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


def _run_check(home: Path, source_root: Path, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = {
        "HOME": str(home),
        "SUPERSTAR_SOURCE_ROOT": str(source_root),
        "PATH": os.environ["PATH"],
    }
    # Default cwd to HOME (a non-git tmp dir) so the new pre-commit hook
    # section doesn't see the surrounding repository's hook by accident.
    effective_cwd = cwd if cwd is not None else home
    return subprocess.run(
        ["bash", str(DEPLOY), "--check"],
        env=env, capture_output=True, text=True, check=False,
        cwd=str(effective_cwd),
    )


def _make_stamped_hook(path: Path, *, version: str, source_root: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(f"""\
        #!/usr/bin/env sh
        # tasktool-pre-commit-hook v1
        # superstar-hook
        # superstar-hook-name: tasktool-pre-commit
        # superstar-hook-version: {version}
        # superstar-hook-source-root: {source_root}
        # superstar-hook-installer: tools/tasktool/install.sh --hook
        # superstar-hook-generated-at: 2026-05-21T00:00:00Z
        exit 0
    """))
    path.chmod(0o755)


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)


def _all_ok_shims(home: Path, source: Path) -> None:
    for name in ("external-reviewer", "reviewer-agent", "tasktool"):
        _make_stamped_shim(home / ".local" / "bin" / name, name=name, version="1.0.0", source_root=str(source))


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


# --- Pre-commit hook row tests ---

def test_check_hook_ok(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    _all_ok_shims(home, source)
    repo = tmp_path / "repo"; repo.mkdir()
    _init_git_repo(repo)
    _make_stamped_hook(repo / ".git" / "hooks" / "pre-commit", version="1.0.0", source_root=str(source))
    result = _run_check(home, source, cwd=repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Pre-commit hook" in result.stdout
    assert "pre-commit" in result.stdout
    assert "OK" in result.stdout


def test_check_hook_drift(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    _all_ok_shims(home, source)
    repo = tmp_path / "repo"; repo.mkdir()
    _init_git_repo(repo)
    _make_stamped_hook(repo / ".git" / "hooks" / "pre-commit", version="0.9.0", source_root=str(source))
    result = _run_check(home, source, cwd=repo)
    assert result.returncode != 0
    assert "DRIFT" in result.stdout
    assert "source-root has 1.0.0" in result.stdout


def test_check_hook_malformed(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    _all_ok_shims(home, source)
    repo = tmp_path / "repo"; repo.mkdir()
    _init_git_repo(repo)
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(
        "#!/usr/bin/env sh\n"
        "# superstar-hook\n"
        "# superstar-hook-name: tasktool-pre-commit\n"
        "exit 0\n"
    )
    hook.chmod(0o755)
    result = _run_check(home, source, cwd=repo)
    assert result.returncode != 0
    assert "MALFORMED" in result.stdout


def test_check_hook_missing_target(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    _all_ok_shims(home, source)
    repo = tmp_path / "repo"; repo.mkdir()
    _init_git_repo(repo)
    # no hook installed
    result = _run_check(home, source, cwd=repo)
    assert result.returncode != 0
    assert "MISSING_TARGET" in result.stdout


def test_check_hook_not_deployed_when_not_tasktool(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    _all_ok_shims(home, source)
    repo = tmp_path / "repo"; repo.mkdir()
    _init_git_repo(repo)
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/usr/bin/env sh\n# someone-elses-hook\nexit 0\n")
    hook.chmod(0o755)
    result = _run_check(home, source, cwd=repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "NOT_DEPLOYED" in result.stdout


def test_check_hook_not_deployed_when_not_in_git(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    _all_ok_shims(home, source)
    not_git = tmp_path / "not-git"; not_git.mkdir()
    result = _run_check(home, source, cwd=not_git)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "NOT_DEPLOYED" in result.stdout
    assert "not in a git working tree" in result.stdout
