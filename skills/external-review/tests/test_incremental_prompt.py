from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_incremental_preamble_includes_chain_summary_and_resolution(tmp_path):
    manifest = {
        "schema_version": 1, "chain": "demo-P1-S1-post-slice",
        "rounds": [
            {"round": 1, "verdict": "revise", "verdict_valid": True,
             "findings_count": 3, "blocking_findings_count": 1,
             "response": "r1-response.md"},
        ],
    }
    chain_dir = tmp_path / "chain"; chain_dir.mkdir()
    (chain_dir / "r1-response.md").write_text("## F1\nSeverity: blocking\nOverall verdict: revise")
    (chain_dir / "r1-resolution.md").write_text("# Resolution for r1\n\n## F1\nStatus: fixed\n")

    preamble = er.build_incremental_preamble(
        manifest=manifest, chain_dir=chain_dir, round_num=2,
        resolution_waiver=False, legacy_first_round=False,
    )

    assert "round 2 of demo-P1-S1-post-slice" in preamble
    assert "F1" in preamble
    assert "Resolution report" in preamble
    assert "Status: fixed" in preamble


def test_incremental_preamble_with_waiver_text(tmp_path):
    manifest = {"chain": "demo", "rounds": [{"round": 1, "response": "r1-response.md", "verdict": "revise", "verdict_valid": True}]}
    chain_dir = tmp_path / "chain"; chain_dir.mkdir()
    (chain_dir / "r1-response.md").write_text("Overall verdict: revise")
    preamble = er.build_incremental_preamble(
        manifest=manifest, chain_dir=chain_dir, round_num=2,
        resolution_waiver=True, legacy_first_round=False,
    )
    assert "MISSING — explicitly waived" in preamble
