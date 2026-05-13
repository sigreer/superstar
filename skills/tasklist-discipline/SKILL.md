---
name: tasklist-discipline
description: Use whenever planning, closing slices/phases, or referencing work items in a project that has docs/TASKLIST.md. Encodes the stable-ID scheme (P/S/T/X), status emoji set, close-in-place rule, and phase-archive convention.
---

# TASKLIST Discipline

A `docs/TASKLIST.md` file is the canonical, top-level tracker for the project. It groups work into **phases**, **slices**, **tasks**, and **cross-cutting** items, each with a stable, never-renumbered ID. This skill encodes the rules for adding, closing, and archiving work against that file.

**Announce at start:** "I'm using the tasklist-discipline skill to update TASKLIST.md."

## When to use

- About to plan or write a new spec → confirm an ID exists for the work; if not, allocate one.
- About to close a slice → flip status in place per the rules below.
- About to close a phase → archive per the rules below.
- Referencing work in a spec, plan, reviewer chain folder, or commit — use the canonical IDs.
- Onboarding a project — `[[project-setup]]` will offer to scaffold TASKLIST.md if missing.

## ID scheme

Every unit of work has a stable identifier. Within a nested context, the short form is sufficient — fully-qualified IDs are used only for cross-scope references.

| Scope            | Short form (in headers/labels) | Fully-qualified (in references) |
|------------------|--------------------------------|---------------------------------|
| Phase            | `P2`                           | `P2`                            |
| Slice            | `S1`                           | `P2.S1`                         |
| Follow-up slice  | `S5a`                          | `P2.S5a`                        |
| Task             | `T3`                           | `P2.S5.T3`                      |
| Cross-cutting    | `X4`                           | `P2.X4` (or just `X4` if global)|

**Stability.** IDs are assigned at birth and **never renumbered**. New slices get the next free integer; follow-ups get the next free letter under their parent. Sections are arranged in **execution order**; IDs preserve **creation order**. If they diverge, that's expected — that's the whole point of stable IDs.

## Status set

Every slice and task carries a glanceable emoji + a status tag.

| Emoji | Tag                  | Meaning                       |
|-------|----------------------|-------------------------------|
| ✅    | `DONE YYYY-MM-DD`    | Complete                      |
| 🚧    | `IN PROGRESS`        | Active work                   |
| ⏸    | `BLOCKED on …`       | Waiting on a dependency       |
| ☐    | `READY` / `TODO`     | Not started, unblocked        |

## Closing a slice

1. Tick the checkboxes inside the slice (☐ → ✅).
2. Flip the slice header to `✅ DONE YYYY-MM-DD`.
3. Append post-impl notes inline under the slice (spec/plan links, reviewer chain link, commit SHAs, verification evidence).
4. **Do not move the section** to a "completed" graveyard within the live file. Its execution-order position is the timeline up until the phase closes.

## Closing a phase (archival)

When **every** slice in a phase is ✅:

1. Move the entire phase section to `docs/archived-tasks/P{n}-<short-title>.md`.
2. Replace the phase here with a one-line summary that links to the archive file.
3. Capture the phase's full verification run (wall-clock, any waivers) inline in the archive note.
4. Cross-cutting items that complete may be archived the same way (`docs/archived-tasks/X-<short-title>.md`) or left ✅ in the cross-cutting list — operator's call based on whether the context still has signal.

A phase archive should be preceded by a `post-phase` review via `[[external-review]]`. Do not archive on a `revise` verdict.

## New work mid-slice

| Scenario                        | Action                                                                              |
|---------------------------------|-------------------------------------------------------------------------------------|
| Incidental fix in the same area | `Inline follow-on` task under the parent slice.                                     |
| Real unit of work               | New slice with its own ID — letter suffix if it hangs off a parent, integer if standalone, `X{n}` if cross-cutting and unscheduled. |
| Bug surfaced by review          | `Inline follow-on` if cheap; new `S{n}a` follow-up slice if it deserves its own scope.|

## Referencing TASKLIST items

- In specs, plans, and reviewer chain folders, use the fully-qualified ID at first mention (`P9.S3a`) and the short form afterwards.
- Plan and spec filenames embed the ID: `YYYY-MM-DD-<id>-<slug>(-design).md`.
- Reviewer chain folders are keyed by target stem; they inherit the ID via the filename.
- Commit messages may use either form; prefer the fully-qualified form for cross-phase commits.

## Scaffolding TASKLIST.md

If a project does not yet have `docs/TASKLIST.md`, do not create one mid-flow. Defer to `[[project-setup]]` and ask the user to run "init project for superstar". The skill's template lives at `skills/tasklist-discipline/templates/TASKLIST.template.md`.

## Red flags

| Thought                                                       | Reality                                                                  |
|---------------------------------------------------------------|--------------------------------------------------------------------------|
| "I'll renumber to make execution order match the IDs"         | No. IDs are stable. Execution order is positional, IDs are creation order.|
| "This new bug is tiny, I'll just fix it without an ID"        | If it touches a slice that's already ✅, it needs a follow-up ID.        |
| "I'll move the closed slice to the bottom for cleanliness"    | Close in place. Move only at phase close, and only to the archive file.  |
| "I'll mark the phase ✅ before running post-phase review"     | Review first. `revise` blocks closure.                                   |
| "The status tag is fine without a date"                       | `DONE` requires `YYYY-MM-DD`. Future-you needs the timestamp.            |

## Integration

- `[[writing-plans]]` — embeds slice IDs in plan filenames; references TASKLIST entries.
- `[[brainstorming]]` — references TASKLIST when scoping new work.
- `[[external-review]]` — passes TASKLIST.md as `--context` for `spec` / `plan` / `post-slice` / `post-phase` reviews.
- `[[subagent-driven-development]]` — flips slice status on close; triggers phase-archive at phase end.
- `[[project-setup]]` — scaffolds TASKLIST.md from the template if missing.
