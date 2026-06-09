1. Findings

F1 — Severity: blocking  
`docs/tasklist.json` has closed P9 slices still stored at `workflow_step: "implement"` with stale transient review fields. Examples: P9.S1 is `status: "done"` but still has `review_active: true`, `review_stage: "passed"`, and `workflow_step: "implement"` at `docs/tasklist.json:354-361`; same pattern repeats for P9.S2 at `390-397` and P9.S3 at `426-433`. `tasktool infer-step --all --diff` exits 1 and reports all three should be `done`. This is tracker drift at the phase closeout boundary.

F2 — Severity: blocking  
The phase measurement gate is not evidenced or explicitly deferred. The spec makes measurement a goal at `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:40-45` and calls for a representative multistore trial window of at least 10 slices at `271-277`. The only tracker note is a baseline-like value of `4.59`, not a post-S2/S3 success measurement, at `docs/tasklist.json:328`. A live repo stats run from this checkout gives `slice_count=3`, `rounds_per_slice=6.0`, `combined.chains=0`, so the closeout evidence does not demonstrate the phase goal or explain why the trial is deferred.

F3 — Severity: minor  
P9.S2 and P9.S3 `refs` omit their post-slice reviewer chains even though `reviewer_chain` is set. P9.S2 refs end at the plan reviewer chain at `docs/tasklist.json:383-389`, while the post-slice chain is only in `reviewer_chain` at `392`; P9.S3 has the same shape at `419-428`. The canonical field is present, so this is not a gate failure, but the artifact list is inconsistent with P9.S1 and weakens archive-note completeness.

2. Open questions / assumptions

I assume this review is happening before `tasktool archive-phase P9`, since P9 is still active in `docs/tasklist.json` rather than under `archived_phases`.

3. Suggested document edits

Add a closeout/archive note that separates “implementation accepted” from “representative measurement not yet run,” or attach the actual multistore `stats --since` trial evidence. Also repair the P9.S1-S3 workflow-step drift before archiving.

4. Verification gaps / commands that should be run

Already run:
`python -m pytest skills/external-review/tests -q` -> 354 passed.  
`tasktool validate` -> only pre-existing X29 missing-path warnings.  
`tasktool infer-step --all --diff` -> fails for P9.S1, P9.S2, P9.S3 stored `implement` vs inferred `done`.  
`python skills/external-review/scripts/external-reviewer.py stats --since 2026-06-07 --json` -> per-slice complete, but `rounds_per_slice=6.0` over only 3 slices.

Still needed:
Repair workflow-step drift, rerun `tasktool infer-step --all --diff`, and either run the representative measurement window or document the measurement as explicitly deferred before archive.

Overall verdict: revise

