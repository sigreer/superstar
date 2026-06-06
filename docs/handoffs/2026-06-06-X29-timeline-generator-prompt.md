# Coordinator handoff — X29 Visual Work-History Timeline Generator

You are the coordinator for implementing **X29** of superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- tasktool entry: run `tasktool brief X29` (canonical tracker: `docs/tasklist.json`).
- Spec: [`docs/specs/2026-06-06-X29-timeline-design.md`](../specs/2026-06-06-X29-timeline-design.md)
- Plan: [`docs/plans/2026-06-06-X29-timeline-generator.md`](../plans/2026-06-06-X29-timeline-generator.md)
- Plan reviewer chain (verdict `ready`, round 3): `docs/reviewer/x29-timeline-generator-plan/`
- Spec reviewer chain (verdict `ready with small edits`, applied): `docs/reviewer/x29-timeline-design-spec/`

## Work shape

X29 is a **cross-cutting row**, not a phase/slice — there is no `tasktool schedule`/`ready-slices` step and `--workflow-step` is not valid on it. The plan is 14 sequential TDD tasks creating `tools/timeline/` (extract → model → render → CLI, plus a run-once `backfill.py`) and one `pyproject.toml` line. First execution step: `tasktool set X29 --status in_progress`. Run from an isolated worktree per `superstar:using-git-worktrees`.

Hard constraints from the spec (binding on every subagent):
- Python 3 stdlib only; git via subprocess. No third-party deps.
- No skill, hook, CLAUDE.md, or tasktool-help reference to the tool — zero agent-context footprint.
- Output is a single self-contained HTML file (no external fetches).
- `timeline.py` is read-only; only `backfill.py --write` mutates (archive files only).

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than the process of delegating to a subagent. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
- **At the end of the work**, invoke `superstar:external-review` with `--kind post-slice --work-id X29` against the plan, with the spec as context.
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until the verdict is `ready` or `ready with small edits`, or there is a genuine reason to escalate to the user.
- **Close the row via `tasktool close X29`** when reviewed (closes and archives by default — intended). Per CLAUDE.md, ask the user about a version bump before any release scripts run.
- Acceptance includes two real-repo renders (this repo and `/home/simon/Dev/sigreer/multistore`) plus a `backfill.py` dry-run against multistore; the `--write` happens later in the multistore repo with the user reviewing.

## First action

Read this file (the handoff prompt), then run `tasktool brief X29`. Read the spec and the plan. Then invoke `superstar:subagent-driven-development` and begin with Task 1.
