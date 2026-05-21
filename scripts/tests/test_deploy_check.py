"""Tests for scripts/deploy.sh --check status lattice."""
from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEPLOY = REPO_ROOT / "scripts" / "deploy.sh"


def _make_stamped_shim(path: Path, *, name: str, version: str, source_root: str, installer: str = "skills/external-review/install.sh") -> None:
    path.write_text(textwrap.dedent(f"""\
        #!/usr/bin/env bash
        # superstar-shim
        # superstar-shim-name: {name}
        # superstar-shim-version: {version}
        # superstar-shim-source-root: {source_root}
        # superstar-shim-installer: {installer}
        # superstar-shim-generated-at: 2026-05-21T00:00:00Z
        exec true
    """))
    path.chmod(0o755)


def _run_check(home: Path, source_root: Path) -> subprocess.CompletedProcess:
    env = {
        "HOME": str(home),
        "SUPERSTAR_SOURCE_ROOT": str(source_root),
        "PATH": os.environ["PATH"],
    }
    return subprocess.run(
        ["bash", str(DEPLOY), "--check"],
        env=env, capture_output=True, text=True, check=False,
    )


def test_check_exits_zero_when_all_ok(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    for name in ("external-reviewer", "reviewer-agent", "tasktool"):
        _make_stamped_shim(home / ".local" / "bin" / name, name=name, version="1.0.0", source_root=str(source))
    result = _run_check(home, source)
    assert result.returncode == 0, result.stdout + result.stderr


def test_check_exits_nonzero_on_drift(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    _make_stamped_shim(home / ".local" / "bin" / "external-reviewer", name="external-reviewer", version="0.9.0", source_root=str(source))
    _make_stamped_shim(home / ".local" / "bin" / "reviewer-agent", name="reviewer-agent", version="1.0.0", source_root=str(source))
    _make_stamped_shim(home / ".local" / "bin" / "tasktool", name="tasktool", version="1.0.0", source_root=str(source))
    result = _run_check(home, source)
    assert result.returncode != 0
    assert "DRIFT" in result.stdout


def test_check_exits_nonzero_on_malformed(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    (home / ".local" / "bin" / "external-reviewer").write_text(
        "#!/usr/bin/env bash\n# superstar-shim\n# superstar-shim-name: external-reviewer\nexec true\n"
    )
    (home / ".local" / "bin" / "external-reviewer").chmod(0o755)
    _make_stamped_shim(home / ".local" / "bin" / "reviewer-agent", name="reviewer-agent", version="1.0.0", source_root=str(source))
    _make_stamped_shim(home / ".local" / "bin" / "tasktool", name="tasktool", version="1.0.0", source_root=str(source))
    result = _run_check(home, source)
    assert result.returncode != 0
    assert "MALFORMED" in result.stdout


def test_check_exits_nonzero_on_missing_target(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    _make_stamped_shim(home / ".local" / "bin" / "external-reviewer", name="external-reviewer", version="1.0.0", source_root=str(source))
    _make_stamped_shim(home / ".local" / "bin" / "reviewer-agent", name="reviewer-agent", version="1.0.0", source_root=str(source))
    result = _run_check(home, source)
    assert result.returncode != 0
    assert "MISSING_TARGET" in result.stdout


def test_check_exits_nonzero_on_missing_source(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    for name in ("external-reviewer", "reviewer-agent", "tasktool"):
        _make_stamped_shim(home / ".local" / "bin" / name, name=name, version="1.0.0", source_root="/nonexistent/path")
    result = _run_check(home, source)
    assert result.returncode != 0
    assert "MISSING_SOURCE" in result.stdout


def test_check_zero_on_source_root_info_only(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source_a = tmp_path / "src-a"; source_a.mkdir(); (source_a / "VERSION").write_text("1.0.0\n")
    source_b = tmp_path / "src-b"; source_b.mkdir(); (source_b / "VERSION").write_text("1.0.0\n")
    _make_stamped_shim(home / ".local" / "bin" / "external-reviewer", name="external-reviewer", version="1.0.0", source_root=str(source_a))
    _make_stamped_shim(home / ".local" / "bin" / "reviewer-agent", name="reviewer-agent", version="1.0.0", source_root=str(source_b))
    _make_stamped_shim(home / ".local" / "bin" / "tasktool", name="tasktool", version="1.0.0", source_root=str(source_b))
    result = _run_check(home, source_a)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SOURCE_ROOT_INFO" in result.stdout or "source-root differs" in result.stdout.lower()


def test_check_home_literal_expanded_in_output(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = home / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    for name in ("external-reviewer", "reviewer-agent", "tasktool"):
        _make_stamped_shim(home / ".local" / "bin" / name, name=name, version="1.0.0", source_root="$HOME/src")
    result = _run_check(home, source)
    assert "$HOME/" not in result.stdout
    assert str(source) in result.stdout
