<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 2 of x12-tasktool-require-authoritative-routing-X12-post-slice.

In incremental mode:
- Verify whether prior findings are resolved per the resolution report below.
- Reuse the existing finding IDs (F1, F2, …). If a prior finding is resolved,
  mark it RESOLVED in your findings list with its original ID. If still
  unresolved, keep its ID.
- Only introduce new finding IDs for genuine regressions caused by the fix, or
  blocking issues clearly missed in earlier rounds. Do not reopen broad review
  unless prior fixes changed broad architecture.

## Review chain summary

| round | verdict | findings | blocking |
|---|---|---|---|
| 1 | revise | 3 | 2 |

## Prior-round findings

Source: merged findings from r1 (authoritative)

# Merged findings for r1

## Primary

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


## Sweep 1

# Review — 2026-05-20-X12-tasktool-require-authoritative-routing.md (post-slice, round 1)

- Target: `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md`
- Request: `docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/r1-2026-05-20T1509-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

S1.F1 Severity: blocking — The required final verification gate is failing. The plan requires `PYTHONPATH=tools pytest tools/tasktool/tests/ -v` to pass at [docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888), but I ran it and got `1 failed, 307 passed`. The failure is `tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_writes_project_config`: the command exits 0, but `.tasktool/config.json` is not written under `tmp_path`, causing the read at [tools/tasktool/tests/test_cli_integration.py:387](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/tools/tasktool/tests/test_cli_integration.py:387) to raise `FileNotFoundError`. This blocks post-slice readiness.

S1.F2 Severity: important — The plan/checklist evidence was not updated, so the target document still presents the slice as unexecuted. Every implementation step remains unchecked, including lifecycle start at [docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:19](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:19) and final verification at [docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888). For a completion gate, this makes it ambiguous which steps were actually performed and which evidence is current.

S1.F3 Severity: important — The review-context task row in this worktree still says X12 is `ready` with `started: null` at [docs/tasklist.json:175](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/docs/tasklist.json:175). The authoritative checkout does show X12 as `in_progress`, but that mutation is staged/uncommitted in `/home/simon/Dev/sigreer/skills/superstar`. The prompt’s context file therefore contradicts the plan’s expected post-implementation state at [docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1896](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1896). Either the reviewer context needs to use the authoritative tasklist, or the completion evidence needs to call out that routed tasklist state lives outside the implementation branch.

S1.F4 Severity: minor — `--accept-authoritative` does not acquire the lock even though the spec/test plan calls it a locked verification path. The implementation returns immediately at [tools/tasktool/commands.py:289](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/tools/tasktool/commands.py:289), before the `tasktool_lock(authority)` block at [tools/tasktool/commands.py:295](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/tools/tasktool/commands.py:295). The plan/spec acceptance says this mode “acquires the lock, writes nothing” in the testing section, so either the implementation or the acceptance text should be corrected.

2. Open questions / assumptions

I treated the failing full-suite command as authoritative because it is the exact final verification command named by the plan. The failure may be sensitive to the current `/tmp/.git` ancestor in this environment, but that still means the repo’s own suite does not currently pass under the requested gate.

3. Suggested document edits

Update the plan checklist to reflect actual completed steps and attach the final verification result only after the suite is green.

Clarify tasklist evidence for routed lifecycle mutations: reviewers should know whether to inspect the implementation worktree’s `docs/tasklist.json` or the authoritative checkout’s tasklist.

If `--accept-authoritative` intentionally does not lock, update the spec/plan test expectation to stop claiming that it does.

4. Verification gaps / commands that should be run

`PYTHONPATH=tools pytest tools/tasktool/tests/ -v` currently fails and must be rerun after fixing `test_config_init_authority_writes_project_config`.

After the suite is green, rerun `git status --short` in both the implementation worktree and the authoritative checkout to make sure only intended review/tasklist artifacts remain dirty.

Overall verdict: revise
1. Findings

S1.F1 Severity: blocking — The required final verification gate is failing. The plan requires `PYTHONPATH=tools pytest tools/tasktool/tests/ -v` to pass at [docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888), but I ran it and got `1 failed, 307 passed`. The failure is `tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_writes_project_config`: the command exits 0, but `.tasktool/config.json` is not written under `tmp_path`, causing the read at [tools/tasktool/tests/test_cli_integration.py:387](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/tools/tasktool/tests/test_cli_integration.py:387) to raise `FileNotFoundError`. This blocks post-slice readiness.

S1.F2 Severity: important — The plan/checklist evidence was not updated, so the target document still presents the slice as unexecuted. Every implementation step remains unchecked, including lifecycle start at [docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:19](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:19) and final verification at [docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888). For a completion gate, this makes it ambiguous which steps were actually performed and which evidence is current.

S1.F3 Severity: important — The review-context task row in this worktree still says X12 is `ready` with `started: null` at [docs/tasklist.json:175](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/docs/tasklist.json:175). The authoritative checkout does show X12 as `in_progress`, but that mutation is staged/uncommitted in `/home/simon/Dev/sigreer/skills/superstar`. The prompt’s context file therefore contradicts the plan’s expected post-implementation state at [docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1896](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1896). Either the reviewer context needs to use the authoritative tasklist, or the completion evidence needs to call out that routed tasklist state lives outside the implementation branch.

S1.F4 Severity: minor — `--accept-authoritative` does not acquire the lock even though the spec/test plan calls it a locked verification path. The implementation returns immediately at [tools/tasktool/commands.py:289](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/tools/tasktool/commands.py:289), before the `tasktool_lock(authority)` block at [tools/tasktool/commands.py:295](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/tools/tasktool/commands.py:295). The plan/spec acceptance says this mode “acquires the lock, writes nothing” in the testing section, so either the implementation or the acceptance text should be corrected.

2. Open questions / assumptions

I treated the failing full-suite command as authoritative because it is the exact final verification command named by the plan. The failure may be sensitive to the current `/tmp/.git` ancestor in this environment, but that still means the repo’s own suite does not currently pass under the requested gate.

3. Suggested document edits

Update the plan checklist to reflect actual completed steps and attach the final verification result only after the suite is green.

Clarify tasklist evidence for routed lifecycle mutations: reviewers should know whether to inspect the implementation worktree’s `docs/tasklist.json` or the authoritative checkout’s tasklist.

If `--accept-authoritative` intentionally does not lock, update the spec/plan test expectation to stop claiming that it does.

4. Verification gaps / commands that should be run

`PYTHONPATH=tools pytest tools/tasktool/tests/ -v` currently fails and must be rerun after fixing `test_config_init_authority_writes_project_config`.

After the suite is green, rerun `git status --short` in both the implementation worktree and the authoritative checkout to make sure only intended review/tasklist artifacts remain dirty.

Overall verdict: revise

---

## Reviewer stderr (tail)

```text
l out that routed tasklist state lives outside the implementation branch.

S1.F4 Severity: minor — `--accept-authoritative` does not acquire the lock even though the spec/test plan calls it a locked verification path. The implementation returns immediately at [tools/tasktool/commands.py:289](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/tools/tasktool/commands.py:289), before the `tasktool_lock(authority)` block at [tools/tasktool/commands.py:295](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/tools/tasktool/commands.py:295). The plan/spec acceptance says this mode “acquires the lock, writes nothing” in the testing section, so either the implementation or the acceptance text should be corrected.

2. Open questions / assumptions

I treated the failing full-suite command as authoritative because it is the exact final verification command named by the plan. The failure may be sensitive to the current `/tmp/.git` ancestor in this environment, but that still means the repo’s own suite does not currently pass under the requested gate.

3. Suggested document edits

Update the plan checklist to reflect actual completed steps and attach the final verification result only after the suite is green.

Clarify tasklist evidence for routed lifecycle mutations: reviewers should know whether to inspect the implementation worktree’s `docs/tasklist.json` or the authoritative checkout’s tasklist.

If `--accept-authoritative` intentionally does not lock, update the spec/plan test expectation to stop claiming that it does.

4. Verification gaps / commands that should be run

`PYTHONPATH=tools pytest tools/tasktool/tests/ -v` currently fails and must be rerun after fixing `test_config_init_authority_writes_project_config`.

After the suite is green, rerun `git status --short` in both the implementation worktree and the authoritative checkout to make sure only intended review/tasklist artifacts remain dirty.

Overall verdict: revise
hook: Stop
hook: Stop Completed
tokens used
124,781
```



## Resolution report for prior round

# X12 post-slice r1 resolution

## F1

Status: fixed.

Evidence:
- Commit: `X12: resolve post-slice review findings`.
- Files: `tools/tasktool/cli.py`, `tools/tasktool/tests/test_cli_integration.py`.
- Change: `config init-authority` and `config init-local` now keep an unmarked current working directory as the bootstrap project root instead of climbing to an ambient ancestor git repo.
- RED: targeted regression command failed because `.tasktool/config.json` was written to the ambient ancestor.
- GREEN: `PYTHONPATH=tools pytest tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_ignores_ambient_ancestor_git_repo tools/tasktool/tests/test_migrate_cli.py::test_accept_authoritative_is_noop tools/tasktool/tests/test_migrate_cli.py::test_accept_authoritative_acquires_authority_lock -q` -> `3 passed`.
- GREEN: `PYTHONPATH=tools pytest tools/tasktool/tests/ -q` -> `310 passed`.

## F2

Status: documented as routed-state evidence; no code change needed in this slice.

Evidence:
- Commit: `X12: resolve post-slice review findings`.
- Files: `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md`, this resolution file.
- Authoritative checkout command: `/home/simon/Dev/sigreer/skills/superstar ./tools/tasktool/tasktool show X12`.
- Result: `status: in_progress`, `started: 2026-05-20`, refs include the X12 spec and plan.
- Explanation: the implementation worktree's checked-out `docs/tasklist.json` can be stale under authoritative-checkout routing; lifecycle state lives in the authoritative checkout. Reviewer context should use routed authority state for task lifecycle.

## F3

Status: fixed.

Evidence:
- Commit: `X12: resolve post-slice review findings`.
- Files: `tools/tasktool/commands.py`, `tools/tasktool/tests/test_migrate_cli.py`.
- Change: `config migrate-from-local --accept-authoritative` now enters `tasktool_lock(authority)`, re-checks clean authority state, re-reads authoritative `docs/tasklist.json`, recomputes deltas, writes nothing, and prints a summary.
- RED: targeted regression command failed because the summary was missing and a held authority lock was ignored.
- GREEN: `PYTHONPATH=tools pytest tools/tasktool/tests/test_cli_integration.py tools/tasktool/tests/test_migrate_cli.py -v` -> `36 passed`.

## S1.F1

Status: fixed.

Evidence:
- Commit: `X12: resolve post-slice review findings`.
- Files: `tools/tasktool/cli.py`, `tools/tasktool/tests/test_cli_integration.py`.
- GREEN: `PYTHONPATH=tools pytest tools/tasktool/tests/ -q` -> `310 passed`.
- GREEN: `PYTHONPATH=tools pytest tools/tasktool/tests/test_cli_integration.py tools/tasktool/tests/test_migrate_cli.py -v` -> `36 passed`.

## S1.F2

Status: fixed.

Evidence:
- Commit: `X12: resolve post-slice review findings`.
- Files: `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md`.
- Change: plan checklist checkboxes are marked complete, and the evidence section records RED/GREEN test results plus routed lifecycle state.
- GREEN: `./tools/tasktool/tasktool validate` -> `ok`.

## S1.F3

Status: documented as routed-state evidence; no code change needed in this slice.

Evidence:
- Commit: `X12: resolve post-slice review findings`.
- Files: `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md`, this resolution file.
- Authoritative checkout command: `/home/simon/Dev/sigreer/skills/superstar ./tools/tasktool/tasktool show X12`.
- Result: `status: in_progress`, `started: 2026-05-20`.
- Explanation: stale review-context `docs/tasklist.json` is a workflow context hole for reviewers, not an implementation worktree file to hand-edit. The plan now calls out that routed lifecycle state lives in the authoritative checkout.

## S1.F4

Status: fixed.

Evidence:
- Commit: `X12: resolve post-slice review findings`.
- Files: `tools/tasktool/commands.py`, `tools/tasktool/tests/test_migrate_cli.py`.
- Change: `--accept-authoritative` uses the lock path and exits with a no-write summary.
- RED: held-lock regression failed before the fix because the command returned 0 without acquiring the lock.
- GREEN: targeted regression command -> `3 passed`.


## Changes since prior round

Worktree status: clean

### git diff base..HEAD

diff --git a/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md b/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md
index 9361dd3..ad540a2 100644
--- a/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md
+++ b/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md
@@ -10,13 +10,13 @@
 
 **Spec:** `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md`
 
-**Tasktool row:** X12 (cross-cutting). Confirmed via `tasktool show X12` (status=ready, refs spec).
+**Tasktool row:** X12 (cross-cutting). Current lifecycle state is routed through the authoritative checkout at `/home/simon/Dev/sigreer/skills/superstar`; `./tools/tasktool/tasktool show X12` there reports `status: in_progress`, `started: 2026-05-20`, with refs to this spec and plan. The implementation worktree's checked-out `docs/tasklist.json` can be stale by design and is not the lifecycle source of truth for this routed slice.
 
 ---
 
 ## Lifecycle start
 
-- [ ] **Step 0: Mark X12 in progress**
+- [x] **Step 0: Mark X12 in progress**
 
 ```bash
 ./tools/tasktool/tasktool start X12
@@ -24,6 +24,8 @@
 
 Expected: exit 0; `tasktool show X12` reports `status: in_progress` with a `started:` date.
 
+Evidence: verified from the authoritative checkout with `./tools/tasktool/tasktool show X12`: status `in_progress`, started `2026-05-20`.
+
 ---
 
 ## File structure
@@ -53,7 +55,7 @@ Files modified in this slice:
 - Modify: `tools/tasktool/config.py`
 - Modify: `tools/tasktool/tests/test_authority_config.py`
 
-- [ ] **Step 1: Add the failing test for the sentinel**
+- [x] **Step 1: Add the failing test for the sentinel**
 
 Edit `tools/tasktool/tests/test_authority_config.py`. Replace the existing `test_missing_config_defaults_to_local` function with:
 
@@ -108,7 +110,7 @@ from tasktool.config import (
 )
 ```
 
-- [ ] **Step 2: Run the test to verify it fails**
+- [x] **Step 2: Run the test to verify it fails**
 
 ```bash
 PYTHONPATH=tools pytest tools/tasktool/tests/test_authority_config.py -v
@@ -116,7 +118,7 @@ PYTHONPATH=tools pytest tools/tasktool/tests/test_authority_config.py -v
 
 Expected: ImportError or `mutation_mode == "local"` assertion failure (the sentinel and predicate don't exist yet).
 
-- [ ] **Step 3: Add the sentinel + predicate to config.py**
+- [x] **Step 3: Add the sentinel + predicate to config.py**
 
 Edit `tools/tasktool/config.py`. Replace the existing module body with:
 
@@ -196,7 +198,7 @@ def is_authoritative_required(cfg: TasktoolConfig) -> bool:
     return cfg.tasklist.mutation_mode == UNCONFIGURED
 ```
 
-- [ ] **Step 4: Run tests, expect pass**
+- [x] **Step 4: Run tests, expect pass**
 
 ```bash
 PYTHONPATH=tools pytest tools/tasktool/tests/test_authority_config.py -v
@@ -204,7 +206,7 @@ PYTHONPATH=tools pytest tools/tasktool/tests/test_authority_config.py -v
 
 Expected: 4 passed (the three new tests plus the existing `test_round_trip_authoritative_config` and `test_invalid_mode_raises`, minus the deleted `test_missing_config_defaults_to_local`).
 
-- [ ] **Step 5: Commit**
+- [x] **Step 5: Commit**
 
 ```bash
 git add tools/tasktool/config.py tools/tasktool/tests/test_authority_config.py
@@ -219,7 +221,7 @@ git commit -m "X12: distinguish unconfigured tasktool config from explicit local
 - Modify: `tools/tasktool/commands.py`
 - Create: `tools/tasktool/tests/test_unconfigured_mutation.py`
 
-- [ ] **Step 1: Write the failing test**
+- [x] **Step 1: Write the failing test**
 
 Create `tools/tasktool/tests/test_unconfigured_mutation.py`:
 
@@ -376,7 +378,7 @@ def test_bootstrap_init_before_init_authority_fails(tmp_path):
 
 (The `init-local` part of `test_explicit_local_mode_still_mutates` is forward-referenced; it will pass after Task 3.)
 
-- [ ] **Step 2: Run the test, expect mutation tests to fail with the hard-error message NOT present**
+- [x] **Step 2: Run the test, expect mutation tests to fail with the hard-error message NOT present**
 
 ```bash
 PYTHONPATH=tools pytest tools/tasktool/tests/test_unconfigured_mutation.py -v
@@ -384,7 +386,7 @@ PYTHONPATH=tools pytest tools/tasktool/tests/test_unconfigured_mutation.py -v
 
 Expected: `test_init_errors_without_authority_config`, `test_start_errors_without_authority_config`, `test_validate_normalise_errors_unconfigured` fail (mutations currently succeed). Read-only tests pass. `test_explicit_local_mode_still_mutates` fails on the `config init-local` line (subcommand doesn't exist yet).
 
-- [ ] **Step 3: Add the hard-error path in `_resolve_write_root`**
+- [x] **Step 3: Add the hard-error path in `_resolve_write_root`**
 
 In `tools/tasktool/commands.py`, update the imports near the top of the file to add `is_authoritative_required`:
 
@@ -433,7 +435,7 @@ def _resolve_write_root(repo_root: Path) -> tuple[Path, bool, str, str]:
     )
 ```
 
-- [ ] **Step 4: Run the tests again**
+- [x] **Step 4: Run the tests again**
 
 ```bash
 PYTHONPATH=tools pytest tools/tasktool/tests/test_unconfigured_mutation.py -v
@@ -441,7 +443,7 @@ PYTHONPATH=tools pytest tools/tasktool/tests/test_unconfigured_mutation.py -v
 
 Expected: every test except `test_explicit_local_mode_still_mutates` passes. The latter still fails on `config init-local` (forward-referenced to Task 3).
 
-- [ ] **Step 5: Run the full tasktool suite to surface regressions**
+- [x] **Step 5: Run the full tasktool suite to surface regressions**
 
 ```bash
 PYTHONPATH=tools pytest tools/tasktool/tests/ -v
@@ -449,7 +451,7 @@ PYTHONPATH=tools pytest tools/tasktool/tests/ -v
 
 Expected: failures in any test that called `tasktool init` / `tasktool start` etc. against a fresh `tmp_path` without first configuring authority. Capture the list — those tests get explicit `config init-local` or `config init-authority` setup in Task 6.
 
-- [ ] **Step 6: Commit**
+- [x] **Step 6: Commit**
 
 ```bash
 git add tools/tasktool/commands.py tools/tasktool/tests/test_unconfigured_mutation.py
@@ -465,7 +467,7 @@ git commit -m "X12: refuse mutations when tasktool authority routing is unconfig
 - Modify: `tools/tasktool/cli.py`
 - Create: `tools/tasktool/tests/test_init_local.py`
 
-- [ ] **Step 1: Write the failing test**
+- [x] **Step 1: Write the failing test**
 
 Create `tools/tasktool/tests/test_init_local.py`:
 
@@ -525,7 +527,7 @@ def test_init_local_refuses_overwriting_authoritative(tmp_path):
     assert "already configured" in r.stderr or "already configured" in r.stdout
 ```
 
-- [ ] **Step 2: Run the test, expect failure**
+- [x] **Step 2: Run the test, expect failure**
 
 ```bash
 PYTHONPATH=tools pytest tools/tasktool/tests/test_init_local.py -v
@@ -533,7 +535,7 @@ PYTHONPATH=tools pytest tools/tasktool/tests/test_init_local.py -v
 
 Expected: argparse-level failures (`invalid choice: 'init-local'`).
 
-- [ ] **Step 3: Add `cmd_config_init_local` to commands.py**
+- [x] **Step 3: Add `cmd_config_init_local` to commands.py**
 
 In `tools/tasktool/commands.py`, immediately after `cmd_config_init_authority`, add:
 
@@ -572,7 +574,7 @@ def cmd_config_init_local(*, repo_root: Path) -> None:
 
 Ensure `json` is imported at the top of `commands.py` (it already is — check the existing import block).
 
-- [ ] **Step 4: Register the subcommand in cli.py**
+- [x] **Step 4: Register the subcommand in cli.py**
 
 In `tools/tasktool/cli.py`, immediately after the `init-authority` parser registration (around line 29-30), add:
 
@@ -588,7 +590,7 @@ In the dispatch block where `config_cmd == "init-authority"` is handled (around
                 commands.cmd_config_init_local(repo_root=repo_root)
 ```
 
-- [ ] **Step 5: Run the test, expect pass**
+- [x] **Step 5: Run the test, expect pass**
 
 ```bash
 PYTHONPATH=tools pytest tools/tasktool/tests/test_init_local.py tools/tasktool/tests/test_unconfigured_mutation.py -v
@@ -596,7 +598,7 @@ PYTHONPATH=tools pytest tools/tasktool/tests/test_init_local.py tools/tasktool/t
 
 Expected: both files pass in full now.
 
-- [ ] **Step 6: Commit**
+- [x] **Step 6: Commit**
 
 ```bash
 git add tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/tests/test_init_local.py
@@ -611,7 +613,7 @@ git commit -m "X12: add tasktool config init-local for auditable local-mode opt-
 - Create: `tools/tasktool/migrate.py`
 - Create: `tools/tasktool/tests/test_migrate.py`
 
-- [ ] **Step 1: Write the failing test for the diff walker**
+- [x] **Step 1: Write the failing test for the diff walker**
 
 Create `tools/tasktool/tests/test_migrate.py`:
 
@@ -890,7 +892,7 @@ def test_per_field_migration_acceptance(row_type):
         )
 ```
 
-- [ ] **Step 2: Run, expect ImportError**
+- [x] **Step 2: Run, expect ImportError**
 
 ```bash
 PYTHONPATH=tools pytest tools/tasktool/tests/test_migrate.py -v
@@ -898,7 +900,7 @@ PYTHONPATH=tools pytest tools/tasktool/tests/test_migrate.py -v
 
 Expected: `ModuleNotFoundError: No module named 'tasktool.migrate'`.
 
-- [ ] **Step 3: Implement the migrator**
+- [x] **Step 3: Implement the migrator**
 
 Create `tools/tasktool/migrate.py`:
 
@@ -1178,7 +1180,7 @@ def _fmt_value(v: object) -> str:
     return repr(v)
 ```
 
-- [ ] **Step 4: Run the migrate tests, expect pass**
+- [x] **Step 4: Run the migrate tests, expect pass**
 
 ```bash
 PYTHONPATH=tools pytest tools/tasktool/tests/test_migrate.py -v
@@ -1186,7 +1188,7 @@ PYTHONPATH=tools pytest tools/tasktool/tests/test_migrate.py -v
 
 Expected: all tests pass, including the row-type-parametrized full-field migration acceptance test that loops over every supported dataclass field. Pytest reports six parametrized cases for that test (one per row dataclass); per-field assertions run inside each case.
 
-- [ ] **Step 5: Commit**
+- [x] **Step 5: Commit**
 
 ```bash
 git add tools/tasktool/migrate.py tools/tasktool/tests/test_migrate.py
@@ -1202,7 +1204,7 @@ git commit -m "X12: add dataclass-driven migrator for tasktool drift reconciliat
 - Modify: `tools/tasktool/cli.py`
 - Create: `tools/tasktool/tests/test_migrate_cli.py`
 
-- [ ] **Step 1: Write the failing CLI integration test**
+- [x] **Step 1: Write the failing CLI integration test**
 
 Create `tools/tasktool/tests/test_migrate_cli.py`:
 
@@ -1519,7 +1521,7 @@ def test_migrate_emits_notify_events_for_task_transitions(tmp_path):
     assert task_events, f"no notify event found for task status change. events={events}"
 ```
 
-- [ ] **Step 2: Run, expect failure**
+- [x] **Step 2: Run, expect failure**
 
 ```bash
 PYTHONPATH=tools pytest tools/tasktool/tests/test_migrate_cli.py -v
@@ -1527,7 +1529,7 @@ PYTHONPATH=tools pytest tools/tasktool/tests/test_migrate_cli.py -v
 
 Expected: `argparse` errors (`invalid choice: 'migrate-from-local'`).
 
-- [ ] **Step 3: Add the command body**
+- [x] **Step 3: Add the command body**
 
 Before writing the body, make `same_repository` available — `commands.py` currently imports selected names from `tasktool.worktree` but not this one. Update the existing import block at the top of `tools/tasktool/commands.py` to add `same_repository`:
 
@@ -1726,7 +1728,7 @@ def _notify_status_transitions(local: "Project", pre_merge_authoritative: "Proje
 
 `load_project` is already imported at the top of `commands.py` — no new import needed.
 
-- [ ] **Step 4: Register CLI subparser**
+- [x] **Step 4: Register CLI subparser**
 
 In `tools/tasktool/cli.py`, after the `init-local` registration (added in Task 3), add:
 
@@ -1757,7 +1759,7 @@ In the dispatch block, immediately after the `init-local` branch:
                 )
 ```
 
-- [ ] **Step 5: Run the CLI test, expect pass**
+- [x] **Step 5: Run the CLI test, expect pass**
 
 ```bash
 PYTHONPATH=tools pytest tools/tasktool/tests/test_migrate_cli.py -v
@@ -1765,7 +1767,7 @@ PYTHONPATH=tools pytest tools/tasktool/tests/test_migrate_cli.py -v
 
 Expected: all 7 tests pass.
 
-- [ ] **Step 6: Commit**
+- [x] **Step 6: Commit**
 
 ```bash
 git add tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/tests/test_migrate_cli.py
@@ -1782,7 +1784,7 @@ git commit -m "X12: add tasktool config migrate-from-local subcommand"
 - Modify: `skills/tasklist-discipline/SKILL.md`
 - Modify: `skills/using-git-worktrees/SKILL.md`
 
-- [ ] **Step 1: Run the full tasktool suite**
+- [x] **Step 1: Run the full tasktool suite**
 
 ```bash
 PYTHONPATH=tools pytest tools/tasktool/tests/ -v 2>&1 | tee /tmp/x12-test-output.txt
@@ -1792,7 +1794,7 @@ Capture failing tests. Each likely failure is one of:
 1. A test that calls `tasktool init` (or any mutating command) against `tmp_path` without first running `config init-local` or `config init-authority`.
 2. A test that asserts behaviour that depended on the implicit-`local` default.
 
-- [ ] **Step 2: Repair each failing test by adding explicit `init-local`**
+- [x] **Step 2: Repair each failing test by adding explicit `init-local`**
 
 For each failing test that depended on implicit-`local`, prepend a `tasktool config init-local` invocation. Example pattern (apply to each occurrence):
 
@@ -1816,7 +1818,7 @@ def test_foo(tmp_path):
 
 For tests that specifically exercise the *authoritative* path, replace with `config init-authority --branch main`.
 
-- [ ] **Step 3: Re-run, expect green**
+- [x] **Step 3: Re-run, expect green**
 
 ```bash
 PYTHONPATH=tools pytest tools/tasktool/tests/ -v
@@ -1824,7 +1826,7 @@ PYTHONPATH=tools pytest tools/tasktool/tests/ -v
 
 Expected: full suite passes.
 
-- [ ] **Step 4: Update `skills/project-setup/SKILL.md`**
+- [x] **Step 4: Update `skills/project-setup/SKILL.md`**
 
 Locate the section in `skills/project-setup/SKILL.md` that describes tasktool bootstrap (search for `tasktool init`). Replace it with the new ordered sequence:
 
@@ -1848,7 +1850,7 @@ Locate the section in `skills/project-setup/SKILL.md` that describes tasktool bo
 If a repo opts out of authoritative routing on purpose (no worktree convention, single-checkout workflows), the operator may run `tasktool config init-local` instead of `init-authority`. The opt-out should be a deliberate, committed choice — never the implicit default.
 ```
 
-- [ ] **Step 5: Update `skills/tasklist-discipline/SKILL.md`**
+- [x] **Step 5: Update `skills/tasklist-discipline/SKILL.md`**
 
 Find the existing paragraph that opens "When `.tasktool/config.json` sets `tasklist.mutation_mode` to `authoritative-checkout`…" (around line 12). Replace it with:
 
@@ -1858,7 +1860,7 @@ Tasktool requires authoritative-checkout routing for any mutating command. When
 If a mutation errors with `no authoritative-checkout routing configured`, run `tasktool config init-authority --branch <branch>` from the target branch (or, for an audited single-checkout workflow, `tasktool config init-local`). To reconcile a tasklist that drifted under the previous default — i.e. a worktree's `docs/tasklist.json` that was mutated without routing — run `tasktool config migrate-from-local --authority-root <path> --accept-local` from the drifted worktree.
 ```
 
-- [ ] **Step 6: Update `skills/using-git-worktrees/SKILL.md`**
+- [x] **Step 6: Update `skills/using-git-worktrees/SKILL.md`**
 
 Find the line that begins "If tasktool authoritative-checkout routing is configured" (around line 16). Replace it with:
 
@@ -1866,7 +1868,7 @@ Find the line that begins "If tasktool authoritative-checkout routing is configu
 Tasktool mutations from worktrees always route through the configured authoritative checkout. If `.tasktool/config.json` is missing in a repo you intend to work in, set it up first via `tasktool config init-authority --branch <branch>` from the target branch. Once routing is configured, mutations may be invoked from the implementation worktree: stay put, do not leave the worktree to hand-edit the authoritative checkout or run lifecycle commands elsewhere; run `tasktool start`, `tasktool ref`, `tasktool note`, and `tasktool close` from the active implementation worktree and let routing write through the configured authority.
 ```
 
-- [ ] **Step 7: Skim-test the skill text**
+- [x] **Step 7: Skim-test the skill text**
 
 ```bash
 grep -n "mutation_mode\|authoritative\|migrate-from-local" skills/project-setup/SKILL.md skills/tasklist-discipline/SKILL.md skills/using-git-worktrees/SKILL.md
@@ -1874,7 +1876,7 @@ grep -n "mutation_mode\|authoritative\|migrate-from-local" skills/project-setup/
 
 Confirm: no remaining "when configured" / conditional phrasing for the rule itself; `migrate-from-local` mentioned at least once for the remediation path.
 
-- [ ] **Step 8: Commit**
+- [x] **Step 8: Commit**
 
 ```bash
 git add tools/tasktool/tests/ skills/project-setup/SKILL.md skills/tasklist-discipline/SKILL.md skills/using-git-worktrees/SKILL.md
@@ -1885,7 +1887,7 @@ git commit -m "X12: tighten tasktool skills to require authoritative routing"
 
 ## Task 7: Close X12 and prepare for review
 
-- [ ] **Step 1: Run the full suite once more**
+- [x] **Step 1: Run the full suite once more**
 
 ```bash
 PYTHONPATH=tools pytest tools/tasktool/tests/ -v
@@ -1893,11 +1895,11 @@ PYTHONPATH=tools pytest tools/tasktool/tests/ -v
 
 Expected: all tests pass.
 
-- [ ] **Step 2: Mark X12 review-ready**
+- [x] **Step 2: Mark X12 review-ready**
 
 The cross-cutting item moves to status `done` only after external `post-slice` review (next step in execution). Leave it `in_progress` here; closure happens via `tasktool close X12` after the post-slice review verdict.
 
-- [ ] **Step 3: Capture evidence for the post-slice review**
+- [x] **Step 3: Capture evidence for the post-slice review**
 
 Note for the post-slice reviewer:
 - Spec: `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md`
@@ -1905,6 +1907,13 @@ Note for the post-slice reviewer:
 - Spec reviewer chain: `docs/reviewer/x12-tasktool-require-authoritative-routing-design-spec/`
 - Implementation evidence: commits `X12: *` on this branch.
 
+Post-slice resolution evidence, 2026-05-20:
+- RED: `PYTHONPATH=tools pytest tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_ignores_ambient_ancestor_git_repo tools/tasktool/tests/test_migrate_cli.py::test_accept_authoritative_is_noop tools/tasktool/tests/test_migrate_cli.py::test_accept_authoritative_acquires_authority_lock -q` failed with 3 expected failures before the fix.
+- GREEN: the same targeted regression command passed with `3 passed`.
+- GREEN: `PYTHONPATH=tools pytest tools/tasktool/tests/test_cli_integration.py tools/tasktool/tests/test_migrate_cli.py -v` passed with `36 passed`.
+- GREEN: `PYTHONPATH=tools pytest tools/tasktool/tests/ -q` passed with `310 passed`.
+- Authority state: `/home/simon/Dev/sigreer/skills/superstar ./tools/tasktool/tasktool show X12` reports `status: in_progress`, `started: 2026-05-20`; routed lifecycle state lives there, not in this worktree's stale review-context tasklist.
+
 ---
 
 ## Out of scope
diff --git a/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/.reviewer-output/r1-primary/last-message.md b/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/.reviewer-output/r1-primary/last-message.md
new file mode 100644
index 0000000..b705be6
--- /dev/null
+++ b/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/.reviewer-output/r1-primary/last-message.md
@@ -0,0 +1,33 @@
+1. Findings
+
+F1 - Severity: blocking  
+`PYTHONPATH=tools pytest tools/tasktool/tests/ -q` fails: `tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_writes_project_config` expects `.tasktool/config.json` under the test `cwd`, but it is not written there. This violates the plan’s final gate at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888-1894`. The likely trigger is `_find_repo_root()` selecting an ancestor with `.git` at `tools/tasktool/cli.py:8-12`; in this review environment `/tmp/.git` exists, so the config is written to `/tmp/.tasktool/config.json` instead of the test tmpdir. Test expectation is at `tools/tasktool/tests/test_cli_integration.py:380-388`.
+
+F2 - Severity: blocking  
+X12 is not lifecycle-started for a post-slice gate. `docs/tasklist.json:176-185` still has `started: null` and `status: ready`, while the plan explicitly requires `tasktool start X12` at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:19-25` and later says to leave the row `in_progress` before post-slice review at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1896-1898`. `./tools/tasktool/tasktool show X12` confirms `status: ready`.
+
+F3 - Severity: important  
+`config migrate-from-local --accept-authoritative` returns before the lock/re-read/exit-summary path. `tools/tasktool/commands.py:289-290` exits immediately after printing the initial diff. The spec requires acquiring `tasktool_lock`, re-reading authoritative state inside the lock, and printing a one-line summary at `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md:107-109`. This leaves the verification-mode semantics weaker than specified and untested for concurrent/stale authoritative state.
+
+2. Open questions / assumptions
+
+Was the full tasktool suite previously run in an environment without `/tmp/.git`? If so, that evidence is environment-sensitive and should not be used as the only closeout proof.
+
+3. Suggested document edits
+
+Update the plan/evidence section to record the actual verification command output, including the failing test if this review result is accepted. Do not mark X12 close-ready until the task row is moved to `in_progress` and the suite is green.
+
+4. Verification gaps / commands that should be run
+
+Run:
+
+```bash
+PYTHONPATH=tools pytest tools/tasktool/tests/ -q
+./tools/tasktool/tasktool show X12
+./tools/tasktool/tasktool validate
+```
+
+I ran those here: `validate` passes, but the full tasktool suite fails as described above, and X12 remains `ready`.
+
+Overall verdict: revise
+
diff --git a/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/.reviewer-output/r1-sweep1/last-message.md b/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/.reviewer-output/r1-sweep1/last-message.md
new file mode 100644
index 0000000..ab68d50
--- /dev/null
+++ b/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/.reviewer-output/r1-sweep1/last-message.md
@@ -0,0 +1,29 @@
+1. Findings
+
+F1 Severity: blocking — The required final verification gate is failing. The plan requires `PYTHONPATH=tools pytest tools/tasktool/tests/ -v` to pass at [docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888), but I ran it and got `1 failed, 307 passed`. The failure is `tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_writes_project_config`: the command exits 0, but `.tasktool/config.json` is not written under `tmp_path`, causing the read at [tools/tasktool/tests/test_cli_integration.py:387](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/tools/tasktool/tests/test_cli_integration.py:387) to raise `FileNotFoundError`. This blocks post-slice readiness.
+
+F2 Severity: important — The plan/checklist evidence was not updated, so the target document still presents the slice as unexecuted. Every implementation step remains unchecked, including lifecycle start at [docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:19](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:19) and final verification at [docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888). For a completion gate, this makes it ambiguous which steps were actually performed and which evidence is current.
+
+F3 Severity: important — The review-context task row in this worktree still says X12 is `ready` with `started: null` at [docs/tasklist.json:175](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/docs/tasklist.json:175). The authoritative checkout does show X12 as `in_progress`, but that mutation is staged/uncommitted in `/home/simon/Dev/sigreer/skills/superstar`. The prompt’s context file therefore contradicts the plan’s expected post-implementation state at [docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1896](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1896). Either the reviewer context needs to use the authoritative tasklist, or the completion evidence needs to call out that routed tasklist state lives outside the implementation branch.
+
+F4 Severity: minor — `--accept-authoritative` does not acquire the lock even though the spec/test plan calls it a locked verification path. The implementation returns immediately at [tools/tasktool/commands.py:289](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/tools/tasktool/commands.py:289), before the `tasktool_lock(authority)` block at [tools/tasktool/commands.py:295](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority/tools/tasktool/commands.py:295). The plan/spec acceptance says this mode “acquires the lock, writes nothing” in the testing section, so either the implementation or the acceptance text should be corrected.
+
+2. Open questions / assumptions
+
+I treated the failing full-suite command as authoritative because it is the exact final verification command named by the plan. The failure may be sensitive to the current `/tmp/.git` ancestor in this environment, but that still means the repo’s own suite does not currently pass under the requested gate.
+
+3. Suggested document edits
+
+Update the plan checklist to reflect actual completed steps and attach the final verification result only after the suite is green.
+
+Clarify tasklist evidence for routed lifecycle mutations: reviewers should know whether to inspect the implementation worktree’s `docs/tasklist.json` or the authoritative checkout’s tasklist.
+
+If `--accept-authoritative` intentionally does not lock, update the spec/plan test expectation to stop claiming that it does.
+
+4. Verification gaps / commands that should be run
+
+`PYTHONPATH=tools pytest tools/tasktool/tests/ -v` currently fails and must be rerun after fixing `test_config_init_authority_writes_project_config`.
+
+After the suite is green, rerun `git status --short` in both the implementation worktree and the authoritative checkout to make sure only intended review/tasklist artifacts remain dirty.
+
+Overall verdict: revise
\ No newline at end of file
diff --git a/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/chain.json b/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/chain.json
new file mode 100644
index 0000000..9a54db2
--- /dev/null
+++ b/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/chain.json
@@ -0,0 +1,76 @@
+{
+  "schema_version": 1,
+  "chain": "x12-tasktool-require-authoritative-routing-X12-post-slice",
+  "kind": "post-slice",
+  "target": "docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md",
+  "work_id": "X12",
+  "legacy_migrated": false,
+  "rounds": [
+    {
+      "round": 1,
+      "reviewers": [
+        {
+          "role": "primary",
+          "sweep_group": null,
+          "parent_round": 1,
+          "request": "r1-2026-05-20T1509-primary-request.md",
+          "response": "r1-2026-05-20T1509-primary-response.md",
+          "verdict": "revise",
+          "verdict_valid": true,
+          "returncode": 0,
+          "status": "ok",
+          "provider": "codex",
+          "caller_provider": "codex",
+          "sandbox": {
+            "repo_root": "/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority",
+            "scratch_dir": "/tmp/superstar-reviewer-x12-tasktool-require-authoritative-routing-X12-post-slice-r1-primary-lekbney3",
+            "response_dir": "docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/.reviewer-output/r1-primary",
+            "mode": "workspace-write-with-read-access"
+          }
+        },
+        {
+          "role": "sweep",
+          "sweep_group": 1,
+          "parent_round": 1,
+          "request": "r1-2026-05-20T1509-sweep1-request.md",
+          "response": "r1-2026-05-20T1509-sweep1-response.md",
+          "verdict": "revise",
+          "verdict_valid": true,
+          "returncode": 0,
+          "status": "ok",
+          "provider": "codex",
+          "caller_provider": "codex",
+          "sandbox": {
+            "repo_root": "/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority",
+            "scratch_dir": "/tmp/superstar-reviewer-x12-tasktool-require-authoritative-routing-X12-post-slice-r1-sweep1-840qft3g",
+            "response_dir": "docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/.reviewer-output/r1-sweep1",
+            "mode": "workspace-write-with-read-access"
+          }
+        }
+      ],
+      "status": "ok",
+      "returncode": 0,
+      "merged_verdict": "revise",
+      "merged_findings": "r1-merged-findings.md",
+      "request": "r1-2026-05-20T1509-primary-request.md",
+      "response": "r1-2026-05-20T1509-primary-response.md",
+      "resolution": null,
+      "resolution_parse_status": null,
+      "resolution_waiver": false,
+      "head_sha_at_request": "f966d23316b7254dca58b8c9610960449f143c03",
+      "head_sha_after_round": "f966d23316b7254dca58b8c9610960449f143c03",
+      "worktree_dirty_at_request": true,
+      "verdict": "revise",
+      "verdict_valid": true,
+      "findings_count": 3,
+      "blocking_findings_count": 2,
+      "base_ref": null,
+      "base_ref_source": null,
+      "diff_included": false
+    }
+  ],
+  "sweep_checkpoints": {
+    "first-round": "completed",
+    "final-ready": "pending"
+  }
+}
diff --git a/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/r1-2026-05-20T1509-primary-request.md b/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/r1-2026-05-20T1509-primary-request.md
new file mode 100644
index 0000000..4ca7ae0
--- /dev/null
+++ b/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/r1-2026-05-20T1509-primary-request.md
@@ -0,0 +1,1072 @@
+<!-- superstar-prompt:start -->
+You are acting as an independent senior engineering reviewer.
+
+Review stance:
+- Lead with findings, ordered by severity.
+- Focus on correctness, consistency, implementation risk, missing acceptance
+  gates, vague handoffs, ungrounded assumptions, unverified claims, and drift
+  from the codebase.
+- Give exact file/line references when possible.
+- If the document is sound, say that clearly and list residual risks.
+- Keep the review actionable. Avoid broad rewrites unless the current structure
+  creates concrete risk.
+
+Repository root:
+/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority
+
+Target kind:
+post-slice
+
+Review mode:
+Post-slice review. Treat this as a completion gate for one
+slice of work. Compare the completed changes and stated evidence against the
+slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
+untracked artifacts, missing tests, failing or skipped verification, broken
+cross-site behavior, and claims not supported by the repo state.
+
+Target document:
+docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md
+
+Additional context files:
+- docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md
+- docs/tasklist.json
+
+Review output contract:
+1. Findings
+   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
+     stable if this review is iterated in subsequent rounds.
+   - Mark severity inline: `Severity: blocking | important | minor | nit`.
+2. Open questions / assumptions
+3. Suggested document edits
+4. Verification gaps / commands that should be run, if any
+
+End your review with this exact line, as plain text on its own line:
+
+    Overall verdict: <ready|ready with small edits|revise>
+
+Do not bold, italicise, prefix with `##`, split across lines, or drop the
+word "Overall". Do not write `**Verdict: ready**` or place the value on a
+new line after a heading.
+
+Read the files from disk. Do not rely only on the snippets in this prompt.
+
+
+## Target Preview
+
+### docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md
+
+    1	# X12 — tasktool: require authoritative-checkout routing for mutations — Implementation Plan
+    2	
+    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
+    4	
+    5	**Goal:** Make authoritative-checkout routing structurally required for mutating tasktool commands so the AGS sidebar widget, TTS announcements, and on-disk source-of-truth cannot diverge silently; add a `migrate-from-local` subcommand for reconciling drift, and an `init-local` subcommand for the explicit opt-out.
+    6	
+    7	**Architecture:** Three production-code changes in `tools/tasktool/`: (1) `config.py` gains a `MutationModeUnconfigured` sentinel so `load_config` distinguishes "no config file" from "config says local"; (2) `commands.py:_resolve_write_root` raises `CommandError` on the mutation path when unconfigured, and gains `cmd_config_init_local` + `cmd_config_migrate_from_local`; (3) `cli.py` registers two new `config` subcommands. The migrator walks `dataclasses.fields()` on every row type in `tools/tasktool/model.py` so adding fields to the model cannot silently drop them from migration. Three skills under `skills/` are tightened from conditional to required wording.
+    8	
+    9	**Tech Stack:** Python 3.11 (slots dataclasses, `dataclasses.fields()` introspection), pytest, existing `tasktool_lock` and `validate_authoritative_checkout` helpers in `tools/tasktool/worktree.py`.
+   10	
+   11	**Spec:** `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md`
+   12	
+   13	**Tasktool row:** X12 (cross-cutting). Confirmed via `tasktool show X12` (status=ready, refs spec).
+   14	
+   15	---
+   16	
+   17	## Lifecycle start
+   18	
+   19	- [ ] **Step 0: Mark X12 in progress**
+   20	
+   21	```bash
+   22	./tools/tasktool/tasktool start X12
+   23	```
+   24	
+   25	Expected: exit 0; `tasktool show X12` reports `status: in_progress` with a `started:` date.
+   26	
+   27	---
+   28	
+   29	## File structure
+   30	
+   31	Files created in this slice:
+   32	- `tools/tasktool/migrate.py` — pure-Python diff/merge over the model dataclass tree. New module so `commands.py` stays focused on CLI command bodies and the migrator's row-walking logic has its own home.
+   33	- `tools/tasktool/tests/test_migrate.py` — unit tests for the migrator (diff, dataclass coverage, conflict handling).
+   34	- `tools/tasktool/tests/test_unconfigured_mutation.py` — tests for the hard-error behaviour.
+   35	- `tools/tasktool/tests/test_init_local.py` — tests for the `init-local` CLI subcommand.
+   36	- `tools/tasktool/tests/test_migrate_cli.py` — CLI integration tests for `config migrate-from-local`.
+   37	
+   38	Files modified in this slice:
+   39	- `tools/tasktool/config.py` — new sentinel and `is_authoritative_required` predicate; `load_config` returns sentinel when no file.
+   40	- `tools/tasktool/commands.py` — `_resolve_write_root` hard-error path; new `cmd_config_init_local` and `cmd_config_migrate_from_local`.
+   41	- `tools/tasktool/cli.py` — register `config init-local` and `config migrate-from-local` subparsers.
+   42	- `tools/tasktool/tests/test_authority_config.py` — replace `test_missing_config_defaults_to_local` (no longer true) with `test_missing_config_returns_unconfigured`.
+   43	- `tools/tasktool/tests/test_cli_integration.py` — any existing tests that relied on the implicit-`local` default get an explicit `init-local` or `init-authority` setup line.
+   44	- `skills/project-setup/SKILL.md` — order change + setup-precondition for missing authority config.
+   45	- `skills/tasklist-discipline/SKILL.md` — promote routing from optional to required; add remediation pointer.
+   46	- `skills/using-git-worktrees/SKILL.md` — remove "if configured" conditional.
+   47	
+   48	---
+   49	
+   50	## Task 1: Distinguish "unconfigured" from "explicit local" in config.py
+   51	
+   52	**Files:**
+   53	- Modify: `tools/tasktool/config.py`
+   54	- Modify: `tools/tasktool/tests/test_authority_config.py`
+   55	
+   56	- [ ] **Step 1: Add the failing test for the sentinel**
+   57	
+   58	Edit `tools/tasktool/tests/test_authority_config.py`. Replace the existing `test_missing_config_defaults_to_local` function with:
+   59	
+   60	```python
+   61	def test_missing_config_returns_unconfigured(tmp_path):
+   62	    cfg = load_config(tmp_path)
+   63	    assert cfg.tasklist.mutation_mode == "unconfigured"
+   64	    assert is_authoritative_required(cfg) is True
+   65	
+   66	
+   67	def test_explicit_local_is_configured(tmp_path):
+   68	    (tmp_path / ".tasktool").mkdir()
+   69	    (tmp_path / ".tasktool" / "config.json").write_text(
+   70	        '{"schema_version":1,"tasklist":{"mutation_mode":"local","authoritative_branch":"main"}}'
+   71	    )
+   72	    cfg = load_config(tmp_path)
+   73	    assert cfg.tasklist.mutation_mode == "local"
+   74	    assert is_authoritative_required(cfg) is False
+   75	
+   76	
+   77	def test_authoritative_mode_does_not_require_init(tmp_path):
+   78	    (tmp_path / ".tasktool").mkdir()
+   79	    (tmp_path / ".tasktool" / "config.json").write_text(
+   80	        '{"schema_version":1,"tasklist":{"mutation_mode":"authoritative-checkout","authoritative_branch":"main"}}'
+   81	    )
+   82	    cfg = load_config(tmp_path)
+   83	    assert is_authoritative_required(cfg) is False
+   84	
+   85	
+   86	def test_config_with_omitted_mutation_mode_is_unconfigured(tmp_path):
+   87	    """A config file present but lacking mutation_mode must NOT silently
+   88	    default to local. It is treated identically to a missing file."""
+   89	    (tmp_path / ".tasktool").mkdir()
+   90	    (tmp_path / ".tasktool" / "config.json").write_text(
+   91	        '{"schema_version":1,"tasklist":{}}'
+   92	    )
+   93	    cfg = load_config(tmp_path)
+   94	    assert cfg.tasklist.mutation_mode == "unconfigured"
+   95	    assert is_authoritative_required(cfg) is True
+   96	```
+   97	
+   98	Add `is_authoritative_required` to the import line:
+   99	
+  100	```python
+  101	from tasktool.config import (
+  102	    DEFAULT_CONFIG_REL,
+  103	    TasklistConfig,
+  104	    TasktoolConfig,
+  105	    is_authoritative_required,
+  106	    load_config,
+  107	    save_config,
+  108	)
+  109	```
+  110	
+  111	- [ ] **Step 2: Run the test to verify it fails**
+  112	
+  113	```bash
+  114	PYTHONPATH=tools pytest tools/tasktool/tests/test_authority_config.py -v
+  115	```
+  116	
+  117	Expected: ImportError or `mutation_mode == "local"` assertion failure (the sentinel and predicate don't exist yet).
+  118	
+  119	- [ ] **Step 3: Add the sentinel + predicate to config.py**
+  120	
+  121	Edit `tools/tasktool/config.py`. Replace the existing module body with:
+  122	
+  123	```python
+  124	from __future__ import annotations
+  125	
+  126	import json
+  127	from dataclasses import dataclass, field
+  128	from pathlib import Path
+  129	
+  130	DEFAULT_CONFIG_REL = Path(".tasktool/config.json")
+  131	
+  132	# Sentinel returned when no .tasktool/config.json exists. Distinguishes
+  133	# "operator never configured this repo" from "operator explicitly chose local".
+  134	UNCONFIGURED = "unconfigured"
+  135	
+  136	VALID_MUTATION_MODES = {"local", "authoritative-checkout"}
+  137	
+  138	
+  139	@dataclass(frozen=True)
+  140	class TasklistConfig:
+  141	    mutation_mode: str = UNCONFIGURED
+  142	    authoritative_branch: str = "main"
+  143	
+  144	
+  145	@dataclass(frozen=True)
+  146	class TasktoolConfig:
+  147	    schema_version: int = 1
+  148	    tasklist: TasklistConfig = field(default_factory=TasklistConfig)
+  149	
+  150	
+  151	def _parse_tasklist(raw: dict) -> TasklistConfig:
+  152	    if "mutation_mode" not in raw:
+  153	        # Config file exists but omits mutation_mode — treat as unconfigured,
+  154	        # the same way a missing config file is treated. Operators must opt in.
+  155	        return TasklistConfig(
+  156	            mutation_mode=UNCONFIGURED,
+  157	            authoritative_branch=raw.get("authoritative_branch", "main"),
+  158	        )
+  159	    mode = raw["mutation_mode"]
+  160	    if mode not in VALID_MUTATION_MODES:
+  161	        raise ValueError(f"unknown mutation_mode: {mode}")
+  162	    return TasklistConfig(
+  163	        mutation_mode=mode,
+  164	        authoritative_branch=raw.get("authoritative_branch", "main"),
+  165	    )
+  166	
+  167	
+  168	def load_config(repo_root: Path) -> TasktoolConfig:
+  169	    path = repo_root / DEFAULT_CONFIG_REL
+  170	    if not path.exists():
+  171	        return TasktoolConfig()  # default field gives UNCONFIGURED
+  172	    raw = json.loads(path.read_text(encoding="utf-8"))
+  173	    if raw.get("schema_version", 1) != 1:
+  174	        raise ValueError(f"unsupported tasktool config schema_version: {raw.get('schema_version')}")
+  175	    return TasktoolConfig(
+  176	        schema_version=1,
+  177	        tasklist=_parse_tasklist(raw.get("tasklist", {})),
+  178	    )
+  179	
+  180	
+  181	def save_config(repo_root: Path, cfg: TasktoolConfig) -> None:
+  182	    path = repo_root / DEFAULT_CONFIG_REL
+  183	    path.parent.mkdir(parents=True, exist_ok=True)
+  184	    body = {
+  185	        "schema_version": cfg.schema_version,
+  186	        "tasklist": {
+  187	            "mutation_mode": cfg.tasklist.mutation_mode,
+  188	            "authoritative_branch": cfg.tasklist.authoritative_branch,
+  189	        },
+  190	    }
+  191	    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
+  192	
+  193	
+  194	def is_authoritative_required(cfg: TasktoolConfig) -> bool:
+  195	    """True iff mutations should be refused for this config."""
+  196	    return cfg.tasklist.mutation_mode == UNCONFIGURED
+  197	```
+  198	
+  199	- [ ] **Step 4: Run tests, expect pass**
+  200	
+  201	```bash
+  202	PYTHONPATH=tools pytest tools/tasktool/tests/test_authority_config.py -v
+  203	```
+  204	
+  205	Expected: 4 passed (the three new tests plus the existing `test_round_trip_authoritative_config` and `test_invalid_mode_raises`, minus the deleted `test_missing_config_defaults_to_local`).
+  206	
+  207	- [ ] **Step 5: Commit**
+  208	
+  209	```bash
+  210	git add tools/tasktool/config.py tools/tasktool/tests/test_authority_config.py
+  211	git commit -m "X12: distinguish unconfigured tasktool config from explicit local mode"
+  212	```
+  213	
+  214	---
+  215	
+  216	## Task 2: Hard-error mutations when unconfigured
+  217	
+  218	**Files:**
+  219	- Modify: `tools/tasktool/commands.py`
+  220	- Create: `tools/tasktool/tests/test_unconfigured_mutation.py`
+  221	
+  222	- [ ] **Step 1: Write the failing test**
+  223	
+  224	Create `tools/tasktool/tests/test_unconfigured_mutation.py`:
+  225	
+  226	```python
+  227	from __future__ import annotations
+  228	
+  229	import subprocess
+  230	import sys
+  231	from pathlib import Path
+  232	
+  233	import pytest
+  234	
+  235	REPO_ROOT = Path(__file__).resolve().parents[3]
+  236	PKG_DIR = REPO_ROOT / "tools"
+  237	
+  238	
+  239	def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
+  240	    import os
+  241	    env = os.environ.copy()
+  242	    env["PYTHONPATH"] = str(PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")
+  243	    return subprocess.run(
+  244	        [sys.executable, "-m", "tasktool", *args],
+  245	        capture_output=True, text=True, cwd=cwd, env=env,
+  246	    )
+  247	
+  248	
+  249	def _git_init(path: Path) -> None:
+  250	    subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, capture_output=True)
+  251	    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
+  252	                    "commit", "--allow-empty", "-m", "init"],
+  253	                   cwd=path, check=True, capture_output=True)
+  254	
+  255	
+  256	def test_init_errors_without_authority_config(tmp_path):
+  257	    _git_init(tmp_path)
+  258	    r = run_cli("init", "--project", "demo", cwd=tmp_path)
+  259	    assert r.returncode != 0
+  260	    assert "no authoritative-checkout routing configured" in r.stderr
+  261	    assert "tasktool config init-authority" in r.stderr
+  262	    assert not (tmp_path / "docs" / "tasklist.json").exists()
+  263	
+  264	
+  265	def test_start_errors_without_authority_config(tmp_path):
+  266	    _git_init(tmp_path)
+  267	    # Create a tasklist by writing the file directly so `start` has a row to operate on.
+  268	    (tmp_path / "docs").mkdir()
+  269	    (tmp_path / "docs" / "tasklist.json").write_text(
+  270	        '{"schema_version":1,"project":"demo","phases":[],'
+  271	        '"cross_cutting":[{"id":"X1","title":"t","created":"2026-05-20","status":"ready",'
+  272	        '"refs":[],"notes":"","started":null,"closed":null}],"archived_phases":[]}'
+  273	    )
+  274	    r = run_cli("start", "X1", cwd=tmp_path)
+  275	    assert r.returncode != 0
+  276	    assert "no authoritative-checkout routing configured" in r.stderr
+  277	
+  278	
+  279	def test_validate_without_normalise_works_unconfigured(tmp_path):
+  280	    _git_init(tmp_path)
+  281	    (tmp_path / "docs").mkdir()
+  282	    (tmp_path / "docs" / "tasklist.json").write_text(
+  283	        '{"schema_version":1,"project":"demo","phases":[],'
+  284	        '"cross_cutting":[],"archived_phases":[]}'
+  285	    )
+  286	    r = run_cli("validate", cwd=tmp_path)
+  287	    assert r.returncode == 0, r.stdout + r.stderr
+  288	
+  289	
+  290	def test_validate_normalise_errors_unconfigured(tmp_path):
+  291	    _git_init(tmp_path)
+  292	    (tmp_path / "docs").mkdir()
+  293	    (tmp_path / "docs" / "tasklist.json").write_text(
+  294	        '{"schema_version":1,"project":"demo","phases":[],'
+  295	        '"cross_cutting":[],"archived_phases":[]}'
+  296	    )
+  297	    r = run_cli("validate", "--normalise", cwd=tmp_path)
+  298	    assert r.returncode != 0
+  299	    assert "no authoritative-checkout routing configured" in r.stderr
+  300	
+  301	
+  302	def test_render_works_unconfigured(tmp_path):
+  303	    _git_init(tmp_path)
+  304	    (tmp_path / "docs").mkdir()
+  305	    (tmp_path / "docs" / "tasklist.json").write_text(
+  306	        '{"schema_version":1,"project":"demo","phases":[],'
+  307	        '"cross_cutting":[],"archived_phases":[]}'
+  308	    )
+  309	    r = run_cli("render", cwd=tmp_path)
+  310	    assert r.returncode == 0, r.stdout + r.stderr
+  311	
+  312	
+  313	@pytest.mark.parametrize("readonly_cmd", [
+  314	    ("render",),
+  315	    ("validate",),
+  316	    ("brief",),
+  317	    ("schema",),
+  318	    ("show", "P1"),
+  319	    ("phase-status", "P1"),
+  320	    ("ready-slices", "P1"),
+  321	    ("list",),
+  322	    ("next-id",),
+  323	])
+  324	def test_other_readonly_commands_work_unconfigured(tmp_path, readonly_cmd):
+  325	    """Spec test #5: read-only commands beyond render/validate succeed without config.
+  326	    Every command listed as read-only in the spec must exit 0 against a valid
+  327	    tasklist when no .tasktool/config.json exists."""
+  328	    _git_init(tmp_path)
+  329	    (tmp_path / "docs").mkdir()
+  330	    (tmp_path / "docs" / "tasklist.json").write_text(
+  331	        '{"schema_version":1,"project":"demo",'
+  332	        '"phases":[{"id":"P1","title":"p","created":"2026-05-20","status":"ready",'
+  333	        '"started":null,"closed":null,"spec_path":null,"plan_path":null,'
+  334	        '"planning_path":null,"phase_reviewer_chain":null,"notes":"","slices":['
+  335	        '{"id":"S1","title":"s","created":"2026-05-20","status":"ready",'
+  336	        '"started":null,"closed":null,"blocked_on":null,"depends_on":[],'
+  337	        '"planning_status":"proposed","parallel_group":null,"plan_path":null,'
+  338	        '"refs":[],"notes":"","reviewer_chain":null,"tasks":[]}]}],'
+  339	        '"cross_cutting":[],"archived_phases":[]}'
+  340	    )
+  341	    r = run_cli(*readonly_cmd, cwd=tmp_path)
+  342	    assert r.returncode == 0, (
+  343	        f"read-only command {readonly_cmd} should succeed without config; "
+  344	        f"stdout={r.stdout!r} stderr={r.stderr!r}"
+  345	    )
+  346	    assert "no authoritative-checkout routing configured" not in r.stderr, r.stderr
+  347	
+  348	
+  349	def test_explicit_local_mode_still_mutates(tmp_path):
+  350	    _git_init(tmp_path)
+  351	    r = run_cli("config", "init-local", cwd=tmp_path)
+  352	    assert r.returncode == 0, r.stdout + r.stderr
+  353	    r = run_cli("init", "--project", "demo", cwd=tmp_path)
+  354	    assert r.returncode == 0, r.stdout + r.stderr
+  355	    assert (tmp_path / "docs" / "tasklist.json").exists()
+  356	
+  357	
+  358	def test_bootstrap_init_authority_then_init_succeeds(tmp_path):
+  359	    """Spec test #6: greenfield positive — init-authority first, then init succeeds."""
+  360	    _git_init(tmp_path)
+  361	    r = run_cli("config", "init-authority", "--branch", "main", cwd=tmp_path)
+  362	    assert r.returncode == 0, r.stdout + r.stderr
+  363	    r = run_cli("init", "--project", "demo", cwd=tmp_path)
+  364	    assert r.returncode == 0, r.stdout + r.stderr
+  365	    assert (tmp_path / "docs" / "tasklist.json").exists()
+  366	
+  367	
+  368	def test_bootstrap_init_before_init_authority_fails(tmp_path):
+  369	    """Spec test #7: explicit negative — bare `init` without prior authority config errors."""
+  370	    _git_init(tmp_path)
+  371	    r = run_cli("init", "--project", "demo", cwd=tmp_path)
+  372	    assert r.returncode != 0
+  373	    assert "no authoritative-checkout routing configured" in r.stderr
+  374	    assert not (tmp_path / "docs" / "tasklist.json").exists()
+  375	```
+  376	
+  377	(The `init-local` part of `test_explicit_local_mode_still_mutates` is forward-referenced; it will pass after Task 3.)
+  378	
+  379	- [ ] **Step 2: Run the test, expect mutation tests to fail with the hard-error message NOT present**
+  380	
+  381	```bash
+  382	PYTHONPATH=tools pytest tools/tasktool/tests/test_unconfigured_mutation.py -v
+  383	```
+  384	
+  385	Expected: `test_init_errors_without_authority_config`, `test_start_errors_without_authority_config`, `test_validate_normalise_errors_unconfigured` fail (mutations currently succeed). Read-only tests pass. `test_explicit_local_mode_still_mutates` fails on the `config init-local` line (subcommand doesn't exist yet).
+  386	
+  387	- [ ] **Step 3: Add the hard-error path in `_resolve_write_root`**
+  388	
+  389	In `tools/tasktool/commands.py`, update the imports near the top of the file to add `is_authoritative_required`:
+  390	
+  391	```python
+  392	from tasktool.config import (
+  393	    TasklistConfig,
+  394	    TasktoolConfig,
+  395	    is_authoritative_required,
+  396	    load_config,
+  397	    save_config,
+  398	)
+  399	```
+  400	
+  401	Replace `_resolve_write_root` (currently at `tools/tasktool/commands.py:80-98`) with:
+  402	
+  403	```python
+  404	UNCONFIGURED_HINT = (
+  405	    "tasktool: this repository has no authoritative-checkout routing configured. "
+  406	    "Run `tasktool config init-authority --branch <branch>` from the authoritative "
+  407	    "checkout to enable safe routing. Existing local-mode tasklists can be reconciled "
+  408	    "with `tasktool config migrate-from-local`. To opt out explicitly, run "
+  409	    "`tasktool config init-local`."
+  410	)
+  411	
+  412	
+  413	def _resolve_write_root(repo_root: Path) -> tuple[Path, bool, str, str]:
+  414	    cfg = load_config(repo_root)
+  415	    if is_authoritative_required(cfg):
+  416	        raise CommandError(UNCONFIGURED_HINT)
+  417	    if cfg.tasklist.mutation_mode == "local":
+  418	        return repo_root, False, cfg.tasklist.mutation_mode, cfg.tasklist.authoritative_branch
+  419	    try:
+  420	        authoritative = find_authoritative_root(repo_root, branch=cfg.tasklist.authoritative_branch)
+  421	        validate_authoritative_checkout(
+  422	            authoritative,
+  423	            expected_branch=cfg.tasklist.authoritative_branch,
+  424	            caller_root=repo_root,
+  425	        )
+  426	    except AuthorityError as exc:
+  427	        raise CommandError(str(exc)) from exc
+  428	    return (
+  429	        authoritative,
+  430	        repo_root.resolve() != authoritative.resolve(),
+  431	        cfg.tasklist.mutation_mode,
+  432	        cfg.tasklist.authoritative_branch,
+  433	    )
+  434	```
+  435	
+  436	- [ ] **Step 4: Run the tests again**
+  437	
+  438	```bash
+  439	PYTHONPATH=tools pytest tools/tasktool/tests/test_unconfigured_mutation.py -v
+  440	```
+  441	
+  442	Expected: every test except `test_explicit_local_mode_still_mutates` passes. The latter still fails on `config init-local` (forward-referenced to Task 3).
+  443	
+  444	- [ ] **Step 5: Run the full tasktool suite to surface regressions**
+  445	
+  446	```bash
+  447	PYTHONPATH=tools pytest tools/tasktool/tests/ -v
+  448	```
+  449	
+  450	Expected: failures in any test that called `tasktool init` / `tasktool start` etc. against a fresh `tmp_path` without first configuring authority. Capture the list — those tests get explicit `config init-local` or `config init-authority` setup in Task 6.
+  451	
+  452	- [ ] **Step 6: Commit**
+  453	
+  454	```bash
+  455	git add tools/tasktool/commands.py tools/tasktool/tests/test_unconfigured_mutation.py
+  456	git commit -m "X12: refuse mutations when tasktool authority routing is unconfigured"
+  457	```
+  458	
+  459	---
+  460	
+  461	## Task 3: Add `tasktool config init-local` subcommand
+  462	
+  463	**Files:**
+  464	- Modify: `tools/tasktool/commands.py`
+  465	- Modify: `tools/tasktool/cli.py`
+  466	- Create: `tools/tasktool/tests/test_init_local.py`
+  467	
+  468	- [ ] **Step 1: Write the failing test**
+  469	
+  470	Create `tools/tasktool/tests/test_init_local.py`:
+  471	
+  472	```python
+  473	from __future__ import annotations
+  474	
+  475	import json
+  476	import subprocess
+  477	import sys
+  478	from pathlib import Path
+  479	
+  480	REPO_ROOT = Path(__file__).resolve().parents[3]
+  481	PKG_DIR = REPO_ROOT / "tools"
+  482	
+  483	
+  484	def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
+  485	    import os
+  486	    env = os.environ.copy()
+  487	    env["PYTHONPATH"] = str(PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")
+  488	    return subprocess.run(
+  489	        [sys.executable, "-m", "tasktool", *args],
+  490	        capture_output=True, text=True, cwd=cwd, env=env,
+  491	    )
+  492	
+  493	
+  494	def _git_init(path: Path) -> None:
+  495	    subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, capture_output=True)
+  496	
+  497	
+  498	def test_init_local_writes_config(tmp_path):
+  499	    _git_init(tmp_path)
+  500	    r = run_cli("config", "init-local", cwd=tmp_path)
+  501	    assert r.returncode == 0, r.stdout + r.stderr
+  502	    data = json.loads((tmp_path / ".tasktool" / "config.json").read_text())
+  503	    assert data["tasklist"]["mutation_mode"] == "local"
+  504	
+  505	
+  506	def test_init_local_then_init_succeeds(tmp_path):
+  507	    _git_init(tmp_path)
+  508	    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
+  509	                    "commit", "--allow-empty", "-m", "init"],
+  510	                   cwd=tmp_path, check=True, capture_output=True)
+  511	    assert run_cli("config", "init-local", cwd=tmp_path).returncode == 0
+  512	    r = run_cli("init", "--project", "demo", cwd=tmp_path)
+  513	    assert r.returncode == 0, r.stdout + r.stderr
+  514	    assert (tmp_path / "docs" / "tasklist.json").exists()
+  515	
+  516	
+  517	def test_init_local_refuses_overwriting_authoritative(tmp_path):
+  518	    _git_init(tmp_path)
+  519	    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
+  520	                    "commit", "--allow-empty", "-m", "init"],
+  521	                   cwd=tmp_path, check=True, capture_output=True)
+  522	    assert run_cli("config", "init-authority", "--branch", "main", cwd=tmp_path).returncode == 0
+  523	    r = run_cli("config", "init-local", cwd=tmp_path)
+  524	    assert r.returncode != 0
+  525	    assert "already configured" in r.stderr or "already configured" in r.stdout
+  526	```
+  527	
+  528	- [ ] **Step 2: Run the test, expect failure**
+  529	
+  530	```bash
+  531	PYTHONPATH=tools pytest tools/tasktool/tests/test_init_local.py -v
+  532	```
+  533	
+  534	Expected: argparse-level failures (`invalid choice: 'init-local'`).
+  535	
+  536	- [ ] **Step 3: Add `cmd_config_init_local` to commands.py**
+  537	
+  538	In `tools/tasktool/commands.py`, immediately after `cmd_config_init_authority`, add:
+  539	
+  540	Design note (intentional): `cmd_config_init_local` refuses ONLY when the existing config is `authoritative-checkout` — switching away from authoritative routing is a non-trivial workflow change and should require deliberate operator action (delete the config file first). It is idempotent against an existing `local` config (re-runs are no-ops, exit 0) and overwrites a config file whose `mutation_mode` is missing (treating that case as bootstrap completion).
+  541	
+  542	```python
+  543	def cmd_config_init_local(*, repo_root: Path) -> None:
+  544	    existing_path = repo_root / ".tasktool" / "config.json"
+  545	    if existing_path.exists():
+  546	        raw = json.loads(existing_path.read_text(encoding="utf-8"))
+  547	        mode = raw.get("tasklist", {}).get("mutation_mode")
+  548	        if mode == "authoritative-checkout":
+  549	            raise CommandError(
+  550	                "tasktool: this repository is already configured for authoritative-checkout "
+  551	                "routing; refusing to overwrite. Delete `.tasktool/config.json` first if you "
+  552	                "really intend to switch to local mode."
+  553	            )
+  554	        if mode == "local":
+  555	            # Idempotent: already configured for local mode.
+  556	            print(
+  557	                "tasktool: already configured for local mutation mode (no change).",
+  558	                file=sys.stderr,
+  559	            )
+  560	            return
+  561	    cfg = TasktoolConfig(
+  562	        tasklist=TasklistConfig(mutation_mode="local")
+  563	    )
+  564	    save_config(repo_root, cfg)
+  565	    _git_stage(repo_root, repo_root / ".tasktool" / "config.json")
+  566	    print(
+  567	        "tasktool: configured for local mutation mode. Worktree-side mutations will "
+  568	        "NOT be routed to a shared authoritative checkout.",
+  569	        file=sys.stderr,
+  570	    )
+  571	```
+  572	
+  573	Ensure `json` is imported at the top of `commands.py` (it already is — check the existing import block).
+  574	
+  575	- [ ] **Step 4: Register the subcommand in cli.py**
+  576	
+  577	In `tools/tasktool/cli.py`, immediately after the `init-authority` parser registration (around line 29-30), add:
+  578	
+  579	```python
+  580	    p_config_local = config_sub.add_parser("init-local")
+  581	    # No arguments — explicit opt-out, writes mutation_mode=local.
+  582	```
+  583	
+  584	In the dispatch block where `config_cmd == "init-authority"` is handled (around `tools/tasktool/cli.py:191`), add an `elif` branch:
+  585	
+  586	```python
+  587	            elif args.config_cmd == "init-local":
+  588	                commands.cmd_config_init_local(repo_root=repo_root)
+  589	```
+  590	
+  591	- [ ] **Step 5: Run the test, expect pass**
+  592	
+  593	```bash
+  594	PYTHONPATH=tools pytest tools/tasktool/tests/test_init_local.py tools/tasktool/tests/test_unconfigured_mutation.py -v
+  595	```
+  596	
+  597	Expected: both files pass in full now.
+  598	
+  599	- [ ] **Step 6: Commit**
+  600	
+
+[truncated: 1314 additional lines]
+
+## Context Previews
+
+### docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md
+
+    1	# X12 — tasktool: require authoritative-checkout routing for mutations
+    2	
+    3	**Status:** spec
+    4	**Tasktool ID:** X12 (cross-cutting)
+    5	**Date:** 2026-05-20
+    6	
+    7	## Problem
+    8	
+    9	`tools/tasktool` already implements authoritative-checkout routing: when `.tasktool/config.json` sets `tasklist.mutation_mode` to `authoritative-checkout`, mutating commands route writes to the configured authoritative checkout (typically the `main` worktree) instead of the caller's CWD `docs/tasklist.json`. The mechanism is sound and exercised in this repo.
+   10	
+   11	It is also opt-in. The default mutation mode is `local` (`tools/tasktool/config.py:13`), and projects with no `.tasktool/config.json` silently fall back to that default. Neither `tasktool init` nor the `project-setup` skill wires the authority config automatically. The result: a fresh project — or any project that never ran `tasktool config init-authority` — mutates whatever `docs/tasklist.json` happens to be in CWD, including the copy that lives inside a worktree.
+   12	
+   13	The user-visible symptom is divergence between the TTS announcements emitted by `tools/tasktool/notify.py` (which fire from whichever tasklist.json was mutated, anywhere on disk) and the AGS sidebar widget (`~/.config/ags/gizmos/sidebar/tasklists/data.ts:147`), which only monitors `<projectRoot>/docs/tasklist.json`. A worktree-side mutation announces correctly but never reaches the file the widget watches. The example case is `multistore` P13.S6: the worktree `docs/tasklist.json` shows `status: in_progress, started: 2026-05-20`; the main-branch copy shows `status: ready, started: null`. Multistore has no `.tasktool/` directory at all.
+   14	
+   15	The skills (`tasklist-discipline`, `using-git-worktrees`) treat authority routing as conditional — "when configured" — rather than as a binding requirement. That phrasing reflects the implementation but defeats the intent: authoritative routing should be the *only* supported mode for mutations, because it is the only mode under which the widget, TTS, and on-disk source-of-truth agree.
+   16	
+   17	## Goals
+   18	
+   19	1. Make authoritative-checkout routing structurally required for mutating tasktool commands. A repo with no authority config cannot accidentally mutate a worktree copy.
+   20	2. Provide a first-class migration path for repos that already drifted under the old default, so an operator can reconcile worktree-only state back into the authoritative checkout without hand-editing JSON.
+   21	3. Update the skills that govern tasktool usage so the documented workflow matches the enforced behaviour.
+   22	
+   23	## Non-goals
+   24	
+   25	- Changing the AGS sidebar widget. Once routing is enforced, the widget's existing single-file watch is correct by construction.
+   26	- Auto-detecting the authoritative branch name. `tasktool config init-authority` already takes the branch explicitly; this spec does not add main/master inference.
+   27	- Reconciling `multistore`'s current drift in code. The new `migrate-from-local` subcommand is the tool; running it against multistore is a one-shot operator action after this change ships.
+   28	- Removing the `local` mutation mode. It remains a valid *explicit* opt-out, written by hand, for repos that intentionally want CWD-local mutations and have no worktree convention. What changes is that it is no longer the implicit default.
+   29	
+   30	## Design
+   31	
+   32	### 1. Mutation default → hard error
+   33	
+   34	`tools/tasktool/config.py` continues to accept `mutation_mode: "local"` as a valid configured value. What changes is the behaviour when no `.tasktool/config.json` exists, or when the file exists but does not specify `mutation_mode`:
+   35	
+   36	- Today: silently defaults to `local`.
+   37	- After: `load_config()` returns a sentinel "unconfigured" state. `_resolve_write_root` in `tools/tasktool/commands.py` raises `CommandError` for mutating commands with the message:
+   38	
+   39	  > tasktool: this repository has no authoritative-checkout routing configured. Run `tasktool config init-authority --branch <branch>` from the authoritative checkout to enable safe routing. Existing local-mode tasklists can be reconciled with `tasktool config migrate-from-local`.
+   40	
+   41	Mutating commands are those that go through `_write_context`: `init`, `create *`, `set`, `start`, `close`, `block`, `unblock`, `deps`, `ratify`, `planning-path`, `note`, `ref`, `title`, `archive-phase`, `import`, and `validate --normalise` (the `--normalise` flag triggers a `_write_context` write at `tools/tasktool/commands.py:814`; plain `validate` remains read-only).
+   42	
+   43	This means the bootstrap order changes. Today: `tasktool init` (creates `docs/tasklist.json`) → optionally `tasktool config init-authority --branch <branch>`. After: `tasktool config init-authority --branch <branch>` first (writes `.tasktool/config.json` — does not go through `_write_context`, validates branch directly), *then* `tasktool init` (routes through the authority and creates the tasklist in the right checkout). `cmd_config_init_authority` is exempt from the hard error by virtue of not flowing through `_write_context`; this is preserved deliberately so the bootstrap path remains usable. The `project-setup` skill documents the new order.
+   44	
+   45	Read-only commands — `render`, `validate` (without `--normalise`), `brief`, `schema`, `show`, `phase-status`, `ready-slices`, `list`, `next-id` — must continue to work without config. They read whichever `docs/tasklist.json` is in CWD. The error is raised *only* on the mutation path.
+   46	
+   47	An explicit `mutation_mode: "local"` keeps its current behaviour: mutations land in CWD's `docs/tasklist.json` with no routing. The hard error fires only for unconfigured repos.
+   48	
+   49	### 2. `tasktool config init-authority` — no functional change
+   50	
+   51	The existing subcommand keeps its semantics: invoked as `tasktool config init-authority --branch <branch>`, must be run from the target branch in a clean checkout, writes `.tasktool/config.json` with `mutation_mode: authoritative-checkout` and the supplied branch name, stages the file. The hardening here is by virtue of step 1 — operators discover they need to run it because mutations now fail loudly without it.
+   52	
+   53	### 2a. `tasktool config init-local` — new auditable opt-out
+   54	
+   55	To keep `mutation_mode: "local"` from requiring hand-edited JSON, add a thin sibling subcommand:
+   56	
+   57	```
+   58	tasktool config init-local
+   59	```
+   60	
+   61	Writes `.tasktool/config.json` with `mutation_mode: local`, stages the file, and prints a one-line notice that worktree-side mutations will not be routed. Behaviour is otherwise identical to today's `local` mode; this exists purely so the opt-out leaves a tracked, committed artifact, and so the hard error message can point at a concrete remediation rather than at a JSON snippet to copy. Does not go through `_write_context`.
+   62	
+   63	### 3. `tasktool config migrate-from-local` — new subcommand
+   64	
+   65	Synopsis:
+   66	
+   67	```
+   68	tasktool config migrate-from-local --authority-root <path> [--local-root <path>]
+   69	                                   [--dry-run]
+   70	                                   [--accept-local | --accept-authoritative]
+   71	```
+   72	
+   73	Rationale for the explicit root flags: the realistic drift case is a repo with no `.tasktool/config.json` anywhere on disk — including the worktree the operator is sitting in. Requiring authority config in either tree would create a bootstrap deadlock (you cannot `init-authority` into the drifted worktree without first being on `main` there, and you cannot reach the worktree's tasklist from `main` once you switch). Passing both roots explicitly bypasses any dependency on existing config:
+   74	
+   75	- `--authority-root <path>` (required): absolute or repo-relative path to the checkout that will become authoritative. Must resolve to a git checkout in the same common-dir as the caller. The migration writes here.
+   76	- `--local-root <path>` (optional, default = CWD's repo root): absolute or repo-relative path to the checkout whose `docs/tasklist.json` holds the drifted state to capture. Read-only.
+   77	
+   78	Semantics:
+   79	
+   80	1. **Preconditions.** Both roots resolve to git checkouts. `same_repository(authority_root, local_root)` returns true. `validate_authoritative_checkout(authority_root, expected_branch=<resolved>, caller_root=local_root)` succeeds — the authority root is on its target branch, clean of unmerged paths, and free of unstaged `docs/tasklist.json` changes. If `.tasktool/config.json` exists in `authority_root` and specifies a `mutation_mode`/`authoritative_branch`, those values are honoured; otherwise the authority root's *current branch* is treated as the target (and persisted into a new `.tasktool/config.json` on successful migration). Either tasklist missing → `CommandError` with a remediation hint.
+   81	2. **Load both tasklists.** Local = `<local_root>/docs/tasklist.json` parsed via existing `_load`. Authoritative = `<authority_root>/docs/tasklist.json` parsed via existing `_load`. If the two are byte-identical, exit 0 with "no drift detected".
+   82	3. **Row-level diff (full persisted surface).** Walk every row class the model persists, using dataclass introspection (`dataclasses.fields()` on `Project`, `Phase`, `Slice`, `Task`, `CrossCutting`, and any other row dataclass declared in `tools/tasktool/model.py`) so the diff cannot silently omit fields. Concretely:
+   83	   - **Top-level scalars on `Project`** — `project`, `north_star`, `last_reviewed`, and any other top-level scalar declared in the dataclass.
+   84	   - **`phases[]`** keyed by `Phase.id`. For each phase: every field declared on `Phase` (including `status`, `started`, `closed`, `title`, `spec_path`, `plan_path`, `planning_path`, `planning_status`, `refs`, `notes`, `depends_on`, `blocked_on`, `parallel_group`, `reviewer_chain`, `phase_reviewer_chain`, `created`).
+   85	   - **`phases[].slices[]`** keyed by `Slice.id` within its phase. Every field declared on `Slice`.
+   86	   - **`phases[].slices[].tasks[]`** (and any other nested rows the model declares) keyed by `Task.id` within its slice. Every field declared on `Task`.
+   87	   - **`cross_cutting[]`** keyed by `CrossCutting.id`. Every field declared on `CrossCutting`.
+   88	   - **`archived_phases[]`** keyed by `id`. Every field declared on the archive row type.
+   89	   - For each row: present in local only → candidate addition; present in authoritative only → candidate deletion (flagged as conflict — main is ahead); present in both → every dataclass field is compared. Each differing field is a delta.
+   90	   The implementation is one short recursive walker keyed off `dataclasses.fields()`, not a hand-maintained field list. The test suite asserts that adding a new field to any row dataclass without updating the walker fails loudly (see Testing).
+   91	4. **Render a human-readable diff** to stdout, e.g.:
+   92	
+   93	   ```
+   94	   P13.S6  status: ready → in_progress
+   95	           started: null → 2026-05-20
+   96	   P13.S7  status: ready → done
+   97	           closed: null → 2026-05-19
+   98	   X9      notes: "" → "deferred to phase 14"
+   99	   ```
+  100	
+  101	5. **`--dry-run`**: stop here.
+  102	6. **Conflict policy.** Exactly one of `--accept-local` / `--accept-authoritative` must be provided unless stdin is a TTY (in which case the operator is prompted interactively). There is no implicit default.
+  103	   - `--accept-local`: the local copy wins per-field for rows present in both trees. Rows present in local only are added to the authoritative tasklist. Rows present in the authoritative tasklist only are **kept** — they are never silently deleted under any policy; the diff prints them as `authoritative-only (kept)` and the migration leaves them in place. This protects work that was committed to `main` while the worktree was diverging.
+  104	   - `--accept-authoritative`: authoritative wins per-field for rows present in both trees. No write occurs; the command becomes a verification step. Rows present in local only are reported as `local-only (not migrated)` and skipped. Rows present in the authoritative tasklist only are likewise reported and kept (same rule as above).
+  105	   - No flag and stdin is a TTY: print the diff, then prompt once accepting `local` / `authoritative` / `abort`. The chosen policy is logged in the exit message.
+  106	   - No flag and stdin is not a TTY: `CommandError`: `migrate-from-local requires one of --accept-local or --accept-authoritative in non-interactive contexts`.
+  107	7. **Apply.** Acquire `tasktool_lock` on the authoritative root. Re-read the authoritative tasklist inside the lock (defensive against concurrent writes). Apply the resolved deltas in memory. `_save(authoritative_root, project)`. Stage the file via existing best-effort stage.
+  108	8. **Notify.** For each row whose `status` changed, call `_notify_status` with the post-migration status so the TTS pipeline and any downstream consumers see the transition. Non-status field changes do not notify.
+  109	9. **Exit message.** Print a one-line summary: `migrated N rows (S status transitions) to <authoritative-root>`. Leave the local tasklist.json untouched; the next mutation routes through authority and the local copy becomes irrelevant.
+  110	
+  111	The command does **not** attempt to replay the deltas as a sequence of individual tasktool subcommands. A single merged `_save` is simpler, atomic under the lock, and avoids combinatorial issues (e.g. a slice that was both started and closed in the worktree).
+  112	
+  113	### 4. Skills
+  114	
+  115	- `skills/project-setup/SKILL.md` — add to the setup checklist: **before `tasktool init`**, from the target branch, run `tasktool config init-authority --branch <main-branch>` and commit `.tasktool/config.json`; then run `tasktool init`. The reverse order would fail under the new hard error because `tasktool init` itself routes through `_write_context`. Surface a missing/unconfigured authority as a setup-precondition failure on par with a missing `docs/tasklist.json`.
+  116	- `skills/tasklist-discipline/SKILL.md` — change the existing paragraph that opens "When `.tasktool/config.json` sets `tasklist.mutation_mode` to `authoritative-checkout`…" so that authoritative routing is described as the required mode. Add a one-line remediation pointer: if a mutation errors with "no authoritative-checkout routing configured", run `tasktool config init-authority --branch <branch>` from the target branch.
+  117	- `skills/using-git-worktrees/SKILL.md` — remove the "If tasktool authoritative-checkout routing is configured" conditional. Replace with the unconditional rule that tasktool mutations from worktrees route through authority; if config is missing, configure it before starting implementation work.
+  118	
+  119	No new skill files. No new top-level docs.
+  120	
+  121	## Component boundaries
+  122	
+  123	- `config.py` owns the unconfigured-vs-explicit-local distinction. It exposes a small predicate (`is_authoritative_required(cfg) -> bool` or equivalent) consumed by `commands.py`. Adding the predicate keeps `commands.py` free of policy logic.
+  124	- `commands.py` owns the routing decision and the new `cmd_config_migrate_from_local` function. Pure-Python diff/merge over the existing `Project` dataclass tree; reuses `_load`, `_save`, `tasktool_lock`, `_notify_status`.
+  125	- `cli.py` owns argument parsing for the new subcommands. `config migrate-from-local`: `--authority-root <path>` (required), `--local-root <path>` (optional, defaults to caller repo root), `--dry-run`, `--accept-local`, `--accept-authoritative`. `config init-local`: no arguments.
+  126	- `worktree.py` is unchanged. `find_authoritative_root`, `validate_authoritative_checkout`, and `tasktool_lock` already do what `migrate-from-local` needs.
+  127	
+  128	## Error handling
+  129	
+  130	- Unconfigured repo, mutating command: `CommandError` with the migration hint message (verbatim above). Non-zero exit.
+  131	- `init-authority` from wrong branch: existing behaviour preserved.
+  132	- `migrate-from-local` with no `--authority-root`: `CommandError`: `migrate-from-local requires --authority-root <path>`. The command never assumes a config-driven default; the path must be explicit so the migration is unambiguous even when `.tasktool/config.json` is absent from every checkout.
+  133	- `migrate-from-local` with neither `--accept-local` nor `--accept-authoritative` and stdin is not a TTY: `CommandError`: `migrate-from-local requires one of --accept-local or --accept-authoritative in non-interactive contexts`.
+  134	- `migrate-from-local` where `--authority-root` and `--local-root` are not the same git common-dir: `CommandError`: `authority root and local root are not the same repository`.
+  135	- `migrate-from-local` when authoritative tasklist is missing entirely: `CommandError`: tells the user to run `tasktool init` in the authoritative checkout first.
+  136	- `migrate-from-local` with no detectable drift: exit 0, message "no drift detected".
+  137	- `migrate-from-local` with `--accept-local` and no TTY when prompt would be needed: covered by the per-flag explicit semantics; no interactive fallback in non-TTY contexts.
+  138	
+  139	## Testing
+  140	
+  141	New tests under `tools/tasktool/tests/`:
+  142	
+  143	1. `test_config_default_errors_on_mutation` — fresh repo, no `.tasktool/config.json`; `tasktool start P1.S1` raises `CommandError` containing the migration hint substring.
+  144	2. `test_config_default_errors_on_validate_normalise` — fresh repo, no config; `tasktool validate --normalise` raises `CommandError` (mutating); `tasktool validate` (no flag) still works.
+  145	3. `test_config_explicit_local_mode_still_mutates_cwd` — config with `mutation_mode: local`; `tasktool start P1.S1` mutates CWD's tasklist; assert no regression.
+  146	4. `test_config_init_local_writes_config` — `tasktool config init-local` from a fresh repo writes `.tasktool/config.json` with `mutation_mode: local`, stages it, and the next `tasktool start` succeeds against CWD.
+  147	5. `test_readonly_commands_work_without_config` — `render`, `validate` (no `--normalise`), `brief`, `schema`, `show`, `phase-status`, `ready-slices`, `list`, `next-id` succeed against an unconfigured repo.
+  148	6. `test_bootstrap_init_after_init_authority` — greenfield: `tasktool config init-authority --branch main` then `tasktool init` on the same checkout creates `docs/tasklist.json` in that checkout.
+  149	7. `test_bootstrap_init_before_init_authority_fails` — greenfield: running `tasktool init` first (without authority config) fails with the migration hint.
+  150	8. `test_migrate_from_local_drifted_repo_no_config_anywhere` — repo with main checkout and a linked worktree that has divergent `docs/tasklist.json` but **no `.tasktool/config.json` in either tree**; `tasktool config migrate-from-local --authority-root <main> --accept-local` from the worktree succeeds, writes the merged tasklist to the main checkout, and writes a fresh `.tasktool/config.json` into the main checkout. This is the F1 acceptance test.
+  151	9. `test_migrate_from_local_dry_run` — divergent tasklists; `--dry-run` prints the row-level diff and writes nothing in either tree.
+  152	10. `test_migrate_from_local_accept_local_applies_deltas` — divergent `status`, `started`, `closed`, `refs`, `notes`; `--accept-local` writes them through to the authoritative tasklist; assert post-merge equality.
+  153	11. `test_migrate_from_local_accept_authoritative_noop` — `--accept-authoritative` acquires the lock, writes nothing, exits 0.
+  154	12. `test_migrate_from_local_emits_notify_events` — status transitions during migration produce notify events matching the existing fixture pattern in `tools/tasktool/tests/test_notify.py`.
+  155	13. `test_migrate_from_local_no_drift_exits_clean` — byte-identical tasklists; command exits 0 with the "no drift detected" message.
+  156	14. `test_migrate_from_local_full_field_surface` — for each row type in the model (`Project`, `Phase`, `Slice`, `Task`, `CrossCutting`, archived phase row), create a divergence on each declared dataclass field — including `blocked_on`, `planning_status`, `reviewer_chain`, `phase_reviewer_chain`, `archived_phases`, `project`, `north_star`, `last_reviewed` — and assert every field migrates through. Implementation uses `dataclasses.fields()` parameterisation so adding a new field to a row dataclass without updating the migrator's walker fails this test.
+  157	15. `test_migrate_from_local_walker_covers_all_dataclass_fields` — meta-test: introspects the migrator's known-field set against `dataclasses.fields()` on every row type; fails loudly if a model field is missing from the walker. Belt-and-braces complement to test 14.
+  158	16. `test_migrate_from_local_handles_nested_tasks` — phase with slice with tasks; task-level divergence (`status`, `notes`, `refs`) migrates correctly.
+  159	17. `test_migrate_from_local_preserves_authority_only_rows` — authoritative tasklist has a row missing from the local tasklist (e.g. a phase committed to main while the worktree was diverging). Under `--accept-local`, the row is kept in the authoritative tasklist after migration, never deleted. Diff output labels it `authoritative-only (kept)`.
+  160	
+  161	Existing tests should be audited for any that rely on the implicit-`local` default; those switch to either configuring `local` explicitly (via the new `init-local` command or a fixture that writes the config) or configuring `authoritative-checkout`, whichever matches the test's intent.
+  162	
+  163	## Migration & rollout
+  164	
+  165	After merge, the operator action for `multistore` (and any other repo that drifted under the old default) does **not** require `.tasktool/config.json` to exist anywhere in advance:
+  166	
+  167	```
+  168	# From the drifted worktree (e.g. multistore/.worktrees/p13-s6-closeout).
+  169	# --authority-root points at the on-disk checkout that holds main.
+  170	# --local-root defaults to CWD; pass it explicitly only if running from elsewhere.
+  171	
+  172	tasktool config migrate-from-local \
+  173	    --authority-root /home/simon/Dev/multistore \
+  174	    --dry-run                                            # preview the diff
+  175	
+  176	tasktool config migrate-from-local \
+  177	    --authority-root /home/simon/Dev/multistore \
+  178	    --accept-local                                       # apply, capture worktree drift
+  179	
+  180	# migrate-from-local writes .tasktool/config.json into the authority root if absent,
+  181	# using its current branch as the authoritative branch. Commit it alongside the
+  182	# tasklist update in the authority checkout:
+  183	
+  184	git -C /home/simon/Dev/multistore add docs/tasklist.json .tasktool/config.json
+  185	git -C /home/simon/Dev/multistore commit -m "tasktool: enable authoritative routing and reconcile drift"
+  186	```
+  187	
+  188	For a clean greenfield project (no drift), the bootstrap is the plain sequence — note that `init-authority` runs *before* `init`, because `init` itself routes through `_write_context`:
+  189	
+  190	```
+  191	cd <repo-on-main>
+  192	tasktool config init-authority --branch main
+  193	tasktool init
+  194	git add .tasktool/config.json docs/tasklist.json
+  195	git commit -m "tasktool: initialise with authoritative routing"
+  196	```
+  197	
+  198	The change is otherwise transparent for repos already running `authoritative-checkout` (this one).
+  199	
+  200	## Open questions
+
+[truncated: 6 additional lines]
+### docs/tasklist.json
+
+    1	{
+    2	  "archived_phases": [
+    3	    {
+    4	      "archived_date": "2026-05-18",
+    5	      "archived_path": "docs/archived-tasks/P2-tasktool-json-backed-task-management-cli.md",
+    6	      "id": "P2",
+    7	      "title": "tasktool: JSON-backed task management CLI"
+    8	    },
+    9	    {
+   10	      "archived_date": "2026-05-19",
+   11	      "archived_path": "docs/archived-tasks/P4-tasktool-coordination-and-lifecycle-auth.md",
+   12	      "id": "P4",
+   13	      "title": "Tasktool coordination and lifecycle authority"
+   14	    },
+   15	    {
+   16	      "archived_date": "2026-05-19",
+   17	      "archived_path": "docs/archived-tasks/P3-phase-planning-workflow.md",
+   18	      "id": "P3",
+   19	      "title": "Phase planning workflow"
+   20	    }
+   21	  ],
+   22	  "cross_cutting": [
+   23	    {
+   24	      "closed": "2026-05-18",
+   25	      "created": "2026-05-18",
+   26	      "id": "X1",
+   27	      "notes": "Changed external-review default prompt transport from argv to stdin so the bundled Codex reviewer-agent receives prompts via codex exec '-' and avoids argv length failures.",
+   28	      "refs": [],
+   29	      "started": null,
+   30	      "status": "done",
+   31	      "title": "Default external-review prompt transport to stdin"
+   32	    },
+   33	    {
+   34	      "closed": "2026-05-18",
+   35	      "created": "2026-05-18",
+   36	      "id": "X2",
+   37	      "notes": "Added repo-local tools/tasktool/tasktool launcher, updated tasklist/project-setup docs to prefer it, and taught the pre-commit hook to use the repo-local launcher before falling back to a global tasktool shim.",
+   38	      "refs": [],
+   39	      "started": null,
+   40	      "status": "done",
+   41	      "title": "Add repo-local tasktool launcher"
+   42	    },
+   43	    {
+   44	      "closed": "2026-05-19",
+   45	      "created": "2026-05-19",
+   46	      "id": "X3",
+   47	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. External-review verdict parsing now accepts markdown-emphasized Overall Verdict headings such as **5. Overall Verdict** followed by ready/revise text.",
+   48	      "refs": [
+   49	        "skills/external-review/scripts/external-reviewer.py",
+   50	        "skills/external-review/tests/test_heading_style_verdict.py"
+   51	      ],
+   52	      "started": null,
+   53	      "status": "done",
+   54	      "title": "Spot fix: parse bold external-review verdict headings"
+   55	    },
+   56	    {
+   57	      "closed": "2026-05-19",
+   58	      "created": "2026-05-19",
+   59	      "id": "X4",
+   60	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. Legacy markdown import now accepts fully-qualified slice IDs and additional cross-cutting forms including tagged done items, blocked cross rows coerced to ready, and archived cross rows treated as done.",
+   61	      "refs": [
+   62	        "tools/tasktool/importer.py"
+   63	      ],
+   64	      "started": null,
+   65	      "status": "done",
+   66	      "title": "Spot fix: broaden legacy tasklist importer compatibility"
+   67	    },
+   68	    {
+   69	      "closed": "2026-05-19",
+   70	      "created": "2026-05-19",
+   71	      "id": "X5",
+   72	      "notes": "User-requested hook update completed outside the normal workflow for speed. Adds Stop/SubagentStop finished-agent notifications, milestone message derivation from final agent text/transcript payloads, Hypr TTS config reuse with OPENAI_API_KEY fallback, and non-TTS ding fallbacks.\nSuperseded by X8: final-text milestone parsing was removed; agent hooks now emit generic dings and semantic spoken notifications come from tasktool status changes.",
+   73	      "refs": [
+   74	        "hooks/agent-finished",
+   75	        "hooks/hooks.json",
+   76	        "hooks/hooks-cursor.json",
+   77	        "tests/claude-code/test-agent-finished-hook.sh"
+   78	      ],
+   79	      "started": null,
+   80	      "status": "done",
+   81	      "title": "Add finished-agent notification hook"
+   82	    },
+   83	    {
+   84	      "closed": "2026-05-19",
+   85	      "created": "2026-05-19",
+   86	      "id": "X6",
+   87	      "notes": "Codex startup skips Stop/SubagentStop notification hooks when hooks.json uses async=true; fix should preserve finished-agent notification behavior while avoiding unsupported async hook registration in Codex.\nSet finished-agent Stop/SubagentStop hook registrations to async=false for Codex compatibility. The hook now backgrounds real notification playback internally so synchronous hook registration returns quickly while dry-run tests remain foreground and deterministic.",
+   88	      "refs": [
+   89	        "hooks/hooks.json",
+   90	        "hooks/agent-finished",
+   91	        "tests/claude-code/test-hook-config.sh",
+   92	        "tests/claude-code/test-agent-finished-hook.sh"
+   93	      ],
+   94	      "started": null,
+   95	      "status": "done",
+   96	      "title": "Fix Codex finished-agent hook compatibility"
+   97	    },
+   98	    {
+   99	      "closed": "2026-05-19",
+  100	      "created": "2026-05-19",
+  101	      "id": "X7",
+  102	      "notes": "Codex reported superstar/6.0.0 because the installable local marketplace payload under plugins/superstar still declared version 6.0.0 and the version bump audit did not track that embedded manifest.\n\nBumped the embedded Codex plugin payload manifest to 6.0.1 and added it to the version bump check. Reinstalled superstar@superstar-dev, then rebuilt the 6.0.1 runtime cache as a materialized copy of this checkout with .agents excluded so Codex sees the full skills/hooks tree while codex plugin list still reports installed/enabled. Final probe shows cache version 6.0.1, skills/hooks present, and no async-hook warning.",
+  103	      "refs": [
+  104	        ".version-bump.json",
+  105	        "plugins/superstar/.codex-plugin/plugin.json",
+  106	        ".agents/plugins/marketplace.json",
+  107	        "tests/codex-plugin-sync/test-version-drift.sh",
+  108	        "tests/codex-plugin-sync/test-local-marketplace.sh"
+  109	      ],
+  110	      "started": null,
+  111	      "status": "done",
+  112	      "title": "Fix Superstar Codex plugin payload version drift"
+  113	    },
+  114	    {
+  115	      "closed": "2026-05-19",
+  116	      "created": "2026-05-19",
+  117	      "id": "X8",
+  118	      "notes": "Move semantic spoken notifications to tasktool status transitions for ready/in_progress/blocked/done. Keep agent Stop/SubagentStop hooks as generic completion dings only, with different sound styles for Claude and Codex.\nAgent Stop/SubagentStop hooks now emit generic harness-specific dings only. Semantic spoken notifications moved to tasktool status events for ready, in_progress, blocked, and done, including create, set, close, block, unblock, and archive-phase paths.",
+  119	      "refs": [
+  120	        "hooks/agent-finished",
+  121	        "tools/tasktool/notify.py",
+  122	        "tools/tasktool/commands.py",
+  123	        "tools/tasktool/tests/test_notify.py",
+  124	        "tools/tasktool/tests/test_commands.py",
+  125	        "tools/tasktool/tests/conftest.py",
+  126	        "tests/claude-code/test-agent-finished-hook.sh"
+  127	      ],
+  128	      "started": null,
+  129	      "status": "done",
+  130	      "title": "Move semantic notifications from agent hooks to tasktool status changes"
+  131	    },
+  132	    {
+  133	      "closed": "2026-05-19",
+  134	      "created": "2026-05-19",
+  135	      "id": "X9",
+  136	      "notes": "Rapid tasktool status changes currently spawn independent notifier processes, causing overlapping TTS/audio. Add a single-audio queue with at most three queued tasktool events; overflow should collapse to a single 'multiple other events' summary and drop further items.\nAdded a file-backed notification queue shared by agent dings and tasktool TTS. Only one worker drains audio at a time. Queue capacity is three pending events; overflow keeps the first two pending items and replaces the rest with a single 'Multiple other events' summary, dropping further burst items while the summary remains queued.",
+  137	      "refs": [
+  138	        "tools/tasktool/notify.py",
+  139	        "tools/tasktool/tests/test_notify.py"
+  140	      ],
+  141	      "started": null,
+  142	      "status": "done",
+  143	      "title": "Coalesce bursty tasktool audio notifications"
+  144	    },
+  145	    {
+  146	      "closed": "2026-05-20",
+  147	      "created": "2026-05-20",
+  148	      "id": "X10",
+  149	      "notes": "",
+  150	      "refs": [
+  151	        "docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md",
+  152	        "docs/reviewer/x10-verdict-parser-claude-formatting-design-spec",
+  153	        "docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md"
+  154	      ],
+  155	      "started": null,
+  156	      "status": "done",
+  157	      "title": "Harden external-review verdict parser and prompt against Claude formatting variants"
+  158	    },
+  159	    {
+  160	      "closed": null,
+  161	      "created": "2026-05-20",
+  162	      "id": "X11",
+  163	      "notes": "",
+  164	      "refs": [
+  165	        "docs/specs/2026-05-20-X11-global-external-reviewer-bridge-design.md",
+  166	        "docs/reviewer/x11-global-external-reviewer-bridge-design-spec",
+  167	        "docs/plans/2026-05-20-X11-global-external-reviewer-bridge.md",
+  168	        "docs/reviewer/x11-global-external-reviewer-bridge-plan",
+  169	        "docs/handoffs/2026-05-20-X11-global-external-reviewer-bridge-prompt.md"
+  170	      ],
+  171	      "started": null,
+  172	      "status": "ready",
+  173	      "title": "Make external-review bridge global"
+  174	    },
+  175	    {
+  176	      "closed": null,
+  177	      "created": "2026-05-20",
+  178	      "id": "X12",
+  179	      "notes": "",
+  180	      "refs": [
+  181	        "docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md",
+  182	        "docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md"
+  183	      ],
+  184	      "started": null,
+  185	      "status": "ready",
+  186	      "title": "tasktool: require authoritative-checkout routing for mutations"
+  187	    }
+  188	  ],
+  189	  "last_reviewed": "2026-05-18",
+  190	  "north_star": "",
+  191	  "phases": [
+  192	    {
+  193	      "closed": "2026-05-17",
+  194	      "created": "2026-05-17",
+  195	      "id": "P1",
+  196	      "notes": "",
+  197	      "phase_reviewer_chain": null,
+  198	      "plan_path": null,
+  199	      "planning_path": null,
+  200	      "slices": [],
+
+[truncated: 9 additional lines]
+
+<!-- superstar-prompt:end -->
\ No newline at end of file
diff --git a/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/r1-2026-05-20T1509-primary-response.md b/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/r1-2026-05-20T1509-primary-response.md
new file mode 100644
index 0000000..7cd199d
--- /dev/null
+++ b/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/r1-2026-05-20T1509-primary-response.md
@@ -0,0 +1,119 @@
+# Review — 2026-05-20-X12-tasktool-require-authoritative-routing.md (post-slice, round 1)
+
+- Target: `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md`
+- Request: `docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/r1-2026-05-20T1509-primary-request.md`
+- Reviewer command: `reviewer-agent`
+- Reviewer provider: `codex`
+- Sandbox: repo read-only; scratch/output writable
+- Status: `ok`
+
+---
+
+1. Findings
+
+F1 - Severity: blocking  
+`PYTHONPATH=tools pytest tools/tasktool/tests/ -q` fails: `tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_writes_project_config` expects `.tasktool/config.json` under the test `cwd`, but it is not written there. This violates the plan’s final gate at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888-1894`. The likely trigger is `_find_repo_root()` selecting an ancestor with `.git` at `tools/tasktool/cli.py:8-12`; in this review environment `/tmp/.git` exists, so the config is written to `/tmp/.tasktool/config.json` instead of the test tmpdir. Test expectation is at `tools/tasktool/tests/test_cli_integration.py:380-388`.
+
+F2 - Severity: blocking  
+X12 is not lifecycle-started for a post-slice gate. `docs/tasklist.json:176-185` still has `started: null` and `status: ready`, while the plan explicitly requires `tasktool start X12` at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:19-25` and later says to leave the row `in_progress` before post-slice review at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1896-1898`. `./tools/tasktool/tasktool show X12` confirms `status: ready`.
+
+F3 - Severity: important  
+`config migrate-from-local --accept-authoritative` returns before the lock/re-read/exit-summary path. `tools/tasktool/commands.py:289-290` exits immediately after printing the initial diff. The spec requires acquiring `tasktool_lock`, re-reading authoritative state inside the lock, and printing a one-line summary at `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md:107-109`. This leaves the verification-mode semantics weaker than specified and untested for concurrent/stale authoritative state.
+
+2. Open questions / assumptions
+
+Was the full tasktool suite previously run in an environment without `/tmp/.git`? If so, that evidence is environment-sensitive and should not be used as the only closeout proof.
+
+3. Suggested document edits
+
+Update the plan/evidence section to record the actual verification command output, including the failing test if this review result is accepted. Do not mark X12 close-ready until the task row is moved to `in_progress` and the suite is green.
+
+4. Verification gaps / commands that should be run
+
+Run:
+
+```bash
+PYTHONPATH=tools pytest tools/tasktool/tests/ -q
+./tools/tasktool/tasktool show X12
+./tools/tasktool/tasktool validate
+```
+
+I ran those here: `validate` passes, but the full tasktool suite fails as described above, and X12 remains `ready`.
+
+Overall verdict: revise
+
+
+1. Findings
+
+F1 - Severity: blocking  
+`PYTHONPATH=tools pytest tools/tasktool/tests/ -q` fails: `tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_writes_project_config` expects `.tasktool/config.json` under the test `cwd`, but it is not written there. This violates the plan’s final gate at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1888-1894`. The likely trigger is `_find_repo_root()` selecting an ancestor with `.git` at `tools/tasktool/cli.py:8-12`; in this review environment `/tmp/.git` exists, so the config is written to `/tmp/.tasktool/config.json` instead of the test tmpdir. Test expectation is at `tools/tasktool/tests/test_cli_integration.py:380-388`.
+
+F2 - Severity: blocking  
+X12 is not lifecycle-started for a post-slice gate. `docs/tasklist.json:176-185` still has `started: null` and `status: ready`, while the plan explicitly requires `tasktool start X12` at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:19-25` and later says to leave the row `in_progress` before post-slice review at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1896-1898`. `./tools/tasktool/tasktool show X12` confirms `status: ready`.
+
+F3 - Severity: important  
+`config migrate-from-local --accept-authoritative` returns before the lock/re-read/exit-summary path. `tools/tasktool/commands.py:289-290` exits immediately after printing the initial diff. The spec requires acquiring `tasktool_lock`, re-reading authoritative state inside the lock, and printing a one-line summary at `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md:107-109`. This leaves the verification-mode semantics weaker than specified and untested for concurrent/stale authoritative state.
+
+2. Open questions / assumptions
+
+Was the full tasktool suite previously run in an environment without `/tmp/.git`? If so, that evidence is environment-sensitive and should not be used as the only closeout proof.
+
+3. Suggested document edits
+
+Update the plan/evidence section to record the actual verification command output, including the failing test if this review result is accepted. Do not mark X12 close-ready until the task row is moved to `in_progress` and the suite is green.
+
+4. Verification gaps / commands that should be run
+
+Run:
+
+```bash
+PYTHONPATH=tools pytest tools/tasktool/tests/ -q
+./tools/tasktool/tasktool show X12
+./tools/tasktool/tasktool validate
+```
+
+I ran those here: `validate` passes, but the full tasktool suite fails as described above, and X12 remains `ready`.
+
+Overall verdict: revise
+
+---
+
+## Reviewer stderr (tail)
+
+```text
+fig.json` instead of the test tmpdir. Test expectation is at `tools/tasktool/tests/test_cli_integration.py:380-388`.
+
+F2 - Severity: blocking  
+X12 is not lifecycle-started for a post-slice gate. `docs/tasklist.json:176-185` still has `started: null` and `status: ready`, while the plan explicitly requires `tasktool start X12` at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:19-25` and later says to leave the row `in_progress` before post-slice review at `docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md:1896-1898`. `./tools/tasktool/tasktool show X12` confirms `status: ready`.
+
+F3 - Severity: important  
+`config migrate-from-local --accept-authoritative` returns before the lock/re-read/exit-summary path. `tools/tasktool/commands.py:289-290` exits immediately after printing the initial diff. The spec requires acquiring `tasktool_lock`, re-reading authoritative state inside the lock, and printing a one-line summary at `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md:107-109`. This leaves the verification-mode semantics weaker than specified and untested for concurrent/stale authoritative state.
+
+2. Open questions / assumptions
+
+Was the full tasktool suite previously run in an environment without `/tmp/.git`? If so, that evidence is environment-sensitive and should not be used as the only closeout proof.
+
+3. Suggested document edits
+
+Update the plan/evidence section to record the actual verification command output, including the failing test if this review result is accepted. Do not mark X12 close-ready until the task row is moved to `in_progress` and the suite is green.
+
+4. Verification gaps / commands that should be run
+
+Run:
+
+```bash
+PYTHONPATH=tools pytest tools/tasktool/tests/ -q
+./tools/tasktool/tasktool show X12
+./tools/tasktool/tasktool validate
+```
+
+I ran those here: `validate` passes, but the full tasktool suite fails as described above, and X12 remains `ready`.
+
+Overall verdict: revise
+
+
+hook: Stop
+hook: Stop Completed
+tokens used
+100,049
+```
diff --git a/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/r1-2026-05-20T1509-sweep1-request.md b/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/r1-2026-05-20T1509-sweep1-request.md
new file mode 100644
index 0000000..4ca7ae0
--- /dev/null
+++ b/docs/reviewer/x12-tasktool-require-authoritative-routing-X12-post-slice/r1-2026-05-20T1509-sweep1-request.md
@@ -0,0 +1,1072 @@
+<!-- superstar-prompt:start -->
+You are acting as an independent senior engineering reviewer.
+
+Review stance:
+- Lead with findings, ordered by severity.
+- Focus on correctness, consistency, implementation risk, missing acceptance
+  gates, vague handoffs, ungrounded assumptions, unverified claims, and drift
+  from the codebase.
+- Give exact file/line references when possible.
+- If the document is sound, say that clearly and list residual risks.
+- Keep the review actionable. Avoid broad rewrites unless the current structure
+  creates concrete risk.
+
+Repository root:
+/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority
+
+Target kind:
+post-slice
+
+Review mode:
+Post-slice review. Treat this as a completion gate for one
+slice of work. Compare the completed changes and stated evidence against the
+slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
+untracked artifacts, missing tests, failing or skipped verification, broken
+cross-site behavior, and claims not supported by the repo state.
+
+Target document:
+docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md
+
+Additional context files:
+- docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md
+- docs/tasklist.json
+
+Review output contract:
+1. Findings
+   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
+     stable if this review is iterated in subsequent rounds.
+   - Mark severity inline: `Severity: blocking | important | minor | nit`.
+2. Open questions / assumptions
+3. Suggested document edits
+4. Verification gaps / commands that should be run, if any
+
+End your review with this exact line, as plain text on its own line:
+
+    Overall verdict: <ready|ready with small edits|revise>
+
+Do not bold, italicise, prefix with `##`, split across lines, or drop the
+word "Overall". Do not write `**Verdict: ready**` or place the value on a
+new line after a heading.
+
+Read the files from disk. Do not rely only on the snippets in this prompt.
+
+
+## Target Preview
+
+### docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md
+
+    1	# X12 — tasktool: require authoritative-checkout routing for mutations — Implementation Plan
+    2	
+    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
+    4	
+    5	**Goal:** Make authoritative-checkout routing structurally required for mutating tasktool commands so the AGS sidebar widget, TTS announcements, and on-disk source-of-truth cannot diverge silently; add a `migrate-from-local` subcommand for reconciling drift, and an `init-local` subcommand for the explicit opt-out.
+    6	
+    7	**Architecture:** Three production-code changes in `tools/tasktool/`: (1) `config.py` gains a `MutationModeUnconfigured` sentinel so `load_config` distinguishes "no config file" from "config says local"; (2) `commands.py:_resolve_write_root` raises `CommandError` on the mutation path when unconfigured, and gains `cmd_config_init_local` + `cmd_config_migrate_from_local`; (3) `cli.py` registers two new `config` subcommands. The migrator walks `dataclasses.fields()` on every row type in `tools/tasktool/model.py` so adding fields to the model cannot silently drop them from migration. Three skills under `skills/` are tightened from conditional to required wording.
+    8	
+    9	**Tech Stack:** Python 3.11 (slots dataclasses, `dataclasses.fields()` introspection), pytest, existing `tasktool_lock` and `validate_authoritative_checkout` helpers in `tools/tasktool/worktree.py`.
+   10	
+   11	**Spec:** `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md`
+   12	
+   13	**Tasktool row:** X12 (cross-cutting). Confirmed via `tasktool show X12` (status=ready, refs spec).
+   14	
+   15	---
+   16	
+   17	## Lifecycle start
+   18	
+   19	- [ ] **Step 0: Mark X12 in progress**
+   20	
+   21	```bash
+   22	./tools/tasktool/tasktool start X12
+   23	```
+   24	
+   25	Expected: exit 0; `tasktool show X12` reports `status: in_progress` with a `started:` date.
+   26	
+   27	---
+   28	
+   29	## File structure
+   30	
+   31	Files created in this slice:
+   32	- `tools/tasktool/migrate.py` — pure-Python diff/merge over the model dataclass tree. New module so `commands.py` stays focused on CLI command bodies and the migrator's row-walking logic has its own home.
+   33	- `tools/tasktool/tests/test_migrate.py` — unit tests for the migrator (diff, dataclass coverage, conflict handling).
+   34	- `tools/tasktool/tests/test_unconfigured_mutation.py` — tests for the hard-error behaviour.
+   35	- `tools/tasktool/tests/test_init_local.py` — tests for the `init-local` CLI subcommand.
+   36	- `tools/tasktool/tests/test_migrate_cli.py` — CLI integration tests for `config migrate-from-local`.
+   37	
+   38	Files modified in this slice:
+   39	- `tools/tasktool/config.py` — new sentinel and `is_authoritative_required` predicate; `load_config` returns sentinel when no file.
+   40	- `tools/tasktool/commands.py` — `_resolve_write_root` hard-error path; new `cmd_config_init_local` and `cmd_config_migrate_from_local`.
+   41	- `tools/tasktool/cli.py` — register `config init-local` and `config migrate-from-local` subparsers.
+   42	- `tools/tasktool/tests/test_authority_config.py` — replace `test_missing_config_defaults_to_local` (no longer true) with `test_missing_config_returns_unconfigured`.
+   43	- `tools/tasktool/tests/test_cli_integration.py` — any existing tests that relied on the implicit-`local` default get an explicit `init-local` or `init-authority` setup line.
+   44	- `skills/project-setup/SKILL.md` — order change + setup-precondition for missing authority config.
+   45	- `skills/tasklist-discipline/SKILL.md` — promote routing from optional to required; add remediation pointer.
+   46	- `skills/using-git-worktrees/SKILL.md` — remove "if configured" conditional.
+   47	
+   48	---
+   49	
+   50	## Task 1: Distinguish "unconfigured" from "explicit local" in config.py
+   51	
+   52	**Files:**
+   53	- Modify: `tools/tasktool/config.py`
+   54	- Modify: `tools/tasktool/tests/test_authority_config.py`
+   55	
+   56	- [ ] **Step 1: Add the failing test for the sentinel**
+   57	
+   58	Edit `tools/tasktool/tests/test_authority_config.py`. Replace the existing `test_missing_config_defaults_to_local` function with:
+   59	
+   60	```python
+   61	def test_missing_config_returns_unconfigured(tmp_path):
+   62	    cfg = load_config(tmp_path)
+   63	    assert cfg.tasklist.mutation_mode == "unconfigured"
+   64	    assert is_authoritative_required(cfg) is True
+   65	
+   66	
+   67	def test_explicit_local_is_configured(tmp_path):
+   68	    (tmp_path / ".tasktool").mkdir()
+   69	    (tmp_path / ".tasktool" / "config.json").write_text(
+   70	        '{"schema_version":1,"tasklist":{"mutation_mode":"local","authoritative_branch":"main"}}'
+   71	    )
+   72	    cfg = load_config(tmp_path)
+   73	    assert cfg.tasklist.mutation_mode == "local"
+   74	    assert is_authoritative_required(cfg) is False
+   75	
+   76	
+   77	def test_authoritative_mode_does_not_require_init(tmp_path):
+   78	    (tmp_path / ".tasktool").mkdir()
+   79	    (tmp_path / ".tasktool" / "config.json").write_text(
+   80	        '{"schema_version":1,"tasklist":{"mutation_mode":"authoritative-checkout","authoritative_branch":"main"}}'
+   81	    )
+   82	    cfg = load_config(tmp_path)
+   83	    assert is_authoritative_required(cfg) is False
+   84	
+   85	
+   86	def test_config_with_omitted_mutation_mode_is_unconfigured(tmp_path):
+   87	    """A config file present but lacking mutation_mode must NOT silently
+   88	    default to local. It is treated identically to a missing file."""
+   89	    (tmp_path / ".tasktool").mkdir()
+   90	    (tmp_path / ".tasktool" / "config.json").write_text(
+   91	        '{"schema_version":1,"tasklist":{}}'
+   92	    )
+   93	    cfg = load_config(tmp_path)
+   94	    assert cfg.tasklist.mutation_mode == "unconfigured"
+   95	    assert is_authoritative_required(cfg) is True
+   96	```
+   97	
+   98	Add `is_authoritative_required` to the import line:
+   99	
+  100	```python
+  101	from tasktool.config import (
+  102	    DEFAULT_CONFIG_REL,
+  103	    TasklistConfig,
+  104	    TasktoolConfig,
+  105	    is_authoritative_required,
+  106	    load_config,
+  107	    save_config,
+  108	)
+  109	```
+  110	
+  111	- [ ] **Step 2: Run the test to verify it fails**
+  112	
+  113	```bash
+  114	PYTHONPATH=tools pytest tools/tasktool/tests/test_authority_config.py -v
+  115	```
+  116	
+  117	Expected: ImportError or `mutation_mode == "local"` assertion failure (the sentinel and predicate don't exist yet).
+  118	
+  119	- [ ] **Step 3: Add the sentinel + predicate to config.py**
+  120	
+  121	Edit `tools/tasktool/config.py`. Replace the existing module body with:
+  122	
+  123	```python
+  124	from __future__ import annotations
+  125	
+  126	import json
+  127	from dataclasses import dataclass, field
+  128	from pathlib import Path
+  129	
+  130	DEFAULT_CONFIG_REL = Path(".tasktool/config.json")
+  131	
+  132	# Sentinel returned when no .tasktool/config.json exists. Distinguishes
+  133	# "operator never configured this repo" from "operator explicitly chose local".
+  134	UNCONFIGURED = "unconfigured"
+  135	
+  136	VALID_MUTATION_MODES = {"local", "authoritative-checkout"}
+  137	
+  138	
+  139	@dataclass(frozen=True)
+  140	class TasklistConfig:
+  141	    mutation_mode: str = UNCONFIGURED
+  142	    authoritative_branch: str = "main"
+  143	
+  144	
+  145	@dataclass(frozen=True)
+  146	class TasktoolConfig:
+  147	    schema_version: int = 1
+  148	    tasklist: TasklistConfig = field(default_factory=TasklistConfig)
+  149	
+  150	
+  151	def _parse_tasklist(raw: dict) -> TasklistConfig:
+  152	    if "mutation_mode" not in raw:
+  153	        # Config file exists but omits mutation_mode — treat as unconfigured,
+  154	        # the same way a missing config file is treated. Operators must opt in.
+  155	        return TasklistConfig(
+  156	            mutation_mode=UNCONFIGURED,
+  157	            authoritative_branch=raw.get("authoritative_branch", "main"),
+  158	        )
+  159	    mode = raw["mutation_mode"]
+  160	    if mode not in VALID_MUTATION_MODES:
+  161	        raise ValueError(f"unknown mutation_mode: {mode}")
+  162	    return TasklistConfig(
+  163	        mutation_mode=mode,
+  164	        authoritative_branch=raw.get("authoritative_branch", "main"),
+  165	    )
+  166	
+  167	
+  168	def load_config(repo_root: Path) -> TasktoolConfig:
+  169	    path = repo_root / DEFAULT_CONFIG_REL
+  170	    if not path.exists():
+  171	        return TasktoolConfig()  # default field gives UNCONFIGURED
+  172	    raw = json.loads(path.read_text(encoding="utf-8"))
+  173	    if raw.get("schema_version", 1) != 1:
+  174	        raise ValueError(f"unsupported tasktool config schema_version: {raw.get('schema_version')}")
+  175	    return TasktoolConfig(
+  176	        schema_version=1,
+  177	        tasklist=_parse_tasklist(raw.get("tasklist", {})),
+  178	    )
+  179	
+  180	
+  181	def save_config(repo_root: Path, cfg: TasktoolConfig) -> None:
+  182	    path = repo_root / DEFAULT_CONFIG_REL
+  183	    path.parent.mkdir(parents=True, exist_ok=True)
+  184	    body = {
+  185	        "schema_version": cfg.schema_version,
+  186	        "tasklist": {
[truncated: 1388 additional lines]


---

You are acting as an independent senior engineering reviewer.

Review stance:
- Lead with findings, ordered by severity.
- Focus on correctness, consistency, implementation risk, missing acceptance
  gates, vague handoffs, ungrounded assumptions, unverified claims, and drift
  from the codebase.
- Give exact file/line references when possible.
- If the document is sound, say that clearly and list residual risks.
- Keep the review actionable. Avoid broad rewrites unless the current structure
  creates concrete risk.

Repository root:
/home/simon/Dev/sigreer/skills/superstar/.worktrees/x12-tasktool-authority

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md

Additional context files:
- docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md
- /home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json

Review output contract:
1. Findings
   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
     stable if this review is iterated in subsequent rounds.
   - Mark severity inline: `Severity: blocking | important | minor | nit`.
2. Open questions / assumptions
3. Suggested document edits
4. Verification gaps / commands that should be run, if any

End your review with this exact line, as plain text on its own line:

    Overall verdict: <ready|ready with small edits|revise>

Do not bold, italicise, prefix with `##`, split across lines, or drop the
word "Overall". Do not write `**Verdict: ready**` or place the value on a
new line after a heading.

Read the files from disk. Do not rely only on the snippets in this prompt.


## Target Preview

### docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md

    1	# X12 — tasktool: require authoritative-checkout routing for mutations — Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Make authoritative-checkout routing structurally required for mutating tasktool commands so the AGS sidebar widget, TTS announcements, and on-disk source-of-truth cannot diverge silently; add a `migrate-from-local` subcommand for reconciling drift, and an `init-local` subcommand for the explicit opt-out.
    6	
    7	**Architecture:** Three production-code changes in `tools/tasktool/`: (1) `config.py` gains a `MutationModeUnconfigured` sentinel so `load_config` distinguishes "no config file" from "config says local"; (2) `commands.py:_resolve_write_root` raises `CommandError` on the mutation path when unconfigured, and gains `cmd_config_init_local` + `cmd_config_migrate_from_local`; (3) `cli.py` registers two new `config` subcommands. The migrator walks `dataclasses.fields()` on every row type in `tools/tasktool/model.py` so adding fields to the model cannot silently drop them from migration. Three skills under `skills/` are tightened from conditional to required wording.
    8	
    9	**Tech Stack:** Python 3.11 (slots dataclasses, `dataclasses.fields()` introspection), pytest, existing `tasktool_lock` and `validate_authoritative_checkout` helpers in `tools/tasktool/worktree.py`.
   10	
   11	**Spec:** `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md`
   12	
   13	**Tasktool row:** X12 (cross-cutting). Current lifecycle state is routed through the authoritative checkout at `/home/simon/Dev/sigreer/skills/superstar`; `./tools/tasktool/tasktool show X12` there reports `status: in_progress`, `started: 2026-05-20`, with refs to this spec and plan. The implementation worktree's checked-out `docs/tasklist.json` can be stale by design and is not the lifecycle source of truth for this routed slice.
   14	
   15	---
   16	
   17	## Lifecycle start
   18	
   19	- [x] **Step 0: Mark X12 in progress**
   20	
   21	```bash
   22	./tools/tasktool/tasktool start X12
   23	```
   24	
   25	Expected: exit 0; `tasktool show X12` reports `status: in_progress` with a `started:` date.
   26	
   27	Evidence: verified from the authoritative checkout with `./tools/tasktool/tasktool show X12`: status `in_progress`, started `2026-05-20`.
   28	
   29	---
   30	
   31	## File structure
   32	
   33	Files created in this slice:
   34	- `tools/tasktool/migrate.py` — pure-Python diff/merge over the model dataclass tree. New module so `commands.py` stays focused on CLI command bodies and the migrator's row-walking logic has its own home.
   35	- `tools/tasktool/tests/test_migrate.py` — unit tests for the migrator (diff, dataclass coverage, conflict handling).
   36	- `tools/tasktool/tests/test_unconfigured_mutation.py` — tests for the hard-error behaviour.
   37	- `tools/tasktool/tests/test_init_local.py` — tests for the `init-local` CLI subcommand.
   38	- `tools/tasktool/tests/test_migrate_cli.py` — CLI integration tests for `config migrate-from-local`.
   39	
   40	Files modified in this slice:
   41	- `tools/tasktool/config.py` — new sentinel and `is_authoritative_required` predicate; `load_config` returns sentinel when no file.
   42	- `tools/tasktool/commands.py` — `_resolve_write_root` hard-error path; new `cmd_config_init_local` and `cmd_config_migrate_from_local`.
   43	- `tools/tasktool/cli.py` — register `config init-local` and `config migrate-from-local` subparsers.
   44	- `tools/tasktool/tests/test_authority_config.py` — replace `test_missing_config_defaults_to_local` (no longer true) with `test_missing_config_returns_unconfigured`.
   45	- `tools/tasktool/tests/test_cli_integration.py` — any existing tests that relied on the implicit-`local` default get an explicit `init-local` or `init-authority` setup line.
   46	- `skills/project-setup/SKILL.md` — order change + setup-precondition for missing authority config.
   47	- `skills/tasklist-discipline/SKILL.md` — promote routing from optional to required; add remediation pointer.
   48	- `skills/using-git-worktrees/SKILL.md` — remove "if configured" conditional.
   49	
   50	---
   51	
   52	## Task 1: Distinguish "unconfigured" from "explicit local" in config.py
   53	
   54	**Files:**
   55	- Modify: `tools/tasktool/config.py`
   56	- Modify: `tools/tasktool/tests/test_authority_config.py`
   57	
   58	- [x] **Step 1: Add the failing test for the sentinel**
   59	
   60	Edit `tools/tasktool/tests/test_authority_config.py`. Replace the existing `test_missing_config_defaults_to_local` function with:
   61	
   62	```python
   63	def test_missing_config_returns_unconfigured(tmp_path):
   64	    cfg = load_config(tmp_path)
   65	    assert cfg.tasklist.mutation_mode == "unconfigured"
   66	    assert is_authoritative_required(cfg) is True
   67	
   68	
   69	def test_explicit_local_is_configured(tmp_path):
   70	    (tmp_path / ".tasktool").mkdir()
   71	    (tmp_path / ".tasktool" / "config.json").write_text(
   72	        '{"schema_version":1,"tasklist":{"mutation_mode":"local","authoritative_branch":"main"}}'
   73	    )
   74	    cfg = load_config(tmp_path)
   75	    assert cfg.tasklist.mutation_mode == "local"
   76	    assert is_authoritative_required(cfg) is False
   77	
   78	
   79	def test_authoritative_mode_does_not_require_init(tmp_path):
   80	    (tmp_path / ".tasktool").mkdir()
   81	    (tmp_path / ".tasktool" / "config.json").write_text(
   82	        '{"schema_version":1,"tasklist":{"mutation_mode":"authoritative-checkout","authoritative_branch":"main"}}'
   83	    )
   84	    cfg = load_config(tmp_path)
   85	    assert is_authoritative_required(cfg) is False
   86	
   87	
   88	def test_config_with_omitted_mutation_mode_is_unconfigured(tmp_path):
   89	    """A config file present but lacking mutation_mode must NOT silently
   90	    default to local. It is treated identically to a missing file."""
   91	    (tmp_path / ".tasktool").mkdir()
   92	    (tmp_path / ".tasktool" / "config.json").write_text(
   93	        '{"schema_version":1,"tasklist":{}}'
   94	    )
   95	    cfg = load_config(tmp_path)
   96	    assert cfg.tasklist.mutation_mode == "unconfigured"
   97	    assert is_authoritative_required(cfg) is True
   98	```
   99	
  100	Add `is_authoritative_required` to the import line:
  101	
  102	```python
  103	from tasktool.config import (
  104	    DEFAULT_CONFIG_REL,
  105	    TasklistConfig,
  106	    TasktoolConfig,
  107	    is_authoritative_required,
  108	    load_config,
  109	    save_config,
  110	)
  111	```
  112	
  113	- [x] **Step 2: Run the test to verify it fails**
  114	
  115	```bash
  116	PYTHONPATH=tools pytest tools/tasktool/tests/test_authority_config.py -v
  117	```
  118	
  119	Expected: ImportError or `mutation_mode == "local"` assertion failure (the sentinel and predicate don't exist yet).
  120	
  121	- [x] **Step 3: Add the sentinel + predicate to config.py**
  122	
  123	Edit `tools/tasktool/config.py`. Replace the existing module body with:
  124	
  125	```python
  126	from __future__ import annotations
  127	
  128	import json
  129	from dataclasses import dataclass, field
  130	from pathlib import Path
  131	
  132	DEFAULT_CONFIG_REL = Path(".tasktool/config.json")
  133	
  134	# Sentinel returned when no .tasktool/config.json exists. Distinguishes
  135	# "operator never configured this repo" from "operator explicitly chose local".
  136	UNCONFIGURED = "unconfigured"
  137	
  138	VALID_MUTATION_MODES = {"local", "authoritative-checkout"}
  139	
  140	
  141	@dataclass(frozen=True)
  142	class TasklistConfig:
  143	    mutation_mode: str = UNCONFIGURED
  144	    authoritative_branch: str = "main"
  145	
  146	
  147	@dataclass(frozen=True)
  148	class TasktoolConfig:
  149	    schema_version: int = 1
  150	    tasklist: TasklistConfig = field(default_factory=TasklistConfig)

[truncated: 1773 additional lines]

<!-- superstar-prompt:end -->