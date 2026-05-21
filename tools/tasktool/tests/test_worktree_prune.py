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


def test_prune_keep_branch_leaves_branch(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--keep-branch")
    assert res.returncode == 0
    assert not wt.exists()
    from tasktool.worktree import branch_exists
    assert branch_exists(repo, "worktree-p1-s1-first-slice") is True


def _project_with_closed_unmerged(tmp_path):
    repo = _init_repo(tmp_path / "p2")
    (repo / "docs").mkdir()
    _tasktool(repo, "config", "init-local")
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    _tasktool(repo, "create", "slice", "P1", "--title", "First slice")
    wt_path = repo / ".worktrees" / "worktree-p1-s1-first-slice"
    _run(repo, "git", "worktree", "add", "-b",
         "worktree-p1-s1-first-slice", str(wt_path))
    _tasktool(repo, "start", "P1.S1", "--adopt", str(wt_path))
    # Diverge so branch is unmerged.
    (wt_path / "f").write_text("x")
    _run(wt_path, "git", "add", "f")
    _run(wt_path, "git", "commit", "-q", "-m", "work")
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    return repo, wt_path


def test_force_overrides_in_progress_guard(project_with_worktree):
    repo, wt = project_with_worktree
    # Slice still in_progress, no merge.
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--force")
    assert res.returncode == 0
    assert not wt.exists()


def test_force_overrides_unmerged_branch_guard(tmp_path):
    # Build separate project: slice closed but branch never merged.
    repo, wt = _project_with_closed_unmerged(tmp_path)
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--force")
    assert res.returncode == 0


def test_force_overrides_dirty_tree_guard(project_with_worktree):
    repo, wt = project_with_worktree
    (wt / "dirty.txt").write_text("x")
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--force")
    assert res.returncode == 0
    assert not wt.exists()


def test_force_does_not_affect_close_review_gate(project_with_worktree):
    """--force on `prune` must NOT bypass the close review gate.

    The close path is unchanged; --force is scoped to prune guards only.
    """
    repo, _wt = project_with_worktree
    # Attempt to close without --skip-review-gate; --force is not even a
    # close flag, but we re-confirm by checking close's behaviour.
    res = _tasktool(repo, "close", "P1.S1", check=False)
    assert res.returncode != 0
    assert "review" in res.stderr.lower() or "reviewer" in res.stderr.lower()


def test_force_does_not_flip_slice_status(project_with_worktree):
    """After `prune --force` on an in_progress slice, the slice MUST remain
    in_progress. --force is destructive only for the worktree, not for
    lifecycle state."""
    repo, _wt = project_with_worktree
    _tasktool(repo, "worktree", "prune", "P1.S1", "--force")
    show = _tasktool(repo, "show", "P1.S1").stdout
    assert "in_progress" in show
    assert "status: done" not in show.lower()


def test_force_does_not_clear_depends_on(tmp_path):
    """--force prune of one slice must not touch dependent slices' depends_on."""
    repo = _init_repo(tmp_path / "p")
    (repo / "docs").mkdir()
    _tasktool(repo, "config", "init-local")
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    _tasktool(repo, "create", "slice", "P1", "--title", "first")
    _tasktool(repo, "create", "slice", "P1", "--title", "second")
    _tasktool(repo, "deps", "P1.S2", "--add", "P1.S1")
    # Build a worktree for S1 manually.
    wt_path = repo / ".worktrees" / "w"
    _run(repo, "git", "worktree", "add", "-b", "w", str(wt_path))
    _tasktool(repo, "start", "P1.S1", "--adopt", str(wt_path))
    _tasktool(repo, "worktree", "prune", "P1.S1", "--force")
    show = _tasktool(repo, "show", "P1.S2").stdout
    assert "P1.S1" in show  # dependency edge intact


def test_prune_from_inside_sets_pending_marker_and_skips_remove(project_with_worktree, monkeypatch):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    # Invoke prune with cwd inside the doomed worktree.
    res = subprocess.run(
        [str(TASKTOOL), "--project-root", str(repo),
         "worktree", "prune", "P1.S1"],
        cwd=wt, text=True, capture_output=True, check=False,
    )
    assert res.returncode == 0
    # Pending marker set, fields preserved.
    show = _tasktool(repo, "show", "P1.S1").stdout
    assert "worktree_prune_pending" in show
    # Worktree still present.
    assert wt.exists()
    # Exact follow-up line printed.
    assert "git worktree remove" in res.stdout
    assert "tasktool worktree prune P1.S1 --finalize" in res.stdout


def test_finalize_refuses_when_no_pending(project_with_worktree):
    repo, _wt = project_with_worktree
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--finalize", check=False)
    assert res.returncode != 0
    assert "no pending prune" in res.stderr.lower()


def test_finalize_refuses_when_path_still_registered(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    # Trigger prune-from-inside to set pending marker.
    subprocess.run(
        [str(TASKTOOL), "--project-root", str(repo),
         "worktree", "prune", "P1.S1"],
        cwd=wt, text=True, capture_output=True, check=True,
    )
    # Worktree still registered. --finalize must refuse.
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--finalize", check=False)
    assert res.returncode != 0
    assert "still registered" in res.stderr.lower() or "git worktree list" in res.stderr.lower()


def test_finalize_refuses_when_directory_still_present(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    subprocess.run(
        [str(TASKTOOL), "--project-root", str(repo),
         "worktree", "prune", "P1.S1"],
        cwd=wt, text=True, capture_output=True, check=True,
    )
    # Unregister via git but leave the directory present.
    _run(repo, "git", "worktree", "remove", "--force", str(wt))
    # Recreate the directory as a plain dir to simulate leftover state.
    wt.mkdir(parents=True, exist_ok=True)
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--finalize", check=False)
    assert res.returncode != 0
    assert "directory still present" in res.stderr.lower()


def test_finalize_succeeds_when_all_preconditions_met(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    subprocess.run(
        [str(TASKTOOL), "--project-root", str(repo),
         "worktree", "prune", "P1.S1"],
        cwd=wt, text=True, capture_output=True, check=True,
    )
    # Caller performs the destructive step out-of-band.
    _run(repo, "git", "worktree", "remove", str(wt))
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--finalize")
    assert res.returncode == 0
    show = _tasktool(repo, "show", "P1.S1").stdout
    assert "worktree_pruned_at" in show
    assert "worktree_prune_pending" not in show or "false" in show.lower()


def test_prune_emits_recent_head_note_but_succeeds(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    # Create a fresh commit in the worktree before merging again to advance HEAD;
    # since branch is already merged into main as a separate ref, refresh the HEAD
    # timestamp on the worktree by amending.
    _run(wt, "git", "commit", "--allow-empty", "-q",
         "--amend", "--no-edit", "--date=now")
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--force",
                    check=False)
    assert res.returncode == 0
    assert "HEAD moved" in res.stderr
