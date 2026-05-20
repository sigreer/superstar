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

  > tasktool: this repository has no authoritative-checkout routing configured. Run `tasktool config init-authority --branch <branch>` from the authoritative checkout to enable safe routing. Existing local-mode tasklists can be reconciled with `tasktool config migrate-from-local`.

Mutating commands are those that go through `_write_context`: `init`, `create *`, `set`, `start`, `close`, `block`, `unblock`, `deps`, `ratify`, `planning-path`, `note`, `ref`, `title`, `archive-phase`, `import`, and `validate --normalise` (the `--normalise` flag triggers a `_write_context` write at `tools/tasktool/commands.py:814`; plain `validate` remains read-only).

This means the bootstrap order changes. Today: `tasktool init` (creates `docs/tasklist.json`) → optionally `tasktool config init-authority --branch <branch>`. After: `tasktool config init-authority --branch <branch>` first (writes `.tasktool/config.json` — does not go through `_write_context`, validates branch directly), *then* `tasktool init` (routes through the authority and creates the tasklist in the right checkout). `cmd_config_init_authority` is exempt from the hard error by virtue of not flowing through `_write_context`; this is preserved deliberately so the bootstrap path remains usable. The `project-setup` skill documents the new order.

Read-only commands — `render`, `validate` (without `--normalise`), `brief`, `schema`, `show`, `phase-status`, `ready-slices`, `list`, `next-id` — must continue to work without config. They read whichever `docs/tasklist.json` is in CWD. The error is raised *only* on the mutation path.

An explicit `mutation_mode: "local"` keeps its current behaviour: mutations land in CWD's `docs/tasklist.json` with no routing. The hard error fires only for unconfigured repos.

### 2. `tasktool config init-authority` — no functional change

The existing subcommand keeps its semantics: invoked as `tasktool config init-authority --branch <branch>`, must be run from the target branch in a clean checkout, writes `.tasktool/config.json` with `mutation_mode: authoritative-checkout` and the supplied branch name, stages the file. The hardening here is by virtue of step 1 — operators discover they need to run it because mutations now fail loudly without it.

### 2a. `tasktool config init-local` — new auditable opt-out

To keep `mutation_mode: "local"` from requiring hand-edited JSON, add a thin sibling subcommand:

```
tasktool config init-local
```

Writes `.tasktool/config.json` with `mutation_mode: local`, stages the file, and prints a one-line notice that worktree-side mutations will not be routed. Behaviour is otherwise identical to today's `local` mode; this exists purely so the opt-out leaves a tracked, committed artifact, and so the hard error message can point at a concrete remediation rather than at a JSON snippet to copy. Does not go through `_write_context`.

### 3. `tasktool config migrate-from-local` — new subcommand

Synopsis:

```
tasktool config migrate-from-local --authority-root <path> [--local-root <path>]
                                   [--dry-run]
                                   [--accept-local | --accept-authoritative]
```

Rationale for the explicit root flags: the realistic drift case is a repo with no `.tasktool/config.json` anywhere on disk — including the worktree the operator is sitting in. Requiring authority config in either tree would create a bootstrap deadlock (you cannot `init-authority` into the drifted worktree without first being on `main` there, and you cannot reach the worktree's tasklist from `main` once you switch). Passing both roots explicitly bypasses any dependency on existing config:

- `--authority-root <path>` (required): absolute or repo-relative path to the checkout that will become authoritative. Must resolve to a git checkout in the same common-dir as the caller. The migration writes here.
- `--local-root <path>` (optional, default = CWD's repo root): absolute or repo-relative path to the checkout whose `docs/tasklist.json` holds the drifted state to capture. Read-only.

Semantics:

1. **Preconditions.** Both roots resolve to git checkouts. `same_repository(authority_root, local_root)` returns true. `validate_authoritative_checkout(authority_root, expected_branch=<resolved>, caller_root=local_root)` succeeds — the authority root is on its target branch, clean of unmerged paths, and free of unstaged `docs/tasklist.json` changes. If `.tasktool/config.json` exists in `authority_root` and specifies a `mutation_mode`/`authoritative_branch`, those values are honoured; otherwise the authority root's *current branch* is treated as the target (and persisted into a new `.tasktool/config.json` on successful migration). Either tasklist missing → `CommandError` with a remediation hint.
2. **Load both tasklists.** Local = `<local_root>/docs/tasklist.json` parsed via existing `_load`. Authoritative = `<authority_root>/docs/tasklist.json` parsed via existing `_load`. If the two are byte-identical, exit 0 with "no drift detected".
3. **Row-level diff (full persisted surface).** Walk every row class the model persists, using dataclass introspection (`dataclasses.fields()` on `Project`, `Phase`, `Slice`, `Task`, `CrossCutting`, and any other row dataclass declared in `tools/tasktool/model.py`) so the diff cannot silently omit fields. Concretely:
   - **Top-level scalars on `Project`** — `project`, `north_star`, `last_reviewed`, and any other top-level scalar declared in the dataclass.
   - **`phases[]`** keyed by `Phase.id`. For each phase: every field declared on `Phase` (including `status`, `started`, `closed`, `title`, `spec_path`, `plan_path`, `planning_path`, `planning_status`, `refs`, `notes`, `depends_on`, `blocked_on`, `parallel_group`, `reviewer_chain`, `phase_reviewer_chain`, `created`).
   - **`phases[].slices[]`** keyed by `Slice.id` within its phase. Every field declared on `Slice`.
   - **`phases[].slices[].tasks[]`** (and any other nested rows the model declares) keyed by `Task.id` within its slice. Every field declared on `Task`.
   - **`cross_cutting[]`** keyed by `CrossCutting.id`. Every field declared on `CrossCutting`.
   - **`archived_phases[]`** keyed by `id`. Every field declared on the archive row type.
   - For each row: present in local only → candidate addition; present in authoritative only → candidate deletion (flagged as conflict — main is ahead); present in both → every dataclass field is compared. Each differing field is a delta.
   The implementation is one short recursive walker keyed off `dataclasses.fields()`, not a hand-maintained field list. The test suite asserts that adding a new field to any row dataclass without updating the walker fails loudly (see Testing).
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

- `skills/project-setup/SKILL.md` — add to the setup checklist: **before `tasktool init`**, from the target branch, run `tasktool config init-authority --branch <main-branch>` and commit `.tasktool/config.json`; then run `tasktool init`. The reverse order would fail under the new hard error because `tasktool init` itself routes through `_write_context`. Surface a missing/unconfigured authority as a setup-precondition failure on par with a missing `docs/tasklist.json`.
- `skills/tasklist-discipline/SKILL.md` — change the existing paragraph that opens "When `.tasktool/config.json` sets `tasklist.mutation_mode` to `authoritative-checkout`…" so that authoritative routing is described as the required mode. Add a one-line remediation pointer: if a mutation errors with "no authoritative-checkout routing configured", run `tasktool config init-authority --branch <branch>` from the target branch.
- `skills/using-git-worktrees/SKILL.md` — remove the "If tasktool authoritative-checkout routing is configured" conditional. Replace with the unconditional rule that tasktool mutations from worktrees route through authority; if config is missing, configure it before starting implementation work.

No new skill files. No new top-level docs.

## Component boundaries

- `config.py` owns the unconfigured-vs-explicit-local distinction. It exposes a small predicate (`is_authoritative_required(cfg) -> bool` or equivalent) consumed by `commands.py`. Adding the predicate keeps `commands.py` free of policy logic.
- `commands.py` owns the routing decision and the new `cmd_config_migrate_from_local` function. Pure-Python diff/merge over the existing `Project` dataclass tree; reuses `_load`, `_save`, `tasktool_lock`, `_notify_status`.
- `cli.py` owns argument parsing for the new subcommands. `config migrate-from-local`: `--authority-root <path>` (required), `--local-root <path>` (optional, defaults to caller repo root), `--dry-run`, `--accept-local`, `--accept-authoritative`. `config init-local`: no arguments.
- `worktree.py` is unchanged. `find_authoritative_root`, `validate_authoritative_checkout`, and `tasktool_lock` already do what `migrate-from-local` needs.

## Error handling

- Unconfigured repo, mutating command: `CommandError` with the migration hint message (verbatim above). Non-zero exit.
- `init-authority` from wrong branch: existing behaviour preserved.
- `migrate-from-local` with no `--authority-root`: `CommandError`: `migrate-from-local requires --authority-root <path>`. The command never assumes a config-driven default; the path must be explicit so the migration is unambiguous even when `.tasktool/config.json` is absent from every checkout.
- `migrate-from-local` where `--authority-root` and `--local-root` are not the same git common-dir: `CommandError`: `authority root and local root are not the same repository`.
- `migrate-from-local` when authoritative tasklist is missing entirely: `CommandError`: tells the user to run `tasktool init` in the authoritative checkout first.
- `migrate-from-local` with no detectable drift: exit 0, message "no drift detected".
- `migrate-from-local` with `--accept-local` and no TTY when prompt would be needed: covered by the per-flag explicit semantics; no interactive fallback in non-TTY contexts.

## Testing

New tests under `tools/tasktool/tests/`:

1. `test_config_default_errors_on_mutation` — fresh repo, no `.tasktool/config.json`; `tasktool start P1.S1` raises `CommandError` containing the migration hint substring.
2. `test_config_default_errors_on_validate_normalise` — fresh repo, no config; `tasktool validate --normalise` raises `CommandError` (mutating); `tasktool validate` (no flag) still works.
3. `test_config_explicit_local_mode_still_mutates_cwd` — config with `mutation_mode: local`; `tasktool start P1.S1` mutates CWD's tasklist; assert no regression.
4. `test_config_init_local_writes_config` — `tasktool config init-local` from a fresh repo writes `.tasktool/config.json` with `mutation_mode: local`, stages it, and the next `tasktool start` succeeds against CWD.
5. `test_readonly_commands_work_without_config` — `render`, `validate` (no `--normalise`), `brief`, `schema`, `show`, `phase-status`, `ready-slices`, `list`, `next-id` succeed against an unconfigured repo.
6. `test_bootstrap_init_after_init_authority` — greenfield: `tasktool config init-authority --branch main` then `tasktool init` on the same checkout creates `docs/tasklist.json` in that checkout.
7. `test_bootstrap_init_before_init_authority_fails` — greenfield: running `tasktool init` first (without authority config) fails with the migration hint.
8. `test_migrate_from_local_drifted_repo_no_config_anywhere` — repo with main checkout and a linked worktree that has divergent `docs/tasklist.json` but **no `.tasktool/config.json` in either tree**; `tasktool config migrate-from-local --authority-root <main> --accept-local` from the worktree succeeds, writes the merged tasklist to the main checkout, and writes a fresh `.tasktool/config.json` into the main checkout. This is the F1 acceptance test.
9. `test_migrate_from_local_dry_run` — divergent tasklists; `--dry-run` prints the row-level diff and writes nothing in either tree.
10. `test_migrate_from_local_accept_local_applies_deltas` — divergent `status`, `started`, `closed`, `refs`, `notes`; `--accept-local` writes them through to the authoritative tasklist; assert post-merge equality.
11. `test_migrate_from_local_accept_authoritative_noop` — `--accept-authoritative` acquires the lock, writes nothing, exits 0.
12. `test_migrate_from_local_emits_notify_events` — status transitions during migration produce notify events matching the existing fixture pattern in `tools/tasktool/tests/test_notify.py`.
13. `test_migrate_from_local_no_drift_exits_clean` — byte-identical tasklists; command exits 0 with the "no drift detected" message.
14. `test_migrate_from_local_full_field_surface` — for each row type in the model (`Project`, `Phase`, `Slice`, `Task`, `CrossCutting`, archived phase row), create a divergence on each declared dataclass field — including `blocked_on`, `planning_status`, `reviewer_chain`, `phase_reviewer_chain`, `archived_phases`, `project`, `north_star`, `last_reviewed` — and assert every field migrates through. Implementation uses `dataclasses.fields()` parameterisation so adding a new field to a row dataclass without updating the migrator's walker fails this test.
15. `test_migrate_from_local_walker_covers_all_dataclass_fields` — meta-test: introspects the migrator's known-field set against `dataclasses.fields()` on every row type; fails loudly if a model field is missing from the walker. Belt-and-braces complement to test 14.
16. `test_migrate_from_local_handles_nested_tasks` — phase with slice with tasks; task-level divergence (`status`, `notes`, `refs`) migrates correctly.

Existing tests should be audited for any that rely on the implicit-`local` default; those switch to either configuring `local` explicitly (via the new `init-local` command or a fixture that writes the config) or configuring `authoritative-checkout`, whichever matches the test's intent.

## Migration & rollout

After merge, the operator action for `multistore` (and any other repo that drifted under the old default) does **not** require `.tasktool/config.json` to exist anywhere in advance:

```
# From the drifted worktree (e.g. multistore/.worktrees/p13-s6-closeout).
# --authority-root points at the on-disk checkout that holds main.
# --local-root defaults to CWD; pass it explicitly only if running from elsewhere.

tasktool config migrate-from-local \
    --authority-root /home/simon/Dev/multistore \
    --dry-run                                            # preview the diff

tasktool config migrate-from-local \
    --authority-root /home/simon/Dev/multistore \
    --accept-local                                       # apply, capture worktree drift

# migrate-from-local writes .tasktool/config.json into the authority root if absent,
# using its current branch as the authoritative branch. Commit it alongside the
# tasklist update in the authority checkout:

git -C /home/simon/Dev/multistore add docs/tasklist.json .tasktool/config.json
git -C /home/simon/Dev/multistore commit -m "tasktool: enable authoritative routing and reconcile drift"
```

For a clean greenfield project (no drift), the bootstrap is the plain sequence — note that `init-authority` runs *before* `init`, because `init` itself routes through `_write_context`:

```
cd <repo-on-main>
tasktool config init-authority --branch main
tasktool init
git add .tasktool/config.json docs/tasklist.json
git commit -m "tasktool: initialise with authoritative routing"
```

The change is otherwise transparent for repos already running `authoritative-checkout` (this one).

## Open questions

None. Product decisions settled:

- Enforcement aggressiveness: hard error on missing config for mutating commands.
- Reconciliation approach: dedicated `migrate-from-local` subcommand with explicit `--authority-root` / `--local-root` flags, no precondition that authority config already exist.
- `local` mode opt-out: kept, surfaced as `tasktool config init-local` so the opt-out is an auditable committed artifact rather than hand-edited JSON.
