from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from tasktool.model import (
    Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status, PlanningStatus,
)
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
        ph = Phase(
            id="P1", title="phase", created="2026-05-17",
            status=Status.IN_PROGRESS,
            planning_path="docs/specs/2026-05-17-p1-phase-plan.md",
        )
        s = Slice(
            id="S1", title="slice", created="2026-05-17", status=Status.BLOCKED,
            blocked_on=BlockedOn(kind="id", value="P1.S2"),
            depends_on=["P1.S2"],
            planning_status=PlanningStatus.RATIFIED,
            parallel_group="bootstrap",
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

def test_started_field_round_trips_on_slice():
    text = """{
      "project": "demo",
      "schema_version": 1,
      "phases": [{
        "id": "P1",
        "title": "Phase",
        "created": "2026-05-19",
        "slices": [{
          "id": "S1",
          "title": "Slice",
          "created": "2026-05-19",
          "started": "2026-05-19"
        }]
      }]
    }"""
    p = loads_project(text)
    assert p.phases[0].slices[0].started == "2026-05-19"
    assert '"started": "2026-05-19"' in dumps_canonical(p)


def test_legacy_tasklist_without_archived_cross_cutting_loads():
    project = loads_project(
        json.dumps(
            {
                "project": "demo",
                "schema_version": 1,
                "phases": [],
                "cross_cutting": [],
                "archived_phases": [],
            }
        )
    )

    assert project.archived_cross_cutting == []


def test_slice_worktree_fields_round_trip():
    from tasktool.serialize import from_dict, to_dict
    raw = {
        "project": "demo",
        "schema_version": 1,
        "phases": [{
            "id": "P1", "title": "P", "created": "2026-05-21", "status": "ready",
            "slices": [{
                "id": "S1", "title": "S", "created": "2026-05-21", "status": "ready",
                "worktree_path": ".worktrees/worktree-p1-s1-s",
                "worktree_branch": "worktree-p1-s1-s",
                "worktree_in_place": False,
                "worktree_pruned_at": None,
                "worktree_prune_pending": False,
                "worktree_prune_pending_at": None,
            }],
        }],
        "cross_cutting": [],
        "archived_phases": [],
        "archived_cross_cutting": [],
    }
    p = from_dict(raw)
    out = to_dict(p)
    s = out["phases"][0]["slices"][0]
    assert s["worktree_path"] == ".worktrees/worktree-p1-s1-s"
    assert s["worktree_branch"] == "worktree-p1-s1-s"
    assert s["worktree_in_place"] is False


def test_slice_worktree_fields_default_null_when_absent():
    from tasktool.serialize import from_dict, to_dict
    raw = {
        "project": "demo", "schema_version": 1,
        "phases": [{
            "id": "P1", "title": "P", "created": "2026-05-21", "status": "ready",
            "slices": [{"id": "S1", "title": "S", "created": "2026-05-21", "status": "ready"}],
        }],
        "cross_cutting": [], "archived_phases": [], "archived_cross_cutting": [],
    }
    p = from_dict(raw)
    s = p.phases[0].slices[0]
    assert s.worktree_path is None
    assert s.worktree_branch is None
    assert s.worktree_in_place is False
    assert s.worktree_pruned_at is None
    assert s.worktree_prune_pending is False
    assert s.worktree_prune_pending_at is None


def test_cross_worktree_fields_round_trip():
    from tasktool.serialize import from_dict, to_dict
    raw = {
        "project": "demo", "schema_version": 1,
        "phases": [],
        "cross_cutting": [{
            "id": "X9", "title": "x", "created": "2026-05-21", "status": "ready",
            "worktree_path": ".worktrees/worktree-x9-x",
            "worktree_branch": "worktree-x9-x",
            "worktree_in_place": False,
            "worktree_pruned_at": None,
            "worktree_prune_pending": False,
            "worktree_prune_pending_at": None,
        }],
        "archived_phases": [], "archived_cross_cutting": [],
    }
    p = from_dict(raw)
    out = to_dict(p)
    assert out["cross_cutting"][0]["worktree_path"] == ".worktrees/worktree-x9-x"
