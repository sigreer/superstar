import json, os, subprocess, sys
from pathlib import Path
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


def _setup_chain(tmp_path):
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
        "rounds": [{"round": 1, "status": "rate-limited", "verdict": None, "verdict_valid": False}],
        "sweep_checkpoints": {"first-round": "pending", "final-ready": "pending"},
    }))
    return repo, chain_dir


def test_manual_approve_writes_synthetic_round(tmp_path):
    repo, chain_dir = _setup_chain(tmp_path)
    env = os.environ.copy()
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "rs.json")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "manual-approve", "--kind", "post-slice", "--file", "plan.md",
         "--work-id", "X", "--note", "Approved at standup — codex still down."],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((chain_dir / "chain.json").read_text())
    head = manifest["rounds"][-1]
    assert head["status"] == "manual-approved"
    assert head["verdict"] == "ready"
    assert head["verdict_valid"] is True
    assert head["approval_note"] == "Approved at standup — codex still down."
    assert "approved_by" in head and head["approved_by"]
    candidates = list(chain_dir.glob(f"r{head['round']}-*response.md"))
    assert candidates
    body = candidates[0].read_text()
    assert "Approved at standup — codex still down." in body
    assert "Overall verdict: ready (manual approval)" in body
