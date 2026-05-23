1. Findings

F1. Severity: blocking — Task 3 targets the wrong migration module/API. The plan says to add a v1→v2 schema migration in `tools/tasktool/migrate.py` and test `from tasktool.migrate import migrate_file` ([docs/plans/2026-05-23-P6.S1-workflow-step-field.md:391](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-23-P6.S1-workflow-step-field.md:391>), [464](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-23-P6.S1-workflow-step-field.md:464>), [475](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-23-P6.S1-workflow-step-field.md:475>)). In the repo, `tools/tasktool/migrate.py` is the authoritative/local drift reconciler, not a tasklist schema migrator, and it has no `migrate_file` dispatcher ([tools/tasktool/migrate.py:44](</home/simon/Dev/sigreer/skills/superstar/tools/tasktool/migrate.py:44>), [52](</home/simon/Dev/sigreer/skills/superstar/tools/tasktool/migrate.py:52>), [86](</home/simon/Dev/sigreer/skills/superstar/tools/tasktool/migrate.py:86>)). Implementing this as written risks corrupting a separate subsystem and starts from tests that cannot import the planned API. Either add an explicit schema-upgrade path in the actual load/validate flow, or remove Task 3’s fake migration API and document that v1 rows are tolerated by `from_dict` plus schema version emission.

F2. Severity: important — The plan’s schema test instructions do not match the current schema generator. It tells implementers to import `generate()` and inspect `$defs`/`definitions` ([docs/plans/2026-05-23-P6.S1-workflow-step-field.md:404](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-23-P6.S1-workflow-step-field.md:404>), [425](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-23-P6.S1-workflow-step-field.md:425>)), but the module exposes `build_schema()` and inlines phase/slice schemas under `properties.phases.items...` ([tools/tasktool/schema_gen.py:7](</home/simon/Dev/sigreer/skills/superstar/tools/tasktool/schema_gen.py:7>), [42](</home/simon/Dev/sigreer/skills/superstar/tools/tasktool/schema_gen.py:42>), [70](</home/simon/Dev/sigreer/skills/superstar/tools/tasktool/schema_gen.py:70>)); existing tests already use `build_schema()` ([tools/tasktool/tests/test_schema_gen.py:1](</home/simon/Dev/sigreer/skills/superstar/tools/tasktool/tests/test_schema_gen.py:1>), [18](</home/simon/Dev/sigreer/skills/superstar/tools/tasktool/tests/test_schema_gen.py:18>)). Rewrite Task 3 tests against the existing schema shape so the TDD steps are executable.

F3. Severity: important — `cmd_infer_step` is specified with the wrong project loader. The plan snippet calls `load_project(repo_root)` ([docs/plans/2026-05-23-P6.S1-workflow-step-field.md:1132](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-23-P6.S1-workflow-step-field.md:1132>)), but `load_project` expects the JSON file path; command functions use `_load(repo_root)` to resolve `docs/tasklist.json` ([tools/tasktool/commands.py:22](</home/simon/Dev/sigreer/skills/superstar/tools/tasktool/commands.py:22>), [116](</home/simon/Dev/sigreer/skills/superstar/tools/tasktool/commands.py:116>), [1400](</home/simon/Dev/sigreer/skills/superstar/tools/tasktool/commands.py:1400>), [1590](</home/simon/Dev/sigreer/skills/superstar/tools/tasktool/commands.py:1590>)). If followed literally, the new CLI will try to read the repo directory as a file. Change the plan to use `_load(repo_root)` and include a CLI test that fails if `infer-step` reads the wrong path.

F4. Severity: important — Skill markdown coverage is inconsistent with the spec and acceptance criteria. The spec requires updates to both `skills/subagent-driven-development/SKILL.md` and `skills/executing-plans/SKILL.md` ([docs/specs/2026-05-23-P6-programmatic-workflow-enhancements-design.md:173](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-23-P6-programmatic-workflow-enhancements-design.md:173>), [199](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-23-P6-programmatic-workflow-enhancements-design.md:199>)). The plan overview says “five skill markdown files” and omits `executing-plans` from the file table and Task 11 files/commit ([docs/plans/2026-05-23-P6.S1-workflow-step-field.md:7](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-23-P6.S1-workflow-step-field.md:7>), [70](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-23-P6.S1-workflow-step-field.md:70>), [1548](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-23-P6.S1-workflow-step-field.md:1548>), [1633](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-23-P6.S1-workflow-step-field.md:1633>)). Add the missing file and update the count; otherwise acceptance criterion 9 is not met.

2. Open questions / assumptions

- Is “schema migration” meant to become a new tasktool capability in S1, or is S1 only supposed to keep v1 rows readable and emit v2 on next save?
- Should `infer-step --all --diff` treat stored `None` as non-drift exactly as the spec says? The plan’s snippet currently computes `stored != inferred["step"]`, which flags every unset row as drift ([docs/plans/2026-05-23-P6.S1-workflow-step-field.md:1160](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-23-P6.S1-workflow-step-field.md:1160>)).

3. Suggested document edits

- Replace Task 3’s `migrate_file` work with repo-grounded schema-version handling, or explicitly add a new schema migration module/API with tests.
- Rewrite schema tests to use `build_schema()` and inline schema paths.
- Change `cmd_infer_step` pseudocode to call `_load(repo_root)` and make `None` stored values non-drift.
- Add `skills/executing-plans/SKILL.md` to the overview, Task 11, commit command, and final version-bump wording.

4. Verification gaps / commands that should be run

- `cd tools/tasktool && python -m pytest tests/test_schema_gen.py tests/test_serialize.py tests/test_commands.py -v`
- `cd tools/tasktool && python -m pytest tests/test_cli_integration.py -k infer_step -v`
- `python -m pytest skills/external-review/tests/ -v`
- `tools/tasktool/tasktool infer-step --all --diff; test $? -eq 0 -o $? -eq 1`

Overall verdict: revise

