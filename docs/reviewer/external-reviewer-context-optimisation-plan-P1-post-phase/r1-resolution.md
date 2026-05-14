# Resolution for r1

## F1
Status: fixed
Evidence:
- Commit: (this commit)
- Files: `skills/external-review/scripts/external-reviewer.py` (compute_diff_section sub-headings demoted to `###`; `_find_section_end` hardened to scan only known anchors), `skills/external-review/tests/test_incremental_budget.py` (new test: `test_apply_budget_trims_diff_with_nested_subheadings`).
- Verification: `python3 -m pytest skills/external-review/tests/ -q` → 142 passed. New regression test forces a `## Changes since prior round` block with nested `## git diff` heading + 150 KB body and confirms `apply_budget` trims it under an 80 KB budget.

Notes:
Two-part fix: (a) compute_diff_section emits `###` sub-headings so it doesn't poison its own section's end-detection, and (b) _find_section_end now uses only the four known budget anchors as section boundaries, not any `## ` heading — robust against future nested-heading insertions.

## F2
Status: fixed
Evidence:
- Commit: (this commit)
- Files: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md` (Phase close: observed-evidence subsection added; Step 3 invocation now includes `--work-id P1`).

Notes:
Phase-close checkboxes will be ticked in the coordinator's final close-out commit after the post-phase verdict returns `ready`.

## F3
Status: fixed (same evidence as F2 — observed phase-close measurements recorded inline).

## F4
Status: fixed
Evidence:
- Commit: (this commit)
- Files: `skills/external-review/SKILL.md` (sweep-aggregation paragraph rewritten to align with the new truth table).
