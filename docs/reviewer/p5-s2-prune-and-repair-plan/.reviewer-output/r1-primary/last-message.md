1. Findings

F1. Severity: blocking — The plan’s execution preconditions are false in the live repo. The plan says `P5.S2` is ratified and that `P5.S1` is assumed shipped with `worktree` commands and model fields available (`docs/plans/2026-05-21-P5-S2-prune-and-repair.md:13-20`, `:49-57`). Live `docs/tasklist.json` has both `P5.S1` and `P5.S2` at `planning_status: "proposed"` and `status: "ready"` (`docs/tasklist.json:262-300`), and current tasktool has no `worktree` subcommand or `start --ad-hoc`/`--adopt` surface (`tools/tasktool/cli.py:97-99`). The plan is not executable until either P5.S1 lands and both rows are ratified, or this plan is rewritten to include the missing P5.S1 contracts.

F2. Severity: blocking — The serialization plan assumes a non-default omission policy that the current repo does not implement. Task 2 says to emit the audit fields only when non-default and expects `validate --strict-format` to leave `docs/tasklist.json` unchanged (`docs/plans/2026-05-21-P5-S2-prune-and-repair.md:162-187`). Current `serialize.py` uses `asdict(p)` and recursively emits all dataclass fields (`tools/tasktool/serialize.py:11-23`). If the audit fields are added directly to the dataclasses, canonical output will add default keys to every slice/X row, contradicting the plan’s gate. This needs an explicit serializer change or an explicit tasklist rewrite/migration expectation.

F3. Severity: important — The stash guard is broader than the spec and not tested for false positives. The spec asks for refusing stash entries “attributable to the worktree” (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:257-260`), but the planned helper treats any repository stash as dirty (`docs/plans/2026-05-21-P5-S2-prune-and-repair.md:472-484`). That can block pruning a clean worktree because of an unrelated stash from another worktree/branch. Either align the implementation with branch/worktree attribution, or document the stricter safety rule in the spec/plan and add a test for unrelated stashes.

F4. Severity: important — The branch-merged guard hard-codes `main` instead of using tasktool’s configured authoritative branch. The spec says merge into the slice’s authoritative parent, “e.g. `main`” (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:147-151`), and tasktool already stores `authoritative_branch` in config (`tools/tasktool/config.py:12-16`). The plan’s `_authoritative_parent_branch()` always returns `"main"` and leaves the mismatch as a known sharp edge (`docs/plans/2026-05-21-P5-S2-prune-and-repair.md:832-839`, `:1456-1458`). That should be resolved in the plan, not deferred inside a destructive cleanup command.

F5. Severity: minor — The in-place prune behavior is specified but intentionally left without explicit coverage. The spec lifecycle table requires `worktree prune` on `--in-place` slices to be a no-op that records `worktree_pruned_at` (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:198-202`). The plan only notes that this is “implicitly covered” and invites a reviewer to flag it (`docs/plans/2026-05-21-P5-S2-prune-and-repair.md:1443-1446`). Add the explicit test; this is cheap and protects a lifecycle row.

2. Open questions / assumptions

- Is `P5.S1` expected to be implemented before this plan is handed to workers? If yes, update tasklist state and rerun the plan review after S1 lands.
- Should stash handling be conservative across the whole repository, or limited to stashes attributable to the recorded worktree branch?
- Is the authoritative parent branch always the configured tasktool authoritative branch for P5, or will P5.S1 introduce per-slice parent metadata?

3. Suggested document edits

- Replace the “assumed shipped” P5.S1 section with a hard preflight: `tasktool show P5.S1`, `tasktool show P5.S2`, `tasktool start --help`, `tasktool worktree --help`, and a failure condition if S1 is not `done`/ratified and the CLI surface is absent.
- Amend Task 2 to match the actual serializer policy after P5.S1 lands. Do not assert unchanged canonical bytes unless non-default omission is really implemented.
- Change `_authoritative_parent_branch()` to read the resolved tasktool config’s authoritative branch, or add a task to introduce parent-branch metadata before prune.
- Add tests for unrelated stash behavior and in-place prune.

4. Verification gaps / commands that should be run

- `tools/tasktool/tasktool show P5.S1`
- `tools/tasktool/tasktool show P5.S2`
- `tools/tasktool/tasktool worktree --help`
- `tools/tasktool/tasktool validate --strict-format`
- `python -m pytest tools/tasktool/tests -q`

Overall verdict: revise

