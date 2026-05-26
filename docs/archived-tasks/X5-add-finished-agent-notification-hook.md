# X5 - Add finished-agent notification hook

status: done
created: 2026-05-19
closed: 2026-05-19

## References

- hooks/agent-finished
- hooks/hooks.json
- hooks/hooks-cursor.json
- tests/claude-code/test-agent-finished-hook.sh

## Notes

User-requested hook update completed outside the normal workflow for speed. Adds Stop/SubagentStop finished-agent notifications, milestone message derivation from final agent text/transcript payloads, Hypr TTS config reuse with OPENAI_API_KEY fallback, and non-TTS ding fallbacks.
Superseded by X8: final-text milestone parsing was removed; agent hooks now emit generic dings and semantic spoken notifications come from tasktool status changes.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-19",
  "created": "2026-05-19",
  "id": "X5",
  "notes": "User-requested hook update completed outside the normal workflow for speed. Adds Stop/SubagentStop finished-agent notifications, milestone message derivation from final agent text/transcript payloads, Hypr TTS config reuse with OPENAI_API_KEY fallback, and non-TTS ding fallbacks.\nSuperseded by X8: final-text milestone parsing was removed; agent hooks now emit generic dings and semantic spoken notifications come from tasktool status changes.",
  "refs": [
    "hooks/agent-finished",
    "hooks/hooks.json",
    "hooks/hooks-cursor.json",
    "tests/claude-code/test-agent-finished-hook.sh"
  ],
  "started": null,
  "status": "done",
  "title": "Add finished-agent notification hook",
  "worktree_branch": null,
  "worktree_in_place": false,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
