# X19 - Install TodoWrite snapshot hook via deploy.sh

status: done
created: 2026-05-23
closed: 2026-05-23

## References

- hooks/hooks.json
- hooks/todo-snapshot
- .codex-plugin/plugin.json
- plugins/superstar/.codex-plugin/plugin.json
- scripts/tests/test_todo_snapshot_hook.py
- docs/archived-tasks/X20-install-codex-todo-snapshot-hook.md
- VERSION
- package.json
- .agents/plugins/marketplace.json
- .claude-plugin/plugin.json
- .claude-plugin/marketplace.json
- .cursor-plugin/plugin.json
- gemini-extension.json

## Notes

Closed after confirming the implementation shipped through commits e4bcf79, 413fbc8, and 0e2c711. X19's Claude TodoWrite hook was already present; the follow-up Codex mirror added Codex plugin hook registration, update_plan snapshot conversion under ~/.codex/projects/<project-slug>/<session_id>/todos.json, tests, the requested patch bump, and deploy verification. X20 was an accidental duplicate crosscut created during the Codex follow-up and is referenced here for traceability.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-23",
  "created": "2026-05-23",
  "id": "X19",
  "notes": "Closed after confirming the implementation shipped through commits e4bcf79, 413fbc8, and 0e2c711. X19's Claude TodoWrite hook was already present; the follow-up Codex mirror added Codex plugin hook registration, update_plan snapshot conversion under ~/.codex/projects/<project-slug>/<session_id>/todos.json, tests, the requested patch bump, and deploy verification. X20 was an accidental duplicate crosscut created during the Codex follow-up and is referenced here for traceability.",
  "refs": [
    "hooks/hooks.json",
    "hooks/todo-snapshot",
    ".codex-plugin/plugin.json",
    "plugins/superstar/.codex-plugin/plugin.json",
    "scripts/tests/test_todo_snapshot_hook.py",
    "docs/archived-tasks/X20-install-codex-todo-snapshot-hook.md",
    "VERSION",
    "package.json",
    ".agents/plugins/marketplace.json",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".cursor-plugin/plugin.json",
    "gemini-extension.json"
  ],
  "started": null,
  "status": "done",
  "title": "Install TodoWrite snapshot hook via deploy.sh",
  "worktree_branch": null,
  "worktree_in_place": false,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
