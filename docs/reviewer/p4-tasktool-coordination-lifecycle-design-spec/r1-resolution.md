# Round 1 Resolution

Resolved reviewer findings from `r1-2026-05-19T2153-response.md`.

- F1: Updated the design so every authoritative-mode mutation uses the shared tasktool lock, including direct invocations from the authoritative checkout. Updated the plan with an authority-root lock contention test.
- F2: Replaced committed absolute-path config with tracked project policy plus machine-local root discovery via `TASKTOOL_AUTHORITY_ROOT` or `git worktree list --porcelain`. Updated config tests and CLI initializer steps accordingly.
- F3: Added a two-root command contract to the spec. Updated the plan to require `invocation_root` for reviewer artifacts and `write_root` for tasklist load/save/stage, with tests for `close`, `set --status done`, and out-of-repo reviewer paths.
- F4: Defined `tasktool set <id> --status in_progress` as a compatibility alias for `tasktool start <id>`. Updated the plan with a regression test and implementation guidance.
