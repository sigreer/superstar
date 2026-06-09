"""Regression: when the final-ready sweep fires post-primary, the primary
artefacts are renamed to add the `-primary` suffix. The response body, which
embeds a `Request:` header pointing at the original request file, must be
rewritten so it references the renamed request path.

Pre-fix, the response body kept the original `r{N}-{ts}-request.md` reference
even after the file was renamed to `r{N}-{ts}-primary-request.md`, leaving
artifacts mutually inconsistent.
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


def test_final_ready_rename_rewrites_response_request_header(tmp_path):
    repo = _init_repo(tmp_path)
    _write_stub(repo, "revise")
    r1 = _run(
        repo, "--kind", "post-slice", "--work-id", "P1.S1",
        "--file", "plan.md", "--review-depth", "thorough", "--emit", "json",
        "--no-preflight",
    )
    assert r1.returncode == 0, r1.stderr

    chain = repo / "docs" / "reviewer" / "plan-P1-S1-post-slice"
    (chain / "r1-resolution.md").write_text("## Resolution\n\nstatus: applied\n")

    # Round 2 stub returns ready -> final-ready fires AFTER primary runs,
    # triggering the post-hoc rename of primary artefacts.
    _write_stub(repo, "ready")
    r2 = _run(
        repo, "--kind", "post-slice", "--work-id", "P1.S1",
        "--file", "plan.md", "--review-depth", "thorough", "--emit", "json",
    )
    assert r2.returncode == 0, r2.stderr

    primary_responses = list(chain.glob("r2-*-primary-response.md"))
    primary_requests = list(chain.glob("r2-*-primary-request.md"))
    assert primary_responses, list(chain.iterdir())
    assert primary_requests, list(chain.iterdir())

    primary_response = primary_responses[0]
    primary_request = primary_requests[0]

    body = primary_response.read_text(encoding="utf-8")
    # The body's Request: line must reference the renamed request file that
    # actually exists on disk, not the pre-rename basename.
    assert f"- Request: `{primary_request.name}`" in body or (
        primary_request.name in body
    ), body
    # The pre-rename non-namespaced basename must NOT appear as the Request:
    # reference (it would otherwise point at a path that does not exist).
    stale_basename = primary_request.name.replace("-primary-request.md", "-request.md")
    assert f"- Request: `{stale_basename}`" not in body, body
    # Sanity: the referenced request file exists.
    assert primary_request.exists()
