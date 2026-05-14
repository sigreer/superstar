---
name: executing-plans
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Note:** Tell your human partner that Superstar works much better with access to subagents. The quality of its work will be significantly higher if run on a platform with subagent support (such as Claude Code or Codex). If subagents are available, use superstar:subagent-driven-development instead of this skill.

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns about the plan
3. If concerns: Raise them with your human partner before starting
4. If no concerns: Create TodoWrite and proceed

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Run the in-loop internal review per `[[requesting-internal-review]]` if the plan or task calls for it
5. Mark as completed

### Step 3: Close Each Slice (REQUIRED GATE)

When the last task in a slice is verified — **before flipping slice status** — run the external-review gate:

- Announce: "I'm using the external-review skill to gate slice close."
- **REQUIRED SUB-SKILL:** `superstar:external-review` with `--kind post-slice`, passing the plan as `--file` and the spec + TASKLIST.md as `--context`.
- On `revise`: address findings, re-submit. Loop until verdict ∈ {ready, ready with small edits}.
- Only then flip the slice status per `[[tasklist-discipline]]`.

**This gate is separate from any per-task internal review.** Even when the in-loop internal/code-quality review has approved every task in the slice, the external review at slice boundary is still required. They are different reviews with different scopes (per-task vs. per-slice) and different reviewers (in-session subagent vs. third-party CLI).

### Step 4: Close the Phase (REQUIRED GATE)

When the last slice in a phase has closed — **before archiving the phase**:

- **REQUIRED SUB-SKILL:** `superstar:external-review` with `--kind post-phase`.
- Same gate rules. Iterate until accepted.
- Then archive the phase per `[[tasklist-discipline]]`.

### Step 5: Complete Development

After all tasks, slices, and the phase are closed:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use superstar:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent
- **Internal review ≠ external review.** Per-task internal review is in-loop and may run more than once per task. External review is a separate, out-of-loop gate at slice and phase boundaries. One does not satisfy the other.
- **Never flip a slice or phase to ✅ before its external review returns a `ready` verdict.**

## Integration

**Required workflow skills:**
- **superstar:using-git-worktrees** - Ensures isolated workspace (creates one or verifies existing)
- **superstar:writing-plans** - Creates the plan this skill executes
- **superstar:external-review** - Run `--kind post-slice` after each slice and `--kind post-phase` at phase close
- **superstar:tasklist-discipline** - Slice/phase status flips and phase archival rules
- **superstar:finishing-a-development-branch** - Complete development after all tasks
