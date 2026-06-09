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
post-phase

Review mode:
Post-phase review. Treat this as a closeout gate for a whole
phase. Compare the implementation, archive/TASKLIST updates, and verification
evidence against the phase spec/plan. Prioritize: unresolved acceptance
criteria, stale docs, missing archive notes, cross-cutting tracker drift,
deferred gates without justification, and regressions outside the phase scope.

Target document:
docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md

Additional context files:
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
  201	
  202	### S3 — Combined spec+plan gate for small slices
  203	
  204	**S3.a Eligibility (skill text, `brainstorming` + `writing-plans`).** The
  205	combined gate is for slice-level specs only — phase-level specs (like this
  206	one) always receive a standalone spec review. A slice may use the combined
  207	gate when ALL hold:
  208	
  209	- Single-surface change (one tool/skill/app area; no new subsystem).
  210	- No cross-repo or cross-plugin impact.
  211	- Spec fits the existing phase direction (no new product decisions).
  212	
  213	When eligible, brainstorming still writes the spec but skips the standalone
  214	spec review; writing-plans proceeds immediately, and the plan review carries
  215	the spec-coverage burden. Ineligible or uncertain → today's two-gate flow.
  216	
  217	**S3.b `--combined-gate <spec-path>` flag.** `external-reviewer review --kind
  218	plan --combined-gate <path/to/spec.md>` takes the spec path as its explicit
  219	argument: the file must exist (exit 2 otherwise) and is automatically added to
  220	the context set, so the spec attachment is verifiable rather than inferred
  221	from `--context` (which also carries tracker files). The flag appends to the
  222	plan MODE_GUIDANCE: "This plan's spec did not receive a standalone review.
  223	Also review the attached spec for completeness, internal consistency, and
  224	groundedness; tag spec-level findings distinctly." It is valid only with
  225	`--kind plan` (exit 2 otherwise). `chain.json` records `combined_gate: true`
  226	and the spec path per round so `stats` can segment combined vs standalone
  227	chains.
  228	
  229	**S3.c Workflow-step compatibility.** `tasktool set <id> --workflow-step plan`
  230	directly from spec-written state must not be blocked by any step-ordering
  231	validation; verify and adjust tasktool only if it enforces spec-review-passed
  232	as a precondition (current behaviour check is an S3 task, expected no-op).
  233	
  234	## Acceptance criteria (phase)
  235	
  236	1. Omitting `--review-depth` yields `standard` for spec/plan and `thorough`
  237	   for post-slice/post-phase, with `depth_resolved` recorded in `chain.json`;
  238	   explicit flags override.
  239	2. A spec/plan chain whose prior round was `revise` refuses round N+1 without
  240	   `r{N}-resolution.md` (exit 3), waivable with `--allow-missing-resolution`.
  241	3. With `AGENT_REVIEWER_MODEL_LIGHT`/`_STRONG` set, each reviewer process
  242	   receives the model mapped by the S1.d invocation matrix (covering
  243	   first-round primary, follow-up primary, post-slice/post-phase primary,
  244	   first-round sweep, and final-ready sweep) and `chain.json` records it;
  245	   with neither set, invocation is byte-identical to today.
  246	4. `external-reviewer preflight` catches each check-class in a fixture
  247	   document (placeholder, dangling path, missing section, oversized context)
  248	   and passes a known-good document; `review` auto-runs it on round 1 and
  249	   `--no-preflight` skips.
  250	5. `--combined-gate <spec-path>` injects the spec-coverage guidance, adds the
  251	   spec to context, exits 2 when the path is missing or the kind is not
  252	   `plan`, and stamps `combined_gate` plus the spec path in `chain.json`.
  253	6. `stats --since 2026-06-07 --json` returns only rounds started on/after the
  254	   date (UTC), reports the excluded-legacy count, and emits the per-slice
  255	   section: passing-post-slice work-id denominator, all-rounds numerator,
  256	   rounds-per-slice ratio, the uncorrelated-chain list, and the
  257	   `per_slice_complete` flag. Test fixture: a slice with spec, plan, and
  258	   post-slice chains sharing a `work_id` — the numerator includes all three
  259	   kinds' rounds; a variant with a missing spec-chain `work_id` sets
  260	   `per_slice_complete: false` and lists the chain as uncorrelated.
  261	7. All affected skill texts (external-review, brainstorming, writing-plans,
  262	   subagent-driven-development) reflect the new defaults, trimming rule,
  263	   `--work-id` on slice-level spec/plan reviews, preflight step, and
  264	   combined-gate eligibility.
  265	8. Existing pytest suite in `skills/external-review/tests/` passes; new
  266	   behaviours covered by unit tests added there.
  267	
  268	## Measurement plan
  269	
  270	- Baseline: the stats table in **Problem** (multistore, captured 2026-06-06).
  271	- Trial: after S1 ships (and again after S2/S3), run normal slice work in
  272	  multistore for a representative window (≥10 slices), then compare
  273	  `external-reviewer stats --since <ship-date>` against baseline.
  274	- Success: rounds/slice ≤ 4.5 as computed by the S1.e per-slice metric
  275	  (passing-post-slice work-ids as denominator); spec+plan reviewer invocations
  276	  (including sweeps) roughly halved; post-slice revise rate not worse than
  277	  baseline 47% (the post-slice gate must not weaken).
  278	- Segment combined-gate chains via the `combined_gate` stamp before drawing
  279	  conclusions.
  280	
  281	## Risks
  282	
  283	- **Quality regression on spec/plan gates** from losing sweeps and using a
  284	  lighter model. Mitigation: post-slice gate unchanged at `thorough` with the
  285	  strong model; escalation is one explicit flag away; measurement plan watches
  286	  post-slice revise rate as the canary (defects slipping past cheaper early
  287	  gates would surface there).
  288	- **Preflight false positives** (path heuristic flagging prose). Mitigation:
  289	  the S2.a exemption rules (fenced blocks, placeholder/glob characters,
  290	  `docs/reviewer/` paths), the link-vs-backtick severity split, the
  291	  `--no-preflight` escape, and validation of the heuristic against the
  292	  existing corpus of specs/plans in this repo and multistore.
  293	- **Resolution-gate friction on spec/plan chains** mid-migration. Mitigation:
  294	  existing waiver flag; gate only fires when the prior verdict was `revise`.
  295	- **Version skew**: shims hard-fail on VERSION drift, so S1's CLI changes ship
  296	  with a version bump and `install.sh` re-run per the release process.

## Context Previews

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

[truncated: 246 additional lines]

<!-- superstar-prompt:end -->