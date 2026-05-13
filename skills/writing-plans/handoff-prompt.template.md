# Coordinator handoff — <PHASE-OR-SLICE-ID> <Short Title>

You are the coordinator for implementing **<PHASE-OR-SLICE-ID>** of <project-name> at `<absolute-repo-path>`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- TASKLIST entry: [`docs/TASKLIST.md`](docs/TASKLIST.md) — find <PHASE-OR-SLICE-ID>.
- Spec: [`<relative-path-to-spec>`](<relative-path-to-spec>)
- Plan: [`<relative-path-to-plan>`](<relative-path-to-plan>)
- Reviewer chain folder (will be created on first review): `docs/reviewer/<chain-folder>/`

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than the process of delegating to a subagent. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
- **At the end of each slice**, invoke `superstar:external-review` with `--kind post-slice`.
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until the verdict is `ready` or `ready with small edits`, or there is a genuine reason to escalate to the user.
- **At the end of the phase** (after the final slice closes), invoke `superstar:external-review` with `--kind post-phase`. Same delegation rule.
- **Update TASKLIST.md status in place** (☐ → ✅) when a slice closes. Archive the phase per `superstar:tasklist-discipline` when all slices are ✅.

## First action

Read this file (the handoff prompt), the TASKLIST entry, the spec, and the plan. Then invoke `superstar:subagent-driven-development` and begin the first slice.
