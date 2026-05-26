# X4 - Spot fix: broaden legacy tasklist importer compatibility

status: done
created: 2026-05-19
closed: 2026-05-19

## References

- tools/tasktool/importer.py

## Notes

User-requested blocking spot fix completed outside the normal workflow for speed. Legacy markdown import now accepts fully-qualified slice IDs and additional cross-cutting forms including tagged done items, blocked cross rows coerced to ready, and archived cross rows treated as done.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-19",
  "created": "2026-05-19",
  "id": "X4",
  "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. Legacy markdown import now accepts fully-qualified slice IDs and additional cross-cutting forms including tagged done items, blocked cross rows coerced to ready, and archived cross rows treated as done.",
  "refs": [
    "tools/tasktool/importer.py"
  ],
  "started": null,
  "status": "done",
  "title": "Spot fix: broaden legacy tasklist importer compatibility",
  "worktree_branch": null,
  "worktree_in_place": false,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
