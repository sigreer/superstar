# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/specs/2026-06-08-X29-timeline-day-axis-design.md` — "Day walk"
  section.
Notes:
The active-day definition no longer keys off *shown* X closes. It now reads
"every embedded X close — regardless of the initial `--show-x` state." Added an
explicit F1 invariant: X-only days are active days, get a reserved date marker
exactly as X cards already reserve layout space while hidden, and are therefore
never folded into a collapsed quiet run — so toggling X on can never reveal an X
card on a day without a date pill or inside a quiet segment. This matches the
shipped client-side instant-toggle contract (X always embedded; visibility is a
CSS toggle, not a re-render).

## F2
Status: fixed
Evidence:
- Files: `docs/specs/2026-06-08-X29-timeline-day-axis-design.md` — Part 2 opening
  paragraph, Part 1 apply-list, and "Affected code".
Notes:
Removed the contradictory wording. One contract now: the hour-threshold
`quiet_gaps` / `GAP_THRESHOLD_HOURS` API is **retired/removed**, and quiet
rendering is driven entirely by a day-run classifier over the active-day set
(`QUIET_RUN_DAYS`). Part 1's apply-list no longer lists "coverage intervals
feeding `quiet_gaps`" (with an added note that there is deliberately no
`quiet_gaps` consumer), and "Affected code" states the API is removed rather than
"call sites use the helper."

## F3
Status: fixed
Evidence:
- Files: `docs/specs/2026-06-08-X29-timeline-day-axis-design.md` — Part 1
  apply-list ("duration operand") and Testing ("Duration under normalization").
Notes:
The interval-effective-instant model now explicitly covers the popout duration
computation (`_duration_text`): a day-precision close used as a duration operand
resolves to end-of-day so the P4-shaped case (minute start later than a
day-precision close on the same date) yields a positive duration, while the
displayed close label stays day-only (no fabricated time). Added a dedicated
regression test for this in the Testing section.
