# Coordinator handoff — P7.S3 Scheduling overlap detection

You are the coordinator for implementing **P7.S3** of Superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- tasktool entry: run `tasktool brief P7.S3` (canonical tracker: `docs/tasklist.json`).
- schedule: run `tasktool schedule P7` and `tasktool ready-slices P7` before dispatching work, and `tasktool surface check P7` once this slice's own surface commands exist.
- Spec: [`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md`](../specs/2026-06-02-P7-integration-surface-parallel-safety-design.md) — section **§4.C** governs this slice.
- Plan: [`docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md`](../plans/2026-06-04-P7-S3-scheduling-overlap-detection.md)
- Reviewer chain folder (plan-review round already recorded here; post-slice rounds append): `docs/reviewer/p7-s3-scheduling-overlap-detection-plan/` (post-slice review opens a new chain `docs/reviewer/<...>-post-slice/`).

## Slice-specific notes

- **Deps `P7.S1, P7.S2` are both `done`.** S3 reads the `integration_surfaces` / `coordination_group` / `reservations` fields S1 added and the `surface`/`reserve`/`coordinate` commands S2 wired. No dependency-graph change is proposed; do not add a `parallel_group`.
- **Surfaces this slice writes:** `commands` (behavioural). It also adds a `surface check` subparser + ratify-warning print in `cli`. No reservations.
- **All additions are warning-only** — no new blocks. The five tasks are: (1) surface-relation helpers + `cmd_schedule` enrichment, (2) `cmd_ready_slices` enrichment, (3) `cmd_surface_check` + CLI wiring, (4) `cmd_ratify --parallel-group` warning, (5) full-suite verification + ratify + close.
- **Source of truth is `tools/tasktool/`** — never edit the `plugins/superstar/` copy (synced at release).

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than the process of delegating to a subagent. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
- **Integrate-current-main checkpoint** before the post-slice review: run `tasktool worktree status P7.S3 --integration`; if a sibling landed since `worktree_base_sha`, integrate base, regenerate derived artifacts, rerun verification, then review.
- **At the end of the slice**, invoke `superstar:external-review` with `--kind post-slice` (`--work-id P7.S3`).
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until the verdict is `ready` or `ready with small edits`.
- **Close the slice via `tasktool ratify P7.S3` then `tasktool close P7.S3`** when reviewed; the CLI enforces the post-slice external-review gate. (No version bump / plugin re-sync here — that happens at phase close per the repo release policy.)

## First action

Read this file (the handoff prompt), then run `tasktool brief P7.S3`. Read §4.C of the spec and the plan. Run `./tools/tasktool/tasktool start P7.S3` to create the isolated worktree and flip the slice to `in_progress`, `cd` into the printed path, and work there. Then invoke `superstar:subagent-driven-development` and begin with Task 1.
