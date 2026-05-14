from pathlib import Path
import subprocess
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def _fake_result(returncode: int, stdout: str, stderr: str):
    return subprocess.CompletedProcess(
        args=["fake"], returncode=returncode, stdout=stdout, stderr=stderr,
    )


def test_success_stderr_with_full_prompt_echo_does_not_persist_prompt(tmp_path):
    """Success path: stderr containing the entire echoed prompt must not be written."""
    prompt_text = f"{er.PROMPT_SENTINEL_START}\n" + ("X" * 50_000) + f"\n{er.PROMPT_SENTINEL_END}"
    result = _fake_result(
        returncode=0,
        stdout="# Review\nactual review body\nOverall verdict: ready",
        stderr=f"banner line\n{prompt_text}\nmore banner",
    )
    response_path = tmp_path / "r1-response.md"
    prompt_path = tmp_path / "r1-request.md"
    prompt_path.write_text("ignored")
    target = tmp_path / "plan.md"
    target.write_text("ignored")
    er.write_review_artifact(
        root=tmp_path, target=target, kind="plan",
        command_template="fake", prompt_file=prompt_path,
        response_file=response_path, round_num=1, result=result,
    )
    body = response_path.read_text()
    assert er.PROMPT_SENTINEL_START not in body
    assert er.PROMPT_SENTINEL_END not in body
    assert "X" * 1000 not in body  # the 50 KB of echoed payload must not appear
    assert "actual review body" in body
    assert response_path.stat().st_size < 8 * 1024  # under 8 KB


def test_success_with_short_clean_stderr_keeps_tail_capped(tmp_path):
    """Success path: short stderr (no echo) may be retained but capped to 2 KB."""
    result = _fake_result(
        returncode=0,
        stdout="# Review\nbody\nOverall verdict: ready",
        stderr="harmless banner\nsession info\n",
    )
    response_path = tmp_path / "r1-response.md"
    prompt_path = tmp_path / "r1-request.md"
    prompt_path.write_text("ignored")
    target = tmp_path / "plan.md"
    target.write_text("ignored")
    er.write_review_artifact(
        root=tmp_path, target=target, kind="plan",
        command_template="fake", prompt_file=prompt_path,
        response_file=response_path, round_num=1, result=result,
    )
    body = response_path.read_text()
    assert "body" in body
    if "## Reviewer stderr (tail)" in body:
        tail = body.split("## Reviewer stderr (tail)", 1)[1]
        assert len(tail) <= 2 * 1024 + 200  # 200 bytes of fenced-block scaffolding
