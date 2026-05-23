1. Findings

F5. Severity: blocking — UNRESOLVED. The main `_find_row` lookup now correctly delegates to `_find_item`, so single-ID lookup for `P6.S1` is fixed. However, the `--all` implementation still uses short slice IDs when building rows: `rows.append(("slice", s.id, ...))` at `docs/plans/2026-05-23-P6.S1-workflow-step-field.md:1226-1227`. That has two concrete problems: it prints `S1`, while the plan’s own CLI test expects `P6.S1` at `docs/plans/2026-05-23-P6.S1-workflow-step-field.md:1148-1153`, and it calls `_stored_step_for_id(project, s.id)` / `infer_step_for_id(project, s.id)`, which will become ambiguous as soon as multiple phases contain `S1`. Build a qualified ID in the phase loop, e.g. `qid = f"{ph.id}.{s.id}"`, and use that for stored lookup, inference, and output. Also fix the remaining invalid serialization fixture at `docs/plans/2026-05-23-P6.S1-workflow-step-field.md:260-262`, which still creates `Slice(id="P6.S1")` despite the plan now documenting short persisted IDs.

F7. Severity: blocking — The new CLI integration helper is not executable under the plan’s own test command. The plan appends `_run()` that invokes `["tools/tasktool/tasktool", ...]` with `cwd=None` for the temp project fixture at `docs/plans/2026-05-23-P6.S1-workflow-step-field.md:1121-1126`, but Step 7.5 runs from `cd tools/tasktool` at `docs/plans/2026-05-23-P6.S1-workflow-step-field.md:1268-1270`. From that cwd, `tools/tasktool/tasktool` resolves to `tools/tasktool/tools/tasktool/tasktool` and will fail before exercising `infer-step`. Reuse the existing `run_cli()` / `WRAPPER` pattern already in `tools/tasktool/tests/test_cli_integration.py` instead of introducing a second subprocess helper with a relative executable path.

F1. RESOLVED — The plan still avoids `tools/tasktool/migrate.py` and relies on v1 load defaults plus `to_dict` promotion to schema version 2.

F2. RESOLVED — Schema tests target `build_schema()` and the current inline schema shape.

F3. RESOLVED — `cmd_infer_step` uses `_load(repo_root)`, and stored `None` is explicitly not drift.

F4. RESOLVED — The architecture summary now says “Six skill markdown files” and includes `executing-plans`.

F6. RESOLVED — `UsageError` is planned as a `CommandError` subclass, and CLI-level validation tests were added for no-op and invalid workflow-step calls.

2. Open questions / assumptions

- I assume `infer-step --all` should display fully-qualified slice IDs, matching existing tasktool output patterns and the plan’s own tests.
- I assume keeping one invalid `Slice(id="P6.S1")` fixture is accidental, not an intended exception to the persisted short-ID rule.

3. Suggested document edits

- In Task 7, change the slice row loop to compute `qid = f"{ph.id}.{s.id}"` and use `qid` everywhere in that row.
- Change `test_workflow_step_default_none_omitted_from_json()` to use `Slice(id="S1", ...)`.
- Replace the new `_run()` helper in `test_cli_integration.py` with the existing `run_cli()` helper, or call the absolute `WRAPPER`.

4. Verification gaps / commands that should be run

- `cd tools/tasktool && python -m pytest tests/test_cli_integration.py -k infer_step -v`
- `cd tools/tasktool && python -m pytest tests/test_commands.py -k 'infer_step or list_filter_workflow_step' -v`
- Add/keep a test asserting `infer-step --all --diff` output uses `P6.S1`, not `S1`.

Overall verdict: revise