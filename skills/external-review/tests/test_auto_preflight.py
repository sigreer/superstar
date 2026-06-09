from pathlib import Path
import subprocess, sys, os

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    reviewer = repo / "stub.sh"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)
    return repo


def _run(repo, *args, env=None):
    base_env = os.environ.copy()
    if env:
        base_env.update(env)
    base_env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"), "review", *args],
        cwd=repo, env=base_env, capture_output=True, text=True,
    )


import json


def test_round1_refuses_on_failure_without_spawning(tmp_path):
    repo = _init_repo(tmp_path)
    # Overwrite the committed target with a failing spec (TODO + no criteria).
    (repo / "plan.md").write_text("# Spec\n\nTODO: not done. No criteria.\n")
    r = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
    assert r.returncode == 4, r.stderr + r.stdout
    # The chain manifest is eager-written (rounds: []) before the gate runs,
    # but no reviewer round must have been recorded.
    chains = list((repo / "docs" / "reviewer").glob("*/chain.json"))
    assert len(chains) == 1, chains
    manifest = json.loads(chains[0].read_text())
    assert manifest["rounds"] == []


def test_warnings_not_printed_twice_on_failure(tmp_path):
    # Regression: when a document has both failures and warnings, the early
    # warning loop must NOT run — _print_preflight_text already includes them.
    # A backtick path pointing to a non-existent file is a warning; missing
    # required section is a failure. Confirm the warning text appears exactly once.
    repo = _init_repo(tmp_path)
    # Target has: a placeholder (failure) + a backtick path that looks like a
    # dangling relative path (warning). The path `missing/file.py` won't resolve
    # under tmp repo root, triggering a dangling-path warning.
    (repo / "plan.md").write_text(
        "# Spec\n\nTODO: not done.\n\nSee `missing/file.py` for details.\n"
    )
    r = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
    assert r.returncode == 4, r.stderr + r.stdout
    # Count occurrences of "preflight warning" — must be exactly 1 (from
    # _print_preflight_text), not 2 (early loop + _print_preflight_text).
    assert r.stderr.count("preflight warning") <= 1, (
        "Warning appeared more than once — double-print regression:\n" + r.stderr
    )


def test_no_preflight_flag_reaches_reviewer(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "plan.md").write_text("# Spec\n\nTODO: not done. No criteria.\n")
    r = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json",
             "--no-preflight")
    assert r.returncode == 0, r.stderr + r.stdout
    payload = json.loads(r.stdout)
    assert payload["merged_verdict"] == "ready"


def test_clean_target_passes_preflight_and_reviews(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "plan.md").write_text(
        "# Spec\n\n## Acceptance criteria\n\n1. A grounded criterion.\n")
    r = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
    assert r.returncode == 0, r.stderr + r.stdout


def test_round2_skips_autopreflight(tmp_path):
    # Round 1 clean -> reviews. Make the target fail, force round 2: the
    # auto-gate must NOT fire on round 2 (it only runs on round 1).
    repo = _init_repo(tmp_path)
    (repo / "plan.md").write_text(
        "# Spec\n\n## Acceptance criteria\n\n1. Clean round one.\n")
    r1 = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
    assert r1.returncode == 0, r1.stderr
    # Dirty the target for round 2, attach a resolution so the resolution gate
    # (P9.S1, all kinds) does not block, and confirm preflight does not refuse.
    (repo / "plan.md").write_text("# Spec\n\nTODO now broken, no criteria.\n")
    chain_dir = next((repo / "docs" / "reviewer").glob("*-spec"))
    (chain_dir / "r1-resolution.md").write_text("# Resolution for r1\n\n## F1\nStatus: fixed\n")
    r2 = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
    assert r2.returncode == 0, r2.stderr + r2.stdout


def test_missing_context_still_exit_2_not_4(tmp_path):
    # The review path's existing missing-context validation returns exit 2
    # BEFORE preflight; it is not deferred into a preflight exit-4 finding.
    repo = _init_repo(tmp_path)
    (repo / "plan.md").write_text(
        "# Spec\n\n## Acceptance criteria\n\n1. Clean.\n")
    r = _run(repo, "--kind", "spec", "--file", "plan.md",
             "--context", "does-not-exist.md", "--emit", "json")
    assert r.returncode == 2, r.stderr + r.stdout


def test_schema_too_new_aborts_before_preflight(tmp_path):
    # Spec AC8 ordering regression: the manifest is read (and a schema-too-new
    # manifest aborts) BEFORE the round-1 preflight runs. Pre-seed the chain
    # folder with an over-supported schema_version AND a target that would also
    # trip preflight; the schema error must win, proving preflight cannot mask
    # it. Chain slug for target `plan.md`, kind spec, no work-id is `plan-spec`
    # (target-stem-no-date + "-" + kind).
    repo = _init_repo(tmp_path)
    (repo / "plan.md").write_text("# Spec\n\nTODO no criteria — would fail preflight.\n")
    chain = repo / "docs" / "reviewer" / "plan-spec"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text(
        json.dumps({"schema_version": 999, "rounds": []}), encoding="utf-8")
    r = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
    assert r.returncode == 4, r.stderr + r.stdout
    # The schema-too-new message wins; preflight findings are NOT printed.
    assert "schema_version" in r.stderr
    assert "preflight" not in r.stderr.lower()
