# Review — 2026-05-14-external-reviewer-context-optimisation-plan.md (post-phase, round 1)

- Target: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md`
- Request: `docs/reviewer/external-reviewer-context-optimisation-plan-P1-post-phase/r1-2026-05-14T1652-primary-request.md`
- Reviewer command: `reviewer-agent`
- Status: `ok`

---

**Findings**
- F1 Severity: blocking: `apply_budget()` does not actually trim large diff bodies when the diff contains its own `##` headings. The section end finder stops at the first nested heading after `## Changes since prior round`, while `compute_diff_section()` emits `## git diff base..HEAD` and `## git diff HEAD (uncommitted)`, so only the small pre-heading text is considered the diff body. A prompt with a 150 KB diff and 100 KB budget still returns ~150 KB. See [external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:174), [external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:182), and [external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:1034). This violates the S2 budget guarantee in [spec](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md:129).

- F2 Severity: blocking: phase close is not complete in the target plan. All three phase-close checkboxes remain unchecked, including final suite run, real-chain dry-run note, and post-phase review iteration. See [plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:2790). The post-phase chain folder currently contains only an untracked request file and no `chain.json` or response, so there is no completed post-phase gate artifact to evaluate.

- F3 Severity: important: the spec requires a live rerun of the known broken multistore chain with request-size evidence, but the plan downgrades it to “optional but recommended” and does not record results. Compare [spec](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md:174) with [plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:2795). This leaves the main empirical acceptance gate unproven.

- F4 Severity: important: `SKILL.md` still contains stale sweep aggregation guidance: it says `merged_verdict` is `revise` if any reviewer or `verdict_valid: false` says so, which contradicts the new failed-sweep truth table where failed sweeps are ignored. See [SKILL.md](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/SKILL.md:124) versus [SKILL.md](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/SKILL.md:77).

**Open questions / assumptions**
- I assume the phase is intended to close now. If the post-phase review was intentionally interrupted, this review should be treated as a pre-close review, not a closeout verdict.
- There is no `TASKLIST.md` in this repo; the handoffs state the plan checkboxes are the tracker, so I reviewed the plan as the tracker.

**Suggested document edits**
- Mark phase-close Step 1-3 complete only after evidence exists, and add a short closeout note with test count, real-chain request size, verdict/status, and whether the bypass note appeared.
- Fix the post-phase command in the plan to include `--work-id P1` or equivalent, matching the script’s requirement for `post-phase`.

**Verification gaps / commands**
- I ran: `python3 -m py_compile skills/external-review/scripts/external-reviewer.py && python3 -m pytest skills/external-review/tests/ -q` → `141 passed, 1 warning`.
- Add a regression test where `apply_budget()` receives a `## Changes since prior round` section containing nested `## git diff...` headings and must still trim/drop the full diff body.
- Run and record the multistore live-chain dry-run from the phase-close section.

**Overall verdict: revise**

---

## Reviewer stderr (tail)

```text
 it to “optional but recommended” and does not record results. Compare [spec](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md:174) with [plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md:2795). This leaves the main empirical acceptance gate unproven.

- F4 Severity: important: `SKILL.md` still contains stale sweep aggregation guidance: it says `merged_verdict` is `revise` if any reviewer or `verdict_valid: false` says so, which contradicts the new failed-sweep truth table where failed sweeps are ignored. See [SKILL.md](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/SKILL.md:124) versus [SKILL.md](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/SKILL.md:77).

**Open questions / assumptions**
- I assume the phase is intended to close now. If the post-phase review was intentionally interrupted, this review should be treated as a pre-close review, not a closeout verdict.
- There is no `TASKLIST.md` in this repo; the handoffs state the plan checkboxes are the tracker, so I reviewed the plan as the tracker.

**Suggested document edits**
- Mark phase-close Step 1-3 complete only after evidence exists, and add a short closeout note with test count, real-chain request size, verdict/status, and whether the bypass note appeared.
- Fix the post-phase command in the plan to include `--work-id P1` or equivalent, matching the script’s requirement for `post-phase`.

**Verification gaps / commands**
- I ran: `python3 -m py_compile skills/external-review/scripts/external-reviewer.py && python3 -m pytest skills/external-review/tests/ -q` → `141 passed, 1 warning`.
- Add a regression test where `apply_budget()` receives a `## Changes since prior round` section containing nested `## git diff...` headings and must still trim/drop the full diff body.
- Run and record the multistore live-chain dry-run from the phase-close section.

**Overall verdict: revise**
tokens used
128,452
```
