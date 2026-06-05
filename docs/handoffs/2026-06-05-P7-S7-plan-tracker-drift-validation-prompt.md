# Coordinator handoff — P7.S7 Plan ↔ tracker drift validation

You are the coordinator for implementing **P7.S7** of superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible. (This slice is small and sequential — Task 2 depends on Task 1's function, Task 3 on Task 2 — so expect mostly serial dispatch.)

## Inputs

- tasktool entry: run `tasktool brief P7.S7` (canonical tracker: `docs/tasklist.json`).
- schedule: P7.S7 has no parallel siblings; its deps (P7.S1, P7.S6) are `done`. Run `tasktool ready-slices P7` to confirm it is ready before dispatching.
- Spec: [`docs/specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md`](../specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md)
- Plan: [`docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md`](../plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md)
- Reviewer chain folders: spec chain already exists at `docs/reviewer/p7-s7-plan-tracker-drift-validation-design-spec/`; the plan chain is `docs/reviewer/p7-s7-plan-tracker-drift-validation-plan/`; the post-slice chain `docs/reviewer/p7-s7-plan-tracker-drift-validation-P7S7-post-slice/` will be created on first post-slice review.

## Isolation

Before editing any implementation file, ensure an isolated worktree exists for this slice via `superstar:using-git-worktrees` (the lifecycle start step is `tasktool start P7.S7`). Do not implement on a bare `main` checkout. Only `tools/tasktool/validate.py`, `tools/tasktool/commands.py`, and `tools/tasktool/tests/test_validate.py` are touched — do **not** hand-edit the `plugins/superstar/tools/tasktool/` mirror.

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than the process of delegating to a subagent. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
- **At the end of the slice**, invoke `superstar:external-review` with `--kind post-slice --work-id P7.S7`.
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until the verdict is `ready` or `ready with small edits`, or there is a genuine reason to escalate to the user.
- This is a single-slice tail of phase P7. After the slice closes, this is the **last active slice** of P7 (S8 is cancelled); run `superstar:external-review` with `--kind post-phase --work-id P7` and then archive.
- **Close the slice via `tasktool close P7.S7`** when reviewed; the CLI enforces the post-slice external-review gate. Archive the phase via `tasktool archive-phase P7` when all slices are terminal.

## First action

Read this file (the handoff prompt), then run `tasktool brief P7.S7`. Read the spec and the plan. Ensure the isolated worktree exists (`tasktool start P7.S7`). Then invoke `superstar:subagent-driven-development` and begin with Task 1.
