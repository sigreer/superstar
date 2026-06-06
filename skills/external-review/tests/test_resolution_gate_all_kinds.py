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
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: revise'\n")
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


def test_spec_round2_refused_without_resolution(tmp_path):
    repo = _init_repo(tmp_path)
    r1 = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
    assert r1.returncode == 0, r1.stderr
    r2 = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
    assert r2.returncode == 3, r2.stderr + r2.stdout
    assert "r1-resolution.md" in r2.stderr


def test_spec_round2_proceeds_with_resolution(tmp_path):
    repo = _init_repo(tmp_path)
    _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
    chain_dir = next((repo / "docs" / "reviewer").glob("*-spec"))
    (chain_dir / "r1-resolution.md").write_text(
        "# Resolution for r1\n\n## F1\nStatus: fixed\n", encoding="utf-8")
    r2 = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
    assert r2.returncode == 0, r2.stderr


def test_spec_round2_waiver_bypasses(tmp_path):
    repo = _init_repo(tmp_path)
    _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
    r2 = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json",
              "--allow-missing-resolution")
    assert r2.returncode == 0, r2.stderr


def test_plan_round2_refused_without_resolution(tmp_path):
    repo = _init_repo(tmp_path)
    r1 = _run(repo, "--kind", "plan", "--file", "plan.md", "--emit", "json")
    assert r1.returncode == 0, r1.stderr
    r2 = _run(repo, "--kind", "plan", "--file", "plan.md", "--emit", "json")
    assert r2.returncode == 3, r2.stderr + r2.stdout
