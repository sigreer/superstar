# Coordinator handoff — external-reviewer context optimisation (Slice 2)

You are the coordinator continuing the **external-reviewer context optimisation** work of `sigreer/skills/superstar` at `/home/simon/Dev/sigreer/skills/superstar`. Slice 1 has closed; you are picking up at Slice 2.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible. The `superstar:tasklist-discipline` and `superstar:external-review` skills apply at slice/phase boundaries.

## Inputs

- Spec: [`docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md`](docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md) (status: ready)
- Plan: [`docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md`](docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md) — Slice 1 checkboxes all ticked; Slice 2 (lines 1826–2682) and Slice 3 (lines 2684+) remain.
- S1 post-slice chain: `docs/reviewer/external-reviewer-context-optimisation-plan-S1-post-slice/` (closed r5 = `ready`, fully committed).
- Reviewer chains you will create:
  - `docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice/`
  - `docs/reviewer/external-reviewer-context-optimisation-plan-S3-post-slice/`
  - `docs/reviewer/external-reviewer-context-optimisation-plan-post-phase/`

There is no `docs/TASKLIST.md` in this repo. Slice IDs come from the plan: **S2** (Incremental prompt diet, 6 tasks), **S3** (SKILL.md update, 1 task). Phase close follows S3.

## Repo state at handoff

- Branch: `main`. Local-only; **do not push**. Ahead of `origin/main` by ~75 commits at handoff.
- Working tree: clean except `review-stderr.log` (gitignored).
- Test baseline: `python3 -m pytest skills/external-review/tests/ -q` → **128 passed, 1 warning** (pre-existing `datetime.utcnow()` deprecation in `synthesize_legacy_manifest`).
- Latest S1 commit: `0c9e5da` ("external-reviewer: S1 post-slice close-out (r5 ready)").

## What landed in S1 (so you know what S2 builds on)

S1 closed in 5 review rounds. Key behavioral changes already in `skills/external-review/scripts/external-reviewer.py`:

- `PROMPT_SENTINEL_START`/`END` constants + `strip_prompt_echo()` helper.
- `make_prompt()` wraps the entire prompt body in sentinels.
- `write_review_artifact()` strips sentinels from both streams *before* size capping; success path caps stderr tail to 2 KB, failed path drops stdout entirely and caps stderr to 4 KB.
- `run_one_reviewer()` forces `verdict=None, verdict_valid=False, findings_count=0, blocking_findings_count=0` when `result.returncode != 0`.
- `write_merged_findings()` excludes failed reviewers; returns `None` if all failed.
- `compute_merged_verdict()` returns `None` when primary failed; otherwise aggregates only over `returncode == 0` reviewers per spec §S1.7.
- `round_entry["reviewers"]` + emitted JSON `reviewers[]` both carry per-reviewer `status` and `returncode`. Top-level round entry also carries `status` + `returncode` (from primary).
- `migrate_manifest_inplace()` soft-migrates legacy chain.json entries (missing `status`/`returncode`) to `status: "unknown"` / `returncode: None`. Wired into both the read path and the synthesize-from-disk path.
- `build_incremental_preamble()` walks backward past `status ∈ {failed, unknown}` rounds to find the last trusted round. Adds a "Note: rounds X..Y were process failures or pre-S1 entries; skipped." annotation. Returns a preamble with **stable** `## Review chain summary`, `## Prior-round findings`, `## Resolution report for prior round`, `## Changes since prior round` subheadings. **These headings are the regex anchors Task 2.4's budget trimmer will use — do not rename them.**
- Resolution gate (`post-slice` / `post-phase`) bypasses when `prior.status == "failed"`; still fires on `"unknown"` (legacy) and on real `"revise"` verdicts.
- `--prompt-transport` default is mode-aware: `arg` on broad / round 1, `stdin` on incremental rounds (round 2+). This was bundled into commit `670bcff` by user instruction; it predates Task 2's diet but does not replace it.
- Final-ready sweep rename now rewrites the response body's `Request:` line so request/response references stay consistent post-rename (sweep fix from r3).

## Tests added in S1 (33 new test cases; in case S2 trips one)

- `test_sentinel_stripper.py` (7), `test_response_artifact.py` (4), `test_failed_round_truth.py` (1, extended with merged-verdict + size assertions), `test_merged_findings_skips_failed.py` (4), `test_returncode_status_persisted.py` (4), `test_chain_soft_migration.py` (2), `test_preamble_skips_failed.py` (3), `test_resolution_gate_bypass.py` (2), `test_failed_r2_bounded_r3.py` (2 — includes the previously-xfail r3-size test, now enforced), `test_final_ready_rename_response_body.py` (1), `test_failed_findings_zeroed.py` (1).

If S2 changes break any of these, the implementer must reconcile — they're load-bearing for S1's correctness contract.

## Tasks in Slice 2 (from plan)

- **Task 2.1** — Drop context previews on incremental rounds (plan line 1830).
- **Task 2.2** — Trim target preview on incremental (plan line 1922).
- **Task 2.3** — Cap prior-text reads in `build_incremental_preamble` (plan line 2006). Will consume the stable `## ` headings S1 added.
- **Task 2.4** — Add `--incremental-budget-chars` with priority-order truncation (plan line 2151).
- **Task 2.5** — Tighten diff caps (plan line 2458).
- **Task 2.6** — Slice 2 acceptance check (plan line 2631).

**Then Slice 3:** Task 3.1 — Update `skills/external-review/SKILL.md` (plan line 2686).

**Then post-phase:** `superstar:external-review --kind post-phase --review-depth thorough` on the plan, with the spec as context.

## Items deferred from S1 review for S2 to absorb

The S1 r1 fixer deferred a handful of S2-overlapping findings — the plan tasks already cover them, but be aware so subagents don't think they're "new" issues:

- Context-preview drop (→ Task 2.1)
- Target-preview trim (→ Task 2.2)
- Prior-text caps (→ Task 2.3)
- Budget knob (→ Task 2.4)
- Diff cap tightening (→ Task 2.5)

If a subagent finds an existing test that already feels "diet-shaped" (e.g., asserts smaller previews), that's a leftover artifact of S1's wider work, not a problem.

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper than dispatching. Tiebreak: delegate.
- **Do not read large files or run investigations yourself.** Delegate to subagents and accept short summaries.
- **At the end of S2**, invoke `superstar:external-review --kind post-slice --review-depth thorough` (S2 changes touch hot paths). For S3 (docs-only), `standard` depth is fine.
- **Reviewer-driven fixes go to fix subagents**, never inline. The fix subagent must write `docs/reviewer/<chain>/r{N}-resolution.md` before signaling completion. Coordinator commits round artifacts after each verdict (S1 showed the reviewer flags untracked chain files; commit them as part of the round close-out, not as a separate ticket).
- **At phase close** (after S3 verdict ∈ {ready, ready with small edits}): invoke `superstar:external-review --kind post-phase --review-depth thorough` and then `superstar:finishing-a-development-branch`.
- **Tick plan checkboxes** as slices close (S1's are already ticked).

## Pre-flight reads (for subagents, not for you)

- Spec §S2 (the diet contract), §6 (acceptance gate).
- Plan "Files at a glance," "Conventions used throughout the plan," and Slice 2 tasks one-by-one. Slice 2 tasks are TDD-first like S1's were.

## First action

Invoke `superstar:subagent-driven-development` and begin Slice 2 with **Task 2.1**. Read only the Task 2.1 block from the plan (around line 1830) before dispatching — do not read the whole 2818-line plan into your context. Delegate task-text extraction to a subagent if needed.

## One quirk to know

Chain folder names normalize `.` → `-` in work IDs. `--work-id S2` produces `external-reviewer-context-optimisation-plan-S2-post-slice/`. The plan's example invocation at the end of S2 reads `--work-id S2` directly — that's correct.
