"""Tests for _renamespace_finding_ids — the sweep finding-ID namespacing helper."""
from pathlib import Path
import importlib.util
import sys

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "external-reviewer.py"

# Load the script as a module (the file has a dash in its name so we can't import normally).
_spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["external_reviewer"] = _mod
_spec.loader.exec_module(_mod)
_renamespace_finding_ids = _mod._renamespace_finding_ids


def test_heading_and_prose_renamespaced_once():
    out = _renamespace_finding_ids("## F1\nsee F2", 1)
    assert out == "## S1.F1\nsee S1.F2"


def test_already_prefixed_ids_not_double_rewritten():
    src = "## S1.F1\nsee S1.F2"
    # Idempotent under a second pass with the same index.
    assert _renamespace_finding_ids(src, 1) == src
    # And not double-prefixed when re-namespacing into a different sweep number.
    assert _renamespace_finding_ids(src, 2) == src


def test_idempotent_when_called_twice():
    once = _renamespace_finding_ids("## F1\nsee F2", 1)
    twice = _renamespace_finding_ids(once, 1)
    assert once == twice == "## S1.F1\nsee S1.F2"


def test_does_not_mangle_midword_identifiers():
    # F1Score has a word char after the digit, so \b doesn't fire — must be left alone.
    assert _renamespace_finding_ids("def F1Score(): pass", 1) == "def F1Score(): pass"
    # Prefix-word context (e.g. RF1) must also be left alone.
    assert _renamespace_finding_ids("see RF1 elsewhere", 1) == "see RF1 elsewhere"


def test_no_double_prefix_on_heading():
    # Regression test for the original two-pass bug.
    out = _renamespace_finding_ids("## F1", 1)
    assert out == "## S1.F1"
    assert "S1.S1" not in out
