# X12 — tasktool: require authoritative-checkout routing for mutations

**Status:** spec
**Tasktool ID:** X12 (cross-cutting)
**Date:** 2026-05-20

## Problem

`tools/tasktool` already implements authoritative-checkout routing: when `.tasktool/config.json` sets `tasklist.mutation_mode` to `authoritative-checkout`, mutating commands route writes to the configured authoritative checkout (typically the `main` worktree) instead of the caller's CWD `docs/tasklist.json`. The mechanism is sound and exercised in this repo.

It is also opt-in. The default mutation mode is `local` (`tools/tasktool/config.py:13`), and projects with no `.tasktool/config.json` silently fall back to that default. Neither `tasktool init` nor the `project-setup` skill wires the authority config automatically. The result: a fresh project — or any project that never ran `tasktool config init-authority` — mutates whatever `docs/tasklist.json` happens to be in CWD, including the copy that lives inside a worktree.

The user-visible symptom is divergence between the TTS announcements emitted by `tools/tasktool/notify.py` (which fire from whichever tasklist.json was mutated, anywhere on disk) and the AGS sidebar widget (`~/.config/ags/gizmos/sidebar/tasklists/data.ts:147`), which only monitors `<projectRoot>/docs/tasklist.json`. A worktree-side mutation announces correctly but never reaches the file the widget watches. The example case is `multistore` P13.S6: the worktree `docs/tasklist.json` shows `status: in_progress, started: 2026-05-20`; the main-branch copy shows `status: ready, started: null`. Multistore has no `.tasktool/` directory at all.

The skills (`tasklist-discipline`, `using-git-worktrees`) treat authority routing as conditional — "when configured" — rather than as a binding requirement. That phrasing reflects the implementation but defeats the intent: authoritative routing should be the *only* supported mode for mutations, because it is the only mode under which the widget, TTS, and on-disk source-of-truth agree.

## Goals

1. Make authoritative-checkout routing structurally required for mutating tasktool commands. A repo with no authority config cannot accidentally mutate a worktree copy.
2. Provide a first-class migration path for repos that already drifted under the old default, so an operator can reconcile worktree-only state back into the authoritative checkout without hand-editing JSON.
3. Update the skills that govern tasktool usage so the documented workflow matches the enforced behaviour.

## Non-goals

- Changing the AGS sidebar widget. Once routing is enforced, the widget's existing single-file watch is correct by construction.
- Auto-detecting the authoritative branch name. `tasktool config init-authority` already takes the branch explicitly; this spec does not add main/master inference.
- Reconciling `multistore`'s current drift in code. The new `migrate-from-local` subcommand is the tool; running it against multistore is a one-shot operator action after this change ships.
- Removing the `local` mutation mode. It remains a valid *explicit* opt-out, written by hand, for repos that intentionally want CWD-local mutations and have no worktree convention. What changes is that it is no longer the implicit default.

## Design

### 1. Mutation default → hard error

`tools/tasktool/config.py` continues to accept `mutation_mode: "local"` as a valid configured value. What changes is the behaviour when no `.tasktool/config.json` exists, or when the file exists but does not specify `mutation_mode`:

- Today: silently defaults to `local`.
- After: `load_config()` returns a sentinel "unconfigured" state. `_resolve_write_root` in `tools/tasktool/commands.py` raises `CommandError` for mutating commands with the message:

  > tasktool: this repository has no authoritative-checkout routing configured. Run `tasktool config init-authority <branch>` from the authoritative checkout to enable safe routing. Existing local-mode tasklists can be reconciled with `tasktool config migrate-from-local`.

Mutating commands are those that go through `_write_context`: `init`, `create *`, `set`, `start`, `close`, `block`, `unblock`, `deps`, `ratify`, `planning-path`, `note`, `ref`, `title`, `archive-phase`, `import`.

This means the bootstrap order changes. Today: `tasktool init` (creates `docs/tasklist.json`) → optionally `tasktool config init-authority <branch>`. After: `tasktool config init-authority <branch>` first (writes `.tasktool/config.json` — does not go through `_write_context`, validates branch directly), *then* `tasktool init` (routes through the authority and creates the tasklist in the right checkout). `cmd_config_init_authority` is exempt from the hard error by virtue of not flowing through `_write_context`; this is preserved deliberately so the bootstrap path remains usable. The `project-setup` skill documents the new order.

Read-only commands — `render`, `validate`, `brief`, `schema`, `show`, `phase-status`, `ready-slices`, `list`, `next-id` — must continue to work without config. They read whichever `docs/tasklist.json` is in CWD. The error is raised *only* on the mutation path.

An explicit `mutation_mode: "local"` keeps its current behaviour: mutations land in CWD's `docs/tasklist.json` with no routing. The hard error fires only for unconfigured repos.

### 2. `tasktool config init-authority` — no functional change

The existing subcommand keeps its semantics: must be run from the target branch in a clean checkout, writes `.tasktool/config.json` with `mutation_mode: authoritative-checkout` and the supplied branch name, stages the file. The hardening here is by virtue of step 1 — operators discover they need to run it because mutations now fail loudly without it.

### 3. `tasktool config migrate-from-local` — new subcommand

Synopsis:

```
tasktool config migrate-from-local [--dry-run]
                                   [--accept-local | --accept-authoritative]
```

Semantics:

1. **Preconditions.** Authority config exists (otherwise the caller should be running `init-authority` first, not `migrate-from-local`). Caller's repo is the same git common-dir as the authoritative root. Authoritative root resolves cleanly via `find_authoritative_root`. If any precondition fails, raise `CommandError` with a specific remediation.
2. **Load both tasklists.** Local = CWD's `docs/tasklist.json` parsed via existing `_load`. Authoritative = authoritative root's `docs/tasklist.json` parsed via existing `_load`. If the two are byte-identical, exit 0 with "no drift detected".
3. **Row-level diff.** Walk phases, slices (nested under phases), and `cross_cutting`. For each row keyed by ID:
   - Row exists in local only → candidate addition.
   - Row exists in authoritative only → candidate deletion (rare; usually means main is ahead — flag as conflict).
   - Both → compare field-by-field across `status`, `started`, `closed`, `title`, `refs`, `notes`, `depends_on`, `parallel_group`, `spec_path`, `plan_path`, `planning_path`, `follow_up`, and any other persisted scalar/list fields. Each differing field is a delta.
4. **Render a human-readable diff** to stdout, e.g.:

   ```
   P13.S6  status: ready → in_progress
           started: null → 2026-05-20
   P13.S7  status: ready → done
           closed: null → 2026-05-19
   X9      notes: "" → "deferred to phase 14"
   ```

5. **`--dry-run`**: stop here.
6. **Conflict policy.**
   - `--accept-local` (default): the local copy wins per-field. This is the realistic migration direction — worktree drift is what we need to capture.
   - `--accept-authoritative`: authoritative wins per-field. No write occurs; the command becomes a verification step.
   - No flag and stdin is a TTY: prompt once at the top with the diff already printed, accepting `local`/`authoritative`/`abort`.
   - No flag and stdin is not a TTY: error, demand explicit flag.
7. **Apply.** Acquire `tasktool_lock` on the authoritative root. Re-read the authoritative tasklist inside the lock (defensive against concurrent writes). Apply the resolved deltas in memory. `_save(authoritative_root, project)`. Stage the file via existing best-effort stage.
8. **Notify.** For each row whose `status` changed, call `_notify_status` with the post-migration status so the TTS pipeline and any downstream consumers see the transition. Non-status field changes do not notify.
9. **Exit message.** Print a one-line summary: `migrated N rows (S status transitions) to <authoritative-root>`. Leave the local tasklist.json untouched; the next mutation routes through authority and the local copy becomes irrelevant.

The command does **not** attempt to replay the deltas as a sequence of individual tasktool subcommands. A single merged `_save` is simpler, atomic under the lock, and avoids combinatorial issues (e.g. a slice that was both started and closed in the worktree).

### 4. Skills

- `skills/project-setup/SKILL.md` — add to the setup checklist: after `tasktool init`, run `tasktool config init-authority <main-branch>` and commit `.tasktool/config.json`. Surface a missing/unconfigured authority as a setup-precondition failure on par with a missing `docs/tasklist.json`.
- `skills/tasklist-discipline/SKILL.md` — change the existing paragraph that opens "When `.tasktool/config.json` sets `tasklist.mutation_mode` to `authoritative-checkout`…" so that authoritative routing is described as the required mode. Add a one-line remediation pointer: if a mutation errors with "no authoritative-checkout routing configured", run `tasktool config init-authority <branch>` from the target branch.
- `skills/using-git-worktrees/SKILL.md` — remove the "If tasktool authoritative-checkout routing is configured" conditional. Replace with the unconditional rule that tasktool mutations from worktrees route through authority; if config is missing, configure it before starting implementation work.

No new skill files. No new top-level docs.

## Component boundaries

- `config.py` owns the unconfigured-vs-explicit-local distinction. It exposes a small predicate (`is_authoritative_required(cfg) -> bool` or equivalent) consumed by `commands.py`. Adding the predicate keeps `commands.py` free of policy logic.
- `commands.py` owns the routing decision and the new `cmd_config_migrate_from_local` function. Pure-Python diff/merge over the existing `Project` dataclass tree; reuses `_load`, `_save`, `tasktool_lock`, `_notify_status`.
- `cli.py` owns argument parsing for the new subcommand: `--dry-run`, `--accept-local`, `--accept-authoritative`.
- `worktree.py` is unchanged. `find_authoritative_root`, `validate_authoritative_checkout`, and `tasktool_lock` already do what `migrate-from-local` needs.

## Error handling

- Unconfigured repo, mutating command: `CommandError` with the migration hint message (verbatim above). Non-zero exit.
- `init-authority` from wrong branch: existing behaviour preserved.
- `migrate-from-local` with no authority config: `CommandError`: `run tasktool config init-authority <branch> before migrating`.
- `migrate-from-local` when authoritative tasklist is missing entirely: `CommandError`: tells the user to run `tasktool init` in the authoritative checkout first.
- `migrate-from-local` with no detectable drift: exit 0, message "no drift detected".
- `migrate-from-local` with `--accept-local` and no TTY when prompt would be needed: covered by the per-flag explicit semantics; no interactive fallback in non-TTY contexts.

## Testing

New tests under `tools/tasktool/tests/`:

1. `test_config_default_errors_on_mutation` — fresh repo, no `.tasktool/config.json`; `tasktool start P1.S1` raises `CommandError` containing the migration hint substring.
2. `test_config_explicit_local_mode_still_mutates_cwd` — config with `mutation_mode: local`; `tasktool start P1.S1` mutates CWD's tasklist; assert no regression.
3. `test_readonly_commands_work_without_config` — `render`, `validate`, `brief` succeed against an unconfigured repo.
4. `test_migrate_from_local_dry_run` — divergent tasklists; `--dry-run` prints the row-level diff and writes nothing.
5. `test_migrate_from_local_accept_local_applies_deltas` — divergent `status`, `started`, `closed`, `refs`, `notes`; `--accept-local` writes them through to the authoritative tasklist; assert post-merge equality.
6. `test_migrate_from_local_accept_authoritative_noop` — `--accept-authoritative` acquires the lock, writes nothing, exits 0.
7. `test_migrate_from_local_emits_notify_events` — status transitions during migration produce notify events matching the existing fixture pattern in `tools/tasktool/tests/test_notify.py`.
8. `test_migrate_from_local_no_drift_exits_clean` — byte-identical tasklists; command exits 0 with the "no drift detected" message.
9. `test_migrate_from_local_requires_authority_config` — no `.tasktool/config.json`; command raises `CommandError` directing the user to run `init-authority` first.

Existing tests should be audited for any that rely on the implicit-`local` default; those switch to either configuring `local` explicitly or configuring `authoritative-checkout`, whichever matches the test's intent.

## Migration & rollout

After merge, the operator action for `multistore` (and any other repo that drifted under the old default) is:

```
cd <repo>                                                      # any checkout
tasktool config init-authority main                            # writes .tasktool/config.json from main
tasktool config migrate-from-local --accept-local              # captures worktree drift
git -C <authoritative checkout> add docs/tasklist.json .tasktool/config.json
git -C <authoritative checkout> commit -m "tasktool: enable authoritative routing and reconcile drift"
```

The change is otherwise transparent for repos already running `authoritative-checkout` (this one).

## Open questions

None. The two product decisions — enforcement aggressiveness (hard error) and reconciliation approach (dedicated `migrate-from-local` subcommand) — are settled.
