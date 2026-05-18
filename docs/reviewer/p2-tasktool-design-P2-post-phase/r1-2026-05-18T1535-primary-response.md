# Review — 2026-05-17-P2-tasktool-design.md (post-phase, round 1)

- Target: `docs/specs/2026-05-17-P2-tasktool-design.md`
- Request: `docs/reviewer/p2-tasktool-design-P2-post-phase/r1-2026-05-18T1535-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

**1. Findings**

F1 — Severity: blocking  
The target spec is stale against the implemented/migrated phase state. It still says `Status: spec, awaiting external review` and links the TASKLIST entry to deleted `docs/TASKLIST.md` ([docs/specs/2026-05-17-P2-tasktool-design.md:3](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:3>), [line 6](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:6>)). More importantly, §12 still leaves the AGS import/read API questions open even though acceptance requires open questions to be resolved or explicitly deferred ([lines 361-363](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:361>), [lines 367-370](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:367>)). This blocks clean phase closeout as a document gate.

F2 — Severity: important  
The spec’s `tasktool set` surface no longer matches the implementation. The spec advertises `tasktool set <id> --status (ready|in_progress|blocked|done)` and says `blocked` is rejected only on non-slice IDs ([docs/specs/2026-05-17-P2-tasktool-design.md:212](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:212>), [line 216](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:216>)). Actual CLI help exposes only `{ready,in_progress,done}`, with blocking routed through `tasktool block`; S1 post-implementation notes explicitly record that `blocked` was removed from `set --status` ([docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:3136](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:3136>)). This is user-facing drift.

F3 — Severity: minor  
The S1 and S2 plans still show all task checkboxes unchecked despite the tracker marking both slices done. S1 has 75 unchecked steps and S2 has 70; both plans say checkbox syntax is for tracking ([S1 line 3](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:3>), [S2 line 3](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:3>)). This does not contradict implementation evidence, but it makes archive review noisier and undermines the plans as closeout records.

**2. Open Questions / Assumptions**

I assume P2 is intentionally still active until this post-phase review returns a verdict; `docs/tasklist.json` has P2 `in_progress`, all three slices `done`, and no phase archive entry yet.

S2’s skipped review gate is documented in `docs/tasklist.json`, and the reviewer response text contains a `ready` verdict, but `chain.json` did not parse it into `merged_verdict`. That is acceptable only because the skip note explains the parser artifact.

**3. Suggested Document Edits**

Update the spec header and TASKLIST link to reference `docs/tasklist.json` or `tasktool show P2`.

Resolve or explicitly defer the AGS questions in §12 with the implemented choice: package import via shim/PYTHONPATH and exported `load_project`, `brief`, etc., or shelling out if that is the intended AGS path.

Change §7.3 so `set --status` lists only `ready|in_progress|done`; keep `tasktool block` / `unblock` as the only blocking mutation path.

Either mark S1/S2 checklist items complete or add a short note that the plans are historical implementation recipes and closeout evidence is in their post-implementation sections / reviewer chains.

**4. Verification Gaps / Commands**

Ran:

```bash
PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v
PYTHONPATH=tools python3 tools/tasktool/__main__.py validate --strict-format --format json
PYTHONPATH=tools python3 tools/tasktool/__main__.py render
```

Results: 160 tests passed; live `docs/tasklist.json` validates cleanly with no warnings/errors.

**5. Overall Verdict**

revise
**1. Findings**

F1 — Severity: blocking  
The target spec is stale against the implemented/migrated phase state. It still says `Status: spec, awaiting external review` and links the TASKLIST entry to deleted `docs/TASKLIST.md` ([docs/specs/2026-05-17-P2-tasktool-design.md:3](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:3>), [line 6](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:6>)). More importantly, §12 still leaves the AGS import/read API questions open even though acceptance requires open questions to be resolved or explicitly deferred ([lines 361-363](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:361>), [lines 367-370](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:367>)). This blocks clean phase closeout as a document gate.

F2 — Severity: important  
The spec’s `tasktool set` surface no longer matches the implementation. The spec advertises `tasktool set <id> --status (ready|in_progress|blocked|done)` and says `blocked` is rejected only on non-slice IDs ([docs/specs/2026-05-17-P2-tasktool-design.md:212](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:212>), [line 216](</home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:216>)). Actual CLI help exposes only `{ready,in_progress,done}`, with blocking routed through `tasktool block`; S1 post-implementation notes explicitly record that `blocked` was removed from `set --status` ([docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:3136](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:3136>)). This is user-facing drift.

F3 — Severity: minor  
The S1 and S2 plans still show all task checkboxes unchecked despite the tracker marking both slices done. S1 has 75 unchecked steps and S2 has 70; both plans say checkbox syntax is for tracking ([S1 line 3](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:3>), [S2 line 3](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:3>)). This does not contradict implementation evidence, but it makes archive review noisier and undermines the plans as closeout records.

**2. Open Questions / Assumptions**

I assume P2 is intentionally still active until this post-phase review returns a verdict; `docs/tasklist.json` has P2 `in_progress`, all three slices `done`, and no phase archive entry yet.

S2’s skipped review gate is documented in `docs/tasklist.json`, and the reviewer response text contains a `ready` verdict, but `chain.json` did not parse it into `merged_verdict`. That is acceptable only because the skip note explains the parser artifact.

**3. Suggested Document Edits**

Update the spec header and TASKLIST link to reference `docs/tasklist.json` or `tasktool show P2`.

Resolve or explicitly defer the AGS questions in §12 with the implemented choice: package import via shim/PYTHONPATH and exported `load_project`, `brief`, etc., or shelling out if that is the intended AGS path.

Change §7.3 so `set --status` lists only `ready|in_progress|done`; keep `tasktool block` / `unblock` as the only blocking mutation path.

Either mark S1/S2 checklist items complete or add a short note that the plans are historical implementation recipes and closeout evidence is in their post-implementation sections / reviewer chains.

**4. Verification Gaps / Commands**

Ran:

```bash
PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v
PYTHONPATH=tools python3 tools/tasktool/__main__.py validate --strict-format --format json
PYTHONPATH=tools python3 tools/tasktool/__main__.py render
```

Results: 160 tests passed; live `docs/tasklist.json` validates cleanly with no warnings/errors.

**5. Overall Verdict**

revise

---

## Reviewer stderr (tail)

```text
as 75 unchecked steps and S2 has 70; both plans say checkbox syntax is for tracking ([S1 line 3](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:3>), [S2 line 3](</home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md:3>)). This does not contradict implementation evidence, but it makes archive review noisier and undermines the plans as closeout records.

**2. Open Questions / Assumptions**

I assume P2 is intentionally still active until this post-phase review returns a verdict; `docs/tasklist.json` has P2 `in_progress`, all three slices `done`, and no phase archive entry yet.

S2’s skipped review gate is documented in `docs/tasklist.json`, and the reviewer response text contains a `ready` verdict, but `chain.json` did not parse it into `merged_verdict`. That is acceptable only because the skip note explains the parser artifact.

**3. Suggested Document Edits**

Update the spec header and TASKLIST link to reference `docs/tasklist.json` or `tasktool show P2`.

Resolve or explicitly defer the AGS questions in §12 with the implemented choice: package import via shim/PYTHONPATH and exported `load_project`, `brief`, etc., or shelling out if that is the intended AGS path.

Change §7.3 so `set --status` lists only `ready|in_progress|done`; keep `tasktool block` / `unblock` as the only blocking mutation path.

Either mark S1/S2 checklist items complete or add a short note that the plans are historical implementation recipes and closeout evidence is in their post-implementation sections / reviewer chains.

**4. Verification Gaps / Commands**

Ran:

```bash
PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v
PYTHONPATH=tools python3 tools/tasktool/__main__.py validate --strict-format --format json
PYTHONPATH=tools python3 tools/tasktool/__main__.py render
```

Results: 160 tests passed; live `docs/tasklist.json` validates cleanly with no warnings/errors.

**5. Overall Verdict**

revise
tokens used
119,850
```
