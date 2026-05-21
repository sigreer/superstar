from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = ROOT
INSTALLER = ROOT / "skills" / "external-review" / "install.sh"


def _seed_fake_source(path: Path, version: str) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "VERSION").write_text(version + "\n")
    script_dir = path / "skills" / "external-review" / "scripts"
    script_dir.mkdir(parents=True)
    stub = script_dir / "external-reviewer.py"
    stub.write_text("#!/usr/bin/env python3\nimport sys\nprint('STUB INVOKED')\nsys.exit(0)\n")
    stub.chmod(0o755)
    lib_dir = path / "scripts" / "lib"
    lib_dir.mkdir(parents=True)
    real_fragment = REPO_ROOT / "scripts" / "lib" / "shim-version-check.sh"
    (lib_dir / "shim-version-check.sh").write_text(real_fragment.read_text())
    installer_dir = path / "skills" / "external-review"
    real_installer = REPO_ROOT / "skills" / "external-review" / "install.sh"
    (installer_dir / "install.sh").write_text(real_installer.read_text())
    (installer_dir / "install.sh").chmod(0o755)
    return path


def _run_installer(*, source_root: Path, bin_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(source_root / "skills" / "external-review" / "install.sh")],
        env={
            "EXTERNAL_REVIEWER_SOURCE_ROOT": str(source_root),
            "EXTERNAL_REVIEWER_BIN": str(bin_dir),
            "HOME": str(bin_dir),
            "PATH": os.environ["PATH"],
        },
        capture_output=True, text=True, check=True,
    )


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
    (current_root / "VERSION").write_text("0.0.0\n")
    lib_dir = current_root / "scripts" / "lib"
    lib_dir.mkdir(parents=True)
    (lib_dir / "shim-version-check.sh").write_text(
        (REPO_ROOT / "scripts" / "lib" / "shim-version-check.sh").read_text()
    )

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


def test_generated_shim_carries_stamp_header(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    source_root = _seed_fake_source(tmp_path / "src", version="1.0.0")
    _run_installer(source_root=source_root, bin_dir=bin_dir)
    text = (bin_dir / "external-reviewer").read_text(encoding="utf-8")
    assert "# superstar-shim" in text
    assert "superstar-shim-name: external-reviewer" in text
    assert "superstar-shim-version: 1.0.0" in text
    assert "superstar-shim-source-root:" in text
    assert "superstar-shim-installer: skills/external-review/install.sh" in text
    assert "superstar-shim-generated-at:" in text


def test_generated_shim_embeds_version_check_fragment(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    source_root = _seed_fake_source(tmp_path / "src", version="1.0.0")
    _run_installer(source_root=source_root, bin_dir=bin_dir)
    text = (bin_dir / "external-reviewer").read_text(encoding="utf-8")
    assert "__superstar_check_version()" in text
    assert '__superstar_check_version "1.0.0"' in text


def test_generated_shim_refuses_when_source_version_drifts(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    source_root = _seed_fake_source(tmp_path / "src", version="1.0.0")
    _run_installer(source_root=source_root, bin_dir=bin_dir)
    (source_root / "VERSION").write_text("1.0.1\n")
    result = subprocess.run(
        [str(bin_dir / "external-reviewer"), "--help"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert "external-reviewer shim is 1.0.0 but Superstar source is 1.0.1" in result.stderr
