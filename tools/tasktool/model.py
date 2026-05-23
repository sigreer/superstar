from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

SCHEMA_VERSION = 2

class Status(str, Enum):
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"

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
