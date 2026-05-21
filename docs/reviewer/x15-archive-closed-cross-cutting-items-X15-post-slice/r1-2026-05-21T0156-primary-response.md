# Review — 2026-05-21-X15-archive-closed-cross-cutting-items.md (post-slice, round 1)

- Target: `docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md`
- Request: `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/r1-2026-05-21T0156-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

# Post-slice review — X15 archive closed cross-cutting items

## Findings

**F1. Slice work item is not started or closed. Severity: important**

`docs/tasklist.json:213-225` shows `X15` is still `status: ready`, `started: null`, `closed: null`. The plan's Execution Setup Step 1 mandates `tasktool start X15` and Task 5 Step 4 mandates `tasktool close X15 [--no-archive]`. A post-slice review fired while the work item is still `ready` contradicts the lifecycle the plan and `tasklist-discipline` skill define for this slice.

**F2. All implementation changes are uncommitted. Severity: important**

`git status` shows 19 modified files plus 5 untracked artifacts (spec, plan, handoff, new test, reviewer dir). The plan's Task 5 Step 5 calls for a single commit before close. No commit on `x15-…` branch references this work — the last commit on HEAD is `91261f1 X16: …`. Post-slice gating should normally happen against committed (or at minimum, staged) state; reviewers cannot confirm artifact stability against a working tree that can still drift.

**F3. Doc-test enforcement missing. Severity: important**

`tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` is unmodified (`git diff --stat` returns nothing for it). Plan Task 4 Step 1 explicitly required adding:
```python
assert "tasktool close X" in text
assert "--no-archive" in text
assert "archive-cross" in text
```
The SKILL.md edits do contain those strings (`skills/tasklist-discipline/SKILL.md:22,64,65,76`), so the user-facing copy lands — but there is no regression guard. If a future SKILL edit drops the lines, nothing fails. This is the only acceptance criterion in Task 4 and it was skipped.

**F4. External post-slice review not run. Severity: important**

`docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/chain.json` has `"rounds": []` and both `sweep_checkpoints` are `pending`. Plan Task 5 Step 3 is explicit: run `external-reviewer review --kind post-slice …` until verdict is `ready` / `ready with small edits`. The chain folder was created but no round was executed. (This very review may be the missing round 1 — if so, the chain still needs round files written and the verdict recorded before close.)

**F5. Test suite not exercised (or evidence not surfaced). Severity: important**

Plan Task 5 Step 1 requires `python3 -m pytest tools/tasktool/tests -q` and `tools/tasktool/tasktool validate --strict-format` to pass before closeout. No evidence in the worktree (no test output capture, no reviewer round noting the result, and no commit). Given the volume of touched files (model, serialize, validate, schema_gen, migrate, render, commands, cli, 6 test files + 1 new), a green run is the load-bearing claim of this slice and it is unverifiable from repo state.

**F6. Implementation deviation from plan (acceptable but worth noting). Severity: minor**

Plan Task 3 Step 6 specifies a separate `_raise_if_archived_cross(p, id, *, for_close)` helper called after `_load` and before `_find_item`. The actual implementation folds the archived-id hint into `_find_item` itself (`tools/tasktool/commands.py:481-484`). The behavior the tests assert (`test_close_archived_cross_reports_archived_hint`) still holds, but `archive-cross X<archived-id>` will surface the close-flavored phrase "may already be archived" rather than the archive-cross-flavored "is already archived" required by spec §4. The hint message branches by `for_close` in the plan; the current code does not. Confirm by tracing `cmd_archive_cross` on an already-archived id — `_find_item` raises before the `cmd_archive_cross` body can emit the spec-mandated `cross-cutting X1 is already archived`.

**F7. `_archive_cross_at_root` writes the archive file outside the validation/atomicity claim. Severity: minor**

The spec §4 says: "build archive content in memory, mutate the project in memory, validate, write the archive file, save tasklist.json, and stage both touched files." The implementation orders: mutate → `validate_project(p)` → `archive_path.write_text(...)` → return → caller calls `_save`. So validation runs before the file is on disk — good. But the test `test_archive_cross_atomicity_no_orphan_file_on_validation_failure` patches `validate_project` *globally*, which means the `validate_project` inside `_archive_cross_at_root` also raises before mutation gets persisted — that proves the orphan-file invariant. Less obvious: if `_save` later fails (disk full, IO error), the markdown file is already on disk and `cross_cutting` mutation is lost from tasklist, producing an orphan archive on retry. Not a regression vs. phase archive (same shape), but the plan/spec called out atomicity explicitly; surfacing this residual risk is worthwhile.

**F8. `cmd_archive_cross` does not assert active membership before archive. Severity: minor**

`_find_item` resolves archived-X to an error, but if an X has been hand-edited into both lists (or a future bug allows it), `_archive_cross_at_root`'s `any(a.id == item.id for a in p.archived_cross_cutting)` guard fires only after `_find_item` succeeds. Coverage exists for the duplicate-id validation path; there is no test for `cmd_archive_cross` on an id only present in `archived_cross_cutting` (the resolver path). Low likelihood, low impact, but a one-line test would close it.

**F9. Reviewer chain naming/work-id sanity. Severity: nit**

Chain dir is `x15-archive-closed-cross-cutting-items-X15-post-slice` and `chain.json` repeats `work_id: X15`. Conventional pattern (cf. prior `x10-…-X10-…` chain entries in tasklist.json refs) is fine; flagging only because the duplicated `X15` segment looks like a typo at a glance.

## Open questions / assumptions

- Is the intent to commit X15 *with* its own delivery row archived (the new default) or kept visible (`--no-archive`)? Plan Task 5 Step 4 leaves it operator-choice; the reviewer cannot infer the desired final tasklist shape.
- Was the test suite run locally and is the green evidence simply not yet recorded in the reviewer chain, or has it never been run end-to-end?
- Is `_raise_if_archived_cross` plan deviation (F6) intentional, or did the implementor not notice the spec-mandated split between close-time and archive-time hint phrasing?

## Suggested document edits

- Plan Task 4 Step 1: keep it. Add it back to the slice — it is currently the only test that prevents SKILL.md drift, and it was skipped.
- Plan Task 5 Step 1: require the operator to paste the `pytest` summary into the reviewer chain round file as evidence rather than relying on local-only execution.
- Spec §4 / Plan Task 3 Step 6: either reconcile the wording so both `close` and `archive-cross` can share `_find_item`'s single hint message, or restore the dual-phrasing helper. Right now spec text and code disagree on the `archive-cross`-on-archived-id error string.

## Verification gaps / commands to run

```sh
python3 -m pytest tools/tasktool/tests -q
tools/tasktool/tasktool validate --strict-format
tools/tasktool/tasktool render | rg -n "Cross-cutting|Archived cross-cutting|X15"
tools/tasktool/tasktool show X15
```

Then exercise the spec-mandated error path that F6 flags:
```sh
# after archiving X1, expect "cross-cutting X1 is already archived"
tools/tasktool/tasktool archive-cross X1
```

And record the result in `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/r1-…md` so the chain stops being empty.

Overall verdict: revise
