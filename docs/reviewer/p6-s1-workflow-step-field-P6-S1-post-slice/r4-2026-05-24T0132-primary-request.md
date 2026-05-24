<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 4 of p6-s1-workflow-step-field-P6-S1-post-slice.

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
| 1 | None | 0 | 0 |
| 2 | revise | 1 | 1 |
| 3 | None | 0 | 0 |

## Prior-round findings

Source: primary reviewer response from r2


Note: round 3 was a process failure, rate-limited, or pre-S1 entry; skipped.
# Review — 2026-05-23-P6.S1-workflow-step-field.md (post-slice, round 2)

- Target: `docs/plans/2026-05-23-P6.S1-workflow-step-field.md`
- Request: `docs/reviewer/p6-s1-workflow-step-field-P6-S1-post-slice/r2-2026-05-24T0108-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: blocking  
`infer-step` does not implement the slice inference contract from the reviewed spec. The spec says a slice with `phase.spec_path` absent must infer `spec` regardless of `slice.plan_path` (`docs/specs/2026-05-23-P6-programmatic-workflow-enhancements-design.md:102-108`). The plan’s implementation snippet also includes `has_phase_spec` and returns `spec` when it is absent (`docs/plans/2026-05-23-P6.S1-workflow-step-field.md:942-950`). The committed code ignores `phase.spec_path` and infers from `slice.plan_path` alone (`tools/tasktool/commands.py:2352-2368`). I reproduced the mismatch with a project containing no phase spec and a ratified slice plan; `commands.infer_step_for_id(..., "P6.S1")` returned `{'step': 'implement', 'blocked': False}`. The tasklist note explicitly records this as an intentional deviation (`docs/tasklist.json:316`), so this needs either a code/test fix to honor the spec or a reviewed spec/plan amendment before the slice can pass.

2. Open questions / assumptions

I’m treating the spec as authoritative over the internally contradictory plan tests because this is a post-slice gate against the accepted design. If the desired product behavior is actually “slice plan implies past spec even when the phase has no spec,” update the spec and acceptance criteria explicitly.

3. Suggested document edits

Add a resolution note to the plan or tasklist after fixing F1, including the exact inference rule chosen and the regression test added. If the implementation keeps the current behavior, amend `docs/specs/2026-05-23-P6-programmatic-workflow-enhancements-design.md:102-108` and the plan snippet at `docs/plans/2026-05-23-P6.S1-workflow-step-field.md:942-950` so future agents do not inherit two different contracts.

4. Verification gaps / commands that should be run

I ran:

`python -m pytest tools/tasktool/tests/test_model.py tools/tasktool/tests/test_serialize.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_render.py tools/tasktool/tests/test_brief.py tools/tasktool/tests/test_schema_gen.py tools/tasktool/tests/test_cli_integration.py tools/tasktool/tests/test_v1_compat.py skills/external-review/tests/test_workflow_block_calls.py -q`  
Result: `201 passed`, with one `.pytest_cache` read-only warning.

`tools/tasktool/tasktool validate`  
Result: `ok`.

`tools/tasktool/tasktool infer-step P6.S1 --format json`, `tools/tasktool/tasktool infer-step P6 --format json`, and `tools/tasktool/tasktool infer-step --all --diff --format json`  
Result: no drift, but that does not cover the missing-phase-spec edge case in F1.

Add/run a regression test for: phase has no `spec_path`, slice has `plan_path`, slice planning status is `ratified`; expected result must match the resolved contract.

Overall verdict: revise


## Resolution report for prior round

MISSING — please verify whether changes occurred.

## Changes since prior round

Worktree status: dirty

### git diff base..HEAD



### git diff HEAD (uncommitted)

diff --git a/docs/reviewer/p6-s1-workflow-step-field-P6-S1-post-slice/chain.json b/docs/reviewer/p6-s1-workflow-step-field-P6-S1-post-slice/chain.json
index d46d842..40187cd 100644
--- a/docs/reviewer/p6-s1-workflow-step-field-P6-S1-post-slice/chain.json
+++ b/docs/reviewer/p6-s1-workflow-step-field-P6-S1-post-slice/chain.json
@@ -189,6 +189,81 @@
       "base_ref": "c0c5c098875954bbba3a86485457da9ace43fdfc",
       "base_ref_source": "auto",
       "diff_included": true
+    },
+    {
+      "round": 3,
+      "reviewers": [
+        {
+          "role": "primary",
+          "sweep_group": null,
+          "parent_round": 3,
+          "request": "r3-2026-05-24T0131-request.md",
+          "response": "r3-2026-05-24T0131-response.md",
+          "verdict": null,
+          "verdict_valid": false,
+          "returncode": 1,
+          "status": "failed",
+          "provider": "codex",
+          "caller_provider": "claude",
+          "model": null,
+          "sandbox": {
+            "repo_root": "/home/simon/Dev/sigreer/skills/superstar",
+            "scratch_dir": "/tmp/superstar-reviewer-p6-s1-workflow-step-field-P6-S1-post-slice-r3-primary-25o7abk3",
+            "response_dir": "docs/reviewer/p6-s1-workflow-step-field-P6-S1-post-slice/.reviewer-output/r3-primary",
+            "mode": "workspace-write-with-read-access"
+          },
+          "started_at": "2026-05-24T00:31:56.621Z",
+          "finished_at": "2026-05-24T00:31:56.625Z",
+          "duration_ms": 3,
+          "estimated_usage": {
+            "formula": "ceil(chars / 4)",
+            "prompt_chars": 173779,
+            "response_chars": 654,
+            "estimated_input_tokens": 43445,
+            "estimated_output_tokens": 164,
+            "estimated_total_tokens": 43609
+          },
+          "exact_usage": null,
+          "usage_capture_status": "estimated_only",
+          "usage_capture_error": null
+        }
+      ],
+      "status": "failed",
+      "returncode": 1,
+      "started_at": "2026-05-24T00:31:56.621Z",
+      "finished_at": "2026-05-24T00:31:56.625Z",
+      "duration_ms": 3,
+      "provider": "codex",
+      "caller_provider": "claude",
+      "model": null,
+      "estimated_usage": {
+        "formula": "ceil(chars / 4)",
+        "prompt_chars": 173779,
+        "response_chars": 654,
+        "estimated_input_tokens": 43445,
+        "estimated_output_tokens": 164,
+        "estimated_total_tokens": 43609
+      },
+      "exact_usage": null,
+      "usage_capture_status": "estimated_only",
+      "usage_capture_error": null,
+      "merged_verdict": null,
+      "merged_findings": null,
+      "request": "r3-2026-05-24T0131-request.md",
+      "response": "r3-2026-05-24T0131-response.md",
+      "resolution": "r2-resolution.md",
+      "resolution_parse_status": "ok",
+      "resolution_waiver": false,
+      "head_sha_at_request": "2f2cc179eed9f107076eec2c385a2292b78e15d2",
+      "head_sha_after_round": "2f2cc179eed9f107076eec2c385a2292b78e15d2",
+      "worktree_dirty_at_request": false,
+      "verdict": null,
+      "verdict_valid": false,
+      "findings_count": 0,
+      "blocking_findings_count": 0,
+      "base_ref": "c0c5c098875954bbba3a86485457da9ace43fdfc",
+      "base_ref_source": "auto",
+      "diff_included": true
     }
   ],
   "sweep_checkpoints": {


### Untracked files

### docs/reviewer/p6-s1-workflow-step-field-P6-S1-post-slice/r3-2026-05-24T0131-request.md

```
<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 3 of p6-s1-workflow-step-field-P6-S1-post-slice.

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
| 1 | None | 0 | 0 |
| 2 | revise | 1 | 1 |

## Prior-round findings

Source: primary reviewer response from r2

# Review — 2026-05-23-P6.S1-workflow-step-field.md (post-slice, round 2)

- Target: `docs/plans/2026-05-23-P6.S1-workflow-step-field.md`
- Request: `docs/reviewer/p6-s1-workflow-step-field-P6-S1-post-slice/r2-2026-05-24T0108-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: blocking  
`infer-step` does not implement the slice inference contract from the reviewed spec. The spec says a slice with `phase.spec_path` absent must infer `spec` regardless of `slice.plan_path` (`docs/specs/2026-05-23-P6-programmatic-workflow-enhancements-design.md:102-108`). The plan’s implementation snippet also includes `has_phase_spec` and returns `spec` when it is absent (`docs/plans/2026-05-23-P6.S1-workflow-step-field.md:942-950`). The committed code ignores `phase.spec_path` and infers from `slice.plan_path` alone (`tools/tasktool/commands.py:2352-2368`). I reproduced the mismatch with a project containing no phase spec and a ratified slice plan; `commands.infer_step_for_id(..., "P6.S1")` returned `{'step': 'implement', 'blocked': False}`. The tasklist note explicitly records this as an intentional deviation (`docs/tasklist.json:316`), so this needs either a code/test fix to honor the spec or a reviewed spec/plan amendment before the slice can pass.

2. Open questions / assumptions

I’m treating the spec as authoritative over the internally contradictory plan tests because this is a post-slice gate against the accepted design. If the desired product behavior is actually “slice plan implies past spec even when the phase has no spec,” update the spec and acceptance criteria explicitly.

3. Suggested document edits

Add a resolution note to the plan or tasklist after fixing F1, including the exact inference rule chosen and the regression test added. If the implementation keeps the current behavior, amend `docs/specs/2026-05-23-P6-programmatic-workflow-enhancements-design.md:102-108` and the plan snippet at `docs/plans/2026-05-23-P6.S1-workflow-step-field.md:942-950` so future agents do not inherit two different contracts.

4. Verification gaps / commands that should be run

I ran:

`python -m pytest tools/tasktool/tests/test_model.py tools/tasktool/tests/test_serialize.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_render.py tools/tasktool/tests/test_brief.py tools/tasktool/tests/test_schema_gen.py tools/tasktool/tests/test_cli_integration.py tools/tasktool/tests/test_v1_compat.py skills/external-review/tests/test_workflow_block_calls.py -q`  
Result: `201 passed`, with one `.pytest_cache` read-only warning.

`tools/tasktool/tasktool validate`  
Result: `ok`.

`tools/tasktool/tasktool infer-step P6.S1 --format json`, `tools/tasktool/tasktool infer-step P6 --format json`, and `tools/tasktool/tasktool infer-step --all --diff --format json`  
Result: no drift, but that does not cover the missing-phase-spec edge case in F1.

Add/run a regression test for: phase has no `spec_path`, slice has `plan_path`, slice planning status is `ratified`; expected result must match the resolved contract.

Overall verdict: revise


## Resolution report for prior round

# Resolution for r2

## F1
Status: fixed
Evidence:
- Commit: cc4256f
- Files: `docs/specs/2026-05-23-P6-programmatic-workflow-enhancements-design.md` §3.3 amended (R3 added); `docs/plans/2026-05-23-P6.S1-workflow-step-field.md` Step 5.3 snippet amended; `tools/tasktool/tests/test_commands.py` adds two regression tests.
- Verification: `cd tools/tasktool && python -m pytest` — full suite green (666 passed).

Notes:
Resolved by amending the spec to match the shipped behavior (option recommended by reviewer; selected by user). `slice.plan_path` is the authoritative signal for moving past spec at the slice level; phase-level inference still consults `phase.spec_path`. Plan tests were already correct; spec §3.3 was over-precise. Two regression tests pin the contract for "no phase.spec_path + ratified slice plan ⇒ implement" and the proposed/plan variant.


## Changes since prior round

Worktree status: clean

### git diff base..HEAD

diff --git a/.agents/plugins/marketplace.json b/.agents/plugins/marketplace.json
index 93bfd72..0b0bf4f 100644
--- a/.agents/plugins/marketplace.json
+++ b/.agents/plugins/marketplace.json
@@ -6,7 +6,7 @@
   "plugins": [
     {
       "name": "superstar",
-      "version": "6.7.0",
+      "version": "6.8.0",
       "source": {
         "source": "local",
         "path": "./plugins/superstar"
diff --git a/.claude-plugin/marketplace.json b/.claude-plugin/marketplace.json
index 608e61f..80662ff 100644
--- a/.claude-plugin/marketplace.json
+++ b/.claude-plugin/marketplace.json
@@ -9,7 +9,7 @@
     {
       "name": "superstar",
       "description": "Core skills library for Claude Code: TDD, debugging, collaboration patterns, and proven techniques",
-      "version": "6.7.0",
+      "version": "6.8.0",
       "source": "./",
       "author": {
         "name": "Simon Greer",
diff --git a/.claude-plugin/plugin.json b/.claude-plugin/plugin.json
index 5843be7..bf21bfa 100644
--- a/.claude-plugin/plugin.json
+++ b/.claude-plugin/plugin.json
@@ -1,7 +1,7 @@
 {
   "name": "superstar",
   "description": "Core skills library for Claude Code: TDD, debugging, collaboration patterns, and proven techniques",
-  "version": "6.7.0",
+  "version": "6.8.0",
   "author": {
     "name": "Simon Greer",
     "email": "simon@sidewayssystems.co.uk"
diff --git a/.codex-plugin/plugin.json b/.codex-plugin/plugin.json
index 589b7f8..d9ec2c2 100644
--- a/.codex-plugin/plugin.json
+++ b/.codex-plugin/plugin.json
@@ -1,6 +1,6 @@
 {
   "name": "superstar",
-  "version": "6.7.0",
+  "version": "6.8.0",
   "description": "An agentic skills framework & software development methodology that works: planning, TDD, debugging, and collaboration workflows.",
   "author": {
     "name": "Simon Greer",
diff --git a/.cursor-plugin/plugin.json b/.cursor-plugin/plugin.json
index f5892d3..9658a53 100644
--- a/.cursor-plugin/plugin.json
+++ b/.cursor-plugin/plugin.json
@@ -2,7 +2,7 @@
   "name": "superstar",
   "displayName": "Superstar",
   "description": "Core skills library: TDD, debugging, collaboration patterns, and proven techniques",
-  "version": "6.7.0",
+  "version": "6.8.0",
   "author": {
     "name": "Simon Greer",
     "email": "simon@sidewayssystems.co.uk"
diff --git a/VERSION b/VERSION
index f0e13c5..e029aa9 100644
--- a/VERSION
+++ b/VERSION
@@ -1 +1 @@
-6.7.0
+6.8.0
diff --git a/docs/archived-tasks/X22-add-cancelled-terminal-status-to-tasktoo.md b/docs/archived-tasks/X22-add-cancelled-terminal-status-to-tasktoo.md
new file mode 100644
index 0000000..dc31212
--- /dev/null
+++ b/docs/archived-tasks/X22-add-cancelled-terminal-status-to-tasktoo.md
@@ -0,0 +1,45 @@
+# X22 - Add cancelled terminal status to tasktool
+
+status: done
+created: 2026-05-23
+started: 2026-05-23
+closed: 2026-05-24
+
+## References
+
+- docs/specs/2026-05-23-X22-cancelled-status-design.md
+- docs/reviewer/x22-cancelled-status-design-spec
+- docs/plans/2026-05-23-X22-cancelled-status.md
+- docs/handoffs/2026-05-23-X22-cancelled-status-prompt.md
+- docs/reviewer/x22-cancelled-status-plan
+
+## Notes
+
+cancelled status shipped
+
+## Full cross-cutting JSON (for tasktool unarchive)
+
+```json
+{
+  "closed": "2026-05-24",
+  "created": "2026-05-23",
+  "id": "X22",
+  "notes": "cancelled status shipped",
+  "refs": [
+    "docs/specs/2026-05-23-X22-cancelled-status-design.md",
+    "docs/reviewer/x22-cancelled-status-design-spec",
+    "docs/plans/2026-05-23-X22-cancelled-status.md",
+    "docs/handoffs/2026-05-23-X22-cancelled-status-prompt.md",
+    "docs/reviewer/x22-cancelled-status-plan"
+  ],
+  "started": "2026-05-23",
+  "status": "done",
+  "title": "Add cancelled terminal status to tasktool",
[truncated: 1565 additional lines]
```

### docs/reviewer/p6-s1-workflow-step-field-P6-S1-post-slice/r3-2026-05-24T0131-response.md

```
# Review — 2026-05-23-P6.S1-workflow-step-field.md (post-slice, round 3)

- Target: `docs/plans/2026-05-23-P6.S1-workflow-step-field.md`
- Request: `docs/reviewer/p6-s1-workflow-step-field-P6-S1-post-slice/r3-2026-05-24T0131-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `failed (1)`

---

_Reviewer process failed; no stdout persisted._

---

## Reviewer stderr (tail, sanitised)

```text
ERROR: reviewer-agent shim is 6.7.0 but Superstar source is 6.8.0
Re-run: bash /home/simon/Dev/sigreer/skills/superstar/skills/project-setup/install-reviewer-agent.sh
```

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
docs/plans/2026-05-23-P6.S1-workflow-step-field.md

Additional context files:
- docs/specs/2026-05-23-P6-programmatic-workflow-enhancements-design.md
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

### docs/plans/2026-05-23-P6.S1-workflow-step-field.md

    1	# P6.S1 — `workflow_step` field + transient review block + read-only `infer-step`
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Add `workflow_step` as a first-class field on `Slice` and `Phase`, add a transient review block on `Slice` written by external-reviewer, and ship a read-only `tasktool infer-step` command — without changing any existing transition behaviour.
    6	
    7	**Architecture:** Strictly additive. Three new enums and four new fields in `tools/tasktool/model.py`; serialiser elides defaults; `tasktool set` gets new flags but stays back-compatible; `tasktool infer-step` is a pure read-only computation over current state; renderers suppress empty review blocks. External-reviewer gains three best-effort `tasktool set` calls when `--work-id` points at a slice. Six skill markdown files get small pointer paragraphs. No migration, no auto-advance, no transition gating.
    8	
    9	**Tech Stack:** Python 3.11+, `dataclasses`, `argparse`, `pytest`. Tasktool layout under `tools/tasktool/`. Skill markdown under `skills/`.
   10	
   11	---
   12	
   13	## Lifecycle pre-flight
   14	
   15	- [ ] **Step 0.1: Confirm working directory is the repo root**
   16	
   17	```bash
   18	test -f docs/tasklist.json -a -d tools/tasktool
   19	```
   20	
   21	Expected: exit 0.
   22	
   23	- [ ] **Step 0.2: Mark the slice started**
   24	
   25	```bash
   26	tools/tasktool/tasktool start P6.S1 --in-place
   27	```
   28	
   29	Expected stdout: `P6.S1`. (`--in-place` because the slice is small and editing in the main checkout is appropriate; the user has historically accepted in-place for tasktool internals.)
   30	
   31	- [ ] **Step 0.3: Ratify scheduling**
   32	
   33	The slice has no dependencies and no parallel-group peers. Confirm:
   34	
   35	```bash
   36	tools/tasktool/tasktool schedule P6
   37	```
   38	
   39	Expected: P6.S1 listed with `deps=-`, `group=-`. Then ratify:
   40	
   41	```bash
   42	tools/tasktool/tasktool ratify P6.S1
   43	```
   44	
   45	Expected: `P6.S1 ratified`.
   46	
   47	---
   48	
   49	## File structure (overview)
   50	
   51	| Path | Change |
   52	|---|---|
   53	| `tools/tasktool/model.py` | Add three enums; add four fields; bump `SCHEMA_VERSION` 1 → 2 |
   54	| `tools/tasktool/serialize.py` | Round-trip enums; elide review-block defaults |
   55	| `tools/tasktool/commands.py` | Relax `cmd_set`; add `cmd_infer_step`; extend `cmd_list` filter; extend `cmd_show` output |
   56	| `tools/tasktool/cli.py` | New args on `set`; new `infer-step` subparser; new `--workflow-step` filter on `list` |
   57	| `tools/tasktool/schema_gen.py` | Add new property entries to the inline phase/slice schemas; bump `SCHEMA_VERSION` const |
   58	| `tools/tasktool/render.py` | Workflow-step column; review-block conditional row |
   59	| `tools/tasktool/brief.py` | Workflow-step in heading; review-block conditional block |
   60	| `tools/tasktool/tests/test_model.py` | Round-trip with new fields |
   61	| `tools/tasktool/tests/test_serialize.py` | Default elision; enum round-trip |
   62	| `tools/tasktool/tests/test_commands.py` | `set` flag validation; `infer-step` (slice + phase + cross) |
   63	| `tools/tasktool/tests/test_render.py` | Review-block suppression |
   64	| `tools/tasktool/tests/test_brief.py` | Workflow-step heading |
   65	| `tools/tasktool/tests/test_schema_gen.py` | New enum types appear in schema |
   66	| `tools/tasktool/tests/test_cli_integration.py` | End-to-end `set` + `infer-step` invocations |
   67	| `tools/tasktool/tests/test_v1_compat.py` | Verify v1 tasklist loads with new fields at defaults; subsequent save emits schema_version: 2 |
   68	| `skills/external-review/scripts/external-reviewer.py` | Three best-effort `tasktool set` calls |
   69	| `skills/external-review/tests/test_workflow_block_calls.py` | Mocked tasktool calls for the three lifecycle moments |
   70	| `skills/tasklist-discipline/SKILL.md` | New `workflow_step` section |
   71	| `skills/brainstorming/SKILL.md` | One-liner pointer |
   72	| `skills/writing-plans/SKILL.md` | One-liner pointer |
   73	| `skills/subagent-driven-development/SKILL.md` | One-liner pointer |
   74	| `skills/executing-plans/SKILL.md` | One-liner pointer |
   75	| `skills/external-review/SKILL.md` | One-liner about the transient block |
   76	
   77	---
   78	
   79	## Task 1: Add enums and fields to the model
   80	
   81	**Files:**
   82	- Modify: `tools/tasktool/model.py`
   83	- Test: `tools/tasktool/tests/test_model.py`
   84	
   85	- [ ] **Step 1.1: Write the failing test**
   86	
   87	Append to `tools/tasktool/tests/test_model.py`:
   88	
   89	```python
   90	from tasktool.model import (
   91	    Slice, Phase, SCHEMA_VERSION,
   92	    SliceWorkflowStep, PhaseWorkflowStep, ReviewStage,
   93	)
   94	
   95	
   96	def test_schema_version_is_2():
   97	    assert SCHEMA_VERSION == 2
   98	
   99	
  100	def test_slice_has_workflow_step_default_none():
  101	    # Slice IDs in the model are short (`S1`); qualification happens at the CLI layer.
  102	    s = Slice(id="S1", title="t", created="2026-05-23")
  103	    assert s.workflow_step is None
  104	    assert s.review_active is False
  105	    assert s.review_stage is None
  106	
  107	
  108	def test_phase_has_workflow_step_default_none():
  109	    p = Phase(id="P6", title="t", created="2026-05-23")
  110	    assert p.workflow_step is None
  111	
  112	
  113	def test_slice_accepts_workflow_step_enum():
  114	    s = Slice(
  115	        id="S1", title="t", created="2026-05-23",
  116	        workflow_step=SliceWorkflowStep.PLAN,
  117	        review_active=True,
  118	        review_stage=ReviewStage.AWAITING_RESPONSE,
  119	    )
  120	    assert s.workflow_step is SliceWorkflowStep.PLAN
  121	    assert s.review_active is True
  122	    assert s.review_stage is ReviewStage.AWAITING_RESPONSE
  123	
  124	
  125	def test_phase_accepts_workflow_step_enum():
  126	    p = Phase(
  127	        id="P6", title="t", created="2026-05-23",
  128	        workflow_step=PhaseWorkflowStep.READY,
  129	    )
  130	    assert p.workflow_step is PhaseWorkflowStep.READY
  131	
  132	
  133	def test_slice_workflow_step_values():
  134	    assert {e.value for e in SliceWorkflowStep} == {"spec", "plan", "implement", "done"}
  135	
  136	
  137	def test_phase_workflow_step_values():
  138	    assert {e.value for e in PhaseWorkflowStep} == {"spec", "ready", "in_progress", "done"}
  139	
  140	
  141	def test_review_stage_values():
  142	    assert {e.value for e in ReviewStage} == {"awaiting_response", "applying_fixes", "passed"}
  143	```
  144	
  145	- [ ] **Step 1.2: Run test to verify it fails**
  146	
  147	```bash
  148	cd tools/tasktool && python -m pytest tests/test_model.py -v 2>&1 | tail -20
  149	```
  150	

[truncated: 1669 additional lines]

<!-- superstar-prompt:end -->