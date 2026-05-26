# X14 - Stabilize local Claude/Codex plugin current entrypoints

status: done
created: 2026-05-20
started: 2026-05-20
closed: 2026-05-20

## Notes

Publish scripts now maintain materialized versioned and current plugin cache directories for Claude and Codex, rewrite hook commands to current/, and refresh the global external-reviewer shim so project-level scripts do not need updating after version bumps.
Implemented stable materialized current/ entrypoints for local Claude and Codex plugin caches, updated external-reviewer shim installation to target current/, and verified Codex/Claude publish tests plus installer pytest and tasktool validate.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-20",
  "created": "2026-05-20",
  "id": "X14",
  "notes": "Publish scripts now maintain materialized versioned and current plugin cache directories for Claude and Codex, rewrite hook commands to current/, and refresh the global external-reviewer shim so project-level scripts do not need updating after version bumps.\nImplemented stable materialized current/ entrypoints for local Claude and Codex plugin caches, updated external-reviewer shim installation to target current/, and verified Codex/Claude publish tests plus installer pytest and tasktool validate.",
  "refs": [],
  "started": "2026-05-20",
  "status": "done",
  "title": "Stabilize local Claude/Codex plugin current entrypoints",
  "worktree_branch": null,
  "worktree_in_place": false,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
