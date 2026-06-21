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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-x31-tasktool-janitor-cleanup-skill

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-21-X31-tasktool-janitor-skill.md

Additional context files:
- docs/specs/2026-06-21-X31-tasktool-janitor-skill-design.md

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

### docs/plans/2026-06-21-X31-tasktool-janitor-skill.md

    1	# Tasktool Janitor Skill Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Add a reusable on-demand Superstar skill, `tasktool-janitor`, for evidence-based cleanup of open tasktool rows without bulk-closing or mutating before approval.
    6	
    7	**Architecture:** Implement this as a new canonical skill under top-level `skills/tasktool-janitor/SKILL.md`, backed by string-level lifecycle documentation tests. The skill composes with `tasklist-discipline` and `dispatching-parallel-agents`; it does not add tasktool commands or change tracker behavior.
    8	
    9	**Tech Stack:** Markdown skill content, Python pytest string assertions, optional shell skill-trigger fixture. No new dependencies.
   10	
   11	---
   12	
   13	## Scheduling Contract
   14	
   15	`X31` is a cross-cutting implementation item. It is not nested under a phase, has no `depends_on`, `parallel_group`, `coordination_group`, integration-surface metadata, or reservations. Treat implementation as one isolated work item:
   16	
   17	```bash
   18	tasktool start X31
   19	```
   20	
   21	Use the worktree path printed by `tasktool start`. Do not edit implementation files from the authoritative checkout.
   22	
   23	## File Structure
   24	
   25	- **Create:** `skills/tasktool-janitor/SKILL.md`
   26	  - Owns the reusable cleanup workflow: read-only intake, row batching, worker dossier contract, coordinator reconciliation, approval-before-mutation, tasktool-only small-batch mutation, and audit trail guidance.
   27	- **Modify:** `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`
   28	  - Adds guardrail tests for the new skill file and its load-bearing instructions.
   29	- **Optional create:** `tests/skill-triggering/prompts/tasktool-janitor.txt`
   30	  - Adds a natural-language prompt for manual trigger testing.
   31	- **Optional modify:** `tests/skill-triggering/run-all.sh`
   32	  - Include `tasktool-janitor` only if the implementation team wants this prompt in the slow Claude-based trigger suite.
   33	
   34	Do not hand-edit `plugins/superstar/skills/**`. The generated Codex/Claude plugin mirrors are refreshed by publish/sync tooling after the source skill is accepted.
   35	
   36	## Verification Commands
   37	
   38	Focused verification:
   39	
   40	```bash
   41	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
   42	```
   43	
   44	Full relevant verification:
   45	
   46	```bash
   47	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
   48	tasktool validate
   49	git diff --check
   50	```
   51	
   52	Optional manual validation after implementation:
   53	
   54	```bash
   55	cd /home/simon/Dev/sigreer/multistore
   56	tasktool list --open
   57	git status --short
   58	```
   59	
   60	Then dry-run the skill mentally or in a supervised session against `X*` rows only, producing dossiers without running mutating commands.
   61	
   62	---
   63	
   64	### Task 0: Start X31 and capture the baseline
   65	
   66	**Files:** none
   67	
   68	- [ ] **Step 1: Start the cross-cutting work item**
   69	
   70	Run from `/home/simon/Dev/sigreer/skills/superstar`:
   71	
   72	```bash
   73	tasktool brief X31
   74	tasktool start X31
   75	```
   76	
   77	Expected: `tasktool brief X31` prints the existing X31 row, and `tasktool start` prints a worktree path under `.worktrees/` and records the worktree on the X31 row.
   78	
   79	- [ ] **Step 2: Enter the worktree**
   80	
   81	Run:
   82	
   83	```bash
   84	cd <path-printed-by-tasktool-start>
   85	```
   86	
   87	Expected: the shell is inside the X31 implementation worktree.
   88	
   89	- [ ] **Step 3: Confirm the canonical skill/test paths**
   90	
   91	Run:
   92	
   93	```bash
   94	sed -n '1,20p' tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
   95	find skills -maxdepth 2 -name SKILL.md | sort
   96	```
   97	
   98	Expected: `skill_text()` reads from top-level `skills/<name>/SKILL.md`, and no `skills/tasktool-janitor/SKILL.md` exists yet.
   99	
  100	- [ ] **Step 4: Run the baseline focused test**
  101	
  102	Run:
  103	
  104	```bash
  105	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
  106	```
  107	
  108	Expected: passes before X31 edits. If it fails, stop and report the pre-existing failure before changing files.
  109	
  110	---
  111	
  112	### Task 1: Add failing guardrail tests for `tasktool-janitor`
  113	
  114	**Files:**
  115	- Modify: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`
  116	
  117	- [ ] **Step 1: Add the failing tests**
  118	
  119	Append these tests near the other skill-content assertions:
  120	
  121	```python
  122	def test_tasktool_janitor_skill_exists_with_trigger_frontmatter() -> None:
  123	    text = skill_text("tasktool-janitor")
  124	
  125	    assert "name: tasktool-janitor" in text
  126	    assert "description: Use when cleaning up open tasktool rows" in text
  127	    assert "cross-cutting X items" in text
  128	    assert "large sets of heterogeneous tasklist cleanup candidates" in text
  129	
  130	
  131	def test_tasktool_janitor_starts_read_only_and_batches_work() -> None:
  132	    text = skill_text("tasktool-janitor")
  133	
  134	    assert "tasktool list --open" in text
  135	    assert "git status --short" in text
  136	    assert "read-only" in text.lower()
  137	    assert "more than six candidate rows" in text
  138	    assert "4-6 rows" in text
  139	    assert "dispatching-parallel-agents" in text
  140	    assert "must not review 20+ heterogeneous rows alone" in text
  141	
  142	
  143	def test_tasktool_janitor_forbids_worker_mutations() -> None:
  144	    text = skill_text("tasktool-janitor")
  145	
  146	    assert "Workers must not run" in text
  147	    assert "tasktool close <id>" in text
  148	    assert "tasktool cancel <id> --reason" in text
  149	    assert "tasktool set <id>" in text
  150	    assert "tasktool note <id>" in text
  151	    assert "tasktool ref <id>" in text
  152	    assert "must not edit files" in text
  153	
  154	
  155	def test_tasktool_janitor_defines_dossier_contract() -> None:
  156	    text = skill_text("tasktool-janitor")
  157	
  158	    for field in [
  159	        "Recommended action",
  160	        "Evidence checked",
  161	        "Rationale",
  162	        "Proposed command",
  163	        "Confidence / risk notes",
  164	    ]:
  165	        assert field in text
  166	
  167	    for action in ["keep", "close", "cancel", "promote", "uncertain"]:
  168	        assert action in text
  169	
  170	    assert "Age alone is never evidence" in text
  171	    assert "promote" in text and "normal Superstar spec/plan workflow" in text
  172	
  173	
  174	def test_tasktool_janitor_requires_approval_and_safe_mutation_batches() -> None:
  175	    text = skill_text("tasktool-janitor")
  176	
  177	    assert "explicit user approval" in text
  178	    assert "tasktool close XNN" in text
  179	    assert "tasktool cancel XNN --reason" in text
  180	    assert "landed-branch gate" in text
  181	    assert "docs/tasklist.json" in text
  182	    assert "close` auto-commits" in text
  183	    assert "has no equivalent opt-out flag" in text
  184	    assert "stages tracker/archive changes instead" in text
  185	    assert "small batches" in text
  186	    assert "tasktool validate" in text
  187	    assert "re-check open rows" in text
  188	    assert "Stop and report if tasktool refuses" in text
  189	
  190	
  191	def test_tasktool_janitor_requires_audit_trail_for_substantial_cleanup() -> None:
  192	    text = skill_text("tasktool-janitor")
  193	
  194	    assert "durable audit artifact" in text
  195	    assert "unless the user explicitly requests chat-only" in text
  196	    assert "docs/handoffs/YYYY-MM-DD-tasktool-janitor-audit.md" in text
  197	    assert "archived-task path" in text
  198	```
  199	
  200	- [ ] **Step 2: Run the focused test and confirm failure**
  201	
  202	Run:
  203	
  204	```bash
  205	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
  206	```
  207	
  208	Expected: fails because `skills/tasktool-janitor/SKILL.md` does not exist.
  209	
  210	Do not commit this failing state. Task 2 creates the skill and makes the tests pass.
  211	
  212	---
  213	
  214	### Task 2: Create `skills/tasktool-janitor/SKILL.md`
  215	
  216	**Files:**
  217	- Create: `skills/tasktool-janitor/SKILL.md`
  218	
  219	- [ ] **Step 1: Create the skill directory and file**
  220	
  221	Create `skills/tasktool-janitor/SKILL.md` with this content:
  222	
  223	```markdown
  224	---
  225	name: tasktool-janitor
  226	description: Use when cleaning up open tasktool rows, especially cross-cutting X items, stale phase/slice entries, or large sets of heterogeneous tasklist cleanup candidates
  227	---
  228	
  229	# Tasktool Janitor
  230	
  231	Clean up open tasktool rows by auditing evidence first, reconciling recommendations conservatively, asking for approval, and applying only small approved `tasktool` mutation batches.
  232	
  233	## Required Setup
  234	
  235	Use `superstar:tasklist-discipline` first. For large or heterogeneous cleanup sets, use `superstar:dispatching-parallel-agents` to split independent row audits.
  236	
  237	Start read-only:
  238	
  239	```bash
  240	tasktool list --open
  241	git status --short
  242	```
  243	
  244	When the user asks for crosscuts, isolate `X*` rows from the open list. Dirty work does not block read-only audit, but before mutation check whether `docs/tasklist.json` itself is dirty or staged with unrelated edits.
  245	
  246	`tasktool close` auto-commits scoped tracker/archive changes by default, so unrelated tracker dirt can be folded into the lifecycle commit; use `tasktool close --no-commit` only when the operator intentionally wants a staged lifecycle package.
  247	
  248	The cancel command stages tracker/archive changes instead. It has no equivalent opt-out flag, so the operator must commit or otherwise handle the staged lifecycle package deliberately. Resolve or stash unrelated tracker dirt before either command.
  249	
  250	## Batching
  251	
  252	Delegate when the cleanup set has more than six candidate rows or spans more than one coherent theme.
  253	
  254	- Use one worker per theme or per bounded batch of 4-6 rows.
  255	- Workers may inspect `tasktool show`, specs, plans, handoffs, reviewer chains, archived task notes, source files, docs, recent commits, and targeted `rg` results.
  256	- Workers must return dossiers, not prose-only summaries.
  257	- A single coordinator must not review 20+ heterogeneous rows alone.
  258	- Workers must not edit files.
  259	
  260	Workers must not run:
  261	
  262	```bash
  263	tasktool close <id>
  264	tasktool cancel <id> --reason "..."
  265	tasktool set <id> ...
  266	tasktool note <id> ...
  267	tasktool ref <id> ...
  268	```
  269	
  270	## Dossier Contract
  271	
  272	Every row gets this dossier:
  273	
  274	```markdown
  275	## <id> — <title>
  276	
  277	**Recommended action:** keep | close | cancel | promote | uncertain
  278	**Evidence checked:** <commands/files/refs reviewed>
  279	**Rationale:** <why the evidence supports the recommendation>
  280	**Proposed command:** <exact tasktool command, or "none">
  281	**Confidence / risk notes:** <known gaps, ambiguity, or blast radius>
  282	```
  283	
  284	Action meanings:
  285	
  286	| Action | Meaning |
  287	|--------|---------|
  288	| `keep` | The row is still valid and should remain open. |
  289	| `close` | The work is truthfully done and evidence supports `tasktool close <id>`. |
  290	| `cancel` | The work is abandoned, superseded, invalid, intentionally not shipping, or no longer desired. |
  291	| `promote` | The row should feed the normal Superstar spec/plan workflow before it can be resolved. |
  292	| `uncertain` | Evidence is incomplete or conflicting; do not mutate. |
  293	
  294	Age alone is never evidence for `close` or `cancel`.
  295	
  296	## Reconciliation
  297	
  298	Merge worker dossiers into grouped recommendations. Re-check every `close` and `cancel` recommendation yourself against the cited evidence. Downgrade weak or incomplete evidence to `uncertain`.
  299	
  300	Present grouped recommendations to the user before mutation. Include exact proposed commands for rows you recommend changing, and ask for explicit user approval.
  301	
  302	Record `promote` recommendations in the audit artifact and route them into the normal Superstar spec/plan workflow if the user wants to pursue them. Do not turn `promote` into ad-hoc implementation during cleanup.
  303	
  304	## Mutation Rules
  305	
  306	After approval, use only `tasktool` commands:
  307	
  308	```bash
  309	tasktool close XNN
  310	tasktool cancel XNN --reason "..."
  311	```
  312	
  313	- `tasktool close XNN` is only for truthfully done work.
  314	- `tasktool cancel XNN --reason "..."` is for abandoned, superseded, invalid, or intentionally unshipped work.
  315	- `tasktool cancel` does not apply to task rows; non-cross lifecycle details stay with `tasklist-discipline`.
  316	- `tasktool close XNN` on a cross row still passes the landed-branch gate. If a row records an unlanded worktree branch, close is refused; do not improvise flags. Consult `tasklist-discipline` for any sanctioned override and required reason.
  317	- Before each mutation batch, confirm `docs/tasklist.json` is not dirty or staged with unrelated edits.
  318	- `close` auto-commits scoped tracker/archive changes by default and supports `--no-commit` for an intentional staged lifecycle package.
  319	- The cancel command stages tracker/archive changes instead. It has no equivalent opt-out flag, so the operator must commit or otherwise handle that staged package deliberately.
  320	- Apply changes in small batches.
  321	- After each batch, run `tasktool validate` and re-check open rows with `tasktool list --open`.
  322	- Preserve unrelated dirty/staged work.
  323	- Stop and report if tasktool refuses a mutation. Do not hand-edit `docs/tasklist.json`.
  324	
  325	## Audit Trail
  326	
  327	For substantial cleanup, leave or recommend a durable audit artifact unless the user explicitly requests chat-only output.
  328	
  329	Default path:
  330	
  331	```text
  332	docs/handoffs/YYYY-MM-DD-tasktool-janitor-audit.md
  333	```
  334	
  335	Record original row id/title, action, evidence, command run, final state, archived-task path when applicable, and unresolved uncertainties.
  336	```
  337	
  338	- [ ] **Step 2: Run the focused tests**
  339	
  340	Run:
  341	
  342	```bash
  343	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
  344	```
  345	
  346	Expected: passes.
  347	
  348	- [ ] **Step 3: Commit tests plus skill**
  349	
  350	Run:
  351	
  352	```bash
  353	git add tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py skills/tasktool-janitor/SKILL.md
  354	git commit -m "X31: add tasktool janitor skill"
  355	```
  356	
  357	Expected: commit succeeds.
  358	
  359	---
  360	
  361	### Task 3: Add optional trigger fixture without making the suite slower by default
  362	
  363	**Files:**
  364	- Create: `tests/skill-triggering/prompts/tasktool-janitor.txt`
  365	- Optional modify: `tests/skill-triggering/run-all.sh`
  366	
  367	- [ ] **Step 1: Add a natural prompt fixture**
  368	
  369	Create `tests/skill-triggering/prompts/tasktool-janitor.txt`:
  370	
  371	```text
  372	Please clean up the tasktool crosscuts. Start by auditing the open X rows and propose what should stay open, close, cancel, promote, or remain uncertain. Do not mutate anything until I approve the recommendations.
  373	```
  374	
  375	- [ ] **Step 2: Decide whether to include it in `run-all.sh`**
  376	
  377	Default: do not add it to `SKILLS` in `tests/skill-triggering/run-all.sh`, because that suite shells out to Claude and is slower/flakier than the string-level guardrails. If the implementer chooses to include it, add `"tasktool-janitor"` to the `SKILLS` array and document the increased suite cost in the commit message.
  378	
  379	- [ ] **Step 3: Commit the fixture**
  380	
  381	Run:
  382	
  383	```bash
  384	git add tests/skill-triggering/prompts/tasktool-janitor.txt
  385	git commit -m "X31: add tasktool janitor trigger prompt"
  386	```
  387	
  388	Expected: commit succeeds. If no trigger fixture is added, skip this task and record the reason in the implementation summary.
  389	
  390	---
  391	
  392	### Task 4: Verify source-only scope and generated mirror boundary
  393	
  394	**Files:** none unless verification finds accidental mirror edits
  395	
  396	- [ ] **Step 1: Check for accidental generated mirror edits**
  397	
  398	Run:
  399	
  400	```bash
  401	git status --short
  402	git diff --name-only -- plugins/superstar/skills
  403	```
  404	
  405	Expected: no `plugins/superstar/skills/**` changes. If generated mirror files changed, inspect why. Revert only accidental mirror edits made by this implementation; preserve unrelated user changes.
  406	
  407	- [ ] **Step 2: Run focused verification**
  408	
  409	Run:
  410	
  411	```bash
  412	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
  413	```
  414	
  415	Expected: all tests pass.
  416	
  417	- [ ] **Step 3: Run tasktool validation**
  418	
  419	Run:
  420	
  421	```bash
  422	tasktool validate
  423	```
  424	
  425	Expected: exits 0. Existing warnings unrelated to X31 may remain; record them exactly in the implementation summary.
  426	
  427	- [ ] **Step 4: Run diff whitespace validation**
  428	
  429	Run:
  430	
  431	```bash
  432	git diff --check
  433	```
  434	
  435	Expected: no output and exit 0.
  436	
  437	---
  438	
  439	### Task 5: External post-slice review and closeout
  440	
  441	**Files:** reviewer artifacts and tasktool lifecycle files only
  442	
  443	- [ ] **Step 1: Confirm the implementation branch is ready for review**
  444	
  445	Run:
  446	
  447	```bash
  448	git status --short
  449	```
  450	
  451	Expected: only committed X31 implementation changes, or a clean worktree. If unrelated dirty files are present, stop and resolve scope before review.
  452	
  453	- [ ] **Step 2: Run post-slice review**
  454	
  455	Run:
  456	
  457	```bash
  458	external-reviewer review \
  459	  --kind post-slice \
  460	  --file docs/plans/2026-06-21-X31-tasktool-janitor-skill.md \
  461	  --work-id X31 \
  462	  --context docs/specs/2026-06-21-X31-tasktool-janitor-skill-design.md \
  463	  --emit json
  464	```
  465	
  466	Expected: `merged_verdict` is `ready` or `ready with small edits`. If the verdict is `revise`, dispatch a fix subagent, write the required reviewer resolution file, and resubmit.
  467	
  468	- [ ] **Step 3: Ask the version-bump question before final shipping commit/publish**
  469	
  470	Because this changes user-shipping `skills/` content, ask:
  471	
  472	```text
  473	Bump the version before/after this commit? (current: <current> -> patch <next-patch> / minor <next-minor> / no bump)
  474	```
  475	
  476	Do not silently bump. If the user chooses a bump, run `./scripts/bump-version.sh <new-version>` and commit the bump separately as `Bump Superstar to <new-version>`.
  477	
  478	If the bump commit is blocked by shim or hook version drift, run:
  479	
  480	```bash
  481	bash tools/tasktool/install.sh --hook --force
  482	```
  483	
  484	Then rerun the commit.
  485	
  486	- [ ] **Step 4: Merge, close, and prune through normal tasktool lifecycle**
  487	
  488	Follow `subagent-driven-development` closeout. Merge the X31 worktree branch back to `main` using `finishing-a-development-branch` Option 1 mechanics before closing; `--allow-unlanded` is not the sanctioned path for normal X31 completion.
  489	
  490	```bash
  491	git checkout main
  492	git merge <x31-worktree-branch>
  493	tasktool close X31
  494	tasktool worktree prune X31
  495	```
  496	
  497	Expected: X31 closes only after the implementation is landed and reviewed. If `tasktool close` refuses, stop and report the refusal.
  498	
  499	## Acceptance
  500	
  501	- `skills/tasktool-janitor/SKILL.md` exists and passes the guardrail tests.
  502	- Worker mutation bans, dossier schema, approval-before-mutation, tracker close auto-commit safeguards, cancel staged-package safeguards, landed-gate warning, and durable audit guidance are present in the skill.
  503	- Focused docs-lifecycle pytest passes.
  504	- `tasktool validate` exits 0, with only pre-existing warnings if any.
  505	- No generated plugin mirror files are hand-edited.
  506	- Post-slice review passes before X31 closeout.

## Context Previews

### docs/specs/2026-06-21-X31-tasktool-janitor-skill-design.md

    1	# X31 — Tasktool Janitor Skill Design
    2	
    3	**Status:** spec
    4	**Work row:** `X31` — Tasktool janitor cleanup skill
    5	**Canonical source:** top-level `skills/`; generated plugin mirrors are implementation/publish outputs, not hand-edited sources.
    6	
    7	## Problem
    8	
    9	Superstar-managed repos accumulate open cross-cutting rows as phases finish, plans change, and follow-up work gets superseded. Cleaning those rows is deceptively risky: a stale title can look obsolete even when source, docs, or reviewer chains prove the work is still live; a row can be old without being abandoned; and a single coordinator reviewing twenty unrelated rows in one context is likely to flatten evidence into guesses.
   10	
   11	The repo already has `tasklist-discipline` for tasktool lifecycle rules and `dispatching-parallel-agents` for independent investigations. What is missing is a reusable on-demand cleanup skill that teaches agents how to run tracker janitorial work: start read-only, split row audits into bounded worker assignments, require a per-row evidence dossier, reconcile recommendations conservatively, ask the user before mutation, and only then apply approved `tasktool` commands in small validated batches.
   12	
   13	The motivating validation repo is `/home/simon/Dev/sigreer/multistore`, where many open `X*` cross-cutting rows need careful cleanup. The new skill must remain generic across Superstar/tasktool repos and must not hard-code multistore phases, paths, or row IDs.
   14	
   15	## Goals
   16	
   17	- Add a new on-demand Superstar skill named `tasktool-janitor`.
   18	- Trigger for prompts such as "clean up the tasktool crosscuts using janitor skill", "audit stale X rows", or "review open cross-cutting/phase/slice cleanup candidates".
   19	- Specialize tracker cleanup methodology without duplicating all of `tasklist-discipline`.
   20	- Make evidence dossiers the mandatory output unit for each reviewed row.
   21	- Coordinate worker agents for heterogeneous or large row sets instead of letting one context bulk-review everything.
   22	- Prevent mutation until the coordinator has presented grouped recommendations and received user approval.
   23	- Preserve a durable audit trail for substantial cleanup unless the user explicitly requests chat-only output.
   24	
   25	## Non-Goals
   26	
   27	- No new `tasktool` subcommands or data model changes.
   28	- No automatic bulk close/cancel behavior.
   29	- No project-specific multistore logic.
   30	- No replacement for `tasklist-discipline`; the janitor skill composes with it for lifecycle semantics.
   31	- No implementation work in target repos while auditing cleanup candidates. If a row needs real code or docs work, the recommendation is `promote` or `keep`, not an inline fix.
   32	
   33	## Skill Name and Placement
   34	
   35	Create:
   36	
   37	- `skills/tasktool-janitor/SKILL.md`
   38	
   39	Do not create a separate CLI tool. The first implementation is process guidance only. Publish/sync scripts already copy top-level `skills/` into `plugins/superstar/skills/`, so the generated mirror should be refreshed by normal release tooling later rather than hand-edited in this slice.
   40	
   41	The frontmatter should use trigger-only wording:
   42	
   43	```yaml
   44	---
   45	name: tasktool-janitor
   46	description: Use when cleaning up open tasktool rows, especially cross-cutting X items, stale phase/slice entries, or large sets of heterogeneous tasklist cleanup candidates
   47	---
   48	```
   49	
   50	## Required Workflow
   51	
   52	### 1. Read-Only Intake
   53	
   54	The skill must start by loading `superstar:tasklist-discipline` and then running:
   55	
   56	```bash
   57	tasktool list --open
   58	git status --short
   59	```
   60	
   61	When the user asks for crosscuts, the coordinator isolates `X*` rows from the open list before dispatch. The skill may inspect `tasktool show <id>`, specs, plans, handoffs, reviewer chains, archived task notes, source files, docs, recent commits, and targeted `rg` results, but it must remain read-only during classification.
   62	
   63	If `git status --short` shows unrelated dirty or staged work, the coordinator records that fact in the audit context and avoids committing or reverting it. Dirty work does not automatically block read-only audit. Before mutation, however, the coordinator must specifically check whether `docs/tasklist.json` is itself dirty or staged with unrelated edits.
   64	
   65	`tasktool close` auto-commits scoped tracker/archive changes by default, so pre-existing tracker dirt can be folded into that lifecycle commit; use `tasktool close --no-commit` only when the operator intentionally wants the tracker to remain staged.
   66	
   67	The cancel command stages tracker/archive changes instead. That command has no equivalent opt-out flag, so the operator must handle the staged lifecycle package deliberately. Resolve or stash unrelated tracker dirt before either command.
   68	
   69	### 2. Batching and Delegation
   70	
   71	The skill must require coordinator-led batching when cleanup involves more than six candidate rows or spans more than one coherent theme:
   72	
   73	- Use one worker per coherent theme or per bounded batch of 4-6 rows.
   74	- Use `dispatching-parallel-agents` when batches are independent.
   75	- Workers may inspect evidence but must not edit files or run mutating tasktool commands.
   76	- Workers must return dossiers, not prose-only summaries.
   77	- A single coordinator must not review 20+ heterogeneous rows alone.
   78	
   79	Acceptable worker evidence sources include:
   80	
   81	- `tasktool show <id>`
   82	- `tasktool list --open`
   83	- `docs/specs/`, `docs/plans/`, `docs/handoffs/`
   84	- `docs/reviewer/`
   85	- `docs/archived-tasks/`
   86	- relevant source/docs paths named by the row
   87	- targeted `rg` searches
   88	- recent commits where needed
   89	
   90	Workers must not run:
   91	
   92	```bash
   93	tasktool close <id>
   94	tasktool cancel <id> --reason "..."
   95	tasktool set <id> ...
   96	tasktool note <id> ...
   97	tasktool ref <id> ...
   98	```
   99	
  100	### 3. Dossier Contract
  101	
  102	Every audited row must produce a dossier with this shape:
  103	
  104	```markdown
  105	## <id> — <title>
  106	
  107	**Recommended action:** keep | close | cancel | promote | uncertain
  108	**Evidence checked:** <commands/files/refs reviewed>
  109	**Rationale:** <why the evidence supports the recommendation>
  110	**Proposed command:** <exact tasktool command, or "none">
  111	**Confidence / risk notes:** <known gaps, ambiguity, or blast radius>
  112	```
  113	
  114	Action meanings:
  115	
  116	| Action | Meaning |
  117	|--------|---------|
  118	| `keep` | The row is still valid and should remain open. |
  119	| `close` | The work is truthfully done and evidence supports `tasktool close <id>`. |
  120	| `cancel` | The work is abandoned, superseded, invalid, intentionally not shipping, or no longer desired; use `tasktool cancel <id> --reason "..."`. |
  121	| `promote` | The row should become or feed a proper phase/slice/spec/plan before it can be resolved. |
  122	| `uncertain` | Evidence is incomplete or conflicting; do not mutate. |
  123	
  124	Age alone is never evidence for `close` or `cancel`.
  125	
  126	`promote` does not run a tasktool mutation during janitor cleanup. The coordinator records the promotion recommendation in the audit artifact and routes it into the normal Superstar spec/plan workflow if the user wants to pursue it.
  127	
  128	### 4. Coordinator Reconciliation
  129	
  130	The coordinator merges worker dossiers into grouped recommendations. Before presenting anything to the user, the coordinator must re-check every `close` and `cancel` recommendation against the cited evidence. Weak recommendations are downgraded to `uncertain`.
  131	
  132	The user-facing recommendation must group rows by action and include the exact commands proposed for approved mutation. The coordinator must ask for approval before running any mutating command.
  133	
  134	### 5. Mutation Discipline
  135	
  136	After approval, the coordinator applies changes only with tasktool commands:
  137	
  138	```bash
  139	tasktool close XNN
  140	tasktool cancel XNN --reason "..."
  141	```
  142	
  143	The skill must state:
  144	
  145	- `tasktool close XNN` is only for truthfully done work.
  146	- `tasktool cancel XNN --reason "..."` is for abandoned, superseded, invalid, or intentionally unshipped work.
  147	- `tasktool cancel` does not apply to task rows; non-cross lifecycle details remain owned by `tasklist-discipline`.
  148	- `tasktool close XNN` on a cross row still passes tasktool's landed-branch gate. If the row records an unlanded worktree branch, close is refused; do not improvise flags, and consult `tasklist-discipline` for any sanctioned override and required reason.
  149	- Before any mutation, confirm `docs/tasklist.json` is not itself dirty or staged with unrelated edits. `close` auto-commits scoped tracker/archive changes by default and supports `--no-commit` for an intentional staged lifecycle package.
  150	- The cancel command stages tracker/archive changes instead, with no equivalent opt-out flag, and requires the operator to commit or otherwise handle that staged package deliberately.
  151	- Apply changes in small batches.
  152	- Run `tasktool validate` and re-check open rows after each batch.
  153	- Preserve unrelated dirty/staged work.
  154	- Stop and report if tasktool refuses a mutation instead of hand-editing `docs/tasklist.json`.
  155	
  156	### 6. Audit Trail
  157	
  158	For substantial cleanup, the skill must leave or recommend a durable audit artifact unless the user explicitly requests chat-only output. The artifact should live under `docs/handoffs/` or another existing repo docs area chosen by local convention and record:
  159	
  160	- original row id and title
  161	- action recommended
  162	- evidence checked
  163	- command approved and run, if any
  164	- final state after mutation, including the archived-task path when closing or cancelling an `X*` row archives it
  165	- unresolved uncertainties
  166	
  167	The skill should avoid forcing a particular filename because cleanup may happen outside a formal spec/plan slice. A recommended default is:
  168	
  169	```text
  170	docs/handoffs/YYYY-MM-DD-tasktool-janitor-audit.md
  171	```
  172	
  173	## Composition With Existing Skills
  174	
  175	- `tasklist-discipline`: required for lifecycle meanings, sanctioned commands, cancellation semantics, and artifact boundaries.
  176	- `dispatching-parallel-agents`: required when the candidate set splits into independent row batches.
  177	- `using-git-worktrees`: not required for pure read-only administrative audit; use it only if the cleanup turns into implementation work or active slice lifecycle mutations beyond approved administrative cleanup.
  178	- `subagent-driven-development`: not required for the janitor audit itself, because this is not plan execution. If a dossier recommends `promote`, future implementation should go through the normal spec/plan/implementation loop.
  179	
  180	## Acceptance Criteria
  181	
  182	- `skills/tasktool-janitor/SKILL.md` exists with trigger-focused frontmatter.
  183	- The skill requires read-only intake with `tasktool list --open` and `git status --short`.
  184	- The skill requires batching or worker delegation for large heterogeneous cleanup sets.
  185	- The skill forbids worker agents from mutating tasktool state or editing files.
  186	- The skill defines the dossier schema and the five allowed recommendations: `keep`, `close`, `cancel`, `promote`, `uncertain`.
  187	- The skill requires coordinator re-check of every `close` and `cancel` recommendation before user presentation.
  188	- The skill requires explicit user approval before any `tasktool close` or `tasktool cancel`.
  189	- The skill requires small mutation batches followed by `tasktool validate` and open-row re-check.
  190	- The skill requires a durable audit artifact for substantial cleanup unless the user asks for chat-only.
  191	- Regression tests or trigger tests cover the new skill file and key guardrails.
  192	
  193	## Test Strategy
  194	
  195	Add focused string-level tests under `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` because this repo already uses that file to pin load-bearing skill prose. The tests should assert:
  196	
  197	- the skill file exists and has the expected frontmatter trigger;
  198	- tests pin `name: tasktool-janitor` and the description phrase `cleaning up open tasktool rows`;
  199	- intake commands are present;
  200	- worker mutation bans are present;

[truncated: 16 additional lines]

<!-- superstar-prompt:end -->