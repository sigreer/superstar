1. Findings

F1 (Severity: blocking) RESOLVED. The plan now moves lifecycle refusal checks ahead of worktree mutation in `cmd_start` via `_preflight_start` before `_apply_start_*` (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:899-922`, `:926-938`) and adds explicit done/blocked no-side-effect tests (`:1143-1177`).

F2 (Severity: blocking) RESOLVED. The auto-adopt test now creates an authoritative checkout, commits the tasklist row before creating the linked worker, runs `start` from the linked worktree with authority routing, and asserts the authoritative `docs/tasklist.json` is updated (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:1250-1297`).

F7 (Severity: blocking) New. The `--ad-hoc` task is internally inconsistent and will fail its own planned test. `cmd_start` immediately dispatches to `_start_ad_hoc` whenever `ad_hoc is not None`, ignoring any positional `id` (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:893-896`), while the planned acceptance test requires `tasktool start P1.S1 --ad-hoc x` to be rejected (`:1401-1405`). `_start_ad_hoc` has no `id` parameter and cannot enforce that rule (`:1417-1434`). Add the rejection before the early return, or change the test/CLI contract.

F3 (Severity: important) UNRESOLVED. The implementation snippet no longer hardcodes `main`; it reads `authoritative_branch` (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:1749-1764`). But the prior finding also asked for a non-`main` fixture, and the plan still has no such test. The only status tests use `git init -b main` (`:1508-1522`, `:1686-1721`). Add a `develop` or similarly named authoritative branch fixture that proves `worktree status` reports ahead/behind against the configured parent.

F4 (Severity: important) UNRESOLVED. The plan clarifies that `project-setup` owns the installer acceptance (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:36`), but the proposed skill row is not executable in the normal repo-root context: it runs `python -c "from tasktool.worktree_lifecycle import ..."` without setting `PYTHONPATH` (`:2043-2049`). In this repo, `python -c "import tasktool"` from the root fails unless the `tools/tasktool/tasktool` launcher has exported `PYTHONPATH` (`tools/tasktool/tasktool:4-6`). Either make the row use an executable path that sets `PYTHONPATH`, add a small helper command reachable through `tools/tasktool/tasktool`, or keep the `.gitignore` edit as shell logic. Also, line `:2125` says skill-runtime exercises the idempotence behavior, but this plan only adds helper unit tests, not an end-to-end project-setup acceptance gate.

F5 (Severity: important) RESOLVED. The plan explicitly rejects coercion, adds strict deserializer helpers for bool/string values, and adds malformed raw JSON tests (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:301-364`, `:447-461`, `:464-470`).

F6 (Severity: minor) RESOLVED. New command snippets use existing `_subprocess`, and the new lifecycle module imports `subprocess` where it uses bare `subprocess.run` (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:986-999`, `:1756-1774`, `:130`, `:760-768`).

2. Open questions / assumptions

- Should `--ad-hoc` be represented as a mutually exclusive mode that forbids an ID at argparse level, or should `cmd_start` own the semantic rejection? The current plan has the test but not the implementation.
- For project-setup, is it acceptable for the skill to depend on a repo-local `tools/tasktool` tree in arbitrary target repos, or should the `.gitignore` audit remain independent shell/file logic?

3. Suggested document edits

- In Task 7, add `if id is not None: raise CommandError("--ad-hoc does not accept an id")` before `_start_ad_hoc(...)`, or remove the rejected-ID test and state that the positional ID is ignored. Rejection is the safer CLI contract.
- In Task 9, add a non-`main` branch fixture for `worktree status`, including a config with `authoritative_branch` set to that branch and an assertion that output says `vs <branch>`.
- In Task 11, replace bare `python -c "from tasktool..."` skill snippets with a launcher-backed invocation or an explicit `PYTHONPATH=<active-superstar>/tools python -c ...` pattern. Add a verification step that actually runs the row command in a repo-root shell.

4. Verification gaps / commands that should be run

- `cd tools && python -m pytest tasktool/tests/test_start_worktree.py -v -k ad_hoc`
- `cd tools && python -m pytest tasktool/tests/test_worktree_subcommands.py -v -k worktree_status` with a non-`main` authoritative branch case added.
- From repo root, verify the project-setup row command works without ambient environment assumptions.

Overall verdict: revise

