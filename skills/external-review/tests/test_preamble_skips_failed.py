from pathlib import Path
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def _round(n, status, verdict="revise", merged="r-merged.md", response="r-response.md", findings=1, blocking=0):
    return {
        "round": n, "status": status,
        "merged_verdict": verdict, "verdict": verdict, "verdict_valid": True,
        "findings_count": findings, "blocking_findings_count": blocking,
        "response": response, "merged_findings": merged,
    }


def test_preamble_walks_back_past_failed(tmp_path):
    (tmp_path / "r1-merged-findings.md").write_text("REAL R1 FINDINGS")
    (tmp_path / "r2-2026-response.md").write_text("ECHOED PROMPT GARBAGE")
    manifest = {
        "chain": "demo", "rounds": [
            _round(1, "ok", merged="r1-merged-findings.md"),
            _round(2, "failed", verdict=None, response="r2-2026-response.md", merged=None),
        ],
    }
    out = er.build_incremental_preamble(
        manifest=manifest, chain_dir=tmp_path, round_num=3,
        resolution_waiver=False, legacy_first_round=False, diff_section="",
    )
    assert "REAL R1 FINDINGS" in out
    assert "ECHOED PROMPT GARBAGE" not in out
    assert "skipped" in out.lower()


def test_preamble_walks_back_past_unknown(tmp_path):
    (tmp_path / "r1-response.md").write_text("LEGACY OF DUBIOUS ORIGIN")
    (tmp_path / "r2-merged-findings.md").write_text("REAL R2 FINDINGS")
    manifest = {
        "chain": "demo", "rounds": [
            _round(1, "unknown", response="r1-response.md", merged=None),
            _round(2, "ok", merged="r2-merged-findings.md"),
        ],
    }
    out = er.build_incremental_preamble(
        manifest=manifest, chain_dir=tmp_path, round_num=3,
        resolution_waiver=False, legacy_first_round=False, diff_section="",
    )
    assert "REAL R2 FINDINGS" in out
    assert "LEGACY OF DUBIOUS ORIGIN" not in out


def test_preamble_no_successful_prior_round(tmp_path):
    (tmp_path / "r1-response.md").write_text("ECHO")
    manifest = {
        "chain": "demo", "rounds": [
            _round(1, "failed", verdict=None, response="r1-response.md", merged=None),
        ],
    }
    out = er.build_incremental_preamble(
        manifest=manifest, chain_dir=tmp_path, round_num=2,
        resolution_waiver=False, legacy_first_round=False, diff_section="",
    )
    assert "ECHO" not in out
    assert "no prior review available" in out.lower() or "no successful prior" in out.lower()
