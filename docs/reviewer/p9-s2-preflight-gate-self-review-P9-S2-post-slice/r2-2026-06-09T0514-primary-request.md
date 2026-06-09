<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 2 of p9-s2-preflight-gate-self-review-P9-S2-post-slice.

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
| 1 | revise | 2 | 1 |

## Prior-round findings

Source: merged findings from r1 (authoritative)

# Merged findings for r1

## Primary

# Review — 2026-06-09-P9.S2-preflight-gate-self-review.md (post-slice, round 1)

- Target: `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md`
- Request: `docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/r1-2026-06-09T0456-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: blocking — The tracker state does not support slice completion. The plan requires `tasktool start P9.S2` and expects the slice to show started/in progress at lines 41-44, but the live tracker still has `started: null` and `status: "ready"` in `docs/tasklist.json` lines 390-392. `/tmp/p9s2-brief.md` also reports `status: ready` / `workflow_step: implement` at lines 1-4. This means the required Task 0 lifecycle step was not completed, and the slice cannot be treated as fully executed.

F2 — Severity: important — The target plan is still an unchecked implementation plan, not a completed evidence record. It explicitly says checkbox syntax is for task tracking at line 3, but the required steps remain unchecked, including Task 0 at lines 41 and 46, Task 5 verification at lines 1020, 1074, and 1078, and merge/close hygiene at line 1082. The repo has four P9.S2 implementation commits and tests pass, so the code work appears real, but the document itself does not record which gates were actually run or completed.

2. Open questions / assumptions

I assume this post-slice review is intended to gate implementation completion before merge/close, so I am not treating Task 5 Step 7 merge-back/close/version-bump work as required before this review. If the team’s intended gate is “ready to close,” then Step 7 is also incomplete.

3. Suggested document edits

Update the tracker lifecycle first, or document why the slice was intentionally implemented without `tasktool start`. Then update the plan or a linked evidence note so Task 5 contains actual verification results rather than only planned commands.

Also fix the two preflight warnings in the plan: `tests/test_resolution_gate.py` is quoted at lines 32 and 745, but from repo root the existing path is `skills/external-review/tests/test_resolution_gate.py`.

4. Verification gaps / commands that should be run

I ran these checks during review:

- `python -m pytest skills/external-review/tests/test_preflight.py skills/external-review/tests/test_preflight_subcommand.py skills/external-review/tests/test_auto_preflight.py -q` → 39 passed.
- `python -m pytest skills/external-review/tests -q` → 336 passed.
- `tasktool artifact status P9.S2 --strict` → ok.
- `tasktool validate` → only pre-existing X29 missing-path warnings.
- `git status --short` → only the current post-slice reviewer chain is untracked.

Before resubmission, run `tasktool show P9.S2` and confirm it no longer reports `status: ready` with `started: null`.

Overall verdict: revise

---

## Reviewer stderr (tail)

```text
2026-06-09T03:56:16.725546Z ERROR codex_core_skills::loader: failed to stat skills path /home/simon/.codex/.tmp/plugins/plugins/life-science-research/skills/clinvar-variation-skill/SKILL.md: No such file or directory (os error 2)
```


## Sweep 1

# Review — 2026-06-09-P9.S2-preflight-gate-self-review.md (post-slice, round 1)

- Target: `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md`
- Request: `docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/r1-2026-06-09T0456-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

S1.F1 Severity: blocking — `P9.S2` is not in a completed slice state. `tasktool brief P9.S2` still reports `status: ready` and `workflow_step: implement`, and the supplied brief has the same state at `/tmp/p9s2-brief.md:1-4`. The target document also still has unchecked start/ratify steps at `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md:37-54` and unchecked wrap-up steps for full verification, post-slice review, merge-back, close, and release hygiene at `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md:1018-1084`. As a post-slice completion gate, this cannot pass while the tracker and plan both say the slice is still in implementation.

S1.F2 Severity: important — The target document is still an implementation plan, not a post-slice self-review/evidence record. The verification steps at `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md:1020-1080` describe commands to run, but do not record the actual outputs or completion evidence. I independently ran the key commands and they passed, but the document under review does not support its own completion claim.

S1.F3 Severity: minor — Round-1 auto-preflight prints warnings twice when failures are also present. `external-reviewer.py:3018-3019` prints each warning before checking failures, then `external-reviewer.py:3026` prints the full grouped preflight text again, including warnings. This is not a correctness blocker, but it drifts from the “same findings list” behavior and can confuse users on mixed failure/warning documents.

2. Open questions / assumptions

I treated the untracked `docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/` path as the current review chain produced for this review, not as an implementation artifact defect.

3. Suggested document edits

Add a short post-slice evidence section to the target document or use a dedicated completion note. It should record actual command outputs, tracker state, commit list, known residual warnings, and whether merge/close/release hygiene is intentionally deferred.

Mark completed plan checkboxes or stop using the plan as the review target for post-slice completion.

For S1.F3, only print preflight warnings early when the preflight is otherwise OK, or remove the early warning loop and let `_print_preflight_text()` handle all findings.

4. Verification gaps / commands that should be run, if any

I ran these successfully:
`python -m pytest skills/external-review/tests/test_preflight.py skills/external-review/tests/test_preflight_subcommand.py skills/external-review/tests/test_auto_preflight.py -q` — 39 passed.
`python -m pytest skills/external-review/tests -q` — 336 passed.
CLI help smoke for `preflight` and `--no-preflight` — present.
Behavioral smoke for `run_preflight_checks()` — bad doc false, good doc true.
Real-corpus preflight sample — 0 failures; P9.S1 plan had 8 warnings.

Still needed before completion: update tracker lifecycle (`start`/close as appropriate), land/merge per the repo workflow, and decide the version bump/release hygiene called out in the plan.

Overall verdict: revise



## Resolution report for prior round

# Resolution for r1

## F1
Status: fixed
Evidence:
- Tracker lifecycle applied by coordinator: `tasktool start P9.S2` + `tasktool ratify P9.S2` run; commit `f03c777` ("P9.S2: mark slice in_progress + ratified (lifecycle)") landed on `main` and merged into the worktree via `0d8b662`.
- `tasktool brief P9.S2` now reports `status: in_progress`, `started: 2026-06-09`, `planning_status: ratified`, `workflow_step: implement`.

## F2
Status: fixed
Evidence:
- All completed task checkboxes in `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md` marked `[x]`: Task 0 (Steps 1–2), Task 1 (Steps 1–8), Task 2 (Steps 1–8), Task 3 (Steps 1–7), Task 4 (Steps 1–5), Task 5 (Steps 1–6). Task 5 Step 7 (merge-back/close/release hygiene) remains `[ ]` — intentionally deferred until this review reaches `ready`.
- New `## Post-slice evidence (round 1)` section added at the end of the plan (after the Spec-coverage map table) recording: task commits (SHAs 833f049, 838f7ae, ce5f929, d1d478b, f03c777, 0d8b662), test result (`337 passed, 1 warning in 24.09s`), CLI smoke, behavioural smoke, real-corpus validation (0 failures), tracker state, residual DeprecationWarning, and pending Step 7 note.
- Also corrected two dangling backtick path references per the reviewer's suggested edits: `tests/test_resolution_gate.py` at lines 32 and 745 corrected to `skills/external-review/tests/test_resolution_gate.py`.
- Files: `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md`

## S1.F1
Status: fixed
Notes: Duplicate of F1 (tracker lifecycle); resolved as above.

## S1.F2
Status: fixed
Notes: Duplicate of F2 (plan-as-evidence); resolved as above.

## S1.F3
Status: fixed
Evidence:
- Files: `skills/external-review/scripts/external-reviewer.py` (lines 3016–3027)
- Round-1 gate restructured: failure path (`not preflight.ok`) now prints the ERROR header + `_print_preflight_text(preflight, ...)` and returns 4 immediately; the early warning loop runs only on the `ok` (proceed) path. Warnings are no longer printed twice on a mixed failure+warning document.
- Regression test `test_warnings_not_printed_twice_on_failure` added to `skills/external-review/tests/test_auto_preflight.py` — asserts `r.stderr.count("preflight warning") <= 1` on a failing+warning document.
- Verification: `python -m pytest skills/external-review/tests -q` → `337 passed, 1 warning in 24.09s`


## Changes since prior round

Worktree status: clean

### git diff base..HEAD

diff --git a/docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md b/docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md
index 1b07238..c5e8397 100644
--- a/docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md
+++ b/docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md
@@ -29,7 +29,7 @@ spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "ex
 er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
 ```
 
-- Subprocess tests reuse the `_init_repo`/`_run` harness pattern from `tests/test_resolution_gate.py` (a throwaway git repo with a `stub.sh` reviewer on `AGENT_REVIEWER_CMD`).
+- Subprocess tests reuse the `_init_repo`/`_run` harness pattern from `skills/external-review/tests/test_resolution_gate.py` (a throwaway git repo with a `stub.sh` reviewer on `AGENT_REVIEWER_CMD`).
 - Test command: `python -m pytest skills/external-review/tests/<file> -q` from the repo root.
 
 ---
@@ -38,12 +38,12 @@ er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
 
 **Files:** none (tracker only).
 
-- [ ] **Step 1: Mark the slice started**
+- [x] **Step 1: Mark the slice started**
 
 Run: `tasktool start P9.S2`
 Expected: exit 0; `tasktool show P9.S2` shows status `in_progress` / started.
 
-- [ ] **Step 2: Ratify the scheduling contract**
+- [x] **Step 2: Ratify the scheduling contract**
 
 The plan confirms the existing graph (`deps=P9.S1`, no parallel group). Run:
 
@@ -63,7 +63,7 @@ The pure function and its helpers. No argparse, no chain I/O, no LLM. Built incr
 - Modify: `skills/external-review/scripts/external-reviewer.py` (add the dataclasses + helpers + `run_preflight_checks` near the other module-level helpers — place after `apply_budget`/the `_BUDGET_SECTIONS` block region, i.e. anywhere above `def parse_args`, e.g. after line ~640; the functions are self-contained)
 - Test: `skills/external-review/tests/test_preflight.py` (create)
 
-- [ ] **Step 1: Write the failing unit tests**
+- [x] **Step 1: Write the failing unit tests**
 
 Create `skills/external-review/tests/test_preflight.py`:
 
@@ -233,12 +233,12 @@ def test_clean_document_passes(tmp_path):
     assert res.failures == []
 ```
 
-- [ ] **Step 2: Run tests to verify they fail**
+- [x] **Step 2: Run tests to verify they fail**
 
 Run: `python -m pytest skills/external-review/tests/test_preflight.py -q`
 Expected: FAIL — `AttributeError: module ... has no attribute 'run_preflight_checks'`.
 
-- [ ] **Step 3: Implement the dataclasses and code-masking helpers**
+- [x] **Step 3: Implement the dataclasses and code-masking helpers**
 
 In `external-reviewer.py`, add this block above `def parse_args` (the `dataclass` import already exists at line 37; `re`/`Path` are imported):
 
@@ -318,7 +318,7 @@ def _inline_code_spans(text: str):
         yield line_no, m.group(2)
 ```
 
-- [ ] **Step 4: Implement the placeholder scan**
+- [x] **Step 4: Implement the placeholder scan**
 
 Add below the masking helpers:
 
@@ -343,7 +343,7 @@ def _scan_placeholders(text: str, findings: list) -> None:
                     f"placeholder token {label!r} in prose", line=i))
 ```
 
-- [ ] **Step 5: Implement the referenced-path scans**
+- [x] **Step 5: Implement the referenced-path scans**
 
 Add below the placeholder scan:
 
@@ -407,7 +407,7 @@ def _scan_backtick_paths(text: str, repo_root: Path, findings: list) -> None:
                 line=line_no, path=s))
 ```
 
-- [ ] **Step 6: Implement the section + context checks and the top-level function**
+- [x] **Step 6: Implement the section + context checks and the top-level function**
 
 Add below the path scans:
 
@@ -491,12 +491,12 @@ def run_preflight_checks(kind: str, target: Path, context: list, repo_root: Path
     return PreflightResult(findings)
 ```
 
-- [ ] **Step 7: Run tests to verify they pass**
+- [x] **Step 7: Run tests to verify they pass**
 
 Run: `python -m pytest skills/external-review/tests/test_preflight.py -q`
 Expected: PASS (all).
 
-- [ ] **Step 8: Commit**
+- [x] **Step 8: Commit**
 
 ```bash
 git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_preflight.py
@@ -511,7 +511,7 @@ git commit -m "P9.S2: deterministic preflight check core (run_preflight_checks +
 - Modify: `skills/external-review/scripts/external-reviewer.py` (subparser after `sp_stats` block ~line 1993-2001; `run_preflight` function — add near `run_stats` ~line 2403; dispatch in `main` after the `stats` dispatch ~line 2578)
 - Test: `skills/external-review/tests/test_preflight_subcommand.py` (create)
 
-- [ ] **Step 1: Write the failing subprocess tests**
+- [x] **Step 1: Write the failing subprocess tests**
 
 Create `skills/external-review/tests/test_preflight_subcommand.py`:
 
@@ -635,12 +635,12 @@ def test_subcommand_oversized_context_warning(tmp_path):
     assert "context" in _checks(json.loads(r.stdout), "warnings")
 ```
 
-- [ ] **Step 2: Run tests to verify they fail**
+- [x] **Step 2: Run tests to verify they fail**
 
 Run: `python -m pytest skills/external-review/tests/test_preflight_subcommand.py -q`
 Expected: FAIL — argparse rejects the `preflight` subcommand (`invalid choice`).
 
-- [ ] **Step 3: Add the subparser**
+- [x] **Step 3: Add the subparser**
 
 In `parse_args`, immediately after the `sp_stats` block (after the `--since` argument added at ~line 1998-2001, before `return parser.parse_args(argv)`):
 
@@ -665,7 +665,7 @@ In `parse_args`, immediately after the `sp_stats` block (after the `--since` arg
     )
 ```
 
-- [ ] **Step 4: Add `run_preflight` and the text printer**
+- [x] **Step 4: Add `run_preflight` and the text printer**
 
 Add near `run_stats` (~line 2403):
 
@@ -704,7 +704,7 @@ def run_preflight(args) -> int:
     return 0 if result.ok else 4
 ```
 
-- [ ] **Step 5: Dispatch in `main`**
+- [x] **Step 5: Dispatch in `main`**
 
 In `main`, alongside the other non-review dispatches (after `if args.command == "stats": return run_stats(args)` ~line 2578), add:
 
@@ -715,17 +715,17 @@ In `main`, alongside the other non-review dispatches (after `if args.command ==
 
 (Place it before the `# From here on: args.command == "review"` comment so it never touches review-only args.)
 
-- [ ] **Step 6: Run tests to verify they pass**
+- [x] **Step 6: Run tests to verify they pass**
 
 Run: `python -m pytest skills/external-review/tests/test_preflight_subcommand.py -q`
 Expected: PASS.
 
-- [ ] **Step 7: Smoke the help surface**
+- [x] **Step 7: Smoke the help surface**
 
 Run: `python3 skills/external-review/scripts/external-reviewer.py preflight --help`
 Expected: shows `--file`, `--kind`, `--context`, `--emit`.
 
-- [ ] **Step 8: Commit**
+- [x] **Step 8: Commit**
 
 ```bash
 git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_preflight_subcommand.py
@@ -740,9 +740,9 @@ git commit -m "P9.S2: external-reviewer preflight subcommand (text/json, exit 0/
 - Modify: `skills/external-review/scripts/external-reviewer.py` (review subparser ~line 1900 area for the flag; review path right after `round_num = next_round_number(chain_dir)` ~line 2715)
 - Test: `skills/external-review/tests/test_auto_preflight.py` (create)
 
-- [ ] **Step 1: Write the failing subprocess tests**
+- [x] **Step 1: Write the failing subprocess tests**
 
-Create `skills/external-review/tests/test_auto_preflight.py`. Copy the `_init_repo`/`_run` helpers from `tests/test_resolution_gate.py` verbatim at the top (stub reviewer emits `Overall verdict: ready`; `_run` sets `AGENT_REVIEWER_CMD` and invokes `review`). Then:
+Create `skills/external-review/tests/test_auto_preflight.py`. Copy the `_init_repo`/`_run` helpers from `skills/external-review/tests/test_resolution_gate.py` verbatim at the top (stub reviewer emits `Overall verdict: ready`; `_run` sets `AGENT_REVIEWER_CMD` and invokes `review`). Then:
 
 ```python
 import json
@@ -827,12 +827,12 @@ def test_schema_too_new_aborts_before_preflight(tmp_path):
     assert "preflight" not in r.stderr.lower()
 ```
 
-- [ ] **Step 2: Run tests to verify they fail**
+- [x] **Step 2: Run tests to verify they fail**
 
 Run: `python -m pytest skills/external-review/tests/test_auto_preflight.py -q`
 Expected: FAIL — round-1 failing target currently reviews (exit 0) instead of refusing (exit 4); `--no-preflight` is an unrecognized argument.
 
-- [ ] **Step 3: Add the `--no-preflight` flag**
+- [x] **Step 3: Add the `--no-preflight` flag**
 
 In the review subparser, after the `--allow-missing-resolution` argument (~line 1900-1904), add:
 
@@ -844,7 +844,7 @@ In the review subparser, after the `--allow-missing-resolution` argument (~line
     )
 ```
 
-- [ ] **Step 4: Hook the auto-gate after the round number is known**
+- [x] **Step 4: Hook the auto-gate after the round number is known**
 
 In `main`, immediately after `round_num = next_round_number(chain_dir)` (~line 2715) and before the `timestamp = ...` line, add:
 
@@ -866,17 +866,17 @@ In `main`, immediately after `round_num = next_round_number(chain_dir)` (~line 2
 
 (`target` is the resolved `Path` and `context` is the resolved `list[Path]` from earlier in the review path — confirm with `grep -n 'context: list\[Path\]' skills/external-review/scripts/external-reviewer.py` that both names are in scope at this point.)
 
-- [ ] **Step 5: Run tests to verify they pass**
+- [x] **Step 5: Run tests to verify they pass**
 
 Run: `python -m pytest skills/external-review/tests/test_auto_preflight.py -q`
 Expected: PASS.
 
-- [ ] **Step 6: Run the dependent suites for regressions**
+- [x] **Step 6: Run the dependent suites for regressions**
 
 Run: `python -m pytest skills/external-review/tests/test_resolution_gate.py skills/external-review/tests/test_resolution_gate_all_kinds.py skills/external-review/tests/test_mode.py skills/external-review/tests/test_sweep_planning.py -q`
 Expected: PASS. These exercise round-1 `review` with stub targets; if any uses a stub target that now trips preflight (e.g. a one-line `# plan` with no sections), add `--no-preflight` to that invocation OR give the fixture target the minimal required sections. Locate with `grep -rln '"review"' skills/external-review/tests/` and re-run the full suite in Task 5 to catch all.
 
-- [ ] **Step 7: Commit**
+- [x] **Step 7: Commit**
 
 ```bash
 git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_auto_preflight.py
@@ -898,7 +898,7 @@ minimal sections, include those changed test files in this `git add` too (run
 - Modify: `skills/executing-plans/SKILL.md` (line 55 tracker-context guidance — folded-in P9.S1 finding)
 - Modify: `skills/tasklist-discipline/SKILL.md` (line ~205 Integration bullet — folded-in P9.S1 finding)
 
-- [ ] **Step 1: external-review SKILL.md — preflight subcommand docs**
+- [x] **Step 1: external-review SKILL.md — preflight subcommand docs**
 
 In `skills/external-review/SKILL.md`, add a new section after the "Round mode" section (locate with `grep -n '^## Review depth' skills/external-review/SKILL.md` and insert just before it):
 
@@ -942,7 +942,7 @@ And add a `preflight` row to the "Subcommands at a glance" table (locate with `g
 | `external-reviewer preflight ...` | Deterministic pre-review checks (no LLM). Exit 4 on failure. |
 ```
 
-- [ ] **Step 2: brainstorming SKILL.md — spec self-review checklist**
+- [x] **Step 2: brainstorming SKILL.md — spec self-review checklist**
 
 In `skills/brainstorming/SKILL.md`, the "Spec Self-Review" section currently lists four numbered checks (Placeholder scan, Internal consistency, Scope check, Ambiguity check) ending with "Fix any issues inline." (~line 124-132). After the existing numbered list and before "Fix any issues inline", insert:
 
@@ -960,7 +960,7 @@ same `--context` you will pass to the spec review) and fix any failures before
 invoking external review.
 ```
 
-- [ ] **Step 3: writing-plans SKILL.md — plan self-review checklist**
+- [x] **Step 3: writing-plans SKILL.md — plan self-review checklist**
 
 In `skills/writing-plans/SKILL.md`, the "Self-Review" section lists numbered checks ending around the "Scheduling check" item. After the existing items and before "If you find issues, fix them inline.", insert:
 
@@ -977,7 +977,7 @@ Then run `external-reviewer preflight --kind plan --file <plan-path> --context <
 and fix any failures before invoking the plan review.
 ```
 
-- [ ] **Step 4: Folded-in P9.S1 finding — executing-plans + tasklist-discipline tracker context**
+- [x] **Step 4: Folded-in P9.S1 finding — executing-plans + tasklist-discipline tracker context**
 
 `skills/executing-plans/SKILL.md` line 55 currently reads:
 
@@ -1003,7 +1003,7 @@ Change to:
 - `[[external-review]]` — passes tracker context as `--context`; prefer `tasktool brief <work-id>` output over the full `docs/tasklist.json` when the tasklist is large, and stamp `--work-id` on slice-level reviews.
 ```
 
-- [ ] **Step 5: Verify the skill texts and commit**
+- [x] **Step 5: Verify the skill texts and commit**
 
 Run: `grep -n 'preflight' skills/external-review/SKILL.md skills/brainstorming/SKILL.md skills/writing-plans/SKILL.md`
 Expected: the new mentions present in all three.
@@ -1017,12 +1017,12 @@ git commit -m "P9.S2: document preflight + add spec/plan self-review checklists;
 
 ### Task 5: Full verification + slice wrap-up
 
-- [ ] **Step 1: Run the entire external-review test suite**
+- [x] **Step 1: Run the entire external-review test suite**
 
 Run: `python -m pytest skills/external-review/tests -q`
 Expected: PASS, zero failures/errors. If a pre-existing `review` test fixture now trips the round-1 auto-gate (one-line target with no required section), fix that fixture by either adding `--no-preflight` to the invocation or giving the target the minimal section the kind requires — these are test-fixture updates, not behaviour changes.
 
-- [ ] **Step 2: Smoke the new CLI surface**
+- [x] **Step 2: Smoke the new CLI surface**
 
 ```bash
 python3 skills/external-review/scripts/external-reviewer.py preflight --help
@@ -1031,7 +1031,7 @@ python3 skills/external-review/scripts/external-reviewer.py review --help | grep
 
 Expected: preflight help lists `--file/--kind/--context/--emit`; review help shows `--no-preflight`.
 
-- [ ] **Step 3: Behavioural smoke — preflight catches and passes**
+- [x] **Step 3: Behavioural smoke — preflight catches and passes**
 
 ```bash
 python3 - <<'PY'
@@ -1053,7 +1053,7 @@ PY
 
 Expected: `OK`.
 
-- [ ] **Step 4: Validate the path heuristic against this repo's real corpus**
+- [x] **Step 4: Validate the path heuristic against this repo's real corpus**
 
 Run preflight over a sample of this repo's existing committed specs/plans to confirm the heuristic does not produce a wall of false positives on real documents:
 
@@ -1071,11 +1071,11 @@ done
 
 Expected: zero or few failures on these real, already-reviewed documents (warnings from illustrative backtick paths are acceptable). If a real document produces spurious *failures*, refine the heuristic (not the document) and re-run Task 1's tests.
 
-- [ ] **Step 5: Verification-before-completion**
+- [x] **Step 5: Verification-before-completion**
 
 Invoke `superstar:verification-before-completion`; confirm the four `P9.S2:` task commits exist (`git log --oneline` for Tasks 1-4) and the worktree is clean (`git status --short`).
 
-- [ ] **Step 6: Post-slice external review**
+- [x] **Step 6: Post-slice external review**
 
 Per `superstar:subagent-driven-development`, run `[[external-review]]` `--kind post-slice --file docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md --work-id P9.S2` with the spec and `tasktool brief P9.S2` output (scratch file) as context. Post-slice defaults to `thorough` with no depth flag. The target plan has a "Verification" heading (this task), so the round-1 auto-gate's section check passes. Iterate to `ready` / `ready with small edits`, writing `r{N}-resolution.md` between revise rounds.
 
@@ -1098,3 +1098,55 @@ Merge the worktree branch to `main` BEFORE `tasktool close P9.S2` (the close gat
 | Spec AC7 (skill texts) | Task 4 |
 | Spec AC8 (pytest green + named regression tests) | Tasks 1–3 + Task 5 |
 | Heuristic-false-positive risk validation | Task 5 (step 4) |
+
+---
+
+## Post-slice evidence (round 1)
+
+### Task commits
+
+| SHA | Message |
+|---|---|
+| `833f049` | P9.S2: deterministic preflight check core (run_preflight_checks + helpers) |
+| `838f7ae` | P9.S2: external-reviewer preflight subcommand (text/json, exit 0/4) |
+| `ce5f929` | P9.S2: auto-run preflight on review round 1 (exit 4) + --no-preflight |
+| `d1d478b` | P9.S2: document preflight + add spec/plan self-review checklists; uniform tracker-context guidance |
+| `f03c777` | P9.S2: mark slice in_progress + ratified (lifecycle) |
+| `0d8b662` | Merge branch 'main' into worktree-p9-s2-deterministic-preflight-gate |
+
+### Test results
+
+`python -m pytest skills/external-review/tests -q` → `337 passed, 1 warning in 24.09s`
+
+The 1 warning is a pre-existing `datetime.utcnow()` DeprecationWarning in `test_legacy_migration.py` → `external-reviewer.py:3595` (a legacy migration function not introduced by this slice).
+
+### CLI smoke
+
+- `python3 skills/external-review/scripts/external-reviewer.py preflight --help` → exposes `--file`, `--kind`, `--context`, `--emit`.
+- `python3 skills/external-review/scripts/external-reviewer.py review --help | grep no-preflight` → shows `--no-preflight`.
+
+### Behavioural smoke
+
+`run_preflight_checks("spec", bad_doc, [], root).ok` → `False`; `run_preflight_checks("spec", good_doc, [], root).ok` → `True`.
+
+### Real-corpus validation
+
+`preflight --kind spec docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md` and `preflight --kind plan docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md`: 0 failures across both documents. Warnings present on the P9.S1 plan (forward-reference backtick paths pointing to files created by later plan steps) — correct severity, expected behaviour.
+
+### Tracker state
+
+`tasktool brief P9.S2` reports:
+- `status: in_progress`
+- `started: 2026-06-09`
+- `workflow_step: implement`
+- `planning_status: ratified`
+
+The post-slice review runs while the slice is in the `implement` step by design. `tasktool close P9.S2` is intentionally deferred until this review reaches `ready` or `ready with small edits`.
+
+### Residual
+
+One pre-existing `DeprecationWarning: datetime.datetime.utcnow()` in `skills/external-review/scripts/external-reviewer.py:3595` inside a legacy migration function (`synthesize_manifest_from_legacy_files`). Not introduced by this slice; tracked as a separate clean-up item.
+
+### Pending
+
+Task 5 Step 7 (merge-back to `main`, `tasktool close P9.S2`, version bump, and release hygiene) is intentionally deferred until this post-slice review gate reaches `ready` / `ready with small edits`.
diff --git a/docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/.reviewer-output/r1-primary/codex-events.jsonl b/docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/.reviewer-output/r1-primary/codex-events.jsonl
new file mode 100644
index 0000000..f0caae8
--- /dev/null
+++ b/docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/.reviewer-output/r1-primary/codex-events.jsonl
@@ -0,0 +1,88 @@
+{"type":"thread.started","thread_id":"019eaa86-160e-7991-a8ef-3f1384b4ab49"}
+{"type":"turn.started"}
+{"type":"item.completed","item":{"id":"item_0","type":"agent_message","text":"Using `superstar:external-review` for the reviewer gate workflow and a quick memory pass because this is in the Superstar repo and the request is specifically a post-slice completion review."}}
+{"type":"item.started","item":{"id":"item_1","type":"command_execution","command":"/usr/bin/zsh -lc \"sed -n '1,220p' /home/simon/.codex/plugins/cache/superstar-dev/superstar/current/skills/external-review/SKILL.md\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_1","type":"command_execution","command":"/usr/bin/zsh -lc \"sed -n '1,220p' /home/simon/.codex/plugins/cache/superstar-dev/superstar/current/skills/external-review/SKILL.md\"","aggregated_output":"---\nname: external-review\ndescription: Use after writing a spec, after writing a plan, after completing a slice, and after completing a phase. Invokes a third-party reviewer via a file-based CLI bridge, stores each round under a per-document chain folder, and gates progress on the returned verdict.\n---\n\n# External Review\n\nAn independent reviewer (not the coordinating agent) reviews a target document or completed slice/phase. The bridge is the global `external-reviewer` command — provider-neutral, configured via `AGENT_REVIEWER_CMD`. Each round writes a `request.md` and `response.md` pair under a per-document chain folder so the iteration history is durable and committable.\n\n**Bridge command.** `external-reviewer` is the global canonical review-chain bridge command. It is installed by `skills/external-review/install.sh` and delegates to `skills/external-review/scripts/external-reviewer.py` in the active Superstar checkout. Local publish scripts maintain stable materialized plugin-cache entrypoints at `~/.codex/plugins/cache/superstar-dev/superstar/current/` and `~/.claude/plugins/cache/superstar-dev/superstar/current/`; when the installer is run from one of those caches, or when a publisher supplies `EXTERNAL_REVIEWER_SOURCE_ROOT`, the generated shim points at `current/` instead of a versioned cache directory. When the source script is under `$HOME`, the generated shim stores a literal `$HOME/...` path so it does not pin a machine-specific `/home/simon/...` string while still expanding to the checkout at runtime. Do not run or copy a full repo-local `scripts/external-reviewer.py` bridge. Existing repos may keep a tiny compatibility shim at that path only so old handoffs continue to delegate to the global command.\n\n**Announce at start:** \"I'm using the external-review skill to run a `<kind>` review on `<target>`.\"\n\n## When to use\n\nFour checkpoints, mapped to `--kind`:\n\n| Stage                          | `--kind`      | Triggered by                                                              |\n|--------------------------------|---------------|---------------------------------------------------------------------------|\n| Spec written, before plan      | `spec`        | `[[writing-plans]]` after the spec is saved, before drafting the plan     |\n| Plan written, before execution | `plan`        | `[[writing-plans]]` after the plan is saved, before handing off to execute|\n| Slice complete                 | `post-slice`  | `[[subagent-driven-development]]` after a slice's tasks all close         |\n| Phase complete                 | `post-phase`  | `[[subagent-driven-development]]` after the last slice of a phase closes  |\n\n`design`, `implementation`, and `other` are valid for ad-hoc reviews and do not gate the main workflow.\n\n## When NOT to use\n\n- Mid-implementation single-commit asks — use `[[requesting-internal-review]]` instead.\n- WIP / unstable targets — the reviewer needs a stable file on disk.\n- The user wants the coordinating agent itself to review — that is a different skill.\n\n## Configuration\n\nBy default the bridge chooses the opposite reviewer provider from the caller:\n\n| Caller | Default reviewer |\n|---|---|\n| Claude | Codex |\n| Codex | Claude |\n\nProvider selection is controlled by `--reviewer-provider auto|codex|claude|custom` or `AGENT_REVIEWER_PROVIDER`. Caller detection is controlled by `--caller-provider auto|claude|codex|unknown` or `AGENT_REVIEWER_CALLER`. When caller detection is `auto`, explicit caller env wins first; known harness env vars are checked next; then the bridge inspects the local process ancestry for unambiguous `claude` or `codex` executables. If both provider and caller are `auto` and the caller cannot be detected, the bridge fails closed and asks for an explicit provider or command.\n\n**Model tiering (optional).** Set `AGENT_REVIEWER_MODEL_LIGHT` and/or `AGENT_REVIEWER_MODEL_STRONG` to tier reviewer models by gate: spec/plan/design/implementation/other primaries use LIGHT; post-slice/post-phase primaries and all sweeps use STRONG. There is no cross-tier fallback — an unset tier simply omits the model override for those invocations. `--model <name>` forces one model for every reviewer in the round. The chosen model is exported as `AGENT_REVIEWER_MODEL` to the reviewer command and recorded in `chain.json`.\n\nThe reviewer command is still overrideable via `AGENT_REVIEWER_CMD` or `--reviewer-cmd`. Any explicit reviewer command is treated as `custom` and bypasses provider auto-selection. Custom wrappers are responsible for their own sandboxing.\n\nThe default command remains `reviewer-agent`. The safe wrapper contract is:\n\n- reviewed repo is readable but not writable;\n- `AGENT_REVIEWER_SCRATCH_DIR` is writable and short-lived;\n- `AGENT_REVIEWER_RESPONSE_DIR` is writable for final-message handoff;\n- wrappers may write machine-readable sidecars such as `reviewer-metadata.json`,\n  `codex-events.jsonl`, or `claude-output.json` under\n  `AGENT_REVIEWER_RESPONSE_DIR`; the review text contract remains stdout plus\n  the persisted response artifact;\n- wrappers must not use Codex `--dangerously-bypass-approvals-and-sandbox` or Claude `--dangerously-skip-permissions` unless the operator has supplied an external OS sandbox and chosen a custom command.\n- Codex currently uses `disk-full-read-access`, which may expose files outside the repo for reading. This fork accepts that read-side risk to keep the write-side mitigation simple.\n\nThe command may be:\n\n- A bare executable (`reviewer-agent`) — the prompt is supplied per `--prompt-transport` (`stdin` | `arg` | `file`, default `stdin`).\n- A template with placeholders (`{prompt_file}`, `{prompt_text}`, `{target_file}`, `{kind}`, `{chain_dir}`, `{round}`, `{previous_response}`, `{resolution_file}`, `{session_file}`, `{repo_root}`, `{response_dir}`, `{scratch_dir}`, `{request_file}`) — substituted and run through the shell. Env vars are authoritative; placeholders are derived convenience values.\n\nThe bridge exports `AGENT_REVIEWER_REPO_ROOT`, `AGENT_REVIEWER_CHAIN_DIR`, `AGENT_REVIEWER_REQUEST_FILE`, `AGENT_REVIEWER_RESPONSE_DIR`, `AGENT_REVIEWER_SCRATCH_DIR`, `AGENT_REVIEWER_TARGET_FILE`, `AGENT_REVIEWER_KIND`, `AGENT_REVIEWER_ROLE`, and `AGENT_REVIEWER_SWEEP_INDEX` for every reviewer process. `AGENT_REVIEWER_SWEEP_INDEX` is always set: empty for primary, numeric for sweeps. These env vars are authoritative; command placeholders are convenience sugar derived from the same values.\n\nScratch directories are owner-only and normally removed by the bridge. If a process is killed before cleanup, remove stale dirs with:\n\n```bash\nfind \"${TMPDIR:-/tmp}\" -maxdepth 1 -type d -name 'superstar-reviewer-*' -mtime +1 -prune -exec rm -rf -- {} +\n```\n\nIf `reviewer-agent` is missing, `[[project-setup]]` will offer to install/configure it. If the command emits no `Overall verdict`, treat the round as `revise` and ask the reviewer to honour the response contract on the next round.\n\n- `--incremental-budget-chars` (default `400000`) sets a target cap on assembled prompt size for incremental rounds. The prompt is pruned in priority order — target preview, diff body, resolution body, prior findings body — toward the target; sentinel markers, chain summary, and finding-ID lists are never trimmed. The final size may exceed the target by ~150 bytes due to the appended `<!-- budget-applied: ... -->` diagnostic note.\n\n**Slice review block.** When invoked with `--kind plan` or `--kind post-slice` and a slice `--work-id`, the script writes a transient `review_active` / `review_stage` pair on the slice row via `tasktool set`. The block is cleared when the slice's `workflow_step` is changed by the next manual setter call. The writes are best-effort: if `tasktool` is missing or fails, a warning is logged and the review continues.\n\n## How a round runs\n\nFor `post-slice` and `post-phase`, run a scope preflight before invoking the reviewer:\n\n```bash\ngit status --short\n```\n\nIf the status includes unrelated dirty files, setup/migration artifacts, legacy path moves, untracked vendored reviewer scripts, copied chain output from unrelated work, unrelated reviewer chains, unrelated tasklist mutations, files from another slice, or any dirty files outside the slice/phase scope, stop and resolve the boundary first. This is a hard blocker, not reviewer discretion: do not invoke `post-slice` or `post-phase` review against an ambiguous artifact set.\n\nUse the requested `--work-id` to judge scope before review:\n\n- `docs/reviewer/<this-chain>/...` for the current work is allowed; reviewer chain folders for another slice/phase are blockers.\n- `docs/tasklist.json` changes are allowed only when they correspond to the current slice/phase closeout; allocation/status changes for other work are blockers.\n- Dirty implementation files must belong to the current slice/phase evidence set; files from another slice must move to that slice's worktree or be merged separately before review.\n- A normal `main`/`master` checkout is planning/review-only by default; post-slice/post-phase review should run from the slice/phase implementation worktree unless the human partner explicitly opted out of isolation in the current turn.\n\nA reviewer is expected to fail a boundary review when the artifact set is ambiguous, but the coordinator should block before spending reviewer time.\n\n```bash\nexternal-reviewer review \\\n    --kind <spec|plan|post-slice|post-phase> \\\n    --file <path/to/target.md> \\\n    --work-id <P2.S3 | P2>   # required for post-slice / post-phase\n    [--context <path>]... \\\n    [--review-depth standard|thorough|exhaustive]  # default: by kind \\\n    [--reviewer-provider auto|codex|claude|custom] \\\n    [--caller-provider auto|claude|codex|unknown] \\\n    [--incremental-budget-chars 400000] \\\n    --emit json\n```\n\n- Output folder: `docs/reviewer/<target-stem-no-date>[-<work-id-dotless>]-<kind>/`\n- Round number, base ref, and prior verdict are read from `chain.json` in the chain folder.\n- Each round emits `r{N}-{timestamp}-request.md` and `r{N}-{timestamp}-response.md`. When `--review-depth thorough` or `exhaustive` runs sweep reviewers, filenames become `r{N}-{ts}-primary-*.md` and `r{N}-{ts}-sweep{K}-*.md`, plus a `r{N}-merged-findings.md`.\n- `--emit json` returns the structured payload described in \"Reading the response\". Always use `--emit json` from this skill — agents consume the JSON, not paths or human prose.\n\nWhen `docs/tasklist.json` exists and the reviewed target maps to a tasktool row, register the chain directory after a passing spec or plan review:\n\n```bash\ntasktool artifact add <id> --kind reviewer --path docs/reviewer/<chain>/\n```\n\nThe command **blocks** until the reviewer exits (default `--timeout 900`). Run it in the **foreground**. Do not background it, do not poll the chain folder, do not retry in a loop.\n\n**Prompt transport.** The script defaults to `stdin` for every bare reviewer command. This matches the bundled `reviewer-agent` wrapper and avoids `ARG_MAX` failures when prompts grow large. Override with `--prompt-transport {stdin|arg|file}` or `AGENT_REVIEWER_TRANSPORT` only when a custom reviewer backend cannot accept stdin.\n\n## Failure handling\n\nWhen the configured reviewer command exits non-zero, the round is recorded as a **process failure**, not as a verdict:\n\n- The persisted response file is a short stub (≤ 8 KB total): header, status, and the sentinel-stripped tail of the reviewer's stderr capped at 4 KB. No stdout is written.\n- `chain.json` records `status: \"failed\"`, `returncode: <rc>`, `verdict: null`, `verdict_valid: false` on both the round entry and the per-reviewer entry.\n- For any kind, the next round's resolution-required gate is **bypassed** with a stderr notice. A process failure has no findings to resolve; the next round is a re-attempt of the same review, not a fix-and-re-review. For `post-slice` / `post-phase`, a fix subagent is still used when the retry itself returns findings.\n- The next round's preamble walks backward past `status: \"failed\"` (and legacy `status: \"unknown\"`) rounds and embeds the merged-findings from the most recent `status: \"ok\"` round, prefixed with a `Note: rounds N..K were process failures...; skipped.` line. If no successful prior round exists, only the chain summary table is embedded.\n\n**Sentinel-wrapped prompts.** Every prompt is wrapped in `<!-- superstar-prompt:start -->` / `<!-- superstar-prompt:end -->` markers. If a reviewer echoes the prompt on stdout or stderr, the markers let the script strip the echo before persisting to disk, eliminating the recursive prompt-bloat class.\n\n### Multi-reviewer truth (sweeps)\n\nWhen `--review-depth thorough` or `exhaustive` runs sweeps alongside the primary:\n\n| Primary | Sweeps | Top-level `status` | `verdict_valid` | `merged_verdict` | Process exit |\n|---|---|---|---|---|---|\n| ok | all ok | `ok` | per merged | computed | `0` |\n| ok | some failed | `ok` | per merged (ok reviewers only) | computed from ok | `0` |\n| ok | all failed | `ok` | per primary | primary's verdict | `0` |\n| failed | any/all | `failed` | `false` | `null` | primary's returncode |\n\nFailed sweeps are excluded from merged-findings and do not flip the top-level status.\n\n## Rate-limit handling\n\nWhen the reviewer's provider rate-limits the configured command (e.g. codex usage cap, Claude API quota), the script detects the failure mode distinctly from a generic crash and stops to ask the operator.\n\n**Exit code 8** signals \"reviewer rate-limited; pick a recovery path.\" On exit 8 the script emits this JSON on stdout:\n\n```json\n{\n  \"rate_limited\": true,\n  \"reviewer_cmd\": \"<basename>\",\n  \"reset_at\":    \"<ISO local time>\",\n  \"reset_source\": \"regex:<pattern-name>\",\n  \"chain\":  \"<chain folder name>\",\n  \"round\":  <int>,\n  \"request_path\": \"<absolute path>\",\n  \"raw_stderr_tail\": \"<last 2 KB of reviewer stderr>\"\n}\n```\n\nPersistent state lives at `~/.config/superstar/reviewer-state.json` (override via `AGENT_REVIEWER_STATE_FILE` or `--state-file`). Subsequent invocations against any chain refuse to spawn until `reset_at` passes.\n\n### The recovery menu\n\nOn exit 8 the coordinator MUST present this menu via `AskUserQuestion` (no auto-pick):\n\n| Option | Mechanism |\n|---|---|\n| **Manual approve** | Coordinator collects a one-line note, then runs `external-reviewer manual-approve --kind X --file Y --work-id Z --note \"...\"`. Writes a synthetic round with `status: \"manual-approved\"`, `verdict: \"ready\"`. Chain advances. |\n| **Schedule retry** | Coordinator invokes the **harness-level `schedule` skill** to register a one-shot routine at `reset_at + 5 min` re-invoking the same `review` command. If the harness lacks `schedule`, falls back to printing an `at`/`cron`-suitable command for the operator. Current chain gate pauses. |\n| **Human bridge** | Coordinator prints `r{N}-request.md` path. Operator obtains a response from an external reviewer (web UI, manual reading, etc.) and either pastes the text in chat or provides a local file path. Coordinator runs `external-reviewer ingest-response --kind X --file Y --work-id Z (--from-paste FILE \\| --from-link PATH)`. Writes the response with status `human-bridged`. |\n| **Hold** | Do nothing. Exit the current gate. State persists; next session sees the same limit. |\n\nRepeated refusals against the **same chain** while the limit is open do NOT append new rounds — they coalesce onto the head rate-limited round via `last_refused_at` / `refused_at[]` (capped at 20).\n\n### Status semantics\n\nA `status: \"rate-limited\"` round is treated symmetrically with `status: \"failed\"`:\n- The resolution-required gate is bypassed for the next round.\n- `build_incremental_preamble` walks back past it to find the last `ok` round.\n- It is excluded from `merged_verdict` and `write_merged_findings` aggregation.\n\nManual-approved (`status: \"manual-approved\"`) and human-bridged (`status: \"human-bridged\"`) rounds carry real verdicts and pass through the existing gating machinery unchanged.\n\n### Subcommands at a glance\n\n| Subcommand | Purpose |\n|---|---|\n| `external-reviewer manual-approve ...` | Record an operator-approved closure on the chain. |\n| `external-reviewer ingest-response ...` | Write an externally-obtained reviewer response into the chain. |\n| `external-reviewer stats [--json] [--since <ISO date>]` | Summarize review-chain timing and usage estimates from `docs/reviewer/**/chain.json`. Provider comparison counts reviewer invocations, including sweeps. `--since` filters to rounds after the given date (rounds without timestamps are excluded and counted). The table includes a rounds-per-slice line; chains without `--work-id` are flagged as `per_slice_complete: false`. |\n| `external-reviewer show-limit` | Print the current `~/.config/superstar/reviewer-state.json` content. |\n| `external-reviewer clear-limit [--reviewer-cmd X]` | Clear the limit entry (for a single reviewer or all). Idempotent. |\n\n## Reading the response\n\nThe JSON output (always use `--emit json`) is the source of truth. Agents MUST consult:\n\n- `merged_verdict` — authoritative for gating slice/phase progress.\n- `verdict_valid` — if `false`, treat as `revise`.\n- `resolution_parse_status` — `ok` | `partial` | `unparseable` | `null`.\n- `reviewers[]` — per-reviewer verdicts and review text.\n- `review` — for multi-reviewer rounds, this contains the merged findings; for single-reviewer rounds, the primary review.\n\nVerdict values: `ready`, `ready with small edits`, `revise` (or `null` if unparseable).\n\n| Verdict                  | Action                                                                          |\n|--------------------------|---------------------------------------------------------------------------------|\n| `ready`                  | Proceed to the next stage.                                                      |\n| `ready with small edits` | Apply the suggested edits, proceed. Do not re-submit unless the edits are large.|\n| `revise`                 | Apply findings, then re-submit with the same `--kind` for round N+1.            |\n\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_2","type":"command_execution","command":"/usr/bin/zsh -lc 'rg -n \"P9|preflight|external-reviewer|review-pipeline|skills/superstar\" /home/simon/.codex/memories/MEMORY.md'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_2","type":"command_execution","command":"/usr/bin/zsh -lc 'rg -n \"P9|preflight|external-reviewer|review-pipeline|skills/superstar\" /home/simon/.codex/memories/MEMORY.md'","aggregated_output":"26:- P23.S5, docs/plans/2026-06-08-P23.S5-shared-http-418-source-isolation-and-corrective-proof.md, docs/handoffs/2026-06-08-P23.S5-shared-http-418-source-isolation-and-corrective-proof-prompt.md, external-reviewer review --kind plan, edge probe, edge:probe, buildEdgeProbeReport, buildActivationContractForSite, buildDnsPlan, tasktool artifact status P23.S5 --strict\n80:- P23.S1, tasktool brief P23.S1, tasktool show P23, tasktool schedule P23, tasktool prepare existing, external-reviewer review --kind spec, tasktool artifact status P23.S1 --strict, docs/specs/2026-06-05-P23.S1-sharewear-cloudflare-proxy-and-origin-calibration-design.md, docs/reviewer/p23-s1-sharewear-cloudflare-proxy-and-origin-calibration-design-spec, trailing whitespace\n92:- P23.S1, external-reviewer review --kind plan, docs/plans/2026-06-05-P23.S1-sharewear-cloudflare-proxy-and-origin-calibration.md, docs/handoffs/2026-06-05-P23.S1-sharewear-cloudflare-proxy-and-origin-calibration-prompt.md, docs/reviewer/p23-s1-sharewear-cloudflare-proxy-and-origin-calibration-plan, tasktool set P23.S1 --workflow-step implement, tasktool surface list P23, tasktool reserve list P23, artifact add --kind evidence\n104:- P23.S1, tasktool start P23.S1, tasktool worktree status P23.S1 --integration, site:requirements, dns:plan, edge:probe, HTTP/2 418, launch-state, X67, docs/design/_evidence/p23-s1/sharewear-cloudflare-proxy-and-origin-calibration.md, docs/design/_evidence/p23-s1/captures, external-reviewer review --kind post-slice, tasktool close P23.S1, not-ready\n195:- P23.S3’s reviewed plan established the evidence flow: public DNS preflight -> offline plan -> provider comparison if creds exist -> approval gate -> optional apply -> propagation checks -> HTTP/robots/sitemap smoke -> final state table -> post-slice review/close, and `dns:apply` human output should be rendered from captured JSON instead of by re-running the mutation command [Task 7]\n241:- P22.S1, activation contract baseline, tasktool prepare existing, external-reviewer review --kind spec, external-reviewer review --kind plan, docs/specs/2026-06-04-P22.S1-activation-contract-baseline-design.md, docs/plans/2026-06-04-P22.S1-activation-contract-baseline.md, docs/handoffs/2026-06-04-P22.S1-activation-contract-baseline-prompt.md, unrelated staged phase spec\n338:- P22.S5, activation readiness closeout, tasktool prepare existing P22.S5, external-reviewer review --kind spec, external-reviewer review --kind plan, docs/specs/2026-06-05-P22.S5-activation-readiness-closeout-design.md, docs/plans/2026-06-05-P22.S5-activation-readiness-closeout.md, docs/handoffs/2026-06-05-P22.S5-activation-readiness-closeout-prompt.md, tasktool surface check P22\n382:- `external-reviewer` can fail before review if the installed reviewer shim lags Superstar source; reinstalling with `bash /home/simon/Dev/sigreer/skills/superstar/skills/project-setup/install-reviewer-agent.sh` fixed the `6.8.5` versus `6.9.0` mismatch here [Task 9]\n403:- Symptom: the first post-slice review attempt fails before review starts with a shim-version complaint. Cause: `reviewer-agent` on PATH lags the Superstar source checkout. Fix: reinstall the shim from `skills/project-setup/install-reviewer-agent.sh` before invoking `external-reviewer` [Task 9]\n413:applies_to: cwd=/home/simon/Dev/sigreer/skills/superstar; reuse_rule=safe for this repo’s tasktool lifecycle command family, but revalidate current tracker semantics, review-chain paths, version policy, and worktree versus authoritative-checkout state before mutating\n419:- rollout_summaries/2026-06-05T15-10-45-iBOh-p8_s1_close_gate_lifecycle_auto_commit.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/06/05/rollout-2026-06-05T16-10-45-019e9856-2e2a-7360-92e2-bf567729fda1.jsonl, updated_at=2026-06-05T16:48:06+00:00, thread_id=019e9856-2e2a-7360-92e2-bf567729fda1, landed-branch gating on close and status-done)\n429:- rollout_summaries/2026-06-05T15-10-45-iBOh-p8_s1_close_gate_lifecycle_auto_commit.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/06/05/rollout-2026-06-05T16-10-45-019e9856-2e2a-7360-92e2-bf567729fda1.jsonl, updated_at=2026-06-05T16:48:06+00:00, thread_id=019e9856-2e2a-7360-92e2-bf567729fda1, scoped commit helper and lifecycle-authored auto-commit paths)\n439:- rollout_summaries/2026-06-05T15-10-45-iBOh-p8_s1_close_gate_lifecycle_auto_commit.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/06/05/rollout-2026-06-05T16-10-45-019e9856-2e2a-7360-92e2-bf567729fda1.jsonl, updated_at=2026-06-05T16:48:06+00:00, thread_id=019e9856-2e2a-7360-92e2-bf567729fda1, real hook integration coverage)\n449:- rollout_summaries/2026-06-05T15-10-45-iBOh-p8_s1_close_gate_lifecycle_auto_commit.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/06/05/rollout-2026-06-05T16-10-45-019e9856-2e2a-7360-92e2-bf567729fda1.jsonl, updated_at=2026-06-05T16:48:06+00:00, thread_id=019e9856-2e2a-7360-92e2-bf567729fda1, post-slice review through merge, close, prune, and version prompt)\n484:applies_to: cwd=/home/simon/Dev/sigreer/skills/superstar; reuse_rule=safe for P8 closeout-sequence planning in this repo, but revalidate current skill layout, lifecycle test expectations, and version-bump policy before implementation\n490:- rollout_summaries/2026-06-05T22-24-29-yHgQ-p8_s2_skill_closeout_sequence_spec_and_plan.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/06/05/rollout-2026-06-05T23-24-29-019e99e3-4579-71f3-a4a2-90c993938120.jsonl, updated_at=2026-06-05T22:49:43+00:00, thread_id=019e99e3-4579-71f3-a4a2-90c993938120, spec review and commit)\n494:- P8.S2, skill closeout sequence, docs/specs/2026-06-05-P8.S2-skill-closeout-sequence-design.md, plugins/superstar/skills, top-level skills, finishing-a-development-branch, external-reviewer review --kind spec, e270416\n500:- rollout_summaries/2026-06-05T22-24-29-yHgQ-p8_s2_skill_closeout_sequence_spec_and_plan.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/06/05/rollout-2026-06-05T23-24-29-019e99e3-4579-71f3-a4a2-90c993938120.jsonl, updated_at=2026-06-05T22:49:43+00:00, thread_id=019e99e3-4579-71f3-a4a2-90c993938120, plan, handoff, and ratified implement-ready state)\n510:- rollout_summaries/2026-06-05T22-24-29-yHgQ-p8_s2_skill_closeout_sequence_spec_and_plan.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/06/05/rollout-2026-06-05T23-24-29-019e99e3-4579-71f3-a4a2-90c993938120.jsonl, updated_at=2026-06-05T22:49:43+00:00, thread_id=019e99e3-4579-71f3-a4a2-90c993938120, schedule/surface state and untouched draft note)\n540:applies_to: cwd=/home/simon/Dev/sigreer/skills/superstar; reuse_rule=safe for this repo’s tasktool/worktree command family, but revalidate current tracker semantics, declared integration surfaces, worktree-base fields, and staged tasklist state before mutating\n546:- rollout_summaries/2026-06-04T22-48-46-YfJJ-p7_s5_conservative_worktree_sync_spec_plan_and_handoff.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/06/04/rollout-2026-06-04T23-48-46-019e94d3-268b-76f3-a8ff-0917bab1139f.jsonl, updated_at=2026-06-04T23:14:01+00:00, thread_id=019e94d3-268b-76f3-a8ff-0917bab1139f, tracker-first planning through committed handoff)\n556:- rollout_summaries/2026-06-04T23-14-47-eBj4-p7_s5_conservative_worktree_sync.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/06/05/rollout-2026-06-05T00-14-47-019e94ea-f9f0-7c83-9ea8-762444063692.jsonl, updated_at=2026-06-05T00:25:41+00:00, thread_id=019e94ea-f9f0-7c83-9ea8-762444063692, parser, stub, and dirty-state helper hardening)\n562:## Task 3: Implemented strict preflight refusals for sync before any git mutation, success\n566:- rollout_summaries/2026-06-04T23-14-47-eBj4-p7_s5_conservative_worktree_sync.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/06/05/rollout-2026-06-05T00-14-47-019e94ea-f9f0-7c83-9ea8-762444063692.jsonl, updated_at=2026-06-05T00:25:41+00:00, thread_id=019e94ea-f9f0-7c83-9ea8-762444063692, preflight refusal logic)\n570:- _preflight_worktree_sync, worktree_base_sha, unresolved merge entries, authoritative tracker drift, slice-only ID, base branch resolution, refuse before mutating git, test_worktree_sync.py\n576:- rollout_summaries/2026-06-04T23-14-47-eBj4-p7_s5_conservative_worktree_sync.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/06/05/rollout-2026-06-05T00-14-47-019e94ea-f9f0-7c83-9ea8-762444063692.jsonl, updated_at=2026-06-05T00:25:41+00:00, thread_id=019e94ea-f9f0-7c83-9ea8-762444063692, merge/rebase execution and invariant coverage)\n586:- rollout_summaries/2026-06-04T23-14-47-eBj4-p7_s5_conservative_worktree_sync.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/06/05/rollout-2026-06-05T00-14-47-019e94ea-f9f0-7c83-9ea8-762444063692.jsonl, updated_at=2026-06-05T00:25:41+00:00, thread_id=019e94ea-f9f0-7c83-9ea8-762444063692, verification, review, and closeout)\n590:- python -m pytest tools/tasktool/tests/test_worktree_sync.py -q, 790 passed, tasktool validate, external-reviewer review --kind post-slice, tasktool artifact add, reviewer_chain, tasktool close P7.S5, mixed staged docs/tasklist.json\n606:- Sync preflight order should stay: slice-only eligibility, recorded/live worktree or in-place resolution, `worktree_base_sha`, base branch resolution, unresolved merge entries, dirtiness, and authoritative tracker drift; preflight should refuse before mutating git [Task 3]\n658:- P21.S5, activation-readiness.md, blocked-before-host-mutation, external-reviewer, IsADirectoryError, docs/design/_evidence/p21-s5, tasktool close P21.S5, tasktool worktree prune P21.S5, X59, GHCR denied, route-and-dns-smoke.md, authoritative checkout\n782:- `external-reviewer review --kind post-slice` in this toolchain cannot take `docs/design/_evidence/<slice>` as a directory context; it tries to `read_text()` the path and fails with `IsADirectoryError`. Pass each evidence file as its own `--context` argument [Task 3]\n1012:- In this workflow, a post-slice `external-reviewer` `revise` result is blocking; expect a fix subagent plus `rN-resolution.md` before re-review, and do not assume the slice is closed until the follow-up review chain says so [Task 2]\n1198:- rollout_summaries/2026-05-26T17-46-16-enqG-p19_s2_external_review_cwd_mixup.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/05/26/rollout-2026-05-26T18-46-16-019e6564-f8f2-7631-9a23-505e236f0be2.jsonl, updated_at=2026-05-26T17:49:36+00:00, thread_id=019e6564-f8f2-7631-9a23-505e236f0be2, multistore reviewer-chain investigation from the Superstar checkout)\n1202:- P19.S2, external-reviewer, cwd mixup, wrong checkout, chain.json, r1-resolution.md, docs/reviewer, explicit cd, worktree vs main\n1261:- Symptom: `external-reviewer` appears to restart at `r1-*` instead of continuing to `r2-*`. Cause: the review command was launched from the wrong checkout, so it created a fresh chain in `main`. Fix: use `cd <worktree> && external-reviewer ...`, then inspect the worktree `chain.json` before blaming round numbering [Task 5]\n1354:- P18.S2, subagent-driven-development, content-container, !important normalization, multiline className line numbers, external-reviewer review --kind post-slice, tasktool close P18.S2, tasktool ready-slices P18, report-only JSONL\n1366:- P18.S2, superstar:writing-plans, tasktool start P18.S2 --in-place, external-reviewer review --kind spec, external-reviewer review --kind plan, deterministic JSONL, scripts/p18-audit-fixtures, matchesAny, handoff prompt, unrelated staged P19 paths\n1384:- The spec/plan review command shapes that worked were `external-reviewer review --kind spec --file <spec> --work-id P18.S2 --context <spec> --context <policy> --context <manifest> --emit json` and the equivalent `--kind plan` call [Task 3]\n1484:- superstar:writing-plans, P18.S3, external-reviewer review --kind plan, Selected outcome, handoff prompt, docs/reviewer/p18-s3-repository-audit-report-P18-S3-post-slice, tasktool show P18.S3\n1695:applies_to: cwd=/home/simon/Dev/sigreer/skills/superstar; reuse_rule=safe for this repo’s release and plugin-maintenance workflows, but revalidate current version numbers, cache locations, and deploy outputs on the live checkout\n1701:- rollout_summaries/2026-05-26T12-51-29-7kni-superstar_global_tasktool_shim_patch_bump_deploy_crosscut.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/05/26/rollout-2026-05-26T13-51-29-019e6457-15e3-73d0-bb5c-ba0cb74c33bc.jsonl, updated_at=2026-05-26T13:02:49+00:00, thread_id=019e6457-15e3-73d0-bb5c-ba0cb74c33bc, guidance, release, and bookkeeping repair)\n1711:- rollout_summaries/2026-05-26T13-42-20-xyWn-superstar_codex_hooks_json_cache_refresh_and_deploy_hardenin.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/05/26/rollout-2026-05-26T14-42-20-019e6485-a2d3-71b0-977e-cae6a9941aa3.jsonl, updated_at=2026-05-26T14:12:25+00:00, thread_id=019e6485-a2d3-71b0-977e-cae6a9941aa3, live cache regression fix and deploy hardening)\n1721:- rollout_summaries/2026-05-26T14-15-53-OKRd-superstar_archive_crosscuts_tts_workflow_artifacts.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/05/26/rollout-2026-05-26T15-15-53-019e64a4-5a4b-7943-b472-9701a103ef6b.jsonl, updated_at=2026-05-26T15:19:37+00:00, thread_id=019e64a4-5a4b-7943-b472-9701a103ef6b, tasktool tracker and notifier hooks)\n1731:- rollout_summaries/2026-05-26T17-43-03-Z3iC-superstar_sound_fallback_patch_bump_deploy_crosscut.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/05/26/rollout-2026-05-26T18-43-03-019e6562-04d5-7b62-96c2-8e4ae6bd6ef6.jsonl, updated_at=2026-05-26T17:47:32+00:00, thread_id=019e6562-04d5-7b62-96c2-8e4ae6bd6ef6, archived crosscut plus release)\n1737:- Related skill: skills/superstar-release-deploy/SKILL.md\n1743:- rollout_summaries/2026-05-23T18-37-25-2vdR-codex_todo_snapshot_async_hook_fix_deploy.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/05/23/rollout-2026-05-23T19-37-25-019e5620-b7b6-7a23-86c0-fc011d1994d7.jsonl, updated_at=2026-05-23T19:56:13+00:00, thread_id=019e5620-b7b6-7a23-86c0-fc011d1994d7, hook-cache drift fix plus 6.6.6 deploy)\n1749:- Related skill: skills/superstar-release-deploy/SKILL.md\n1755:- rollout_summaries/2026-05-24T11-05-51-XNeA-superstar_tasklist_cancelled_lifecycle_patch_bump_deploy.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/05/24/rollout-2026-05-24T12-05-51-019e59a9-a915-7540-b0e1-5ec1ca89d8c4.jsonl, updated_at=2026-05-24T11:12:39+00:00, thread_id=019e59a9-a915-7540-b0e1-5ec1ca89d8c4, tasklist-discipline drift fix plus 6.8.1 release)\n1761:- Related skill: skills/superstar-release-deploy/SKILL.md\n1767:- rollout_summaries/2026-06-02T19-47-36-QPRP-superstar_shared_surface_tasktool_design_critique.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/06/02/rollout-2026-06-02T20-47-36-019e89e0-9128-7a13-b4eb-8319b9b4a255.jsonl, updated_at=2026-06-02T19:52:26+00:00, thread_id=019e89e0-9128-7a13-b4eb-8319b9b4a255, grounded workflow critique rather than implementation)\n1777:- rollout_summaries/2026-06-05T14-31-07-4fqh-p8_closeout_integrity_design_opinion.md (cwd=/home/simon/Dev/sigreer/skills/superstar, rollout_path=/home/simon/.codex/sessions/2026/06/05/rollout-2026-06-05T15-31-07-019e9831-e49a-7881-b17f-6e94986d9649.jsonl, updated_at=2026-06-05T14:32:28+00:00, thread_id=019e9831-e49a-7881-b17f-6e94986d9649, design-opinion answer grounded in live tasktool code)\n1886:- Related skill: skills/superstar-project-bootstrap/SKILL.md\n1896:- syprtv, git init -b main, tasktool config init-authority --branch main, tasktool init --project syprtv, git@github.com:sigreer/syprtv.git, gh auth status, ERROR: Repository not found., reviewer-agent, external-reviewer, .worktrees/\n1898:- Related skill: skills/superstar-project-bootstrap/SKILL.md\n1913:- If the repo does not yet have its own `tools/tasktool/install.sh`, the working fallback installer is the Superstar checkout’s `bash /home/simon/Dev/sigreer/skills/superstar/tools/tasktool/install.sh --hook`, unless the user has already said hooks/shims are managed globally [Task 2]\n1914:- `external-reviewer` and `reviewer-agent` were available on `PATH`, but `reviewer-agent --help` is not a reliable availability probe because it errors on missing `AGENT_REVIEWER_REPO_ROOT`; use `command -v reviewer-agent` instead [Task 2]\n1945:- P5.S1, sport widget fixture controls overhaul, node --test, gi://GLib, .ts suffix imports, createSportTabs, external-reviewer, tasktool artifact status, tasktool artifact commit, rugby ESPN dates\n","exit_code":0,"status":"completed"}}
+{"type":"item.completed","item":{"id":"item_3","type":"agent_message","text":"I’m going to ground this against the actual worktree now: current git state, task tracker row, the target self-review document, and the implementation diff/tests. That is the only way to tell whether the post-slice evidence supports closure."}}
+{"type":"item.started","item":{"id":"item_4","type":"command_execution","command":"/usr/bin/zsh -lc 'git status --short'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_4","type":"command_execution","command":"/usr/bin/zsh -lc 'git status --short'","aggregated_output":"?? docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_5","type":"command_execution","command":"/usr/bin/zsh -lc 'git log --oneline --decorate -8'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_5","type":"command_execution","command":"/usr/bin/zsh -lc 'git log --oneline --decorate -8'","aggregated_output":"d1d478b (HEAD -> worktree-p9-s2-deterministic-preflight-gate) P9.S2: document preflight + add spec/plan self-review checklists; uniform tracker-context guidance\nce5f929 P9.S2: auto-run preflight on review round 1 (exit 4) + --no-preflight\n838f7ae P9.S2: external-reviewer preflight subcommand (text/json, exit 0/4)\n833f049 P9.S2: deterministic preflight check core (run_preflight_checks + helpers)\nfa9a8f5 (main) P9.S2: set workflow_step=implement after plan gate\n2fc1af7 P9.S2: add preflight-gate + self-review implementation plan + handoff\n2d1b9b6 P9.S2: add deterministic preflight gate + self-review spec\n5d374a0 Sync plugins/superstar mirror to 6.9.1\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_6","type":"command_execution","command":"/usr/bin/zsh -lc 'cat /tmp/p9s2-brief.md'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_6","type":"command_execution","command":"/usr/bin/zsh -lc 'cat /tmp/p9s2-brief.md'","aggregated_output":"# P9.S2 — Deterministic preflight gate + strengthened self-review checklists [step: implement]\nstatus: ready\nworkflow_step: implement\nplan: docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md\ndepends_on:\n  - P9.S1\nplanning_status: proposed\nreviewer_chain: docs/reviewer/p9-s2-preflight-gate-self-review-plan\n\nParent phase: P9 — Review-pipeline efficiency: fewer rounds, cheaper rounds [ready]\n\nSibling slices:\n  S1  [done]  Quick wins: kind-aware depth defaults, context trimming, resolution gate for all kinds, model tiering, stats --since + per-slice metric\n  S2  [ready]  Deterministic preflight gate + strengthened self-review checklists\n  S3  [ready]  Combined spec+plan gate for small slices\n\nOpen tasks:\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_7","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md | sed -n '1,260p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_7","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md | sed -n '1,260p'\"","aggregated_output":"     1\t# P9.S2 — Deterministic Preflight Gate + Strengthened Self-Review Checklists Implementation Plan\n     2\t\n     3\t> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.\n     4\t\n     5\t**Goal:** Add an `external-reviewer preflight` subcommand and a round-1 auto-gate that catch mechanical revise-class findings (placeholders, dangling paths, missing sections, oversized context) deterministically before any paid reviewer round, plus self-review checklists in the planning skills.\n     6\t\n     7\t**Architecture:** One pure function `run_preflight_checks(kind, target, context, repo_root) -> PreflightResult` in `skills/external-review/scripts/external-reviewer.py` does all deterministic checks (no LLM, no chain I/O). A `preflight` subcommand and the `review` round-1 path both call it. Skill-text changes document the surface and add author checklists.\n     8\t\n     9\t**Tech Stack:** Python 3 (stdlib only), pytest (`skills/external-review/tests/`), markdown skill files.\n    10\t\n    11\t**Spec:** `docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md`.\n    12\t\n    13\t**Scheduling:** `P9.S2` depends on `P9.S1` (done) and gates `P9.S3` (`tasktool schedule P9` confirms `deps=P9.S1`, `waiting_on=-`, ready). No `parallel_group`. Declared integration surfaces (same as S1, serialized behind it): `skills/external-review/scripts/external-reviewer.py`, `skills/external-review/SKILL.md`, `skills/brainstorming/SKILL.md`, `skills/writing-plans/SKILL.md`. S3 is serialized behind S2 via `depends_on`, so no sibling runs in parallel — no reservations needed. The plan does not change the dependency graph; Task 0 ratifies the slice as planned.\n    14\t\n    15\t---\n    16\t\n    17\t## Conventions used by every task\n    18\t\n    19\t- Repo root: `/home/simon/Dev/sigreer/skills/superstar` (work from an isolated worktree created via `superstar:using-git-worktrees`).\n    20\t- Line numbers below are anchors as of commit `2d1b9b6`; re-locate with the given grep if drifted.\n    21\t- The module is loaded in unit tests the way every existing test does it:\n    22\t\n    23\t```python\n    24\tfrom pathlib import Path\n    25\timport sys, importlib.util\n    26\tSCRIPTS = Path(__file__).resolve().parents[1] / \"scripts\"\n    27\tsys.path.insert(0, str(SCRIPTS))\n    28\tspec = importlib.util.spec_from_file_location(\"external_reviewer\", SCRIPTS / \"external-reviewer.py\")\n    29\ter = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)\n    30\t```\n    31\t\n    32\t- Subprocess tests reuse the `_init_repo`/`_run` harness pattern from `tests/test_resolution_gate.py` (a throwaway git repo with a `stub.sh` reviewer on `AGENT_REVIEWER_CMD`).\n    33\t- Test command: `python -m pytest skills/external-review/tests/<file> -q` from the repo root.\n    34\t\n    35\t---\n    36\t\n    37\t### Task 0: Start the slice and ratify scheduling\n    38\t\n    39\t**Files:** none (tracker only).\n    40\t\n    41\t- [ ] **Step 1: Mark the slice started**\n    42\t\n    43\tRun: `tasktool start P9.S2`\n    44\tExpected: exit 0; `tasktool show P9.S2` shows status `in_progress` / started.\n    45\t\n    46\t- [ ] **Step 2: Ratify the scheduling contract**\n    47\t\n    48\tThe plan confirms the existing graph (`deps=P9.S1`, no parallel group). Run:\n    49\t\n    50\t```bash\n    51\ttasktool ratify P9.S2\n    52\t```\n    53\t\n    54\tExpected: exit 0. `tasktool ready-slices P9` continues to list `P9.S2` (and not `P9.S3`, which waits on S2).\n    55\t\n    56\t---\n    57\t\n    58\t### Task 1: Preflight check core (`run_preflight_checks` + helpers)\n    59\t\n    60\tThe pure function and its helpers. No argparse, no chain I/O, no LLM. Built incrementally with unit tests in one new file.\n    61\t\n    62\t**Files:**\n    63\t- Modify: `skills/external-review/scripts/external-reviewer.py` (add the dataclasses + helpers + `run_preflight_checks` near the other module-level helpers — place after `apply_budget`/the `_BUDGET_SECTIONS` block region, i.e. anywhere above `def parse_args`, e.g. after line ~640; the functions are self-contained)\n    64\t- Test: `skills/external-review/tests/test_preflight.py` (create)\n    65\t\n    66\t- [ ] **Step 1: Write the failing unit tests**\n    67\t\n    68\tCreate `skills/external-review/tests/test_preflight.py`:\n    69\t\n    70\t```python\n    71\tfrom pathlib import Path\n    72\timport sys, importlib.util\n    73\tSCRIPTS = Path(__file__).resolve().parents[1] / \"scripts\"\n    74\tsys.path.insert(0, str(SCRIPTS))\n    75\tspec = importlib.util.spec_from_file_location(\"external_reviewer\", SCRIPTS / \"external-reviewer.py\")\n    76\ter = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)\n    77\t\n    78\t\n    79\tdef _run(kind, body, *, context=None, repo=None, tmp_path=None):\n    80\t    repo = repo or tmp_path\n    81\t    target = repo / \"doc.md\"\n    82\t    target.write_text(body, encoding=\"utf-8\")\n    83\t    return er.run_preflight_checks(kind, target, [Path(c) for c in (context or [])], repo)\n    84\t\n    85\t\n    86\tdef _msgs(result, severity):\n    87\t    bucket = result.failures if severity == \"failure\" else result.warnings\n    88\t    return \" || \".join(f.message for f in bucket)\n    89\t\n    90\t\n    91\t# --- target readable ---\n    92\tdef test_missing_target_is_failure(tmp_path):\n    93\t    res = er.run_preflight_checks(\"spec\", tmp_path / \"nope.md\", [], tmp_path)\n    94\t    assert not res.ok\n    95\t    assert any(f.check == \"target\" for f in res.failures)\n    96\t\n    97\t\n    98\tdef test_empty_target_is_failure(tmp_path):\n    99\t    res = _run(\"spec\", \"   \\n\\n\", tmp_path=tmp_path)\n   100\t    assert any(f.check == \"target\" for f in res.failures)\n   101\t\n   102\t\n   103\t# --- placeholders ---\n   104\tdef test_placeholder_in_prose_fails(tmp_path):\n   105\t    res = _run(\"spec\", \"# Spec\\n\\n## Acceptance criteria\\n\\nThis is TODO still.\\n\", tmp_path=tmp_path)\n   106\t    assert any(f.check == \"placeholder\" for f in res.failures)\n   107\t\n   108\t\n   109\tdef test_placeholder_in_fenced_block_exempt(tmp_path):\n   110\t    body = \"# Spec\\n\\n## Acceptance criteria\\n\\n```\\nTODO leftover\\n```\\n\"\n   111\t    res = _run(\"spec\", body, tmp_path=tmp_path)\n   112\t    assert not any(f.check == \"placeholder\" for f in res.failures)\n   113\t\n   114\t\n   115\tdef test_placeholder_in_inline_code_exempt(tmp_path):\n   116\t    body = \"# Spec\\n\\n## Acceptance criteria\\n\\nThe scanner flags `TODO` tokens.\\n\"\n   117\t    res = _run(\"spec\", body, tmp_path=tmp_path)\n   118\t    assert not any(f.check == \"placeholder\" for f in res.failures)\n   119\t\n   120\t\n   121\tdef test_triple_question_mark_placeholder(tmp_path):\n   122\t    res = _run(\"spec\", \"# S\\n\\n## Acceptance criteria\\n\\nvalue is ??? here\\n\", tmp_path=tmp_path)\n   123\t    assert any(f.check == \"placeholder\" for f in res.failures)\n   124\t\n   125\t\n   126\t# --- paths ---\n   127\tdef test_dangling_markdown_link_fails(tmp_path):\n   128\t    body = \"# S\\n\\n## Acceptance criteria\\n\\nSee [the file](docs/nope/missing.md).\\n\"\n   129\t    res = _run(\"spec\", body, tmp_path=tmp_path)\n   130\t    assert any(f.check == \"dangling-link\" for f in res.failures)\n   131\t\n   132\t\n   133\tdef test_existing_markdown_link_ok(tmp_path):\n   134\t    (tmp_path / \"docs\").mkdir()\n   135\t    (tmp_path / \"docs\" / \"real.md\").write_text(\"x\")\n   136\t    body = \"# S\\n\\n## Acceptance criteria\\n\\nSee [the file](docs/real.md).\\n\"\n   137\t    res = _run(\"spec\", body, tmp_path=tmp_path)\n   138\t    assert not any(f.check == \"dangling-link\" for f in res.failures)\n   139\t\n   140\t\n   141\tdef test_dangling_backtick_path_warns(tmp_path):\n   142\t    body = \"# S\\n\\n## Acceptance criteria\\n\\nLook at `skills/gone/x.py` for details.\\n\"\n   143\t    res = _run(\"spec\", body, tmp_path=tmp_path)\n   144\t    assert any(f.check == \"dangling-path\" for f in res.warnings)\n   145\t    assert not any(f.check == \"dangling-path\" for f in res.failures)\n   146\t\n   147\t\n   148\tdef test_fenced_path_exempt(tmp_path):\n   149\t    body = \"# S\\n\\n## Acceptance criteria\\n\\n```\\ncat skills/gone/x.py\\n```\\n\"\n   150\t    res = _run(\"spec\", body, tmp_path=tmp_path)\n   151\t    assert not any(f.check in (\"dangling-path\", \"dangling-link\") for f in res.failures + res.warnings)\n   152\t\n   153\t\n   154\tdef test_glob_and_placeholder_paths_exempt(tmp_path):\n   155\t    body = \"# S\\n\\n## Acceptance criteria\\n\\nName is `docs/specs/YYYY-MM-DD-<id>-slug.md` here.\\n\"\n   156\t    res = _run(\"spec\", body, tmp_path=tmp_path)\n   157\t    assert not any(f.path for f in res.failures + res.warnings)\n   158\t\n   159\t\n   160\tdef test_docs_reviewer_path_exempt(tmp_path):\n   161\t    body = \"# S\\n\\n## Acceptance criteria\\n\\nChain at `docs/reviewer/foo-spec/chain.json`.\\n\"\n   162\t    res = _run(\"spec\", body, tmp_path=tmp_path)\n   163\t    assert not any(f.check == \"dangling-path\" for f in res.warnings)\n   164\t\n   165\t\n   166\tdef test_url_not_treated_as_path(tmp_path):\n   167\t    body = \"# S\\n\\n## Acceptance criteria\\n\\nSee [home](https://example.com/page).\\n\"\n   168\t    res = _run(\"spec\", body, tmp_path=tmp_path)\n   169\t    assert not any(f.check == \"dangling-link\" for f in res.failures)\n   170\t\n   171\t\n   172\tdef test_path_with_line_suffix_resolves(tmp_path):\n   173\t    (tmp_path / \"src\").mkdir()\n   174\t    (tmp_path / \"src\" / \"a.py\").write_text(\"x\\n\")\n   175\t    body = \"# S\\n\\n## Acceptance criteria\\n\\nFix `src/a.py:12` now.\\n\"\n   176\t    res = _run(\"spec\", body, tmp_path=tmp_path)\n   177\t    assert not any(f.check == \"dangling-path\" for f in res.warnings)\n   178\t\n   179\t\n   180\t# --- sections ---\n   181\tdef test_spec_missing_acceptance_section_fails(tmp_path):\n   182\t    res = _run(\"spec\", \"# Spec\\n\\nProse only, no criteria heading.\\n\", tmp_path=tmp_path)\n   183\t    assert any(f.check == \"missing-section\" for f in res.failures)\n   184\t\n   185\t\n   186\tdef test_plan_needs_task_and_verification(tmp_path):\n   187\t    only_tasks = \"# Plan\\n\\n### Task 1\\n\\n- [ ] do it\\n\"\n   188\t    res = _run(\"plan\", only_tasks, tmp_path=tmp_path)\n   189\t    assert any(\"verif\" in f.message or \"verification\" in f.message for f in res.failures)\n   190\t\n   191\t\n   192\tdef test_plan_with_checkbox_and_verification_ok(tmp_path):\n   193\t    body = \"# Plan\\n\\n### Task 1\\n\\n- [ ] do it\\n\\n## Verification\\n\\nrun pytest\\n\"\n   194\t    res = _run(\"plan\", body, tmp_path=tmp_path)\n   195\t    assert not any(f.check == \"missing-section\" for f in res.failures)\n   196\t\n   197\t\n   198\tdef test_post_slice_needs_evidence_section(tmp_path):\n   199\t    res = _run(\"post-slice\", \"# Slice\\n\\n### Task 1\\n\\nno evidence heading\\n\", tmp_path=tmp_path)\n   200\t    assert any(f.check == \"missing-section\" for f in res.failures)\n   201\t\n   202\t\n   203\tdef test_design_kind_no_section_requirement(tmp_path):\n   204\t    res = _run(\"design\", \"# Design\\n\\nfree-form, no fixed shape.\\n\", tmp_path=tmp_path)\n   205\t    assert not any(f.check == \"missing-section\" for f in res.failures)\n   206\t\n   207\t\n   208\t# --- context hygiene ---\n   209\tdef test_missing_context_file_fails(tmp_path):\n   210\t    body = \"# S\\n\\n## Acceptance criteria\\n\\nok\\n\"\n   211\t    res = _run(\"spec\", body, context=[tmp_path / \"missing-ctx.md\"], tmp_path=tmp_path)\n   212\t    assert any(f.check == \"context\" for f in res.failures)\n   213\t\n   214\t\n   215\tdef test_oversized_context_warns(tmp_path):\n   216\t    big = tmp_path / \"big.json\"\n   217\t    big.write_text(\"x\" * (17 * 1024))\n   218\t    body = \"# S\\n\\n## Acceptance criteria\\n\\nok\\n\"\n   219\t    res = _run(\"spec\", body, context=[big], tmp_path=tmp_path)\n   220\t    assert any(f.check == \"context\" for f in res.warnings)\n   221\t\n   222\t\n   223\tdef test_clean_document_passes(tmp_path):\n   224\t    (tmp_path / \"docs\").mkdir()\n   225\t    (tmp_path / \"docs\" / \"real.md\").write_text(\"x\")\n   226\t    body = (\n   227\t        \"# Spec\\n\\n## Acceptance criteria\\n\\n\"\n   228\t        \"1. A real criterion referencing [a file](docs/real.md).\\n\"\n   229\t        \"2. Another grounded statement.\\n\"\n   230\t    )\n   231\t    res = _run(\"spec\", body, tmp_path=tmp_path)\n   232\t    assert res.ok\n   233\t    assert res.failures == []\n   234\t```\n   235\t\n   236\t- [ ] **Step 2: Run tests to verify they fail**\n   237\t\n   238\tRun: `python -m pytest skills/external-review/tests/test_preflight.py -q`\n   239\tExpected: FAIL — `AttributeError: module ... has no attribute 'run_preflight_checks'`.\n   240\t\n   241\t- [ ] **Step 3: Implement the dataclasses and code-masking helpers**\n   242\t\n   243\tIn `external-reviewer.py`, add this block above `def parse_args` (the `dataclass` import already exists at line 37; `re`/`Path` are imported):\n   244\t\n   245\t```python\n   246\t# --- P9.S2 deterministic preflight ----------------------------------------\n   247\t\n   248\t@dataclass\n   249\tclass PreflightFinding:\n   250\t    check: str          # \"target\" | \"placeholder\" | \"dangling-link\" |\n   251\t                        # \"dangling-path\" | \"missing-section\" | \"context\"\n   252\t    severity: str       # \"failure\" | \"warning\"\n   253\t    message: str\n   254\t    line: int | None = None\n   255\t    path: str | None = None\n   256\t\n   257\t\n   258\t@dataclass\n   259\tclass PreflightResult:\n   260\t    findings: list\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_8","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md | sed -n '1,260p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_8","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md | sed -n '1,260p'\"","aggregated_output":"     1\t# P9.S2 — Deterministic preflight gate + strengthened self-review checklists\n     2\t\n     3\t**Date:** 2026-06-09\n     4\t**Status:** draft\n     5\t**Tracker:** P9.S2 (slice of P9 — Review-pipeline efficiency)\n     6\t**Parent spec:** `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md` (S2 section)\n     7\t**Depends on:** P9.S1 (done)\n     8\t\n     9\t## Problem\n    10\t\n    11\tP9.S1 made each reviewer round cheaper (kind-aware depth defaults, model\n    12\ttiering) and added a rounds-per-slice metric. It did not reduce *round count*.\n    13\tThe phase baseline (multistore, `external-reviewer stats`, 2026-06-06) shows\n    14\tspec/plan/post-slice chains averaging ~2.3–2.7 rounds each, with revise rates of\n    15\t34–47%. The phase design observes that many `revise` findings are mechanical —\n    16\tplaceholder text, dangling file references, missing acceptance/verification\n    17\tsections, oversized tracker context — and are catchable locally for free before\n    18\tthe first paid reviewer round.\n    19\t\n    20\tToday nothing catches these locally. An author writes a spec or plan, invokes\n    21\t`external-reviewer review`, and pays a full reviewer round to be told \"this\n    22\treferences a file that does not exist\" or \"no verification section.\" That round\n    23\tplus its fix cycle is pure avoidable cost.\n    24\t\n    25\t## Goal\n    26\t\n    27\tCatch mechanical revise-class findings deterministically (no LLM calls) before\n    28\tthe first paid reviewer round, and prime authors to self-check the\n    29\tnon-mechanical drivers. Concretely:\n    30\t\n    31\t- A `external-reviewer preflight` subcommand that runs deterministic checks and\n    32\t  reports findings.\n    33\t- `external-reviewer review` auto-runs those checks on round 1 and refuses on\n    34\t  failure (escape hatch `--no-preflight`).\n    35\t- `brainstorming` and `writing-plans` self-review checklists name the top\n    36\t  historical revise drivers and instruct running preflight before external\n    37\t  review.\n    38\t\n    39\tThis is S2 of the phase. It does not change the verdict contract, chain layout,\n    40\tprovider invocation, or any S1 behaviour.\n    41\t\n    42\t## Non-goals / out of scope\n    43\t\n    44\t- No LLM calls in preflight — every check is deterministic and offline.\n    45\t- No new review *kinds*, no verdict-contract or chain-folder changes.\n    46\t- No combined spec+plan gate (that is S3; `--combined-gate`).\n    47\t- No changes to S1 behaviour (depth defaults, model tiering, resolution gate,\n    48\t  stats). S2 only adds the preflight surface and the checklist text.\n    49\t- No consumer-repo (multistore) changes.\n    50\t\n    51\t## Design\n    52\t\n    53\tAll CLI behaviour lives in\n    54\t`skills/external-review/scripts/external-reviewer.py`. Documentation lives in\n    55\t`skills/external-review/SKILL.md`, `skills/brainstorming/SKILL.md`, and\n    56\t`skills/writing-plans/SKILL.md`. Tests live in\n    57\t`skills/external-review/tests/`.\n    58\t\n    59\t### S2.a — `external-reviewer preflight` subcommand\n    60\t\n    61\t```\n    62\texternal-reviewer preflight --kind <kind> --file <target> [--context <path>]... [--emit json]\n    63\t```\n    64\t\n    65\t`--kind` takes the same choices as `review`\n    66\t(`spec|plan|design|implementation|post-slice|post-phase|other`). `--file` is the\n    67\ttarget document; `--context` may repeat. `--emit` is `text` (default) or `json`.\n    68\t\n    69\tA single pure function does the work so the subcommand and the round-1\n    70\tauto-gate share one implementation:\n    71\t\n    72\t```\n    73\trun_preflight_checks(kind, target: Path, context: list[Path], repo_root: Path) -> PreflightResult\n    74\t```\n    75\t\n    76\t`PreflightResult` carries an ordered list of findings, each a small record:\n    77\t`check` (which check produced it), `severity` (`failure` | `warning`),\n    78\t`message`, and optional `line` / `path`. Two helpers expose the rollup:\n    79\t`PreflightResult.failures` and `.warnings`. The function performs **no I/O on\n    80\tthe chain folder and no LLM calls** — it only reads the target and context\n    81\tfiles from disk.\n    82\t\n    83\tThe deterministic checks:\n    84\t\n    85\t**1. Target readable.** The target exists, is non-empty after stripping\n    86\twhitespace, and decodes as UTF-8. Any failure here is a `failure` and short-\n    87\tcircuits the remaining content checks (a binary or empty target cannot be\n    88\tmeaningfully scanned).\n    89\t\n    90\t**2. Placeholder scan.** The whole-token placeholders `TBD`, `TODO`, `FIXME`,\n    91\t`XXX`, `???`, and `lorem ipsum` (case-insensitive) anywhere in the target's\n    92\tprose are `failure`s, reported with line numbers. **Exemption:** text inside\n    93\tfenced code blocks *and* inline code spans (single/double backtick) is masked\n    94\tbefore the scan. The phase design exempts fenced blocks; this slice also\n    95\texempts inline code spans because specs and plans legitimately name these\n    96\ttokens in backticks when describing tooling (this very document does), and an\n    97\tinline-code mention is not an unfinished-work marker. Masking replaces exempt\n    98\tregions with same-length spaces so reported line/column positions stay\n    99\taccurate. Whole-token matching uses boundaries appropriate to each token\n   100\t(word-boundary for the alphanumeric tokens; literal match for `???`).\n   101\t\n   102\t**3. Referenced-path check.** Two syntaxes are scanned outside masked code\n   103\tregions:\n   104\t\n   105\t- **Markdown links** — `[text](path)`. A path that looks repo-relative but does\n   106\t  not exist on disk is a `failure`.\n   107\t- **Backtick-quoted strings** — an inline-code span whose content looks like a\n   108\t  repo-relative path but does not exist is a `warning` (prose cites paths\n   109\t  illustratively; a dangling backtick path is worth flagging but not blocking).\n   110\t\n   111\t\"Looks repo-relative\" heuristic: the string contains `/` **and** either has a\n   112\tfile extension (a `.` in the final segment) or its first segment is a known\n   113\tproject directory (`docs`, `skills`, `tools`, `hooks`, `scripts`, `tests`,\n   114\t`src`). Exemptions (skipped entirely, no finding):\n   115\t\n   116\t- Anything inside a fenced code block (illustrative command/code).\n   117\t- Paths containing placeholder/glob characters: `<`, `>`, `*`, `{`, `}`, `$`,\n   118\t  `…` (e.g. `docs/specs/YYYY-MM-DD-<id>-slug.md`).\n   119\t- Paths whose first segment is `docs/reviewer` (future/generated reviewer\n   120\t  artifacts that legitimately do not exist yet).\n   121\t- URLs (a scheme like `http://`, `https://`, `mailto:`).\n   122\t\n   123\tPaths are resolved relative to `repo_root`. Absolute paths are resolved as-is.\n   124\tNote the asymmetry: the markdown-link scan runs on text with **fenced blocks\n   125\tmasked but inline code visible** (so `[x](path)` links are seen); the backtick\n   126\tscan reads inline-code spans directly. Fenced content is exempt for both.\n   127\t\n   128\t**4. Kind-required sections.** Heading detection is keyword-based and tolerant\n   129\tof phrasing — a heading line (`#`-prefixed) whose text matches the keyword\n   130\t(case-insensitive substring) counts.\n   131\t\n   132\t- `plan` → requires **both** a task section (a heading matching `task`, or the\n   133\t  presence of any GitHub-style checkbox line `- [ ]` / `- [x]`) **and** a\n   134\t  verification/acceptance section (heading matching `verif`, `accept`, or\n   135\t  `gate`). A missing either is a `failure`.\n   136\t- `spec` → requires an acceptance-criteria section (heading matching `accept`\n   137\t  or `criteria`). Missing is a `failure`.\n   138\t- `post-slice` / `post-phase` → require an evidence/verification section\n   139\t  (heading matching `verif`, `evidence`, or `accept`) in the target. Missing is\n   140\t  a `failure`.\n   141\t- `design` / `implementation` / `other` → no required-section check (these\n   142\t  kinds have no fixed shape).\n   143\t\n   144\t**5. Context hygiene.** In the **standalone `preflight` subcommand**, a missing\n   145\t`--file` target or a missing `--context` path is a `failure` surfaced in the\n   146\tfindings list (the subcommand has no other validation layer, so it must report\n   147\tmissing files itself). In the **`review` auto-preflight path** this case never\n   148\tarises: `review` already hard-fails a missing target or context with **exit 2\n   149\tbefore** chain discovery or the preflight gate (current\n   150\t`external-reviewer.py` behaviour, preserved unchanged — so `--no-preflight`\n   151\tstays byte-identical to today). Any existing context file larger than 16 KB\n   152\tproduces a `warning` naming the file and its size, hinting to pass\n   153\t`tasktool brief <work-id>` output instead (this catches the\n   154\tfull-`docs/tasklist.json` habit S1.b discouraged in prose). The 16 KB warning\n   155\tapplies in both the subcommand and the auto-preflight path.\n   156\t\n   157\t**Output and exit codes.** Text mode prints a grouped findings list\n   158\t(failures first, then warnings) with a one-line summary; a clean run prints a\n   159\tshort \"preflight passed\" line. `--emit json` prints\n   160\t`{\"ok\": <bool>, \"failures\": [...], \"warnings\": [...]}` where each entry is the\n   161\tfinding record. **Exit 0** = no failures (warnings allowed); **exit 4** =\n   162\tone or more failures. Exit 4 is the phase-design-assigned preflight failure\n   163\tcode, deliberately distinct from the exit-3 resolution gate.\n   164\t\n   165\tExit 4 is also returned by `review` for a schema-too-new manifest. The two are\n   166\tsequential, never simultaneous: in `review`, the manifest is read (and a\n   167\tschema-too-new manifest aborts with exit 4) **before** the round number is\n   168\tknown, and the round-1 auto-preflight (S2.b) needs the round number, so it runs\n   169\tstrictly after the manifest read. A schema-too-new manifest therefore aborts\n   170\tbefore preflight ever runs — preflight cannot mask it. The shared code is\n   171\taccepted: both causes mean \"input not reviewable, fix it,\" and introducing a\n   172\tnew code for preflight would diverge from the phase design's exit-4 assignment.\n   173\t\n   174\t### S2.b — Auto-preflight on round 1\n   175\t\n   176\t`review` runs `run_preflight_checks` in-process **before submitting a round-1\n   177\treview** and refuses on failure, printing the same findings list and returning\n   178\texit 4. The gate fires only when `round_num == 1` (the broad first round).\n   179\tIncremental rounds (N+1) skip it — the diff/resolution machinery already covers\n   180\tthem, and re-scanning an already-reviewed document for dangling paths adds\n   181\tfriction without catching revise drivers.\n   182\t\n   183\tA new `--no-preflight` flag on the `review` subparser skips the auto-gate\n   184\tentirely (escape hatch for an author who has deliberately accepted a finding, or\n   185\tfor non-standard documents). When skipped, behaviour is byte-identical to today.\n   186\t\n   187\tThe exact sequence inside `review` is: (1) resolve `--file` and `--context`\n   188\tpaths, **including the existing existence validation that returns exit 2 for a\n   189\tmissing target or context file** before any manifest or preflight work (this\n   190\tcheck is preserved unchanged, so a missing file is never deferred into a\n   191\tpreflight exit-4 finding in the `review` path); (2) discover/read the chain\n   192\tmanifest — a schema-too-new manifest aborts here with exit 4; (3) apply the\n   193\tresolution-required gate (round 2+ only);\n   194\t(4) determine the round number from the chain; (5) **if `round_num == 1` and not\n   195\t`--no-preflight`, run `run_preflight_checks` and return exit 4 on any failure**;\n   196\t(6) only then construct the prompt and spawn the reviewer. The gate runs after\n   197\tthe round number is known but before any reviewer process is spawned, so a\n   198\tfailing preflight costs nothing in reviewer time. Warnings do not block — they\n   199\tprint to stderr and the review proceeds.\n   200\t\n   201\tThe chain folder is created (and the manifest eager-written) before the round\n   202\tnumber is determined, so a round-1 preflight failure leaves an **empty chain\n   203\tfolder with no round artifacts**. This is acceptable: the empty folder is inert\n   204\tand is reused on the re-run once the failures are fixed. No round entry, request\n   205\tfile, or response file is written for a preflight-refused round.\n   206\t\n   207\t### S2.c — Self-review checklists\n   208\t\n   209\t`brainstorming` (spec self-review section) and `writing-plans` (plan self-review\n   210\tsection) gain a short checklist of the top historical revise drivers, framed as\n   211\texplicit author checks:\n   212\t\n   213\t- Vague verification steps (\"verify it works\" with no command to run).\n   214\t- Claims not grounded in the repo (referenced functions, flags, or files that\n   215\t  do not exist).\n   216\t- Tasklist drift (work-id, status, or dependency mismatch vs\n   217\t  `docs/tasklist.json`).\n   218\t- Acceptance criteria a reviewer cannot evaluate from the document alone.\n   219\t\n   220\tEach checklist ends by instructing the author to run\n   221\t`external-reviewer preflight --kind <kind> --file <doc>` (with the same\n   222\t`--context` they will pass to `review`) and fix any failures before invoking\n   223\texternal review. `external-reviewer SKILL.md` documents the `preflight`\n   224\tsubcommand, the round-1 auto-gate, and `--no-preflight`.\n   225\t\n   226\t## Acceptance criteria\n   227\t\n   228\t1. `external-reviewer preflight --kind spec --file <doc>` exists, runs no LLM\n   229\t   calls, and prints a findings list; `--emit json` prints\n   230\t   `{\"ok\", \"failures\", \"warnings\"}`.\n   231\t2. Each check class is caught on a purpose-built fixture **via the standalone\n   232\t   `preflight` subcommand**: a placeholder token in prose (failure), a dangling\n   233\t   markdown link (failure), a dangling backtick path (warning), a missing\n   234\t   kind-required section (failure), a missing context file (failure, subcommand\n   235\t   only), and an oversized (>16 KB) context file (warning).\n   236\t3. A known-good document (no placeholders, all links resolve, required sections\n   237\t   present, lean context) passes with exit 0 and zero failures.\n   238\t4. Exemptions hold, with the placeholder scan and path scan treating inline\n   239\t   code differently:\n   240\t   - Placeholder tokens inside fenced code blocks **and** inline-code spans\n   241\t     produce no placeholder finding.\n   242\t   - A path inside a fenced code block produces no path finding.\n   243\t   - A dangling repo-relative path inside an **inline-code span** produces a\n   244\t     `warning` (it is scanned, not suppressed) — unless separately exempt.\n   245\t   - Paths with glob/placeholder characters, `docs/reviewer/` paths, and URLs\n   246\t     produce no path finding regardless of where they appear.\n   247\t5. `external-reviewer review` auto-runs preflight on round 1 and returns exit 4\n   248\t   (no reviewer process spawned) when a content failure is present;\n   249\t   `--no-preflight` skips the gate and the review proceeds; round 2+ never runs\n   250\t   the auto-gate. A missing `--file`/`--context` in the `review` path still\n   251\t   returns exit 2 from the existing early validation (not deferred into\n   252\t   preflight exit 4).\n   253\t6. Exit codes: preflight content failures return 4, a clean preflight returns 0,\n   254\t   warnings alone return 0; the `review` path's pre-existing missing-file\n   255\t   validation continues to return exit 2.\n   256\t7. `external-reviewer SKILL.md`, `brainstorming/SKILL.md`, and\n   257\t   `writing-plans/SKILL.md` document the preflight subcommand, the round-1\n   258\t   auto-gate / `--no-preflight`, and the self-review checklist with the\n   259\t   revise-driver list.\n   260\t8. The existing `skills/external-review/tests/` suite passes, and the new\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_9","type":"command_execution","command":"/usr/bin/zsh -lc 'tasktool show P9.S2'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_9","type":"command_execution","command":"/usr/bin/zsh -lc 'tasktool show P9.S2'","aggregated_output":"# P9.S2 — Deterministic preflight gate + strengthened self-review checklists\nstatus: ready\nworkflow_step: implement\ndepends_on:\n  - P9.S1\nplanning_status: proposed\nrefs:\n  - docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md\n  - docs/reviewer/p9-s2-preflight-gate-self-review-design-spec\n  - docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md\n  - docs/handoffs/2026-06-09-P9.S2-preflight-gate-self-review-prompt.md\n  - docs/reviewer/p9-s2-preflight-gate-self-review-plan\nnotes:\nP9.S1 Task 6 review flagged stale tracker-context guidance in skills/executing-plans/SKILL.md (~line 55) and skills/tasklist-discipline/SKILL.md (~line 205): both still instruct passing full docs/tasklist.json with no tasktool-brief preference or --work-id mention. Fold the uniform-guidance fix into S2's checklist work.\n\nTasks:\n","exit_code":0,"status":"completed"}}
+{"type":"item.completed","item":{"id":"item_10","type":"agent_message","text":"Initial state already shows a scope issue: the only dirty item is the new post-slice reviewer chain, while the slice row is still `status: ready` / `workflow_step: implement`. I’m checking whether the self-review document records this as intentionally pre-close or whether it claims completion anyway."}}
+{"type":"item.started","item":{"id":"item_11","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md | sed -n '260,760p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_11","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md | sed -n '260,760p'\"","aggregated_output":"   260\t    findings: list\n   261\t\n   262\t    @property\n   263\t    def failures(self) -> list:\n   264\t        return [f for f in self.findings if f.severity == \"failure\"]\n   265\t\n   266\t    @property\n   267\t    def warnings(self) -> list:\n   268\t        return [f for f in self.findings if f.severity == \"warning\"]\n   269\t\n   270\t    @property\n   271\t    def ok(self) -> bool:\n   272\t        return not self.failures\n   273\t\n   274\t\n   275\t_FENCE_LINE_RE = re.compile(r\"^\\s*(`{3,}|~{3,})\")\n   276\t_INLINE_CODE_RE = re.compile(r\"(`+)(.+?)\\1\")\n   277\t\n   278\t\n   279\tdef _blank_like(line: str) -> str:\n   280\t    \"\"\"Replace every non-newline char with a space (keeps offsets stable).\"\"\"\n   281\t    return re.sub(r\"[^\\n]\", \" \", line)\n   282\t\n   283\t\n   284\tdef _mask_fenced(text: str) -> str:\n   285\t    \"\"\"Blank out fenced code blocks (and their fence lines), preserving line\n   286\t    count and length so reported line numbers stay accurate.\"\"\"\n   287\t    out = []\n   288\t    in_fence = False\n   289\t    marker = None\n   290\t    for line in text.splitlines(keepends=True):\n   291\t        m = _FENCE_LINE_RE.match(line)\n   292\t        if not in_fence:\n   293\t            if m:\n   294\t                in_fence = True\n   295\t                marker = m.group(1)[0]\n   296\t                out.append(_blank_like(line))\n   297\t            else:\n   298\t                out.append(line)\n   299\t        else:\n   300\t            close = m and m.group(1)[0] == marker\n   301\t            out.append(_blank_like(line))\n   302\t            if close:\n   303\t                in_fence = False\n   304\t                marker = None\n   305\t    return \"\".join(out)\n   306\t\n   307\t\n   308\tdef _mask_inline_code(text: str) -> str:\n   309\t    \"\"\"Blank inline-code spans (after fenced blocks are already masked).\"\"\"\n   310\t    return _INLINE_CODE_RE.sub(lambda m: \" \" * len(m.group(0)), text)\n   311\t\n   312\t\n   313\tdef _inline_code_spans(text: str):\n   314\t    \"\"\"Yield (line_no, content) for inline-code spans outside fenced blocks.\"\"\"\n   315\t    fmasked = _mask_fenced(text)\n   316\t    for m in _INLINE_CODE_RE.finditer(fmasked):\n   317\t        line_no = fmasked.count(\"\\n\", 0, m.start()) + 1\n   318\t        yield line_no, m.group(2)\n   319\t```\n   320\t\n   321\t- [ ] **Step 4: Implement the placeholder scan**\n   322\t\n   323\tAdd below the masking helpers:\n   324\t\n   325\t```python\n   326\t_PLACEHOLDER_TOKENS = [\n   327\t    (re.compile(r\"\\bTBD\\b\", re.IGNORECASE), \"TBD\"),\n   328\t    (re.compile(r\"\\bTODO\\b\", re.IGNORECASE), \"TODO\"),\n   329\t    (re.compile(r\"\\bFIXME\\b\", re.IGNORECASE), \"FIXME\"),\n   330\t    (re.compile(r\"\\bXXX\\b\", re.IGNORECASE), \"XXX\"),\n   331\t    (re.compile(r\"\\?{3,}\"), \"???\"),\n   332\t    (re.compile(r\"\\blorem ipsum\\b\", re.IGNORECASE), \"lorem ipsum\"),\n   333\t]\n   334\t\n   335\t\n   336\tdef _scan_placeholders(text: str, findings: list) -> None:\n   337\t    masked = _mask_inline_code(_mask_fenced(text))\n   338\t    for i, line in enumerate(masked.splitlines(), start=1):\n 

[… 392251 bytes elided to fit cap of 160000 bytes …]

"formula": "ceil(chars / 4)",
+            "prompt_chars": 41778,
+            "response_chars": 3497,
+            "estimated_input_tokens": 10445,
+            "estimated_output_tokens": 875,
+            "estimated_total_tokens": 11320
+          },
+          "exact_usage": null,
+          "usage_capture_status": "estimated_only",
+          "usage_capture_error": null
+        }
+      ],
+      "status": "ok",
+      "returncode": 0,
+      "started_at": "2026-06-09T03:56:14.480Z",
+      "finished_at": "2026-06-09T03:59:07.284Z",
+      "duration_ms": 172804,
+      "provider": "codex",
+      "caller_provider": "claude",
+      "model": null,
+      "estimated_usage": {
+        "formula": "ceil(chars / 4)",
+        "prompt_chars": 41778,
+        "response_chars": 3222,
+        "estimated_input_tokens": 10445,
+        "estimated_output_tokens": 806,
+        "estimated_total_tokens": 11251
+      },
+      "exact_usage": null,
+      "usage_capture_status": "estimated_only",
+      "usage_capture_error": null,
+      "merged_verdict": "revise",
+      "merged_findings": "r1-merged-findings.md",
+      "request": "r1-2026-06-09T0456-primary-request.md",
+      "response": "r1-2026-06-09T0456-primary-response.md",
+      "resolution": null,
+      "resolution_parse_status": null,
+      "resolution_waiver": false,
+      "head_sha_at_request": "d1d478b79ae89be5c4d08b9477c9a5e4506b9a64",
+      "head_sha_after_round": "d1d478b79ae89be5c4d08b9477c9a5e4506b9a64",
+      "worktree_dirty_at_request": true,
+      "verdict": "revise",
+      "verdict_valid": true,
+      "findings_count": 2,
+      "blocking_findings_count": 1,
+      "base_ref": null,
+      "base_ref_source": null,
+      "diff_included": false,
+      "depth_resolved": "thorough"
+    }
+  ],
+  "sweep_checkpoints": {
+    "first-round": "completed",
+    "final-ready": "pending"
+  }
+}
diff --git a/docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/r1-2026-06-09T0456-primary-request.md b/docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/r1-2026-06-09T0456-primary-request.md
new file mode 100644
index 0000000..12506bf
--- /dev/null
+++ b/docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/r1-2026-06-09T0456-primary-request.md
@@ -0,0 +1,887 @@
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
+/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p9-s2-deterministic-preflight-gate
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
+docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md
+
+Additional context files:
+- docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md
+- /tmp/p9s2-brief.md
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
+### docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md
+
+    1	# P9.S2 — Deterministic Preflight Gate + Strengthened Self-Review Checklists Implementation Plan
+    2	
+    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
+    4	
+    5	**Goal:** Add an `external-reviewer preflight` subcommand and a round-1 auto-gate that catch mechanical revise-class findings (placeholders, dangling paths, missing sections, oversized context) deterministically before any paid reviewer round, plus self-review checklists in the planning skills.
+    6	
+    7	**Architecture:** One pure function `run_preflight_checks(kind, target, context, repo_root) -> PreflightResult` in `skills/external-review/scripts/external-reviewer.py` does all deterministic checks (no LLM, no chain I/O). A `preflight` subcommand and the `review` round-1 path both call it. Skill-text changes document the surface and add author checklists.
+    8	
+    9	**Tech Stack:** Python 3 (stdlib only), pytest (`skills/external-review/tests/`), markdown skill files.
+   10	
+   11	**Spec:** `docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md`.
+   12	
+   13	**Scheduling:** `P9.S2` depends on `P9.S1` (done) and gates `P9.S3` (`tasktool schedule P9` confirms `deps=P9.S1`, `waiting_on=-`, ready). No `parallel_group`. Declared integration surfaces (same as S1, serialized behind it): `skills/external-review/scripts/external-reviewer.py`, `skills/external-review/SKILL.md`, `skills/brainstorming/SKILL.md`, `skills/writing-plans/SKILL.md`. S3 is serialized behind S2 via `depends_on`, so no sibling runs in parallel — no reservations needed. The plan does not change the dependency graph; Task 0 ratifies the slice as planned.
+   14	
+   15	---
+   16	
+   17	## Conventions used by every task
+   18	
+   19	- Repo root: `/home/simon/Dev/sigreer/skills/superstar` (work from an isolated worktree created via `superstar:using-git-worktrees`).
+   20	- Line numbers below are anchors as of commit `2d1b9b6`; re-locate with the given grep if drifted.
+   21	- The module is loaded in unit tests the way every existing test does it:
+   22	
+   23	```python
+   24	from pathlib import Path
+   25	import sys, importlib.util
+   26	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
+   27	sys.path.insert(0, str(SCRIPTS))
+   28	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
+   29	er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
+   30	```
+   31	
+   32	- Subprocess tests reuse the `_init_repo`/`_run` harness pattern from `tests/test_resolution_gate.py` (a throwaway git repo with a `stub.sh` reviewer on `AGENT_REVIEWER_CMD`).
+   33	- Test command: `python -m pytest skills/external-review/tests/<file> -q` from the repo root.
+   34	
+   35	---
+   36	
+   37	### Task 0: Start the slice and ratify scheduling
+   38	
+   39	**Files:** none (tracker only).
+   40	
+   41	- [ ] **Step 1: Mark the slice started**
+   42	
+   43	Run: `tasktool start P9.S2`
+   44	Expected: exit 0; `tasktool show P9.S2` shows status `in_progress` / started.
+   45	
+   46	- [ ] **Step 2: Ratify the scheduling contract**
+   47	
+   48	The plan confirms the existing graph (`deps=P9.S1`, no parallel group). Run:
+   49	
+   50	```bash
+   51	tasktool ratify P9.S2
+   52	```
+   53	
+   54	Expected: exit 0. `tasktool ready-slices P9` continues to list `P9.S2` (and not `P9.S3`, which waits on S2).
+   55	
+   56	---
+   57	
+   58	### Task 1: Preflight check core (`run_preflight_checks` + helpers)
+   59	
+   60	The pure function and its helpers. No argparse, no chain I/O, no LLM. Built incrementally with unit tests in one new file.
+   61	
+   62	**Files:**
+   63	- Modify: `skills/external-review/scripts/external-reviewer.py` (add the dataclasses + helpers + `run_preflight_checks` near the other module-level helpers — place after `apply_budget`/the `_BUDGET_SECTIONS` block region, i.e. anywhere above `def parse_args`, e.g. after line ~640; the functions are self-contained)
+   64	- Test: `skills/external-review/tests/test_preflight.py` (create)
+   65	
+   66	- [ ] **Step 1: Write the failing unit tests**
+   67	
+   68	Create `skills/external-review/tests/test_preflight.py`:
+   69	
+   70	```python
+   71	from pathlib import Path
+   72	import sys, importlib.util
+   73	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
+   74	sys.path.insert(0, str(SCRIPTS))
+   75	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
+   76	er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
+   77	
+   78	
+   79	def _run(kind, body, *, context=None, repo=None, tmp_path=None):
+   80	    repo = repo or tmp_path
+   81	    target = repo / "doc.md"
+   82	    target.write_text(body, encoding="utf-8")
+   83	    return er.run_preflight_checks(kind, target, [Path(c) for c in (context or [])], repo)
+   84	
+   85	
+   86	def _msgs(result, severity):
+   87	    bucket = result.failures if severity == "failure" else result.warnings
+   88	    return " || ".join(f.message for f in bucket)
+   89	
+   90	
+   91	# --- target readable ---
+   92	def test_missing_target_is_failure(tmp_path):
+   93	    res = er.run_preflight_checks("spec", tmp_path / "nope.md", [], tmp_path)
+   94	    assert not res.ok
+   95	    assert any(f.check == "target" for f in res.failures)
+   96	
+   97	
+   98	def test_empty_target_is_failure(tmp_path):
+   99	    res = _run("spec", "   \n\n", tmp_path=tmp_path)
+  100	    assert any(f.check == "target" for f in res.failures)
+  101	
+  102	
+  103	# --- placeholders ---
+  104	def test_placeholder_in_prose_fails(tmp_path):
+  105	    res = _run("spec", "# Spec\n\n## Acceptance criteria\n\nThis is TODO still.\n", tmp_path=tmp_path)
+  106	    assert any(f.check == "placeholder" for f in res.failures)
+  107	
+  108	
+  109	def test_placeholder_in_fenced_block_exempt(tmp_path):
+  110	    body = "# Spec\n\n## Acceptance criteria\n\n```\nTODO leftover\n```\n"
+  111	    res = _run("spec", body, tmp_path=tmp_path)
+  112	    assert not any(f.check == "placeholder" for f in res.failures)
+  113	
+  114	
+  115	def test_placeholder_in_inline_code_exempt(tmp_path):
+  116	    body = "# Spec\n\n## Acceptance criteria\n\nThe scanner flags `TODO` tokens.\n"
+  117	    res = _run("spec", body, tmp_path=tmp_path)
+  118	    assert not any(f.check == "placeholder" for f in res.failures)
+  119	
+  120	
+  121	def test_triple_question_mark_placeholder(tmp_path):
+  122	    res = _run("spec", "# S\n\n## Acceptance criteria\n\nvalue is ??? here\n", tmp_path=tmp_path)
+  123	    assert any(f.check == "placeholder" for f in res.failures)
+  124	
+  125	
+  126	# --- paths ---
+  127	def test_dangling_markdown_link_fails(tmp_path):
+  128	    body = "# S\n\n## Acceptance criteria\n\nSee [the file](docs/nope/missing.md).\n"
+  129	    res = _run("spec", body, tmp_path=tmp_path)
+  130	    assert any(f.check == "dangling-link" for f in res.failures)
+  131	
+  132	
+  133	def test_existing_markdown_link_ok(tmp_path):
+  134	    (tmp_path / "docs").mkdir()
+  135	    (tmp_path / "docs" / "real.md").write_text("x")
+  136	    body = "# S\n\n## Acceptance criteria\n\nSee [the file](docs/real.md).\n"
+  137	    res = _run("spec", body, tmp_path=tmp_path)
+  138	    assert not any(f.check == "dangling-link" for f in res.failures)
+  139	
+  140	
+  141	def test_dangling_backtick_path_warns(tmp_path):
+  142	    body = "# S\n\n## Acceptance criteria\n\nLook at `skills/gone/x.py` for details.\n"
+  143	    res = _run("spec", body, tmp_path=tmp_path)
+  144	    assert any(f.check == "dangling-path" for f in res.warnings)
+  145	    assert not any(f.check == "dangling-path" for f in res.failures)
+  146	
+  147	
+  148	def test_fenced_path_exempt(tmp_path):
+  149	    body = "# S\n\n## Acceptance criteria\n\n```\ncat skills/gone/x.py\n```\n"
+  150	    res = _run("spec", body, tmp_path=tmp_path)
+  151	    assert not any(f.check in ("dangling-path", "dangling-link") for f in res.failures + res.warnings)
+  152	
+  153	
+  154	def test_glob_and_placeholder_paths_exempt(tmp_path):
+  155	    body = "# S\n\n## Acceptance criteria\n\nName is `docs/specs/YYYY-MM-DD-<id>-slug.md` here.\n"
+  156	    res = _run("spec", body, tmp_path=tmp_path)
+  157	    assert not any(f.path for f in res.failures + res.warnings)
+  158	
+  159	
+  160	def test_docs_reviewer_path_exempt(tmp_path):
+  161	    body = "# S\n\n## Acceptance criteria\n\nChain at `docs/reviewer/foo-spec/chain.json`.\n"
+  162	    res = _run("spec", body, tmp_path=tmp_path)
+  163	    assert not any(f.check == "dangling-path" for f in res.warnings)
+  164	
+  165	
+  166	def test_url_not_treated_as_path(tmp_path):
+  167	    body = "# S\n\n## Acceptance criteria\n\nSee [home](https://example.com/page).\n"
+  168	    res = _run("spec", body, tmp_path=tmp_path)
+  169	    assert not any(f.check == "dangling-link" for f in res.failures)
+  170	
+  171	
+  172	def test_path_with_line_suffix_resolves(tmp_path):
+  173	    (tmp_path / "src").mkdir()
+  174	    (tmp_path / "src" / "a.py").write_text("x\n")
+  175	    body = "# S\n\n## Acceptance criteria\n\nFix `src/a.py:12` now.\n"
+  176	    res = _run("spec", body, tmp_path=tmp_path)
+  177	    assert not any(f.check == "dangling-path" for f in res.warnings)
+  178	
+  179	
+  180	# --- sections ---
+  181	def test_spec_missing_acceptance_section_fails(tmp_path):
+  182	    res = _run("spec", "# Spec\n\nProse only, no criteria heading.\n", tmp_path=tmp_path)
+  183	    assert any(f.check == "missing-section" for f in res.failures)
+  184	
+  185	
+  186	def test_plan_needs_task_and_verification(tmp_path):
+  187	    only_tasks = "# Plan\n\n### Task 1\n\n- [ ] do it\n"
+  188	    res = _run("plan", only_tasks, tmp_path=tmp_path)
+  189	    assert any("verif" in f.message or "verification" in f.message for f in res.failures)
+  190	
+  191	
+  192	def test_plan_with_checkbox_and_verification_ok(tmp_path):
+  193	    body = "# Plan\n\n### Task 1\n\n- [ ] do it\n\n## Verification\n\nrun pytest\n"
+  194	    res = _run("plan", body, tmp_path=tmp_path)
+  195	    assert not any(f.check == "missing-section" for f in res.failures)
+  196	
+  197	
+  198	def test_post_slice_needs_evidence_section(tmp_path):
+  199	    res = _run("post-slice", "# Slice\n\n### Task 1\n\nno evidence heading\n", tmp_path=tmp_path)
+  200	    assert any(f.check == "missing-section" for f in res.failures)
+  201	
+  202	
+  203	def test_design_kind_no_section_requirement(tmp_path):
+  204	    res = _run("design", "# Design\n\nfree-form, no fixed shape.\n", tmp_path=tmp_path)
+  205	    assert not any(f.check == "missing-section" for f in res.failures)
+  206	
+  207	
+  208	# --- context hygiene ---
+  209	def test_missing_context_file_fails(tmp_path):
+  210	    body = "# S\n\n## Acceptance criteria\n\nok\n"
+  211	    res = _run("spec", body, context=[tmp_path / "missing-ctx.md"], tmp_path=tmp_path)
+  212	    assert any(f.check == "context" for f in res.failures)
+  213	
+  214	
+  215	def test_oversized_context_warns(tmp_path):
+  216	    big = tmp_path / "big.json"
+  217	    big.write_text("x" * (17 * 1024))
+  218	    body = "# S\n\n## Acceptance criteria\n\nok\n"
+  219	    res = _run("spec", body, context=[big], tmp_path=tmp_path)
+  220	    assert any(f.check == "context" for f in res.warnings)
+  221	
+  222	
+  223	def test_clean_document_passes(tmp_path):
+  224	    (tmp_path / "docs").mkdir()
+  225	    (tmp_path / "docs" / "real.md").write_text("x")
+  226	    body = (
+  227	        "# Spec\n\n## Acceptance criteria\n\n"
+  228	        "1. A real criterion referencing [a file](docs/real.md).\n"
+  229	        "2. Another grounded statement.\n"
+  230	    )
+  231	    res = _run("spec", body, tmp_path=tmp_path)
+  232	    assert res.ok
+  233	    assert res.failures == []
+  234	```
+  235	
+  236	- [ ] **Step 2: Run tests to verify they fail**
+  237	
+  238	Run: `python -m pytest skills/external-review/tests/test_preflight.py -q`
+  239	Expected: FAIL — `AttributeError: module ... has no attribute 'run_preflight_checks'`.
+  240	
+  241	- [ ] **Step 3: Implement the dataclasses and code-masking helpers**
+  242	
+  243	In `external-reviewer.py`, add this block above `def parse_args` (the `dataclass` import already exists at line 37; `re`/`Path` are imported):
+  244	
+  245	```python
+  246	# --- P9.S2 deterministic preflight ----------------------------------------
+  247	
+  248	@dataclass
+  249	class PreflightFinding:
+  250	    check: str          # "target" | "placeholder" | "dangling-link" |
+  251	                        # "dangling-path" | "missing-section" | "context"
+  252	    severity: str       # "failure" | "warning"
+  253	    message: str
+  254	    line: int | None = None
+  255	    path: str | None = None
+  256	
+  257	
+  258	@dataclass
+  259	class PreflightResult:
+  260	    findings: list
+  261	
+  262	    @property
+  263	    def failures(self) -> list:
+  264	        return [f for f in self.findings if f.severity == "failure"]
+  265	
+  266	    @property
+  267	    def warnings(self) -> list:
+  268	        return [f for f in self.findings if f.severity == "warning"]
+  269	
+  270	    @property
+  271	    def ok(self) -> bool:
+  272	        return not self.failures
+  273	
+  274	
+  275	_FENCE_LINE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
+  276	_INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1")
+  277	
+  278	
+  279	def _blank_like(line: str) -> str:
+  280	    """Replace every non-newline char with a space (keeps offsets stable)."""
+  281	    return re.sub(r"[^\n]", " ", line)
+  282	
+  283	
+  284	def _mask_fenced(text: str) -> str:
+  285	    """Blank out fenced code blocks (and their fence lines), preserving line
+  286	    count and length so reported line numbers stay accurate."""
+  287	    out = []
+  288	    in_fence = False
+  289	    marker = None
+  290	    for line in text.splitlines(keepends=True):
+  291	        m = _FENCE_LINE_RE.match(line)
+  292	        if not in_fence:
+  293	            if m:
+  294	                in_fence = True
+  295	                marker = m.group(1)[0]
+  296	                out.append(_blank_like(line))
+  297	            else:
+  298	                out.append(line)
+  299	        else:
+  300	            close = m and m.group(1)[0] == marker
+  301	            out.append(_blank_like(line))
+  302	            if close:
+  303	                in_fence = False
+  304	                marker = None
+  305	    return "".join(out)
+  306	
+  307	
+  308	def _mask_inline_code(text: str) -> str:
+  309	    """Blank inline-code spans (after fenced blocks are already masked)."""
+  310	    return _INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), text)
+  311	
+  312	
+  313	def _inline_code_spans(text: str):
+  314	    """Yield (line_no, content) for inline-code spans outside fenced blocks."""
+  315	    fmasked = _mask_fenced(text)
+  316	    for m in _INLINE_CODE_RE.finditer(fmasked):
+  317	        line_no = fmasked.count("\n", 0, m.start()) + 1
+  318	        yield line_no, m.group(2)
+  319	```
+  320	
+  321	- [ ] **Step 4: Implement the placeholder scan**
+  322	
+  323	Add below the masking helpers:
+  324	
+  325	```python
+  326	_PLACEHOLDER_TOKENS = [
+  327	    (re.compile(r"\bTBD\b", re.IGNORECASE), "TBD"),
+  328	    (re.compile(r"\bTODO\b", re.IGNORECASE), "TODO"),
+  329	    (re.compile(r"\bFIXME\b", re.IGNORECASE), "FIXME"),
+  330	    (re.compile(r"\bXXX\b", re.IGNORECASE), "XXX"),
+  331	    (re.compile(r"\?{3,}"), "???"),
+  332	    (re.compile(r"\blorem ipsum\b", re.IGNORECASE), "lorem ipsum"),
+  333	]
+  334	
+  335	
+  336	def _scan_placeholders(text: str, findings: list) -> None:
+  337	    masked = _mask_inline_code(_mask_fenced(text))
+  338	    for i, line in enumerate(masked.splitlines(), start=1):
+  339	        for rx, label in _PLACEHOLDER_TOKENS:
+  340	            if rx.search(line):
+  341	                findings.append(PreflightFinding(
+  342	                    "placeholder", "failure",
+  343	                    f"placeholder token {label!r} in prose", line=i))
+  344	```
+  345	
+  346	- [ ] **Step 5: Implement the referenced-path scans**
+  347	
+  348	Add below the placeholder scan:
+  349	
+  350	```python
+  351	_KNOWN_DIRS = ("docs", "skills", "tools", "hooks", "scripts", "tests", "src")
+  352	_GLOB_CHARS = set("<>*{}$…")
+  353	_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://|^mailto:")
+  354	_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
+  355	_LINE_SUFFIX_RE = re.compile(r":\d+(-\d+)?$")
+  356	
+  357	
+  358	def _looks_repo_relative(s: str) -> bool:
+  359	    if "/" not in s or _URL_RE.search(s):
+  360	        return False
+  361	    first = s.split("/", 1)[0]
+  362	    last = s.rsplit("/", 1)[-1]
+  363	    has_ext = "." in last and not last.endswith(".")
+  364	    return has_ext or first in _KNOWN_DIRS
+  365	
+  366	
+  367	def _exempt_path(s: str) -> bool:
+  368	    if any(c in _GLOB_CHARS for c in s):
+  369	        return True
+  370	    norm = s.lstrip("./")
+  371	    return norm == "docs/reviewer" or norm.startswith("docs/reviewer/")
+  372	
+  373	
+  374	def _path_exists(s: str, repo_root: Path) -> bool:
+  375	    p = Path(s)
+  376	    if not p.is_absolute():
+  377	        p = repo_root / s
+  378	    return p.exists()
+  379	
+  380	
+  381	def _scan_md_links(text: str, repo_root: Path, findings: list) -> None:
+  382	    fmasked = _mask_fenced(text)  # links survive; fenced content gone
+  383	    for m in _MD_LINK_RE.finditer(fmasked):
+  384	        target = m.group(1).split("#", 1)[0].strip()
+  385	        if not target or not _looks_repo_relative(target) or _exempt_path(target):
+  386	            continue
+  387	        if not _path_exists(target, repo_root):
+  388	            line_no = fmasked.count("\n", 0, m.start()) + 1
+  389	            findings.append(PreflightFinding(
+  390	                "dangling-link", "failure",
+  391	                f"markdown link target does not exist: {target}",
+  392	                line=line_no, path=target))
+  393	
+  394	
+  395	def _scan_backtick_paths(text: str, repo_root: Path, findings: list) -> None:
+  396	    for line_no, content in _inline_code_spans(text):
+  397	        s = content.strip()
+  398	        if not s or any(ch.isspace() for ch in s):
+  399	            continue  # paths have no spaces; skip commands/snippets
+  400	        if not _looks_repo_relative(s) or _exempt_path(s):
+  401	            continue
+  402	        candidate = _LINE_SUFFIX_RE.sub("", s)
+  403	        if not _path_exists(candidate, repo_root):
+  404	            findings.append(PreflightFinding(
+  405	                "dangling-path", "warning",
+  406	                f"backtick-quoted path does not exist: {s}",
+  407	                line=line_no, path=s))
+  408	```
+  409	
+  410	- [ ] **Step 6: Implement the section + context checks and the top-level function**
+  411	
+  412	Add below the path scans:
+  413	
+  414	```python
+  415	def _headings(text: str) -> list:
+  416	    fmasked = _mask_fenced(text)
+  417	    return [ln.lstrip("#").strip()
+  418	            for ln in fmasked.splitlines() if ln.lstrip().startswith("#")]
+  419	
+  420	
+  421	def _has_heading_kw(headings: list, *kws: str) -> bool:
+  422	    low = [h.lower() for h in headings]
+  423	    return any(any(k in h for k in kws) for h in low)
+  424	
+  425	
+  426	def _has_checkbox(text: str) -> bool:
+  427	    return re.search(r"(?m)^\s*[-*]\s*\[[ xX]\]", _mask_fenced(text)) is not None
+  428	
+  429	
+  430	def _check_sections(kind: str, text: str, findings: list) -> None:
+  431	    headings = _headings(text)
+  432	    if kind == "plan":
+  433	        if not (_has_heading_kw(headings, "task") or _has_checkbox(text)):
+  434	            findings.append(PreflightFinding(
+  435	                "missing-section", "failure",
+  436	                "plan has no task section (no 'task' heading or checkbox list)"))
+  437	        if not _has_heading_kw(headings, "verif", "accept", "gate"):
+  438	            findings.append(PreflightFinding(
+  439	                "missing-section", "failure",
+  440	                "plan has no verification/acceptance/gates section"))
+  441	    elif kind == "spec":
+  442	        if not _has_heading_kw(headings, "accept", "criteria"):
+  443	            findings.append(PreflightFinding(
+  444	                "missing-section", "failure",
+  445	                "spec has no acceptance-criteria section"))
+  446	    elif kind in ("post-slice", "post-phase"):
+  447	        if not _has_heading_kw(headings, "verif", "evidence", "accept"):
+  448	            findings.append(PreflightFinding(
+  449	                "missing-section", "failure",
+  450	                f"{kind} target has no evidence/verification section"))
+  451	
+  452	
+  453	def run_preflight_checks(kind: str, target: Path, context: list, repo_root: Path) -> PreflightResult:
+  454	    """Deterministic pre-review checks. No LLM calls, no chain I/O."""
+  455	    findings: list = []
+  456	    target = Path(target)
+  457	    try:
+  458	        raw = target.read_bytes()
+  459	    except (FileNotFoundError, IsADirectoryError):
+  460	        findings.append(PreflightFinding("target", "failure", f"target not found: {target}"))
+  461	        return PreflightResult(findings)
+  462	    if not raw.strip():
+  463	        findings.append(PreflightFinding("target", "failure", f"target is empty: {target}"))
+  464	        return PreflightResult(findings)
+  465	    try:
+  466	        text = raw.decode("utf-8")
+  467	    except UnicodeDecodeError:
+  468	        findings.append(PreflightFinding("target", "failure", f"target is not valid UTF-8: {target}"))
+  469	        return PreflightResult(findings)
+  470	
+  471	    _scan_placeholders(text, findings)
+  472	    _scan_md_links(text, repo_root, findings)
+  473	    _scan_backtick_paths(text, repo_root, findings)
+  474	    _check_sections(kind, text, findings)
+  475	
+  476	    for c in context:
+  477	        cp = Path(c)
+  478	        if not cp.is_absolute():
+  479	            cp = repo_root / cp
+  480	        if not cp.exists():
+  481	            findings.append(PreflightFinding(
+  482	                "context", "failure", f"context file not found: {c}", path=str(c)))
+  483	            continue
+  484	        size = cp.stat().st_size
+  485	        if size > 16 * 1024:
+  486	            findings.append(PreflightFinding(
+  487	                "context", "warning",
+  488	                f"context file is large ({size} bytes > 16KB): {c}; "
+  489	                f"prefer `tasktool brief` output", path=str(c)))
+  490	
+  491	    return PreflightResult(findings)
+  492	```
+  493	
+  494	- [ ] **Step 7: Run tests to verify they pass**
+  495	
+  496	Run: `python -m pytest skills/external-review/tests/test_preflight.py -q`
+  497	Expected: PASS (all).
+  498	
+  499	- [ ] **Step 8: Commit**
+  500	
+  501	```bash
+  502	git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_preflight.py
+  503	git commit -m "P9.S2: deterministic preflight check core (run_preflight_checks + helpers)"
+  504	```
+  505	
+  506	---
+  507	
+  508	### Task 2: `preflight` subcommand
+  509	
+  510	**Files:**
+  511	- Modify: `skills/external-review/scripts/external-reviewer.py` (subparser after `sp_stats` block ~line 1993-2001; `run_preflight` function — add near `run_stats` ~line 2403; dispatch in `main` after the `stats` dispatch ~line 2578)
+  512	- Test: `skills/external-review/tests/test_preflight_subcommand.py` (create)
+  513	
+  514	- [ ] **Step 1: Write the failing subprocess tests**
+  515	
+  516	Create `skills/external-review/tests/test_preflight_subcommand.py`:
+  517	
+  518	```python
+  519	from pathlib import Path
+  520	import json, subprocess, sys
+  521	
+  522	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
+  523	SCRIPT = SCRIPTS / "external-reviewer.py"
+  524	
+  525	
+  526	def _repo(tmp_path):
+  527	    # run_preflight() calls repo_root() (git rev-parse, check=True), so the
+  528	    # cwd must be a git repo — init one, matching the review subprocess harness.
+  529	    repo = tmp_path / "repo"
+  530	    (repo / "docs").mkdir(parents=True)
+  531	    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
+  532	    return repo
+  533	
+  534	
+  535	def _pf(repo, *args):
+  536	    return subprocess.run(
+  537	        [sys.executable, str(SCRIPT), "preflight", *args],
+  538	        cwd=repo, capture_output=True, text=True,
+  539	    )
+  540	
+  541	
+  542	def test_clean_doc_exit_0(tmp_path):
+  543	    repo = _repo(tmp_path)
+  544	    (repo / "doc.md").write_text(
+  545	        "# Spec\n\n## Acceptance criteria\n\n1. A grounded criterion.\n")
+  546	    r = _pf(repo, "--kind", "spec", "--file", "doc.md")
+  547	    assert r.returncode == 0, r.stderr + r.stdout
+  548	
+  549	
+  550	def test_failure_doc_exit_4(tmp_path):
+  551	    repo = _repo(tmp_path)
+  552	    (repo / "doc.md").write_text("# Spec\n\nNo criteria, and a TODO marker.\n")
+  553	    r = _pf(repo, "--kind", "spec", "--file", "doc.md")
+  554	    assert r.returncode == 4, r.stderr + r.stdout
+  555	
+  556	
+  557	def test_emit_json_shape(tmp_path):
+  558	    repo = _repo(tmp_path)
+  559	    (repo / "doc.md").write_text("# Spec\n\nNo criteria here. TODO.\n")
+  560	    r = _pf(repo, "--kind", "spec", "--file", "doc.md", "--emit", "json")
+  561	    assert r.returncode == 4
+  562	    payload = json.loads(r.stdout)
+  563	    assert payload["ok"] is False
+  564	    assert isinstance(payload["failures"], list) and payload["failures"]
+  565	    assert "warnings" in payload
+  566	    assert {"check", "severity", "message"} <= set(payload["failures"][0])
+  567	
+  568	
+  569	def test_warning_only_exit_0(tmp_path):
+  570	    repo = _repo(tmp_path)
+  571	    (repo / "doc.md").write_text(
+  572	        "# Spec\n\n## Acceptance criteria\n\nSee `skills/gone/x.py` (dangling, warns).\n")
+  573	    r = _pf(repo, "--kind", "spec", "--file", "doc.md", "--emit", "json")
+  574	    assert r.returncode == 0
+  575	    payload = json.loads(r.stdout)
+  576	    assert payload["ok"] is True
+  577	    assert payload["warnings"]
+  578	
+  579	
+  580	# --- AC2: each check class exercised THROUGH the standalone subcommand ---
+  581	def _checks(payload, severity):
+  582	    return {f["check"] for f in payload[severity]}
+  583	
+  584	
+  585	def test_subcommand_placeholder_failure(tmp_path):
+  586	    repo = _repo(tmp_path)
+  587	    (repo / "doc.md").write_text("# Spec\n\n## Acceptance criteria\n\nstill TODO here\n")
+  588	    r = _pf(repo, "--kind", "spec", "--file", "doc.md", "--emit", "json")
+  589	    assert r.returncode == 4
+  590	    assert "placeholder" in _checks(json.loads(r.stdout), "failures")
+  591	
+  592	
+  593	def test_subcommand_dangling_link_failure(tmp_path):
+  594	    repo = _repo(tmp_path)
+  595	    (repo / "doc.md").write_text(
+  596	        "# Spec\n\n## Acceptance criteria\n\nSee [x](docs/gone/missing.md).\n")
+  597	    r = _pf(repo, "--kind", "spec", "--file", "doc.md", "--emit", "json")
+  598	    assert r.returncode == 4
+  599	    assert "dangling-link" in _checks(json.loads(r.stdout), "failures")
+  600	
+
+[truncated: 500 additional lines]
+
+## Context Previews
+
+### docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md
+
+    1	# P9.S2 — Deterministic preflight gate + strengthened self-review checklists
+    2	
+    3	**Date:** 2026-06-09
+    4	**Status:** draft
+    5	**Tracker:** P9.S2 (slice of P9 — Review-pipeline efficiency)
+    6	**Parent spec:** `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md` (S2 section)
+    7	**Depends on:** P9.S1 (done)
+    8	
+    9	## Problem
+   10	
+   11	P9.S1 made each reviewer round cheaper (kind-aware depth defaults, model
+   12	tiering) and added a rounds-per-slice metric. It did not reduce *round count*.
+   13	The phase baseline (multistore, `external-reviewer stats`, 2026-06-06) shows
+   14	spec/plan/post-slice chains averaging ~2.3–2.7 rounds each, with revise rates of
+   15	34–47%. The phase design observes that many `revise` findings are mechanical —
+   16	placeholder text, dangling file references, missing acceptance/verification
+   17	sections, oversized tracker context — and are catchable locally for free before
+   18	the first paid reviewer round.
+   19	
+   20	Today nothing catches these locally. An author writes a spec or plan, invokes
+   21	`external-reviewer review`, and pays a full reviewer round to be told "this
+   22	references a file that does not exist" or "no verification section." That round
+   23	plus its fix cycle is pure avoidable cost.
+   24	
+   25	## Goal
+   26	
+   27	Catch mechanical revise-class findings deterministically (no LLM calls) before
+   28	the first paid reviewer round, and prime authors to self-check the
+   29	non-mechanical drivers. Concretely:
+   30	
+   31	- A `external-reviewer preflight` subcommand that runs deterministic checks and
+   32	  reports findings.
+   33	- `external-reviewer review` auto-runs those checks on round 1 and refuses on
+   34	  failure (escape hatch `--no-preflight`).
+   35	- `brainstorming` and `writing-plans` self-review checklists name the top
+   36	  historical revise drivers and instruct running preflight before external
+   37	  review.
+   38	
+   39	This is S2 of the phase. It does not change the verdict contract, chain layout,
+   40	provider invocation, or any S1 behaviour.
+   41	
+   42	## Non-goals / out of scope
+   43	
+   44	- No LLM calls in preflight — every check is deterministic and offline.
+   45	- No new review *kinds*, no verdict-contract or chain-folder changes.
+   46	- No combined spec+plan gate (that is S3; `--combined-gate`).
+   47	- No changes to S1 behaviour (depth defaults, model tiering, resolution gate,
+   48	  stats). S2 only adds the preflight surface and the checklist text.
+   49	- No consumer-repo (multistore) changes.
+   50	
+   51	## Design
+   52	
+   53	All CLI behaviour lives in
+   54	`skills/external-review/scripts/external-reviewer.py`. Documentation lives in
+   55	`skills/external-review/SKILL.md`, `skills/brainstorming/SKILL.md`, and
+   56	`skills/writing-plans/SKILL.md`. Tests live in
+   57	`skills/external-review/tests/`.
+   58	
+   59	### S2.a — `external-reviewer preflight` subcommand
+   60	
+   61	```
+   62	external-reviewer preflight --kind <kind> --file <target> [--context <path>]... [--emit json]
+   63	```
+   64	
+   65	`--kind` takes the same choices as `review`
+   66	(`spec|plan|design|implementation|post-slice|post-phase|other`). `--file` is the
+   67	target document; `--context` may repeat. `--emit` is `text` (default) or `json`.
+   68	
+   69	A single pure function does the work so the subcommand and the round-1
+   70	auto-gate share one implementation:
+   71	
+   72	```
+   73	run_preflight_checks(kind, target: Path, context: list[Path], repo_root: Path) -> PreflightResult
+   74	```
+   75	
+   76	`PreflightResult` carries an ordered list of findings, each a small record:
+   77	`check` (which check produced it), `severity` (`failure` | `warning`),
+   78	`message`, and optional `line` / `path`. Two helpers expose the rollup:
+   79	`PreflightResult.failures` and `.warnings`. The function performs **no I/O on
+   80	the chain folder and no LLM calls** — it only reads the target and context
+   81	files from disk.
+   82	
+   83	The deterministic checks:
+   84	
+   85	**1. Target readable.** The target exists, is non-empty after stripping
+   86	whitespace, and decodes as UTF-8. Any failure here is a `failure` and short-
+   87	circuits the remaining content checks (a binary or empty target cannot be
+   88	meaningfully scanned).
+   89	
+   90	**2. Placeholder scan.** The whole-token placeholders `TBD`, `TODO`, `FIXME`,
+   91	`XXX`, `???`, and `lorem ipsum` (case-insensitive) anywhere in the target's
+   92	prose are `failure`s, reported with line numbers. **Exemption:** text inside
+   93	fenced code blocks *and* inline code spans (single/double backtick) is masked
+   94	before the scan. The phase design exempts fenced blocks; this slice also
+   95	exempts inline code spans because specs and plans legitimately name these
+   96	tokens in backticks when describing tooling (this very document does), and an
+   97	inline-code mention is not an unfinished-work marker. Masking replaces exempt
+   98	regions with same-length spaces so reported line/column positions stay
+   99	accurate. Whole-token matching uses boundaries appropriate to each token
+  100	(word-boundary for the alphanumeric tokens; literal match for `???`).
+  101	
+  102	**3. Referenced-path check.** Two syntaxes are scanned outside masked code
+  103	regions:
+  104	
+  105	- **Markdown links** — `[text](path)`. A path that looks repo-relative but does
+  106	  not exist on disk is a `failure`.
+  107	- **Backtick-quoted strings** — an inline-code span whose content looks like a
+  108	  repo-relative path but does not exist is a `warning` (prose cites paths
+  109	  illustratively; a dangling backtick path is worth flagging but not blocking).
+  110	
+  111	"Looks repo-relative" heuristic: the string contains `/` **and** either has a
+  112	file extension (a `.` in the final segment) or its first segment is a known
+  113	project directory (`docs`, `skills`, `tools`, `hooks`, `scripts`, `tests`,
+  114	`src`). Exemptions (skipped entirely, no finding):
+  115	
+  116	- Anything inside a fenced code block (illustrative command/code).
+  117	- Paths containing placeholder/glob characters: `<`, `>`, `*`, `{`, `}`, `$`,
+  118	  `…` (e.g. `docs/specs/YYYY-MM-DD-<id>-slug.md`).
+  119	- Paths whose first segment is `docs/reviewer` (future/generated reviewer
+  120	  artifacts that legitimately do not exist yet).
+  121	- URLs (a scheme like `http://`, `https://`, `mailto:`).
+  122	
+  123	Paths are resolved relative to `repo_root`. Absolute paths are resolved as-is.
+  124	Note the asymmetry: the markdown-link scan runs on text with **fenced blocks
+  125	masked but inline code visible** (so `[x](path)` links are seen); the backtick
+  126	scan reads inline-code spans directly. Fenced content is exempt for both.
+  127	
+  128	**4. Kind-required sections.** Heading detection is keyword-based and tolerant
+  129	of phrasing — a heading line (`#`-prefixed) whose text matches the keyword
+  130	(case-insensitive substring) counts.
+  131	
+  132	- `plan` → requires **both** a task section (a heading matching `task`, or the
+  133	  presence of any GitHub-style checkbox line `- [ ]` / `- [x]`) **and** a
+  134	  verification/acceptance section (heading matching `verif`, `accept`, or
+  135	  `gate`). A missing either is a `failure`.
+  136	- `spec` → requires an acceptance-criteria section (heading matching `accept`
+  137	  or `criteria`). Missing is a `failure`.
+  138	- `post-slice` / `post-phase` → require an evidence/verification section
+  139	  (heading matching `verif`, `evidence`, or `accept`) in the target. Missing is
+  140	  a `failure`.
+  141	- `design` / `implementation` / `other` → no required-section check (these
+  142	  kinds have no fixed shape).
+  143	
+  144	**5. Context hygiene.** In the **standalone `preflight` subcommand**, a missing
+  145	`--file` target or a missing `--context` path is a `failure` surfaced in the
+  146	findings list (the subcommand has no other validation layer, so it must report
+  147	missing files itself). In the **`review` auto-preflight path** this case never
+  148	arises: `review` already hard-fails a missing target or context with **exit 2
+  149	before** chain discovery or the preflight gate (current
+  150	`external-reviewer.py` behaviour, preserved unchanged — so `--no-preflight`
+  151	stays byte-identical to today). Any existing context file larger than 16 KB
+  152	produces a `warning` naming the file and its size, hinting to pass
+  153	`tasktool brief <work-id>` output instead (this catches the
+  154	full-`docs/tasklist.json` habit S1.b discouraged in prose). The 16 KB warning
+  155	applies in both the subcommand and the auto-preflight path.
+  156	
+  157	**Output and exit codes.** Text mode prints a grouped findings list
+  158	(failures first, then warnings) with a one-line summary; a clean run prints a
+  159	short "preflight passed" line. `--emit json` prints
+  160	`{"ok": <bool>, "failures": [...], "warnings": [...]}` where each entry is the
+  161	finding record. **Exit 0** = no failures (warnings allowed); **exit 4** =
+  162	one or more failures. Exit 4 is the phase-design-assigned preflight failure
+  163	code, deliberately distinct from the exit-3 resolution gate.
+  164	
+  165	Exit 4 is also returned by `review` for a schema-too-new manifest. The two are
+  166	sequential, never simultaneous: in `review`, the manifest is read (and a
+  167	schema-too-new manifest aborts with exit 4) **before** the round number is
+  168	known, and the round-1 auto-preflight (S2.b) needs the round number, so it runs
+  169	strictly after the manifest read. A schema-too-new manifest therefore aborts
+  170	before preflight ever runs — preflight cannot mask it. The shared code is
+  171	accepted: both causes mean "input not reviewable, fix it," and introducing a
+  172	new code for preflight would diverge from the phase design's exit-4 assignment.
+  173	
+  174	### S2.b — Auto-preflight on round 1
+  175	
+  176	`review` runs `run_preflight_checks` in-process **before submitting a round-1
+  177	review** and refuses on failure, printing the same findings list and returning
+  178	exit 4. The gate fires only when `round_num == 1` (the broad first round).
+  179	Incremental rounds (N+1) skip it — the diff/resolution machinery already covers
+  180	them, and re-scanning an already-reviewed document for dangling paths adds
+  181	friction without catching revise drivers.
+  182	
+  183	A new `--no-preflight` flag on the `review` subparser skips the auto-gate
+  184	entirely (escape hatch for an author who has deliberately accepted a finding, or
+  185	for non-standard documents). When skipped, behaviour is byte-identical to today.
+  186	
+  187	The exact sequence inside `review` is: (1) resolve `--file` and `--context`
+  188	paths, **including the existing existence validation that returns exit 2 for a
+  189	missing target or context file** before any manifest or preflight work (this
+  190	check is preserved unchanged, so a missing file is never deferred into a
+  191	preflight exit-4 finding in the `review` path); (2) discover/read the chain
+  192	manifest — a schema-too-new manifest aborts here with exit 4; (3) apply the
+  193	resolution-required gate (round 2+ only);
+  194	(4) determine the round number from the chain; (5) **if `round_num == 1` and not
+  195	`--no-preflight`, run `run_preflight_checks` and return exit 4 on any failure**;
+  196	(6) only then construct the prompt and spawn the reviewer. The gate runs after
+  197	the round number is known but before any reviewer process is spawned, so a
+  198	failing preflight costs nothing in reviewer time. Warnings do not block — they
+  199	print to stderr and the review proceeds.
+  200	
+
+[truncated: 98 additional lines]
+### /tmp/p9s2-brief.md
+
+    1	# P9.S2 — Deterministic preflight gate + strengthened self-review checklists [step: implement]
+    2	status: ready
+    3	workflow_step: implement
+    4	plan: docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md
+    5	depends_on:
+    6	  - P9.S1
+    7	planning_status: proposed
+    8	reviewer_chain: docs/reviewer/p9-s2-preflight-gate-self-review-plan
+    9	
+   10	Parent phase: P9 — Review-pipeline efficiency: fewer rounds, cheaper rounds [ready]
+   11	
+   12	Sibling slices:
+   13	  S1  [done]  Quick wins: kind-aware depth defaults, context trimming, resolution gate for all kinds, model tiering, stats --since + per-slice metric
+   14	  S2  [ready]  Deterministic preflight gate + strengthened self-review checklists
+   15	  S3  [ready]  Combined spec+plan gate for small slices
+   16	
+   17	Open tasks:
+
+<!-- superstar-prompt:end -->
\ No newline at end of file
diff --git a/docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/r1-2026-06-09T0456-primary-response.md b/docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/r1-2026-06-09T0456-primary-response.md
new file mode 100644
index 0000000..989082c
--- /dev/null
+++ b/docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/r1-2026-06-09T0456-primary-response.md
@@ -0,0 +1,48 @@
+# Review — 2026-06-09-P9.S2-preflight-gate-self-review.md (post-slice, round 1)
+
+- Target: `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md`
+- Request: `docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/r1-2026-06-09T0456-primary-request.md`
+- Reviewer command: `reviewer-agent`
+- Reviewer provider: `codex`
+- Sandbox: repo read-only; scratch/output writable
+- Status: `ok`
+
+---
+
+1. Findings
+
+F1 — Severity: blocking — The tracker state does not support slice completion. The plan requires `tasktool start P9.S2` and expects the slice to show started/in progress at lines 41-44, but the live tracker still has `started: null` and `status: "ready"` in `docs/tasklist.json` lines 390-392. `/tmp/p9s2-brief.md` also reports `status: ready` / `workflow_step: implement` at lines 1-4. This means the required Task 0 lifecycle step was not completed, and the slice cannot be treated as fully executed.
+
+F2 — Severity: important — The target plan is still an unchecked implementation plan, not a completed evidence record. It explicitly says checkbox syntax is for task tracking at line 3, but the required steps remain unchecked, including Task 0 at lines 41 and 46, Task 5 verification at lines 1020, 1074, and 1078, and merge/close hygiene at line 1082. The repo has four P9.S2 implementation commits and tests pass, so the code work appears real, but the document itself does not record which gates were actually run or completed.
+
+2. Open questions / assumptions
+
+I assume this post-slice review is intended to gate implementation completion before merge/close, so I am not treating Task 5 Step 7 merge-back/close/version-bump work as required before this review. If the team’s intended gate is “ready to close,” then Step 7 is also incomplete.
+
+3. Suggested document edits
+
+Update the tracker lifecycle first, or document why the slice was intentionally implemented without `tasktool start`. Then update the plan or a linked evidence note so Task 5 contains actual verification results rather than only planned commands.
+
+Also fix the two preflight warnings in the plan: `tests/test_resolution_gate.py` is quoted at lines 32 and 745, but from repo root the existing path is `skills/external-review/tests/test_resolution_gate.py`.
+
+4. Verification gaps / commands that should be run
+
+I ran these checks during review:
+
+- `python -m pytest skills/external-review/tests/test_preflight.py skills/external-review/tests/test_preflight_subcommand.py skills/external-review/tests/test_auto_preflight.py -q` → 39 passed.
+- `python -m pytest skills/external-review/tests -q` → 336 passed.
+- `tasktool artifact status P9.S2 --strict` → ok.
+- `tasktool validate` → only pre-existing X29 missing-path warnings.
+- `git status --short` → only the current post-slice reviewer chain is untracked.
+
+Before resubmission, run `tasktool show P9.S2` and confirm it no longer reports `status: ready` with `started: null`.
+
+Overall verdict: revise
+
+---
+
+## Reviewer stderr (tail)
+
+```text
+2026-06-09T03:56:16.725546Z ERROR codex_core_skills::loader: failed to stat skills path /home/simon/.codex/.tmp/plugins/plugins/life-science-research/skills/clinvar-variation-skill/SKILL.md: No such file or directory (os error 2)
+```
diff --git a/docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/r1-2026-06-09T0456-sweep1-request.md b/docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/r1-2026-06-09T0456-sweep1-request.md
new file mode 100644
index 0000000..12506bf
--- /dev/null
+++ b/docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice/r1-2026-06-09T0456-sweep1-request.md
@@ -0,0 +1,887 @@
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
+/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p9-s2-deterministic-preflight-gate
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
+docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md
+
+Additional context files:
+- docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md
+- /tmp/p9s2-brief.md
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
+### docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md
+
+    1	# P9.S2 — Deterministic Preflight Gate + Strengthened Self-Review Checklists Implementation Plan
+    2	
+    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
+    4	
+    5	**Goal:** Add an `external-reviewer preflight` subcommand and a round-1 auto-gate that catch mechanical revise-class findings (placeholders, dangling paths, missing sections, oversized context) deterministically before any paid reviewer round, plus self-review checklists in the planning skills.
+    6	
+    7	**Architecture:** One pure function `run_preflight_checks(kind, target, context, repo_root) -> PreflightResult` in `skills/external-review/scripts/external-reviewer.py` does all deterministic checks (no LLM, no chain I/O). A `preflight` subcommand and the `review` round-1 path both call it. Skill-text changes document the surface and add author checklists.
+    8	
+    9	**Tech Stack:** Python 3 (stdlib only), pytest (`skills/external-review/tests/`), markdown skill files.
+   10	
+   11	**Spec:** `docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md`.
+   12	
+   13	**Scheduling:** `P9.S2` depends on `P9.S1` (done) and gates `P9.S3` (`tasktool schedule P9` confirms `deps=P9.S1`, `waiting_on=-`, ready). No `parallel_group`. Declared integration surfaces (same as S1, serialized behind it): `skills/external-review/scripts/external-reviewer.py`, `skills/external-review/SKILL.md`, `skills/brainstorming/SKILL.md`, `skills/writing-plans/SKILL.md`. S3 is serialized behind S2 via `depends_on`, so no sibling runs in parallel — no reservations needed. The plan does not change the dependency graph; Task 0 ratifies the slice as planned.
+   14	
+   15	---
+   16	
+   17	## Conventions used by every task
+   18	
+   19	- Repo root: `/home/simon/Dev/sigreer/skills/superstar` (work from an isolated worktree created via `superstar:using-git-worktrees`).
+   20	- Line numbers below are anchors as of commit `2d1b9b6`; re-locate with the given grep if drifted.
+   21	- The module is loaded in unit tests the way every existing test does it:
+   22	
+   23	```python
+   24	from pathlib import Path
+   25	import sys, importlib.util
+   26	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
+   27	sys.path.insert(0, str(SCRIPTS))
+   28	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
+   29	er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
+   30	```
+   31	
+   32	- Subprocess tests reuse the `_init_repo`/`_run` harness pattern from `tests/test_resolution_gate.py` (a throwaway git repo with a `stub.sh` reviewer on `AGENT_REVIEWER_CMD`).
+   33	- Test command: `python -m pytest skills/external-review/tests/<file> -q` from the repo root.
+   34	
+   35	---
+   36	
+   37	### Task 0: Start the slice and ratify scheduling
+   38	
+   39	**Files:** none (tracker only).
+   40	
+   41	- [ ] **Step 1: Mark the slice started**
+   42	
+   43	Run: `tasktool start P9.S2`
+   44	Expected: exit 0; `tasktool show P9.S2` shows status `in_progress` / started.
+   45	
+   46	- [ ] **Step 2: Ratify the scheduling contract**
+   47	
+   48	The plan confirms the existing graph (`deps=P9.S1`, no parallel group). Run:
+   49	
+   50	```bash
+   51	tasktool ratify P9.S2
+   52	```
+   53	
+   54	Expected: exit 0. `tasktool ready-slices P9` continues to list `P9.S2` (and not `P9.S3`, which waits on S2).
+   55	
+   56	---
+   57	
+   58	### Task 1: Preflight check core (`run_preflight_checks` + helpers)
+   59	
+   60	The pure function and its helpers. No argparse, no chain I/O, no LLM. Built incrementally with unit tests in one new file.
+   61	
+   62	**Files:**
+   63	- Modify: `skills/external-review/scripts/external-reviewer.py` (add the dataclasses + helpers + `run_preflight_checks` near the other module-level helpers — place after `apply_budget`/the `_BUDGET_SECTIONS` block region, i.e. anywhere above `def parse_args`, e.g. after line ~640; the functions are self-contained)
+   64	- Test: `skills/external-review/tests/test_preflight.py` (create)
+   65	
+   66	- [ ] **Step 1: Write the failing unit tests**
+   67	
+   68	Create `skills/external-review/tests/test_preflight.py`:
+   69	
+   70	```python
+   71	from pathlib import Path
+   72	import sys, importlib.util
+   73	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
+   74	sys.path.insert(0, str(SCRIPTS))
+   75	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
+   76	er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
+   77	
+   78	
+   79	def _run(kind, body, *, context=None, repo=None, tmp_path=None):
+   80	    repo = repo or tmp_path
+   81	    target = repo / "doc.md"
+   82	    target.write_text(body, encoding="utf-8")
+   83	    return er.run_preflight_checks(kind, target, [Path(c) for c in (context or [])], repo)
+   84	
+   85	
+   86	def _msgs(result, severity):
+   87	    bucket = result.failures if severity == "failure" else result.warnings
+   88	    return " || ".join(f.message for f in bucket)
+   89	
+   90	
+   91	# --- target readable ---
+   92	def test_missing_target_is_failure(tmp_path):
+   93	    res = er.run_preflight_checks("spec", tmp_path / "nope.md", [], tmp_path)
+   94	    assert not res.ok
+   95	    assert any(f.check == "target" for f in res.failures)
+   96	
+   97	
+   98	def test_empty_target_is_failure(tmp_path):
+   99	    res = _run("spec", "   \n\n", tmp_path=tmp_path)
+  100	    assert any(f.check == "target" for f in res.failures)
+  101	
+  102	
+  103	# --- placeholders ---
+  104	def test_placeholder_in_prose_fails(tmp_path):
+  105	    res = _run("spec", "# Spec\n\n## Acceptance criteria\n\nThis is TODO still.\n", tmp_path=tmp_path)
+  106	    assert any(f.check == "placeholder" for f in res.failures)
+  107	
+  108	
+  109	def test_placeholder_in_fenced_block_exempt(tmp_path):
+  110	    body = "# Spec\n\n## Acceptance criteria\n\n```\nTODO leftover\n```\n"
+  111	    res = _run("spec", body, tmp_path=tmp_path)
+  112	    assert not any(f.check == "placeholder" for f in res.failures)
+  113	
+  114	
+  115	def test_placeholder_in_inline_code_exempt(tmp_path):
+  116	    body = "# Spec\n\n## Acceptance criteria\n\nThe scanner flags `TODO` tokens.\n"
+  117	    res = _run("spec", body, tmp_path=tmp_path)
+  118	    assert not any(f.check == "placeholder" for f in res.failures)
+  119	
+  120	
+  121	def test_triple_question_mark_placeholder(tmp_path):
+  122	    res = _run("spec", "# S\n\n## Acceptance criteria\n\nvalue is ??? here\n", tmp_path=tmp_path)
+  123	    assert any(f.check == "placeholder" for f in res.failures)
+  124	
+  125	
+  126	# --- paths ---
+  127	def test_dangling_markdown_link_fails(tmp_path):
+  128	    body = "# S\n\n## Acceptance criteria\n\nSee [the file](docs/nope/missing.md).\n"
+  129	    res = _run("spec", body, tmp_path=tmp_path)
+  130	    assert any(f.check == "dangling-link" for f in res.failures)
+  131	
+  132	
+  133	def test_existing_markdown_link_ok(tmp_path):
+  134	    (tmp_path / "docs").mkdir()
+  135	    (tmp_path / "docs" / "real.md").write_text("x")
+  136	    body = "# S\n\n## Acceptance criteria\n\nSee [the file](docs/real.md).\n"
+  137	    res = _run("spec", body, tmp_path=tmp_path)
+  138	    assert not any(f.check == "dangling-link" for f in res.failures)
+  139	
+  140	
+  141	def test_dangling_backtick_path_warns(tmp_path):
+  142	    body = "# S\n\n## Acceptance criteria\n\nLook at `skills/gone/x.py` for details.\n"
+  143	    res = _run("spec", body, tmp_path=tmp_path)
+  144	    assert any(f.check == "dangling-path" for f in res.warnings)
+  145	    assert not any(f.check == "dangling-path" for f in res.failures)
+  146	
+  147	
+  148	def test_fenced_path_exempt(tmp_path):
+  149	    body = "# S\n\n## Acceptance criteria\n\n```\ncat skills/gone/x.py\n```\n"
+  150	    res = _run("spec", body, tmp_path=tmp_path)
+  151	    assert not any(f.check in ("dangling-path", "dangling-link") for f in res.failures + res.warnings)
+  152	
+  153	
+  154	def test_glob_and_placeholder_paths_exempt(tmp_path):
+  155	    body = "# S\n\n## Acceptance criteria\n\nName is `docs/specs/YYYY-MM-DD-<id>-slug.md` here.\n"
+  156	    res = _run("spec", body, tmp_path=tmp_path)
+  157	    assert not any(f.path for f in res.failures + res.warnings)
+  158	
+  159	
+  160	def test_docs_reviewer_path_exempt(tmp_path):
+  161	    body = "# S\n\n## Acceptance criteria\n\nChain at `docs/reviewer/foo-spec/chain.json`.\n"
+  162	    res = _run("spec", body, tmp_path=tmp_path)
+  163	    assert not any(f.check == "dangling-path" for f in res.warnings)
+  164	
+  165	
+  166	def test_url_not_treated_as_path(tmp_path):
+  167	    body = "# S\n\n## Acceptance criteria\n\nSee [home](https://example.com/page).\n"
+  168	    res = _run("spec", body, tmp_path=tmp_path)
+  169	    assert not any(f.check == "dangling-link" for f in res.failures)
+  170	
+  171	
+  172	def test_path_with_line_suffix_resolves(tmp_path):
+  173	    (tmp_path / "src").mkdir()
+  174	    (tmp_path / "src" / "a.py").write_text("x\n")
+  175	    body = "# S\n\n## Acceptance criteria\n\nFix `src/a.py:12` now.\n"
+  176	    res = _run("spec", body, tmp_path=tmp_path)
+  177	    assert not any(f.check == "dangling-path" for f in res.warnings)
+  178	
+  179	
+  180	# --- sections ---
+  181	def test_spec_missing_acceptance_section_fails(tmp_path):
+  182	    res = _run("spec", "# Spec\n\nProse only, no criteria heading.\n", tmp_path=tmp_path)
+  183	    assert any(f.check == "missing-section" for f in res.failures)
+  184	
+  185	
+  186	def test_plan_needs_task_and_verification(tmp_path):
+  187	    only_tasks = "# Plan\n\n### Task 1\n\n- [ ] do it\n"
+  188	    res = _run("plan", only_tasks, tmp_path=tmp_path)
+  189	    assert any("verif" in f.message or "verification" in f.message for f in res.failures)
+  190	
+  191	
+  192	def test_plan_with_checkbox_and_verification_ok(tmp_path):
+  193	    body = "# Plan\n\n### Task 1\n\n- [ ] do it\n\n## Verification\n\nrun pytest\n"
+  194	    res = _run("plan", body, tmp_path=tmp_path)
+  195	    assert not any(f.check == "missing-section" for f in res.failures)
+  196	
+  197	
+  198	def test_post_slice_needs_evidence_section(tmp_path):
+  199	    res = _run("post-slice", "# Slice\n\n### Task 1\n\nno evidence heading\n", tmp_path=tmp_path)
+  200	    assert any(f.check == "missing-section" for f in res.failures)
+  201	
+  202	
+  203	def test_design_kind_no_section_requirement(tmp_path):
+  204	    res = _run("design", "# Design\n\nfree-form, no fixed shape.\n", tmp_path=tmp_path)
+  205	    assert not any(f.check == "missing-section" for f in res.failures)
+  206	
+  207	
+  208	# --- context hygiene ---
+  209	def test_missing_context_file_fails(tmp_path):
+  210	    body = "# S\n\n## Acceptance criteria\n\nok\n"
+  211	    res = _run("spec", body, context=[tmp_path / "missing-ctx.md"], tmp_path=tmp_path)
+  212	    assert any(f.check == "context" for f in res.failures)
+  213	
+  214	
+  215	def test_oversized_context_warns(tmp_path):
+  216	    big = tmp_path / "big.json"
+  217	    big.write_text("x" * (17 * 1024))
+  218	    body = "# S\n\n## Acceptance criteria\n\nok\n"
+  219	    res = _run("spec", body, context=[big], tmp_path=tmp_path)
+  220	    assert any(f.check == "context" for f in res.warnings)
+  221	
+  222	
+  223	def test_clean_document_passes(tmp_path):
+  224	    (tmp_path / "docs").mkdir()
+  225	    (tmp_path / "docs" / "real.md").write_text("x")
+  226	    body = (
+  227	        "# Spec\n\n## Acceptance criteria\n\n"
+  228	        "1. A real criterion referencing [a file](docs/real.md).\n"
+  229	        "2. Another grounded statement.\n"
+  230	    )
+  231	    res = _run("spec", body, tmp_path=tmp_path)
+  232	    assert res.ok
+  233	    assert res.failures == []
+  234	```
+  235	
+  236	- [ ] **Step 2: Run tests to verify they fail**
+  237	
+  238	Run: `python -m pytest skills/external-review/tests/test_preflight.py -q`
+  239	Expected: FAIL — `AttributeError: module ... has no attribute 'run_preflight_checks'`.
+  240	
+  241	- [ ] **Step 3: Implement the dataclasses and code-masking helpers**
+  242	
+  243	In `external-reviewer.py`, add this block above `def parse_args` (the `dataclass` import already exists at line 37; `re`/`Path` are imported):
+  244	
+  245	```python
+  246	# --- P9.S2 deterministic preflight ----------------------------------------
+  247	
[truncated: 864 additional lines]


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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p9-s2-deterministic-preflight-gate

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md

Additional context files:
- docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md
- /tmp/p9s2-brief.md

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

### docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md

    1	# P9.S2 — Deterministic Preflight Gate + Strengthened Self-Review Checklists Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Add an `external-reviewer preflight` subcommand and a round-1 auto-gate that catch mechanical revise-class findings (placeholders, dangling paths, missing sections, oversized context) deterministically before any paid reviewer round, plus self-review checklists in the planning skills.
    6	
    7	**Architecture:** One pure function `run_preflight_checks(kind, target, context, repo_root) -> PreflightResult` in `skills/external-review/scripts/external-reviewer.py` does all deterministic checks (no LLM, no chain I/O). A `preflight` subcommand and the `review` round-1 path both call it. Skill-text changes document the surface and add author checklists.
    8	
    9	**Tech Stack:** Python 3 (stdlib only), pytest (`skills/external-review/tests/`), markdown skill files.
   10	
   11	**Spec:** `docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md`.
   12	
   13	**Scheduling:** `P9.S2` depends on `P9.S1` (done) and gates `P9.S3` (`tasktool schedule P9` confirms `deps=P9.S1`, `waiting_on=-`, ready). No `parallel_group`. Declared integration surfaces (same as S1, serialized behind it): `skills/external-review/scripts/external-reviewer.py`, `skills/external-review/SKILL.md`, `skills/brainstorming/SKILL.md`, `skills/writing-plans/SKILL.md`. S3 is serialized behind S2 via `depends_on`, so no sibling runs in parallel — no reservations needed. The plan does not change the dependency graph; Task 0 ratifies the slice as planned.
   14	
   15	---
   16	
   17	## Conventions used by every task
   18	
   19	- Repo root: `/home/simon/Dev/sigreer/skills/superstar` (work from an isolated worktree created via `superstar:using-git-worktrees`).
   20	- Line numbers below are anchors as of commit `2d1b9b6`; re-locate with the given grep if drifted.
   21	- The module is loaded in unit tests the way every existing test does it:
   22	
   23	```python
   24	from pathlib import Path
   25	import sys, importlib.util
   26	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
   27	sys.path.insert(0, str(SCRIPTS))
   28	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
   29	er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
   30	```
   31	
   32	- Subprocess tests reuse the `_init_repo`/`_run` harness pattern from `skills/external-review/tests/test_resolution_gate.py` (a throwaway git repo with a `stub.sh` reviewer on `AGENT_REVIEWER_CMD`).
   33	- Test command: `python -m pytest skills/external-review/tests/<file> -q` from the repo root.
   34	
   35	---
   36	
   37	### Task 0: Start the slice and ratify scheduling
   38	
   39	**Files:** none (tracker only).
   40	
   41	- [x] **Step 1: Mark the slice started**
   42	
   43	Run: `tasktool start P9.S2`
   44	Expected: exit 0; `tasktool show P9.S2` shows status `in_progress` / started.
   45	
   46	- [x] **Step 2: Ratify the scheduling contract**
   47	
   48	The plan confirms the existing graph (`deps=P9.S1`, no parallel group). Run:
   49	
   50	```bash
   51	tasktool ratify P9.S2
   52	```
   53	
   54	Expected: exit 0. `tasktool ready-slices P9` continues to list `P9.S2` (and not `P9.S3`, which waits on S2).
   55	
   56	---
   57	
   58	### Task 1: Preflight check core (`run_preflight_checks` + helpers)
   59	
   60	The pure function and its helpers. No argparse, no chain I/O, no LLM. Built incrementally with unit tests in one new file.
   61	
   62	**Files:**
   63	- Modify: `skills/external-review/scripts/external-reviewer.py` (add the dataclasses + helpers + `run_preflight_checks` near the other module-level helpers — place after `apply_budget`/the `_BUDGET_SECTIONS` block region, i.e. anywhere above `def parse_args`, e.g. after line ~640; the functions are self-contained)
   64	- Test: `skills/external-review/tests/test_preflight.py` (create)
   65	
   66	- [x] **Step 1: Write the failing unit tests**
   67	
   68	Create `skills/external-review/tests/test_preflight.py`:
   69	
   70	```python
   71	from pathlib import Path
   72	import sys, importlib.util
   73	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
   74	sys.path.insert(0, str(SCRIPTS))
   75	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
   76	er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
   77	
   78	
   79	def _run(kind, body, *, context=None, repo=None, tmp_path=None):
   80	    repo = repo or tmp_path
   81	    target = repo / "doc.md"
   82	    target.write_text(body, encoding="utf-8")
   83	    return er.run_preflight_checks(kind, target, [Path(c) for c in (context or [])], repo)
   84	
   85	
   86	def _msgs(result, severity):
   87	    bucket = result.failures if severity == "failure" else result.warnings
   88	    return " || ".join(f.message for f in bucket)
   89	
   90	
   91	# --- target readable ---
   92	def test_missing_target_is_failure(tmp_path):
   93	    res = er.run_preflight_checks("spec", tmp_path / "nope.md", [], tmp_path)
   94	    assert not res.ok
   95	    assert any(f.check == "target" for f in res.failures)
   96	
   97	
   98	def test_empty_target_is_failure(tmp_path):
   99	    res = _run("spec", "   \n\n", tmp_path=tmp_path)
  100	    assert any(f.check == "target" for f in res.failures)
  101	
  102	
  103	# --- placeholders ---
  104	def test_placeholder_in_prose_fails(tmp_path):
  105	    res = _run("spec", "# Spec\n\n## Acceptance criteria\n\nThis is TODO still.\n", tmp_path=tmp_path)
  106	    assert any(f.check == "placeholder" for f in res.failures)
  107	
  108	
  109	def test_placeholder_in_fenced_block_exempt(tmp_path):
  110	    body = "# Spec\n\n## Acceptance criteria\n\n```\nTODO leftover\n```\n"
  111	    res = _run("spec", body, tmp_path=tmp_path)
  112	    assert not any(f.check == "placeholder" for f in res.failures)
  113	
  114	
  115	def test_placeholder_in_inline_code_exempt(tmp_path):
  116	    body = "# Spec\n\n## Acceptance criteria\n\nThe scanner flags `TODO` tokens.\n"
  117	    res = _run("spec", body, tmp_path=tmp_path)
  118	    assert not any(f.check == "placeholder" for f in res.failures)
  119	
  120	
  121	def test_triple_question_mark_placeholder(tmp_path):
  122	    res = _run("spec", "# S\n\n## Acceptance criteria\n\nvalue is ??? here\n", tmp_path=tmp_path)
  123	    assert any(f.check == "placeholder" for f in res.failures)
  124	
  125	
  126	# --- paths ---
  127	def test_dangling_markdown_link_fails(tmp_path):
  128	    body = "# S\n\n## Acceptance criteria\n\nSee [the file](docs/nope/missing.md).\n"
  129	    res = _run("spec", body, tmp_path=tmp_path)
  130	    assert any(f.check == "dangling-link" for f in res.failures)
  131	
  132	
  133	def test_existing_markdown_link_ok(tmp_path):
  134	    (tmp_path / "docs").mkdir()
  135	    (tmp_path / "docs" / "real.md").write_text("x")
  136	    body = "# S\n\n## Acceptance criteria\n\nSee [the file](docs/real.md).\n"
  137	    res = _run("spec", body, tmp_path=tmp_path)
  138	    assert not any(f.check == "dangling-link" for f in res.failures)
  139	
  140	
  141	def test_dangling_backtick_path_warns(tmp_path):
  142	    body = "# S\n\n## Acceptance criteria\n\nLook at `skills/gone/x.py` for details.\n"
  143	    res = _run("spec", body, tmp_path=tmp_path)
  144	    assert any(f.check == "dangling-path" for f in res.warnings)
  145	    assert not any(f.check == "dangling-path" for f in res.failures)
  146	
  147	
  148	def test_fenced_path_exempt(tmp_path):
  149	    body = "# S\n\n## Acceptance criteria\n\n```\ncat skills/gone/x.py\n```\n"
  150	    res = _run("spec", body, tmp_path=tmp_path)

[truncated: 1002 additional lines]

<!-- superstar-prompt:end -->