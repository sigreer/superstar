---
name: tasklist-discipline
description: Use whenever planning, closing slices/phases, or referencing work items in a project that uses docs/tasklist.json. Teaches the tasktool CLI surface and the gating concepts; the CLI enforces the rules.
---

# TASKLIST Discipline

A `docs/tasklist.json` file is the canonical, top-level tracker for the project. It groups work into **phases**, **slices**, **tasks**, and **cross-cutting** items, each with a stable, never-renumbered ID. All mutations flow through `tasktool`; a pre-commit hook refuses non-canonical bytes, orphaned spec/plan filenames, and any commit that touches the legacy `docs/TASKLIST.md`.

**Announce at start:** "I'm using the tasklist-discipline skill to update docs/tasklist.json via tasktool."

## When to use

- About to plan or write a new spec → allocate an ID with `tasktool create phase|slice|task|cross …` **before** the spec file lands. The TASKLIST row is the allocation; the spec/plan/reviewer-chain filenames are downstream.
- About to close a slice → `tasktool close <slice-id>`. The CLI enforces the post-slice external-review gate.
- About to close a phase → `tasktool archive-phase <phase-id>`. The CLI enforces the post-phase gate and writes the archive note.
- Entering a slice → `tasktool brief <slice-id>` instead of reading the JSON.
- Onboarding a project — `[[project-setup]]` runs `tasktool init` and installs the hook.

## Conceptual model

| Scope | Short form | Fully-qualified |
|-------|-----------|-----------------|
| Phase | `P2` | `P2` |
| Slice | `S1` (follow-up: `S5a`) | `P2.S1` (`P2.S5a`) |
| Task | `T3` | `P2.S5.T3` |
| Cross-cutting | `X4` | `X4` (top-level; not nested under a phase) |

IDs are assigned at birth and **never renumbered**. The `tasktool create` family does orphan-aware allocation (`max+1` across `docs/tasklist.json`, `docs/specs/`, `docs/plans/`, `docs/reviewer/`) and prints the new ID.

Status enum: `ready | in_progress | blocked | done`. Only slices may take `blocked` (and only via `tasktool block <slice-id> --on …`). Emoji are a render concern; `tasktool render` and `tasktool brief` handle that. `done` requires `closed`; the CLI stamps it.

## Daily commands

```sh
tasktool brief <id>            # start-of-work primer for slice or phase
tasktool show <id>             # full detail
tasktool list --open           # everything ready / in_progress / blocked
tasktool create slice <phase-id> --title "…"
tasktool set <id> --status in_progress
tasktool note <id> --append "…"
tasktool ref <id> --add path/to/artifact
tasktool block <slice-id> --on P2.S5
tasktool close <slice-id>      # enforces post-slice review gate
tasktool archive-phase <phase-id>  # enforces post-phase review gate
tasktool validate              # full validation
```

Run `tasktool --help` (or `tasktool <cmd> --help`) for the full surface.

## Gating concepts (why the CLI refuses you)

- **Post-slice external review.** `tasktool close <slice-id>` reads `chain.json` from the slice's reviewer chain folder (`docs/reviewer/<slug>-post-slice/` by default; override with `--reviewer-chain`). It refuses unless the latest round's verdict ∈ {`ready`, `ready with small edits`}. Per-task internal reviews do not satisfy this gate.
- **Post-phase external review.** `tasktool archive-phase <phase-id>` refuses until every slice is `done` *and* the phase's post-phase chain returns `ready` / `ready with small edits`.
- **`--skip-review-gate`** exists for emergencies and is recorded in the slice/phase `notes` with a timestamp. Use it only when the operator has explicitly chosen to bypass.

See `[[external-review]]` for how to drive the reviewer.

## Hand-edits are an emergency path, not a workflow

If a raw edit is genuinely needed:

```sh
TASKTOOL_RAW=1 $EDITOR docs/tasklist.json
tasktool validate --normalise
```

`--normalise` re-serialises the file through the canonical formatter so the pre-commit hook accepts it. There is no `tasktool edit --raw` subcommand by design — the friction keeps agents on the sanctioned commands.

## New work mid-slice

| Scenario | Action |
|----------|--------|
| Incidental fix in the same area | `tasktool create task <slice-id> --title …` |
| Real unit of work | `tasktool create slice <phase-id> --title …` (or `--follow-up <slice-id>` for a letter-suffix) |
| Bug surfaced by review | Inline task if cheap; follow-up slice if it deserves its own scope. |
| Cross-cutting, unscheduled | `tasktool create cross --title …` |

## Referencing items in artifacts

- Specs, plans, reviewer chain folders: fully-qualified ID at first mention (`P9.S3a`), short form afterwards.
- Plan and spec filenames embed the ID: `YYYY-MM-DD-<id>-<slug>(-design).md`. The pre-commit hook rejects filenames whose ID has no `tasklist.json` row.
- Commit messages may use either form; prefer fully-qualified for cross-phase commits.

## Red flags

| Thought | Reality |
|---------|---------|
| "I'll just edit `docs/tasklist.json` by hand quickly." | The hook will refuse non-canonical bytes; `tasktool` is faster than fighting the hook. Use the CLI. |
| "I'll mark the slice `done` with `set` instead of `close` to skip the review gate." | `tasktool set --status done` routes through the same gate as `close`. The gate cannot be bypassed by reaching for a different subcommand. |
| "I'll commit the spec now and add the row after." | The pre-commit hook rejects orphan spec/plan filenames. Allocate first. |
| "`tasktool` says the verdict isn't ready, but the reviewer comments look fine." | Re-read the verdict line. `revise` is `revise`. If the reviewer chain is mis-parsed, fix the chain; do not pass `--skip-review-gate` casually. |
| "I'll bring back `docs/TASKLIST.md` for readability." | The hook refuses commits that touch it. Use `tasktool render` if you want markdown. |
| "I'll just renumber IDs to match execution order." | No. IDs are stable. Execution order lives in the array order; IDs preserve creation order. |

## Integration

- `[[writing-plans]]` — embeds slice IDs in plan filenames; calls `tasktool show <id>` for context.
- `[[brainstorming]]` — allocates IDs via `tasktool create` before writing the spec.
- `[[external-review]]` — passes `docs/tasklist.json` (or `tasktool render` output) as `--context`.
- `[[subagent-driven-development]]` — calls `tasktool close <slice-id>` at slice end and `tasktool archive-phase` at phase end.
- `[[project-setup]]` — runs `tasktool init` and `install.sh --hook`.
