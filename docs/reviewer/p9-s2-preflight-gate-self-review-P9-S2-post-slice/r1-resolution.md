# Resolution for r1

## F1
Status: fixed
Evidence:
- Tracker lifecycle applied by coordinator: `tasktool start P9.S2` + `tasktool ratify P9.S2` run; commit `f03c777` ("P9.S2: mark slice in_progress + ratified (lifecycle)") landed on `main` and merged into the worktree via `0d8b662`.
- `tasktool brief P9.S2` now reports `status: in_progress`, `started: 2026-06-09`, `planning_status: ratified`, `workflow_step: implement`.

## F2
Status: fixed
Evidence:
- All completed task checkboxes in `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md` marked `[x]`: Task 0 (Steps 1–2), Task 1 (Steps 1–8), Task 2 (Steps 1–8), Task 3 (Steps 1–7), Task 4 (Steps 1–5), Task 5 (Steps 1–6). Task 5 Step 7 (merge-back/close/release hygiene) remains `[ ]` — intentionally deferred until this review reaches `ready`.
- New `## Post-slice evidence (round 1)` section added at the end of the plan (after the Spec-coverage map table) recording: task commits (SHAs 833f049, 838f7ae, ce5f929, d1d478b, f03c777, 0d8b662), test result (`337 passed, 1 warning in 24.09s`), CLI smoke, behavioural smoke, real-corpus validation (0 failures), tracker state, residual DeprecationWarning, and pending Step 7 note.
- Also corrected two dangling backtick path references per the reviewer's suggested edits: `tests/test_resolution_gate.py` at lines 32 and 745 corrected to `skills/external-review/tests/test_resolution_gate.py`.
- Files: `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md`

## S1.F1
Status: fixed
Notes: Duplicate of F1 (tracker lifecycle); resolved as above.

## S1.F2
Status: fixed
Notes: Duplicate of F2 (plan-as-evidence); resolved as above.

## S1.F3
Status: fixed
Evidence:
- Files: `skills/external-review/scripts/external-reviewer.py` (lines 3016–3027)
- Round-1 gate restructured: failure path (`not preflight.ok`) now prints the ERROR header + `_print_preflight_text(preflight, ...)` and returns 4 immediately; the early warning loop runs only on the `ok` (proceed) path. Warnings are no longer printed twice on a mixed failure+warning document.
- Regression test `test_warnings_not_printed_twice_on_failure` added to `skills/external-review/tests/test_auto_preflight.py` — asserts `r.stderr.count("preflight warning") <= 1` on a failing+warning document.
- Verification: `python -m pytest skills/external-review/tests -q` → `337 passed, 1 warning in 24.09s`
