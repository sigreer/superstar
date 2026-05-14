<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 2 of external-reviewer-context-optimisation-plan-S2-post-slice.

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

# Review — 2026-05-14-external-reviewer-context-optimisation-plan.md (post-slice, round 1)

- Target: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md`
- Request: `docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice/r1-2026-05-14T1628-primary-request.md`
- Reviewer command: `reviewer-agent`
- Status: `ok`

---

1. Findings

F1. Severity: minor - Slice 2 manual evidence is checked but not recorded.  
[docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:2638) lists the synthetic large-chain check and expected `<200 KB` result, but does not capture the observed request size. I reran the check and got `84,854` bytes, so this is evidence hygiene, not a correctness blocker.

F2. Severity: minor - Worktree has an untracked review artifact directory.  
`git status --short` reports `?? docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice/`. This appears to be the current review chain artifact, but it should be committed, ignored, or otherwise intentionally handled before final closeout.

2. Open questions / assumptions

- Assumption: this post-slice gate is for Slice 2, based on the checked Slice 2 tasks and the `S2-post-slice` review artifact path.
- No implementation-blocking questions.

3. Suggested document edits

- Under Task 2.6 Step 2, add the observed manual-check output, e.g. `Observed: r2 request was 84,854 bytes`.
- After this review completes, record or land the `docs/reviewer/...S2-post-slice/` artifacts according to the repo’s review-chain convention.

4. Verification gaps / commands run

Commands I ran:

```bash
python3 -m pytest skills/external-review/tests/test_incremental_budget.py skills/external-review/tests/test_failed_r2_bounded_r3.py skills/external-review/tests/test_diff_caps.py -q
python3 -m pytest skills/external-review/tests/ -q
git status --short
```

Results:

- Focused Slice 2 tests: `8 passed`
- Full external-review suite: `141 passed, 1 warning`
- Manual synthetic check: r2 request `84,854` bytes, under the `<200 KB` acceptance gate

5. Overall verdict: ready with small edits

---

## Reviewer stderr (tail)

```text
s/external-review/tests/test_diff_caps.py
  2628	git commit -m "external-reviewer: global diff cap, untracked-file count + line limits"
  2629	```
  2630	

codex
1. Findings

F1. Severity: minor - Slice 2 manual evidence is checked but not recorded.  
[docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:2638) lists the synthetic large-chain check and expected `<200 KB` result, but does not capture the observed request size. I reran the check and got `84,854` bytes, so this is evidence hygiene, not a correctness blocker.

F2. Severity: minor - Worktree has an untracked review artifact directory.  
`git status --short` reports `?? docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice/`. This appears to be the current review chain artifact, but it should be committed, ignored, or otherwise intentionally handled before final closeout.

2. Open questions / assumptions

- Assumption: this post-slice gate is for Slice 2, based on the checked Slice 2 tasks and the `S2-post-slice` review artifact path.
- No implementation-blocking questions.

3. Suggested document edits

- Under Task 2.6 Step 2, add the observed manual-check output, e.g. `Observed: r2 request was 84,854 bytes`.
- After this review completes, record or land the `docs/reviewer/...S2-post-slice/` artifacts according to the repo’s review-chain convention.

4. Verification gaps / commands run

Commands I ran:

```bash
python3 -m pytest skills/external-review/tests/test_incremental_budget.py skills/external-review/tests/test_failed_r2_bounded_r3.py skills/external-review/tests/test_diff_caps.py -q
python3 -m pytest skills/external-review/tests/ -q
git status --short
```

Results:

- Focused Slice 2 tests: `8 passed`
- Full external-review suite: `141 passed, 1 warning`
- Manual synthetic check: r2 request `84,854` bytes, under the `<200 KB` acceptance gate

5. Overall verdict: ready with small edits
tokens used
94,203
```


## Sweep 1

# Review — 2026-05-14-external-reviewer-context-optimisation-plan.md (post-slice, round 1)

- Target: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md`
- Request: `docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice/r1-2026-05-14T1628-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Status: `ok`

---

1. Findings

S1.F1. Severity: important - The slice leaves untracked, incomplete review artifacts in the worktree.  
`git status --short` reports `?? docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice/`. That directory contains only:

- `r1-2026-05-14T1628-primary-request.md`
- `r1-2026-05-14T1628-primary-response.md`
- `r1-2026-05-14T1628-sweep1-request.md`

There is no `chain.json` and no sweep response. For a post-slice completion gate, this should be resolved before claiming the slice is closed: commit the intended review artifacts, remove the partial chain, or rerun/land a complete chain.

S1.F2. Severity: minor - `--incremental-budget-chars` is documented as a cap, but `apply_budget()` can return a prompt over the requested budget.  
[external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:242) trims until `len(out) <= budget_chars`, then appends the budget note afterward. The test also allows overage: [test_incremental_budget.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/tests/test_incremental_budget.py:27). I reproduced `budget_chars=200` returning length `266`. This is small in normal use, but it weakens the “global cap” claim in the CLI help at [external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:968).

S1.F3. Severity: minor - Slice 2 manual acceptance is checked off without recording the observed evidence in the plan.  
[the plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:2638) marks the synthetic large-chain check complete and states the expected `<200 KB` request size, but does not record the actual measured request size.

2. Open questions / assumptions

- I assume this gate is for Slice 2, based on the completed Slice 2 checkboxes and the untracked `S2-post-slice` review chain.
- I assume the untracked review directory is intended slice evidence, not disposable local scratch.

3. Suggested document edits

- Add the observed synthetic check result under Task 2.6 Step 2.
- Either land or discard the partial `docs/reviewer/...S2-post-slice/` artifacts.
- Tighten the budget implementation or docs/tests so “cap” means either exact `<= budget_chars` or explicitly “budget plus diagnostic note.”

4. Verification gaps / commands run

- `python3 -m pytest skills/external-review/tests/` -> `141 passed, 1 warning`
- `git status --short` -> one untracked review artifact directory
- `find docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice -maxdepth 2 -type f ...` -> showed incomplete artifact set
- Budget repro: `apply_budget(..., budget_chars=200)` returned length `266`

5. Overall verdict: revise

---

## Reviewer stderr (tail)

```text
00 KB` result, but does not capture the observed request size. I reran the check and got `84,854` bytes, so this is evidence hygiene, not a correctness blocker.

S1.F2. Severity: minor - Worktree has an untracked review artifact directory.  
`git status --short` reports `?? docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice/`. This appears to be the current review chain artifact, but it should be committed, ignored, or otherwise intentionally handled before final closeout.

2. Open questions / assumptions

- Assumption: this post-slice gate is for Slice 2, based on the checked Slice 2 tasks and the `S2-post-slice` review artifact path.
- No implementation-blocking questions.

3. Suggested document edits

- Under Task 2.6 Step 2, add the observed manual-check output, e.g. `Observed: r2 request was 84,854 bytes`.
- After this review completes, record or land the `docs/reviewer/...S2-post-slice/` artifacts according to the repo’s review-chain convention.

4. Verification gaps / commands run

Commands I ran:

```bash
python3 -m pytest skills/external-review/tests/test_incremental_budget.py skills/external-review/tests/test_failed_r2_bounded_r3.py skills/external-review/tests/test_diff_caps.py -q

codex
The suite is green: `141 passed, 1 warning`. I found no failing acceptance tests, but the repo still has an untracked and apparently incomplete post-slice review artifact directory, so the close-out state is not clean.
exec
/usr/bin/zsh -lc "python3 - <<'PY'
from pathlib import Path
import importlib.util
p=Path('skills/external-review/scripts/external-reviewer.py')
spec=importlib.util.spec_from_file_location('er', p)
er=importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
body = f\"{er.PROMPT_SENTINEL_START}\\n## Review chain summary\\nkeep\\n\\n## Target Preview\\n\" + (\"T\"*10000) + f\"\\n{er.PROMPT_SENTINEL_END}\"
out = er.apply_budget(body, budget_chars=200)
print(len(out))
print(out[:120].replace('\\n','\\\\n'))
PY" in /home/simon/Dev/sigreer/skills/superstar
 succeeded in 0ms:
266
```



## Resolution report for prior round

# Resolution for r1

## F1
Status: fixed
Evidence:
- Commit: ee4185de9ce43e6a874811d064123b89c2f0b8af
- Files: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:2665`
- Verification: grepped the new line; manual recheck ran 84,854 bytes (matches reviewer's measurement)

Notes:
Plan Task 2.6 Step 2 now records the observed r2 request size.

## F2
Status: waived
Evidence:
- N/A — chain folder will be committed by the coordinator at round close-out

Notes:
Per coordinator handoff convention, the post-slice review chain folder is committed as part of the round close-out (S1 followed the same pattern). Not a separate ticket.

## S1.F1
Status: waived (duplicate of F2)
Notes:
Same as F2 — chain artifacts will be committed by the coordinator. Marking duplicate.

## S1.F2
Status: fixed
Evidence:
- Commit: ee4185de9ce43e6a874811d064123b89c2f0b8af
- Files: `skills/external-review/scripts/external-reviewer.py:973` (argparse help), `skills/external-review/scripts/external-reviewer.py:215` (apply_budget docstring)
- Verification: `python3 -m pytest skills/external-review/tests/ -q` → 141 passed (no behaviour change)

Notes:
Documentation tightened to acknowledge the small diagnostic-note overhead. The trim loop continues to fit content to `budget_chars`; the appended `<!-- budget-applied: ... -->` note is ~150 bytes. No code restructure; the test already permits ≤budget+500.

## S1.F3
Status: fixed (duplicate of F1)
Notes:
Same as F1 — Plan Task 2.6 Step 2 now records 84,854 bytes evidence.


## Changes since prior round

Worktree status: dirty

## git diff base..HEAD

diff --git a/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md b/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md
index 4f86857..56e73de 100644
--- a/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md
+++ b/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md
@@ -2662,7 +2662,7 @@ AGENT_REVIEWER_CMD="bash -c 'echo Overall verdict: ready'" \
 ls -la docs/reviewer/plan-plan/r2-*-request.md
 ```
 
-Expected: the round-2 request file is under 200 KB.
+Expected: the round-2 request file is under 200 KB. Observed at S2 close: r2 request was 84,854 bytes (well under the 200 KB ceiling).
 
 - [x] **Step 3: Commit any final fixes**
 
diff --git a/skills/external-review/scripts/external-reviewer.py b/skills/external-review/scripts/external-reviewer.py
index b0e0d08..1eae1a6 100755
--- a/skills/external-review/scripts/external-reviewer.py
+++ b/skills/external-review/scripts/external-reviewer.py
@@ -211,6 +211,9 @@ def apply_budget(text: str, budget_chars: int) -> str:
 
     Appends a `<!-- budget-applied: ... -->` HTML comment immediately before
     the end sentinel summarising trims.
+
+    Note: the final string may exceed `budget_chars` by up to ~200 bytes — the
+    trim loop fits content to the budget, then appends a diagnostic note.
     """
     import re
     if len(text) <= budget_chars:
@@ -967,10 +970,10 @@ def parse_args() -> argparse.Namespace:
     parser.add_argument(
         "--incremental-budget-chars",
         type=int, default=400_000,
-        help="Global cap on assembled prompt size for incremental rounds. "
-             "When exceeded, low-priority sections are trimmed first "
-             "(target preview, diff body, resolution body, prior findings) "
-             "before any user-required content. Default 400000.",
+        help="Target cap on assembled prompt size for incremental rounds. "
+             "Trims low-priority sections first; the final size is the trimmed "
+             "budget plus a small diagnostic note (`<!-- budget-applied: ... -->`, "
+             "~150 bytes). Default 400000.",
     )
     return parser.parse_args()
 


## git diff HEAD (uncommitted)



## Untracked files

- docs/reviewer/external-reviewer-context-optimisation-plan-S2-post-slice/ (omitted: binary or unreadable)


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
/home/simon/Dev/sigreer/skills/superstar

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md

Additional context files:
- docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md

Review output contract:
1. Findings
   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
     stable if this review is iterated in subsequent rounds.
   - Mark severity inline: `Severity: blocking | important | minor | nit`.
2. Open questions / assumptions
3. Suggested document edits
4. Verification gaps / commands that should be run, if any
5. Overall verdict: one of "ready", "ready with small edits", or "revise"

Read the files from disk. Do not rely only on the snippets in this prompt.


## Target Preview

### docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md

    1	# external-reviewer context optimisation Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Eliminate the recursive prompt-echo loop in external-reviewer chains and bound incremental-round prompt size, while preserving the JSON output contract and exit codes.
    6	
    7	**Architecture:** Three slices: (S1) make failure truthful — failed reviewer turns can never produce a fake verdict, prompt echoes never reach disk, preambles walk past failed rounds; (S2) put incremental-mode prompts on a diet — drop context previews, trim target preview, cap prior-text reads, add a single budget knob with deterministic preservation priority; (S3) update `skills/external-review/SKILL.md` with the new behaviour. All changes target a single file (`skills/external-review/scripts/external-reviewer.py`) and its test suite (`skills/external-review/tests/`).
    8	
    9	**Tech Stack:** Python 3 standard library only (no new deps). Test framework: pytest. Module loaded via importlib because the script has a hyphen in its filename.
   10	
   11	**Source spec:** `docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md` (status: `ready`).
   12	
   13	**Spec → Plan mapping for the test items.** The spec's S3 lists 15 tests plus a docs item; this plan pairs each test with its implementation under TDD discipline. The mapping is:
   14	
   15	| Spec S3 item | Plan task |
   16	|---|---|
   17	| 1. failed-process verdict suppression | Task 1.5 |
   18	| 2. failed sweep can't poison merged findings | Task 1.6 |
   19	| 3. sentinel-stripping happy path | Task 1.1 |
   20	| 4. sentinel-stripping truncated echo | Task 1.1 |
   21	| 5. success-stderr dropped or capped | Task 1.3 |
   22	| 6. failed-stderr cap after sentinel-stripping | Task 1.4 |
   23	| 7. preamble walks back past failed rounds | Task 1.10 |
   24	| 8. preamble treats `status: "unknown"` as untrusted | Task 1.10 |
   25	| 9. process-failed prior round bypasses resolution gate | Task 1.11 |
   26	| 10. incremental drops context previews | Task 2.1 |
   27	| 11. target preview trimmed on incremental | Task 2.2 |
   28	| 12. prior-text caps applied | Task 2.3 |
   29	| 13. budget cap preserves priority order | Task 2.4 |
   30	| 14. r3-request bounded after simulated failed r2 | Task 1.12 |
   31	| 15. chain.json soft-migration | Task 1.9 |
   32	| 16. SKILL.md docs update | Task 3.1 |
   33	
   34	---
   35	
   36	## Files at a glance
   37	
   38	- **Modified:** `skills/external-review/scripts/external-reviewer.py` — all code changes live here.
   39	- **Modified:** `skills/external-review/SKILL.md` — docs update in S3.
   40	- **Created (tests):** `skills/external-review/tests/test_sentinel_stripper.py`, `test_response_artifact.py`, `test_failed_round_truth.py`, `test_merged_findings_skips_failed.py`, `test_returncode_status_persisted.py`, `test_preamble_skips_failed.py`, `test_resolution_gate_bypass.py`, `test_failed_r2_bounded_r3.py`, `test_chain_soft_migration.py`, `test_incremental_drops_context.py`, `test_target_preview_trim.py`, `test_prior_text_caps.py`, `test_incremental_budget.py`, `test_diff_caps.py`.
   41	- **Untouched:** every other file in the repo.
   42	
   43	## Test-file boilerplate
   44	
   45	Every new test file in this plan starts with the same import block as the existing tests in `skills/external-review/tests/`:
   46	
   47	```python
   48	from pathlib import Path
   49	import sys
   50	import importlib.util
   51	
   52	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
   53	sys.path.insert(0, str(SCRIPTS))
   54	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
   55	er = importlib.util.module_from_spec(spec)
   56	spec.loader.exec_module(er)
   57	```
   58	
   59	Reference: `skills/external-review/tests/test_manifest.py:1-13`. Re-paste this block at the top of every new test file in the steps below — do not abbreviate it.
   60	
   61	## Conventions used throughout the plan
   62	
   63	- All file paths are relative to the repo root `/home/simon/Dev/sigreer/skills/superstar/`.
   64	- All `python3 -m pytest` invocations should be run from the repo root.
   65	- Each task ends in a commit. Commit messages follow `<scope>: <change>`; `<scope>` is `external-reviewer`.
   66	- Line-number anchors (e.g. `external-reviewer.py:451`) reflect the script *before* this plan's edits. As the plan proceeds, line numbers will drift; the surrounding context strings in each step's `Edit` blocks are what makes the edit unambiguous, not the anchors.
   67	
   68	---
   69	
   70	## Slice 1 — Failure-truth + echo containment
   71	
   72	This is the keystone slice. Without it, any size optimisation only delays the corruption. Do not begin Slice 2 until every task in Slice 1 is committed and the test suite is green.
   73	
   74	### Task 1.1: Sentinel stripper
   75	
   76	**Files:**
   77	- Modify: `skills/external-review/scripts/external-reviewer.py` (add module-level constants near the top, add helper near `parse_verdict`)
   78	- Create: `skills/external-review/tests/test_sentinel_stripper.py`
   79	
   80	- [x] **Step 1: Write the failing tests**
   81	
   82	Create `skills/external-review/tests/test_sentinel_stripper.py`:
   83	
   84	```python
   85	from pathlib import Path
   86	import sys
   87	import importlib.util
   88	
   89	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
   90	sys.path.insert(0, str(SCRIPTS))
   91	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
   92	er = importlib.util.module_from_spec(spec)
   93	spec.loader.exec_module(er)
   94	
   95	
   96	def test_strip_removes_full_marker_block():
   97	    text = (
   98	        "preamble\n"
   99	        f"{er.PROMPT_SENTINEL_START}\nechoed prompt body\n{er.PROMPT_SENTINEL_END}\n"
  100	        "actual review\n"
  101	    )
  102	    out = er.strip_prompt_echo(text)
  103	    assert "echoed prompt body" not in out
  104	    assert er.PROMPT_SENTINEL_START not in out
  105	    assert er.PROMPT_SENTINEL_END not in out
  106	    assert "preamble" in out
  107	    assert "actual review" in out
  108	
  109	
  110	def test_strip_end_only_deletes_from_start_of_stream():
  111	    text = f"truncated echo tail here\n{er.PROMPT_SENTINEL_END}\nactual review\n"
  112	    out = er.strip_prompt_echo(text)
  113	    assert "truncated echo tail here" not in out
  114	    assert er.PROMPT_SENTINEL_END not in out
  115	    assert out.strip().startswith("actual review")
  116	
  117	
  118	def test_strip_start_only_deletes_to_end_of_stream():
  119	    text = f"preamble\n{er.PROMPT_SENTINEL_START}\nprompt body leaks to end\n"
  120	    out = er.strip_prompt_echo(text)
  121	    assert "prompt body leaks to end" not in out
  122	    assert er.PROMPT_SENTINEL_START not in out
  123	    assert out.strip() == "preamble"
  124	
  125	
  126	def test_strip_no_markers_passes_text_through():
  127	    text = "a clean review with no echo at all"
  128	    assert er.strip_prompt_echo(text) == text
  129	
  130	
  131	def test_strip_handles_empty_string():
  132	    assert er.strip_prompt_echo("") == ""
  133	
  134	
  135	def test_strip_handles_multiple_blocks():
  136	    text = (
  137	        f"head\n{er.PROMPT_SENTINEL_START}\nblock1\n{er.PROMPT_SENTINEL_END}\n"
  138	        f"middle\n{er.PROMPT_SENTINEL_START}\nblock2\n{er.PROMPT_SENTINEL_END}\n"
  139	        "tail"
  140	    )
  141	    out = er.strip_prompt_echo(text)
  142	    assert "block1" not in out
  143	    assert "block2" not in out
  144	    assert "head" in out and "middle" in out and "tail" in out
  145	```
  146	
  147	- [x] **Step 2: Run tests to verify they fail**
  148	
  149	Run: `python3 -m pytest skills/external-review/tests/test_sentinel_stripper.py -v`
  150	Expected: all six tests fail with `AttributeError: module 'external_reviewer' has no attribute 'PROMPT_SENTINEL_START'`.

[truncated: 2668 additional lines]

<!-- superstar-prompt:end -->