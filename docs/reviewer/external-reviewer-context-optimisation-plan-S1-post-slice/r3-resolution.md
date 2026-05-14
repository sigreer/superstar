# Resolution for r3

## F1
Status: waived
Evidence:
- Primary marked F1 RESOLVED at [r3 primary response](./r3-2026-05-14T1552-primary-response.md) lines 16-17.
- `parse_findings` only runs on `primary.returncode == 0`; regression coverage in `skills/external-review/tests/test_failed_findings_zeroed.py`.

Notes:
No action required. F1 from prior rounds remains fixed and asserted.

## F2
Status: waived
Evidence:
- Primary marked F2 RESOLVED at [r3 primary response](./r3-2026-05-14T1552-primary-response.md) lines 19-20.
- `skills/external-review/tests/test_failed_r2_bounded_r3.py:83` carries no `xfail` marker; suite passes.

Notes:
No action required.

## F3
Status: waived
Evidence:
- Primary marked F3 RESOLVED at [r3 primary response](./r3-2026-05-14T1552-primary-response.md) lines 22-23.
- `docs/reviewer/plan-plan/` is gone; r2 chain artifacts are tracked.

Notes:
The only untracked path at primary scan time was the in-flight r3 request, which is expected per the standard chain workflow.

## F4
Status: waived
Evidence:
- Primary marked F4 RESOLVED at [r3 primary response](./r3-2026-05-14T1552-primary-response.md) lines 25-26.

Notes:
Slice 1 checkboxes ticked.

## S1.F1
Status: waived
Evidence:
- Finding raised against the in-flight r3 chain artifacts (`r3-*-primary-request.md`, `r3-*-primary-response.md`, `r3-*-sweep1-request.md`) being untracked and not yet recorded in `chain.json` at sweep scan time.
- Same observation in the sweep stderr tail: `git status --short --untracked-files=all` printed only files from the very review round being executed.

Notes:
This is the inherent chicken-and-egg of the review loop: in-flight round artifacts must be written before the round can complete, and the manifest entry plus `git add` happen post-verdict when the coordinator commits the round. Marking this as a defect would make the post-slice gate unsatisfiable for the round that observes itself. The coordinator commits this round's chain artifacts (including the r3 request/response trio and the updated `chain.json`) alongside this resolution per the standard external-review hygiene rule. Not a defect of the slice's production code.

## S1.F2
Status: fixed
Evidence:
- Production fix: [`skills/external-review/scripts/external-reviewer.py`](../../skills/external-review/scripts/external-reviewer.py) — the final-ready post-rename block now rewrites the response body's `Request:` header line so it references the renamed `r{N}-{ts}-primary-request.md` instead of the pre-rename non-namespaced path. Also refreshes `ReviewerResult.review_body` so downstream merging uses the corrected text.
- Regression test: `skills/external-review/tests/test_final_ready_rename_response_body.py::test_final_ready_rename_rewrites_response_request_header` runs a r1=revise → r2=ready end-to-end fixture to trigger the post-hoc rename and asserts the body references the renamed request file (and not the stale basename).
- Commit: `4410e0b` — `external-reviewer: rewrite response Request: header on final-ready rename`.
- Pytest: full suite `128 passed, 1 warning` (baseline 127 + 1 new test).

Notes:
The artifact inconsistency the sweep observed in this very chain (the r3 primary response body still pointing at `r3-2026-05-14T1552-request.md` after the file was renamed to `r3-2026-05-14T1552-primary-request.md`) was a real bug. The fix prevents future rounds from producing the same inconsistency. The historical artifacts already in this chain folder are left as-is — rewriting them would invalidate the immutable review-chain record.

## S1.F3
Status: fixed
Evidence:
- Test fix: [`skills/external-review/tests/test_failed_round_truth.py`](../../skills/external-review/tests/test_failed_round_truth.py) — `test_failed_reviewer_with_echoed_verdict_is_not_trusted` now loads `chain.json` and asserts `rounds[-1]["merged_verdict"] is None`, plus asserts the persisted response file is `< 8 KiB`.
- Commit: `8680e3c` — `external-reviewer: assert merged_verdict=null and <8KiB response on failed round`.
- Pytest: full suite `128 passed, 1 warning`.

Notes:
Spec §S3 item 1's two acceptance bullets (`merged_verdict: null` and response file under 8 KiB) are now directly asserted alongside the existing status/returncode/verdict checks, in the same failed-process scenario.
