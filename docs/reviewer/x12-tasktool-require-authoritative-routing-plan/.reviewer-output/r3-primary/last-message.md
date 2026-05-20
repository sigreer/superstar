1. Findings

F6 (Severity: important) UNRESOLVED. The read-only acceptance half is now covered: the test includes `render`, `validate`, `brief`, `schema`, `show`, `phase-status`, `ready-slices`, `list`, and `next-id`, and asserts exit 0 (`docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:313-346`). However, the “full persisted surface” acceptance test still does not cover every dataclass field as required by the spec. The spec explicitly calls for every field on persisted rows, including `title` and `created` (`docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md:82-90`, `:152-157`), and the current model persists those fields on `Task`, `Slice`, `Phase`, and `CrossCutting` (`tools/tasktool/model.py:24-84`). The new per-field test skips `id`, `title`, and `created` outright (`docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:780-809`). Skipping `id` is defensible because row identity is keyed by it, but skipping `title` and `created` leaves real mutable persisted fields untested.

F7 (Severity: important) RESOLVED. `_load_project_at` now delegates directly to `load_project(tasklist_path)` (`docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1666-1671`), matching the existing serializer API (`tools/tasktool/serialize.py:100-101`).

F8 (Severity: important) RESOLVED. The notification helper now descends into `slice.tasks` and emits task-qualified IDs (`docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1686-1716`), and the CLI test now checks a task status transition emits a notify event for `P1.S1.T1` (`docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1480-1511`).

F1 (Severity: blocking) RESOLVED. No regression found in the dry-run ordering from the prior resolution.

F2 (Severity: blocking) RESOLVED. No regression found in authority branch resolution.

F3 (Severity: blocking) RESOLVED. No regression found in enum-preserving notify calls.

F4 (Severity: important) RESOLVED. No regression found in omitted `mutation_mode` handling.

F5 (Severity: important) RESOLVED. The plan now explicitly instructs adding `same_repository` to the existing `tasktool.worktree` import block (`docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1524-1540`).

2. Open questions / assumptions

Assumption: `id` may remain excluded from the per-field migration acceptance test because it is the row identity key and changing it is represented as local-only plus authoritative-only rows, not a field update. That exception should be stated explicitly in the plan if retained.

3. Suggested document edits

In `_value_pair_for_field`, stop skipping `title` and `created`. Keep only `id` and `schema_version` as explicit non-field-migration exceptions, then add sample values for:

```python
if field.name == "title":
    return ("authority title", "local title")
if field.name == "created":
    return ("2026-05-19", "2026-05-20")
```

Update the comment from “Identity / immutable fields” to say only `id` is identity-keyed, and explain any intentional exception.

Also update the stale “Expected: all 9 tests pass” text after adding the new parametrized test (`docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1173-1179`).

4. Verification gaps / commands

After the plan edit, the implementation worker should still run:

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_authority_config.py tools/tasktool/tests/test_unconfigured_mutation.py tools/tasktool/tests/test_init_local.py tools/tasktool/tests/test_migrate.py tools/tasktool/tests/test_migrate_cli.py -v
PYTHONPATH=tools pytest tools/tasktool/tests/ -v
tools/tasktool/tasktool validate
```

Overall verdict: revise
