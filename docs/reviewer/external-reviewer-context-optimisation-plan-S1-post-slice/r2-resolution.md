# Resolution for r2

## F1
Status: waived
Evidence:
- r2 already marked F1 RESOLVED in its findings list; no action required.
- Verification: see [r2 response](./r2-2026-05-14T1548-response.md) lines 12-13.

Notes:
The r2 reviewer confirmed the F1 fix from r1 (failed primary rounds zero out `findings_count` / `blocking_findings_count`). No regression. The merged verdict landed as `revise` solely because of F3 below — the parsed resolution status itself is `ok`.

## F2
Status: waived
Evidence:
- r2 already marked F2 RESOLVED.
- Verification: see [r2 response](./r2-2026-05-14T1548-response.md) lines 15-16.

Notes:
Stale `xfail` removed in r1; r2 confirmed the test passes normally.

## F3
Status: fixed
Evidence:
- Files removed: `docs/reviewer/plan-plan/chain.json`, `docs/reviewer/plan-plan/r1-2026-05-14T1541-request.md`, `docs/reviewer/plan-plan/r1-2026-05-14T1541-response.md` (entire `docs/reviewer/plan-plan/` directory deleted).
- Verification: `git status --short --untracked-files=all` after cleanup shows only the legitimate r2 review-chain artifacts (`chain.json` update, `r2-*-request.md`, `r2-*-response.md`) which are about to be committed as part of this review round per the standard chain workflow.
- Pytest: `python3 -m pytest skills/external-review/tests/ -q` → `127 passed, 1 warning`.

Notes:
`docs/reviewer/plan-plan/` was confirmed scratch output from an earlier test run against `/tmp/tmp.zfelhBHpAi/plan.md` (visible in the request preamble of `r1-2026-05-14T1541-request.md`). It predated the F1 fix (chain.json mtime 15:41:01; F1 fix commit `42f71fd` landed 15:46), which is exactly why its `findings_count: 1` for a failed round looked like the very bug F1 fixed — it was a fossil from the pre-fix codebase rather than a live regression. Deleted entirely; the directory was never tracked so no `git rm` was required.

The other untracked files flagged by r2 (`r2-*-request.md`, the modified `chain.json`) are the active review-chain artifacts for this very round. They are intentionally committed alongside this resolution (standard external-review hygiene: artifacts land with the round that produced them).

## F4
Status: waived
Evidence:
- r2 already marked F4 RESOLVED.
- Verification: see [r2 response](./r2-2026-05-14T1548-response.md) lines 28-29.

Notes:
Slice 1 checkboxes confirmed ticked in r2.
