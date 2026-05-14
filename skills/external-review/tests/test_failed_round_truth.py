from pathlib import Path
import os
import subprocess
import sys
import json
import importlib.util

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


FAKE_FAILED_WITH_ECHOED_VERDICT = """#!/usr/bin/env bash
# Echo a prompt-looking blob on stderr that contains plausible verdict text,
# then exit non-zero. This is the multistore failure mode.
cat 1>&2 <<'EOF'
Reading prompt from stdin...
OpenAI Codex v0.130.0
user
You are continuing an existing review chain.
... (echoed) ...
Overall verdict: revise
EOF
exit 1
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


def test_failed_reviewer_with_echoed_verdict_is_not_trusted(tmp_path):
    repo = _init_repo(tmp_path)
    reviewer = repo / "fake.sh"
    reviewer.write_text(FAKE_FAILED_WITH_ECHOED_VERDICT)
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    # Process should exit with the reviewer's non-zero code, not 0.
    assert result.returncode != 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["verdict_valid"] is False
    assert payload["verdict"] is None
    assert payload["status"] == "failed"
    assert payload["returncode"] != 0

    # Spec §S3 item 1: the manifest entry for a failed round must record
    # `merged_verdict: null`, and the persisted response file must be small
    # (under 8 KiB) since failed runs persist only a sanitised stderr tail.
    chain_dir = repo / "docs" / "reviewer" / "plan-plan"
    manifest = json.loads((chain_dir / "chain.json").read_text(encoding="utf-8"))
    last_round = manifest["rounds"][-1]
    assert last_round["merged_verdict"] is None, last_round

    response_name = last_round["reviewers"][0]["response"]
    response_path = chain_dir / response_name
    assert response_path.exists(), response_path
    size = response_path.stat().st_size
    assert size < 8 * 1024, f"failed-round response file too large: {size} bytes"
