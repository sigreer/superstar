---
name: project-setup
description: Use when the user says "init project for superstar", "set up this project", or similar. Audits the current repo for the conventions the other skills depend on (TASKLIST.md, doc dirs, reviewer CLI, hooks) and offers to scaffold anything missing.
---

# Project Setup

Audit the current repo against the conventions the rest of the superstar skills depend on, then offer to scaffold whatever is missing. The checks are deliberately additive — running this skill on an already-set-up project is a no-op.

**Announce at start:** "I'm using the project-setup skill to audit this project for superstar conventions."

## When to use

- User explicitly asks: "init project for superstar", "set up this project for superstar", "superstar setup", etc.
- A skill discovers a missing convention mid-flow (e.g. `[[tasklist-discipline]]` asked to update TASKLIST.md but the file is absent) and the user asks to scaffold it.
- A new fork or new repo where the planning/review workflow has never been used.

Do **not** invoke automatically. The user must request it.

## What the skill checks

For each check the skill must report **status** (`present` / `missing` / `partial`) and, when missing or partial, **offer to scaffold it**. Always ask before writing. Never modify existing files without confirmation.

| # | Check                                                    | Pass criteria                                                          | Scaffold action                                                              |
|---|----------------------------------------------------------|------------------------------------------------------------------------|------------------------------------------------------------------------------|
| 1 | `docs/TASKLIST.md`                                       | File exists with the standard header + status legend.                  | Copy from `skills/tasklist-discipline/templates/TASKLIST.template.md`, fill in `<project-name>` and the current date. |
| 2 | `docs/specs/` directory                                  | Directory exists.                                                      | `mkdir -p docs/specs` and add a `.gitkeep`.                                  |
| 3 | `docs/plans/` directory                                  | Directory exists.                                                      | `mkdir -p docs/plans` and add a `.gitkeep`.                                  |
| 4 | `docs/handoffs/` directory                               | Directory exists.                                                      | `mkdir -p docs/handoffs` and add a `.gitkeep`.                               |
| 5 | `docs/reviewer/` directory                               | Directory exists (chain folders land here).                            | `mkdir -p docs/reviewer` and add a `.gitkeep`.                               |
| 6 | `docs/archived-tasks/` directory                         | Directory exists (phase-close target).                                 | `mkdir -p docs/archived-tasks` and add a `.gitkeep`.                         |
| 7 | `scripts/external-reviewer.py`                           | Either present at the repo root, or `AGENT_REVIEWER_CMD` is set.       | Copy from `skills/external-review/scripts/external-reviewer.py`, `chmod +x`. |
| 8 | Reviewer command available                               | `AGENT_REVIEWER_CMD` (env) is set, or the default `reviewer-agent` is on `PATH`. | Print the exact env-var or wrapper-install instruction; do **not** install third-party tools without confirmation. |
| 9 | CLAUDE.md mentions superstar planning discipline | The repo's CLAUDE.md (or AGENTS.md / GEMINI.md) references the skill set. | Append a small "Planning & implementation discipline" block referencing `brainstorming`, `writing-plans`, `subagent-driven-development`, `external-review`, `tasklist-discipline`. |

## The process

1. **Legacy detection.** Scan for upstream `superpowers` artefacts (see "Legacy migration" below). If any are present, run that flow **before** the standard audit so the audit sees the migrated layout, not the legacy one.
2. **Run the audit.** Iterate the checks above. Build a status table.
3. **Report findings.** Present the table to the user. Use the standard `present` / `missing` / `partial` language.
4. **Offer scaffolding.** For each `missing` or `partial` item, ask the user whether to scaffold it. Allow "all", "none", or per-item selection.
5. **Apply.** For each accepted item, run the scaffold action. Use `git add -N` (intent-to-add) on new empty files so `.gitkeep`s show up in `git status` but aren't auto-staged.
6. **Verify.** Re-run the audit and confirm everything the user accepted is now `present`. Print the new table.
7. **Report.** Summarise what was created, what was skipped, and what manual action (if any) is still required — e.g. installing the reviewer command, editing the placeholder fields in `TASKLIST.md`.

## Legacy migration (when superpowers artefacts are present)

Run this **before** the standard audit. The flow is a two-question dialogue. **Do not take any action until both answers are collected.**

### Detection

Scan for any of the following — surface a hit only if at least one is found:

| Signal                                                              | How to find it                                                            |
|---------------------------------------------------------------------|---------------------------------------------------------------------------|
| `docs/superpowers/` directory                                       | `test -d docs/superpowers`                                                |
| Intermediate fork tree `docs/amazingabilities/` (rare)             | `test -d docs/amazingabilities`                                           |
| `superpowers:<skill>` namespace references                          | `grep -rn 'superpowers:' .` (with the standard exclusions below)          |
| Plugin-name references (`obra/superpowers`, `superpowers@…`)        | `grep -rin 'obra/superpowers\|superpowers@' .`                            |
| `Superpowers` mentioned in CLAUDE.md / AGENTS.md / GEMINI.md        | `grep -lin 'superpowers' CLAUDE.md AGENTS.md GEMINI.md 2>/dev/null`       |

**Scope:** all files in the working tree, regardless of extension. References to `superpowers` can land in JSON, shell scripts, env files, YAML configs, etc. — not just markdown. Apply only the standard exclusions: `.git/`, `node_modules/`, `dist/`, `build/`, anything matched by `.gitignore`, and binary files (grep's default `-I` behaviour, or `git grep` which already skips binaries).

Report all hits as one combined finding. Do not act yet.

### Question 1 — what to do with the legacy artefacts

Before asking, **enumerate the full contents of `docs/superpowers/`** (`find docs/superpowers -type f`) and bucket each entry:

| Bucket                              | Auto-route to              | Example                                |
|-------------------------------------|----------------------------|----------------------------------------|
| `docs/superpowers/specs/**`         | `docs/specs/**`            | `…/specs/2026-05-09-p9-…-design.md`    |
| `docs/superpowers/plans/**`         | `docs/plans/**`            | `…/plans/2026-05-09-p9-….md`           |
| Anything else under `docs/superpowers/` | **Unknown — ask the user.** | `docs/superpowers/p3-execution-kickoff.md`, loose handoff notes, README scratch files |

Loose files are common (kickoff notes, handoff prompts that predated `docs/handoffs/`, ad-hoc README scratch). If any exist, include them in the dry-run summary with a per-file prompt: move to `docs/specs/`, `docs/plans/`, `docs/handoffs/`, `docs/`, leave in place, or delete. **Never silently route an unknown file.** Resolve every loose file before applying Q1.

Then ask the user to pick one. Present all three options regardless of which signals were detected:

| Choice            | Action                                                                                                                            |
|-------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| **Duplicate**     | Copy `docs/superpowers/specs/` → `docs/specs/`, `docs/superpowers/plans/` → `docs/plans/`, and per-file copies for loose files per the per-file prompt. Leave originals in place. |
| **Migrate fully** | `git mv` everything per the auto-route table + per-file resolutions. Once `docs/superpowers/` is empty, `rmdir` it. If any loose file was left in place or its parent is non-empty for any reason, leave the tree alone and report it.|
| **Do nothing**    | Leave the legacy paths untouched.                                                                                                 |

### Question 2 — what to do with references to those paths

Ask the user to pick one. This question is asked **after** Q1 is answered but **before** any action is taken on either:

| Choice                | Action                                                                                                                            |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| **Update references** | Grep the entire working tree (all extensions, not just `*.md`) for old paths and the `superpowers:` namespace; rewrite each in place per the mapping table below. |
| **List references**   | Print a `file:line` table of every reference. Do not write. User decides per-file out of band.                                    |
| **Leave alone**       | Don't touch references. Apply Q1's choice only.                                                                                   |

The rewrite covers **all file types** — markdown, JSON, YAML, shell scripts, env files, code comments. Do not narrow to `*.md`. Apply only the standard exclusions (`.git/`, `node_modules/`, `dist/`, `build/`, gitignored paths, binary files). Do not stop to ask whether non-markdown files are in scope — they always are.

### Mapping from old to new

When applying either Q1=Migrate or Q2=Update, use exactly this mapping. Never invent new mappings:

| Old                                        | New                                              |
|--------------------------------------------|--------------------------------------------------|
| `docs/superpowers/specs/`                  | `docs/specs/`                                    |
| `docs/superpowers/plans/`                  | `docs/plans/`                                    |
| `superpowers:requesting-code-review`       | `superstar:requesting-internal-review`           |
| `superpowers:receiving-code-review`        | `superstar:receiving-internal-review`            |
| `superpowers:using-superpowers`            | `superstar:using-superstar`                      |
| `superpowers:<other-skill>`                | `superstar:<other-skill>` (one-for-one rename)   |
| `obra/superpowers` / `superpowers@*`       | `sigreer/superstar` / `superstar@*`              |

### Applying the migration

After **both** answers are in:

1. **Print a dry-run summary.** Show every path that will be created/moved/deleted and every file whose contents will be rewritten (counts + sample line). One section per action.
2. **Confirm once more** if Q1 ∈ {Migrate} or Q2 = Update. (Duplicate + List + Leave alone are non-destructive — no second confirm needed.)
3. **Apply.**
   - Path moves: `git mv` to preserve history.
   - Path duplicates: `cp -r` (and `git add -N` the new paths).
   - Reference rewrites: in-place `sed`, scoped to the file list grepped earlier. Never re-grep mid-apply.
4. **Re-run the standard audit** so the regular table reflects the post-migration state. The migration may have satisfied items 2–6 of the checklist (the `docs/specs/`, `docs/plans/` etc. directories now exist).

### Rules

- Never delete legacy paths when Q1 ∈ {Duplicate, Do nothing}.
- Never modify references when Q2 = Leave alone.
- Never run the reference rewrite without showing the dry-run summary first.
- Skip files in `.git/`, `node_modules/`, `dist/`, `build/`, and any path matching `.gitignore` patterns.
- If the user picked Migrate but the old tree has files newer than their `docs/specs/` counterparts (rare — would indicate prior partial migration), surface a conflict report and ask before overwriting.

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
| "TASKLIST.md is missing, I'll just create it"                  | Run the audit, present the table, ask. Don't write without consent.    |
| "The user said 'set up everything', skip the confirmations"   | Confirm the *list* once, then proceed. Don't write files without showing what.|
| "AGENT_REVIEWER_CMD is unset, I'll edit their shell rc"        | Out of scope. Print the suggested value and stop.                      |
| "Existing CLAUDE.md is fine, I'll rewrite it cleaner"          | No. Append a section if needed; never rewrite.                         |

## Integration

- `[[tasklist-discipline]]` — provides the TASKLIST.md template.
- `[[external-review]]` — provides the reviewer script and the `AGENT_REVIEWER_CMD` expectation.
- `[[writing-plans]]` — relies on the `docs/specs/`, `docs/plans/`, `docs/handoffs/` tree.
- `[[subagent-driven-development]]` — relies on `docs/reviewer/` for chain folders.
