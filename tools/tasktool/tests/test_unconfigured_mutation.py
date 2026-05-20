from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_DIR = REPO_ROOT / "tools"


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "tasktool", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "--allow-empty",
            "-m",
            "init",
        ],
        cwd=path,
        check=True,
        capture_output=True,
    )


def _write_empty_tasklist(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "tasklist.json").write_text(
        '{"schema_version":1,"project":"demo","phases":[],'
        '"cross_cutting":[],"archived_phases":[]}',
        encoding="utf-8",
    )


def _write_tasklist_with_rows(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "docs" / "tasklist.json").write_text(
        '{"schema_version":1,"project":"demo",'
        '"phases":[{"id":"P1","title":"p","created":"2026-05-20","status":"ready",'
        '"started":null,"closed":null,"spec_path":null,"plan_path":null,'
        '"planning_path":null,"phase_reviewer_chain":null,"notes":"","slices":['
        '{"id":"S1","title":"s","created":"2026-05-20","status":"ready",'
        '"started":null,"closed":null,"blocked_on":null,"depends_on":[],'
        '"planning_status":"proposed","parallel_group":null,"plan_path":null,'
        '"refs":[],"notes":"","reviewer_chain":null,"tasks":[]}]}],'
        '"cross_cutting":[{"id":"X1","title":"x","created":"2026-05-20","status":"ready",'
        '"refs":[],"notes":"","started":null,"closed":null}],'
        '"archived_phases":[]}',
        encoding="utf-8",
    )


def test_init_errors_without_authority_config(tmp_path: Path) -> None:
    _git_init(tmp_path)
    r = run_cli("init", "--project", "demo", cwd=tmp_path)
    assert r.returncode != 0
    assert "no authoritative-checkout routing configured" in r.stderr
    assert "tasktool config init-authority" in r.stderr
    assert "tasktool config migrate-from-local" in r.stderr
    assert "tasktool config init-local" in r.stderr
    assert not (tmp_path / "docs" / "tasklist.json").exists()


def test_start_errors_without_authority_config(tmp_path: Path) -> None:
    _git_init(tmp_path)
    _write_tasklist_with_rows(tmp_path)
    r = run_cli("start", "X1", cwd=tmp_path)
    assert r.returncode != 0
    assert "no authoritative-checkout routing configured" in r.stderr


def test_validate_without_normalise_works_unconfigured(tmp_path: Path) -> None:
    _git_init(tmp_path)
    _write_empty_tasklist(tmp_path)
    r = run_cli("validate", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


def test_validate_normalise_errors_unconfigured(tmp_path: Path) -> None:
    _git_init(tmp_path)
    _write_empty_tasklist(tmp_path)
    r = run_cli("validate", "--normalise", cwd=tmp_path)
    assert r.returncode != 0
    assert "no authoritative-checkout routing configured" in r.stderr


def test_render_works_unconfigured(tmp_path: Path) -> None:
    _git_init(tmp_path)
    _write_empty_tasklist(tmp_path)
    r = run_cli("render", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.parametrize(
    "readonly_cmd",
    [
        ("render",),
        ("validate",),
        ("brief", "P1.S1"),
        ("schema",),
        ("show", "P1"),
        ("phase-status",),
        ("ready-slices", "P1"),
        ("list",),
        ("next-id", "--kind", "slice", "--phase", "P1"),
    ],
)
def test_other_readonly_commands_work_unconfigured(
    tmp_path: Path,
    readonly_cmd: tuple[str, ...],
) -> None:
    _git_init(tmp_path)
    _write_tasklist_with_rows(tmp_path)
    r = run_cli(*readonly_cmd, cwd=tmp_path)
    assert r.returncode == 0, (
        f"read-only command {readonly_cmd} should succeed without config; "
        f"stdout={r.stdout!r} stderr={r.stderr!r}"
    )
    assert "no authoritative-checkout routing configured" not in r.stderr


def test_explicit_local_mode_still_mutates(tmp_path: Path) -> None:
    _git_init(tmp_path)
    r = run_cli("config", "init-local", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    r = run_cli("init", "--project", "demo", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / "docs" / "tasklist.json").exists()


def test_bootstrap_init_authority_then_init_succeeds(tmp_path: Path) -> None:
    _git_init(tmp_path)
    r = run_cli("config", "init-authority", "--branch", "main", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    r = run_cli("init", "--project", "demo", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / "docs" / "tasklist.json").exists()


def test_bootstrap_init_before_init_authority_fails(tmp_path: Path) -> None:
    _git_init(tmp_path)
    r = run_cli("init", "--project", "demo", cwd=tmp_path)
    assert r.returncode != 0
    assert "no authoritative-checkout routing configured" in r.stderr
    assert not (tmp_path / "docs" / "tasklist.json").exists()
