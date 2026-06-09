"""Visual-acceptance defect fixes (X29).

Defect 1: start/end label prominence — `.phase-title` and `.ring-label` must
share an identical font style, and start/end identity is conveyed by emoji
markers (racing car for start, chequered flag for end) rather than by a font
weight that moves with reading direction.

Defect 2: a central spine line must always be present (a full-height dotted
base spine), and consecutive rendered day-markers must keep a fixed, consistent
vertical gap regardless of how many short idle days separate them.
"""

import datetime as dt
import re

from timeline import model, render
from timeline.tests.helpers import phase, slice_

GEN = dt.datetime(2026, 6, 6, 12, 0)


def _phase(pid, **kw):
    return model._item(pid, "phase", None, phase(pid, **kw))


def _slice(pid, sid, **kw):
    return model._item(f"{pid}.{sid}", "slice", pid, slice_(sid, **kw))


def _tops(html, cls, attr="data-ta"):
    pat = re.compile(r'<div class="' + cls
                     + r'[^"]*" data-key="([^"]+)"[^>]*'
                     + attr + r'="(-?\d+)"')
    return {m.group(1): int(m.group(2)) for m in pat.finditer(html)}


# --- Defect 1: matching font + emoji markers -------------------------------

def test_phase_title_and_ring_label_share_font():
    p = _phase("P1", status="done", started="2026-06-01", closed="2026-06-02")
    h = render.render_html("t", [p], generated=GEN).html
    title = re.search(r"\.phase-title\{([^}]*)\}", h).group(1)
    ring = re.search(r"\.ring-label\{([^}]*)\}", h).group(1)
    title_fw = re.search(r"font-weight:(\d+)", title).group(1)
    ring_fw = re.search(r"font-weight:(\d+)", ring).group(1)
    title_fs = re.search(r"font-size:(\d+px)", title).group(1)
    ring_fs = re.search(r"font-size:(\d+px)", ring).group(1)
    assert title_fw == ring_fw, "start/end labels must share font-weight"
    assert title_fs == ring_fs, "start/end labels must share font-size"


def test_start_label_carries_racing_car_emoji():
    p = _phase("P1", status="done", started="2026-06-01", closed="2026-06-02",
               title="Big unit of work")
    h = render.render_html("t", [p], generated=GEN).html
    title = re.search(r'<div class="phase-title"[^>]*>(.*?)</div>', h, re.S).group(1)
    assert title.startswith("\U0001F3CE️ "), repr(title)


def test_end_label_carries_chequered_flag_emoji():
    p = _phase("P1", status="done", started="2026-06-01", closed="2026-06-02",
               title="Big unit of work")
    h = render.render_html("t", [p], generated=GEN).html
    ring = re.search(r'<div class="ring-label"[^>]*>(.*?)</div>', h, re.S).group(1)
    assert ring.startswith("\U0001F3C1 "), repr(ring)


def test_open_label_carries_racing_car_emoji():
    p = _phase("P9", status="ready", started="2026-06-05")
    h = render.render_html("t", [p], generated=GEN).html
    lbl = re.search(r'<div class="open-label"[^>]*>(.*?)</div>', h, re.S).group(1)
    assert lbl.startswith("\U0001F3CE️ "), repr(lbl)


# --- Defect 2A: always-present central spine -------------------------------

def test_base_spine_present_spanning_content():
    items = [
        _phase("P1", status="done", started="2026-06-01", closed="2026-06-02"),
        _slice("P1", "S1", status="done", closed="2026-06-01"),
        _phase("P2", status="done", started="2026-06-04", closed="2026-06-05"),
        _slice("P2", "S1", status="done", closed="2026-06-04"),
    ]
    h = render.render_html("t", items, generated=GEN).html
    m = re.search(r'<div class="base-spine"[^>]*data-ta="(-?\d+)" '
                  r'data-ha="(\d+)" data-td="(-?\d+)" data-hd="(\d+)"', h)
    assert m, "a full-height dotted base spine element must be present"
    ta, ha, td, hd = (int(g) for g in m.groups())
    # base-spine css must default to dotted at left:50%
    css = re.search(r"\.base-spine\{([^}]*)\}", h).group(1)
    assert "left:50%" in css and "dotted" in css
    # spans from near the top content to near the bottom content in both dirs
    for top, height in ((ta, ha), (td, hd)):
        all_tops = []
        for cls in ("phase-node", "phase-ring", "slice-card", "date-pill"):
            attr = "data-ta" if (top, height) == (ta, ha) else "data-td"
            all_tops += list(_tops(h, cls, attr).values())
        assert top <= min(all_tops) + 5
        assert top + height >= max(all_tops) - 5


# --- Defect 2B: consistent idle-day spacing --------------------------------

def _pill_gaps(html, attr):
    tops = sorted(_tops(html, "date-pill", attr).values())
    return [b - a for a, b in zip(tops, tops[1:])]


def test_short_idle_runs_keep_fixed_per_day_gap():
    # 19 May active, 20 May idle (1-day), 21 May active, 22+23 May idle (2-day),
    # 24 May active. Every consecutive rendered day must keep >= the fixed gap,
    # and per-day spacing must be roughly uniform across the 1-idle and 2-idle
    # stretches (no collapse to ~0).
    items = [
        _phase("P1", status="done", started="2026-05-19", closed="2026-05-24"),
        _slice("P1", "S1", status="done", closed="2026-05-19"),
        _slice("P1", "S2", status="done", closed="2026-05-21"),
        _slice("P1", "S3", status="done", closed="2026-05-24"),
    ]
    h = render.render_html("t", items, generated=GEN).html
    threshold = render.MIN_GAP_PX - 1
    pill_height = 16   # a date pill is ~16px tall
    for attr in ("data-ta", "data-td"):
        gaps = _pill_gaps(h, attr)
        assert len(gaps) == 5, (attr, gaps)        # 19..24 May -> 5 consecutive gaps
        # No idle-day collapse: every consecutive day clears the fixed threshold
        # and is comfortably larger than a single pill's height. (The scale anchors
        # every day-marker a uniform 24h apart; the per-direction collision sweep
        # may nudge the boundary pills next to the start node / end ring, so we
        # assert tight consistency rather than bit-exact equality.)
        assert all(g >= threshold for g in gaps), (attr, gaps)
        assert all(g > pill_height for g in gaps), (attr, gaps)
        assert max(gaps) <= 1.4 * min(gaps), (attr, gaps)


def test_quiet_run_still_collapses_with_label():
    # >=3-day idle run still collapses to one quiet segment + label, and does
    # NOT get per-day pills.
    items = [
        _phase("P1", status="done", started="2026-05-19", closed="2026-05-25"),
        _slice("P1", "S1", status="done", closed="2026-05-19"),
        _slice("P1", "S2", status="done", closed="2026-05-25"),
    ]
    h = render.render_html("t", items, generated=GEN).html
    assert "quiet day" in h
    assert re.search(r'class="gap"', h)
    pills = sorted(_tops(h, "date-pill").keys())
    # only the two active days get pills; the 5 idle days collapse
    assert pills == ["pill-2026-05-19", "pill-2026-05-25"]
