# Coordinator handoff — X17 Transactional Spec and Plan Artifact Handling

You are the coordinator for implementing **X17** of Superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- tasktool entry: run `tasktool brief X17` (canonical tracker: `docs/tasklist.json`).
- Spec: [`docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md`](docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md)
- Plan: [`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md`](docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md)
- Spec reviewer chain folder: `docs/reviewer/x17-transactional-spec-plan-artifacts-design-spec/`
- Plan reviewer chain folder: `docs/reviewer/x17-transactional-spec-plan-artifacts-plan/`

## Coordinator discipline

- Start with `tasktool start X17`.
- Keep implementation work in an isolated worktree unless the user explicitly opts out.
- Do not perform reviewer-driven fixes yourself when delegation is practical. Pass reviewer responses to fix subagents and integrate their changes.
- At closeout, run the plan's verification gates:

```bash
PYTHONPATH=tools pytest tools/tasktool/tests -q
tools/tasktool/tasktool validate --strict-format
git diff --check
```

- Run `superstar:external-review` with `--kind post-slice --work-id X17` before closing.
- Close X17 with `tasktool close X17` only after post-slice review returns `ready` or `ready with small edits`.
- This changes `tools/` and `skills/`; before finished-work commit/publish closeout, ask the AGENTS.md version-bump question.

## First action

Read this handoff, then run:

```bash
tasktool brief X17
```

Read the spec and plan. Then invoke `superstar:subagent-driven-development` and implement the plan task by task.
