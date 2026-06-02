# Coordinator handoff — P7.S8 Reviewer-Artifact Collision Investigation

You are the coordinator for implementing **P7.S8** of Superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill.

## Inputs

- tasktool entry: run `tasktool brief P7.S8` (canonical tracker: `docs/tasklist.json`).
- Spec: [`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md`](../specs/2026-06-02-P7-integration-surface-parallel-safety-design.md) — see §4.H.
- Plan: [`docs/plans/2026-06-02-P7-S8-reviewer-artifact-investigation.md`](../plans/2026-06-02-P7-S8-reviewer-artifact-investigation.md)
- Plan reviewer chain (passed `ready with small edits`): `docs/reviewer/p7-s8-reviewer-artifact-investigation-plan/`

## Slice-specific notes — THIS IS AN INVESTIGATION SLICE

- **No `depends_on`; independently executable; parallel-safe** (disjoint surface: `external-review`).
- The first deliverable is a **reproduce-or-refute decision**, NOT a feature. The current `external-reviewer` bridge already work_id-scopes chain folders and round/role-uniques request files, so the expected outcome is **Branch B (does not reproduce)**.
- **Branch A (fix ships)** — only if the investigation finds a *workflow-reachable* collision: apply the fix across BOTH basename sites (`run_one_reviewer` AND the final-ready primary-rename at `external-reviewer.py:2694-2698`), with the deterministic (token + timestamp pinned) regression tests. Close via the normal gated `tasktool close P7.S8` with a post-slice review.
- **Branch B (no fix)** — persist the decision artifact to `docs/notes/2026-06-02-P7-S8-reviewer-artifact-investigation-decision.md`, then **`tasktool cancel P7.S8 --reason "investigation: collision does not reproduce against current bridge; see <note path>"`** (cancel bypasses the post-slice gate because nothing shipped). Do NOT `close` an unshipped slice.

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless genuinely cheaper than delegating. Tiebreak: delegate.
- **Do not pollute your context.** Delegate the investigation to a subagent; receive the decision + evidence back.
- If Branch A ships code: **at the end of the slice** invoke `superstar:external-review` with `--kind post-slice`, delegate any reviewer-driven fixes, and `tasktool close P7.S8`.
- If Branch B: cancel as above — no post-slice review is required for unshipped work.

## First action

Read this file, then run `tasktool brief P7.S8`. Read the spec (§4.H) and the plan. Verify isolation per `superstar:using-git-worktrees` (plan's first step is `tasktool start P7.S8`). Then invoke `superstar:subagent-driven-development`, run the reproduction/decision gate first, and follow the chosen branch.
