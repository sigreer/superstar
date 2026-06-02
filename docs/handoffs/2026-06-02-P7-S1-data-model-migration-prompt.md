# Coordinator handoff — P7.S1 Data Model + Migration (schema v3)

You are the coordinator for implementing **P7.S1** of Superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- tasktool entry: run `tasktool brief P7.S1` (canonical tracker: `docs/tasklist.json`).
- Spec: [`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md`](../specs/2026-06-02-P7-integration-surface-parallel-safety-design.md) — see §4.A.
- Plan: [`docs/plans/2026-06-02-P7-S1-data-model-migration.md`](../plans/2026-06-02-P7-S1-data-model-migration.md)
- Plan reviewer chain (passed `ready with small edits`): `docs/reviewer/p7-s1-data-model-migration-plan/`
- Post-slice reviewer chain (created on first review): `docs/reviewer/p7-s1-data-model-migration-post-slice/`

## Slice-specific notes

- **P7.S1 has no `depends_on` and blocks S2/S3/S4/S6/S7 — implement it first.** It is the schema-v3 data-model foundation.
- Source of truth is `tools/tasktool/`; the `plugins/superstar/tools/tasktool/` copy is synced by release scripts — edit only `tools/tasktool/`.
- The blocking ledger-drift-merge concern (Task 5a) is load-bearing: `reservations_ledger` must be union-merge, NOT scalar, in `migrate.py`, or a stale local checkout can erase authoritative archived reservations under authoritative-checkout mode. Do not let a subagent "simplify" it back to scalar.
- This phase ships user-facing tooling: at phase close (not this slice), ask the user about a version bump per CLAUDE.md before any release script runs.

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless genuinely cheaper than delegating. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents.
- **At the end of the slice**, invoke `superstar:external-review` with `--kind post-slice`.
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until the verdict is `ready` / `ready with small edits`.
- **Close the slice via `tasktool close P7.S1`** when reviewed; the CLI enforces the post-slice gate.

## First action

Read this file, then run `tasktool brief P7.S1`. Read the spec (§4.A) and the plan. Verify you are in an isolated worktree per `superstar:using-git-worktrees` (the plan's first step is `tasktool start P7.S1`). Then invoke `superstar:subagent-driven-development` and execute the plan task-by-task.
