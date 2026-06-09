1. Findings

F1. RESOLVED. Severity: blocking. Task 2’s `_repo()` now initializes a git repo before subprocess invocation, so `run_preflight()` can call `repo_root()` successfully. Reference: `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md:526`.

F2. RESOLVED. Severity: important. Task 2 now includes standalone `preflight --emit json` subprocess coverage for all AC2 check classes: placeholder, dangling markdown link, dangling backtick path, missing section, missing context, and oversized context. Reference: `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md:580`.

F3. RESOLVED. Severity: important. Task 3 now includes `test_schema_too_new_aborts_before_preflight`, with a too-new `chain.json` and a target that would otherwise fail preflight, asserting the schema path wins. Reference: `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md:810`.

No unresolved findings.

2. Open questions / assumptions

I assume the remaining `preflight` subcommand should keep the existing git-root requirement, matching the current `review` path and the updated subprocess harness.

3. Suggested document edits

Small edit: Task 5 Step 4 runs `--kind spec` for both a spec and a plan sample. The plan sample should use `--kind plan`; otherwise the smoke may report a misleading missing acceptance-criteria failure on an already-reviewed plan. Reference: `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md:1061`.

4. Verification gaps / commands

No blocking verification gaps. Keep the planned gates:
`python -m pytest skills/external-review/tests -q`
`python3 skills/external-review/scripts/external-reviewer.py preflight --help`
`python3 skills/external-review/scripts/external-reviewer.py review --help | grep -A1 -- '--no-preflight'`

Overall verdict: ready with small edits

