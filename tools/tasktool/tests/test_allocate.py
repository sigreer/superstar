# tools/tasktool/tests/test_allocate.py
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from tasktool.model import Project, Phase, Slice, CrossCutting
from tasktool.allocate import (
    next_phase_id, next_slice_id, next_task_id, next_cross_id, scan_orphan_ids,
)

def _mkfile(root: Path, rel: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("", encoding="utf-8")

class PhaseAllocTests(unittest.TestCase):
    def test_empty_project(self):
        p = Project(project="demo")
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(next_phase_id(p, Path(td)), "P1")

    def test_existing_phases(self):
        p = Project(project="demo")
        p.phases.append(Phase(id="P1", title="a", created="2026-05-17"))
        p.phases.append(Phase(id="P3", title="b", created="2026-05-17"))
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(next_phase_id(p, Path(td)), "P4")

    def test_orphan_in_specs(self):
        p = Project(project="demo")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _mkfile(root, "docs/specs/2026-05-17-P7-orphan-spec.md")
            self.assertEqual(next_phase_id(p, root), "P8")

    def test_orphan_lowercase_in_plans(self):
        """Regression: lowercase artifact names (e.g. p7) must be detected."""
        p = Project(project="demo")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _mkfile(root, "docs/plans/2026-05-17-p7-orphan-spec.md")
            self.assertEqual(next_phase_id(p, root), "P8")

    def test_orphan_in_reviewer(self):
        p = Project(project="demo")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "docs/reviewer/something-P5-post-slice").mkdir(parents=True)
            self.assertEqual(next_phase_id(p, root), "P6")

class SliceAllocTests(unittest.TestCase):
    def test_first_slice(self):
        p = Project(project="demo")
        p.phases.append(Phase(id="P1", title="a", created="2026-05-17"))
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(next_slice_id(p, "P1", Path(td)), "S1")

    def test_next_slice(self):
        p = Project(project="demo")
        ph = Phase(id="P1", title="a", created="2026-05-17")
        ph.slices.append(Slice(id="S1", title="a", created="2026-05-17"))
        ph.slices.append(Slice(id="S2a", title="a", created="2026-05-17"))
        p.phases.append(ph)
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(next_slice_id(p, "P1", Path(td)), "S3")

    def test_followup_letter(self):
        p = Project(project="demo")
        ph = Phase(id="P1", title="a", created="2026-05-17")
        ph.slices.append(Slice(id="S1", title="a", created="2026-05-17"))
        ph.slices.append(Slice(id="S1a", title="a", created="2026-05-17"))
        p.phases.append(ph)
        with tempfile.TemporaryDirectory() as td:
            from tasktool.allocate import next_followup_letter
            self.assertEqual(next_followup_letter(p, "P1", "S1", Path(td)), "S1b")

class TaskAllocTests(unittest.TestCase):
    def test_first_task(self):
        p = Project(project="demo")
        ph = Phase(id="P1", title="a", created="2026-05-17")
        ph.slices.append(Slice(id="S1", title="a", created="2026-05-17"))
        p.phases.append(ph)
        self.assertEqual(next_task_id(p, "P1", "S1"), "T1")

class CrossAllocTests(unittest.TestCase):
    def test_first_cross(self):
        p = Project(project="demo")
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(next_cross_id(p, Path(td)), "X1")
