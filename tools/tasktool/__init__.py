"""tasktool — JSON-backed task management CLI."""
__version__ = "0.1.0"

from tasktool.model import (
    Project,
    Phase,
    Slice,
    Task,
    CrossCutting,
    BlockedOn,
    Status,
    ArchivedPhase,
    SCHEMA_VERSION,
)
from tasktool.serialize import load_project, save_project, dumps_canonical, loads_project
from tasktool.importer import parse_tasklist_md

__all__ = [
    "__version__",
    "Project",
    "Phase",
    "Slice",
    "Task",
    "CrossCutting",
    "BlockedOn",
    "Status",
    "ArchivedPhase",
    "SCHEMA_VERSION",
    "load_project",
    "save_project",
    "dumps_canonical",
    "loads_project",
    "parse_tasklist_md",
]
