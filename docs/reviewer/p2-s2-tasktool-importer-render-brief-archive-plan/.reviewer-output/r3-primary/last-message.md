1. Findings

F6. Severity: blocking  
[docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:143](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:143) captures the phase status tag, but the importer snippet never parses `DONE YYYY-MM-DD` into `Phase.closed` at [line 165](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:165). That blocks the real migration: `docs/TASKLIST.md` has `P1` as `✅ DONE 2026-05-17`, Task 12 expects that closed date at [line 1220](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:1220), and validation rejects `done` items without `closed`. Add phase-tag parsing and a test asserting historical `P1.closed == "2026-05-17"`.

F2. Severity: important  
Still unresolved for phases. The plan now correctly narrows blocked status by kind at [line 61](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:61), and cross-cutting blocked input is handled at [line 371](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:371). But the phase parser excludes `⏸` at [line 145](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:145) and only says it becomes “unparsed bullet noise” at [line 149](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:149), which contradicts the stated importer rule at [line 70](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:70). Add a blocked-phase test and either coerce to ready with the promised warning or deliberately fail import before write.

F3. Severity: important  
Still unresolved due to a stale contradictory sentence. [Line 317](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:317) still says archived/historical phase references are captured as `ArchivedPhase`, while [line 383](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:383) and Task 12 say historical `P1` remains in `phases[]`. Remove or rewrite the line 317 claim.

F1. RESOLVED  
Task 13 now sets `P2.S2.plan_path` through the raw-edit escape hatch at [line 1292](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:1292), and verification expects the brief to show the plan reference at [line 1319](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:1319).

F4. RESOLVED  
The archive command now builds content in memory, mutates the model, and calls `validate_project(p)` before archive filesystem writes at [line 1060](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:1060).

F5. RESOLVED  
The plan now emits the skip warning to stderr at [line 1025](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:1025), and the CLI test asserts it at [line 1103](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:1103).

2. Open questions / assumptions

I assume historical `P1` must stay in `phases[]`, because the current migration acceptance criteria explicitly require that.

3. Suggested document edits

Add phase `DONE` tag parsing alongside slice `DONE` parsing, with tests for `P1.closed`.

Make the blocked-phase importer behavior match line 70.

Delete the stale `ArchivedPhase` claim on line 317.

4. Verification gaps / commands

After edits, add/run:

```bash
PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_importer -v
PYTHONPATH=tools python3 -m tasktool import docs/TASKLIST.md --dry-run --project superstar >/tmp/preview.json 2>/tmp/preview-warnings.txt
PYTHONPATH=tools python3 -m tasktool validate
```

5. Overall verdict

revise