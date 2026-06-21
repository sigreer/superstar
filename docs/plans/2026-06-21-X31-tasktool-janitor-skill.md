# Tasktool Janitor Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable on-demand Superstar skill, `tasktool-janitor`, for evidence-based cleanup of open tasktool rows without bulk-closing or mutating before approval.

**Architecture:** Implement this as a new canonical skill under top-level `skills/tasktool-janitor/SKILL.md`, backed by string-level lifecycle documentation tests. The skill composes with `tasklist-discipline` and `dispatching-parallel-agents`; it does not add tasktool commands or change tracker behavior.

**Tech Stack:** Markdown skill content, Python pytest string assertions, optional shell skill-trigger fixture. No new dependencies.

---

## Scheduling Contract

`X31` is a cross-cutting implementation item. It is not nested under a phase, has no `depends_on`, `parallel_group`, `coordination_group`, integration-surface metadata, or reservations. Treat implementation as one isolated work item:

```bash
tasktool start X31
```

Use the worktree path printed by `tasktool start`. Do not edit implementation files from the authoritative checkout.

## File Structure

- **Create:** `skills/tasktool-janitor/SKILL.md`
  - Owns the reusable cleanup workflow: read-only intake, row batching, worker dossier contract, coordinator reconciliation, approval-before-mutation, tasktool-only small-batch mutation, and audit trail guidance.
- **Modify:** `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`
  - Adds guardrail tests for the new skill file and its load-bearing instructions.
- **Optional create:** `tests/skill-triggering/prompts/tasktool-janitor.txt`
  - Adds a natural-language prompt for manual trigger testing.
- **Optional modify:** `tests/skill-triggering/run-all.sh`
  - Include `tasktool-janitor` only if the implementation team wants this prompt in the slow Claude-based trigger suite.

Do not hand-edit `plugins/superstar/skills/**`. The generated Codex/Claude plugin mirrors are refreshed by publish/sync tooling after the source skill is accepted.

## Verification Commands

Focused verification:

```bash
python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
```

Full relevant verification:

```bash
python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
tasktool validate
git diff --check
```

Optional manual validation after implementation:

```bash
cd /home/simon/Dev/sigreer/multistore
tasktool list --open
git status --short
```

Then dry-run the skill mentally or in a supervised session against `X*` rows only, producing dossiers without running mutating commands.

---

### Task 0: Start X31 and capture the baseline

**Files:** none

- [ ] **Step 1: Start the cross-cutting work item**

Run from `/home/simon/Dev/sigreer/skills/superstar`:

```bash
tasktool brief X31
tasktool start X31
```

Expected: `tasktool brief X31` prints the existing X31 row, and `tasktool start` prints a worktree path under `.worktrees/` and records the worktree on the X31 row.

- [ ] **Step 2: Enter the worktree**

Run:

```bash
cd <path-printed-by-tasktool-start>
```

Expected: the shell is inside the X31 implementation worktree.

- [ ] **Step 3: Confirm the canonical skill/test paths**

Run:

```bash
sed -n '1,20p' tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
find skills -maxdepth 2 -name SKILL.md | sort
```

Expected: `skill_text()` reads from top-level `skills/<name>/SKILL.md`, and no `skills/tasktool-janitor/SKILL.md` exists yet.

- [ ] **Step 4: Run the baseline focused test**

Run:

```bash
python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
```

Expected: passes before X31 edits. If it fails, stop and report the pre-existing failure before changing files.

---

### Task 1: Add failing guardrail tests for `tasktool-janitor`

**Files:**
- Modify: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`

- [ ] **Step 1: Add the failing tests**

Append these tests near the other skill-content assertions:

```python
def test_tasktool_janitor_skill_exists_with_trigger_frontmatter() -> None:
    text = skill_text("tasktool-janitor")

    assert "name: tasktool-janitor" in text
    assert "description: Use when cleaning up open tasktool rows" in text
    assert "cross-cutting X items" in text
    assert "large sets of heterogeneous tasklist cleanup candidates" in text


def test_tasktool_janitor_starts_read_only_and_batches_work() -> None:
    text = skill_text("tasktool-janitor")

    assert "tasktool list --open" in text
    assert "git status --short" in text
    assert "read-only" in text.lower()
    assert "more than six candidate rows" in text
    assert "4-6 rows" in text
    assert "dispatching-parallel-agents" in text
    assert "must not review 20+ heterogeneous rows alone" in text


def test_tasktool_janitor_forbids_worker_mutations() -> None:
    text = skill_text("tasktool-janitor")

    assert "Workers must not run" in text
    assert "tasktool close <id>" in text
    assert "tasktool cancel <id> --reason" in text
    assert "tasktool set <id>" in text
    assert "tasktool note <id>" in text
    assert "tasktool ref <id>" in text
    assert "must not edit files" in text


def test_tasktool_janitor_defines_dossier_contract() -> None:
    text = skill_text("tasktool-janitor")

    for field in [
        "Recommended action",
        "Evidence checked",
        "Rationale",
        "Proposed command",
        "Confidence / risk notes",
    ]:
        assert field in text

    for action in ["keep", "close", "cancel", "promote", "uncertain"]:
        assert action in text

    assert "Age alone is never evidence" in text
    assert "promote" in text and "normal Superstar spec/plan workflow" in text


def test_tasktool_janitor_requires_approval_and_safe_mutation_batches() -> None:
    text = skill_text("tasktool-janitor")

    assert "explicit user approval" in text
    assert "tasktool close XNN" in text
    assert "tasktool cancel XNN --reason" in text
    assert "landed-branch gate" in text
    assert "docs/tasklist.json" in text
    assert "close` auto-commits" in text
    assert "has no equivalent opt-out flag" in text
    assert "stages the archive and leaves the tracker edit unstaged" in text
    assert "small batches" in text
    assert "tasktool validate" in text
    assert "re-check open rows" in text
    assert "Stop and report if tasktool refuses" in text


def test_tasktool_janitor_requires_audit_trail_for_substantial_cleanup() -> None:
    text = skill_text("tasktool-janitor")

    assert "durable audit artifact" in text
    assert "unless the user explicitly requests chat-only" in text
    assert "docs/handoffs/YYYY-MM-DD-tasktool-janitor-audit.md" in text
    assert "archived-task path" in text
```

- [ ] **Step 2: Run the focused test and confirm failure**

Run:

```bash
python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
```

Expected: fails because `skills/tasktool-janitor/SKILL.md` does not exist.

Do not commit this failing state. Task 2 creates the skill and makes the tests pass.

---

### Task 2: Create `skills/tasktool-janitor/SKILL.md`

**Files:**
- Create: `skills/tasktool-janitor/SKILL.md`

- [ ] **Step 1: Create the skill directory and file**

Create `skills/tasktool-janitor/SKILL.md` with this content:

```markdown
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
```

- [ ] **Step 2: Run the focused tests**

Run:

```bash
python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
```

Expected: passes.

- [ ] **Step 3: Commit tests plus skill**

Run:

```bash
git add tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py skills/tasktool-janitor/SKILL.md
git commit -m "X31: add tasktool janitor skill"
```

Expected: commit succeeds.

---

### Task 3: Add optional trigger fixture without making the suite slower by default

**Files:**
- Create: `tests/skill-triggering/prompts/tasktool-janitor.txt`
- Optional modify: `tests/skill-triggering/run-all.sh`

- [ ] **Step 1: Add a natural prompt fixture**

Create `tests/skill-triggering/prompts/tasktool-janitor.txt`:

```text
Please clean up the tasktool crosscuts. Start by auditing the open X rows and propose what should stay open, close, cancel, promote, or remain uncertain. Do not mutate anything until I approve the recommendations.
```

- [ ] **Step 2: Decide whether to include it in `run-all.sh`**

Default: do not add it to `SKILLS` in `tests/skill-triggering/run-all.sh`, because that suite shells out to Claude and is slower/flakier than the string-level guardrails. If the implementer chooses to include it, add `"tasktool-janitor"` to the `SKILLS` array and document the increased suite cost in the commit message.

- [ ] **Step 3: Commit the fixture**

Run:

```bash
git add tests/skill-triggering/prompts/tasktool-janitor.txt
git commit -m "X31: add tasktool janitor trigger prompt"
```

Expected: commit succeeds. If no trigger fixture is added, skip this task and record the reason in the implementation summary.

---

### Task 4: Verify source-only scope and generated mirror boundary

**Files:** none unless verification finds accidental mirror edits

- [ ] **Step 1: Check for accidental generated mirror edits**

Run:

```bash
git status --short
git diff --name-only -- plugins/superstar/skills
```

Expected: no `plugins/superstar/skills/**` changes. If generated mirror files changed, inspect why. Revert only accidental mirror edits made by this implementation; preserve unrelated user changes.

- [ ] **Step 2: Run focused verification**

Run:

```bash
python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
```

Expected: all tests pass.

- [ ] **Step 3: Run tasktool validation**

Run:

```bash
tasktool validate
```

Expected: exits 0. Existing warnings unrelated to X31 may remain; record them exactly in the implementation summary.

- [ ] **Step 4: Run diff whitespace validation**

Run:

```bash
git diff --check
```

Expected: no output and exit 0.

---

### Task 5: External post-slice review and closeout

**Files:** reviewer artifacts and tasktool lifecycle files only

- [ ] **Step 1: Confirm the implementation branch is ready for review**

Run:

```bash
git status --short
```

Expected: only committed X31 implementation changes, or a clean worktree. If unrelated dirty files are present, stop and resolve scope before review.

- [ ] **Step 2: Run post-slice review**

Run:

```bash
external-reviewer review \
  --kind post-slice \
  --file docs/plans/2026-06-21-X31-tasktool-janitor-skill.md \
  --work-id X31 \
  --context docs/specs/2026-06-21-X31-tasktool-janitor-skill-design.md \
  --emit json
```

Expected: `merged_verdict` is `ready` or `ready with small edits`. If the verdict is `revise`, dispatch a fix subagent, write the required reviewer resolution file, and resubmit.

- [ ] **Step 3: Ask the version-bump question before final shipping commit/publish**

Because this changes user-shipping `skills/` content, ask:

```text
Bump the version before/after this commit? (current: <current> -> patch <next-patch> / minor <next-minor> / no bump)
```

Do not silently bump. If the user chooses a bump, run `./scripts/bump-version.sh <new-version>` and commit the bump separately as `Bump Superstar to <new-version>`.

If the bump commit is blocked by shim or hook version drift, run:

```bash
bash tools/tasktool/install.sh --hook --force
```

Then rerun the commit.

- [ ] **Step 4: Merge, close, and prune through normal tasktool lifecycle**

Follow `subagent-driven-development` closeout. Merge the X31 worktree branch back to `main` using `finishing-a-development-branch` Option 1 mechanics before closing; `--allow-unlanded` is not the sanctioned path for normal X31 completion.

```bash
git checkout main
git merge <x31-worktree-branch>
tasktool close X31
tasktool worktree prune X31
```

Expected: X31 closes only after the implementation is landed and reviewed. If `tasktool close` refuses, stop and report the refusal.

## Acceptance

- `skills/tasktool-janitor/SKILL.md` exists and passes the guardrail tests.
- Worker mutation bans, dossier schema, approval-before-mutation, tracker close auto-commit safeguards, cancel staged-package safeguards, landed-gate warning, and durable audit guidance are present in the skill.
- Focused docs-lifecycle pytest passes.
- `tasktool validate` exits 0, with only pre-existing warnings if any.
- No generated plugin mirror files are hand-edited.
- Post-slice review passes before X31 closeout.
