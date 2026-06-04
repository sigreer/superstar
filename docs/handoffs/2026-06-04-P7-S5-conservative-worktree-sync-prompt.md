# Coordinator handoff — P7.S5 Conservative worktree sync

You are the coordinator for implementing **P7.S5** of Superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- tasktool entry: run `tasktool brief P7.S5` (canonical tracker: `docs/tasklist.json`).
- schedule: run `tasktool schedule P7` and `tasktool ready-slices P7` before dispatching work.
- Spec: [`docs/specs/2026-06-04-P7-S5-conservative-worktree-sync-design.md`](docs/specs/2026-06-04-P7-S5-conservative-worktree-sync-design.md)
- Plan: [`docs/plans/2026-06-04-P7-S5-conservative-worktree-sync.md`](docs/plans/2026-06-04-P7-S5-conservative-worktree-sync.md)
- Spec reviewer chain: `docs/reviewer/p7-s5-conservative-worktree-sync-design-spec/`
- Plan reviewer chain: `docs/reviewer/p7-s5-conservative-worktree-sync-plan/`
- Post-slice reviewer chain folder (created during closeout): `docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice/`

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than the process of delegating to a subagent. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
- **Start the slice first** with `tasktool start P7.S5`, then work from the printed implementation worktree.
- **At the end of the slice**, invoke `superstar:external-review` with `--kind post-slice`.
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until the verdict is `ready` or `ready with small edits`, or there is a genuine reason to escalate to the user.
- **Close the slice via `tasktool close P7.S5`** when the slice is reviewed; the CLI enforces the post-slice external-review gate.

## Current planning state

- `P7.S5` is ratified with `depends_on: P7.S4`, `workflow_step: implement`, and integration surface `worktree`.
- The spec review passed as `ready with small edits` in `docs/reviewer/p7-s5-conservative-worktree-sync-design-spec/`.
- The plan review initially returned `revise`; round 2 passed as `ready` in `docs/reviewer/p7-s5-conservative-worktree-sync-plan/`.
- The authoritative checkout had unrelated staged P7.S6 planning artifacts when this handoff was written. Preserve unrelated staged files and do not include them in P7.S5 commits.

## First action

Read this file, then run:

```sh
tasktool brief P7.S5
tasktool schedule P7
tasktool ready-slices P7
```

Read the spec and the plan. Then invoke `superstar:subagent-driven-development` and begin with Task 1 in the plan.
