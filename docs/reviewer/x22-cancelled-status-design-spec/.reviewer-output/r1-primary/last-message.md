1. Findings

F1. Severity: blocking. The spec’s “tasks must not parse `cancelled`” requirement is not enforceable as written. `Task.status` uses the shared `Status` enum in `tools/tasktool/model.py:20-28`, and `from_dict()` parses task status through `Status(v)` in `tools/tasktool/serialize.py:75-84`. If `Status.CANCELLED` is added, a raw task row with `"status": "cancelled"` will parse. Also, `tasktool validate` loads via `load_project()` and then calls `validate_project()`; it does not run JSON Schema validation first (`tools/tasktool/commands.py:1686-1689`). The spec only requires a JSON-schema test at `docs/specs/2026-05-23-X22-cancelled-status-design.md:71` and then says to generalize `validate.py:73` to `is_terminal()` at line 168, which would make a cancelled task with `closed` look semantically acceptable unless `_check_task()` explicitly rejects it. Add a spec requirement that semantic validation rejects `Status.CANCELLED` for tasks, and add a `tasktool validate`/`validate_project` test, not only a JSON-schema test.

F2. Severity: important. The schedule contract refers to fields that do not exist today. The spec says `done_deps` / `open_deps` “keep current meaning” at `docs/specs/2026-05-23-X22-cancelled-status-design.md:153`, but current `cmd_schedule()` emits `depends_on`, `waiting_on`, and `ready`; there is no `done_deps` or `open_deps` in `tools/tasktool/commands.py:1491-1505`. This creates implementation ambiguity: either the change is adding three new fields, or it is preserving `waiting_on` and adding only `cancelled_deps`. Specify the exact before/after JSON shape and text rendering.

F3. Severity: important. The `phase-status` cancelled-dependency section is underspecified against the current command shape. `phase-status` is global and takes no phase id (`tools/tasktool/cli.py:226-228`), and current output only lists open phases, open cross-cutting, and recent archived phases (`tools/tasktool/commands.py:1523-1569`). The spec says it should grow `Blocked by cancelled deps: <slice-id> waiting on <cancelled-dep-id>` at `docs/specs/2026-05-23-X22-cancelled-status-design.md:155`, but does not say whether this is computed across all active phases, whether JSON output also changes, or where the section appears. Add those details and a test expectation.

F4. Severity: important. `show`/`brief` cancellation-reason surfacing conflicts with default cross-cutting auto-archive. The spec says cancelling an X item auto-archives by default at `docs/specs/2026-05-23-X22-cancelled-status-design.md:117`, and later says `brief` and `show` surface the cancellation reason for cancelled rows at line 163. But current `cmd_show()` only finds active rows via `_find_item()` (`tools/tasktool/commands.py:1399-1402`), and `_find_item()` rejects archived X ids as “not found in active tasklist” (`tools/tasktool/commands.py:532-539`). If default `tasktool cancel X22` archives the row, `tasktool show X22` will not surface anything unless the spec also requires archive lookup. Clarify whether reason surfacing applies only to active `--no-archive` rows, or add an explicit archive-read behavior.

F5. Severity: minor. The notification requirement is not grounded in the current notifier API. The spec says to reuse the “done” audio cue with a “Cancelled” title prefix at `docs/specs/2026-05-23-X22-cancelled-status-design.md:173`, but `notify.py` currently builds a generic event message as `<id> <status>: <title>` (`tools/tasktool/notify.py:362-370`) and playback uses TTS first, then the generic `tasktool` ding (`tools/tasktool/notify.py:247-253`). There is no status-specific “done audio cue” or title-prefix mechanism. Specify whether the event payload title should be mutated, the spoken message should be special-cased, or the requirement is simply to emit status `cancelled`.

2. Open questions / assumptions

- Should a cancelled phase with no open slices be allowed without `--cascade`, even if some children are already `cancelled`? The spec implies yes, but a test should pin it.
- Should `archive-cross X22` accept an already-cancelled visible X item created via `cancel --no-archive`? The `_archive_cross_at_root` section implies yes; add this as a test.
- Should `cmd_block`, `cmd_unblock`, `cmd_deps`, `cmd_ratify`, `cmd_ref`, `cmd_note`, and `cmd_title` refuse cancelled rows, or are notes/refs/title edits still allowed after cancellation? The spec covers `start`, `close`, and `set`, but not other lifecycle-adjacent mutations.

3. Suggested document edits

- In “Validation”, add: `_check_task()` must reject `Status.CANCELLED` regardless of `closed`, because normal tasktool loading and validation do not rely on JSON Schema.
- Replace the schedule bullet with a concrete JSON example showing existing `waiting_on` plus new `cancelled_deps`, or explicitly introduce `done_deps` / `open_deps` as new fields.
- Expand the `phase-status` bullet to say whether it scans every active phase and whether `--format json` includes cancelled-dependency rows.
- Amend the render/surfacing section to distinguish active cancelled X rows from archived cancelled X rows.
- Rewrite the notification bullet around the actual event contract: emitted status, title, message, and fallback audio behavior.

4. Verification gaps / commands that should be run

- `python -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_cli_integration.py -q`
- `python -m pytest tools/tasktool/tests/test_importer.py tools/tasktool/tests/test_render.py tools/tasktool/tests/test_brief.py tools/tasktool/tests/test_notify.py -q`
- `tools/tasktool/tasktool validate --strict-format`
- Add focused tests for semantic task rejection, schedule JSON shape, global `phase-status` cancelled-dep rendering, archived cancelled X lookup behavior if supported, and `cancel --no-archive` followed by `archive-cross`.

Overall verdict: revise

