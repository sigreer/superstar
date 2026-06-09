import json
import os
import subprocess
from pathlib import Path
import sys, importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "rs.json"))


def test_rate_limit_payload_shape():
    payload = er.make_rate_limit_payload(
        reviewer_cmd="reviewer-agent",
        reset_at="2026-05-14T18:48:00",
        reset_source="regex:codex_usage_limit",
        chain="some-chain",
        round_num=2,
        request_path="docs/reviewer/some-chain/r2-...-request.md",
        raw_stderr_tail="ERROR: You've hit your usage limit ...",
    )
    assert payload["rate_limited"] is True
    assert payload["reviewer_cmd"] == "reviewer-agent"
    assert payload["reset_at"] == "2026-05-14T18:48:00"
    assert payload["reset_source"] == "regex:codex_usage_limit"
    assert payload["chain"] == "some-chain"
    assert payload["round"] == 2
    assert payload["request_path"].endswith("r2-...-request.md")
    assert "raw_stderr_tail" in payload


def test_rate_limit_payload_serialises_to_json():
    payload = er.make_rate_limit_payload(
        reviewer_cmd="reviewer-agent",
        reset_at="2026-05-14T18:48:00",
        reset_source="regex:codex_usage_limit",
        chain="c", round_num=2, request_path="r", raw_stderr_tail="t",
    )
    s = json.dumps(payload)
    assert "rate_limited" in s


def test_failed_reviewer_with_rate_limit_stderr_triggers_state_write(tmp_path, monkeypatch):
    """A reviewer subprocess that exits non-zero with rate-limit stderr must:
       - cause the script to exit 8
       - write a state entry
       - emit the rate-limit JSON payload on stdout
    """
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\nbody\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    # Reviewer simulator: prints rate-limit error to stderr, exits 1.
    reviewer = repo / "fake.sh"
    reviewer.write_text(
        "#!/usr/bin/env bash\n"
        "echo \"ERROR: You've hit your usage limit. Try again at 6:48 PM.\" >&2\n"
        "exit 1\n"
    )
    reviewer.chmod(0o755)

    state_file = tmp_path / "state.json"
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(state_file)

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json",
         "--no-preflight"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == er.EXIT_CODE_RATE_LIMITED, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["rate_limited"] is True
    assert "reset_at" in payload
    # State file written
    state = json.loads(state_file.read_text())
    key = str(reviewer)
    assert state["limits"][key]["limited"] is True
