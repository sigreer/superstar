"""Tests for the plain-format support added to scripts/bump-version.sh."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_SCRIPT = REPO_ROOT / "scripts" / "bump-version.sh"


def _seed_repo(tmp_path: Path, version: str) -> Path:
    """Build an isolated fake repo so the script's own REPO_ROOT resolution
    (`cd $SCRIPT_DIR/.. && pwd`) lands inside tmp_path and cannot mutate the
    real checkout."""
    (tmp_path / "package.json").write_text(json.dumps({"version": version}, indent=2) + "\n")
    (tmp_path / "VERSION").write_text(version + "\n")
    config = {
        "files": [
            {"path": "package.json", "field": "version"},
            {"path": "VERSION", "format": "plain"},
        ],
        "audit": {"exclude": []},
    }
    (tmp_path / ".version-bump.json").write_text(json.dumps(config, indent=2) + "\n")
    (tmp_path / "scripts").mkdir(exist_ok=True)
    fake_script = tmp_path / "scripts" / "bump-version.sh"
    fake_script.symlink_to(REAL_SCRIPT)
    return tmp_path


def _run(script_args: list[str], repo: Path) -> subprocess.CompletedProcess:
    fake_script = repo / "scripts" / "bump-version.sh"
    assert fake_script.exists(), "fake script symlink missing — call _seed_repo first"
    return subprocess.run(
        ["bash", str(fake_script), *script_args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def test_check_lists_plain_version(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path, "1.2.3")
    result = _run(["--check"], repo)
    assert result.returncode == 0, result.stderr
    assert "VERSION" in result.stdout
    assert "1.2.3" in result.stdout


def test_bump_writes_plain_version(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path, "1.2.3")
    result = _run(["1.2.4"], repo)
    assert result.returncode == 0, result.stderr
    assert (repo / "VERSION").read_text().strip() == "1.2.4"
    assert json.loads((repo / "package.json").read_text())["version"] == "1.2.4"


def test_check_detects_drift_between_plain_and_json(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path, "1.2.3")
    (repo / "VERSION").write_text("1.2.4\n")
    result = _run(["--check"], repo)
    assert result.returncode != 0
    assert "DRIFT" in result.stdout
