# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-06-X29-timeline-generator.md` (Task 1, Step 2)
- Verification: Task 1 now sets `pythonpath = ["tools"]` in `[tool.pytest.ini_options]`, making the `from timeline import ...` strategy explicit rather than relying on importlib-mode package-root inference. CLI entrypoints (`timeline.py`, `backfill.py`) insert `Path(__file__).resolve().parents[1]` (= `tools/`) when run as scripts — both shims already pointed at `parents[1]`, not the repo root.

Notes:
The `tasktool` suite relies on the same `tools`-on-sys.path convention implicitly (verified: `python3 -m pytest tools/tasktool/tests/test_allocate.py -q` passes while `python3 -c "import tasktool"` fails); the explicit `pythonpath` entry removes the fragility for both.

## F2
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-06-X29-timeline-generator.md` (Task 10, Step 3: `_card` now computes `dot_css = "dot x-node" if "x-node" in css else "dot"`; CSS adds `body.show-x .dot.x-node{display:block}`)
- Verification: new test `test_x_dot_hidden_with_card` asserts `class="dot x-node` appears in the emitted HTML.

## F3
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-06-X29-timeline-generator.md` (Task 13: new `_phase_closes` + `_clamp_start` helpers; `plan_rewrites` clamps mined starts)
- Verification: new tests `test_started_clamped_to_previous_phase_close` (mined 04-20 vs prev close 04-27 → clamped to 04-27) and `test_started_kept_when_after_previous_close` (mined 04-25 vs prev close 04-20 → kept).

## F4
Status: fixed
Evidence:
- Files: `docs/specs/2026-06-06-X29-timeline-design.md` (Date resolution, rule 3); `docs/plans/2026-06-06-X29-timeline-generator.md` (Task 4 `replay` docstring)
- Verification: spec narrowed per the review's offered alternative — replay is deliberately status-transition-only; date fields are read once from the final file and are already authoritative for the date, so change-tracking them adds no resolvable information under the precedence rules. The plan docstring now states this and points at the spec section.

## F5
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-06-X29-timeline-generator.md` (Task 14, Step 6)
- Verification: closeout now reads `tasktool close X29` (cross-cutting close gate; closes and archives by default — archive-on-close is the intended end state), plus the CLAUDE.md version-bump question before any release scripts.

## F6
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-06-X29-timeline-generator.md` (Task 10: `_duration_text` helper appended to the card detail; `span_text` computed from anchors and rendered in the header meta line)
- Verification: new tests `test_detail_includes_duration` ("2h 14m") and `test_header_shows_date_span` ("29 Apr 2026 … 6 Jun 2026").

Notes:
On the open questions: (1) `tools` on `sys.path` via explicit `pythonpath`, matching tasktool. (2) X29 archives on close — intended. (3) Yes — `backfill.py --write` in multistore is deliberately out of this repo's execution scope: Task 14 Step 4 proves the dry-run; the `--write` + human review happens in the multistore repo, which is where spec acceptance 2 is exercised.
