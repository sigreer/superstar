# Merged findings for r1

## Primary

# Review — 2026-06-21-X31-tasktool-janitor-skill.md (post-slice, round 1)

- Target: `docs/plans/2026-06-21-X31-tasktool-janitor-skill.md`
- Request: `docs/reviewer/x31-tasktool-janitor-skill-X31-post-slice/r1-2026-06-21T0234-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

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


## Sweep 1

# Review — 2026-06-21-X31-tasktool-janitor-skill.md (post-slice, round 1)

- Target: `docs/plans/2026-06-21-X31-tasktool-janitor-skill.md`
- Request: `docs/reviewer/x31-tasktool-janitor-skill-X31-post-slice/r1-2026-06-21T0234-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

I have enough to complete the review. I verified the skill and test files on disk, the git history, the working-tree state, and the generated-mirror boundary directly. I manually cross-checked every assertion in the six `tasktool-janitor` tests against `skills/tasktool-janitor/SKILL.md` (all match). `git diff --check` is clean; the only untracked artifact is this review's own reviewer chain. I was unable to execute `pytest` and `tasktool validate` (sandbox blocked them), so those are noted as verification gaps below.

---

Findings

S1.F1 — Skill contradicts the approved spec on unrelated tracker dirt. Severity: important
The spec, `docs/specs/2026-06-21-X31-tasktool-janitor-skill-design.md:65`, states: "`tasktool close` auto-commits scoped tracker/archive changes by default, so pre-existing tracker dirt can be folded into that lifecycle commit." The shipped skill, `skills/tasktool-janitor/SKILL.md:23`, states the opposite: "unrelated tracker dirt must be cleared before close or cancel." The plan's prescribed test wording (plan Task 1, line 182) was `"close` auto-commits"` with no clearing requirement; the committed test `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py:358` instead pins `"unrelated tracker dirt must be cleared before close or cancel"`. So both the skill prose and its guardrail test diverged from the spec/plan in the same direction. The implemented stance is the safer one and is internally coherent (it pairs with the line 94 pre-mutation dirt check), so this is not a behavioral defect — but it is an unreconciled drift from an approved spec. Either update the spec line to match the shipped "clear first" stance, or add a one-line note in the implementation summary acknowledging the deliberate tightening.

S1.F2 — Mild internal tension between "auto-commits scoped changes" framing and "clear dirt first" rule. Severity: minor
`SKILL.md:23` (Required Setup) now says unrelated dirt "must be cleared," while `SKILL.md:95` (Mutation Rules) still says "`close` auto-commits scoped tracker/archive changes by default and supports `--no-commit`..." without restating the clear-first requirement. The two are reconcilable (scoped lifecycle changes are auto-committed; unrelated dirt is the operator's responsibility to clear), but a reader scanning only the Mutation Rules bullet could miss the clear-first obligation. Consider echoing "after clearing unrelated dirt" in the line 95 bullet for consistency.

S1.F3 — Optional Task 3 was skipped, but the required skip-reason record is absent/unverifiable. Severity: minor
`tests/skill-triggering/prompts/tasktool-janitor.txt` does not exist (confirmed by `ls`), and no commit `X31: add tasktool janitor trigger prompt` was made. The plan explicitly permits skipping (Task 3 Step 3, File Structure "Optional create"), but conditions it on "record the reason in the implementation summary." No implementation summary / handoff artifact is present in the worktree, so the skip is unrecorded. Add the one-line reason to the closeout summary.

S1.F4 — `tasktool validate` and `pytest` results are unverified at the gate. Severity: minor
Acceptance items "Focused docs-lifecycle pytest passes" and "`tasktool validate` exits 0" (plan lines 503–504) require evidence. The sandbox blocked both commands during this review. I manually verified all 6 janitor tests' string assertions against the skill file, so I have high confidence pytest passes, but `tasktool validate` has not been executed and should be run before closeout per Task 4 Step 3.

S1.F5 — Dossier template uses ASCII hyphen rather than the spec's em-dash. Severity: nit
`SKILL.md:52` renders the heading as `## <id> - <title>`; the spec (line 105) uses `## <id> — <title>`. No test pins this and it is cosmetic. Leave as-is or align to the spec; not worth a round-trip on its own.

Confirmed-good (no action):
- Both `skills/tasktool-janitor/SKILL.md` and the test additions are committed together in `97a5806` (191 insertions, 2 files); no failing-test state was left committed (plan Task 1 Step 2 satisfied).
- No `plugins/superstar/skills/**` mirror files were touched (`git diff --name-only HEAD~1 -- plugins/superstar/skills` empty) — generated-mirror boundary respected (Task 4 Step 1).
- `git diff --check` is clean; working tree carries only the untracked reviewer chain, which is expected for this review.
- All spec Acceptance Criteria (spec lines 182–191) are represented in the skill: read-only intake, batching/delegation, worker mutation+file-edit bans, five-action dossier schema, coordinator re-check, approval-before-mutation, small-batch + validate + re-check, durable audit artifact.
- X31 remains open/unmerged, which is correct at a post-slice gate; the plan's merge-before-close sequencing (Task 5 Step 4) is sound.

Open questions / assumptions
- Was the S1.F1 "clear dirt first" tightening a deliberate decision by the implementer, or unintended drift? If deliberate, the spec should be amended so the canonical design and the shipped skill agree.
- Is a trigger fixture (Task 3) wanted at all for this skill, or is the string-level guardrail considered sufficient? The answer determines whether S1.F3 is "record skip reason" or "add the fixture."

Suggested document edits
- Spec line 65: replace "pre-existing tracker dirt can be folded into that lifecycle commit" with the shipped stance ("unrelated tracker dirt must be cleared before close or cancel; only scoped lifecycle changes are auto-committed"), OR add a note in the closeout summary that the skill intentionally tightened this.
- `SKILL.md:95`: optionally append a clause pointing back to the clear-first rule so the Mutation Rules section is self-contained.
- Closeout summary: record the Task 3 skip reason and the `tasktool validate` result.

Verification gaps / commands to run before closeout
- `python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` (blocked here; assertions manually verified)
- `tasktool validate` (not run; required by acceptance, expect exit 0 with only pre-existing warnings)

Overall verdict: ready with small edits

