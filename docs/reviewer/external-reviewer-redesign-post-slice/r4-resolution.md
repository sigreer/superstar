# Resolution for r4

Round 4 of the Slice 1 post-slice chain. Reviewer returned
`ready with small edits` with 2 findings, closing the Slice 1
post-slice gate. Both findings are addressed below.

- Verdict: `ready with small edits`
- Target: `docs/superstar/plans/2026-05-13-external-reviewer-redesign.md`
- Response: `docs/reviewer/external-reviewer-redesign-post-slice/r4-2026-05-14T0141-response.md`
- Status: closes the Slice 1 post-slice review gate. No further round
  required.

## F1
Status: fixed
Evidence:
- Commit: `a90f7dd` (`external-review: S1 closeout edits + commit r4 chain artefacts`)
- Files: `docs/superstar/plans/2026-05-13-external-reviewer-redesign.md`
  (~line 2995)
- Verification: closeout note now enumerates all post-review fix
  commits (rounds 1–4) and records `23 passed`.

Notes:
Slice 1 closeout evidence stale. Round 4 reviewer noted the closeout
note in the plan only listed round 1 / round 2 fix commits and
reported `21 passed`, missing the round-3 fix commits (`5cbb0fb`,
`6bc9289`, `062dccb`, `a8e6127`) and the current `23 passed` test
count. Updated `docs/superstar/plans/2026-05-13-external-reviewer-redesign.md`
around line 2995 to list all post-review fix commits (round 1 /
round 2 / round 3 / round 4) and update the test count to `23 passed`.
Added a note that round 4 returned `ready with small edits`, closing
the gate.

## F2
Status: fixed
Evidence:
- Commit: `a90f7dd` (bundled with F1)
- Files: `docs/superstar/specs/2026-05-13-external-reviewer-redesign-design.md`
  (lines 312–316 area)
- Verification: design spec now documents all three accepted finding
  styles matching live `parse_findings` behaviour.

Notes:
Spec describes findings as heading/bullet only. Round 4 reviewer noted
the design spec at lines 312–316 only documented `^##\s+F\d+\b`
(heading) and bullet forms, while the parser at
`skills/external-review/scripts/external-reviewer.py:503` also accepts
prose-style `F<n>. <severity>: ...` findings (added in round-2 /
round-3 parser work and covered by `test_findings.py`). Rewrote the
"Finding-count parsing" section in
`docs/superstar/specs/2026-05-13-external-reviewer-redesign-design.md`
to document all three accepted styles (prose, heading, bullet), the
prose > heading > bullet precedence rule, severity derivation,
ID-based de-duplication, and the "no findings" sentinel — matching
the live `parse_findings` / `_collect_findings` behaviour.

## Verification

- `python3 -m pytest skills/external-review/tests/` → `23 passed`
  (unchanged; this round was doc-only).
- No code changes.

## Commit

This resolution and the two doc edits, plus the round-4 chain
artefacts (`r4-*-request.md`, `r4-*-response.md`, `chain.json` round-4
entry), are committed together in a single commit titled
`external-review: S1 closeout edits + commit r4 chain artefacts`
(`a90f7dd`).
