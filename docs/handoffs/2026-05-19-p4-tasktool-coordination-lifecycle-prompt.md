# Coordinator handoff — P4 Tasktool Coordination and Lifecycle Authority

You are the coordinator for implementing **P4** of Superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible, but respect the schedule: `P4.S2` depends on `P4.S1`.

## Inputs

- tasktool entry: run `tasktool brief P4` (canonical tracker: `docs/tasklist.json`).
- schedule: run `tasktool schedule P4` and `tasktool ready-slices P4` before dispatching work.
- Spec: [`docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md`](docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md)
- Plan: [`docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md`](docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md)
- Spec reviewer chain: `docs/reviewer/p4-tasktool-coordination-lifecycle-design-spec/` (verdict: `ready with small edits`, edits applied)
- Plan reviewer chain: `docs/reviewer/p4-tasktool-coordination-lifecycle-plan/` (verdict: `ready with small edits`, edits applied)

## Coordinator discipline

- Do not perform implementation fixes yourself unless the fix is genuinely cheaper than delegation. Tiebreak: delegate.
- Do not pollute coordinator context with broad file reads. Delegate investigations and receive concise summaries.
- Run implementation from an isolated worktree per the `superstar:using-git-worktrees` preflight.
- Execute `P4.S1` first. Do not start `P4.S2` until `P4.S1` passes post-slice external review and closes via `tasktool close P4.S1`.
- At the end of each slice, invoke `superstar:external-review` with `--kind post-slice` and the `--work-id` for that slice.
- Pass reviewer findings to fix subagents and iterate until verdict is `ready` or `ready with small edits`.
- At phase close, invoke `superstar:external-review` with `--kind post-phase`, then archive via `tasktool archive-phase P4`.

## First Action

Run:

```sh
tasktool brief P4
tasktool schedule P4
tasktool ready-slices P4
```

Then read the spec and plan, invoke `superstar:subagent-driven-development`, and begin with `P4.S1`.
