# Review — 2026-05-19-p4-tasktool-coordination-lifecycle-design.md (post-phase, round 2)

- Target: `docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md`
- Request: `docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r2-2026-05-19T2342-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

# Review — 2026-05-19-p4-tasktool-coordination-lifecycle-design.md (post-phase, round 2)

- Target: `docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md`
- Mode: incremental verification against r1 resolution report
- Verified at HEAD `ff19dfb`

## 1. Findings

**F1 — RESOLVED.** `tools/tasktool/cli.py:67-68` exposes `--allow-ready-close` and `--reason` on the `set` parser; `tools/tasktool/commands.py:357-377` plumbs them through `cmd_set` and routes through the shared `_apply_ready_close_override` audit helper. Error message at `commands.py:373-376` now references the actual `set` flag combination. Parity with `close` is real, not just documented.

**F2 — RESOLVED.** `tools/tasktool/validate.py:45-59` now asserts `started >= created`, `closed >= created`, and `closed >= started`. Verified inline; resolution report records `pytest tools/tasktool/tests/test_validate.py … -q -> 110 passed`.

**F3 — RESOLVED.** `docs/tasklist.json` shows P4 `started: "2026-05-19"`, `status: "in_progress"`. Phase lifecycle marker now exists before archive.

**F4 — RESOLVED.** `docs/tasklist.json` P4.S1 carries an explicit grandfathering note explaining the `started: null` is intentional pre-P4.S2-guard residue. Future readers will not mistake it for a defect.

**F5 — RESOLVED.** `skills/tasklist-discipline/SKILL.md:40` now documents that `tasktool unblock <slice-id> --resume` resumes through the same lifecycle path and stamps `started` when needed. Skill regression test covers it.

**F6 — RESOLVED (waived with reason).** Resolution explains the intentional lifecycle tightening: `set --status in_progress` routes through `_start_item`, which refuses already-done rows. Reopen policy is explicitly out of P4 scope per acceptance criteria. Acceptable waiver.

**F7 — RESOLVED (waived with reason).** `docs/tasklist.json` is the canonical status surface; plan checkboxes are advisory. Acceptable waiver.

**F8 — DEFERRED (correctly).** Archive remains gated on this round's verdict. Resolution correctly refuses to bypass the gate. Once this review returns ready / ready-with-small-edits, `tasktool archive-phase P4` is the next action.

**F9 — RESOLVED.** No issue noted in r1; reverified by resolution.

**S1.F1 — PARTIALLY RESOLVED, DEFERRED.** P4 is now started (lifecycle marker present); close + archive is appropriately deferred until this round's verdict lands. No additional action needed *this* round.

**S1.F2 — RESOLVED.** Same as F4.

**S1.F3 — RESOLVED.** Same as F1.

**S1.F4 — RESOLVED (waived with reason).** Spec explicitly defers abrupt project migration. Acceptable.

**S1.F5 — RESOLVED.** Reviewer chain directory and `r1-resolution.md` are committed in `ff19dfb`. `git status` clean.

**S1.F6 — RESOLVED.** Resolution records `tools/tasktool/tasktool validate --strict-format -> ok` and full-suite `pytest tools/tasktool/tests -q -> 253 passed in 22.22s`.

**S1.F7 — RESOLVED.** P4 was started; phase lifecycle hook is exercised. The remaining ambiguity (start accepts phases but close does not require it for phases) is consistent with the spec's intent that phase close is gated by slice completion. No further action.

**S1.F8 — RESOLVED (waived with reason).** `planning_path` vs `spec_path` field-naming ambiguity is a pre-existing tasklist convention, not a P4 lifecycle issue. Acceptable.

**F10 (new) — Spec text drift vs implemented bypass surface.** Severity: nit
Spec §Lifecycle Enforcement (lines 151-156) still says only "Closing slices from `ready` is refused unless `--allow-ready-close` is supplied" without mentioning that the bypass is now exposed on *both* `close` and `set --status done`. Since F1 was resolved by code, the spec narrative should mirror it (one sentence). Not blocking; consider including in the archive commit. The plan and skill are already correct.

## 2. Open questions / assumptions

- Assumed the `253 passed` result reported in `r1-resolution.md` reflects the same code at HEAD `ff19dfb`. The repair commit is the same `HEAD` as the verification run; the worktree is clean per the chain summary.
- No new code landed between resolution and this round; reverification is a re-read, not a re-run.

## 3. Suggested document edits (non-blocking)

- Spec §Lifecycle Enforcement: add a sentence noting that `--allow-ready-close --reason` is exposed on both `tasktool close` and `tasktool set --status done`, and both append the same audit note. Resolves F10.
- Phase archive note (to be materialised by `tasktool archive-phase P4`): include the P4.S1 grandfathering rationale already present in the tasklist note.

## 4. Verification gaps / commands to run

Closeout actions, in order:

```sh
git status --short                              # expect clean
tools/tasktool/tasktool validate --strict-format
tools/tasktool/tasktool close P4 --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase
tools/tasktool/tasktool archive-phase P4
```

No code-level verification gaps remain. F10 is a one-line doc edit and can ride the archive commit.

## 5. Overall verdict

**ready with small edits**

All actionable findings from r1 (F1, F2, F3, F4, F5, S1.F2, S1.F3, S1.F5, S1.F6, S1.F7) are resolved in code or data. Remaining items are intentional waivers (F6, F7, S1.F4, S1.F8) with stated reasons consistent with the P4 scope, and one correctly-deferred archive action (F8 / S1.F1) which this review unblocks. F10 is a nit-level spec narrative drift that should ride the archive commit but does not gate close. Run `tasktool close P4` + `tasktool archive-phase P4` next.
