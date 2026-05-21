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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/x15-archive-closed-cross-cutting-items

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md

Additional context files:
- docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md
- docs/tasklist.json

Review output contract:
1. Findings
   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
     stable if this review is iterated in subsequent rounds.
   - Mark severity inline: `Severity: blocking | important | minor | nit`.
2. Open questions / assumptions
3. Suggested document edits
4. Verification gaps / commands that should be run, if any

End your review with this exact line, as plain text on its own line:

    Overall verdict: <ready|ready with small edits|revise>

Do not bold, italicise, prefix with `##`, split across lines, or drop the
word "Overall". Do not write `**Verdict: ready**` or place the value on a
new line after a heading.

Read the files from disk. Do not rely only on the snippets in this prompt.


## Target Preview

### docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md

    1	# Archive Closed Cross-Cutting Items Implementation Plan
    2
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4
    5	**Goal:** Add lossless archive support for completed `X*` cross-cutting items, with default archive-on-close, `--no-archive`, and manual `archive-cross`.
    6
    7	**Architecture:** Extend the tasktool model with an `archived_cross_cutting` pointer list, then route all X-item archive behavior through command helpers that mirror phase archive atomicity: build archive content in memory, mutate project state in memory, validate, write files, save, stage, notify. Rendering, schema, migration, and tasklist-discipline docs consume the new model field without changing phase archival behavior.
    8
    9	**Tech Stack:** Python dataclasses, tasktool CLI, canonical JSON serialization, unittest/pytest tests under `tools/tasktool/tests`.
   10
   11	---
   12
   13	## File Structure
   14
   15	- Modify `tools/tasktool/model.py` to add `ArchivedCrossCutting` and `Project.archived_cross_cutting`.
   16	- Modify `tools/tasktool/serialize.py` to load/save the new field while preserving legacy tasklists that omit it.
   17	- Modify `tools/tasktool/validate.py` to validate archived X pointer IDs, dates, paths, duplicates, and active/archive collisions.
   18	- Modify `tools/tasktool/schema_gen.py` so `tasktool schema` includes `archived_cross_cutting`.
   19	- Modify `tools/tasktool/migrate.py` so drift migration treats archived X pointers as a top-level collection.
   20	- Modify `tools/tasktool/commands.py` to add `cmd_archive_cross`, default archive-on-close for crosscuts, `--no-archive` enforcement, archive markdown writing, and friendly archived-not-found checks.
   21	- Modify `tools/tasktool/cli.py` to add `close --no-archive` and `archive-cross`.
   22	- Modify `tools/tasktool/render.py` to render archived X pointers separately.
   23	- Verify `tools/tasktool/brief.py` keeps archived X-items outside the active brief surface.
   24	- Modify `skills/tasklist-discipline/SKILL.md` to document X-item close/archive behavior.
   25	- Add or extend tests in `tools/tasktool/tests/test_commands.py`, `test_validate.py`, `test_render.py`, `test_migrate.py`, `test_schema_gen.py`, and CLI integration tests as needed.
   26
   27	## Execution Setup
   28
   29	- [ ] **Step 1: Start from an isolated implementation worktree**
   30
   31	Run from the repository root:
   32
   33	```sh
   34	git status --short
   35	tools/tasktool/tasktool show X15
   36	```
   37
   38	Expected: `X15` exists and references:
   39
   40	```text
   41	docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md
   42	docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md
   43	```
   44
   45	If execution is happening in a new worktree, run the task lifecycle start before editing implementation files. Current `cmd_start` resolves all tasktool row kinds through `_find_item`, so cross-cutting IDs are supported:
   46
   47	```sh
   48	tools/tasktool/tasktool start X15
   49	```
   50
   51	Expected: `X15` moves to `in_progress`.
   52
   53	## Task 1: Model, Serialization, Schema, and Migration
   54
   55	**Files:**
   56	- Modify: `tools/tasktool/model.py`
   57	- Modify: `tools/tasktool/serialize.py`
   58	- Modify: `tools/tasktool/schema_gen.py`
   59	- Modify: `tools/tasktool/migrate.py`
   60	- Modify: `tools/tasktool/tests/test_migrate.py`
   61	- Add or modify: `tools/tasktool/tests/test_schema_gen.py`
   62
   63	- [ ] **Step 1: Add failing model/migration tests**
   64
   65	Append tests to `tools/tasktool/tests/test_migrate.py`:
   66
   67	```python
   68	from tasktool.model import ArchivedCrossCutting
   69
   70
   71	def test_archived_cross_cutting_drift_migrates():
   72	    local = _project_with_slice()
   73	    local.archived_cross_cutting.append(
   74	        ArchivedCrossCutting(
   75	            id="X1",
   76	            title="archived cross",
   77	            archived_path="docs/archived-tasks/X1-archived-cross.md",
   78	            archived_date=_today(),
   79	        )
   80	    )
   81	    authoritative = _project_with_slice()
   82
   83	    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)
   84	    merged = apply_deltas(
   85	        authoritative=authoritative,
   86	        local=local,
   87	        deltas=deltas,
   88	        conflicts=conflicts,
   89	        policy="accept-local",
   90	    )
   91
   92	    assert any(d.kind == "add" and d.row_id == "X1" for d in deltas)
   93	    assert merged.archived_cross_cutting[0].id == "X1"
   94	```
   95
   96	Update the existing imports and parametrization in the same file so `ArchivedCrossCutting` is included anywhere `ArchivedPhase` appears in field coverage:
   97
   98	```python
   99	from tasktool.model import (
  100	    ArchivedCrossCutting,
  101	    ArchivedPhase,
  102	    CrossCutting,
  103	    Phase,
  104	    Project,
  105	    Slice,
  106	    Status,
  107	    Task,
  108	)
  109	```
  110
  111	Add `ArchivedCrossCutting` to:
  112
  113	```python
  114	for row_type in (Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, ArchivedCrossCutting):
  115	```
  116
  117	and:
  118
  119	```python
  120	[Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, ArchivedCrossCutting]
  121	```
  122
  123	Extend `_value_pair_for_field`:
  124
  125	```python
  126	if field.name in {"id", "phases", "slices", "tasks", "cross_cutting", "archived_phases", "archived_cross_cutting"}:
  127	    return (None, None)
  128	```
  129
  130	Extend `set_on`/`get_on`:
  131
  132	```python
  133	elif type_ is ArchivedCrossCutting:
  134	    if not tree.archived_cross_cutting:
  135	        tree.archived_cross_cutting.append(
  136	            ArchivedCrossCutting(
  137	                id="X0",
  138	                title="archived cross",
  139	                archived_path="docs/archived-tasks/X0-archived-cross.md",
  140	                archived_date=_today(),
  141	            )
  142	        )
  143	    setattr(tree.archived_cross_cutting[0], f.name, value)
  144	```
  145
  146	```python
  147	if type_ is ArchivedCrossCutting:
  148	    return getattr(tree.archived_cross_cutting[0], f.name)
  149	```
  150
  151	- [ ] **Step 2: Add failing schema test**
  152
  153	Create `tools/tasktool/tests/test_schema_gen.py` if absent:
  154
  155	```python
  156	from tasktool.schema_gen import build_schema
  157
  158
  159	def test_schema_includes_archived_cross_cutting():
  160	    schema = build_schema()
  161	    properties = schema["properties"]
  162	    assert "archived_cross_cutting" in properties
  163	    archived = properties["archived_cross_cutting"]["items"]
  164	    assert archived["required"] == ["id", "title", "archived_path", "archived_date"]
  165	    assert archived["properties"]["id"]["pattern"] == r"^X\d+$"
  166	```
  167
  168	- [ ] **Step 3: Run tests to verify failure**
  169
  170	Run:
  171
  172	```sh
  173	python3 -m pytest tools/tasktool/tests/test_migrate.py tools/tasktool/tests/test_schema_gen.py -q
  174	```
  175
  176	Expected: failures for missing `ArchivedCrossCutting`, missing project field, and missing schema property.
  177
  178	- [ ] **Step 4: Implement model and serialization**
  179
  180	In `tools/tasktool/model.py`, add:
  181
  182	```python
  183	@dataclass(slots=True)
  184	class ArchivedCrossCutting:
  185	    id: str
  186	    title: str
  187	    archived_path: str
  188	    archived_date: str
  189	```
  190
  191	Add the new field to `Project`:
  192
  193	```python
  194	archived_cross_cutting: list[ArchivedCrossCutting] = field(default_factory=list)
  195	```
  196
  197	In `tools/tasktool/serialize.py`, import the new dataclass:
  198
  199	```python
  200	Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, ArchivedCrossCutting, BlockedOn,
  201	```
  202
  203	Add loader helper:
  204
  205	```python
  206	def _arch_cross(ad):
  207	    return ArchivedCrossCutting(
  208	        id=ad["id"], title=ad["title"],
  209	        archived_path=ad["archived_path"], archived_date=ad["archived_date"],
  210	    )
  211	```
  212
  213	Add the field when constructing `Project`:
  214
  215	```python
  216	archived_cross_cutting=[_arch_cross(a) for a in d.get("archived_cross_cutting", [])],
  217	```
  218
  219	Add a legacy-load test in a serialization-focused test file:
  220
  221	```python
  222	def test_legacy_tasklist_without_archived_cross_cutting_loads():
  223	    project = loads_project(
  224	        json.dumps(
  225	            {
  226	                "project": "demo",
  227	                "schema_version": 1,
  228	                "phases": [],
  229	                "cross_cutting": [],
  230	                "archived_phases": [],
  231	            }
  232	        )
  233	    )
  234
  235	    assert project.archived_cross_cutting == []
  236	```
  237
  238	- [ ] **Step 5: Implement schema and migration**
  239
  240	In `tools/tasktool/schema_gen.py`, create a dedicated archived X schema or reuse the archived pointer shape with an X pattern:
  241
  242	```python
  243	archived_cross = {
  244	    "type": "object",
  245	    "required": ["id", "title", "archived_path", "archived_date"],
  246	    "properties": {
  247	        "id": {"type": "string", "pattern": r"^X\d+$"},
  248	        "title": {"type": "string"},
  249	        "archived_path": {"type": "string"},
  250	        "archived_date": date_str,
  251	    },
  252	    "additionalProperties": False,
  253	}
  254	```
  255
  256	Add to top-level properties:
  257
  258	```python
  259	"archived_cross_cutting": {"type": "array", "items": archived_cross},
  260	```
  261
  262	In `tools/tasktool/migrate.py`, update imports:
  263
  264	```python
  265	from tasktool.model import ArchivedCrossCutting, ArchivedPhase, CrossCutting, Phase, Project, Slice, Task
  266	```
  267
  268	Update:
  269
  270	```python
  271	_PROJECT_COLLECTIONS = ("phases", "cross_cutting", "archived_phases", "archived_cross_cutting")
  272	```
  273
  274	Add to `walker_field_coverage`:
  275
  276	```python
  277	"ArchivedCrossCutting": {field.name for field in fields(ArchivedCrossCutting)},
  278	```
  279
  280	Add `_diff_collection` and `_apply_collection` calls for `archived_cross_cutting`, using `ArchivedCrossCutting`.
  281
  282	In `_diff_project`, mirror the existing `archived_phases` block:
  283
  284	```python
  285	    _diff_collection(
  286	        local_rows=local.archived_cross_cutting,
  287	        authoritative_rows=authoritative.archived_cross_cutting,
  288	        id_prefix="",
  289	        row_dataclass=ArchivedCrossCutting,
  290	        nested=[],
  291	        deltas=deltas,
  292	        conflicts=conflicts,
  293	    )
  294	```
  295
  296	In `_apply_local`, mirror the existing `archived_phases` block:
  297
  298	```python
  299	    _apply_collection(
  300	        authoritative_rows=merged.archived_cross_cutting,
  301	        local_rows=local.archived_cross_cutting,
  302	        deltas=deltas,
  303	        id_prefix="",
  304	        nested=[],
  305	    )
  306	```
  307
  308	- [ ] **Step 6: Run focused tests**
  309
  310	Run:
  311
  312	```sh
  313	python3 -m pytest tools/tasktool/tests/test_migrate.py tools/tasktool/tests/test_schema_gen.py -q
  314	```
  315
  316	Expected: pass.
  317
  318	## Task 2: Validation and Rendering
  319
  320	**Files:**
  321	- Modify: `tools/tasktool/validate.py`
  322	- Modify: `tools/tasktool/render.py`
  323	- Modify: `tools/tasktool/tests/test_validate.py`
  324	- Modify: `tools/tasktool/tests/test_render.py`
  325
  326	- [ ] **Step 1: Add failing validation tests**
  327
  328	Add imports to `tools/tasktool/tests/test_validate.py`:
  329
  330	```python
  331	from tasktool.model import ArchivedCrossCutting
  332	```
  333
  334	Add tests:
  335
  336	```python
  337	def test_validate_rejects_duplicate_archived_cross_ids():
  338	    p = Project(project="demo")
  339	    p.archived_cross_cutting.extend([
  340	        ArchivedCrossCutting(id="X1", title="one", archived_path="docs/archived-tasks/X1-one.md", archived_date="2026-05-21"),
  341	        ArchivedCrossCutting(id="X1", title="two", archived_path="docs/archived-tasks/X1-two.md", archived_date="2026-05-21"),
  342	    ])
  343
  344	    with pytest.raises(ValidationError, match="duplicate archived cross id X1"):
  345	        validate_project(p)
  346
  347
  348	def test_validate_rejects_active_and_archived_cross_id_collision():
  349	    p = Project(project="demo")
  350	    p.cross_cutting.append(CrossCutting(id="X1", title="active", created="2026-05-21"))
  351	    p.archived_cross_cutting.append(
  352	        ArchivedCrossCutting(id="X1", title="archived", archived_path="docs/archived-tasks/X1-archived.md", archived_date="2026-05-21")
  353	    )
  354
  355	    with pytest.raises(ValidationError, match="X1 appears in both active and archived cross-cutting"):
  356	        validate_project(p)
  357
  358
  359	def test_validate_rejects_malformed_archived_cross_date_and_path():
  360	    p = Project(project="demo")
  361	    p.archived_cross_cutting.append(
  362	        ArchivedCrossCutting(id="X1", title="archived", archived_path="", archived_date="20260521")
  363	    )
  364
  365	    with pytest.raises(ValidationError):
  366	        validate_project(p)
  367	```
  368
  369	- [ ] **Step 2: Add failing render test**
  370
  371	In `tools/tasktool/tests/test_render.py`, import `ArchivedCrossCutting` and add:
  372
  373	```python
  374	def test_render_shows_archived_cross_section():
  375	    p = Project(project="demo")
  376	    p.cross_cutting.append(CrossCutting(id="X1", title="active cross", created="2026-05-21"))
  377	    p.archived_cross_cutting.append(
  378	        ArchivedCrossCutting(
  379	            id="X2",
  380	            title="archived cross",
  381	            archived_path="docs/archived-tasks/X2-archived-cross.md",
  382	            archived_date="2026-05-21",
  383	        )
  384	    )
  385
  386	    out = render_project(p)
  387
  388	    assert "## Cross-cutting (`X*`)" in out
  389	    assert "## Archived cross-cutting (`X*`)" in out
  390	    active_section, archived_section = out.split("## Archived cross-cutting (`X*`)", 1)
  391	    assert "**X1**" in active_section
  392	    assert "**X2**" not in active_section
  393	    assert "**X2**" in archived_section
  394	    assert "docs/archived-tasks/X2-archived-cross.md" in archived_section
  395	```
  396
  397	- [ ] **Step 3: Run tests to verify failure**
  398
  399	Run:
  400
  401	```sh
  402	python3 -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_render.py -q
  403	```
  404
  405	Expected: failures until validation/rendering know the new field.
  406
  407	- [ ] **Step 4: Implement validation**
  408
  409	In `tools/tasktool/validate.py`, import `ArchivedCrossCutting` and add:
  410
  411	```python
  412	def _check_archived_cross(c: ArchivedCrossCutting, scope: str) -> None:
  413	    _check_id(c.id, _CROSS_RE, scope)
  414	    _require(bool(c.title.strip()), f"{scope}: archived cross title is required")
  415	    _require(bool(c.archived_path.strip()), f"{scope}: archived_path is required")
  416	    _check_date(c.archived_date, scope, "archived_date")
  417	```
  418
  419	Before using those helpers, verify the current signatures in `validate.py`:
  420
  421	```sh
  422	rg -n "def _check_date|_CROSS_RE" tools/tasktool/validate.py
  423	```
  424
  425	Expected: `_CROSS_RE` exists and `_check_date` accepts `(value, scope, field)`.
  426
  427	In `validate_project`, after active cross validation:
  428
  429	```python
  430	seen_archived_cross: set[str] = set()
  431	for c in p.archived_cross_cutting:
  432	    _require(c.id not in seen_archived_cross, f"X*: duplicate archived cross id {c.id}")
  433	    _require(c.id not in seen_cross, f"{c.id} appears in both active and archived cross-cutting")
  434	    seen_archived_cross.add(c.id)
  435	    _check_archived_cross(c, c.id)
  436	```
  437
  438	In `collect_known_ids`, add:
  439
  440	```python
  441	for x in getattr(p, "archived_cross_cutting", []) or []:
  442	    ids.add(x.id if hasattr(x, "id") else x["id"])
  443	```
  444
  445	- [ ] **Step 5: Implement rendering**
  446
  447	In `tools/tasktool/render.py`, after archived phases:
  448
  449	```python
  450	    if getattr(p, "archived_cross_cutting", None):
  451	        lines += ["## Archived cross-cutting (`X*`)", ""]
  452	        for a in p.archived_cross_cutting:
  453	            lines.append(
  454	                f"- **{a.id}** — {a.title} → [`{a.archived_path}`]({a.archived_path}) ({a.archived_date})"
  455	            )
  456	        lines.append("")
  457	```
  458
  459	- [ ] **Step 6: Run focused tests**
  460
  461	Run:
  462
  463	```sh
  464	python3 -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_render.py -q
  465	```
  466
  467	Expected: pass.
  468
  469	## Task 3: Archive Commands and CLI
  470
  471	**Files:**
  472	- Modify: `tools/tasktool/commands.py`
  473	- Modify: `tools/tasktool/cli.py`
  474	- Modify: `tools/tasktool/tests/test_commands.py`
  475	- Modify: `tools/tasktool/tests/test_cli_integration.py`
  476
  477	- [ ] **Step 1: Add failing command tests**
  478
  479	In `tools/tasktool/tests/test_commands.py`, import `ValidationError` if needed:
  480
  481	```python
  482	from tasktool.validate import ValidationError
  483	```
  484
  485	Add tests:
  486
  487	```python
  488	class CrossArchiveTests(unittest.TestCase):
  489	    def setUp(self):
  490	        self.t = _Tmp()
  491	        commands.cmd_init(repo_root=self.t.root, project="demo")
  492
  493	    def tearDown(self):
  494	        self.t.cleanup()
  495
  496	    def test_close_cross_archives_by_default(self):
  497	        commands.cmd_create_cross(repo_root=self.t.root, title="archive me")
  498
  499	        commands.cmd_close(repo_root=self.t.root, id="X1")
  500
  501	        p = load_project(self.t.root / "docs/tasklist.json")
  502	        self.assertEqual(p.cross_cutting, [])
  503	        self.assertEqual(p.archived_cross_cutting[0].id, "X1")
  504	        archive_path = self.t.root / p.archived_cross_cutting[0].archived_path
  505	        self.assertTrue(archive_path.exists())
  506	        self.assertIn('"id": "X1"', archive_path.read_text(encoding="utf-8"))
  507
  508	    def test_close_cross_no_archive_keeps_visible(self):
  509	        commands.cmd_create_cross(repo_root=self.t.root, title="keep visible")
  510
  511	        commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)
  512
  513	        p = load_project(self.t.root / "docs/tasklist.json")
  514	        self.assertEqual(p.cross_cutting[0].status, Status.DONE)
  515	        self.assertEqual(p.archived_cross_cutting, [])
  516
  517	    def test_archive_cross_archives_done_visible_item(self):
  518	        commands.cmd_create_cross(repo_root=self.t.root, title="later")
  519	        commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)
  520
  521	        commands.cmd_archive_cross(repo_root=self.t.root, id="X1")
  522
  523	        p = load_project(self.t.root / "docs/tasklist.json")
  524	        self.assertEqual(p.cross_cutting, [])
  525	        self.assertEqual(p.archived_cross_cutting[0].id, "X1")
  526
  527	    def test_archive_cross_rejects_ready_item(self):
  528	        commands.cmd_create_cross(repo_root=self.t.root, title="not done")
  529
  530	        with self.assertRaisesRegex(commands.CommandError, "must be done before archive"):
  531	            commands.cmd_archive_cross(repo_root=self.t.root, id="X1")
  532
  533	    def test_close_no_archive_rejects_non_cross_items(self):
  534	        commands.cmd_create_phase(repo_root=self.t.root, title="phase")
  535
  536	        with self.assertRaisesRegex(commands.CommandError, "--no-archive is only valid for cross-cutting items"):
  537	            commands.cmd_close(repo_root=self.t.root, id="P1", no_archive=True, skip_review_gate=True)
  538
  539	    def test_archive_cross_preserves_full_json(self):
  540	        commands.cmd_create_cross(repo_root=self.t.root, title="full data")
  541	        commands.cmd_close(
  542	            repo_root=self.t.root,
  543	            id="X1",
  544	            no_archive=True,
  545	            refs=["docs/specs/example.md"],
  546	            note="important note",
  547	        )
  548
  549	        commands.cmd_archive_cross(repo_root=self.t.root, id="X1")
  550
  551	        p = load_project(self.t.root / "docs/tasklist.json")
  552	        text = (self.t.root / p.archived_cross_cutting[0].archived_path).read_text(encoding="utf-8")
  553	        self.assertIn('"id": "X1"', text)
  554	        self.assertIn('"refs": [', text)
  555	        self.assertIn('"docs/specs/example.md"', text)
  556	        self.assertIn('"notes": "important note"', text)
  557
  558	    def test_close_archived_cross_reports_archived_hint(self):
  559	        commands.cmd_create_cross(repo_root=self.t.root, title="already archived")
  560	        commands.cmd_close(repo_root=self.t.root, id="X1")
  561
  562	        with self.assertRaisesRegex(commands.CommandError, "may already be archived"):
  563	            commands.cmd_close(repo_root=self.t.root, id="X1")
  564
  565	    def test_brief_archived_cross_is_not_active_surface(self):
  566	        from tasktool.brief import brief
  567
  568	        commands.cmd_create_cross(repo_root=self.t.root, title="brief archived")
  569	        commands.cmd_close(repo_root=self.t.root, id="X1")
  570	        p = load_project(self.t.root / "docs/tasklist.json")
  571
  572	        with self.assertRaisesRegex(ValueError, "X1: not found"):
  573	            brief(p, "X1")
  574
  575	    def test_archive_cross_atomicity_no_orphan_file_on_validation_failure(self):
  576	        commands.cmd_create_cross(repo_root=self.t.root, title="atomic")
  577	        commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)
  578
  579	        with patch("tasktool.commands.validate_project", side_effect=ValidationError("forced")):
  580	            with self.assertRaises(ValidationError):
  581	                commands.cmd_archive_cross(repo_root=self.t.root, id="X1")
  582
  583	        self.assertFalse((self.t.root / "docs/archived-tasks/X1-atomic.md").exists())
  584	        p = load_project(self.t.root / "docs/tasklist.json")
  585	        self.assertEqual(p.cross_cutting[0].id, "X1")
  586
  587	    def test_archive_cross_does_not_reemit_done_notification(self):
  588	        commands.cmd_create_cross(repo_root=self.t.root, title="notify once")
  589	        log = self.t.root / "notify.jsonl"
  590	        with patch.dict(
  591	            os.environ,
  592	            {"SUPERSTAR_NOTIFY_DISABLE": "0", "SUPERSTAR_NOTIFY_DRY_RUN": "1", "SUPERSTAR_NOTIFY_LOG": str(log)},
  593	        ):
  594	            commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)
  595	            commands.cmd_archive_cross(repo_root=self.t.root, id="X1")
  596
  597	        events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
  598	        done_events = [event for event in events if event["id"] == "X1" and event["status"] == "done"]
  599	        self.assertEqual(len(done_events), 1)
  600	```

[truncated: 357 additional lines]

## Context Previews

### docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md

    1	# X15 - Archive closed cross-cutting items
    2
    3	**Status:** spec
    4	**Tasktool ID:** X15 (cross-cutting)
    5	**Date:** 2026-05-21
    6
    7	## Problem
    8
    9	Cross-cutting items (`X*`) are top-level work items that are not contained by a phase. They are useful for small workflow fixes, tool hardening, or opportunistic cleanup that does not deserve a full phase. Once completed, however, closed X-items remain in the active `cross_cutting` array and continue to appear in rendered tasklists. Over time, those completed rows pollute the working view even though they no longer require action.
   10
   11	Phase work already has a lossless archive path: `tasktool archive-phase` removes the phase from active `docs/tasklist.json`, writes a full archive file under `docs/archived-tasks/`, and leaves compact pointer metadata in the active tasklist. Cross-cutting work needs the same “move it out of the active view without losing evidence” treatment, scaled to a single X-item instead of a phase containing slices.
   12
   13	## Goals
   14
   15	1. Archive completed cross-cutting items by default when they are closed.
   16	2. Preserve archived X-item data losslessly in a per-item archive file.
   17	3. Keep an explicit opt-out for the rare case where a closed X-item should remain visible in the active tasklist.
   18	4. Provide a manual command to archive a done-but-visible X-item later.
   19
   20	## Non-goals
   21
   22	- No three-day auto-archive policy in this slice.
   23	- No standalone slice archival. Slices remain archived through their parent phase.
   24	- No compaction or lossy summary format for archived X-items.
   25	- No change to phase archival semantics.
   26	- No `unarchive-cross` command. The archive file embeds full JSON so a future unarchive command can be implemented, but this slice does not ship one.
   27	- No schema version bump. `archived_cross_cutting` is backwards-compatible and defaults to `[]` for legacy tasklists.
   28
   29	## Design
   30
   31	### 1. Archive model
   32
   33	Add a new top-level archive pointer list to `docs/tasklist.json`:
   34
   35	```json
   36	"archived_cross_cutting": [
   37	  {
   38	    "archived_date": "2026-05-21",
   39	    "archived_path": "docs/archived-tasks/X15-archive-closed-cross-cutting-items.md",
   40	    "id": "X15",
   41	    "title": "Archive closed cross-cutting items"
   42	  }
   43	]
   44	```
   45
   46	The active `cross_cutting` array remains the source of truth for visible, active X-items. Once an X-item is archived, it is removed from `cross_cutting` and represented in `archived_cross_cutting` by pointer metadata only.
   47
   48	Each archived X-item gets its own markdown archive file under `docs/archived-tasks/`:
   49
   50	```text
   51	docs/archived-tasks/X15-archive-closed-cross-cutting-items.md
   52	```
   53
   54	The archive file stores full canonical JSON for the X-item, including title, created date, started date, status, closed date, refs, and notes. The operation is lossless relocation, not data compaction. The mental model is the same as phase archives: phases are folders in the archive box; X-items are loose papers in the same box.
   55
   56	### 2. Default close behavior
   57
   58	`tasktool close X15` closes and archives the cross-cutting item in one operation:
   59
   60	1. Resolve `X15` from active `cross_cutting`.
   61	2. Set `status` to `done`.
   62	3. Stamp `closed` if it was not already set.
   63	4. Apply any supplied refs or close note using the existing close semantics.
   64	5. Build the archive markdown content in memory, including full X-item JSON.
   65	6. Remove the X-item from active `cross_cutting` in memory.
   66	7. Append the pointer row to `archived_cross_cutting` in memory.
   67	8. Validate the mutated project before any archive file is written.
   68	9. Write `docs/archived-tasks/X15-<slug>.md`.
   69	10. Save `docs/tasklist.json`.
   70	11. Stage both `docs/tasklist.json` and the new archive file.
   71	12. Emit the existing done notification exactly once.
   72
   73	Cross-cutting close remains ungated by external review, matching today’s behavior.
   74
   75	### 3. Close opt-out
   76
   77	Add `--no-archive` to `tasktool close` for cross-cutting items:
   78
   79	```sh
   80	tools/tasktool/tasktool close X15 --no-archive
   81	```
   82
   83	For X-items only, `--no-archive` means “close this item but leave it visible in active `cross_cutting`.” It is an opt-out of immediate archiving, not an instruction to keep the row visible forever. The user can archive the row later with `archive-cross`.
   84
   85	For slices and phases, supplying `--no-archive` fails with `--no-archive is only valid for cross-cutting items`. The flag exists to control X-item close behavior only.
   86
   87	### 4. Manual archive command
   88
   89	Add:
   90
   91	```sh
   92	tools/tasktool/tasktool archive-cross X15
   93	```
   94
   95	This archives a closed X-item that still exists in active `cross_cutting`, typically because it was closed with `--no-archive` or predates this feature.
   96
   97	Rules:
   98
   99	- `archive-cross` accepts only cross-cutting IDs.
  100	- The X-item must exist in active `cross_cutting`.
  101	- The X-item must be `done`.
  102	- If an archive pointer already exists for that ID, fail rather than overwrite.
  103	- If the archive file path already exists, fail rather than overwrite.
  104	- On success, use the same atomic ordering as default close: build archive content in memory, mutate the project in memory, validate, write the archive file, save `docs/tasklist.json`, and stage both touched files.
  105	- `archive-cross` does not re-emit a done notification, because it archives an item that is already done. The status transition happened at close time.
  106
  107	There is no bulk auto-cleanup command in this slice.
  108
  109	### 5. Archive file format
  110
  111	Use the phase archive style but scaled to one cross-cutting item:
  112
  113	````md
  114	# X15 - Archive closed cross-cutting items
  115
  116	status: done
  117	created: 2026-05-21
  118	closed: 2026-05-21
  119
  120	## References
  121
  122	- docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md
  123
  124	## Notes
  125
  126	<notes, if present>
  127
  128	## Full cross-cutting JSON (for tasktool unarchive)
  129
  130	```json
  131	{
  132	  "closed": "2026-05-21",
  133	  "created": "2026-05-21",
  134	  "id": "X15",
  135	  "notes": "",
  136	  "refs": [],
  137	  "started": null,
  138	  "status": "done",
  139	  "title": "Archive closed cross-cutting items"
  140	}
  141	```
  142	````
  143
  144	The exact JSON should be emitted through the existing canonical serialization path or a small helper that shares the same ordering rules. The archive file is the durable evidence store.
  145
  146	### 6. Rendering and listing
  147
  148	`tasktool render` should keep showing active `cross_cutting` as it does today, but archived X-items should no longer appear in that active section.
  149
  150	Add an archived X section after archived phases when `archived_cross_cutting` is non-empty:
  151
  152	```md
  153	## Archived cross-cutting (`X*`)
  154
  155	- **X15** - Archive closed cross-cutting items -> [`docs/archived-tasks/X15-archive-closed-cross-cutting-items.md`](docs/archived-tasks/X15-archive-closed-cross-cutting-items.md) (2026-05-21)
  156	```
  157
  158	Archive pointers are append-only in archive time order, matching `archived_phases`.
  159
  160	`tasktool list --open` naturally excludes archived X-items because they are no longer in `cross_cutting`. `tasktool list --kind cross` should continue to list active X-items only. A separate archive listing flag is not required for this slice; `render` is enough for human visibility.
  161
  162	`tasktool brief X15` after archival should fail with the same active-tasklist-not-found semantics as archived phases rather than loading the archive file. The archive file is evidence, not part of the active workflow surface.
  163
  164	## Component boundaries
  165
  166	- `tools/tasktool/model.py` owns the new `ArchivedCrossCutting` dataclass and `Project.archived_cross_cutting` field.
  167	- `tools/tasktool/serialize.py` owns backwards-compatible loading when older tasklists omit `archived_cross_cutting`.
  168	- `tools/tasktool/validate.py` owns ID uniqueness and date/path validation for archived X pointers.
  169	- `tools/tasktool/migrate.py` owns migration/merge semantics for the new top-level collection so authoritative-checkout reconciliation preserves archived X pointers.
  170	- `tools/tasktool/schema_gen.py` owns JSON schema coverage for `archived_cross_cutting`.
  171	- `tools/tasktool/commands.py` owns archive behavior, including `cmd_archive_cross`, close-with-default-archive, and archive file writing.
  172	- `tools/tasktool/cli.py` owns `close --no-archive` and the new `archive-cross` subcommand.
  173	- `tools/tasktool/render.py` owns displaying archived X pointers.
  174	- `tools/tasktool/brief.py` keeps archived X-items outside the active brief surface.
  175	- `tools/tasktool/tests/` owns behavioral coverage.
  176	- `skills/tasklist-discipline/SKILL.md` owns user-facing workflow guidance for closing and archiving X-items.
  177
  178	## Error handling
  179
  180	- `tasktool close X15` where `X15` is already archived: fail with `cross-cutting X15 not found in active tasklist; it may already be archived`. Implement this by checking `archived_cross_cutting` in the close/archive-cross wrapper before falling back to the generic not-found error.
  181	- `tasktool close X15 --no-archive` succeeds and leaves the item in active `cross_cutting`.
  182	- `tasktool close P4.S1 --no-archive` fails with `--no-archive is only valid for cross-cutting items`.
  183	- `tasktool archive-cross X15` where `X15` is not `done`: fail with `cross-cutting X15 must be done before archive; run tasktool close X15 first`.
  184	- `tasktool archive-cross X15` where the pointer already exists: fail with `cross-cutting X15 is already archived`.
  185	- Archive path collision: fail before mutating `docs/tasklist.json`.
  186	- Validation should reject duplicate archived X IDs, archived X IDs that also appear in active `cross_cutting`, invalid archived dates, and empty archive paths.
  187
  188	## Testing
  189
  190	Add focused tests under `tools/tasktool/tests/`:
  191
  192	1. `test_close_cross_archives_by_default` - create an X-item, close it, assert it is removed from `cross_cutting`, added to `archived_cross_cutting`, and a markdown archive file exists.
  193	2. `test_close_cross_no_archive_keeps_visible` - close with `--no-archive`, assert the item remains in active `cross_cutting` with `status: done` and no archive pointer/file is created.
  194	3. `test_archive_cross_archives_done_visible_item` - close with `--no-archive`, then run `archive-cross`, assert the item moves to the archive pointer list and the file is written.
  195	4. `test_archive_cross_rejects_ready_item` - `archive-cross` on a ready X-item fails with the done-before-archive message.
  196	5. `test_close_no_archive_rejects_non_cross_items` - supplying `--no-archive` when closing a slice or phase fails clearly.
  197	6. `test_validate_rejects_duplicate_archived_cross_ids` - duplicate archive pointers fail validation.
  198	7. `test_validate_rejects_active_and_archived_cross_id_collision` - the same `X*` ID cannot appear in both active and archived lists.
  199	8. `test_render_shows_archived_cross_section` - render includes active X-items separately from archived X pointers.
  200	9. `test_archive_cross_preserves_full_json` - archive markdown contains the full X-item JSON, including refs and notes.

[truncated: 34 additional lines]
### docs/tasklist.json

    1	{
    2	  "archived_cross_cutting": [],
    3	  "archived_phases": [
    4	    {
    5	      "archived_date": "2026-05-18",
    6	      "archived_path": "docs/archived-tasks/P2-tasktool-json-backed-task-management-cli.md",
    7	      "id": "P2",
    8	      "title": "tasktool: JSON-backed task management CLI"
    9	    },
   10	    {
   11	      "archived_date": "2026-05-19",
   12	      "archived_path": "docs/archived-tasks/P4-tasktool-coordination-and-lifecycle-auth.md",
   13	      "id": "P4",
   14	      "title": "Tasktool coordination and lifecycle authority"
   15	    },
   16	    {
   17	      "archived_date": "2026-05-19",
   18	      "archived_path": "docs/archived-tasks/P3-phase-planning-workflow.md",
   19	      "id": "P3",
   20	      "title": "Phase planning workflow"
   21	    }
   22	  ],
   23	  "cross_cutting": [
   24	    {
   25	      "closed": "2026-05-18",
   26	      "created": "2026-05-18",
   27	      "id": "X1",
   28	      "notes": "Changed external-review default prompt transport from argv to stdin so the bundled Codex reviewer-agent receives prompts via codex exec '-' and avoids argv length failures.",
   29	      "refs": [],
   30	      "started": null,
   31	      "status": "done",
   32	      "title": "Default external-review prompt transport to stdin"
   33	    },
   34	    {
   35	      "closed": "2026-05-18",
   36	      "created": "2026-05-18",
   37	      "id": "X2",
   38	      "notes": "Added repo-local tools/tasktool/tasktool launcher, updated tasklist/project-setup docs to prefer it, and taught the pre-commit hook to use the repo-local launcher before falling back to a global tasktool shim.",
   39	      "refs": [],
   40	      "started": null,
   41	      "status": "done",
   42	      "title": "Add repo-local tasktool launcher"
   43	    },
   44	    {
   45	      "closed": "2026-05-19",
   46	      "created": "2026-05-19",
   47	      "id": "X3",
   48	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. External-review verdict parsing now accepts markdown-emphasized Overall Verdict headings such as **5. Overall Verdict** followed by ready/revise text.",
   49	      "refs": [
   50	        "skills/external-review/scripts/external-reviewer.py",
   51	        "skills/external-review/tests/test_heading_style_verdict.py"
   52	      ],
   53	      "started": null,
   54	      "status": "done",
   55	      "title": "Spot fix: parse bold external-review verdict headings"
   56	    },
   57	    {
   58	      "closed": "2026-05-19",
   59	      "created": "2026-05-19",
   60	      "id": "X4",
   61	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. Legacy markdown import now accepts fully-qualified slice IDs and additional cross-cutting forms including tagged done items, blocked cross rows coerced to ready, and archived cross rows treated as done.",
   62	      "refs": [
   63	        "tools/tasktool/importer.py"
   64	      ],
   65	      "started": null,
   66	      "status": "done",
   67	      "title": "Spot fix: broaden legacy tasklist importer compatibility"
   68	    },
   69	    {
   70	      "closed": "2026-05-19",
   71	      "created": "2026-05-19",
   72	      "id": "X5",
   73	      "notes": "User-requested hook update completed outside the normal workflow for speed. Adds Stop/SubagentStop finished-agent notifications, milestone message derivation from final agent text/transcript payloads, Hypr TTS config reuse with OPENAI_API_KEY fallback, and non-TTS ding fallbacks.\nSuperseded by X8: final-text milestone parsing was removed; agent hooks now emit generic dings and semantic spoken notifications come from tasktool status changes.",
   74	      "refs": [
   75	        "hooks/agent-finished",
   76	        "hooks/hooks.json",
   77	        "hooks/hooks-cursor.json",
   78	        "tests/claude-code/test-agent-finished-hook.sh"
   79	      ],
   80	      "started": null,
   81	      "status": "done",
   82	      "title": "Add finished-agent notification hook"
   83	    },
   84	    {
   85	      "closed": "2026-05-19",
   86	      "created": "2026-05-19",
   87	      "id": "X6",
   88	      "notes": "Codex startup skips Stop/SubagentStop notification hooks when hooks.json uses async=true; fix should preserve finished-agent notification behavior while avoiding unsupported async hook registration in Codex.\nSet finished-agent Stop/SubagentStop hook registrations to async=false for Codex compatibility. The hook now backgrounds real notification playback internally so synchronous hook registration returns quickly while dry-run tests remain foreground and deterministic.",
   89	      "refs": [
   90	        "hooks/hooks.json",
   91	        "hooks/agent-finished",
   92	        "tests/claude-code/test-hook-config.sh",
   93	        "tests/claude-code/test-agent-finished-hook.sh"
   94	      ],
   95	      "started": null,
   96	      "status": "done",
   97	      "title": "Fix Codex finished-agent hook compatibility"
   98	    },
   99	    {
  100	      "closed": "2026-05-19",
  101	      "created": "2026-05-19",
  102	      "id": "X7",
  103	      "notes": "Codex reported superstar/6.0.0 because the installable local marketplace payload under plugins/superstar still declared version 6.0.0 and the version bump audit did not track that embedded manifest.\n\nBumped the embedded Codex plugin payload manifest to 6.0.1 and added it to the version bump check. Reinstalled superstar@superstar-dev, then rebuilt the 6.0.1 runtime cache as a materialized copy of this checkout with .agents excluded so Codex sees the full skills/hooks tree while codex plugin list still reports installed/enabled. Final probe shows cache version 6.0.1, skills/hooks present, and no async-hook warning.",
  104	      "refs": [
  105	        ".version-bump.json",
  106	        "plugins/superstar/.codex-plugin/plugin.json",
  107	        ".agents/plugins/marketplace.json",
  108	        "tests/codex-plugin-sync/test-version-drift.sh",
  109	        "tests/codex-plugin-sync/test-local-marketplace.sh"
  110	      ],
  111	      "started": null,
  112	      "status": "done",
  113	      "title": "Fix Superstar Codex plugin payload version drift"
  114	    },
  115	    {
  116	      "closed": "2026-05-19",
  117	      "created": "2026-05-19",
  118	      "id": "X8",
  119	      "notes": "Move semantic spoken notifications to tasktool status transitions for ready/in_progress/blocked/done. Keep agent Stop/SubagentStop hooks as generic completion dings only, with different sound styles for Claude and Codex.\nAgent Stop/SubagentStop hooks now emit generic harness-specific dings only. Semantic spoken notifications moved to tasktool status events for ready, in_progress, blocked, and done, including create, set, close, block, unblock, and archive-phase paths.",
  120	      "refs": [
  121	        "hooks/agent-finished",
  122	        "tools/tasktool/notify.py",
  123	        "tools/tasktool/commands.py",
  124	        "tools/tasktool/tests/test_notify.py",
  125	        "tools/tasktool/tests/test_commands.py",
  126	        "tools/tasktool/tests/conftest.py",
  127	        "tests/claude-code/test-agent-finished-hook.sh"
  128	      ],
  129	      "started": null,
  130	      "status": "done",
  131	      "title": "Move semantic notifications from agent hooks to tasktool status changes"
  132	    },
  133	    {
  134	      "closed": "2026-05-19",
  135	      "created": "2026-05-19",
  136	      "id": "X9",
  137	      "notes": "Rapid tasktool status changes currently spawn independent notifier processes, causing overlapping TTS/audio. Add a single-audio queue with at most three queued tasktool events; overflow should collapse to a single 'multiple other events' summary and drop further items.\nAdded a file-backed notification queue shared by agent dings and tasktool TTS. Only one worker drains audio at a time. Queue capacity is three pending events; overflow keeps the first two pending items and replaces the rest with a single 'Multiple other events' summary, dropping further burst items while the summary remains queued.",
  138	      "refs": [
  139	        "tools/tasktool/notify.py",
  140	        "tools/tasktool/tests/test_notify.py"
  141	      ],
  142	      "started": null,
  143	      "status": "done",
  144	      "title": "Coalesce bursty tasktool audio notifications"
  145	    },
  146	    {
  147	      "closed": "2026-05-20",
  148	      "created": "2026-05-20",
  149	      "id": "X10",
  150	      "notes": "",
  151	      "refs": [
  152	        "docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md",
  153	        "docs/reviewer/x10-verdict-parser-claude-formatting-design-spec",
  154	        "docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md"
  155	      ],
  156	      "started": null,
  157	      "status": "done",
  158	      "title": "Harden external-review verdict parser and prompt against Claude formatting variants"
  159	    },
  160	    {
  161	      "closed": "2026-05-20",
  162	      "created": "2026-05-20",
  163	      "id": "X11",
  164	      "notes": "",
  165	      "refs": [
  166	        "docs/specs/2026-05-20-X11-global-external-reviewer-bridge-design.md",
  167	        "docs/reviewer/x11-global-external-reviewer-bridge-design-spec",
  168	        "docs/plans/2026-05-20-X11-global-external-reviewer-bridge.md",
  169	        "docs/reviewer/x11-global-external-reviewer-bridge-plan",
  170	        "docs/handoffs/2026-05-20-X11-global-external-reviewer-bridge-prompt.md"
  171	      ],
  172	      "started": "2026-05-20",
  173	      "status": "done",
  174	      "title": "Make external-review bridge global"
  175	    },
  176	    {
  177	      "closed": "2026-05-20",
  178	      "created": "2026-05-20",
  179	      "id": "X12",
  180	      "notes": "",
  181	      "refs": [
  182	        "docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md",
  183	        "docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md"
  184	      ],
  185	      "started": "2026-05-20",
  186	      "status": "done",
  187	      "title": "tasktool: require authoritative-checkout routing for mutations"
  188	    },
  189	    {
  190	      "closed": "2026-05-20",
  191	      "created": "2026-05-20",
  192	      "id": "X13",
  193	      "notes": "Fixed tasktool close --refs parsing so repeated flags and comma-separated refs both record every path. Verified with focused red/green regressions and full tasktool test suite.",
  194	      "refs": [
  195	        "tools/tasktool/cli.py",
  196	        "tools/tasktool/tests/test_cli_integration.py",
  197	        "tools/tasktool/tests/test_worktree_authority.py"
  198	      ],
  199	      "started": "2026-05-20",
  200	      "status": "done",

[truncated: 60 additional lines]

<!-- superstar-prompt:end -->