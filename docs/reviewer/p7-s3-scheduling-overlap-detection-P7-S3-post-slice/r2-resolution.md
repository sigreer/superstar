# Resolution for r2

## F1
Status: fixed
Evidence:
- Confirmed resolved by the round-2 reviewer: the 5.3 smoke block in `docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md:914-937` now passes `--project-root "$SCRATCH"` on every tasktool call; reviewer ran it -> smoke exit=0.

Notes:
Fixed in the round-1 resolution commit. No further action.

## S1.F2
Status: fixed
Evidence:
- Duplicate of F1; same smoke-block fix. Confirmed resolved by the round-2 reviewer.

Notes:
Duplicate of F1.

## S1.F1
Status: waived
Evidence:
- Accepted by the round-2 reviewer. Authoritative checkout `./tools/tasktool/tasktool brief P7.S3` (from /home/simon/Dev/sigreer/skills/superstar) reports status: in_progress, workflow_step: implement, review_active: true, review_stage: applying_fixes, started: 2026-06-04. The worktree's committed docs/tasklist.json is an expected stale snapshot under authoritative-checkout routing; planning_status: proposed during implementation is by design (ratify-at-close).

Notes:
False positive from the read-only worktree snapshot; no lifecycle defect.

## F2
Status: waived
Evidence:
- The repo enforces NO whitespace gate. Re-verified in this worktree: `git config --get core.whitespace` is unset; there is no `.pre-commit-config.yaml` (none tracked, none at repo root); the installed `.git/hooks/pre-commit` (tasktool-pre-commit-hook v1, in the shared git common-dir) enforces only tasklist/tasktool rules (TASKLIST.md blocking, tasklist.json canonical/validation, spec/plan orphan checks) and contains no whitespace check. `git diff --check` is the reviewer's own heuristic, not a project closeout gate (it is not listed in the plan's Task 5).
- The flagged lines are verbatim machine-generated reviewer audit output (`.reviewer-output/r1-primary/last-message.md:3,27`, `.reviewer-output/r1-sweep1/last-message.md:3,6,24-27`, `r1-merged-findings.md`). The trailing double-spaces are semantic Markdown hard-breaks (e.g. `F1 Severity: important` followed by two spaces). Editing them would corrupt the committed audit trail and alter rendering.
- Committing the `.reviewer-output/` audit subdir is the established repo convention: `git ls-files 'docs/reviewer/*post-slice*' | grep -c reviewer-output` -> 119 files already tracked on main (e.g. the P7.S4 chain). This slice follows convention; it does not introduce a new standard.
- The repo-source diff (tools/tasktool + the plan) is whitespace-clean on its own: `git diff --check main..HEAD -- ':(exclude)docs/reviewer/**'` exits 0. Only the generated reviewer artifacts trip `git diff --check`.

Notes:
Documented exception for generated reviewer artifacts — the reviewer listed this as an acceptable resolution ("explicitly document and gate an allowed exception for generated reviewer artifacts"). A permanent structural fix (a `.gitattributes` entry `docs/reviewer/** -whitespace`, or normalizing the reviewer tool's output) is the right permanent home but is a cross-cutting repo-policy change unrelated to this scheduling-overlap slice; it is recommended as a SEPARATE follow-up (P7 still has open slices S5/S6/S7, or a standalone hygiene change) and kept out of this slice to preserve post-slice scope isolation.
