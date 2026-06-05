"""P8.S1: landed-branch close gate + lifecycle auto-commit.

Spec: docs/specs/2026-06-05-P8.S1-close-gate-lifecycle-auto-commit-design.md
"""
import json
import os
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
PYTHONPATH = str(Path(__file__).resolve().parents[2])

BRANCH = "worktree-p1-s1-lifecycle-core"
WT_REL = f".worktrees/{BRANCH}"


def run(root, *args, cwd=None):
    env = os.environ.copy()
    env["PYTHONPATH"] = PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, str(TOOL), "--project-root", str(root), *args],
        text=True, capture_output=True, env=env, cwd=cwd,
    )


def _git(cwd, *args):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, text=True, capture_output=True
    )


def tasklist(root):
    return json.loads((root / "docs" / "tasklist.json").read_text())


def the_slice(root):
    return tasklist(root)["phases"][0]["slices"][0]


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


def start_with_unlanded_commit(tmp_path):
    """Started slice whose worktree branch has a commit NOT on main."""
    root = seed_repo(tmp_path)
    assert run(root, "start", "P1.S1").returncode == 0
    # Commit the staged tracker mutations (create/start): `git merge` aborts
    # when the index differs from HEAD, and several tests merge from root.
    _git(root, "commit", "-m", "tracker: rows + start", "--", "docs/tasklist.json")
    wt = root / WT_REL
    (wt / "work.txt").write_text("payload\n")
    _git(wt, "add", "-A")
    _git(wt, "commit", "-m", "slice work")
    return root, wt


def test_close_refuses_unlanded_branch(tmp_path):
    root, _wt = start_with_unlanded_commit(tmp_path)
    r = run(root, "close", "P1.S1", "--skip-review-gate")
    assert r.returncode == 1, r.stdout + r.stderr
    out = r.stdout + r.stderr
    assert BRANCH in out
    assert "not landed" in out
    assert "main" in out
    assert "--allow-unlanded" in out
    assert "NOT performed" in out
    assert "git merge" in out
    assert the_slice(root)["status"] != "done"


def test_close_passes_when_branch_landed(tmp_path):
    root, _wt = start_with_unlanded_commit(tmp_path)
    _git(root, "merge", "--no-ff", "-m", "land P1.S1", BRANCH)
    r = run(root, "close", "P1.S1", "--skip-review-gate")
    assert r.returncode == 0, r.stdout + r.stderr
    assert the_slice(root)["status"] == "done"


def test_close_in_place_slice_is_exempt(tmp_path):
    root = seed_repo(tmp_path)
    assert run(root, "start", "P1.S1", "--in-place").returncode == 0
    r = run(root, "close", "P1.S1", "--skip-review-gate")
    assert r.returncode == 0, r.stdout + r.stderr
    assert the_slice(root)["status"] == "done"


def test_close_without_recorded_branch_is_exempt(tmp_path):
    root = seed_repo(tmp_path)
    r = run(
        root,
        "close",
        "P1.S1",
        "--skip-review-gate",
        "--allow-ready-close",
        "--reason",
        "doc-only slice",
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert the_slice(root)["status"] == "done"


def test_close_with_deleted_branch_says_cannot_verify(tmp_path):
    root, wt = start_with_unlanded_commit(tmp_path)
    _git(root, "worktree", "remove", "--force", str(wt))
    _git(root, "branch", "-D", BRANCH)
    r = run(root, "close", "P1.S1", "--skip-review-gate")
    assert r.returncode == 1, r.stdout + r.stderr
    out = r.stdout + r.stderr
    assert "no longer exists" in out
    assert "cannot verify" in out
    assert "--allow-unlanded" in out


def test_allow_unlanded_requires_reason(tmp_path):
    root, _wt = start_with_unlanded_commit(tmp_path)
    r = run(root, "close", "P1.S1", "--skip-review-gate", "--allow-unlanded")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "--reason" in (r.stdout + r.stderr)
    assert the_slice(root)["status"] != "done"


def test_allow_unlanded_with_reason_closes_and_audits(tmp_path):
    root, _wt = start_with_unlanded_commit(tmp_path)
    r = run(
        root,
        "close",
        "P1.S1",
        "--skip-review-gate",
        "--allow-unlanded",
        "--reason",
        "spike branch intentionally abandoned",
    )
    assert r.returncode == 0, r.stdout + r.stderr
    sl = the_slice(root)
    assert sl["status"] == "done"
    assert (
        "allow-unlanded override for P1.S1: spike branch intentionally abandoned"
        in sl["notes"]
    )


def test_cross_item_with_unlanded_branch_is_gated(tmp_path):
    root = seed_repo(tmp_path)
    assert run(root, "create", "cross", "--title", "Cross work").returncode == 0
    _git(root, "worktree", "add", str(root / ".worktrees" / "x1"), "-b", "wt-x1")
    xwt = root / ".worktrees" / "x1"
    (xwt / "x.txt").write_text("x\n")
    _git(xwt, "add", "-A")
    _git(xwt, "commit", "-m", "cross work")
    data = tasklist(root)
    data["cross_cutting"][0]["worktree_branch"] = "wt-x1"
    data["cross_cutting"][0]["worktree_path"] = ".worktrees/x1"
    (root / "docs" / "tasklist.json").write_text(json.dumps(data))
    r = run(root, "close", "X1")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "wt-x1" in (r.stdout + r.stderr)
