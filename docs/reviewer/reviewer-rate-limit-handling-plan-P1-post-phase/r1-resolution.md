# Resolution for r1

## F1
Status: fixed
Evidence:
- Commit: a4f6d65
- Files: `skills/external-review/scripts/external-reviewer.py:178-260` (state_file_path, _state_lock_path, _StateLock, load_state, save_state, _load_state_locked, _save_state_locked, update_state)
- Verification: `python3 -m pytest skills/external-review/tests/test_state_file.py -v` → 17 passed

Notes:
Both load_state and save_state now acquire fcntl.flock(LOCK_EX) on a
companion lock file (`<state>.lock`, mode 0o600, parent dir 0o700).
Previously save_state held the lock on the .tmp file (which is unlinked by
os.replace, defeating cross-process exclusion). Added an explicit
`update_state(mutator)` helper that performs a locked read-modify-write so
dependent read/write pairs are atomic across processes — recommended for
all rate-limit recorders that read state, mutate, then write. New test
`test_save_state_concurrent_writers_preserve_keys` forks two writers that
each load+mutate+save a distinct key under contention; both keys persist.
A second new test `test_state_lock_file_exists_after_save` asserts the
companion is created next to the state file.

## F2
Status: fixed
Evidence:
- Commit: a4f6d65
- Files: `skills/external-review/tests/test_rate_limit_detection.py` (new `test_claude_pattern_extracts_reset_time`)
- Verification: `python3 -m pytest skills/external-review/tests/test_rate_limit_detection.py -v` → 5 passed

Notes:
Inspection confirmed the pattern was already non-capturing:
`(?:rate limit|rate-limited).*?reset (?:at|in)? ?(.+?)$`. Group 1 already
captures the reset clock, not the alternation. No source change required.
A new regression test pins this contract: a "rate limit exceeded. Reset at
18:30" stderr produces `name == "claude_cli_rate_limit"` and the parsed
reset_at lands on 18:30 local (not the 4-hour fallback). This guards
against future refactors that might re-introduce the capturing alternation.

## F3
Status: fixed
Evidence:
- Commit: 80364c5
- Files: `docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md:2984-2995`

Notes:
Flipped the "Invoke `superstar:finishing-a-development-branch`" checkbox
from [x] to [ ] with an inline note pointing at the new "TASKLIST.md
waiver" section. The waiver explains that this fork has no
`docs/TASKLIST.md` by design (CLAUDE.md opt-out) and that the integration
step is held until the user explicitly requests it. This resolves the
drift between the plan and the close-out commit (`c325439`) which had
already labelled the work as "Ready for finishing-a-development-branch".

## S1.F1
Status: fixed (same fix as F1)
Notes:
Duplicate of F1.

## S1.F2
Status: fixed
Evidence:
- Commit: a4f6d65
- Files: `skills/external-review/scripts/external-reviewer.py:1722-1732` (main() arg hoist)
- Verification: `python3 -m pytest skills/external-review/tests/test_state_file.py::test_reviewer_cmd_flag_hoists_to_env -v`

Notes:
`main()` now hoists `args.reviewer_cmd` into `os.environ["AGENT_REVIEWER_CMD"]`
immediately after parse_args() — alongside the existing `--state-file`
hoist — so `reviewer_cmd_basename()` honours the CLI flag value as the
state key. The hoist is conditional on the flag differing from the
existing env var, so argparse's env-default echo-back is a no-op. A new
end-to-end test spins up a fake rate-limited reviewer via
`--reviewer-cmd <path>` with AGENT_REVIEWER_CMD unset in the environment
and asserts the resulting state-file entry is keyed by the CLI-provided
path.

## S1.F3
Status: fixed
Evidence:
- Commit: a4f6d65
- Files: `skills/external-review/scripts/external-reviewer.py:1635-1647` (run_show_limit)
- Verification: `python3 -m pytest skills/external-review/tests/test_show_clear_limit.py::test_show_limit_prunes_expired -v`

Notes:
`run_show_limit` now iterates over a snapshot of `state["limits"]` keys
and calls `get_active_limit(key)` for each, exploiting that helper's
existing side-effect of pruning expired/malformed entries from the state
file. After the prune pass it re-reads state and prints. A new test
seeds an expired entry, runs `show-limit`, asserts "no active limits" on
stdout, and confirms the expired entry was removed from the on-disk
state file.

## S1.F4
Status: fixed (same as F3)
Notes:
Duplicate of F3.
