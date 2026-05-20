1. Findings

F1 (Severity: blocking): RESOLVED. The subprocess test environments are now minimal and do not inherit coordinator `AGENT_REVIEWER_*` values. `test_usage_metrics.py:50-56` sets `AGENT_REVIEWER_STATE_FILE` under `tmp_path`, and both review-round subprocesses use that helper at `test_usage_metrics.py:65` and `test_usage_metrics.py:110`. The wrapper missing-env test also starts from a minimal env at `test_reviewer_agent_wrapper.py:88-94`.

F2 (Severity: important): RESOLVED. `collect_review_stats` now delegates provider accounting to `_provider_usage_records_for_stats`, which iterates `round_entry["reviewers"]` when present and falls back to the top-level round entry for legacy manifests at `external-reviewer.py:2070-2088`. The aggregation loop uses those invocation records at `external-reviewer.py:2124-2141`, and the new test covers primary+sweep counting at `test_usage_metrics.py:189-244`. The skill text documents that provider comparison counts reviewer invocations, including sweeps, at `SKILL.md:189`.

2. Open questions / assumptions

None.

3. Suggested document edits

None.

4. Verification gaps / commands that should be run, if any

I ran:

```bash
python -m pytest skills/external-review/tests/test_usage_metrics.py skills/external-review/tests/test_reviewer_agent_wrapper.py -q
```

Result: 9 passed, 1 warning. The warning is only pytest cache write failure under the read-only review worktree, not a test failure.

Overall verdict: ready