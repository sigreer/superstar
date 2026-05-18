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

# ───── set / close / block / unblock ─────

def _resolve_id(p: Project, id: str) -> str:
    """Resolve a short ID to its fully-qualified form when unambiguous (spec §7 conventions).
    Phase and cross IDs need no resolution. Short S/T IDs are accepted only when exactly one
    matching item exists across the whole project."""
    parsed = parse_id(id)[0]
    if "." in id or parsed in ("phase", "cross"):
        return id
    if parsed == "slice":
        matches = [(ph.id, s.id) for ph in p.phases for s in ph.slices if s.id == id]
        if not matches:
            raise CommandError(f"slice {id} not found")
        if len(matches) > 1:
            qids = ", ".join(f"{ph}.{s}" for ph, s in matches)
            raise CommandError(f"ambiguous short id {id!r}; matches: {qids}. Use fully-qualified form.")
        return f"{matches[0][0]}.{matches[0][1]}"
    if parsed == "task":
        matches = [(ph.id, s.id, t.id) for ph in p.phases for s in ph.slices for t in s.tasks if t.id == id]
        if not matches:
            raise CommandError(f"task {id} not found")
        if len(matches) > 1:
            qids = ", ".join(f"{ph}.{s}.{t}" for ph, s, t in matches)
            raise CommandError(f"ambiguous short id {id!r}; matches: {qids}. Use fully-qualified form.")
        ph, s, t = matches[0]
        return f"{ph}.{s}.{t}"
    return id

def cmd_create_task(*, repo_root: Path, slice_id: str, title: str) -> str:
    """Now accepts unambiguous short slice IDs via _resolve_id. Replaces the
    fully-qualified-only version from Task 8."""
    p = _load(repo_root)
    qid = _resolve_id(p, slice_id)
    if parse_id(qid)[0] != "slice":
        raise CommandError(f"task creation requires a slice id, got {slice_id!r} ({parse_id(qid)[0]})")
    phase_part, slice_part, _ = split_qualified(qid)
    phase = next(ph for ph in p.phases if ph.id == phase_part)
    slc = next(s for s in phase.slices if s.id == slice_part)
    new_id = next_task_id(p, phase_part, slice_part)
    slc.tasks.append(Task(id=new_id, title=title, created=_today()))
    _save(repo_root, p)
    return new_id

def _find_item(p: Project, id: str):
    """Returns (qid, container_list, item). Accepts fully-qualified or unambiguous short.
    The returned qid is the fully-qualified form — callers MUST use it for any downstream
    operation that searches by ID (reviewer-chain discovery in particular), to avoid the
    short-form aliasing across historical chains."""
    qid = _resolve_id(p, id)
    parsed = parse_id(qid)[0]
    if parsed == "phase":
        for ph in p.phases:
            if ph.id == qid:
                return qid, p.phases, ph
        raise CommandError(f"phase {qid} not found")
    if parsed == "cross":
        for c in p.cross_cutting:
            if c.id == qid:
                return qid, p.cross_cutting, c
        raise CommandError(f"cross-cutting {qid} not found")
    phase_part, slice_part, task_part = split_qualified(qid)
    phase = next((ph for ph in p.phases if ph.id == phase_part), None)
    if phase is None:
        raise CommandError(f"phase {phase_part} not found")
    if task_part is not None:
        slc = next((s for s in phase.slices if s.id == slice_part), None)
        if slc is None:
            raise CommandError(f"slice {phase_part}.{slice_part} not found")
        task = next((t for t in slc.tasks if t.id == task_part), None)
        if task is None:
            raise CommandError(f"task {qid} not found")
        return qid, slc.tasks, task
    slc = next((s for s in phase.slices if s.id == slice_part), None)
    if slc is None:
        raise CommandError(f"slice {qid} not found")
    return qid, phase.slices, slc

def _apply_review_gate(
    repo_root: Path, p: Project, item, id: str, kind_label: str,
    reviewer_chain: Path | None, skip_review_gate: bool,
) -> None:
    """Mutates item to record reviewer_chain or skip note."""
    if skip_review_gate:
        ts = _dt.datetime.now().isoformat(timespec="seconds")
        note = f"[{ts}] review gate skipped for {id}"
        item.notes = (item.notes + "\n" + note).strip() if item.notes else note
        return
    gate_kind = "post-slice" if kind_label == "slice" else "post-phase"
    try:
        result = check_gate(repo_root, id, gate_kind, explicit=reviewer_chain)
    except GateError as e:
        raise CommandError(f"review gate failed: {e}") from e
    rel = result.chain.relative_to(repo_root).as_posix()
    if kind_label == "slice":
        item.reviewer_chain = rel
    else:
        item.phase_reviewer_chain = rel

def cmd_set(
    *, repo_root: Path, id: str, status: str,
    reviewer_chain: Path | None = None, skip_review_gate: bool = False,
) -> None:
    p = _load(repo_root)
    qid, _container, item = _find_item(p, id)
    new_status = Status(status)
    kind = parse_id(qid)[0]
    if new_status == Status.BLOCKED and kind != "slice":
        raise CommandError(f"only slices can be blocked; {qid} is a {kind}")
    if new_status == Status.DONE and kind in ("slice", "phase"):
        _apply_review_gate(repo_root, p, item, qid, kind, reviewer_chain, skip_review_gate)
    item.status = new_status
    if new_status == Status.DONE and item.closed is None:
        item.closed = _today()
    _save(repo_root, p)

def cmd_close(
    *, repo_root: Path, id: str,
    refs: list[str] | None = None, closed_date: str | None = None,
    note: str | None = None,
    reviewer_chain: Path | None = None, skip_review_gate: bool = False,
) -> None:
    p = _load(repo_root)
    qid, _container, item = _find_item(p, id)
    kind = parse_id(qid)[0]
    if kind == "task" or kind == "cross":
        pass  # no gate; just close
    elif kind in ("slice", "phase"):
        _apply_review_gate(repo_root, p, item, qid, kind, reviewer_chain, skip_review_gate)
    else:
        raise CommandError(f"cannot close {kind} {qid}")
    item.status = Status.DONE
    item.closed = closed_date or _today()
    if refs:
        for r in refs:
            if r not in item.refs:
                item.refs.append(r)
    if note:
        item.notes = (item.notes + "\n" + note).strip() if item.notes else note
    _save(repo_root, p)

def cmd_block(*, repo_root: Path, slice_id: str, on: str) -> None:
    p = _load(repo_root)
    if not is_slice_id(slice_id):
        raise CommandError(f"block only works on slices; {slice_id} is a {kind_of(slice_id)}")
    _qid, _container, item = _find_item(p, slice_id)
    if on.startswith("external:"):
        item.blocked_on = BlockedOn(kind="external", value=on[len("external:"):])
    else:
        parse_id(on)  # validate
        item.blocked_on = BlockedOn(kind="id", value=on)
    item.status = Status.BLOCKED
    _save(repo_root, p)

def cmd_unblock(*, repo_root: Path, slice_id: str, resume: bool = False) -> None:
    p = _load(repo_root)
    if not is_slice_id(slice_id):
        raise CommandError(f"unblock only works on slices; {slice_id} is a {kind_of(slice_id)}")
    _qid, _container, item = _find_item(p, slice_id)
    item.blocked_on = None
    item.status = Status.IN_PROGRESS if resume else Status.READY
    _save(repo_root, p)

# ───── note / ref / title ─────

def cmd_note(
    *, repo_root: Path, id: str,
    append: str | None = None, replace: str | None = None,
) -> None:
    if (append is None) == (replace is None):
        raise CommandError("cmd_note requires exactly one of append/replace")
    p = _load(repo_root)
    _qid, _container, item = _find_item(p, id)
    if append is not None:
        item.notes = (item.notes + "\n" + append).strip() if item.notes else append
    else:
        item.notes = replace or ""
    _save(repo_root, p)

def cmd_ref(
    *, repo_root: Path, id: str,
    add: str | None = None, remove: str | None = None,
) -> None:
    if (add is None) == (remove is None):
        raise CommandError("cmd_ref requires exactly one of add/remove")
    p = _load(repo_root)
    qid, _container, item = _find_item(p, id)
    if not hasattr(item, "refs"):
        raise CommandError(f"{qid}: this item kind does not have refs")
    if add is not None and add not in item.refs:
        item.refs.append(add)
    elif remove is not None and remove in item.refs:
        item.refs.remove(remove)
    _save(repo_root, p)

def cmd_title(*, repo_root: Path, id: str, new: str) -> None:
    p = _load(repo_root)
    _qid, _container, item = _find_item(p, id)
    item.title = new
    _save(repo_root, p)
