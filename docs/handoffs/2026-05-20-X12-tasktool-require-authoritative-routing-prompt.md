# Coordinator handoff — X12 tasktool: require authoritative-checkout routing for mutations

You are the coordinator for implementing **X12** of superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- tasktool entry: run `tasktool brief X12` (canonical tracker: `docs/tasklist.json`).
- X12 is cross-cutting (not a phase slice). `tasktool schedule` / `ready-slices` do not apply; proceed task-by-task per the plan.
- Spec: [`docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md`](../specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md)
- Plan: [`docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md`](../plans/2026-05-20-X12-tasktool-require-authoritative-routing.md)
- Reviewer chain folders (already populated through plan review):
  - Spec: `docs/reviewer/x12-tasktool-require-authoritative-routing-design-spec/`
  - Plan: `docs/reviewer/x12-tasktool-require-authoritative-routing-plan/`
  - Post-slice (will be created on first review): `docs/reviewer/x12-tasktool-require-authoritative-routing-post-slice/`

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than the process of delegating to a subagent. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
- **At the end of the slice** (X12 is a single cross-cutting slice), invoke `superstar:external-review` with `--kind post-slice` and `--work-id X12`. Use `AGENT_REVIEWER_PROVIDER=codex` to keep continuity with the spec/plan reviewers.
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent that writes a `docs/reviewer/<chain>/r{N}-resolution.md` per the post-slice contract. Iterate until the verdict is `ready` or `ready with small edits`.
- **Close the cross-cutting item via `tasktool close X12`** when the post-slice review passes; the CLI enforces the post-slice external-review gate.

## Special notes for X12

- The plan introduces a hard error on missing `.tasktool/config.json`. This repo already has `mutation_mode: authoritative-checkout` configured, so the implementation work itself routes correctly. Subagents must NOT delete or rewrite `.tasktool/config.json` during implementation.
- Task 6 (skill text updates) edits three skill files that other workflows depend on. Verify all three open without rendering issues after the edits.
- Task 2 step 5 explicitly captures the list of pre-existing tests that broke under the new hard-error default. Track those failures, then in Task 6 step 2 repair each by adding either `tasktool config init-local` or `tasktool config init-authority --branch main` setup to the fixture.
- Bump the Superstar plugin version after the implementation work is complete: this is a user-visible behaviour change. Default to a minor bump (X.(Y+1).0). Confirm with the user before running `./scripts/bump-version.sh`.

## First action

Read this file, then run `tasktool brief X12`. Read the spec and the plan. Then invoke `superstar:subagent-driven-development` and dispatch Task 1 (config.py sentinel + tests) as the first subagent task.
