from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


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


def _read_config(root: Path) -> dict:
    return json.loads((root / ".tasktool" / "config.json").read_text(encoding="utf-8"))


def _write_config(root: Path, body: dict) -> None:
    path = root / ".tasktool" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body), encoding="utf-8")


def test_config_init_local_writes_config_and_stages_it(tmp_path: Path) -> None:
    _git_init(tmp_path)

    r = run_cli("config", "init-local", cwd=tmp_path)

    assert r.returncode == 0, r.stdout + r.stderr
    assert "local" in r.stderr
    assert "will not be routed" in r.stderr
    raw = _read_config(tmp_path)
    assert raw["tasklist"]["mutation_mode"] == "local"
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    assert ".tasktool/config.json" in staged.stdout.splitlines()


def test_config_init_local_is_idempotent_for_existing_local_config(tmp_path: Path) -> None:
    _git_init(tmp_path)
    _write_config(
        tmp_path,
        {
            "schema_version": 1,
            "tasklist": {
                "mutation_mode": "local",
                "authoritative_branch": "main",
            },
        },
    )

    r = run_cli("config", "init-local", cwd=tmp_path)

    assert r.returncode == 0, r.stdout + r.stderr
    assert _read_config(tmp_path)["tasklist"]["mutation_mode"] == "local"


def test_config_init_local_then_init_succeeds(tmp_path: Path) -> None:
    _git_init(tmp_path)

    r = run_cli("config", "init-local", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    r = run_cli("init", "--project", "demo", cwd=tmp_path)

    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / "docs" / "tasklist.json").exists()


def test_config_init_local_refuses_overwriting_authoritative_config(tmp_path: Path) -> None:
    _git_init(tmp_path)
    _write_config(
        tmp_path,
        {
            "schema_version": 1,
            "tasklist": {
                "mutation_mode": "authoritative-checkout",
                "authoritative_branch": "main",
            },
        },
    )

    r = run_cli("config", "init-local", cwd=tmp_path)

    assert r.returncode == 1
    assert "already configured" in r.stderr
    assert "refusing to overwrite" in r.stderr
    assert _read_config(tmp_path)["tasklist"]["mutation_mode"] == "authoritative-checkout"


def test_config_init_local_completes_config_that_omits_mutation_mode(tmp_path: Path) -> None:
    _git_init(tmp_path)
    _write_config(
        tmp_path,
        {
            "schema_version": 1,
            "tasklist": {
                "authoritative_branch": "main",
            },
        },
    )

    r = run_cli("config", "init-local", cwd=tmp_path)

    assert r.returncode == 0, r.stdout + r.stderr
    raw = _read_config(tmp_path)
    assert raw["tasklist"]["mutation_mode"] == "local"
    assert raw["tasklist"]["authoritative_branch"] == "main"
