# tools/tasktool/tests/test_validate.py
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from tasktool.model import Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status
from tasktool.serialize import save_project, dumps_canonical
from tasktool.validate import (
    validate_project, ValidationError, strict_format_check, normalise_file,
)

def _project_with_slice(**slice_kwargs) -> Project:
    p = Project(project="demo")
    ph = Phase(id="P1", title="phase", created="2026-05-17")
    s = Slice(id="S1", title="slice", created="2026-05-17", **slice_kwargs)
    ph.slices.append(s)
    p.phases.append(ph)
    return p

class IdFormatTests(unittest.TestCase):
    def test_valid(self):
        p = _project_with_slice()
        validate_project(p)  # no raise

    def test_bad_phase_id(self):
        p = _project_with_slice()
        p.phases[0].id = "Phase1"
        with self.assertRaises(ValidationError):
            validate_project(p)

class UniquenessTests(unittest.TestCase):
    def test_duplicate_phase_ids(self):
        p = Project(project="demo")
        p.phases.append(Phase(id="P1", title="a", created="2026-05-17"))
        p.phases.append(Phase(id="P1", title="b", created="2026-05-17"))
        with self.assertRaises(ValidationError) as ctx:
            validate_project(p)
        self.assertIn("duplicate", str(ctx.exception).lower())

    def test_duplicate_slice_ids_within_phase(self):
        p = _project_with_slice()
        p.phases[0].slices.append(Slice(id="S1", title="dup", created="2026-05-17"))
        with self.assertRaises(ValidationError):
            validate_project(p)

class StatusTransitionTests(unittest.TestCase):
    def test_done_requires_closed(self):
        p = _project_with_slice(status=Status.DONE, closed=None)
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_done_with_closed_ok(self):
        p = _project_with_slice(status=Status.DONE, closed="2026-05-17")
        validate_project(p)

    def test_blocked_on_phase_rejected(self):
        p = _project_with_slice()
        p.phases[0].status = Status.BLOCKED
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_blocked_on_task_rejected(self):
        p = _project_with_slice()
        p.phases[0].slices[0].tasks.append(
            Task(id="T1", title="t", created="2026-05-17", status=Status.BLOCKED),
        )
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_blocked_slice_requires_blocked_on(self):
        p = _project_with_slice(status=Status.BLOCKED, blocked_on=None)
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_blocked_slice_with_blocked_on_ok(self):
        p = _project_with_slice(
            status=Status.BLOCKED,
            blocked_on=BlockedOn(kind="id", value="P1.S2"),
        )
        validate_project(p)

class DateOrderTests(unittest.TestCase):
    def test_closed_before_created_rejected(self):
        p = _project_with_slice(
            status=Status.DONE, closed="2026-05-16",
        )
        # need created set on slice itself; the helper already does that.
        p.phases[0].slices[0].created = "2026-05-17"
        with self.assertRaises(ValidationError):
            validate_project(p)

class DateFormatTests(unittest.TestCase):
    def test_malformed_created_rejected(self):
        p = _project_with_slice()
        p.phases[0].slices[0].created = "17-05-2026"
        with self.assertRaises(ValidationError) as ctx:
            validate_project(p)
        self.assertIn("date", str(ctx.exception).lower())

    def test_malformed_closed_rejected(self):
        p = _project_with_slice(status=Status.DONE, closed="not-a-date")
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_invalid_calendar_month_rejected(self):
        p = _project_with_slice()
        p.phases[0].slices[0].created = "2026-99-99"
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_invalid_calendar_day_rejected(self):
        p = _project_with_slice()
        p.phases[0].slices[0].created = "2026-02-31"
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_valid_calendar_date_accepted(self):
        p = _project_with_slice()
        p.phases[0].slices[0].created = "2026-02-28"
        validate_project(p)  # no raise

    def test_basic_iso_format_rejected(self):
        # Python's date.fromisoformat accepts 20260228, but we require dashes.
        p = _project_with_slice()
        p.phases[0].slices[0].created = "20260228"
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_week_date_format_rejected(self):
        p = _project_with_slice()
        p.phases[0].slices[0].created = "2026-W09-6"
        with self.assertRaises(ValidationError):
            validate_project(p)

class PathWarningTests(unittest.TestCase):
    def test_missing_ref_emits_warning(self):
        from tasktool.validate import find_path_warnings
        p = _project_with_slice(refs=["nonexistent.md"])
        with tempfile.TemporaryDirectory() as td:
            warnings = find_path_warnings(p, Path(td))
        self.assertTrue(any("nonexistent.md" in w for w in warnings))

    def test_existing_ref_no_warning(self):
        from tasktool.validate import find_path_warnings
        p = _project_with_slice(refs=["a.md"])
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "a.md").write_text("", encoding="utf-8")
            warnings = find_path_warnings(p, Path(td))
        self.assertEqual(warnings, [])

class StrictFormatTests(unittest.TestCase):
    def test_canonical_passes(self):
        p = Project(project="demo")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tasklist.json"
            save_project(p, path)
            strict_format_check(path)  # no raise

    def test_non_canonical_fails(self):
        p = Project(project="demo")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tasklist.json"
            path.write_text(dumps_canonical(p).replace("  ", "    "), encoding="utf-8")
            with self.assertRaises(ValidationError):
                strict_format_check(path)

    def test_normalise_rewrites_file(self):
        p = Project(project="demo")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tasklist.json"
            path.write_text(dumps_canonical(p).replace("  ", "    "), encoding="utf-8")
            normalise_file(path)
            strict_format_check(path)  # now passes
