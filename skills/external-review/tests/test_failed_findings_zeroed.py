"""Regression: failed primary reviewer must record findings_count=0 even if
its stderr (or stdout) body contains finding-shaped markdown like `## F1`
with `Severity: blocking`. Spec requires findings_count=0 when returncode!=0.
"""
from pathlib import Path
import os
import subprocess
import sys
import json

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


FAKE_FAILED_WITH_FINDING_SHAPED_STDERR = """#!/usr/bin/env bash
# Echo finding-shaped markdown on stderr, then exit non-zero. The script
# must NOT trust this content for findings counting.
cat 1>&2 <<'EOF'
Reading prompt from stdin...
1. Findings

## F1
Severity: blocking
Some failure-mode echo.

## F2
Severity: important
Another echoed finding.

5. Overall verdict: revise
EOF
exit 2
"""


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    return repo


def test_failed_reviewer_findings_forced_to_zero(tmp_path):
    repo = _init_repo(tmp_path)
    reviewer = repo / "fake.sh"
    reviewer.write_text(FAKE_FAILED_WITH_FINDING_SHAPED_STDERR)
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert payload["verdict_valid"] is False
    # Spec: failed reviewers must record findings_count = 0.
    assert payload["findings_count"] == 0, payload
    assert payload["blocking_findings_count"] == 0, payload

    # And chain.json must reflect the same truth.
    chain_dirs = list((repo / "docs" / "reviewer").glob("plan-*"))
    assert chain_dirs, "expected a chain dir"
    chain_json = chain_dirs[0] / "chain.json"
    manifest = json.loads(chain_json.read_text())
    last_round = manifest["rounds"][-1]
    assert last_round["status"] == "failed"
    assert last_round["findings_count"] == 0, last_round
    assert last_round["blocking_findings_count"] == 0, last_round
