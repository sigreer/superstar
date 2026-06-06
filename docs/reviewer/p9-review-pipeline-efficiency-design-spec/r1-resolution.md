# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md` (S1.d)
- Verification: S1.d now contains an explicit invocation matrix (kind × role ×
  round) replacing the "pre-run state is final-ready" phrasing; acceptance
  criterion 3 enumerates the five invocation classes the matrix must cover.

Notes:
Open question answered in-spec: follow-up primaries keep their kind's tier
(spec/plan stay LIGHT on all rounds). The light-model-issues-decisive-ready
trade-off is now stated explicitly as the accepted cost posture, with the
post-slice gate as the canary.

## F2
Status: fixed
Evidence:
- Files: `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md` (S3.b)
- Verification: `--combined-gate` is now `--combined-gate <spec-path>` — the
  spec path is the flag's explicit argument, must exist (exit 2), is
  auto-added to context, and is only valid with `--kind plan`. The spec path
  is stamped into `chain.json` alongside `combined_gate: true`. Acceptance
  criterion 5 updated to match.

## F3
Status: fixed
Evidence:
- Files: `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md`
  (S1.e, acceptance criterion 6, measurement plan)
- Verification: S1.e now defines the rounds-per-slice metric: denominator =
  distinct slice work-ids whose post-slice chain's latest in-window round has
  a passing merged verdict; numerator = all rounds (incl. sweeps) across those
  work-ids' spec/plan/post-slice chains; uncorrelated chains listed, not
  dropped. UTC date parsing pinned (date-only = midnight UTC). Measurement
  plan references this metric as the source of the ≤ 4.5 figure.

## F4
Status: fixed
Evidence:
- Files: `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md`
  (S2.a check 3, Risks)
- Verification: path check now has explicit exemptions (fenced code blocks,
  placeholder/glob characters `<>*{}$…`, `docs/reviewer/` future artifacts)
  and a severity split: dangling markdown links fail, dangling backtick paths
  warn. Risks section references these rules instead of "tuned heuristic".

Notes:
Remaining open question from r1 (combined gate scope) also resolved in-spec:
S3.a now states the combined gate is slice-level only; phase-level specs
always get a standalone review.
