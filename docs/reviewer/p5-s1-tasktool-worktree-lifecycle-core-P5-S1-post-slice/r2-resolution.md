# Resolution for r2

## F1
Status: fixed (RESOLVED by primary in r1 verification; no further action required)
Evidence:
- Primary r2 verdict: ready — F1 marked RESOLVED in primary review at docs/reviewer/p5-s1-tasktool-worktree-lifecycle-core-P5-S1-post-slice/r2-...-primary-response.md
- Final close step happens after this r2 verdict passes.

Notes:
F1 is the closeout-gate finding; primary confirmed it is resolved for review purposes.

## F2
Status: fixed (RESOLVED by primary in r1 verification)
Evidence:
- Primary r2 verdict: ready — F2 marked RESOLVED.

Notes:
to_dict default omission landed in commit 48ead69 (r1 fix).

## F3
Status: fixed (RESOLVED by primary in r1 verification)
Evidence:
- Primary r2 verdict: ready — F3 marked RESOLVED.

Notes:
_read_context wired for cmd_worktree_list and cmd_worktree_status in commit 48ead69 (r1 fix).

## S1.F1
Status: fixed
Evidence:
- Commit: c3f3aa2c8ecb3269d05f1f2268d1512069e23c0a
- Files: `tools/tasktool/worktree_lifecycle.py`, `tools/tasktool/commands.py`, `tools/tasktool/tests/test_start_worktree.py`, `tools/tasktool/tests/test_worktree_subcommands.py`
- Verification: new tests assert `--adopt <main-checkout>` is rejected for both `start --adopt` and `worktree adopt`; existing adopt tests still pass; full suite 464 passed (up from 462, +2 new tests).

Notes:
Added `is_authoritative_checkout()` helper in `worktree_lifecycle.py` that compares a candidate path against the primary entry reported by `git worktree list --porcelain` (the first `worktree ` line; subsequent entries are linked worktrees). `_apply_start_adopt` and `cmd_worktree_adopt` now refuse with a precise error pointing the operator at `git worktree add` when the adopt path resolves to the main checkout. Auto-adopt was already correctly gated via `is_inside_linked_worktree()` (which returns False for the main checkout because `git rev-parse --git-dir` equals `--git-common-dir` there), so no change was required in the auto-adopt block of `cmd_start`.

## S1.F2
Status: deferred (closeout step, post-review)
Evidence:
- Same circular closeout-gate finding as F1/F2 in r1; the actual `tasktool close P5.S1` runs after this r2 verdict.

Notes:
No code change needed.
