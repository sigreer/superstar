from pathlib import Path
import sys, importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_verdict_ready():
    v, valid = er.parse_verdict("Findings: ok\n\nOverall verdict: ready\n")
    assert v == "ready"
    assert valid is True


def test_verdict_ready_with_small_edits_markdown():
    body = "**Overall verdict:** `ready with small edits`."
    v, valid = er.parse_verdict(body)
    assert v == "ready with small edits"
    assert valid is True


def test_verdict_revise_case_insensitive():
    v, valid = er.parse_verdict("OVERALL VERDICT: Revise")
    assert v == "revise"
    assert valid is True


def test_verdict_takes_last_match():
    body = "Overall verdict: ready\n\n...later...\n\nOverall verdict: revise"
    v, valid = er.parse_verdict(body)
    assert v == "revise"


def test_verdict_unknown_returns_invalid():
    v, valid = er.parse_verdict("Overall verdict: looks fine to me")
    assert v is None
    assert valid is False


def test_verdict_missing_returns_invalid():
    v, valid = er.parse_verdict("Some review prose with no verdict line.")
    assert v is None
    assert valid is False


from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_bare_verdict_ready_with_small_edits():
    v, valid = er.parse_verdict("**Verdict: ready with small edits.**")
    assert v == "ready with small edits"
    assert valid is True


def test_bare_verdict_revise():
    v, valid = er.parse_verdict("**Verdict: revise.**")
    assert v == "revise"
    assert valid is True


def test_bare_verdict_not_matched_in_prose():
    body = "the previous round's verdict was revise, but this is just narrative.\n"
    v, valid = er.parse_verdict(body)
    assert v is None
    assert valid is False


def test_overall_preferred_over_bare():
    body = (
        "**Verdict: revise**\n\n"
        "...more prose...\n\n"
        "Overall verdict: ready\n"
    )
    v, valid = er.parse_verdict(body)
    assert v == "ready"
    assert valid is True


def test_bare_verdict_rejects_extra_words_after_value():
    v, valid = er.parse_verdict("**Verdict: ready for review**")
    assert v is None
    assert valid is False


def test_bare_verdict_rejects_hyphenated_value():
    v, valid = er.parse_verdict("Verdict: ready-ish")
    assert v is None
    assert valid is False


def test_bare_verdict_rejects_qualified_value():
    v, valid = er.parse_verdict("Verdict: ready with small edits pending changes")
    assert v is None
    assert valid is False


def test_bare_verdict_rejects_contradictory_same_line_prose():
    v, valid = er.parse_verdict("**Verdict: ready. Important findings remain unresolved.**")
    assert v is None
    assert valid is False


def test_bare_verdict_rejects_benign_same_line_prose():
    body = "**Verdict: ready with small edits.** Full review written to /tmp/foo.md."
    v, valid = er.parse_verdict(body)
    assert v is None
    assert valid is False


def test_parse_reformatted_verdict_helper():
    raw = "## Overall Verdict\n\n**revise** — text\n"
    v, valid = er.parse_reformatted_verdict(raw)
    assert v == "revise"
    assert valid is True


def test_parse_reformatted_verdict_fixture_bare():
    raw = (FIXTURES / "claude-bare-verdict-ready-with-small-edits.md").read_text()
    v, valid = er.parse_reformatted_verdict(raw)
    assert v == "ready with small edits"
    assert valid is True


def test_parse_reformatted_verdict_fixture_heading():
    raw = (FIXTURES / "claude-heading-revise.md").read_text()
    v, valid = er.parse_reformatted_verdict(raw)
    assert v == "revise"
    assert valid is True
