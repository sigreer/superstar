# P5 Worktree Lifecycle Feedback

I think the audit identifies the right root problem and the right ownership boundary. The important shift is the post-discussion update: worktree lifecycle should be tasktool-owned, not skill-owned or project-doc-owned.

The strongest argument is that the current skill makes every agent repeatedly re-derive facts that tasktool already knows: slice ID, slug, authoritative branch, repo root, lifecycle state, and whether the work is implementation-bound. Moving creation/adoption/cleanup into `tasktool start` and `tasktool close` turns that from repeated reasoning into deterministic tooling.

I would support the proposed P5 direction with a few refinements:

- Make `tasktool start <id>` idempotent. If a slice already has a recorded live worktree, it should print/reuse that path rather than create another one.
- Store both `worktree_path` and `worktree_branch` on the slice. Close/prune checks need a stable branch reference, not just a path.
- Treat native harness worktrees as an adoption path. If already inside a linked worktree, tasktool should adopt or verify it rather than fight the harness.
- Be careful with `tasktool close` auto-pruning if the command is run from inside the worktree being removed. It may need to defer cleanup, run from the authoritative checkout, or print a follow-up cleanup command.
- Keep subagent behavior explicit: parent creates/adopts the worktree; subagents inherit cwd and must not call `tasktool start`.
- Include stale-state repair commands early: `tasktool worktree list`, `status`, `adopt`, and `prune` are not extras. They are needed because drift is one of the observed failures.

I would shape P5 roughly as:

1. Add tasktool-managed worktree lifecycle: schema fields, canonical `.worktrees/worktree-<id>-<slug>` path, `start`, `adopt`, `list/status/prune`, and `.gitignore` verification.
2. Add close/cleanup guards: merged branch check, dirty/untracked/stash checks, `--keep-worktree`, and guarded prune behavior.
3. Rewrite `using-git-worktrees` as a thin pointer to tasktool, with a subagent early-exit and much less prose.

The key thing I would avoid is landing this as only a skill rewrite. Shrinking the skill helps, but the larger win is removing the decision tree from the agent path entirely. Tasktool should make the correct path the easy path.
