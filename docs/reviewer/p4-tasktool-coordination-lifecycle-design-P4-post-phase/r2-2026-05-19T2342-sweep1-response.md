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

**F1 (carry-over from r1.F1 / r1.S1.F3) — resolved.** Severity: minor (verify-only)
`tools/tasktool/cli.py:67,81` adds `--allow-ready-close` to both the `set` and `close` parsers, and the dispatch wires `allow_ready_close` and `reason` through `cmd_set` (line 220) and `cmd_close` (line 230). The set/close asymmetry is gone. No issue remaining; flagged so the closeout reviewer can confirm intent.

**F2 (carry-over from r1.F2) — resolved.** Severity: minor (verify-only)
`tools/tasktool/validate.py:54-59` now rejects both `started < created` and `closed < started`, applied uniformly across `Task`, `Slice`, `Phase`, and `CrossCutting` (`_check_dates` called from each item validator). Matches the resolution claim.

**F3 (carry-over from r1.F3 / r1.S1.F1) — phase started, but P4 close/archive still pending.** Severity: important
`docs/tasklist.json:288-290` now has `status: "in_progress"`, `started: "2026-05-19"` for P4, so the phase lifecycle marker is in place. However, the phase is **not yet closed** and there is no `phase_reviewer_chain` set. This round is the gate; once it returns `ready`/`ready with small edits`, closeout still must:
1. Commit the untracked `docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/` directory.
2. Record `phase_reviewer_chain` on P4 (or rely on `archive-phase --reviewer-chain` to do so).
3. Run `tasktool archive-phase P4 --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase`.

Not blocking this verdict — by construction these steps run after this review — but flagged so the closeout actor doesn't skip the chain-tracking and archive step.

**F4 — Phase-level reviewer chain field never assigned by `archive-phase` path needs confirming.** Severity: minor
`P4.phase_reviewer_chain` is `null` in `docs/tasklist.json:142,156,246`. Worth a dry-run of `archive-phase P4 --reviewer-chain ...` to confirm the field is populated on the in-memory phase before archive serialization, otherwise the archived row will lose the post-phase chain link. The P2 archived entry in `archived_phases` has no reviewer-chain pointer either (`docs/tasklist.json:2-9`), so historical precedent suggests the archive surface drops it — confirm whether that is intentional.

**F5 — `.tasktool/config.json` still absent from this repo (r1.S1.F4 waived).** Severity: minor / informational
R1 sweep flagged this as "phase ships without proving routing on its own tasklist." The resolution waived it, citing the non-goal "do not require all existing projects to adopt authoritative routing immediately." Consistent with spec §Non-Goals line 204. No action required; recording so the waiver is visible in the chain.

**F6 — Plan checkboxes still unchecked across Tasks 1–7 (r1.F7 waived).** Severity: nit
`docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md` still has every `- [ ]` unflipped despite all commits landing. Resolution waived on grounds that `docs/tasklist.json` is canonical. The waiver is defensible, but the plan file's own `> For agentic workers:` header instructs them to use checkbox tracking — that text now contradicts standing project policy. Either (a) flip the boxes in the archive commit, or (b) add a one-line note at the top of the plan that boxes are not maintained post-implementation. Not a blocker.

**F7 — Reviewer-chain artifacts are still untracked.** Severity: minor
`git status --short` shows three untracked R2 artifacts in the post-phase chain dir (`r2-...primary-request.md`, `r2-...primary-response.md`, `r2-...sweep1-request.md`). r1.S1.F5 noted this and r1-resolution marked it "fixed" by including the chain dir in the repair commit — but R2 artifacts have since accumulated and remain untracked, and the sweep1 *response* file is missing for R2 (only the request is present). Closeout must (a) ensure sweep1 ran and its response is materialized, and (b) `git add docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/` before `archive-phase` runs. If sweep1 was deliberately skipped this round, document that.

**F8 — Phase support on `tasktool start` is exercised; r1.S1.F7 confirmed resolved.** Severity: nit (verify-only)
`P4` carries `started: "2026-05-19"`, demonstrating the phase code path. No follow-up needed.

**F9 — Acceptance criteria full pass-check.** No issue
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

- `docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md` header: add one line acknowledging that checkbox state is not maintained after implementation (F6), or flip the boxes in the archive commit.
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

R1's blocking and important findings (set/close override parity, validator ordering, phase lifecycle marker, P4.S1 grandfathering note, `unblock --resume` documentation, chain commit) are resolved in code or accepted as documented waivers. The remaining items are closeout mechanics: stage the R2 chain artifacts (and the missing sweep1 response, if expected), run the verification commands, then `archive-phase P4` with the post-phase chain. The phase is functionally complete and the spec acceptance criteria are met. The only minor risks left in scope are F4 (confirm `archive-phase` persists `phase_reviewer_chain`) and F7 (the untracked R2 artifacts plus the missing sweep1 response), both of which are addressable in the archive commit itself.
