# P3 — Phase Planning Workflow

**Status:** in implementation
**Date:** 2026-05-19
**TASKLIST entry:** `P3` in `docs/tasklist.json`

## Objective

Add a phase-planning layer to Superstar so agents can review project status, shape the next phase, record prospective slices, and make scheduling/dependency assumptions visible before slice specs and plans are written.

The durable boundary is:

- `docs/tasklist.json` stores machine-readable scheduling facts.
- This document records the phase rationale and bootstrap constraints.
- Slice specs/plans later ratify or update the graph through tasktool.

## Bootstrap Constraints

This phase is implementing its own workflow, so it must respect the existing tasktool rules before all new fields are available.

- The phase plan is registered as both `spec_path` and `planning_path` for `P3`.
- Do not stage unregistered dated files under `docs/specs/` or `docs/plans/`.
- If a planning draft lacks a task ID, keep it under `docs/_drafts/` or leave it unstaged.
- Existing unrelated dirty files are not part of P3 and must not be reverted or committed with this work.
- `blocked_on` remains runtime state only; planned scheduling uses `depends_on`.

## Target Behavior

Tasktool gains first-class phase scheduling fields:

- `Phase.planning_path`
- `Slice.depends_on`
- `Slice.planning_status`
- `Slice.parallel_group`

Tasktool also gains scheduling queries:

- `tasktool phase-status`
- `tasktool schedule <phase-id>`
- `tasktool ready-slices <phase-id>`
- `tasktool deps <slice-id> --add/--remove <dependency>`
- `tasktool ratify <slice-id>`

The new `phase-planning` skill uses those commands to support two workflows:

- Project status review after a phase closes.
- Phase shaping once the next body of work is conceptually agreed.

## Slices

### P3.S1 — Schema and validation foundation

Add the tasktool data model fields, JSON serialization, JSON schema output, validation, render/brief support, and backward-compatible loading for existing tasklist files.

Blocks: `P3.S2`, `P3.S3`.

### P3.S2 — Scheduling CLI

Add the command surface for dependency updates, scheduling output, ready-slice discovery, planning-path assignment, and project phase-status review.

Depends on: `P3.S1`.

### P3.S3 — Workflow skill and integration docs

Add the `phase-planning` skill and update `tasklist-discipline`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `using-superstar`, and README workflow references.

Depends on: `P3.S1`. Can proceed in parallel with `P3.S2` after command names are known.

### P3.S4 — Bootstrap migration and dogfood pass

Register this document as `planning_path`, run `tasktool schedule P3` and `tasktool ready-slices P3`, and make sure P3 itself models its intended dependency graph.

Depends on: `P3.S2`, `P3.S3`.

## Closeout Goals

- `tasktool validate --strict-format` passes.
- Tasktool unit and CLI integration tests pass.
- The new skill gives a clear status-review and phase-shaping workflow.
- P3’s own tasklist row records the phase plan and dependencies.
- The pre-commit hook still rejects orphan dated spec/plan files.
