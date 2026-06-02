1. Findings

F1. Severity: blocking — RESOLVED. Step 8 and the proposed `_review()` helper now capture `before`, run the reviewer, capture `after`, and return `after - before`, so the distinct-work-id collision check no longer self-intersects on earlier artifacts. See `docs/plans/2026-06-02-P7-S8-reviewer-artifact-investigation.md:101-114` and `:245-257`.

F2. Severity: important — UNRESOLVED. The same-work-id reproduction/test path is still time-dependent. Step 9.1 still relies on two fresh worktrees landing in the same minute, because the current bridge uses minute timestamps at `external-reviewer.py:2575`, and the plan does not pin or inject that timestamp. The Branch A test text says it pins “the unique token AND the timestamp” at `docs/plans/...:210`, but `_review()` only supports `fake_unique` at `:245-257`; there is no timestamp override. The negative-control test at `:275-281` can still fail across a minute boundary even with `AGENT_REVIEWER_FAKE_UNIQUE=deadbeef`.

F3. Severity: important — RESOLVED. Branch B now gives a concrete sanctioned lifecycle path: persist the decision artifact and run `tasktool cancel P7.S8 --reason ...`, matching the tasklist cancellation model. See `docs/plans/...:296-307`.

F4. Severity: important — NEW. Branch A’s proposed basename fix misses the existing primary-artifact rename path used when final-ready sweeps trigger. The plan changes `run_one_reviewer()` to call `request_basename()` at `docs/plans/...:194-207`, but the real script also reconstructs a basename during the late primary rename at `skills/external-review/scripts/external-reviewer.py:2692-2698` as `f"r{round_num}-{timestamp}{new_suffix}"`. If Branch A is implemented as written, a uuid-bearing primary request can be renamed back to a non-unique `rN-<minute>-primary-request.md`, leaving the same-folder/same-round/same-minute cross-worktree collision class open for sweep-enabled runs. The plan needs to update that rename path and add coverage for it, or explicitly constrain the fix/test scope so this path is impossible.

2. Open questions / assumptions

I assume Branch A remains a real executable branch, not just illustrative fallback text. If the intended outcome is strictly Branch B unless Step 9 finds a workflow-reachable collision, Branch A can be shorter, but it still should not contain a misleading or incomplete fix recipe.

3. Suggested document edits

- Add a deterministic timestamp injection strategy for Step 9.1 and Branch A tests, or avoid claiming deterministic same-minute collision proof.
- Align the helper prose with the actual helper: either add a timestamp override or remove “test-mode timestamp override.”
- In Branch A, update every basename construction path, including the final-ready primary rename at `external-reviewer.py:2696`.
- Add a regression case for sweep-triggered primary renaming if Branch A ships code.

4. Verification gaps / commands that should be run

- Run the Step 8 distinct-work-id repro and confirm `COLLISION: False`.
- For Branch A only, run a deterministic same-folder collision repro with timestamp and uniqueness both controlled.
- For Branch A only, run a sweep-enabled repro/test that exercises the primary rename path.
- Then run `python -m pytest skills/external-review/tests -q` and `python -m pytest tools/tasktool/tests -q`.

Overall verdict: revise