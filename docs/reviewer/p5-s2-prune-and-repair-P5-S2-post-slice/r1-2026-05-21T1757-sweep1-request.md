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
/home/simon/Dev/sigreer/skills/superstar/.claude/worktrees/P5.S2-prune-and-repair

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-21-P5-S2-prune-and-repair.md

Additional context files:
- docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md
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

### docs/plans/2026-05-21-P5-S2-prune-and-repair.md

    1	# P5.S2 Prune + Repair Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Add `tasktool worktree prune` (with `--keep-branch`, `--force`, `--finalize`) and `tasktool worktree repair`, the three audit fields (`worktree_pruned_at`, `worktree_prune_pending`, `worktree_prune_pending_at`), and a post-merge prune step in the `finishing-a-development-branch` skill.
    6	
    7	**Architecture:** Extend the existing `tools/tasktool/worktree.py` module with prune/repair primitives (guard checks, git plumbing, prune-from-inside detection). Add `cmd_worktree_prune` and `cmd_worktree_repair` in `tools/tasktool/commands.py` reusing the existing `_write_context`/`_load`/`_save`/`_find_item` helpers. Extend the `Slice` and `CrossCutting` dataclasses in `model.py` with optional audit fields; teach `serialize.py` to round-trip them; teach `validate.py` to type-check them. Wire the new subcommands into the `worktree` argparse group introduced by P5.S1.
    8	
    9	**Tech Stack:** Python 3.11, argparse, dataclasses, subprocess for git plumbing, pytest with `tmp_path` for git fixtures.
   10	
   11	**Spec:** `docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md` §5.3, §5.3.1, §5.3.2, §6 P5.S2.
   12	
   13	**Tasktool row:** `P5.S2`. Plan path already reserved via `tasktool prepare`. Implementation starts with `tasktool start P5.S2` as the first execution step (see Task 0).
   14	
   15	**Hard precondition: P5.S1 has shipped.** P5.S1 introduces every contract this plan depends on. **Before Task 0 the executor MUST run the preflight in Task -1 below.** If any preflight check fails, stop and notify the coordinator — do not attempt to recreate S1 work inline.
   16	
   17	P5.S1 contracts this plan relies on:
   18	- `Slice.worktree_path: str | None`, `Slice.worktree_branch: str | None`, `Slice.worktree_in_place: bool` on the model (also on `CrossCutting` for ad-hoc rows).
   19	- `cmd_start` records both fields; `cmd_worktree_list`, `cmd_worktree_status`, `cmd_worktree_adopt` exist.
   20	- The `tasktool worktree` argparse group exists in `cli.py` with `list`, `status`, `adopt` subparsers.
   21	- `tools/tasktool/worktree.py` already contains `_git`, `worktree_roots`, `git_common_dir`, `find_authoritative_root`. We will add to it.
   22	- `tasktool start --ad-hoc <slug>` allocates an `X<n>` cross-cutting row with `worktree_path` / `worktree_branch` recorded and `notes: "ad-hoc"`.
   23	- `serialize.py`'s slice/cross dict already emits the P5.S1 `worktree_*` fields. Since the current `serialize.py` uses `asdict(p)` (see `tools/tasktool/serialize.py:11-23`), every dataclass field is emitted unconditionally. Reviewer F2 (round 1) flagged that adding new fields will therefore extend canonical bytes — that is expected and handled by Task 2's normalise step.
   24	
   25	---
   26	
   27	## File Structure
   28	
   29	Files to create:
   30	- `tools/tasktool/tests/test_worktree_prune.py` — all prune-path tests (guards, `--force`, `--keep-branch`, prune-from-inside, `--finalize` preconditions, recent-HEAD note, ad-hoc lifecycle, `--force` scope negatives).
   31	- `tools/tasktool/tests/test_worktree_repair.py` — `repair` happy-path and refusal tests.
   32	
   33	Files to modify:
   34	- `tools/tasktool/model.py` — add `worktree_pruned_at`, `worktree_prune_pending`, `worktree_prune_pending_at` to `Slice` and `CrossCutting`.
   35	- `tools/tasktool/serialize.py` — round-trip the new audit fields.
   36	- `tools/tasktool/validate.py` — type/shape check the new fields.
   37	- `tools/tasktool/worktree.py` — add `is_inside_worktree`, `branch_is_merged`, `working_tree_dirty`, `head_age_seconds`, `git_worktree_remove`, `git_branch_delete`, `git_worktree_add`, `branch_exists`, `path_is_registered_worktree`.
   38	- `tools/tasktool/commands.py` — add `cmd_worktree_prune` and `cmd_worktree_repair`.
   39	- `tools/tasktool/cli.py` — extend the `worktree` subparser group with `prune` (with `--keep-branch`, `--force`, `--finalize` mutually exclusive group) and `repair`.
   40	- `tools/tasktool/schema_gen.py` — emit the new audit fields in the generated schema.
   41	- `tools/tasktool/tests/test_schema_gen.py` — assert the new fields appear in the emitted schema.
   42	- `tools/tasktool/tests/test_model.py` — round-trip the new fields.
   43	- `tools/tasktool/tests/test_validate.py` — type-check failures for the new fields.
   44	- `skills/finishing-a-development-branch/SKILL.md` — append the post-merge `tasktool worktree prune` step.
   45	
   46	---
   47	
   48	## Task -1: Preflight — confirm P5.S1 has shipped
   49	
   50	**Files:** none (read-only checks).
   51	
   52	- [ ] **Step 1: Confirm P5.S1 row is done and ratified**
   53	
   54	Run: `tools/tasktool/tasktool show P5.S1`
   55	Expected: `status: done` and `planning_status: ratified`.
   56	If not: STOP. Notify the coordinator that S1 is not yet shipped; P5.S2 cannot proceed.
   57	
   58	- [ ] **Step 2: Confirm P5.S2 is ratified**
   59	
   60	Run: `tools/tasktool/tasktool show P5.S2`
   61	Expected: `planning_status: ratified` and `depends_on: ["P5.S1"]`.
   62	If not: STOP and ask the coordinator to ratify.
   63	
   64	- [ ] **Step 3: Confirm the S1 CLI surface is present**
   65	
   66	Run: `tools/tasktool/tasktool worktree --help`
   67	Expected: `list`, `status`, `adopt` subcommands listed; exit 0.
   68	
   69	Run: `tools/tasktool/tasktool start --help`
   70	Expected: `--in-place`, `--adopt`, `--ad-hoc` flags listed.
   71	
   72	If either help text is missing flags or subcommands, STOP. The plan's assumed S1 contracts are absent and Task 5+ will fail.
   73	
   74	- [ ] **Step 4: Confirm baseline test suite is green on the current branch**
   75	
   76	Run: `python -m pytest tools/tasktool/tests -q` and `tools/tasktool/tasktool validate --strict-format`
   77	Expected: both exit 0. If not: STOP and notify the coordinator before starting S2 work.
   78	
   79	---
   80	
   81	## Task 0: Start the slice
   82	
   83	**Files:** none (tasktool state only).
   84	
   85	- [ ] **Step 1: Confirm row exists and is ratified**
   86	
   87	Run: `tools/tasktool/tasktool show P5.S2`
   88	Expected: row prints with `planning_status: ratified` and `depends_on: ["P5.S1"]`.
   89	
   90	- [ ] **Step 2: Mark slice in_progress**
   91	
   92	Run: `tools/tasktool/tasktool start P5.S2`
   93	Expected: exit 0; status becomes `in_progress`.
   94	
   95	- [ ] **Step 3: Run baseline tests**
   96	
   97	Run: `python -m pytest tools/tasktool/tests -q`
   98	Expected: PASS (treat any pre-existing failures as a blocker; do not proceed).
   99	
  100	---
  101	
  102	## Task 1: Add the three audit fields to the model
  103	
  104	**Files:**
  105	- Modify: `tools/tasktool/model.py` (the `Slice` dataclass around lines 35-51 and `CrossCutting` around lines 68-77).
  106	- Modify: `tools/tasktool/tests/test_model.py`.
  107	
  108	- [ ] **Step 1: Write the failing model round-trip test**
  109	
  110	Add to `tools/tasktool/tests/test_model.py`:
  111	
  112	```python
  113	def test_slice_audit_fields_default_to_none_and_false():
  114	    from tasktool.model import Slice
  115	    s = Slice(id="S1", title="t", created="2026-05-21")
  116	    assert s.worktree_pruned_at is None
  117	    assert s.worktree_prune_pending is False
  118	    assert s.worktree_prune_pending_at is None
  119	
  120	
  121	def test_cross_audit_fields_default_to_none_and_false():
  122	    from tasktool.model import CrossCutting
  123	    c = CrossCutting(id="X1", title="t", created="2026-05-21")
  124	    assert c.worktree_pruned_at is None
  125	    assert c.worktree_prune_pending is False
  126	    assert c.worktree_prune_pending_at is None
  127	```
  128	
  129	- [ ] **Step 2: Run to verify failure**
  130	
  131	Run: `python -m pytest tools/tasktool/tests/test_model.py -q -k audit`
  132	Expected: FAIL — `AttributeError` on `worktree_pruned_at`.
  133	
  134	- [ ] **Step 3: Add the fields**
  135	
  136	In `tools/tasktool/model.py`, after the existing `worktree_*` fields added by P5.S1 on `Slice` (immediately before `tasks: list[Task]`), add:
  137	
  138	```python
  139	    worktree_pruned_at: str | None = None
  140	    worktree_prune_pending: bool = False
  141	    worktree_prune_pending_at: str | None = None
  142	```
  143	
  144	Repeat on `CrossCutting` (after the P5.S1 `worktree_*` fields, before `refs`/`notes`).
  145	
  146	- [ ] **Step 4: Run to verify pass**
  147	
  148	Run: `python -m pytest tools/tasktool/tests/test_model.py -q -k audit`
  149	Expected: PASS.
  150	
  151	- [ ] **Step 5: Commit**
  152	
  153	```bash
  154	git add tools/tasktool/model.py tools/tasktool/tests/test_model.py
  155	git commit -m "P5.S2: add worktree prune audit fields to model"
  156	```
  157	
  158	---
  159	
  160	## Task 2: Round-trip the audit fields in serialize.py
  161	
  162	**Files:**
  163	- Modify: `tools/tasktool/serialize.py`.
  164	- Modify: `tools/tasktool/tests/test_serialize.py`.
  165	
  166	- [ ] **Step 1: Write the failing JSON round-trip test**
  167	
  168	Add to `tools/tasktool/tests/test_serialize.py`:
  169	
  170	```python
  171	def test_serialize_audit_fields_round_trip(tmp_path):
  172	    from tasktool.model import Project, Phase, Slice
  173	    from tasktool.serialize import save_project, load_project
  174	    p = Project(project="demo")
  175	    ph = Phase(id="P5", title="t", created="2026-05-21")
  176	    s = Slice(id="S2", title="t", created="2026-05-21",
  177	              worktree_pruned_at="2026-05-22",
  178	              worktree_prune_pending=True,
  179	              worktree_prune_pending_at="2026-05-22")
  180	    ph.slices.append(s)
  181	    p.phases.append(ph)
  182	    path = tmp_path / "tasklist.json"
  183	    save_project(p, path)
  184	    p2 = load_project(path)
  185	    s2 = p2.phases[0].slices[0]
  186	    assert s2.worktree_pruned_at == "2026-05-22"
  187	    assert s2.worktree_prune_pending is True
  188	    assert s2.worktree_prune_pending_at == "2026-05-22"
  189	```
  190	
  191	Plus a parallel test for `CrossCutting`.
  192	
  193	- [ ] **Step 2: Run to verify failure**
  194	
  195	Run: `python -m pytest tools/tasktool/tests/test_serialize.py -q -k audit`
  196	Expected: FAIL — fields missing from emitted JSON / dropped on load.
  197	
  198	- [ ] **Step 3: Extend serialize.py load path**
  199	
  200	The current serializer uses `asdict(p)` and emits *every* dataclass field unconditionally (`tools/tasktool/serialize.py:11-23`). Therefore the **emit path needs no edits** — once Task 1 adds the fields to the dataclasses, they appear in canonical output automatically.
  201	
  202	The **load path (`from_dict`)** is keyword-based and must be taught the new keys. In `_slice` (lines 41-56) add three kwargs to the `Slice(...)` constructor call:
  203	
  204	```python
  205	            worktree_pruned_at=sd.get("worktree_pruned_at"),
  206	            worktree_prune_pending=sd.get("worktree_prune_pending", False),
  207	            worktree_prune_pending_at=sd.get("worktree_prune_pending_at"),
  208	```
  209	
  210	(If P5.S1 already added `worktree_path`/`worktree_branch`/`worktree_in_place` kwargs here, place the new three next to them.)
  211	
  212	In `_cross` (lines 70-78) add the same three kwargs to the `CrossCutting(...)` constructor call.
  213	
  214	- [ ] **Step 4: Run to verify pass**
  215	
  216	Run: `python -m pytest tools/tasktool/tests/test_serialize.py -q`
  217	Expected: PASS.
  218	
  219	- [ ] **Step 5: Normalise the existing tasklist**
  220	
  221	Because `asdict` now emits the three new keys on every slice and every cross-cutting row, the on-disk `docs/tasklist.json` is no longer in canonical form. Re-canonicalise:
  222	
  223	```bash
  224	tools/tasktool/tasktool validate --normalise
  225	tools/tasktool/tasktool validate --strict-format
  226	```
  227	
  228	Expected: first command rewrites `docs/tasklist.json` with the new default keys on every row; second command exits 0.
  229	
  230	Inspect the diff: every slice should now contain `"worktree_pruned_at": null`, `"worktree_prune_pending": false`, `"worktree_prune_pending_at": null`. Every cross-cutting row likewise. No semantic changes.
  231	
  232	- [ ] **Step 6: Commit (includes the tasklist re-normalisation)**
  233	
  234	```bash
  235	git add tools/tasktool/serialize.py tools/tasktool/tests/test_serialize.py docs/tasklist.json
  236	git commit -m "P5.S2: round-trip worktree prune audit fields"
  237	```
  238	
  239	---
  240	
  241	## Task 3: Validate the new audit fields
  242	
  243	**Files:**
  244	- Modify: `tools/tasktool/validate.py` (extend `_check_slice` around lines 77-95 and `_check_cross` around lines 110-115).
  245	- Modify: `tools/tasktool/tests/test_validate.py`.
  246	
  247	- [ ] **Step 1: Write the failing validation tests**
  248	
  249	Add to `tools/tasktool/tests/test_validate.py`:
  250	
  251	```python
  252	def test_validate_rejects_pending_without_at_timestamp():
  253	    from tasktool.model import Project, Phase, Slice
  254	    from tasktool.validate import validate_project, ValidationError
  255	    p = Project(project="d")
  256	    ph = Phase(id="P1", title="t", created="2026-05-21")
  257	    s = Slice(id="S1", title="t", created="2026-05-21",
  258	              worktree_prune_pending=True,
  259	              worktree_prune_pending_at=None)
  260	    ph.slices.append(s)
  261	    p.phases.append(ph)
  262	    import pytest
  263	    with pytest.raises(ValidationError, match="worktree_prune_pending"):
  264	        validate_project(p)
  265	
  266	
  267	def test_validate_rejects_pending_at_without_pending_flag():
  268	    from tasktool.model import Project, Phase, Slice
  269	    from tasktool.validate import validate_project, ValidationError
  270	    p = Project(project="d")
  271	    ph = Phase(id="P1", title="t", created="2026-05-21")
  272	    s = Slice(id="S1", title="t", created="2026-05-21",
  273	              worktree_prune_pending=False,
  274	              worktree_prune_pending_at="2026-05-22")
  275	    ph.slices.append(s)
  276	    p.phases.append(ph)
  277	    import pytest
  278	    with pytest.raises(ValidationError, match="worktree_prune_pending_at"):
  279	        validate_project(p)
  280	
  281	
  282	def test_validate_accepts_worktree_pruned_at_alone():
  283	    from tasktool.model import Project, Phase, Slice
  284	    from tasktool.validate import validate_project
  285	    p = Project(project="d")
  286	    ph = Phase(id="P1", title="t", created="2026-05-21")
  287	    s = Slice(id="S1", title="t", created="2026-05-21",
  288	              worktree_pruned_at="2026-05-22")
  289	    ph.slices.append(s)
  290	    p.phases.append(ph)
  291	    validate_project(p)  # no raise
  292	
  293	
  294	def test_validate_rejects_bad_pruned_at_date():
  295	    from tasktool.model import Project, Phase, Slice
  296	    from tasktool.validate import validate_project, ValidationError
  297	    p = Project(project="d")
  298	    ph = Phase(id="P1", title="t", created="2026-05-21")
  299	    s = Slice(id="S1", title="t", created="2026-05-21",
  300	              worktree_pruned_at="not-a-date")
  301	    ph.slices.append(s)
  302	    p.phases.append(ph)
  303	    import pytest
  304	    with pytest.raises(ValidationError):
  305	        validate_project(p)
  306	```
  307	
  308	- [ ] **Step 2: Run to verify failure**
  309	
  310	Run: `python -m pytest tools/tasktool/tests/test_validate.py -q -k "pending or pruned_at"`
  311	Expected: FAIL — `worktree_prune_pending`/`worktree_pruned_at` not enforced.
  312	
  313	- [ ] **Step 3: Add validation in validate.py**
  314	
  315	In `tools/tasktool/validate.py`, extend `_check_slice` (after the existing date checks, after line 89):
  316	
  317	```python
  318	    _check_date(s.worktree_pruned_at, scope, "worktree_pruned_at")
  319	    _check_date(s.worktree_prune_pending_at, scope, "worktree_prune_pending_at")
  320	    if s.worktree_prune_pending and s.worktree_prune_pending_at is None:
  321	        raise ValidationError(
  322	            f"{scope}: worktree_prune_pending=True requires worktree_prune_pending_at"
  323	        )
  324	    if (not s.worktree_prune_pending) and s.worktree_prune_pending_at is not None:
  325	        raise ValidationError(
  326	            f"{scope}: worktree_prune_pending_at requires worktree_prune_pending=True"
  327	        )
  328	```
  329	
  330	Add the identical block to `_check_cross` (after line 115).
  331	
  332	- [ ] **Step 4: Run to verify pass**
  333	
  334	Run: `python -m pytest tools/tasktool/tests/test_validate.py -q`
  335	Expected: PASS.
  336	
  337	- [ ] **Step 5: Update schema generator**
  338	
  339	Open `tools/tasktool/schema_gen.py`. Find the slice property block (the one P5.S1 extended with `worktree_path`/`worktree_branch`). Add:
  340	
  341	```python
  342	        "worktree_pruned_at": {"type": ["string", "null"]},
  343	        "worktree_prune_pending": {"type": "boolean"},
  344	        "worktree_prune_pending_at": {"type": ["string", "null"]},
  345	```
  346	
  347	Repeat for cross-cutting properties.
  348	
  349	- [ ] **Step 6: Update schema-gen test**
  350	
  351	Add to `tools/tasktool/tests/test_schema_gen.py`:
  352	
  353	```python
  354	def test_schema_includes_prune_audit_fields():
  355	    from tasktool import schema_gen
  356	    schema = schema_gen.build_schema()
  357	    slice_props = schema["$defs"]["slice"]["properties"]
  358	    assert "worktree_pruned_at" in slice_props
  359	    assert "worktree_prune_pending" in slice_props
  360	    assert "worktree_prune_pending_at" in slice_props
  361	    cross_props = schema["$defs"]["cross"]["properties"]
  362	    assert "worktree_pruned_at" in cross_props
  363	    assert "worktree_prune_pending" in cross_props
  364	    assert "worktree_prune_pending_at" in cross_props
  365	```
  366	
  367	(If the existing schema-gen test file uses different paths into the schema dict, mirror those.)
  368	
  369	- [ ] **Step 7: Run all validate/schema tests**
  370	
  371	Run: `python -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_schema_gen.py -q`
  372	Expected: PASS.
  373	
  374	- [ ] **Step 8: Commit**
  375	
  376	```bash
  377	git add tools/tasktool/validate.py tools/tasktool/schema_gen.py tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_schema_gen.py
  378	git commit -m "P5.S2: validate worktree prune audit fields and emit in schema"
  379	```
  380	
  381	---
  382	
  383	## Task 4: Add git plumbing helpers in worktree.py
  384	
  385	**Files:**
  386	- Modify: `tools/tasktool/worktree.py`.
  387	- Create: `tools/tasktool/tests/test_worktree_prune.py` (only the plumbing-helper unit tests in this task; CLI tests come later).
  388	
  389	- [ ] **Step 1: Write failing tests for the helpers**
  390	
  391	Create `tools/tasktool/tests/test_worktree_prune.py` starting with a small fixture builder. Place at top of file:
  392	
  393	```python
  394	from __future__ import annotations
  395	
  396	import subprocess
  397	import time
  398	from pathlib import Path
  399	
  400	import pytest
  401	
  402	
  403	def _run(cwd: Path, *args: str) -> str:
  404	    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True).stdout
  405	
  406	
  407	def _init_repo(root: Path) -> Path:
  408	    root.mkdir(parents=True, exist_ok=True)
  409	    _run(root, "git", "init", "-q", "-b", "main")
  410	    _run(root, "git", "config", "user.email", "t@example.com")
  411	    _run(root, "git", "config", "user.name", "t")
  412	    (root / "README").write_text("init\n")
  413	    _run(root, "git", "add", "README")
  414	    _run(root, "git", "commit", "-q", "-m", "init")
  415	    return root
  416	
  417	
  418	def _add_worktree(root: Path, branch: str, path: Path) -> Path:
  419	    _run(root, "git", "worktree", "add", "-b", branch, str(path))
  420	    return path
  421	```
  422	
  423	Then add helper tests:
  424	
  425	```python
  426	def test_is_inside_worktree_true(tmp_path):
  427	    from tasktool.worktree import is_inside_worktree
  428	    root = _init_repo(tmp_path / "r")
  429	    wt = _add_worktree(root, "feat", tmp_path / "r" / ".worktrees" / "wt")
  430	    assert is_inside_worktree(wt) is True
  431	    assert is_inside_worktree(root) is False
  432	
  433	
  434	def test_working_tree_dirty_detects_uncommitted_and_untracked(tmp_path):
  435	    from tasktool.worktree import working_tree_dirty
  436	    root = _init_repo(tmp_path / "r")
  437	    assert working_tree_dirty(root) == (False, [])
  438	    (root / "new.txt").write_text("x")
  439	    dirty, files = working_tree_dirty(root)
  440	    assert dirty is True
  441	    assert "new.txt" in files
  442	
  443	
  444	def test_working_tree_dirty_flags_stashes_attributable_to_worktree(tmp_path):
  445	    """Spec §5.3: refuse 'stash entries attributable to the worktree'.
  446	
  447	    Stashes in git are global to the repository; we cannot attribute them to a
  448	    specific linked worktree, but `git stash list` records the BRANCH at the
  449	    time of stash. A stash made on a different branch is NOT attributable to
  450	    this worktree and must NOT be flagged.
  451	    """
  452	    from tasktool.worktree import working_tree_dirty
  453	    root = _init_repo(tmp_path / "r")
  454	    # Create another branch and stash on it.
  455	    _run(root, "git", "checkout", "-q", "-b", "other")
  456	    (root / "scratch").write_text("x")
  457	    _run(root, "git", "add", "scratch")
  458	    _run(root, "git", "stash", "push", "-u", "-m", "unrelated")
  459	    # Back to main; this worktree's branch is now `main`. The stash above
  460	    # belongs to `other`, not to us, and should NOT be flagged.
  461	    _run(root, "git", "checkout", "-q", "main")
  462	    dirty, files = working_tree_dirty(root)
  463	    assert dirty is False, f"unrelated stash flagged dirty: {files}"
  464	
  465	
  466	def test_working_tree_dirty_flags_own_branch_stash(tmp_path):
  467	    from tasktool.worktree import working_tree_dirty
  468	    root = _init_repo(tmp_path / "r")
  469	    (root / "scratch").write_text("x")
  470	    _run(root, "git", "add", "scratch")
  471	    _run(root, "git", "stash", "push", "-u", "-m", "ours")
  472	    dirty, files = working_tree_dirty(root)
  473	    assert dirty is True
  474	    assert any("stash" in f.lower() for f in files)
  475	
  476	
  477	def test_branch_is_merged(tmp_path):
  478	    from tasktool.worktree import branch_is_merged
  479	    root = _init_repo(tmp_path / "r")
  480	    wt = _add_worktree(root, "feat", tmp_path / "r" / ".worktrees" / "wt")
  481	    (wt / "f").write_text("x")
  482	    _run(wt, "git", "add", "f")
  483	    _run(wt, "git", "commit", "-q", "-m", "f")
  484	    assert branch_is_merged(root, branch="feat", into="main") is False
  485	    _run(root, "git", "merge", "--no-ff", "-q", "-m", "m", "feat")
  486	    assert branch_is_merged(root, branch="feat", into="main") is True
  487	
  488	
  489	def test_head_age_seconds(tmp_path):
  490	    from tasktool.worktree import head_age_seconds
  491	    root = _init_repo(tmp_path / "r")
  492	    age = head_age_seconds(root)
  493	    assert age >= 0
  494	    assert age < 60  # commit was just made
  495	
  496	
  497	def test_path_is_registered_worktree(tmp_path):
  498	    from tasktool.worktree import path_is_registered_worktree
  499	    root = _init_repo(tmp_path / "r")
  500	    wt = _add_worktree(root, "feat", tmp_path / "r" / ".worktrees" / "wt")
  501	    assert path_is_registered_worktree(root, wt) is True
  502	    assert path_is_registered_worktree(root, tmp_path / "nope") is False
  503	
  504	
  505	def test_branch_exists(tmp_path):
  506	    from tasktool.worktree import branch_exists
  507	    root = _init_repo(tmp_path / "r")
  508	    assert branch_exists(root, "main") is True
  509	    assert branch_exists(root, "nope") is False
  510	```
  511	
  512	- [ ] **Step 2: Run to verify failure**
  513	
  514	Run: `python -m pytest tools/tasktool/tests/test_worktree_prune.py -q`
  515	Expected: FAIL — `ImportError` on each helper.
  516	
  517	- [ ] **Step 3: Implement helpers in worktree.py**
  518	
  519	Append to `tools/tasktool/worktree.py`:
  520	
  521	```python
  522	def is_inside_worktree(path: Path) -> bool:
  523	    """True iff `path` lies inside a linked (non-primary) git worktree.
  524	
  525	    Implementation: `git rev-parse --git-dir` vs `--git-common-dir`.
  526	    """
  527	    try:
  528	        gd = subprocess.run(
  529	            ["git", "rev-parse", "--absolute-git-dir"],
  530	            cwd=path, text=True, capture_output=True, check=True,
  531	        ).stdout.strip()
  532	        gcd = subprocess.run(
  533	            ["git", "rev-parse", "--git-common-dir"],
  534	            cwd=path, text=True, capture_output=True, check=True,
  535	        ).stdout.strip()
  536	        gcd_abs = gcd if Path(gcd).is_absolute() else str((path / gcd).resolve())
  537	        return Path(gd).resolve() != Path(gcd_abs).resolve()
  538	    except subprocess.CalledProcessError:
  539	        return False
  540	
  541	
  542	def working_tree_dirty(root: Path) -> tuple[bool, list[str]]:
  543	    """Return (dirty, offending_items).
  544	
  545	    Spec §5.3 guard: "no uncommitted, untracked, or stashed changes in the
  546	    worktree". Sources of dirtiness:
  547	      1. `git status --porcelain` on the worktree (tracked + untracked).
  548	      2. `git stash list` entries whose recorded branch matches the worktree's
  549	         current branch. Stash entries are repo-global but each row's message
  550	         records "WIP on <branch>:" or "On <branch>:"; we attribute by branch.
  551	         Stashes recorded on an UNRELATED branch are not the worktree's problem
  552	         and are NOT flagged.
  553	    """
  554	    items: list[str] = []
  555	    status = _git(root, "status", "--porcelain", check=False).stdout.splitlines()
  556	    items.extend(line[3:] for line in status if line.strip())
  557	
  558	    branch = git_current_branch(root)
  559	    if branch:
  560	        stash = _git(root, "stash", "list", check=False).stdout.splitlines()
  561	        # Each line looks like: "stash@{0}: WIP on feat: 1234abcd msg"
  562	        # or "stash@{0}: On feat: msg".
  563	        marker_wip = f"WIP on {branch}:"
  564	        marker_on = f"On {branch}:"
  565	        for line in stash:
  566	            if marker_wip in line or marker_on in line:
  567	                items.append(f"stash: {line}")
  568	    return (bool(items), items)
  569	
  570	
  571	def branch_is_merged(root: Path, *, branch: str, into: str) -> bool:
  572	    """True iff `branch` is reachable from `into` (a strict ancestor or equal)."""
  573	    res = _git(root, "merge-base", "--is-ancestor", branch, into, check=False)
  574	    return res.returncode == 0
  575	
  576	
  577	def head_age_seconds(root: Path) -> float:
  578	    """Seconds since the worktree HEAD commit's committer date."""
  579	    out = _git(root, "log", "-1", "--format=%ct", "HEAD").stdout.strip()
  580	    return max(0.0, time.time() - float(out))
  581	
  582	
  583	def path_is_registered_worktree(root: Path, path: Path) -> bool:
  584	    """True iff `path` (resolved) is in `git worktree list --porcelain` output."""
  585	    target = path.resolve()
  586	    for wt_path, _branch in worktree_roots(root):
  587	        if wt_path == target:
  588	            return True
  589	    return False
  590	
  591	
  592	def branch_exists(root: Path, branch: str) -> bool:
  593	    res = _git(root, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False)
  594	    return res.returncode == 0
  595	
  596	
  597	def git_worktree_remove(root: Path, path: Path, *, force: bool = False) -> None:
  598	    args = ["worktree", "remove"]
  599	    if force:
  600	        args.append("--force")

[truncated: 979 additional lines]

## Context Previews

### docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md

    1	# P5 — Tasktool-owned worktree lifecycle & `using-git-worktrees` skill collapse
    2	
    3	**Date:** 2026-05-21
    4	**Phase ID:** P5
    5	**Status:** spec
    6	**Source material:** `docs/notes/2026-05-21-P5-using-git-worktrees-audit.md`, `docs/notes/2026-05-21-P5-worktree-lifecycle-feedback.md`
    7	
    8	---
    9	
   10	## 1. Problem
   11	
   12	Telemetry attributes roughly a third of session tokens in implementation-heavy work to the `using-git-worktrees` skill. The audit (see source) traces the cost to **repeated agent cognition**, not to skill bloat per se:
   13	
   14	- Subagents reload the skill and re-run Step 0 even when their cwd is already inside a linked worktree.
   15	- Every session re-derives the worktree directory, branch name, and naming convention from filesystem state and reflog history, because no per-project authority records the chosen convention.
   16	- The skill describes a four-branch decision tree (native tool vs fallback, multiple candidate dirs, submodule guard, in-place opt-out) that the agent walks through on every load.
   17	- In the audited multistore project the skill's assumptions only partially match reality — three ignored worktree dirs exist, only one is used, none are documented, and `git worktree list` shows zero live worktrees despite a reflog full of past `worktree-p13-*` merges. Drift between skill assumptions and project state guarantees re-derivation.
   18	
   19	The root cause is **ownership**. Worktree lifecycle is currently the agent's responsibility, mediated by prose. Tasktool already knows everything the agent re-derives — slice ID, slug, authoritative branch, repo root, lifecycle state, whether the work is implementation-bound — but does not own the worktree. This spec moves that ownership to tasktool.
   20	
   21	## 2. Thesis
   22	
   23	**P5 is not "make the skill shorter."** Shrinking the skill is a side effect. The work is to **remove the recurring decision from agent cognition** and make tasktool the lifecycle authority for worktrees. Once that is true, the skill collapses naturally to a thin pointer and a subagent early-exit.
   24	
   25	## 3. Goals
   26	
   27	1. **Authority shift.** Tasktool creates, adopts, tracks, and cleans up worktrees. The skill stops describing how to do any of those things.
   28	2. **Deterministic convention.** One canonical path (`.worktrees/worktree-<id>-<slug>`), one branch name (matches dir name), one `.gitignore` entry, enforced by the installer.
   29	3. **Drift elimination.** Slice state and worktree state are co-located in `tasklist.json`. Stale worktrees cannot accumulate silently; missing worktrees cannot be papered over.
   30	4. **Subagent token reduction.** Dispatched subagents already inside a linked worktree skip the skill entirely.
   31	5. **Native-harness coexistence.** When a harness creates its own worktree (e.g. `EnterWorktree`), tasktool adopts and tracks rather than fighting.
   32	
   33	## 4. Non-goals
   34	
   35	- Multi-worktree-per-slice. One slice → one worktree.
   36	- Remote-worktree management or cross-project worktree sharing.
   37	- Per-harness worktree directories. `.claude/worktrees/` and `.codex/worktrees/` are deprecated; the installer warns on detection but performs no automatic migration. Removal of the legacy paths is scheduled one minor version after P5 ships.
   38	- Replacing `git worktree` for ad-hoc human use outside the slice model. `tasktool worktree …` is slice-scoped tooling, not a generic git wrapper.
   39	
   40	## 5. Design
   41	
   42	### 5.1 Canonical layout
   43	
   44	- **Location:** `.worktrees/` at the authoritative repo root. Always git-ignored. The installer adds the entry if absent.
   45	- **Per-slice path:** `.worktrees/worktree-<id-slug>-<title-slug>`. See the canonical naming function below.
   46	- **Branch name:** identical to the directory base name. Eliminates the path/branch ambiguity that prune logic would otherwise face.
   47	
   48	#### Canonical naming function (normative)
   49	
   50	```
   51	worktree_name(id, title) =
   52	    "worktree-" + slugify_id(id) + "-" + slugify_title(title)
   53	
   54	slugify_id(id):
   55	    lowercase(id)
   56	    replace "." with "-"
   57	    strip any character not in [a-z0-9-]
   58	    collapse repeated "-" into single "-"
   59	    strip leading/trailing "-"
   60	
   61	slugify_title(title):
   62	    lowercase(title)
   63	    replace whitespace and "_" with "-"
   64	    strip any character not in [a-z0-9-]
   65	    collapse repeated "-" into single "-"
   66	    strip leading/trailing "-"
   67	    truncate to 40 characters at a "-" boundary if longer
   68	```
   69	
   70	Worked examples:
   71	
   72	| ID      | Title                                  | Directory & branch                                        |
   73	|---------|----------------------------------------|-----------------------------------------------------------|
   74	| `P5.S1` | "Tasktool worktree lifecycle core"     | `worktree-p5-s1-tasktool-worktree-lifecycle-core`         |
   75	| `X42`   | "Hotfix: shim drift"                   | `worktree-x42-hotfix-shim-drift`                          |
   76	| `P13.S2`| "Checkout rewrite"                     | `worktree-p13-s2-checkout-rewrite`                        |
   77	
   78	**Collision handling.** If the computed path or branch already exists and is not the recorded worktree for this slice, `start` fails with repair guidance (see §5.3 reuse rules). Tasktool never silently appends a suffix.
   79	- **Legacy paths:** `.claude/worktrees/`, `.codex/worktrees/`, and the global `~/.config/superstar/worktrees/<project>` path are deprecated. Installer warns on detection; removal one minor version after this phase ships.
   80	
   81	### 5.2 Schema additions (`docs/tasklist.json`)
   82	
   83	Each slice (and each cross-cutting item that runs implementation work) gains two optional fields:
   84	
   85	```json
   86	{
   87	  "worktree_path": ".worktrees/worktree-p5-s1-tasktool-worktree-core",
   88	  "worktree_branch": "worktree-p5-s1-tasktool-worktree-core"
   89	}
   90	```
   91	
   92	- Both fields default to `null`. Existing entries are not rewritten; `tasktool start` backfills on first invocation.
   93	- **Both** are stored (not just path) because prune guards need a stable branch reference even if the directory has been manually deleted, and start needs a stable path even if the branch has been force-renamed.
   94	- An `--in-place` start records `worktree_path: null` plus a `worktree_in_place: true` audit marker on the slice, so a later `close` does not interpret missing-worktree as broken state.
   95	- Additional audit fields written by lifecycle commands: `worktree_pruned_at` (set by successful `prune` / `prune --finalize`), `worktree_prune_pending: true` and `worktree_prune_pending_at` (set by prune-from-inside, cleared by `--finalize`). All are optional and null/absent by default.
   96	
   97	### 5.3 Tasktool CLI surface
   98	
   99	#### `tasktool start <id> [--in-place | --adopt <path>]` &nbsp;·&nbsp; `tasktool start --ad-hoc <slug>`
  100	
  101	Two syntaxes. The first takes a known tasklist ID. The second omits `<id>` because the ID is allocated by tasktool from the cross-cutting namespace as part of the call.
  102	
  103	Default behavior: create `.worktrees/worktree-<id>-<slug>` on a branch of the same name (forked from the slice's parent branch per existing tasktool rules), set slice → `in_progress`, record `worktree_path` and `worktree_branch`, print the `cd` line for the user.
  104	
  105	**Idempotent reuse rules.** If `worktree_path` is already recorded, tasktool checks the live state and chooses:
  106	
  107	| State | Behavior |
  108	|-------|----------|
  109	| Path exists, is a linked worktree, branch matches | Print the `cd` line. No-op. |
  110	| Path missing entirely, branch missing | Fail with repair guidance: `tasktool worktree repair <id>` will recreate from recorded fields. |
  111	| Path missing, branch still present | Fail with repair guidance pointing at `tasktool worktree adopt <id> <new-path>` or `tasktool worktree repair <id>`. |
  112	| Path present but not a linked worktree (e.g. plain dir) | Fail. Do not overwrite. Suggest `tasktool worktree prune <id> --force` then re-`start`. |
  113	| Path present, branch mismatched | Fail. This is genuinely ambiguous — refuse rather than guess. |
  114	
  115	Tasktool never silently recreates over ambiguous state. Repair is always an explicit command.
  116	
  117	**Flags:**
  118	- `--in-place` — explicit opt-out for planning/spec slices that do not touch code. Sets the `worktree_in_place` audit marker; subsequent `close` will not search for a worktree.
  119	- `--adopt <path>` — record an externally-created worktree (e.g. one created by `EnterWorktree`). Tasktool verifies the path is a linked worktree and that its branch is appropriate, then stores both fields. Auto-detect: if the caller's cwd is already inside a linked worktree of the parent repo, `start` switches to adopt mode automatically and uses the detected path.
  120	- `--ad-hoc <slug>` — throwaway worktrees for hotfixes / exploration outside a phase plan. Allocates a normal cross-cutting `X<n>` row (using existing `tasktool create cross` machinery and the existing `X\d+` ID grammar — no new ID family, no schema change to `archived_cross_cutting`), with `status: in_progress`, `title: "Ad-hoc: <slug>"`, `notes: "ad-hoc"`, and the standard `worktree_path` / `worktree_branch` fields. The row uses a deliberately non-default close path so worktree fields survive long enough for prune to run:
  121	   1. `tasktool close <Xn> --no-archive` — required for ad-hoc rows. Flips status to `done` and leaves the row in `cross_cutting` with `worktree_path` / `worktree_branch` intact. **Defaulting `close` to auto-archive (current behavior for cross-cutting rows) would delete the row before prune could find it; the spec requires `--no-archive` rather than changing the existing default.**
  122	   2. `tasktool worktree prune <Xn>` — standard three-guard prune; nulls worktree fields and records `worktree_pruned_at`.
  123	   3. `tasktool archive-cross <Xn>` — archives the now-pruned row via the existing workflow.
  124	
  125	  Ad-hoc rows are tagged with `notes: "ad-hoc"` so `tasktool list` can hide them by default (visible under `tasktool list --all`). The skill / `tasklist-discipline` doc spells out the three-step sequence; tasktool itself does not enforce the ordering beyond the existing close/archive command surface.
  126	
  127	**Subagent guard.** Tasktool refuses `start` when any of the following signals indicate the caller is a dispatched subagent. Signals are checked in this order; the first present wins:
  128	
  129	1. `SUPERSTAR_SUBAGENT_ROLE` env var set to any non-empty value. Set by the Superstar shim when a coordinator dispatches a subagent via the Claude `Task` tool or Codex `subagent` equivalent. This is the supported, harness-set signal.
  130	2. `CLAUDE_AGENT_ROLE` env var set to any value other than `coordinator` or `main`. Forward-compat hook for harness-native subagent signals when those become available.
  131	3. `SUPERSTAR_FORCE_SUBAGENT=1` env var. Test-only override; documented and used by P5.S3 fixtures.
  132	
  133	On any positive signal, `start` exits non-zero with: `"Subagents must inherit the parent's worktree; call the parent or 'cd' into the existing recorded path: <worktree_path>."`
  134	
  135	**Absence of all three signals is treated as "not a subagent."** Tasktool will not infer subagent status from parent-process fingerprinting, cwd heuristics, or pty introspection — those produce too many false positives in plain shells. This means a coordinator that loses its env (e.g. via `env -i`) will look like a top-level invocation and `start` will proceed; the `tasklist-discipline` doc rule is the load-bearing guard for that case and is documented as such.
  136	
  137	`SUPERSTAR_SUBAGENT_ROLE` is added to the Claude shim and Codex shim as part of P5.S3.
  138	
  139	#### `tasktool close <id>` — unchanged worktree semantics
  140	
  141	**`tasktool close` does not touch the worktree.** Its existing meaning — review-gated slice closure run at slice boundary, before merge-back — is preserved unchanged. The slice's `worktree_path` / `worktree_branch` / `worktree_in_place` fields are retained verbatim across `close`, so `worktree list` continues to see the slice's worktree as a closed-but-retained row until it is explicitly pruned post-merge.
  142	
  143	This split is deliberate. `close` runs *before* merge-back in the established workflow (see `[[executing-plans]]`, `[[finishing-a-development-branch]]`), so it cannot enforce a merged-branch guard without breaking that workflow. Destructive cleanup is a separate operation owned by `tasktool worktree prune`.
  144	
  145	#### `tasktool worktree prune <id> [--keep-branch | --force]`
  146	
  147	Removes the recorded worktree. Invoked post-merge (typically from `[[finishing-a-development-branch]]` after the slice's branch lands on the authoritative parent). Guards (three, all durably observable from filesystem and tasklist state):
  148	
  149	1. Slice status is `done` (i.e. `close` has already run and the review gates passed).
  150	2. Branch is merged into the slice's authoritative parent (e.g. `main`).
  151	3. Working tree is clean: no uncommitted, untracked, or stashed changes in the worktree.
  152	
  153	If any guard fails, prune is refused with a precise reason. **`--force` overrides prune guards only.** It does not affect `tasktool close`, slice status, review gates, dependency gates, or any other lifecycle concern — those keep their existing semantics. `--force` is the destructive escape hatch for the cleanup step alone.
  154	
  155	**In-flight subagent detection is explicitly out of scope for P5.** A robust check would require a tasktool-managed lease/lock file written on subagent dispatch and cleared on exit. That mechanism is deferred to a follow-up (tracked under §8). For P5, prune relies on the clean-tree guard plus operator discipline: subagents that exit cleanly leave a clean tree; subagents that are abandoned leave dirty/untracked state that the clean-tree guard catches. Prune emits a non-blocking informational note when it observes a worktree whose `HEAD` has moved within the last 60 seconds, but does not refuse on that basis.
  156	
  157	`--keep-branch` removes the worktree directory but leaves the branch in place (useful when the branch will be referenced by tags/releases).
  158	
  159	After a successful prune (or `--force` prune), tasktool nulls `worktree_path` and `worktree_branch` on the slice and records a `worktree_pruned_at` audit timestamp. `worktree_in_place: true` slices have no worktree to prune; `prune` is a no-op that records the audit timestamp.
  160	
  161	**Prune from inside the worktree being removed.** Detected via `git rev-parse --git-dir` vs `--git-common-dir`. Tasktool:
  162	1. Performs every non-destructive action (guards, audit log).
  163	2. Sets a `worktree_prune_pending: true` marker on the slice (and records `worktree_prune_pending_at: <timestamp>`), pinning the staged path so `--finalize` can verify it later. Worktree fields are **not** nulled at this step.
  164	3. Skips the `git worktree remove` call.
  165	4. Prints the exact follow-up command to chat: `cd <authoritative-root> && git worktree remove <path> && tasktool worktree prune <id> --finalize`.
  166	
  167	`--finalize` (run from outside the worktree) performs the field nulling and audit timestamp. It is guard-light (does not re-run the three destructive guards) but enforces three preconditions before mutating state:
  168	
  169	1. `worktree_prune_pending: true` is set on the slice. Without it, `--finalize` refuses with: "no pending prune to finalize; run `tasktool worktree prune <id>` first."
  170	2. The previously recorded `worktree_path` is no longer a registered git worktree (per `git worktree list --porcelain`).
  171	3. No directory exists at the previously recorded `worktree_path`.
  172	
  173	If preconditions 2 or 3 fail, `--finalize` refuses with the specific reason and does not null the fields — this prevents hiding a still-live or partially-removed worktree from `worktree list`. On success, `--finalize` clears `worktree_prune_pending`, nulls `worktree_path` and `worktree_branch`, and sets `worktree_pruned_at`.
  174	
  175	No chdir magic, no re-exec.
  176	
  177	#### `tasktool worktree <subcommand>`
  178	
  179	Slice-scoped, not a generic git-worktree wrapper. All subcommands except `list` take a slice ID.
  180	
  181	- `tasktool worktree list [--all]` — by default, lists every slice that currently has a non-null `worktree_path` (active + closed-but-not-yet-pruned). `--all` additionally includes `--in-place` slices and slices with a `worktree_pruned_at` audit timestamp but no surviving fields. Output columns: ID, status, path, branch, health (`live` / `missing-path` / `missing-branch` / `mismatched` / `in-place` / `pruned`).
  182	- `tasktool worktree status <id>` — detailed health for one slice's worktree: path, branch, ahead/behind parent, dirty state, last activity.
  183	- `tasktool worktree adopt <id> <path>` — record an existing linked worktree against a slice. Used when the harness or human created the worktree out-of-band, or when repairing state after a path rename.
  184	- `tasktool worktree prune <id> [--keep-branch | --force | --finalize]` — remove the recorded worktree. Applies the three guards described under `tasktool worktree prune` above (slice-done, branch-merged, clean-tree). `--force` overrides prune guards only; `--keep-branch` removes the directory but leaves the branch; `--finalize` records the post-prune field nulling without re-running guards when the directory was already removed externally (the prune-from-inside two-step).
  185	- `tasktool worktree repair <id>` — recreate a missing worktree from recorded `worktree_path` + `worktree_branch` fields. Refuses if the branch is also missing (use `adopt` after creating one manually, or restart the slice).
  186	
  187	### 5.3.1 Lifecycle state table
  188	
  189	Persisted field values for each command, assuming the slice was created normally (not `--in-place` or `--ad-hoc` unless noted).
  190	
  191	| Command | `worktree_path` | `worktree_branch` | `worktree_in_place` | `worktree_pruned_at` | Disk state |
  192	|---|---|---|---|---|---|
  193	| `start` (fresh) | recorded | recorded | absent | absent | linked worktree created |
  194	| `start` (idempotent reuse, consistent) | unchanged | unchanged | unchanged | unchanged | unchanged |
  195	| `start --in-place` | null | null | `true` | absent | nothing on disk |
  196	| `start --adopt <path>` | recorded (= path) | recorded (from path's branch) | absent | absent | linked worktree pre-existed |
  197	| `close` | unchanged | unchanged | unchanged | unchanged | unchanged |
  198	| `worktree prune` (success) | nulled | nulled | unchanged | set to now | worktree removed; branch removed unless `--keep-branch` |
  199	| `worktree prune` (prune-from-inside, before `--finalize`) | unchanged | unchanged | unchanged | absent | worktree still present; `worktree_prune_pending: true` set on slice |
  200	| `worktree prune --finalize` (preconditions met) | nulled | nulled | unchanged | set to now | (caller already removed the worktree); `worktree_prune_pending` cleared |

[truncated: 125 additional lines]
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
   14	    }
   15	  ],
   16	  "archived_phases": [
   17	    {
   18	      "archived_date": "2026-05-18",
   19	      "archived_path": "docs/archived-tasks/P2-tasktool-json-backed-task-management-cli.md",
   20	      "id": "P2",
   21	      "title": "tasktool: JSON-backed task management CLI"
   22	    },
   23	    {
   24	      "archived_date": "2026-05-19",
   25	      "archived_path": "docs/archived-tasks/P4-tasktool-coordination-and-lifecycle-auth.md",
   26	      "id": "P4",
   27	      "title": "Tasktool coordination and lifecycle authority"
   28	    },
   29	    {
   30	      "archived_date": "2026-05-19",
   31	      "archived_path": "docs/archived-tasks/P3-phase-planning-workflow.md",
   32	      "id": "P3",
   33	      "title": "Phase planning workflow"
   34	    },
   35	    {
   36	      "archived_date": "2026-05-20",
   37	      "archived_path": "docs/archived-tasks/P1-external-reviewer-work-historical.md",
   38	      "id": "P1",
   39	      "title": "External-reviewer work (historical)"
   40	    }
   41	  ],
   42	  "cross_cutting": [
   43	    {
   44	      "closed": "2026-05-18",
   45	      "created": "2026-05-18",
   46	      "id": "X1",
   47	      "notes": "Changed external-review default prompt transport from argv to stdin so the bundled Codex reviewer-agent receives prompts via codex exec '-' and avoids argv length failures.",
   48	      "refs": [],
   49	      "started": null,
   50	      "status": "done",
   51	      "title": "Default external-review prompt transport to stdin"
   52	    },
   53	    {
   54	      "closed": "2026-05-18",
   55	      "created": "2026-05-18",
   56	      "id": "X2",
   57	      "notes": "Added repo-local tools/tasktool/tasktool launcher, updated tasklist/project-setup docs to prefer it, and taught the pre-commit hook to use the repo-local launcher before falling back to a global tasktool shim.",
   58	      "refs": [],
   59	      "started": null,
   60	      "status": "done",
   61	      "title": "Add repo-local tasktool launcher"
   62	    },
   63	    {
   64	      "closed": "2026-05-19",
   65	      "created": "2026-05-19",
   66	      "id": "X3",
   67	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. External-review verdict parsing now accepts markdown-emphasized Overall Verdict headings such as **5. Overall Verdict** followed by ready/revise text.",
   68	      "refs": [
   69	        "skills/external-review/scripts/external-reviewer.py",
   70	        "skills/external-review/tests/test_heading_style_verdict.py"
   71	      ],
   72	      "started": null,
   73	      "status": "done",
   74	      "title": "Spot fix: parse bold external-review verdict headings"
   75	    },
   76	    {
   77	      "closed": "2026-05-19",
   78	      "created": "2026-05-19",
   79	      "id": "X4",
   80	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. Legacy markdown import now accepts fully-qualified slice IDs and additional cross-cutting forms including tagged done items, blocked cross rows coerced to ready, and archived cross rows treated as done.",
   81	      "refs": [
   82	        "tools/tasktool/importer.py"
   83	      ],
   84	      "started": null,
   85	      "status": "done",
   86	      "title": "Spot fix: broaden legacy tasklist importer compatibility"
   87	    },
   88	    {
   89	      "closed": "2026-05-19",
   90	      "created": "2026-05-19",
   91	      "id": "X5",
   92	      "notes": "User-requested hook update completed outside the normal workflow for speed. Adds Stop/SubagentStop finished-agent notifications, milestone message derivation from final agent text/transcript payloads, Hypr TTS config reuse with OPENAI_API_KEY fallback, and non-TTS ding fallbacks.\nSuperseded by X8: final-text milestone parsing was removed; agent hooks now emit generic dings and semantic spoken notifications come from tasktool status changes.",
   93	      "refs": [
   94	        "hooks/agent-finished",
   95	        "hooks/hooks.json",
   96	        "hooks/hooks-cursor.json",
   97	        "tests/claude-code/test-agent-finished-hook.sh"
   98	      ],
   99	      "started": null,
  100	      "status": "done",
  101	      "title": "Add finished-agent notification hook"
  102	    },
  103	    {
  104	      "closed": "2026-05-19",
  105	      "created": "2026-05-19",
  106	      "id": "X6",
  107	      "notes": "Codex startup skips Stop/SubagentStop notification hooks when hooks.json uses async=true; fix should preserve finished-agent notification behavior while avoiding unsupported async hook registration in Codex.\nSet finished-agent Stop/SubagentStop hook registrations to async=false for Codex compatibility. The hook now backgrounds real notification playback internally so synchronous hook registration returns quickly while dry-run tests remain foreground and deterministic.",
  108	      "refs": [
  109	        "hooks/hooks.json",
  110	        "hooks/agent-finished",
  111	        "tests/claude-code/test-hook-config.sh",
  112	        "tests/claude-code/test-agent-finished-hook.sh"
  113	      ],
  114	      "started": null,
  115	      "status": "done",
  116	      "title": "Fix Codex finished-agent hook compatibility"
  117	    },
  118	    {
  119	      "closed": "2026-05-19",
  120	      "created": "2026-05-19",
  121	      "id": "X7",
  122	      "notes": "Codex reported superstar/6.0.0 because the installable local marketplace payload under plugins/superstar still declared version 6.0.0 and the version bump audit did not track that embedded manifest.\n\nBumped the embedded Codex plugin payload manifest to 6.0.1 and added it to the version bump check. Reinstalled superstar@superstar-dev, then rebuilt the 6.0.1 runtime cache as a materialized copy of this checkout with .agents excluded so Codex sees the full skills/hooks tree while codex plugin list still reports installed/enabled. Final probe shows cache version 6.0.1, skills/hooks present, and no async-hook warning.",
  123	      "refs": [
  124	        ".version-bump.json",
  125	        "plugins/superstar/.codex-plugin/plugin.json",
  126	        ".agents/plugins/marketplace.json",
  127	        "tests/codex-plugin-sync/test-version-drift.sh",
  128	        "tests/codex-plugin-sync/test-local-marketplace.sh"
  129	      ],
  130	      "started": null,
  131	      "status": "done",
  132	      "title": "Fix Superstar Codex plugin payload version drift"
  133	    },
  134	    {
  135	      "closed": "2026-05-19",
  136	      "created": "2026-05-19",
  137	      "id": "X8",
  138	      "notes": "Move semantic spoken notifications to tasktool status transitions for ready/in_progress/blocked/done. Keep agent Stop/SubagentStop hooks as generic completion dings only, with different sound styles for Claude and Codex.\nAgent Stop/SubagentStop hooks now emit generic harness-specific dings only. Semantic spoken notifications moved to tasktool status events for ready, in_progress, blocked, and done, including create, set, close, block, unblock, and archive-phase paths.",
  139	      "refs": [
  140	        "hooks/agent-finished",
  141	        "tools/tasktool/notify.py",
  142	        "tools/tasktool/commands.py",
  143	        "tools/tasktool/tests/test_notify.py",
  144	        "tools/tasktool/tests/test_commands.py",
  145	        "tools/tasktool/tests/conftest.py",
  146	        "tests/claude-code/test-agent-finished-hook.sh"
  147	      ],
  148	      "started": null,
  149	      "status": "done",
  150	      "title": "Move semantic notifications from agent hooks to tasktool status changes"
  151	    },
  152	    {
  153	      "closed": "2026-05-19",
  154	      "created": "2026-05-19",
  155	      "id": "X9",
  156	      "notes": "Rapid tasktool status changes currently spawn independent notifier processes, causing overlapping TTS/audio. Add a single-audio queue with at most three queued tasktool events; overflow should collapse to a single 'multiple other events' summary and drop further items.\nAdded a file-backed notification queue shared by agent dings and tasktool TTS. Only one worker drains audio at a time. Queue capacity is three pending events; overflow keeps the first two pending items and replaces the rest with a single 'Multiple other events' summary, dropping further burst items while the summary remains queued.",
  157	      "refs": [
  158	        "tools/tasktool/notify.py",
  159	        "tools/tasktool/tests/test_notify.py"
  160	      ],
  161	      "started": null,
  162	      "status": "done",
  163	      "title": "Coalesce bursty tasktool audio notifications"
  164	    },
  165	    {
  166	      "closed": "2026-05-20",
  167	      "created": "2026-05-20",
  168	      "id": "X10",
  169	      "notes": "",
  170	      "refs": [
  171	        "docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md",
  172	        "docs/reviewer/x10-verdict-parser-claude-formatting-design-spec",
  173	        "docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md"
  174	      ],
  175	      "started": null,
  176	      "status": "done",
  177	      "title": "Harden external-review verdict parser and prompt against Claude formatting variants"
  178	    },
  179	    {
  180	      "closed": "2026-05-20",
  181	      "created": "2026-05-20",
  182	      "id": "X11",
  183	      "notes": "",
  184	      "refs": [
  185	        "docs/specs/2026-05-20-X11-global-external-reviewer-bridge-design.md",
  186	        "docs/reviewer/x11-global-external-reviewer-bridge-design-spec",
  187	        "docs/plans/2026-05-20-X11-global-external-reviewer-bridge.md",
  188	        "docs/reviewer/x11-global-external-reviewer-bridge-plan",
  189	        "docs/handoffs/2026-05-20-X11-global-external-reviewer-bridge-prompt.md"
  190	      ],
  191	      "started": "2026-05-20",
  192	      "status": "done",
  193	      "title": "Make external-review bridge global"
  194	    },
  195	    {
  196	      "closed": "2026-05-20",
  197	      "created": "2026-05-20",
  198	      "id": "X12",
  199	      "notes": "",
  200	      "refs": [

[truncated: 136 additional lines]

<!-- superstar-prompt:end -->