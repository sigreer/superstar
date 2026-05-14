from pathlib import Path
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def test_apply_budget_preserves_priority_under_cap():
    body = (
        f"{er.PROMPT_SENTINEL_START}\n"
        "## Review chain summary\n\n| round | verdict |\n| 1 | revise |\n\n"
        "## Prior-round findings\n\nF1: blocking, F2: important\n" + ("P" * 80_000) + "\n"
        "## Resolution report for prior round\n\n" + ("R" * 50_000) + "\n"
        "## Changes since prior round\n\n" + ("D" * 100_000) + "\n"
        "## Target Preview\n\n" + ("T" * 60_000) + "\n"
        f"{er.PROMPT_SENTINEL_END}\n"
    )
    out = er.apply_budget(body, budget_chars=120_000)
    assert er.PROMPT_SENTINEL_START in out
    assert er.PROMPT_SENTINEL_END in out
    assert "## Review chain summary" in out
    assert "F1: blocking, F2: important" in out
    assert len(out) <= 120_000 + 500
    assert "<!-- budget-applied:" in out


def test_apply_budget_passthrough_under_cap():
    body = "small body"
    assert er.apply_budget(body, budget_chars=10_000) == body


def test_cli_budget_trims_actual_request(tmp_path):
    """End-to-end: spawn the script with a tiny --incremental-budget-chars
    and confirm the persisted request file carries the budget-applied note
    and stays within the budget."""
    import os, subprocess, sys, json
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n" + ("body line\n" * 50))
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    reviewer = repo / "fake.sh"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)

    r1 = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    assert r1.returncode == 0, r1.stderr

    chain_dir = repo / "docs/reviewer/plan-plan"
    (chain_dir / "r1-merged-findings.md").write_text("M" * 60_000)

    r2 = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md",
         "--mode", "incremental", "--incremental-budget-chars", "20000",
         "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    assert r2.returncode == 0, r2.stderr

    request_file = next(chain_dir.glob("r2-*-request.md"))
    body = request_file.read_text()
    assert "<!-- budget-applied:" in body
    assert len(body) <= 20_000 + 500


def test_apply_budget_trims_diff_with_nested_subheadings():
    """apply_budget must trim the diff body even when compute_diff_section
    emits nested ### sub-headings inside the 'Changes since prior round'
    section.  The old _find_section_end (scanning for any \\n## heading)
    would stop at the first nested heading and leave the section untouched."""
    big_diff = "X" * 150_000
    body = (
        f"{er.PROMPT_SENTINEL_START}\n"
        "## Changes since prior round\n\n"
        "### git diff base..HEAD\n\n"
        + big_diff + "\n"
        "## Target Preview\n\n"
        "some preview\n"
        f"{er.PROMPT_SENTINEL_END}\n"
    )
    out = er.apply_budget(body, budget_chars=80_000)
    # Must have been trimmed
    assert len(out) <= 80_000 + 500
    # The section header must still be present
    assert "## Changes since prior round" in out
    # The diff body must actually have been cut
    assert ("bytes elided" in out or "diff_body dropped to fit budget" in out
            or "[diff_body" in out)
