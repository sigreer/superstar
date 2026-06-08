# X29 — Timeline iteration: day-axis spine + legacy interval fix

## Status

Iteration on the shipped `tools/timeline` implementation. Extends — does not
replace — `docs/specs/2026-06-06-X29-timeline-design.md` (the "base spec"). Only
the deltas below change; everything in the base spec that is not contradicted
here still holds. This is the acceptance-driven completion of slice **X29**: the
human visual-acceptance gate surfaced two defects and one visual redesign, all in
the date/gap/lane machinery.

## Motivation

Visual acceptance of the superstar render surfaced three items:

1. **Bug — legacy phases share one spine instead of parallel lanes.** Phases that
   ran concurrently in the day-precision era (e.g. superstar P3 ∥ P4, both
   2026-05-19) collapse onto a single track; minute-precision phases (P5+)
   separate correctly.
2. **Bug — inactivity renders as a blank stop, not a dotted segment.** The
   "N quiet days" bridge does not appear between phases; the spine just stops and
   restarts.
3. **Enhancement — dates clutter every card title.** Days are the primary unit of
   measure, but the date is appended to each card/title face. The request: make
   the day axis the spine's backbone and pull dates off the faces.

Bugs 1 and 2 share a single root cause (below); item 3 is the day-axis redesign.

## Part 1 — Day-precision end normalization (fixes Bug 1 and Bug 2)

### Root cause

Day-precision dates resolve to `00:00` of their day. That is correct for a
**start/created** boundary but wrong for an **end/closed** boundary: it pins a
legacy phase's close to the *start* of its day — before that same phase's
minute-precision `started`, and before later same-day activity. Confirmed in
superstar data:

```
P4  started = 2026-05-19 23:41 (minute)   closed = 2026-05-19 00:00 (day)
```

The phase interval is therefore **inverted** (`end < start`). Every consumer of
phase intervals then misbehaves:

- `_overlap_keys` / `assign_lanes` compare inverted intervals, so genuinely
  concurrent legacy phases are not detected as overlapping → they share a lane →
  **Bug 1**.
- `quiet_gaps` merges coverage `(start, end)` where `end < start`, corrupting the
  merge → gaps are mis-computed and the dotted bridge never renders → **Bug 2**.

### Change

Introduce a single notion of an **interval-effective instant** for a date value
used as a *boundary*:

- A boundary used as an **end/close** with **day** precision resolves to
  end-of-day (`23:59:59` of that date).
- A boundary used as a **start/created** with day precision stays at `00:00`.
- Minute-precision values are unchanged in both roles.

Apply it at every place that treats a date as an interval boundary, an ordering
key, a scale anchor, or a **duration operand**: `phase_span` (the `end`), the
span tuples feeding `assign_lanes` and `_overlap_keys`, the `anchors` list
feeding `TimeScale`, slice/X **close** instants used for vertical positioning (so
a day-precision close sorts *after* same-day minute-precision activity rather
than before it), and the popout **duration computation** (`_duration_text`) — so
the documented P4 case (minute-precision start later than a day-precision close
on the same date) yields a real positive duration instead of an empty or
inverted one. Day-precision *starts/creates* feeding duration stay at `00:00`.

Note there is no `quiet_gaps` consumer in this list: Part 2 retires that
hour-threshold API entirely (see below), so the only remaining interval/anchor
consumers are lane assignment, overlap detection, the scale, positioning, and
duration.

**Display is unaffected.** `_fmt` already renders day-precision values with no
time-of-day; the end-of-day instant is an internal sort/interval value only.
Never surface a fabricated `23:59` (or `00:00`) in any label.

Outcome: legacy intervals become well-formed → P3 ∥ P4 regain parallel lanes;
coverage merges correctly → inactivity renders again (now via the day walk in
Part 2).

## Part 2 — Day-axis date spine

The spine becomes an explicit **day axis**. This **retires** the base spec's
hour-threshold gap bridge (`quiet_gaps` / `GAP_THRESHOLD_HOURS`) and the
"completion date/time on every card" rule. Quiet rendering is now driven
entirely by a **day-run classifier** over the active-day set (`QUIET_RUN_DAYS`),
not by coverage-interval hour math; `quiet_gaps` and `GAP_THRESHOLD_HOURS` are
removed, not reused.

### Day walk

Compute the set of **active days** = every calendar date carrying ≥1 **embedded**
point event, using each event's local date. Embedded events are: phase starts,
phase closes, slice closes, **and every embedded X close — regardless of the
initial `--show-x` state**. Because X-items are always embedded and merely
toggled client-side, X-only days are active days: each gets a date marker
reserved exactly as X cards already reserve layout space while hidden. This is
the F1 invariant — toggling X on can never reveal an X card on a day with no date
pill, nor inside a collapsed quiet-run segment, because an X-only day counts as
active and is therefore never part of an idle run. Walk the inclusive calendar
range from the earliest to the latest active day:

- **Active day** → one **date marker** on the spine: a faint full-width
  horizontal divider hairline plus a date pill (`19 May 2026`) centred on the
  spine. That day's cards/nodes hang off it as today, but **with the date removed
  from the title/face**.
- **Run of 1–2 consecutive idle days** (no active events) → each idle day still
  gets its own empty date pill (divider + pill, no cards).
- **Run of 3+ consecutive idle days** → collapse the entire run into one dotted
  "N quiet days" segment with the count = number of idle days in the run. No
  per-day pills inside a collapsed run.

The threshold constant is named (e.g. `QUIET_RUN_DAYS = 3`).

### Dates move to the popout

- Card faces show **ID + title only** — no trailing date/time.
- Phase node/title and close-ring labels drop their inline date clauses
  (`started <date>`, `complete · <date>`); the day axis now carries that.
- The **hover/click popout is unchanged**: full verbatim title, item ID,
  started/closed datetimes **with precision markers**, and computed duration all
  remain there. Exact times (`22:44`), durations, and minute precision survive
  only in the popout.

### Spacing (unchanged engine)

The existing time-proportional `TimeScale` with min/max guard rails is retained
unchanged — items keep their proportional vertical positions (busy days take more
height; sparse days less). Date pills and dividers **overlay** the proportional
layout: an **active day's** pill/divider sits at that date's first rendered event
position; an **idle day's** pill (1–2-day runs) has no event to anchor to, so it
is positioned by mapping that calendar day's local **noon** through `TimeScale`,
keeping it between the surrounding active days. Pills and dividers do not quantize
the scale into equal bands. A collapsed "N quiet days" run still compresses to the capped dotted
segment, as the gap cap already does.

### Direction toggle

Date pills and divider hairlines are positioned for **both** reading directions
and emitted with `data-ta`/`data-td` (and `data-ha`/`data-hd` for the divider
spans) exactly like existing elements, so the in-page newest/oldest-first toggle
flips them with everything else. Default remains newest-first.

## Affected code

- `render.py`: new interval-effective-instant helper used by `phase_span`, the
  span tuples, `anchors`, close-instant positioning, and `_duration_text`. The
  hour-threshold `quiet_gaps` / `GAP_THRESHOLD_HOURS` API is **removed**; a new
  day-walk over the active-day set (including all embedded X closes) emits date
  markers + dividers and classifies idle runs (`QUIET_RUN_DAYS`) into collapsed
  quiet segments. `_card`, `_node_html`, `_ring_html` drop inline date clauses
  from faces (popout/detail retains them).
- No change to `extract.py`, `model.py` date resolution, `backfill.py`, or the
  CLI surface. `--show-x` and overrides behave as before.

## Testing

Add to `tools/timeline/tests/` (all stdlib + pytest, fixture-driven):

- **End-of-day normalization:** a phase with `started` minute-precision later
  than a day-precision `closed` on the same date yields a well-formed (non-empty,
  non-inverted) interval; two same-day day-precision phases are detected as
  overlapping and assigned distinct lanes (Bug 1 regression).
- **Duration under normalization:** the same P4-shaped case (minute start later
  than a day-precision close) yields a **positive** popout duration via the
  interval-effective instants, while the displayed close label stays day-only
  (no fabricated time) (F3 regression).
- **X-only active days:** an X-item whose close falls on a date with no
  phase/slice activity produces a date marker on the axis even when rendered with
  `show_x=False`; assert that day is never folded into a collapsed quiet run and
  that an X-only day always carries a date pill (F1 regression).
- **Inactivity:** coverage with a multi-day hole produces a quiet segment
  (Bug 2 regression) at the correct day count.
- **Day walk boundaries:** active day → pill; a 1-day and a 2-day idle run →
  per-day empty pills; a 3-day and a longer idle run → single "N quiet days"
  collapse with correct count; first/last active day frame the range.
- **Dates off faces:** rendered card/node/ring markup contains no date on the
  face, while the detail/popout markup still contains the closed datetime and
  duration.
- **Dual direction:** every date pill and divider carries both `data-ta` and
  `data-td`; toggling direction is covered by the existing smoke assertions
  extended to the new elements.

Existing tests stay green; any base-spec test asserting a date on a card face or
the hour-threshold bridge is updated to the new model (and called out to the
post-slice reviewer as an intended change, like the prior T5/T6 deviations).

## Non-goals

- No uniform/quantized day-band layout — the proportional engine stays.
- No change to date *resolution* precedence, replay, backfill, overrides, or the
  CLI.
- No calendar-week/month grouping; the axis is per-day with quiet-run collapse.
- No new dependencies; single self-contained HTML file unchanged.

## Acceptance

1. Re-render this repo: superstar P3 ∥ P4 show as **parallel lanes**; at least one
   multi-day inactivity stretch renders as a dotted **"N quiet days"** segment;
   card faces carry **no dates**; the day axis shows a date pill per active day
   with 3+ idle runs collapsed; hover/click still reveals exact datetimes and
   durations; newest/oldest-first flips pills and dividers.
2. Re-render `/home/simon/Dev/sigreer/multistore` (dry-run/read-only) and eyeball:
   legacy day-precision phases lane correctly and the day axis reads cleanly on a
   longer, busier history.
3. `python3 -m pytest tools/timeline/tests -q` passes including the new
   regressions; full default `python3 -m pytest` discovery unaffected.
4. Human visual-acceptance sign-off on both rendered files — the X29 close gate.
