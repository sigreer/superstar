from pathlib import Path
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def _setup(tmp_path):
    target = tmp_path / "plan.md"; target.write_text("# plan\nbody\n")
    ctx1 = tmp_path / "spec.md"; ctx1.write_text("# spec\nx\n")
    ctx2 = tmp_path / "TASKLIST.md"; ctx2.write_text("# tasks\ny\n")
    return target, [ctx1, ctx2]


def test_broad_mode_includes_context_previews(tmp_path, monkeypatch):
    target, context = _setup(tmp_path)
    monkeypatch.chdir(tmp_path)
    out = er.make_prompt(
        root=tmp_path, target=target, kind="plan",
        context=context, max_lines=10, mode="broad",
        incremental_preamble=None,
    )
    assert "## Context Previews" in out


def test_incremental_mode_excludes_context_previews(tmp_path, monkeypatch):
    target, context = _setup(tmp_path)
    monkeypatch.chdir(tmp_path)
    out = er.make_prompt(
        root=tmp_path, target=target, kind="plan",
        context=context, max_lines=10, mode="incremental",
        incremental_preamble="prior preamble",
    )
    assert "## Context Previews" not in out
    # Context files are still NAMED in the preamble or body.
    assert "spec.md" in out
    assert "TASKLIST.md" in out
