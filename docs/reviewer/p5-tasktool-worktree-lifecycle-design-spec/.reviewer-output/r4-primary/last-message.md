1. Findings

F1 Severity: blocking — RESOLVED. `tasktool close` remains non-destructive and cleanup is explicitly moved to `tasktool worktree prune` post-merge (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:139`-`159`).

F2 Severity: important — RESOLVED. Naming examples now match the lowercase canonical naming function (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:50`-`76`).

F3 Severity: important — RESOLVED. `close` retains worktree fields; prune/finalize null them and records audit state (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:141`, `159`, `167`-`173`).

F4 Severity: important — RESOLVED. Subagent detection now names concrete signals, precedence, fallback behavior, and tests (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:127`-`137`, `280`-`288`).

F5 Severity: minor — RESOLVED. Legacy migration policy is consistently warning-only/no automatic migration (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:37`, `216`-`220`, `300`).

F6 Severity: minor — UNRESOLVED, narrowed to an internal doc inconsistency. The normative ad-hoc flow now correctly requires `tasktool close <Xn> --no-archive` before prune, matching current `cmd_close` behavior where cross-cutting rows archive by default unless `no_archive` is set (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:120`-`123`; `tools/tasktool/commands.py:698`-`736`; `tools/tasktool/tests/test_commands.py:128`-`147`). But the lifecycle table still says `close <ad-hoc-Xn>` leaves the row in `cross_cutting` (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:204`-`206`). That row should say `close <ad-hoc-Xn> --no-archive`; otherwise the table contradicts the command sequence and current code.

F7 Severity: blocking — RESOLVED. The spec no longer claims a hard in-flight-subagent prune guard and explicitly defers leases/lock files (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:155`, `298`-`303`).

F8 Severity: important — RESOLVED. `--finalize` now requires a pending marker and verifies the recorded worktree is neither registered nor present on disk before nulling fields (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:161`-`173`, `267`-`271`).

2. Open questions / assumptions

- I assume the “row status → done, stays in `cross_cutting`” table entry is intended to describe the `--no-archive` path, not default `close`.

3. Suggested document edits

- In the lifecycle table, change `close <ad-hoc-Xn>` to `close <ad-hoc-Xn> --no-archive`.
- Optionally remove or qualify the separate “Prune on an ad-hoc `X<n>` row succeeds via the same flow” smoke test at line 263, since the end-to-end test at line 272 is now the stronger and clearer acceptance gate.

4. Verification gaps / commands

I ran:

- `tools/tasktool/tasktool validate --strict-format` — passed.

Still needed before implementation planning, as the spec already says:

- `python -m pytest tools/tasktool/tests -q`

Overall verdict: ready with small edits