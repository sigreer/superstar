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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p9-s3-combined-spec-plan-gate-for-small-slices

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-09-P9.S3-combined-spec-plan-gate.md

Additional context files:
- docs/specs/2026-06-09-P9.S3-combined-spec-plan-gate-design.md
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

### docs/plans/2026-06-09-P9.S3-combined-spec-plan-gate.md

    1	# P9.S3 — Combined spec+plan gate for small slices — Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Add a `--combined-gate <spec-path>` option to `external-reviewer review --kind plan` that folds an un-reviewed spec into the plan review, persists the combination on the chain, segments it in `stats`, and routes eligible small slices through it via skill text.
    6	
    7	**Architecture:** All CLI behaviour is additive in the single script `skills/external-review/scripts/external-reviewer.py`: one new argparse flag, an early kind/existence validation, chain-level persistence mirroring the existing `work_id` precedent, a prompt-guidance append threaded through a new optional `make_prompt(extra_guidance=...)` parameter, a per-round manifest stamp, and a `combined_gate` segment in `collect_review_stats`/`print_stats_table`. Skill text (brainstorming, writing-plans, external-review) documents eligibility and invocation. The tasktool workflow-step transition is already unenforced, so that slice adds only a regression test.
    8	
    9	**Tech Stack:** Python 3 (stdlib only, argparse/json/pathlib), pytest (subprocess + module-import test styles already established in `skills/external-review/tests/` and `tools/tasktool/tests/`).
   10	
   11	**Spec:** `docs/specs/2026-06-09-P9.S3-combined-spec-plan-gate-design.md`
   12	
   13	---
   14	
   15	## Scheduling contract
   16	
   17	- **Tracker row:** `P9.S3` (slice of `P9`). `workflow_step: plan`.
   18	- **`depends_on`:** `P9.S1`, `P9.S2` — both `done`. Confirmed unchanged; no `tasktool deps` edit needed.
   19	- **`parallel_group`:** none. S1 and S2 are `done`, so S3 is the only live slice in P9 — no sibling overlap.
   20	- **Surface/reservation table:** **not required.** No concurrent sibling can overlap this slice's surfaces (the only edited files are `skills/external-review/scripts/external-reviewer.py`, its tests, `tools/tasktool/tests/`, and three SKILL.md files; no other live P9 slice touches them).
   21	- **Ratification:** run `tasktool ratify P9.S3` once this plan settles (Task 0 confirms; final check before plan review).
   22	
   23	---
   24	
   25	## File structure
   26	
   27	| File | Responsibility | Change |
   28	|---|---|---|
   29	| `skills/external-review/scripts/external-reviewer.py` | CLI: flag, validation, persistence, prompt guidance, stamp, stats | Modify |
   30	| `skills/external-review/tests/test_combined_gate.py` | Unit + subprocess tests for flag/validation/persistence/prompt/stamp | Create |
   31	| `skills/external-review/tests/test_combined_gate_stats.py` | Unit tests for stats segmentation | Create |
   32	| `tools/tasktool/tests/test_workflow_step_spec_to_plan.py` | Regression: `set --workflow-step plan` from `spec` succeeds | Create |
   33	| `skills/external-review/SKILL.md` | Document `--combined-gate`, persistence, stats segment | Modify |
   34	| `skills/brainstorming/SKILL.md` | Combined-gate eligibility + "write spec, skip standalone review" branch | Modify |
   35	| `skills/writing-plans/SKILL.md` | Combined-gate eligibility + `--combined-gate` plan-review invocation + workflow-step note | Modify |
   36	
   37	**Shared definitions introduced (referenced by later tasks):**
   38	
   39	- Module constant `COMBINED_GATE_GUIDANCE` (Task 3) — the spec-coverage instruction text.
   40	- `make_prompt(..., extra_guidance: str | None = None)` (Task 3) — appends to the kind's mode guidance.
   41	- Manifest top-level key `combined_gate_spec` (Task 2) — repo-relative spec path persisted on round 1.
   42	- Round-entry keys `combined_gate: true` and `combined_gate_spec` (Task 2).
   43	- Stats dict key `combined_gate` with `combined`/`standalone` sub-blocks (Task 4).
   44	
   45	---
   46	
   47	## Task 0: Confirm scheduling and baseline tests
   48	
   49	**Files:** none (verification only)
   50	
   51	- [ ] **Step 1: Confirm the row and dependencies**
   52	
   53	Run: `tasktool show P9.S3 && tasktool schedule P9`
   54	Expected: `P9.S3` `workflow_step: plan`, `depends_on: P9.S1, P9.S2`; both deps `done/ratified`; `P9.S3` `ready`.
   55	
   56	- [ ] **Step 2: Confirm the baseline suite is green before changes**
   57	
   58	Run: `cd /home/simon/Dev/sigreer/skills/superstar && python -m pytest skills/external-review/tests tools/tasktool/tests -q`
   59	Expected: PASS (record the count; new tests are added against this baseline).
   60	
   61	- [ ] **Step 3: Ratify the scheduling contract**
   62	
   63	Run: `tasktool ratify P9.S3`
   64	Expected: exit 0 (planning_status → ratified).
   65	
   66	---
   67	
   68	## Task 1: `--combined-gate` flag, kind guard, and path existence
   69	
   70	Add the flag and the two early exit-2 validations (kind must be `plan`; an explicitly-supplied spec path must exist). This task does **not** yet attach the spec to context, persist it, or change the prompt — those are Tasks 2–3. The flag is wired and rejects misuse.
   71	
   72	**Files:**
   73	- Modify: `skills/external-review/scripts/external-reviewer.py` (review subparser near `--no-preflight`, ~line 2141-2145; early validation in the review dispatch after the `--work-id` guard, ~line 2879-2886)
   74	- Test: `skills/external-review/tests/test_combined_gate.py` (create)
   75	
   76	- [ ] **Step 1: Write the failing tests (kind guard + missing path)**
   77	
   78	Create `skills/external-review/tests/test_combined_gate.py`:
   79	
   80	```python
   81	from pathlib import Path
   82	import subprocess, sys, os
   83	
   84	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
   85	SCRIPT = SCRIPTS / "external-reviewer.py"
   86	
   87	
   88	def _init_repo(tmp_path: Path) -> Path:
   89	    repo = tmp_path / "repo"; repo.mkdir()
   90	    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
   91	    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
   92	    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
   93	    (repo / "plan.md").write_text(
   94	        "# Plan\n\n## Tasks\n- [ ] do it\n\n## Verification\nRun `pytest`.\n"
   95	    )
   96	    (repo / "spec.md").write_text("# Spec\n\n## Acceptance criteria\n1. works\n")
   97	    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
   98	    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
   99	    reviewer = repo / "stub.sh"
  100	    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
  101	    reviewer.chmod(0o755)
  102	    return repo
  103	
  104	
  105	def _run(repo: Path, *args: str):
  106	    env = os.environ.copy(); env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
  107	    return subprocess.run(
  108	        [sys.executable, str(SCRIPT), "review", *args, "--emit", "json"],
  109	        cwd=repo, env=env, capture_output=True, text=True,
  110	    )
  111	
  112	
  113	def test_combined_gate_non_plan_kind_exits_2(tmp_path):
  114	    repo = _init_repo(tmp_path)
  115	    r = _run(repo, "--kind", "spec", "--file", "plan.md",
  116	             "--combined-gate", "spec.md")
  117	    assert r.returncode == 2, r.stderr
  118	    # Must be OUR validation, not argparse's "unrecognized arguments" (which
  119	    # also exits 2). This is what makes the test prove the new behaviour.
  120	    assert "unrecognized arguments" not in r.stderr
  121	    assert "only valid with --kind plan" in r.stderr
  122	    # No chain folder created.
  123	    assert not (repo / "docs" / "reviewer").exists()
  124	
  125	
  126	def test_combined_gate_missing_spec_exits_2(tmp_path):
  127	    repo = _init_repo(tmp_path)
  128	    r = _run(repo, "--kind", "plan", "--file", "plan.md",
  129	             "--combined-gate", "nope.md")
  130	    assert r.returncode == 2, r.stderr
  131	    assert "unrecognized arguments" not in r.stderr
  132	    assert "not found" in r.stderr.lower()
  133	    assert "nope.md" in r.stderr
  134	    assert not (repo / "docs" / "reviewer").exists()
  135	```
  136	
  137	- [ ] **Step 2: Run the tests to verify they fail**
  138	
  139	Run: `cd /home/simon/Dev/sigreer/skills/superstar && python -m pytest skills/external-review/tests/test_combined_gate.py -v`
  140	Expected: FAIL — before the flag is added, argparse prints `unrecognized arguments: --combined-gate`, so the `"unrecognized arguments" not in r.stderr` and the specific-message assertions fail. This confirms the tests exercise the *new* validation path, not argparse's default rejection.
  141	
  142	- [ ] **Step 3: Add the argparse flag**
  143	
  144	In `external-reviewer.py`, in the `sp_review` block, immediately after the `--no-preflight` argument (~line 2145):
  145	
  146	```python
  147	    sp_review.add_argument(
  148	        "--combined-gate",
  149	        default=None,
  150	        metavar="SPEC_PATH",
  151	        help="Plan-only. Attach this (un-reviewed) spec to the plan review so "
  152	             "one review covers both. Persisted on the chain; reused on later "
  153	             "rounds. Exits 2 if used with a non-plan kind or a missing path.",
  154	    )
  155	```
  156	
  157	- [ ] **Step 4: Add the early validations**
  158	
  159	In `main()`, in the review path, immediately after the existing `--work-id`
  160	guard block (the `if args.kind in ("post-slice", "post-phase") and not
  161	args.work_id:` block ending ~line 2885), add:
  162	
  163	```python
  164	    # --combined-gate is plan-only; validate before any chain work so misuse
  165	    # never creates a chain folder.
  166	    if args.combined_gate is not None and args.kind != "plan":
  167	        print(
  168	            "ERROR: --combined-gate is only valid with --kind plan.",
  169	            file=sys.stderr,
  170	        )
  171	        return 2
  172	```
  173	
  174	Then, immediately after the existing target-existence check resolves `root`
  175	and `target` (after the `if not target.exists(): ... return 2` block, ~line
  176	2891), add the explicit-path existence check:
  177	
  178	```python
  179	    combined_gate_explicit: Path | None = None
  180	    if args.combined_gate is not None:
  181	        combined_gate_explicit = (
  182	            (root / args.combined_gate).resolve()
  183	            if not Path(args.combined_gate).is_absolute()
  184	            else Path(args.combined_gate).resolve()
  185	        )
  186	        if not combined_gate_explicit.exists():
  187	            print(
  188	                f"ERROR: --combined-gate spec not found: {combined_gate_explicit}",
  189	                file=sys.stderr,
  190	            )
  191	            return 2
  192	```
  193	
  194	- [ ] **Step 5: Run the tests to verify they pass**
  195	
  196	Run: `cd /home/simon/Dev/sigreer/skills/superstar && python -m pytest skills/external-review/tests/test_combined_gate.py -v`
  197	Expected: PASS (both `test_combined_gate_non_plan_kind_exits_2` and `test_combined_gate_missing_spec_exits_2`).
  198	
  199	- [ ] **Step 6: Commit**
  200	
  201	```bash
  202	git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_combined_gate.py
  203	git commit -m "P9.S3: add --combined-gate flag with kind/path validation"
  204	```
  205	
  206	---
  207	
  208	## Task 2: Chain-level persistence, mismatch (exit 6), context attachment, and round stamp
  209	
  210	Resolve the **effective** combined spec (explicit on round 1 → persist; reused from manifest on later rounds), enforce the exit-6 mismatch rules, attach the effective spec to the context set (deduped), and stamp the round entry. Prompt guidance is still Task 3; here the manifest and context wiring land.
  211	
  212	**Files:**
  213	- Modify: `skills/external-review/scripts/external-reviewer.py` (new-manifest dict ~line 2938-2947; existing-manifest branch ~line 2951-2971; context list ~line 2893-2899 / just after the manifest branch; round_entry dict ~line 3284-3313)
  214	- Test: `skills/external-review/tests/test_combined_gate.py` (extend)
  215	
  216	- [ ] **Step 1: Write the failing tests**
  217	
  218	Append to `skills/external-review/tests/test_combined_gate.py`:
  219	
  220	```python
  221	import json
  222	
  223	
  224	def _chain_dir(repo: Path) -> Path:
  225	    base = repo / "docs" / "reviewer"
  226	    # Single chain expected in these tests.
  227	    return next(d for d in base.iterdir() if d.is_dir())
  228	
  229	
  230	def _manifest(repo: Path) -> dict:
  231	    return json.loads((_chain_dir(repo) / "chain.json").read_text())
  232	
  233	
  234	def test_round1_persists_and_stamps_combined_gate(tmp_path):
  235	    repo = _init_repo(tmp_path)
  236	    r = _run(repo, "--kind", "plan", "--file", "plan.md",
  237	             "--work-id", "P1.S1", "--combined-gate", "spec.md")
  238	    assert r.returncode == 0, r.stderr
  239	    m = _manifest(repo)
  240	    assert m["combined_gate_spec"] == "spec.md"          # chain-level persist
  241	    rnd = m["rounds"][-1]
  242	    assert rnd["combined_gate"] is True                  # round stamp
  243	    assert rnd["combined_gate_spec"] == "spec.md"
  244	
  245	
  246	def test_round2_without_flag_reuses_persisted_spec(tmp_path):
  247	    repo = _init_repo(tmp_path)
  248	    r1 = _run(repo, "--kind", "plan", "--file", "plan.md",
  249	              "--work-id", "P1.S1", "--combined-gate", "spec.md")
  250	    assert r1.returncode == 0, r1.stderr
  251	    # Round 2 omits --combined-gate; allow-missing-resolution because r1 was ready.
  252	    r2 = _run(repo, "--kind", "plan", "--file", "plan.md",
  253	              "--work-id", "P1.S1", "--allow-missing-resolution")
  254	    assert r2.returncode == 0, r2.stderr
  255	    m = _manifest(repo)
  256	    assert len(m["rounds"]) == 2
  257	    assert m["rounds"][-1]["combined_gate"] is True      # still combined on r2
  258	    assert m["rounds"][-1]["combined_gate_spec"] == "spec.md"
  259	
  260	
  261	def test_round2_different_spec_exits_6(tmp_path):
  262	    repo = _init_repo(tmp_path)
  263	    (repo / "other-spec.md").write_text("# Other\n\n## Acceptance criteria\n1. x\n")
  264	    r1 = _run(repo, "--kind", "plan", "--file", "plan.md",
  265	              "--work-id", "P1.S1", "--combined-gate", "spec.md")
  266	    assert r1.returncode == 0, r1.stderr
  267	    r2 = _run(repo, "--kind", "plan", "--file", "plan.md", "--work-id", "P1.S1",
  268	              "--combined-gate", "other-spec.md", "--allow-missing-resolution")
  269	    assert r2.returncode == 6, r2.stderr
  270	    assert "combined" in r2.stderr.lower()
  271	
  272	
  273	def test_combined_gate_on_noncombined_chain_exits_6(tmp_path):
  274	    repo = _init_repo(tmp_path)
  275	    # Round 1 is a standalone plan review (no --combined-gate).
  276	    r1 = _run(repo, "--kind", "plan", "--file", "plan.md", "--work-id", "P1.S1")
  277	    assert r1.returncode == 0, r1.stderr
  278	    r2 = _run(repo, "--kind", "plan", "--file", "plan.md", "--work-id", "P1.S1",
  279	              "--combined-gate", "spec.md", "--allow-missing-resolution")
  280	    assert r2.returncode == 6, r2.stderr
  281	
  282	
  283	def test_standalone_plan_has_no_combined_keys(tmp_path):
  284	    repo = _init_repo(tmp_path)
  285	    r = _run(repo, "--kind", "plan", "--file", "plan.md", "--work-id", "P1.S1")
  286	    assert r.returncode == 0, r.stderr
  287	    m = _manifest(repo)
  288	    assert "combined_gate_spec" not in m
  289	    assert "combined_gate" not in m["rounds"][-1]
  290	
  291	
  292	def test_combined_gate_attaches_spec_to_context(tmp_path):
  293	    # Round 1 is broad, so attached context is previewed in the request.
  294	    # "Acceptance criteria" appears only in spec.md (not in plan.md), so its
  295	    # presence proves the spec was attached to the review context.
  296	    repo = _init_repo(tmp_path)
  297	    r = _run(repo, "--kind", "plan", "--file", "plan.md",
  298	             "--work-id", "P1.S1", "--combined-gate", "spec.md")
  299	    assert r.returncode == 0, r.stderr
  300	    request = next(_chain_dir(repo).glob("r1-*-request.md")).read_text()
  301	    assert "Acceptance criteria" in request
  302	
  303	
  304	def test_combined_gate_dedupes_spec_in_context(tmp_path):
  305	    # Spec supplied both via --combined-gate and --context must attach once.
  306	    repo = _init_repo(tmp_path)
  307	    r = _run(repo, "--kind", "plan", "--file", "plan.md", "--work-id", "P1.S1",
  308	             "--combined-gate", "spec.md", "--context", "spec.md")
  309	    assert r.returncode == 0, r.stderr
  310	    request = next(_chain_dir(repo).glob("r1-*-request.md")).read_text()
  311	    # spec.md's unique content is previewed exactly once (deduped).
  312	    assert request.count("Acceptance criteria") == 1
  313	```
  314	
  315	- [ ] **Step 2: Run the tests to verify they fail**
  316	
  317	Run: `cd /home/simon/Dev/sigreer/skills/superstar && python -m pytest skills/external-review/tests/test_combined_gate.py -v -k "round1 or round2 or noncombined or standalone_plan_has or attaches_spec or dedupes"`
  318	Expected: FAIL — manifest has no `combined_gate_spec`/`combined_gate` keys, the mismatch cases return 0 instead of 6, and the spec is not yet attached to context (no "Acceptance criteria" in the request).
  319	
  320	- [ ] **Step 3: Persist on the new-manifest (round 1) branch**
  321	
  322	In the `if manifest is None:` block, do **not** add a `combined_gate_spec` key
  323	to the manifest literal — a standalone chain must omit the key entirely (spec
  324	"absent on standalone" contract; `test_standalone_plan_has_no_combined_keys`
  325	asserts `"combined_gate_spec" not in m`). Instead, set it conditionally
  326	**only when combined**, immediately after the `write_manifest(manifest_path,
  327	manifest)` eager-write at the end of the `if manifest is None:` block (~line
  328	2950). Store the repo-relative path so the value is portable:
  329	
  330	```python
  331	        write_manifest(manifest_path, manifest)
  332	        if combined_gate_explicit is not None:
  333	            manifest["combined_gate_spec"] = rel_or_abs(combined_gate_explicit, root)
  334	            write_manifest(manifest_path, manifest)
  335	```
  336	
  337	(Two writes keep the existing eager-write semantics intact for the standalone
  338	case; the second write only happens for combined chains.)
  339	
  340	- [ ] **Step 4: Resolve the effective spec + enforce exit-6 on the existing-manifest branch**
  341	
  342	After the existing `work_id` mismatch/backfill logic in the `else:` branch
  343	(after the `if stored_work_id is None and args.work_id is not None:` backfill,
  344	~line 2971), add:
  345	
  346	```python
  347	        # Combined-gate chain identity: a combined chain stays combined for its
  348	        # whole life (the spec remains un-reviewed). Mirror the work_id rule.
  349	        stored_combined = manifest.get("combined_gate_spec")
  350	        explicit_rel = (
  351	            rel_or_abs(combined_gate_explicit, root)
  352	            if combined_gate_explicit is not None else None
  353	        )
  354	        if explicit_rel is not None:
  355	            if stored_combined is None:
  356	                print(
  357	                    "ERROR: --combined-gate was not set when this chain was "
  358	                    "created; a chain cannot become combined mid-stream.",
  359	                    file=sys.stderr,
  360	                )
  361	                return 6
  362	            if stored_combined != explicit_rel:
  363	                print(
  364	                    f"ERROR: --combined-gate {explicit_rel!r} does not match the "
  365	                    f"chain's stored combined_gate_spec {stored_combined!r}. "
  366	                    "A combined chain cannot switch which spec it covers.",
  367	                    file=sys.stderr,
  368	                )
  369	                return 6
  370	```
  371	
  372	- [ ] **Step 5: Compute the effective combined spec and attach it to context**
  373	
  374	After the whole new/existing manifest branch resolves (after the
  375	`if manifest is None: ... else: ...` block, before the resolution-gate block at
  376	~line 2973), compute the effective spec path and append it to `context`,
  377	deduplicating by resolved path:
  378	
  379	```python
  380	    # Effective combined spec = explicit (round 1) or persisted (later rounds).
  381	    stored_combined = manifest.get("combined_gate_spec")
  382	    combined_gate_effective: Path | None = None
  383	    if combined_gate_explicit is not None:
  384	        combined_gate_effective = combined_gate_explicit
  385	    elif stored_combined is not None:
  386	        combined_gate_effective = (
  387	            (root / stored_combined).resolve()
  388	            if not Path(stored_combined).is_absolute()
  389	            else Path(stored_combined).resolve()
  390	        )
  391	        if not combined_gate_effective.exists():
  392	            print(
  393	                f"ERROR: chain's combined_gate_spec not found: "
  394	                f"{combined_gate_effective}",
  395	                file=sys.stderr,
  396	            )
  397	            return 2
  398	    if combined_gate_effective is not None:
  399	        if combined_gate_effective not in context:
  400	            context.append(combined_gate_effective)
  401	```
  402	
  403	> Note: `context` is a `list[Path]` of resolved paths (built at ~line 2893), so
  404	> the `not in` membership check deduplicates correctly when the same spec was
  405	> also passed via `--context`.
  406	
  407	- [ ] **Step 6: Stamp the round entry**
  408	
  409	In the `round_entry` dict (the dict that already sets `"depth_resolved":
  410	args.review_depth,` ~line 3312), add the combined-gate stamp **only when the
  411	round is combined** so standalone rounds stay byte-identical. Replace the
  412	`depth_resolved` line with:
  413	
  414	```python
  415	        "depth_resolved": args.review_depth,
  416	        **(
  417	            {"combined_gate": True,
  418	             "combined_gate_spec": rel_or_abs(combined_gate_effective, root)}
  419	            if combined_gate_effective is not None else {}
  420	        ),
  421	```
  422	
  423	- [ ] **Step 7: Run the tests to verify they pass**
  424	
  425	Run: `cd /home/simon/Dev/sigreer/skills/superstar && python -m pytest skills/external-review/tests/test_combined_gate.py -v`
  426	Expected: PASS (all Task 1 + Task 2 tests).
  427	
  428	- [ ] **Step 8: Commit**
  429	
  430	```bash
  431	git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_combined_gate.py
  432	git commit -m "P9.S3: persist combined-gate on chain, enforce mismatch, stamp rounds"
  433	```
  434	
  435	---
  436	
  437	## Task 3: Inject the spec-coverage prompt guidance
  438	
  439	Thread an optional `extra_guidance` parameter through `make_prompt` and pass the combined-gate instruction when the round is combined. Standalone plan reviews keep `extra_guidance=None` and assemble a byte-identical prompt.
  440	
  441	**Files:**
  442	- Modify: `skills/external-review/scripts/external-reviewer.py` (`make_prompt` ~line 958-989; module constant near `MODE_GUIDANCE` ~line 124; the primary `make_prompt` call ~line 3084 and the `final-ready` sweep call ~line 3191)
  443	- Test: `skills/external-review/tests/test_combined_gate.py` (extend)
  444	
  445	- [ ] **Step 1: Write the failing tests**
  446	
  447	Append to `skills/external-review/tests/test_combined_gate.py`:
  448	
  449	```python
  450	import importlib.util
  451	
  452	_spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPT)
  453	er = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(er)
  454	
  455	
  456	def test_make_prompt_default_is_unchanged(tmp_path):
  457	    # extra_guidance=None must not alter the assembled plan prompt.
  458	    repo = _init_repo(tmp_path)
  459	    root = repo
  460	    target = repo / "plan.md"
  461	    base = er.make_prompt(root=root, target=target, kind="plan",
  462	                          context=[], max_lines=600)
  463	    explicit_none = er.make_prompt(root=root, target=target, kind="plan",
  464	                                   context=[], max_lines=600, extra_guidance=None)
  465	    assert base == explicit_none
  466	
  467	
  468	def test_make_prompt_appends_extra_guidance(tmp_path):
  469	    repo = _init_repo(tmp_path)
  470	    p = er.make_prompt(root=repo, target=repo / "plan.md", kind="plan",
  471	                       context=[], max_lines=600,
  472	                       extra_guidance=er.COMBINED_GATE_GUIDANCE)
  473	    assert "did not receive a standalone review" in p
  474	    assert "tag spec-level findings distinctly" in p
  475	
  476	
  477	def test_combined_review_prompt_contains_guidance(tmp_path):
  478	    repo = _init_repo(tmp_path)
  479	    r = _run(repo, "--kind", "plan", "--file", "plan.md",
  480	             "--work-id", "P1.S1", "--combined-gate", "spec.md")
  481	    assert r.returncode == 0, r.stderr
  482	    request = next(_chain_dir(repo).glob("r1-*-request.md")).read_text()
  483	    assert "did not receive a standalone review" in request
  484	
  485	
  486	def test_standalone_review_prompt_has_no_guidance(tmp_path):
  487	    repo = _init_repo(tmp_path)
  488	    r = _run(repo, "--kind", "plan", "--file", "plan.md", "--work-id", "P1.S1")
  489	    assert r.returncode == 0, r.stderr
  490	    request = next(_chain_dir(repo).glob("r1-*-request.md")).read_text()
  491	    assert "did not receive a standalone review" not in request
  492	
  493	
  494	def test_round2_reattaches_guidance_without_flag(tmp_path):
  495	    # Spec AC8: a round-2 fixture proving guidance + spec re-attachment when the
  496	    # flag is omitted on the re-submit (the chain reuses the persisted spec).
  497	    repo = _init_repo(tmp_path)
  498	    r1 = _run(repo, "--kind", "plan", "--file", "plan.md",
  499	              "--work-id", "P1.S1", "--combined-gate", "spec.md")
  500	    assert r1.returncode == 0, r1.stderr
  501	    r2 = _run(repo, "--kind", "plan", "--file", "plan.md",
  502	              "--work-id", "P1.S1", "--allow-missing-resolution")
  503	    assert r2.returncode == 0, r2.stderr
  504	    request = sorted(_chain_dir(repo).glob("r2-*-request.md"))[-1].read_text()
  505	    # Guidance re-applied on round 2 even though --combined-gate was omitted...
  506	    assert "did not receive a standalone review" in request
  507	    # ...and the spec is still attached (listed among the prompt's context files).
  508	    assert "spec.md" in request
  509	```
  510	
  511	- [ ] **Step 2: Run the tests to verify they fail**
  512	
  513	Run: `cd /home/simon/Dev/sigreer/skills/superstar && python -m pytest skills/external-review/tests/test_combined_gate.py -v -k "make_prompt or guidance or reattaches"`
  514	Expected: FAIL — `make_prompt` has no `extra_guidance` kwarg (TypeError) and `er.COMBINED_GATE_GUIDANCE` does not exist (AttributeError); the round-2 request lacks the guidance text.
  515	
  516	- [ ] **Step 3: Add the guidance constant**
  517	
  518	In `external-reviewer.py`, immediately after the `MODE_GUIDANCE` dict closes
  519	(~line 124), add:
  520	
  521	```python
  522	COMBINED_GATE_GUIDANCE = (
  523	    "This plan's spec did not receive a standalone review. Also review the "
  524	    "attached spec for completeness, internal consistency, and groundedness; "
  525	    "tag spec-level findings distinctly."
  526	)
  527	```
  528	
  529	- [ ] **Step 4: Add the `extra_guidance` parameter to `make_prompt`**
  530	
  531	Change the `make_prompt` signature (~line 958) to add the keyword-only
  532	parameter, and append it to the mode guidance before formatting:
  533	
  534	```python
  535	def make_prompt(
  536	    *,
  537	    root: Path,
  538	    target: Path,
  539	    kind: str,
  540	    context: list[Path],
  541	    max_lines: int,
  542	    mode: str = "broad",
  543	    incremental_preamble: str | None = None,
  544	    incremental_budget_chars: int | None = None,
  545	    extra_guidance: str | None = None,
  546	) -> str:
  547	    context_display = "\n".join(f"- {rel_or_abs(p, root)}" for p in context) or "- none"
  548	    mode_guidance = MODE_GUIDANCE[kind]
  549	    if extra_guidance:
  550	        mode_guidance = mode_guidance + "\n\n" + extra_guidance
  551	    body = REVIEW_PROMPT.format(
  552	        repo_root=root,
  553	        kind=kind,
  554	        mode_guidance=mode_guidance,
  555	        target_file=rel_or_abs(target, root),
  556	        context_files=context_display,
  557	    )
  558	```
  559	
  560	(The rest of `make_prompt` is unchanged. With `extra_guidance=None` the
  561	`mode_guidance` value is identical to today, so existing callers are
  562	byte-stable — verified by `test_make_prompt_default_is_unchanged`.)
  563	
  564	- [ ] **Step 5: Pass the guidance from the review flow**
  565	
  566	Compute the guidance once after the effective spec is known (Task 2 Step 5),
  567	e.g. right before the primary `make_prompt` call (~line 3084):
  568	
  569	```python
  570	    combined_guidance = (
  571	        COMBINED_GATE_GUIDANCE if combined_gate_effective is not None else None
  572	    )
  573	```
  574	
  575	Then pass `extra_guidance=combined_guidance` to **both** `make_prompt` calls —
  576	the primary call (~line 3084) and the `final-ready` sweep call (~line 3191):
  577	
  578	```python
  579	    prompt_text = make_prompt(
  580	        root=root, target=target, kind=args.kind,
  581	        context=context, max_lines=args.max_lines,
  582	        mode=mode, incremental_preamble=incremental_preamble,
  583	        incremental_budget_chars=args.incremental_budget_chars,
  584	        extra_guidance=combined_guidance,
  585	    )
  586	```
  587	
  588	```python
  589	                sweep_prompt = make_prompt(
  590	                    root=root, target=target, kind=args.kind,
  591	                    context=context, max_lines=args.max_lines,
  592	                    mode="broad", incremental_preamble=None,
  593	                    incremental_budget_chars=args.incremental_budget_chars,
  594	                    extra_guidance=combined_guidance,
  595	                )
  596	```
  597	
  598	(First-round sweeps reuse `prompt_text` directly, so they already carry the
  599	guidance. Plan reviews default to `standard` depth with no sweeps; passing the
  600	guidance to the `final-ready` rebuild keeps an escalated `--review-depth

[truncated: 322 additional lines]

## Context Previews

### docs/specs/2026-06-09-P9.S3-combined-spec-plan-gate-design.md

    1	# P9.S3 — Combined spec+plan gate for small slices
    2	
    3	**Date:** 2026-06-09
    4	**Status:** draft
    5	**Tracker:** P9.S3 (slice of P9 — Review-pipeline efficiency)
    6	**Parent spec:** `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md` (S3 section)
    7	**Depends on:** P9.S1 (done), P9.S2 (done)
    8	
    9	## Problem
   10	
   11	Every slice in a Superstar-driven project pays for three review gates — spec,
   12	plan, post-slice. The phase baseline (multistore, `external-reviewer stats`,
   13	2026-06-06) shows spec chains averaging ~2.3 rounds and plan chains ~2.7. For a
   14	small, single-surface slice — one tool or skill area, no new subsystem, no new
   15	product decisions — the standalone spec review and the plan review largely
   16	re-examine the same narrow change. The spec gate's rounds are avoidable in that
   17	case: one review that covers both the plan and its (un-reviewed) spec would
   18	catch the same defects at half the early-gate cost.
   19	
   20	P9.S1 made each round cheaper (depth defaults, model tiering) and P9.S2 caught
   21	mechanical defects locally before the first paid round (`preflight`). Neither
   22	removed an entire gate. S3 closes that gap for eligible slices by folding the
   23	spec review into the plan review.
   24	
   25	## Goal
   26	
   27	Let an eligible small slice skip the standalone spec review and instead carry
   28	spec coverage into the plan review, halving the early-gate round count for those
   29	slices without weakening review quality. Concretely:
   30	
   31	- A `--combined-gate <spec-path>` flag on `external-reviewer review --kind plan`
   32	  that attaches the un-reviewed spec to the plan review and instructs the
   33	  reviewer to also review the spec, tagging spec-level findings distinctly.
   34	- `chain.json` stamps `combined_gate` + the spec path per round so combined
   35	  chains are identifiable after the fact.
   36	- `external-reviewer stats` segments plan chains into combined vs standalone so
   37	  the phase measurement plan can quantify the saving.
   38	- `brainstorming` and `writing-plans` skill text defines eligibility and routes
   39	  eligible slices through the combined gate.
   40	
   41	This is S3 of the phase. It does not change the verdict contract, chain layout,
   42	provider invocation, or any S1/S2 behaviour.
   43	
   44	## Non-goals / out of scope
   45	
   46	- No combined gate for phase-level specs — phase specs always receive a
   47	  standalone spec review.
   48	- No mechanical eligibility enforcement — eligibility is author judgment guided
   49	  by skill text; the CLI does not gate on it.
   50	- No changes to the verdict contract, chain-folder layout, merged-verdict truth
   51	  table, or provider invocation shape.
   52	- No changes to S1 behaviour (depth defaults, model tiering, resolution gate,
   53	  base stats) or S2 behaviour (preflight) beyond the additive
   54	  `combined_gate` stats segment.
   55	- No consumer-repo (multistore) changes.
   56	
   57	## Design
   58	
   59	All CLI behaviour lives in
   60	`skills/external-review/scripts/external-reviewer.py`. Skill text lives in
   61	`skills/brainstorming/SKILL.md`, `skills/writing-plans/SKILL.md`, and
   62	`skills/external-review/SKILL.md`. Tests live in
   63	`skills/external-review/tests/`. Workflow-step verification touches
   64	`tools/tasktool/` only with a regression test (no production code change
   65	expected).
   66	
   67	### S3.a — Eligibility (skill text)
   68	
   69	`skills/brainstorming/SKILL.md` (spec flow) and
   70	`skills/writing-plans/SKILL.md` (plan flow) gain a short "Combined spec+plan
   71	gate" section. The combined gate applies to
   72	**slice-level specs only** — a phase-level spec (like the P9 phase design)
   73	always receives a standalone spec review.
   74	
   75	A slice may use the combined gate when **all** of these hold:
   76	
   77	- **Single-surface change** — one tool/skill/app area; no new subsystem.
   78	- **No cross-repo or cross-plugin impact.**
   79	- **Spec fits the existing phase direction** — no new product decisions that
   80	  would otherwise warrant a standalone spec conversation.
   81	
   82	When eligible, `brainstorming` still writes the spec document and commits the
   83	spec artifact transaction, but **skips the standalone external spec review**;
   84	it transitions directly to `writing-plans`. `writing-plans` then invokes the
   85	plan review with `--combined-gate <spec-path>`, so the plan review carries the
   86	spec-coverage burden. The author still sets `--workflow-step plan` after writing
   87	the plan (see S3.c).
   88	
   89	Ineligible or uncertain → today's two-gate flow (standalone spec review, then
   90	plan review) unchanged. The skill text frames this as a judgment call with a
   91	bias toward the standard two-gate flow: if any condition is doubtful, do not use
   92	the combined gate.
   93	
   94	### S3.b — `--combined-gate <spec-path>` flag
   95	
   96	`external-reviewer review --kind plan --combined-gate <path/to/spec.md>` takes
   97	the spec path as its explicit argument.
   98	
   99	**Validation** (both surfaced before any chain or reviewer work, matching the
  100	existing early-validation block at the top of the `review` dispatch):
  101	
  102	- `--combined-gate` is valid **only with `--kind plan`** — any other kind exits
  103	  **2** with a clear message.
  104	- The spec path **must exist** — a missing path exits **2** with a clear
  105	  message (same exit-2 idiom used today for a missing `--file`/`--context`).
  106	
  107	**Context attachment.** The resolved spec path is added to the review's context
  108	set so the spec is attached to the prompt and recorded as a context file. If the
  109	same path was also passed via `--context`, it is **deduplicated** (attached
  110	once) — resolved-path identity is the dedup key. This makes the spec attachment
  111	verifiable from the flag rather than inferred from whatever `--context` happens
  112	to carry (which also carries tracker files).
  113	
  114	**Prompt guidance.** When `--combined-gate` is set, the plan `MODE_GUIDANCE` is
  115	augmented with a spec-coverage instruction:
  116	
  117	> This plan's spec did not receive a standalone review. Also review the attached
  118	> spec for completeness, internal consistency, and groundedness; tag spec-level
  119	> findings distinctly.
  120	
  121	`make_prompt` currently formats `MODE_GUIDANCE[kind]` internally. To thread the
  122	augmentation cleanly, `make_prompt` gains an optional `extra_guidance: str |
  123	None = None` parameter; when set, it is appended to the kind's mode guidance
  124	before formatting. The default (`None`) keeps every existing call byte-identical.
  125	The guidance applies to **every round** of a combined chain (round-1 broad and
  126	incremental follow-ups), since the spec remains un-reviewed throughout.
  127	
  128	**Manifest stamp.** Each round entry (the dict assembled near
  129	`external-reviewer.py:3312`) records:
  130	
  131	- `combined_gate: true`
  132	- `combined_gate_spec: <repo-relative spec path, resolved against repo root>`
  133	
  134	Standalone plan rounds and all non-plan rounds do **not** carry these keys (see
  135	Open decisions resolved below), so existing chains read back unchanged.
  136	
  137	**Chain-level persistence and follow-up rounds.** A combined chain stays
  138	combined for its whole life: the spec remains un-reviewed, so every round must
  139	carry the guidance, attach the spec, and stamp the round. To make that robust
  140	against the caller forgetting the flag on a re-submit, the **first round
  141	persists `combined_gate_spec` at the chain (manifest top) level** — the same
  142	place and precedent as the stored `work_id`. On any later round of that chain:
  143	
  144	- If `--combined-gate` is **omitted**, the persisted chain-level
  145	  `combined_gate_spec` is reused automatically — the spec is re-attached to
  146	  context, the guidance is re-applied, and the round is re-stamped. The combined
  147	  classification therefore cannot silently lapse on round 2+.
  148	- If `--combined-gate <same-path>` is passed, behaviour is identical (idempotent).
  149	- If `--combined-gate <different-path>` is passed, the run exits **6** with a
  150	  chain-mismatch error — the same exit code and idiom used today for a
  151	  `--work-id` that disagrees with the chain's stored value. (A combined chain
  152	  cannot retroactively switch which spec it covers.)
  153	
  154	A chain that was **not** combined on round 1 (no persisted `combined_gate_spec`)
  155	and receives `--combined-gate` on a later round is rejected the same way (exit
  156	6): the combined decision is made at chain start, not mid-stream. This keeps the
  157	stats classification (any round combined ⇒ chain combined) consistent with the
  158	per-round stamps.
  159	
  160	### S3.b-stats — Combined-gate segmentation in `stats`
  161	
  162	`collect_review_stats` classifies each **plan** chain in the window:
  163	
  164	- **combined** if any in-window round has `combined_gate == true`;
  165	- **standalone** otherwise.
  166	
  167	A new top-level `combined_gate` block is added to the stats dict:
  168	
  169	```
  170	"combined_gate": {
  171	  "combined":   {"chains": <int>, "rounds": <int>},
  172	  "standalone": {"chains": <int>, "rounds": <int>}
  173	}
  174	```
  175	
  176	`chains` counts distinct plan chains in each class; `rounds` counts in-window
  177	round entries across those chains (round entries, matching the existing
  178	per-kind `round_count` convention — not reviewer invocations). Only plan chains
  179	are classified; non-plan kinds are not represented in this block.
  180	
  181	`print_stats_table` prints one summary line after the per-slice line, e.g.:
  182	
  183	```
  184	combined-gate (plan): combined=<chains>c/<rounds>r  standalone=<chains>c/<rounds>r
  185	```
  186	
  187	`--json` output carries the same `combined_gate` block. When there are no plan
  188	chains in the window, both classes report zeros (the block is always present
  189	for a stable schema).
  190	
  191	### S3.c — Workflow-step compatibility (verify-only)
  192	
  193	The combined-gate flow sets `tasktool set <slice-id> --workflow-step plan`
  194	directly from spec-written state, without an intervening spec-review-passed
  195	step. This must not be blocked.
  196	
  197	**Verified during this slice's design:** `tools/tasktool` enforces no
  198	step-ordering precondition — `_validate_set_flags`
  199	(`tools/tasktool/commands.py:110-117`) only checks that the supplied step value
  200	is a member of the allowed set for the row kind (slice:

[truncated: 101 additional lines]
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
   38	    },
   39	    {
   40	      "archived_date": "2026-05-24",
   41	      "archived_path": "docs/archived-tasks/X22-add-cancelled-terminal-status-to-tasktoo.md",
   42	      "id": "X22",
   43	      "title": "Add cancelled terminal status to tasktool"
   44	    },
   45	    {
   46	      "archived_date": "2026-05-24",
   47	      "archived_path": "docs/archived-tasks/X23-document-cancelled-lifecycle-and-admin-c.md",
   48	      "id": "X23",
   49	      "title": "Document cancelled lifecycle and admin closeout guidance"
   50	    },
   51	    {
   52	      "archived_date": "2026-05-26",
   53	      "archived_path": "docs/archived-tasks/X24-use-global-tasktool-shim-in-superstar-gu.md",
   54	      "id": "X24",
   55	      "title": "Use global tasktool shim in Superstar guidance"
   56	    },
   57	    {
   58	      "archived_date": "2026-05-26",
   59	      "archived_path": "docs/archived-tasks/X25-duck-media-audio-during-tasktool-tts-and.md",
   60	      "id": "X25",
   61	      "title": "Duck media audio during tasktool TTS and verify Codex plugin payload"
   62	    },
   63	    {
   64	      "archived_date": "2026-05-26",
   65	      "archived_path": "docs/archived-tasks/X26-fix-codex-marketplace-payload-refresh-fo.md",
   66	      "id": "X26",
   67	      "title": "Fix Codex marketplace payload refresh for Superstar"
   68	    },
   69	    {
   70	      "archived_date": "2026-05-26",
   71	      "archived_path": "docs/archived-tasks/X1-default-external-review-prompt-transport.md",
   72	      "id": "X1",
   73	      "title": "Default external-review prompt transport to stdin"
   74	    },
   75	    {
   76	      "archived_date": "2026-05-26",
   77	      "archived_path": "docs/archived-tasks/X2-add-repo-local-tasktool-launcher.md",
   78	      "id": "X2",
   79	      "title": "Add repo-local tasktool launcher"
   80	    },
   81	    {
   82	      "archived_date": "2026-05-26",
   83	      "archived_path": "docs/archived-tasks/X3-spot-fix-parse-bold-external-review-verd.md",
   84	      "id": "X3",
   85	      "title": "Spot fix: parse bold external-review verdict headings"
   86	    },
   87	    {
   88	      "archived_date": "2026-05-26",
   89	      "archived_path": "docs/archived-tasks/X4-spot-fix-broaden-legacy-tasklist-importe.md",
   90	      "id": "X4",
   91	      "title": "Spot fix: broaden legacy tasklist importer compatibility"
   92	    },
   93	    {
   94	      "archived_date": "2026-05-26",
   95	      "archived_path": "docs/archived-tasks/X5-add-finished-agent-notification-hook.md",
   96	      "id": "X5",
   97	      "title": "Add finished-agent notification hook"
   98	    },
   99	    {
  100	      "archived_date": "2026-05-26",
  101	      "archived_path": "docs/archived-tasks/X6-fix-codex-finished-agent-hook-compatibil.md",
  102	      "id": "X6",
  103	      "title": "Fix Codex finished-agent hook compatibility"
  104	    },
  105	    {
  106	      "archived_date": "2026-05-26",
  107	      "archived_path": "docs/archived-tasks/X7-fix-superstar-codex-plugin-payload-versi.md",
  108	      "id": "X7",
  109	      "title": "Fix Superstar Codex plugin payload version drift"
  110	    },
  111	    {
  112	      "archived_date": "2026-05-26",
  113	      "archived_path": "docs/archived-tasks/X8-move-semantic-notifications-from-agent-h.md",
  114	      "id": "X8",
  115	      "title": "Move semantic notifications from agent hooks to tasktool status changes"
  116	    },
  117	    {
  118	      "archived_date": "2026-05-26",
  119	      "archived_path": "docs/archived-tasks/X9-coalesce-bursty-tasktool-audio-notificat.md",
  120	      "id": "X9",
  121	      "title": "Coalesce bursty tasktool audio notifications"
  122	    },
  123	    {
  124	      "archived_date": "2026-05-26",
  125	      "archived_path": "docs/archived-tasks/X10-harden-external-review-verdict-parser-an.md",
  126	      "id": "X10",
  127	      "title": "Harden external-review verdict parser and prompt against Claude formatting variants"
  128	    },
  129	    {
  130	      "archived_date": "2026-05-26",
  131	      "archived_path": "docs/archived-tasks/X11-make-external-review-bridge-global.md",
  132	      "id": "X11",
  133	      "title": "Make external-review bridge global"
  134	    },
  135	    {
  136	      "archived_date": "2026-05-26",
  137	      "archived_path": "docs/archived-tasks/X12-tasktool-require-authoritative-checkout-.md",
  138	      "id": "X12",
  139	      "title": "tasktool: require authoritative-checkout routing for mutations"
  140	    },
  141	    {
  142	      "archived_date": "2026-05-26",
  143	      "archived_path": "docs/archived-tasks/X13-fix-tasktool-close-repeated-refs-parsing.md",
  144	      "id": "X13",
  145	      "title": "Fix tasktool close repeated refs parsing"
  146	    },
  147	    {
  148	      "archived_date": "2026-05-26",
  149	      "archived_path": "docs/archived-tasks/X14-stabilize-local-claude-codex-plugin-curr.md",
  150	      "id": "X14",
  151	      "title": "Stabilize local Claude/Codex plugin current entrypoints"
  152	    },
  153	    {
  154	      "archived_date": "2026-05-26",
  155	      "archived_path": "docs/archived-tasks/X17-make-spec-and-plan-artifact-handling-tra.md",
  156	      "id": "X17",
  157	      "title": "Make spec and plan artifact handling transactional"
  158	    },
  159	    {
  160	      "archived_date": "2026-05-26",
  161	      "archived_path": "docs/archived-tasks/X27-add-tasktool-tts-for-workflow-artifacts-.md",
  162	      "id": "X27",
  163	      "title": "Add tasktool TTS for workflow artifacts and step changes"
  164	    },
  165	    {
  166	      "archived_date": "2026-05-26",
  167	      "archived_path": "docs/archived-tasks/X28-prefer-explicit-notification-ding-sound-.md",
  168	      "id": "X28",
  169	      "title": "Prefer explicit notification ding sound file"
  170	    }
  171	  ],
  172	  "archived_phases": [
  173	    {
  174	      "archived_date": "2026-05-18",
  175	      "archived_path": "docs/archived-tasks/P2-tasktool-json-backed-task-management-cli.md",
  176	      "id": "P2",
  177	      "title": "tasktool: JSON-backed task management CLI"
  178	    },
  179	    {
  180	      "archived_date": "2026-05-19",
  181	      "archived_path": "docs/archived-tasks/P4-tasktool-coordination-and-lifecycle-auth.md",
  182	      "id": "P4",
  183	      "title": "Tasktool coordination and lifecycle authority"
  184	    },
  185	    {
  186	      "archived_date": "2026-05-19",
  187	      "archived_path": "docs/archived-tasks/P3-phase-planning-workflow.md",
  188	      "id": "P3",
  189	      "title": "Phase planning workflow"
  190	    },
  191	    {
  192	      "archived_date": "2026-05-20",
  193	      "archived_path": "docs/archived-tasks/P1-external-reviewer-work-historical.md",
  194	      "id": "P1",
  195	      "title": "External-reviewer work (historical)"
  196	    },
  197	    {
  198	      "archived_date": "2026-05-21",
  199	      "archived_path": "docs/archived-tasks/P5-tasktool-owned-worktree-lifecycle-using-.md",
  200	      "id": "P5",

[truncated: 241 additional lines]

<!-- superstar-prompt:end -->