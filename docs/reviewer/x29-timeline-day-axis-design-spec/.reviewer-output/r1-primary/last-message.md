1. Findings

F1 (Severity: blocking) — X-item days are underspecified and conflict with the existing instant toggle contract. The spec defines active days as including “shown X close” events in [docs/specs/2026-06-08-X29-timeline-day-axis-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-08-X29-timeline-day-axis-design.md:85), while also saying `--show-x` behaves as before in [the same spec](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-08-X29-timeline-day-axis-design.md:135). In the shipped X29 worktree, X-items are always embedded, reserve layout space even when hidden, and are toggled client-side without regeneration in `render.py` lines 321-327 and 551-553. If the initial render has `show_x=False`, “shown X close” could exclude X-only days from the day axis; toggling X on would then reveal X cards/nodes on days with no date marker, or inside a collapsed quiet-run segment. The spec needs to choose: include all embedded X close days in the axis regardless of initial visibility, or make the axis/gap segments also toggle/recompute with X visibility.

F2 (Severity: important) — The spec gives contradictory implementation guidance for `quiet_gaps`. It says the day-axis model “replaces” the hour-threshold `quiet_gaps` bridge in [lines 79-81](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-08-X29-timeline-day-axis-design.md:79), but Part 1 still requires effective instants for “coverage intervals feeding `quiet_gaps`” in [lines 62-65](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-08-X29-timeline-day-axis-design.md:62), and Affected code says `quiet_gaps` call sites use the new helper while also “replacing the hour-threshold gap pass” in [lines 130-133](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-08-X29-timeline-day-axis-design.md:130). Current `quiet_gaps` is explicitly hour-threshold based in `render.py` lines 15 and 121-145. The plan cannot reliably follow this until the spec states whether `quiet_gaps` is deleted, renamed/reworked into day-run collapse, or retained only as a lower-level coverage helper.

F3 (Severity: important) — Duration calculation is left out of the effective-instant model. The spec says the popout keeps “computed duration” in [lines 107-109](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-08-X29-timeline-day-axis-design.md:107), but the “apply it everywhere” list in [lines 62-67](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-08-X29-timeline-day-axis-design.md:62) does not mention duration/detail computation. The current renderer computes duration from raw `started.when` and `closed.when` in `render.py` lines 463-475, so the documented P4 case can still produce an empty or inverted duration even after lanes and anchors are fixed. The spec should say whether duration uses interval-effective start/end internally while labels continue to display the original day-precision date.

2. Open questions / assumptions

I assume the intended X behavior is still the base-spec instant toggle with all X data embedded. If so, the day axis probably needs to include all embedded X close days, not only initially visible X days.

I assume “day-precision close = end-of-day” is meant for all interval math, including duration, not just lane/scale positioning.

3. Suggested document edits

Change “shown X close” to either “all embedded X close events” or explicitly describe how date markers and quiet segments toggle when X visibility changes.

Replace the mixed `quiet_gaps` wording with one clear contract: for example, “retire the hour-threshold `quiet_gaps` API and replace it with a day-run classifier over active days,” or “keep `quiet_gaps` only as an internal coverage-normalization helper, but quiet rendering is driven by `QUIET_RUN_DAYS`.”

Add duration/detail to the effective-instant section and testing list, with a regression for same-day minute start plus day-precision close.

4. Verification gaps / commands that should be run

Add/extend tests for X-only active days with `show_x=False`, then assert toggling X on does not reveal cards inside collapsed quiet runs or without a date marker.

Run `python3 -m pytest tools/timeline/tests -q` in the X29 worktree after implementation.

Run full default `python3 -m pytest` from the repo root after ensuring timeline tests are discovered.

Overall verdict: revise