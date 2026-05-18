from __future__ import annotations
import unittest
from tasktool.importer import parse_tasklist_md
from tasktool.model import Status

PHASE_HEADER = """\
# Project Task List

## P2 — tasktool: JSON-backed task management CLI 🚧 `IN PROGRESS`

Spec: [`docs/specs/2026-05-17-P2-tasktool-design.md`](specs/2026-05-17-P2-tasktool-design.md). Plan: _pending_.
"""

PHASE_HEADER_DONE = """\
## P1 — Old phase ✅ `DONE 2026-05-17`

Closed; see archive.
"""

class TestImporterPhase(unittest.TestCase):
    def test_phase_header_basic(self):
        r = parse_tasklist_md(PHASE_HEADER)
        self.assertEqual(len(r.project.phases), 1)
        ph = r.project.phases[0]
        self.assertEqual(ph.id, "P2")
        self.assertEqual(ph.title, "tasktool: JSON-backed task management CLI")
        self.assertEqual(ph.status, Status.IN_PROGRESS)
        self.assertEqual(ph.spec_path, "docs/specs/2026-05-17-P2-tasktool-design.md")
        self.assertIsNone(ph.plan_path)

    def test_phase_blocked_emoji_coerces_to_ready_with_warning(self):
        text = "## P3 — Blocked phase ⏸\n"
        r = parse_tasklist_md(text)
        self.assertEqual(len(r.project.phases), 1)
        ph = r.project.phases[0]
        self.assertEqual(ph.id, "P3")
        self.assertEqual(ph.status, Status.READY)
        self.assertTrue(
            any("blocked status not allowed on phase" in w for w in r.warnings),
            f"expected warning substring, got {r.warnings!r}",
        )

    def test_phase_done_tag_sets_closed(self):
        r = parse_tasklist_md(PHASE_HEADER_DONE)
        self.assertEqual(len(r.project.phases), 1)
        ph = r.project.phases[0]
        self.assertEqual(ph.id, "P1")
        self.assertEqual(ph.status, Status.DONE)
        self.assertEqual(ph.closed, "2026-05-17")


SLICES_BLOCK = """\
## P2 — Demo 🚧 `IN PROGRESS`

- ✅ **S1** `DONE 2026-05-18` — CLI core: data model. Plan: [`docs/plans/2026-05-17-p2-s1.md`](plans/2026-05-17-p2-s1.md). Post-impl: 139 tests.
- ☐ **S2** Importer, render, brief. Plan: _pending._
- ⏸ **S3a** `BLOCKED on P2.S3` — follow-up cleanup.
"""

class TestImporterSlices(unittest.TestCase):
    def test_slice_parsing(self):
        r = parse_tasklist_md(SLICES_BLOCK)
        self.assertEqual(len(r.project.phases), 1)
        slices = r.project.phases[0].slices
        self.assertEqual([s.id for s in slices], ["S1", "S2", "S3a"])
        self.assertEqual(slices[0].status, Status.DONE)
        self.assertEqual(slices[0].closed, "2026-05-18")
        self.assertEqual(slices[0].plan_path, "docs/plans/2026-05-17-p2-s1.md")
        self.assertEqual(slices[1].status, Status.READY)
        self.assertIsNone(slices[1].plan_path)
        self.assertEqual(slices[2].status, Status.BLOCKED)
        self.assertIsNotNone(slices[2].blocked_on)
        self.assertEqual(slices[2].blocked_on.kind, "id")
        self.assertEqual(slices[2].blocked_on.value, "P2.S3")

    def test_slice_external_blocked(self):
        text = (
            "## P2 — Demo 🚧 `IN PROGRESS`\n\n"
            "- ⏸ **S4** `BLOCKED on external:foo/bar#42` — wait\n"
        )
        r = parse_tasklist_md(text)
        slices = r.project.phases[0].slices
        self.assertEqual(len(slices), 1)
        self.assertEqual(slices[0].status, Status.BLOCKED)
        self.assertIsNotNone(slices[0].blocked_on)
        self.assertEqual(slices[0].blocked_on.kind, "external")
        self.assertEqual(slices[0].blocked_on.value, "foo/bar#42")

    def test_slice_unrecognised_tag_warns(self):
        text = (
            "## P2 — Demo 🚧 `IN PROGRESS`\n\n"
            "- ☐ **S5** `WAT lol` — odd tag\n"
        )
        r = parse_tasklist_md(text)
        slices = r.project.phases[0].slices
        self.assertEqual(len(slices), 1)
        self.assertEqual(slices[0].id, "S5")
        self.assertEqual(slices[0].status, Status.READY)
        self.assertIsNone(slices[0].closed)
        self.assertIsNone(slices[0].blocked_on)
        self.assertTrue(
            any("unrecognised tag on slice S5" in w and "`WAT lol`" in w for w in r.warnings),
            f"expected unrecognised-tag warning, got {r.warnings!r}",
        )


CROSS_AND_NOISE = """\
## Cross-cutting (`X*`) — opportunistic, unscheduled

- ☐ **X1** — gather telemetry for skill firing rate.
- ⏸ **X2** — bogus blocked cross item.
- malformed bullet

## P1 — Old work (historical) ✅ `DONE 2025-12-01`

Closed; see `docs/archived-tasks/P1-old.md`.
"""


class TestImporterMisc(unittest.TestCase):
    def test_cross_and_warnings(self):
        r = parse_tasklist_md(CROSS_AND_NOISE)
        # Both cross items captured; X2's blocked status coerced to ready.
        self.assertEqual([c.id for c in r.project.cross_cutting], ["X1", "X2"])
        self.assertEqual(r.project.cross_cutting[0].status, Status.READY)
        self.assertEqual(r.project.cross_cutting[1].status, Status.READY)
        # P1 stays in phases[] (historical imports never become ArchivedPhase).
        self.assertTrue(any(ph.id == "P1" for ph in r.project.phases))
        self.assertFalse(r.project.archived_phases)
        # X2's invalid status surfaces as a warning.
        self.assertTrue(any("blocked status not allowed on cross" in w for w in r.warnings))
        # The malformed bullet surfaces as a warning.
        self.assertTrue(any("malformed bullet" in w for w in r.warnings))


if __name__ == "__main__":
    unittest.main()
