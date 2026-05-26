# X28 - Prefer explicit notification ding sound file

status: done
created: 2026-05-26
closed: 2026-05-26

## References

- tools/tasktool/notify.py

## Notes

Recorded the externally supplied notification sound-file change: tasktool ding playback now prefers SUPERSTAR_NOTIFY_DING_FILE or /usr/share/sounds/Enchanted/stereo/bell.ogg before falling back to sound-theme names.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-26",
  "created": "2026-05-26",
  "id": "X28",
  "notes": "Recorded the externally supplied notification sound-file change: tasktool ding playback now prefers SUPERSTAR_NOTIFY_DING_FILE or /usr/share/sounds/Enchanted/stereo/bell.ogg before falling back to sound-theme names.",
  "refs": [
    "tools/tasktool/notify.py"
  ],
  "started": null,
  "status": "done",
  "title": "Prefer explicit notification ding sound file",
  "worktree_branch": null,
  "worktree_in_place": false,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
