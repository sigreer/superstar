# tools/tasktool/schema_gen.py
"""Generate a JSON Schema (draft 2020-12) describing tasklist.json."""
from __future__ import annotations
import json
from tasktool.model import SCHEMA_VERSION

def build_schema() -> dict:
    task_status_enum = ["ready", "in_progress", "done"]
    phase_status_enum = ["ready", "in_progress", "done", "cancelled"]
    cross_status_enum = ["ready", "in_progress", "done", "cancelled"]
    slice_status_enum = ["ready", "in_progress", "blocked", "done", "cancelled"]
    planning_status_enum = ["proposed", "ratified", "superseded"]
    date_str = {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"}
    nullable_date = {"oneOf": [date_str, {"type": "null"}]}
    blocked_on = {
        "oneOf": [
            {"type": "null"},
            {
                "type": "object",
                "required": ["kind", "value"],
                "properties": {
                    "kind": {"enum": ["id", "external"]},
                    "value": {"type": "string"},
                },
                "additionalProperties": False,
            },
        ],
    }
    task = {
        "type": "object",
        "required": ["id", "title", "created", "status"],
        "properties": {
            "id": {"type": "string", "pattern": r"^T\d+$"},
            "title": {"type": "string"},
            "created": date_str,
            "started": nullable_date,
            "status": {"enum": task_status_enum},
            "closed": nullable_date,
            "refs": {"type": "array", "items": {"type": "string"}},
            "notes": {"type": "string"},
        },
        "additionalProperties": False,
    }
    slice_ = {
        "type": "object",
        "required": ["id", "title", "created", "status"],
        "properties": {
            "id": {"type": "string", "pattern": r"^S\d+[a-z]?$"},
            "title": {"type": "string"},
            "created": date_str,
            "started": nullable_date,
            "status": {"enum": slice_status_enum},
            "closed": nullable_date,
            "blocked_on": blocked_on,
            "depends_on": {"type": "array", "items": {"type": "string"}},
            "planning_status": {"enum": planning_status_enum},
            "parallel_group": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "plan_path": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "refs": {"type": "array", "items": {"type": "string"}},
            "notes": {"type": "string"},
            "reviewer_chain": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "tasks": {"type": "array", "items": task},
            "worktree_path": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "worktree_branch": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "worktree_in_place": {"type": "boolean"},
            "worktree_pruned_at": {"oneOf": [date_str, {"type": "null"}]},
            "worktree_prune_pending": {"type": "boolean"},
            "worktree_prune_pending_at": {"oneOf": [date_str, {"type": "null"}]},
        },
        "additionalProperties": False,
    }
    phase = {
        "type": "object",
        "required": ["id", "title", "created", "status"],
        "properties": {
            "id": {"type": "string", "pattern": r"^P\d+$"},
            "title": {"type": "string"},
            "created": date_str,
            "started": nullable_date,
            "status": {"enum": phase_status_enum},
            "closed": nullable_date,
            "spec_path": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "plan_path": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "planning_path": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "phase_reviewer_chain": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "notes": {"type": "string"},
            "slices": {"type": "array", "items": slice_},
        },
        "additionalProperties": False,
    }
    cross = {
        "type": "object",
        "required": ["id", "title", "created", "status"],
        "properties": {
            "id": {"type": "string", "pattern": r"^X\d+$"},
            "title": {"type": "string"},
            "created": date_str,
            "started": nullable_date,
            "status": {"enum": cross_status_enum},
            "closed": nullable_date,
            "refs": {"type": "array", "items": {"type": "string"}},
            "notes": {"type": "string"},
            "worktree_path": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "worktree_branch": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "worktree_in_place": {"type": "boolean"},
            "worktree_pruned_at": {"oneOf": [date_str, {"type": "null"}]},
            "worktree_prune_pending": {"type": "boolean"},
            "worktree_prune_pending_at": {"oneOf": [date_str, {"type": "null"}]},
        },
        "additionalProperties": False,
    }
    archived = {
        "type": "object",
        "required": ["id", "title", "archived_path", "archived_date"],
        "properties": {
            "id": {"type": "string"},
            "title": {"type": "string"},
            "archived_path": {"type": "string"},
            "archived_date": date_str,
        },
        "additionalProperties": False,
    }
    archived_cross = {
        "type": "object",
        "required": ["id", "title", "archived_path", "archived_date"],
        "properties": {
            "id": {"type": "string", "pattern": r"^X\d+$"},
            "title": {"type": "string"},
            "archived_path": {"type": "string"},
            "archived_date": date_str,
        },
        "additionalProperties": False,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "tasktool tasklist.json",
        "type": "object",
        "required": ["project", "schema_version"],
        "properties": {
            "schema_version": {"const": SCHEMA_VERSION},
            "project": {"type": "string"},
            "north_star": {"type": "string"},
            "last_reviewed": {"oneOf": [date_str, {"type": "null"}]},
            "phases": {"type": "array", "items": phase},
            "cross_cutting": {"type": "array", "items": cross},
            "archived_phases": {"type": "array", "items": archived},
            "archived_cross_cutting": {"type": "array", "items": archived_cross},
        },
        "additionalProperties": False,
    }

def dump_schema() -> str:
    return json.dumps(build_schema(), indent=2, sort_keys=True) + "\n"
