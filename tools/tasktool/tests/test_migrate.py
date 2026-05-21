from __future__ import annotations

from dataclasses import fields
from datetime import date

import pytest

from tasktool.migrate import (
    apply_deltas,
    compute_deltas,
    render_diff,
    walker_field_coverage,
)
from tasktool.model import (
    ArchivedCrossCutting,
    ArchivedPhase,
    CrossCutting,
    Phase,
    Project,
    Slice,
    Status,
    Task,
)


def _today() -> str:
    return date.today().isoformat()


def _project_with_slice(slice_status: Status = Status.READY) -> Project:
    return Project(
        project="demo",
        north_star="ns",
        last_reviewed=_today(),
        phases=[
            Phase(
                id="P1",
                title="phase",
                created=_today(),
                slices=[
                    Slice(
                        id="S1",
                        title="slice",
                        created=_today(),
                        status=slice_status,
                    ),
                ],
            )
        ],
    )


def test_no_drift_yields_no_deltas():
    local = _project_with_slice()
    authoritative = _project_with_slice()

    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)

    assert deltas == []
    assert conflicts == []


def test_public_api_accepts_positional_arguments():
    local = _project_with_slice(slice_status=Status.IN_PROGRESS)
    authoritative = _project_with_slice(slice_status=Status.READY)

    deltas, conflicts = compute_deltas(local, authoritative)
    merged = apply_deltas(authoritative, local, deltas, conflicts, "accept-local")

    assert merged.phases[0].slices[0].status == Status.IN_PROGRESS


def test_slice_status_drift_is_a_delta():
    local = _project_with_slice(slice_status=Status.IN_PROGRESS)
    authoritative = _project_with_slice(slice_status=Status.READY)

    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)

    assert any(d.row_id == "P1.S1" and d.field == "status" for d in deltas)
    assert conflicts == []


def test_local_only_row_is_addition():
    local = _project_with_slice()
    local.cross_cutting.append(
        CrossCutting(id="X9", title="local-only", created=_today())
    )
    authoritative = _project_with_slice()

    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)

    assert any(d.kind == "add" and d.row_id == "X9" for d in deltas)
    assert conflicts == []


def test_authoritative_only_row_is_kept_not_deleted():
    local = _project_with_slice()
    authoritative = _project_with_slice()
    authoritative.cross_cutting.append(
        CrossCutting(id="X9", title="authority-only", created=_today())
    )

    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)

    assert any(c.kind == "authoritative-only" and c.row_id == "X9" for c in conflicts)
    assert not any(d.kind == "delete" for d in deltas)


def test_apply_deltas_accept_local_preserves_authoritative_only_and_applies_status():
    local = _project_with_slice(slice_status=Status.IN_PROGRESS)
    authoritative = _project_with_slice(slice_status=Status.READY)
    authoritative.cross_cutting.append(
        CrossCutting(id="X9", title="authority-only", created=_today())
    )

    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)
    merged = apply_deltas(
        authoritative=authoritative,
        local=local,
        deltas=deltas,
        conflicts=conflicts,
        policy="accept-local",
    )

    assert any(c.id == "X9" for c in merged.cross_cutting)
    assert merged.phases[0].slices[0].status == Status.IN_PROGRESS


def test_apply_deltas_accept_authoritative_returns_authoritative_unchanged():
    local = _project_with_slice(slice_status=Status.IN_PROGRESS)
    authoritative = _project_with_slice(slice_status=Status.READY)
    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)

    merged = apply_deltas(
        authoritative=authoritative,
        local=local,
        deltas=deltas,
        conflicts=conflicts,
        policy="accept-authoritative",
    )

    assert merged is authoritative
    assert merged.phases[0].slices[0].status == Status.READY


def test_nested_task_field_drift_migrates():
    local = _project_with_slice()
    local.phases[0].slices[0].tasks.append(
        Task(
            id="T1",
            title="task",
            created=_today(),
            status=Status.IN_PROGRESS,
            notes="local",
        )
    )
    authoritative = _project_with_slice()
    authoritative.phases[0].slices[0].tasks.append(
        Task(id="T1", title="task", created=_today(), status=Status.READY, notes="")
    )

    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)

    fields_changed = {(d.row_id, d.field) for d in deltas}
    assert ("P1.S1.T1", "status") in fields_changed
    assert ("P1.S1.T1", "notes") in fields_changed
    assert conflicts == []


def test_render_diff_prints_field_changes_and_authoritative_only_rows():
    local = _project_with_slice(slice_status=Status.IN_PROGRESS)
    authoritative = _project_with_slice(slice_status=Status.READY)
    authoritative.cross_cutting.append(
        CrossCutting(id="X9", title="authority-only", created=_today())
    )
    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)

    rendered = render_diff(deltas, conflicts)

    assert "P1.S1" in rendered
    assert "status:" in rendered
    assert "ready -> in_progress" in rendered
    assert "X9" in rendered
    assert "authoritative-only (kept)" in rendered


def test_walker_covers_every_dataclass_field():
    coverage = walker_field_coverage()
    for row_type in (
        Project,
        Phase,
        Slice,
        Task,
        CrossCutting,
        ArchivedPhase,
        ArchivedCrossCutting,
    ):
        declared = {f.name for f in fields(row_type)}
        walked = coverage.get(row_type.__name__, set())
        missing = declared - walked
        assert not missing, (
            f"{row_type.__name__} fields missing from migrator walker: {missing}. "
            "Update tools/tasktool/migrate.py:_field_walker_map."
        )


def test_archived_phase_drift_migrates():
    local = _project_with_slice()
    local.archived_phases.append(
        ArchivedPhase(
            id="P0",
            title="old",
            archived_path="docs/x",
            archived_date=_today(),
        )
    )
    authoritative = _project_with_slice()

    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)

    assert any(d.kind == "add" and d.row_id == "P0" for d in deltas)
    assert conflicts == []


def test_archived_cross_cutting_drift_migrates():
    local = _project_with_slice()
    local.archived_cross_cutting.append(
        ArchivedCrossCutting(
            id="X1",
            title="archived cross",
            archived_path="docs/archived-tasks/X1-archived-cross.md",
            archived_date=_today(),
        )
    )
    authoritative = _project_with_slice()

    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)
    merged = apply_deltas(
        authoritative=authoritative,
        local=local,
        deltas=deltas,
        conflicts=conflicts,
        policy="accept-local",
    )

    assert any(d.kind == "add" and d.row_id == "X1" for d in deltas)
    assert conflicts == []
    assert merged.archived_cross_cutting[0].id == "X1"


def test_top_level_project_field_drift_migrates():
    local = _project_with_slice()
    local.north_star = "new mission"
    authoritative = _project_with_slice()
    authoritative.north_star = "old mission"

    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)

    assert any(d.row_id == "<project>" and d.field == "north_star" for d in deltas)
    assert conflicts == []


def _value_pair_for_field(row_type, field) -> tuple[object, object]:
    if field.name in {
        "id",
        "phases",
        "slices",
        "tasks",
        "cross_cutting",
        "archived_phases",
        "archived_cross_cutting",
    }:
        return (None, None)
    if field.name == "schema_version":
        return (1, 2)
    if field.name == "project":
        return ("old-project", "new-project")
    if field.name == "status":
        return (Status.READY, Status.IN_PROGRESS)
    if field.name == "title":
        return ("authority title", "local title")
    if field.name == "created":
        return ("2026-05-19", "2026-05-20")
    if field.name in {
        "started",
        "closed",
        "spec_path",
        "plan_path",
        "planning_path",
        "parallel_group",
        "reviewer_chain",
        "phase_reviewer_chain",
        "last_reviewed",
        "north_star",
        "archived_path",
        "archived_date",
    }:
        return (None, "2026-05-21")
    if field.name in {"refs", "depends_on"}:
        return ([], ["new-ref"])
    if field.name == "notes":
        return ("", "migrated notes")
    if field.name == "blocked_on":
        from tasktool.model import BlockedOn

        return (None, BlockedOn(kind="external", value="blocker"))
    if field.name == "planning_status":
        from tasktool.model import PlanningStatus

        return (PlanningStatus.PROPOSED, PlanningStatus.RATIFIED)
    return (None, None)


@pytest.mark.parametrize(
    "row_type",
    [Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, ArchivedCrossCutting],
)
def test_per_field_migration_acceptance_for_non_identity_non_collection_fields(row_type):
    for f in fields(row_type):
        auth_val, local_val = _value_pair_for_field(row_type, f)
        if auth_val is None and local_val is None:
            continue

        local = _project_with_slice()
        authoritative = _project_with_slice()

        def set_on(tree, value, *, type_=row_type):
            if type_ is Project:
                setattr(tree, f.name, value)
            elif type_ is Phase:
                setattr(tree.phases[0], f.name, value)
            elif type_ is Slice:
                setattr(tree.phases[0].slices[0], f.name, value)
            elif type_ is Task:
                if not tree.phases[0].slices[0].tasks:
                    tree.phases[0].slices[0].tasks.append(
                        Task(id="T1", title="task", created=_today())
                    )
                setattr(tree.phases[0].slices[0].tasks[0], f.name, value)
            elif type_ is CrossCutting:
                if not tree.cross_cutting:
                    tree.cross_cutting.append(
                        CrossCutting(id="X1", title="cross", created=_today())
                    )
                setattr(tree.cross_cutting[0], f.name, value)
            elif type_ is ArchivedPhase:
                if not tree.archived_phases:
                    tree.archived_phases.append(
                        ArchivedPhase(
                            id="P0",
                            title="archived",
                            archived_path="docs/x",
                            archived_date=_today(),
                        )
                    )
                setattr(tree.archived_phases[0], f.name, value)
            elif type_ is ArchivedCrossCutting:
                if not tree.archived_cross_cutting:
                    tree.archived_cross_cutting.append(
                        ArchivedCrossCutting(
                            id="X0",
                            title="archived cross",
                            archived_path="docs/archived-tasks/X0-archived-cross.md",
                            archived_date=_today(),
                        )
                    )
                setattr(tree.archived_cross_cutting[0], f.name, value)
            else:
                raise AssertionError(f"unknown row type: {type_}")

        def get_on(tree, *, type_=row_type):
            if type_ is Project:
                return getattr(tree, f.name)
            if type_ is Phase:
                return getattr(tree.phases[0], f.name)
            if type_ is Slice:
                return getattr(tree.phases[0].slices[0], f.name)
            if type_ is Task:
                return getattr(tree.phases[0].slices[0].tasks[0], f.name)
            if type_ is CrossCutting:
                return getattr(tree.cross_cutting[0], f.name)
            if type_ is ArchivedPhase:
                return getattr(tree.archived_phases[0], f.name)
            if type_ is ArchivedCrossCutting:
                return getattr(tree.archived_cross_cutting[0], f.name)
            raise AssertionError(f"unknown row type: {type_}")

        set_on(local, local_val)
        set_on(authoritative, auth_val)

        deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)
        merged = apply_deltas(
            authoritative=authoritative,
            local=local,
            deltas=deltas,
            conflicts=conflicts,
            policy="accept-local",
        )

        assert get_on(merged) == local_val, (
            f"{row_type.__name__}.{f.name} migration failed: "
            f"expected {local_val!r}, got {get_on(merged)!r}"
        )
