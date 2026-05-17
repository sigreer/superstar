# Project Task List

Top-level task tracker for **superstar (personal fork)**. This document is the canonical overview. Per-phase, per-slice, and per-task details live in the linked plans. Completed phases live in [`docs/archived-tasks/`](archived-tasks/).

**Last reviewed:** 2026-05-17.

> **Transitional note.** This file is the canonical tracker today. Once `P2` (tasktool) ships, this file is imported into `docs/tasklist.json` and removed; per-slice progress is then tracked via the `tasktool` CLI. Pre-existing work (the external-reviewer phases) has been retroactively assigned `P1` to keep IDs collision-free; that phase is already closed and is referenced here only for ID-allocation purposes.

---

## Numbering & status discipline

See [`superstar:tasklist-discipline`](https://github.com/sigreer/superstar/tree/main/skills/tasklist-discipline) for the full rules. Summary:

**ID scheme.** Stable IDs, never renumbered. Short form within nested context; fully-qualified for cross-scope references.

| Scope           | Short form (in headers) | Fully-qualified (in references) |
|-----------------|--------------------------|---------------------------------|
| Phase           | `P2`                     | `P2`                            |
| Slice           | `S1`                     | `P2.S1`                         |
| Follow-up slice | `S5a`                    | `P2.S5a`                        |
| Task            | `T3`                     | `P2.S5.T3`                      |
| Cross-cutting   | `X4`                     | `P2.X4`                         |

**Status.**

| Emoji | Tag                  | Meaning                  |
|-------|----------------------|--------------------------|
| ✅    | `DONE YYYY-MM-DD`    | Complete                 |
| 🚧    | `IN PROGRESS`        | Active work              |
| ⏸    | `BLOCKED on …`       | Waiting on a dependency  |
| ☐    | `READY` / `TODO`     | Not started, unblocked   |

---

## North Star

Make superstar's workflow skills produce reliable, machine-readable artifacts so that downstream tools (AGS sidebar, reviewers, future dashboards) can consume project state without re-parsing brittle markdown. The first beachhead is the tasklist itself.

---

## P1 — External-reviewer work (historical) ✅ `DONE 2026-05-17`

Pre-existing phase, reconstructed from `docs/specs/`, `docs/plans/`, and `docs/reviewer/` to preserve ID continuity. Not actively tracked here; see existing artifacts for detail.

---

## P2 — tasktool: JSON-backed task management CLI 🚧 `IN PROGRESS`

Spec: [`docs/specs/2026-05-17-P2-tasktool-design.md`](specs/2026-05-17-P2-tasktool-design.md). Plan: _pending_.

- ☐ **S1** CLI core: data model, canonical serializer, allocation, validation, reviewer-gate, and the create/set/close/block/note/ref/title/show/list/validate/schema/next-id/init commands. Plan: [`docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md`](plans/2026-05-17-p2-s1-tasktool-cli-core.md).
- ☐ **S2** Importer, render, brief, archive-phase; migrate this repo from `TASKLIST.md` to `tasklist.json`. Plan: _pending — written after S1 ships._
- ☐ **S3** Rewrite `tasklist-discipline` skill; install pre-commit hook; touch up sibling skills (`writing-plans`, `external-review`, `project-setup`, `brainstorming`, `subagent-driven-development`). Plan: _pending — written after S2 ships._

---

## Cross-cutting (`X*`) — opportunistic, unscheduled

_None yet._

---

## How to use this map

- **Starting a new session?** Read this file first to orient. Drill into the linked plan only when you're working on a specific slice.
- **Finishing a slice?** Tick boxes (☐ → ✅), flip the slice header emoji + tag to `✅ DONE YYYY-MM-DD`, append post-impl notes inline. Don't renumber. Don't relocate within the live file.
- **Finishing a phase?** Run `external-review --kind post-phase` first. On `ready` / `ready with small edits`, move the entire phase section to `docs/archived-tasks/P{n}-<short-title>.md` and leave a one-line summary + archive link here.
- **Adding a new initiative?** Give it the next free ID, insert at the correct execution-order position, link the plan as soon as it exists.
