from pathlib import Path
import subprocess
import sys
import os
import json

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _repo(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    rev = repo / "stub.sh"
    rev.write_text(
        "#!/usr/bin/env bash\n"
        "echo \"## F1\nSeverity: minor\nOverall verdict: ready with small edits\"\n"
    )
    rev.chmod(0o755)
    return repo


def test_thorough_round_1_writes_primary_and_sweep_files(tmp_path):
    repo = _repo(tmp_path)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    r = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "external-reviewer.py"),
            "review",
            "--kind",
            "post-slice",
            "--work-id",
            "P1.S1",
            "--file",
            "plan.md",
            "--review-depth",
            "thorough",
            "--emit",
            "json",
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, r.stderr

    chain = repo / "docs" / "reviewer" / "plan-P1-S1-post-slice"
    primary = list(chain.glob("r1-*-primary-response.md"))
    sweeps = list(chain.glob("r1-*-sweep1-response.md"))
    merged = chain / "r1-merged-findings.md"
    assert primary
    assert sweeps
    assert merged.exists()

    payload = json.loads(r.stdout)
    assert payload["review_depth"] == "thorough"
    assert len(payload["reviewers"]) == 2
    assert payload["reviewers"][0]["role"] == "primary"
    assert payload["reviewers"][1]["role"] == "sweep"
    assert payload["merged_findings_path"] is not None


def test_standard_depth_keeps_original_filenames_and_single_reviewer(tmp_path):
    repo = _repo(tmp_path)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    r = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "external-reviewer.py"),
            "review",
            "--kind",
            "post-slice",
            "--work-id",
            "P1.S1",
            "--file",
            "plan.md",
            "--emit",
            "json",
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, r.stderr

    chain = repo / "docs" / "reviewer" / "plan-P1-S1-post-slice"
    # No namespaced files at standard depth.
    assert not list(chain.glob("r1-*-primary-response.md"))
    assert not list(chain.glob("r1-*-sweep*-response.md"))
    # Original filenames present.
    assert list(chain.glob("r1-*-response.md"))
    assert not (chain / "r1-merged-findings.md").exists()

    payload = json.loads(r.stdout)
    assert payload["review_depth"] == "standard"
    assert len(payload["reviewers"]) == 1
    assert payload["reviewers"][0]["role"] == "primary"
    assert payload["merged_findings_path"] is None
    assert payload["merged_verdict"] == payload["verdict"]
