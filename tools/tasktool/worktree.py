from __future__ import annotations

import contextlib
import os
import subprocess
import time
from pathlib import Path


class AuthorityError(RuntimeError):
    pass


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=check,
    )


def git_common_dir(root: Path) -> Path:
    out = _git(root, "rev-parse", "--git-common-dir").stdout.strip()
    path = Path(out)
    return path if path.is_absolute() else (root / path).resolve()


def git_current_branch(root: Path) -> str:
    return _git(root, "branch", "--show-current").stdout.strip()


def current_branch_head_sha(root: Path, branch: str) -> str:
    """Return the full 40-char commit SHA at the tip of `branch`."""
    return _git(root, "rev-parse", "--verify", f"refs/heads/{branch}").stdout.strip()


def same_repository(left: Path, right: Path) -> bool:
    try:
        return git_common_dir(left) == git_common_dir(right)
    except subprocess.CalledProcessError:
        return False


def worktree_roots(root: Path) -> list[tuple[Path, str]]:
    result = _git(root, "worktree", "list", "--porcelain")
    rows: list[tuple[Path, str]] = []
    current_path: Path | None = None
    current_branch = ""
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            if current_path is not None:
                rows.append((current_path, current_branch))
            current_path = Path(line.removeprefix("worktree ")).resolve()
            current_branch = ""
        elif line.startswith("branch "):
            current_branch = line.removeprefix("branch refs/heads/")
    if current_path is not None:
        rows.append((current_path, current_branch))
    return rows


def find_authoritative_root(caller_root: Path, *, branch: str) -> Path:
    env_root = os.environ.get("TASKTOOL_AUTHORITY_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    matches = [path for path, item_branch in worktree_roots(caller_root) if item_branch == branch]
    if len(matches) == 1:
        return matches[0]
    raise AuthorityError(
        f"cannot determine authoritative checkout for branch {branch}; "
        "set TASKTOOL_AUTHORITY_ROOT=/absolute/path"
    )


def has_unmerged_paths(root: Path) -> bool:
    out = _git(root, "ls-files", "-u").stdout.strip()
    return bool(out)


def tasklist_has_unsafe_dirty_state(root: Path) -> bool:
    """Return True when tasklist has unstaged changes.

    Staged-only tasklist changes are allowed: they are the serialized pending
    state from earlier tasktool commands in the same authoritative checkout.
    Unstaged tasklist bytes are refused because tasktool cannot attribute them.
    """
    result = _git(root, "status", "--porcelain", "--", "docs/tasklist.json", check=False)
    for line in result.stdout.splitlines():
        if len(line) >= 2 and line[1] != " ":
            return True
    return False


def validate_authoritative_checkout(
    root: Path,
    *,
    expected_branch: str,
    caller_root: Path,
) -> None:
    root = root.resolve()
    if not (root / ".git").exists() and not (root / ".git").is_file():
        raise AuthorityError(f"authoritative_root is not a git checkout: {root}")
    if not same_repository(root, caller_root):
        raise AuthorityError("authoritative_root is not the same repository as caller")
    branch = git_current_branch(root)
    if branch != expected_branch:
        raise AuthorityError(f"authoritative checkout is on {branch!r}; expected branch {expected_branch}")
    if has_unmerged_paths(root):
        raise AuthorityError("authoritative checkout has unresolved merge conflicts")


@contextlib.contextmanager
def tasktool_lock(repo_root: Path, timeout_seconds: float = 30.0):
    timeout_seconds = float(os.environ.get("TASKTOOL_LOCK_TIMEOUT", timeout_seconds))
    lock_path = git_common_dir(repo_root) / "tasktool.lock"
    start = time.monotonic()
    fd = None
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(fd, str(os.getpid()).encode("ascii"))
            break
        except FileExistsError:
            if time.monotonic() - start > timeout_seconds:
                raise AuthorityError(f"timed out waiting for tasktool lock: {lock_path}")
            time.sleep(0.05)
    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
        with contextlib.suppress(FileNotFoundError):
            lock_path.unlink()


def is_inside_worktree(path: Path) -> bool:
    """True iff `path` lies inside a linked (non-primary) git worktree.

    Implementation: `git rev-parse --absolute-git-dir` vs `--git-common-dir`.
    """
    try:
        gd = subprocess.run(
            ["git", "rev-parse", "--absolute-git-dir"],
            cwd=path, text=True, capture_output=True, check=True,
        ).stdout.strip()
        gcd = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=path, text=True, capture_output=True, check=True,
        ).stdout.strip()
        gcd_abs = gcd if Path(gcd).is_absolute() else str((path / gcd).resolve())
        return Path(gd).resolve() != Path(gcd_abs).resolve()
    except subprocess.CalledProcessError:
        return False


def working_tree_dirty(root: Path) -> tuple[bool, list[str]]:
    """Return (dirty, offending_items).

    Spec §5.3 guard: "no uncommitted, untracked, or stashed changes in the
    worktree". Sources of dirtiness:
      1. `git status --porcelain` on the worktree (tracked + untracked).
      2. `git stash list` entries whose recorded branch matches the worktree's
         current branch. Stash entries are repo-global but each row's message
         records "WIP on <branch>:" or "On <branch>:"; we attribute by branch.
         Stashes recorded on an UNRELATED branch are not the worktree's problem
         and are NOT flagged.
    """
    items: list[str] = []
    status = _git(root, "status", "--porcelain", check=False).stdout.splitlines()
    items.extend(line[3:] for line in status if line.strip())

    branch = git_current_branch(root)
    if branch:
        stash = _git(root, "stash", "list", check=False).stdout.splitlines()
        # Each line looks like: "stash@{0}: WIP on feat: 1234abcd msg"
        # or "stash@{0}: On feat: msg".
        marker_wip = f"WIP on {branch}:"
        marker_on = f"On {branch}:"
        for line in stash:
            if marker_wip in line or marker_on in line:
                items.append(f"stash: {line}")
    return (bool(items), items)


def branch_is_merged(root: Path, *, branch: str, into: str) -> bool:
    """True iff `branch` is reachable from `into` (a strict ancestor or equal)."""
    res = _git(root, "merge-base", "--is-ancestor", branch, into, check=False)
    return res.returncode == 0


def head_age_seconds(root: Path) -> float:
    """Seconds since the worktree HEAD commit's committer date."""
    out = _git(root, "log", "-1", "--format=%ct", "HEAD").stdout.strip()
    return max(0.0, time.time() - float(out))


def path_is_registered_worktree(root: Path, path: Path) -> bool:
    """True iff `path` (resolved) is in `git worktree list --porcelain` output."""
    target = path.resolve()
    for wt_path, _branch in worktree_roots(root):
        if wt_path == target:
            return True
    return False


def branch_exists(root: Path, branch: str) -> bool:
    res = _git(root, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False)
    return res.returncode == 0


def git_worktree_remove(root: Path, path: Path, *, force: bool = False) -> None:
    args = ["worktree", "remove"]
    if force:
        args.append("--force")
    args.append(str(path))
    _git(root, *args)


def git_branch_delete(root: Path, branch: str, *, force: bool = False) -> None:
    flag = "-D" if force else "-d"
    _git(root, "branch", flag, branch)


def git_worktree_add(root: Path, path: Path, branch: str) -> None:
    """Create a linked worktree at `path` checking out existing `branch`."""
    _git(root, "worktree", "add", str(path), branch)
