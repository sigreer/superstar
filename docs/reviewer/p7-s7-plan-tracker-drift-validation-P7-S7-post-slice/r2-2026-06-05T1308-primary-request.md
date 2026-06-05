<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 2 of p7-s7-plan-tracker-drift-validation-P7-S7-post-slice.

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
| 1 | revise | 2 | 0 |

## Prior-round findings

Source: merged findings from r1 (authoritative)

# Merged findings for r1

## Primary

# Review — 2026-06-05-P7-S7-plan-tracker-drift-validation.md (post-slice, round 1)

- Target: `docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md`
- Request: `docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/r1-2026-06-05T1257-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: important  
`tasktool validate --format json` does not meet the plan’s live-tracker smoke expectation. The plan expects `ok: true`, rc 0, and empty `warnings` at [docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared/docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md:511). Fresh output is `ok: true` but includes `P7.S5.refs: path does not exist: docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice`. This is not an S7 surface-drift regression, but it means the stated acceptance command is not clean and should be reconciled or explicitly documented as unrelated pre-existing repo drift before closeout.

F2 — Severity: important  
Post-slice review artifacts are untracked and not registered on the S7 row. `git status --short --untracked-files=all` shows untracked files under `docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/`, while `docs/tasklist.json` still has `reviewer_chain` pointing at the plan-review chain at [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared/docs/tasklist.json:454). That is expected during the review itself, but it is not ready for final slice closeout until the post-slice chain is committed/registered.

2. Open questions / assumptions

I assume the P7.S5 missing reviewer-chain warning is unrelated existing repo drift, not introduced by S7. If so, the S7 closeout should either fix the missing tracked ref or record that the S7 acceptance is “no S7 drift warnings” rather than “empty warnings”.

3. Suggested document edits

Update the plan’s Task 3/DoD smoke wording to distinguish “no surface-drift warnings” from “no warnings at all”, unless the intended gate really is a globally clean `tasktool validate --format json`.

4. Verification gaps / commands that should be run

Fresh checks run:
`cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q` → 15 passed.  
`cd tools/tasktool && python -m pytest -q` → 789 passed.  
`tasktool validate --no-path-warnings --format json` → `ok: true`, no warnings.  
`tasktool validate --format json` → `ok: true`, one P7.S5 path warning.  
`git diff --check 65acbcb..HEAD` → clean.

Overall verdict: revise


## Sweep 1

# Review — 2026-06-05-P7-S7-plan-tracker-drift-validation.md (post-slice, round 1)

- Target: `docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md`
- Request: `docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/r1-2026-06-05T1257-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings
S1.F1. Severity: important — The live tracker does not satisfy the plan’s plain-validate smoke expectation. [docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared/docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md:513) expects `tasktool validate --format json` to return empty `warnings`, but the current repo returns:
`P7.S5.refs: path does not exist: docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice`.
The stale ref is in [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared/docs/tasklist.json:386), and the matching directory is absent. This is not a P7.S7 surface-drift warning, but it means the stated live-tracker smoke output is not true as written.

2. Open questions / assumptions
I assume P7.S7 is intentionally still `in_progress` until this post-slice review passes; the row is ratified and has `integration_surfaces: ["validate"]` at [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared/docs/tasklist.json:440).

3. Suggested document edits
Either fix the stale P7.S5 reviewer ref / restore the missing reviewer directory, or amend the closeout evidence to state that plain validate currently has one unrelated path warning while the P7.S7 acceptance signal is “no `surfaces` / `reservations` / `parallel_group` drift warnings and rc 0.”

4. Verification gaps / commands that should be run
I ran:
`cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q` — 15 passed.
`cd tools/tasktool && python -m pytest tests/test_validate.py tests/test_commands.py -q` — 265 passed.
`cd tools/tasktool && python -m pytest -q` — 789 passed.
`tasktool validate --no-path-warnings --format json` — clean.
`tasktool validate --format json` — rc 0 / ok true, but one unrelated P7.S5 path warning.

Overall verdict: ready with small edits



## Resolution report for prior round

# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md:513-514` (Task 3, Step 7 `Expected:` line) and `docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md:582` (Definition of done second bullet).
- Verification: `tasktool validate --format json` → `{"ok": true, "errors": [], "warnings": ["P7.S5.refs: path does not exist: docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice"]}` — ok:true, rc 0, only warning is the unrelated P7.S5 path warning (no surfaces/reservations/parallel_group drift warning); `tasktool validate --no-path-warnings --format json` → `{"ok": true, "errors": [], "warnings": []}` — ok:true, empty warnings.

Notes:
Reconciled Step 7's opening `Expected:` from "empty warnings" to "no surfaces/reservations/parallel_group drift warnings" and added an explicit sentence calling out the pre-existing P7.S5 path warning (`P7.S5.refs: path does not exist: docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice`) as unrelated P7.S5 drift (uncommitted reviewer-chain directory) that is out of S7 scope and not a surface-drift warning. This makes the headline consistent with the detailed acceptance bar already present two sentences later. The Definition of Done bullet was also tightened to state that both invocations return ok:true with no S7 surface-drift warnings, and to name the pre-existing P7.S5 warning explicitly. No code, tests, or tracker changes were made; fixing the P7.S5 stale ref would breach the S7 slice boundary.

## S1.F1
Status: fixed
Notes:
Same root cause as F1 — the sweep reviewer's S1.F1 is a duplicate of the same finding (the "empty warnings" over-promise in Task 3 Step 7). Resolved by the identical plan-wording reconciliation described under F1. No additional changes required.

## F2
Status: waived
Notes:
The untracked post-slice reviewer-chain folder (`docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/`) and the `reviewer_chain` pointer in `docs/tasklist.json` (which still points at the plan-review chain) are the expected mid-review state, as the reviewer itself acknowledged ("this is normal during the review itself"). They are resolved by the standard slice-closeout step: the coordinator commits the post-slice chain folder and runs `tasktool close P7.S7`, which registers the post-slice chain. This is performed AFTER this review round passes. No code or plan change is warranted; nothing in the artifact set needs to change for F2.


## Changes since prior round

Worktree status: dirty

### git diff base..HEAD

diff --git a/docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md b/docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md
index a8e9d71..2826bc5 100644
--- a/docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md
+++ b/docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md
@@ -511,7 +511,7 @@ Expected: PASS (no regressions; existing `validate` tests unaffected because cle
 - [ ] **Step 7: Manual smoke check against the live tracker**
 
 Run: `tasktool validate --format json`
-Expected: `ok: true`, `rc 0`, **empty `warnings`**. The full S7 planning package (spec, plan, handoff) and S7's own `validate` surface declaration (Task 5) all exist, so there are no S7 path warnings. The live tracker's only `parallel_group` slices (P7.S2, P7.S4, `group=core-after-model`) are terminal (`done`), so Check 1 skips them, and S7's plan mentions every surface/reservation it declares, so Check 2 is silent. The acceptance bar is: **no `surfaces`/`reservations`/`parallel_group` drift warnings, and `rc 0`** (drift is never an error). If a surface-drift warning does appear, it is genuine drift — reconcile the tracker or plan before closing the slice. (Note: if Task 5's surface declaration has not yet run when you spot-check mid-implementation, S7 will not warn — it has no `parallel_group` and an empty surface list — so this remains clean throughout.)
+Expected: `ok: true`, `rc 0`, and **no `surfaces`/`reservations`/`parallel_group` drift warnings**. The live tracker currently emits one unrelated, pre-existing path warning — `P7.S5.refs: path does not exist: docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice` — which originates from an uncommitted P7.S5 reviewer-chain directory; this is outside S7 scope and is NOT a surface-drift warning. The full S7 planning package (spec, plan, handoff) and S7's own `validate` surface declaration (Task 5) all exist, so there are no S7 path warnings. The live tracker's only `parallel_group` slices (P7.S2, P7.S4, `group=core-after-model`) are terminal (`done`), so Check 1 skips them, and S7's plan mentions every surface/reservation it declares, so Check 2 is silent. The acceptance bar is: **no `surfaces`/`reservations`/`parallel_group` drift warnings, and `rc 0`** (drift is never an error). If a surface-drift warning does appear, it is genuine drift — reconcile the tracker or plan before closing the slice. (Note: if Task 5's surface declaration has not yet run when you spot-check mid-implementation, S7 will not warn — it has no `parallel_group` and an empty surface list — so this remains clean throughout.)
 
 - [ ] **Step 8: Commit**
 
@@ -579,7 +579,7 @@ git commit -m "P7.S7: declare validate surface + ratify drift-validation slice"
 - `find_surface_drift_warnings` exists in `validate.py` with the binding signature and both checks (spec §4.A–§4.C).
 - `tasktool validate` emits Check 1 always and Check 2 only when plan files are in scope (`not no_path_warnings`); neither changes the exit code (spec §4.D).
 - All new tests in `SurfaceDriftWarningTests` pass; the full `tools/tasktool` suite is green.
-- `tasktool validate` and `tasktool validate --no-path-warnings` both return `ok: true` against the live tracker.
+- `tasktool validate` and `tasktool validate --no-path-warnings` both return `ok: true` against the live tracker, with **no S7 surface-drift warnings**. The `--no-path-warnings` invocation is fully clean (empty warnings); the plain invocation has only the unrelated pre-existing P7.S5 path warning (`P7.S5.refs: path does not exist: docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice`), which is outside S7 scope.
 - No `model.py`/`serialize.py`/`migrate.py`/schema/CLI changes (spec §4.E, §6).
 - The slice is ratified.
 
diff --git a/docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/r1-resolution.md b/docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/r1-resolution.md
new file mode 100644
index 0000000..6f1be54
--- /dev/null
+++ b/docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/r1-resolution.md
@@ -0,0 +1,20 @@
+# Resolution for r1
+
+## F1
+Status: fixed
+Evidence:
+- Files: `docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md:513-514` (Task 3, Step 7 `Expected:` line) and `docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md:582` (Definition of done second bullet).
+- Verification: `tasktool validate --format json` → `{"ok": true, "errors": [], "warnings": ["P7.S5.refs: path does not exist: docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice"]}` — ok:true, rc 0, only warning is the unrelated P7.S5 path warning (no surfaces/reservations/parallel_group drift warning); `tasktool validate --no-path-warnings --format json` → `{"ok": true, "errors": [], "warnings": []}` — ok:true, empty warnings.
+
+Notes:
+Reconciled Step 7's opening `Expected:` from "empty warnings" to "no surfaces/reservations/parallel_group drift warnings" and added an explicit sentence calling out the pre-existing P7.S5 path warning (`P7.S5.refs: path does not exist: docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice`) as unrelated P7.S5 drift (uncommitted reviewer-chain directory) that is out of S7 scope and not a surface-drift warning. This makes the headline consistent with the detailed acceptance bar already present two sentences later. The Definition of Done bullet was also tightened to state that both invocations return ok:true with no S7 surface-drift warnings, and to name the pre-existing P7.S5 warning explicitly. No code, tests, or tracker changes were made; fixing the P7.S5 stale ref would breach the S7 slice boundary.
+
+## S1.F1
+Status: fixed
+Notes:
+Same root cause as F1 — the sweep reviewer's S1.F1 is a duplicate of the same finding (the "empty warnings" over-promise in Task 3 Step 7). Resolved by the identical plan-wording reconciliation described under F1. No additional changes required.
+
+## F2
+Status: waived
+Notes:
+The untracked post-slice reviewer-chain folder (`docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/`) and the `reviewer_chain` pointer in `docs/tasklist.json` (which still points at the plan-review chain) are the expected mid-review state, as the reviewer itself acknowledged ("this is normal during the review itself"). They are resolved by the standard slice-closeout step: the coordinator commits the post-slice chain folder and runs `tasktool close P7.S7`, which registers the post-slice chain. This is performed AFTER this review round passes. No code or plan change is warranted; nothing in the artifact set needs to change for F2.


### git diff HEAD (uncommitted)



### Untracked files

- docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/.reviewer-output/ (omitted: binary or unreadable)
### docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/chain.json

```
{
  "schema_version": 1,
  "chain": "p7-s7-plan-tracker-drift-validation-P7-S7-post-slice",
  "kind": "post-slice",
  "target": "docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md",
  "work_id": "P7.S7",
  "legacy_migrated": false,
  "rounds": [
    {
      "round": 1,
      "reviewers": [
        {
          "role": "primary",
          "sweep_group": null,
          "parent_round": 1,
          "request": "r1-2026-06-05T1257-primary-request.md",
          "response": "r1-2026-06-05T1257-primary-response.md",
          "verdict": "revise",
          "verdict_valid": true,
          "returncode": 0,
          "status": "ok",
          "provider": "codex",
          "caller_provider": "claude",
          "model": null,
          "sandbox": {
            "repo_root": "/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared",
            "scratch_dir": "/tmp/superstar-reviewer-p7-s7-plan-tracker-drift-validation-P7-S7-post-slice-r1-primary-2keynmc3",
            "response_dir": "docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/.reviewer-output/r1-primary",
            "mode": "workspace-write-with-read-access"
          },
          "started_at": "2026-06-05T11:57:30.279Z",
          "finished_at": "2026-06-05T12:01:02.554Z",
          "duration_ms": 212274,
          "estimated_usage": {
            "formula": "ceil(chars / 4)",
            "prompt_chars": 53278,
            "response_chars": 2796,
            "estimated_input_tokens": 13320,
            "estimated_output_tokens": 699,
            "estimated_total_tokens": 14019
          },
          "exact_usage": null,
          "usage_capture_status": "estimated_only",
          "usage_capture_error": null
        },
        {
          "role": "sweep",
          "sweep_group": 1,
          "parent_round": 1,
          "request": "r1-2026-06-05T1257-sweep1-request.md",
          "response": "r1-2026-06-05T1257-sweep1-response.md",
          "verdict": "ready with small edits",
          "verdict_valid": true,
          "returncode": 0,
          "status": "ok",
          "provider": "codex",
          "caller_provider": "claude",
          "model": null,
          "sandbox": {
            "repo_root": "/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared",
            "scratch_dir": "/tmp/superstar-reviewer-p7-s7-plan-tracker-drift-validation-P7-S7-post-slice-r1-sweep1-j70o9hcy",
            "response_dir": "docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/.reviewer-output/r1-sweep1",
            "mode": "workspace-write-with-read-access"
          },
          "started_at": "2026-06-05T12:01:02.556Z",
          "finished_at": "2026-06-05T12:05:00.605Z",
          "duration_ms": 238049,
          "estimated_usage": {
            "formula": "ceil(chars / 4)",
            "prompt_chars": 53278,
            "response_chars": 2476,
            "estimated_input_tokens": 13320,
            "estimated_output_tokens": 619,
            "estimated_total_tokens": 13939
          },
          "exact_usage": null,
          "usage_capture_status": "estimated_only",
          "usage_capture_error": null
        }
      ],
      "status": "ok",
      "returncode": 0,
      "started_at": "2026-06-05T11:57:30.279Z",
      "finished_at": "2026-06-05T12:01:02.554Z",
      "duration_ms": 212274,
      "provider": "codex",
      "caller_provider": "claude",
      "model": null,
      "estimated_usage": {
        "formula": "ceil(chars / 4)",
        "prompt_chars": 53278,
        "response_chars": 2796,
        "estimated_input_tokens": 13320,
        "estimated_output_tokens": 699,
        "estimated_total_tokens": 14019
      },
      "exact_usage": null,
      "usage_capture_status": "estimated_only",
      "usage_capture_error": null,
      "merged_verdict": "revise",
      "merged_findings": "r1-merged-findings.md",
      "request": "r1-2026-06-05T1257-primary-request.md",
      "response": "r1-2026-06-05T1257-primary-response.md",
      "resolution": null,
      "resolution_parse_status": null,
      "resolution_waiver": false,
      "head_sha_at_request": "d4524711835b4f7f89532f6d6ec808dc21a9ed41",
      "head_sha_after_round": "d4524711835b4f7f89532f6d6ec808dc21a9ed41",
      "worktree_dirty_at_request": true,
      "verdict": "revise",
      "verdict_valid": true,
      "findings_count": 2,
      "blocking_findings_count": 0,
      "base_ref": null,
      "base_ref_source": null,
      "diff_included": false
    }
  ],
  "sweep_checkpoints": {
    "first-round": "completed",
    "final-ready": "pending"
  }
}

```

### docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/r1-2026-06-05T1257-primary-request.md

```
<!-- superstar-prompt:start -->
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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md

Additional context files:
- docs/specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md
- docs/tasklist.json

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

### docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md

    1	# P7.S7 — Plan ↔ tracker drift validation: Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Add two non-fatal `tasktool validate` warnings so a slice's tracker-declared `integration_surfaces`/`reservations` cannot silently diverge from its plan document.
    6	
    7	**Architecture:** One new pure helper `find_surface_drift_warnings(p, repo_root, *, include_plan_checks)` in `tools/tasktool/validate.py`, mirroring the existing `find_path_warnings`. It runs Check 1 (a slice in a `parallel_group` declaring no surfaces — always on) and, when `include_plan_checks` is true, Check 2 (a tracker-declared surface/reservation absent from the slice's plan file — substring presence, not table parsing). It is wired into `_cmd_validate_at_root` next to `find_path_warnings`, with Check 2 gated on `not no_path_warnings`. No model/schema/CLI change; warnings flow through the existing text/JSON `warnings` channel and never change the exit code.
    8	
    9	**Tech Stack:** Python 3.11+, stdlib only. Tests with `unittest` under `tools/tasktool/tests/`.
   10	
   11	**Spec:** [`docs/specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md`](../specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md) (§4 is authoritative). Implements P7 spec §4.G.
   12	
   13	---
   14	
   15	## Scheduling contract
   16	
   17	`tasktool show P7.S7` / `tasktool schedule P7` confirm:
   18	
   19	- `depends_on = [P7.S1, P7.S6]` — both `done`. S1 added the `integration_surfaces`/`reservations`/`coordination_group` fields this plan reads; S6 established the plan-table convention this check audits.
   20	- `parallel_group = none`, `coordination_group = none`. S7 is an independently-executable single slice.
   21	- **Integration surfaces for S7 itself:** `validate` (it edits `validate.py` + its test). Disjoint from every other P7 slice's surfaces (`skills`, `worktree`, `commands`/`cli`), and all siblings are terminal anyway — no overlap, no coordination needed. The S7 row currently carries this only as a prose note; Task 5 declares it as a real `integration_surfaces` value (`tasktool surface add P7.S7 validate`) so the tracker is self-consistent before ratification — dogfooding the very check this slice ships.
   22	
   23	No dependency-graph change is required. Task 5 declares S7's own write surface and then ratifies the row.
   24	
   25	## How to run the tools
   26	
   27	All `tasktool`/`pytest` commands run from the repo root unless noted. The test module is `tools/tasktool/tests/test_validate.py`; run focused tests with:
   28	
   29	```bash
   30	cd tools/tasktool && python -m pytest tests/test_validate.py -k drift -q
   31	```
   32	
   33	The package imports as `tasktool` (the `tools/tasktool/` dir is the package root on `sys.path` when invoked via the shim / from inside `tools/tasktool`).
   34	
   35	## File structure
   36	
   37	| File | Responsibility | Change |
   38	|------|----------------|--------|
   39	| `tools/tasktool/validate.py` | Structural validation + non-fatal warning helpers | **Modify** — add `find_surface_drift_warnings` (reuses `is_terminal`, already imported) |
   40	| `tools/tasktool/commands.py` | `validate` command wiring (`_cmd_validate_at_root`) | **Modify** — import and call the new helper alongside `find_path_warnings` |
   41	| `tools/tasktool/tests/test_validate.py` | Validation unit tests | **Modify** — add a `SurfaceDriftWarningTests` class; extend imports (`Reservation`, `Status`) |
   42	
   43	The mirror copy under `plugins/superstar/tools/tasktool/` is produced by the publish/sync scripts at release time; **do not hand-edit it** in this slice.
   44	
   45	---
   46	
   47	## Task 1: Check 1 — no-surface-in-parallel-group nudge
   48	
   49	Spec §4.B. Pure, no file I/O. A non-terminal slice with a `parallel_group` set but empty `integration_surfaces` warrants a nudge.
   50	
   51	**Files:**
   52	- Modify: `tools/tasktool/validate.py` (add `find_surface_drift_warnings`; `is_terminal` is already imported)
   53	- Test: `tools/tasktool/tests/test_validate.py` (new `SurfaceDriftWarningTests`)
   54	
   55	- [ ] **Step 1: Extend the test imports**
   56	
   57	At the top of `tools/tasktool/tests/test_validate.py`, the model import currently ends with `Status,`. Add `Reservation,` to that `from tasktool.model import (...)` block (it already imports `Status`). The final block must include `Reservation` and `Status`:
   58	
   59	```python
   60	from tasktool.model import (
   61	    ArchivedCrossCutting,
   62	    Project,
   63	    Phase,
   64	    Slice,
   65	    Task,
   66	    CrossCutting,
   67	    BlockedOn,
   68	    Reservation,
   69	    Status,
   70	)
   71	```
   72	
   73	- [ ] **Step 2: Write the failing test for Check 1**
   74	
   75	Append this class to `tools/tasktool/tests/test_validate.py`:
   76	
   77	```python
   78	class SurfaceDriftWarningTests(unittest.TestCase):
   79	    def test_parallel_group_no_surfaces_warns(self):
   80	        from tasktool.validate import find_surface_drift_warnings
   81	        p = _project_with_slice(parallel_group="core")
   82	        with tempfile.TemporaryDirectory() as td:
   83	            warnings = find_surface_drift_warnings(
   84	                p, Path(td), include_plan_checks=True
   85	            )
   86	        self.assertTrue(
   87	            any("parallel_group" in w and "P1.S1" in w for w in warnings),
   88	            warnings,
   89	        )
   90	
   91	    def test_parallel_group_with_surfaces_no_warn(self):
   92	        from tasktool.validate import find_surface_drift_warnings
   93	        p = _project_with_slice(
   94	            parallel_group="core", integration_surfaces=["commands"]
   95	        )
   96	        with tempfile.TemporaryDirectory() as td:
   97	            warnings = find_surface_drift_warnings(
   98	                p, Path(td), include_plan_checks=True
   99	            )
  100	        self.assertEqual(
  101	            [w for w in warnings if "parallel_group" in w], []
  102	        )
  103	
  104	    def test_no_parallel_group_no_surfaces_no_warn(self):
  105	        from tasktool.validate import find_surface_drift_warnings
  106	        p = _project_with_slice()  # no parallel_group, no surfaces
  107	        with tempfile.TemporaryDirectory() as td:
  108	            warnings = find_surface_drift_warnings(
  109	                p, Path(td), include_plan_checks=True
  110	            )
  111	        self.assertEqual(warnings, [])
  112	
  113	    def test_terminal_slice_in_parallel_group_no_warn(self):
  114	        from tasktool.validate import find_surface_drift_warnings
  115	        p = _project_with_slice(
  116	            parallel_group="core",
  117	            status=Status.DONE,
  118	            closed="2026-05-18",
  119	        )
  120	        with tempfile.TemporaryDirectory() as td:
  121	            warnings = find_surface_drift_warnings(
  122	                p, Path(td), include_plan_checks=True
  123	            )
  124	        self.assertEqual(warnings, [])
  125	
  126	    def test_check1_runs_even_when_plan_checks_disabled(self):
  127	        from tasktool.validate import find_surface_drift_warnings
  128	        p = _project_with_slice(parallel_group="core")
  129	        with tempfile.TemporaryDirectory() as td:
  130	            warnings = find_surface_drift_warnings(
  131	                p, Path(td), include_plan_checks=False
  132	            )
  133	        self.assertTrue(
  134	            any("parallel_group" in w for w in warnings), warnings
  135	        )
  136	```
  137	
  138	- [ ] **Step 3: Run the test to verify it fails**
  139	
  140	Run: `cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q`
  141	Expected: FAIL — `ImportError: cannot import name 'find_surface_drift_warnings'`.
  142	
  143	- [ ] **Step 4: Implement Check 1 in `find_surface_drift_warnings`**
[truncated: 862 additional lines]
```

### docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/r1-2026-06-05T1257-primary-response.md

```
# Review — 2026-06-05-P7-S7-plan-tracker-drift-validation.md (post-slice, round 1)

- Target: `docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md`
- Request: `docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/r1-2026-06-05T1257-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: important  
`tasktool validate --format json` does not meet the plan’s live-tracker smoke expectation. The plan expects `ok: true`, rc 0, and empty `warnings` at [docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared/docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md:511). Fresh output is `ok: true` but includes `P7.S5.refs: path does not exist: docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice`. This is not an S7 surface-drift regression, but it means the stated acceptance command is not clean and should be reconciled or explicitly documented as unrelated pre-existing repo drift before closeout.

F2 — Severity: important  
Post-slice review artifacts are untracked and not registered on the S7 row. `git status --short --untracked-files=all` shows untracked files under `docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/`, while `docs/tasklist.json` still has `reviewer_chain` pointing at the plan-review chain at [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared/docs/tasklist.json:454). That is expected during the review itself, but it is not ready for final slice closeout until the post-slice chain is committed/registered.

2. Open questions / assumptions

I assume the P7.S5 missing reviewer-chain warning is unrelated existing repo drift, not introduced by S7. If so, the S7 closeout should either fix the missing tracked ref or record that the S7 acceptance is “no S7 drift warnings” rather than “empty warnings”.

3. Suggested document edits

Update the plan’s Task 3/DoD smoke wording to distinguish “no surface-drift warnings” from “no warnings at all”, unless the intended gate really is a globally clean `tasktool validate --format json`.

4. Verification gaps / commands that should be run

Fresh checks run:
`cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q` → 15 passed.  
`cd tools/tasktool && python -m pytest -q` → 789 passed.  
`tasktool validate --no-path-warnings --format json` → `ok: true`, no warnings.  
`tasktool validate --format json` → `ok: true`, one P7.S5 path warning.  
`git diff --check 65acbcb..HEAD` → clean.

Overall verdict: revise

```

### docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/r1-2026-06-05T1257-sweep1-request.md

```
<!-- superstar-prompt:start -->
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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md

Additional context files:
- docs/specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md
- docs/tasklist.json

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

### docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md

    1	# P7.S7 — Plan ↔ tracker drift validation: Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Add two non-fatal `tasktool validate` warnings so a slice's tracker-declared `integration_surfaces`/`reservations` cannot silently diverge from its plan document.
    6	
    7	**Architecture:** One new pure helper `find_surface_drift_warnings(p, repo_root, *, include_plan_checks)` in `tools/tasktool/validate.py`, mirroring the existing `find_path_warnings`. It runs Check 1 (a slice in a `parallel_group` declaring no surfaces — always on) and, when `include_plan_checks` is true, Check 2 (a tracker-declared surface/reservation absent from the slice's plan file — substring presence, not table parsing). It is wired into `_cmd_validate_at_root` next to `find_path_warnings`, with Check 2 gated on `not no_path_warnings`. No model/schema/CLI change; warnings flow through the existing text/JSON `warnings` channel and never change the exit code.
    8	
    9	**Tech Stack:** Python 3.11+, stdlib only. Tests with `unittest` under `tools/tasktool/tests/`.
   10	
   11	**Spec:** [`docs/specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md`](../specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md) (§4 is authoritative). Implements P7 spec §4.G.
   12	
   13	---
   14	
   15	## Scheduling contract
   16	
   17	`tasktool show P7.S7` / `tasktool schedule P7` confirm:
   18	
   19	- `depends_on = [P7.S1, P7.S6]` — both `done`. S1 added the `integration_surfaces`/`reservations`/`coordination_group` fields this plan reads; S6 established the plan-table convention this check audits.
   20	- `parallel_group = none`, `coordination_group = none`. S7 is an independently-executable single slice.
   21	- **Integration surfaces for S7 itself:** `validate` (it edits `validate.py` + its test). Disjoint from every other P7 slice's surfaces (`skills`, `worktree`, `commands`/`cli`), and all siblings are terminal anyway — no overlap, no coordination needed. The S7 row currently carries this only as a prose note; Task 5 declares it as a real `integration_surfaces` value (`tasktool surface add P7.S7 validate`) so the tracker is self-consistent before ratification — dogfooding the very check this slice ships.
   22	
   23	No dependency-graph change is required. Task 5 declares S7's own write surface and then ratifies the row.
   24	
   25	## How to run the tools
   26	
   27	All `tasktool`/`pytest` commands run from the repo root unless noted. The test module is `tools/tasktool/tests/test_validate.py`; run focused tests with:
   28	
   29	```bash
   30	cd tools/tasktool && python -m pytest tests/test_validate.py -k drift -q
   31	```
   32	
   33	The package imports as `tasktool` (the `tools/tasktool/` dir is the package root on `sys.path` when invoked via the shim / from inside `tools/tasktool`).
   34	
   35	## File structure
   36	
   37	| File | Responsibility | Change |
   38	|------|----------------|--------|
   39	| `tools/tasktool/validate.py` | Structural validation + non-fatal warning helpers | **Modify** — add `find_surface_drift_warnings` (reuses `is_terminal`, already imported) |
   40	| `tools/tasktool/commands.py` | `validate` command wiring (`_cmd_validate_at_root`) | **Modify** — import and call the new helper alongside `find_path_warnings` |
   41	| `tools/tasktool/tests/test_validate.py` | Validation unit tests | **Modify** — add a `SurfaceDriftWarningTests` class; extend imports (`Reservation`, `Status`) |
   42	
   43	The mirror copy under `plugins/superstar/tools/tasktool/` is produced by the publish/sync scripts at release time; **do not hand-edit it** in this slice.
   44	
   45	---
   46	
   47	## Task 1: Check 1 — no-surface-in-parallel-group nudge
   48	
   49	Spec §4.B. Pure, no file I/O. A non-terminal slice with a `parallel_group` set but empty `integration_surfaces` warrants a nudge.
   50	
   51	**Files:**
   52	- Modify: `tools/tasktool/validate.py` (add `find_surface_drift_warnings`; `is_terminal` is already imported)
   53	- Test: `tools/tasktool/tests/test_validate.py` (new `SurfaceDriftWarningTests`)
   54	
   55	- [ ] **Step 1: Extend the test imports**
   56	
   57	At the top of `tools/tasktool/tests/test_validate.py`, the model import currently ends with `Status,`. Add `Reservation,` to that `from tasktool.model import (...)` block (it already imports `Status`). The final block must include `Reservation` and `Status`:
   58	
   59	```python
   60	from tasktool.model import (
   61	    ArchivedCrossCutting,
   62	    Project,
   63	    Phase,
   64	    Slice,
   65	    Task,
   66	    CrossCutting,
   67	    BlockedOn,
   68	    Reservation,
   69	    Status,
   70	)
   71	```
   72	
   73	- [ ] **Step 2: Write the failing test for Check 1**
   74	
   75	Append this class to `tools/tasktool/tests/test_validate.py`:
   76	
   77	```python
   78	class SurfaceDriftWarningTests(unittest.TestCase):
   79	    def test_parallel_group_no_surfaces_warns(self):
   80	        from tasktool.validate import find_surface_drift_warnings
   81	        p = _project_with_slice(parallel_group="core")
   82	        with tempfile.TemporaryDirectory() as td:
   83	            warnings = find_surface_drift_warnings(
   84	                p, Path(td), include_plan_checks=True
   85	            )
   86	        self.assertTrue(
   87	            any("parallel_group" in w and "P1.S1" in w for w in warnings),
   88	            warnings,
   89	        )
   90	
   91	    def test_parallel_group_with_surfaces_no_warn(self):
   92	        from tasktool.validate import find_surface_drift_warnings
   93	        p = _project_with_slice(
   94	            parallel_group="core", integration_surfaces=["commands"]
   95	        )
   96	        with tempfile.TemporaryDirectory() as td:
   97	            warnings = find_surface_drift_warnings(
   98	                p, Path(td), include_plan_checks=True
   99	            )
  100	        self.assertEqual(
  101	            [w for w in warnings if "parallel_group" in w], []
  102	        )
  103	
  104	    def test_no_parallel_group_no_surfaces_no_warn(self):
  105	        from tasktool.validate import find_surface_drift_warnings
  106	        p = _project_with_slice()  # no parallel_group, no surfaces
  107	        with tempfile.TemporaryDirectory() as td:
  108	            warnings = find_surface_drift_warnings(
  109	                p, Path(td), include_plan_checks=True
  110	            )
  111	        self.assertEqual(warnings, [])
  112	
  113	    def test_terminal_slice_in_parallel_group_no_warn(self):
  114	        from tasktool.validate import find_surface_drift_warnings
  115	        p = _project_with_slice(
  116	            parallel_group="core",
  117	            status=Status.DONE,
  118	            closed="2026-05-18",
  119	        )
  120	        with tempfile.TemporaryDirectory() as td:
  121	            warnings = find_surface_drift_warnings(
  122	                p, Path(td), include_plan_checks=True
  123	            )
  124	        self.assertEqual(warnings, [])
  125	
  126	    def test_check1_runs_even_when_plan_checks_disabled(self):
  127	        from tasktool.validate import find_surface_drift_warnings
  128	        p = _project_with_slice(parallel_group="core")
  129	        with tempfile.TemporaryDirectory() as td:
  130	            warnings = find_surface_drift_warnings(
  131	                p, Path(td), include_plan_checks=False
  132	            )
  133	        self.assertTrue(
  134	            any("parallel_group" in w for w in warnings), warnings
  135	        )
  136	```
  137	
  138	- [ ] **Step 3: Run the test to verify it fails**
  139	
  140	Run: `cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q`
  141	Expected: FAIL — `ImportError: cannot import name 'find_surface_drift_warnings'`.
  142	
  143	- [ ] **Step 4: Implement Check 1 in `find_surface_drift_warnings`**
[truncated: 862 additional lines]
```

### docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/r1-2026-06-05T1257-sweep1-response.md

```
# Review — 2026-06-05-P7-S7-plan-tracker-drift-validation.md (post-slice, round 1)

- Target: `docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md`
- Request: `docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/r1-2026-06-05T1257-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings
F1. Severity: important — The live tracker does not satisfy the plan’s plain-validate smoke expectation. [docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared/docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md:513) expects `tasktool validate --format json` to return empty `warnings`, but the current repo returns:
`P7.S5.refs: path does not exist: docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice`.
The stale ref is in [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared/docs/tasklist.json:386), and the matching directory is absent. This is not a P7.S7 surface-drift warning, but it means the stated live-tracker smoke output is not true as written.

2. Open questions / assumptions
I assume P7.S7 is intentionally still `in_progress` until this post-slice review passes; the row is ratified and has `integration_surfaces: ["validate"]` at [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared/docs/tasklist.json:440).

3. Suggested document edits
Either fix the stale P7.S5 reviewer ref / restore the missing reviewer directory, or amend the closeout evidence to state that plain validate currently has one unrelated path warning while the P7.S7 acceptance signal is “no `surfaces` / `reservations` / `parallel_group` drift warnings and rc 0.”

4. Verification gaps / commands that should be run
I ran:
`cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q` — 15 passed.
`cd tools/tasktool && python -m pytest tests/test_validate.py tests/test_commands.py -q` — 265 passed.
`cd tools/tasktool && python -m pytest -q` — 789 passed.
`tasktool validate --no-path-warnings --format json` — clean.
`tasktool validate --format json` — rc 0 / ok true, but one unrelated P7.S5 path warning.

Overall verdict: ready with small edits

```

### docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/r1-merged-findings.md

```
# Merged findings for r1

## Primary

# Review — 2026-06-05-P7-S7-plan-tracker-drift-validation.md (post-slice, round 1)

- Target: `docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md`
- Request: `docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/r1-2026-06-05T1257-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: important  
`tasktool validate --format json` does not meet the plan’s live-tracker smoke expectation. The plan expects `ok: true`, rc 0, and empty `warnings` at [docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared/docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md:511). Fresh output is `ok: true` but includes `P7.S5.refs: path does not exist: docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice`. This is not an S7 surface-drift regression, but it means the stated acceptance command is not clean and should be reconciled or explicitly documented as unrelated pre-existing repo drift before closeout.

F2 — Severity: important  
Post-slice review artifacts are untracked and not registered on the S7 row. `git status --short --untracked-files=all` shows untracked files under `docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/`, while `docs/tasklist.json` still has `reviewer_chain` pointing at the plan-review chain at [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared/docs/tasklist.json:454). That is expected during the review itself, but it is not ready for final slice closeout until the post-slice chain is committed/registered.

2. Open questions / assumptions

I assume the P7.S5 missing reviewer-chain warning is unrelated existing repo drift, not introduced by S7. If so, the S7 closeout should either fix the missing tracked ref or record that the S7 acceptance is “no S7 drift warnings” rather than “empty warnings”.

3. Suggested document edits

Update the plan’s Task 3/DoD smoke wording to distinguish “no surface-drift warnings” from “no warnings at all”, unless the intended gate really is a globally clean `tasktool validate --format json`.

4. Verification gaps / commands that should be run

Fresh checks run:
`cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q` → 15 passed.  
`cd tools/tasktool && python -m pytest -q` → 789 passed.  
`tasktool validate --no-path-warnings --format json` → `ok: true`, no warnings.  
`tasktool validate --format json` → `ok: true`, one P7.S5 path warning.  
`git diff --check 65acbcb..HEAD` → clean.

Overall verdict: revise


## Sweep 1

# Review — 2026-06-05-P7-S7-plan-tracker-drift-validation.md (post-slice, round 1)

- Target: `docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md`
- Request: `docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice/r1-2026-06-05T1257-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings
S1.F1. Severity: important — The live tracker does not satisfy the plan’s plain-validate smoke expectation. [docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared/docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md:513) expects `tasktool validate --format json` to return empty `warnings`, but the current repo returns:
`P7.S5.refs: path does not exist: docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice`.
The stale ref is in [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared/docs/tasklist.json:386), and the matching directory is absent. This is not a P7.S7 surface-drift warning, but it means the stated live-tracker smoke output is not true as written.

2. Open questions / assumptions
I assume P7.S7 is intentionally still `in_progress` until this post-slice review passes; the row is ratified and has `integration_surfaces: ["validate"]` at [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared/docs/tasklist.json:440).

3. Suggested document edits
Either fix the stale P7.S5 reviewer ref / restore the missing reviewer directory, or amend the closeout evidence to state that plain validate currently has one unrelated path warning while the P7.S7 acceptance signal is “no `surfaces` / `reservations` / `parallel_group` drift warnings and rc 0.”

4. Verification gaps / commands that should be run
I ran:
`cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q` — 15 passed.
`cd tools/tasktool && python -m pytest tests/test_validate.py tests/test_commands.py -q` — 265 passed.
`cd tools/tasktool && python -m pytest -q` — 789 passed.
`tasktool validate --no-path-warnings --format json` — clean.
`tasktool validate --format json` — rc 0 / ok true, but one unrelated P7.S5 path warning.

Overall verdict: ready with small edits


```



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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s7-plan-tracker-drift-validation-declared

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md

Additional context files:
- docs/specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md
- docs/tasklist.json

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

### docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md

    1	# P7.S7 — Plan ↔ tracker drift validation: Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Add two non-fatal `tasktool validate` warnings so a slice's tracker-declared `integration_surfaces`/`reservations` cannot silently diverge from its plan document.
    6	
    7	**Architecture:** One new pure helper `find_surface_drift_warnings(p, repo_root, *, include_plan_checks)` in `tools/tasktool/validate.py`, mirroring the existing `find_path_warnings`. It runs Check 1 (a slice in a `parallel_group` declaring no surfaces — always on) and, when `include_plan_checks` is true, Check 2 (a tracker-declared surface/reservation absent from the slice's plan file — substring presence, not table parsing). It is wired into `_cmd_validate_at_root` next to `find_path_warnings`, with Check 2 gated on `not no_path_warnings`. No model/schema/CLI change; warnings flow through the existing text/JSON `warnings` channel and never change the exit code.
    8	
    9	**Tech Stack:** Python 3.11+, stdlib only. Tests with `unittest` under `tools/tasktool/tests/`.
   10	
   11	**Spec:** [`docs/specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md`](../specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md) (§4 is authoritative). Implements P7 spec §4.G.
   12	
   13	---
   14	
   15	## Scheduling contract
   16	
   17	`tasktool show P7.S7` / `tasktool schedule P7` confirm:
   18	
   19	- `depends_on = [P7.S1, P7.S6]` — both `done`. S1 added the `integration_surfaces`/`reservations`/`coordination_group` fields this plan reads; S6 established the plan-table convention this check audits.
   20	- `parallel_group = none`, `coordination_group = none`. S7 is an independently-executable single slice.
   21	- **Integration surfaces for S7 itself:** `validate` (it edits `validate.py` + its test). Disjoint from every other P7 slice's surfaces (`skills`, `worktree`, `commands`/`cli`), and all siblings are terminal anyway — no overlap, no coordination needed. The S7 row currently carries this only as a prose note; Task 5 declares it as a real `integration_surfaces` value (`tasktool surface add P7.S7 validate`) so the tracker is self-consistent before ratification — dogfooding the very check this slice ships.
   22	
   23	No dependency-graph change is required. Task 5 declares S7's own write surface and then ratifies the row.
   24	
   25	## How to run the tools
   26	
   27	All `tasktool`/`pytest` commands run from the repo root unless noted. The test module is `tools/tasktool/tests/test_validate.py`; run focused tests with:
   28	
   29	```bash
   30	cd tools/tasktool && python -m pytest tests/test_validate.py -k drift -q
   31	```
   32	
   33	The package imports as `tasktool` (the `tools/tasktool/` dir is the package root on `sys.path` when invoked via the shim / from inside `tools/tasktool`).
   34	
   35	## File structure
   36	
   37	| File | Responsibility | Change |
   38	|------|----------------|--------|
   39	| `tools/tasktool/validate.py` | Structural validation + non-fatal warning helpers | **Modify** — add `find_surface_drift_warnings` (reuses `is_terminal`, already imported) |
   40	| `tools/tasktool/commands.py` | `validate` command wiring (`_cmd_validate_at_root`) | **Modify** — import and call the new helper alongside `find_path_warnings` |
   41	| `tools/tasktool/tests/test_validate.py` | Validation unit tests | **Modify** — add a `SurfaceDriftWarningTests` class; extend imports (`Reservation`, `Status`) |
   42	
   43	The mirror copy under `plugins/superstar/tools/tasktool/` is produced by the publish/sync scripts at release time; **do not hand-edit it** in this slice.
   44	
   45	---
   46	
   47	## Task 1: Check 1 — no-surface-in-parallel-group nudge
   48	
   49	Spec §4.B. Pure, no file I/O. A non-terminal slice with a `parallel_group` set but empty `integration_surfaces` warrants a nudge.
   50	
   51	**Files:**
   52	- Modify: `tools/tasktool/validate.py` (add `find_surface_drift_warnings`; `is_terminal` is already imported)
   53	- Test: `tools/tasktool/tests/test_validate.py` (new `SurfaceDriftWarningTests`)
   54	
   55	- [ ] **Step 1: Extend the test imports**
   56	
   57	At the top of `tools/tasktool/tests/test_validate.py`, the model import currently ends with `Status,`. Add `Reservation,` to that `from tasktool.model import (...)` block (it already imports `Status`). The final block must include `Reservation` and `Status`:
   58	
   59	```python
   60	from tasktool.model import (
   61	    ArchivedCrossCutting,
   62	    Project,
   63	    Phase,
   64	    Slice,
   65	    Task,
   66	    CrossCutting,
   67	    BlockedOn,
   68	    Reservation,
   69	    Status,
   70	)
   71	```
   72	
   73	- [ ] **Step 2: Write the failing test for Check 1**
   74	
   75	Append this class to `tools/tasktool/tests/test_validate.py`:
   76	
   77	```python
   78	class SurfaceDriftWarningTests(unittest.TestCase):
   79	    def test_parallel_group_no_surfaces_warns(self):
   80	        from tasktool.validate import find_surface_drift_warnings
   81	        p = _project_with_slice(parallel_group="core")
   82	        with tempfile.TemporaryDirectory() as td:
   83	            warnings = find_surface_drift_warnings(
   84	                p, Path(td), include_plan_checks=True
   85	            )
   86	        self.assertTrue(
   87	            any("parallel_group" in w and "P1.S1" in w for w in warnings),
   88	            warnings,
   89	        )
   90	
   91	    def test_parallel_group_with_surfaces_no_warn(self):
   92	        from tasktool.validate import find_surface_drift_warnings
   93	        p = _project_with_slice(
   94	            parallel_group="core", integration_surfaces=["commands"]
   95	        )
   96	        with tempfile.TemporaryDirectory() as td:
   97	            warnings = find_surface_drift_warnings(
   98	                p, Path(td), include_plan_checks=True
   99	            )
  100	        self.assertEqual(
  101	            [w for w in warnings if "parallel_group" in w], []
  102	        )
  103	
  104	    def test_no_parallel_group_no_surfaces_no_warn(self):
  105	        from tasktool.validate import find_surface_drift_warnings
  106	        p = _project_with_slice()  # no parallel_group, no surfaces
  107	        with tempfile.TemporaryDirectory() as td:
  108	            warnings = find_surface_drift_warnings(
  109	                p, Path(td), include_plan_checks=True
  110	            )
  111	        self.assertEqual(warnings, [])
  112	
  113	    def test_terminal_slice_in_parallel_group_no_warn(self):
  114	        from tasktool.validate import find_surface_drift_warnings
  115	        p = _project_with_slice(
  116	            parallel_group="core",
  117	            status=Status.DONE,
  118	            closed="2026-05-18",
  119	        )
  120	        with tempfile.TemporaryDirectory() as td:
  121	            warnings = find_surface_drift_warnings(
  122	                p, Path(td), include_plan_checks=True
  123	            )
  124	        self.assertEqual(warnings, [])
  125	
  126	    def test_check1_runs_even_when_plan_checks_disabled(self):
  127	        from tasktool.validate import find_surface_drift_warnings
  128	        p = _project_with_slice(parallel_group="core")
  129	        with tempfile.TemporaryDirectory() as td:
  130	            warnings = find_surface_drift_warnings(
  131	                p, Path(td), include_plan_checks=False
  132	            )
  133	        self.assertTrue(
  134	            any("parallel_group" in w for w in warnings), warnings
  135	        )
  136	```
  137	
  138	- [ ] **Step 3: Run the test to verify it fails**
  139	
  140	Run: `cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q`
  141	Expected: FAIL — `ImportError: cannot import name 'find_surface_drift_warnings'`.
  142	
  143	- [ ] **Step 4: Implement Check 1 in `find_surface_drift_warnings`**
  144	
  145	First, extend the existing model import near the top of `tools/tasktool/validate.py`. It currently ends:
  146	
  147	```python
  148	from tasktool.model import (
  149	    ArchivedCrossCutting,
  150	    Project,

[truncated: 442 additional lines]

<!-- superstar-prompt:end -->