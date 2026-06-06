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

    close_only is True when no resolvable start exists."""
    start = phase.started.when
    if start is None:
        slice_starts = [s.started.when for s in items
                        if s.kind == "slice" and s.parent == phase.key
                        and s.started.when]
        start = min(slice_starts) if slice_starts else None
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


def quiet_gaps(intervals, threshold_hours=GAP_THRESHOLD_HOURS):
    """Merge phase coverage intervals; return gaps longer than the threshold.

    intervals: list of (start, end) datetimes (end None = open: covers to max).
    -> list of (gap_start, gap_end)
    """
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
