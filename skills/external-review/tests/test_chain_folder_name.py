from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_post_slice_includes_work_id_dotless(tmp_path):
    target = tmp_path / "2026-05-13-feature-plan.md"; target.write_text("x")
    assert er.chain_folder_name(target, "post-slice", "P2.S3") == "feature-plan-P2-S3-post-slice"


def test_post_phase_phase_id(tmp_path):
    target = tmp_path / "feature.md"; target.write_text("x")
    assert er.chain_folder_name(target, "post-phase", "P2") == "feature-P2-post-phase"


def test_spec_ignores_work_id(tmp_path):
    target = tmp_path / "feature.md"; target.write_text("x")
    assert er.chain_folder_name(target, "spec", "P2.S3") == "feature-spec"


def test_no_work_id_for_spec_unchanged(tmp_path):
    target = tmp_path / "feature.md"; target.write_text("x")
    assert er.chain_folder_name(target, "spec", None) == "feature-spec"
