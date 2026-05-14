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


def test_explicit_empty_findings_heading_returns_zero():
    body = "## Findings\nnone\n\nOverall verdict: ready"
    n, blocking = er.parse_findings(body)
    assert n == 0
    assert blocking == 0


def test_explicit_findings_none_inline_returns_zero():
    body = "Findings: none\n\nOverall verdict: ready"
    n, blocking = er.parse_findings(body)
    assert n == 0
    assert blocking == 0


def test_prose_without_finding_ids_returns_none():
    # Per spec: body present, no crash sentinel, no recognised finding form,
    # no explicit-empty marker -> unparseable -> coordinator inspects prose.
    body = "This response has prose but no F IDs. Overall verdict: revise"
    n, blocking = er.parse_findings(body)
    assert n is None
    assert blocking is None


def test_crash_sentinel_returns_none():
    body = "Reviewer crashed: connection reset"
    n, blocking = er.parse_findings(body)
    assert n is None
    assert blocking is None


def test_prose_style_findings_counted():
    body = (
        "1. Findings\n\n"
        "F1. Blocking: the live entrypoint is broken. See file.py:43.\n\n"
        "F2. Blocking: the post-slice gate is not clean.\n\n"
        "F3. Important: head_sha is captured at the wrong time.\n\n"
        "Overall verdict: revise\n"
    )
    n, blocking = er.parse_findings(body)
    assert n == 3
    assert blocking == 2


def test_crash_phrase_in_quoted_content_does_not_block_parse():
    body = (
        "1. Findings\n\n"
        "F1. Blocking: the parser misbehaves when the body contains the\n"
        "string `\"reviewer crashed\"` inside a fenced excerpt:\n\n"
        "```python\n"
        "if 'reviewer crashed' in text.lower():\n"
        "    return None, None\n"
        "```\n\n"
        "F2. Important: cover this with a regression test.\n\n"
        "Overall verdict: revise\n"
    )
    n, blocking = er.parse_findings(body)
    assert n == 2
    assert blocking == 1
