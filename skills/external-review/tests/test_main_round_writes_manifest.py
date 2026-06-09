from pathlib import Path
import subprocess, sys, json, importlib.util, os

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


FAKE_REVIEWER = """#!/usr/bin/env bash
cat <<'EOF'
## F1
Severity: blocking
Stub finding.

Overall verdict: revise
EOF
"""


def test_main_writes_manifest_entry(tmp_path, monkeypatch):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    reviewer = repo / "stub-reviewer.sh"
    reviewer.write_text(FAKE_REVIEWER); reviewer.chmod(0o755)

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json",
         "--no-preflight"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert payload["verdict"] == "revise"
    assert payload["verdict_valid"] is True
    assert payload["round"] == 1

    chain_dir = repo / "docs" / "reviewer" / "plan-plan"
    manifest = json.loads((chain_dir / "chain.json").read_text())
    assert manifest["schema_version"] == 1
    assert len(manifest["rounds"]) == 1
    assert manifest["rounds"][0]["verdict"] == "revise"
