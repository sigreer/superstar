from __future__ import annotations

import json
import subprocess
from pathlib import Path

TASKTOOL = Path(__file__).resolve().parents[1] / "tasktool"


def _run(cwd: Path, *args: str) -> str:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True).stdout


def _tasktool(repo: Path, *args: str, check: bool = True):
    return subprocess.run(
        [str(TASKTOOL), "--project-root", str(repo), *args],
        text=True, capture_output=True, check=check,
    )


def _init_repo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    _run(root, "git", "init", "-q", "-b", "main")
    _run(root, "git", "config", "user.email", "t@example.com")
    _run(root, "git", "config", "user.name", "t")
    (root / "README").write_text("init\n")
    _run(root, "git", "add", "README")
    _run(root, "git", "commit", "-q", "-m", "init")
    return root


def _seed(repo: Path, *slice_titles: str) -> None:
    (repo / "docs").mkdir(exist_ok=True)
    _tasktool(repo, "config", "init-local")
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    for title in slice_titles:
        _tasktool(repo, "create", "slice", "P1", "--title", title)
    _run(repo, "git", "add", "-A")
    _run(repo, "git", "commit", "-q", "-m", "seed")


def test_integration_reports_base_ahead_count(tmp_path):
    repo = _init_repo(tmp_path / "proj")
    _seed(repo, "First slice")
    _tasktool(repo, "start", "P1.S1")  # records worktree_base_sha at current main
    # Advance main by two commits after the worktree branched.
    (repo / "x").write_text("1")
    _run(repo, "git", "add", "x")
    _run(repo, "git", "commit", "-q", "-m", "x")
    (repo / "y").write_text("2")
    _run(repo, "git", "add", "y")
    _run(repo, "git", "commit", "-q", "-m", "y")
    out = _tasktool(repo, "worktree", "status", "P1.S1", "--integration").stdout
    assert "base ahead of worktree_base_sha: 2 commit" in out
