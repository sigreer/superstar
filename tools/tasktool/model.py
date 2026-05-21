from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

SCHEMA_VERSION = 1

class Status(str, Enum):
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"

class PlanningStatus(str, Enum):
    PROPOSED = "proposed"
    RATIFIED = "ratified"
    SUPERSEDED = "superseded"

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
    reviewer_chain: str | None = None
    tasks: list[Task] = field(default_factory=list)

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
