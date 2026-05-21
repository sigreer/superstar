# Coordinator handoff - X15 Archive closed cross-cutting items

You are the coordinator for implementing **X15** of Superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is orchestration. Use the `superstar:subagent-driven-development` skill with parallel agents where useful, or `superstar:executing-plans` if the user explicitly chooses inline execution.

## Inputs

- Tasktool entry: run `tools/tasktool/tasktool brief X15` (canonical tracker: `docs/tasklist.json`).
- Spec: [`docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md`](docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md)
- Plan: [`docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md`](docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md)
- Spec review chain: `docs/reviewer/x15-archive-closed-cross-cutting-items-design-spec/`
- Plan review chain: `docs/reviewer/x15-archive-closed-cross-cutting-items-plan/`
- Post-slice reviewer chain folder to create/use: `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/`

## Coordinator Discipline

- Start with `tools/tasktool/tasktool brief X15`, then read the spec and plan.
- If implementing in a worktree, run `tools/tasktool/tasktool start X15` before editing implementation files.
- Keep the implementation scoped to tasktool cross-cutting archive behavior.
- Preserve the user's existing staged P1 archive cleanup unless they explicitly ask you to include or alter it.
- Delegate implementation tasks where practical. Do not collapse unrelated plan tasks into one large edit.
- At closeout, run `tools/tasktool/tasktool validate --strict-format` and `python3 -m pytest tools/tasktool/tests -q`.
- Run `superstar:external-review` with `--kind post-slice` and `--work-id X15` against the completed implementation evidence. Iterate until the verdict is `ready` or `ready with small edits`.
- Before committing finished work that changes `skills/` or `tools/`, ask whether to bump the Superstar plugin version, per `AGENTS.md`.

## First Action

Run:

```sh
tools/tasktool/tasktool brief X15
sed -n '1,260p' docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md
sed -n '1,260p' docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md
```

Then invoke `superstar:subagent-driven-development` and execute the plan task-by-task.
