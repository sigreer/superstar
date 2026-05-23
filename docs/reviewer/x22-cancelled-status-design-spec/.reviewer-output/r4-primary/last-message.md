1. Findings

F1. RESOLVED. Severity: blocking. The spec still requires both JSON-schema and semantic validation to reject `cancelled` tasks, including `_check_task()` and `validate_project()` tests (`docs/specs/2026-05-23-X22-cancelled-status-design.md:73-79`, `:312-313`).

F2. RESOLVED. Severity: important. The schedule contract is concrete and grounded in the current row shape, preserving `depends_on`, narrowing `waiting_on`, and adding `cancelled_deps` in JSON and text output (`docs/specs/2026-05-23-X22-cancelled-status-design.md:176-212`, `:303-308`).

F3. RESOLVED. Severity: important. The spec keeps global `phase-status` unchanged and scopes cancelled-dependency surfacing to phase-scoped `schedule` (`docs/specs/2026-05-23-X22-cancelled-status-design.md:210-211`).

F4. RESOLVED. Severity: important. Active vs archived `show`/`brief` behavior is explicit, including preserving the archived-X “not found in active tasklist” behavior (`docs/specs/2026-05-23-X22-cancelled-status-design.md:222-223`, `:321-322`).

F5. RESOLVED. Severity: minor. Notification behavior is grounded in the existing generic `tasktool-status` notifier and no longer invents a status-specific audio cue (`docs/specs/2026-05-23-X22-cancelled-status-design.md:231-239`).

F6. RESOLVED. Severity: important. The archive-phase notification gap is fixed: cancelled phase archival must notify with the actual phase status and has a regression test forbidding a misleading `done` event (`docs/specs/2026-05-23-X22-cancelled-status-design.md:241-244`, `:327-328`).

F7. RESOLVED. Severity: blocking. The prior task-leak blocker is now explicitly covered. The spec requires `cmd_list` to suppress tasks whose parent slice is terminal, preserves the task rows unchanged for `show`, and adds focused tests for slice cancellation and phase cascade (`docs/specs/2026-05-23-X22-cancelled-status-design.md:218-221`, `:286-288`). This is grounded in the current independent task iteration path (`tools/tasktool/commands.py:1571-1604`).

2. Open questions / assumptions

- `note --replace` remains unspecified. The spec allows `note --append` on cancelled rows, but the current CLI also has `note --replace` (`tools/tasktool/cli.py:166-170`; implementation in `tools/tasktool/commands.py:1096-1109`). Because the cancellation reason is stored only in `notes`, the implementation plan should explicitly reject `note --replace` on cancelled rows or deliberately allow it with a test documenting that the audit line can be overwritten.

3. Suggested document edits

- Change “with three explicit enums” to “with four explicit enums” at `docs/specs/2026-05-23-X22-cancelled-status-design.md:62`.
- Add one bullet to the lifecycle-adjacent command table for `note --replace`, with the intended behavior and a test expectation.

4. Verification gaps / commands that should be run

- I did not run tests; this was a pre-implementation spec review.
- Keep the proposed focused verification set:
  - `python -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_cli_integration.py -q`
  - `python -m pytest tools/tasktool/tests/test_importer.py tools/tasktool/tests/test_render.py tools/tasktool/tests/test_brief.py tools/tasktool/tests/test_notify.py -q`
  - `tools/tasktool/tasktool validate --strict-format`

Overall verdict: ready with small edits

