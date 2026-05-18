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
docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md

Additional context files:
- docs/specs/2026-05-17-P2-tasktool-design.md
- docs/tasklist.json

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

### docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md

    1	# P2.S2 — tasktool importer / render / brief / archive-phase Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Add the four S2 commands to `tasktool` (`import`, `render`, `brief`, `archive-phase`), then migrate this repository from `docs/TASKLIST.md` to `docs/tasklist.json`. End state: `docs/TASKLIST.md` is deleted, `docs/tasklist.json` is the canonical tracker, `tasktool render` reproduces a semantically-equivalent markdown view on demand, and `tasktool brief P2.S2` returns the start-of-work primer for the next agent that picks up work in this phase.
    6	
    7	**Architecture:** Three new pure modules under `tools/tasktool/` — `importer.py` (markdown→Project), `render.py` (Project→markdown), `brief.py` (Project→primer markdown). `commands.py` grows four new `cmd_*` functions; `cli.py` grows four subparsers. The new modules follow the S1 layering rule: pure, side-effect-free, tested in isolation; `commands` is the only disk-touching orchestrator. `archive-phase` extends `commands` with a new orchestrator that reuses `reviewer_gate.check_gate` (via `_apply_review_gate`'s `phase` branch) and adds an `ArchivedPhase` record alongside writing a markdown summary.
    8	
    9	**Tech Stack:** Python 3.11+ (stdlib only — `re`, `pathlib`, `json`, `datetime`, `argparse`, `unittest`). Zero third-party deps. Same conventions as S1.
   10	
   11	---
   12	
   13	## File structure
   14	
   15	Created in this slice:
   16	
   17	```
   18	tools/tasktool/
   19	├── importer.py             # parse TASKLIST.md → Project (best-effort, lossy-by-design)
   20	├── render.py               # Project → markdown view (not byte-identical to old TASKLIST.md)
   21	├── brief.py                # Project + id → start-of-work primer markdown
   22	└── tests/
   23	    ├── test_importer.py
   24	    ├── test_render.py
   25	    └── test_brief.py
   26	```
   27	
   28	Modified in this slice:
   29	
   30	```
   31	tools/tasktool/
   32	├── commands.py             # +cmd_import / +cmd_render / +cmd_brief / +cmd_archive_phase
   33	├── cli.py                  # +import / +render / +brief / +archive-phase subparsers
   34	├── __init__.py             # re-export importer.parse_tasklist_md, render.render_project, brief.brief
   35	└── tests/
   36	    ├── test_commands.py    # +cmd_archive_phase tests
   37	    └── test_cli_integration.py   # +import/render/brief/archive-phase CLI tests
   38	```
   39	
   40	Repo files touched at migration time (Task 11):
   41	
   42	```
   43	docs/
   44	├── tasklist.json           # NEW, canonical
   45	├── TASKLIST.md             # DELETED
   46	└── archived-tasks/         # may receive P1 summary if --archive-historical is used
   47	```
   48	
   49	Not touched in this slice: `tools/tasktool/templates/pre-commit-tasktool` (S3); any sibling skills (S3).
   50	
   51	---
   52	
   53	## Conventions used throughout
   54	
   55	- **TDD:** every task writes the failing test, runs it red, implements the minimum, runs it green, commits. Commits per task, not per step.
   56	- **Commit message prefix:** `P2.S2:` followed by an imperative one-liner.
   57	- **Run tests via:** `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`.
   58	- **No third-party deps.** Stdlib only.
   59	- **Python style:** dataclasses with `slots=True`; `from __future__ import annotations` everywhere; type hints on public functions.
   60	- **Pure modules return data; commands print/save.** `importer.parse_tasklist_md(text) -> ParseResult`, `render.render_project(p) -> str`, `brief.brief(p, qid) -> str`. None of those touch disk.
   61	- **Status emoji table** — applies *by kind*. The data model only allows `blocked` on slices (spec §6.6, enforced by `validate.py`). Importer/renderer must respect this:
   62	
   63	  | emoji | status        | extra tag suffix              | valid on   |
   64	  |-------|---------------|-------------------------------|------------|
   65	  | ✅    | `done`        | `DONE YYYY-MM-DD`             | phase/slice/task/cross |
   66	  | 🚧    | `in_progress` | `IN PROGRESS`                 | phase/slice/task/cross |
   67	  | ⏸     | `blocked`     | `BLOCKED on <text>`           | **slice only** |
   68	  | ☐     | `ready`       | `READY` / `TODO` (interchangeable on import; render emits `READY`) | phase/slice/task/cross |
   69	
   70	  **Importer rule:** a `⏸ blocked` marker on a phase or cross-cutting bullet emits a warning (`f"line {lineno}: blocked status not allowed on {kind}; coerced to ready"`) and the parser falls back to `Status.READY`. **Render rule:** `_phase_tag` and the cross-cutting render branch only emit a `BLOCKED on …` tag for slices; on a phase/cross the function returns `""` even if status somehow == blocked (the validator rejects that on save, but the renderer must also never produce invalid markdown).
   71	
   72	---
   73	
   74	## Task 1: Importer — phase header parsing
   75	
   76	**Files:**
   77	- Create: `tools/tasktool/importer.py`
   78	- Create: `tools/tasktool/tests/test_importer.py`
   79	
   80	The importer is the riskiest module because the input is hand-written markdown. We build it incrementally: phases first, then slices, then cross-cutting, then archived references. Each task adds one parser concern with fixtures.
   81	
   82	`parse_tasklist_md(text: str) -> ParseResult` returns:
   83	
   84	```python
   85	@dataclass(slots=True)
   86	class ParseResult:
   87	    project: Project           # parsed model (may be partial on errors)
   88	    warnings: list[str]        # unparsed lines / ambiguous tokens
   89	```
   90	
   91	The parser is **forgiving**: it never raises on malformed input. Anything it cannot interpret becomes a warning (line number + offending text). The caller decides whether to abort.
   92	
   93	- [ ] **Step 1: Write the failing test**
   94	
   95	```python
   96	# tools/tasktool/tests/test_importer.py
   97	from __future__ import annotations
   98	import unittest
   99	from tasktool.importer import parse_tasklist_md
  100	from tasktool.model import Status
  101	
  102	PHASE_HEADER = """\
  103	# Project Task List
  104	
  105	## P2 — tasktool: JSON-backed task management CLI 🚧 `IN PROGRESS`
  106	
  107	Spec: [`docs/specs/2026-05-17-P2-tasktool-design.md`](specs/2026-05-17-P2-tasktool-design.md). Plan: _pending_.
  108	"""
  109	
  110	PHASE_HEADER_DONE = """\
  111	## P1 — Old phase ✅ `DONE 2026-05-17`
  112	
  113	Closed; see archive.
  114	"""
  115	
  116	class TestImporterPhase(unittest.TestCase):
  117	    def test_phase_header_basic(self):
  118	        r = parse_tasklist_md(PHASE_HEADER)
  119	        self.assertEqual(len(r.project.phases), 1)
  120	        ph = r.project.phases[0]
  121	        self.assertEqual(ph.id, "P2")
  122	        self.assertEqual(ph.title, "tasktool: JSON-backed task management CLI")
  123	        self.assertEqual(ph.status, Status.IN_PROGRESS)
  124	        self.assertEqual(ph.spec_path, "docs/specs/2026-05-17-P2-tasktool-design.md")
  125	        self.assertIsNone(ph.plan_path)  # "_pending_" → None
  126	
  127	    def test_phase_done_tag_sets_closed(self):
  128	        r = parse_tasklist_md(PHASE_HEADER_DONE)
  129	        self.assertEqual(len(r.project.phases), 1)
  130	        ph = r.project.phases[0]
  131	        self.assertEqual(ph.id, "P1")
  132	        self.assertEqual(ph.status, Status.DONE)
  133	        self.assertEqual(ph.closed, "2026-05-17")  # required for validator pass
  134	```
  135	
  136	- [ ] **Step 2: Run test to verify it fails**
  137	
  138	Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_importer -v`
  139	Expected: FAIL with `ModuleNotFoundError: No module named 'tasktool.importer'`.
  140	
  141	- [ ] **Step 3: Write minimal implementation**
  142	
  143	```python
  144	# tools/tasktool/importer.py
  145	from __future__ import annotations
  146	import re
  147	from dataclasses import dataclass, field
  148	from tasktool.model import Project, Phase, Status
  149	
  150	EMOJI_TO_STATUS = {
  151	    "✅": Status.DONE,
  152	    "🚧": Status.IN_PROGRESS,
  153	    "⏸": Status.BLOCKED,
  154	    "☐": Status.READY,
  155	}
  156	
  157	PHASE_HEADER_RE = re.compile(
  158	    r"^##\s+(?P<id>P\d+)\s+—\s+(?P<title>.+?)\s+"
  159	    r"(?P<emoji>[✅🚧☐])(?:\s+`(?P<tag>[^`]+)`)?\s*$"
  160	)
  161	# Phase headers may NOT use ⏸ (blocked is slice-only — spec §6.6).
  162	# A `⏸ Pn …` line matches the fallback below, which records the item
  163	# under `phases[]` with status=READY and emits an explicit warning.
  164	PHASE_HEADER_BLOCKED_RE = re.compile(
  165	    r"^##\s+(?P<id>P\d+)\s+—\s+(?P<title>.+?)\s+"
  166	    r"⏸(?:\s+`(?P<tag>[^`]+)`)?\s*$"
  167	)
  168	PHASE_DONE_TAG_RE = re.compile(r"^DONE\s+(?P<date>\d{4}-\d{2}-\d{2})$")
  169	SPEC_RE = re.compile(r"Spec:\s*\[`(?P<path>[^`]+)`\]\([^)]+\)")
  170	PLAN_RE = re.compile(r"Plan:\s*(?:\[`(?P<path>[^`]+)`\]\([^)]+\)|_pending_)")
  171	
  172	@dataclass(slots=True)
  173	class ParseResult:
  174	    project: Project
  175	    warnings: list[str] = field(default_factory=list)
  176	
  177	def _apply_phase_tag(phase: Phase, tag: str | None) -> None:
  178	    """Translate the optional `\`...\`` tag suffix into model fields."""
  179	    if not tag:
  180	        return
  181	    dm = PHASE_DONE_TAG_RE.match(tag)
  182	    if dm:
  183	        phase.closed = dm.group("date")
  184	    # `IN PROGRESS` adds no extra field beyond the emoji-derived status.
  185	    # Other tag forms are ignored (warnings are emitted elsewhere only
  186	    # for clearly-invalid statuses like blocked-on-phase).
  187	
  188	def parse_tasklist_md(text: str) -> ParseResult:
  189	    project = Project(project="<imported>", schema_version=1)
  190	    warnings: list[str] = []
  191	    current_phase: Phase | None = None
  192	    for lineno, raw in enumerate(text.splitlines(), start=1):
  193	        m = PHASE_HEADER_RE.match(raw)
  194	        if m:
  195	            current_phase = Phase(
  196	                id=m.group("id"),
  197	                title=m.group("title").strip(),
  198	                created="1970-01-01",  # placeholder; importer cannot recover real created dates
  199	                status=EMOJI_TO_STATUS[m.group("emoji")],
  200	            )
  201	            _apply_phase_tag(current_phase, m.group("tag"))
  202	            project.phases.append(current_phase)
  203	            continue
  204	        bm = PHASE_HEADER_BLOCKED_RE.match(raw)
  205	        if bm:
  206	            warnings.append(
  207	                f"line {lineno}: blocked status not allowed on phase; coerced to ready"
  208	            )
  209	            current_phase = Phase(
  210	                id=bm.group("id"),
  211	                title=bm.group("title").strip(),
  212	                created="1970-01-01",
  213	                status=Status.READY,
  214	            )
  215	            project.phases.append(current_phase)
  216	            continue
  217	        if current_phase is not None:
  218	            sm = SPEC_RE.search(raw)
  219	            if sm:
  220	                current_phase.spec_path = sm.group("path")
  221	            pm = PLAN_RE.search(raw)
  222	            if pm and pm.group("path"):
  223	                current_phase.plan_path = pm.group("path")
  224	    return ParseResult(project=project, warnings=warnings)
  225	```
  226	
  227	- [ ] **Step 4: Run test to verify it passes**
  228	
  229	Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_importer -v`
  230	Expected: PASS.
  231	
  232	- [ ] **Step 5: Commit**
  233	
  234	```bash
  235	git add tools/tasktool/importer.py tools/tasktool/tests/test_importer.py
  236	git commit -m "P2.S2: importer — phase header parsing"
  237	```
  238	
  239	---
  240	
  241	## Task 2: Importer — slice bullet parsing
  242	
  243	**Files:**
  244	- Modify: `tools/tasktool/importer.py`
  245	- Modify: `tools/tasktool/tests/test_importer.py`
  246	
  247	Slice bullets look like:
  248	
  249	```
  250	- ✅ **S1** `DONE 2026-05-18` — CLI core: data model, ... Plan: [`docs/plans/...`](...). Post-impl: 139 tests; ...
  251	- ☐ **S2** Importer, render, brief, archive-phase; ...  Plan: _pending — written after S1 ships._
  252	```
  253	
  254	The slice line contains: emoji, ID (`S\d+[a-z]?`), tag in backticks (optional for `READY`), then title text, optional inline `Plan: [...]` link, optional trailing prose.
  255	
  256	- [ ] **Step 1: Write the failing test**
  257	
  258	```python
  259	# add to test_importer.py
  260	SLICES_BLOCK = """\
  261	## P2 — Demo 🚧 `IN PROGRESS`
  262	
  263	- ✅ **S1** `DONE 2026-05-18` — CLI core: data model. Plan: [`docs/plans/2026-05-17-p2-s1.md`](plans/2026-05-17-p2-s1.md). Post-impl: 139 tests.
  264	- ☐ **S2** Importer, render, brief. Plan: _pending._
  265	- ⏸ **S3a** `BLOCKED on P2.S2` — follow-up cleanup.
  266	"""
  267	
  268	class TestImporterSlices(unittest.TestCase):
  269	    def test_slice_parsing(self):
  270	        r = parse_tasklist_md(SLICES_BLOCK)
  271	        self.assertEqual(len(r.project.phases), 1)
  272	        slices = r.project.phases[0].slices
  273	        self.assertEqual([s.id for s in slices], ["S1", "S2", "S3a"])
  274	        self.assertEqual(slices[0].status, Status.DONE)
  275	        self.assertEqual(slices[0].closed, "2026-05-18")
  276	        self.assertEqual(slices[0].plan_path, "docs/plans/2026-05-17-p2-s1.md")
  277	        self.assertEqual(slices[1].status, Status.READY)
  278	        self.assertIsNone(slices[1].plan_path)
  279	        self.assertEqual(slices[2].status, Status.BLOCKED)
  280	        self.assertIsNotNone(slices[2].blocked_on)
  281	        self.assertEqual(slices[2].blocked_on.kind, "id")
  282	        self.assertEqual(slices[2].blocked_on.value, "P2.S3")  # parsed from "BLOCKED on P2.S3"... see note
  283	```
  284	
  285	Note: the test asserts `P2.S3` because that's what the tag says. Adjust the fixture if needed; the importer's job is to capture the literal value after "BLOCKED on ".
  286	
  287	Correct the test fixture: change the third bullet to `\`BLOCKED on P2.S3\`` (without the `a`) so the assertion is self-consistent. The slice ID itself is `S3a`; what it's blocked on is `P2.S3`.
  288	
  289	- [ ] **Step 2: Run test to verify it fails**
  290	
  291	Expected: FAIL — no slice parsing yet.
  292	
  293	- [ ] **Step 3: Write the implementation**
  294	
  295	Add to `importer.py`:
  296	
  297	```python
  298	SLICE_LINE_RE = re.compile(
  299	    r"^-\s+(?P<emoji>[✅🚧⏸☐])\s+\*\*(?P<id>S\d+[a-z]?)\*\*"
  300	    r"(?:\s+`(?P<tag>[^`]+)`)?"
  301	    r"(?:\s+—\s+(?P<rest>.+))?$"
  302	)
  303	DONE_TAG_RE   = re.compile(r"^DONE\s+(?P<date>\d{4}-\d{2}-\d{2})$")
  304	BLOCKED_TAG_RE = re.compile(r"^BLOCKED on\s+(?P<on>.+)$")
  305	INLINE_PLAN_RE = re.compile(r"Plan:\s*\[`(?P<path>[^`]+)`\]\([^)]+\)")
  306	```
  307	
  308	Extend the loop in `parse_tasklist_md`:
  309	
  310	```python
  311	from tasktool.model import Slice, BlockedOn
  312	
  313	# inside loop, after PHASE_HEADER_RE branch:
  314	sm = SLICE_LINE_RE.match(raw)
  315	if sm and current_phase is not None:
  316	    emoji = sm.group("emoji")
  317	    tag = sm.group("tag")
  318	    rest = sm.group("rest") or ""
  319	    title = rest.split(". Plan:", 1)[0].strip() or "<untitled>"
  320	    s = Slice(
  321	        id=sm.group("id"),
  322	        title=title,
  323	        created="1970-01-01",
  324	        status=EMOJI_TO_STATUS[emoji],
  325	    )
  326	    if tag:
  327	        dm = DONE_TAG_RE.match(tag)
  328	        if dm:
  329	            s.closed = dm.group("date")
  330	        bm = BLOCKED_TAG_RE.match(tag)
  331	        if bm:
  332	            on = bm.group("on").strip()
  333	            s.blocked_on = BlockedOn(kind="external" if on.startswith("external:") else "id",
  334	                                     value=on[len("external:"):] if on.startswith("external:") else on)
  335	    pm = INLINE_PLAN_RE.search(rest)
  336	    if pm:
  337	        s.plan_path = pm.group("path")
  338	    current_phase.slices.append(s)
  339	    continue
  340	```
  341	
  342	- [ ] **Step 4: Run test to verify it passes**
  343	
  344	Expected: PASS.
  345	
  346	- [ ] **Step 5: Commit**
  347	
  348	```bash
  349	git add tools/tasktool/importer.py tools/tasktool/tests/test_importer.py
  350	git commit -m "P2.S2: importer — slice bullet parsing"
  351	```
  352	
  353	---
  354	
  355	## Task 3: Importer — cross-cutting + archived references + warnings
  356	
  357	**Files:**
  358	- Modify: `tools/tasktool/importer.py`
  359	- Modify: `tools/tasktool/tests/test_importer.py`
  360	
  361	Cross-cutting block is introduced by `## Cross-cutting` and contains bullets shaped like slice bullets but with `X\d+` IDs. Historical / archived references show up as one-line phase summaries (no slice bullets); they are imported as ordinary `phases[]` entries with `status: done` and an "imported as historical" note (see the rule restated lower in this task). The importer **never** writes to `archived_phases[]` — that table is exclusively populated by `tasktool archive-phase`.
  362	
  363	Unmatched lines under a known section are silently ignored *unless* they look like a bullet (`-` at start) — those become warnings.
  364	
  365	- [ ] **Step 1: Write the failing test**
  366	
  367	```python
  368	# add to test_importer.py
  369	CROSS_AND_NOISE = """\
  370	## Cross-cutting (`X*`) — opportunistic, unscheduled
  371	
  372	- ☐ **X1** — gather telemetry for skill firing rate.
  373	- ⏸ **X2** — bogus blocked cross item.
  374	- malformed bullet
  375	
  376	## P1 — Old work (historical) ✅ `DONE 2025-12-01`
  377	
  378	Closed; see `docs/archived-tasks/P1-old.md`.
  379	"""
  380	
  381	class TestImporterMisc(unittest.TestCase):
  382	    def test_cross_and_warnings(self):
  383	        r = parse_tasklist_md(CROSS_AND_NOISE)
  384	        # Both cross items are captured; X2's blocked status is coerced to ready.
  385	        self.assertEqual([c.id for c in r.project.cross_cutting], ["X1", "X2"])
  386	        self.assertEqual(r.project.cross_cutting[0].status, Status.READY)
  387	        self.assertEqual(r.project.cross_cutting[1].status, Status.READY)
  388	        # P1 stays in phases[] (historical imports never become ArchivedPhase).
  389	        self.assertTrue(any(ph.id == "P1" for ph in r.project.phases))
  390	        self.assertFalse(r.project.archived_phases)
  391	        # X2's invalid status surfaces as a warning.
  392	        self.assertTrue(any("blocked status not allowed on cross" in w for w in r.warnings))
  393	        # The malformed bullet surfaces as a warning.
  394	        self.assertTrue(any("malformed bullet" in w for w in r.warnings))
  395	
  396	    def test_blocked_phase_coerced_to_ready_with_warning(self):
  397	        text = "## P9 — Bogus blocked phase ⏸ `BLOCKED on something`\n"
  398	        r = parse_tasklist_md(text)
  399	        self.assertEqual(len(r.project.phases), 1)
  400	        self.assertEqual(r.project.phases[0].id, "P9")
  401	        self.assertEqual(r.project.phases[0].status, Status.READY)
  402	        self.assertTrue(
  403	            any("blocked status not allowed on phase" in w for w in r.warnings)
  404	        )
  405	```
  406	
  407	- [ ] **Step 2: Run test to verify it fails**
  408	
  409	Expected: FAIL — no cross-cutting parsing, no warnings collection.
  410	
  411	- [ ] **Step 3: Implementation**
  412	
  413	Add to `importer.py`:
  414	
  415	```python
  416	CROSS_HEADER_RE = re.compile(r"^##\s+Cross-cutting\b")
  417	CROSS_LINE_RE = re.compile(
  418	    r"^-\s+(?P<emoji>[✅🚧☐])\s+\*\*(?P<id>X\d+)\*\*"
  419	    r"(?:\s+—\s+(?P<rest>.+))?$"
  420	)
  421	# Cross-cutting items may NOT be blocked (spec §6.6). A line like
  422	# `- ⏸ **X1** ...` is matched by a fallback regex that uses the wider
  423	# emoji set, emits the "blocked status not allowed on cross" warning,
  424	# and coerces the status to READY before appending the item.
  425	CROSS_LINE_BLOCKED_RE = re.compile(
  426	    r"^-\s+⏸\s+\*\*(?P<id>X\d+)\*\*"
  427	    r"(?:\s+—\s+(?P<rest>.+))?$"
  428	)
  429	```
  430	
  431	In `parse_tasklist_md`, track an `in_cross` flag toggled by `CROSS_HEADER_RE`. When set:
  432	
  433	1. Try `CROSS_LINE_RE`. On match, append `CrossCutting` with the emoji's status.
  434	2. Otherwise try `CROSS_LINE_BLOCKED_RE`. On match, emit a warning `f"line {lineno}: blocked status not allowed on cross; coerced to ready"` and append with `Status.READY`.
  435	3. Otherwise, any line beginning with `- ` becomes a warning of the form `f"line {lineno}: unparsed bullet: {raw!r}"`.
  436	
  437	**Historical / archived phases are imported as ordinary `phases[]` entries**, never as `ArchivedPhase` records. `ArchivedPhase` is reserved for the `tasktool archive-phase` workflow (a phase being archived *now*), not for retroactive imports. The phase status is taken from the emoji on the header; `(historical)` / `(archived)` substrings in the title are left in the title as-is (no special handling — they round-trip through `render` cleanly).
  438	
  439	This makes Task 12's migration check unambiguous: P1 stays in `phases[]` with `status: done` and a historical note; nothing is moved to `archived_phases[]` during the migration.
  440	
  441	- [ ] **Step 4: Run test to verify it passes**
  442	
  443	Expected: PASS.
  444	
  445	- [ ] **Step 5: Commit**
  446	
  447	```bash
  448	git add tools/tasktool/importer.py tools/tasktool/tests/test_importer.py
  449	git commit -m "P2.S2: importer — cross-cutting and warnings"
  450	```
  451	
  452	---
  453	
  454	## Task 4: `tasktool import` command + CLI wiring
  455	
  456	**Files:**
  457	- Modify: `tools/tasktool/commands.py`
  458	- Modify: `tools/tasktool/cli.py`
  459	- Modify: `tools/tasktool/__init__.py`
  460	- Modify: `tools/tasktool/tests/test_cli_integration.py`
  461	
  462	`tasktool import PATH [--dry-run] [--project NAME]`:
  463	
  464	1. Read the markdown file.
  465	2. Call `parse_tasklist_md(text)`.
  466	3. If `--project NAME` is given, override `project.project`; otherwise leave whatever the parser set (default `<imported>`) and the user can edit later via the raw-edit escape hatch (it's the only field there is no command for).
  467	4. If `--dry-run`, print the canonical JSON (via `dumps_canonical`) and the warnings to stdout, do NOT touch disk.
  468	5. Otherwise, refuse if `docs/tasklist.json` already exists unless `--force` is passed. On success, write canonically (via `_save`, which also runs `validate_project`) and print the warnings to stderr.
  469	
  470	- [ ] **Step 1: Write the failing CLI integration test**
  471	
  472	```python
  473	# add to test_cli_integration.py
  474	def test_import_creates_tasklist_json(self):
  475	    # tmp repo with a tiny TASKLIST.md
  476	    (self.repo / "TASKLIST.md").write_text(
  477	        "## P2 — Demo 🚧 `IN PROGRESS`\n\n- ✅ **S1** `DONE 2026-01-01` — done.\n"
  478	    )
  479	    rc, out, err = self.run_cli(["import", str(self.repo / "TASKLIST.md")])
  480	    self.assertEqual(rc, 0)
  481	    self.assertTrue((self.repo / "docs" / "tasklist.json").exists())
  482	    rc2, out2, _ = self.run_cli(["show", "P2.S1"])
  483	    self.assertEqual(rc2, 0)
  484	    self.assertIn("done", out2)
  485	
  486	def test_import_dry_run(self):
  487	    (self.repo / "TASKLIST.md").write_text("## P2 — Demo 🚧 `IN PROGRESS`\n")
  488	    rc, out, err = self.run_cli(["import", str(self.repo / "TASKLIST.md"), "--dry-run"])
  489	    self.assertEqual(rc, 0)
  490	    self.assertFalse((self.repo / "docs" / "tasklist.json").exists())
  491	    self.assertIn('"id": "P2"', out)
  492	```
  493	
  494	- [ ] **Step 2: Run tests to verify they fail**
  495	
  496	Expected: FAIL — `tasktool import` is not a known command.
  497	
  498	- [ ] **Step 3: Implementation**
  499	
  500	In `commands.py`:
  501	
  502	```python
  503	def cmd_import(
  504	    *, repo_root: Path, md_path: Path,
  505	    dry_run: bool = False, force: bool = False, project: str | None = None,
  506	) -> tuple[int, str, str]:
  507	    """Returns (rc, stdout, stderr_warnings)."""
  508	    from tasktool.importer import parse_tasklist_md
  509	    from tasktool.serialize import dumps_canonical
  510	    text = md_path.read_text(encoding="utf-8")
  511	    result = parse_tasklist_md(text)
  512	    if project:
  513	        result.project.project = project
  514	    elif result.project.project == "<imported>":
  515	        result.project.project = repo_root.name
  516	    result.project.last_reviewed = _today()
  517	    warnings_text = "\n".join(result.warnings)
  518	    if dry_run:
  519	        return 0, dumps_canonical(result.project), warnings_text
  520	    target = _tasklist_path(repo_root)
  521	    if target.exists() and not force:
  522	        raise CommandError(f"{target}: already exists. Pass --force to overwrite.")
  523	    _save(repo_root, result.project)
  524	    return 0, f"wrote {target}\n", warnings_text
  525	```
  526	
  527	In `cli.py` (under `_build_parser`):
  528	
  529	```python
  530	p_import = sub.add_parser("import")
  531	p_import.add_argument("md_path", type=Path)
  532	p_import.add_argument("--dry-run", action="store_true")
  533	p_import.add_argument("--force", action="store_true")
  534	p_import.add_argument("--project")
  535	```
  536	
  537	In `main`:
  538	
  539	```python
  540	elif args.cmd == "import":
  541	    rc, out, warn = commands.cmd_import(
  542	        repo_root=root, md_path=args.md_path,
  543	        dry_run=args.dry_run, force=args.force, project=args.project,
  544	    )
  545	    if out:
  546	        sys.stdout.write(out)
  547	    if warn:
  548	        sys.stderr.write(warn + "\n")
  549	    return rc
  550	```
  551	
  552	In `__init__.py`, add `from tasktool.importer import parse_tasklist_md` to the imports and `"parse_tasklist_md"` to `__all__`.
  553	
  554	- [ ] **Step 4: Run tests to verify they pass**
  555	
  556	Run: `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`
  557	Expected: all tests pass.
  558	
  559	- [ ] **Step 5: Commit**
  560	
  561	```bash
  562	git add tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/__init__.py tools/tasktool/tests/test_cli_integration.py
  563	git commit -m "P2.S2: tasktool import command"
  564	```
  565	
  566	---
  567	
  568	## Task 5: `render` module — phases + slices + cross-cutting
  569	
  570	**Files:**
  571	- Create: `tools/tasktool/render.py`
  572	- Create: `tools/tasktool/tests/test_render.py`
  573	
  574	`render.render_project(p: Project) -> str` produces a markdown document approximating the original `TASKLIST.md` shape. It is **not byte-identical** to the hand-written original — that's the explicit non-goal in spec §3. Section ordering, ID-allocation prose, and the "How to use this map" footer are dropped. Only essential content is rendered: project header, last-reviewed line, North Star (if set), per-phase sections, cross-cutting section, archived-phases section.
  575	
  576	- [ ] **Step 1: Write the failing test**
  577	
  578	```python
  579	# tools/tasktool/tests/test_render.py
  580	from __future__ import annotations
  581	import unittest
  582	from tasktool.model import Project, Phase, Slice, CrossCutting, Status, BlockedOn
  583	from tasktool.render import render_project
  584	
  585	class TestRender(unittest.TestCase):
  586	    def test_basic_render(self):
  587	        p = Project(project="demo", north_star="Make it good.", last_reviewed="2026-05-18")
  588	        p.phases.append(Phase(
  589	            id="P2", title="Demo phase", created="2026-05-17",
  590	            status=Status.IN_PROGRESS, spec_path="docs/specs/x.md",
  591	        ))
  592	        p.phases[0].slices.append(Slice(
  593	            id="S1", title="First slice", created="2026-05-17",
  594	            status=Status.DONE, closed="2026-05-18",
  595	            plan_path="docs/plans/y.md",
  596	        ))
  597	        p.phases[0].slices.append(Slice(
  598	            id="S2", title="Second slice", created="2026-05-17",
  599	            status=Status.BLOCKED, blocked_on=BlockedOn(kind="id", value="P2.S1"),
  600	        ))

[truncated: 832 additional lines]

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
### docs/tasklist.json

    1	{
    2	  "archived_phases": [],
    3	  "cross_cutting": [],
    4	  "last_reviewed": "2026-05-18",
    5	  "north_star": "",
    6	  "phases": [
    7	    {
    8	      "closed": "2026-05-17",
    9	      "created": "2026-05-17",
   10	      "id": "P1",
   11	      "notes": "",
   12	      "phase_reviewer_chain": null,
   13	      "plan_path": null,
   14	      "slices": [],
   15	      "spec_path": null,
   16	      "status": "done",
   17	      "title": "External-reviewer work (historical)"
   18	    },
   19	    {
   20	      "closed": null,
   21	      "created": "2026-05-17",
   22	      "id": "P2",
   23	      "notes": "",
   24	      "phase_reviewer_chain": null,
   25	      "plan_path": null,
   26	      "slices": [
   27	        {
   28	          "blocked_on": null,
   29	          "closed": "2026-05-18",
   30	          "created": "2026-05-17",
   31	          "id": "S1",
   32	          "notes": "",
   33	          "plan_path": "docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md",
   34	          "refs": [],
   35	          "reviewer_chain": "docs/reviewer/p2-s1-tasktool-cli-core-P2-S1-post-slice/",
   36	          "status": "done",
   37	          "tasks": [],
   38	          "title": "CLI core: data model, canonical serializer, allocation, validation, reviewer-gate, and the create/set/close/block/note/ref/title/show/list/validate/schema/next-id/init commands"
   39	        },
   40	        {
   41	          "blocked_on": null,
   42	          "closed": null,
   43	          "created": "2026-05-18",
   44	          "id": "S2",
   45	          "notes": "",
   46	          "plan_path": "docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md",
   47	          "refs": [],
   48	          "reviewer_chain": null,
   49	          "status": "in_progress",
   50	          "tasks": [],
   51	          "title": "Importer, render, brief, archive-phase; migrate this repo from `TASKLIST.md` to `tasklist.json`"
   52	        },
   53	        {
   54	          "blocked_on": null,
   55	          "closed": null,
   56	          "created": "2026-05-18",
   57	          "id": "S3",
   58	          "notes": "",
   59	          "plan_path": null,
   60	          "refs": [],
   61	          "reviewer_chain": null,
   62	          "status": "ready",
   63	          "tasks": [],
   64	          "title": "Rewrite `tasklist-discipline` skill; install pre-commit hook; touch up sibling skills (`writing-plans`, `external-review`, `project-setup`, `brainstorming`, `subagent-driven-development`)"
   65	        }
   66	      ],
   67	      "spec_path": "docs/specs/2026-05-17-P2-tasktool-design.md",
   68	      "status": "in_progress",
   69	      "title": "tasktool: JSON-backed task management CLI"
   70	    }
   71	  ],
   72	  "project": "superstar",
   73	  "schema_version": 1
   74	}

<!-- superstar-prompt:end -->