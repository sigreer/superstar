from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_resolve_mode_round_1_auto_is_broad():
    assert er.resolve_mode("auto", round_num=1) == "broad"


def test_resolve_mode_round_n_auto_is_incremental():
    assert er.resolve_mode("auto", round_num=2) == "incremental"
    assert er.resolve_mode("auto", round_num=5) == "incremental"


def test_resolve_mode_explicit_broad_round_n():
    assert er.resolve_mode("broad", round_num=3) == "broad"


def test_resolve_mode_incremental_round_1_raises():
    import pytest
    with pytest.raises(ValueError):
        er.resolve_mode("incremental", round_num=1)
