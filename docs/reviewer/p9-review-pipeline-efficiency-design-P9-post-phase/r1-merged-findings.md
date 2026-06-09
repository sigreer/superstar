# Merged findings for r1

## Primary

# Review — 2026-06-06-P9-review-pipeline-efficiency-design.md (post-phase, round 1)

- Target: `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md`
- Request: `docs/reviewer/p9-review-pipeline-efficiency-design-P9-post-phase/r1-2026-06-09T2310-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1. Severity: blocking. The closeout evidence does not justify the phase’s stated success metric. The phase goal is `≤ 4.5` rounds/slice ([spec](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:40>)), and the measurement plan says success is judged by `external-reviewer stats --since <ship-date>` over a representative window ([spec](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:270>)). The current repo evidence from `python skills/external-review/scripts/external-reviewer.py stats --since 2026-06-07 --json` is `slices=3`, `rounds=18`, `rounds/slice=6.0`, `per_slice_complete=true`, with `combined=0c/0r`. That may be too small to be the representative ≥10-slice trial, but the closeout document does not say the metric is deferred or explain why the phase is ready despite the current window missing the target.

F2. Severity: important. Completed P9 slices still carry stale transient review/workflow state. P9.S1, P9.S2, and P9.S3 are `status: done`, but each still has `review_active: true`, `review_stage: passed`, and `workflow_step: implement` ([tasklist](</home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:354>), [tasklist](</home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:390>), [tasklist](</home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:426>)). The tracker guidance says `workflow_step` tracks through `done` and that transient review blocks clear when review finishes ([tasklist-discipline](</home/simon/Dev/sigreer/skills/superstar/skills/tasklist-discipline/SKILL.md:154>), [tasklist-discipline](</home/simon/Dev/sigreer/skills/superstar/skills/tasklist-discipline/SKILL.md:180>)). This is not blocking code behavior, but it is closeout drift and will mislead `tasktool brief`/status consumers.

F3. Severity: minor. The phase spec still says `Status: draft` while the phase is being presented for post-phase closeout ([spec](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:4>)). That stale header should be updated or explicitly treated as historical.

2. Open questions / assumptions

I assume `tasktool archive-phase P9` is intended to run only after this post-phase review returns ready; therefore I am not treating the missing `docs/archived-tasks/P9-...md` archive note as a finding by itself.

3. Suggested document edits

Add a closeout/evidence section to the P9 spec or a dedicated phase-close note that records: shipped slice verdicts, test command output, `stats --since` output, and whether the ≤4.5 metric is met now or deferred to the ≥10-slice multistore trial with an owner/date.

Clean the P9 tracker fields before archive: clear stale `review_active`/`review_stage`, set completed slice `workflow_step` values consistently, and update the spec status header.

4. Verification gaps / commands that should be run, if any

Ran: `python -m pytest skills/external-review/tests tools/tasktool/tests/test_workflow_step_spec_to_plan.py` → 355 passed.

Ran: `tasktool validate` → exit 0, but unrelated X29 missing-ref warnings remain.

Ran: `external-reviewer preflight --kind post-phase --file docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md --context docs/tasklist.json` → 0 failures, 1 warning that `docs/tasklist.json` is oversized; acceptable for archive-drift review only if intentional.

Overall verdict: revise


## Sweep 1

# Review — 2026-06-06-P9-review-pipeline-efficiency-design.md (post-phase, round 1)

- Target: `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md`
- Request: `docs/reviewer/p9-review-pipeline-efficiency-design-P9-post-phase/r1-2026-06-09T2310-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

S1.F1 — Severity: blocking  
`docs/tasklist.json` has closed P9 slices still stored at `workflow_step: "implement"` with stale transient review fields. Examples: P9.S1 is `status: "done"` but still has `review_active: true`, `review_stage: "passed"`, and `workflow_step: "implement"` at `docs/tasklist.json:354-361`; same pattern repeats for P9.S2 at `390-397` and P9.S3 at `426-433`. `tasktool infer-step --all --diff` exits 1 and reports all three should be `done`. This is tracker drift at the phase closeout boundary.

S1.F2 — Severity: blocking  
The phase measurement gate is not evidenced or explicitly deferred. The spec makes measurement a goal at `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:40-45` and calls for a representative multistore trial window of at least 10 slices at `271-277`. The only tracker note is a baseline-like value of `4.59`, not a post-S2/S3 success measurement, at `docs/tasklist.json:328`. A live repo stats run from this checkout gives `slice_count=3`, `rounds_per_slice=6.0`, `combined.chains=0`, so the closeout evidence does not demonstrate the phase goal or explain why the trial is deferred.

S1.F3 — Severity: minor  
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

