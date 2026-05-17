# Coordinator handoff — P2.S1 tasktool CLI core

You are the coordinator for implementing **P2.S1** of superstar (personal fork) at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- TASKLIST entry: [`docs/TASKLIST.md`](docs/TASKLIST.md) — find P2.S1.
- Spec: [`docs/specs/2026-05-17-P2-tasktool-design.md`](docs/specs/2026-05-17-P2-tasktool-design.md) (reviewer chain: `docs/reviewer/p2-tasktool-design-spec/`, verdict `ready with small edits` at round 4)
- Plan: [`docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md`](docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md) (reviewer chain: `docs/reviewer/p2-s1-tasktool-cli-core-plan/`, verdict `ready with small edits` at round 4)
- Reviewer chain folder (will be created on first post-slice review): `docs/reviewer/p2-s1-tasktool-cli-core-plan-P2.S1-post-slice/`

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than the process of delegating to a subagent. Tiebreak: delegate.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
- **At the end of each slice**, invoke `superstar:external-review` with `--kind post-slice`.
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until the verdict is `ready` or `ready with small edits`, or there is a genuine reason to escalate to the user.
- **At the end of the phase** (after the final slice closes), invoke `superstar:external-review` with `--kind post-phase`. Same delegation rule. Note: this is the **first slice of three** (P2.S1, P2.S2, P2.S3); plan files for S2 and S3 do not exist yet — they will be written after S1 closes (S1 ships the CLI surface that S2's import/render/migration depends on).
- **Update TASKLIST.md status in place** (☐ → ✅) when a slice closes. **Once the CLI ships (mid-S2 migration), TASKLIST.md is replaced by `docs/tasklist.json` and this rule becomes "run `tasktool close P2.S1`".** For S1 specifically, hand-edit TASKLIST.md as today.
- Archive the phase per `superstar:tasklist-discipline` when all slices are ✅.

## Slice-specific notes

- **Stdlib only** — no third-party deps. Any `pip install` is a process failure.
- **Test invocation always uses `PYTHONPATH=tools`** (the package lives at `tools/tasktool/`, not on the default Python path). The installer (Task 15) handles this for runtime; the test gate command shown in every task is what an agent runs *before* installing.
- **Do not run `tools/tasktool/install.sh`** as part of slice implementation — it writes to `~/.local/bin`. Task 14's commit step is sufficient; the operator runs the installer when ready.
- The plan defers `import`, `render`, `brief`, `archive-phase`, the pre-commit hook, and any skill rewrites to **S2 and S3**. If a subagent starts reaching for those, stop them.

## First action

Read this file (the handoff prompt), the TASKLIST entry, the spec, and the plan. Then invoke `superstar:subagent-driven-development` and begin Task 1.
