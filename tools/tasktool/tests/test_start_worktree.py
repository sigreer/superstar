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


def _seed_started(tmp_path):
    root = seed_repo(tmp_path)
    assert run(root, "start", "P1.S1").returncode == 0
    return root, ".worktrees/worktree-p1-s1-lifecycle-core"


def test_start_refused_when_path_missing_branch_missing(tmp_path):
    root, rel = _seed_started(tmp_path)
    # Remove worktree dir and delete branch.
    name = Path(rel).name
    _git(root, "worktree", "remove", "--force", rel)
    _git(root, "branch", "-D", name)
    r = run(root, "start", "P1.S1")
    assert r.returncode != 0
    assert "recorded worktree gone" in (r.stdout + r.stderr)


def test_start_refused_when_path_missing_branch_present(tmp_path):
    root, rel = _seed_started(tmp_path)
    name = Path(rel).name
    # git worktree remove deletes the dir but keeps the branch.
    _git(root, "worktree", "remove", "--force", rel)
    r = run(root, "start", "P1.S1")
    assert r.returncode != 0
    assert "still exists" in (r.stdout + r.stderr)


def test_start_refused_when_path_is_plain_dir(tmp_path):
    root, rel = _seed_started(tmp_path)
    name = Path(rel).name
    _git(root, "worktree", "remove", "--force", rel)
    # Drop a non-worktree directory at the recorded path.
    (root / rel).mkdir(parents=True)
    r = run(root, "start", "P1.S1")
    assert r.returncode != 0
    assert "not a linked worktree" in (r.stdout + r.stderr)


def test_start_on_done_row_does_not_create_worktree(tmp_path):
    """Lifecycle preflight (F1): a row that is already `done` must be refused
    BEFORE any `.worktrees/` or branch creation happens."""
    root = seed_repo(tmp_path)
    # Set status=done via the underlying machinery: start, then close (skip review gate).
    assert run(root, "start", "P1.S1").returncode == 0
    # remove the auto-created worktree dir & branch so we can observe "no side effects"
    # cleanly on the second start attempt
    expected_name = "worktree-p1-s1-lifecycle-core"
    _git(root, "worktree", "remove", "--force", f".worktrees/{expected_name}")
    _git(root, "branch", "-D", expected_name)
    # Re-record the worktree fields as null so the second `start` can't classify the
    # row as "needs repair"; mark slice done directly via `set --status done --skip-review-gate`.
    assert run(root, "set", "P1.S1", "--status", "done", "--skip-review-gate").returncode == 0
    r = run(root, "start", "P1.S1")
    assert r.returncode != 0
    assert "already done" in (r.stdout + r.stderr)
    # No new branch, no new worktree directory
    assert not (root / ".worktrees" / expected_name).exists()
    out = _git(root, "branch", "--list", expected_name).stdout.strip()
    assert out == ""


def test_start_on_blocked_row_without_resume_does_not_create_worktree(tmp_path):
    """F1: blocked-row preflight refusal must precede git mutation."""
    root = seed_repo(tmp_path)
    # Create a second slice and block it on the first
    assert run(root, "create", "slice", "P1", "--title", "Dependent").returncode == 0
    assert run(root, "block", "P1.S2", "--on", "external:waiting").returncode == 0
    r = run(root, "start", "P1.S2")
    assert r.returncode != 0
    assert "blocked" in (r.stdout + r.stderr)
    assert not (root / ".worktrees" / "worktree-p1-s2-dependent").exists()
    out = _git(root, "branch", "--list", "worktree-p1-s2-dependent").stdout.strip()
    assert out == ""


def test_start_refused_when_branch_mismatched(tmp_path):
    root, rel = _seed_started(tmp_path)
    name = Path(rel).name
    # Force the worktree onto a different branch.
    _git(root, "checkout", "-b", "elsewhere", "main")
    _git(root / rel, "checkout", "-b", "elsewhere2")
    r = run(root, "start", "P1.S1")
    assert r.returncode != 0
    out = r.stdout + r.stderr
    assert "different branch" in out
