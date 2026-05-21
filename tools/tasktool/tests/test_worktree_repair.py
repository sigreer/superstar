from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tasktool.tests.test_worktree_prune import (
    _init_repo, _run, _tasktool, TASKTOOL,
)


@pytest.fixture
def project_with_missing_worktree(tmp_path):
    repo = _init_repo(tmp_path / "p")
    (repo / "docs").mkdir()
    _tasktool(repo, "config", "init-local")
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    _tasktool(repo, "create", "slice", "P1", "--title", "Slice 1")
    wt_path = repo / ".worktrees" / "worktree-p1-s1-slice-1"
    _run(repo, "git", "worktree", "add", "-b",
         "worktree-p1-s1-slice-1", str(wt_path))
    _tasktool(repo, "start", "P1.S1", "--adopt", str(wt_path))
    # Remove the worktree directory and unregister, but keep the branch.
    _run(repo, "git", "worktree", "remove", "--force", str(wt_path))
    return repo, wt_path


def test_repair_recreates_worktree_when_branch_exists(project_with_missing_worktree):
    repo, wt_path = project_with_missing_worktree
    from tasktool.worktree import branch_exists
    assert branch_exists(repo, "worktree-p1-s1-slice-1") is True
    res = _tasktool(repo, "worktree", "repair", "P1.S1")
    assert res.returncode == 0
    assert wt_path.exists()
    assert (wt_path / ".git").exists()


def test_repair_refuses_when_branch_missing(project_with_missing_worktree):
    repo, _wt = project_with_missing_worktree
    _run(repo, "git", "branch", "-D", "worktree-p1-s1-slice-1")
    res = _tasktool(repo, "worktree", "repair", "P1.S1", check=False)
    assert res.returncode != 0
    assert "branch" in res.stderr.lower() and "missing" in res.stderr.lower()


def test_repair_refuses_when_no_recorded_fields(tmp_path):
    repo = _init_repo(tmp_path / "p")
    (repo / "docs").mkdir()
    _tasktool(repo, "config", "init-local")
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    _tasktool(repo, "create", "slice", "P1", "--title", "Slice 1")
    res = _tasktool(repo, "worktree", "repair", "P1.S1", check=False)
    assert res.returncode != 0


def test_repair_no_op_when_worktree_already_live(tmp_path):
    repo = _init_repo(tmp_path / "p")
    (repo / "docs").mkdir()
    _tasktool(repo, "config", "init-local")
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    _tasktool(repo, "create", "slice", "P1", "--title", "Slice 1")
    wt = repo / ".worktrees" / "worktree-p1-s1-slice-1"
    _run(repo, "git", "worktree", "add", "-b",
         "worktree-p1-s1-slice-1", str(wt))
    _tasktool(repo, "start", "P1.S1", "--adopt", str(wt))
    res = _tasktool(repo, "worktree", "repair", "P1.S1")
    assert res.returncode == 0
    assert wt.exists()
