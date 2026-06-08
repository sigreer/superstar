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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p9-s1-quick-wins-kind-aware-depth-defaults

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md

Additional context files:
- docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md
- /tmp/p9s1-brief-context.md

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

### docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md

    1	# P9.S1 — Review-Pipeline Quick Wins Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Cut external-review cost by defaulting depth per kind, extending the resolution gate to all kinds, tiering reviewer models, trimming context guidance, and adding `stats --since` with a rounds-per-slice metric.
    6	
    7	**Architecture:** All behaviour changes live in `skills/external-review/scripts/external-reviewer.py` (CLI) and `skills/project-setup/scripts/reviewer-agent` (provider wrapper); guidance changes live in four SKILL.md files. Every CLI change is opt-out-preserving: explicit flags and unset env vars reproduce today's behaviour byte-for-byte.
    8	
    9	**Tech Stack:** Python 3 (stdlib only), bash, pytest (`skills/external-review/tests/`).
   10	
   11	**Spec:** `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md` (S1 section).
   12	
   13	**Scheduling:** `P9.S1` is ratified, has no `depends_on`, and gates `P9.S2`/`P9.S3` (both depend on it; S3 also depends on S2). Declared integration surfaces: `skills/external-review/scripts/external-reviewer.py`, `skills/external-review/SKILL.md`, `skills/project-setup/scripts/reviewer-agent`. No sibling slice may run in parallel with this one (`tasktool surface check P9` is clean because S2/S3 are serialized behind S1).
   14	
   15	---
   16	
   17	## Conventions used by every task
   18	
   19	- Repo root: `/home/simon/Dev/sigreer/skills/superstar` (work from an isolated worktree created via `superstar:using-git-worktrees`).
   20	- The module under test is loaded the way every existing test does it:
   21	
   22	```python
   23	from pathlib import Path
   24	import sys, importlib.util
   25	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
   26	sys.path.insert(0, str(SCRIPTS))
   27	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
   28	er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
   29	```
   30	
   31	- Test command: `python -m pytest skills/external-review/tests/<file> -q` from the repo root.
   32	- Line numbers below are anchors as of commit `b9babcf`; re-locate with the given grep if drifted.
   33	
   34	### Task 0: Start the slice
   35	
   36	- [ ] **Step 1: Mark the slice started**
   37	
   38	Run: `tasktool start P9.S1`
   39	Expected: exit 0; `tasktool show P9.S1` shows status `started`.
   40	
   41	---
   42	
   43	### Task 1: Kind-aware depth defaults
   44	
   45	**Files:**
   46	- Modify: `skills/external-review/scripts/external-reviewer.py` (argparse ~line 1851; main review path after the work-id check ~line 2445; round-entry construction — locate with `grep -n '"review_depth":' skills/external-review/scripts/external-reviewer.py`)
   47	- Test: `skills/external-review/tests/test_depth_defaults.py` (create)
   48	
   49	- [ ] **Step 1: Write the failing tests**
   50	
   51	Create `skills/external-review/tests/test_depth_defaults.py`:
   52	
   53	```python
   54	from pathlib import Path
   55	import sys, importlib.util
   56	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
   57	sys.path.insert(0, str(SCRIPTS))
   58	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
   59	er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
   60	
   61	
   62	def test_spec_defaults_standard():
   63	    assert er.resolve_review_depth(None, "spec") == "standard"
   64	
   65	
   66	def test_plan_defaults_standard():
   67	    assert er.resolve_review_depth(None, "plan") == "standard"
   68	
   69	
   70	def test_design_implementation_other_default_standard():
   71	    for kind in ("design", "implementation", "other"):
   72	        assert er.resolve_review_depth(None, kind) == "standard"
   73	
   74	
   75	def test_post_slice_defaults_thorough():
   76	    assert er.resolve_review_depth(None, "post-slice") == "thorough"
   77	
   78	
   79	def test_post_phase_defaults_thorough():
   80	    assert er.resolve_review_depth(None, "post-phase") == "thorough"
   81	
   82	
   83	def test_explicit_flag_wins_over_kind_default():
   84	    assert er.resolve_review_depth("exhaustive", "spec") == "exhaustive"
   85	    assert er.resolve_review_depth("standard", "post-slice") == "standard"
   86	
   87	
   88	def test_argparse_review_depth_default_is_none():
   89	    args = er.parse_args([
   90	        "review", "--kind", "spec", "--file", "x.md",
   91	    ])
   92	    assert args.review_depth is None
   93	```
   94	
   95	- [ ] **Step 2: Run tests to verify they fail**
   96	
   97	Run: `python -m pytest skills/external-review/tests/test_depth_defaults.py -q`
   98	Expected: FAIL — `AttributeError: ... has no attribute 'resolve_review_depth'`.
   99	
  100	- [ ] **Step 3: Implement the resolver and rewire the default**
  101	
  102	In `external-reviewer.py`, directly below the `DEPTH_DEFAULTS` dict (~line 1744), add:
  103	
  104	```python
  105	# Kind-aware depth defaults (P9.S1): post gates get sweeps by default,
  106	# planning gates stay cheap. Explicit --review-depth always wins.
  107	KIND_DEPTH_DEFAULTS = {
  108	    "post-slice": "thorough",
  109	    "post-phase": "thorough",
  110	}
  111	
  112	
  113	def resolve_review_depth(explicit: str | None, kind: str) -> str:
  114	    if explicit is not None:
  115	        return explicit
  116	    return KIND_DEPTH_DEFAULTS.get(kind, "standard")
  117	```
  118	
  119	Change the argparse line (~1851) from:
  120	
  121	```python
  122	    sp_review.add_argument("--review-depth", choices=["standard", "thorough", "exhaustive"],
  123	                        default="standard")
  124	```
  125	
  126	to:
  127	
  128	```python
  129	    sp_review.add_argument("--review-depth", choices=["standard", "thorough", "exhaustive"],
  130	                        default=None,
  131	                        help="Default: 'thorough' for post-slice/post-phase, 'standard' otherwise.")
  132	```
  133	
  134	In the review path of `main`, immediately after the `--work-id` requirement check (locate with `grep -n 'work-id is required' skills/external-review/scripts/external-reviewer.py`, ~line 2439-2445), add:
  135	
  136	```python
  137	    args.review_depth = resolve_review_depth(args.review_depth, args.kind)
  138	```
  139	
  140	Every downstream use (`plan_sweeps(depth=args.review_depth, ...)` twice, and the JSON emit `"review_depth": args.review_depth`) then sees the resolved value — verify with `grep -n 'args.review_depth' skills/external-review/scripts/external-reviewer.py` that all uses are after the resolution line.
  141	
  142	- [ ] **Step 4: Record `depth_resolved` in the chain manifest**
  143	
  144	Locate the round-entry dict construction (`grep -n '"diff_included"' skills/external-review/scripts/external-reviewer.py` — the dict that is appended to `manifest["rounds"]`). Add one key alongside the existing metadata keys:
  145	
  146	```python
  147	        "depth_resolved": args.review_depth,
  148	```
  149	
  150	- [ ] **Step 5: Add a manifest assertion to the test file**
  151	
  152	Append to `test_depth_defaults.py`. It uses the same subprocess harness as `tests/test_resolution_gate.py` (`_init_repo` builds a throwaway git repo with a `stub.sh` reviewer; `_run` invokes the script with `AGENT_REVIEWER_CMD` pointed at the stub):
  153	
  154	```python
  155	import subprocess, os, json
  156	
  157	
  158	def _init_repo(tmp_path):
  159	    repo = tmp_path / "repo"
  160	    repo.mkdir()
  161	    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
  162	    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
  163	    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
  164	    (repo / "plan.md").write_text("# plan\n")
  165	    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
  166	    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
  167	    reviewer = repo / "stub.sh"
  168	    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
  169	    reviewer.chmod(0o755)
  170	    return repo
  171	
  172	
  173	def _run(repo, *args):
  174	    env = os.environ.copy()
  175	    env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
  176	    return subprocess.run(
  177	        [sys.executable, str(SCRIPTS / "external-reviewer.py"), "review", *args],
  178	        cwd=repo, env=env, capture_output=True, text=True,
  179	    )
  180	
  181	
  182	def test_round_entry_records_depth_resolved(tmp_path):
  183	    repo = _init_repo(tmp_path)
  184	    r = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
  185	    assert r.returncode == 0, r.stderr
  186	    chains = list((repo / "docs" / "reviewer").glob("*/chain.json"))
  187	    assert len(chains) == 1
  188	    manifest = json.loads(chains[0].read_text())
  189	    assert manifest["rounds"][-1]["depth_resolved"] == "standard"
  190	```
  191	
  192	- [ ] **Step 6: Run tests to verify they pass**
  193	
  194	Run: `python -m pytest skills/external-review/tests/test_depth_defaults.py -q`
  195	Expected: PASS (all).
  196	
  197	- [ ] **Step 7: Check no existing tests regressed**
  198	
  199	Run: `python -m pytest skills/external-review/tests -q`
  200	Expected: PASS. `tests/test_sweep_planning.py` and `tests/test_review_depth.py` exercise `plan_sweeps` with explicit depth strings, so they are unaffected; any test constructing `parse_args` without `--review-depth` and asserting `"standard"` must be updated to assert `None` (find with `grep -rn 'review_depth' skills/external-review/tests/`).
  201	
  202	- [ ] **Step 8: Commit**
  203	
  204	```bash
  205	git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_depth_defaults.py
  206	git commit -m "P9.S1: kind-aware review-depth defaults (post gates thorough, planning gates standard)"
  207	```
  208	
  209	---
  210	
  211	### Task 2: Resolution gate for all kinds
  212	
  213	**Files:**
  214	- Modify: `skills/external-review/scripts/external-reviewer.py` (gate block ~line 2532; `--allow-missing-resolution` help ~line 1840)
  215	- Test: `skills/external-review/tests/test_resolution_gate_all_kinds.py` (create; model it on `tests/test_resolution_gate.py`)
  216	
  217	- [ ] **Step 1: Write the failing tests**
  218	
  219	Create `skills/external-review/tests/test_resolution_gate_all_kinds.py`, reusing the exact `_init_repo`/`_run` harness from `tests/test_resolution_gate.py` (copy those two helpers verbatim — the stub reviewer there emits `Overall verdict: revise`, which is what seeds the gate):
  220	
  221	```python
  222	from pathlib import Path
  223	import subprocess, sys, os
  224	
  225	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
  226	
  227	# _init_repo and _run: copy verbatim from tests/test_resolution_gate.py
  228	# (stub.sh emits "Overall verdict: revise"; _run sets AGENT_REVIEWER_CMD).
  229	
  230	
  231	def test_spec_round2_refused_without_resolution(tmp_path):
  232	    repo = _init_repo(tmp_path)
  233	    r1 = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
  234	    assert r1.returncode == 0, r1.stderr
  235	    r2 = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
  236	    assert r2.returncode == 3, r2.stderr + r2.stdout
  237	    assert "r1-resolution.md" in r2.stderr
  238	
  239	
  240	def test_spec_round2_proceeds_with_resolution(tmp_path):
  241	    repo = _init_repo(tmp_path)
  242	    _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
  243	    chain_dir = next((repo / "docs" / "reviewer").glob("*-spec"))
  244	    (chain_dir / "r1-resolution.md").write_text(
  245	        "# Resolution for r1\n\n## F1\nStatus: fixed\n", encoding="utf-8")
  246	    r2 = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
  247	    assert r2.returncode == 0, r2.stderr
  248	
  249	
  250	def test_spec_round2_waiver_bypasses(tmp_path):
  251	    repo = _init_repo(tmp_path)
  252	    _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
  253	    r2 = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json",
  254	              "--allow-missing-resolution")
  255	    assert r2.returncode == 0, r2.stderr
  256	
  257	
  258	def test_plan_round2_refused_without_resolution(tmp_path):
  259	    repo = _init_repo(tmp_path)
  260	    r1 = _run(repo, "--kind", "plan", "--file", "plan.md", "--emit", "json")
  261	    assert r1.returncode == 0, r1.stderr
  262	    r2 = _run(repo, "--kind", "plan", "--file", "plan.md", "--emit", "json")
  263	    assert r2.returncode == 3, r2.stderr + r2.stdout
  264	```
  265	
  266	**Also update the existing test that asserts the old behaviour:** `tests/test_resolution_gate.py::test_spec_round_2_never_gated` (~line 58) currently asserts a spec round 2 proceeds without a resolution. Delete it — `test_resolution_gate_all_kinds.py` supersedes it with the inverted contract.
  267	
  268	- [ ] **Step 2: Run tests to verify they fail**
  269	
  270	Run: `python -m pytest skills/external-review/tests/test_resolution_gate_all_kinds.py -q`
  271	Expected: FAIL — spec/plan rounds currently bypass the gate (exit 0 paths where 3 is expected).
  272	
  273	- [ ] **Step 3: Implement — drop the kind restriction**
  274	
  275	At ~line 2532, change:
  276	
  277	```python
  278	    if (
  279	        args.kind in ("post-slice", "post-phase")
  280	        and manifest["rounds"]
  281	        and not args.allow_missing_resolution
  282	    ):
  283	```
  284	
  285	to:
  286	
  287	```python
  288	    if (
  289	        manifest["rounds"]
  290	        and not args.allow_missing_resolution
  291	    ):
  292	```
  293	
  294	The block's internals already key off `prior_verdict == "revise"` / `verdict_valid is False` and the failed/rate-limited bypass statuses, so no other logic changes. Update the argparse help (~line 1840-1843) from:
  295	
  296	```python
  297	        help="Waive the resolution-required gate for post-slice/post-phase round 2+.",
  298	```
  299	
  300	to:
  301	
  302	```python
  303	        help="Waive the resolution-required gate for round 2+ (any kind).",
  304	```
  305	
  306	- [ ] **Step 4: Run tests to verify they pass**
  307	
  308	Run: `python -m pytest skills/external-review/tests/test_resolution_gate_all_kinds.py -q`
  309	Expected: PASS.
  310	
  311	- [ ] **Step 5: Check existing gate/bypass tests**
  312	
  313	Run: `python -m pytest skills/external-review/tests/test_resolution_gate.py skills/external-review/tests/test_resolution_gate_bypass.py skills/external-review/tests/test_failed_round_truth.py -q`
  314	Expected: PASS after deleting `test_spec_round_2_never_gated` (Step 1). The remaining tests use post-slice/post-phase kinds, whose behaviour is unchanged. Also grep the rest of the suite for the same assumption: `grep -rn 'never_gated\|spec.*round.*2' skills/external-review/tests/ | grep -v all_kinds` and fix any other test that relies on ungated spec/plan rounds (e.g. multi-round spec tests that don't write a resolution file — add the resolution file or a `--allow-missing-resolution` flag to those invocations, whichever the test's intent matches).
  315	
  316	- [ ] **Step 6: Commit**
  317	
  318	```bash
  319	git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_resolution_gate_all_kinds.py
  320	git commit -m "P9.S1: extend resolution-required gate to all review kinds"
  321	```
  322	
  323	---
  324	
  325	### Task 3: Model tiering — selection matrix in the CLI
  326	
  327	**Files:**
  328	- Modify: `skills/external-review/scripts/external-reviewer.py` (`ReviewerInvocationContext` ~line 1358; `run_one_reviewer` ~line 1505; argparse ~line 1853)
  329	- Test: `skills/external-review/tests/test_model_tiering.py` (create)
  330	
  331	- [ ] **Step 1: Write the failing tests**
  332	
  333	Create `skills/external-review/tests/test_model_tiering.py`:
  334	
  335	```python
  336	from pathlib import Path
  337	import sys, importlib.util
  338	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
  339	sys.path.insert(0, str(SCRIPTS))
  340	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
  341	er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
  342	
  343	LIGHT = {"AGENT_REVIEWER_MODEL_LIGHT": "small-model"}
  344	STRONG = {"AGENT_REVIEWER_MODEL_STRONG": "big-model"}
  345	BOTH = {**LIGHT, **STRONG}
  346	
  347	
  348	def test_spec_primary_uses_light():
  349	    assert er.model_for_invocation("spec", "primary", env=BOTH) == "small-model"
  350	
  351	
  352	def test_plan_primary_any_round_uses_light():
  353	    # Matrix is round-independent: follow-up primaries keep their kind's tier.
  354	    assert er.model_for_invocation("plan", "primary", env=BOTH) == "small-model"
  355	
  356	
  357	def test_post_slice_primary_uses_strong():
  358	    assert er.model_for_invocation("post-slice", "primary", env=BOTH) == "big-model"
  359	
  360	
  361	def test_post_phase_primary_uses_strong():
  362	    assert er.model_for_invocation("post-phase", "primary", env=BOTH) == "big-model"
  363	
  364	
  365	def test_sweep_always_strong_even_for_spec():
  366	    assert er.model_for_invocation("spec", "sweep", env=BOTH) == "big-model"
  367	
  368	
  369	def test_no_cross_tier_fallback():
  370	    # LIGHT never substitutes for STRONG and vice versa.
  371	    assert er.model_for_invocation("post-slice", "primary", env=LIGHT) is None
  372	    assert er.model_for_invocation("spec", "primary", env=STRONG) is None
  373	
  374	
  375	def test_unset_env_returns_none():
  376	    assert er.model_for_invocation("spec", "primary", env={}) is None
  377	
  378	
  379	def test_cli_model_overrides_matrix():
  380	    assert er.model_for_invocation("spec", "primary", cli_model="forced", env=BOTH) == "forced"
  381	
  382	
  383	def test_context_env_includes_model_when_set(tmp_path):
  384	    ctx = er.ReviewerInvocationContext(
  385	        repo_root=tmp_path, chain_dir=tmp_path, request_file=tmp_path / "r.md",
  386	        response_dir=tmp_path, scratch_dir=tmp_path, target_file=tmp_path / "t.md",
  387	        kind="spec", role="primary", sweep_index=None,
  388	        provider="claude", caller_provider="codex", model="small-model",
  389	    )
  390	    assert ctx.env()["AGENT_REVIEWER_MODEL"] == "small-model"
  391	
  392	
  393	def test_context_env_omits_model_when_unset(tmp_path):
  394	    ctx = er.ReviewerInvocationContext(
  395	        repo_root=tmp_path, chain_dir=tmp_path, request_file=tmp_path / "r.md",
  396	        response_dir=tmp_path, scratch_dir=tmp_path, target_file=tmp_path / "t.md",
  397	        kind="spec", role="primary", sweep_index=None,
  398	        provider="claude", caller_provider="codex",
  399	    )
  400	    assert "AGENT_REVIEWER_MODEL" not in ctx.env()
  401	
  402	
  403	def test_argparse_model_flag_default_none():
  404	    args = er.parse_args(["review", "--kind", "spec", "--file", "x.md"])
  405	    assert args.model is None
  406	
  407	
  408	def test_model_recorded_end_to_end_without_sidecar(tmp_path):
  409	    # F3 gate: a stub reviewer emits no usage sidecar; the requested tier
  410	    # model must still land in emitted JSON and chain.json round entry.
  411	    # _init_repo/_run: copy verbatim from tests/test_resolution_gate.py,
  412	    # but make stub.sh emit "Overall verdict: ready" and have _run accept
  413	    # an env overlay (tests/test_resolution_gate.py's _run already takes
  414	    # env=None — pass {"AGENT_REVIEWER_MODEL_LIGHT": "small-model"}).
  415	    import json as _json
  416	    repo = _init_repo(tmp_path)
  417	    r = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json",
  418	             env={"AGENT_REVIEWER_MODEL_LIGHT": "small-model"})
  419	    assert r.returncode == 0, r.stderr
  420	    payload = _json.loads(r.stdout)
  421	    assert payload["model"] == "small-model"
  422	    assert payload["reviewers"][0]["model"] == "small-model"
  423	    chain_json = next((repo / "docs" / "reviewer").glob("*/chain.json"))
  424	    manifest = _json.loads(chain_json.read_text())
  425	    assert manifest["rounds"][-1]["model"] == "small-model"
  426	```
  427	
  428	(Include the `_init_repo`/`_run` helpers at the top of `test_model_tiering.py` alongside the unit tests — same imports pattern as Task 1 Step 5.)
  429	
  430	- [ ] **Step 2: Run tests to verify they fail**
  431	
  432	Run: `python -m pytest skills/external-review/tests/test_model_tiering.py -q`
  433	Expected: FAIL — `model_for_invocation` undefined; `ReviewerInvocationContext` has no `model` field.
  434	
  435	- [ ] **Step 3: Implement**
  436	
  437	(a) Below `KIND_DEPTH_DEFAULTS` (Task 1), add:
  438	
  439	```python
  440	def model_for_invocation(
  441	    kind: str,
  442	    role: str,
  443	    *,
  444	    cli_model: str | None = None,
  445	    env: dict | None = None,
  446	) -> str | None:
  447	    """P9.S1 model-tier matrix. No cross-tier fallback by design:
  448	    spec/plan primaries -> LIGHT; post gates and all sweeps -> STRONG."""
  449	    env = env if env is not None else os.environ
  450	    if cli_model:
  451	        return cli_model
  452	    if role != "primary" or kind in ("post-slice", "post-phase"):
  453	        return env.get("AGENT_REVIEWER_MODEL_STRONG") or None
  454	    return env.get("AGENT_REVIEWER_MODEL_LIGHT") or None
  455	```
  456	
  457	(b) `ReviewerInvocationContext` (~line 1358): add field `model: str | None = None` after `caller_provider`, and change `env()` to conditionally include it:
  458	
  459	```python
  460	    def env(self) -> dict:
  461	        out = {
  462	            "AGENT_REVIEWER_REPO_ROOT": str(self.repo_root),
  463	            "AGENT_REVIEWER_CHAIN_DIR": str(self.chain_dir),
  464	            "AGENT_REVIEWER_REQUEST_FILE": str(self.request_file),
  465	            "AGENT_REVIEWER_RESPONSE_DIR": str(self.response_dir),
  466	            "AGENT_REVIEWER_SCRATCH_DIR": str(self.scratch_dir),
  467	            "AGENT_REVIEWER_TARGET_FILE": str(self.target_file),
  468	            "AGENT_REVIEWER_KIND": self.kind,
  469	            "AGENT_REVIEWER_ROLE": self.role,
  470	            "AGENT_REVIEWER_SWEEP_INDEX": "" if self.sweep_index is None else str(self.sweep_index),
  471	            "AGENT_REVIEWER_PROVIDER": self.provider,
  472	            "AGENT_REVIEWER_CALLER": self.caller_provider,
  473	        }
  474	        if self.model:
  475	            out["AGENT_REVIEWER_MODEL"] = self.model
  476	        return out
  477	```
  478	
  479	(c) In `run_one_reviewer`, where `invocation_context = ReviewerInvocationContext(...)` is constructed (~line 1510), compute and pass the model:
  480	
  481	```python
  482	    model_requested = model_for_invocation(
  483	        args.kind, role, cli_model=getattr(args, "model", None),
  484	    )
  485	    invocation_context = ReviewerInvocationContext(
  486	        ...,  # existing fields unchanged
  487	        model=model_requested,
  488	    )
  489	```
  490	
  491	(d) Where the per-reviewer `model` is captured from the usage sidecar (locate with `grep -n 'usage_capture\["model"\]\|capture\["model"\]' skills/external-review/scripts/external-reviewer.py`, fed by `build_usage_capture` ~line 1294): when the sidecar yields no model, fall back to `model_requested` so the chain records what was asked for:
  492	
  493	```python
  494	    model_recorded = captured_model or model_requested
  495	```
  496	
  497	(`captured_model` = whatever local name holds `build_usage_capture(...)["model"]`; keep the sidecar value when present — it is the model that actually ran.)
  498	
  499	(e) argparse (~after `--review-depth`):
  500	
  501	```python
  502	    sp_review.add_argument(
  503	        "--model",
  504	        default=None,
  505	        help="Override the reviewer model for every reviewer in this round "
  506	             "(bypasses the LIGHT/STRONG tier matrix).",
  507	    )
  508	```
  509	
  510	- [ ] **Step 4: Run tests to verify they pass**
  511	
  512	Run: `python -m pytest skills/external-review/tests/test_model_tiering.py skills/external-review/tests/test_reviewer_invocation_context.py -q`
  513	Expected: PASS. If `test_reviewer_invocation_context.py` asserts the exact env-dict key set, update it to allow the conditional key (assert the 11 base keys are present, and `AGENT_REVIEWER_MODEL` absent when `model=None`).
  514	
  515	- [ ] **Step 5: Commit**
  516	
  517	```bash
  518	git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_model_tiering.py skills/external-review/tests/test_reviewer_invocation_context.py
  519	git commit -m "P9.S1: model-tier matrix (LIGHT/STRONG) with per-reviewer AGENT_REVIEWER_MODEL export"
  520	```
  521	
  522	---
  523	
  524	### Task 4: reviewer-agent honours AGENT_REVIEWER_MODEL
  525	
  526	**Files:**
  527	- Modify: `skills/project-setup/scripts/reviewer-agent` (codex branch ~line 32; claude branch ~line 52)
  528	- Test: `skills/external-review/tests/test_reviewer_agent_model_flag.py` (create; model it on `tests/test_reviewer_agent_wrapper.py`, which already stubs provider binaries on PATH)
  529	
  530	- [ ] **Step 1: Write the failing tests**
  531	
  532	Create `skills/external-review/tests/test_reviewer_agent_model_flag.py`, reusing the `_fake_bin`/`_env` helpers from `tests/test_reviewer_agent_wrapper.py` verbatim (`_fake_bin` drops a fake `codex`/`claude` python script on PATH that records argv to `<name>-calls.json`; `_env` builds the required `AGENT_REVIEWER_*` env with PATH prepended):
  533	
  534	```python
  535	from pathlib import Path
  536	import json, os, subprocess
  537	
  538	ROOT = Path(__file__).resolve().parents[3]
  539	WRAPPER = ROOT / "skills" / "project-setup" / "scripts" / "reviewer-agent"
  540	
  541	# _fake_bin and _env: copy verbatim from tests/test_reviewer_agent_wrapper.py.
  542	
  543	
  544	def _argv(calls):
  545	    return json.loads(calls.read_text())["argv"]
  546	
  547	
  548	def test_codex_receives_model_flag(tmp_path):
  549	    calls = _fake_bin(tmp_path, "codex")
  550	    env = _env(tmp_path, "codex")
  551	    env["AGENT_REVIEWER_MODEL"] = "tier-model"
  552	    r = subprocess.run([str(WRAPPER)], input="prompt", env=env, text=True,
  553	                       capture_output=True, timeout=20)
  554	    assert r.returncode == 0, r.stderr
  555	    argv = _argv(calls)
  556	    i = argv.index("-m")
  557	    assert argv[i:i + 2] == ["-m", "tier-model"]
  558	
  559	
  560	def test_codex_no_model_flag_when_unset(tmp_path):
  561	    calls = _fake_bin(tmp_path, "codex")
  562	    r = subprocess.run([str(WRAPPER)], input="prompt", env=_env(tmp_path, "codex"),
  563	                       text=True, capture_output=True, timeout=20)
  564	    assert r.returncode == 0, r.stderr
  565	    assert "-m" not in _argv(calls)
  566	
  567	
  568	def test_claude_receives_model_flag(tmp_path):
  569	    calls = _fake_bin(tmp_path, "claude")
  570	    env = _env(tmp_path, "claude")
  571	    env["AGENT_REVIEWER_MODEL"] = "tier-model"
  572	    r = subprocess.run([str(WRAPPER)], input="prompt", env=env, text=True,
  573	                       capture_output=True, timeout=20)
  574	    assert r.returncode == 0, r.stderr
  575	    argv = _argv(calls)
  576	    i = argv.index("--model")
  577	    assert argv[i:i + 2] == ["--model", "tier-model"]
  578	
  579	
  580	def test_claude_no_model_flag_when_unset(tmp_path):
  581	    calls = _fake_bin(tmp_path, "claude")
  582	    r = subprocess.run([str(WRAPPER)], input="prompt", env=_env(tmp_path, "claude"),
  583	                       text=True, capture_output=True, timeout=20)
  584	    assert r.returncode == 0, r.stderr
  585	    assert "--model" not in _argv(calls)
  586	```
  587	
  588	Note: the fake `claude` stub from `_fake_bin` prints `Overall verdict: ready` to stdout, which the wrapper's claude branch captures as `claude-output.json`; the wrapper's JSON-extraction fallback passes raw text through on `json.JSONDecodeError`, so the stub works for both providers unchanged.
  589	
  590	- [ ] **Step 2: Run tests to verify they fail**
  591	
  592	Run: `python -m pytest skills/external-review/tests/test_reviewer_agent_model_flag.py -q`
  593	Expected: FAIL — no model flags are passed today.
  594	
  595	- [ ] **Step 3: Implement in the wrapper**
  596	
  597	In `skills/project-setup/scripts/reviewer-agent`, inside the `codex)` case before the `codex exec` invocation, add:
  598	
  599	```bash
  600	    model_args=()

[truncated: 479 additional lines]

## Context Previews

### docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md

    1	# P9 — Review-pipeline efficiency: fewer rounds, cheaper rounds
    2	
    3	**Date:** 2026-06-06
    4	**Status:** draft
    5	**Tracker:** P9 (phase)
    6	
    7	## Problem
    8	
    9	Every slice in a Superstar-driven project pays for three review gates — spec,
   10	plan, post-slice — and each gate usually takes multiple rounds. Measured
   11	baseline from the largest consumer repo (multistore, `external-reviewer stats`,
   12	captured 2026-06-06):
   13	
   14	| kind       | rounds | first | follow-up | pass | revise | revise rate |
   15	|------------|--------|-------|-----------|------|--------|-------------|
   16	| spec       | 151    | 66    | 85        | 65   | 51     | 34%         |
   17	| plan       | 172    | 64    | 108       | 62   | 80     | 47%         |
   18	| post-slice | 156    | 69    | 87        | 63   | 73     | 47%         |
   19	
   20	That is ~7.3 reviewer rounds per slice (spec 2.3, plan 2.7, post-slice 2.3),
   21	before counting sweep reviewers. A measured round-1 `plan` review at
   22	`--review-depth thorough` (P23.S3 in multistore) consumed ~1.03M total tokens
   23	across primary + sweep (~173k non-cache-read), with both reviewers returning
   24	the same verdict — concordant sweeps on low-risk gates are pure cost.
   25	
   26	Two structural observations drive this design:
   27	
   28	1. **Round count dominates cost, not round size.** Plan chains average ~1.7
   29	   follow-up rounds. Each `revise` verdict costs a full reviewer run plus a
   30	   local fix cycle. Many revise findings are mechanical (missing acceptance
   31	   gates, dangling file references, placeholder text, tasklist drift) and are
   32	   catchable locally for free.
   33	2. **Redundancy is spent in the wrong place.** Sweeps currently run wherever
   34	   `thorough` is passed, and in practice callers pass `thorough` for spec and
   35	   plan reviews too. The gate where an agent is most likely to have fabricated
   36	   "done" is post-slice; that is where redundancy belongs.
   37	
   38	## Goals
   39	
   40	- Cut average reviewer rounds per slice from ~7.3 to ≤ 4.5 without weakening
   41	  the post-slice gate.
   42	- Halve spec/plan reviewer invocations (depth defaults + combined gate).
   43	- Catch mechanical revise-class findings locally before the first paid round.
   44	- Make the improvement measurable: `stats --since` comparison against the
   45	  baseline table above.
   46	
   47	## Non-goals / out of scope
   48	
   49	- No changes to reviewer providers themselves (`codex exec` / `claude --print`
   50	  invocation shape stays, beyond honouring a model override).
   51	- No prompt-template rewrites beyond the combined-gate guidance addition.
   52	- No consumer-repo (multistore) changes; it consumes the updated plugin.
   53	- No changes to the verdict contract, chain folder layout, or merged-verdict
   54	  truth table.
   55	
   56	## Design
   57	
   58	Three slices, ordered so S1 ships immediately and the trial comparison can
   59	start while S2/S3 land.
   60	
   61	### S1 — Quick wins: kind-aware depth defaults, context trimming, resolution gate for all kinds, model tiering, `stats --since`
   62	
   63	All changes in `skills/external-review/scripts/external-reviewer.py`,
   64	`skills/external-review/SKILL.md`, `skills/project-setup/scripts/reviewer-agent`,
   65	and the skill texts that invoke reviews (`skills/brainstorming/SKILL.md`,
   66	`skills/writing-plans/SKILL.md`, `skills/subagent-driven-development/SKILL.md`
   67	where they reference review invocation).
   68	
   69	**S1.a Kind-aware depth defaults.** `--review-depth` argparse default changes
   70	from `"standard"` to `None` (external-reviewer.py:1851-1852). Resolution order:
   71	explicit flag > kind default. Kind defaults: `spec`/`plan`/`design`/
   72	`implementation`/`other` → `standard`; `post-slice`/`post-phase` → `thorough`.
   73	The resolved depth is recorded per round in `chain.json` (new field
   74	`depth_resolved`) so stats can segment. Skill text examples stop passing
   75	`--review-depth thorough` for spec/plan invocations and document the defaults.
   76	Explicit `--review-depth thorough` on a spec/plan review continues to work
   77	exactly as today (escalation stays one flag away).
   78	
   79	**S1.b Context trimming.** Skill text change only: callers pass `tasktool
   80	brief <work-id>` output written to a temp/scratch file (or the phase-filtered
   81	extract) as `--context` instead of the full `docs/tasklist.json`. The
   82	external-review SKILL.md "Context files" section gains a rule: do not pass
   83	files whose bulk is unrelated to the work item; prefer `tasktool brief`.
   84	(Enforcement arrives with S2's preflight size warning.)
   85	
   86	**S1.c Resolution gate for all kinds.** The round-N+1 resolution-required gate
   87	(external-reviewer.py:2532-2536) drops its
   88	`args.kind in ("post-slice", "post-phase")` restriction: any kind whose prior
   89	round verdict was `revise` requires `r{N}-resolution.md` before the next round,
   90	with the existing `--allow-missing-resolution` waiver and the existing
   91	process-failure bypass unchanged. Rationale: incremental rounds only converge
   92	fast when the reviewer can verify fixes against a resolution report; spec/plan
   93	chains currently skip this and pay extra rounds re-litigating. SKILL.md
   94	resolution-artifact section updates accordingly. Migration note: existing
   95	chains with a `revise` tail and no resolution file will refuse the next round
   96	until a resolution is written or the waiver is passed — acceptable, the waiver
   97	is the escape hatch.
   98	
   99	**S1.d Model tiering.** `reviewer-agent` honours a new optional
  100	`AGENT_REVIEWER_MODEL` env var: `claude --print --model "$AGENT_REVIEWER_MODEL"`
  101	/ `codex exec -m "$AGENT_REVIEWER_MODEL"` when set, no flag when unset.
  102	`external-reviewer.py` sets `AGENT_REVIEWER_MODEL` for each reviewer process
  103	from optional env config, per this exact invocation matrix (every round, not
  104	just round 1 — follow-up primaries keep their kind's tier):
  105	
  106	| Reviewer invocation                                   | Model env used               |
  107	|-------------------------------------------------------|------------------------------|
  108	| `spec`/`plan`/`design`/`implementation`/`other` primary, any round | `AGENT_REVIEWER_MODEL_LIGHT` |
  109	| `post-slice`/`post-phase` primary, any round          | `AGENT_REVIEWER_MODEL_STRONG`|
  110	| Any sweep (first-round or final-ready), any kind      | `AGENT_REVIEWER_MODEL_STRONG`|
  111	
  112	- The mapped env var being unset → `AGENT_REVIEWER_MODEL` is not exported for
  113	  that invocation; behaviour identical to today. There is no cross-tier
  114	  fallback (LIGHT never substitutes for STRONG or vice versa).
  115	- A per-invocation `--model <name>` flag overrides the matrix for every
  116	  reviewer in that round.
  117	- Accepted trade-off (explicit): at `standard` depth a spec/plan chain's
  118	  decisive `ready` can come from the light model. That is the intended cost
  119	  posture — the post-slice gate (strong model, `thorough`) is the safety net,
  120	  and the measurement plan watches post-slice revise rate as the canary.
  121	
  122	The chosen model (or `null`) is recorded in the existing `model` field in
  123	`chain.json` round entries.
  124	
  125	**S1.e `stats --since <ISO-date>` + per-slice metric.** `run_stats` gains a
  126	`--since` filter on round `started_at`, so a trial window can be compared
  127	against the historical baseline. Dates are parsed as UTC; a date-only value
  128	means midnight UTC (matching the `utc_now_iso()` timestamps already stored in
  129	`chain.json`). Rounds without timestamps (legacy) are excluded when `--since`
  130	is passed, and the output notes how many were excluded (no silent truncation).
  131	
  132	To support the rounds-per-slice goal directly, stats also gains a per-slice
  133	section: chains are grouped by stored `work_id`; the **denominator** is the
  134	count of distinct slice work-ids that have a `post-slice` chain whose latest
  135	round in the window has a passing merged verdict (`ready` / `ready with small
  136	edits`); the **numerator** is all rounds (including sweeps) across the `spec`,
  137	`plan`, and `post-slice` chains of those work-ids. Both numbers and the
  138	resulting rounds-per-slice ratio appear in text and `--json` output.
  139	
  140	Correlation requires `work_id` on every gate, so the review-invoking skill
  141	texts (`brainstorming`, `writing-plans`) are updated in this slice to pass
  142	`--work-id <slice-id>` on slice-level `spec` and `plan` reviews whenever a
  143	tasktool row exists (today only `post-slice`/`post-phase` require it; the CLI
  144	already accepts and stores it for all kinds). In-window `spec`/`plan` chains
  145	without a `work_id` are listed as uncorrelated AND flag the ratio: stats
  146	prints/emits `per_slice_complete: false` with a warning that early-gate rounds
  147	may be undercounted, so the ≤ 4.5 figure cannot be claimed from an incomplete
  148	window.
  149	
  150	### S2 — Deterministic preflight gate + strengthened self-review checklists
  151	
  152	**S2.a `external-reviewer preflight` subcommand.**
  153	
  154	```
  155	external-reviewer preflight --kind <kind> --file <target> [--context <path>]...
  156	```
  157	
  158	Deterministic checks, no LLM calls:
  159	
  160	1. Target exists, non-empty, UTF-8.
  161	2. Placeholder scan: `TBD`, `TODO`, `FIXME`, `XXX`, `???`, `lorem ipsum`
  162	   (case-insensitive, whole-token) outside fenced code blocks.
  163	3. Referenced-path check: markdown links and backtick-quoted strings that look
  164	   like repo-relative paths (heuristic: contain `/` and an extension or are
  165	   under a known docs/src dir) must exist on disk, with explicit exemptions —
  166	   anything inside fenced code blocks, paths containing placeholder or glob
  167	   characters (`<`, `>`, `*`, `{`, `}`, `$`, `…`), and paths under
  168	   `docs/reviewer/` (future/generated artifacts) are skipped. Severity split:
  169	   a dangling **markdown link** is a failure; a dangling **backtick path** is
  170	   a warning (prose often cites paths illustratively). Failures list each
  171	   dangling path.
  172	4. Kind-required sections: `plan` → at least one task list and a
  173	   verification/acceptance-gates section; `spec` → acceptance criteria section;
  174	   `post-slice`/`post-phase` → evidence/verification section in the target.
  175	   Section detection is by heading keyword match, tolerant of phrasing
  176	   (`Verification`, `Acceptance`, `Gates`, `Evidence`).
  177	5. Context hygiene: every `--context` file exists; warn (not fail) when any
  178	   context file exceeds 16KB with a hint to pass `tasktool brief` output
  179	   instead (catches the full-`tasklist.json` habit from S1.b).
  180	
  181	Output: human-readable findings list + `--emit json`; exit 0 = pass
  182	(warnings allowed), exit 4 = failures present (distinct from the existing
  183	exit 3 resolution-gate code).
  184	
  185	**S2.b Auto-preflight on round 1.** `review` runs the same checks in-process
  186	before submitting a round-1 (broad-mode) review and refuses on failure,
  187	printing the findings. `--no-preflight` skips. Incremental rounds (N+1) skip
  188	auto-preflight — the diff/resolution machinery covers them, and re-running
  189	path checks on an already-reviewed document adds friction without catching the
  190	revise drivers.
  191	
  192	**S2.c Self-review checklists.** `brainstorming` (spec self-review section)
  193	and `writing-plans` (plan self-review) skill texts gain a short list of the
  194	top historical revise drivers as explicit checks: vague verification steps
  195	("verify it works" without a command), claims not grounded in the repo
  196	(referenced functions/flags that don't exist), tasklist drift (work-id,
  197	status, or dependency mismatches vs `docs/tasklist.json`), and acceptance
  198	criteria that a reviewer cannot evaluate from the document alone. The
  199	checklist instructs running `external-reviewer preflight` before invoking
  200	external review.

[truncated: 96 additional lines]
### /tmp/p9s1-brief-context.md

    1	# P9.S1 — Quick wins: kind-aware depth defaults, context trimming, resolution gate for all kinds, model tiering, stats --since + per-slice metric [step: implement]
    2	status: ready
    3	workflow_step: implement
    4	plan: docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md
    5	planning_status: ratified
    6	reviewer_chain: docs/reviewer/p9-s1-review-pipeline-quick-wins-plan
    7	
    8	Parent phase: P9 — Review-pipeline efficiency: fewer rounds, cheaper rounds [ready]
    9	
   10	Sibling slices:
   11	  S1  [ready]  Quick wins: kind-aware depth defaults, context trimming, resolution gate for all kinds, model tiering, stats --since + per-slice metric
   12	  S2  [ready]  Deterministic preflight gate + strengthened self-review checklists
   13	  S3  [ready]  Combined spec+plan gate for small slices
   14	
   15	Open tasks:
   16	# P9 — Review-pipeline efficiency: fewer rounds, cheaper rounds
   17	
   18	P9.S1  [ready/ratified]  group=-  ready  deps=-  waiting_on=-  cancelled_deps=-  Quick wins: kind-aware depth defaults, context trimming, resolution gate for all kinds, model tiering, stats --since + per-slice metric
   19	P9.S2  [ready/proposed]  group=-  waiting  deps=P9.S1  waiting_on=P9.S1  cancelled_deps=-  Deterministic preflight gate + strengthened self-review checklists
   20	P9.S3  [ready/proposed]  group=-  waiting  deps=P9.S1, P9.S2  waiting_on=P9.S1, P9.S2  cancelled_deps=-  Combined spec+plan gate for small slices

<!-- superstar-prompt:end -->