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


def test_rate_limit_payload_shape():
    payload = er.make_rate_limit_payload(
        reviewer_cmd="reviewer-agent",
        reset_at="2026-05-14T18:48:00",
        reset_source="regex:codex_usage_limit",
        chain="some-chain",
        round_num=2,
        request_path="docs/reviewer/some-chain/r2-...-request.md",
        raw_stderr_tail="ERROR: You've hit your usage limit ...",
    )
    assert payload["rate_limited"] is True
    assert payload["reviewer_cmd"] == "reviewer-agent"
    assert payload["reset_at"] == "2026-05-14T18:48:00"
    assert payload["reset_source"] == "regex:codex_usage_limit"
    assert payload["chain"] == "some-chain"
    assert payload["round"] == 2
    assert payload["request_path"].endswith("r2-...-request.md")
    assert "raw_stderr_tail" in payload


def test_rate_limit_payload_serialises_to_json():
    payload = er.make_rate_limit_payload(
        reviewer_cmd="reviewer-agent",
        reset_at="2026-05-14T18:48:00",
        reset_source="regex:codex_usage_limit",
        chain="c", round_num=2, request_path="r", raw_stderr_tail="t",
    )
    s = json.dumps(payload)
    assert "rate_limited" in s
