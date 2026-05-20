# Coordinator handoff — X10 Verdict Parser & Prompt Hardening

You are the coordinator for implementing **X10** of the superstar fork at `/home/simon/Dev/sigreer/skills/superstar/.worktrees/x10-verdict-parser` (branch `x10-verdict-parser`).

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- tasktool entry: run `tasktool brief X10` (canonical tracker: `docs/tasklist.json`). X10 is a `cross_cutting` item, not a phase/slice — `tasktool schedule` / `ratify` / `ready-slices` do not apply.
- Spec: [`docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md`](../specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md)
- Plan: [`docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md`](../plans/2026-05-20-X10-verdict-parser-claude-formatting.md)
- Spec reviewer chain (ready at r5): `docs/reviewer/x10-verdict-parser-claude-formatting-design-spec/`
- Plan reviewer chain (ready at r2): `docs/reviewer/x10-verdict-parser-claude-formatting-plan/`
- Post-slice reviewer chain (will be created on first review): `docs/reviewer/2026-05-20-X10-verdict-parser-claude-formatting-X10-post-slice/`

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than the process of delegating to a subagent. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
- **At the end of the slice** (after Task 5), invoke `superstar:external-review` with `--kind post-slice --work-id X10`.
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until the verdict is `ready` or `ready with small edits`, or there is a genuine reason to escalate to the user.
- **No phase close required.** X10 is `cross_cutting`. After post-slice review passes, run `tasktool close X10` (no `--reviewer-chain` flag — that is phase/slice-only; see Task 6 in the plan).

## First action

Read this file (the handoff prompt), then run `tasktool brief X10`. Read the spec and the plan. Then invoke `superstar:subagent-driven-development` and begin with Task 1 of the plan.
