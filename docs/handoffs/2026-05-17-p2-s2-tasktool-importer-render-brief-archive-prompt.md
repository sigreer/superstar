# Coordinator handoff — P2.S2 tasktool importer / render / brief / archive-phase

You are the coordinator for implementing **P2.S2** of superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- TASKLIST entry: [`docs/TASKLIST.md`](docs/TASKLIST.md) — find P2.S2.
- Spec: [`docs/specs/2026-05-17-P2-tasktool-design.md`](docs/specs/2026-05-17-P2-tasktool-design.md)
- Plan: [`docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md`](docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md)
- Reviewer chain folder (will be created on first review): `docs/reviewer/p2-s2-tasktool-importer-render-brief-archive-P2-S2-post-slice/`

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than the process of delegating to a subagent. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
- **At the end of each slice**, invoke `superstar:external-review` with `--kind post-slice`.
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until the verdict is `ready` or `ready with small edits`, or there is a genuine reason to escalate to the user.
- **At the end of the phase** (after the final slice closes), invoke `superstar:external-review` with `--kind post-phase`. Same delegation rule.
- **Update TASKLIST.md status in place** (☐ → ✅) when a slice closes. Archive the phase per `superstar:tasklist-discipline` when all slices are ✅.

## First action

Read this file (the handoff prompt), the TASKLIST entry, the spec, and the plan. Then invoke `superstar:subagent-driven-development` and begin the first task in the plan (Task 1: importer phase-header parsing).
