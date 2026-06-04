# tools/tasktool/tests/test_commands.py
from __future__ import annotations
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tasktool import commands
from tasktool.serialize import load_project
from tasktool.model import Status
from tasktool.validate import ValidationError

class _Tmp:
    def __init__(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        (self.root / "docs").mkdir()
        commands.cmd_config_init_local(repo_root=self.root)
    def cleanup(self):
        self._td.cleanup()

class InitTests(unittest.TestCase):
    def test_init_creates_empty_project(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="superstar", north_star="ns")
            path = t.root / "docs/tasklist.json"
            self.assertTrue(path.exists())
            p = load_project(path)
            self.assertEqual(p.project, "superstar")
            self.assertEqual(p.north_star, "ns")
        finally:
            t.cleanup()

    def test_init_refuses_existing_without_force(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="a")
            with self.assertRaises(commands.CommandError):
                commands.cmd_init(repo_root=t.root, project="b")
        finally:
            t.cleanup()

    def test_init_without_project_uses_repo_root_name(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root)
            p = load_project(t.root / "docs/tasklist.json")
            self.assertEqual(p.project, t.root.name)
        finally:
            t.cleanup()

class CreateTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
    def tearDown(self):
        self.t.cleanup()

    def test_create_phase(self):
        new_id = commands.cmd_create_phase(
            repo_root=self.t.root, title="Tasktool",
            planning="docs/specs/phase-plan.md",
        )
        self.assertEqual(new_id, "P1")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(len(p.phases), 1)
        self.assertEqual(p.phases[0].title, "Tasktool")
        self.assertEqual(p.phases[0].planning_path, "docs/specs/phase-plan.md")

    def test_create_slice(self):
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="foundation")
        new_id = commands.cmd_create_slice(
            repo_root=self.t.root, phase_id="P1", title="CLI core",
            depends_on=["P1.S1"], parallel_group="bootstrap",
        )
        self.assertEqual(new_id, "S2")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[1].title, "CLI core")
        self.assertEqual(p.phases[0].slices[1].depends_on, ["P1.S1"])
        self.assertEqual(p.phases[0].slices[1].parallel_group, "bootstrap")

    def test_create_followup_slice(self):
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
        fid = commands.cmd_create_slice(
            repo_root=self.t.root, phase_id="P1", title="S1a", follow_up="S1",
        )
        self.assertEqual(fid, "S1a")

    def test_create_task(self):
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
        new_id = commands.cmd_create_task(
            repo_root=self.t.root, slice_id="P1.S1", title="implement",
        )
        self.assertEqual(new_id, "T1")

    def test_create_cross(self):
        new_id = commands.cmd_create_cross(repo_root=self.t.root, title="docs cleanup")
        self.assertEqual(new_id, "X1")

    def test_create_emits_ready_notification(self):
        log = self.t.root / "notify.jsonl"
        with patch.dict(
            os.environ,
            {"SUPERSTAR_NOTIFY_DISABLE": "0", "SUPERSTAR_NOTIFY_DRY_RUN": "1", "SUPERSTAR_NOTIFY_LOG": str(log)},
        ):
            new_id = commands.cmd_create_phase(repo_root=self.t.root, title="Tasktool")
        events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(new_id, "P1")
        self.assertEqual(events[-1]["type"], "tasktool-status")
        self.assertEqual(events[-1]["id"], "P1")
        self.assertEqual(events[-1]["status"], "ready")
        self.assertEqual(events[-1]["message"], "P1 ready: Tasktool")


class CrossArchiveTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")

    def tearDown(self):
        self.t.cleanup()

    def test_close_cross_archives_by_default(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="archive me")

        commands.cmd_close(repo_root=self.t.root, id="X1")

        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.cross_cutting, [])
        self.assertEqual(p.archived_cross_cutting[0].id, "X1")
        archive_path = self.t.root / p.archived_cross_cutting[0].archived_path
        self.assertTrue(archive_path.exists())
        self.assertIn('"id": "X1"', archive_path.read_text(encoding="utf-8"))

    def test_close_cross_no_archive_keeps_visible(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="keep visible")

        commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)

        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.cross_cutting[0].status, Status.DONE)
        self.assertEqual(p.archived_cross_cutting, [])

    def test_archive_cross_archives_done_visible_item(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="later")
        commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)

        commands.cmd_archive_cross(repo_root=self.t.root, id="X1")

        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.cross_cutting, [])
        self.assertEqual(p.archived_cross_cutting[0].id, "X1")

    def test_create_cross_does_not_reuse_archived_id(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="archived")
        commands.cmd_close(repo_root=self.t.root, id="X1")

        new_id = commands.cmd_create_cross(repo_root=self.t.root, title="new")

        self.assertEqual(new_id, "X2")

    def test_archive_cross_rejects_ready_item(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="not done")

        with self.assertRaisesRegex(commands.CommandError, "must be done before archive"):
            commands.cmd_archive_cross(repo_root=self.t.root, id="X1")

    def test_close_no_archive_rejects_non_cross_items(self):
        commands.cmd_create_phase(repo_root=self.t.root, title="phase")

        with self.assertRaisesRegex(
            commands.CommandError,
            "--no-archive is only valid for cross-cutting items",
        ):
            commands.cmd_close(
                repo_root=self.t.root,
                id="P1",
                no_archive=True,
            )

    def test_archive_cross_preserves_full_json(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="full data")
        commands.cmd_close(
            repo_root=self.t.root,
            id="X1",
            no_archive=True,
            refs=["docs/specs/example.md"],
            note="important note",
        )

        commands.cmd_archive_cross(repo_root=self.t.root, id="X1")

        p = load_project(self.t.root / "docs/tasklist.json")
        text = (self.t.root / p.archived_cross_cutting[0].archived_path).read_text(
            encoding="utf-8"
        )
        self.assertIn('"id": "X1"', text)
        self.assertIn('"refs": [', text)
        self.assertIn('"docs/specs/example.md"', text)
        self.assertIn('"notes": "important note"', text)

    def test_close_archived_cross_reports_archived_hint(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="already archived")
        commands.cmd_close(repo_root=self.t.root, id="X1")

        with self.assertRaisesRegex(commands.CommandError, "may already be archived"):
            commands.cmd_close(repo_root=self.t.root, id="X1")

    def test_archive_cross_archived_id_reports_archived_error(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="already archived")
        commands.cmd_close(repo_root=self.t.root, id="X1")

        with self.assertRaisesRegex(
            commands.CommandError,
            "cross-cutting X1 is already archived",
        ):
            commands.cmd_archive_cross(repo_root=self.t.root, id="X1")

    def test_brief_archived_cross_is_not_active_surface(self):
        from tasktool.brief import brief

        commands.cmd_create_cross(repo_root=self.t.root, title="brief archived")
        commands.cmd_close(repo_root=self.t.root, id="X1")
        p = load_project(self.t.root / "docs/tasklist.json")

        with self.assertRaisesRegex(ValueError, "X1: not found"):
            brief(p, "X1")

    def test_archive_cross_atomicity_no_orphan_file_on_validation_failure(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="atomic")
        commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)

        with patch("tasktool.commands.validate_project", side_effect=ValidationError("forced")):
            with self.assertRaises(ValidationError):
                commands.cmd_archive_cross(repo_root=self.t.root, id="X1")

        self.assertFalse((self.t.root / "docs/archived-tasks/X1-atomic.md").exists())
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.cross_cutting[0].id, "X1")

    def test_archive_cross_does_not_reemit_done_notification(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="notify once")
        log = self.t.root / "notify.jsonl"
        with patch.dict(
            os.environ,
            {
                "SUPERSTAR_NOTIFY_DISABLE": "0",
                "SUPERSTAR_NOTIFY_DRY_RUN": "1",
                "SUPERSTAR_NOTIFY_LOG": str(log),
            },
        ):
            commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)
            commands.cmd_archive_cross(repo_root=self.t.root, id="X1")

        events = [
            json.loads(line)
            for line in log.read_text(encoding="utf-8").splitlines()
        ]
        done_events = [
            event
            for event in events
            if event["id"] == "X1" and event["status"] == "done"
        ]
        self.assertEqual(len(done_events), 1)

import json

def _write_passing_chain(root: Path, name: str, verdict: str = "ready") -> Path:
    chain = root / "docs/reviewer" / name
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text(
        json.dumps({"rounds": [{"round": 1, "merged_verdict": verdict, "status": "ok"}]}),
        encoding="utf-8",
    )
    return chain

class SetStatusTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
        commands.cmd_create_task(repo_root=self.t.root, slice_id="P1.S1", title="T1")
    def tearDown(self):
        self.t.cleanup()

    def test_set_task_in_progress(self):
        commands.cmd_set(repo_root=self.t.root, id="P1.S1.T1", status="in_progress")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].tasks[0].status, Status.IN_PROGRESS)

    def test_set_task_in_progress_emits_notification(self):
        log = self.t.root / "notify.jsonl"
        with patch.dict(
            os.environ,
            {"SUPERSTAR_NOTIFY_DISABLE": "0", "SUPERSTAR_NOTIFY_DRY_RUN": "1", "SUPERSTAR_NOTIFY_LOG": str(log)},
        ):
            commands.cmd_set(repo_root=self.t.root, id="P1.S1.T1", status="in_progress")
        events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(events[-1]["id"], "P1.S1.T1")
        self.assertEqual(events[-1]["status"], "in_progress")
        self.assertEqual(events[-1]["message"], "P1.S1.T1 in progress: T1")

    def test_set_task_done_auto_stamps_closed(self):
        commands.cmd_set(repo_root=self.t.root, id="P1.S1.T1", status="done")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertIsNotNone(p.phases[0].slices[0].tasks[0].closed)

    def test_set_slice_done_requires_review_gate(self):
        with self.assertRaises(commands.CommandError):
            commands.cmd_set(repo_root=self.t.root, id="P1.S1", status="done")

    def test_set_slice_done_passes_with_chain(self):
        _write_passing_chain(self.t.root, "p1-s1-post-slice", "ready")
        commands.cmd_start(repo_root=self.t.root, id="P1.S1")
        commands.cmd_set(repo_root=self.t.root, id="P1.S1", status="done")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].status, Status.DONE)
        self.assertIsNotNone(p.phases[0].slices[0].reviewer_chain)

    def test_set_slice_done_skip_gate(self):
        commands.cmd_start(repo_root=self.t.root, id="P1.S1")
        commands.cmd_set(
            repo_root=self.t.root, id="P1.S1", status="done", skip_review_gate=True,
        )
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].status, Status.DONE)
        self.assertIn("review gate skipped", p.phases[0].slices[0].notes)

    def test_set_slice_done_ready_override_requires_reason(self):
        _write_passing_chain(self.t.root, "p1-s1-post-slice", "ready")
        with self.assertRaises(commands.CommandError) as ctx:
            commands.cmd_set(
                repo_root=self.t.root,
                id="P1.S1",
                status="done",
                allow_ready_close=True,
            )
        self.assertIn("requires --reason", str(ctx.exception))
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].status, Status.READY)

    def test_set_slice_done_ready_override_records_audit_note(self):
        _write_passing_chain(self.t.root, "p1-s1-post-slice", "ready")
        commands.cmd_set(
            repo_root=self.t.root,
            id="P1.S1",
            status="done",
            allow_ready_close=True,
            reason="legacy scripted close before lifecycle start existed",
        )
        p = load_project(self.t.root / "docs/tasklist.json")
        slc = p.phases[0].slices[0]
        self.assertEqual(slc.status, Status.DONE)
        self.assertIsNone(slc.started)
        self.assertIn(
            "ready-close override for P1.S1: legacy scripted close before lifecycle start existed",
            slc.notes,
        )

class CloseTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
    def tearDown(self):
        self.t.cleanup()

    def test_close_slice_with_chain_and_refs(self):
        _write_passing_chain(self.t.root, "p1-s1-post-slice", "ready")
        log = self.t.root / "notify.jsonl"
        with patch.dict(
            os.environ,
            {"SUPERSTAR_NOTIFY_DISABLE": "0", "SUPERSTAR_NOTIFY_DRY_RUN": "1", "SUPERSTAR_NOTIFY_LOG": str(log)},
        ):
            commands.cmd_start(repo_root=self.t.root, id="P1.S1")
            commands.cmd_close(
                repo_root=self.t.root, id="P1.S1",
                refs=["docs/a.md", "docs/b.md"], note="post-impl",
            )
        p = load_project(self.t.root / "docs/tasklist.json")
        s = p.phases[0].slices[0]
        self.assertEqual(s.status, Status.DONE)
        self.assertEqual(s.refs, ["docs/a.md", "docs/b.md"])
        self.assertIn("post-impl", s.notes)
        events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(events[-1]["id"], "P1.S1")
        self.assertEqual(events[-1]["status"], "done")

class BlockTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S2")
    def tearDown(self):
        self.t.cleanup()

    def test_block_slice_by_id(self):
        log = self.t.root / "notify.jsonl"
        with patch.dict(
            os.environ,
            {"SUPERSTAR_NOTIFY_DISABLE": "0", "SUPERSTAR_NOTIFY_DRY_RUN": "1", "SUPERSTAR_NOTIFY_LOG": str(log)},
        ):
            commands.cmd_block(repo_root=self.t.root, slice_id="P1.S1", on="P1.S2")
        p = load_project(self.t.root / "docs/tasklist.json")
        s = p.phases[0].slices[0]
        self.assertEqual(s.status, Status.BLOCKED)
        self.assertEqual(s.blocked_on.kind, "id")
        self.assertEqual(s.blocked_on.value, "P1.S2")
        events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(events[-1]["id"], "P1.S1")
        self.assertEqual(events[-1]["status"], "blocked")

    def test_block_external(self):
        commands.cmd_block(repo_root=self.t.root, slice_id="P1.S1", on="external:vendor")
        p = load_project(self.t.root / "docs/tasklist.json")
        s = p.phases[0].slices[0]
        self.assertEqual(s.blocked_on.kind, "external")
        self.assertEqual(s.blocked_on.value, "vendor")

    def test_block_rejects_task(self):
        commands.cmd_create_task(repo_root=self.t.root, slice_id="P1.S1", title="t")
        with self.assertRaises(commands.CommandError):
            commands.cmd_block(repo_root=self.t.root, slice_id="P1.S1.T1", on="P1.S2")

    def test_unblock(self):
        commands.cmd_block(repo_root=self.t.root, slice_id="P1.S1", on="P1.S2")
        log = self.t.root / "notify.jsonl"
        with patch.dict(
            os.environ,
            {"SUPERSTAR_NOTIFY_DISABLE": "0", "SUPERSTAR_NOTIFY_DRY_RUN": "1", "SUPERSTAR_NOTIFY_LOG": str(log)},
        ):
            commands.cmd_unblock(repo_root=self.t.root, slice_id="P1.S1")
        p = load_project(self.t.root / "docs/tasklist.json")
        s = p.phases[0].slices[0]
        self.assertEqual(s.status, Status.READY)
        self.assertIsNone(s.blocked_on)
        events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(events[-1]["status"], "ready")

    def test_unblock_resume_emits_in_progress_notification(self):
        commands.cmd_block(repo_root=self.t.root, slice_id="P1.S1", on="P1.S2")
        log = self.t.root / "notify.jsonl"
        with patch.dict(
            os.environ,
            {"SUPERSTAR_NOTIFY_DISABLE": "0", "SUPERSTAR_NOTIFY_DRY_RUN": "1", "SUPERSTAR_NOTIFY_LOG": str(log)},
        ):
            commands.cmd_unblock(repo_root=self.t.root, slice_id="P1.S1", resume=True)
        events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(events[-1]["id"], "P1.S1")
        self.assertEqual(events[-1]["status"], "in_progress")

class SchedulingTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(
            repo_root=self.t.root, title="P1",
            planning="docs/specs/phase-plan.md",
        )
        commands.cmd_create_slice(
            repo_root=self.t.root, phase_id="P1", title="S1",
            parallel_group="bootstrap",
        )
        commands.cmd_create_slice(
            repo_root=self.t.root, phase_id="P1", title="S2",
            depends_on=["P1.S1"], parallel_group="followup",
        )

    def tearDown(self):
        self.t.cleanup()

    def test_deps_add_remove(self):
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S3")
        commands.cmd_deps(repo_root=self.t.root, slice_id="P1.S3", add="P1.S1")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[2].depends_on, ["P1.S1"])
        commands.cmd_deps(repo_root=self.t.root, slice_id="P1.S3", remove="P1.S1")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[2].depends_on, [])

    def test_ratify_sets_planning_status_and_group(self):
        commands.cmd_ratify(
            repo_root=self.t.root, slice_id="P1.S1",
            status="ratified", parallel_group="core",
        )
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].planning_status.value, "ratified")
        self.assertEqual(p.phases[0].slices[0].parallel_group, "core")

    def test_ready_slices_respects_dependencies(self):
        out = commands.cmd_ready_slices(repo_root=self.t.root, phase_id="P1")
        self.assertIn("P1.S1", out)
        self.assertNotIn("P1.S2", out)
        commands.cmd_start(repo_root=self.t.root, id="P1.S1")
        commands.cmd_close(repo_root=self.t.root, id="P1.S1", skip_review_gate=True)
        out = commands.cmd_ready_slices(repo_root=self.t.root, phase_id="P1")
        self.assertIn("P1.S2", out)

    def test_schedule_shows_waiting_dependencies(self):
        out = commands.cmd_schedule(repo_root=self.t.root, phase_id="P1")
        self.assertIn("P1.S2", out)
        self.assertIn("waiting_on=P1.S1", out)
        self.assertIn("planning: docs/specs/phase-plan.md", out)

    def test_phase_status_lists_open_work(self):
        out = commands.cmd_phase_status(repo_root=self.t.root)
        self.assertIn("Open phases", out)
        self.assertIn("P1", out)

    def test_schedule_emits_cancelled_deps(self):
        commands.cmd_cancel(repo_root=self.t.root, id="P1.S1", reason="dropped")
        out = commands.cmd_schedule(
            repo_root=self.t.root, phase_id="P1", format="json"
        )
        rows = json.loads(out)
        s2 = next(r for r in rows if r["id"] == "P1.S2")
        self.assertEqual(s2["cancelled_deps"], ["P1.S1"])
        self.assertEqual(s2["waiting_on"], [])
        self.assertFalse(s2["ready"])

    def test_schedule_text_includes_cancelled_deps(self):
        commands.cmd_cancel(repo_root=self.t.root, id="P1.S1", reason="dropped")
        out = commands.cmd_schedule(repo_root=self.t.root, phase_id="P1")
        self.assertIn("cancelled_deps=P1.S1", out)

    def test_ready_slices_omits_slice_with_cancelled_dep(self):
        commands.cmd_cancel(repo_root=self.t.root, id="P1.S1", reason="dropped")
        out = commands.cmd_ready_slices(repo_root=self.t.root, phase_id="P1")
        self.assertNotIn("P1.S2", out)

    def test_list_open_omits_child_tasks_of_cancelled_slice(self):
        # Add a ready task under P1.S1, then cancel the slice.
        commands.cmd_create_task(
            repo_root=self.t.root, slice_id="P1.S1", title="ready task",
        )
        out_before = commands.cmd_list(
            repo_root=self.t.root, open_only=True, format="json",
        )
        rows_before = json.loads(out_before)
        self.assertTrue(
            any(r["id"] == "P1.S1.T1" for r in rows_before),
            f"expected P1.S1.T1 ready before cancel: {rows_before}",
        )
        commands.cmd_cancel(
            repo_root=self.t.root, id="P1.S1", reason="dropped",
        )
        out_after = commands.cmd_list(
            repo_root=self.t.root, open_only=True, format="json",
        )
        rows_after = json.loads(out_after)
        ids_after = {r["id"] for r in rows_after}
        self.assertNotIn(
            "P1.S1.T1", ids_after,
            f"child task should be suppressed under cancelled parent: {rows_after}",
        )
        # And the cancelled slice itself is not "open".
        self.assertNotIn("P1.S1", ids_after)

    def test_list_open_omits_child_tasks_of_cascaded_phase(self):
        # Add a task under each slice, then cascade-cancel the phase.
        commands.cmd_create_task(
            repo_root=self.t.root, slice_id="P1.S1", title="t-a",
        )
        commands.cmd_create_task(
            repo_root=self.t.root, slice_id="P1.S2", title="t-b",
        )
        commands.cmd_cancel(
            repo_root=self.t.root, id="P1", reason="pivot", cascade=True,
        )
        out = commands.cmd_list(
            repo_root=self.t.root, open_only=True, format="json",
        )
        rows = json.loads(out)
        ids = {r["id"] for r in rows}
        self.assertNotIn("P1.S1.T1", ids)
        self.assertNotIn("P1.S2.T1", ids)

    def test_show_slice_still_emits_child_tasks_after_cancel(self):
        commands.cmd_create_task(
            repo_root=self.t.root, slice_id="P1.S1", title="kept task",
        )
        commands.cmd_cancel(
            repo_root=self.t.root, id="P1.S1", reason="dropped",
        )
        out = commands.cmd_show(repo_root=self.t.root, id="P1.S1")
        # Cancelled slice still surfaces child tasks via show.
        self.assertIn("T1", out)
        self.assertIn("kept task", out)
        # Child task status was not mutated: it remains "ready" (pre-cancel).
        p = load_project(self.t.root / "docs/tasklist.json")
        s1 = p.phases[0].slices[0]
        self.assertEqual(s1.tasks[0].status, Status.READY)

    def test_brief_surfaces_cancellation_reason_for_active_cancelled_slice(self):
        commands.cmd_cancel(
            repo_root=self.t.root, id="P1.S1", reason="scope dropped",
        )
        out = commands.cmd_brief(repo_root=self.t.root, id="P1.S1")
        self.assertIn("scope dropped", out)
        reason_pos = out.find("scope dropped")
        title_pos = out.find("# P1.S1")
        self.assertNotEqual(reason_pos, -1)
        self.assertNotEqual(title_pos, -1)
        self.assertLess(reason_pos, title_pos)

    def test_show_surfaces_reason_for_active_cancelled_x(self):
        x_id = commands.cmd_create_cross(
            repo_root=self.t.root, title="cross thing",
        )
        commands.cmd_cancel(
            repo_root=self.t.root, id=x_id, reason="defer",
            no_archive=True,
        )
        out = commands.cmd_show(repo_root=self.t.root, id=x_id)
        self.assertIn("Cancelled ", out)
        self.assertIn("defer", out)

    def test_show_returns_not_found_for_archived_cancelled_x(self):
        x_id = commands.cmd_create_cross(
            repo_root=self.t.root, title="archive me",
        )
        # Default cancel auto-archives the cross-cutting row.
        commands.cmd_cancel(repo_root=self.t.root, id=x_id, reason="defer")
        with self.assertRaises(commands.CommandError) as ctx:
            commands.cmd_show(repo_root=self.t.root, id=x_id)
        self.assertIn("not found in active tasklist", str(ctx.exception))

    def test_phase_status_excludes_cancelled_phase(self):
        commands.cmd_cancel(
            repo_root=self.t.root, id="P1", reason="pivot", cascade=True,
        )
        out = commands.cmd_phase_status(repo_root=self.t.root, format="json")
        data = json.loads(out)
        open_phase_ids = {ph["id"] for ph in data["open_phases"]}
        self.assertNotIn("P1", open_phase_ids)

    def test_phase_status_excludes_cancelled_no_archive_cross(self):
        x_id = commands.cmd_create_cross(
            repo_root=self.t.root, title="X-thing",
        )
        commands.cmd_cancel(
            repo_root=self.t.root, id=x_id, reason="dropped",
            no_archive=True,
        )
        out = commands.cmd_phase_status(repo_root=self.t.root, format="json")
        data = json.loads(out)
        open_x_ids = {c["id"] for c in data["open_cross_cutting"]}
        self.assertNotIn(x_id, open_x_ids)

class ShortFormResolutionTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
        commands.cmd_create_task(repo_root=self.t.root, slice_id="P1.S1", title="t")
    def tearDown(self):
        self.t.cleanup()

    def test_short_slice_unambiguous_resolves(self):
        # Only one slice in the project — short form S1 should resolve.
        commands.cmd_note(repo_root=self.t.root, id="S1", append="via short")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertIn("via short", p.phases[0].slices[0].notes)

    def test_short_task_unambiguous_resolves(self):
        commands.cmd_note(repo_root=self.t.root, id="T1", append="via short")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertIn("via short", p.phases[0].slices[0].tasks[0].notes)

    def test_short_slice_ambiguous_rejected(self):
        commands.cmd_create_phase(repo_root=self.t.root, title="P2")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P2", title="S1")
        with self.assertRaises(commands.CommandError) as ctx:
            commands.cmd_note(repo_root=self.t.root, id="S1", append="x")
        self.assertIn("ambiguous", str(ctx.exception).lower())

    def test_create_task_accepts_short_slice(self):
        new_id = commands.cmd_create_task(repo_root=self.t.root, slice_id="S1", title="t2")
        self.assertEqual(new_id, "T2")

class NoteRefTitleTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
    def tearDown(self):
        self.t.cleanup()

    def test_note_append(self):
        commands.cmd_note(repo_root=self.t.root, id="P1.S1", append="hello")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].notes, "hello")
        commands.cmd_note(repo_root=self.t.root, id="P1.S1", append="world")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].notes, "hello\nworld")

    def test_note_replace(self):
        commands.cmd_note(repo_root=self.t.root, id="P1.S1", append="hello")
        commands.cmd_note(repo_root=self.t.root, id="P1.S1", replace="fresh")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].notes, "fresh")

    def test_ref_add_remove(self):
        commands.cmd_ref(repo_root=self.t.root, id="P1.S1", add="docs/a.md")
        commands.cmd_ref(repo_root=self.t.root, id="P1.S1", add="docs/b.md")
        commands.cmd_ref(repo_root=self.t.root, id="P1.S1", remove="docs/a.md")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].refs, ["docs/b.md"])

    def test_title_set(self):
        commands.cmd_title(repo_root=self.t.root, id="P1.S1", new="renamed")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].title, "renamed")

class ShowListTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1 title")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1 title")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S2 title")
        commands.cmd_create_task(repo_root=self.t.root, slice_id="P1.S1", title="t1")
    def tearDown(self):
        self.t.cleanup()

    def test_show_phase(self):
        out = commands.cmd_show(repo_root=self.t.root, id="P1")
        self.assertIn("P1 title", out)
        self.assertIn("S1", out)
        self.assertIn("S2", out)

    def test_show_slice(self):
        out = commands.cmd_show(repo_root=self.t.root, id="P1.S1")
        self.assertIn("S1 title", out)
        self.assertIn("T1", out)

    def test_list_filter_status_open(self):
        out = commands.cmd_list(repo_root=self.t.root, open_only=True)
        self.assertIn("P1.S1", out)

    def test_list_format_json(self):
        out = commands.cmd_list(repo_root=self.t.root, format="json")
        import json as _j
        data = _j.loads(out)
        self.assertIsInstance(data, list)

class NextIdTests(unittest.TestCase):
    def test_next_phase_empty(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            self.assertEqual(
                commands.cmd_next_id(repo_root=t.root, kind="phase"), "P1",
            )
        finally:
            t.cleanup()

class ValidateCmdTests(unittest.TestCase):
    def test_validate_clean(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            rc, out = commands.cmd_validate(repo_root=t.root)
            self.assertEqual(rc, 0)
        finally:
            t.cleanup()

    def test_validate_strict_format_detects_drift(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            path = t.root / "docs/tasklist.json"
            path.write_text(path.read_text().replace("  ", "    "), encoding="utf-8")
            rc, out = commands.cmd_validate(repo_root=t.root, strict_format=True)
            self.assertEqual(rc, 1)
        finally:
            t.cleanup()

    def test_validate_normalise_fixes(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            path = t.root / "docs/tasklist.json"
            path.write_text(path.read_text().replace("  ", "    "), encoding="utf-8")
            rc, _ = commands.cmd_validate(repo_root=t.root, normalise=True)
            self.assertEqual(rc, 0)
            rc, _ = commands.cmd_validate(repo_root=t.root, strict_format=True)
            self.assertEqual(rc, 0)
        finally:
            t.cleanup()

class SchemaCmdTests(unittest.TestCase):
    def test_schema_emits_valid_json(self):
        out = commands.cmd_schema()
        import json as _j
        data = _j.loads(out)
        self.assertEqual(data["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertIn("properties", data)
        self.assertIn("phases", data["properties"])

import subprocess as _sp

class GitStageTests(unittest.TestCase):
    def test_writes_stage_file_when_in_git_repo(self):
        t = _Tmp()
        try:
            _sp.run(["git", "init", "-q"], cwd=t.root, check=True)
            _sp.run(["git", "config", "user.email", "t@t"], cwd=t.root, check=True)
            _sp.run(["git", "config", "user.name", "t"], cwd=t.root, check=True)
            commands.cmd_init(repo_root=t.root, project="demo")
            staged = _sp.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=t.root, capture_output=True, text=True, check=True,
            ).stdout
            self.assertIn("docs/tasklist.json", staged)
        finally:
            t.cleanup()

    def test_writes_silent_when_not_in_git_repo(self):
        t = _Tmp()
        try:
            # No git init. Should not raise.
            commands.cmd_init(repo_root=t.root, project="demo")
            self.assertTrue((t.root / "docs/tasklist.json").exists())
        finally:
            t.cleanup()

    def test_no_stage_skips_git_add(self):
        t = _Tmp()
        try:
            _sp.run(["git", "init", "-q"], cwd=t.root, check=True)
            _sp.run(["git", "config", "user.email", "t@t"], cwd=t.root, check=True)
            _sp.run(["git", "config", "user.name", "t"], cwd=t.root, check=True)
            commands.STAGE_AFTER_WRITE = False
            try:
                commands.cmd_init(repo_root=t.root, project="demo")
            finally:
                commands.STAGE_AFTER_WRITE = True
            staged = _sp.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=t.root, capture_output=True, text=True, check=True,
            ).stdout
            self.assertNotIn("docs/tasklist.json", staged)
        finally:
            t.cleanup()


class ArchivePhaseTests(unittest.TestCase):
    def test_archive_phase_writes_summary_and_moves_to_archived(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            pid = commands.cmd_create_phase(repo_root=t.root, title="A phase")
            sid = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="Only slice")
            commands.cmd_start(repo_root=t.root, id=f"{pid}.{sid}")
            commands.cmd_close(
                repo_root=t.root, id=f"{pid}.{sid}",
                skip_review_gate=True,
            )
            commands.cmd_archive_phase(repo_root=t.root, phase_id=pid, skip_review_gate=True)
            p = load_project(t.root / "docs" / "tasklist.json")
            self.assertFalse(any(ph.id == pid for ph in p.phases))
            self.assertEqual([a.id for a in p.archived_phases], [pid])
            arch_path = t.root / p.archived_phases[0].archived_path
            self.assertTrue(arch_path.exists())
            body = arch_path.read_text(encoding="utf-8")
            self.assertIn(f"# {pid} —", body)
            self.assertIn("```json", body)
        finally:
            t.cleanup()

    def test_archive_phase_refuses_with_open_slices(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
            commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="open slice")
            with self.assertRaises(commands.CommandError) as cm:
                commands.cmd_archive_phase(repo_root=t.root, phase_id=pid, skip_review_gate=True)
            self.assertIn("open slices", str(cm.exception).lower())
        finally:
            t.cleanup()

    def test_archive_phase_accepts_cancelled_phase_skipping_gate(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            pid = commands.cmd_create_phase(repo_root=t.root, title="cancelled phase")
            commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="S1")
            # Cancel the phase (cascades the single open slice).
            commands.cmd_cancel(
                repo_root=t.root, id=pid, reason="pivoting", cascade=True
            )
            # No reviewer chain, no skip flag — cancelled phase must bypass gate.
            commands.cmd_archive_phase(repo_root=t.root, phase_id=pid)
            p = load_project(t.root / "docs" / "tasklist.json")
            self.assertTrue(any(a.id == pid for a in p.archived_phases))
            self.assertFalse(any(ph.id == pid for ph in p.phases))
            # Archive markdown records cancelled status, not done.
            arch_path = t.root / next(
                a for a in p.archived_phases if a.id == pid
            ).archived_path
            body = arch_path.read_text(encoding="utf-8")
            self.assertIn("status: cancelled", body)
            self.assertNotIn("status: done", body)
            # Skip-note appended to phase notes (persisted in archive JSON).
            self.assertIn(
                "Phase cancelled; post-phase review gate skipped", body
            )
        finally:
            t.cleanup()

    def test_archive_phase_refuses_cancelled_phase_with_open_slices(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            pid = commands.cmd_create_phase(repo_root=t.root, title="cancelled phase")
            commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="S1")
            # Hand-craft inconsistent state: phase cancelled but a slice still
            # in a non-terminal status. Edit the on-disk tasklist directly.
            from tasktool.serialize import dumps_canonical
            path = t.root / "docs" / "tasklist.json"
            p = load_project(path)
            phase = next(ph for ph in p.phases if ph.id == pid)
            phase.status = Status.CANCELLED
            phase.closed = _dt.date.today().isoformat()
            # Slice S1 is still status=ready (default) — open.
            path.write_text(dumps_canonical(p), encoding="utf-8")
            with self.assertRaises(commands.CommandError) as cm:
                commands.cmd_archive_phase(repo_root=t.root, phase_id=pid)
            self.assertIn("open", str(cm.exception).lower())
        finally:
            t.cleanup()

    def test_archive_phase_notifier_uses_real_status_for_cancelled(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            pid = commands.cmd_create_phase(repo_root=t.root, title="cancelled phase")
            commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="S1")
            commands.cmd_cancel(
                repo_root=t.root, id=pid, reason="pivoting", cascade=True
            )
            log = t.root / "notify.jsonl"
            with patch.dict(
                os.environ,
                {
                    "SUPERSTAR_NOTIFY_DISABLE": "0",
                    "SUPERSTAR_NOTIFY_DRY_RUN": "1",
                    "SUPERSTAR_NOTIFY_LOG": str(log),
                },
            ):
                commands.cmd_archive_phase(repo_root=t.root, phase_id=pid)
            events = [
                json.loads(line)
                for line in log.read_text(encoding="utf-8").splitlines()
            ]
            archive_events = [e for e in events if e["id"] == pid]
            self.assertTrue(archive_events, "expected an archive event for the phase")
            self.assertEqual(archive_events[-1]["status"], "cancelled")
            self.assertTrue(all(e["status"] != "done" for e in archive_events))
        finally:
            t.cleanup()

    def test_archive_phase_done_phase_still_emits_done_notification(self):
        # Regression guard: non-cancelled phase must continue to notify done.
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            pid = commands.cmd_create_phase(repo_root=t.root, title="done phase")
            sid = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="S1")
            commands.cmd_start(repo_root=t.root, id=f"{pid}.{sid}")
            commands.cmd_close(
                repo_root=t.root, id=f"{pid}.{sid}", skip_review_gate=True,
            )
            log = t.root / "notify.jsonl"
            with patch.dict(
                os.environ,
                {
                    "SUPERSTAR_NOTIFY_DISABLE": "0",
                    "SUPERSTAR_NOTIFY_DRY_RUN": "1",
                    "SUPERSTAR_NOTIFY_LOG": str(log),
                },
            ):
                commands.cmd_archive_phase(
                    repo_root=t.root, phase_id=pid, skip_review_gate=True,
                )
            events = [
                json.loads(line)
                for line in log.read_text(encoding="utf-8").splitlines()
            ]
            archive_events = [
                e for e in events if e["id"] == pid and e["kind"] == "phase"
            ]
            self.assertTrue(archive_events, "expected a phase notify event")
            self.assertEqual(archive_events[-1]["status"], "done")
        finally:
            t.cleanup()


import datetime as _dt


class CancelTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S2")
        commands.cmd_create_task(repo_root=self.t.root, slice_id="P1.S1", title="T1")

    def tearDown(self):
        self.t.cleanup()

    def _slice(self, qid="P1.S1"):
        p = load_project(self.t.root / "docs/tasklist.json")
        phase_id, slice_id = qid.split(".")
        ph = next(x for x in p.phases if x.id == phase_id)
        return next(s for s in ph.slices if s.id == slice_id)

    def test_cancel_slice_stamps_status_closed_and_audit_note(self):
        commands.cmd_cancel(
            repo_root=self.t.root, id="P1.S1", reason="scope dropped"
        )
        s = self._slice()
        self.assertEqual(s.status, Status.CANCELLED)
        self.assertEqual(s.closed, _dt.date.today().isoformat())
        self.assertIn("Cancelled ", s.notes)
        self.assertIn("scope dropped", s.notes)

    def test_cancel_requires_reason_none(self):
        with self.assertRaisesRegex(commands.CommandError, "--reason"):
            commands.cmd_cancel(repo_root=self.t.root, id="P1.S1", reason=None)

    def test_cancel_requires_reason_empty(self):
        with self.assertRaisesRegex(commands.CommandError, "--reason"):
            commands.cmd_cancel(repo_root=self.t.root, id="P1.S1", reason="")

    def test_cancel_requires_reason_whitespace(self):
        with self.assertRaisesRegex(commands.CommandError, "--reason"):
            commands.cmd_cancel(repo_root=self.t.root, id="P1.S1", reason="   ")

    def test_cancel_rejects_task_id(self):
        with self.assertRaisesRegex(
            commands.CommandError, "cancel does not apply to tasks"
        ):
            commands.cmd_cancel(
                repo_root=self.t.root, id="P1.S1.T1", reason="x"
            )

    def test_cancel_rejects_already_terminal(self):
        # Mark P1.S1 cancelled first, then try again.
        commands.cmd_cancel(repo_root=self.t.root, id="P1.S1", reason="first")
        with self.assertRaisesRegex(commands.CommandError, "already"):
            commands.cmd_cancel(repo_root=self.t.root, id="P1.S1", reason="second")

    def test_cancel_no_archive_rejected_for_slice(self):
        with self.assertRaisesRegex(commands.CommandError, "--no-archive"):
            commands.cmd_cancel(
                repo_root=self.t.root, id="P1.S1", reason="x", no_archive=True
            )

    def test_cancel_cascade_rejected_for_slice(self):
        with self.assertRaisesRegex(commands.CommandError, "--cascade"):
            commands.cmd_cancel(
                repo_root=self.t.root, id="P1.S1", reason="x", cascade=True
            )

    def test_cancel_clears_review_state(self):
        # Drive the slice into a state with active review and a workflow_step set,
        # then cancel; review fields must clear, workflow_step must remain.
        commands.cmd_set(
            self.t.root, id="P1.S1",
            workflow_step="implement",
            review_active=True,
            review_stage="awaiting_response",
        )
        commands.cmd_cancel(repo_root=self.t.root, id="P1.S1", reason="dropped")
        s = self._slice()
        self.assertEqual(s.status, Status.CANCELLED)
        self.assertFalse(s.review_active)
        self.assertIsNone(s.review_stage)
        # workflow_step is informative on cancelled rows and must survive.
        self.assertIsNotNone(s.workflow_step)
        self.assertEqual(s.workflow_step.value, "implement")

    def test_cancel_slice_emits_cancelled_notification_once(self):
        log = self.t.root / "notify.jsonl"
        with patch.dict(
            os.environ,
            {
                "SUPERSTAR_NOTIFY_DISABLE": "0",
                "SUPERSTAR_NOTIFY_DRY_RUN": "1",
                "SUPERSTAR_NOTIFY_LOG": str(log),
            },
        ):
            commands.cmd_cancel(repo_root=self.t.root, id="P1.S1", reason="x")
        events = [
            json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()
        ]
        cancel_events = [e for e in events if e["id"] == "P1.S1" and e["status"] == "cancelled"]
        self.assertEqual(len(cancel_events), 1)


class CancelCrossTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_cross(repo_root=self.t.root, title="cross item")

    def tearDown(self):
        self.t.cleanup()

    def test_cancel_cross_auto_archives_with_status_cancelled(self):
        commands.cmd_cancel(repo_root=self.t.root, id="X1", reason="superseded")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertTrue(all(c.id != "X1" for c in p.cross_cutting))
        archived = next(a for a in p.archived_cross_cutting if a.id == "X1")
        text = (self.t.root / archived.archived_path).read_text(encoding="utf-8")
        self.assertIn("status: cancelled", text)

    def test_cancel_cross_no_archive_keeps_visible(self):
        commands.cmd_cancel(
            repo_root=self.t.root, id="X1", reason="defer", no_archive=True
        )
        p = load_project(self.t.root / "docs/tasklist.json")
        x = next(c for c in p.cross_cutting if c.id == "X1")
        self.assertEqual(x.status, Status.CANCELLED)
        self.assertEqual(p.archived_cross_cutting, [])

    def test_archive_cross_after_cancel_no_archive_preserves_status(self):
        commands.cmd_cancel(
            repo_root=self.t.root, id="X1", reason="defer", no_archive=True
        )
        commands.cmd_archive_cross(repo_root=self.t.root, id="X1")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertTrue(all(c.id != "X1" for c in p.cross_cutting))
        archived = next(a for a in p.archived_cross_cutting if a.id == "X1")
        body = (self.t.root / archived.archived_path).read_text(encoding="utf-8")
        self.assertIn("status: cancelled", body)
        self.assertNotIn("status: done", body)

    def test_cancel_cross_emits_cancelled_notification_once(self):
        log = self.t.root / "notify.jsonl"
        with patch.dict(
            os.environ,
            {
                "SUPERSTAR_NOTIFY_DISABLE": "0",
                "SUPERSTAR_NOTIFY_DRY_RUN": "1",
                "SUPERSTAR_NOTIFY_LOG": str(log),
            },
        ):
            commands.cmd_cancel(repo_root=self.t.root, id="X1", reason="x")
        events = [
            json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()
        ]
        cancel_events = [e for e in events if e["id"] == "X1" and e["status"] == "cancelled"]
        self.assertEqual(len(cancel_events), 1)


class CancelPhaseTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S2")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S3")

    def tearDown(self):
        self.t.cleanup()

    def _phase(self):
        p = load_project(self.t.root / "docs/tasklist.json")
        return next(x for x in p.phases if x.id == "P1")

    def _slice(self, sid):
        ph = self._phase()
        return next(s for s in ph.slices if s.id == sid)

    def _close_slice(self, sid):
        commands.cmd_start(repo_root=self.t.root, id=f"P1.{sid}")
        commands.cmd_close(
            repo_root=self.t.root, id=f"P1.{sid}", skip_review_gate=True
        )

    def test_cancel_phase_refuses_with_open_slices(self):
        with self.assertRaisesRegex(commands.CommandError, "open"):
            commands.cmd_cancel(repo_root=self.t.root, id="P1", reason="pivoting")

    def test_cancel_phase_refuses_lists_open_slice_ids(self):
        # Close S1 so only S2/S3 are open; error should list them.
        self._close_slice("S1")
        with self.assertRaisesRegex(commands.CommandError, "S2.*S3"):
            commands.cmd_cancel(repo_root=self.t.root, id="P1", reason="pivot")

    def test_cancel_phase_succeeds_when_all_slices_terminal(self):
        # S1 done, S2 cancelled, S3 cancelled -> phase cancels without --cascade.
        self._close_slice("S1")
        commands.cmd_cancel(repo_root=self.t.root, id="P1.S2", reason="dropped")
        commands.cmd_cancel(repo_root=self.t.root, id="P1.S3", reason="dropped")
        commands.cmd_cancel(repo_root=self.t.root, id="P1", reason="rollup")
        ph = self._phase()
        self.assertEqual(ph.status, Status.CANCELLED)
        self.assertEqual(ph.closed, _dt.date.today().isoformat())
        # Done child untouched
        s1 = self._slice("S1")
        self.assertEqual(s1.status, Status.DONE)

    def test_cancel_phase_cascade_cancels_open_leaves_done(self):
        # S1 done, S2 ready, S3 in_progress
        self._close_slice("S1")
        commands.cmd_start(repo_root=self.t.root, id="P1.S3")
        s1_closed_before = self._slice("S1").closed
        commands.cmd_cancel(
            repo_root=self.t.root, id="P1", reason="pivot", cascade=True
        )
        ph = self._phase()
        s1 = self._slice("S1")
        s2 = self._slice("S2")
        s3 = self._slice("S3")
        self.assertEqual(ph.status, Status.CANCELLED)
        self.assertEqual(s1.status, Status.DONE)
        self.assertEqual(s1.closed, s1_closed_before)
        self.assertEqual(s2.status, Status.CANCELLED)
        self.assertEqual(s3.status, Status.CANCELLED)
        self.assertIn("(cascaded from P1)", s2.notes)
        self.assertIn("(cascaded from P1)", s3.notes)
        self.assertEqual(s2.closed, _dt.date.today().isoformat())
        self.assertEqual(s3.closed, _dt.date.today().isoformat())

    def test_cancel_phase_cascade_notifies_each_cascaded_child_and_phase(self):
        self._close_slice("S1")
        log = self.t.root / "notify.jsonl"
        with patch.dict(
            os.environ,
            {
                "SUPERSTAR_NOTIFY_DISABLE": "0",
                "SUPERSTAR_NOTIFY_DRY_RUN": "1",
                "SUPERSTAR_NOTIFY_LOG": str(log),
            },
        ):
            commands.cmd_cancel(
                repo_root=self.t.root, id="P1", reason="pivot", cascade=True
            )
        events = [
            json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()
        ]
        ids_with_cancel = sorted(
            e["id"] for e in events if e["status"] == "cancelled"
        )
        self.assertEqual(ids_with_cancel, ["P1", "P1.S2", "P1.S3"])
        # The done slice S1 must NOT emit a cancel event.
        self.assertFalse(
            any(e["id"] == "P1.S1" and e["status"] == "cancelled" for e in events)
        )


class CancelledRowGuardTests(unittest.TestCase):
    """Lifecycle-adjacent commands must refuse to mutate cancelled rows
    (except note --append, ref add/remove, and title)."""

    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S2")
        commands.cmd_cancel(
            repo_root=self.t.root, id="P1.S1", reason="scope dropped"
        )

    def tearDown(self):
        self.t.cleanup()

    def _slice(self, qid="P1.S1"):
        p = load_project(self.t.root / "docs/tasklist.json")
        phase_id, slice_id = qid.split(".")
        ph = next(x for x in p.phases if x.id == phase_id)
        return next(s for s in ph.slices if s.id == slice_id)

    def test_cmd_close_refuses_cancelled(self):
        with self.assertRaisesRegex(commands.CommandError, "cancelled"):
            commands.cmd_close(
                repo_root=self.t.root, id="P1.S1", skip_review_gate=True
            )

    def test_cmd_set_refuses_cancelled_for_all_new_statuses(self):
        for new in ("ready", "in_progress", "done"):
            with self.assertRaisesRegex(commands.CommandError, "cancelled"):
                commands.cmd_set(
                    repo_root=self.t.root, id="P1.S1", status=new,
                    skip_review_gate=True,
                )

    def test_cmd_set_refuses_status_cancelled_with_hint(self):
        # Defense in depth: even on a non-cancelled row, status="cancelled"
        # must be rejected and point at `tasktool cancel`.
        with self.assertRaisesRegex(commands.CommandError, "tasktool cancel"):
            commands.cmd_set(
                repo_root=self.t.root, id="P1.S2", status="cancelled",
            )

    def test_cmd_start_refuses_cancelled(self):
        with self.assertRaisesRegex(commands.CommandError, "cancelled"):
            commands.cmd_start(repo_root=self.t.root, id="P1.S1")

    def test_cmd_block_refuses_cancelled(self):
        with self.assertRaisesRegex(commands.CommandError, "cancelled"):
            commands.cmd_block(
                repo_root=self.t.root, slice_id="P1.S1", on="P1.S2"
            )

    def test_cmd_unblock_refuses_cancelled(self):
        with self.assertRaisesRegex(commands.CommandError, "cancelled"):
            commands.cmd_unblock(repo_root=self.t.root, slice_id="P1.S1")

    def test_cmd_deps_add_refuses_cancelled(self):
        with self.assertRaisesRegex(commands.CommandError, "cancelled"):
            commands.cmd_deps(
                repo_root=self.t.root, slice_id="P1.S1", add="P1.S2"
            )

    def test_cmd_deps_remove_refuses_cancelled(self):
        with self.assertRaisesRegex(commands.CommandError, "cancelled"):
            commands.cmd_deps(
                repo_root=self.t.root, slice_id="P1.S1", remove="P1.S2"
            )

    def test_cmd_ratify_refuses_cancelled(self):
        with self.assertRaisesRegex(commands.CommandError, "cancelled"):
            commands.cmd_ratify(
                repo_root=self.t.root, slice_id="P1.S1", status="ratified"
            )

    def test_cmd_note_replace_refuses_cancelled_with_append_hint(self):
        with self.assertRaisesRegex(commands.CommandError, "--append"):
            commands.cmd_note(
                repo_root=self.t.root, id="P1.S1", replace="overwrite"
            )

    def test_cmd_note_append_allowed_on_cancelled(self):
        commands.cmd_note(
            repo_root=self.t.root, id="P1.S1", append="post-mortem note"
        )
        s = self._slice("P1.S1")
        self.assertIn("post-mortem note", s.notes)

    def test_cmd_ref_add_allowed_on_cancelled(self):
        commands.cmd_ref(
            repo_root=self.t.root, id="P1.S1", add="docs/foo.md"
        )
        s = self._slice("P1.S1")
        self.assertIn("docs/foo.md", s.refs)

    def test_cmd_ref_remove_allowed_on_cancelled(self):
        commands.cmd_ref(
            repo_root=self.t.root, id="P1.S1", add="docs/foo.md"
        )
        commands.cmd_ref(
            repo_root=self.t.root, id="P1.S1", remove="docs/foo.md"
        )
        s = self._slice("P1.S1")
        self.assertNotIn("docs/foo.md", s.refs)

    def test_cmd_title_allowed_on_cancelled(self):
        commands.cmd_title(
            repo_root=self.t.root, id="P1.S1", new="new title"
        )
        s = self._slice("P1.S1")
        self.assertEqual(s.title, "new title")

    def test_cli_set_choices_do_not_include_cancelled(self):
        from tasktool import cli
        parser = cli._build_parser()
        # Find the 'set' subparser action and verify --status choices.
        set_action = None
        for action in parser._actions:
            if hasattr(action, "choices") and isinstance(action.choices, dict):
                if "set" in action.choices:
                    set_action = action.choices["set"]
                    break
        self.assertIsNotNone(set_action)
        status_arg = next(
            a for a in set_action._actions
            if "--status" in getattr(a, "option_strings", [])
        )
        self.assertNotIn("cancelled", status_arg.choices)
# ── P6.S1 Task 4: cmd_set workflow-step / review flags ──
import pytest  # noqa: E402  (placed at file end for cohesion with new P6.S1 tests)


def test_set_workflow_step_on_slice(tmp_project_with_p6_s1):
    p = tmp_project_with_p6_s1
    commands.cmd_set(p, id="P6.S1", workflow_step="plan")
    state = commands.load_project(p / "docs" / "tasklist.json")
    s = state.phases[0].slices[0]
    assert s.workflow_step.value == "plan"


def test_set_workflow_step_on_slice_emits_notification(tmp_project_with_p6_s1, monkeypatch):
    p = tmp_project_with_p6_s1
    calls = []
    monkeypatch.setattr(commands, "notify_tasktool_workflow_step", lambda **kwargs: calls.append(kwargs))

    commands.cmd_set(p, id="P6.S1", workflow_step="plan")

    assert calls == [
        {
            "work_id": "P6.S1",
            "kind": "slice",
            "step": "plan",
            "title": "t",
        }
    ]


def test_set_workflow_step_on_phase(tmp_project_with_p6_s1):
    p = tmp_project_with_p6_s1
    commands.cmd_set(p, id="P6", workflow_step="ready")
    state = commands.load_project(p / "docs" / "tasklist.json")
    assert state.phases[0].workflow_step.value == "ready"


def test_set_workflow_step_on_phase_emits_notification(tmp_project_with_p6_s1, monkeypatch):
    p = tmp_project_with_p6_s1
    calls = []
    monkeypatch.setattr(commands, "notify_tasktool_workflow_step", lambda **kwargs: calls.append(kwargs))

    commands.cmd_set(p, id="P6", workflow_step="ready")

    assert calls == [
        {
            "work_id": "P6",
            "kind": "phase",
            "step": "ready",
            "title": "t",
        }
    ]


def test_set_same_workflow_step_does_not_emit_notification(tmp_project_with_p6_s1, monkeypatch):
    p = tmp_project_with_p6_s1
    commands.cmd_set(p, id="P6.S1", workflow_step="plan")
    calls = []
    monkeypatch.setattr(commands, "notify_tasktool_workflow_step", lambda **kwargs: calls.append(kwargs))

    commands.cmd_set(p, id="P6.S1", workflow_step="plan")

    assert calls == []


def test_set_rejects_no_op_invocation(tmp_project_with_p6_s1):
    p = tmp_project_with_p6_s1
    with pytest.raises(commands.UsageError, match="at least one mutating flag"):
        commands.cmd_set(p, id="P6.S1")


def test_set_rejects_workflow_step_and_clear(tmp_project_with_p6_s1):
    p = tmp_project_with_p6_s1
    with pytest.raises(commands.UsageError, match="mutually exclusive"):
        commands.cmd_set(p, id="P6.S1", workflow_step="plan", clear_workflow_step=True)


def test_set_rejects_review_active_false_with_stage(tmp_project_with_p6_s1):
    p = tmp_project_with_p6_s1
    with pytest.raises(commands.UsageError, match="review-stage cannot be set"):
        commands.cmd_set(p, id="P6.S1", review_active=False, review_stage="passed")


def test_set_rejects_review_flags_on_phase(tmp_project_with_p6_s1):
    p = tmp_project_with_p6_s1
    with pytest.raises(commands.UsageError, match="review.*only.*slice"):
        commands.cmd_set(p, id="P6", review_active=True)


def test_set_rejects_slice_step_value_on_phase(tmp_project_with_p6_s1):
    p = tmp_project_with_p6_s1
    with pytest.raises(commands.UsageError, match="not valid for phase"):
        commands.cmd_set(p, id="P6", workflow_step="plan")


def test_set_rejects_phase_step_value_on_slice(tmp_project_with_p6_s1):
    p = tmp_project_with_p6_s1
    with pytest.raises(commands.UsageError, match="not valid for slice"):
        commands.cmd_set(p, id="P6.S1", workflow_step="ready")


def test_set_status_only_still_works(tmp_project_with_p6_s1):
    p = tmp_project_with_p6_s1
    commands.cmd_set(p, id="P6.S1", status="in_progress")
    state = commands.load_project(p / "docs" / "tasklist.json")
    assert state.phases[0].slices[0].status.value == "in_progress"


def test_set_workflow_step_clears_review_block(tmp_project_with_p6_s1):
    p = tmp_project_with_p6_s1
    commands.cmd_set(p, id="P6.S1", review_active=True, review_stage="awaiting_response")
    commands.cmd_set(p, id="P6.S1", workflow_step="plan")
    state = commands.load_project(p / "docs" / "tasklist.json")
    s = state.phases[0].slices[0]
    assert s.review_active is False
    assert s.review_stage is None


def test_clear_workflow_step(tmp_project_with_p6_s1):
    p = tmp_project_with_p6_s1
    commands.cmd_set(p, id="P6.S1", workflow_step="plan")
    commands.cmd_set(p, id="P6.S1", clear_workflow_step=True)
    state = commands.load_project(p / "docs" / "tasklist.json")
    assert state.phases[0].slices[0].workflow_step is None


def _make_project(slice_kwargs=None, phase_kwargs=None, extra_slices=None):
    # Slices use SHORT ids in the model — qualification is done at the CLI/lookup layer.
    from tasktool.model import Project, Phase, Slice
    s = Slice(id="S1", title="t", created="2026-05-23", **(slice_kwargs or {}))
    slices = [s] + list(extra_slices or [])
    ph = Phase(id="P6", title="t", created="2026-05-23", slices=slices, **(phase_kwargs or {}))
    return Project(project="t", phases=[ph])


def test_infer_step_slice_no_plan_no_phase_spec():
    p = _make_project()
    assert commands.infer_step_for_id(p, "P6.S1") == {"step": "spec", "blocked": False}


def test_infer_step_slice_phase_has_spec_no_plan():
    p = _make_project(phase_kwargs={"spec_path": "docs/specs/P6.md"})
    assert commands.infer_step_for_id(p, "P6.S1") == {"step": "spec", "blocked": False}


def test_infer_step_slice_plan_proposed():
    from tasktool.model import PlanningStatus
    p = _make_project(slice_kwargs={"plan_path": "docs/plans/P6.S1.md", "planning_status": PlanningStatus.PROPOSED})
    assert commands.infer_step_for_id(p, "P6.S1") == {"step": "plan", "blocked": False}


def test_infer_step_slice_plan_ratified_ready():
    from tasktool.model import PlanningStatus
    p = _make_project(slice_kwargs={"plan_path": "docs/plans/P6.S1.md", "planning_status": PlanningStatus.RATIFIED})
    assert commands.infer_step_for_id(p, "P6.S1") == {"step": "implement", "blocked": False}


def test_infer_step_slice_done_wins_over_everything():
    from tasktool.model import Status
    p = _make_project(slice_kwargs={"status": Status.DONE})
    assert commands.infer_step_for_id(p, "P6.S1") == {"step": "done", "blocked": False}


def test_infer_step_slice_no_phase_spec_with_ratified_plan_is_implement():
    """Regression for F1 (post-slice review). A ratified slice plan with no
    phase.spec_path infers 'implement' — slice.plan_path is the authoritative
    signal for moving past spec at the slice level. See docs/specs/2026-05-23-P6
    §3.3 (R3 amendment)."""
    from tasktool.model import PlanningStatus
    p = _make_project(slice_kwargs={
        "plan_path": "docs/plans/P6.S1.md",
        "planning_status": PlanningStatus.RATIFIED,
    })
    assert commands.infer_step_for_id(p, "P6.S1") == {"step": "implement", "blocked": False}


def test_infer_step_slice_no_phase_spec_with_proposed_plan_is_plan():
    """Regression for F1: mirror test for the plan step."""
    from tasktool.model import PlanningStatus
    p = _make_project(slice_kwargs={
        "plan_path": "docs/plans/P6.S1.md",
        "planning_status": PlanningStatus.PROPOSED,
    })
    assert commands.infer_step_for_id(p, "P6.S1") == {"step": "plan", "blocked": False}


def test_infer_step_slice_blocked_overlay():
    from tasktool.model import Status, PlanningStatus, BlockedOn
    p = _make_project(slice_kwargs={
        "status": Status.BLOCKED,
        "plan_path": "docs/plans/P6.S1.md",
        "planning_status": PlanningStatus.RATIFIED,
        "blocked_on": BlockedOn(kind="external", value="waiting on x"),
    })
    assert commands.infer_step_for_id(p, "P6.S1") == {"step": "implement", "blocked": True}


def test_infer_step_done_overrides_blocked():
    from tasktool.model import Status
    p = _make_project(slice_kwargs={"status": Status.DONE})
    # Even if blocked were set somehow, done wins. (status=done can't coexist with blocked
    # in the validator, but the inference contract is explicit.)
    assert commands.infer_step_for_id(p, "P6.S1") == {"step": "done", "blocked": False}


def test_infer_step_cross_cutting_returns_na():
    from tasktool.model import Project, CrossCutting
    p = Project(project="t",
                cross_cutting=[CrossCutting(id="X1", title="t", created="2026-05-23")])
    assert commands.infer_step_for_id(p, "X1") == {"step": "n/a", "blocked": False}


def _phase_with(*statuses):
    from tasktool.model import Project, Phase, Slice, Status
    slices = [
        Slice(id=f"S{i+1}", title="t", created="2026-05-23",
              status=Status(s))
        for i, s in enumerate(statuses)
    ]
    ph = Phase(id="P6", title="t", created="2026-05-23",
               spec_path="docs/specs/P6.md", slices=slices)
    return Project(project="t", phases=[ph])


def test_phase_step_no_spec():
    from tasktool.model import Project, Phase
    p = Project(project="t", phases=[Phase(id="P6", title="t", created="2026-05-23")])
    assert commands.infer_step_for_id(p, "P6") == {"step": "spec", "blocked": False}


def test_phase_step_spec_but_no_slices():
    from tasktool.model import Project, Phase
    p = Project(project="t", phases=[
        Phase(id="P6", title="t", created="2026-05-23", spec_path="docs/specs/P6.md")
    ])
    assert commands.infer_step_for_id(p, "P6") == {"step": "spec", "blocked": False}


def test_phase_step_all_ready():
    p = _phase_with("ready", "ready")
    assert commands.infer_step_for_id(p, "P6") == {"step": "ready", "blocked": False}


def test_phase_step_one_in_progress():
    p = _phase_with("in_progress", "ready")
    assert commands.infer_step_for_id(p, "P6") == {"step": "in_progress", "blocked": False}


def test_phase_step_blocked_overlay():
    p = _phase_with("blocked", "ready")
    assert commands.infer_step_for_id(p, "P6") == {"step": "in_progress", "blocked": True}


def test_phase_step_done_plus_ready():
    p = _phase_with("done", "ready")
    assert commands.infer_step_for_id(p, "P6") == {"step": "in_progress", "blocked": False}


def test_phase_step_done_plus_blocked():
    p = _phase_with("done", "blocked")
    assert commands.infer_step_for_id(p, "P6") == {"step": "in_progress", "blocked": True}


def test_phase_step_all_done():
    p = _phase_with("done", "done")
    assert commands.infer_step_for_id(p, "P6") == {"step": "done", "blocked": False}


def test_list_filter_workflow_step(tmp_project_with_p6_s1):
    p = tmp_project_with_p6_s1
    commands.cmd_set(p, id="P6.S1", workflow_step="plan")
    text = commands.cmd_list(repo_root=p, workflow_step="plan", format="json")
    assert any(row["id"] == "P6.S1" for row in json.loads(text))
    text_no = commands.cmd_list(repo_root=p, workflow_step="implement", format="json")
    assert not any(row["id"] == "P6.S1" for row in json.loads(text_no))


class SurfaceCommandTests(unittest.TestCase):
    def _setup_phase_with_slice(self, t):
        commands.cmd_init(repo_root=t.root, project="demo")
        pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
        sid = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="slice")
        return pid, sid

    def test_surface_add_appends_unique_sorted(self):
        t = _Tmp()
        try:
            pid, sid = self._setup_phase_with_slice(t)
            commands.cmd_surface_add(
                repo_root=t.root, slice_id=f"{pid}.{sid}",
                surfaces=["cms-block-registry", "directus-schema", "cms-block-registry"],
            )
            p = load_project(t.root / "docs/tasklist.json")
            slc = p.phases[0].slices[0]
            self.assertEqual(slc.integration_surfaces, ["cms-block-registry", "directus-schema"])
        finally:
            t.cleanup()

    def test_surface_remove_drops_one(self):
        t = _Tmp()
        try:
            pid, sid = self._setup_phase_with_slice(t)
            commands.cmd_surface_add(
                repo_root=t.root, slice_id=f"{pid}.{sid}",
                surfaces=["cms-block-registry", "directus-schema"],
            )
            commands.cmd_surface_remove(
                repo_root=t.root, slice_id=f"{pid}.{sid}", surface="directus-schema",
            )
            p = load_project(t.root / "docs/tasklist.json")
            self.assertEqual(p.phases[0].slices[0].integration_surfaces, ["cms-block-registry"])
        finally:
            t.cleanup()

    def test_surface_add_refuses_cancelled_slice(self):
        t = _Tmp()
        try:
            pid, sid = self._setup_phase_with_slice(t)
            commands.cmd_cancel(repo_root=t.root, id=f"{pid}.{sid}", reason="dropped")
            with self.assertRaises(commands.CommandError):
                commands.cmd_surface_add(
                    repo_root=t.root, slice_id=f"{pid}.{sid}", surfaces=["x"],
                )
        finally:
            t.cleanup()

    def test_surface_list_renders_phase_slices(self):
        t = _Tmp()
        try:
            pid, sid = self._setup_phase_with_slice(t)
            commands.cmd_surface_add(
                repo_root=t.root, slice_id=f"{pid}.{sid}",
                surfaces=["cms-block-registry", "directus-schema"],
            )
            out = commands.cmd_surface_list(repo_root=t.root, phase_id=pid)
            self.assertIn(f"{pid}.{sid}", out)
            self.assertIn("cms-block-registry", out)
            self.assertIn("directus-schema", out)
        finally:
            t.cleanup()

    def test_surface_list_all_phases_when_omitted(self):
        t = _Tmp()
        try:
            pid, sid = self._setup_phase_with_slice(t)
            commands.cmd_surface_add(
                repo_root=t.root, slice_id=f"{pid}.{sid}", surfaces=["theme-tail-css"],
            )
            out = commands.cmd_surface_list(repo_root=t.root, phase_id=None)
            self.assertIn("theme-tail-css", out)
        finally:
            t.cleanup()


class CoordinateCommandTests(unittest.TestCase):
    def _setup(self, t):
        commands.cmd_init(repo_root=t.root, project="demo")
        pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
        sid = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="slice")
        return pid, sid

    def test_coordinate_sets_group(self):
        t = _Tmp()
        try:
            pid, sid = self._setup(t)
            commands.cmd_coordinate(repo_root=t.root, slice_id=f"{pid}.{sid}", group="cms")
            p = load_project(t.root / "docs/tasklist.json")
            self.assertEqual(p.phases[0].slices[0].coordination_group, "cms")
        finally:
            t.cleanup()

    def test_coordinate_clear_resets_to_none(self):
        t = _Tmp()
        try:
            pid, sid = self._setup(t)
            commands.cmd_coordinate(repo_root=t.root, slice_id=f"{pid}.{sid}", group="cms")
            commands.cmd_coordinate(repo_root=t.root, slice_id=f"{pid}.{sid}", clear=True)
            p = load_project(t.root / "docs/tasklist.json")
            self.assertIsNone(p.phases[0].slices[0].coordination_group)
        finally:
            t.cleanup()

    def test_coordinate_requires_group_or_clear(self):
        t = _Tmp()
        try:
            pid, sid = self._setup(t)
            with self.assertRaises(commands.CommandError):
                commands.cmd_coordinate(repo_root=t.root, slice_id=f"{pid}.{sid}")
        finally:
            t.cleanup()

    def test_coordinate_refuses_cancelled_slice(self):
        # A valid --group is passed so the flag-validation guard is satisfied and
        # the cancelled-slice guard inside `_require_slice` is the thing under test.
        t = _Tmp()
        try:
            pid, sid = self._setup(t)
            commands.cmd_cancel(repo_root=t.root, id=f"{pid}.{sid}", reason="dropped")
            with self.assertRaises(commands.CommandError):
                commands.cmd_coordinate(repo_root=t.root, slice_id=f"{pid}.{sid}", group="cms")
        finally:
            t.cleanup()


class ReserveCommandTests(unittest.TestCase):
    def _phase(self, t, n_slices=1):
        commands.cmd_init(repo_root=t.root, project="demo")
        pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
        sids = [
            commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title=f"slice{i}")
            for i in range(n_slices)
        ]
        return pid, sids

    def test_reserve_add_records_reservation(self):
        t = _Tmp()
        try:
            pid, (sid,) = self._phase(t, 1)
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{sid}",
                resource_value="homepage-sort:15", scope="phase", note="hero band",
            )
            p = load_project(t.root / "docs/tasklist.json")
            res = p.phases[0].slices[0].reservations
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0].resource, "homepage-sort")
            self.assertEqual(res[0].value, "15")
            self.assertEqual(res[0].scope, "phase")
            self.assertEqual(res[0].note, "hero band")
        finally:
            t.cleanup()

    def test_reserve_add_rejects_malformed_resource_value(self):
        t = _Tmp()
        try:
            pid, (sid,) = self._phase(t, 1)
            with self.assertRaises(commands.CommandError):
                commands.cmd_reserve_add(
                    repo_root=t.root, slice_id=f"{pid}.{sid}",
                    resource_value="no-colon-here", scope="phase",
                )
        finally:
            t.cleanup()

    def test_reserve_add_refuses_phase_scope_collision(self):
        t = _Tmp()
        try:
            pid, (s0, s1) = self._phase(t, 2)
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s0}",
                resource_value="homepage-sort:15", scope="phase",
            )
            with self.assertRaises(commands.CommandError) as cm:
                commands.cmd_reserve_add(
                    repo_root=t.root, slice_id=f"{pid}.{s1}",
                    resource_value="homepage-sort:15", scope="phase",
                )
            msg = str(cm.exception)
            self.assertIn("homepage-sort:15", msg)
            self.assertIn(f"{pid}.{s0}", msg)
        finally:
            t.cleanup()

    def test_reserve_add_collision_counts_done_holder(self):
        t = _Tmp()
        try:
            pid, (s0, s1) = self._phase(t, 2)
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s0}",
                resource_value="homepage-sort:15", scope="phase",
            )
            commands.cmd_start(repo_root=t.root, id=f"{pid}.{s0}")
            commands.cmd_close(repo_root=t.root, id=f"{pid}.{s0}", skip_review_gate=True)
            # s0 is now done; the slot stays taken.
            with self.assertRaises(commands.CommandError):
                commands.cmd_reserve_add(
                    repo_root=t.root, slice_id=f"{pid}.{s1}",
                    resource_value="homepage-sort:15", scope="phase",
                )
        finally:
            t.cleanup()

    def test_reserve_add_ignores_cancelled_holder(self):
        t = _Tmp()
        try:
            pid, (s0, s1) = self._phase(t, 2)
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s0}",
                resource_value="homepage-sort:15", scope="phase",
            )
            commands.cmd_cancel(repo_root=t.root, id=f"{pid}.{s0}", reason="dropped")
            # s0 cancelled → slot released → no refusal.
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s1}",
                resource_value="homepage-sort:15", scope="phase",
            )
            p = load_project(t.root / "docs/tasklist.json")
            s1_row = next(s for s in p.phases[0].slices if s.id == s1)
            self.assertEqual(len(s1_row.reservations), 1)
        finally:
            t.cleanup()

    def test_reserve_add_same_slice_no_self_collision(self):
        t = _Tmp()
        try:
            pid, (s0,) = self._phase(t, 1)
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s0}",
                resource_value="homepage-sort:15", scope="phase",
            )
            # Re-adding the SAME value to the SAME slice is idempotent, not a collision.
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s0}",
                resource_value="homepage-sort:15", scope="phase",
            )
            p = load_project(t.root / "docs/tasklist.json")
            self.assertEqual(len(p.phases[0].slices[0].reservations), 1)
        finally:
            t.cleanup()

    def test_reserve_add_same_slice_phase_and_project_both_held(self):
        # Self-dedupe must key on (resource, value, scope): a slice may hold the
        # same resource:value at BOTH phase and project scope. Only the
        # project-scoped one is laddered (Task 9), so a scope-blind self-dedupe
        # would silently drop the reservation that must reach the ledger.
        t = _Tmp()
        try:
            pid, (s0,) = self._phase(t, 1)
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s0}",
                resource_value="route-slug:/offers", scope="phase",
            )
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s0}",
                resource_value="route-slug:/offers", scope="project",
            )
            p = load_project(t.root / "docs/tasklist.json")
            res = p.phases[0].slices[0].reservations
            scopes = sorted(r.scope for r in res if r.resource == "route-slug" and r.value == "/offers")
            self.assertEqual(scopes, ["phase", "project"])
        finally:
            t.cleanup()

    def test_reserve_add_project_scope_collides_across_active_phases(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            p1 = commands.cmd_create_phase(repo_root=t.root, title="phase1")
            a = commands.cmd_create_slice(repo_root=t.root, phase_id=p1, title="a")
            p2 = commands.cmd_create_phase(repo_root=t.root, title="phase2")
            b = commands.cmd_create_slice(repo_root=t.root, phase_id=p2, title="b")
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{p1}.{a}",
                resource_value="directus-collection:home_slider", scope="project",
            )
            with self.assertRaises(commands.CommandError) as cm:
                commands.cmd_reserve_add(
                    repo_root=t.root, slice_id=f"{p2}.{b}",
                    resource_value="directus-collection:home_slider", scope="project",
                )
            self.assertIn(f"{p1}.{a}", str(cm.exception))
        finally:
            t.cleanup()

    def test_reserve_add_project_scope_collides_with_ledger(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
            sid = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="s")
            # Seed an archived holder into the ledger directly.
            from tasktool.model import LedgerReservation
            from tasktool.serialize import load_project, save_project
            proj = load_project(t.root / "docs/tasklist.json")
            proj.reservations_ledger.append(LedgerReservation(
                resource="route-slug", value="/offers", scope="project",
                note=None, owner_id="P3.S4", owner_phase_id="P3",
                archived_date="2026-05-01",
            ))
            save_project(proj, t.root / "docs/tasklist.json")
            with self.assertRaises(commands.CommandError) as cm:
                commands.cmd_reserve_add(
                    repo_root=t.root, slice_id=f"{pid}.{sid}",
                    resource_value="route-slug:/offers", scope="project",
                )
            msg = str(cm.exception)
            self.assertIn("route-slug:/offers", msg)
            self.assertIn("P3.S4", msg)
        finally:
            t.cleanup()

    def test_reserve_add_phase_scope_does_not_consult_ledger(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
            sid = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="s")
            from tasktool.model import LedgerReservation
            from tasktool.serialize import load_project, save_project
            proj = load_project(t.root / "docs/tasklist.json")
            proj.reservations_ledger.append(LedgerReservation(
                resource="route-slug", value="/offers", scope="project",
                note=None, owner_id="P3.S4", owner_phase_id="P3",
                archived_date="2026-05-01",
            ))
            save_project(proj, t.root / "docs/tasklist.json")
            # phase-scope add of the same value must NOT be blocked by the project ledger.
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{sid}",
                resource_value="route-slug:/offers", scope="phase",
            )
        finally:
            t.cleanup()

    def test_force_requires_reason(self):
        t = _Tmp()
        try:
            pid, (s0, s1) = self._phase(t, 2)
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s0}",
                resource_value="homepage-sort:15", scope="phase",
            )
            with self.assertRaises(commands.CommandError) as cm:
                commands.cmd_reserve_add(
                    repo_root=t.root, slice_id=f"{pid}.{s1}",
                    resource_value="homepage-sort:15", scope="phase",
                    force=True,  # no reason
                )
            self.assertIn("--reason", str(cm.exception))
        finally:
            t.cleanup()

    def test_force_with_reason_overrides_and_records_note(self):
        t = _Tmp()
        try:
            pid, (s0, s1) = self._phase(t, 2)
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s0}",
                resource_value="homepage-sort:15", scope="phase",
            )
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s1}",
                resource_value="homepage-sort:15", scope="phase",
                force=True, reason="intentional shared band",
            )
            p = load_project(t.root / "docs/tasklist.json")
            s0_row = next(s for s in p.phases[0].slices if s.id == s0)
            s1_row = next(s for s in p.phases[0].slices if s.id == s1)
            # Reserving slice gained the reservation + an override note.
            self.assertEqual(len(s1_row.reservations), 1)
            self.assertIn("Reservation-override", s1_row.notes)
            self.assertIn("homepage-sort:15", s1_row.notes)
            self.assertIn(f"{pid}.{s0}", s1_row.notes)
            self.assertIn("intentional shared band", s1_row.notes)
            # Holder slice is NOT mutated.
            self.assertEqual(len(s0_row.reservations), 1)
            self.assertEqual(s0_row.notes, "")
        finally:
            t.cleanup()

    def test_force_without_collision_still_requires_reason(self):
        t = _Tmp()
        try:
            pid, (s0,) = self._phase(t, 1)
            with self.assertRaises(commands.CommandError):
                commands.cmd_reserve_add(
                    repo_root=t.root, slice_id=f"{pid}.{s0}",
                    resource_value="homepage-sort:9", scope="phase",
                    force=True,  # force always requires reason
                )
        finally:
            t.cleanup()

    def test_reserve_remove_drops_matching(self):
        t = _Tmp()
        try:
            pid, (s0,) = self._phase(t, 1)
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s0}",
                resource_value="homepage-sort:15", scope="phase",
            )
            commands.cmd_reserve_remove(
                repo_root=t.root, slice_id=f"{pid}.{s0}",
                resource_value="homepage-sort:15",
            )
            p = load_project(t.root / "docs/tasklist.json")
            self.assertEqual(p.phases[0].slices[0].reservations, [])
        finally:
            t.cleanup()

    def test_reserve_remove_releases_slot_for_sibling(self):
        t = _Tmp()
        try:
            pid, (s0, s1) = self._phase(t, 2)
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s0}",
                resource_value="homepage-sort:15", scope="phase",
            )
            commands.cmd_reserve_remove(
                repo_root=t.root, slice_id=f"{pid}.{s0}",
                resource_value="homepage-sort:15",
            )
            # slot freed → sibling may now claim it
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s1}",
                resource_value="homepage-sort:15", scope="phase",
            )
        finally:
            t.cleanup()

    def test_reserve_list_renders(self):
        t = _Tmp()
        try:
            pid, (s0,) = self._phase(t, 1)
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s0}",
                resource_value="homepage-sort:15", scope="phase",
            )
            out = commands.cmd_reserve_list(repo_root=t.root, phase_id=pid)
            self.assertIn(f"{pid}.{s0}", out)
            self.assertIn("homepage-sort:15", out)
            self.assertIn("phase", out)
        finally:
            t.cleanup()

    def test_reserve_add_refuses_cancelled_slice(self):
        t = _Tmp()
        try:
            pid, (s0,) = self._phase(t, 1)
            commands.cmd_cancel(repo_root=t.root, id=f"{pid}.{s0}", reason="dropped")
            with self.assertRaises(commands.CommandError):
                commands.cmd_reserve_add(
                    repo_root=t.root, slice_id=f"{pid}.{s0}",
                    resource_value="homepage-sort:15", scope="phase",
                )
        finally:
            t.cleanup()

    def test_reserve_remove_refuses_cancelled_slice(self):
        t = _Tmp()
        try:
            pid, (s0,) = self._phase(t, 1)
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s0}",
                resource_value="homepage-sort:15", scope="phase",
            )
            commands.cmd_cancel(repo_root=t.root, id=f"{pid}.{s0}", reason="dropped")
            with self.assertRaises(commands.CommandError):
                commands.cmd_reserve_remove(
                    repo_root=t.root, slice_id=f"{pid}.{s0}",
                    resource_value="homepage-sort:15",
                )
        finally:
            t.cleanup()


class LedgerPopulationTests(unittest.TestCase):
    def _archive_ready(self, t, pid, sid, *, cancel=False):
        if cancel:
            commands.cmd_cancel(repo_root=t.root, id=f"{pid}.{sid}", reason="dropped")
        else:
            commands.cmd_start(repo_root=t.root, id=f"{pid}.{sid}")
            commands.cmd_close(repo_root=t.root, id=f"{pid}.{sid}", skip_review_gate=True)

    def test_archive_phase_ladders_project_reservations_from_done_slices(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
            sid = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="s")
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{sid}",
                resource_value="route-slug:/offers", scope="project",
            )
            # phase-scoped reservation must NOT be laddered
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{sid}",
                resource_value="homepage-sort:15", scope="phase",
            )
            self._archive_ready(t, pid, sid)
            commands.cmd_archive_phase(repo_root=t.root, phase_id=pid, skip_review_gate=True)
            p = load_project(t.root / "docs/tasklist.json")
            ledger = p.reservations_ledger
            self.assertEqual(len(ledger), 1)
            lr = ledger[0]
            self.assertEqual((lr.resource, lr.value, lr.scope), ("route-slug", "/offers", "project"))
            self.assertEqual(lr.owner_id, f"{pid}.{sid}")
            self.assertEqual(lr.owner_phase_id, pid)
            self.assertTrue(lr.archived_date)
        finally:
            t.cleanup()

    def test_archive_phase_excludes_cancelled_slice_reservations(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
            s_done = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="done")
            s_cx = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="cancelled")
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s_done}",
                resource_value="route-slug:/a", scope="project",
            )
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{s_cx}",
                resource_value="route-slug:/b", scope="project",
            )
            self._archive_ready(t, pid, s_cx, cancel=True)
            self._archive_ready(t, pid, s_done)
            commands.cmd_archive_phase(repo_root=t.root, phase_id=pid, skip_review_gate=True)
            p = load_project(t.root / "docs/tasklist.json")
            values = {(lr.resource, lr.value) for lr in p.reservations_ledger}
            self.assertEqual(values, {("route-slug", "/a")})
        finally:
            t.cleanup()

    def test_archive_phase_dedupes_on_resource_value_scope_owner(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
            a = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="a")
            b = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="b")
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{a}",
                resource_value="cache-tag:home", scope="project",
            )
            # b force-shares the same project value → two distinct owners
            commands.cmd_reserve_add(
                repo_root=t.root, slice_id=f"{pid}.{b}",
                resource_value="cache-tag:home", scope="project",
                force=True, reason="shared cache tag",
            )
            self._archive_ready(t, pid, a)
            self._archive_ready(t, pid, b)
            commands.cmd_archive_phase(repo_root=t.root, phase_id=pid, skip_review_gate=True)
            p = load_project(t.root / "docs/tasklist.json")
            owners = sorted(lr.owner_id for lr in p.reservations_ledger)
            self.assertEqual(owners, sorted([f"{pid}.{a}", f"{pid}.{b}"]))
            self.assertEqual(len(p.reservations_ledger), 2)
        finally:
            t.cleanup()

    def test_ledger_population_helper_is_idempotent_on_repeat(self):
        from tasktool.commands import _ladder_project_reservations
        from tasktool.model import Project, Phase, Slice, Reservation, Status
        proj = Project(project="demo")
        slc = Slice(id="S1", title="s", created="2026-06-02", status=Status.DONE)
        slc.reservations.append(Reservation(resource="route-slug", value="/x", scope="project", note=None))
        phase = Phase(id="P1", title="p", created="2026-06-02")
        phase.slices.append(slc)
        _ladder_project_reservations(proj, phase, archived_date="2026-06-02")
        _ladder_project_reservations(proj, phase, archived_date="2026-06-02")
        self.assertEqual(len(proj.reservations_ledger), 1)


class SurfaceOverlapSchedulingTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        # S1, S2, S3, S4 all created at top level (no deps) unless added below.
        for _ in range(4):
            commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="s")

    def tearDown(self):
        self.t.cleanup()

    def _row(self, rows, qid):
        return next(r for r in rows if r["id"] == qid)

    def test_schedule_warns_unguarded_surface_overlap(self):
        # S1 and S2 both write cms-block-registry, no dep, no coordination group.
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        rows = json.loads(commands.cmd_schedule(
            repo_root=self.t.root, phase_id="P1", format="json"))
        s1 = self._row(rows, "P1.S1")
        self.assertEqual(
            s1["surface_overlap"],
            [{"sibling": "P1.S2", "surfaces": ["cms-block-registry"]}],
        )
        self.assertEqual(s1["coordinated"], [])
        # Symmetric: S2 also reports S1.
        self.assertEqual(
            self._row(rows, "P1.S2")["surface_overlap"],
            [{"sibling": "P1.S1", "surfaces": ["cms-block-registry"]}],
        )

    def test_schedule_dep_link_suppresses_overlap(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        commands.cmd_deps(repo_root=self.t.root, slice_id="P1.S2", add="P1.S1")
        rows = json.loads(commands.cmd_schedule(
            repo_root=self.t.root, phase_id="P1", format="json"))
        self.assertEqual(self._row(rows, "P1.S1")["surface_overlap"], [])
        self.assertEqual(self._row(rows, "P1.S2")["surface_overlap"], [])

    def test_schedule_coordination_group_reports_coordinated_not_warned(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        commands.cmd_coordinate(repo_root=self.t.root, slice_id="P1.S1", group="cms")
        commands.cmd_coordinate(repo_root=self.t.root, slice_id="P1.S2", group="cms")
        rows = json.loads(commands.cmd_schedule(
            repo_root=self.t.root, phase_id="P1", format="json"))
        s1 = self._row(rows, "P1.S1")
        self.assertEqual(s1["surface_overlap"], [])
        self.assertEqual(
            s1["coordinated"],
            [{"sibling": "P1.S2", "surfaces": ["cms-block-registry"], "group": "cms"}],
        )

    def test_schedule_text_shows_overlap_line(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        out = commands.cmd_schedule(repo_root=self.t.root, phase_id="P1")
        self.assertIn("surface_overlap: P1.S2 (cms-block-registry)", out)

    def test_schedule_done_slice_not_a_candidate(self):
        # A done slice that shares a surface must not be reported as an overlap.
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        commands.cmd_start(repo_root=self.t.root, id="P1.S2")
        commands.cmd_close(repo_root=self.t.root, id="P1.S2", skip_review_gate=True)
        rows = json.loads(commands.cmd_schedule(
            repo_root=self.t.root, phase_id="P1", format="json"))
        self.assertEqual(self._row(rows, "P1.S1")["surface_overlap"], [])

    def test_schedule_waiting_slice_is_candidate_not_subject(self):
        # S2 waits on S4 (not done) => not ready-for-work => not a warning SUBJECT,
        # but it is still a CANDIDATE a ready sibling (S1) can collide with.
        commands.cmd_deps(repo_root=self.t.root, slice_id="P1.S2", add="P1.S4")
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        rows = json.loads(commands.cmd_schedule(
            repo_root=self.t.root, phase_id="P1", format="json"))
        # S1 (ready subject) reports the overlap with not-yet-ready S2.
        self.assertEqual(
            self._row(rows, "P1.S1")["surface_overlap"],
            [{"sibling": "P1.S2", "surfaces": ["cms-block-registry"]}],
        )
        # S2 is not ready-for-work, so it is not a subject: no relations on its row.
        self.assertEqual(self._row(rows, "P1.S2")["surface_overlap"], [])
        self.assertEqual(self._row(rows, "P1.S2")["coordinated"], [])

    def test_ready_slices_warns_unguarded_overlap(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        rows = json.loads(commands.cmd_ready_slices(
            repo_root=self.t.root, phase_id="P1", format="json"))
        s1 = self._row(rows, "P1.S1")
        self.assertEqual(
            s1["surface_overlap"],
            [{"sibling": "P1.S2", "surfaces": ["cms-block-registry"]}],
        )

    def test_ready_slices_text_shows_overlap_line(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        out = commands.cmd_ready_slices(repo_root=self.t.root, phase_id="P1")
        self.assertIn("P1.S1", out)
        self.assertIn("surface_overlap: P1.S2 (cms-block-registry)", out)

    def test_surface_check_json_shape(self):
        # S1 <-> S2 unguarded overlap; S3 <-> S4 coordinated.
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S3",
                                 surfaces=["directus-schema"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S4",
                                 surfaces=["directus-schema"])
        commands.cmd_coordinate(repo_root=self.t.root, slice_id="P1.S3", group="cms")
        commands.cmd_coordinate(repo_root=self.t.root, slice_id="P1.S4", group="cms")
        report = json.loads(commands.cmd_surface_check(
            repo_root=self.t.root, phase_id="P1", format="json"))
        self.assertEqual(report["phase"], "P1")
        self.assertEqual(
            report["unguarded_overlaps"],
            [{"slices": ["P1.S1", "P1.S2"], "surfaces": ["cms-block-registry"]}],
        )
        self.assertEqual(
            report["coordinated_surfaces"],
            [{"slices": ["P1.S3", "P1.S4"], "surfaces": ["directus-schema"],
              "group": "cms"}],
        )
        self.assertEqual(report["reservation_contention"], [])

    def test_surface_check_reports_forced_reservation_contention(self):
        # A --force override is the only way two non-cancelled slices hold the
        # same resource:value; surface check surfaces it for audit.
        commands.cmd_reserve_add(repo_root=self.t.root, slice_id="P1.S1",
                                 resource_value="homepage-sort:15", scope="phase")
        commands.cmd_reserve_add(repo_root=self.t.root, slice_id="P1.S2",
                                 resource_value="homepage-sort:15", scope="phase",
                                 force=True, reason="intentional shared slot")
        report = json.loads(commands.cmd_surface_check(
            repo_root=self.t.root, phase_id="P1", format="json"))
        self.assertEqual(
            report["reservation_contention"],
            [{"resource": "homepage-sort", "value": "15",
              "slices": ["P1.S1", "P1.S2"]}],
        )

    def test_surface_check_same_slice_dual_scope_is_not_contention(self):
        # One slice may hold the same resource:value at BOTH phase and project
        # scope. That is one holder, not contention — qid de-duplicated per
        # (resource, value), so reservation_contention stays empty.
        commands.cmd_reserve_add(repo_root=self.t.root, slice_id="P1.S1",
                                 resource_value="homepage-sort:15", scope="phase")
        commands.cmd_reserve_add(repo_root=self.t.root, slice_id="P1.S1",
                                 resource_value="homepage-sort:15", scope="project")
        report = json.loads(commands.cmd_surface_check(
            repo_root=self.t.root, phase_id="P1", format="json"))
        self.assertEqual(report["reservation_contention"], [])

    def test_surface_check_text_sections(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        out = commands.cmd_surface_check(repo_root=self.t.root, phase_id="P1")
        self.assertIn("Unguarded surface overlaps", out)
        self.assertIn("P1.S1, P1.S2: cms-block-registry", out)
        self.assertIn("(none)", out)  # coordinated + contention sections empty

    def test_surface_check_unknown_phase_raises(self):
        with self.assertRaises(commands.CommandError):
            commands.cmd_surface_check(repo_root=self.t.root, phase_id="P9")

    def test_ratify_parallel_group_warns_on_surface_overlap(self):
        # S1 already in group 'core' with a shared surface; ratifying S2 into the
        # same group with the same surface and no dep/coordination link warns.
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        commands.cmd_ratify(repo_root=self.t.root, slice_id="P1.S1",
                            parallel_group="core")
        warning = commands.cmd_ratify(repo_root=self.t.root, slice_id="P1.S2",
                                      parallel_group="core")
        self.assertIsNotNone(warning)
        self.assertIn("P1.S2", warning)
        self.assertIn("P1.S1", warning)
        self.assertIn("cms-block-registry", warning)
        self.assertIn("core", warning)
        # The mutation still applied despite the warning.
        p = load_project(self.t.root / "docs/tasklist.json")
        s2 = p.phases[0].slices[1]
        self.assertEqual(s2.parallel_group, "core")
        self.assertEqual(s2.planning_status.value, "ratified")

    def test_ratify_no_warning_when_dep_link_present(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        commands.cmd_deps(repo_root=self.t.root, slice_id="P1.S2", add="P1.S1")
        commands.cmd_ratify(repo_root=self.t.root, slice_id="P1.S1",
                            parallel_group="core")
        warning = commands.cmd_ratify(repo_root=self.t.root, slice_id="P1.S2",
                                      parallel_group="core")
        self.assertIsNone(warning)

    def test_ratify_no_warning_without_parallel_group(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        warning = commands.cmd_ratify(repo_root=self.t.root, slice_id="P1.S2")
        self.assertIsNone(warning)
