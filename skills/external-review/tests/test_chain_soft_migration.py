from pathlib import Path
import os, subprocess, sys, json, importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def _init(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    return repo


def test_legacy_chain_entries_treated_as_unknown(tmp_path):
    repo = _init(tmp_path)
    chain_dir = repo / "docs" / "reviewer" / "plan-plan"
    chain_dir.mkdir(parents=True)
    # Hand-write a pre-S1 chain.json: one round with no returncode/status.
    legacy = {
        "schema_version": 1,
        "chain": "plan-plan",
        "kind": "plan",
        "target": "plan.md",
        "work_id": None,
        "legacy_migrated": False,
        "rounds": [{
            "round": 1,
            "reviewers": [{
                "role": "primary", "sweep_group": None, "parent_round": 1,
                "request": "r1-request.md", "response": "r1-response.md",
                "verdict": "revise", "verdict_valid": True,
            }],
            "merged_verdict": "revise",
            "merged_findings": None,
            "request": "r1-request.md",
            "response": "r1-response.md",
            "resolution": None,
            "resolution_parse_status": None,
            "resolution_waiver": False,
            "head_sha_at_request": None,
            "head_sha_after_round": None,
            "worktree_dirty_at_request": False,
            "verdict": "revise",
            "verdict_valid": True,
            "findings_count": 1,
            "blocking_findings_count": 1,
            "base_ref": None,
            "base_ref_source": None,
            "diff_included": False,
        }],
        "sweep_checkpoints": {"first-round": "pending", "final-ready": "pending"},
    }
    (chain_dir / "chain.json").write_text(json.dumps(legacy))
    (chain_dir / "r1-response.md").write_text("# old response\nOverall verdict: revise\n")
    (chain_dir / "r1-request.md").write_text("old request")

    loaded = er.read_manifest(chain_dir / "chain.json")
    er.migrate_manifest_inplace(loaded)
    round1 = loaded["rounds"][0]
    assert round1.get("status") == "unknown"
    assert round1.get("returncode") is None
    assert round1["reviewers"][0]["status"] == "unknown"
    assert round1["reviewers"][0]["returncode"] is None


def test_synthesized_legacy_manifest_marks_rounds_unknown(tmp_path):
    """Chain with on-disk r1-* artifacts but no chain.json: synthesize + migrate."""
    repo = _init(tmp_path)
    chain_dir = repo / "docs" / "reviewer" / "plan-plan"
    chain_dir.mkdir(parents=True)
    (chain_dir / "r1-2025-01-01T0000-request.md").write_text("legacy request")
    (chain_dir / "r1-2025-01-01T0000-response.md").write_text(
        "# old response\nOverall verdict: revise\n"
    )

    import os, subprocess, sys
    reviewer = repo / "ok.sh"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json",
         "--allow-missing-resolution"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr

    manifest = json.loads((chain_dir / "chain.json").read_text())
    rounds = manifest["rounds"]
    assert len(rounds) == 2
    assert rounds[0]["round"] == 1 and rounds[0]["status"] == "unknown"
    assert rounds[0]["returncode"] is None
    assert rounds[1]["status"] == "ok"
