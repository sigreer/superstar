# tools/tasktool/commands.py
from __future__ import annotations
import datetime as _dt
import json as _json
import os as _os
import sys
import subprocess as _subprocess
from contextlib import contextmanager
from dataclasses import asdict as _asdict
from pathlib import Path
from tasktool.config import (
    TasklistConfig,
    TasktoolConfig,
    is_authoritative_required,
    load_config,
    save_config,
)
from tasktool.model import (
    ArchivedCrossCutting,
    Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status, PlanningStatus,
    SliceWorkflowStep, PhaseWorkflowStep, ReviewStage,
    is_terminal,
)
from tasktool.serialize import load_project, save_project
from tasktool.validate import validate_project
from tasktool.allocate import (
    next_phase_id, next_slice_id, next_task_id, next_cross_id, next_followup_letter,
)
from tasktool.artifacts import (
    ArtifactError,
    ArtifactKind,
    ArtifactProblem,
    NormalizedArtifact,
    add_artifact_to_item,
    artifact_kind_for_path,
    artifact_status_baseline_paths,
    disallowed_staged_paths,
    git_status_map,
    normalize_artifact_path,
    referenced_path_is_unstaged,
    referenced_paths_for_archives,
    referenced_paths_for_item,
    render_status_json,
    render_status_text,
    same_slug_orphans,
    workflow_files,
)
from tasktool.ids import split_qualified, kind_of, is_slice_id, parse_id
from tasktool.migrate import apply_deltas, compute_deltas, render_diff
from tasktool.reviewer_gate import check_gate, GateError, GatePass
from tasktool.notify import (
    notify_tasktool_artifact,
    notify_tasktool_status,
    notify_tasktool_workflow_step,
)
from tasktool.worktree import (
    AuthorityError,
    find_authoritative_root,
    git_current_branch,
    same_repository,
    tasklist_has_unsafe_dirty_state,
    tasktool_lock,
    validate_authoritative_checkout,
)

class CommandError(RuntimeError):
    pass


class UsageError(CommandError):
    """Misuse of a tasktool command — invalid flag combination, unknown ID, etc.

    Inherits CommandError so cli.py's existing `except CommandError` clause
    catches it and emits the standard `tasktool: <msg>` line with exit code 1.
    """


def _validate_set_flags(
    *, id, status, workflow_step, clear_workflow_step,
    review_active, review_stage, reviewer_chain,
) -> None:
    mutating = any(
        x is not None
        for x in (status, workflow_step, review_active, review_stage, reviewer_chain)
    )
    mutating = mutating or clear_workflow_step
    if not mutating:
        raise UsageError("tasktool set: at least one mutating flag is required")
    if workflow_step is not None and clear_workflow_step:
        raise UsageError(
            "tasktool set: --workflow-step and --clear-workflow-step are mutually exclusive"
        )
    if review_active is False and review_stage is not None:
        raise UsageError(
            "tasktool set: --review-stage cannot be set when --review-active is false"
        )
    try:
        kind = kind_of(id)
    except Exception as exc:
        raise UsageError(f"tasktool set: invalid id {id!r}: {exc}") from exc
    # For qualified ids (P6.S1), kind_of via parse_id returns the kind of the
    # deepest level — that's what we want.
    if (review_active is not None or review_stage is not None) and kind != "slice":
        raise UsageError(
            "tasktool set: --review-active / --review-stage are review flags "
            "only valid on slice rows"
        )
    if workflow_step is not None:
        if kind == "slice" and workflow_step not in {"spec", "plan", "implement", "done"}:
            raise UsageError(
                f"tasktool set: workflow_step {workflow_step!r} not valid for slice rows"
            )
        if kind == "phase" and workflow_step not in {"spec", "ready", "in_progress", "done"}:
            raise UsageError(
                f"tasktool set: workflow_step {workflow_step!r} not valid for phase rows"
            )
        if kind == "cross":
            raise UsageError(
                "tasktool set: --workflow-step is not valid for cross-cutting rows"
            )
        if kind == "task":
            raise UsageError(
                "tasktool set: --workflow-step is not valid for task rows"
            )


def _refuse_if_cancelled(qid: str, item, command: str) -> None:
    """Refuse a lifecycle command if the row is in CANCELLED status."""
    if item.status == Status.CANCELLED:
        hint = " — use note --append" if command == "replace notes" else ""
        raise CommandError(
            f"{qid}: cannot {command} a cancelled row{hint}"
        )

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

def _git_stage_rel(repo_root: Path, rel: str) -> None:
    if not STAGE_AFTER_WRITE:
        return
    try:
        _subprocess.run(
            ["git", "add", "--", rel],
            cwd=repo_root,
            check=False,
            stdout=_subprocess.DEVNULL,
            stderr=_subprocess.DEVNULL,
        )
    except OSError:
        pass

def _today() -> str:
    return _dt.date.today().isoformat()

def _tasklist_path(repo_root: Path) -> Path:
    return repo_root / DEFAULT_JSON_REL

def _ensure_authoritative_tasklist_clean(repo_root: Path) -> None:
    if tasklist_has_unsafe_dirty_state(repo_root):
        raise CommandError(
            "authoritative docs/tasklist.json has unstaged changes; "
            "commit, stash, or normalise them before running tasktool"
        )

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

def _notify_artifact(
    *, qid: str, kind: str, artifact_kind: ArtifactKind, title: str
) -> None:
    if artifact_kind not in {ArtifactKind.SPEC, ArtifactKind.PLAN}:
        return
    try:
        notify_tasktool_artifact(
            work_id=qid,
            kind=kind,
            artifact_kind=artifact_kind.value,
            title=title,
        )
    except Exception:
        pass

def _notify_workflow_step(*, qid: str, kind: str, step: str, title: str) -> None:
    try:
        notify_tasktool_workflow_step(
            work_id=qid,
            kind=kind,
            step=step,
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
def _read_context(repo_root: Path):
    """Read-only equivalent of `_write_context`.

    Resolves the authoritative checkout for read purposes without acquiring
    `.git/tasktool.lock` or enforcing authoritative cleanliness. Use this for
    commands that only inspect state (e.g. `worktree list`, `worktree status`).
    """
    write_root, _routed, mode, authoritative_branch = _resolve_write_root(repo_root)
    if mode == "authoritative-checkout":
        try:
            validate_authoritative_checkout(
                write_root,
                expected_branch=authoritative_branch,
                caller_root=repo_root,
            )
        except AuthorityError as exc:
            raise CommandError(str(exc)) from exc
    yield write_root


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
                _ensure_authoritative_tasklist_clean(write_root)
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

def cmd_config_init_local(*, repo_root: Path) -> None:
    cfg = load_config(repo_root)
    if cfg.tasklist.mutation_mode == "local":
        return
    if cfg.tasklist.mutation_mode == "authoritative-checkout":
        raise CommandError(
            "tasktool is already configured for authoritative-checkout; "
            "refusing to overwrite with local mode"
        )
    cfg = TasktoolConfig(
        tasklist=TasklistConfig(
            mutation_mode="local",
            authoritative_branch=cfg.tasklist.authoritative_branch,
        )
    )
    save_config(repo_root, cfg)
    _git_stage(repo_root, repo_root / ".tasktool" / "config.json")
    print(
        "tasktool: configured local mutation mode; worktree-side mutations will not be routed.",
        file=sys.stderr,
    )

def _git_root(path: Path) -> Path:
    try:
        out = _subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
    except _subprocess.CalledProcessError as exc:
        raise CommandError(f"not a git checkout: {path}") from exc
    return Path(out).resolve()

def _resolve_root_arg(base_root: Path, raw: Path | None) -> Path:
    if raw is None:
        return _git_root(base_root)
    candidate = raw.expanduser()
    if not candidate.is_absolute():
        candidate = base_root / candidate
    return _git_root(candidate.resolve())

def _iter_project_rows(p: Project):
    yield "<project>", "project", p.project, p
    for phase in p.phases:
        yield phase.id, "phase", phase.title, phase
        for slc in phase.slices:
            slice_qid = f"{phase.id}.{slc.id}"
            yield slice_qid, "slice", slc.title, slc
            for task in slc.tasks:
                yield f"{slice_qid}.{task.id}", "task", task.title, task
    for item in p.cross_cutting:
        yield item.id, "cross", item.title, item

def _notify_migrated_status_transitions(authoritative: Project, row_ids: set[str]) -> None:
    for qid, kind, title, item in _iter_project_rows(authoritative):
        if qid in row_ids and hasattr(item, "status"):
            _notify_status(qid=qid, kind=kind, status=item.status, title=title)

def cmd_config_migrate_from_local(
    *,
    repo_root: Path,
    authority_root: Path | None,
    local_root: Path | None = None,
    dry_run: bool = False,
    accept_local: bool = False,
    accept_authoritative: bool = False,
    stdin_is_tty: bool = False,
) -> None:
    if authority_root is None:
        raise CommandError("migrate-from-local requires --authority-root <path>")
    if accept_local and accept_authoritative:
        raise CommandError("migrate-from-local accepts only one policy flag")

    authority = _resolve_root_arg(repo_root, authority_root)
    local = _resolve_root_arg(repo_root, local_root)
    if not same_repository(authority, local):
        raise CommandError("authority root and local root are not the same repository")

    cfg = load_config(authority)
    config_path = authority / ".tasktool" / "config.json"
    needs_config = is_authoritative_required(cfg)
    expected_branch = cfg.tasklist.authoritative_branch
    if needs_config:
        expected_branch = git_current_branch(authority)
        if not expected_branch:
            raise CommandError("authority checkout must be on a branch")

    try:
        validate_authoritative_checkout(
            authority,
            expected_branch=expected_branch,
            caller_root=local,
        )
    except AuthorityError as exc:
        raise CommandError(str(exc)) from exc

    _ensure_authoritative_tasklist_clean(authority)

    local_project = _load(local)
    authoritative_project = _load(authority)
    deltas, conflicts = compute_deltas(local_project, authoritative_project)
    if not deltas and not conflicts:
        print("no drift detected")
        return

    diff_text = render_diff(deltas, conflicts)
    sys.stdout.write(diff_text)
    if dry_run:
        return
    if not accept_local and not accept_authoritative:
        if not stdin_is_tty:
            raise CommandError(
                "migrate-from-local requires one of --accept-local or "
                "--accept-authoritative in non-interactive contexts"
            )
        choice = input("Accept local, authoritative, or abort? [local/authoritative/abort] ").strip().lower()
        if choice == "local":
            accept_local = True
        elif choice == "authoritative":
            accept_authoritative = True
        else:
            raise CommandError("migrate-from-local aborted")
    if accept_authoritative:
        try:
            with tasktool_lock(authority):
                _ensure_authoritative_tasklist_clean(authority)
                authoritative_project = _load(authority)
                compute_deltas(local_project, authoritative_project)
        except AuthorityError as exc:
            raise CommandError(str(exc)) from exc
        print(
            f"accepted authoritative tasklist; migrated 0 rows "
            f"(0 status transitions) to {authority}"
        )
        return

    status_transition_rows: set[str] = set()
    migrated_rows: set[str] = set()
    try:
        with tasktool_lock(authority):
            _ensure_authoritative_tasklist_clean(authority)
            authoritative_project = _load(authority)
            deltas, conflicts = compute_deltas(local_project, authoritative_project)
            status_transition_rows = {
                delta.row_id
                for delta in deltas
                if delta.kind == "field" and delta.field == "status"
            }
            migrated_rows = {delta.row_id for delta in deltas}
            merged = apply_deltas(
                authoritative=authoritative_project,
                local=local_project,
                deltas=deltas,
                conflicts=conflicts,
                policy="accept-local",
            )
            _save(authority, merged)
            if needs_config:
                save_config(
                    authority,
                    TasktoolConfig(
                        tasklist=TasklistConfig(
                            mutation_mode="authoritative-checkout",
                            authoritative_branch=expected_branch,
                        )
                    ),
                )
                _git_stage(authority, config_path)
            _notify_migrated_status_transitions(merged, status_transition_rows)
    except AuthorityError as exc:
        raise CommandError(str(exc)) from exc

    print(
        f"migrated {len(migrated_rows)} rows "
        f"({len(status_transition_rows)} status transitions) to {authority}"
    )

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
        if any(a.id == qid for a in p.archived_cross_cutting):
            raise CommandError(
                f"cross-cutting {qid} not found in active tasklist; it may already be archived"
            )
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
    if is_terminal(item.status):
        raise CommandError(f"{qid} is already {item.status.value}")
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

def _archive_cross_at_root(
    write_root: Path,
    p: Project,
    item: CrossCutting,
) -> tuple[Path, str]:
    if not is_terminal(item.status):
        raise CommandError(
            f"cross-cutting {item.id} must be done before archive; run tasktool close {item.id} first"
        )
    if any(a.id == item.id for a in p.archived_cross_cutting):
        raise CommandError(f"cross-cutting {item.id} is already archived")

    slug = _slugify(item.title)
    archive_rel = f"docs/archived-tasks/{item.id}-{slug}.md"
    archive_path = write_root / archive_rel
    if archive_path.exists():
        raise CommandError(f"archive path already exists: {archive_rel}")

    def _coerce_cross_json(node):
        if isinstance(node, Status):
            return node.value
        if isinstance(node, dict):
            return {key: _coerce_cross_json(value) for key, value in node.items()}
        if isinstance(node, list):
            return [_coerce_cross_json(value) for value in node]
        return node

    cross_json = _json.dumps(
        _coerce_cross_json(_asdict(item)),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"
    summary_lines = [
        f"# {item.id} - {item.title}",
        "",
        f"status: {item.status.value}",
        f"created: {item.created}",
    ]
    if item.started:
        summary_lines.append(f"started: {item.started}")
    if item.closed:
        summary_lines.append(f"closed: {item.closed}")
    if item.refs:
        summary_lines += ["", "## References", ""]
        summary_lines.extend(f"- {ref}" for ref in item.refs)
    if item.notes:
        summary_lines += ["", "## Notes", "", item.notes]
    summary_lines += [
        "",
        "## Full cross-cutting JSON (for tasktool unarchive)",
        "",
        "```json",
        cross_json.rstrip(),
        "```",
        "",
    ]

    p.cross_cutting = [cross for cross in p.cross_cutting if cross.id != item.id]
    p.archived_cross_cutting.append(
        ArchivedCrossCutting(
            id=item.id,
            title=item.title,
            archived_path=archive_rel,
            archived_date=_today(),
        )
    )
    validate_project(p)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text("\n".join(summary_lines), encoding="utf-8")
    return archive_path, archive_rel

_SUBAGENT_REFUSAL = (
    "Subagents must inherit the parent's worktree; call the parent or "
    "'cd' into the existing recorded path: {worktree_path}."
)


def _subagent_signal() -> str | None:
    """Return the name of the first env signal indicating dispatched-subagent
    status, in precedence order, or None if no signal is present.

    Precedence (spec §5.3):
      1. SUPERSTAR_SUBAGENT_ROLE  -- any non-empty value
      2. CLAUDE_AGENT_ROLE        -- any value other than 'coordinator' / 'main'
      3. SUPERSTAR_FORCE_SUBAGENT -- value == '1' (test-only override)

    No fingerprinting fallback. Absence of all three signals = not a subagent.
    """
    role = _os.environ.get("SUPERSTAR_SUBAGENT_ROLE", "")
    if role.strip():
        return "SUPERSTAR_SUBAGENT_ROLE"
    claude_role = _os.environ.get("CLAUDE_AGENT_ROLE", "").strip().lower()
    if claude_role and claude_role not in {"coordinator", "main"}:
        return "CLAUDE_AGENT_ROLE"
    if _os.environ.get("SUPERSTAR_FORCE_SUBAGENT", "") == "1":
        return "SUPERSTAR_FORCE_SUBAGENT"
    return None


def _lookup_worktree_path_for_refusal(repo_root: Path, id: str | None) -> str:
    """Best-effort lookup of the slice's recorded worktree_path for inclusion
    in the subagent refusal message. Never raises; returns '<not recorded>' on
    any failure."""
    if not id:
        return "<not recorded>"
    try:
        with _write_context(repo_root) as write_root:
            p = _load(write_root)
            _qid, _container, item = _find_item(p, id)
            return getattr(item, "worktree_path", None) or "<not recorded>"
    except Exception:
        return "<not recorded>"


def cmd_start(
    *,
    repo_root: Path,
    id: str,
    resume: bool = False,
    in_place: bool = False,
    adopt: str | None = None,
    ad_hoc: str | None = None,
) -> None:
    signal = _subagent_signal()
    if signal is not None:
        worktree_path = _lookup_worktree_path_for_refusal(repo_root, id)
        raise CommandError(
            _SUBAGENT_REFUSAL.format(worktree_path=worktree_path)
            + f" [signal: {signal}]"
        )
    if ad_hoc is not None:
        # Reject a positional id alongside --ad-hoc at the command layer too,
        # so the rejection holds even when callers reach cmd_start without going
        # through the CLI dispatcher (e.g. direct Python imports in tests).
        if id is not None:
            raise CommandError("--ad-hoc does not accept a positional id")
        if in_place or adopt is not None:
            raise CommandError("--ad-hoc is mutually exclusive with --in-place and --adopt")
        # Allocate a fresh X<n> cross-cutting row and create its worktree.
        _start_ad_hoc(repo_root=repo_root, slug=ad_hoc)
        return
    if in_place and adopt is not None:
        raise CommandError("--in-place and --adopt are mutually exclusive")
    # Auto-adopt: when invoked from inside a linked worktree of this repo, the
    # tasklist write must hit the main checkout's docs/tasklist.json (in local
    # mode) or be routed normally (in authoritative-checkout mode). Capture the
    # linked-worktree path so we can record it as the adopted path below, then
    # retarget `repo_root` to the main checkout for `_write_context`.
    from tasktool.worktree_lifecycle import is_inside_linked_worktree
    auto_adopt_path: Path | None = None
    effective_root = repo_root
    if adopt is None and not in_place and ad_hoc is None and is_inside_linked_worktree(repo_root):
        auto_adopt_path = repo_root.resolve()
        # In local mode, _resolve_write_root would write to the linked worktree's
        # tasklist.json. Retarget to the main checkout (common-dir's parent) so
        # the slice row in the canonical tasklist gets the worktree fields. In
        # authoritative-checkout mode, _resolve_write_root already routes; do
        # not retarget there.
        try:
            cfg = load_config(repo_root)
            if cfg.tasklist.mutation_mode == "local":
                common = _subprocess.run(
                    ["git", "rev-parse", "--git-common-dir"], cwd=repo_root,
                    text=True, capture_output=True, check=True,
                ).stdout.strip()
                main_checkout = Path(common).resolve().parent
                effective_root = main_checkout
        except (_subprocess.CalledProcessError, Exception):
            pass
    with _write_context(effective_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        kind = parse_id(qid)[0]
        # ─── Lifecycle preflight FIRST. No git/worktree mutation may run if the
        # row is DONE, or BLOCKED without --resume. _preflight_start raises before
        # we touch the filesystem.
        _preflight_start(qid, item, resume=resume)
        if in_place:
            _apply_start_in_place(qid, item)
        else:
            adopt_path: Path | None = Path(adopt).expanduser().resolve() if adopt else None
            if adopt_path is None and auto_adopt_path is not None:
                adopt_path = auto_adopt_path
            if adopt_path is not None:
                _apply_start_adopt(write_root, qid, item, adopt_path)
            else:
                _apply_start_default(write_root, qid, item, resume=resume)
        # _start_item now only mutates status/blocked_on/started; refusals already
        # happened in _preflight_start, so this call cannot raise after side effects.
        _start_item(qid, item, resume=resume)
        _save(write_root, p)
        _notify_status(qid=qid, kind=kind, status=item.status, title=item.title)


def _preflight_start(qid: str, item, *, resume: bool) -> None:
    """Lifecycle refusals from `_start_item` lifted to run BEFORE any disk mutation.

    `_start_item` itself is kept unchanged so callers like `cmd_set` / `cmd_unblock`
    that don't touch worktrees continue to work; this preflight just runs the same
    checks earlier so the worktree branch of `cmd_start` can't leave dangling
    on-disk state after a refusal.
    """
    if item.status == Status.DONE:
        raise CommandError(f"{qid} is already done")
    if item.status == Status.BLOCKED and not resume:
        raise CommandError(f"{qid} is blocked; use start --resume to clear blocked_on")


def _start_ad_hoc(*, repo_root: Path, slug: str) -> None:
    slug = (slug or "").strip()
    if not slug:
        raise CommandError("--ad-hoc requires a non-empty <slug>")
    title = f"Ad-hoc: {slug}"
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        new_id = next_cross_id(p, write_root)
        item = CrossCutting(
            id=new_id, title=title, created=_today(),
            status=Status.IN_PROGRESS, started=_today(), notes="ad-hoc",
        )
        p.cross_cutting.append(item)
        _apply_start_default(write_root, new_id, item, resume=False)
        _save(write_root, p)
        _notify_status(qid=new_id, kind="cross", status=item.status, title=item.title)
        print(new_id)


def _apply_start_default(write_root: Path, qid: str, item, *, resume: bool) -> None:
    if item.worktree_in_place:
        # In-place slice; default start is a no-op on disk.
        return
    if not (write_root / ".git").exists():
        # No git repo (tests that pre-date P5.S1). Behave as pre-P5 start.
        return
    from tasktool.worktree_lifecycle import (
        RecordedState, classify_recorded_state, worktree_name,
    )
    name = worktree_name(qid, item.title)
    canonical_rel = f".worktrees/{name}"
    canonical_path = (write_root / canonical_rel).resolve()
    canonical_branch = name

    recorded_path = (write_root / item.worktree_path).resolve() if item.worktree_path else None
    state = classify_recorded_state(
        write_root, recorded_path=recorded_path, recorded_branch=item.worktree_branch,
    )
    if state == RecordedState.CONSISTENT:
        print(f"cd {recorded_path}")
        return
    if state == RecordedState.BOTH_MISSING:
        raise CommandError(
            f"{qid}: recorded worktree gone (path and branch missing); "
            f"run `tasktool worktree repair {qid}` (P5.S2) or re-record with `tasktool worktree adopt`."
        )
    if state == RecordedState.PATH_MISSING:
        raise CommandError(
            f"{qid}: recorded worktree path missing but branch {item.worktree_branch!r} still exists; "
            f"run `tasktool worktree adopt {qid} <new-path>` or `tasktool worktree repair {qid}` (P5.S2)."
        )
    if state == RecordedState.PATH_NOT_WORKTREE:
        raise CommandError(
            f"{qid}: recorded path {item.worktree_path!r} exists but is not a linked worktree. "
            f"Run `tasktool worktree prune {qid} --force` (P5.S2) then re-`start`."
        )
    if state == RecordedState.BRANCH_MISMATCH:
        raise CommandError(
            f"{qid}: linked worktree at {item.worktree_path!r} is on a different branch than "
            f"recorded ({item.worktree_branch!r}). Refusing to guess; resolve manually."
        )
    assert state == RecordedState.ABSENT
    # Fresh creation: refuse if canonical path or branch already exists out-of-band.
    if canonical_path.exists():
        raise CommandError(
            f"{qid}: canonical worktree path {canonical_rel!r} already exists outside tasktool. "
            f"Adopt with `tasktool worktree adopt {qid} {canonical_rel}` or remove it manually."
        )
    res = _subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{canonical_branch}"],
        cwd=write_root,
    )
    if res.returncode == 0:
        raise CommandError(
            f"{qid}: branch {canonical_branch!r} already exists out-of-band; "
            f"adopt the existing worktree or delete the branch."
        )
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    _subprocess.run(
        ["git", "worktree", "add", "-b", canonical_branch, str(canonical_path)],
        cwd=write_root, check=True, text=True, capture_output=True,
    )
    item.worktree_path = canonical_rel
    item.worktree_branch = canonical_branch
    item.worktree_in_place = False
    print(f"cd {canonical_path}")


def _apply_start_in_place(qid: str, item) -> None:
    if item.worktree_path is not None:
        raise CommandError(
            f"{qid}: --in-place refused; slice already has a recorded worktree at {item.worktree_path!r}."
        )
    item.worktree_in_place = True
    item.worktree_path = None
    item.worktree_branch = None


def _apply_start_adopt(write_root: Path, qid: str, item, adopt_path: Path) -> None:
    from tasktool.worktree_lifecycle import (
        is_authoritative_checkout, linked_worktree_branch,
    )
    if is_authoritative_checkout(write_root, adopt_path):
        raise CommandError(
            f"{qid}: --adopt refused; {adopt_path} is the main checkout, not a linked "
            f"worktree. Create a linked worktree first with `git worktree add` then "
            f"adopt that path."
        )
    branch = linked_worktree_branch(write_root, adopt_path)
    if branch is None:
        raise CommandError(
            f"{qid}: --adopt {adopt_path} is not a linked worktree of this repository."
        )
    try:
        rel = adopt_path.relative_to(write_root.resolve())
        rel_str = str(rel)
    except ValueError:
        rel_str = str(adopt_path)
    item.worktree_path = rel_str
    item.worktree_branch = branch
    item.worktree_in_place = False
    print(f"cd {adopt_path}")

def cmd_set(
    repo_root: Path | None = None,
    *,
    id: str,
    status: str | None = None,
    workflow_step: str | None = None,
    clear_workflow_step: bool = False,
    review_active: bool | None = None,
    review_stage: str | None = None,
    reviewer_chain: Path | None = None,
    skip_review_gate: bool = False,
    allow_ready_close: bool = False,
    reason: str | None = None,
) -> None:
    # Tolerate the historical positional/keyword `repo_root=` calling style: it
    # is required, but accepting it positionally lets the new tests call
    # `cmd_set(p, id=...)` (matches the plan spec) while old callers keep
    # working unchanged.
    if repo_root is None:
        raise TypeError("cmd_set: repo_root is required")
    _validate_set_flags(
        id=id, status=status, workflow_step=workflow_step,
        clear_workflow_step=clear_workflow_step,
        review_active=review_active, review_stage=review_stage,
        reviewer_chain=reviewer_chain,
    )
    if status == "cancelled":
        raise CommandError(
            f"{id}: cannot set status=cancelled directly; "
            f"use `tasktool cancel <id> --reason \"...\"`"
        )
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        _refuse_if_cancelled(qid, item, "set")
        kind = parse_id(qid)[0]
        workflow_step_notification: str | None = None

        if status is not None:
            new_status = Status(status)
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

        if workflow_step is not None:
            previous_step = getattr(item, "workflow_step", None)
            step_changed = previous_step is None or previous_step.value != workflow_step
            if kind == "slice":
                item.workflow_step = SliceWorkflowStep(workflow_step)
                # Step change clears the slice review block.
                item.review_active = False
                item.review_stage = None
            elif kind == "phase":
                item.workflow_step = PhaseWorkflowStep(workflow_step)
            if step_changed:
                workflow_step_notification = workflow_step
        elif clear_workflow_step:
            item.workflow_step = None
            if kind == "slice":
                item.review_active = False
                item.review_stage = None

        if review_active is not None and kind == "slice":
            item.review_active = bool(review_active)
            if not review_active:
                item.review_stage = None
        if review_stage is not None and kind == "slice":
            item.review_stage = ReviewStage(review_stage)

        _save(write_root, p)
        if workflow_step_notification is not None:
            _notify_workflow_step(
                qid=qid,
                kind=kind,
                step=workflow_step_notification,
                title=item.title,
            )
        if status is not None:
            _notify_status(qid=qid, kind=kind, status=item.status, title=item.title)

def cmd_close(
    *, repo_root: Path, id: str,
    refs: list[str] | None = None, closed_date: str | None = None,
    note: str | None = None,
    reviewer_chain: Path | None = None, skip_review_gate: bool = False,
    allow_ready_close: bool = False, reason: str | None = None,
    no_archive: bool = False,
) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        _refuse_if_cancelled(qid, item, "close")
        kind = parse_id(qid)[0]
        if no_archive and kind != "cross":
            raise CommandError("--no-archive is only valid for cross-cutting items")
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
        archive_path: Path | None = None
        if kind == "cross" and not no_archive:
            archive_path, _archive_rel = _archive_cross_at_root(write_root, p, item)
        _save(write_root, p)
        if archive_path is not None:
            _git_stage(write_root, archive_path)
        _notify_status(qid=qid, kind=kind, status=item.status, title=item.title)

def _stamp_cancellation(item, reason: str, *, suffix: str | None) -> None:
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    line = f"Cancelled {ts}: {reason}"
    if suffix:
        line += f" ({suffix})"
    item.notes = (item.notes + "\n" + line).strip() if item.notes else line
    item.status = Status.CANCELLED
    item.closed = _today()
    # Clear transient review state introduced by P6.S1 so cancelled rows
    # don't render with stale review block. workflow_step is left intact —
    # it records the furthest step the work reached, which is informative.
    if hasattr(item, "review_active"):
        item.review_active = False
    if hasattr(item, "review_stage"):
        item.review_stage = None


def cmd_cancel(
    *, repo_root: Path, id: str, reason: str | None,
    cascade: bool = False, no_archive: bool = False,
) -> None:
    if reason is None or not reason.strip():
        raise CommandError(f"{id}: cancel requires --reason")
    reason = reason.strip()

    kind = parse_id(id)[0]
    if kind == "task":
        raise CommandError(
            "cancel does not apply to tasks; cancel the parent slice instead"
        )
    if cascade and kind != "phase":
        raise CommandError(f"{id}: --cascade is only valid for phase ids")
    if no_archive and kind != "cross":
        raise CommandError(f"{id}: --no-archive is only valid for cross-cutting ids")

    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        if is_terminal(item.status):
            raise CommandError(f"{qid} is already {item.status.value}; cannot cancel")

        if kind == "phase":
            open_slices = [s for s in item.slices if not is_terminal(s.status)]
            if open_slices and not cascade:
                ids = ", ".join(s.id for s in open_slices)
                raise CommandError(
                    f"{qid}: phase has open slices ({ids}); use --cascade to cancel them"
                )
            for s in open_slices:
                _stamp_cancellation(s, reason, suffix=f"cascaded from {qid}")
                _notify_status(
                    qid=f"{qid}.{s.id}", kind="slice",
                    status=s.status, title=s.title,
                )
            _stamp_cancellation(item, reason, suffix=None)
            _save(write_root, p)
            _notify_status(qid=qid, kind="phase", status=item.status, title=item.title)
            return

        _stamp_cancellation(item, reason, suffix=None)

        archive_path: Path | None = None
        if kind == "cross" and not no_archive:
            archive_path, _archive_rel = _archive_cross_at_root(write_root, p, item)
        _save(write_root, p)
        if archive_path is not None:
            _git_stage(write_root, archive_path)
        _notify_status(qid=qid, kind=kind, status=item.status, title=item.title)


def cmd_archive_cross(*, repo_root: Path, id: str) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        if any(a.id == id for a in p.archived_cross_cutting):
            raise CommandError(f"cross-cutting {id} is already archived")
        qid, _container, item = _find_item(p, id)
        kind = parse_id(qid)[0]
        if kind != "cross":
            raise CommandError(f"archive-cross only works on cross-cutting items; {qid} is a {kind}")
        archive_path, _archive_rel = _archive_cross_at_root(write_root, p, item)
        _save(write_root, p)
        _git_stage(write_root, archive_path)

def cmd_block(*, repo_root: Path, slice_id: str, on: str) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        if not is_slice_id(slice_id):
            raise CommandError(f"block only works on slices; {slice_id} is a {kind_of(slice_id)}")
        _qid, _container, item = _find_item(p, slice_id)
        _refuse_if_cancelled(_qid, item, "block")
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
        _refuse_if_cancelled(_qid, item, "unblock")
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
        _refuse_if_cancelled(qid, item, "change deps for")
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
        _refuse_if_cancelled(qid, item, "ratify")
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
        if replace is not None:
            _refuse_if_cancelled(_qid, item, "replace notes")
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

# ───── workflow artifacts ─────

def cmd_artifact_add(
    *,
    repo_root: Path,
    id: str,
    kind: str,
    path: Path,
    allow_missing: bool = False,
) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        try:
            artifact = normalize_artifact_path(
                invocation_root=repo_root,
                write_root=write_root,
                raw_path=path,
                kind=ArtifactKind(kind),
                allow_missing=allow_missing,
            )
            added = add_artifact_to_item(item, artifact)
        except (ArtifactError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        _save(write_root, p)
        if artifact.exists_in_write_root:
            _git_stage_rel(write_root, artifact.relative_path)
        if added and artifact.exists_in_write_root:
            _notify_artifact(qid=qid, kind=parse_id(qid)[0], artifact_kind=artifact.kind, title=item.title)
        state = "added" if added else "already present"
        print(f"{qid}: {state} {artifact.relative_path}")


def _artifact_status_problems(
    repo_root: Path,
    id: str | None,
    *,
    baseline_root: Path | None = None,
) -> list[ArtifactProblem]:
    p = _load(repo_root)
    status_map = git_status_map(repo_root)
    referenced: set[str] = set()
    problems: list[ArtifactProblem] = []
    if id:
        qid, _container, item = _find_item(p, id)
        scoped = [(qid, item)]
    else:
        scoped = [
            (qid, item)
            for qid, _kind, _title, item in _iter_project_rows(p)
            if qid != "<project>"
        ]

    for qid, item in scoped:
        for rel in sorted(referenced_paths_for_item(item)):
            referenced.add(rel)
            if not (repo_root / rel).exists():
                problems.append(
                    ArtifactProblem(
                        "error",
                        "missing-referenced-artifact",
                        qid,
                        rel,
                        "referenced artifact path does not exist",
                    )
                )
            elif referenced_path_is_unstaged(rel, status_map):
                kind = artifact_kind_for_path(rel)
                kind_text = kind.value if kind else "<kind>"
                problems.append(
                    ArtifactProblem(
                        "error",
                        "referenced-artifact-unstaged",
                        qid,
                        rel,
                        "referenced artifact exists but is not staged: "
                        f"{rel}; run tasktool artifact add {qid} --kind {kind_text} --path {rel} "
                        f"or tasktool artifact commit {qid} --message ...",
                    )
                )

    files = workflow_files(repo_root)
    if id is None:
        referenced.update(referenced_paths_for_archives(p, repo_root))
    tasklist_status = status_map.get("docs/tasklist.json")
    if files and tasklist_status and tasklist_status.has_unstaged_worktree_change:
        problems.append(
            ArtifactProblem(
                "error",
                "unstaged-tasklist-with-workflow-artifacts",
                None,
                "docs/tasklist.json",
                "docs/tasklist.json has unstaged changes while workflow artifacts are present",
            )
        )

    if id is None:
        baseline = artifact_status_baseline_paths(baseline_root or repo_root)
        for rel in sorted(files - referenced):
            if rel in baseline:
                continue
            if rel.endswith(".md") or rel.startswith("docs/reviewer/"):
                problems.append(
                    ArtifactProblem(
                        "warning",
                        "unreferenced-workflow-artifact",
                        None,
                        rel,
                        "unreferenced workflow artifact",
                    )
                )
    return problems


def cmd_artifact_status(*, repo_root: Path, id: str | None, strict: bool, format: str) -> int:
    write_root, _routed, _mode, _authoritative_branch = _resolve_write_root(repo_root)
    try:
        problems = _artifact_status_problems(write_root, id, baseline_root=repo_root)
    except ArtifactError as exc:
        raise CommandError(str(exc)) from exc
    out = render_status_json(problems) if format == "json" else render_status_text(problems)
    sys.stdout.write(out)
    return 1 if strict and problems else 0


def cmd_artifact_commit(*, repo_root: Path, id: str, message: str) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        paths = sorted(referenced_paths_for_item(item))
        missing = [rel for rel in paths if not (write_root / rel).exists()]
        if missing:
            raise CommandError("missing referenced artifacts: " + ", ".join(missing))
        _git_stage_rel(write_root, "docs/tasklist.json")
        for rel in paths:
            _git_stage_rel(write_root, rel)
        status_code = cmd_artifact_status(repo_root=write_root, id=qid, strict=True, format="text")
        if status_code != 0:
            raise CommandError("artifact status is not clean")
        orphans = same_slug_orphans(write_root, row_id=qid, referenced=set(paths))
        if orphans:
            raise CommandError("unreferenced same-slug workflow artifacts: " + ", ".join(orphans))
        bad = disallowed_staged_paths(write_root, paths)
        if bad:
            raise CommandError("unrelated staged paths: " + ", ".join(bad))
        result = _subprocess.run(
            ["git", "commit", "-m", message],
            cwd=write_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise CommandError(result.stderr.strip() or result.stdout.strip() or "git commit failed")
        print(result.stdout.strip())


def _artifact_specs_from_args(spec: str | None, plan: str | None, handoff: str | None) -> list[tuple[str, Path]]:
    pairs: list[tuple[str, Path]] = []
    if spec:
        pairs.append(("spec", Path(spec)))
    if plan:
        pairs.append(("plan", Path(plan)))
    if handoff:
        pairs.append(("handoff", Path(handoff)))
    return pairs


def _normalized_artifacts_from_args(
    *,
    invocation_root: Path,
    write_root: Path,
    spec: str | None,
    plan: str | None,
    handoff: str | None,
) -> list[NormalizedArtifact]:
    artifacts = []
    for artifact_kind, artifact_path in _artifact_specs_from_args(spec, plan, handoff):
        try:
            artifacts.append(
                normalize_artifact_path(
                    invocation_root=invocation_root,
                    write_root=write_root,
                    raw_path=artifact_path,
                    kind=ArtifactKind(artifact_kind),
                    allow_missing=True,
                )
            )
        except (ArtifactError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
    return artifacts


def cmd_prepare(
    *,
    repo_root: Path,
    mode: str,
    id: str | None = None,
    phase_id: str | None = None,
    title: str | None = None,
    spec: str | None = None,
    plan: str | None = None,
    handoff: str | None = None,
) -> None:
    if mode == "existing" and id is None:
        raise CommandError("prepare existing requires an id")
    if mode in {"cross", "phase"} and not title:
        raise CommandError(f"prepare {mode} requires --title")
    if mode == "slice" and (not title or not phase_id):
        raise CommandError("prepare slice requires <phase-id> and --title")
    if mode not in {"existing", "cross", "phase", "slice"}:
        raise CommandError(f"unknown prepare mode: {mode}")

    with _write_context(repo_root) as write_root:
        artifacts = _normalized_artifacts_from_args(
            invocation_root=repo_root,
            write_root=write_root,
            spec=spec,
            plan=plan,
            handoff=handoff,
        )
        p = _load(write_root)
        created_kind: str | None = None
        if mode == "existing":
            target_id = id or ""
            qid, _container, item = _find_item(p, target_id)
            target_id = qid
        elif mode == "cross":
            target_id = next_cross_id(p, write_root)
            item = CrossCutting(id=target_id, title=title or "", created=_today())
            p.cross_cutting.append(item)
            created_kind = "cross"
        elif mode == "phase":
            target_id = next_phase_id(p, write_root)
            item = Phase(id=target_id, title=title or "", created=_today())
            p.phases.append(item)
            created_kind = "phase"
        else:
            phase = next((ph for ph in p.phases if ph.id == phase_id), None)
            if phase is None:
                raise CommandError(f"phase {phase_id} not found")
            new_id = next_slice_id(p, phase_id or "", write_root)
            item = Slice(id=new_id, title=title or "", created=_today())
            phase.slices.append(item)
            target_id = f"{phase_id}.{new_id}"
            created_kind = "slice"

        for artifact in artifacts:
            try:
                add_artifact_to_item(item, artifact)
            except ArtifactError as exc:
                raise CommandError(str(exc)) from exc
        _save(write_root, p)
        for artifact in artifacts:
            if artifact.exists_in_write_root:
                _git_stage_rel(write_root, artifact.relative_path)
        if created_kind is not None:
            _notify_status(qid=target_id, kind=created_kind, status=item.status, title=item.title)
    print(target_id)

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
    from tasktool.model import extract_cancellation_reason
    p = _load(repo_root)
    qid, _container, item = _find_item(p, id)
    lines = [f"# {qid} — {item.title}", f"status: {item.status.value}"]
    _ws = getattr(item, "workflow_step", None)
    if _ws is not None:
        lines.append(f"workflow_step: {_ws.value}")
    if getattr(item, "review_active", False):
        _stage = getattr(item, "review_stage", None)
        lines.append("review_active: true")
        lines.append(f"review_stage: {_stage.value if _stage is not None else 'unknown'}")
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
    if getattr(item, "worktree_path", None):
        lines.append(f"worktree_path: {item.worktree_path}")
    if getattr(item, "worktree_branch", None):
        lines.append(f"worktree_branch: {item.worktree_branch}")
    if getattr(item, "worktree_in_place", False):
        lines.append("worktree_in_place: true")
    if getattr(item, "worktree_pruned_at", None):
        lines.append(f"worktree_pruned_at: {item.worktree_pruned_at}")
    if getattr(item, "worktree_prune_pending", False):
        lines.append("worktree_prune_pending: true")
        if getattr(item, "worktree_prune_pending_at", None):
            lines.append(f"worktree_prune_pending_at: {item.worktree_prune_pending_at}")
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
    if item.status == Status.CANCELLED:
        reason = extract_cancellation_reason(getattr(item, "notes", None))
        if reason:
            lines.insert(0, "")
            lines.insert(0, f"**{reason}**")
    return "\n".join(lines) + "\n"

def _phase_by_id(p: Project, phase_id: str) -> Phase:
    phase = next((ph for ph in p.phases if ph.id == phase_id), None)
    if phase is None:
        raise CommandError(f"phase {phase_id} not found")
    return phase

def _done_slice_ids(phase: Phase) -> set[str]:
    return {f"{phase.id}.{s.id}" for s in phase.slices if s.status == Status.DONE}

def _cancelled_slice_ids(phase: Phase) -> set[str]:
    return {f"{phase.id}.{s.id}" for s in phase.slices if s.status == Status.CANCELLED}

def _is_slice_ready_for_work(phase: Phase, s: Slice) -> bool:
    if is_terminal(s.status) or s.status == Status.BLOCKED:
        return False
    if s.planning_status == PlanningStatus.SUPERSEDED:
        return False
    cancelled = _cancelled_slice_ids(phase)
    if any(dep in cancelled for dep in s.depends_on):
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
    cancelled = _cancelled_slice_ids(phase)
    rows = []
    for s in phase.slices:
        waiting_on = [
            dep for dep in s.depends_on if dep not in done and dep not in cancelled
        ]
        cancelled_deps = [dep for dep in s.depends_on if dep in cancelled]
        ready = _is_slice_ready_for_work(phase, s) and not cancelled_deps
        rows.append({
            "id": f"{phase.id}.{s.id}",
            "status": s.status.value,
            "planning_status": s.planning_status.value,
            "parallel_group": s.parallel_group,
            "depends_on": s.depends_on,
            "waiting_on": waiting_on,
            "cancelled_deps": cancelled_deps,
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
        cancelled_str = (
            ", ".join(row["cancelled_deps"]) if row["cancelled_deps"] else "-"
        )
        group = row["parallel_group"] or "-"
        lines.append(
            f"{row['id']}  [{row['status']}/{row['planning_status']}]  "
            f"group={group}  {ready}  deps={deps}  waiting_on={waits}  "
            f"cancelled_deps={cancelled_str}  {row['title']}"
        )
    return "\n".join(lines).rstrip() + "\n"

def cmd_phase_status(*, repo_root: Path, recent: int = 3, format: str = "text") -> str:
    p = _load(repo_root)
    open_cross = [c for c in p.cross_cutting if not is_terminal(c.status)]
    open_phases = [ph for ph in p.phases if not is_terminal(ph.status)]
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

def _iter_items(p: Project, *, suppress_children_of_terminal: bool = False):
    for ph in p.phases:
        yield ("phase", ph.id, ph)
        for s in ph.slices:
            yield ("slice", f"{ph.id}.{s.id}", s)
            if suppress_children_of_terminal and is_terminal(s.status):
                # Containment rule: when reporting only open work, skip the
                # child tasks of a terminal (done/cancelled) parent slice.
                # Their statuses are not mutated; cmd_show still emits them
                # verbatim.
                continue
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
    show_all: bool = False,
    workflow_step: str | None = None,
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
    for item_kind, qid, item in _iter_items(
        p, suppress_children_of_terminal=open_only,
    ):
        if phase and not qid.startswith(phase):
            continue
        if kind and item_kind != kind:
            continue
        if status_filter and item.status.value not in status_filter:
            continue
        if workflow_step is not None:
            item_step = getattr(item, "workflow_step", None)
            if item_step is None or item_step.value != workflow_step:
                continue
        if (
            not show_all
            and item_kind == "cross"
            and (getattr(item, "notes", "") or "").strip() == "ad-hoc"
        ):
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
    open_slices = [s.id for s in phase.slices if not is_terminal(s.status)]
    if open_slices:
        raise CommandError(
            f"phase {phase_id} has open slices: {', '.join(open_slices)}"
        )
    if phase.status == Status.CANCELLED:
        # Cancelled phases bypass the post-phase reviewer gate; record the skip.
        skip_note = "Phase cancelled; post-phase review gate skipped"
        phase.notes = (
            phase.notes + "\n" + skip_note if phase.notes else skip_note
        )
    else:
        if skip_review_gate:
            print(f"warning: review gate skipped for {phase_id}", file=_sys.stderr)
        _apply_review_gate(invocation_root, phase, phase_id, "phase",
                           reviewer_chain, skip_review_gate)
    if not is_terminal(phase.status):
        phase.status = Status.DONE
        phase.closed = phase.closed or _today()
    else:
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
    _notify_status(qid=phase_id, kind="phase", status=phase.status, title=phase.title)

def cmd_brief(*, repo_root: Path, id: str) -> str:
    from tasktool.brief import brief as _brief
    p = _load(repo_root)
    qid = _resolve_id(p, id)
    return _brief(p, qid)


def _iter_worktree_rows(p):
    """Yield (qid, item) pairs for every slice + cross row that may carry worktree fields."""
    for ph in p.phases:
        for s in ph.slices:
            yield f"{ph.id}.{s.id}", s
    for c in p.cross_cutting:
        yield c.id, c


def _health_for(write_root: Path, item) -> str:
    from tasktool.worktree_lifecycle import (
        RecordedState, classify_recorded_state,
    )
    if item.worktree_in_place:
        return "in-place"
    if item.worktree_path is None and item.worktree_branch is None:
        if getattr(item, "worktree_pruned_at", None):
            return "pruned"
        return "absent"
    recorded_path = (write_root / item.worktree_path).resolve() if item.worktree_path else None
    state = classify_recorded_state(
        write_root, recorded_path=recorded_path, recorded_branch=item.worktree_branch,
    )
    return {
        RecordedState.CONSISTENT: "live",
        RecordedState.BOTH_MISSING: "missing-path",
        RecordedState.PATH_MISSING: "missing-path",
        RecordedState.PATH_NOT_WORKTREE: "mismatched",
        RecordedState.BRANCH_MISMATCH: "mismatched",
        RecordedState.ABSENT: "absent",
    }[state]


def cmd_worktree_list(*, repo_root: Path, show_all: bool = False) -> str:
    with _read_context(repo_root) as write_root:
        p = _load(write_root)
        rows = []
        for qid, item in _iter_worktree_rows(p):
            has_path = item.worktree_path is not None
            is_in_place = item.worktree_in_place
            is_pruned = (not has_path) and (not is_in_place) and bool(
                getattr(item, "worktree_pruned_at", None)
            )
            if not show_all and not has_path:
                continue
            if is_in_place and not show_all:
                continue
            if is_pruned and not show_all:
                continue
            health = _health_for(write_root, item)
            path = item.worktree_path or ""
            branch = item.worktree_branch or ""
            rows.append((qid, item.status.value, path, branch, health))
        if not rows:
            return "(no worktrees)\n"
        widths = [max(len(str(r[i])) for r in rows) for i in range(5)]
        headers = ("ID", "STATUS", "PATH", "BRANCH", "HEALTH")
        widths = [max(widths[i], len(headers[i])) for i in range(5)]
        line = lambda r: "  ".join(str(r[i]).ljust(widths[i]) for i in range(5))
        out_lines = [line(headers)] + [line(r) for r in rows]
        return "\n".join(out_lines) + "\n"


def cmd_worktree_status(*, repo_root: Path, id: str) -> str:
    with _read_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        if item.worktree_in_place:
            return f"{qid}: in-place (no worktree on disk)\n"
        if item.worktree_path is None:
            return f"{qid}: no worktree recorded\n"
        wt = (write_root / item.worktree_path).resolve()
        health = _health_for(write_root, item)
        lines = [
            f"{qid}: {health}",
            f"path: {item.worktree_path}",
            f"branch: {item.worktree_branch}",
        ]
        if health == "live":
            # ahead/behind vs the configured authoritative parent branch (NOT a
            # hardcoded "main"). _resolve_write_root already exposes this via
            # `authoritative_branch`; we re-read config here directly to avoid
            # double-routing inside the existing _write_context.
            from tasktool.config import load_config
            parent_branch = load_config(write_root).tasklist.authoritative_branch
            try:
                ab = _subprocess.run(
                    ["git", "rev-list", "--left-right", "--count",
                     f"{parent_branch}...{item.worktree_branch}"],
                    cwd=write_root, text=True, capture_output=True, check=True,
                ).stdout.strip().split()
                behind, ahead = ab[0], ab[1]
                lines.append(f"ahead/behind: {ahead}/{behind} (vs {parent_branch})")
            except _subprocess.CalledProcessError:
                lines.append(f"ahead/behind: unknown (vs {parent_branch})")
            dirty = _subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=wt, text=True, capture_output=True, check=True,
            ).stdout.splitlines()
            lines.append(f"dirty: {'clean' if not dirty else f'{len(dirty)} path(s)'}")
            last = _subprocess.run(
                ["git", "log", "-1", "--format=%cI"],
                cwd=wt, text=True, capture_output=True, check=True,
            ).stdout.strip()
            lines.append(f"last_activity: {last}")
        return "\n".join(lines) + "\n"


def cmd_worktree_adopt(*, repo_root: Path, id: str, path: Path) -> None:
    from tasktool.worktree_lifecycle import (
        RecordedState, classify_recorded_state, is_authoritative_checkout,
        linked_worktree_branch,
    )
    path = path.expanduser().resolve()
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        if item.worktree_in_place:
            raise CommandError(f"{qid}: cannot adopt; slice is marked --in-place")
        if is_authoritative_checkout(write_root, path):
            raise CommandError(
                f"{qid}: adopt refused; {path} is the main checkout, not a linked "
                f"worktree. Create a linked worktree first with `git worktree add` "
                f"then adopt that path."
            )
        branch = linked_worktree_branch(write_root, path)
        if branch is None:
            raise CommandError(f"{qid}: {path} is not a linked worktree of this repository.")
        # If the current record is still live and consistent, refuse to clobber.
        if item.worktree_path is not None:
            recorded = (write_root / item.worktree_path).resolve()
            state = classify_recorded_state(
                write_root, recorded_path=recorded, recorded_branch=item.worktree_branch,
            )
            if state == RecordedState.CONSISTENT and recorded != path:
                raise CommandError(
                    f"{qid}: a live worktree is already recorded at {item.worktree_path!r}; "
                    f"prune it first (P5.S2) before adopting a new path."
                )
        try:
            rel = path.relative_to(write_root.resolve())
            rel_str = str(rel)
        except ValueError:
            rel_str = str(path)
        item.worktree_path = rel_str
        item.worktree_branch = branch
        item.worktree_in_place = False
        # Adopt clears a previously recorded pruned-at marker; it represents a fresh association.
        item.worktree_pruned_at = None
        _save(write_root, p)


def cmd_worktree_ensure_gitignore(*, repo_root: Path) -> str:
    from tasktool.worktree_lifecycle import ensure_gitignore_entry
    changed = ensure_gitignore_entry(repo_root)
    return "added .worktrees/ to .gitignore\n" if changed else ".worktrees/ already ignored\n"


def cmd_worktree_check_legacy(*, repo_root: Path, project_name: str) -> tuple[str, int]:
    from tasktool.worktree_lifecycle import legacy_worktree_dirs
    import os
    home = Path(os.path.expanduser("~"))
    found = legacy_worktree_dirs(repo_root, home=home, project_name=project_name)
    if not found:
        return ("no legacy worktree directories detected\n", 0)
    lines = ["legacy worktree directories detected (warn-only, not removed):"]
    lines.extend(f"  - {p}" for p in found)
    return ("\n".join(lines) + "\n", 1)


def cmd_worktree_prune(
    *, repo_root: Path, id: str,
    keep_branch: bool = False, force: bool = False, finalize: bool = False,
) -> None:
    from tasktool import worktree as wt
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)

        if finalize:
            _worktree_finalize(write_root, item, qid)
            _save(write_root, p)
            return

        # In-place slices: no worktree to prune; record timestamp and exit.
        if getattr(item, "worktree_in_place", False):
            item.worktree_pruned_at = _today()
            _save(write_root, p)
            print(f"{qid}: --in-place slice; no worktree to remove.")
            return

        # Already pruned (no path on file)?
        path_str = getattr(item, "worktree_path", None)
        branch = getattr(item, "worktree_branch", None)
        if not path_str or not branch:
            raise CommandError(
                f"{qid}: no recorded worktree to prune "
                f"(worktree_path={path_str!r}, worktree_branch={branch!r})"
            )
        wt_path = (write_root / path_str).resolve()

        # Guard 1: slice status is terminal (done OR cancelled), unless --force.
        if not force:
            if not is_terminal(getattr(item, "status", None)):
                raise CommandError(
                    f"{qid}: slice status is {item.status.value!r}; prune requires "
                    f"a terminal status (run `tasktool close {qid}` or "
                    f"`tasktool cancel {qid}` first, or pass --force)"
                )

            # Guard 2: branch merged into authoritative parent.
            parent = _authoritative_parent_branch(write_root, qid)
            if not wt.branch_is_merged(write_root, branch=branch, into=parent):
                raise CommandError(
                    f"{qid}: branch {branch!r} is not merged into {parent!r}; "
                    f"merge first or pass --force"
                )

            # Guard 3: clean worktree.
            if wt_path.exists():
                dirty, items = wt.working_tree_dirty(wt_path)
                if dirty:
                    pretty = ", ".join(items[:5]) + (" ..." if len(items) > 5 else "")
                    raise CommandError(
                        f"{qid}: worktree at {wt_path} is not clean: {pretty}"
                    )

        # Recent-HEAD informational note (never refuses).
        if wt_path.exists():
            try:
                age = wt.head_age_seconds(wt_path)
                if age < 60:
                    print(
                        f"note: {qid} worktree HEAD moved {age:.0f}s ago; "
                        f"proceeding with prune",
                        file=sys.stderr,
                    )
            except Exception:
                pass

        # Prune-from-inside detection.
        cwd = Path.cwd()
        if wt.is_inside_worktree(cwd) and _path_under(cwd, wt_path):
            item.worktree_prune_pending = True
            item.worktree_prune_pending_at = _today()
            _save(write_root, p)
            authoritative = write_root
            print(
                f"{qid}: prune deferred (running inside the worktree being removed).\n"
                f"Run this from outside:\n"
                f"  cd {authoritative} && git worktree remove {wt_path} && "
                f"tasktool worktree prune {qid} --finalize"
            )
            return

        # Destructive step.
        if wt_path.exists():
            wt.git_worktree_remove(write_root, wt_path, force=force)
        if not keep_branch and wt.branch_exists(write_root, branch):
            wt.git_branch_delete(write_root, branch, force=force)

        item.worktree_path = None
        item.worktree_branch = None
        item.worktree_pruned_at = _today()
        # Clear any stale pending marker.
        item.worktree_prune_pending = False
        item.worktree_prune_pending_at = None
        _save(write_root, p)
        print(f"{qid}: worktree pruned (path={wt_path}, branch={branch})")


def _worktree_finalize(write_root: Path, item, qid: str) -> None:
    from tasktool import worktree as wt
    if not getattr(item, "worktree_prune_pending", False):
        raise CommandError(
            f"{qid}: no pending prune to finalize; "
            f"run `tasktool worktree prune {qid}` first."
        )
    path_str = getattr(item, "worktree_path", None)
    if not path_str:
        raise CommandError(f"{qid}: pending prune missing worktree_path; cannot finalize")
    wt_path = (write_root / path_str).resolve()
    if wt.path_is_registered_worktree(write_root, wt_path):
        raise CommandError(
            f"{qid}: worktree at {wt_path} is still registered in `git worktree list`; "
            f"run `git worktree remove {wt_path}` before --finalize"
        )
    if wt_path.exists():
        raise CommandError(
            f"{qid}: directory still present at {wt_path}; "
            f"remove it before --finalize"
        )
    item.worktree_path = None
    item.worktree_branch = None
    item.worktree_prune_pending = False
    item.worktree_prune_pending_at = None
    item.worktree_pruned_at = _today()
    print(f"{qid}: finalize complete; audit fields recorded.")


def _path_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _authoritative_parent_branch(write_root: Path, qid: str) -> str:
    """Return the merge-target branch for a slice's worktree.

    Read from `.tasktool/config.json` (`tasklist.authoritative_branch`),
    matching the existing `TasklistConfig` surface in `tools/tasktool/config.py`.
    Falls back to "main" when no config file is present (matches
    `TasklistConfig`'s default).
    """
    from tasktool.config import load_config
    return load_config(write_root).tasklist.authoritative_branch


def cmd_worktree_repair(*, repo_root: Path, id: str) -> None:
    from tasktool import worktree as wt
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        path_str = getattr(item, "worktree_path", None)
        branch = getattr(item, "worktree_branch", None)
        if not path_str or not branch:
            raise CommandError(
                f"{qid}: no recorded worktree fields to repair "
                f"(worktree_path={path_str!r}, worktree_branch={branch!r}); "
                f"use `tasktool worktree adopt {qid} <path>` after recreating manually"
            )
        wt_path = (write_root / path_str).resolve()
        # Already live? No-op.
        if wt.path_is_registered_worktree(write_root, wt_path) and wt_path.exists():
            print(f"{qid}: worktree already live at {wt_path}; no action.")
            return
        if not wt.branch_exists(write_root, branch):
            raise CommandError(
                f"{qid}: branch {branch!r} missing; cannot repair. "
                f"Recreate the branch or use `tasktool worktree adopt {qid} <path>`."
            )
        wt.git_worktree_add(write_root, wt_path, branch)
        print(f"{qid}: worktree recreated at {wt_path} on branch {branch}.")


# ───── infer-step (workflow_step inference) ─────

def _find_row(p: Project, qid: str):
    """Returns ("slice", phase, slice) | ("phase", phase, None) | ("cross", cross, None).

    Delegates to the existing `_find_item` helper, which already handles
    qualified-vs-short ID resolution. Raises UsageError on missing IDs.
    """
    try:
        qid_resolved, _container, item = _find_item(p, qid)
    except CommandError as e:
        raise UsageError(str(e)) from e
    parsed = parse_id(qid_resolved)[0]
    if parsed == "slice":
        phase_part = split_qualified(qid_resolved)[0]
        phase = next(ph for ph in p.phases if ph.id == phase_part)
        return "slice", phase, item
    if parsed == "phase":
        return "phase", item, None
    if parsed == "cross":
        return "cross", item, None
    raise UsageError(f"infer-step: unsupported id kind: {qid}")


def _infer_step_for_slice(phase: Phase, slice_: Slice) -> dict:
    if slice_.status == Status.DONE:
        return {"step": "done", "blocked": False}
    blocked = slice_.status == Status.BLOCKED
    has_slice_plan = bool(slice_.plan_path)
    plan_ratified = slice_.planning_status == PlanningStatus.RATIFIED
    # Per spec §3.3: the slice-level step is driven by the slice's own plan_path.
    # Absence of plan_path keeps the slice in the spec stage; once a plan exists,
    # ratification advances it to implement. (The phase's spec_path governs the
    # phase-level inference, handled in Task 6.)
    if not has_slice_plan:
        step = "spec"
    elif not plan_ratified:
        step = "plan"
    else:
        step = "implement"
    return {"step": step, "blocked": blocked}


def _infer_step_for_phase(phase: Phase) -> dict:
    if not phase.spec_path:
        return {"step": "spec", "blocked": False}
    if not phase.slices:
        return {"step": "spec", "blocked": False}
    statuses = [s.status for s in phase.slices]
    if all(s == Status.DONE for s in statuses):
        return {"step": "done", "blocked": False}
    any_started = any(s in (Status.IN_PROGRESS, Status.BLOCKED, Status.DONE) for s in statuses)
    if any_started:
        blocked = any(s == Status.BLOCKED for s in statuses)
        return {"step": "in_progress", "blocked": blocked}
    return {"step": "ready", "blocked": False}


def infer_step_for_id(p: Project, qid: str) -> dict:
    kind, parent, child = _find_row(p, qid)
    if kind == "cross":
        return {"step": "n/a", "blocked": False}
    if kind == "slice":
        return _infer_step_for_slice(parent, child)
    if kind == "phase":
        return _infer_step_for_phase(parent)
    raise UsageError(f"infer-step: unsupported kind for {qid}")


def _stored_step_for(item) -> str | None:
    """Return the stored workflow_step value (enum .value) or None."""
    ws = getattr(item, "workflow_step", None)
    if ws is None:
        return None
    return getattr(ws, "value", ws)


def _format_single_text(qid: str, inferred: dict, stored: str | None) -> str:
    parts = [f"{qid}: {inferred['step']}"]
    if inferred.get("blocked"):
        parts.append("(blocked)")
    parts.append(f"(stored: {stored})")
    return " ".join(parts) + "\n"


def _format_all_row(qid: str, inferred: dict, stored: str | None, drift: bool) -> str:
    prefix = "!" if drift else " "
    return f"{prefix} {qid:<10} inferred={inferred['step']}  stored={stored}\n"


def cmd_infer_step(
    *, repo_root: Path, id: str | None, all: bool, diff: bool, format: str,
) -> int:
    """Infer workflow_step for one row or every row.

    Returns:
      - 0 on success (single-row, or --all with no drift when --diff)
      - 1 when --all --diff finds drift
      - 2 on a process error (unknown id)
    """
    try:
        p = _load(repo_root)
    except CommandError as e:
        print(f"tasktool: {e}", file=sys.stderr)
        return 2

    if not all:
        # Single-row mode.
        try:
            kind, parent, child = _find_row(p, id)
        except UsageError as e:
            print(f"tasktool: {e}", file=sys.stderr)
            return 2
        # Build the qualified id from the resolved row.
        if kind == "slice":
            qid = f"{parent.id}.{child.id}"
            item = child
        else:
            qid = parent.id
            item = parent
        inferred = infer_step_for_id(p, qid)
        stored = _stored_step_for(item)
        if format == "json":
            print(_json.dumps({
                "id": qid,
                "step": inferred["step"],
                "blocked": inferred["blocked"],
                "stored": stored,
            }))
        else:
            sys.stdout.write(_format_single_text(qid, inferred, stored))
        return 0

    # --all mode: iterate phases + slices + cross-cutting.
    # Cross-cutting rows always emit step="n/a" and are never flagged as drift
    # (spec §3.3 + AC 16).
    rows: list[tuple[str, dict, str | None, bool]] = []
    for ph in p.phases:
        ph_inferred = _infer_step_for_phase(ph)
        rows.append((ph.id, ph_inferred, _stored_step_for(ph), False))
        for s in ph.slices:
            qid = f"{ph.id}.{s.id}"
            s_inferred = _infer_step_for_slice(ph, s)
            rows.append((qid, s_inferred, _stored_step_for(s), False))
    for c in p.cross_cutting:
        rows.append((c.id, {"step": "n/a", "blocked": False}, None, True))

    # `stored=None` is opt-in — never counts as drift. Cross-cutting rows are
    # never drift candidates regardless of stored value.
    def _is_drift(inferred: dict, stored: str | None, is_cross: bool) -> bool:
        if is_cross:
            return False
        return stored is not None and stored != inferred["step"]

    if diff:
        rows = [
            (qid, inf, stored, is_cross)
            for (qid, inf, stored, is_cross) in rows
            if _is_drift(inf, stored, is_cross)
        ]

    if format == "json":
        for qid, inf, stored, is_cross in rows:
            print(_json.dumps({
                "id": qid,
                "step": inf["step"],
                "blocked": inf["blocked"],
                "stored": stored,
                "drift": _is_drift(inf, stored, is_cross),
            }))
    else:
        for qid, inf, stored, is_cross in rows:
            sys.stdout.write(
                _format_all_row(qid, inf, stored, _is_drift(inf, stored, is_cross))
            )

    if diff and rows:
        return 1
    return 0
