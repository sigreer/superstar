# tools/tasktool/tests/test_validate.py
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from tasktool.model import (
    ArchivedCrossCutting,
    Project,
    Phase,
    Slice,
    Task,
    CrossCutting,
    BlockedOn,
    Reservation,
    Status,
)
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

    def test_duplicate_archived_cross_ids(self):
        p = Project(project="demo")
        p.archived_cross_cutting.extend([
            ArchivedCrossCutting(
                id="X1",
                title="one",
                archived_path="docs/archived-tasks/X1-one.md",
                archived_date="2026-05-21",
            ),
            ArchivedCrossCutting(
                id="X1",
                title="two",
                archived_path="docs/archived-tasks/X1-two.md",
                archived_date="2026-05-21",
            ),
        ])

        with self.assertRaisesRegex(ValidationError, "duplicate archived cross id X1"):
            validate_project(p)

    def test_active_and_archived_cross_id_collision(self):
        p = Project(project="demo")
        p.cross_cutting.append(
            CrossCutting(id="X1", title="active", created="2026-05-21")
        )
        p.archived_cross_cutting.append(
            ArchivedCrossCutting(
                id="X1",
                title="archived",
                archived_path="docs/archived-tasks/X1-archived.md",
                archived_date="2026-05-21",
            )
        )

        with self.assertRaisesRegex(
            ValidationError,
            "X1 appears in both active and archived cross-cutting",
        ):
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

class DependencyTests(unittest.TestCase):
    def _project_with_two_slices(self) -> Project:
        p = _project_with_slice()
        p.phases[0].slices.append(Slice(id="S2", title="slice 2", created="2026-05-17"))
        return p

    def test_slice_dependency_on_existing_slice_ok(self):
        p = self._project_with_two_slices()
        p.phases[0].slices[1].depends_on = ["P1.S1"]
        validate_project(p)

    def test_slice_dependency_must_be_fully_qualified(self):
        p = self._project_with_two_slices()
        p.phases[0].slices[1].depends_on = ["S1"]
        with self.assertRaises(ValidationError) as ctx:
            validate_project(p)
        self.assertIn("fully-qualified slice", str(ctx.exception))

    def test_slice_dependency_must_exist(self):
        p = self._project_with_two_slices()
        p.phases[0].slices[1].depends_on = ["P1.S99"]
        with self.assertRaises(ValidationError) as ctx:
            validate_project(p)
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_slice_dependency_rejects_self_dependency(self):
        p = self._project_with_two_slices()
        p.phases[0].slices[0].depends_on = ["P1.S1"]
        with self.assertRaises(ValidationError) as ctx:
            validate_project(p)
        self.assertIn("itself", str(ctx.exception).lower())

    def test_slice_dependency_rejects_cycles(self):
        p = self._project_with_two_slices()
        p.phases[0].slices[0].depends_on = ["P1.S2"]
        p.phases[0].slices[1].depends_on = ["P1.S1"]
        with self.assertRaises(ValidationError) as ctx:
            validate_project(p)
        self.assertIn("cycle", str(ctx.exception).lower())

class DateOrderTests(unittest.TestCase):
    def test_closed_before_created_rejected(self):
        p = _project_with_slice(
            status=Status.DONE, closed="2026-05-16",
        )
        # need created set on slice itself; the helper already does that.
        p.phases[0].slices[0].created = "2026-05-17"
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_started_before_created_rejected(self):
        p = _project_with_slice(started="2026-05-16")
        p.phases[0].slices[0].created = "2026-05-17"
        with self.assertRaises(ValidationError) as ctx:
            validate_project(p)
        self.assertIn("started", str(ctx.exception))
        self.assertIn("precedes created", str(ctx.exception))

    def test_closed_before_started_rejected(self):
        p = _project_with_slice(
            started="2026-05-18",
            status=Status.DONE,
            closed="2026-05-17",
        )
        with self.assertRaises(ValidationError) as ctx:
            validate_project(p)
        self.assertIn("closed", str(ctx.exception))
        self.assertIn("precedes started", str(ctx.exception))

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

    def test_malformed_slice_started_rejected(self):
        p = _project_with_slice(started="20260517")
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_malformed_phase_started_rejected(self):
        p = _project_with_slice()
        p.phases[0].started = "20260517"
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_malformed_task_started_rejected(self):
        p = _project_with_slice()
        p.phases[0].slices[0].tasks.append(
            Task(id="T1", title="t", created="2026-05-17", started="2026-W20-7"),
        )
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_malformed_cross_cutting_started_rejected(self):
        p = _project_with_slice()
        p.cross_cutting.append(
            CrossCutting(id="X1", title="x", created="2026-05-17", started="2026-02-31"),
        )
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_malformed_archived_cross_date_and_path_rejected(self):
        p = Project(project="demo")
        p.archived_cross_cutting.append(
            ArchivedCrossCutting(
                id="X1",
                title="archived",
                archived_path="",
                archived_date="20260521",
            )
        )

        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_started_none_accepted(self):
        p = _project_with_slice(started=None)
        p.phases[0].started = None
        p.phases[0].slices[0].tasks.append(
            Task(id="T1", title="t", created="2026-05-17", started=None),
        )
        p.cross_cutting.append(
            CrossCutting(id="X1", title="x", created="2026-05-17", started=None),
        )
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

class SchemaEnumTests(unittest.TestCase):
    def _get_schema(self):
        from tasktool.schema_gen import build_schema
        return build_schema()

    def _find_kind(self, schema, pattern):
        """Return properties dict for items matching id pattern in schema."""
        def _walk(obj):
            if isinstance(obj, dict):
                props = obj.get("properties", {})
                id_pat = props.get("id", {}).get("pattern", "")
                if pattern in id_pat:
                    return props
                for v in obj.values():
                    result = _walk(v)
                    if result is not None:
                        return result
            elif isinstance(obj, list):
                for v in obj:
                    result = _walk(v)
                    if result is not None:
                        return result
            return None
        return _walk(schema)

    def test_task_status_has_no_blocked(self):
        """Task status enum must not contain 'blocked'."""
        schema = self._get_schema()
        task_props = self._find_kind(schema, r"^T\d+$")
        self.assertIsNotNone(task_props, "task schema not found")
        task_status_enum = task_props["status"]["enum"]
        self.assertNotIn("blocked", task_status_enum)

    def test_slice_status_has_blocked(self):
        """Slice status enum must contain 'blocked'."""
        schema = self._get_schema()
        slice_props = self._find_kind(schema, r"^S\d+")
        self.assertIsNotNone(slice_props, "slice schema not found")
        slice_status_enum = slice_props["status"]["enum"]
        self.assertIn("blocked", slice_status_enum)

    def test_phase_status_has_no_blocked(self):
        """Phase status enum must not contain 'blocked'."""
        schema = self._get_schema()
        phase_props = self._find_kind(schema, r"^P\d+$")
        self.assertIsNotNone(phase_props, "phase schema not found")
        phase_status_enum = phase_props["status"]["enum"]
        self.assertNotIn("blocked", phase_status_enum)

    def test_slice_schema_has_planning_fields(self):
        schema = self._get_schema()
        slice_props = self._find_kind(schema, r"^S\d+")
        self.assertIn("depends_on", slice_props)
        self.assertIn("planning_status", slice_props)
        self.assertIn("parallel_group", slice_props)

    def test_phase_schema_has_planning_path(self):
        schema = self._get_schema()
        phase_props = self._find_kind(schema, r"^P\d+$")
        self.assertIn("planning_path", phase_props)

    def test_lifecycle_items_include_started_date(self):
        schema = self._get_schema()
        for pattern in (r"^T\d+$", r"^S\d+", r"^P\d+$", r"^X\d+$"):
            props = self._find_kind(schema, pattern)
            self.assertIsNotNone(props)
            self.assertEqual(props["started"]["oneOf"][0]["pattern"], r"^\d{4}-\d{2}-\d{2}$")

    def test_cross_status_has_no_blocked(self):
        """Cross-cutting status enum must not contain 'blocked'."""
        schema = self._get_schema()
        cross_props = self._find_kind(schema, r"^X\d+$")
        self.assertIsNotNone(cross_props, "cross schema not found")
        cross_status_enum = cross_props["status"]["enum"]
        self.assertNotIn("blocked", cross_status_enum)


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


def test_validate_rejects_in_place_with_recorded_path():
    from tasktool.model import Project, Phase, Slice, Status
    from tasktool.validate import validate_project, ValidationError
    import pytest as _pt
    p = Project(project="d", phases=[Phase(id="P1", title="t", created="2026-05-21",
        slices=[Slice(id="S1", title="t", created="2026-05-21",
            worktree_in_place=True, worktree_path=".worktrees/x", worktree_branch="x")])])
    with _pt.raises(ValidationError, match="worktree_in_place"):
        validate_project(p)


def test_loads_project_rejects_string_for_worktree_in_place():
    from tasktool.serialize import loads_project
    from tasktool.validate import ValidationError
    import pytest as _pt
    text = (
        '{"project":"d","schema_version":1,'
        '"phases":[{"id":"P1","title":"t","created":"2026-05-21","status":"ready",'
        '"slices":[{"id":"S1","title":"t","created":"2026-05-21","status":"ready",'
        '"worktree_in_place":"false"}]}],'
        '"cross_cutting":[],"archived_phases":[],"archived_cross_cutting":[]}'
    )
    with _pt.raises(ValidationError, match="worktree_in_place"):
        loads_project(text)


def test_loads_project_rejects_int_for_worktree_path():
    from tasktool.serialize import loads_project
    from tasktool.validate import ValidationError
    import pytest as _pt
    text = (
        '{"project":"d","schema_version":1,'
        '"phases":[{"id":"P1","title":"t","created":"2026-05-21","status":"ready",'
        '"slices":[{"id":"S1","title":"t","created":"2026-05-21","status":"ready",'
        '"worktree_path":7,"worktree_branch":"x"}]}],'
        '"cross_cutting":[],"archived_phases":[],"archived_cross_cutting":[]}'
    )
    with _pt.raises(ValidationError, match="worktree_path"):
        loads_project(text)


def test_loads_project_rejects_non_date_for_pruned_at():
    from tasktool.serialize import loads_project, from_dict
    from tasktool.validate import ValidationError, validate_project
    import pytest as _pt
    text = (
        '{"project":"d","schema_version":1,'
        '"phases":[{"id":"P1","title":"t","created":"2026-05-21","status":"ready",'
        '"slices":[{"id":"S1","title":"t","created":"2026-05-21","status":"ready",'
        '"worktree_pruned_at":42}]}],'
        '"cross_cutting":[],"archived_phases":[],"archived_cross_cutting":[]}'
    )
    with _pt.raises(ValidationError, match="worktree_pruned_at"):
        loads_project(text)
    raw = {
        "project": "d", "schema_version": 1,
        "phases": [{"id": "P1", "title": "t", "created": "2026-05-21", "status": "ready",
            "slices": [{"id": "S1", "title": "t", "created": "2026-05-21", "status": "ready",
                "worktree_pruned_at": "not-a-date"}]}],
        "cross_cutting": [], "archived_phases": [], "archived_cross_cutting": [],
    }
    p = from_dict(raw)
    with _pt.raises(ValidationError):
        validate_project(p)


def test_validate_rejects_partial_worktree_fields():
    from tasktool.model import Project, Phase, Slice
    from tasktool.validate import validate_project, ValidationError
    import pytest as _pt
    p = Project(project="d", phases=[Phase(id="P1", title="t", created="2026-05-21",
        slices=[Slice(id="S1", title="t", created="2026-05-21",
            worktree_path=".worktrees/x", worktree_branch=None)])])
    with _pt.raises(ValidationError, match="both null or both set"):
        validate_project(p)


def test_validate_rejects_pending_without_at_timestamp():
    from tasktool.model import Project, Phase, Slice
    from tasktool.validate import validate_project, ValidationError
    p = Project(project="d")
    ph = Phase(id="P1", title="t", created="2026-05-21")
    s = Slice(id="S1", title="t", created="2026-05-21",
              worktree_prune_pending=True,
              worktree_prune_pending_at=None)
    ph.slices.append(s)
    p.phases.append(ph)
    import pytest
    with pytest.raises(ValidationError, match="worktree_prune_pending"):
        validate_project(p)


def test_validate_rejects_pending_at_without_pending_flag():
    from tasktool.model import Project, Phase, Slice
    from tasktool.validate import validate_project, ValidationError
    p = Project(project="d")
    ph = Phase(id="P1", title="t", created="2026-05-21")
    s = Slice(id="S1", title="t", created="2026-05-21",
              worktree_prune_pending=False,
              worktree_prune_pending_at="2026-05-22")
    ph.slices.append(s)
    p.phases.append(ph)
    import pytest
    with pytest.raises(ValidationError, match="worktree_prune_pending_at"):
        validate_project(p)


def test_validate_accepts_worktree_pruned_at_alone():
    from tasktool.model import Project, Phase, Slice
    from tasktool.validate import validate_project
    p = Project(project="d")
    ph = Phase(id="P1", title="t", created="2026-05-21")
    s = Slice(id="S1", title="t", created="2026-05-21",
              worktree_pruned_at="2026-05-22")
    ph.slices.append(s)
    p.phases.append(ph)
    validate_project(p)  # no raise


def test_cancelled_slice_requires_closed_date():
    import pytest
    p = _project_with_slice(status=Status.CANCELLED, closed=None)
    with pytest.raises(ValidationError, match="cancelled.*closed"):
        validate_project(p)


def test_cancelled_slice_with_closed_passes():
    p = _project_with_slice(
        status=Status.CANCELLED,
        started="2026-05-17",
        closed="2026-05-17",
    )
    validate_project(p)


def test_cancelled_task_rejected_semantically():
    import pytest
    p = _project_with_slice()
    p.phases[0].slices[0].tasks.append(
        Task(id="T1", title="t", created="2026-05-17",
             status=Status.CANCELLED, closed="2026-05-17"),
    )
    with pytest.raises(ValidationError, match="cancel.*task"):
        validate_project(p)


def test_cancelled_phase_requires_closed():
    import pytest
    p = Project(project="demo")
    p.phases.append(Phase(id="P1", title="p", created="2026-05-17",
                          status=Status.CANCELLED))
    with pytest.raises(ValidationError, match="cancelled.*closed"):
        validate_project(p)


def test_cancelled_cross_requires_closed():
    import pytest
    p = Project(project="demo")
    p.cross_cutting.append(CrossCutting(id="X1", title="x", created="2026-05-17",
                                        status=Status.CANCELLED))
    with pytest.raises(ValidationError, match="cancelled.*closed"):
        validate_project(p)


def test_validate_rejects_bad_pruned_at_date():
    from tasktool.model import Project, Phase, Slice
    from tasktool.validate import validate_project, ValidationError
    p = Project(project="d")
    ph = Phase(id="P1", title="t", created="2026-05-21")
    s = Slice(id="S1", title="t", created="2026-05-21",
              worktree_pruned_at="not-a-date")
    ph.slices.append(s)
    p.phases.append(ph)
    import pytest
    with pytest.raises(ValidationError):
        validate_project(p)


class SurfaceDriftWarningTests(unittest.TestCase):
    def test_parallel_group_no_surfaces_warns(self):
        from tasktool.validate import find_surface_drift_warnings
        p = _project_with_slice(parallel_group="core")
        with tempfile.TemporaryDirectory() as td:
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=True
            )
        self.assertTrue(
            any("parallel_group" in w and "P1.S1" in w for w in warnings),
            warnings,
        )

    def test_parallel_group_with_surfaces_no_warn(self):
        from tasktool.validate import find_surface_drift_warnings
        p = _project_with_slice(
            parallel_group="core", integration_surfaces=["commands"]
        )
        with tempfile.TemporaryDirectory() as td:
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=True
            )
        self.assertEqual(
            [w for w in warnings if "parallel_group" in w], []
        )

    def test_no_parallel_group_no_surfaces_no_warn(self):
        from tasktool.validate import find_surface_drift_warnings
        p = _project_with_slice()  # no parallel_group, no surfaces
        with tempfile.TemporaryDirectory() as td:
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=True
            )
        self.assertEqual(warnings, [])

    def test_terminal_slice_in_parallel_group_no_warn(self):
        from tasktool.validate import find_surface_drift_warnings
        p = _project_with_slice(
            parallel_group="core",
            status=Status.DONE,
            closed="2026-05-18",
        )
        with tempfile.TemporaryDirectory() as td:
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=True
            )
        self.assertEqual(warnings, [])

    def test_check1_runs_even_when_plan_checks_disabled(self):
        from tasktool.validate import find_surface_drift_warnings
        p = _project_with_slice(parallel_group="core")
        with tempfile.TemporaryDirectory() as td:
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=False
            )
        self.assertTrue(
            any("parallel_group" in w for w in warnings), warnings
        )

    def _plan_repo(self, td, plan_text):
        """Create a repo root with a plan file and return (repo_root, plan_rel)."""
        plan_rel = "docs/plans/plan.md"
        plan_abs = Path(td) / plan_rel
        plan_abs.parent.mkdir(parents=True, exist_ok=True)
        plan_abs.write_text(plan_text, encoding="utf-8")
        return Path(td), plan_rel

    def test_surface_present_in_plan_no_warn(self):
        from tasktool.validate import find_surface_drift_warnings
        with tempfile.TemporaryDirectory() as td:
            root, plan_rel = self._plan_repo(td, "writes the commands surface")
            p = _project_with_slice(
                plan_path=plan_rel, integration_surfaces=["commands"]
            )
            warnings = find_surface_drift_warnings(
                p, root, include_plan_checks=True
            )
        self.assertEqual([w for w in warnings if "surface" in w], [])

    def test_surface_absent_from_plan_warns(self):
        from tasktool.validate import find_surface_drift_warnings
        with tempfile.TemporaryDirectory() as td:
            root, plan_rel = self._plan_repo(td, "this plan mentions nothing useful")
            p = _project_with_slice(
                plan_path=plan_rel, integration_surfaces=["commands"]
            )
            warnings = find_surface_drift_warnings(
                p, root, include_plan_checks=True
            )
        self.assertTrue(
            any("commands" in w and "does not appear in plan" in w for w in warnings),
            warnings,
        )

    def test_reservation_absent_from_plan_warns(self):
        from tasktool.validate import find_surface_drift_warnings
        with tempfile.TemporaryDirectory() as td:
            root, plan_rel = self._plan_repo(td, "no reservations here")
            p = _project_with_slice(
                plan_path=plan_rel,
                reservations=[Reservation(resource="homepage-sort", value="15")],
            )
            warnings = find_surface_drift_warnings(
                p, root, include_plan_checks=True
            )
        self.assertTrue(
            any("homepage-sort:15" in w for w in warnings), warnings
        )

    def test_surface_match_is_case_insensitive(self):
        from tasktool.validate import find_surface_drift_warnings
        with tempfile.TemporaryDirectory() as td:
            root, plan_rel = self._plan_repo(td, "uses the cms-block-registry here")
            p = _project_with_slice(
                plan_path=plan_rel,
                integration_surfaces=["CMS-Block-Registry"],
            )
            warnings = find_surface_drift_warnings(
                p, root, include_plan_checks=True
            )
        self.assertEqual([w for w in warnings if "surface" in w], [])

    def test_no_plan_path_no_check2_warning(self):
        from tasktool.validate import find_surface_drift_warnings
        p = _project_with_slice(integration_surfaces=["commands"])  # plan_path None
        with tempfile.TemporaryDirectory() as td:
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=True
            )
        self.assertEqual([w for w in warnings if "does not appear" in w], [])

    def test_missing_plan_file_no_check2_warning(self):
        from tasktool.validate import find_surface_drift_warnings
        p = _project_with_slice(
            plan_path="docs/plans/gone.md", integration_surfaces=["commands"]
        )
        with tempfile.TemporaryDirectory() as td:
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=True
            )
        self.assertEqual([w for w in warnings if "does not appear" in w], [])

    def test_non_utf8_plan_file_swallowed(self):
        from tasktool.validate import find_surface_drift_warnings
        with tempfile.TemporaryDirectory() as td:
            plan_rel = "docs/plans/plan.md"
            plan_abs = Path(td) / plan_rel
            plan_abs.parent.mkdir(parents=True, exist_ok=True)
            plan_abs.write_bytes(b"\xff\xfe invalid utf8 \x80")
            p = _project_with_slice(
                plan_path=plan_rel, integration_surfaces=["commands"]
            )
            # Must not raise; decode error becomes a skip (no Check 2 warning).
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=True
            )
        self.assertEqual([w for w in warnings if "does not appear" in w], [])

    def test_check2_suppressed_when_plan_checks_disabled(self):
        from tasktool.validate import find_surface_drift_warnings
        with tempfile.TemporaryDirectory() as td:
            root, plan_rel = self._plan_repo(td, "mentions nothing")
            p = _project_with_slice(
                plan_path=plan_rel, integration_surfaces=["commands"]
            )
            warnings = find_surface_drift_warnings(
                p, root, include_plan_checks=False
            )
        self.assertEqual([w for w in warnings if "does not appear" in w], [])
