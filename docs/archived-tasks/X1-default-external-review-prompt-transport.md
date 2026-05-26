# X1 - Default external-review prompt transport to stdin

status: done
created: 2026-05-18
closed: 2026-05-18

## Notes

Changed external-review default prompt transport from argv to stdin so the bundled Codex reviewer-agent receives prompts via codex exec '-' and avoids argv length failures.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-18",
  "created": "2026-05-18",
  "id": "X1",
  "notes": "Changed external-review default prompt transport from argv to stdin so the bundled Codex reviewer-agent receives prompts via codex exec '-' and avoids argv length failures.",
  "refs": [],
  "started": null,
  "status": "done",
  "title": "Default external-review prompt transport to stdin",
  "worktree_branch": null,
  "worktree_in_place": false,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
