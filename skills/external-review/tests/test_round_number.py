from pathlib import Path
import json, sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_no_chain_dir_round_is_one(tmp_path):
    assert er.next_round_number(tmp_path / "absent") == 1


def test_manifest_present_takes_precedence(tmp_path):
    d = tmp_path / "chain"; d.mkdir()
    er.write_manifest(d / "chain.json", {
        "schema_version": 1, "rounds": [{"round": 1}, {"round": 2}]
    })
    assert er.next_round_number(d) == 3


def test_legacy_dir_no_manifest_falls_back_to_filename_scan(tmp_path):
    d = tmp_path / "chain"; d.mkdir()
    (d / "r1-2026-05-01T0900-request.md").write_text("")
    (d / "r2-2026-05-02T0900-request.md").write_text("")
    assert er.next_round_number(d) == 3
