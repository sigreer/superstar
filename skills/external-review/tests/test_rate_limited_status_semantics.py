import json, os, subprocess, sys
from pathlib import Path
import datetime as dt
import importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "rs.json"))


def test_resolution_gate_bypasses_on_rate_limited_prior(tmp_path):
    """post-slice r2 must NOT demand a resolution doc if r1 was rate-limited."""
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    chain_dir = repo / "docs/reviewer/plan-X-post-slice"
    chain_dir.mkdir(parents=True)
    (chain_dir / "chain.json").write_text(json.dumps({
        "schema_version": 1, "chain": "plan-X-post-slice", "kind": "post-slice",
        "target": "plan.md", "work_id": "X", "legacy_migrated": False,
        "rounds": [{
            "round": 1, "status": "rate-limited", "verdict": None, "verdict_valid": False,
            "merged_verdict": None, "returncode": None,
        }],
        "sweep_checkpoints": {"first-round": "pending", "final-ready": "pending"},
    }))

    reviewer = repo / "fake.sh"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "rs.json")

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--file", "plan.md", "--work-id", "X", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr


def test_preamble_walks_back_past_rate_limited(tmp_path):
    """build_incremental_preamble should skip rate-limited rounds when finding
    the last trusted round, just like it does for failed/unknown."""
    chain_dir = tmp_path / "chain"; chain_dir.mkdir()
    (chain_dir / "r1-merged-findings.md").write_text("trusted r1 findings F1: ...\n")
    manifest = {
        "schema_version": 1, "chain": "demo", "kind": "post-slice", "target": "x",
        "work_id": None, "legacy_migrated": False,
        "rounds": [
            {"round": 1, "status": "ok", "verdict": "revise", "verdict_valid": True,
             "merged_verdict": "revise", "findings_count": 1, "blocking_findings_count": 1,
             "response": "r1-response.md", "merged_findings": "r1-merged-findings.md"},
            {"round": 2, "status": "rate-limited", "verdict": None, "verdict_valid": False,
             "merged_verdict": None, "returncode": None},
        ],
        "sweep_checkpoints": {"first-round": "done", "final-ready": "pending"},
    }
    out = er.build_incremental_preamble(
        manifest=manifest, chain_dir=chain_dir, round_num=3,
        resolution_waiver=True, legacy_first_round=False, diff_section="",
    )
    # Trusted round is r1 — its merged findings are embedded.
    assert "trusted r1 findings" in out
    # Annotation about skipped rounds mentions rate-limited
    assert "rounds 2..2 were" in out or "rate-limited" in out.lower()


def test_merged_verdict_excludes_rate_limited_reviewers():
    """If primary is ok and a sweep is rate-limited, merged verdict comes from primary only."""
    reviewers = [
        {"role": "primary", "verdict": "ready", "verdict_valid": True, "returncode": 0, "status": "ok"},
        {"role": "sweep",   "verdict": None,    "verdict_valid": False, "returncode": None, "status": "rate-limited"},
    ]
    merged = er.compute_merged_verdict(reviewers)
    assert merged == "ready"


def test_merged_verdict_all_rate_limited_returns_none():
    reviewers = [
        {"role": "primary", "verdict": None, "verdict_valid": False, "returncode": None, "status": "rate-limited"},
        {"role": "sweep",   "verdict": None, "verdict_valid": False, "returncode": None, "status": "rate-limited"},
    ]
    assert er.compute_merged_verdict(reviewers) is None


def test_write_merged_findings_returns_none_when_all_rate_limited(tmp_path):
    """If every reviewer in the round is rate-limited, no merged file is written."""
    primary = {
        "role": "primary", "sweep_index": None, "status": "rate-limited",
        "returncode": None, "review_body": "", "verdict": None, "verdict_valid": False,
    }
    sweeps = [{
        "role": "sweep", "sweep_index": 1, "status": "rate-limited",
        "returncode": None, "review_body": "", "verdict": None, "verdict_valid": False,
    }]
    out_path = er.write_merged_findings(
        chain_dir=tmp_path, round_num=1, primary=primary, sweeps=sweeps,
    )
    assert out_path is None
    assert not (tmp_path / "r1-merged-findings.md").exists()


def test_write_merged_findings_excludes_rate_limited_sweep(tmp_path):
    """When primary is ok and a sweep is rate-limited, sweep is excluded from merge."""
    primary = {
        "role": "primary", "sweep_index": None, "status": "ok",
        "returncode": 0, "review_body": "primary review body\n",
        "verdict": "ready", "verdict_valid": True,
    }
    sweeps = [{
        "role": "sweep", "sweep_index": 1, "status": "rate-limited",
        "returncode": None, "review_body": "should-not-appear",
        "verdict": None, "verdict_valid": False,
    }]
    out_path = er.write_merged_findings(
        chain_dir=tmp_path, round_num=1, primary=primary, sweeps=sweeps,
    )
    assert out_path is not None
    assert out_path.exists()
    body = out_path.read_text()
    assert "primary review body" in body
    assert "should-not-appear" not in body
    assert "Sweep 1" not in body
