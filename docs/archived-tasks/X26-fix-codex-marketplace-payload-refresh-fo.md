# X26 - Fix Codex marketplace payload refresh for Superstar

status: done
created: 2026-05-26
started: 2026-05-26
closed: 2026-05-26

## References

- .agents/plugins/marketplace.json
- plugins/superstar
- scripts/publish-to-local-codex.sh
- tests/codex-plugin-sync/test-local-marketplace.sh
- tests/codex-plugin-sync/test-publish-to-local-codex.sh
- scripts/tests/test_deploy_check.py
- .version-bump.json

## Notes

Codex startup refreshes cache from the local marketplace path and does not materialize symlinked payload directories. Fixed by making plugins/superstar a real embedded runtime payload and teaching publish-to-local-codex to refresh it from the repo root before installing.
Fixed Codex startup cache regression by replacing symlinked embedded plugin payload with materialized runtime files, adding embedded VERSION to version sync, and updating publish-to-local-codex to refresh the embedded payload before codex plugin add. Verification: Codex marketplace test, publish-to-local-codex test, deploy_check pytest, bump-version --check, tasktool validate --strict-format, git diff --check, deploy.sh all rows OK at 6.8.4, codex plugin list preserved hooks/tools/skills in cache, cached hook runner smoke passed.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-26",
  "created": "2026-05-26",
  "id": "X26",
  "notes": "Codex startup refreshes cache from the local marketplace path and does not materialize symlinked payload directories. Fixed by making plugins/superstar a real embedded runtime payload and teaching publish-to-local-codex to refresh it from the repo root before installing.\nFixed Codex startup cache regression by replacing symlinked embedded plugin payload with materialized runtime files, adding embedded VERSION to version sync, and updating publish-to-local-codex to refresh the embedded payload before codex plugin add. Verification: Codex marketplace test, publish-to-local-codex test, deploy_check pytest, bump-version --check, tasktool validate --strict-format, git diff --check, deploy.sh all rows OK at 6.8.4, codex plugin list preserved hooks/tools/skills in cache, cached hook runner smoke passed.",
  "refs": [
    ".agents/plugins/marketplace.json",
    "plugins/superstar",
    "scripts/publish-to-local-codex.sh",
    "tests/codex-plugin-sync/test-local-marketplace.sh",
    "tests/codex-plugin-sync/test-publish-to-local-codex.sh",
    "scripts/tests/test_deploy_check.py",
    ".version-bump.json"
  ],
  "started": "2026-05-26",
  "status": "done",
  "title": "Fix Codex marketplace payload refresh for Superstar",
  "worktree_branch": null,
  "worktree_in_place": true,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
