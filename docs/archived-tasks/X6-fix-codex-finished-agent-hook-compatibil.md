# X6 - Fix Codex finished-agent hook compatibility

status: done
created: 2026-05-19
closed: 2026-05-19

## References

- hooks/hooks.json
- hooks/agent-finished
- tests/claude-code/test-hook-config.sh
- tests/claude-code/test-agent-finished-hook.sh

## Notes

Codex startup skips Stop/SubagentStop notification hooks when hooks.json uses async=true; fix should preserve finished-agent notification behavior while avoiding unsupported async hook registration in Codex.
Set finished-agent Stop/SubagentStop hook registrations to async=false for Codex compatibility. The hook now backgrounds real notification playback internally so synchronous hook registration returns quickly while dry-run tests remain foreground and deterministic.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-19",
  "created": "2026-05-19",
  "id": "X6",
  "notes": "Codex startup skips Stop/SubagentStop notification hooks when hooks.json uses async=true; fix should preserve finished-agent notification behavior while avoiding unsupported async hook registration in Codex.\nSet finished-agent Stop/SubagentStop hook registrations to async=false for Codex compatibility. The hook now backgrounds real notification playback internally so synchronous hook registration returns quickly while dry-run tests remain foreground and deterministic.",
  "refs": [
    "hooks/hooks.json",
    "hooks/agent-finished",
    "tests/claude-code/test-hook-config.sh",
    "tests/claude-code/test-agent-finished-hook.sh"
  ],
  "started": null,
  "status": "done",
  "title": "Fix Codex finished-agent hook compatibility",
  "worktree_branch": null,
  "worktree_in_place": false,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
