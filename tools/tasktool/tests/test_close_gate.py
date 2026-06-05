"""P8.S1: landed-branch close gate + lifecycle auto-commit.

Spec: docs/specs/2026-06-05-P8.S1-close-gate-lifecycle-auto-commit-design.md
"""
import json
import os
import shlex
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


# ───── Task 2: gate on cmd_set --status done ─────

def test_set_done_refuses_unlanded_branch(tmp_path):
    root, _wt = start_with_unlanded_commit(tmp_path)
    r = run(root, "set", "P1.S1", "--status", "done", "--skip-review-gate")
    assert r.returncode == 1, r.stdout + r.stderr
    out = r.stdout + r.stderr
    assert "not landed" in out
    assert BRANCH in out
    assert the_slice(root)["status"] != "done"


def test_set_done_allow_unlanded_closes_and_audits(tmp_path):
    root, _wt = start_with_unlanded_commit(tmp_path)
    r = run(
        root,
        "set",
        "P1.S1",
        "--status",
        "done",
        "--skip-review-gate",
        "--allow-unlanded",
        "--reason",
        "landed via squash outside git",
    )
    assert r.returncode == 0, r.stdout + r.stderr
    sl = the_slice(root)
    assert sl["status"] == "done"
    assert "allow-unlanded override for P1.S1: landed via squash outside git" in sl["notes"]


def test_set_non_done_status_is_not_gated(tmp_path):
    root, _wt = start_with_unlanded_commit(tmp_path)
    r = run(root, "set", "P1.S1", "--status", "ready")
    assert r.returncode == 0, r.stdout + r.stderr


# ───── Task 3: _git_commit_scoped ─────

def _plain_repo(tmp_path):
    repo = tmp_path / "plain"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "T")
    (repo / "seed.txt").write_text("seed\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "seed")
    return repo


def test_commit_scoped_commits_only_named_paths(tmp_path):
    from tasktool import commands
    repo = _plain_repo(tmp_path)
    (repo / "a.txt").write_text("a\n")
    (repo / "b.txt").write_text("b\n")
    _git(repo, "add", "-A")
    ok = commands._git_commit_scoped(repo, ["a.txt"], "scoped: a only")
    assert ok is True
    committed = _git(repo, "show", "--name-only", "--format=", "HEAD").stdout.split()
    assert committed == ["a.txt"]
    still_staged = _git(repo, "diff", "--cached", "--name-only").stdout.split()
    assert still_staged == ["b.txt"]
    assert _git(repo, "log", "-1", "--format=%s").stdout.strip() == "scoped: a only"


def test_commit_scoped_failure_warns_and_returns_false(tmp_path, capsys):
    from tasktool import commands
    repo = _plain_repo(tmp_path)
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho hook says no >&2\nexit 1\n")
    hook.chmod(0o755)
    (repo / "a.txt").write_text("a\n")
    _git(repo, "add", "-A")
    ok = commands._git_commit_scoped(repo, ["a.txt"], "will fail")
    assert ok is False
    err = capsys.readouterr().err
    assert "auto-commit failed" in err
    assert f"git -C {shlex.quote(str(repo))} commit" in err
    assert _git(repo, "log", "-1", "--format=%s").stdout.strip() == "seed"


def test_commit_scoped_empty_rels_refuses_without_committing_staged_file(tmp_path, capsys):
    from tasktool import commands
    repo = _plain_repo(tmp_path)
    (repo / "unrelated.txt").write_text("unrelated\n")
    _git(repo, "add", "-A")
    ok = commands._git_commit_scoped(repo, [], "should not commit")
    assert ok is False
    err = capsys.readouterr().err
    assert "no scoped paths" in err
    assert _git(repo, "log", "-1", "--format=%s").stdout.strip() == "seed"
    still_staged = _git(repo, "diff", "--cached", "--name-only").stdout.split()
    assert still_staged == ["unrelated.txt"]


def test_commit_scoped_failure_warns_with_quoted_manual_command_and_keeps_path_staged(
    tmp_path, capsys
):
    from tasktool import commands
    repo = tmp_path / "plain repo; $(touch pwned)"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "T")
    (repo / "seed.txt").write_text("seed\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "seed")
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho hook says no >&2\nexit 1\n")
    hook.chmod(0o755)
    rel = "dir with spaces/file; $(touch nope).txt"
    (repo / "dir with spaces").mkdir()
    (repo / rel).write_text("a\n")
    _git(repo, "add", "-A")
    message = "will fail; $(touch message-pwned)"
    ok = commands._git_commit_scoped(repo, [rel], message)
    assert ok is False
    err = capsys.readouterr().err
    assert "auto-commit failed" in err
    assert f"git -C {shlex.quote(str(repo))} commit" in err
    assert f"-m {shlex.quote(message)}" in err
    assert f"-- {shlex.quote(rel)}" in err
    still_staged = _git(repo, "diff", "--cached", "--name-only").stdout.splitlines()
    assert still_staged == [rel]
    assert _git(repo, "log", "-1", "--format=%s").stdout.strip() == "seed"


def test_commit_scoped_skipped_when_staging_disabled(tmp_path, monkeypatch):
    from tasktool import commands
    repo = _plain_repo(tmp_path)
    (repo / "a.txt").write_text("a\n")
    _git(repo, "add", "-A")
    monkeypatch.setattr(commands, "STAGE_AFTER_WRITE", False)
    ok = commands._git_commit_scoped(repo, ["a.txt"], "should not happen")
    assert ok is True
    assert _git(repo, "log", "-1", "--format=%s").stdout.strip() == "seed"


# ───── Task 4: auto-commit on close ─────

def _landed(tmp_path):
    root, wt = start_with_unlanded_commit(tmp_path)
    _git(root, "merge", "--no-ff", "-m", "land P1.S1", BRANCH)
    return root, wt


def test_close_autocommits_tracker(tmp_path):
    root, _wt = _landed(tmp_path)
    r = run(root, "close", "P1.S1", "--skip-review-gate")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (
        _git(root, "status", "--porcelain", "--", "docs/tasklist.json").stdout.strip()
        == ""
    )
    assert (
        _git(root, "log", "-1", "--format=%s").stdout.strip()
        == "P1.S1: close slice (status=done)"
    )


def test_close_autocommit_leaves_sibling_staged_entries(tmp_path):
    root, _wt = _landed(tmp_path)
    (root / "sibling.txt").write_text("co-staged by a sibling session\n")
    _git(root, "add", "sibling.txt")
    r = run(root, "close", "P1.S1", "--skip-review-gate")
    assert r.returncode == 0, r.stdout + r.stderr
    committed = _git(root, "show", "--name-only", "--format=", "HEAD").stdout.split()
    assert committed == ["docs/tasklist.json"]
    assert "sibling.txt" in _git(root, "diff", "--cached", "--name-only").stdout


def test_close_cross_autocommits_tracker_and_archive(tmp_path):
    root = seed_repo(tmp_path)
    assert run(root, "create", "cross", "--title", "Cross work").returncode == 0
    r = run(root, "close", "X1")
    assert r.returncode == 0, r.stdout + r.stderr
    committed = sorted(
        _git(root, "show", "--name-only", "--format=", "HEAD").stdout.split()
    )
    assert "docs/tasklist.json" in committed
    assert any(p.startswith("docs/archived-tasks/X1-") for p in committed)
    assert len(committed) == 2
    assert (
        _git(root, "log", "-1", "--format=%s").stdout.strip()
        == "X1: close cross-cutting (status=done)"
    )


def test_close_no_commit_preserves_staged_state(tmp_path):
    root, _wt = _landed(tmp_path)
    r = run(root, "close", "P1.S1", "--skip-review-gate", "--no-commit")
    assert r.returncode == 0, r.stdout + r.stderr
    assert the_slice(root)["status"] == "done"
    assert "docs/tasklist.json" in _git(root, "diff", "--cached", "--name-only").stdout
    assert _git(root, "log", "-1", "--format=%s").stdout.strip() == "land P1.S1"


def test_close_commit_failure_warns_but_exits_zero(tmp_path):
    root, _wt = _landed(tmp_path)
    hook = root / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    r = run(root, "close", "P1.S1", "--skip-review-gate")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "auto-commit failed" in r.stderr
    assert the_slice(root)["status"] == "done"
    assert "docs/tasklist.json" in _git(root, "diff", "--cached", "--name-only").stdout


def test_close_no_stage_means_no_stage_and_no_commit(tmp_path):
    """Global --no-stage disables staging and auto-commit git side effects."""
    root, _wt = _landed(tmp_path)
    r = run(root, "--no-stage", "close", "P1.S1", "--skip-review-gate")
    assert r.returncode == 0, r.stdout + r.stderr
    assert the_slice(root)["status"] == "done"
    assert "docs/tasklist.json" not in _git(root, "diff", "--cached", "--name-only").stdout
    assert _git(root, "log", "-1", "--format=%s").stdout.strip() == "land P1.S1"
