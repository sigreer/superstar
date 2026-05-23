# X20 - Install Codex todo snapshot hook

status: done
created: 2026-05-23
started: 2026-05-23
closed: 2026-05-23

## References

- .codex-plugin/plugin.json
- plugins/superstar/.codex-plugin/plugin.json
- hooks/hooks.json
- hooks/todo-snapshot
- scripts/tests/test_todo_snapshot_hook.py
- VERSION
- package.json
- .agents/plugins/marketplace.json
- .claude-plugin/plugin.json
- .claude-plugin/marketplace.json
- .cursor-plugin/plugin.json
- gemini-extension.json

## Notes

Codex can mirror the X19 Claude TodoWrite snapshot approach via the Codex plugin hooks surface. Added Codex plugin hook registration, extended the shared todo-snapshot hook to convert update_plan payloads into the existing todos.json shape under ~/.codex/projects/<project-slug>/<session_id>/todos.json, widened the PostToolUse matcher for Codex plan tool names, added shell-hook coverage for Claude and Codex payloads, applied the requested patch bump, and deployed refreshed Codex/Claude caches.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-23",
  "created": "2026-05-23",
  "id": "X20",
  "notes": "Codex can mirror the X19 Claude TodoWrite snapshot approach via the Codex plugin hooks surface. Added Codex plugin hook registration, extended the shared todo-snapshot hook to convert update_plan payloads into the existing todos.json shape under ~/.codex/projects/<project-slug>/<session_id>/todos.json, widened the PostToolUse matcher for Codex plan tool names, added shell-hook coverage for Claude and Codex payloads, applied the requested patch bump, and deployed refreshed Codex/Claude caches.",
  "refs": [
    ".codex-plugin/plugin.json",
    "plugins/superstar/.codex-plugin/plugin.json",
    "hooks/hooks.json",
    "hooks/todo-snapshot",
    "scripts/tests/test_todo_snapshot_hook.py",
    "VERSION",
    "package.json",
    ".agents/plugins/marketplace.json",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".cursor-plugin/plugin.json",
    "gemini-extension.json"
  ],
  "started": "2026-05-23",
  "status": "done",
  "title": "Install Codex todo snapshot hook",
  "worktree_branch": null,
  "worktree_in_place": false,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
