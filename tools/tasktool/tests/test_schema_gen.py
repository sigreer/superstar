from tasktool.schema_gen import build_schema


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
