"""Tests for skills/project-setup/install-reviewer-agent.sh."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER = REPO_ROOT / "skills" / "project-setup" / "install-reviewer-agent.sh"
FRAGMENT = REPO_ROOT / "scripts" / "lib" / "shim-version-check.sh"


def _seed_source(path: Path, version: str) -> Path:
    path.mkdir(parents=True)
    (path / "VERSION").write_text(version + "\n")
    script_dir = path / "skills" / "project-setup" / "scripts"
    script_dir.mkdir(parents=True)
    real = REPO_ROOT / "skills" / "project-setup" / "scripts" / "reviewer-agent"
    (script_dir / "reviewer-agent").write_text(real.read_text())
    (script_dir / "reviewer-agent").chmod(0o755)
    lib_dir = path / "scripts" / "lib"
    lib_dir.mkdir(parents=True)
    (lib_dir / "shim-version-check.sh").write_text(FRAGMENT.read_text())
    return path


def _run(source_root: Path, bin_dir: Path, *, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    env = {
        "EXTERNAL_REVIEWER_SOURCE_ROOT": str(source_root),
        "EXTERNAL_REVIEWER_BIN": str(bin_dir),
        "HOME": str(bin_dir),
        "PATH": os.environ["PATH"],
    }
    return subprocess.run(
        ["bash", str(INSTALLER), *(extra_args or [])],
        env=env, capture_output=True, text=True, check=False,
    )


def test_install_writes_redirect_shim(tmp_path: Path) -> None:
    source = _seed_source(tmp_path / "src", "1.0.0")
    bin_dir = tmp_path / "bin"
    result = _run(source, bin_dir)
    assert result.returncode == 0, result.stderr
    target = bin_dir / "reviewer-agent"
    assert target.exists()
    text = target.read_text()
    assert "superstar-shim-name: reviewer-agent" in text
    assert "superstar-shim-version: 1.0.0" in text
    assert "skills/project-setup/scripts/reviewer-agent" in text
    assert os.access(target, os.X_OK)


def test_install_passes_bash_n_syntax_check(tmp_path: Path) -> None:
    source = _seed_source(tmp_path / "src", "1.0.0")
    bin_dir = tmp_path / "bin"
    _run(source, bin_dir)
    target = bin_dir / "reviewer-agent"
    result = subprocess.run(["bash", "-n", str(target)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_install_refuses_to_overwrite_unstamped_file(tmp_path: Path) -> None:
    source = _seed_source(tmp_path / "src", "1.0.0")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "reviewer-agent").write_text("#!/usr/bin/env bash\necho hand-edited\n")
    (bin_dir / "reviewer-agent").chmod(0o755)
    result = _run(source, bin_dir)
    assert result.returncode != 0
    assert "not a reviewer-agent shim" in result.stderr or "not a superstar-shim" in result.stderr


def test_install_overwrites_unstamped_file_with_force(tmp_path: Path) -> None:
    source = _seed_source(tmp_path / "src", "1.0.0")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "reviewer-agent").write_text("#!/usr/bin/env bash\necho hand-edited\n")
    (bin_dir / "reviewer-agent").chmod(0o755)
    result = _run(source, bin_dir, extra_args=["--force"])
    assert result.returncode == 0, result.stderr
    assert "superstar-shim-name: reviewer-agent" in (bin_dir / "reviewer-agent").read_text()


def test_generated_shim_refuses_on_version_drift(tmp_path: Path) -> None:
    source = _seed_source(tmp_path / "src", "1.0.0")
    bin_dir = tmp_path / "bin"
    _run(source, bin_dir)
    (source / "VERSION").write_text("1.0.1\n")
    result = subprocess.run(
        [str(bin_dir / "reviewer-agent")],
        env={"PATH": os.environ["PATH"]},
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert "reviewer-agent shim is 1.0.0 but Superstar source is 1.0.1" in result.stderr
