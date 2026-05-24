from __future__ import annotations
import unittest
from tasktool.model import (
    Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status,
    PlanningStatus, ArchivedCrossCutting, SCHEMA_VERSION, is_terminal,
    SliceWorkflowStep, PhaseWorkflowStep, ReviewStage,
)

class StatusTests(unittest.TestCase):
    def test_status_values(self):
        self.assertEqual(
            {s.value for s in Status},
            {"ready", "in_progress", "blocked", "done", "cancelled"},
        )

    def test_planning_status_values(self):
        self.assertEqual(
            {s.value for s in PlanningStatus},
            {"proposed", "ratified", "superseded"},
        )

class ConstructionTests(unittest.TestCase):
    def test_empty_project(self):
        p = Project(project="superstar")
        self.assertEqual(p.schema_version, SCHEMA_VERSION)
        self.assertEqual(p.phases, [])
        self.assertEqual(p.cross_cutting, [])
        self.assertEqual(p.archived_phases, [])
        self.assertEqual(p.archived_cross_cutting, [])

    def test_phase_defaults(self):
        ph = Phase(id="P2", title="tasktool", created="2026-05-17")
        self.assertEqual(ph.status, Status.READY)
        self.assertIsNone(ph.closed)
        self.assertIsNone(ph.spec_path)
        self.assertIsNone(ph.plan_path)
        self.assertIsNone(ph.planning_path)
        self.assertIsNone(ph.phase_reviewer_chain)
        self.assertEqual(ph.notes, "")
        self.assertEqual(ph.slices, [])

    def test_slice_defaults(self):
        s = Slice(id="S1", title="CLI core", created="2026-05-17")
        self.assertEqual(s.status, Status.READY)
        self.assertIsNone(s.blocked_on)
        self.assertEqual(s.depends_on, [])
        self.assertEqual(s.planning_status, PlanningStatus.PROPOSED)
        self.assertIsNone(s.parallel_group)
        self.assertIsNone(s.reviewer_chain)
        self.assertEqual(s.refs, [])
        self.assertEqual(s.tasks, [])

    def test_task_defaults(self):
        t = Task(id="T1", title="x", created="2026-05-17")
        self.assertEqual(t.status, Status.READY)
        self.assertIsNone(t.closed)
        self.assertEqual(t.refs, [])

    def test_cross_defaults(self):
        x = CrossCutting(id="X1", title="x", created="2026-05-17")
        self.assertEqual(x.status, Status.READY)

    def test_blocked_on_id(self):
        b = BlockedOn(kind="id", value="P2.S1")
        self.assertEqual(b.kind, "id")
    def test_blocked_on_external(self):
        b = BlockedOn(kind="external", value="vendor X")
        self.assertEqual(b.value, "vendor X")


class PublicAPITests(unittest.TestCase):
    """Verify the package-level public API promised by the spec."""

    def test_import_load_project_and_project(self):
        """from tasktool import load_project, Project must succeed."""
        import tasktool
        self.assertTrue(callable(tasktool.load_project))
        self.assertIs(tasktool.Project, Project)

    def test_all_exports_present(self):
        import tasktool
        for name in [
            "load_project", "save_project", "dumps_canonical", "loads_project",
            "Project", "Phase", "Slice", "Task", "CrossCutting", "BlockedOn",
            "Status", "PlanningStatus", "ArchivedPhase", "ArchivedCrossCutting",
            "SCHEMA_VERSION",
        ]:
            self.assertTrue(hasattr(tasktool, name), f"tasktool.{name} missing")


def test_slice_audit_fields_default_to_none_and_false():
    from tasktool.model import Slice
    s = Slice(id="S1", title="t", created="2026-05-21")
    assert s.worktree_pruned_at is None
    assert s.worktree_prune_pending is False
    assert s.worktree_prune_pending_at is None


def test_cross_audit_fields_default_to_none_and_false():
    from tasktool.model import CrossCutting
    c = CrossCutting(id="X1", title="t", created="2026-05-21")
    assert c.worktree_pruned_at is None
    assert c.worktree_prune_pending is False
    assert c.worktree_prune_pending_at is None


def test_schema_version_is_2():
    assert SCHEMA_VERSION == 2


def test_slice_has_workflow_step_default_none():
    s = Slice(id="S1", title="t", created="2026-05-23")
    assert s.workflow_step is None
    assert s.review_active is False
    assert s.review_stage is None


def test_phase_has_workflow_step_default_none():
    p = Phase(id="P6", title="t", created="2026-05-23")
    assert p.workflow_step is None


def test_slice_accepts_workflow_step_enum():
    s = Slice(
        id="S1", title="t", created="2026-05-23",
        workflow_step=SliceWorkflowStep.PLAN,
        review_active=True,
        review_stage=ReviewStage.AWAITING_RESPONSE,
    )
    assert s.workflow_step is SliceWorkflowStep.PLAN
    assert s.review_active is True
    assert s.review_stage is ReviewStage.AWAITING_RESPONSE


def test_phase_accepts_workflow_step_enum():
    p = Phase(
        id="P6", title="t", created="2026-05-23",
        workflow_step=PhaseWorkflowStep.READY,
    )
    assert p.workflow_step is PhaseWorkflowStep.READY


def test_slice_workflow_step_values():
    assert {e.value for e in SliceWorkflowStep} == {"spec", "plan", "implement", "done"}


def test_phase_workflow_step_values():
    assert {e.value for e in PhaseWorkflowStep} == {"spec", "ready", "in_progress", "done"}


def test_review_stage_values():
    assert {e.value for e in ReviewStage} == {"awaiting_response", "applying_fixes", "passed"}


def test_is_terminal_done_and_cancelled_only():
    assert is_terminal(Status.DONE) is True
    assert is_terminal(Status.CANCELLED) is True
    assert is_terminal(Status.READY) is False
    assert is_terminal(Status.IN_PROGRESS) is False
    assert is_terminal(Status.BLOCKED) is False


def test_cancelled_enum_value():
    assert Status.CANCELLED.value == "cancelled"
