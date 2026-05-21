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


TASKTOOL = Path(__file__).resolve().parents[1] / "tasktool"


def _tasktool(repo: Path, *args: str, check: bool = True):
    return subprocess.run(
        [str(TASKTOOL), "--project-root", str(repo), *args],
        text=True, capture_output=True, check=check,
    )


@pytest.fixture
def project_with_worktree(tmp_path):
    """Build a project with phase P1, slice S1 in_progress, branch merged, clean."""
    repo = _init_repo(tmp_path / "proj")
    (repo / "docs").mkdir()
    _tasktool(repo, "config", "init-local")
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    _tasktool(repo, "create", "slice", "P1", "--title", "First slice")
    # Simulate P5.S1's start: create a linked worktree and record fields.
    wt_path = repo / ".worktrees" / "worktree-p1-s1-first-slice"
    _run(repo, "git", "worktree", "add", "-b",
         "worktree-p1-s1-first-slice", str(wt_path))
    _tasktool(repo, "start", "P1.S1", "--adopt", str(wt_path))
    return repo, wt_path


def test_prune_refuses_when_slice_in_progress(project_with_worktree):
    repo, _wt = project_with_worktree
    res = _tasktool(repo, "worktree", "prune", "P1.S1", check=False)
    assert res.returncode != 0
    assert "slice" in res.stderr.lower()
    assert "done" in res.stderr.lower() or "in_progress" in res.stderr.lower()


def test_prune_refuses_when_branch_unmerged(project_with_worktree):
    repo, wt = project_with_worktree
    # Diverge the branch so it is not an ancestor of main.
    (wt / "feature.txt").write_text("x")
    _run(wt, "git", "add", "feature.txt")
    _run(wt, "git", "commit", "-q", "-m", "feature work")
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    res = _tasktool(repo, "worktree", "prune", "P1.S1", check=False)
    assert res.returncode != 0
    assert "merged" in res.stderr.lower()


def test_prune_refuses_with_dirty_tracked_file(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    (wt / "dirty.txt").write_text("x")
    res = _tasktool(repo, "worktree", "prune", "P1.S1", check=False)
    assert res.returncode != 0
    assert "clean" in res.stderr.lower() or "dirty" in res.stderr.lower()
    assert "dirty.txt" in res.stderr


def test_prune_refuses_with_untracked_file(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    (wt / "scratch.tmp").write_text("x")
    res = _tasktool(repo, "worktree", "prune", "P1.S1", check=False)
    assert res.returncode != 0
    assert "scratch.tmp" in res.stderr


def test_prune_refuses_with_stash_entry(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    (wt / "x").write_text("x")
    _run(wt, "git", "add", "x")
    _run(wt, "git", "stash", "push", "-u", "-m", "s")
    res = _tasktool(repo, "worktree", "prune", "P1.S1", check=False)
    assert res.returncode != 0
    assert "stash" in res.stderr.lower()


def test_prune_in_place_slice_is_noop_but_records_audit(tmp_path):
    """Spec §5.3.1: prune on an --in-place slice is a no-op on disk but records
    worktree_pruned_at.
    """
    repo = _init_repo(tmp_path / "p")
    (repo / "docs").mkdir()
    _tasktool(repo, "config", "init-local")
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    _tasktool(repo, "create", "slice", "P1", "--title", "Planning slice")
    _tasktool(repo, "start", "P1.S1", "--in-place")
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    res = _tasktool(repo, "worktree", "prune", "P1.S1")
    assert res.returncode == 0
    show = _tasktool(repo, "show", "P1.S1").stdout
    assert "worktree_pruned_at" in show
    # No disk side-effect: no .worktrees dir created.
    assert not (repo / ".worktrees").exists() or not any((repo / ".worktrees").iterdir())


def test_prune_happy_path(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    res = _tasktool(repo, "worktree", "prune", "P1.S1")
    assert res.returncode == 0
    # Worktree directory removed, branch removed.
    assert not wt.exists()
    from tasktool.worktree import branch_exists
    assert branch_exists(repo, "worktree-p1-s1-first-slice") is False
    # Audit fields recorded.
    show = _tasktool(repo, "show", "P1.S1").stdout
    assert "worktree_pruned_at" in show
