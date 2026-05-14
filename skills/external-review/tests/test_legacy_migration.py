from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_synthesize_manifest_from_legacy_files(tmp_path):
    d = tmp_path / "old-chain"; d.mkdir()
    (d / "r1-2026-04-01T0900-request.md").write_text("prompt body")
    (d / "r1-2026-04-01T0905-response.md").write_text(
        "## F1\nSeverity: blocking\n\nOverall verdict: revise\n"
    )
    (d / "r2-2026-04-02T1200-request.md").write_text("prompt body 2")

    manifest = er.synthesize_legacy_manifest(
        chain_dir=d, chain="old-chain", kind="post-slice",
        target="docs/plans/old.md", work_id="P1.S1",
    )

    assert manifest["legacy_migrated"] is True
    assert manifest["work_id"] == "P1.S1"
    assert len(manifest["rounds"]) == 2
    r1, r2 = manifest["rounds"]
    assert r1["legacy"] is True
    assert r1["verdict"] == "revise"
    assert r1["verdict_valid"] is True
    assert r1["findings_count"] == 1
    assert r1["blocking_findings_count"] == 1
    assert r1["head_sha_after_round"] is None
    assert r2["response"] is None  # only request file existed
