1. Findings

F1 Severity: blocking - RESOLVED. The spec now explicitly gates `tasktool set <id> --status done` via D7 and the shared landed-gate applicability/callout at `docs/specs/2026-06-05-P8.S1-close-gate-lifecycle-auto-commit-design.md:17`, `:23-31`, with tests at `:110-111`.

F2 Severity: minor - RESOLVED. The hook acceptance reference now points to the real template path, `tools/tasktool/templates/pre-commit-tasktool`, at `docs/specs/2026-06-05-P8.S1-close-gate-lifecycle-auto-commit-design.md:121`.

2. Open questions / assumptions

- Assumption: `cmd_set(status=done)` should reuse the same gate implementation but may have command-specific refusal text if needed; the current spec is sufficient because it defines shared behavior and dedicated tests.
- Assumption: including prune deferral in auto-commit scope is intentional, even though D1 says “worktree-prune completion only.”

3. Suggested document edits

- Small clarity edit: change D1 from “close + worktree-prune completion only” to “close + worktree-prune state changes” or explicitly mention deferral there, matching the later deferral call site at `:85`.
- In the escape hatch subsection, mention `tasktool set <id> --status done --allow-unlanded --reason "..."` alongside `tasktool close`, since D7 makes it a supported path.

4. Verification gaps / commands that should be run

- `python -m pytest tools/tasktool/tests`
- Targeted CLI tests for `tasktool set P1.S1 --status done` with an unlanded recorded branch, including refusal and override audit note.
- Targeted pathspec auto-commit test with unrelated staged content confirming only command-authored paths are committed.

Overall verdict: ready with small edits