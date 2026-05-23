from __future__ import annotations
import unittest
from tasktool.model import (
    ArchivedCrossCutting,
    Project,
    Phase,
    Slice,
    CrossCutting,
    Status,
    BlockedOn,
)
from tasktool.render import render_project, STATUS_EMOJI

class TestRender(unittest.TestCase):
    def test_basic_render(self):
        p = Project(project="demo", north_star="Make it good.", last_reviewed="2026-05-18")
        p.phases.append(Phase(
            id="P2", title="Demo phase", created="2026-05-17",
            started="2026-05-18", status=Status.IN_PROGRESS, spec_path="docs/specs/x.md",
        ))
        p.phases[0].slices.append(Slice(
            id="S1", title="First slice", created="2026-05-17",
            started="2026-05-17", status=Status.DONE, closed="2026-05-18",
            plan_path="docs/plans/y.md",
        ))
        p.phases[0].slices.append(Slice(
            id="S2", title="Second slice", created="2026-05-17",
            status=Status.BLOCKED, blocked_on=BlockedOn(kind="id", value="P2.S1"),
        ))
        p.cross_cutting.append(CrossCutting(
            id="X1", title="cross item", created="2026-05-17", started="2026-05-18",
        ))
        out = render_project(p)
        self.assertIn("# demo", out)
        self.assertIn("Make it good.", out)
        self.assertIn("## P2 — Demo phase 🚧 `IN PROGRESS`", out)
        self.assertIn("Started: 2026-05-18.", out)
        self.assertIn("- ✅ **S1** `DONE 2026-05-18` — First slice", out)
        self.assertIn("Started: 2026-05-17.", out)
        self.assertIn("- ⏸ **S2** `BLOCKED on P2.S1` — Second slice", out)
        self.assertIn("- ☐ **X1** — cross item. Started: 2026-05-18.", out)
        self.assertNotIn("Started: None", out)

    def test_blocked_status_on_phase_renders_as_ready_defensively(self):
        p = Project(project="demo")
        # Bypass validator: set status directly to BLOCKED on a phase.
        ph = Phase(id="P1", title="Bogus blocked phase", created="2026-05-17",
                   status=Status.BLOCKED)
        p.phases.append(ph)
        out = render_project(p)
        self.assertIn("☐", out)        # coerced to READY emoji
        self.assertNotIn("⏸", out)     # blocked emoji must NOT appear
        self.assertNotIn("`BLOCKED", out)  # no blocked tag

    def test_blocked_status_on_cross_renders_as_ready_defensively(self):
        p = Project(project="demo")
        p.cross_cutting.append(CrossCutting(id="X1", title="bogus blocked cross",
                                             created="2026-05-17",
                                             status=Status.BLOCKED))
        out = render_project(p)
        self.assertIn("☐", out)
        self.assertNotIn("⏸", out)

    def test_render_shows_archived_cross_section(self):
        p = Project(project="demo")
        p.cross_cutting.append(
            CrossCutting(id="X1", title="active cross", created="2026-05-21")
        )
        p.archived_cross_cutting.append(
            ArchivedCrossCutting(
                id="X2",
                title="archived cross",
                archived_path="docs/archived-tasks/X2-archived-cross.md",
                archived_date="2026-05-21",
            )
        )

        out = render_project(p)

        self.assertIn("## Cross-cutting (`X*`)", out)
        self.assertIn("## Archived cross-cutting (`X*`)", out)
        active_section, archived_section = out.split("## Archived cross-cutting (`X*`)", 1)
        self.assertIn("**X1**", active_section)
        self.assertNotIn("**X2**", active_section)
        self.assertIn("**X2**", archived_section)
        self.assertIn("docs/archived-tasks/X2-archived-cross.md", archived_section)


class TestCancelledRendering(unittest.TestCase):
    def test_cancelled_emoji_present(self):
        self.assertEqual(STATUS_EMOJI[Status.CANCELLED], "🚫")

    def test_cancelled_slice_renders_with_closed_date(self):
        p = Project(project="demo")
        ph = Phase(id="P1", title="p", created="2026-05-23")
        ph.slices.append(Slice(
            id="S1", title="dropped", created="2026-05-23",
            status=Status.CANCELLED, closed="2026-05-23",
        ))
        p.phases.append(ph)
        out = render_project(p)
        self.assertIn("🚫", out)
        self.assertIn("2026-05-23", out)

    def test_cancelled_phase_renders_with_closed_date(self):
        p = Project(project="demo")
        p.phases.append(Phase(
            id="P1", title="dropped phase", created="2026-05-23",
            status=Status.CANCELLED, closed="2026-05-23",
        ))
        out = render_project(p)
        self.assertIn("🚫", out)
        self.assertIn("2026-05-23", out)


if __name__ == "__main__":
    unittest.main()
