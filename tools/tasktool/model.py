from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

SCHEMA_VERSION = 3

_CANCEL_LINE_RE = re.compile(r"^Cancelled \S+: .*$", re.M)


def extract_cancellation_reason(notes: str | None) -> str | None:
    """Return the first `Cancelled <ts>: <reason>` block from notes,
    or the last non-empty line if the prefix isn't present, or None if notes is empty."""
    if not notes:
        return None
    m = _CANCEL_LINE_RE.search(notes)
    if m:
        return m.group(0)
    for line in reversed(notes.splitlines()):
        if line.strip():
            return line.strip()
    return None

class Status(str, Enum):
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


def is_terminal(status: Status) -> bool:
    return status in (Status.DONE, Status.CANCELLED)

class PlanningStatus(str, Enum):
    PROPOSED = "proposed"
    RATIFIED = "ratified"
    SUPERSEDED = "superseded"

class SliceWorkflowStep(str, Enum):
    SPEC = "spec"
    PLAN = "plan"
    IMPLEMENT = "implement"
    DONE = "done"

class PhaseWorkflowStep(str, Enum):
    SPEC = "spec"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class ReviewStage(str, Enum):
    AWAITING_RESPONSE = "awaiting_response"
    APPLYING_FIXES = "applying_fixes"
    PASSED = "passed"

@dataclass(slots=True)
class BlockedOn:
    kind: Literal["id", "external"]
    value: str

@dataclass(slots=True)
class Reservation:
    resource: str
    value: str
    scope: Literal["phase", "project"] = "phase"
    note: str | None = None

@dataclass(slots=True)
class LedgerReservation:
    resource: str
    value: str
    scope: Literal["phase", "project"]
    note: str | None
    owner_id: str
    owner_phase_id: str
    archived_date: str

@dataclass(slots=True)
class Task:
    id: str
    title: str
    created: str
    started: str | None = None
    status: Status = Status.READY
    closed: str | None = None
    refs: list[str] = field(default_factory=list)
    notes: str = ""

@dataclass(slots=True)
class Slice:
    id: str
    title: str
    created: str
    started: str | None = None
    status: Status = Status.READY
    closed: str | None = None
    blocked_on: BlockedOn | None = None
    depends_on: list[str] = field(default_factory=list)
    planning_status: PlanningStatus = PlanningStatus.PROPOSED
    parallel_group: str | None = None
    plan_path: str | None = None
    refs: list[str] = field(default_factory=list)
    notes: str = ""
    workflow_step: SliceWorkflowStep | None = None
    review_active: bool = False
    review_stage: ReviewStage | None = None
    reviewer_chain: str | None = None
    tasks: list[Task] = field(default_factory=list)
    worktree_path: str | None = None
    worktree_branch: str | None = None
    worktree_in_place: bool = False
    worktree_pruned_at: str | None = None
    worktree_prune_pending: bool = False
    worktree_prune_pending_at: str | None = None
    integration_surfaces: list[str] = field(default_factory=list)
    reservations: list[Reservation] = field(default_factory=list)
    coordination_group: str | None = None
    worktree_base_sha: str | None = None
    landed_base_sha: str | None = None

@dataclass(slots=True)
class Phase:
    id: str
    title: str
    created: str
    started: str | None = None
    status: Status = Status.READY
    closed: str | None = None
    spec_path: str | None = None
    plan_path: str | None = None
    planning_path: str | None = None
    phase_reviewer_chain: str | None = None
    notes: str = ""
    workflow_step: PhaseWorkflowStep | None = None
    slices: list[Slice] = field(default_factory=list)

@dataclass(slots=True)
class CrossCutting:
    id: str
    title: str
    created: str
    started: str | None = None
    status: Status = Status.READY
    closed: str | None = None
    refs: list[str] = field(default_factory=list)
    notes: str = ""
    worktree_path: str | None = None
    worktree_branch: str | None = None
    worktree_in_place: bool = False
    worktree_pruned_at: str | None = None
    worktree_prune_pending: bool = False
    worktree_prune_pending_at: str | None = None

@dataclass(slots=True)
class ArchivedPhase:
    id: str
    title: str
    archived_path: str
    archived_date: str

@dataclass(slots=True)
class ArchivedCrossCutting:
    id: str
    title: str
    archived_path: str
    archived_date: str

@dataclass(slots=True)
class Project:
    project: str
    schema_version: int = SCHEMA_VERSION
    north_star: str = ""
    last_reviewed: str | None = None
    phases: list[Phase] = field(default_factory=list)
    cross_cutting: list[CrossCutting] = field(default_factory=list)
    archived_phases: list[ArchivedPhase] = field(default_factory=list)
    archived_cross_cutting: list[ArchivedCrossCutting] = field(default_factory=list)
    reservations_ledger: list[LedgerReservation] = field(default_factory=list)
