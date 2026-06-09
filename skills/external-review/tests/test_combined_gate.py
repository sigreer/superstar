from pathlib import Path
import subprocess, sys, os

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "external-reviewer.py"


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text(
        "# Plan\n\n## Tasks\n- [ ] do it\n\n## Verification\nRun `pytest`.\n"
    )
    (repo / "spec.md").write_text("# Spec\n\n## Acceptance criteria\n1. works\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    reviewer = repo / "stub.sh"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)
    return repo


def _run(repo: Path, *args: str):
    env = os.environ.copy(); env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "review", *args, "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True,
    )


def test_combined_gate_non_plan_kind_exits_2(tmp_path):
    repo = _init_repo(tmp_path)
    r = _run(repo, "--kind", "spec", "--file", "plan.md",
             "--combined-gate", "spec.md")
    assert r.returncode == 2, r.stderr
    # Must be OUR validation, not argparse's "unrecognized arguments" (which
    # also exits 2). This is what makes the test prove the new behaviour.
    assert "unrecognized arguments" not in r.stderr
    assert "only valid with --kind plan" in r.stderr
    # No chain folder created.
    assert not (repo / "docs" / "reviewer").exists()


def test_combined_gate_missing_spec_exits_2(tmp_path):
    repo = _init_repo(tmp_path)
    r = _run(repo, "--kind", "plan", "--file", "plan.md",
             "--combined-gate", "nope.md")
    assert r.returncode == 2, r.stderr
    assert "unrecognized arguments" not in r.stderr
    assert "not found" in r.stderr.lower()
    assert "nope.md" in r.stderr
    assert not (repo / "docs" / "reviewer").exists()


import json


def _chain_dir(repo: Path) -> Path:
    base = repo / "docs" / "reviewer"
    # Single chain expected in these tests.
    return next(d for d in base.iterdir() if d.is_dir())


def _manifest(repo: Path) -> dict:
    return json.loads((_chain_dir(repo) / "chain.json").read_text())


def test_round1_persists_and_stamps_combined_gate(tmp_path):
    repo = _init_repo(tmp_path)
    r = _run(repo, "--kind", "plan", "--file", "plan.md",
             "--work-id", "P1.S1", "--combined-gate", "spec.md")
    assert r.returncode == 0, r.stderr
    m = _manifest(repo)
    assert m["combined_gate_spec"] == "spec.md"          # chain-level persist
    rnd = m["rounds"][-1]
    assert rnd["combined_gate"] is True                  # round stamp
    assert rnd["combined_gate_spec"] == "spec.md"


def test_round2_without_flag_reuses_persisted_spec(tmp_path):
    repo = _init_repo(tmp_path)
    r1 = _run(repo, "--kind", "plan", "--file", "plan.md",
              "--work-id", "P1.S1", "--combined-gate", "spec.md")
    assert r1.returncode == 0, r1.stderr
    # Round 2 omits --combined-gate; allow-missing-resolution because r1 was ready.
    r2 = _run(repo, "--kind", "plan", "--file", "plan.md",
              "--work-id", "P1.S1", "--allow-missing-resolution")
    assert r2.returncode == 0, r2.stderr
    m = _manifest(repo)
    assert len(m["rounds"]) == 2
    assert m["rounds"][-1]["combined_gate"] is True      # still combined on r2
    assert m["rounds"][-1]["combined_gate_spec"] == "spec.md"


def test_round2_different_spec_exits_6(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "other-spec.md").write_text("# Other\n\n## Acceptance criteria\n1. x\n")
    r1 = _run(repo, "--kind", "plan", "--file", "plan.md",
              "--work-id", "P1.S1", "--combined-gate", "spec.md")
    assert r1.returncode == 0, r1.stderr
    r2 = _run(repo, "--kind", "plan", "--file", "plan.md", "--work-id", "P1.S1",
              "--combined-gate", "other-spec.md", "--allow-missing-resolution")
    assert r2.returncode == 6, r2.stderr
    assert "combined" in r2.stderr.lower()


def test_combined_gate_on_noncombined_chain_exits_6(tmp_path):
    repo = _init_repo(tmp_path)
    # Round 1 is a standalone plan review (no --combined-gate).
    r1 = _run(repo, "--kind", "plan", "--file", "plan.md", "--work-id", "P1.S1")
    assert r1.returncode == 0, r1.stderr
    r2 = _run(repo, "--kind", "plan", "--file", "plan.md", "--work-id", "P1.S1",
              "--combined-gate", "spec.md", "--allow-missing-resolution")
    assert r2.returncode == 6, r2.stderr


def test_standalone_plan_has_no_combined_keys(tmp_path):
    repo = _init_repo(tmp_path)
    r = _run(repo, "--kind", "plan", "--file", "plan.md", "--work-id", "P1.S1")
    assert r.returncode == 0, r.stderr
    m = _manifest(repo)
    assert "combined_gate_spec" not in m
    assert "combined_gate" not in m["rounds"][-1]


def test_combined_gate_attaches_spec_to_context(tmp_path):
    # Round 1 is broad, so attached context is previewed in the request.
    # "Acceptance criteria" appears only in spec.md (not in plan.md), so its
    # presence proves the spec was attached to the review context.
    repo = _init_repo(tmp_path)
    r = _run(repo, "--kind", "plan", "--file", "plan.md",
             "--work-id", "P1.S1", "--combined-gate", "spec.md")
    assert r.returncode == 0, r.stderr
    request = next(_chain_dir(repo).glob("r1-*-request.md")).read_text()
    assert "Acceptance criteria" in request


def test_combined_gate_dedupes_spec_in_context(tmp_path):
    # Spec supplied both via --combined-gate and --context must attach once.
    repo = _init_repo(tmp_path)
    r = _run(repo, "--kind", "plan", "--file", "plan.md", "--work-id", "P1.S1",
             "--combined-gate", "spec.md", "--context", "spec.md")
    assert r.returncode == 0, r.stderr
    request = next(_chain_dir(repo).glob("r1-*-request.md")).read_text()
    # spec.md's unique content is previewed exactly once (deduped).
    assert request.count("Acceptance criteria") == 1
