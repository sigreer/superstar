"""Read tracker data out of a repo: live file, archive JSON blocks, git replay."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

TRACKER = "docs/tasklist.json"

_PHASE_BLOCK_RE = re.compile(
    r"^## Full phase JSON.*?^```json\n(.*?)^```", re.S | re.M)
_CROSS_BLOCK_RE = re.compile(
    r"^## Full cross-cutting JSON.*?^```json\n(.*?)^```", re.S | re.M)


def git(repo, *args, check=True):
    proc = subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise SystemExit(f"timeline: git {' '.join(args)} failed: "
                         f"{proc.stderr.strip()}")
    return proc.stdout


def repo_root(path):
    return Path(git(path, "rev-parse", "--show-toplevel").strip())


def read_live(repo):
    p = Path(repo) / TRACKER
    if not p.exists():
        raise SystemExit(f"timeline: {p} not found — not a tasktool project")
    return json.loads(p.read_text())


def read_archives(repo):
    """-> (project_docs, x_objects, warnings).

    Reads both '## Full phase JSON' blocks (a project-shaped object whose
    `phases` array holds the archived phase) and '## Full cross-cutting JSON'
    blocks (a single item object). Files with neither block (pure-legacy
    markdown) are ignored — they are backfill.py's input, not ours.
    """
    project_docs, x_objects, warnings = [], [], []
    arch = Path(repo) / "docs" / "archived-tasks"
    files = sorted(arch.glob("*.md")) if arch.is_dir() else []
    for f in files:
        text = f.read_text()
        pm = _PHASE_BLOCK_RE.search(text)
        cm = _CROSS_BLOCK_RE.search(text)
        try:
            if pm:
                project_docs.append(json.loads(pm.group(1)))
            elif cm:
                x_objects.append(json.loads(cm.group(1)))
        except json.JSONDecodeError as e:
            warnings.append(f"{f.name}: unparseable JSON block: {e}")
    return project_docs, x_objects, warnings
