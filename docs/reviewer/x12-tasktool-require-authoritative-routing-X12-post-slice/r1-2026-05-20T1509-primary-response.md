# Review — 2026-05-20-X12-tasktool-require-authoritative-routing.md (post-slice, round 1)

- Target: `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md`
- Request: `docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/r1-2026-05-20T1509-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 - Severity: blocking  
`PYTHONPATH=tools pytest tools/tasktool/tests/ -q` fails: `tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_writes_project_config` expects `.tasktool/config.json` under the test `cwd`, but it is not written there. This violates the plan’s final gate at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888-1894`. The likely trigger is `_find_repo_root()` selecting an ancestor with `.git` at `tools/tasktool/cli.py:8-12`; in this review environment `/tmp/.git` exists, so the config is written to `/tmp/.tasktool/config.json` instead of the test tmpdir. Test expectation is at `tools/tasktool/tests/test_cli_integration.py:380-388`.

F2 - Severity: blocking  
X12 is not lifecycle-started for a post-slice gate. `docs/tasklist.json:176-185` still has `started: null` and `status: ready`, while the plan explicitly requires `tasktool start X12` at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:19-25` and later says to leave the row `in_progress` before post-slice review at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1896-1898`. `./tools/tasktool/tasktool show X12` confirms `status: ready`.

F3 - Severity: important  
`config migrate-from-local --accept-authoritative` returns before the lock/re-read/exit-summary path. `tools/tasktool/commands.py:289-290` exits immediately after printing the initial diff. The spec requires acquiring `tasktool_lock`, re-reading authoritative state inside the lock, and printing a one-line summary at `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md:107-109`. This leaves the verification-mode semantics weaker than specified and untested for concurrent/stale authoritative state.

2. Open questions / assumptions

Was the full tasktool suite previously run in an environment without `/tmp/.git`? If so, that evidence is environment-sensitive and should not be used as the only closeout proof.

3. Suggested document edits

Update the plan/evidence section to record the actual verification command output, including the failing test if this review result is accepted. Do not mark X12 close-ready until the task row is moved to `in_progress` and the suite is green.

4. Verification gaps / commands that should be run

Run:

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/ -q
./tools/tasktool/tasktool show X12
./tools/tasktool/tasktool validate
```

I ran those here: `validate` passes, but the full tasktool suite fails as described above, and X12 remains `ready`.

Overall verdict: revise


1. Findings

F1 - Severity: blocking  
`PYTHONPATH=tools pytest tools/tasktool/tests/ -q` fails: `tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_writes_project_config` expects `.tasktool/config.json` under the test `cwd`, but it is not written there. This violates the plan’s final gate at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888-1894`. The likely trigger is `_find_repo_root()` selecting an ancestor with `.git` at `tools/tasktool/cli.py:8-12`; in this review environment `/tmp/.git` exists, so the config is written to `/tmp/.tasktool/config.json` instead of the test tmpdir. Test expectation is at `tools/tasktool/tests/test_cli_integration.py:380-388`.

F2 - Severity: blocking  
X12 is not lifecycle-started for a post-slice gate. `docs/tasklist.json:176-185` still has `started: null` and `status: ready`, while the plan explicitly requires `tasktool start X12` at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:19-25` and later says to leave the row `in_progress` before post-slice review at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1896-1898`. `./tools/tasktool/tasktool show X12` confirms `status: ready`.

F3 - Severity: important  
`config migrate-from-local --accept-authoritative` returns before the lock/re-read/exit-summary path. `tools/tasktool/commands.py:289-290` exits immediately after printing the initial diff. The spec requires acquiring `tasktool_lock`, re-reading authoritative state inside the lock, and printing a one-line summary at `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md:107-109`. This leaves the verification-mode semantics weaker than specified and untested for concurrent/stale authoritative state.

2. Open questions / assumptions

Was the full tasktool suite previously run in an environment without `/tmp/.git`? If so, that evidence is environment-sensitive and should not be used as the only closeout proof.

3. Suggested document edits

Update the plan/evidence section to record the actual verification command output, including the failing test if this review result is accepted. Do not mark X12 close-ready until the task row is moved to `in_progress` and the suite is green.

4. Verification gaps / commands that should be run

Run:

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/ -q
./tools/tasktool/tasktool show X12
./tools/tasktool/tasktool validate
```

I ran those here: `validate` passes, but the full tasktool suite fails as described above, and X12 remains `ready`.

Overall verdict: revise

---

## Reviewer stderr (tail)

```text
fig.json` instead of the test tmpdir. Test expectation is at `tools/tasktool/tests/test_cli_integration.py:380-388`.

F2 - Severity: blocking  
X12 is not lifecycle-started for a post-slice gate. `docs/tasklist.json:176-185` still has `started: null` and `status: ready`, while the plan explicitly requires `tasktool start X12` at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:19-25` and later says to leave the row `in_progress` before post-slice review at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1896-1898`. `./tools/tasktool/tasktool show X12` confirms `status: ready`.

F3 - Severity: important  
`config migrate-from-local --accept-authoritative` returns before the lock/re-read/exit-summary path. `tools/tasktool/commands.py:289-290` exits immediately after printing the initial diff. The spec requires acquiring `tasktool_lock`, re-reading authoritative state inside the lock, and printing a one-line summary at `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md:107-109`. This leaves the verification-mode semantics weaker than specified and untested for concurrent/stale authoritative state.

2. Open questions / assumptions

Was the full tasktool suite previously run in an environment without `/tmp/.git`? If so, that evidence is environment-sensitive and should not be used as the only closeout proof.

3. Suggested document edits

Update the plan/evidence section to record the actual verification command output, including the failing test if this review result is accepted. Do not mark X12 close-ready until the task row is moved to `in_progress` and the suite is green.

4. Verification gaps / commands that should be run

Run:

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/ -q
./tools/tasktool/tasktool show X12
./tools/tasktool/tasktool validate
```

I ran those here: `validate` passes, but the full tasktool suite fails as described above, and X12 remains `ready`.

Overall verdict: revise


hook: Stop
hook: Stop Completed
tokens used
100,049
```
