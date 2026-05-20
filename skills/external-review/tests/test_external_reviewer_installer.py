from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INSTALLER = ROOT / "skills" / "external-review" / "install.sh"


def run_installer(bin_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["EXTERNAL_REVIEWER_BIN"] = str(bin_dir)
    return subprocess.run(
        ["bash", str(INSTALLER), *args],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def run_installer_with_env(
    bin_dir: Path,
    extra_env: dict[str, str],
    *args: str,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["EXTERNAL_REVIEWER_BIN"] = str(bin_dir)
    env.update(extra_env)
    return subprocess.run(
        ["bash", str(INSTALLER), *args],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_installer_writes_source_tree_shim_to_configured_bin(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"

    result = run_installer(bin_dir)

    assert result.returncode == 0, result.stderr
    shim = bin_dir / "external-reviewer"
    assert shim.exists()
    assert os.access(shim, os.X_OK)

    text = shim.read_text(encoding="utf-8")
    assert "external-reviewer shim" in text
    assert "skills/external-review/scripts/external-reviewer.py" in text
    assert "/home/simon/" not in text
    assert "Pointing at" in result.stdout


def test_generated_external_reviewer_help_works_from_any_cwd(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    install = run_installer(bin_dir)
    assert install.returncode == 0, install.stderr

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    other_cwd = tmp_path / "other"
    other_cwd.mkdir()
    result = subprocess.run(
        ["external-reviewer", "--help"],
        cwd=other_cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "review" in result.stdout


def test_installer_can_pin_shim_to_materialized_current_root(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    current_root = tmp_path / "cache" / "superstar-dev" / "superstar" / "current"
    script_dir = current_root / "skills" / "external-review" / "scripts"
    script_dir.mkdir(parents=True)
    source = script_dir / "external-reviewer.py"
    source.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "print('current external reviewer')\n",
        encoding="utf-8",
    )
    source.chmod(0o755)

    result = run_installer_with_env(
        bin_dir,
        {"EXTERNAL_REVIEWER_SOURCE_ROOT": str(current_root)},
    )

    assert result.returncode == 0, result.stderr
    text = (bin_dir / "external-reviewer").read_text(encoding="utf-8")
    assert "/current/skills/external-review/scripts/external-reviewer.py" in text


def test_installer_refuses_to_overwrite_unknown_command(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    target = bin_dir / "external-reviewer"
    target.write_text("#!/usr/bin/env bash\necho unknown\n", encoding="utf-8")
    target.chmod(0o755)

    result = run_installer(bin_dir)

    assert result.returncode != 0
    assert "not an external-reviewer shim" in result.stderr
    assert "echo unknown" in target.read_text(encoding="utf-8")


def test_installer_force_overwrites_unknown_command(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    target = bin_dir / "external-reviewer"
    target.write_text("#!/usr/bin/env bash\necho unknown\n", encoding="utf-8")
    target.chmod(0o755)

    result = run_installer(bin_dir, "--force")

    assert result.returncode == 0, result.stderr
    assert "external-reviewer shim" in target.read_text(encoding="utf-8")
