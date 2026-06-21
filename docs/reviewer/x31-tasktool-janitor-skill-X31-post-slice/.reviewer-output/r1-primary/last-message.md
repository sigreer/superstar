I have everything I need. I verified the slice by reading the committed artifacts, checking repo state, and validating the skill's load-bearing factual claims against the actual `tasktool` implementation. Here is the review.

---

Findings

F1 — Severity: important. The shipped skill contradicts its own spec and plan on tracker-dirt handling, and the skill is the correct one. `skills/tasktool-janitor/SKILL.md:23` states: "`tasktool close` auto-commits only scoped lifecycle tracker/archive changes by default; unrelated tracker dirt must be cleared before close or cancel." This is verifiably correct: `cmd_close` calls `_git_commit_scoped` (`tools/tasktool/commands.py:1342-1351`), which runs `git commit -m <msg> -- docs/tasklist.json [archive]` (`commands.py:191-192`). A pathspec commit commits the *entire* working-tree content of `docs/tasklist.json`, so any unrelated edits to that file are swept into the lifecycle commit — clearing dirt first is the right guidance. But the spec (`docs/specs/2026-06-21-...-design.md:65`) and the plan (`docs/plans/2026-06-21-...-skill.md:246`) say the opposite — "pre-existing tracker dirt **can be folded into** that lifecycle commit." Those documents now give actively unsafe advice that the verified tool behavior and the shipped skill both reject. The implementation also changed the Task 1 test verbatim (plan line 182 pinned `"close\` auto-commits"`; the committed test at `test_skill_tasktool_lifecycle_docs.py:358` instead pins `"unrelated tracker dirt must be cleared before close or cancel"`), so this was a deliberate correction made during implementation but never back-propagated to the spec/plan. Recommend updating the spec §Read-Only Intake and plan File-Structure prose to match the shipped skill (or adding a one-line note that the spec wording was superseded).

F2 — Severity: minor. The skill's claim that "The cancel command stages tracker/archive changes instead" (`SKILL.md:25`, `:96`) overstates what `cmd_cancel` does. `cmd_cancel` (`commands.py:1413-1420`) calls `_save` (writes `docs/tasklist.json` to the working tree, leaving it **unstaged**) and `_git_stage` on the *archive* file only. So after a cross-row cancel, the archive is staged but the tracker edit is an unstaged modification, and nothing is committed. The operator-facing takeaway (no auto-commit, no `--no-commit` equivalent, must be handled deliberately) is correct and well-supported (cmd_cancel has no `no_commit` param; CLI dispatch at `cli.py:496/508` only passes it for close). Consider tightening "stages tracker/archive changes" to "stages the archive and leaves the tracker edit unstaged, with no auto-commit."

F3 — Severity: minor. Task 3's optional trigger fixture `tests/skill-triggering/prompts/tasktool-janitor.txt` was not created — `git diff --stat main...HEAD` shows only two files changed (`SKILL.md`, the test). The plan explicitly permits skipping (Task 3 Step 3: "If no trigger fixture is added, skip this task and record the reason in the implementation summary"), but no implementation summary artifact recording the skip was found in the worktree. Confirm the skip is intentional and note the reason at closeout.

F4 — Severity: minor (verification gap). I could not execute `python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` in this review environment (the harness declined the command). As compensation I hand-checked every assertion in all six `test_tasktool_janitor_*` tests (`test_skill_tasktool_lifecycle_docs.py:298-374`) against the committed `SKILL.md` — all 30+ substrings match, including the frontmatter, intake commands, batching thresholds, worker mutation bans, dossier fields/actions, approval/landed-gate/auto-commit lines, and audit-trail path. `git diff --check` is clean (no output, exit 0) and `git diff --name-only -- plugins/superstar/skills` is empty, so the generated mirror boundary (Task 4) holds. The implementer should still confirm the pytest run and `tasktool validate` are green before closeout.

Open questions / assumptions
- Was the F1 wording reversal (spec/plan "can be folded" → skill "must be cleared") a conscious correctness fix during implementation? I assume yes based on the matching test change; please confirm so the spec/plan can be reconciled rather than the skill reverted.
- F3: is the trigger fixture being deliberately deferred? If so, that's within the plan's allowance — just record it.

Suggested document edits
- Spec line 65 and plan line 246: replace "unrelated/pre-existing tracker dirt can be folded into the lifecycle commit" with the skill's "must be cleared before close or cancel," or add a superseded-by note.
- `SKILL.md:25`/`:96`: clarify that cancel stages only the archive and leaves the tracker edit unstaged (no auto-commit, no opt-out flag).
- At closeout, add the implementation summary recording the Task 3 skip reason (or create the fixture).

Verification gaps / commands that should be run
- `python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` (confirm green — I could not run it here).
- `tasktool validate` (Task 4 Step 3 — confirm exit 0; record any pre-existing warnings).
- These are pre-merge gates; the X31 branch is correctly still unmerged at review time (Task 5 closeout follows this review).

The slice is functionally complete and the shipping artifact is sound and verified against tool behavior; the edits above are small and mostly reconcile stale spec/plan prose with the (correct) skill.

Overall verdict: ready with small edits