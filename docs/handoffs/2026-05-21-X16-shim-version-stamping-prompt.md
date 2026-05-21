# Coordinator handoff — X16 Stamp installed shims and enforce version drift

You are the coordinator for implementing **X16** of superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- tasktool entry: run `tasktool brief X16` (canonical tracker: `docs/tasklist.json`).
- schedule: X16 is a cross-cutting row, not a slice. No `tasktool schedule` / `ready-slices` step is required. Tasks T1–T11 in the plan execute as a single linear sequence.
- Spec: [`docs/specs/2026-05-21-X16-shim-version-stamping-design.md`](docs/specs/2026-05-21-X16-shim-version-stamping-design.md)
- Plan: [`docs/plans/2026-05-21-X16-shim-version-stamping.md`](docs/plans/2026-05-21-X16-shim-version-stamping.md)
- Spec reviewer chain (already closed `ready with small edits`): `docs/reviewer/x16-shim-version-stamping-design-spec/`
- Plan reviewer chain (already closed `ready`): `docs/reviewer/x16-shim-version-stamping-plan/`
- Implementation reviewer chain (will be created on first post-slice review): `docs/reviewer/x16-shim-version-stamping/`

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than the process of delegating to a subagent. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
- **At the end of the implementation work** (after Task 10), invoke `superstar:external-review` with `--kind post-slice` (treat X16's whole task sequence as one slice for review purposes). Pass the spec and plan as `--context`.
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until the verdict is `ready` or `ready with small edits`.
- **Close X16 via `tasktool close X16`** when the implementation review is satisfied; the CLI enforces any closeout gates.

## X16-specific context the next session needs

1. **The work in flight is a personal fork's tooling refactor.** CLAUDE.md flags this repo as the personal Superstar fork — the "94% rejection rate" upstream contributor guidelines do NOT apply here. Iterate freely on skills, hooks, and tooling. The brainstorming → spec → plan → review workflow IS binding.
2. **Version bump policy.** Per CLAUDE.md, before committing finished work that ships to users, ask the user whether to bump the version. X16 touches `skills/`, `tools/`, `hooks/`, and adds top-level `VERSION` machinery — explicitly in the "bump before shipping" category. Task 11 has a dedicated step for this prompt. **Do not bump unilaterally.**
3. **Working tree state at handoff.** The working tree contains in-flight X15 + P1 archive work as unstaged changes on top of `main`. That work is unrelated to X16 and should be left alone. Stage and commit only X16-related changes per Task 1–10. The user will handle X15/P1 separately.
4. **Reviewer chains already committed for X16:** the spec chain (`x16-shim-version-stamping-design-spec/`) and plan chain (`x16-shim-version-stamping-plan/`) are both on `main`. The implementation chain folder (`x16-shim-version-stamping/`) will appear when Task 11 runs post-slice review.
5. **Cross-cutting work, no slice graph.** This is `X16`, a cross-cutting row. No `depends_on`, no `parallel_group`, no `tasktool ratify` step needed. The 11 tasks in the plan are sequential because each builds on the previous (VERSION file → fragment → installers → publish/deploy → cleanup).
6. **Three commits already on main for X16 setup:**
   - `1032111` — initial spec
   - `5f67582` — spec r1 review findings applied
   - `91261f1` — spec reviewer chain (r1+r2)
   - `7eb29cc` — initial plan
   - `9676d04` — plan r1 review findings applied (F1–F5)
   - `fd1acdf` — plan r2 review findings applied (F6 dry-run, F7 claude excludes)
   - The plan reviewer chain (`x16-shim-version-stamping-plan/r1`, `r2`, `r3`) is NOT yet committed. Commit it as part of the implementation work or as a prep commit before Task 1.

## First action

Read this file (the handoff prompt), then run `tasktool brief X16`. Read the spec and the plan. Commit the plan reviewer chain folder `docs/reviewer/x16-shim-version-stamping-plan/` if it's still untracked. Then invoke `superstar:subagent-driven-development` and begin with Task 1 (VERSION file + bump-version plain format).
