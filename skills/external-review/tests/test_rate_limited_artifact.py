import json
from pathlib import Path
import sys, importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "rs.json"))


def test_rate_limited_artifact_shape(tmp_path):
    chain_dir = tmp_path / "chain"
    chain_dir.mkdir()
    out_path = er.write_rate_limited_artifact(
        chain_dir=chain_dir,
        round_num=2,
        timestamp="2026-05-14T1800",
        reviewer_cmd="reviewer-agent",
        reset_at="2026-05-14T18:48:00",
        raw_stderr_tail="ERROR: You've hit your usage limit. ...",
    )
    body = out_path.read_text(encoding="utf-8")
    assert out_path.exists()
    # Cap: <= 8 KB (same as failed-round)
    assert len(body.encode("utf-8")) <= 8 * 1024
    # Required fields
    assert "Status: `rate-limited`" in body
    assert "2026-05-14T18:48:00" in body
    assert "ERROR: You've hit your usage limit" in body
    # Note pointing user to the menu / retry
    assert "rerun after that or use the menu" in body
