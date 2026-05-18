# tools/tasktool/commands.py
from __future__ import annotations
import datetime as _dt
from pathlib import Path
from tasktool.model import (
    Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status,
)
from tasktool.serialize import load_project, save_project
from tasktool.validate import validate_project
from tasktool.allocate import (
    next_phase_id, next_slice_id, next_task_id, next_cross_id, next_followup_letter,
)
from tasktool.ids import split_qualified, kind_of, is_slice_id, parse_id
from tasktool.reviewer_gate import check_gate, GateError, GatePass

class CommandError(RuntimeError):
    pass

DEFAULT_JSON_REL = "docs/tasklist.json"

def _today() -> str:
    return _dt.date.today().isoformat()

def _tasklist_path(repo_root: Path) -> Path:
    return repo_root / DEFAULT_JSON_REL

def _load(repo_root: Path) -> Project:
    path = _tasklist_path(repo_root)
    if not path.exists():
        raise CommandError(f"{path}: tasklist.json not found. Run `tasktool init` first.")
    return load_project(path)

def _save(repo_root: Path, p: Project) -> None:
    validate_project(p)
    save_project(p, _tasklist_path(repo_root))

# ───── init ─────

def cmd_init(*, repo_root: Path, project: str | None = None, north_star: str = "", force: bool = False) -> None:
    """Create empty tasklist.json. If `project` is omitted, derive from repo_root.name
    (matches spec §7.1 syntax `init [--project NAME]`)."""
    path = _tasklist_path(repo_root)
    if path.exists() and not force:
        raise CommandError(f"{path}: already exists. Pass --force to overwrite.")
    path.parent.mkdir(parents=True, exist_ok=True)
    project_name = project or repo_root.name
    _save(repo_root, Project(project=project_name, north_star=north_star, last_reviewed=_today()))

# ───── create ─────

def cmd_create_phase(*, repo_root: Path, title: str, spec: str | None = None, plan: str | None = None) -> str:
    p = _load(repo_root)
    new_id = next_phase_id(p, repo_root)
    p.phases.append(Phase(
        id=new_id, title=title, created=_today(),
        spec_path=spec, plan_path=plan,
    ))
    _save(repo_root, p)
    return new_id

def cmd_create_slice(
    *, repo_root: Path, phase_id: str, title: str,
    follow_up: str | None = None, plan: str | None = None,
) -> str:
    p = _load(repo_root)
    phase = next((ph for ph in p.phases if ph.id == phase_id), None)
    if phase is None:
        raise CommandError(f"phase {phase_id} not found")
    if follow_up is None:
        new_id = next_slice_id(p, phase_id, repo_root)
    else:
        new_id = next_followup_letter(p, phase_id, follow_up, repo_root)
    phase.slices.append(Slice(
        id=new_id, title=title, created=_today(), plan_path=plan,
    ))
    _save(repo_root, p)
    return new_id

def cmd_create_task(*, repo_root: Path, slice_id: str, title: str) -> str:
    """In Task 8, only fully-qualified slice IDs (e.g. P1.S2) are accepted.
    Task 9 extends this to accept unambiguous short IDs by routing through _resolve_id."""
    p = _load(repo_root)
    phase_part, slice_part, _ = split_qualified(slice_id)
    if phase_part is None or slice_part is None:
        raise CommandError(f"task creation requires fully-qualified slice id (e.g. P1.S2), got {slice_id!r}")
    phase = next((ph for ph in p.phases if ph.id == phase_part), None)
    if phase is None:
        raise CommandError(f"phase {phase_part} not found")
    slc = next((s for s in phase.slices if s.id == slice_part), None)
    if slc is None:
        raise CommandError(f"slice {phase_part}.{slice_part} not found")
    new_id = next_task_id(p, phase_part, slice_part)
    slc.tasks.append(Task(id=new_id, title=title, created=_today()))
    _save(repo_root, p)
    return new_id

def cmd_create_cross(*, repo_root: Path, title: str) -> str:
    p = _load(repo_root)
    new_id = next_cross_id(p, repo_root)
    p.cross_cutting.append(CrossCutting(id=new_id, title=title, created=_today()))
    _save(repo_root, p)
    return new_id
