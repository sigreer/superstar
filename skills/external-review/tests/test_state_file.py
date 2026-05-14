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
