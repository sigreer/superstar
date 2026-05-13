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

1. **Run the audit.** Iterate the checks above. Build a status table.
2. **Report findings.** Present the table to the user. Use the standard `present` / `missing` / `partial` language.
3. **Offer scaffolding.** For each `missing` or `partial` item, ask the user whether to scaffold it. Allow "all", "none", or per-item selection.
4. **Apply.** For each accepted item, run the scaffold action. Use `git add -N` (intent-to-add) on new empty files so `.gitkeep`s show up in `git status` but aren't auto-staged.
5. **Verify.** Re-run the audit and confirm everything the user accepted is now `present`. Print the new table.
6. **Report.** Summarise what was created, what was skipped, and what manual action (if any) is still required — e.g. installing the reviewer command, editing the placeholder fields in `TASKLIST.md`.

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
