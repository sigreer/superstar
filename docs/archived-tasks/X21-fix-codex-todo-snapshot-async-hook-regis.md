# X21 - Fix Codex todo snapshot async hook registration

status: done
created: 2026-05-23
started: 2026-05-23
closed: 2026-05-23

## References

- scripts/tests/test_todo_snapshot_hook.py
- hooks/hooks.json

## Notes

Root cause: the installed Codex current cache still had PostToolUse todo-snapshot registered with async=true, which Codex skips because async hooks are unsupported. Source hooks/hooks.json now has async=false with regression coverage, and live Codex current plus 6.6.5 cache copies were aligned to async=false. Verification: pytest -q scripts/tests/test_todo_snapshot_hook.py; tasktool validate --strict-format; scripts/deploy.sh --check; codex debug prompt-input warning grep returned no async-hook warning.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-23",
  "created": "2026-05-23",
  "id": "X21",
  "notes": "Root cause: the installed Codex current cache still had PostToolUse todo-snapshot registered with async=true, which Codex skips because async hooks are unsupported. Source hooks/hooks.json now has async=false with regression coverage, and live Codex current plus 6.6.5 cache copies were aligned to async=false. Verification: pytest -q scripts/tests/test_todo_snapshot_hook.py; tasktool validate --strict-format; scripts/deploy.sh --check; codex debug prompt-input warning grep returned no async-hook warning.",
  "refs": [
    "scripts/tests/test_todo_snapshot_hook.py",
    "hooks/hooks.json"
  ],
  "started": "2026-05-23",
  "status": "done",
  "title": "Fix Codex todo snapshot async hook registration",
  "worktree_branch": null,
  "worktree_in_place": false,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
