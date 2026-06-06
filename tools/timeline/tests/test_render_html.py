import datetime as dt

from timeline import model, render
from timeline.tests.helpers import phase, slice_, x

GEN = dt.datetime(2026, 6, 6, 12, 0)


def _items():
    p20 = model._item("P20", "phase", None,
                      phase("P20", status="done", started="2026-05-29",
                            closed="2026-05-30", title="Marketing library"))
    s1 = model._item("P20.S1", "slice", "P20",
                     slice_("S1", status="done", closed="2026-05-29",
                            title="Component inventory"))
    p1 = model._item("P1", "phase", None,
                     phase("P1", status="done", closed="2026-04-29",
                           title="Legacy close-only"))
    x1 = model._item("X1", "x", None,
                     x("X1", status="done", closed="2026-05-29",
                       title="Cross item"))
    open_p = model._item("P23", "phase", None,
                         phase("P23", status="ready", started="2026-06-05",
                               title="Open phase"))
    return [p1, p20, s1, x1, open_p]


def test_render_produces_selfcontained_html():
    result = render.render_html("fixture", _items(), generated=GEN)
    h = result.html
    assert h.startswith("<!DOCTYPE html>")
    for needle in ("Marketing library", "Component inventory", "Cross item",
                   "phase-node", "slice-card", "x-node", "showX",
                   "Legacy close-only", "Open phase"):
        assert needle in h
    # Self-contained: no external fetches.
    assert "http://" not in h and "https://" not in h and "src=" not in h


def test_day_precision_shows_no_time_minute_shows_time():
    items = _items()
    items[2].closed = model.DateValue(dt.datetime(2026, 5, 29, 10, 14),
                                      "minute", "replay")
    h = render.render_html("fixture", items, generated=GEN).html
    assert "10:14" in h
    h2 = render.render_html("fixture", _items(), generated=GEN).html
    assert "00:00" not in h2  # day precision never fakes a midnight time


def test_show_x_flag_sets_initial_body_class():
    off = render.render_html("fixture", _items(), generated=GEN).html
    on = render.render_html("fixture", _items(), generated=GEN, show_x=True).html
    assert '<body class="">' in off
    assert '<body class="show-x">' in on


def test_unplaced_items_reported_not_rendered():
    dateless = model._item("P99", "phase", None, phase("P99", status="ready"))
    result = render.render_html("fixture", _items() + [dateless], generated=GEN)
    assert "P99" in result.unplaced
    assert "P99" not in result.html


def test_x_dot_hidden_with_card():
    h = render.render_html("fixture", _items(), generated=GEN).html
    assert 'class="dot x-node' in h  # the X dot toggles with the card


def test_detail_includes_duration():
    items = _items()
    items[2].started = model.DateValue(dt.datetime(2026, 5, 29, 8, 0),
                                       "minute", "replay")
    items[2].closed = model.DateValue(dt.datetime(2026, 5, 29, 10, 14),
                                      "minute", "replay")
    h = render.render_html("fixture", items, generated=GEN).html
    assert "2h 14m" in h


def test_header_shows_date_span():
    h = render.render_html("fixture", _items(), generated=GEN).html
    assert "29 Apr 2026" in h and "6 Jun 2026" in h


def test_html_escapes_titles():
    bad = model._item("X5", "x", None,
                      x("X5", status="done", closed="2026-05-29",
                        title="<script>alert(1)</script>"))
    h = render.render_html("fixture", _items() + [bad], generated=GEN).html
    assert "<script>alert(1)</script>" not in h
    assert "&lt;script&gt;" in h


def test_card_title_attribute_carries_full_title():
    h = render.render_html("fixture", _items(), generated=GEN).html
    assert 'title="Component inventory"' in h
    assert 'title="Cross item"' in h


def test_card_title_attribute_escapes_malicious_titles():
    bad = model._item("X6", "x", None,
                      x("X6", status="done", closed="2026-05-29",
                        title='"x" onmouseover="alert(1)"'))
    h = render.render_html("fixture", _items() + [bad], generated=GEN).html
    assert 'onmouseover="alert(1)"' not in h
    assert "&quot;x&quot; onmouseover=&quot;alert(1)&quot;" in h


def test_card_truncation_css_present():
    h = render.render_html("fixture", _items(), generated=GEN).html
    assert "white-space:nowrap" in h
    assert "overflow:hidden" in h
    assert "text-overflow:ellipsis" in h


def test_card_hover_and_open_untruncate():
    h = render.render_html("fixture", _items(), generated=GEN).html
    assert ".slice-card:hover,.slice-card.open{" in h
    assert "white-space:normal" in h
