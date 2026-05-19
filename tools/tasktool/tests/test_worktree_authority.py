import os
import subprocess
from pathlib import Path

from tasktool.worktree import (
    AuthorityError,
    find_authoritative_root,
    git_common_dir,
    git_current_branch,
    same_repository,
    tasklist_has_unsafe_dirty_state,
    validate_authoritative_checkout,
)


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True)


def _repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "tasktool-tests@example.invalid")
    _git(root, "config", "user.name", "Tasktool Tests")
    (root / "README.md").write_text("x\n")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "init")
    return root


def test_git_common_dir_is_shared_by_linked_worktree(tmp_path):
    root = _repo(tmp_path)
    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    assert git_common_dir(root) == git_common_dir(worker)


def test_validate_authoritative_checkout_rejects_wrong_branch(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-b", "other")
    try:
        validate_authoritative_checkout(root, expected_branch="main", caller_root=root)
    except AuthorityError as exc:
        assert "expected branch main" in str(exc)
    else:
        raise AssertionError("expected AuthorityError")


def test_same_repository_true_for_linked_worktree(tmp_path):
    root = _repo(tmp_path)
    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    assert same_repository(root, worker)


def test_find_authoritative_root_uses_branch_worktree(tmp_path):
    root = _repo(tmp_path)
    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    assert find_authoritative_root(worker, branch="main") == root


def test_find_authoritative_root_fails_closed_when_missing(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-b", "feature")
    try:
        find_authoritative_root(root, branch="main")
    except AuthorityError as exc:
        assert "TASKTOOL_AUTHORITY_ROOT" in str(exc)
    else:
        raise AssertionError("expected AuthorityError")


def test_validate_authoritative_checkout_permits_dirty_tasklist_check_to_caller(tmp_path):
    root = _repo(tmp_path)
    (root / "docs").mkdir()
    (root / "docs" / "tasklist.json").write_text("{}\n")
    assert validate_authoritative_checkout(root, expected_branch="main", caller_root=root) is None


def test_unsafe_tasklist_dirty_state_detects_unstaged_bytes(tmp_path):
    root = _repo(tmp_path)
    (root / "docs").mkdir()
    (root / "docs" / "tasklist.json").write_text("{}\n")
    _git(root, "add", "docs/tasklist.json")
    assert tasklist_has_unsafe_dirty_state(root) is False
    (root / "docs" / "tasklist.json").write_text('{"changed":true}\n')
    assert tasklist_has_unsafe_dirty_state(root) is True
