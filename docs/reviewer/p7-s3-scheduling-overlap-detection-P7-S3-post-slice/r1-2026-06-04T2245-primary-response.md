# Review — 2026-06-04-P7-S3-scheduling-overlap-detection.md (post-slice, round 1)

- Target: `docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md`
- Request: `docs/reviewer/p7-s3-scheduling-overlap-detection-P7-S3-post-slice/r1-2026-06-04T2245-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 Severity: important  
[docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s3-scheduling-overlap-detection-ready/docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md:914) gives a manual smoke command that fails as written. It sets `TT="$PWD/tools/tasktool/tasktool"`, then `cd "$SCRATCH"` and calls `$TT config init-local` / `$TT init ...` without `--project-root "$SCRATCH"`. Running that exact shape produced `smoke exit=1` with an authoritative-routing error, contradicting the expected `smoke exit=0` at line 938. The implementation itself smoked successfully when each wrapper call used `--project-root "$SCRATCH"`.

2. Open questions / assumptions

I treated the untracked `docs/reviewer/p7-s3-scheduling-overlap-detection-P7-S3-post-slice/` directory as this active review’s expected output, not a submitted-work defect.

3. Suggested document edits

Update the smoke block at lines 914-938 to either:
- create/use an explicit scratch project root via `"$TT" --project-root "$SCRATCH" ...` for every tasktool invocation, or
- use the same `PYTHONPATH=tools python -m tasktool ...` style as the CLI integration tests.

4. Verification gaps / commands that should be run

Verified:
- `python -m pytest tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_cli_integration.py -q` -> 235 passed
- `python -m pytest -q` -> 1066 passed
- `git diff --check main..HEAD` -> clean
- `./tools/tasktool/tasktool worktree status P7.S3 --integration` -> base ahead 0, landed since base none; P7.S1/P7.S2 still reported as undetermined because landed proof is unknown

No blocking implementation findings found.

Overall verdict: ready with small edits
