import subprocess, sys, os, json
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)


def _split_stub(repo: Path) -> Path:
    """Stub reviewer: primary returns ready, sweep returns revise."""
    rev = repo / "stub.sh"
    rev.write_text(
        '#!/usr/bin/env bash\n'
        'PROMPT="$1"\n'
        'case "$PROMPT" in\n'
        '  *sweep*) printf "## F1\\nSeverity: blocking\\nOverall verdict: revise\\n" ;;\n'
        '  *)       printf "Overall verdict: ready\\n" ;;\n'
        'esac\n'
    )
    rev.chmod(0o755)
    return rev


def test_gate_fires_when_merged_verdict_is_revise_even_if_primary_ready(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    rev = _split_stub(repo)

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = f'{rev} {{prompt_file}}'

    # Round 1: thorough → sweep returns revise → merged_verdict revise, primary ready.
    r1 = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--work-id", "P1.S1",
         "--file", "plan.md", "--review-depth", "thorough", "--emit", "json",
         "--no-preflight"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert r1.returncode == 0, r1.stderr
    p1 = json.loads(r1.stdout)
    assert p1["merged_verdict"] == "revise", p1
    # Primary reviewer should have said ready (proves it's merged that triggers).
    assert p1["reviewers"][0]["verdict"] == "ready", p1

    # Round 2 without resolution: gate must fire on merged_verdict.
    r2 = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--work-id", "P1.S1",
         "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert r2.returncode == 3, (r2.stdout, r2.stderr)
    assert "resolution" in (r2.stderr + r2.stdout).lower()


def test_gate_waivable_with_allow_missing_resolution(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    rev = _split_stub(repo)

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = f'{rev} {{prompt_file}}'

    r1 = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--work-id", "P1.S1",
         "--file", "plan.md", "--review-depth", "thorough", "--emit", "json",
         "--no-preflight"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert r1.returncode == 0
    assert json.loads(r1.stdout)["merged_verdict"] == "revise"

    # Round 2 with waiver: should succeed.
    r2 = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--work-id", "P1.S1",
         "--file", "plan.md", "--emit", "json", "--allow-missing-resolution"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert r2.returncode == 0, (r2.stdout, r2.stderr)


def test_top_level_verdict_reflects_merged_when_sweeps_present(tmp_path):
    """JSON `verdict` should mirror merged outcome (worst-of), not just primary."""
    repo = tmp_path / "r"
    _init_repo(repo)
    rev = _split_stub(repo)

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = f'{rev} {{prompt_file}}'

    r1 = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--work-id", "P1.S1",
         "--file", "plan.md", "--review-depth", "thorough", "--emit", "json",
         "--no-preflight"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert r1.returncode == 0
    p1 = json.loads(r1.stdout)
    assert p1["merged_verdict"] == "revise"
    assert p1["verdict"] == "revise", p1


def test_top_level_verdict_is_primary_when_no_sweeps(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    rev = repo / "stub.sh"
    rev.write_text(
        '#!/usr/bin/env bash\n'
        'printf "Overall verdict: ready\\n"\n'
    )
    rev.chmod(0o755)

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = f'{rev} {{prompt_file}}'

    r1 = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--work-id", "P1.S1",
         "--file", "plan.md", "--emit", "json", "--no-preflight"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert r1.returncode == 0, r1.stderr
    p1 = json.loads(r1.stdout)
    assert p1["verdict"] == "ready"
    # merged_verdict equals primary when no sweep group.
    assert p1["merged_verdict"] == "ready"
