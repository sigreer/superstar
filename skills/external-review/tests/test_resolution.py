from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


SAMPLE = """# Resolution for r1

## F1
Status: fixed
Evidence:
- Commit: abc1234
- Verification: pytest passed

Notes:
Did the thing.

## F2
Status: waived
Evidence:
- No code change
"""


def test_parse_resolution_extracts_statuses():
    result = er.parse_resolution(SAMPLE)
    assert result.status == "ok"
    assert result.findings == {"F1": "fixed", "F2": "waived"}


def test_parse_resolution_partial_when_missing_status():
    body = "## F1\nNotes only, no Status line"
    result = er.parse_resolution(body)
    assert result.status == "partial"
    assert "F1" in result.unmatched


def test_parse_resolution_unparseable_when_no_headings():
    body = "just prose, no headings"
    result = er.parse_resolution(body)
    assert result.status == "unparseable"
    assert result.findings == {}
