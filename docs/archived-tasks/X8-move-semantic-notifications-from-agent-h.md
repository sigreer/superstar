# X8 - Move semantic notifications from agent hooks to tasktool status changes

status: done
created: 2026-05-19
closed: 2026-05-19

## References

- hooks/agent-finished
- tools/tasktool/notify.py
- tools/tasktool/commands.py
- tools/tasktool/tests/test_notify.py
- tools/tasktool/tests/test_commands.py
- tools/tasktool/tests/conftest.py
- tests/claude-code/test-agent-finished-hook.sh

## Notes

Move semantic spoken notifications to tasktool status transitions for ready/in_progress/blocked/done. Keep agent Stop/SubagentStop hooks as generic completion dings only, with different sound styles for Claude and Codex.
Agent Stop/SubagentStop hooks now emit generic harness-specific dings only. Semantic spoken notifications moved to tasktool status events for ready, in_progress, blocked, and done, including create, set, close, block, unblock, and archive-phase paths.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-19",
  "created": "2026-05-19",
  "id": "X8",
  "notes": "Move semantic spoken notifications to tasktool status transitions for ready/in_progress/blocked/done. Keep agent Stop/SubagentStop hooks as generic completion dings only, with different sound styles for Claude and Codex.\nAgent Stop/SubagentStop hooks now emit generic harness-specific dings only. Semantic spoken notifications moved to tasktool status events for ready, in_progress, blocked, and done, including create, set, close, block, unblock, and archive-phase paths.",
  "refs": [
    "hooks/agent-finished",
    "tools/tasktool/notify.py",
    "tools/tasktool/commands.py",
    "tools/tasktool/tests/test_notify.py",
    "tools/tasktool/tests/test_commands.py",
    "tools/tasktool/tests/conftest.py",
    "tests/claude-code/test-agent-finished-hook.sh"
  ],
  "started": null,
  "status": "done",
  "title": "Move semantic notifications from agent hooks to tasktool status changes",
  "worktree_branch": null,
  "worktree_in_place": false,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
