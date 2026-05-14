import datetime as dt
import json
import os
from pathlib import Path
import sys
import importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "reviewer-state.json"))


def test_state_path_uses_env_override(tmp_path, monkeypatch):
    target = tmp_path / "custom-state.json"
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(target))
    assert er.state_file_path() == target


def test_load_state_missing_file_returns_empty():
    state = er.load_state()
    assert state == {"schema_version": 1, "limits": {}}


def test_load_state_round_trip(tmp_path):
    target = Path(os.environ["AGENT_REVIEWER_STATE_FILE"])
    target.write_text(json.dumps({"schema_version": 1, "limits": {"reviewer-agent": {"limited": True}}}))
    state = er.load_state()
    assert state["limits"]["reviewer-agent"]["limited"] is True


def test_load_state_corrupt_file_fails_open(capsys, tmp_path):
    target = Path(os.environ["AGENT_REVIEWER_STATE_FILE"])
    target.write_text("{not json")
    state = er.load_state()
    assert state == {"schema_version": 1, "limits": {}}
    captured = capsys.readouterr()
    assert "reviewer-state.json" in captured.err  # warning surfaced


def test_save_state_creates_parent_dir_0700(tmp_path, monkeypatch):
    target = tmp_path / "nested" / "deep" / "state.json"
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(target))
    er.save_state({"schema_version": 1, "limits": {"reviewer-agent": {"limited": True}}})
    assert target.exists()
    # Parent dir permissions: 0o700 (owner rwx, nothing else)
    parent_mode = oct(target.parent.stat().st_mode & 0o777)
    assert parent_mode == "0o700"


def test_save_state_round_trip():
    er.save_state({"schema_version": 1, "limits": {"reviewer-agent": {"limited": True, "reset_at": "2026-05-14T18:48:00"}}})
    out = er.load_state()
    assert out["limits"]["reviewer-agent"]["reset_at"] == "2026-05-14T18:48:00"


def test_save_state_atomic_via_tmp_rename(tmp_path, monkeypatch):
    """Writing should go through a .tmp file then rename, so a crash mid-write
    can never corrupt the on-disk state."""
    target = tmp_path / "state.json"
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(target))
    target.write_text('{"schema_version": 1, "limits": {"reviewer-agent": {"limited": false}}}')
    er.save_state({"schema_version": 1, "limits": {"reviewer-agent": {"limited": True}}})
    # After save, no orphan .tmp file remains
    assert not (tmp_path / "state.json.tmp").exists()
    assert er.load_state()["limits"]["reviewer-agent"]["limited"] is True


def test_get_active_limit_expires_past_reset(monkeypatch):
    past = (dt.datetime.now() - dt.timedelta(hours=1)).isoformat(timespec="seconds")
    er.save_state({"schema_version": 1, "limits": {"reviewer-agent": {
        "limited": True, "reset_at": past, "limited_at": past, "reset_source": "test",
        "raw_stderr_tail": "", "chain": "x", "round": 1
    }}})
    # get_active_limit clears expired entries in-place and returns None.
    assert er.get_active_limit("reviewer-agent") is None
    # The state file should now show limits={} for reviewer-agent (entry removed).
    assert "reviewer-agent" not in er.load_state()["limits"]


def test_get_active_limit_returns_live_entry():
    future = (dt.datetime.now() + dt.timedelta(hours=1)).isoformat(timespec="seconds")
    er.save_state({"schema_version": 1, "limits": {"reviewer-agent": {
        "limited": True, "reset_at": future, "limited_at": "x", "reset_source": "t",
        "raw_stderr_tail": "", "chain": "c", "round": 1
    }}})
    entry = er.get_active_limit("reviewer-agent")
    assert entry is not None
    assert entry["reset_at"] == future


def test_get_active_limit_no_entry_returns_none():
    assert er.get_active_limit("reviewer-agent") is None


def test_reviewer_cmd_basename_simple(monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_CMD", "reviewer-agent")
    assert er.reviewer_cmd_basename() == "reviewer-agent"


def test_reviewer_cmd_basename_template(monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_CMD", "bash -c 'reviewer-agent {prompt_file}'")
    assert er.reviewer_cmd_basename() == "bash"


def test_reviewer_cmd_basename_state_key_override(monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_CMD", "bash -c 'foo'")
    monkeypatch.setenv("AGENT_REVIEWER_STATE_KEY", "codex")
    assert er.reviewer_cmd_basename() == "codex"


def test_reviewer_cmd_basename_default(monkeypatch):
    monkeypatch.delenv("AGENT_REVIEWER_CMD", raising=False)
    monkeypatch.delenv("AGENT_REVIEWER_STATE_KEY", raising=False)
    assert er.reviewer_cmd_basename() == "reviewer-agent"


def _concurrent_writer(state_path: str, key: str) -> None:
    """Process target: read-modify-write a single key under state lock."""
    import os as _os
    import time as _time
    import importlib.util as _ilu
    from pathlib import Path as _Path
    _os.environ["AGENT_REVIEWER_STATE_FILE"] = state_path
    scripts_dir = _Path(__file__).resolve().parents[1] / "scripts"
    _spec = _ilu.spec_from_file_location("external_reviewer", scripts_dir / "external-reviewer.py")
    _er = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_er)
    # Atomic RMW under the state lock: a missing lock (or split read/write
    # locks) would let one writer overwrite the other's key.
    def _mutate(s):
        # Small sleep maximises contention so a broken lock would lose a key.
        _time.sleep(0.05)
        s["limits"][key] = {
            "limited": True, "reset_at": "x", "limited_at": "x",
            "reset_source": "t", "raw_stderr_tail": "", "chain": "c", "round": 1,
        }
    _er.update_state(_mutate)


def test_save_state_concurrent_writers_preserve_keys(tmp_path, monkeypatch):
    """Two concurrent save_state calls writing different keys must both land
    (state-file locking — spec line 79)."""
    import multiprocessing as mp
    state = tmp_path / "rs.json"
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(state))
    # Seed an empty state so both workers race on a known starting point.
    er.save_state({"schema_version": 1, "limits": {}})

    ctx = mp.get_context("fork")
    p1 = ctx.Process(target=_concurrent_writer, args=(str(state), "alpha"))
    p2 = ctx.Process(target=_concurrent_writer, args=(str(state), "beta"))
    p1.start(); p2.start()
    p1.join(timeout=10); p2.join(timeout=10)
    assert p1.exitcode == 0 and p2.exitcode == 0
    final = json.loads(state.read_text())
    assert "alpha" in final["limits"]
    assert "beta" in final["limits"]


def test_state_lock_file_exists_after_save(tmp_path, monkeypatch):
    """The companion .lock file should be created next to the state file."""
    target = tmp_path / "rs.json"
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(target))
    er.save_state({"schema_version": 1, "limits": {}})
    assert (tmp_path / "rs.json.lock").exists()


def test_reviewer_cmd_flag_hoists_to_env(tmp_path):
    """S1.F2: --reviewer-cmd passed on the CLI must be hoisted to
    AGENT_REVIEWER_CMD so reviewer_cmd_basename() uses it as the state key.
    End-to-end via subprocess: a rate-limited reviewer should produce a
    state entry keyed by the CLI-provided command path."""
    import subprocess
    state_file = tmp_path / "rs.json"
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    fake = tmp_path / "fake.sh"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        "echo \"ERROR: You've hit your usage limit. Try again at 11:59 PM.\" >&2\n"
        "exit 1\n"
    )
    fake.chmod(0o755)

    env = os.environ.copy()
    env.pop("AGENT_REVIEWER_CMD", None)  # ensure CLI is the only source
    env["AGENT_REVIEWER_STATE_FILE"] = str(state_file)
    SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md",
         "--reviewer-cmd", str(fake), "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == er.EXIT_CODE_RATE_LIMITED, proc.stderr
    state = json.loads(state_file.read_text())
    assert str(fake) in state["limits"], f"state key missing; got: {list(state['limits'])}"
