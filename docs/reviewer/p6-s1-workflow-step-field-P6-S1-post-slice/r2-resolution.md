# Resolution for r2

## F1
Status: fixed
Evidence:
- Commit: <pending>
- Files: `docs/specs/2026-05-23-P6-programmatic-workflow-enhancements-design.md` §3.3 amended (R3 added); `docs/plans/2026-05-23-P6.S1-workflow-step-field.md` Step 5.3 snippet amended; `tools/tasktool/tests/test_commands.py` adds two regression tests.
- Verification: `cd tools/tasktool && python -m pytest` — full suite green (666 passed).

Notes:
Resolved by amending the spec to match the shipped behavior (option recommended by reviewer; selected by user). `slice.plan_path` is the authoritative signal for moving past spec at the slice level; phase-level inference still consults `phase.spec_path`. Plan tests were already correct; spec §3.3 was over-precise. Two regression tests pin the contract for "no phase.spec_path + ratified slice plan ⇒ implement" and the proposed/plan variant.
