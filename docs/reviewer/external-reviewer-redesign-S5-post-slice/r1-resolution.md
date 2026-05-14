# Resolution for r1

Round 1 of the S5 post-slice chain. Reviewer returned `revise` with 3
findings (1 blocking). F1 is a real bug in `compute_diff_section`; F2
and F3 are housekeeping (plan stale + in-flight chain artefacts).

## F1
Status: fixed
Evidence:
- Commit: `cf65a88` `external-review: scope diff status/untracked to --changed-files paths`
- Files:
  - `skills/external-review/scripts/external-reviewer.py`
  - `skills/external-review/tests/test_diff.py`
- Verification:
  - `compute_diff_section` now scopes `git status --porcelain` to the
    same `paths` passed for the diff command, so unrelated
    dirty/untracked files no longer leak into the prompt when callers
    pass `--changed-files`. The untracked-file preview loop iterates
    the scoped `git status --porcelain -- <paths>` output, so only
    in-scope untracked entries are previewed.
  - `diff_included` in the manifest round entry and JSON payload now
    requires `base_source in {"auto", "explicit"}` and a non-empty
    `diff_section` in addition to `not args.no_diff`. The
    `unavailable` case (incremental mode without a prior
    `head_sha_after_round`) no longer reports `diff_included=true`.
  - Two new regression tests in `test_diff.py`
    (`test_paths_scope_excludes_unrelated_untracked` and
    `test_paths_scope_includes_in_scope_untracked`) assert the scoping
    fix; full suite went from 70 to 72 passing.

Notes:
This was also flagged by the in-loop S5.1 code-quality reviewer and
the S5.2 reviewer's `diff_included` accuracy nit, so the fix addresses
both in one commit.

## F2
Status: fixed
Evidence:
- Commit: this commit (`external-review: S5 r1 closeout`)
- Files: `docs/superstar/plans/2026-05-13-external-reviewer-redesign.md`
- Verification: all 10 `- [ ]` entries across Slice 5's Tasks 5.1 and
  5.2 are flipped to `- [x]`; Slice 6+ checkboxes unchanged. A Slice
  5 closeout note is appended documenting the two implementation
  commits (`faed8b5`, `1934627`), the post-r1 fix commit (`cf65a88`),
  the final test count (`72 passed`), the post-slice review outcome,
  and the standing pre-flight branch-check + dirty-files overrides.

## F3
Status: fixed/waived
Evidence:
- This commit (`external-review: S5 r1 closeout`) commits the
  in-flight S5 chain artefacts:
  - `docs/reviewer/external-reviewer-redesign-S5-post-slice/chain.json`
  - `docs/reviewer/external-reviewer-redesign-S5-post-slice/r1-2026-05-14T0334-request.md`
  - `docs/reviewer/external-reviewer-redesign-S5-post-slice/r1-2026-05-14T0334-response.md`
  - `docs/reviewer/external-reviewer-redesign-S5-post-slice/r1-resolution.md`
- Pre-existing dirty tracked files (`CLAUDE.md` and the four
  `skills/*/SKILL.md` files) remain untouched under the standing
  human-partner authorisation recorded in the Slice 1, 2, and 4
  closeout notes; the Slice 5 closeout note restates the override so
  it carries forward.

Notes:
The "in-flight" state of the S5 chain folder at request time (request
materialised, response and chain.json pending) is the expected
round-lifecycle pattern documented in the Slice 1 closeout. With this
commit the round closes and the artefacts land.
