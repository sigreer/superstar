import json
import os
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
PYTHONPATH = str(Path(__file__).resolve().parents[2])


def run(root, *args):
    env = os.environ.copy()
    env["PYTHONPATH"] = PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, str(TOOL), "--project-root", str(root), *args],
        text=True, capture_output=True, env=env,
    )


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True)


def seed_with_started_slice(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "T")
    (root / "docs").mkdir()
    assert run(root, "config", "init-local").returncode == 0
    assert run(root, "init", "--project", "demo").returncode == 0
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "init")
    assert run(root, "create", "phase", "--title", "P").returncode == 0
    assert run(root, "create", "slice", "P1", "--title", "Slice one").returncode == 0
    assert run(root, "start", "P1.S1").returncode == 0
    return root


def test_worktree_list_shows_live_slice(tmp_path):
    root = seed_with_started_slice(tmp_path)
    r = run(root, "worktree", "list")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "P1.S1" in r.stdout
    assert "worktree-p1-s1-slice-one" in r.stdout
    assert "live" in r.stdout


def test_worktree_list_hides_in_place_by_default_shows_with_all(tmp_path):
    root = seed_with_started_slice(tmp_path)
    # Second slice in-place
    assert run(root, "create", "slice", "P1", "--title", "Spec slice").returncode == 0
    assert run(root, "start", "P1.S2", "--in-place").returncode == 0
    r_default = run(root, "worktree", "list")
    r_all = run(root, "worktree", "list", "--all")
    assert "P1.S2" not in r_default.stdout
    assert "P1.S2" in r_all.stdout
    assert "in-place" in r_all.stdout


def test_worktree_list_marks_missing_path(tmp_path):
    root = seed_with_started_slice(tmp_path)
    # Remove the worktree directory out-of-band but keep the branch
    _git(root, "worktree", "remove", "--force", ".worktrees/worktree-p1-s1-slice-one")
    r = run(root, "worktree", "list")
    assert r.returncode == 0
    assert "missing-path" in r.stdout
