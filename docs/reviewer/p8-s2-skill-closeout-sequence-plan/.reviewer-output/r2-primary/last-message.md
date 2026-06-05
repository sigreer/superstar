I've read all five relevant files from disk — the plan, the spec, and the three target skill files (`subagent-driven-development`, `finishing-a-development-branch`, `tasklist-discipline`) — and cross-checked every test literal in Tasks 1/3/4 against both the prose blocks the plan inserts and the verbatim replacement-target anchors in the current skill files. This is an incremental round-2 review verifying resolution of F1–F7.

Here is my review.

---

Review — 2026-06-05-P8.S2-skill-closeout-sequence.md (plan, round 2)

- Target: `docs/plans/2026-06-05-P8.S2-skill-closeout-sequence.md`
- Mode: incremental (round 2); resolution report was MISSING, so I re-verified each prior finding against disk.

Findings

F1 — Slice-end test anchor vs prose mismatch (`proceed.`). Severity: blocking → RESOLVED.
The test anchor is now `section.index("On `ready` / `ready with small edits`, proceed")` (plan line 133, period dropped), and Task 2 Step 1 prose (plan line 189) reads `…On `ready` / `ready with small edits`, proceed to merge-back.` The anchor is a clean substring of the prose. The replacement also folds the old steps 4+5 into one step 4 and reorders so `merge the worktree branch back` (step 5), `tasktool close <slice-id>` (step 6), and `tasktool worktree prune <slice-id>` (step 7) follow in order. Since Task 2 Step 1 replaces the entire current steps 3–6 (skill lines 59–62), no stale `proceed.` line survives. The order assertion `review_ready < merge_back < close < prune` holds, and the first `tasktool close <slice-id>` occurrence in the section is step 6 (step 5 says only "before close", not the literal).

F2 — Finishing-branch anchor case mismatch (`do`/`Do`). Severity: blocking → RESOLVED.
Test now asserts `"Do not run Step 6 cleanup before `tasktool close <slice-id>`"` (plan line 262, capital D); Task 3 Step 3 prose (plan line 287) inserts the same string with capital D. Match confirmed.

F3 — Tasklist anchor case mismatch (`Truthful`). Severity: blocking → RESOLVED.
Test asserts `"Truthful sibling lifecycle rows are bookkeeping"` (plan line 353); Task 4 Step 3 prose (plan line 375) writes the same capitalized phrase. Match.

F4 — Tasklist anchor case mismatch (`Sibling`). Severity: blocking → RESOLVED.
Test asserts `"Sibling artifacts remain hands-off"` (plan line 354); prose (plan line 375) writes `Sibling artifacts remain hands-off:`. Anchor is a substring. Match. I also re-verified the remaining tasklist anchors — `Shared tracker versus sibling artifacts`, `` `docs/tasklist.json` is the shared canonical tracker ``, `implementation files, specs, plans, handoffs, reviewer chains`, `A sibling's close is co-staged, so I must stop`, and `tracker is whole-file bookkeeping` — all present verbatim in the inserted paragraph (plan line 375) and red-flag row (plan line 383). The insert anchors exist on disk: `**Implementation isolation boundary:**` (skill line 28) and `**Administrative closeout exception:**` (skill line 30) bracket the insertion point, and the Red flags table exists (skill line 182).

F5 — Task 2 committed still-failing tests, breaking green-commit bisectability. Severity: important → RESOLVED.
Task 1 now adds only the two `subagent-driven-development` tests; Task 2 Step 5 stages just that test file plus the subagent skill (plan line 238). The finishing-branch test is introduced in Task 3 Step 1 and committed in Task 3 Step 7 alongside its skill; the tasklist test is introduced in Task 4 Step 1 and committed in Task 4 Step 6. Every commit is now green. This also matches the Working Conventions rule on plan line 53.

F6 — Phase-end edit dropped the spec's verify-and-skip instruction. Severity: minor → RESOLVED.
Task 2 Step 2 (plan line 200) now ends with "Verify no tasktool-owned slice worktree remains before doing any cleanup, and do not re-run per-slice prune against rows with no recorded worktree," matching spec §2 (spec line 50). This edit lands in the phase-end section, outside `_slice_end_section`, so it does not perturb the slice-end ordering assertions.

F7 — Loosely anchored `--force` replacement target. Severity: nit → RESOLVED.
Task 3 Step 5 (plan lines 308–310) now quotes the exact existing sentence to replace, and it matches `skills/finishing-a-development-branch/SKILL.md:252` verbatim. The other finishing-branch anchors are confirmed on disk: `### Step 4: Present Options` (line 88), `Then run Cleanup workspace (Step 6).` (line 156), and the `prune` enforces three guards paragraph (line 252).

Diagram check (from round-1 verification gap) — confirmed addressed. The replacement target `"post-slice verdict ready?" -> "tasktool close <slice-id>" [label="ready"];` / `"tasktool close <slice-id>" -> "Last slice in phase?";` exists verbatim at skill lines 154–155. After Task 2 Step 3 the forbidden edge is gone, the new chain (`post-slice verdict ready? → Merge back → close → prune → Last slice in phase?`) keeps the graph connected, the `digraph process`/`## Model Selection` slice anchors exist (skill lines 99/169), and the negative assertion `'"post-slice verdict ready?" -> "tasktool close <slice-id>"' not in diagram` is satisfied since the only remaining `tasktool close <slice-id>` references are the node declaration and the two new edges.

New observations (non-blocking)

F8 — Phase-end replacement uses a positional anchor ("replace step 4") rather than quoting the existing sentence. Severity: nit.
Task 2 Step 2 (plan line 197) says "replace step 4 with:" without quoting the current text (`tasktool archive-phase <phase-id>` … `then invoke `[[finishing-a-development-branch]]`.`, skill line 68). The numbered list item is unique so this is locatable, but quoting it verbatim — as F7's fix now does elsewhere — would remove the last bit of anchor ambiguity in the plan. Optional.

Open questions / assumptions
- I assume the implementer pastes the test and prose blocks verbatim. Under that assumption the focused suite goes green at Task 2 Step 4, Task 3 Step 6, and Task 4 Step 5, and the full suite at Task 5 Step 2.
- I confirmed the existing `test_subagent_driven_development_has_integrate_main_checkpoint` is not regressed: the integrate-current-main checkpoint (skill line 58) and the first slice-end `tasktool close <slice-id>` occurrence are both preserved by the replacement.
- Task 5 Step 6 invokes `external-reviewer review …` as the closeout command while the in-flow prose references the `[[external-review]]` skill / `tasktool`. This naming was present in round 1, is not a regression from any fix, and is out of scope for incremental review — noting only for awareness.

Suggested document edits
- Optional (F8): quote the current phase-end step 4 sentence in Task 2 Step 2 the same way Task 3 Step 5 now quotes its replacement target.

Verification gaps / commands that should be run
- None blocking. The plan's gate (`python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` after each of Tasks 2/3/4, then the full `tools/tasktool/tests -q` in Task 5) is correct and, with F1–F5 reconciled, will now pass at the steps where the plan claims green. The implementer should still run the focused suite at the end of each task and confirm green before committing, rather than relying on the asserted "Expected: pass" notes.

All four round-1 blocking findings (F1–F4) and the important finding (F5) are resolved and verified against the on-disk skill files; the two lower-severity findings (F6, F7) are also resolved. The single new item (F8) is an optional nit and does not gate execution.

Overall verdict: ready with small edits