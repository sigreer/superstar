# X31 — Tasktool Janitor Skill Design

**Status:** spec
**Work row:** `X31` — Tasktool janitor cleanup skill
**Canonical source:** top-level `skills/`; generated plugin mirrors are implementation/publish outputs, not hand-edited sources.

## Problem

Superstar-managed repos accumulate open cross-cutting rows as phases finish, plans change, and follow-up work gets superseded. Cleaning those rows is deceptively risky: a stale title can look obsolete even when source, docs, or reviewer chains prove the work is still live; a row can be old without being abandoned; and a single coordinator reviewing twenty unrelated rows in one context is likely to flatten evidence into guesses.

The repo already has `tasklist-discipline` for tasktool lifecycle rules and `dispatching-parallel-agents` for independent investigations. What is missing is a reusable on-demand cleanup skill that teaches agents how to run tracker janitorial work: start read-only, split row audits into bounded worker assignments, require a per-row evidence dossier, reconcile recommendations conservatively, ask the user before mutation, and only then apply approved `tasktool` commands in small validated batches.

The motivating validation repo is `/home/simon/Dev/sigreer/multistore`, where many open `X*` cross-cutting rows need careful cleanup. The new skill must remain generic across Superstar/tasktool repos and must not hard-code multistore phases, paths, or row IDs.

## Goals

- Add a new on-demand Superstar skill named `tasktool-janitor`.
- Trigger for prompts such as "clean up the tasktool crosscuts using janitor skill", "audit stale X rows", or "review open cross-cutting/phase/slice cleanup candidates".
- Specialize tracker cleanup methodology without duplicating all of `tasklist-discipline`.
- Make evidence dossiers the mandatory output unit for each reviewed row.
- Coordinate worker agents for heterogeneous or large row sets instead of letting one context bulk-review everything.
- Prevent mutation until the coordinator has presented grouped recommendations and received user approval.
- Preserve a durable audit trail for substantial cleanup unless the user explicitly requests chat-only output.

## Non-Goals

- No new `tasktool` subcommands or data model changes.
- No automatic bulk close/cancel behavior.
- No project-specific multistore logic.
- No replacement for `tasklist-discipline`; the janitor skill composes with it for lifecycle semantics.
- No implementation work in target repos while auditing cleanup candidates. If a row needs real code or docs work, the recommendation is `promote` or `keep`, not an inline fix.

## Skill Name and Placement

Create:

- `skills/tasktool-janitor/SKILL.md`

Do not create a separate CLI tool. The first implementation is process guidance only. Publish/sync scripts already copy top-level `skills/` into `plugins/superstar/skills/`, so the generated mirror should be refreshed by normal release tooling later rather than hand-edited in this slice.

The frontmatter should use trigger-only wording:

```yaml
---
name: tasktool-janitor
description: Use when cleaning up open tasktool rows, especially cross-cutting X items, stale phase/slice entries, or large sets of heterogeneous tasklist cleanup candidates
---
```

## Required Workflow

### 1. Read-Only Intake

The skill must start by loading `superstar:tasklist-discipline` and then running:

```bash
tasktool list --open
git status --short
```

When the user asks for crosscuts, the coordinator isolates `X*` rows from the open list before dispatch. The skill may inspect `tasktool show <id>`, specs, plans, handoffs, reviewer chains, archived task notes, source files, docs, recent commits, and targeted `rg` results, but it must remain read-only during classification.

If `git status --short` shows unrelated dirty or staged work, the coordinator records that fact in the audit context and avoids committing or reverting it. Dirty work does not automatically block read-only audit. Before mutation, however, the coordinator must specifically check whether `docs/tasklist.json` is itself dirty or staged with unrelated edits: `tasktool close` and `tasktool cancel` auto-commit scoped tracker/archive changes by default, and pre-existing tracker dirt can be folded into that lifecycle commit. Resolve or stash unrelated tracker dirt first; use `tasktool close --no-commit` only when the operator intentionally wants the tracker to remain staged.

### 2. Batching and Delegation

The skill must require coordinator-led batching when cleanup involves more than six candidate rows or spans more than one coherent theme:

- Use one worker per coherent theme or per bounded batch of 4-6 rows.
- Use `dispatching-parallel-agents` when batches are independent.
- Workers may inspect evidence but must not edit files or run mutating tasktool commands.
- Workers must return dossiers, not prose-only summaries.
- A single coordinator must not review 20+ heterogeneous rows alone.

Acceptable worker evidence sources include:

- `tasktool show <id>`
- `tasktool list --open`
- `docs/specs/`, `docs/plans/`, `docs/handoffs/`
- `docs/reviewer/`
- `docs/archived-tasks/`
- relevant source/docs paths named by the row
- targeted `rg` searches
- recent commits where needed

Workers must not run:

```bash
tasktool close <id>
tasktool cancel <id> --reason "..."
tasktool set <id> ...
tasktool note <id> ...
tasktool ref <id> ...
```

### 3. Dossier Contract

Every audited row must produce a dossier with this shape:

```markdown
## <id> — <title>

**Recommended action:** keep | close | cancel | promote | uncertain
**Evidence checked:** <commands/files/refs reviewed>
**Rationale:** <why the evidence supports the recommendation>
**Proposed command:** <exact tasktool command, or "none">
**Confidence / risk notes:** <known gaps, ambiguity, or blast radius>
```

Action meanings:

| Action | Meaning |
|--------|---------|
| `keep` | The row is still valid and should remain open. |
| `close` | The work is truthfully done and evidence supports `tasktool close <id>`. |
| `cancel` | The work is abandoned, superseded, invalid, intentionally not shipping, or no longer desired; use `tasktool cancel <id> --reason "..."`. |
| `promote` | The row should become or feed a proper phase/slice/spec/plan before it can be resolved. |
| `uncertain` | Evidence is incomplete or conflicting; do not mutate. |

Age alone is never evidence for `close` or `cancel`.

`promote` does not run a tasktool mutation during janitor cleanup. The coordinator records the promotion recommendation in the audit artifact and routes it into the normal Superstar spec/plan workflow if the user wants to pursue it.

### 4. Coordinator Reconciliation

The coordinator merges worker dossiers into grouped recommendations. Before presenting anything to the user, the coordinator must re-check every `close` and `cancel` recommendation against the cited evidence. Weak recommendations are downgraded to `uncertain`.

The user-facing recommendation must group rows by action and include the exact commands proposed for approved mutation. The coordinator must ask for approval before running any mutating command.

### 5. Mutation Discipline

After approval, the coordinator applies changes only with tasktool commands:

```bash
tasktool close XNN
tasktool cancel XNN --reason "..."
```

The skill must state:

- `tasktool close XNN` is only for truthfully done work.
- `tasktool cancel XNN --reason "..."` is for abandoned, superseded, invalid, or intentionally unshipped work.
- `tasktool cancel` does not apply to task rows; non-cross lifecycle details remain owned by `tasklist-discipline`.
- `tasktool close XNN` on a cross row still passes tasktool's landed-branch gate. If the row records an unlanded worktree branch, close is refused; do not improvise flags, and consult `tasklist-discipline` for any sanctioned override and required reason.
- Before any `close` or `cancel`, confirm `docs/tasklist.json` is not itself dirty or staged with unrelated edits because close/cancel auto-commit scoped tracker/archive changes by default. Resolve or stash unrelated tracker dirt first; use `--no-commit` only for an intentional staged lifecycle package.
- Apply changes in small batches.
- Run `tasktool validate` and re-check open rows after each batch.
- Preserve unrelated dirty/staged work.
- Stop and report if tasktool refuses a mutation instead of hand-editing `docs/tasklist.json`.

### 6. Audit Trail

For substantial cleanup, the skill must leave or recommend a durable audit artifact unless the user explicitly requests chat-only output. The artifact should live under `docs/handoffs/` or another existing repo docs area chosen by local convention and record:

- original row id and title
- action recommended
- evidence checked
- command approved and run, if any
- final state after mutation, including the archived-task path when closing or cancelling an `X*` row archives it
- unresolved uncertainties

The skill should avoid forcing a particular filename because cleanup may happen outside a formal spec/plan slice. A recommended default is:

```text
docs/handoffs/YYYY-MM-DD-tasktool-janitor-audit.md
```

## Composition With Existing Skills

- `tasklist-discipline`: required for lifecycle meanings, sanctioned commands, cancellation semantics, and artifact boundaries.
- `dispatching-parallel-agents`: required when the candidate set splits into independent row batches.
- `using-git-worktrees`: not required for pure read-only administrative audit; use it only if the cleanup turns into implementation work or active slice lifecycle mutations beyond approved administrative cleanup.
- `subagent-driven-development`: not required for the janitor audit itself, because this is not plan execution. If a dossier recommends `promote`, future implementation should go through the normal spec/plan/implementation loop.

## Acceptance Criteria

- `skills/tasktool-janitor/SKILL.md` exists with trigger-focused frontmatter.
- The skill requires read-only intake with `tasktool list --open` and `git status --short`.
- The skill requires batching or worker delegation for large heterogeneous cleanup sets.
- The skill forbids worker agents from mutating tasktool state or editing files.
- The skill defines the dossier schema and the five allowed recommendations: `keep`, `close`, `cancel`, `promote`, `uncertain`.
- The skill requires coordinator re-check of every `close` and `cancel` recommendation before user presentation.
- The skill requires explicit user approval before any `tasktool close` or `tasktool cancel`.
- The skill requires small mutation batches followed by `tasktool validate` and open-row re-check.
- The skill requires a durable audit artifact for substantial cleanup unless the user asks for chat-only.
- Regression tests or trigger tests cover the new skill file and key guardrails.

## Test Strategy

Add focused string-level tests under `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` because this repo already uses that file to pin load-bearing skill prose. The tests should assert:

- the skill file exists and has the expected frontmatter trigger;
- tests pin `name: tasktool-janitor` and the description phrase `cleaning up open tasktool rows`;
- intake commands are present;
- worker mutation bans are present;
- the dossier fields and recommendation enum are present;
- approval-before-mutation and small-batch validation language is present;
- substantial cleanup audit trail guidance is present.

Implementation may optionally add a skill-triggering prompt fixture if the current harness supports it cheaply, but string-level skill guardrails are sufficient for the first slice.

## Validation Ground

Use multistore only as a manual validation/training ground after the skill exists. A dry run in `/home/simon/Dev/sigreer/multistore` should be able to produce grouped dossiers for open `X*` rows without running any mutating command. That dry run is not required to close this planning package, but the implementation plan should include it as optional manual validation if the environment is available.

## Open Decisions Resolved

- Skill name: `tasktool-janitor`.
- First version is documentation/process only, not a tasktool command.
- The audit artifact is required for substantial cleanup, but its exact location follows repo convention.
- Multistore is validation context, not embedded behavior.
