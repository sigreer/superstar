---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** If working in an isolated worktree, it should have been created via the `superstar:using-git-worktrees` skill at execution time.

**Save plans to:** `docs/plans/YYYY-MM-DD-<id>-<slug>.md` where `<id>` is the tasktool ID for the work (e.g. `p2-s3a`). If the project has no `docs/tasklist.json`, omit the ID segment. User preferences for plan location override this default.

**tasktool integration:** If `docs/tasklist.json` exists, this plan must correspond to a row in it. See [[tasklist-discipline]] for the ID scheme. **Before writing the plan file, verify the row for `<id>` exists** — run `tasktool show <id>` and confirm exit 0. If it doesn't (e.g. a spec was committed without a row, though the pre-commit hook should have caught that), stop and create the row via `tasktool create …` per [[tasklist-discipline]]. Never let the plan be the artifact that mints an ID.

**Artifact transaction:** Before writing the plan and handoff, register future paths with `tasktool prepare existing <id> --plan <plan-path> --handoff <handoff-path>`. After writing each file, run `tasktool artifact add <id> --kind plan --path <plan-path>` and `tasktool artifact add <id> --kind handoff --path <handoff-path>`. After plan review passes, register the reviewer chain, run `tasktool artifact status <id> --strict`, and use `tasktool artifact commit <id> --message "<id>: add <slug> plan"` unless the user explicitly asked not to commit.

**Lifecycle start step:** When docs/tasklist.json exists and the plan executes a slice, the first execution step must be `tasktool start <slice-id>` before dispatching or editing implementation files. Use the concrete slice ID in generated plans, not the placeholder. This is separate from TodoWrite and from prose status updates.

**Scheduling ratification:** For slice plans, inspect `tasktool show <slice-id>` and `tasktool schedule <phase-id>` before drafting. The plan must explicitly confirm or update `depends_on`, `parallel_group`, and whether the slice remains independently plannable/executable. If the spec/plan work discovers a dependency change, update it with `tasktool deps`; when the plan settles, run `tasktool ratify <slice-id>` so coordinators can rely on `tasktool ready-slices <phase-id>`.

**Integration surfaces & reservations:** A slice plan that may run in parallel with siblings must include a **surface/reservation table** — for this slice (and any sibling it could overlap), list `integration_surfaces`, `reservations` (`resource:value` + scope), and `coordination_group`. Declare them on the tracker with `tasktool surface add` / `tasktool reserve add` / `tasktool coordinate`, then run `tasktool surface check <phase-id>` before ratifying. Do not place slices that share a surface in the same `parallel_group` without a `depends_on` (serialize) or a `coordination_group` (coordinate). A duplicate scarce-resource allocation is refused at declaration time — pick a free value rather than `--force`, unless you genuinely intend a coordinated shared allocation and record the reason.

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task

## Remember
- Exact file paths always
- Complete code in every step — if a step changes code, show the code
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits

## Self-Review

After writing the complete plan, look at the spec with fresh eyes and check the plan against it. This is a checklist you run yourself — not a subagent dispatch.

**1. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.

**2. Placeholder scan:** Search your plan for red flags — any of the patterns from the "No Placeholders" section above. Fix them.

**3. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

**4. Handoff artifact:** After the plan-review gate passes, confirm `docs/handoffs/<plan-stem>-prompt.md` exists on disk (run `ls`), was filled in (no `{{placeholder}}` strings remain), was registered with `tasktool artifact add`, and was echoed to chat in a fenced block. If any of those are missing, you skipped the Execution Handoff and must complete it before offering the execution choice.

**5. Scheduling check:** For slice plans, confirm the tasktool row is ratified and that the dependencies named in the plan match `tasktool schedule <phase-id>`. If the plan changed the dependency graph, update tasktool before external plan review so the reviewer sees the real scheduling contract.

If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a spec requirement with no task, add the task.

## External review checkpoints

This skill enforces two **gating** external reviews. Both are mandatory unless the user explicitly waives them.

**Communication contract:** Do not ask the user before these reviews unless blocked by a real ambiguity, missing dependency, or reviewer finding that requires a product decision. Continue automatically from spec review to plan drafting to plan review. Speak to the user only for genuine questions/blockers, or after both the spec and implementation plan have passed external review.

### 1. Spec review (after spec save, before plan drafting)

If the brainstorming step produced a spec, run `[[external-review]]` with `--kind spec` against that spec **before** starting the plan, whether it lives under `docs/specs/`, `docs/superstar/specs/`, or a user-specified path. Iterate until the verdict is `ready` or `ready with small edits`. During this stage you may apply the reviewer's edits directly — no parallel implementation subagents exist yet. Do not ask the user before this review unless blocked.

When `docs/tasklist.json` exists, a passing spec review is not complete until the spec transaction from `[[brainstorming]]` is closed: register the spec-review chain, run `tasktool artifact status <id> --strict`, and immediately commit the registered spec/reviewer artifacts with `tasktool artifact commit <id> --message "<id>: add <slug> spec"` unless the user explicitly asked not to commit. Do this before drafting the plan.

### 2. Plan review (after plan save, before execution handoff)

After saving the plan, run `[[external-review]]` with `--kind plan` against the plan, passing the spec as `--context`. Iterate until the verdict is `ready` or `ready with small edits` before proceeding to the handoff step below. Do not ask the user before this review unless blocked.

After the plan review verdict is `ready` / `ready with small edits`, set the slice's workflow step before handing off:

```bash
tasktool set <slice-id> --workflow-step implement
```

See [[tasklist-discipline]] for the field summary.

## Execution Handoff

After both reviews are passed, write a **handoff prompt** for the next session and offer the execution choice.

> **STOP — do not skip ahead to Step C.** Steps A and B produce the cross-session contract; Step C is the in-session menu. The two are not interchangeable. Do not offer the execution choice until `docs/handoffs/<plan-stem>-prompt.md` exists on disk **and** has been echoed to chat in a fenced block. Verify with `ls docs/handoffs/<plan-stem>-prompt.md` before proceeding to C.

### Red flags

| Thought | Reality |
|---------|---------|
| "I'll just offer the execution choice — the next session will figure out the rest." | No. The handoff doc is the cross-session contract. Without it, the next session reconstructs from scratch. |
| "The plan header already mentions `subagent-driven-development`, so a separate handoff is redundant." | No. The header names a skill; the handoff prompt names paths, IDs, and the reviewer chain. They are additive, not duplicative. |
| "Steps A/B are infrastructure — only Step C is user-visible." | The handoff file IS the user-visible payoff for the *next* session. Skipping A/B silently breaks that session. |

### Step A — Write the handoff prompt

Copy `handoff-prompt.template.md` (next to this SKILL) to `docs/handoffs/<plan-stem>-prompt.md` and fill in the placeholders: phase/slice ID, project name, absolute repo path, spec path, plan path, reviewer chain folder name. Register it with `tasktool artifact add <id> --kind handoff --path docs/handoffs/<plan-stem>-prompt.md`.

**Template resolution.** The template ships at `skills/writing-plans/handoff-prompt.template.md` inside this plugin. If that relative path doesn't resolve from your working directory, fall back to `$CLAUDE_PLUGIN_DIR/skills/writing-plans/handoff-prompt.template.md` (when running inside a Claude Code plugin context).

### Step B — Echo the handoff to chat

Print the filled-in handoff prompt to chat in a fenced block, plus the absolute path to the committed file, so the user can copy it into a new session immediately.

### Step C — Offer execution choice in-session

**Precondition:** Step A wrote `docs/handoffs/<plan-stem>-prompt.md` and Step B echoed it. If either is missing, return to A — do not print the menu below.


**"Plan complete and saved to `docs/plans/<filename>.md`. Handoff prompt saved to `docs/handoffs/<filename>-prompt.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, run external-review at each slice and phase close.

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use superstar:subagent-driven-development
- Fresh subagent per task + two-stage review + external-review at slice/phase boundaries

**If Inline Execution chosen:**
- **REQUIRED SUB-SKILL:** Use superstar:executing-plans
- Batch execution with checkpoints for review
