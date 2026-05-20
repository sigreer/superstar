from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SHIM = ROOT / "skills" / "project-setup" / "scripts" / "external-reviewer-shim.py"


def run_shim(path: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATH"] = f"{path}:{env.get('PATH', '')}"
    return subprocess.run(
        [sys.executable, str(SHIM), *args],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_compat_shim_delegates_to_global_external_reviewer(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "external-reviewer"
    log = tmp_path / "args.txt"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        f"printf '%s\\n' \"$@\" > {log}\n"
        "echo delegated\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)

    result = run_shim(str(bin_dir), "review", "--kind", "spec")

    assert result.returncode == 0
    assert result.stdout.strip() == "delegated"
    assert log.read_text(encoding="utf-8").splitlines() == ["review", "--kind", "spec"]


def test_compat_shim_missing_global_command_exits_127(tmp_path: Path) -> None:
    bin_dir = tmp_path / "empty"
    bin_dir.mkdir()

    result = run_shim(str(bin_dir), "review")

    assert result.returncode == 127
    assert "`external-reviewer` is not on PATH" in result.stderr
    assert "skills/external-review/install.sh" in result.stderr


def test_compat_shim_refuses_self_resolution(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "external-reviewer"
    fake.symlink_to(SHIM)

    result = run_shim(str(bin_dir), "review")

    assert result.returncode == 127
    assert "resolved `external-reviewer` back to itself" in result.stderr
