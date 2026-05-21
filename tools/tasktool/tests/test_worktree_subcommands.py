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


def test_worktree_status_live_slice_reports_clean(tmp_path):
    root = seed_with_started_slice(tmp_path)
    r = run(root, "worktree", "status", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    out = r.stdout
    assert "path:" in out
    assert "branch: worktree-p1-s1-slice-one" in out
    assert "ahead/behind:" in out
    assert "dirty: clean" in out
    assert "last_activity:" in out


def test_worktree_status_reports_dirty_after_edit(tmp_path):
    root = seed_with_started_slice(tmp_path)
    wt = root / ".worktrees" / "worktree-p1-s1-slice-one"
    (wt / "note.txt").write_text("dirty\n")
    r = run(root, "worktree", "status", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "dirty: 1 path(s)" in r.stdout


def test_worktree_status_unknown_slice(tmp_path):
    root = seed_with_started_slice(tmp_path)
    r = run(root, "worktree", "status", "P9.S9")
    assert r.returncode != 0
    assert "not found" in (r.stdout + r.stderr)


def test_worktree_status_uses_configured_authoritative_branch(tmp_path):
    """F3: when `authoritative_branch=develop`, status must report ahead/behind
    against `develop`, not against a hardcoded `main`."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "develop")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "T")
    (root / "docs").mkdir()
    assert run(root, "config", "init-authority", "--branch", "develop").returncode == 0
    assert run(root, "init", "--project", "demo").returncode == 0
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "init")
    assert run(root, "create", "phase", "--title", "P").returncode == 0
    assert run(root, "create", "slice", "P1", "--title", "Slice").returncode == 0
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "seed slice")
    assert run(root, "start", "P1.S1").returncode == 0
    r = run(root, "worktree", "status", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    # Crucially: the report names `develop` as the parent, not `main`.
    assert "vs develop" in r.stdout
    assert "vs main" not in r.stdout


def test_worktree_status_in_place_slice(tmp_path):
    root = seed_with_started_slice(tmp_path)
    assert run(root, "create", "slice", "P1", "--title", "Spec slice").returncode == 0
    assert run(root, "start", "P1.S2", "--in-place").returncode == 0
    r = run(root, "worktree", "status", "P1.S2")
    assert r.returncode == 0
    assert "in-place" in r.stdout


def test_worktree_adopt_records_external_worktree(tmp_path):
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
    assert run(root, "create", "slice", "P1", "--title", "Slice").returncode == 0
    external = tmp_path / "external"
    _git(root, "worktree", "add", "-b", "external-branch", str(external))
    r = run(root, "worktree", "adopt", "P1.S1", str(external))
    assert r.returncode == 0, r.stdout + r.stderr
    sl = json.loads((root / "docs" / "tasklist.json").read_text())["phases"][0]["slices"][0]
    assert sl["worktree_branch"] == "external-branch"
    assert sl["worktree_path"].endswith("external")


def test_worktree_adopt_refuses_non_worktree(tmp_path):
    root = seed_with_started_slice(tmp_path)
    plain = tmp_path / "plain"
    plain.mkdir()
    r = run(root, "worktree", "adopt", "P1.S1", str(plain))
    assert r.returncode != 0
    assert "not a linked worktree" in (r.stdout + r.stderr)


def test_worktree_adopt_refuses_to_overwrite_live_record(tmp_path):
    root = seed_with_started_slice(tmp_path)
    external = tmp_path / "external"
    _git(root, "worktree", "add", "-b", "external-branch", str(external))
    r = run(root, "worktree", "adopt", "P1.S1", str(external))
    assert r.returncode != 0
    assert "already" in (r.stdout + r.stderr)


def test_worktree_adopt_overwrites_dead_record(tmp_path):
    root = seed_with_started_slice(tmp_path)
    # Kill the live worktree but keep the branch
    _git(root, "worktree", "remove", "--force", ".worktrees/worktree-p1-s1-slice-one")
    external = tmp_path / "external"
    _git(root, "worktree", "add", "-b", "external-branch", str(external))
    r = run(root, "worktree", "adopt", "P1.S1", str(external))
    assert r.returncode == 0, r.stdout + r.stderr
    sl = json.loads((root / "docs" / "tasklist.json").read_text())["phases"][0]["slices"][0]
    assert sl["worktree_branch"] == "external-branch"
