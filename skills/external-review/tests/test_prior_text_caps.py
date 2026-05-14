from pathlib import Path
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def test_cap_with_elision_passthrough_small():
    text = "small body"
    assert er.cap_with_elision(text, max_bytes=1000) == text


def test_cap_with_elision_truncates_large():
    text = "X" * 200_000
    out = er.cap_with_elision(text, max_bytes=80 * 1024)
    assert len(out.encode("utf-8")) <= 80 * 1024 + 200  # marker scaffolding
    assert "bytes elided" in out


def test_preamble_caps_prior_response_text(tmp_path):
    # 200 KB merged findings → must be capped to ≤ 80 KB in the preamble.
    big = tmp_path / "r1-merged-findings.md"
    big.write_text("M" * 200_000)
    manifest = {
        "chain": "demo",
        "rounds": [{
            "round": 1, "status": "ok",
            "verdict": "revise", "verdict_valid": True,
            "merged_verdict": "revise",
            "findings_count": 1, "blocking_findings_count": 1,
            "response": "r1-response.md",
            "merged_findings": "r1-merged-findings.md",
        }],
    }
    out = er.build_incremental_preamble(
        manifest=manifest, chain_dir=tmp_path, round_num=2,
        resolution_waiver=False, legacy_first_round=False, diff_section="",
    )
    # The total preamble text contains the capped merged-findings inline.
    # Assert "M" sequence is shorter than the raw 200 KB and that the elision
    # marker is present.
    assert len(out) < 200_000
    assert "bytes elided" in out
