from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_substitute_all_new_placeholders(tmp_path):
    chain_dir = tmp_path / "chain"; chain_dir.mkdir()
    prev = chain_dir / "r1-response.md"; prev.write_text("x")
    res = chain_dir / "r1-resolution.md"; res.write_text("y")
    session = chain_dir / "session.state"

    out = er.expand_command_template(
        "echo {chain_dir} {round} {previous_response} {resolution_file} {session_file}",
        prompt_file=chain_dir / "r2-request.md",
        prompt_text="prompt",
        target_file=Path("plan.md"),
        kind="post-slice",
        chain_dir=chain_dir,
        round_num=2,
        previous_response=prev,
        resolution_file=res,
        session_file=session,
    )
    assert str(chain_dir) in out
    assert "2" in out
    assert str(prev) in out
    assert str(res) in out
    assert str(session) in out


def test_substitute_optional_placeholders_empty(tmp_path):
    chain_dir = tmp_path / "chain"; chain_dir.mkdir()
    session = chain_dir / "session.state"
    out = er.expand_command_template(
        "echo [{previous_response}] [{resolution_file}]",
        prompt_file=chain_dir / "r1-request.md",
        prompt_text="prompt",
        target_file=Path("plan.md"),
        kind="spec",
        chain_dir=chain_dir,
        round_num=1,
        previous_response=None,
        resolution_file=None,
        session_file=session,
    )
    assert "[]" in out
    # Confirm both are empty placeholders
    assert out.count("[]") == 2


def test_substitute_preserves_legacy_placeholders(tmp_path):
    chain_dir = tmp_path / "chain"; chain_dir.mkdir()
    session = chain_dir / "session.state"
    prompt_file = chain_dir / "r1-request.md"
    out = er.expand_command_template(
        "reviewer {prompt_file} --target {target_file} --kind {kind}",
        prompt_file=prompt_file,
        prompt_text="hello",
        target_file=Path("plan.md"),
        kind="plan",
        chain_dir=chain_dir,
        round_num=1,
        previous_response=None,
        resolution_file=None,
        session_file=session,
    )
    assert str(prompt_file) in out
    assert "plan.md" in out
    assert "plan" in out
