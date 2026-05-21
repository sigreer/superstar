import json
import os
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
PYTHONPATH = str(Path(__file__).resolve().parents[2])


def run(root, *args, env_extra=None):
    env = os.environ.copy()
    env["PYTHONPATH"] = PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(TOOL), "--project-root", str(root), *args],
        text=True, capture_output=True, env=env,
    )


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True)


def seed_repo(tmp_path):
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
    assert run(root, "create", "phase", "--title", "Phase one").returncode == 0
    assert run(root, "create", "slice", "P1", "--title", "Lifecycle core").returncode == 0
    return root


def tasklist(root):
    return json.loads((root / "docs" / "tasklist.json").read_text())


def test_start_records_worktree_path_and_branch_and_creates_dir(tmp_path):
    root = seed_repo(tmp_path)
    r = run(root, "start", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(root)["phases"][0]["slices"][0]
    expected_name = "worktree-p1-s1-lifecycle-core"
    assert sl["worktree_path"] == f".worktrees/{expected_name}"
    assert sl["worktree_branch"] == expected_name
    assert sl["worktree_in_place"] is False
    assert (root / ".worktrees" / expected_name).is_dir()
    # Branch exists
    branches = _git(root, "branch", "--list", expected_name).stdout
    assert expected_name in branches
    # Output prints a `cd` line pointing at the worktree
    assert ".worktrees/" + expected_name in r.stdout


def test_start_is_idempotent_when_consistent(tmp_path):
    root = seed_repo(tmp_path)
    assert run(root, "start", "P1.S1").returncode == 0
    r = run(root, "start", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    # Still recorded once, dir still present, no error.
    sl = tasklist(root)["phases"][0]["slices"][0]
    assert sl["worktree_path"] == ".worktrees/worktree-p1-s1-lifecycle-core"
