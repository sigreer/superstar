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


VALID_RESPONSE = """# External reviewer response
Some findings...
Overall verdict: ready with small edits
"""


def test_ingest_response_from_paste(tmp_path):
    repo, chain_dir = _setup_chain(tmp_path)
    paste_file = tmp_path / "pasted.md"
    paste_file.write_text(VALID_RESPONSE)
    env = os.environ.copy()
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "rs.json")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "ingest-response", "--kind", "post-slice", "--file", "plan.md",
         "--work-id", "X", "--from-paste", str(paste_file)],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((chain_dir / "chain.json").read_text())
    head = manifest["rounds"][-1]
    assert head["status"] == "human-bridged"
    assert head["verdict"] == "ready with small edits"
    candidates = list(chain_dir.glob(f"r{head['round']}-*response.md"))
    assert candidates
    body = candidates[0].read_text()
    assert "Overall verdict: ready with small edits" in body


def test_ingest_response_from_link_strips_outer_fence(tmp_path):
    repo, chain_dir = _setup_chain(tmp_path)
    linked = tmp_path / "fenced.md"
    fenced = f"```\n{VALID_RESPONSE}\n```\n"
    linked.write_text(fenced)
    env = os.environ.copy()
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "rs.json")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "ingest-response", "--kind", "post-slice", "--file", "plan.md",
         "--work-id", "X", "--from-link", str(linked)],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    candidates = list(chain_dir.glob("r*-response.md"))
    body = candidates[0].read_text()
    assert "Overall verdict: ready with small edits" in body
    assert not body.startswith("```")


def test_ingest_response_rewrites_heading_style_verdict(tmp_path):
    repo, chain_dir = _setup_chain(tmp_path)
    weird = tmp_path / "weird.md"
    weird.write_text("# foo\n\nfindings ...\n\n5. Overall verdict\n\nready\n")
    env = os.environ.copy()
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "rs.json")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "ingest-response", "--kind", "post-slice", "--file", "plan.md",
         "--work-id", "X", "--from-paste", str(weird)],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0
    manifest = json.loads((chain_dir / "chain.json").read_text())
    head = manifest["rounds"][-1]
    assert head["verdict"] == "ready"


def test_ingest_response_unparseable_exits_2(tmp_path):
    repo, chain_dir = _setup_chain(tmp_path)
    bad = tmp_path / "bad.md"
    bad.write_text("some text without a verdict line\n")
    env = os.environ.copy()
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "rs.json")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "ingest-response", "--kind", "post-slice", "--file", "plan.md",
         "--work-id", "X", "--from-paste", str(bad)],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 2
    candidates = list(chain_dir.glob("r*-response.md"))
    assert candidates
