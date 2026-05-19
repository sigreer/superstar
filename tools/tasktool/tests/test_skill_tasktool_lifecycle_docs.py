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


def test_using_git_worktrees_allows_routed_tasktool_writes_from_worktrees() -> None:
    text = skill_text("using-git-worktrees")

    assert "tasktool" in text
    assert "implementation worktree" in text
    assert "authoritative-checkout" in text
    assert "routing is configured" in text
    assert "do not leave the worktree" in text


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
