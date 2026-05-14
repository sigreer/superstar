# Coordinator handoff — reviewer rate-limit handling

You are the coordinator for implementing the **reviewer rate-limit handling** feature of `sigreer/skills/superstar` at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- Spec: [`docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md`](docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md) (review chain: `docs/reviewer/reviewer-rate-limit-handling-design-spec/`, closed at r2 `ready with small edits`).
- Plan: [`docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md`](docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md) (review chain: `docs/reviewer/reviewer-rate-limit-handling-plan-plan/`, closed at r4 `ready`).
- Reviewer chain folders that will be created during implementation:
  - Per slice: `docs/reviewer/reviewer-rate-limit-handling-plan-S{1..7}-post-slice/`
  - Phase close: `docs/reviewer/reviewer-rate-limit-handling-plan-post-phase/`

This repo has no `docs/TASKLIST.md`. Slice IDs come from the plan: **S1** (state file + detection foundations), **S2** (CLI integration), **S3** (rate-limited status semantics), **S4** (refusal coalescing), **S5** (new subcommands), **S6** (SKILL.md docs), **S7** (acceptance).

## Critical session-policy carry-over: external-review bypass

The reviewer CLI was rate-limited during the spec/plan phase of this work, which is the exact problem this feature solves. The user has had two prior policies in effect across this session:

1. **External-review bypass** at slice/phase boundaries while building this feature, because the reviewer is itself the rate-limited service we're fixing.
2. **Subagents must NOT auto-invoke `superstar:external-review`** under any circumstances. Implementer and fix subagents dispatched from this coordinator MUST receive explicit instructions to that effect in their prompts.

When dispatching subagents, include a line like:

> **Critical constraint:** Do NOT invoke `superstar:external-review`. Do NOT run `external-reviewer.py review`. The reviewer CLI is rate-limited.

If the rate limit clears mid-implementation AND the user explicitly re-enables external-review, the coordinator may then invoke `superstar:external-review --kind post-slice` at each slice close per normal workflow. Until that explicit re-enablement, skip the gate. Either way, document the choice in each slice's close-out commit message.

When the feature lands (S6 commits SKILL.md), future work can stop bypassing — the new menu becomes the canonical handling.

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than the process of delegating to a subagent. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
- **Update plan task checkboxes (`- [ ]` → `- [x]`)** as slices close. There is no TASKLIST.md to update.

## Pre-flight (read these first)

- Spec §4 architecture, §5 state file, §7.4 status semantics, §7.5 coalescing, §11 acceptance.
- Plan "Files at a glance", "Conventions used throughout the plan", "Spec → Plan mapping", "Bypass note" at the end.
- Plan Task 2.0 — the argparse refactor — is foundational. It MUST land before Tasks 2.1+ proceed, otherwise later snippets (manual-approve, ingest-response, show-limit, clear-limit dispatch) cannot be placed correctly.

The plan is structured TDD-first: every task writes a failing test, then minimal implementation, then commit. Subagents must follow this discipline.

## First action

Invoke `superstar:subagent-driven-development` and begin Slice 1 with Task 1.1. Read only the Task 1.1 block from the plan before dispatching the implementer — do not read the whole 2700-line plan into your context. Delegate task-text extraction to a subagent if needed.

## One quirk to know

Plan Task 2.0 (the argparse refactor) introduces real argparse subparsers. The current script uses a positional `choices=["review"]` argument. The refactor preserves all existing `review` flags and adds `--state-file` to it. All four new subcommands (`manual-approve`, `ingest-response`, `show-limit`, `clear-limit`) are added as sub-parsers under the same top-level. The dispatch block at the top of `main()` (after `parse_args()` + `--state-file` env hoist) routes non-`review` subcommands BEFORE any access of review-only args. Workers following the plan's Task 2.0 code blocks verbatim will not hit AttributeError.

If something in the script has drifted from the plan's snippets between when the plan was written and execution starts (unlikely, but possible if other branches merge), the subagent should flag DONE_WITH_CONCERNS rather than improvise.
