from pathlib import Path
import json
import os
import subprocess
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_substitute_all_new_placeholders(tmp_path):
    chain_dir = tmp_path / "chain"; chain_dir.mkdir()
    prev = chain_dir / "r1-response.md"; prev.write_text("x")
    res = chain_dir / "r1-resolution.md"; res.write_text("y")
    session = chain_dir / "session.state"

    out = er.expand_command_template(
        "echo {chain_dir} {round} {previous_response} {resolution_file} {session_file}",
        prompt_file=chain_dir / "r2-request.md",
        prompt_text="prompt",
        target_file=Path("plan.md"),
        kind="post-slice",
        chain_dir=chain_dir,
        round_num=2,
        previous_response=prev,
        resolution_file=res,
        session_file=session,
    )
    assert str(chain_dir) in out
    assert "2" in out
    assert str(prev) in out
    assert str(res) in out
    assert str(session) in out


def test_substitute_optional_placeholders_empty(tmp_path):
    chain_dir = tmp_path / "chain"; chain_dir.mkdir()
    session = chain_dir / "session.state"
    out = er.expand_command_template(
        "echo [{previous_response}] [{resolution_file}]",
        prompt_file=chain_dir / "r1-request.md",
        prompt_text="prompt",
        target_file=Path("plan.md"),
        kind="spec",
        chain_dir=chain_dir,
        round_num=1,
        previous_response=None,
        resolution_file=None,
        session_file=session,
    )
    assert "[]" in out
    # Confirm both are empty placeholders
    assert out.count("[]") == 2


def test_substitute_preserves_legacy_placeholders(tmp_path):
    chain_dir = tmp_path / "chain"; chain_dir.mkdir()
    session = chain_dir / "session.state"
    prompt_file = chain_dir / "r1-request.md"
    out = er.expand_command_template(
        "reviewer {prompt_file} --target {target_file} --kind {kind}",
        prompt_file=prompt_file,
        prompt_text="hello",
        target_file=Path("plan.md"),
        kind="plan",
        chain_dir=chain_dir,
        round_num=1,
        previous_response=None,
        resolution_file=None,
        session_file=session,
    )
    assert str(prompt_file) in out
    assert "plan.md" in out
    assert "plan" in out


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


def test_round_2_primary_receives_previous_response_and_resolution(tmp_path):
    """S6 contract: on round N+1 the primary reviewer must see the prior
    response and resolution paths via `{previous_response}` / `{resolution_file}`.
    Sweeps must continue to receive empty strings (isolated, no anchoring)."""
    repo = _init_repo(tmp_path)
    # Stub records its argv to a per-call log file so we can inspect what the
    # primary vs sweep received.
    log_dir = repo / "stub_log"
    log_dir.mkdir()
    stub = repo / "stub.sh"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        f"echo \"PREV=$1 RES=$2\" >> {log_dir}/calls.log\n"
        "echo 'Overall verdict: revise'\n"
    )
    stub.chmod(0o755)

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = f"{stub} {{previous_response}} {{resolution_file}}"

    def _run(extra_args=()):
        return subprocess.run(
            [
                sys.executable, str(SCRIPTS / "external-reviewer.py"), "review",
                "--kind", "post-slice", "--work-id", "P1.S1",
                "--file", "plan.md", "--emit", "json",
                *extra_args,
            ],
            cwd=repo, env=env, capture_output=True, text=True, timeout=60,
        )

    r1 = _run(("--no-preflight",))
    assert r1.returncode == 0, r1.stderr
    chain = repo / "docs" / "reviewer" / "plan-P1-S1-post-slice"
    (chain / "r1-resolution.md").write_text("## Resolution\n\nstatus: applied\n")

    # Truncate the log so we only see round-2 calls.
    (log_dir / "calls.log").write_text("")

    r2 = _run()
    assert r2.returncode == 0, r2.stderr

    calls = (log_dir / "calls.log").read_text().strip().splitlines()
    # Standard depth: just the primary on round 2.
    assert len(calls) == 1, calls
    line = calls[0]
    # Primary on round 2 must reference the prior response & resolution paths.
    assert "r1-" in line and "response.md" in line, line
    assert "r1-resolution.md" in line, line


def test_round_2_sweep_receives_empty_previous_and_resolution(tmp_path):
    """Sweep reviewers are isolated and must NOT receive prior-round paths
    via the template — placeholders should expand to empty strings for them."""
    repo = _init_repo(tmp_path)
    log_dir = repo / "stub_log"; log_dir.mkdir()
    stub = repo / "stub.sh"
    # Tag each call with role-inferred filename argument so we can tell
    # sweep vs primary apart by what's in the prompt path.
    stub.write_text(
        "#!/usr/bin/env bash\n"
        # Args: $1=prompt_file, $2=prev, $3=res
        f"echo \"PROMPT=$1 PREV=$2 RES=$3\" >> {log_dir}/calls.log\n"
        "echo 'Overall verdict: ready'\n"
    )
    stub.chmod(0o755)

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = (
        f"{stub} {{prompt_file}} {{previous_response}} {{resolution_file}}"
    )

    def _run(extra_args=()):
        return subprocess.run(
            [
                sys.executable, str(SCRIPTS / "external-reviewer.py"), "review",
                "--kind", "post-slice", "--work-id", "P1.S1",
                "--file", "plan.md", "--review-depth", "thorough",
                "--sweep-policy", "final-ready", "--emit", "json",
                *extra_args,
            ],
            cwd=repo, env=env, capture_output=True, text=True, timeout=60,
        )

    # Round 1 with sweep-policy=final-ready: ready → no sweep, primary only.
    r1 = _run(("--no-preflight",))
    assert r1.returncode == 0, r1.stderr
    # Write a resolution so round 2 has both prior response AND resolution to surface.
    chain = repo / "docs" / "reviewer" / "plan-P1-S1-post-slice"
    (chain / "r1-resolution.md").write_text("## Resolution\n\nstatus: applied\n")
    # Round 2 (ready) → final-ready sweep fires.
    (log_dir / "calls.log").write_text("")
    r2 = _run()
    assert r2.returncode == 0, r2.stderr

    calls = (log_dir / "calls.log").read_text().strip().splitlines()
    assert len(calls) == 2, calls
    # Identify primary vs sweep: primary runs first (its request filename
    # is non-namespaced until renamed); sweep request contains `-sweep1-`.
    sweep_line = next(c for c in calls if "-sweep1-request.md" in c)
    primary_line = next(c for c in calls if "-sweep" not in c)
    # Primary receives the prior paths.
    assert "r1-" in primary_line and "response.md" in primary_line
    assert "r1-resolution.md" in primary_line
    # Sweep receives empty strings for PREV and RES — placeholders collapse to nothing.
    # The expected shape is "PROMPT=<path> PREV= RES=" with trailing whitespace.
    assert sweep_line.endswith("PREV= RES=") or "PREV=  RES=" in sweep_line, sweep_line
