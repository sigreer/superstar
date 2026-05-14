from pathlib import Path
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def _setup(tmp_path, n_lines=600):
    target = tmp_path / "plan.md"
    target.write_text("\n".join(f"line {i}" for i in range(n_lines)) + "\n")
    return target


def test_broad_mode_target_preview_uses_max_lines(tmp_path, monkeypatch):
    target = _setup(tmp_path)
    monkeypatch.chdir(tmp_path)
    out = er.make_prompt(
        root=tmp_path, target=target, kind="plan", context=[],
        max_lines=600, mode="broad", incremental_preamble=None,
    )
    assert "line 500" in out  # broad mode renders up to max_lines


def test_incremental_mode_target_preview_trimmed_to_150(tmp_path, monkeypatch):
    target = _setup(tmp_path)
    monkeypatch.chdir(tmp_path)
    out = er.make_prompt(
        root=tmp_path, target=target, kind="plan", context=[],
        max_lines=600, mode="incremental", incremental_preamble="x",
    )
    assert "line 100" in out      # within trim window
    assert "line 200" not in out  # past 150-line trim
