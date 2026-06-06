Findings

F1 Severity: blocking — UNRESOLVED. The import strategy is still not executable for the direct-run acceptance commands. The plan correctly adds `pythonpath = ["tools"]` for pytest and says CLI entrypoints insert `tools` themselves, but both direct-run shims insert `Path(__file__).resolve().parents[2]`, which is the repo root, not `tools`: `docs/plans/2026-06-06-X29-timeline-generator.md:43`, `docs/plans/2026-06-06-X29-timeline-generator.md:1777`, `docs/plans/2026-06-06-X29-timeline-generator.md:1932`. With that path, `from timeline import ...` will not find `tools/timeline`. The planned unit tests call `timeline.main(...)` after importing the package under pytest, so they do not exercise this direct script path: `docs/plans/2026-06-06-X29-timeline-generator.md:1710`. The acceptance commands do use the direct script path and would fail: `docs/plans/2026-06-06-X29-timeline-generator.md:2291`, `docs/plans/2026-06-06-X29-timeline-generator.md:2301`. Change both shims to insert `parents[1]`, or change the import/package layout consistently, and add at least one subprocess test for `python3 tools/timeline/timeline.py ...`.

F2 Severity: important — RESOLVED. The X dot now receives `dot x-node`, CSS covers `body.show-x .dot.x-node`, and the plan adds `test_x_dot_hidden_with_card`: `docs/plans/2026-06-06-X29-timeline-generator.md:1374`, `docs/plans/2026-06-06-X29-timeline-generator.md:1584`, `docs/plans/2026-06-06-X29-timeline-generator.md:1634`.

F3 Severity: important — RESOLVED. The backfill plan now adds `_phase_closes`, `_clamp_start`, and applies the clamp before writing mined `started` dates: `docs/plans/2026-06-06-X29-timeline-generator.md:2149`, `docs/plans/2026-06-06-X29-timeline-generator.md:2166`, `docs/plans/2026-06-06-X29-timeline-generator.md:2220`.

F4 Severity: important — RESOLVED. The plan now explicitly narrows replay to status transitions only and ties date fields to final-file precedence: `docs/plans/2026-06-06-X29-timeline-generator.md:623`.

F5 Severity: important — RESOLVED. The closeout instruction now uses `tasktool close X29` and states archive-on-close is intended: `docs/plans/2026-06-06-X29-timeline-generator.md:2316`.

F6 Severity: minor — RESOLVED. The plan now tests and renders duration plus header span: `docs/plans/2026-06-06-X29-timeline-generator.md:1379`, `docs/plans/2026-06-06-X29-timeline-generator.md:1389`, `docs/plans/2026-06-06-X29-timeline-generator.md:1459`, `docs/plans/2026-06-06-X29-timeline-generator.md:1561`.

Open questions / assumptions

- I assume `from timeline import ...` remains the intended import style, matching the new pytest `pythonpath = ["tools"]` entry.

Suggested document edits

- Replace `Path(__file__).resolve().parents[2]` with `parents[1]` in both `timeline.py` and `backfill.py` snippets.
- Add a subprocess CLI test that runs `python3 tools/timeline/timeline.py --repo <fixture> -o <out>` from the repo root, so the direct-run shim is covered before Task 14.

Verification gaps / commands that should be run

- `python3 -m pytest tools/timeline/tests/test_cli.py -q`
- `python3 tools/timeline/timeline.py --repo . -o /tmp/superstar-timeline.html`
- `python3 tools/timeline/backfill.py --repo /home/simon/Dev/sigreer/multistore`

Overall verdict: revise

