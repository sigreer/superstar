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

import enum


class RecordedState(enum.Enum):
    """Outcome of comparing the recorded worktree_path/branch against live filesystem state.

    Spec §5.3 idempotent-reuse table. CONSISTENT means `start` is a no-op;
    every other variant requires explicit operator action (refused with a
    targeted error message in `cmd_start`).
    """
    ABSENT = "absent"                       # No path recorded; start should create.
    CONSISTENT = "consistent"               # Path is a linked worktree, branch matches.
    BOTH_MISSING = "both_missing"           # Path gone, branch gone — repair.
    PATH_MISSING = "path_missing"           # Path gone, branch still present — adopt/repair.
    PATH_NOT_WORKTREE = "path_not_worktree" # Plain dir at recorded path — refuse.
    BRANCH_MISMATCH = "branch_mismatch"     # Linked worktree, wrong branch — refuse.


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=check
    )


def linked_worktree_branch(authoritative_root: Path, candidate: Path) -> str | None:
    """Return the branch checked out at `candidate` if it is a linked worktree of
    `authoritative_root`, else None. Resolution uses `git worktree list --porcelain`."""
    if not candidate.exists():
        return None
    candidate = candidate.resolve()
    result = _git(authoritative_root, "worktree", "list", "--porcelain")
    current_path: Path | None = None
    current_branch: str = ""
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            if current_path is not None and current_path == candidate:
                return current_branch or None
            current_path = Path(line.removeprefix("worktree ")).resolve()
            current_branch = ""
        elif line.startswith("branch "):
            current_branch = line.removeprefix("branch refs/heads/")
    if current_path is not None and current_path == candidate:
        return current_branch or None
    return None


def _branch_exists(root: Path, branch: str) -> bool:
    res = _git(root, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False)
    return res.returncode == 0


def classify_recorded_state(
    authoritative_root: Path,
    *,
    recorded_path: Path | None,
    recorded_branch: str | None,
) -> RecordedState:
    """Classify the live state of a recorded worktree against the filesystem.

    Spec §5.3 idempotent-reuse table. `recorded_path`/`recorded_branch` must
    either both be set or both be None.
    """
    if recorded_path is None and recorded_branch is None:
        return RecordedState.ABSENT
    assert recorded_path is not None and recorded_branch is not None
    path_exists = recorded_path.exists()
    branch_exists = _branch_exists(authoritative_root, recorded_branch)
    if not path_exists and not branch_exists:
        return RecordedState.BOTH_MISSING
    if not path_exists and branch_exists:
        return RecordedState.PATH_MISSING
    # Path exists.
    live_branch = linked_worktree_branch(authoritative_root, recorded_path)
    if live_branch is None:
        return RecordedState.PATH_NOT_WORKTREE
    if live_branch == recorded_branch:
        return RecordedState.CONSISTENT
    return RecordedState.BRANCH_MISMATCH


def is_inside_linked_worktree(cwd: Path) -> bool:
    """True when `cwd` is inside a linked git worktree (not the main checkout).

    Detected by `git rev-parse --git-dir` differing from `--git-common-dir`.
    Returns False outside any git repository.
    """
    try:
        gd = subprocess.run(
            ["git", "rev-parse", "--git-dir"], cwd=cwd, text=True,
            capture_output=True, check=True,
        ).stdout.strip()
        cd = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"], cwd=cwd, text=True,
            capture_output=True, check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return False
    return Path(gd).resolve() != Path(cd).resolve()


def legacy_worktree_dirs(
    repo_root: Path,
    *,
    home: Path,
    project_name: str,
) -> list[Path]:
    """Return any legacy per-harness worktree directories that exist.

    Spec §5.4. Used by `project-setup` to warn the operator. Tasktool does
    NOT delete or move anything — this is detection only. Removal is
    scheduled one minor version after P5 ships.
    """
    candidates = [
        repo_root / ".claude" / "worktrees",
        repo_root / ".codex" / "worktrees",
        home / ".config" / "superstar" / "worktrees" / project_name,
    ]
    return [c for c in candidates if c.exists()]


def ensure_gitignore_entry(repo_root: Path, *, entry: str = ".worktrees/") -> bool:
    """Ensure `entry` (default `.worktrees/`) is a literal line in `<repo>/.gitignore`.

    Idempotent: returns True when the file was created or the line was appended,
    False when the line was already present. Used by `project-setup` row 1d.
    """
    gi = repo_root / ".gitignore"
    if not gi.exists():
        gi.write_text(entry + "\n")
        return True
    text = gi.read_text()
    lines = text.splitlines()
    if any(line.strip() == entry.rstrip("/") or line.strip() == entry for line in lines):
        return False
    sep = "" if text.endswith("\n") else "\n"
    gi.write_text(text + sep + entry + "\n")
    return True
