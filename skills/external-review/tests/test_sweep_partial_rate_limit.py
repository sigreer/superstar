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


def test_sweep_rate_limited_primary_ok_round_still_succeeds(tmp_path):
    """When the primary succeeds and a sweep is rate-limited, the round still
    returns the primary's verdict; the sweep is recorded as status=rate-limited
    in reviewers[]; state file IS written so subsequent runs refuse pre-spawn.

    Sweeps are separate run_one_reviewer() calls with role="sweep", same reviewer_cmd
    template. We distinguish primary vs sweep by invocation count using a sentinel file.
    """
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    sentinel = tmp_path / "called_once"
    reviewer = repo / "reviewer.sh"
    reviewer.write_text(
        "#!/usr/bin/env bash\n"
        f"SENTINEL='{sentinel}'\n"
        "if [ ! -f \"$SENTINEL\" ]; then\n"
        "  touch \"$SENTINEL\"\n"
        "  echo 'Overall verdict: ready'\n"
        "  exit 0\n"
        "else\n"
        "  echo \"ERROR: You've hit your usage limit. Try again at 11:59 PM.\" >&2\n"
        "  exit 1\n"
        "fi\n"
    )
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "rs.json")

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md",
         "--independent-reviewers", "1", "--sweep-policy", "first-round", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["merged_verdict"] == "ready"
    reviewers_by_role = {r["role"]: r["status"] for r in payload.get("reviewers", [])}
    assert reviewers_by_role.get("primary") == "ok"
    sweep_entries = [v for k, v in reviewers_by_role.items() if k == "sweep"]
    assert sweep_entries and sweep_entries[0] == "rate-limited"
    state_file = tmp_path / "rs.json"
    state = json.loads(state_file.read_text())
    assert state["limits"]
