from pathlib import Path
import json
import os
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    (repo / "plan.md").write_text("# Plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    reviewer = repo / "fake-reviewer.sh"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)
    return repo, reviewer


def test_manifest_records_provider_and_sandbox(tmp_path):
    repo, reviewer = _repo(tmp_path)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "state.json")
    result = subprocess.run(
        [
            sys.executable, str(SCRIPTS / "external-reviewer.py"),
            "review", "--kind", "post-slice", "--work-id", "P1.S1",
            "--file", "plan.md", "--emit", "json",
            "--no-preflight",
        ],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    chain = repo / "docs" / "reviewer" / "plan-P1-S1-post-slice"
    manifest = json.loads((chain / "chain.json").read_text())
    reviewer_entry = manifest["rounds"][0]["reviewers"][0]
    assert reviewer_entry["provider"] == "custom"
    assert reviewer_entry["sandbox"]["repo_root"] == str(repo)
    assert reviewer_entry["sandbox"]["mode"] == "custom"
    assert reviewer_entry["sandbox"]["response_dir"].endswith(".reviewer-output/r1-primary")
    assert "scratch_dir" in reviewer_entry["sandbox"]


def test_response_artifact_mentions_provider_and_sandbox(tmp_path):
    repo, reviewer = _repo(tmp_path)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "state.json")
    result = subprocess.run(
        [
            sys.executable, str(SCRIPTS / "external-reviewer.py"),
            "review", "--kind", "spec", "--file", "plan.md", "--emit", "json",
            "--no-preflight",
        ],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    response_text = (repo / payload["review_path"]).read_text()
    assert "- Reviewer provider: `custom`" in response_text
    assert "- Sandbox: " in response_text
