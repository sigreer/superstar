# P9 — Review-pipeline efficiency: fewer rounds, cheaper rounds

**Date:** 2026-06-06
**Status:** draft
**Tracker:** P9 (phase)

## Problem

Every slice in a Superstar-driven project pays for three review gates — spec,
plan, post-slice — and each gate usually takes multiple rounds. Measured
baseline from the largest consumer repo (multistore, `external-reviewer stats`,
captured 2026-06-06):

| kind       | rounds | first | follow-up | pass | revise | revise rate |
|------------|--------|-------|-----------|------|--------|-------------|
| spec       | 151    | 66    | 85        | 65   | 51     | 34%         |
| plan       | 172    | 64    | 108       | 62   | 80     | 47%         |
| post-slice | 156    | 69    | 87        | 63   | 73     | 47%         |

That is ~7.3 reviewer rounds per slice (spec 2.3, plan 2.7, post-slice 2.3),
before counting sweep reviewers. A measured round-1 `plan` review at
`--review-depth thorough` (P23.S3 in multistore) consumed ~1.03M total tokens
across primary + sweep (~173k non-cache-read), with both reviewers returning
the same verdict — concordant sweeps on low-risk gates are pure cost.

Two structural observations drive this design:

1. **Round count dominates cost, not round size.** Plan chains average ~1.7
   follow-up rounds. Each `revise` verdict costs a full reviewer run plus a
   local fix cycle. Many revise findings are mechanical (missing acceptance
   gates, dangling file references, placeholder text, tasklist drift) and are
   catchable locally for free.
2. **Redundancy is spent in the wrong place.** Sweeps currently run wherever
   `thorough` is passed, and in practice callers pass `thorough` for spec and
   plan reviews too. The gate where an agent is most likely to have fabricated
   "done" is post-slice; that is where redundancy belongs.

## Goals

- Cut average reviewer rounds per slice from ~7.3 to ≤ 4.5 without weakening
  the post-slice gate.
- Halve spec/plan reviewer invocations (depth defaults + combined gate).
- Catch mechanical revise-class findings locally before the first paid round.
- Make the improvement measurable: `stats --since` comparison against the
  baseline table above.

## Non-goals / out of scope

- No changes to reviewer providers themselves (`codex exec` / `claude --print`
  invocation shape stays, beyond honouring a model override).
- No prompt-template rewrites beyond the combined-gate guidance addition.
- No consumer-repo (multistore) changes; it consumes the updated plugin.
- No changes to the verdict contract, chain folder layout, or merged-verdict
  truth table.

## Design

Three slices, ordered so S1 ships immediately and the trial comparison can
start while S2/S3 land.

### S1 — Quick wins: kind-aware depth defaults, context trimming, resolution gate for all kinds, model tiering, `stats --since`

All changes in `skills/external-review/scripts/external-reviewer.py`,
`skills/external-review/SKILL.md`, `skills/project-setup/scripts/reviewer-agent`,
and the skill texts that invoke reviews (`skills/brainstorming/SKILL.md`,
`skills/writing-plans/SKILL.md`, `skills/subagent-driven-development/SKILL.md`
where they reference review invocation).

**S1.a Kind-aware depth defaults.** `--review-depth` argparse default changes
from `"standard"` to `None` (external-reviewer.py:1851-1852). Resolution order:
explicit flag > kind default. Kind defaults: `spec`/`plan`/`design`/
`implementation`/`other` → `standard`; `post-slice`/`post-phase` → `thorough`.
The resolved depth is recorded per round in `chain.json` (new field
`depth_resolved`) so stats can segment. Skill text examples stop passing
`--review-depth thorough` for spec/plan invocations and document the defaults.
Explicit `--review-depth thorough` on a spec/plan review continues to work
exactly as today (escalation stays one flag away).

**S1.b Context trimming.** Skill text change only: callers pass `tasktool
brief <work-id>` output written to a temp/scratch file (or the phase-filtered
extract) as `--context` instead of the full `docs/tasklist.json`. The
external-review SKILL.md "Context files" section gains a rule: do not pass
files whose bulk is unrelated to the work item; prefer `tasktool brief`.
(Enforcement arrives with S2's preflight size warning.)

**S1.c Resolution gate for all kinds.** The round-N+1 resolution-required gate
(external-reviewer.py:2532-2536) drops its
`args.kind in ("post-slice", "post-phase")` restriction: any kind whose prior
round verdict was `revise` requires `r{N}-resolution.md` before the next round,
with the existing `--allow-missing-resolution` waiver and the existing
process-failure bypass unchanged. Rationale: incremental rounds only converge
fast when the reviewer can verify fixes against a resolution report; spec/plan
chains currently skip this and pay extra rounds re-litigating. SKILL.md
resolution-artifact section updates accordingly. Migration note: existing
chains with a `revise` tail and no resolution file will refuse the next round
until a resolution is written or the waiver is passed — acceptable, the waiver
is the escape hatch.

**S1.d Model tiering.** `reviewer-agent` honours a new optional
`AGENT_REVIEWER_MODEL` env var: `claude --print --model "$AGENT_REVIEWER_MODEL"`
/ `codex exec -m "$AGENT_REVIEWER_MODEL"` when set, no flag when unset.
`external-reviewer.py` sets `AGENT_REVIEWER_MODEL` for each reviewer process
from optional env config, per this exact invocation matrix (every round, not
just round 1 — follow-up primaries keep their kind's tier):

| Reviewer invocation                                   | Model env used               |
|-------------------------------------------------------|------------------------------|
| `spec`/`plan`/`design`/`implementation`/`other` primary, any round | `AGENT_REVIEWER_MODEL_LIGHT` |
| `post-slice`/`post-phase` primary, any round          | `AGENT_REVIEWER_MODEL_STRONG`|
| Any sweep (first-round or final-ready), any kind      | `AGENT_REVIEWER_MODEL_STRONG`|

- The mapped env var being unset → `AGENT_REVIEWER_MODEL` is not exported for
  that invocation; behaviour identical to today. There is no cross-tier
  fallback (LIGHT never substitutes for STRONG or vice versa).
- A per-invocation `--model <name>` flag overrides the matrix for every
  reviewer in that round.
- Accepted trade-off (explicit): at `standard` depth a spec/plan chain's
  decisive `ready` can come from the light model. That is the intended cost
  posture — the post-slice gate (strong model, `thorough`) is the safety net,
  and the measurement plan watches post-slice revise rate as the canary.

The chosen model (or `null`) is recorded in the existing `model` field in
`chain.json` round entries.

**S1.e `stats --since <ISO-date>` + per-slice metric.** `run_stats` gains a
`--since` filter on round `started_at`, so a trial window can be compared
against the historical baseline. Dates are parsed as UTC; a date-only value
means midnight UTC (matching the `utc_now_iso()` timestamps already stored in
`chain.json`). Rounds without timestamps (legacy) are excluded when `--since`
is passed, and the output notes how many were excluded (no silent truncation).

To support the rounds-per-slice goal directly, stats also gains a per-slice
section: chains are grouped by stored `work_id`; the **denominator** is the
count of distinct slice work-ids that have a `post-slice` chain whose latest
round in the window has a passing merged verdict (`ready` / `ready with small
edits`); the **numerator** is all rounds (including sweeps) across the `spec`,
`plan`, and `post-slice` chains of those work-ids. Both numbers and the
resulting rounds-per-slice ratio appear in text and `--json` output.

Correlation requires `work_id` on every gate, so the review-invoking skill
texts (`brainstorming`, `writing-plans`) are updated in this slice to pass
`--work-id <slice-id>` on slice-level `spec` and `plan` reviews whenever a
tasktool row exists (today only `post-slice`/`post-phase` require it; the CLI
already accepts and stores it for all kinds). In-window `spec`/`plan` chains
without a `work_id` are listed as uncorrelated AND flag the ratio: stats
prints/emits `per_slice_complete: false` with a warning that early-gate rounds
may be undercounted, so the ≤ 4.5 figure cannot be claimed from an incomplete
window.

### S2 — Deterministic preflight gate + strengthened self-review checklists

**S2.a `external-reviewer preflight` subcommand.**

```
external-reviewer preflight --kind <kind> --file <target> [--context <path>]...
```

Deterministic checks, no LLM calls:

1. Target exists, non-empty, UTF-8.
2. Placeholder scan: `TBD`, `TODO`, `FIXME`, `XXX`, `???`, `lorem ipsum`
   (case-insensitive, whole-token) outside fenced code blocks.
3. Referenced-path check: markdown links and backtick-quoted strings that look
   like repo-relative paths (heuristic: contain `/` and an extension or are
   under a known docs/src dir) must exist on disk, with explicit exemptions —
   anything inside fenced code blocks, paths containing placeholder or glob
   characters (`<`, `>`, `*`, `{`, `}`, `$`, `…`), and paths under
   `docs/reviewer/` (future/generated artifacts) are skipped. Severity split:
   a dangling **markdown link** is a failure; a dangling **backtick path** is
   a warning (prose often cites paths illustratively). Failures list each
   dangling path.
4. Kind-required sections: `plan` → at least one task list and a
   verification/acceptance-gates section; `spec` → acceptance criteria section;
   `post-slice`/`post-phase` → evidence/verification section in the target.
   Section detection is by heading keyword match, tolerant of phrasing
   (`Verification`, `Acceptance`, `Gates`, `Evidence`).
5. Context hygiene: every `--context` file exists; warn (not fail) when any
   context file exceeds 16KB with a hint to pass `tasktool brief` output
   instead (catches the full-`tasklist.json` habit from S1.b).

Output: human-readable findings list + `--emit json`; exit 0 = pass
(warnings allowed), exit 4 = failures present (distinct from the existing
exit 3 resolution-gate code).

**S2.b Auto-preflight on round 1.** `review` runs the same checks in-process
before submitting a round-1 (broad-mode) review and refuses on failure,
printing the findings. `--no-preflight` skips. Incremental rounds (N+1) skip
auto-preflight — the diff/resolution machinery covers them, and re-running
path checks on an already-reviewed document adds friction without catching the
revise drivers.

**S2.c Self-review checklists.** `brainstorming` (spec self-review section)
and `writing-plans` (plan self-review) skill texts gain a short list of the
top historical revise drivers as explicit checks: vague verification steps
("verify it works" without a command), claims not grounded in the repo
(referenced functions/flags that don't exist), tasklist drift (work-id,
status, or dependency mismatches vs `docs/tasklist.json`), and acceptance
criteria that a reviewer cannot evaluate from the document alone. The
checklist instructs running `external-reviewer preflight` before invoking
external review.

### S3 — Combined spec+plan gate for small slices

**S3.a Eligibility (skill text, `brainstorming` + `writing-plans`).** The
combined gate is for slice-level specs only — phase-level specs (like this
one) always receive a standalone spec review. A slice may use the combined
gate when ALL hold:

- Single-surface change (one tool/skill/app area; no new subsystem).
- No cross-repo or cross-plugin impact.
- Spec fits the existing phase direction (no new product decisions).

When eligible, brainstorming still writes the spec but skips the standalone
spec review; writing-plans proceeds immediately, and the plan review carries
the spec-coverage burden. Ineligible or uncertain → today's two-gate flow.

**S3.b `--combined-gate <spec-path>` flag.** `external-reviewer review --kind
plan --combined-gate <path/to/spec.md>` takes the spec path as its explicit
argument: the file must exist (exit 2 otherwise) and is automatically added to
the context set, so the spec attachment is verifiable rather than inferred
from `--context` (which also carries tracker files). The flag appends to the
plan MODE_GUIDANCE: "This plan's spec did not receive a standalone review.
Also review the attached spec for completeness, internal consistency, and
groundedness; tag spec-level findings distinctly." It is valid only with
`--kind plan` (exit 2 otherwise). `chain.json` records `combined_gate: true`
and the spec path per round so `stats` can segment combined vs standalone
chains.

**S3.c Workflow-step compatibility.** `tasktool set <id> --workflow-step plan`
directly from spec-written state must not be blocked by any step-ordering
validation; verify and adjust tasktool only if it enforces spec-review-passed
as a precondition (current behaviour check is an S3 task, expected no-op).

## Acceptance criteria (phase)

1. Omitting `--review-depth` yields `standard` for spec/plan and `thorough`
   for post-slice/post-phase, with `depth_resolved` recorded in `chain.json`;
   explicit flags override.
2. A spec/plan chain whose prior round was `revise` refuses round N+1 without
   `r{N}-resolution.md` (exit 3), waivable with `--allow-missing-resolution`.
3. With `AGENT_REVIEWER_MODEL_LIGHT`/`_STRONG` set, each reviewer process
   receives the model mapped by the S1.d invocation matrix (covering
   first-round primary, follow-up primary, post-slice/post-phase primary,
   first-round sweep, and final-ready sweep) and `chain.json` records it;
   with neither set, invocation is byte-identical to today.
4. `external-reviewer preflight` catches each check-class in a fixture
   document (placeholder, dangling path, missing section, oversized context)
   and passes a known-good document; `review` auto-runs it on round 1 and
   `--no-preflight` skips.
5. `--combined-gate <spec-path>` injects the spec-coverage guidance, adds the
   spec to context, exits 2 when the path is missing or the kind is not
   `plan`, and stamps `combined_gate` plus the spec path in `chain.json`.
6. `stats --since 2026-06-07 --json` returns only rounds started on/after the
   date (UTC), reports the excluded-legacy count, and emits the per-slice
   section: passing-post-slice work-id denominator, all-rounds numerator,
   rounds-per-slice ratio, the uncorrelated-chain list, and the
   `per_slice_complete` flag. Test fixture: a slice with spec, plan, and
   post-slice chains sharing a `work_id` — the numerator includes all three
   kinds' rounds; a variant with a missing spec-chain `work_id` sets
   `per_slice_complete: false` and lists the chain as uncorrelated.
7. All affected skill texts (external-review, brainstorming, writing-plans,
   subagent-driven-development) reflect the new defaults, trimming rule,
   `--work-id` on slice-level spec/plan reviews, preflight step, and
   combined-gate eligibility.
8. Existing pytest suite in `skills/external-review/tests/` passes; new
   behaviours covered by unit tests added there.

## Measurement plan

- Baseline: the stats table in **Problem** (multistore, captured 2026-06-06).
- Trial: after S1 ships (and again after S2/S3), run normal slice work in
  multistore for a representative window (≥10 slices), then compare
  `external-reviewer stats --since <ship-date>` against baseline.
- Success: rounds/slice ≤ 4.5 as computed by the S1.e per-slice metric
  (passing-post-slice work-ids as denominator); spec+plan reviewer invocations
  (including sweeps) roughly halved; post-slice revise rate not worse than
  baseline 47% (the post-slice gate must not weaken).
- Segment combined-gate chains via the `combined_gate` stamp before drawing
  conclusions.

## Risks

- **Quality regression on spec/plan gates** from losing sweeps and using a
  lighter model. Mitigation: post-slice gate unchanged at `thorough` with the
  strong model; escalation is one explicit flag away; measurement plan watches
  post-slice revise rate as the canary (defects slipping past cheaper early
  gates would surface there).
- **Preflight false positives** (path heuristic flagging prose). Mitigation:
  the S2.a exemption rules (fenced blocks, placeholder/glob characters,
  `docs/reviewer/` paths), the link-vs-backtick severity split, the
  `--no-preflight` escape, and validation of the heuristic against the
  existing corpus of specs/plans in this repo and multistore.
- **Resolution-gate friction on spec/plan chains** mid-migration. Mitigation:
  existing waiver flag; gate only fires when the prior verdict was `revise`.
- **Version skew**: shims hard-fail on VERSION drift, so S1's CLI changes ship
  with a version bump and `install.sh` re-run per the release process.
