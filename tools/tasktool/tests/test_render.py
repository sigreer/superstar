from __future__ import annotations
import unittest
from tasktool.model import Project, Phase, Slice, CrossCutting, Status, BlockedOn
from tasktool.render import render_project

class TestRender(unittest.TestCase):
    def test_basic_render(self):
        p = Project(project="demo", north_star="Make it good.", last_reviewed="2026-05-18")
        p.phases.append(Phase(
            id="P2", title="Demo phase", created="2026-05-17",
            status=Status.IN_PROGRESS, spec_path="docs/specs/x.md",
        ))
        p.phases[0].slices.append(Slice(
            id="S1", title="First slice", created="2026-05-17",
            status=Status.DONE, closed="2026-05-18",
            plan_path="docs/plans/y.md",
        ))
        p.phases[0].slices.append(Slice(
            id="S2", title="Second slice", created="2026-05-17",
            status=Status.BLOCKED, blocked_on=BlockedOn(kind="id", value="P2.S1"),
        ))
        p.cross_cutting.append(CrossCutting(id="X1", title="cross item", created="2026-05-17"))
        out = render_project(p)
        self.assertIn("# demo", out)
        self.assertIn("Make it good.", out)
        self.assertIn("## P2 — Demo phase 🚧 `IN PROGRESS`", out)
        self.assertIn("- ✅ **S1** `DONE 2026-05-18` — First slice", out)
        self.assertIn("- ⏸ **S2** `BLOCKED on P2.S1` — Second slice", out)
        self.assertIn("- ☐ **X1**", out)


if __name__ == "__main__":
    unittest.main()
