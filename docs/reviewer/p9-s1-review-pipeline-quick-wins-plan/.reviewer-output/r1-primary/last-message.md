1. Findings

F1 Severity: important — Per-slice stats will undercount sweeps.
The spec requires the per-slice numerator to include “all rounds (including sweeps)” across spec/plan/post-slice chains (`docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:132-138`). But the plan’s proposed implementation sums `len(rounds)` only (`docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md:785-789`), while current chain data stores sweep reviewers inside a single round’s `reviewers` array (`skills/external-review/scripts/external-reviewer.py:2804-2828`). The proposed tests also only cover one-reviewer rounds (`docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md:669-678`), so this bug would pass.

F2 Severity: important — Context trimming misses an active review-invoking skill.
The spec names `subagent-driven-development` as one of the skill texts that invoke reviews (`docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:63-67`) and says callers should prefer `tasktool brief` over full `docs/tasklist.json` (`docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:79-83`). The plan only updates external-review, brainstorming, and writing-plans for context trimming, while Task 6 Step 7 limits subagent-driven-development to review-depth verification (`docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md:858-864`, `docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md:940-943`). Current `skills/subagent-driven-development/SKILL.md:59` and `:66` still instruct passing full `docs/tasklist.json`.

F3 Severity: important — Model recording has no executable acceptance gate.
The spec requires the chosen model to be recorded in the existing `model` field (`docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:122-123`). The plan describes falling back from missing sidecar model to `model_requested` (`docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md:469-475`), but the Task 3 tests only cover the helper, argparse default, and context env (`docs/plans/2026-06-06-P9.S1-review-pipeline-quick-wins.md:348-406`). An implementation could export `AGENT_REVIEWER_MODEL` correctly but still leave chain/JSON `model` as null when the reviewer wrapper emits no usage sidecar, and the planned tests would not catch it.

2. Open questions / assumptions

- Is “rounds including sweeps” intended to count reviewer invocations, not manifest round entries? Current storage shape strongly implies yes.
- Should subagent-driven-development also switch post-slice/post-phase tracker context to `tasktool brief <work-id>`, or should it explicitly document when full tasklist context is still acceptable?

3. Suggested document edits

- In Task 5, change per-slice `rounds_total` to count reviewer invocations: if `round_entry["reviewers"]` exists, count its length; otherwise count 1 for legacy/single-reviewer rounds.
- Add a stats test with one chain round containing primary + sweep reviewers and assert `rounds_total` includes both.
- In Task 6, add explicit edits for `skills/subagent-driven-development/SKILL.md:59` and `:66` to prefer `tasktool brief <work-id>` over full `docs/tasklist.json`.
- In Task 3, add an end-to-end test where `AGENT_REVIEWER_MODEL_LIGHT` is set, a spec review runs with a stub reviewer that emits no usage sidecar, and emitted JSON plus `chain.json` record `"model": "small-model"`.

4. Verification gaps / commands that should be run

- Add targeted tests for sweep-inclusive per-slice stats and sidecar-missing model recording before relying on the full suite.
- Keep the existing final gates: `python -m pytest skills/external-review/tests -q`, help grep checks for `--model`/`--since`/review-depth, and real-chain `external-reviewer stats --since ... --json`.

Overall verdict: revise