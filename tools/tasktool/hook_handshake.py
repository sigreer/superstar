"""Startup handshake for the tasktool <-> pre-commit hook version stamp.

Returns an error message string if the installed hook is stale relative to the
Superstar source declared in its stamped header. Returns None for all other
states (no repo, no hook, non-tasktool hook, missing source VERSION).

Cheap: a couple of subprocess.run + Path.exists + a short read_text. Called
unconditionally from cli.main; silent on the happy path.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Optional

_HEADER_KEYS = (
    "superstar-hook-name",
    "superstar-hook-version",
    "superstar-hook-source-root",
)
_HEADER_RE = re.compile(r"^#\s*([a-z][a-z0-9-]*):\s*(.+?)\s*$")


def _git_top(cwd: Path) -> Optional[Path]:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def _parse_header(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines()[:32]:
        m = _HEADER_RE.match(line)
        if not m:
            continue
        out[m.group(1)] = m.group(2)
    return out


def _expand_path(value: str) -> str:
    return os.path.expanduser(os.path.expandvars(value))


def check_pre_commit_hook(cwd: Optional[Path] = None) -> Optional[str]:
    cwd = cwd or Path.cwd()
    repo_top = _git_top(cwd)
    if repo_top is None:
        return None
    hook_path = repo_top / ".git" / "hooks" / "pre-commit"
    if not hook_path.exists():
        return None
    try:
        header = _parse_header(hook_path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return None
    if header.get("superstar-hook-name") != "tasktool-pre-commit":
        return None
    hook_version = header.get("superstar-hook-version", "").strip()
    source_root_raw = header.get("superstar-hook-source-root", "").strip()
    if not hook_version or not source_root_raw:
        return None
    source_root = Path(_expand_path(source_root_raw))
    version_file = source_root / "VERSION"
    try:
        src_version = version_file.read_text(encoding="utf-8").splitlines()[0].strip()
    except (OSError, IndexError):
        return None
    if not src_version or src_version == hook_version:
        return None
    return (
        f"ERROR: tasktool pre-commit hook is {hook_version} but Superstar source is {src_version}\n"
        f"Hook: {hook_path}\n"
        f"Re-run: bash {source_root}/tools/tasktool/install.sh --hook --force"
    )
