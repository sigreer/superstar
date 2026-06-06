"""Render TimelineItem records to a single self-contained HTML page."""

from __future__ import annotations

import bisect
import datetime as dt
import html as _html

PALETTE = ["#7c5cff", "#10ac84", "#ff9f43", "#4cc2ff",
           "#ee5253", "#f368e0", "#01a3a4", "#feca57"]
SLATE = "#8395a7"
PX_PER_HOUR = 3.0
MIN_GAP_PX = 34     # bursts expand to at least this much per adjacent pair
MAX_GAP_PX = 140    # quiet stretches compress to at most this much
GAP_THRESHOLD_HOURS = 24


def _done_slices(phase_key, items):
    return [i for i in items
            if i.kind == "slice" and i.parent == phase_key and i.status == "done"]


def visible_items(items):
    """Apply the spec's display rules; preserves input order."""
    out = []
    for it in items:
        if it.excluded:
            continue
        if it.kind == "phase":
            if it.status == "cancelled" and not _done_slices(it.key, items):
                continue
            out.append(it)
        elif it.kind == "slice":
            if it.status != "done" or it.closed.when is None:
                continue
            parent = next((p for p in items if p.key == it.parent), None)
            if parent and parent.excluded:
                continue
            out.append(it)
        else:  # x
            if it.status == "done" and it.closed.when is not None:
                out.append(it)
    return out


def phase_span(phase, items):
    """-> (start|None, end|None, close_only). end None means the phase is open.

    close_only is True when no resolvable start exists. When the phase has no
    `started`, the earliest slice activity (start OR close) is used: a slice
    closing proves the phase was active by then, and legacy phases often have
    slice closes but no slice starts (multistore P11)."""
    start = phase.started.when
    if start is None:
        slice_dates = [d for s in items
                       if s.kind == "slice" and s.parent == phase.key
                       for d in (s.started.when, s.closed.when)
                       if d is not None]
        start = min(slice_dates) if slice_dates else None
    if start is None:
        start = phase.created.when
    end = phase.closed.when
    return start, end, start is None


class TimeScale:
    """Piecewise-linear time->y mapping: proportional between anchor events,
    clamped per adjacent pair to [MIN_GAP_PX, MAX_GAP_PX]."""

    def __init__(self, timestamps, px_per_hour=PX_PER_HOUR,
                 min_gap=MIN_GAP_PX, max_gap=MAX_GAP_PX):
        self._anchors = sorted(set(timestamps))
        self._ys = []
        y = 0.0
        for i, t in enumerate(self._anchors):
            if i:
                hours = (t - self._anchors[i - 1]).total_seconds() / 3600.0
                y += min(max(hours * px_per_hour, min_gap), max_gap)
            self._ys.append(y)

    def y(self, when):
        i = bisect.bisect_left(self._anchors, when)
        if i < len(self._anchors) and self._anchors[i] == when:
            return self._ys[i]
        if i == 0:
            return self._ys[0] if self._ys else 0.0
        if i == len(self._anchors):
            return self._ys[-1]
        a0, a1 = self._anchors[i - 1], self._anchors[i]
        frac = (when - a0).total_seconds() / (a1 - a0).total_seconds()
        return self._ys[i - 1] + frac * (self._ys[i] - self._ys[i - 1])

    @property
    def height(self):
        return (self._ys[-1] if self._ys else 0.0) + 80.0


def assign_lanes(spans):
    """Greedy interval lane assignment for phase strands.

    spans: iterable of (key, start, end) with start/end datetimes (end may be
    None for an open phase — treat as datetime.max for packing).
    -> ({key: lane}, lane_count)
    """
    assignment, lane_ends = {}, []
    inf = dt.datetime.max
    ordered = sorted(spans, key=lambda s: (s[1], s[2] or inf))
    for key, start, end in ordered:
        end = end or inf
        for lane, lane_end in enumerate(lane_ends):
            if start >= lane_end:
                lane_ends[lane] = end
                assignment[key] = lane
                break
        else:
            lane_ends.append(end)
            assignment[key] = len(lane_ends) - 1
    return assignment, len(lane_ends)


def quiet_gaps(intervals, threshold_hours=GAP_THRESHOLD_HOURS, anchors=()):
    """Merge phase coverage intervals; return gaps longer than the threshold.

    intervals: list of (start, end) datetimes (end None = open: covers to max).
    anchors: datetimes of every rendered point event (slice closes, X closes,
    phase boundaries). Each anchor counts as zero-length coverage, so a
    reported gap can never contain a rendered item — an anchor inside a hole
    splits it.
    -> list of (gap_start, gap_end)
    """
    intervals = list(intervals) + [(a, a) for a in anchors]
    if not intervals:
        return []
    inf = dt.datetime.max
    merged = []
    for start, end in sorted((s, e or inf) for s, e in intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    gaps = []
    for (s0, e0), (s1, e1) in zip(merged, merged[1:]):
        if (s1 - e0).total_seconds() / 3600.0 > threshold_hours:
            gaps.append((e0, s1))
    return gaps


from dataclasses import dataclass as _dataclass


@_dataclass
class RenderResult:
    html: str
    unplaced: list


def _color(phase_key):
    try:
        return PALETTE[int(phase_key.lstrip("PX")) % len(PALETTE)]
    except ValueError:
        return SLATE


def _fmt(dv):
    if dv.when is None:
        return "—"
    if dv.precision == "minute":
        return dv.when.strftime("%-d %b %Y, %H:%M")
    return dv.when.strftime("%-d %b %Y")


def render_html(project, items, *, generated, show_x=False):
    vis = visible_items(items)
    phases = [i for i in vis if i.kind == "phase"]
    slices = [i for i in vis if i.kind == "slice"]
    xs = [i for i in vis if i.kind == "x"]

    spans, unplaced = {}, []
    for p in phases:
        start, end, close_only = phase_span(p, items)
        if start is None and end is None:
            unplaced.append(p.key)
            continue
        spans[p.key] = (start or end, end, close_only)
    placeable_phases = [p for p in phases if p.key in spans]

    anchors = []
    for start, end, _ in spans.values():
        anchors.append(start)
        anchors.append(end or generated)
    anchors += [s.closed.when for s in slices if s.parent in spans]
    anchors += [i.closed.when for i in xs]
    if not anchors:
        anchors = [generated]
    scale = TimeScale(anchors)
    span_text = (f"{min(anchors).strftime('%-d %b %Y')} – {max(anchors).strftime('%-d %b %Y')}"
                 if len(anchors) > 1 else "")

    lane_of, lane_count = assign_lanes(
        [(k, s, e) for k, (s, e, _) in spans.items()])
    overlapping = _overlap_keys(spans)
    strand_off = lambda lane: (lane - (lane_count - 1) / 2) * 12

    parts = []
    # Strands + phase nodes + close rings.
    for p in placeable_phases:
        start, end, close_only = spans[p.key]
        color = _color(p.key)
        off = strand_off(lane_of[p.key])
        y0, y1 = scale.y(start), scale.y(end or generated)
        if not close_only:
            parts.append(
                f'<div class="strand" style="top:{y0:.0f}px;'
                f'height:{max(y1 - y0, 2):.0f}px;'
                f'margin-left:{off:.0f}px;background:{color}"></div>')
            parts.append(_phase_start_node(p, y0, off, color))
        if end is not None:
            ring = "#9aa0a6" if p.status == "cancelled" else color
            label = "cancelled" if p.status == "cancelled" else "complete"
            parts.append(
                f'<div class="phase-ring" style="top:{y1:.0f}px;'
                f'margin-left:{off:.0f}px;border-color:{ring}"></div>'
                f'<div class="ring-label" style="top:{y1:.0f}px;color:{ring}">'
                f'{_html.escape(p.key)} — {_html.escape(p.label())} {label} · {_fmt(p.closed)}</div>')
        else:
            parts.append(
                f'<div class="open-label" style="top:{y1 + 24:.0f}px;'
                f'color:{color}">{_html.escape(p.key)} in progress…</div>')

    # Quiet gaps.
    for gap_start, gap_end in quiet_gaps(
            [(s, e) for s, e, _ in spans.values()], anchors=anchors):
        gy0, gy1 = scale.y(gap_start), scale.y(gap_end)
        days = max(1, round((gap_end - gap_start).total_seconds() / 86400))
        parts.append(
            f'<div class="gap" style="top:{gy0:.0f}px;'
            f'height:{gy1 - gy0:.0f}px"></div>'
            f'<div class="gap-label" style="top:{(gy0 + gy1) / 2:.0f}px">'
            f'{days} quiet day{"s" if days != 1 else ""}</div>')

    # Slice cards: phase owns a side while overlapping, else alternate.
    counters = {}
    for s in sorted(slices, key=lambda i: i.closed.when):
        if s.parent not in spans:
            unplaced.append(s.key)
            continue
        color = _color(s.parent)
        n = counters[s.parent] = counters.get(s.parent, -1) + 1
        if s.parent in overlapping:
            side = "left" if lane_of[s.parent] % 2 == 0 else "right"
        else:
            side = "left" if n % 2 == 0 else "right"
        parts.append(_card(s, scale.y(s.closed.when), side, color,
                           strand_off(lane_of[s.parent]), css="slice-card"))

    # X-items: neutral, alternating, hidden unless body.show-x.
    for n, i in enumerate(sorted(xs, key=lambda i: i.closed.when)):
        side = "left" if n % 2 == 0 else "right"
        parts.append(_card(i, scale.y(i.closed.when), side, SLATE, 0,
                           css="slice-card x-node"))

    legend = "".join(
        f'<span class="chip"><i style="background:{_color(p.key)}"></i>'
        f'{_html.escape(p.key)}</span>' for p in placeable_phases)
    done_slices = len(slices)
    body_class = "show-x" if show_x else ""
    html_out = _SHELL.format(
        project=_html.escape(project), legend=legend, span=span_text,
        n_phases=sum(1 for p in placeable_phases if p.status == "done"),
        n_slices=done_slices, height=int(scale.height),
        generated=generated.strftime("%-d %b %Y %H:%M"),
        body_class=body_class, checked="checked" if show_x else "",
        content="\n".join(parts))
    return RenderResult(html_out, unplaced)


def _overlap_keys(spans):
    keys = list(spans)
    out = set()
    inf = dt.datetime.max
    for i, a in enumerate(keys):
        s0, e0, _ = spans[a]
        for b in keys[i + 1:]:
            s1, e1, _ = spans[b]
            if s0 < (e1 or inf) and s1 < (e0 or inf):
                out.update((a, b))
    return out


def _phase_start_node(p, y, off, color):
    sd = p.started if p.started.when else p.created
    clause = f'<span class="dim"> started {_fmt(sd)}</span>' if sd.when else ""
    return (f'<div class="phase-node" style="top:{y:.0f}px;'
            f'margin-left:{off:.0f}px;background:{color}"></div>'
            f'<div class="phase-title" style="top:{y:.0f}px">'
            f'{_html.escape(p.key)} — {_html.escape(p.label())}{clause}</div>')


def _duration_text(started, closed):
    if started.when is None or closed.when is None:
        return ""
    delta = closed.when - started.when
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


def _card(item, y, side, color, off, css):
    started_clause = (f'started {_fmt(item.started)} · '
                      if item.started.when else "")
    detail = (f'<div class="detail">{_html.escape(item.key)} · '
              f'{_html.escape(item.title)}<br>'
              f'{started_clause}closed {_fmt(item.closed)}'
              f'{_duration_text(item.started, item.closed)}</div>')
    dot_css = "dot x-node" if "x-node" in css else "dot"
    return (f'<div class="{css} {side}" title="{_html.escape(item.label())}" '
            f'onclick="this.classList.toggle(\'open\')" '
            f'style="top:{y:.0f}px;border-color:{color}66;background:{color}14">'
            f'<b>{_html.escape(item.key)}</b> {_html.escape(item.label())}'
            f'<span class="dim"> {_fmt(item.closed)}</span>{detail}</div>'
            f'<div class="{dot_css} {side}-dot" '
            f'style="top:{y:.0f}px;margin-left:{off:.0f}px;background:{color}"></div>')


_SHELL = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{project} — timeline</title>
<style>
body{{font-family:system-ui,sans-serif;background:#fafafa;color:#333;margin:0}}
header{{position:sticky;top:0;background:#fff;border-bottom:1px solid #e5e5e5;
  padding:14px 28px;z-index:10}}
header h1{{font-size:18px;margin:0 0 4px}}
header .meta{{font-size:12px;color:#888}}
.chip{{font-size:11px;margin-right:10px;color:#555}}
.chip i{{display:inline-block;width:9px;height:9px;border-radius:50%;
  margin-right:4px}}
#wrap{{position:relative;max-width:980px;margin:30px auto;height:{height}px}}
.strand{{position:absolute;left:50%;width:4px;border-radius:2px;
  transform:translateX(-50%)}}
.phase-node{{position:absolute;left:50%;width:18px;height:18px;
  border-radius:50%;border:3px solid #fff;transform:translate(-50%,-50%);
  box-shadow:0 0 0 2px currentColor;z-index:3}}
.phase-ring{{position:absolute;left:50%;width:14px;height:14px;
  border-radius:50%;background:#fff;border:3px solid;
  transform:translate(-50%,-50%);z-index:3}}
.phase-title{{position:absolute;left:50%;margin-left:26px;font-size:13px;
  font-weight:700;transform:translateY(-50%);max-width:40%}}
.ring-label{{position:absolute;right:50%;margin-right:26px;font-size:11px;
  font-weight:600;transform:translateY(-50%)}}
.open-label{{position:absolute;left:50%;margin-left:26px;font-size:11px;
  font-style:italic;transform:translateY(-50%)}}
.dim{{color:#999;font-weight:400;font-size:11px}}
.gap{{position:absolute;left:50%;border-left:3px dotted #aaa;
  transform:translateX(-50%)}}
.gap-label{{position:absolute;left:50%;margin-left:14px;font-size:10px;
  color:#999;font-style:italic;transform:translateY(-50%)}}
.slice-card{{position:absolute;max-width:38%;font-size:12px;cursor:pointer;
  border:1px solid;border-radius:6px;padding:6px 10px;
  transform:translateY(-50%);z-index:2;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.slice-card:hover,.slice-card.open{{white-space:normal;overflow:visible;
  text-overflow:clip;z-index:6;background:#fff!important}}
.slice-card.left{{right:50%;margin-right:22px;text-align:right}}
.slice-card.right{{left:50%;margin-left:22px}}
.dot{{position:absolute;left:50%;width:11px;height:11px;border-radius:50%;
  transform:translate(-50%,-50%);z-index:3}}
.detail{{display:none;margin-top:6px;padding-top:6px;
  border-top:1px solid rgba(0,0,0,.1);font-size:11px;color:#666}}
.slice-card.open .detail{{display:block}}
.x-node{{display:none}}
body.show-x .x-node{{display:block}}
body.show-x .dot.x-node{{display:block}}
label.xtoggle{{font-size:12px;color:#555;float:right;cursor:pointer}}
</style></head>
<body class="{body_class}">
<header><h1>{project} — work timeline</h1>
<div class="meta">{span} · {n_phases} phases · {n_slices} slices completed ·
generated {generated}
<label class="xtoggle"><input type="checkbox" id="showX" {checked}
onchange="document.body.classList.toggle('show-x',this.checked)">
show cross-cutting items</label></div>
<div>{legend}</div></header>
<div id="wrap">
{content}
</div></body></html>
"""
