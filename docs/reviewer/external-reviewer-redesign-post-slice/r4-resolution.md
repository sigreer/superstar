# Round 4 resolution — Slice 1 post-slice review (slice-closing)

- Verdict: `ready with small edits`
- Target: `docs/superstar/plans/2026-05-13-external-reviewer-redesign.md`
- Response: `docs/reviewer/external-reviewer-redesign-post-slice/r4-2026-05-14T0141-response.md`
- Status: **closes the Slice 1 post-slice review gate.** No further round required.

## Findings & resolution

### F1 (Important) — Slice 1 closeout evidence stale

Round 4 reviewer noted the closeout note in the plan only listed round 1 / round 2 fix commits and reported `21 passed`, missing the round-3 fix commits (`5cbb0fb`, `6bc9289`, `062dccb`, `a8e6127`) and the current `23 passed` test count.

**Fix:** Updated `docs/superstar/plans/2026-05-13-external-reviewer-redesign.md` around line 2995 to list all post-review fix commits (round 1 / round 2 / round 3 / round 4) and update the test count to `23 passed`. Added a note that round 4 returned `ready with small edits`, closing the gate.

### F2 (Important) — Spec describes findings as heading/bullet only

Round 4 reviewer noted the design spec at lines 312–316 only documented `^##\s+F\d+\b` (heading) and bullet forms, while the parser at `skills/external-review/scripts/external-reviewer.py:503` also accepts prose-style `F<n>. <severity>: ...` findings (added in round-2 / round-3 parser work and covered by `test_findings.py`).

**Fix:** Rewrote the "Finding-count parsing" section in `docs/superstar/specs/2026-05-13-external-reviewer-redesign-design.md` to document all three accepted styles (prose, heading, bullet), the prose > heading > bullet precedence rule, severity derivation, ID-based de-duplication, and the "no findings" sentinel — matching the live `parse_findings` / `_collect_findings` behaviour.

## Verification

- `python3 -m pytest skills/external-review/tests/` → `23 passed` (unchanged; this round was doc-only).
- No code changes.

## Commit

This resolution and the two doc edits, plus the round-4 chain artefacts (`r4-*-request.md`, `r4-*-response.md`, `chain.json` round-4 entry), are committed together in a single commit titled `external-review: S1 closeout edits + commit r4 chain artefacts`.
