"""Per-slice worktree lifecycle policy (P5.S1).

Pure helpers only — no git mutation, no tasklist mutation. Higher-level
command code in `commands.py` wires these together.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from tasktool.ids import parse_id

_TITLE_TRUNCATE = 40


def _slugify_id(id_value: str) -> str:
    # parse_id raises IdParseError on garbage; do this first so callers get a
    # clean error before we attempt to slugify.
    parse_id(id_value)
    s = id_value.lower().replace(".", "-")
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def _slugify_title(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if len(s) > _TITLE_TRUNCATE:
        cut = s[:_TITLE_TRUNCATE]
        last_dash = cut.rfind("-")
        if last_dash > 0:
            cut = cut[:last_dash]
        s = cut.rstrip("-")
    return s


def worktree_name(id_value: str, title: str) -> str:
    """Return the canonical worktree directory & branch name for (id, title).

    Spec §5.1. Stable, lowercase, deterministic. The same string is used as
    both the directory base name (under `.worktrees/`) and the git branch.
    """
    id_part = _slugify_id(id_value)
    title_part = _slugify_title(title)
    if not title_part:
        return f"worktree-{id_part}"
    return f"worktree-{id_part}-{title_part}"
