# Coordinator handoff — P7.S2 surface / reserve / coordinate CLI

You are the coordinator for implementing **P7.S2** of Superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- tasktool entry: run `tasktool brief P7.S2` (canonical tracker: `docs/tasklist.json`).
- Spec: [`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md`](../specs/2026-06-02-P7-integration-surface-parallel-safety-design.md) — see §4.B.
- Plan: [`docs/plans/2026-06-02-P7-S2-surface-reserve-coordinate-cli.md`](../plans/2026-06-02-P7-S2-surface-reserve-coordinate-cli.md)
- Plan reviewer chain (passed `ready with small edits`): `docs/reviewer/p7-s2-surface-reserve-coordinate-cli-plan/`
- Post-slice reviewer chain (created on first review): `docs/reviewer/p7-s2-surface-reserve-coordinate-cli-post-slice/`

## Slice-specific notes

- **Depends on P7.S1** — do not start until S1 (schema v3 fields) has landed. The plan's own stop-condition checks that `SCHEMA_VERSION == 3` and the new fields exist.
- **Parallel-safe with P7.S4** (disjoint surfaces: `cli`/`commands` vs `worktree`). They may run in separate worktrees concurrently.
- Load-bearing behaviour: `reserve add` HARD-REFUSES duplicate `resource:value` within scope; `--force` requires `--reason` and mutates only the reserving slice; ledger dedupe is keyed `resource:value:scope:owner_id`; cancelled slices never enter the ledger. The scope-comparison rule (collision computed over the holder set chosen by the NEW reservation's scope) is binding — keep it consistent with spec §4.B.
- Source of truth is `tools/tasktool/`; the `plugins/superstar/` copy is release-synced — edit only `tools/tasktool/`.

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless genuinely cheaper than delegating. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents.
- **At the end of the slice**, invoke `superstar:external-review` with `--kind post-slice`.
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until `ready` / `ready with small edits`.
- **Close the slice via `tasktool close P7.S2`** when reviewed; the CLI enforces the post-slice gate.

## First action

Read this file, then run `tasktool brief P7.S2`. Confirm P7.S1 is `done`. Read the spec (§4.B) and the plan. Verify an isolated worktree per `superstar:using-git-worktrees` (plan's first step is `tasktool start P7.S2`). Then invoke `superstar:subagent-driven-development` and execute task-by-task.
