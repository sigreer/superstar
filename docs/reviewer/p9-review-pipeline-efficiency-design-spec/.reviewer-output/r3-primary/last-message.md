1. Findings

F1 (Severity: important): RESOLVED. Model-tiering remains explicit and acceptance-covered at `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:99-123` and `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:241-245`.

F2 (Severity: important): RESOLVED. `--combined-gate <spec-path>` remains constrained to `plan`, verifies the spec path, injects guidance, includes context, and stamps manifest state at `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:217-227` and `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:250-252`.

F3 (Severity: important): RESOLVED. The spec now requires slice-level spec/plan review invocations to pass `--work-id <slice-id>` whenever a tasktool row exists, and blocks claiming the ≤ 4.5 metric when in-window spec/plan chains are uncorrelated. See `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:140-148`; acceptance criterion 6 adds the shared-`work_id` and missing-`work_id` fixtures at `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:253-260`, and criterion 7 covers the skill-text update at `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:261-264`. This is grounded in the existing CLI: `--work-id` is already accepted generally, not just for post gates (`skills/external-review/scripts/external-reviewer.py:1835-1839`), while the current required-only restriction is limited to post gates (`skills/external-review/scripts/external-reviewer.py:2438-2445`).

F4 (Severity: minor): RESOLVED. The preflight path rules still separate markdown-link failures from backtick warnings and exempt code blocks, placeholder/glob paths, and future reviewer artifacts at `docs/specs/2026-06-06-P9-review-pipeline-efficiency-design.md:163-171`.

2. Open questions / assumptions

None blocking. I assume the implementation plan will split S1/S2/S3 in the order described and keep the metric fixture work in S1, since the correctness of the trial depends on that landing before measurement starts.

3. Suggested document edits

No required edits.

4. Verification gaps / commands that should be run

- `python -m pytest skills/external-review/tests -q`
- Targeted new tests for `stats --since` correlated and uncorrelated `work_id` fixtures, including the `per_slice_complete: false` case.

Overall verdict: ready