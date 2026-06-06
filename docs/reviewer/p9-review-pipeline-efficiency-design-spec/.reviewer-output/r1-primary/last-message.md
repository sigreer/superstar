1. Findings

F1 (Severity: important): The model-tiering rule has an undefined “final-ready” state for primaries, so implementers can weaken the final acceptance path accidentally. The spec says `AGENT_REVIEWER_MODEL_STRONG` is used for “all sweeps, and any round whose pre-run state is final-ready” at [docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:105). In the current implementation, final-ready sweep planning is decided only after the current primary returns a ready verdict, not as a pre-run state ([skills/external-review/scripts/external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:2682)). This leaves the primary on a decisive ready-producing follow-up eligible for the light model if the implementation interprets “pre-run” literally. Specify exactly which reviewer invocations use strong on follow-up rounds, especially round N primaries after a prior revise and all final-ready checkpoints.

F2 (Severity: important): `--combined-gate` only requires “at least one `--context` file”, but the workflow already uses context for tracker files and plans, so the flag can pass without the spec being attached. The spec states the context file is “the spec” at [docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:179), but it does not define how the CLI verifies that. Existing skill guidance currently passes `docs/tasklist.json` as context for spec/plan/post-slice reviews ([skills/external-review/SKILL.md](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/SKILL.md:278)), and S1 changes that habit toward `tasktool brief`, so a combined-gate review could satisfy the flag with tracker context only. Add an explicit spec-context contract, such as `--spec-context <path>`, a filename/artifact heuristic, or a refusal unless one context path matches the originating `docs/specs/...` artifact.

F3 (Severity: important): The measurement goal “rounds per slice ≤ 4.5” is not fully supported by the proposed `stats --since` output. Current stats count chains, rounds, first/follow-up rounds, verdicts, and provider invocations ([skills/external-review/scripts/external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:2167)), but they do not compute the number of completed slices in the window or correlate review chains to slices beyond optional `work_id` fields. The spec adds a round timestamp filter at [docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:114), then acceptance asks only that filtered rounds are returned at line 208. Define whether the denominator comes from distinct `work_id`s with post-slice chains, tasktool rows closed since the ship date, or a manual trial list; otherwise the headline success metric can be claimed inconsistently.

F4 (Severity: minor): The preflight path check is likely to false-fail valid specs/plans that contain illustrative repo paths, placeholders, or command examples. The spec makes dangling backtick-quoted repo-like strings hard failures at [docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:132), but many Superstar documents include placeholders such as `docs/reviewer/<chain>/`, glob-like paths, or command arguments that are not meant to exist yet. The risk section mentions false positives but only says the heuristic will be tuned ([docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:235)). Add explicit exemptions or severity rules for placeholders, globs, generated future artifacts, and command snippets.

2. Open questions / assumptions

- Should all round N+1 primaries after a prior revise use `AGENT_REVIEWER_MODEL_STRONG`, or only post-slice/post-phase and sweeps?
- Is combined-gate intended only for slice specs, or can phase-level specs/plans use it too?
- Should `stats --since` parse date-only values in local time or UTC? Existing `started_at` values are UTC ISO strings from `utc_now_iso()`.

3. Suggested document edits

- Replace “any round whose pre-run state is final-ready” with a concrete invocation matrix covering first-round primary, follow-up primary, post-slice/post-phase primary, first-round sweep, and final-ready sweep.
- Change `--combined-gate` from “requires at least one `--context` file” to a verifiable spec attachment rule.
- Extend acceptance criterion 6 to include the denominator and output fields needed for rounds-per-slice comparison.
- Add preflight path-check exemptions for `<placeholder>` segments, glob characters, fenced command blocks, and explicitly future/generated artifact paths.

4. Verification gaps / commands that should be run

- `python -m pytest skills/external-review/tests -q`
- Add targeted tests for model selection per role/kind/round, combined-gate refusal when only tracker context is supplied, `stats --since` legacy exclusion and denominator behavior, and preflight path-check exemptions.

Overall verdict: revise