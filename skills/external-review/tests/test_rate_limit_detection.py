# skills/external-review/tests/test_rate_limit_detection.py
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


def test_codex_sample_extracts_time_group():
    matched, reset_at, _ = er.detect_rate_limit(CODEX_STDERR)
    assert matched is True
    # reset_at parsing strengthened in Task 1.5; for this task only assert non-None.
    assert reset_at is not None


def test_unmatched_stderr_returns_falsey():
    matched, reset_at, name = er.detect_rate_limit("Traceback ...\nValueError: foo\n")
    assert matched is False
    assert reset_at is None
    assert name is None


def test_user_pattern_via_env(monkeypatch):
    monkeypatch.setenv(
        "AGENT_REVIEWER_RATE_LIMIT_PATTERNS",
        r"my_backend=ERROR limit hit until (\d{1,2}:\d{2})",
    )
    matched, reset_at, name = er.detect_rate_limit("ERROR limit hit until 14:30")
    assert matched is True
    assert name == "my_backend"
    # reset_at parsing strengthened in Task 1.5; for now just assert non-None.
    assert reset_at is not None
