"""Direct tests for scripts/lib/shim-version-check.sh."""
from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FRAGMENT = REPO_ROOT / "scripts" / "lib" / "shim-version-check.sh"


def _run_fragment(tmp_path: Path, shim_version: str, source_version: str | None) -> subprocess.CompletedProcess:
    """Source the fragment in a synthetic harness; call the function; return result."""
    source_root = tmp_path / "fake-source"
    source_root.mkdir()
    if source_version is not None:
        (source_root / "VERSION").write_text(source_version + "\n")
    script = textwrap.dedent(f"""
        #!/usr/bin/env bash
        source "{FRAGMENT}"
        __superstar_check_version "{shim_version}" "test-shim" "{source_root}" "skills/test/install.sh"
        echo "REACHED_END"
    """)
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=False)


def test_versions_match_exec_continues(tmp_path: Path) -> None:
    result = _run_fragment(tmp_path, "1.0.0", "1.0.0")
    assert result.returncode == 0
    assert "REACHED_END" in result.stdout


def test_version_drift_hard_exits(tmp_path: Path) -> None:
    result = _run_fragment(tmp_path, "1.0.0", "1.0.1")
    assert result.returncode == 1
    assert "REACHED_END" not in result.stdout
    assert "test-shim shim is 1.0.0 but Superstar source is 1.0.1" in result.stderr
    assert "skills/test/install.sh" in result.stderr


def test_missing_version_file_exec_continues(tmp_path: Path) -> None:
    """No VERSION file at the source root must NOT block exec."""
    result = _run_fragment(tmp_path, "1.0.0", None)
    assert result.returncode == 0
    assert "REACHED_END" in result.stdout


def test_empty_shim_version_exec_continues(tmp_path: Path) -> None:
    result = _run_fragment(tmp_path, "", "1.0.0")
    assert result.returncode == 0
    assert "REACHED_END" in result.stdout
