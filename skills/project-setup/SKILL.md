---
name: project-setup
description: Use when the user says "init project for superstar", "set up this project", or similar. Audits the current repo for the conventions the other skills depend on (docs/tasklist.json, doc dirs, reviewer CLI, pre-commit hook) and offers to scaffold anything missing.
---

# Project Setup

Audit the current repo against the conventions the rest of the superstar skills depend on, then offer to scaffold whatever is missing. The checks are deliberately additive — running this skill on an already-set-up project is a no-op.

**Announce at start:** "I'm using the project-setup skill to audit this project for superstar conventions."

## When to use

- User explicitly asks: "init project for superstar", "set up this project for superstar", "superstar setup", etc.
- A skill discovers a missing convention mid-flow (e.g. `[[tasklist-discipline]]` asked to update `docs/tasklist.json` via tasktool but the file is absent) and the user asks to scaffold it.
- A new fork or new repo where the planning/review workflow has never been used.

Do **not** invoke automatically. The user must request it.

## What the skill checks

For each check the skill must report **status** (`present` / `missing` / `partial`) and, when missing or partial, **offer to scaffold it**. Always ask before writing. Never modify existing files without confirmation.

| # | Check                                                    | Pass criteria                                                          | Scaffold action                                                              |
|---|----------------------------------------------------------|------------------------------------------------------------------------|------------------------------------------------------------------------------|
| 0 | Local git repo                                           | `git rev-parse --is-inside-work-tree` succeeds.                        | `git init` before installing hooks or running git-backed verification.        |
| 1 | `docs/tasklist.json`                                     | File exists and validates clean (`tools/tasktool/tasktool validate`, or `tasktool validate` when the global shim is installed). | Run `tools/tasktool/tasktool config init-authority --branch <main-branch>` first, then `tools/tasktool/tasktool init --project <name>`. |
| 1a| `.tasktool/config.json` authoritative routing             | File exists with `tasklist.mutation_mode` set to `authoritative-checkout` for the repo's main branch. Missing or unconfigured authority is a setup precondition failure, the same as a missing tasklist. | `tools/tasktool/tasktool config init-authority --branch <main-branch>` from the authoritative checkout before `tasktool init`. |
| 1b| `.git/hooks/pre-commit` (tasktool hook)                  | Tasktool hook installed (`grep -q 'tasktool-pre-commit-hook' .git/hooks/pre-commit`). | `bash tools/tasktool/install.sh --hook` (or the equivalent for non-superstar repos). |
| 1c| Legacy `docs/TASKLIST.md` import decision                | If `docs/TASKLIST.md` exists, the user has explicitly chosen `tasktool import docs/TASKLIST.md --project <name>` or chosen to start with a new empty tracker. | Show `tools/tasktool/tasktool import docs/TASKLIST.md --dry-run --project <name>`, surface warnings, then ask whether to import, start empty, or stop. |
| 1d| Implementation worktree location                         | `git check-ignore -q .worktrees/` succeeds (or the repo's explicit worktree directory such as `worktrees/` succeeds). | Add `.worktrees/` to `.gitignore` (create the file if needed). Do not create per-slice worktrees here; `[[using-git-worktrees]]` owns that. |
| 2 | `docs/specs/` directory                                  | Directory exists.                                                      | `mkdir -p docs/specs` and add a `.gitkeep`.                                  |
| 3 | `docs/plans/` directory                                  | Directory exists.                                                      | `mkdir -p docs/plans` and add a `.gitkeep`.                                  |
| 4 | `docs/handoffs/` directory                               | Directory exists.                                                      | `mkdir -p docs/handoffs` and add a `.gitkeep`.                               |
| 5 | `docs/reviewer/` directory                               | Directory exists (chain folders land here).                            | `mkdir -p docs/reviewer` and add a `.gitkeep`.                               |
| 6 | `docs/archived-tasks/` directory                         | Directory exists (phase-close target).                                 | `mkdir -p docs/archived-tasks` and add a `.gitkeep`.                         |
| 7 | Global `external-reviewer` bridge available | `command -v external-reviewer` succeeds and `external-reviewer --help` exits 0. | Run or print `bash <active-superstar-checkout>/skills/external-review/install.sh` after confirmation. |
| 8 | Reviewer command available                               | `AGENT_REVIEWER_CMD` (env) is set, or the default `reviewer-agent` is on `PATH`. | Print the exact command to install `skills/project-setup/scripts/reviewer-agent` to a user-chosen bin dir, or the exact `AGENT_REVIEWER_CMD` override. Do **not** install third-party tools or edit shell config without confirmation. The wrapper must not use provider bypass/no-sandbox flags. |
| 9 | CLAUDE.md mentions superstar planning discipline | The repo's CLAUDE.md (or AGENTS.md / GEMINI.md) references the skill set. | Append a small "Planning & implementation discipline" block referencing `brainstorming`, `writing-plans`, `subagent-driven-development`, `external-review`, `tasklist-discipline`. |

**Safe reviewer wrapper.** The bundled template at `skills/project-setup/scripts/reviewer-agent` is the default recommendation. It expects `external-reviewer.py` to pass `AGENT_REVIEWER_PROVIDER`, `AGENT_REVIEWER_REPO_ROOT`, `AGENT_REVIEWER_RESPONSE_DIR`, `AGENT_REVIEWER_SCRATCH_DIR`, and `AGENT_REVIEWER_TARGET_FILE`. Do not recommend wrappers that call Codex with `--dangerously-bypass-approvals-and-sandbox` or Claude with `--dangerously-skip-permissions`.

## The process

1. **Legacy detection.** Scan for upstream `superpowers` artefacts (see "Legacy migration" below). If any are present, run that flow **before** the standard audit so the audit sees the migrated layout, not the legacy one.
2. **Run the audit.** Iterate the checks above. Build a status table.
3. **Report findings.** Present the table to the user. Use the standard `present` / `missing` / `partial` language.
4. **Offer scaffolding.** For each `missing` or `partial` item, ask the user whether to scaffold it. Allow "all", "none", or per-item selection.
5. **Apply.** For each accepted item, run the scaffold action. Use `git add -N` (intent-to-add) on new empty files so `.gitkeep`s show up in `git status` but aren't auto-staged.
6. **Verify.** Re-run the audit and confirm everything the user accepted is now `present`. Include `git check-ignore -q .worktrees/` in verification when the worktree-location row is accepted. Print the new table.
7. **Run the setup boundary.** Follow "Setup boundary before implementation" below.
8. **Report.** Summarise what was created, what was skipped, what must be committed or stashed before feature work, and what manual action (if any) is still required — e.g. installing the reviewer command, importing `docs/TASKLIST.md`, populating the north-star or first phase title via `tasktool create`.

## Setup Boundary Before Implementation

Setup is its own change. Do not continue into `[[brainstorming]]`, `[[writing-plans]]`, `[[subagent-driven-development]]`, or `[[external-review]]` while migration/scaffold artifacts are still mixed with feature work.

After any accepted scaffold or legacy migration:

1. Run `git status --short` and classify every dirty path as one of:
   - setup/migration (`docs/tasklist.json`, `.gitignore` worktree-ignore entries, `docs/specs/`, `docs/plans/`, `docs/handoffs/`, `docs/reviewer/`, `docs/archived-tasks/`, global `external-reviewer` shim installation, `.git/hooks/pre-commit`, `CLAUDE.md` / `AGENTS.md` / `GEMINI.md`, legacy `docs/superpowers/` moves);
   - feature implementation;
   - local noise or user-owned changes.
2. Confirm `.tasktool/config.json` exists and names `authoritative-checkout` routing for the repo's main branch. If it is missing or lacks `tasklist.mutation_mode`, run `tools/tasktool/tasktool config init-authority --branch <main-branch>` from the authoritative checkout before any `tasktool init` or other mutating command.
3. Run `tools/tasktool/tasktool validate` when the repo-local launcher exists, otherwise `tasktool validate`.
4. If `docs/TASKLIST.md` exists, stop until the user chooses one path:
   - import it with `tools/tasktool/tasktool import docs/TASKLIST.md --project <name>` after first showing `--dry-run` output;
   - start with an empty tracker and leave/delete the legacy file by explicit user choice;
   - stop setup.
5. If migration moved dated historical files into `docs/specs/` or `docs/plans/`, dry-run the orphan check before any commit:
   ```bash
   TASKTOOL=tasktool
   test -x tools/tasktool/tasktool && TASKTOOL=tools/tasktool/tasktool
   git diff --name-only --diff-filter=ACMR -- docs/specs docs/plans |
     grep -E '^docs/(specs|plans)/[0-9]{4}-[0-9]{2}-[0-9]{2}-' |
     xargs -r "$TASKTOOL" validate --check-orphans
   ```
   If this fails, do not press on. Ask the user whether to import matching IDs, keep those historical docs outside orphan-checked paths, or defer tracking `docs/tasklist.json`.
6. Stop at the boundary. Ask the user to choose one of:
   - commit the setup/migration as a standalone setup commit;
   - stash/shelve it;
   - leave it dirty and pause feature work.

Do not run post-slice or post-phase review until this boundary is resolved. Reviewers correctly treat unrelated setup artifacts, untracked reviewer scripts, copied chain outputs, and legacy path moves as ambiguous scope.

## Legacy migration (when superpowers artefacts are present)

Run this **before** the standard audit. **All of the heavy lifting is performed by a Python script** at `skills/project-setup/scripts/migrate-from-superpowers.py`. The skill's job is to detect, ask the two questions, and invoke the script with the right flags. **Do not freestyle the migration logic.** The script is the single source of truth for the mapping table, file enumeration, and rewrite rules; deviating from it risks inconsistent state across projects.

### Detection

A single dry-run invocation is the cheapest detection mechanism:

```bash
python3 skills/project-setup/scripts/migrate-from-superpowers.py --emit=json
```

The JSON output has two keys to gate on:

- `paths.has_legacy_dir` — `true` if `docs/superpowers/` exists.
- `refs` — non-empty object if any `superpowers:` / `obra/superpowers` / `superpowers@…` references remain.

If both are empty, skip the migration flow entirely. Otherwise, present the findings to the user and proceed to Q1/Q2.

### Simplification — no per-file prompting

Loose files at the root of `docs/superpowers/` (kickoff notes, handoff scratch) are **always** moved to `docs/` alongside the rest. No per-file dialog; the script enumerates them and routes them deterministically. If the user wants to delete any of them, they do that themselves after the migration. This keeps the flow predictable.

### Question 1 — what to do with the legacy artefacts

| Choice            | Script flag             | Action                                                                                                                            |
|-------------------|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| **Migrate fully** | `--paths=migrate`       | `git mv` `specs/` and `plans/` subtrees to their canonical destinations; `git mv` loose files into `docs/`; `rmdir docs/superpowers/` once empty. |
| **Duplicate**     | `--paths=duplicate`     | `cp -r` everything into the new locations, `git add -N` the copies. Originals left in place.                                      |
| **Do nothing**    | `--paths=nothing`       | Leave the legacy paths untouched.                                                                                                 |

### Question 2 — what to do with references to those paths

| Choice                | Script flag        | Action                                                                                                                            |
|-----------------------|--------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| **Update references** | `--refs=update`    | In-place rewrite per the canonical mapping (all file types, not just `.md`). Trailing-slash form `docs/superpowers/` only — bare references without trailing slash are flagged in the summary but not rewritten. |
| **List references**   | `--refs=list`      | Print a per-file occurrence table. No writes. User decides what to do out of band.                                                |
| **Leave alone**       | `--refs=nothing`   | Don't touch references. Apply Q1's choice only.                                                                                   |

### Canonical mapping (defined in the script)

The script applies these substitutions, in this order. The skill does not duplicate this list — it is documented here for human reference only:

1. `docs/superpowers/specs/` → `docs/specs/`
2. `docs/superpowers/plans/` → `docs/plans/`
3. `docs/superpowers/` → `docs/`
4. `superpowers:requesting-code-review` → `superstar:requesting-internal-review`
5. `superpowers:receiving-code-review` → `superstar:receiving-internal-review`
6. `superpowers:using-superpowers` → `superstar:using-superstar`
7. `superpowers:` → `superstar:` (catch-all for other skills)
8. `obra/superpowers` → `sigreer/superstar`
9. `superpowers@` → `superstar@`

Trailing-slash form for path rewrites avoids mangling hyphenated filenames like `docs/superpowers-old.md`. Bare references without trailing slash (e.g. `[link](docs/superpowers)`) are not rewritten automatically — they're rare and the user can clean them up after the migration.

The script exempts a small set of files from rewriting so historical/definitional references aren't corrupted: the script itself, `skills/project-setup/SKILL.md`, `RELEASE-NOTES.md`, and `CHANGELOG.md`.

### Applying the migration

After **both** answers are in:

1. **Show the dry-run summary.** Re-run the script without `--apply`, with the user's chosen `--paths` and `--refs` values:
   ```bash
   python3 skills/project-setup/scripts/migrate-from-superpowers.py \
       --paths=<choice> --refs=<choice>
   ```
   Surface the output to the user.
2. **Confirm once more** if Q1 = `migrate` or Q2 = `update`. (Duplicate / list / nothing are non-destructive — no second confirm needed.)
3. **Apply.** Re-run the same command with `--apply` appended:
   ```bash
   python3 skills/project-setup/scripts/migrate-from-superpowers.py \
       --apply --paths=<choice> --refs=<choice>
   ```
4. **Re-run the standard audit** so the regular table reflects the post-migration state. The migration may have satisfied items 2–6 of the checklist (`docs/specs/`, `docs/plans/` etc. now exist).
5. **Run the setup boundary.** Legacy path moves and reference rewrites must be committed or shelved separately before implementation work starts.

### Rules

- **Never reimplement the migration in shell or inline edits.** Always shell out to the script. It is the single source of truth.
- Never run `--apply` without first showing the dry-run summary.
- The script handles its own exclusions (`.git/`, gitignored paths, binaries, exempt files). Do not pre-filter or duplicate that logic.
- If the script reports that `docs/superpowers/` is non-empty after a `migrate` run (rare — would indicate an unexpected file type or permission issue), surface the warning to the user instead of pressing on.
- Do not treat migrated `docs/specs/` or `docs/plans/` files as harmless docs churn. Once `docs/tasklist.json` is tracked, the pre-commit hook checks dated spec/plan filenames against task IDs; historical migrated files can be orphaned and must be resolved at the setup boundary.

## Extending the checklist

When new project-mechanics conventions are introduced anywhere in the superstar skill set, add a row to the table above. Each row must specify:

- **Pass criteria** — an exact condition (file path, command, env var) that can be checked deterministically.
- **Scaffold action** — what to write/create, or which template to copy from. If a scaffold needs user input (a project name, a slug), the skill must prompt for it before writing.

Order rows by dependency: a row that scaffolds a directory must precede a row that fills it.

## Hard rules

- **Never modify existing files** without explicit confirmation, even if the content looks stale.
- **Never install third-party tools** (Python packages, CLI binaries) without confirmation. Print the install command and ask.
- **Never run the scaffold blindly.** Always show the audit table first, then ask per-item or "all".
- **Never set `AGENT_REVIEWER_CMD` in the user's shell config.** Suggest the value; let them install it themselves.

## Red flags

| Thought                                                        | Reality                                                                |
|----------------------------------------------------------------|------------------------------------------------------------------------|
| "`docs/tasklist.json` is missing, I'll just create it"         | Run the audit, present the table, ask. Configure authority with `tasktool config init-authority --branch <main-branch>` before `tasktool init`, and don't run either without consent. |
| "The user said 'set up everything', skip the confirmations"   | Confirm the *list* once, then proceed. Don't write files without showing what.|
| "AGENT_REVIEWER_CMD is unset, I'll edit their shell rc"        | Out of scope. Print the suggested value and stop.                      |
| "Existing CLAUDE.md is fine, I'll rewrite it cleaner"          | No. Append a section if needed; never rewrite.                         |

## Integration

- `[[tasklist-discipline]]` — describes tasktool conventions; the CLI itself ships the canonical scaffold via `tools/tasktool/tasktool init`.
- `[[external-review]]` — provides the global bridge command contract and the `AGENT_REVIEWER_CMD` expectation.
- `[[writing-plans]]` — relies on the `docs/specs/`, `docs/plans/`, `docs/handoffs/` tree.
- `[[subagent-driven-development]]` — relies on `docs/reviewer/` for chain folders.
