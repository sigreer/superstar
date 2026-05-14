from pathlib import Path
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def _r(role, idx, body, returncode):
    return er.ReviewerResult(
        role=role, sweep_index=idx,
        request_path=Path("/tmp/req"), response_path=Path("/tmp/resp"),
        review_body=body,
        verdict="revise" if returncode == 0 else None,
        verdict_valid=(returncode == 0),
        returncode=returncode,
    )


def test_failed_sweep_excluded_from_merged_findings(tmp_path):
    primary = _r("primary", None, "## F1\nSeverity: blocking\nReal primary finding.\n", 0)
    bad_sweep = _r("sweep", 1, "ECHOED PROMPT TEXT WITH FAKE VERDICT", 1)
    path = er.write_merged_findings(
        chain_dir=tmp_path, round_num=1, primary=primary, sweeps=[bad_sweep],
    )
    content = path.read_text()
    assert "Real primary finding" in content
    assert "ECHOED PROMPT TEXT" not in content
    # The "## Sweep 1" heading should not appear because the sweep was failed.
    assert "## Sweep 1" not in content


def test_all_failed_writes_no_merged_findings(tmp_path):
    primary = _r("primary", None, "bad", 1)
    sweep = _r("sweep", 1, "bad", 1)
    path = er.write_merged_findings(
        chain_dir=tmp_path, round_num=1, primary=primary, sweeps=[sweep],
    )
    assert path is None
