# Resolution for r1

## F1
Status: fixed
Evidence:
- Commit: ee4185de9ce43e6a874811d064123b89c2f0b8af
- Files: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:2665`
- Verification: grepped the new line; manual recheck ran 84,854 bytes (matches reviewer's measurement)

Notes:
Plan Task 2.6 Step 2 now records the observed r2 request size.

## F2
Status: waived
Evidence:
- N/A — chain folder will be committed by the coordinator at round close-out

Notes:
Per coordinator handoff convention, the post-slice review chain folder is committed as part of the round close-out (S1 followed the same pattern). Not a separate ticket.

## S1.F1
Status: waived (duplicate of F2)
Notes:
Same as F2 — chain artifacts will be committed by the coordinator. Marking duplicate.

## S1.F2
Status: fixed
Evidence:
- Commit: ee4185de9ce43e6a874811d064123b89c2f0b8af
- Files: `skills/external-review/scripts/external-reviewer.py:973` (argparse help), `skills/external-review/scripts/external-reviewer.py:215` (apply_budget docstring)
- Verification: `python3 -m pytest skills/external-review/tests/ -q` → 141 passed (no behaviour change)

Notes:
Documentation tightened to acknowledge the small diagnostic-note overhead. The trim loop continues to fit content to `budget_chars`; the appended `<!-- budget-applied: ... -->` note is ~150 bytes. No code restructure; the test already permits ≤budget+500.

## S1.F3
Status: fixed (duplicate of F1)
Notes:
Same as F1 — Plan Task 2.6 Step 2 now records 84,854 bytes evidence.
