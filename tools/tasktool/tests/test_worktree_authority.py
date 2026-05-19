import subprocess
import json
import os
import sys
from pathlib import Path

from tasktool.worktree import (
    AuthorityError,
    find_authoritative_root,
    git_common_dir,
    git_current_branch,
    same_repository,
    tasklist_has_unsafe_dirty_state,
    validate_authoritative_checkout,
)


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True)


def _repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "tasktool-tests@example.invalid")
    _git(root, "config", "user.name", "Tasktool Tests")
    (root / "README.md").write_text("x\n")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "init")
    return root


def test_git_common_dir_is_shared_by_linked_worktree(tmp_path):
    root = _repo(tmp_path)
    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    assert git_common_dir(root) == git_common_dir(worker)


def test_validate_authoritative_checkout_rejects_wrong_branch(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-b", "other")
    try:
        validate_authoritative_checkout(root, expected_branch="main", caller_root=root)
    except AuthorityError as exc:
        assert "expected branch main" in str(exc)
    else:
        raise AssertionError("expected AuthorityError")


def test_same_repository_true_for_linked_worktree(tmp_path):
    root = _repo(tmp_path)
    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    assert same_repository(root, worker)


def test_same_repository_false_for_unrelated_repos(tmp_path):
    left_parent = tmp_path / "left"
    right_parent = tmp_path / "right"
    left_parent.mkdir()
    right_parent.mkdir()
    left = _repo(left_parent)
    right = _repo(right_parent)
    assert same_repository(left, right) is False


def test_find_authoritative_root_uses_branch_worktree(tmp_path):
    root = _repo(tmp_path)
    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    assert find_authoritative_root(worker, branch="main") == root


def test_find_authoritative_root_uses_env_override(tmp_path, monkeypatch):
    root = _repo(tmp_path)
    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    monkeypatch.setenv("TASKTOOL_AUTHORITY_ROOT", str(root))
    assert find_authoritative_root(worker, branch="missing") == root


def test_find_authoritative_root_fails_closed_when_missing(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-b", "feature")
    try:
        find_authoritative_root(root, branch="main")
    except AuthorityError as exc:
        assert "TASKTOOL_AUTHORITY_ROOT" in str(exc)
    else:
        raise AssertionError("expected AuthorityError")


def test_validate_authoritative_checkout_permits_dirty_tasklist_check_to_caller(tmp_path):
    root = _repo(tmp_path)
    (root / "docs").mkdir()
    (root / "docs" / "tasklist.json").write_text("{}\n")
    assert validate_authoritative_checkout(root, expected_branch="main", caller_root=root) is None


def test_unsafe_tasklist_dirty_state_detects_unstaged_bytes(tmp_path):
    root = _repo(tmp_path)
    (root / "docs").mkdir()
    (root / "docs" / "tasklist.json").write_text("{}\n")
    _git(root, "add", "docs/tasklist.json")
    assert tasklist_has_unsafe_dirty_state(root) is False
    (root / "docs" / "tasklist.json").write_text('{"changed":true}\n')
    assert tasklist_has_unsafe_dirty_state(root) is True


TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"


def _tasktool(cwd, *args, env=None):
    merged_env = os.environ.copy()
    merged_env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2]) + os.pathsep + merged_env.get("PYTHONPATH", "")
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        env=merged_env,
    )


def _seed_tasktool_repo(tmp_path):
    root = _repo(tmp_path)
    (root / "docs").mkdir()
    r = _tasktool(root, "init", "--project", "demo")
    assert r.returncode == 0, r.stdout + r.stderr
    r = _tasktool(root, "create", "phase", "--title", "P")
    assert r.returncode == 0, r.stdout + r.stderr
    r = _tasktool(root, "create", "slice", "P1", "--title", "S")
    assert r.returncode == 0, r.stdout + r.stderr
    _git(root, "add", ".")
    _git(root, "commit", "-m", "tasklist")
    return root


def _authority_with_worker(tmp_path):
    root = _seed_tasktool_repo(tmp_path)
    r = _tasktool(root, "config", "init-authority", "--branch", "main")
    assert r.returncode == 0, r.stdout + r.stderr
    _git(root, "add", ".")
    _git(root, "commit", "-m", "authority")
    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    return root, worker


def assert_worker_tasklist_unchanged(root, worker, *args):
    before = (worker / "docs/tasklist.json").read_text()
    r = _tasktool(worker, *args)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before
    assert "authoritative checkout" in r.stderr
    return json.loads((root / "docs/tasklist.json").read_text())


def test_worker_mutation_updates_authority_not_worker(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    before_worker = (worker / "docs/tasklist.json").read_text()

    r = _tasktool(worker, "set", "P1.S1", "--status", "in_progress")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "authoritative checkout" in r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before_worker

    authority = json.loads((root / "docs/tasklist.json").read_text())
    assert authority["phases"][0]["slices"][0]["status"] == "in_progress"
    assert authority["phases"][0]["slices"][0]["started"]


def test_worker_start_routes_to_authority(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    before_worker = (worker / "docs/tasklist.json").read_text()
    r = _tasktool(worker, "start", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "authoritative checkout" in r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before_worker
    data = json.loads((root / "docs/tasklist.json").read_text())
    assert data["phases"][0]["slices"][0]["status"] == "in_progress"
    assert data["phases"][0]["slices"][0]["started"]


def test_authoritative_checkout_write_uses_same_lock(tmp_path):
    root = _seed_tasktool_repo(tmp_path)
    r = _tasktool(root, "config", "init-authority", "--branch", "main")
    assert r.returncode == 0, r.stdout + r.stderr
    common = git_common_dir(root)
    (common / "tasktool.lock").write_text("held")
    try:
        r = _tasktool(
            root,
            "set",
            "P1.S1",
            "--status",
            "in_progress",
            env={"TASKTOOL_LOCK_TIMEOUT": "0.1"},
        )
    finally:
        (common / "tasktool.lock").unlink()
    assert r.returncode == 1
    assert "timed out waiting for tasktool lock" in r.stderr


def test_authoritative_unstaged_tasklist_refuses_before_mutation(tmp_path):
    root = _seed_tasktool_repo(tmp_path)
    r = _tasktool(root, "config", "init-authority", "--branch", "main")
    assert r.returncode == 0, r.stdout + r.stderr
    _git(root, "add", ".")
    _git(root, "commit", "-m", "authority")
    (root / "docs/tasklist.json").write_text('{"manual":"edit"}\n')
    r = _tasktool(root, "set", "P1.S1", "--status", "in_progress")
    assert r.returncode == 1
    assert "unstaged changes" in r.stderr


def test_worker_close_records_reviewer_chain_in_authority(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    chain = worker / "docs" / "reviewer" / "p1-s1-post-slice"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}')
    before_worker = (worker / "docs/tasklist.json").read_text()

    r = _tasktool(worker, "start", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before_worker
    r = _tasktool(worker, "close", "P1.S1", "--reviewer-chain", str(chain))
    assert r.returncode == 0, r.stdout + r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before_worker
    authority = json.loads((root / "docs/tasklist.json").read_text())
    assert authority["phases"][0]["slices"][0]["status"] == "done"
    assert authority["phases"][0]["slices"][0]["reviewer_chain"] == "docs/reviewer/p1-s1-post-slice"


def test_worker_set_done_records_reviewer_chain_in_authority(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    chain = worker / "docs" / "reviewer" / "p1-s1-post-slice"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}')

    r = _tasktool(worker, "set", "P1.S1", "--status", "done", "--reviewer-chain", str(chain))
    assert r.returncode == 0, r.stdout + r.stderr
    authority = json.loads((root / "docs/tasklist.json").read_text())
    assert authority["phases"][0]["slices"][0]["reviewer_chain"] == "docs/reviewer/p1-s1-post-slice"


def test_reviewer_chain_outside_invocation_repo_is_rejected(tmp_path):
    root = _seed_tasktool_repo(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    r = _tasktool(root, "set", "P1.S1", "--status", "done", "--reviewer-chain", str(outside))
    assert r.returncode == 1
    assert "outside repository" in r.stderr


def test_routed_create_note_ref_title_block_unblock_deps_ratify_and_planning_path(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    data = assert_worker_tasklist_unchanged(root, worker, "create", "phase", "--title", "Second phase")
    assert data["phases"][1]["title"] == "Second phase"
    data = assert_worker_tasklist_unchanged(root, worker, "create", "cross", "--title", "Cross item")
    assert data["cross_cutting"][0]["title"] == "Cross item"
    data = assert_worker_tasklist_unchanged(root, worker, "create", "task", "P1.S1", "--title", "New task")
    assert data["phases"][0]["slices"][0]["tasks"][0]["title"] == "New task"
    data = assert_worker_tasklist_unchanged(root, worker, "note", "P1.S1", "--append", "worker note")
    assert "worker note" in data["phases"][0]["slices"][0]["notes"]
    data = assert_worker_tasklist_unchanged(root, worker, "ref", "P1.S1", "--add", "docs/example.md")
    assert "docs/example.md" in data["phases"][0]["slices"][0]["refs"]
    data = assert_worker_tasklist_unchanged(root, worker, "title", "P1.S1", "--set", "Retitled")
    assert data["phases"][0]["slices"][0]["title"] == "Retitled"
    data = assert_worker_tasklist_unchanged(root, worker, "block", "P1.S1", "--on", "external:waiting")
    assert data["phases"][0]["slices"][0]["status"] == "blocked"
    data = assert_worker_tasklist_unchanged(root, worker, "unblock", "P1.S1", "--resume")
    assert data["phases"][0]["slices"][0]["status"] == "in_progress"
    assert_worker_tasklist_unchanged(root, worker, "create", "slice", "P1", "--title", "Second")
    data = assert_worker_tasklist_unchanged(root, worker, "deps", "P1.S2", "--add", "P1.S1")
    assert data["phases"][0]["slices"][1]["depends_on"] == ["P1.S1"]
    data = assert_worker_tasklist_unchanged(root, worker, "ratify", "P1.S2", "--parallel-group", "followup")
    assert data["phases"][0]["slices"][1]["parallel_group"] == "followup"
    data = assert_worker_tasklist_unchanged(root, worker, "planning-path", "P1", "--set", "docs/specs/p1.md")
    assert data["phases"][0]["planning_path"] == "docs/specs/p1.md"


def test_routed_validate_normalise_updates_authority_only(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    raw = json.loads((root / "docs/tasklist.json").read_text())
    (root / "docs/tasklist.json").write_text(json.dumps(raw, separators=(",", ":")))
    _git(root, "add", "docs/tasklist.json")
    before = (worker / "docs/tasklist.json").read_text()
    r = _tasktool(worker, "validate", "--normalise")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before
    assert (root / "docs/tasklist.json").read_text().endswith("\n")


def test_routed_init_force_updates_authority_only(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    before = (worker / "docs/tasklist.json").read_text()
    r = _tasktool(worker, "init", "--project", "replacement", "--force")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before
    data = json.loads((root / "docs/tasklist.json").read_text())
    assert data["project"] == "replacement"


def test_routed_import_writes_authority_only(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    sample = worker / "TASKLIST_sample.md"
    sample.write_text("## P2 — Imported phase 🚧 `IN PROGRESS`\n")
    before = (worker / "docs/tasklist.json").read_text()
    r = _tasktool(worker, "import", str(sample), "--force")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before
    assert "Imported phase" in (root / "docs/tasklist.json").read_text()


def test_routed_archive_phase_writes_authority_archive_artifact(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    assert_worker_tasklist_unchanged(root, worker, "start", "P1.S1")
    assert_worker_tasklist_unchanged(root, worker, "close", "P1.S1", "--skip-review-gate")
    chain = worker / "docs" / "reviewer" / "p1-post-phase"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}')
    before = (worker / "docs/tasklist.json").read_text()
    r = _tasktool(worker, "archive-phase", "P1", "--reviewer-chain", str(chain))
    assert r.returncode == 0, r.stdout + r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before
    assert list((root / "docs" / "archived-tasks").glob("P1-*.md"))
    assert not (worker / "docs" / "archived-tasks").exists()
