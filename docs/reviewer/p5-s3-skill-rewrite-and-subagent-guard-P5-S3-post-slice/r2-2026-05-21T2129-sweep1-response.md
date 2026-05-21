# Review — 2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md (post-slice, round 2)

- Target: `docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md`
- Request: `docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/r2-2026-05-21T2129-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: blocking — A compliant dispatched subagent cannot run the current tasktool lifecycle tests after following the new prompt directive. The templates require the first shell command to be `export SUPERSTAR_SUBAGENT_ROLE=<role>` ([implementer-prompt.md](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/skills/subagent-driven-development/implementer-prompt.md:21), [spec-reviewer-prompt.md](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/skills/subagent-driven-development/spec-reviewer-prompt.md:15)), and `cmd_start` refuses whenever that env var is present ([commands.py](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/tools/tasktool/commands.py:733)). But existing positive lifecycle tests copy the ambient environment into subprocesses ([test_lifecycle_start.py](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/tools/tasktool/tests/test_lifecycle_start.py:11)), so they fail under the exact env the new subagent templates mandate. Repro run: `export SUPERSTAR_SUBAGENT_ROLE=implementer; python -m pytest tools/tasktool/tests/test_lifecycle_start.py::test_start_slice_sets_in_progress_and_started -q` fails with the new refusal message. This leaves the slice with a broken subagent verification path: subagents are told to export the guard variable, then cannot run tests that assert top-level `tasktool start` behavior unless those tests explicitly scrub or override the subagent env.

2. Open questions / assumptions

I treated the best-effort prompt-template shim as accepted by the plan, despite the spec’s literal shim wording. I did not treat that mismatch as a finding because the plan explicitly scopes it as prose plus runtime guard.

3. Suggested document edits

Update the test helpers that expect coordinator/top-level behavior to sanitize `SUPERSTAR_SUBAGENT_ROLE`, `CLAUDE_AGENT_ROLE`, and `SUPERSTAR_FORCE_SUBAGENT`, or add an explicit coordinator test env. Add a regression test that runs at least one positive `tasktool start` lifecycle test under an ambient `SUPERSTAR_SUBAGENT_ROLE` and proves the test harness isolates the subprocess correctly.

4. Verification gaps / commands that should be run

Already run during this review:
`tools/tasktool/tasktool validate --strict-format` -> `ok`
`python -m pytest tools/tasktool/tests/test_lifecycle_start.py tools/tasktool/tests/test_subagent_prompt_shim.py tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` -> `38 passed`
`python -m pytest tools/tasktool/tests -q` -> `526 passed`
`export SUPERSTAR_SUBAGENT_ROLE=implementer; python -m pytest tools/tasktool/tests/test_lifecycle_start.py::test_start_slice_sets_in_progress_and_started -q` -> `1 failed`

Overall verdict: revise
