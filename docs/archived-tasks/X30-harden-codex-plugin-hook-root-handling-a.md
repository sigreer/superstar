# X30 - Harden Codex plugin hook root handling and deploy cache checks

status: done
created: 2026-06-12
started: 2026-06-12
closed: 2026-06-12

## References

- hooks/hooks.json
- plugins/superstar/hooks/hooks.json
- scripts/deploy.sh
- scripts/lib/publish-common.sh
- scripts/tests/test_todo_snapshot_hook.py
- scripts/tests/test_deploy_check.py
- tests/claude-code/test-hook-config.sh
- plugins/superstar/skills/brainstorming/SKILL.md
- plugins/superstar/skills/external-review/SKILL.md
- plugins/superstar/skills/external-review/scripts/external-reviewer.py
- plugins/superstar/skills/writing-plans/SKILL.md

## Notes

Implemented hook root cleanup and Codex deploy-cache check alignment. Verification: python3 -m pytest scripts/tests -q; bash tests/claude-code/test-hook-config.sh; bash tests/claude-code/test-publish-to-local-claude.sh; bash tests/codex-plugin-sync/test-publish-to-local-codex.sh; ./scripts/bump-version.sh --check; ./scripts/deploy.sh --check; tasktool validate --strict-format (only pre-existing X29 missing-ref warnings); git diff --check.
Included embedded Codex payload sync produced by publish/deploy materialization so plugins/superstar mirrors the canonical top-level skills.
Release refs: implementation commit 6c985f0; patch bump commit 752a868. Deployed 6.10.1 with ./scripts/deploy.sh; deploy check reported Codex 6.10.1 version cache OK, Claude current/version caches OK, global shims and pre-commit hook OK.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-06-12",
  "created": "2026-06-12",
  "id": "X30",
  "notes": "Implemented hook root cleanup and Codex deploy-cache check alignment. Verification: python3 -m pytest scripts/tests -q; bash tests/claude-code/test-hook-config.sh; bash tests/claude-code/test-publish-to-local-claude.sh; bash tests/codex-plugin-sync/test-publish-to-local-codex.sh; ./scripts/bump-version.sh --check; ./scripts/deploy.sh --check; tasktool validate --strict-format (only pre-existing X29 missing-ref warnings); git diff --check.\nIncluded embedded Codex payload sync produced by publish/deploy materialization so plugins/superstar mirrors the canonical top-level skills.\nRelease refs: implementation commit 6c985f0; patch bump commit 752a868. Deployed 6.10.1 with ./scripts/deploy.sh; deploy check reported Codex 6.10.1 version cache OK, Claude current/version caches OK, global shims and pre-commit hook OK.",
  "refs": [
    "hooks/hooks.json",
    "plugins/superstar/hooks/hooks.json",
    "scripts/deploy.sh",
    "scripts/lib/publish-common.sh",
    "scripts/tests/test_todo_snapshot_hook.py",
    "scripts/tests/test_deploy_check.py",
    "tests/claude-code/test-hook-config.sh",
    "plugins/superstar/skills/brainstorming/SKILL.md",
    "plugins/superstar/skills/external-review/SKILL.md",
    "plugins/superstar/skills/external-review/scripts/external-reviewer.py",
    "plugins/superstar/skills/writing-plans/SKILL.md"
  ],
  "started": "2026-06-12",
  "status": "done",
  "title": "Harden Codex plugin hook root handling and deploy cache checks",
  "worktree_branch": null,
  "worktree_in_place": false,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
