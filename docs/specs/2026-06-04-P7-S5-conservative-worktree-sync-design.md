# P7.S5 — Conservative worktree sync

**Status:** design (spec)
**Date:** 2026-06-04
**Slice ID:** `P7.S5`
**Parent phase:** `P7 — Integration-surface-aware parallel slice safety`

## 1. Problem

`P7.S4` made stale worktrees visible: `tasktool worktree status <slice-id> --integration`
reports when the configured base branch has advanced since a slice recorded
`worktree_base_sha`, and whether sibling slices landed in that window. That
is enough to detect risk, but the recovery step is still raw git.

Raw git is too easy to run from the wrong checkout, against the wrong base, or
with unresolved tracker drift. The phase design intentionally rejects an
unconditional sync command; the mutating recovery path must be explicit,
conservative, and auditable.

## 2. Goals

1. Add `tasktool worktree sync <slice-id> (--merge | --rebase)`.
2. Refuse unless the slice has a recorded worktree or is explicitly in-place.
3. Refuse unless `worktree_base_sha` is present and the configured authoritative
   base branch resolves.
4. Refuse unless the implementation worktree is clean and has no unresolved
   merge state, with the staged-tasklist exception described below.
5. Refuse if `docs/tasklist.json` has unsafe unstaged tasklist drift in the
   authoritative checkout.
6. On a successful merge or rebase, advance the slice's `worktree_base_sha` to
   the base-branch HEAD that was integrated.
7. Print follow-up instructions to rerun `worktree status --integration`,
   regenerate derived artifacts, and rerun verification.

## 3. Non-goals

- No automatic conflict resolution. If merge or rebase conflicts, git stops and
  `tasktool` must leave `worktree_base_sha` unchanged.
- No default strategy. The caller must choose `--merge` or `--rebase`.
- No remote fetching. The command integrates the local configured base branch.
- No lifecycle status changes. Sync does not start, close, block, or ratify a
  slice.
- No skill-document updates. `P7.S6` owns the end-of-slice checkpoint and skill
  wording.

## 4. Command contract

```sh
tasktool worktree sync <slice-id> --merge
tasktool worktree sync <slice-id> --rebase
```

`--merge` and `--rebase` are mutually exclusive and one is required.

The command resolves the row through the existing authoritative routing used by
other tasktool writes. The base branch comes only from
`.tasktool/config.json` / `load_config(write_root).tasklist.authoritative_branch`;
there is no hard-coded `main` fallback in command logic beyond the config
default.

## 5. Refusal rules

The command refuses before invoking mutating git when any of these are true:

1. The ID is not a slice.
2. The slice has neither `worktree_in_place` nor a recorded `worktree_path`.
3. A recorded linked worktree is not live and consistent according to the
   existing `_health_for` classification.
4. `worktree_base_sha` is missing.
5. The configured base branch cannot be resolved to a commit SHA.
6. The target worktree has uncommitted tracked changes, untracked files, or a
   stash attributable to its current branch, using the existing
   `worktree.working_tree_dirty` helper. When the target worktree is the
   authoritative checkout, staged-only `docs/tasklist.json` is excluded from
   this dirty check because tasktool itself commonly stages serialized tracker
   mutations there.
7. The target worktree has unresolved merge entries, detected with
   `worktree.has_unmerged_paths(target_worktree)`.
8. The authoritative checkout has unsafe unstaged `docs/tasklist.json` drift,
   using `worktree.tasklist_has_unsafe_dirty_state(write_root)`.

Staged-only `docs/tasklist.json` changes in the authoritative checkout are
allowed. Existing tasktool commands commonly stage serialized tracker mutations;
sync should not reject that safe state. Unstaged `docs/tasklist.json` bytes are
still refused.

For a linked worktree, git operations run in the resolved linked worktree path
and tasklist writes run in the authoritative checkout. For an in-place slice,
the target worktree is the repo root; if that checkout is already on the base
branch, syncing base into itself is a no-op git operation that can still advance
`worktree_base_sha` to the current base SHA.

## 6. Success semantics

Before running git, capture:

- `base_branch` from config,
- `base_head_before` from `current_branch_head_sha(write_root, base_branch)`,
- `previous_worktree_base_sha` from the slice row.

Run exactly one git operation in the target worktree, integrating the captured
SHA rather than the moving branch ref:

- `git merge --no-edit <base_head_before>` for `--merge`;
- `git rebase <base_head_before>` for `--rebase`.

After the operation succeeds, set `slice.worktree_base_sha = base_head_before`
and save the tasklist. The command advances to the SHA it actually attempted to
integrate, not a later base tip that may appear after the git command started.
That makes the integrated SHA and the recorded SHA identical by construction.

The git operation must not hold the tasktool lock. The implementation performs
the git merge/rebase first, then re-enters the normal locked authoritative write
path to re-read the row, set `worktree_base_sha`, and save. `git merge` must be
non-interactive; use `--no-edit` and a subprocess environment that cannot open
an editor.

Output includes:

- the slice ID,
- the strategy used,
- the base branch and integrated SHA,
- the previous and new `worktree_base_sha`,
- follow-up commands:
  - `tasktool worktree status <slice-id> --integration`,
  - project verification commands chosen by the implementer,
  - regenerate derived artifacts when the project has generated snapshots,
    checksums, schemas, or lock files.

## 7. Failure semantics

If git returns non-zero, the command raises a tasktool error and leaves
`worktree_base_sha` unchanged. The user resolves or aborts the git state with
normal git commands. If the user manually resolves and commits the merge or
rebase outside tasktool, they should rerun the same
`tasktool worktree sync ...` command afterward; git should report the captured
base as already integrated, and the successful tasktool run can then advance
`worktree_base_sha`.

The command does not try to detect whether a failed merge/rebase partially
integrated commits. The invariant is simple: `worktree_base_sha` advances only
after the selected git command exits zero.

`--rebase` rewrites the slice branch's commits. Callers should avoid it when
another system already references the old commit SHAs, such as an in-flight
review or pull request.

## 8. File responsibilities

| File | Responsibility |
|------|----------------|
| `tools/tasktool/cli.py` | Add the `worktree sync` subparser with required mutually exclusive `--merge` / `--rebase` flags and route it to commands. |
| `tools/tasktool/commands.py` | Implement `cmd_worktree_sync`, row lookup, precondition checks, target worktree resolution, git invocation, base-SHA update, save, and human-readable output. |
| `tools/tasktool/worktree.py` | Add small git helpers only if needed for clean sync implementation. Reuse existing helpers for branch resolution, dirty checks, and unresolved merge detection where possible. |
| `tools/tasktool/tests/test_worktree_sync.py` | New focused tests for CLI contract, refusal cases, merge/rebase success, git-failure no-advance behavior, and staged-vs-unstaged tasklist drift. |

## 9. Testing strategy

Tests should build small local git repositories with `tasktool init-local`,
phase/slice rows, and linked or in-place worktrees, following the style of
`test_worktree_integration.py` and `test_worktree_prune.py`.

Required coverage:

1. Parser rejects `worktree sync` with neither strategy and with both strategies.
2. A clean linked worktree can `--merge` the configured base branch and advances
   `worktree_base_sha` to the pre-operation base head.
3. A clean linked worktree can `--rebase` the configured base branch and advances
   `worktree_base_sha` to the pre-operation base head.
4. An in-place slice in a single-checkout repo syncs in the repo root and
   advances `worktree_base_sha`, including when staged-only `docs/tasklist.json`
   tracker bytes are present.
5. Missing `worktree_base_sha` refuses before git mutation.
6. Dirty target worktree refuses before git mutation.
7. Unstaged authoritative `docs/tasklist.json` drift refuses; staged-only
   tasklist changes do not.
8. A merge conflict returns non-zero and leaves `worktree_base_sha` unchanged.
9. `worktree status --integration` after a successful sync no longer reports
   already-integrated base commits as ahead of `worktree_base_sha`.

## 10. Scheduling

`P7.S5` depends on `P7.S4` because it mutates the `worktree_base_sha` field that
S4 records and uses S4's integration detection as its post-sync verification.
It writes the `worktree` integration surface. It does not need to wait for
`P7.S6` skill changes, because S6 documents this command after it lands.

The slice remains independently plannable and executable now that `P7.S4` is
done. It should not be parallel-dispatched with any other open slice that writes
the `worktree` surface unless a dependency or `coordination_group` is declared.
