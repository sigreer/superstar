# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-08-X29-timeline-day-axis.md` — Task 4, Step 3
  quiet-run bounds block.
Notes:
The quiet-segment bounds now branch by reading direction, mirroring the retired
`_gap_bounds`. For `desc` (newest-first) the visually-above side is the newer
content (`date >= nxt_d`) and below is older (`date <= prev_d`); for `asc` the
older side is above (`date <= prev_d`) and newer below (`date >= nxt_d`). This
prevents the negative `bot - top` that previously dropped the segment in
newest-first (the default) and satisfies the spec's dual-direction acceptance.

## F2
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-08-X29-timeline-day-axis.md` — added a "Test layout"
  note in the header and File Structure; every task's test target and focused
  pytest command retargeted.
Notes:
There is no `test_render.py`. Tests are now placed in the real modules: `_eff_end`
+ lanes + `classify_days` in `test_render_lanes.py`; `_duration_text` in
`test_render_rules.py`; pills/dividers/x-only/dates-off-faces in
`test_render_html.py`; dual-direction pills in `test_render_direction.py`. All
focused `pytest` and `git add` commands reference these real paths.

## F3
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-08-X29-timeline-day-axis.md` — all test snippets.
Notes:
Test imports now follow the existing suite convention: `from timeline import
model, render` and `from timeline.tests.helpers import phase, slice_, x` (no
`tools.` prefix). The speculative `helpers.render_sample` / `slice_card_face` API
from r1 was removed entirely; Task 4/5 tests now build items inline with
`model._item(...)` and assert on the HTML with `re`, exactly like the existing
`test_render_html.py` / `test_render_direction.py`. Date values use
`model.DateValue(when, precision, source)`.

Notes (assumption raised by reviewer):
The plan and spec are committed on `main` before handoff, so Step 0.1's
`git merge --no-edit main` brings them onto the worktree branch. Step 0.1 now
states this explicitly.
