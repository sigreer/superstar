"""Tests for tools/tasktool/install.sh (shim install path, not the hook path)."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
INSTALLER = REPO_ROOT / "tools" / "tasktool" / "install.sh"
FRAGMENT = REPO_ROOT / "scripts" / "lib" / "shim-version-check.sh"


def _seed_source(path: Path, version: str) -> Path:
    path.mkdir(parents=True)
    (path / "VERSION").write_text(version + "\n")
    tools = path / "tools" / "tasktool"
    tools.mkdir(parents=True)
    (tools / "__init__.py").write_text("")
    (tools / "__main__.py").write_text("print('STUB INVOKED')\n")
    install_target = tools / "install.sh"
    install_target.write_text((REPO_ROOT / "tools" / "tasktool" / "install.sh").read_text())
    install_target.chmod(0o755)
    lib_dir = path / "scripts" / "lib"
    lib_dir.mkdir(parents=True)
    (lib_dir / "shim-version-check.sh").write_text(FRAGMENT.read_text())
    return path


def _run(source: Path, home: Path) -> subprocess.CompletedProcess:
    env = {
        "HOME": str(home),
        "PATH": os.environ["PATH"],
    }
    return subprocess.run(
        ["bash", str(source / "tools" / "tasktool" / "install.sh")],
        env=env, capture_output=True, text=True, check=False,
    )


def test_install_writes_stamped_shim(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".local" / "bin").mkdir(parents=True)
    source = _seed_source(tmp_path / "src", "1.0.0")
    result = _run(source, home)
    assert result.returncode == 0, result.stderr
    target = home / ".local" / "bin" / "tasktool"
    text = target.read_text()
    assert "superstar-shim-name: tasktool" in text
    assert "superstar-shim-version: 1.0.0" in text


def test_shim_refuses_on_drift(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".local" / "bin").mkdir(parents=True)
    source = _seed_source(tmp_path / "src", "1.0.0")
    _run(source, home)
    (source / "VERSION").write_text("1.0.1\n")
    result = subprocess.run(
        [str(home / ".local" / "bin" / "tasktool")],
        env={"PATH": os.environ["PATH"]},
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert "tasktool shim is 1.0.0 but Superstar source is 1.0.1" in result.stderr
