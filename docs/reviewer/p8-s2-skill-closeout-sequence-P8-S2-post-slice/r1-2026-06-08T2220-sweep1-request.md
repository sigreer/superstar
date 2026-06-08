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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p8-s2-skill-updates-merge-back-before-close

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-05-P8.S2-skill-closeout-sequence.md

Additional context files:
- docs/specs/2026-06-05-P8.S2-skill-closeout-sequence-design.md
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

### docs/plans/2026-06-05-P8.S2-skill-closeout-sequence.md

    1	# P8.S2 — Skill Closeout Sequence Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Align Superstar's skill prose with the P8.S1 landed-branch close gate: slice closeout must review, merge back, close, and cleanly prune in that order, while documenting that tracker bookkeeping is shared and sibling artifacts remain isolated.
    6	
    7	**Architecture:** This is a skill-content slice with string-level regression tests. Update the canonical top-level `skills/` source tree only; `plugins/superstar/skills/` is a generated mirror and must not be hand-edited. Keep the edits narrow: one closeout sequence in `subagent-driven-development`, one non-interactive merge-back clarification in `finishing-a-development-branch`, one sibling-boundary rule in `tasklist-discipline`, and matching tests in `test_skill_tasktool_lifecycle_docs.py`.
    8	
    9	**Tech Stack:** Markdown skill files, Python pytest string assertions. No new dependencies.
   10	
   11	---
   12	
   13	## Scheduling Contract
   14	
   15	`P8.S2` depends on `P8.S1`, and `P8.S1` is done. `tasktool schedule P8`, `tasktool ready-slices P8`, and `tasktool surface check P8` show `P8.S2` is ready with no unguarded surface overlaps.
   16	
   17	| Slice | integration_surfaces | reservations | coordination_group |
   18	|-------|---------------------|--------------|--------------------|
   19	| `P8.S1` | `lifecycle` | (none) | (none) |
   20	| `P8.S2` | `skills`, `lifecycle-docs-test` | (none) | (none) |
   21	
   22	This plan does not change `depends_on`, `parallel_group`, `coordination_group`, or reservations. After the plan review passes, run `tasktool ratify P8.S2`.
   23	
   24	## File Structure
   25	
   26	- **Modify** `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:
   27	  - Add focused string regressions for the new slice-end order, non-interactive merge-back, non-force prune, and sibling-boundary prose.
   28	- **Modify** `skills/subagent-driven-development/SKILL.md`:
   29	  - Replace the slice-end list steps 3-6 with review -> fix loop -> non-interactive merge-back -> close -> clean prune.
   30	  - Update the process diagram to insert `Merge back to base branch` and `tasktool worktree prune <slice-id>` nodes between post-slice review readiness and phase checks.
   31	  - Update the phase-end finishing sentence so it cannot imply per-slice merge/prune repeats.
   32	- **Modify** `skills/finishing-a-development-branch/SKILL.md`:
   33	  - Add a non-interactive per-slice merge-back entry before the Step 4 menu.
   34	  - Clarify that Step 5's merge mechanics can be used before close, but Step 6 tasktool prune waits until after `tasktool close`.
   35	  - Strengthen normal prune guidance: no `--force` on the closeout path.
   36	- **Modify** `skills/tasklist-discipline/SKILL.md`:
   37	  - Add a shared-tracker versus sibling-artifact boundary paragraph.
   38	  - Add the red-flag row for co-staged sibling close state.
   39	
   40	Do **not** modify `skills/using-git-worktrees/SKILL.md`. If implementation discovers a direct contradiction there, stop and update both `tools/tasktool/tests/fixtures/p5_s3_skill_body.txt` and `tools/tasktool/tests/fixtures/p5_s3_subagent_load.txt` in the same commit; that is not expected.
   41	
   42	Do **not** hand-edit `plugins/superstar/skills/**`. Before final commit, run:
   43	
   44	```bash
   45	diff -qr skills plugins/superstar/skills || true
   46	```
   47	
   48	Use the output only as a mirror drift check. This slice is accepted when canonical `skills/` and tests are correct; plugin mirror sync/publish is not part of this slice.
   49	
   50	## Working Conventions
   51	
   52	- Start implementation from the authoritative checkout with `tasktool start P8.S2`, then work inside the printed `.worktrees/worktree-p8-s2-...` path.
   53	- Commit after each green task. Do not commit the intentionally failing test-only state from Task 1.
   54	- Run focused tests from the active implementation worktree:
   55	
   56	```bash
   57	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
   58	```
   59	
   60	- Final verification:
   61	
   62	```bash
   63	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
   64	python -m pytest tools/tasktool/tests -q
   65	```
   66	
   67	---
   68	
   69	### Task 0: Start the slice and confirm the canonical edit tree
   70	
   71	**Files:** none (lifecycle and inspection only)
   72	
   73	- [ ] **Step 1: Start the slice and enter the worktree**
   74	
   75	Run from the authoritative checkout:
   76	
   77	```bash
   78	tasktool start P8.S2
   79	```
   80	
   81	Expected: prints a worktree path under `.worktrees/worktree-p8-s2-...` and records `worktree_path` / `worktree_branch` on the row.
   82	
   83	Then run:
   84	
   85	```bash
   86	cd .worktrees/worktree-p8-s2-skill-updates-merge-back-before-cl
   87	```
   88	
   89	Use the exact path printed by `tasktool start`.
   90	
   91	- [ ] **Step 2: Confirm the test harness reads top-level `skills/`**
   92	
   93	Run:
   94	
   95	```bash
   96	sed -n '1,14p' tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
   97	```
   98	
   99	Expected: `skill_text()` reads `(ROOT / "skills" / name / "SKILL.md")`.
  100	
  101	- [ ] **Step 3: Baseline focused test**
  102	
  103	Run:
  104	
  105	```bash
  106	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
  107	```
  108	
  109	Expected: passes before changes. If it fails, stop and report the failure.
  110	
  111	---
  112	
  113	### Task 1: Add failing `subagent-driven-development` lifecycle-doc tests
  114	
  115	**Files:**
  116	- Modify: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`
  117	
  118	- [ ] **Step 1: Append failing subagent-driven-development tests**
  119	
  120	Add these tests near the existing `test_subagent_driven_development_has_integrate_main_checkpoint` test:
  121	
  122	```python
  123	def _slice_end_section(text: str) -> str:
  124	    start = text.index("- **At the end of each slice**")
  125	    end = text.index("- **At the end of the phase**", start)
  126	    return text[start:end]
  127	
  128	
  129	def test_subagent_driven_development_merges_before_close_and_prunes_after() -> None:
  130	    text = skill_text("subagent-driven-development")
  131	    section = _slice_end_section(text)
  132	
  133	    review_ready = section.index("On `ready` / `ready with small edits`, proceed")
  134	    merge_back = section.index("merge the worktree branch back")
  135	    close = section.index("tasktool close <slice-id>")
  136	    prune = section.index("tasktool worktree prune <slice-id>")
  137	
  138	    assert review_ready < merge_back < close < prune
  139	    assert "[[finishing-a-development-branch]]" in section
  140	    assert "must not present the interactive Step 4 options menu" in section
  141	    assert "Option 1 merge mechanics" in section
  142	    assert "landed-branch gate" in section
  143	    assert "auto-commits" in section
  144	    assert "--force" in section
  145	    assert "normal closeout path" in section
  146	
  147	
  148	def test_subagent_driven_development_diagram_has_merge_close_prune_order() -> None:
  149	    text = skill_text("subagent-driven-development")
  150	    diagram_start = text.index("digraph process")
  151	    diagram_end = text.index("## Model Selection", diagram_start)
  152	    diagram = text[diagram_start:diagram_end]
  153	
  154	    assert '"Merge back to base branch"' in diagram
  155	    assert '"tasktool worktree prune <slice-id>"' in diagram
  156	    assert '"post-slice verdict ready?" -> "Merge back to base branch"' in diagram
  157	    assert '"Merge back to base branch" -> "tasktool close <slice-id>"' in diagram
  158	    assert '"tasktool close <slice-id>" -> "tasktool worktree prune <slice-id>"' in diagram
  159	    assert '"post-slice verdict ready?" -> "tasktool close <slice-id>"' not in diagram
  160	```
  161	
  162	- [ ] **Step 2: Run the focused tests and confirm failure**
  163	
  164	Run:
  165	
  166	```bash
  167	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
  168	```
  169	
  170	Expected: the two new tests fail because the new prose has not been added yet.
  171	
  172	- [ ] **Step 3: Leave the failing tests uncommitted**
  173	
  174	Do not commit yet. Task 2 will make these two tests pass and commit them with the matching skill change.
  175	
  176	---
  177	
  178	### Task 2: Update `subagent-driven-development` slice-end flow
  179	
  180	**Files:**
  181	- Modify: `skills/subagent-driven-development/SKILL.md`
  182	
  183	- [ ] **Step 1: Replace the slice-end closeout list**
  184	
  185	In `skills/subagent-driven-development/SKILL.md`, replace the current steps 3-6 under `- **At the end of each slice**` with this block, preserving existing steps 1-2:
  186	
  187	```markdown
  188	  3. Invoke `[[external-review]]` with `--kind post-slice`, passing the plan as `--file` and the spec + `docs/tasklist.json` as `--context`.
  189	  4. Read the verdict. On `ready` / `ready with small edits`, proceed to merge-back. On `merged_verdict: revise` (or `verdict_valid: false`), **dispatch a fix subagent** with the previous response file as input. The fix subagent MUST write `docs/reviewer/<chain>/r{N}-resolution.md` per the contract in `[[external-review]]` before signaling completion. Wait for completion. Re-submit. Iterate.
  190	  5. **Merge back before close.** For a tasktool-owned implementation worktree, use `[[finishing-a-development-branch]]` Option 1 merge mechanics to merge the worktree branch back to the base branch in this same session. In autonomous per-slice closeout, this must not present the interactive Step 4 options menu: the user already asked the session to execute, so run the Option 1 merge mechanics directly, verify on the merged base branch, and return here. Do not run that skill's cleanup/prune step before close.
  191	  6. Run `tasktool close <slice-id>`. The CLI re-checks the reviewer chain, refuses on `revise`, re-checks the landed-branch gate from P8.S1, and auto-commits the lifecycle-authored tracker/archive files it writes. See `[[tasklist-discipline]]`.
  192	  7. **Clean prune after close.** Run `tasktool worktree prune <slice-id>` on the normal closeout path. Do not use `--force` for normal closeout: forced prune is only for discard or irrecoverable scratch cleanup, bypasses normal landed/clean guards, and can skip the landed-base evidence stamp.
  193	```
  194	
  195	- [ ] **Step 2: Update the phase-end line**
  196	
  197	In the phase-end list, replace this current step:
  198	
  199	```markdown
  200	  4. On verdict acceptance, run `tasktool archive-phase <phase-id>` (the CLI re-checks the post-phase chain), then invoke `[[finishing-a-development-branch]]`.
  201	```
  202	
  203	with:
  204	
  205	```markdown
  206	  4. On verdict acceptance, run `tasktool archive-phase <phase-id>` (the CLI re-checks the post-phase chain), then invoke `[[finishing-a-development-branch]]` only for any remaining branch finalization. Under the normal per-slice flow, slice branches have already merged and tasktool-owned worktrees have already been pruned. Verify no tasktool-owned slice worktree remains before doing any cleanup, and do not re-run per-slice prune against rows with no recorded worktree.
  207	```
  208	
  209	- [ ] **Step 3: Update the process diagram nodes and edges**
  210	
  211	In the `digraph process` block, replace the single close edge:
  212	
  213	```dot
  214	    "post-slice verdict ready?" -> "tasktool close <slice-id>" [label="ready"];
  215	    "tasktool close <slice-id>" -> "Last slice in phase?";
  216	```
  217	
  218	with:
  219	
  220	```dot
  221	    "Merge back to base branch" [shape=box];
  222	    "tasktool worktree prune <slice-id>" [shape=box];
  223	    "post-slice verdict ready?" -> "Merge back to base branch" [label="ready"];
  224	    "Merge back to base branch" -> "tasktool close <slice-id>";
  225	    "tasktool close <slice-id>" -> "tasktool worktree prune <slice-id>";
  226	    "tasktool worktree prune <slice-id>" -> "Last slice in phase?";
  227	```
  228	
  229	If the file already declares nodes separately from edges in that region, place the two new node declarations near `"tasktool close <slice-id>" [shape=box];` and keep the edges in the flow section. The test requires the exact edge strings above.
  230	
  231	- [ ] **Step 4: Run tests and confirm remaining failures are outside this skill**
  232	
  233	Run:
  234	
  235	```bash
  236	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
  237	```
  238	
  239	Expected: all tests in `test_skill_tasktool_lifecycle_docs.py` pass.
  240	
  241	- [ ] **Step 5: Commit**
  242	
  243	```bash
  244	git add tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py skills/subagent-driven-development/SKILL.md
  245	git commit -m "docs: merge back before slice close"
  246	```
  247	
  248	---
  249	
  250	### Task 3: Update `finishing-a-development-branch` merge/prune guidance
  251	
  252	**Files:**
  253	- Modify: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`
  254	- Modify: `skills/finishing-a-development-branch/SKILL.md`
  255	
  256	- [ ] **Step 1: Add the failing finishing-branch test**
  257	
  258	Add this test near the other skill lifecycle tests:
  259	
  260	```python
  261	def test_finishing_branch_documents_noninteractive_per_slice_mergeback() -> None:
  262	    text = skill_text("finishing-a-development-branch")
  263	
  264	    assert "Non-Interactive Per-Slice Merge-Back" in text
  265	    assert "skip Step 4" in text
  266	    assert "Option 1 merge mechanics" in text
  267	    assert "return to `subagent-driven-development`" in text
  268	    assert "Do not run Step 6 cleanup before `tasktool close <slice-id>`" in text
  269	    assert "tasktool worktree prune <slice-id>" in text
  270	    assert "--force" in text
  271	    assert "not the normal closeout path" in text
  272	```
  273	
  274	- [ ] **Step 2: Run the focused tests and confirm failure**
  275	
  276	Run:
  277	
  278	```bash
  279	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
  280	```
  281	
  282	Expected: the new `finishing-a-development-branch` test fails because the prose has not been added yet.
  283	
  284	- [ ] **Step 3: Add a non-interactive per-slice section before Step 4**
  285	
  286	Insert this section immediately before `### Step 4: Present Options`:
  287	
  288	```markdown
  289	### Non-Interactive Per-Slice Merge-Back
  290	
  291	When `subagent-driven-development` reaches per-slice closeout for a tasktool-owned implementation worktree, it may call into this skill for the Option 1 merge mechanics without presenting the interactive menu. In that path, skip Step 4, run the Option 1 merge mechanics from Step 5 directly, verify on the merged base branch, and return to `subagent-driven-development` for `tasktool close <slice-id>` and post-close prune.
  292	
  293	Do not run Step 6 cleanup before `tasktool close <slice-id>`. `tasktool worktree prune <slice-id>` requires a terminal row, so prune belongs after close in the normal slice-end sequence.
  294	```
  295	
  296	- [ ] **Step 4: Clarify the end of Option 1**
  297	
  298	In Step 5's Option 1 block, replace:
  299	
  300	```markdown
  301	Then run Cleanup workspace (Step 6).
  302	```
  303	
  304	with:
  305	
  306	```markdown
  307	Then run Cleanup workspace (Step 6), except when this option is being used as the non-interactive per-slice merge-back from `subagent-driven-development`. In that per-slice path, return to `subagent-driven-development`; it will run `tasktool close <slice-id>` first and then run Step 6 cleanup afterward.
  308	```
  309	
  310	- [ ] **Step 5: Strengthen tasktool prune guidance**
  311	
  312	In Step 6, after the paragraph that starts `` `prune` enforces three guards``, replace this existing sentence:
  313	
  314	```markdown
  315	For an irrecoverable scratch worktree, `tasktool worktree prune <slice-id> --force` overrides the prune guards only; it does not affect close, slice status, or review gates.
  316	```
  317	
  318	with:
  319	
  320	```markdown
  321	For an irrecoverable scratch worktree, `tasktool worktree prune <slice-id> --force` overrides the prune guards only; it does not affect close, slice status, or review gates. `--force` is not the normal closeout path: it bypasses the landed/clean proof used by normal prune and can skip the landed-base evidence stamp.
  322	```
  323	
  324	- [ ] **Step 6: Run focused tests**
  325	
  326	Run:
  327	
  328	```bash
  329	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
  330	```
  331	
  332	Expected: all tests in `test_skill_tasktool_lifecycle_docs.py` pass.
  333	
  334	- [ ] **Step 7: Commit**
  335	
  336	```bash
  337	git add tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py skills/finishing-a-development-branch/SKILL.md
  338	git commit -m "docs: split merge-back from prune cleanup"
  339	```
  340	
  341	---
  342	
  343	### Task 4: Update `tasklist-discipline` sibling boundary
  344	
  345	**Files:**
  346	- Modify: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`
  347	- Modify: `skills/tasklist-discipline/SKILL.md`
  348	
  349	- [ ] **Step 1: Add the failing tasklist-discipline test**
  350	
  351	Add this test near `test_tasklist_discipline_documents_surface_reserve_coordinate`:
  352	
  353	```python
  354	def test_tasklist_discipline_documents_shared_tracker_boundary() -> None:
  355	    text = skill_text("tasklist-discipline")
  356	
  357	    assert "Shared tracker versus sibling artifacts" in text
  358	    assert "`docs/tasklist.json` is the shared canonical tracker" in text
  359	    assert "Truthful sibling lifecycle rows are bookkeeping" in text
  360	    assert "Sibling artifacts remain hands-off" in text
  361	    assert "implementation files, specs, plans, handoffs, reviewer chains" in text
  362	    assert "A sibling's close is co-staged, so I must stop" in text
  363	    assert "tracker is whole-file bookkeeping" in text
  364	```
  365	
  366	- [ ] **Step 2: Run the focused tests and confirm failure**
  367	
  368	Run:
  369	
  370	```bash
  371	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
  372	```
  373	
  374	Expected: the new `tasklist-discipline` test fails because the prose has not been added yet.
  375	
  376	- [ ] **Step 3: Add the shared tracker boundary paragraph**
  377	
  378	Insert this paragraph after the `**Implementation isolation boundary:**` paragraph and before `**Administrative closeout exception:**`:
  379	
  380	```markdown
  381	**Shared tracker versus sibling artifacts.** `docs/tasklist.json` is the shared canonical tracker. Truthful sibling lifecycle rows are bookkeeping, not sibling implementation work, and P8.S1 close/prune commands auto-commit the lifecycle-authored tracker/archive files they write through scoped path commits. Do not stop merely because a sibling's close state is visible in the tracker. Sibling artifacts remain hands-off: implementation files, specs, plans, handoffs, reviewer chains, archived task files not authored by the current lifecycle command, setup/migration files, and any non-tracker files outside the current scope must not be committed or rewritten by the current slice. If co-staged sibling tracker state appears, inspect the path set and proceed only when the staged paths are tracker lifecycle bookkeeping; ask only when sibling artifacts or unrelated files are mixed in.
  382	```
  383	
  384	- [ ] **Step 4: Add the red-flag row**
  385	
  386	In the Red flags table, add this row near the setup/artifact boundary rows:
  387	
  388	```markdown
  389	| "A sibling's close is co-staged, so I must stop." | The tracker is whole-file bookkeeping. Truthful sibling lifecycle rows in `docs/tasklist.json` can be carried by scoped lifecycle commits; leave sibling artifacts alone and stop only when non-tracker files are mixed in. |
  390	```
  391	
  392	- [ ] **Step 5: Run focused tests**
  393	
  394	Run:
  395	
  396	```bash
  397	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
  398	```
  399	
  400	Expected: all tests in `test_skill_tasktool_lifecycle_docs.py` pass.
  401	
  402	- [ ] **Step 6: Commit**
  403	
  404	```bash
  405	git add tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py skills/tasklist-discipline/SKILL.md
  406	git commit -m "docs: clarify shared tracker closeout boundary"
  407	```
  408	
  409	---
  410	
  411	### Task 5: Final verification and closeout preparation
  412	
  413	**Files:** none expected, unless formatting/test adjustments are required.
  414	
  415	- [ ] **Step 1: Run focused lifecycle-doc tests**
  416	
  417	Run:
  418	
  419	```bash
  420	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
  421	```
  422	
  423	Expected: pass.
  424	
  425	- [ ] **Step 2: Run the full tasktool test suite**
  426	
  427	Run:
  428	
  429	```bash
  430	python -m pytest tools/tasktool/tests -q
  431	```
  432	
  433	Expected: pass.
  434	
  435	- [ ] **Step 3: Confirm `using-git-worktrees` was not touched**
  436	
  437	Run:
  438	
  439	```bash
  440	git diff --name-only main...HEAD | rg '(^|/)using-git-worktrees/' || true
  441	```
  442	
  443	Expected: no output. If there is output, run:
  444	
  445	```bash
  446	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py::test_using_git_worktrees_matches_token_budget_fixture tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py::test_subagent_early_exit_load_matches_fixture -q
  447	```
  448	
  449	Expected: pass, and the commit message must explain why `using-git-worktrees` changed.
  450	
  451	- [ ] **Step 4: Check generated mirror drift without editing it**
  452	
  453	Run:
  454	
  455	```bash
  456	diff -qr skills plugins/superstar/skills || true
  457	```
  458	
  459	Expected: output may report drift because this slice edits canonical `skills/` only. Do not hand-edit `plugins/superstar/skills/**` for this slice.
  460	
  461	- [ ] **Step 5: Ask the required version-bump question before final closeout commit/merge**
  462	
  463	Because this slice changes user-shipping `skills/` content, ask:
  464	
  465	```text
  466	Bump the version before/after this commit? (current: X.Y.Z -> patch X.Y.(Z+1) / minor X.(Y+1).0 / no bump)
  467	```
  468	
  469	Use the current version from `package.json`. If the user is still AFK, stop before a version bump decision; do not silently bump. This question is required by `AGENTS.md` before finished skill work ships.
  470	
  471	- [ ] **Step 6: Post-slice review and close**
  472	
  473	After implementation commits and verification pass, run:
  474	
  475	```bash
  476	external-reviewer review --kind post-slice --file docs/plans/2026-06-05-P8.S2-skill-closeout-sequence.md --work-id P8.S2 --context docs/specs/2026-06-05-P8.S2-skill-closeout-sequence-design.md --context docs/tasklist.json --review-depth thorough --emit json
  477	```
  478	
  479	If the reviewer returns `revise`, delegate fixes to a fix subagent and write `docs/reviewer/<chain>/rN-resolution.md` before resubmitting.
  480	
  481	When the post-slice verdict is `ready` / `ready with small edits`, dogfood the new sequence:
  482	
  483	```bash
  484	# Merge worktree branch back to main using the non-interactive Option 1 merge mechanics.
  485	# Then close and cleanly prune.
  486	tasktool close P8.S2
  487	tasktool worktree prune P8.S2
  488	```
  489	
  490	Expected: `tasktool close` succeeds only after the worktree branch has landed; normal prune succeeds without `--force`.

## Context Previews

### docs/specs/2026-06-05-P8.S2-skill-closeout-sequence-design.md

    1	# P8.S2 — skill closeout sequence alignment
    2	
    3	**Status:** spec (brainstormed 2026-06-05)
    4	**Slice row:** `P8.S2` · Phase doc: [`docs/specs/2026-06-05-P8-closeout-integrity-design.md`](2026-06-05-P8-closeout-integrity-design.md)
    5	**Dependency:** `P8.S1` is done. This slice documents the close gate and lifecycle auto-commit behavior shipped by P8.S1; it does not describe aspirational behavior.
    6	
    7	## Problem
    8	
    9	P7 closeout proved that the workflow prose still allowed agents to finish in the wrong order: post-slice review passed, `tasktool close` marked the slice done, but the worktree branch was never merged back to `main`. P8.S1 made the worst state unrepresentable in tooling by refusing close/set-done on unlanded recorded branches and by auto-committing close/prune tracker changes.
   10	
   11	The skills now need to teach the same operational sequence. If the prose still says "review then close" without a merge-back step, future agents will hit the P8.S1 refusal late and may misread the refusal as a tooling problem. If prune guidance still normalizes `--force`, agents can remove worktrees without the normal landed proof and skip the `landed_base_sha` stamp. If `tasklist-discipline` treats any sibling tracker mutation as a blocker, concurrent closeout agents can recreate the P7 politeness deadlock even though the tracker is shared bookkeeping.
   12	
   13	## Design Decisions
   14	
   15	| # | Decision | Rationale |
   16	|---|----------|-----------|
   17	| D1 | Update `subagent-driven-development` so it preserves the existing scope preflight and integrate-current-main checkpoint, then inserts merge-back after post-slice external review and before `tasktool close <slice-id>`, followed by clean non-force prune. | Matches P8.S1's landed-branch close gate. The merge-back belongs in the same session after review and before close so the tracker cannot say done while the deliverables live only on a worktree branch. |
   18	| D2 | Describe `tasktool close` as auto-committing its lifecycle-authored files after P8.S1, while preserving the rule that sibling implementation artifacts remain hands-off. | P8.S1 changed close/prune tracker behavior from staged-only to scoped auto-commit. The skill should reduce deadlocks without inviting broad commits. |
   19	| D3 | Add explicit non-force prune guidance: clean the worktree and run `tasktool worktree prune <slice-id>` without `--force`; use `--force` only for discard/irrecoverable scratch cleanup, because it bypasses landed proof and skips the landed-sha stamp. | The normal path should preserve provenance. Forced prune is destructive cleanup, not routine closeout. |
   20	| D4 | Update `tasklist-discipline` to distinguish sibling artifacts from shared tracker state in `docs/tasklist.json`. | Agents must still stop before committing another slice's code, spec, plan, or reviewer artifacts. They should not stop merely because another closeout produced true tracker state in the shared canonical file, and P8.S1 should make lingering co-staged tracker state rare. |
   21	| D5 | Keep `using-git-worktrees` unchanged unless implementation finds a direct contradiction. | It is intentionally thin and fixture-pinned by `test_using_git_worktrees_matches_token_budget_fixture`; changing it would expand this slice's blast radius. |
   22	| D6 | Update `finishing-a-development-branch` so agents can use Option 1's merge mechanics before slice close without also running its cleanup step before the row is terminal. | The closeout sequence should reuse that skill's merge mechanics, but prune must remain a dedicated post-close step because tasktool prune requires a done/cancelled row. |
   23	
   24	## Required Behavior
   25	
   26	### 1. `subagent-driven-development` slice-end sequence
   27	
   28	The "At the end of each slice" list must explicitly include a merge-back step after post-slice external review reaches `ready` / `ready with small edits` and before `tasktool close <slice-id>`.
   29	
   30	The step must:
   31	
   32	- invoke or reference `[[finishing-a-development-branch]]`;
   33	- state that local merge option 1's merge mechanics are the normal path for a tasktool-owned implementation worktree when the user asked the session to finish autonomously;
   34	- state that autonomous per-slice closeout must not present the interactive Step 4 options menu; it uses the Option 1 merge mechanics directly because `subagent-driven-development` has a continuous-execution contract;
   35	- state that only the merge portion of `finishing-a-development-branch` runs before close; its cleanup/prune step is deferred until after `tasktool close <slice-id>`;
   36	- require verification on the merged base branch before close;
   37	- say `tasktool close <slice-id>` will re-check the post-slice review gate and the landed-branch gate;
   38	- say close auto-commits the lifecycle-authored tracker/archive files after P8.S1;
   39	- say clean prune follows close and must be non-force in the normal path.
   40	
   41	The process diagram in the same skill must reflect the same ordering by adding both a merge-back node and a per-slice non-force prune node: post-slice review ready -> merge back to base -> `tasktool close <slice-id>` -> non-force prune. There must be no path that implies `tasktool close` before merge-back for tasktool-owned worktrees.
   42	
   43	### 2. `finishing-a-development-branch` under the new per-slice flow
   44	
   45	`finishing-a-development-branch` must distinguish merge-back from cleanup for tasktool-owned implementation worktrees:
   46	
   47	- Option 1's merge mechanics may be used from `subagent-driven-development` after post-slice review and before `tasktool close`.
   48	- The skill must document a non-interactive per-slice merge-back entry for tasktool-owned worktrees: skip the Step 4 menu, run the Option 1 merge mechanics, and return to `subagent-driven-development` for close and prune.
   49	- Option 1's cleanup step must not be run before close, because `tasktool worktree prune <slice-id>` refuses until the row is terminal.
   50	- Once `subagent-driven-development` has closed and pruned every slice as part of per-slice closeout, the phase-end invocation is branch finalization only. It should verify that no tasktool-owned slice worktrees remain to merge/prune and should not re-run per-slice prune against rows with no recorded worktree.
   51	
   52	### 3. Prune guidance
   53	
   54	Any closeout prose that mentions worktree cleanup must say the normal command is:
   55	
   56	```bash
   57	tasktool worktree prune <slice-id>
   58	```
   59	
   60	The prose must explain that `--force` is reserved for discard or irrecoverable scratch cleanup. The reason must be operational, not stylistic: forced prune bypasses normal guards, can leave `merged_proven=False`, and does not provide the normal landed-base stamp evidence. The implementing agent may use the exact internal field names that exist after P8.S1/P7.S4, but the meaning must be clear.
   61	
   62	### 4. Shared tracker versus sibling artifacts
   63	
   64	`tasklist-discipline` must gain a sibling-boundary paragraph near the implementation isolation / workflow artifact guidance and a red-flag row covering this mistaken reasoning:
   65	
   66	> "A sibling's close is co-staged, so I must stop."
   67	
   68	The replacement rule:
   69	
   70	- `docs/tasklist.json` is a shared canonical tracker. Truthful sibling lifecycle rows are bookkeeping, not sibling implementation work.
   71	- It is acceptable for lifecycle auto-commit to commit the whole tracker state it authored or had to carry, provided the command commits only declared lifecycle-authored paths.
   72	- Agents must still leave sibling artifacts alone: implementation files, specs, plans, handoffs, reviewer chains, archived task files not authored by the current lifecycle command, and any setup/migration files outside the current scope.
   73	- After P8.S1, `tasktool close` and normal prune should auto-commit their lifecycle mutations, so a lingering co-staged sibling close should be unusual. If encountered, inspect the path set and use the scoped tasktool command or ask only when non-tracker artifacts are mixed in.
   74	
   75	### 5. Tests
   76	
   77	Extend `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` with string-level regressions for:
   78	
   79	- the merge-back step in `subagent-driven-development` appears after post-slice review readiness and before the slice-end prose occurrence of `tasktool close <slice-id>`; anchor this assertion on nearby slice-end text so it cannot match the diagram or red-flag occurrences accidentally;
   80	- the skill references `[[finishing-a-development-branch]]` or the exact skill name in the slice-end closeout section;
   81	- the slice-end closeout prose explicitly avoids presenting the interactive options menu during autonomous per-slice closeout;
   82	- the normal prune command is non-force and the prose warns against routine `--force`;
   83	- `tasklist-discipline` documents the shared tracker versus sibling artifact boundary;
   84	- the new red-flag row contains the co-staged sibling close misconception and the corrected tracker-bookkeeping rule.
   85	
   86	If implementation touches `using-git-worktrees`, it must also update `tools/tasktool/tests/fixtures/p5_s3_skill_body.txt` and `tools/tasktool/tests/fixtures/p5_s3_subagent_load.txt` in the same commit. The preferred outcome is no `using-git-worktrees` edit.
   87	
   88	## File Scope
   89	
   90	Top-level `skills/` is the canonical source tree for skill content in this repo. `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` reads from `skills/<name>/SKILL.md`, and the publish scripts regenerate `plugins/superstar/skills/` from that source tree. Do not hand-edit the generated mirror for this slice.
   91	
   92	Expected files:
   93	
   94	- `skills/subagent-driven-development/SKILL.md`
   95	- `skills/tasklist-discipline/SKILL.md`
   96	- `skills/finishing-a-development-branch/SKILL.md`
   97	- `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`
   98	
   99	Conditional files:
  100	
  101	- `skills/using-git-worktrees/SKILL.md` and its fixtures only if a direct contradiction is found. Avoid this by default.
  102	- `plugins/superstar/skills/**` only if the implementation intentionally regenerates or syncs the plugin mirror after changing top-level `skills/`; mirror-only edits are wrong.
  103	
  104	## Scheduling and Surfaces
  105	
  106	`P8.S2` remains serialized after `P8.S1`; P8.S1 is already done, so this slice is ready. No `parallel_group`, `coordination_group`, or reservations are needed.
  107	
  108	| Slice | integration_surfaces | reservations | coordination_group |
  109	|-------|---------------------|--------------|--------------------|
  110	| `P8.S1` | `lifecycle` | (none) | (none) |
  111	| `P8.S2` | `skills`, `lifecycle-docs-test` | (none) | (none) |
  112	
  113	`tasktool surface check P8` should report no unguarded overlaps.
  114	
  115	## Acceptance
  116	
  117	- `python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` passes.
  118	- The updated `subagent-driven-development` skill has exactly one coherent normal slice-end order: review, merge-back, close, non-force prune.
  119	- The updated `finishing-a-development-branch` skill no longer implies that pre-close merge-back must also run pre-close prune.
  120	- The updated `tasklist-discipline` skill gives agents a concrete sibling-boundary rule that permits shared tracker bookkeeping while preserving artifact isolation.
  121	- The implementation does not modify `using-git-worktrees` unless its fixtures are updated and the change is justified in the commit message.
  122	
  123	## Out of Scope
  124	
  125	- Any change to tasktool close/prune behavior; P8.S1 owns the tooling.
  126	- Performing a release or local publish. Because this slice changes user-shipping `skills/` content, the closeout agent must still ask the repo-policy version-bump question before committing finished implementation work.
  127	- Any broad rewrite of skill voice, headings, or workflow philosophy beyond the closeout integrity correction.
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

[truncated: 291 additional lines]

<!-- superstar-prompt:end -->