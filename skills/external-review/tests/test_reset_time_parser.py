import datetime as dt
from pathlib import Path
import sys, importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def test_parse_pm_clock(monkeypatch):
    fixed = dt.datetime(2026, 5, 14, 17, 0, 0)
    monkeypatch.setattr(er, "_now_local", lambda: fixed)
    out = er._parse_reset_time("6:48 PM")
    assert out == dt.datetime(2026, 5, 14, 18, 48, 0)


def test_parse_am_clock(monkeypatch):
    fixed = dt.datetime(2026, 5, 14, 17, 0, 0)
    monkeypatch.setattr(er, "_now_local", lambda: fixed)
    out = er._parse_reset_time("9:15 AM")
    assert out == dt.datetime(2026, 5, 15, 9, 15, 0)


def test_parse_24h_clock(monkeypatch):
    fixed = dt.datetime(2026, 5, 14, 17, 0, 0)
    monkeypatch.setattr(er, "_now_local", lambda: fixed)
    out = er._parse_reset_time("19:30")
    assert out == dt.datetime(2026, 5, 14, 19, 30, 0)


def test_parse_past_24h_wraps(monkeypatch):
    fixed = dt.datetime(2026, 5, 14, 17, 0, 0)
    monkeypatch.setattr(er, "_now_local", lambda: fixed)
    out = er._parse_reset_time("08:00")
    assert out == dt.datetime(2026, 5, 15, 8, 0, 0)


def test_parse_unparseable_falls_back(monkeypatch):
    fixed = dt.datetime(2026, 5, 14, 17, 0, 0)
    monkeypatch.setattr(er, "_now_local", lambda: fixed)
    monkeypatch.setenv("AGENT_REVIEWER_LIMIT_FALLBACK_HOURS", "4")
    out = er._parse_reset_time("some_weird_string")
    assert out == dt.datetime(2026, 5, 14, 21, 0, 0)
