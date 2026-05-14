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
