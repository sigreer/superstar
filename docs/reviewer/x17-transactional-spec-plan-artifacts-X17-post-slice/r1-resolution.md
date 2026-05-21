# Resolution for round 1

F1 was a review-context issue. `tasktool start X17` was run from the authoritative checkout before implementation, and `/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json` currently records X17 as `in_progress` with `started: 2026-05-21`. The first review was invoked from the implementation worktree and used that worktree's stale `docs/tasklist.json` context, which does not receive routed tasktool mutations. The rerun will pass the authoritative tasklist path explicitly.

F2 was fixed in commit `724edce` (`X17: include archived artifacts in status`). Global artifact status now counts `archived_phases[].archived_path` as referenced and parses archived phase markdown JSON snapshots to include embedded workflow artifact references such as `spec_path`, `plan_path`, `planning_path`, reviewer chains, and refs. Regression coverage was added in `tools/tasktool/tests/test_artifact_cli.py`.

Verification after the fix:

```sh
PYTHONPATH=tools pytest tools/tasktool/tests -q
tools/tasktool/tasktool validate --strict-format
git diff --check
tools/tasktool/tasktool artifact status X17 --strict
```

Results: `347 passed`; validation `ok`; whitespace check clean; scoped X17 artifact status `ok`.
