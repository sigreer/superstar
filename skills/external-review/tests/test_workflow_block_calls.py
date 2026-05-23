import subprocess
from unittest.mock import patch, MagicMock
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "external-reviewer.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("er", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _slice_id_for_kind(kind, work_id):
    # Helper used by tests below to invoke the public helper directly.
    er = _load_module()
    return er.maybe_update_workflow_block_target(kind=kind, work_id=work_id)


def test_no_call_when_work_id_missing():
    assert _slice_id_for_kind("plan", None) is None


def test_no_call_when_kind_is_spec():
    assert _slice_id_for_kind("spec", "P6.S1") is None


def test_no_call_when_work_id_is_phase():
    assert _slice_id_for_kind("plan", "P6") is None


def test_no_call_when_work_id_is_cross():
    assert _slice_id_for_kind("plan", "X19") is None


def test_yields_slice_id_for_plan():
    assert _slice_id_for_kind("plan", "P6.S1") == "P6.S1"


def test_yields_slice_id_for_post_slice():
    assert _slice_id_for_kind("post-slice", "P6.S1") == "P6.S1"


def test_lifecycle_calls_in_order():
    er = _load_module()
    with patch.object(er, "_run_tasktool_set") as fake:
        er.workflow_block_round_start("P6.S1")
        er.workflow_block_after_verdict("P6.S1", verdict="revise")
        er.workflow_block_after_verdict("P6.S1", verdict="ready")
        calls = [c.kwargs for c in fake.call_args_list]
        assert calls[0] == {"id": "P6.S1", "review_active": "true", "review_stage": "awaiting_response"}
        assert calls[1] == {"id": "P6.S1", "review_stage": "applying_fixes"}
        assert calls[2] == {"id": "P6.S1", "review_stage": "passed"}


def test_tasktool_failure_does_not_raise():
    er = _load_module()
    with patch.object(er.subprocess, "run", side_effect=FileNotFoundError("no tasktool")):
        # Should not raise.
        er.workflow_block_round_start("P6.S1")
