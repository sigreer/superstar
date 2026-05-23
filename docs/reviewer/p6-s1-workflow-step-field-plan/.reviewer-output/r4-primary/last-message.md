1. Findings

F5. RESOLVED — `infer-step --all` now builds `qid = f"{ph.id}.{s.id}"` and uses it for output, stored lookup, and inference at `docs/plans/2026-05-23-P6.S1-workflow-step-field.md:1224-1227`. The CLI regression test also asserts `P6.S1` appears and freestanding `S1` does not at lines 1147-1149. The invalid serialization fixture is also fixed to `Slice(id="S1")` at lines 260-262.

F7. RESOLVED — The plan no longer introduces the broken `_run()` helper. It explicitly says to reuse the existing `run_cli` helper at lines 1114-1115, and all new integration tests invoke `run_cli(...)` from lines 1121 onward. That matches the existing repo pattern in `tools/tasktool/tests/test_cli_integration.py`.

F1. RESOLVED — Still no schema migration subsystem is introduced.

F2. RESOLVED — Schema work remains scoped to `build_schema()` and inline schema properties.

F3. RESOLVED — `cmd_infer_step` is specified to use `_load(repo_root)`, and stored `None` is not treated as drift.

F4. RESOLVED — The architecture summary still says six skill markdown files and includes `executing-plans`.

F6. RESOLVED — `UsageError` is specified as a `CommandError` subclass, with CLI tests for controlled no-op and invalid workflow-step errors.

2. Open questions / assumptions

- I assume the minor wording conflict in Step 12.3 is accidental: line 1754 says “each command exits 0” while also allowing `infer-step --all --diff` to exit 1. The latter is correct for drift mode.

3. Suggested document edits

- Optional small edit: change Step 12.3 expected text to “all commands exit 0 except `infer-step --all --diff`, which may exit 1 when drift is present.”

4. Verification gaps / commands that should be run

- The plan now includes the targeted checks needed for the prior regressions:
  - `cd tools/tasktool && python -m pytest tests/test_cli_integration.py -k infer_step -v`
  - `cd tools/tasktool && python -m pytest tests/test_commands.py -k 'infer_step or list_filter_workflow_step' -v`
  - full `cd tools/tasktool && python -m pytest`
  - `python -m pytest skills/external-review/tests/`

Overall verdict: ready with small edits
