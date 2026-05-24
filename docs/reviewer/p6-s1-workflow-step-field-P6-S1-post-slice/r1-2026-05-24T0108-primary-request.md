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
docs/plans/2026-05-23-P6.S1-workflow-step-field.md

Additional context files:
- docs/specs/2026-05-23-P6-programmatic-workflow-enhancements-design.md
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

### docs/plans/2026-05-23-P6.S1-workflow-step-field.md

    1	# P6.S1 — `workflow_step` field + transient review block + read-only `infer-step`
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Add `workflow_step` as a first-class field on `Slice` and `Phase`, add a transient review block on `Slice` written by external-reviewer, and ship a read-only `tasktool infer-step` command — without changing any existing transition behaviour.
    6	
    7	**Architecture:** Strictly additive. Three new enums and four new fields in `tools/tasktool/model.py`; serialiser elides defaults; `tasktool set` gets new flags but stays back-compatible; `tasktool infer-step` is a pure read-only computation over current state; renderers suppress empty review blocks. External-reviewer gains three best-effort `tasktool set` calls when `--work-id` points at a slice. Six skill markdown files get small pointer paragraphs. No migration, no auto-advance, no transition gating.
    8	
    9	**Tech Stack:** Python 3.11+, `dataclasses`, `argparse`, `pytest`. Tasktool layout under `tools/tasktool/`. Skill markdown under `skills/`.
   10	
   11	---
   12	
   13	## Lifecycle pre-flight
   14	
   15	- [ ] **Step 0.1: Confirm working directory is the repo root**
   16	
   17	```bash
   18	test -f docs/tasklist.json -a -d tools/tasktool
   19	```
   20	
   21	Expected: exit 0.
   22	
   23	- [ ] **Step 0.2: Mark the slice started**
   24	
   25	```bash
   26	tools/tasktool/tasktool start P6.S1 --in-place
   27	```
   28	
   29	Expected stdout: `P6.S1`. (`--in-place` because the slice is small and editing in the main checkout is appropriate; the user has historically accepted in-place for tasktool internals.)
   30	
   31	- [ ] **Step 0.3: Ratify scheduling**
   32	
   33	The slice has no dependencies and no parallel-group peers. Confirm:
   34	
   35	```bash
   36	tools/tasktool/tasktool schedule P6
   37	```
   38	
   39	Expected: P6.S1 listed with `deps=-`, `group=-`. Then ratify:
   40	
   41	```bash
   42	tools/tasktool/tasktool ratify P6.S1
   43	```
   44	
   45	Expected: `P6.S1 ratified`.
   46	
   47	---
   48	
   49	## File structure (overview)
   50	
   51	| Path | Change |
   52	|---|---|
   53	| `tools/tasktool/model.py` | Add three enums; add four fields; bump `SCHEMA_VERSION` 1 → 2 |
   54	| `tools/tasktool/serialize.py` | Round-trip enums; elide review-block defaults |
   55	| `tools/tasktool/commands.py` | Relax `cmd_set`; add `cmd_infer_step`; extend `cmd_list` filter; extend `cmd_show` output |
   56	| `tools/tasktool/cli.py` | New args on `set`; new `infer-step` subparser; new `--workflow-step` filter on `list` |
   57	| `tools/tasktool/schema_gen.py` | Add new property entries to the inline phase/slice schemas; bump `SCHEMA_VERSION` const |
   58	| `tools/tasktool/render.py` | Workflow-step column; review-block conditional row |
   59	| `tools/tasktool/brief.py` | Workflow-step in heading; review-block conditional block |
   60	| `tools/tasktool/tests/test_model.py` | Round-trip with new fields |
   61	| `tools/tasktool/tests/test_serialize.py` | Default elision; enum round-trip |
   62	| `tools/tasktool/tests/test_commands.py` | `set` flag validation; `infer-step` (slice + phase + cross) |
   63	| `tools/tasktool/tests/test_render.py` | Review-block suppression |
   64	| `tools/tasktool/tests/test_brief.py` | Workflow-step heading |
   65	| `tools/tasktool/tests/test_schema_gen.py` | New enum types appear in schema |
   66	| `tools/tasktool/tests/test_cli_integration.py` | End-to-end `set` + `infer-step` invocations |
   67	| `tools/tasktool/tests/test_v1_compat.py` | Verify v1 tasklist loads with new fields at defaults; subsequent save emits schema_version: 2 |
   68	| `skills/external-review/scripts/external-reviewer.py` | Three best-effort `tasktool set` calls |
   69	| `skills/external-review/tests/test_workflow_block_calls.py` | Mocked tasktool calls for the three lifecycle moments |
   70	| `skills/tasklist-discipline/SKILL.md` | New `workflow_step` section |
   71	| `skills/brainstorming/SKILL.md` | One-liner pointer |
   72	| `skills/writing-plans/SKILL.md` | One-liner pointer |
   73	| `skills/subagent-driven-development/SKILL.md` | One-liner pointer |
   74	| `skills/executing-plans/SKILL.md` | One-liner pointer |
   75	| `skills/external-review/SKILL.md` | One-liner about the transient block |
   76	
   77	---
   78	
   79	## Task 1: Add enums and fields to the model
   80	
   81	**Files:**
   82	- Modify: `tools/tasktool/model.py`
   83	- Test: `tools/tasktool/tests/test_model.py`
   84	
   85	- [ ] **Step 1.1: Write the failing test**
   86	
   87	Append to `tools/tasktool/tests/test_model.py`:
   88	
   89	```python
   90	from tasktool.model import (
   91	    Slice, Phase, SCHEMA_VERSION,
   92	    SliceWorkflowStep, PhaseWorkflowStep, ReviewStage,
   93	)
   94	
   95	
   96	def test_schema_version_is_2():
   97	    assert SCHEMA_VERSION == 2
   98	
   99	
  100	def test_slice_has_workflow_step_default_none():
  101	    # Slice IDs in the model are short (`S1`); qualification happens at the CLI layer.
  102	    s = Slice(id="S1", title="t", created="2026-05-23")
  103	    assert s.workflow_step is None
  104	    assert s.review_active is False
  105	    assert s.review_stage is None
  106	
  107	
  108	def test_phase_has_workflow_step_default_none():
  109	    p = Phase(id="P6", title="t", created="2026-05-23")
  110	    assert p.workflow_step is None
  111	
  112	
  113	def test_slice_accepts_workflow_step_enum():
  114	    s = Slice(
  115	        id="S1", title="t", created="2026-05-23",
  116	        workflow_step=SliceWorkflowStep.PLAN,
  117	        review_active=True,
  118	        review_stage=ReviewStage.AWAITING_RESPONSE,
  119	    )
  120	    assert s.workflow_step is SliceWorkflowStep.PLAN
  121	    assert s.review_active is True
  122	    assert s.review_stage is ReviewStage.AWAITING_RESPONSE
  123	
  124	
  125	def test_phase_accepts_workflow_step_enum():
  126	    p = Phase(
  127	        id="P6", title="t", created="2026-05-23",
  128	        workflow_step=PhaseWorkflowStep.READY,
  129	    )
  130	    assert p.workflow_step is PhaseWorkflowStep.READY
  131	
  132	
  133	def test_slice_workflow_step_values():
  134	    assert {e.value for e in SliceWorkflowStep} == {"spec", "plan", "implement", "done"}
  135	
  136	
  137	def test_phase_workflow_step_values():
  138	    assert {e.value for e in PhaseWorkflowStep} == {"spec", "ready", "in_progress", "done"}
  139	
  140	
  141	def test_review_stage_values():
  142	    assert {e.value for e in ReviewStage} == {"awaiting_response", "applying_fixes", "passed"}
  143	```
  144	
  145	- [ ] **Step 1.2: Run test to verify it fails**
  146	
  147	```bash
  148	cd tools/tasktool && python -m pytest tests/test_model.py -v 2>&1 | tail -20
  149	```
  150	
  151	Expected: `ImportError` on `SliceWorkflowStep`, etc.
  152	
  153	- [ ] **Step 1.3: Implement the model changes**
  154	
  155	Edit `tools/tasktool/model.py`. Add the three enum classes after the `PlanningStatus` class (around line 17):
  156	
  157	```python
  158	class SliceWorkflowStep(str, Enum):
  159	    SPEC = "spec"
  160	    PLAN = "plan"
  161	    IMPLEMENT = "implement"
  162	    DONE = "done"
  163	
  164	class PhaseWorkflowStep(str, Enum):
  165	    SPEC = "spec"
  166	    READY = "ready"
  167	    IN_PROGRESS = "in_progress"
  168	    DONE = "done"
  169	
  170	class ReviewStage(str, Enum):
  171	    AWAITING_RESPONSE = "awaiting_response"
  172	    APPLYING_FIXES = "applying_fixes"
  173	    PASSED = "passed"
  174	```
  175	
  176	Add fields to `Slice` (after `notes: str = ""`, before `reviewer_chain`):
  177	
  178	```python
  179	    workflow_step: SliceWorkflowStep | None = None
  180	    review_active: bool = False
  181	    review_stage: ReviewStage | None = None
  182	```
  183	
  184	Add field to `Phase` (after `notes: str = ""`, before `slices`):
  185	
  186	```python
  187	    workflow_step: PhaseWorkflowStep | None = None
  188	```
  189	
  190	Change `SCHEMA_VERSION = 1` to `SCHEMA_VERSION = 2`.
  191	
  192	- [ ] **Step 1.4: Run tests to verify they pass**
  193	
  194	```bash
  195	cd tools/tasktool && python -m pytest tests/test_model.py -v 2>&1 | tail -20
  196	```
  197	
  198	Expected: all tests pass.
  199	
  200	- [ ] **Step 1.5: Commit**
  201	
  202	```bash
  203	git add tools/tasktool/model.py tools/tasktool/tests/test_model.py
  204	git commit -m "P6.S1: add workflow_step enums and fields to model"
  205	```
  206	
  207	---
  208	
  209	## Task 2: Round-trip serialisation with default elision
  210	
  211	**Files:**
  212	- Modify: `tools/tasktool/serialize.py`
  213	- Test: `tools/tasktool/tests/test_serialize.py`
  214	
  215	The review-block fields and `workflow_step` must be elided when at default, matching the existing `_strip_worktree_defaults` pattern. Enum values serialise as strings.
  216	
  217	- [ ] **Step 2.1: Write the failing test**
  218	
  219	Append to `tools/tasktool/tests/test_serialize.py`:
  220	
  221	```python
  222	import json
  223	from tasktool.model import (
  224	    Project, Phase, Slice, SliceWorkflowStep, PhaseWorkflowStep, ReviewStage,
  225	)
  226	from tasktool.serialize import to_dict, from_dict
  227	
  228	
  229	def _round_trip(p: Project) -> Project:
  230	    return from_dict(to_dict(p))
  231	
  232	
  233	def test_workflow_step_round_trip_slice():
  234	    s = Slice(id="S1", title="t", created="2026-05-23",
  235	              workflow_step=SliceWorkflowStep.PLAN)
  236	    ph = Phase(id="P6", title="t", created="2026-05-23", slices=[s])
  237	    p = Project(project="x", phases=[ph])
  238	    rt = _round_trip(p)
  239	    assert rt.phases[0].slices[0].workflow_step is SliceWorkflowStep.PLAN
  240	
  241	
  242	def test_workflow_step_round_trip_phase():
  243	    ph = Phase(id="P6", title="t", created="2026-05-23",
  244	               workflow_step=PhaseWorkflowStep.IN_PROGRESS)
  245	    p = Project(project="x", phases=[ph])
  246	    rt = _round_trip(p)
  247	    assert rt.phases[0].workflow_step is PhaseWorkflowStep.IN_PROGRESS
  248	
  249	
  250	def test_review_fields_round_trip():
  251	    s = Slice(id="S1", title="t", created="2026-05-23",
  252	              review_active=True, review_stage=ReviewStage.APPLYING_FIXES)
  253	    ph = Phase(id="P6", title="t", created="2026-05-23", slices=[s])
  254	    p = Project(project="x", phases=[ph])
  255	    rt = _round_trip(p)
  256	    assert rt.phases[0].slices[0].review_active is True
  257	    assert rt.phases[0].slices[0].review_stage is ReviewStage.APPLYING_FIXES
  258	
  259	
  260	def test_workflow_step_default_none_omitted_from_json():
  261	    s = Slice(id="S1", title="t", created="2026-05-23")
  262	    ph = Phase(id="P6", title="t", created="2026-05-23", slices=[s])
  263	    p = Project(project="x", phases=[ph])
  264	    raw = to_dict(p)
  265	    s_dict = raw["phases"][0]["slices"][0]
  266	    assert "workflow_step" not in s_dict
  267	    assert "review_active" not in s_dict
  268	    assert "review_stage" not in s_dict
  269	    assert "workflow_step" not in raw["phases"][0]
  270	
  271	
  272	def test_review_active_false_omitted_even_with_stage_explicit():
  273	    # Defensive: stage should be cleared whenever active is false. The
  274	    # serialiser must not emit a row with active=false AND stage=<something>.
  275	    s = Slice(id="S1", title="t", created="2026-05-23",
  276	              review_active=False, review_stage=None)
  277	    ph = Phase(id="P6", title="t", created="2026-05-23", slices=[s])
  278	    raw = to_dict(Project(project="x", phases=[ph]))
  279	    assert "review_active" not in raw["phases"][0]["slices"][0]
  280	    assert "review_stage" not in raw["phases"][0]["slices"][0]
  281	
  282	
  283	def test_legacy_row_without_workflow_fields_loads_clean():
  284	    raw = {
  285	        "project": "x",
  286	        "schema_version": 1,
  287	        "phases": [{
  288	            "id": "P1", "title": "t", "created": "2026-05-01", "slices": [
  289	                {"id": "S1", "title": "t", "created": "2026-05-01"}
  290	            ]
  291	        }],
  292	        "cross_cutting": [],
  293	        "archived_phases": [],
  294	        "archived_cross_cutting": [],
  295	    }
  296	    p = from_dict(raw)
  297	    assert p.phases[0].workflow_step is None
  298	    assert p.phases[0].slices[0].workflow_step is None
  299	    assert p.phases[0].slices[0].review_active is False
  300	    assert p.phases[0].slices[0].review_stage is None
  301	```
  302	
  303	- [ ] **Step 2.2: Run tests to confirm failure**
  304	
  305	```bash
  306	cd tools/tasktool && python -m pytest tests/test_serialize.py -v 2>&1 | tail -30
  307	```
  308	
  309	Expected: failures referencing missing serialisation logic for the new enums.
  310	
  311	- [ ] **Step 2.3: Update `serialize.py`**
  312	
  313	Add to the imports at the top:
  314	
  315	```python
  316	from tasktool.model import (
  317	    Project, Phase, Slice, Task, CrossCutting, ArchivedPhase,
  318	    ArchivedCrossCutting, BlockedOn,
  319	    Status, PlanningStatus, SliceWorkflowStep, PhaseWorkflowStep, ReviewStage,
  320	    SCHEMA_VERSION,
  321	)
  322	```
  323	
  324	Add a sibling helper next to `_strip_worktree_defaults`:
  325	
  326	```python
  327	_WORKFLOW_DEFAULT_OMIT = {
  328	    "workflow_step": None,
  329	    "review_active": False,
  330	    "review_stage": None,
  331	}
  332	
  333	
  334	def _strip_workflow_defaults(d: dict) -> dict:
  335	    for field, default in _WORKFLOW_DEFAULT_OMIT.items():
  336	        if field in d and d[field] == default:
  337	            del d[field]
  338	    return d
  339	```
  340	
  341	Extend `_coerce` inside `to_dict` so the three new enums serialise as strings:
  342	
  343	```python
  344	def _coerce(obj):
  345	    if isinstance(obj, (Status, PlanningStatus, SliceWorkflowStep, PhaseWorkflowStep, ReviewStage)):
  346	        return obj.value
  347	    return obj
  348	```
  349	
  350	In the walker that strips defaults per row (look for the existing call to `_strip_worktree_defaults`), add a parallel call to `_strip_workflow_defaults` for slice and phase nodes.
  351	
  352	In `from_dict`, coerce string values back into enums when present:
  353	
  354	```python
  355	def _slice_from(d: dict) -> Slice:
  356	    ...
  357	    if "workflow_step" in d and d["workflow_step"] is not None:
  358	        d = {**d, "workflow_step": SliceWorkflowStep(d["workflow_step"])}
  359	    if "review_stage" in d and d["review_stage"] is not None:
  360	        d = {**d, "review_stage": ReviewStage(d["review_stage"])}
  361	    return Slice(**d)
  362	```
  363	
  364	(Match the existing per-row reconstruction style — if `from_dict` currently uses `**d`, route through the enum coercion step before constructing. If it uses a Pydantic-style schema, follow that idiom instead.)
  365	
  366	For phases:
  367	
  368	```python
  369	def _phase_from(d: dict) -> Phase:
  370	    ...
  371	    if "workflow_step" in d and d["workflow_step"] is not None:
  372	        d = {**d, "workflow_step": PhaseWorkflowStep(d["workflow_step"])}
  373	    return Phase(...)
  374	```
  375	
  376	- [ ] **Step 2.4: Run tests**
  377	
  378	```bash
  379	cd tools/tasktool && python -m pytest tests/test_serialize.py tests/test_model.py -v 2>&1 | tail -25
  380	```
  381	
  382	Expected: all new tests pass; all pre-existing serialise/model tests still pass.
  383	
  384	- [ ] **Step 2.5: Commit**
  385	
  386	```bash
  387	git add tools/tasktool/serialize.py tools/tasktool/tests/test_serialize.py
  388	git commit -m "P6.S1: round-trip workflow_step + review block, omit defaults"
  389	```
  390	
  391	---
  392	
  393	## Task 3: Schema generator update + v1 compatibility
  394	
  395	**Files:**
  396	- Modify: `tools/tasktool/schema_gen.py`
  397	- Test: `tools/tasktool/tests/test_schema_gen.py`
  398	- New: `tools/tasktool/tests/test_v1_compat.py`
  399	
  400	**Important — no schema migration is added in S1.** `tools/tasktool/migrate.py` is the local-drift reconciler, not a tasklist-schema migrator, and S1 does not introduce a new migration subsystem. Instead, S1 relies on two existing properties:
  401	
  402	1. `from_dict` ignores legacy rows missing the new fields (the dataclass defaults kick in).
  403	2. `to_dict` writes `schema_version: 2` because `SCHEMA_VERSION = 2`. The next save of any v1 tasklist therefore promotes it to v2 automatically.
  404	
  405	So this task is: extend the inline phase/slice schemas in `build_schema()` to include the new properties, and add a small compatibility test proving a v1 dict round-trips cleanly.
  406	
  407	- [ ] **Step 3.1: Write the failing schema test**
  408	
  409	Append to `tools/tasktool/tests/test_schema_gen.py` (the file imports `build_schema` already — see `tools/tasktool/tests/test_schema_gen.py:1`):
  410	
  411	```python
  412	def test_schema_version_bumped_to_2():
  413	    schema = build_schema()
  414	    assert schema["properties"]["schema_version"]["const"] == 2
  415	
  416	
  417	def test_slice_schema_includes_workflow_step():
  418	    schema = build_schema()
  419	    slice_schema = schema["properties"]["phases"]["items"]["properties"]["slices"]["items"]
  420	    ws = slice_schema["properties"]["workflow_step"]
  421	    assert ws == {"oneOf": [{"enum": ["spec", "plan", "implement", "done"]}, {"type": "null"}]}
  422	
  423	
  424	def test_slice_schema_includes_review_block_fields():
  425	    schema = build_schema()
  426	    slice_schema = schema["properties"]["phases"]["items"]["properties"]["slices"]["items"]
  427	    assert slice_schema["properties"]["review_active"] == {"type": "boolean"}
  428	    assert slice_schema["properties"]["review_stage"] == {
  429	        "oneOf": [{"enum": ["awaiting_response", "applying_fixes", "passed"]}, {"type": "null"}]
  430	    }
  431	
  432	
  433	def test_phase_schema_includes_workflow_step():
  434	    schema = build_schema()
  435	    phase_schema = schema["properties"]["phases"]["items"]
  436	    ws = phase_schema["properties"]["workflow_step"]
  437	    assert ws == {"oneOf": [{"enum": ["spec", "ready", "in_progress", "done"]}, {"type": "null"}]}
  438	
  439	
  440	def test_cross_schema_does_not_include_workflow_step():
  441	    schema = build_schema()
  442	    cross_schema = schema["properties"]["cross_cutting"]["items"]
  443	    assert "workflow_step" not in cross_schema["properties"]
  444	```
  445	
  446	- [ ] **Step 3.2: Verify failure**
  447	
  448	```bash
  449	cd tools/tasktool && python -m pytest tests/test_schema_gen.py -v 2>&1 | tail -15
  450	```
  451	
  452	Expected: assertions failing because the new properties don't exist yet (and `additionalProperties: False` may also break round-trip tests until the schema is extended).
  453	
  454	- [ ] **Step 3.3: Extend the inline schemas in `build_schema()`**
  455	
  456	In `tools/tasktool/schema_gen.py`, edit the `slice_` block (around line 42) to add the three new properties before `additionalProperties: False`:
  457	
  458	```python
  459	            "worktree_prune_pending_at": {"oneOf": [date_str, {"type": "null"}]},
  460	            "workflow_step": {"oneOf": [
  461	                {"enum": ["spec", "plan", "implement", "done"]},
  462	                {"type": "null"},
  463	            ]},
  464	            "review_active": {"type": "boolean"},
  465	            "review_stage": {"oneOf": [
  466	                {"enum": ["awaiting_response", "applying_fixes", "passed"]},
  467	                {"type": "null"},
  468	            ]},
  469	        },
  470	        "additionalProperties": False,
  471	    }
  472	```
  473	
  474	Edit the `phase` block (around line 70) to add one property:
  475	
  476	```python
  477	            "phase_reviewer_chain": {"oneOf": [{"type": "string"}, {"type": "null"}]},
  478	            "notes": {"type": "string"},
  479	            "workflow_step": {"oneOf": [
  480	                {"enum": ["spec", "ready", "in_progress", "done"]},
  481	                {"type": "null"},
  482	            ]},
  483	            "slices": {"type": "array", "items": slice_},
  484	```
  485	
  486	The top-level `schema_version` property should already reference `SCHEMA_VERSION`. If it uses a literal, change it to the constant. Verify by searching the file for `schema_version` and tightening it to `{"const": SCHEMA_VERSION}` if it isn't already.
  487	
  488	- [ ] **Step 3.4: Write the v1 compatibility test**
  489	
  490	Create `tools/tasktool/tests/test_v1_compat.py`:
  491	
  492	```python
  493	import json
  494	from pathlib import Path
  495	
  496	from tasktool.serialize import from_dict, to_dict
  497	
  498	
  499	def _v1_raw() -> dict:
  500	    # Persisted slice IDs are short — see schema_gen.py:46 `^S\d+[a-z]?$`.
  501	    return {
  502	        "project": "x", "schema_version": 1, "north_star": "",
  503	        "phases": [{
  504	            "id": "P1", "title": "t", "created": "2026-05-01", "status": "ready",
  505	            "slices": [{"id": "S1", "title": "t", "created": "2026-05-01", "status": "ready"}],
  506	        }],
  507	        "cross_cutting": [], "archived_phases": [], "archived_cross_cutting": [],
  508	    }
  509	
  510	
  511	def test_v1_loads_with_new_field_defaults():
  512	    p = from_dict(_v1_raw())
  513	    assert p.phases[0].workflow_step is None
  514	    s = p.phases[0].slices[0]
  515	    assert s.workflow_step is None
  516	    assert s.review_active is False
  517	    assert s.review_stage is None
  518	
  519	
  520	def test_v1_to_v2_promotion_on_save():
  521	    p = from_dict(_v1_raw())
  522	    out = to_dict(p)
  523	    assert out["schema_version"] == 2
  524	    # The legacy row should not gain a workflow_step key automatically.
  525	    assert "workflow_step" not in out["phases"][0]
  526	    assert "workflow_step" not in out["phases"][0]["slices"][0]
  527	
  528	
  529	def test_v1_validates_against_v2_schema_after_save():
  530	    # If jsonschema is available in the test env, validate; otherwise skip.
  531	    pytest = __import__("pytest")
  532	    try:
  533	        import jsonschema
  534	    except ImportError:
  535	        pytest.skip("jsonschema not installed")
  536	    from tasktool.schema_gen import build_schema
  537	    p = from_dict(_v1_raw())
  538	    out = to_dict(p)
  539	    jsonschema.validate(instance=out, schema=build_schema())
  540	```
  541	
  542	- [ ] **Step 3.5: Run tests**
  543	
  544	```bash
  545	cd tools/tasktool && python -m pytest tests/test_schema_gen.py tests/test_v1_compat.py -v 2>&1 | tail -25
  546	```
  547	
  548	Expected: pass.
  549	
  550	- [ ] **Step 3.6: Commit**
  551	
  552	```bash
  553	git add tools/tasktool/schema_gen.py tools/tasktool/tests/test_schema_gen.py tools/tasktool/tests/test_v1_compat.py
  554	git commit -m "P6.S1: extend schema for workflow_step + review block; verify v1 compat"
  555	```
  556	
  557	---
  558	
  559	## Task 4: Relax `tasktool set` — make `--status` optional, add new flags
  560	
  561	**Files:**
  562	- Modify: `tools/tasktool/cli.py` (lines 88–95)
  563	- Modify: `tools/tasktool/commands.py` (function `cmd_set`)
  564	- Test: `tools/tasktool/tests/test_commands.py`
  565	
  566	- [ ] **Step 4.1: Write failing tests**
  567	
  568	Append to `tools/tasktool/tests/test_commands.py`:
  569	
  570	```python
  571	import pytest
  572	from tasktool import commands
  573	
  574	
  575	def test_set_workflow_step_on_slice(tmp_project_with_p6_s1):
  576	    p = tmp_project_with_p6_s1
  577	    commands.cmd_set(p, id="P6.S1", workflow_step="plan")
  578	    state = commands.load_project(p)
  579	    s = state.phases[0].slices[0]
  580	    assert s.workflow_step.value == "plan"
  581	
  582	
  583	def test_set_workflow_step_on_phase(tmp_project_with_p6_s1):
  584	    p = tmp_project_with_p6_s1
  585	    commands.cmd_set(p, id="P6", workflow_step="ready")
  586	    state = commands.load_project(p)
  587	    assert state.phases[0].workflow_step.value == "ready"
  588	
  589	
  590	def test_set_rejects_no_op_invocation(tmp_project_with_p6_s1):
  591	    p = tmp_project_with_p6_s1
  592	    with pytest.raises(commands.UsageError, match="at least one mutating flag"):
  593	        commands.cmd_set(p, id="P6.S1")
  594	
  595	
  596	def test_set_rejects_workflow_step_and_clear(tmp_project_with_p6_s1):
  597	    p = tmp_project_with_p6_s1
  598	    with pytest.raises(commands.UsageError, match="mutually exclusive"):
  599	        commands.cmd_set(p, id="P6.S1", workflow_step="plan", clear_workflow_step=True)
  600	

[truncated: 1220 additional lines]

## Context Previews

### docs/specs/2026-05-23-P6-programmatic-workflow-enhancements-design.md

    1	# P6 — Programmatic Workflow Enhancements (Design)
    2	
    3	**Phase ID:** P6
    4	**Date:** 2026-05-23
    5	**Status:** spec (awaiting external review)
    6	
    7	## 1. Motivation
    8	
    9	The tasktool data model and skill suite already encode a multi-step workflow per slice — brainstorm a spec, write a plan, implement, review, close — but the *step* itself is never stored. Skills and humans infer "where in the workflow am I?" from a combination of `spec_path`, `plan_path`, `planning_status`, `status`, `started`, `closed`, and the presence of a `reviewer_chain` folder. That inference is reliable enough today, but:
   10	
   11	- Downstream consumers that want to *react* to the current step (session-rename hooks, statuslines, future automation) have no first-class field to read.
   12	- The relationship between fields is implicit in skill prose and the reviewer-gate code, not in the model.
   13	- Future enhancements (auto-advance, transition gating, worktree automation, refusing operations on the wrong step) are blocked on having an authoritative step value.
   14	
   15	This phase introduces `workflow_step` as a first-class field on `Slice` and `Phase`, plus a transient *review block* on `Slice` populated by the external-reviewer script. The first slice ships only the storage, manual setter, and a read-only inference command — no automation, no migration. Subsequent slices in this phase build on that foundation.
   16	
   17	## 2. Scope
   18	
   19	### In scope (this phase)
   20	
   21	- **S1 (designed in detail below):** Add `workflow_step` field on `Slice` and `Phase`; add transient review block on `Slice`; add `tasktool set --workflow-step`; add `tasktool infer-step` (read-only); update render / show / brief to surface the field; update skill markdown to point at it; ship a small change to the external-reviewer script so it writes the review block.
   22	- **S2 (sketched):** Auto-advance `workflow_step` on existing transition commands (`prepare`, `artifact add`, `start`, `close`). One-shot migration backfill of existing rows.
   23	- **S3 (sketched):** Session-rename hook — reads the slice's `workflow_step` and writes `<agent>-<Pn.Sm>-<step>` to the harness session label (Claude Code `/rename` equivalent on the underlying JSONL summary; Codex equivalent).
   24	
   25	### Out of scope (recorded as future slices or follow-up items)
   26	
   27	- Adding a `cancelled` status / flag on slices.
   28	- Refusing operations when `workflow_step` is wrong (e.g., refusing `start` if step != `implement`).
   29	- Collapsing `planning_status` into `workflow_step`.
   30	- Collapsing `Phase.status` into `Phase.workflow_step`.
   31	- Worktree automation triggered off step transitions.
   32	- A phase-level *review block* analogous to the slice-level one.
   33	- Reorganising tasktool's CLI surface around workflow verbs rather than the current command set.
   34	- CrossCutting (`X*`) workflow steps — these items skip spec/plan and the step model adds little value.
   35	
   36	## 3. Design — S1: Add `workflow_step` field and read-only inference
   37	
   38	### 3.1 Model changes
   39	
   40	In `tools/tasktool/model.py`:
   41	
   42	```python
   43	class SliceWorkflowStep(str, Enum):
   44	    SPEC = "spec"
   45	    PLAN = "plan"
   46	    IMPLEMENT = "implement"
   47	    DONE = "done"
   48	
   49	class PhaseWorkflowStep(str, Enum):
   50	    SPEC = "spec"
   51	    READY = "ready"
   52	    IN_PROGRESS = "in_progress"
   53	    DONE = "done"
   54	
   55	class ReviewStage(str, Enum):
   56	    AWAITING_RESPONSE = "awaiting_response"
   57	    APPLYING_FIXES = "applying_fixes"
   58	    PASSED = "passed"
   59	```
   60	
   61	Field additions:
   62	
   63	- `Slice.workflow_step: SliceWorkflowStep | None = None`
   64	- `Slice.review_active: bool = False`
   65	- `Slice.review_stage: ReviewStage | None = None`
   66	- `Phase.workflow_step: PhaseWorkflowStep | None = None`
   67	
   68	`CrossCutting` is unchanged.
   69	
   70	`SCHEMA_VERSION` bumps from `1` to `2`. Serialise enum values as plain lowercase strings. `None` is legal and means "not set" — for `workflow_step` this is the default for existing rows; for the review fields it means "no review currently active".
   71	
   72	### 3.2 CLI surface
   73	
   74	New / changed commands:
   75	
   76	- `tasktool set <id> --workflow-step <value>` — value must match the row kind (`spec|plan|implement|done` for slices; `spec|ready|in_progress|done` for phases). `--clear-workflow-step` to unset.
   77	- `tasktool set <id> --review-active <bool>` and `--review-stage <value>` — owned by the external-reviewer script. Skills/agents should not write these directly. Calling `--review-active false` clears `--review-stage` too. Only valid against slice rows.
   78	
   79	**Argument shape changes to `tasktool set`.** Today `tasktool set` requires `--status` (`tools/tasktool/cli.py:88`, `tools/tasktool/commands.py:941`). S1 relaxes this so the command accepts any non-empty subset of `{--status, --workflow-step, --clear-workflow-step, --review-active, --review-stage}` plus existing flags like `--blocked-on` / `--depends-on`. Validation rules:
   80	
   81	- At least one mutating flag must be present (no-op invocations are rejected).
   82	- `--workflow-step` and `--clear-workflow-step` are mutually exclusive.
   83	- `--review-active false` implicitly clears `--review-stage`; passing `--review-stage <value>` together with `--review-active false` is rejected.
   84	- `--review-active` and `--review-stage` against non-slice rows are rejected.
   85	- `--workflow-step` values are validated against the row's kind enum (slice vs phase).
   86	- All other existing single-flag behaviour (`tasktool set --status …`) keeps working unchanged.
   87	- `tasktool infer-step <id>` — print the inferred step for a single row (text by default; `--format json` for structured).
   88	- `tasktool infer-step --all` — print one line per row (slices + phases) with current vs inferred step.
   89	- `tasktool infer-step --all --diff` — same as `--all` but only emits rows where stored ≠ inferred.
   90	- `tasktool list --workflow-step <value>` — filter by stored step.
   91	
   92	Surfaced in existing commands:
   93	
   94	- `tasktool show <id>` — print `workflow_step` next to `status`; print the review block iff `review_active == true`.
   95	- `tasktool render` — show step glyph or column for slices/phases where space allows; review block only when active.
   96	- `tasktool brief <id>` — include step in the heading, review block only when active.
   97	
   98	### 3.3 Inference rules (read-only in S1)
   99	
  100	**For a slice:**
  101	
  102	```
  103	phase.spec_path absent                                       → spec
  104	phase.spec_path present and slice.plan_path absent           → spec
  105	slice.plan_path present and slice.planning_status != ratified → plan
  106	slice.plan_path present, planning_status == ratified,
  107	  status in {ready, in_progress}                             → implement
  108	status == done                                               → done
  109	```
  110	
  111	**Blocked slices.** `Status.BLOCKED` is an orthogonal overlay on the workflow step, not a step itself. The inference rules above are applied as if `status == in_progress` (i.e., the blocker doesn't change which step the work is in), and the result is annotated:
  112	
  113	- Text output: inferred step suffixed with `(blocked)`, e.g. `plan (blocked)`.
  114	- JSON output: `{"step": "plan", "blocked": true}`.
  115	
  116	`status == done` always wins regardless of any earlier state — a closed slice infers `done` even if other fields would imply something earlier (the precedence is: `done` > any computed value).
  117	
  118	**`infer-step --all --diff` exit code.** Exits `0` when every row matches its stored value or has no stored value. Exits `1` when any row differs (informational; the command itself never writes). Process errors (file not found, etc.) use `2` per existing tasktool convention.
  119	
  120	**For a phase.** Rules are evaluated top-to-bottom; the first match wins. They are total over the slice-status alphabet `{ready, in_progress, blocked, done}`.
  121	
  122	```
  123	1. phase.spec_path absent                                    → spec
  124	2. phase.spec_path present, no child slices                  → spec
  125	3. child slices exist, every slice.status == done            → done
  126	4. any child slice.status in {in_progress, blocked, done}    → in_progress
  127	5. otherwise (every child slice.status == ready)             → ready
  128	```
  129	
  130	Rationale: rule 3 takes precedence over rule 4 so a phase whose current children are all closed always lands on `done`. If new non-`done` slices are later added to that phase, rule 3 stops matching and rule 4 takes over — the phase becomes `in_progress` again. Rule 4 collapses every mixed state ("some started, some not", "some done, some still pending", "one slice is blocked but the rest aren't started") into `in_progress`: once the phase has begun in any way, it is in progress. Rule 5 fires only when no work has begun at all on any child.
  131	
  132	**Phase blocked annotation.** When rule 4 matches *and* any child slice has `status == blocked`, the inference output carries a `(blocked)` annotation in text form and `blocked: true` in JSON — symmetric with the slice-level annotation in §3.3. The base step remains `in_progress`. Rule 3 (all done) ignores the blocked overlay because no slice can be both `done` and `blocked`.
  133	
  134	**For cross-cutting:** inference returns `n/a`; `--diff` ignores these rows.
  135	
  136	### 3.4 Transient review block (slice)
  137	
  138	**Scope of ownership.** In the current model, *spec review is phase-owned* — `Phase` carries `spec_path` and `phase_reviewer_chain`; slices have no `spec_path`. The slice-level review block introduced here therefore covers only **slice-owned reviews**: plan review (review of `slice.plan_path`) and post-slice review (review of completed slice work). Phase-level spec/plan reviews remain tracked through `Phase.phase_reviewer_chain` only; a phase-level transient review block is explicit future scope and is **not** added in S1 (see §6).
  139	
  140	This means the review block on a slice is only populated when the slice's `workflow_step ∈ {plan, implement}` — i.e., during plan review or post-slice review. When a slice is in `workflow_step == spec`, the active review (if any) belongs to the parent phase, not the slice; the slice's review block stays empty.
  141	
  142	Owned by the external-reviewer script (`skills/external-review/scripts/external-reviewer.py`), not by skills or agents:
  143	
  144	| Field | Type | Set when |
  145	|---|---|---|
  146	| `review_active` | bool | Reviewer starts a chain on this slice's current step (plan or post-slice). `true` until the round completes or the step advances. |
  147	| `review_stage` | enum: `awaiting_response \| applying_fixes \| passed` | `awaiting_response` while the reviewer is being called; `applying_fixes` once a `revise` verdict comes back and fixes are in progress; `passed` after a `ready` / `ready with small edits` verdict. Cleared when `review_active` becomes `false`. |
  148	
  149	JSON serialisation: when `review_active == false` and `review_stage` is unset (the default), both fields are **omitted** from the serialised row, the same way `worktree_*` defaults are elided today. This keeps `tasklist.json` token-clean for rows not under active review.
  150	
  151	**Mapping from `external-reviewer review` to a slice ID.** Today the bridge only requires `--work-id` for `post-slice` and `post-phase`. For the new tasktool calls in S1, the script writes the review block only when `--work-id` resolves to a slice row; it is a no-op when `--work-id` is absent or resolves to a phase / cross-cutting row. Concretely:
  152	
  153	- `--kind plan` invocations with `--work-id <Pn.Sm>` → write block to that slice.
  154	- `--kind post-slice` invocations with `--work-id <Pn.Sm>` → write block to that slice.
  155	- All other invocations (`--kind spec`, `--kind post-phase`, missing/non-slice `--work-id`) → no tasktool write; phase-owned reviews are out of scope for the slice block in S1.
  156	
  157	Lifecycle (slice-owned reviews only):
  158	
  159	1. External-reviewer is invoked with `--work-id <Pn.Sm>` → calls `tasktool set <id> --review-active true --review-stage awaiting_response`.
  160	2. Reviewer responds → if verdict is `revise`, call `--review-stage applying_fixes`. If verdict is `ready`/`ready_with_small_edits`, call `--review-stage passed`.
  161	3. Agent reaches the next step → calls `tasktool set <id> --workflow-step <next>`. This implicitly clears `review_active`, `review_stage`.
  162	4. If the slice's `workflow_step` reaches `done`, the review block is permanently absent.
  163	
  164	Render policy: `render`, `brief`, `show` print the review block only when `review_active == true`. Steady-state token cost: zero for rows not under review.
  165	
  166	### 3.5 Skill markdown updates
  167	
  168	All updates are light-touch in S1: pointing at the field, scoping it correctly, explicitly noting that the field is informational in S1 and will drive automation in later slices. No skill *requires* the field to be set.
  169	
  170	- **`skills/tasklist-discipline/SKILL.md`** *(primary update)*: Add a `workflow_step` section listing the slice and phase enum values, when to set them manually, and that automation comes later. Show example commands. Cite the read-only `infer-step` command for sanity-checking. Explicit scoping line: *"`workflow_step` tracks where a slice or phase is in the spec → plan → implement → done sequence. The two enums are intentionally different: slices step through spec/plan/implement/done; phases step through spec/ready/in_progress/done. Cross-cutting items (`X*`) do not have a `workflow_step` — they skip the spec/plan loop."*
  171	- **`skills/brainstorming/SKILL.md`**: At the spec-commit step, a one-liner: after `tasktool artifact add … --kind spec`, suggest `tasktool set <id> --workflow-step spec` if not already set. After spec review passes, the skill prose mentions that the agent should set `--workflow-step plan` before invoking writing-plans.
  172	- **`skills/writing-plans/SKILL.md`**: At the plan-commit step, mirror pattern. After plan review passes, set `--workflow-step implement`.
  173	- **`skills/subagent-driven-development/SKILL.md`** and **`skills/executing-plans/SKILL.md`**: Note that the slice's `workflow_step` should be `implement` when work starts and `done` only after post-slice review passes.
  174	- **`skills/external-review/SKILL.md`**: Brief note that the reviewer script writes the transient review block automatically — no agent action required.
  175	- **`skills/project-setup/SKILL.md`**: No changes in S1.
  176	
  177	The shared framing across all updates: *"The field is informational in S1. Setting it correctly now means S2 can take it from here."*
  178	
  179	### 3.6 External-reviewer script change
  180	
  181	`skills/external-review/scripts/external-reviewer.py` (or equivalent bridge) gains three small calls:
  182	
  183	- On chain start: `tasktool set <id> --review-active true --review-stage awaiting_response`.
  184	- After reviewer responds with a non-ready verdict: `tasktool set <id> --review-stage applying_fixes`.
  185	- After reviewer responds with a ready / ready-with-small-edits verdict: `tasktool set <id> --review-stage passed`.
  186	
  187	Best-effort: failures to update tasktool (e.g., row not found, tasktool not installed) log a warning but do not block the review.
  188	
  189	### 3.7 Files touched (S1)
  190	
  191	- `tools/tasktool/model.py` — enums, fields, schema bump.
  192	- `tools/tasktool/serialize.py` — round-trip + validation.
  193	- `tools/tasktool/commands.py` — `set` (new flags), `infer-step` (new command), filters on `list`, render output in `show`/`render`/`brief`.
  194	- `tools/tasktool/cli.py` — argparse wiring.
  195	- `tools/tasktool/schema_gen.py` — schema bump + new enum types.
  196	- `tools/tasktool/render.py` — workflow_step column + review block.
  197	- `tools/tasktool/brief.py` — heading + review block.
  198	- `tools/tasktool/tests/` — round-trip, inference rules, CLI tests.
  199	- `skills/tasklist-discipline/SKILL.md` — new `workflow_step` section.
  200	- `skills/brainstorming/SKILL.md`, `skills/writing-plans/SKILL.md`, `skills/subagent-driven-development/SKILL.md`, `skills/executing-plans/SKILL.md`, `skills/external-review/SKILL.md` — short pointers.

[truncated: 78 additional lines]
### docs/tasklist.json

    1	{
    2	  "archived_cross_cutting": [
    3	    {
    4	      "archived_date": "2026-05-21",
    5	      "archived_path": "docs/archived-tasks/X15-archive-closed-cross-cutting-items.md",
    6	      "id": "X15",
    7	      "title": "Archive closed cross-cutting items"
    8	    },
    9	    {
   10	      "archived_date": "2026-05-21",
   11	      "archived_path": "docs/archived-tasks/X16-stamp-installed-shims-and-enforce-versio.md",
   12	      "id": "X16",
   13	      "title": "Stamp installed shims and enforce version drift refusal"
   14	    },
   15	    {
   16	      "archived_date": "2026-05-23",
   17	      "archived_path": "docs/archived-tasks/X18-harden-external-reviewer-caller-detectio.md",
   18	      "id": "X18",
   19	      "title": "Harden external reviewer caller detection for Codex"
   20	    },
   21	    {
   22	      "archived_date": "2026-05-23",
   23	      "archived_path": "docs/archived-tasks/X20-install-codex-todo-snapshot-hook.md",
   24	      "id": "X20",
   25	      "title": "Install Codex todo snapshot hook"
   26	    },
   27	    {
   28	      "archived_date": "2026-05-23",
   29	      "archived_path": "docs/archived-tasks/X19-install-todowrite-snapshot-hook-via-depl.md",
   30	      "id": "X19",
   31	      "title": "Install TodoWrite snapshot hook via deploy.sh"
   32	    },
   33	    {
   34	      "archived_date": "2026-05-23",
   35	      "archived_path": "docs/archived-tasks/X21-fix-codex-todo-snapshot-async-hook-regis.md",
   36	      "id": "X21",
   37	      "title": "Fix Codex todo snapshot async hook registration"
   38	    }
   39	  ],
   40	  "archived_phases": [
   41	    {
   42	      "archived_date": "2026-05-18",
   43	      "archived_path": "docs/archived-tasks/P2-tasktool-json-backed-task-management-cli.md",
   44	      "id": "P2",
   45	      "title": "tasktool: JSON-backed task management CLI"
   46	    },
   47	    {
   48	      "archived_date": "2026-05-19",
   49	      "archived_path": "docs/archived-tasks/P4-tasktool-coordination-and-lifecycle-auth.md",
   50	      "id": "P4",
   51	      "title": "Tasktool coordination and lifecycle authority"
   52	    },
   53	    {
   54	      "archived_date": "2026-05-19",
   55	      "archived_path": "docs/archived-tasks/P3-phase-planning-workflow.md",
   56	      "id": "P3",
   57	      "title": "Phase planning workflow"
   58	    },
   59	    {
   60	      "archived_date": "2026-05-20",
   61	      "archived_path": "docs/archived-tasks/P1-external-reviewer-work-historical.md",
   62	      "id": "P1",
   63	      "title": "External-reviewer work (historical)"
   64	    },
   65	    {
   66	      "archived_date": "2026-05-21",
   67	      "archived_path": "docs/archived-tasks/P5-tasktool-owned-worktree-lifecycle-using-.md",
   68	      "id": "P5",
   69	      "title": "Tasktool-owned worktree lifecycle & using-git-worktrees skill collapse"
   70	    }
   71	  ],
   72	  "cross_cutting": [
   73	    {
   74	      "closed": "2026-05-18",
   75	      "created": "2026-05-18",
   76	      "id": "X1",
   77	      "notes": "Changed external-review default prompt transport from argv to stdin so the bundled Codex reviewer-agent receives prompts via codex exec '-' and avoids argv length failures.",
   78	      "refs": [],
   79	      "started": null,
   80	      "status": "done",
   81	      "title": "Default external-review prompt transport to stdin"
   82	    },
   83	    {
   84	      "closed": "2026-05-18",
   85	      "created": "2026-05-18",
   86	      "id": "X2",
   87	      "notes": "Added repo-local tools/tasktool/tasktool launcher, updated tasklist/project-setup docs to prefer it, and taught the pre-commit hook to use the repo-local launcher before falling back to a global tasktool shim.",
   88	      "refs": [],
   89	      "started": null,
   90	      "status": "done",
   91	      "title": "Add repo-local tasktool launcher"
   92	    },
   93	    {
   94	      "closed": "2026-05-19",
   95	      "created": "2026-05-19",
   96	      "id": "X3",
   97	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. External-review verdict parsing now accepts markdown-emphasized Overall Verdict headings such as **5. Overall Verdict** followed by ready/revise text.",
   98	      "refs": [
   99	        "skills/external-review/scripts/external-reviewer.py",
  100	        "skills/external-review/tests/test_heading_style_verdict.py"
  101	      ],
  102	      "started": null,
  103	      "status": "done",
  104	      "title": "Spot fix: parse bold external-review verdict headings"
  105	    },
  106	    {
  107	      "closed": "2026-05-19",
  108	      "created": "2026-05-19",
  109	      "id": "X4",
  110	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. Legacy markdown import now accepts fully-qualified slice IDs and additional cross-cutting forms including tagged done items, blocked cross rows coerced to ready, and archived cross rows treated as done.",
  111	      "refs": [
  112	        "tools/tasktool/importer.py"
  113	      ],
  114	      "started": null,
  115	      "status": "done",
  116	      "title": "Spot fix: broaden legacy tasklist importer compatibility"
  117	    },
  118	    {
  119	      "closed": "2026-05-19",
  120	      "created": "2026-05-19",
  121	      "id": "X5",
  122	      "notes": "User-requested hook update completed outside the normal workflow for speed. Adds Stop/SubagentStop finished-agent notifications, milestone message derivation from final agent text/transcript payloads, Hypr TTS config reuse with OPENAI_API_KEY fallback, and non-TTS ding fallbacks.\nSuperseded by X8: final-text milestone parsing was removed; agent hooks now emit generic dings and semantic spoken notifications come from tasktool status changes.",
  123	      "refs": [
  124	        "hooks/agent-finished",
  125	        "hooks/hooks.json",
  126	        "hooks/hooks-cursor.json",
  127	        "tests/claude-code/test-agent-finished-hook.sh"
  128	      ],
  129	      "started": null,
  130	      "status": "done",
  131	      "title": "Add finished-agent notification hook"
  132	    },
  133	    {
  134	      "closed": "2026-05-19",
  135	      "created": "2026-05-19",
  136	      "id": "X6",
  137	      "notes": "Codex startup skips Stop/SubagentStop notification hooks when hooks.json uses async=true; fix should preserve finished-agent notification behavior while avoiding unsupported async hook registration in Codex.\nSet finished-agent Stop/SubagentStop hook registrations to async=false for Codex compatibility. The hook now backgrounds real notification playback internally so synchronous hook registration returns quickly while dry-run tests remain foreground and deterministic.",
  138	      "refs": [
  139	        "hooks/hooks.json",
  140	        "hooks/agent-finished",
  141	        "tests/claude-code/test-hook-config.sh",
  142	        "tests/claude-code/test-agent-finished-hook.sh"
  143	      ],
  144	      "started": null,
  145	      "status": "done",
  146	      "title": "Fix Codex finished-agent hook compatibility"
  147	    },
  148	    {
  149	      "closed": "2026-05-19",
  150	      "created": "2026-05-19",
  151	      "id": "X7",
  152	      "notes": "Codex reported superstar/6.0.0 because the installable local marketplace payload under plugins/superstar still declared version 6.0.0 and the version bump audit did not track that embedded manifest.\n\nBumped the embedded Codex plugin payload manifest to 6.0.1 and added it to the version bump check. Reinstalled superstar@superstar-dev, then rebuilt the 6.0.1 runtime cache as a materialized copy of this checkout with .agents excluded so Codex sees the full skills/hooks tree while codex plugin list still reports installed/enabled. Final probe shows cache version 6.0.1, skills/hooks present, and no async-hook warning.",
  153	      "refs": [
  154	        ".version-bump.json",
  155	        "plugins/superstar/.codex-plugin/plugin.json",
  156	        ".agents/plugins/marketplace.json",
  157	        "tests/codex-plugin-sync/test-version-drift.sh",
  158	        "tests/codex-plugin-sync/test-local-marketplace.sh"
  159	      ],
  160	      "started": null,
  161	      "status": "done",
  162	      "title": "Fix Superstar Codex plugin payload version drift"
  163	    },
  164	    {
  165	      "closed": "2026-05-19",
  166	      "created": "2026-05-19",
  167	      "id": "X8",
  168	      "notes": "Move semantic spoken notifications to tasktool status transitions for ready/in_progress/blocked/done. Keep agent Stop/SubagentStop hooks as generic completion dings only, with different sound styles for Claude and Codex.\nAgent Stop/SubagentStop hooks now emit generic harness-specific dings only. Semantic spoken notifications moved to tasktool status events for ready, in_progress, blocked, and done, including create, set, close, block, unblock, and archive-phase paths.",
  169	      "refs": [
  170	        "hooks/agent-finished",
  171	        "tools/tasktool/notify.py",
  172	        "tools/tasktool/commands.py",
  173	        "tools/tasktool/tests/test_notify.py",
  174	        "tools/tasktool/tests/test_commands.py",
  175	        "tools/tasktool/tests/conftest.py",
  176	        "tests/claude-code/test-agent-finished-hook.sh"
  177	      ],
  178	      "started": null,
  179	      "status": "done",
  180	      "title": "Move semantic notifications from agent hooks to tasktool status changes"
  181	    },
  182	    {
  183	      "closed": "2026-05-19",
  184	      "created": "2026-05-19",
  185	      "id": "X9",
  186	      "notes": "Rapid tasktool status changes currently spawn independent notifier processes, causing overlapping TTS/audio. Add a single-audio queue with at most three queued tasktool events; overflow should collapse to a single 'multiple other events' summary and drop further items.\nAdded a file-backed notification queue shared by agent dings and tasktool TTS. Only one worker drains audio at a time. Queue capacity is three pending events; overflow keeps the first two pending items and replaces the rest with a single 'Multiple other events' summary, dropping further burst items while the summary remains queued.",
  187	      "refs": [
  188	        "tools/tasktool/notify.py",
  189	        "tools/tasktool/tests/test_notify.py"
  190	      ],
  191	      "started": null,
  192	      "status": "done",
  193	      "title": "Coalesce bursty tasktool audio notifications"
  194	    },
  195	    {
  196	      "closed": "2026-05-20",
  197	      "created": "2026-05-20",
  198	      "id": "X10",
  199	      "notes": "",
  200	      "refs": [

[truncated: 141 additional lines]

<!-- superstar-prompt:end -->