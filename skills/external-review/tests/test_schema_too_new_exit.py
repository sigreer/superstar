"""Exit code 4: chain.json schema_version newer than the script supports."""
from pathlib import Path
import json
import os
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    reviewer = repo / "stub.sh"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)
    return repo


def test_schema_too_new_returns_exit_4(tmp_path):
    repo = _init_repo(tmp_path)
    chain_dir = repo / "docs" / "reviewer" / "plan-spec"
    chain_dir.mkdir(parents=True)
    manifest_path = chain_dir / "chain.json"
    manifest_path.write_text(json.dumps({"schema_version": 99, "rounds": []}))

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    r = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "external-reviewer.py"),
            "review",
            "--kind",
            "spec",
            "--file",
            "plan.md",
            "--emit",
            "json",
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 4, f"stdout={r.stdout!r} stderr={r.stderr!r}"
    assert "schema_version" in r.stderr
    assert "chain.json" in r.stderr
