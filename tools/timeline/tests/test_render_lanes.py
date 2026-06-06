import datetime as dt

from timeline import render

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
