# Resolution for r2

## F1
Status: deferred
Notes:
Closeout (`tasktool close X16`) is the explicit final step after the post-slice review passes. The plan's Task 11 / T11 schedules this step; the coordinator runs it after r3+ verdict is `ready`. Not in scope for this fix round.

## F2
Status: fixed
Evidence:
- Commit: f618c6e
- Files: `scripts/deploy.sh:130` (new `check_hook`), `scripts/deploy.sh:272` (call site between Global shims and Plugin caches), `scripts/tests/test_deploy_check.py:131` (six new cases) and helper updates at `scripts/tests/test_deploy_check.py:28`.
- Verification:
  - `python3 -m pytest scripts/tests/test_deploy_check.py -v` → 13 passed.
  - `bash scripts/deploy.sh --check` against the real repo prints a new "Pre-commit hook" section with row `pre-commit  OK  v6.5.0 root=<repo>` and exits 0.

Notes:
Added a Pre-commit hook diagnostic section between Global shims and Plugin caches in `run_check`. The new `check_hook` function resolves the hook path via `git rev-parse --git-path hooks/pre-commit` (worktree-safe, matches the install.sh --hook resolution), then emits one of `OK / MISSING_TARGET / MALFORMED / DRIFT / MISSING_SOURCE / NOT_DEPLOYED` with the same exit-code semantics as the shim section. Foreign (non-tasktool) hooks and the absence of a git working tree emit `NOT_DEPLOYED` without flipping the exit code. Reuses the existing `PARSE_HEADER` awk (which already matches both `superstar-shim-*` and `superstar-hook-*` keys) and `EXPAND_PATH`. The test helper `_run_check` now accepts an optional `cwd` (and defaults to `home` so existing tests don't accidentally see the surrounding repo's hook), and the new cases create a fresh `git init` directory under `tmp_path` and exercise each lattice state.

## F3
Status: fixed
Evidence:
- Commit: f618c6e
- Files: `tools/tasktool/hook_handshake.py:26` (new `_git_hook_path` helper) and `tools/tasktool/hook_handshake.py:75` (replaced hardcoded path); `tools/tasktool/tests/test_hook_handshake.py:128` (new `test_drift_returns_error_in_worktree`).
- Verification: `python3 -m pytest tools/tasktool/tests/test_hook_handshake.py tools/tasktool/tests/test_pre_commit_hook.py -v` → 23 passed.

Notes:
Replaced the hardcoded `repo_top / ".git" / "hooks" / "pre-commit"` path with a `git rev-parse --git-path hooks/pre-commit` resolution and absolute-path normalization (relative results are joined with `repo_top`). This mirrors the worktree-safe resolution already in `tools/tasktool/install.sh --hook`. The new test creates a real linked worktree via `git worktree add`, sanity-checks that `.git` inside the worktree is a file (gitdir pointer), then writes a stale stamped hook at the path that `git rev-parse --git-path` reports (the common-dir hooks/ of the primary repo). The handshake correctly returns the drift message when invoked from inside the worktree — proving the previous hardcoded path would have silently missed it.
