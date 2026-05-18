# P2.S2 — tasktool importer / render / brief / archive-phase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the four S2 commands to `tasktool` (`import`, `render`, `brief`, `archive-phase`), then migrate this repository from `docs/TASKLIST.md` to `docs/tasklist.json`. End state: `docs/TASKLIST.md` is deleted, `docs/tasklist.json` is the canonical tracker, `tasktool render` reproduces a semantically-equivalent markdown view on demand, and `tasktool brief P2.S2` returns the start-of-work primer for the next agent that picks up work in this phase.

**Architecture:** Three new pure modules under `tools/tasktool/` — `importer.py` (markdown→Project), `render.py` (Project→markdown), `brief.py` (Project→primer markdown). `commands.py` grows four new `cmd_*` functions; `cli.py` grows four subparsers. The new modules follow the S1 layering rule: pure, side-effect-free, tested in isolation; `commands` is the only disk-touching orchestrator. `archive-phase` extends `commands` with a new orchestrator that reuses `reviewer_gate.check_gate` (via `_apply_review_gate`'s `phase` branch) and adds an `ArchivedPhase` record alongside writing a markdown summary.

**Tech Stack:** Python 3.11+ (stdlib only — `re`, `pathlib`, `json`, `datetime`, `argparse`, `unittest`). Zero third-party deps. Same conventions as S1.

---

## File structure

Created in this slice:

```
tools/tasktool/
├── importer.py             # parse TASKLIST.md → Project (best-effort, lossy-by-design)
├── render.py               # Project → markdown view (not byte-identical to old TASKLIST.md)
├── brief.py                # Project + id → start-of-work primer markdown
└── tests/
    ├── test_importer.py
    ├── test_render.py
    └── test_brief.py
```

Modified in this slice:

```
tools/tasktool/
├── commands.py             # +cmd_import / +cmd_render / +cmd_brief / +cmd_archive_phase
├── cli.py                  # +import / +render / +brief / +archive-phase subparsers
├── __init__.py             # re-export importer.parse_tasklist_md, render.render_project, brief.brief
└── tests/
    ├── test_commands.py    # +cmd_archive_phase tests
    └── test_cli_integration.py   # +import/render/brief/archive-phase CLI tests
```

Repo files touched at migration time (Task 11):

```
docs/
├── tasklist.json           # NEW, canonical
├── TASKLIST.md             # DELETED
└── archived-tasks/         # may receive P1 summary if --archive-historical is used
```

Not touched in this slice: `tools/tasktool/templates/pre-commit-tasktool` (S3); any sibling skills (S3).

---

## Conventions used throughout

- **TDD:** every task writes the failing test, runs it red, implements the minimum, runs it green, commits. Commits per task, not per step.
- **Commit message prefix:** `P2.S2:` followed by an imperative one-liner.
- **Run tests via:** `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`.
- **No third-party deps.** Stdlib only.
- **Python style:** dataclasses with `slots=True`; `from __future__ import annotations` everywhere; type hints on public functions.
- **Pure modules return data; commands print/save.** `importer.parse_tasklist_md(text) -> ParseResult`, `render.render_project(p) -> str`, `brief.brief(p, qid) -> str`. None of those touch disk.
- **Status emoji table** — applies *by kind*. The data model only allows `blocked` on slices (spec §6.6, enforced by `validate.py`). Importer/renderer must respect this:

  | emoji | status        | extra tag suffix              | valid on   |
  |-------|---------------|-------------------------------|------------|
  | ✅    | `done`        | `DONE YYYY-MM-DD`             | phase/slice/task/cross |
  | 🚧    | `in_progress` | `IN PROGRESS`                 | phase/slice/task/cross |
  | ⏸     | `blocked`     | `BLOCKED on <text>`           | **slice only** |
  | ☐     | `ready`       | `READY` / `TODO` (interchangeable on import; render emits `READY`) | phase/slice/task/cross |

  **Importer rule:** a `⏸ blocked` marker on a phase or cross-cutting bullet emits a warning (`f"line {lineno}: blocked status not allowed on {kind}; coerced to ready"`) and the parser falls back to `Status.READY`. **Render rule:** `_phase_tag` and the cross-cutting render branch only emit a `BLOCKED on …` tag for slices; on a phase/cross the function returns `""` even if status somehow == blocked (the validator rejects that on save, but the renderer must also never produce invalid markdown).

---

## Task 1: Importer — phase header parsing

**Files:**
- Create: `tools/tasktool/importer.py`
- Create: `tools/tasktool/tests/test_importer.py`

The importer is the riskiest module because the input is hand-written markdown. We build it incrementally: phases first, then slices, then cross-cutting, then archived references. Each task adds one parser concern with fixtures.

`parse_tasklist_md(text: str) -> ParseResult` returns:

```python
@dataclass(slots=True)
class ParseResult:
    project: Project           # parsed model (may be partial on errors)
    warnings: list[str]        # unparsed lines / ambiguous tokens
```

The parser is **forgiving**: it never raises on malformed input. Anything it cannot interpret becomes a warning (line number + offending text). The caller decides whether to abort.

- [ ] **Step 1: Write the failing test**

```python
# tools/tasktool/tests/test_importer.py
from __future__ import annotations
import unittest
from tasktool.importer import parse_tasklist_md
from tasktool.model import Status

PHASE_HEADER = """\
# Project Task List

## P2 — tasktool: JSON-backed task management CLI 🚧 `IN PROGRESS`

Spec: [`docs/specs/2026-05-17-P2-tasktool-design.md`](specs/2026-05-17-P2-tasktool-design.md). Plan: _pending_.
"""

PHASE_HEADER_DONE = """\
## P1 — Old phase ✅ `DONE 2026-05-17`

Closed; see archive.
"""

class TestImporterPhase(unittest.TestCase):
    def test_phase_header_basic(self):
        r = parse_tasklist_md(PHASE_HEADER)
        self.assertEqual(len(r.project.phases), 1)
        ph = r.project.phases[0]
        self.assertEqual(ph.id, "P2")
        self.assertEqual(ph.title, "tasktool: JSON-backed task management CLI")
        self.assertEqual(ph.status, Status.IN_PROGRESS)
        self.assertEqual(ph.spec_path, "docs/specs/2026-05-17-P2-tasktool-design.md")
        self.assertIsNone(ph.plan_path)  # "_pending_" → None

    def test_phase_done_tag_sets_closed(self):
        r = parse_tasklist_md(PHASE_HEADER_DONE)
        self.assertEqual(len(r.project.phases), 1)
        ph = r.project.phases[0]
        self.assertEqual(ph.id, "P1")
        self.assertEqual(ph.status, Status.DONE)
        self.assertEqual(ph.closed, "2026-05-17")  # required for validator pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_importer -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tasktool.importer'`.

- [ ] **Step 3: Write minimal implementation**

```python
# tools/tasktool/importer.py
from __future__ import annotations
import re
from dataclasses import dataclass, field
from tasktool.model import Project, Phase, Status

EMOJI_TO_STATUS = {
    "✅": Status.DONE,
    "🚧": Status.IN_PROGRESS,
    "⏸": Status.BLOCKED,
    "☐": Status.READY,
}

PHASE_HEADER_RE = re.compile(
    r"^##\s+(?P<id>P\d+)\s+—\s+(?P<title>.+?)\s+"
    r"(?P<emoji>[✅🚧☐])(?:\s+`(?P<tag>[^`]+)`)?\s*$"
)
# Phase headers may NOT use ⏸ (blocked is slice-only — spec §6.6).
# A `⏸ Pn …` line matches the fallback below, which records the item
# under `phases[]` with status=READY and emits an explicit warning.
PHASE_HEADER_BLOCKED_RE = re.compile(
    r"^##\s+(?P<id>P\d+)\s+—\s+(?P<title>.+?)\s+"
    r"⏸(?:\s+`(?P<tag>[^`]+)`)?\s*$"
)
PHASE_DONE_TAG_RE = re.compile(r"^DONE\s+(?P<date>\d{4}-\d{2}-\d{2})$")
SPEC_RE = re.compile(r"Spec:\s*\[`(?P<path>[^`]+)`\]\([^)]+\)")
PLAN_RE = re.compile(r"Plan:\s*(?:\[`(?P<path>[^`]+)`\]\([^)]+\)|_pending_)")

@dataclass(slots=True)
class ParseResult:
    project: Project
    warnings: list[str] = field(default_factory=list)

def _apply_phase_tag(phase: Phase, tag: str | None) -> None:
    """Translate the optional `\`...\`` tag suffix into model fields."""
    if not tag:
        return
    dm = PHASE_DONE_TAG_RE.match(tag)
    if dm:
        phase.closed = dm.group("date")
    # `IN PROGRESS` adds no extra field beyond the emoji-derived status.
    # Other tag forms are ignored (warnings are emitted elsewhere only
    # for clearly-invalid statuses like blocked-on-phase).

def parse_tasklist_md(text: str) -> ParseResult:
    project = Project(project="<imported>", schema_version=1)
    warnings: list[str] = []
    current_phase: Phase | None = None
    for lineno, raw in enumerate(text.splitlines(), start=1):
        m = PHASE_HEADER_RE.match(raw)
        if m:
            current_phase = Phase(
                id=m.group("id"),
                title=m.group("title").strip(),
                created="1970-01-01",  # placeholder; importer cannot recover real created dates
                status=EMOJI_TO_STATUS[m.group("emoji")],
            )
            _apply_phase_tag(current_phase, m.group("tag"))
            project.phases.append(current_phase)
            continue
        bm = PHASE_HEADER_BLOCKED_RE.match(raw)
        if bm:
            warnings.append(
                f"line {lineno}: blocked status not allowed on phase; coerced to ready"
            )
            current_phase = Phase(
                id=bm.group("id"),
                title=bm.group("title").strip(),
                created="1970-01-01",
                status=Status.READY,
            )
            project.phases.append(current_phase)
            continue
        if current_phase is not None:
            sm = SPEC_RE.search(raw)
            if sm:
                current_phase.spec_path = sm.group("path")
            pm = PLAN_RE.search(raw)
            if pm and pm.group("path"):
                current_phase.plan_path = pm.group("path")
    return ParseResult(project=project, warnings=warnings)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_importer -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/importer.py tools/tasktool/tests/test_importer.py
git commit -m "P2.S2: importer — phase header parsing"
```

---

## Task 2: Importer — slice bullet parsing

**Files:**
- Modify: `tools/tasktool/importer.py`
- Modify: `tools/tasktool/tests/test_importer.py`

Slice bullets look like:

```
- ✅ **S1** `DONE 2026-05-18` — CLI core: data model, ... Plan: [`docs/plans/...`](...). Post-impl: 139 tests; ...
- ☐ **S2** Importer, render, brief, archive-phase; ...  Plan: _pending — written after S1 ships._
```

The slice line contains: emoji, ID (`S\d+[a-z]?`), tag in backticks (optional for `READY`), then title text, optional inline `Plan: [...]` link, optional trailing prose.

- [ ] **Step 1: Write the failing test**

```python
# add to test_importer.py
SLICES_BLOCK = """\
## P2 — Demo 🚧 `IN PROGRESS`

- ✅ **S1** `DONE 2026-05-18` — CLI core: data model. Plan: [`docs/plans/2026-05-17-p2-s1.md`](plans/2026-05-17-p2-s1.md). Post-impl: 139 tests.
- ☐ **S2** Importer, render, brief. Plan: _pending._
- ⏸ **S3a** `BLOCKED on P2.S2` — follow-up cleanup.
"""

class TestImporterSlices(unittest.TestCase):
    def test_slice_parsing(self):
        r = parse_tasklist_md(SLICES_BLOCK)
        self.assertEqual(len(r.project.phases), 1)
        slices = r.project.phases[0].slices
        self.assertEqual([s.id for s in slices], ["S1", "S2", "S3a"])
        self.assertEqual(slices[0].status, Status.DONE)
        self.assertEqual(slices[0].closed, "2026-05-18")
        self.assertEqual(slices[0].plan_path, "docs/plans/2026-05-17-p2-s1.md")
        self.assertEqual(slices[1].status, Status.READY)
        self.assertIsNone(slices[1].plan_path)
        self.assertEqual(slices[2].status, Status.BLOCKED)
        self.assertIsNotNone(slices[2].blocked_on)
        self.assertEqual(slices[2].blocked_on.kind, "id")
        self.assertEqual(slices[2].blocked_on.value, "P2.S3")  # parsed from "BLOCKED on P2.S3"... see note
```

Note: the test asserts `P2.S3` because that's what the tag says. Adjust the fixture if needed; the importer's job is to capture the literal value after "BLOCKED on ".

Correct the test fixture: change the third bullet to `\`BLOCKED on P2.S3\`` (without the `a`) so the assertion is self-consistent. The slice ID itself is `S3a`; what it's blocked on is `P2.S3`.

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL — no slice parsing yet.

- [ ] **Step 3: Write the implementation**

Add to `importer.py`:

```python
SLICE_LINE_RE = re.compile(
    r"^-\s+(?P<emoji>[✅🚧⏸☐])\s+\*\*(?P<id>S\d+[a-z]?)\*\*"
    r"(?:\s+`(?P<tag>[^`]+)`)?"
    r"(?:\s+—\s+(?P<rest>.+))?$"
)
DONE_TAG_RE   = re.compile(r"^DONE\s+(?P<date>\d{4}-\d{2}-\d{2})$")
BLOCKED_TAG_RE = re.compile(r"^BLOCKED on\s+(?P<on>.+)$")
INLINE_PLAN_RE = re.compile(r"Plan:\s*\[`(?P<path>[^`]+)`\]\([^)]+\)")
```

Extend the loop in `parse_tasklist_md`:

```python
from tasktool.model import Slice, BlockedOn

# inside loop, after PHASE_HEADER_RE branch:
sm = SLICE_LINE_RE.match(raw)
if sm and current_phase is not None:
    emoji = sm.group("emoji")
    tag = sm.group("tag")
    rest = sm.group("rest") or ""
    title = rest.split(". Plan:", 1)[0].strip() or "<untitled>"
    s = Slice(
        id=sm.group("id"),
        title=title,
        created="1970-01-01",
        status=EMOJI_TO_STATUS[emoji],
    )
    if tag:
        dm = DONE_TAG_RE.match(tag)
        if dm:
            s.closed = dm.group("date")
        bm = BLOCKED_TAG_RE.match(tag)
        if bm:
            on = bm.group("on").strip()
            s.blocked_on = BlockedOn(kind="external" if on.startswith("external:") else "id",
                                     value=on[len("external:"):] if on.startswith("external:") else on)
    pm = INLINE_PLAN_RE.search(rest)
    if pm:
        s.plan_path = pm.group("path")
    current_phase.slices.append(s)
    continue
```

- [ ] **Step 4: Run test to verify it passes**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/importer.py tools/tasktool/tests/test_importer.py
git commit -m "P2.S2: importer — slice bullet parsing"
```

---

## Task 3: Importer — cross-cutting + archived references + warnings

**Files:**
- Modify: `tools/tasktool/importer.py`
- Modify: `tools/tasktool/tests/test_importer.py`

Cross-cutting block is introduced by `## Cross-cutting` and contains bullets shaped like slice bullets but with `X\d+` IDs. Historical / archived references show up as one-line phase summaries (no slice bullets); they are imported as ordinary `phases[]` entries with `status: done` and an "imported as historical" note (see the rule restated lower in this task). The importer **never** writes to `archived_phases[]` — that table is exclusively populated by `tasktool archive-phase`.

Unmatched lines under a known section are silently ignored *unless* they look like a bullet (`-` at start) — those become warnings.

- [ ] **Step 1: Write the failing test**

```python
# add to test_importer.py
CROSS_AND_NOISE = """\
## Cross-cutting (`X*`) — opportunistic, unscheduled

- ☐ **X1** — gather telemetry for skill firing rate.
- ⏸ **X2** — bogus blocked cross item.
- malformed bullet

## P1 — Old work (historical) ✅ `DONE 2025-12-01`

Closed; see `docs/archived-tasks/P1-old.md`.
"""

class TestImporterMisc(unittest.TestCase):
    def test_cross_and_warnings(self):
        r = parse_tasklist_md(CROSS_AND_NOISE)
        # Both cross items are captured; X2's blocked status is coerced to ready.
        self.assertEqual([c.id for c in r.project.cross_cutting], ["X1", "X2"])
        self.assertEqual(r.project.cross_cutting[0].status, Status.READY)
        self.assertEqual(r.project.cross_cutting[1].status, Status.READY)
        # P1 stays in phases[] (historical imports never become ArchivedPhase).
        self.assertTrue(any(ph.id == "P1" for ph in r.project.phases))
        self.assertFalse(r.project.archived_phases)
        # X2's invalid status surfaces as a warning.
        self.assertTrue(any("blocked status not allowed on cross" in w for w in r.warnings))
        # The malformed bullet surfaces as a warning.
        self.assertTrue(any("malformed bullet" in w for w in r.warnings))

    def test_blocked_phase_coerced_to_ready_with_warning(self):
        text = "## P9 — Bogus blocked phase ⏸ `BLOCKED on something`\n"
        r = parse_tasklist_md(text)
        self.assertEqual(len(r.project.phases), 1)
        self.assertEqual(r.project.phases[0].id, "P9")
        self.assertEqual(r.project.phases[0].status, Status.READY)
        self.assertTrue(
            any("blocked status not allowed on phase" in w for w in r.warnings)
        )
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL — no cross-cutting parsing, no warnings collection.

- [ ] **Step 3: Implementation**

Add to `importer.py`:

```python
CROSS_HEADER_RE = re.compile(r"^##\s+Cross-cutting\b")
CROSS_LINE_RE = re.compile(
    r"^-\s+(?P<emoji>[✅🚧☐])\s+\*\*(?P<id>X\d+)\*\*"
    r"(?:\s+—\s+(?P<rest>.+))?$"
)
# Cross-cutting items may NOT be blocked (spec §6.6). A line like
# `- ⏸ **X1** ...` is matched by a fallback regex that uses the wider
# emoji set, emits the "blocked status not allowed on cross" warning,
# and coerces the status to READY before appending the item.
CROSS_LINE_BLOCKED_RE = re.compile(
    r"^-\s+⏸\s+\*\*(?P<id>X\d+)\*\*"
    r"(?:\s+—\s+(?P<rest>.+))?$"
)
```

In `parse_tasklist_md`, track an `in_cross` flag toggled by `CROSS_HEADER_RE`. When set:

1. Try `CROSS_LINE_RE`. On match, append `CrossCutting` with the emoji's status.
2. Otherwise try `CROSS_LINE_BLOCKED_RE`. On match, emit a warning `f"line {lineno}: blocked status not allowed on cross; coerced to ready"` and append with `Status.READY`.
3. Otherwise, any line beginning with `- ` becomes a warning of the form `f"line {lineno}: unparsed bullet: {raw!r}"`.

**Historical / archived phases are imported as ordinary `phases[]` entries**, never as `ArchivedPhase` records. `ArchivedPhase` is reserved for the `tasktool archive-phase` workflow (a phase being archived *now*), not for retroactive imports. The phase status is taken from the emoji on the header; `(historical)` / `(archived)` substrings in the title are left in the title as-is (no special handling — they round-trip through `render` cleanly).

This makes Task 12's migration check unambiguous: P1 stays in `phases[]` with `status: done` and a historical note; nothing is moved to `archived_phases[]` during the migration.

- [ ] **Step 4: Run test to verify it passes**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/importer.py tools/tasktool/tests/test_importer.py
git commit -m "P2.S2: importer — cross-cutting and warnings"
```

---

## Task 4: `tasktool import` command + CLI wiring

**Files:**
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/cli.py`
- Modify: `tools/tasktool/__init__.py`
- Modify: `tools/tasktool/tests/test_cli_integration.py`

`tasktool import PATH [--dry-run] [--project NAME]`:

1. Read the markdown file.
2. Call `parse_tasklist_md(text)`.
3. If `--project NAME` is given, override `project.project`; otherwise leave whatever the parser set (default `<imported>`) and the user can edit later via the raw-edit escape hatch (it's the only field there is no command for).
4. If `--dry-run`, print the canonical JSON (via `dumps_canonical`) and the warnings to stdout, do NOT touch disk.
5. Otherwise, refuse if `docs/tasklist.json` already exists unless `--force` is passed. On success, write canonically (via `_save`, which also runs `validate_project`) and print the warnings to stderr.

- [ ] **Step 1: Write the failing CLI integration test**

```python
# add to test_cli_integration.py
def test_import_creates_tasklist_json(self):
    # tmp repo with a tiny TASKLIST.md
    (self.repo / "TASKLIST.md").write_text(
        "## P2 — Demo 🚧 `IN PROGRESS`\n\n- ✅ **S1** `DONE 2026-01-01` — done.\n"
    )
    rc, out, err = self.run_cli(["import", str(self.repo / "TASKLIST.md")])
    self.assertEqual(rc, 0)
    self.assertTrue((self.repo / "docs" / "tasklist.json").exists())
    rc2, out2, _ = self.run_cli(["show", "P2.S1"])
    self.assertEqual(rc2, 0)
    self.assertIn("done", out2)

def test_import_dry_run(self):
    (self.repo / "TASKLIST.md").write_text("## P2 — Demo 🚧 `IN PROGRESS`\n")
    rc, out, err = self.run_cli(["import", str(self.repo / "TASKLIST.md"), "--dry-run"])
    self.assertEqual(rc, 0)
    self.assertFalse((self.repo / "docs" / "tasklist.json").exists())
    self.assertIn('"id": "P2"', out)
```

- [ ] **Step 2: Run tests to verify they fail**

Expected: FAIL — `tasktool import` is not a known command.

- [ ] **Step 3: Implementation**

In `commands.py`:

```python
def cmd_import(
    *, repo_root: Path, md_path: Path,
    dry_run: bool = False, force: bool = False, project: str | None = None,
) -> tuple[int, str, str]:
    """Returns (rc, stdout, stderr_warnings)."""
    from tasktool.importer import parse_tasklist_md
    from tasktool.serialize import dumps_canonical
    text = md_path.read_text(encoding="utf-8")
    result = parse_tasklist_md(text)
    if project:
        result.project.project = project
    elif result.project.project == "<imported>":
        result.project.project = repo_root.name
    result.project.last_reviewed = _today()
    warnings_text = "\n".join(result.warnings)
    if dry_run:
        return 0, dumps_canonical(result.project), warnings_text
    target = _tasklist_path(repo_root)
    if target.exists() and not force:
        raise CommandError(f"{target}: already exists. Pass --force to overwrite.")
    _save(repo_root, result.project)
    return 0, f"wrote {target}\n", warnings_text
```

In `cli.py` (under `_build_parser`):

```python
p_import = sub.add_parser("import")
p_import.add_argument("md_path", type=Path)
p_import.add_argument("--dry-run", action="store_true")
p_import.add_argument("--force", action="store_true")
p_import.add_argument("--project")
```

In `main`:

```python
elif args.cmd == "import":
    rc, out, warn = commands.cmd_import(
        repo_root=root, md_path=args.md_path,
        dry_run=args.dry_run, force=args.force, project=args.project,
    )
    if out:
        sys.stdout.write(out)
    if warn:
        sys.stderr.write(warn + "\n")
    return rc
```

In `__init__.py`, add `from tasktool.importer import parse_tasklist_md` to the imports and `"parse_tasklist_md"` to `__all__`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/__init__.py tools/tasktool/tests/test_cli_integration.py
git commit -m "P2.S2: tasktool import command"
```

---

## Task 5: `render` module — phases + slices + cross-cutting

**Files:**
- Create: `tools/tasktool/render.py`
- Create: `tools/tasktool/tests/test_render.py`

`render.render_project(p: Project) -> str` produces a markdown document approximating the original `TASKLIST.md` shape. It is **not byte-identical** to the hand-written original — that's the explicit non-goal in spec §3. Section ordering, ID-allocation prose, and the "How to use this map" footer are dropped. Only essential content is rendered: project header, last-reviewed line, North Star (if set), per-phase sections, cross-cutting section, archived-phases section.

- [ ] **Step 1: Write the failing test**

```python
# tools/tasktool/tests/test_render.py
from __future__ import annotations
import unittest
from tasktool.model import Project, Phase, Slice, CrossCutting, Status, BlockedOn
from tasktool.render import render_project

class TestRender(unittest.TestCase):
    def test_basic_render(self):
        p = Project(project="demo", north_star="Make it good.", last_reviewed="2026-05-18")
        p.phases.append(Phase(
            id="P2", title="Demo phase", created="2026-05-17",
            status=Status.IN_PROGRESS, spec_path="docs/specs/x.md",
        ))
        p.phases[0].slices.append(Slice(
            id="S1", title="First slice", created="2026-05-17",
            status=Status.DONE, closed="2026-05-18",
            plan_path="docs/plans/y.md",
        ))
        p.phases[0].slices.append(Slice(
            id="S2", title="Second slice", created="2026-05-17",
            status=Status.BLOCKED, blocked_on=BlockedOn(kind="id", value="P2.S1"),
        ))
        p.cross_cutting.append(CrossCutting(id="X1", title="cross item", created="2026-05-17"))
        out = render_project(p)
        self.assertIn("# demo", out)
        self.assertIn("Make it good.", out)
        self.assertIn("## P2 — Demo phase 🚧 `IN PROGRESS`", out)
        self.assertIn("- ✅ **S1** `DONE 2026-05-18` — First slice", out)
        self.assertIn("- ⏸ **S2** `BLOCKED on P2.S1` — Second slice", out)
        self.assertIn("- ☐ **X1**", out)
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL — `tasktool.render` does not exist.

- [ ] **Step 3: Implementation**

```python
# tools/tasktool/render.py
from __future__ import annotations
from tasktool.model import Project, Phase, Slice, CrossCutting, Status

STATUS_EMOJI = {
    Status.DONE: "✅",
    Status.IN_PROGRESS: "🚧",
    Status.BLOCKED: "⏸",
    Status.READY: "☐",
}

def _slice_tag(s: Slice) -> str:
    if s.status is Status.DONE and s.closed:
        return f" `DONE {s.closed}`"
    if s.status is Status.IN_PROGRESS:
        return " `IN PROGRESS`"
    if s.status is Status.BLOCKED and s.blocked_on:
        prefix = "external:" if s.blocked_on.kind == "external" else ""
        return f" `BLOCKED on {prefix}{s.blocked_on.value}`"
    return ""

def _phase_tag(ph: Phase) -> str:
    if ph.status is Status.DONE and ph.closed:
        return f" `DONE {ph.closed}`"
    if ph.status is Status.IN_PROGRESS:
        return " `IN PROGRESS`"
    return ""

def render_project(p: Project) -> str:
    lines: list[str] = [f"# {p.project}", ""]
    if p.last_reviewed:
        lines += [f"**Last reviewed:** {p.last_reviewed}.", ""]
    if p.north_star:
        lines += ["## North Star", "", p.north_star, ""]
    for ph in p.phases:
        lines.append(f"## {ph.id} — {ph.title} {STATUS_EMOJI[ph.status]}{_phase_tag(ph)}")
        lines.append("")
        if ph.spec_path or ph.plan_path:
            spec = f"[`{ph.spec_path}`]({ph.spec_path})" if ph.spec_path else "_none_"
            plan = f"[`{ph.plan_path}`]({ph.plan_path})" if ph.plan_path else "_pending_"
            lines.append(f"Spec: {spec}. Plan: {plan}.")
            lines.append("")
        for s in ph.slices:
            title = s.title
            plan_part = f" Plan: [`{s.plan_path}`]({s.plan_path})." if s.plan_path else ""
            lines.append(f"- {STATUS_EMOJI[s.status]} **{s.id}**{_slice_tag(s)} — {title}.{plan_part}")
        lines.append("")
    if p.cross_cutting:
        lines += ["## Cross-cutting (`X*`)", ""]
        for c in p.cross_cutting:
            lines.append(f"- {STATUS_EMOJI[c.status]} **{c.id}** — {c.title}.")
        lines.append("")
    if p.archived_phases:
        lines += ["## Archived phases", ""]
        for a in p.archived_phases:
            lines.append(f"- **{a.id}** — {a.title} → [`{a.archived_path}`]({a.archived_path}) ({a.archived_date})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_render -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/render.py tools/tasktool/tests/test_render.py
git commit -m "P2.S2: render module"
```

---

## Task 6: `tasktool render` command + CLI

**Files:**
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/cli.py`
- Modify: `tools/tasktool/__init__.py`
- Modify: `tools/tasktool/tests/test_cli_integration.py`

- [ ] **Step 1: Write the failing CLI test**

```python
def test_render_outputs_markdown(self):
    self.run_cli(["init", "--project", "demo"])
    self.run_cli(["create", "phase", "--title", "Demo phase"])
    rc, out, _ = self.run_cli(["render"])
    self.assertEqual(rc, 0)
    self.assertIn("## P1 — Demo phase", out)
```

- [ ] **Step 2: Verify it fails**

Expected: FAIL — `render` is not a subcommand.

- [ ] **Step 3: Implementation**

In `commands.py`:

```python
def cmd_render(*, repo_root: Path, format: str = "markdown") -> str:
    from tasktool.render import render_project
    if format != "markdown":
        raise CommandError(f"render: unsupported format {format!r} (only 'markdown' for S2)")
    return render_project(_load(repo_root))
```

In `cli.py`:

```python
p_render = sub.add_parser("render")
p_render.add_argument("--format", default="markdown", choices=["markdown"])
```

In `main`:

```python
elif args.cmd == "render":
    sys.stdout.write(commands.cmd_render(repo_root=root, format=args.format))
```

Re-export `render_project` from `__init__.py`.

- [ ] **Step 4: Verify it passes**

Run: `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`
Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/__init__.py tools/tasktool/tests/test_cli_integration.py
git commit -m "P2.S2: tasktool render command"
```

---

## Task 7: `brief` module

**Files:**
- Create: `tools/tasktool/brief.py`
- Create: `tools/tasktool/tests/test_brief.py`

`brief.brief(p: Project, qid: str) -> str` produces the "start-of-work primer" described in spec §7.4:

- **For a slice (`P2.S2`)**: header (`# P2.S2 — title`), slice status + plan_path, parent phase one-liner, sibling-slice status table, open tasks in this slice.
- **For a phase (`P2`)**: header, phase status + spec/plan paths, slice status table.
- **For a task (`P2.S1.T3`)**: header, task status + notes, parent slice one-liner. (Edge case; not the primary use case.)
- **For a cross (`X1`)**: header, status, refs, notes.

- [ ] **Step 1: Write the failing test**

```python
# tools/tasktool/tests/test_brief.py
from __future__ import annotations
import unittest
from tasktool.model import Project, Phase, Slice, Task, Status
from tasktool.brief import brief

def _sample() -> Project:
    p = Project(project="demo", last_reviewed="2026-05-18")
    ph = Phase(id="P2", title="Phase 2", created="2026-05-17", status=Status.IN_PROGRESS)
    p.phases.append(ph)
    s1 = Slice(id="S1", title="Done slice", created="2026-05-17", status=Status.DONE, closed="2026-05-18")
    s2 = Slice(id="S2", title="Active slice", created="2026-05-17", status=Status.IN_PROGRESS,
               plan_path="docs/plans/x.md")
    s2.tasks.append(Task(id="T1", title="open task", created="2026-05-17"))
    s2.tasks.append(Task(id="T2", title="done task", created="2026-05-17",
                         status=Status.DONE, closed="2026-05-18"))
    ph.slices += [s1, s2]
    return p

class TestBrief(unittest.TestCase):
    def test_slice_brief(self):
        out = brief(_sample(), "P2.S2")
        self.assertIn("# P2.S2 — Active slice", out)
        self.assertIn("status: in_progress", out)
        self.assertIn("plan: docs/plans/x.md", out)
        self.assertIn("Parent phase: P2 — Phase 2 [in_progress]", out)
        self.assertIn("Sibling slices:", out)
        self.assertIn("S1  [done]", out)
        self.assertIn("Open tasks:", out)
        self.assertIn("T1  [ready]  open task", out)
        self.assertNotIn("T2", out)  # done tasks excluded from "Open tasks"

    def test_phase_brief(self):
        out = brief(_sample(), "P2")
        self.assertIn("# P2 — Phase 2", out)
        self.assertIn("Slices:", out)
        self.assertIn("S1  [done]", out)
        self.assertIn("S2  [in_progress]", out)
```

- [ ] **Step 2: Verify it fails**

Expected: FAIL — module does not exist.

- [ ] **Step 3: Implementation**

```python
# tools/tasktool/brief.py
from __future__ import annotations
from tasktool.model import Project, Phase, Slice, Task, CrossCutting, Status
from tasktool.ids import parse_id, split_qualified

def _find(p: Project, qid: str):
    parts = qid.split(".")
    if len(parts) == 1:
        if qid.startswith("P"):
            return next((ph for ph in p.phases if ph.id == qid), None)
        if qid.startswith("X"):
            return next((c for c in p.cross_cutting if c.id == qid), None)
        return None
    if len(parts) == 2:
        ph = next((ph for ph in p.phases if ph.id == parts[0]), None)
        if ph is None:
            return None
        return next((s for s in ph.slices if s.id == parts[1]), None)
    if len(parts) == 3:
        ph = next((ph for ph in p.phases if ph.id == parts[0]), None)
        if ph is None:
            return None
        s = next((s for s in ph.slices if s.id == parts[1]), None)
        if s is None:
            return None
        return next((t for t in s.tasks if t.id == parts[2]), None)
    return None

def _phase_for(p: Project, qid: str) -> Phase | None:
    return next((ph for ph in p.phases if ph.id == qid.split(".")[0]), None)

def brief(p: Project, qid: str) -> str:
    item = _find(p, qid)
    if item is None:
        raise ValueError(f"{qid}: not found")
    kind = parse_id(qid)[0]
    lines: list[str] = []
    if kind == "slice":
        ph = _phase_for(p, qid)
        lines.append(f"# {qid} — {item.title}")
        lines.append(f"status: {item.status.value}")
        if item.plan_path:
            lines.append(f"plan: {item.plan_path}")
        if item.reviewer_chain:
            lines.append(f"reviewer_chain: {item.reviewer_chain}")
        lines.append("")
        lines.append(f"Parent phase: {ph.id} — {ph.title} [{ph.status.value}]")
        lines.append("")
        lines.append("Sibling slices:")
        for s in ph.slices:
            lines.append(f"  {s.id}  [{s.status.value}]  {s.title}")
        lines.append("")
        lines.append("Open tasks:")
        for t in item.tasks:
            if t.status is not Status.DONE:
                lines.append(f"  {t.id}  [{t.status.value}]  {t.title}")
    elif kind == "phase":
        lines.append(f"# {qid} — {item.title}")
        lines.append(f"status: {item.status.value}")
        if item.spec_path:
            lines.append(f"spec: {item.spec_path}")
        if item.plan_path:
            lines.append(f"plan: {item.plan_path}")
        lines.append("")
        lines.append("Slices:")
        for s in item.slices:
            lines.append(f"  {s.id}  [{s.status.value}]  {s.title}")
    elif kind == "task":
        lines.append(f"# {qid} — {item.title}")
        lines.append(f"status: {item.status.value}")
        if item.notes:
            lines.append(f"notes:\n{item.notes}")
    elif kind == "cross":
        lines.append(f"# {qid} — {item.title}")
        lines.append(f"status: {item.status.value}")
        if item.refs:
            lines.append("refs:")
            for r in item.refs:
                lines.append(f"  - {r}")
        if item.notes:
            lines.append(f"notes:\n{item.notes}")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Verify it passes**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/brief.py tools/tasktool/tests/test_brief.py
git commit -m "P2.S2: brief module"
```

---

## Task 8: `tasktool brief` command + CLI

**Files:**
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/cli.py`
- Modify: `tools/tasktool/__init__.py`
- Modify: `tools/tasktool/tests/test_cli_integration.py`

- [ ] **Step 1: Write the failing CLI test**

```python
def test_brief_slice(self):
    self.run_cli(["init", "--project", "demo"])
    self.run_cli(["create", "phase", "--title", "Phase"])
    self.run_cli(["create", "slice", "P1", "--title", "Slice"])
    self.run_cli(["create", "task", "P1.S1", "--title", "Task A"])
    rc, out, _ = self.run_cli(["brief", "P1.S1"])
    self.assertEqual(rc, 0)
    self.assertIn("# P1.S1 — Slice", out)
    self.assertIn("Parent phase: P1", out)
    self.assertIn("Open tasks:", out)
    self.assertIn("Task A", out)
```

- [ ] **Step 2: Verify it fails**

Expected: FAIL.

- [ ] **Step 3: Implementation**

In `commands.py`:

```python
def cmd_brief(*, repo_root: Path, id: str) -> str:
    from tasktool.brief import brief as _brief
    p = _load(repo_root)
    qid = _resolve_id(p, id)
    return _brief(p, qid)
```

In `cli.py`:

```python
p_brief = sub.add_parser("brief")
p_brief.add_argument("id")
```

In `main`:

```python
elif args.cmd == "brief":
    sys.stdout.write(commands.cmd_brief(repo_root=root, id=args.id))
```

Re-export `brief` from `__init__.py`.

- [ ] **Step 4: Verify it passes**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/__init__.py tools/tasktool/tests/test_cli_integration.py
git commit -m "P2.S2: tasktool brief command"
```

---

## Task 9: `archive-phase` command — orchestrator

**Files:**
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/tests/test_commands.py`

Per spec §7.3 and §8.2:

1. Refuse unless every slice in the phase has `status: done`.
2. Apply the post-phase review gate (auto-discover `docs/reviewer/<phase-id>-post-phase/` unless `--reviewer-chain` given; latest round verdict must be `ready` or `ready with small edits`; `--skip-review-gate` bypasses with a stderr warning + notes record).
3. If the phase's own status is not `done`, set it to `done` and stamp `closed=today` (consistent with `cmd_close` for phases).
4. Build the archive markdown at `docs/archived-tasks/P{n}-<slug>.md` containing:
   - `# P{n} — title`
   - status / closed / spec / plan
   - one-line per slice (id, status, closed, title)
   - a fenced ```json``` code block with the full phase dict (via the canonical serializer) — enables future `tasktool unarchive`.
5. Remove the phase from `project.phases`. Append an `ArchivedPhase(id, title, archived_path, archived_date=today())` to `project.archived_phases`.
6. `_save` the project (which `validate_project`s and `git add`s).

`<slug>` is generated from the phase title via the rule: lowercase, replace non-alphanumerics with `-`, collapse repeated `-`, trim leading/trailing `-`. Cap at 40 chars.

- [ ] **Step 1: Write the failing test**

```python
# add to test_commands.py
def test_archive_phase_writes_summary_and_moves_to_archived(self):
    root = self.repo  # tmpdir set up by base class
    from tasktool import commands
    commands.cmd_init(repo_root=root, project="demo", north_star="")
    pid = commands.cmd_create_phase(repo_root=root, title="A phase")
    sid = commands.cmd_create_slice(repo_root=root, phase_id=pid, title="Only slice")
    # Close the slice with --skip-review-gate so we don't need a chain folder.
    commands.cmd_close(
        repo_root=root, id=f"{pid}.{sid}",
        skip_review_gate=True,
    )
    commands.cmd_archive_phase(repo_root=root, phase_id=pid, skip_review_gate=True)
    # Phase removed from active list.
    from tasktool.serialize import load_project
    p = load_project(root / "docs" / "tasklist.json")
    self.assertFalse(any(ph.id == pid for ph in p.phases))
    self.assertEqual([a.id for a in p.archived_phases], [pid])
    # Summary file exists and contains the JSON code block.
    arch_path = root / p.archived_phases[0].archived_path
    self.assertTrue(arch_path.exists())
    body = arch_path.read_text(encoding="utf-8")
    self.assertIn(f"# {pid} —", body)
    self.assertIn("```json", body)

def test_archive_phase_refuses_with_open_slices(self):
    from tasktool import commands
    commands.cmd_init(repo_root=self.repo, project="demo")
    pid = commands.cmd_create_phase(repo_root=self.repo, title="phase")
    commands.cmd_create_slice(repo_root=self.repo, phase_id=pid, title="open slice")
    with self.assertRaises(commands.CommandError) as cm:
        commands.cmd_archive_phase(repo_root=self.repo, phase_id=pid, skip_review_gate=True)
    self.assertIn("open slices", str(cm.exception).lower())
```

- [ ] **Step 2: Verify it fails**

Expected: FAIL — `cmd_archive_phase` does not exist.

- [ ] **Step 3: Implementation**

Add to `commands.py`:

```python
import re as _re

def _slugify(text: str) -> str:
    s = _re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:40] or "phase"

def cmd_archive_phase(
    *, repo_root: Path, phase_id: str,
    reviewer_chain: Path | None = None, skip_review_gate: bool = False,
) -> None:
    import sys as _sys
    from tasktool.model import ArchivedPhase
    from tasktool.serialize import dumps_canonical
    p = _load(repo_root)
    phase = next((ph for ph in p.phases if ph.id == phase_id), None)
    if phase is None:
        raise CommandError(f"phase {phase_id} not found")
    open_slices = [s.id for s in phase.slices if s.status != Status.DONE]
    if open_slices:
        raise CommandError(
            f"phase {phase_id} has open slices: {', '.join(open_slices)}"
        )
    if skip_review_gate:
        # Spec §8.2: bypass MUST emit a stderr warning so the operator (and CI)
        # can audit gate-skip events even when stdout is consumed.
        print(f"warning: review gate skipped for {phase_id}", file=_sys.stderr)
    # Reuse the existing review-gate apply path (it writes phase_reviewer_chain
    # on success or records the bypass into notes on skip).
    _apply_review_gate(repo_root, p, phase, phase_id, "phase",
                       reviewer_chain, skip_review_gate)
    if phase.status != Status.DONE:
        phase.status = Status.DONE
        phase.closed = phase.closed or _today()
    slug = _slugify(phase.title)
    archive_dir = repo_root / "docs" / "archived-tasks"
    archive_rel = f"docs/archived-tasks/{phase_id}-{slug}.md"
    archive_path = repo_root / archive_rel
    # 1. Build the archive content fully in memory (no disk side effects yet).
    sub_project = Project(project=p.project)
    sub_project.phases.append(phase)
    phase_json = dumps_canonical(sub_project)
    summary_lines = [f"# {phase_id} — {phase.title}", "", f"status: {phase.status.value}"]
    if phase.closed:
        summary_lines.append(f"closed: {phase.closed}")
    if phase.spec_path:
        summary_lines.append(f"spec: {phase.spec_path}")
    if phase.plan_path:
        summary_lines.append(f"plan: {phase.plan_path}")
    summary_lines += ["", "## Slices", ""]
    for s in phase.slices:
        closed = f" — closed {s.closed}" if s.closed else ""
        summary_lines.append(f"- **{s.id}** [{s.status.value}]{closed} — {s.title}")
    summary_lines += ["", "## Full phase JSON (for tasktool unarchive)", "", "```json", phase_json.rstrip(), "```", ""]
    summary_text = "\n".join(summary_lines)
    # 2. Mutate the project model.
    p.phases = [ph for ph in p.phases if ph.id != phase_id]
    p.archived_phases.append(ArchivedPhase(
        id=phase_id, title=phase.title,
        archived_path=archive_rel, archived_date=_today(),
    ))
    # 3. Validate BEFORE any filesystem side effects. If this raises,
    #    nothing has touched disk and the workspace stays consistent.
    validate_project(p)
    # 4. Now safe to write both artefacts. JSON last so a writer error
    #    on the archive file does not leave tasklist.json mid-archive.
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(summary_text, encoding="utf-8")
    _save(repo_root, p)  # re-validates (harmless) and atomically writes the JSON
    _git_stage(repo_root, archive_path)
```

- [ ] **Step 4: Verify it passes**

Run: `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
git commit -m "P2.S2: archive-phase command"
```

---

## Task 10: `archive-phase` CLI wiring

**Files:**
- Modify: `tools/tasktool/cli.py`
- Modify: `tools/tasktool/tests/test_cli_integration.py`

- [ ] **Step 1: Write the failing CLI test**

```python
def test_archive_phase_cli(self):
    self.run_cli(["init", "--project", "demo"])
    self.run_cli(["create", "phase", "--title", "Phase to archive"])
    self.run_cli(["create", "slice", "P1", "--title", "Slice"])
    self.run_cli(["close", "P1.S1", "--skip-review-gate"])
    rc, out, err = self.run_cli([
        "archive-phase", "P1", "--skip-review-gate",
    ])
    self.assertEqual(rc, 0)
    self.assertIn("review gate skipped for P1", err)  # spec §8.2 audit warning
    self.assertTrue((self.repo / "docs" / "archived-tasks").exists())
    md = list((self.repo / "docs" / "archived-tasks").glob("P1-*.md"))
    self.assertEqual(len(md), 1)
```

- [ ] **Step 2: Verify it fails**

Expected: FAIL — `archive-phase` is not a subcommand.

- [ ] **Step 3: Implementation**

In `cli.py` `_build_parser`:

```python
p_arch = sub.add_parser("archive-phase")
p_arch.add_argument("phase_id")
p_arch.add_argument("--reviewer-chain", type=Path)
p_arch.add_argument("--skip-review-gate", action="store_true")
```

In `main`:

```python
elif args.cmd == "archive-phase":
    commands.cmd_archive_phase(
        repo_root=root, phase_id=args.phase_id,
        reviewer_chain=args.reviewer_chain,
        skip_review_gate=args.skip_review_gate,
    )
```

- [ ] **Step 4: Verify it passes**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/cli.py tools/tasktool/tests/test_cli_integration.py
git commit -m "P2.S2: archive-phase CLI"
```

---

## Task 11: Importer round-trip fixture test

**Files:**
- Modify: `tools/tasktool/tests/test_importer.py`

A targeted fixture file `tools/tasktool/tests/fixtures/TASKLIST_sample.md` exercises every emoji / status / blocking shape so we can detect parser regressions independently of the live `docs/TASKLIST.md`.

- [ ] **Step 1: Create the fixture**

Create `tools/tasktool/tests/fixtures/TASKLIST_sample.md` containing one phase done, one in-progress, slices with each status (including a `S{n}a` follow-up), one externally-blocked slice, a cross-cutting item, and one bullet that is intentionally malformed (`- this should warn`).

- [ ] **Step 2: Write the test**

```python
from pathlib import Path
class TestImporterFixture(unittest.TestCase):
    def test_sample_fixture_roundtrip(self):
        path = Path(__file__).parent / "fixtures" / "TASKLIST_sample.md"
        text = path.read_text(encoding="utf-8")
        r = parse_tasklist_md(text)
        # Every expected ID present.
        ph_ids = [ph.id for ph in r.project.phases]
        self.assertIn("P1", ph_ids)
        self.assertIn("P2", ph_ids)
        all_slice_ids = [s.id for ph in r.project.phases for s in ph.slices]
        self.assertIn("S1a", all_slice_ids)
        # Malformed bullet surfaced.
        self.assertTrue(any("should warn" in w for w in r.warnings))
        # render → re-parse is stable for IDs.
        from tasktool.render import render_project
        round_tripped = parse_tasklist_md(render_project(r.project))
        self.assertEqual(ph_ids, [ph.id for ph in round_tripped.project.phases])
```

- [ ] **Step 3: Verify it passes**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_importer -v`
Expected: PASS (or fix the importer/render until it does — this is where parser bugs surface).

- [ ] **Step 4: Commit**

```bash
git add tools/tasktool/tests/fixtures/TASKLIST_sample.md tools/tasktool/tests/test_importer.py
git commit -m "P2.S2: importer round-trip fixture"
```

---

## Task 12: Migrate this repo — generate `docs/tasklist.json`

**Files:**
- Create: `docs/tasklist.json`
- Delete: `docs/TASKLIST.md`

This is a one-shot operation, performed manually with the CLI. No tests — instead, two manual verifications.

- [ ] **Step 1: Dry-run the import**

Run:

```bash
PYTHONPATH=tools python3 -m tasktool import docs/TASKLIST.md --dry-run --project superstar > /tmp/preview.json 2> /tmp/preview-warnings.txt
```

Read `/tmp/preview-warnings.txt`. Every warning must be a deliberate edit-time concern (e.g. malformed bullet you want to fix) or an artefact of intentionally-unparsed prose (e.g. the "How to use this map" section). If a warning indicates lost data (e.g. a known slice missing), STOP and fix the importer.

- [ ] **Step 2: Inspect the preview JSON**

Read `/tmp/preview.json`. Confirm:

- `project: "superstar"`.
- `schema_version: 1`.
- `phases[]` contains `P1` (historical, status `done`, closed date `2026-05-17`) and `P2` (status `in_progress`).
- `P2.slices[]` contains `S1` (done, closed `2026-05-18`, plan path set), `S2` (ready), `S3` (ready).
- `S1.reviewer_chain` is `null` in the import (the live file's reviewer chain folder reference is post-impl prose — not machine-parseable in the markdown). After import, run `PYTHONPATH=tools python3 -m tasktool note P2.S1 --append "imported from TASKLIST.md; reviewer chain at docs/reviewer/p2-s1-tasktool-cli-core-P2-S1-post-slice/"` to preserve the history, OR manually populate `reviewer_chain` via the TASKTOOL_RAW=1 editor workflow if that turns out to be the only data we lose in import. Choose at execution time based on what `validate` says.

- [ ] **Step 3: Perform the real import**

```bash
PYTHONPATH=tools python3 -m tasktool import docs/TASKLIST.md --project superstar
```

Expected: writes `docs/tasklist.json`, stages it via `git add`, prints any warnings to stderr.

- [ ] **Step 4: Run validate**

```bash
PYTHONPATH=tools python3 -m tasktool validate
```

Expected: `ok` (warnings about missing files are OK; errors are not).

- [ ] **Step 5: Compare `tasktool render` against the original**

```bash
PYTHONPATH=tools python3 -m tasktool render > /tmp/rendered.md
diff -u docs/TASKLIST.md /tmp/rendered.md | less
```

The diff will be large — that is expected, since `render` is intentionally lossy (no "How to use this map" footer, simpler section ordering). What you are checking for is **semantic equivalence**: every phase header, every slice bullet, every status emoji and tag, and every plan/spec link is present. If any required content is missing, fix the importer or the renderer and re-run from Step 3.

- [ ] **Step 6: Patch up post-import state**

Things the importer cannot recover from prose:

- Slice `reviewer_chain` (S1 has one). Use the raw-edit escape hatch:
  ```bash
  TASKTOOL_RAW=1 $EDITOR docs/tasklist.json   # add the reviewer_chain field
  PYTHONPATH=tools python3 -m tasktool validate --normalise
  ```
- Per-item `created` dates (importer stamps `1970-01-01` as a sentinel because dates are not in the markdown). Use the raw-edit escape hatch to backfill from `git log --reverse --diff-filter=A -- docs/TASKLIST.md` (best-effort) or set them all to the phase/slice's `closed` date for done items, today for ready ones.

After every raw edit, run `tasktool validate --normalise` so the result is hook-acceptable.

- [ ] **Step 7: Verify brief works against the imported data**

```bash
PYTHONPATH=tools python3 -m tasktool brief P2.S2
```

Expected: prints the slice's status, the parent phase summary, sibling slice statuses, and any open tasks. If the output is empty or wrong, fix and re-import.

- [ ] **Step 8: Delete `docs/TASKLIST.md`**

```bash
git rm docs/TASKLIST.md
```

- [ ] **Step 9: Commit**

```bash
git add docs/tasklist.json
git commit -m "P2.S2: migrate TASKLIST.md → docs/tasklist.json"
```

---

## Task 13: Reflect P2.S2 progress in the new tasklist.json

**Files:**
- Modify: `docs/tasklist.json` (via CLI)

After the file is in place, mark S2's plan link and bring its status to `in_progress` to reflect the active work. This also serves as a smoke test of mutation commands against the imported file.

- [ ] **Step 1: Set plan_path on S2 via the raw-edit escape hatch**

`Slice.plan_path` is the field the renderer and `brief` read; `refs[]` is for ad-hoc URLs. There is no S1-shipped CLI command for setting `plan_path` on an existing slice (the field is only writable at `create slice --plan`). Use the documented raw-edit escape hatch from spec §8.3:

```bash
TASKTOOL_RAW=1 $EDITOR docs/tasklist.json
# In the editor: locate the S2 slice object under P2 and set
#   "plan_path": "docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md"
PYTHONPATH=tools python3 -m tasktool validate --normalise
```

The `validate --normalise` step canonicalises the file so the pre-commit hook (installed in S3) will accept it; running it now is harmless even before the hook exists.

A native `tasktool set-plan <id> --path PATH` command would be nicer, but adding mutation surface is out of scope for S2 (spec §10 step 5 places the skill rewrite + sibling skill touch-ups in S3, and the surface freeze for S2 is intentional). If reviewers later require it, add as a follow-up slice (`S2a`).

- [ ] **Step 2: Set S2 to in_progress**

```bash
PYTHONPATH=tools python3 -m tasktool set P2.S2 --status in_progress
```

- [ ] **Step 3: Verify**

```bash
PYTHONPATH=tools python3 -m tasktool brief P2.S2
```

Expected: shows `status: in_progress` and the plan reference.

- [ ] **Step 4: Commit**

```bash
git add docs/tasklist.json
git commit -m "P2.S2: mark slice in_progress in tasklist.json"
```

---

## Task 14: Self-review

- [ ] **Step 1: Spec coverage walk-through**

Open `docs/specs/2026-05-17-P2-tasktool-design.md` next to this plan. For each S2-relevant section, point at a task:

| Spec section | Task |
|---|---|
| §7.1 `import` | T1–T4 |
| §7.4 `render` | T5–T6 |
| §7.4 `brief` | T7–T8 |
| §7.3 `archive-phase` | T9–T10 |
| §8.2 phase review gate | T9 (`_apply_review_gate` reuse) |
| §10 migration | T12–T13 |
| §11 importer fixture test | T11 |

If a section is uncovered, add a task before submitting for review.

- [ ] **Step 2: Run the full suite**

```bash
PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v
```

Expected: all green, count > 139 (S1 baseline).

- [ ] **Step 3: Run `tasktool validate` on the live JSON**

```bash
PYTHONPATH=tools python3 -m tasktool validate
```

Expected: `ok`.

---

## Task 15: External post-slice review

After all tasks above are committed and the test suite is green:

1. Create the post-slice reviewer chain folder under `docs/reviewer/p2-s2-tasktool-importer-render-brief-archive-P2-S2-post-slice/`.
2. Invoke `[[external-review]]` with `--kind post-slice --file docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md --context docs/specs/2026-05-17-P2-tasktool-design.md --context docs/tasklist.json`.
3. Iterate (delegating fixes to subagents per `subagent-driven-development`) until verdict ∈ `{ready, ready with small edits}`.
4. Close the slice:
   ```bash
   PYTHONPATH=tools python3 -m tasktool close P2.S2 \
       --reviewer-chain docs/reviewer/p2-s2-tasktool-importer-render-brief-archive-P2-S2-post-slice
   ```
5. Commit the final state with the `P2.S2: close slice — reviewer ready` message.
