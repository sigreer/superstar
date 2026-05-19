# Merged findings for r2

## Primary

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


## Sweep 1

# Review — 2026-05-19-p4-tasktool-coordination-lifecycle-design.md (post-phase, round 2)

- Target: `docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md`
- Request: `docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r2-2026-05-19T2342-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

Based on reading the spec, plan, tasklist, R1 chain artifacts, and verifying R1 resolution claims against the actual code, here is the R2 post-phase review.

---

# Post-Phase Review — P4 Tasktool Coordination and Lifecycle Authority (round 2)

- Target: `docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md`
- Kind: post-phase
- Round: 2 (after `ff19dfb tasktool: resolve P4 post-phase lifecycle findings`)

## 1. Findings

**S1.F1 (carry-over from r1.F1 / r1.S1.F3) — resolved.** Severity: minor (verify-only)
`tools/tasktool/cli.py:67,81` adds `--allow-ready-close` to both the `set` and `close` parsers, and the dispatch wires `allow_ready_close` and `reason` through `cmd_set` (line 220) and `cmd_close` (line 230). The set/close asymmetry is gone. No issue remaining; flagged so the closeout reviewer can confirm intent.

**S1.F2 (carry-over from r1.F2) — resolved.** Severity: minor (verify-only)
`tools/tasktool/validate.py:54-59` now rejects both `started < created` and `closed < started`, applied uniformly across `Task`, `Slice`, `Phase`, and `CrossCutting` (`_check_dates` called from each item validator). Matches the resolution claim.

**S1.F3 (carry-over from r1.F3 / r1.S1.F1) — phase started, but P4 close/archive still pending.** Severity: important
`docs/tasklist.json:288-290` now has `status: "in_progress"`, `started: "2026-05-19"` for P4, so the phase lifecycle marker is in place. However, the phase is **not yet closed** and there is no `phase_reviewer_chain` set. This round is the gate; once it returns `ready`/`ready with small edits`, closeout still must:
1. Commit the untracked `docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/` directory.
2. Record `phase_reviewer_chain` on P4 (or rely on `archive-phase --reviewer-chain` to do so).
3. Run `tasktool archive-phase P4 --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase`.

Not blocking this verdict — by construction these steps run after this review — but flagged so the closeout actor doesn't skip the chain-tracking and archive step.

**S1.F4 — Phase-level reviewer chain field never assigned by `archive-phase` path needs confirming.** Severity: minor
`P4.phase_reviewer_chain` is `null` in `docs/tasklist.json:142,156,246`. Worth a dry-run of `archive-phase P4 --reviewer-chain ...` to confirm the field is populated on the in-memory phase before archive serialization, otherwise the archived row will lose the post-phase chain link. The P2 archived entry in `archived_phases` has no reviewer-chain pointer either (`docs/tasklist.json:2-9`), so historical precedent suggests the archive surface drops it — confirm whether that is intentional.

**S1.F5 — `.tasktool/config.json` still absent from this repo (r1.S1.F4 waived).** Severity: minor / informational
R1 sweep flagged this as "phase ships without proving routing on its own tasklist." The resolution waived it, citing the non-goal "do not require all existing projects to adopt authoritative routing immediately." Consistent with spec §Non-Goals line 204. No action required; recording so the waiver is visible in the chain.

**S1.F6 — Plan checkboxes still unchecked across Tasks 1–7 (r1.F7 waived).** Severity: nit
`docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md` still has every `- [ ]` unflipped despite all commits landing. Resolution waived on grounds that `docs/tasklist.json` is canonical. The waiver is defensible, but the plan file's own `> For agentic workers:` header instructs them to use checkbox tracking — that text now contradicts standing project policy. Either (a) flip the boxes in the archive commit, or (b) add a one-line note at the top of the plan that boxes are not maintained post-implementation. Not a blocker.

**S1.F7 — Reviewer-chain artifacts are still untracked.** Severity: minor
`git status --short` shows three untracked R2 artifacts in the post-phase chain dir (`r2-...primary-request.md`, `r2-...primary-response.md`, `r2-...sweep1-request.md`). r1.S1.F5 noted this and r1-resolution marked it "fixed" by including the chain dir in the repair commit — but R2 artifacts have since accumulated and remain untracked, and the sweep1 *response* file is missing for R2 (only the request is present). Closeout must (a) ensure sweep1 ran and its response is materialized, and (b) `git add docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/` before `archive-phase` runs. If sweep1 was deliberately skipped this round, document that.

**S1.F8 — Phase support on `tasktool start` is exercised; r1.S1.F7 confirmed resolved.** Severity: nit (verify-only)
`P4` carries `started: "2026-05-19"`, demonstrating the phase code path. No follow-up needed.

**S1.F9 — Acceptance criteria full pass-check.** No issue
Spot-checked all 12 acceptance criteria against the live tree:
- `--strict-format` validator now enforces date ordering ✓
- `--allow-ready-close` parity on both `set` and `close` ✓
- two-root reviewer-gate contract preserved ✓
- `started` field on all four item types ✓
- `start`, `--resume`, and the `set --status in_progress` alias ✓
- close guard with `--allow-ready-close --reason` audit note ✓
- skill regression tests pin all five updated skills ✓
- P4.S1 grandfathering note recorded ✓
I could not execute `pytest`/`validate --strict-format` from this session — see §4.

## 2. Open questions / assumptions

- **Sweep1 response** for R2 is absent (`r2-...sweep1-response.md` missing). Assumed sweep1 either failed or is still running; closeout must materialize or explicitly waive it.
- Assumed `python -m pytest tools/tasktool/tests -q` and `tools/tasktool/tasktool validate --strict-format` are green at `ff19dfb` (resolution claims `253 passed`). Could not execute in this review.
- Assumed `tasktool archive-phase P4 --reviewer-chain ...` works on a phase whose own status is `in_progress` (not `done`), and that it auto-flips P4 to `done` + populates `phase_reviewer_chain` + materializes `docs/archived-tasks/P4-*.md`. If it requires `tasktool close P4` first, the closeout sequence in the plan (lines 1314–1326) needs an explicit close step.

## 3. Suggested document edits

None blocking. Optional polish:

- `docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md` header: add one line acknowledging that checkbox state is not maintained after implementation (S1.F6), or flip the boxes in the archive commit.
- When `tasktool archive-phase P4` runs, ensure the generated `docs/archived-tasks/P4-*.md` carries forward P4.S1's grandfathering note so future readers see why a `done` slice in this archive carries `started: null` (r1.F4 follow-through).

## 4. Verification gaps / commands that should be run

Before the archive commit:

```sh
PYTHONPATH=tools python -m pytest tools/tasktool/tests -q
tools/tasktool/tasktool validate --strict-format
git status --short
```

Expected:

- All tasktool tests pass (resolution claims 253 passed).
- `validate --strict-format` clean (P4 row now has `started`; P4.S1 row still `started: null` and `status: "done"` — confirm the validator does not flag the grandfathered slice).
- After staging the R2 chain artifacts, only the post-phase chain dir should be dirty before `archive-phase` runs.

Then the closeout actions:

```sh
git add docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/
# Confirm whether `close` is required before `archive-phase`. If so:
tools/tasktool/tasktool close P4 \
  --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase
tools/tasktool/tasktool archive-phase P4 \
  --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase
```

Inspect the resulting `docs/archived-tasks/P4-*.md` and the updated `archived_phases` entry; verify `phase_reviewer_chain` was persisted.

## 5. Overall verdict

**ready with small edits**

R1's blocking and important findings (set/close override parity, validator ordering, phase lifecycle marker, P4.S1 grandfathering note, `unblock --resume` documentation, chain commit) are resolved in code or accepted as documented waivers. The remaining items are closeout mechanics: stage the R2 chain artifacts (and the missing sweep1 response, if expected), run the verification commands, then `archive-phase P4` with the post-phase chain. The phase is functionally complete and the spec acceptance criteria are met. The only minor risks left in scope are S1.F4 (confirm `archive-phase` persists `phase_reviewer_chain`) and S1.F7 (the untracked R2 artifacts plus the missing sweep1 response), both of which are addressable in the archive commit itself.

