# Coordinator handoff — P2.S3 Skill rewrite & pre-commit hook

You are the coordinator for implementing **P2.S3** of superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.

## Inputs

- tasktool entry: run `tasktool brief P2.S3` (or `PYTHONPATH=/home/simon/Dev/sigreer/skills/superstar/tools python3 -m tasktool brief P2.S3` if the shim is not on PATH yet).
- Spec: [`docs/specs/2026-05-17-P2-tasktool-design.md`](docs/specs/2026-05-17-P2-tasktool-design.md)
- Plan: [`docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md`](docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md)
- Plan reviewer chain (passed `ready` at round 5): [`docs/reviewer/p2-s3-skill-rewrite-and-hook-plan/`](docs/reviewer/p2-s3-skill-rewrite-and-hook-plan/)
- Post-slice reviewer chain folder (will be created on first review): `docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/`

## Coordinator discipline (non-negotiable)

- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than the process of delegating to a subagent. Tiebreak: delegate. The `tasktool brief` / `tasktool show` calls are coordinator-cheap; everything else is a subagent.
- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
- **At the end of the slice**, invoke `superstar:external-review` with `--kind post-slice --work-id P2.S3 --file docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md --context docs/specs/2026-05-17-P2-tasktool-design.md --context docs/tasklist.json --prompt-transport stdin --review-depth thorough --emit json`.
- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until the verdict is `ready` or `ready with small edits`, or there is a genuine reason to escalate to the user.
- **Close the slice via `tasktool close P2.S3`** — the CLI re-checks the reviewer chain and refuses on `revise`. The hook installed by Task 4 will also be in effect from that task onward; any reviewer-chain artifacts that get committed must satisfy it.
- **At the end of the phase** (after the final slice closes — note P2 has only S1, S2, S3 currently; if no further slices are added, the phase closes when S3 closes), invoke `superstar:external-review` with `--kind post-phase` and then `tasktool archive-phase P2`. Same delegation rule.

## Known parser caveat

The plan-review chain for this slice's plan reached an explicit `Overall Verdict: ready` at round 5, but the JSON `merged_verdict`/`verdict` shows `None` because the reviewer wrapper duplicates its body in stdout and stderr, confusing the script's parser. P2.S2 hit and documented the same artifact. If the post-slice review hits it too, read the response body directly and use `--skip-review-gate` on `tasktool close` only after confirming the substantive verdict is unambiguous (record the bypass reason in the slice `notes` per spec §8.2). Do **not** routinely bypass the gate.

## First action

Read this file (the handoff prompt), run `tasktool brief P2.S3`, then read the spec and the plan. Then invoke `superstar:subagent-driven-development` and begin Task 1 of the plan.
