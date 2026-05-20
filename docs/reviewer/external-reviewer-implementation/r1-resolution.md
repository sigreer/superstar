## F1
Status: fixed
Evidence:
- Commit: pending
- Files: `skills/external-review/tests/test_usage_metrics.py`, `skills/external-review/tests/test_reviewer_agent_wrapper.py`
- Verification: `python -m pytest skills/external-review/tests/test_usage_metrics.py skills/external-review/tests/test_reviewer_agent_wrapper.py -q` -> 9 passed
- Verification: `python -m pytest skills/external-review/tests -q` -> 249 passed, 1 warning

Notes:
Subprocess tests now build minimal environments instead of copying the coordinator environment. The review-round tests set `AGENT_REVIEWER_STATE_FILE` under `tmp_path`, and the wrapper missing-env test starts from a clean environment containing only `PATH` and `AGENT_REVIEWER_PROVIDER`.

## F2
Status: fixed
Evidence:
- Commit: pending
- Files: `skills/external-review/scripts/external-reviewer.py`, `skills/external-review/tests/test_usage_metrics.py`, `skills/external-review/SKILL.md`
- Verification: `python -m pytest skills/external-review/tests/test_usage_metrics.py skills/external-review/tests/test_reviewer_agent_wrapper.py -q` -> 9 passed
- Verification: `python -m pytest skills/external-review/tests -q` -> 249 passed, 1 warning

Notes:
`collect_review_stats` now aggregates provider comparison records from each reviewer entry when `round_entry["reviewers"]` is present, falling back to the round-level entry for legacy manifests. The stats documentation now states that provider comparison counts reviewer invocations, including sweeps.
