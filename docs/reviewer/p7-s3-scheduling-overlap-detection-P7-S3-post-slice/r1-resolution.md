# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md:914-936` (section "5.3 Manual CLI smoke")
- Commit: this resolution and the plan fix are committed together on branch worktree-p7-s3-scheduling-overlap-detection-ready (HEAD; message: "P7.S3: post-slice r1 fixes — robust smoke block; waive stale-tracker false positive")
- Verification: rewrote the 5.3 smoke block so every tasktool invocation passes the real global `--project-root "$SCRATCH"` flag (confirmed real via `./tools/tasktool/tasktool --help` -> `[--project-root PROJECT_ROOT]` and `cli.py:36` / `_resolve_project_root` at `cli.py:19-21`). This pins each call to the throwaway dir instead of walking up to the repo's authoritative tracker. Removed the now-redundant `cd "$SCRATCH"`. Ran the rewritten block end-to-end in a real `mktemp -d` with `SUPERSTAR_SUBAGENT_ROLE` unset -> `smoke exit=0`. Key output:
  ```
  Unguarded surface overlaps (add a depends_on or coordination_group):
    - P1.S1, P1.S2: cms-block-registry
  ...
  P1.S1  [ready/proposed]  group=-  ...  a
      surface_overlap: P1.S2 (cms-block-registry)
  P1.S2  [ready/proposed]  group=-  ...  b
      surface_overlap: P1.S1 (cms-block-registry)
  ...
  tasktool: ratify warning: P1.S2 shares an integration surface with sibling(s) already in parallel_group 'core', ...
    - P1.S1: cms-block-registry
  smoke exit=0
  ```
  Separately confirmed the `ratify warning` is emitted on **stderr** (stdout empty for that call) by splitting the streams.

Notes:
The original block set `TT="$PWD/tools/tasktool/tasktool"` (an absolute path into the repo) and only `cd "$SCRATCH"`. Because the wrapper still resolves the project root by walking up from cwd into the repo tree, it routed to the already-configured authoritative repo tracker and exited 1 with an authoritative-routing error — contradicting the documented `smoke exit=0`. Passing `--project-root "$SCRATCH"` explicitly is the documented, supported way to target the throwaway dir; the CLI integration tests use the equivalent `cwd`-based isolation. Plan-only edit; no tasktool source touched.

## S1.F2
Status: fixed
Evidence:
- Same fix as F1 (the two findings describe the same smoke-block defect). See F1 evidence.

Notes:
Duplicate of F1.

## S1.F1
Status: waived
Evidence:
- Authoritative tracker (main checkout) `env -u SUPERSTAR_SUBAGENT_ROLE ./tools/tasktool/tasktool brief P7.S3` (run from `/home/simon/Dev/sigreer/skills/superstar`) returns:
  ```
  # P7.S3 — Scheduling overlap detection: ... [step: implement]
  status: in_progress
  workflow_step: implement
  review_active: true
  review_stage: applying_fixes
  started: 2026-06-04
  ```
  i.e. `tasktool start` DID flip the slice to in_progress and the review block is active. `git -C /home/simon/Dev/sigreer/skills/superstar status --short docs/tasklist.json` shows `M  docs/tasklist.json` — the lifecycle churn lives (uncommitted) in the authoritative checkout, not the worktree branch.
- The worktree's committed `docs/tasklist.json` is an expected stale point-in-time snapshot from base commit `a8e3661`; tasktool routes lifecycle mutations to the authoritative checkout, so the worktree copy is correctly stale and the read-only reviewer sandbox only sees this worktree copy.
- `planning_status: proposed` during implementation is by design for this slice — the plan (line ~19) specifies ratify happens at CLOSE (`tasktool ratify P7.S3`), not before implementation. Ratify/close are the coordinator's final step after this review passes. So "not ratified" now is correct, not a defect.

Notes:
False positive from reading the read-only worktree's committed snapshot. There is no lifecycle defect. Intentionally NOT mutating the worktree's `docs/tasklist.json` to avoid a spurious tasklist change on the worktree branch that would conflict at merge.
