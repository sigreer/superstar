"""Tests for sweep planning order-of-operations (F1).

The `final-ready` sweep must be planned AFTER the current round's primary
runs, using the CURRENT primary's verdict — not the prior manifest round's.
"""
from pathlib import Path
import json
import os
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


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


def _write_stub(repo, verdict: str):
    reviewer = repo / "stub.sh"
    reviewer.write_text(
        "#!/usr/bin/env bash\n"
        f"echo 'Overall verdict: {verdict}'\n"
    )
    reviewer.chmod(0o755)
    return reviewer


def _run(repo, *args, env=None):
    base_env = os.environ.copy()
    if env:
        base_env.update(env)
    base_env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"), "review", *args],
        cwd=repo, env=base_env, capture_output=True, text=True, timeout=60,
    )


def test_round_2_primary_ready_triggers_final_ready_sweep(tmp_path):
    """Round 1 returns revise; round 2 primary returns ready. The current
    round's primary verdict must drive `final-ready` sweep planning."""
    repo = _init_repo(tmp_path)
    _write_stub(repo, "revise")
    r1 = _run(
        repo, "--kind", "post-slice", "--work-id", "P1.S1",
        "--file", "plan.md", "--review-depth", "thorough", "--emit", "json",
    )
    assert r1.returncode == 0, r1.stderr
    p1 = json.loads(r1.stdout)
    # Round 1 with revise should have triggered a first-round sweep.
    assert any(r["role"] == "sweep" for r in p1["reviewers"]), p1

    chain = repo / "docs" / "reviewer" / "plan-P1-S1-post-slice"
    # Provide resolution so round 2 isn't gated.
    (chain / "r1-resolution.md").write_text(
        "## Resolution\n\nstatus: applied\n"
    )

    # Now stub returns ready; round 2 primary must trigger final-ready sweep.
    _write_stub(repo, "ready")
    r2 = _run(
        repo, "--kind", "post-slice", "--work-id", "P1.S1",
        "--file", "plan.md", "--review-depth", "thorough", "--emit", "json",
    )
    assert r2.returncode == 0, r2.stderr
    p2 = json.loads(r2.stdout)
    # Final-ready sweep MUST fire on this round.
    sweep_roles = [r["role"] for r in p2["reviewers"]]
    assert sweep_roles.count("sweep") >= 1, f"expected final-ready sweep on r2, got {sweep_roles}"
    assert p2["merged_findings_path"] is not None
    assert (chain / "r2-merged-findings.md").exists()


def test_round_1_primary_ready_no_sweep(tmp_path):
    """Round 1 primary ready: no checkpoint applies (first-round is for revise
    at round 1; final-ready is round>1). No sweep should fire."""
    repo = _init_repo(tmp_path)
    _write_stub(repo, "ready")
    # Use a sweep policy of final-ready (so first-round does not apply).
    r1 = _run(
        repo, "--kind", "post-slice", "--work-id", "P1.S1",
        "--file", "plan.md", "--review-depth", "thorough",
        "--sweep-policy", "final-ready", "--emit", "json",
    )
    assert r1.returncode == 0, r1.stderr
    p1 = json.loads(r1.stdout)
    assert all(r["role"] == "primary" for r in p1["reviewers"]), p1
    assert p1["merged_findings_path"] is None


def test_final_ready_checkpoint_prevents_re_fire(tmp_path):
    """Once final-ready completes, a subsequent ready round must not re-fire it."""
    repo = _init_repo(tmp_path)
    _write_stub(repo, "revise")
    _run(
        repo, "--kind", "post-slice", "--work-id", "P1.S1",
        "--file", "plan.md", "--review-depth", "thorough", "--emit", "json",
    )

    chain = repo / "docs" / "reviewer" / "plan-P1-S1-post-slice"
    (chain / "r1-resolution.md").write_text("## Resolution\n\nstatus: applied\n")

    # Round 2: ready → final-ready fires.
    _write_stub(repo, "ready")
    r2 = _run(
        repo, "--kind", "post-slice", "--work-id", "P1.S1",
        "--file", "plan.md", "--review-depth", "thorough", "--emit", "json",
    )
    assert r2.returncode == 0, r2.stderr
    p2 = json.loads(r2.stdout)
    assert any(r["role"] == "sweep" for r in p2["reviewers"])

    # Round 3: ready again. final-ready checkpoint already complete; no sweep.
    r3 = _run(
        repo, "--kind", "post-slice", "--work-id", "P1.S1",
        "--file", "plan.md", "--review-depth", "thorough", "--emit", "json",
    )
    assert r3.returncode == 0, r3.stderr
    p3 = json.loads(r3.stdout)
    assert all(r["role"] == "primary" for r in p3["reviewers"]), p3
