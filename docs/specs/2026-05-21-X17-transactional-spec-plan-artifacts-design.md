# X17 — transactional spec and plan artifact handling

**Status:** spec
**Tasktool ID:** X17 (cross-cutting)
**Date:** 2026-05-21

## Problem

The current Superstar workflow intentionally allows spec, plan, handoff, and reviewer-chain artifacts to be produced on the authoritative checkout (`main`). That is the right place for durable planning state: later agents need one canonical tasklist and one canonical set of workflow artifacts.

The failure mode is that tasktool only owns `docs/tasklist.json`. A spec/planning agent can create or revise files under `docs/specs/`, `docs/plans/`, `docs/handoffs/`, `docs/reviewer/`, and `docs/archived-tasks/`, while separately updating `docs/tasklist.json` through `tasktool create`, `tasktool ref`, `tasktool archive-phase`, or manual edits. If those files are left unstaged or only partly staged, the next routed mutation fails with:

> authoritative docs/tasklist.json has unstaged changes; commit, stash, or normalise them before running tasktool

That guard is correct. It prevents a later `tasktool start` or `tasktool close` from writing over unattributed authoritative task state. But it catches the problem late, after the checkout has already accumulated loose workflow state.

The recent X15/X16 collision is the concrete symptom: X15 spec/plan/tracker state was present in the authoritative checkout while another agent tried to run X16 lifecycle commands. Tasktool blocked the X16 mutation, but it did not provide a first-class way for the X15 planning agent to create, register, validate, stage, and optionally commit its workflow artifacts as one durable transaction.

## Goals

1. Add tasktool commands that make spec/plan/handoff/reviewer artifact registration transactional with the tasklist row they belong to.
2. Make the safe path ergonomic enough that agents do not hand-edit `docs/tasklist.json` or leave orphan dated docs behind.
3. Preserve the current model where planning artifacts live on the authoritative checkout and implementation still runs from isolated worktrees.
4. Fail early when the authoritative checkout already has unsafe tasklist or artifact dirt.
5. Update workflow skills so spec/plan agents use the new commands instead of treating artifact staging as an afterthought.

## Non-goals

- Generating spec or plan prose. Agents still write the documents; tasktool owns registration, validation, staging, and optional commit boundaries.
- Replacing external-review. Reviewer-chain generation remains owned by the external-review tooling. Tasktool only registers and validates the chain artifact after it exists.
- Auto-merging unrelated dirty state. The command refuses ambiguous checkouts rather than guessing what belongs to the current work item.
- Moving planning off `main`. This spec keeps durable planning state on the authoritative checkout by design.
- Changing implementation worktree creation or merge-back rules.

## Design

### 1. `tasktool artifact add`

Add a new mutating command:

```bash
tasktool artifact add <id> --kind spec --path docs/specs/...
tasktool artifact add <id> --kind plan --path docs/plans/...
tasktool artifact add <id> --kind handoff --path docs/handoffs/...
tasktool artifact add <id> --kind reviewer --path docs/reviewer/<chain-dir>/
tasktool artifact add <id> --kind archive --path docs/archived-tasks/...
```

Semantics:

- Routes through the configured authoritative checkout using the existing `_write_context` path.
- Refuses if the authoritative `docs/tasklist.json` has unstaged changes, using the existing unsafe-dirty guard.
- Resolves `<id>` through the same `_find_item` path used by `tasktool ref`, so short IDs behave consistently.
- Requires `--path` to be repository-relative after normalization. Absolute paths are accepted only if they resolve inside the invocation repository; they are stored as relative paths.
- Requires the target path to exist, except `--kind spec|plan|handoff --allow-missing` for the narrow case where the row is being reserved before the agent writes the file. The default is strict existence checking.
- Adds the path to `item.refs` if not already present. For phase/slice-specific model fields that already exist, it also updates the typed field:
  - `--kind spec` updates `spec_path` when the item has that field.
  - `--kind plan` updates `plan_path` when the item has that field.
  - `--kind reviewer` updates `reviewer_chain` for slices and `phase_reviewer_chain` for phases when applicable.
  - Cross-cutting items continue to use `refs` only, because they intentionally have no typed spec/plan fields today.
- Saves `docs/tasklist.json`, stages it, and stages the artifact path itself with `git add`.
- Prints the registered relative path and whether it was newly added or already present.

This command is the direct replacement for ad hoc `tasktool ref X --add <path>` during planning. `tasktool ref` remains available for generic references, but workflow skills should prefer `artifact add` for spec/plan/handoff/reviewer paths.

### 1a. Path resolution and routed writes

The command must preserve the existing tasktool distinction between invocation root and write root:

- **Invocation root**: the checkout where the user ran `tasktool`.
- **Write root**: the authoritative checkout selected by `_write_context`.
- **Stored path**: always a repository-relative POSIX path, independent of which checkout invoked the command.

Artifact paths are interpreted as follows:

1. A relative `--path` is resolved against the invocation root for user intent and validated to stay inside that checkout.
2. An absolute `--path` is accepted only if it resolves inside the invocation root.
3. The stored path is the path relative to the invocation root.
4. Existence is checked at the write root for normal planning artifacts, because durable spec/plan/handoff/reviewer artifacts are required to live on the authoritative checkout.
5. If the path exists only in a linked implementation worktree and not in the write root, `artifact add` refuses with:

   ```text
   artifact exists in invocation checkout but not authoritative checkout; create or copy it to the authoritative checkout before registering
   ```

6. Staging always happens in the write root. The command runs `git add docs/tasklist.json <stored-path>` from the write root.

This deliberately does not copy artifacts from an implementation worktree into `main`. Copying would hide the boundary that caused the original problem. Planning artifacts are authoritative workflow state; if they are meant to be durable, they must already exist in the authoritative checkout before they are registered without `--allow-missing`.

### 2. `tasktool artifact status`

Add a read-only diagnostic command:

```bash
tasktool artifact status [<id>] [--format text|json] [--strict]
```

When `<id>` is omitted, it scans the active tasklist and the workflow artifact directories. It reports:

- Referenced artifact paths that do not exist.
- Existing dated spec/plan/handoff files that are not referenced by any tasklist row.
- Reviewer-chain directories under `docs/reviewer/` that are not referenced by any row.
- Workflow artifact files that are unstaged while `docs/tasklist.json` is staged or clean.
- Referenced artifact paths for the scoped row that exist but are untracked or unstaged.
- `docs/tasklist.json` changes that are unstaged while workflow artifacts are present.

When `<id>` is supplied, the report is limited to that row and its references.

This command does not mutate. It gives agents and hooks a cheap preflight for "will this planning state surprise the next tasktool mutation?"

For row-scoped checks, `artifact status <id> --strict` must report referenced artifacts that exist but are untracked or unstaged. That includes the common sequence `prepare --spec <future-path>`, write the spec file, then forget to stage it. The diagnostic code for this case is `referenced-artifact-unstaged`, and the message must name the path plus the exact next command:

```text
referenced artifact exists but is not staged: docs/specs/...; run tasktool artifact add <id> --kind spec --path docs/specs/... or tasktool artifact commit <id> --message ...
```

Exit behavior:

- Without `--strict`, exit 0 after printing the report, even when problems are present.
- With `--strict`, exit 1 when any problem is present and exit 0 when the report is clean.
- `--format json` returns:

  ```json
  {
    "ok": false,
    "problems": [
      {
        "severity": "error",
        "code": "missing-referenced-artifact",
        "id": "X17",
        "path": "docs/specs/example.md",
        "message": "referenced artifact path does not exist"
      }
    ]
  }
  ```

Initial severities are `error` and `warning`. `--strict` fails on both unless a future flag explicitly narrows the threshold; that narrower flag is out of scope for this slice.

### 3. `tasktool artifact commit`

Add an optional transaction closeout command:

```bash
tasktool artifact commit <id> --message "X17: add transactional artifact spec"
```

Semantics:

- Routes to the authoritative checkout.
- Refuses if `docs/tasklist.json` has unstaged changes before the transaction begins.
- Checks referenced artifact paths and refuses missing references.
- Stages `docs/tasklist.json` plus every referenced existing artifact path for the row.
- Runs `artifact status <id> --strict` after staging so prepared-but-newly-written artifacts are allowed to become part of the transaction.
- Runs a target-slug orphan scan and refuses unreferenced dated artifacts that appear to belong to the same work item.
- Refuses if the staged diff contains paths outside:
  - `docs/tasklist.json`
  - `.tasktool/config.json`
  - `docs/specs/`
  - `docs/plans/`
  - `docs/handoffs/`
  - `docs/reviewer/`
  - `docs/archived-tasks/`
- Creates a git commit with the supplied message.
- Does not push.

The ordering is intentional. `artifact commit` is allowed to remediate `referenced-artifact-unstaged` by staging referenced existing artifacts itself. It still refuses missing references, unrelated staged paths, and post-staging strict-status problems.

This is deliberately separate from `artifact add`. Some agents may need multiple review iterations before committing. The important property is that tasktool can now close the planning transaction when the spec/plan/review bundle is ready.

Target-slug matching is deterministic:

- The command derives the target slug from the first referenced spec or plan filename for the row by removing the leading `YYYY-MM-DD-` date and the leading task ID segment, then removing a trailing `-design` for specs and `-prompt` for handoffs.
- For `docs/reviewer/`, it treats directories containing that slug and the review kind suffix as belonging to the row.
- For `docs/specs/`, `docs/plans/`, and `docs/handoffs/`, it treats dated filenames containing both the row ID and the target slug as belonging to the row.
- For `docs/archived-tasks/`, it only considers paths explicitly referenced by the row. Phase archive generation remains owned by `archive-phase`; archive files are not guessed from slug alone.

If no target slug can be derived, `artifact commit` skips slug-based orphan refusal and relies on `artifact status <id> --strict` plus the staged-path allowlist. This keeps commit safe without making old or unusual task rows uncommittable.

### 4. `tasktool prepare` as a convenience wrapper

Add a higher-level command for the common "mint row and register artifacts" case:

```bash
tasktool prepare cross \
  --title "Make spec and plan artifact handling transactional" \
  --spec docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md \
  --plan docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md \
  --handoff docs/handoffs/2026-05-21-X17-transactional-spec-plan-artifacts-prompt.md
```

Full grammar:

```bash
tasktool prepare cross --title <title> [--spec <path>] [--plan <path>] [--handoff <path>]
tasktool prepare phase --title <title> [--spec <path>] [--plan <path>] [--handoff <path>]
tasktool prepare slice <phase-id> --title <title> [--plan <path>] [--handoff <path>]
tasktool prepare existing <id> [--spec <path>] [--plan <path>] [--handoff <path>]
```

There is no top-level `--id` mode. Existing-row registration is always `prepare existing <id>` so the CLI grammar stays unambiguous.

`prepare` is a composition of existing tasktool operations:

1. Create the row (`create cross`, `create phase`, or `create slice`) if an ID was not supplied.
2. Register the supplied artifact paths using `artifact add --allow-missing`.
3. Stage `docs/tasklist.json`.
4. Print the new ID and the exact files the agent must create next.

`prepare` does not create empty spec/plan files by default. Empty docs look valid to filesystem checks while containing no useful contract. If a future workflow wants templates, that can be a separate flag with explicit template content.

### 5. Skill updates

Update these skills:

- `skills/brainstorming/SKILL.md`: before writing a spec, create or prepare the tasktool row using `tasktool prepare` or `tasktool create` + `tasktool artifact add --kind spec --allow-missing`. After writing the spec file, rerun `tasktool artifact add --kind spec --path <spec>` so the now-existing artifact is staged. After spec review passes, run `tasktool artifact add --kind reviewer` for the spec reviewer chain, then close the spec transaction with `tasktool artifact commit <id> --message "<id>: add <slug> spec"`.
- `skills/writing-plans/SKILL.md`: before writing the plan/handoff, register the intended paths with `tasktool artifact add --allow-missing`; after writing the plan and handoff, rerun `tasktool artifact add` for both existing files so they are staged. After review passes, register the plan reviewer chain and close the planning transaction with `tasktool artifact commit <id> --message "<id>: add <slug> plan"`.
- `skills/tasklist-discipline/SKILL.md`: document that spec/plan/handoff/reviewer paths are workflow artifacts and should be registered through `tasktool artifact`, not generic refs or manual JSON edits.
- `skills/external-review/SKILL.md`: after a successful spec/plan review, register the reviewer-chain directory with `tasktool artifact add --kind reviewer` when `docs/tasklist.json` exists.

The skills should still commit according to the existing workflow. The new command gives them a deterministic staging and validation surface; it does not remove the need for commits.

## Component boundaries

- `tools/tasktool/artifacts.py` owns path classification, row-artifact mapping, orphan detection, and staging path calculation.
- `tools/tasktool/commands.py` owns command orchestration and reuse of `_write_context`, `_find_item`, `_save`, and `_git_stage`.
- `tools/tasktool/cli.py` owns argument parsing for `artifact` and `prepare`.
- `tools/tasktool/tests/test_artifacts.py` covers pure path/status logic.
- `tools/tasktool/tests/test_artifact_cli.py` covers command behavior through the CLI.

Keeping path classification in a small module avoids growing `commands.py` into a mixed CLI, model, and filesystem-policy file.

## Error handling

- Unknown ID: reuse existing `cross-cutting X not found` / `phase not found` style errors from `_find_item`.
- Path outside repository: `artifact path is outside repository: <path>`.
- Missing path without `--allow-missing`: `artifact path does not exist: <path>`.
- Path exists only in the invocation worktree during a routed mutation: `artifact exists in invocation checkout but not authoritative checkout; create or copy it to the authoritative checkout before registering`.
- Unsupported path for kind: `spec artifacts must live under docs/specs/`, `plan artifacts must live under docs/plans/`, and equivalent messages for handoff/reviewer/archive.
- Unsafe authoritative tasklist dirt: preserve the existing tasktool error.
- `artifact commit` with unrelated staged files: print the disallowed paths and refuse.
- `prepare existing <id>` with create-only options such as `--title`: refuse with a usage error.
- `prepare slice` without `<phase-id>`: argparse usage error.

## Testing

Add focused pytest coverage:

1. `artifact add` registers a spec path for an existing cross-cutting row, stages `docs/tasklist.json`, and stages the spec file.
2. `artifact add --allow-missing` registers a future spec path and stages only `docs/tasklist.json`.
3. `artifact add` rejects paths outside the repo.
4. `artifact add --kind plan` rejects files outside `docs/plans/`.
5. `artifact add --kind reviewer` accepts a directory under `docs/reviewer/` and registers it in `refs`.
6. `artifact status` reports unreferenced dated spec/plan/handoff files.
7. `artifact status <id>` reports missing referenced files for that row.
8. `artifact status` exits non-zero when run with `--strict` and problems are present.
9. `artifact commit <id>` stages only allowed workflow paths and creates a commit.
10. `artifact commit <id>` refuses unrelated staged code changes.
11. `prepare cross --title ... --spec ...` allocates the next X ID and registers intended artifact refs without creating empty files.
12. `prepare existing X17 --spec ... --plan ...` registers artifacts against an existing row without allocating a new ID.
13. Authority routing: running `artifact add` from a linked implementation worktree mutates and stages the authoritative checkout, not the worktree copy.
14. Unsafe-dirty guard: `artifact add` refuses when authoritative `docs/tasklist.json` has unstaged bytes.
15. Routed path safety: running `artifact add` from a linked worktree where the artifact exists only in the worktree refuses with the explicit invocation-only artifact error.
16. Prepared future artifact closeout: `prepare cross --spec docs/specs/future.md`, then creating `future.md`, then running `artifact status <id> --strict` reports `referenced-artifact-unstaged` until `artifact add <id> --kind spec --path docs/specs/future.md` or `artifact commit <id> --message ...` stages it.

Run gates:

```bash
PYTHONPATH=tools pytest tools/tasktool/tests -q
tools/tasktool/tasktool validate --strict-format
git diff --check
```

## Migration and rollout

This is additive. Existing refs remain valid. No existing tasklist schema migration is required.

After the command ships, planning agents should use this sequence:

```bash
tasktool prepare cross \
  --title "<title>" \
  --spec docs/specs/YYYY-MM-DD-XNN-slug-design.md

# write spec, then stage the now-existing referenced artifact:
tasktool artifact add XNN --kind spec --path docs/specs/YYYY-MM-DD-XNN-slug-design.md

# run review, then:
tasktool artifact add XNN --kind reviewer --path docs/reviewer/<spec-chain>/
tasktool artifact status XNN --strict
tasktool artifact commit XNN --message "XNN: add <slug> spec"

# write plan + handoff, run plan review, then:
tasktool artifact add XNN --kind plan --path docs/plans/YYYY-MM-DD-XNN-slug.md
tasktool artifact add XNN --kind handoff --path docs/handoffs/YYYY-MM-DD-XNN-slug-prompt.md
tasktool artifact add XNN --kind reviewer --path docs/reviewer/<plan-chain>/
tasktool artifact status XNN --strict
tasktool artifact commit XNN --message "XNN: add <slug> plan"
```

Once skills adopt the sequence, loose spec/plan/reviewer artifacts on `main` become a visible status failure instead of hidden ambient state.

## Open questions

None. The design chooses explicit tasktool ownership of workflow artifact registration, while leaving prose generation and external-review behavior in their existing tools.
