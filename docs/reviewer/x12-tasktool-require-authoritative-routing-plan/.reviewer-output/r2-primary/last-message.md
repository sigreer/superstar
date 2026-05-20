1. Findings

F6 (Severity: important) UNRESOLVED. The plan still does not concretely cover all spec-listed acceptance gates. The added read-only test only parametrizes `brief`, `schema`, `list`, and `ready-slices` and merely asserts the unconfigured-routing message is absent, allowing non-zero exits for “unrelated reasons” ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):313-334). The spec requires read-only commands including `show`, `phase-status`, and `next-id` to continue to work unconfigured, not just avoid one error string ([spec](docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md):45,143-147). The plan also still lacks a concrete “full persisted surface” migration test that mutates every field on every row type; the Task 4 tests cover selected fields and a coverage meta-test, but not the per-field migration acceptance described in the spec ([spec](docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md):152-157; [plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):724-755).

F7 (Severity: important) The migration command body remains non-executable as written because `_load_project_at` is included with a `raise NotImplementedError` placeholder ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):1511-1524). The plan later tells the implementer to replace it ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):1568-1576), but this is a pre-implementation plan with concrete code blocks; it should use the existing loader directly. Current `tools/tasktool/serialize.py` already exposes `load_project(path: Path) -> Project` ([serialize.py](tools/tasktool/serialize.py):100-101), and `commands.py` already imports it ([commands.py](tools/tasktool/commands.py):12). Replace the placeholder with `return load_project(tasklist_path)` and remove the exploratory handoff text.

F8 (Severity: important) The notification helper still misses task status transitions. The spec says to notify “for each row whose status changed” ([spec](docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md):108), and tasks are persisted rows with `status` fields ([model.py](tools/tasktool/model.py):24-33). The planned `_notify_status_transitions` walks cross-cutting rows, phases, and slices, but never descends into `slice.tasks` ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):1539-1551). A migrated task from `ready` to `in_progress` would be silently applied without a notify event.

F1 (Severity: blocking) RESOLVED. `--dry-run` now renders the diff and returns before conflict policy selection ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):1454-1466), and the plan includes a dry-run-without-policy test ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):1224-1235).

F2 (Severity: blocking) RESOLVED. The command body now loads `load_config(authority_root)`, honors an existing `authoritative-checkout` branch, and only falls back to `git_current_branch` when authority config is absent ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):1432-1452).

F3 (Severity: blocking) RESOLVED. `_notify_status_transitions` now passes the status enum object through to `_notify_status` instead of converting it to a string ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):1539-1563).

F4 (Severity: important) RESOLVED. The config parser now treats a present config file with omitted `mutation_mode` as `unconfigured`, with a dedicated test ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):86-96,151-159).

F5 (Severity: important) RESOLVED. The plan now explicitly adds `same_repository` to the `tasktool.worktree` import guidance ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):1361-1379).

2. Open questions / assumptions

Assumption: notification coverage is intended to include task rows because the migrator treats tasks as persisted row entities and the spec says “each row.”

3. Suggested document edits

Replace `_load_project_at` with the concrete existing implementation:

```python
def _load_project_at(tasklist_path: Path) -> "Project":
    return load_project(tasklist_path)
```

Add `show`, `phase-status`, and `next-id` to the unconfigured read-only acceptance tests, and assert successful exit where the command has valid input.

Add a concrete full-field migration test that parametrizes over every dataclass field for `Project`, `Phase`, `Slice`, `Task`, `CrossCutting`, and `ArchivedPhase`, writes a local-vs-authoritative divergence, applies `accept-local`, and asserts the authoritative result contains the local value.

Extend `_notify_status_transitions` to walk tasks and add a CLI notify test for a task status transition, not only a slice transition.

4. Verification gaps / commands

Run after plan edits:

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_authority_config.py tools/tasktool/tests/test_unconfigured_mutation.py tools/tasktool/tests/test_init_local.py tools/tasktool/tests/test_migrate.py tools/tasktool/tests/test_migrate_cli.py -v
PYTHONPATH=tools pytest tools/tasktool/tests/ -v
tools/tasktool/tasktool validate
```

Overall verdict: revise