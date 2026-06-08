# Coordinator handoff — X29 Timeline day-axis iteration

You are the coordinator for implementing the **X29 day-axis iteration** of superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill, one implementer subagent per task (the 6 tasks are sequential — they all edit `tools/timeline/render.py`, so do not run two implementers in parallel).

## Context

X29 (`tools/timeline`, the visual work-history timeline generator) already shipped its original 14-task implementation; those commits live on the worktree branch. This iteration is **acceptance-driven**: the human visual-acceptance check surfaced two bugs and one redesign, captured in a new spec and plan. X29 remains `in_progress` and its close is still gated on human visual acceptance.

## Inputs

- tasktool entry: run `tasktool brief X29` (canonical tracker: `docs/tasklist.json`). X29 is a cross-cutting row, not a phase/slice — no `schedule`/`ready-slices`/`archive-phase`.
- Spec: [`docs/specs/2026-06-08-X29-timeline-day-axis-design.md`](docs/specs/2026-06-08-X29-timeline-day-axis-design.md) (extends base `docs/specs/2026-06-06-X29-timeline-design.md`). Spec review: `docs/reviewer/x29-timeline-day-axis-design-spec/` (r2 `ready with small edits`).
- Plan: [`docs/plans/2026-06-08-X29-timeline-day-axis.md`](docs/plans/2026-06-08-X29-timeline-day-axis.md) — 6 sequential TDD tasks. Plan review: `docs/reviewer/x29-timeline-day-axis-plan/` (r2 `ready`).
- Post-slice reviewer chain (created on first review): `docs/reviewer/x29-timeline-day-axis-X29-post-slice/`.

## Worktree (already exists — adopt, do not recreate)

```
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-x29-visual-work-history-timeline-generator
```

Branch `worktree-x29-visual-work-history-timeline-generator`. The spec and plan are committed on `main`. **First execution step (Plan Step 0.1): `tasktool start X29` (idempotent), then `cd` into the worktree and `git merge --no-edit main`** so the committed spec + plan land on the branch. Confirm the baseline suite is green (`python3 -m pytest tools/timeline/tests -q`, expect 77 passed) before dispatching Task 1.

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself.** Delegate every implementation and reviewer-driven fix to a subagent. Your context is for orchestration only.
- Fresh implementer subagent per task with `export SUPERSTAR_SUBAGENT_ROLE=implementer` first; paste the full task text from the plan; work dir = the worktree. Then a spec-compliance reviewer subagent, then a code-quality reviewer; fix→re-review loops until both pass. Tasks 1→6 are strictly sequential.
- **At slice close**, invoke `superstar:external-review` with `--kind post-slice --work-id X29` (file = the plan; context = the day-axis spec + `tasktool brief X29`). Run it **from the worktree** after committing the task work on the branch and merging current `main` (avoid the stale-tracker trap: tracker mutations route to the authoritative checkout, so integrate before reviewing). Reviewer-driven fixes go to fix subagents, never the coordinator. Iterate to `ready` / `ready with small edits`.
- **Flag the intended deviations** to the post-slice reviewer: the retired `quiet_gaps`/`_gap_bounds`/`GAP_THRESHOLD_HOURS` API and the base-spec tests that moved the date off card/node/ring faces (precedent: the prior T5/T6 review-driven deviations).

## Acceptance & close

- Task 6 is acceptance: full `python3 -m pytest -q` green, render this repo + `/home/simon/Dev/sigreer/multistore` (read-only; no `backfill --write`), then **ask the human partner to eyeball both HTML files in a browser**. That visual sign-off is the X29 close gate.
- After visual acceptance, record it in the post-slice resolution doc, then `tasktool close X29` (closes **and** archives — intended for a completed cross-cutting item).
- Per `CLAUDE.md`, ask the human partner about a version bump before running any release scripts (`scripts/publish-to-local-codex.sh` etc.). Docs/tracker changes don't need a bump; the `tools/` change does once it ships.

## First action

Read this file, run `tasktool brief X29`, read the spec and plan, then execute Plan Step 0 (start/adopt worktree + merge main + green baseline). Then invoke `superstar:subagent-driven-development` and dispatch the Task 1 implementer.
