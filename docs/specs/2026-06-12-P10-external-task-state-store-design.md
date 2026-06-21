# P10 — External Task-State Store (sharded global git repo)

- **Work ID:** P10 (phase)
- **Date:** 2026-06-12
- **Status in tracker:** ready / not started (reserved via `tasktool prepare phase`)
- **Repo:** superstar (`tools/tasktool/` — tasktool's home; code + tests live here)
- **Pilot consumer:** multistore (`../../multistore`)

## 1. Problem

tasktool stores all mutable task state in a single repo-tracked file, `docs/tasklist.json`
(`DEFAULT_JSON_REL = "docs/tasklist.json"`, `tools/tasktool/commands.py:137`). In
`authoritative-checkout` mode — which multistore uses (its `.tasktool/config.json` sets
`mutation_mode` to `authoritative-checkout`) — every
lifecycle mutation from any worktree is routed to the **main checkout's** copy of that one
file (`_resolve_write_root` → `find_authoritative_root`, `commands.py:281-301`).

Before any write, `_write_context` calls `_ensure_authoritative_tasklist_clean()`, which
**hard-refuses the mutation if main's `docs/tasklist.json` has uncommitted changes**
(`commands.py:225-230`, invoked at `commands.py:335`). The refusal is correct given the
design: the auto-commit step is a pathspec commit, `git commit -- docs/tasklist.json`
(`_git_commit_scoped`, `commands.py:177-217`, command at line 192). A pathspec commit cannot
commit *part* of a file, so an unrelated staged edit to `docs/tasklist.json` (e.g. a
sibling task adding `refs`) would be **bundled into the unrelated lifecycle commit**.

The observed failure (multistore, 2026-06-12): a `tasktool close P25.S5` was blocked
because main's `docs/tasklist.json` carried an unrelated staged X72 `refs` edit — two
disjoint regions of one JSON file that the tool cannot separate. This recurs whenever work
happens in parallel (the normal case), because **globally-true task state is coupled to a
single per-worktree file**.

Root cause, stated precisely: task state (status, workflow step, reservations,
worktree/SHA bookkeeping) describes the *work*, not a *branch*. Storing it in one tracked
file forces it to branch, diverge, and serialize on a single path — manufacturing the
conflicts and dirty-tree blocks.

## 2. Goal & non-goals

**Goal.** Relocate mutable task state out of every project worktree into a single external
git-backed store, sharded one file per independently-mutated row, so that:

- a project worktree's cleanliness is **irrelevant** to tasktool mutations;
- concurrent lifecycle actions on independent rows never contend on a shared file;
- Git's safety properties (history, audit trail, offline access) are preserved without a
  running service.

**Non-goals (this phase).**

- Moving human-readable artifacts out of repos. Specs, plans, evidence, and reviewer chains
  **stay in the project repo** and branch with the code that produced them. Task rows
  reference them by path today (`refs: list[str]`, `model.py:88,104`); pinning each ref to
  a commit SHA is a deferred enhancement (§4.5), not part of the pilot.
- Building a daemon / MCP server. The store is a plain git repo; a service facade can be
  added later over the same data if ever wanted.
- Changing the in-memory `Project` data model (`tools/tasktool/model.py`). Only the
  (de)serialization seam changes.
- Migrating every project at once. Rollout is opt-in; multistore is the pilot.

## 3. Decisions (locked during brainstorming)

1. **Only state moves out**; artifacts stay in-repo, referenced by path (SHA-pinning
   deferred — §4.5).
2. **Sharded** storage — one file per independently-mutated row.
3. **Backing** — a dedicated git repo of sharded JSON (no SQLite, no service).
4. **Topology** — one global store, namespaced by project.
5. **Rollout** — opt-in third mutation mode; multistore migrated first as the pilot;
   superstar itself migrated only after the pilot proves out.

## 4. Architecture

### 4.1 A third mutation mode

A new `mutation_mode: "external-store"` joins the existing `local` and
`authoritative-checkout` (`tools/tasktool/config.py:9`, `VALID_MUTATION_MODES`). Projects on
the existing two modes are unaffected. `.tasktool/config.json` gains a `store` block:

```json
{
  "schema_version": 1,
  "tasklist": { "mutation_mode": "external-store", "authoritative_branch": "main" },
  "store": { "project_id": "multistore", "root": "~/.tasktool-store", "remote": null }
}
```

- `project_id` — namespace within the global store. Required in this mode.
- `root` — store location. Default `~/.tasktool-store`; overridable by
  `$TASKTOOL_STORE_ROOT` (for tests/CI/alternate machines).
- `remote` — optional git remote for cross-machine sync. `null` = local-only.

`config.py` is extended to parse/serialize the `store` block and to validate that
`external-store` requires a `project_id`.

### 4.2 Store layout

The store is its own git repo:

```
~/.tasktool-store/                 (git repo; optional remote; $TASKTOOL_STORE_ROOT override)
  projects/<project_id>/
    project.json                   # near-immutable header ONLY:
                                   #   project, schema_version, north_star, last_reviewed
    rows/<ID>.json                 # ONE file per slice / cross-cutting / phase-header
    archived/<ID>.json             # ONE file per archived phase / cross-cutting entry
    ledger/<NNNN>-<resource>.json  # ONE file per reservations-ledger entry (append-only)
```

**Shard granularity = the contention boundary = the *slice*, not the phase.** P25.S2 and
P25.S5 must be separate files; sharding at phase granularity would rebuild the same
collision one level up. Specifically:

- **Phase header** (`Phase` fields minus `slices`) → `rows/<Pn>.json`. Rarely mutated.
- **Slice** (`Slice`, including its child `tasks[]`) → `rows/<Pn.Sm>.json`. The child
  `tasks[]` stay inside the slice file because only the slice owner mutates them — no
  cross-owner contention.
- **Cross-cutting** (`CrossCutting`) → `rows/<Xn>.json`.
- **Archived entries** (`ArchivedPhase`, `ArchivedCrossCutting`, `model.py:156-168`) →
  one file each under `archived/`. Archive flows **append** these
  (`cmd_archive_phase` appends `archived_phases`, `commands.py:2768-2779`; cross archive
  appends `archived_cross_cutting`, `commands.py:855-862`), so per-entry files mean two
  independent archive flows touch **disjoint** files — no shared-file contention.
- **Reservation-ledger entries** (`LedgerReservation`, `model.py:70-78`) → one file each
  under `ledger/`. Phase archive ladders project reservations into the ledger
  (`commands.py:2730`); modelling each entry as its own append-only file keeps those
  writes disjoint too.

This is a deliberate response to the contention boundary: **no row-level or
archive/ledger mutation shares a mutable file with another.** The only genuinely shared
file is `project.json`, which now holds **only** the near-immutable header
(`north_star`/`last_reviewed`, mutated rarely — e.g. by phase-planning). Those infrequent
header writes are serialized by the store lock (§4.4) with no lost updates; they are never
on the hot path of closes/archives.

**No persisted index file.** The `Project` is assembled by reading `project.json` and
globbing `rows/*.json`, `archived/*.json`, `ledger/*.json` on each read. tasktool reads are
not perf-critical, and a persisted index would itself become a hot, contended file — the
exact thing we are eliminating. Display ordering is carried as an `order: int` field on
each row (mutated only by explicit reorder operations, which are rare).

### 4.3 Read/write seam (small blast radius)

The in-memory `Project`/`Phase`/`Slice`/`Task`/`CrossCutting` model (`model.py`) is
**unchanged**. Only the (de)serialization layer (`tools/tasktool/serialize.py`) and three
helpers in `commands.py` change:

- `_load` (`commands.py:232`): in `external-store` mode, read `project.json` + glob
  `rows/*.json` → assemble the identical `Project`.
- `_save` (`commands.py:238`): **dirty-diff write.** Re-read the current on-disk rows,
  serialize the new `Project` per-row, and write only rows whose serialized content changed
  (plus delete row files for archived/removed rows). Each row file is written via
  temp-file + atomic `rename` so a row is never observed half-written. Then commit exactly
  the changed paths in the store repo.
- `_write_context` / `_resolve_write_root` (`commands.py:281,324`): in `external-store`
  mode, **the project worktree's cleanliness is not checked** —
  `_ensure_authoritative_tasklist_clean` and `find_authoritative_root` routing do not apply.
  This is the core win.

Because `commands.py` operates on the in-memory `Project`, the ~3,556 lines of command
logic are largely untouched; the change concentrates in the serialize layer and the
load/save/context helpers.

### 4.4 Concurrency

- A short-lived store-level advisory lock (`flock` on
  `~/.tasktool-store/.tasktool.lock`) wraps only the stage+commit critical section. Two
  agents closing two different slices write disjoint row files and serialize only for the
  commit instant. This replaces today's project-level `.git/tasktool.lock`.
- Lock acquisition uses a bounded wait with a clear timeout error (no indefinite hang).

### 4.5 Atomicity with landed code

The "task done but code never landed" hazard is real once state is decoupled from the code
commit. Mitigations build on the **existing** lifecycle rather than moving it (anchor fields
already exist on `Slice`: `worktree_base_sha`, `landed_base_sha`, `model.py:120-121`):

- **P10 does not change the close/prune boundary.** Today `cmd_close` enforces landedness
  via `_apply_landed_gate`, marks done, saves, and commits (`commands.py:1286-1318`); the
  `landed_base_sha` value is stamped later, during `worktree prune`, after the
  branch-merged guard passes (`commands.py:3284-3293`). External-store mode keeps this exact
  split — close still runs `_apply_landed_gate`, prune still stamps `landed_base_sha`. The
  only change is that both writes land in the store, not in the worktree's `docs/tasklist.json`.
- **Reconciler** — a tasktool subcommand (final surface decided in S4: a new `doctor`
  command vs. an extension of the existing `validate`) flags drift:
  - rows `done` with a prune-stamped `landed_base_sha` that is not an ancestor of the
    authoritative branch HEAD (landed-then-rewound), **and** rows `done` but never
    pruned/stamped whose branch is not merged into HEAD (done-but-not-landed);
  - rows whose artifact refs point at a path that does not exist at the authoritative HEAD
    (rebased-away or never-committed artifact). Artifact refs remain `list[str]` paths
    today (`Slice.refs`/`Task.refs`, `model.py:88,104`); the pilot reconciler checks
    **path existence at HEAD**. Pinning each ref to a specific commit SHA (`{path, sha}`)
    is a deferred enhancement whose encoding S4 decides — it is **not** required for the
    pilot.
  - It is runnable standalone and from the pre-push hook / CI.

### 4.6 Bootstrap & offline degradation

- A fresh project clone carries only `.tasktool/config.json`. On first run, if the store
  repo or the project namespace is missing, tasktool guides the user:
  `tasktool store init` (create local) or `tasktool store clone <remote>`.
- If the store is unreachable: **read commands degrade with a clear message; write commands
  refuse cleanly** rather than corrupting or silently no-op'ing.
- `$TASKTOOL_STORE_ROOT` overrides the location for tests/CI and alternate machines.

### 4.7 New `store` subcommand group

`tasktool store {init, clone, migrate, path, status}`:

- `init` — create the global store git repo and the project namespace.
- `clone <remote>` — clone an existing store for this machine.
- `migrate` — see §5.
- `path` — print the resolved store path for the current project (diagnostics).
- `status` — show store cleanliness, current project namespace, last commit.

## 5. Migration & rollout

Opt-in; existing modes keep working unchanged.

`tasktool store migrate` (extends `tools/tasktool/migrate.py`) runs in this strict order;
the round-trip equality check gates the destructive step:

1. Read the project's existing `docs/tasklist.json` (schema v3, `model.py:7`) into a
   `Project` (the pre-migration baseline).
2. Write sharded rows + `archived/` + `ledger/` + `project.json` into
   `~/.tasktool-store/projects/<project_id>/` (nothing in the project repo is touched yet).
3. **Round-trip gate:** assemble a `Project` from the freshly-written store and assert it
   deep-equals the baseline from step 1. **If unequal, ABORT:** the project repo is still
   untouched (`docs/tasklist.json` intact and unstaged, config unchanged), and the
   half-written store namespace is discarded. Nothing is committed anywhere.
4. Only after the gate passes: flip `.tasktool/config.json` to
   `mutation_mode: external-store` with the `store` block, then `git rm docs/tasklist.json`,
   and commit the config change + removal together. The repo now carries **no** task state.
   (Reversible: `docs/tasklist.json` remains in git history; re-import is possible from any
   prior commit.)

**Pre-commit hook change (required, F4).** The generated hook currently *blocks* staged
deletion of `docs/tasklist.json` (`tools/tasktool/templates/pre-commit-tasktool:33-37`).
The migration commit in step 4 stages exactly that deletion, so the hook must be updated to
**allow** the deletion when `.tasktool/config.json` is in `external-store` mode (and
continue blocking it otherwise). Project-setup and any tooling that assumes a tracked
`docs/tasklist.json` must likewise tolerate its absence in this mode.

**Pilot order:** migrate multistore first; run it for a period; migrate superstar itself
only once the pilot is proven.

## 6. Suggested slice breakdown (for phase-planning / writing-plans)

This is phase-sized. A likely decomposition (final slicing is the planning step's job):

- **S1 — Config + mode plumbing.** Add `external-store` to `VALID_MUTATION_MODES`, parse the
  `store` block, store-path resolution (config + `$TASKTOOL_STORE_ROOT`), `tasktool store
  path/status/init`.
- **S2 — Sharded serialize layer.** Per-row read/glob assembly + dirty-diff atomic writes
  in `serialize.py`; round-trip tests against fixtures.
- **S3 — Load/save/context integration.** Wire `_load`/`_save`/`_write_context` for the new
  mode; store-level lock; remove worktree-cleanliness coupling in this mode.
- **S4 — Atomicity & reconciler.** Keep the existing close/prune `landed_base_sha` split;
  add the drift reconciler (decide `doctor` vs `validate` extension here); pre-push/CI
  wiring. Decide whether to introduce SHA-pinned artifact refs or stay path-existence-only.
- **S5 — Migration + pilot.** `tasktool store migrate` (round-trip gate before destructive
  `git rm`); pre-commit hook change to allow the `docs/tasklist.json` deletion in
  `external-store` mode; migrate multistore; project-setup tolerates absent
  `docs/tasklist.json`.

## 7. Acceptance criteria

Concrete, reviewer-checkable criteria (commands run from `tools/tasktool/`):

- **Regression for the reported bug:** an integration test where the project worktree has
  unrelated dirty/staged content (including a dirty `docs/` file) and a `tasktool close`
  on a row in `external-store` mode **succeeds** and produces a store commit that touches
  **only** that row's file. Run: `python -m pytest tools/tasktool/tests -k external_store`.
- **Concurrency (row closes):** a test launching two concurrent closes on two slices of the
  same phase produces two store commits, each touching exactly one disjoint row file, with
  no lost update. Assert both rows reach `done` and the store has two row-scoped commits.
- **Concurrency (project-level metadata):** a test running two operations that both touch
  project-level metadata — e.g. a phase archive (appends `archived/`, ladders `ledger/`,
  `commands.py:2730,2768-2779`) concurrently with a cross archive (appends `archived/`,
  `commands.py:855-862`) — produces disjoint per-entry files with **no lost update** in
  either `archived/` or `ledger/`, and the store lock serializes their commits.
- **Round-trip:** for a representative fixture tasklist, assembling `Project` from the
  sharded store (rows + `archived/` + `ledger/` + `project.json`) deep-equals the `Project`
  loaded from the original `docs/tasklist.json`.
- **Migration safety (ordering):** `store migrate` on a sample repo asserts store↔baseline
  round-trip equality **before** any project-repo change; an injected inequality makes
  migrate abort **before** the config flip and `git rm`, leaving `docs/tasklist.json` intact
  and unstaged and the config unchanged.
- **Migration safety (hook):** a migration integration test installs the generated
  pre-commit hook, runs a **real `git commit`** of the external-store config flip + staged
  `docs/tasklist.json` deletion, and asserts the commit **succeeds** (hook allows the
  deletion in `external-store` mode) — and that the same staged deletion is still **blocked**
  under the other modes.
- **Atomicity reconciler:** the reconciler (the S4-named `doctor` command or `validate`
  extension) exits non-zero and names the row when a `done` row's prune-stamped
  `landed_base_sha` is not an ancestor of the authoritative HEAD, or when a `done` row was
  never stamped and its branch is not merged into HEAD; it exits zero when all done rows are
  landed.
- **Offline:** with `$TASKTOOL_STORE_ROOT` pointed at a non-existent path, a read command
  prints the bootstrap guidance and a write command refuses with a non-zero exit and no
  partial write.
- **Backward compatibility:** the existing suite passes unchanged for `local` and
  `authoritative-checkout` projects: `python -m pytest tools/tasktool/tests`.

## 8. Risks & mitigations

| Risk | Mitigation |
| --- | --- |
| State decoupled from code commit (done-but-not-landed) | `landed_base_sha` on close + `tasktool doctor` reconciler (§4.5) |
| Store unavailable on a fresh clone / new machine | Bootstrap guidance; reads degrade, writes refuse cleanly (§4.6) |
| Concurrent commits to the store repo race on git index | Short store-level `flock` around stage+commit only (§4.4) |
| Artifact drift (row points at rebased-away `{path, SHA}`) | Reconciler flags missing/rebased artifact refs (§4.5) |
| Migration data loss | Round-trip deep-equal check gates the destructive `git rm` (§5) |
| Tooling assuming tracked `docs/tasklist.json` | Update pre-commit hook + project-setup to tolerate absence in this mode (§5) |

## 9. Open questions for planning

- Exact `tasktool doctor` invocation surface vs folding into `validate` — decide in S4.
- Whether `order` is stored per-row or derived from ID numbering — decide in S2 (default:
  explicit `order` field for stability across reorders).
- Cross-machine sync ergonomics (auto-pull/push vs manual) — out of scope for the pilot;
  `remote: null` local-only is sufficient to prove the model.
