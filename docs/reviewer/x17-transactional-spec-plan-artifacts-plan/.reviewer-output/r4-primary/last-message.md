1. Findings

F7 Severity: important — RESOLVED  
The plan now adds `referenced_path_is_unstaged()` and checks both the referenced path and any dirty child path under a referenced directory via `status_path.startswith(prefix)` (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:752-760`). `cmd_artifact_status` uses that helper for referenced artifacts (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:811-816`), and the new regression covers a registered reviewer directory whose child `chain.json` is written after commit and must report `referenced-artifact-unstaged` (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:600-613`).

F2 Severity: important — RESOLVED  
No regression found from the prior resolution.

F6 Severity: important — RESOLVED  
No regression found from the prior resolution; the F7 dirty-child follow-up is now covered.

F1 Severity: blocking — RESOLVED  
No regression found from the prior resolution.

F3 Severity: important — RESOLVED  
No regression found from the prior resolution.

F4 Severity: important — RESOLVED  
No regression found from the prior resolution.

F5 Severity: important — RESOLVED  
No regression found from the prior resolution.

2. Open questions / assumptions

I assume the small status-message wording drift below can be handled as an editorial plan edit rather than another review-blocking implementation issue.

3. Suggested document edits

The spec requires `referenced-artifact-unstaged` messages to name the path plus the exact next command (`docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md:111-115`). The plan’s implementation still uses only `"referenced artifact exists but is not staged"` (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:815-816`). Update that message, or add a renderer branch for this problem code, so text output includes the suggested `tasktool artifact add ...` / `tasktool artifact commit ...` command.

4. Verification gaps / commands that should be run

Keep the planned gates:

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_artifacts.py tools/tasktool/tests/test_artifact_cli.py tools/tasktool/tests/test_worktree_authority.py -q
PYTHONPATH=tools pytest tools/tasktool/tests -q
tools/tasktool/tasktool validate --strict-format
git diff --check
```

Overall verdict: ready with small edits

