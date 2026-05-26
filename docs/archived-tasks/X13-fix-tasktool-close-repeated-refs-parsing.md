# X13 - Fix tasktool close repeated refs parsing

status: done
created: 2026-05-20
started: 2026-05-20
closed: 2026-05-20

## References

- tools/tasktool/cli.py
- tools/tasktool/tests/test_cli_integration.py
- tools/tasktool/tests/test_worktree_authority.py

## Notes

Fixed tasktool close --refs parsing so repeated flags and comma-separated refs both record every path. Verified with focused red/green regressions and full tasktool test suite.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-20",
  "created": "2026-05-20",
  "id": "X13",
  "notes": "Fixed tasktool close --refs parsing so repeated flags and comma-separated refs both record every path. Verified with focused red/green regressions and full tasktool test suite.",
  "refs": [
    "tools/tasktool/cli.py",
    "tools/tasktool/tests/test_cli_integration.py",
    "tools/tasktool/tests/test_worktree_authority.py"
  ],
  "started": "2026-05-20",
  "status": "done",
  "title": "Fix tasktool close repeated refs parsing",
  "worktree_branch": null,
  "worktree_in_place": false,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
