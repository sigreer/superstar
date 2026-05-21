# P5.S3 — Skill rewrite + subagent guard + workflow updates — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse `using-git-worktrees` to ≤40 lines around a subagent early-exit, teach `tasktool start` to refuse dispatched subagents via three env signals, and update the coordinator's dispatch prompt templates to instruct subagents to export `SUPERSTAR_SUBAGENT_ROLE` so the runtime guard has the highest practical chance of firing when subagents follow the directive.

**Architecture:** Five disjoint edit clusters:
1. Skill rewrite (`using-git-worktrees/SKILL.md` shrunk; long-form submodule guard relocated to `references/submodules.md`).
2. Subagent guard inside `tools/tasktool/commands.py::cmd_start` (three env signals with declared precedence, single refusal message, no fingerprinting).
3. Workflow cross-reference updates in `tasklist-discipline`, `executing-plans`, `subagent-driven-development` (no touch to `finishing-a-development-branch` — that belongs to P5.S2).
4. Coordinator-facing dispatch prompt updates: extend `skills/subagent-driven-development/implementer-prompt.md` (and the spec-reviewer / code-quality-reviewer prompt templates) to instruct each dispatched subagent to export `SUPERSTAR_SUBAGENT_ROLE=<role>` as its first shell command. This is a best-effort prose directive (Superstar does not wrap the harness's native dispatch tool), backed by the runtime guard in step 2 and the load-bearing prose rule in step 3. Tests assert the directive is present in every template and that a simulated `env -i bash` dispatch is correctly refused.
5. Tests: signal-precedence and plain-shell false-negative coverage for the guard, template fixture tests for the shim directive, a token-budget regression fixture for the skill body, and a doc-shape test for the rewritten skill (≤40 lines, `<SUBAGENT-STOP>` block present).

**Tech Stack:** Python (3.10+) for tasktool, pytest for tests, bash for fixtures, plain Markdown for skill / template edits.

**Out of scope (handled elsewhere):**
- Schema field reads/writes for `worktree_path` / `worktree_branch` / `worktree_in_place` — owned by P5.S1.
- Worktree creation, adoption, prune, repair, finalize — owned by P5.S1 / P5.S2.
- `finishing-a-development-branch` edits (post-merge prune step) — owned by P5.S2 per spec §5.3.2 (`:212-214`). The spec's P5.S3 slice paragraph at §6 (`:275-277`) lists all three workflow skills, but §5.3.2 splits ownership and assigns the prune step to P5.S2. Treat §5.3.2 as authoritative; this slice does not modify `finishing-a-development-branch`. Task 1.5 below verifies P5.S2 actually shipped the prune step before this slice starts so the workflow gap is not silently left open.
- Removal of legacy `.claude/worktrees/` / `.codex/worktrees/` paths — deferred per spec §4.

**Shim scope (read this before Task 8).** The spec at `:137` and `:286` says "the Claude shim and Codex shim" export `SUPERSTAR_SUBAGENT_ROLE`. The Superstar repo does not currently wrap the harness's native dispatch tool (Claude Code's `Task`, Codex's `spawn_agent`) — there is no Python or JS interceptor between the harness and the subagent process where an env var could be injected programmatically. The honest implementation is therefore a **best-effort prose guard**: the coordinator's dispatch prompt templates instruct the subagent to export the variable as its first shell command. The runtime guard in `tasktool start` (Task 7) is the load-bearing safety net; the prose rule in `tasklist-discipline` (Task 9) is the load-bearing *cultural* rule. The prompt-template directive (Task 8) raises the probability that the runtime guard fires in real use, but does not guarantee it. Task 8 acknowledges this explicitly and adds a simulated-harness transcript test (Task 8 Step 8.5) to prove the dispatch-time refusal actually works in a realistic shell when the directive is followed. If a future harness change exposes a real env-injection point, that integration can be wired in without breaking either the runtime guard or the prose rule.

**Scheduling preconditions (verify before starting):**

```sh
tools/tasktool/tasktool show P5.S3
tools/tasktool/tasktool schedule P5
```

Expected: `P5.S3` exists with `status: ready`, `depends_on: [P5.S1, P5.S2]`, `planning_status: proposed`. After plan-review passes, the writing-plans flow will ratify (coordinator-side `tasktool ratify P5.S3 --parallel-group …` is **not** part of this plan — the coordinator owns ratification).

**Verification baseline (must pass against `main` before slice start, per spec §10):**

```sh
tools/tasktool/tasktool validate --strict-format
python -m pytest tools/tasktool/tests -q
```

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `skills/using-git-worktrees/SKILL.md` | rewrite (226 → ≤40 lines) | Subagent early-exit block + 4 one-line rules. |
| `skills/using-git-worktrees/references/submodules.md` | create | Submodule guard lifted from current SKILL.md §0; loaded on demand. |
| `skills/tasklist-discipline/SKILL.md` | append paragraph | Subagents must inherit cwd; never call `tasktool start`. |
| `skills/executing-plans/SKILL.md` | minor edits | Add cross-reference to the rewritten skill's early-exit; mention parent-creates-worktree pattern. |
| `skills/subagent-driven-development/SKILL.md` | minor edits | One-line reminder that subagents inherit cwd and never call `tasktool start`. |
| `skills/subagent-driven-development/implementer-prompt.md` | minor edits | Add explicit `SUPERSTAR_SUBAGENT_ROLE=implementer` directive in the dispatch template. |
| `skills/subagent-driven-development/spec-reviewer-prompt.md` | minor edits | Same directive, role=`spec-reviewer`. |
| `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | minor edits | Same directive, role=`code-quality-reviewer`. |
| `tools/tasktool/commands.py` | extend `cmd_start` | Three-signal subagent guard with declared precedence; refusal message verbatim from spec §5.3. |
| `tools/tasktool/tests/test_lifecycle_start.py` | extend | Add guard tests (precedence, refusal message, plain-shell false-negative). |
| `tools/tasktool/tests/fixtures/p5_s3_skill_body.txt` | create | Frozen copy of the rewritten skill body for the token-budget regression test. |
| `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` | extend | Skill-shape tests: ≤40 lines, contains `<SUBAGENT-STOP>` block, contains `tasktool start` reference, references `references/submodules.md`. |
| `tools/tasktool/tests/test_subagent_prompt_shim.py` | create | Assert each of the three subagent-prompt templates exports `SUPERSTAR_SUBAGENT_ROLE=<expected>`. |

---

## Task 1: Establish baseline + lifecycle start

**Files:** none — verification + tasktool lifecycle only.

- [ ] **Step 1.1: Verify scheduling preconditions**

```sh
tools/tasktool/tasktool show P5.S3
tools/tasktool/tasktool schedule P5
```

Expected: `P5.S3` exists with `depends_on: [P5.S1, P5.S2]`. If absent or differs, stop — coordinator needs to fix the row before this plan can execute.

- [ ] **Step 1.2: Verify baseline tests pass**

```sh
tools/tasktool/tasktool validate --strict-format
python -m pytest tools/tasktool/tests -q
```

Expected: both exit 0. If anything fails on `main`, stop and report — do not start the slice over a red baseline.

- [ ] **Step 1.3: Start the slice**

```sh
tools/tasktool/tasktool start P5.S3
```

Expected: status flips to `in_progress`. This is the lifecycle gate; do not substitute prose, TodoWrite, or hand JSON edits.

- [ ] **Step 1.4: Verify P5.S2 shipped the `finishing-a-development-branch` prune step**

This slice deliberately does not modify `finishing-a-development-branch` (spec §5.3.2 assigns the prune step to P5.S2). Confirm P5.S2 actually delivered that edit before this slice begins, so the workflow gap is not silently left open:

```sh
tools/tasktool/tasktool show P5.S2
grep -nE "tasktool worktree prune" skills/finishing-a-development-branch/SKILL.md
```

Expected: `P5.S2` status is `done` (closed by P5.S2's external review gate), and `grep` returns at least one match showing the post-merge prune step. If `P5.S2` is not done, **stop** — this slice waits on it. If `P5.S2` is done but `finishing-a-development-branch` does not mention `tasktool worktree prune`, stop and surface the gap to the coordinator (this would be a P5.S2 closeout defect, not a P5.S3 problem to paper over).

- [ ] **Step 1.5: No commit yet.**

This task produces no diff. Proceed to Task 2.

---

## Task 2: Extract submodule guard to `references/submodules.md`

**Files:**
- Create: `skills/using-git-worktrees/references/submodules.md`

- [ ] **Step 2.1: Create the references directory and submodules reference**

```sh
mkdir -p skills/using-git-worktrees/references
```

Write `skills/using-git-worktrees/references/submodules.md` with this content:

```markdown
# Submodule guard for using-git-worktrees

Load this reference **only** when `tasktool start` reports a worktree-detection conflict caused by a submodule, or when the early-exit block in `SKILL.md` cannot decide whether the current directory is a linked worktree or a submodule checkout.

## Why this matters

`GIT_DIR != GIT_COMMON_DIR` is true in two distinct situations:

1. The current directory is a linked git worktree (e.g. `.worktrees/worktree-p5-s3-…`).
2. The current directory is a git submodule checkout.

The submodule case must **not** be treated as a worktree. Treating a submodule as a linked worktree skips legitimate worktree creation and corrupts the slice's evidence boundary.

## Disambiguating

Run:

```sh
git rev-parse --show-superproject-working-tree 2>/dev/null
```

- Empty output (or non-zero exit): you are **not** in a submodule. The `GIT_DIR != GIT_COMMON_DIR` signal is genuine — treat the directory as a linked worktree.
- Non-empty output (a path): you are inside a submodule of that superproject. Treat the directory as a normal repo checkout and do not skip the worktree creation step.

## What to do

If you discover you are in a submodule and tasktool refuses to proceed, leave the submodule (`cd` to the superproject root, or to the authoritative checkout) and re-run `tasktool start <id>` from there. Do not attempt to nest a worktree inside the submodule.
```

- [ ] **Step 2.2: Stage the new file**

```sh
git add skills/using-git-worktrees/references/submodules.md
```

- [ ] **Step 2.3: Defer commit until the skill rewrite lands (Task 3).** This keeps the rewrite atomic.

---

## Task 3: Rewrite `using-git-worktrees/SKILL.md`

**Files:**
- Modify: `skills/using-git-worktrees/SKILL.md` (current 226 lines → target ≤40 lines including frontmatter, per spec §5.5)

- [ ] **Step 3.1: Replace the entire file with the rewritten body**

Write `skills/using-git-worktrees/SKILL.md` with exactly this content:

```markdown
---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - ensures an isolated workspace exists via native tools or git worktree fallback
---

<SUBAGENT-STOP>
You were dispatched as a subagent. The parent coordinator has already created or adopted the worktree for the active slice and `cd`d you into it. Do not read or apply the rest of this skill, and do not call `tasktool start`. If `git rev-parse --git-dir` differs from `git rev-parse --git-common-dir` (and you are not inside a submodule — see `references/submodules.md` if uncertain), you are inside the parent's linked worktree; proceed with your task. If they match, you are in a plain checkout; ask the parent before editing files.
</SUBAGENT-STOP>

# Using Git Worktrees

**Announce at start:** "I'm using the using-git-worktrees skill to enter the slice worktree."

**Rule:** Implementation slice/task work runs in an isolated linked worktree owned by tasktool. A plain `main`/`master` checkout is planning/read-only by default unless the human partner opts out of isolation in the current turn.

**Run:** `tasktool start <slice-id>` from the authoritative checkout (or from an already-linked worktree of the same repo — tasktool will auto-adopt). It creates the worktree at `.worktrees/worktree-<id>-<slug>`, records the path and branch on the slice row, and prints the `cd` line. Idempotent: a consistent recorded path is a no-op. See `[[tasklist-discipline]]` for the lifecycle commands and the routing rules.

**Opt-out:** For planning, spec, or design slices that touch no code, run `tasktool start <slice-id> --in-place`. The slice row records `worktree_in_place: true`; later `close` and `worktree prune` treat the slice as having no worktree.

**Drift:** If `tasktool start` reports a conflict (path missing, branch mismatched, plain-dir collision), run the exact `tasktool worktree {adopt,repair,prune --force}` command it prints. Do not improvise with raw `git worktree` invocations; do not delete `.worktrees/` directories by hand.

For submodule-vs-worktree disambiguation, see `references/submodules.md`.
```

- [ ] **Step 3.2: Verify length ≤ 40 lines including frontmatter**

```sh
wc -l skills/using-git-worktrees/SKILL.md
```

Expected: ≤ 40. If over, tighten the body — do not add a Quick Reference table, Common Mistakes section, Red Flags table, or decision tree to bring it back under target; those are deliberately forbidden by §5.5.

- [ ] **Step 3.3: Verify the `<SUBAGENT-STOP>` block is the first content after frontmatter**

```sh
grep -n "<SUBAGENT-STOP>\|</SUBAGENT-STOP>" skills/using-git-worktrees/SKILL.md
```

Expected: opening tag near line 6, closing tag before the `# Using Git Worktrees` heading.

- [ ] **Step 3.4: Commit Tasks 2 + 3 atomically**

```sh
git add skills/using-git-worktrees/SKILL.md skills/using-git-worktrees/references/submodules.md
git commit -m "P5.S3: rewrite using-git-worktrees skill to subagent early-exit + tasktool pointer"
```

---

## Task 4: Write failing skill-shape tests

**Files:**
- Modify: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` (append tests)

- [ ] **Step 4.1: Read the existing module to understand the helper conventions**

```sh
sed -n '1,40p' tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
```

Expected: a `skill_text(name)` helper exists. (If the helper signature differs, adapt the snippets below to match; do not rename the helper.)

- [ ] **Step 4.2: Append the skill-shape tests**

Append these tests to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:

```python
def test_using_git_worktrees_is_thin_and_has_subagent_stop_block() -> None:
    text = skill_text("using-git-worktrees")
    lines = text.splitlines()
    assert len(lines) <= 40, (
        f"using-git-worktrees SKILL.md must be <=40 lines (spec §5.5); "
        f"got {len(lines)}"
    )
    assert "<SUBAGENT-STOP>" in text, "missing <SUBAGENT-STOP> opening tag"
    assert "</SUBAGENT-STOP>" in text, "missing </SUBAGENT-STOP> closing tag"
    # The block must precede the human-facing heading.
    assert text.index("<SUBAGENT-STOP>") < text.index("# Using Git Worktrees")


def test_using_git_worktrees_points_at_tasktool_start() -> None:
    text = skill_text("using-git-worktrees")
    assert "tasktool start" in text, "skill must instruct calling tasktool start"
    assert "--in-place" in text, "skill must document the --in-place opt-out"


def test_using_git_worktrees_has_no_forbidden_sections() -> None:
    text = skill_text("using-git-worktrees")
    forbidden = ["## Quick Reference", "## Common Mistakes", "## Red Flags",
                 "### 1a.", "### 1b.", "## Step 0", "## Step 1", "## Step 3", "## Step 4"]
    for marker in forbidden:
        assert marker not in text, (
            f"forbidden section/heading present (spec §5.5 forbids it): {marker!r}"
        )


def test_using_git_worktrees_references_submodules_doc() -> None:
    text = skill_text("using-git-worktrees")
    assert "references/submodules.md" in text, (
        "skill must point at references/submodules.md for the submodule guard"
    )
    from pathlib import Path
    submod = Path(__file__).resolve().parents[3] / "skills" / "using-git-worktrees" / "references" / "submodules.md"
    assert submod.is_file(), f"references/submodules.md must exist at {submod}"
```

- [ ] **Step 4.3: Run the new tests; verify they pass against the rewritten skill**

```sh
python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -v
```

Expected: the four new tests pass. (If the skill was rewritten correctly in Task 3 they should be green on first run; this is a guard-rail, not TDD red→green for the skill itself.)

- [ ] **Step 4.4: Commit**

```sh
git add tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
git commit -m "P5.S3: test using-git-worktrees skill shape (length, stop-block, no forbidden sections)"
```

---

## Task 5: Capture token-budget regression fixture

**Files:**
- Create: `tools/tasktool/tests/fixtures/p5_s3_skill_body.txt`
- Modify: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` (append regression test)

The spec §6 P5.S3 requires a concrete token-budget regression fixture so future edits cannot silently regrow the skill. Mechanism: freeze the post-rewrite body as a fixture file and assert the live skill matches it byte-for-byte, except for trailing whitespace normalisation. Future edits must consciously update the fixture, which is the audit trail.

- [ ] **Step 5.1: Capture the frozen fixture**

```sh
mkdir -p tools/tasktool/tests/fixtures
cp skills/using-git-worktrees/SKILL.md tools/tasktool/tests/fixtures/p5_s3_skill_body.txt
```

- [ ] **Step 5.2: Append the regression test**

Append this test to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:

```python
def test_using_git_worktrees_matches_token_budget_fixture() -> None:
    """Token-budget regression. If you must edit the skill, update the fixture
    in the same commit so the diff is visible in review. Spec P5.S3 §6."""
    from pathlib import Path
    live = (Path(__file__).resolve().parents[3]
            / "skills" / "using-git-worktrees" / "SKILL.md").read_text()
    fixture = (Path(__file__).resolve().parent / "fixtures"
               / "p5_s3_skill_body.txt").read_text()
    # Normalise trailing whitespace on each line; preserve structure otherwise.
    def norm(s: str) -> str:
        return "\n".join(line.rstrip() for line in s.splitlines())
    assert norm(live) == norm(fixture), (
        "using-git-worktrees SKILL.md drifted from the P5.S3 token-budget "
        "fixture. If this is intentional, update "
        "tools/tasktool/tests/fixtures/p5_s3_skill_body.txt in the same commit."
    )
```

- [ ] **Step 5.3: Run the regression test**

```sh
python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py::test_using_git_worktrees_matches_token_budget_fixture -v
```

Expected: PASS.

- [ ] **Step 5.4: Commit**

```sh
git add tools/tasktool/tests/fixtures/p5_s3_skill_body.txt tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
git commit -m "P5.S3: freeze using-git-worktrees skill body as token-budget regression fixture"
```

---

## Task 5b: Subagent early-exit transcript fixture

Spec §6 P5.S3 also asks for "a representative subagent transcript that previously loaded the full skill now loads only the early-exit block." Task 5 covers the byte-for-byte body freeze (silent-growth detection); this task covers the **transcript-side behavior**: the bytes a subagent actually consumes when it follows the early-exit instruction.

**Files:**
- Create: `tools/tasktool/tests/fixtures/p5_s3_subagent_load.txt`
- Modify: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` (append transcript test)

- [ ] **Step 5b.1: Define the load contract**

A dispatched subagent that honours the `<SUBAGENT-STOP>` block should consume only the bytes between the opening and closing tags (inclusive of the tags themselves), and zero bytes from anywhere else in the skill. Capture that span as a fixture so a future edit that breaks the early-exit (e.g. moves content above the `<SUBAGENT-STOP>` tag, inlines the submodule reference back into the body, or renames the tag) makes the test fail visibly.

- [ ] **Step 5b.2: Extract the early-exit span**

```sh
python3 - <<'PY'
from pathlib import Path
text = Path("skills/using-git-worktrees/SKILL.md").read_text()
start = text.index("<SUBAGENT-STOP>")
end   = text.index("</SUBAGENT-STOP>") + len("</SUBAGENT-STOP>")
span  = text[start:end]
Path("tools/tasktool/tests/fixtures/p5_s3_subagent_load.txt").write_text(span)
print(f"captured {len(span)} chars, {span.count(chr(10))+1} lines")
PY
```

Expected: prints something like `captured ~700 chars, ~3 lines`. The fixture file now contains exactly the bytes a compliant subagent loads.

- [ ] **Step 5b.3: Append the transcript test**

Append to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:

```python
def test_subagent_early_exit_load_matches_fixture() -> None:
    """Spec §6 P5.S3 transcript regression. A compliant subagent loads only
    the bytes inside the <SUBAGENT-STOP> ... </SUBAGENT-STOP> block. This
    test reconstructs that span from the live skill and asserts it matches
    the frozen fixture, so any edit that displaces, renames, or splits the
    early-exit block surfaces here."""
    from pathlib import Path
    live = (Path(__file__).resolve().parents[3]
            / "skills" / "using-git-worktrees" / "SKILL.md").read_text()
    start_tag = "<SUBAGENT-STOP>"
    end_tag = "</SUBAGENT-STOP>"
    assert start_tag in live and end_tag in live, "early-exit tags missing"
    start = live.index(start_tag)
    end = live.index(end_tag) + len(end_tag)
    span = live[start:end]

    fixture = (Path(__file__).resolve().parent / "fixtures"
               / "p5_s3_subagent_load.txt").read_text()
    assert span == fixture, (
        "subagent early-exit span drifted from the P5.S3 transcript fixture. "
        "Update tools/tasktool/tests/fixtures/p5_s3_subagent_load.txt in the "
        "same commit and explain the behavior change in the commit message."
    )

    # Sanity: the early-exit block must be substantially smaller than the
    # full skill. If they were the same size, the load budget would be
    # unchanged from the rewritten skill body (which is already tiny but
    # still larger than the early-exit subset).
    assert len(span) < len(live), "early-exit span must be a proper subset"
    # The early-exit block must instruct against running tasktool start.
    assert "tasktool start" in span and (
        "do not call" in span.lower() or "do not" in span.lower()
    ), "early-exit block must forbid `tasktool start` from a subagent"
```

- [ ] **Step 5b.4: Run the transcript test**

```sh
python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py::test_subagent_early_exit_load_matches_fixture -v
```

Expected: PASS.

- [ ] **Step 5b.5: Commit**

```sh
git add tools/tasktool/tests/fixtures/p5_s3_subagent_load.txt tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
git commit -m "P5.S3: subagent early-exit transcript fixture + behavior regression test"
```

---

## Task 6: Write failing subagent-guard tests for `tasktool start`

**Files:**
- Modify: `tools/tasktool/tests/test_lifecycle_start.py` (append tests)

Existing scaffolding (`run`, `seed`, `tasklist`, `ready_chain` helpers and the `tasktool start` `subprocess.run(...)` pattern) is already in place — use it.

- [ ] **Step 6.1: Append the guard tests**

Append these tests to `tools/tasktool/tests/test_lifecycle_start.py`:

```python
REFUSAL_MARKER = "Subagents must inherit the parent's worktree"

# Spec §5.3 verbatim sentence; the trailing period is load-bearing and
# asserted by test_start_refusal_message_matches_spec_verbatim.
REFUSAL_SPEC_SENTENCE_TEMPLATE = (
    "Subagents must inherit the parent's worktree; call the parent or "
    "'cd' into the existing recorded path: {worktree_path}."
)


def _run_with_env(root, *args, extra_env=None):
    """Like the module-level `run` but allows injecting / replacing env vars."""
    env = os.environ.copy()
    env["PYTHONPATH"] = PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
    if extra_env:
        # `None` means delete.
        for k, v in extra_env.items():
            if v is None:
                env.pop(k, None)
            else:
                env[k] = v
    return subprocess.run(
        [sys.executable, str(TOOL), "--project-root", str(root), *args],
        text=True,
        capture_output=True,
        env=env,
    )


def test_start_refuses_when_superstar_subagent_role_set(tmp_path):
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={"SUPERSTAR_SUBAGENT_ROLE": "implementer"},
    )
    assert r.returncode != 0, r.stdout + r.stderr
    assert REFUSAL_MARKER in (r.stderr + r.stdout)


def test_start_refuses_when_claude_agent_role_is_subagent(tmp_path):
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={
            "SUPERSTAR_SUBAGENT_ROLE": None,
            "CLAUDE_AGENT_ROLE": "subagent",
        },
    )
    assert r.returncode != 0, r.stdout + r.stderr
    assert REFUSAL_MARKER in (r.stderr + r.stdout)


def test_start_proceeds_when_claude_agent_role_is_coordinator(tmp_path):
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={
            "SUPERSTAR_SUBAGENT_ROLE": None,
            "CLAUDE_AGENT_ROLE": "coordinator",
        },
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_start_proceeds_when_claude_agent_role_is_main(tmp_path):
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={
            "SUPERSTAR_SUBAGENT_ROLE": None,
            "CLAUDE_AGENT_ROLE": "main",
        },
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_start_refuses_when_force_subagent_set(tmp_path):
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={
            "SUPERSTAR_SUBAGENT_ROLE": None,
            "CLAUDE_AGENT_ROLE": None,
            "SUPERSTAR_FORCE_SUBAGENT": "1",
        },
    )
    assert r.returncode != 0, r.stdout + r.stderr
    assert REFUSAL_MARKER in (r.stderr + r.stdout)


def test_start_proceeds_in_plain_shell(tmp_path):
    """False-negative guard: under `env -i`-equivalent (all three signals
    unset), start must proceed. Spec §5.3."""
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={
            "SUPERSTAR_SUBAGENT_ROLE": None,
            "CLAUDE_AGENT_ROLE": None,
            "SUPERSTAR_FORCE_SUBAGENT": None,
        },
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_start_signal_precedence_superstar_wins(tmp_path):
    """When SUPERSTAR_SUBAGENT_ROLE is set, the refusal message must mention
    it (or at minimum, the call must refuse) even if CLAUDE_AGENT_ROLE would
    on its own have produced a proceed-result. Spec §5.3."""
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={
            "SUPERSTAR_SUBAGENT_ROLE": "implementer",
            "CLAUDE_AGENT_ROLE": "coordinator",   # would have allowed
        },
    )
    assert r.returncode != 0, (
        "SUPERSTAR_SUBAGENT_ROLE must win over CLAUDE_AGENT_ROLE=coordinator"
    )
    assert REFUSAL_MARKER in (r.stderr + r.stdout)


def test_start_refusal_message_matches_spec_verbatim(tmp_path):
    """The spec sentence at §5.3 must appear verbatim (including trailing
    period) in the emitted refusal output. Extra suffixes after the period
    are permitted (structured diagnostics), but the sentence itself cannot
    drift."""
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={"SUPERSTAR_SUBAGENT_ROLE": "implementer"},
    )
    assert r.returncode != 0
    # The recorded worktree_path is <not recorded> for a fresh seed; this is
    # what the spec wants substituted in place of <worktree_path>.
    expected_sentence = REFUSAL_SPEC_SENTENCE_TEMPLATE.format(
        worktree_path="<not recorded>"
    )
    combined = r.stderr + r.stdout
    assert expected_sentence in combined, (
        f"refusal message must contain the spec sentence verbatim "
        f"(including trailing period). Looking for:\n  {expected_sentence!r}\n"
        f"Got:\n{combined!r}"
    )


def test_start_env_i_bash_subshell_proceeds(tmp_path):
    """End-to-end plain-shell check: spawn the tasktool start under
    `env -i bash -c ...` so absolutely nothing leaks from the test runner's
    environment beyond PATH + PYTHONPATH. Spec §6 P5.S3 'no false positives
    in plain shells, including under env -i bash'."""
    seed(tmp_path)
    cmd = (
        f"PATH={os.environ.get('PATH','')} "
        f"PYTHONPATH={PYTHONPATH} "
        f"{sys.executable} {TOOL} --project-root {tmp_path} start P1.S1"
    )
    r = subprocess.run(
        ["env", "-i", "bash", "-c", cmd],
        text=True, capture_output=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
```

- [ ] **Step 6.2: Run the new tests and verify they fail (guard not yet implemented)**

```sh
python -m pytest tools/tasktool/tests/test_lifecycle_start.py -k "subagent or precedence or env_i_bash or plain_shell" -v
```

Expected: refusal tests FAIL (start currently succeeds with no env guard). Proceed tests PASS. If the proceed tests fail at this stage, stop — the test scaffolding is wrong, not the guard.

- [ ] **Step 6.3: No commit yet.** The tests land with the guard implementation in Task 7.

---

## Task 7: Implement the subagent guard in `cmd_start`

**Files:**
- Modify: `tools/tasktool/commands.py` (`cmd_start` around line 659; add module-level helper above it)

- [ ] **Step 7.1: Add the env-signal helper at module scope**

Insert above the existing `def cmd_start(...)` definition (around line 658) the following helper:

```python
import os as _os  # if not already imported at module top; otherwise reuse the existing import

_SUBAGENT_REFUSAL = (
    "Subagents must inherit the parent's worktree; call the parent or "
    "'cd' into the existing recorded path: {worktree_path}."
)


def _subagent_signal() -> str | None:
    """Return the name of the first env signal indicating dispatched-subagent
    status, in precedence order, or None if no signal is present.

    Precedence (spec §5.3):
      1. SUPERSTAR_SUBAGENT_ROLE  -- any non-empty value
      2. CLAUDE_AGENT_ROLE        -- any value other than 'coordinator' / 'main'
      3. SUPERSTAR_FORCE_SUBAGENT -- value == '1' (test-only override)

    No fingerprinting fallback. Absence of all three signals = not a subagent.
    """
    role = _os.environ.get("SUPERSTAR_SUBAGENT_ROLE", "")
    if role.strip():
        return "SUPERSTAR_SUBAGENT_ROLE"
    claude_role = _os.environ.get("CLAUDE_AGENT_ROLE", "").strip().lower()
    if claude_role and claude_role not in {"coordinator", "main"}:
        return "CLAUDE_AGENT_ROLE"
    if _os.environ.get("SUPERSTAR_FORCE_SUBAGENT", "") == "1":
        return "SUPERSTAR_FORCE_SUBAGENT"
    return None
```

(If `os` is already imported at the top of `commands.py`, drop the `_os` alias and reference `os.environ` directly. Confirm with `grep -n "^import os\|^from os " tools/tasktool/commands.py` before editing.)

- [ ] **Step 7.2: Wire the guard into `cmd_start`**

Replace the body of `cmd_start` (currently lines 659–666):

```python
def cmd_start(*, repo_root: Path, id: str, resume: bool = False) -> None:
    signal = _subagent_signal()
    if signal is not None:
        # Lookup worktree_path for a more useful refusal message. We cannot
        # call _load() before _write_context() in the normal flow; use a
        # best-effort cheap read for the message only.
        worktree_path = "<not recorded>"
        try:
            with _write_context(repo_root) as write_root:
                p = _load(write_root)
                _qid, _container, item = _find_item(p, id)
                worktree_path = getattr(item, "worktree_path", None) or "<not recorded>"
        except Exception:
            pass
        raise CommandError(
            _SUBAGENT_REFUSAL.format(worktree_path=worktree_path)
            + f" [signal: {signal}]"
        )
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        kind = parse_id(qid)[0]
        _start_item(qid, item, resume=resume)
        _save(write_root, p)
        _notify_status(qid=qid, kind=kind, status=item.status, title=item.title)
```

Notes:
- `CommandError` is the existing error class raised by other commands; the CLI surface in `cli.py` already converts it to a non-zero exit with the message on stderr (verify with `grep -n "CommandError" tools/tasktool/cli.py`).
- The `worktree_path` field will not exist on existing slice models until P5.S1 lands; the `getattr(..., None)` keeps the message robust against that.
- The spec's refusal sentence (`Subagents must inherit the parent's worktree; call the parent or 'cd' into the existing recorded path: <worktree_path>.`) is preserved **verbatim, including the trailing period**, as a substring of the emitted error. A `[signal: <name>]` suffix is appended after the period as structured diagnostics. The verbatim-substring assertion in Task 6 (`test_start_refusal_message_matches_spec_verbatim`) gates against drift on the spec sentence itself.

- [ ] **Step 7.3: Run the guard tests; verify they now pass**

```sh
python -m pytest tools/tasktool/tests/test_lifecycle_start.py -v
```

Expected: all tests pass — both the new guard tests from Task 6 and the pre-existing lifecycle-start tests.

- [ ] **Step 7.4: Run the full tasktool suite to catch regressions**

```sh
python -m pytest tools/tasktool/tests -q
```

Expected: green. If a pre-existing test that calls `tasktool start` in a fixture that happens to have `CLAUDE_AGENT_ROLE` set in the test runner's env starts failing, fix the test by setting `SUPERSTAR_SUBAGENT_ROLE`/`CLAUDE_AGENT_ROLE` to `None` in its env explicitly — the guard is intentionally strict.

- [ ] **Step 7.5: Commit**

```sh
git add tools/tasktool/commands.py tools/tasktool/tests/test_lifecycle_start.py
git commit -m "P5.S3: refuse tasktool start when invoked as a dispatched subagent (three env signals)"
```

---

## Task 8: Update subagent-dispatch prompt templates to export `SUPERSTAR_SUBAGENT_ROLE`

**Files:**
- Modify: `skills/subagent-driven-development/implementer-prompt.md`
- Modify: `skills/subagent-driven-development/spec-reviewer-prompt.md`
- Modify: `skills/subagent-driven-development/code-quality-reviewer-prompt.md`
- Create: `tools/tasktool/tests/test_subagent_prompt_shim.py`

Background: there is no native env-injection point on Claude Code's `Task` tool. The closest analogue to a "shim" in this repo is the coordinator-facing prompt template in `skills/subagent-driven-development/*-prompt.md`. We extend those templates with an explicit directive: the dispatched subagent exports `SUPERSTAR_SUBAGENT_ROLE=<role>` in its shell session before running tooling. The shim test asserts the directive is present and names a non-empty role; the runtime guard in Task 7 catches the env var when it is set.

- [ ] **Step 8.1: Append the directive to `implementer-prompt.md`**

Find the `## Before You Begin` section (around line 20) of `skills/subagent-driven-development/implementer-prompt.md`. Insert a new section **before** it:

```markdown
    ## Subagent Role (mandatory)

    You were dispatched by a coordinator. The first command you run in any
    shell you open MUST be:

    ```sh
    export SUPERSTAR_SUBAGENT_ROLE=implementer
    ```

    This is a load-bearing signal. The tasktool CLI uses it to refuse
    `tasktool start <id>` (slice creation belongs to the parent). Do not
    unset it; do not start the slice yourself; do not run `tasktool start`
    at all. If you need to record progress, use `tasktool note`,
    `tasktool ref`, or ask the coordinator.

```

- [ ] **Step 8.2: Apply the same edit to `spec-reviewer-prompt.md` with role=`spec-reviewer`**

Same section, same wording, but the `export` line is:

```sh
export SUPERSTAR_SUBAGENT_ROLE=spec-reviewer
```

- [ ] **Step 8.3: Apply the same edit to `code-quality-reviewer-prompt.md` with role=`code-quality-reviewer`**

```sh
export SUPERSTAR_SUBAGENT_ROLE=code-quality-reviewer
```

- [ ] **Step 8.4: Create the shim-presence test**

Write `tools/tasktool/tests/test_subagent_prompt_shim.py`:

```python
"""Spec §6 P5.S3 "Claude shim and Codex shim integration tests confirm
SUPERSTAR_SUBAGENT_ROLE is exported in dispatched subagents and absent in
coordinator sessions."

Implementation note: the harnesses (Claude Code, Codex) do not expose an env
injection point on their native dispatch tools. The supported mechanism is
the coordinator-facing prompt template: dispatched subagents are instructed
to export SUPERSTAR_SUBAGENT_ROLE=<role> as their first shell command. These
tests assert the directive is present and unambiguous in each template, and
that coordinator-side documentation does NOT instruct the coordinator to set
the same variable in its own session.
"""
from __future__ import annotations
from pathlib import Path

PROMPTS = Path(__file__).resolve().parents[3] / "skills" / "subagent-driven-development"

EXPECTED = {
    "implementer-prompt.md": "implementer",
    "spec-reviewer-prompt.md": "spec-reviewer",
    "code-quality-reviewer-prompt.md": "code-quality-reviewer",
}


def test_each_subagent_prompt_exports_subagent_role():
    for fname, role in EXPECTED.items():
        text = (PROMPTS / fname).read_text()
        expected = f"export SUPERSTAR_SUBAGENT_ROLE={role}"
        assert expected in text, (
            f"{fname} must contain `{expected}` so dispatched subagents "
            f"trigger the tasktool subagent guard (spec §5.3)."
        )


def test_each_subagent_prompt_forbids_calling_tasktool_start():
    for fname in EXPECTED:
        text = (PROMPTS / fname).read_text()
        # The directive paragraph must explicitly forbid tasktool start.
        assert "do not run `tasktool start`" in text.lower() or \
               "do not call `tasktool start`" in text.lower() or \
               "do not start the slice yourself" in text.lower(), (
            f"{fname} must explicitly forbid the dispatched subagent from "
            f"calling tasktool start"
        )


def test_coordinator_skill_does_not_set_subagent_role_for_itself():
    """The coordinator must NOT export SUPERSTAR_SUBAGENT_ROLE in its own
    session — if it did, every `tasktool start` from the coordinator would
    refuse. Spec §5.3."""
    skill = (PROMPTS / "SKILL.md").read_text()
    assert "export SUPERSTAR_SUBAGENT_ROLE" not in skill, (
        "subagent-driven-development SKILL.md must not instruct the "
        "coordinator to export SUPERSTAR_SUBAGENT_ROLE for itself"
    )
```

- [ ] **Step 8.5: Add a simulated-harness dispatch transcript test**

Append to `tools/tasktool/tests/test_subagent_prompt_shim.py`:

```python
import os
import subprocess
import sys
from pathlib import Path

PYTHONPATH_REPO = str(Path(__file__).resolve().parents[2])
TASKTOOL_MAIN = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"


def test_simulated_subagent_dispatch_refuses_tasktool_start(tmp_path):
    """Simulated 'harness dispatch' end-to-end. We model what happens when a
    coordinator-dispatched subagent follows the prompt-template directive:
    1. The subagent opens a shell (we use `bash -c`, env scrubbed via env -i).
    2. The subagent runs `export SUPERSTAR_SUBAGENT_ROLE=implementer` as its
       first command (per the directive landed in Task 8 Step 8.1).
    3. The subagent then attempts `tasktool start <slice-id>`.
    Expected: tasktool refuses with the spec's verbatim sentence.

    This is the closest thing to a 'real harness integration test' the repo
    can express without an actual Task-tool wrapper: it proves the runtime
    guard fires for a subagent that followed the directive, in a shell with
    no leaked env from the test runner."""
    # Seed a tasklist in tmp_path using the local CLI flow.
    (tmp_path / "docs").mkdir()
    def _seed(*args, env_extra=None):
        env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": PYTHONPATH_REPO}
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            [sys.executable, str(TASKTOOL_MAIN),
             "--project-root", str(tmp_path), *args],
            env=env, text=True, capture_output=True,
        )
    assert _seed("config", "init-local").returncode == 0
    assert _seed("init", "--project", "demo").returncode == 0
    assert _seed("create", "phase", "--title", "Phase").returncode == 0
    assert _seed("create", "slice", "P1", "--title", "Slice").returncode == 0

    # Simulated dispatched-subagent shell. `env -i` strips inherited env so
    # the only signal is the one the directive tells the subagent to export.
    script = (
        f"export SUPERSTAR_SUBAGENT_ROLE=implementer && "
        f"{sys.executable} {TASKTOOL_MAIN} "
        f"--project-root {tmp_path} start P1.S1"
    )
    r = subprocess.run(
        ["env", "-i",
         f"PATH={os.environ.get('PATH','')}",
         f"PYTHONPATH={PYTHONPATH_REPO}",
         "bash", "-c", script],
        text=True, capture_output=True,
    )
    assert r.returncode != 0, (
        f"simulated subagent should have been refused; stdout={r.stdout!r} "
        f"stderr={r.stderr!r}"
    )
    spec_sentence = (
        "Subagents must inherit the parent's worktree; call the parent or "
        "'cd' into the existing recorded path: <not recorded>."
    )
    assert spec_sentence in (r.stdout + r.stderr), (
        f"refusal did not carry the spec sentence verbatim; "
        f"got: {r.stdout + r.stderr!r}"
    )


def test_simulated_coordinator_dispatch_proceeds(tmp_path):
    """The mirror case: a coordinator that did NOT export
    SUPERSTAR_SUBAGENT_ROLE (i.e. did not run the dispatched-subagent
    directive) must be able to call `tasktool start` normally. This pins
    down 'absent in coordinator sessions' from spec §6 P5.S3."""
    (tmp_path / "docs").mkdir()
    def _seed(*args):
        return subprocess.run(
            [sys.executable, str(TASKTOOL_MAIN),
             "--project-root", str(tmp_path), *args],
            env={"PATH": os.environ.get("PATH", ""),
                 "PYTHONPATH": PYTHONPATH_REPO},
            text=True, capture_output=True,
        )
    assert _seed("config", "init-local").returncode == 0
    assert _seed("init", "--project", "demo").returncode == 0
    assert _seed("create", "phase", "--title", "Phase").returncode == 0
    assert _seed("create", "slice", "P1", "--title", "Slice").returncode == 0

    script = (
        f"{sys.executable} {TASKTOOL_MAIN} "
        f"--project-root {tmp_path} start P1.S1"
    )
    r = subprocess.run(
        ["env", "-i",
         f"PATH={os.environ.get('PATH','')}",
         f"PYTHONPATH={PYTHONPATH_REPO}",
         "bash", "-c", script],
        text=True, capture_output=True,
    )
    assert r.returncode == 0, (
        f"coordinator (no SUPERSTAR_SUBAGENT_ROLE) should have proceeded; "
        f"stdout={r.stdout!r} stderr={r.stderr!r}"
    )
```

This is not a real Claude/Codex harness integration — those would require harness instrumentation outside this repo's reach — but it is the highest-fidelity simulation available: an `env -i` shell with only the directive's env mutation, exercising the real tasktool binary path. The plan acknowledges this scope honestly: if a future harness exposes real dispatch instrumentation, the simulated transcript can be replaced with a real one in a follow-up X-item.

- [ ] **Step 8.6: Run the shim tests**

```sh
python -m pytest tools/tasktool/tests/test_subagent_prompt_shim.py -v
```

Expected: all five tests PASS (three template-presence tests + two simulated-dispatch tests). If `test_coordinator_skill_does_not_set_subagent_role_for_itself` fails, the coordinator SKILL was edited incorrectly in Task 9 — return there. If the simulated-dispatch tests fail, the guard in Task 7 is wrong, not this task.

- [ ] **Step 8.7: Commit**

```sh
git add skills/subagent-driven-development/implementer-prompt.md \
        skills/subagent-driven-development/spec-reviewer-prompt.md \
        skills/subagent-driven-development/code-quality-reviewer-prompt.md \
        tools/tasktool/tests/test_subagent_prompt_shim.py
git commit -m "P5.S3: dispatched-subagent prompts export SUPERSTAR_SUBAGENT_ROLE; add shim presence tests"
```

---

## Task 9: Append the subagent paragraph to `tasklist-discipline`

**Files:**
- Modify: `skills/tasklist-discipline/SKILL.md` (add a paragraph; preserve existing text)

Insert this paragraph immediately after the existing "Implementation isolation boundary" paragraph (currently around line 28) — i.e. before `## Conceptual model`:

```markdown
**Subagent rule (load-bearing).** Parents create or adopt worktrees via `tasktool start <slice-id>`. Dispatched subagents inherit the parent's cwd and **must not** call `tasktool start` — implementation work happens inside the parent's already-recorded worktree, and a subagent starting a slice double-counts the lifecycle row and corrupts the slice's worktree fields. Tasktool refuses `tasktool start` when it observes a dispatched-subagent signal (`SUPERSTAR_SUBAGENT_ROLE`, `CLAUDE_AGENT_ROLE`, or the test-only `SUPERSTAR_FORCE_SUBAGENT=1`). The runtime guard is detection-dependent — a coordinator that loses its env (e.g. `env -i`) will look like a top-level invocation — so **this prose rule is the load-bearing guard**; the env signals are belt-and-braces.
```

- [ ] **Step 9.1: Apply the edit**

Use the Edit tool with `old_string` anchored on the last sentence of the current "Implementation isolation boundary" paragraph (`authoritative routing sends the mutation to the configured checkout.`) and `new_string` extending it with the paragraph above.

- [ ] **Step 9.2: Verify with grep**

```sh
grep -n "Subagent rule (load-bearing)" skills/tasklist-discipline/SKILL.md
```

Expected: one match, between the isolation paragraph and `## Conceptual model`.

- [ ] **Step 9.3: Commit**

```sh
git add skills/tasklist-discipline/SKILL.md
git commit -m "P5.S3: tasklist-discipline forbids subagent tasktool start (load-bearing prose rule)"
```

---

## Task 10: Add the one-line cross-references in `executing-plans` and `subagent-driven-development`

**Files:**
- Modify: `skills/executing-plans/SKILL.md` (cross-reference + worktree-ownership clarifier in Step 0; do NOT change the Step 3 close semantics — that text remains unchanged per spec §5.3.2)
- Modify: `skills/subagent-driven-development/SKILL.md` (one-line reminder added to the existing worktree paragraph in "Slice and phase boundaries")

- [ ] **Step 10.1: Update `executing-plans/SKILL.md` Step 0**

Replace the existing Step 0 (`### Step 0: Verify Implementation Workspace`) body with a tighter version that defers to the rewritten skill:

```markdown
### Step 0: Verify Implementation Workspace

Before reading the plan as executable work, run `[[using-git-worktrees]]` as the first executable gate. The parent coordinator (you) creates or adopts the slice worktree via `tasktool start <slice-id>` — that single command is the lifecycle gate. Verify one of these is true:

- You are already in a linked worktree for this slice and the slice row's `worktree_path` matches your cwd; or
- You ran `tasktool start <slice-id>` and `cd`d into the printed path.

Subagents dispatched by you inherit cwd and must not call `tasktool start` themselves — see `[[tasklist-discipline]]` "Subagent rule (load-bearing)" and the `<SUBAGENT-STOP>` block at the top of `[[using-git-worktrees]]`.

If you are in a normal repo checkout, especially on `main` or `master`, it is read-only/planning-only by default. Do not edit files, run tests that create artifacts, write reviewer chains, or mutate tasktool state for the implementation slice there unless the human partner explicitly opts out of isolation in the current turn.

Parallel or adjacent slices require separate worktrees. Same repo on a different branch is not enough if the workspace is shared.
```

- [ ] **Step 10.2: Update `subagent-driven-development/SKILL.md`**

Find the paragraph in the "Slice and phase boundaries" section that currently begins `Before dispatching any implementation subagent, run [[using-git-worktrees]]…` (around line 35). Append, after that paragraph, this single line:

```markdown
**Subagents inherit your cwd and must not call `tasktool start`.** The implementer/spec-reviewer/code-quality-reviewer prompt templates already export `SUPERSTAR_SUBAGENT_ROLE` so tasktool refuses subagent-side `start` calls; see `[[tasklist-discipline]]` "Subagent rule" for the load-bearing prose rule.
```

- [ ] **Step 10.3: Confirm we did NOT touch `finishing-a-development-branch`**

```sh
git diff --name-only HEAD~5..HEAD -- skills/finishing-a-development-branch/
```

Expected: empty output. If anything appears, revert it — that skill is owned by P5.S2.

- [ ] **Step 10.4: Run the full pytest suite once more**

```sh
python -m pytest tools/tasktool/tests -q
```

Expected: green.

- [ ] **Step 10.5: Commit**

```sh
git add skills/executing-plans/SKILL.md skills/subagent-driven-development/SKILL.md
git commit -m "P5.S3: cross-reference rewritten using-git-worktrees skill from executing-plans and subagent-driven-development"
```

---

## Task 11: Final verification + slice close handoff

**Files:** none — verification + handoff only.

- [ ] **Step 11.1: Re-run validate and the full pytest suite**

```sh
tools/tasktool/tasktool validate --strict-format
python -m pytest tools/tasktool/tests -q
```

Expected: both green.

- [ ] **Step 11.2: Verify the doc shape end-to-end**

```sh
wc -l skills/using-git-worktrees/SKILL.md
grep -c "<SUBAGENT-STOP>" skills/using-git-worktrees/SKILL.md
ls skills/using-git-worktrees/references/submodules.md
grep -c "Subagent rule (load-bearing)" skills/tasklist-discipline/SKILL.md
grep -c "export SUPERSTAR_SUBAGENT_ROLE=implementer" skills/subagent-driven-development/implementer-prompt.md
grep -c "export SUPERSTAR_SUBAGENT_ROLE=spec-reviewer" skills/subagent-driven-development/spec-reviewer-prompt.md
grep -c "export SUPERSTAR_SUBAGENT_ROLE=code-quality-reviewer" skills/subagent-driven-development/code-quality-reviewer-prompt.md
```

Expected: line count ≤ 40; each `grep -c` returns ≥ 1; the `ls` call succeeds.

- [ ] **Step 11.3: Stop here.**

Do **not** run `tasktool close P5.S3` yet. Slice close is gated by `[[external-review]] --kind post-slice` per the coordinator's workflow, which happens outside this implementation plan. Hand the slice back to the coordinator with a summary of the commits and `git status` clean.

---

## Self-Review Checklist

**1. Spec coverage**

| Spec item | Covered by |
|---|---|
| §5.5 skill rewrite structure | Task 3 (rewrite), Task 4 (shape tests) |
| §5.5 submodule guidance to `references/submodules.md` | Task 2 |
| §5.6 `tasklist-discipline` paragraph | Task 9 |
| §5.3.2 `executing-plans` cross-references | Task 10.1 |
| §5.3.2 `subagent-driven-development` one-line reminder | Task 10.2 |
| §5.3.2 leave `finishing-a-development-branch` alone | Task 10.3 (explicit check) |
| §5.3 three-signal subagent guard + precedence | Task 6 (tests), Task 7 (implementation) |
| §5.3 refusal message verbatim | Task 7 (`_SUBAGENT_REFUSAL` constant) |
| §5.3 no fingerprinting fallback | Task 7 (helper only reads env) |
| §5.3 plain-shell false-negative under `env -i bash` | Task 6 (`test_start_env_i_bash_subshell_proceeds`) |
| §5.3 `SUPERSTAR_SUBAGENT_ROLE` shim export | Task 8 (best-effort prose guard via prompt templates + presence tests + simulated dispatch transcript test). See "Shim scope" preamble for the limits of this implementation. |
| §6 P5.S3 skill body ≤ 40 lines + `<SUBAGENT-STOP>` test | Task 4 |
| §6 P5.S3 token-budget regression — silent-growth detection | Task 5 (`tools/tasktool/tests/fixtures/p5_s3_skill_body.txt` + byte-for-byte diff test) |
| §6 P5.S3 token-budget regression — subagent transcript behavior | Task 5b (`tools/tasktool/tests/fixtures/p5_s3_subagent_load.txt` + early-exit span behavior test) |
| §6 P5.S3 "exported in dispatched subagents, absent in coordinator" | Task 8 Step 8.5 (`test_simulated_subagent_dispatch_refuses_tasktool_start` + `test_simulated_coordinator_dispatch_proceeds`) |

**2. Placeholder scan:** none of the tasks contain "TBD", "TODO", "implement later", or "fill in details". Every code/edit step shows the exact content.

**3. Type consistency:** `_subagent_signal()` returns `str | None`; `CommandError` is the existing class in `tools/tasktool/commands.py`; `_SUBAGENT_REFUSAL` is a string template with one named field (`{worktree_path}`). Helper name (`_subagent_signal`) is used in only one call site (Task 7 Step 7.2).

**4. Scheduling check:** `tasktool show P5.S3` confirms `depends_on: [P5.S1, P5.S2]`, `planning_status: proposed`. The plan does not change the dependency graph; no `tasktool deps` mutation is required. Ratification (`tasktool ratify`) is the coordinator's responsibility after this plan passes external review.

**5. Slice scope discipline:** Tasks 2, 3, 4, 5 touch only the rewritten skill and its tests. Tasks 6, 7 touch only `tasktool commands.py` and `test_lifecycle_start.py`. Task 8 touches only subagent-driven-development prompt templates and the new shim test. Tasks 9, 10 touch only the cross-reference text in tasklist-discipline / executing-plans / subagent-driven-development SKILL.md. `finishing-a-development-branch` is explicitly checked at Task 10.3 and never modified.

**6. Open questions / deferred concerns:**
- The harness ("Claude shim" / "Codex shim") does not expose an env-injection mechanism on its native dispatch tool. The plan implements the shim as a documented directive in the coordinator's dispatch templates, asserted by template-presence tests **and** by a simulated-harness transcript test (`env -i bash -c` exercising the real tasktool binary; Task 8 Step 8.5). The plan's "Shim scope" preamble explicitly downgrades this from a real harness integration to a best-effort prose guard backed by the runtime refusal. If a future harness change exposes real env injection on `Task` / `spawn_agent`, the prompt-template directive can be retired in a follow-up X-item without breaking the runtime guard.
- The refusal message preserves the spec's sentence verbatim (including the trailing period) as a substring; a `[signal: <name>]` diagnostic suffix follows after the period. The verbatim-substring assertion in `test_start_refusal_message_matches_spec_verbatim` (Task 6) gates against drift.
- §5.3.2 of the spec (`:212-214`) and the P5.S3 slice description (`:275-277`) disagree about who owns the `finishing-a-development-branch` edit. The plan treats §5.3.2 as authoritative (P5.S2 owns it) and adds Task 1.4 to verify P5.S2 actually shipped that edit before this slice runs. If P5.S2 closed without it, this slice stops and surfaces the gap rather than papering over it.
