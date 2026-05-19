# P4 — Tasktool Coordination and Lifecycle Authority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make tasklist mutations safe under parallel worktrees and make active work visibly enter `in_progress` before slice close.

**Architecture:** Add a tasktool runtime layer that resolves whether a write should mutate locally or through an authoritative checkout, guarded by a lock in the shared git directory for every authoritative-mode write. Then add explicit lifecycle state (`started`) and `tasktool start`, with `set --status in_progress` as a compatibility alias and close-time enforcement for slices. Skills become instructions for the enforced command path, not the only enforcement mechanism.

**Tech Stack:** Python 3 stdlib (`tasktool`), Git CLI, JSON, markdown skills.

**TASKLIST entry:** `P4` in `docs/tasklist.json`; slices `P4.S1` and `P4.S2`.

---

## Scheduling Contract

`tasktool schedule P4` currently reports:

```text
P4.S1  [ready/ratified]  group=coordination  ready  deps=-  waiting_on=-  Authoritative tasklist mutations
P4.S2  [ready/ratified]  group=lifecycle  waiting  deps=P4.S1  waiting_on=P4.S1  Lifecycle status enforcement
```

Execute `P4.S1` first. Do not start `P4.S2` until `P4.S1` has passed its post-slice review and `tasktool close P4.S1` succeeds.

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `tools/tasktool/config.py` | Load/save `.tasktool/config.json`; define config dataclasses and validation. |
| Create | `tools/tasktool/worktree.py` | Git repository/worktree discovery, authoritative checkout validation, lock acquisition. |
| Modify | `tools/tasktool/commands.py` | Route mutating commands through a write context; add `cmd_config_init_authority`; later add `cmd_start` and lifecycle enforcement. |
| Modify | `tools/tasktool/cli.py` | Add `config init-authority`, `start`, and `close --allow-ready-close --reason`. |
| Modify | `tools/tasktool/model.py` | Add `started` fields to Phase/Slice/Task/CrossCutting in P4.S2. |
| Modify | `tools/tasktool/serialize.py` | Backward-compatible load/save for `started`. |
| Modify | `tools/tasktool/schema_gen.py` | Include `started` in generated schema. |
| Modify | `tools/tasktool/render.py` and `tools/tasktool/brief.py` | Surface `started` where useful. |
| Create | `tools/tasktool/tests/test_authority_config.py` | Config parsing and validation tests. |
| Create | `tools/tasktool/tests/test_worktree_authority.py` | Git worktree routing, unsafe-state, and locking tests. |
| Create | `tools/tasktool/tests/test_lifecycle_start.py` | `start`, `started`, and ready-close enforcement tests. |
| Modify | `skills/tasklist-discipline/SKILL.md` | Document authoritative routing and lifecycle commands. |
| Modify | `skills/using-git-worktrees/SKILL.md` | Explain routed tasktool writes from implementation worktrees. |
| Modify | `skills/subagent-driven-development/SKILL.md` | Require `tasktool start <slice-id>` before dispatch. |
| Modify | `skills/executing-plans/SKILL.md` | Replace prose-only in-progress step with `tasktool start`. |
| Modify | `skills/writing-plans/SKILL.md` | Plans must include a concrete `tasktool start` execution step. |

## P4.S1 — Authoritative Tasklist Mutations

### Task 1: Config Model and CLI Initializer

**Files:**
- Create: `tools/tasktool/config.py`
- Modify: `tools/tasktool/cli.py`
- Modify: `tools/tasktool/commands.py`
- Test: `tools/tasktool/tests/test_authority_config.py`

- [ ] **Step 1: Write failing config tests**

Create `tools/tasktool/tests/test_authority_config.py`:

```python
import json
from pathlib import Path

from tasktool.config import (
    DEFAULT_CONFIG_REL,
    TasktoolConfig,
    TasklistConfig,
    load_config,
    save_config,
)

def test_missing_config_defaults_to_local(tmp_path):
    cfg = load_config(tmp_path)
    assert cfg.tasklist.mutation_mode == "local"

def test_round_trip_authoritative_config(tmp_path):
    cfg = TasktoolConfig(
        tasklist=TasklistConfig(
            mutation_mode="authoritative-checkout",
            authoritative_branch="main",
        )
    )
    save_config(tmp_path, cfg)
    raw = json.loads((tmp_path / DEFAULT_CONFIG_REL).read_text())
    assert raw["schema_version"] == 1
    assert raw["tasklist"]["mutation_mode"] == "authoritative-checkout"
    assert "authoritative_root" not in raw["tasklist"]
    assert load_config(tmp_path) == cfg

def test_invalid_mode_raises(tmp_path):
    path = tmp_path / DEFAULT_CONFIG_REL
    path.parent.mkdir()
    path.write_text('{"schema_version":1,"tasklist":{"mutation_mode":"bad"}}')
    try:
        load_config(tmp_path)
    except ValueError as exc:
        assert "unknown mutation_mode" in str(exc)
    else:
        raise AssertionError("expected ValueError")
```

Run: `python -m pytest tools/tasktool/tests/test_authority_config.py -v`
Expected: FAIL because `tasktool.config` does not exist.

- [ ] **Step 2: Implement config module**

Create `tools/tasktool/config.py`:

```python
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG_REL = Path(".tasktool/config.json")
VALID_MUTATION_MODES = {"local", "authoritative-checkout"}

@dataclass(frozen=True)
class TasklistConfig:
    mutation_mode: str = "local"
    authoritative_branch: str = "main"

@dataclass(frozen=True)
class TasktoolConfig:
    schema_version: int = 1
    tasklist: TasklistConfig = field(default_factory=TasklistConfig)

def _parse_tasklist(raw: dict) -> TasklistConfig:
    mode = raw.get("mutation_mode", "local")
    if mode not in VALID_MUTATION_MODES:
        raise ValueError(f"unknown mutation_mode: {mode}")
    return TasklistConfig(
        mutation_mode=mode,
        authoritative_branch=raw.get("authoritative_branch", "main"),
    )

def load_config(repo_root: Path) -> TasktoolConfig:
    path = repo_root / DEFAULT_CONFIG_REL
    if not path.exists():
        return TasktoolConfig()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema_version", 1) != 1:
        raise ValueError(f"unsupported tasktool config schema_version: {raw.get('schema_version')}")
    return TasktoolConfig(
        schema_version=1,
        tasklist=_parse_tasklist(raw.get("tasklist", {})),
    )

def save_config(repo_root: Path, cfg: TasktoolConfig) -> None:
    path = repo_root / DEFAULT_CONFIG_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "schema_version": cfg.schema_version,
        "tasklist": {
            "mutation_mode": cfg.tasklist.mutation_mode,
            "authoritative_branch": cfg.tasklist.authoritative_branch,
        },
    }
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
```

Run: `python -m pytest tools/tasktool/tests/test_authority_config.py -v`
Expected: PASS.

- [ ] **Step 3: Add CLI initializer test**

Append to `tools/tasktool/tests/test_cli_integration.py`:

```python
def test_config_init_authority_writes_project_config(tmp_path):
    r = run_cli(
        "config", "init-authority",
        "--branch", "main",
        cwd=tmp_path,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads((tmp_path / ".tasktool" / "config.json").read_text())
    assert data["tasklist"]["mutation_mode"] == "authoritative-checkout"
    assert "authoritative_root" not in data["tasklist"]
    assert data["tasklist"]["authoritative_branch"] == "main"
```

Run: `python -m pytest tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_writes_project_config -v`
Expected: FAIL because the command does not exist.

- [ ] **Step 4: Add command and CLI plumbing**

In `tools/tasktool/commands.py`, import config helpers and add:

```python
from tasktool.config import TasktoolConfig, TasklistConfig, save_config

def cmd_config_init_authority(*, repo_root: Path, branch: str) -> None:
    cfg = TasktoolConfig(
        tasklist=TasklistConfig(
            mutation_mode="authoritative-checkout",
            authoritative_branch=branch,
        )
    )
    save_config(repo_root, cfg)
    _git_stage(repo_root, repo_root / ".tasktool" / "config.json")
```

In `tools/tasktool/cli.py`, add a `config` command group:

```python
p_config = sub.add_parser("config")
config_sub = p_config.add_subparsers(dest="config_cmd", required=True)
p_config_auth = config_sub.add_parser("init-authority")
p_config_auth.add_argument("--branch", default="main")
```

And dispatch:

```python
elif args.cmd == "config":
    if args.config_cmd == "init-authority":
        commands.cmd_config_init_authority(
            repo_root=root,
            branch=args.branch,
        )
```

Run:

```sh
python -m pytest tools/tasktool/tests/test_authority_config.py tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_writes_project_config -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```sh
git add tools/tasktool/config.py tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/tests/test_authority_config.py tools/tasktool/tests/test_cli_integration.py
git commit -m "tasktool: add authoritative checkout config"
```

### Task 2: Git Worktree Authority Detection

**Files:**
- Create: `tools/tasktool/worktree.py`
- Test: `tools/tasktool/tests/test_worktree_authority.py`

- [ ] **Step 1: Write failing worktree helper tests**

Create `tools/tasktool/tests/test_worktree_authority.py`:

```python
import os
import subprocess
from pathlib import Path

from tasktool.worktree import (
    AuthorityError,
    find_authoritative_root,
    git_common_dir,
    git_current_branch,
    same_repository,
    tasklist_has_unsafe_dirty_state,
    validate_authoritative_checkout,
)

def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True)

def _repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "tasktool-tests@example.invalid")
    _git(root, "config", "user.name", "Tasktool Tests")
    (root / "README.md").write_text("x\n")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "init")
    return root

def test_git_common_dir_is_shared_by_linked_worktree(tmp_path):
    root = _repo(tmp_path)
    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    assert git_common_dir(root) == git_common_dir(worker)

def test_validate_authoritative_checkout_rejects_wrong_branch(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-b", "other")
    try:
        validate_authoritative_checkout(root, expected_branch="main", caller_root=root)
    except AuthorityError as exc:
        assert "expected branch main" in str(exc)
    else:
        raise AssertionError("expected AuthorityError")

def test_same_repository_true_for_linked_worktree(tmp_path):
    root = _repo(tmp_path)
    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    assert same_repository(root, worker)

def test_find_authoritative_root_uses_branch_worktree(tmp_path):
    root = _repo(tmp_path)
    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    assert find_authoritative_root(worker, branch="main") == root

def test_find_authoritative_root_fails_closed_when_missing(tmp_path):
    root = _repo(tmp_path)
    _git(root, "checkout", "-b", "feature")
    try:
        find_authoritative_root(root, branch="main")
    except AuthorityError as exc:
        assert "TASKTOOL_AUTHORITY_ROOT" in str(exc)
    else:
        raise AssertionError("expected AuthorityError")
```

Run: `python -m pytest tools/tasktool/tests/test_worktree_authority.py -v`
Expected: FAIL because `tasktool.worktree` does not exist.

- [ ] **Step 2: Implement worktree helpers**

Create `tools/tasktool/worktree.py`:

```python
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

def tasklist_dirty(root: Path) -> bool:
    result = _git(root, "status", "--porcelain", "--", "docs/tasklist.json", check=False)
    return bool(result.stdout.strip())

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
```

Run: `python -m pytest tools/tasktool/tests/test_worktree_authority.py -v`
Expected: PASS.

- [ ] **Step 3: Add dirty tasklist validation test**

Append:

```python
def test_validate_authoritative_checkout_permits_dirty_tasklist_check_to_caller(tmp_path):
    root = _repo(tmp_path)
    (root / "docs").mkdir()
    (root / "docs" / "tasklist.json").write_text("{}\n")
    assert validate_authoritative_checkout(root, expected_branch="main", caller_root=root) is None
```

Staged-only tasklist changes are allowed, but unstaged tasklist bytes are unsafe. Add this test:

```python
def test_unsafe_tasklist_dirty_state_detects_unstaged_bytes(tmp_path):
    root = _repo(tmp_path)
    (root / "docs").mkdir()
    (root / "docs" / "tasklist.json").write_text("{}\n")
    _git(root, "add", "docs/tasklist.json")
    assert tasklist_has_unsafe_dirty_state(root) is False
    (root / "docs" / "tasklist.json").write_text('{"changed":true}\n')
    assert tasklist_has_unsafe_dirty_state(root) is True
```

- [ ] **Step 4: Commit**

```sh
git add tools/tasktool/worktree.py tools/tasktool/tests/test_worktree_authority.py
git commit -m "tasktool: add git worktree authority helpers"
```

### Task 3: Route Mutating Commands Through Authority

**Files:**
- Modify: `tools/tasktool/commands.py`
- Test: `tools/tasktool/tests/test_worktree_authority.py`
- Test: `tools/tasktool/tests/test_cli_integration.py`

- [ ] **Step 1: Write failing routing integration test**

Append to `tools/tasktool/tests/test_worktree_authority.py`:

```python
import json
import sys

TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"

def _tasktool(cwd, *args):
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
    )

def _seed_tasktool_repo(tmp_path):
    root = _repo(tmp_path)
    (root / "docs").mkdir()
    r = _tasktool(root, "init", "--project", "demo")
    assert r.returncode == 0, r.stdout + r.stderr
    r = _tasktool(root, "create", "phase", "--title", "P")
    assert r.returncode == 0, r.stdout + r.stderr
    r = _tasktool(root, "create", "slice", "P1", "--title", "S")
    assert r.returncode == 0, r.stdout + r.stderr
    _git(root, "add", ".")
    _git(root, "commit", "-m", "tasklist")
    return root

def test_worker_mutation_updates_authority_not_worker(tmp_path):
    root = _seed_tasktool_repo(tmp_path)
    r = _tasktool(root, "config", "init-authority", "--branch", "main")
    assert r.returncode == 0, r.stdout + r.stderr
    _git(root, "add", ".tasktool/config.json")
    _git(root, "commit", "-m", "configure tasktool authority")

    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    before_worker = (worker / "docs/tasklist.json").read_text()

    r = _tasktool(worker, "set", "P1.S1", "--status", "in_progress")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "authoritative checkout" in r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before_worker

    authority = json.loads((root / "docs/tasklist.json").read_text())
    assert authority["phases"][0]["slices"][0]["status"] == "in_progress"

def test_authoritative_checkout_write_uses_same_lock(tmp_path):
    root = _seed_tasktool_repo(tmp_path)
    r = _tasktool(root, "config", "init-authority", "--branch", "main")
    assert r.returncode == 0, r.stdout + r.stderr
    common = git_common_dir(root)
    (common / "tasktool.lock").write_text("held")
    r = subprocess.run(
        [sys.executable, str(TOOL), "set", "P1.S1", "--status", "in_progress"],
        cwd=root,
        text=True,
        capture_output=True,
        env={**os.environ, "TASKTOOL_LOCK_TIMEOUT": "0.1"},
    )
    assert r.returncode == 1
    assert "timed out waiting for tasktool lock" in r.stderr

def test_authoritative_unstaged_tasklist_refuses_before_mutation(tmp_path):
    root = _seed_tasktool_repo(tmp_path)
    r = _tasktool(root, "config", "init-authority", "--branch", "main")
    assert r.returncode == 0, r.stdout + r.stderr
    _git(root, "add", ".")
    _git(root, "commit", "-m", "authority")
    (root / "docs/tasklist.json").write_text('{"manual":"edit"}\n')
    r = _tasktool(root, "set", "P1.S1", "--status", "in_progress")
    assert r.returncode == 1
    assert "unstaged changes" in r.stderr
```

Run: `python -m pytest tools/tasktool/tests/test_worktree_authority.py::test_worker_mutation_updates_authority_not_worker -v`
Expected: FAIL because commands still mutate the current checkout.

- [ ] **Step 2: Add write root resolution**

In `tools/tasktool/commands.py`, add imports:

```python
import sys
from contextlib import contextmanager
from tasktool.config import load_config
from tasktool.worktree import (
    AuthorityError,
    find_authoritative_root,
    same_repository,
    tasklist_has_unsafe_dirty_state,
    tasktool_lock,
    validate_authoritative_checkout,
)
```

Add helper:

```python
def _resolve_write_root(repo_root: Path) -> tuple[Path, bool]:
    cfg = load_config(repo_root)
    if cfg.tasklist.mutation_mode == "local":
        return repo_root, False
    authoritative = find_authoritative_root(repo_root, branch=cfg.tasklist.authoritative_branch)
    try:
        validate_authoritative_checkout(
            authoritative,
            expected_branch=cfg.tasklist.authoritative_branch,
            caller_root=repo_root,
        )
    except AuthorityError as exc:
        raise CommandError(str(exc)) from exc
    return authoritative, repo_root.resolve() != authoritative

@contextmanager
def _write_context(repo_root: Path):
    write_root, routed = _resolve_write_root(repo_root)
    cfg = load_config(repo_root)
    if cfg.tasklist.mutation_mode == "authoritative-checkout":
        with tasktool_lock(repo_root):
            if tasklist_has_unsafe_dirty_state(write_root):
                raise CommandError(
                    "authoritative docs/tasklist.json has unstaged changes; "
                    "commit, stash, or normalise them before running tasktool"
                )
            if routed:
                print(f"tasktool: routed mutation to authoritative checkout: {write_root}", file=sys.stderr)
            yield write_root
    else:
        yield write_root
```

Then wrap every mutating command body with `_write_context`. Pattern:

```python
def cmd_set(...):
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        ...
        _save(write_root, p)
```

Apply this pattern to all mutating commands listed in the spec. Do not wrap read-only commands.

Run the failing routing test again.
Expected: PASS.

- [ ] **Step 3: Preserve invocation root for reviewer gates**

Refactor `_apply_review_gate` to accept both roots:

```python
def _apply_review_gate(
    invocation_root: Path,
    write_root: Path,
    p: Project,
    item,
    id: str,
    kind_label: str,
    reviewer_chain: Path | None,
    skip_review_gate: bool,
) -> None:
    ...
    if reviewer_chain is not None:
        resolved = (invocation_root / reviewer_chain).resolve() if not reviewer_chain.is_absolute() else reviewer_chain.resolve()
        try:
            resolved.relative_to(invocation_root.resolve())
        except ValueError as exc:
            raise CommandError(f"reviewer chain is outside repository: {reviewer_chain}") from exc
        reviewer_chain = resolved
    result = check_gate(invocation_root, id, gate_kind, explicit=reviewer_chain)
    rel = result.chain.relative_to(invocation_root).as_posix()
```

Call it from `cmd_set` and `cmd_close` with `invocation_root=repo_root` and `write_root=write_root`. This keeps gate discovery in the worker checkout while saving the repo-relative chain into the authoritative tasklist.

- [ ] **Step 4: Add reviewer-chain routing test**

Append:

```python
def test_worker_close_records_reviewer_chain_in_authority(tmp_path):
    root = _seed_tasktool_repo(tmp_path)
    _tasktool(root, "config", "init-authority", "--branch", "main")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "authority")
    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    chain = worker / "docs" / "reviewer" / "p1-s1-post-slice"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}')
    before_worker = (worker / "docs/tasklist.json").read_text()

    r = _tasktool(worker, "close", "P1.S1", "--reviewer-chain", str(chain))
    assert r.returncode == 0, r.stdout + r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before_worker
    authority = json.loads((root / "docs/tasklist.json").read_text())
    assert authority["phases"][0]["slices"][0]["status"] == "done"
    assert authority["phases"][0]["slices"][0]["reviewer_chain"] == "docs/reviewer/p1-s1-post-slice"

def test_worker_set_done_records_reviewer_chain_in_authority(tmp_path):
    root = _seed_tasktool_repo(tmp_path)
    _tasktool(root, "config", "init-authority", "--branch", "main")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "authority")
    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    chain = worker / "docs" / "reviewer" / "p1-s1-post-slice"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}')

    r = _tasktool(worker, "set", "P1.S1", "--status", "done", "--reviewer-chain", str(chain))
    assert r.returncode == 0, r.stdout + r.stderr
    authority = json.loads((root / "docs/tasklist.json").read_text())
    assert authority["phases"][0]["slices"][0]["reviewer_chain"] == "docs/reviewer/p1-s1-post-slice"

def test_reviewer_chain_outside_invocation_repo_is_rejected(tmp_path):
    root = _seed_tasktool_repo(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    r = _tasktool(root, "set", "P1.S1", "--status", "done", "--reviewer-chain", str(outside))
    assert r.returncode == 1
    assert "outside repository" in r.stderr
```

Run: `python -m pytest tools/tasktool/tests/test_worktree_authority.py::test_worker_close_records_reviewer_chain_in_authority -v`
Expected: PASS.

- [ ] **Step 5: Add mutating command routing matrix**

Append:

```python
def _authority_with_worker(tmp_path):
    root = _seed_tasktool_repo(tmp_path)
    r = _tasktool(root, "config", "init-authority", "--branch", "main")
    assert r.returncode == 0, r.stdout + r.stderr
    _git(root, "add", ".")
    _git(root, "commit", "-m", "authority")
    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    return root, worker

def assert_worker_tasklist_unchanged(root, worker, *args):
    before = (worker / "docs/tasklist.json").read_text()
    r = _tasktool(worker, *args)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before
    assert "authoritative checkout" in r.stderr
    return json.loads((root / "docs/tasklist.json").read_text())

def test_routed_create_note_ref_title_block_unblock_deps_ratify_and_planning_path(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    data = assert_worker_tasklist_unchanged(root, worker, "create", "phase", "--title", "Second phase")
    assert data["phases"][1]["title"] == "Second phase"
    data = assert_worker_tasklist_unchanged(root, worker, "create", "cross", "--title", "Cross item")
    assert data["cross_cutting"][0]["title"] == "Cross item"
    data = assert_worker_tasklist_unchanged(root, worker, "create", "task", "P1.S1", "--title", "New task")
    assert data["phases"][0]["slices"][0]["tasks"][0]["title"] == "New task"
    data = assert_worker_tasklist_unchanged(root, worker, "note", "P1.S1", "--append", "worker note")
    assert "worker note" in data["phases"][0]["slices"][0]["notes"]
    data = assert_worker_tasklist_unchanged(root, worker, "ref", "P1.S1", "--add", "docs/example.md")
    assert "docs/example.md" in data["phases"][0]["slices"][0]["refs"]
    data = assert_worker_tasklist_unchanged(root, worker, "title", "P1.S1", "--set", "Retitled")
    assert data["phases"][0]["slices"][0]["title"] == "Retitled"
    data = assert_worker_tasklist_unchanged(root, worker, "block", "P1.S1", "--on", "external:waiting")
    assert data["phases"][0]["slices"][0]["status"] == "blocked"
    data = assert_worker_tasklist_unchanged(root, worker, "unblock", "P1.S1", "--resume")
    assert data["phases"][0]["slices"][0]["status"] == "in_progress"
    assert_worker_tasklist_unchanged(root, worker, "create", "slice", "P1", "--title", "Second")
    data = assert_worker_tasklist_unchanged(root, worker, "deps", "P1.S2", "--add", "P1.S1")
    assert data["phases"][0]["slices"][1]["depends_on"] == ["P1.S1"]
    data = assert_worker_tasklist_unchanged(root, worker, "ratify", "P1.S2", "--parallel-group", "followup")
    assert data["phases"][0]["slices"][1]["parallel_group"] == "followup"
    data = assert_worker_tasklist_unchanged(root, worker, "planning-path", "P1", "--set", "docs/specs/p1.md")
    assert data["phases"][0]["planning_path"] == "docs/specs/p1.md"

def test_routed_validate_normalise_updates_authority_only(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    raw = json.loads((root / "docs/tasklist.json").read_text())
    (worker / "docs/tasklist.json").write_text(json.dumps(raw, separators=(",", ":")))
    before = (worker / "docs/tasklist.json").read_text()
    r = _tasktool(worker, "validate", "--normalise")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before
    assert (root / "docs/tasklist.json").read_text().endswith("\n")

def test_routed_init_force_updates_authority_only(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    before = (worker / "docs/tasklist.json").read_text()
    r = _tasktool(worker, "init", "--project", "replacement", "--force")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before
    data = json.loads((root / "docs/tasklist.json").read_text())
    assert data["project"] == "replacement"

def test_routed_import_writes_authority_only(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    sample = worker / "TASKLIST_sample.md"
    sample.write_text("# Demo\n\n- [ ] P1 — Imported phase\n")
    before = (worker / "docs/tasklist.json").read_text()
    r = _tasktool(worker, "import", str(sample), "--force")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before
    assert "Imported phase" in (root / "docs/tasklist.json").read_text()

def test_routed_archive_phase_writes_authority_archive_artifact(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    assert_worker_tasklist_unchanged(
        root, worker,
        "close", "P1.S1",
        "--skip-review-gate",
    )
    chain = worker / "docs" / "reviewer" / "p1-post-phase"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}')
    before = (worker / "docs/tasklist.json").read_text()
    r = _tasktool(worker, "archive-phase", "P1", "--reviewer-chain", str(chain))
    assert r.returncode == 0, r.stdout + r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before
    assert list((root / "docs" / "archived-tasks").glob("P1-*.md"))
```

These tests intentionally include commands with extra side effects. `archive-phase` must create and stage its archive markdown in the authoritative checkout, not the worker checkout.

- [ ] **Step 6: Full tasktool tests**

Run:

```sh
python -m pytest tools/tasktool/tests -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```sh
git add tools/tasktool/commands.py tools/tasktool/tests/test_worktree_authority.py
git commit -m "tasktool: route mutations to authoritative checkout"
```

### P4.S1 Closeout

- [ ] **Step 1: Validate**

Run:

```sh
tasktool validate --strict-format
python -m pytest tools/tasktool/tests -v
```

Expected: both pass.

- [ ] **Step 2: External review**

Run:

```sh
python3 skills/external-review/scripts/external-reviewer.py review \
  --kind post-slice \
  --file docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md \
  --work-id P4.S1 \
  --context docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md \
  --context docs/tasklist.json \
  --emit json
```

If verdict is `revise`, dispatch fixes and re-submit per `superstar:subagent-driven-development`.

- [ ] **Step 3: Close slice**

```sh
tasktool close P4.S1 --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-P4-S1-post-slice
```

## P4.S2 — Lifecycle Status Enforcement

### Task 4: Add `started` Field

**Files:**
- Modify: `tools/tasktool/model.py`
- Modify: `tools/tasktool/serialize.py`
- Modify: `tools/tasktool/schema_gen.py`
- Modify: `tools/tasktool/render.py`
- Modify: `tools/tasktool/brief.py`
- Test: `tools/tasktool/tests/test_serialize.py`
- Test: `tools/tasktool/tests/test_validate.py`

- [ ] **Step 1: Write failing serialization test**

Append to `tools/tasktool/tests/test_serialize.py`:

```python
def test_started_field_round_trips_on_slice():
    text = """{
      "project": "demo",
      "schema_version": 1,
      "phases": [{
        "id": "P1",
        "title": "Phase",
        "created": "2026-05-19",
        "slices": [{
          "id": "S1",
          "title": "Slice",
          "created": "2026-05-19",
          "started": "2026-05-19"
        }]
      }]
    }"""
    p = loads_project(text)
    assert p.phases[0].slices[0].started == "2026-05-19"
    assert '"started": "2026-05-19"' in dumps_canonical(p)
```

Run: `python -m pytest tools/tasktool/tests/test_serialize.py::test_started_field_round_trips_on_slice -v`
Expected: FAIL because `Slice.started` does not exist.

- [ ] **Step 2: Add model and serializer support**

In `tools/tasktool/model.py`, add `started: str | None = None` to `Task`, `Slice`, `Phase`, and `CrossCutting` after `created`.

In `tools/tasktool/serialize.py`, load `started=...` for each item type. Existing files should default to `None`.

Run:

```sh
python -m pytest tools/tasktool/tests/test_serialize.py::test_started_field_round_trips_on_slice -v
python -m pytest tools/tasktool/tests/test_model.py tools/tasktool/tests/test_validate.py -v
```

Expected: PASS.

- [ ] **Step 3: Update render and brief display**

Add `started` to `cmd_show` output near `closed`, and to rendered markdown when non-null. Keep empty `started` out of the rendered view.

Run:

```sh
python -m pytest tools/tasktool/tests/test_render.py tools/tasktool/tests/test_brief.py -v
```

Expected: PASS after updating expected snippets if needed.

- [ ] **Step 4: Commit**

```sh
git add tools/tasktool/model.py tools/tasktool/serialize.py tools/tasktool/schema_gen.py tools/tasktool/render.py tools/tasktool/brief.py tools/tasktool/tests
git commit -m "tasktool: add started lifecycle field"
```

### Task 5: Add `tasktool start`

**Files:**
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/cli.py`
- Test: `tools/tasktool/tests/test_lifecycle_start.py`

- [ ] **Step 1: Write failing start tests**

Create `tools/tasktool/tests/test_lifecycle_start.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"

def run(root, *args):
    return subprocess.run(
        [sys.executable, str(TOOL), "--project-root", str(root), *args],
        text=True,
        capture_output=True,
    )

def seed(root):
    (root / "docs").mkdir()
    assert run(root, "init", "--project", "demo").returncode == 0
    assert run(root, "create", "phase", "--title", "Phase").returncode == 0
    assert run(root, "create", "slice", "P1", "--title", "Slice").returncode == 0
    assert run(root, "create", "task", "P1.S1", "--title", "Task").returncode == 0

def tasklist(root):
    return json.loads((root / "docs" / "tasklist.json").read_text())

def test_start_slice_sets_in_progress_and_started(tmp_path):
    seed(tmp_path)
    r = run(tmp_path, "start", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "in_progress"
    assert sl["started"]

def test_set_in_progress_sets_started(tmp_path):
    seed(tmp_path)
    r = run(tmp_path, "set", "P1.S1", "--status", "in_progress")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "in_progress"
    assert sl["started"]

def test_start_done_item_refuses(tmp_path):
    seed(tmp_path)
    chain = tmp_path / "docs" / "reviewer" / "p1-s1-post-slice"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}')
    assert run(tmp_path, "start", "P1.S1").returncode == 0
    assert run(tmp_path, "close", "P1.S1", "--reviewer-chain", str(chain)).returncode == 0
    r = run(tmp_path, "start", "P1.S1")
    assert r.returncode == 1
    assert "already done" in r.stderr
```

Run: `python -m pytest tools/tasktool/tests/test_lifecycle_start.py -v`
Expected: FAIL because `start` does not exist.

- [ ] **Step 2: Implement command**

In `tools/tasktool/commands.py`, add:

```python
def cmd_start(*, repo_root: Path, id: str, resume: bool = False) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        kind = parse_id(qid)[0]
        _start_item(qid, item, resume=resume)
        _save(write_root, p)
        _notify_status(qid=qid, kind=kind, status=item.status, title=item.title)

def _start_item(qid: str, item, *, resume: bool = False) -> None:
        if item.status == Status.DONE:
            raise CommandError(f"{qid} is already done")
        if item.status == Status.BLOCKED:
            if not resume:
                raise CommandError(f"{qid} is blocked; use start --resume to clear blocked_on")
            item.blocked_on = None
        item.status = Status.IN_PROGRESS
        if getattr(item, "started", None) is None:
            item.started = _today()
```

In `cmd_set`, when `new_status == Status.IN_PROGRESS`, call `_start_item(qid, item)` instead of directly assigning `item.status`. This makes `set --status in_progress` a compatibility alias for `start` and preserves existing CLI muscle memory.

In `tools/tasktool/cli.py`, add:

```python
p_start = sub.add_parser("start")
p_start.add_argument("id")
p_start.add_argument("--resume", action="store_true")
```

Dispatch:

```python
elif args.cmd == "start":
    commands.cmd_start(repo_root=root, id=args.id, resume=args.resume)
```

Run: `python -m pytest tools/tasktool/tests/test_lifecycle_start.py -v`
Expected: PASS.

- [ ] **Step 3: Add routed start test**

Append to `tools/tasktool/tests/test_worktree_authority.py`:

```python
def test_worker_start_routes_to_authority(tmp_path):
    root = _seed_tasktool_repo(tmp_path)
    _tasktool(root, "config", "init-authority", "--branch", "main")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "authority")
    worker = tmp_path / "worker"
    _git(root, "worktree", "add", "-b", "worker", str(worker))
    before_worker = (worker / "docs/tasklist.json").read_text()
    r = _tasktool(worker, "start", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before_worker
    data = json.loads((root / "docs/tasklist.json").read_text())
    assert data["phases"][0]["slices"][0]["status"] == "in_progress"
    assert data["phases"][0]["slices"][0]["started"]
```

Run: `python -m pytest tools/tasktool/tests/test_worktree_authority.py::test_worker_start_routes_to_authority -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```sh
git add tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/tests/test_lifecycle_start.py tools/tasktool/tests/test_worktree_authority.py
git commit -m "tasktool: add start command"
```

### Task 6: Enforce Slice Start Before Close

**Files:**
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/cli.py`
- Test: `tools/tasktool/tests/test_lifecycle_start.py`

- [ ] **Step 0: Start P4.S2 with the newly added command**

After Task 5 has committed `tasktool start`, run:

```sh
tasktool start P4.S2
```

Expected: `tasktool show P4.S2` reports `status: in_progress` and a `started:` date. This prevents P4.S2's own closeout from tripping the new ready-close guard after Task 6 lands.

- [ ] **Step 1: Write failing ready-close tests**

Append:

```python
def test_close_ready_slice_refuses_without_override(tmp_path):
    seed(tmp_path)
    chain = tmp_path / "docs" / "reviewer" / "p1-s1-post-slice"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}')
    r = run(tmp_path, "close", "P1.S1", "--reviewer-chain", str(chain))
    assert r.returncode == 1
    assert "must be started before close" in r.stderr

def test_close_ready_slice_override_records_note(tmp_path):
    seed(tmp_path)
    chain = tmp_path / "docs" / "reviewer" / "p1-s1-post-slice"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}')
    r = run(
        tmp_path,
        "close", "P1.S1",
        "--reviewer-chain", str(chain),
        "--allow-ready-close",
        "--reason", "legacy slice closed before start existed",
    )
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "done"
    assert "ready-close override" in sl["notes"]
```

Run: `python -m pytest tools/tasktool/tests/test_lifecycle_start.py::test_close_ready_slice_refuses_without_override -v`
Expected: FAIL because close still allows ready slices.

- [ ] **Step 2: Implement enforcement**

In `cmd_close`, add parameters:

```python
allow_ready_close: bool = False,
reason: str | None = None,
```

Before setting `item.status = Status.DONE`, add:

```python
if kind == "slice" and getattr(item, "started", None) is None:
    if not allow_ready_close:
        raise CommandError(f"{qid} must be started before close; run `tasktool start {qid}` first")
    ts = _dt.datetime.now().isoformat(timespec="seconds")
    audit = f"[{ts}] ready-close override for {qid}: {reason or 'no reason supplied'}"
    item.notes = (item.notes + "\n" + audit).strip() if item.notes else audit
```

In `tools/tasktool/cli.py`, add to close parser:

```python
p_close.add_argument("--allow-ready-close", action="store_true")
p_close.add_argument("--reason")
```

Pass both to `cmd_close`.

Run:

```sh
python -m pytest tools/tasktool/tests/test_lifecycle_start.py -v
python -m pytest tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_cli_integration.py -v
```

Expected: update existing close tests to call `cmd_start` before slice close or pass `allow_ready_close=True` where they model legacy closure.

- [ ] **Step 3: Commit**

```sh
git add tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/tests
git commit -m "tasktool: require slice start before close"
```

### Task 7: Skill Documentation Updates

**Files:**
- Modify: `skills/tasklist-discipline/SKILL.md`
- Modify: `skills/using-git-worktrees/SKILL.md`
- Modify: `skills/subagent-driven-development/SKILL.md`
- Modify: `skills/executing-plans/SKILL.md`
- Modify: `skills/writing-plans/SKILL.md`

- [ ] **Step 1: Add skill-content regression tests**

Create `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

def read(path):
    return (ROOT / path).read_text()

def test_subagent_skill_requires_tasktool_start():
    text = read("skills/subagent-driven-development/SKILL.md")
    assert "tasktool start <slice-id>" in text
    assert "before dispatching implementation" in text

def test_executing_plans_skill_uses_tasktool_start():
    text = read("skills/executing-plans/SKILL.md")
    assert "tasktool start <slice-id>" in text

def test_tasklist_discipline_documents_authoritative_checkout():
    text = read("skills/tasklist-discipline/SKILL.md")
    assert "authoritative checkout" in text
    assert "tasktool start" in text
```

Run: `python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -v`
Expected: FAIL until docs are updated.

- [ ] **Step 2: Update `tasklist-discipline`**

Add a section after the implementation isolation boundary:

```markdown
## Authoritative Checkout Routing

When `.tasktool/config.json` sets `mutation_mode` to `authoritative-checkout`, mutating tasktool commands may be run from an implementation worktree, but the write lands in the configured authoritative checkout under a lock. The worktree's `docs/tasklist.json` is a read-only mirror for implementation purposes.

Use `tasktool config init-authority --branch main` from the project root to opt in. At runtime, tasktool discovers the checkout for that branch through `git worktree list --porcelain`; if discovery is ambiguous, set `TASKTOOL_AUTHORITY_ROOT=/absolute/path/to/main` for the invocation.
```

Add `tasktool start <id>` to Daily commands and explain that active slice execution starts with it.

- [ ] **Step 3: Update execution skills**

In `skills/subagent-driven-development/SKILL.md`, after ready-slice selection and before dispatch:

```markdown
Before dispatching implementation for a slice, run `tasktool start <slice-id>`. If authoritative checkout routing is configured, this command may be invoked from the slice worktree; tasktool will route the mutation to the authoritative checkout.
```

In the process graph, insert `tasktool start <slice-id>` before implementer dispatch.

In `skills/executing-plans/SKILL.md`, replace "Mark as in_progress" with:

```markdown
1. Run `tasktool start <slice-id>` before editing implementation files.
```

In `skills/writing-plans/SKILL.md`, require generated slice plans to include `tasktool start <slice-id>` as the first execution step when the project has `docs/tasklist.json`.

- [ ] **Step 4: Run docs regression test**

Run:

```sh
python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```sh
git add skills/tasklist-discipline/SKILL.md skills/using-git-worktrees/SKILL.md skills/subagent-driven-development/SKILL.md skills/executing-plans/SKILL.md skills/writing-plans/SKILL.md tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
git commit -m "skills: require routed tasktool start workflow"
```

### P4.S2 Closeout

- [ ] **Step 1: Validate**

Run:

```sh
tasktool validate --strict-format
python -m pytest tools/tasktool/tests -v
```

Expected: PASS.

- [ ] **Step 2: External review**

Run:

```sh
python3 skills/external-review/scripts/external-reviewer.py review \
  --kind post-slice \
  --file docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md \
  --work-id P4.S2 \
  --context docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md \
  --context docs/tasklist.json \
  --emit json
```

Iterate until verdict is `ready` or `ready with small edits`.

- [ ] **Step 3: Close slice and phase**

```sh
tasktool close P4.S2 --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-P4-S2-post-slice
```

Then run post-phase review and archive:

```sh
python3 skills/external-review/scripts/external-reviewer.py review \
  --kind post-phase \
  --file docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md \
  --work-id P4 \
  --context docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md \
  --context docs/tasklist.json \
  --emit json

tasktool archive-phase P4 --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase
```

## Final Verification

Run:

```sh
tasktool validate --strict-format
python -m pytest tools/tasktool/tests -v
git status --short
```

Expected:

- tasktool validation passes;
- tasktool tests pass;
- only intentional P4 files and review artifacts are dirty before final commit;
- no implementation worktree branch contains a `docs/tasklist.json` delta caused by tasktool mutations.
