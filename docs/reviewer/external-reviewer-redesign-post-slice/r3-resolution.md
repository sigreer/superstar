# Round 3 resolution

## F1 — verdict still `revise`, no round-3 response in manifest yet
- **Verdict:** addressed (will be resolved by passing the next round).
- **Analysis:** F1 is procedural — the reviewer noted that the latest recorded verdict is still `revise` and round 3 was not yet in the manifest because the review was actively iterating. F2 (chain artefacts untracked) and F3 (parser spec drift) are the substantive causes; once they are fixed and round 4 returns `ready` or `ready with small edits`, F1 dissolves on its own.
- **No direct change** is made for F1 in this resolution. The next round's submission is the resolution.

## F2 — chain artefacts untracked
- **Verdict:** fixed.
- **What changed:** committed `r2-2026-05-14T0129-request.md`, `r2-2026-05-14T0129-response.md`, `r3-2026-05-14T0136-request.md`, `r3-2026-05-14T0136-response.md`, and the updated `chain.json` (which already had round 3 appended with correct counts).
- **Workflow note:** going forward, the resolution pattern for each round should include staging and committing the just-finished round's chain artefacts (`r{N}-*-request.md`, `r{N}-*-response.md`, and any `chain.json` delta) as part of — or immediately alongside — the resolution commit. Round 2 deferred this and round 3 inherited the backlog; the rule keeps the chain folder reproducible from `git log` alone.
- **Commit:** `5cbb0fb` (`external-review: commit r2 and r3 chain artefacts`).

## F3 — `parse_findings` spec drift (returns `(0, 0)` for unparseable bodies)
- **Verdict:** fixed.
- **Spec contract** (`docs/superstar/specs/2026-05-13-external-reviewer-redesign-design.md`, "Finding-count parsing", ~line 317): if no accepted finding form matches AND no crash sentinel fires, `findings_count` and `blocking_findings_count` are `null` so the coordinator inspects the prose. Previous behaviour returned `(0, 0)`, conflating "explicitly zero findings" with "unparseable response".
- **What changed:**
  - `skills/external-review/scripts/external-reviewer.py`:
    - `parse_findings` now distinguishes three outcomes:
      1. Crash sentinel matched → `(None, None)`. The crash check short-circuits before `_collect_findings`, so a body that triggers the sentinel never silently returns a number.
      2. At least one finding-form regex (prose, heading, or bullet) matched → `(n, blocking)` with real counts (`n >= 1`).
      3. Body present, no crash sentinel, no recognised finding form, no explicit-empty marker → `(None, None)`.
    - New `EMPTY_FINDINGS_RE` recognises explicit empty declarations (`## Findings\nnone`, `Findings: none`, `Findings: n/a`, `Findings: 0`) as the legitimate `(0, 0)` case. This preserves the ability for a reviewer to declare zero findings without forcing the coordinator into prose-inspection.
- **Tests** (`skills/external-review/tests/test_findings.py`):
  - Added `test_prose_without_finding_ids_returns_none` — asserts `parse_findings("This response has prose but no F IDs. Overall verdict: revise") == (None, None)`.
  - Added `test_explicit_empty_findings_heading_returns_zero` and `test_explicit_findings_none_inline_returns_zero` for the two explicit-empty marker forms.
  - Replaced the previous `test_no_findings_returns_zero` (which asserted `(0, 0)` for `"Overall verdict: ready\n\nNo findings."`) — that assertion was contrary to spec. The two new explicit-empty tests cover the legitimate zero-findings case.
  - Renamed `test_unparseable_returns_none` to `test_crash_sentinel_returns_none` to reflect that the prose-without-IDs path now has its own dedicated test.
- **Verification on real artefacts:**
  ```
  r1-2026-05-14T0124-response.md -> (3, 2)
  r2-2026-05-14T0129-response.md -> (3, 2)
  r3-2026-05-14T0136-response.md -> (4, 2)
  ```
  All three still parse to the expected counts after the fix.
- **chain.json:** round 3's entry was already recorded with the correct `(4, 2)` when the round ran (the live response parses with both old and new code because it contains real `F1./F2./F3./F4.` prose findings). No re-emission was needed for content, but the file is now committed as part of F2.
- **Test suite:** `python3 -m pytest skills/external-review/tests/` → `23 passed` (up from 21).
- **Commit:** `6bc9289` (parser fix + tests bundled in the same commit).

## F4 — r2-resolution.md references "see git log" instead of SHAs
- **Verdict:** fixed.
- **What changed:** edited `docs/reviewer/external-reviewer-redesign-post-slice/r2-resolution.md` lines 21, 30, and 35 to name the actual commit SHAs:
  - Line 21 (F1 parser fix): `see git log` → `43f0aff`.
  - Line 30 (F2 planning artefacts): `see git log` → `591a20c` (bundled commit).
  - Line 35 (F3 checkboxes): `see git log` → `591a20c` (bundled with F2).
- **Commit:** captured in the same commit as this resolution doc (see closing commit SHA below).
