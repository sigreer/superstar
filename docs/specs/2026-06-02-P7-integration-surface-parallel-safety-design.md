# P7 — Integration-surface-aware parallel slice safety

**Status:** design (spec)
**Date:** 2026-06-02
**Phase ID:** `P7`

## 1. Problem

`tasktool` decides whether slices may run in parallel from **declared feature
dependencies** (`Slice.depends_on`) and the `parallel_group` tag. Those answer
"does S4's feature need S3's feature first?" They do **not** answer the question
that actually governs safe parallel execution: **what shared write surface does
each slice mutate?**

This gap produced a real failure in the `multistore` project, phase P20. Four
storefront-marketing slices (`P20.S2`–`P20.S5`) each declared a dependency only
on the bootstrap slice `P20.S1`, so `tasktool ready-slices`/`schedule` reported
them as independently executable. They were feature-distinct (slider, promo
bands, overlays, blog) but **integration-overlapping**: every one of them wrote
the same centralized CMS-block machinery — block contracts, parser allowlists,
Directus schema/seed files, renderer dispatch, theme CSS tails, and the homepage
ordering array.

The observed consequences:

1. **Conflict-bomb merges.** `P20.S4`'s merge conflicted across `page-renderer.tsx`,
   theme CSS, reviewer-request artifacts, `docs/tasklist.json`, Directus
   bootstrap/schema/seed files, content-contract schemas/types, and parser tests.
2. **Stale-base merges.** `P20.S4` was completed in a worktree that branched from
   `main` *before* `P20.S2`/`P20.S3` and their cleanup landed. The worktree
   snapshot was older than `main`, so the merge replayed churn that was already
   integrated.
3. **A real semantic collision, not just textual churn.** `P20.S3` and `P20.S4`
   independently chose homepage sort slot `15`. Nothing forced the second slice
   onto a free slot at planning time; the collision was discovered and resolved
   at merge.
4. **Merge-unsafe reviewer artifacts.** Generated reviewer-request files
   add/add-conflicted despite not being behavioral code.

The root cause is **dependency modeling by feature intent rather than by
integration surface.** "Slider" and "promo bands" were non-dependent product
slices, but they both wrote the same registry, schema, seed arrays, ordering
slots, parser unions, and theme areas. The tool allowed parallel execution
because the declared dependencies were technically satisfied.

## 2. Goals

1. **Prevention.** Let planning declare, per slice, the **integration surfaces**
   it writes and the **scarce resources** it allocates. `tasktool` warns when
   sibling ready/in-progress slices share a surface with no dependency or
   coordination link, and *refuses* a duplicate scarce-resource allocation.
2. **Recovery.** When a sibling slice has landed on the base branch since a
   slice's worktree branched, surface that fact reliably and provide a
   conservative "integrate current main" path before the post-slice review/merge,
   plus a documented centralized-registry merge playbook.
3. **Merge-safe reviewer artifacts.** Generated reviewer-request files must never
   add/add-conflict between sibling worktrees.
4. **Plan ↔ tracker coherence.** Declared surfaces/reservations must be reflected
   in planning artifacts so the plan and the tracker cannot silently diverge.

## 3. Non-goals (explicit)

- **Directus-specific verifier diagnostics and stale-token handling.** These were
  real `multistore` pain points (a stale `DIRECTUS_ADMIN_TOKEN` shadowing valid
  admin credentials made a non-code problem look like a schema failure), but they
  are project-specific. Superstar core is general-purpose and zero-dependency;
  Directus tooling belongs in the `multistore` project, not here.
- **Automatic merge-conflict resolution.** The tooling detects and routes; it does
  not auto-merge semantic conflicts.
- **Path-glob surface *inference* as the primary model.** Explicit declaration is
  the source of truth. A path-glob comparison survives only as a deferred,
  warning-only post-implementation *audit* (§4.G), never as the planning model.
- **A "touches existing resource" reservation kind.** Reservations model scarce
  *allocations* (claiming a new value). Modifying a shared existing resource is a
  *surface/coordination* concern, not an allocation, so maintenance work is not
  falsely blocked. A future "touches-existing" field is noted, not built here.
- **`worktree sync` as an unconditional command.** Detection ships first; the
  mutating sync command is gated behind strict preconditions and is the explicit
  deferral candidate if scope tightens.

## 4. Design

### 4.A Data model (`model.py`, schema `v2 → v3`; `migrate.py`)

Add to `Slice`:

- `integration_surfaces: list[str]` — conventional surface tags naming shared
  write areas the slice mutates. Free-form strings, but a recommended vocabulary
  is documented in `tasklist-discipline` (e.g. `cms-block-registry`,
  `directus-schema`, `page-renderer-dispatch`, `theme-tail-css`,
  `content-contract-types`, `reviewer-artifacts`). Default `[]`.
- `reservations: list[Reservation]` where
  `Reservation = {resource: str, value: str, scope: "phase" | "project", note: str | None}`.
  A reservation is a **scarce allocation claim** on a single value
  (`homepage-sort:15`, `directus-collection:homepage_slider`, `route-slug:/offers`,
  `block-kind:slider`, `cache-tag:home`). Default `[]`.
- `coordination_group: str | None` — names a set of slices that *intentionally*
  share an integration surface and agree to coordinate (serialize reviews,
  designate an integration owner, run the registry merge playbook). Distinct from
  `parallel_group`, which asserts independent parallelism. Default `None`.
- `worktree_base_sha: str | None` — the base-branch commit the slice's worktree
  was created from, recorded at `tasktool start`. Enables reliable
  "a sibling landed since this slice branched" detection that survives later
  rebases/merges, instead of fragile merge-base inference. Default `None`.
- `landed_base_sha: str | None` — the base-branch commit at which this slice's
  work landed, recorded at post-merge prune (see §4.D). This is the authoritative
  "this slice shipped to base" signal that `closed` (a date) cannot provide.
  Default `None`.

Add to `Project`:

- `reservations_ledger: list[LedgerReservation]` where
  `LedgerReservation = Reservation + {owner_id: str, owner_phase_id: str, archived_date: str}`.
  Project-scoped reservations are copied here when their owning phase is archived,
  so project-scope uniqueness checks — and the refusal message that must name the
  holder (§4.B) — survive removal of shipped phases from the active tracker. The
  extra fields preserve the owning slice/phase and archive date for the refusal
  message and audit trail. Default `[]`.

Schema bump to `v3`. Migration is additive: missing fields default to empty/`None`
and `reservations_ledger` to `[]`. Round-trip and v1/v2 compatibility tests
extended.

**Serialization rule (F5).** New fields follow the existing omit-when-default
convention in `serialize.py`: an empty `integration_surfaces`/`reservations`,
a `None` `coordination_group`/`worktree_base_sha`/`landed_base_sha`, and an empty
`Project.reservations_ledger` are **omitted** on serialization, exactly as
default-valued worktree/workflow keys are today. Historical rows therefore gain no
churn on round-trip; a row's bytes change only once it actually declares a surface,
reservation, coordination group, or base SHA.

### 4.B Declaration CLI (`cli.py` + `commands.py`)

```sh
tasktool surface add <slice-id> <surface> [<surface>...]
tasktool surface remove <slice-id> <surface>
tasktool surface list [<phase-id>]

tasktool reserve add <slice-id> <resource>:<value> [--scope phase|project] [--note "..."] [--force --reason "..."]
tasktool reserve remove <slice-id> <resource>:<value>
tasktool reserve list [<phase-id>]

tasktool coordinate <slice-id> --group <name>     # set coordination_group
tasktool coordinate <slice-id> --clear
```

- `surface`/`coordinate` are declaration-only; they never refuse.
- **`reserve add` refuses** when the same `resource:value` is already held by
  another **non-cancelled** slice within the relevant scope:
  - `scope: phase` (default) — checks other non-cancelled slices in the same
    phase. Done slices count: a done slice shipped that value to `main`, so the
    slot is taken.
  - `scope: project` — checks all non-cancelled slices across **active** phases
    *and* `Project.reservations_ledger`.
  The refusal names the holding slice (from the slice row, or from the ledger's
  `owner_id`/`owner_phase_id`/`archived_date` for archived holders) and the value.
- **Override (F3).** `--force` is the only way to add a colliding reservation and
  **requires** `--reason "<text>"`. It mutates **only the reserving slice**: it
  appends the reservation and records a timestamped note
  `Reservation-override <ISO-ts>: <resource>:<value> over <holder-id> — <reason>`.
  The holder slice is **not** mutated. `--force` without `--reason` is refused.
  Without `--force`, a collision is a hard refusal (exit non-zero). This refusal
  is the gate that would have forced `P20.S4` off slot `15` at planning time.
- **Cancelled work never enters the ledger.** On `tasktool archive-phase`,
  project-scoped reservations from the phase's **non-cancelled (`done`)** slices
  are appended to `Project.reservations_ledger` as `LedgerReservation`s, carrying
  `owner_id`/`owner_phase_id`/`archived_date`. Cancelled slices ship nothing, so
  their reservations — including `--force` overrides — are released and never
  laddered.
- **Ledger dedupe preserves every holder (F7).** Dedup is keyed on
  `resource:value:scope:owner_id`, **not** `resource:value:scope`. Re-archiving the
  same phase is idempotent (same owner ⇒ same key), but two distinct `done` slices
  that intentionally `--force`-shared a project-scoped value both survive in the
  ledger, so the owner-metadata audit trail is never silently collapsed to one
  holder. A project-scope `reserve add` collision check that matches any ledger
  entry on `resource:value:scope` (regardless of owner) still refuses — multiple
  recorded holders strengthen, not weaken, the refusal message.

### 4.C Scheduling overlap detection (`commands.py`)

Augment the existing scheduling reporters; **surface overlap is a warning, not a
block** (surfaces are coarse — two slices may touch the same registry in
non-conflicting ways), while **reservation contention is already prevented at
declaration time**.

- `cmd_ready_slices` and `cmd_schedule`: for each ready/in-progress slice, compute
  the set of other non-terminal slices that (a) share ≥1 integration surface,
  (b) have **no** `depends_on` link in either direction, and (c) are **not** in
  the same `coordination_group`. Emit a `surface_overlap` field/warning listing
  the sibling(s) and shared surface(s). Slices in a shared `coordination_group`
  are reported as `coordinated`, not warned.
- New `tasktool surface check <phase-id>` — a dedicated read-only report:
  - every unguarded surface overlap (siblings sharing a surface without a dep or
    coordination link),
  - every coordinated surface (shared surface within a `coordination_group`),
  - reservation contention within the phase (should be empty if `reserve add`
    refusal held; surfaced for audit and for `--force` overrides).
  Text and `--format json`. Intended to be run during ratification and before
  parallel dispatch.
- `cmd_ratify --parallel-group <g>`: when adding a slice whose surfaces overlap
  another slice already in that `parallel_group` with no dep/coordination link,
  print a warning (does not refuse). Steers the planner toward either a
  `depends_on` (serialize) or a `coordination_group` (coordinate).

### 4.D Worktree integration detection (`worktree*.py`, `commands.py`)

- `tasktool start` records `worktree_base_sha` = the base-branch HEAD the worktree
  branched from (the commit `git worktree add -b` forked from). For `--in-place`
  and `--adopt`, record the current base-branch HEAD / the adopted branch's
  merge-base with base, respectively.
- Extend `tasktool worktree status` with an `--integration` mode that reports, for
  a slice:
  - commits the base branch is ahead of `worktree_base_sha`,
  - which **sibling slices** (same phase) landed on base since `worktree_base_sha`,
  - whether any landed sibling shares an integration surface with this slice
    (i.e. "you are stale against a sibling that wrote a surface you also write").
  Detection/reporting only — hard to misuse, immediate value.

**"Landed" source of truth (F2).** `closed` is a date, not proof the slice
reached base. The integration report establishes "landed" in priority order:

1. **`landed_base_sha` (authoritative).** Recorded on the slice at post-merge
   prune: `tasktool worktree prune <slice-id>` runs *after* the merge in
   `finishing-a-development-branch`, so at prune time tasktool stamps
   `landed_base_sha` = current base-branch HEAD. A non-null `landed_base_sha` is
   definitive proof the slice shipped to base, and is robust to squash-merges and
   later branch deletion (the failure modes that break ancestry checks).
   **Stamping preconditions (F6).** `landed_base_sha` is stamped **only** when all
   hold: (a) slice status is `done` (never `cancelled`); (b) the prune is the
   normal guarded path — the prune's existing branch-merged guard passed, proving
   `worktree_branch` is merged into base; (c) it is **not** a `--force` prune
   (force bypasses the merged guard, so the merged state is unproven) and **not** a
   `--finalize`-only cleanup unless the merged state was already proven in the same
   prune. A cancelled slice, a forced/unmerged prune, or a finalize-only path
   leaves `landed_base_sha` `None` — better to report `landed: unknown` than to
   fabricate a landed signal.
2. **Branch-ancestry fallback.** For a done slice with a still-existing
   `worktree_branch` but no `landed_base_sha` (e.g. merged outside the prune path),
   `git merge-base --is-ancestor <worktree_branch> <base-HEAD>` decides. Reported
   as a weaker signal.
3. **Unknown.** A done slice with neither signal is reported as
   `landed: unknown` (not silently treated as landed), so the coordinator knows the
   integration check could not prove it.

The "since `worktree_base_sha`" window uses commit ordering on base
(`git rev-list worktree_base_sha..base-HEAD`); a sibling counts as "landed since"
when its `landed_base_sha` is in that range, or its branch merged into that range.

### 4.E Conservative `worktree sync` (`worktree*.py`) — deferral candidate

`tasktool worktree sync <slice-id>` integrates the current base branch into the
slice's worktree branch, with strict preconditions, so the recovery checkpoint
has a first-class command instead of raw git:

- refuses unless the worktree tree is clean,
- requires the configured authoritative base branch (no guessing),
- requires an explicit `--merge` or `--rebase` choice (no default mutation),
- refuses if there is unresolved tasklist drift,
- **on success, advances `worktree_base_sha`** to the base-branch HEAD that was
  integrated, so subsequent `worktree status --integration` runs do not repeatedly
  re-report already-integrated base commits,
- on success, prints the follow-up (regenerate derived artifacts, rerun
  verification) rather than assuming it.

Ships **after** §4.D. If scope tightens, `sync` is deferred and the recovery
checkpoint (§4.F) falls back to documented raw-git steps; detection (§4.D) still
delivers the core value.

### 4.F Skill changes (recovery + discipline)

- **`subagent-driven-development`:**
  1. After `tasktool ready-slices <phase-id>`, run `tasktool surface check
     <phase-id>`. Do **not** parallel-dispatch slices that share an integration
     surface without a declared `depends_on` or a shared `coordination_group` —
     serialize them (add a dep) or coordinate them (assign a `coordination_group`,
     designate an integration owner, plan to run the registry playbook).
  2. New **"integrate current main" checkpoint** in the slice-end sequence,
     *before* `external-review --kind post-slice`: run `tasktool worktree status
     <slice-id> --integration`. If a sibling has landed since `worktree_base_sha`,
     integrate base (`tasktool worktree sync … --merge|--rebase`, or documented
     raw-git fallback), regenerate derived artifacts (checksums/snapshots), rerun
     verification, **then** run the post-slice review.
  3. Reference a new **centralized-registry merge playbook**
     (`skills/subagent-driven-development/references/registry-merge-playbook.md`):
     preserve **both** semantic additions, regenerate checksums/snapshots, rerun
     focused parser/schema/seed tests, then rerun integrated verification.
- **`tasklist-discipline`:** document `surface`/`reserve`/`coordinate` in the
  conceptual model and daily-commands list; document the recommended surface
  vocabulary and the `coordination_group` vs `parallel_group` distinction; add
  red-flag rows:
  - "These slices are feature-independent, so they're parallel-safe" → parallel
    safety is about **write surface**, not feature independence; declare surfaces
    and run `surface check`.
  - "I'll pick a sort slot / collection name / route slug freely" → **reserve** it
    so siblings cannot collide; for project-global resources use `--scope project`.
  - "We both need the CMS registry, so I'll just `parallel_group` them" → shared
    surface needs a `coordination_group` (coordinate) or a `depends_on`
    (serialize), not a `parallel_group` (which asserts independence).
- **`phase-planning` / `writing-plans`:** when proposing parallel groups, declare
  each slice's integration surfaces and reservations and emit a **surface/
  reservation table** in the plan; run `tasktool surface check <phase-id>` before
  ratifying parallel groups.

### 4.G Plan ↔ tracker drift enforcement (`validate.py`, skills) — partial defer OK

- Plans (and phase-planning docs) include a structured **surface/reservation
  table** per slice (enforced by the skills in §4.F).
- `tasktool validate` (or `artifact status --strict`) gains a check that declared
  `integration_surfaces`/`reservations` on a slice are reflected in its plan's
  table, flagging drift. Where parsing the plan table is too brittle for this
  phase, the minimum bar is a `validate` warning when a slice in a `parallel_group`
  declares **no** surfaces at all (the "you forgot to think about this" nudge).

### 4.H Merge-safe reviewer artifacts (`external-review`) — investigate-first, deferral candidate

The P20 report cited reviewer-request files as add/add-conflicting. **Current
`external-reviewer` already mitigates the obvious cause**: post-slice/post-phase
chain folders are keyed by `work_id`
(`skills/external-review/scripts/external-reviewer.py:727`), request files are
round/role-unique (`…:1403`), and `--work-id` is required for post-slice/post-phase
(`…:2439`). So the spec does **not** assume a current bug.

S8 is therefore an **investigation slice, not a fix slice**: reproduce the reported
collision against *current* `external-reviewer` (the P20 conflict may have come from
an older bridge, from `docs/tasklist.json` close churn rather than request files, or
from a phase-level shared path). Decide one of:

- **Reproduces** → fix with per-slice/round-unique paths or an append/merge-safe
  format, with the reproduced scenario as the regression test.
- **Does not reproduce** → document why in the phase archive note and **drop S8**;
  the residual `docs/tasklist.json` close-churn conflict is already addressed by the
  integrate-current-main checkpoint (§4.F), not by reviewer-artifact naming.

S8 carries no behavioural commitment beyond the investigation until the collision is
grounded.

### 4.I Deferred / future (recorded, not built)

- `tasktool surface audit <slice-id>` — compares the slice branch diff to
  configurable path globs and warns on **undeclared** surfaces ("you touched
  `infra/directus/**` but did not declare `directus-schema`"). Warning-only safety
  net; complements but does not replace explicit declaration.
- A `reservation.touches_existing` distinction for maintenance edits to shared
  resources.
- Cross-project (multi-repo) reservation registries.

## 5. Recommended slice decomposition

The implementation plan (writing-plans) will detail tasks; this is the proposed
shape, dependencies, and parallel/coordination assumptions.

| Slice | Scope | depends_on | Surfaces (this phase) |
|-------|-------|-----------|------------------------|
| `S1` | Data model + migration (schema v3): surfaces, reservations{resource,value,scope,note}, coordination_group, worktree_base_sha, landed_base_sha, project reservations_ledger (LedgerReservation) | — | `model`, `serialize`, `migrate` |
| `S2` | `surface` / `reserve` / `coordinate` CLI; reservation allocation refusal (phase + project scope) + `--force --reason`; ledger population on archive | `S1` | `cli`, `commands` |
| `S3` | Scheduling overlap detection: `ready-slices`/`schedule` warnings, `surface check`, `ratify` warning, coordination-group suppression | `S1`, `S2` | `commands` |
| `S4` | `worktree start` base-sha recording + `worktree prune` landed-sha stamping + `worktree status --integration` | `S1` | `commands`, `worktree` |
| `S5` | Conservative `worktree sync` (advances base-sha; deferral candidate) | `S4` | `worktree` |
| `S6` | Skill changes: `subagent-driven-development` checkpoint + registry-merge-playbook; `tasklist-discipline`; `phase-planning`/`writing-plans` tables | `S2`, `S3`, `S4` | `skills` |
| `S7` | Plan ↔ tracker drift validation | `S1`, `S6` | `validate` |
| `S8` | **Investigate** reviewer-artifact collision vs current bridge; fix only if reproduced, else drop | — | `external-review`, `reviewer-artifacts` |

Parallel/coordination notes (dog-fooding the model):

- `S2` and `S4` both depend only on `S1` and share **no** integration surface
  (`commands`/`cli` vs `worktree`) → genuinely parallel.
- `S3` depends on `S2` (it warns using the data `S2` writes) → serialized.
- `S7` and `S8` touch disjoint surfaces (`validate` vs `external-review`) →
  parallel, but each depends on its own prerequisites.
- `S6` writes `skills` and documents the commands from `S2`/`S3`/`S4`; it should
  land after they stabilize.

## 6. Testing strategy

- **Model/migration (`S1`):** round-trip serialize/deserialize with the new
  fields; v1→v3 and v2→v3 migration; defaults; `reservations_ledger` round-trip.
- **CLI (`S2`):** `surface add/remove/list`; `reserve add` refusal on duplicate
  within phase scope and project scope (including against done slices and the
  ledger); `--force` requires `--reason`, mutates only the reserving slice, records
  the override note; two `--force`-shared project reservations both survive ledger
  archive (dedupe on `resource:value:scope:owner_id`); re-archiving a phase is
  idempotent; `coordinate` set/clear.
- **Scheduling (`S3`):** overlap warning emitted for surface-sharing siblings with
  no dep/coordination link; suppressed within `coordination_group`; suppressed
  when a dep links them; `surface check` JSON shape; `ratify` warning.
- **Worktree (`S4`/`S5`):** `worktree_base_sha` recorded on `start`/`--in-place`/
  `--adopt`; `landed_base_sha` stamped at post-merge `prune`; `status
  --integration` identifies landed surface-sharing siblings via `landed_base_sha`
  (authoritative), branch-ancestry (fallback), and `landed: unknown` (neither);
  `sync` precondition refusals (dirty tree, wrong branch, missing merge/rebase
  choice, tasklist drift) and base-sha advancement on success. **Stamping
  guards:** `landed_base_sha` is stamped on the normal merged-branch prune of a
  `done` slice, and is **not** stamped for a cancelled-slice prune, a `--force`
  prune of an unmerged branch, or a `--finalize`-only cleanup.
- **Skills (`S6`):** docs lifecycle test extended to assert the new commands and
  the integrate-main checkpoint are documented; playbook file exists.
- **Validation (`S7`):** drift detection / no-surface-in-parallel-group warning.
- **Reviewer artifacts (`S8`):** first reproduce (or fail to reproduce) the
  reported add/add collision against the current bridge; only if reproduced, a
  regression test asserting two simulated sibling worktrees produce non-colliding
  request paths.

## 7. Rollout & compatibility

- All new fields default empty; existing projects load unchanged after the v3
  migration. The model is **opt-in** — projects that declare nothing behave exactly
  as today.
- New warnings are non-fatal; the only new *refusal* is duplicate scarce-resource
  allocation, which is overridable with `--force`.
- Version bump and plugin re-sync handled at phase close per the repo's release
  policy (not during spec/plan authoring).
