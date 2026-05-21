from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pytest


def _run(cwd: Path, *args: str) -> str:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True).stdout


def _init_repo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    _run(root, "git", "init", "-q", "-b", "main")
    _run(root, "git", "config", "user.email", "t@example.com")
    _run(root, "git", "config", "user.name", "t")
    (root / "README").write_text("init\n")
    _run(root, "git", "add", "README")
    _run(root, "git", "commit", "-q", "-m", "init")
    return root


def _add_worktree(root: Path, branch: str, path: Path) -> Path:
    _run(root, "git", "worktree", "add", "-b", branch, str(path))
    return path


def test_is_inside_worktree_true(tmp_path):
    from tasktool.worktree import is_inside_worktree
    root = _init_repo(tmp_path / "r")
    wt = _add_worktree(root, "feat", tmp_path / "r" / ".worktrees" / "wt")
    assert is_inside_worktree(wt) is True
    assert is_inside_worktree(root) is False


def test_working_tree_dirty_detects_uncommitted_and_untracked(tmp_path):
    from tasktool.worktree import working_tree_dirty
    root = _init_repo(tmp_path / "r")
    assert working_tree_dirty(root) == (False, [])
    (root / "new.txt").write_text("x")
    dirty, files = working_tree_dirty(root)
    assert dirty is True
    assert "new.txt" in files


def test_working_tree_dirty_flags_stashes_attributable_to_worktree(tmp_path):
    """Spec §5.3: refuse 'stash entries attributable to the worktree'.

    Stashes in git are global to the repository; we cannot attribute them to a
    specific linked worktree, but `git stash list` records the BRANCH at the
    time of stash. A stash made on a different branch is NOT attributable to
    this worktree and must NOT be flagged.
    """
    from tasktool.worktree import working_tree_dirty
    root = _init_repo(tmp_path / "r")
    # Create another branch and stash on it.
    _run(root, "git", "checkout", "-q", "-b", "other")
    (root / "scratch").write_text("x")
    _run(root, "git", "add", "scratch")
    _run(root, "git", "stash", "push", "-u", "-m", "unrelated")
    # Back to main; this worktree's branch is now `main`. The stash above
    # belongs to `other`, not to us, and should NOT be flagged.
    _run(root, "git", "checkout", "-q", "main")
    dirty, files = working_tree_dirty(root)
    assert dirty is False, f"unrelated stash flagged dirty: {files}"


def test_working_tree_dirty_flags_own_branch_stash(tmp_path):
    from tasktool.worktree import working_tree_dirty
    root = _init_repo(tmp_path / "r")
    (root / "scratch").write_text("x")
    _run(root, "git", "add", "scratch")
    _run(root, "git", "stash", "push", "-u", "-m", "ours")
    dirty, files = working_tree_dirty(root)
    assert dirty is True
    assert any("stash" in f.lower() for f in files)


def test_branch_is_merged(tmp_path):
    from tasktool.worktree import branch_is_merged
    root = _init_repo(tmp_path / "r")
    wt = _add_worktree(root, "feat", tmp_path / "r" / ".worktrees" / "wt")
    (wt / "f").write_text("x")
    _run(wt, "git", "add", "f")
    _run(wt, "git", "commit", "-q", "-m", "f")
    assert branch_is_merged(root, branch="feat", into="main") is False
    _run(root, "git", "merge", "--no-ff", "-q", "-m", "m", "feat")
    assert branch_is_merged(root, branch="feat", into="main") is True


def test_head_age_seconds(tmp_path):
    from tasktool.worktree import head_age_seconds
    root = _init_repo(tmp_path / "r")
    age = head_age_seconds(root)
    assert age >= 0
    assert age < 60  # commit was just made


def test_path_is_registered_worktree(tmp_path):
    from tasktool.worktree import path_is_registered_worktree
    root = _init_repo(tmp_path / "r")
    wt = _add_worktree(root, "feat", tmp_path / "r" / ".worktrees" / "wt")
    assert path_is_registered_worktree(root, wt) is True
    assert path_is_registered_worktree(root, tmp_path / "nope") is False


def test_branch_exists(tmp_path):
    from tasktool.worktree import branch_exists
    root = _init_repo(tmp_path / "r")
    assert branch_exists(root, "main") is True
    assert branch_exists(root, "nope") is False
