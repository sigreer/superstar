# X12 post-slice r1 resolution

## F1

Status: fixed.

Evidence:
- Commit: `X12: resolve post-slice review findings`.
- Files: `tools/tasktool/cli.py`, `tools/tasktool/tests/test_cli_integration.py`.
- Change: `config init-authority` and `config init-local` now keep an unmarked current working directory as the bootstrap project root instead of climbing to an ambient ancestor git repo.
- RED: targeted regression command failed because `.tasktool/config.json` was written to the ambient ancestor.
- GREEN: `PYTHONPATH=tools pytest tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_ignores_ambient_ancestor_git_repo tools/tasktool/tests/test_migrate_cli.py::test_accept_authoritative_is_noop tools/tasktool/tests/test_migrate_cli.py::test_accept_authoritative_acquires_authority_lock -q` -> `3 passed`.
- GREEN: `PYTHONPATH=tools pytest tools/tasktool/tests/ -q` -> `310 passed`.

## F2

Status: documented as routed-state evidence; no code change needed in this slice.

Evidence:
- Commit: `X12: resolve post-slice review findings`.
- Files: `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md`, this resolution file.
- Authoritative checkout command: `/home/simon/Dev/sigreer/skills/superstar ./tools/tasktool/tasktool show X12`.
- Result: `status: in_progress`, `started: 2026-05-20`, refs include the X12 spec and plan.
- Explanation: the implementation worktree's checked-out `docs/tasklist.json` can be stale under authoritative-checkout routing; lifecycle state lives in the authoritative checkout. Reviewer context should use routed authority state for task lifecycle.

## F3

Status: fixed.

Evidence:
- Commit: `X12: resolve post-slice review findings`.
- Files: `tools/tasktool/commands.py`, `tools/tasktool/tests/test_migrate_cli.py`.
- Change: `config migrate-from-local --accept-authoritative` now enters `tasktool_lock(authority)`, re-checks clean authority state, re-reads authoritative `docs/tasklist.json`, recomputes deltas, writes nothing, and prints a summary.
- RED: targeted regression command failed because the summary was missing and a held authority lock was ignored.
- GREEN: `PYTHONPATH=tools pytest tools/tasktool/tests/test_cli_integration.py tools/tasktool/tests/test_migrate_cli.py -v` -> `36 passed`.

## S1.F1

Status: fixed.

Evidence:
- Commit: `X12: resolve post-slice review findings`.
- Files: `tools/tasktool/cli.py`, `tools/tasktool/tests/test_cli_integration.py`.
- GREEN: `PYTHONPATH=tools pytest tools/tasktool/tests/ -q` -> `310 passed`.
- GREEN: `PYTHONPATH=tools pytest tools/tasktool/tests/test_cli_integration.py tools/tasktool/tests/test_migrate_cli.py -v` -> `36 passed`.

## S1.F2

Status: fixed.

Evidence:
- Commit: `X12: resolve post-slice review findings`.
- Files: `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md`.
- Change: plan checklist checkboxes are marked complete, and the evidence section records RED/GREEN test results plus routed lifecycle state.
- GREEN: `./tools/tasktool/tasktool validate` -> `ok`.

## S1.F3

Status: documented as routed-state evidence; no code change needed in this slice.

Evidence:
- Commit: `X12: resolve post-slice review findings`.
- Files: `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md`, this resolution file.
- Authoritative checkout command: `/home/simon/Dev/sigreer/skills/superstar ./tools/tasktool/tasktool show X12`.
- Result: `status: in_progress`, `started: 2026-05-20`.
- Explanation: stale review-context `docs/tasklist.json` is a workflow context hole for reviewers, not an implementation worktree file to hand-edit. The plan now calls out that routed lifecycle state lives in the authoritative checkout.

## S1.F4

Status: fixed.

Evidence:
- Commit: `X12: resolve post-slice review findings`.
- Files: `tools/tasktool/commands.py`, `tools/tasktool/tests/test_migrate_cli.py`.
- Change: `--accept-authoritative` uses the lock path and exits with a no-write summary.
- RED: held-lock regression failed before the fix because the command returned 0 without acquiring the lock.
- GREEN: targeted regression command -> `3 passed`.
