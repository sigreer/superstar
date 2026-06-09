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
