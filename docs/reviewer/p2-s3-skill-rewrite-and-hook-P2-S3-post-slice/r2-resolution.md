# Resolution for r2

## F4 (primary, minor)
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md` (file map row for `test_pre_commit_hook.py`)
- Verification: row no longer claims a literal `TASKTOOL_RAW=1` test; explicitly notes that `TASKTOOL_RAW` is editor-side scaffolding the hook does not inspect.

Notes:
Applied the primary reviewer's optional suggestion to soften the wording. The test continues to cover the recovery path semantically via `test_raw_edit_then_normalise_passes`.

## S1.F1 (sweep, blocking — current-round review artifacts untracked)
Status: waived
Evidence:
- Chain: `docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/`
- Verification: the r2 request/response/sweep files are now staged in the same commit as this resolution doc. They were necessarily untracked at the moment the sweep reviewer inspected the worktree, because the bridge writes them before the reviewer reads.

Notes:
This is the artifact-catch-22 pattern documented in the slice handoff (`docs/handoffs/2026-05-18-p2-s3-skill-rewrite-and-hook-prompt.md` "Known parser caveat" section refers to P2.S2 hitting the same shape): every post-slice round emits new request/response files into the chain folder, and a sweep reviewer with no chain context will always see those as "untracked" at request time. The primary reviewer, which has chain context, understands this and rated r2 `ready with small edits`. The substantive verdict is unambiguous: all earlier findings are RESOLVED per the primary, and the sweep's only remaining blocker is the artifact loop itself. Committing the r2 chain alongside this resolution closes it for r3.
