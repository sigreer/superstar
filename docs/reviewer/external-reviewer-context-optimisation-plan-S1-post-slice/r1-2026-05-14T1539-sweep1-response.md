# Review — 2026-05-14-external-reviewer-context-optimisation-plan.md (post-slice, round 1)

- Target: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md`
- Request: `docs/reviewer/external-reviewer-context-optimisation-plan-S1-post-slice/r1-2026-05-14T1539-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Status: `ok`

---

1. Findings

F1. Severity: blocking. Failed primary rounds can still record false finding counts. The implementation forces `verdict=None` / `verdict_valid=False` on reviewer failure at [external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:655), but later always parses findings from `primary.review_body` at [external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:1230) and writes them into the round entry at [external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:1269). This violates the spec requirement that failed reviewers force `findings_count = 0` ([spec](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md:90)). I confirmed with a failing reviewer whose stderr contained `## F99` / `Severity: blocking`: JSON and `chain.json` recorded `findings_count: 1`, `blocking_findings_count: 1` despite `status: failed`.

F2. Severity: blocking. The post-slice review artifacts are untracked and incomplete. `git status --short` shows:
`?? docs/reviewer/external-reviewer-context-optimisation-plan-S1-post-slice/`
`?? docs/reviewer/plan-plan/`
`?? review-stderr.log`
The S1 review chain folder contains only `r1-...primary-request.md`, `r1-...primary-response.md`, and `r1-...sweep1-request.md`; there is no `chain.json` and no sweep response. That is not a complete post-slice gate artifact.

F3. Severity: important. Slice progress was not marked in the plan. The handoff requires updating plan checkboxes as slices close ([handoff](/home/simon/Dev/sigreer/skills/superstar/docs/handoffs/2026-05-14-external-reviewer-context-optimisation-plan-prompt.md:26)), but Slice 1 tasks still show unchecked steps starting at [plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:80). The commits exist, but the canonical plan document does not reflect completion.

F4. Severity: minor. A passing S1 acceptance test is still marked `xfail`. [test_failed_r2_bounded_r3.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/tests/test_failed_r2_bounded_r3.py:84) marks `test_r3_request_size_bounded` as expected failure, but the full suite reports it as XPASS. Remove the stale marker so the size-bound acceptance is a normal enforced test.

2. Open questions / assumptions

No open design questions. I assume Slice 1 is intended to be closed now, based on the commit series ending at `external-reviewer: e2e test — failed r2 yields bounded clean r3`.

3. Suggested document edits

Update the Slice 1 checkboxes in the plan after F1 is fixed and verification is rerun. Also add a short Slice 1 evidence note with the exact test command and result, including that the XPASS has been resolved.

4. Verification gaps / commands

I ran:

`python3 -m pytest skills/external-review/tests/test_sentinel_stripper.py skills/external-review/tests/test_response_artifact.py skills/external-review/tests/test_failed_round_truth.py skills/external-review/tests/test_merged_findings_skips_failed.py skills/external-review/tests/test_returncode_status_persisted.py skills/external-review/tests/test_preamble_skips_failed.py skills/external-review/tests/test_resolution_gate_bypass.py skills/external-review/tests/test_failed_r2_bounded_r3.py skills/external-review/tests/test_chain_soft_migration.py -q`

Result: `28 passed, 1 xpassed`.

`python3 -m pytest skills/external-review/tests/ -q -rxX`

Result: `125 passed, 1 xpassed, 1 warning`; XPASS is `test_r3_request_size_bounded`.

5. Overall verdict: revise

---

## Reviewer stderr (tail)

```text
f](/home/simon/Dev/sigreer/skills/superstar/docs/handoffs/2026-05-14-external-reviewer-context-optimisation-plan-prompt.md:26)), but Slice 1 tasks still show unchecked steps starting at [plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:80). The commits exist, but the canonical plan document does not reflect completion.

F4. Severity: minor. A passing S1 acceptance test is still marked `xfail`. [test_failed_r2_bounded_r3.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/tests/test_failed_r2_bounded_r3.py:84) marks `test_r3_request_size_bounded` as expected failure, but the full suite reports it as XPASS. Remove the stale marker so the size-bound acceptance is a normal enforced test.

2. Open questions / assumptions

No open design questions. I assume Slice 1 is intended to be closed now, based on the commit series ending at `external-reviewer: e2e test — failed r2 yields bounded clean r3`.

3. Suggested document edits

Update the Slice 1 checkboxes in the plan after F1 is fixed and verification is rerun. Also add a short Slice 1 evidence note with the exact test command and result, including that the XPASS has been resolved.

4. Verification gaps / commands

I ran:

`python3 -m pytest skills/external-review/tests/test_sentinel_stripper.py skills/external-review/tests/test_response_artifact.py skills/external-review/tests/test_failed_round_truth.py skills/external-review/tests/test_merged_findings_skips_failed.py skills/external-review/tests/test_returncode_status_persisted.py skills/external-review/tests/test_preamble_skips_failed.py skills/external-review/tests/test_resolution_gate_bypass.py skills/external-review/tests/test_failed_r2_bounded_r3.py skills/external-review/tests/test_chain_soft_migration.py -q`

Result: `28 passed, 1 xpassed`.

`python3 -m pytest skills/external-review/tests/ -q -rxX`

Result: `125 passed, 1 xpassed, 1 warning`; XPASS is `test_r3_request_size_bounded`.

5. Overall verdict: revise
tokens used
42,769
```
