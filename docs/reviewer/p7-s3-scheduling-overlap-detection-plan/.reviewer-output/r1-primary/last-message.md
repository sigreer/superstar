1. Findings

F1. Severity: important. `cmd_schedule` enrichment is broader than the spec’s reporter contract. The spec limits `cmd_ready_slices` / `cmd_schedule` warnings to “each ready/in-progress slice” while comparing against other non-terminal slices (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:186-190`). The plan’s `_surface_overlap_map` makes every non-terminal slice a subject (`docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md:224-250`), and `cmd_schedule` then attaches those relations to every row, including blocked or dependency-waiting rows (`docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md:282-302`). Add a test for a blocked or waiting slice that shares a surface and define the intended behavior. If the spec remains authoritative, only ready/in-progress schedule rows should receive reporter warnings.

F2. Severity: important. The manual smoke command can mask ratify failures because the semicolon breaks the `&&` chain inside the subshell (`docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md:878-892`). If the first `ratify` fails, `echo "exit=$?"` still runs, then the second ratify can run, and the subshell’s final status may not represent the failure being smoked. Use explicit captures, e.g. run each ratify on its own line, store `$?`, print it, and fail if non-zero.

F3. Severity: minor. The invariant checklist says the “single slice holding the same `resource:value` at phase and project scope is not contention” case is covered by tests (`docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md:926`), but the listed command-level test only covers two slices forced onto the same value (`docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md:475-489`). Add a direct regression where one slice has both scopes and `reservation_contention` stays empty.

F4. Severity: minor. The suggested failing-test command for Task 4 is malformed/confusing: it repeats the same test file and `-k` selector in one pytest invocation (`docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md:725-730`). Replace it with a single executable command such as `python -m pytest tools/tasktool/tests/test_commands.py -k "ratify_parallel_group or ratify_no_warning" -q`, or just keep the simpler `-k ratify`.

2. Open questions / assumptions

Assumption: `surface check` is intentionally all non-terminal pairs, because the spec says “every unguarded surface overlap” for the dedicated audit (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:192-199`). F1 is only about the reporter surfaces `ready-slices` and `schedule`.

3. Suggested document edits

Clarify the subject predicate for reporter warnings before implementation: either rename `_surface_overlap_map` as an all-active helper and filter at the reporter row, or parameterize it so `cmd_schedule` only emits `surface_overlap` / `coordinated` for ready/in-progress subjects.

Patch the manual smoke shell block so every command remains in the guarded flow and ratify exit codes are asserted, not just printed.

Add the missing self-scope reservation-contention test and fix the Task 4 pytest command.

4. Verification gaps / commands that should be run

The planned focused and full pytest gates are appropriate after the small fixes:
`python -m pytest tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_cli_integration.py -q`
`python -m pytest tools/tasktool/tests -q`
`python -m pytest -q`

Also run the corrected manual smoke command after fixing the shell grouping.

Overall verdict: ready with small edits

