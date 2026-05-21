1. Findings

S1.F4 — Severity: blocking — UNRESOLVED — The collection collision is fixed by `pyproject.toml:1-3`, but the documented full pytest gate still does not pass as written. The plan requires `python3 -m pytest scripts/tests/ tools/tasktool/tests/ skills/external-review/tests/ -v` and expects every test to pass at `docs/plans/2026-05-21-X16-shim-version-stamping.md:2302`. Running that exact command now collects 666 tests, then fails with 41 failures: `625 passed, 41 failed`. The failures share the same root cause: tests invoking `external-reviewer.py review` hit the default reviewer state lock under `/home/simon/.config/superstar/reviewer-state.json.lock`, and this review sandbox cannot write there. The failing path is reached through `get_active_limit()` at `skills/external-review/scripts/external-reviewer.py:1340`, `load_state()` at `skills/external-review/scripts/external-reviewer.py:237`, and `_StateLock.__enter__()` creating the lock file at `skills/external-review/scripts/external-reviewer.py:220`.

F1 — RESOLVED — X16 remains `ready`, but r3 already established this is intentional until a ready post-slice verdict returns; the plan still sequences closeout after review at `docs/plans/2026-05-21-X16-shim-version-stamping.md:2359`.

F2 — RESOLVED — `bash scripts/deploy.sh --check` exits 0 and prints the `Pre-commit hook:` row as `OK v6.5.0`.

F3 — RESOLVED — The linked-worktree hook path fix remains covered; the aggregate run reached and passed `tools/tasktool/tests/test_hook_handshake.py::test_drift_returns_error_in_worktree`.

2. Open questions / assumptions

I assume the Step 11 pytest command is meant to be runnable in the reviewer gate environment as written. If the intended contract is “run with a writable `AGENT_REVIEWER_STATE_FILE`,” that needs to be encoded in the plan or the tests should isolate that env var themselves.

3. Suggested document edits

No document-only edit is sufficient if Step 11 remains the gate. Either make the affected tests set `AGENT_REVIEWER_STATE_FILE` to `tmp_path`, or update the gate command to provide a writable state file explicitly.

4. Verification gaps / commands that should be run

Fresh verification I ran:

```bash
python3 -m pytest scripts/tests/ tools/tasktool/tests/ skills/external-review/tests/ -v
# 666 collected; 625 passed, 41 failed

bash scripts/deploy.sh --check
# exit 0; pre-commit OK v6.5.0

bash scripts/bump-version.sh --check
# exit 0; all declared files in sync at 6.5.0

tools/tasktool/tasktool show X16
# status: ready

AGENT_REVIEWER_STATE_FILE=/tmp/x16-reviewer-state.json python3 -m pytest \
  skills/external-review/tests/test_work_id.py::test_spec_without_work_id_ok \
  skills/external-review/tests/test_returncode_status_persisted.py::test_ok_round_persists_status_and_returncode \
  skills/external-review/tests/test_diff_wiring.py::test_round2_embeds_diff_in_prompt_for_spec_kind -q
# 3 passed
```

Overall verdict: revise