I have enough to complete the review. I verified the skill and test files on disk, the git history, the working-tree state, and the generated-mirror boundary directly. I manually cross-checked every assertion in the six `tasktool-janitor` tests against `skills/tasktool-janitor/SKILL.md` (all match). `git diff --check` is clean; the only untracked artifact is this review's own reviewer chain. I was unable to execute `pytest` and `tasktool validate` (sandbox blocked them), so those are noted as verification gaps below.

---

Findings

F1 — Skill contradicts the approved spec on unrelated tracker dirt. Severity: important
The spec, `docs/specs/2026-06-21-X31-tasktool-janitor-skill-design.md:65`, states: "`tasktool close` auto-commits scoped tracker/archive changes by default, so pre-existing tracker dirt can be folded into that lifecycle commit." The shipped skill, `skills/tasktool-janitor/SKILL.md:23`, states the opposite: "unrelated tracker dirt must be cleared before close or cancel." The plan's prescribed test wording (plan Task 1, line 182) was `"close` auto-commits"` with no clearing requirement; the committed test `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py:358` instead pins `"unrelated tracker dirt must be cleared before close or cancel"`. So both the skill prose and its guardrail test diverged from the spec/plan in the same direction. The implemented stance is the safer one and is internally coherent (it pairs with the line 94 pre-mutation dirt check), so this is not a behavioral defect — but it is an unreconciled drift from an approved spec. Either update the spec line to match the shipped "clear first" stance, or add a one-line note in the implementation summary acknowledging the deliberate tightening.

F2 — Mild internal tension between "auto-commits scoped changes" framing and "clear dirt first" rule. Severity: minor
`SKILL.md:23` (Required Setup) now says unrelated dirt "must be cleared," while `SKILL.md:95` (Mutation Rules) still says "`close` auto-commits scoped tracker/archive changes by default and supports `--no-commit`..." without restating the clear-first requirement. The two are reconcilable (scoped lifecycle changes are auto-committed; unrelated dirt is the operator's responsibility to clear), but a reader scanning only the Mutation Rules bullet could miss the clear-first obligation. Consider echoing "after clearing unrelated dirt" in the line 95 bullet for consistency.

F3 — Optional Task 3 was skipped, but the required skip-reason record is absent/unverifiable. Severity: minor
`tests/skill-triggering/prompts/tasktool-janitor.txt` does not exist (confirmed by `ls`), and no commit `X31: add tasktool janitor trigger prompt` was made. The plan explicitly permits skipping (Task 3 Step 3, File Structure "Optional create"), but conditions it on "record the reason in the implementation summary." No implementation summary / handoff artifact is present in the worktree, so the skip is unrecorded. Add the one-line reason to the closeout summary.

F4 — `tasktool validate` and `pytest` results are unverified at the gate. Severity: minor
Acceptance items "Focused docs-lifecycle pytest passes" and "`tasktool validate` exits 0" (plan lines 503–504) require evidence. The sandbox blocked both commands during this review. I manually verified all 6 janitor tests' string assertions against the skill file, so I have high confidence pytest passes, but `tasktool validate` has not been executed and should be run before closeout per Task 4 Step 3.

F5 — Dossier template uses ASCII hyphen rather than the spec's em-dash. Severity: nit
`SKILL.md:52` renders the heading as `## <id> - <title>`; the spec (line 105) uses `## <id> — <title>`. No test pins this and it is cosmetic. Leave as-is or align to the spec; not worth a round-trip on its own.

Confirmed-good (no action):
- Both `skills/tasktool-janitor/SKILL.md` and the test additions are committed together in `97a5806` (191 insertions, 2 files); no failing-test state was left committed (plan Task 1 Step 2 satisfied).
- No `plugins/superstar/skills/**` mirror files were touched (`git diff --name-only HEAD~1 -- plugins/superstar/skills` empty) — generated-mirror boundary respected (Task 4 Step 1).
- `git diff --check` is clean; working tree carries only the untracked reviewer chain, which is expected for this review.
- All spec Acceptance Criteria (spec lines 182–191) are represented in the skill: read-only intake, batching/delegation, worker mutation+file-edit bans, five-action dossier schema, coordinator re-check, approval-before-mutation, small-batch + validate + re-check, durable audit artifact.
- X31 remains open/unmerged, which is correct at a post-slice gate; the plan's merge-before-close sequencing (Task 5 Step 4) is sound.

Open questions / assumptions
- Was the F1 "clear dirt first" tightening a deliberate decision by the implementer, or unintended drift? If deliberate, the spec should be amended so the canonical design and the shipped skill agree.
- Is a trigger fixture (Task 3) wanted at all for this skill, or is the string-level guardrail considered sufficient? The answer determines whether F3 is "record skip reason" or "add the fixture."

Suggested document edits
- Spec line 65: replace "pre-existing tracker dirt can be folded into that lifecycle commit" with the shipped stance ("unrelated tracker dirt must be cleared before close or cancel; only scoped lifecycle changes are auto-committed"), OR add a note in the closeout summary that the skill intentionally tightened this.
- `SKILL.md:95`: optionally append a clause pointing back to the clear-first rule so the Mutation Rules section is self-contained.
- Closeout summary: record the Task 3 skip reason and the `tasktool validate` result.

Verification gaps / commands to run before closeout
- `python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` (blocked here; assertions manually verified)
- `tasktool validate` (not run; required by acceptance, expect exit 0 with only pre-existing warnings)

Overall verdict: ready with small edits