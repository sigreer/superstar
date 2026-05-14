# Resolution for r2

## F1
Status: fixed (carryover; already resolved in r1)

## F2
Status: fixed
Evidence:
- Commit: 7b25d067e7e575b38a4f56c90a4a299bfd65f898
- Files: chain dir committed in same commit
Notes:
The chain folder is now tracked. From r3 onward the sweep will not flag it as untracked.

## S1.F1
Status: fixed (duplicate of F2)
Notes:
Same as F2 — chain folder is now committed.

## S1.F2
Status: fixed
Evidence:
- Commit: 7b25d067e7e575b38a4f56c90a4a299bfd65f898
- Files: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:2696`
- Verification: grep "to fit the cap" and "global \`--incremental-budget-chars\` cap" in the plan Slice 3 block — should return no matches.

Notes:
Slice 3's planned SKILL.md text now uses the softened "target cap" wording with the diagnostic-note caveat, matching the argparse help and apply_budget docstring landed in r1.

## S1.F3
Status: fixed (duplicate of F1)
