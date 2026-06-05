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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared

Target kind:
post-phase

Review mode:
Post-phase review. Treat this as a closeout gate for a whole
phase. Compare the implementation, archive/TASKLIST updates, and verification
evidence against the phase spec/plan. Prioritize: unresolved acceptance
criteria, stale docs, missing archive notes, cross-cutting tracker drift,
deferred gates without justification, and regressions outside the phase scope.

Target document:
docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md

Additional context files:
- docs/tasklist.json
- docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md
- docs/specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md

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

### docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md

    1	# P7 — Integration-surface-aware parallel slice safety
    2	
    3	**Status:** design (spec)
    4	**Date:** 2026-06-02
    5	**Phase ID:** `P7`
    6	
    7	## 1. Problem
    8	
    9	`tasktool` decides whether slices may run in parallel from **declared feature
   10	dependencies** (`Slice.depends_on`) and the `parallel_group` tag. Those answer
   11	"does S4's feature need S3's feature first?" They do **not** answer the question
   12	that actually governs safe parallel execution: **what shared write surface does
   13	each slice mutate?**
   14	
   15	This gap produced a real failure in the `multistore` project, phase P20. Four
   16	storefront-marketing slices (`P20.S2`–`P20.S5`) each declared a dependency only
   17	on the bootstrap slice `P20.S1`, so `tasktool ready-slices`/`schedule` reported
   18	them as independently executable. They were feature-distinct (slider, promo
   19	bands, overlays, blog) but **integration-overlapping**: every one of them wrote
   20	the same centralized CMS-block machinery — block contracts, parser allowlists,
   21	Directus schema/seed files, renderer dispatch, theme CSS tails, and the homepage
   22	ordering array.
   23	
   24	The observed consequences:
   25	
   26	1. **Conflict-bomb merges.** `P20.S4`'s merge conflicted across `page-renderer.tsx`,
   27	   theme CSS, reviewer-request artifacts, `docs/tasklist.json`, Directus
   28	   bootstrap/schema/seed files, content-contract schemas/types, and parser tests.
   29	2. **Stale-base merges.** `P20.S4` was completed in a worktree that branched from
   30	   `main` *before* `P20.S2`/`P20.S3` and their cleanup landed. The worktree
   31	   snapshot was older than `main`, so the merge replayed churn that was already
   32	   integrated.
   33	3. **A real semantic collision, not just textual churn.** `P20.S3` and `P20.S4`
   34	   independently chose homepage sort slot `15`. Nothing forced the second slice
   35	   onto a free slot at planning time; the collision was discovered and resolved
   36	   at merge.
   37	4. **Merge-unsafe reviewer artifacts.** Generated reviewer-request files
   38	   add/add-conflicted despite not being behavioral code.
   39	
   40	The root cause is **dependency modeling by feature intent rather than by
   41	integration surface.** "Slider" and "promo bands" were non-dependent product
   42	slices, but they both wrote the same registry, schema, seed arrays, ordering
   43	slots, parser unions, and theme areas. The tool allowed parallel execution
   44	because the declared dependencies were technically satisfied.
   45	
   46	## 2. Goals
   47	
   48	1. **Prevention.** Let planning declare, per slice, the **integration surfaces**
   49	   it writes and the **scarce resources** it allocates. `tasktool` warns when
   50	   sibling ready/in-progress slices share a surface with no dependency or
   51	   coordination link, and *refuses* a duplicate scarce-resource allocation.
   52	2. **Recovery.** When a sibling slice has landed on the base branch since a
   53	   slice's worktree branched, surface that fact reliably and provide a
   54	   conservative "integrate current main" path before the post-slice review/merge,
   55	   plus a documented centralized-registry merge playbook.
   56	3. **Merge-safe reviewer artifacts.** Generated reviewer-request files must never
   57	   add/add-conflict between sibling worktrees.
   58	4. **Plan ↔ tracker coherence.** Declared surfaces/reservations must be reflected
   59	   in planning artifacts so the plan and the tracker cannot silently diverge.
   60	
   61	## 3. Non-goals (explicit)
   62	
   63	- **Directus-specific verifier diagnostics and stale-token handling.** These were
   64	  real `multistore` pain points (a stale `DIRECTUS_ADMIN_TOKEN` shadowing valid
   65	  admin credentials made a non-code problem look like a schema failure), but they
   66	  are project-specific. Superstar core is general-purpose and zero-dependency;
   67	  Directus tooling belongs in the `multistore` project, not here.
   68	- **Automatic merge-conflict resolution.** The tooling detects and routes; it does
   69	  not auto-merge semantic conflicts.
   70	- **Path-glob surface *inference* as the primary model.** Explicit declaration is
   71	  the source of truth. A path-glob comparison survives only as a deferred,
   72	  warning-only post-implementation *audit* (§4.G), never as the planning model.
   73	- **A "touches existing resource" reservation kind.** Reservations model scarce
   74	  *allocations* (claiming a new value). Modifying a shared existing resource is a
   75	  *surface/coordination* concern, not an allocation, so maintenance work is not
   76	  falsely blocked. A future "touches-existing" field is noted, not built here.
   77	- **`worktree sync` as an unconditional command.** Detection ships first; the
   78	  mutating sync command is gated behind strict preconditions and is the explicit
   79	  deferral candidate if scope tightens.
   80	
   81	## 4. Design
   82	
   83	### 4.A Data model (`model.py`, schema `v2 → v3`; `migrate.py`)
   84	
   85	Add to `Slice`:
   86	
   87	- `integration_surfaces: list[str]` — conventional surface tags naming shared
   88	  write areas the slice mutates. Free-form strings, but a recommended vocabulary
   89	  is documented in `tasklist-discipline` (e.g. `cms-block-registry`,
   90	  `directus-schema`, `page-renderer-dispatch`, `theme-tail-css`,
   91	  `content-contract-types`, `reviewer-artifacts`). Default `[]`.
   92	- `reservations: list[Reservation]` where
   93	  `Reservation = {resource: str, value: str, scope: "phase" | "project", note: str | None}`.
   94	  A reservation is a **scarce allocation claim** on a single value
   95	  (`homepage-sort:15`, `directus-collection:homepage_slider`, `route-slug:/offers`,
   96	  `block-kind:slider`, `cache-tag:home`). Default `[]`.
   97	- `coordination_group: str | None` — names a set of slices that *intentionally*
   98	  share an integration surface and agree to coordinate (serialize reviews,
   99	  designate an integration owner, run the registry merge playbook). Distinct from
  100	  `parallel_group`, which asserts independent parallelism. Default `None`.
  101	- `worktree_base_sha: str | None` — the base-branch commit the slice's worktree
  102	  was created from, recorded at `tasktool start`. Enables reliable
  103	  "a sibling landed since this slice branched" detection that survives later
  104	  rebases/merges, instead of fragile merge-base inference. Default `None`.
  105	- `landed_base_sha: str | None` — the base-branch commit at which this slice's
  106	  work landed, recorded at post-merge prune (see §4.D). This is the authoritative
  107	  "this slice shipped to base" signal that `closed` (a date) cannot provide.
  108	  Default `None`.
  109	
  110	Add to `Project`:
  111	
  112	- `reservations_ledger: list[LedgerReservation]` where
  113	  `LedgerReservation = Reservation + {owner_id: str, owner_phase_id: str, archived_date: str}`.
  114	  Project-scoped reservations are copied here when their owning phase is archived,
  115	  so project-scope uniqueness checks — and the refusal message that must name the
  116	  holder (§4.B) — survive removal of shipped phases from the active tracker. The
  117	  extra fields preserve the owning slice/phase and archive date for the refusal
  118	  message and audit trail. Default `[]`.
  119	
  120	Schema bump to `v3`. Migration is additive: missing fields default to empty/`None`
  121	and `reservations_ledger` to `[]`. Round-trip and v1/v2 compatibility tests
  122	extended.
  123	
  124	**Serialization rule (F5).** New fields follow the existing omit-when-default
  125	convention in `serialize.py`: an empty `integration_surfaces`/`reservations`,
  126	a `None` `coordination_group`/`worktree_base_sha`/`landed_base_sha`, and an empty
  127	`Project.reservations_ledger` are **omitted** on serialization, exactly as
  128	default-valued worktree/workflow keys are today. Historical rows therefore gain no
  129	churn on round-trip; a row's bytes change only once it actually declares a surface,
  130	reservation, coordination group, or base SHA.
  131	
  132	### 4.B Declaration CLI (`cli.py` + `commands.py`)
  133	
  134	```sh
  135	tasktool surface add <slice-id> <surface> [<surface>...]
  136	tasktool surface remove <slice-id> <surface>
  137	tasktool surface list [<phase-id>]
  138	
  139	tasktool reserve add <slice-id> <resource>:<value> [--scope phase|project] [--note "..."] [--force --reason "..."]
  140	tasktool reserve remove <slice-id> <resource>:<value>
  141	tasktool reserve list [<phase-id>]
  142	
  143	tasktool coordinate <slice-id> --group <name>     # set coordination_group
  144	tasktool coordinate <slice-id> --clear
  145	```
  146	
  147	- `surface`/`coordinate` are declaration-only; they never refuse.
  148	- **`reserve add` refuses** when the same `resource:value` is already held by
  149	  another **non-cancelled** slice within the relevant scope:
  150	  - `scope: phase` (default) — checks other non-cancelled slices in the same
  151	    phase. Done slices count: a done slice shipped that value to `main`, so the
  152	    slot is taken.
  153	  - `scope: project` — checks all non-cancelled slices across **active** phases
  154	    *and* `Project.reservations_ledger`.
  155	  The refusal names the holding slice (from the slice row, or from the ledger's
  156	  `owner_id`/`owner_phase_id`/`archived_date` for archived holders) and the value.
  157	- **Override (F3).** `--force` is the only way to add a colliding reservation and
  158	  **requires** `--reason "<text>"`. It mutates **only the reserving slice**: it
  159	  appends the reservation and records a timestamped note
  160	  `Reservation-override <ISO-ts>: <resource>:<value> over <holder-id> — <reason>`.
  161	  The holder slice is **not** mutated. `--force` without `--reason` is refused.
  162	  Without `--force`, a collision is a hard refusal (exit non-zero). This refusal
  163	  is the gate that would have forced `P20.S4` off slot `15` at planning time.
  164	- **Cancelled work never enters the ledger.** On `tasktool archive-phase`,
  165	  project-scoped reservations from the phase's **non-cancelled (`done`)** slices
  166	  are appended to `Project.reservations_ledger` as `LedgerReservation`s, carrying
  167	  `owner_id`/`owner_phase_id`/`archived_date`. Cancelled slices ship nothing, so
  168	  their reservations — including `--force` overrides — are released and never
  169	  laddered.
  170	- **Ledger dedupe preserves every holder (F7).** Dedup is keyed on
  171	  `resource:value:scope:owner_id`, **not** `resource:value:scope`. Re-archiving the
  172	  same phase is idempotent (same owner ⇒ same key), but two distinct `done` slices
  173	  that intentionally `--force`-shared a project-scoped value both survive in the
  174	  ledger, so the owner-metadata audit trail is never silently collapsed to one
  175	  holder. A project-scope `reserve add` collision check that matches any ledger
  176	  entry on `resource:value:scope` (regardless of owner) still refuses — multiple
  177	  recorded holders strengthen, not weaken, the refusal message.
  178	
  179	### 4.C Scheduling overlap detection (`commands.py`)
  180	
  181	Augment the existing scheduling reporters; **surface overlap is a warning, not a
  182	block** (surfaces are coarse — two slices may touch the same registry in
  183	non-conflicting ways), while **reservation contention is already prevented at
  184	declaration time**.
  185	
  186	- `cmd_ready_slices` and `cmd_schedule`: for each ready/in-progress slice, compute
  187	  the set of other non-terminal slices that (a) share ≥1 integration surface,
  188	  (b) have **no** `depends_on` link in either direction, and (c) are **not** in
  189	  the same `coordination_group`. Emit a `surface_overlap` field/warning listing
  190	  the sibling(s) and shared surface(s). Slices in a shared `coordination_group`
  191	  are reported as `coordinated`, not warned.
  192	- New `tasktool surface check <phase-id>` — a dedicated read-only report:
  193	  - every unguarded surface overlap (siblings sharing a surface without a dep or
  194	    coordination link),
  195	  - every coordinated surface (shared surface within a `coordination_group`),
  196	  - reservation contention within the phase (should be empty if `reserve add`
  197	    refusal held; surfaced for audit and for `--force` overrides).
  198	  Text and `--format json`. Intended to be run during ratification and before
  199	  parallel dispatch.
  200	- `cmd_ratify --parallel-group <g>`: when adding a slice whose surfaces overlap
  201	  another slice already in that `parallel_group` with no dep/coordination link,
  202	  print a warning (does not refuse). Steers the planner toward either a
  203	  `depends_on` (serialize) or a `coordination_group` (coordinate).
  204	
  205	### 4.D Worktree integration detection (`worktree*.py`, `commands.py`)
  206	
  207	- `tasktool start` records `worktree_base_sha` = the base-branch HEAD the worktree
  208	  branched from (the commit `git worktree add -b` forked from). For `--in-place`
  209	  and `--adopt`, record the current base-branch HEAD / the adopted branch's
  210	  merge-base with base, respectively.
  211	- Extend `tasktool worktree status` with an `--integration` mode that reports, for
  212	  a slice:
  213	  - commits the base branch is ahead of `worktree_base_sha`,
  214	  - which **sibling slices** (same phase) landed on base since `worktree_base_sha`,
  215	  - whether any landed sibling shares an integration surface with this slice
  216	    (i.e. "you are stale against a sibling that wrote a surface you also write").
  217	  Detection/reporting only — hard to misuse, immediate value.
  218	
  219	**"Landed" source of truth (F2).** `closed` is a date, not proof the slice
  220	reached base. The integration report establishes "landed" in priority order:
  221	
  222	1. **`landed_base_sha` (authoritative).** Recorded on the slice at post-merge
  223	   prune: `tasktool worktree prune <slice-id>` runs *after* the merge in
  224	   `finishing-a-development-branch`, so at prune time tasktool stamps
  225	   `landed_base_sha` = current base-branch HEAD. A non-null `landed_base_sha` is
  226	   definitive proof the slice shipped to base, and is robust to squash-merges and
  227	   later branch deletion (the failure modes that break ancestry checks).
  228	   **Stamping preconditions (F6).** `landed_base_sha` is stamped **only** when all
  229	   hold: (a) slice status is `done` (never `cancelled`); (b) the prune is the
  230	   normal guarded path — the prune's existing branch-merged guard passed, proving
  231	   `worktree_branch` is merged into base; (c) it is **not** a `--force` prune
  232	   (force bypasses the merged guard, so the merged state is unproven) and **not** a
  233	   `--finalize`-only cleanup unless the merged state was already proven in the same
  234	   prune. A cancelled slice, a forced/unmerged prune, or a finalize-only path
  235	   leaves `landed_base_sha` `None` — better to report `landed: unknown` than to
  236	   fabricate a landed signal.
  237	2. **Branch-ancestry fallback.** For a done slice with a still-existing
  238	   `worktree_branch` but no `landed_base_sha` (e.g. merged outside the prune path),
  239	   `git merge-base --is-ancestor <worktree_branch> <base-HEAD>` decides. Reported
  240	   as a weaker signal.
  241	3. **Unknown.** A done slice with neither signal is reported as
  242	   `landed: unknown` (not silently treated as landed), so the coordinator knows the
  243	   integration check could not prove it.
  244	
  245	The "since `worktree_base_sha`" window uses commit ordering on base
  246	(`git rev-list worktree_base_sha..base-HEAD`); a sibling counts as "landed since"
  247	when its `landed_base_sha` is in that range, or its branch merged into that range.
  248	
  249	### 4.E Conservative `worktree sync` (`worktree*.py`) — deferral candidate
  250	
  251	`tasktool worktree sync <slice-id>` integrates the current base branch into the
  252	slice's worktree branch, with strict preconditions, so the recovery checkpoint
  253	has a first-class command instead of raw git:
  254	
  255	- refuses unless the worktree tree is clean,
  256	- requires the configured authoritative base branch (no guessing),
  257	- requires an explicit `--merge` or `--rebase` choice (no default mutation),
  258	- refuses if there is unresolved tasklist drift,
  259	- **on success, advances `worktree_base_sha`** to the base-branch HEAD that was
  260	  integrated, so subsequent `worktree status --integration` runs do not repeatedly
  261	  re-report already-integrated base commits,
  262	- on success, prints the follow-up (regenerate derived artifacts, rerun
  263	  verification) rather than assuming it.
  264	
  265	Ships **after** §4.D. If scope tightens, `sync` is deferred and the recovery
  266	checkpoint (§4.F) falls back to documented raw-git steps; detection (§4.D) still
  267	delivers the core value.
  268	
  269	### 4.F Skill changes (recovery + discipline)
  270	
  271	- **`subagent-driven-development`:**
  272	  1. After `tasktool ready-slices <phase-id>`, run `tasktool surface check
  273	     <phase-id>`. Do **not** parallel-dispatch slices that share an integration
  274	     surface without a declared `depends_on` or a shared `coordination_group` —
  275	     serialize them (add a dep) or coordinate them (assign a `coordination_group`,
  276	     designate an integration owner, plan to run the registry playbook).
  277	  2. New **"integrate current main" checkpoint** in the slice-end sequence,
  278	     *before* `external-review --kind post-slice`: run `tasktool worktree status
  279	     <slice-id> --integration`. If a sibling has landed since `worktree_base_sha`,
  280	     integrate base (`tasktool worktree sync … --merge|--rebase`, or documented
  281	     raw-git fallback), regenerate derived artifacts (checksums/snapshots), rerun
  282	     verification, **then** run the post-slice review.
  283	  3. Reference a new **centralized-registry merge playbook**
  284	     (`skills/subagent-driven-development/references/registry-merge-playbook.md`):
  285	     preserve **both** semantic additions, regenerate checksums/snapshots, rerun
  286	     focused parser/schema/seed tests, then rerun integrated verification.
  287	- **`tasklist-discipline`:** document `surface`/`reserve`/`coordinate` in the
  288	  conceptual model and daily-commands list; document the recommended surface
  289	  vocabulary and the `coordination_group` vs `parallel_group` distinction; add
  290	  red-flag rows:
  291	  - "These slices are feature-independent, so they're parallel-safe" → parallel
  292	    safety is about **write surface**, not feature independence; declare surfaces
  293	    and run `surface check`.
  294	  - "I'll pick a sort slot / collection name / route slug freely" → **reserve** it
  295	    so siblings cannot collide; for project-global resources use `--scope project`.
  296	  - "We both need the CMS registry, so I'll just `parallel_group` them" → shared
  297	    surface needs a `coordination_group` (coordinate) or a `depends_on`
  298	    (serialize), not a `parallel_group` (which asserts independence).
  299	- **`phase-planning` / `writing-plans`:** when proposing parallel groups, declare
  300	  each slice's integration surfaces and reservations and emit a **surface/
  301	  reservation table** in the plan; run `tasktool surface check <phase-id>` before
  302	  ratifying parallel groups.
  303	
  304	### 4.G Plan ↔ tracker drift enforcement (`validate.py`, skills) — partial defer OK
  305	
  306	- Plans (and phase-planning docs) include a structured **surface/reservation
  307	  table** per slice (enforced by the skills in §4.F).
  308	- `tasktool validate` (or `artifact status --strict`) gains a check that declared
  309	  `integration_surfaces`/`reservations` on a slice are reflected in its plan's
  310	  table, flagging drift. Where parsing the plan table is too brittle for this
  311	  phase, the minimum bar is a `validate` warning when a slice in a `parallel_group`
  312	  declares **no** surfaces at all (the "you forgot to think about this" nudge).
  313	
  314	### 4.H Merge-safe reviewer artifacts (`external-review`) — investigate-first, deferral candidate
  315	
  316	The P20 report cited reviewer-request files as add/add-conflicting. **Current
  317	`external-reviewer` already mitigates the obvious cause**: post-slice/post-phase
  318	chain folders are keyed by `work_id`
  319	(`skills/external-review/scripts/external-reviewer.py:727`), request files are
  320	round/role-unique (`…:1403`), and `--work-id` is required for post-slice/post-phase
  321	(`…:2439`). So the spec does **not** assume a current bug.
  322	
  323	S8 is therefore an **investigation slice, not a fix slice**: reproduce the reported
  324	collision against *current* `external-reviewer` (the P20 conflict may have come from
  325	an older bridge, from `docs/tasklist.json` close churn rather than request files, or
  326	from a phase-level shared path). Decide one of:
  327	
  328	- **Reproduces** → fix with per-slice/round-unique paths or an append/merge-safe
  329	  format, with the reproduced scenario as the regression test.
  330	- **Does not reproduce** → document why in the phase archive note and **drop S8**;
  331	  the residual `docs/tasklist.json` close-churn conflict is already addressed by the
  332	  integrate-current-main checkpoint (§4.F), not by reviewer-artifact naming.
  333	
  334	S8 carries no behavioural commitment beyond the investigation until the collision is
  335	grounded.
  336	
  337	### 4.I Deferred / future (recorded, not built)
  338	
  339	- `tasktool surface audit <slice-id>` — compares the slice branch diff to
  340	  configurable path globs and warns on **undeclared** surfaces ("you touched
  341	  `infra/directus/**` but did not declare `directus-schema`"). Warning-only safety
  342	  net; complements but does not replace explicit declaration.
  343	- A `reservation.touches_existing` distinction for maintenance edits to shared
  344	  resources.
  345	- Cross-project (multi-repo) reservation registries.
  346	
  347	## 5. Recommended slice decomposition
  348	
  349	The implementation plan (writing-plans) will detail tasks; this is the proposed
  350	shape, dependencies, and parallel/coordination assumptions.
  351	
  352	| Slice | Scope | depends_on | Surfaces (this phase) |
  353	|-------|-------|-----------|------------------------|
  354	| `S1` | Data model + migration (schema v3): surfaces, reservations{resource,value,scope,note}, coordination_group, worktree_base_sha, landed_base_sha, project reservations_ledger (LedgerReservation) | — | `model`, `serialize`, `migrate` |
  355	| `S2` | `surface` / `reserve` / `coordinate` CLI; reservation allocation refusal (phase + project scope) + `--force --reason`; ledger population on archive | `S1` | `cli`, `commands` |
  356	| `S3` | Scheduling overlap detection: `ready-slices`/`schedule` warnings, `surface check`, `ratify` warning, coordination-group suppression | `S1`, `S2` | `commands` |
  357	| `S4` | `worktree start` base-sha recording + `worktree prune` landed-sha stamping + `worktree status --integration` | `S1` | `commands`, `worktree` |
  358	| `S5` | Conservative `worktree sync` (advances base-sha; deferral candidate) | `S4` | `worktree` |
  359	| `S6` | Skill changes: `subagent-driven-development` checkpoint + registry-merge-playbook; `tasklist-discipline`; `phase-planning`/`writing-plans` tables | `S2`, `S3`, `S4` | `skills` |
  360	| `S7` | Plan ↔ tracker drift validation | `S1`, `S6` | `validate` |
  361	| `S8` | **Investigate** reviewer-artifact collision vs current bridge; fix only if reproduced, else drop | — | `external-review`, `reviewer-artifacts` |
  362	
  363	Parallel/coordination notes (dog-fooding the model):
  364	
  365	- `S2` and `S4` both depend only on `S1` and share **no** integration surface
  366	  (`commands`/`cli` vs `worktree`) → genuinely parallel.
  367	- `S3` depends on `S2` (it warns using the data `S2` writes) → serialized.
  368	- `S7` and `S8` touch disjoint surfaces (`validate` vs `external-review`) →
  369	  parallel, but each depends on its own prerequisites.
  370	- `S6` writes `skills` and documents the commands from `S2`/`S3`/`S4`; it should
  371	  land after they stabilize.
  372	
  373	## 6. Testing strategy
  374	
  375	- **Model/migration (`S1`):** round-trip serialize/deserialize with the new
  376	  fields; v1→v3 and v2→v3 migration; defaults; `reservations_ledger` round-trip.
  377	- **CLI (`S2`):** `surface add/remove/list`; `reserve add` refusal on duplicate
  378	  within phase scope and project scope (including against done slices and the
  379	  ledger); `--force` requires `--reason`, mutates only the reserving slice, records
  380	  the override note; two `--force`-shared project reservations both survive ledger
  381	  archive (dedupe on `resource:value:scope:owner_id`); re-archiving a phase is
  382	  idempotent; `coordinate` set/clear.
  383	- **Scheduling (`S3`):** overlap warning emitted for surface-sharing siblings with
  384	  no dep/coordination link; suppressed within `coordination_group`; suppressed
  385	  when a dep links them; `surface check` JSON shape; `ratify` warning.
  386	- **Worktree (`S4`/`S5`):** `worktree_base_sha` recorded on `start`/`--in-place`/
  387	  `--adopt`; `landed_base_sha` stamped at post-merge `prune`; `status
  388	  --integration` identifies landed surface-sharing siblings via `landed_base_sha`
  389	  (authoritative), branch-ancestry (fallback), and `landed: unknown` (neither);
  390	  `sync` precondition refusals (dirty tree, wrong branch, missing merge/rebase
  391	  choice, tasklist drift) and base-sha advancement on success. **Stamping
  392	  guards:** `landed_base_sha` is stamped on the normal merged-branch prune of a
  393	  `done` slice, and is **not** stamped for a cancelled-slice prune, a `--force`
  394	  prune of an unmerged branch, or a `--finalize`-only cleanup.
  395	- **Skills (`S6`):** docs lifecycle test extended to assert the new commands and
  396	  the integrate-main checkpoint are documented; playbook file exists.
  397	- **Validation (`S7`):** drift detection / no-surface-in-parallel-group warning.
  398	- **Reviewer artifacts (`S8`):** first reproduce (or fail to reproduce) the
  399	  reported add/add collision against the current bridge; only if reproduced, a
  400	  regression test asserting two simulated sibling worktrees produce non-colliding
  401	  request paths.
  402	
  403	## 7. Rollout & compatibility
  404	
  405	- All new fields default empty; existing projects load unchanged after the v3
  406	  migration. The model is **opt-in** — projects that declare nothing behave exactly
  407	  as today.
  408	- New warnings are non-fatal; the only new *refusal* is duplicate scarce-resource
  409	  allocation, which is overridable with `--force`.
  410	- Version bump and plugin re-sync handled at phase close per the repo's release
  411	  policy (not during spec/plan authoring).

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

[truncated: 298 additional lines]
### docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md

    1	# P7.S7 — Plan ↔ tracker drift validation: Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Add two non-fatal `tasktool validate` warnings so a slice's tracker-declared `integration_surfaces`/`reservations` cannot silently diverge from its plan document.
    6	
    7	**Architecture:** One new pure helper `find_surface_drift_warnings(p, repo_root, *, include_plan_checks)` in `tools/tasktool/validate.py`, mirroring the existing `find_path_warnings`. It runs Check 1 (a slice in a `parallel_group` declaring no surfaces — always on) and, when `include_plan_checks` is true, Check 2 (a tracker-declared surface/reservation absent from the slice's plan file — substring presence, not table parsing). It is wired into `_cmd_validate_at_root` next to `find_path_warnings`, with Check 2 gated on `not no_path_warnings`. No model/schema/CLI change; warnings flow through the existing text/JSON `warnings` channel and never change the exit code.
    8	
    9	**Tech Stack:** Python 3.11+, stdlib only. Tests with `unittest` under `tools/tasktool/tests/`.
   10	
   11	**Spec:** [`docs/specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md`](../specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md) (§4 is authoritative). Implements P7 spec §4.G.
   12	
   13	---
   14	
   15	## Scheduling contract
   16	
   17	`tasktool show P7.S7` / `tasktool schedule P7` confirm:
   18	
   19	- `depends_on = [P7.S1, P7.S6]` — both `done`. S1 added the `integration_surfaces`/`reservations`/`coordination_group` fields this plan reads; S6 established the plan-table convention this check audits.
   20	- `parallel_group = none`, `coordination_group = none`. S7 is an independently-executable single slice.
   21	- **Integration surfaces for S7 itself:** `validate` (it edits `validate.py` + its test). Disjoint from every other P7 slice's surfaces (`skills`, `worktree`, `commands`/`cli`), and all siblings are terminal anyway — no overlap, no coordination needed. The S7 row currently carries this only as a prose note; Task 5 declares it as a real `integration_surfaces` value (`tasktool surface add P7.S7 validate`) so the tracker is self-consistent before ratification — dogfooding the very check this slice ships.
   22	
   23	No dependency-graph change is required. Task 5 declares S7's own write surface and then ratifies the row.
   24	
   25	## How to run the tools
   26	
   27	All `tasktool`/`pytest` commands run from the repo root unless noted. The test module is `tools/tasktool/tests/test_validate.py`; run focused tests with:
   28	
   29	```bash
   30	cd tools/tasktool && python -m pytest tests/test_validate.py -k drift -q
   31	```
   32	
   33	The package imports as `tasktool` (the `tools/tasktool/` dir is the package root on `sys.path` when invoked via the shim / from inside `tools/tasktool`).
   34	
   35	## File structure
   36	
   37	| File | Responsibility | Change |
   38	|------|----------------|--------|
   39	| `tools/tasktool/validate.py` | Structural validation + non-fatal warning helpers | **Modify** — add `find_surface_drift_warnings` (reuses `is_terminal`, already imported) |
   40	| `tools/tasktool/commands.py` | `validate` command wiring (`_cmd_validate_at_root`) | **Modify** — import and call the new helper alongside `find_path_warnings` |
   41	| `tools/tasktool/tests/test_validate.py` | Validation unit tests | **Modify** — add a `SurfaceDriftWarningTests` class; extend imports (`Reservation`, `Status`) |
   42	
   43	The mirror copy under `plugins/superstar/tools/tasktool/` is produced by the publish/sync scripts at release time; **do not hand-edit it** in this slice.
   44	
   45	---
   46	
   47	## Task 1: Check 1 — no-surface-in-parallel-group nudge
   48	
   49	Spec §4.B. Pure, no file I/O. A non-terminal slice with a `parallel_group` set but empty `integration_surfaces` warrants a nudge.
   50	
   51	**Files:**
   52	- Modify: `tools/tasktool/validate.py` (add `find_surface_drift_warnings`; `is_terminal` is already imported)
   53	- Test: `tools/tasktool/tests/test_validate.py` (new `SurfaceDriftWarningTests`)
   54	
   55	- [ ] **Step 1: Extend the test imports**
   56	
   57	At the top of `tools/tasktool/tests/test_validate.py`, the model import currently ends with `Status,`. Add `Reservation,` to that `from tasktool.model import (...)` block (it already imports `Status`). The final block must include `Reservation` and `Status`:
   58	
   59	```python
   60	from tasktool.model import (
   61	    ArchivedCrossCutting,
   62	    Project,
   63	    Phase,
   64	    Slice,
   65	    Task,
   66	    CrossCutting,
   67	    BlockedOn,
   68	    Reservation,
   69	    Status,
   70	)
   71	```
   72	
   73	- [ ] **Step 2: Write the failing test for Check 1**
   74	
   75	Append this class to `tools/tasktool/tests/test_validate.py`:
   76	
   77	```python
   78	class SurfaceDriftWarningTests(unittest.TestCase):
   79	    def test_parallel_group_no_surfaces_warns(self):
   80	        from tasktool.validate import find_surface_drift_warnings
   81	        p = _project_with_slice(parallel_group="core")
   82	        with tempfile.TemporaryDirectory() as td:
   83	            warnings = find_surface_drift_warnings(
   84	                p, Path(td), include_plan_checks=True
   85	            )
   86	        self.assertTrue(
   87	            any("parallel_group" in w and "P1.S1" in w for w in warnings),
   88	            warnings,
   89	        )
   90	
   91	    def test_parallel_group_with_surfaces_no_warn(self):
   92	        from tasktool.validate import find_surface_drift_warnings
   93	        p = _project_with_slice(
   94	            parallel_group="core", integration_surfaces=["commands"]
   95	        )
   96	        with tempfile.TemporaryDirectory() as td:
   97	            warnings = find_surface_drift_warnings(
   98	                p, Path(td), include_plan_checks=True
   99	            )
  100	        self.assertEqual(
  101	            [w for w in warnings if "parallel_group" in w], []
  102	        )
  103	
  104	    def test_no_parallel_group_no_surfaces_no_warn(self):
  105	        from tasktool.validate import find_surface_drift_warnings
  106	        p = _project_with_slice()  # no parallel_group, no surfaces
  107	        with tempfile.TemporaryDirectory() as td:
  108	            warnings = find_surface_drift_warnings(
  109	                p, Path(td), include_plan_checks=True
  110	            )
  111	        self.assertEqual(warnings, [])
  112	
  113	    def test_terminal_slice_in_parallel_group_no_warn(self):
  114	        from tasktool.validate import find_surface_drift_warnings
  115	        p = _project_with_slice(
  116	            parallel_group="core",
  117	            status=Status.DONE,
  118	            closed="2026-05-18",
  119	        )
  120	        with tempfile.TemporaryDirectory() as td:
  121	            warnings = find_surface_drift_warnings(
  122	                p, Path(td), include_plan_checks=True
  123	            )
  124	        self.assertEqual(warnings, [])
  125	
  126	    def test_check1_runs_even_when_plan_checks_disabled(self):
  127	        from tasktool.validate import find_surface_drift_warnings
  128	        p = _project_with_slice(parallel_group="core")
  129	        with tempfile.TemporaryDirectory() as td:
  130	            warnings = find_surface_drift_warnings(
  131	                p, Path(td), include_plan_checks=False
  132	            )
  133	        self.assertTrue(
  134	            any("parallel_group" in w for w in warnings), warnings
  135	        )
  136	```
  137	
  138	- [ ] **Step 3: Run the test to verify it fails**
  139	
  140	Run: `cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q`
  141	Expected: FAIL — `ImportError: cannot import name 'find_surface_drift_warnings'`.
  142	
  143	- [ ] **Step 4: Implement Check 1 in `find_surface_drift_warnings`**
  144	
  145	First, extend the existing model import near the top of `tools/tasktool/validate.py`. It currently ends:
  146	
  147	```python
  148	from tasktool.model import (
  149	    ArchivedCrossCutting,
  150	    Project,
  151	    Phase,
  152	    Slice,
  153	    Task,
  154	    CrossCutting,
  155	    Status,
  156	    PlanningStatus,
  157	    is_terminal,
  158	)
  159	```
  160	
  161	`is_terminal` is already imported — no change needed there. Now add the new function after `find_path_warnings` (after its `return warnings`, around line 256):
  162	
  163	```python
  164	def find_surface_drift_warnings(
  165	    p: Project, repo_root: Path, *, include_plan_checks: bool
  166	) -> list[str]:
  167	    """Non-fatal warnings that a slice's tracker-declared integration surfaces /
  168	    reservations are not reflected in its plan (Check 2, gated by
  169	    `include_plan_checks`), or that a slice in a parallel_group declares no surfaces
  170	    at all (Check 1, always run). Pure and non-raising: returns [] when clean and
  171	    swallows plan read errors to a skip. Mirrors find_path_warnings. See spec §4."""
  172	    warnings: list[str] = []
  173	    for ph in p.phases:
  174	        for s in ph.slices:
  175	            if is_terminal(s.status):
  176	                continue
  177	            scope = f"{ph.id}.{s.id}"
  178	            # Check 1 — parallel_group slice with no declared surfaces.
  179	            if s.parallel_group is not None and not s.integration_surfaces:
  180	                warnings.append(
  181	                    f"{scope}: in parallel_group {s.parallel_group!r} but declares "
  182	                    f"no integration_surfaces — declare them with "
  183	                    f"`tasktool surface add {scope} <surface>` or remove it from the "
  184	                    f"parallel group"
  185	                )
  186	    return warnings
  187	```
  188	
  189	- [ ] **Step 5: Run the test to verify it passes**
  190	
  191	Run: `cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q`
  192	Expected: PASS (5 tests).
  193	
  194	- [ ] **Step 6: Commit**
  195	
  196	```bash
  197	git add tools/tasktool/validate.py tools/tasktool/tests/test_validate.py
  198	git commit -m "P7.S7: add no-surface-in-parallel-group validate nudge (Check 1)"
  199	```
  200	

[truncated: 392 additional lines]
### docs/specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md

    1	# P7.S7 — Plan ↔ tracker drift validation
    2	
    3	**Status:** design (spec)
    4	**Date:** 2026-06-05
    5	**Slice ID:** `P7.S7`
    6	**Parent phase:** [`P7 — Integration-surface-aware parallel slice safety`](2026-06-02-P7-integration-surface-parallel-safety-design.md)
    7	**Implements:** P7 spec §4.G ("Plan ↔ tracker drift enforcement").
    8	**Depends on:** P7.S1 (the `integration_surfaces`/`reservations`/`coordination_group` fields exist), P7.S6 (the skills now tell planners to emit a surface/reservation table in each plan, so there is something to check against).
    9	
   10	## 1. Problem
   11	
   12	P7 added a per-slice integration-surface model to the tracker: a slice declares the
   13	shared write `integration_surfaces` it mutates, the scarce `reservations` it
   14	allocates, and an optional `coordination_group` (P7.S1 data model, P7.S2 CLI). The
   15	workflow skills (P7.S6) now instruct planners to **emit a surface/reservation table
   16	in each slice plan** and to declare the same facts on the tracker before ratifying a
   17	parallel group.
   18	
   19	Nothing keeps those two records honest. A planner can:
   20	
   21	- declare `integration_surfaces` / `reservations` on the tracker (`tasktool surface
   22	  add` / `tasktool reserve add`) but never mention them in the plan document, or
   23	  amend the tracker after the plan was written — so the plan silently understates
   24	  what the slice writes; or
   25	- place a slice in a `parallel_group` (asserting it is independently mergeable) while
   26	  declaring **no** surfaces at all — the exact "we never thought about write surface"
   27	  omission that produced the `multistore` P20 conflict-bomb the whole phase exists to
   28	  prevent.
   29	
   30	The plan and the tracker are the two artifacts a coordinator reads when deciding
   31	whether slices may run in parallel. When they disagree, the safety the rest of P7
   32	provides is undermined: `surface check` reasons over the tracker, humans reason over
   33	the plan, and a gap between them reintroduces the original failure mode.
   34	
   35	## 2. Goals
   36	
   37	1. **Catch tracker→plan drift.** When a slice declares a surface or reservation on
   38	   the tracker that does **not** appear anywhere in its plan document, surface it as
   39	   a non-fatal `tasktool validate` warning so the planner reconciles the two.
   40	2. **Catch the "forgot entirely" omission.** When a non-terminal slice sits in a
   41	   `parallel_group` but declares **no** `integration_surfaces`, nudge the planner to
   42	   declare them (or drop the parallel grouping) — the spec's documented minimum bar
   43	   (P7 spec §4.G).
   44	3. **Stay non-fatal and opt-in.** No new refusals, no exit-code changes, no model or
   45	   schema change. Projects that declare nothing behave exactly as today. Warnings
   46	   flow through the existing `tasktool validate` text/JSON `warnings` channel.
   47	4. **Be robust to plan format.** The detection must not depend on parsing a
   48	   rigidly-structured markdown table, because P7.S6 specifies the surface/reservation
   49	   table only loosely (no fixed headers or column order). A lenient "is this value
   50	   mentioned in the plan at all?" check is deliberately preferred over a brittle
   51	   table parser.
   52	
   53	## 3. Non-goals (explicit)
   54	
   55	- **Strict markdown-table parsing.** Extracting per-slice rows/cells from the plan's
   56	  surface/reservation table and diffing each cell is explicitly **not** built. The
   57	  P7 spec (§3, §4.G) already rules path-glob/structured *inference* out as the
   58	  planning model and authorizes a lenient minimum bar where table parsing "is too
   59	  brittle for this phase." S7 honours that: it does a substring presence check, not a
   60	  table parse.
   61	- **Reverse-direction drift (plan declares, tracker missing).** Detecting a surface
   62	  that a plan's table lists but the tracker does not carry requires actually parsing
   63	  the plan to know what it *declares* versus merely *mentions*. That is deferred to a
   64	  future slice (recorded in §7), because it cannot be done without the brittle parser
   65	  this slice intentionally avoids.
   66	- **Blocking / refusal.** Drift is a warning, never an error. `tasktool validate`
   67	  exit code is unchanged by these checks (it remains driven by structural validation
   68	  errors only). This mirrors `find_path_warnings`, which is also non-fatal.
   69	- **Checking terminal slices.** `done`/`cancelled` slices shipped (or abandoned)
   70	  whatever they declared; re-litigating their plans adds only noise. Both checks
   71	  consider non-terminal slices only.
   72	- **New CLI surface.** No new subcommand. The checks ride the existing `tasktool
   73	  validate` command. `artifact status --strict` is intentionally left untouched so
   74	  the drift logic lives in exactly one place.
   75	- **Skill edits.** P7.S6 owns the plan-table convention and the planner-facing
   76	  guidance. S7 is pure tooling (`validate.py`); it adds no skill prose.
   77	
   78	## 4. Design
   79	
   80	All behaviour lives in `tools/tasktool/validate.py` and its wiring in
   81	`tools/tasktool/commands.py`. No `model.py`, `serialize.py`, or `migrate.py` change;
   82	no schema bump.
   83	
   84	### 4.A New function: `find_surface_drift_warnings`
   85	
   86	Add a module-level function mirroring the existing `find_path_warnings` shape (same
   87	file, same return contract — a list of human-readable warning strings, never
   88	raising):
   89	
   90	```python
   91	def find_surface_drift_warnings(
   92	    p: Project, repo_root: Path, *, include_plan_checks: bool
   93	) -> list[str]:
   94	    """Return non-fatal warnings where a slice's tracker-declared integration
   95	    surfaces / reservations are not reflected in its plan, or where a slice in a
   96	    parallel_group declares no surfaces at all. Mirrors find_path_warnings: pure,
   97	    non-raising, returns [] when clean. `include_plan_checks` gates the file-reading
   98	    half (Check 2, §4.C); Check 1 (§4.B) runs regardless. See §4.D for the flag's
   99	    binding contract."""
  100	```
  101	
  102	It walks every phase's slices, skipping terminal slices (`is_terminal(s.status)`),
  103	and applies the two checks below. Warning strings are scoped `P{ph}.{S}` to match the
  104	existing warning style (e.g. `P7.S3.surfaces: ...`).
  105	
  106	### 4.B Check 1 — no-surface-in-parallel-group nudge (pure, no file I/O)
  107	
  108	For each **non-terminal** slice with `s.parallel_group is not None` and
  109	`s.integration_surfaces == []`:
  110	
  111	```
  112	P7.S5: in parallel_group 'core' but declares no integration_surfaces —
  113	  declare them with `tasktool surface add P7.S5 <surface>` or remove it from the parallel group
  114	```
  115	
  116	Rationale: a slice that asserts parallel-independence (`parallel_group`) without
  117	naming a single write surface is the "we forgot to think about merge safety" smell.
  118	This is the spec's documented minimum bar and requires no plan file, so it always
  119	runs (it is not gated by `--no-path-warnings`; see §4.D). The check keys on
  120	`integration_surfaces` only — absence of a `reservation` is not a smell (most slices
  121	allocate no scarce resource), so reservations do not trigger this nudge.
  122	
  123	### 4.C Check 2 — tracker-surface-absent-from-plan drift (lenient parse)
  124	
  125	For each **non-terminal** slice that has a `plan_path`, where that plan file **exists
  126	on disk**, and that declares ≥1 surface or reservation: read the plan text once
  127	(UTF-8), lowercase it, and for each declared item check substring presence
  128	(case-insensitive):
  129	
  130	- for each `surface` in `s.integration_surfaces`: warn if `surface.lower()` is not a
  131	  substring of the plan text:
  132	
  133	  ```
  134	  P7.S3.surfaces: tracker declares surface 'commands' but it does not appear in
  135	    plan docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md (plan may be stale)
  136	  ```
  137	
  138	- for each `reservation` in `s.reservations`: form the token `f"{resource}:{value}"`
  139	  and warn if that token (lowercased) is not a substring of the plan text:
  140	
  141	  ```
  142	  P7.S5.reservations: tracker declares reservation 'homepage-sort:15' but it does
  143	    not appear in plan docs/plans/...md (plan may be stale)
  144	  ```
  145	
  146	Skip conditions (no warning, no crash):
  147	
  148	- `plan_path is None` → the slice has no plan to check; skip Check 2 for it.
  149	- `plan_path` set but the file does not exist on disk → **skip** (do not emit a Check 2
  150	  warning). The missing file is already reported by the existing
  151	  `find_path_warnings` (`{scope}.plan_path: path does not exist`); S7 must not
  152	  double-warn. A read error (e.g. permissions) is likewise swallowed to a skip — this
  153	  is a best-effort nudge, not a gate.
  154	- slice declares no surfaces and no reservations → nothing to check.
  155	
  156	The substring bar is deliberately loose: the value need only be **mentioned
  157	somewhere** in the plan (a table cell, a prose sentence, a code fence). The goal is
  158	"did the planner account for this surface at all?", not "is the table perfectly
  159	formatted." False negatives (the plan mentions the surface only in unrelated prose)
  160	are an accepted cost of avoiding the brittle table parser §3 rejects.
  161	
  162	### 4.D Wiring in `commands.py`
  163	
  164	In `_cmd_validate_at_root`, alongside the existing `find_path_warnings` call. The new
  165	function takes one flag, `include_plan_checks`, that gates the file-reading half:
  166	
  167	```python
  168	if project is not None and not errors:
  169	    # Check 1 always runs; Check 2 (reads plan files) only when plan files are present.
  170	    warnings.extend(
  171	        find_surface_drift_warnings(
  172	            project, repo_root, include_plan_checks=not no_path_warnings
  173	        )
  174	    )
  175	    if not no_path_warnings:
  176	        warnings.extend(find_path_warnings(project, repo_root))
  177	```
  178	
  179	Behaviour contract:
  180	
  181	- **Check 1** (no file I/O) runs **always** — it is safe in any context, so
  182	  `find_surface_drift_warnings` emits it regardless of `include_plan_checks`.
  183	- **Check 2** (reads plan files) runs **only** when `include_plan_checks` is true,
  184	  i.e. `not no_path_warnings`. The pre-commit hook passes `--no-path-warnings` because
  185	  it validates a **sandboxed copy** of `docs/tasklist.json` whose referenced plan
  186	  files are not present in the sandbox; running Check 2 there would emit false "does
  187	  not appear in plan" warnings for every declared surface. Gating Check 2 on the same
  188	  flag as `find_path_warnings` keeps the two file-dependent checks consistent.
  189	
  190	The binding signature is `find_surface_drift_warnings(p: Project, repo_root: Path, *,
  191	include_plan_checks: bool) -> list[str]`, matching the §4.A sketch.
  192	
  193	Warnings are appended to the same `warnings` list the command already builds, so they
  194	appear in both the text output (`warning: <msg>`) and the JSON output
  195	(`{"warnings": [...]}`), and they **do not** change `rc` (which stays driven by
  196	`errors`).
  197	
  198	### 4.E What does *not* change
  199	
  200	- No `model.py` / `serialize.py` / `migrate.py` edit; no schema version bump.

[truncated: 65 additional lines]

<!-- superstar-prompt:end -->