from __future__ import annotations
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path
from tasktool.model import Project, Phase, Slice, Task, CrossCutting, Status
from tasktool.brief import brief

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = _REPO_ROOT / "tools"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(_PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "tasktool", *args],
        capture_output=True, text=True, cwd=_REPO_ROOT, env=env, check=True,
    )

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


def test_brief_includes_workflow_step_when_set(tmp_project_with_p6_s1):
    _run_cli("--project-root", str(tmp_project_with_p6_s1),
             "set", "P6.S1", "--workflow-step", "implement")
    out = _run_cli("--project-root", str(tmp_project_with_p6_s1),
                   "brief", "P6.S1").stdout
    assert "implement" in out


def test_brief_omits_review_block_when_inactive(tmp_project_with_p6_s1):
    out = _run_cli("--project-root", str(tmp_project_with_p6_s1),
                   "brief", "P6.S1").stdout
    assert "review_active" not in out


def _cancelled_slice_project(notes: str) -> Project:
    p = Project(project="demo", last_reviewed="2026-05-23")
    ph = Phase(id="P1", title="Phase 1", created="2026-05-17",
               status=Status.IN_PROGRESS)
    s = Slice(id="S1", title="Cancelled slice", created="2026-05-17",
              status=Status.CANCELLED, closed="2026-05-24", notes=notes)
    ph.slices.append(s)
    p.phases.append(ph)
    return p


class TestBriefCancelledReason(unittest.TestCase):
    def test_brief_surfaces_cancellation_reason_at_top(self):
        notes = "Cancelled 2026-05-24T10:00:00: scope dropped"
        out = brief(_cancelled_slice_project(notes), "P1.S1")
        reason_pos = out.find("scope dropped")
        first_section = re.search(r"^##? ", out, flags=re.M)
        self.assertNotEqual(reason_pos, -1)
        if first_section:
            self.assertLess(reason_pos, first_section.start())

    def test_brief_falls_back_to_last_notes_line_when_no_prefix(self):
        # Notes that lack a `Cancelled <ts>: ` prefix line — fall back
        # to the last non-empty line.
        notes = "some earlier note\nlegacy last line"
        out = brief(_cancelled_slice_project(notes), "P1.S1")
        self.assertIn("legacy last line", out)
        # And it leads — before the first section header.
        reason_pos = out.find("legacy last line")
        first_section = re.search(r"^##? ", out, flags=re.M)
        self.assertNotEqual(reason_pos, -1)
        if first_section:
            self.assertLess(reason_pos, first_section.start())

    def test_brief_no_reason_block_on_non_cancelled_rows(self):
        # A normal (non-cancelled) slice should not gain a "Cancelled " block.
        out = brief(_sample(), "P2.S2")
        self.assertNotIn("Cancelled ", out)


if __name__ == "__main__":
    unittest.main()
