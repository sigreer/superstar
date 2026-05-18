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

    def test_phase_done_tag_sets_closed(self):
        r = parse_tasklist_md(PHASE_HEADER_DONE)
        self.assertEqual(len(r.project.phases), 1)
        ph = r.project.phases[0]
        self.assertEqual(ph.id, "P1")
        self.assertEqual(ph.status, Status.DONE)
        self.assertEqual(ph.closed, "2026-05-17")


if __name__ == "__main__":
    unittest.main()
