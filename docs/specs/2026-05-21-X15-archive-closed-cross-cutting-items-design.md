# X15 - Archive closed cross-cutting items

**Status:** spec
**Tasktool ID:** X15 (cross-cutting)
**Date:** 2026-05-21

## Problem

Cross-cutting items (`X*`) are top-level work items that are not contained by a phase. They are useful for small workflow fixes, tool hardening, or opportunistic cleanup that does not deserve a full phase. Once completed, however, closed X-items remain in the active `cross_cutting` array and continue to appear in rendered tasklists. Over time, those completed rows pollute the working view even though they no longer require action.

Phase work already has a lossless archive path: `tasktool archive-phase` removes the phase from active `docs/tasklist.json`, writes a full archive file under `docs/archived-tasks/`, and leaves compact pointer metadata in the active tasklist. Cross-cutting work needs the same “move it out of the active view without losing evidence” treatment, scaled to a single X-item instead of a phase containing slices.

## Goals

1. Archive completed cross-cutting items by default when they are closed.
2. Preserve archived X-item data losslessly in a per-item archive file.
3. Keep an explicit opt-out for the rare case where a closed X-item should remain visible in the active tasklist.
4. Provide a manual command to archive a done-but-visible X-item later.

## Non-goals

- No three-day auto-archive policy in this slice.
- No standalone slice archival. Slices remain archived through their parent phase.
- No compaction or lossy summary format for archived X-items.
- No change to phase archival semantics.
- No `unarchive-cross` command. The archive file embeds full JSON so a future unarchive command can be implemented, but this slice does not ship one.
- No schema version bump. `archived_cross_cutting` is backwards-compatible and defaults to `[]` for legacy tasklists.

## Design

### 1. Archive model

Add a new top-level archive pointer list to `docs/tasklist.json`:

```json
"archived_cross_cutting": [
  {
    "archived_date": "2026-05-21",
    "archived_path": "docs/archived-tasks/X15-archive-closed-cross-cutting-items.md",
    "id": "X15",
    "title": "Archive closed cross-cutting items"
  }
]
```

The active `cross_cutting` array remains the source of truth for visible, active X-items. Once an X-item is archived, it is removed from `cross_cutting` and represented in `archived_cross_cutting` by pointer metadata only.

Each archived X-item gets its own markdown archive file under `docs/archived-tasks/`:

```text
docs/archived-tasks/X15-archive-closed-cross-cutting-items.md
```

The archive file stores full canonical JSON for the X-item, including title, created date, started date, status, closed date, refs, and notes. The operation is lossless relocation, not data compaction. The mental model is the same as phase archives: phases are folders in the archive box; X-items are loose papers in the same box.

### 2. Default close behavior

`tasktool close X15` closes and archives the cross-cutting item in one operation:

1. Resolve `X15` from active `cross_cutting`.
2. Set `status` to `done`.
3. Stamp `closed` if it was not already set.
4. Apply any supplied refs or close note using the existing close semantics.
5. Build the archive markdown content in memory, including full X-item JSON.
6. Remove the X-item from active `cross_cutting` in memory.
7. Append the pointer row to `archived_cross_cutting` in memory.
8. Validate the mutated project before any archive file is written.
9. Write `docs/archived-tasks/X15-<slug>.md`.
10. Save `docs/tasklist.json`.
11. Stage both `docs/tasklist.json` and the new archive file.
12. Emit the existing done notification exactly once.

Cross-cutting close remains ungated by external review, matching today’s behavior.

### 3. Close opt-out

Add `--no-archive` to `tasktool close` for cross-cutting items:

```sh
tools/tasktool/tasktool close X15 --no-archive
```

For X-items only, `--no-archive` means “close this item but leave it visible in active `cross_cutting`.” It is an opt-out of immediate archiving, not an instruction to keep the row visible forever. The user can archive the row later with `archive-cross`.

For slices and phases, supplying `--no-archive` fails with `--no-archive is only valid for cross-cutting items`. The flag exists to control X-item close behavior only.

### 4. Manual archive command

Add:

```sh
tools/tasktool/tasktool archive-cross X15
```

This archives a closed X-item that still exists in active `cross_cutting`, typically because it was closed with `--no-archive` or predates this feature.

Rules:

- `archive-cross` accepts only cross-cutting IDs.
- The X-item must exist in active `cross_cutting`.
- The X-item must be `done`.
- If an archive pointer already exists for that ID, fail rather than overwrite.
- If the archive file path already exists, fail rather than overwrite.
- On success, use the same atomic ordering as default close: build archive content in memory, mutate the project in memory, validate, write the archive file, save `docs/tasklist.json`, and stage both touched files.
- `archive-cross` does not re-emit a done notification, because it archives an item that is already done. The status transition happened at close time.

There is no bulk auto-cleanup command in this slice.

### 5. Archive file format

Use the phase archive style but scaled to one cross-cutting item:

````md
# X15 - Archive closed cross-cutting items

status: done
created: 2026-05-21
closed: 2026-05-21

## References

- docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md

## Notes

<notes, if present>

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-21",
  "created": "2026-05-21",
  "id": "X15",
  "notes": "",
  "refs": [],
  "started": null,
  "status": "done",
  "title": "Archive closed cross-cutting items"
}
```
````

The exact JSON should be emitted through the existing canonical serialization path or a small helper that shares the same ordering rules. The archive file is the durable evidence store.

### 6. Rendering and listing

`tasktool render` should keep showing active `cross_cutting` as it does today, but archived X-items should no longer appear in that active section.

Add an archived X section after archived phases when `archived_cross_cutting` is non-empty:

```md
## Archived cross-cutting (`X*`)

- **X15** - Archive closed cross-cutting items -> [`docs/archived-tasks/X15-archive-closed-cross-cutting-items.md`](docs/archived-tasks/X15-archive-closed-cross-cutting-items.md) (2026-05-21)
```

Archive pointers are append-only in archive time order, matching `archived_phases`.

`tasktool list --open` naturally excludes archived X-items because they are no longer in `cross_cutting`. `tasktool list --kind cross` should continue to list active X-items only. A separate archive listing flag is not required for this slice; `render` is enough for human visibility.

`tasktool brief X15` after archival should fail with the same active-tasklist-not-found semantics as archived phases rather than loading the archive file. The archive file is evidence, not part of the active workflow surface.

## Component boundaries

- `tools/tasktool/model.py` owns the new `ArchivedCrossCutting` dataclass and `Project.archived_cross_cutting` field.
- `tools/tasktool/serialize.py` owns backwards-compatible loading when older tasklists omit `archived_cross_cutting`.
- `tools/tasktool/validate.py` owns ID uniqueness and date/path validation for archived X pointers.
- `tools/tasktool/migrate.py` owns migration/merge semantics for the new top-level collection so authoritative-checkout reconciliation preserves archived X pointers.
- `tools/tasktool/schema_gen.py` owns JSON schema coverage for `archived_cross_cutting`.
- `tools/tasktool/commands.py` owns archive behavior, including `cmd_archive_cross`, close-with-default-archive, and archive file writing.
- `tools/tasktool/cli.py` owns `close --no-archive` and the new `archive-cross` subcommand.
- `tools/tasktool/render.py` owns displaying archived X pointers.
- `tools/tasktool/brief.py` keeps archived X-items outside the active brief surface.
- `tools/tasktool/tests/` owns behavioral coverage.
- `skills/tasklist-discipline/SKILL.md` owns user-facing workflow guidance for closing and archiving X-items.

## Error handling

- `tasktool close X15` where `X15` is already archived: fail with `cross-cutting X15 not found in active tasklist; it may already be archived`. Implement this by checking `archived_cross_cutting` in the close/archive-cross wrapper before falling back to the generic not-found error.
- `tasktool close X15 --no-archive` succeeds and leaves the item in active `cross_cutting`.
- `tasktool close P4.S1 --no-archive` fails with `--no-archive is only valid for cross-cutting items`.
- `tasktool archive-cross X15` where `X15` is not `done`: fail with `cross-cutting X15 must be done before archive; run tasktool close X15 first`.
- `tasktool archive-cross X15` where the pointer already exists: fail with `cross-cutting X15 is already archived`.
- Archive path collision: fail before mutating `docs/tasklist.json`.
- Validation should reject duplicate archived X IDs, archived X IDs that also appear in active `cross_cutting`, invalid archived dates, and empty archive paths.

## Testing

Add focused tests under `tools/tasktool/tests/`:

1. `test_close_cross_archives_by_default` - create an X-item, close it, assert it is removed from `cross_cutting`, added to `archived_cross_cutting`, and a markdown archive file exists.
2. `test_close_cross_no_archive_keeps_visible` - close with `--no-archive`, assert the item remains in active `cross_cutting` with `status: done` and no archive pointer/file is created.
3. `test_archive_cross_archives_done_visible_item` - close with `--no-archive`, then run `archive-cross`, assert the item moves to the archive pointer list and the file is written.
4. `test_archive_cross_rejects_ready_item` - `archive-cross` on a ready X-item fails with the done-before-archive message.
5. `test_close_no_archive_rejects_non_cross_items` - supplying `--no-archive` when closing a slice or phase fails clearly.
6. `test_validate_rejects_duplicate_archived_cross_ids` - duplicate archive pointers fail validation.
7. `test_validate_rejects_active_and_archived_cross_id_collision` - the same `X*` ID cannot appear in both active and archived lists.
8. `test_render_shows_archived_cross_section` - render includes active X-items separately from archived X pointers.
9. `test_archive_cross_preserves_full_json` - archive markdown contains the full X-item JSON, including refs and notes.
10. `test_legacy_tasklist_without_archived_cross_cutting_loads` - older `docs/tasklist.json` files without the new field load and save normally.
11. `test_list_kind_cross_excludes_archived_items` - `tasktool list --kind cross` lists active X-items only after one has been archived.
12. `test_archive_cross_atomicity_no_orphan_file_on_validation_failure` - force validation failure after the in-memory archive move and assert no archive markdown file is written and the active tasklist remains unchanged.
13. `test_tasktool_migrate_preserves_archived_cross_cutting` - migration/merge logic round-trips the new archive pointer list.
14. `test_schema_includes_archived_cross_cutting` - generated schema includes the new top-level field.
15. `test_archive_cross_does_not_reemit_done_notification` - closing emits the done notification once; later manual archive does not emit a second done event.

Run:

```sh
tools/tasktool/tasktool validate --strict-format
python3 -m pytest tools/tasktool/tests -q
```

## Rollout

This repo already has many closed cross-cutting items in active `cross_cutting`. This feature does not need to bulk-archive them automatically as part of implementation. After the feature lands, the operator can archive selected completed X-items with:

```sh
tools/tasktool/tasktool archive-cross X1
tools/tasktool/tasktool archive-cross X2
```

Newly closed X-items will archive by default unless closed with `--no-archive`.

## Open questions

None. Product decisions settled:

- Archive is lossless per-item relocation to `docs/archived-tasks/`.
- `tasktool close X*` archives by default.
- `tasktool close X* --no-archive` is the immediate archive opt-out.
- `tasktool archive-cross X*` is the manual later cleanup path.
- No auto-archive policy in this slice.
