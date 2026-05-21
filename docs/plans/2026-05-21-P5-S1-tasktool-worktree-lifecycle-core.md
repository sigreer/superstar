# P5.S1 — Tasktool Worktree Lifecycle Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make tasktool the lifecycle authority for per-slice git worktrees by adding canonical naming, schema fields, `start` (default / `--in-place` / `--adopt` / `--ad-hoc`), `worktree list|status|adopt`, and installer/project-setup wiring. Prune, repair, finalize, skill rewrite, and subagent guard are explicitly out of scope (P5.S2 / P5.S3).

**Architecture:** Add a focused `tools/tasktool/worktree_lifecycle.py` module with three pure parts — the canonical naming function (`worktree_name`), worktree-aware filesystem inspectors (`inspect_recorded_state`, `linked_worktree_branch`, `is_inside_linked_worktree`), and idempotent-reuse decision (`classify_recorded_state`). Wire it through `commands.py` (extended `cmd_start`, new `cmd_worktree_list / status / adopt`, ad-hoc allocation reusing existing `cmd_create_cross`) and `cli.py` (new `--in-place`, `--adopt`, `--ad-hoc` flags on `start`; new `worktree` subparser group). Schema fields (`worktree_path`, `worktree_branch`, `worktree_in_place`, `worktree_pruned_at`, `worktree_prune_pending`, `worktree_prune_pending_at`) are added to `Slice` and `CrossCutting` dataclasses with `serialize.py`, `schema_gen.py`, and `validate.py` round-trip support. P5.S1 reserves the `_pruned_at` / `_prune_pending*` field names so P5.S2 can write to them without a second schema migration. Project-setup's existing row 1d gains a one-line legacy-dir warning.

**Tech Stack:** Python 3.11, argparse, dataclasses, pytest, `git worktree` CLI helpers already used by `tools/tasktool/worktree.py`.

**Spec:** `docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md`

**Tasktool row:** `P5.S1` (slice). The first execution step is `tools/tasktool/tasktool start P5.S1` from the authoritative checkout (or an existing linked worktree). Schedule already shows `P5.S1` is independently ready with no dependencies; no `tasktool deps` / `ratify` change required for this slice (the coordinator handles ratification when committing the plan).

---

## File Structure

Files to create:
- `tools/tasktool/worktree_lifecycle.py` — canonical naming, recorded-state inspection, idempotent-reuse classifier.
- `tools/tasktool/tests/test_worktree_naming.py` — unit tests for `worktree_name` (table-driven, matches spec §5.1).
- `tools/tasktool/tests/test_worktree_lifecycle.py` — unit tests for the classifier and inspectors (uses real `git worktree` against `tmp_path`, following `test_worktree_authority.py` style).
- `tools/tasktool/tests/test_start_worktree.py` — CLI integration tests for `tasktool start` default / `--in-place` / `--adopt` / `--ad-hoc` paths.
- `tools/tasktool/tests/test_worktree_subcommands.py` — CLI tests for `tasktool worktree list`, `status`, `adopt`.
- `tools/tasktool/tests/test_project_setup_gitignore.py` — covers the project-setup audit row for `.worktrees/` and the legacy-dir warning (calls the same audit helper, no subprocess against an external installer).

Files to modify:
- `tools/tasktool/model.py` — add six optional fields to `Slice` and `CrossCutting`.
- `tools/tasktool/serialize.py` — round-trip the new fields in `_slice` and `_cross`.
- `tools/tasktool/schema_gen.py` — extend the `slice_` and `cross` JSON Schema blocks.
- `tools/tasktool/validate.py` — strict format checks for the new fields (`worktree_in_place` is `bool|absent`; `worktree_path` and `worktree_branch` are `string|null`; null-consistency between path and `--in-place`).
- `tools/tasktool/commands.py` — extend `cmd_start` with mode flags and reuse classifier; add `cmd_worktree_list`, `cmd_worktree_status`, `cmd_worktree_adopt`; add ad-hoc allocator helper that wraps `cmd_create_cross`.
- `tools/tasktool/cli.py` — extend `start` parser with `--in-place`, `--adopt PATH`, `--ad-hoc SLUG`; add `worktree` subparser group with `list [--all]`, `status <id>`, `adopt <id> <path>`.
- `skills/project-setup/SKILL.md` — extend row 1d audit step to also warn (not fix) on detection of legacy `.claude/worktrees/`, `.codex/worktrees/`, `~/.config/superstar/worktrees/<project>` directories.

**Installer ownership (clarification per reviewer F4).** Spec §5.4 is headed "Installer / `project-setup` changes" and lists `.gitignore` + legacy-dir warnings as the two installer obligations. In this fork there is no separate shell installer that owns `.gitignore` edits: `tools/tasktool/install.sh` only installs the shim and pre-commit hook. The `project-setup` skill (row 1d) is the operator-facing surface that enforces `.gitignore` containing `.worktrees/` (via `git check-ignore -q .worktrees/`) and offers to scaffold the entry when missing. **This plan treats `project-setup` as the installer for §5.4** and adds explicit Task 11 coverage for the idempotence claim ("entry appears exactly once even if the audit runs twice"). No changes to `tools/tasktool/install.sh` are made in this slice.

Files **not** modified in S1 (deferred to S2/S3):
- `skills/using-git-worktrees/SKILL.md` (rewritten in S3).
- `skills/tasklist-discipline/SKILL.md` (subagent paragraph in S3).
- `skills/finishing-a-development-branch/SKILL.md` (prune step in S2).
- Anything that introduces `worktree prune`, `worktree repair`, `--finalize`, or the subagent env-var guard.

---

## Task 1: Canonical naming function

**Files:**
- Create: `tools/tasktool/worktree_lifecycle.py`
- Create: `tools/tasktool/tests/test_worktree_naming.py`

- [ ] **Step 1: Write the failing tests**

Create `tools/tasktool/tests/test_worktree_naming.py`:

```python
import pytest

from tasktool.worktree_lifecycle import worktree_name


@pytest.mark.parametrize(
    "id_, title, expected",
    [
        ("P5.S1", "Tasktool worktree lifecycle core",
         "worktree-p5-s1-tasktool-worktree-lifecycle-core"),
        ("X42", "Hotfix: shim drift",
         "worktree-x42-hotfix-shim-drift"),
        ("P13.S2", "Checkout rewrite",
         "worktree-p13-s2-checkout-rewrite"),
        # Whitespace + underscore collapse
        ("P1.S1", "  Foo   bar__baz  ",
         "worktree-p1-s1-foo-bar-baz"),
        # Non-ascii / punctuation stripped
        ("P1.S1", "Café — déjà vu!",
         "worktree-p1-s1-caf-d-j-vu"),
        # Repeated dashes collapsed
        ("P1.S1", "a---b",
         "worktree-p1-s1-a-b"),
        # Slice followup letter preserved
        ("P2.S3a", "Follow up",
         "worktree-p2-s3a-follow-up"),
    ],
)
def test_worktree_name_table(id_, title, expected):
    assert worktree_name(id_, title) == expected


def test_worktree_name_truncates_long_title_at_dash_boundary():
    long_title = "alpha bravo charlie delta echo foxtrot golf hotel india juliet"
    out = worktree_name("P1.S1", long_title)
    # slug portion (after "worktree-p1-s1-") must be <= 40 chars and end on a dash boundary
    slug = out.removeprefix("worktree-p1-s1-")
    assert len(slug) <= 40
    assert not slug.endswith("-")
    # truncation must not introduce a trailing partial word
    assert out.startswith("worktree-p1-s1-alpha-bravo-charlie-delta-echo")


def test_worktree_name_empty_title_keeps_id_segment():
    # Empty/all-stripped title must still produce a stable name (no trailing dash, no collision risk)
    out = worktree_name("X9", "!!!")
    assert out == "worktree-x9"


def test_worktree_name_rejects_malformed_id():
    from tasktool.ids import IdParseError
    with pytest.raises(IdParseError):
        worktree_name("not-an-id", "title")
```

- [ ] **Step 2: Run tests, confirm they fail**

Run: `cd tools && python -m pytest tasktool/tests/test_worktree_naming.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tasktool.worktree_lifecycle'`.

- [ ] **Step 3: Implement `worktree_name`**

Create `tools/tasktool/worktree_lifecycle.py`:

```python
"""Per-slice worktree lifecycle policy (P5.S1).

Pure helpers only — no git mutation, no tasklist mutation. Higher-level
command code in `commands.py` wires these together.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from tasktool.ids import parse_id

_TITLE_TRUNCATE = 40


def _slugify_id(id_value: str) -> str:
    # parse_id raises IdParseError on garbage; do this first so callers get a
    # clean error before we attempt to slugify.
    parse_id(id_value)
    s = id_value.lower().replace(".", "-")
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def _slugify_title(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if len(s) > _TITLE_TRUNCATE:
        cut = s[:_TITLE_TRUNCATE]
        last_dash = cut.rfind("-")
        if last_dash > 0:
            cut = cut[:last_dash]
        s = cut.rstrip("-")
    return s


def worktree_name(id_value: str, title: str) -> str:
    """Return the canonical worktree directory & branch name for (id, title).

    Spec §5.1. Stable, lowercase, deterministic. The same string is used as
    both the directory base name (under `.worktrees/`) and the git branch.
    """
    id_part = _slugify_id(id_value)
    title_part = _slugify_title(title)
    if not title_part:
        return f"worktree-{id_part}"
    return f"worktree-{id_part}-{title_part}"
```

- [ ] **Step 4: Run tests, confirm they pass**

Run: `cd tools && python -m pytest tasktool/tests/test_worktree_naming.py -v`
Expected: PASS for all parametrized cases plus the four explicit tests.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/worktree_lifecycle.py \
        tools/tasktool/tests/test_worktree_naming.py
git commit -m "P5.S1: canonical worktree_name function"
```

---

## Task 2: Schema fields on `Slice` and `CrossCutting`

**Files:**
- Modify: `tools/tasktool/model.py:35-51` (Slice), `tools/tasktool/model.py:68-77` (CrossCutting)
- Modify: `tools/tasktool/serialize.py:41-56` (_slice), `tools/tasktool/serialize.py:70-78` (_cross)
- Modify: `tools/tasktool/schema_gen.py:42-63` (slice_), `tools/tasktool/schema_gen.py:83-97` (cross)
- Modify: `tools/tasktool/validate.py:77-95` (_check_slice), `tools/tasktool/validate.py:110-115` (_check_cross)
- Test: `tools/tasktool/tests/test_schema_gen.py`, `tools/tasktool/tests/test_serialize.py`, `tools/tasktool/tests/test_validate.py`

- [ ] **Step 1: Write a failing round-trip test**

Append to `tools/tasktool/tests/test_serialize.py`:

```python
def test_slice_worktree_fields_round_trip():
    from tasktool.serialize import from_dict, to_dict
    raw = {
        "project": "demo",
        "schema_version": 1,
        "phases": [{
            "id": "P1", "title": "P", "created": "2026-05-21", "status": "ready",
            "slices": [{
                "id": "S1", "title": "S", "created": "2026-05-21", "status": "ready",
                "worktree_path": ".worktrees/worktree-p1-s1-s",
                "worktree_branch": "worktree-p1-s1-s",
                "worktree_in_place": False,
                "worktree_pruned_at": None,
                "worktree_prune_pending": False,
                "worktree_prune_pending_at": None,
            }],
        }],
        "cross_cutting": [],
        "archived_phases": [],
        "archived_cross_cutting": [],
    }
    p = from_dict(raw)
    out = to_dict(p)
    s = out["phases"][0]["slices"][0]
    assert s["worktree_path"] == ".worktrees/worktree-p1-s1-s"
    assert s["worktree_branch"] == "worktree-p1-s1-s"
    assert s["worktree_in_place"] is False


def test_slice_worktree_fields_default_null_when_absent():
    from tasktool.serialize import from_dict, to_dict
    raw = {
        "project": "demo", "schema_version": 1,
        "phases": [{
            "id": "P1", "title": "P", "created": "2026-05-21", "status": "ready",
            "slices": [{"id": "S1", "title": "S", "created": "2026-05-21", "status": "ready"}],
        }],
        "cross_cutting": [], "archived_phases": [], "archived_cross_cutting": [],
    }
    p = from_dict(raw)
    s = p.phases[0].slices[0]
    assert s.worktree_path is None
    assert s.worktree_branch is None
    assert s.worktree_in_place is False
    assert s.worktree_pruned_at is None
    assert s.worktree_prune_pending is False
    assert s.worktree_prune_pending_at is None


def test_cross_worktree_fields_round_trip():
    from tasktool.serialize import from_dict, to_dict
    raw = {
        "project": "demo", "schema_version": 1,
        "phases": [],
        "cross_cutting": [{
            "id": "X9", "title": "x", "created": "2026-05-21", "status": "ready",
            "worktree_path": ".worktrees/worktree-x9-x",
            "worktree_branch": "worktree-x9-x",
            "worktree_in_place": False,
            "worktree_pruned_at": None,
            "worktree_prune_pending": False,
            "worktree_prune_pending_at": None,
        }],
        "archived_phases": [], "archived_cross_cutting": [],
    }
    p = from_dict(raw)
    out = to_dict(p)
    assert out["cross_cutting"][0]["worktree_path"] == ".worktrees/worktree-x9-x"
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd tools && python -m pytest tasktool/tests/test_serialize.py::test_slice_worktree_fields_round_trip -v`
Expected: FAIL — `Slice` has no `worktree_path` attribute.

- [ ] **Step 3: Extend the dataclasses**

In `tools/tasktool/model.py`, add to `Slice` (after the existing `tasks` field) and `CrossCutting` (after `notes`) the same six fields, all optional:

```python
# Inside @dataclass(slots=True) class Slice:
    worktree_path: str | None = None
    worktree_branch: str | None = None
    worktree_in_place: bool = False
    worktree_pruned_at: str | None = None
    worktree_prune_pending: bool = False
    worktree_prune_pending_at: str | None = None
```

Repeat the exact same six lines inside `CrossCutting`. Order: keep them at the **end** of the dataclass body so kw-only / positional argument order is preserved.

- [ ] **Step 4: Extend `serialize.py`**

In `tools/tasktool/serialize.py`, replace the `_slice` and `_cross` constructors with versions that read the new keys.

**Raw-type strictness (per reviewer F5).** The deserializer must NOT coerce. `bool(sd.get("worktree_in_place"))` would silently turn the string `"false"` into `True` and validation would then run against the coerced value, hiding the bug. Use a `_strict_bool` helper that raises `ValidationError` for any non-bool, non-None value, and a `_strict_optional_str` helper that raises for any non-string, non-None value. Wire them into both `_slice` and `_cross`.

```python
def _strict_bool(value, *, scope: str, field: str, default: bool = False) -> bool:
    """Raise ValidationError if value is not None and not a real bool."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    from tasktool.validate import ValidationError
    raise ValidationError(f"{scope}.{field}: expected bool, got {type(value).__name__} ({value!r})")


def _strict_opt_str(value, *, scope: str, field: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    from tasktool.validate import ValidationError
    raise ValidationError(f"{scope}.{field}: expected string or null, got {type(value).__name__} ({value!r})")


    def _slice(sd):
        scope = f"phases[].slices[id={sd.get('id')}]"
        return Slice(
            id=sd["id"], title=sd["title"], created=sd["created"],
            started=sd.get("started"),
            status=_status(sd.get("status", "ready")),
            closed=sd.get("closed"),
            blocked_on=_blocked(sd.get("blocked_on")),
            depends_on=list(sd.get("depends_on", [])),
            planning_status=_planning_status(sd.get("planning_status", "proposed")),
            parallel_group=sd.get("parallel_group"),
            plan_path=sd.get("plan_path"),
            refs=list(sd.get("refs", [])),
            notes=sd.get("notes", ""),
            reviewer_chain=sd.get("reviewer_chain"),
            tasks=[_task(t) for t in sd.get("tasks", [])],
            worktree_path=_strict_opt_str(sd.get("worktree_path"), scope=scope, field="worktree_path"),
            worktree_branch=_strict_opt_str(sd.get("worktree_branch"), scope=scope, field="worktree_branch"),
            worktree_in_place=_strict_bool(sd.get("worktree_in_place"), scope=scope, field="worktree_in_place"),
            worktree_pruned_at=_strict_opt_str(sd.get("worktree_pruned_at"), scope=scope, field="worktree_pruned_at"),
            worktree_prune_pending=_strict_bool(sd.get("worktree_prune_pending"), scope=scope, field="worktree_prune_pending"),
            worktree_prune_pending_at=_strict_opt_str(sd.get("worktree_prune_pending_at"), scope=scope, field="worktree_prune_pending_at"),
        )
    def _cross(xd):
        scope = f"cross_cutting[id={xd.get('id')}]"
        return CrossCutting(
            id=xd["id"], title=xd["title"], created=xd["created"],
            started=xd.get("started"),
            status=_status(xd.get("status", "ready")),
            closed=xd.get("closed"),
            refs=list(xd.get("refs", [])),
            notes=xd.get("notes", ""),
            worktree_path=_strict_opt_str(xd.get("worktree_path"), scope=scope, field="worktree_path"),
            worktree_branch=_strict_opt_str(xd.get("worktree_branch"), scope=scope, field="worktree_branch"),
            worktree_in_place=_strict_bool(xd.get("worktree_in_place"), scope=scope, field="worktree_in_place"),
            worktree_pruned_at=_strict_opt_str(xd.get("worktree_pruned_at"), scope=scope, field="worktree_pruned_at"),
            worktree_prune_pending=_strict_bool(xd.get("worktree_prune_pending"), scope=scope, field="worktree_prune_pending"),
            worktree_prune_pending_at=_strict_opt_str(xd.get("worktree_prune_pending_at"), scope=scope, field="worktree_prune_pending_at"),
        )
```

(Place the two `_strict_*` helpers at module scope in `serialize.py`, above `from_dict`. The lazy import of `ValidationError` avoids a circular import.)

`to_dict` is generic over dataclass fields (it uses `asdict`-style walking in `_coerce`), so it picks up the new fields automatically. Verify by re-reading `serialize.py:11-23` after the change.

- [ ] **Step 5: Extend `schema_gen.py`**

In `tools/tasktool/schema_gen.py`, add these properties to **both** the `slice_` and `cross` property blocks (`schema_gen.py:42-63` and `schema_gen.py:83-97`):

```python
            "worktree_path": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "worktree_branch": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "worktree_in_place": {"type": "boolean"},
            "worktree_pruned_at": {"oneOf": [date_str, {"type": "null"}]},
            "worktree_prune_pending": {"type": "boolean"},
            "worktree_prune_pending_at": {"oneOf": [date_str, {"type": "null"}]},
```

Do not add them to `required`; they are all optional.

- [ ] **Step 6: Extend `validate.py`**

In `tools/tasktool/validate.py`, after the existing date checks in `_check_slice` (around line 89) and `_check_cross` (around line 115), add:

```python
    # worktree fields (P5.S1)
    if s.worktree_in_place:
        _require(
            s.worktree_path is None and s.worktree_branch is None,
            f"{scope}: worktree_in_place=true requires worktree_path/branch null",
        )
    _require(
        (s.worktree_path is None) == (s.worktree_branch is None),
        f"{scope}: worktree_path and worktree_branch must be both null or both set",
    )
    _check_date(s.worktree_pruned_at, scope, "worktree_pruned_at")
    _check_date(s.worktree_prune_pending_at, scope, "worktree_prune_pending_at")
```

Repeat the same block inside `_check_cross` with `c` instead of `s`.

- [ ] **Step 7: Run the full tasktool suite**

Run: `cd tools && python -m pytest tasktool/tests -q`
Expected: all pre-existing tests still pass; the three new serialize tests pass.

- [ ] **Step 8: Add schema-gen and validate coverage**

Append to `tools/tasktool/tests/test_schema_gen.py`:

```python
def test_schema_describes_slice_worktree_fields():
    from tasktool.schema_gen import build_schema
    sch = build_schema()
    slc = sch["properties"]["phases"]["items"]["properties"]["slices"]["items"]
    for key in ("worktree_path", "worktree_branch", "worktree_in_place",
                "worktree_pruned_at", "worktree_prune_pending", "worktree_prune_pending_at"):
        assert key in slc["properties"], key
    assert slc["additionalProperties"] is False


def test_schema_describes_cross_worktree_fields():
    from tasktool.schema_gen import build_schema
    sch = build_schema()
    xc = sch["properties"]["cross_cutting"]["items"]
    for key in ("worktree_path", "worktree_branch", "worktree_in_place",
                "worktree_pruned_at", "worktree_prune_pending", "worktree_prune_pending_at"):
        assert key in xc["properties"], key
```

Append to `tools/tasktool/tests/test_validate.py`:

```python
def test_validate_rejects_in_place_with_recorded_path():
    from tasktool.model import Project, Phase, Slice, Status
    from tasktool.validate import validate_project, ValidationError
    import pytest as _pt
    p = Project(project="d", phases=[Phase(id="P1", title="t", created="2026-05-21",
        slices=[Slice(id="S1", title="t", created="2026-05-21",
            worktree_in_place=True, worktree_path=".worktrees/x", worktree_branch="x")])])
    with _pt.raises(ValidationError, match="worktree_in_place"):
        validate_project(p)


def test_loads_project_rejects_string_for_worktree_in_place():
    """F5: raw JSON `"worktree_in_place": "false"` must be rejected by the
    deserializer (not silently coerced to True by `bool(...)`)."""
    from tasktool.serialize import loads_project
    from tasktool.validate import ValidationError
    import pytest as _pt
    text = (
        '{"project":"d","schema_version":1,'
        '"phases":[{"id":"P1","title":"t","created":"2026-05-21","status":"ready",'
        '"slices":[{"id":"S1","title":"t","created":"2026-05-21","status":"ready",'
        '"worktree_in_place":"false"}]}],'
        '"cross_cutting":[],"archived_phases":[],"archived_cross_cutting":[]}'
    )
    with _pt.raises(ValidationError, match="worktree_in_place"):
        loads_project(text)


def test_loads_project_rejects_int_for_worktree_path():
    """F5: raw JSON `"worktree_path": 7` must be rejected by the deserializer."""
    from tasktool.serialize import loads_project
    from tasktool.validate import ValidationError
    import pytest as _pt
    text = (
        '{"project":"d","schema_version":1,'
        '"phases":[{"id":"P1","title":"t","created":"2026-05-21","status":"ready",'
        '"slices":[{"id":"S1","title":"t","created":"2026-05-21","status":"ready",'
        '"worktree_path":7,"worktree_branch":"x"}]}],'
        '"cross_cutting":[],"archived_phases":[],"archived_cross_cutting":[]}'
    )
    with _pt.raises(ValidationError, match="worktree_path"):
        loads_project(text)


def test_loads_project_rejects_non_date_for_pruned_at():
    """F5: `worktree_pruned_at` must be a valid date or null; `validate_project`
    runs the date format check, and the deserializer ensures the raw type is
    string-or-null first."""
    from tasktool.serialize import loads_project, from_dict
    from tasktool.validate import ValidationError, validate_project
    import pytest as _pt
    # An int here is caught by the deserializer (string-or-null)
    text = (
        '{"project":"d","schema_version":1,'
        '"phases":[{"id":"P1","title":"t","created":"2026-05-21","status":"ready",'
        '"slices":[{"id":"S1","title":"t","created":"2026-05-21","status":"ready",'
        '"worktree_pruned_at":42}]}],'
        '"cross_cutting":[],"archived_phases":[],"archived_cross_cutting":[]}'
    )
    with _pt.raises(ValidationError, match="worktree_pruned_at"):
        loads_project(text)
    # A garbage date string is caught by validate_project's date check
    raw = {
        "project": "d", "schema_version": 1,
        "phases": [{"id": "P1", "title": "t", "created": "2026-05-21", "status": "ready",
            "slices": [{"id": "S1", "title": "t", "created": "2026-05-21", "status": "ready",
                "worktree_pruned_at": "not-a-date"}]}],
        "cross_cutting": [], "archived_phases": [], "archived_cross_cutting": [],
    }
    p = from_dict(raw)
    with _pt.raises(ValidationError):
        validate_project(p)


def test_validate_rejects_partial_worktree_fields():
    from tasktool.model import Project, Phase, Slice
    from tasktool.validate import validate_project, ValidationError
    import pytest as _pt
    p = Project(project="d", phases=[Phase(id="P1", title="t", created="2026-05-21",
        slices=[Slice(id="S1", title="t", created="2026-05-21",
            worktree_path=".worktrees/x", worktree_branch=None)])])
    with _pt.raises(ValidationError, match="both null or both set"):
        validate_project(p)
```

- [ ] **Step 9: Run all tests**

Run: `cd tools && python -m pytest tasktool/tests -q`
Expected: PASS.

- [ ] **Step 10: Confirm existing tasklist still validates**

Run: `./tools/tasktool/tasktool validate --strict-format`
Expected: exit 0 (only the pre-existing path warnings, no schema regression).

- [ ] **Step 11: Commit**

```bash
git add tools/tasktool/model.py tools/tasktool/serialize.py \
        tools/tasktool/schema_gen.py tools/tasktool/validate.py \
        tools/tasktool/tests/test_serialize.py \
        tools/tasktool/tests/test_schema_gen.py \
        tools/tasktool/tests/test_validate.py
git commit -m "P5.S1: tasklist schema fields for worktree lifecycle"
```

---

## Task 3: Recorded-state inspector and reuse classifier

**Files:**
- Modify: `tools/tasktool/worktree_lifecycle.py`
- Create: `tools/tasktool/tests/test_worktree_lifecycle.py`

This task adds the pure decision function the `start` command will call to handle the idempotent-reuse table from spec §5.3.

- [ ] **Step 1: Write failing tests**

Create `tools/tasktool/tests/test_worktree_lifecycle.py`:

```python
import subprocess
from pathlib import Path

import pytest

from tasktool.worktree_lifecycle import (
    RecordedState,
    classify_recorded_state,
    is_inside_linked_worktree,
    linked_worktree_branch,
)


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True)


def _repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "T")
    (root / "README.md").write_text("x\n")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "init")
    return root


def test_classify_no_record_returns_absent(tmp_path):
    root = _repo(tmp_path)
    state = classify_recorded_state(root, recorded_path=None, recorded_branch=None)
    assert state == RecordedState.ABSENT


def test_classify_path_and_branch_live_returns_consistent(tmp_path):
    root = _repo(tmp_path)
    wt = tmp_path / "linked"
    _git(root, "worktree", "add", "-b", "feat", str(wt))
    state = classify_recorded_state(root, recorded_path=wt, recorded_branch="feat")
    assert state == RecordedState.CONSISTENT


def test_classify_path_missing_branch_missing_returns_both_missing(tmp_path):
    root = _repo(tmp_path)
    state = classify_recorded_state(
        root,
        recorded_path=tmp_path / "ghost",
        recorded_branch="never-existed",
    )
    assert state == RecordedState.BOTH_MISSING


def test_classify_path_missing_branch_present_returns_path_missing(tmp_path):
    root = _repo(tmp_path)
    _git(root, "branch", "feat")
    state = classify_recorded_state(
        root,
        recorded_path=tmp_path / "ghost",
        recorded_branch="feat",
    )
    assert state == RecordedState.PATH_MISSING


def test_classify_path_present_but_not_worktree_returns_path_not_worktree(tmp_path):
    root = _repo(tmp_path)
    plain = tmp_path / "plain"
    plain.mkdir()
    state = classify_recorded_state(root, recorded_path=plain, recorded_branch="any")
    assert state == RecordedState.PATH_NOT_WORKTREE


def test_classify_path_present_branch_mismatched_returns_branch_mismatch(tmp_path):
    root = _repo(tmp_path)
    wt = tmp_path / "linked"
    _git(root, "worktree", "add", "-b", "feat", str(wt))
    state = classify_recorded_state(root, recorded_path=wt, recorded_branch="other")
    assert state == RecordedState.BRANCH_MISMATCH


def test_linked_worktree_branch_returns_branch(tmp_path):
    root = _repo(tmp_path)
    wt = tmp_path / "linked"
    _git(root, "worktree", "add", "-b", "feat", str(wt))
    assert linked_worktree_branch(root, wt) == "feat"


def test_linked_worktree_branch_returns_none_for_plain_dir(tmp_path):
    root = _repo(tmp_path)
    plain = tmp_path / "plain"
    plain.mkdir()
    assert linked_worktree_branch(root, plain) is None


def test_is_inside_linked_worktree_true_in_linked(tmp_path):
    root = _repo(tmp_path)
    wt = tmp_path / "linked"
    _git(root, "worktree", "add", "-b", "feat", str(wt))
    assert is_inside_linked_worktree(wt) is True


def test_is_inside_linked_worktree_false_in_main_checkout(tmp_path):
    root = _repo(tmp_path)
    assert is_inside_linked_worktree(root) is False
```

- [ ] **Step 2: Run, confirm failure**

Run: `cd tools && python -m pytest tasktool/tests/test_worktree_lifecycle.py -v`
Expected: FAIL — `RecordedState` / `classify_recorded_state` not found.

- [ ] **Step 3: Implement the inspectors and classifier**

Append to `tools/tasktool/worktree_lifecycle.py`:

```python
import enum


class RecordedState(enum.Enum):
    """Outcome of comparing the recorded worktree_path/branch against live filesystem state.

    Spec §5.3 idempotent-reuse table. CONSISTENT means `start` is a no-op;
    every other variant requires explicit operator action (refused with a
    targeted error message in `cmd_start`).
    """
    ABSENT = "absent"                       # No path recorded; start should create.
    CONSISTENT = "consistent"               # Path is a linked worktree, branch matches.
    BOTH_MISSING = "both_missing"           # Path gone, branch gone — repair.
    PATH_MISSING = "path_missing"           # Path gone, branch still present — adopt/repair.
    PATH_NOT_WORKTREE = "path_not_worktree" # Plain dir at recorded path — refuse.
    BRANCH_MISMATCH = "branch_mismatch"     # Linked worktree, wrong branch — refuse.


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=check
    )


def linked_worktree_branch(authoritative_root: Path, candidate: Path) -> str | None:
    """Return the branch checked out at `candidate` if it is a linked worktree of
    `authoritative_root`, else None. Resolution uses `git worktree list --porcelain`."""
    if not candidate.exists():
        return None
    candidate = candidate.resolve()
    result = _git(authoritative_root, "worktree", "list", "--porcelain")
    current_path: Path | None = None
    current_branch: str = ""
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            if current_path is not None and current_path == candidate:
                return current_branch or None
            current_path = Path(line.removeprefix("worktree ")).resolve()
            current_branch = ""
        elif line.startswith("branch "):
            current_branch = line.removeprefix("branch refs/heads/")
    if current_path is not None and current_path == candidate:
        return current_branch or None
    return None


def _branch_exists(root: Path, branch: str) -> bool:
    res = _git(root, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False)
    return res.returncode == 0


def classify_recorded_state(
    authoritative_root: Path,
    *,
    recorded_path: Path | None,
    recorded_branch: str | None,
) -> RecordedState:
    """Classify the live state of a recorded worktree against the filesystem.

    Spec §5.3 idempotent-reuse table. `recorded_path`/`recorded_branch` must
    either both be set or both be None.
    """
    if recorded_path is None and recorded_branch is None:
        return RecordedState.ABSENT
    assert recorded_path is not None and recorded_branch is not None
    path_exists = recorded_path.exists()
    branch_exists = _branch_exists(authoritative_root, recorded_branch)
    if not path_exists and not branch_exists:
        return RecordedState.BOTH_MISSING
    if not path_exists and branch_exists:
        return RecordedState.PATH_MISSING
    # Path exists.
    live_branch = linked_worktree_branch(authoritative_root, recorded_path)
    if live_branch is None:
        return RecordedState.PATH_NOT_WORKTREE
    if live_branch == recorded_branch:
        return RecordedState.CONSISTENT
    return RecordedState.BRANCH_MISMATCH


def is_inside_linked_worktree(cwd: Path) -> bool:
    """True when `cwd` is inside a linked git worktree (not the main checkout).

    Detected by `git rev-parse --git-dir` differing from `--git-common-dir`.
    Returns False outside any git repository.
    """
    try:
        gd = subprocess.run(
            ["git", "rev-parse", "--git-dir"], cwd=cwd, text=True,
            capture_output=True, check=True,
        ).stdout.strip()
        cd = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"], cwd=cwd, text=True,
            capture_output=True, check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return False
    return Path(gd).resolve() != Path(cd).resolve()
```

- [ ] **Step 4: Run tests, confirm pass**

Run: `cd tools && python -m pytest tasktool/tests/test_worktree_lifecycle.py -v`
Expected: PASS for all ten tests.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/worktree_lifecycle.py \
        tools/tasktool/tests/test_worktree_lifecycle.py
git commit -m "P5.S1: recorded-state classifier + worktree inspectors"
```

---

## Task 4: `tasktool start <id>` default path (create + backfill)

**Files:**
- Modify: `tools/tasktool/commands.py:659-666` (`cmd_start`)
- Modify: `tools/tasktool/cli.py:97-99` (start parser)
- Create: `tools/tasktool/tests/test_start_worktree.py`

The default `start` path creates `.worktrees/worktree-<id>-<slug>` on a same-named branch and records both fields. Backfill behavior: if the slice has no `worktree_path` yet (pre-existing slice), `start` computes and records. If `worktree_path` is already set, classifier decides (Task 5).

- [ ] **Step 1: Write the failing test**

Create `tools/tasktool/tests/test_start_worktree.py`:

```python
import json
import os
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
PYTHONPATH = str(Path(__file__).resolve().parents[2])


def run(root, *args, env_extra=None):
    env = os.environ.copy()
    env["PYTHONPATH"] = PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(TOOL), "--project-root", str(root), *args],
        text=True, capture_output=True, env=env,
    )


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True)


def seed_repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "T")
    (root / "docs").mkdir()
    assert run(root, "config", "init-local").returncode == 0
    assert run(root, "init", "--project", "demo").returncode == 0
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "init")
    assert run(root, "create", "phase", "--title", "Phase one").returncode == 0
    assert run(root, "create", "slice", "P1", "--title", "Lifecycle core").returncode == 0
    return root


def tasklist(root):
    return json.loads((root / "docs" / "tasklist.json").read_text())


def test_start_records_worktree_path_and_branch_and_creates_dir(tmp_path):
    root = seed_repo(tmp_path)
    r = run(root, "start", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(root)["phases"][0]["slices"][0]
    expected_name = "worktree-p1-s1-lifecycle-core"
    assert sl["worktree_path"] == f".worktrees/{expected_name}"
    assert sl["worktree_branch"] == expected_name
    assert sl["worktree_in_place"] is False
    assert (root / ".worktrees" / expected_name).is_dir()
    # Branch exists
    branches = _git(root, "branch", "--list", expected_name).stdout
    assert expected_name in branches
    # Output prints a `cd` line pointing at the worktree
    assert ".worktrees/" + expected_name in r.stdout


def test_start_is_idempotent_when_consistent(tmp_path):
    root = seed_repo(tmp_path)
    assert run(root, "start", "P1.S1").returncode == 0
    r = run(root, "start", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    # Still recorded once, dir still present, no error.
    sl = tasklist(root)["phases"][0]["slices"][0]
    assert sl["worktree_path"] == ".worktrees/worktree-p1-s1-lifecycle-core"
```

- [ ] **Step 2: Run and confirm failure**

Run: `cd tools && python -m pytest tasktool/tests/test_start_worktree.py -v`
Expected: FAIL — `worktree_path` is null because `cmd_start` doesn't yet create the worktree.

- [ ] **Step 3: Extend `cmd_start`**

In `tools/tasktool/commands.py`, replace the body of `cmd_start` (`commands.py:659-666`) with:

```python
def cmd_start(
    *,
    repo_root: Path,
    id: str,
    resume: bool = False,
    in_place: bool = False,
    adopt: str | None = None,
    ad_hoc: str | None = None,
) -> None:
    if ad_hoc is not None:
        # Reject a positional id alongside --ad-hoc at the command layer too,
        # so the rejection holds even when callers reach cmd_start without going
        # through the CLI dispatcher (e.g. direct Python imports in tests).
        if id is not None:
            raise CommandError("--ad-hoc does not accept a positional id")
        if in_place or adopt is not None:
            raise CommandError("--ad-hoc is mutually exclusive with --in-place and --adopt")
        # Allocate a fresh X<n> cross-cutting row and create its worktree.
        _start_ad_hoc(repo_root=repo_root, slug=ad_hoc)
        return
    if in_place and adopt is not None:
        raise CommandError("--in-place and --adopt are mutually exclusive")
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        kind = parse_id(qid)[0]
        # ─── Lifecycle preflight FIRST. No git/worktree mutation may run if the
        # row is DONE, or BLOCKED without --resume. _preflight_start raises before
        # we touch the filesystem.
        _preflight_start(qid, item, resume=resume)
        if in_place:
            _apply_start_in_place(qid, item)
        else:
            adopt_path: Path | None = Path(adopt).expanduser().resolve() if adopt else None
            # Auto-adopt: caller cwd is inside a linked worktree of this repo.
            from tasktool.worktree_lifecycle import is_inside_linked_worktree
            if adopt_path is None and is_inside_linked_worktree(repo_root):
                adopt_path = repo_root.resolve()
            if adopt_path is not None:
                _apply_start_adopt(write_root, qid, item, adopt_path)
            else:
                _apply_start_default(write_root, qid, item, resume=resume)
        # _start_item now only mutates status/blocked_on/started; refusals already
        # happened in _preflight_start, so this call cannot raise after side effects.
        _start_item(qid, item, resume=resume)
        _save(write_root, p)
        _notify_status(qid=qid, kind=kind, status=item.status, title=item.title)


def _preflight_start(qid: str, item, *, resume: bool) -> None:
    """Lifecycle refusals from `_start_item` lifted to run BEFORE any disk mutation.

    `_start_item` itself is kept unchanged so callers like `cmd_set` / `cmd_unblock`
    that don't touch worktrees continue to work; this preflight just runs the same
    checks earlier so the worktree branch of `cmd_start` can't leave dangling
    on-disk state after a refusal.
    """
    if item.status == Status.DONE:
        raise CommandError(f"{qid} is already done")
    if item.status == Status.BLOCKED and not resume:
        raise CommandError(f"{qid} is blocked; use start --resume to clear blocked_on")
```

Then add these three helpers in `commands.py` near `_start_item` (around line 569):

```python
def _apply_start_default(write_root: Path, qid: str, item, *, resume: bool) -> None:
    from tasktool.worktree_lifecycle import (
        RecordedState, classify_recorded_state, worktree_name,
    )
    name = worktree_name(qid, item.title)
    canonical_rel = f".worktrees/{name}"
    canonical_path = (write_root / canonical_rel).resolve()
    canonical_branch = name

    recorded_path = (write_root / item.worktree_path).resolve() if item.worktree_path else None
    state = classify_recorded_state(
        write_root, recorded_path=recorded_path, recorded_branch=item.worktree_branch,
    )
    if state == RecordedState.CONSISTENT:
        print(f"cd {recorded_path}")
        return
    if state == RecordedState.BOTH_MISSING:
        raise CommandError(
            f"{qid}: recorded worktree gone (path and branch missing); "
            f"run `tasktool worktree repair {qid}` (P5.S2) or re-record with `tasktool worktree adopt`."
        )
    if state == RecordedState.PATH_MISSING:
        raise CommandError(
            f"{qid}: recorded worktree path missing but branch {item.worktree_branch!r} still exists; "
            f"run `tasktool worktree adopt {qid} <new-path>` or `tasktool worktree repair {qid}` (P5.S2)."
        )
    if state == RecordedState.PATH_NOT_WORKTREE:
        raise CommandError(
            f"{qid}: recorded path {item.worktree_path!r} exists but is not a linked worktree. "
            f"Run `tasktool worktree prune {qid} --force` (P5.S2) then re-`start`."
        )
    if state == RecordedState.BRANCH_MISMATCH:
        raise CommandError(
            f"{qid}: linked worktree at {item.worktree_path!r} is on a different branch than "
            f"recorded ({item.worktree_branch!r}). Refusing to guess; resolve manually."
        )
    assert state == RecordedState.ABSENT
    # Fresh creation: refuse if canonical path or branch already exists out-of-band.
    if canonical_path.exists():
        raise CommandError(
            f"{qid}: canonical worktree path {canonical_rel!r} already exists outside tasktool. "
            f"Adopt with `tasktool worktree adopt {qid} {canonical_rel}` or remove it manually."
        )
    res = _subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{canonical_branch}"],
        cwd=write_root,
    )
    if res.returncode == 0:
        raise CommandError(
            f"{qid}: branch {canonical_branch!r} already exists out-of-band; "
            f"adopt the existing worktree or delete the branch."
        )
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    _subprocess.run(
        ["git", "worktree", "add", "-b", canonical_branch, str(canonical_path)],
        cwd=write_root, check=True, text=True, capture_output=True,
    )
    item.worktree_path = canonical_rel
    item.worktree_branch = canonical_branch
    item.worktree_in_place = False
    print(f"cd {canonical_path}")


def _apply_start_in_place(qid: str, item) -> None:
    if item.worktree_path is not None:
        raise CommandError(
            f"{qid}: --in-place refused; slice already has a recorded worktree at {item.worktree_path!r}."
        )
    item.worktree_in_place = True
    item.worktree_path = None
    item.worktree_branch = None


def _apply_start_adopt(write_root: Path, qid: str, item, adopt_path: Path) -> None:
    from tasktool.worktree_lifecycle import linked_worktree_branch
    branch = linked_worktree_branch(write_root, adopt_path)
    if branch is None:
        raise CommandError(
            f"{qid}: --adopt {adopt_path} is not a linked worktree of this repository."
        )
    try:
        rel = adopt_path.relative_to(write_root.resolve())
        rel_str = str(rel)
    except ValueError:
        rel_str = str(adopt_path)
    item.worktree_path = rel_str
    item.worktree_branch = branch
    item.worktree_in_place = False
    print(f"cd {adopt_path}")
```

Leave `_start_ad_hoc` as a stub (`raise CommandError("--ad-hoc not yet implemented")`) so the import resolves; the real body lands in Task 7.

- [ ] **Step 4: Extend the CLI parser**

In `tools/tasktool/cli.py`, replace the `p_start` block (`cli.py:97-99`) with:

```python
    p_start = sub.add_parser("start")
    p_start.add_argument("id", nargs="?")
    p_start.add_argument("--resume", action="store_true")
    p_start_mode = p_start.add_mutually_exclusive_group()
    p_start_mode.add_argument("--in-place", action="store_true")
    p_start_mode.add_argument("--adopt", metavar="PATH")
    p_start_mode.add_argument("--ad-hoc", metavar="SLUG")
```

And update the dispatcher (`cli.py:314-315`):

```python
        elif args.cmd == "start":
            if args.ad_hoc is None and not args.id:
                p.error("start requires <id> unless --ad-hoc <slug> is given")
            commands.cmd_start(
                repo_root=root, id=args.id, resume=args.resume,
                in_place=args.in_place, adopt=args.adopt, ad_hoc=args.ad_hoc,
            )
```

- [ ] **Step 5: Run the new tests**

Run: `cd tools && python -m pytest tasktool/tests/test_start_worktree.py -v -k "records_worktree_path or idempotent_when_consistent"`
Expected: PASS.

- [ ] **Step 6: Run the existing lifecycle-start tests**

Run: `cd tools && python -m pytest tasktool/tests/test_lifecycle_start.py -v`
Expected: PASS (the existing tests don't pass `--in-place`/`--adopt` and call against the local fixture root — they should keep working; if `seed()` in that file does not `git init`, the new `_apply_start_default` will fail because there is no git repo. Inspect `tools/tasktool/tests/test_lifecycle_start.py:22-28`; if no `git init` is present, **add an in-place fallback**: when the project-root has no `.git` directory, `cmd_start` skips worktree creation and emits a warning. Add this guard at the top of `_apply_start_default`:

```python
    if not (write_root / ".git").exists():
        # No git repo (tests that pre-date P5.S1). Behave as pre-P5 start.
        return
```

This keeps the pre-existing test suite green without changing its setup helpers.)

Run: `cd tools && python -m pytest tasktool/tests -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/cli.py \
        tools/tasktool/tests/test_start_worktree.py
git commit -m "P5.S1: tasktool start default path creates and records worktree"
```

---

## Task 5: Idempotent-reuse failure modes for `start`

**Files:**
- Modify: `tools/tasktool/tests/test_start_worktree.py`

The implementation from Task 4 already returns the right `CommandError` for each ambiguous state; this task adds explicit CLI-level coverage for every row of the spec §5.3 table.

- [ ] **Step 1: Write the failing tests**

Append to `tools/tasktool/tests/test_start_worktree.py`:

```python
def _seed_started(tmp_path):
    root = seed_repo(tmp_path)
    assert run(root, "start", "P1.S1").returncode == 0
    return root, ".worktrees/worktree-p1-s1-lifecycle-core"


def test_start_refused_when_path_missing_branch_missing(tmp_path):
    root, rel = _seed_started(tmp_path)
    # Remove worktree dir and delete branch.
    name = Path(rel).name
    _git(root, "worktree", "remove", "--force", rel)
    _git(root, "branch", "-D", name)
    r = run(root, "start", "P1.S1")
    assert r.returncode != 0
    assert "recorded worktree gone" in (r.stdout + r.stderr)


def test_start_refused_when_path_missing_branch_present(tmp_path):
    root, rel = _seed_started(tmp_path)
    name = Path(rel).name
    # git worktree remove deletes the dir but keeps the branch.
    _git(root, "worktree", "remove", "--force", rel)
    r = run(root, "start", "P1.S1")
    assert r.returncode != 0
    assert "still exists" in (r.stdout + r.stderr)


def test_start_refused_when_path_is_plain_dir(tmp_path):
    root, rel = _seed_started(tmp_path)
    name = Path(rel).name
    _git(root, "worktree", "remove", "--force", rel)
    # Drop a non-worktree directory at the recorded path.
    (root / rel).mkdir(parents=True)
    r = run(root, "start", "P1.S1")
    assert r.returncode != 0
    assert "not a linked worktree" in (r.stdout + r.stderr)


def test_start_on_done_row_does_not_create_worktree(tmp_path):
    """Lifecycle preflight (F1): a row that is already `done` must be refused
    BEFORE any `.worktrees/` or branch creation happens."""
    root = seed_repo(tmp_path)
    # Set status=done via the underlying machinery: start, then close (skip review gate).
    assert run(root, "start", "P1.S1").returncode == 0
    # remove the auto-created worktree dir & branch so we can observe "no side effects"
    # cleanly on the second start attempt
    expected_name = "worktree-p1-s1-lifecycle-core"
    _git(root, "worktree", "remove", "--force", f".worktrees/{expected_name}")
    _git(root, "branch", "-D", expected_name)
    # Re-record the worktree fields as null so the second `start` can't classify the
    # row as "needs repair"; mark slice done directly via `set --status done --skip-review-gate`.
    assert run(root, "set", "P1.S1", "--status", "done", "--skip-review-gate").returncode == 0
    r = run(root, "start", "P1.S1")
    assert r.returncode != 0
    assert "already done" in (r.stdout + r.stderr)
    # No new branch, no new worktree directory
    assert not (root / ".worktrees" / expected_name).exists()
    out = _git(root, "branch", "--list", expected_name).stdout.strip()
    assert out == ""


def test_start_on_blocked_row_without_resume_does_not_create_worktree(tmp_path):
    """F1: blocked-row preflight refusal must precede git mutation."""
    root = seed_repo(tmp_path)
    # Create a second slice and block it on the first
    assert run(root, "create", "slice", "P1", "--title", "Dependent").returncode == 0
    assert run(root, "block", "P1.S2", "--on", "external:waiting").returncode == 0
    r = run(root, "start", "P1.S2")
    assert r.returncode != 0
    assert "blocked" in (r.stdout + r.stderr)
    assert not (root / ".worktrees" / "worktree-p1-s2-dependent").exists()
    out = _git(root, "branch", "--list", "worktree-p1-s2-dependent").stdout.strip()
    assert out == ""


def test_start_refused_when_branch_mismatched(tmp_path):
    root, rel = _seed_started(tmp_path)
    name = Path(rel).name
    # Force the worktree onto a different branch.
    _git(root, "checkout", "-b", "elsewhere", "main")
    _git(root / rel, "checkout", "-b", "elsewhere2")
    r = run(root, "start", "P1.S1")
    assert r.returncode != 0
    out = r.stdout + r.stderr
    assert "different branch" in out
```

- [ ] **Step 2: Run, confirm pass**

Run: `cd tools && python -m pytest tasktool/tests/test_start_worktree.py -v`
Expected: PASS for all five reuse-table cases.

- [ ] **Step 3: Commit**

```bash
git add tools/tasktool/tests/test_start_worktree.py
git commit -m "P5.S1: cover ambiguous reuse states in tasktool start"
```

---

## Task 6: `--in-place` and `--adopt` (incl. auto-adopt)

**Files:**
- Modify: `tools/tasktool/tests/test_start_worktree.py`

The handlers are already wired in Task 4; this task asserts behavior end-to-end.

- [ ] **Step 1: Write the failing tests**

Append to `tools/tasktool/tests/test_start_worktree.py`:

```python
def test_start_in_place_marks_slice(tmp_path):
    root = seed_repo(tmp_path)
    r = run(root, "start", "P1.S1", "--in-place")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(root)["phases"][0]["slices"][0]
    assert sl["worktree_in_place"] is True
    assert sl["worktree_path"] is None
    assert sl["worktree_branch"] is None
    # No .worktrees directory created
    assert not (root / ".worktrees" / "worktree-p1-s1-lifecycle-core").exists()


def test_start_adopt_records_external_worktree(tmp_path):
    root = seed_repo(tmp_path)
    external = tmp_path / "external"
    _git(root, "worktree", "add", "-b", "manual-branch", str(external))
    r = run(root, "start", "P1.S1", "--adopt", str(external))
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(root)["phases"][0]["slices"][0]
    assert sl["worktree_branch"] == "manual-branch"
    assert sl["worktree_path"].endswith("external")


def test_start_adopt_refuses_non_worktree_path(tmp_path):
    root = seed_repo(tmp_path)
    plain = tmp_path / "plain"
    plain.mkdir()
    r = run(root, "start", "P1.S1", "--adopt", str(plain))
    assert r.returncode != 0
    assert "not a linked worktree" in (r.stdout + r.stderr)


def test_start_auto_adopt_from_linked_worktree_routes_to_authoritative(tmp_path):
    """F2: end-to-end authoritative-routing fixture.

    - Authoritative checkout on `main` configured via `config init-authority`.
    - Tasklist row committed to `main` so the routed write target has a real row.
    - A linked worker checkout is created; `tasktool start` is invoked from inside it.
    - Assertion: the worktree fields are persisted in the AUTHORITATIVE checkout's
      `docs/tasklist.json`, and the recorded path is the linked worker's path.
    """
    # 1. Build authoritative main checkout with init-authority routing.
    auth = tmp_path / "authoritative"
    auth.mkdir()
    _git(auth, "init", "-b", "main")
    _git(auth, "config", "user.email", "t@example.invalid")
    _git(auth, "config", "user.name", "T")
    (auth / "docs").mkdir()
    assert run(auth, "config", "init-authority", "--branch", "main").returncode == 0
    assert run(auth, "init", "--project", "demo").returncode == 0
    _git(auth, "add", "-A")
    _git(auth, "commit", "-m", "init")
    assert run(auth, "create", "phase", "--title", "Phase one").returncode == 0
    assert run(auth, "create", "slice", "P1", "--title", "Lifecycle core").returncode == 0
    _git(auth, "add", "-A")
    _git(auth, "commit", "-m", "seed slice")

    # 2. Create a linked worker checkout from the authoritative repo.
    worker = tmp_path / "worker"
    _git(auth, "worktree", "add", "-b", "feature-branch", str(worker))

    # 3. Run tasktool start from inside the worker; routing must auto-adopt.
    env_extra = {"TASKTOOL_AUTHORITY_ROOT": str(auth)}
    r = run(worker, "start", "P1.S1", env_extra=env_extra)
    assert r.returncode == 0, r.stdout + r.stderr

    # 4. Assertion: the authoritative tasklist now records the worker's path/branch.
    sl = tasklist(auth)["phases"][0]["slices"][0]
    assert sl["worktree_branch"] == "feature-branch"
    assert Path(sl["worktree_path"]).name == "worker"

    # 5. The worker checkout's tasklist (if any) must NOT shadow the authoritative one.
    worker_tasklist = worker / "docs" / "tasklist.json"
    if worker_tasklist.exists():
        wsl = json.loads(worker_tasklist.read_text())["phases"][0]["slices"][0]
        # routed writes go to auth; worker copy is whatever was committed on feature-branch
        # (the seed slice with no worktree fields). The test is satisfied as long as
        # the authoritative copy carries the new fields.
        assert sl["worktree_branch"] == "feature-branch"


def test_start_auto_adopt_unrouted_local_repo(tmp_path):
    """Lighter sibling of the routed test: in `config init-local` mode (no
    authoritative routing), auto-adopt should still record the linked-worktree
    path against the slice. Verifies the `is_inside_linked_worktree` branch of
    `cmd_start` without going through `_resolve_write_root`.
    """
    root = seed_repo(tmp_path)
    linked = tmp_path / "linked"
    _git(root, "worktree", "add", "-b", "in-flight", str(linked))
    # Commit the seeded slice so the linked worktree sees the tasklist row.
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "seed slice")
    # Pull main's commit into the linked worktree
    _git(linked, "merge", "main", "--ff")
    r = run(linked, "start", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(root)["phases"][0]["slices"][0]
    assert sl["worktree_branch"] == "in-flight"
    assert Path(sl["worktree_path"]).name == "linked"


def test_start_in_place_then_normal_start_is_refused(tmp_path):
    root = seed_repo(tmp_path)
    assert run(root, "start", "P1.S1", "--in-place").returncode == 0
    r = run(root, "start", "P1.S1")
    # Slice is already in_progress (so _start_item is a no-op), and worktree
    # state shows ABSENT path with worktree_in_place=true. Subsequent default
    # start must not create a worktree behind the user's back.
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(root)["phases"][0]["slices"][0]
    assert sl["worktree_in_place"] is True
    assert sl["worktree_path"] is None
```

- [ ] **Step 2: Run, confirm the in-place-then-default test fails**

Run: `cd tools && python -m pytest tasktool/tests/test_start_worktree.py -v -k "in_place_then_normal"`
Expected: FAIL — `_apply_start_default` currently treats `worktree_path=None` as "no record" and would create a worktree, erasing the in-place marker.

- [ ] **Step 3: Patch `_apply_start_default` for in-place safety**

In `tools/tasktool/commands.py`, near the top of `_apply_start_default`, add:

```python
    if item.worktree_in_place:
        # In-place slice; default start is a no-op on disk.
        return
```

- [ ] **Step 4: Run all `test_start_worktree.py` tests**

Run: `cd tools && python -m pytest tasktool/tests/test_start_worktree.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/tests/test_start_worktree.py
git commit -m "P5.S1: --in-place, --adopt, and auto-adopt for tasktool start"
```

---

## Task 7: `--ad-hoc <slug>` allocates X<n> and creates worktree

**Files:**
- Modify: `tools/tasktool/commands.py` (replace the `_start_ad_hoc` stub from Task 4)
- Modify: `tools/tasktool/tests/test_start_worktree.py`

Per spec §5.3: `--ad-hoc <slug>` allocates a normal cross-cutting `X<n>` row (existing `cmd_create_cross` machinery, existing `X\d+` grammar — **no grammar change**), with `status: in_progress`, `title: "Ad-hoc: <slug>"`, `notes: "ad-hoc"`, and the standard worktree fields.

- [ ] **Step 1: Write the failing tests**

Append to `tools/tasktool/tests/test_start_worktree.py`:

```python
def test_start_ad_hoc_creates_X_row_and_worktree(tmp_path):
    root = seed_repo(tmp_path)
    r = run(root, "start", "--ad-hoc", "shim-drift")
    assert r.returncode == 0, r.stdout + r.stderr
    tl = tasklist(root)
    assert len(tl["cross_cutting"]) == 1
    x = tl["cross_cutting"][0]
    assert x["id"].startswith("X")
    assert x["title"] == "Ad-hoc: shim-drift"
    assert x["status"] == "in_progress"
    assert x["notes"] == "ad-hoc"
    name = f"worktree-{x['id'].lower()}-ad-hoc-shim-drift"
    assert x["worktree_path"] == f".worktrees/{name}"
    assert x["worktree_branch"] == name
    assert (root / ".worktrees" / name).is_dir()
    # CLI prints the allocated ID so callers can chain commands
    assert x["id"] in r.stdout


def test_start_ad_hoc_requires_slug(tmp_path):
    root = seed_repo(tmp_path)
    r = run(root, "start", "--ad-hoc", "")
    assert r.returncode != 0
    assert "slug" in (r.stdout + r.stderr).lower()


def test_start_ad_hoc_rejects_id_argument(tmp_path):
    root = seed_repo(tmp_path)
    r = run(root, "start", "P1.S1", "--ad-hoc", "x")
    assert r.returncode != 0
```

- [ ] **Step 2: Run, confirm failure**

Run: `cd tools && python -m pytest tasktool/tests/test_start_worktree.py -v -k ad_hoc`
Expected: FAIL — stub raises.

- [ ] **Step 3: Implement `_start_ad_hoc`**

Replace the stub in `tools/tasktool/commands.py` with:

```python
def _start_ad_hoc(*, repo_root: Path, slug: str) -> None:
    slug = (slug or "").strip()
    if not slug:
        raise CommandError("--ad-hoc requires a non-empty <slug>")
    title = f"Ad-hoc: {slug}"
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        new_id = next_cross_id(p, write_root)
        item = CrossCutting(
            id=new_id, title=title, created=_today(),
            status=Status.IN_PROGRESS, started=_today(), notes="ad-hoc",
        )
        p.cross_cutting.append(item)
        _apply_start_default(write_root, new_id, item, resume=False)
        _save(write_root, p)
        _notify_status(qid=new_id, kind="cross", status=item.status, title=item.title)
        print(new_id)
```

Also: in the CLI dispatcher (Task 4 edit), the parser currently refuses `id` together with `--ad-hoc` because of the mutually-exclusive group on the mode flags but **not** on `id`. Tighten the dispatcher check:

```python
        elif args.cmd == "start":
            if args.ad_hoc is not None:
                if args.id is not None:
                    p.error("--ad-hoc cannot be combined with a positional id")
            elif not args.id:
                p.error("start requires <id> unless --ad-hoc <slug> is given")
            commands.cmd_start(
                repo_root=root, id=args.id, resume=args.resume,
                in_place=args.in_place, adopt=args.adopt, ad_hoc=args.ad_hoc,
            )
```

- [ ] **Step 4: Run tests**

Run: `cd tools && python -m pytest tasktool/tests/test_start_worktree.py -v -k ad_hoc`
Expected: PASS.

- [ ] **Step 5: Run the full suite**

Run: `cd tools && python -m pytest tasktool/tests -q`
Expected: PASS.

- [ ] **Step 6: Hide ad-hoc rows from default `tasktool list`**

Spec §5.3: "Ad-hoc rows are tagged with `notes: \"ad-hoc\"` so `tasktool list` can hide them by default (visible under `tasktool list --all`)." Implement this in the existing `cmd_list` so ad-hoc rows created by Step 3 don't pollute the default tracker view.

Find `cmd_list` in `tools/tasktool/commands.py` (around line 1296). Locate the cross-cutting iteration and add a filter:

```python
# Inside cmd_list, where cross_cutting rows are rendered:
for c in p.cross_cutting:
    if not show_all and (c.notes or "").strip() == "ad-hoc":
        continue
    ...
```

(`show_all` is already a parameter on `cmd_list`; if the parameter is named differently in the existing implementation, use that name. Verify with `grep "def cmd_list" tools/tasktool/commands.py`.)

Add a test in `tools/tasktool/tests/test_start_worktree.py`:

```python
def test_ad_hoc_row_hidden_from_default_list_visible_with_all(tmp_path):
    root = seed_repo(tmp_path)
    assert run(root, "start", "--ad-hoc", "shim-drift").returncode == 0
    r_default = run(root, "list")
    r_all = run(root, "list", "--all")
    assert "Ad-hoc: shim-drift" not in r_default.stdout
    assert "Ad-hoc: shim-drift" in r_all.stdout
```

Run: `cd tools && python -m pytest tasktool/tests/test_start_worktree.py -v -k hidden_from_default`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/cli.py \
        tools/tasktool/tests/test_start_worktree.py
git commit -m "P5.S1: --ad-hoc allocates X<n> row plus worktree; list hides by default"
```

---

## Task 8: `tasktool worktree list [--all]`

**Files:**
- Modify: `tools/tasktool/commands.py` (new `cmd_worktree_list`)
- Modify: `tools/tasktool/cli.py` (new `worktree` subparser group)
- Create: `tools/tasktool/tests/test_worktree_subcommands.py`

Default output: every slice and cross-cutting row with a non-null `worktree_path`. `--all` additionally includes `--in-place` rows and rows with `worktree_pruned_at` set but no live fields. Columns: ID, status, path, branch, health.

- [ ] **Step 1: Write the failing test**

Create `tools/tasktool/tests/test_worktree_subcommands.py`:

```python
import json
import os
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
PYTHONPATH = str(Path(__file__).resolve().parents[2])


def run(root, *args):
    env = os.environ.copy()
    env["PYTHONPATH"] = PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, str(TOOL), "--project-root", str(root), *args],
        text=True, capture_output=True, env=env,
    )


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True)


def seed_with_started_slice(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "T")
    (root / "docs").mkdir()
    assert run(root, "config", "init-local").returncode == 0
    assert run(root, "init", "--project", "demo").returncode == 0
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "init")
    assert run(root, "create", "phase", "--title", "P").returncode == 0
    assert run(root, "create", "slice", "P1", "--title", "Slice one").returncode == 0
    assert run(root, "start", "P1.S1").returncode == 0
    return root


def test_worktree_list_shows_live_slice(tmp_path):
    root = seed_with_started_slice(tmp_path)
    r = run(root, "worktree", "list")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "P1.S1" in r.stdout
    assert "worktree-p1-s1-slice-one" in r.stdout
    assert "live" in r.stdout


def test_worktree_list_hides_in_place_by_default_shows_with_all(tmp_path):
    root = seed_with_started_slice(tmp_path)
    # Second slice in-place
    assert run(root, "create", "slice", "P1", "--title", "Spec slice").returncode == 0
    assert run(root, "start", "P1.S2", "--in-place").returncode == 0
    r_default = run(root, "worktree", "list")
    r_all = run(root, "worktree", "list", "--all")
    assert "P1.S2" not in r_default.stdout
    assert "P1.S2" in r_all.stdout
    assert "in-place" in r_all.stdout


def test_worktree_list_marks_missing_path(tmp_path):
    root = seed_with_started_slice(tmp_path)
    # Remove the worktree directory out-of-band but keep the branch
    _git(root, "worktree", "remove", "--force", ".worktrees/worktree-p1-s1-slice-one")
    r = run(root, "worktree", "list")
    assert r.returncode == 0
    assert "missing-path" in r.stdout
```

- [ ] **Step 2: Run, confirm failure**

Run: `cd tools && python -m pytest tasktool/tests/test_worktree_subcommands.py -v -k worktree_list`
Expected: FAIL — `worktree` subcommand not registered.

- [ ] **Step 3: Implement `cmd_worktree_list`**

Add to `tools/tasktool/commands.py`:

```python
def _iter_worktree_rows(p):
    """Yield (qid, item) pairs for every slice + cross row that may carry worktree fields."""
    for ph in p.phases:
        for s in ph.slices:
            yield f"{ph.id}.{s.id}", s
    for c in p.cross_cutting:
        yield c.id, c


def _health_for(write_root: Path, item) -> str:
    from tasktool.worktree_lifecycle import (
        RecordedState, classify_recorded_state,
    )
    if item.worktree_in_place:
        return "in-place"
    if item.worktree_path is None and item.worktree_branch is None:
        if getattr(item, "worktree_pruned_at", None):
            return "pruned"
        return "absent"
    recorded_path = (write_root / item.worktree_path).resolve() if item.worktree_path else None
    state = classify_recorded_state(
        write_root, recorded_path=recorded_path, recorded_branch=item.worktree_branch,
    )
    return {
        RecordedState.CONSISTENT: "live",
        RecordedState.BOTH_MISSING: "missing-path",
        RecordedState.PATH_MISSING: "missing-path",
        RecordedState.PATH_NOT_WORKTREE: "mismatched",
        RecordedState.BRANCH_MISMATCH: "mismatched",
        RecordedState.ABSENT: "absent",
    }[state]


def cmd_worktree_list(*, repo_root: Path, show_all: bool = False) -> str:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        rows = []
        for qid, item in _iter_worktree_rows(p):
            has_path = item.worktree_path is not None
            is_in_place = item.worktree_in_place
            is_pruned = (not has_path) and (not is_in_place) and bool(
                getattr(item, "worktree_pruned_at", None)
            )
            if not show_all and not has_path:
                continue
            if is_in_place and not show_all:
                continue
            if is_pruned and not show_all:
                continue
            health = _health_for(write_root, item)
            path = item.worktree_path or ""
            branch = item.worktree_branch or ""
            rows.append((qid, item.status.value, path, branch, health))
        if not rows:
            return "(no worktrees)\n"
        widths = [max(len(str(r[i])) for r in rows) for i in range(5)]
        headers = ("ID", "STATUS", "PATH", "BRANCH", "HEALTH")
        widths = [max(widths[i], len(headers[i])) for i in range(5)]
        line = lambda r: "  ".join(str(r[i]).ljust(widths[i]) for i in range(5))
        out_lines = [line(headers)] + [line(r) for r in rows]
        return "\n".join(out_lines) + "\n"
```

- [ ] **Step 4: Add the CLI parser**

In `tools/tasktool/cli.py`, after the existing `p_start` block, add:

```python
    p_wt = sub.add_parser("worktree")
    wt_sub = p_wt.add_subparsers(dest="wt_cmd", required=True)
    p_wt_list = wt_sub.add_parser("list")
    p_wt_list.add_argument("--all", action="store_true", dest="show_all")
    p_wt_status = wt_sub.add_parser("status")
    p_wt_status.add_argument("id")
    p_wt_adopt = wt_sub.add_parser("adopt")
    p_wt_adopt.add_argument("id")
    p_wt_adopt.add_argument("path")
```

And in the dispatcher (`cli.py`, after the `start` branch):

```python
        elif args.cmd == "worktree":
            if args.wt_cmd == "list":
                sys.stdout.write(commands.cmd_worktree_list(repo_root=root, show_all=args.show_all))
            elif args.wt_cmd == "status":
                sys.stdout.write(commands.cmd_worktree_status(repo_root=root, id=args.id))
            elif args.wt_cmd == "adopt":
                commands.cmd_worktree_adopt(repo_root=root, id=args.id, path=Path(args.path))
```

(`cmd_worktree_status` / `cmd_worktree_adopt` ship in Tasks 9 / 10; for now, in the dispatcher above, leave only the `list` branch wired and the others raising `NotImplementedError` via stubs in `commands.py` to avoid `AttributeError`.)

- [ ] **Step 5: Run tests**

Run: `cd tools && python -m pytest tasktool/tests/test_worktree_subcommands.py -v -k worktree_list`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/cli.py \
        tools/tasktool/tests/test_worktree_subcommands.py
git commit -m "P5.S1: tasktool worktree list"
```

---

## Task 9: `tasktool worktree status <id>`

**Files:**
- Modify: `tools/tasktool/commands.py` (new `cmd_worktree_status`)
- Modify: `tools/tasktool/tests/test_worktree_subcommands.py`

Detailed health for one slice: path, branch, ahead/behind parent (`git rev-list --left-right --count`), dirty state (count of `git status --porcelain` lines), last activity (`HEAD` commit timestamp).

- [ ] **Step 1: Write the failing test**

Append to `tools/tasktool/tests/test_worktree_subcommands.py`:

```python
def test_worktree_status_live_slice_reports_clean(tmp_path):
    root = seed_with_started_slice(tmp_path)
    r = run(root, "worktree", "status", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    out = r.stdout
    assert "path:" in out
    assert "branch: worktree-p1-s1-slice-one" in out
    assert "ahead/behind:" in out
    assert "dirty: clean" in out
    assert "last_activity:" in out


def test_worktree_status_reports_dirty_after_edit(tmp_path):
    root = seed_with_started_slice(tmp_path)
    wt = root / ".worktrees" / "worktree-p1-s1-slice-one"
    (wt / "note.txt").write_text("dirty\n")
    r = run(root, "worktree", "status", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "dirty: 1 path(s)" in r.stdout


def test_worktree_status_unknown_slice(tmp_path):
    root = seed_with_started_slice(tmp_path)
    r = run(root, "worktree", "status", "P9.S9")
    assert r.returncode != 0
    assert "not found" in (r.stdout + r.stderr)


def test_worktree_status_uses_configured_authoritative_branch(tmp_path):
    """F3: when `authoritative_branch=develop`, status must report ahead/behind
    against `develop`, not against a hardcoded `main`."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "develop")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "T")
    (root / "docs").mkdir()
    assert run(root, "config", "init-authority", "--branch", "develop").returncode == 0
    assert run(root, "init", "--project", "demo").returncode == 0
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "init")
    assert run(root, "create", "phase", "--title", "P").returncode == 0
    assert run(root, "create", "slice", "P1", "--title", "Slice").returncode == 0
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "seed slice")
    assert run(root, "start", "P1.S1").returncode == 0
    r = run(root, "worktree", "status", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    # Crucially: the report names `develop` as the parent, not `main`.
    assert "vs develop" in r.stdout
    assert "vs main" not in r.stdout


def test_worktree_status_in_place_slice(tmp_path):
    root = seed_with_started_slice(tmp_path)
    assert run(root, "create", "slice", "P1", "--title", "Spec slice").returncode == 0
    assert run(root, "start", "P1.S2", "--in-place").returncode == 0
    r = run(root, "worktree", "status", "P1.S2")
    assert r.returncode == 0
    assert "in-place" in r.stdout
```

- [ ] **Step 2: Run, confirm failure**

Run: `cd tools && python -m pytest tasktool/tests/test_worktree_subcommands.py -v -k worktree_status`
Expected: FAIL — stub raises `NotImplementedError`.

- [ ] **Step 3: Implement `cmd_worktree_status`**

In `tools/tasktool/commands.py`, replace the stub with:

```python
def cmd_worktree_status(*, repo_root: Path, id: str) -> str:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        if item.worktree_in_place:
            return f"{qid}: in-place (no worktree on disk)\n"
        if item.worktree_path is None:
            return f"{qid}: no worktree recorded\n"
        wt = (write_root / item.worktree_path).resolve()
        health = _health_for(write_root, item)
        lines = [
            f"{qid}: {health}",
            f"path: {item.worktree_path}",
            f"branch: {item.worktree_branch}",
        ]
        if health == "live":
            # ahead/behind vs the configured authoritative parent branch (NOT a
            # hardcoded "main"). _resolve_write_root already exposes this via
            # `authoritative_branch`; we re-read config here directly to avoid
            # double-routing inside the existing _write_context.
            from tasktool.config import load_config
            parent_branch = load_config(write_root).tasklist.authoritative_branch
            try:
                ab = _subprocess.run(
                    ["git", "rev-list", "--left-right", "--count",
                     f"{parent_branch}...{item.worktree_branch}"],
                    cwd=write_root, text=True, capture_output=True, check=True,
                ).stdout.strip().split()
                behind, ahead = ab[0], ab[1]
                lines.append(f"ahead/behind: {ahead}/{behind} (vs {parent_branch})")
            except _subprocess.CalledProcessError:
                lines.append(f"ahead/behind: unknown (vs {parent_branch})")
            dirty = _subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=wt, text=True, capture_output=True, check=True,
            ).stdout.splitlines()
            lines.append(f"dirty: {'clean' if not dirty else f'{len(dirty)} path(s)'}")
            last = _subprocess.run(
                ["git", "log", "-1", "--format=%cI"],
                cwd=wt, text=True, capture_output=True, check=True,
            ).stdout.strip()
            lines.append(f"last_activity: {last}")
        return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run tests**

Run: `cd tools && python -m pytest tasktool/tests/test_worktree_subcommands.py -v -k worktree_status`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/tests/test_worktree_subcommands.py
git commit -m "P5.S1: tasktool worktree status"
```

---

## Task 10: `tasktool worktree adopt <id> <path>`

**Files:**
- Modify: `tools/tasktool/commands.py` (new `cmd_worktree_adopt`)
- Modify: `tools/tasktool/tests/test_worktree_subcommands.py`

Adopt an existing linked worktree against a slice. Verify it is a linked worktree of the authoritative repo and store both fields. Refuse if the slice already has a different `worktree_path` (require an explicit `--force`? Spec §5.3 says adopt is used "when the harness or human created the worktree out-of-band, or when repairing state after a path rename" — repair is destructive of the previous record, so it must overwrite when the previous record is dead. Implement: overwrite when previous classifier state is not `CONSISTENT`; refuse with guidance when previous state is `CONSISTENT` and the new path differs).

- [ ] **Step 1: Write the failing tests**

Append to `tools/tasktool/tests/test_worktree_subcommands.py`:

```python
def test_worktree_adopt_records_external_worktree(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "T")
    (root / "docs").mkdir()
    assert run(root, "config", "init-local").returncode == 0
    assert run(root, "init", "--project", "demo").returncode == 0
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "init")
    assert run(root, "create", "phase", "--title", "P").returncode == 0
    assert run(root, "create", "slice", "P1", "--title", "Slice").returncode == 0
    external = tmp_path / "external"
    _git(root, "worktree", "add", "-b", "external-branch", str(external))
    r = run(root, "worktree", "adopt", "P1.S1", str(external))
    assert r.returncode == 0, r.stdout + r.stderr
    sl = json.loads((root / "docs" / "tasklist.json").read_text())["phases"][0]["slices"][0]
    assert sl["worktree_branch"] == "external-branch"
    assert sl["worktree_path"].endswith("external")


def test_worktree_adopt_refuses_non_worktree(tmp_path):
    root = seed_with_started_slice(tmp_path)
    plain = tmp_path / "plain"
    plain.mkdir()
    r = run(root, "worktree", "adopt", "P1.S1", str(plain))
    assert r.returncode != 0
    assert "not a linked worktree" in (r.stdout + r.stderr)


def test_worktree_adopt_refuses_to_overwrite_live_record(tmp_path):
    root = seed_with_started_slice(tmp_path)
    external = tmp_path / "external"
    _git(root, "worktree", "add", "-b", "external-branch", str(external))
    r = run(root, "worktree", "adopt", "P1.S1", str(external))
    assert r.returncode != 0
    assert "already" in (r.stdout + r.stderr)


def test_worktree_adopt_overwrites_dead_record(tmp_path):
    root = seed_with_started_slice(tmp_path)
    # Kill the live worktree but keep the branch
    _git(root, "worktree", "remove", "--force", ".worktrees/worktree-p1-s1-slice-one")
    external = tmp_path / "external"
    _git(root, "worktree", "add", "-b", "external-branch", str(external))
    r = run(root, "worktree", "adopt", "P1.S1", str(external))
    assert r.returncode == 0, r.stdout + r.stderr
    sl = json.loads((root / "docs" / "tasklist.json").read_text())["phases"][0]["slices"][0]
    assert sl["worktree_branch"] == "external-branch"
```

- [ ] **Step 2: Implement `cmd_worktree_adopt`**

In `tools/tasktool/commands.py`, replace the adopt stub:

```python
def cmd_worktree_adopt(*, repo_root: Path, id: str, path: Path) -> None:
    from tasktool.worktree_lifecycle import (
        RecordedState, classify_recorded_state, linked_worktree_branch,
    )
    path = path.expanduser().resolve()
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        if item.worktree_in_place:
            raise CommandError(f"{qid}: cannot adopt; slice is marked --in-place")
        # If the current record is still live and consistent, refuse to clobber.
        if item.worktree_path is not None:
            recorded = (write_root / item.worktree_path).resolve()
            state = classify_recorded_state(
                write_root, recorded_path=recorded, recorded_branch=item.worktree_branch,
            )
            if state == RecordedState.CONSISTENT and recorded != path:
                raise CommandError(
                    f"{qid}: a live worktree is already recorded at {item.worktree_path!r}; "
                    f"prune it first (P5.S2) before adopting a new path."
                )
        branch = linked_worktree_branch(write_root, path)
        if branch is None:
            raise CommandError(f"{qid}: {path} is not a linked worktree of this repository.")
        try:
            rel = path.relative_to(write_root.resolve())
            rel_str = str(rel)
        except ValueError:
            rel_str = str(path)
        item.worktree_path = rel_str
        item.worktree_branch = branch
        item.worktree_in_place = False
        # Adopt clears a previously recorded pruned-at marker; it represents a fresh association.
        item.worktree_pruned_at = None
        _save(write_root, p)
```

- [ ] **Step 3: Run tests**

Run: `cd tools && python -m pytest tasktool/tests/test_worktree_subcommands.py -v -k worktree_adopt`
Expected: PASS.

- [ ] **Step 4: Run the full suite**

Run: `cd tools && python -m pytest tasktool/tests -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/tests/test_worktree_subcommands.py
git commit -m "P5.S1: tasktool worktree adopt"
```

---

## Task 11: Project-setup `.gitignore` enforcement and legacy-dir warnings

**Files:**
- Modify: `skills/project-setup/SKILL.md` (row 1d wording — augment, do not replace)
- Modify: `tools/tasktool/worktree_lifecycle.py` (new helpers: `legacy_worktree_dirs`, `ensure_gitignore_entry`)
- Modify: `tools/tasktool/commands.py` (new `cmd_worktree_ensure_gitignore`, `cmd_worktree_check_legacy`)
- Modify: `tools/tasktool/cli.py` (new `worktree ensure-gitignore` and `worktree check-legacy` subcommands)
- Create: `tools/tasktool/tests/test_project_setup_gitignore.py`

The skill is the authority for the audit. Tasktool ships a pure helper that lists the legacy paths the skill should warn about. This keeps the discovery logic testable in Python without depending on shell installer state.

- [ ] **Step 1: Write the failing helper test**

Create `tools/tasktool/tests/test_project_setup_gitignore.py`:

```python
from pathlib import Path

from tasktool.worktree_lifecycle import legacy_worktree_dirs


def test_legacy_worktree_dirs_detects_each_known_path(tmp_path):
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    (repo / ".claude" / "worktrees").mkdir(parents=True)
    (repo / ".codex" / "worktrees").mkdir(parents=True)
    (home / ".config" / "superstar" / "worktrees" / "demo").mkdir(parents=True)
    found = legacy_worktree_dirs(repo, home=home, project_name="demo")
    expected = {
        repo / ".claude" / "worktrees",
        repo / ".codex" / "worktrees",
        home / ".config" / "superstar" / "worktrees" / "demo",
    }
    assert set(found) == expected


def test_legacy_worktree_dirs_empty_when_none_present(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    assert legacy_worktree_dirs(repo, home=home, project_name="demo") == []


def test_legacy_worktree_dirs_ignores_missing_project_dir(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    (home / ".config" / "superstar" / "worktrees").mkdir(parents=True)
    # No per-project subdir under worktrees/ → no match
    assert legacy_worktree_dirs(repo, home=home, project_name="absent") == []


def test_gitignore_entry_idempotent(tmp_path):
    """F4 acceptance: running the audit twice must not add `.worktrees/` twice."""
    from tasktool.worktree_lifecycle import ensure_gitignore_entry

    repo = tmp_path / "repo"
    repo.mkdir()
    gi = repo / ".gitignore"
    gi.write_text("node_modules/\n")
    # First call adds the entry
    changed_first = ensure_gitignore_entry(repo)
    assert changed_first is True
    text_after_first = gi.read_text()
    assert text_after_first.count(".worktrees/\n") == 1
    # Second call is a no-op
    changed_second = ensure_gitignore_entry(repo)
    assert changed_second is False
    assert gi.read_text() == text_after_first


def test_gitignore_entry_creates_file_when_absent(tmp_path):
    from tasktool.worktree_lifecycle import ensure_gitignore_entry
    repo = tmp_path / "repo"
    repo.mkdir()
    changed = ensure_gitignore_entry(repo)
    assert changed is True
    assert (repo / ".gitignore").read_text() == ".worktrees/\n"
```

- [ ] **Step 2: Implement the helper**

Append to `tools/tasktool/worktree_lifecycle.py`:

```python
def legacy_worktree_dirs(
    repo_root: Path,
    *,
    home: Path,
    project_name: str,
) -> list[Path]:
    """Return any legacy per-harness worktree directories that exist.

    Spec §5.4. Used by `project-setup` to warn the operator. Tasktool does
    NOT delete or move anything — this is detection only. Removal is
    scheduled one minor version after P5 ships.
    """
    candidates = [
        repo_root / ".claude" / "worktrees",
        repo_root / ".codex" / "worktrees",
        home / ".config" / "superstar" / "worktrees" / project_name,
    ]
    return [c for c in candidates if c.exists()]


def ensure_gitignore_entry(repo_root: Path, *, entry: str = ".worktrees/") -> bool:
    """Ensure `entry` (default `.worktrees/`) is a literal line in `<repo>/.gitignore`.

    Idempotent: returns True when the file was created or the line was appended,
    False when the line was already present. Used by `project-setup` row 1d.
    """
    gi = repo_root / ".gitignore"
    if not gi.exists():
        gi.write_text(entry + "\n")
        return True
    text = gi.read_text()
    lines = text.splitlines()
    if any(line.strip() == entry.rstrip("/") or line.strip() == entry for line in lines):
        return False
    sep = "" if text.endswith("\n") else "\n"
    gi.write_text(text + sep + entry + "\n")
    return True
```

- [ ] **Step 3: Wire launcher-backed CLI commands so the skill can invoke without ambient PYTHONPATH**

The reviewer correctly noted (F4 round 2) that `python -c "from tasktool..."` is not reachable from a clean repo-root shell. Add two new launcher-backed subcommands so `project-setup` can call `tools/tasktool/tasktool worktree ensure-gitignore` and `tools/tasktool/tasktool worktree check-legacy`, which the existing launcher already wraps with the correct `PYTHONPATH`.

In `tools/tasktool/commands.py`, add:

```python
def cmd_worktree_ensure_gitignore(*, repo_root: Path) -> str:
    from tasktool.worktree_lifecycle import ensure_gitignore_entry
    changed = ensure_gitignore_entry(repo_root)
    return "added .worktrees/ to .gitignore\n" if changed else ".worktrees/ already ignored\n"


def cmd_worktree_check_legacy(*, repo_root: Path, project_name: str) -> tuple[str, int]:
    from tasktool.worktree_lifecycle import legacy_worktree_dirs
    import os
    home = Path(os.path.expanduser("~"))
    found = legacy_worktree_dirs(repo_root, home=home, project_name=project_name)
    if not found:
        return ("no legacy worktree directories detected\n", 0)
    lines = ["legacy worktree directories detected (warn-only, not removed):"]
    lines.extend(f"  - {p}" for p in found)
    return ("\n".join(lines) + "\n", 1)
```

In `tools/tasktool/cli.py`, extend the `worktree` subparser group (added in Task 8):

```python
    p_wt_gi = wt_sub.add_parser("ensure-gitignore")
    p_wt_legacy = wt_sub.add_parser("check-legacy")
    p_wt_legacy.add_argument("--project", required=True)
```

And in the dispatcher:

```python
            elif args.wt_cmd == "ensure-gitignore":
                sys.stdout.write(commands.cmd_worktree_ensure_gitignore(repo_root=root))
            elif args.wt_cmd == "check-legacy":
                text, rc = commands.cmd_worktree_check_legacy(repo_root=root, project_name=args.project)
                sys.stdout.write(text)
                if rc != 0:
                    return rc
```

(Add a CLI test in `test_worktree_subcommands.py` that asserts `tools/tasktool/tasktool worktree ensure-gitignore` followed by a second invocation produces "added ... " then "already ignored", and that `worktree check-legacy --project demo` exits 0 when no legacy dirs are present and exits non-zero with the directory list when they are.)

- [ ] **Step 4: Update the project-setup skill row 1d**

Open `skills/project-setup/SKILL.md`. Locate the row 1d line (currently at `SKILL.md:31`). Replace it (and the matching reference in the verification step on the line near `SKILL.md:50`) with:

```markdown
| 1d| Implementation worktree location                         | `git check-ignore -q .worktrees/` succeeds **and** `tools/tasktool/tasktool worktree check-legacy --project <name>` exits 0 (no legacy directories). | Run `tools/tasktool/tasktool worktree ensure-gitignore` (idempotent; creates `.gitignore` if absent and appends `.worktrees/` only when missing). If `worktree check-legacy` reports any of `.claude/worktrees/`, `.codex/worktrees/`, or `~/.config/superstar/worktrees/<project>`, **warn** the user (do not delete). Removal is scheduled for the release after P5 ships. Do not create per-slice worktrees here; `[[using-git-worktrees]]` owns that. |
```

And in step 6 verification (currently `SKILL.md:50`), append: `Also re-run \`tools/tasktool/tasktool worktree check-legacy --project <name>\` and surface any reported paths so the operator can decide on manual removal.`

- [ ] **Step 5: Run helper tests**

Run: `cd tools && python -m pytest tasktool/tests/test_project_setup_gitignore.py -v`
Expected: PASS for the helper tests added in step 1 plus the CLI-launcher tests added in step 3.

- [ ] **Step 6: Smoke-test the launcher-backed commands from repo root**

From the project root (no `PYTHONPATH` set):

```bash
./tools/tasktool/tasktool worktree ensure-gitignore
./tools/tasktool/tasktool worktree ensure-gitignore   # second call is a no-op
./tools/tasktool/tasktool worktree check-legacy --project superstar
```

Expected: first call prints `added .worktrees/ to .gitignore` (or `already ignored` if the entry pre-existed), the second call prints `already ignored`, the check-legacy call prints either `no legacy worktree directories detected` (exit 0) or a warning list (exit non-zero).

- [ ] **Step 7: Commit**

```bash
git add tools/tasktool/worktree_lifecycle.py \
        tools/tasktool/commands.py tools/tasktool/cli.py \
        tools/tasktool/tests/test_project_setup_gitignore.py \
        tools/tasktool/tests/test_worktree_subcommands.py \
        skills/project-setup/SKILL.md
git commit -m "P5.S1: launcher-backed gitignore + legacy-check; project-setup row 1d"
```

---

## Task 12: Final verification

- [ ] **Step 1: Run the spec's §10 verification commands**

Run from repo root:

```bash
./tools/tasktool/tasktool validate --strict-format
```

Expected: exit 0 (pre-existing `path does not exist` warnings for the not-yet-written S2/S3 plans are acceptable; no schema errors).

```bash
cd tools && python -m pytest tasktool/tests -q
```

Expected: PASS for ≥ original 391 tests plus all new tests added in this slice (target ≈ 430).

- [ ] **Step 2: Spot-check the new fields on a real start**

From the authoritative checkout (or any linked worktree):

```bash
./tools/tasktool/tasktool show P5.S1
./tools/tasktool/tasktool worktree list
./tools/tasktool/tasktool worktree status P5.S1
```

Expected: `worktree list` shows `P5.S1` with `health=live` (assuming `tasktool start P5.S1` ran at the top of execution); `worktree status` reports clean dirty state.

- [ ] **Step 3: Acceptance criteria mapped to spec §9**

Re-read spec §9 (lines 305-313). For each criterion in P5.S1's scope (1, 5 in part, 8), confirm:
- **AC1**: `tasktool start <id>` is the single entry point for implementation work. The wider phase's skill rewrite (S3) restates this in prose; S1 ships the underlying behavior.
- **AC5**: `tasklist.json` round-trips all four field families (`worktree_path`, `worktree_branch`, `worktree_in_place`, `worktree_pruned_at`); existing tasklists continue to load. Verified by Task 2 tests.
- **AC8**: The naming function in §5.1 produces stable, lowercase, collision-free paths for every fixture in the §5.1 worked-examples table. Verified by Task 1 parametrized tests.

S2 carries ACs 3 & 4; S3 carries ACs 2 & 7. AC6 (installer) is verified by the row-1d audit change in Task 11; no automatic migration runs.

No commit for Task 12 — verification only.

---

## Self-Review Notes

- **Spec §5.1 (naming):** Task 1, parametrized against the §5.1 worked-examples table plus edge cases (empty title, non-ascii, dash collapse, slice followup letter).
- **Spec §5.2 (schema fields):** Task 2, round-trip + validate + schema-gen coverage for both `Slice` and `CrossCutting`.
- **Spec §5.3 default `start`:** Task 4. Idempotent reuse table: Task 5 (each row). `--in-place`: Task 6. `--adopt` (manual + auto): Task 6. `--ad-hoc`: Task 7.
- **Spec §5.3.1 lifecycle table (S1 rows):** `start (fresh)`, `start (idempotent reuse)`, `start --in-place`, `start --adopt`, `start --ad-hoc` — all covered by Tasks 4 / 6 / 7. `close` / prune / repair / finalize / `worktree prune` rows are out of scope.
- **Spec §5.3 `worktree` subcommands (S1 subset):** `list`, `status`, `adopt`. Tasks 8-10. `prune`/`repair`/`--finalize` deferred to S2.
- **Spec §5.4 (installer):** Task 11, with a tested helper for legacy-dir detection and a skill-side audit row that uses it. Tasktool itself does not run the installer; the skill is the operator-facing surface.
- **Spec §6 P5.S1 test list:** Every bullet maps to a test —
  - "Idempotent `start` returns no-op when state is consistent" → Task 4 test.
  - "Each ambiguous-state row in the reuse table fails with the documented guidance" → Task 5, five tests.
  - "`--adopt` records an externally-created linked worktree and refuses non-worktree paths" → Task 6, two tests.
  - "Auto-adopt fires when cwd is already inside a linked worktree of the parent repo" → Task 6 test.
  - "`--in-place` records the audit marker and leaves `worktree_path` null" → Task 6 test.
  - "Schema round-trip: write new fields, re-read, validate" → Task 2 tests.
  - "Installer adds `.gitignore` entry exactly once and warns (does not delete) on legacy dirs" → Task 11 covers detection (`legacy_worktree_dirs`) and idempotence (`ensure_gitignore_entry` is unit-tested for "no double-write on second call"). The launcher-backed CLI commands `worktree ensure-gitignore` and `worktree check-legacy` are the operator-facing surface and are CLI-tested from a clean repo-root shell (no ambient `PYTHONPATH` assumed). The `project-setup` skill row 1d calls those CLI commands, so the audit gate is executable end-to-end without invoking Python by hand.

- **Scope discipline:** No file added under `tools/tasktool/` introduces a function named `prune`, `repair`, `finalize`, or anything subagent-env-var related. The schema reserves `worktree_pruned_at` / `worktree_prune_pending` / `worktree_prune_pending_at` so S2 can write them without a re-migration; S1 reads them only in `_health_for` (treating a row with `worktree_pruned_at` set and no `worktree_path` as "pruned" in `worktree list --all`).

- **No new ID grammar:** `--ad-hoc` reuses the existing `X<n>` family via `next_cross_id`. `ids.py` is unchanged.

- **`tasktool close` is untouched:** Spec §5.3 explicitly preserves `close` semantics. No edits to `cmd_close` in this slice.

- **Type consistency check:** All callers of `worktree_name(id, title)`, `classify_recorded_state(authoritative_root, recorded_path=..., recorded_branch=...)`, `linked_worktree_branch(root, candidate)`, and `is_inside_linked_worktree(cwd)` use the signatures defined in Tasks 1 and 3. `_apply_start_default`, `_apply_start_in_place`, `_apply_start_adopt`, `_health_for`, `cmd_worktree_list`, `cmd_worktree_status`, `cmd_worktree_adopt`, and `_start_ad_hoc` are all introduced together in Tasks 4 / 6 / 7 / 8 / 9 / 10 with matching call sites.

- **Backward compatibility:** Slices and cross-cutting rows without the new fields load unchanged because every field defaults. Existing `tasktool validate` runs against the live tasklist continue to pass (verified at end of Task 2 and Task 12).
