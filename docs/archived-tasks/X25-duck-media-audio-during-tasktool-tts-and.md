# X25 - Duck media audio during tasktool TTS and verify Codex plugin payload

status: done
created: 2026-05-26
started: 2026-05-26
closed: 2026-05-26

## References

- tools/tasktool/notify.py
- tools/tasktool/tests/test_notify.py
- scripts/deploy.sh
- scripts/publish-to-local-codex.sh
- scripts/publish-to-local-claude.sh

## Notes

Diagnosed Codex 6.8.2 cache as incomplete: versioned cache lacked VERSION/runtime payload and current was missing; deploy check now verifies materialized hook/tool/skill payloads.
Implemented tasktool TTS media duck/restore, hardened Codex/Claude publish checks to require hooks/hooks.json, and expanded deploy --check to verify materialized payloads in current and versioned caches. Verification: py_compile notify/test_notify, pytest tools/tasktool/tests/test_notify.py -q (7 passed), pytest tools/tasktool/tests -q (668 passed), bump-version --check, tasktool validate --strict-format, git diff --check, cached Codex hook runner smoke, deploy.sh completed with all rows OK at 6.8.3.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-26",
  "created": "2026-05-26",
  "id": "X25",
  "notes": "Diagnosed Codex 6.8.2 cache as incomplete: versioned cache lacked VERSION/runtime payload and current was missing; deploy check now verifies materialized hook/tool/skill payloads.\nImplemented tasktool TTS media duck/restore, hardened Codex/Claude publish checks to require hooks/hooks.json, and expanded deploy --check to verify materialized payloads in current and versioned caches. Verification: py_compile notify/test_notify, pytest tools/tasktool/tests/test_notify.py -q (7 passed), pytest tools/tasktool/tests -q (668 passed), bump-version --check, tasktool validate --strict-format, git diff --check, cached Codex hook runner smoke, deploy.sh completed with all rows OK at 6.8.3.",
  "refs": [
    "tools/tasktool/notify.py",
    "tools/tasktool/tests/test_notify.py",
    "scripts/deploy.sh",
    "scripts/publish-to-local-codex.sh",
    "scripts/publish-to-local-claude.sh"
  ],
  "started": "2026-05-26",
  "status": "done",
  "title": "Duck media audio during tasktool TTS and verify Codex plugin payload",
  "worktree_branch": null,
  "worktree_in_place": true,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
