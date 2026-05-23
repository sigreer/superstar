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


def test_v1_to_v2_promotion_on_save():
    p = from_dict(_v1_raw())
    out = to_dict(p)
    assert out["schema_version"] == 2
    assert "workflow_step" not in out["phases"][0]
    assert "workflow_step" not in out["phases"][0]["slices"][0]


def test_v1_validates_against_v2_schema_after_save():
    pytest = __import__("pytest")
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")
    from tasktool.schema_gen import build_schema
    p = from_dict(_v1_raw())
    out = to_dict(p)
    jsonschema.validate(instance=out, schema=build_schema())
