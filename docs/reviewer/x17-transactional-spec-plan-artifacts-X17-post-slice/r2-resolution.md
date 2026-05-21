# Resolution for r2

## F1
Status: fixed
Evidence:
- Commit: authoritative tasklist lifecycle state is staged on `main`; implementation commits are `0e2e9cf`, `724edce`, and `be72b2b`
- Files: `/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json`
- Verification: `tasktool brief X17` from `/home/simon/Dev/sigreer/skills/superstar` reports `status: in_progress` and `started: 2026-05-21`

Notes:
Round 2 accepted that this was a stale implementation-worktree context issue. The remaining lifecycle closeout is intentionally performed after the post-slice review gate passes.

## F2
Status: fixed
Evidence:
- Commit: `be72b2b` (`X17: baseline legacy artifact status warnings`)
- Files: `.tasktool/artifact-status-baseline.json`, `tools/tasktool/artifacts.py`, `tools/tasktool/commands.py`, `tools/tasktool/tests/test_artifact_cli.py`
- Verification: `PYTHONPATH=tools pytest tools/tasktool/tests -q` -> `352 passed`
- Verification: `tools/tasktool/tasktool validate --strict-format` -> `ok`
- Verification: `git diff --check` -> clean
- Verification: `tools/tasktool/tasktool artifact status --strict` -> `artifact status: ok`
- Verification: `tools/tasktool/tasktool artifact status X17 --strict` -> `artifact status: ok`

Notes:
The repo now has a deterministic `.tasktool/artifact-status-baseline.json` listing only the known pre-X17 legacy `unreferenced-workflow-artifact` paths. Global status subtracts that baseline only for the `unreferenced-workflow-artifact` diagnostic. Row-scoped status remains unaffected, and the baseline does not suppress missing referenced artifacts, unstaged referenced artifacts, or dirty tasklist problems. New unlisted loose workflow artifacts still fail `artifact status --strict`.
