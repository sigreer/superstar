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
echo "Stub finding."
echo "Overall verdict: revise"
"""

FAKE_FAIL = """#!/usr/bin/env bash
echo "stderr noise" 1>&2
exit 1
"""


def _init(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    return repo


def _run(repo, reviewer_src, *extra_args):
    reviewer = repo / "fake.sh"; reviewer.write_text(reviewer_src); reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--file", "plan.md",
         "--work-id", "P1.S1", "--emit", "json", *extra_args],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )


def test_failed_prior_round_bypasses_resolution_gate(tmp_path):
    repo = _init(tmp_path)
    r1 = _run(repo, FAKE_OK, "--no-preflight")
    assert r1.returncode == 0, r1.stderr
    # Satisfy the gate for r2 so r2 actually invokes the (failing) reviewer
    # and records a status:"failed" round. Without this, r2 would be blocked
    # by the gate (rc=3) and never get persisted into chain.json.
    (repo / "docs/reviewer/plan-P1-S1-post-slice/r1-resolution.md").write_text("ok\n")
    r2 = _run(repo, FAKE_FAIL)
    assert r2.returncode != 0
    r3 = _run(repo, FAKE_OK)
    assert r3.returncode != 3, (
        f"resolution gate fired despite failed prior round; "
        f"stderr: {r3.stderr}"
    )


def test_unknown_prior_round_does_not_bypass_gate(tmp_path):
    repo = _init(tmp_path)
    _run(repo, FAKE_OK, "--no-preflight")
    chain_path = repo / "docs/reviewer/plan-P1-S1-post-slice/chain.json"
    manifest = json.loads(chain_path.read_text())
    manifest["rounds"][0]["status"] = "unknown"
    chain_path.write_text(json.dumps(manifest))
    r2 = _run(repo, FAKE_OK)
    assert r2.returncode == 3, (
        f"resolution gate did not fire on unknown prior; rc={r2.returncode} "
        f"stderr={r2.stderr}"
    )
