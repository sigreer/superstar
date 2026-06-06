Findings

F1 Severity: blocking — The planned package/import path is not executable. The plan creates `tools/timeline/__init__.py` and only adds `tools/timeline/tests` to `testpaths` (`docs/plans/2026-06-06-X29-timeline-generator.md:20`, `:37`), but tests import `from timeline import ...` (`:141`, `:516`, `:918`, `:1629`) and the CLI direct-run shim inserts the repo root, not `tools`, before `from timeline import extract, model, render` (`:1719-1722`). From the repo root, `timeline` is not importable unless `tools` is on `sys.path`/`PYTHONPATH`. This makes the planned test pass gates and `python3 tools/timeline/timeline.py ...` acceptance command fail. Add an explicit import strategy, for example `pythonpath = ["tools"]` in pytest config plus CLI `sys.path.insert(0, str(Path(__file__).resolve().parents[1]))`, or change the package/import layout consistently.

F2 Severity: important — The X-item toggle does not actually hide the whole X item. The renderer adds `x-node` only to the card (`docs/plans/2026-06-06-X29-timeline-generator.md:1482-1486`), while `_card()` always emits a separate dot without that class (`:1524-1533`); CSS hides only `.x-node` (`:1577-1578`). The spec requires X-items to show/hide instantly as items (`docs/specs/2026-06-06-X29-timeline-design.md:155-158`). Add a test that the X dot is hidden with the card, then either wrap card+dot or pass an extra dot class.

F3 Severity: important — Backfill omits the spec’s “cross-checked against previous phase close” requirement. The spec requires commit-mined starts to be cross-checked against the previous phase close for the sequential legacy era (`docs/specs/2026-06-06-X29-timeline-design.md:169-171`). The plan only mines first mentions (`docs/plans/2026-06-06-X29-timeline-generator.md:1912-1926`) and blindly fills `started` from `mentions` (`:2100-2104`). Add ordering/cross-check logic and a test for a mined start before/after the previous phase close.

F4 Severity: important — Replay does not record date field changes, despite the spec requiring it. The spec says replay records “status transitions and date field changes per item” (`docs/specs/2026-06-06-X29-timeline-design.md:102-105`). The plan’s replay model extracts only statuses (`docs/plans/2026-06-06-X29-timeline-generator.md:603-611`) and only appends transitions when status changes (`:637-646`), then `apply_replay()` only consumes status transitions (`:750-755`). Add date-field history capture or explicitly narrow the spec; otherwise date-only edits without a status transition cannot upgrade/fill correctly.

F5 Severity: important — Closeout command is inconsistent with the tracker workflow for an X item. The row is cross-cutting (`docs/tasklist.json:210-224`), but the plan says to finish with `tasktool set X29 --status done` “via the close gate” (`docs/plans/2026-06-06-X29-timeline-generator.md:2197-2198`). Existing workflow expects `tasktool close X29` for cross-cutting items, which closes and archives by default. Correct the closeout instruction and state whether archive-on-close is desired.

F6 Severity: minor — Two visual acceptance details are not implemented or tested in the plan. The spec requires click expansion to include computed duration (`docs/specs/2026-06-06-X29-timeline-design.md:146-147`) and the header to show the overall date span (`:159-160`). The planned detail block has started/closed only (`docs/plans/2026-06-06-X29-timeline-generator.md:1524-1527`), and the header has counts plus generation time only (`:1582-1587`). Add small tests and fields for duration/date span.

Open questions / assumptions

- Should `tools/timeline` follow the existing `tasktool` style with `tools` on `PYTHONPATH`, or should it be imported as `tools.timeline`?
- Is X29 intended to archive immediately on close, or remain visible with `--no-archive` for a release/version-bump follow-up?
- Is actual `backfill.py --write` in multistore deliberately out of scope for X29, despite spec acceptance item 2 depending on it?

Suggested document edits

- Add the chosen import path strategy to Task 1 and update all test/CLI commands accordingly.
- Add tests for X dot visibility, replay date-field changes, backfill previous-phase-close cross-check, computed duration, and header date span.
- Replace the final closeout command with the correct cross-cutting lifecycle command.

Verification gaps / commands that should be run

- `python3 -m pytest tools/timeline/tests -q`
- `python3 -m pytest -q`
- `python3 tools/timeline/timeline.py --repo . -o /tmp/superstar-timeline.html`
- `python3 tools/timeline/timeline.py --repo /home/simon/Dev/sigreer/multistore -o /tmp/multistore-timeline.html`
- `python3 tools/timeline/backfill.py --repo /home/simon/Dev/sigreer/multistore`
- `tasktool validate`

Overall verdict: revise

