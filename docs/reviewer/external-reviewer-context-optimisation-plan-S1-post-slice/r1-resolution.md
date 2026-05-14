# Resolution for r1

Two reviewers (primary + sweep1) returned overlapping findings. Where a
sweep finding restates a primary finding verbatim, both stable IDs are
addressed under a single section and cross-referenced.

## F1
Status: fixed
Evidence:
- Commit: 42f71fd ("external-reviewer: zero findings count on failed primary")
- Files: `skills/external-review/scripts/external-reviewer.py:1230-1238` (guard the
  `parse_findings` call on `primary.returncode == 0`; force `(0, 0)` otherwise).
- Tests: `skills/external-review/tests/test_failed_findings_zeroed.py` (new
  regression — failed reviewer whose stderr contains `## F1` /
  `Severity: blocking` must yield `findings_count == 0` and
  `blocking_findings_count == 0` in both emitted JSON and `chain.json`).
- Verification: `python3 -m pytest skills/external-review/tests/test_failed_findings_zeroed.py -v` → `1 passed`.

Notes:
This is the same defect raised in the sweep as `S1.F1` (see below); the
fix below covers both. The implementation already forced
`verdict=None` / `verdict_valid=False` on reviewer failure, but
`parse_findings(primary.review_body)` ran unconditionally a few lines
later, persisting echo-derived counts into both the JSON payload and
the round entry in `chain.json`. The fix gates the parse on a
successful returncode.

## S1.F1
Status: fixed
Evidence:
- Same as F1. Single commit `42f71fd` resolves both reports.

Notes:
Sweep restated the primary finding with identical reproduction and
identical line refs. No additional work required.

## F2
Status: deferred
Evidence:
- Files: `docs/reviewer/external-reviewer-context-optimisation-plan-S1-post-slice/`
  is now complete (contains `chain.json`,
  `r1-2026-05-14T1539-primary-{request,response}.md`,
  `r1-2026-05-14T1539-sweep1-{request,response}.md`,
  `r1-merged-findings.md`) — the partial-folder concern is no longer
  reproducible.
- The untracked status of the chain folder, `docs/reviewer/plan-plan/`,
  and `review-stderr.log` is workspace state that the coordinator
  (not this fix subagent) controls. Per the slice instructions to this
  subagent ("Do not change anything outside scripts/tests/SKILL.md or
  the chain folder"), adding/removing top-level paths is out of scope.

Notes:
Deferred to coordinator for normal post-slice housekeeping
(commit the chain folder, decide on `review-stderr.log` ignore vs.
delete). The actual artifact set inside the chain folder is now
complete, so the finding's substantive concern is resolved.

## S1.F2
Status: deferred
Evidence:
- Same as F2. Both reviewers flagged identical untracked-artifact
  state; resolution is identical.

Notes:
Same triage — coordinator-side housekeeping, not in this subagent's
scope.

## F3
Status: fixed
Evidence:
- Commit: 0611dfd ("external-reviewer: drop stale xfail on r3 size-bound test")
- Files: `skills/external-review/tests/test_failed_r2_bounded_r3.py:84` (removed
  `@pytest.mark.xfail(reason="size guarantee tightens after Slice 2", strict=False)`
  marker; removed now-unused `import pytest`).
- Verification: `python3 -m pytest skills/external-review/tests/ -v` →
  `127 passed, 1 warning` (no XPASS line; the size assertion now passes
  as a regular enforced test).

Notes:
The plan's note that the size guarantee tightens after Slice 2 is
still accurate — Slice 2 may add a stricter assertion at a smaller
bound. Removing the non-strict xfail today simply ensures that the
current 250 KB ceiling cannot regress silently. A future regression
breaks the test loudly instead of being swallowed as expected.

Same defect as sweep finding `S1.F4`.

## S1.F4
Status: fixed
Evidence:
- Same as F3. Single commit `0611dfd` resolves both reports.

## F4
Status: deferred
Evidence:
- The plan document `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md`
  is outside this fix subagent's allowed edit scope (per slice
  instructions: only `external-reviewer.py`, its tests, `SKILL.md`,
  and the chain folder may be edited).
- Coordinator will tick Slice 1 checkboxes and append the Slice 1
  closeout evidence note as part of post-resolution close-out, before
  re-submitting for r2.

Notes:
Same as sweep finding `S1.F3`. The checkbox state is a plan-doc
concern, not a code/test concern; deferred to coordinator.

## S1.F3
Status: deferred
Evidence:
- Same as F4.

Notes:
Coordinator action item.

---

## Verification summary

Final test run after both fixes:

```
python3 -m pytest skills/external-review/tests/ -v
...
127 passed, 1 warning
```

- Baseline before this resolution: `125 passed, 1 xpassed`.
- After: `127 passed` (1 new regression test added; 1 stale xfail
  promoted to a regular pass).
- No new failures. No xfail/xpass remaining in the suite.

## New commits

- `42f71fd` external-reviewer: zero findings count on failed primary
- `0611dfd` external-reviewer: drop stale xfail on r3 size-bound test
- (this resolution doc commit follows)
