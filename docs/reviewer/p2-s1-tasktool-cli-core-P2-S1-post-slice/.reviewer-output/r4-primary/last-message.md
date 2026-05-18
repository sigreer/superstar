1. Findings

F1 — RESOLVED — Relative `--reviewer-chain` paths remain fixed by resolving explicit relative paths against `repo_root`.

F2 — RESOLVED — Reviewer-chain discovery still uses boundary-aware matching and the `p1-s1` / `p1-s10` regression tests pass.

F3 — RESOLVED — `tasktool set --status blocked` is still rejected cleanly by argparse.

F4 — RESOLVED — The plan now records post-implementation evidence and updated test count.

S1.F1 — Severity: important — Still partially unresolved. `scan_orphan_ids()` now detects lowercase reviewer slice IDs, but `next_slice_id()` does not use reviewer artifacts at all. In [allocate.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/allocate.py:51), slice allocation scans only `docs/specs` and `docs/plans`, so a lowercase reviewer folder like `docs/reviewer/p2-s3-post-slice/` is ignored and `next_slice_id(Project(...P2...), "P2", root)` returns `S1` even though `scan_orphan_ids(root, "slice")` sees `[3]`. This leaves the original plan/reviewer lowercase collision risk open for reviewer-only artifacts.

S1.F2 — RESOLVED — [schema_gen.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/schema_gen.py:8) now splits slice and non-blocked status enums; tests cover task/phase/cross excluding `blocked` and slice including it.

S1.F3 — RESOLVED — [__init__.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/__init__.py:4) now exports the promised model and serializer API, with `__all__` coverage.

2. Open Questions / Assumptions

I’m treating reviewer-folder IDs as still in scope for S1.F1 because the prior finding explicitly named lowercase plan/reviewer artifact names, and `scan_orphan_ids()` already scans `docs/reviewer`.

3. Suggested Document Edits

Update the post-implementation evidence line for S1.F1 at [the plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:3141) after fixing `next_slice_id()` to include matching reviewer folders, or mark the current fix as partial.

4. Verification

Ran:

`PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`

Result: 138 tests passed.

Also ran `bash -n tools/tasktool/install.sh` and schema JSON validation successfully.

Additional repro showed `scan slice: [3]` but `next slice: S1` for a lowercase `docs/reviewer/p2-s3-post-slice` folder.

5. Overall verdict

revise