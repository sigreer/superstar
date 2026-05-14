# skills/external-review/tests/test_rate_limit_detection.py
import datetime as dt
from pathlib import Path
import sys, importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


CODEX_STDERR = (
    "ERROR: You've hit your usage limit. Upgrade to Pro "
    "(https://chatgpt.com/explore/pro), visit https://chatgpt.com/codex/settings/usage "
    "to purchase more credits or try again at 6:48 PM.\n"
)


def test_codex_sample_matches():
    matched, _reset_at, name = er.detect_rate_limit(CODEX_STDERR)
    assert matched is True
    assert name == "codex_usage_limit"


def test_codex_sample_extracts_time_group(monkeypatch):
    monkeypatch.setattr(er, "_now_local", lambda: dt.datetime(2026, 5, 14, 17, 0, 0))
    matched, reset_at, _ = er.detect_rate_limit(CODEX_STDERR)
    assert matched is True
    assert reset_at == dt.datetime(2026, 5, 14, 18, 48, 0)


def test_unmatched_stderr_returns_falsey():
    matched, reset_at, name = er.detect_rate_limit("Traceback ...\nValueError: foo\n")
    assert matched is False
    assert reset_at is None
    assert name is None


def test_claude_pattern_extracts_reset_time(monkeypatch):
    """F2: the claude_cli_rate_limit pattern must capture the reset clock,
    not the (rate limit|rate-limited) alternation. Group 1 should be the
    time text, parseable by _parse_reset_time."""
    monkeypatch.setattr(er, "_now_local", lambda: dt.datetime(2026, 5, 14, 17, 0, 0))
    stderr = "Error: rate limit exceeded. Reset at 18:30"
    matched, reset_at, name = er.detect_rate_limit(stderr)
    assert matched is True
    assert name == "claude_cli_rate_limit"
    assert reset_at == dt.datetime(2026, 5, 14, 18, 30, 0)


def test_user_pattern_via_env(monkeypatch):
    monkeypatch.setenv(
        "AGENT_REVIEWER_RATE_LIMIT_PATTERNS",
        r"my_backend=ERROR limit hit until (\d{1,2}:\d{2})",
    )
    matched, reset_at, name = er.detect_rate_limit("ERROR limit hit until 14:30")
    assert matched is True
    assert name == "my_backend"
    assert reset_at is not None and reset_at.hour == 14 and reset_at.minute == 30
