from __future__ import annotations

import copy
from dataclasses import dataclass, fields
from enum import Enum
from typing import Literal

from tasktool.model import (
    ArchivedCrossCutting,
    ArchivedPhase,
    CrossCutting,
    Phase,
    Project,
    Slice,
    Task,
)

Policy = Literal["accept-local", "accept-authoritative"]

_PROJECT_COLLECTIONS = (
    "phases",
    "cross_cutting",
    "archived_phases",
    "archived_cross_cutting",
)

# reservations_ledger rows have no `.id`; their identity is this composite.
_LEDGER_KEY_FIELDS = ("resource", "value", "scope", "owner_id")


@dataclass(frozen=True)
class Delta:
    kind: Literal["field", "add"]
    row_id: str
    field: str | None
    local_value: object | None
    authoritative_value: object | None


@dataclass(frozen=True)
class Conflict:
    kind: Literal["authoritative-only"]
    row_id: str
    note: str


def compute_deltas(
    local: Project, authoritative: Project
) -> tuple[list[Delta], list[Conflict]]:
    deltas: list[Delta] = []
    conflicts: list[Conflict] = []
    _diff_project(local, authoritative, deltas, conflicts)
    return deltas, conflicts


def apply_deltas(
    authoritative: Project,
    local: Project,
    deltas: list[Delta],
    conflicts: list[Conflict],
    policy: Policy,
) -> Project:
    if policy == "accept-authoritative":
        return authoritative
    if policy != "accept-local":
        raise ValueError(f"unknown policy: {policy}")
    return _apply_local(authoritative, local, deltas)


def render_diff(deltas: list[Delta], conflicts: list[Conflict]) -> str:
    lines: list[str] = []
    for delta in deltas:
        if delta.kind == "add":
            lines.append(f"{delta.row_id:12s}  add (local-only)")
            continue
        lines.append(
            f"{delta.row_id:12s}  {delta.field}: "
            f"{_fmt_value(delta.authoritative_value)} -> {_fmt_value(delta.local_value)}"
        )
    for conflict in conflicts:
        lines.append(
            f"{conflict.row_id:12s}  authoritative-only (kept): {conflict.note}"
        )
    if not lines:
        return "no drift detected\n"
    return "\n".join(lines) + "\n"


def walker_field_coverage() -> dict[str, set[str]]:
    return {
        "Project": (
            set(_project_scalar_fields())
            | set(_PROJECT_COLLECTIONS)
            | {"reservations_ledger"}
        ),
        "Phase": {field.name for field in fields(Phase)},
        "Slice": {field.name for field in fields(Slice)},
        "Task": {field.name for field in fields(Task)},
        "CrossCutting": {field.name for field in fields(CrossCutting)},
        "ArchivedPhase": {field.name for field in fields(ArchivedPhase)},
        "ArchivedCrossCutting": {
            field.name for field in fields(ArchivedCrossCutting)
        },
    }


def _project_scalar_fields() -> tuple[str, ...]:
    handled = set(_PROJECT_COLLECTIONS) | {"reservations_ledger"}
    return tuple(
        field.name
        for field in fields(Project)
        if field.name not in handled
    )


def _diff_project(
    local: Project,
    authoritative: Project,
    deltas: list[Delta],
    conflicts: list[Conflict],
) -> None:
    for field_name in _project_scalar_fields():
        _append_field_delta(
            deltas,
            row_id="<project>",
            field_name=field_name,
            local_value=getattr(local, field_name),
            authoritative_value=getattr(authoritative, field_name),
        )

    if _ledger_has_local_additions(local, authoritative):
        deltas.append(
            Delta(
                kind="add",
                row_id="<project>.reservations_ledger",
                field=None,
                local_value=list(local.reservations_ledger),
                authoritative_value=list(authoritative.reservations_ledger),
            )
        )

    _diff_collection(
        local_rows=local.phases,
        authoritative_rows=authoritative.phases,
        id_prefix="",
        row_dataclass=Phase,
        nested=[("slices", Slice, [("tasks", Task, [])])],
        deltas=deltas,
        conflicts=conflicts,
    )
    _diff_collection(
        local_rows=local.cross_cutting,
        authoritative_rows=authoritative.cross_cutting,
        id_prefix="",
        row_dataclass=CrossCutting,
        nested=[],
        deltas=deltas,
        conflicts=conflicts,
    )
    _diff_collection(
        local_rows=local.archived_phases,
        authoritative_rows=authoritative.archived_phases,
        id_prefix="",
        row_dataclass=ArchivedPhase,
        nested=[],
        deltas=deltas,
        conflicts=conflicts,
    )
    _diff_collection(
        local_rows=local.archived_cross_cutting,
        authoritative_rows=authoritative.archived_cross_cutting,
        id_prefix="",
        row_dataclass=ArchivedCrossCutting,
        nested=[],
        deltas=deltas,
        conflicts=conflicts,
    )


def _diff_collection(
    *,
    local_rows: list,
    authoritative_rows: list,
    id_prefix: str,
    row_dataclass: type,
    nested: list[tuple[str, type, list]],
    deltas: list[Delta],
    conflicts: list[Conflict],
) -> None:
    local_by_id = {row.id: row for row in local_rows}
    authoritative_by_id = {row.id: row for row in authoritative_rows}

    for row_id in local_by_id.keys() - authoritative_by_id.keys():
        deltas.append(
            Delta(
                kind="add",
                row_id=_qualify(id_prefix, row_id),
                field=None,
                local_value=local_by_id[row_id],
                authoritative_value=None,
            )
        )

    for row_id in authoritative_by_id.keys() - local_by_id.keys():
        conflicts.append(
            Conflict(
                kind="authoritative-only",
                row_id=_qualify(id_prefix, row_id),
                note="present in authoritative tasklist only",
            )
        )

    nested_attrs = {attr for attr, _, _ in nested}
    for row_id in local_by_id.keys() & authoritative_by_id.keys():
        local_row = local_by_id[row_id]
        authoritative_row = authoritative_by_id[row_id]
        qualified_row_id = _qualify(id_prefix, row_id)

        for field in fields(row_dataclass):
            if field.name in nested_attrs:
                continue
            _append_field_delta(
                deltas,
                row_id=qualified_row_id,
                field_name=field.name,
                local_value=getattr(local_row, field.name),
                authoritative_value=getattr(authoritative_row, field.name),
            )

        for attr, child_dataclass, deeper in nested:
            _diff_collection(
                local_rows=getattr(local_row, attr),
                authoritative_rows=getattr(authoritative_row, attr),
                id_prefix=qualified_row_id,
                row_dataclass=child_dataclass,
                nested=deeper,
                deltas=deltas,
                conflicts=conflicts,
            )


def _append_field_delta(
    deltas: list[Delta],
    *,
    row_id: str,
    field_name: str,
    local_value: object,
    authoritative_value: object,
) -> None:
    if local_value == authoritative_value:
        return
    deltas.append(
        Delta(
            kind="field",
            row_id=row_id,
            field=field_name,
            local_value=local_value,
            authoritative_value=authoritative_value,
        )
    )


def _apply_local(authoritative: Project, local: Project, deltas: list[Delta]) -> Project:
    merged = copy.deepcopy(authoritative)

    for delta in deltas:
        if delta.kind == "field" and delta.row_id == "<project>":
            setattr(merged, _require_field(delta), copy.deepcopy(delta.local_value))

    merged.reservations_ledger = _union_ledger(authoritative, local)

    _apply_collection(
        authoritative_rows=merged.phases,
        local_rows=local.phases,
        deltas=deltas,
        id_prefix="",
        nested=[("slices", Slice, [("tasks", Task, [])])],
    )
    _apply_collection(
        authoritative_rows=merged.cross_cutting,
        local_rows=local.cross_cutting,
        deltas=deltas,
        id_prefix="",
        nested=[],
    )
    _apply_collection(
        authoritative_rows=merged.archived_phases,
        local_rows=local.archived_phases,
        deltas=deltas,
        id_prefix="",
        nested=[],
    )
    _apply_collection(
        authoritative_rows=merged.archived_cross_cutting,
        local_rows=local.archived_cross_cutting,
        deltas=deltas,
        id_prefix="",
        nested=[],
    )
    return merged


def _apply_collection(
    *,
    authoritative_rows: list,
    local_rows: list,
    deltas: list[Delta],
    id_prefix: str,
    nested: list[tuple[str, type, list]],
) -> None:
    authoritative_by_id = {row.id: row for row in authoritative_rows}
    local_by_id = {row.id: row for row in local_rows}

    for row_id, local_row in local_by_id.items():
        qualified_row_id = _qualify(id_prefix, row_id)
        if row_id not in authoritative_by_id and any(
            delta.kind == "add" and delta.row_id == qualified_row_id
            for delta in deltas
        ):
            authoritative_rows.append(copy.deepcopy(local_row))
            authoritative_by_id[row_id] = authoritative_rows[-1]

    nested_attrs = {attr for attr, _, _ in nested}
    for row_id, authoritative_row in authoritative_by_id.items():
        if row_id not in local_by_id:
            continue
        local_row = local_by_id[row_id]
        qualified_row_id = _qualify(id_prefix, row_id)

        for delta in deltas:
            if (
                delta.kind == "field"
                and delta.row_id == qualified_row_id
                and delta.field not in nested_attrs
            ):
                setattr(
                    authoritative_row,
                    _require_field(delta),
                    copy.deepcopy(delta.local_value),
                )

        for attr, _child_dataclass, deeper in nested:
            _apply_collection(
                authoritative_rows=getattr(authoritative_row, attr),
                local_rows=getattr(local_row, attr),
                deltas=deltas,
                id_prefix=qualified_row_id,
                nested=deeper,
            )


def _require_field(delta: Delta) -> str:
    if delta.field is None:
        raise ValueError(f"delta {delta!r} has no field")
    return delta.field


def _ledger_key(row) -> tuple:
    return tuple(getattr(row, name) for name in _LEDGER_KEY_FIELDS)


def _ledger_has_local_additions(local, authoritative) -> bool:
    authoritative_keys = {_ledger_key(r) for r in authoritative.reservations_ledger}
    return any(
        _ledger_key(r) not in authoritative_keys
        for r in local.reservations_ledger
    )


def _union_ledger(authoritative, local) -> list:
    """Union authoritative + local ledger rows, deduped on the composite key.

    Authoritative rows are NEVER dropped (a stale-local empty ledger cannot
    erase archived reservations); local-only rows are appended. The first
    occurrence of each composite key wins, so authoritative metadata is
    authoritative for shared keys.
    """
    merged: list = []
    seen: set = set()
    for row in list(authoritative.reservations_ledger) + list(local.reservations_ledger):
        key = _ledger_key(row)
        if key in seen:
            continue
        seen.add(key)
        merged.append(copy.deepcopy(row))
    return merged


def _qualify(prefix: str, row_id: str) -> str:
    if not prefix:
        return row_id
    return f"{prefix}.{row_id}"


def _fmt_value(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, Enum):
        return value.value
    return repr(value)
