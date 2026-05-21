---
name: tasklist-discipline
description: Use whenever planning, closing slices/phases, or referencing work items in a project that uses docs/tasklist.json. Teaches the tasktool CLI surface and the gating concepts; the CLI enforces the rules.
---

# TASKLIST Discipline

A `docs/tasklist.json` file is the canonical, top-level tracker for the project. It groups work into **phases**, **slices**, **tasks**, and **cross-cutting** items, each with a stable, never-renumbered ID. All mutations flow through `tasktool`; a pre-commit hook refuses non-canonical bytes, orphaned spec/plan filenames, and any commit that touches the legacy `docs/TASKLIST.md`.

Prefer the repo-local launcher `tools/tasktool/tasktool` when it exists; it works from a fresh clone without installing a global shim. The global `tasktool` command is an optional convenience installed by `bash tools/tasktool/install.sh`. If neither is available, use `PYTHONPATH=tools python3 -m tasktool`.

`.tasktool/config.json` must set `tasklist.mutation_mode` to `authoritative-checkout` for normal superstar work. Mutating commands route through the configured authoritative checkout instead of editing the local worktree's `docs/tasklist.json` directly. Treat that routing as the source of truth: run `tasktool` from the implementation worktree, let the tool acquire the shared lock and update the authoritative checkout, then continue from the same implementation worktree. If a mutating command reports that no authoritative-checkout routing is configured, stop and run `tasktool config init-authority --branch <main-branch>` from the authoritative checkout before retrying; use `tasktool config init-local` only for explicit local-only test fixtures or non-workflow throwaway repos.

**Announce at start:** "I'm using the tasklist-discipline skill to update docs/tasklist.json via tasktool."

## When to use

- About to plan or write a new spec → allocate an ID with `tasktool create phase|slice|task|cross …` **before** the spec file lands. The TASKLIST row is the allocation; the spec/plan/reviewer-chain filenames are downstream.
- About to start implementation for a slice → `tasktool start <slice-id>`. This records the lifecycle start and moves the row to `in_progress`; do this before dispatching implementation or editing implementation files.
- About to close a slice → `tasktool close <slice-id>`. The CLI enforces the post-slice external-review gate.
- About to close a phase → `tasktool archive-phase <phase-id>`. The CLI enforces the post-phase gate and writes the archive note.
- About to close a cross-cutting item → `tasktool close <x-id>`. The CLI marks it done and archives it by default. Use `--no-archive` only when the closed X-item must remain visible temporarily; later run `tasktool archive-cross <x-id>`.
- Entering a slice → `tasktool brief <slice-id>` instead of reading the JSON.
- Onboarding a project — `[[project-setup]]` runs `tasktool init` and installs the hook.

Onboarding has a hard setup boundary: after `[[project-setup]]` configures `.tasktool/config.json` with authoritative routing, creates or imports `docs/tasklist.json`, installs hooks, installs the global `external-reviewer` shim or replaces a legacy repo-local reviewer bridge with the compatibility shim, moves legacy `docs/superpowers/` files, or edits `CLAUDE.md` / `AGENTS.md`, that setup/migration must be committed, stashed, or explicitly paused before implementation work begins.

**Implementation isolation boundary:** If tasklist work is tied to starting, continuing, reviewing, or closing an implementation slice, invoke `[[using-git-worktrees]]` before tasktool status/ref/note/close mutations for an active implementation slice. `tasktool start`, `tasktool set`, `tasktool ref`, `tasktool note`, `tasktool close`, and reviewer-chain registration are not harmless bookkeeping when run from a shared checkout: they dirty the slice evidence set. A normal `main`/`master` checkout is planning/setup/read-only by default unless the user explicitly opts out of isolation in the current turn. Invoke `tasktool` from the active implementation worktree; authoritative routing sends the mutation to the configured checkout.

**Subagent rule (load-bearing).** Parents create or adopt worktrees via `tasktool start <slice-id>`. Dispatched subagents inherit the parent's cwd and **must not** call `tasktool start` — implementation work happens inside the parent's already-recorded worktree, and a subagent starting a slice double-counts the lifecycle row and corrupts the slice's worktree fields. Tasktool refuses `tasktool start` when it observes a dispatched-subagent signal (`SUPERSTAR_SUBAGENT_ROLE`, `CLAUDE_AGENT_ROLE`, or the test-only `SUPERSTAR_FORCE_SUBAGENT=1`). The runtime guard is detection-dependent — a coordinator that loses its env (e.g. `env -i`) will look like a top-level invocation — so **this prose rule is the load-bearing guard**; the env signals are belt-and-braces.

## Conceptual model

| Scope | Short form | Fully-qualified |
|-------|-----------|-----------------|
| Phase | `P2` | `P2` |
| Slice | `S1` (follow-up: `S5a`) | `P2.S1` (`P2.S5a`) |
| Task | `T3` | `P2.S5.T3` |
| Cross-cutting | `X4` | `X4` (top-level; not nested under a phase) |

IDs are assigned at birth and **never renumbered**. The `tasktool create` family does orphan-aware allocation (`max+1` across `docs/tasklist.json`, `docs/specs/`, `docs/plans/`, `docs/reviewer/`) and prints the new ID.
Archived X IDs are still reserved, so a new cross-cutting item will not reuse an ID that has moved to `archived_cross_cutting`.
Commands run against an archived X-id report a may-already-be-archived hint because archive files are evidence, not part of the active tasklist workflow surface.

Status enum: `ready | in_progress | blocked | done`. Only slices may take `blocked` (and only via `tasktool block <slice-id> --on …`). Emoji are a render concern; `tasktool render` and `tasktool brief` handle that. `tasktool start <slice-id>` is the normal way to enter `in_progress`; `tasktool set <id> --status in_progress` is a compatibility alias for older plans and ad-hoc rows. `tasktool unblock <slice-id> --resume` resumes through the same lifecycle path and stamps `started` when needed. `done` requires `closed`; the CLI stamps it.

Phase planning uses separate scheduling metadata. `planning_path` points at the phase-scoped planning/design document. `depends_on` records planned slice sequencing; it is not the same as runtime `blocked_on`. `planning_status` is `proposed | ratified | superseded`, and `parallel_group` names slices intended to be planned or executed together.

## Daily commands

```sh
tools/tasktool/tasktool brief <id>            # start-of-work primer for slice or phase
tools/tasktool/tasktool show <id>             # full detail
tools/tasktool/tasktool list --open           # everything ready / in_progress / blocked
tools/tasktool/tasktool create slice <phase-id> --title "…"
tools/tasktool/tasktool prepare existing <id> --plan path/to/plan.md
tools/tasktool/tasktool artifact add <id> --kind spec --path path/to/spec.md
tools/tasktool/tasktool artifact status <id> --strict
tools/tasktool/tasktool artifact commit <id> --message "…"
tools/tasktool/tasktool start <slice-id>      # lifecycle start + in_progress
tools/tasktool/tasktool set <id> --status in_progress  # compatibility alias
tools/tasktool/tasktool note <id> --append "…"
tools/tasktool/tasktool ref <id> --add path/to/artifact
tools/tasktool/tasktool block <slice-id> --on P2.S5
tools/tasktool/tasktool deps <slice-id> --add P2.S1
tools/tasktool/tasktool ratify <slice-id> --parallel-group bootstrap
tools/tasktool/tasktool schedule <phase-id>
tools/tasktool/tasktool ready-slices <phase-id>
tools/tasktool/tasktool phase-status
tools/tasktool/tasktool close <slice-id>      # enforces post-slice review gate
tools/tasktool/tasktool close <x-id>          # closes and archives cross-cutting by default
tools/tasktool/tasktool close <x-id> --no-archive
tools/tasktool/tasktool archive-cross <x-id>  # archive a done visible cross-cutting item
tools/tasktool/tasktool archive-phase <phase-id>  # enforces post-phase review gate
tools/tasktool/tasktool validate              # full validation
```

Run `tools/tasktool/tasktool --help` (or `tools/tasktool/tasktool <cmd> --help`) for the full surface.

## Gating concepts (why the CLI refuses you)

- **Post-slice external review.** `tasktool close <slice-id>` reads `chain.json` from the slice's reviewer chain folder (`docs/reviewer/<slug>-post-slice/` by default; override with `--reviewer-chain`). It refuses unless the latest round's verdict ∈ {`ready`, `ready with small edits`}. Per-task internal reviews do not satisfy this gate.
- **Post-phase external review.** `tasktool archive-phase <phase-id>` refuses until every slice is `done` *and* the phase's post-phase chain returns `ready` / `ready with small edits`.
- **Cross-cutting archive.** `tasktool close <x-id>` is ungated by external review and moves the completed X-item out of active `cross_cutting` into `archived_cross_cutting`, with a lossless markdown archive under `docs/archived-tasks/`. `--no-archive` leaves it visible as `done`; `tasktool archive-cross <x-id>` moves it later without sending another done notification.
- **`--skip-review-gate`** exists for emergencies and is recorded in the slice/phase `notes` with a timestamp. Use it only when the operator has explicitly chosen to bypass.

See `[[external-review]]` for how to drive the reviewer.

## Hand-edits are an emergency path, not a workflow

If a raw edit is genuinely needed:

```sh
TASKTOOL_RAW=1 $EDITOR docs/tasklist.json
tools/tasktool/tasktool validate --normalise
```

`--normalise` re-serialises the file through the canonical formatter so the pre-commit hook accepts it. There is no `tasktool edit --raw` subcommand by design — the friction keeps agents on the sanctioned commands.

## New work mid-slice

| Scenario | Action |
|----------|--------|
| Incidental fix in the same area | `tools/tasktool/tasktool create task <slice-id> --title …` |
| Real unit of work | `tools/tasktool/tasktool create slice <phase-id> --title …` (or `--follow-up <slice-id>` for a letter-suffix) |
| Bug surfaced by review | Inline task if cheap; follow-up slice if it deserves its own scope. |
| Cross-cutting, unscheduled | `tools/tasktool/tasktool create cross --title …` |

Creating a new slice or X-item is allocation/tracking only. It does not authorize implementing that work in the current slice worktree. If the discovery is truly incidental to the active slice, add an in-slice task and keep going. If it is real follow-up work, record it and defer until the current slice closes, or create a separate isolated worktree for that follow-up after the current slice boundary is clean.

## Referencing items in artifacts

- Specs, plans, reviewer chain folders: fully-qualified ID at first mention (`P9.S3a`), short form afterwards.
- Plan and spec filenames embed the ID: `YYYY-MM-DD-<id>-<slug>(-design).md`. The pre-commit hook rejects filenames whose ID has no `tasklist.json` row.
- Phase planning docs should be registered through `planning_path` once supported. During bootstrap or migration, either attach the document to `spec_path` for the phase ID or keep unregistered drafts outside orphan-checked paths such as `docs/_drafts/`.
- Commit messages may use either form; prefer fully-qualified for cross-phase commits.

## Workflow artifacts

Spec, plan, handoff, reviewer-chain, and archived-task paths are workflow artifacts. Register them through `tasktool artifact add` or `tasktool prepare`; do not hand-edit `docs/tasklist.json` refs for these paths. Use `tasktool artifact status <id> --strict` before handing work to another agent.

## Red flags

| Thought | Reality |
|---------|---------|
| "I'll just edit `docs/tasklist.json` by hand quickly." | The hook will refuse non-canonical bytes; `tasktool` is faster than fighting the hook. Use the CLI. |
| "I'll mark the slice `done` with `set` instead of `close` to skip the review gate." | `tasktool set --status done` routes through the same gate as `close`. The gate cannot be bypassed by reaching for a different subcommand. |
| "I'll commit the spec now and add the row after." | The pre-commit hook rejects orphan spec/plan filenames. Allocate first. |
| "`tasktool` says the verdict isn't ready, but the reviewer comments look fine." | Re-read the verdict line. `revise` is `revise`. If the reviewer chain is mis-parsed, fix the chain; do not pass `--skip-review-gate` casually. |
| "I'll bring back `docs/TASKLIST.md` for readability." | The hook refuses commits that touch it. Use `tasktool render` if you want markdown. |
| "I'll just renumber IDs to match execution order." | No. IDs are stable. Execution order lives in the array order; IDs preserve creation order. |
| "Setup files are just scaffolding; I'll leave them dirty while implementing." | No. Setup/migration artifacts make post-slice review scope ambiguous. Resolve the setup boundary first. |
| "I created a follow-up slice/X-item, so I can knock it out in this worktree." | No. Allocation is not implementation permission. Follow-up work gets deferred or gets its own isolated worktree. |
| "I only need to add refs or flip the row before creating the worktree." | No. For an active implementation slice, tasktool refs/status/notes are part of the slice artifact set. Isolate first. |
| "The slice is currently blocked, so I'll add `blocked_on` to model the phase plan." | No. Use `depends_on` for planned sequencing. Use `blocked_on` only for active runtime blockers. |

## Integration

- `[[writing-plans]]` — embeds slice IDs in plan filenames; calls `tools/tasktool/tasktool show <id>` for context.
- `[[brainstorming]]` — allocates IDs via `tools/tasktool/tasktool create` before writing the spec.
- `[[external-review]]` — passes `docs/tasklist.json` (or `tasktool render` output) as `--context`.
- `[[subagent-driven-development]]` — calls `tools/tasktool/tasktool close <slice-id>` at slice end and `tools/tasktool/tasktool archive-phase` at phase end.
- `[[project-setup]]` — runs `tasktool init` and `install.sh --hook`.
