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

**F1 — Severity: important.** Test suite has not been executed in evidence. The plan's verification gate (Task 5 Step 1) requires `tools/tasktool/tasktool validate --strict-format` and `python3 -m pytest tools/tasktool/tests -q` to pass. The chain folder `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/chain.json` shows `rounds: []` and no committed reviewer artifacts, and there is no log of these commands succeeding against the current diff. With ~600 LOC of new code and 11 new behavioral tests, a full pytest run is the load-bearing evidence; the slice should not be closed until the operator pastes the green output (or it is captured in the round artifacts).

**F2 — Severity: minor.** Error-message drift between `cmd_archive_cross` and the spec. The spec (§4 / "Error handling") says `tasktool archive-cross X15` where the pointer already exists must fail with `cross-cutting X15 is already archived`. In the implementation, `_find_item` is reached first and raises the close-flavored message `cross-cutting X15 not found in active tasklist; it may already be archived` (`tools/tasktool/commands.py:481-484`). The "already archived" branch inside `_archive_cross_at_root` (lines that emit `is already archived`) is only reachable if the row is *both* in active `cross_cutting` and `archived_cross_cutting`, which validation disallows. Net effect: the user-facing `archive-cross` path never emits the spec's intended message. Either tighten the message in `_find_item` to be neutral and let `_archive_cross_at_root` produce the precise message, or add a dedicated precheck on `cmd_archive_cross` before `_find_item` (matches the plan's `_raise_if_archived_cross` Step 6 design, which was not implemented).

**F3 — Severity: minor.** `_find_item`'s archived-hint side-effect now applies to every command (`start`, `set`, `block`, `unblock`, `archive-cross`, `note`, `ref`, `brief`) — not just `close`. That is arguably a usability win but it is broader than what the plan and spec described (both scoped the hint to `cmd_close`). Worth a sentence in the SKILL or a docstring comment; not a behavior bug.

**F4 — Severity: minor.** `test_close_no_archive_rejects_non_cross_items` passes `skip_review_gate=True` (`tools/tasktool/tests/test_commands.py`), but with the current `cmd_close` ordering the `--no-archive` rejection fires before the gate check, so `skip_review_gate` is unreachable filler. Not a defect — but if the kind/gate ordering is ever swapped, this test will silently bypass the new rule. Either drop `skip_review_gate=True` or assert ordering explicitly.

**F5 — Severity: minor.** Task 5 Step 4 (close `X15` itself) and Step 5 (commit) are inherently incomplete at review time — that is expected. Flagging so the closeout checklist is not lost: the worktree still shows `X15` active in `docs/tasklist.json` (lines 23+ list X1..X14 active, X15 not yet appearing in `cross_cutting` because it sits outside the file's visible head), the plan/spec/handoff/reviewer-folder are all untracked, and no `Archive X15` commit exists yet. The plan rightly defers these to post-review; just confirming nothing is silently missed.

**F6 — Severity: nit.** `_archive_cross_at_root` writes the archive markdown after `validate_project(p)` succeeds, satisfying atomicity. However `_save` happens *after* `archive_path.write_text`, so a failure during JSON write/save leaves the archive file on disk without a corresponding pointer entry on disk. The in-memory pointer is correctly added before validation, and `_save` is the canonical-write path, so practical risk is low; if you care about strict on-disk atomicity, write the archive file last (post-`_save`) or wrap in a try/unlink. Plan and spec both accept the current ordering, so this is informational.

**F7 — Severity: nit.** `next_cross_id` was extended to consume both `archived_cross_cutting` and `scan_orphan_ids` (`tools/tasktool/allocate.py:99-101`). Good — it prevents ID reuse. The plan did not call this out explicitly; the new test `test_create_cross_does_not_reuse_archived_id` covers it. Worth a one-line callout in `skills/tasklist-discipline/SKILL.md` so users know archived X IDs are still reserved.

## Open questions / assumptions

- Was `python3 -m pytest tools/tasktool/tests -q` run cleanly against this exact diff? Please attach the tail of the run to a round artifact before closing.
- Was `tools/tasktool/tasktool render` smoke-checked? The new "Archived cross-cutting (`X*`)" header is only exercised through unit tests today.
- Intent on F2 — is the cross-command hint deliberate, or do you want a precise `is already archived` message specifically for `archive-cross`?

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
