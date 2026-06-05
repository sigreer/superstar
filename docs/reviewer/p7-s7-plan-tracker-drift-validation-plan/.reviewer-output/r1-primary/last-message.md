1. Findings

F1 Severity: blocking  
`P7.S7`’s own tracker row does not actually declare the `validate` integration surface, but the plan says the row can be ratified as-is. The plan states “Integration surfaces for S7 itself: `validate`” and “No dependency-graph change is required. The plan ratifies the row as-is” at `docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md:19-23`, then only ratifies in Task 5 at `:548-564`. The tracker row only has a prose note saying “Surfaces: validate”; it has no `integration_surfaces` field in the actual slice data at `docs/tasklist.json:439-443`. For a slice whose purpose is tracker/plan drift validation, this leaves immediate drift in the artifact set and means `surface check`/scheduling tooling cannot reason over the declared write surface. Add a task before ratification to run `tasktool surface add P7.S7 validate` and commit that tracker mutation.

F2 Severity: blocking  
The planned `cmd_validate` integration tests contradict Check 1’s spec and implementation. Check 1 only warns when `parallel_group is not None` and `integration_surfaces` is empty, as shown in the plan’s own implementation snippet at `docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md:178-185`. But both command tests construct `parallel_group="core"` with `integration_surfaces=["commands"]` and still assert `"parallel_group"` is present at `:402-420` and `:422-440`. A correct implementation will not emit that warning, so these tests either fail or pressure the implementer to violate the spec. Use separate fixture slices, or use a single slice with `parallel_group="core"` plus no surfaces and a missing reservation token to exercise Check 1 and Check 2 together.

F3 Severity: important  
The manual smoke expectation is not grounded in current tracker state. The plan says the real tracker has no `parallel_group` slices and no new warnings should appear at `docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md:507-510`, but `docs/tasklist.json` currently has terminal P7 slices with `parallel_group` set at `docs/tasklist.json:287-291` and `:344-349`, and current `tasktool validate --format json` already reports a warning for the missing S7 handoff ref listed at `docs/tasklist.json:444-448`. The acceptance gate should either create/register that handoff before the smoke check or explicitly baseline the existing path warning and require “no additional surface-drift warnings.”

2. Open questions / assumptions

Assumption: `validate` is intended to be the tracker-declared surface name for edits to `tools/tasktool/validate.py`, `commands.py`, and related validation tests, matching the plan prose.

3. Suggested document edits

Add a tracker-prep task before implementation or before ratification:

`tasktool surface add P7.S7 validate`, then commit `docs/tasklist.json`.

Rewrite the two Task 3 integration tests so the Check 1 fixture has no `integration_surfaces`. For combined coverage, either add a second slice for Check 2 or declare a reservation and assert the reservation drift warning.

Update the manual smoke section to acknowledge the existing missing-handoff warning or add the missing handoff artifact before claiming the live tracker warning baseline.

4. Verification gaps / commands

Run these after edits:

`tasktool show P7.S7` and confirm `integration_surfaces` includes `validate`.

`tasktool validate --format json` and record whether only the known pre-existing path warning remains, or fix the handoff warning first.

`cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q`

Overall verdict: revise