1. Findings

F1 (Severity: blocking): The new tests are not hermetic under the reviewer bridge environment. `test_usage_metrics.py` builds subprocess envs from `os.environ.copy()` at `skills/external-review/tests/test_usage_metrics.py:56` and `:102` without setting `AGENT_REVIEWER_STATE_FILE` to a temp path, so the subprocess tries to lock/write the real user state file. In this review run, both review-round tests failed with `OSError: [Errno 30] Read-only file system: '/home/simon/.config/superstar/reviewer-state.json.lock'`. `test_reviewer_agent_wrapper.py:91-94` has the inverse leak: it copies inherited `AGENT_REVIEWER_*` vars, so the “required env missing” test can accidentally pass the wrapper’s required-env check and returned `0` here instead of expected `2`. Build test envs from a clean minimal dict, explicitly set only needed variables, and put `AGENT_REVIEWER_STATE_FILE` under `tmp_path`.

F2 (Severity: important): `external-reviewer stats` undercounts usage for thorough/exhaustive review rounds. The manifest records per-reviewer metrics at `skills/external-review/scripts/external-reviewer.py:2659-2680`, but `collect_review_stats` only reads the top-level primary `round_entry` fields at `skills/external-review/scripts/external-reviewer.py:2103-2120`. Sweep reviewer usage and duration are ignored, even though sweeps are a normal documented review mode. Provider comparisons will therefore report materially lower token/duration totals for the highest-cost review modes. Aggregate provider usage from `round_entry["reviewers"]` when present, falling back to top-level fields only for legacy manifests.

2. Open questions / assumptions

I assume the goal of “provider comparison” is actual reviewer-invocation cost visibility, not only primary-chain round cost. That matches the new per-reviewer manifest fields and the skill text warning not to mix exact provider usage into comparable estimates.

3. Suggested document edits

Update `skills/external-review/SKILL.md` around the stats description to say whether stats count review rounds or reviewer invocations. If the intended behavior is invocation-level accounting, document that sweeps are included.

4. Verification gaps / commands that should be run

I ran:

```bash
python3 -m pytest skills/external-review/tests/test_usage_metrics.py skills/external-review/tests/test_reviewer_agent_wrapper.py
```

Result: 3 failed, 5 passed. The failures are the hermetic-env issues described in F1.

Overall verdict: revise

