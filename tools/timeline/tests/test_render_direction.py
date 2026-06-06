"""Direction toggle: default newest-at-top, in-page switch to oldest-first.

Every positioned element carries data-ta (first-to-last top) and data-td
(last-to-first top). The emitted inline style uses the data-td value — the
default reading order — and the toggle's inline script swaps tops.
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


def _tops(html, cls, attr):
    pat = re.compile(r'<div class="' + cls
                     + r'[^"]*" data-key="([^"]+)"[^>]*'
                     + attr + r'="(-?\d+)"')
    return {m.group(1): int(m.group(2)) for m in pat.finditer(html)}


def _two_phases():
    p1 = _phase("P1", status="done", started="2026-06-01", closed="2026-06-02")
    s1 = _slice("P1", "S1", status="done", closed="2026-06-01")
    p2 = _phase("P2", status="done", started="2026-06-04", closed="2026-06-05")
    s2 = _slice("P2", "S1", status="done", closed="2026-06-04")
    return [p1, s1, p2, s2]


def test_default_reading_order_is_newest_at_top():
    h = render.render_html("t", _two_phases(), generated=GEN).html
    td = _tops(h, "phase-ring", "data-td")
    ta = _tops(h, "phase-ring", "data-ta")
    assert td["P2"] < td["P1"]      # newer phase above in the default order
    assert ta["P1"] < ta["P2"]      # toggled order is oldest-first
    # The emitted inline top is the default (newest-first) value.
    m = re.search(r'<div class="phase-ring" data-key="P2" '
                  r'style="top:(\d+)px', h)
    assert m and int(m.group(1)) == td["P2"]


def test_phase_node_precedes_children_in_default_order_too():
    # The header-before-contents rule holds in BOTH reading orders: in
    # newest-at-top mode each phase block still opens with its node/title.
    items = _two_phases()
    h = render.render_html("t", items, generated=GEN).html
    for attr in ("data-ta", "data-td"):
        nodes = _tops(h, "phase-node", attr)
        cards = _tops(h, "slice-card", attr)
        rings = _tops(h, "phase-ring", attr)
        for pk in ("P1", "P2"):
            kid = cards[f"{pk}.S1"]
            assert nodes[pk] < kid, attr
            assert rings[pk] > kid, attr


def test_direction_toggle_markup_and_script():
    h = render.render_html("t", _two_phases(), generated=GEN).html
    assert 'id="dirNewest"' in h
    assert re.search(r'<input type="checkbox" id="dirNewest" checked', h)
    assert "function setDir" in h
    # Still self-contained: the script is inline, no external fetches.
    assert "http://" not in h and "https://" not in h and "src=" not in h


def test_range_elements_carry_both_heights():
    items = _two_phases()
    h = render.render_html("t", items, generated=GEN).html
    m = re.search(r'<div class="strand" data-key="P1"[^>]*data-ta="(-?\d+)" '
                  r'data-ha="(\d+)" data-td="(-?\d+)" data-hd="(\d+)"', h)
    assert m, "strand must carry per-direction top and height"
    # The strand covers node..ring in both directions.
    for top_attr, h_attr in (("data-ta", "data-ha"), ("data-td", "data-hd")):
        nodes = _tops(h, "phase-node", top_attr)
        rings = _tops(h, "phase-ring", top_attr)
        sm = re.search(r'<div class="strand" data-key="P1"[^>]*'
                       + top_attr + r'="(-?\d+)"[^>]*'
                       + h_attr + r'="(\d+)"', h)
        top, height = int(sm.group(1)), int(sm.group(2))
        assert top == nodes["P1"]
        assert top + height == rings["P1"]


def test_open_phase_block_reads_header_first_in_default_order():
    p = _phase("P9", status="ready", started="2026-06-05")
    s = _slice("P9", "S1", status="done", closed="2026-06-05")
    h = render.render_html("t", [p, s], generated=GEN).html
    nodes = _tops(h, "phase-node", "data-td")
    cards = _tops(h, "slice-card", "data-td")
    assert nodes["P9"] < cards["P9.S1"]
