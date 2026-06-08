1. Findings

F1. Severity: blocking — Task 4’s quiet-run bounds are directionally wrong for newest-first rendering.  
In [docs/plans/2026-06-08-X29-timeline-day-axis.md:465](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-06-08-X29-timeline-day-axis.md:465)-[471](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-06-08-X29-timeline-day-axis.md:471), the same date predicates are used for both `asc` and `desc`. But in `desc`, `nxt_d` is visually above the quiet run and `prev_d` is visually below it. The proposed code computes `top` from older dates (`<= prev_d`) and `bot` from newer dates (`>= nxt_d`), so `bot - top` will usually be negative and the quiet segment is skipped. The existing implementation’s `_gap_bounds` explicitly branches on direction for this reason in `tools/timeline/render.py:230-243` in the X29 worktree. This misses the spec’s dual-direction/default newest-first acceptance in [docs/specs/2026-06-08-X29-timeline-day-axis-design.md:141](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-08-X29-timeline-day-axis-design.md:141)-[146](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-08-X29-timeline-day-axis-design.md:146).

F2. Severity: important — The plan’s test paths and commands do not match the actual test layout.  
The plan repeatedly targets `tools/timeline/tests/test_render.py`, for example [docs/plans/2026-06-08-X29-timeline-day-axis.md:39](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-06-08-X29-timeline-day-axis.md:39), [88](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-06-08-X29-timeline-day-axis.md:88), [135](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-06-08-X29-timeline-day-axis.md:135), [512](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-06-08-X29-timeline-day-axis.md:512), and [611](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-06-08-X29-timeline-day-axis.md:611). In the X29 worktree there is no `tools/timeline/tests/test_render.py`; the live tests are split across `test_render_lanes.py`, `test_render_rules.py`, `test_render_html.py`, `test_render_layout.py`, `test_render_direction.py`, and `test_render_scale.py`. Following the plan literally makes the focused pytest commands and `git add` commands fail.

F3. Severity: important — The proposed active-day/date-marker test helper import contradicts the repo’s import pattern.  
Task 4 suggests `from tools.timeline.tests import helpers` at [docs/plans/2026-06-08-X29-timeline-day-axis.md:354](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-06-08-X29-timeline-day-axis.md:354), but the existing test suite imports helpers as `from timeline.tests.helpers import ...` (`tools/timeline/tests/test_render_html.py:4`, `tools/timeline/tests/test_render_direction.py:12`). This is a small syntax change, but as written it creates needless import drift in new tests.

2. Open questions / assumptions

I assume the plan will be committed or otherwise made visible to the X29 worktree before handoff. Current `main` has the plan staged but not in `HEAD`, so the plan’s `git merge --no-edit main` instruction will not bring this plan into the worktree until that commit exists.

3. Suggested document edits

Revise Task 4’s quiet-run bounds snippet to branch by direction, mirroring the old `_gap_bounds` logic: for `asc`, content before the run is `<= prev_d` and after is `>= nxt_d`; for `desc`, the visual “above” side is `>= nxt_d` and the visual “below” side is `<= prev_d`.

Replace all `tools/timeline/tests/test_render.py` references with the actual target modules, for example lane/classifier tests in `test_render_lanes.py`, phase-span/duration helper tests in `test_render_rules.py` or `test_render_html.py`, markup tests in `test_render_html.py`, and direction tests in `test_render_direction.py`.

Use `from timeline.tests import helpers` or `from timeline.tests.helpers import ...` consistently with the existing suite.

4. Verification gaps / commands that should be run

After the document edits, the plan should use focused commands against real modules, for example:

`python3 -m pytest tools/timeline/tests/test_render_lanes.py tools/timeline/tests/test_render_rules.py -k "end_of_day or distinct_lanes or classify or duration" -v`

`python3 -m pytest tools/timeline/tests/test_render_html.py tools/timeline/tests/test_render_direction.py -k "date_pill or x_only or no_date or direction" -v`

`python3 -m pytest tools/timeline/tests -q`

Overall verdict: revise