---
name: phase-planning
description: Use after a phase closes or when shaping the next phase of work. Reviews project status, proposes next bodies of work, and records phase-level objectives, slices, dependencies, and parallelization assumptions.
---

# Phase Planning

Use this skill when the work is bigger than one slice but not yet ready for normal spec/plan writing.

**Announce at start:** "I'm using the phase-planning skill to shape the next phase and scheduling graph."

## Modes

### Project Status Review

Use when the human partner asks what should come next.

1. Run `tasktool phase-status`.
2. Inspect recent archived phase notes, open cross-cutting items, and recent reviewer artifacts when they are relevant.
3. Identify cross-cutters that should be handled before a new phase.
4. Recommend 1-3 next bodies of work with sequencing rationale.
5. Offer a follow-on prompt another agent can use to start phase shaping or brainstorming.

Keep this advisory. Do not create tasktool rows unless the human partner chooses a direction.

### Phase Shaping

Use when the human partner has conceptually agreed a phase.

1. Create or confirm a phase row via `tasktool create phase`.
2. Write one phase-scoped planning document. Prefer `docs/specs/YYYY-MM-DD-<phase-id>-<slug>-design.md` for bootstrap compatibility, then set `planning_path` with `tasktool planning-path <phase-id> --set <path>`.
3. Register prospective slices with `tasktool create slice <phase-id> --title ...`.
4. Record planned dependencies with `tasktool deps <slice-id> --add <dependency-slice-id>`.
5. Record intended planning/execution lanes with `tasktool ratify <slice-id> --status proposed --parallel-group <group>`.
6. Declare each slice's write surfaces and scarce reservations: `tasktool surface add <slice-id> <surface>...` and `tasktool reserve add <slice-id> <resource>:<value> [--scope phase|project]`. **Before ratifying any `parallel_group`, run `tasktool surface check <phase-id>`** and resolve every unguarded surface overlap — add a `depends_on` to serialize, or a `coordination_group` to coordinate. A `parallel_group` must not contain slices that share an integration surface without one of those links.
7. Run `tasktool schedule <phase-id>` and include the output or a concise summary in the phase planning document.

The document must include:
- phase objectives and closeout goals;
- prospective slices and acceptance intent;
- dependency assumptions and likely blockers;
- parallel planning/execution opportunities;
- explicit notes on which dependencies must be ratified by slice spec/plan writers.
- a **surface/reservation table**: one row per prospective slice listing its `integration_surfaces`, `reservations` (`resource:value` + scope), and `coordination_group`.

## Worktree And Hook Hygiene

`docs/tasklist.json` is canonical and the pre-commit hook rejects orphan dated spec/plan filenames. If a planning document pollutes the worktree before tasktool can reference it:

- If it has a phase ID, register that ID first and attach the file as `spec_path` or `planning_path`.
- If it has no registered ID, keep it outside orphan-checked paths such as `docs/_drafts/`.
- Do not stage unregistered dated files under `docs/specs/` or `docs/plans/`.
- Do not close a slice or phase while unrelated dirty files make review scope ambiguous.

## Ratification Contract

Phase shaping records best-known scheduling. Slice spec and plan writers must ratify it later:

- If the slice remains independent, run `tasktool ratify <slice-id>`.
- If it depends on another slice, update `depends_on` with `tasktool deps` before plan review.
- If it is superseded, run `tasktool ratify <slice-id> --status superseded` and explain the replacement in the phase planning document or slice notes.

## Red Flags

| Thought | Reality |
|---------|---------|
| "I'll just put dependency notes in the phase doc." | Tools cannot schedule prose. Put durable dependencies in `depends_on`. |
| "This slice is not ready yet, so mark it blocked." | Planned sequencing is `depends_on`; runtime interruption is `blocked_on`. |
| "The phase plan can live as an untracked draft in `docs/specs/`." | Dated spec/plan filenames are hook-checked. Register the ID or keep drafts elsewhere. |
| "The first sketch is final." | Phase shaping is provisional. Slice plans ratify or update the graph. |
| "These slices are in different features, so I'll `parallel_group` them." | Parallel groups are about shared **write surface**, not feature boundaries. Declare `integration_surfaces` and run `tasktool surface check <phase-id>` before ratifying a parallel group. |
