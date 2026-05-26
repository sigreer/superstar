# X9 - Coalesce bursty tasktool audio notifications

status: done
created: 2026-05-19
closed: 2026-05-19

## References

- tools/tasktool/notify.py
- tools/tasktool/tests/test_notify.py

## Notes

Rapid tasktool status changes currently spawn independent notifier processes, causing overlapping TTS/audio. Add a single-audio queue with at most three queued tasktool events; overflow should collapse to a single 'multiple other events' summary and drop further items.
Added a file-backed notification queue shared by agent dings and tasktool TTS. Only one worker drains audio at a time. Queue capacity is three pending events; overflow keeps the first two pending items and replaces the rest with a single 'Multiple other events' summary, dropping further burst items while the summary remains queued.

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-19",
  "created": "2026-05-19",
  "id": "X9",
  "notes": "Rapid tasktool status changes currently spawn independent notifier processes, causing overlapping TTS/audio. Add a single-audio queue with at most three queued tasktool events; overflow should collapse to a single 'multiple other events' summary and drop further items.\nAdded a file-backed notification queue shared by agent dings and tasktool TTS. Only one worker drains audio at a time. Queue capacity is three pending events; overflow keeps the first two pending items and replaces the rest with a single 'Multiple other events' summary, dropping further burst items while the summary remains queued.",
  "refs": [
    "tools/tasktool/notify.py",
    "tools/tasktool/tests/test_notify.py"
  ],
  "started": null,
  "status": "done",
  "title": "Coalesce bursty tasktool audio notifications",
  "worktree_branch": null,
  "worktree_in_place": false,
  "worktree_path": null,
  "worktree_prune_pending": false,
  "worktree_prune_pending_at": null,
  "worktree_pruned_at": null
}
```
