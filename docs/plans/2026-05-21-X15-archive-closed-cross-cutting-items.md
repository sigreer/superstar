# Archive Closed Cross-Cutting Items Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add lossless archive support for completed `X*` cross-cutting items, with default archive-on-close, `--no-archive`, and manual `archive-cross`.

**Architecture:** Extend the tasktool model with an `archived_cross_cutting` pointer list, then route all X-item archive behavior through command helpers that mirror phase archive atomicity: build archive content in memory, mutate project state in memory, validate, write files, save, stage, notify. Rendering, schema, migration, and tasklist-discipline docs consume the new model field without changing phase archival behavior.

**Tech Stack:** Python dataclasses, tasktool CLI, canonical JSON serialization, unittest/pytest tests under `tools/tasktool/tests`.

---

## File Structure

- Modify `tools/tasktool/model.py` to add `ArchivedCrossCutting` and `Project.archived_cross_cutting`.
- Modify `tools/tasktool/serialize.py` to load/save the new field while preserving legacy tasklists that omit it.
- Modify `tools/tasktool/validate.py` to validate archived X pointer IDs, dates, paths, duplicates, and active/archive collisions.
- Modify `tools/tasktool/schema_gen.py` so `tasktool schema` includes `archived_cross_cutting`.
- Modify `tools/tasktool/migrate.py` so drift migration treats archived X pointers as a top-level collection.
- Modify `tools/tasktool/commands.py` to add `cmd_archive_cross`, default archive-on-close for crosscuts, `--no-archive` enforcement, archive markdown writing, and friendly archived-not-found checks.
- Modify `tools/tasktool/cli.py` to add `close --no-archive` and `archive-cross`.
- Modify `tools/tasktool/render.py` to render archived X pointers separately.
- Verify `tools/tasktool/brief.py` keeps archived X-items outside the active brief surface.
- Modify `skills/tasklist-discipline/SKILL.md` to document X-item close/archive behavior.
- Add or extend tests in `tools/tasktool/tests/test_commands.py`, `test_validate.py`, `test_render.py`, `test_migrate.py`, `test_schema_gen.py`, and CLI integration tests as needed.

## Execution Setup

- [ ] **Step 1: Start from an isolated implementation worktree**

Run from the repository root:

```sh
git status --short
tools/tasktool/tasktool show X15
```

Expected: `X15` exists and references:

```text
docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md
docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md
```

If execution is happening in a new worktree, run the task lifecycle start before editing implementation files. Current `cmd_start` resolves all tasktool row kinds through `_find_item`, so cross-cutting IDs are supported:

```sh
tools/tasktool/tasktool start X15
```

Expected: `X15` moves to `in_progress`.

## Task 1: Model, Serialization, Schema, and Migration

**Files:**
- Modify: `tools/tasktool/model.py`
- Modify: `tools/tasktool/serialize.py`
- Modify: `tools/tasktool/schema_gen.py`
- Modify: `tools/tasktool/migrate.py`
- Modify: `tools/tasktool/tests/test_migrate.py`
- Add or modify: `tools/tasktool/tests/test_schema_gen.py`

- [ ] **Step 1: Add failing model/migration tests**

Append tests to `tools/tasktool/tests/test_migrate.py`:

```python
from tasktool.model import ArchivedCrossCutting


def test_archived_cross_cutting_drift_migrates():
    local = _project_with_slice()
    local.archived_cross_cutting.append(
        ArchivedCrossCutting(
            id="X1",
            title="archived cross",
            archived_path="docs/archived-tasks/X1-archived-cross.md",
            archived_date=_today(),
        )
    )
    authoritative = _project_with_slice()

    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)
    merged = apply_deltas(
        authoritative=authoritative,
        local=local,
        deltas=deltas,
        conflicts=conflicts,
        policy="accept-local",
    )

    assert any(d.kind == "add" and d.row_id == "X1" for d in deltas)
    assert merged.archived_cross_cutting[0].id == "X1"
```

Update the existing imports and parametrization in the same file so `ArchivedCrossCutting` is included anywhere `ArchivedPhase` appears in field coverage:

```python
from tasktool.model import (
    ArchivedCrossCutting,
    ArchivedPhase,
    CrossCutting,
    Phase,
    Project,
    Slice,
    Status,
    Task,
)
```

Add `ArchivedCrossCutting` to:

```python
for row_type in (Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, ArchivedCrossCutting):
```

and:

```python
[Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, ArchivedCrossCutting]
```

Extend `_value_pair_for_field`:

```python
if field.name in {"id", "phases", "slices", "tasks", "cross_cutting", "archived_phases", "archived_cross_cutting"}:
    return (None, None)
```

Extend `set_on`/`get_on`:

```python
elif type_ is ArchivedCrossCutting:
    if not tree.archived_cross_cutting:
        tree.archived_cross_cutting.append(
            ArchivedCrossCutting(
                id="X0",
                title="archived cross",
                archived_path="docs/archived-tasks/X0-archived-cross.md",
                archived_date=_today(),
            )
        )
    setattr(tree.archived_cross_cutting[0], f.name, value)
```

```python
if type_ is ArchivedCrossCutting:
    return getattr(tree.archived_cross_cutting[0], f.name)
```

- [ ] **Step 2: Add failing schema test**

Create `tools/tasktool/tests/test_schema_gen.py` if absent:

```python
from tasktool.schema_gen import build_schema


def test_schema_includes_archived_cross_cutting():
    schema = build_schema()
    properties = schema["properties"]
    assert "archived_cross_cutting" in properties
    archived = properties["archived_cross_cutting"]["items"]
    assert archived["required"] == ["id", "title", "archived_path", "archived_date"]
    assert archived["properties"]["id"]["pattern"] == r"^X\d+$"
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```sh
python3 -m pytest tools/tasktool/tests/test_migrate.py tools/tasktool/tests/test_schema_gen.py -q
```

Expected: failures for missing `ArchivedCrossCutting`, missing project field, and missing schema property.

- [ ] **Step 4: Implement model and serialization**

In `tools/tasktool/model.py`, add:

```python
@dataclass(slots=True)
class ArchivedCrossCutting:
    id: str
    title: str
    archived_path: str
    archived_date: str
```

Add the new field to `Project`:

```python
archived_cross_cutting: list[ArchivedCrossCutting] = field(default_factory=list)
```

In `tools/tasktool/serialize.py`, import the new dataclass:

```python
Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, ArchivedCrossCutting, BlockedOn,
```

Add loader helper:

```python
def _arch_cross(ad):
    return ArchivedCrossCutting(
        id=ad["id"], title=ad["title"],
        archived_path=ad["archived_path"], archived_date=ad["archived_date"],
    )
```

Add the field when constructing `Project`:

```python
archived_cross_cutting=[_arch_cross(a) for a in d.get("archived_cross_cutting", [])],
```

Add a legacy-load test in a serialization-focused test file:

```python
def test_legacy_tasklist_without_archived_cross_cutting_loads():
    project = loads_project(
        json.dumps(
            {
                "project": "demo",
                "schema_version": 1,
                "phases": [],
                "cross_cutting": [],
                "archived_phases": [],
            }
        )
    )

    assert project.archived_cross_cutting == []
```

- [ ] **Step 5: Implement schema and migration**

In `tools/tasktool/schema_gen.py`, create a dedicated archived X schema or reuse the archived pointer shape with an X pattern:

```python
archived_cross = {
    "type": "object",
    "required": ["id", "title", "archived_path", "archived_date"],
    "properties": {
        "id": {"type": "string", "pattern": r"^X\d+$"},
        "title": {"type": "string"},
        "archived_path": {"type": "string"},
        "archived_date": date_str,
    },
    "additionalProperties": False,
}
```

Add to top-level properties:

```python
"archived_cross_cutting": {"type": "array", "items": archived_cross},
```

In `tools/tasktool/migrate.py`, update imports:

```python
from tasktool.model import ArchivedCrossCutting, ArchivedPhase, CrossCutting, Phase, Project, Slice, Task
```

Update:

```python
_PROJECT_COLLECTIONS = ("phases", "cross_cutting", "archived_phases", "archived_cross_cutting")
```

Add to `walker_field_coverage`:

```python
"ArchivedCrossCutting": {field.name for field in fields(ArchivedCrossCutting)},
```

Add `_diff_collection` and `_apply_collection` calls for `archived_cross_cutting`, using `ArchivedCrossCutting`.

In `_diff_project`, mirror the existing `archived_phases` block:

```python
    _diff_collection(
        local_rows=local.archived_cross_cutting,
        authoritative_rows=authoritative.archived_cross_cutting,
        id_prefix="",
        row_dataclass=ArchivedCrossCutting,
        nested=[],
        deltas=deltas,
        conflicts=conflicts,
    )
```

In `_apply_local`, mirror the existing `archived_phases` block:

```python
    _apply_collection(
        authoritative_rows=merged.archived_cross_cutting,
        local_rows=local.archived_cross_cutting,
        deltas=deltas,
        id_prefix="",
        nested=[],
    )
```

- [ ] **Step 6: Run focused tests**

Run:

```sh
python3 -m pytest tools/tasktool/tests/test_migrate.py tools/tasktool/tests/test_schema_gen.py -q
```

Expected: pass.

## Task 2: Validation and Rendering

**Files:**
- Modify: `tools/tasktool/validate.py`
- Modify: `tools/tasktool/render.py`
- Modify: `tools/tasktool/tests/test_validate.py`
- Modify: `tools/tasktool/tests/test_render.py`

- [ ] **Step 1: Add failing validation tests**

Add imports to `tools/tasktool/tests/test_validate.py`:

```python
from tasktool.model import ArchivedCrossCutting
```

Add tests:

```python
def test_validate_rejects_duplicate_archived_cross_ids():
    p = Project(project="demo")
    p.archived_cross_cutting.extend([
        ArchivedCrossCutting(id="X1", title="one", archived_path="docs/archived-tasks/X1-one.md", archived_date="2026-05-21"),
        ArchivedCrossCutting(id="X1", title="two", archived_path="docs/archived-tasks/X1-two.md", archived_date="2026-05-21"),
    ])

    with pytest.raises(ValidationError, match="duplicate archived cross id X1"):
        validate_project(p)


def test_validate_rejects_active_and_archived_cross_id_collision():
    p = Project(project="demo")
    p.cross_cutting.append(CrossCutting(id="X1", title="active", created="2026-05-21"))
    p.archived_cross_cutting.append(
        ArchivedCrossCutting(id="X1", title="archived", archived_path="docs/archived-tasks/X1-archived.md", archived_date="2026-05-21")
    )

    with pytest.raises(ValidationError, match="X1 appears in both active and archived cross-cutting"):
        validate_project(p)


def test_validate_rejects_malformed_archived_cross_date_and_path():
    p = Project(project="demo")
    p.archived_cross_cutting.append(
        ArchivedCrossCutting(id="X1", title="archived", archived_path="", archived_date="20260521")
    )

    with pytest.raises(ValidationError):
        validate_project(p)
```

- [ ] **Step 2: Add failing render test**

In `tools/tasktool/tests/test_render.py`, import `ArchivedCrossCutting` and add:

```python
def test_render_shows_archived_cross_section():
    p = Project(project="demo")
    p.cross_cutting.append(CrossCutting(id="X1", title="active cross", created="2026-05-21"))
    p.archived_cross_cutting.append(
        ArchivedCrossCutting(
            id="X2",
            title="archived cross",
            archived_path="docs/archived-tasks/X2-archived-cross.md",
            archived_date="2026-05-21",
        )
    )

    out = render_project(p)

    assert "## Cross-cutting (`X*`)" in out
    assert "## Archived cross-cutting (`X*`)" in out
    active_section, archived_section = out.split("## Archived cross-cutting (`X*`)", 1)
    assert "**X1**" in active_section
    assert "**X2**" not in active_section
    assert "**X2**" in archived_section
    assert "docs/archived-tasks/X2-archived-cross.md" in archived_section
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```sh
python3 -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_render.py -q
```

Expected: failures until validation/rendering know the new field.

- [ ] **Step 4: Implement validation**

In `tools/tasktool/validate.py`, import `ArchivedCrossCutting` and add:

```python
def _check_archived_cross(c: ArchivedCrossCutting, scope: str) -> None:
    _check_id(c.id, _CROSS_RE, scope)
    _require(bool(c.title.strip()), f"{scope}: archived cross title is required")
    _require(bool(c.archived_path.strip()), f"{scope}: archived_path is required")
    _check_date(c.archived_date, scope, "archived_date")
```

Before using those helpers, verify the current signatures in `validate.py`:

```sh
rg -n "def _check_date|_CROSS_RE" tools/tasktool/validate.py
```

Expected: `_CROSS_RE` exists and `_check_date` accepts `(value, scope, field)`.

In `validate_project`, after active cross validation:

```python
seen_archived_cross: set[str] = set()
for c in p.archived_cross_cutting:
    _require(c.id not in seen_archived_cross, f"X*: duplicate archived cross id {c.id}")
    _require(c.id not in seen_cross, f"{c.id} appears in both active and archived cross-cutting")
    seen_archived_cross.add(c.id)
    _check_archived_cross(c, c.id)
```

In `collect_known_ids`, add:

```python
for x in getattr(p, "archived_cross_cutting", []) or []:
    ids.add(x.id if hasattr(x, "id") else x["id"])
```

- [ ] **Step 5: Implement rendering**

In `tools/tasktool/render.py`, after archived phases:

```python
    if getattr(p, "archived_cross_cutting", None):
        lines += ["## Archived cross-cutting (`X*`)", ""]
        for a in p.archived_cross_cutting:
            lines.append(
                f"- **{a.id}** — {a.title} → [`{a.archived_path}`]({a.archived_path}) ({a.archived_date})"
            )
        lines.append("")
```

- [ ] **Step 6: Run focused tests**

Run:

```sh
python3 -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_render.py -q
```

Expected: pass.

## Task 3: Archive Commands and CLI

**Files:**
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/cli.py`
- Modify: `tools/tasktool/tests/test_commands.py`
- Modify: `tools/tasktool/tests/test_cli_integration.py`

- [ ] **Step 1: Add failing command tests**

In `tools/tasktool/tests/test_commands.py`, import `ValidationError` if needed:

```python
from tasktool.validate import ValidationError
```

Add tests:

```python
class CrossArchiveTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")

    def tearDown(self):
        self.t.cleanup()

    def test_close_cross_archives_by_default(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="archive me")

        commands.cmd_close(repo_root=self.t.root, id="X1")

        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.cross_cutting, [])
        self.assertEqual(p.archived_cross_cutting[0].id, "X1")
        archive_path = self.t.root / p.archived_cross_cutting[0].archived_path
        self.assertTrue(archive_path.exists())
        self.assertIn('"id": "X1"', archive_path.read_text(encoding="utf-8"))

    def test_close_cross_no_archive_keeps_visible(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="keep visible")

        commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)

        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.cross_cutting[0].status, Status.DONE)
        self.assertEqual(p.archived_cross_cutting, [])

    def test_archive_cross_archives_done_visible_item(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="later")
        commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)

        commands.cmd_archive_cross(repo_root=self.t.root, id="X1")

        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.cross_cutting, [])
        self.assertEqual(p.archived_cross_cutting[0].id, "X1")

    def test_archive_cross_rejects_ready_item(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="not done")

        with self.assertRaisesRegex(commands.CommandError, "must be done before archive"):
            commands.cmd_archive_cross(repo_root=self.t.root, id="X1")

    def test_close_no_archive_rejects_non_cross_items(self):
        commands.cmd_create_phase(repo_root=self.t.root, title="phase")

        with self.assertRaisesRegex(commands.CommandError, "--no-archive is only valid for cross-cutting items"):
            commands.cmd_close(repo_root=self.t.root, id="P1", no_archive=True, skip_review_gate=True)

    def test_archive_cross_preserves_full_json(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="full data")
        commands.cmd_close(
            repo_root=self.t.root,
            id="X1",
            no_archive=True,
            refs=["docs/specs/example.md"],
            note="important note",
        )

        commands.cmd_archive_cross(repo_root=self.t.root, id="X1")

        p = load_project(self.t.root / "docs/tasklist.json")
        text = (self.t.root / p.archived_cross_cutting[0].archived_path).read_text(encoding="utf-8")
        self.assertIn('"id": "X1"', text)
        self.assertIn('"refs": [', text)
        self.assertIn('"docs/specs/example.md"', text)
        self.assertIn('"notes": "important note"', text)

    def test_close_archived_cross_reports_archived_hint(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="already archived")
        commands.cmd_close(repo_root=self.t.root, id="X1")

        with self.assertRaisesRegex(commands.CommandError, "may already be archived"):
            commands.cmd_close(repo_root=self.t.root, id="X1")

    def test_brief_archived_cross_is_not_active_surface(self):
        from tasktool.brief import brief

        commands.cmd_create_cross(repo_root=self.t.root, title="brief archived")
        commands.cmd_close(repo_root=self.t.root, id="X1")
        p = load_project(self.t.root / "docs/tasklist.json")

        with self.assertRaisesRegex(ValueError, "X1: not found"):
            brief(p, "X1")

    def test_archive_cross_atomicity_no_orphan_file_on_validation_failure(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="atomic")
        commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)

        with patch("tasktool.commands.validate_project", side_effect=ValidationError("forced")):
            with self.assertRaises(ValidationError):
                commands.cmd_archive_cross(repo_root=self.t.root, id="X1")

        self.assertFalse((self.t.root / "docs/archived-tasks/X1-atomic.md").exists())
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.cross_cutting[0].id, "X1")

    def test_archive_cross_does_not_reemit_done_notification(self):
        commands.cmd_create_cross(repo_root=self.t.root, title="notify once")
        log = self.t.root / "notify.jsonl"
        with patch.dict(
            os.environ,
            {"SUPERSTAR_NOTIFY_DISABLE": "0", "SUPERSTAR_NOTIFY_DRY_RUN": "1", "SUPERSTAR_NOTIFY_LOG": str(log)},
        ):
            commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)
            commands.cmd_archive_cross(repo_root=self.t.root, id="X1")

        events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        done_events = [event for event in events if event["id"] == "X1" and event["status"] == "done"]
        self.assertEqual(len(done_events), 1)
```

- [ ] **Step 2: Add failing CLI tests**

In `tools/tasktool/tests/test_cli_integration.py`, add CLI-level coverage following existing helper patterns:

```python
def test_cli_close_cross_no_archive_keeps_visible(tmp_path):
    root = init_repo(tmp_path)
    run_tasktool(root, "create", "cross", "--title", "visible")

    run_tasktool(root, "close", "X1", "--no-archive")

    project = load_project(root / "docs/tasklist.json")
    assert project.cross_cutting[0].id == "X1"
    assert project.cross_cutting[0].status == Status.DONE
    assert project.archived_cross_cutting == []


def test_cli_archive_cross_moves_done_item(tmp_path):
    root = init_repo(tmp_path)
    run_tasktool(root, "create", "cross", "--title", "later")
    run_tasktool(root, "close", "X1", "--no-archive")

    run_tasktool(root, "archive-cross", "X1")

    project = load_project(root / "docs/tasklist.json")
    assert project.cross_cutting == []
    assert project.archived_cross_cutting[0].id == "X1"
```

Add list behavior coverage using the same helpers:

```python
def test_cli_list_kind_cross_excludes_archived_items(tmp_path):
    root = init_repo(tmp_path)
    run_tasktool(root, "create", "cross", "--title", "archived")
    run_tasktool(root, "create", "cross", "--title", "active")
    run_tasktool(root, "close", "X1")

    result = run_tasktool(root, "list", "--kind", "cross")

    assert "X1" not in result.stdout
    assert "X2" in result.stdout
```

Use the actual helper names in `test_cli_integration.py`; if they differ from `init_repo` or `run_tasktool`, adapt only the helper calls, not the assertions.

- [ ] **Step 3: Run tests to verify failure**

Run:

```sh
python3 -m pytest tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_cli_integration.py -q
```

Expected: failures for missing `no_archive`, `cmd_archive_cross`, and CLI parser support.

- [ ] **Step 4: Implement archive helpers in commands**

In `tools/tasktool/commands.py`, import `json`, `asdict`, and `ArchivedCrossCutting`:

```python
import json as _json
from dataclasses import asdict as _asdict
```

Add helper:

```python
def _archive_cross_at_root(write_root: Path, p: Project, item: CrossCutting) -> tuple[Path, str]:
    from tasktool.model import ArchivedCrossCutting

    if item.status != Status.DONE:
        raise CommandError(f"cross-cutting {item.id} must be done before archive; run tasktool close {item.id} first")
    if any(a.id == item.id for a in p.archived_cross_cutting):
        raise CommandError(f"cross-cutting {item.id} is already archived")

    slug = _slugify(item.title)
    archive_rel = f"docs/archived-tasks/{item.id}-{slug}.md"
    archive_path = write_root / archive_rel
    if archive_path.exists():
        raise CommandError(f"archive path already exists: {archive_rel}")

    def _coerce_cross_json(node):
        if isinstance(node, Status):
            return node.value
        if isinstance(node, dict):
            return {key: _coerce_cross_json(value) for key, value in node.items()}
        if isinstance(node, list):
            return [_coerce_cross_json(value) for value in node]
        return node

    cross_json = _json.dumps(
        _coerce_cross_json(_asdict(item)),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"
    summary_lines = [f"# {item.id} - {item.title}", "", f"status: {item.status.value}"]
    summary_lines.append(f"created: {item.created}")
    if item.started:
        summary_lines.append(f"started: {item.started}")
    if item.closed:
        summary_lines.append(f"closed: {item.closed}")
    if item.refs:
        summary_lines += ["", "## References", ""]
        summary_lines.extend(f"- {ref}" for ref in item.refs)
    if item.notes:
        summary_lines += ["", "## Notes", "", item.notes]
    summary_lines += [
        "",
        "## Full cross-cutting JSON (for tasktool unarchive)",
        "",
        "```json",
        cross_json.rstrip(),
        "```",
        "",
    ]

    p.cross_cutting = [cross for cross in p.cross_cutting if cross.id != item.id]
    p.archived_cross_cutting.append(
        ArchivedCrossCutting(
            id=item.id,
            title=item.title,
            archived_path=archive_rel,
            archived_date=_today(),
        )
    )
    validate_project(p)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text("\n".join(summary_lines), encoding="utf-8")
    return archive_path, archive_rel
```

This deliberately uses a bare X-item JSON object, not a wrapper `Project`, so the archive shape matches the spec and a future `unarchive-cross` can parse a single row directly. Keep the archive heading ASCII hyphenated (`# X1 - title`) to match this spec's file examples and the repo's default ASCII editing style.

- [ ] **Step 5: Wire close behavior**

Change `cmd_close` signature:

```python
no_archive: bool = False,
```

After resolving `kind`, reject non-cross opt-out:

```python
if no_archive and kind != "cross":
    raise CommandError("--no-archive is only valid for cross-cutting items")
```

Replace the existing `cmd_close` tail that currently does `_save(write_root, p)` and `_notify_status(...)` with a single unified tail. Do not leave the old save/notify calls in place.

After status/refs/notes are applied, archive X-items unless opted out:

```python
archive_path: Path | None = None
if kind == "cross" and not no_archive:
    archive_path, _archive_rel = _archive_cross_at_root(write_root, p, item)
_save(write_root, p)
if archive_path is not None:
    _git_stage(write_root, archive_path)
_notify_status(qid=qid, kind=kind, status=item.status, title=item.title)
```

If `_archive_cross_at_root` mutates `p.cross_cutting`, make sure `_notify_status` still uses the local `item` reference captured before removal.

- [ ] **Step 6: Add manual command**

Add:

```python
def cmd_archive_cross(*, repo_root: Path, id: str) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        kind = parse_id(qid)[0]
        if kind != "cross":
            raise CommandError("archive-cross only works on cross-cutting items")
        archive_path, _archive_rel = _archive_cross_at_root(write_root, p, item)
        _save(write_root, p)
        _git_stage(write_root, archive_path)
```

Add an explicit precheck before `_find_item` in `cmd_close` and `cmd_archive_cross`:

```python
def _raise_if_archived_cross(p: Project, id: str, *, for_close: bool) -> None:
    if parse_id(id)[0] != "cross":
        return
    if any(item.id == id for item in p.archived_cross_cutting):
        if for_close:
            raise CommandError(f"cross-cutting {id} not found in active tasklist; it may already be archived")
        raise CommandError(f"cross-cutting {id} is already archived")
```

Call it after loading `p` and before `_find_item`.

- [ ] **Step 7: Wire CLI**

In `tools/tasktool/cli.py`, add:

```python
p_close.add_argument("--no-archive", action="store_true")
```

Pass it into `cmd_close`:

```python
no_archive=args.no_archive,
```

Add parser:

```python
p_arch_cross = sub.add_parser("archive-cross")
p_arch_cross.add_argument("id")
```

Add dispatch:

```python
elif args.cmd == "archive-cross":
    commands.cmd_archive_cross(repo_root=root, id=args.id)
```

- [ ] **Step 8: Run focused tests**

Run:

```sh
python3 -m pytest tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_cli_integration.py -q
```

Expected: pass.

## Task 4: Documentation

**Files:**
- Modify: `skills/tasklist-discipline/SKILL.md`
- Modify: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`

- [ ] **Step 1: Add or update doc test**

Inspect `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` and add assertions that the skill documents:

```python
assert "tasktool close X" in text
assert "--no-archive" in text
assert "archive-cross" in text
```

- [ ] **Step 2: Run doc test to verify failure**

Run:

```sh
python3 -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
```

Expected: failure until the skill is updated.

- [ ] **Step 3: Update tasklist-discipline**

In `skills/tasklist-discipline/SKILL.md`, add a short subsection near the cross-cutting command docs:

```md
## Cross-cutting archive behavior

`tasktool close X12` closes and archives the X-item by default. The row moves out of active `cross_cutting`, a lossless archive file is written under `docs/archived-tasks/`, and a compact pointer is kept in `archived_cross_cutting`.

Use `tasktool close X12 --no-archive` when a completed crosscut should remain visible in the active tasklist for now. Later, run `tasktool archive-cross X12` to move a done-but-visible X-item into the archive.
```

Use a four-backtick outer fence if this text is placed inside another fenced example.

- [ ] **Step 4: Run doc test**

Run:

```sh
python3 -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
```

Expected: pass.

## Task 5: Full Verification and Closeout

**Files:**
- Modify: `docs/tasklist.json`
- Modify or create: `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/*`

- [ ] **Step 1: Run full tasktool tests**

Run:

```sh
tools/tasktool/tasktool validate --strict-format
python3 -m pytest tools/tasktool/tests -q
```

Expected: validation prints `ok`; pytest passes.

- [ ] **Step 2: Render a manual smoke check**

Run:

```sh
tools/tasktool/tasktool render | rg -n "Cross-cutting|Archived cross-cutting|X15"
```

Expected: active and archived crosscut sections render without malformed markdown. `X15` appears according to its current status at the time of the smoke check.

- [ ] **Step 3: Run external post-slice review**

Run:

```sh
external-reviewer review \
  --kind post-slice \
  --file docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md \
  --work-id X15 \
  --context docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md \
  --context docs/tasklist.json \
  --review-depth thorough \
  --caller-provider codex \
  --reviewer-provider claude \
  --emit json
```

Expected: `merged_verdict` is `ready` or `ready with small edits`. If reviewer returns `revise`, write `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/rN-resolution.md`, apply fixes, rerun tests, and resubmit.

- [ ] **Step 4: Close X15**

Because `X15` is itself a cross-cutting item and this feature changes default X close behavior, close it explicitly without archiving if the archive implementation is not meant to archive its own delivery row immediately:

```sh
tools/tasktool/tasktool close X15 --no-archive
```

If the operator wants to exercise the new default archive path on the delivery row, omit `--no-archive`.

Expected: `X15` is `done`, and close behavior matches the chosen flag.

- [ ] **Step 5: Commit implementation**

Before committing finished work that changes `skills/` or `tools/`, ask the user whether to bump the Superstar plugin version, per `AGENTS.md`.

If the user says no version bump:

```sh
git status --short
git add tools/tasktool skills/tasklist-discipline/SKILL.md docs/tasklist.json docs/reviewer docs/archived-tasks
git commit -m "tasktool: archive closed cross-cutting items"
```

If the user says to bump, run `./scripts/bump-version.sh <new-version>` and commit that bump separately before publish/sync scripts.
