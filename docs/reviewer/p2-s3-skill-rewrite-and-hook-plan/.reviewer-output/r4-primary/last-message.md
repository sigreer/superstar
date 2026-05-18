**Findings**

F8 — Severity: blocking — The planned hook still allows deleting `docs/tasklist.json`. `STAGED` excludes deletions via `--diff-filter=ACMR`, and the validation block only runs when `git ls-files --cached --error-unmatch docs/tasklist.json` succeeds. If `docs/tasklist.json` is staged for deletion, `HAS_INDEX_TASKLIST=0`, so the hook skips both strict-format and full validation. That conflicts with the spec’s “Always run `tasktool validate`” hook requirement. See `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:279`, `:288`, `:295`, `:308`, `:322`; spec at `docs/specs/2026-05-17-P2-tasktool-design.md:288`.

F1 — RESOLVED — `--hook` dispatch is still planned before shim logic and uses Bash invocation. See `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:343` and `:541`.

F2 — RESOLVED — Orphan validation keeps fully qualified IDs and includes the wrong-phase regression. See `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:129` and `:192`.

F3 — RESOLVED — The hook validates staged/index content via `:docs/tasklist.json` and has staged/worktree divergence tests. See `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:258`, `:300`, `:464`, and `:490`.

F4 — RESOLVED — The plan preserves `cmd_validate(..., format=...) -> tuple[int, str]` and appends orphan findings to the existing `errors` JSON field. See `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:205` and `:231`.

F5 — RESOLVED — `docs/tasklist.json` now records the plan in `refs` and explains why `plan_path` remains null. See `docs/tasklist.json:58`.

F6 — RESOLVED — Cross-cutting filename handling now supports top-level `YYYY-MM-DD-xN-...` IDs and tests unknown top-level cross IDs. See `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:101`, `:145`, `:174`, and `:183`.

F7 — RESOLVED — Hook idempotence now uses the stable `tasktool-pre-commit-hook` marker and includes a double-install test. See `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:266`, `:361`, and `:483`.

**Open Questions / Assumptions**

I assume `docs/tasklist.json` must remain present in a tasktool-managed repo, consistent with the plan goal and spec.

**Suggested Document Edits**

Add an explicit deletion guard before `HAS_INDEX_TASKLIST`, for example fail if `git diff --cached --name-only --diff-filter=D -- docs/tasklist.json` reports the file. Add `test_tasklist_json_deletion_rejected`.

Optionally update the project-setup audit row to grep for `tasktool-pre-commit-hook` instead of `tasktool validate --strict-format` for consistency with the new stable marker.

**Verification Gaps / Commands**

Run after edits:

`python -m pytest tools/tasktool/tests/test_pre_commit_hook.py -v`

`python -m pytest tools/tasktool/tests/test_validate_orphans.py -v`

`python -m pytest tools/tasktool/tests -q`

**Overall Verdict**

revise