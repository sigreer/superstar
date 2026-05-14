# Review — 2026-05-14-external-reviewer-context-optimisation-plan.md (post-slice, round 1)

- Target: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md`
- Request: `docs/reviewer/external-reviewer-context-optimisation-plan-S1-post-slice/r1-2026-05-14T1539-primary-request.md`
- Reviewer command: `reviewer-agent`
- Status: `ok`

---

1. Findings

F1 — Severity: blocking — Failed primary rounds still record findings from failed stderr.  
The spec requires `findings_count = 0` for `result.returncode != 0`, regardless of body content ([spec](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md:90)). The implementation forces `verdict=None`/`verdict_valid=False` in `run_one_reviewer`, but later still runs `parse_findings(primary.review_body)` unconditionally and persists those counts ([external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:1230), [external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:1269)). I reproduced a failed reviewer whose stderr contains `## F1` and `Severity: blocking`; emitted JSON returned `status=failed`, `verdict_valid=False`, but `findings_count=1`, `blocking_findings_count=1`. That violates S1 chain-integrity acceptance.

F2 — Severity: important — The r3 size acceptance assertion is marked `xfail` even though it passes.  
[test_failed_r2_bounded_r3.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/tests/test_failed_r2_bounded_r3.py:84) marks the `<250 KB` r3 request test as non-strict xfail. The current suite reports `XPASS`, so the assertion is currently satisfied, but a future regression would be hidden as an expected failure. The plan only allows xfail “if the test fails on r3 size” ([plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:1788)); remove the xfail now or make it strict only if there is a deliberate pending failure.

F3 — Severity: important — Post-slice artifacts are untracked and incomplete.  
`git status --short` shows:
`?? docs/reviewer/external-reviewer-context-optimisation-plan-S1-post-slice/`
`?? review-stderr.log`  
The reviewer chain folder contains only `r1-2026-05-14T1539-primary-request.md`, with no response or `chain.json`. Because the script can synthesize legacy manifests from loose `r*-request.md` files, leaving a partial review-chain artifact in the repo risks confusing the next gate run.

F4 — Severity: minor — The plan checkboxes still show Slice 1 as entirely incomplete.  
All Slice 1 task steps remain `- [ ]` in the target plan, including the final acceptance task ([plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:80)). The commits indicate implementation happened, but the document does not reflect slice state, so the post-slice handoff is not self-evidencing.

2. Open questions / assumptions

I assume Slice 1 is intended to close now, before Slice 2 starts. If so, F1 and F2 should be fixed before accepting the slice.

3. Suggested document edits

Update the plan’s Slice 1 checkboxes after fixes land, and add the actual verification summary from the closeout run. If F2 is intentionally deferred, document why the size assertion must remain xfailed despite currently passing.

4. Verification gaps / commands

Ran:

```bash
python3 -m pytest skills/external-review/tests/ -q
```

Result: `125 passed, 1 xpassed, 1 warning`.

Also ran focused S1 tests:

```bash
python3 -m pytest skills/external-review/tests/test_sentinel_stripper.py \
  skills/external-review/tests/test_response_artifact.py \
  skills/external-review/tests/test_failed_round_truth.py \
  skills/external-review/tests/test_merged_findings_skips_failed.py \
  skills/external-review/tests/test_returncode_status_persisted.py \
  skills/external-review/tests/test_chain_soft_migration.py \
  skills/external-review/tests/test_preamble_skips_failed.py \
  skills/external-review/tests/test_resolution_gate_bypass.py \
  skills/external-review/tests/test_failed_r2_bounded_r3.py -q -rxX
```

Result: `28 passed, 1 xpassed`.

Add a regression test for failed reviewer stderr containing finding-shaped text and assert emitted JSON plus `chain.json` both record zero findings/blocking findings.

5. Overall verdict: revise

---

## Reviewer stderr (tail)

```text
n synthesize legacy manifests from loose `r*-request.md` files, leaving a partial review-chain artifact in the repo risks confusing the next gate run.

F4 — Severity: minor — The plan checkboxes still show Slice 1 as entirely incomplete.  
All Slice 1 task steps remain `- [ ]` in the target plan, including the final acceptance task ([plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:80)). The commits indicate implementation happened, but the document does not reflect slice state, so the post-slice handoff is not self-evidencing.

2. Open questions / assumptions

I assume Slice 1 is intended to close now, before Slice 2 starts. If so, F1 and F2 should be fixed before accepting the slice.

3. Suggested document edits

Update the plan’s Slice 1 checkboxes after fixes land, and add the actual verification summary from the closeout run. If F2 is intentionally deferred, document why the size assertion must remain xfailed despite currently passing.

4. Verification gaps / commands

Ran:

```bash
python3 -m pytest skills/external-review/tests/ -q
```

Result: `125 passed, 1 xpassed, 1 warning`.

Also ran focused S1 tests:

```bash
python3 -m pytest skills/external-review/tests/test_sentinel_stripper.py \
  skills/external-review/tests/test_response_artifact.py \
  skills/external-review/tests/test_failed_round_truth.py \
  skills/external-review/tests/test_merged_findings_skips_failed.py \
  skills/external-review/tests/test_returncode_status_persisted.py \
  skills/external-review/tests/test_chain_soft_migration.py \
  skills/external-review/tests/test_preamble_skips_failed.py \
  skills/external-review/tests/test_resolution_gate_bypass.py \
  skills/external-review/tests/test_failed_r2_bounded_r3.py -q -rxX
```

Result: `28 passed, 1 xpassed`.

Add a regression test for failed reviewer stderr containing finding-shaped text and assert emitted JSON plus `chain.json` both record zero findings/blocking findings.

5. Overall verdict: revise
tokens used
81,965
```
