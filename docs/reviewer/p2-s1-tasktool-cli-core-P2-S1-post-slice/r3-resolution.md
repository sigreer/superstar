# R3 Resolution — P2.S1 post-slice sweep

All three sweep findings addressed. TDD applied: failing test added, then fixed, then green confirmed before moving to next finding.

## S1.F1

**Status: fixed**

`_PHASE_PAT`, `_SLICE_PAT`, `_TASK_PAT`, and `_CROSS_PAT` in `tools/tasktool/allocate.py` all now compiled with `re.IGNORECASE`. Regression test `test_orphan_lowercase_in_plans` added: an orphan at `docs/plans/2026-05-17-p7-orphan-spec.md` (lowercase `p7`) now causes `next_phase_id` to return `P8`.

## S1.F2

**Status: fixed**

`tools/tasktool/schema_gen.py` now defines two enums: `slice_status_enum` (full, includes `blocked`) and `non_blocked_status_enum` (`ready`, `in_progress`, `done`). Task, phase, and cross schemas use `non_blocked_status_enum`; slice schema uses `slice_status_enum`. Four schema tests added to `test_validate.py` (`SchemaEnumTests`): task/phase/cross must not contain `blocked`, slice must contain `blocked`.

## S1.F3

**Status: fixed**

`tools/tasktool/__init__.py` now re-exports `Project`, `Phase`, `Slice`, `Task`, `CrossCutting`, `BlockedOn`, `Status`, `ArchivedPhase`, `SCHEMA_VERSION` from `tasktool.model`, and `load_project`, `save_project`, `dumps_canonical`, `loads_project` from `tasktool.serialize`. `__all__` lists all exports. Two tests added to `test_model.py` (`PublicAPITests`): `from tasktool import load_project, Project` succeeds and all 13 promised names are present.

## Summary

Full suite: **138 tests, all green** (was 131 before r3).
