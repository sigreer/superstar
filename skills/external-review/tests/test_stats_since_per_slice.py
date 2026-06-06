from pathlib import Path
import json, sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def _chain(tmp_path, name, kind, work_id, rounds):
    d = tmp_path / name
    d.mkdir(parents=True)
    er.write_manifest(d / "chain.json", {
        "schema_version": 1, "chain": name, "kind": kind,
        "work_id": work_id, "rounds": rounds,
    })


def _round(n, started_at, verdict="ready", status="ok"):
    return {
        "round": n, "started_at": started_at, "status": status,
        "verdict": verdict, "merged_verdict": verdict, "verdict_valid": True,
        "duration_ms": 1000,
    }


def test_parse_since_date_only_is_utc_midnight():
    d = er.parse_since("2026-06-07")
    assert d.tzinfo is not None
    assert (d.hour, d.minute, d.utcoffset().total_seconds()) == (0, 0, 0.0)


def test_since_filters_rounds_and_counts_legacy(tmp_path):
    _chain(tmp_path, "old-spec", "spec", "P1.S1", [
        _round(1, "2026-05-01T10:00:00.000Z"),
        {"round": 2, "status": "ok", "verdict": "ready",
         "merged_verdict": "ready", "verdict_valid": True},  # legacy: no started_at
    ])
    _chain(tmp_path, "new-spec", "spec", "P1.S2", [
        _round(1, "2026-06-10T10:00:00.000Z"),
    ])
    stats = er.collect_review_stats(tmp_path, since=er.parse_since("2026-06-07"))
    assert stats["round_count"] == 1
    assert stats["excluded_legacy_rounds"] == 1


def test_per_slice_correlated(tmp_path):
    ts = "2026-06-10T10:00:00.000Z"
    _chain(tmp_path, "s1-spec", "spec", "P1.S1", [_round(1, ts)])
    _chain(tmp_path, "s1-plan", "plan", "P1.S1", [_round(1, ts), _round(2, ts)])
    _chain(tmp_path, "s1-post", "post-slice", "P1.S1", [_round(1, ts)])
    stats = er.collect_review_stats(tmp_path)
    ps = stats["per_slice"]
    assert ps["slice_count"] == 1          # P1.S1 has a passing post-slice round
    assert ps["rounds_total"] == 4         # all rounds across all three gates
    assert ps["rounds_per_slice"] == 4.0
    assert ps["per_slice_complete"] is True
    assert ps["uncorrelated_chains"] == []


def test_per_slice_counts_sweep_invocations(tmp_path):
    # A thorough post-slice round stores primary + sweep inside one round
    # entry's "reviewers" list; the numerator must count both invocations.
    ts = "2026-06-10T10:00:00.000Z"
    sweep_round = _round(1, ts)
    sweep_round["reviewers"] = [
        {"role": "primary", "verdict": "ready", "status": "ok"},
        {"role": "sweep", "verdict": "ready", "status": "ok"},
    ]
    _chain(tmp_path, "s1-spec", "spec", "P1.S1", [_round(1, ts)])
    _chain(tmp_path, "s1-post", "post-slice", "P1.S1", [sweep_round])
    stats = er.collect_review_stats(tmp_path)
    ps = stats["per_slice"]
    assert ps["slice_count"] == 1
    assert ps["rounds_total"] == 3         # 1 spec primary + post primary + post sweep
    assert ps["rounds_per_slice"] == 3.0


def test_per_slice_uncorrelated_flags_incomplete(tmp_path):
    ts = "2026-06-10T10:00:00.000Z"
    _chain(tmp_path, "s1-spec", "spec", None, [_round(1, ts)])   # missing work_id
    _chain(tmp_path, "s1-plan", "plan", "P1.S1", [_round(1, ts)])
    _chain(tmp_path, "s1-post", "post-slice", "P1.S1", [_round(1, ts)])
    stats = er.collect_review_stats(tmp_path)
    ps = stats["per_slice"]
    assert ps["per_slice_complete"] is False
    assert "s1-spec" in ps["uncorrelated_chains"]


def test_per_slice_denominator_requires_passing_post_slice(tmp_path):
    ts = "2026-06-10T10:00:00.000Z"
    _chain(tmp_path, "s1-post", "post-slice", "P1.S1", [_round(1, ts, verdict="revise")])
    stats = er.collect_review_stats(tmp_path)
    assert stats["per_slice"]["slice_count"] == 0


def test_per_slice_latest_in_window_round_decides(tmp_path):
    _chain(tmp_path, "s1-post", "post-slice", "P1.S1", [
        _round(1, "2026-06-10T10:00:00.000Z", verdict="revise"),
        _round(2, "2026-06-11T10:00:00.000Z", verdict="ready with small edits"),
    ])
    stats = er.collect_review_stats(tmp_path)
    assert stats["per_slice"]["slice_count"] == 1
