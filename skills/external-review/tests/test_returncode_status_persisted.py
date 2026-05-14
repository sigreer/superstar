from pathlib import Path
import os, subprocess, sys, json, importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


FAKE_OK = """#!/usr/bin/env bash
echo "## F1"
echo "Severity: blocking"
echo "stub"
echo "Overall verdict: revise"
"""

FAKE_FAIL = """#!/usr/bin/env bash
echo "noise on stderr" 1>&2
exit 1
"""


def _init(tmp_path, reviewer_src):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    reviewer = repo / "fake.sh"; reviewer.write_text(reviewer_src); reviewer.chmod(0o755)
    return repo, reviewer


def _run(repo, reviewer):
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )


def test_ok_round_persists_status_and_returncode(tmp_path):
    repo, reviewer = _init(tmp_path, FAKE_OK)
    result = _run(repo, reviewer)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["returncode"] == 0
    manifest = json.loads((repo / "docs/reviewer/plan-plan/chain.json").read_text())
    round1 = manifest["rounds"][0]
    assert round1["status"] == "ok"
    assert round1["returncode"] == 0
    assert round1["reviewers"][0]["status"] == "ok"
    assert round1["reviewers"][0]["returncode"] == 0


def test_failed_round_persists_status_failed(tmp_path):
    repo, reviewer = _init(tmp_path, FAKE_FAIL)
    result = _run(repo, reviewer)
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert payload["returncode"] != 0
    assert payload["verdict_valid"] is False
    manifest = json.loads((repo / "docs/reviewer/plan-plan/chain.json").read_text())
    round1 = manifest["rounds"][0]
    assert round1["status"] == "failed"
    assert round1["returncode"] != 0
    assert round1["verdict_valid"] is False
    assert round1["reviewers"][0]["status"] == "failed"


def test_emitted_json_reviewers_carry_status_and_returncode(tmp_path):
    repo, reviewer = _init(tmp_path, FAKE_OK)
    result = _run(repo, reviewer)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["reviewers"], "expected at least one reviewer"
    for r in payload["reviewers"]:
        assert r["status"] == "ok"
        assert r["returncode"] == 0


def test_emitted_json_reviewers_show_failure(tmp_path):
    repo, reviewer = _init(tmp_path, FAKE_FAIL)
    result = _run(repo, reviewer)
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    for r in payload["reviewers"]:
        assert r["status"] == "failed"
        assert r["returncode"] != 0
        assert r["verdict_valid"] is False
