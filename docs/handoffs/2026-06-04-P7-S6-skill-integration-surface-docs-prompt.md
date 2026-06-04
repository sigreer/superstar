# Coordinator handoff — P7.S6 Skill changes for integration-surface-aware parallel safety

You are the coordinator for implementing **P7.S6** of superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible. Note: P7.S6 is a small, mostly-sequential documentation slice (five short doc edits guarded by string-assertion tests), so tasks largely run in series; the value of subagents here is fresh context per task and the two-stage in-loop review, not parallelism.

## Inputs

- tasktool entry: run `tasktool brief P7.S6` (canonical tracker: `docs/tasklist.json`).
- schedule: `tasktool show P7.S6` — the row is `ratified`, `depends_on = P7.S2, P7.S3, P7.S4` (all `done`), no parallel group.
- Spec (§4.F + §6 `S6` govern this slice): [`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md`](docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md)
- Plan: [`docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md`](docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md)
- Reviewer chain folder (will be created on first post-slice review): `docs/reviewer/p7-s6-skill-integration-surface-docs-post-slice/`

## Slice-specific notes

- **Nature:** pure docs slice. It edits four `SKILL.md` files (`subagent-driven-development`, `tasklist-discipline`, `phase-planning`, `writing-plans`) and adds `skills/subagent-driven-development/references/registry-merge-playbook.md`. No tasktool Python behaviour changes — the CLI surface it documents (`surface`/`reserve`/`coordinate`/`surface check`/`worktree status --integration`) already shipped in P7.S2–S4.
- **TDD here = doc-content assertions.** Each task adds a string-assertion function to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`, runs it red, then edits the skill prose to turn it green. Test command: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -q`.
- **Self-edit caution:** the implementer will be editing `writing-plans` and `subagent-driven-development` — the very skills in play. The plan gives exact insert/replace anchors; have subagents follow them verbatim and not "improve" surrounding prose.
- **No P7.S5 dependency:** the integrate-current-main checkpoint documents `tasktool worktree sync` as "when available" plus a raw-git fallback, so the slice is correct whether or not S5 has shipped.
- **Version bump:** this slice ships skill changes (`skills/**`), so per `CLAUDE.md` ask the human partner about a version bump at slice/phase closeout — not during the per-task commits.

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than delegating to a subagent. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
- **First execution step is `tasktool start P7.S6`** (Task 0) before any file edits, from an isolated slice worktree.
- **At the end of the slice**, invoke `superstar:external-review` with `--kind post-slice` (recommended `--review-depth thorough`), passing the plan as `--file` and the spec + `docs/tasklist.json` as `--context`, with `--work-id P7.S6`.
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until the verdict is `ready` or `ready with small edits`.
- **Close the slice via `tasktool close P7.S6`** when reviewed; the CLI enforces the post-slice external-review gate.
- P7.S6 is the second-to-last slice of P7. After it closes, only **P7.S7** (plan↔tracker drift validation, which `depends_on P7.S6`) remains before the phase can be archived — do **not** `archive-phase P7` from this slice.

## First action

Read this file (the handoff prompt), then run `tasktool brief P7.S6`. Read the spec §4.F/§6 and the plan. Then invoke `superstar:subagent-driven-development` and begin with Task 0 (`tasktool start P7.S6`).
