# Resolution for r1

Round 1 returned a primary verdict of `ready with small edits` and a sweep verdict of `revise`. This repair addresses the actionable lifecycle findings and records explicit waivers or deferrals for closeout-only items.

Repair commit: this commit (`tasktool: resolve P4 post-phase lifecycle findings`)

## F1
Status: fixed
Evidence:
- Files: `tools/tasktool/cli.py`, `tools/tasktool/commands.py`, `tools/tasktool/tests/test_commands.py`, `tools/tasktool/tests/test_lifecycle_start.py`.
- `tasktool set --status done` now accepts `--allow-ready-close` and `--reason`, applies the same ready-close audit note as `tasktool close`, and still refuses never-started slices when the override or reason is missing.
- Verification: `python -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_lifecycle_start.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` -> `110 passed`.

## F2
Status: fixed
Evidence:
- Files: `tools/tasktool/validate.py`, `tools/tasktool/tests/test_validate.py`.
- Validator now rejects `started < created` and `closed < started` after validating date shape and calendar validity.
- Verification: same targeted pytest run -> `110 passed`.

## F3
Status: fixed
Evidence:
- Files: `docs/tasklist.json`.
- Ran `tools/tasktool/tasktool start P4`; P4 now has `status: in_progress` and `started: 2026-05-19`, so the phase lifecycle marker exists before the next close/archive attempt.

## F4
Status: fixed
Evidence:
- Files: `docs/tasklist.json`.
- Added a P4.S1 note through tasktool: "P4.S1 is grandfathered under pre-P4.S2 lifecycle rules: it was closed before the started-field close guard and ready-close override audit note existed, so started remains null intentionally."

## F5
Status: fixed
Evidence:
- Files: `skills/tasklist-discipline/SKILL.md`, `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`.
- The skill now documents that `tasktool unblock <slice-id> --resume` resumes through the same lifecycle path and stamps `started` when needed.
- Verification: same targeted pytest run -> `110 passed`.

## F6
Status: waived
Evidence:
- The current behavior is intentional lifecycle tightening: `set --status in_progress` routes through `_start_item`, and `_start_item` refuses already-done rows.
- Reopening done work remains outside P4 scope; no separate reopen command or policy was specified in the P4 acceptance criteria.

## F7
Status: waived
Evidence:
- `docs/tasklist.json` is the canonical status surface for this repo; P4.S2 is already `done` there and the plan checkboxes are advisory implementation scaffolding.
- No code or validation behavior depends on plan checkbox state.

## F8
Status: deferred
Evidence:
- Archive remains gated on the next post-phase review round. The current chain round has merged verdict `revise`, so closing or archiving P4 now would require bypassing the review gate.
- This repair starts P4 and writes the resolution artifact required for the next round; archive should run after the post-phase chain returns `ready` or `ready with small edits`.

## F9
Status: waived
Evidence:
- Primary reviewer reported no issue. Existing acceptance coverage remains in the tasktool test suite, and the final verification set is rerun for this repair before commit.

## S1.F1
Status: deferred
Evidence:
- P4 has now been started via tasktool, addressing the unstamped phase lifecycle marker.
- P4 close/archive is deferred until the post-phase reviewer chain no longer has merged verdict `revise`; bypassing the gate here would weaken the workflow P4 is validating.

## S1.F2
Status: fixed
Evidence:
- Same as F4. P4.S1 now has an explicit grandfathering note in `docs/tasklist.json`.

## S1.F3
Status: fixed
Evidence:
- Same as F1. `set --status done` now has ready-close override parity with `close`.

## S1.F4
Status: waived
Evidence:
- The P4 spec explicitly did not require abrupt migration of existing projects to authoritative mode.
- Adding `.tasktool/config.json` would be a policy adoption step for the repo, not a repair for the lifecycle bugs found in this round.

## S1.F5
Status: fixed
Evidence:
- The post-phase reviewer chain directory and this `r1-resolution.md` are included in the repair commit.

## S1.F6
Status: fixed
Evidence:
- Verification commands are run and recorded before the repair commit.

## S1.F7
Status: fixed
Evidence:
- Same as F3. P4 now exercises `tasktool start P4` and carries a phase-level `started` marker.

## S1.F8
Status: waived
Evidence:
- The reviewer identified an existing field-naming ambiguity (`planning_path` holds the P4 design doc while `spec_path` is null). This is consistent with existing P3/P4 tasklist usage and is not part of the P4 lifecycle repair scope.

## Verification

Targeted red-green verification:
- Initial targeted run failed for the new tests: validator ordering was not enforced and `set` did not accept `--allow-ready-close` / `--reason`.
- After implementation: `python -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_lifecycle_start.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` -> `110 passed`.

Final verification:
- `tools/tasktool/tasktool validate --strict-format` -> `ok`
- `python -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_lifecycle_start.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_cli_integration.py tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -v` -> `132 passed in 11.21s`
- `python -m pytest tools/tasktool/tests -q` -> `253 passed in 22.22s`
