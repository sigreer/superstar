# X7 - Fix Superstar Codex plugin payload version drift

status: done
created: 2026-05-19
closed: 2026-05-19

## References

- .version-bump.json
- plugins/superstar/.codex-plugin/plugin.json
- .agents/plugins/marketplace.json
- tests/codex-plugin-sync/test-version-drift.sh
- tests/codex-plugin-sync/test-local-marketplace.sh

## Notes

Codex reported superstar/6.0.0 because the installable local marketplace payload under plugins/superstar still declared version 6.0.0 and the version bump audit did not track that embedded manifest.

Bumped the embedded Codex plugin payload manifest to 6.0.1 and added it to the version bump check. Reinstalled superstar@superstar-dev, then rebuilt the 6.0.1 runtime cache as a materialized copy of this checkout with .agents excluded so Codex sees the full skills/hooks tree while codex plugin list still reports installed/enabled. Final probe shows cache version 6.0.1, skills/hooks present, and no async-hook warning.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-19",
  "created": "2026-05-19",
  "id": "X7",
  "notes": "Codex reported superstar/6.0.0 because the installable local marketplace payload under plugins/superstar still declared version 6.0.0 and the version bump audit did not track that embedded manifest.\n\nBumped the embedded Codex plugin payload manifest to 6.0.1 and added it to the version bump check. Reinstalled superstar@superstar-dev, then rebuilt the 6.0.1 runtime cache as a materialized copy of this checkout with .agents excluded so Codex sees the full skills/hooks tree while codex plugin list still reports installed/enabled. Final probe shows cache version 6.0.1, skills/hooks present, and no async-hook warning.",
  "refs": [
    ".version-bump.json",
    "plugins/superstar/.codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
    "tests/codex-plugin-sync/test-version-drift.sh",
    "tests/codex-plugin-sync/test-local-marketplace.sh"
  ],
  "started": null,
  "status": "done",
  "title": "Fix Superstar Codex plugin payload version drift",
  "worktree_branch": null,
  "worktree_in_place": false,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
