"""Tests for Slice 5.2: CLI flag wiring of diff into incremental preamble."""
from pathlib import Path
import subprocess, sys, json, importlib.util, os

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


FAKE_REVIEWER = """#!/usr/bin/env bash
cat <<'EOF'
## F1
Severity: blocking
Stub finding.

Overall verdict: revise
EOF
"""


def _init_repo(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    return repo


def test_default_diff_paths_post_slice_is_none(tmp_path):
    target = tmp_path / "slice.md"; target.write_text("x")
    paths = er.default_diff_paths("post-slice", target, [], tmp_path)
    assert paths is None


def test_default_diff_paths_post_phase_is_none(tmp_path):
    target = tmp_path / "p.md"; target.write_text("x")
    paths = er.default_diff_paths("post-phase", target, [target], tmp_path)
    assert paths is None


def test_default_diff_paths_spec_returns_doc_and_context(tmp_path):
    target = tmp_path / "spec.md"; target.write_text("x")
    ctx = tmp_path / "ctx.md"; ctx.write_text("y")
    paths = er.default_diff_paths("spec", target, [ctx], tmp_path)
    assert paths == ["spec.md", "ctx.md"]


def test_build_incremental_preamble_accepts_diff_section(tmp_path):
    manifest = {"chain": "demo", "rounds": [
        {"round": 1, "response": "r1-response.md", "verdict": "revise", "verdict_valid": True}
    ]}
    chain_dir = tmp_path / "c"; chain_dir.mkdir()
    (chain_dir / "r1-response.md").write_text("Overall verdict: revise")
    out = er.build_incremental_preamble(
        manifest=manifest, chain_dir=chain_dir, round_num=2,
        resolution_waiver=False, legacy_first_round=False,
        diff_section="DIFFY_MARKER\n",
    )
    assert "Changes since prior round" in out
    assert "DIFFY_MARKER" in out


def test_build_incremental_preamble_default_diff_section_placeholder(tmp_path):
    manifest = {"chain": "demo", "rounds": [
        {"round": 1, "response": "r1-response.md", "verdict": "revise", "verdict_valid": True}
    ]}
    chain_dir = tmp_path / "c"; chain_dir.mkdir()
    (chain_dir / "r1-response.md").write_text("Overall verdict: revise")
    out = er.build_incremental_preamble(
        manifest=manifest, chain_dir=chain_dir, round_num=2,
        resolution_waiver=False, legacy_first_round=False,
    )
    assert "not available" in out


def _run(repo, args, env_extra=None):
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py")] + args,
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )


def _setup_chain_round_one(tmp_path):
    """Run a round 1 plan review to seed a chain manifest with head_sha_after_round."""
    repo = _init_repo(tmp_path)
    (repo / "plan.md").write_text("# plan\nv1\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    reviewer = repo / "rev.sh"
    reviewer.write_text(FAKE_REVIEWER); reviewer.chmod(0o755)
    r = _run(repo, ["review", "--kind", "plan", "--file", "plan.md", "--emit", "json",
                    "--no-preflight"],
             env_extra={"AGENT_REVIEWER_CMD": str(reviewer)})
    assert r.returncode == 0, r.stderr
    return repo, reviewer


def test_round2_embeds_diff_in_prompt_for_spec_kind(tmp_path):
    repo, reviewer = _setup_chain_round_one(tmp_path)
    # Change plan.md so a diff exists base..HEAD
    (repo / "plan.md").write_text("# plan\nv1\nv2-changed\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "edit"], check=True)
    r = _run(repo, ["review", "--kind", "plan", "--file", "plan.md", "--emit", "json",
                    "--allow-missing-resolution"],
             env_extra={"AGENT_REVIEWER_CMD": str(reviewer)})
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    prompt_path = repo / payload["prompt_path"]
    body = prompt_path.read_text()
    assert "Changes since prior round" in body
    assert "+v2-changed" in body
    # Manifest fields
    manifest = json.loads((repo / "docs/reviewer/plan-plan/chain.json").read_text())
    r2 = manifest["rounds"][-1]
    assert r2["diff_included"] is True
    assert r2["base_ref"]
    assert r2["base_ref_source"] == "auto"
    assert payload["diff_included"] is True
    assert payload["base_ref"] == r2["base_ref"]


def test_no_diff_flag_suppresses_diff(tmp_path):
    repo, reviewer = _setup_chain_round_one(tmp_path)
    (repo / "plan.md").write_text("# plan\nv1\nv2\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "e"], check=True)
    r = _run(repo, ["review", "--kind", "plan", "--file", "plan.md", "--emit", "json", "--no-diff",
                    "--allow-missing-resolution"],
             env_extra={"AGENT_REVIEWER_CMD": str(reviewer)})
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    body = (repo / payload["prompt_path"]).read_text()
    assert "diff suppressed via --no-diff" in body
    assert "+v2" not in body
    manifest = json.loads((repo / "docs/reviewer/plan-plan/chain.json").read_text())
    r2 = manifest["rounds"][-1]
    assert r2["diff_included"] is False
    assert r2["base_ref_source"] == "suppressed"
    assert payload["diff_included"] is False


def test_base_ref_explicit_override(tmp_path):
    repo, reviewer = _setup_chain_round_one(tmp_path)
    # Create commits B and C; pass --base-ref pointing at B so only C..HEAD is diffed.
    (repo / "plan.md").write_text("# plan\nv1\nB\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "B"], check=True)
    sha_b = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                           capture_output=True, text=True, check=True).stdout.strip()
    (repo / "plan.md").write_text("# plan\nv1\nB\nC-line\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "C"], check=True)

    r = _run(repo, ["review", "--kind", "plan", "--file", "plan.md", "--emit", "json",
                    "--base-ref", sha_b, "--allow-missing-resolution"],
             env_extra={"AGENT_REVIEWER_CMD": str(reviewer)})
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    body = (repo / payload["prompt_path"]).read_text()
    assert "+C-line" in body
    assert "+B" not in body  # since base was B
    manifest = json.loads((repo / "docs/reviewer/plan-plan/chain.json").read_text())
    r2 = manifest["rounds"][-1]
    assert r2["base_ref"] == sha_b
    assert r2["base_ref_source"] == "explicit"


def test_changed_files_limits_diff_scope(tmp_path):
    repo, reviewer = _setup_chain_round_one(tmp_path)
    (repo / "plan.md").write_text("# plan\nv1\nplan-change\n")
    (repo / "other.md").write_text("OTHER_FILE_CHANGE\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "two"], check=True)

    r = _run(repo, ["review", "--kind", "plan", "--file", "plan.md", "--emit", "json",
                    "--changed-files", "plan.md", "--allow-missing-resolution"],
             env_extra={"AGENT_REVIEWER_CMD": str(reviewer)})
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    body = (repo / payload["prompt_path"]).read_text()
    assert "+plan-change" in body
    assert "OTHER_FILE_CHANGE" not in body


def test_max_diff_lines_truncates(tmp_path):
    repo, reviewer = _setup_chain_round_one(tmp_path)
    big = "\n".join(f"line{i}" for i in range(500)) + "\n"
    (repo / "plan.md").write_text(big)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "big"], check=True)
    r = _run(repo, ["review", "--kind", "plan", "--file", "plan.md", "--emit", "json",
                    "--max-diff-lines", "20", "--allow-missing-resolution"],
             env_extra={"AGENT_REVIEWER_CMD": str(reviewer)})
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    body = (repo / payload["prompt_path"]).read_text()
    assert "additional lines" in body
