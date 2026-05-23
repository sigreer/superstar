import pytest

from tasktool.schema_gen import build_schema


def _task_schema(schema):
    return schema["properties"]["phases"]["items"]["properties"]["slices"]["items"]["properties"]["tasks"]["items"]


def _slice_schema(schema):
    return schema["properties"]["phases"]["items"]["properties"]["slices"]["items"]


def _phase_schema(schema):
    return schema["properties"]["phases"]["items"]


def _cross_schema(schema):
    return schema["properties"]["cross_cutting"]["items"]


def test_task_status_enum_rejects_cancelled():
    schema = build_schema()
    task_status = _task_schema(schema)["properties"]["status"]["enum"]
    assert "cancelled" not in task_status
    assert task_status == ["ready", "in_progress", "done"]


def test_raw_task_with_cancelled_status_fails_jsonschema_validation():
    jsonschema = pytest.importorskip("jsonschema")
    schema = build_schema()
    bad = {
        "project": "t", "schema_version": schema["properties"]["schema_version"]["const"], "phases": [{
            "id": "P1", "title": "p", "created": "2026-05-23", "status": "ready",
            "slices": [{
                "id": "S1", "title": "s", "created": "2026-05-23", "status": "ready",
                "tasks": [{
                    "id": "T1", "title": "t", "created": "2026-05-23",
                    "status": "cancelled",
                }],
            }],
        }],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_phase_and_cross_status_enums_include_cancelled():
    schema = build_schema()
    phase_status = _phase_schema(schema)["properties"]["status"]["enum"]
    cross_status = _cross_schema(schema)["properties"]["status"]["enum"]
    assert "cancelled" in phase_status
    assert "cancelled" in cross_status


def test_slice_status_enum_includes_cancelled_and_blocked():
    schema = build_schema()
    slice_status = _slice_schema(schema)["properties"]["status"]["enum"]
    assert set(slice_status) == {"ready", "in_progress", "blocked", "done", "cancelled"}


def test_schema_includes_archived_cross_cutting():
    schema = build_schema()
    properties = schema["properties"]
    assert "archived_cross_cutting" in properties
    archived = properties["archived_cross_cutting"]["items"]
    assert archived["required"] == [
        "id",
        "title",
        "archived_path",
        "archived_date",
    ]
    assert archived["properties"]["id"]["pattern"] == r"^X\d+$"


def test_schema_describes_slice_worktree_fields():
    from tasktool.schema_gen import build_schema
    sch = build_schema()
    slc = sch["properties"]["phases"]["items"]["properties"]["slices"]["items"]
    for key in ("worktree_path", "worktree_branch", "worktree_in_place",
                "worktree_pruned_at", "worktree_prune_pending", "worktree_prune_pending_at"):
        assert key in slc["properties"], key
    assert slc["additionalProperties"] is False


def test_schema_describes_cross_worktree_fields():
    from tasktool.schema_gen import build_schema
    sch = build_schema()
    xc = sch["properties"]["cross_cutting"]["items"]
    for key in ("worktree_path", "worktree_branch", "worktree_in_place",
                "worktree_pruned_at", "worktree_prune_pending", "worktree_prune_pending_at"):
        assert key in xc["properties"], key


def test_schema_includes_prune_audit_fields():
    from tasktool import schema_gen
    schema = schema_gen.build_schema()
    slice_props = schema["properties"]["phases"]["items"]["properties"]["slices"]["items"]["properties"]
    assert "worktree_pruned_at" in slice_props
    assert "worktree_prune_pending" in slice_props
    assert "worktree_prune_pending_at" in slice_props
    cross_props = schema["properties"]["cross_cutting"]["items"]["properties"]
    assert "worktree_pruned_at" in cross_props
    assert "worktree_prune_pending" in cross_props
    assert "worktree_prune_pending_at" in cross_props
