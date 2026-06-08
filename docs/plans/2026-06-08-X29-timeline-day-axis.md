# X29 Timeline Day-Axis Iteration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix two legacy-data rendering bugs and add a day-axis date spine to `tools/timeline`, so concurrent legacy phases lane correctly, inactivity renders again, and dates live on the spine (and popout) instead of cluttering card faces.

**Architecture:** All changes are in `tools/timeline/render.py` plus its tests. One root cause (day-precision closes resolving to `00:00`, inverting legacy intervals) is fixed by an interval-effective-instant helper applied to interval/anchor/duration math. The hour-threshold gap API is retired and replaced by a calendar day-walk classifier that drives date pills, dividers, and collapsed quiet-day runs.

**Tech Stack:** Python 3 stdlib only (`datetime`, `bisect`, `html`), pytest. No third-party deps. Self-contained single-file HTML output.

**Spec:** `docs/specs/2026-06-08-X29-timeline-day-axis-design.md` (and base spec `docs/specs/2026-06-06-X29-timeline-design.md`).

**Worktree:** `.worktrees/worktree-x29-visual-work-history-timeline-generator` (branch `worktree-x29-visual-work-history-timeline-generator`). The worktree already exists and is the X29 implementation isolation. Merge current `main` into the branch first so this committed plan and spec are present on the branch.

**Scheduling:** X29 is a standalone cross-cutting item — no phase siblings, no `parallel_group`, no shared integration surfaces. No `tasktool deps`/`surface`/`reserve` changes required.

**Test layout (read before writing tests):** the render suite is split across `tools/timeline/tests/test_render_lanes.py`, `test_render_rules.py`, `test_render_html.py`, `test_render_layout.py`, `test_render_direction.py`, `test_render_scale.py`. There is **no** `test_render.py`. Tests import `from timeline import model, render` and `from timeline.tests.helpers import phase, slice_, x`, build items with `model._item(key, kind, parent, dict)`, render via `render.render_html("fixture", items, generated=GEN)`, and assert on the HTML string with `re`. Date values are `model.DateValue(when, precision, source)` where `precision ∈ {"day","minute"}`.

---

## Execution Step 0: Start / adopt the worktree

- [ ] **Step 0.1: Adopt the worktree and integrate main**

```bash
tasktool start X29        # idempotent; prints the cd line for the existing worktree
cd .worktrees/worktree-x29-visual-work-history-timeline-generator
git merge --no-edit main  # bring the committed day-axis spec + this plan onto the branch
```

(The plan and spec are committed on `main` before this handoff, so the merge brings them in.)

- [ ] **Step 0.2: Confirm the baseline suite is green**

Run: `python3 -m pytest tools/timeline/tests -q`
Expected: PASS (the existing 77 tests). This is the pre-change baseline.

---

## File Structure

- **Modify:** `tools/timeline/render.py` — add `_eff_end` helper and `QUIET_RUN_DAYS`; apply effective instants to `phase_span`, anchors, slice/X positioning, and `_duration_text`; remove `quiet_gaps`/`GAP_THRESHOLD_HOURS`/`_gap_bounds`; add `classify_days` + day-marker layout elements + pill/divider/quiet-segment rendering; strip dates from card/node/ring faces.
- **Modify tests:** `test_render_lanes.py` (eff_end, lanes, classify), `test_render_rules.py` (duration), `test_render_html.py` (pills/dividers, x-only, dates-off-faces), `test_render_direction.py` (dual-direction pills). Reuse helpers in `tools/timeline/tests/helpers.py`; do not add new helper APIs.
- **No change:** `extract.py`, `model.py`, `backfill.py`, `timeline.py`, the CLI surface, overrides, `--show-x` semantics.

A note on existing tests: some base-spec tests assert a date on a card face or exercise the hour-threshold gap (`quiet_gaps`). Those are updated in the relevant task below and called out to the post-slice reviewer as intended model changes (precedent: the prior T5/T6 deviations).

---

## Task 1: Interval-effective end helper + well-formed legacy intervals (Bug 1)

**Files:**
- Modify: `tools/timeline/render.py` (add helper near `_fmt`; edit `phase_span`, `render_html` anchor construction)
- Test: `tools/timeline/tests/test_render_lanes.py`

- [ ] **Step 1: Write the failing test**

Append to `tools/timeline/tests/test_render_lanes.py` (it already imports `render`; add `model` if absent):

```python
import datetime as dt
from timeline import model, render


def test_day_precision_close_is_end_of_day_not_inverted():
    closed = model.DateValue(dt.datetime(2026, 5, 19, 0, 0, 0), "day", "field")
    assert render._eff_end(closed) == dt.datetime(2026, 5, 19, 23, 59, 59)
    started = dt.datetime(2026, 5, 19, 23, 41, 0)   # P4-shaped minute start
    assert render._eff_end(closed) > started        # interval no longer inverted


def test_two_same_day_phases_get_distinct_lanes():
    end = render._eff_end(model.DateValue(dt.datetime(2026, 5, 19, 0, 0), "day", "field"))
    spans = {
        "P3": (dt.datetime(2026, 5, 19, 0, 0), end, False),
        "P4": (dt.datetime(2026, 5, 19, 0, 0), end, False),
    }
    lane_of, count = render.assign_lanes([(k, s, e) for k, (s, e, _) in spans.items()])
    assert count == 2 and lane_of["P3"] != lane_of["P4"]
    assert "P3" in render._overlap_keys(spans) and "P4" in render._overlap_keys(spans)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tools/timeline/tests/test_render_lanes.py -k "end_of_day or distinct_lanes" -v`
Expected: FAIL — `render._eff_end` does not exist (AttributeError).

- [ ] **Step 3: Add the helper and normalize phase ends + anchors**

In `render.py`, add the helper directly after `_fmt` (around line 259):

```python
def _eff_end(dv):
    """Interval-effective instant for a date value used as an END/close boundary.

    Day-precision dates resolve to 00:00, which is correct for a start but pins a
    close to the *start* of its day — before same-day minute activity, inverting
    legacy intervals. As an end boundary a day-precision value resolves to
    end-of-day (23:59:59) instead. Minute precision and None pass through. This is
    an internal sort/interval/duration value only; never surface it in a label.
    """
    if dv is None or dv.when is None:
        return None
    if dv.precision == "day":
        return dv.when.replace(hour=23, minute=59, second=59)
    return dv.when
```

In `phase_span`, change the end line (was `end = phase.closed.when`):

```python
    end = _eff_end(phase.closed)
    return start, end, start is None
```

In `render_html`, change the two slice/X `closed.when` anchor appends to use `_eff_end`:

```python
    anchors += [_eff_end(s.closed) for s in slices if s.parent in spans]
    anchors += [_eff_end(i.closed) for i in xs]
```

(`spans` already carries the normalized end via `phase_span`, so `assign_lanes` and `_overlap_keys` need no further change.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tools/timeline/tests/test_render_lanes.py -k "end_of_day or distinct_lanes" -v`
Expected: PASS.

- [ ] **Step 5: Run the full timeline suite (catch regressions early)**

Run: `python3 -m pytest tools/timeline/tests -q`
Expected: PASS (some date-on-face / gap tests still pass here; they change in Tasks 3–5).

- [ ] **Step 6: Commit**

```bash
git add tools/timeline/render.py tools/timeline/tests/test_render_lanes.py
git commit -m "X29: end-of-day normalization for day-precision closes (Bug 1: legacy lanes)"
```

---

## Task 2: Effective instants for slice/X positioning + duration (F3)

**Files:**
- Modify: `tools/timeline/render.py` (`_duration_text`; the `els` construction for slice/X cards in `render_html`)
- Test: `tools/timeline/tests/test_render_rules.py`

- [ ] **Step 1: Write the failing test**

Append to `tools/timeline/tests/test_render_rules.py`:

```python
import datetime as dt
from timeline import model, render


def test_duration_positive_for_same_day_minute_start_day_close():
    started = model.DateValue(dt.datetime(2026, 5, 19, 23, 41, 0), "minute", "replay")
    closed = model.DateValue(dt.datetime(2026, 5, 19, 0, 0, 0), "day", "field")
    text = render._duration_text(started, closed)
    assert text.strip() != ""   # day/minute mixed -> "· 1 day", never empty
    assert "-" not in text       # never a negative/inverted duration


def test_duration_minute_pair_unchanged():
    started = model.DateValue(dt.datetime(2026, 5, 21, 17, 21, 0), "minute", "replay")
    closed = model.DateValue(dt.datetime(2026, 5, 21, 18, 15, 0), "minute", "replay")
    assert render._duration_text(started, closed) == " · 0h 54m"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tools/timeline/tests/test_render_rules.py -k duration -v`
Expected: FAIL — `test_duration_positive...` returns "" (current code computes `closed.when - started.when` = negative → `total <= 0` → "").

- [ ] **Step 3: Use effective instants in `_duration_text` and slice/X positioning**

Replace the head of `_duration_text` (currently `if started.when is None or closed.when is None: return ""` then `delta = closed.when - started.when`):

```python
def _duration_text(started, closed):
    start_eff = started.when            # starts stay at 00:00 for day precision
    close_eff = _eff_end(closed)        # ends resolve to end-of-day
    if start_eff is None or close_eff is None:
        return ""
    delta = close_eff - start_eff
    total = int(delta.total_seconds())
    if total <= 0:
        return ""
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if started.precision == "day" or closed.precision == "day":
        d = max(days, 1)
        return f" · {d} day{'s' if d != 1 else ''}"
    if days:
        return f" · {days}d {hours}h"
    return f" · {hours}h {minutes:02d}m"
```

Normalize the slice/X card `when` used for positioning. In `render_html`, the slice loop builds `_El(s.key, "card", s.closed.when, ...)`; the X loop uses `i.closed.when`. Change both to `_eff_end(...)` and sort by the effective instant:

```python
    for s in sorted(slices, key=lambda i: _eff_end(i.closed)):
        ...
        els.append(_El(s.key, "card", _eff_end(s.closed),
                       (("L" if side == "left" else "R", 14), ("C", 7)),
                       phase=s.parent, item=s, side=side))
    ...
    for n, i in enumerate(sorted(xs, key=lambda i: _eff_end(i.closed))):
        side = "left" if n % 2 == 0 else "right"
        els.append(_El(i.key, "card", _eff_end(i.closed),
                       (("L" if side == "left" else "R", 14), ("C", 7)),
                       item=i, side=side))
```

(The card *label* still calls `_fmt(item.closed)` — raw date, no fabricated time. Unchanged in this task; removed from the face in Task 5.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tools/timeline/tests/test_render_rules.py -k duration -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/timeline/render.py tools/timeline/tests/test_render_rules.py
git commit -m "X29: effective instants for duration + slice/X positioning (F3)"
```

---

## Task 3: Day-walk classifier replaces hour-threshold gaps (Bug 2 + feature core)

**Files:**
- Modify: `tools/timeline/render.py` (add `QUIET_RUN_DAYS` + `classify_days`; remove `quiet_gaps`, `GAP_THRESHOLD_HOURS`)
- Test: `tools/timeline/tests/test_render_lanes.py`

- [ ] **Step 1: Write the failing test**

Append to `tools/timeline/tests/test_render_lanes.py`:

```python
from datetime import date


def test_classify_days_active_short_idle_and_quiet_run():
    active = {date(2026, 5, 19), date(2026, 5, 21), date(2026, 6, 5)}
    out = render.classify_days(active)
    # 19th active; 20th is a 1-day idle -> own day marker; 21st active;
    # 22 May..4 Jun is a 14-day idle run (>=3) -> single quiet; 5 Jun active.
    assert [e[0] for e in out] == ["day", "day", "day", "quiet", "day"]
    assert out[0] == ("day", date(2026, 5, 19), True)
    assert out[1] == ("day", date(2026, 5, 20), False)   # short idle pill
    assert out[2] == ("day", date(2026, 5, 21), True)
    assert out[3][0] == "quiet" and out[3][3] == 14       # 14 quiet days
    assert out[4] == ("day", date(2026, 6, 5), True)


def test_classify_days_two_day_idle_not_collapsed():
    active = {date(2026, 5, 19), date(2026, 5, 22)}       # 20,21 idle = 2 days < 3
    out = render.classify_days(active)
    assert [e[0] for e in out] == ["day", "day", "day", "day"]
    assert out[1][2] is False and out[2][2] is False      # both idle pills


def test_classify_days_three_day_idle_collapses():
    active = {date(2026, 5, 19), date(2026, 5, 23)}       # 20,21,22 idle = 3 days
    out = render.classify_days(active)
    assert [e[0] for e in out] == ["day", "quiet", "day"]
    assert out[1][3] == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tools/timeline/tests/test_render_lanes.py -k classify -v`
Expected: FAIL — `render.classify_days` does not exist.

- [ ] **Step 3: Add `QUIET_RUN_DAYS` + `classify_days`; remove the hour-threshold API**

Near the top constants (replace `GAP_THRESHOLD_HOURS = 24`):

```python
QUIET_RUN_DAYS = 3      # a run of >= this many idle days collapses to one segment
```

Delete the `quiet_gaps(...)` function (lines ~121–145) and the `_gap_bounds(...)` function (lines ~230–243) — both are superseded. Add `classify_days` where `quiet_gaps` was:

```python
def classify_days(active_dates):
    """Walk the inclusive calendar range over the active-day set and classify
    each day. Returns an ordered list of:
      ("day", date, is_active)                  -- a date marker (pill + divider)
      ("quiet", run_start, run_end, n_days)     -- a collapsed run of >= QUIET_RUN_DAYS idle days
    Idle runs only occur strictly between active days (the range is framed by the
    first and last active day), so there is never a leading/trailing idle run.
    """
    if not active_dates:
        return []
    days = sorted(active_dates)
    lo, hi, active = days[0], days[-1], set(days)
    out, run = [], []
    one = dt.timedelta(days=1)
    d = lo
    while d <= hi:
        if d in active:
            if run:
                if len(run) >= QUIET_RUN_DAYS:
                    out.append(("quiet", run[0], run[-1], len(run)))
                else:
                    out.extend(("day", r, False) for r in run)
                run = []
            out.append(("day", d, True))
        else:
            run.append(d)
        d += one
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tools/timeline/tests/test_render_lanes.py -k classify -v`
Expected: PASS.

- [ ] **Step 5: Remove now-dead references and confirm import health**

Any test referencing `quiet_gaps` / `_gap_bounds` / `GAP_THRESHOLD_HOURS` tests a retired API; update or delete it.

Run: `grep -rn "quiet_gaps\|_gap_bounds\|GAP_THRESHOLD_HOURS" tools/timeline`
Expected after fixes: no matches in `render.py` or live tests (only historical mentions in committed reviewer docs).

Run (from repo root): `python3 -c "import sys; sys.path.insert(0,'tools'); import timeline.render"`
Expected: no ImportError / NameError.

- [ ] **Step 6: Commit**

```bash
git add tools/timeline/render.py tools/timeline/tests/test_render_lanes.py
git commit -m "X29: day-walk classifier; retire hour-threshold quiet_gaps (Bug 2)"
```

---

## Task 4: Render date pills, dividers, and quiet segments (dual-direction, X-aware)

**Files:**
- Modify: `tools/timeline/render.py` (`render_html` — build date-marker `_El`s, render markers + quiet segments; add `_RANK` entry; add CSS to `_SHELL`)
- Test: `tools/timeline/tests/test_render_html.py`, `tools/timeline/tests/test_render_direction.py`

- [ ] **Step 1: Write the failing tests**

Append to `tools/timeline/tests/test_render_html.py`:

```python
import re


def test_date_pills_and_dividers_render_with_quiet_run():
    items = [
        model._item("P1", "phase", None,
                    phase("P1", status="done", started="2026-05-19", closed="2026-06-05")),
        model._item("P1.S1", "slice", "P1",
                    slice_("S1", status="done", closed="2026-05-19", title="First slice")),
        model._item("P1.S2", "slice", "P1",
                    slice_("S2", status="done", closed="2026-06-05", title="Later slice")),
    ]
    html = render.render_html("fixture", items, generated=GEN).html
    assert 'class="date-pill' in html and 'class="day-divider' in html
    # active days 19 May and 5 Jun get pills; the 20 May..4 Jun run collapses
    assert re.search(r'class="date-pill[^>]*>19 May 2026<', html)
    assert re.search(r'class="date-pill[^>]*>5 Jun 2026<', html)
    assert "quiet day" in html


def test_x_only_day_gets_pill_even_when_hidden():
    items = [
        model._item("P1", "phase", None,
                    phase("P1", status="done", started="2026-05-19", closed="2026-05-19")),
        model._item("P1.S1", "slice", "P1",
                    slice_("S1", status="done", closed="2026-05-19")),
        model._item("X1", "x", None,
                    x("X1", status="done", closed="2026-05-25", title="Cross item")),
    ]
    html = render.render_html("fixture", items, generated=GEN, show_x=False).html
    # X-only day 25 May is active -> a date pill, even though X cards are CSS-hidden
    assert re.search(r'class="date-pill[^>]*>25 May 2026<', html)
```

Append to `tools/timeline/tests/test_render_direction.py` (reuses its `_tops` helper):

```python
def test_date_pills_carry_both_direction_tops():
    items = [
        model._item("P1", "phase", None,
                    phase("P1", status="done", started="2026-06-01", closed="2026-06-02")),
        model._item("P1.S1", "slice", "P1", slice_("S1", status="done", closed="2026-06-01")),
    ]
    html = render.render_html("fixture", items, generated=GEN).html
    asc = _tops(html, "date-pill", "data-ta")
    desc = _tops(html, "date-pill", "data-td")
    assert asc and desc and set(asc) == set(desc)   # every pill has both tops
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tools/timeline/tests/test_render_html.py tools/timeline/tests/test_render_direction.py -k "date_pill or x_only or both_direction" -v`
Expected: FAIL — no `date-pill` / `day-divider` markup exists yet.

- [ ] **Step 3: Build active-day set (X-aware), add date markers to layout, render markers + quiet segments**

In `render_html`, after `els` is fully populated but **before** the `layout(...)` calls, compute the X-aware active-day set and add date-marker elements:

```python
    # Active days = every embedded point event's local date, including ALL X
    # closes regardless of --show-x (X data is always embedded; visibility is a
    # client-side CSS toggle). F1 invariant: an X-only day is active, so it always
    # gets a pill and is never folded into a quiet run.
    active_dates = set()
    for start, end, close_only in spans.values():
        if not close_only:
            active_dates.add(start.date())
        if end is not None:
            active_dates.add(end.date())
    for s in slices:
        if s.parent in spans:
            active_dates.add(_eff_end(s.closed).date())
    for i in xs:
        active_dates.add(_eff_end(i.closed).date())

    day_entries = classify_days(active_dates)

    # First-event instant per active day (anchors the marker); idle days use noon.
    first_instant = {}
    for e in els:
        d = e.when.date()
        if d not in first_instant or e.when < first_instant[d]:
            first_instant[d] = e.when

    date_marker = {}   # date -> _El (for quiet-segment bounds + rendering)
    for entry in day_entries:
        if entry[0] != "day":
            continue
        d = entry[1]
        anchor = first_instant.get(d) or dt.datetime.combine(d, dt.time(12, 0))
        m = _El(f"date-{d.isoformat()}", "date", anchor, (("C", 6),))
        date_marker[d] = m
        els.append(m)
```

Add `"date"` to the tie-break rank so a marker sorts above that day's items at equal y:

```python
_RANK = {"date": -1, "node": 0, "card": 1, "open": 1, "ring": 2}
```

(`layout()`'s node/ring forcing pass only touches elements with a `phase`; markers have `phase=None` and are placed by the generic sweep on track "C" — no other change to `layout`.)

After the existing strand/band rendering and **in place of** the old `gaps = quiet_gaps(...)` block, render date markers then quiet segments:

```python
    # Date pills + divider hairlines (one per "day" entry).
    for entry in day_entries:
        if entry[0] != "day":
            continue
        d = entry[1]
        m = date_marker[d]
        ta, td = tops(m)
        label = d.strftime("%-d %b %Y")
        parts.append(
            f'<div class="day-divider" data-key="div-{d.isoformat()}" '
            f'style="top:{td}px" data-ta="{ta}" data-td="{td}"></div>'
            f'<div class="date-pill" data-key="pill-{d.isoformat()}" '
            f'style="top:{td}px" data-ta="{ta}" data-td="{td}">{label}</div>')

    # Quiet runs: dotted segment hugging the content of the bracketing active days.
    # Bounds branch by direction (mirrors the retired _gap_bounds): in desc
    # (newest-first) the newer side is visually ABOVE; in asc the older side is.
    active_sorted = sorted(date_marker)
    for entry in day_entries:
        if entry[0] != "quiet":
            continue
        run_start, run_end, ndays = entry[1], entry[2], entry[3]
        i = bisect.bisect_left(active_sorted, run_start)
        prev_d = active_sorted[i - 1] if i > 0 else None
        nxt_d = active_sorted[i] if i < len(active_sorted) else None
        if prev_d is None or nxt_d is None:
            continue
        bounds, ok = {}, True
        for dirn in ("asc", "desc"):
            if dirn == "desc":                       # newest-first
                above = [e for e in els if e.when.date() >= nxt_d]
                below = [e for e in els if e.when.date() <= prev_d]
            else:                                     # oldest-first
                above = [e for e in els if e.when.date() <= prev_d]
                below = [e for e in els if e.when.date() >= nxt_d]
            if not above or not below:
                ok = False
                break
            top = max(e.ys[dirn] + e.half() for e in above)
            bot = min(e.ys[dirn] - e.half() for e in below)
            if bot - top < 30:
                ok = False
                break
            bounds[dirn] = (top + 6 + PAD_TOP, bot - 6 + PAD_TOP)
        if not ok:
            continue
        ga0, ga1 = bounds["asc"]
        gd0, gd1 = bounds["desc"]
        parts.append(
            f'<div class="gap" data-key="quiet-{run_start.isoformat()}" '
            f'style="top:{gd0:.0f}px;height:{gd1 - gd0:.0f}px" '
            f'data-ta="{ga0:.0f}" data-ha="{ga1 - ga0:.0f}" '
            f'data-td="{gd0:.0f}" data-hd="{gd1 - gd0:.0f}"></div>'
            f'<div class="gap-label" data-key="quiet-{run_start.isoformat()}" '
            f'style="top:{(gd0 + gd1) / 2:.0f}px" '
            f'data-ta="{(ga0 + ga1) / 2:.0f}" data-td="{(gd0 + gd1) / 2:.0f}">'
            f'{ndays} quiet day{"s" if ndays != 1 else ""}</div>')
```

`bisect` is already imported at the top of `render.py`. Add CSS to `_SHELL` (alongside the existing `.gap` / `.gap-label` rules, which are kept):

```css
.day-divider{{position:absolute;left:0;right:0;height:1px;background:#ececef;
  transform:translateY(-50%);z-index:0}}
.date-pill{{position:absolute;left:50%;transform:translate(-50%,-50%);
  background:#fff;border:1px solid #d9d2f5;color:#6d28d9;font-size:10px;
  font-weight:700;padding:2px 8px;border-radius:11px;white-space:nowrap;z-index:4}}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tools/timeline/tests/test_render_html.py tools/timeline/tests/test_render_direction.py -k "date_pill or x_only or both_direction" -v`
Expected: PASS.

- [ ] **Step 5: Confirm the toggle script covers new elements + render smoke**

The existing `setDir(...)` script iterates `#wrap [data-ta]` and swaps `top` (and `height` when `data-hd` present). Date pills/dividers carry `data-ta`/`data-td` and no `data-hd`, so they flip with no script change. Verify on a real render:

Run: `python3 tools/timeline/timeline.py --repo . -o /tmp/x29-day-axis.html && grep -c 'class="date-pill' /tmp/x29-day-axis.html`
Expected: non-zero count; command exits 0.

- [ ] **Step 6: Commit**

```bash
git add tools/timeline/render.py tools/timeline/tests/test_render_html.py tools/timeline/tests/test_render_direction.py
git commit -m "X29: day-axis date pills, dividers, quiet-run segments (dual-direction, X-aware)"
```

---

## Task 5: Strip dates from card/node/ring faces (keep in popout)

**Files:**
- Modify: `tools/timeline/render.py` (`_card`, `_node_html`, `_ring_html`)
- Test: `tools/timeline/tests/test_render_html.py`

- [ ] **Step 1: Write the failing test**

Append to `tools/timeline/tests/test_render_html.py`:

```python
def test_card_face_has_no_date_but_detail_does():
    items = [
        model._item("P1", "phase", None,
                    phase("P1", status="done", started="2026-05-19", closed="2026-05-19")),
        model._item("P1.S1", "slice", "P1",
                    slice_("S1", status="done", closed="2026-05-19", title="Foo slice")),
    ]
    html = render.render_html("fixture", items, generated=GEN).html
    card = re.search(r'<div class="slice-card[^>]*data-key="P1\.S1".*?</div>\s*</div>',
                     html, re.S).group(0)
    face, _, detail = card.partition('<div class="detail"')
    assert "19 May 2026" not in face        # date stripped from the visible face
    assert "19 May 2026" in detail          # still in the click-to-expand popout
    assert "closed" in detail               # datetime + duration retained


def test_phase_node_and_ring_faces_have_no_inline_date():
    items = [model._item("P1", "phase", None,
                         phase("P1", status="done", started="2026-05-19", closed="2026-05-20"))]
    html = render.render_html("fixture", items, generated=GEN).html
    title = re.search(r'<div class="phase-title"[^>]*>(.*?)</div>', html, re.S).group(1)
    assert "May" not in title               # node title face carries no date
    ring = re.search(r'<div class="ring-label"[^>]*>(.*?)</div>', html, re.S).group(1)
    assert "May" not in ring and "complete" in ring
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tools/timeline/tests/test_render_html.py -k "no_date or no_inline_date" -v`
Expected: FAIL — faces currently include `_fmt(...)` dates.

- [ ] **Step 3: Remove date clauses from faces; keep detail/popout intact**

In `_card`, drop the date span from the visible face (the `detail` div already carries `started`/`closed`/duration). The face currently ends `...{_html.escape(item.label())}<span class="dim"> {_fmt(item.closed)}</span>{detail}</div>`:

```python
    return (f'<div class="{css} {side}" data-key="{key}" '
            f'title="{_html.escape(item.label())}" '
            f'onclick="this.classList.toggle(\'open\')" '
            f'style="top:{td}px;border-color:{color}66;background:{color}14" '
            f'{pos}>'
            f'<b>{key}</b> {_html.escape(item.label())}{detail}</div>'
            f'<div class="{dot_css} {side}-dot" data-key="{key}" '
            f'style="top:{td}px;margin-left:{off:.0f}px;background:{color}" '
            f'{pos}></div>')
```

In `_node_html`, drop the ` started <date>` clause (remove the `sd`/`clause` lines and their use):

```python
def _node_html(p, ta, td, off, color):
    key = _html.escape(p.key)
    pos = f'data-ta="{ta}" data-td="{td}"'
    return (f'<div class="phase-band" data-key="{key}" '
            f'style="top:{td}px;background:{color}0d" {pos}></div>'
            f'<div class="phase-node" data-key="{key}" '
            f'style="top:{td}px;margin-left:{off:.0f}px;background:{color}" '
            f'{pos}></div>'
            f'<div class="phase-title" data-key="{key}" '
            f'style="top:{td}px;color:{color}" {pos}>'
            f'{key} — {_html.escape(p.label())}</div>')
```

In `_ring_html`, drop the ` · {_fmt(p.closed)}` from the face (keep the "complete"/"cancelled" word):

```python
    return (f'<div class="phase-ring" data-key="{key}" '
            f'style="top:{td}px;margin-left:{off:.0f}px;border-color:{ring}" '
            f'{pos}></div>'
            f'<div class="ring-label" data-key="{key}" '
            f'style="top:{td}px;color:{ring}" {pos}>'
            f'{key} — {_html.escape(p.label())} {label}</div>')
```

- [ ] **Step 4: Update any base-spec tests that asserted a face date**

Run: `grep -rn "started \|complete ·\|class=\"dim\"> " tools/timeline/tests`
For each test asserting a date on a card/node/ring *face* (as opposed to the `.detail` popout), retarget it to the popout or delete it (the date moved to the day axis + popout). Note these as intended model changes for the post-slice reviewer.

- [ ] **Step 5: Run tests to verify pass**

Run: `python3 -m pytest tools/timeline/tests/test_render_html.py -k "no_date or no_inline_date" -v`
Expected: PASS.

Run: `python3 -m pytest tools/timeline/tests -q`
Expected: PASS (full timeline suite green).

- [ ] **Step 6: Commit**

```bash
git add tools/timeline/render.py tools/timeline/tests/test_render_html.py
git commit -m "X29: dates off card/node/ring faces; retained in popout + day axis"
```

---

## Task 6: Acceptance — re-render, full suite, visual sign-off

**Files:** none (verification only)

- [ ] **Step 1: Full default suite**

Run: `python3 -m pytest -q`
Expected: PASS. (If a pre-existing unrelated failure appears, confirm it reproduces on `main` before attributing it to X29 — the prior X29 acceptance found phantom full-suite failures that were a `SUPERSTAR_SUBAGENT_ROLE` artifact, not real.)

- [ ] **Step 2: Render this repo and inspect markup**

```bash
python3 tools/timeline/timeline.py --repo . -o /tmp/x29-superstar.html
grep -c 'class="date-pill' /tmp/x29-superstar.html   # > 0
grep -c 'quiet day' /tmp/x29-superstar.html          # >= 1 (a 3+ idle run collapsed)
```
Expected: P3 ∥ P4 lane separately; date pills present; at least one quiet segment; no dates on card faces.

- [ ] **Step 3: Render multistore (read-only) for the busier history**

```bash
python3 tools/timeline/timeline.py --repo /home/simon/Dev/sigreer/multistore -o /tmp/x29-multistore.html
```
Expected: exit 0; legacy day-precision phases lane correctly; day axis reads cleanly on a longer history. (Read-only render; no `backfill --write` here.)

- [ ] **Step 4: Human visual acceptance**

Ask the human partner to open `/tmp/x29-superstar.html` and `/tmp/x29-multistore.html` in a browser and confirm: parallel legacy lanes, dotted quiet-day segments, date pills on the spine, clean card faces, and the newest/oldest-first toggle flipping pills + dividers. This is the X29 close gate (carried over from the prior post-slice resolution).

- [ ] **Step 5: Final commit (if any verification-driven tweaks were made)**

```bash
git add -A tools/timeline
git commit -m "X29: day-axis acceptance — re-render + full suite green"
```

---

## Self-Review notes (author)

- **Spec coverage:** Part 1 end-of-day normalization → Tasks 1–2; `quiet_gaps` retirement + day-walk → Task 3; pills/dividers/quiet segments + X-aware active days + dual-direction → Task 4; dates-off-faces (popout retained) → Task 5; testing list (normalization, duration, classify boundaries, X-only, dates-off-faces, dual-direction) distributed across Tasks 1–5; acceptance (superstar + multistore + full suite + human sign-off) → Task 6. Spec-review F1 (X-only), F2 (quiet_gaps retired), F3 (duration) each have a dedicated test.
- **Type consistency:** `_eff_end` is the single helper name used in Tasks 1, 2, 4. `classify_days` returns the tuple shapes consumed verbatim in Task 4. `QUIET_RUN_DAYS` defined once (Task 3). `date-pill` / `day-divider` CSS classes and the kept `.gap`/`.gap-label` reuse are consistent across Task 4 markup and CSS.
- **Direction correctness (plan-review F1):** the quiet-run bounds branch on `asc`/`desc` exactly like the retired `_gap_bounds` — newer side is visually above in `desc`, older side above in `asc`.
- **Test layout (plan-review F2/F3):** every focused command targets a real module (`test_render_lanes.py`, `test_render_rules.py`, `test_render_html.py`, `test_render_direction.py`); imports use `from timeline import model, render` / `from timeline.tests.helpers import ...`; no new helper APIs are introduced.
- **Idle-pill positioning:** active days anchor at the day's first event instant; idle days at local noon mapped through the same scale (`first_instant.get(d) or noon`), matching the spec's Spacing clause.
- **Reviewer call-outs:** retired `quiet_gaps`/`_gap_bounds`/`GAP_THRESHOLD_HOURS` and base-spec face-date test changes are intended model changes — flag them to the post-slice reviewer (precedent: T5/T6 deviations).
