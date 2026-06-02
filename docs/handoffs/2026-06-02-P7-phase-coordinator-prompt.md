# Coordinator handoff — P7 Integration-surface-aware parallel slice safety

You are the coordinator for implementing **phase P7** of Superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use `superstar:subagent-driven-development` with parallel agents where the schedule allows.

## What P7 builds (and why)

tasktool currently decides parallel-safety from declared *feature* dependencies (`depends_on`), not from the *write surface* a slice mutates. In the multistore P20 phase that let feature-independent slices co-write the same CMS registry / Directus schema / homepage sort-slot and conflict-bomb at merge. P7 adds **prevention** (declared integration surfaces + scarce-resource reservations, with overlap warnings and duplicate-reservation refusal) and **recovery** (worktree base/landed-SHA tracking + an integrate-current-main checkpoint + a registry merge playbook).

Governing spec: [`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md`](../specs/2026-06-02-P7-integration-surface-parallel-safety-design.md) (externally reviewed → `ready`).

## Inputs

- Canonical tracker: `docs/tasklist.json`. Run `tasktool brief P7`, then `tasktool schedule P7` and `tasktool ready-slices P7` before each dispatch.
- This is a personal fork: its own `tasktool` is the thing being extended. Source of truth is `tools/tasktool/`; the `plugins/superstar/tools/tasktool/` copy is synced by release scripts — edit only `tools/tasktool/`.

## Slice map & schedule

| Slice | Plan (reviewed → ready w/ small edits) | Status |
|-------|----------------------------------------|--------|
| **S1** Data model + migration (schema v3) | `docs/plans/2026-06-02-P7-S1-data-model-migration.md` | ratified, planned — **start here (no deps; blocks S2/S3/S4/S6/S7)** |
| **S2** surface/reserve/coordinate CLI | `docs/plans/2026-06-02-P7-S2-surface-reserve-coordinate-cli.md` | ratified, planned — deps S1; `parallel_group=core-after-model` with S4 |
| **S4** worktree base/landed-sha + status --integration | `docs/plans/2026-06-02-P7-S4-worktree-integration-detection.md` | ratified, planned — deps S1; `parallel_group=core-after-model` with S2 |
| **S8** reviewer-artifact collision investigation | `docs/plans/2026-06-02-P7-S8-reviewer-artifact-investigation.md` | ratified, planned — **no deps; runnable now in parallel with S1**; investigation-first (expected outcome: cancel, not close) |
| S3 scheduling overlap detection | — (plan just-in-time) | proposed — deps S1, S2 |
| S5 conservative `worktree sync` | — (plan just-in-time) | proposed — deps S4 (deferral candidate) |
| S6 skill changes + registry-merge-playbook | — (plan just-in-time) | proposed — deps S2, S3, S4 |
| S7 plan↔tracker drift validation | — (plan just-in-time) | proposed — deps S1, S6 |

Each planned slice has its own per-slice coordinator handoff under `docs/handoffs/2026-06-02-P7-S{1,2,4,8}-*-prompt.md`. **S3/S5/S6/S7 are intentionally unplanned** — their plans cite concrete command signatures/field names that only become real once S1–S4 land, so plan them just-in-time (`superstar:writing-plans`) when their dependencies are `done`.

## Execution order

1. **S1 and S8 are `ready` now** (run `tasktool ready-slices P7`). They share no integration surface (`model`/`serialize`/`migrate` vs `external-review`) → genuinely parallel; run each in its own worktree.
2. After S1 is `done`, **S2 and S4 become ready** (`core-after-model`) and are parallel-safe with each other (disjoint surfaces: `cli`/`commands` vs `worktree`).
3. Plan S3 once S2 is done; plan S6 once S2/S3/S4 are done; plan S5 once S4 is done; plan S7 once S6 is done.
4. **Dog-food the phase as it ships:** once S2/S3 exist, use `tasktool surface`/`reserve`/`surface check` on the remaining P7 slices; once S4 exists, use `tasktool worktree status --integration` before each post-slice review.

## Coordinator discipline (non-negotiable)

- **Do not perform fixes yourself** unless strictly cheaper than delegating. Tiebreak: delegate.
- **Do not pollute your context** — delegate investigations, reads, and edits to subagents.
- **At each slice close**, invoke `superstar:external-review --kind post-slice`; delegate reviewer-driven fixes to a fix subagent; iterate to `ready` / `ready with small edits`; then `tasktool close P7.S<n>` (S8 Branch B uses `tasktool cancel` instead — see its handoff).
- **At phase close**, invoke `superstar:external-review --kind post-phase`, then `tasktool archive-phase P7`, then `superstar:finishing-a-development-branch`.
- **Version bump:** P7 ships user-facing tooling. Per `CLAUDE.md`, at phase close ask the user about a version bump before any release/sync script runs.

## First action

Read this file, then `tasktool brief P7` and `tasktool ready-slices P7`. Read the spec. Invoke `superstar:using-git-worktrees` then `superstar:subagent-driven-development`, and begin S1 and S8 (each in its own isolated worktree).
