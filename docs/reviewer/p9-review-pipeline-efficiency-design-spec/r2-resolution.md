# Resolution for r2

## F3
Status: fixed
Evidence:
- Files: `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md`
  (S1.e, acceptance criteria 6 and 7)
- Verification: S1.e now requires the review-invoking skill texts
  (`brainstorming`, `writing-plans`) to pass `--work-id <slice-id>` on
  slice-level spec and plan reviews whenever a tasktool row exists, so all
  three gates of a slice correlate by `work_id`. Uncorrelated in-window
  spec/plan chains flag the metric via `per_slice_complete: false` with a
  warning that early-gate rounds may be undercounted — the ≤ 4.5 figure is
  explicitly not claimable from an incomplete window. Acceptance criterion 6
  adds the suggested fixture (three chains sharing a work_id → numerator
  includes all three kinds' rounds; missing spec-chain work_id →
  `per_slice_complete: false` + uncorrelated listing). Criterion 7 adds the
  `--work-id` skill-text requirement.

Notes:
Open question answered: require `--work-id` on slice-level spec/plan
invocations (the simpler option matching the existing manifest field), rather
than inferring correlation from tasklist artifact paths.
