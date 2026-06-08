<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 2 of p9-s1-review-pipeline-quick-wins-P9-S1-post-slice.

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
| 1 | revise | None | None |

## Prior-round findings

Source: merged findings from r1 (authoritative)

# Merged findings for r1

## Primary

# Review — 2026-06-06-P9.S1-review-pipeline-quick-wins.md (post-slice, round 1)

- Target: `docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md`
- Request: `docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/r1-2026-06-07T0045-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

No findings. The S1 implementation matches the plan/spec scope, and the P9.S1-scoped artifact check is clean.

2. Open questions / assumptions

Assumption: the unchecked boxes in `docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md` are treated as implementation instructions, not a live completion checklist. Actual completion evidence is in commits, tests, tracker state, and repo behavior.

3. Suggested document edits

None required for this gate.

4. Verification gaps / commands that should be run, if any

Verified:
- `python -m pytest skills/external-review/tests -q` → `297 passed`
- `git diff --check` → clean
- `tasktool validate` → `ok`
- `tasktool artifact status P9.S1 --strict` → `artifact status: ok`
- CLI smoke checks for `--review-depth`, `--model`, and `stats --since` help text passed
- Behavioral smoke for depth/model helpers printed `OK`

Residual non-blocking repo issue: unscoped `tasktool artifact status --strict` fails on unrelated X29 artifact refs, not P9.S1.

Overall verdict: ready


## Sweep 1

# Review — 2026-06-06-P9.S1-review-pipeline-quick-wins.md (post-slice, round 1)

- Target: `docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md`
- Request: `docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/r1-2026-06-07T0045-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

S1.F1. Severity: blocking — `git diff --check main..HEAD` fails on a committed whitespace error: `skills/external-review/tests/test_resolution_gate.py:55: new blank line at EOF.` This contradicts the claimed clean verification and leaves a standard completion gate failing, even though the pytest suite passes.

S1.F2. Severity: minor — Some guidance still describes the resolution bypass/gate as post-slice/post-phase-specific after the implementation made it kind-independent. See `skills/external-review/SKILL.md:132` and `skills/subagent-driven-development/SKILL.md:331`. The canonical resolution section is updated at `skills/external-review/SKILL.md:247`, but these stale lines can mislead future spec/plan review retries.

2. Open questions / assumptions

No open questions. I treated the unchecked boxes in the plan as implementation instructions, not a live completion checklist.

3. Suggested document edits

Update the stale guidance lines to say process-failure bypass and resolution-gate refusal apply to round 2+ for any kind, while post-slice/post-phase still use fix subagents.

4. Verification gaps / commands that should be run, if any

Verified:
- `python -m pytest skills/external-review/tests -q` -> `297 passed`
- `tasktool artifact status P9.S1 --strict` -> `artifact status: ok`
- `tasktool validate` -> `ok`

Must rerun after fixing S1.F1:
- `git diff --check main..HEAD`
- optionally `python -m pytest skills/external-review/tests/test_resolution_gate.py -q`

Overall verdict: revise



## Resolution report for prior round

# Resolution for r1

## S1.F1
Status: fixed
Evidence:
- Commit: 7a0f9541cd1778458605d7de6f7e0e2238b9118a
- Files: `skills/external-review/tests/test_resolution_gate.py:55`
- Verification: `git diff --check main..HEAD` → exit 0 (clean); `python -m pytest skills/external-review/tests/test_resolution_gate.py -q` → 2 passed in 0.89s

Notes:
Removed the stray trailing blank line left by the Task 2 test deletion. The committed HEAD had a double newline at EOF (`\n\n`); fixed to a single newline (`\n`).

## S1.F2
Status: fixed
Evidence:
- Commit: 7a0f9541cd1778458605d7de6f7e0e2238b9118a
- Files: `skills/external-review/SKILL.md:132`, `skills/subagent-driven-development/SKILL.md:331`
- Verification:
  - `skills/external-review/SKILL.md:132`: "For any kind, the next round's resolution-required gate is **bypassed** with a stderr notice. A process failure has no findings to resolve; the next round is a re-attempt of the same review, not a fix-and-re-review. For `post-slice` / `post-phase`, a fix subagent is still used when the retry itself returns findings."
  - `skills/subagent-driven-development/SKILL.md:331`: "Round N+1 of any kind exits 3 without `r{N-1}-resolution.md` or `--allow-missing-resolution`; post-slice/post-phase still delegate fixes to a subagent."

Notes:
Updated both stale lines to state the gate/bypass applies to round 2+ of any kind; post-slice/post-phase delegation language preserved.


## Changes since prior round

Worktree status: dirty

### git diff base..HEAD

diff --git a/docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/r1-resolution.md b/docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/r1-resolution.md
new file mode 100644
index 0000000..5cede83
--- /dev/null
+++ b/docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/r1-resolution.md
@@ -0,0 +1,23 @@
+# Resolution for r1
+
+## S1.F1
+Status: fixed
+Evidence:
+- Commit: 7a0f9541cd1778458605d7de6f7e0e2238b9118a
+- Files: `skills/external-review/tests/test_resolution_gate.py:55`
+- Verification: `git diff --check main..HEAD` → exit 0 (clean); `python -m pytest skills/external-review/tests/test_resolution_gate.py -q` → 2 passed in 0.89s
+
+Notes:
+Removed the stray trailing blank line left by the Task 2 test deletion. The committed HEAD had a double newline at EOF (`\n\n`); fixed to a single newline (`\n`).
+
+## S1.F2
+Status: fixed
+Evidence:
+- Commit: 7a0f9541cd1778458605d7de6f7e0e2238b9118a
+- Files: `skills/external-review/SKILL.md:132`, `skills/subagent-driven-development/SKILL.md:331`
+- Verification:
+  - `skills/external-review/SKILL.md:132`: "For any kind, the next round's resolution-required gate is **bypassed** with a stderr notice. A process failure has no findings to resolve; the next round is a re-attempt of the same review, not a fix-and-re-review. For `post-slice` / `post-phase`, a fix subagent is still used when the retry itself returns findings."
+  - `skills/subagent-driven-development/SKILL.md:331`: "Round N+1 of any kind exits 3 without `r{N-1}-resolution.md` or `--allow-missing-resolution`; post-slice/post-phase still delegate fixes to a subagent."
+
+Notes:
+Updated both stale lines to state the gate/bypass applies to round 2+ of any kind; post-slice/post-phase delegation language preserved.
diff --git a/skills/external-review/SKILL.md b/skills/external-review/SKILL.md
index bc7c9f7..811463c 100644
--- a/skills/external-review/SKILL.md
+++ b/skills/external-review/SKILL.md
@@ -129,7 +129,7 @@ When the configured reviewer command exits non-zero, the round is recorded as a
 
 - The persisted response file is a short stub (≤ 8 KB total): header, status, and the sentinel-stripped tail of the reviewer's stderr capped at 4 KB. No stdout is written.
 - `chain.json` records `status: "failed"`, `returncode: <rc>`, `verdict: null`, `verdict_valid: false` on both the round entry and the per-reviewer entry.
-- For `post-slice` / `post-phase`, the next round's resolution-required gate is **bypassed** with a stderr notice. A process failure has no findings to resolve; the next round is a re-attempt of the same review, not a fix-and-re-review.
+- For any kind, the next round's resolution-required gate is **bypassed** with a stderr notice. A process failure has no findings to resolve; the next round is a re-attempt of the same review, not a fix-and-re-review. For `post-slice` / `post-phase`, a fix subagent is still used when the retry itself returns findings.
 - The next round's preamble walks backward past `status: "failed"` (and legacy `status: "unknown"`) rounds and embeds the merged-findings from the most recent `status: "ok"` round, prefixed with a `Note: rounds N..K were process failures...; skipped.` line. If no successful prior round exists, only the chain summary table is embedded.
 
 **Sentinel-wrapped prompts.** Every prompt is wrapped in `<!-- superstar-prompt:start -->` / `<!-- superstar-prompt:end -->` markers. If a reviewer echoes the prompt on stdout or stderr, the markers let the script strip the echo before persisting to disk, eliminating the recursive prompt-bloat class.
diff --git a/skills/external-review/tests/test_resolution_gate.py b/skills/external-review/tests/test_resolution_gate.py
index d72681d..60f4965 100644
--- a/skills/external-review/tests/test_resolution_gate.py
+++ b/skills/external-review/tests/test_resolution_gate.py
@@ -52,4 +52,3 @@ def test_post_slice_round_2_proceeds_with_waiver(tmp_path):
               "--file", "plan.md", "--emit", "json",
               "--allow-missing-resolution")
     assert r2.returncode == 0, r2.stderr
-
diff --git a/skills/subagent-driven-development/SKILL.md b/skills/subagent-driven-development/SKILL.md
index 5a38276..cbc0376 100644
--- a/skills/subagent-driven-development/SKILL.md
+++ b/skills/subagent-driven-development/SKILL.md
@@ -328,7 +328,7 @@ Done!
 | "I'll read the file to figure out what's wrong before delegating"         | No. Dispatch an investigator subagent and wait for the summary.        |
 | "It's just a one-line change, no need to delegate"                        | Bar is *strictly cheaper than delegating*. When in doubt, delegate.    |
 | "I'll skip post-slice review on this one, it's a small slice"             | No. Slice boundary is a gate. Run `[[external-review]] --kind post-slice`.|
-| "I'll resubmit without the resolution file, the reviewer will figure it out" | No. Post-slice/post-phase round N+1 exits 3 without `r{N-1}-resolution.md` or `--allow-missing-resolution`. |
+| "I'll resubmit without the resolution file, the reviewer will figure it out" | No. Round N+1 of any kind exits 3 without `r{N-1}-resolution.md` or `--allow-missing-resolution`; post-slice/post-phase still delegate fixes to a subagent. |
 | "The plan's final close-out task ran, so I should ask before post-slice review" | No. The slice is not closed until `[[external-review]] --kind post-slice` passes and tasktool close succeeds afterward. |
 
 **Process reds (also never):**


### git diff HEAD (uncommitted)



### Untracked files

- docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/.reviewer-output/ (omitted: binary or unreadable)
### docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/chain.json

```
{
  "schema_version": 1,
  "chain": "p9-s1-review-pipeline-quick-wins-P9-S1-post-slice",
  "kind": "post-slice",
  "target": "docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md",
  "work_id": "P9.S1",
  "legacy_migrated": false,
  "rounds": [
    {
      "round": 1,
      "reviewers": [
        {
          "role": "primary",
          "sweep_group": null,
          "parent_round": 1,
          "request": "r1-2026-06-07T0045-primary-request.md",
          "response": "r1-2026-06-07T0045-primary-response.md",
          "verdict": "ready",
          "verdict_valid": true,
          "returncode": 0,
          "status": "ok",
          "provider": "codex",
          "caller_provider": "claude",
          "model": null,
          "sandbox": {
            "repo_root": "/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p9-s1-quick-wins-kind-aware-depth-defaults",
            "scratch_dir": "/tmp/superstar-reviewer-p9-s1-review-pipeline-quick-wins-P9-S1-post-slice-r1-primary-60k6ugc0",
            "response_dir": "docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/.reviewer-output/r1-primary",
            "mode": "workspace-write-with-read-access"
          },
          "started_at": "2026-06-06T23:45:19.972Z",
          "finished_at": "2026-06-06T23:48:43.750Z",
          "duration_ms": 203778,
          "estimated_usage": {
            "formula": "ceil(chars / 4)",
            "prompt_chars": 45009,
            "response_chars": 1438,
            "estimated_input_tokens": 11253,
            "estimated_output_tokens": 360,
            "estimated_total_tokens": 11613
          },
          "exact_usage": null,
          "usage_capture_status": "estimated_only",
          "usage_capture_error": null
        },
        {
          "role": "sweep",
          "sweep_group": 1,
          "parent_round": 1,
          "request": "r1-2026-06-07T0045-sweep1-request.md",
          "response": "r1-2026-06-07T0045-sweep1-response.md",
          "verdict": "revise",
          "verdict_valid": true,
          "returncode": 0,
          "status": "ok",
          "provider": "codex",
          "caller_provider": "claude",
          "model": null,
          "sandbox": {
            "repo_root": "/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p9-s1-quick-wins-kind-aware-depth-defaults",
            "scratch_dir": "/tmp/superstar-reviewer-p9-s1-review-pipeline-quick-wins-P9-S1-post-slice-r1-sweep1-rzlmrwat",
            "response_dir": "docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/.reviewer-output/r1-sweep1",
            "mode": "workspace-write-with-read-access"
          },
          "started_at": "2026-06-06T23:48:43.753Z",
          "finished_at": "2026-06-06T23:51:25.187Z",
          "duration_ms": 161433,
          "estimated_usage": {
            "formula": "ceil(chars / 4)",
            "prompt_chars": 45009,
            "response_chars": 1917,
            "estimated_input_tokens": 11253,
            "estimated_output_tokens": 480,
            "estimated_total_tokens": 11733
          },
          "exact_usage": null,
          "usage_capture_status": "estimated_only",
          "usage_capture_error": null
        }
      ],
      "status": "ok",
      "returncode": 0,
      "started_at": "2026-06-06T23:45:19.972Z",
      "finished_at": "2026-06-06T23:48:43.750Z",
      "duration_ms": 203778,
      "provider": "codex",
      "caller_provider": "claude",
      "model": null,
      "estimated_usage": {
        "formula": "ceil(chars / 4)",
        "prompt_chars": 45009,
        "response_chars": 1438,
        "estimated_input_tokens": 11253,
        "estimated_output_tokens": 360,
        "estimated_total_tokens": 11613
      },
      "exact_usage": null,
      "usage_capture_status": "estimated_only",
      "usage_capture_error": null,
      "merged_verdict": "revise",
      "merged_findings": "r1-merged-findings.md",
      "request": "r1-2026-06-07T0045-primary-request.md",
      "response": "r1-2026-06-07T0045-primary-response.md",
      "resolution": null,
      "resolution_parse_status": null,
      "resolution_waiver": false,
      "head_sha_at_request": "1cf127f79b7276e3e038c14b03e02e46cea0653a",
      "head_sha_after_round": "1cf127f79b7276e3e038c14b03e02e46cea0653a",
      "worktree_dirty_at_request": true,
      "verdict": "ready",
      "verdict_valid": true,
      "findings_count": null,
      "blocking_findings_count": null,
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

### docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/r1-2026-06-07T0045-primary-request.md

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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p9-s1-quick-wins-kind-aware-depth-defaults

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md

Additional context files:
- docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md
- /tmp/p9s1-brief-context.md

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

### docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md

    1	# P9.S1 — Review-Pipeline Quick Wins Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Cut external-review cost by defaulting depth per kind, extending the resolution gate to all kinds, tiering reviewer models, trimming context guidance, and adding `stats --since` with a rounds-per-slice metric.
    6	
    7	**Architecture:** All behaviour changes live in `skills/external-review/scripts/external-reviewer.py` (CLI) and `skills/project-setup/scripts/reviewer-agent` (provider wrapper); guidance changes live in four SKILL.md files. Every CLI change is opt-out-preserving: explicit flags and unset env vars reproduce today's behaviour byte-for-byte.
    8	
    9	**Tech Stack:** Python 3 (stdlib only), bash, pytest (`skills/external-review/tests/`).
   10	
   11	**Spec:** `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md` (S1 section).
   12	
   13	**Scheduling:** `P9.S1` is ratified, has no `depends_on`, and gates `P9.S2`/`P9.S3` (both depend on it; S3 also depends on S2). Declared integration surfaces: `skills/external-review/scripts/external-reviewer.py`, `skills/external-review/SKILL.md`, `skills/project-setup/scripts/reviewer-agent`. No sibling slice may run in parallel with this one (`tasktool surface check P9` is clean because S2/S3 are serialized behind S1).
   14	
   15	---
   16	
   17	## Conventions used by every task
   18	
   19	- Repo root: `/home/simon/Dev/sigreer/skills/superstar` (work from an isolated worktree created via `superstar:using-git-worktrees`).
   20	- The module under test is loaded the way every existing test does it:
   21	
   22	```python
   23	from pathlib import Path
   24	import sys, importlib.util
   25	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
   26	sys.path.insert(0, str(SCRIPTS))
   27	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
   28	er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
   29	```
   30	
   31	- Test command: `python -m pytest skills/external-review/tests/<file> -q` from the repo root.
   32	- Line numbers below are anchors as of commit `b9babcf`; re-locate with the given grep if drifted.
   33	
   34	### Task 0: Start the slice
   35	
   36	- [ ] **Step 1: Mark the slice started**
   37	
   38	Run: `tasktool start P9.S1`
   39	Expected: exit 0; `tasktool show P9.S1` shows status `started`.
   40	
   41	---
   42	
   43	### Task 1: Kind-aware depth defaults
   44	
   45	**Files:**
   46	- Modify: `skills/external-review/scripts/external-reviewer.py` (argparse ~line 1851; main review path after the work-id check ~line 2445; round-entry construction — locate with `grep -n '"review_depth":' skills/external-review/scripts/external-reviewer.py`)
   47	- Test: `skills/external-review/tests/test_depth_defaults.py` (create)
   48	
   49	- [ ] **Step 1: Write the failing tests**
   50	
   51	Create `skills/external-review/tests/test_depth_defaults.py`:
   52	
   53	```python
   54	from pathlib import Path
   55	import sys, importlib.util
   56	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
   57	sys.path.insert(0, str(SCRIPTS))
   58	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
   59	er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
   60	
   61	
   62	def test_spec_defaults_standard():
   63	    assert er.resolve_review_depth(None, "spec") == "standard"
   64	
   65	
   66	def test_plan_defaults_standard():
   67	    assert er.resolve_review_depth(None, "plan") == "standard"
   68	
   69	
   70	def test_design_implementation_other_default_standard():
   71	    for kind in ("design", "implementation", "other"):
   72	        assert er.resolve_review_depth(None, kind) == "standard"
   73	
   74	
   75	def test_post_slice_defaults_thorough():
   76	    assert er.resolve_review_depth(None, "post-slice") == "thorough"
   77	
   78	
   79	def test_post_phase_defaults_thorough():
   80	    assert er.resolve_review_depth(None, "post-phase") == "thorough"
   81	
   82	
   83	def test_explicit_flag_wins_over_kind_default():
   84	    assert er.resolve_review_depth("exhaustive", "spec") == "exhaustive"
   85	    assert er.resolve_review_depth("standard", "post-slice") == "standard"
   86	
   87	
   88	def test_argparse_review_depth_default_is_none():
   89	    args = er.parse_args([
   90	        "review", "--kind", "spec", "--file", "x.md",
   91	    ])
   92	    assert args.review_depth is None
   93	```
   94	
   95	- [ ] **Step 2: Run tests to verify they fail**
   96	
   97	Run: `python -m pytest skills/external-review/tests/test_depth_defaults.py -q`
   98	Expected: FAIL — `AttributeError: ... has no attribute 'resolve_review_depth'`.
   99	
  100	- [ ] **Step 3: Implement the resolver and rewire the default**
  101	
  102	In `external-reviewer.py`, directly below the `DEPTH_DEFAULTS` dict (~line 1744), add:
  103	
  104	```python
  105	# Kind-aware depth defaults (P9.S1): post gates get sweeps by default,
  106	# planning gates stay cheap. Explicit --review-depth always wins.
  107	KIND_DEPTH_DEFAULTS = {
  108	    "post-slice": "thorough",
  109	    "post-phase": "thorough",
  110	}
  111	
  112	
  113	def resolve_review_depth(explicit: str | None, kind: str) -> str:
  114	    if explicit is not None:
  115	        return explicit
  116	    return KIND_DEPTH_DEFAULTS.get(kind, "standard")
  117	```
  118	
  119	Change the argparse line (~1851) from:
  120	
  121	```python
  122	    sp_review.add_argument("--review-depth", choices=["standard", "thorough", "exhaustive"],
  123	                        default="standard")
  124	```
  125	
  126	to:
  127	
  128	```python
  129	    sp_review.add_argument("--review-depth", choices=["standard", "thorough", "exhaustive"],
  130	                        default=None,
  131	                        help="Default: 'thorough' for post-slice/post-phase, 'standard' otherwise.")
  132	```
  133	
  134	In the review path of `main`, immediately after the `--work-id` requirement check (locate with `grep -n 'work-id is required' skills/external-review/scripts/external-reviewer.py`, ~line 2439-2445), add:
  135	
  136	```python
  137	    args.review_depth = resolve_review_depth(args.review_depth, args.kind)
  138	```
  139	
  140	Every downstream use (`plan_sweeps(depth=args.review_depth, ...)` twice, and the JSON emit `"review_depth": args.review_depth`) then sees the resolved value — verify with `grep -n 'args.review_depth' skills/external-review/scripts/external-reviewer.py` that all uses are after the resolution line.
  141	
  142	- [ ] **Step 4: Record `depth_resolved` in the chain manifest**
  143	
[truncated: 690 additional lines]
```

### docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/r1-2026-06-07T0045-primary-response.md

```
# Review — 2026-06-06-P9.S1-review-pipeline-quick-wins.md (post-slice, round 1)

- Target: `docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md`
- Request: `docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/r1-2026-06-07T0045-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

No findings. The S1 implementation matches the plan/spec scope, and the P9.S1-scoped artifact check is clean.

2. Open questions / assumptions

Assumption: the unchecked boxes in `docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md` are treated as implementation instructions, not a live completion checklist. Actual completion evidence is in commits, tests, tracker state, and repo behavior.

3. Suggested document edits

None required for this gate.

4. Verification gaps / commands that should be run, if any

Verified:
- `python -m pytest skills/external-review/tests -q` → `297 passed`
- `git diff --check` → clean
- `tasktool validate` → `ok`
- `tasktool artifact status P9.S1 --strict` → `artifact status: ok`
- CLI smoke checks for `--review-depth`, `--model`, and `stats --since` help text passed
- Behavioral smoke for depth/model helpers printed `OK`

Residual non-blocking repo issue: unscoped `tasktool artifact status --strict` fails on unrelated X29 artifact refs, not P9.S1.

Overall verdict: ready

```

### docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/r1-2026-06-07T0045-sweep1-request.md

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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p9-s1-quick-wins-kind-aware-depth-defaults

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md

Additional context files:
- docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md
- /tmp/p9s1-brief-context.md

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

### docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md

    1	# P9.S1 — Review-Pipeline Quick Wins Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Cut external-review cost by defaulting depth per kind, extending the resolution gate to all kinds, tiering reviewer models, trimming context guidance, and adding `stats --since` with a rounds-per-slice metric.
    6	
    7	**Architecture:** All behaviour changes live in `skills/external-review/scripts/external-reviewer.py` (CLI) and `skills/project-setup/scripts/reviewer-agent` (provider wrapper); guidance changes live in four SKILL.md files. Every CLI change is opt-out-preserving: explicit flags and unset env vars reproduce today's behaviour byte-for-byte.
    8	
    9	**Tech Stack:** Python 3 (stdlib only), bash, pytest (`skills/external-review/tests/`).
   10	
   11	**Spec:** `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md` (S1 section).
   12	
   13	**Scheduling:** `P9.S1` is ratified, has no `depends_on`, and gates `P9.S2`/`P9.S3` (both depend on it; S3 also depends on S2). Declared integration surfaces: `skills/external-review/scripts/external-reviewer.py`, `skills/external-review/SKILL.md`, `skills/project-setup/scripts/reviewer-agent`. No sibling slice may run in parallel with this one (`tasktool surface check P9` is clean because S2/S3 are serialized behind S1).
   14	
   15	---
   16	
   17	## Conventions used by every task
   18	
   19	- Repo root: `/home/simon/Dev/sigreer/skills/superstar` (work from an isolated worktree created via `superstar:using-git-worktrees`).
   20	- The module under test is loaded the way every existing test does it:
   21	
   22	```python
   23	from pathlib import Path
   24	import sys, importlib.util
   25	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
   26	sys.path.insert(0, str(SCRIPTS))
   27	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
   28	er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
   29	```
   30	
   31	- Test command: `python -m pytest skills/external-review/tests/<file> -q` from the repo root.
   32	- Line numbers below are anchors as of commit `b9babcf`; re-locate with the given grep if drifted.
   33	
   34	### Task 0: Start the slice
   35	
   36	- [ ] **Step 1: Mark the slice started**
   37	
   38	Run: `tasktool start P9.S1`
   39	Expected: exit 0; `tasktool show P9.S1` shows status `started`.
   40	
   41	---
   42	
   43	### Task 1: Kind-aware depth defaults
   44	
   45	**Files:**
   46	- Modify: `skills/external-review/scripts/external-reviewer.py` (argparse ~line 1851; main review path after the work-id check ~line 2445; round-entry construction — locate with `grep -n '"review_depth":' skills/external-review/scripts/external-reviewer.py`)
   47	- Test: `skills/external-review/tests/test_depth_defaults.py` (create)
   48	
   49	- [ ] **Step 1: Write the failing tests**
   50	
   51	Create `skills/external-review/tests/test_depth_defaults.py`:
   52	
   53	```python
   54	from pathlib import Path
   55	import sys, importlib.util
   56	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
   57	sys.path.insert(0, str(SCRIPTS))
   58	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
   59	er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
   60	
   61	
   62	def test_spec_defaults_standard():
   63	    assert er.resolve_review_depth(None, "spec") == "standard"
   64	
   65	
   66	def test_plan_defaults_standard():
   67	    assert er.resolve_review_depth(None, "plan") == "standard"
   68	
   69	
   70	def test_design_implementation_other_default_standard():
   71	    for kind in ("design", "implementation", "other"):
   72	        assert er.resolve_review_depth(None, kind) == "standard"
   73	
   74	
   75	def test_post_slice_defaults_thorough():
   76	    assert er.resolve_review_depth(None, "post-slice") == "thorough"
   77	
   78	
   79	def test_post_phase_defaults_thorough():
   80	    assert er.resolve_review_depth(None, "post-phase") == "thorough"
   81	
   82	
   83	def test_explicit_flag_wins_over_kind_default():
   84	    assert er.resolve_review_depth("exhaustive", "spec") == "exhaustive"
   85	    assert er.resolve_review_depth("standard", "post-slice") == "standard"
   86	
   87	
   88	def test_argparse_review_depth_default_is_none():
   89	    args = er.parse_args([
   90	        "review", "--kind", "spec", "--file", "x.md",
   91	    ])
   92	    assert args.review_depth is None
   93	```
   94	
   95	- [ ] **Step 2: Run tests to verify they fail**
   96	
   97	Run: `python -m pytest skills/external-review/tests/test_depth_defaults.py -q`
   98	Expected: FAIL — `AttributeError: ... has no attribute 'resolve_review_depth'`.
   99	
  100	- [ ] **Step 3: Implement the resolver and rewire the default**
  101	
  102	In `external-reviewer.py`, directly below the `DEPTH_DEFAULTS` dict (~line 1744), add:
  103	
  104	```python
  105	# Kind-aware depth defaults (P9.S1): post gates get sweeps by default,
  106	# planning gates stay cheap. Explicit --review-depth always wins.
  107	KIND_DEPTH_DEFAULTS = {
  108	    "post-slice": "thorough",
  109	    "post-phase": "thorough",
  110	}
  111	
  112	
  113	def resolve_review_depth(explicit: str | None, kind: str) -> str:
  114	    if explicit is not None:
  115	        return explicit
  116	    return KIND_DEPTH_DEFAULTS.get(kind, "standard")
  117	```
  118	
  119	Change the argparse line (~1851) from:
  120	
  121	```python
  122	    sp_review.add_argument("--review-depth", choices=["standard", "thorough", "exhaustive"],
  123	                        default="standard")
  124	```
  125	
  126	to:
  127	
  128	```python
  129	    sp_review.add_argument("--review-depth", choices=["standard", "thorough", "exhaustive"],
  130	                        default=None,
  131	                        help="Default: 'thorough' for post-slice/post-phase, 'standard' otherwise.")
  132	```
  133	
  134	In the review path of `main`, immediately after the `--work-id` requirement check (locate with `grep -n 'work-id is required' skills/external-review/scripts/external-reviewer.py`, ~line 2439-2445), add:
  135	
  136	```python
  137	    args.review_depth = resolve_review_depth(args.review_depth, args.kind)
  138	```
  139	
  140	Every downstream use (`plan_sweeps(depth=args.review_depth, ...)` twice, and the JSON emit `"review_depth": args.review_depth`) then sees the resolved value — verify with `grep -n 'args.review_depth' skills/external-review/scripts/external-reviewer.py` that all uses are after the resolution line.
  141	
  142	- [ ] **Step 4: Record `depth_resolved` in the chain manifest**
  143	
[truncated: 690 additional lines]
```

### docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/r1-2026-06-07T0045-sweep1-response.md

```
# Review — 2026-06-06-P9.S1-review-pipeline-quick-wins.md (post-slice, round 1)

- Target: `docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md`
- Request: `docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/r1-2026-06-07T0045-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1. Severity: blocking — `git diff --check main..HEAD` fails on a committed whitespace error: `skills/external-review/tests/test_resolution_gate.py:55: new blank line at EOF.` This contradicts the claimed clean verification and leaves a standard completion gate failing, even though the pytest suite passes.

F2. Severity: minor — Some guidance still describes the resolution bypass/gate as post-slice/post-phase-specific after the implementation made it kind-independent. See `skills/external-review/SKILL.md:132` and `skills/subagent-driven-development/SKILL.md:331`. The canonical resolution section is updated at `skills/external-review/SKILL.md:247`, but these stale lines can mislead future spec/plan review retries.

2. Open questions / assumptions

No open questions. I treated the unchecked boxes in the plan as implementation instructions, not a live completion checklist.

3. Suggested document edits

Update the stale guidance lines to say process-failure bypass and resolution-gate refusal apply to round 2+ for any kind, while post-slice/post-phase still use fix subagents.

4. Verification gaps / commands that should be run, if any

Verified:
- `python -m pytest skills/external-review/tests -q` -> `297 passed`
- `tasktool artifact status P9.S1 --strict` -> `artifact status: ok`
- `tasktool validate` -> `ok`

Must rerun after fixing F1:
- `git diff --check main..HEAD`
- optionally `python -m pytest skills/external-review/tests/test_resolution_gate.py -q`

Overall verdict: revise

```

### docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/r1-merged-findings.md

```
# Merged findings for r1

## Primary

# Review — 2026-06-06-P9.S1-review-pipeline-quick-wins.md (post-slice, round 1)

- Target: `docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md`
- Request: `docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/r1-2026-06-07T0045-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

No findings. The S1 implementation matches the plan/spec scope, and the P9.S1-scoped artifact check is clean.

2. Open questions / assumptions

Assumption: the unchecked boxes in `docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md` are treated as implementation instructions, not a live completion checklist. Actual completion evidence is in commits, tests, tracker state, and repo behavior.

3. Suggested document edits

None required for this gate.

4. Verification gaps / commands that should be run, if any

Verified:
- `python -m pytest skills/external-review/tests -q` → `297 passed`
- `git diff --check` → clean
- `tasktool validate` → `ok`
- `tasktool artifact status P9.S1 --strict` → `artifact status: ok`
- CLI smoke checks for `--review-depth`, `--model`, and `stats --since` help text passed
- Behavioral smoke for depth/model helpers printed `OK`

Residual non-blocking repo issue: unscoped `tasktool artifact status --strict` fails on unrelated X29 artifact refs, not P9.S1.

Overall verdict: ready


## Sweep 1

# Review — 2026-06-06-P9.S1-review-pipeline-quick-wins.md (post-slice, round 1)

- Target: `docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md`
- Request: `docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice/r1-2026-06-07T0045-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

S1.F1. Severity: blocking — `git diff --check main..HEAD` fails on a committed whitespace error: `skills/external-review/tests/test_resolution_gate.py:55: new blank line at EOF.` This contradicts the claimed clean verification and leaves a standard completion gate failing, even though the pytest suite passes.

S1.F2. Severity: minor — Some guidance still describes the resolution bypass/gate as post-slice/post-phase-specific after the implementation made it kind-independent. See `skills/external-review/SKILL.md:132` and `skills/subagent-driven-development/SKILL.md:331`. The canonical resolution section is updated at `skills/external-review/SKILL.md:247`, but these stale lines can mislead future spec/plan review retries.

2. Open questions / assumptions

No open questions. I treated the unchecked boxes in the plan as implementation instructions, not a live completion checklist.

3. Suggested document edits

Update the stale guidance lines to say process-failure bypass and resolution-gate refusal apply to round 2+ for any kind, while post-slice/post-phase still use fix subagents.

4. Verification gaps / commands that should be run, if any

Verified:
- `python -m pytest skills/external-review/tests -q` -> `297 passed`
- `tasktool artifact status P9.S1 --strict` -> `artifact status: ok`
- `tasktool validate` -> `ok`

Must rerun after fixing S1.F1:
- `git diff --check main..HEAD`
- optionally `python -m pytest skills/external-review/tests/test_resolution_gate.py -q`

Overall verdict: revise


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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p9-s1-quick-wins-kind-aware-depth-defaults

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md

Additional context files:
- docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md
- /tmp/p9s1-brief-context.md

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

### docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md

    1	# P9.S1 — Review-Pipeline Quick Wins Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Cut external-review cost by defaulting depth per kind, extending the resolution gate to all kinds, tiering reviewer models, trimming context guidance, and adding `stats --since` with a rounds-per-slice metric.
    6	
    7	**Architecture:** All behaviour changes live in `skills/external-review/scripts/external-reviewer.py` (CLI) and `skills/project-setup/scripts/reviewer-agent` (provider wrapper); guidance changes live in four SKILL.md files. Every CLI change is opt-out-preserving: explicit flags and unset env vars reproduce today's behaviour byte-for-byte.
    8	
    9	**Tech Stack:** Python 3 (stdlib only), bash, pytest (`skills/external-review/tests/`).
   10	
   11	**Spec:** `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md` (S1 section).
   12	
   13	**Scheduling:** `P9.S1` is ratified, has no `depends_on`, and gates `P9.S2`/`P9.S3` (both depend on it; S3 also depends on S2). Declared integration surfaces: `skills/external-review/scripts/external-reviewer.py`, `skills/external-review/SKILL.md`, `skills/project-setup/scripts/reviewer-agent`. No sibling slice may run in parallel with this one (`tasktool surface check P9` is clean because S2/S3 are serialized behind S1).
   14	
   15	---
   16	
   17	## Conventions used by every task
   18	
   19	- Repo root: `/home/simon/Dev/sigreer/skills/superstar` (work from an isolated worktree created via `superstar:using-git-worktrees`).
   20	- The module under test is loaded the way every existing test does it:
   21	
   22	```python
   23	from pathlib import Path
   24	import sys, importlib.util
   25	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
   26	sys.path.insert(0, str(SCRIPTS))
   27	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
   28	er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
   29	```
   30	
   31	- Test command: `python -m pytest skills/external-review/tests/<file> -q` from the repo root.
   32	- Line numbers below are anchors as of commit `b9babcf`; re-locate with the given grep if drifted.
   33	
   34	### Task 0: Start the slice
   35	
   36	- [ ] **Step 1: Mark the slice started**
   37	
   38	Run: `tasktool start P9.S1`
   39	Expected: exit 0; `tasktool show P9.S1` shows status `started`.
   40	
   41	---
   42	
   43	### Task 1: Kind-aware depth defaults
   44	
   45	**Files:**
   46	- Modify: `skills/external-review/scripts/external-reviewer.py` (argparse ~line 1851; main review path after the work-id check ~line 2445; round-entry construction — locate with `grep -n '"review_depth":' skills/external-review/scripts/external-reviewer.py`)
   47	- Test: `skills/external-review/tests/test_depth_defaults.py` (create)
   48	
   49	- [ ] **Step 1: Write the failing tests**
   50	
   51	Create `skills/external-review/tests/test_depth_defaults.py`:
   52	
   53	```python
   54	from pathlib import Path
   55	import sys, importlib.util
   56	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
   57	sys.path.insert(0, str(SCRIPTS))
   58	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
   59	er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
   60	
   61	
   62	def test_spec_defaults_standard():
   63	    assert er.resolve_review_depth(None, "spec") == "standard"
   64	
   65	
   66	def test_plan_defaults_standard():
   67	    assert er.resolve_review_depth(None, "plan") == "standard"
   68	
   69	
   70	def test_design_implementation_other_default_standard():
   71	    for kind in ("design", "implementation", "other"):
   72	        assert er.resolve_review_depth(None, kind) == "standard"
   73	
   74	
   75	def test_post_slice_defaults_thorough():
   76	    assert er.resolve_review_depth(None, "post-slice") == "thorough"
   77	
   78	
   79	def test_post_phase_defaults_thorough():
   80	    assert er.resolve_review_depth(None, "post-phase") == "thorough"
   81	
   82	
   83	def test_explicit_flag_wins_over_kind_default():
   84	    assert er.resolve_review_depth("exhaustive", "spec") == "exhaustive"
   85	    assert er.resolve_review_depth("standard", "post-slice") == "standard"
   86	
   87	
   88	def test_argparse_review_depth_default_is_none():
   89	    args = er.parse_args([
   90	        "review", "--kind", "spec", "--file", "x.md",
   91	    ])
   92	    assert args.review_depth is None
   93	```
   94	
   95	- [ ] **Step 2: Run tests to verify they fail**
   96	
   97	Run: `python -m pytest skills/external-review/tests/test_depth_defaults.py -q`
   98	Expected: FAIL — `AttributeError: ... has no attribute 'resolve_review_depth'`.
   99	
  100	- [ ] **Step 3: Implement the resolver and rewire the default**
  101	
  102	In `external-reviewer.py`, directly below the `DEPTH_DEFAULTS` dict (~line 1744), add:
  103	
  104	```python
  105	# Kind-aware depth defaults (P9.S1): post gates get sweeps by default,
  106	# planning gates stay cheap. Explicit --review-depth always wins.
  107	KIND_DEPTH_DEFAULTS = {
  108	    "post-slice": "thorough",
  109	    "post-phase": "thorough",
  110	}
  111	
  112	
  113	def resolve_review_depth(explicit: str | None, kind: str) -> str:
  114	    if explicit is not None:
  115	        return explicit
  116	    return KIND_DEPTH_DEFAULTS.get(kind, "standard")
  117	```
  118	
  119	Change the argparse line (~1851) from:
  120	
  121	```python
  122	    sp_review.add_argument("--review-depth", choices=["standard", "thorough", "exhaustive"],
  123	                        default="standard")
  124	```
  125	
  126	to:
  127	
  128	```python
  129	    sp_review.add_argument("--review-depth", choices=["standard", "thorough", "exhaustive"],
  130	                        default=None,
  131	                        help="Default: 'thorough' for post-slice/post-phase, 'standard' otherwise.")
  132	```
  133	
  134	In the review path of `main`, immediately after the `--work-id` requirement check (locate with `grep -n 'work-id is required' skills/external-review/scripts/external-reviewer.py`, ~line 2439-2445), add:
  135	
  136	```python
  137	    args.review_depth = resolve_review_depth(args.review_depth, args.kind)
  138	```
  139	
  140	Every downstream use (`plan_sweeps(depth=args.review_depth, ...)` twice, and the JSON emit `"review_depth": args.review_depth`) then sees the resolved value — verify with `grep -n 'args.review_depth' skills/external-review/scripts/external-reviewer.py` that all uses are after the resolution line.
  141	
  142	- [ ] **Step 4: Record `depth_resolved` in the chain manifest**
  143	
  144	Locate the round-entry dict construction (`grep -n '"diff_included"' skills/external-review/scripts/external-reviewer.py` — the dict that is appended to `manifest["rounds"]`). Add one key alongside the existing metadata keys:
  145	
  146	```python
  147	        "depth_resolved": args.review_depth,
  148	```
  149	
  150	- [ ] **Step 5: Add a manifest assertion to the test file**

[truncated: 929 additional lines]

<!-- superstar-prompt:end -->