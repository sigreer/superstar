from pathlib import Path
import sys, importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
_spec = importlib.util.spec_from_file_location(
    "external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(er)


def _chain(tmp_path, name, kind, rounds, work_id="P1.S1"):
    d = tmp_path / name
    d.mkdir(parents=True)
    er.write_manifest(d / "chain.json", {
        "schema_version": 1, "chain": name, "kind": kind,
        "work_id": work_id, "rounds": rounds,
    })


def _round(n, combined=False):
    r = {"round": n, "status": "ok", "verdict": "ready",
         "merged_verdict": "ready", "verdict_valid": True, "duration_ms": 1000,
         "started_at": "2026-06-10T10:00:00.000Z"}
    if combined:
        r["combined_gate"] = True
        r["combined_gate_spec"] = "spec.md"
    return r


def test_segments_combined_and_standalone_plan_chains(tmp_path):
    _chain(tmp_path, "a-plan", "plan",
           [_round(1, combined=True), _round(2, combined=True)], work_id="P1.S1")
    _chain(tmp_path, "b-plan", "plan", [_round(1)], work_id="P1.S2")
    stats = er.collect_review_stats(tmp_path)
    cg = stats["combined_gate"]
    assert cg["combined"] == {"chains": 1, "rounds": 2}
    assert cg["standalone"] == {"chains": 1, "rounds": 1}


def test_no_plan_chains_yields_zeros(tmp_path):
    _chain(tmp_path, "a-spec", "spec", [_round(1)])
    stats = er.collect_review_stats(tmp_path)
    cg = stats["combined_gate"]
    assert cg["combined"] == {"chains": 0, "rounds": 0}
    assert cg["standalone"] == {"chains": 0, "rounds": 0}


def test_partial_combined_chain_counts_as_combined(tmp_path):
    # A chain combined on any in-window round is classified combined.
    _chain(tmp_path, "c-plan", "plan", [_round(1), _round(2, combined=True)])
    stats = er.collect_review_stats(tmp_path)
    assert stats["combined_gate"]["combined"] == {"chains": 1, "rounds": 2}
    assert stats["combined_gate"]["standalone"] == {"chains": 0, "rounds": 0}
