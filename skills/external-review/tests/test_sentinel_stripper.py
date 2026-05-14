from pathlib import Path
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def test_strip_removes_full_marker_block():
    text = (
        "preamble\n"
        f"{er.PROMPT_SENTINEL_START}\nechoed prompt body\n{er.PROMPT_SENTINEL_END}\n"
        "actual review\n"
    )
    out = er.strip_prompt_echo(text)
    assert "echoed prompt body" not in out
    assert er.PROMPT_SENTINEL_START not in out
    assert er.PROMPT_SENTINEL_END not in out
    assert "preamble" in out
    assert "actual review" in out


def test_strip_end_only_deletes_from_start_of_stream():
    text = f"truncated echo tail here\n{er.PROMPT_SENTINEL_END}\nactual review\n"
    out = er.strip_prompt_echo(text)
    assert "truncated echo tail here" not in out
    assert er.PROMPT_SENTINEL_END not in out
    assert out.strip().startswith("actual review")


def test_strip_start_only_deletes_to_end_of_stream():
    text = f"preamble\n{er.PROMPT_SENTINEL_START}\nprompt body leaks to end\n"
    out = er.strip_prompt_echo(text)
    assert "prompt body leaks to end" not in out
    assert er.PROMPT_SENTINEL_START not in out
    assert out.strip() == "preamble"


def test_strip_no_markers_passes_text_through():
    text = "a clean review with no echo at all"
    assert er.strip_prompt_echo(text) == text


def test_strip_handles_empty_string():
    assert er.strip_prompt_echo("") == ""


def test_strip_handles_multiple_blocks():
    text = (
        f"head\n{er.PROMPT_SENTINEL_START}\nblock1\n{er.PROMPT_SENTINEL_END}\n"
        f"middle\n{er.PROMPT_SENTINEL_START}\nblock2\n{er.PROMPT_SENTINEL_END}\n"
        "tail"
    )
    out = er.strip_prompt_echo(text)
    assert "block1" not in out
    assert "block2" not in out
    assert "head" in out and "middle" in out and "tail" in out
