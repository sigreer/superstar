# Project Task List

Top-level task tracker for **<project-name>**. This document is the canonical overview. Per-phase, per-slice, and per-task details live in the linked plans. Completed phases live in [`docs/archived-tasks/`](archived-tasks/).

**Last reviewed:** <YYYY-MM-DD>.

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

**Closing a slice.** Tick the boxes (☐ → ✅), flip the slice header to `✅ DONE YYYY-MM-DD`, append post-impl notes inline. Don't move closed slices within this file.

**Closing a phase.** When every slice is ✅, move the section to `docs/archived-tasks/P{n}-<short-title>.md` and leave a one-line link in its place here.

---

## North Star

<One short paragraph describing the project's overall direction. Replace this section with project-specific intent.>

---

## P1 — <Phase 1 title> 🚧 `IN PROGRESS`

Spec: [`docs/specs/YYYY-MM-DD-p1-<slug>-design.md`](specs/YYYY-MM-DD-p1-<slug>-design.md). Plan: [`docs/plans/YYYY-MM-DD-p1-<slug>.md`](plans/YYYY-MM-DD-p1-<slug>.md).

- ☐ **S1** <Slice 1 title>. Plan: [`docs/plans/YYYY-MM-DD-p1-s1-<slug>.md`](plans/YYYY-MM-DD-p1-s1-<slug>.md).
- ☐ **S2** <Slice 2 title>. Plan: [`docs/plans/YYYY-MM-DD-p1-s2-<slug>.md`](plans/YYYY-MM-DD-p1-s2-<slug>.md).

---

## Cross-cutting (`X*`) — opportunistic, unscheduled

These items have no fixed slot in the slice progression. They get pulled into a slice (or stand up as their own slice) when there's a reason to do them. Promotion to a slice keeps the original `X` ID in the changelog note.

- ☐ **X1** <Cross-cutting item title>.

---

## How to use this map

- **Starting a new session?** Read this file first to orient. Drill into the linked plan only when you're working on a specific slice.
- **Finishing a slice?** Tick boxes (☐ → ✅), flip the slice header emoji + tag to `✅ DONE YYYY-MM-DD`, append post-impl notes inline. Don't renumber. Don't relocate within the live file.
- **Finishing a phase?** Run `external-review --kind post-phase` first. On `ready` / `ready with small edits`, move the entire phase section to `docs/archived-tasks/P{n}-<short-title>.md` and leave a one-line summary + archive link here.
- **Adding a new initiative?** Give it the next free ID, insert at the correct execution-order position, link the plan as soon as it exists.
