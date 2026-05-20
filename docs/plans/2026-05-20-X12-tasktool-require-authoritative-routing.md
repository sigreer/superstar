# X12 — tasktool: require authoritative-checkout routing for mutations — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make authoritative-checkout routing structurally required for mutating tasktool commands so the AGS sidebar widget, TTS announcements, and on-disk source-of-truth cannot diverge silently; add a `migrate-from-local` subcommand for reconciling drift, and an `init-local` subcommand for the explicit opt-out.

**Architecture:** Three production-code changes in `tools/tasktool/`: (1) `config.py` gains a `MutationModeUnconfigured` sentinel so `load_config` distinguishes "no config file" from "config says local"; (2) `commands.py:_resolve_write_root` raises `CommandError` on the mutation path when unconfigured, and gains `cmd_config_init_local` + `cmd_config_migrate_from_local`; (3) `cli.py` registers two new `config` subcommands. The migrator walks `dataclasses.fields()` on every row type in `tools/tasktool/model.py` so adding fields to the model cannot silently drop them from migration. Three skills under `skills/` are tightened from conditional to required wording.

**Tech Stack:** Python 3.11 (slots dataclasses, `dataclasses.fields()` introspection), pytest, existing `tasktool_lock` and `validate_authoritative_checkout` helpers in `tools/tasktool/worktree.py`.

**Spec:** `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md`

**Tasktool row:** X12 (cross-cutting). Confirmed via `tasktool show X12` (status=ready, refs spec).

---

## Lifecycle start

- [ ] **Step 0: Mark X12 in progress**

```bash
./tools/tasktool/tasktool start X12
```

Expected: exit 0; `tasktool show X12` reports `status: in_progress` with a `started:` date.

---

## File structure

Files created in this slice:
- `tools/tasktool/migrate.py` — pure-Python diff/merge over the model dataclass tree. New module so `commands.py` stays focused on CLI command bodies and the migrator's row-walking logic has its own home.
- `tools/tasktool/tests/test_migrate.py` — unit tests for the migrator (diff, dataclass coverage, conflict handling).
- `tools/tasktool/tests/test_unconfigured_mutation.py` — tests for the hard-error behaviour.
- `tools/tasktool/tests/test_init_local.py` — tests for the `init-local` CLI subcommand.
- `tools/tasktool/tests/test_migrate_cli.py` — CLI integration tests for `config migrate-from-local`.

Files modified in this slice:
- `tools/tasktool/config.py` — new sentinel and `is_authoritative_required` predicate; `load_config` returns sentinel when no file.
- `tools/tasktool/commands.py` — `_resolve_write_root` hard-error path; new `cmd_config_init_local` and `cmd_config_migrate_from_local`.
- `tools/tasktool/cli.py` — register `config init-local` and `config migrate-from-local` subparsers.
- `tools/tasktool/tests/test_authority_config.py` — replace `test_missing_config_defaults_to_local` (no longer true) with `test_missing_config_returns_unconfigured`.
- `tools/tasktool/tests/test_cli_integration.py` — any existing tests that relied on the implicit-`local` default get an explicit `init-local` or `init-authority` setup line.
- `skills/project-setup/SKILL.md` — order change + setup-precondition for missing authority config.
- `skills/tasklist-discipline/SKILL.md` — promote routing from optional to required; add remediation pointer.
- `skills/using-git-worktrees/SKILL.md` — remove "if configured" conditional.

---

## Task 1: Distinguish "unconfigured" from "explicit local" in config.py

**Files:**
- Modify: `tools/tasktool/config.py`
- Modify: `tools/tasktool/tests/test_authority_config.py`

- [ ] **Step 1: Add the failing test for the sentinel**

Edit `tools/tasktool/tests/test_authority_config.py`. Replace the existing `test_missing_config_defaults_to_local` function with:

```python
def test_missing_config_returns_unconfigured(tmp_path):
    cfg = load_config(tmp_path)
    assert cfg.tasklist.mutation_mode == "unconfigured"
    assert is_authoritative_required(cfg) is True


def test_explicit_local_is_configured(tmp_path):
    (tmp_path / ".tasktool").mkdir()
    (tmp_path / ".tasktool" / "config.json").write_text(
        '{"schema_version":1,"tasklist":{"mutation_mode":"local","authoritative_branch":"main"}}'
    )
    cfg = load_config(tmp_path)
    assert cfg.tasklist.mutation_mode == "local"
    assert is_authoritative_required(cfg) is False


def test_authoritative_mode_does_not_require_init(tmp_path):
    (tmp_path / ".tasktool").mkdir()
    (tmp_path / ".tasktool" / "config.json").write_text(
        '{"schema_version":1,"tasklist":{"mutation_mode":"authoritative-checkout","authoritative_branch":"main"}}'
    )
    cfg = load_config(tmp_path)
    assert is_authoritative_required(cfg) is False


def test_config_with_omitted_mutation_mode_is_unconfigured(tmp_path):
    """A config file present but lacking mutation_mode must NOT silently
    default to local. It is treated identically to a missing file."""
    (tmp_path / ".tasktool").mkdir()
    (tmp_path / ".tasktool" / "config.json").write_text(
        '{"schema_version":1,"tasklist":{}}'
    )
    cfg = load_config(tmp_path)
    assert cfg.tasklist.mutation_mode == "unconfigured"
    assert is_authoritative_required(cfg) is True
```

Add `is_authoritative_required` to the import line:

```python
from tasktool.config import (
    DEFAULT_CONFIG_REL,
    TasklistConfig,
    TasktoolConfig,
    is_authoritative_required,
    load_config,
    save_config,
)
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_authority_config.py -v
```

Expected: ImportError or `mutation_mode == "local"` assertion failure (the sentinel and predicate don't exist yet).

- [ ] **Step 3: Add the sentinel + predicate to config.py**

Edit `tools/tasktool/config.py`. Replace the existing module body with:

```python
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG_REL = Path(".tasktool/config.json")

# Sentinel returned when no .tasktool/config.json exists. Distinguishes
# "operator never configured this repo" from "operator explicitly chose local".
UNCONFIGURED = "unconfigured"

VALID_MUTATION_MODES = {"local", "authoritative-checkout"}


@dataclass(frozen=True)
class TasklistConfig:
    mutation_mode: str = UNCONFIGURED
    authoritative_branch: str = "main"


@dataclass(frozen=True)
class TasktoolConfig:
    schema_version: int = 1
    tasklist: TasklistConfig = field(default_factory=TasklistConfig)


def _parse_tasklist(raw: dict) -> TasklistConfig:
    if "mutation_mode" not in raw:
        # Config file exists but omits mutation_mode — treat as unconfigured,
        # the same way a missing config file is treated. Operators must opt in.
        return TasklistConfig(
            mutation_mode=UNCONFIGURED,
            authoritative_branch=raw.get("authoritative_branch", "main"),
        )
    mode = raw["mutation_mode"]
    if mode not in VALID_MUTATION_MODES:
        raise ValueError(f"unknown mutation_mode: {mode}")
    return TasklistConfig(
        mutation_mode=mode,
        authoritative_branch=raw.get("authoritative_branch", "main"),
    )


def load_config(repo_root: Path) -> TasktoolConfig:
    path = repo_root / DEFAULT_CONFIG_REL
    if not path.exists():
        return TasktoolConfig()  # default field gives UNCONFIGURED
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


def is_authoritative_required(cfg: TasktoolConfig) -> bool:
    """True iff mutations should be refused for this config."""
    return cfg.tasklist.mutation_mode == UNCONFIGURED
```

- [ ] **Step 4: Run tests, expect pass**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_authority_config.py -v
```

Expected: 4 passed (the three new tests plus the existing `test_round_trip_authoritative_config` and `test_invalid_mode_raises`, minus the deleted `test_missing_config_defaults_to_local`).

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/config.py tools/tasktool/tests/test_authority_config.py
git commit -m "X12: distinguish unconfigured tasktool config from explicit local mode"
```

---

## Task 2: Hard-error mutations when unconfigured

**Files:**
- Modify: `tools/tasktool/commands.py`
- Create: `tools/tasktool/tests/test_unconfigured_mutation.py`

- [ ] **Step 1: Write the failing test**

Create `tools/tasktool/tests/test_unconfigured_mutation.py`:

```python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_DIR = REPO_ROOT / "tools"


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "tasktool", *args],
        capture_output=True, text=True, cwd=cwd, env=env,
    )


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "--allow-empty", "-m", "init"],
                   cwd=path, check=True, capture_output=True)


def test_init_errors_without_authority_config(tmp_path):
    _git_init(tmp_path)
    r = run_cli("init", "--project", "demo", cwd=tmp_path)
    assert r.returncode != 0
    assert "no authoritative-checkout routing configured" in r.stderr
    assert "tasktool config init-authority" in r.stderr
    assert not (tmp_path / "docs" / "tasklist.json").exists()


def test_start_errors_without_authority_config(tmp_path):
    _git_init(tmp_path)
    # Create a tasklist by writing the file directly so `start` has a row to operate on.
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "tasklist.json").write_text(
        '{"schema_version":1,"project":"demo","phases":[],'
        '"cross_cutting":[{"id":"X1","title":"t","created":"2026-05-20","status":"ready",'
        '"refs":[],"notes":"","started":null,"closed":null}],"archived_phases":[]}'
    )
    r = run_cli("start", "X1", cwd=tmp_path)
    assert r.returncode != 0
    assert "no authoritative-checkout routing configured" in r.stderr


def test_validate_without_normalise_works_unconfigured(tmp_path):
    _git_init(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "tasklist.json").write_text(
        '{"schema_version":1,"project":"demo","phases":[],'
        '"cross_cutting":[],"archived_phases":[]}'
    )
    r = run_cli("validate", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


def test_validate_normalise_errors_unconfigured(tmp_path):
    _git_init(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "tasklist.json").write_text(
        '{"schema_version":1,"project":"demo","phases":[],'
        '"cross_cutting":[],"archived_phases":[]}'
    )
    r = run_cli("validate", "--normalise", cwd=tmp_path)
    assert r.returncode != 0
    assert "no authoritative-checkout routing configured" in r.stderr


def test_render_works_unconfigured(tmp_path):
    _git_init(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "tasklist.json").write_text(
        '{"schema_version":1,"project":"demo","phases":[],'
        '"cross_cutting":[],"archived_phases":[]}'
    )
    r = run_cli("render", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.parametrize("readonly_cmd", [
    ("brief",),
    ("schema",),
    ("list",),
    ("ready-slices", "P1"),
])
def test_other_readonly_commands_work_unconfigured(tmp_path, readonly_cmd):
    """Spec test #5: read-only commands beyond render/validate succeed without config."""
    _git_init(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "tasklist.json").write_text(
        '{"schema_version":1,"project":"demo",'
        '"phases":[{"id":"P1","title":"p","created":"2026-05-20","status":"ready",'
        '"started":null,"closed":null,"spec_path":null,"plan_path":null,'
        '"planning_path":null,"phase_reviewer_chain":null,"notes":"","slices":[]}],'
        '"cross_cutting":[],"archived_phases":[]}'
    )
    r = run_cli(*readonly_cmd, cwd=tmp_path)
    # Some of these may exit non-zero for unrelated reasons (e.g. ready-slices
    # with no ready slices); the assertion is just that they do NOT error with
    # the unconfigured-routing message.
    assert "no authoritative-checkout routing configured" not in r.stderr, r.stderr


def test_explicit_local_mode_still_mutates(tmp_path):
    _git_init(tmp_path)
    r = run_cli("config", "init-local", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    r = run_cli("init", "--project", "demo", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / "docs" / "tasklist.json").exists()


def test_bootstrap_init_authority_then_init_succeeds(tmp_path):
    """Spec test #6: greenfield positive — init-authority first, then init succeeds."""
    _git_init(tmp_path)
    r = run_cli("config", "init-authority", "--branch", "main", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    r = run_cli("init", "--project", "demo", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / "docs" / "tasklist.json").exists()


def test_bootstrap_init_before_init_authority_fails(tmp_path):
    """Spec test #7: explicit negative — bare `init` without prior authority config errors."""
    _git_init(tmp_path)
    r = run_cli("init", "--project", "demo", cwd=tmp_path)
    assert r.returncode != 0
    assert "no authoritative-checkout routing configured" in r.stderr
    assert not (tmp_path / "docs" / "tasklist.json").exists()
```

(The `init-local` part of `test_explicit_local_mode_still_mutates` is forward-referenced; it will pass after Task 3.)

- [ ] **Step 2: Run the test, expect mutation tests to fail with the hard-error message NOT present**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_unconfigured_mutation.py -v
```

Expected: `test_init_errors_without_authority_config`, `test_start_errors_without_authority_config`, `test_validate_normalise_errors_unconfigured` fail (mutations currently succeed). Read-only tests pass. `test_explicit_local_mode_still_mutates` fails on the `config init-local` line (subcommand doesn't exist yet).

- [ ] **Step 3: Add the hard-error path in `_resolve_write_root`**

In `tools/tasktool/commands.py`, update the imports near the top of the file to add `is_authoritative_required`:

```python
from tasktool.config import (
    TasklistConfig,
    TasktoolConfig,
    is_authoritative_required,
    load_config,
    save_config,
)
```

Replace `_resolve_write_root` (currently at `tools/tasktool/commands.py:80-98`) with:

```python
UNCONFIGURED_HINT = (
    "tasktool: this repository has no authoritative-checkout routing configured. "
    "Run `tasktool config init-authority --branch <branch>` from the authoritative "
    "checkout to enable safe routing. Existing local-mode tasklists can be reconciled "
    "with `tasktool config migrate-from-local`. To opt out explicitly, run "
    "`tasktool config init-local`."
)


def _resolve_write_root(repo_root: Path) -> tuple[Path, bool, str, str]:
    cfg = load_config(repo_root)
    if is_authoritative_required(cfg):
        raise CommandError(UNCONFIGURED_HINT)
    if cfg.tasklist.mutation_mode == "local":
        return repo_root, False, cfg.tasklist.mutation_mode, cfg.tasklist.authoritative_branch
    try:
        authoritative = find_authoritative_root(repo_root, branch=cfg.tasklist.authoritative_branch)
        validate_authoritative_checkout(
            authoritative,
            expected_branch=cfg.tasklist.authoritative_branch,
            caller_root=repo_root,
        )
    except AuthorityError as exc:
        raise CommandError(str(exc)) from exc
    return (
        authoritative,
        repo_root.resolve() != authoritative.resolve(),
        cfg.tasklist.mutation_mode,
        cfg.tasklist.authoritative_branch,
    )
```

- [ ] **Step 4: Run the tests again**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_unconfigured_mutation.py -v
```

Expected: every test except `test_explicit_local_mode_still_mutates` passes. The latter still fails on `config init-local` (forward-referenced to Task 3).

- [ ] **Step 5: Run the full tasktool suite to surface regressions**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/ -v
```

Expected: failures in any test that called `tasktool init` / `tasktool start` etc. against a fresh `tmp_path` without first configuring authority. Capture the list — those tests get explicit `config init-local` or `config init-authority` setup in Task 6.

- [ ] **Step 6: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/tests/test_unconfigured_mutation.py
git commit -m "X12: refuse mutations when tasktool authority routing is unconfigured"
```

---

## Task 3: Add `tasktool config init-local` subcommand

**Files:**
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/cli.py`
- Create: `tools/tasktool/tests/test_init_local.py`

- [ ] **Step 1: Write the failing test**

Create `tools/tasktool/tests/test_init_local.py`:

```python
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_DIR = REPO_ROOT / "tools"


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "tasktool", *args],
        capture_output=True, text=True, cwd=cwd, env=env,
    )


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, capture_output=True)


def test_init_local_writes_config(tmp_path):
    _git_init(tmp_path)
    r = run_cli("config", "init-local", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads((tmp_path / ".tasktool" / "config.json").read_text())
    assert data["tasklist"]["mutation_mode"] == "local"


def test_init_local_then_init_succeeds(tmp_path):
    _git_init(tmp_path)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "--allow-empty", "-m", "init"],
                   cwd=tmp_path, check=True, capture_output=True)
    assert run_cli("config", "init-local", cwd=tmp_path).returncode == 0
    r = run_cli("init", "--project", "demo", cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / "docs" / "tasklist.json").exists()


def test_init_local_refuses_overwriting_authoritative(tmp_path):
    _git_init(tmp_path)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "--allow-empty", "-m", "init"],
                   cwd=tmp_path, check=True, capture_output=True)
    assert run_cli("config", "init-authority", "--branch", "main", cwd=tmp_path).returncode == 0
    r = run_cli("config", "init-local", cwd=tmp_path)
    assert r.returncode != 0
    assert "already configured" in r.stderr or "already configured" in r.stdout
```

- [ ] **Step 2: Run the test, expect failure**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_init_local.py -v
```

Expected: argparse-level failures (`invalid choice: 'init-local'`).

- [ ] **Step 3: Add `cmd_config_init_local` to commands.py**

In `tools/tasktool/commands.py`, immediately after `cmd_config_init_authority`, add:

Design note (intentional): `cmd_config_init_local` refuses ONLY when the existing config is `authoritative-checkout` — switching away from authoritative routing is a non-trivial workflow change and should require deliberate operator action (delete the config file first). It is idempotent against an existing `local` config (re-runs are no-ops, exit 0) and overwrites a config file whose `mutation_mode` is missing (treating that case as bootstrap completion).

```python
def cmd_config_init_local(*, repo_root: Path) -> None:
    existing_path = repo_root / ".tasktool" / "config.json"
    if existing_path.exists():
        raw = json.loads(existing_path.read_text(encoding="utf-8"))
        mode = raw.get("tasklist", {}).get("mutation_mode")
        if mode == "authoritative-checkout":
            raise CommandError(
                "tasktool: this repository is already configured for authoritative-checkout "
                "routing; refusing to overwrite. Delete `.tasktool/config.json` first if you "
                "really intend to switch to local mode."
            )
        if mode == "local":
            # Idempotent: already configured for local mode.
            print(
                "tasktool: already configured for local mutation mode (no change).",
                file=sys.stderr,
            )
            return
    cfg = TasktoolConfig(
        tasklist=TasklistConfig(mutation_mode="local")
    )
    save_config(repo_root, cfg)
    _git_stage(repo_root, repo_root / ".tasktool" / "config.json")
    print(
        "tasktool: configured for local mutation mode. Worktree-side mutations will "
        "NOT be routed to a shared authoritative checkout.",
        file=sys.stderr,
    )
```

Ensure `json` is imported at the top of `commands.py` (it already is — check the existing import block).

- [ ] **Step 4: Register the subcommand in cli.py**

In `tools/tasktool/cli.py`, immediately after the `init-authority` parser registration (around line 29-30), add:

```python
    p_config_local = config_sub.add_parser("init-local")
    # No arguments — explicit opt-out, writes mutation_mode=local.
```

In the dispatch block where `config_cmd == "init-authority"` is handled (around `tools/tasktool/cli.py:191`), add an `elif` branch:

```python
            elif args.config_cmd == "init-local":
                commands.cmd_config_init_local(repo_root=repo_root)
```

- [ ] **Step 5: Run the test, expect pass**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_init_local.py tools/tasktool/tests/test_unconfigured_mutation.py -v
```

Expected: both files pass in full now.

- [ ] **Step 6: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/tests/test_init_local.py
git commit -m "X12: add tasktool config init-local for auditable local-mode opt-out"
```

---

## Task 4: Implement the dataclass-driven migrator

**Files:**
- Create: `tools/tasktool/migrate.py`
- Create: `tools/tasktool/tests/test_migrate.py`

- [ ] **Step 1: Write the failing test for the diff walker**

Create `tools/tasktool/tests/test_migrate.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import date

import pytest

from tasktool.migrate import (
    Conflict,
    Delta,
    compute_deltas,
    apply_deltas,
    walker_field_coverage,
)
from tasktool.model import (
    ArchivedPhase,
    CrossCutting,
    Phase,
    Project,
    Slice,
    Status,
    Task,
)


def _today() -> str:
    return date.today().isoformat()


def _project_with_slice(slice_status: Status = Status.READY) -> Project:
    return Project(
        project="demo",
        north_star="ns",
        last_reviewed=_today(),
        phases=[
            Phase(
                id="P1", title="phase", created=_today(),
                slices=[
                    Slice(id="S1", title="slice", created=_today(),
                          status=slice_status),
                ],
            )
        ],
    )


def test_no_drift_yields_no_deltas():
    a = _project_with_slice()
    b = _project_with_slice()
    deltas, conflicts = compute_deltas(local=a, authoritative=b)
    assert deltas == []
    assert conflicts == []


def test_slice_status_drift_is_a_delta():
    local = _project_with_slice(slice_status=Status.IN_PROGRESS)
    authoritative = _project_with_slice(slice_status=Status.READY)
    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)
    assert any(d.row_id == "P1.S1" and d.field == "status" for d in deltas)
    assert conflicts == []


def test_local_only_row_is_addition():
    local = _project_with_slice()
    local.cross_cutting.append(
        CrossCutting(id="X9", title="local-only", created=_today())
    )
    authoritative = _project_with_slice()
    deltas, _ = compute_deltas(local=local, authoritative=authoritative)
    assert any(d.kind == "add" and d.row_id == "X9" for d in deltas)


def test_authoritative_only_row_is_kept_not_deleted():
    local = _project_with_slice()
    authoritative = _project_with_slice()
    authoritative.cross_cutting.append(
        CrossCutting(id="X9", title="authority-only", created=_today())
    )
    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)
    # Authority-only rows are flagged but NOT deleted under any policy.
    assert any(c.kind == "authoritative-only" and c.row_id == "X9" for c in conflicts)
    assert not any(d.kind == "delete" for d in deltas)


def test_apply_deltas_accept_local_preserves_authoritative_only():
    local = _project_with_slice(slice_status=Status.IN_PROGRESS)
    authoritative = _project_with_slice(slice_status=Status.READY)
    authoritative.cross_cutting.append(
        CrossCutting(id="X9", title="authority-only", created=_today())
    )
    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)
    merged = apply_deltas(
        authoritative=authoritative, local=local,
        deltas=deltas, conflicts=conflicts, policy="accept-local",
    )
    # X9 still present.
    assert any(c.id == "X9" for c in merged.cross_cutting)
    # P1.S1 status updated to local's IN_PROGRESS.
    assert merged.phases[0].slices[0].status == Status.IN_PROGRESS


def test_nested_task_field_drift_migrates():
    local = _project_with_slice()
    local.phases[0].slices[0].tasks.append(
        Task(id="T1", title="task", created=_today(),
             status=Status.IN_PROGRESS, notes="local")
    )
    authoritative = _project_with_slice()
    authoritative.phases[0].slices[0].tasks.append(
        Task(id="T1", title="task", created=_today(),
             status=Status.READY, notes="")
    )
    deltas, _ = compute_deltas(local=local, authoritative=authoritative)
    fields_changed = {(d.row_id, d.field) for d in deltas}
    assert ("P1.S1.T1", "status") in fields_changed
    assert ("P1.S1.T1", "notes") in fields_changed


def test_walker_covers_every_dataclass_field():
    """Meta-test: introspect the walker against `dataclasses.fields()` on every
    row dataclass and assert no field is silently missing from the walker."""
    coverage = walker_field_coverage()
    for row_type in (Project, Phase, Slice, Task, CrossCutting, ArchivedPhase):
        declared = {f.name for f in fields(row_type)}
        walked = coverage.get(row_type.__name__, set())
        missing = declared - walked
        assert not missing, (
            f"{row_type.__name__} fields missing from migrator walker: {missing}. "
            "Update tools/tasktool/migrate.py:_field_walker_map."
        )


def test_archived_phase_drift_migrates():
    local = _project_with_slice()
    local.archived_phases.append(
        ArchivedPhase(id="P0", title="old", archived_path="docs/x", archived_date=_today())
    )
    authoritative = _project_with_slice()
    deltas, _ = compute_deltas(local=local, authoritative=authoritative)
    assert any(d.kind == "add" and d.row_id == "P0" for d in deltas)


def test_top_level_project_field_drift_migrates():
    local = _project_with_slice()
    local.north_star = "new mission"
    authoritative = _project_with_slice()
    authoritative.north_star = "old mission"
    deltas, _ = compute_deltas(local=local, authoritative=authoritative)
    assert any(d.row_id == "<project>" and d.field == "north_star" for d in deltas)
```

- [ ] **Step 2: Run, expect ImportError**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_migrate.py -v
```

Expected: `ModuleNotFoundError: No module named 'tasktool.migrate'`.

- [ ] **Step 3: Implement the migrator**

Create `tools/tasktool/migrate.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, fields, replace
from enum import Enum
from typing import Iterable, Literal

from tasktool.model import (
    ArchivedPhase,
    CrossCutting,
    Phase,
    Project,
    Slice,
    Task,
)

Policy = Literal["accept-local", "accept-authoritative"]

# Row identity rules. Each entry: (collection-attribute-name on parent, child-row-type,
# id-attribute on child, optional nested walker key). The walker descends in this order.
_PROJECT_COLLECTIONS = ("phases", "cross_cutting", "archived_phases")


@dataclass(frozen=True)
class Delta:
    """A field- or row-level change to apply to the authoritative project."""
    kind: Literal["field", "add"]
    row_id: str   # e.g. "P1.S1", "P1.S1.T2", "X9", "<project>"
    field: str | None   # None when kind == "add"
    local_value: object | None
    authoritative_value: object | None


@dataclass(frozen=True)
class Conflict:
    """Drift that requires operator awareness but does not auto-resolve to deletion."""
    kind: Literal["authoritative-only"]
    row_id: str
    note: str


# ─── Public API ──────────────────────────────────────────────────────────────


def compute_deltas(*, local: Project, authoritative: Project) -> tuple[list[Delta], list[Conflict]]:
    deltas: list[Delta] = []
    conflicts: list[Conflict] = []
    _diff_project(local, authoritative, deltas, conflicts)
    return deltas, conflicts


def apply_deltas(
    *,
    authoritative: Project,
    local: Project,
    deltas: list[Delta],
    conflicts: list[Conflict],
    policy: Policy,
) -> Project:
    """Return a NEW Project with deltas applied per the policy. Never mutates
    inputs. Authoritative-only rows (in `conflicts`) are preserved unconditionally."""
    if policy == "accept-authoritative":
        return authoritative
    if policy != "accept-local":
        raise ValueError(f"unknown policy: {policy}")
    return _apply_local(authoritative, local, deltas)


def render_diff(deltas: list[Delta], conflicts: list[Conflict]) -> str:
    """Human-readable diff for stdout."""
    lines: list[str] = []
    for d in deltas:
        if d.kind == "add":
            lines.append(f"{d.row_id:12s}  add (local-only)")
        else:
            la = _fmt_value(d.local_value)
            au = _fmt_value(d.authoritative_value)
            lines.append(f"{d.row_id:12s}  {d.field}: {au} → {la}")
    for c in conflicts:
        lines.append(f"{c.row_id:12s}  authoritative-only (kept): {c.note}")
    if not lines:
        return "no drift detected\n"
    return "\n".join(lines) + "\n"


def walker_field_coverage() -> dict[str, set[str]]:
    """Return {RowTypeName: {field_names_the_walker_compares}}.
    Used by the meta-test to assert no model field is silently missing."""
    coverage: dict[str, set[str]] = {}
    coverage["Project"] = set(_project_scalar_fields())
    coverage["Project"].update(_PROJECT_COLLECTIONS)
    coverage["Phase"] = {f.name for f in fields(Phase)}
    coverage["Slice"] = {f.name for f in fields(Slice)}
    coverage["Task"] = {f.name for f in fields(Task)}
    coverage["CrossCutting"] = {f.name for f in fields(CrossCutting)}
    coverage["ArchivedPhase"] = {f.name for f in fields(ArchivedPhase)}
    return coverage


# ─── Internals ───────────────────────────────────────────────────────────────


def _project_scalar_fields() -> tuple[str, ...]:
    skip = set(_PROJECT_COLLECTIONS)
    return tuple(f.name for f in fields(Project) if f.name not in skip)


def _diff_project(
    local: Project,
    authoritative: Project,
    deltas: list[Delta],
    conflicts: list[Conflict],
) -> None:
    # Top-level scalar fields.
    for fname in _project_scalar_fields():
        lv = getattr(local, fname)
        av = getattr(authoritative, fname)
        if lv != av:
            deltas.append(Delta(kind="field", row_id="<project>", field=fname,
                                 local_value=lv, authoritative_value=av))
    # phases (with nested slices and tasks).
    _diff_collection(
        local_rows=local.phases,
        authoritative_rows=authoritative.phases,
        id_prefix="",
        row_dataclass=Phase,
        nested=[("slices", Slice, [("tasks", Task)])],
        deltas=deltas,
        conflicts=conflicts,
    )
    # cross_cutting.
    _diff_collection(
        local_rows=local.cross_cutting,
        authoritative_rows=authoritative.cross_cutting,
        id_prefix="",
        row_dataclass=CrossCutting,
        nested=[],
        deltas=deltas,
        conflicts=conflicts,
    )
    # archived_phases.
    _diff_collection(
        local_rows=local.archived_phases,
        authoritative_rows=authoritative.archived_phases,
        id_prefix="",
        row_dataclass=ArchivedPhase,
        nested=[],
        deltas=deltas,
        conflicts=conflicts,
    )


def _diff_collection(
    *,
    local_rows: list,
    authoritative_rows: list,
    id_prefix: str,
    row_dataclass,
    nested: list[tuple[str, type, list[tuple[str, type]]]],
    deltas: list[Delta],
    conflicts: list[Conflict],
) -> None:
    local_by_id = {r.id: r for r in local_rows}
    auth_by_id = {r.id: r for r in authoritative_rows}
    for rid in local_by_id.keys() - auth_by_id.keys():
        deltas.append(Delta(kind="add", row_id=_qualify(id_prefix, rid),
                            field=None, local_value=local_by_id[rid],
                            authoritative_value=None))
    for rid in auth_by_id.keys() - local_by_id.keys():
        conflicts.append(Conflict(kind="authoritative-only",
                                  row_id=_qualify(id_prefix, rid),
                                  note=f"present in authoritative tasklist only"))
    for rid in local_by_id.keys() & auth_by_id.keys():
        lr = local_by_id[rid]
        ar = auth_by_id[rid]
        qrid = _qualify(id_prefix, rid)
        # Compare every dataclass field except declared collection attributes,
        # which are handled by recursive descent.
        nested_attrs = {nattr for nattr, _, _ in nested}
        for f in fields(row_dataclass):
            if f.name in nested_attrs:
                continue
            lv = getattr(lr, f.name)
            av = getattr(ar, f.name)
            if lv != av:
                deltas.append(Delta(kind="field", row_id=qrid, field=f.name,
                                     local_value=lv, authoritative_value=av))
        # Recurse into nested collections.
        for nattr, ndataclass, deeper in nested:
            _diff_collection(
                local_rows=getattr(lr, nattr),
                authoritative_rows=getattr(ar, nattr),
                id_prefix=qrid,
                row_dataclass=ndataclass,
                nested=[(da, dc, []) for da, dc in deeper],
                deltas=deltas,
                conflicts=conflicts,
            )


def _qualify(prefix: str, rid: str) -> str:
    return f"{prefix}.{rid}" if prefix else rid


def _apply_local(authoritative: Project, local: Project, deltas: list[Delta]) -> Project:
    """Rebuild the authoritative Project with local-wins deltas applied.
    Implementation: deep-copy via dataclass replace at each level, then mutate
    in place against the new copy. authoritative-only rows are kept by virtue
    of starting from `authoritative` and only adding/overwriting."""
    import copy
    merged = copy.deepcopy(authoritative)
    # Top-level field deltas.
    for d in deltas:
        if d.row_id == "<project>" and d.kind == "field":
            setattr(merged, d.field, d.local_value)
    # Row-level operations.
    _apply_collection(merged.phases, local.phases, deltas, "", Phase,
                     [("slices", Slice, [("tasks", Task)])])
    _apply_collection(merged.cross_cutting, local.cross_cutting, deltas, "",
                     CrossCutting, [])
    _apply_collection(merged.archived_phases, local.archived_phases, deltas, "",
                     ArchivedPhase, [])
    return merged


def _apply_collection(
    auth_rows: list,
    local_rows: list,
    deltas: list[Delta],
    id_prefix: str,
    row_dataclass,
    nested: list[tuple[str, type, list[tuple[str, type]]]],
) -> None:
    import copy
    auth_by_id = {r.id: r for r in auth_rows}
    local_by_id = {r.id: r for r in local_rows}
    nested_attrs = {nattr for nattr, _, _ in nested}
    # Additions from local-only.
    for rid, lrow in local_by_id.items():
        qrid = _qualify(id_prefix, rid)
        if rid not in auth_by_id and any(
            d.kind == "add" and d.row_id == qrid for d in deltas
        ):
            auth_rows.append(copy.deepcopy(lrow))
            auth_by_id[rid] = auth_rows[-1]
    # Field-level overwrites for rows in both.
    for rid, arow in auth_by_id.items():
        if rid not in local_by_id:
            continue
        lrow = local_by_id[rid]
        qrid = _qualify(id_prefix, rid)
        for d in deltas:
            if d.kind == "field" and d.row_id == qrid and d.field not in nested_attrs:
                setattr(arow, d.field, d.local_value)
        # Recurse.
        for nattr, ndataclass, deeper in nested:
            _apply_collection(
                auth_rows=getattr(arow, nattr),
                local_rows=getattr(lrow, nattr),
                deltas=deltas,
                id_prefix=qrid,
                row_dataclass=ndataclass,
                nested=[(da, dc, []) for da, dc in deeper],
            )


def _fmt_value(v: object) -> str:
    if v is None:
        return "null"
    if isinstance(v, Enum):
        return v.value
    if isinstance(v, str):
        return repr(v)
    return repr(v)
```

- [ ] **Step 4: Run the migrate tests, expect pass**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_migrate.py -v
```

Expected: all 9 tests pass.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/migrate.py tools/tasktool/tests/test_migrate.py
git commit -m "X12: add dataclass-driven migrator for tasktool drift reconciliation"
```

---

## Task 5: Wire `tasktool config migrate-from-local` CLI subcommand

**Files:**
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/cli.py`
- Create: `tools/tasktool/tests/test_migrate_cli.py`

- [ ] **Step 1: Write the failing CLI integration test**

Create `tools/tasktool/tests/test_migrate_cli.py`:

```python
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_DIR = REPO_ROOT / "tools"


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "tasktool", *args],
        capture_output=True, text=True, cwd=cwd, env=env,
    )


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _setup_main_with_worktree(tmp_path: Path) -> tuple[Path, Path]:
    """Build a repo on `main`, populate tasklist, then add a linked worktree
    on a feature branch with a divergent tasklist. NO `.tasktool/config.json`
    in either tree."""
    main = tmp_path / "main"
    main.mkdir()
    _git("init", "-b", "main", cwd=main)
    _git("config", "user.email", "t@t", cwd=main)
    _git("config", "user.name", "t", cwd=main)
    (main / "docs").mkdir()
    (main / "docs" / "tasklist.json").write_text(json.dumps({
        "schema_version": 1, "project": "demo", "north_star": "",
        "last_reviewed": None,
        "phases": [{
            "id": "P1", "title": "p1", "created": "2026-05-20", "status": "ready",
            "started": None, "closed": None, "spec_path": None, "plan_path": None,
            "planning_path": None, "phase_reviewer_chain": None, "notes": "",
            "slices": [{
                "id": "S1", "title": "s1", "created": "2026-05-20", "status": "ready",
                "started": None, "closed": None, "blocked_on": None,
                "depends_on": [], "planning_status": "proposed",
                "parallel_group": None, "plan_path": None, "refs": [],
                "notes": "", "reviewer_chain": None, "tasks": []
            }],
        }],
        "cross_cutting": [], "archived_phases": [],
    }, indent=2))
    _git("add", ".", cwd=main)
    _git("commit", "-m", "init", cwd=main)

    work = tmp_path / "wt-feature"
    _git("worktree", "add", "-b", "feature", str(work), cwd=main)
    # Diverge on the worktree: slice goes in-progress.
    tl = json.loads((work / "docs" / "tasklist.json").read_text())
    tl["phases"][0]["slices"][0]["status"] = "in_progress"
    tl["phases"][0]["slices"][0]["started"] = "2026-05-20"
    (work / "docs" / "tasklist.json").write_text(json.dumps(tl, indent=2))
    return main, work


def test_migrate_dry_run_no_writes(tmp_path):
    main, work = _setup_main_with_worktree(tmp_path)
    r = run_cli(
        "config", "migrate-from-local",
        "--authority-root", str(main),
        "--dry-run",
        cwd=work,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "P1.S1" in r.stdout
    assert "status" in r.stdout
    # Authoritative file unchanged.
    auth = json.loads((main / "docs" / "tasklist.json").read_text())
    assert auth["phases"][0]["slices"][0]["status"] == "ready"


def test_migrate_accept_local_applies(tmp_path):
    main, work = _setup_main_with_worktree(tmp_path)
    r = run_cli(
        "config", "migrate-from-local",
        "--authority-root", str(main),
        "--accept-local",
        cwd=work,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    auth = json.loads((main / "docs" / "tasklist.json").read_text())
    assert auth["phases"][0]["slices"][0]["status"] == "in_progress"
    assert auth["phases"][0]["slices"][0]["started"] == "2026-05-20"
    # Bootstrap side effect: authority root now has a config.
    cfg = json.loads((main / ".tasktool" / "config.json").read_text())
    assert cfg["tasklist"]["mutation_mode"] == "authoritative-checkout"


def test_migrate_accept_authoritative_noop(tmp_path):
    main, work = _setup_main_with_worktree(tmp_path)
    before = (main / "docs" / "tasklist.json").read_text()
    r = run_cli(
        "config", "migrate-from-local",
        "--authority-root", str(main),
        "--accept-authoritative",
        cwd=work,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert (main / "docs" / "tasklist.json").read_text() == before


def test_migrate_no_drift_exits_clean(tmp_path):
    main, work = _setup_main_with_worktree(tmp_path)
    # Sync the worktree back to authoritative so there is no drift.
    auth_text = (main / "docs" / "tasklist.json").read_text()
    (work / "docs" / "tasklist.json").write_text(auth_text)
    r = run_cli(
        "config", "migrate-from-local",
        "--authority-root", str(main),
        "--accept-local",
        cwd=work,
    )
    assert r.returncode == 0
    assert "no drift detected" in r.stdout


def test_migrate_requires_authority_root(tmp_path):
    main, work = _setup_main_with_worktree(tmp_path)
    r = run_cli(
        "config", "migrate-from-local",
        cwd=work,
    )
    assert r.returncode != 0
    assert "--authority-root" in r.stderr


def test_migrate_requires_policy_in_non_tty(tmp_path):
    main, work = _setup_main_with_worktree(tmp_path)
    r = run_cli(
        "config", "migrate-from-local",
        "--authority-root", str(main),
        cwd=work,
    )
    assert r.returncode != 0
    assert "accept-local" in r.stderr or "accept-authoritative" in r.stderr


def test_migrate_dry_run_works_without_policy(tmp_path):
    """Spec §3 / F1: --dry-run must be usable without --accept-* in non-TTY contexts."""
    main, work = _setup_main_with_worktree(tmp_path)
    r = run_cli(
        "config", "migrate-from-local",
        "--authority-root", str(main),
        "--dry-run",
        cwd=work,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "P1.S1" in r.stdout


def test_migrate_with_explicit_local_root(tmp_path):
    """Spec §3: --local-root can be passed explicitly when caller is invoked
    from somewhere other than the drifted worktree."""
    main, work = _setup_main_with_worktree(tmp_path)
    # Invoke from main but target the worktree as local-root.
    r = run_cli(
        "config", "migrate-from-local",
        "--authority-root", str(main),
        "--local-root", str(work),
        "--accept-local",
        cwd=main,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    auth = json.loads((main / "docs" / "tasklist.json").read_text())
    assert auth["phases"][0]["slices"][0]["status"] == "in_progress"


def test_migrate_different_repositories_errors(tmp_path):
    """Spec §error-handling: authority-root and local-root must share a common git dir."""
    main, _work = _setup_main_with_worktree(tmp_path)
    # Build a totally separate repo.
    other = tmp_path / "other"
    other.mkdir()
    _git("init", "-b", "main", cwd=other)
    _git("config", "user.email", "t@t", cwd=other)
    _git("config", "user.name", "t", cwd=other)
    (other / "docs").mkdir()
    (other / "docs" / "tasklist.json").write_text('{"schema_version":1,"project":"x","phases":[],"cross_cutting":[],"archived_phases":[]}')
    _git("add", ".", cwd=other)
    _git("commit", "-m", "init", cwd=other)

    r = run_cli(
        "config", "migrate-from-local",
        "--authority-root", str(main),
        "--local-root", str(other),
        "--accept-local",
        cwd=main,
    )
    assert r.returncode != 0
    assert "not the same repository" in r.stderr


def test_migrate_honours_existing_authority_config(tmp_path):
    """F2: when authority_root has a configured authoritative_branch, migrate
    validates against that branch — not against authority_root's current branch."""
    main, work = _setup_main_with_worktree(tmp_path)
    # Pre-configure the authority root.
    assert run_cli("config", "init-authority", "--branch", "main", cwd=main).returncode == 0
    _git("add", ".tasktool/config.json", cwd=main)
    _git("commit", "-m", "configure authority", cwd=main)
    r = run_cli(
        "config", "migrate-from-local",
        "--authority-root", str(main),
        "--accept-local",
        cwd=work,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    auth = json.loads((main / "docs" / "tasklist.json").read_text())
    assert auth["phases"][0]["slices"][0]["status"] == "in_progress"
    # The pre-existing config is preserved, not overwritten.
    cfg = json.loads((main / ".tasktool" / "config.json").read_text())
    assert cfg["tasklist"]["mutation_mode"] == "authoritative-checkout"
    assert cfg["tasklist"]["authoritative_branch"] == "main"


def test_migrate_preserves_authority_only_rows(tmp_path):
    main, work = _setup_main_with_worktree(tmp_path)
    # Add a cross-cutting row to the authoritative tasklist that isn't in the worktree.
    auth = json.loads((main / "docs" / "tasklist.json").read_text())
    auth["cross_cutting"].append({
        "id": "X9", "title": "auth-only", "created": "2026-05-20",
        "status": "ready", "started": None, "closed": None,
        "refs": [], "notes": "",
    })
    (main / "docs" / "tasklist.json").write_text(json.dumps(auth, indent=2))
    _git("add", ".", cwd=main)
    _git("commit", "-m", "add x9", cwd=main)
    r = run_cli(
        "config", "migrate-from-local",
        "--authority-root", str(main),
        "--accept-local",
        cwd=work,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    merged = json.loads((main / "docs" / "tasklist.json").read_text())
    assert any(c["id"] == "X9" for c in merged["cross_cutting"])


def test_migrate_emits_notify_events(tmp_path, monkeypatch):
    """Spec test #12: status transitions during migration emit notify events.
    Uses SUPERSTAR_NOTIFY_LOG so the worker writes one JSON line per event
    to a tempfile instead of routing through TTS."""
    main, work = _setup_main_with_worktree(tmp_path)
    log_path = tmp_path / "notify.log"
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    env["SUPERSTAR_NOTIFY_LOG"] = str(log_path)
    # Override the autouse fixture's SUPERSTAR_NOTIFY_DISABLE for this subprocess only.
    env.pop("SUPERSTAR_NOTIFY_DISABLE", None)
    r = subprocess.run(
        [sys.executable, "-m", "tasktool",
         "config", "migrate-from-local",
         "--authority-root", str(main),
         "--accept-local"],
        capture_output=True, text=True, cwd=work, env=env,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert log_path.exists(), "notify log was not written"
    events = [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]
    # At least one event for P1.S1 going ready -> in_progress.
    matches = [e for e in events if "P1.S1" in e.get("message", "")
               and "in progress" in e.get("message", "")]
    assert matches, f"no notify event found for P1.S1 status change. events={events}"
```

- [ ] **Step 2: Run, expect failure**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_migrate_cli.py -v
```

Expected: `argparse` errors (`invalid choice: 'migrate-from-local'`).

- [ ] **Step 3: Add the command body**

Before writing the body, make `same_repository` available — `commands.py` currently imports selected names from `tasktool.worktree` but not this one. Update the existing import block at the top of `tools/tasktool/commands.py` to add `same_repository`:

```python
from tasktool.worktree import (
    AuthorityError,
    find_authoritative_root,
    git_current_branch,
    git_common_dir,
    has_unmerged_paths,
    same_repository,                      # ← add
    tasklist_has_unsafe_dirty_state,
    tasktool_lock,
    validate_authoritative_checkout,
)
```

(Confirm the exact list of imports already present and add `same_repository` to the existing alphabetised block; do not duplicate names that are already imported.)

Also verify the helper for loading a `Project` from an absolute path. Inspect `tools/tasktool/serialize.py`:

```bash
grep -n "^def " tools/tasktool/serialize.py
```

If `serialize.py` does not already expose a `Project`-returning loader that takes an absolute path, look at how `_load(repo_root)` in `commands.py` deserialises today and reuse the same code path. The plan body below uses the placeholder name `load_project_from_path`; replace both call sites with the function that exists (e.g. `project_from_json` or `_load` invoked with the repo root computed from the tasklist path).

In `tools/tasktool/commands.py`, immediately after `cmd_config_init_local`, add:

```python
def cmd_config_migrate_from_local(
    *,
    caller_root: Path,
    authority_root: Path,
    local_root: Path | None,
    dry_run: bool,
    policy: str | None,
) -> None:
    """Reconcile a worktree's docs/tasklist.json into an authoritative checkout."""
    import sys
    from tasktool.migrate import (
        apply_deltas,
        compute_deltas,
        render_diff,
    )

    local_root = (local_root or caller_root).resolve()
    authority_root = authority_root.resolve()

    if not authority_root.exists():
        raise CommandError(f"authority root does not exist: {authority_root}")
    if not local_root.exists():
        raise CommandError(f"local root does not exist: {local_root}")
    if not same_repository(authority_root, local_root):
        raise CommandError(
            "authority root and local root are not the same repository"
        )

    auth_tasklist = authority_root / "docs" / "tasklist.json"
    local_tasklist = local_root / "docs" / "tasklist.json"
    if not auth_tasklist.exists():
        raise CommandError(
            f"authoritative tasklist not found: {auth_tasklist}. "
            "Run `tasktool init` in the authority checkout first."
        )
    if not local_tasklist.exists():
        raise CommandError(
            f"local tasklist not found: {local_tasklist}. Nothing to migrate."
        )

    # Resolve target branch: honour an existing authority config if present;
    # otherwise fall back to the authority root's current branch and persist it
    # later (after a successful migration).
    auth_cfg = load_config(authority_root)
    if auth_cfg.tasklist.mutation_mode == "authoritative-checkout":
        branch = auth_cfg.tasklist.authoritative_branch
    else:
        branch = git_current_branch(authority_root)
        if not branch:
            raise CommandError(
                f"authority root is in detached HEAD state and has no configured "
                f"authoritative branch; cannot determine branch: {authority_root}"
            )
    try:
        validate_authoritative_checkout(
            authority_root,
            expected_branch=branch,
            caller_root=local_root,
        )
    except AuthorityError as exc:
        raise CommandError(str(exc)) from exc

    # Load both tasklists and compute the diff up-front so --dry-run can stop
    # without needing a policy.
    local_project = _load_project_at(local_tasklist)
    auth_project = _load_project_at(auth_tasklist)
    deltas, conflicts = compute_deltas(local=local_project, authoritative=auth_project)
    diff_text = render_diff(deltas, conflicts)
    print(diff_text, end="")

    if not deltas and not conflicts:
        return  # "no drift detected" already printed by render_diff

    if dry_run:
        return

    # Now resolve policy — only required when we will actually write.
    if policy is None:
        if sys.stdin.isatty():
            policy = _prompt_policy_interactive()
        else:
            raise CommandError(
                "migrate-from-local requires one of --accept-local or --accept-authoritative "
                "in non-interactive contexts"
            )

    # Acquire lock and apply.
    with tasktool_lock(authority_root):
        # Re-read inside the lock for defence against concurrent writes.
        auth_project_inside_lock = _load_project_at(auth_tasklist)
        merged = apply_deltas(
            authoritative=auth_project_inside_lock, local=local_project,
            deltas=deltas, conflicts=conflicts, policy=policy,
        )
        _save(authority_root, merged)

        # Bootstrap config in authority root if missing, so subsequent mutations route.
        cfg_path = authority_root / ".tasktool" / "config.json"
        if auth_cfg.tasklist.mutation_mode != "authoritative-checkout":
            save_config(authority_root, TasktoolConfig(
                tasklist=TasklistConfig(
                    mutation_mode="authoritative-checkout",
                    authoritative_branch=branch,
                ),
            ))
            _git_stage(authority_root, cfg_path)

    # Notify on status transitions: pass the Status enum through unchanged so
    # _notify_status (which calls .value) stays happy.
    _notify_status_transitions(local_project, auth_project)

    status_changes = sum(1 for d in deltas if d.field == "status")
    print(
        f"migrated {len(deltas)} deltas ({status_changes} status transitions) "
        f"to {authority_root}",
        file=sys.stderr,
    )


def _load_project_at(tasklist_path: Path) -> "Project":
    """Load a Project from any tasklist.json path. Thin wrapper over the existing
    JSON deserialiser in tools/tasktool/serialize.py — replace the body with a
    direct call to the existing helper after running:

        grep -n '^def ' tools/tasktool/serialize.py

    For example, if serialize.py exposes `project_from_json(path: Path) -> Project`,
    this function is one line: `return project_from_json(tasklist_path)`. If only
    a repo-root-based loader exists, derive the repo root from the tasklist path
    (`tasklist_path.parent.parent`) and call that."""
    raise NotImplementedError(
        "replace with the appropriate call to tools/tasktool/serialize.py"
    )


def _prompt_policy_interactive() -> str:
    import sys
    sys.stderr.write("Choose conflict policy [local/authoritative/abort]: ")
    sys.stderr.flush()
    answer = sys.stdin.readline().strip().lower()
    if answer in ("local", "l"):
        return "accept-local"
    if answer in ("authoritative", "auth", "a"):
        return "accept-authoritative"
    raise CommandError("aborted by operator")


def _notify_status_transitions(local: "Project", pre_merge_authoritative: "Project") -> None:
    """Emit notify events for rows whose status changed between pre-merge
    authoritative and local. Best-effort; never raises. Passes the Status enum
    through unchanged — _notify_status expects an enum, not a string."""
    try:
        def walk(p):
            for cc in p.cross_cutting:
                yield cc.id, cc, "cross"
            for ph in p.phases:
                yield ph.id, ph, "phase"
                for sl in ph.slices:
                    yield f"{ph.id}.{sl.id}", sl, "slice"
        pre = {qid: row for qid, row, _ in walk(pre_merge_authoritative)}
        for qid, row, kind in walk(local):
            old = pre.get(qid)
            if old is None:
                continue
            row_status = getattr(row, "status", None)
            old_status = getattr(old, "status", None)
            if row_status != old_status:
                _notify_status(
                    qid=qid, kind=kind,
                    status=row_status,           # Status enum, not str
                    title=getattr(row, "title", ""),
                )
    except Exception:
        pass
```

Important: `_load_project_at` above is a placeholder body that raises. The implementing engineer MUST replace it with one or two lines that delegate to the existing loader in `tools/tasktool/serialize.py`. Run the `grep -n "^def " tools/tasktool/serialize.py` command first, then pick the function that takes a `Path` and returns a `Project`. If only a repo-root helper exists, the implementation is:

```python
def _load_project_at(tasklist_path: Path) -> "Project":
    repo_root = tasklist_path.parent.parent
    return _load(repo_root)
```

— where `_load` is the existing helper already used by `cmd_init` and friends.

- [ ] **Step 4: Register CLI subparser**

In `tools/tasktool/cli.py`, after the `init-local` registration (added in Task 3), add:

```python
    p_migrate = config_sub.add_parser("migrate-from-local")
    p_migrate.add_argument("--authority-root", required=True,
                            help="Path to the checkout that will become authoritative.")
    p_migrate.add_argument("--local-root", default=None,
                            help="Path to the divergent checkout (default: caller repo root).")
    p_migrate.add_argument("--dry-run", action="store_true")
    policy_group = p_migrate.add_mutually_exclusive_group()
    policy_group.add_argument("--accept-local", dest="policy",
                              action="store_const", const="accept-local")
    policy_group.add_argument("--accept-authoritative", dest="policy",
                              action="store_const", const="accept-authoritative")
```

In the dispatch block, immediately after the `init-local` branch:

```python
            elif args.config_cmd == "migrate-from-local":
                commands.cmd_config_migrate_from_local(
                    caller_root=repo_root,
                    authority_root=Path(args.authority_root),
                    local_root=Path(args.local_root) if args.local_root else None,
                    dry_run=args.dry_run,
                    policy=args.policy,
                )
```

- [ ] **Step 5: Run the CLI test, expect pass**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_migrate_cli.py -v
```

Expected: all 7 tests pass.

- [ ] **Step 6: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/tests/test_migrate_cli.py
git commit -m "X12: add tasktool config migrate-from-local subcommand"
```

---

## Task 6: Repair regressions in existing tests and update skills

**Files:**
- Modify: as flagged by Task 2 step 5 (any test that relied on implicit-`local`).
- Modify: `skills/project-setup/SKILL.md`
- Modify: `skills/tasklist-discipline/SKILL.md`
- Modify: `skills/using-git-worktrees/SKILL.md`

- [ ] **Step 1: Run the full tasktool suite**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/ -v 2>&1 | tee /tmp/x12-test-output.txt
```

Capture failing tests. Each likely failure is one of:
1. A test that calls `tasktool init` (or any mutating command) against `tmp_path` without first running `config init-local` or `config init-authority`.
2. A test that asserts behaviour that depended on the implicit-`local` default.

- [ ] **Step 2: Repair each failing test by adding explicit `init-local`**

For each failing test that depended on implicit-`local`, prepend a `tasktool config init-local` invocation. Example pattern (apply to each occurrence):

Before:
```python
def test_foo(tmp_path):
    r = run_cli("init", "--project", "x", cwd=tmp_path)
    ...
```

After:
```python
def test_foo(tmp_path):
    # X12: tasktool now refuses mutations without explicit routing config.
    # This test asserts behaviour orthogonal to routing, so opt out via init-local.
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, check=True, capture_output=True)
    assert run_cli("config", "init-local", cwd=tmp_path).returncode == 0
    r = run_cli("init", "--project", "x", cwd=tmp_path)
    ...
```

For tests that specifically exercise the *authoritative* path, replace with `config init-authority --branch main`.

- [ ] **Step 3: Re-run, expect green**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/ -v
```

Expected: full suite passes.

- [ ] **Step 4: Update `skills/project-setup/SKILL.md`**

Locate the section in `skills/project-setup/SKILL.md` that describes tasktool bootstrap (search for `tasktool init`). Replace it with the new ordered sequence:

```markdown
1. **Configure authoritative routing before initialising.** From the target branch (typically `main`) of a clean checkout, run:

       tasktool config init-authority --branch main
       git add .tasktool/config.json
       git commit -m "tasktool: enable authoritative routing"

2. **Then create the tasklist.** From the same checkout:

       tasktool init --project <name>
       git add docs/tasklist.json
       git commit -m "tasktool: initialise tasklist"

   The order matters: `tasktool init` routes through `_write_context`, which refuses to run without an authority config.

3. **Project-setup precondition:** A missing or unconfigured `.tasktool/config.json` is a setup failure, on par with a missing `docs/tasklist.json`. Surface it the same way: do not proceed with downstream skill steps until both are present.

If a repo opts out of authoritative routing on purpose (no worktree convention, single-checkout workflows), the operator may run `tasktool config init-local` instead of `init-authority`. The opt-out should be a deliberate, committed choice — never the implicit default.
```

- [ ] **Step 5: Update `skills/tasklist-discipline/SKILL.md`**

Find the existing paragraph that opens "When `.tasktool/config.json` sets `tasklist.mutation_mode` to `authoritative-checkout`…" (around line 12). Replace it with:

```markdown
Tasktool requires authoritative-checkout routing for any mutating command. When the operator has run `tasktool config init-authority --branch <branch>`, mutating commands route writes to the configured authoritative checkout instead of editing the local worktree's `docs/tasklist.json` directly. Treat that routing as the source of truth: run `tasktool` from the implementation worktree, let the tool acquire the shared lock and update the authoritative checkout, then continue from the same implementation worktree.

If a mutation errors with `no authoritative-checkout routing configured`, run `tasktool config init-authority --branch <branch>` from the target branch (or, for an audited single-checkout workflow, `tasktool config init-local`). To reconcile a tasklist that drifted under the previous default — i.e. a worktree's `docs/tasklist.json` that was mutated without routing — run `tasktool config migrate-from-local --authority-root <path> --accept-local` from the drifted worktree.
```

- [ ] **Step 6: Update `skills/using-git-worktrees/SKILL.md`**

Find the line that begins "If tasktool authoritative-checkout routing is configured" (around line 16). Replace it with:

```markdown
Tasktool mutations from worktrees always route through the configured authoritative checkout. If `.tasktool/config.json` is missing in a repo you intend to work in, set it up first via `tasktool config init-authority --branch <branch>` from the target branch. Once routing is configured, mutations may be invoked from the implementation worktree: stay put, do not leave the worktree to hand-edit the authoritative checkout or run lifecycle commands elsewhere; run `tasktool start`, `tasktool ref`, `tasktool note`, and `tasktool close` from the active implementation worktree and let routing write through the configured authority.
```

- [ ] **Step 7: Skim-test the skill text**

```bash
grep -n "mutation_mode\|authoritative\|migrate-from-local" skills/project-setup/SKILL.md skills/tasklist-discipline/SKILL.md skills/using-git-worktrees/SKILL.md
```

Confirm: no remaining "when configured" / conditional phrasing for the rule itself; `migrate-from-local` mentioned at least once for the remediation path.

- [ ] **Step 8: Commit**

```bash
git add tools/tasktool/tests/ skills/project-setup/SKILL.md skills/tasklist-discipline/SKILL.md skills/using-git-worktrees/SKILL.md
git commit -m "X12: tighten tasktool skills to require authoritative routing"
```

---

## Task 7: Close X12 and prepare for review

- [ ] **Step 1: Run the full suite once more**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/ -v
```

Expected: all tests pass.

- [ ] **Step 2: Mark X12 review-ready**

The cross-cutting item moves to status `done` only after external `post-slice` review (next step in execution). Leave it `in_progress` here; closure happens via `tasktool close X12` after the post-slice review verdict.

- [ ] **Step 3: Capture evidence for the post-slice review**

Note for the post-slice reviewer:
- Spec: `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md`
- Plan: this document
- Spec reviewer chain: `docs/reviewer/x12-tasktool-require-authoritative-routing-design-spec/`
- Implementation evidence: commits `X12: *` on this branch.

---

## Out of scope

- Reconciling multistore's drift in code. After this slice ships, the operator runs `tasktool config migrate-from-local --authority-root /home/simon/Dev/multistore --accept-local` from the drifted worktree as a one-shot.
- AGS sidebar widget changes. Routing enforcement makes the existing single-file watch correct by construction.
- Auto-detecting main vs. master. `init-authority` keeps taking `--branch` explicitly.
