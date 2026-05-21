# Resolution for r1

## F1
Status: deferred
Evidence:
- Commit: N/A (lifecycle close-out happens after review reaches ready verdict)
- Files: docs/tasklist.json (authoritative checkout, will be committed via slice closeout)
- Verification: closeout will run `tasktool close P5.S2` then commit the routed mutations

Notes:
F1 is the structural observation that the slice has not yet been closed. By the external-review protocol, post-slice review precedes `tasktool close`. The unstaged docs/tasklist.json in the authoritative checkout contains routed mutations from `tasktool ratify`/`start`/normalise during this slice; those will be committed alongside the close-out commit once the chain reaches ready. No code change resolves this within the review loop — it resolves itself when the chain closes.

## S1.F1
Status: deferred
Evidence: (same as F1; sweep duplicate)

Notes:
Same rationale as F1.

## F2
Status: fixed
Evidence:
- Commit: f00a97c (see git log; this commit also contains this resolution file — amend chain referencing previous SHA)
- Files: skills/finishing-a-development-branch/SKILL.md
- Verification: grep -n "tasktool worktree prune" skills/finishing-a-development-branch/SKILL.md; manual read of options 1 and 4

Notes:
Option 1 (merge path) no longer instructs `git branch -d` after default `tasktool worktree prune` (branch is already gone). Manual `git branch -d` is kept as a fallback for `--keep-branch` or non-tasktool worktrees. Option 4 (discard path) directs tasktool-owned worktrees to `tasktool worktree prune <slice-id> --force` (which handles both worktree dir AND branch with force-delete); `git branch -D` is the fallback for non-tasktool worktrees.

## S1.F2
Status: fixed
Evidence: same as F2.

Notes:
Sweep duplicate of F2.
