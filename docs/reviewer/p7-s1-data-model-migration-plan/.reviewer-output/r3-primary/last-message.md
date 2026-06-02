Findings

F1 Severity: blocking. RESOLVED. The plan continues to treat `reservations_ledger` as merge-aware rather than scalar, with dedicated ledger tests and a union/never-delete implementation path keyed on `resource:value:scope:owner_id` (`docs/plans/2026-06-02-P7-S1-data-model-migration.md:738`, `docs/plans/2026-06-02-P7-S1-data-model-migration.md:833`, `docs/plans/2026-06-02-P7-S1-data-model-migration.md:855`, `docs/plans/2026-06-02-P7-S1-data-model-migration.md:888`, `docs/plans/2026-06-02-P7-S1-data-model-migration.md:905`). This matches the spec requirement that archived project-scoped reservations survive phase archival and dedupe by owner-aware identity (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:112`, `docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:170`).

F2 Severity: important. RESOLVED. The plan includes `tools/tasktool/__init__.py` in scope and adds Task 1b to export `Reservation` and `LedgerReservation` and extend `test_all_exports_present` (`docs/plans/2026-06-02-P7-S1-data-model-migration.md:26`, `docs/plans/2026-06-02-P7-S1-data-model-migration.md:210`, `docs/plans/2026-06-02-P7-S1-data-model-migration.md:216`, `docs/plans/2026-06-02-P7-S1-data-model-migration.md:238`).

F3 Severity: important. RESOLVED. The schema gate still imports `jsonschema` directly in the new P7 acceptance test and explicitly forbids a conditional skip, so missing `jsonschema` is a hard failure for this slice (`docs/plans/2026-06-02-P7-S1-data-model-migration.md:609`, `docs/plans/2026-06-02-P7-S1-data-model-migration.md:616`, `docs/plans/2026-06-02-P7-S1-data-model-migration.md:658`, `docs/plans/2026-06-02-P7-S1-data-model-migration.md:666`).

F4 Severity: blocking. RESOLVED. The plan now explicitly updates both existing stale schema-version tests: `tools/tasktool/tests/test_model.py::test_schema_version_is_2` is renamed/updated in Task 1 (`docs/plans/2026-06-02-P7-S1-data-model-migration.md:117`, baseline test at `tools/tasktool/tests/test_model.py:107`), and `tools/tasktool/tests/test_schema_gen.py::test_schema_version_bumped_to_2` is renamed/updated in Task 4 (`docs/plans/2026-06-02-P7-S1-data-model-migration.md:642`, baseline test at `tools/tasktool/tests/test_schema_gen.py:108`). The final grep gate also catches any remaining current-version `== 2` assertions while allowing raw v2 fixtures (`docs/plans/2026-06-02-P7-S1-data-model-migration.md:1137`, `docs/plans/2026-06-02-P7-S1-data-model-migration.md:1142`).

Open questions / assumptions

I assume the slightly stale wording at `docs/plans/2026-06-02-P7-S1-data-model-migration.md:41` (“all four touched test files” while listing five) and `docs/plans/2026-06-02-P7-S1-data-model-migration.md:597` (`test_v1_validates_against_v2_schema_after_save`, later renamed) will be cleaned opportunistically, but neither creates implementation ambiguity.

Suggested document edits

Update the two stale prose references noted above: “all five touched test files” at line 41, and the v1 compat test name at line 597 to the v3 name introduced in Task 6.

Verification gaps / commands

Run the plan’s gates as written after implementation:

`python -m pytest tools/tasktool/tests/test_migrate.py -q`

`python -m pytest tools/tasktool/tests/test_model.py tools/tasktool/tests/test_schema_gen.py -q`

`rg -n "schema_version.*2|SCHEMA_VERSION == 2|const.*2" tools/tasktool/tests`

`python -m pytest tools/tasktool/tests -q`

`python -m pytest -q`

Overall verdict: ready with small edits

