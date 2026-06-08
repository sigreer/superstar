import datetime as dt

from timeline import model, render

D = lambda day, hour=0: dt.datetime(2026, 6, day, hour)


def test_sequential_phases_share_lane_zero():
    spans = [("P1", D(1), D(3)), ("P2", D(4), D(6))]
    lanes, n = render.assign_lanes(spans)
    assert lanes == {"P1": 0, "P2": 0} and n == 1


def test_two_overlapping_phases_get_two_lanes():
    spans = [("P1", D(1), D(5)), ("P2", D(3), D(8))]
    lanes, n = render.assign_lanes(spans)
    assert n == 2 and lanes["P1"] != lanes["P2"]


def test_three_way_overlap_gets_three_lanes():
    spans = [("P14", D(1), D(9)), ("P16", D(4), D(6)), ("P17", D(5), D(7))]
    lanes, n = render.assign_lanes(spans)
    assert n == 3 and len(set(lanes.values())) == 3


def test_lane_frees_after_phase_closes():
    spans = [("P1", D(1), D(3)), ("P2", D(2), D(8)), ("P3", D(4), D(6))]
    lanes, n = render.assign_lanes(spans)
    assert n == 2 and lanes["P3"] == lanes["P1"]


def test_quiet_gaps_between_coverage():
    spans = [("P1", D(1), D(3)), ("P2", D(3, 12), D(5)), ("P3", D(9), D(10))]
    gaps = render.quiet_gaps([(s, e) for _, s, e in spans])
    # P1->P2 gap is 12h: below the 24h threshold, not reported.
    assert gaps == [(D(5), D(9))]


def test_quiet_gaps_split_by_interior_anchor():
    # A rendered event inside a coverage hole must never sit inside a
    # reported gap: the anchor splits the gap.
    cover = [(D(1), D(3)), (D(9), D(10))]
    gaps = render.quiet_gaps(cover, anchors=[D(6)])
    assert gaps == [(D(3), D(6)), (D(6), D(9))]


def test_quiet_gaps_anchor_near_edge_suppresses_short_remainder():
    # Anchor 12h after coverage ends: the sub-gap before it is below the
    # threshold and disappears; only the long remainder is reported.
    gaps = render.quiet_gaps([(D(1), D(3)), (D(9), D(10))], anchors=[D(3, 12)])
    assert gaps == [(D(3, 12), D(9))]


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
