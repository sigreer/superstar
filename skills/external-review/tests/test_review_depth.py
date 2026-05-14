from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_resolve_depth_standard_no_sweeps():
    plan = er.plan_sweeps(depth="standard", policy=None, count=None,
                          round_num=1, checkpoints={"first-round": "pending", "final-ready": "pending"},
                          primary_verdict_pre_run=None)
    assert plan.sweep_count == 0


def test_resolve_depth_thorough_first_round():
    plan = er.plan_sweeps(depth="thorough", policy=None, count=None,
                          round_num=1, checkpoints={"first-round": "pending", "final-ready": "pending"},
                          primary_verdict_pre_run=None)
    assert plan.sweep_count == 1
    assert plan.checkpoint == "first-round"


def test_thorough_final_ready_fires_once(tmp_path):
    # round 2, prior primary returned 'ready' for the first time; final-ready not yet done.
    plan = er.plan_sweeps(depth="thorough", policy=None, count=None,
                          round_num=2, checkpoints={"first-round": "completed", "final-ready": "pending"},
                          primary_verdict_pre_run="ready")
    assert plan.sweep_count == 1
    assert plan.checkpoint == "final-ready"


def test_final_ready_skipped_when_already_completed():
    plan = er.plan_sweeps(depth="thorough", policy=None, count=None,
                          round_num=3, checkpoints={"first-round": "completed", "final-ready": "completed"},
                          primary_verdict_pre_run="ready")
    assert plan.sweep_count == 0


def test_exhaustive_first_round_two_sweeps():
    plan = er.plan_sweeps(depth="exhaustive", policy=None, count=None,
                          round_num=1, checkpoints={"first-round": "pending", "final-ready": "pending"},
                          primary_verdict_pre_run=None)
    assert plan.sweep_count == 2
