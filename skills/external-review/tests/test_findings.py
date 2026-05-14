from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_heading_findings_counted():
    body = "## F1\nSeverity: blocking\n\n## F2\nSeverity: minor\n\n## F3\nSeverity: blocking"
    n, blocking = er.parse_findings(body)
    assert n == 3
    assert blocking == 2


def test_bullet_findings_counted():
    body = "- F1: something blocking (blocking)\n- F2 minor thing"
    n, blocking = er.parse_findings(body)
    assert n == 2
    assert blocking == 1


def test_no_findings_returns_zero():
    body = "Overall verdict: ready\n\nNo findings."
    n, blocking = er.parse_findings(body)
    assert n == 0
    assert blocking == 0


def test_unparseable_returns_none():
    body = "Reviewer crashed: connection reset"
    n, blocking = er.parse_findings(body)
    assert n is None
    assert blocking is None
