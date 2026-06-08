from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def skill_text(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


def test_tasklist_discipline_documents_authority_and_start_workflow() -> None:
    text = skill_text("tasklist-discipline")

    assert "authoritative-checkout" in text
    assert "authoritative checkout" in text
    assert "configured" in text
    assert "tasktool start <slice-id>" in text
    assert "set <id> --status in_progress" in text
    assert "compatibility" in text
    assert "tasktool unblock <slice-id> --resume" in text
    assert "stamps `started` when needed" in text
    assert "tasktool close <x-id>" in text
    assert "--no-archive" in text
    assert "archive-cross" in text
    assert "archived x ids are still reserved" in text.lower()
    assert "cancelled` phases" in text
    assert "Administrative closeout exception" in text
    assert "already-superseded planning rows" in text
    assert "cancelled phases bypass" in text


def test_active_skills_use_global_tasktool_shim_not_repo_local_launcher() -> None:
    for skill in ["tasklist-discipline", "project-setup"]:
        text = skill_text(skill)
        assert "tools/tasktool/tasktool" not in text
        assert "repo-local launcher" not in text
        assert "repo-local tasktool" not in text
        assert "project-scoped tasktool" not in text


def test_subagent_driven_development_starts_slice_before_dispatch() -> None:
    text = skill_text("subagent-driven-development")

    start_index = text.index("tasktool start <slice-id>")
    dispatch_index = text.index("Before dispatching any implementation subagent")
    assert start_index < dispatch_index
    assert "must run `tasktool start <slice-id>`" in text
    assert "before dispatching implementation" in text


def test_executing_plans_uses_tasktool_start_for_in_progress_state() -> None:
    text = skill_text("executing-plans")

    assert "tasktool start <slice-id>" in text
    assert "Mark as in_progress" not in text
    assert "prose-only" not in text


def test_writing_plans_requires_start_as_first_execution_step() -> None:
    text = skill_text("writing-plans")

    assert "docs/tasklist.json exists" in text
    assert "tasktool start <slice-id>" in text
    assert "first execution step" in text
    assert "before dispatching or editing implementation files" in text


def test_planning_skills_reference_artifact_transactions() -> None:
    brainstorming = skill_text("brainstorming")
    writing = skill_text("writing-plans")
    discipline = skill_text("tasklist-discipline")
    review = skill_text("external-review")

    assert "tasktool prepare" in brainstorming
    assert "tasktool artifact add" in brainstorming
    assert "tasktool artifact commit" in brainstorming
    assert "tasktool artifact status" in writing
    assert "workflow artifacts" in discipline
    assert "tasktool artifact add" in review


def test_using_git_worktrees_is_thin_and_has_subagent_stop_block() -> None:
    text = skill_text("using-git-worktrees")
    lines = text.splitlines()
    assert len(lines) <= 40, (
        f"using-git-worktrees SKILL.md must be <=40 lines (spec §5.5); "
        f"got {len(lines)}"
    )
    assert "<SUBAGENT-STOP>" in text, "missing <SUBAGENT-STOP> opening tag"
    assert "</SUBAGENT-STOP>" in text, "missing </SUBAGENT-STOP> closing tag"
    # The block must precede the human-facing heading.
    assert text.index("<SUBAGENT-STOP>") < text.index("# Using Git Worktrees")


def test_using_git_worktrees_points_at_tasktool_start() -> None:
    text = skill_text("using-git-worktrees")
    assert "tasktool start" in text, "skill must instruct calling tasktool start"
    assert "--in-place" in text, "skill must document the --in-place opt-out"


def test_using_git_worktrees_has_no_forbidden_sections() -> None:
    text = skill_text("using-git-worktrees")
    forbidden = ["## Quick Reference", "## Common Mistakes", "## Red Flags",
                 "### 1a.", "### 1b.", "## Step 0", "## Step 1", "## Step 3", "## Step 4"]
    for marker in forbidden:
        assert marker not in text, (
            f"forbidden section/heading present (spec §5.5 forbids it): {marker!r}"
        )


def test_using_git_worktrees_references_submodules_doc() -> None:
    text = skill_text("using-git-worktrees")
    assert "references/submodules.md" in text, (
        "skill must point at references/submodules.md for the submodule guard"
    )
    from pathlib import Path
    submod = Path(__file__).resolve().parents[3] / "skills" / "using-git-worktrees" / "references" / "submodules.md"
    assert submod.is_file(), f"references/submodules.md must exist at {submod}"


def test_using_git_worktrees_matches_token_budget_fixture() -> None:
    """Token-budget regression. If you must edit the skill, update the fixture
    in the same commit so the diff is visible in review. Spec P5.S3 §6."""
    from pathlib import Path
    live = (Path(__file__).resolve().parents[3]
            / "skills" / "using-git-worktrees" / "SKILL.md").read_text()
    fixture = (Path(__file__).resolve().parent / "fixtures"
               / "p5_s3_skill_body.txt").read_text()
    def norm(s: str) -> str:
        return "\n".join(line.rstrip() for line in s.splitlines())
    assert norm(live) == norm(fixture), (
        "using-git-worktrees SKILL.md drifted from the P5.S3 token-budget "
        "fixture. If this is intentional, update "
        "tools/tasktool/tests/fixtures/p5_s3_skill_body.txt in the same commit."
    )


def test_subagent_early_exit_load_matches_fixture() -> None:
    """Spec §6 P5.S3 transcript regression. A compliant subagent loads only
    the bytes inside the <SUBAGENT-STOP> ... </SUBAGENT-STOP> block."""
    from pathlib import Path
    live = (Path(__file__).resolve().parents[3]
            / "skills" / "using-git-worktrees" / "SKILL.md").read_text()
    start_tag = "<SUBAGENT-STOP>"
    end_tag = "</SUBAGENT-STOP>"
    assert start_tag in live and end_tag in live, "early-exit tags missing"
    start = live.index(start_tag)
    end = live.index(end_tag) + len(end_tag)
    span = live[start:end]

    fixture = (Path(__file__).resolve().parent / "fixtures"
               / "p5_s3_subagent_load.txt").read_text()
    assert span == fixture, (
        "subagent early-exit span drifted from the P5.S3 transcript fixture. "
        "Update tools/tasktool/tests/fixtures/p5_s3_subagent_load.txt in the "
        "same commit and explain the behavior change in the commit message."
    )

    assert len(span) < len(live), "early-exit span must be a proper subset"
    assert "tasktool start" in span and (
        "do not call" in span.lower() or "do not" in span.lower()
    ), "early-exit block must forbid `tasktool start` from a subagent"


def test_registry_merge_playbook_exists() -> None:
    playbook = (
        ROOT
        / "skills"
        / "subagent-driven-development"
        / "references"
        / "registry-merge-playbook.md"
    )
    assert playbook.is_file(), f"registry merge playbook must exist at {playbook}"
    body = playbook.read_text(encoding="utf-8")
    # The playbook's load-bearing instructions.
    assert "preserve both" in body.lower()
    assert "regenerate" in body.lower()
    assert "rerun" in body.lower()


def test_subagent_driven_development_runs_surface_check_before_parallel_dispatch() -> None:
    text = skill_text("subagent-driven-development")
    assert "tasktool surface check <phase-id>" in text
    assert "Do not parallel-dispatch slices that share an integration surface" in text
    # surface check is described alongside ready-slices, before dispatch
    rs = text.index("tasktool ready-slices <phase-id>")
    sc = text.index("tasktool surface check <phase-id>")
    assert rs < sc, "surface check must be documented after ready-slices"


def test_subagent_driven_development_has_integrate_main_checkpoint() -> None:
    text = skill_text("subagent-driven-development")
    assert "tasktool worktree status <slice-id> --integration" in text
    assert "Integrate-current-main checkpoint" in text
    assert "references/registry-merge-playbook.md" in text
    # the checkpoint precedes the close gate in the slice-end sequence
    integ = text.index("tasktool worktree status <slice-id> --integration")
    close = text.index("tasktool close <slice-id>")
    assert integ < close, "integrate-main checkpoint must precede the close gate"


def _slice_end_section(text: str) -> str:
    start = text.index("- **At the end of each slice**")
    end = text.index("- **At the end of the phase**", start)
    return text[start:end]


def test_subagent_driven_development_merges_before_close_and_prunes_after() -> None:
    text = skill_text("subagent-driven-development")
    section = _slice_end_section(text)

    review_ready = section.index("On `ready` / `ready with small edits`, proceed")
    merge_back = section.index("merge the worktree branch back")
    close = section.index("tasktool close <slice-id>")
    prune = section.index("tasktool worktree prune <slice-id>")

    assert review_ready < merge_back < close < prune
    assert "[[finishing-a-development-branch]]" in section
    assert "must not present the interactive Step 4 options menu" in section
    assert "Option 1 merge mechanics" in section
    assert "landed-branch gate" in section
    assert "auto-commits" in section
    assert "--force" in section
    assert "normal closeout path" in section


def test_subagent_driven_development_diagram_has_merge_close_prune_order() -> None:
    text = skill_text("subagent-driven-development")
    diagram_start = text.index("digraph process")
    diagram_end = text.index("## Model Selection", diagram_start)
    diagram = text[diagram_start:diagram_end]

    assert '"Merge back to base branch"' in diagram
    assert '"tasktool worktree prune <slice-id>"' in diagram
    assert '"post-slice verdict ready?" -> "Merge back to base branch"' in diagram
    assert '"Merge back to base branch" -> "tasktool close <slice-id>"' in diagram
    assert '"tasktool close <slice-id>" -> "tasktool worktree prune <slice-id>"' in diagram
    assert '"post-slice verdict ready?" -> "tasktool close <slice-id>"' not in diagram


def test_tasklist_discipline_documents_surface_reserve_coordinate() -> None:
    text = skill_text("tasklist-discipline")
    # daily-commands surface
    assert "tasktool surface add <slice-id>" in text
    assert "tasktool surface check <phase-id>" in text
    assert "tasktool reserve add <slice-id>" in text
    assert "tasktool coordinate <slice-id> --group" in text
    # conceptual model + vocabulary
    assert "integration_surfaces" in text
    assert "reservations" in text
    assert "cms-block-registry" in text
    # coordination_group vs parallel_group distinction is spelled out
    assert "coordination_group" in text
    assert "parallel_group" in text
    # the three new red-flag claims
    assert "feature independence" in text
    assert "duplicate" in text.lower()


def test_finishing_branch_documents_noninteractive_per_slice_mergeback() -> None:
    text = skill_text("finishing-a-development-branch")

    assert "Non-Interactive Per-Slice Merge-Back" in text
    assert "skip Step 4" in text
    assert "Option 1 merge mechanics" in text
    assert "return to `subagent-driven-development`" in text
    assert "Do not run Step 6 cleanup before `tasktool close <slice-id>`" in text
    assert "tasktool worktree prune <slice-id>" in text
    assert "--force" in text
    assert "not the normal closeout path" in text


def test_phase_planning_and_writing_plans_document_surface_tables() -> None:
    for skill in ["phase-planning", "writing-plans"]:
        text = skill_text(skill)
        assert "surface/reservation table" in text, (
            f"{skill} must require a surface/reservation table"
        )
        assert "tasktool surface check <phase-id>" in text, (
            f"{skill} must tell the author to run surface check before ratifying"
        )
