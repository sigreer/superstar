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


def _populate(state_file, key="codex"):
    future = (dt.datetime.now() + dt.timedelta(hours=1)).isoformat(timespec="seconds")
    Path(state_file).write_text(json.dumps({"schema_version": 1, "limits": {
        key: {"limited": True, "limited_at": "x", "reset_at": future,
              "reset_source": "test", "raw_stderr_tail": "...", "chain": "c", "round": 1}
    }}))


def _run(args, env):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py")] + args,
        env=env, capture_output=True, text=True, timeout=10,
    )


def test_show_limit_with_entry(tmp_path):
    state_file = tmp_path / "rs.json"
    _populate(state_file)
    env = os.environ.copy(); env["AGENT_REVIEWER_STATE_FILE"] = str(state_file)
    proc = _run(["show-limit"], env)
    assert proc.returncode == 0
    assert "codex" in proc.stdout
    assert "limited" in proc.stdout


def test_show_limit_empty(tmp_path):
    env = os.environ.copy(); env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "absent.json")
    proc = _run(["show-limit"], env)
    assert proc.returncode == 0
    assert "no active limits" in proc.stdout.lower()


def test_clear_limit_removes_entry(tmp_path):
    state_file = tmp_path / "rs.json"
    _populate(state_file, key="codex")
    env = os.environ.copy(); env["AGENT_REVIEWER_STATE_FILE"] = str(state_file)
    proc = _run(["clear-limit", "--reviewer-cmd", "codex"], env)
    assert proc.returncode == 0
    state = json.loads(state_file.read_text())
    assert "codex" not in state["limits"]


def test_clear_limit_all_when_no_filter(tmp_path):
    state_file = tmp_path / "rs.json"
    future = (dt.datetime.now() + dt.timedelta(hours=1)).isoformat(timespec="seconds")
    state_file.write_text(json.dumps({"schema_version": 1, "limits": {
        "codex": {"limited": True, "reset_at": future, "limited_at": "x", "reset_source": "t", "raw_stderr_tail": "", "chain": "c", "round": 1},
        "claude": {"limited": True, "reset_at": future, "limited_at": "x", "reset_source": "t", "raw_stderr_tail": "", "chain": "c", "round": 1},
    }}))
    env = os.environ.copy(); env["AGENT_REVIEWER_STATE_FILE"] = str(state_file)
    proc = _run(["clear-limit"], env)
    assert proc.returncode == 0
    assert json.loads(state_file.read_text())["limits"] == {}


def test_clear_limit_idempotent_on_missing(tmp_path):
    env = os.environ.copy(); env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "absent.json")
    proc = _run(["clear-limit", "--reviewer-cmd", "codex"], env)
    assert proc.returncode == 0
