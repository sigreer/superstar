from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path
from tasktool.model import (
    Project, Phase, Slice, Task, CrossCutting, ArchivedPhase,
    ArchivedCrossCutting, BlockedOn, Reservation, LedgerReservation,
    Status, PlanningStatus, SCHEMA_VERSION,
    SliceWorkflowStep, PhaseWorkflowStep, ReviewStage,
)

_WORKTREE_DEFAULT_OMIT = {
    # field -> default value to omit on
    "worktree_path": None,
    "worktree_branch": None,
    "worktree_pruned_at": None,
    "worktree_prune_pending_at": None,
    "worktree_in_place": False,
    "worktree_prune_pending": False,
}


def _strip_worktree_defaults(d: dict) -> dict:
    """Drop worktree_* keys whose values equal their dataclass default.

    Historical rows that never set worktree_* fields must NOT gain those keys
    when re-serialised. Rows that explicitly set non-default values keep them.
    """
    for field, default in _WORKTREE_DEFAULT_OMIT.items():
        if field in d and d[field] == default:
            del d[field]
    return d


_WORKFLOW_DEFAULT_OMIT = {
    "workflow_step": None,
    "review_active": False,
    "review_stage": None,
}


def _strip_workflow_defaults(d: dict) -> dict:
    """Drop workflow/review keys whose values equal their dataclass default.

    Historical rows must not gain these keys on round-trip when unset.
    """
    for field, default in _WORKFLOW_DEFAULT_OMIT.items():
        if field in d and d[field] == default:
            del d[field]
    return d


_P7_DEFAULT_OMIT = {
    "coordination_group": None,
    "worktree_base_sha": None,
    "landed_base_sha": None,
}


def _strip_p7_defaults(d: dict) -> dict:
    """Drop P7 slice keys whose values equal their dataclass default.

    Empty integration_surfaces / reservations lists and None scalar fields
    are omitted so historical rows gain no churn on round-trip (spec §4.A F5).
    """
    for field, default in _P7_DEFAULT_OMIT.items():
        if field in d and d[field] == default:
            del d[field]
    if d.get("integration_surfaces") == []:
        d.pop("integration_surfaces", None)
    if d.get("reservations") == []:
        d.pop("reservations", None)
    return d


def to_dict(p: Project) -> dict:
    def _coerce(obj):
        if isinstance(obj, (Status, PlanningStatus,
                            SliceWorkflowStep, PhaseWorkflowStep, ReviewStage)):
            return obj.value
        return obj
    raw = asdict(p)
    def walk(node):
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return _coerce(node)
    out = walk(raw)
    # Omit worktree_* fields whose values equal dataclass defaults from
    # serialised slice and cross-cutting rows.
    for phase in out.get("phases", []):
        # Phase only has workflow_step (no review_* fields apply to phases).
        if "workflow_step" in phase and phase["workflow_step"] is None:
            del phase["workflow_step"]
        for slc in phase.get("slices", []):
            _strip_worktree_defaults(slc)
            _strip_workflow_defaults(slc)
            _strip_p7_defaults(slc)
    for cross in out.get("cross_cutting", []):
        _strip_worktree_defaults(cross)
    # Omit reservations_ledger when empty so historical projects gain no churn.
    if out.get("reservations_ledger") == []:
        del out["reservations_ledger"]
    # Always emit current SCHEMA_VERSION on save (auto-promotion of legacy rows).
    out["schema_version"] = SCHEMA_VERSION
    return out

def _strict_bool(value, *, scope: str, field: str, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    from tasktool.validate import ValidationError
    raise ValidationError(f"{scope}.{field}: expected bool, got {type(value).__name__} ({value!r})")


def _strict_opt_str(value, *, scope: str, field: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    from tasktool.validate import ValidationError
    raise ValidationError(f"{scope}.{field}: expected string or null, got {type(value).__name__} ({value!r})")


def from_dict(d: dict) -> Project:
    def _status(v):
        return Status(v) if isinstance(v, str) else v
    def _planning_status(v):
        return PlanningStatus(v) if isinstance(v, str) else v
    def _slice_workflow_step(v):
        return SliceWorkflowStep(v) if isinstance(v, str) else v
    def _phase_workflow_step(v):
        return PhaseWorkflowStep(v) if isinstance(v, str) else v
    def _review_stage(v):
        return ReviewStage(v) if isinstance(v, str) else v
    def _task(td):
        return Task(
            id=td["id"], title=td["title"], created=td["created"],
            started=td.get("started"),
            status=_status(td.get("status", "ready")),
            closed=td.get("closed"),
            refs=list(td.get("refs", [])),
            notes=td.get("notes", ""),
        )
    def _blocked(b):
        return None if b is None else BlockedOn(kind=b["kind"], value=b["value"])
    def _reservation(rd):
        return Reservation(
            resource=rd["resource"], value=rd["value"],
            scope=rd.get("scope", "phase"), note=rd.get("note"),
        )
    def _ledger_reservation(rd):
        return LedgerReservation(
            resource=rd["resource"], value=rd["value"], scope=rd["scope"],
            note=rd.get("note"), owner_id=rd["owner_id"],
            owner_phase_id=rd["owner_phase_id"], archived_date=rd["archived_date"],
        )
    def _slice(sd):
        scope = f"phases[].slices[id={sd.get('id')}]"
        return Slice(
            id=sd["id"], title=sd["title"], created=sd["created"],
            started=sd.get("started"),
            status=_status(sd.get("status", "ready")),
            closed=sd.get("closed"),
            blocked_on=_blocked(sd.get("blocked_on")),
            depends_on=list(sd.get("depends_on", [])),
            planning_status=_planning_status(sd.get("planning_status", "proposed")),
            parallel_group=sd.get("parallel_group"),
            plan_path=sd.get("plan_path"),
            refs=list(sd.get("refs", [])),
            notes=sd.get("notes", ""),
            workflow_step=_slice_workflow_step(sd.get("workflow_step")),
            review_active=_strict_bool(sd.get("review_active"), scope=scope, field="review_active"),
            review_stage=_review_stage(sd.get("review_stage")),
            reviewer_chain=sd.get("reviewer_chain"),
            tasks=[_task(t) for t in sd.get("tasks", [])],
            worktree_path=_strict_opt_str(sd.get("worktree_path"), scope=scope, field="worktree_path"),
            worktree_branch=_strict_opt_str(sd.get("worktree_branch"), scope=scope, field="worktree_branch"),
            worktree_in_place=_strict_bool(sd.get("worktree_in_place"), scope=scope, field="worktree_in_place"),
            worktree_pruned_at=_strict_opt_str(sd.get("worktree_pruned_at"), scope=scope, field="worktree_pruned_at"),
            worktree_prune_pending=_strict_bool(sd.get("worktree_prune_pending"), scope=scope, field="worktree_prune_pending"),
            worktree_prune_pending_at=_strict_opt_str(sd.get("worktree_prune_pending_at"), scope=scope, field="worktree_prune_pending_at"),
            integration_surfaces=list(sd.get("integration_surfaces", [])),
            reservations=[_reservation(r) for r in sd.get("reservations", [])],
            coordination_group=sd.get("coordination_group"),
            worktree_base_sha=_strict_opt_str(sd.get("worktree_base_sha"), scope=scope, field="worktree_base_sha"),
            landed_base_sha=_strict_opt_str(sd.get("landed_base_sha"), scope=scope, field="landed_base_sha"),
        )
    def _phase(pd):
        return Phase(
            id=pd["id"], title=pd["title"], created=pd["created"],
            started=pd.get("started"),
            status=_status(pd.get("status", "ready")),
            closed=pd.get("closed"),
            spec_path=pd.get("spec_path"),
            plan_path=pd.get("plan_path"),
            planning_path=pd.get("planning_path"),
            phase_reviewer_chain=pd.get("phase_reviewer_chain"),
            notes=pd.get("notes", ""),
            workflow_step=_phase_workflow_step(pd.get("workflow_step")),
            slices=[_slice(s) for s in pd.get("slices", [])],
        )
    def _cross(xd):
        scope = f"cross_cutting[id={xd.get('id')}]"
        return CrossCutting(
            id=xd["id"], title=xd["title"], created=xd["created"],
            started=xd.get("started"),
            status=_status(xd.get("status", "ready")),
            closed=xd.get("closed"),
            refs=list(xd.get("refs", [])),
            notes=xd.get("notes", ""),
            worktree_path=_strict_opt_str(xd.get("worktree_path"), scope=scope, field="worktree_path"),
            worktree_branch=_strict_opt_str(xd.get("worktree_branch"), scope=scope, field="worktree_branch"),
            worktree_in_place=_strict_bool(xd.get("worktree_in_place"), scope=scope, field="worktree_in_place"),
            worktree_pruned_at=_strict_opt_str(xd.get("worktree_pruned_at"), scope=scope, field="worktree_pruned_at"),
            worktree_prune_pending=_strict_bool(xd.get("worktree_prune_pending"), scope=scope, field="worktree_prune_pending"),
            worktree_prune_pending_at=_strict_opt_str(xd.get("worktree_prune_pending_at"), scope=scope, field="worktree_prune_pending_at"),
        )
    def _arch(ad):
        return ArchivedPhase(
            id=ad["id"], title=ad["title"],
            archived_path=ad["archived_path"], archived_date=ad["archived_date"],
        )
    def _arch_cross(ad):
        return ArchivedCrossCutting(
            id=ad["id"], title=ad["title"],
            archived_path=ad["archived_path"], archived_date=ad["archived_date"],
        )
    return Project(
        project=d["project"],
        schema_version=d.get("schema_version", SCHEMA_VERSION),
        north_star=d.get("north_star", ""),
        last_reviewed=d.get("last_reviewed"),
        phases=[_phase(p) for p in d.get("phases", [])],
        cross_cutting=[_cross(x) for x in d.get("cross_cutting", [])],
        archived_phases=[_arch(a) for a in d.get("archived_phases", [])],
        archived_cross_cutting=[
            _arch_cross(a) for a in d.get("archived_cross_cutting", [])
        ],
        reservations_ledger=[
            _ledger_reservation(r) for r in d.get("reservations_ledger", [])
        ],
    )

def dumps_canonical(p: Project) -> str:
    body = json.dumps(to_dict(p), indent=2, sort_keys=True, ensure_ascii=False)
    return body + "\n"

def loads_project(text: str) -> Project:
    return from_dict(json.loads(text))

def load_project(path: Path) -> Project:
    return loads_project(path.read_text(encoding="utf-8"))

def save_project(p: Project, path: Path) -> None:
    """Atomic write: tempfile + rename. Always canonical bytes."""
    text = dumps_canonical(p)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
