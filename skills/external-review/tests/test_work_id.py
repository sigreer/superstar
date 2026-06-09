from pathlib import Path
import subprocess, sys, os

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"; repo.mkdir()
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


def test_post_slice_without_work_id_errors(tmp_path):
    repo = _init_repo(tmp_path)
    env = os.environ.copy(); env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True,
    )
    assert r.returncode == 2
    assert "--work-id" in r.stderr


def test_post_phase_without_work_id_errors(tmp_path):
    repo = _init_repo(tmp_path)
    env = os.environ.copy(); env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-phase", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True,
    )
    assert r.returncode == 2


def test_spec_without_work_id_ok(tmp_path):
    repo = _init_repo(tmp_path)
    env = os.environ.copy(); env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "spec", "--file", "plan.md", "--emit", "json",
         "--no-preflight"],
        cwd=repo, env=env, capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
