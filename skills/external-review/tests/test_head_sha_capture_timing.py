"""F3: head_sha_at_request must be captured before the reviewer runs,
and head_sha_after_round captured after. If the reviewer mutates repo
state (e.g., creates a commit), the two fields must differ."""
from pathlib import Path
import subprocess, sys, json, os


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


# Reviewer stub: makes a commit in the repo, then emits a verdict.
FAKE_REVIEWER_THAT_COMMITS = """#!/usr/bin/env bash
set -e
# Mutate repo state mid-review: write a file and commit it.
echo "side-effect" > side-effect.txt
git add side-effect.txt
git -c user.email=stub@stub -c user.name=stub commit -q -m "reviewer side effect"
cat <<'EOF'
## F1
Severity: blocking
Stub finding.

Overall verdict: revise
EOF
"""


def test_head_sha_captured_before_and_after_reviewer(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    sha_before = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    reviewer = repo / "stub-reviewer.sh"
    reviewer.write_text(FAKE_REVIEWER_THAT_COMMITS)
    reviewer.chmod(0o755)

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr

    sha_after = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert sha_before != sha_after, "stub should have created a new commit"

    chain_dir = repo / "docs" / "reviewer" / "plan-plan"
    manifest = json.loads((chain_dir / "chain.json").read_text())
    round_entry = manifest["rounds"][0]

    assert round_entry["head_sha_at_request"] == sha_before, (
        "head_sha_at_request must reflect HEAD before the reviewer ran"
    )
    assert round_entry["head_sha_after_round"] == sha_after, (
        "head_sha_after_round must reflect HEAD after the reviewer ran"
    )
    assert round_entry["head_sha_at_request"] != round_entry["head_sha_after_round"]
