from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tasktool.model import CrossCutting, Phase, Project, Slice, Status, Task
from tasktool.serialize import load_project, save_project

TOOL_ROOT = Path(__file__).resolve().parents[2]


def run_cli(*args: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    merged_env["PYTHONPATH"] = str(TOOL_ROOT) + os.pathsep + merged_env.get("PYTHONPATH", "")
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "tasktool", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        env=merged_env,
    )


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )


def _repo(tmp_path: Path, name: str = "repo") -> Path:
    root = tmp_path / name
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "tasktool-tests@example.invalid")
    _git(root, "config", "user.name", "Tasktool Tests")
    (root / "README.md").write_text("x\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "init")
    return root


def _project(*, slice_status: Status = Status.READY) -> Project:
    return Project(
        project="demo",
        north_star="ship",
        last_reviewed="2026-05-20",
        phases=[
            Phase(
                id="P1",
                title="Phase",
                created="2026-05-20",
                slices=[
                    Slice(
                        id="S1",
                        title="Slice",
                        created="2026-05-20",
                        status=slice_status,
                    )
                ],
            )
        ],
    )


def _write_tasklist(root: Path, project: Project) -> None:
    (root / "docs").mkdir(exist_ok=True)
    save_project(project, root / "docs" / "tasklist.json")


def _authority_and_worker(tmp_path: Path) -> tuple[Path, Path]:
    authority = _repo(tmp_path)
    _write_tasklist(authority, _project())
    _git(authority, "add", "docs/tasklist.json")
    _git(authority, "commit", "-m", "tasklist")
    worker = tmp_path / "worker"
    _git(authority, "worktree", "add", "-b", "worker", str(worker))
    return authority, worker


def _config(root: Path) -> dict:
    return json.loads((root / ".tasktool" / "config.json").read_text(encoding="utf-8"))


def test_drifted_linked_worktree_no_config_accept_local_writes_authority_and_config(tmp_path: Path) -> None:
    authority, worker = _authority_and_worker(tmp_path)
    local = load_project(worker / "docs" / "tasklist.json")
    local.phases[0].slices[0].status = Status.IN_PROGRESS
    local.phases[0].slices[0].started = "2026-05-20"
    _write_tasklist(worker, local)

    r = run_cli("config", "migrate-from-local", "--authority-root", str(authority), "--accept-local", cwd=worker)

    assert r.returncode == 0, r.stderr
    assert "migrated 1 rows (1 status transitions)" in r.stdout
    migrated = load_project(authority / "docs" / "tasklist.json")
    assert migrated.phases[0].slices[0].status == Status.IN_PROGRESS
    assert migrated.phases[0].slices[0].started == "2026-05-20"
    assert _config(authority)["tasklist"] == {
        "authoritative_branch": "main",
        "mutation_mode": "authoritative-checkout",
    }
    staged = _git(authority, "diff", "--cached", "--name-only").stdout.splitlines()
    assert "docs/tasklist.json" in staged
    assert ".tasktool/config.json" in staged


def test_accept_local_refuses_unstaged_authority_tasklist_and_preserves_bytes(tmp_path: Path) -> None:
    authority, worker = _authority_and_worker(tmp_path)
    authoritative = load_project(authority / "docs" / "tasklist.json")
    authoritative.phases[0].slices[0].notes = "manual authority edit"
    _write_tasklist(authority, authoritative)
    dirty_bytes = (authority / "docs" / "tasklist.json").read_bytes()
    local = load_project(worker / "docs" / "tasklist.json")
    local.phases[0].slices[0].status = Status.IN_PROGRESS
    _write_tasklist(worker, local)

    r = run_cli("config", "migrate-from-local", "--authority-root", str(authority), "--accept-local", cwd=worker)

    assert r.returncode == 1
    assert "authoritative docs/tasklist.json has unstaged changes" in r.stderr
    assert (authority / "docs" / "tasklist.json").read_bytes() == dirty_bytes
    assert not (authority / ".tasktool" / "config.json").exists()


def test_missing_config_detached_authority_fails_without_empty_branch_config(tmp_path: Path) -> None:
    authority, worker = _authority_and_worker(tmp_path)
    _git(authority, "checkout", "--detach", "HEAD")
    local = load_project(worker / "docs" / "tasklist.json")
    local.phases[0].slices[0].status = Status.IN_PROGRESS
    _write_tasklist(worker, local)

    r = run_cli("config", "migrate-from-local", "--authority-root", str(authority), "--accept-local", cwd=worker)

    assert r.returncode == 1
    assert "authority checkout must be on a branch" in r.stderr
    assert not (authority / ".tasktool" / "config.json").exists()


def test_dry_run_prints_diff_and_writes_nothing(tmp_path: Path) -> None:
    authority, worker = _authority_and_worker(tmp_path)
    before = (authority / "docs" / "tasklist.json").read_text(encoding="utf-8")
    local = load_project(worker / "docs" / "tasklist.json")
    local.phases[0].slices[0].notes = "local note"
    _write_tasklist(worker, local)

    r = run_cli("config", "migrate-from-local", "--authority-root", str(authority), "--dry-run", cwd=worker)

    assert r.returncode == 0, r.stderr
    assert "P1.S1" in r.stdout
    assert "notes:" in r.stdout
    assert (authority / "docs" / "tasklist.json").read_text(encoding="utf-8") == before
    assert not (authority / ".tasktool" / "config.json").exists()


def test_accept_local_applies_status_dates_refs_and_notes(tmp_path: Path) -> None:
    authority, worker = _authority_and_worker(tmp_path)
    local = load_project(worker / "docs" / "tasklist.json")
    slc = local.phases[0].slices[0]
    slc.status = Status.DONE
    slc.started = "2026-05-20"
    slc.closed = "2026-05-21"
    slc.refs = ["docs/plans/p1-s1.md"]
    slc.notes = "done locally"
    _write_tasklist(worker, local)

    r = run_cli("config", "migrate-from-local", "--authority-root", str(authority), "--accept-local", cwd=worker)

    assert r.returncode == 0, r.stderr
    migrated = load_project(authority / "docs" / "tasklist.json")
    migrated_slice = migrated.phases[0].slices[0]
    assert migrated_slice.status == Status.DONE
    assert migrated_slice.started == "2026-05-20"
    assert migrated_slice.closed == "2026-05-21"
    assert migrated_slice.refs == ["docs/plans/p1-s1.md"]
    assert migrated_slice.notes == "done locally"


def test_accept_authoritative_is_noop(tmp_path: Path) -> None:
    authority, worker = _authority_and_worker(tmp_path)
    before = (authority / "docs" / "tasklist.json").read_text(encoding="utf-8")
    local = load_project(worker / "docs" / "tasklist.json")
    local.phases[0].slices[0].status = Status.IN_PROGRESS
    _write_tasklist(worker, local)

    r = run_cli(
        "config",
        "migrate-from-local",
        "--authority-root",
        str(authority),
        "--accept-authoritative",
        cwd=worker,
    )

    assert r.returncode == 0, r.stderr
    assert "P1.S1" in r.stdout
    assert (authority / "docs" / "tasklist.json").read_text(encoding="utf-8") == before
    assert not (authority / ".tasktool" / "config.json").exists()


def test_no_drift_exits_cleanly(tmp_path: Path) -> None:
    authority, worker = _authority_and_worker(tmp_path)

    r = run_cli("config", "migrate-from-local", "--authority-root", str(authority), "--accept-local", cwd=worker)

    assert r.returncode == 0, r.stderr
    assert "no drift detected" in r.stdout
    assert not (authority / ".tasktool" / "config.json").exists()


def test_non_tty_missing_policy_errors(tmp_path: Path) -> None:
    authority, worker = _authority_and_worker(tmp_path)
    local = load_project(worker / "docs" / "tasklist.json")
    local.phases[0].slices[0].status = Status.IN_PROGRESS
    _write_tasklist(worker, local)

    r = run_cli("config", "migrate-from-local", "--authority-root", str(authority), cwd=worker)

    assert r.returncode == 1
    assert "migrate-from-local requires one of --accept-local or --accept-authoritative" in r.stderr


def test_unrelated_repo_roots_error(tmp_path: Path) -> None:
    authority = _repo(tmp_path, "authority")
    local = _repo(tmp_path, "local")
    _write_tasklist(authority, _project())
    _write_tasklist(local, _project(slice_status=Status.IN_PROGRESS))

    r = run_cli("config", "migrate-from-local", "--authority-root", str(authority), "--accept-local", cwd=local)

    assert r.returncode == 1
    assert "authority root and local root are not the same repository" in r.stderr


def test_authoritative_only_rows_are_preserved_under_accept_local(tmp_path: Path) -> None:
    authority, worker = _authority_and_worker(tmp_path)
    auth = load_project(authority / "docs" / "tasklist.json")
    auth.cross_cutting.append(CrossCutting(id="X9", title="main only", created="2026-05-20"))
    _write_tasklist(authority, auth)
    _git(authority, "add", "docs/tasklist.json")
    local = load_project(worker / "docs" / "tasklist.json")
    local.phases[0].slices[0].status = Status.IN_PROGRESS
    _write_tasklist(worker, local)

    r = run_cli("config", "migrate-from-local", "--authority-root", str(authority), "--accept-local", cwd=worker)

    assert r.returncode == 0, r.stderr
    assert "authoritative-only (kept)" in r.stdout
    migrated = load_project(authority / "docs" / "tasklist.json")
    assert any(item.id == "X9" for item in migrated.cross_cutting)
    assert migrated.phases[0].slices[0].status == Status.IN_PROGRESS


def test_nested_task_divergence_migrates(tmp_path: Path) -> None:
    authority, worker = _authority_and_worker(tmp_path)
    auth = load_project(authority / "docs" / "tasklist.json")
    auth.phases[0].slices[0].tasks.append(Task(id="T1", title="Task", created="2026-05-20"))
    _write_tasklist(authority, auth)
    _git(authority, "add", "docs/tasklist.json")
    local = load_project(worker / "docs" / "tasklist.json")
    local.phases[0].slices[0].tasks.append(
        Task(
            id="T1",
            title="Task",
            created="2026-05-20",
            status=Status.DONE,
            closed="2026-05-21",
            refs=["docs/task.md"],
            notes="nested local",
        )
    )
    _write_tasklist(worker, local)

    r = run_cli("config", "migrate-from-local", "--authority-root", str(authority), "--accept-local", cwd=worker)

    assert r.returncode == 0, r.stderr
    migrated_task = load_project(authority / "docs" / "tasklist.json").phases[0].slices[0].tasks[0]
    assert migrated_task.status == Status.DONE
    assert migrated_task.closed == "2026-05-21"
    assert migrated_task.refs == ["docs/task.md"]
    assert migrated_task.notes == "nested local"


def test_status_transitions_emit_notify_events(tmp_path: Path) -> None:
    authority, worker = _authority_and_worker(tmp_path)
    log = tmp_path / "notify.jsonl"
    local = load_project(worker / "docs" / "tasklist.json")
    local.phases[0].slices[0].status = Status.IN_PROGRESS
    _write_tasklist(worker, local)

    r = run_cli(
        "config",
        "migrate-from-local",
        "--authority-root",
        str(authority),
        "--accept-local",
        cwd=worker,
        env={
            "SUPERSTAR_NOTIFY_DISABLE": "0",
            "SUPERSTAR_NOTIFY_DRY_RUN": "1",
            "SUPERSTAR_NOTIFY_LOG": str(log),
        },
    )

    assert r.returncode == 0, r.stderr
    events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert events[-1]["type"] == "tasktool-status"
    assert events[-1]["id"] == "P1.S1"
    assert events[-1]["kind"] == "slice"
    assert events[-1]["status"] == "in_progress"
