from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from tasktool.model import Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status
from tasktool.serialize import (
    load_project, save_project, dumps_canonical, loads_project, to_dict, from_dict,
)

class RoundTripTests(unittest.TestCase):
    def test_empty_project_roundtrip(self):
        p = Project(project="demo")
        d = to_dict(p)
        back = from_dict(d)
        self.assertEqual(back, p)

    def test_full_project_roundtrip(self):
        p = Project(project="demo", north_star="x", last_reviewed="2026-05-17")
        ph = Phase(id="P1", title="phase", created="2026-05-17", status=Status.IN_PROGRESS)
        s = Slice(
            id="S1", title="slice", created="2026-05-17", status=Status.BLOCKED,
            blocked_on=BlockedOn(kind="id", value="P1.S2"),
            refs=["a.md", "b.md"],
        )
        s.tasks.append(Task(id="T1", title="task", created="2026-05-17"))
        ph.slices.append(s)
        p.phases.append(ph)
        p.cross_cutting.append(CrossCutting(id="X1", title="x", created="2026-05-17"))

        back = from_dict(to_dict(p))
        self.assertEqual(back, p)

class CanonicalFormatTests(unittest.TestCase):
    def test_dumps_sorted_keys(self):
        p = Project(project="demo")
        out = dumps_canonical(p)
        parsed = json.loads(out)
        self.assertEqual(parsed["project"], "demo")
        keys = list(parsed.keys())
        self.assertEqual(keys, sorted(keys))

    def test_dumps_trailing_newline(self):
        out = dumps_canonical(Project(project="demo"))
        self.assertTrue(out.endswith("\n"))

    def test_dumps_indent_two(self):
        out = dumps_canonical(Project(project="demo"))
        self.assertIn("\n  ", out)

class DiskIOTests(unittest.TestCase):
    def test_save_then_load(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tasklist.json"
            p = Project(project="demo")
            save_project(p, path)
            loaded = load_project(path)
            self.assertEqual(loaded, p)

    def test_save_is_canonical_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tasklist.json"
            p = Project(project="demo")
            save_project(p, path)
            on_disk = path.read_text(encoding="utf-8")
            self.assertEqual(on_disk, dumps_canonical(p))
