from __future__ import annotations
import unittest
from tasktool.model import Project, Phase, Slice, Task, Status
from tasktool.brief import brief

def _sample() -> Project:
    p = Project(project="demo", last_reviewed="2026-05-18")
    ph = Phase(id="P2", title="Phase 2", created="2026-05-17", status=Status.IN_PROGRESS)
    p.phases.append(ph)
    s1 = Slice(id="S1", title="Done slice", created="2026-05-17", status=Status.DONE, closed="2026-05-18")
    s2 = Slice(id="S2", title="Active slice", created="2026-05-17", status=Status.IN_PROGRESS,
               started="2026-05-18", plan_path="docs/plans/x.md")
    s2.tasks.append(Task(id="T1", title="open task", created="2026-05-17"))
    s2.tasks.append(Task(id="T2", title="done task", created="2026-05-17",
                         status=Status.DONE, closed="2026-05-18"))
    ph.slices += [s1, s2]
    return p

class TestBrief(unittest.TestCase):
    def test_slice_brief(self):
        out = brief(_sample(), "P2.S2")
        self.assertIn("# P2.S2 — Active slice", out)
        self.assertIn("status: in_progress", out)
        self.assertIn("started: 2026-05-18", out)
        self.assertIn("plan: docs/plans/x.md", out)
        self.assertIn("Parent phase: P2 — Phase 2 [in_progress]", out)
        self.assertIn("Sibling slices:", out)
        self.assertIn("S1  [done]", out)
        self.assertIn("Open tasks:", out)
        self.assertIn("T1  [ready]  open task", out)
        self.assertNotIn("T2", out)  # done tasks excluded

    def test_phase_brief(self):
        out = brief(_sample(), "P2")
        self.assertIn("# P2 — Phase 2", out)
        self.assertIn("Slices:", out)
        self.assertIn("S1  [done]", out)
        self.assertIn("S2  [in_progress] started=2026-05-18", out)


if __name__ == "__main__":
    unittest.main()
