from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG_REL = Path(".tasktool/config.json")
VALID_MUTATION_MODES = {"local", "authoritative-checkout"}


@dataclass(frozen=True)
class TasklistConfig:
    mutation_mode: str = "local"
    authoritative_branch: str = "main"


@dataclass(frozen=True)
class TasktoolConfig:
    schema_version: int = 1
    tasklist: TasklistConfig = field(default_factory=TasklistConfig)


def _parse_tasklist(raw: dict) -> TasklistConfig:
    mode = raw.get("mutation_mode", "local")
    if mode not in VALID_MUTATION_MODES:
        raise ValueError(f"unknown mutation_mode: {mode}")
    return TasklistConfig(
        mutation_mode=mode,
        authoritative_branch=raw.get("authoritative_branch", "main"),
    )


def load_config(repo_root: Path) -> TasktoolConfig:
    path = repo_root / DEFAULT_CONFIG_REL
    if not path.exists():
        return TasktoolConfig()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema_version", 1) != 1:
        raise ValueError(f"unsupported tasktool config schema_version: {raw.get('schema_version')}")
    return TasktoolConfig(
        schema_version=1,
        tasklist=_parse_tasklist(raw.get("tasklist", {})),
    )


def save_config(repo_root: Path, cfg: TasktoolConfig) -> None:
    path = repo_root / DEFAULT_CONFIG_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "schema_version": cfg.schema_version,
        "tasklist": {
            "mutation_mode": cfg.tasklist.mutation_mode,
            "authoritative_branch": cfg.tasklist.authoritative_branch,
        },
    }
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
