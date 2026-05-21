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
