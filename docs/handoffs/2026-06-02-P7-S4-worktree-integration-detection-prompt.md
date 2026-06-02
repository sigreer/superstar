# Coordinator handoff — P7.S4 Worktree Integration Detection

You are the coordinator for implementing **P7.S4** of Superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- tasktool entry: run `tasktool brief P7.S4` (canonical tracker: `docs/tasklist.json`).
- Spec: [`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md`](../specs/2026-06-02-P7-integration-surface-parallel-safety-design.md) — see §4.D.
- Plan: [`docs/plans/2026-06-02-P7-S4-worktree-integration-detection.md`](../plans/2026-06-02-P7-S4-worktree-integration-detection.md)
- Plan reviewer chain (passed `ready with small edits`): `docs/reviewer/p7-s4-worktree-integration-detection-plan/`
- Post-slice reviewer chain (created on first review): `docs/reviewer/p7-s4-worktree-integration-detection-post-slice/`

## Slice-specific notes

- **Depends on P7.S1** (model fields `worktree_base_sha`, `landed_base_sha`). Do not start until S1 has landed; this slice must not patch `model.py`/`serialize.py`/`migrate.py` — report any gap there as an S1 escape, don't fix it here.
- **Parallel-safe with P7.S2** (disjoint surfaces: `worktree` vs `cli`/`commands`).
- Load-bearing correctness: `landed_base_sha` is stamped ONLY on the guarded merged-branch prune of a `done` slice — never for cancelled / `--force`-unmerged / `--finalize`-only prunes. The `status --integration` ancestry fallback must use the half-open `worktree_base_sha..base-HEAD` window (a sibling merged BEFORE this worktree branched is NOT landed-since).
- Source of truth is `tools/tasktool/`; the `plugins/superstar/` copy is release-synced — edit only `tools/tasktool/`.

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless genuinely cheaper than delegating. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents.
- **At the end of the slice**, invoke `superstar:external-review` with `--kind post-slice`.
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until `ready` / `ready with small edits`.
- **Close the slice via `tasktool close P7.S4`** when reviewed; the CLI enforces the post-slice gate.

## First action

Read this file, then run `tasktool brief P7.S4`. Confirm P7.S1 is `done`. Read the spec (§4.D) and the plan. Verify an isolated worktree per `superstar:using-git-worktrees` (plan's first step is `tasktool start P7.S4`). Then invoke `superstar:subagent-driven-development` and execute task-by-task.
