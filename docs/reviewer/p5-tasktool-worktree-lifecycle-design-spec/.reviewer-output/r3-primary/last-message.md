1. Findings

F1 Severity: blocking — RESOLVED. The spec keeps `tasktool close` semantics unchanged and moves destructive cleanup to explicit `tasktool worktree prune` after merge-back (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:131`-`145`, `191`-`197`, `286`-`289`).

F2 Severity: important — RESOLVED. The schema example now uses lowercase path and branch names matching the normative naming function (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:50`-`76`, `85`-`89`).

F3 Severity: important — RESOLVED. `close` now explicitly retains `worktree_path`, `worktree_branch`, and `worktree_in_place`; prune/finalize nulls fields and records `worktree_pruned_at` (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:131`-`158`, `174`-`189`).

F4 Severity: important — RESOLVED. Subagent detection for `start` now names concrete signals, precedence, fallback semantics, and tests (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:119`-`129`, `257`-`266`).

F5 Severity: minor — RESOLVED. Legacy migration policy is consistently “warn, no automatic migration” (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:37`, `199`-`203`, `291`).

F6 Severity: blocking — UNRESOLVED, narrowed. The `AH<n>` ID-family issue is fixed by using normal `X<n>` rows, but the ad-hoc lifecycle still conflicts with current cross-cutting close/archive semantics. The spec says `tasktool close <Xn>` leaves an ad-hoc row in `cross_cutting` until `tasktool worktree prune <Xn>` runs (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:117`, `187`-`189`). Current `cmd_close` archives cross-cutting items by default unless `--no-archive` is supplied (`tools/tasktool/commands.py:698`-`736`), and tests lock that behavior (`tools/tasktool/tests/test_commands.py:128`-`147`). Once archived, the active row is removed (`tools/tasktool/commands.py:645`-`648`), so prune cannot find the row/fields unless the spec explicitly changes ad-hoc close behavior or requires `close --no-archive`.

F7 Severity: blocking — RESOLVED. The spec no longer claims a hard in-flight-subagent prune guard. It explicitly defers leases/lock files out of P5 and removes that guard from acceptance (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:147`, `271`-`282`, `289`).

F8 Severity: important — NEW. `worktree prune --finalize` is underspecified as a guard-bypassing state mutation. The spec says `--finalize` nulls fields and records the audit timestamp “assuming” external removal already happened, and the tests say it does so “without re-running guards” (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:153`-`158`, `181`-`183`, `250`-`251`). There is no required precondition that the recorded path is absent, no pending-prune marker from the first step, and no check that the removed worktree was the recorded path. That can hide a still-live/dirty worktree from `worktree list` by nulling its tracking fields.

2. Open questions / assumptions

- Should ad-hoc `tasktool close <Xn>` implicitly behave like `tasktool close <Xn> --no-archive`, or should the documented command be `tasktool close <Xn> --no-archive`?
- Should `--finalize` require a recorded “pending prune from inside” state, or is it enough to refuse unless the recorded path is no longer a registered git worktree and no filesystem directory remains at that path?
- For `tasktool start --ad-hoc <slug>`, should the command syntax omit `<id>` entirely? Current synopsis still reads `tasktool start <id> ... --ad-hoc <slug>`.

3. Suggested document edits

- In §5.3, replace the ad-hoc close sentence with an explicit storage-compatible command path, e.g. `tasktool close <Xn> --no-archive` is required before prune, followed by `tasktool archive-cross <Xn>` after prune.
- Add an ad-hoc lifecycle test that proves `close` leaves the row active and `archive-cross` only happens after prune.
- Define `--finalize` preconditions: recorded path must match the previously printed path, must no longer be a registered worktree, and tasktool must either have a pending-prune marker or independently verify the directory is gone before nulling fields.
- Update the CLI synopsis to clarify ad-hoc syntax, for example `tasktool start <id> [--in-place | --adopt <path>]` and `tasktool start --ad-hoc <slug>`.

4. Verification gaps / commands

I ran:

- `tools/tasktool/tasktool validate --strict-format` — passed.

Still needed before implementation planning:

- `python -m pytest tools/tasktool/tests -q`
- Tests for ad-hoc close/prune/archive ordering against current cross-cutting archive behavior.
- Tests for `--finalize` refusal when the recorded worktree still exists or was not the path staged by the first prune-from-inside step.

Overall verdict: revise

