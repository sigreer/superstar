# Resolution for r1

Round 1 of the S7 post-slice chain. Reviewer returned `revise` with 4
findings (2 blocking technical, 2 important procedural). The two
blocking technical findings (F1 sweep-planning ordering, F2
placeholder plumbing regression) were fixed in dedicated commits
before this closeout; the two procedural findings (F3 plan checkboxes,
F4 dirty tree on `main`) are addressed here.

## F1

Status: fixed
Evidence:
- Commit: `d23c579`
- Files: `skills/external-review/scripts/external-reviewer.py`
- Verification:
  - `plan_sweeps` is now invoked after the current primary's result is
    known, so `final-ready` correctly fires on a `revise → ready`
    transition rather than being skipped because the prior manifest
    round's verdict was `revise`.
  - Covered by the round-2 reproduction described in the reviewer
    response (primary `ready` after a round-1 `revise`) and by the
    existing `test_review_depth.py` planner tests.

## F2

Status: fixed
Evidence:
- Commit: `fbcead7`
- Files: `skills/external-review/scripts/external-reviewer.py`
- Verification:
  - `run_one_reviewer()` now forwards the resolved `previous_response`
    and `resolution_file` paths into `run_reviewer()` instead of
    hard-coding `None`, so the S6 `{previous_response}` and
    `{resolution_file}` placeholders substitute correctly for real
    reviewer invocations on round N+1.
  - The `AGENT_REVIEWER_CMD="stub {previous_response} {resolution_file}"`
    reproduction the reviewer described (which previously received
    `ARGS:|`) now receives the real artefact paths.

## F3

Status: fixed
Evidence:
- Commit: this commit (`external-review: S7 r1 closeout`)
- Files: `docs/superstar/plans/2026-05-13-external-reviewer-redesign.md`
- Verification:
  - All `- [ ]` Step entries in Slice 7 Tasks 7.1, 7.2, and 7.3
    (lines ~2194–2737) are flipped to `- [x]`.
  - A Slice 7 closeout note is appended after the Slice 6 closeout,
    documenting the implementation commits (`3445f3a`, `6bb8399`,
    `4016f80`, `eb187da`), the post-r1 fix commits (`d23c579`,
    `fbcead7`), the final test count (`96 passed`), the standing
    on-`main` + dirty-files override, and the disposition of the
    round-1 findings.

## F4

Status: waived
Evidence:
- The repo's standing on-`main` + pre-existing dirty-files override
  applies. Recorded at the Slice 4 closeout and restated at each
  subsequent slice closeout in
  `docs/superstar/plans/2026-05-13-external-reviewer-redesign.md`;
  the Slice 7 closeout note appended in this commit restates it
  again. The pre-existing dirty tracked files (`CLAUDE.md` and the
  four `skills/*/SKILL.md` files) remain untouched.
- The untracked `docs/reviewer/external-reviewer-redesign-S7-post-slice/`
  folder is the in-flight S7 chain itself; this commit lands all of
  its round-1 artefacts (request, response, chain.json, resolution),
  which is the expected round-lifecycle pattern documented in the
  Slice 1 closeout.
