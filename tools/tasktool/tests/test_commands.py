# tools/tasktool/tests/test_commands.py
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from tasktool import commands
from tasktool.serialize import load_project
from tasktool.model import Status

class _Tmp:
    def __init__(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        (self.root / "docs").mkdir()
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
        new_id = commands.cmd_create_phase(repo_root=self.t.root, title="Tasktool")
        self.assertEqual(new_id, "P1")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(len(p.phases), 1)
        self.assertEqual(p.phases[0].title, "Tasktool")

    def test_create_slice(self):
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        new_id = commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="CLI core")
        self.assertEqual(new_id, "S1")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].title, "CLI core")

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

    def test_set_task_done_auto_stamps_closed(self):
        commands.cmd_set(repo_root=self.t.root, id="P1.S1.T1", status="done")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertIsNotNone(p.phases[0].slices[0].tasks[0].closed)

    def test_set_slice_done_requires_review_gate(self):
        with self.assertRaises(commands.CommandError):
            commands.cmd_set(repo_root=self.t.root, id="P1.S1", status="done")

    def test_set_slice_done_passes_with_chain(self):
        _write_passing_chain(self.t.root, "p1-s1-post-slice", "ready")
        commands.cmd_set(repo_root=self.t.root, id="P1.S1", status="done")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].status, Status.DONE)
        self.assertIsNotNone(p.phases[0].slices[0].reviewer_chain)

    def test_set_slice_done_skip_gate(self):
        commands.cmd_set(
            repo_root=self.t.root, id="P1.S1", status="done", skip_review_gate=True,
        )
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].status, Status.DONE)
        self.assertIn("review gate skipped", p.phases[0].slices[0].notes)

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
        commands.cmd_close(
            repo_root=self.t.root, id="P1.S1",
            refs=["docs/a.md", "docs/b.md"], note="post-impl",
        )
        p = load_project(self.t.root / "docs/tasklist.json")
        s = p.phases[0].slices[0]
        self.assertEqual(s.status, Status.DONE)
        self.assertEqual(s.refs, ["docs/a.md", "docs/b.md"])
        self.assertIn("post-impl", s.notes)

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
        commands.cmd_block(repo_root=self.t.root, slice_id="P1.S1", on="P1.S2")
        p = load_project(self.t.root / "docs/tasklist.json")
        s = p.phases[0].slices[0]
        self.assertEqual(s.status, Status.BLOCKED)
        self.assertEqual(s.blocked_on.kind, "id")
        self.assertEqual(s.blocked_on.value, "P1.S2")

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
        commands.cmd_unblock(repo_root=self.t.root, slice_id="P1.S1")
        p = load_project(self.t.root / "docs/tasklist.json")
        s = p.phases[0].slices[0]
        self.assertEqual(s.status, Status.READY)
        self.assertIsNone(s.blocked_on)

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
