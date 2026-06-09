# P9 — Review-pipeline efficiency: post-phase closeout evidence

**Date:** 2026-06-09
**Phase:** P9 (Review-pipeline efficiency)
**Spec:** [`docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md`](../specs/2026-06-06-P9-review-pipeline-efficiency-design.md)
**Owner:** Simon Greer

This note records the post-phase closeout evidence for P9. It separates
**implementation accepted** (done) from **representative measurement**
(explicitly deferred to the multistore trial as the phase spec designs it).

## Shipped slices + post-slice verdicts

All three slices are `status: done`, merged to `main`, and each passed its
post-slice external review.

| Slice  | Title                                                     | Post-slice verdict (final round)        | Reviewer chain |
|--------|-----------------------------------------------------------|------------------------------------------|----------------|
| P9.S1  | Quick wins (depth defaults, trimming, resolution gate, model tiering, `stats --since` + per-slice metric) | `ready` (r1 ready, r2 ready) | [`docs/reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice`](../reviewer/p9-s1-review-pipeline-quick-wins-P9-S1-post-slice) |
| P9.S2  | Deterministic preflight gate + strengthened self-review checklists | `ready` (r1 revise → r2 ready) | [`docs/reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice`](../reviewer/p9-s2-preflight-gate-self-review-P9-S2-post-slice) |
| P9.S3  | Combined spec+plan gate for small slices                  | `ready with small edits` (r1) | [`docs/reviewer/p9-s3-combined-spec-plan-gate-P9-S3-post-slice`](../reviewer/p9-s3-combined-spec-plan-gate-P9-S3-post-slice) |

## Test evidence

`python -m pytest skills/external-review/tests tools/tasktool/tests -q`
→ **1196 passed, 1 warning** (167s).

Note: when the suite is run with `SUPERSTAR_SUBAGENT_ROLE` exported, the
`tools/tasktool/tests` fixtures that call `tasktool start` are blocked by the
subagent-role guard and report as failures. That is a test-harness artifact of
the role guard, not a defect — run without the env var, the full suite is green
(1196 passed). `skills/external-review/tests` alone is 354 passed and is
unaffected by the role guard.

## Current stats (this repo)

`external-reviewer stats --since 2026-06-07 --json` (post-ship window):

- `per_slice.slice_count`: **3**
- `per_slice.rounds_total`: **18**
- `per_slice.rounds_per_slice`: **6.0**
- `per_slice.per_slice_complete`: `true`
- `per_slice.uncorrelated_chains`: `[]`
- Combined-gate adoption: **0 chains / 0 rounds (0c/0r)** — the stats payload
  emits no `combined_gate` block because no eligible slice has exercised the
  combined spec+plan gate yet in this repo.

## Metric status — DEFERRED

The phase success metric is **≤ 4.5 reviewer rounds/slice** (spec
[Goals](../specs/2026-06-06-P9-review-pipeline-efficiency-design.md), ~line 40),
to be judged by `external-reviewer stats --since <ship-date>` over a
**representative window of ≥ 10 slices in the multistore consumer repo** (spec
[Measurement plan](../specs/2026-06-06-P9-review-pipeline-efficiency-design.md),
~lines 270–277).

**This metric is DEFERRED, not met.** The spec itself designs measurement as
the ≥10-slice multistore trial; the correct closeout position is therefore:

- **Implementation: accepted.** All three slices shipped, passed post-slice
  external review, and the test suite is green (1196 passed).
- **Representative measurement: deferred.** This repo's current post-ship
  window is only **3 slices at 6.0 rounds/slice**, with **combined-gate
  adoption = 0c/0r**. Three slices is below the ≥10-slice representative
  threshold the spec requires, and the combined gate has not yet been
  exercised here (0 adoption), so this window is **not** the representative
  trial and must not be read as the phase verdict on the metric. No passing
  measurement is claimed.

**Deferral record:**

- **Owner:** Simon Greer
- **Trigger:** after ≥ 10 slices ship in the multistore consumer repo.
- **Procedure:** run `external-reviewer stats --since <P9-ship-date>` in
  multistore, compare `rounds_per_slice` against the ≤ 4.5 target and the
  baseline table in the spec's **Problem** section, confirm spec+plan reviewer
  invocations are roughly halved, and confirm the post-slice revise rate is not
  worse than the baseline 47%. Segment combined-gate chains via the
  `combined_gate` stamp before drawing conclusions.
