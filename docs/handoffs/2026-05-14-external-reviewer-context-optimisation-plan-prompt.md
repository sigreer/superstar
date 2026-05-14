# Coordinator handoff — external-reviewer context optimisation

You are the coordinator for implementing the **external-reviewer context optimisation** work of `sigreer/skills/superstar` at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- Spec: [`docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md`](docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md)
- Plan: [`docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md`](docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md)
- Spec review chain: `docs/reviewer/external-reviewer-context-optimisation-spec-spec/` (verdict: ready with small edits, applied)
- Plan review chain: `docs/reviewer/external-reviewer-context-optimisation-plan-plan/` (verdict: ready at r3)
- Reviewer chain folders that will be created during implementation:
  - Per slice: `docs/reviewer/external-reviewer-context-optimisation-plan-S{1,2,3}-post-slice/`
  - Phase close: `docs/reviewer/external-reviewer-context-optimisation-plan-post-phase/`

This repo has no `docs/TASKLIST.md`. Slice IDs come from the plan: **S1** (Failure-truth + echo containment), **S2** (Incremental prompt diet), **S3** (Docs).

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than the process of delegating to a subagent. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
- **At the end of each slice**, invoke `superstar:external-review` with `--kind post-slice`. Use `--review-depth thorough` for S1 (high-risk: correctness changes to chain semantics). Standard for S2/S3.
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until the verdict is `ready` or `ready with small edits`.
- **At the end of the phase** (after S3 closes), invoke `superstar:external-review` with `--kind post-phase --review-depth thorough`.
- **Update plan task checkboxes (`- [ ]` → `- [x]`)** as slices close. There is no TASKLIST.md to update in this repo.

## Pre-flight (read these first)

- Spec: §1 problem summary, §S1.7 multi-reviewer truth table, §S1.8 process-failed gate bypass, §6 acceptance gate.
- Plan: "Files at a glance," "Conventions used throughout the plan," "Spec → Plan mapping for the test items."

The plan is structured TDD-first: every task writes a failing test, then minimal implementation, then commit. Subagents must follow this discipline.

## First action

Invoke `superstar:subagent-driven-development` and begin Slice 1 with Task 1.1.
