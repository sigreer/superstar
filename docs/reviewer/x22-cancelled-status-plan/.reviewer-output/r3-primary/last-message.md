1. Findings

F7 — Severity: important  
The plan still contains a few non-executable snippets against the current CLI/module APIs. In `tools/tasktool/cli.py`, the file imports `commands` and dispatch uses `root`, not `repo_root`; the plan’s cancel dispatch snippet calls bare `cmd_cancel(repo_root=repo_root, ...)`, which would raise if copied directly (`docs/plans/2026-05-23-X22-cancelled-status.md:673-679`; current pattern at `tools/tasktool/cli.py:6`, `:289`, `:435-436`). Task 14’s brief tests call `brief(repo_root=..., id=...)`, but `tasktool.brief.brief` currently accepts `(Project, qid)`; the repo-root wrapper is `cmd_brief` (`docs/plans/...:1298-1318`; `tools/tasktool/brief.py:44`; `tools/tasktool/commands.py:1859-1863`). Task 9’s title test passes `title=`, but `cmd_title` takes `new=` (`docs/plans/...:889-892`; `tools/tasktool/commands.py:1386`). These will create false failures during implementation unless corrected.

F1 — Severity: blocking — RESOLVED  
Still resolved. The plan covers `brief.py`, `cmd_show`, active cancelled row reason surfacing, and archived-X not-found behavior in Task 14 (`docs/plans/2026-05-23-X22-cancelled-status.md:1284-1387`).

F2 — Severity: important — RESOLVED  
Still resolved. Task 2 includes an instance-level JSON Schema rejection test for a raw task row with `status: "cancelled"` (`docs/plans/...:161-178`).

F3 — Severity: important — RESOLVED  
Still resolved. Task 9 includes direct `cmd_set(..., status="cancelled")` rejection and a `tasktool cancel` hint (`docs/plans/...:848-853`, `:917-926`).

F4 — Severity: important — RESOLVED  
Still resolved. Task 7 and Task 8 test cancelled notification calls for direct slice/X cancellation and cascaded phase cancellation (`docs/plans/...:569-581`, `:761-774`).

F6 — Severity: important — RESOLVED  
Resolved in this revision. Task 13 now explicitly covers `cmd_phase_status` open-phase/open-X filters and `cmd_worktree_prune` terminal handling, with tests and implementation notes replacing strict `Status.DONE` checks with `is_terminal()` where the spec requires it (`docs/plans/...:1151-1280`; spec contract at `docs/specs/2026-05-23-X22-cancelled-status-design.md:155-175`; current code sites at `tools/tasktool/commands.py:1523-1527`, `:2067-2073`).

F5 — Severity: minor — RESOLVED  
Resolved. The smoke block now uses the existing global `--project-root` option before the subcommand (`docs/plans/...:1472-1490`; parser at `tools/tasktool/cli.py:34-43`, `:59-64`).

2. Open questions / assumptions

None. I treated the plan’s inline snippets as intended implementation guidance because the document is task-by-task and asks implementers to copy/adapt the snippets.

3. Suggested document edits

- In Task 7, change the CLI dispatch snippet to:
  `commands.cmd_cancel(repo_root=root, id=args.id, reason=args.reason, cascade=args.cascade, no_archive=args.no_archive)`.
- In Task 14 tests, either call `commands.cmd_brief(repo_root=..., id=...)` or load the project and call `brief(project, "P1.S1")`.
- In Task 9’s title test, call `cmd_title(..., new="new title")`.
- Optional cleanup: remove or reword the Task 7 note saying a phase-cancel test should still fail, since phase-cancel tests are not introduced until Task 8 (`docs/plans/...:690-696`).

4. Verification gaps / commands that should be run

Keep the existing final gate block. After the API-snippet fixes above, the plan’s targeted gates are sufficient:

```bash
PYTHONPATH=tools python3 -m pytest tools/tasktool/tests/ -q
PYTHONPATH=tools python3 -m pytest tools/tasktool/tests/test_commands.py -q -k "phase_status or worktree_prune or cancelled"
PYTHONPATH=tools python3 -m pytest tools/tasktool/tests/test_cli_integration.py -q -k cancel
tools/tasktool/tasktool validate --strict-format
tools/tasktool/tasktool show X22
```

Overall verdict: ready with small edits

