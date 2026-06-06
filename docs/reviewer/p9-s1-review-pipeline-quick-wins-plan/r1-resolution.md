# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md` (Task 5)
- Verification: per-slice `rounds_total` now counts reviewer invocations —
  `len(round_entry.get("reviewers") or [None])` per round entry, so thorough
  rounds count primary + sweeps while legacy single-reviewer rounds count 1.
  Added `test_per_slice_counts_sweep_invocations` with a primary+sweep
  `reviewers` array asserting `rounds_total == 3` for spec(1) + post(2).

## F2
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md` (Task 6
  Step 7)
- Verification: Task 6 Step 7 now contains exact before/after edits for
  `skills/subagent-driven-development/SKILL.md` end-of-slice item 3 (~:59) and
  end-of-phase item 2 (~:66), switching tracker context to `tasktool brief`
  (and `phase-status` for post-phase) with an explicit allowance for the full
  tasklist when small or when cross-phase tracker drift is in scope —
  answering the reviewer's open question about when full context stays
  acceptable.

## F3
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md` (Task 3
  Step 1)
- Verification: added `test_model_recorded_end_to_end_without_sidecar` — runs
  a full spec round through a stub reviewer (no usage sidecar) with
  `AGENT_REVIEWER_MODEL_LIGHT=small-model` and asserts the model lands in the
  emitted JSON top-level `model`, `reviewers[0].model`, and the chain.json
  round entry. This is the executable gate for the sidecar-missing fallback in
  Task 3 Step 3(d).

Notes:
Open question 1 (count invocations vs round entries): yes — invocations;
implemented and tested as above.
