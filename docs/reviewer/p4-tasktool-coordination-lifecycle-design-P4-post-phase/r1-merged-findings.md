# Merged findings for r1

## Primary

# Review — 2026-05-19-p4-tasktool-coordination-lifecycle-design.md (post-phase, round 1)

- Target: `docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md`
- Request: `docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

# Post-Phase Review — P4 Tasktool Coordination and Lifecycle Authority

- Target: `docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md`
- Kind: post-phase
- Verdict gate runs against tasklist + plan + implementation in this worktree.

## 1. Findings

**F1 — `set --status done` has no `--allow-ready-close` parity with `close`.** Severity: important
`tools/tasktool/commands.py:363-367` rejects a never-started slice during `cmd_set` with a hard error and instructs the user to run `tasktool close ... --allow-ready-close --reason`. No equivalent flag exists on the `set` parser (`tools/tasktool/cli.py`) nor on `cmd_set`. The spec lists `tasktool set P1.S1 --status done --reviewer-chain ...` as using "the same two-root reviewer-gate contract as `tasktool close`" (spec §Acceptance, line 192) and the project intent is parity. Today, legacy or scripted callers that use `set --status done` cannot proceed at all once a slice predates the guard — they must switch commands. This is exactly the post-slice S1.F2 finding from the P4.S2 reviewer chain and it was not resolved before close. Either add `--allow-ready-close --reason` to `set`, or amend the spec to declare `close` the sole legacy-bypass path.

**F2 — `validate` ordering of `started` not enforced.** Severity: minor
`tools/tasktool/validate.py:45-55` (`_check_dates`) was extended in commit `3f98a3d` to add calendar-shape validation for `started`, but it does not assert `created <= started` or `started <= closed`. The commit message ("validate started lifecycle dates") overstates the change. Both P4.S2 post-slice reviewers flagged this (F1 / S1.F1). An import or manual edit can therefore produce a row with nonsensical ordering and pass `--strict-format`. Add the ordering check (and a test) alongside the existing `closed >= created` rule.

**F3 — P4 phase tracker drift at archive time.** Severity: minor
`docs/tasklist.json:241-291`: P4 is `status: ready`, `started: null`, `closed: null` despite both slices being `done`. The spec (§Lifecycle Enforcement) notes phases are gated by slice completion and does not require `tasktool start P4`, so this is by design — but it means once `tasktool archive-phase P4` runs, the archive will carry forward a phase whose own lifecycle dates were never stamped. If "phase started" is meant to be a meaningful marker (acceptance criterion line 194 mentions phases accept `start`), consider either auto-stamping `started` on first slice start or documenting that phase rows skip `started` by policy.

**F4 — P4.S1 closed with `started: null` and no override audit note.** Severity: minor / informational
`docs/tasklist.json:251-266`. P4.S1 was closed by commit `57dae31` before `fd59f7f` introduced the guard, so the close was legal at the time. However, the resulting row now violates the invariant P4.S2 was designed to enforce. There is no `ready-close override` audit trail in `notes` because the override didn't exist when the close ran. This is expected by the spec ("Existing files load with `started: null`") but worth recording in the phase archive notes so future readers understand why a `done` slice in the P4 phase carries no `started` date.

**F5 — `unblock --resume` silently stamps `started`.** Severity: minor
`tools/tasktool/commands.py:436` calls `_start_item(qid, item, resume=True)` from `cmd_unblock`. This was flagged in the P4.S2 primary reviewer (F4) and not documented in the spec, the plan, or `skills/tasklist-discipline/SKILL.md`. The behavior is plausibly correct (unblocking a slice should resume in-progress and stamp a start), but the side effect is invisible to anyone reading docs. Add a one-line note where `unblock --resume` is described.

**F6 — `set --status in_progress` on a `done` item now errors.** Severity: nit
`commands.py:368-369` unconditionally routes `IN_PROGRESS` transitions through `_start_item`, which refuses done items with "already done". Previously this was a direct status assignment. The spec doesn't address re-opening done items either way, so this is an unannounced behavior change. Either codify in skills/spec (re-opens require a separate path) or restore the prior direct-assignment for the `done -> in_progress` edge.

**F7 — Plan file checkboxes remain unchecked.** Severity: nit
`docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md` — every `- [ ]` under Tasks 4-7 and the closeout sections is still unchecked even though the git history (`b810698`, `dc09679`, `fd59f7f`, `6abf660`, `3f98a3d`, `ed40767`, `c4deda7`) shows the work shipped and the tasklist confirms `P4.S2` is `done`. Either flip them to `- [x]` as part of the archive commit or document that `docs/tasklist.json` is the canonical status surface and plan boxes are advisory only. The post-slice S1.F4 finding flagged this and it was not addressed.

**F8 — No archive artifact for P4 yet.** Severity: informational
`docs/archived-tasks/` only contains `P2-...md`. The plan's P4.S2 closeout (lines 1314-1326) calls for `tasktool archive-phase P4 --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase` after this review concludes. The reviewer chain directory exists untracked (per `git status`). This review is the gate; once it returns ready / ready-with-small-edits, run the archive step. Not a finding to fix; just confirming the closeout sequence is intact.

**F9 — Acceptance coverage spot-checks.** No issue
Routing matrix tests, lock contention, reviewer-chain-outside-repo refusal, fail-closed authority discovery, `start`, `set --status in_progress` alias, slice close guard, and skill regression for all five skills are all present (`tools/tasktool/tests/test_worktree_authority.py`, `test_lifecycle_start.py`, `test_skill_tasktool_lifecycle_docs.py`). The S1.F3 sweep claim ("only 3 of 5 skills tested") was inaccurate at the time of writing — current test pins all five.

## 2. Open questions / assumptions

- Assumed `python -m pytest tools/tasktool/tests -v` is green at HEAD (`c4deda7`). I could not execute the suite from this reviewer pass. The plan's Final Verification (lines 1330-1343) requires it; please paste the result in the chain before archiving.
- Assumed `tasktool validate --strict-format` passes on the current tasklist. The only suspicious row is P4.S1 (`done` + `started: null`), which is allowed by the validator's current rules.
- Assumed `archive-phase P4` works against a phase whose own status is `ready` (no `tasktool start P4` was run). Worth confirming on a dry-run before archive.

## 3. Suggested document edits

- Spec §Acceptance: clarify F1 — either add `set --status done --allow-ready-close --reason` to the contract or strike the "same contract as close" wording for done-via-set.
- Spec §Lifecycle Enforcement and `skills/tasklist-discipline/SKILL.md`: add a sentence describing F5 (`unblock --resume` stamps `started`).
- Spec §Lifecycle Enforcement: state whether phase rows are expected to carry `started` (F3) or are exempt.
- Plan file: either flip Task 4-7 boxes to `[x]` as part of the archive commit, or add a closeout step "TASKLIST.json is canonical; plan checkboxes are not maintained post-implementation" (F7).
- Phase archive note (`tasktool archive-phase P4` will materialize `docs/archived-tasks/P4-*.md`): include a sentence explaining P4.S1's `started: null` per F4.

## 4. Verification gaps / commands to run

```sh
PYTHONPATH=tools python -m pytest tools/tasktool/tests -v
tools/tasktool/tasktool validate --strict-format
git status --short
```

Expected before archive:
- All tasktool tests pass (including `test_lifecycle_start.py`, `test_worktree_authority.py`, `test_skill_tasktool_lifecycle_docs.py`).
- `validate --strict-format` clean.
- Only `docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/` dirty (will be staged by `archive-phase`).

If F2 (validate ordering) is addressed, add a test asserting `started < created` and `closed < started` are rejected, then re-run `pytest tools/tasktool/tests/test_validate.py -v`.

## 5. Overall verdict

**ready with small edits**

The phase delivers the spec end-to-end: authoritative-checkout routing for every mutating command with a shared lock, the two-root reviewer-gate contract, fail-closed authority discovery, the `started` field across all four item types, `tasktool start` with `--resume`, the `set --status in_progress` alias, the slice-close guard with `--allow-ready-close --reason` audit-noted escape, and skill rewrites covered by regression tests for all five targeted skills. Two carry-overs from the P4.S2 post-slice review remain unaddressed — F1 (set/close parity for `--allow-ready-close`) and F2 (validator ordering) — and several minor polish items (F3-F7) should be resolved or documented before `tasktool archive-phase P4` runs. None of them block the close; F1 is the one most worth resolving in this round because it leaves an inconsistent CLI surface that future legacy migrations will hit.


## Sweep 1

# Review — 2026-05-19-p4-tasktool-coordination-lifecycle-design.md (post-phase, round 1)

- Target: `docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md`
- Request: `docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

# Post-Phase Review — P4 Tasktool Coordination and Lifecycle Authority

## 1. Findings

### S1.F1 — Phase P4 is not actually closed or archived  **Severity: blocking**
`docs/tasklist.json` shows P4 with `status: "ready"`, `closed: null`, `started: null`, `phase_reviewer_chain: null`, and no entry in `archived_phases`. Both slices are `done`, but the phase itself was never moved through `in_progress`/`done` and has not been archived. A post-phase gate cannot be closed in this state.
- Required: `tasktool start P4` (or accept ready-close on the phase via `archive-phase`), `tasktool close P4 --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase`, then `tasktool archive-phase P4`.
- Also: `phase_reviewer_chain` must be persisted to the post-phase chain dir (currently untracked).

### S1.F2 — P4.S1 was closed without a `started` marker  **Severity: important**
`P4.S1.started: null`, `status: "done"`. The spec/plan added the enforcement only in P4.S2, so this happened under the older rules — not a code defect, but it is a tracker artifact that violates the invariant the phase just introduced. Two options, pick one and apply: (a) backfill `started` for P4.S1 with a one-time normalisation, or (b) add an explicit note recording it as a grandfathered close. Leaving it as-is means the canonical tracker contains a slice that fails the rule the phase exists to enforce — bad dogfooding signal.

### S1.F3 — `set --status done` bypass asymmetry vs `close`  **Severity: important**
`commands.py:363-367` refuses `set --status done` on a never-started slice and tells the user to either `start` first or use `close --allow-ready-close --reason ...`. But `cmd_set` itself has no `--allow-ready-close/--reason` parameters (`commands.py:350`, `cli.py` set parser), so the suggested bypass is only reachable via `close`. Spec Acceptance: "`set P1.S1 --status done --reviewer-chain ...` uses the same two-root reviewer-gate contract as `close`" — the gate contract matches, but the ready-close override does not. Either: (a) document explicitly that `set --status done` has no bypass (and `close` is the only path) and update the error message to drop the misleading suggestion of a flag combination that doesn't exist on `set`, or (b) add matching `--allow-ready-close/--reason` to `set`. Option (a) is fine and cheaper.

### S1.F4 — This repo does not dogfood authoritative routing  **Severity: minor**
There is no `.tasktool/config.json` at the repo root, so the project still mutates in `local` mode. P4 implemented the capability; consider committing `.tasktool/config.json` (via `tasktool config init-authority --branch main`) as part of phase closeout so superstar itself runs under the new rules going forward. The spec said existing projects don't need to migrate "abruptly," so this isn't a blocker, but the phase ships without ever proving the routing works on its own tasklist.

### S1.F5 — Post-phase reviewer chain directory is untracked  **Severity: minor**
`docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/` shows in `git status` as untracked. Expected during the review round itself, but it must be committed before `archive-phase` so the archived note has a stable reviewer link.

### S1.F6 — Spec acceptance: validate + test evidence not produced in this review  **Severity: minor**
Acceptance criteria require `tasktool validate --strict-format` to pass and the test matrix (authority config, worktree routing, lock contention, lifecycle start, ready-close) to be green. The relevant test files exist (`test_authority_config.py`, `test_worktree_authority.py`, `test_lifecycle_start.py`, `test_skill_tasktool_lifecycle_docs.py`) but I could not execute them in this plan-mode review session. Closeout must run them and record the result. See section 4.

### S1.F7 — `cmd_start` accepts phases per spec but lifecycle for phases is not exercised by tasklist  **Severity: nit**
Spec says `start` accepts phases. The implementation accepts them, but `P4` itself was never started, and the close-time enforcement explicitly excludes phases. Confirm intent: either remove phase support from `start` (it is dead surface area) or actually require `tasktool start P4` at phase kickoff and document it in `phase-planning`/`writing-plans`. Right now both paths exist and neither is exercised.

### S1.F8 — Spec uses `planning_path` for the spec doc; `spec_path` left null  **Severity: nit**
P4 record has `planning_path: "docs/specs/.../p4-...-design.md"` but `spec_path: null`. The same pattern exists for P3, so this seems intentional (`planning_path` is the umbrella). Worth flagging because the field name `spec_path` reads like "where the spec lives" — a future reader will be confused.

## 2. Open Questions / Assumptions

- Is it acceptable to grandfather P4.S1's missing `started` marker, or do you want `tasktool` to gain a one-time backfill helper? (S1.F2)
- Should `set --status done` ever support `--allow-ready-close`, or is the asymmetry deliberate to force the explicit `close` path? (S1.F3)
- Does the closeout intend to flip this repo to authoritative routing in the same commit, or defer? (S1.F4)
- Should `tasktool start <phase>` be retained as a real lifecycle hook for phases, or pruned? (S1.F7)

## 3. Suggested Document Edits

- **Spec, Lifecycle Enforcement section:** add a sentence clarifying that the ready-close override is only exposed on `tasktool close`, not on `tasktool set --status done` (resolving S1.F3 toward option (a)).
- **Spec, Acceptance Criteria:** add an explicit criterion that the project running P4 commits `.tasktool/config.json` configured for `authoritative-checkout` as part of phase closeout, or note explicitly that superstar itself defers adoption.
- **Spec, Phase lifecycle:** clarify whether phases are expected to pass through `tasktool start` (currently ambiguous: `start` accepts them but `close` does not require it).

## 4. Verification Gaps / Commands To Run

Plan-mode prevented me from executing these. They must be run before declaring the phase ready:

```sh
tools/tasktool/tasktool validate --strict-format
python -m pytest tools/tasktool/tests -q
# Spot checks against acceptance criteria:
python -m pytest tools/tasktool/tests/test_authority_config.py \
                 tools/tasktool/tests/test_worktree_authority.py \
                 tools/tasktool/tests/test_lifecycle_start.py \
                 tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -v
```

Closeout actions (also currently undone):

```sh
git add docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/
# After verdict is "ready":
tools/tasktool/tasktool close P4 \
  --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase
tools/tasktool/tasktool archive-phase P4
```

## 5. Overall Verdict

**revise**

The implementation and skill changes look coherent and the slice-level work landed cleanly, but the phase itself has not been closed or archived in `docs/tasklist.json`, P4.S1 carries `started: null` after the very rule the phase enforces, and the `set` vs `close` bypass asymmetry produces a misleading error message. Address S1.F1–S1.F3 (and run the verification commands in §4) and a follow-up round should reach "ready" quickly.

