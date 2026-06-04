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


def test_sync_refuses_missing_worktree_base_sha(tmp_path):
    repo = init_repo(tmp_path / "repo")
    start_linked(repo)
    path = repo / "docs" / "tasklist.json"
    data = json.loads(path.read_text())
    data["phases"][0]["slices"][0].pop("worktree_base_sha", None)
    path.write_text(json.dumps(data, indent=2) + "\n")
    git(repo, "add", "docs/tasklist.json")
    r = run(repo, "worktree", "sync", "P1.S1", "--merge")
    assert r.returncode != 0
    assert "worktree_base_sha" in (r.stdout + r.stderr)


def test_sync_refuses_non_slice_id(tmp_path):
    repo = init_repo(tmp_path / "repo")
    r = run(repo, "worktree", "sync", "P1", "--merge")
    assert r.returncode != 0
    assert "worktree sync only supports slices" in (r.stdout + r.stderr)


def test_sync_refuses_unhealthy_recorded_worktree(tmp_path):
    repo = init_repo(tmp_path / "repo")
    wt = start_linked(repo)
    git(repo, "worktree", "remove", "--force", str(wt))
    r = run(repo, "worktree", "sync", "P1.S1", "--merge")
    assert r.returncode != 0
    assert "recorded worktree is not live" in (r.stdout + r.stderr)


def test_sync_refuses_dirty_linked_worktree(tmp_path):
    repo = init_repo(tmp_path / "repo")
    wt = start_linked(repo)
    advance_main(repo, "base-change")
    (wt / "dirty.txt").write_text("dirty\n")
    r = run(repo, "worktree", "sync", "P1.S1", "--merge")
    assert r.returncode != 0
    assert "not clean" in (r.stdout + r.stderr)
    assert "dirty.txt" in (r.stdout + r.stderr)


def test_sync_refuses_unstaged_authoritative_tasklist(tmp_path):
    repo = init_repo(tmp_path / "repo")
    start_linked(repo)
    advance_main(repo, "base-change")
    data = json.loads((repo / "docs" / "tasklist.json").read_text())
    data["north_star"] = "unstaged"
    (repo / "docs" / "tasklist.json").write_text(json.dumps(data, indent=2) + "\n")
    r = run(repo, "worktree", "sync", "P1.S1", "--merge")
    assert r.returncode != 0
    assert "docs/tasklist.json has unstaged changes" in (r.stdout + r.stderr)


def test_sync_merge_integrates_captured_base_sha_and_advances_row(tmp_path):
    repo = init_repo(tmp_path / "repo")
    wt = start_linked(repo)
    base_head = advance_main(repo, "base-change", "base")
    (wt / "slice-work").write_text("slice\n")
    git(wt, "add", "slice-work")
    git(wt, "commit", "-q", "-m", "slice work")
    old_base = slice_row(repo)["worktree_base_sha"]
    r = run(repo, "worktree", "sync", "P1.S1", "--merge")
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"integrated main at {base_head}" in r.stdout
    assert slice_row(repo)["worktree_base_sha"] == base_head
    assert slice_row(repo)["worktree_base_sha"] != old_base
    assert (wt / "base-change").read_text() == "base\n"


def test_sync_rebase_integrates_captured_base_sha_and_advances_row(tmp_path):
    repo = init_repo(tmp_path / "repo")
    wt = start_linked(repo)
    base_head = advance_main(repo, "base-change", "base")
    (wt / "slice-work").write_text("slice\n")
    git(wt, "add", "slice-work")
    git(wt, "commit", "-q", "-m", "slice work")
    r = run(repo, "worktree", "sync", "P1.S1", "--rebase")
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"integrated main at {base_head}" in r.stdout
    assert slice_row(repo)["worktree_base_sha"] == base_head
    assert (wt / "base-change").read_text() == "base\n"


def test_sync_merge_non_fast_forward_is_non_interactive(tmp_path):
    repo = init_repo(tmp_path / "repo")
    wt = start_linked(repo)
    advance_main(repo, "main-only", "base")
    (wt / "slice-only").write_text("slice\n")
    git(wt, "add", "slice-only")
    git(wt, "commit", "-q", "-m", "slice work")
    r = run(repo, "worktree", "sync", "P1.S1", "--merge")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "follow-up:" in r.stdout
    log = git(wt, "log", "-1", "--format=%s").strip()
    assert log.startswith("Merge")
