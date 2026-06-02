import json
from pathlib import Path

from tasktool.serialize import from_dict, to_dict


def _v1_raw() -> dict:
    return {
        "project": "x", "schema_version": 1, "north_star": "",
        "phases": [{
            "id": "P1", "title": "t", "created": "2026-05-01", "status": "ready",
            "slices": [{"id": "S1", "title": "t", "created": "2026-05-01", "status": "ready"}],
        }],
        "cross_cutting": [], "archived_phases": [], "archived_cross_cutting": [],
    }


def test_v1_loads_with_new_field_defaults():
    p = from_dict(_v1_raw())
    assert p.phases[0].workflow_step is None
    s = p.phases[0].slices[0]
    assert s.workflow_step is None
    assert s.review_active is False
    assert s.review_stage is None


def test_v1_to_v3_promotion_on_save():
    p = from_dict(_v1_raw())
    out = to_dict(p)
    assert out["schema_version"] == 3
    assert "workflow_step" not in out["phases"][0]
    slc = out["phases"][0]["slices"][0]
    assert "workflow_step" not in slc
    # P7 fields must NOT appear on a historical default-valued row.
    for key in (
        "integration_surfaces", "reservations", "coordination_group",
        "worktree_base_sha", "landed_base_sha",
    ):
        assert key not in slc
    assert "reservations_ledger" not in out


def test_v1_validates_against_v3_schema_after_save():
    pytest = __import__("pytest")
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")
    from tasktool.schema_gen import build_schema
    p = from_dict(_v1_raw())
    out = to_dict(p)
    jsonschema.validate(instance=out, schema=build_schema())


def _v2_raw() -> dict:
    raw = _v1_raw()
    raw["schema_version"] = 2
    # A v2 row may carry workflow/worktree keys; include a representative one.
    raw["phases"][0]["slices"][0]["workflow_step"] = "implement"
    return raw


def test_v2_loads_with_p7_field_defaults():
    p = from_dict(_v2_raw())
    s = p.phases[0].slices[0]
    assert s.integration_surfaces == []
    assert s.reservations == []
    assert s.coordination_group is None
    assert s.worktree_base_sha is None
    assert s.landed_base_sha is None
    assert p.reservations_ledger == []


def test_v2_to_v3_promotion_adds_no_p7_churn():
    p = from_dict(_v2_raw())
    out = to_dict(p)
    assert out["schema_version"] == 3
    slc = out["phases"][0]["slices"][0]
    # The one explicitly-set v2 key is preserved...
    assert slc["workflow_step"] == "implement"
    # ...and no defaulted P7 key is introduced.
    for key in (
        "integration_surfaces", "reservations", "coordination_group",
        "worktree_base_sha", "landed_base_sha",
    ):
        assert key not in slc
    assert "reservations_ledger" not in out
