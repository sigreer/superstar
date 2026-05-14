import json, os, subprocess, sys
from pathlib import Path
import datetime as dt
import importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "rs.json"))


def _make_repo(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\nbody\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    return repo


def test_active_limit_refuses_spawn(tmp_path, monkeypatch):
    """When state shows an active limit, the script must exit 8 without spawning."""
    state_file = tmp_path / "state.json"
    future = (dt.datetime.now() + dt.timedelta(hours=1)).isoformat(timespec="seconds")
    repo = _make_repo(tmp_path)
    sentinel = repo / "spawn-evidence.txt"
    reviewer = repo / "fake-reviewer"
    reviewer.write_text(f"#!/usr/bin/env bash\ntouch '{sentinel}'\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)

    # State key is the full first-whitespace token of AGENT_REVIEWER_CMD,
    # which for a bare absolute path is the full path.
    key = str(reviewer)
    state_file.write_text(json.dumps({"schema_version": 1, "limits": {
        key: {
            "limited": True, "limited_at": "x", "reset_at": future, "reset_source": "test",
            "raw_stderr_tail": "", "chain": "c", "round": 1,
        }
    }}))

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(state_file)

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == er.EXIT_CODE_RATE_LIMITED, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["rate_limited"] is True
    # No spawn happened
    assert not sentinel.exists()


def test_expired_limit_clears_and_proceeds(tmp_path):
    """When reset_at is in the past, pre-spawn check clears the entry and proceeds."""
    state_file = tmp_path / "state.json"
    past = (dt.datetime.now() - dt.timedelta(hours=1)).isoformat(timespec="seconds")
    repo = _make_repo(tmp_path)
    reviewer = repo / "fake-reviewer"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)
    key = str(reviewer)
    state_file.write_text(json.dumps({"schema_version": 1, "limits": {
        key: {
            "limited": True, "limited_at": "x", "reset_at": past, "reset_source": "test",
            "raw_stderr_tail": "", "chain": "c", "round": 1,
        }
    }}))

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(state_file)

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    # Entry should be removed from state
    state = json.loads(state_file.read_text())
    assert key not in state.get("limits", {})
