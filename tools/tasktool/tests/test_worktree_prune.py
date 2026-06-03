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


def test_ad_hoc_lifecycle_close_without_no_archive_breaks_prune(tmp_path):
    """Spec §5.3: default `close` on a cross-cutting row auto-archives, which
    destroys worktree fields before prune can find them. This is the foot-gun
    `start --ad-hoc` requires `--no-archive` to avoid.
    """
    repo = _init_repo(tmp_path / "p")
    (repo / "docs").mkdir()
    _tasktool(repo, "config", "init-local")
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "start", "--ad-hoc", "explore")
    # Discover the allocated ID by reading tasktool list.
    # Ad-hoc cross rows are hidden by default; use --all to list them.
    listing = _tasktool(repo, "list", "--kind", "cross", "--all").stdout
    xid = _extract_xid(listing, title_contains="Ad-hoc: explore")
    assert xid is not None
    # Foot-gun: close without --no-archive auto-archives.
    _tasktool(repo, "close", xid)
    # Now prune cannot find the row.
    res = _tasktool(repo, "worktree", "prune", xid, check=False)
    assert res.returncode != 0


def test_ad_hoc_lifecycle_full_flow_with_no_archive(tmp_path):
    repo = _init_repo(tmp_path / "p")
    (repo / "docs").mkdir()
    _tasktool(repo, "config", "init-local")
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "start", "--ad-hoc", "hotfix")
    # Ad-hoc cross rows are hidden by default; use --all to list them.
    listing = _tasktool(repo, "list", "--kind", "cross", "--all").stdout
    xid = _extract_xid(listing, title_contains="Ad-hoc: hotfix")
    assert xid is not None
    # Recorded worktree path.
    show = _tasktool(repo, "show", xid).stdout
    assert "worktree_path" in show
    # Step 1: close with --no-archive.
    _tasktool(repo, "close", xid, "--no-archive")
    # Step 2: prune (no merge required for ad-hoc by spec? — spec defers to
    # standard three-guard prune. For this test we force-prune because the
    # ad-hoc branch is not merged into main).
    _tasktool(repo, "worktree", "prune", xid, "--force")
    # Step 3: archive-cross.
    _tasktool(repo, "archive-cross", xid)
    # archive-cross moves the row from `cross_cutting` to `archived_cross_cutting`.
    # `tasktool list --kind cross` lists active cross rows; the archived row will
    # NOT appear there. Verify the archive by reading tasklist.json directly.
    import json
    data = json.loads((repo / "docs" / "tasklist.json").read_text())
    archived_ids = [a["id"] for a in data.get("archived_cross_cutting", [])]
    assert xid in archived_ids


def test_worktree_prune_accepts_cancelled_slice_without_force(project_with_worktree):
    """X22: a clean worktree on a cancelled slice prunes without --force.

    The terminal precondition that previously required Status.DONE now accepts
    any terminal status (done OR cancelled).
    """
    repo, wt = project_with_worktree
    # Merge the branch so guard 2 passes without --force.
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    # Cancel the slice instead of closing it.
    _tasktool(repo, "cancel", "P1.S1", "--reason", "dropped")
    res = _tasktool(repo, "worktree", "prune", "P1.S1", check=False)
    assert res.returncode == 0, (
        f"expected prune to succeed for cancelled slice; "
        f"stderr={res.stderr!r}, stdout={res.stdout!r}"
    )
    assert not wt.exists()


def _extract_xid(listing: str, *, title_contains: str) -> str | None:
    import re
    for line in listing.splitlines():
        if title_contains in line:
            m = re.search(r"\b(X\d+)\b", line)
            if m:
                return m.group(1)
    return None


def test_current_branch_head_sha_matches_rev_parse(tmp_path):
    from tasktool.worktree import current_branch_head_sha
    root = _init_repo(tmp_path / "r")
    expected = _run(root, "git", "rev-parse", "main").strip()
    assert current_branch_head_sha(root, "main") == expected
    assert len(current_branch_head_sha(root, "main")) == 40


def test_merge_base_sha_returns_fork_point(tmp_path):
    from tasktool.worktree import merge_base_sha
    root = _init_repo(tmp_path / "r")
    fork = _run(root, "git", "rev-parse", "main").strip()
    _run(root, "git", "checkout", "-q", "-b", "feat")
    (root / "a").write_text("a")
    _run(root, "git", "add", "a")
    _run(root, "git", "commit", "-q", "-m", "feat work")
    _run(root, "git", "checkout", "-q", "main")
    (root / "b").write_text("b")
    _run(root, "git", "add", "b")
    _run(root, "git", "commit", "-q", "-m", "main work")
    assert merge_base_sha(root, "feat", "main") == fork


def test_rev_list_helpers_count_window_and_membership(tmp_path):
    from tasktool.worktree import rev_list_count, rev_list_shas, commit_is_in_range
    root = _init_repo(tmp_path / "r")
    base = _run(root, "git", "rev-parse", "main").strip()
    (root / "c1").write_text("1")
    _run(root, "git", "add", "c1")
    _run(root, "git", "commit", "-q", "-m", "c1")
    mid = _run(root, "git", "rev-parse", "main").strip()
    (root / "c2").write_text("2")
    _run(root, "git", "add", "c2")
    _run(root, "git", "commit", "-q", "-m", "c2")
    head = _run(root, "git", "rev-parse", "main").strip()
    # base..head spans exactly the two new commits.
    assert rev_list_count(root, base, head) == 2
    shas = rev_list_shas(root, base, head)
    assert head in shas and mid in shas and base not in shas
    # `mid` is reachable from head but not from base -> in range.
    assert commit_is_in_range(root, mid, base=base, head=head) is True
    # `base` itself is excluded by the half-open A..B window.
    assert commit_is_in_range(root, base, base=base, head=head) is False


def test_prune_stamps_landed_base_sha_on_merged_done_slice(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    base_head = _run(repo, "git", "rev-parse", "main").strip()
    res = _tasktool(repo, "worktree", "prune", "P1.S1")
    assert res.returncode == 0
    show = _tasktool(repo, "show", "P1.S1").stdout
    assert f"landed_base_sha: {base_head}" in show


def test_prune_does_not_stamp_landed_base_sha_for_cancelled_slice(project_with_worktree):
    repo, wt = project_with_worktree
    # Merge so the branch-merged guard would pass, then cancel (not close).
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    _tasktool(repo, "cancel", "P1.S1", "--reason", "dropped")
    res = _tasktool(repo, "worktree", "prune", "P1.S1")
    assert res.returncode == 0
    show = _tasktool(repo, "show", "P1.S1").stdout
    assert "landed_base_sha:" not in show


def test_force_prune_unmerged_does_not_stamp_landed_base_sha(tmp_path):
    repo, wt = _project_with_closed_unmerged(tmp_path)  # done but branch unmerged
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--force")
    assert res.returncode == 0
    show = _tasktool(repo, "show", "P1.S1").stdout
    assert "landed_base_sha:" not in show


def test_finalize_only_does_not_stamp_landed_base_sha(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    # Trigger the prune-from-inside pending path (defers, never stamps).
    subprocess.run(
        [str(TASKTOOL), "--project-root", str(repo),
         "worktree", "prune", "P1.S1"],
        cwd=wt, text=True, capture_output=True, check=True,
    )
    # Caller performs the destructive removal out-of-band, then finalizes.
    _run(repo, "git", "worktree", "remove", str(wt))
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--finalize")
    assert res.returncode == 0
    show = _tasktool(repo, "show", "P1.S1").stdout
    assert "landed_base_sha:" not in show
