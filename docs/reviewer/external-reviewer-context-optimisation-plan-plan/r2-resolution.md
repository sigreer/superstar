# Resolution for r2

## F1
Status: fixed in r1; reaffirmed in r2.
Evidence:
- No changes in r2 — the reviewer marked F1 as RESOLVED.

## F2
Status: fixed in r1; reaffirmed in r2.
Evidence:
- No changes in r2 — the reviewer marked F2 as RESOLVED.

## F3
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md` Task 2.4 Step 4 (`apply_budget` body), Task 2.4 Step 2 (unit-test fixture).
- Changes:
  - **Trim-loop bug.** The previous `apply_budget` body broke out of the per-section levels loop after the first successful trim, so a 60 KB section against a 20 KB budget only ever cut to 40 KB. The new loop body removes that `break`, re-extracts `section_body` from the *current* (already-trimmed) text on each iteration, and proceeds through smaller levels until either `len(out) <= budget_chars` or all levels for that section are exhausted (final level `0` drops the body entirely). Each level still skips itself if it doesn't actually reduce size (`if len(replacement) >= len(section_body): continue`), so progress is monotone.
  - **Unit-test labels.** `test_apply_budget_preserves_priority_under_cap` now constructs the fixture with the stable headings introduced by Task 1.10 Step 4 (`## Review chain summary`, `## Prior-round findings`, `## Resolution report for prior round`, `## Changes since prior round`, `## Target Preview`) — matching the real anchors `apply_budget` searches for. The fixture is also bumped: 80 KB of prior-findings padding plus the F-ID line, so the test verifies the F-ID line survives head+tail elision when the section is capped to 16 KB.
- Verification: a manual trace of the new loop on the failing CLI-test scenario (60 KB merged-findings, 20 KB budget) shows: pass 1 caps prior-findings to 40 KB (still over); pass 2 to 16 KB (still over after other sections); pass 3 to 8 KB (under) — total ≤ 20 KB + scaffolding. The previous one-trim-per-section logic would have stopped at 40 KB.

Notes:
The simplification — drop the `break`, re-extract per iteration — is also smaller code than the original. The previous version's "Recompute section_end for the new shorter body in case more iterations follow (they will not here, but defensive)" comment was a hint that the author of the original version (me) suspected the early break was wrong but didn't follow through.

## F4
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md` Task 2.5 Step 1 — the `test_global_diff_cap_applies` fixture.
- Change: the file-body string was `"x" * 80 + "\n" * 200` — which is one 80-character line followed by 200 blank lines, total ~280 bytes. With `max_lines=1` and the per-file cap of `min(max_lines, 200)=1`, each file preview was ~80 bytes. Eight files × ~80 bytes = ~640 bytes, well under any cap → "bytes elided" would never appear and the test was self-failing.
- Fix: replace with `("x" * 80 + "\n") * 200` — 200 genuine 80-character lines per file (~16 KB each). `max_lines` raised to 200 so the per-file cap allows the full preview through. Eight files × ~16 KB = ~128 KB assembled, which exceeds the global-cap floor of 64 KB → `cap_with_elision` fires and the "bytes elided" assertion holds.
- Verification: a hand-calculation against `cap_with_elision(max_bytes=64*1024)` with a 128 KB input gives a 64 KB output containing the elision marker — the test's `assert "bytes elided" in diff` succeeds.

Notes:
The original fixture string was a Python comprehension typo masquerading as a length calculation. The corrected form `("x" * 80 + "\n") * 200` is the canonical Python idiom for "N lines of K characters."

## F5
Status: fixed in r1; reaffirmed in r2.
Evidence:
- No changes in r2 — the reviewer marked F5 as RESOLVED.
