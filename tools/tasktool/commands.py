# tools/tasktool/commands.py
from __future__ import annotations
import datetime as _dt
import sys
import subprocess as _subprocess
from contextlib import contextmanager
from pathlib import Path
from tasktool.config import (
    TasklistConfig,
    TasktoolConfig,
    is_authoritative_required,
    load_config,
    save_config,
)
from tasktool.model import (
    Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status, PlanningStatus,
)
from tasktool.serialize import load_project, save_project
from tasktool.validate import validate_project
from tasktool.allocate import (
    next_phase_id, next_slice_id, next_task_id, next_cross_id, next_followup_letter,
)
from tasktool.ids import split_qualified, kind_of, is_slice_id, parse_id
from tasktool.reviewer_gate import check_gate, GateError, GatePass
from tasktool.notify import notify_tasktool_status
from tasktool.worktree import (
    AuthorityError,
    find_authoritative_root,
    git_current_branch,
    tasklist_has_unsafe_dirty_state,
    tasktool_lock,
    validate_authoritative_checkout,
)

class CommandError(RuntimeError):
    pass

DEFAULT_JSON_REL = "docs/tasklist.json"
UNCONFIGURED_HINT = (
    "tasktool: this repository has no authoritative-checkout routing configured. "
    "Run `tasktool config init-authority --branch <branch>` from the authoritative "
    "checkout to enable safe routing. Existing local-mode tasklists can be reconciled "
    "with `tasktool config migrate-from-local`. To opt out explicitly, run "
    "`tasktool config init-local`."
)

# Process-global toggle for `--no-stage`. Set by cli.main() before dispatch.
STAGE_AFTER_WRITE: bool = True

def _git_stage(repo_root: Path, path: Path) -> None:
    """Best-effort `git add`. Silent on any failure (not a git repo, git missing, etc.).
    Skipped entirely when STAGE_AFTER_WRITE is False (e.g. --no-stage)."""
    if not STAGE_AFTER_WRITE:
        return
    try:
        _subprocess.run(
            ["git", "add", "--", str(path.relative_to(repo_root))],
            cwd=repo_root, check=False,
            stdout=_subprocess.DEVNULL, stderr=_subprocess.DEVNULL,
        )
    except (OSError, ValueError):
        pass

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
    path = _tasklist_path(repo_root)
    save_project(p, path)
    _git_stage(repo_root, path)

def _notify_status(*, qid: str, kind: str, status: Status, title: str) -> None:
    try:
        notify_tasktool_status(
            work_id=qid,
            kind=kind,
            status=status.value,
            title=title,
        )
    except Exception:
        pass

def _resolve_write_root(repo_root: Path) -> tuple[Path, bool, str, str]:
    cfg = load_config(repo_root)
    if is_authoritative_required(cfg):
        raise CommandError(UNCONFIGURED_HINT)
    if cfg.tasklist.mutation_mode == "local":
        return repo_root, False, cfg.tasklist.mutation_mode, cfg.tasklist.authoritative_branch
    try:
        authoritative = find_authoritative_root(repo_root, branch=cfg.tasklist.authoritative_branch)
        validate_authoritative_checkout(
            authoritative,
            expected_branch=cfg.tasklist.authoritative_branch,
            caller_root=repo_root,
        )
    except AuthorityError as exc:
        raise CommandError(str(exc)) from exc
    return (
        authoritative,
        repo_root.resolve() != authoritative.resolve(),
        cfg.tasklist.mutation_mode,
        cfg.tasklist.authoritative_branch,
    )

@contextmanager
def _write_context(repo_root: Path):
    write_root, routed, mode, authoritative_branch = _resolve_write_root(repo_root)
    if mode == "authoritative-checkout":
        try:
            with tasktool_lock(repo_root):
                validate_authoritative_checkout(
                    write_root,
                    expected_branch=authoritative_branch,
                    caller_root=repo_root,
                )
                if tasklist_has_unsafe_dirty_state(write_root):
                    raise CommandError(
                        "authoritative docs/tasklist.json has unstaged changes; "
                        "commit, stash, or normalise them before running tasktool"
                    )
                if routed:
                    print(
                        f"tasktool: routed mutation to authoritative checkout: {write_root}",
                        file=sys.stderr,
                    )
                yield write_root
        except AuthorityError as exc:
            raise CommandError(str(exc)) from exc
    else:
        yield write_root

# ───── config ─────

def cmd_config_init_authority(*, repo_root: Path, branch: str) -> None:
    try:
        current_branch = git_current_branch(repo_root)
    except Exception:
        current_branch = ""
    if current_branch and current_branch != branch:
        raise CommandError(f"current checkout is on {current_branch!r}; expected branch {branch}")
    cfg = TasktoolConfig(
        tasklist=TasklistConfig(
            mutation_mode="authoritative-checkout",
            authoritative_branch=branch,
        )
    )
    save_config(repo_root, cfg)
    _git_stage(repo_root, repo_root / ".tasktool" / "config.json")

# ───── init ─────

def cmd_init(*, repo_root: Path, project: str | None = None, north_star: str = "", force: bool = False) -> None:
    """Create empty tasklist.json. If `project` is omitted, derive from repo_root.name
    (matches spec §7.1 syntax `init [--project NAME]`)."""
    with _write_context(repo_root) as write_root:
        path = _tasklist_path(write_root)
        if path.exists() and not force:
            raise CommandError(f"{path}: already exists. Pass --force to overwrite.")
        path.parent.mkdir(parents=True, exist_ok=True)
        project_name = project or repo_root.name
        _save(write_root, Project(project=project_name, north_star=north_star, last_reviewed=_today()))

# ───── create ─────

def cmd_create_phase(
    *, repo_root: Path, title: str,
    spec: str | None = None, plan: str | None = None,
    planning: str | None = None,
) -> str:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        new_id = next_phase_id(p, write_root)
        phase = Phase(
            id=new_id, title=title, created=_today(),
            spec_path=spec, plan_path=plan, planning_path=planning,
        )
        p.phases.append(phase)
        _save(write_root, p)
        _notify_status(qid=new_id, kind="phase", status=phase.status, title=phase.title)
        return new_id

def cmd_create_slice(
    *, repo_root: Path, phase_id: str, title: str,
    follow_up: str | None = None, plan: str | None = None,
    depends_on: list[str] | None = None, parallel_group: str | None = None,
) -> str:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        phase = next((ph for ph in p.phases if ph.id == phase_id), None)
        if phase is None:
            raise CommandError(f"phase {phase_id} not found")
        if follow_up is None:
            new_id = next_slice_id(p, phase_id, write_root)
        else:
            new_id = next_followup_letter(p, phase_id, follow_up, write_root)
        deps = [_resolve_dependency_id(p, dep) for dep in (depends_on or [])]
        slc = Slice(
            id=new_id, title=title, created=_today(), plan_path=plan,
            depends_on=deps, parallel_group=parallel_group,
        )
        phase.slices.append(slc)
        _save(write_root, p)
        _notify_status(qid=f"{phase_id}.{new_id}", kind="slice", status=slc.status, title=slc.title)
        return new_id

def cmd_create_cross(*, repo_root: Path, title: str) -> str:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        new_id = next_cross_id(p, write_root)
        item = CrossCutting(id=new_id, title=title, created=_today())
        p.cross_cutting.append(item)
        _save(write_root, p)
        _notify_status(qid=new_id, kind="cross", status=item.status, title=item.title)
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

def _resolve_dependency_id(p: Project, id: str) -> str:
    qid = _resolve_id(p, id)
    if parse_id(qid)[0] != "slice" or "." not in qid:
        raise CommandError(f"dependency must be a slice id, got {id!r}")
    return qid

def cmd_create_task(*, repo_root: Path, slice_id: str, title: str) -> str:
    """Now accepts unambiguous short slice IDs via _resolve_id. Replaces the
    fully-qualified-only version from Task 8."""
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid = _resolve_id(p, slice_id)
        if parse_id(qid)[0] != "slice":
            raise CommandError(f"task creation requires a slice id, got {slice_id!r} ({parse_id(qid)[0]})")
        phase_part, slice_part, _ = split_qualified(qid)
        phase = next(ph for ph in p.phases if ph.id == phase_part)
        slc = next(s for s in phase.slices if s.id == slice_part)
        new_id = next_task_id(p, phase_part, slice_part)
        task = Task(id=new_id, title=title, created=_today())
        slc.tasks.append(task)
        _save(write_root, p)
        _notify_status(qid=f"{phase_part}.{slice_part}.{new_id}", kind="task", status=task.status, title=task.title)
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
    invocation_root: Path, item, id: str, kind_label: str,
    reviewer_chain: Path | None, skip_review_gate: bool,
) -> None:
    """Mutates item to record reviewer_chain or skip note."""
    invocation_root = invocation_root.resolve()
    if skip_review_gate:
        ts = _dt.datetime.now().isoformat(timespec="seconds")
        note = f"[{ts}] review gate skipped for {id}"
        item.notes = (item.notes + "\n" + note).strip() if item.notes else note
        return
    gate_kind = "post-slice" if kind_label == "slice" else "post-phase"
    if reviewer_chain is not None:
        resolved = (
            reviewer_chain.resolve()
            if reviewer_chain.is_absolute()
            else (invocation_root / reviewer_chain).resolve()
        )
        try:
            resolved.relative_to(invocation_root)
        except ValueError as exc:
            raise CommandError(f"reviewer chain is outside repository: {reviewer_chain}") from exc
        reviewer_chain = resolved
    try:
        result = check_gate(invocation_root, id, gate_kind, explicit=reviewer_chain)
    except GateError as e:
        raise CommandError(f"review gate failed: {e}") from e
    rel = result.chain.resolve().relative_to(invocation_root).as_posix()
    if kind_label == "slice":
        item.reviewer_chain = rel
    else:
        item.phase_reviewer_chain = rel

def _start_item(qid: str, item, *, resume: bool = False) -> None:
    if item.status == Status.DONE:
        raise CommandError(f"{qid} is already done")
    if item.status == Status.BLOCKED:
        if not resume:
            raise CommandError(f"{qid} is blocked; use start --resume to clear blocked_on")
        item.blocked_on = None
    item.status = Status.IN_PROGRESS
    if getattr(item, "started", None) is None:
        item.started = _today()

def _apply_ready_close_override(qid: str, item, *, reason: str | None) -> None:
    if not reason or not reason.strip():
        raise CommandError(f"{qid} ready-close override requires --reason")
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    audit = f"[{ts}] ready-close override for {qid}: {reason.strip()}"
    item.notes = (item.notes + "\n" + audit).strip() if item.notes else audit

def cmd_start(*, repo_root: Path, id: str, resume: bool = False) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        kind = parse_id(qid)[0]
        _start_item(qid, item, resume=resume)
        _save(write_root, p)
        _notify_status(qid=qid, kind=kind, status=item.status, title=item.title)

def cmd_set(
    *, repo_root: Path, id: str, status: str,
    reviewer_chain: Path | None = None, skip_review_gate: bool = False,
    allow_ready_close: bool = False, reason: str | None = None,
) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        new_status = Status(status)
        kind = parse_id(qid)[0]
        if new_status == Status.BLOCKED and kind != "slice":
            raise CommandError(f"only slices can be blocked; {qid} is a {kind}")
        if new_status == Status.DONE and kind in ("slice", "phase"):
            _apply_review_gate(repo_root, item, qid, kind, reviewer_chain, skip_review_gate)
        if new_status == Status.DONE and kind == "slice" and getattr(item, "started", None) is None:
            if not allow_ready_close:
                raise CommandError(
                    f"{qid} must be started before close; run `tasktool start {qid}` first, "
                    f"or use `tasktool set {qid} --status done --allow-ready-close --reason ...` if applicable"
                )
            _apply_ready_close_override(qid, item, reason=reason)
        if new_status == Status.IN_PROGRESS:
            _start_item(qid, item)
        else:
            item.status = new_status
        if new_status == Status.DONE and item.closed is None:
            item.closed = _today()
        _save(write_root, p)
        _notify_status(qid=qid, kind=kind, status=item.status, title=item.title)

def cmd_close(
    *, repo_root: Path, id: str,
    refs: list[str] | None = None, closed_date: str | None = None,
    note: str | None = None,
    reviewer_chain: Path | None = None, skip_review_gate: bool = False,
    allow_ready_close: bool = False, reason: str | None = None,
) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        kind = parse_id(qid)[0]
        if kind == "task" or kind == "cross":
            pass  # no gate; just close
        elif kind in ("slice", "phase"):
            _apply_review_gate(repo_root, item, qid, kind, reviewer_chain, skip_review_gate)
        else:
            raise CommandError(f"cannot close {kind} {qid}")
        if kind == "slice" and getattr(item, "started", None) is None:
            if not allow_ready_close:
                raise CommandError(f"{qid} must be started before close; run `tasktool start {qid}` first")
            _apply_ready_close_override(qid, item, reason=reason)
        item.status = Status.DONE
        item.closed = closed_date or _today()
        if refs:
            for r in refs:
                if r not in item.refs:
                    item.refs.append(r)
        if note:
            item.notes = (item.notes + "\n" + note).strip() if item.notes else note
        _save(write_root, p)
        _notify_status(qid=qid, kind=kind, status=item.status, title=item.title)

def cmd_block(*, repo_root: Path, slice_id: str, on: str) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        if not is_slice_id(slice_id):
            raise CommandError(f"block only works on slices; {slice_id} is a {kind_of(slice_id)}")
        _qid, _container, item = _find_item(p, slice_id)
        if on.startswith("external:"):
            item.blocked_on = BlockedOn(kind="external", value=on[len("external:"):])
        else:
            parse_id(on)  # validate
            item.blocked_on = BlockedOn(kind="id", value=on)
        item.status = Status.BLOCKED
        _save(write_root, p)
        _notify_status(qid=_qid, kind="slice", status=item.status, title=item.title)

def cmd_unblock(*, repo_root: Path, slice_id: str, resume: bool = False) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        if not is_slice_id(slice_id):
            raise CommandError(f"unblock only works on slices; {slice_id} is a {kind_of(slice_id)}")
        _qid, _container, item = _find_item(p, slice_id)
        item.blocked_on = None
        if resume:
            _start_item(_qid, item, resume=True)
        else:
            item.status = Status.READY
        _save(write_root, p)
        _notify_status(qid=_qid, kind="slice", status=item.status, title=item.title)

def cmd_deps(
    *, repo_root: Path, slice_id: str,
    add: str | None = None, remove: str | None = None,
) -> None:
    if (add is None) == (remove is None):
        raise CommandError("cmd_deps requires exactly one of add/remove")
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, slice_id)
        if parse_id(qid)[0] != "slice":
            raise CommandError(f"deps only works on slices; {qid} is a {parse_id(qid)[0]}")
        dep = _resolve_dependency_id(p, add or remove or "")
        if add is not None and dep not in item.depends_on:
            item.depends_on.append(dep)
        elif remove is not None and dep in item.depends_on:
            item.depends_on.remove(dep)
        _save(write_root, p)

def cmd_ratify(
    *, repo_root: Path, slice_id: str,
    status: str = "ratified", parallel_group: str | None = None,
) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, slice_id)
        if parse_id(qid)[0] != "slice":
            raise CommandError(f"ratify only works on slices; {qid} is a {parse_id(qid)[0]}")
        item.planning_status = PlanningStatus(status)
        if parallel_group is not None:
            item.parallel_group = parallel_group or None
        _save(write_root, p)

def cmd_phase_planning_path(*, repo_root: Path, phase_id: str, path: str | None) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, phase_id)
        if parse_id(qid)[0] != "phase":
            raise CommandError(f"planning-path only works on phases; {qid} is a {parse_id(qid)[0]}")
        item.planning_path = path
        _save(write_root, p)

# ───── note / ref / title ─────

def cmd_note(
    *, repo_root: Path, id: str,
    append: str | None = None, replace: str | None = None,
) -> None:
    if (append is None) == (replace is None):
        raise CommandError("cmd_note requires exactly one of append/replace")
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        _qid, _container, item = _find_item(p, id)
        if append is not None:
            item.notes = (item.notes + "\n" + append).strip() if item.notes else append
        else:
            item.notes = replace or ""
        _save(write_root, p)

def cmd_ref(
    *, repo_root: Path, id: str,
    add: str | None = None, remove: str | None = None,
) -> None:
    if (add is None) == (remove is None):
        raise CommandError("cmd_ref requires exactly one of add/remove")
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        if not hasattr(item, "refs"):
            raise CommandError(f"{qid}: this item kind does not have refs")
        if add is not None and add not in item.refs:
            item.refs.append(add)
        elif remove is not None and remove in item.refs:
            item.refs.remove(remove)
        _save(write_root, p)

def cmd_title(*, repo_root: Path, id: str, new: str) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        _qid, _container, item = _find_item(p, id)
        item.title = new
        _save(write_root, p)

# ───── show / list / next-id ─────

def _item_one_line(prefix: str, item) -> str:
    status_tag = item.status.value
    return f"{prefix}  [{status_tag}]  {item.title}"

def cmd_show(*, repo_root: Path, id: str) -> str:
    p = _load(repo_root)
    qid, _container, item = _find_item(p, id)
    lines = [f"# {qid} — {item.title}", f"status: {item.status.value}"]
    if getattr(item, "started", None):
        lines.append(f"started: {item.started}")
    if getattr(item, "closed", None):
        lines.append(f"closed: {item.closed}")
    if getattr(item, "blocked_on", None):
        bo = item.blocked_on
        lines.append(f"blocked_on: {bo.kind}:{bo.value}")
    if getattr(item, "depends_on", None):
        lines.append("depends_on:")
        for dep in item.depends_on:
            lines.append(f"  - {dep}")
    if getattr(item, "planning_status", None):
        lines.append(f"planning_status: {item.planning_status.value}")
    if getattr(item, "parallel_group", None):
        lines.append(f"parallel_group: {item.parallel_group}")
    if getattr(item, "planning_path", None):
        lines.append(f"planning_path: {item.planning_path}")
    if getattr(item, "refs", None):
        lines.append("refs:")
        for r in item.refs:
            lines.append(f"  - {r}")
    if getattr(item, "notes", ""):
        lines.append(f"notes:\n{item.notes}")
    # children
    if hasattr(item, "slices"):
        lines.append("\nSlices:")
        for s in item.slices:
            lines.append(_item_one_line(f"  {s.id}", s))
    if hasattr(item, "tasks"):
        lines.append("\nTasks:")
        for t in item.tasks:
            lines.append(_item_one_line(f"  {t.id}", t))
    return "\n".join(lines) + "\n"

def _phase_by_id(p: Project, phase_id: str) -> Phase:
    phase = next((ph for ph in p.phases if ph.id == phase_id), None)
    if phase is None:
        raise CommandError(f"phase {phase_id} not found")
    return phase

def _done_slice_ids(phase: Phase) -> set[str]:
    return {f"{phase.id}.{s.id}" for s in phase.slices if s.status == Status.DONE}

def _is_slice_ready_for_work(phase: Phase, s: Slice) -> bool:
    if s.status in (Status.DONE, Status.BLOCKED):
        return False
    if s.planning_status == PlanningStatus.SUPERSEDED:
        return False
    return all(dep in _done_slice_ids(phase) for dep in s.depends_on)

def cmd_ready_slices(*, repo_root: Path, phase_id: str, format: str = "text") -> str:
    p = _load(repo_root)
    phase = _phase_by_id(p, phase_id)
    rows = [
        {
            "id": f"{phase.id}.{s.id}",
            "status": s.status.value,
            "planning_status": s.planning_status.value,
            "parallel_group": s.parallel_group,
            "title": s.title,
        }
        for s in phase.slices
        if _is_slice_ready_for_work(phase, s)
    ]
    if format == "json":
        import json as _j
        return _j.dumps(rows, indent=2) + "\n"
    return "".join(
        f"{r['id']}  [{r['status']}/{r['planning_status']}]  "
        f"{r['parallel_group'] or '-'}  {r['title']}\n"
        for r in rows
    )

def cmd_schedule(*, repo_root: Path, phase_id: str, format: str = "text") -> str:
    p = _load(repo_root)
    phase = _phase_by_id(p, phase_id)
    done = _done_slice_ids(phase)
    rows = []
    for s in phase.slices:
        waiting_on = [dep for dep in s.depends_on if dep not in done]
        ready = _is_slice_ready_for_work(phase, s)
        rows.append({
            "id": f"{phase.id}.{s.id}",
            "status": s.status.value,
            "planning_status": s.planning_status.value,
            "parallel_group": s.parallel_group,
            "depends_on": s.depends_on,
            "waiting_on": waiting_on,
            "ready": ready,
            "title": s.title,
        })
    if format == "json":
        import json as _j
        return _j.dumps(rows, indent=2) + "\n"
    lines = [f"# {phase.id} — {phase.title}", ""]
    if phase.planning_path:
        lines.append(f"planning: {phase.planning_path}")
    for row in rows:
        ready = "ready" if row["ready"] else "waiting"
        deps = ", ".join(row["depends_on"]) if row["depends_on"] else "-"
        waits = ", ".join(row["waiting_on"]) if row["waiting_on"] else "-"
        group = row["parallel_group"] or "-"
        lines.append(
            f"{row['id']}  [{row['status']}/{row['planning_status']}]  "
            f"group={group}  {ready}  deps={deps}  waiting_on={waits}  {row['title']}"
        )
    return "\n".join(lines).rstrip() + "\n"

def cmd_phase_status(*, repo_root: Path, recent: int = 3, format: str = "text") -> str:
    p = _load(repo_root)
    open_cross = [c for c in p.cross_cutting if c.status != Status.DONE]
    open_phases = [ph for ph in p.phases if ph.status != Status.DONE]
    archived = p.archived_phases[-recent:] if recent > 0 else []
    if format == "json":
        import json as _j
        return _j.dumps({
            "project": p.project,
            "last_reviewed": p.last_reviewed,
            "open_phases": [
                {"id": ph.id, "status": ph.status.value, "title": ph.title}
                for ph in open_phases
            ],
            "open_cross_cutting": [
                {"id": c.id, "status": c.status.value, "title": c.title}
                for c in open_cross
            ],
            "recent_archived_phases": [
                {"id": a.id, "title": a.title, "archived_date": a.archived_date,
                 "archived_path": a.archived_path}
                for a in archived
            ],
        }, indent=2) + "\n"
    lines = [f"# {p.project} status"]
    if p.last_reviewed:
        lines.append(f"last_reviewed: {p.last_reviewed}")
    lines += ["", "Open phases:"]
    lines.extend(
        f"  {ph.id}  [{ph.status.value}]  {ph.title}" for ph in open_phases
    )
    if not open_phases:
        lines.append("  none")
    lines += ["", "Open cross-cutting:"]
    lines.extend(
        f"  {c.id}  [{c.status.value}]  {c.title}" for c in open_cross
    )
    if not open_cross:
        lines.append("  none")
    lines += ["", f"Recent archived phases ({len(archived)}):"]
    lines.extend(
        f"  {a.id}  [{a.archived_date}]  {a.title}  {a.archived_path}"
        for a in archived
    )
    if not archived:
        lines.append("  none")
    return "\n".join(lines) + "\n"

def _iter_items(p: Project):
    for ph in p.phases:
        yield ("phase", ph.id, ph)
        for s in ph.slices:
            yield ("slice", f"{ph.id}.{s.id}", s)
            for t in s.tasks:
                yield ("task", f"{ph.id}.{s.id}.{t.id}", t)
    for c in p.cross_cutting:
        yield ("cross", c.id, c)

def cmd_list(
    *, repo_root: Path,
    phase: str | None = None,
    status: list[str] | None = None,
    kind: str | None = None,
    open_only: bool = False,
    format: str = "text",
) -> str:
    p = _load(repo_root)
    if open_only:
        status_filter = {"ready", "in_progress", "blocked"}
    elif status:
        status_filter = set(status)
    else:
        status_filter = None
    rows: list[tuple[str, str, str, str]] = []
    for item_kind, qid, item in _iter_items(p):
        if phase and not qid.startswith(phase):
            continue
        if kind and item_kind != kind:
            continue
        if status_filter and item.status.value not in status_filter:
            continue
        rows.append((qid, item_kind, item.status.value, item.title))
    if format == "json":
        import json as _j
        return _j.dumps(
            [{"id": q, "kind": k, "status": s, "title": t} for q, k, s, t in rows],
            indent=2,
        )
    return "\n".join(f"{q}  [{s}]  {k:5}  {t}" for q, k, s, t in rows) + "\n"

def cmd_next_id(
    *, repo_root: Path, kind: str,
    phase: str | None = None, slice: str | None = None,
) -> str:
    p = _load(repo_root)
    if kind == "phase":
        return next_phase_id(p, repo_root)
    if kind == "slice":
        if not phase:
            raise CommandError("next-id slice requires --phase")
        return next_slice_id(p, phase, repo_root)
    if kind == "task":
        if not phase or not slice:
            raise CommandError("next-id task requires --phase and --slice")
        return next_task_id(p, phase, slice)
    if kind == "cross":
        return next_cross_id(p, repo_root)
    raise CommandError(f"unknown kind {kind}")

# ───── validate / schema ─────

def cmd_validate(
    *, repo_root: Path,
    format: str = "text",
    strict_format: bool = False,
    normalise: bool = False,
    check_orphans: list[str] | None = None,
    no_path_warnings: bool = False,
) -> tuple[int, str]:
    if normalise:
        with _write_context(repo_root) as write_root:
            return _cmd_validate_at_root(
                repo_root=write_root,
                format=format,
                strict_format=strict_format,
                normalise=normalise,
                check_orphans=check_orphans,
                no_path_warnings=no_path_warnings,
            )
    return _cmd_validate_at_root(
        repo_root=repo_root,
        format=format,
        strict_format=strict_format,
        normalise=normalise,
        check_orphans=check_orphans,
        no_path_warnings=no_path_warnings,
    )

def _cmd_validate_at_root(
    *, repo_root: Path,
    format: str,
    strict_format: bool,
    normalise: bool,
    check_orphans: list[str] | None,
    no_path_warnings: bool = False,
) -> tuple[int, str]:
    from tasktool.validate import (
        validate_project, ValidationError, strict_format_check, normalise_file,
        find_path_warnings, validate_orphan_filenames,
    )
    path = _tasklist_path(repo_root)
    if not path.exists():
        return 1, f"{path}: not found"
    errors: list[str] = []
    warnings: list[str] = []
    project: Project | None = None
    try:
        project = load_project(path)
        validate_project(project)
    except (ValidationError, ValueError) as e:
        errors.append(str(e))
    if project is not None and not errors:
        if not no_path_warnings:
            warnings.extend(find_path_warnings(project, repo_root))
        if check_orphans:
            errors.extend(validate_orphan_filenames(project, check_orphans))
    if normalise and not errors:
        try:
            normalise_file(path)
        except ValidationError as e:
            errors.append(str(e))
    if strict_format and not errors:
        try:
            strict_format_check(path)
        except ValidationError as e:
            errors.append(str(e))
    rc = 0 if not errors else 1
    if format == "json":
        import json as _j
        return rc, _j.dumps({"ok": rc == 0, "errors": errors, "warnings": warnings}, indent=2)
    parts: list[str] = []
    if warnings:
        parts.extend(f"warning: {w}" for w in warnings)
    if errors:
        parts.extend(errors)
    elif not warnings:
        parts.append("ok")
    return rc, "\n".join(parts) + "\n"

def cmd_import(
    *, repo_root: Path, md_path: Path,
    dry_run: bool = False, force: bool = False, project: str | None = None,
) -> tuple[int, str, str]:
    """Import a TASKLIST.md markdown file into docs/tasklist.json.
    Returns (rc, stdout, stderr_warnings)."""
    from tasktool.importer import parse_tasklist_md
    from tasktool.serialize import dumps_canonical
    text = md_path.read_text(encoding="utf-8")
    result = parse_tasklist_md(text)
    if project:
        result.project.project = project
    elif result.project.project == "<imported>":
        result.project.project = repo_root.name
    result.project.last_reviewed = _today()
    warnings_text = "\n".join(result.warnings)
    if dry_run:
        return 0, dumps_canonical(result.project), warnings_text
    with _write_context(repo_root) as write_root:
        target = _tasklist_path(write_root)
        if target.exists() and not force:
            raise CommandError(f"{target}: already exists. Pass --force to overwrite.")
        target.parent.mkdir(parents=True, exist_ok=True)
        _save(write_root, result.project)
        return 0, f"wrote {target}\n", warnings_text

def cmd_render(*, repo_root: Path, format: str = "markdown") -> str:
    from tasktool.render import render_project
    if format != "markdown":
        raise CommandError(f"render: unsupported format {format!r} (only 'markdown' for S2)")
    return render_project(_load(repo_root))

def cmd_schema() -> str:
    from tasktool.schema_gen import dump_schema
    return dump_schema()

import re as _re

def _slugify(text: str) -> str:
    s = _re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:40] or "phase"

def cmd_archive_phase(
    *, repo_root: Path, phase_id: str,
    reviewer_chain: Path | None = None, skip_review_gate: bool = False,
) -> None:
    """Archive a completed phase. Per spec §7.3/§8.2:
    refuses if any slice is not done; applies post-phase review gate; writes
    docs/archived-tasks/<pid>-<slug>.md containing a summary + canonical JSON;
    moves phase from project.phases to project.archived_phases."""
    with _write_context(repo_root) as write_root:
        _cmd_archive_phase_at_root(
            invocation_root=repo_root,
            write_root=write_root,
            phase_id=phase_id,
            reviewer_chain=reviewer_chain,
            skip_review_gate=skip_review_gate,
        )

def _cmd_archive_phase_at_root(
    *,
    invocation_root: Path,
    write_root: Path,
    phase_id: str,
    reviewer_chain: Path | None,
    skip_review_gate: bool,
) -> None:
    """Archive a completed phase after the caller has selected the write root."""
    import sys as _sys
    from tasktool.model import ArchivedPhase
    from tasktool.serialize import dumps_canonical

    p = _load(write_root)
    phase = next((ph for ph in p.phases if ph.id == phase_id), None)
    if phase is None:
        raise CommandError(f"phase {phase_id} not found")
    open_slices = [s.id for s in phase.slices if s.status != Status.DONE]
    if open_slices:
        raise CommandError(
            f"phase {phase_id} has open slices: {', '.join(open_slices)}"
        )
    if skip_review_gate:
        print(f"warning: review gate skipped for {phase_id}", file=_sys.stderr)
    _apply_review_gate(invocation_root, phase, phase_id, "phase",
                       reviewer_chain, skip_review_gate)
    if phase.status != Status.DONE:
        phase.status = Status.DONE
        phase.closed = phase.closed or _today()

    slug = _slugify(phase.title)
    archive_rel = f"docs/archived-tasks/{phase_id}-{slug}.md"
    archive_path = write_root / archive_rel

    # Build archive content in memory (no disk side effects yet).
    sub_project = Project(project=p.project)
    sub_project.phases.append(phase)
    phase_json = dumps_canonical(sub_project)
    summary_lines = [f"# {phase_id} — {phase.title}", "", f"status: {phase.status.value}"]
    if phase.closed:
        summary_lines.append(f"closed: {phase.closed}")
    if phase.spec_path:
        summary_lines.append(f"spec: {phase.spec_path}")
    if phase.plan_path:
        summary_lines.append(f"plan: {phase.plan_path}")
    if phase.planning_path:
        summary_lines.append(f"planning: {phase.planning_path}")
    summary_lines += ["", "## Slices", ""]
    for s in phase.slices:
        closed = f" — closed {s.closed}" if s.closed else ""
        deps = f" — depends on {', '.join(s.depends_on)}" if s.depends_on else ""
        summary_lines.append(
            f"- **{s.id}** [{s.status.value}/{s.planning_status.value}]"
            f"{closed}{deps} — {s.title}"
        )
    summary_lines += [
        "",
        "## Full phase JSON (for tasktool unarchive)",
        "",
        "```json",
        phase_json.rstrip(),
        "```",
        "",
    ]
    summary_text = "\n".join(summary_lines)

    # Mutate project state.
    p.phases = [ph for ph in p.phases if ph.id != phase_id]
    p.archived_phases.append(ArchivedPhase(
        id=phase_id, title=phase.title,
        archived_path=archive_rel, archived_date=_today(),
    ))
    # Validate BEFORE any filesystem writes so a bad state aborts cleanly.
    validate_project(p)
    # Now write.
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(summary_text, encoding="utf-8")
    _save(write_root, p)
    _git_stage(write_root, archive_path)
    _notify_status(qid=phase_id, kind="phase", status=Status.DONE, title=phase.title)

def cmd_brief(*, repo_root: Path, id: str) -> str:
    from tasktool.brief import brief as _brief
    p = _load(repo_root)
    qid = _resolve_id(p, id)
    return _brief(p, qid)
