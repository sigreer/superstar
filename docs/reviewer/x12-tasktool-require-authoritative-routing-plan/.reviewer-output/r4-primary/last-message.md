1. Findings

F9 (Severity: minor) NEW. The updated expected-test-count text is still inaccurate. The plan says the parametrized full-field migration test “expands to ~30 test cases across the six row dataclasses” (`docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1187`), but the test is only parametrized by `row_type` (`:820-824`) and loops over fields inside each case (`:830-890`). Pytest will report six parametrized cases for this test, not one case per field. This is documentation-only, but it can mislead implementation verification.

F6 (Severity: important) RESOLVED. The prior acceptance gap is fixed. `_value_pair_for_field` now only excludes `id` and `schema_version`, explicitly explains why, and includes sample divergent values for both `title` and `created` (`docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:780-797`). That satisfies the spec’s persisted-field requirement for `title` and `created` (`docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md:82-90`, `:152-157`) against the current model fields (`tools/tasktool/model.py:24-84`).

F7 (Severity: important) RESOLVED. No regression found; `_load_project_at` delegates directly to `load_project(tasklist_path)` (`docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1674-1679`).

F8 (Severity: important) RESOLVED. No regression found; the plan still walks nested tasks for notifications and includes a task-qualified notify test for `P1.S1.T1` (`docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1488-1519`, `:1694-1723`).

F1 (Severity: blocking) RESOLVED. No regression found in dry-run ordering.

F2 (Severity: blocking) RESOLVED. No regression found in authority branch resolution.

F3 (Severity: blocking) RESOLVED. No regression found in enum-preserving notify calls.

F4 (Severity: important) RESOLVED. No regression found in omitted `mutation_mode` handling.

F5 (Severity: important) RESOLVED. No regression found; `same_repository` is still explicitly added to the existing import block (`docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1532-1544`).

2. Open questions / assumptions

Assumption: excluding `id` from field-level migration remains intentional because row identity changes are represented as local-only and authoritative-only rows, not field updates. The plan now states that clearly.

3. Suggested document edits

Update the expected result at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1187` to avoid claiming per-field pytest expansion. Suggested wording:

`Expected: all tests pass, including the row-type-parametrized full-field migration acceptance test that loops over every supported dataclass field.`

4. Verification gaps / commands

I did not run the implementation test suite because this is a pre-implementation plan review. The plan’s implementation worker should still run:

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_authority_config.py tools/tasktool/tests/test_unconfigured_mutation.py tools/tasktool/tests/test_init_local.py tools/tasktool/tests/test_migrate.py tools/tasktool/tests/test_migrate_cli.py -v
PYTHONPATH=tools pytest tools/tasktool/tests/ -v
./tools/tasktool/tasktool validate
```

Overall verdict: ready with small edits

