# P2.S1 — tasktool CLI core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Python stdlib CLI core for `tasktool` — data model, canonical serializer, validation, ID allocation, reviewer-gate, and the mutation/read commands. End state: `tasktool init && tasktool create phase --title "..." && tasktool show P1` round-trips cleanly, `tasktool validate --strict-format` blocks non-canonical commits.

**Architecture:** Single Python package `tools/tasktool/` (stdlib only). Layered: `ids` / `model` / `serialize` / `validate` / `allocate` / `reviewer_gate` are pure, side-effect-free modules; `commands` orchestrates them and is the only layer that touches disk-as-side-effect; `cli` is argparse glue. Tests under `tools/tasktool/tests/` use `unittest` with tmpdir fixtures.

**Tech Stack:** Python 3.11+ (dataclasses, pathlib, json, argparse, datetime, re, subprocess, hashlib, unittest). Zero third-party dependencies.

---

## File structure

Created in this slice:

```
tools/tasktool/
├── __init__.py            # public API surface: load_project, save_project, brief, etc.
├── __main__.py            # `python -m tasktool` entry; defers to cli.main()
├── cli.py                 # argparse definition + dispatcher
├── ids.py                 # ID regex, parse, fully-qualify, kind detection
├── model.py               # dataclasses: Project, Phase, Slice, Task, CrossCutting, BlockedOn
├── serialize.py           # canonical JSON load/save (sort_keys=True, indent=2, trailing \n)
├── validate.py            # validation rules + strict-format + normalise
├── allocate.py            # orphan-aware next-ID across TASKLIST/specs/plans/reviewer
├── reviewer_gate.py       # chain folder discovery + chain.json verdict check
├── commands.py            # one function per subcommand; called by cli.dispatch
├── schema_gen.py          # generate JSON Schema from dataclasses
├── install.sh             # idempotent installer for ~/.local/bin/tasktool shim
└── tests/
    ├── __init__.py
    ├── test_ids.py
    ├── test_model.py
    ├── test_serialize.py
    ├── test_validate.py
    ├── test_allocate.py
    ├── test_reviewer_gate.py
    ├── test_commands.py
    └── test_cli_integration.py
```

Not touched in this slice: `tools/tasktool/templates/pre-commit-tasktool` (S3), `importer.py` / `render.py` / `brief.py` (S2), any sibling skills (S3).

---

## Conventions used throughout

- **TDD:** every task writes the failing test, runs it red, implements the minimum, runs it green, commits. Commits per task, not per step.
- **Commit message prefix:** `P2.S1:` followed by an imperative one-liner.
- **Run tests via:** `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`. The `tools/` directory must be on `PYTHONPATH` because the package lives at `tools/tasktool/`. Once the installer (Task 15) has been run, the shim sets `PYTHONPATH` automatically — but the raw command shown in every test gate is what an agent will run before installing.
- **No third-party deps.** If you reach for `pytest`, `pydantic`, `click`, stop — stdlib only.
- **Python style:** dataclasses with `slots=True`; `from __future__ import annotations` everywhere; type hints required on public functions.

---

## Task 1: Project skeleton + smoke test

**Files:**
- Create: `tools/tasktool/__init__.py`
- Create: `tools/tasktool/__main__.py`
- Create: `tools/tasktool/cli.py`
- Create: `tools/tasktool/tests/__init__.py`
- Create: `tools/tasktool/tests/test_cli_integration.py`

- [ ] **Step 1: Create empty package skeleton**

```python
# tools/tasktool/__init__.py
"""tasktool — JSON-backed task management CLI."""
__version__ = "0.1.0"
```

```python
# tools/tasktool/__main__.py
from tasktool.cli import main
import sys
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

```python
# tools/tasktool/cli.py
from __future__ import annotations

def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print("tasktool — see docs/specs/2026-05-17-P2-tasktool-design.md")
        return 0
    print(f"tasktool: unknown command: {argv[0]}", flush=True)
    return 2
```

```python
# tools/tasktool/tests/__init__.py
```

- [ ] **Step 2: Write the smoke test**

```python
# tools/tasktool/tests/test_cli_integration.py
from __future__ import annotations
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_DIR = REPO_ROOT / "tools"

def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "tasktool", *args],
        capture_output=True, text=True, cwd=cwd or REPO_ROOT, env=env,
    )

class SmokeTests(unittest.TestCase):
    def test_help_prints_and_exits_zero(self):
        result = run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("tasktool", result.stdout)

    def test_unknown_command_exits_two(self):
        result = run_cli("nope")
        self.assertEqual(result.returncode, 2)
```

- [ ] **Step 3: Run tests**

Run: `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`
Expected: 2 tests pass.

- [ ] **Step 4: Commit**

```bash
git add tools/tasktool/
git commit -m "P2.S1: scaffold tasktool package and smoke test"
```

---

## Task 2: ID parsing module (ids.py)

**Files:**
- Create: `tools/tasktool/ids.py`
- Create: `tools/tasktool/tests/test_ids.py`

- [ ] **Step 1: Write failing tests**

```python
# tools/tasktool/tests/test_ids.py
from __future__ import annotations
import unittest
from tasktool.ids import (
    IdParseError, parse_id, fully_qualify, kind_of, is_slice_id, split_qualified,
)

class ParseIdTests(unittest.TestCase):
    def test_phase(self):
        self.assertEqual(parse_id("P2"), ("phase", "P2"))
    def test_slice(self):
        self.assertEqual(parse_id("S3"), ("slice", "S3"))
    def test_slice_letter_suffix(self):
        self.assertEqual(parse_id("S5a"), ("slice", "S5a"))
    def test_task(self):
        self.assertEqual(parse_id("T1"), ("task", "T1"))
    def test_cross(self):
        self.assertEqual(parse_id("X4"), ("cross", "X4"))
    def test_qualified_phase_slice(self):
        self.assertEqual(parse_id("P2.S3"), ("slice", "P2.S3"))
    def test_qualified_phase_slice_task(self):
        self.assertEqual(parse_id("P2.S3.T1"), ("task", "P2.S3.T1"))
    def test_rejects_lowercase_phase(self):
        with self.assertRaises(IdParseError):
            parse_id("p2")
    def test_rejects_empty(self):
        with self.assertRaises(IdParseError):
            parse_id("")
    def test_rejects_garbage(self):
        with self.assertRaises(IdParseError):
            parse_id("P2..S1")

class KindTests(unittest.TestCase):
    def test_kind_of_short(self):
        self.assertEqual(kind_of("P2"), "phase")
        self.assertEqual(kind_of("S3a"), "slice")
        self.assertEqual(kind_of("T1"), "task")
        self.assertEqual(kind_of("X4"), "cross")
    def test_kind_of_qualified(self):
        self.assertEqual(kind_of("P2.S3.T1"), "task")
    def test_is_slice_id(self):
        self.assertTrue(is_slice_id("S3"))
        self.assertTrue(is_slice_id("P2.S3a"))
        self.assertFalse(is_slice_id("T1"))
        self.assertFalse(is_slice_id("P2"))

class QualifyTests(unittest.TestCase):
    def test_qualify_slice_under_phase(self):
        self.assertEqual(fully_qualify("S3", phase="P2"), "P2.S3")
    def test_qualify_task_under_slice(self):
        self.assertEqual(fully_qualify("T1", phase="P2", slice="S3"), "P2.S3.T1")
    def test_qualify_already_qualified(self):
        self.assertEqual(fully_qualify("P2.S3", phase="P9"), "P2.S3")

class SplitTests(unittest.TestCase):
    def test_split_task(self):
        self.assertEqual(split_qualified("P2.S3.T1"), ("P2", "S3", "T1"))
    def test_split_slice(self):
        self.assertEqual(split_qualified("P2.S3"), ("P2", "S3", None))
    def test_split_phase(self):
        self.assertEqual(split_qualified("P2"), ("P2", None, None))
    def test_split_short_phase(self):
        self.assertEqual(split_qualified("S3"), (None, "S3", None))
```

- [ ] **Step 2: Run tests, verify all fail**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_ids -v`
Expected: ImportError or all-red.

- [ ] **Step 3: Implement ids.py**

```python
# tools/tasktool/ids.py
from __future__ import annotations
import re
from typing import Literal

Kind = Literal["phase", "slice", "task", "cross"]

class IdParseError(ValueError):
    pass

_PHASE = r"P\d+"
_SLICE = r"S\d+[a-z]?"
_TASK = r"T\d+"
_CROSS = r"X\d+"

_SHORT_RE = re.compile(rf"^({_PHASE}|{_SLICE}|{_TASK}|{_CROSS})$")
_QUALIFIED_RE = re.compile(
    rf"^({_PHASE})(?:\.({_SLICE}))?(?:\.({_TASK}))?$"
)

def parse_id(value: str) -> tuple[Kind, str]:
    """Return (kind, normalised-id). Accepts short or qualified form."""
    if not value:
        raise IdParseError("empty id")
    if "." in value:
        m = _QUALIFIED_RE.match(value)
        if not m:
            raise IdParseError(f"malformed qualified id: {value!r}")
        phase, slice_, task = m.groups()
        if task:
            return ("task", value)
        if slice_:
            return ("slice", value)
        return ("phase", phase)
    m = _SHORT_RE.match(value)
    if not m:
        raise IdParseError(f"malformed id: {value!r}")
    head = value[0]
    return ({"P": "phase", "S": "slice", "T": "task", "X": "cross"}[head], value)

def kind_of(value: str) -> Kind:
    return parse_id(value)[0]

def is_slice_id(value: str) -> bool:
    return kind_of(value) == "slice"

def fully_qualify(value: str, *, phase: str | None = None, slice: str | None = None) -> str:
    parse_id(value)  # validate
    if "." in value:
        return value
    head = value[0]
    if head == "P" or head == "X":
        return value
    if head == "S":
        if not phase:
            raise IdParseError(f"cannot qualify slice {value!r} without phase context")
        return f"{phase}.{value}"
    if head == "T":
        if not phase or not slice:
            raise IdParseError(f"cannot qualify task {value!r} without phase+slice context")
        return f"{phase}.{slice}.{value}"
    raise IdParseError(f"unreachable: {value!r}")

def split_qualified(value: str) -> tuple[str | None, str | None, str | None]:
    """Return (phase, slice, task) components; None for missing levels."""
    parse_id(value)
    if "." not in value:
        head = value[0]
        if head == "P":
            return (value, None, None)
        if head == "S":
            return (None, value, None)
        if head == "T":
            return (None, None, value)
        return (None, None, None)  # cross
    m = _QUALIFIED_RE.match(value)
    assert m
    return tuple(m.groups())  # type: ignore[return-value]
```

- [ ] **Step 4: Run tests, verify green**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_ids -v`
Expected: all 17 tests pass.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/ids.py tools/tasktool/tests/test_ids.py
git commit -m "P2.S1: ID parsing and qualification"
```

---

## Task 3: Data model (model.py)

**Files:**
- Create: `tools/tasktool/model.py`
- Create: `tools/tasktool/tests/test_model.py`

- [ ] **Step 1: Write failing tests**

```python
# tools/tasktool/tests/test_model.py
from __future__ import annotations
import unittest
from tasktool.model import (
    Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status, SCHEMA_VERSION,
)

class StatusTests(unittest.TestCase):
    def test_status_values(self):
        self.assertEqual(
            {s.value for s in Status},
            {"ready", "in_progress", "blocked", "done"},
        )

class ConstructionTests(unittest.TestCase):
    def test_empty_project(self):
        p = Project(project="superstar")
        self.assertEqual(p.schema_version, SCHEMA_VERSION)
        self.assertEqual(p.phases, [])
        self.assertEqual(p.cross_cutting, [])
        self.assertEqual(p.archived_phases, [])

    def test_phase_defaults(self):
        ph = Phase(id="P2", title="tasktool", created="2026-05-17")
        self.assertEqual(ph.status, Status.READY)
        self.assertIsNone(ph.closed)
        self.assertIsNone(ph.spec_path)
        self.assertIsNone(ph.plan_path)
        self.assertIsNone(ph.phase_reviewer_chain)
        self.assertEqual(ph.notes, "")
        self.assertEqual(ph.slices, [])

    def test_slice_defaults(self):
        s = Slice(id="S1", title="CLI core", created="2026-05-17")
        self.assertEqual(s.status, Status.READY)
        self.assertIsNone(s.blocked_on)
        self.assertIsNone(s.reviewer_chain)
        self.assertEqual(s.refs, [])
        self.assertEqual(s.tasks, [])

    def test_task_defaults(self):
        t = Task(id="T1", title="x", created="2026-05-17")
        self.assertEqual(t.status, Status.READY)
        self.assertIsNone(t.closed)
        self.assertEqual(t.refs, [])

    def test_cross_defaults(self):
        x = CrossCutting(id="X1", title="x", created="2026-05-17")
        self.assertEqual(x.status, Status.READY)

    def test_blocked_on_id(self):
        b = BlockedOn(kind="id", value="P2.S1")
        self.assertEqual(b.kind, "id")
    def test_blocked_on_external(self):
        b = BlockedOn(kind="external", value="vendor X")
        self.assertEqual(b.value, "vendor X")
```

- [ ] **Step 2: Run, verify red**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_model -v`

- [ ] **Step 3: Implement model.py**

```python
# tools/tasktool/model.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

SCHEMA_VERSION = 1

class Status(str, Enum):
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"

@dataclass(slots=True)
class BlockedOn:
    kind: Literal["id", "external"]
    value: str

@dataclass(slots=True)
class Task:
    id: str
    title: str
    created: str
    status: Status = Status.READY
    closed: str | None = None
    refs: list[str] = field(default_factory=list)
    notes: str = ""

@dataclass(slots=True)
class Slice:
    id: str
    title: str
    created: str
    status: Status = Status.READY
    closed: str | None = None
    blocked_on: BlockedOn | None = None
    plan_path: str | None = None
    refs: list[str] = field(default_factory=list)
    notes: str = ""
    reviewer_chain: str | None = None
    tasks: list[Task] = field(default_factory=list)

@dataclass(slots=True)
class Phase:
    id: str
    title: str
    created: str
    status: Status = Status.READY
    closed: str | None = None
    spec_path: str | None = None
    plan_path: str | None = None
    phase_reviewer_chain: str | None = None
    notes: str = ""
    slices: list[Slice] = field(default_factory=list)

@dataclass(slots=True)
class CrossCutting:
    id: str
    title: str
    created: str
    status: Status = Status.READY
    closed: str | None = None
    refs: list[str] = field(default_factory=list)
    notes: str = ""

@dataclass(slots=True)
class ArchivedPhase:
    id: str
    title: str
    archived_path: str
    archived_date: str

@dataclass(slots=True)
class Project:
    project: str
    schema_version: int = SCHEMA_VERSION
    north_star: str = ""
    last_reviewed: str | None = None
    phases: list[Phase] = field(default_factory=list)
    cross_cutting: list[CrossCutting] = field(default_factory=list)
    archived_phases: list[ArchivedPhase] = field(default_factory=list)
```

- [ ] **Step 4: Run tests green**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_model -v`
Expected: 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/model.py tools/tasktool/tests/test_model.py
git commit -m "P2.S1: data model dataclasses"
```

---

## Task 4: Canonical serializer (serialize.py)

**Files:**
- Create: `tools/tasktool/serialize.py`
- Create: `tools/tasktool/tests/test_serialize.py`

- [ ] **Step 1: Write failing tests**

```python
# tools/tasktool/tests/test_serialize.py
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from tasktool.model import Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status
from tasktool.serialize import (
    load_project, save_project, dumps_canonical, loads_project, to_dict, from_dict,
)

class RoundTripTests(unittest.TestCase):
    def test_empty_project_roundtrip(self):
        p = Project(project="demo")
        d = to_dict(p)
        back = from_dict(d)
        self.assertEqual(back, p)

    def test_full_project_roundtrip(self):
        p = Project(project="demo", north_star="x", last_reviewed="2026-05-17")
        ph = Phase(id="P1", title="phase", created="2026-05-17", status=Status.IN_PROGRESS)
        s = Slice(
            id="S1", title="slice", created="2026-05-17", status=Status.BLOCKED,
            blocked_on=BlockedOn(kind="id", value="P1.S2"),
            refs=["a.md", "b.md"],
        )
        s.tasks.append(Task(id="T1", title="task", created="2026-05-17"))
        ph.slices.append(s)
        p.phases.append(ph)
        p.cross_cutting.append(CrossCutting(id="X1", title="x", created="2026-05-17"))

        back = from_dict(to_dict(p))
        self.assertEqual(back, p)

class CanonicalFormatTests(unittest.TestCase):
    def test_dumps_sorted_keys(self):
        p = Project(project="demo")
        out = dumps_canonical(p)
        parsed = json.loads(out)
        self.assertEqual(parsed["project"], "demo")
        # sort_keys → "phases" before "project" before "schema_version"
        keys = list(parsed.keys())
        self.assertEqual(keys, sorted(keys))

    def test_dumps_trailing_newline(self):
        out = dumps_canonical(Project(project="demo"))
        self.assertTrue(out.endswith("\n"))

    def test_dumps_indent_two(self):
        out = dumps_canonical(Project(project="demo"))
        self.assertIn("\n  ", out)

class DiskIOTests(unittest.TestCase):
    def test_save_then_load(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tasklist.json"
            p = Project(project="demo")
            save_project(p, path)
            loaded = load_project(path)
            self.assertEqual(loaded, p)

    def test_save_is_canonical_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tasklist.json"
            p = Project(project="demo")
            save_project(p, path)
            on_disk = path.read_text(encoding="utf-8")
            self.assertEqual(on_disk, dumps_canonical(p))
```

- [ ] **Step 2: Run, verify red**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_serialize -v`

- [ ] **Step 3: Implement serialize.py**

```python
# tools/tasktool/serialize.py
from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path
from tasktool.model import (
    Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, BlockedOn, Status, SCHEMA_VERSION,
)

def to_dict(p: Project) -> dict:
    def _coerce(obj):
        if isinstance(obj, Status):
            return obj.value
        return obj
    raw = asdict(p)
    # asdict recurses; convert any Status enum values that survived to strings.
    def walk(node):
        if isinstance(node, dict):
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return _coerce(node)
    return walk(raw)

def from_dict(d: dict) -> Project:
    def _status(v):
        return Status(v) if isinstance(v, str) else v
    def _task(td):
        return Task(
            id=td["id"], title=td["title"], created=td["created"],
            status=_status(td.get("status", "ready")),
            closed=td.get("closed"),
            refs=list(td.get("refs", [])),
            notes=td.get("notes", ""),
        )
    def _blocked(b):
        return None if b is None else BlockedOn(kind=b["kind"], value=b["value"])
    def _slice(sd):
        return Slice(
            id=sd["id"], title=sd["title"], created=sd["created"],
            status=_status(sd.get("status", "ready")),
            closed=sd.get("closed"),
            blocked_on=_blocked(sd.get("blocked_on")),
            plan_path=sd.get("plan_path"),
            refs=list(sd.get("refs", [])),
            notes=sd.get("notes", ""),
            reviewer_chain=sd.get("reviewer_chain"),
            tasks=[_task(t) for t in sd.get("tasks", [])],
        )
    def _phase(pd):
        return Phase(
            id=pd["id"], title=pd["title"], created=pd["created"],
            status=_status(pd.get("status", "ready")),
            closed=pd.get("closed"),
            spec_path=pd.get("spec_path"),
            plan_path=pd.get("plan_path"),
            phase_reviewer_chain=pd.get("phase_reviewer_chain"),
            notes=pd.get("notes", ""),
            slices=[_slice(s) for s in pd.get("slices", [])],
        )
    def _cross(xd):
        return CrossCutting(
            id=xd["id"], title=xd["title"], created=xd["created"],
            status=_status(xd.get("status", "ready")),
            closed=xd.get("closed"),
            refs=list(xd.get("refs", [])),
            notes=xd.get("notes", ""),
        )
    def _arch(ad):
        return ArchivedPhase(
            id=ad["id"], title=ad["title"],
            archived_path=ad["archived_path"], archived_date=ad["archived_date"],
        )
    return Project(
        project=d["project"],
        schema_version=d.get("schema_version", SCHEMA_VERSION),
        north_star=d.get("north_star", ""),
        last_reviewed=d.get("last_reviewed"),
        phases=[_phase(p) for p in d.get("phases", [])],
        cross_cutting=[_cross(x) for x in d.get("cross_cutting", [])],
        archived_phases=[_arch(a) for a in d.get("archived_phases", [])],
    )

def dumps_canonical(p: Project) -> str:
    body = json.dumps(to_dict(p), indent=2, sort_keys=True, ensure_ascii=False)
    return body + "\n"

def loads_project(text: str) -> Project:
    return from_dict(json.loads(text))

def load_project(path: Path) -> Project:
    return loads_project(path.read_text(encoding="utf-8"))

def save_project(p: Project, path: Path) -> None:
    """Atomic write: tempfile + rename. Always canonical bytes."""
    text = dumps_canonical(p)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
```

- [ ] **Step 4: Run tests green**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_serialize -v`
Expected: 6 tests pass.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/serialize.py tools/tasktool/tests/test_serialize.py
git commit -m "P2.S1: canonical JSON serializer with atomic write"
```

---

## Task 5: Validation rules (validate.py)

**Files:**
- Create: `tools/tasktool/validate.py`
- Create: `tools/tasktool/tests/test_validate.py`

- [ ] **Step 1: Write failing tests**

```python
# tools/tasktool/tests/test_validate.py
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from tasktool.model import Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status
from tasktool.serialize import save_project, dumps_canonical
from tasktool.validate import (
    validate_project, ValidationError, strict_format_check, normalise_file,
)

def _project_with_slice(**slice_kwargs) -> Project:
    p = Project(project="demo")
    ph = Phase(id="P1", title="phase", created="2026-05-17")
    s = Slice(id="S1", title="slice", created="2026-05-17", **slice_kwargs)
    ph.slices.append(s)
    p.phases.append(ph)
    return p

class IdFormatTests(unittest.TestCase):
    def test_valid(self):
        p = _project_with_slice()
        validate_project(p)  # no raise

    def test_bad_phase_id(self):
        p = _project_with_slice()
        p.phases[0].id = "Phase1"
        with self.assertRaises(ValidationError):
            validate_project(p)

class UniquenessTests(unittest.TestCase):
    def test_duplicate_phase_ids(self):
        p = Project(project="demo")
        p.phases.append(Phase(id="P1", title="a", created="2026-05-17"))
        p.phases.append(Phase(id="P1", title="b", created="2026-05-17"))
        with self.assertRaises(ValidationError) as ctx:
            validate_project(p)
        self.assertIn("duplicate", str(ctx.exception).lower())

    def test_duplicate_slice_ids_within_phase(self):
        p = _project_with_slice()
        p.phases[0].slices.append(Slice(id="S1", title="dup", created="2026-05-17"))
        with self.assertRaises(ValidationError):
            validate_project(p)

class StatusTransitionTests(unittest.TestCase):
    def test_done_requires_closed(self):
        p = _project_with_slice(status=Status.DONE, closed=None)
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_done_with_closed_ok(self):
        p = _project_with_slice(status=Status.DONE, closed="2026-05-17")
        validate_project(p)

    def test_blocked_on_phase_rejected(self):
        p = _project_with_slice()
        p.phases[0].status = Status.BLOCKED
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_blocked_on_task_rejected(self):
        p = _project_with_slice()
        p.phases[0].slices[0].tasks.append(
            Task(id="T1", title="t", created="2026-05-17", status=Status.BLOCKED),
        )
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_blocked_slice_requires_blocked_on(self):
        p = _project_with_slice(status=Status.BLOCKED, blocked_on=None)
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_blocked_slice_with_blocked_on_ok(self):
        p = _project_with_slice(
            status=Status.BLOCKED,
            blocked_on=BlockedOn(kind="id", value="P1.S2"),
        )
        validate_project(p)

class DateOrderTests(unittest.TestCase):
    def test_closed_before_created_rejected(self):
        p = _project_with_slice(
            status=Status.DONE, closed="2026-05-16", created="2026-05-17",
        )
        # need created set on slice itself; the helper already does that.
        p.phases[0].slices[0].created = "2026-05-17"
        with self.assertRaises(ValidationError):
            validate_project(p)

class DateFormatTests(unittest.TestCase):
    def test_malformed_created_rejected(self):
        p = _project_with_slice()
        p.phases[0].slices[0].created = "17-05-2026"
        with self.assertRaises(ValidationError) as ctx:
            validate_project(p)
        self.assertIn("date", str(ctx.exception).lower())

    def test_malformed_closed_rejected(self):
        p = _project_with_slice(status=Status.DONE, closed="not-a-date")
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_invalid_calendar_month_rejected(self):
        p = _project_with_slice()
        p.phases[0].slices[0].created = "2026-99-99"
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_invalid_calendar_day_rejected(self):
        p = _project_with_slice()
        p.phases[0].slices[0].created = "2026-02-31"
        with self.assertRaises(ValidationError):
            validate_project(p)

    def test_valid_calendar_date_accepted(self):
        p = _project_with_slice()
        p.phases[0].slices[0].created = "2026-02-28"
        validate_project(p)  # no raise

class PathWarningTests(unittest.TestCase):
    def test_missing_ref_emits_warning(self):
        from tasktool.validate import find_path_warnings
        p = _project_with_slice(refs=["nonexistent.md"])
        with tempfile.TemporaryDirectory() as td:
            warnings = find_path_warnings(p, Path(td))
        self.assertTrue(any("nonexistent.md" in w for w in warnings))

    def test_existing_ref_no_warning(self):
        from tasktool.validate import find_path_warnings
        p = _project_with_slice(refs=["a.md"])
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "a.md").write_text("", encoding="utf-8")
            warnings = find_path_warnings(p, Path(td))
        self.assertEqual(warnings, [])

class StrictFormatTests(unittest.TestCase):
    def test_canonical_passes(self):
        p = Project(project="demo")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tasklist.json"
            save_project(p, path)
            strict_format_check(path)  # no raise

    def test_non_canonical_fails(self):
        p = Project(project="demo")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tasklist.json"
            path.write_text(dumps_canonical(p).replace("  ", "    "), encoding="utf-8")
            with self.assertRaises(ValidationError):
                strict_format_check(path)

    def test_normalise_rewrites_file(self):
        p = Project(project="demo")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tasklist.json"
            path.write_text(dumps_canonical(p).replace("  ", "    "), encoding="utf-8")
            normalise_file(path)
            strict_format_check(path)  # now passes
```

- [ ] **Step 2: Run red**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_validate -v`

- [ ] **Step 3: Implement validate.py**

```python
# tools/tasktool/validate.py
from __future__ import annotations
import re
from pathlib import Path
from tasktool.model import Project, Phase, Slice, Task, CrossCutting, Status
from tasktool.serialize import load_project, save_project, dumps_canonical
from tasktool.ids import parse_id, IdParseError

class ValidationError(ValueError):
    """Raised when the project violates a validation rule."""

import datetime as _dt

_PHASE_RE = re.compile(r"^P\d+$")
_SLICE_RE = re.compile(r"^S\d+[a-z]?$")
_TASK_RE = re.compile(r"^T\d+$")
_CROSS_RE = re.compile(r"^X\d+$")

def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValidationError(msg)

def _check_id(value: str, pattern: re.Pattern[str], scope: str) -> None:
    _require(bool(pattern.match(value)), f"{scope}: malformed id {value!r}")

def _check_date(value: str | None, scope: str, field: str) -> None:
    """Validate that value parses as a real ISO 8601 calendar date.
    Rejects shape-only matches like 2026-99-99 or 2026-02-31."""
    if value is None:
        return
    try:
        _dt.date.fromisoformat(value)
    except ValueError as e:
        raise ValidationError(
            f"{scope}.{field}: malformed date {value!r} (expected YYYY-MM-DD calendar date): {e}"
        ) from e

def _check_dates(created: str, closed: str | None, scope: str) -> None:
    _check_date(created, scope, "created")
    _check_date(closed, scope, "closed")
    if closed is not None and closed < created:
        raise ValidationError(f"{scope}: closed {closed} precedes created {created}")

def _check_task(t: Task, scope: str) -> None:
    _check_id(t.id, _TASK_RE, scope)
    _require(t.status != Status.BLOCKED, f"{scope}: tasks cannot be blocked (slice-only)")
    if t.status == Status.DONE:
        _require(t.closed is not None, f"{scope}: status=done requires closed date")
    _check_dates(t.created, t.closed, scope)

def _check_slice(s: Slice, scope: str) -> None:
    _check_id(s.id, _SLICE_RE, scope)
    if s.status == Status.BLOCKED:
        _require(s.blocked_on is not None, f"{scope}: blocked requires blocked_on")
    if s.blocked_on is not None:
        _require(s.status == Status.BLOCKED, f"{scope}: blocked_on without blocked status")
    if s.status == Status.DONE:
        _require(s.closed is not None, f"{scope}: status=done requires closed date")
    _check_dates(s.created, s.closed, scope)
    seen: set[str] = set()
    for t in s.tasks:
        sub = f"{scope}.{t.id}"
        _require(t.id not in seen, f"{sub}: duplicate task id")
        seen.add(t.id)
        _check_task(t, sub)

def _check_phase(p: Phase, scope: str) -> None:
    _check_id(p.id, _PHASE_RE, scope)
    _require(p.status != Status.BLOCKED, f"{scope}: phases cannot be blocked")
    if p.status == Status.DONE:
        _require(p.closed is not None, f"{scope}: status=done requires closed date")
    _check_dates(p.created, p.closed, scope)
    seen: set[str] = set()
    for s in p.slices:
        sub = f"{scope}.{s.id}"
        _require(s.id not in seen, f"{sub}: duplicate slice id")
        seen.add(s.id)
        _check_slice(s, sub)

def _check_cross(c: CrossCutting, scope: str) -> None:
    _check_id(c.id, _CROSS_RE, scope)
    _require(c.status != Status.BLOCKED, f"{scope}: cross-cutting cannot be blocked")
    if c.status == Status.DONE:
        _require(c.closed is not None, f"{scope}: status=done requires closed date")
    _check_dates(c.created, c.closed, scope)

def validate_project(p: Project) -> None:
    """Raise ValidationError on rule violation. Returns None on clean."""
    seen_phase: set[str] = set()
    for ph in p.phases:
        _require(ph.id not in seen_phase, f"P*: duplicate phase id {ph.id}")
        seen_phase.add(ph.id)
        _check_phase(ph, ph.id)
    seen_cross: set[str] = set()
    for c in p.cross_cutting:
        _require(c.id not in seen_cross, f"X*: duplicate cross id {c.id}")
        seen_cross.add(c.id)
        _check_cross(c, c.id)

def find_path_warnings(p: Project, repo_root: Path) -> list[str]:
    """Walk every spec_path / plan_path / refs[] and return a list of warning strings
    for paths that do not exist on disk. Non-fatal — used by `tasktool validate`."""
    warnings: list[str] = []
    def _check(rel: str | None, scope: str) -> None:
        if rel is None:
            return
        if not (repo_root / rel).exists():
            warnings.append(f"{scope}: path does not exist: {rel}")
    for ph in p.phases:
        _check(ph.spec_path, f"{ph.id}.spec_path")
        _check(ph.plan_path, f"{ph.id}.plan_path")
        for s in ph.slices:
            _check(s.plan_path, f"{ph.id}.{s.id}.plan_path")
            for r in s.refs:
                _check(r, f"{ph.id}.{s.id}.refs")
            for t in s.tasks:
                for r in t.refs:
                    _check(r, f"{ph.id}.{s.id}.{t.id}.refs")
    for c in p.cross_cutting:
        for r in c.refs:
            _check(r, f"{c.id}.refs")
    return warnings

def strict_format_check(path: Path) -> None:
    """Re-serialise and compare bytes. Raises ValidationError on mismatch."""
    text = path.read_text(encoding="utf-8")
    project = load_project(path)
    canonical = dumps_canonical(project)
    if text != canonical:
        raise ValidationError(
            f"{path}: not in canonical format. Run `tasktool validate --normalise` to fix."
        )

def normalise_file(path: Path) -> None:
    """Load, validate, and re-save in canonical format."""
    p = load_project(path)
    validate_project(p)
    save_project(p, path)
```

- [ ] **Step 4: Run green**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_validate -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/validate.py tools/tasktool/tests/test_validate.py
git commit -m "P2.S1: validation rules + strict-format + normalise"
```

---

## Task 6: ID allocation (allocate.py)

**Files:**
- Create: `tools/tasktool/allocate.py`
- Create: `tools/tasktool/tests/test_allocate.py`

- [ ] **Step 1: Write failing tests**

```python
# tools/tasktool/tests/test_allocate.py
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from tasktool.model import Project, Phase, Slice, CrossCutting
from tasktool.allocate import (
    next_phase_id, next_slice_id, next_task_id, next_cross_id, scan_orphan_ids,
)

def _mkfile(root: Path, rel: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("", encoding="utf-8")

class PhaseAllocTests(unittest.TestCase):
    def test_empty_project(self):
        p = Project(project="demo")
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(next_phase_id(p, Path(td)), "P1")

    def test_existing_phases(self):
        p = Project(project="demo")
        p.phases.append(Phase(id="P1", title="a", created="2026-05-17"))
        p.phases.append(Phase(id="P3", title="b", created="2026-05-17"))
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(next_phase_id(p, Path(td)), "P4")

    def test_orphan_in_specs(self):
        p = Project(project="demo")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _mkfile(root, "docs/specs/2026-05-17-P7-orphan-spec.md")
            self.assertEqual(next_phase_id(p, root), "P8")

    def test_orphan_in_reviewer(self):
        p = Project(project="demo")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "docs/reviewer/something-P5-post-slice").mkdir(parents=True)
            self.assertEqual(next_phase_id(p, root), "P6")

class SliceAllocTests(unittest.TestCase):
    def test_first_slice(self):
        p = Project(project="demo")
        p.phases.append(Phase(id="P1", title="a", created="2026-05-17"))
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(next_slice_id(p, "P1", Path(td)), "S1")

    def test_next_slice(self):
        p = Project(project="demo")
        ph = Phase(id="P1", title="a", created="2026-05-17")
        ph.slices.append(Slice(id="S1", title="a", created="2026-05-17"))
        ph.slices.append(Slice(id="S2a", title="a", created="2026-05-17"))
        p.phases.append(ph)
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(next_slice_id(p, "P1", Path(td)), "S3")

    def test_followup_letter(self):
        p = Project(project="demo")
        ph = Phase(id="P1", title="a", created="2026-05-17")
        ph.slices.append(Slice(id="S1", title="a", created="2026-05-17"))
        ph.slices.append(Slice(id="S1a", title="a", created="2026-05-17"))
        p.phases.append(ph)
        with tempfile.TemporaryDirectory() as td:
            from tasktool.allocate import next_followup_letter
            self.assertEqual(next_followup_letter(p, "P1", "S1", Path(td)), "S1b")

class TaskAllocTests(unittest.TestCase):
    def test_first_task(self):
        p = Project(project="demo")
        ph = Phase(id="P1", title="a", created="2026-05-17")
        ph.slices.append(Slice(id="S1", title="a", created="2026-05-17"))
        p.phases.append(ph)
        self.assertEqual(next_task_id(p, "P1", "S1"), "T1")

class CrossAllocTests(unittest.TestCase):
    def test_first_cross(self):
        p = Project(project="demo")
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(next_cross_id(p, Path(td)), "X1")
```

- [ ] **Step 2: Run red**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_allocate -v`

- [ ] **Step 3: Implement allocate.py**

```python
# tools/tasktool/allocate.py
from __future__ import annotations
import re
from pathlib import Path
from tasktool.model import Project

_PHASE_PAT = re.compile(r"\bP(\d+)\b")
_SLICE_PAT = re.compile(r"\bS(\d+)([a-z]?)\b")
_TASK_PAT = re.compile(r"\bT(\d+)\b")
_CROSS_PAT = re.compile(r"\bX(\d+)\b")

def scan_orphan_ids(repo_root: Path, kind: str) -> set[int]:
    """Scan docs/specs, docs/plans, docs/reviewer folder names for IDs of the given kind.
    kind ∈ {phase, slice, task, cross}. Returns the set of integer suffixes seen."""
    out: set[int] = set()
    pat = {"phase": _PHASE_PAT, "slice": _SLICE_PAT, "task": _TASK_PAT, "cross": _CROSS_PAT}[kind]
    for sub in ("docs/specs", "docs/plans"):
        d = repo_root / sub
        if not d.exists():
            continue
        for p in d.iterdir():
            for m in pat.finditer(p.name):
                out.add(int(m.group(1)))
    rev = repo_root / "docs/reviewer"
    if rev.exists():
        for d in rev.iterdir():
            for m in pat.finditer(d.name):
                out.add(int(m.group(1)))
    return out

def _phase_nums(p: Project) -> set[int]:
    nums = {int(ph.id[1:]) for ph in p.phases}
    nums |= {int(a.id[1:]) for a in p.archived_phases}
    return nums

def next_phase_id(p: Project, repo_root: Path) -> str:
    used = _phase_nums(p) | scan_orphan_ids(repo_root, "phase")
    n = max(used, default=0) + 1
    return f"P{n}"

def next_slice_id(p: Project, phase_id: str, repo_root: Path) -> str:
    phase = next((ph for ph in p.phases if ph.id == phase_id), None)
    if phase is None:
        raise KeyError(f"phase {phase_id} not found")
    used: set[int] = set()
    for s in phase.slices:
        m = _SLICE_PAT.match(s.id)
        if m:
            used.add(int(m.group(1)))
    # also pull orphan slice IDs that reference this phase
    for sub in ("docs/specs", "docs/plans"):
        d = repo_root / sub
        if not d.exists():
            continue
        for fp in d.iterdir():
            if phase_id.lower() in fp.name.lower():
                for m in _SLICE_PAT.finditer(fp.name):
                    used.add(int(m.group(1)))
    n = max(used, default=0) + 1
    return f"S{n}"

def next_followup_letter(p: Project, phase_id: str, base_slice: str, repo_root: Path) -> str:
    phase = next((ph for ph in p.phases if ph.id == phase_id), None)
    if phase is None:
        raise KeyError(f"phase {phase_id} not found")
    base_num = re.match(r"^S(\d+)", base_slice)
    if not base_num:
        raise ValueError(f"bad slice id: {base_slice}")
    base = base_num.group(1)
    used_letters: set[str] = set()
    for s in phase.slices:
        m = re.match(rf"^S{base}([a-z])$", s.id)
        if m:
            used_letters.add(m.group(1))
    nxt = "a"
    while nxt in used_letters:
        nxt = chr(ord(nxt) + 1)
        if nxt > "z":
            raise RuntimeError(f"exhausted follow-up letters under S{base}")
    return f"S{base}{nxt}"

def next_task_id(p: Project, phase_id: str, slice_id: str) -> str:
    phase = next((ph for ph in p.phases if ph.id == phase_id), None)
    if phase is None:
        raise KeyError(f"phase {phase_id} not found")
    slc = next((s for s in phase.slices if s.id == slice_id), None)
    if slc is None:
        raise KeyError(f"slice {phase_id}.{slice_id} not found")
    used = {int(t.id[1:]) for t in slc.tasks}
    n = max(used, default=0) + 1
    return f"T{n}"

def next_cross_id(p: Project, repo_root: Path) -> str:
    used = {int(c.id[1:]) for c in p.cross_cutting} | scan_orphan_ids(repo_root, "cross")
    n = max(used, default=0) + 1
    return f"X{n}"
```

- [ ] **Step 4: Run green**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_allocate -v`

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/allocate.py tools/tasktool/tests/test_allocate.py
git commit -m "P2.S1: orphan-aware ID allocation"
```

---

## Task 7: Reviewer-gate (reviewer_gate.py)

**Files:**
- Create: `tools/tasktool/reviewer_gate.py`
- Create: `tools/tasktool/tests/test_reviewer_gate.py`

- [ ] **Step 1: Write failing tests**

```python
# tools/tasktool/tests/test_reviewer_gate.py
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from tasktool.reviewer_gate import (
    discover_chain, read_latest_verdict, check_gate, GateError, GatePass,
)

def _write_chain(root: Path, name: str, verdict: str | None) -> Path:
    chain = root / "docs/reviewer" / name
    chain.mkdir(parents=True)
    manifest = {"rounds": [{"round": 1, "merged_verdict": verdict, "status": "ok"}]}
    (chain / "chain.json").write_text(json.dumps(manifest), encoding="utf-8")
    return chain

class DiscoveryTests(unittest.TestCase):
    def test_discover_by_explicit_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            chain = _write_chain(root, "p2-s1-post-slice", "ready")
            found = discover_chain(root, "P2.S1", "post-slice", explicit=chain)
            self.assertEqual(found, chain)

    def test_discover_by_id_suffix(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            chain = _write_chain(root, "foo-p2-s1-post-slice", "ready")
            found = discover_chain(root, "P2.S1", "post-slice")
            self.assertEqual(found, chain)

    def test_discover_zero_matches_raises(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(GateError):
                discover_chain(Path(td), "P2.S1", "post-slice")

    def test_discover_multiple_matches_raises(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_chain(root, "a-p2-s1-post-slice", "ready")
            _write_chain(root, "b-p2-s1-post-slice", "ready")
            with self.assertRaises(GateError):
                discover_chain(root, "P2.S1", "post-slice")

class VerdictTests(unittest.TestCase):
    def test_ready_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            chain = _write_chain(root, "p2-s1-post-slice", "ready")
            result = check_gate(root, "P2.S1", "post-slice")
            self.assertIsInstance(result, GatePass)
            self.assertEqual(result.verdict, "ready")

    def test_ready_with_small_edits_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_chain(root, "p2-s1-post-slice", "ready with small edits")
            result = check_gate(root, "P2.S1", "post-slice")
            self.assertEqual(result.verdict, "ready with small edits")

    def test_revise_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_chain(root, "p2-s1-post-slice", "revise")
            with self.assertRaises(GateError):
                check_gate(root, "P2.S1", "post-slice")

    def test_null_verdict_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_chain(root, "p2-s1-post-slice", None)
            with self.assertRaises(GateError):
                check_gate(root, "P2.S1", "post-slice")
```

- [ ] **Step 2: Run red**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_reviewer_gate -v`

- [ ] **Step 3: Implement reviewer_gate.py**

```python
# tools/tasktool/reviewer_gate.py
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

ACCEPTABLE_VERDICTS = {"ready", "ready with small edits"}

class GateError(RuntimeError):
    pass

@dataclass(slots=True)
class GatePass:
    chain: Path
    verdict: str

def _id_token(work_id: str) -> str:
    return work_id.replace(".", "-").lower()

def discover_chain(repo_root: Path, work_id: str, kind: str, *, explicit: Path | None = None) -> Path:
    """Find the reviewer chain folder. kind ∈ {post-slice, post-phase}.
    If explicit is given, just validate it. Otherwise search docs/reviewer/."""
    if explicit is not None:
        if not (explicit / "chain.json").is_file():
            raise GateError(f"{explicit}: not a reviewer chain folder (missing chain.json)")
        return explicit
    base = repo_root / "docs/reviewer"
    if not base.exists():
        raise GateError(f"no docs/reviewer/ directory in {repo_root}")
    token = _id_token(work_id)
    suffix = f"-{kind}"
    candidates = [
        d for d in base.iterdir()
        if d.is_dir() and d.name.endswith(suffix) and token in d.name.lower()
    ]
    if not candidates:
        raise GateError(
            f"no reviewer chain found for {work_id} {kind} under docs/reviewer/"
        )
    if len(candidates) > 1:
        names = ", ".join(c.name for c in candidates)
        raise GateError(
            f"multiple reviewer chains match {work_id} {kind}: {names}. "
            f"Pass --reviewer-chain to disambiguate."
        )
    return candidates[0]

def read_latest_verdict(chain: Path) -> str | None:
    manifest = json.loads((chain / "chain.json").read_text(encoding="utf-8"))
    rounds = manifest.get("rounds", [])
    if not rounds:
        return None
    last = rounds[-1]
    return last.get("merged_verdict") or last.get("verdict")

def check_gate(repo_root: Path, work_id: str, kind: str, *, explicit: Path | None = None) -> GatePass:
    chain = discover_chain(repo_root, work_id, kind, explicit=explicit)
    verdict = read_latest_verdict(chain)
    if verdict not in ACCEPTABLE_VERDICTS:
        raise GateError(
            f"{chain.name}: latest verdict is {verdict!r}; need one of "
            f"{sorted(ACCEPTABLE_VERDICTS)}. Apply findings and re-run the reviewer."
        )
    return GatePass(chain=chain, verdict=verdict)
```

- [ ] **Step 4: Run green**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_reviewer_gate -v`

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/reviewer_gate.py tools/tasktool/tests/test_reviewer_gate.py
git commit -m "P2.S1: reviewer-gate chain discovery and verdict check"
```

---

## Task 8: Commands — init + create

**Files:**
- Create: `tools/tasktool/commands.py`
- Create: `tools/tasktool/tests/test_commands.py`

- [ ] **Step 1: Write failing tests**

```python
# tools/tasktool/tests/test_commands.py
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from tasktool import commands
from tasktool.serialize import load_project
from tasktool.model import Status

class _Tmp:
    def __init__(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        (self.root / "docs").mkdir()
    def cleanup(self):
        self._td.cleanup()

class InitTests(unittest.TestCase):
    def test_init_creates_empty_project(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="superstar", north_star="ns")
            path = t.root / "docs/tasklist.json"
            self.assertTrue(path.exists())
            p = load_project(path)
            self.assertEqual(p.project, "superstar")
            self.assertEqual(p.north_star, "ns")
        finally:
            t.cleanup()

    def test_init_refuses_existing_without_force(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="a")
            with self.assertRaises(commands.CommandError):
                commands.cmd_init(repo_root=t.root, project="b")
        finally:
            t.cleanup()

    def test_init_without_project_uses_repo_root_name(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root)
            p = load_project(t.root / "docs/tasklist.json")
            self.assertEqual(p.project, t.root.name)
        finally:
            t.cleanup()

class CreateTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
    def tearDown(self):
        self.t.cleanup()

    def test_create_phase(self):
        new_id = commands.cmd_create_phase(repo_root=self.t.root, title="Tasktool")
        self.assertEqual(new_id, "P1")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(len(p.phases), 1)
        self.assertEqual(p.phases[0].title, "Tasktool")

    def test_create_slice(self):
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        new_id = commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="CLI core")
        self.assertEqual(new_id, "S1")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].title, "CLI core")

    def test_create_followup_slice(self):
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
        fid = commands.cmd_create_slice(
            repo_root=self.t.root, phase_id="P1", title="S1a", follow_up="S1",
        )
        self.assertEqual(fid, "S1a")

    def test_create_task(self):
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
        new_id = commands.cmd_create_task(
            repo_root=self.t.root, slice_id="P1.S1", title="implement",
        )
        self.assertEqual(new_id, "T1")

    def test_create_cross(self):
        new_id = commands.cmd_create_cross(repo_root=self.t.root, title="docs cleanup")
        self.assertEqual(new_id, "X1")
```

- [ ] **Step 2: Run red**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_commands -v`

- [ ] **Step 3: Implement commands.py (init + create only for now)**

```python
# tools/tasktool/commands.py
from __future__ import annotations
import datetime as _dt
from pathlib import Path
from tasktool.model import (
    Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status,
)
from tasktool.serialize import load_project, save_project
from tasktool.validate import validate_project
from tasktool.allocate import (
    next_phase_id, next_slice_id, next_task_id, next_cross_id, next_followup_letter,
)
from tasktool.ids import split_qualified, kind_of, is_slice_id, parse_id
from tasktool.reviewer_gate import check_gate, GateError, GatePass

class CommandError(RuntimeError):
    pass

DEFAULT_JSON_REL = "docs/tasklist.json"

def _today() -> str:
    return _dt.date.today().isoformat()

def _tasklist_path(repo_root: Path) -> Path:
    return repo_root / DEFAULT_JSON_REL

def _load(repo_root: Path) -> Project:
    path = _tasklist_path(repo_root)
    if not path.exists():
        raise CommandError(f"{path}: tasklist.json not found. Run `tasktool init` first.")
    return load_project(path)

def _save(repo_root: Path, p: Project) -> None:
    validate_project(p)
    save_project(p, _tasklist_path(repo_root))

# ───── init ─────

def cmd_init(*, repo_root: Path, project: str | None = None, north_star: str = "", force: bool = False) -> None:
    """Create empty tasklist.json. If `project` is omitted, derive from repo_root.name
    (matches spec §7.1 syntax `init [--project NAME]`)."""
    path = _tasklist_path(repo_root)
    if path.exists() and not force:
        raise CommandError(f"{path}: already exists. Pass --force to overwrite.")
    path.parent.mkdir(parents=True, exist_ok=True)
    project_name = project or repo_root.name
    _save(repo_root, Project(project=project_name, north_star=north_star, last_reviewed=_today()))

# ───── create ─────

def cmd_create_phase(*, repo_root: Path, title: str, spec: str | None = None, plan: str | None = None) -> str:
    p = _load(repo_root)
    new_id = next_phase_id(p, repo_root)
    p.phases.append(Phase(
        id=new_id, title=title, created=_today(),
        spec_path=spec, plan_path=plan,
    ))
    _save(repo_root, p)
    return new_id

def cmd_create_slice(
    *, repo_root: Path, phase_id: str, title: str,
    follow_up: str | None = None, plan: str | None = None,
) -> str:
    p = _load(repo_root)
    phase = next((ph for ph in p.phases if ph.id == phase_id), None)
    if phase is None:
        raise CommandError(f"phase {phase_id} not found")
    if follow_up is None:
        new_id = next_slice_id(p, phase_id, repo_root)
    else:
        new_id = next_followup_letter(p, phase_id, follow_up, repo_root)
    phase.slices.append(Slice(
        id=new_id, title=title, created=_today(), plan_path=plan,
    ))
    _save(repo_root, p)
    return new_id

def cmd_create_task(*, repo_root: Path, slice_id: str, title: str) -> str:
    """In Task 8, only fully-qualified slice IDs (e.g. P1.S2) are accepted.
    Task 9 extends this to accept unambiguous short IDs by routing through _resolve_id."""
    p = _load(repo_root)
    phase_part, slice_part, _ = split_qualified(slice_id)
    if phase_part is None or slice_part is None:
        raise CommandError(f"task creation requires fully-qualified slice id (e.g. P1.S2), got {slice_id!r}")
    phase = next((ph for ph in p.phases if ph.id == phase_part), None)
    if phase is None:
        raise CommandError(f"phase {phase_part} not found")
    slc = next((s for s in phase.slices if s.id == slice_part), None)
    if slc is None:
        raise CommandError(f"slice {phase_part}.{slice_part} not found")
    new_id = next_task_id(p, phase_part, slice_part)
    slc.tasks.append(Task(id=new_id, title=title, created=_today()))
    _save(repo_root, p)
    return new_id

def cmd_create_cross(*, repo_root: Path, title: str) -> str:
    p = _load(repo_root)
    new_id = next_cross_id(p, repo_root)
    p.cross_cutting.append(CrossCutting(id=new_id, title=title, created=_today()))
    _save(repo_root, p)
    return new_id
```

- [ ] **Step 4: Run green**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_commands -v`

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
git commit -m "P2.S1: init + create commands"
```

---

## Task 9: Commands — set + close + block + unblock (with review gate)

**Files:**
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/tests/test_commands.py`

- [ ] **Step 1: Add failing tests**

Append to `tools/tasktool/tests/test_commands.py`:

```python
import json

def _write_passing_chain(root: Path, name: str, verdict: str = "ready") -> Path:
    chain = root / "docs/reviewer" / name
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text(
        json.dumps({"rounds": [{"round": 1, "merged_verdict": verdict, "status": "ok"}]}),
        encoding="utf-8",
    )
    return chain

class SetStatusTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
        commands.cmd_create_task(repo_root=self.t.root, slice_id="P1.S1", title="T1")
    def tearDown(self):
        self.t.cleanup()

    def test_set_task_in_progress(self):
        commands.cmd_set(repo_root=self.t.root, id="P1.S1.T1", status="in_progress")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].tasks[0].status, Status.IN_PROGRESS)

    def test_set_task_done_auto_stamps_closed(self):
        commands.cmd_set(repo_root=self.t.root, id="P1.S1.T1", status="done")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertIsNotNone(p.phases[0].slices[0].tasks[0].closed)

    def test_set_slice_done_requires_review_gate(self):
        with self.assertRaises(commands.CommandError):
            commands.cmd_set(repo_root=self.t.root, id="P1.S1", status="done")

    def test_set_slice_done_passes_with_chain(self):
        _write_passing_chain(self.t.root, "p1-s1-post-slice", "ready")
        commands.cmd_set(repo_root=self.t.root, id="P1.S1", status="done")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].status, Status.DONE)
        self.assertIsNotNone(p.phases[0].slices[0].reviewer_chain)

    def test_set_slice_done_skip_gate(self):
        commands.cmd_set(
            repo_root=self.t.root, id="P1.S1", status="done", skip_review_gate=True,
        )
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].status, Status.DONE)
        self.assertIn("review gate skipped", p.phases[0].slices[0].notes)

class CloseTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
    def tearDown(self):
        self.t.cleanup()

    def test_close_slice_with_chain_and_refs(self):
        _write_passing_chain(self.t.root, "p1-s1-post-slice", "ready")
        commands.cmd_close(
            repo_root=self.t.root, id="P1.S1",
            refs=["docs/a.md", "docs/b.md"], note="post-impl",
        )
        p = load_project(self.t.root / "docs/tasklist.json")
        s = p.phases[0].slices[0]
        self.assertEqual(s.status, Status.DONE)
        self.assertEqual(s.refs, ["docs/a.md", "docs/b.md"])
        self.assertIn("post-impl", s.notes)

class BlockTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S2")
    def tearDown(self):
        self.t.cleanup()

    def test_block_slice_by_id(self):
        commands.cmd_block(repo_root=self.t.root, slice_id="P1.S1", on="P1.S2")
        p = load_project(self.t.root / "docs/tasklist.json")
        s = p.phases[0].slices[0]
        self.assertEqual(s.status, Status.BLOCKED)
        self.assertEqual(s.blocked_on.kind, "id")
        self.assertEqual(s.blocked_on.value, "P1.S2")

    def test_block_external(self):
        commands.cmd_block(repo_root=self.t.root, slice_id="P1.S1", on="external:vendor")
        p = load_project(self.t.root / "docs/tasklist.json")
        s = p.phases[0].slices[0]
        self.assertEqual(s.blocked_on.kind, "external")
        self.assertEqual(s.blocked_on.value, "vendor")

    def test_block_rejects_task(self):
        commands.cmd_create_task(repo_root=self.t.root, slice_id="P1.S1", title="t")
        with self.assertRaises(commands.CommandError):
            commands.cmd_block(repo_root=self.t.root, slice_id="P1.S1.T1", on="P1.S2")

    def test_unblock(self):
        commands.cmd_block(repo_root=self.t.root, slice_id="P1.S1", on="P1.S2")
        commands.cmd_unblock(repo_root=self.t.root, slice_id="P1.S1")
        p = load_project(self.t.root / "docs/tasklist.json")
        s = p.phases[0].slices[0]
        self.assertEqual(s.status, Status.READY)
        self.assertIsNone(s.blocked_on)

class ShortFormResolutionTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
        commands.cmd_create_task(repo_root=self.t.root, slice_id="P1.S1", title="t")
    def tearDown(self):
        self.t.cleanup()

    def test_short_slice_unambiguous_resolves(self):
        # Only one slice in the project — short form S1 should resolve.
        commands.cmd_note(repo_root=self.t.root, id="S1", append="via short")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertIn("via short", p.phases[0].slices[0].notes)

    def test_short_task_unambiguous_resolves(self):
        commands.cmd_note(repo_root=self.t.root, id="T1", append="via short")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertIn("via short", p.phases[0].slices[0].tasks[0].notes)

    def test_short_slice_ambiguous_rejected(self):
        commands.cmd_create_phase(repo_root=self.t.root, title="P2")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P2", title="S1")
        with self.assertRaises(commands.CommandError) as ctx:
            commands.cmd_note(repo_root=self.t.root, id="S1", append="x")
        self.assertIn("ambiguous", str(ctx.exception).lower())

    def test_create_task_accepts_short_slice(self):
        new_id = commands.cmd_create_task(repo_root=self.t.root, slice_id="S1", title="t2")
        self.assertEqual(new_id, "T2")
```

- [ ] **Step 2: Run red**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_commands -v`
Expected: import errors / attribute errors for the new commands.

- [ ] **Step 3: Extend commands.py**

Append to `tools/tasktool/commands.py`. The appended block introduces `_resolve_id` and then redefines `cmd_create_task` to use it; the later definition shadows Task 8's version (this is intentional — Python keeps the last definition). Alternatively, delete the Task 8 `cmd_create_task` before appending if you prefer a single definition in the file.

```python
# ───── set / close / block / unblock ─────

def _resolve_id(p: Project, id: str) -> str:
    """Resolve a short ID to its fully-qualified form when unambiguous (spec §7 conventions).
    Phase and cross IDs need no resolution. Short S/T IDs are accepted only when exactly one
    matching item exists across the whole project."""
    parsed = parse_id(id)[0]
    if "." in id or parsed in ("phase", "cross"):
        return id
    if parsed == "slice":
        matches = [(ph.id, s.id) for ph in p.phases for s in ph.slices if s.id == id]
        if not matches:
            raise CommandError(f"slice {id} not found")
        if len(matches) > 1:
            qids = ", ".join(f"{ph}.{s}" for ph, s in matches)
            raise CommandError(f"ambiguous short id {id!r}; matches: {qids}. Use fully-qualified form.")
        return f"{matches[0][0]}.{matches[0][1]}"
    if parsed == "task":
        matches = [(ph.id, s.id, t.id) for ph in p.phases for s in ph.slices for t in s.tasks if t.id == id]
        if not matches:
            raise CommandError(f"task {id} not found")
        if len(matches) > 1:
            qids = ", ".join(f"{ph}.{s}.{t}" for ph, s, t in matches)
            raise CommandError(f"ambiguous short id {id!r}; matches: {qids}. Use fully-qualified form.")
        ph, s, t = matches[0]
        return f"{ph}.{s}.{t}"
    return id

def cmd_create_task(*, repo_root: Path, slice_id: str, title: str) -> str:
    """Now accepts unambiguous short slice IDs via _resolve_id. Replaces the
    fully-qualified-only version from Task 8."""
    p = _load(repo_root)
    qid = _resolve_id(p, slice_id)
    if parse_id(qid)[0] != "slice":
        raise CommandError(f"task creation requires a slice id, got {slice_id!r} ({parse_id(qid)[0]})")
    phase_part, slice_part, _ = split_qualified(qid)
    phase = next(ph for ph in p.phases if ph.id == phase_part)
    slc = next(s for s in phase.slices if s.id == slice_part)
    new_id = next_task_id(p, phase_part, slice_part)
    slc.tasks.append(Task(id=new_id, title=title, created=_today()))
    _save(repo_root, p)
    return new_id

def _find_item(p: Project, id: str):
    """Returns (container_list, item). Accepts fully-qualified or unambiguous short."""
    qid = _resolve_id(p, id)
    parsed = parse_id(qid)[0]
    if parsed == "phase":
        for ph in p.phases:
            if ph.id == qid:
                return p.phases, ph
        raise CommandError(f"phase {qid} not found")
    if parsed == "cross":
        for c in p.cross_cutting:
            if c.id == qid:
                return p.cross_cutting, c
        raise CommandError(f"cross-cutting {qid} not found")
    phase_part, slice_part, task_part = split_qualified(qid)
    phase = next((ph for ph in p.phases if ph.id == phase_part), None)
    if phase is None:
        raise CommandError(f"phase {phase_part} not found")
    if task_part is not None:
        slc = next((s for s in phase.slices if s.id == slice_part), None)
        if slc is None:
            raise CommandError(f"slice {phase_part}.{slice_part} not found")
        task = next((t for t in slc.tasks if t.id == task_part), None)
        if task is None:
            raise CommandError(f"task {qid} not found")
        return slc.tasks, task
    slc = next((s for s in phase.slices if s.id == slice_part), None)
    if slc is None:
        raise CommandError(f"slice {qid} not found")
    return phase.slices, slc

def _apply_review_gate(
    repo_root: Path, p: Project, item, id: str, kind_label: str,
    reviewer_chain: Path | None, skip_review_gate: bool,
) -> None:
    """Mutates item to record reviewer_chain or skip note."""
    if skip_review_gate:
        ts = _dt.datetime.now().isoformat(timespec="seconds")
        note = f"[{ts}] review gate skipped for {id}"
        item.notes = (item.notes + "\n" + note).strip() if item.notes else note
        return
    gate_kind = "post-slice" if kind_label == "slice" else "post-phase"
    try:
        result = check_gate(repo_root, id, gate_kind, explicit=reviewer_chain)
    except GateError as e:
        raise CommandError(f"review gate failed: {e}") from e
    rel = result.chain.relative_to(repo_root).as_posix()
    if kind_label == "slice":
        item.reviewer_chain = rel
    else:
        item.phase_reviewer_chain = rel

def cmd_set(
    *, repo_root: Path, id: str, status: str,
    reviewer_chain: Path | None = None, skip_review_gate: bool = False,
) -> None:
    p = _load(repo_root)
    _, item = _find_item(p, id)
    new_status = Status(status)
    kind = parse_id(id)[0]
    if new_status == Status.BLOCKED and kind != "slice":
        raise CommandError(f"only slices can be blocked; {id} is a {kind}")
    if new_status == Status.DONE and kind in ("slice", "phase"):
        _apply_review_gate(repo_root, p, item, id, kind, reviewer_chain, skip_review_gate)
    item.status = new_status
    if new_status == Status.DONE and item.closed is None:
        item.closed = _today()
    _save(repo_root, p)

def cmd_close(
    *, repo_root: Path, id: str,
    refs: list[str] | None = None, closed_date: str | None = None,
    note: str | None = None,
    reviewer_chain: Path | None = None, skip_review_gate: bool = False,
) -> None:
    p = _load(repo_root)
    _, item = _find_item(p, id)
    kind = parse_id(id)[0]
    if kind == "task" or kind == "cross":
        pass  # no gate; just close
    elif kind in ("slice", "phase"):
        _apply_review_gate(repo_root, p, item, id, kind, reviewer_chain, skip_review_gate)
    else:
        raise CommandError(f"cannot close {kind} {id}")
    item.status = Status.DONE
    item.closed = closed_date or _today()
    if refs:
        for r in refs:
            if r not in item.refs:
                item.refs.append(r)
    if note:
        item.notes = (item.notes + "\n" + note).strip() if item.notes else note
    _save(repo_root, p)

def cmd_block(*, repo_root: Path, slice_id: str, on: str) -> None:
    p = _load(repo_root)
    if not is_slice_id(slice_id):
        raise CommandError(f"block only works on slices; {slice_id} is a {kind_of(slice_id)}")
    _, item = _find_item(p, slice_id)
    if on.startswith("external:"):
        item.blocked_on = BlockedOn(kind="external", value=on[len("external:"):])
    else:
        parse_id(on)  # validate
        item.blocked_on = BlockedOn(kind="id", value=on)
    item.status = Status.BLOCKED
    _save(repo_root, p)

def cmd_unblock(*, repo_root: Path, slice_id: str, resume: bool = False) -> None:
    p = _load(repo_root)
    if not is_slice_id(slice_id):
        raise CommandError(f"unblock only works on slices; {slice_id} is a {kind_of(slice_id)}")
    _, item = _find_item(p, slice_id)
    item.blocked_on = None
    item.status = Status.IN_PROGRESS if resume else Status.READY
    _save(repo_root, p)
```

- [ ] **Step 4: Run green**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_commands -v`

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
git commit -m "P2.S1: set/close/block/unblock with review gate"
```

---

## Task 10: Commands — note + ref + title

**Files:**
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/tests/test_commands.py`

- [ ] **Step 1: Add failing tests**

Append to test file:

```python
class NoteRefTitleTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1")
    def tearDown(self):
        self.t.cleanup()

    def test_note_append(self):
        commands.cmd_note(repo_root=self.t.root, id="P1.S1", append="hello")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].notes, "hello")
        commands.cmd_note(repo_root=self.t.root, id="P1.S1", append="world")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].notes, "hello\nworld")

    def test_note_replace(self):
        commands.cmd_note(repo_root=self.t.root, id="P1.S1", append="hello")
        commands.cmd_note(repo_root=self.t.root, id="P1.S1", replace="fresh")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].notes, "fresh")

    def test_ref_add_remove(self):
        commands.cmd_ref(repo_root=self.t.root, id="P1.S1", add="docs/a.md")
        commands.cmd_ref(repo_root=self.t.root, id="P1.S1", add="docs/b.md")
        commands.cmd_ref(repo_root=self.t.root, id="P1.S1", remove="docs/a.md")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].refs, ["docs/b.md"])

    def test_title_set(self):
        commands.cmd_title(repo_root=self.t.root, id="P1.S1", new="renamed")
        p = load_project(self.t.root / "docs/tasklist.json")
        self.assertEqual(p.phases[0].slices[0].title, "renamed")
```

- [ ] **Step 2: Run red, then implement**

Append to `commands.py`:

```python
# ───── note / ref / title ─────

def cmd_note(
    *, repo_root: Path, id: str,
    append: str | None = None, replace: str | None = None,
) -> None:
    if (append is None) == (replace is None):
        raise CommandError("cmd_note requires exactly one of append/replace")
    p = _load(repo_root)
    _, item = _find_item(p, id)
    if append is not None:
        item.notes = (item.notes + "\n" + append).strip() if item.notes else append
    else:
        item.notes = replace or ""
    _save(repo_root, p)

def cmd_ref(
    *, repo_root: Path, id: str,
    add: str | None = None, remove: str | None = None,
) -> None:
    if (add is None) == (remove is None):
        raise CommandError("cmd_ref requires exactly one of add/remove")
    p = _load(repo_root)
    _, item = _find_item(p, id)
    if not hasattr(item, "refs"):
        raise CommandError(f"{id}: this item kind does not have refs")
    if add is not None and add not in item.refs:
        item.refs.append(add)
    elif remove is not None and remove in item.refs:
        item.refs.remove(remove)
    _save(repo_root, p)

def cmd_title(*, repo_root: Path, id: str, new: str) -> None:
    p = _load(repo_root)
    _, item = _find_item(p, id)
    item.title = new
    _save(repo_root, p)
```

- [ ] **Step 3: Run green**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_commands -v`

- [ ] **Step 4: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
git commit -m "P2.S1: note/ref/title commands"
```

---

## Task 11: Commands — show + list + next-id

**Files:**
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/tests/test_commands.py`

- [ ] **Step 1: Add failing tests**

Append:

```python
class ShowListTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1 title")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S1 title")
        commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="S2 title")
        commands.cmd_create_task(repo_root=self.t.root, slice_id="P1.S1", title="t1")
    def tearDown(self):
        self.t.cleanup()

    def test_show_phase(self):
        out = commands.cmd_show(repo_root=self.t.root, id="P1")
        self.assertIn("P1 title", out)
        self.assertIn("S1", out)
        self.assertIn("S2", out)

    def test_show_slice(self):
        out = commands.cmd_show(repo_root=self.t.root, id="P1.S1")
        self.assertIn("S1 title", out)
        self.assertIn("T1", out)

    def test_list_filter_status_open(self):
        out = commands.cmd_list(repo_root=self.t.root, open_only=True)
        self.assertIn("P1.S1", out)

    def test_list_format_json(self):
        out = commands.cmd_list(repo_root=self.t.root, format="json")
        import json as _j
        data = _j.loads(out)
        self.assertIsInstance(data, list)

class NextIdTests(unittest.TestCase):
    def test_next_phase_empty(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            self.assertEqual(
                commands.cmd_next_id(repo_root=t.root, kind="phase"), "P1",
            )
        finally:
            t.cleanup()
```

- [ ] **Step 2: Run red, then implement**

Append to `commands.py`:

```python
# ───── show / list / next-id ─────

def _item_one_line(prefix: str, item) -> str:
    status_tag = item.status.value
    return f"{prefix}  [{status_tag}]  {item.title}"

def cmd_show(*, repo_root: Path, id: str) -> str:
    p = _load(repo_root)
    _, item = _find_item(p, id)
    lines = [f"# {id} — {item.title}", f"status: {item.status.value}"]
    if getattr(item, "closed", None):
        lines.append(f"closed: {item.closed}")
    if getattr(item, "blocked_on", None):
        bo = item.blocked_on
        lines.append(f"blocked_on: {bo.kind}:{bo.value}")
    if getattr(item, "refs", None):
        lines.append("refs:")
        for r in item.refs:
            lines.append(f"  - {r}")
    if getattr(item, "notes", ""):
        lines.append(f"notes:\n{item.notes}")
    # children
    if hasattr(item, "slices"):
        lines.append("\nSlices:")
        for s in item.slices:
            lines.append(_item_one_line(f"  {s.id}", s))
    if hasattr(item, "tasks"):
        lines.append("\nTasks:")
        for t in item.tasks:
            lines.append(_item_one_line(f"  {t.id}", t))
    return "\n".join(lines) + "\n"

def _iter_items(p: Project):
    for ph in p.phases:
        yield ("phase", ph.id, ph)
        for s in ph.slices:
            yield ("slice", f"{ph.id}.{s.id}", s)
            for t in s.tasks:
                yield ("task", f"{ph.id}.{s.id}.{t.id}", t)
    for c in p.cross_cutting:
        yield ("cross", c.id, c)

def cmd_list(
    *, repo_root: Path,
    phase: str | None = None,
    status: list[str] | None = None,
    kind: str | None = None,
    open_only: bool = False,
    format: str = "text",
) -> str:
    p = _load(repo_root)
    if open_only:
        status_filter = {"ready", "in_progress", "blocked"}
    elif status:
        status_filter = set(status)
    else:
        status_filter = None
    rows: list[tuple[str, str, str, str]] = []
    for item_kind, qid, item in _iter_items(p):
        if phase and not qid.startswith(phase):
            continue
        if kind and item_kind != kind:
            continue
        if status_filter and item.status.value not in status_filter:
            continue
        rows.append((qid, item_kind, item.status.value, item.title))
    if format == "json":
        import json as _j
        return _j.dumps(
            [{"id": q, "kind": k, "status": s, "title": t} for q, k, s, t in rows],
            indent=2,
        )
    return "\n".join(f"{q}  [{s}]  {k:5}  {t}" for q, k, s, t in rows) + "\n"

def cmd_next_id(
    *, repo_root: Path, kind: str,
    phase: str | None = None, slice: str | None = None,
) -> str:
    p = _load(repo_root)
    if kind == "phase":
        return next_phase_id(p, repo_root)
    if kind == "slice":
        if not phase:
            raise CommandError("next-id slice requires --phase")
        return next_slice_id(p, phase, repo_root)
    if kind == "task":
        if not phase or not slice:
            raise CommandError("next-id task requires --phase and --slice")
        return next_task_id(p, phase, slice)
    if kind == "cross":
        return next_cross_id(p, repo_root)
    raise CommandError(f"unknown kind {kind}")
```

- [ ] **Step 3: Run green**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_commands -v`

- [ ] **Step 4: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
git commit -m "P2.S1: show/list/next-id commands"
```

---

## Task 12: Validate command + schema command

**Files:**
- Create: `tools/tasktool/schema_gen.py`
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/tests/test_commands.py`

- [ ] **Step 1: Add failing tests**

Append:

```python
class ValidateCmdTests(unittest.TestCase):
    def test_validate_clean(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            rc, out = commands.cmd_validate(repo_root=t.root)
            self.assertEqual(rc, 0)
        finally:
            t.cleanup()

    def test_validate_strict_format_detects_drift(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            path = t.root / "docs/tasklist.json"
            path.write_text(path.read_text().replace("  ", "    "), encoding="utf-8")
            rc, out = commands.cmd_validate(repo_root=t.root, strict_format=True)
            self.assertEqual(rc, 1)
        finally:
            t.cleanup()

    def test_validate_normalise_fixes(self):
        t = _Tmp()
        try:
            commands.cmd_init(repo_root=t.root, project="demo")
            path = t.root / "docs/tasklist.json"
            path.write_text(path.read_text().replace("  ", "    "), encoding="utf-8")
            rc, _ = commands.cmd_validate(repo_root=t.root, normalise=True)
            self.assertEqual(rc, 0)
            rc, _ = commands.cmd_validate(repo_root=t.root, strict_format=True)
            self.assertEqual(rc, 0)
        finally:
            t.cleanup()

class SchemaCmdTests(unittest.TestCase):
    def test_schema_emits_valid_json(self):
        out = commands.cmd_schema()
        import json as _j
        data = _j.loads(out)
        self.assertEqual(data["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertIn("properties", data)
        self.assertIn("phases", data["properties"])
```

- [ ] **Step 2: Implement schema_gen.py**

```python
# tools/tasktool/schema_gen.py
"""Generate a JSON Schema (draft 2020-12) describing tasklist.json."""
from __future__ import annotations
import json
from tasktool.model import SCHEMA_VERSION

def build_schema() -> dict:
    status_enum = ["ready", "in_progress", "blocked", "done"]
    date_str = {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"}
    nullable_date = {"oneOf": [date_str, {"type": "null"}]}
    blocked_on = {
        "oneOf": [
            {"type": "null"},
            {
                "type": "object",
                "required": ["kind", "value"],
                "properties": {
                    "kind": {"enum": ["id", "external"]},
                    "value": {"type": "string"},
                },
                "additionalProperties": False,
            },
        ],
    }
    task = {
        "type": "object",
        "required": ["id", "title", "created", "status"],
        "properties": {
            "id": {"type": "string", "pattern": r"^T\d+$"},
            "title": {"type": "string"},
            "created": date_str,
            "status": {"enum": status_enum},
            "closed": nullable_date,
            "refs": {"type": "array", "items": {"type": "string"}},
            "notes": {"type": "string"},
        },
        "additionalProperties": False,
    }
    slice_ = {
        "type": "object",
        "required": ["id", "title", "created", "status"],
        "properties": {
            "id": {"type": "string", "pattern": r"^S\d+[a-z]?$"},
            "title": {"type": "string"},
            "created": date_str,
            "status": {"enum": status_enum},
            "closed": nullable_date,
            "blocked_on": blocked_on,
            "plan_path": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "refs": {"type": "array", "items": {"type": "string"}},
            "notes": {"type": "string"},
            "reviewer_chain": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "tasks": {"type": "array", "items": task},
        },
        "additionalProperties": False,
    }
    phase = {
        "type": "object",
        "required": ["id", "title", "created", "status"],
        "properties": {
            "id": {"type": "string", "pattern": r"^P\d+$"},
            "title": {"type": "string"},
            "created": date_str,
            "status": {"enum": status_enum},
            "closed": nullable_date,
            "spec_path": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "plan_path": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "phase_reviewer_chain": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "notes": {"type": "string"},
            "slices": {"type": "array", "items": slice_},
        },
        "additionalProperties": False,
    }
    cross = {
        "type": "object",
        "required": ["id", "title", "created", "status"],
        "properties": {
            "id": {"type": "string", "pattern": r"^X\d+$"},
            "title": {"type": "string"},
            "created": date_str,
            "status": {"enum": status_enum},
            "closed": nullable_date,
            "refs": {"type": "array", "items": {"type": "string"}},
            "notes": {"type": "string"},
        },
        "additionalProperties": False,
    }
    archived = {
        "type": "object",
        "required": ["id", "title", "archived_path", "archived_date"],
        "properties": {
            "id": {"type": "string"},
            "title": {"type": "string"},
            "archived_path": {"type": "string"},
            "archived_date": date_str,
        },
        "additionalProperties": False,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "tasktool tasklist.json",
        "type": "object",
        "required": ["project", "schema_version"],
        "properties": {
            "schema_version": {"const": SCHEMA_VERSION},
            "project": {"type": "string"},
            "north_star": {"type": "string"},
            "last_reviewed": {"oneOf": [date_str, {"type": "null"}]},
            "phases": {"type": "array", "items": phase},
            "cross_cutting": {"type": "array", "items": cross},
            "archived_phases": {"type": "array", "items": archived},
        },
        "additionalProperties": False,
    }

def dump_schema() -> str:
    return json.dumps(build_schema(), indent=2, sort_keys=True) + "\n"
```

- [ ] **Step 3: Append commands**

Append to `commands.py`:

```python
# ───── validate / schema ─────

def cmd_validate(
    *, repo_root: Path,
    format: str = "text",
    strict_format: bool = False,
    normalise: bool = False,
) -> tuple[int, str]:
    from tasktool.validate import (
        validate_project, ValidationError, strict_format_check, normalise_file,
        find_path_warnings,
    )
    path = _tasklist_path(repo_root)
    if not path.exists():
        return 1, f"{path}: not found"
    errors: list[str] = []
    warnings: list[str] = []
    project: Project | None = None
    try:
        project = load_project(path)
        validate_project(project)
    except (ValidationError, ValueError) as e:
        errors.append(str(e))
    if project is not None and not errors:
        warnings.extend(find_path_warnings(project, repo_root))
    if normalise and not errors:
        try:
            normalise_file(path)
        except ValidationError as e:
            errors.append(str(e))
    if strict_format and not errors:
        try:
            strict_format_check(path)
        except ValidationError as e:
            errors.append(str(e))
    rc = 0 if not errors else 1
    if format == "json":
        import json as _j
        return rc, _j.dumps({"ok": rc == 0, "errors": errors, "warnings": warnings}, indent=2)
    parts: list[str] = []
    if warnings:
        parts.extend(f"warning: {w}" for w in warnings)
    if errors:
        parts.extend(errors)
    elif not warnings:
        parts.append("ok")
    return rc, "\n".join(parts) + "\n"

def cmd_schema() -> str:
    from tasktool.schema_gen import dump_schema
    return dump_schema()
```

- [ ] **Step 4: Run green**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_commands -v`

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/schema_gen.py tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
git commit -m "P2.S1: validate + schema commands"
```

---

## Task 13: CLI dispatcher (cli.py + __main__.py)

**Files:**
- Modify: `tools/tasktool/cli.py`
- Modify: `tools/tasktool/tests/test_cli_integration.py`

- [ ] **Step 1: Add failing tests**

Append to `test_cli_integration.py`:

```python
import tempfile, json
from pathlib import Path

class _CliTmp:
    def __init__(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        (self.root / "docs").mkdir()
    def cleanup(self):
        self._td.cleanup()

class CliEndToEndTests(unittest.TestCase):
    def test_init_then_create_then_show(self):
        t = _CliTmp()
        try:
            r = run_cli("init", "--project", "demo", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("create", "phase", "--title", "First", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("P1", r.stdout)
            r = run_cli("create", "slice", "P1", "--title", "Slice", cwd=t.root)
            self.assertIn("S1", r.stdout)
            r = run_cli("show", "P1", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("First", r.stdout)
            self.assertIn("S1", r.stdout)
        finally:
            t.cleanup()

    def test_validate_exits_zero_on_fresh_init(self):
        t = _CliTmp()
        try:
            run_cli("init", "--project", "demo", cwd=t.root)
            r = run_cli("validate", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            t.cleanup()

    def test_init_without_project_flag_works(self):
        """Spec acceptance path: `tasktool init && tasktool create phase ...` round-trips."""
        t = _CliTmp()
        try:
            r = run_cli("init", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("create", "phase", "--title", "First", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("show", "P1", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("First", r.stdout)
        finally:
            t.cleanup()

    def test_schema_is_valid_json(self):
        r = run_cli("schema")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertIn("properties", data)
```

- [ ] **Step 2: Run red, then rewrite cli.py**

Replace `tools/tasktool/cli.py`:

```python
# tools/tasktool/cli.py
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from tasktool import commands

def _find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / "docs").is_dir() or (p / ".git").exists():
            return p
    return cur

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tasktool")
    parser.add_argument("--project-root", type=Path, default=None,
                        help="Project root (default: walk up from cwd)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress non-error output. Accepted but minimally used in S1; reserved for richer logging in later slices.")
    parser.add_argument("--verbose", action="store_true",
                        help="Verbose output. Same caveat as --quiet for S1.")
    parser.add_argument("--no-stage", action="store_true",
                        help="Skip `git add` after mutating writes (default: best-effort stage).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--project", default=None,
                        help="project name (defaults to repo_root directory name)")
    p_init.add_argument("--north-star", default="")
    p_init.add_argument("--force", action="store_true")

    p_create = sub.add_parser("create")
    create_sub = p_create.add_subparsers(dest="create_kind", required=True)
    p_phase = create_sub.add_parser("phase")
    p_phase.add_argument("--title", required=True)
    p_phase.add_argument("--spec")
    p_phase.add_argument("--plan")
    p_slice = create_sub.add_parser("slice")
    p_slice.add_argument("phase_id")
    p_slice.add_argument("--title", required=True)
    p_slice.add_argument("--follow-up")
    p_slice.add_argument("--plan")
    p_task = create_sub.add_parser("task")
    p_task.add_argument("slice_id")
    p_task.add_argument("--title", required=True)
    p_cross = create_sub.add_parser("cross")
    p_cross.add_argument("--title", required=True)

    p_set = sub.add_parser("set")
    p_set.add_argument("id")
    p_set.add_argument("--status", required=True,
                       choices=["ready", "in_progress", "blocked", "done"])
    p_set.add_argument("--reviewer-chain", type=Path)
    p_set.add_argument("--skip-review-gate", action="store_true")

    p_close = sub.add_parser("close")
    p_close.add_argument("id")
    p_close.add_argument("--refs", default="")
    p_close.add_argument("--closed-date")
    p_close.add_argument("--note")
    p_close.add_argument("--reviewer-chain", type=Path)
    p_close.add_argument("--skip-review-gate", action="store_true")

    p_block = sub.add_parser("block")
    p_block.add_argument("slice_id")
    p_block.add_argument("--on", required=True)

    p_unblock = sub.add_parser("unblock")
    p_unblock.add_argument("slice_id")
    p_unblock.add_argument("--resume", action="store_true")

    p_note = sub.add_parser("note")
    p_note.add_argument("id")
    g = p_note.add_mutually_exclusive_group(required=True)
    g.add_argument("--append")
    g.add_argument("--replace")

    p_ref = sub.add_parser("ref")
    p_ref.add_argument("id")
    g = p_ref.add_mutually_exclusive_group(required=True)
    g.add_argument("--add")
    g.add_argument("--remove")

    p_title = sub.add_parser("title")
    p_title.add_argument("id")
    p_title.add_argument("--set", dest="new", required=True)

    p_show = sub.add_parser("show")
    p_show.add_argument("id")

    p_list = sub.add_parser("list")
    p_list.add_argument("--phase")
    p_list.add_argument("--status")
    p_list.add_argument("--kind", choices=["phase", "slice", "task", "cross"])
    p_list.add_argument("--open", dest="open_only", action="store_true")
    p_list.add_argument("--format", choices=["text", "json"], default="text")

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--format", choices=["text", "json"], default="text")
    p_validate.add_argument("--strict-format", action="store_true")
    p_validate.add_argument("--normalise", action="store_true")

    sub.add_parser("schema")

    p_nextid = sub.add_parser("next-id")
    p_nextid.add_argument("--kind", required=True, choices=["phase", "slice", "task", "cross"])
    p_nextid.add_argument("--phase")
    p_nextid.add_argument("--slice")
    return parser

def main(argv: list[str]) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    root = args.project_root or _find_repo_root(Path.cwd())
    # Plumb --no-stage into the commands module's process-global toggle.
    commands.STAGE_AFTER_WRITE = not args.no_stage

    try:
        if args.cmd == "init":
            commands.cmd_init(repo_root=root, project=args.project, north_star=args.north_star, force=args.force)
        elif args.cmd == "create":
            if args.create_kind == "phase":
                print(commands.cmd_create_phase(repo_root=root, title=args.title, spec=args.spec, plan=args.plan))
            elif args.create_kind == "slice":
                print(commands.cmd_create_slice(
                    repo_root=root, phase_id=args.phase_id, title=args.title,
                    follow_up=args.follow_up, plan=args.plan,
                ))
            elif args.create_kind == "task":
                print(commands.cmd_create_task(repo_root=root, slice_id=args.slice_id, title=args.title))
            elif args.create_kind == "cross":
                print(commands.cmd_create_cross(repo_root=root, title=args.title))
        elif args.cmd == "set":
            commands.cmd_set(
                repo_root=root, id=args.id, status=args.status,
                reviewer_chain=args.reviewer_chain, skip_review_gate=args.skip_review_gate,
            )
        elif args.cmd == "close":
            refs = [r for r in args.refs.split(",") if r] if args.refs else None
            commands.cmd_close(
                repo_root=root, id=args.id, refs=refs,
                closed_date=args.closed_date, note=args.note,
                reviewer_chain=args.reviewer_chain, skip_review_gate=args.skip_review_gate,
            )
        elif args.cmd == "block":
            commands.cmd_block(repo_root=root, slice_id=args.slice_id, on=args.on)
        elif args.cmd == "unblock":
            commands.cmd_unblock(repo_root=root, slice_id=args.slice_id, resume=args.resume)
        elif args.cmd == "note":
            commands.cmd_note(repo_root=root, id=args.id, append=args.append, replace=args.replace)
        elif args.cmd == "ref":
            commands.cmd_ref(repo_root=root, id=args.id, add=args.add, remove=args.remove)
        elif args.cmd == "title":
            commands.cmd_title(repo_root=root, id=args.id, new=args.new)
        elif args.cmd == "show":
            sys.stdout.write(commands.cmd_show(repo_root=root, id=args.id))
        elif args.cmd == "list":
            status_list = args.status.split(",") if args.status else None
            sys.stdout.write(commands.cmd_list(
                repo_root=root, phase=args.phase, status=status_list,
                kind=args.kind, open_only=args.open_only, format=args.format,
            ))
        elif args.cmd == "validate":
            rc, text = commands.cmd_validate(
                repo_root=root, format=args.format,
                strict_format=args.strict_format, normalise=args.normalise,
            )
            sys.stdout.write(text)
            return rc
        elif args.cmd == "schema":
            sys.stdout.write(commands.cmd_schema())
        elif args.cmd == "next-id":
            print(commands.cmd_next_id(
                repo_root=root, kind=args.kind, phase=args.phase, slice=args.slice,
            ))
        else:
            print(f"unknown command: {args.cmd}", file=sys.stderr)
            return 2
    except commands.CommandError as e:
        print(f"tasktool: {e}", file=sys.stderr)
        return 1
    return 0
```

- [ ] **Step 3: Run green**

Run: `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`
Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add tools/tasktool/cli.py tools/tasktool/tests/test_cli_integration.py
git commit -m "P2.S1: argparse CLI dispatcher"
```

---

## Task 14: Best-effort git-stage after mutations

The spec §7 conventions require mutating commands to `git add` the JSON after writing (best-effort; non-fatal if not a git repo). Add this as a single helper called from `_save`.

**Files:**
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/tests/test_commands.py`

- [ ] **Step 1: Add failing test**

Append to `test_commands.py`:

```python
import subprocess as _sp

class GitStageTests(unittest.TestCase):
    def test_writes_stage_file_when_in_git_repo(self):
        t = _Tmp()
        try:
            _sp.run(["git", "init", "-q"], cwd=t.root, check=True)
            _sp.run(["git", "config", "user.email", "t@t"], cwd=t.root, check=True)
            _sp.run(["git", "config", "user.name", "t"], cwd=t.root, check=True)
            commands.cmd_init(repo_root=t.root, project="demo")
            staged = _sp.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=t.root, capture_output=True, text=True, check=True,
            ).stdout
            self.assertIn("docs/tasklist.json", staged)
        finally:
            t.cleanup()

    def test_writes_silent_when_not_in_git_repo(self):
        t = _Tmp()
        try:
            # No git init. Should not raise.
            commands.cmd_init(repo_root=t.root, project="demo")
            self.assertTrue((t.root / "docs/tasklist.json").exists())
        finally:
            t.cleanup()

    def test_no_stage_skips_git_add(self):
        t = _Tmp()
        try:
            _sp.run(["git", "init", "-q"], cwd=t.root, check=True)
            _sp.run(["git", "config", "user.email", "t@t"], cwd=t.root, check=True)
            _sp.run(["git", "config", "user.name", "t"], cwd=t.root, check=True)
            commands.STAGE_AFTER_WRITE = False
            try:
                commands.cmd_init(repo_root=t.root, project="demo")
            finally:
                commands.STAGE_AFTER_WRITE = True
            staged = _sp.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=t.root, capture_output=True, text=True, check=True,
            ).stdout
            self.assertNotIn("docs/tasklist.json", staged)
        finally:
            t.cleanup()
```

- [ ] **Step 2: Implement the helper**

Modify `_save` in `commands.py`:

```python
import subprocess as _subprocess

# Process-global toggle for `--no-stage`. Set by cli.main() before dispatch.
STAGE_AFTER_WRITE: bool = True

def _git_stage(repo_root: Path, path: Path) -> None:
    """Best-effort `git add`. Silent on any failure (not a git repo, git missing, etc.).
    Skipped entirely when STAGE_AFTER_WRITE is False (e.g. --no-stage)."""
    if not STAGE_AFTER_WRITE:
        return
    try:
        _subprocess.run(
            ["git", "add", "--", str(path.relative_to(repo_root))],
            cwd=repo_root, check=False,
            stdout=_subprocess.DEVNULL, stderr=_subprocess.DEVNULL,
        )
    except (OSError, ValueError):
        pass

def _save(repo_root: Path, p: Project) -> None:
    validate_project(p)
    path = _tasklist_path(repo_root)
    save_project(p, path)
    _git_stage(repo_root, path)
```

- [ ] **Step 3: Run green**

Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_commands -v`

- [ ] **Step 4: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
git commit -m "P2.S1: best-effort git-stage after mutations"
```

---

## Task 15: Installer script

**Files:**
- Create: `tools/tasktool/install.sh`

- [ ] **Step 1: Write installer**

```bash
#!/usr/bin/env bash
# tools/tasktool/install.sh — install/update the ~/.local/bin/tasktool shim.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"   # → tools/
TARGET="${HOME}/.local/bin/tasktool"
FORCE="${1:-}"

EXPECTED_SHIM="#!/usr/bin/env bash
# tasktool shim — generated by tasktool/install.sh
exec python3 -m tasktool \"\$@\""

mkdir -p "$(dirname "$TARGET")"

if [[ -f "$TARGET" ]] && [[ "$FORCE" != "--force" ]]; then
  current="$(cat "$TARGET")"
  if [[ "$current" == "$EXPECTED_SHIM" ]] || grep -q "tasktool shim" "$TARGET" 2>/dev/null; then
    echo "tasktool shim already installed (matches). Updating PYTHONPATH note..."
  else
    echo "ERROR: $TARGET exists and is not a tasktool shim. Re-run with --force to overwrite." >&2
    exit 1
  fi
fi

cat > "$TARGET" <<EOF
#!/usr/bin/env bash
# tasktool shim — generated by tasktool/install.sh
export PYTHONPATH="${PKG_ROOT}\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 -m tasktool "\$@"
EOF
chmod +x "$TARGET"

echo "Installed $TARGET"
echo "Pointing at $PKG_ROOT/tasktool"
"$TARGET" --help >/dev/null
echo "Self-test passed."
```

- [ ] **Step 2: Make executable and dry-run sanity check**

```bash
chmod +x tools/tasktool/install.sh
# Show what it would install without running:
bash -n tools/tasktool/install.sh
echo "syntax ok"
```

- [ ] **Step 3: Commit (do NOT actually run the installer here — that's an end-of-slice step)**

```bash
git add tools/tasktool/install.sh
git commit -m "P2.S1: installer script for ~/.local/bin/tasktool shim"
```

---

## Task 16: End-to-end smoke test against this repo's actual TASKLIST workflow

**Files:**
- Modify: `tools/tasktool/tests/test_cli_integration.py`

- [ ] **Step 1: Add a end-to-end test that exercises the review gate**

Append:

```python
class ReviewGateE2ETests(unittest.TestCase):
    def test_close_slice_requires_chain(self):
        t = _CliTmp()
        try:
            run_cli("init", "--project", "demo", cwd=t.root)
            run_cli("create", "phase", "--title", "P", cwd=t.root)
            run_cli("create", "slice", "P1", "--title", "S", cwd=t.root)
            r = run_cli("close", "P1.S1", cwd=t.root)
            self.assertEqual(r.returncode, 1)
            self.assertIn("review gate", r.stderr.lower())
        finally:
            t.cleanup()

    def test_close_slice_with_passing_chain(self):
        t = _CliTmp()
        try:
            run_cli("init", "--project", "demo", cwd=t.root)
            run_cli("create", "phase", "--title", "P", cwd=t.root)
            run_cli("create", "slice", "P1", "--title", "S", cwd=t.root)
            chain = t.root / "docs/reviewer/p1-s1-post-slice"
            chain.mkdir(parents=True)
            (chain / "chain.json").write_text(
                '{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}',
                encoding="utf-8",
            )
            r = run_cli("close", "P1.S1", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            t.cleanup()

    def test_skip_review_gate(self):
        t = _CliTmp()
        try:
            run_cli("init", "--project", "demo", cwd=t.root)
            run_cli("create", "phase", "--title", "P", cwd=t.root)
            run_cli("create", "slice", "P1", "--title", "S", cwd=t.root)
            r = run_cli("close", "P1.S1", "--skip-review-gate", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            t.cleanup()
```

- [ ] **Step 2: Run full test suite**

Run: `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`
Expected: every test (across all modules) passes.

- [ ] **Step 3: Commit**

```bash
git add tools/tasktool/tests/test_cli_integration.py
git commit -m "P2.S1: end-to-end review-gate integration tests"
```

---

## Task 17: Self-check / polish before slice close

**Files:** read-only inspection across the slice

- [ ] **Step 1: Run the full suite one more time**

Run: `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`
Expected: all green; note the count of tests passing in the post-impl notes you'll add when closing.

- [ ] **Step 2: Test the installed shim end-to-end (optional but recommended)**

```bash
bash tools/tasktool/install.sh
tasktool --help
tasktool schema | python3 -m json.tool > /dev/null && echo "schema ok"
```

- [ ] **Step 3: Verify the spec ↔ code surface match**

Spot-check by listing CLI subcommands and reconciling against §7 of the spec:

```bash
python3 -m tasktool 2>&1 | head -5   # argparse usage line
# Expected subcommands: init, import (deferred to S2), create, set, close, block,
# unblock, note, ref, title, show, brief (deferred to S2), list, render (deferred),
# validate, schema, next-id, archive-phase (deferred to S2).
```

Items deferred to S2: `import`, `brief`, `render`, `archive-phase`. Make a note that they're intentionally absent in S1's slice-close write-up.

- [ ] **Step 4: Stop here — do not flip the TASKLIST slice yet**

The slice-close itself is performed by the coordinator after `external-review --kind post-slice` returns `ready` / `ready with small edits`. Do not edit `docs/TASKLIST.md` from within the slice work; that's the coordinator's job at slice close.

---

## Out of scope (intentionally deferred to S2 / S3)

- `tasktool import` (TASKLIST.md → JSON parser) — S2
- `tasktool render` (JSON → markdown view) — S2
- `tasktool brief` (start-of-work primer) — S2
- `tasktool archive-phase` — S2 (depends on import-validated workflow)
- Pre-commit hook template — S3
- `tasklist-discipline` skill rewrite — S3
- Sibling skill touch-ups — S3
- Actually migrating `docs/TASKLIST.md` to `docs/tasklist.json` in this repo — S2

These are explicitly out-of-scope here. If you find yourself reaching for them, stop — they belong in their own slice.
