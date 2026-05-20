# Coordinator handoff - X11 Global External Reviewer Bridge

You are the coordinator for implementing **X11** of Superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is orchestration. Use the `superstar:subagent-driven-development` skill with parallel agents where possible. Do not implement directly unless the specific fix is genuinely smaller than delegating it.

## Inputs

- tasktool entry: run `tasktool brief X11` or `tools/tasktool/tasktool show X11` from the repo.
- Spec: [`docs/specs/2026-05-20-X11-global-external-reviewer-bridge-design.md`](docs/specs/2026-05-20-X11-global-external-reviewer-bridge-design.md)
- Spec reviewer chain: `docs/reviewer/x11-global-external-reviewer-bridge-design-spec/`
- Plan: [`docs/plans/2026-05-20-X11-global-external-reviewer-bridge.md`](docs/plans/2026-05-20-X11-global-external-reviewer-bridge.md)
- Plan reviewer chain: `docs/reviewer/x11-global-external-reviewer-bridge-plan/`
- Post-slice reviewer chain to create at closeout: `docs/reviewer/x11-global-external-reviewer-bridge-X11-post-slice/`

## Status

- Spec gate: passed, `ready with small edits`.
- Plan gate: passed, `ready with small edits`.
- X11 is still `ready`; first execution step is:
  ```bash
  tools/tasktool/tasktool set X11 --status in_progress
  ```

## Coordinator discipline

- Invoke `superstar:using-git-worktrees` before editing. Use an X11 implementation worktree unless Simon explicitly opts out in the current session.
- Invoke `superstar:subagent-driven-development` before dispatching implementation work.
- Follow the plan task order. It already incorporates both spec-review and plan-review findings.
- Keep `reviewer-agent` unchanged unless a real issue is discovered. The canonical bridge command is `external-reviewer`; `/home/simon/.local/bin/reviewer` is intentionally non-canonical.
- Do not route new guidance through the old repo-local bridge command; `scripts/external-reviewer.py` is compatibility-shim only.
- At implementation closeout, run the X11 post-slice review command from the plan, iterate until the chain verdict is `ready` or `ready with small edits`, then close X11 with `tasktool close X11 --reviewer-chain docs/reviewer/x11-global-external-reviewer-bridge-X11-post-slice`.

## First action

Read this handoff, then run:

```bash
tools/tasktool/tasktool show X11
git status --short
```

Then invoke `superstar:using-git-worktrees`, enter the X11 implementation worktree, mark X11 in progress, and begin Task 0 of the plan.
