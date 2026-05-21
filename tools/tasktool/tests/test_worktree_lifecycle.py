import subprocess
from pathlib import Path

import pytest

from tasktool.worktree_lifecycle import (
    RecordedState,
    classify_recorded_state,
    is_inside_linked_worktree,
    linked_worktree_branch,
)


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True)


def _repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "T")
    (root / "README.md").write_text("x\n")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "init")
    return root


def test_classify_no_record_returns_absent(tmp_path):
    root = _repo(tmp_path)
    state = classify_recorded_state(root, recorded_path=None, recorded_branch=None)
    assert state == RecordedState.ABSENT


def test_classify_path_and_branch_live_returns_consistent(tmp_path):
    root = _repo(tmp_path)
    wt = tmp_path / "linked"
    _git(root, "worktree", "add", "-b", "feat", str(wt))
    state = classify_recorded_state(root, recorded_path=wt, recorded_branch="feat")
    assert state == RecordedState.CONSISTENT


def test_classify_path_missing_branch_missing_returns_both_missing(tmp_path):
    root = _repo(tmp_path)
    state = classify_recorded_state(
        root,
        recorded_path=tmp_path / "ghost",
        recorded_branch="never-existed",
    )
    assert state == RecordedState.BOTH_MISSING


def test_classify_path_missing_branch_present_returns_path_missing(tmp_path):
    root = _repo(tmp_path)
    _git(root, "branch", "feat")
    state = classify_recorded_state(
        root,
        recorded_path=tmp_path / "ghost",
        recorded_branch="feat",
    )
    assert state == RecordedState.PATH_MISSING


def test_classify_path_present_but_not_worktree_returns_path_not_worktree(tmp_path):
    root = _repo(tmp_path)
    plain = tmp_path / "plain"
    plain.mkdir()
    state = classify_recorded_state(root, recorded_path=plain, recorded_branch="any")
    assert state == RecordedState.PATH_NOT_WORKTREE


def test_classify_path_present_branch_mismatched_returns_branch_mismatch(tmp_path):
    root = _repo(tmp_path)
    wt = tmp_path / "linked"
    _git(root, "worktree", "add", "-b", "feat", str(wt))
    state = classify_recorded_state(root, recorded_path=wt, recorded_branch="other")
    assert state == RecordedState.BRANCH_MISMATCH


def test_linked_worktree_branch_returns_branch(tmp_path):
    root = _repo(tmp_path)
    wt = tmp_path / "linked"
    _git(root, "worktree", "add", "-b", "feat", str(wt))
    assert linked_worktree_branch(root, wt) == "feat"


def test_linked_worktree_branch_returns_none_for_plain_dir(tmp_path):
    root = _repo(tmp_path)
    plain = tmp_path / "plain"
    plain.mkdir()
    assert linked_worktree_branch(root, plain) is None


def test_is_inside_linked_worktree_true_in_linked(tmp_path):
    root = _repo(tmp_path)
    wt = tmp_path / "linked"
    _git(root, "worktree", "add", "-b", "feat", str(wt))
    assert is_inside_linked_worktree(wt) is True


def test_is_inside_linked_worktree_false_in_main_checkout(tmp_path):
    root = _repo(tmp_path)
    assert is_inside_linked_worktree(root) is False
