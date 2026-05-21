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
