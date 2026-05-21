# P5.S2 Prune + Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `tasktool worktree prune` (with `--keep-branch`, `--force`, `--finalize`) and `tasktool worktree repair`, the three audit fields (`worktree_pruned_at`, `worktree_prune_pending`, `worktree_prune_pending_at`), and a post-merge prune step in the `finishing-a-development-branch` skill.

**Architecture:** Extend the existing `tools/tasktool/worktree.py` module with prune/repair primitives (guard checks, git plumbing, prune-from-inside detection). Add `cmd_worktree_prune` and `cmd_worktree_repair` in `tools/tasktool/commands.py` reusing the existing `_write_context`/`_load`/`_save`/`_find_item` helpers. Extend the `Slice` and `CrossCutting` dataclasses in `model.py` with optional audit fields; teach `serialize.py` to round-trip them; teach `validate.py` to type-check them. Wire the new subcommands into the `worktree` argparse group introduced by P5.S1.

**Tech Stack:** Python 3.11, argparse, dataclasses, subprocess for git plumbing, pytest with `tmp_path` for git fixtures.

**Spec:** `docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md` §5.3, §5.3.1, §5.3.2, §6 P5.S2.

**Tasktool row:** `P5.S2`. Plan path already reserved via `tasktool prepare`. Implementation starts with `tasktool start P5.S2` as the first execution step (see Task 0).

**Hard precondition: P5.S1 has shipped.** P5.S1 introduces every contract this plan depends on. **Before Task 0 the executor MUST run the preflight in Task -1 below.** If any preflight check fails, stop and notify the coordinator — do not attempt to recreate S1 work inline.

P5.S1 contracts this plan relies on:
- `Slice.worktree_path: str | None`, `Slice.worktree_branch: str | None`, `Slice.worktree_in_place: bool` on the model (also on `CrossCutting` for ad-hoc rows).
- `cmd_start` records both fields; `cmd_worktree_list`, `cmd_worktree_status`, `cmd_worktree_adopt` exist.
- The `tasktool worktree` argparse group exists in `cli.py` with `list`, `status`, `adopt` subparsers.
- `tools/tasktool/worktree.py` already contains `_git`, `worktree_roots`, `git_common_dir`, `find_authoritative_root`. We will add to it.
- `tasktool start --ad-hoc <slug>` allocates an `X<n>` cross-cutting row with `worktree_path` / `worktree_branch` recorded and `notes: "ad-hoc"`.
- `serialize.py`'s slice/cross dict already emits the P5.S1 `worktree_*` fields. Since the current `serialize.py` uses `asdict(p)` (see `tools/tasktool/serialize.py:11-23`), every dataclass field is emitted unconditionally. Reviewer F2 (round 1) flagged that adding new fields will therefore extend canonical bytes — that is expected and handled by Task 2's normalise step.

---

## File Structure

Files to create:
- `tools/tasktool/tests/test_worktree_prune.py` — all prune-path tests (guards, `--force`, `--keep-branch`, prune-from-inside, `--finalize` preconditions, recent-HEAD note, ad-hoc lifecycle, `--force` scope negatives).
- `tools/tasktool/tests/test_worktree_repair.py` — `repair` happy-path and refusal tests.

Files to modify:
- `tools/tasktool/model.py` — add `worktree_pruned_at`, `worktree_prune_pending`, `worktree_prune_pending_at` to `Slice` and `CrossCutting`.
- `tools/tasktool/serialize.py` — round-trip the new audit fields.
- `tools/tasktool/validate.py` — type/shape check the new fields.
- `tools/tasktool/worktree.py` — add `is_inside_worktree`, `branch_is_merged`, `working_tree_dirty`, `head_age_seconds`, `git_worktree_remove`, `git_branch_delete`, `git_worktree_add`, `branch_exists`, `path_is_registered_worktree`.
- `tools/tasktool/commands.py` — add `cmd_worktree_prune` and `cmd_worktree_repair`.
- `tools/tasktool/cli.py` — extend the `worktree` subparser group with `prune` (with `--keep-branch`, `--force`, `--finalize` mutually exclusive group) and `repair`.
- `tools/tasktool/schema_gen.py` — emit the new audit fields in the generated schema.
- `tools/tasktool/tests/test_schema_gen.py` — assert the new fields appear in the emitted schema.
- `tools/tasktool/tests/test_model.py` — round-trip the new fields.
- `tools/tasktool/tests/test_validate.py` — type-check failures for the new fields.
- `skills/finishing-a-development-branch/SKILL.md` — append the post-merge `tasktool worktree prune` step.

---

## Task -1: Preflight — confirm P5.S1 has shipped

**Files:** none (read-only checks).

- [ ] **Step 1: Confirm P5.S1 row is done and ratified**

Run: `tools/tasktool/tasktool show P5.S1`
Expected: `status: done` and `planning_status: ratified`.
If not: STOP. Notify the coordinator that S1 is not yet shipped; P5.S2 cannot proceed.

- [ ] **Step 2: Confirm P5.S2 is ratified**

Run: `tools/tasktool/tasktool show P5.S2`
Expected: `planning_status: ratified` and `depends_on: ["P5.S1"]`.
If not: STOP and ask the coordinator to ratify.

- [ ] **Step 3: Confirm the S1 CLI surface is present**

Run: `tools/tasktool/tasktool worktree --help`
Expected: `list`, `status`, `adopt` subcommands listed; exit 0.

Run: `tools/tasktool/tasktool start --help`
Expected: `--in-place`, `--adopt`, `--ad-hoc` flags listed.

If either help text is missing flags or subcommands, STOP. The plan's assumed S1 contracts are absent and Task 5+ will fail.

- [ ] **Step 4: Confirm baseline test suite is green on the current branch**

Run: `python -m pytest tools/tasktool/tests -q` and `tools/tasktool/tasktool validate --strict-format`
Expected: both exit 0. If not: STOP and notify the coordinator before starting S2 work.

---

## Task 0: Start the slice

**Files:** none (tasktool state only).

- [ ] **Step 1: Confirm row exists and is ratified**

Run: `tools/tasktool/tasktool show P5.S2`
Expected: row prints with `planning_status: ratified` and `depends_on: ["P5.S1"]`.

- [ ] **Step 2: Mark slice in_progress**

Run: `tools/tasktool/tasktool start P5.S2`
Expected: exit 0; status becomes `in_progress`.

- [ ] **Step 3: Run baseline tests**

Run: `python -m pytest tools/tasktool/tests -q`
Expected: PASS (treat any pre-existing failures as a blocker; do not proceed).

---

## Task 1: Add the three audit fields to the model

**Files:**
- Modify: `tools/tasktool/model.py` (the `Slice` dataclass around lines 35-51 and `CrossCutting` around lines 68-77).
- Modify: `tools/tasktool/tests/test_model.py`.

- [ ] **Step 1: Write the failing model round-trip test**

Add to `tools/tasktool/tests/test_model.py`:

```python
def test_slice_audit_fields_default_to_none_and_false():
    from tasktool.model import Slice
    s = Slice(id="S1", title="t", created="2026-05-21")
    assert s.worktree_pruned_at is None
    assert s.worktree_prune_pending is False
    assert s.worktree_prune_pending_at is None


def test_cross_audit_fields_default_to_none_and_false():
    from tasktool.model import CrossCutting
    c = CrossCutting(id="X1", title="t", created="2026-05-21")
    assert c.worktree_pruned_at is None
    assert c.worktree_prune_pending is False
    assert c.worktree_prune_pending_at is None
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tools/tasktool/tests/test_model.py -q -k audit`
Expected: FAIL — `AttributeError` on `worktree_pruned_at`.

- [ ] **Step 3: Add the fields**

In `tools/tasktool/model.py`, after the existing `worktree_*` fields added by P5.S1 on `Slice` (immediately before `tasks: list[Task]`), add:

```python
    worktree_pruned_at: str | None = None
    worktree_prune_pending: bool = False
    worktree_prune_pending_at: str | None = None
```

Repeat on `CrossCutting` (after the P5.S1 `worktree_*` fields, before `refs`/`notes`).

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tools/tasktool/tests/test_model.py -q -k audit`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/model.py tools/tasktool/tests/test_model.py
git commit -m "P5.S2: add worktree prune audit fields to model"
```

---

## Task 2: Round-trip the audit fields in serialize.py

**Files:**
- Modify: `tools/tasktool/serialize.py`.
- Modify: `tools/tasktool/tests/test_serialize.py`.

- [ ] **Step 1: Write the failing JSON round-trip test**

Add to `tools/tasktool/tests/test_serialize.py`:

```python
def test_serialize_audit_fields_round_trip(tmp_path):
    from tasktool.model import Project, Phase, Slice
    from tasktool.serialize import save_project, load_project
    p = Project(project="demo")
    ph = Phase(id="P5", title="t", created="2026-05-21")
    s = Slice(id="S2", title="t", created="2026-05-21",
              worktree_pruned_at="2026-05-22",
              worktree_prune_pending=True,
              worktree_prune_pending_at="2026-05-22")
    ph.slices.append(s)
    p.phases.append(ph)
    path = tmp_path / "tasklist.json"
    save_project(p, path)
    p2 = load_project(path)
    s2 = p2.phases[0].slices[0]
    assert s2.worktree_pruned_at == "2026-05-22"
    assert s2.worktree_prune_pending is True
    assert s2.worktree_prune_pending_at == "2026-05-22"
```

Plus a parallel test for `CrossCutting`.

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tools/tasktool/tests/test_serialize.py -q -k audit`
Expected: FAIL — fields missing from emitted JSON / dropped on load.

- [ ] **Step 3: Extend serialize.py load path**

The current serializer uses `asdict(p)` and emits *every* dataclass field unconditionally (`tools/tasktool/serialize.py:11-23`). Therefore the **emit path needs no edits** — once Task 1 adds the fields to the dataclasses, they appear in canonical output automatically.

The **load path (`from_dict`)** is keyword-based and must be taught the new keys. In `_slice` (lines 41-56) add three kwargs to the `Slice(...)` constructor call:

```python
            worktree_pruned_at=sd.get("worktree_pruned_at"),
            worktree_prune_pending=sd.get("worktree_prune_pending", False),
            worktree_prune_pending_at=sd.get("worktree_prune_pending_at"),
```

(If P5.S1 already added `worktree_path`/`worktree_branch`/`worktree_in_place` kwargs here, place the new three next to them.)

In `_cross` (lines 70-78) add the same three kwargs to the `CrossCutting(...)` constructor call.

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tools/tasktool/tests/test_serialize.py -q`
Expected: PASS.

- [ ] **Step 5: Normalise the existing tasklist**

Because `asdict` now emits the three new keys on every slice and every cross-cutting row, the on-disk `docs/tasklist.json` is no longer in canonical form. Re-canonicalise:

```bash
tools/tasktool/tasktool validate --normalise
tools/tasktool/tasktool validate --strict-format
```

Expected: first command rewrites `docs/tasklist.json` with the new default keys on every row; second command exits 0.

Inspect the diff: every slice should now contain `"worktree_pruned_at": null`, `"worktree_prune_pending": false`, `"worktree_prune_pending_at": null`. Every cross-cutting row likewise. No semantic changes.

- [ ] **Step 6: Commit (includes the tasklist re-normalisation)**

```bash
git add tools/tasktool/serialize.py tools/tasktool/tests/test_serialize.py docs/tasklist.json
git commit -m "P5.S2: round-trip worktree prune audit fields"
```

---

## Task 3: Validate the new audit fields

**Files:**
- Modify: `tools/tasktool/validate.py` (extend `_check_slice` around lines 77-95 and `_check_cross` around lines 110-115).
- Modify: `tools/tasktool/tests/test_validate.py`.

- [ ] **Step 1: Write the failing validation tests**

Add to `tools/tasktool/tests/test_validate.py`:

```python
def test_validate_rejects_pending_without_at_timestamp():
    from tasktool.model import Project, Phase, Slice
    from tasktool.validate import validate_project, ValidationError
    p = Project(project="d")
    ph = Phase(id="P1", title="t", created="2026-05-21")
    s = Slice(id="S1", title="t", created="2026-05-21",
              worktree_prune_pending=True,
              worktree_prune_pending_at=None)
    ph.slices.append(s)
    p.phases.append(ph)
    import pytest
    with pytest.raises(ValidationError, match="worktree_prune_pending"):
        validate_project(p)


def test_validate_rejects_pending_at_without_pending_flag():
    from tasktool.model import Project, Phase, Slice
    from tasktool.validate import validate_project, ValidationError
    p = Project(project="d")
    ph = Phase(id="P1", title="t", created="2026-05-21")
    s = Slice(id="S1", title="t", created="2026-05-21",
              worktree_prune_pending=False,
              worktree_prune_pending_at="2026-05-22")
    ph.slices.append(s)
    p.phases.append(ph)
    import pytest
    with pytest.raises(ValidationError, match="worktree_prune_pending_at"):
        validate_project(p)


def test_validate_accepts_worktree_pruned_at_alone():
    from tasktool.model import Project, Phase, Slice
    from tasktool.validate import validate_project
    p = Project(project="d")
    ph = Phase(id="P1", title="t", created="2026-05-21")
    s = Slice(id="S1", title="t", created="2026-05-21",
              worktree_pruned_at="2026-05-22")
    ph.slices.append(s)
    p.phases.append(ph)
    validate_project(p)  # no raise


def test_validate_rejects_bad_pruned_at_date():
    from tasktool.model import Project, Phase, Slice
    from tasktool.validate import validate_project, ValidationError
    p = Project(project="d")
    ph = Phase(id="P1", title="t", created="2026-05-21")
    s = Slice(id="S1", title="t", created="2026-05-21",
              worktree_pruned_at="not-a-date")
    ph.slices.append(s)
    p.phases.append(ph)
    import pytest
    with pytest.raises(ValidationError):
        validate_project(p)
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tools/tasktool/tests/test_validate.py -q -k "pending or pruned_at"`
Expected: FAIL — `worktree_prune_pending`/`worktree_pruned_at` not enforced.

- [ ] **Step 3: Add validation in validate.py**

In `tools/tasktool/validate.py`, extend `_check_slice` (after the existing date checks, after line 89):

```python
    _check_date(s.worktree_pruned_at, scope, "worktree_pruned_at")
    _check_date(s.worktree_prune_pending_at, scope, "worktree_prune_pending_at")
    if s.worktree_prune_pending and s.worktree_prune_pending_at is None:
        raise ValidationError(
            f"{scope}: worktree_prune_pending=True requires worktree_prune_pending_at"
        )
    if (not s.worktree_prune_pending) and s.worktree_prune_pending_at is not None:
        raise ValidationError(
            f"{scope}: worktree_prune_pending_at requires worktree_prune_pending=True"
        )
```

Add the identical block to `_check_cross` (after line 115).

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tools/tasktool/tests/test_validate.py -q`
Expected: PASS.

- [ ] **Step 5: Update schema generator**

Open `tools/tasktool/schema_gen.py`. Find the slice property block (the one P5.S1 extended with `worktree_path`/`worktree_branch`). Add:

```python
        "worktree_pruned_at": {"type": ["string", "null"]},
        "worktree_prune_pending": {"type": "boolean"},
        "worktree_prune_pending_at": {"type": ["string", "null"]},
```

Repeat for cross-cutting properties.

- [ ] **Step 6: Update schema-gen test**

Add to `tools/tasktool/tests/test_schema_gen.py`:

```python
def test_schema_includes_prune_audit_fields():
    from tasktool import schema_gen
    schema = schema_gen.build_schema()
    slice_props = schema["$defs"]["slice"]["properties"]
    assert "worktree_pruned_at" in slice_props
    assert "worktree_prune_pending" in slice_props
    assert "worktree_prune_pending_at" in slice_props
    cross_props = schema["$defs"]["cross"]["properties"]
    assert "worktree_pruned_at" in cross_props
    assert "worktree_prune_pending" in cross_props
    assert "worktree_prune_pending_at" in cross_props
```

(If the existing schema-gen test file uses different paths into the schema dict, mirror those.)

- [ ] **Step 7: Run all validate/schema tests**

Run: `python -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_schema_gen.py -q`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add tools/tasktool/validate.py tools/tasktool/schema_gen.py tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_schema_gen.py
git commit -m "P5.S2: validate worktree prune audit fields and emit in schema"
```

---

## Task 4: Add git plumbing helpers in worktree.py

**Files:**
- Modify: `tools/tasktool/worktree.py`.
- Create: `tools/tasktool/tests/test_worktree_prune.py` (only the plumbing-helper unit tests in this task; CLI tests come later).

- [ ] **Step 1: Write failing tests for the helpers**

Create `tools/tasktool/tests/test_worktree_prune.py` starting with a small fixture builder. Place at top of file:

```python
from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pytest


def _run(cwd: Path, *args: str) -> str:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True).stdout


def _init_repo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    _run(root, "git", "init", "-q", "-b", "main")
    _run(root, "git", "config", "user.email", "t@example.com")
    _run(root, "git", "config", "user.name", "t")
    (root / "README").write_text("init\n")
    _run(root, "git", "add", "README")
    _run(root, "git", "commit", "-q", "-m", "init")
    return root


def _add_worktree(root: Path, branch: str, path: Path) -> Path:
    _run(root, "git", "worktree", "add", "-b", branch, str(path))
    return path
```

Then add helper tests:

```python
def test_is_inside_worktree_true(tmp_path):
    from tasktool.worktree import is_inside_worktree
    root = _init_repo(tmp_path / "r")
    wt = _add_worktree(root, "feat", tmp_path / "r" / ".worktrees" / "wt")
    assert is_inside_worktree(wt) is True
    assert is_inside_worktree(root) is False


def test_working_tree_dirty_detects_uncommitted_and_untracked(tmp_path):
    from tasktool.worktree import working_tree_dirty
    root = _init_repo(tmp_path / "r")
    assert working_tree_dirty(root) == (False, [])
    (root / "new.txt").write_text("x")
    dirty, files = working_tree_dirty(root)
    assert dirty is True
    assert "new.txt" in files


def test_working_tree_dirty_flags_stashes_attributable_to_worktree(tmp_path):
    """Spec §5.3: refuse 'stash entries attributable to the worktree'.

    Stashes in git are global to the repository; we cannot attribute them to a
    specific linked worktree, but `git stash list` records the BRANCH at the
    time of stash. A stash made on a different branch is NOT attributable to
    this worktree and must NOT be flagged.
    """
    from tasktool.worktree import working_tree_dirty
    root = _init_repo(tmp_path / "r")
    # Create another branch and stash on it.
    _run(root, "git", "checkout", "-q", "-b", "other")
    (root / "scratch").write_text("x")
    _run(root, "git", "add", "scratch")
    _run(root, "git", "stash", "push", "-u", "-m", "unrelated")
    # Back to main; this worktree's branch is now `main`. The stash above
    # belongs to `other`, not to us, and should NOT be flagged.
    _run(root, "git", "checkout", "-q", "main")
    dirty, files = working_tree_dirty(root)
    assert dirty is False, f"unrelated stash flagged dirty: {files}"


def test_working_tree_dirty_flags_own_branch_stash(tmp_path):
    from tasktool.worktree import working_tree_dirty
    root = _init_repo(tmp_path / "r")
    (root / "scratch").write_text("x")
    _run(root, "git", "add", "scratch")
    _run(root, "git", "stash", "push", "-u", "-m", "ours")
    dirty, files = working_tree_dirty(root)
    assert dirty is True
    assert any("stash" in f.lower() for f in files)


def test_branch_is_merged(tmp_path):
    from tasktool.worktree import branch_is_merged
    root = _init_repo(tmp_path / "r")
    wt = _add_worktree(root, "feat", tmp_path / "r" / ".worktrees" / "wt")
    (wt / "f").write_text("x")
    _run(wt, "git", "add", "f")
    _run(wt, "git", "commit", "-q", "-m", "f")
    assert branch_is_merged(root, branch="feat", into="main") is False
    _run(root, "git", "merge", "--no-ff", "-q", "-m", "m", "feat")
    assert branch_is_merged(root, branch="feat", into="main") is True


def test_head_age_seconds(tmp_path):
    from tasktool.worktree import head_age_seconds
    root = _init_repo(tmp_path / "r")
    age = head_age_seconds(root)
    assert age >= 0
    assert age < 60  # commit was just made


def test_path_is_registered_worktree(tmp_path):
    from tasktool.worktree import path_is_registered_worktree
    root = _init_repo(tmp_path / "r")
    wt = _add_worktree(root, "feat", tmp_path / "r" / ".worktrees" / "wt")
    assert path_is_registered_worktree(root, wt) is True
    assert path_is_registered_worktree(root, tmp_path / "nope") is False


def test_branch_exists(tmp_path):
    from tasktool.worktree import branch_exists
    root = _init_repo(tmp_path / "r")
    assert branch_exists(root, "main") is True
    assert branch_exists(root, "nope") is False
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tools/tasktool/tests/test_worktree_prune.py -q`
Expected: FAIL — `ImportError` on each helper.

- [ ] **Step 3: Implement helpers in worktree.py**

Append to `tools/tasktool/worktree.py`:

```python
def is_inside_worktree(path: Path) -> bool:
    """True iff `path` lies inside a linked (non-primary) git worktree.

    Implementation: `git rev-parse --git-dir` vs `--git-common-dir`.
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
```

The `time` and `subprocess` imports already exist at top of the file (verify).

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tools/tasktool/tests/test_worktree_prune.py -q`
Expected: all six helper tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/worktree.py tools/tasktool/tests/test_worktree_prune.py
git commit -m "P5.S2: add prune/repair git plumbing helpers"
```

---

## Task 5: Implement `cmd_worktree_prune` — basic path with all three guards

**Files:**
- Modify: `tools/tasktool/commands.py`.
- Modify: `tools/tasktool/tests/test_worktree_prune.py`.
- Modify: `tools/tasktool/cli.py`.

- [ ] **Step 1: Write CLI integration tests for the three guards**

Add to `tools/tasktool/tests/test_worktree_prune.py`. Use the existing CLI invocation helper pattern from `test_cli_integration.py` (subprocess against `tools/tasktool/tasktool`). Add a fixture that builds a project with one in-progress slice whose worktree is registered:

```python
TASKTOOL = Path(__file__).resolve().parents[1] / "tasktool"


def _tasktool(repo: Path, *args: str, check: bool = True):
    return subprocess.run(
        [str(TASKTOOL), "--project-root", str(repo), *args],
        text=True, capture_output=True, check=check,
    )


@pytest.fixture
def project_with_worktree(tmp_path):
    """Build a project with phase P1, slice S1 in_progress, branch merged, clean."""
    repo = _init_repo(tmp_path / "proj")
    (repo / "docs").mkdir()
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    _tasktool(repo, "create", "slice", "P1", "--title", "First slice")
    # Simulate P5.S1's start: create a linked worktree and record fields.
    wt_path = repo / ".worktrees" / "worktree-p1-s1-first-slice"
    _run(repo, "git", "worktree", "add", "-b",
         "worktree-p1-s1-first-slice", str(wt_path))
    _tasktool(repo, "start", "P1.S1")
    # P5.S1 should have recorded fields; if test environment differs, set manually:
    _tasktool(repo, "worktree", "adopt", "P1.S1", str(wt_path))
    return repo, wt_path


def test_prune_refuses_when_slice_in_progress(project_with_worktree):
    repo, _wt = project_with_worktree
    res = _tasktool(repo, "worktree", "prune", "P1.S1", check=False)
    assert res.returncode != 0
    assert "slice" in res.stderr.lower()
    assert "done" in res.stderr.lower() or "in_progress" in res.stderr.lower()


def test_prune_refuses_when_branch_unmerged(project_with_worktree):
    repo, wt = project_with_worktree
    # Close the slice (manually skip review gate for the test).
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    # Branch is NOT merged into main yet.
    res = _tasktool(repo, "worktree", "prune", "P1.S1", check=False)
    assert res.returncode != 0
    assert "merged" in res.stderr.lower()


def test_prune_refuses_with_dirty_tracked_file(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    # Merge the branch.
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    # Make tree dirty.
    (wt / "dirty.txt").write_text("x")
    res = _tasktool(repo, "worktree", "prune", "P1.S1", check=False)
    assert res.returncode != 0
    assert "clean" in res.stderr.lower() or "dirty" in res.stderr.lower()
    assert "dirty.txt" in res.stderr


def test_prune_refuses_with_untracked_file(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    (wt / "scratch.tmp").write_text("x")
    res = _tasktool(repo, "worktree", "prune", "P1.S1", check=False)
    assert res.returncode != 0
    assert "scratch.tmp" in res.stderr


def test_prune_refuses_with_stash_entry(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    (wt / "x").write_text("x")
    _run(wt, "git", "add", "x")
    _run(wt, "git", "stash", "push", "-u", "-m", "s")
    res = _tasktool(repo, "worktree", "prune", "P1.S1", check=False)
    assert res.returncode != 0
    assert "stash" in res.stderr.lower()


def test_prune_in_place_slice_is_noop_but_records_audit(tmp_path):
    """Spec §5.3.1: prune on an --in-place slice is a no-op on disk but records
    worktree_pruned_at.
    """
    repo = _init_repo(tmp_path / "p")
    (repo / "docs").mkdir()
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    _tasktool(repo, "create", "slice", "P1", "--title", "Planning slice")
    _tasktool(repo, "start", "P1.S1", "--in-place")
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    res = _tasktool(repo, "worktree", "prune", "P1.S1")
    assert res.returncode == 0
    show = _tasktool(repo, "show", "P1.S1").stdout
    assert "worktree_pruned_at" in show
    # No disk side-effect: no .worktrees dir created.
    assert not (repo / ".worktrees").exists() or not any((repo / ".worktrees").iterdir())


def test_prune_happy_path(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    res = _tasktool(repo, "worktree", "prune", "P1.S1")
    assert res.returncode == 0
    # Worktree directory removed, branch removed.
    assert not wt.exists()
    from tasktool.worktree import branch_exists
    assert branch_exists(repo, "worktree-p1-s1-first-slice") is False
    # Audit fields recorded.
    show = _tasktool(repo, "show", "P1.S1").stdout
    assert "worktree_pruned_at" in show
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tools/tasktool/tests/test_worktree_prune.py -q -k "prune"`
Expected: FAIL — `worktree prune` subcommand does not exist.

- [ ] **Step 3: Add the `prune` argparse subparser in cli.py**

In `tools/tasktool/cli.py`, locate the `worktree` subparser group P5.S1 added (search for `p_worktree = sub.add_parser("worktree")`). Add:

```python
    p_wt_prune = wt_sub.add_parser("prune")
    p_wt_prune.add_argument("id")
    prune_excl = p_wt_prune.add_mutually_exclusive_group()
    prune_excl.add_argument("--keep-branch", action="store_true")
    prune_excl.add_argument("--force", action="store_true")
    prune_excl.add_argument("--finalize", action="store_true")
```

In the dispatch block at the bottom of cli.py (next to other `worktree` dispatch), add:

```python
        elif args.worktree_cmd == "prune":
            commands.cmd_worktree_prune(
                repo_root=root,
                id=args.id,
                keep_branch=args.keep_branch,
                force=args.force,
                finalize=args.finalize,
            )
```

- [ ] **Step 4: Implement `cmd_worktree_prune` in commands.py**

Add at the end of `tools/tasktool/commands.py`:

```python
def cmd_worktree_prune(
    *, repo_root: Path, id: str,
    keep_branch: bool = False, force: bool = False, finalize: bool = False,
) -> None:
    from tasktool import worktree as wt
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)

        if finalize:
            _worktree_finalize(write_root, item, qid)
            _save(write_root, p)
            return

        # In-place slices: no worktree to prune; record timestamp and exit.
        if getattr(item, "worktree_in_place", False):
            item.worktree_pruned_at = _today()
            _save(write_root, p)
            print(f"{qid}: --in-place slice; no worktree to remove.")
            return

        # Already pruned (no path on file)?
        path_str = getattr(item, "worktree_path", None)
        branch = getattr(item, "worktree_branch", None)
        if not path_str or not branch:
            raise CommandError(
                f"{qid}: no recorded worktree to prune "
                f"(worktree_path={path_str!r}, worktree_branch={branch!r})"
            )
        wt_path = (write_root / path_str).resolve()

        # Guard 1: slice status is done (unless --force).
        if not force:
            if getattr(item, "status", None) != Status.DONE:
                raise CommandError(
                    f"{qid}: slice status is {item.status.value!r}; prune requires "
                    f"'done' (run `tasktool close {qid}` first, or pass --force)"
                )

            # Guard 2: branch merged into authoritative parent.
            parent = _authoritative_parent_branch(write_root, qid)
            if not wt.branch_is_merged(write_root, branch=branch, into=parent):
                raise CommandError(
                    f"{qid}: branch {branch!r} is not merged into {parent!r}; "
                    f"merge first or pass --force"
                )

            # Guard 3: clean worktree.
            if wt_path.exists():
                dirty, items = wt.working_tree_dirty(wt_path)
                if dirty:
                    pretty = ", ".join(items[:5]) + (" ..." if len(items) > 5 else "")
                    raise CommandError(
                        f"{qid}: worktree at {wt_path} is not clean: {pretty}"
                    )

        # Recent-HEAD informational note (never refuses).
        if wt_path.exists():
            try:
                age = wt.head_age_seconds(wt_path)
                if age < 60:
                    print(
                        f"note: {qid} worktree HEAD moved {age:.0f}s ago; "
                        f"proceeding with prune",
                        file=sys.stderr,
                    )
            except Exception:
                pass

        # Prune-from-inside detection.
        cwd = Path.cwd()
        if wt.is_inside_worktree(cwd) and _path_under(cwd, wt_path):
            item.worktree_prune_pending = True
            item.worktree_prune_pending_at = _today()
            _save(write_root, p)
            authoritative = write_root
            print(
                f"{qid}: prune deferred (running inside the worktree being removed).\n"
                f"Run this from outside:\n"
                f"  cd {authoritative} && git worktree remove {wt_path} && "
                f"tasktool worktree prune {qid} --finalize"
            )
            return

        # Destructive step.
        if wt_path.exists():
            wt.git_worktree_remove(write_root, wt_path, force=force)
        if not keep_branch and wt.branch_exists(write_root, branch):
            wt.git_branch_delete(write_root, branch, force=force)

        item.worktree_path = None
        item.worktree_branch = None
        item.worktree_pruned_at = _today()
        # Clear any stale pending marker.
        item.worktree_prune_pending = False
        item.worktree_prune_pending_at = None
        _save(write_root, p)
        print(f"{qid}: worktree pruned (path={wt_path}, branch={branch})")


def _worktree_finalize(write_root: Path, item, qid: str) -> None:
    from tasktool import worktree as wt
    if not getattr(item, "worktree_prune_pending", False):
        raise CommandError(
            f"{qid}: no pending prune to finalize; "
            f"run `tasktool worktree prune {qid}` first."
        )
    path_str = getattr(item, "worktree_path", None)
    if not path_str:
        raise CommandError(f"{qid}: pending prune missing worktree_path; cannot finalize")
    wt_path = (write_root / path_str).resolve()
    if wt.path_is_registered_worktree(write_root, wt_path):
        raise CommandError(
            f"{qid}: worktree at {wt_path} is still registered in `git worktree list`; "
            f"run `git worktree remove {wt_path}` before --finalize"
        )
    if wt_path.exists():
        raise CommandError(
            f"{qid}: directory still present at {wt_path}; "
            f"remove it before --finalize"
        )
    item.worktree_path = None
    item.worktree_branch = None
    item.worktree_prune_pending = False
    item.worktree_prune_pending_at = None
    item.worktree_pruned_at = _today()
    print(f"{qid}: finalize complete; audit fields recorded.")


def _path_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _authoritative_parent_branch(write_root: Path, qid: str) -> str:
    """Return the merge-target branch for a slice's worktree.

    Read from `.tasktool/config.json` (`tasklist.authoritative_branch`),
    matching the existing `TasklistConfig` surface in `tools/tasktool/config.py`.
    Falls back to "main" when no config file is present (matches
    `TasklistConfig`'s default).
    """
    from tasktool.config import load_config
    return load_config(write_root).tasklist.authoritative_branch
```

Also add `import sys` at the top of commands.py if not present.

- [ ] **Step 5: Run to verify pass**

Run: `python -m pytest tools/tasktool/tests/test_worktree_prune.py -q -k "prune and not finalize and not force and not keep_branch and not recent and not inside and not ad_hoc"`
Expected: PASS for the six tests written in Step 1.

- [ ] **Step 6: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/tests/test_worktree_prune.py
git commit -m "P5.S2: implement worktree prune with three guards"
```

---

## Task 6: `--keep-branch` flag

**Files:** `tools/tasktool/tests/test_worktree_prune.py`.

- [ ] **Step 1: Write the failing test**

```python
def test_prune_keep_branch_leaves_branch(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--keep-branch")
    assert res.returncode == 0
    assert not wt.exists()
    from tasktool.worktree import branch_exists
    assert branch_exists(repo, "worktree-p1-s1-first-slice") is True
```

- [ ] **Step 2: Run**

`python -m pytest tools/tasktool/tests/test_worktree_prune.py -q -k keep_branch`
Expected: PASS (the implementation in Task 5 already honours `--keep-branch`).

- [ ] **Step 3: Commit**

```bash
git add tools/tasktool/tests/test_worktree_prune.py
git commit -m "P5.S2: test --keep-branch leaves branch reachable"
```

---

## Task 7: `--force` flag scope (positives + scope negatives)

**Files:** `tools/tasktool/tests/test_worktree_prune.py`.

- [ ] **Step 1: Write tests covering each guard override and the scope guarantees**

```python
def test_force_overrides_in_progress_guard(project_with_worktree):
    repo, wt = project_with_worktree
    # Slice still in_progress, no merge.
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--force")
    assert res.returncode == 0
    assert not wt.exists()


def test_force_overrides_unmerged_branch_guard(tmp_path):
    # Build separate project: slice closed but branch never merged.
    repo, wt = _project_with_closed_unmerged(tmp_path)  # helper below
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--force")
    assert res.returncode == 0


def test_force_overrides_dirty_tree_guard(project_with_worktree):
    repo, wt = project_with_worktree
    (wt / "dirty.txt").write_text("x")
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--force")
    assert res.returncode == 0
    assert not wt.exists()


def test_force_does_not_affect_close_review_gate(project_with_worktree):
    """--force on `prune` must NOT bypass the close review gate.

    The close path is unchanged; --force is scoped to prune guards only.
    """
    repo, _wt = project_with_worktree
    # Attempt to close without --skip-review-gate; --force is not even a
    # close flag, but we re-confirm by checking close's behaviour.
    res = _tasktool(repo, "close", "P1.S1", check=False)
    assert res.returncode != 0
    assert "review" in res.stderr.lower() or "reviewer" in res.stderr.lower()


def test_force_does_not_flip_slice_status(project_with_worktree):
    """After `prune --force` on an in_progress slice, the slice MUST remain
    in_progress. --force is destructive only for the worktree, not for
    lifecycle state."""
    repo, _wt = project_with_worktree
    _tasktool(repo, "worktree", "prune", "P1.S1", "--force")
    show = _tasktool(repo, "show", "P1.S1").stdout
    assert "in_progress" in show
    assert "status: done" not in show.lower()


def test_force_does_not_clear_depends_on(tmp_path):
    """--force prune of one slice must not touch dependent slices' depends_on."""
    repo = _init_repo(tmp_path / "p")
    (repo / "docs").mkdir()
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    _tasktool(repo, "create", "slice", "P1", "--title", "first")
    _tasktool(repo, "create", "slice", "P1", "--title", "second")
    _tasktool(repo, "deps", "P1.S2", "--add", "P1.S1")
    # Build a worktree for S1 manually.
    wt_path = repo / ".worktrees" / "w"
    _run(repo, "git", "worktree", "add", "-b", "w", str(wt_path))
    _tasktool(repo, "start", "P1.S1")
    _tasktool(repo, "worktree", "adopt", "P1.S1", str(wt_path))
    _tasktool(repo, "worktree", "prune", "P1.S1", "--force")
    show = _tasktool(repo, "show", "P1.S2").stdout
    assert "P1.S1" in show  # dependency edge intact
```

Add the helper:

```python
def _project_with_closed_unmerged(tmp_path):
    repo = _init_repo(tmp_path / "p2")
    (repo / "docs").mkdir()
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    _tasktool(repo, "create", "slice", "P1", "--title", "First slice")
    wt_path = repo / ".worktrees" / "worktree-p1-s1-first-slice"
    _run(repo, "git", "worktree", "add", "-b",
         "worktree-p1-s1-first-slice", str(wt_path))
    _tasktool(repo, "start", "P1.S1")
    _tasktool(repo, "worktree", "adopt", "P1.S1", str(wt_path))
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    return repo, wt_path
```

- [ ] **Step 2: Run**

`python -m pytest tools/tasktool/tests/test_worktree_prune.py -q -k force`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tools/tasktool/tests/test_worktree_prune.py
git commit -m "P5.S2: test --force scoping (prune guards only)"
```

---

## Task 8: Prune-from-inside detection + `--finalize` preconditions

**Files:** `tools/tasktool/tests/test_worktree_prune.py`.

- [ ] **Step 1: Write tests**

```python
def test_prune_from_inside_sets_pending_marker_and_skips_remove(project_with_worktree, monkeypatch):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    # Invoke prune with cwd inside the doomed worktree.
    res = subprocess.run(
        [str(TASKTOOL), "--project-root", str(repo),
         "worktree", "prune", "P1.S1"],
        cwd=wt, text=True, capture_output=True, check=False,
    )
    assert res.returncode == 0
    # Pending marker set, fields preserved.
    show = _tasktool(repo, "show", "P1.S1").stdout
    assert "worktree_prune_pending" in show
    # Worktree still present.
    assert wt.exists()
    # Exact follow-up line printed.
    assert "git worktree remove" in res.stdout
    assert "tasktool worktree prune P1.S1 --finalize" in res.stdout


def test_finalize_refuses_when_no_pending(project_with_worktree):
    repo, _wt = project_with_worktree
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--finalize", check=False)
    assert res.returncode != 0
    assert "no pending prune" in res.stderr.lower()


def test_finalize_refuses_when_path_still_registered(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    # Trigger prune-from-inside to set pending marker.
    subprocess.run(
        [str(TASKTOOL), "--project-root", str(repo),
         "worktree", "prune", "P1.S1"],
        cwd=wt, text=True, capture_output=True, check=True,
    )
    # Worktree still registered. --finalize must refuse.
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--finalize", check=False)
    assert res.returncode != 0
    assert "still registered" in res.stderr.lower() or "git worktree list" in res.stderr.lower()


def test_finalize_refuses_when_directory_still_present(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    subprocess.run(
        [str(TASKTOOL), "--project-root", str(repo),
         "worktree", "prune", "P1.S1"],
        cwd=wt, text=True, capture_output=True, check=True,
    )
    # Unregister via git but leave the directory present.
    _run(repo, "git", "worktree", "remove", "--force", str(wt))
    # Recreate the directory as a plain dir to simulate leftover state.
    wt.mkdir(parents=True, exist_ok=True)
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--finalize", check=False)
    assert res.returncode != 0
    assert "directory still present" in res.stderr.lower()


def test_finalize_succeeds_when_all_preconditions_met(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    subprocess.run(
        [str(TASKTOOL), "--project-root", str(repo),
         "worktree", "prune", "P1.S1"],
        cwd=wt, text=True, capture_output=True, check=True,
    )
    # Caller performs the destructive step out-of-band.
    _run(repo, "git", "worktree", "remove", str(wt))
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--finalize")
    assert res.returncode == 0
    show = _tasktool(repo, "show", "P1.S1").stdout
    assert "worktree_pruned_at" in show
    assert "worktree_prune_pending" not in show or "false" in show.lower()
```

- [ ] **Step 2: Run**

`python -m pytest tools/tasktool/tests/test_worktree_prune.py -q -k "inside or finalize"`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tools/tasktool/tests/test_worktree_prune.py
git commit -m "P5.S2: test prune-from-inside and --finalize preconditions"
```

---

## Task 9: Recent-HEAD informational note

**Files:** `tools/tasktool/tests/test_worktree_prune.py`.

- [ ] **Step 1: Write the test**

```python
def test_prune_emits_recent_head_note_but_succeeds(project_with_worktree):
    repo, wt = project_with_worktree
    _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
         "worktree-p1-s1-first-slice")
    # Create a fresh commit in the worktree before merging again to advance HEAD;
    # since branch is already merged into main as a separate ref, refresh the HEAD
    # timestamp on the worktree by amending.
    _run(wt, "git", "commit", "--allow-empty", "-q",
         "--amend", "--no-edit", "--date=now")
    res = _tasktool(repo, "worktree", "prune", "P1.S1", "--force",
                    check=False)
    assert res.returncode == 0
    assert "HEAD moved" in res.stderr
```

Note: the test uses `--force` because amending HEAD detaches the merged-into-main link; we want to verify the *note* fires, not the merged guard. The recent-HEAD note path runs whether or not guards pass.

- [ ] **Step 2: Run**

`python -m pytest tools/tasktool/tests/test_worktree_prune.py -q -k recent_head`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tools/tasktool/tests/test_worktree_prune.py
git commit -m "P5.S2: recent-HEAD informational note (non-blocking)"
```

---

## Task 10: Ad-hoc lifecycle end-to-end (foot-gun coverage)

**Files:** `tools/tasktool/tests/test_worktree_prune.py`.

- [ ] **Step 1: Write the end-to-end test, including the close-without-`--no-archive` foot-gun**

```python
def test_ad_hoc_lifecycle_close_without_no_archive_breaks_prune(tmp_path):
    """Spec §5.3: default `close` on a cross-cutting row auto-archives, which
    destroys worktree fields before prune can find them. This is the foot-gun
    `start --ad-hoc` requires `--no-archive` to avoid.
    """
    repo = _init_repo(tmp_path / "p")
    (repo / "docs").mkdir()
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "start", "--ad-hoc", "explore")
    # Discover the allocated ID by reading tasktool list.
    listing = _tasktool(repo, "list", "--kind", "cross").stdout
    xid = _extract_xid(listing, title_contains="Ad-hoc: explore")
    assert xid is not None
    # Foot-gun: close without --no-archive auto-archives.
    _tasktool(repo, "close", xid)
    # Now prune cannot find the row.
    res = _tasktool(repo, "worktree", "prune", xid, check=False)
    assert res.returncode != 0


def test_ad_hoc_lifecycle_full_flow_with_no_archive(tmp_path):
    repo = _init_repo(tmp_path / "p")
    (repo / "docs").mkdir()
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "start", "--ad-hoc", "hotfix")
    listing = _tasktool(repo, "list", "--kind", "cross").stdout
    xid = _extract_xid(listing, title_contains="Ad-hoc: hotfix")
    assert xid is not None
    # Recorded worktree path.
    show = _tasktool(repo, "show", xid).stdout
    assert "worktree_path" in show
    # Step 1: close with --no-archive.
    _tasktool(repo, "close", xid, "--no-archive")
    # Step 2: prune (no merge required for ad-hoc by spec? — spec defers to
    # standard three-guard prune. For this test we force-prune because the
    # ad-hoc branch is not merged into main).
    _tasktool(repo, "worktree", "prune", xid, "--force")
    # Step 3: archive-cross.
    _tasktool(repo, "archive-cross", xid)
    # archive-cross moves the row from `cross_cutting` to `archived_cross_cutting`.
    # `tasktool list --kind cross` lists active cross rows; the archived row will
    # NOT appear there. Verify the archive by reading tasklist.json directly.
    import json
    data = json.loads((repo / "docs" / "tasklist.json").read_text())
    archived_ids = [a["id"] for a in data.get("archived_cross_cutting", [])]
    assert xid in archived_ids


def _extract_xid(listing: str, *, title_contains: str) -> str | None:
    import re
    for line in listing.splitlines():
        if title_contains in line:
            m = re.search(r"\b(X\d+)\b", line)
            if m:
                return m.group(1)
    return None
```

- [ ] **Step 2: Run**

`python -m pytest tools/tasktool/tests/test_worktree_prune.py -q -k ad_hoc`
Expected: PASS.

(Note: this test depends on P5.S1's `start --ad-hoc`. If that helper is not yet wired the test will fail at that step — surface the gap to the coordinator rather than papering over it.)

- [ ] **Step 3: Commit**

```bash
git add tools/tasktool/tests/test_worktree_prune.py
git commit -m "P5.S2: ad-hoc lifecycle end-to-end including close-without-no-archive foot-gun"
```

---

## Task 11: Implement `cmd_worktree_repair`

**Files:**
- Modify: `tools/tasktool/commands.py`.
- Modify: `tools/tasktool/cli.py`.
- Create: `tools/tasktool/tests/test_worktree_repair.py`.

- [ ] **Step 1: Write failing tests**

Create `tools/tasktool/tests/test_worktree_repair.py`:

```python
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tasktool.tests.test_worktree_prune import (
    _init_repo, _run, _tasktool, TASKTOOL,
)


@pytest.fixture
def project_with_missing_worktree(tmp_path):
    repo = _init_repo(tmp_path / "p")
    (repo / "docs").mkdir()
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    _tasktool(repo, "create", "slice", "P1", "--title", "Slice 1")
    wt_path = repo / ".worktrees" / "worktree-p1-s1-slice-1"
    _run(repo, "git", "worktree", "add", "-b",
         "worktree-p1-s1-slice-1", str(wt_path))
    _tasktool(repo, "start", "P1.S1")
    _tasktool(repo, "worktree", "adopt", "P1.S1", str(wt_path))
    # Remove the worktree directory and unregister, but keep the branch.
    _run(repo, "git", "worktree", "remove", "--force", str(wt_path))
    return repo, wt_path


def test_repair_recreates_worktree_when_branch_exists(project_with_missing_worktree):
    repo, wt_path = project_with_missing_worktree
    from tasktool.worktree import branch_exists
    assert branch_exists(repo, "worktree-p1-s1-slice-1") is True
    res = _tasktool(repo, "worktree", "repair", "P1.S1")
    assert res.returncode == 0
    assert wt_path.exists()
    assert (wt_path / ".git").exists()


def test_repair_refuses_when_branch_missing(project_with_missing_worktree):
    repo, _wt = project_with_missing_worktree
    _run(repo, "git", "branch", "-D", "worktree-p1-s1-slice-1")
    res = _tasktool(repo, "worktree", "repair", "P1.S1", check=False)
    assert res.returncode != 0
    assert "branch" in res.stderr.lower() and "missing" in res.stderr.lower()


def test_repair_refuses_when_no_recorded_fields(tmp_path):
    repo = _init_repo(tmp_path / "p")
    (repo / "docs").mkdir()
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    _tasktool(repo, "create", "slice", "P1", "--title", "Slice 1")
    res = _tasktool(repo, "worktree", "repair", "P1.S1", check=False)
    assert res.returncode != 0


def test_repair_no_op_when_worktree_already_live(tmp_path):
    repo = _init_repo(tmp_path / "p")
    (repo / "docs").mkdir()
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    _tasktool(repo, "create", "slice", "P1", "--title", "Slice 1")
    wt = repo / ".worktrees" / "worktree-p1-s1-slice-1"
    _run(repo, "git", "worktree", "add", "-b",
         "worktree-p1-s1-slice-1", str(wt))
    _tasktool(repo, "start", "P1.S1")
    _tasktool(repo, "worktree", "adopt", "P1.S1", str(wt))
    res = _tasktool(repo, "worktree", "repair", "P1.S1")
    assert res.returncode == 0
    assert wt.exists()
```

- [ ] **Step 2: Run to verify failure**

`python -m pytest tools/tasktool/tests/test_worktree_repair.py -q`
Expected: FAIL — `worktree repair` subcommand does not exist.

- [ ] **Step 3: Wire CLI**

In `tools/tasktool/cli.py`, in the `worktree` subparser group:

```python
    p_wt_repair = wt_sub.add_parser("repair")
    p_wt_repair.add_argument("id")
```

In dispatch:

```python
        elif args.worktree_cmd == "repair":
            commands.cmd_worktree_repair(repo_root=root, id=args.id)
```

- [ ] **Step 4: Implement `cmd_worktree_repair`**

Append to `tools/tasktool/commands.py`:

```python
def cmd_worktree_repair(*, repo_root: Path, id: str) -> None:
    from tasktool import worktree as wt
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        path_str = getattr(item, "worktree_path", None)
        branch = getattr(item, "worktree_branch", None)
        if not path_str or not branch:
            raise CommandError(
                f"{qid}: no recorded worktree fields to repair "
                f"(worktree_path={path_str!r}, worktree_branch={branch!r}); "
                f"use `tasktool worktree adopt {qid} <path>` after recreating manually"
            )
        wt_path = (write_root / path_str).resolve()
        # Already live? No-op.
        if wt.path_is_registered_worktree(write_root, wt_path) and wt_path.exists():
            print(f"{qid}: worktree already live at {wt_path}; no action.")
            return
        if not wt.branch_exists(write_root, branch):
            raise CommandError(
                f"{qid}: branch {branch!r} missing; cannot repair. "
                f"Recreate the branch or use `tasktool worktree adopt {qid} <path>`."
            )
        wt.git_worktree_add(write_root, wt_path, branch)
        print(f"{qid}: worktree recreated at {wt_path} on branch {branch}.")
```

- [ ] **Step 5: Run**

`python -m pytest tools/tasktool/tests/test_worktree_repair.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/tests/test_worktree_repair.py
git commit -m "P5.S2: implement worktree repair"
```

---

## Task 12: Update `finishing-a-development-branch` SKILL.md

**Files:**
- Modify: `skills/finishing-a-development-branch/SKILL.md`.

- [ ] **Step 1: Edit the skill**

Open `skills/finishing-a-development-branch/SKILL.md`. In Step 6 (Cleanup Workspace), keep the existing `git worktree remove` block as a fallback for non-tasktool projects, but insert a tasktool-first branch above it. Replace the section labelled `**If worktree path is under '.worktrees/', 'worktrees/', or '~/.config/superstar/worktrees/':**` with:

```markdown
**If `docs/tasklist.json` exists and the slice has a recorded worktree:** Prefer the tasktool path. For each slice merged on this branch, run:

```bash
tasktool worktree prune <slice-id>
```

`prune` enforces three guards (slice-done, branch-merged, clean-tree) and removes the worktree directory and branch. If `prune` refuses, address the reported cause (close the slice, complete the merge, clean the tree). For an irrecoverable scratch worktree, `tasktool worktree prune <slice-id> --force` overrides the prune guards only; it does not affect close, slice status, or review gates.

If you are currently inside the worktree being pruned, tasktool prints a two-step follow-up; run it from the authoritative checkout:

```bash
cd <authoritative-root>
git worktree remove <path>
tasktool worktree prune <slice-id> --finalize
```

**Otherwise — no tasktool, worktree path under `.worktrees/`, `worktrees/`, or `~/.config/superstar/worktrees/`:** Superstar created this worktree — we own cleanup.
```

(Leave the rest of the Step 6 block unchanged. Re-verify by reading the file after the edit.)

- [ ] **Step 2: Smoke check**

Run: `grep -n "tasktool worktree prune" skills/finishing-a-development-branch/SKILL.md`
Expected: at least 3 hits (prune call, `--force` note, `--finalize` follow-up).

- [ ] **Step 3: Commit**

```bash
git add skills/finishing-a-development-branch/SKILL.md
git commit -m "P5.S2: invoke tasktool worktree prune from finishing-a-development-branch"
```

---

## Task 13: Full-suite verification

- [ ] **Step 1: Run full tasktool tests**

Run: `python -m pytest tools/tasktool/tests -q`
Expected: all PASS.

- [ ] **Step 2: Run strict-format and schema validation**

Run: `tools/tasktool/tasktool validate --strict-format`
Expected: exit 0.

- [ ] **Step 3: Run repo-wide pre-commit if installed**

```bash
if command -v pre-commit >/dev/null 2>&1; then
    pre-commit run --all-files
else
    echo "pre-commit not installed; skipped"
fi
```

Expected: when installed, exit 0 (failures block — investigate before proceeding). When not installed, "skipped" message and exit 0.

- [ ] **Step 4: No commit at this step — proceeds to slice close in coordinator's hands.**

---

## Self-Review

**1. Spec coverage:**
- §5.3 prune three guards → Task 5 (slice-done, branch-merged, clean-tree).
- §5.3 `--keep-branch` → Task 6.
- §5.3 `--force` scoped to prune guards → Task 7 (positives + scope negatives for close, slice status, depends_on).
- §5.3 prune-from-inside → Task 8 (pending marker, exact follow-up line, skip destructive call).
- §5.3 `--finalize` preconditions → Task 8 (pending required, path absent from list, directory absent).
- §5.3 recent-HEAD informational note (≤60s) → Task 9.
- §5.3 `worktree repair` → Task 11.
- §5.3 audit fields (`worktree_pruned_at`, `worktree_prune_pending`, `worktree_prune_pending_at`) → Tasks 1–3 (model, serialize, validate, schema).
- §5.3.1 lifecycle table rows for prune/finalize → exercised across Tasks 5, 6, 7, 8.
- §5.3.2 `finishing-a-development-branch` skill edit → Task 12.
- §6 P5.S2 test bullets all addressed across Tasks 5–11. The "in-place slice prune is no-op" row of §5.3.1 has an explicit test (`test_prune_in_place_slice_is_noop_but_records_audit`).
- §5.3 spec wording "stash entries attributable to the worktree" — addressed by branch-attribution in `working_tree_dirty` plus the unrelated-stash false-positive test (Task 4).

**2. Placeholder scan:** no "TBD"/"handle edge cases"/"similar to Task N" present. Each step shows the code.

**3. Type consistency:** Helper names used in tests (`is_inside_worktree`, `branch_is_merged`, `working_tree_dirty`, `head_age_seconds`, `path_is_registered_worktree`, `branch_exists`, `git_worktree_remove`, `git_branch_delete`, `git_worktree_add`) match the definitions in Task 4. Command function signatures (`cmd_worktree_prune(*, repo_root, id, keep_branch, force, finalize)`, `cmd_worktree_repair(*, repo_root, id)`) match CLI dispatch.

**4. Handoff artifact:** out of scope for this plan write — coordinator owns the handoff per the writing-plans coordinator override.

**5. Scheduling check:** `P5.S2` depends on `P5.S1` (assumed shipped). No parallel group. The plan does not change the dependency graph.

**Known sharp edges flagged to the coordinator:**
- Tests assume P5.S1's `worktree adopt` accepts an arbitrary path and that `worktree_path`/`worktree_branch` are settable on cross-cutting rows. If S1's actual implementation differs, the fixture helpers may need to be adjusted — Task -1's preflight surfaces this before Task 1 lands.
- `_authoritative_parent_branch` reads `TasklistConfig.authoritative_branch` from `.tasktool/config.json`. The fallback when no config exists is `"main"` (matches the config dataclass default). If a per-slice parent metadata field lands in a later phase, route through that instead.
- The `--no-archive` foot-gun test (Task 10) depends on `start --ad-hoc` being live from P5.S1.
- Tests in Task 5+ call `tasktool close ... --skip-review-gate`. That flag exists on `cmd_close` today (`tools/tasktool/cli.py:110`) so this is not a new dependency.
