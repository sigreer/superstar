from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
PYTHONPATH = str(Path(__file__).resolve().parents[2])


def run(root: Path, *args: str):
    env = os.environ.copy()
    env["PYTHONPATH"] = PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
    env["GIT_EDITOR"] = "false"
    return subprocess.run(
        [sys.executable, str(TOOL), "--project-root", str(root), *args],
        text=True,
        capture_output=True,
        env=env,
    )


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, text=True, capture_output=True, check=True
    ).stdout


def init_repo(root: Path) -> Path:
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@example.invalid")
    git(root, "config", "user.name", "T")
    (root / "docs").mkdir()
    assert run(root, "config", "init-local").returncode == 0
    assert run(root, "init", "--project", "demo").returncode == 0
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "init")
    assert run(root, "create", "phase", "--title", "Phase 1").returncode == 0
    assert run(root, "create", "slice", "P1", "--title", "Sync target").returncode == 0
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "seed slice")
    return root


def slice_row(repo: Path, qid: str = "P1.S1") -> dict:
    data = json.loads((repo / "docs" / "tasklist.json").read_text())
    return next(
        s for ph in data["phases"] for s in ph["slices"]
        if f"{ph['id']}.{s['id']}" == qid
    )


def start_linked(repo: Path) -> Path:
    r = run(repo, "start", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    return (repo / slice_row(repo)["worktree_path"]).resolve()


def advance_main(repo: Path, name: str, content: str = "x") -> str:
    (repo / name).write_text(content + "\n")
    git(repo, "add", name)
    git(repo, "commit", "-q", "-m", f"main {name}")
    return git(repo, "rev-parse", "main").strip()


def test_sync_requires_exactly_one_strategy(tmp_path):
    repo = init_repo(tmp_path / "repo")
    no_strategy = run(repo, "worktree", "sync", "P1.S1")
    assert no_strategy.returncode != 0
    assert "one of the arguments --merge --rebase is required" in no_strategy.stderr
    both = run(repo, "worktree", "sync", "P1.S1", "--merge", "--rebase")
    assert both.returncode != 0
    assert "not allowed with argument" in both.stderr


def test_dirty_helper_allows_staged_tasklist_only(tmp_path):
    from tasktool.worktree import working_tree_dirty_for_sync
    repo = init_repo(tmp_path / "repo")
    data = json.loads((repo / "docs" / "tasklist.json").read_text())
    data["north_star"] = "staged tracker update"
    (repo / "docs" / "tasklist.json").write_text(json.dumps(data, indent=2) + "\n")
    git(repo, "add", "docs/tasklist.json")
    dirty, items = working_tree_dirty_for_sync(repo, allow_staged_tasklist=True)
    assert dirty is False, items


def test_dirty_helper_refuses_staged_tasklist_deletion(tmp_path):
    from tasktool.worktree import working_tree_dirty_for_sync
    repo = init_repo(tmp_path / "repo")
    git(repo, "rm", "docs/tasklist.json")
    dirty, items = working_tree_dirty_for_sync(repo, allow_staged_tasklist=True)
    assert dirty is True
    assert "docs/tasklist.json" in items


def test_dirty_helper_refuses_unstaged_tasklist_and_untracked_files(tmp_path):
    from tasktool.worktree import working_tree_dirty_for_sync
    repo = init_repo(tmp_path / "repo")
    data = json.loads((repo / "docs" / "tasklist.json").read_text())
    data["north_star"] = "unstaged tracker update"
    (repo / "docs" / "tasklist.json").write_text(json.dumps(data, indent=2) + "\n")
    dirty, items = working_tree_dirty_for_sync(repo, allow_staged_tasklist=True)
    assert dirty is True
    assert "docs/tasklist.json" in items
    git(repo, "add", "docs/tasklist.json")
    (repo / "scratch.txt").write_text("scratch\n")
    dirty, items = working_tree_dirty_for_sync(repo, allow_staged_tasklist=True)
    assert dirty is True
    assert "scratch.txt" in items
