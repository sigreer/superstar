# Resolution for r2

## F1
Status: fixed
Evidence:
- Commit: 0b10c0e26b2653715270cfb636758169f22ebb18
- Files: `skills/external-review/scripts/external-reviewer.py:1172-1186` (run_one_reviewer rate-limit recorder; replaced load_state/save_state pair with update_state(mutator))
- Files: `skills/external-review/tests/test_state_concurrency.py` (new — exercises real production write path under concurrency)
- Verification: `python3 -m pytest skills/external-review/tests/ -q` -> 200 passed

Notes:
The production rate-limit write path in run_one_reviewer now uses the
atomic update_state(mutator) helper instead of the load -> mutate -> save
pattern, which kept a lock-free window open between read and write.
The buggy sequence was: load_state() acquired the lock briefly, read,
released; then save_state() reacquired the lock and wrote. A second
process landing between those two locked operations would read the
same stale baseline and the last writer would clobber the first key.

New test `test_concurrent_production_writers_preserve_distinct_keys`
spawns two concurrent end-to-end `review` invocations (each with its
own AGENT_REVIEWER_CMD pointing to a fake.sh that emits rate-limit
stderr and exits 1) sharing one AGENT_REVIEWER_STATE_FILE, then
asserts both reviewer keys survive in the final state. The test loops
8 iterations to amplify collision probability; without the fix it
fails reliably (verified by stashing the source change and re-running
— it failed at iteration 2 with one key clobbered). With the fix it
passes deterministically.

## F2
Status: resolved (round 1)
Notes: Carry-forward; regex was already non-capturing, regression test added in r1.

## F3
Status: resolved (round 1)
Notes: Carry-forward; plan checkbox + TASKLIST waiver landed in r1.

## S1.F2
Status: resolved (round 1)
Notes: Carry-forward.

## S1.F3
Status: resolved (round 1)
Notes: Carry-forward.
