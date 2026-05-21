"""Tests for tools/tasktool/hook_handshake.py."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from tasktool import hook_handshake

REPO_ROOT = Path(__file__).resolve().parents[3]


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)


def _write_hook(repo: Path, *, version: str, source_root: str) -> Path:
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text(
        "#!/usr/bin/env sh\n"
        "# tasktool-pre-commit-hook v1\n"
        "# superstar-hook\n"
        "# superstar-hook-name: tasktool-pre-commit\n"
        f"# superstar-hook-version: {version}\n"
        f"# superstar-hook-source-root: {source_root}\n"
        "# superstar-hook-installer: tools/tasktool/install.sh --hook\n"
        "# superstar-hook-generated-at: 2026-05-21T00:00:00Z\n"
        "exit 0\n"
    )
    hook.chmod(0o755)
    return hook


def test_no_git_repo_silent(tmp_path: Path) -> None:
    assert hook_handshake.check_pre_commit_hook(cwd=tmp_path) is None


def test_no_hook_silent(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    assert hook_handshake.check_pre_commit_hook(cwd=tmp_path) is None


def test_non_tasktool_hook_silent(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/usr/bin/env sh\n# someone-elses-hook\nexit 0\n")
    hook.chmod(0o755)
    assert hook_handshake.check_pre_commit_hook(cwd=tmp_path) is None


def test_matching_version_silent(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    _write_hook(tmp_path, version="1.0.0", source_root=str(source))
    assert hook_handshake.check_pre_commit_hook(cwd=tmp_path) is None


def test_drift_returns_error(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "VERSION").write_text("1.0.1\n")
    hook = _write_hook(tmp_path, version="1.0.0", source_root=str(source))
    msg = hook_handshake.check_pre_commit_hook(cwd=tmp_path)
    assert msg is not None
    assert "tasktool pre-commit hook is 1.0.0 but Superstar source is 1.0.1" in msg
    assert str(hook) in msg
    assert str(source / "tools" / "tasktool" / "install.sh") in msg


def test_home_expansion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _init_git_repo(tmp_path)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    source = fake_home / "src"
    source.mkdir()
    (source / "VERSION").write_text("1.0.1\n")
    _write_hook(tmp_path, version="1.0.0", source_root="$HOME/src")
    msg = hook_handshake.check_pre_commit_hook(cwd=tmp_path)
    assert msg is not None
    assert str(source) in msg


def test_missing_source_version_silent(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    _write_hook(tmp_path, version="1.0.0", source_root=str(source))
    assert hook_handshake.check_pre_commit_hook(cwd=tmp_path) is None


def test_tasktool_main_exits_on_hook_drift(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "VERSION").write_text("1.0.1\n")
    _write_hook(tmp_path, version="1.0.0", source_root=str(source))
    result = subprocess.run(
        ["python3", "-m", "tasktool", "--help"],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "tools")},
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert "tasktool pre-commit hook is 1.0.0 but Superstar source is 1.0.1" in result.stderr


def test_drift_returns_error_in_worktree(tmp_path: Path) -> None:
    # Create a primary git repo, make a commit so a branch exists, then add a
    # linked worktree. The pre-commit hook lives in the common-dir of the
    # primary repo (resolved via `git rev-parse --git-path hooks/pre-commit`
    # from inside the linked worktree).
    primary = tmp_path / "primary"
    primary.mkdir()
    _init_git_repo(primary)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=primary, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=primary, check=True)
    (primary / "README").write_text("hi\n")
    subprocess.run(["git", "add", "README"], cwd=primary, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=primary, check=True)

    worktree = tmp_path / "wt"
    subprocess.run(
        ["git", "worktree", "add", "-q", "-b", "feat", str(worktree)],
        cwd=primary, check=True,
    )

    # Sanity-check: from inside the worktree, .git is a file (gitdir pointer).
    assert (worktree / ".git").is_file()

    source = tmp_path / "src"
    source.mkdir()
    (source / "VERSION").write_text("1.0.1\n")

    # Resolve the hook path the same way handshake does and write a stale
    # stamped hook there (in the primary repo's common-dir hooks/).
    git_path = subprocess.run(
        ["git", "rev-parse", "--git-path", "hooks/pre-commit"],
        cwd=worktree, capture_output=True, text=True, check=True,
    ).stdout.strip()
    hook_path = Path(git_path)
    if not hook_path.is_absolute():
        # repo_top from inside the worktree should be the worktree path
        repo_top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=worktree, capture_output=True, text=True, check=True,
        ).stdout.strip()
        hook_path = Path(repo_top) / hook_path
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(
        "#!/usr/bin/env sh\n"
        "# tasktool-pre-commit-hook v1\n"
        "# superstar-hook\n"
        "# superstar-hook-name: tasktool-pre-commit\n"
        "# superstar-hook-version: 1.0.0\n"
        f"# superstar-hook-source-root: {source}\n"
        "# superstar-hook-installer: tools/tasktool/install.sh --hook\n"
        "# superstar-hook-generated-at: 2026-05-21T00:00:00Z\n"
        "exit 0\n"
    )
    hook_path.chmod(0o755)

    msg = hook_handshake.check_pre_commit_hook(cwd=worktree)
    assert msg is not None, f"expected drift message; got None. hook_path={hook_path}"
    assert "tasktool pre-commit hook is 1.0.0 but Superstar source is 1.0.1" in msg


def test_tasktool_main_runs_normally_when_hook_ok(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    _write_hook(tmp_path, version="1.0.0", source_root=str(source))
    result = subprocess.run(
        ["python3", "-m", "tasktool", "--help"],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "tools")},
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0
