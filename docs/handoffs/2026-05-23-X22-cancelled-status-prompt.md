# Coordinator handoff — X22 Add `cancelled` terminal status to tasktool

You are the coordinator for implementing **X22** of `superstar` at `/home/simon/Dev/sigreer/skills/superstar`.

X22 is a **cross-cutting** item, not a phase or slice. There is no post-phase review gate; the post-slice review gate also does not apply (cross-cutting items close via `tasktool close <x-id>` without a reviewer-chain check). However, the changes touch lifecycle-critical code (status enum, validation, dependency resolution, archive paths), so internal reviews between tasks and a full test sweep at the end are strongly recommended.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill, dispatching one subagent per task in the plan. Most tasks are sequential (later tasks depend on the enum, helper, and CLI verb landing first); a few late tasks (skill-prose update Task 15, version bump Task 16) can be parallelized.

## Inputs

- tasktool entry: run `tools/tasktool/tasktool brief X22` (canonical tracker: `docs/tasklist.json`).
- Spec: [`docs/specs/2026-05-23-X22-cancelled-status-design.md`](../specs/2026-05-23-X22-cancelled-status-design.md)
- Plan: [`docs/plans/2026-05-23-X22-cancelled-status.md`](../plans/2026-05-23-X22-cancelled-status.md)
- Spec reviewer chain (closed): `docs/reviewer/x22-cancelled-status-design-spec/`
- Plan reviewer chain (closed): `docs/reviewer/x22-cancelled-status-plan/`

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than the process of delegating to a subagent. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
- **Per-task internal review.** After each task's subagent reports success, dispatch a second subagent to verify the diff matches the plan task and the new tests pass. Use `superstar:requesting-internal-review` if helpful.
- **No post-slice external review applies** (X22 is cross-cutting). The spec's gating concerns are about the *runtime* gates that the new code introduces, not about gating this implementation itself.
- **Close X22 via `tools/tasktool/tasktool close X22 --note "cancelled status shipped"`** when all 16 tasks are done and the verification block at the end of the plan passes. Cross-cutting close auto-archives by default; no `--no-archive` is needed.
- **Version bump (Task 16.3).** Per `CLAUDE.md`, ship-affecting changes (skills, tools) prompt a version-bump question. Surface the question to the human partner before committing the final state.

## First action

Read this file (the handoff prompt), then:

1. `tools/tasktool/tasktool brief X22` — confirm status, refs, and the spec/plan/reviewer chains.
2. Read the spec and plan in full.
3. Invoke `superstar:subagent-driven-development` and begin with Pre-flight (Steps 0a–0c), then Task 1.

The plan is bite-sized (16 tasks, TDD-shaped, each with explicit commits). Stick to the task order — Tasks 2–6 establish the substrate (enum, schema, validation, render, importer, notify) that Tasks 7–13 build on. Task 14 (brief/show reason surfacing) is independent of the lifecycle work and could run in parallel with Task 9 if you want to fan out, but keeping it serial is fine.
