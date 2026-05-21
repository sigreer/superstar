# Merged findings for r1

## Primary

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


## Sweep 1

# Review — 2026-05-21-X15-archive-closed-cross-cutting-items.md (post-slice, round 1)

- Target: `docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md`
- Request: `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/r1-2026-05-21T0156-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

# Post-slice review — X15 Archive Closed Cross-Cutting Items

## Findings

**S1.F1 — Severity: important.** Test suite has not been executed in evidence. The plan's verification gate (Task 5 Step 1) requires `tools/tasktool/tasktool validate --strict-format` and `python3 -m pytest tools/tasktool/tests -q` to pass. The chain folder `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/chain.json` shows `rounds: []` and no committed reviewer artifacts, and there is no log of these commands succeeding against the current diff. With ~600 LOC of new code and 11 new behavioral tests, a full pytest run is the load-bearing evidence; the slice should not be closed until the operator pastes the green output (or it is captured in the round artifacts).

**S1.F2 — Severity: minor.** Error-message drift between `cmd_archive_cross` and the spec. The spec (§4 / "Error handling") says `tasktool archive-cross X15` where the pointer already exists must fail with `cross-cutting X15 is already archived`. In the implementation, `_find_item` is reached first and raises the close-flavored message `cross-cutting X15 not found in active tasklist; it may already be archived` (`tools/tasktool/commands.py:481-484`). The "already archived" branch inside `_archive_cross_at_root` (lines that emit `is already archived`) is only reachable if the row is *both* in active `cross_cutting` and `archived_cross_cutting`, which validation disallows. Net effect: the user-facing `archive-cross` path never emits the spec's intended message. Either tighten the message in `_find_item` to be neutral and let `_archive_cross_at_root` produce the precise message, or add a dedicated precheck on `cmd_archive_cross` before `_find_item` (matches the plan's `_raise_if_archived_cross` Step 6 design, which was not implemented).

**S1.F3 — Severity: minor.** `_find_item`'s archived-hint side-effect now applies to every command (`start`, `set`, `block`, `unblock`, `archive-cross`, `note`, `ref`, `brief`) — not just `close`. That is arguably a usability win but it is broader than what the plan and spec described (both scoped the hint to `cmd_close`). Worth a sentence in the SKILL or a docstring comment; not a behavior bug.

**S1.F4 — Severity: minor.** `test_close_no_archive_rejects_non_cross_items` passes `skip_review_gate=True` (`tools/tasktool/tests/test_commands.py`), but with the current `cmd_close` ordering the `--no-archive` rejection fires before the gate check, so `skip_review_gate` is unreachable filler. Not a defect — but if the kind/gate ordering is ever swapped, this test will silently bypass the new rule. Either drop `skip_review_gate=True` or assert ordering explicitly.

**S1.F5 — Severity: minor.** Task 5 Step 4 (close `X15` itself) and Step 5 (commit) are inherently incomplete at review time — that is expected. Flagging so the closeout checklist is not lost: the worktree still shows `X15` active in `docs/tasklist.json` (lines 23+ list X1..X14 active, X15 not yet appearing in `cross_cutting` because it sits outside the file's visible head), the plan/spec/handoff/reviewer-folder are all untracked, and no `Archive X15` commit exists yet. The plan rightly defers these to post-review; just confirming nothing is silently missed.

**S1.F6 — Severity: nit.** `_archive_cross_at_root` writes the archive markdown after `validate_project(p)` succeeds, satisfying atomicity. However `_save` happens *after* `archive_path.write_text`, so a failure during JSON write/save leaves the archive file on disk without a corresponding pointer entry on disk. The in-memory pointer is correctly added before validation, and `_save` is the canonical-write path, so practical risk is low; if you care about strict on-disk atomicity, write the archive file last (post-`_save`) or wrap in a try/unlink. Plan and spec both accept the current ordering, so this is informational.

**S1.F7 — Severity: nit.** `next_cross_id` was extended to consume both `archived_cross_cutting` and `scan_orphan_ids` (`tools/tasktool/allocate.py:99-101`). Good — it prevents ID reuse. The plan did not call this out explicitly; the new test `test_create_cross_does_not_reuse_archived_id` covers it. Worth a one-line callout in `skills/tasklist-discipline/SKILL.md` so users know archived X IDs are still reserved.

## Open questions / assumptions

- Was `python3 -m pytest tools/tasktool/tests -q` run cleanly against this exact diff? Please attach the tail of the run to a round artifact before closing.
- Was `tools/tasktool/tasktool render` smoke-checked? The new "Archived cross-cutting (`X*`)" header is only exercised through unit tests today.
- Intent on S1.F2 — is the cross-command hint deliberate, or do you want a precise `is already archived` message specifically for `archive-cross`?

## Suggested document edits

1. Plan Task 5, Step 1: add an explicit "paste tail of pytest output into `docs/reviewer/.../r1-notes.md`" instruction so the reviewer round captures verification evidence rather than relying on the plan body.
2. Plan Task 4: note that `next_cross_id` now reserves archived X IDs (informs the SKILL update copy).
3. Spec §4 / Error handling: reconcile with implementation — either soften "is already archived" or instruct the implementation to short-circuit `cmd_archive_cross` before `_find_item`.

## Verification gaps / commands that should be run

```sh
tools/tasktool/tasktool validate --strict-format
python3 -m pytest tools/tasktool/tests -q
tools/tasktool/tasktool render | rg -n "Cross-cutting|Archived cross-cutting"
```

Capture output under `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/r1-*.md` before requesting the close.

Overall verdict: ready with small edits
