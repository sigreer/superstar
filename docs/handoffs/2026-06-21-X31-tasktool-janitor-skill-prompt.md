# Coordinator handoff - X31 Tasktool Janitor Skill

You are the coordinator for implementing **X31 - Tasktool janitor cleanup skill** in the Superstar repo at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where useful.

## Inputs

- tasktool entry: run `tasktool brief X31` (canonical tracker: `docs/tasklist.json`).
- Spec: [`docs/specs/2026-06-21-X31-tasktool-janitor-skill-design.md`](../specs/2026-06-21-X31-tasktool-janitor-skill-design.md)
- Plan: [`docs/plans/2026-06-21-X31-tasktool-janitor-skill.md`](../plans/2026-06-21-X31-tasktool-janitor-skill.md)
- Spec reviewer chain: `docs/reviewer/x31-tasktool-janitor-skill-design-spec/`
- Plan reviewer chain: `docs/reviewer/x31-tasktool-janitor-skill-plan/`

## Coordinator discipline

- Do not perform implementation fixes yourself unless the fix is genuinely cheaper than delegation. Tiebreak: delegate.
- Start with `tasktool start X31` and work in the printed worktree.
- Preserve unrelated untracked work currently visible in the authoritative checkout.
- Do not hand-edit `plugins/superstar/skills/**`; top-level `skills/` is canonical.
- Run the focused pytest and tasktool validation named in the plan.
- At implementation closeout, run `superstar:external-review` with `--kind post-slice`.
- Before committing finished user-shipping skill changes or publishing, ask the repo-policy version-bump question from `AGENTS.md`.

## First action

Read this file, then run:

```bash
tasktool brief X31
tasktool start X31
```

Enter the printed worktree, read the spec and plan, then invoke `superstar:subagent-driven-development` and execute the plan task by task.
