---
name: tasktool-janitor
description: Use when cleaning up open tasktool rows, especially cross-cutting X items, stale phase/slice entries, or large sets of heterogeneous tasklist cleanup candidates
---

# Tasktool Janitor

Clean up open tasktool rows by auditing evidence first, reconciling recommendations conservatively, asking for approval, and applying only small approved `tasktool` mutation batches.

## Required Setup

Use `superstar:tasklist-discipline` first. For large or heterogeneous cleanup sets, use `superstar:dispatching-parallel-agents` to split independent row audits.

Start read-only:

```bash
tasktool list --open
git status --short
```

When the user asks for crosscuts, isolate `X*` rows from the open list. Dirty work does not block read-only audit, but before mutation check whether `docs/tasklist.json` itself is dirty or staged with unrelated edits.

`tasktool close` auto-commits only scoped lifecycle tracker/archive changes by default; unrelated tracker dirt must be cleared before close or cancel. Use `tasktool close --no-commit` only when the operator intentionally wants a staged lifecycle package.

The cancel command stages the archive and leaves the tracker edit unstaged, with no auto-commit. It has no equivalent opt-out flag, so the operator must commit or otherwise handle the lifecycle package deliberately. Resolve or stash unrelated tracker dirt before either command.

## Batching

Delegate when the cleanup set has more than six candidate rows or spans more than one coherent theme.

- Use one worker per theme or per bounded batch of 4-6 rows.
- Workers may inspect `tasktool show`, specs, plans, handoffs, reviewer chains, archived task notes, source files, docs, recent commits, and targeted `rg` results.
- Workers must return dossiers, not prose-only summaries.
- A single coordinator must not review 20+ heterogeneous rows alone.
- Workers must not edit files.

Workers must not run:

```bash
tasktool close <id>
tasktool cancel <id> --reason "..."
tasktool set <id> ...
tasktool note <id> ...
tasktool ref <id> ...
```

## Dossier Contract

Every row gets this dossier:

```markdown
## <id> - <title>

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
| `cancel` | The work is abandoned, superseded, invalid, intentionally not shipping, or no longer desired. |
| `promote` | The row should feed the normal Superstar spec/plan workflow before it can be resolved. |
| `uncertain` | Evidence is incomplete or conflicting; do not mutate. |

Age alone is never evidence for `close` or `cancel`.

## Reconciliation

Merge worker dossiers into grouped recommendations. Re-check every `close` and `cancel` recommendation yourself against the cited evidence. Downgrade weak or incomplete evidence to `uncertain`.

Present grouped recommendations to the user before mutation. Include exact proposed commands for rows you recommend changing, and ask for explicit user approval.

Record `promote` recommendations in the audit artifact and route them into the normal Superstar spec/plan workflow if the user wants to pursue them. Do not turn `promote` into ad-hoc implementation during cleanup.

## Mutation Rules

After approval, use only `tasktool` commands:

```bash
tasktool close XNN
tasktool cancel XNN --reason "..."
```

- `tasktool close XNN` is only for truthfully done work.
- `tasktool cancel XNN --reason "..."` is for abandoned, superseded, invalid, or intentionally unshipped work.
- `tasktool cancel` does not apply to task rows; non-cross lifecycle details stay with `tasklist-discipline`.
- `tasktool close XNN` on a cross row still passes the landed-branch gate. If a row records an unlanded worktree branch, close is refused; do not improvise flags. Consult `tasklist-discipline` for any sanctioned override and required reason.
- Before each mutation batch, confirm `docs/tasklist.json` is not dirty or staged with unrelated edits.
- After clearing unrelated dirt, `close` auto-commits scoped tracker/archive changes by default and supports `--no-commit` for an intentional staged lifecycle package.
- The cancel command stages the archive and leaves the tracker edit unstaged, with no auto-commit. It has no equivalent opt-out flag, so the operator must commit or otherwise handle that lifecycle package deliberately.
- Apply changes in small batches.
- After each batch, run `tasktool validate` and re-check open rows with `tasktool list --open`.
- Preserve unrelated dirty/staged work.
- Stop and report if tasktool refuses a mutation. Do not hand-edit `docs/tasklist.json`.

## Audit Trail

For substantial cleanup, leave or recommend a durable audit artifact unless the user explicitly requests chat-only output.

Default path:

```text
docs/handoffs/YYYY-MM-DD-tasktool-janitor-audit.md
```

Record original row id/title, action, evidence, command run, final state, archived-task path when applicable, and unresolved uncertainties.
