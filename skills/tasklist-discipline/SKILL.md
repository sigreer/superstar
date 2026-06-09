---
name: tasklist-discipline
description: Use whenever planning, closing slices/phases, or referencing work items in a project that uses docs/tasklist.json. Teaches the tasktool CLI surface and the gating concepts; the CLI enforces the rules.
---

# TASKLIST Discipline

A `docs/tasklist.json` file is the canonical, top-level tracker for the project. It groups work into **phases**, **slices**, **tasks**, and **cross-cutting** items, each with a stable, never-renumbered ID. All mutations flow through `tasktool`; a pre-commit hook refuses non-canonical bytes, orphaned spec/plan filenames, and any commit that touches the legacy `docs/TASKLIST.md`.

Use the global `tasktool` shim installed by `bash <active-superstar-checkout>/tools/tasktool/install.sh`. If `tasktool` is missing or reports a shim/source version mismatch, reinstall that shim from the active Superstar checkout before continuing.

`.tasktool/config.json` must set `tasklist.mutation_mode` to `authoritative-checkout` for normal superstar work. Mutating commands route through the configured authoritative checkout instead of editing the local worktree's `docs/tasklist.json` directly. Treat that routing as the source of truth: run `tasktool` from the implementation worktree, let the tool acquire the shared lock and update the authoritative checkout, then continue from the same implementation worktree. If a mutating command reports that no authoritative-checkout routing is configured, stop and run `tasktool config init-authority --branch <main-branch>` from the authoritative checkout before retrying; use `tasktool config init-local` only for explicit local-only test fixtures or non-workflow throwaway repos.

**Announce at start:** "I'm using the tasklist-discipline skill to update docs/tasklist.json via tasktool."

## When to use

- About to plan or write a new spec → allocate an ID with `tasktool create phase|slice|task|cross …` **before** the spec file lands. The TASKLIST row is the allocation; the spec/plan/reviewer-chain filenames are downstream.
- About to start implementation for a slice → `tasktool start <slice-id>`. This records the lifecycle start and moves the row to `in_progress`; do this before dispatching implementation or editing implementation files.
- About to close a slice → `tasktool close <slice-id>`. The CLI enforces the post-slice external-review gate.
- About to close a phase → `tasktool archive-phase <phase-id>`. For `done` phases the CLI enforces the post-phase gate and writes the archive note; for `cancelled` phases it archives without a post-phase review because nothing shipped.
- About to close a cross-cutting item → `tasktool close <x-id>`. The CLI marks it done and archives it by default. Use `--no-archive` only when the closed X-item must remain visible temporarily; later run `tasktool archive-cross <x-id>`.
- Entering a slice → `tasktool brief <slice-id>` instead of reading the JSON.
- Onboarding a project — `[[project-setup]]` runs `tasktool init` and installs the hook.

Onboarding has a hard setup boundary: after `[[project-setup]]` configures `.tasktool/config.json` with authoritative routing, creates or imports `docs/tasklist.json`, installs hooks, installs the global `external-reviewer` shim or replaces a legacy repo-local reviewer bridge with the compatibility shim, moves legacy `docs/superpowers/` files, or edits `CLAUDE.md` / `AGENTS.md`, that setup/migration must be committed, stashed, or explicitly paused before implementation work begins.

**Implementation isolation boundary:** If tasklist work is tied to starting, continuing, reviewing, or closing an implementation slice, invoke `[[using-git-worktrees]]` before tasktool status/ref/note/close mutations for an active implementation slice. `tasktool start`, `tasktool set`, `tasktool ref`, `tasktool note`, `tasktool close`, and reviewer-chain registration are not harmless bookkeeping when run from a shared checkout: they dirty the slice evidence set. A normal `main`/`master` checkout is planning/setup/read-only by default unless the user explicitly opts out of isolation in the current turn. Invoke `tasktool` from the active implementation worktree; authoritative routing sends the mutation to the configured checkout.

**Shared tracker versus sibling artifacts.** `docs/tasklist.json` is the shared canonical tracker. Truthful sibling lifecycle rows are bookkeeping, not sibling implementation work, and P8.S1 close/prune commands auto-commit the lifecycle-authored tracker/archive files they write through scoped path commits. Do not stop merely because a sibling's close state is visible in the tracker. Sibling artifacts remain hands-off: implementation files, specs, plans, handoffs, reviewer chains, archived task files not authored by the current lifecycle command, setup/migration files, and any non-tracker files outside the current scope must not be committed or rewritten by the current slice. If co-staged sibling tracker state appears, inspect the path set and proceed only when the staged paths are tracker lifecycle bookkeeping; ask only when sibling artifacts or unrelated files are mixed in.

**Administrative closeout exception:** Pure lifecycle bookkeeping for already-superseded planning rows may run from the authoritative checkout without creating a new implementation worktree. Examples: `tasktool cancel <phase-id> --cascade --reason "…"`, `tasktool archive-phase <phase-id>` on that cancelled phase, or adding refs/notes that explain the cancellation. Do not use this exception to edit implementation files, close shipped slices, register reviewer evidence for active implementation work, or mix new product changes into the bookkeeping commit.

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

Status enum: `ready | in_progress | blocked | done | cancelled`. Only slices may take `blocked`. `cancelled` is a terminal status (peer of `done`) recording work that was intentionally not shipped — cancelled, deferred, abandoned, superseded. It is set only via `tasktool cancel <id> --reason "…"`; the `set` verb does not accept it. Tasks cannot be `cancelled`; cancel the parent slice instead.

`blocked` is only set via `tasktool block <slice-id> --on …`. Emoji are a render concern; `tasktool render` and `tasktool brief` handle that. `tasktool start <slice-id>` is the normal way to enter `in_progress`; `tasktool set <id> --status in_progress` is a compatibility alias for older plans and ad-hoc rows. `tasktool unblock <slice-id> --resume` resumes through the same lifecycle path and stamps `started` when needed. `done` requires `closed`; the CLI stamps it.

Phase planning uses separate scheduling metadata. `planning_path` points at the phase-scoped planning/design document. `depends_on` records planned slice sequencing; it is not the same as runtime `blocked_on`. `planning_status` is `proposed | ratified | superseded`, and `parallel_group` names slices intended to be planned or executed together.

Integration-surface metadata models **parallel-execution safety by write surface**, not by feature intent. `integration_surfaces` is a list of conventional tags naming the shared write areas a slice mutates (recommended vocabulary: `cms-block-registry`, `directus-schema`, `page-renderer-dispatch`, `theme-tail-css`, `content-contract-types`, `reviewer-artifacts` — extend per project). `reservations` are scarce-allocation claims on a single value (`homepage-sort:15`, `route-slug:/offers`, `block-kind:slider`), each scoped `phase` (default) or `project`; `tasktool reserve add` **refuses a duplicate allocation** within scope. `coordination_group` names a set of slices that *intentionally* share a surface and agree to coordinate — serialize reviews, designate an integration owner, run the centralized-registry merge playbook. It is the opposite of `parallel_group`, which asserts the slices are independent: a shared surface needs a `coordination_group` or a `depends_on`, never a `parallel_group`.

## Daily commands

```sh
tasktool brief <id>            # start-of-work primer for slice or phase
tasktool show <id>             # full detail
tasktool list --open           # everything ready / in_progress / blocked
tasktool create slice <phase-id> --title "..."
tasktool prepare existing <id> --plan path/to/plan.md
tasktool artifact add <id> --kind spec --path path/to/spec.md
tasktool artifact status <id> --strict
tasktool artifact commit <id> --message "..."
tasktool start <slice-id>      # lifecycle start + in_progress
tasktool set <id> --status in_progress  # compatibility alias
tasktool note <id> --append "..."
tasktool ref <id> --add path/to/artifact
tasktool block <slice-id> --on P2.S5
tasktool deps <slice-id> --add P2.S1
tasktool ratify <slice-id> --parallel-group bootstrap
tasktool surface add <slice-id> <surface> [<surface>...]   # declare shared write surfaces
tasktool surface remove <slice-id> <surface>
tasktool surface list [<phase-id>]
tasktool surface check <phase-id>            # unguarded overlaps + coordinated surfaces + reservation contention
tasktool reserve add <slice-id> <resource>:<value> [--scope phase|project] [--note "..."] [--force --reason "..."]
tasktool reserve remove <slice-id> <resource>:<value>
tasktool reserve list [<phase-id>]
tasktool coordinate <slice-id> --group <name>   # mark intentional shared-surface coordination
tasktool coordinate <slice-id> --clear
tasktool schedule <phase-id>
tasktool ready-slices <phase-id>
tasktool phase-status
tasktool close <slice-id>      # enforces post-slice review gate
tasktool close <x-id>          # closes and archives cross-cutting by default
tasktool close <x-id> --no-archive
tasktool cancel <id> --reason "<text>"           # terminate without shipping
tasktool cancel <phase-id> --reason "..." --cascade  # cancel a phase + its open slices
tasktool cancel <x-id> --reason "..." --no-archive   # keep cancelled X visible
tasktool archive-cross <x-id>  # archive a done visible cross-cutting item
tasktool archive-phase <phase-id>  # done phases require post-phase review; cancelled phases bypass it
tasktool validate              # full validation
```

Run `tasktool --help` (or `tasktool <cmd> --help`) for the full surface.

## Gating concepts (why the CLI refuses you)

- **Post-slice external review.** `tasktool close <slice-id>` reads `chain.json` from the slice's reviewer chain folder (`docs/reviewer/<slug>-post-slice/` by default; override with `--reviewer-chain`). It refuses unless the latest round's verdict ∈ {`ready`, `ready with small edits`}. Per-task internal reviews do not satisfy this gate.
- **Post-phase external review.** `tasktool archive-phase <phase-id>` refuses until every slice is `done` *and* the phase's post-phase chain returns `ready` / `ready with small edits`. If the phase itself is `cancelled`, archive still requires every child slice to be terminal, but it bypasses the post-phase chain because cancelled work never shipped.
- **Cross-cutting archive.** `tasktool close <x-id>` is ungated by external review and moves the completed X-item out of active `cross_cutting` into `archived_cross_cutting`, with a lossless markdown archive under `docs/archived-tasks/`. `--no-archive` leaves it visible as `done`; `tasktool archive-cross <x-id>` moves it later without sending another done notification.
- **`--skip-review-gate`** exists for emergencies and is recorded in the slice/phase `notes` with a timestamp. Use it only when the operator has explicitly chosen to bypass.

See `[[external-review]]` for how to drive the reviewer.

## Cancellation

- `tasktool cancel <id> --reason "<text>"` is the only sanctioned path. Applies to phases, slices, and cross-cutting items. Tasks cannot be cancelled — cancel the parent slice.
- The reason is required and is recorded in `notes` as `Cancelled <ISO-ts>: <reason>` (and `(cascaded from <phase-id>)` for child slices cancelled via `--cascade`).
- Cancellation **bypasses** the post-slice and post-phase external-review gates — cancelled work never shipped. A cancelled phase may be archived with `tasktool archive-phase <phase-id>` without `--skip-review-gate` or a post-phase reviewer chain.
- A cancelled slice does **not** satisfy a downstream `depends_on`. `tasktool schedule <phase-id>` emits `cancelled_deps` for affected slices; `ready-slices` omits them. Cancel the downstream too or remove the dependency.
- Cancelled cross-cutting items auto-archive by default. Use `--no-archive` to keep the cancelled row visible in the active list; archive later with `archive-cross`.
- Phase cancellation refuses if any slice is still open. Use `--cascade` to cancel open slices in one call; already-done slices are never touched.
- Edits on cancelled rows: `note --append`, `ref`, and `title` are allowed (post-mortem context); `set`, `close`, `start`, `block`, `unblock`, `deps`, `ratify`, and `note --replace` are refused.

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
| Incidental fix in the same area | `tasktool create task <slice-id> --title ...` |
| Real unit of work | `tasktool create slice <phase-id> --title ...` (or `--follow-up <slice-id>` for a letter-suffix) |
| Bug surfaced by review | Inline task if cheap; follow-up slice if it deserves its own scope. |
| Cross-cutting, unscheduled | `tasktool create cross --title ...` |

Creating a new slice or X-item is allocation/tracking only. It does not authorize implementing that work in the current slice worktree. If the discovery is truly incidental to the active slice, add an in-slice task and keep going. If it is real follow-up work, record it and defer until the current slice closes, or create a separate isolated worktree for that follow-up after the current slice boundary is clean.

## Referencing items in artifacts

- Specs, plans, reviewer chain folders: fully-qualified ID at first mention (`P9.S3a`), short form afterwards.
- Plan and spec filenames embed the ID: `YYYY-MM-DD-<id>-<slug>(-design).md`. The pre-commit hook rejects filenames whose ID has no `tasklist.json` row.
- Phase planning docs should be registered through `planning_path` once supported. During bootstrap or migration, either attach the document to `spec_path` for the phase ID or keep unregistered drafts outside orphan-checked paths such as `docs/_drafts/`.
- Commit messages may use either form; prefer fully-qualified for cross-phase commits.

## Workflow artifacts

Spec, plan, handoff, reviewer-chain, and archived-task paths are workflow artifacts. Register them through `tasktool artifact add` or `tasktool prepare`; do not hand-edit `docs/tasklist.json` refs for these paths. Use `tasktool artifact status <id> --strict` before handing work to another agent.

## workflow_step

Slices and phases carry an optional `workflow_step` field that tracks where the row is in the spec → plan → implement → done sequence. The two enums are intentionally different:

- **Slice steps:** `spec | plan | implement | done`. Set manually as the slice progresses through its lifecycle.
- **Phase steps:** `spec | ready | in_progress | done`. Set manually for `spec` / `ready`; `in_progress` / `done` are observable from child slice status and surface in `tasktool infer-step`.
- **Cross-cutting (`X*`) rows have no `workflow_step`** — they skip the spec/plan loop.

In this revision the field is **informational only**. No tasktool command auto-advances it; no operation is refused based on its value. Future slices in `P6 — Programmatic Workflow Enhancements` will introduce auto-advance and downstream automation (statusline / session-rename).

### Setting it manually

```bash
tasktool set P6.S1 --workflow-step plan
tasktool set P6 --workflow-step ready
tasktool set P6.S1 --clear-workflow-step
```

### Inspecting inferred values

```bash
tasktool infer-step P6.S1                 # text
tasktool infer-step P6.S1 --format json   # structured
tasktool infer-step --all --diff          # rows where stored != inferred (exit 1 if drift, 0 otherwise)
```

`infer-step` is read-only — it never mutates state. Use it to sanity-check what the field *would* be if you set it manually.

### Transient slice review block

The external-reviewer script writes a small transient block (`review_active`, `review_stage`) on slices when a plan or post-slice review is in progress. The block is cleared when the slice's `workflow_step` changes or when the review finishes. Agents and skills should not write these fields directly.

## Red flags

| Thought | Reality |
|---------|---------|
| "I'll just edit `docs/tasklist.json` by hand quickly." | The hook will refuse non-canonical bytes; `tasktool` is faster than fighting the hook. Use the CLI. |
| "I'll mark the slice `done` with `set` instead of `close` to skip the review gate." | `tasktool set --status done` routes through the same gate as `close`. The gate cannot be bypassed by reaching for a different subcommand. |
| "I'll mark this slice `done` to make it disappear." | Use `cancel`, not `close`. `done` is a lie if the work never shipped — and `close` runs the post-slice review gate, which is meaningless on cancelled work. |
| "I'll commit the spec now and add the row after." | The pre-commit hook rejects orphan spec/plan filenames. Allocate first. |
| "`tasktool` says the verdict isn't ready, but the reviewer comments look fine." | Re-read the verdict line. `revise` is `revise`. If the reviewer chain is mis-parsed, fix the chain; do not pass `--skip-review-gate` casually. |
| "I'll bring back `docs/TASKLIST.md` for readability." | The hook refuses commits that touch it. Use `tasktool render` if you want markdown. |
| "I'll just renumber IDs to match execution order." | No. IDs are stable. Execution order lives in the array order; IDs preserve creation order. |
| "Setup files are just scaffolding; I'll leave them dirty while implementing." | No. Setup/migration artifacts make post-slice review scope ambiguous. Resolve the setup boundary first. |
| "I created a follow-up slice/X-item, so I can knock it out in this worktree." | No. Allocation is not implementation permission. Follow-up work gets deferred or gets its own isolated worktree. |
| "I only need to add refs or flip the row before creating the worktree." | No. For an active implementation slice, tasktool refs/status/notes are part of the slice artifact set. Isolate first. |
| "A sibling's close is co-staged, so I must stop." | The tracker is whole-file bookkeeping. Truthful sibling lifecycle rows in `docs/tasklist.json` can be carried by scoped lifecycle commits; leave sibling artifacts alone and stop only when non-tracker files are mixed in. |
| "The slice is currently blocked, so I'll add `blocked_on` to model the phase plan." | No. Use `depends_on` for planned sequencing. Use `blocked_on` only for active runtime blockers. |
| "These slices are feature-independent, so they're parallel-safe." | Parallel safety is about **write surface**, not feature independence. Declare `integration_surfaces` and run `tasktool surface check <phase-id>` before dispatching them together. |
| "I'll pick a sort slot / collection name / route slug freely." | **Reserve** it (`tasktool reserve add`) so siblings cannot collide; for project-global resources use `--scope project`. The tool refuses a duplicate allocation. |
| "We both need the CMS registry, so I'll just `parallel_group` them." | A shared surface needs a `coordination_group` (coordinate) or a `depends_on` (serialize), not a `parallel_group` — which asserts independence the slices do not have. |

## Integration

- `[[writing-plans]]` — embeds slice IDs in plan filenames; calls `tasktool show <id>` for context.
- `[[brainstorming]]` — allocates IDs via `tasktool create` before writing the spec.
- `[[external-review]]` — passes tracker context as `--context`; prefer `tasktool brief <work-id>` output over the full `docs/tasklist.json` when the tasklist is large, and stamp `--work-id` on slice-level reviews.
- `[[subagent-driven-development]]` — calls `tasktool close <slice-id>` at slice end and `tasktool archive-phase` at phase end.
- `[[project-setup]]` — runs `tasktool init` and `install.sh --hook`.
