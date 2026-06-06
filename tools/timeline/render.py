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
