import json, os, subprocess, sys
from pathlib import Path
import datetime as dt
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


def _setup(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    reviewer = repo / "fake"
    reviewer.write_text("#!/usr/bin/env bash\necho ready\n")
    reviewer.chmod(0o755)
    state_file = tmp_path / "state.json"
    future = (dt.datetime.now() + dt.timedelta(hours=1)).isoformat(timespec="seconds")
    key = str(reviewer)  # state-key matches reviewer_cmd_basename() semantics
    state_file.write_text(json.dumps({"schema_version": 1, "limits": {
        key: {"limited": True, "limited_at": "x", "reset_at": future,
              "reset_source": "test", "raw_stderr_tail": "", "chain": "c", "round": 1}
    }}))
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(state_file)
    return repo, env


def _invoke(repo, env, args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py")] + args,
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )


def test_two_refusals_coalesce_into_one_round(tmp_path):
    repo, env = _setup(tmp_path)
    p1 = _invoke(repo, env, ["review", "--kind", "plan", "--file", "plan.md", "--emit", "json"])
    assert p1.returncode == er.EXIT_CODE_RATE_LIMITED
    chain_dir = next((repo / "docs/reviewer").iterdir())
    manifest = json.loads((chain_dir / "chain.json").read_text())
    assert len(manifest["rounds"]) == 1
    p2 = _invoke(repo, env, ["review", "--kind", "plan", "--file", "plan.md", "--emit", "json"])
    assert p2.returncode == er.EXIT_CODE_RATE_LIMITED
    manifest = json.loads((chain_dir / "chain.json").read_text())
    assert len(manifest["rounds"]) == 1
    head = manifest["rounds"][-1]
    assert head["status"] == "rate-limited"
    assert "last_refused_at" in head
    assert len(head.get("refused_at", [])) >= 2


def test_refused_at_caps_at_20(tmp_path):
    repo, env = _setup(tmp_path)
    for _ in range(25):
        _invoke(repo, env, ["review", "--kind", "plan", "--file", "plan.md", "--emit", "json"])
    chain_dir = next((repo / "docs/reviewer").iterdir())
    manifest = json.loads((chain_dir / "chain.json").read_text())
    head = manifest["rounds"][-1]
    assert len(head["refused_at"]) <= 20
