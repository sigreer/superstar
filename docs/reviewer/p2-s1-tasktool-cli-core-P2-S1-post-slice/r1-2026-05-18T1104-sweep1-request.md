<!-- superstar-prompt:start -->
You are acting as an independent senior engineering reviewer.

Review stance:
- Lead with findings, ordered by severity.
- Focus on correctness, consistency, implementation risk, missing acceptance
  gates, vague handoffs, ungrounded assumptions, unverified claims, and drift
  from the codebase.
- Give exact file/line references when possible.
- If the document is sound, say that clearly and list residual risks.
- Keep the review actionable. Avoid broad rewrites unless the current structure
  creates concrete risk.

Repository root:
/home/simon/Dev/sigreer/skills/superstar

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md

Additional context files:
- docs/specs/2026-05-17-P2-tasktool-design.md
- docs/TASKLIST.md

Review output contract:
1. Findings
   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
     stable if this review is iterated in subsequent rounds.
   - Mark severity inline: `Severity: blocking | important | minor | nit`.
2. Open questions / assumptions
3. Suggested document edits
4. Verification gaps / commands that should be run, if any
5. Overall verdict: one of "ready", "ready with small edits", or "revise"

Read the files from disk. Do not rely only on the snippets in this prompt.


## Target Preview

### docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md

    1	# P2.S1 — tasktool CLI core Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Build the Python stdlib CLI core for `tasktool` — data model, canonical serializer, validation, ID allocation, reviewer-gate, and the mutation/read commands. End state: `tasktool init && tasktool create phase --title "..." && tasktool show P1` round-trips cleanly, `tasktool validate --strict-format` blocks non-canonical commits.
    6	
    7	**Architecture:** Single Python package `tools/tasktool/` (stdlib only). Layered: `ids` / `model` / `serialize` / `validate` / `allocate` / `reviewer_gate` are pure, side-effect-free modules; `commands` orchestrates them and is the only layer that touches disk-as-side-effect; `cli` is argparse glue. Tests under `tools/tasktool/tests/` use `unittest` with tmpdir fixtures.
    8	
    9	**Tech Stack:** Python 3.11+ (dataclasses, pathlib, json, argparse, datetime, re, subprocess, hashlib, unittest). Zero third-party dependencies.
   10	
   11	---
   12	
   13	## File structure
   14	
   15	Created in this slice:
   16	
   17	```
   18	tools/tasktool/
   19	├── __init__.py            # public API surface: load_project, save_project, brief, etc.
   20	├── __main__.py            # `python -m tasktool` entry; defers to cli.main()
   21	├── cli.py                 # argparse definition + dispatcher
   22	├── ids.py                 # ID regex, parse, fully-qualify, kind detection
   23	├── model.py               # dataclasses: Project, Phase, Slice, Task, CrossCutting, BlockedOn
   24	├── serialize.py           # canonical JSON load/save (sort_keys=True, indent=2, trailing \n)
   25	├── validate.py            # validation rules + strict-format + normalise
   26	├── allocate.py            # orphan-aware next-ID across TASKLIST/specs/plans/reviewer
   27	├── reviewer_gate.py       # chain folder discovery + chain.json verdict check
   28	├── commands.py            # one function per subcommand; called by cli.dispatch
   29	├── schema_gen.py          # generate JSON Schema from dataclasses
   30	├── install.sh             # idempotent installer for ~/.local/bin/tasktool shim
   31	└── tests/
   32	    ├── __init__.py
   33	    ├── test_ids.py
   34	    ├── test_model.py
   35	    ├── test_serialize.py
   36	    ├── test_validate.py
   37	    ├── test_allocate.py
   38	    ├── test_reviewer_gate.py
   39	    ├── test_commands.py
   40	    └── test_cli_integration.py
   41	```
   42	
   43	Not touched in this slice: `tools/tasktool/templates/pre-commit-tasktool` (S3), `importer.py` / `render.py` / `brief.py` (S2), any sibling skills (S3).
   44	
   45	---
   46	
   47	## Conventions used throughout
   48	
   49	- **TDD:** every task writes the failing test, runs it red, implements the minimum, runs it green, commits. Commits per task, not per step.
   50	- **Commit message prefix:** `P2.S1:` followed by an imperative one-liner.
   51	- **Run tests via:** `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`. The `tools/` directory must be on `PYTHONPATH` because the package lives at `tools/tasktool/`. Once the installer (Task 15) has been run, the shim sets `PYTHONPATH` automatically — but the raw command shown in every test gate is what an agent will run before installing.
   52	- **No third-party deps.** If you reach for `pytest`, `pydantic`, `click`, stop — stdlib only.
   53	- **Python style:** dataclasses with `slots=True`; `from __future__ import annotations` everywhere; type hints required on public functions.
   54	
   55	---
   56	
   57	## Task 1: Project skeleton + smoke test
   58	
   59	**Files:**
   60	- Create: `tools/tasktool/__init__.py`
   61	- Create: `tools/tasktool/__main__.py`
   62	- Create: `tools/tasktool/cli.py`
   63	- Create: `tools/tasktool/tests/__init__.py`
   64	- Create: `tools/tasktool/tests/test_cli_integration.py`
   65	
   66	- [ ] **Step 1: Create empty package skeleton**
   67	
   68	```python
   69	# tools/tasktool/__init__.py
   70	"""tasktool — JSON-backed task management CLI."""
   71	__version__ = "0.1.0"
   72	```
   73	
   74	```python
   75	# tools/tasktool/__main__.py
   76	from tasktool.cli import main
   77	import sys
   78	if __name__ == "__main__":
   79	    sys.exit(main(sys.argv[1:]))
   80	```
   81	
   82	```python
   83	# tools/tasktool/cli.py
   84	from __future__ import annotations
   85	
   86	def main(argv: list[str]) -> int:
   87	    if not argv or argv[0] in ("-h", "--help"):
   88	        print("tasktool — see docs/specs/2026-05-17-P2-tasktool-design.md")
   89	        return 0
   90	    print(f"tasktool: unknown command: {argv[0]}", flush=True)
   91	    return 2
   92	```
   93	
   94	```python
   95	# tools/tasktool/tests/__init__.py
   96	```
   97	
   98	- [ ] **Step 2: Write the smoke test**
   99	
  100	```python
  101	# tools/tasktool/tests/test_cli_integration.py
  102	from __future__ import annotations
  103	import subprocess
  104	import sys
  105	import unittest
  106	from pathlib import Path
  107	
  108	REPO_ROOT = Path(__file__).resolve().parents[3]
  109	PKG_DIR = REPO_ROOT / "tools"
  110	
  111	def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
  112	    import os
  113	    env = os.environ.copy()
  114	    env["PYTHONPATH"] = str(PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")
  115	    return subprocess.run(
  116	        [sys.executable, "-m", "tasktool", *args],
  117	        capture_output=True, text=True, cwd=cwd or REPO_ROOT, env=env,
  118	    )
  119	
  120	class SmokeTests(unittest.TestCase):
  121	    def test_help_prints_and_exits_zero(self):
  122	        result = run_cli("--help")
  123	        self.assertEqual(result.returncode, 0)
  124	        self.assertIn("tasktool", result.stdout)
  125	
  126	    def test_unknown_command_exits_two(self):
  127	        result = run_cli("nope")
  128	        self.assertEqual(result.returncode, 2)
  129	```
  130	
  131	- [ ] **Step 3: Run tests**
  132	
  133	Run: `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`
  134	Expected: 2 tests pass.
  135	
  136	- [ ] **Step 4: Commit**
  137	
  138	```bash
  139	git add tools/tasktool/
  140	git commit -m "P2.S1: scaffold tasktool package and smoke test"
  141	```
  142	
  143	---
  144	
  145	## Task 2: ID parsing module (ids.py)
  146	
  147	**Files:**
  148	- Create: `tools/tasktool/ids.py`
  149	- Create: `tools/tasktool/tests/test_ids.py`
  150	
  151	- [ ] **Step 1: Write failing tests**
  152	
  153	```python
  154	# tools/tasktool/tests/test_ids.py
  155	from __future__ import annotations
  156	import unittest
  157	from tasktool.ids import (
  158	    IdParseError, parse_id, fully_qualify, kind_of, is_slice_id, split_qualified,
  159	)
  160	
  161	class ParseIdTests(unittest.TestCase):
  162	    def test_phase(self):
  163	        self.assertEqual(parse_id("P2"), ("phase", "P2"))
  164	    def test_slice(self):
  165	        self.assertEqual(parse_id("S3"), ("slice", "S3"))
  166	    def test_slice_letter_suffix(self):
  167	        self.assertEqual(parse_id("S5a"), ("slice", "S5a"))
  168	    def test_task(self):
  169	        self.assertEqual(parse_id("T1"), ("task", "T1"))
  170	    def test_cross(self):
  171	        self.assertEqual(parse_id("X4"), ("cross", "X4"))
  172	    def test_qualified_phase_slice(self):
  173	        self.assertEqual(parse_id("P2.S3"), ("slice", "P2.S3"))
  174	    def test_qualified_phase_slice_task(self):
  175	        self.assertEqual(parse_id("P2.S3.T1"), ("task", "P2.S3.T1"))
  176	    def test_rejects_lowercase_phase(self):
  177	        with self.assertRaises(IdParseError):
  178	            parse_id("p2")
  179	    def test_rejects_empty(self):
  180	        with self.assertRaises(IdParseError):
  181	            parse_id("")
  182	    def test_rejects_garbage(self):
  183	        with self.assertRaises(IdParseError):
  184	            parse_id("P2..S1")
  185	
  186	class KindTests(unittest.TestCase):
  187	    def test_kind_of_short(self):
  188	        self.assertEqual(kind_of("P2"), "phase")
  189	        self.assertEqual(kind_of("S3a"), "slice")
  190	        self.assertEqual(kind_of("T1"), "task")
  191	        self.assertEqual(kind_of("X4"), "cross")
  192	    def test_kind_of_qualified(self):
  193	        self.assertEqual(kind_of("P2.S3.T1"), "task")
  194	    def test_is_slice_id(self):
  195	        self.assertTrue(is_slice_id("S3"))
  196	        self.assertTrue(is_slice_id("P2.S3a"))
  197	        self.assertFalse(is_slice_id("T1"))
  198	        self.assertFalse(is_slice_id("P2"))
  199	
  200	class QualifyTests(unittest.TestCase):
  201	    def test_qualify_slice_under_phase(self):
  202	        self.assertEqual(fully_qualify("S3", phase="P2"), "P2.S3")
  203	    def test_qualify_task_under_slice(self):
  204	        self.assertEqual(fully_qualify("T1", phase="P2", slice="S3"), "P2.S3.T1")
  205	    def test_qualify_already_qualified(self):
  206	        self.assertEqual(fully_qualify("P2.S3", phase="P9"), "P2.S3")
  207	
  208	class SplitTests(unittest.TestCase):
  209	    def test_split_task(self):
  210	        self.assertEqual(split_qualified("P2.S3.T1"), ("P2", "S3", "T1"))
  211	    def test_split_slice(self):
  212	        self.assertEqual(split_qualified("P2.S3"), ("P2", "S3", None))
  213	    def test_split_phase(self):
  214	        self.assertEqual(split_qualified("P2"), ("P2", None, None))
  215	    def test_split_short_phase(self):
  216	        self.assertEqual(split_qualified("S3"), (None, "S3", None))
  217	```
  218	
  219	- [ ] **Step 2: Run tests, verify all fail**
  220	
  221	Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_ids -v`
  222	Expected: ImportError or all-red.
  223	
  224	- [ ] **Step 3: Implement ids.py**
  225	
  226	```python
  227	# tools/tasktool/ids.py
  228	from __future__ import annotations
  229	import re
  230	from typing import Literal
  231	
  232	Kind = Literal["phase", "slice", "task", "cross"]
  233	
  234	class IdParseError(ValueError):
  235	    pass
  236	
  237	_PHASE = r"P\d+"
  238	_SLICE = r"S\d+[a-z]?"
  239	_TASK = r"T\d+"
  240	_CROSS = r"X\d+"
  241	
  242	_SHORT_RE = re.compile(rf"^({_PHASE}|{_SLICE}|{_TASK}|{_CROSS})$")
  243	_QUALIFIED_RE = re.compile(
  244	    rf"^({_PHASE})(?:\.({_SLICE}))?(?:\.({_TASK}))?$"
  245	)
  246	
  247	def parse_id(value: str) -> tuple[Kind, str]:
  248	    """Return (kind, normalised-id). Accepts short or qualified form."""
  249	    if not value:
  250	        raise IdParseError("empty id")
  251	    if "." in value:
  252	        m = _QUALIFIED_RE.match(value)
  253	        if not m:
  254	            raise IdParseError(f"malformed qualified id: {value!r}")
  255	        phase, slice_, task = m.groups()
  256	        if task:
  257	            return ("task", value)
  258	        if slice_:
  259	            return ("slice", value)
  260	        return ("phase", phase)
  261	    m = _SHORT_RE.match(value)
  262	    if not m:
  263	        raise IdParseError(f"malformed id: {value!r}")
  264	    head = value[0]
  265	    return ({"P": "phase", "S": "slice", "T": "task", "X": "cross"}[head], value)
  266	
  267	def kind_of(value: str) -> Kind:
  268	    return parse_id(value)[0]
  269	
  270	def is_slice_id(value: str) -> bool:
  271	    return kind_of(value) == "slice"
  272	
  273	def fully_qualify(value: str, *, phase: str | None = None, slice: str | None = None) -> str:
  274	    parse_id(value)  # validate
  275	    if "." in value:
  276	        return value
  277	    head = value[0]
  278	    if head == "P" or head == "X":
  279	        return value
  280	    if head == "S":
  281	        if not phase:
  282	            raise IdParseError(f"cannot qualify slice {value!r} without phase context")
  283	        return f"{phase}.{value}"
  284	    if head == "T":
  285	        if not phase or not slice:
  286	            raise IdParseError(f"cannot qualify task {value!r} without phase+slice context")
  287	        return f"{phase}.{slice}.{value}"
  288	    raise IdParseError(f"unreachable: {value!r}")
  289	
  290	def split_qualified(value: str) -> tuple[str | None, str | None, str | None]:
  291	    """Return (phase, slice, task) components; None for missing levels."""
  292	    parse_id(value)
  293	    if "." not in value:
  294	        head = value[0]
  295	        if head == "P":
  296	            return (value, None, None)
  297	        if head == "S":
  298	            return (None, value, None)
  299	        if head == "T":
  300	            return (None, None, value)
  301	        return (None, None, None)  # cross
  302	    m = _QUALIFIED_RE.match(value)
  303	    assert m
  304	    return tuple(m.groups())  # type: ignore[return-value]
  305	```
  306	
  307	- [ ] **Step 4: Run tests, verify green**
  308	
  309	Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_ids -v`
  310	Expected: all 17 tests pass.
  311	
  312	- [ ] **Step 5: Commit**
  313	
  314	```bash
  315	git add tools/tasktool/ids.py tools/tasktool/tests/test_ids.py
  316	git commit -m "P2.S1: ID parsing and qualification"
  317	```
  318	
  319	---
  320	
  321	## Task 3: Data model (model.py)
  322	
  323	**Files:**
  324	- Create: `tools/tasktool/model.py`
  325	- Create: `tools/tasktool/tests/test_model.py`
  326	
  327	- [ ] **Step 1: Write failing tests**
  328	
  329	```python
  330	# tools/tasktool/tests/test_model.py
  331	from __future__ import annotations
  332	import unittest
  333	from tasktool.model import (
  334	    Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status, SCHEMA_VERSION,
  335	)
  336	
  337	class StatusTests(unittest.TestCase):
  338	    def test_status_values(self):
  339	        self.assertEqual(
  340	            {s.value for s in Status},
  341	            {"ready", "in_progress", "blocked", "done"},
  342	        )
  343	
  344	class ConstructionTests(unittest.TestCase):
  345	    def test_empty_project(self):
  346	        p = Project(project="superstar")
  347	        self.assertEqual(p.schema_version, SCHEMA_VERSION)
  348	        self.assertEqual(p.phases, [])
  349	        self.assertEqual(p.cross_cutting, [])
  350	        self.assertEqual(p.archived_phases, [])
  351	
  352	    def test_phase_defaults(self):
  353	        ph = Phase(id="P2", title="tasktool", created="2026-05-17")
  354	        self.assertEqual(ph.status, Status.READY)
  355	        self.assertIsNone(ph.closed)
  356	        self.assertIsNone(ph.spec_path)
  357	        self.assertIsNone(ph.plan_path)
  358	        self.assertIsNone(ph.phase_reviewer_chain)
  359	        self.assertEqual(ph.notes, "")
  360	        self.assertEqual(ph.slices, [])
  361	
  362	    def test_slice_defaults(self):
  363	        s = Slice(id="S1", title="CLI core", created="2026-05-17")
  364	        self.assertEqual(s.status, Status.READY)
  365	        self.assertIsNone(s.blocked_on)
  366	        self.assertIsNone(s.reviewer_chain)
  367	        self.assertEqual(s.refs, [])
  368	        self.assertEqual(s.tasks, [])
  369	
  370	    def test_task_defaults(self):
  371	        t = Task(id="T1", title="x", created="2026-05-17")
  372	        self.assertEqual(t.status, Status.READY)
  373	        self.assertIsNone(t.closed)
  374	        self.assertEqual(t.refs, [])
  375	
  376	    def test_cross_defaults(self):
  377	        x = CrossCutting(id="X1", title="x", created="2026-05-17")
  378	        self.assertEqual(x.status, Status.READY)
  379	
  380	    def test_blocked_on_id(self):
  381	        b = BlockedOn(kind="id", value="P2.S1")
  382	        self.assertEqual(b.kind, "id")
  383	    def test_blocked_on_external(self):
  384	        b = BlockedOn(kind="external", value="vendor X")
  385	        self.assertEqual(b.value, "vendor X")
  386	```
  387	
  388	- [ ] **Step 2: Run, verify red**
  389	
  390	Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_model -v`
  391	
  392	- [ ] **Step 3: Implement model.py**
  393	
  394	```python
  395	# tools/tasktool/model.py
  396	from __future__ import annotations
  397	from dataclasses import dataclass, field
  398	from enum import Enum
  399	from typing import Literal
  400	
  401	SCHEMA_VERSION = 1
  402	
  403	class Status(str, Enum):
  404	    READY = "ready"
  405	    IN_PROGRESS = "in_progress"
  406	    BLOCKED = "blocked"
  407	    DONE = "done"
  408	
  409	@dataclass(slots=True)
  410	class BlockedOn:
  411	    kind: Literal["id", "external"]
  412	    value: str
  413	
  414	@dataclass(slots=True)
  415	class Task:
  416	    id: str
  417	    title: str
  418	    created: str
  419	    status: Status = Status.READY
  420	    closed: str | None = None
  421	    refs: list[str] = field(default_factory=list)
  422	    notes: str = ""
  423	
  424	@dataclass(slots=True)
  425	class Slice:
  426	    id: str
  427	    title: str
  428	    created: str
  429	    status: Status = Status.READY
  430	    closed: str | None = None
  431	    blocked_on: BlockedOn | None = None
  432	    plan_path: str | None = None
  433	    refs: list[str] = field(default_factory=list)
  434	    notes: str = ""
  435	    reviewer_chain: str | None = None
  436	    tasks: list[Task] = field(default_factory=list)
  437	
  438	@dataclass(slots=True)
  439	class Phase:
  440	    id: str
  441	    title: str
  442	    created: str
  443	    status: Status = Status.READY
  444	    closed: str | None = None
  445	    spec_path: str | None = None
  446	    plan_path: str | None = None
  447	    phase_reviewer_chain: str | None = None
  448	    notes: str = ""
  449	    slices: list[Slice] = field(default_factory=list)
  450	
  451	@dataclass(slots=True)
  452	class CrossCutting:
  453	    id: str
  454	    title: str
  455	    created: str
  456	    status: Status = Status.READY
  457	    closed: str | None = None
  458	    refs: list[str] = field(default_factory=list)
  459	    notes: str = ""
  460	
  461	@dataclass(slots=True)
  462	class ArchivedPhase:
  463	    id: str
  464	    title: str
  465	    archived_path: str
  466	    archived_date: str
  467	
  468	@dataclass(slots=True)
  469	class Project:
  470	    project: str
  471	    schema_version: int = SCHEMA_VERSION
  472	    north_star: str = ""
  473	    last_reviewed: str | None = None
  474	    phases: list[Phase] = field(default_factory=list)
  475	    cross_cutting: list[CrossCutting] = field(default_factory=list)
  476	    archived_phases: list[ArchivedPhase] = field(default_factory=list)
  477	```
  478	
  479	- [ ] **Step 4: Run tests green**
  480	
  481	Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_model -v`
  482	Expected: 8 tests pass.
  483	
  484	- [ ] **Step 5: Commit**
  485	
  486	```bash
  487	git add tools/tasktool/model.py tools/tasktool/tests/test_model.py
  488	git commit -m "P2.S1: data model dataclasses"
  489	```
  490	
  491	---
  492	
  493	## Task 4: Canonical serializer (serialize.py)
  494	
  495	**Files:**
  496	- Create: `tools/tasktool/serialize.py`
  497	- Create: `tools/tasktool/tests/test_serialize.py`
  498	
  499	- [ ] **Step 1: Write failing tests**
  500	
  501	```python
  502	# tools/tasktool/tests/test_serialize.py
  503	from __future__ import annotations
  504	import json
  505	import tempfile
  506	import unittest
  507	from pathlib import Path
  508	from tasktool.model import Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status
  509	from tasktool.serialize import (
  510	    load_project, save_project, dumps_canonical, loads_project, to_dict, from_dict,
  511	)
  512	
  513	class RoundTripTests(unittest.TestCase):
  514	    def test_empty_project_roundtrip(self):
  515	        p = Project(project="demo")
  516	        d = to_dict(p)
  517	        back = from_dict(d)
  518	        self.assertEqual(back, p)
  519	
  520	    def test_full_project_roundtrip(self):
  521	        p = Project(project="demo", north_star="x", last_reviewed="2026-05-17")
  522	        ph = Phase(id="P1", title="phase", created="2026-05-17", status=Status.IN_PROGRESS)
  523	        s = Slice(
  524	            id="S1", title="slice", created="2026-05-17", status=Status.BLOCKED,
  525	            blocked_on=BlockedOn(kind="id", value="P1.S2"),
  526	            refs=["a.md", "b.md"],
  527	        )
  528	        s.tasks.append(Task(id="T1", title="task", created="2026-05-17"))
  529	        ph.slices.append(s)
  530	        p.phases.append(ph)
  531	        p.cross_cutting.append(CrossCutting(id="X1", title="x", created="2026-05-17"))
  532	
  533	        back = from_dict(to_dict(p))
  534	        self.assertEqual(back, p)
  535	
  536	class CanonicalFormatTests(unittest.TestCase):
  537	    def test_dumps_sorted_keys(self):
  538	        p = Project(project="demo")
  539	        out = dumps_canonical(p)
  540	        parsed = json.loads(out)
  541	        self.assertEqual(parsed["project"], "demo")
  542	        # sort_keys → "phases" before "project" before "schema_version"
  543	        keys = list(parsed.keys())
  544	        self.assertEqual(keys, sorted(keys))
  545	
  546	    def test_dumps_trailing_newline(self):
  547	        out = dumps_canonical(Project(project="demo"))
  548	        self.assertTrue(out.endswith("\n"))
  549	
  550	    def test_dumps_indent_two(self):
  551	        out = dumps_canonical(Project(project="demo"))
  552	        self.assertIn("\n  ", out)
  553	
  554	class DiskIOTests(unittest.TestCase):
  555	    def test_save_then_load(self):
  556	        with tempfile.TemporaryDirectory() as td:
  557	            path = Path(td) / "tasklist.json"
  558	            p = Project(project="demo")
  559	            save_project(p, path)
  560	            loaded = load_project(path)
  561	            self.assertEqual(loaded, p)
  562	
  563	    def test_save_is_canonical_bytes(self):
  564	        with tempfile.TemporaryDirectory() as td:
  565	            path = Path(td) / "tasklist.json"
  566	            p = Project(project="demo")
  567	            save_project(p, path)
  568	            on_disk = path.read_text(encoding="utf-8")
  569	            self.assertEqual(on_disk, dumps_canonical(p))
  570	```
  571	
  572	- [ ] **Step 2: Run, verify red**
  573	
  574	Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_serialize -v`
  575	
  576	- [ ] **Step 3: Implement serialize.py**
  577	
  578	```python
  579	# tools/tasktool/serialize.py
  580	from __future__ import annotations
  581	import json
  582	from dataclasses import asdict
  583	from pathlib import Path
  584	from tasktool.model import (
  585	    Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, BlockedOn, Status, SCHEMA_VERSION,
  586	)
  587	
  588	def to_dict(p: Project) -> dict:
  589	    def _coerce(obj):
  590	        if isinstance(obj, Status):
  591	            return obj.value
  592	        return obj
  593	    raw = asdict(p)
  594	    # asdict recurses; convert any Status enum values that survived to strings.
  595	    def walk(node):
  596	        if isinstance(node, dict):
  597	            return {k: walk(v) for k, v in node.items()}
  598	        if isinstance(node, list):
  599	            return [walk(v) for v in node]
  600	        return _coerce(node)

[truncated: 2528 additional lines]

## Context Previews

### docs/specs/2026-05-17-P2-tasktool-design.md

    1	# P2 — tasktool: JSON-backed task management CLI
    2	
    3	**Status:** spec, awaiting external review
    4	**Author:** Simon Greer (with AI brainstorming)
    5	**Date:** 2026-05-17
    6	**TASKLIST entry:** `P2` in [`docs/TASKLIST.md`](../TASKLIST.md)
    7	
    8	## 1. Problem
    9	
   10	`docs/TASKLIST.md` is the canonical project tracker in superstar's workflow. The format is enforced by prose (the `tasklist-discipline` skill), not by code:
   11	
   12	- Stable P/S/T/X IDs, never renumbered.
   13	- Status emoji set (`✅` / `🚧` / `⏸` / `☐`) paired with status tags (`DONE YYYY-MM-DD`, `IN PROGRESS`, `BLOCKED on …`, `READY`).
   14	- Specific date format, specific filename conventions, specific close-in-place / phase-archive rules.
   15	
   16	Two consequences:
   17	
   18	1. **Brittleness for downstream consumers.** The AGS sidebar, external reviewers, and any future dashboards have to re-parse a hand-edited markdown file whose shape is enforced only by an LLM following a skill. A single stray emoji or missing date breaks the consumer.
   19	2. **Context bloat for agents.** The current pattern is "agent reads the entire TASKLIST.md to orient." Most of that content is irrelevant to the agent's current task. The agent absorbs the whole file because targeted queries do not exist.
   20	
   21	Conformity is enforced by repeatedly reminding agents of the rules. This works imperfectly and consumes context every time.
   22	
   23	## 2. Goals
   24	
   25	- **Eliminate hand-editing of the canonical tracker.** All mutations go through a single CLI that validates inputs at write time.
   26	- **Reduce agent context burden.** Replace "read the whole file" with targeted queries (`tasktool brief <id>`, `tasktool show <id>`, `tasktool list --status open`).
   27	- **Produce reliable structured data for downstream tools** (AGS sidebar, reviewers, future dashboards) without forcing them to re-parse markdown.
   28	- **Preserve the existing mental model** (phases / slices / tasks / cross-cutting; stable IDs; close-in-place; phase archive; status gates).
   29	- **Stay zero-dependency.** Python stdlib only. No package install required at the project level — a global shim points at this repo.
   30	
   31	## 3. Non-goals
   32	
   33	- **Cross-project querying.** Each project keeps its own JSON; there is no central store. AGS can read multiple per-project JSONs if it wants a cross-project view.
   34	- **External-system sync.** No Linear, Jira, GitHub Projects integration. Out of scope.
   35	- **Web UI.** Out of scope. The AGS sidebar is the user-facing view; the CLI is the agent-facing view.
   36	- **Concurrent multi-writer correctness.** Single-user, single-machine. File-level write is atomic via tempfile + rename; no locking beyond that.
   37	- **Backwards compatibility with the markdown shape.** `tasktool render` produces a readable markdown view but is not constrained to byte-match the prior hand-written format.
   38	
   39	## 4. Approach summary
   40	
   41	A Python stdlib CLI (`tasktool`) reads and writes a per-project `docs/tasklist.json`. The CLI is the only sanctioned mutation path; the `tasklist-discipline` skill is rewritten to teach the commands rather than the rules. A pre-commit hook enforces that `docs/tasklist.json` only changes via the CLI. The existing `docs/TASKLIST.md` is parsed by a one-shot importer and then deleted; downstream readers (AGS sidebar) consume the JSON directly or import the Python module.
   42	
   43	## 5. Architecture
   44	
   45	### 5.1 Code location & distribution
   46	
   47	- **Source:** `tools/tasktool/` in the superstar repo. Single Python package; entry point `tools/tasktool/__main__.py`.
   48	- **Stdlib only:** `argparse`, `json`, `pathlib`, `dataclasses`, `datetime`, `re`, `sys`, `os`, `subprocess` (for git-staging the JSON after writes), `unittest`.
   49	- **Global shim:** `~/.local/bin/tasktool` — one-line script: `exec python3 /home/simon/Dev/sigreer/skills/superstar/tools/tasktool/__main__.py "$@"`. Installed once per machine by `tools/tasktool/install.sh`. The installer is idempotent; it errors if a different shim already exists at the target path unless `--force` is passed.
   50	- **No per-project install step.** Projects need only the per-project `docs/tasklist.json` and (optionally) the pre-commit hook.
   51	
   52	### 5.2 Per-project state
   53	
   54	- **`docs/tasklist.json`** — canonical, git-tracked.
   55	- **No committed markdown.** `tasktool render` writes a markdown view to stdout on demand. The output is suitable for piping into a temp file for review or pasting into a PR description.
   56	- **Schema version field** in the JSON enables future migrations.
   57	
   58	### 5.3 Integration with consumers
   59	
   60	- **AGS sidebar (Python):** `import tasktool` directly. The installer adds the package to a known site-packages-equivalent path (or symlinks). Functions like `load_project(path)`, `brief(project, id)` are exposed.
   61	- **Other tools:** read `docs/tasklist.json` directly, validated against the schema emitted by `tasktool schema`.
   62	- **External reviewer / skills:** call `tasktool render`, `tasktool show`, `tasktool brief` as needed.
   63	
   64	## 6. Data model
   65	
   66	### 6.1 Top-level shape (`docs/tasklist.json`)
   67	
   68	```json
   69	{
   70	  "schema_version": 1,
   71	  "project": "superstar",
   72	  "north_star": "Optional one-paragraph project intent.",
   73	  "last_reviewed": "2026-05-17",
   74	  "phases": [ /* Phase[] */ ],
   75	  "cross_cutting": [ /* CrossCuttingItem[] */ ],
   76	  "archived_phases": [ /* { id, title, archived_path, archived_date } */ ]
   77	}
   78	```
   79	
   80	### 6.2 Phase
   81	
   82	```json
   83	{
   84	  "id": "P2",
   85	  "title": "tasktool: JSON-backed task management CLI",
   86	  "status": "in_progress",
   87	  "created": "2026-05-17",
   88	  "closed": null,
   89	  "spec_path": "docs/specs/2026-05-17-P2-tasktool-design.md",
   90	  "plan_path": null,
   91	  "phase_reviewer_chain": null,
   92	  "notes": "",
   93	  "slices": [ /* Slice[] */ ]
   94	}
   95	```
   96	
   97	### 6.3 Slice
   98	
   99	```json
  100	{
  101	  "id": "S1",
  102	  "title": "CLI core",
  103	  "status": "ready",
  104	  "created": "2026-05-17",
  105	  "closed": null,
  106	  "blocked_on": null,
  107	  "plan_path": null,
  108	  "refs": [],
  109	  "notes": "",
  110	  "reviewer_chain": null,
  111	  "tasks": [ /* Task[] */ ]
  112	}
  113	```
  114	
  115	- `id` is the short form within its phase (`S1`, `S5a`).
  116	- Follow-up slices use a letter suffix (`S5a`); the suffix is part of the ID string. Ordering within `slices[]` is execution order; ID order is creation order.
  117	- `blocked_on` is `null` or `{ "kind": "id" | "external", "value": "P2.S1" | "vendor X" }`.
  118	- `reviewer_chain` is the relative path to the post-slice reviewer chain folder once one exists.
  119	
  120	### 6.4 Task
  121	
  122	```json
  123	{
  124	  "id": "T1",
  125	  "title": "Implement data model module",
  126	  "status": "ready",
  127	  "created": "2026-05-17",
  128	  "closed": null,
  129	  "refs": [],
  130	  "notes": ""
  131	}
  132	```
  133	
  134	Inline follow-ons that used to be unstructured bullets become first-class tasks with their own `T{n}` IDs.
  135	
  136	### 6.5 Cross-cutting
  137	
  138	```json
  139	{
  140	  "id": "X1",
  141	  "title": "...",
  142	  "status": "ready",
  143	  "created": "...",
  144	  "closed": null,
  145	  "refs": [],
  146	  "notes": ""
  147	}
  148	```
  149	
  150	### 6.6 Status enum
  151	
  152	`done | in_progress | blocked | ready`
  153	
  154	Stored as a plain string. Emoji is a render concern. `done` requires a non-null `closed` date (validator enforces).
  155	
  156	**Blocking is slice-scoped.** Only slices carry `blocked_on` and may take status `blocked`. Phases, tasks, and cross-cutting items use `ready | in_progress | done` only. Rationale: at the granularity of phases and tasks, "blocked" conflates with "waiting" and "deferred" without adding signal; at the slice boundary it has a clear meaning (a unit of work that cannot proceed until another finishes). The validator rejects `blocked` status on phases/tasks/cross-cutting and rejects a non-null `blocked_on` on the same. The `tasktool block` / `unblock` commands accept only slice IDs and error otherwise.
  157	
  158	### 6.7 Dates
  159	
  160	ISO 8601 date (`YYYY-MM-DD`). `closed` is auto-stamped to today at the moment of status→done; the user can backdate via `--closed-date YYYY-MM-DD`. `created` is auto-stamped at create time and is read-only thereafter (no `tasktool` command edits it; raw-edit escape hatch only).
  161	
  162	### 6.8 Fully-qualified IDs
  163	
  164	Stored as short form (`S2`, `T1`); fully-qualified form (`P2.S1.T1`) is derived for display and CLI arguments. The CLI accepts both forms in arguments; ambiguous short forms (e.g., `S1` without a phase context) are rejected with a clear error.
  165	
  166	### 6.9 Validation rules
  167	
  168	- ID format: `P\d+`, `S\d+[a-z]?`, `T\d+`, `X\d+`.
  169	- IDs unique within their scope.
  170	- `done` requires `closed != null`.
  171	- `blocked` requires `blocked_on != null`.
  172	- `closed >= created` when both set.
  173	- `spec_path`, `plan_path`, `refs[]` are checked for filesystem existence by `tasktool validate` (warning, not error, since paths may be deleted in branches).
  174	- `reviewer_chain` directory must exist at slice close time when post-slice review is required.
  175	
  176	## 7. CLI surface
  177	
  178	Conventions: arguments named `<id>` accept fully-qualified (`P2.S1`) or short form when unambiguous. Mutating commands write atomically (tempfile + rename) and `git add` the file (best-effort; non-fatal if not a git repo).
  179	
  180	### 7.1 Lifecycle
  181	
  182	```
  183	tasktool init [--project NAME] [--north-star TEXT]
  184	    Create empty docs/tasklist.json. Errors if file exists unless --force.
  185	
  186	tasktool import PATH_TO_TASKLIST_MD [--dry-run]
  187	    One-shot migration from existing TASKLIST.md. Prints unparsed lines as warnings.
  188	    --dry-run prints the JSON it would write without touching disk.
  189	
  190	tasktool schema
  191	    Emit the JSON Schema for tasklist.json to stdout.
  192	```
  193	
  194	### 7.2 Create
  195	
  196	```
  197	tasktool create phase --title TEXT [--spec PATH] [--plan PATH]
  198	    Allocates next P{n}, taking the orphan-aware max+1 across the file plus docs/specs/, docs/plans/, docs/reviewer/ filename prefixes. Prints the new ID.
  199	
  200	tasktool create slice <phase-id> --title TEXT [--follow-up <slice-id>] [--plan PATH]

[truncated: 171 additional lines]
### docs/TASKLIST.md

    1	# Project Task List
    2	
    3	Top-level task tracker for **superstar (personal fork)**. This document is the canonical overview. Per-phase, per-slice, and per-task details live in the linked plans. Completed phases live in [`docs/archived-tasks/`](archived-tasks/).
    4	
    5	**Last reviewed:** 2026-05-17.
    6	
    7	> **Transitional note.** This file is the canonical tracker today. Once `P2` (tasktool) ships, this file is imported into `docs/tasklist.json` and removed; per-slice progress is then tracked via the `tasktool` CLI. Pre-existing work (the external-reviewer phases) has been retroactively assigned `P1` to keep IDs collision-free; that phase is already closed and is referenced here only for ID-allocation purposes.
    8	
    9	---
   10	
   11	## Numbering & status discipline
   12	
   13	See [`superstar:tasklist-discipline`](https://github.com/sigreer/superstar/tree/main/skills/tasklist-discipline) for the full rules. Summary:
   14	
   15	**ID scheme.** Stable IDs, never renumbered. Short form within nested context; fully-qualified for cross-scope references.
   16	
   17	| Scope           | Short form (in headers) | Fully-qualified (in references) |
   18	|-----------------|--------------------------|---------------------------------|
   19	| Phase           | `P2`                     | `P2`                            |
   20	| Slice           | `S1`                     | `P2.S1`                         |
   21	| Follow-up slice | `S5a`                    | `P2.S5a`                        |
   22	| Task            | `T3`                     | `P2.S5.T3`                      |
   23	| Cross-cutting   | `X4`                     | `P2.X4`                         |
   24	
   25	**Status.**
   26	
   27	| Emoji | Tag                  | Meaning                  |
   28	|-------|----------------------|--------------------------|
   29	| ✅    | `DONE YYYY-MM-DD`    | Complete                 |
   30	| 🚧    | `IN PROGRESS`        | Active work              |
   31	| ⏸    | `BLOCKED on …`       | Waiting on a dependency  |
   32	| ☐    | `READY` / `TODO`     | Not started, unblocked   |
   33	
   34	---
   35	
   36	## North Star
   37	
   38	Make superstar's workflow skills produce reliable, machine-readable artifacts so that downstream tools (AGS sidebar, reviewers, future dashboards) can consume project state without re-parsing brittle markdown. The first beachhead is the tasklist itself.
   39	
   40	---
   41	
   42	## P1 — External-reviewer work (historical) ✅ `DONE 2026-05-17`
   43	
   44	Pre-existing phase, reconstructed from `docs/specs/`, `docs/plans/`, and `docs/reviewer/` to preserve ID continuity. Not actively tracked here; see existing artifacts for detail.
   45	
   46	---
   47	
   48	## P2 — tasktool: JSON-backed task management CLI 🚧 `IN PROGRESS`
   49	
   50	Spec: [`docs/specs/2026-05-17-P2-tasktool-design.md`](specs/2026-05-17-P2-tasktool-design.md). Plan: _pending_.
   51	
   52	- ☐ **S1** CLI core: data model, canonical serializer, allocation, validation, reviewer-gate, and the create/set/close/block/note/ref/title/show/list/validate/schema/next-id/init commands. Plan: [`docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md`](plans/2026-05-17-p2-s1-tasktool-cli-core.md).
   53	- ☐ **S2** Importer, render, brief, archive-phase; migrate this repo from `TASKLIST.md` to `tasklist.json`. Plan: _pending — written after S1 ships._
   54	- ☐ **S3** Rewrite `tasklist-discipline` skill; install pre-commit hook; touch up sibling skills (`writing-plans`, `external-review`, `project-setup`, `brainstorming`, `subagent-driven-development`). Plan: _pending — written after S2 ships._
   55	
   56	---
   57	
   58	## Cross-cutting (`X*`) — opportunistic, unscheduled
   59	
   60	_None yet._
   61	
   62	---
   63	
   64	## How to use this map
   65	
   66	- **Starting a new session?** Read this file first to orient. Drill into the linked plan only when you're working on a specific slice.
   67	- **Finishing a slice?** Tick boxes (☐ → ✅), flip the slice header emoji + tag to `✅ DONE YYYY-MM-DD`, append post-impl notes inline. Don't renumber. Don't relocate within the live file.
   68	- **Finishing a phase?** Run `external-review --kind post-phase` first. On `ready` / `ready with small edits`, move the entire phase section to `docs/archived-tasks/P{n}-<short-title>.md` and leave a one-line summary + archive link here.
   69	- **Adding a new initiative?** Give it the next free ID, insert at the correct execution-order position, link the plan as soon as it exists.

<!-- superstar-prompt:end -->