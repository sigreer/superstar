# tools/tasktool/validate.py
from __future__ import annotations
import re
from pathlib import Path
from tasktool.model import (
    ArchivedCrossCutting,
    Project,
    Phase,
    Slice,
    Task,
    CrossCutting,
    Status,
    PlanningStatus,
)
from tasktool.serialize import load_project, save_project, dumps_canonical
from tasktool.ids import parse_id, IdParseError

class ValidationError(ValueError):
    """Raised when the project violates a validation rule."""

import datetime as _dt

_PHASE_RE = re.compile(r"^P\d+$")
_SLICE_RE = re.compile(r"^S\d+[a-z]?$")
_TASK_RE = re.compile(r"^T\d+$")
_CROSS_RE = re.compile(r"^X\d+$")
_DATE_SHAPE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValidationError(msg)

def _check_id(value: str, pattern: re.Pattern[str], scope: str) -> None:
    _require(bool(pattern.match(value)), f"{scope}: malformed id {value!r}")

def _check_date(value: str | None, scope: str, field: str) -> None:
    """Validate that value matches the literal YYYY-MM-DD shape *and* parses as a real
    calendar date. The shape check is required because Python 3.11+ `date.fromisoformat`
    additionally accepts forms like `20260228` (basic) and `2026-W09-6` (week-date), which
    would break lexical string comparison elsewhere."""
    if value is None:
        return
    if not _DATE_SHAPE.match(value):
        raise ValidationError(
            f"{scope}.{field}: malformed date {value!r} (expected YYYY-MM-DD)"
        )
    try:
        _dt.date.fromisoformat(value)
    except ValueError as e:
        raise ValidationError(
            f"{scope}.{field}: invalid calendar date {value!r}: {e}"
        ) from e

def _check_dates(
    created: str,
    started: str | None,
    closed: str | None,
    scope: str,
) -> None:
    _check_date(created, scope, "created")
    _check_date(started, scope, "started")
    _check_date(closed, scope, "closed")
    if started is not None and started < created:
        raise ValidationError(f"{scope}: started {started} precedes created {created}")
    if closed is not None and closed < created:
        raise ValidationError(f"{scope}: closed {closed} precedes created {created}")
    if started is not None and closed is not None and closed < started:
        raise ValidationError(f"{scope}: closed {closed} precedes started {started}")

def _check_task(t: Task, scope: str) -> None:
    _check_id(t.id, _TASK_RE, scope)
    _require(t.status != Status.BLOCKED, f"{scope}: tasks cannot be blocked (slice-only)")
    if t.status == Status.DONE:
        _require(t.closed is not None, f"{scope}: status=done requires closed date")
    _check_dates(t.created, t.started, t.closed, scope)

def _check_slice(s: Slice, scope: str) -> None:
    _check_id(s.id, _SLICE_RE, scope)
    _require(
        s.planning_status in set(PlanningStatus),
        f"{scope}: invalid planning_status {s.planning_status!r}",
    )
    if s.status == Status.BLOCKED:
        _require(s.blocked_on is not None, f"{scope}: blocked requires blocked_on")
    if s.blocked_on is not None:
        _require(s.status == Status.BLOCKED, f"{scope}: blocked_on without blocked status")
    if s.status == Status.DONE:
        _require(s.closed is not None, f"{scope}: status=done requires closed date")
    _check_dates(s.created, s.started, s.closed, scope)
    seen: set[str] = set()
    for t in s.tasks:
        sub = f"{scope}.{t.id}"
        _require(t.id not in seen, f"{sub}: duplicate task id")
        seen.add(t.id)
        _check_task(t, sub)

def _check_phase(p: Phase, scope: str) -> None:
    _check_id(p.id, _PHASE_RE, scope)
    _require(p.status != Status.BLOCKED, f"{scope}: phases cannot be blocked")
    if p.status == Status.DONE:
        _require(p.closed is not None, f"{scope}: status=done requires closed date")
    _check_dates(p.created, p.started, p.closed, scope)
    seen: set[str] = set()
    for s in p.slices:
        sub = f"{scope}.{s.id}"
        _require(s.id not in seen, f"{sub}: duplicate slice id")
        seen.add(s.id)
        _check_slice(s, sub)

def _check_cross(c: CrossCutting, scope: str) -> None:
    _check_id(c.id, _CROSS_RE, scope)
    _require(c.status != Status.BLOCKED, f"{scope}: cross-cutting cannot be blocked")
    if c.status == Status.DONE:
        _require(c.closed is not None, f"{scope}: status=done requires closed date")
    _check_dates(c.created, c.started, c.closed, scope)

def _check_archived_cross(c: ArchivedCrossCutting, scope: str) -> None:
    _check_id(c.id, _CROSS_RE, scope)
    _require(bool(c.title.strip()), f"{scope}: archived cross title is required")
    _require(bool(c.archived_path.strip()), f"{scope}: archived_path is required")
    _check_date(c.archived_date, scope, "archived_date")

def validate_project(p: Project) -> None:
    """Raise ValidationError on rule violation. Returns None on clean."""
    seen_phase: set[str] = set()
    for ph in p.phases:
        _require(ph.id not in seen_phase, f"P*: duplicate phase id {ph.id}")
        seen_phase.add(ph.id)
        _check_phase(ph, ph.id)
        _check_slice_dependencies(ph)
    seen_cross: set[str] = set()
    for c in p.cross_cutting:
        _require(c.id not in seen_cross, f"X*: duplicate cross id {c.id}")
        seen_cross.add(c.id)
        _check_cross(c, c.id)
    seen_archived_cross: set[str] = set()
    for c in p.archived_cross_cutting:
        _require(
            c.id not in seen_archived_cross,
            f"X*: duplicate archived cross id {c.id}",
        )
        _require(
            c.id not in seen_cross,
            f"{c.id} appears in both active and archived cross-cutting",
        )
        seen_archived_cross.add(c.id)
        _check_archived_cross(c, c.id)

def _check_slice_dependencies(ph: Phase) -> None:
    slice_ids = {f"{ph.id}.{s.id}" for s in ph.slices}
    graph = {f"{ph.id}.{s.id}": list(s.depends_on) for s in ph.slices}
    for qid, deps in graph.items():
        seen_deps: set[str] = set()
        for dep in deps:
            try:
                kind, parsed = parse_id(dep)
            except IdParseError as e:
                raise ValidationError(f"{qid}.depends_on: malformed dependency {dep!r}") from e
            _require(kind == "slice" and "." in parsed,
                     f"{qid}.depends_on: dependency must be a fully-qualified slice id, got {dep!r}")
            _require(parsed != qid, f"{qid}.depends_on: slice cannot depend on itself")
            _require(parsed in slice_ids, f"{qid}.depends_on: unknown slice dependency {dep!r}")
            _require(parsed not in seen_deps, f"{qid}.depends_on: duplicate dependency {dep!r}")
            seen_deps.add(parsed)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, stack: list[str]) -> None:
        if node in visited:
            return
        if node in visiting:
            cycle = " -> ".join([*stack, node])
            raise ValidationError(f"{ph.id}.depends_on: cycle detected: {cycle}")
        visiting.add(node)
        for dep in graph[node]:
            visit(dep, [*stack, node])
        visiting.remove(node)
        visited.add(node)

    for qid in graph:
        visit(qid, [])

def find_path_warnings(p: Project, repo_root: Path) -> list[str]:
    """Walk every spec_path / plan_path / refs[] and return a list of warning strings
    for paths that do not exist on disk. Non-fatal — used by `tasktool validate`."""
    warnings: list[str] = []
    def _check(rel: str | None, scope: str) -> None:
        if rel is None:
            return
        if not (repo_root / rel).exists():
            warnings.append(f"{scope}: path does not exist: {rel}")
    for ph in p.phases:
        _check(ph.spec_path, f"{ph.id}.spec_path")
        _check(ph.plan_path, f"{ph.id}.plan_path")
        _check(ph.planning_path, f"{ph.id}.planning_path")
        for s in ph.slices:
            _check(s.plan_path, f"{ph.id}.{s.id}.plan_path")
            for r in s.refs:
                _check(r, f"{ph.id}.{s.id}.refs")
            for t in s.tasks:
                for r in t.refs:
                    _check(r, f"{ph.id}.{s.id}.{t.id}.refs")
    for c in p.cross_cutting:
        for r in c.refs:
            _check(r, f"{c.id}.refs")
    return warnings

def strict_format_check(path: Path) -> None:
    """Re-serialise and compare bytes. Raises ValidationError on mismatch."""
    text = path.read_text(encoding="utf-8")
    project = load_project(path)
    canonical = dumps_canonical(project)
    if text != canonical:
        raise ValidationError(
            f"{path}: not in canonical format. Run `tasktool validate --normalise` to fix."
        )

def normalise_file(path: Path) -> None:
    """Load, validate, and re-save in canonical format."""
    p = load_project(path)
    validate_project(p)
    save_project(p, path)

_FILENAME_ID_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}-"
    r"(?:(?P<cross>[Xx]\d+)"
    r"|(?P<phase>[Pp]\d+)"
      r"(?:-(?P<child>[SsXx]\d+[a-z]?))?"
      r"(?:-(?P<task>[Tt]\d+))?"
    r")-",
)

def _normalise_id(*, cross, phase, child, task):
    if cross:
        return cross.upper()
    assert phase is not None
    parts = [phase.upper()]
    if child:
        parts.append(child.upper())
    if task:
        parts.append(task.upper())
    return ".".join(parts)

def collect_known_ids(p):
    ids = set()
    for ph in p.phases:
        ids.add(ph.id)
        for sl in ph.slices:
            ids.add(f"{ph.id}.{sl.id}")
            for t in sl.tasks:
                ids.add(f"{ph.id}.{sl.id}.{t.id}")
    for ph in getattr(p, "archived_phases", []) or []:
        ids.add(ph.id if hasattr(ph, "id") else ph["id"])
    for x in getattr(p, "archived_cross_cutting", []) or []:
        ids.add(x.id if hasattr(x, "id") else x["id"])
    for x in p.cross_cutting:
        ids.add(x.id)
    return ids

def validate_orphan_filenames(p, paths):
    known = collect_known_ids(p)
    findings = []
    for path in paths:
        name = Path(path).name
        m = _FILENAME_ID_RE.match(name)
        if not m:
            continue
        fq = _normalise_id(cross=m.group("cross"), phase=m.group("phase"),
                           child=m.group("child"), task=m.group("task"))
        if fq in known:
            continue
        findings.append(f"{path}: filename references ID {fq} but no matching row in tasklist.json")
    return findings
