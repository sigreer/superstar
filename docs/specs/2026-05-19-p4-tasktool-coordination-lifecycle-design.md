# P4 — Tasktool Coordination and Lifecycle Authority

**Status:** proposed
**Date:** 2026-05-19
**TASKLIST entry:** `P4` in `docs/tasklist.json`

## Objective

Make `tasktool` the enforced authority for two workflow rules that are currently left to agent discipline:

1. Parallel implementation worktrees must not own `docs/tasklist.json` mutations.
2. Active slices and tasks must pass through `in_progress` instead of jumping from `ready` to `done`.

The intended outcome is that agents can keep using normal `tasktool` commands from whatever checkout they are working in, but the tool decides where writes land and which lifecycle transitions are valid.

## Problem

`docs/tasklist.json` is the single source of truth, but linked implementation worktrees currently mutate their local copy. When those branches merge back to `main`, tasklist updates from multiple agents collide as byte-level JSON diffs. This is predictable because each worktree was forked from a stale snapshot of the tracker.

The same workflow has a status-quality issue: agents rarely mark slices or tasks `in_progress`. Rows remain `ready` until they are closed, which makes `tasktool list --open`, `phase-status`, and human progress scans much less useful.

These are not independent usability nits. They expose the same architectural gap: `tasktool` has the canonical data model, but it does not yet enforce the coordinator lifecycle strongly enough.

## Design Summary

`tasktool` gains two linked capabilities:

- **Authoritative checkout routing.** Mutating commands invoked from implementation worktrees are applied to a configured authoritative checkout, normally the project `main` checkout. Every authoritative-mode write uses the same lock, including commands invoked directly from the authoritative checkout. Worker worktrees treat `docs/tasklist.json` as a read-only mirror.
- **Lifecycle start enforcement.** `tasktool start <id>` becomes the normal way to begin work. Slice close is allowed only after a slice has been observed `in_progress`, unless an explicit bypass is supplied and recorded.

The skills are updated to describe the new command surface, but correctness does not depend on prose. The CLI enforces the rules.

## Configuration

Add a tracked project config file:

```json
{
  "schema_version": 1,
  "tasklist": {
    "mutation_mode": "authoritative-checkout",
    "authoritative_branch": "main"
  }
}
```

The default path is `.tasktool/config.json`. This file is intended to be committed because it contains project policy only, not machine-local absolute paths. If no config exists, current behavior remains unchanged so existing projects do not break abruptly.

Field semantics:

- `mutation_mode`
  - `local`: existing behavior; mutate the current checkout.
  - `authoritative-checkout`: route mutating commands from linked worktrees to `authoritative_root`.
- `authoritative_branch`: branch the authoritative checkout must be on when accepting writes.

Machine-local root discovery:

1. If `TASKTOOL_AUTHORITY_ROOT` is set, use it.
2. Otherwise inspect `git worktree list --porcelain` and find the checkout whose branch is `authoritative_branch`.
3. If exactly one checkout matches, use it.
4. If none or more than one match, fail closed and print the exact `TASKTOOL_AUTHORITY_ROOT=/path/to/checkout` override to use.

`tasktool config init-authority --branch main` writes or updates `.tasktool/config.json`. It does not write absolute paths. A separate untracked `.tasktool/local.json` may be added later, but P4 should not require it.

## Mutating Commands

The routing layer applies to all commands that write `docs/tasklist.json`:

- `init`
- `create phase|slice|task|cross`
- `set`
- `start`
- `close`
- `block`
- `unblock`
- `deps`
- `ratify`
- `planning-path`
- `note`
- `ref`
- `title`
- `archive-phase`
- `import`
- `validate --normalise`

Read commands keep using the current checkout by default, but they should warn when authoritative routing is configured and the current worktree copy is older than the authoritative copy. A follow-up may add `--source authoritative|local`; P4 does not need it.

## Routing Rules

For every mutating command:

1. Discover the current repository root and git common directory.
2. Load `.tasktool/config.json` if present.
3. If `mutation_mode` is absent or `local`, mutate the current checkout.
4. Resolve `authoritative_root` via the machine-local discovery rules.
5. Acquire an exclusive lock under the common git directory before loading tasklist data.
6. Validate that `authoritative_root` exists, is a git checkout for the same repository, is on `authoritative_branch`, and has no unresolved merge.
7. Validate that `authoritative_root/docs/tasklist.json` is not dirty in a way that cannot be attributed to tasktool's own current command.
8. Load and mutate `authoritative_root/docs/tasklist.json`, even if the invocation already came from that checkout.
9. Save canonical JSON and best-effort stage the authoritative path.
10. Print a concise routing message only when the invocation root differs from the authoritative root.

The implementation should centralize this routing in one module so command functions do not each grow git-worktree logic.

The lock is mandatory for every authoritative-mode mutation. Direct `main` checkout invocations and worker-routed invocations contend on the same lock, preventing interleaved read-modify-write cycles.

## Two-Root Command Contract

Commands in authoritative mode have two roots:

- `invocation_root`: the checkout where the user or agent ran the command.
- `write_root`: the authoritative checkout whose `docs/tasklist.json` is mutated.

User-supplied file paths and reviewer-chain discovery are interpreted relative to `invocation_root`. Tasklist load/save/stage happens in `write_root`. This applies to `close` and to `set --status done`, because both routes can invoke review-gate checks.

Explicit reviewer-chain paths may be absolute or relative, but they must resolve inside `invocation_root`. Paths outside the repository are refused. The value recorded into tasklist is always repo-relative from `invocation_root`.

## Reviewer Chains From Worktrees

`tasktool close <slice-id>` and `tasktool set <id> --status done` must preserve review-gate semantics when invoked from an implementation worktree.

The gate should evaluate reviewer artifacts relative to the invocation checkout because that is where post-slice review was run. The resulting `reviewer_chain` recorded into the authoritative tasklist remains a repo-relative path, for example:

```text
docs/reviewer/p11-s4c-nav-footer-P11-S4c-post-slice
```

If the reviewer chain path is outside the repository, the command refuses it. If the same repo-relative reviewer chain does not exist in the authoritative checkout yet, close still records the relative path; merge-back will bring the artifacts over. The JSON record must not depend on absolute worktree paths.

## Lifecycle Enforcement

Add:

```sh
tasktool start <id>
```

Behavior:

- Accepts phases, slices, tasks, and cross-cutting items.
- Resolves short IDs exactly like `set`.
- Refuses `done` items.
- Refuses `blocked` slices unless `--resume` is supplied, in which case it clears `blocked_on` and sets `in_progress`.
- Sets `status: in_progress`.
- Records a machine-readable lifecycle marker that proves the item was started before close.

The marker should be explicit rather than inferred from current status, because a row may later move from `in_progress` to `blocked` and back. Add `started: YYYY-MM-DD | null` to phase, slice, task, and cross-cutting records. Existing files load with `started: null`.

`tasktool set <id> --status in_progress` becomes a compatibility alias for `tasktool start <id>`. It sets `started` using the same rules and notifications. This keeps older skill prose or human muscle memory from producing a visible `in_progress` state that later fails close because no start marker exists.

Close behavior:

- Closing tasks and cross-cutting items from `ready` remains allowed for now, because they are often small bookkeeping rows.
- Closing slices from `ready` is refused unless `--allow-ready-close` is supplied.
- `--allow-ready-close` appends an audit note with timestamp and reason.
- Closing phases from `ready` remains allowed only through `archive-phase`; phase lifecycle is already gated by completed slices.

This targets the recurring operational pain without making every tiny task transition noisy.

## Skill Updates

Update these skills:

- `tasklist-discipline`: explain authoritative routing, `tasktool start`, and the `ready -> done` slice close guard.
- `using-git-worktrees`: say worktrees may invoke tasktool mutations, but mutations route to the authoritative checkout when configured.
- `subagent-driven-development`: after selecting a ready slice and before dispatching implementation subagents, run `tasktool start <slice-id>`.
- `executing-plans`: replace the current prose-only "Mark as in_progress" step with `tasktool start <slice-id>`.
- `writing-plans`: plans for slice execution should include `tasktool start <slice-id>` as the first execution step when `docs/tasklist.json` exists.

The status problem is partly skill markdown today, especially in `subagent-driven-development`, but the P4 fix should not rely on skill wording alone.

## Slices

### P4.S1 — Authoritative Tasklist Mutations

Add config loading, git worktree detection, lock acquisition, routing helpers, and command integration for all tasklist-writing commands. Worker worktrees stop committing `docs/tasklist.json` deltas.

### P4.S2 — Lifecycle Status Enforcement

Add `started` fields, `tasktool start`, close-time enforcement for slices, and skill updates that make lifecycle transitions visible and routine.

Depends on: `P4.S1`, because lifecycle commands should use the same routed-write path.

## Acceptance Criteria

- `tasktool validate --strict-format` passes on existing tasklist files.
- Tasktool unit and CLI tests cover local mode, authoritative mode, linked worktree routing, lock contention, unsafe authoritative checkout states, and reviewer-chain recording from a worker worktree.
- A simulated worker worktree can run `tasktool close P1.S1 --reviewer-chain ...` and leave the worker copy of `docs/tasklist.json` unchanged while updating the authoritative checkout.
- Direct authoritative-checkout writes and worker-routed writes contend on the same tasktool lock.
- `tasktool config init-authority --branch main` creates tracked project policy without absolute paths.
- A worker worktree with authoritative routing configured but no discoverable authoritative root fails closed instead of falling back to local mutation.
- `tasktool set P1.S1 --status done --reviewer-chain ...` uses the same two-root reviewer-gate contract as `tasktool close`.
- Explicit reviewer-chain paths outside the invocation repository are refused.
- `tasktool start P1.S1` sets `status: in_progress` and `started`.
- `tasktool set P1.S1 --status in_progress` sets the same `started` marker as `tasktool start`.
- `tasktool close P1.S1` refuses a never-started slice unless `--allow-ready-close --reason "..."` is supplied.
- Skills describe the enforced workflow without asking agents to hand-edit tasklist state.

## Non-Goals

- Do not build a semantic `tasktool merge` command in this phase. It is a fallback for a worse invariant.
- Do not move task state outside the repository.
- Do not add networked locking or a daemon.
- Do not require all existing projects to adopt authoritative routing immediately.
- Do not force every task row through `in_progress` before close in this phase.
