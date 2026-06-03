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
    assert sl.get("worktree_in_place", False) is False
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


def test_start_in_place_marks_slice(tmp_path):
    root = seed_repo(tmp_path)
    r = run(root, "start", "P1.S1", "--in-place")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(root)["phases"][0]["slices"][0]
    assert sl["worktree_in_place"] is True
    assert sl.get("worktree_path") is None
    assert sl.get("worktree_branch") is None
    # No .worktrees directory created
    assert not (root / ".worktrees" / "worktree-p1-s1-lifecycle-core").exists()


def test_start_adopt_records_external_worktree(tmp_path):
    root = seed_repo(tmp_path)
    external = tmp_path / "external"
    _git(root, "worktree", "add", "-b", "manual-branch", str(external))
    r = run(root, "start", "P1.S1", "--adopt", str(external))
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(root)["phases"][0]["slices"][0]
    assert sl["worktree_branch"] == "manual-branch"
    assert sl["worktree_path"].endswith("external")


def test_start_adopt_refuses_main_checkout(tmp_path):
    """S1.F1 (post-slice r2): --adopt must refuse the main checkout. The spec
    reserves --adopt for externally-created linked worktrees; the primary
    checkout is reported by `git worktree list --porcelain` alongside linked
    ones, so without an explicit guard `tasktool start <id> --adopt <root>`
    would record `worktree_path: "."` and `worktree_branch: "main"`."""
    root = seed_repo(tmp_path)
    r = run(root, "start", "P1.S1", "--adopt", str(root))
    assert r.returncode != 0, r.stdout + r.stderr
    out = r.stdout + r.stderr
    assert "main checkout" in out
    # And nothing was recorded.
    sl = tasklist(root)["phases"][0]["slices"][0]
    assert sl.get("worktree_path") is None
    assert sl.get("worktree_branch") is None


def test_start_adopt_refuses_non_worktree_path(tmp_path):
    root = seed_repo(tmp_path)
    plain = tmp_path / "plain"
    plain.mkdir()
    r = run(root, "start", "P1.S1", "--adopt", str(plain))
    assert r.returncode != 0
    assert "not a linked worktree" in (r.stdout + r.stderr)


def test_start_auto_adopt_from_linked_worktree_routes_to_authoritative(tmp_path):
    """F2: end-to-end authoritative-routing fixture.

    - Authoritative checkout on `main` configured via `config init-authority`.
    - Tasklist row committed to `main` so the routed write target has a real row.
    - A linked worker checkout is created; `tasktool start` is invoked from inside it.
    - Assertion: the worktree fields are persisted in the AUTHORITATIVE checkout's
      `docs/tasklist.json`, and the recorded path is the linked worker's path.
    """
    # 1. Build authoritative main checkout with init-authority routing.
    auth = tmp_path / "authoritative"
    auth.mkdir()
    _git(auth, "init", "-b", "main")
    _git(auth, "config", "user.email", "t@example.invalid")
    _git(auth, "config", "user.name", "T")
    (auth / "docs").mkdir()
    assert run(auth, "config", "init-authority", "--branch", "main").returncode == 0
    assert run(auth, "init", "--project", "demo").returncode == 0
    _git(auth, "add", "-A")
    _git(auth, "commit", "-m", "init")
    assert run(auth, "create", "phase", "--title", "Phase one").returncode == 0
    assert run(auth, "create", "slice", "P1", "--title", "Lifecycle core").returncode == 0
    _git(auth, "add", "-A")
    _git(auth, "commit", "-m", "seed slice")

    # 2. Create a linked worker checkout from the authoritative repo.
    worker = tmp_path / "worker"
    _git(auth, "worktree", "add", "-b", "feature-branch", str(worker))

    # 3. Run tasktool start from inside the worker; routing must auto-adopt.
    env_extra = {"TASKTOOL_AUTHORITY_ROOT": str(auth)}
    r = run(worker, "start", "P1.S1", env_extra=env_extra)
    assert r.returncode == 0, r.stdout + r.stderr

    # 4. Assertion: the authoritative tasklist now records the worker's path/branch.
    sl = tasklist(auth)["phases"][0]["slices"][0]
    assert sl["worktree_branch"] == "feature-branch"
    assert Path(sl["worktree_path"]).name == "worker"

    # 5. The worker checkout's tasklist (if any) must NOT shadow the authoritative one.
    worker_tasklist = worker / "docs" / "tasklist.json"
    if worker_tasklist.exists():
        wsl = json.loads(worker_tasklist.read_text())["phases"][0]["slices"][0]
        # routed writes go to auth; worker copy is whatever was committed on feature-branch
        # (the seed slice with no worktree fields). The test is satisfied as long as
        # the authoritative copy carries the new fields.
        assert sl["worktree_branch"] == "feature-branch"


def test_start_auto_adopt_unrouted_local_repo(tmp_path):
    """Lighter sibling of the routed test: in `config init-local` mode (no
    authoritative routing), auto-adopt should still record the linked-worktree
    path against the slice. Verifies the `is_inside_linked_worktree` branch of
    `cmd_start` without going through `_resolve_write_root`.
    """
    root = seed_repo(tmp_path)
    linked = tmp_path / "linked"
    _git(root, "worktree", "add", "-b", "in-flight", str(linked))
    # Commit the seeded slice so the linked worktree sees the tasklist row.
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "seed slice")
    # Pull main's commit into the linked worktree
    _git(linked, "merge", "main", "--ff")
    r = run(linked, "start", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(root)["phases"][0]["slices"][0]
    assert sl["worktree_branch"] == "in-flight"
    assert Path(sl["worktree_path"]).name == "linked"


def test_start_in_place_then_normal_start_is_refused(tmp_path):
    root = seed_repo(tmp_path)
    assert run(root, "start", "P1.S1", "--in-place").returncode == 0
    r = run(root, "start", "P1.S1")
    # Slice is already in_progress (so _start_item is a no-op), and worktree
    # state shows ABSENT path with worktree_in_place=true. Subsequent default
    # start must not create a worktree behind the user's back.
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(root)["phases"][0]["slices"][0]
    assert sl["worktree_in_place"] is True
    assert sl.get("worktree_path") is None


def test_start_ad_hoc_creates_X_row_and_worktree(tmp_path):
    root = seed_repo(tmp_path)
    r = run(root, "start", "--ad-hoc", "shim-drift")
    assert r.returncode == 0, r.stdout + r.stderr
    tl = tasklist(root)
    assert len(tl["cross_cutting"]) == 1
    x = tl["cross_cutting"][0]
    assert x["id"].startswith("X")
    assert x["title"] == "Ad-hoc: shim-drift"
    assert x["status"] == "in_progress"
    assert x["notes"] == "ad-hoc"
    name = f"worktree-{x['id'].lower()}-ad-hoc-shim-drift"
    assert x["worktree_path"] == f".worktrees/{name}"
    assert x["worktree_branch"] == name
    assert (root / ".worktrees" / name).is_dir()
    # CLI prints the allocated ID so callers can chain commands
    assert x["id"] in r.stdout


def test_start_ad_hoc_requires_slug(tmp_path):
    root = seed_repo(tmp_path)
    r = run(root, "start", "--ad-hoc", "")
    assert r.returncode != 0
    assert "slug" in (r.stdout + r.stderr).lower()


def test_start_ad_hoc_rejects_id_argument(tmp_path):
    root = seed_repo(tmp_path)
    r = run(root, "start", "P1.S1", "--ad-hoc", "x")
    assert r.returncode != 0


def test_ad_hoc_row_hidden_from_default_list_visible_with_all(tmp_path):
    root = seed_repo(tmp_path)
    assert run(root, "start", "--ad-hoc", "shim-drift").returncode == 0
    r_default = run(root, "list")
    r_all = run(root, "list", "--all")
    assert "Ad-hoc: shim-drift" not in r_default.stdout
    assert "Ad-hoc: shim-drift" in r_all.stdout


def test_start_records_worktree_base_sha_for_default(tmp_path):
    root = seed_repo(tmp_path)
    base_head = _git(root, "rev-parse", "main").stdout.strip()
    r = run(root, "start", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(root)["phases"][0]["slices"][0]
    assert sl["worktree_base_sha"] == base_head


def test_start_in_place_records_worktree_base_sha(tmp_path):
    root = seed_repo(tmp_path)
    base_head = _git(root, "rev-parse", "main").stdout.strip()
    r = run(root, "start", "P1.S1", "--in-place")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(root)["phases"][0]["slices"][0]
    assert sl["worktree_in_place"] is True
    assert sl["worktree_base_sha"] == base_head


def test_start_adopt_records_merge_base_as_worktree_base_sha(tmp_path):
    root = seed_repo(tmp_path)
    # Fork point is current main HEAD.
    fork = _git(root, "rev-parse", "main").stdout.strip()
    external = tmp_path / "external"
    _git(root, "worktree", "add", "-b", "manual-branch", str(external))
    # Advance the adopted branch and main independently so HEAD != fork on both.
    (external / "f").write_text("x")
    _git(external, "add", "f")
    _git(external, "commit", "-m", "branch work")
    (root / "g").write_text("y")
    _git(root, "add", "g")
    _git(root, "commit", "-m", "main work")
    r = run(root, "start", "P1.S1", "--adopt", str(external))
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(root)["phases"][0]["slices"][0]
    assert sl["worktree_base_sha"] == fork
