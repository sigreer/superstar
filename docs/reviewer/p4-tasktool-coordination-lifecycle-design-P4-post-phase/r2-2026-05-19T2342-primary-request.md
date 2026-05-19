<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 2 of p4-tasktool-coordination-lifecycle-design-P4-post-phase.

In incremental mode:
- Verify whether prior findings are resolved per the resolution report below.
- Reuse the existing finding IDs (F1, F2, …). If a prior finding is resolved,
  mark it RESOLVED in your findings list with its original ID. If still
  unresolved, keep its ID.
- Only introduce new finding IDs for genuine regressions caused by the fix, or
  blocking issues clearly missed in earlier rounds. Do not reopen broad review
  unless prior fixes changed broad architecture.

## Review chain summary

| round | verdict | findings | blocking |
|---|---|---|---|
| 1 | revise | 9 | 0 |

## Prior-round findings

Source: merged findings from r1 (authoritative)

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



## Resolution report for prior round

# Resolution for r1

Round 1 returned a primary verdict of `ready with small edits` and a sweep verdict of `revise`. This repair addresses the actionable lifecycle findings and records explicit waivers or deferrals for closeout-only items.

Repair commit: this commit (`tasktool: resolve P4 post-phase lifecycle findings`)

## F1
Status: fixed
Evidence:
- Files: `tools/tasktool/cli.py`, `tools/tasktool/commands.py`, `tools/tasktool/tests/test_commands.py`, `tools/tasktool/tests/test_lifecycle_start.py`.
- `tasktool set --status done` now accepts `--allow-ready-close` and `--reason`, applies the same ready-close audit note as `tasktool close`, and still refuses never-started slices when the override or reason is missing.
- Verification: `python -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_lifecycle_start.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` -> `110 passed`.

## F2
Status: fixed
Evidence:
- Files: `tools/tasktool/validate.py`, `tools/tasktool/tests/test_validate.py`.
- Validator now rejects `started < created` and `closed < started` after validating date shape and calendar validity.
- Verification: same targeted pytest run -> `110 passed`.

## F3
Status: fixed
Evidence:
- Files: `docs/tasklist.json`.
- Ran `tools/tasktool/tasktool start P4`; P4 now has `status: in_progress` and `started: 2026-05-19`, so the phase lifecycle marker exists before the next close/archive attempt.

## F4
Status: fixed
Evidence:
- Files: `docs/tasklist.json`.
- Added a P4.S1 note through tasktool: "P4.S1 is grandfathered under pre-P4.S2 lifecycle rules: it was closed before the started-field close guard and ready-close override audit note existed, so started remains null intentionally."

## F5
Status: fixed
Evidence:
- Files: `skills/tasklist-discipline/SKILL.md`, `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`.
- The skill now documents that `tasktool unblock <slice-id> --resume` resumes through the same lifecycle path and stamps `started` when needed.
- Verification: same targeted pytest run -> `110 passed`.

## F6
Status: waived
Evidence:
- The current behavior is intentional lifecycle tightening: `set --status in_progress` routes through `_start_item`, and `_start_item` refuses already-done rows.
- Reopening done work remains outside P4 scope; no separate reopen command or policy was specified in the P4 acceptance criteria.

## F7
Status: waived
Evidence:
- `docs/tasklist.json` is the canonical status surface for this repo; P4.S2 is already `done` there and the plan checkboxes are advisory implementation scaffolding.
- No code or validation behavior depends on plan checkbox state.

## F8
Status: deferred
Evidence:
- Archive remains gated on the next post-phase review round. The current chain round has merged verdict `revise`, so closing or archiving P4 now would require bypassing the review gate.
- This repair starts P4 and writes the resolution artifact required for the next round; archive should run after the post-phase chain returns `ready` or `ready with small edits`.

## F9
Status: waived
Evidence:
- Primary reviewer reported no issue. Existing acceptance coverage remains in the tasktool test suite, and the final verification set is rerun for this repair before commit.

## S1.F1
Status: deferred
Evidence:
- P4 has now been started via tasktool, addressing the unstamped phase lifecycle marker.
- P4 close/archive is deferred until the post-phase reviewer chain no longer has merged verdict `revise`; bypassing the gate here would weaken the workflow P4 is validating.

## S1.F2
Status: fixed
Evidence:
- Same as F4. P4.S1 now has an explicit grandfathering note in `docs/tasklist.json`.

## S1.F3
Status: fixed
Evidence:
- Same as F1. `set --status done` now has ready-close override parity with `close`.

## S1.F4
Status: waived
Evidence:
- The P4 spec explicitly did not require abrupt migration of existing projects to authoritative mode.
- Adding `.tasktool/config.json` would be a policy adoption step for the repo, not a repair for the lifecycle bugs found in this round.

## S1.F5
Status: fixed
Evidence:
- The post-phase reviewer chain directory and this `r1-resolution.md` are included in the repair commit.

## S1.F6
Status: fixed
Evidence:
- Verification commands are run and recorded before the repair commit.

## S1.F7
Status: fixed
Evidence:
- Same as F3. P4 now exercises `tasktool start P4` and carries a phase-level `started` marker.

## S1.F8
Status: waived
Evidence:
- The reviewer identified an existing field-naming ambiguity (`planning_path` holds the P4 design doc while `spec_path` is null). This is consistent with existing P3/P4 tasklist usage and is not part of the P4 lifecycle repair scope.

## Verification

Targeted red-green verification:
- Initial targeted run failed for the new tests: validator ordering was not enforced and `set` did not accept `--allow-ready-close` / `--reason`.
- After implementation: `python -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_lifecycle_start.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` -> `110 passed`.

Final verification:
- `tools/tasktool/tasktool validate --strict-format` -> `ok`
- `python -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_lifecycle_start.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_cli_integration.py tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -v` -> `132 passed in 11.21s`
- `python -m pytest tools/tasktool/tests -q` -> `253 passed in 22.22s`


## Changes since prior round

Worktree status: clean

### git diff base..HEAD

diff --git a/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/chain.json b/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/chain.json
new file mode 100644
index 0000000..04370d0
--- /dev/null
+++ b/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/chain.json
@@ -0,0 +1,76 @@
+{
+  "schema_version": 1,
+  "chain": "p4-tasktool-coordination-lifecycle-design-P4-post-phase",
+  "kind": "post-phase",
+  "target": "docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md",
+  "work_id": "P4",
+  "legacy_migrated": false,
+  "rounds": [
+    {
+      "round": 1,
+      "reviewers": [
+        {
+          "role": "primary",
+          "sweep_group": null,
+          "parent_round": 1,
+          "request": "r1-2026-05-19T2328-primary-request.md",
+          "response": "r1-2026-05-19T2328-primary-response.md",
+          "verdict": "ready with small edits",
+          "verdict_valid": true,
+          "returncode": 0,
+          "status": "ok",
+          "provider": "claude",
+          "caller_provider": "codex",
+          "sandbox": {
+            "repo_root": "/home/simon/Dev/sigreer/skills/superstar/.worktrees/p4-s2-lifecycle",
+            "scratch_dir": "/tmp/superstar-reviewer-p4-tasktool-coordination-lifecycle-design-P4-post-phase-r1-primary-8xt9zbk_",
+            "response_dir": "docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/.reviewer-output/r1-primary",
+            "mode": "plan-read-only"
+          }
+        },
+        {
+          "role": "sweep",
+          "sweep_group": 1,
+          "parent_round": 1,
+          "request": "r1-2026-05-19T2328-sweep1-request.md",
+          "response": "r1-2026-05-19T2328-sweep1-response.md",
+          "verdict": "revise",
+          "verdict_valid": true,
+          "returncode": 0,
+          "status": "ok",
+          "provider": "claude",
+          "caller_provider": "codex",
+          "sandbox": {
+            "repo_root": "/home/simon/Dev/sigreer/skills/superstar/.worktrees/p4-s2-lifecycle",
+            "scratch_dir": "/tmp/superstar-reviewer-p4-tasktool-coordination-lifecycle-design-P4-post-phase-r1-sweep1-11bs924r",
+            "response_dir": "docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/.reviewer-output/r1-sweep1",
+            "mode": "plan-read-only"
+          }
+        }
+      ],
+      "status": "ok",
+      "returncode": 0,
+      "merged_verdict": "revise",
+      "merged_findings": "r1-merged-findings.md",
+      "request": "r1-2026-05-19T2328-primary-request.md",
+      "response": "r1-2026-05-19T2328-primary-response.md",
+      "resolution": null,
+      "resolution_parse_status": null,
+      "resolution_waiver": false,
+      "head_sha_at_request": "c4deda7b70104772306e05847161d6b73f379a2a",
+      "head_sha_after_round": "c4deda7b70104772306e05847161d6b73f379a2a",
+      "worktree_dirty_at_request": true,
+      "verdict": "ready with small edits",
+      "verdict_valid": true,
+      "findings_count": 9,
+      "blocking_findings_count": 0,
+      "base_ref": null,
+      "base_ref_source": null,
+      "diff_included": false
+    }
+  ],
+  "sweep_checkpoints": {
+    "first-round": "completed",
+    "final-ready": "pending"
+  }
+}
diff --git a/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-primary-request.md b/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-primary-request.md
new file mode 100644
index 0000000..1b7a8c8
--- /dev/null
+++ b/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-primary-request.md
@@ -0,0 +1,668 @@
+<!-- superstar-prompt:start -->
+You are acting as an independent senior engineering reviewer.
+
+Review stance:
+- Lead with findings, ordered by severity.
+- Focus on correctness, consistency, implementation risk, missing acceptance
+  gates, vague handoffs, ungrounded assumptions, unverified claims, and drift
+  from the codebase.
+- Give exact file/line references when possible.
+- If the document is sound, say that clearly and list residual risks.
+- Keep the review actionable. Avoid broad rewrites unless the current structure
+  creates concrete risk.
+
+Repository root:
+/home/simon/Dev/sigreer/skills/superstar/.worktrees/p4-s2-lifecycle
+
+Target kind:
+post-phase
+
+Review mode:
+Post-phase review. Treat this as a closeout gate for a whole
+phase. Compare the implementation, archive/TASKLIST updates, and verification
+evidence against the phase spec/plan. Prioritize: unresolved acceptance
+criteria, stale docs, missing archive notes, cross-cutting tracker drift,
+deferred gates without justification, and regressions outside the phase scope.
+
+Target document:
+docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md
+
+Additional context files:
+- docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md
+- docs/tasklist.json
+
+Review output contract:
+1. Findings
+   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
+     stable if this review is iterated in subsequent rounds.
+   - Mark severity inline: `Severity: blocking | important | minor | nit`.
+2. Open questions / assumptions
+3. Suggested document edits
+4. Verification gaps / commands that should be run, if any
+5. Overall verdict: one of "ready", "ready with small edits", or "revise"
+
+Read the files from disk. Do not rely only on the snippets in this prompt.
+
+
+## Target Preview
+
+### docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md
+
+    1	# P4 — Tasktool Coordination and Lifecycle Authority
+    2	
+    3	**Status:** proposed
+    4	**Date:** 2026-05-19
+    5	**TASKLIST entry:** `P4` in `docs/tasklist.json`
+    6	
+    7	## Objective
+    8	
+    9	Make `tasktool` the enforced authority for two workflow rules that are currently left to agent discipline:
+   10	
+   11	1. Parallel implementation worktrees must not own `docs/tasklist.json` mutations.
+   12	2. Active slices and tasks must pass through `in_progress` instead of jumping from `ready` to `done`.
+   13	
+   14	The intended outcome is that agents can keep using normal `tasktool` commands from whatever checkout they are working in, but the tool decides where writes land and which lifecycle transitions are valid.
+   15	
+   16	## Problem
+   17	
+   18	`docs/tasklist.json` is the single source of truth, but linked implementation worktrees currently mutate their local copy. When those branches merge back to `main`, tasklist updates from multiple agents collide as byte-level JSON diffs. This is predictable because each worktree was forked from a stale snapshot of the tracker.
+   19	
+   20	The same workflow has a status-quality issue: agents rarely mark slices or tasks `in_progress`. Rows remain `ready` until they are closed, which makes `tasktool list --open`, `phase-status`, and human progress scans much less useful.
+   21	
+   22	These are not independent usability nits. They expose the same architectural gap: `tasktool` has the canonical data model, but it does not yet enforce the coordinator lifecycle strongly enough.
+   23	
+   24	## Design Summary
+   25	
+   26	`tasktool` gains two linked capabilities:
+   27	
+   28	- **Authoritative checkout routing.** Mutating commands invoked from implementation worktrees are applied to a configured authoritative checkout, normally the project `main` checkout. Every authoritative-mode write uses the same lock, including commands invoked directly from the authoritative checkout. Worker worktrees treat `docs/tasklist.json` as a read-only mirror.
+   29	- **Lifecycle start enforcement.** `tasktool start <id>` becomes the normal way to begin work. Slice close is allowed only after a slice has been observed `in_progress`, unless an explicit bypass is supplied and recorded.
+   30	
+   31	The skills are updated to describe the new command surface, but correctness does not depend on prose. The CLI enforces the rules.
+   32	
+   33	## Configuration
+   34	
+   35	Add a tracked project config file:
+   36	
+   37	```json
+   38	{
+   39	  "schema_version": 1,
+   40	  "tasklist": {
+   41	    "mutation_mode": "authoritative-checkout",
+   42	    "authoritative_branch": "main"
+   43	  }
+   44	}
+   45	```
+   46	
+   47	The default path is `.tasktool/config.json`. This file is intended to be committed because it contains project policy only, not machine-local absolute paths. If no config exists, current behavior remains unchanged so existing projects do not break abruptly.
+   48	
+   49	Field semantics:
+   50	
+   51	- `mutation_mode`
+   52	  - `local`: existing behavior; mutate the current checkout.
+   53	  - `authoritative-checkout`: route mutating commands from linked worktrees to `authoritative_root`.
+   54	- `authoritative_branch`: branch the authoritative checkout must be on when accepting writes.
+   55	
+   56	Machine-local root discovery:
+   57	
+   58	1. If `TASKTOOL_AUTHORITY_ROOT` is set, use it.
+   59	2. Otherwise inspect `git worktree list --porcelain` and find the checkout whose branch is `authoritative_branch`.
+   60	3. If exactly one checkout matches, use it.
+   61	4. If none or more than one match, fail closed and print the exact `TASKTOOL_AUTHORITY_ROOT=/path/to/checkout` override to use.
+   62	
+   63	`tasktool config init-authority --branch main` writes or updates `.tasktool/config.json`. It does not write absolute paths. A separate untracked `.tasktool/local.json` may be added later, but P4 should not require it.
+   64	
+   65	## Mutating Commands
+   66	
+   67	The routing layer applies to all commands that write `docs/tasklist.json`:
+   68	
+   69	- `init`
+   70	- `create phase|slice|task|cross`
+   71	- `set`
+   72	- `start`
+   73	- `close`
+   74	- `block`
+   75	- `unblock`
+   76	- `deps`
+   77	- `ratify`
+   78	- `planning-path`
+   79	- `note`
+   80	- `ref`
+   81	- `title`
+   82	- `archive-phase`
+   83	- `import`
+   84	- `validate --normalise`
+   85	
+   86	Read commands keep using the current checkout by default, but they should warn when authoritative routing is configured and the current worktree copy is older than the authoritative copy. A follow-up may add `--source authoritative|local`; P4 does not need it.
+   87	
+   88	## Routing Rules
+   89	
+   90	For every mutating command:
+   91	
+   92	1. Discover the current repository root and git common directory.
+   93	2. Load `.tasktool/config.json` if present.
+   94	3. If `mutation_mode` is absent or `local`, mutate the current checkout.
+   95	4. Resolve `authoritative_root` via the machine-local discovery rules.
+   96	5. Acquire an exclusive lock under the common git directory before loading tasklist data.
+   97	6. Validate that `authoritative_root` exists, is a git checkout for the same repository, is on `authoritative_branch`, and has no unresolved merge.
+   98	7. Validate that `authoritative_root/docs/tasklist.json` is not dirty in a way that cannot be attributed to tasktool's own current command.
+   99	8. Load and mutate `authoritative_root/docs/tasklist.json`, even if the invocation already came from that checkout.
+  100	9. Save canonical JSON and best-effort stage the authoritative path.
+  101	10. Print a concise routing message only when the invocation root differs from the authoritative root.
+  102	
+  103	The implementation should centralize this routing in one module so command functions do not each grow git-worktree logic.
+  104	
+  105	The lock is mandatory for every authoritative-mode mutation. Direct `main` checkout invocations and worker-routed invocations contend on the same lock, preventing interleaved read-modify-write cycles.
+  106	
+  107	## Two-Root Command Contract
+  108	
+  109	Commands in authoritative mode have two roots:
+  110	
+  111	- `invocation_root`: the checkout where the user or agent ran the command.
+  112	- `write_root`: the authoritative checkout whose `docs/tasklist.json` is mutated.
+  113	
+  114	User-supplied file paths and reviewer-chain discovery are interpreted relative to `invocation_root`. Tasklist load/save/stage happens in `write_root`. This applies to `close` and to `set --status done`, because both routes can invoke review-gate checks.
+  115	
+  116	Explicit reviewer-chain paths may be absolute or relative, but they must resolve inside `invocation_root`. Paths outside the repository are refused. The value recorded into tasklist is always repo-relative from `invocation_root`.
+  117	
+  118	## Reviewer Chains From Worktrees
+  119	
+  120	`tasktool close <slice-id>` and `tasktool set <id> --status done` must preserve review-gate semantics when invoked from an implementation worktree.
+  121	
+  122	The gate should evaluate reviewer artifacts relative to the invocation checkout because that is where post-slice review was run. The resulting `reviewer_chain` recorded into the authoritative tasklist remains a repo-relative path, for example:
+  123	
+  124	```text
+  125	docs/reviewer/p11-s4c-nav-footer-P11-S4c-post-slice
+  126	```
+  127	
+  128	If the reviewer chain path is outside the repository, the command refuses it. If the same repo-relative reviewer chain does not exist in the authoritative checkout yet, close still records the relative path; merge-back will bring the artifacts over. The JSON record must not depend on absolute worktree paths.
+  129	
+  130	## Lifecycle Enforcement
+  131	
+  132	Add:
+  133	
+  134	```sh
+  135	tasktool start <id>
+  136	```
+  137	
+  138	Behavior:
+  139	
+  140	- Accepts phases, slices, tasks, and cross-cutting items.
+  141	- Resolves short IDs exactly like `set`.
+  142	- Refuses `done` items.
+  143	- Refuses `blocked` slices unless `--resume` is supplied, in which case it clears `blocked_on` and sets `in_progress`.
+  144	- Sets `status: in_progress`.
+  145	- Records a machine-readable lifecycle marker that proves the item was started before close.
+  146	
+  147	The marker should be explicit rather than inferred from current status, because a row may later move from `in_progress` to `blocked` and back. Add `started: YYYY-MM-DD | null` to phase, slice, task, and cross-cutting records. Existing files load with `started: null`.
+  148	
+  149	`tasktool set <id> --status in_progress` becomes a compatibility alias for `tasktool start <id>`. It sets `started` using the same rules and notifications. This keeps older skill prose or human muscle memory from producing a visible `in_progress` state that later fails close because no start marker exists.
+  150	
+  151	Close behavior:
+  152	
+  153	- Closing tasks and cross-cutting items from `ready` remains allowed for now, because they are often small bookkeeping rows.
+  154	- Closing slices from `ready` is refused unless `--allow-ready-close` is supplied.
+  155	- `--allow-ready-close` appends an audit note with timestamp and reason.
+  156	- Closing phases from `ready` remains allowed only through `archive-phase`; phase lifecycle is already gated by completed slices.
+  157	
+  158	This targets the recurring operational pain without making every tiny task transition noisy.
+  159	
+  160	## Skill Updates
+  161	
+  162	Update these skills:
+  163	
+  164	- `tasklist-discipline`: explain authoritative routing, `tasktool start`, and the `ready -> done` slice close guard.
+  165	- `using-git-worktrees`: say worktrees may invoke tasktool mutations, but mutations route to the authoritative checkout when configured.
+  166	- `subagent-driven-development`: after selecting a ready slice and before dispatching implementation subagents, run `tasktool start <slice-id>`.
+  167	- `executing-plans`: replace the current prose-only "Mark as in_progress" step with `tasktool start <slice-id>`.
+  168	- `writing-plans`: plans for slice execution should include `tasktool start <slice-id>` as the first execution step when `docs/tasklist.json` exists.
+  169	
+  170	The status problem is partly skill markdown today, especially in `subagent-driven-development`, but the P4 fix should not rely on skill wording alone.
+  171	
+  172	## Slices
+  173	
+  174	### P4.S1 — Authoritative Tasklist Mutations
+  175	
+  176	Add config loading, git worktree detection, lock acquisition, routing helpers, and command integration for all tasklist-writing commands. Worker worktrees stop committing `docs/tasklist.json` deltas.
+  177	
+  178	### P4.S2 — Lifecycle Status Enforcement
+  179	
+  180	Add `started` fields, `tasktool start`, close-time enforcement for slices, and skill updates that make lifecycle transitions visible and routine.
+  181	
+  182	Depends on: `P4.S1`, because lifecycle commands should use the same routed-write path.
+  183	
+  184	## Acceptance Criteria
+  185	
+  186	- `tasktool validate --strict-format` passes on existing tasklist files.
+  187	- Tasktool unit and CLI tests cover local mode, authoritative mode, linked worktree routing, lock contention, unsafe authoritative checkout states, and reviewer-chain recording from a worker worktree.
+  188	- A simulated worker worktree can run `tasktool close P1.S1 --reviewer-chain ...` and leave the worker copy of `docs/tasklist.json` unchanged while updating the authoritative checkout.
+  189	- Direct authoritative-checkout writes and worker-routed writes contend on the same tasktool lock.
+  190	- `tasktool config init-authority --branch main` creates tracked project policy without absolute paths.
+  191	- A worker worktree with authoritative routing configured but no discoverable authoritative root fails closed instead of falling back to local mutation.
+  192	- `tasktool set P1.S1 --status done --reviewer-chain ...` uses the same two-root reviewer-gate contract as `tasktool close`.
+  193	- Explicit reviewer-chain paths outside the invocation repository are refused.
+  194	- `tasktool start P1.S1` sets `status: in_progress` and `started`.
+  195	- `tasktool set P1.S1 --status in_progress` sets the same `started` marker as `tasktool start`.
+  196	- `tasktool close P1.S1` refuses a never-started slice unless `--allow-ready-close --reason "..."` is supplied.
+  197	- Skills describe the enforced workflow without asking agents to hand-edit tasklist state.
+  198	
+  199	## Non-Goals
+  200	
+  201	- Do not build a semantic `tasktool merge` command in this phase. It is a fallback for a worse invariant.
+  202	- Do not move task state outside the repository.
+  203	- Do not add networked locking or a daemon.
+  204	- Do not require all existing projects to adopt authoritative routing immediately.
+  205	- Do not force every task row through `in_progress` before close in this phase.
+
+## Context Previews
+
+### docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md
+
+    1	# P4 — Tasktool Coordination and Lifecycle Authority Implementation Plan
+    2	
+    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
+    4	
+    5	**Goal:** Make tasklist mutations safe under parallel worktrees and make active work visibly enter `in_progress` before slice close.
+    6	
+    7	**Architecture:** Add a tasktool runtime layer that resolves whether a write should mutate locally or through an authoritative checkout, guarded by a lock in the shared git directory for every authoritative-mode write. Then add explicit lifecycle state (`started`) and `tasktool start`, with `set --status in_progress` as a compatibility alias and close-time enforcement for slices. Skills become instructions for the enforced command path, not the only enforcement mechanism.
+    8	
+    9	**Tech Stack:** Python 3 stdlib (`tasktool`), Git CLI, JSON, markdown skills.
+   10	
+   11	**TASKLIST entry:** `P4` in `docs/tasklist.json`; slices `P4.S1` and `P4.S2`.
+   12	
+   13	---
+   14	
+   15	## Scheduling Contract
+   16	
+   17	`tasktool schedule P4` currently reports:
+   18	
+   19	```text
+   20	P4.S1  [ready/ratified]  group=coordination  ready  deps=-  waiting_on=-  Authoritative tasklist mutations
+   21	P4.S2  [ready/ratified]  group=lifecycle  waiting  deps=P4.S1  waiting_on=P4.S1  Lifecycle status enforcement
+   22	```
+   23	
+   24	Execute `P4.S1` first. Do not start `P4.S2` until `P4.S1` has passed its post-slice review and `tasktool close P4.S1` succeeds.
+   25	
+   26	## File Map
+   27	
+   28	| Action | Path | Responsibility |
+   29	|--------|------|----------------|
+   30	| Create | `tools/tasktool/config.py` | Load/save `.tasktool/config.json`; define config dataclasses and validation. |
+   31	| Create | `tools/tasktool/worktree.py` | Git repository/worktree discovery, authoritative checkout validation, lock acquisition. |
+   32	| Modify | `tools/tasktool/commands.py` | Route mutating commands through a write context; add `cmd_config_init_authority`; later add `cmd_start` and lifecycle enforcement. |
+   33	| Modify | `tools/tasktool/cli.py` | Add `config init-authority`, `start`, and `close --allow-ready-close --reason`. |
+   34	| Modify | `tools/tasktool/model.py` | Add `started` fields to Phase/Slice/Task/CrossCutting in P4.S2. |
+   35	| Modify | `tools/tasktool/serialize.py` | Backward-compatible load/save for `started`. |
+   36	| Modify | `tools/tasktool/schema_gen.py` | Include `started` in generated schema. |
+   37	| Modify | `tools/tasktool/render.py` and `tools/tasktool/brief.py` | Surface `started` where useful. |
+   38	| Create | `tools/tasktool/tests/test_authority_config.py` | Config parsing and validation tests. |
+   39	| Create | `tools/tasktool/tests/test_worktree_authority.py` | Git worktree routing, unsafe-state, and locking tests. |
+   40	| Create | `tools/tasktool/tests/test_lifecycle_start.py` | `start`, `started`, and ready-close enforcement tests. |
+   41	| Modify | `skills/tasklist-discipline/SKILL.md` | Document authoritative routing and lifecycle commands. |
+   42	| Modify | `skills/using-git-worktrees/SKILL.md` | Explain routed tasktool writes from implementation worktrees. |
+   43	| Modify | `skills/subagent-driven-development/SKILL.md` | Require `tasktool start <slice-id>` before dispatch. |
+   44	| Modify | `skills/executing-plans/SKILL.md` | Replace prose-only in-progress step with `tasktool start`. |
+   45	| Modify | `skills/writing-plans/SKILL.md` | Plans must include a concrete `tasktool start` execution step. |
+   46	
+   47	## P4.S1 — Authoritative Tasklist Mutations
+   48	
+   49	### Task 1: Config Model and CLI Initializer
+   50	
+   51	**Files:**
+   52	- Create: `tools/tasktool/config.py`
+   53	- Modify: `tools/tasktool/cli.py`
+   54	- Modify: `tools/tasktool/commands.py`
+   55	- Test: `tools/tasktool/tests/test_authority_config.py`
+   56	
+   57	- [ ] **Step 1: Write failing config tests**
+   58	
+   59	Create `tools/tasktool/tests/test_authority_config.py`:
+   60	
+   61	```python
+   62	import json
+   63	from pathlib import Path
+   64	
+   65	from tasktool.config import (
+   66	    DEFAULT_CONFIG_REL,
+   67	    TasktoolConfig,
+   68	    TasklistConfig,
+   69	    load_config,
+   70	    save_config,
+   71	)
+   72	
+   73	def test_missing_config_defaults_to_local(tmp_path):
+   74	    cfg = load_config(tmp_path)
+   75	    assert cfg.tasklist.mutation_mode == "local"
+   76	
+   77	def test_round_trip_authoritative_config(tmp_path):
+   78	    cfg = TasktoolConfig(
+   79	        tasklist=TasklistConfig(
+   80	            mutation_mode="authoritative-checkout",
+   81	            authoritative_branch="main",
+   82	        )
+   83	    )
+   84	    save_config(tmp_path, cfg)
+   85	    raw = json.loads((tmp_path / DEFAULT_CONFIG_REL).read_text())
+   86	    assert raw["schema_version"] == 1
+   87	    assert raw["tasklist"]["mutation_mode"] == "authoritative-checkout"
+   88	    assert "authoritative_root" not in raw["tasklist"]
+   89	    assert load_config(tmp_path) == cfg
+   90	
+   91	def test_invalid_mode_raises(tmp_path):
+   92	    path = tmp_path / DEFAULT_CONFIG_REL
+   93	    path.parent.mkdir()
+   94	    path.write_text('{"schema_version":1,"tasklist":{"mutation_mode":"bad"}}')
+   95	    try:
+   96	        load_config(tmp_path)
+   97	    except ValueError as exc:
+   98	        assert "unknown mutation_mode" in str(exc)
+   99	    else:
+  100	        raise AssertionError("expected ValueError")
+  101	```
+  102	
+  103	Run: `python -m pytest tools/tasktool/tests/test_authority_config.py -v`
+  104	Expected: FAIL because `tasktool.config` does not exist.
+  105	
+  106	- [ ] **Step 2: Implement config module**
+  107	
+  108	Create `tools/tasktool/config.py`:
+  109	
+  110	```python
+  111	from __future__ import annotations
+  112	
+  113	import json
+  114	from dataclasses import dataclass, field
+  115	from pathlib import Path
+  116	
+  117	DEFAULT_CONFIG_REL = Path(".tasktool/config.json")
+  118	VALID_MUTATION_MODES = {"local", "authoritative-checkout"}
+  119	
+  120	@dataclass(frozen=True)
+  121	class TasklistConfig:
+  122	    mutation_mode: str = "local"
+  123	    authoritative_branch: str = "main"
+  124	
+  125	@dataclass(frozen=True)
+  126	class TasktoolConfig:
+  127	    schema_version: int = 1
+  128	    tasklist: TasklistConfig = field(default_factory=TasklistConfig)
+  129	
+  130	def _parse_tasklist(raw: dict) -> TasklistConfig:
+  131	    mode = raw.get("mutation_mode", "local")
+  132	    if mode not in VALID_MUTATION_MODES:
+  133	        raise ValueError(f"unknown mutation_mode: {mode}")
+  134	    return TasklistConfig(
+  135	        mutation_mode=mode,
+  136	        authoritative_branch=raw.get("authoritative_branch", "main"),
+  137	    )
+  138	
+  139	def load_config(repo_root: Path) -> TasktoolConfig:
+  140	    path = repo_root / DEFAULT_CONFIG_REL
+  141	    if not path.exists():
+  142	        return TasktoolConfig()
+  143	    raw = json.loads(path.read_text(encoding="utf-8"))
+  144	    if raw.get("schema_version", 1) != 1:
+  145	        raise ValueError(f"unsupported tasktool config schema_version: {raw.get('schema_version')}")
+  146	    return TasktoolConfig(
+  147	        schema_version=1,
+  148	        tasklist=_parse_tasklist(raw.get("tasklist", {})),
+  149	    )
+  150	
+  151	def save_config(repo_root: Path, cfg: TasktoolConfig) -> None:
+  152	    path = repo_root / DEFAULT_CONFIG_REL
+  153	    path.parent.mkdir(parents=True, exist_ok=True)
+  154	    body = {
+  155	        "schema_version": cfg.schema_version,
+  156	        "tasklist": {
+  157	            "mutation_mode": cfg.tasklist.mutation_mode,
+  158	            "authoritative_branch": cfg.tasklist.authoritative_branch,
+  159	        },
+  160	    }
+  161	    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
+  162	```
+  163	
+  164	Run: `python -m pytest tools/tasktool/tests/test_authority_config.py -v`
+  165	Expected: PASS.
+  166	
+  167	- [ ] **Step 3: Add CLI initializer test**
+  168	
+  169	Append to `tools/tasktool/tests/test_cli_integration.py`:
+  170	
+  171	```python
+  172	def test_config_init_authority_writes_project_config(tmp_path):
+  173	    r = run_cli(
+  174	        "config", "init-authority",
+  175	        "--branch", "main",
+  176	        cwd=tmp_path,
+  177	    )
+  178	    assert r.returncode == 0, r.stdout + r.stderr
+  179	    data = json.loads((tmp_path / ".tasktool" / "config.json").read_text())
+  180	    assert data["tasklist"]["mutation_mode"] == "authoritative-checkout"
+  181	    assert "authoritative_root" not in data["tasklist"]
+  182	    assert data["tasklist"]["authoritative_branch"] == "main"
+  183	```
+  184	
+  185	Run: `python -m pytest tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_writes_project_config -v`
+  186	Expected: FAIL because the command does not exist.
+  187	
+  188	- [ ] **Step 4: Add command and CLI plumbing**
+  189	
+  190	In `tools/tasktool/commands.py`, import config helpers and add:
+  191	
+  192	```python
+  193	from tasktool.config import TasktoolConfig, TasklistConfig, save_config
+  194	
+  195	def cmd_config_init_authority(*, repo_root: Path, branch: str) -> None:
+  196	    cfg = TasktoolConfig(
+  197	        tasklist=TasklistConfig(
+  198	            mutation_mode="authoritative-checkout",
+  199	            authoritative_branch=branch,
+  200	        )
+
+[truncated: 1143 additional lines]
+### docs/tasklist.json
+
+    1	{
+    2	  "archived_phases": [
+    3	    {
+    4	      "archived_date": "2026-05-18",
+    5	      "archived_path": "docs/archived-tasks/P2-tasktool-json-backed-task-management-cli.md",
+    6	      "id": "P2",
+    7	      "title": "tasktool: JSON-backed task management CLI"
+    8	    }
+    9	  ],
+   10	  "cross_cutting": [
+   11	    {
+   12	      "closed": "2026-05-18",
+   13	      "created": "2026-05-18",
+   14	      "id": "X1",
+   15	      "notes": "Changed external-review default prompt transport from argv to stdin so the bundled Codex reviewer-agent receives prompts via codex exec '-' and avoids argv length failures.",
+   16	      "refs": [],
+   17	      "started": null,
+   18	      "status": "done",
+   19	      "title": "Default external-review prompt transport to stdin"
+   20	    },
+   21	    {
+   22	      "closed": "2026-05-18",
+   23	      "created": "2026-05-18",
+   24	      "id": "X2",
+   25	      "notes": "Added repo-local tools/tasktool/tasktool launcher, updated tasklist/project-setup docs to prefer it, and taught the pre-commit hook to use the repo-local launcher before falling back to a global tasktool shim.",
+   26	      "refs": [],
+   27	      "started": null,
+   28	      "status": "done",
+   29	      "title": "Add repo-local tasktool launcher"
+   30	    },
+   31	    {
+   32	      "closed": "2026-05-19",
+   33	      "created": "2026-05-19",
+   34	      "id": "X3",
+   35	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. External-review verdict parsing now accepts markdown-emphasized Overall Verdict headings such as **5. Overall Verdict** followed by ready/revise text.",
+   36	      "refs": [
+   37	        "skills/external-review/scripts/external-reviewer.py",
+   38	        "skills/external-review/tests/test_heading_style_verdict.py"
+   39	      ],
+   40	      "started": null,
+   41	      "status": "done",
+   42	      "title": "Spot fix: parse bold external-review verdict headings"
+   43	    },
+   44	    {
+   45	      "closed": "2026-05-19",
+   46	      "created": "2026-05-19",
+   47	      "id": "X4",
+   48	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. Legacy markdown import now accepts fully-qualified slice IDs and additional cross-cutting forms including tagged done items, blocked cross rows coerced to ready, and archived cross rows treated as done.",
+   49	      "refs": [
+   50	        "tools/tasktool/importer.py"
+   51	      ],
+   52	      "started": null,
+   53	      "status": "done",
+   54	      "title": "Spot fix: broaden legacy tasklist importer compatibility"
+   55	    },
+   56	    {
+   57	      "closed": "2026-05-19",
+   58	      "created": "2026-05-19",
+   59	      "id": "X5",
+   60	      "notes": "User-requested hook update completed outside the normal workflow for speed. Adds Stop/SubagentStop finished-agent notifications, milestone message derivation from final agent text/transcript payloads, Hypr TTS config reuse with OPENAI_API_KEY fallback, and non-TTS ding fallbacks.\nSuperseded by X8: final-text milestone parsing was removed; agent hooks now emit generic dings and semantic spoken notifications come from tasktool status changes.",
+   61	      "refs": [
+   62	        "hooks/agent-finished",
+   63	        "hooks/hooks.json",
+   64	        "hooks/hooks-cursor.json",
+   65	        "tests/claude-code/test-agent-finished-hook.sh"
+   66	      ],
+   67	      "started": null,
+   68	      "status": "done",
+   69	      "title": "Add finished-agent notification hook"
+   70	    },
+   71	    {
+   72	      "closed": "2026-05-19",
+   73	      "created": "2026-05-19",
+   74	      "id": "X6",
+   75	      "notes": "Codex startup skips Stop/SubagentStop notification hooks when hooks.json uses async=true; fix should preserve finished-agent notification behavior while avoiding unsupported async hook registration in Codex.\nSet finished-agent Stop/SubagentStop hook registrations to async=false for Codex compatibility. The hook now backgrounds real notification playback internally so synchronous hook registration returns quickly while dry-run tests remain foreground and deterministic.",
+   76	      "refs": [
+   77	        "hooks/hooks.json",
+   78	        "hooks/agent-finished",
+   79	        "tests/claude-code/test-hook-config.sh",
+   80	        "tests/claude-code/test-agent-finished-hook.sh"
+   81	      ],
+   82	      "started": null,
+   83	      "status": "done",
+   84	      "title": "Fix Codex finished-agent hook compatibility"
+   85	    },
+   86	    {
+   87	      "closed": "2026-05-19",
+   88	      "created": "2026-05-19",
+   89	      "id": "X7",
+   90	      "notes": "Codex reported superstar/6.0.0 because the installable local marketplace payload under plugins/superstar still declared version 6.0.0 and the version bump audit did not track that embedded manifest.\n\nBumped the embedded Codex plugin payload manifest to 6.0.1 and added it to the version bump check. Reinstalled superstar@superstar-dev, then rebuilt the 6.0.1 runtime cache as a materialized copy of this checkout with .agents excluded so Codex sees the full skills/hooks tree while codex plugin list still reports installed/enabled. Final probe shows cache version 6.0.1, skills/hooks present, and no async-hook warning.",
+   91	      "refs": [
+   92	        ".version-bump.json",
+   93	        "plugins/superstar/.codex-plugin/plugin.json",
+   94	        ".agents/plugins/marketplace.json",
+   95	        "tests/codex-plugin-sync/test-version-drift.sh",
+   96	        "tests/codex-plugin-sync/test-local-marketplace.sh"
+   97	      ],
+   98	      "started": null,
+   99	      "status": "done",
+  100	      "title": "Fix Superstar Codex plugin payload version drift"
+  101	    },
+  102	    {
+  103	      "closed": "2026-05-19",
+  104	      "created": "2026-05-19",
+  105	      "id": "X8",
+  106	      "notes": "Move semantic spoken notifications to tasktool status transitions for ready/in_progress/blocked/done. Keep agent Stop/SubagentStop hooks as generic completion dings only, with different sound styles for Claude and Codex.\nAgent Stop/SubagentStop hooks now emit generic harness-specific dings only. Semantic spoken notifications moved to tasktool status events for ready, in_progress, blocked, and done, including create, set, close, block, unblock, and archive-phase paths.",
+  107	      "refs": [
+  108	        "hooks/agent-finished",
+  109	        "tools/tasktool/notify.py",
+  110	        "tools/tasktool/commands.py",
+  111	        "tools/tasktool/tests/test_notify.py",
+  112	        "tools/tasktool/tests/test_commands.py",
+  113	        "tools/tasktool/tests/conftest.py",
+  114	        "tests/claude-code/test-agent-finished-hook.sh"
+  115	      ],
+  116	      "started": null,
+  117	      "status": "done",
+  118	      "title": "Move semantic notifications from agent hooks to tasktool status changes"
+  119	    },
+  120	    {
+  121	      "closed": "2026-05-19",
+  122	      "created": "2026-05-19",
+  123	      "id": "X9",
+  124	      "notes": "Rapid tasktool status changes currently spawn independent notifier processes, causing overlapping TTS/audio. Add a single-audio queue with at most three queued tasktool events; overflow should collapse to a single 'multiple other events' summary and drop further items.\nAdded a file-backed notification queue shared by agent dings and tasktool TTS. Only one worker drains audio at a time. Queue capacity is three pending events; overflow keeps the first two pending items and replaces the rest with a single 'Multiple other events' summary, dropping further burst items while the summary remains queued.",
+  125	      "refs": [
+  126	        "tools/tasktool/notify.py",
+  127	        "tools/tasktool/tests/test_notify.py"
+  128	      ],
+  129	      "started": null,
+  130	      "status": "done",
+  131	      "title": "Coalesce bursty tasktool audio notifications"
+  132	    }
+  133	  ],
+  134	  "last_reviewed": "2026-05-18",
+  135	  "north_star": "",
+  136	  "phases": [
+  137	    {
+  138	      "closed": "2026-05-17",
+  139	      "created": "2026-05-17",
+  140	      "id": "P1",
+  141	      "notes": "",
+  142	      "phase_reviewer_chain": null,
+  143	      "plan_path": null,
+  144	      "planning_path": null,
+  145	      "slices": [],
+  146	      "spec_path": null,
+  147	      "started": null,
+  148	      "status": "done",
+  149	      "title": "External-reviewer work (historical)"
+  150	    },
+  151	    {
+  152	      "closed": null,
+  153	      "created": "2026-05-19",
+  154	      "id": "P3",
+  155	      "notes": "",
+  156	      "phase_reviewer_chain": null,
+  157	      "plan_path": null,
+  158	      "planning_path": "docs/specs/2026-05-19-p3-phase-planning-design.md",
+  159	      "slices": [
+  160	        {
+  161	          "blocked_on": null,
+  162	          "closed": null,
+  163	          "created": "2026-05-19",
+  164	          "depends_on": [],
+  165	          "id": "S1",
+  166	          "notes": "",
+  167	          "parallel_group": "foundation",
+  168	          "plan_path": null,
+  169	          "planning_status": "ratified",
+  170	          "refs": [],
+  171	          "reviewer_chain": null,
+  172	          "started": null,
+  173	          "status": "ready",
+  174	          "tasks": [],
+  175	          "title": "Schema and validation foundation"
+  176	        },
+  177	        {
+  178	          "blocked_on": null,
+  179	          "closed": null,
+  180	          "created": "2026-05-19",
+  181	          "depends_on": [
+  182	            "P3.S1"
+  183	          ],
+  184	          "id": "S2",
+  185	          "notes": "",
+  186	          "parallel_group": "cli",
+  187	          "plan_path": null,
+  188	          "planning_status": "ratified",
+  189	          "refs": [],
+  190	          "reviewer_chain": null,
+  191	          "started": null,
+  192	          "status": "ready",
+  193	          "tasks": [],
+  194	          "title": "Scheduling CLI"
+  195	        },
+  196	        {
+  197	          "blocked_on": null,
+  198	          "closed": null,
+  199	          "created": "2026-05-19",
+  200	          "depends_on": [
+
+[truncated: 95 additional lines]
+
+<!-- superstar-prompt:end -->
\ No newline at end of file
diff --git a/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-primary-response.md b/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-primary-response.md
new file mode 100644
index 0000000..78f8000
--- /dev/null
+++ b/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-primary-response.md
@@ -0,0 +1,80 @@
+# Review — 2026-05-19-p4-tasktool-coordination-lifecycle-design.md (post-phase, round 1)
+
+- Target: `docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md`
+- Request: `docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-primary-request.md`
+- Reviewer command: `reviewer-agent`
+- Reviewer provider: `claude`
+- Sandbox: repo read-only; scratch/output writable
+- Status: `ok`
+
+---
+
+# Post-Phase Review — P4 Tasktool Coordination and Lifecycle Authority
+
+- Target: `docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md`
+- Kind: post-phase
+- Verdict gate runs against tasklist + plan + implementation in this worktree.
+
+## 1. Findings
+
+**F1 — `set --status done` has no `--allow-ready-close` parity with `close`.** Severity: important
+`tools/tasktool/commands.py:363-367` rejects a never-started slice during `cmd_set` with a hard error and instructs the user to run `tasktool close ... --allow-ready-close --reason`. No equivalent flag exists on the `set` parser (`tools/tasktool/cli.py`) nor on `cmd_set`. The spec lists `tasktool set P1.S1 --status done --reviewer-chain ...` as using "the same two-root reviewer-gate contract as `tasktool close`" (spec §Acceptance, line 192) and the project intent is parity. Today, legacy or scripted callers that use `set --status done` cannot proceed at all once a slice predates the guard — they must switch commands. This is exactly the post-slice S1.F2 finding from the P4.S2 reviewer chain and it was not resolved before close. Either add `--allow-ready-close --reason` to `set`, or amend the spec to declare `close` the sole legacy-bypass path.
+
+**F2 — `validate` ordering of `started` not enforced.** Severity: minor
+`tools/tasktool/validate.py:45-55` (`_check_dates`) was extended in commit `3f98a3d` to add calendar-shape validation for `started`, but it does not assert `created <= started` or `started <= closed`. The commit message ("validate started lifecycle dates") overstates the change. Both P4.S2 post-slice reviewers flagged this (F1 / S1.F1). An import or manual edit can therefore produce a row with nonsensical ordering and pass `--strict-format`. Add the ordering check (and a test) alongside the existing `closed >= created` rule.
+
+**F3 — P4 phase tracker drift at archive time.** Severity: minor
+`docs/tasklist.json:241-291`: P4 is `status: ready`, `started: null`, `closed: null` despite both slices being `done`. The spec (§Lifecycle Enforcement) notes phases are gated by slice completion and does not require `tasktool start P4`, so this is by design — but it means once `tasktool archive-phase P4` runs, the archive will carry forward a phase whose own lifecycle dates were never stamped. If "phase started" is meant to be a meaningful marker (acceptance criterion line 194 mentions phases accept `start`), consider either auto-stamping `started` on first slice start or documenting that phase rows skip `started` by policy.
+
+**F4 — P4.S1 closed with `started: null` and no override audit note.** Severity: minor / informational
+`docs/tasklist.json:251-266`. P4.S1 was closed by commit `57dae31` before `fd59f7f` introduced the guard, so the close was legal at the time. However, the resulting row now violates the invariant P4.S2 was designed to enforce. There is no `ready-close override` audit trail in `notes` because the override didn't exist when the close ran. This is expected by the spec ("Existing files load with `started: null`") but worth recording in the phase archive notes so future readers understand why a `done` slice in the P4 phase carries no `started` date.
+
+**F5 — `unblock --resume` silently stamps `started`.** Severity: minor
+`tools/tasktool/commands.py:436` calls `_start_item(qid, item, resume=True)` from `cmd_unblock`. This was flagged in the P4.S2 primary reviewer (F4) and not documented in the spec, the plan, or `skills/tasklist-discipline/SKILL.md`. The behavior is plausibly correct (unblocking a slice should resume in-progress and stamp a start), but the side effect is invisible to anyone reading docs. Add a one-line note where `unblock --resume` is described.
+
+**F6 — `set --status in_progress` on a `done` item now errors.** Severity: nit
+`commands.py:368-369` unconditionally routes `IN_PROGRESS` transitions through `_start_item`, which refuses done items with "already done". Previously this was a direct status assignment. The spec doesn't address re-opening done items either way, so this is an unannounced behavior change. Either codify in skills/spec (re-opens require a separate path) or restore the prior direct-assignment for the `done -> in_progress` edge.
+
+**F7 — Plan file checkboxes remain unchecked.** Severity: nit
+`docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md` — every `- [ ]` under Tasks 4-7 and the closeout sections is still unchecked even though the git history (`b810698`, `dc09679`, `fd59f7f`, `6abf660`, `3f98a3d`, `ed40767`, `c4deda7`) shows the work shipped and the tasklist confirms `P4.S2` is `done`. Either flip them to `- [x]` as part of the archive commit or document that `docs/tasklist.json` is the canonical status surface and plan boxes are advisory only. The post-slice S1.F4 finding flagged this and it was not addressed.
+
+**F8 — No archive artifact for P4 yet.** Severity: informational
+`docs/archived-tasks/` only contains `P2-...md`. The plan's P4.S2 closeout (lines 1314-1326) calls for `tasktool archive-phase P4 --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase` after this review concludes. The reviewer chain directory exists untracked (per `git status`). This review is the gate; once it returns ready / ready-with-small-edits, run the archive step. Not a finding to fix; just confirming the closeout sequence is intact.
+
+**F9 — Acceptance coverage spot-checks.** No issue
+Routing matrix tests, lock contention, reviewer-chain-outside-repo refusal, fail-closed authority discovery, `start`, `set --status in_progress` alias, slice close guard, and skill regression for all five skills are all present (`tools/tasktool/tests/test_worktree_authority.py`, `test_lifecycle_start.py`, `test_skill_tasktool_lifecycle_docs.py`). The S1.F3 sweep claim ("only 3 of 5 skills tested") was inaccurate at the time of writing — current test pins all five.
+
+## 2. Open questions / assumptions
+
+- Assumed `python -m pytest tools/tasktool/tests -v` is green at HEAD (`c4deda7`). I could not execute the suite from this reviewer pass. The plan's Final Verification (lines 1330-1343) requires it; please paste the result in the chain before archiving.
+- Assumed `tasktool validate --strict-format` passes on the current tasklist. The only suspicious row is P4.S1 (`done` + `started: null`), which is allowed by the validator's current rules.
+- Assumed `archive-phase P4` works against a phase whose own status is `ready` (no `tasktool start P4` was run). Worth confirming on a dry-run before archive.
+
+## 3. Suggested document edits
+
+- Spec §Acceptance: clarify F1 — either add `set --status done --allow-ready-close --reason` to the contract or strike the "same contract as close" wording for done-via-set.
+- Spec §Lifecycle Enforcement and `skills/tasklist-discipline/SKILL.md`: add a sentence describing F5 (`unblock --resume` stamps `started`).
+- Spec §Lifecycle Enforcement: state whether phase rows are expected to carry `started` (F3) or are exempt.
+- Plan file: either flip Task 4-7 boxes to `[x]` as part of the archive commit, or add a closeout step "TASKLIST.json is canonical; plan checkboxes are not maintained post-implementation" (F7).
+- Phase archive note (`tasktool archive-phase P4` will materialize `docs/archived-tasks/P4-*.md`): include a sentence explaining P4.S1's `started: null` per F4.
+
+## 4. Verification gaps / commands to run
+
+```sh
+PYTHONPATH=tools python -m pytest tools/tasktool/tests -v
+tools/tasktool/tasktool validate --strict-format
+git status --short
+```
+
+Expected before archive:
+- All tasktool tests pass (including `test_lifecycle_start.py`, `test_worktree_authority.py`, `test_skill_tasktool_lifecycle_docs.py`).
+- `validate --strict-format` clean.
+- Only `docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/` dirty (will be staged by `archive-phase`).
+
+If F2 (validate ordering) is addressed, add a test asserting `started < created` and `closed < started` are rejected, then re-run `pytest tools/tasktool/tests/test_validate.py -v`.
+
+## 5. Overall verdict
+
+**ready with small edits**
+
+The phase delivers the spec end-to-end: authoritative-checkout routing for every mutating command with a shared lock, the two-root reviewer-gate contract, fail-closed authority discovery, the `started` field across all four item types, `tasktool start` with `--resume`, the `set --status in_progress` alias, the slice-close guard with `--allow-ready-close --reason` audit-noted escape, and skill rewrites covered by regression tests for all five targeted skills. Two carry-overs from the P4.S2 post-slice review remain unaddressed — F1 (set/close parity for `--allow-ready-close`) and F2 (validator ordering) — and several minor polish items (F3-F7) should be resolved or documented before `tasktool archive-phase P4` runs. None of them block the close; F1 is the one most worth resolving in this round because it leaves an inconsistent CLI surface that future legacy migrations will hit.
diff --git a/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-sweep1-request.md b/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-sweep1-request.md
new file mode 100644
index 0000000..1b7a8c8
--- /dev/null
+++ b/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-sweep1-request.md
@@ -0,0 +1,668 @@
+<!-- superstar-prompt:start -->
+You are acting as an independent senior engineering reviewer.
+
+Review stance:
+- Lead with findings, ordered by severity.
+- Focus on correctness, consistency, implementation risk, missing acceptance
+  gates, vague handoffs, ungrounded assumptions, unverified claims, and drift
+  from the codebase.
+- Give exact file/line references when possible.
+- If the document is sound, say that clearly and list residual risks.
+- Keep the review actionable. Avoid broad rewrites unless the current structure
+  creates concrete risk.
+
+Repository root:
+/home/simon/Dev/sigreer/skills/superstar/.worktrees/p4-s2-lifecycle
+
+Target kind:
+post-phase
+
+Review mode:
+Post-phase review. Treat this as a closeout gate for a whole
+phase. Compare the implementation, archive/TASKLIST updates, and verification
+evidence against the phase spec/plan. Prioritize: unresolved acceptance
+criteria, stale docs, missing archive notes, cross-cutting tracker drift,
+deferred gates without justification, and regressions outside the phase scope.
+
+Target document:
+docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md
+
+Additional context files:
+- docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md
+- docs/tasklist.json
+
+Review output contract:
+1. Findings
+   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
+     stable if this review is iterated in subsequent rounds.
+   - Mark severity inline: `Severity: blocking | important | minor | nit`.
+2. Open questions / assumptions
+3. Suggested document edits
+4. Verification gaps / commands that should be run, if any
+5. Overall verdict: one of "ready", "ready with small edits", or "revise"
+
+Read the files from disk. Do not rely only on the snippets in this prompt.
+
+
+## Target Preview
+
+### docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md
+
+    1	# P4 — Tasktool Coordination and Lifecycle Authority
+    2	
+    3	**Status:** proposed
+    4	**Date:** 2026-05-19
+    5	**TASKLIST entry:** `P4` in `docs/tasklist.json`
+    6	
+    7	## Objective
+    8	
+    9	Make `tasktool` the enforced authority for two workflow rules that are currently left to agent discipline:
+   10	
+   11	1. Parallel implementation worktrees must not own `docs/tasklist.json` mutations.
+   12	2. Active slices and tasks must pass through `in_progress` instead of jumping from `ready` to `done`.
+   13	
+   14	The intended outcome is that agents can keep using normal `tasktool` commands from whatever checkout they are working in, but the tool decides where writes land and which lifecycle transitions are valid.
+   15	
+   16	## Problem
+   17	
+   18	`docs/tasklist.json` is the single source of truth, but linked implementation worktrees currently mutate their local copy. When those branches merge back to `main`, tasklist updates from multiple agents collide as byte-level JSON diffs. This is predictable because each worktree was forked from a stale snapshot of the tracker.
+   19	
+   20	The same workflow has a status-quality issue: agents rarely mark slices or tasks `in_progress`. Rows remain `ready` until they are closed, which makes `tasktool list --open`, `phase-status`, and human progress scans much less useful.
+   21	
+   22	These are not independent usability nits. They expose the same architectural gap: `tasktool` has the canonical data model, but it does not yet enforce the coordinator lifecycle strongly enough.
+   23	
+   24	## Design Summary
+   25	
+   26	`tasktool` gains two linked capabilities:
+   27	
+   28	- **Authoritative checkout routing.** Mutating commands invoked from implementation worktrees are applied to a configured authoritative checkout, normally the project `main` checkout. Every authoritative-mode write uses the same lock, including commands invoked directly from the authoritative checkout. Worker worktrees treat `docs/tasklist.json` as a read-only mirror.
+   29	- **Lifecycle start enforcement.** `tasktool start <id>` becomes the normal way to begin work. Slice close is allowed only after a slice has been observed `in_progress`, unless an explicit bypass is supplied and recorded.
+   30	
+   31	The skills are updated to describe the new command surface, but correctness does not depend on prose. The CLI enforces the rules.
+   32	
+   33	## Configuration
+   34	
+   35	Add a tracked project config file:
+   36	
+   37	```json
+   38	{
+   39	  "schema_version": 1,
+   40	  "tasklist": {
+   41	    "mutation_mode": "authoritative-checkout",
+   42	    "authoritative_branch": "main"
+   43	  }
+   44	}
+   45	```
+   46	
+   47	The default path is `.tasktool/config.json`. This file is intended to be committed because it contains project policy only, not machine-local absolute paths. If no config exists, current behavior remains unchanged so existing projects do not break abruptly.
+   48	
+   49	Field semantics:
+   50	
+   51	- `mutation_mode`
+   52	  - `local`: existing behavior; mutate the current checkout.
+   53	  - `authoritative-checkout`: route mutating commands from linked worktrees to `authoritative_root`.
+   54	- `authoritative_branch`: branch the authoritative checkout must be on when accepting writes.
+   55	
+   56	Machine-local root discovery:
+   57	
+   58	1. If `TASKTOOL_AUTHORITY_ROOT` is set, use it.
+   59	2. Otherwise inspect `git worktree list --porcelain` and find the checkout whose branch is `authoritative_branch`.
+   60	3. If exactly one checkout matches, use it.
+   61	4. If none or more than one match, fail closed and print the exact `TASKTOOL_AUTHORITY_ROOT=/path/to/checkout` override to use.
+   62	
+   63	`tasktool config init-authority --branch main` writes or updates `.tasktool/config.json`. It does not write absolute paths. A separate untracked `.tasktool/local.json` may be added later, but P4 should not require it.
+   64	
+   65	## Mutating Commands
+   66	
+   67	The routing layer applies to all commands that write `docs/tasklist.json`:
+   68	
+   69	- `init`
+   70	- `create phase|slice|task|cross`
+   71	- `set`
+   72	- `start`
+   73	- `close`
+   74	- `block`
+   75	- `unblock`
+   76	- `deps`
+   77	- `ratify`
+   78	- `planning-path`
+   79	- `note`
+   80	- `ref`
+   81	- `title`
+   82	- `archive-phase`
+   83	- `import`
+   84	- `validate --normalise`
+   85	
+   86	Read commands keep using the current checkout by default, but they should warn when authoritative routing is configured and the current worktree copy is older than the authoritative copy. A follow-up may add `--source authoritative|local`; P4 does not need it.
+   87	
+   88	## Routing Rules
+   89	
+   90	For every mutating command:
+   91	
+   92	1. Discover the current repository root and git common directory.
+   93	2. Load `.tasktool/config.json` if present.
+   94	3. If `mutation_mode` is absent or `local`, mutate the current checkout.
+   95	4. Resolve `authoritative_root` via the machine-local discovery rules.
+   96	5. Acquire an exclusive lock under the common git directory before loading tasklist data.
+   97	6. Validate that `authoritative_root` exists, is a git checkout for the same repository, is on `authoritative_branch`, and has no unresolved merge.
+   98	7. Validate that `authoritative_root/docs/tasklist.json` is not dirty in a way that cannot be attributed to tasktool's own current command.
+   99	8. Load and mutate `authoritative_root/docs/tasklist.json`, even if the invocation already came from that checkout.
+  100	9. Save canonical JSON and best-effort stage the authoritative path.
+  101	10. Print a concise routing message only when the invocation root differs from the authoritative root.
+  102	
+  103	The implementation should centralize this routing in one module so command functions do not each grow git-worktree logic.
+  104	
+  105	The lock is mandatory for every authoritative-mode mutation. Direct `main` checkout invocations and worker-routed invocations contend on the same lock, preventing interleaved read-modify-write cycles.
+  106	
+  107	## Two-Root Command Contract
+  108	
+  109	Commands in authoritative mode have two roots:
+  110	
+  111	- `invocation_root`: the checkout where the user or agent ran the command.
+  112	- `write_root`: the authoritative checkout whose `docs/tasklist.json` is mutated.
+  113	
+  114	User-supplied file paths and reviewer-chain discovery are interpreted relative to `invocation_root`. Tasklist load/save/stage happens in `write_root`. This applies to `close` and to `set --status done`, because both routes can invoke review-gate checks.
+  115	
+  116	Explicit reviewer-chain paths may be absolute or relative, but they must resolve inside `invocation_root`. Paths outside the repository are refused. The value recorded into tasklist is always repo-relative from `invocation_root`.
+  117	
+  118	## Reviewer Chains From Worktrees
+  119	
+  120	`tasktool close <slice-id>` and `tasktool set <id> --status done` must preserve review-gate semantics when invoked from an implementation worktree.
+  121	
+  122	The gate should evaluate reviewer artifacts relative to the invocation checkout because that is where post-slice review was run. The resulting `reviewer_chain` recorded into the authoritative tasklist remains a repo-relative path, for example:
+  123	
+  124	```text
+  125	docs/reviewer/p11-s4c-nav-footer-P11-S4c-post-slice
+  126	```
+  127	
+  128	If the reviewer chain path is outside the repository, the command refuses it. If the same repo-relative reviewer chain does not exist in the authoritative checkout yet, close still records the relative path; merge-back will bring the artifacts over. The JSON record must not depend on absolute worktree paths.
+  129	
+  130	## Lifecycle Enforcement
+  131	
+  132	Add:
+  133	
+  134	```sh
+  135	tasktool start <id>
+  136	```
+  137	
+  138	Behavior:
+  139	
+  140	- Accepts phases, slices, tasks, and cross-cutting items.
+  141	- Resolves short IDs exactly like `set`.
+  142	- Refuses `done` items.
+  143	- Refuses `blocked` slices unless `--resume` is supplied, in which case it clears `blocked_on` and sets `in_progress`.
+  144	- Sets `status: in_progress`.
+  145	- Records a machine-readable lifecycle marker that proves the item was started before close.
+  146	
+  147	The marker should be explicit rather than inferred from current status, because a row may later move from `in_progress` to `blocked` and back. Add `started: YYYY-MM-DD | null` to phase, slice, task, and cross-cutting records. Existing files load with `started: null`.
+  148	
+  149	`tasktool set <id> --status in_progress` becomes a compatibility alias for `tasktool start <id>`. It sets `started` using the same rules and notifications. This keeps older skill prose or human muscle memory from producing a visible `in_progress` state that later fails close because no start marker exists.
+  150	
+  151	Close behavior:
+  152	
+  153	- Closing tasks and cross-cutting items from `ready` remains allowed for now, because they are often small bookkeeping rows.
+  154	- Closing slices from `ready` is refused unless `--allow-ready-close` is supplied.
+  155	- `--allow-ready-close` appends an audit note with timestamp and reason.
+  156	- Closing phases from `ready` remains allowed only through `archive-phase`; phase lifecycle is already gated by completed slices.
+  157	
+  158	This targets the recurring operational pain without making every tiny task transition noisy.
+  159	
+  160	## Skill Updates
+  161	
+  162	Update these skills:
+  163	
+  164	- `tasklist-discipline`: explain authoritative routing, `tasktool start`, and the `ready -> done` slice close guard.
+  165	- `using-git-worktrees`: say worktrees may invoke tasktool mutations, but mutations route to the authoritative checkout when configured.
+  166	- `subagent-driven-development`: after selecting a ready slice and before dispatching implementation subagents, run `tasktool start <slice-id>`.
+  167	- `executing-plans`: replace the current prose-only "Mark as in_progress" step with `tasktool start <slice-id>`.
+  168	- `writing-plans`: plans for slice execution should include `tasktool start <slice-id>` as the first execution step when `docs/tasklist.json` exists.
+  169	
+  170	The status problem is partly skill markdown today, especially in `subagent-driven-development`, but the P4 fix should not rely on skill wording alone.
+  171	
+  172	## Slices
+  173	
+  174	### P4.S1 — Authoritative Tasklist Mutations
+  175	
+  176	Add config loading, git worktree detection, lock acquisition, routing helpers, and command integration for all tasklist-writing commands. Worker worktrees stop committing `docs/tasklist.json` deltas.
+  177	
+  178	### P4.S2 — Lifecycle Status Enforcement
+  179	
+  180	Add `started` fields, `tasktool start`, close-time enforcement for slices, and skill updates that make lifecycle transitions visible and routine.
+  181	
+  182	Depends on: `P4.S1`, because lifecycle commands should use the same routed-write path.
+  183	
+  184	## Acceptance Criteria
+  185	
+  186	- `tasktool validate --strict-format` passes on existing tasklist files.
+  187	- Tasktool unit and CLI tests cover local mode, authoritative mode, linked worktree routing, lock contention, unsafe authoritative checkout states, and reviewer-chain recording from a worker worktree.
+  188	- A simulated worker worktree can run `tasktool close P1.S1 --reviewer-chain ...` and leave the worker copy of `docs/tasklist.json` unchanged while updating the authoritative checkout.
+  189	- Direct authoritative-checkout writes and worker-routed writes contend on the same tasktool lock.
+  190	- `tasktool config init-authority --branch main` creates tracked project policy without absolute paths.
+  191	- A worker worktree with authoritative routing configured but no discoverable authoritative root fails closed instead of falling back to local mutation.
+  192	- `tasktool set P1.S1 --status done --reviewer-chain ...` uses the same two-root reviewer-gate contract as `tasktool close`.
+  193	- Explicit reviewer-chain paths outside the invocation repository are refused.
+  194	- `tasktool start P1.S1` sets `status: in_progress` and `started`.
+  195	- `tasktool set P1.S1 --status in_progress` sets the same `started` marker as `tasktool start`.
+  196	- `tasktool close P1.S1` refuses a never-started slice unless `--allow-ready-close --reason "..."` is supplied.
+  197	- Skills describe the enforced workflow without asking agents to hand-edit tasklist state.
+  198	
+  199	## Non-Goals
+  200	
+  201	- Do not build a semantic `tasktool merge` command in this phase. It is a fallback for a worse invariant.
+  202	- Do not move task state outside the repository.
+  203	- Do not add networked locking or a daemon.
+  204	- Do not require all existing projects to adopt authoritative routing immediately.
+  205	- Do not force every task row through `in_progress` before close in this phase.
+
+## Context Previews
+
+### docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md
+
+    1	# P4 — Tasktool Coordination and Lifecycle Authority Implementation Plan
+    2	
+    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
+    4	
+    5	**Goal:** Make tasklist mutations safe under parallel worktrees and make active work visibly enter `in_progress` before slice close.
+    6	
+    7	**Architecture:** Add a tasktool runtime layer that resolves whether a write should mutate locally or through an authoritative checkout, guarded by a lock in the shared git directory for every authoritative-mode write. Then add explicit lifecycle state (`started`) and `tasktool start`, with `set --status in_progress` as a compatibility alias and close-time enforcement for slices. Skills become instructions for the enforced command path, not the only enforcement mechanism.
+    8	
+    9	**Tech Stack:** Python 3 stdlib (`tasktool`), Git CLI, JSON, markdown skills.
+   10	
+   11	**TASKLIST entry:** `P4` in `docs/tasklist.json`; slices `P4.S1` and `P4.S2`.
+   12	
+   13	---
+   14	
+   15	## Scheduling Contract
+   16	
+   17	`tasktool schedule P4` currently reports:
+   18	
+   19	```text
+   20	P4.S1  [ready/ratified]  group=coordination  ready  deps=-  waiting_on=-  Authoritative tasklist mutations
+   21	P4.S2  [ready/ratified]  group=lifecycle  waiting  deps=P4.S1  waiting_on=P4.S1  Lifecycle status enforcement
+   22	```
+   23	
+   24	Execute `P4.S1` first. Do not start `P4.S2` until `P4.S1` has passed its post-slice review and `tasktool close P4.S1` succeeds.
+   25	
+   26	## File Map
+   27	
+   28	| Action | Path | Responsibility |
+   29	|--------|------|----------------|
+   30	| Create | `tools/tasktool/config.py` | Load/save `.tasktool/config.json`; define config dataclasses and validation. |
+   31	| Create | `tools/tasktool/worktree.py` | Git repository/worktree discovery, authoritative checkout validation, lock acquisition. |
+   32	| Modify | `tools/tasktool/commands.py` | Route mutating commands through a write context; add `cmd_config_init_authority`; later add `cmd_start` and lifecycle enforcement. |
+   33	| Modify | `tools/tasktool/cli.py` | Add `config init-authority`, `start`, and `close --allow-ready-close --reason`. |
+   34	| Modify | `tools/tasktool/model.py` | Add `started` fields to Phase/Slice/Task/CrossCutting in P4.S2. |
+   35	| Modify | `tools/tasktool/serialize.py` | Backward-compatible load/save for `started`. |
+   36	| Modify | `tools/tasktool/schema_gen.py` | Include `started` in generated schema. |
+   37	| Modify | `tools/tasktool/render.py` and `tools/tasktool/brief.py` | Surface `started` where useful. |
+   38	| Create | `tools/tasktool/tests/test_authority_config.py` | Config parsing and validation tests. |
+   39	| Create | `tools/tasktool/tests/test_worktree_authority.py` | Git worktree routing, unsafe-state, and locking tests. |
+   40	| Create | `tools/tasktool/tests/test_lifecycle_start.py` | `start`, `started`, and ready-close enforcement tests. |
+   41	| Modify | `skills/tasklist-discipline/SKILL.md` | Document authoritative routing and lifecycle commands. |
+   42	| Modify | `skills/using-git-worktrees/SKILL.md` | Explain routed tasktool writes from implementation worktrees. |
+   43	| Modify | `skills/subagent-driven-development/SKILL.md` | Require `tasktool start <slice-id>` before dispatch. |
+   44	| Modify | `skills/executing-plans/SKILL.md` | Replace prose-only in-progress step with `tasktool start`. |
+   45	| Modify | `skills/writing-plans/SKILL.md` | Plans must include a concrete `tasktool start` execution step. |
+   46	
+   47	## P4.S1 — Authoritative Tasklist Mutations
+   48	
+   49	### Task 1: Config Model and CLI Initializer
+   50	
+   51	**Files:**
+   52	- Create: `tools/tasktool/config.py`
+   53	- Modify: `tools/tasktool/cli.py`
+   54	- Modify: `tools/tasktool/commands.py`
+   55	- Test: `tools/tasktool/tests/test_authority_config.py`
+   56	
+   57	- [ ] **Step 1: Write failing config tests**
+   58	
+   59	Create `tools/tasktool/tests/test_authority_config.py`:
+   60	
+   61	```python
+   62	import json
+   63	from pathlib import Path
+   64	
+   65	from tasktool.config import (
+   66	    DEFAULT_CONFIG_REL,
+   67	    TasktoolConfig,
+   68	    TasklistConfig,
+   69	    load_config,
+   70	    save_config,
+   71	)
+   72	
+   73	def test_missing_config_defaults_to_local(tmp_path):
+   74	    cfg = load_config(tmp_path)
+   75	    assert cfg.tasklist.mutation_mode == "local"
+   76	
+   77	def test_round_trip_authoritative_config(tmp_path):
+   78	    cfg = TasktoolConfig(
+   79	        tasklist=TasklistConfig(
+   80	            mutation_mode="authoritative-checkout",
+   81	            authoritative_branch="main",
+   82	        )
+   83	    )
+   84	    save_config(tmp_path, cfg)
+   85	    raw = json.loads((tmp_path / DEFAULT_CONFIG_REL).read_text())
+   86	    assert raw["schema_version"] == 1
+   87	    assert raw["tasklist"]["mutation_mode"] == "authoritative-checkout"
+   88	    assert "authoritative_root" not in raw["tasklist"]
+   89	    assert load_config(tmp_path) == cfg
+   90	
+   91	def test_invalid_mode_raises(tmp_path):
+   92	    path = tmp_path / DEFAULT_CONFIG_REL
+   93	    path.parent.mkdir()
+   94	    path.write_text('{"schema_version":1,"tasklist":{"mutation_mode":"bad"}}')
+   95	    try:
+   96	        load_config(tmp_path)
+   97	    except ValueError as exc:
+   98	        assert "unknown mutation_mode" in str(exc)
+   99	    else:
+  100	        raise AssertionError("expected ValueError")
+  101	```
+  102	
+  103	Run: `python -m pytest tools/tasktool/tests/test_authority_config.py -v`
+  104	Expected: FAIL because `tasktool.config` does not exist.
+  105	
+  106	- [ ] **Step 2: Implement config module**
+  107	
+  108	Create `tools/tasktool/config.py`:
+  109	
+  110	```python
+  111	from __future__ import annotations
+  112	
+  113	import json
+  114	from dataclasses import dataclass, field
+  115	from pathlib import Path
+  116	
+  117	DEFAULT_CONFIG_REL = Path(".tasktool/config.json")
+  118	VALID_MUTATION_MODES = {"local", "authoritative-checkout"}
+  119	
+  120	@dataclass(frozen=True)
+  121	class TasklistConfig:
+  122	    mutation_mode: str = "local"
+  123	    authoritative_branch: str = "main"
+  124	
+  125	@dataclass(frozen=True)
+  126	class TasktoolConfig:
+  127	    schema_version: int = 1
+  128	    tasklist: TasklistConfig = field(default_factory=TasklistConfig)
+  129	
+  130	def _parse_tasklist(raw: dict) -> TasklistConfig:
+  131	    mode = raw.get("mutation_mode", "local")
+  132	    if mode not in VALID_MUTATION_MODES:
+  133	        raise ValueError(f"unknown mutation_mode: {mode}")
+  134	    return TasklistConfig(
+  135	        mutation_mode=mode,
+  136	        authoritative_branch=raw.get("authoritative_branch", "main"),
+  137	    )
+  138	
+  139	def load_config(repo_root: Path) -> TasktoolConfig:
+  140	    path = repo_root / DEFAULT_CONFIG_REL
+  141	    if not path.exists():
+  142	        return TasktoolConfig()
+  143	    raw = json.loads(path.read_text(encoding="utf-8"))
+  144	    if raw.get("schema_version", 1) != 1:
+  145	        raise ValueError(f"unsupported tasktool config schema_version: {raw.get('schema_version')}")
+  146	    return TasktoolConfig(
+  147	        schema_version=1,
+  148	        tasklist=_parse_tasklist(raw.get("tasklist", {})),
+  149	    )
+  150	
+  151	def save_config(repo_root: Path, cfg: TasktoolConfig) -> None:
+  152	    path = repo_root / DEFAULT_CONFIG_REL
+  153	    path.parent.mkdir(parents=True, exist_ok=True)
+  154	    body = {
+  155	        "schema_version": cfg.schema_version,
+  156	        "tasklist": {
+  157	            "mutation_mode": cfg.tasklist.mutation_mode,
+  158	            "authoritative_branch": cfg.tasklist.authoritative_branch,
+  159	        },
+  160	    }
+  161	    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
+  162	```
+  163	
+  164	Run: `python -m pytest tools/tasktool/tests/test_authority_config.py -v`
+  165	Expected: PASS.
+  166	
+  167	- [ ] **Step 3: Add CLI initializer test**
+  168	
+  169	Append to `tools/tasktool/tests/test_cli_integration.py`:
+  170	
+  171	```python
+  172	def test_config_init_authority_writes_project_config(tmp_path):
+  173	    r = run_cli(
+  174	        "config", "init-authority",
+  175	        "--branch", "main",
+  176	        cwd=tmp_path,
+  177	    )
+  178	    assert r.returncode == 0, r.stdout + r.stderr
+  179	    data = json.loads((tmp_path / ".tasktool" / "config.json").read_text())
+  180	    assert data["tasklist"]["mutation_mode"] == "authoritative-checkout"
+  181	    assert "authoritative_root" not in data["tasklist"]
+  182	    assert data["tasklist"]["authoritative_branch"] == "main"
+  183	```
+  184	
+  185	Run: `python -m pytest tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_writes_project_config -v`
+  186	Expected: FAIL because the command does not exist.
+  187	
+  188	- [ ] **Step 4: Add command and CLI plumbing**
+  189	
+  190	In `tools/tasktool/commands.py`, import config helpers and add:
+  191	
+  192	```python
+  193	from tasktool.config import TasktoolConfig, TasklistConfig, save_config
+  194	
+  195	def cmd_config_init_authority(*, repo_root: Path, branch: str) -> None:
+  196	    cfg = TasktoolConfig(
+  197	        tasklist=TasklistConfig(
+  198	            mutation_mode="authoritative-checkout",
+  199	            authoritative_branch=branch,
+  200	        )
+
+[truncated: 1143 additional lines]
+### docs/tasklist.json
+
+    1	{
+    2	  "archived_phases": [
+    3	    {
+    4	      "archived_date": "2026-05-18",
+    5	      "archived_path": "docs/archived-tasks/P2-tasktool-json-backed-task-management-cli.md",
+    6	      "id": "P2",
+    7	      "title": "tasktool: JSON-backed task management CLI"
+    8	    }
+    9	  ],
+   10	  "cross_cutting": [
+   11	    {
+   12	      "closed": "2026-05-18",
+   13	      "created": "2026-05-18",
+   14	      "id": "X1",
+   15	      "notes": "Changed external-review default prompt transport from argv to stdin so the bundled Codex reviewer-agent receives prompts via codex exec '-' and avoids argv length failures.",
+   16	      "refs": [],
+   17	      "started": null,
+   18	      "status": "done",
+   19	      "title": "Default external-review prompt transport to stdin"
+   20	    },
+   21	    {
+   22	      "closed": "2026-05-18",
+   23	      "created": "2026-05-18",
+   24	      "id": "X2",
+   25	      "notes": "Added repo-local tools/tasktool/tasktool launcher, updated tasklist/project-setup docs to prefer it, and taught the pre-commit hook to use the repo-local launcher before falling back to a global tasktool shim.",
+   26	      "refs": [],
+   27	      "started": null,
+   28	      "status": "done",
+   29	      "title": "Add repo-local tasktool launcher"
+   30	    },
+   31	    {
+   32	      "closed": "2026-05-19",
+   33	      "created": "2026-05-19",
+   34	      "id": "X3",
+   35	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. External-review verdict parsing now accepts markdown-emphasized Overall Verdict headings such as **5. Overall Verdict** followed by ready/revise text.",
+   36	      "refs": [
+   37	        "skills/external-review/scripts/external-reviewer.py",
+   38	        "skills/external-review/tests/test_heading_style_verdict.py"
+   39	      ],
+   40	      "started": null,
+   41	      "status": "done",
+   42	      "title": "Spot fix: parse bold external-review verdict headings"
+   43	    },
+   44	    {
+   45	      "closed": "2026-05-19",
+   46	      "created": "2026-05-19",
+   47	      "id": "X4",
+   48	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. Legacy markdown import now accepts fully-qualified slice IDs and additional cross-cutting forms including tagged done items, blocked cross rows coerced to ready, and archived cross rows treated as done.",
+   49	      "refs": [
+   50	        "tools/tasktool/importer.py"
+   51	      ],
+   52	      "started": null,
+   53	      "status": "done",
+   54	      "title": "Spot fix: broaden legacy tasklist importer compatibility"
+   55	    },
+   56	    {
+   57	      "closed": "2026-05-19",
+   58	      "created": "2026-05-19",
+   59	      "id": "X5",
+   60	      "notes": "User-requested hook update completed outside the normal workflow for speed. Adds Stop/SubagentStop finished-agent notifications, milestone message derivation from final agent text/transcript payloads, Hypr TTS config reuse with OPENAI_API_KEY fallback, and non-TTS ding fallbacks.\nSuperseded by X8: final-text milestone parsing was removed; agent hooks now emit generic dings and semantic spoken notifications come from tasktool status changes.",
+   61	      "refs": [
+   62	        "hooks/agent-finished",
+   63	        "hooks/hooks.json",
+   64	        "hooks/hooks-cursor.json",
+   65	        "tests/claude-code/test-agent-finished-hook.sh"
+   66	      ],
+   67	      "started": null,
+   68	      "status": "done",
+   69	      "title": "Add finished-agent notification hook"
+   70	    },
+   71	    {
+   72	      "closed": "2026-05-19",
+   73	      "created": "2026-05-19",
+   74	      "id": "X6",
+   75	      "notes": "Codex startup skips Stop/SubagentStop notification hooks when hooks.json uses async=true; fix should preserve finished-agent notification behavior while avoiding unsupported async hook registration in Codex.\nSet finished-agent Stop/SubagentStop hook registrations to async=false for Codex compatibility. The hook now backgrounds real notification playback internally so synchronous hook registration returns quickly while dry-run tests remain foreground and deterministic.",
+   76	      "refs": [
+   77	        "hooks/hooks.json",
+   78	        "hooks/agent-finished",
+   79	        "tests/claude-code/test-hook-config.sh",
+   80	        "tests/claude-code/test-agent-finished-hook.sh"
+   81	      ],
+   82	      "started": null,
+   83	      "status": "done",
+   84	      "title": "Fix Codex finished-agent hook compatibility"
+   85	    },
+   86	    {
+   87	      "closed": "2026-05-19",
+   88	      "created": "2026-05-19",
+   89	      "id": "X7",
+   90	      "notes": "Codex reported superstar/6.0.0 because the installable local marketplace payload under plugins/superstar still declared version 6.0.0 and the version bump audit did not track that embedded manifest.\n\nBumped the embedded Codex plugin payload manifest to 6.0.1 and added it to the version bump check. Reinstalled superstar@superstar-dev, then rebuilt the 6.0.1 runtime cache as a materialized copy of this checkout with .agents excluded so Codex sees the full skills/hooks tree while codex plugin list still reports installed/enabled. Final probe shows cache version 6.0.1, skills/hooks present, and no async-hook warning.",
+   91	      "refs": [
+   92	        ".version-bump.json",
+   93	        "plugins/superstar/.codex-plugin/plugin.json",
+   94	        ".agents/plugins/marketplace.json",
+   95	        "tests/codex-plugin-sync/test-version-drift.sh",
+   96	        "tests/codex-plugin-sync/test-local-marketplace.sh"
+   97	      ],
+   98	      "started": null,
+   99	      "status": "done",
+  100	      "title": "Fix Superstar Codex plugin payload version drift"
+  101	    },
+  102	    {
+  103	      "closed": "2026-05-19",
+  104	      "created": "2026-05-19",
+  105	      "id": "X8",
+  106	      "notes": "Move semantic spoken notifications to tasktool status transitions for ready/in_progress/blocked/done. Keep agent Stop/SubagentStop hooks as generic completion dings only, with different sound styles for Claude and Codex.\nAgent Stop/SubagentStop hooks now emit generic harness-specific dings only. Semantic spoken notifications moved to tasktool status events for ready, in_progress, blocked, and done, including create, set, close, block, unblock, and archive-phase paths.",
+  107	      "refs": [
+  108	        "hooks/agent-finished",
+  109	        "tools/tasktool/notify.py",
+  110	        "tools/tasktool/commands.py",
+  111	        "tools/tasktool/tests/test_notify.py",
+  112	        "tools/tasktool/tests/test_commands.py",
+  113	        "tools/tasktool/tests/conftest.py",
+  114	        "tests/claude-code/test-agent-finished-hook.sh"
+  115	      ],
+  116	      "started": null,
+  117	      "status": "done",
+  118	      "title": "Move semantic notifications from agent hooks to tasktool status changes"
+  119	    },
+  120	    {
+  121	      "closed": "2026-05-19",
+  122	      "created": "2026-05-19",
+  123	      "id": "X9",
+  124	      "notes": "Rapid tasktool status changes currently spawn independent notifier processes, causing overlapping TTS/audio. Add a single-audio queue with at most three queued tasktool events; overflow should collapse to a single 'multiple other events' summary and drop further items.\nAdded a file-backed notification queue shared by agent dings and tasktool TTS. Only one worker drains audio at a time. Queue capacity is three pending events; overflow keeps the first two pending items and replaces the rest with a single 'Multiple other events' summary, dropping further burst items while the summary remains queued.",
+  125	      "refs": [
+  126	        "tools/tasktool/notify.py",
+  127	        "tools/tasktool/tests/test_notify.py"
+  128	      ],
+  129	      "started": null,
+  130	      "status": "done",
+  131	      "title": "Coalesce bursty tasktool audio notifications"
+  132	    }
+  133	  ],
+  134	  "last_reviewed": "2026-05-18",
+  135	  "north_star": "",
+  136	  "phases": [
+  137	    {
+  138	      "closed": "2026-05-17",
+  139	      "created": "2026-05-17",
+  140	      "id": "P1",
+  141	      "notes": "",
+  142	      "phase_reviewer_chain": null,
+  143	      "plan_path": null,
+  144	      "planning_path": null,
+  145	      "slices": [],
+  146	      "spec_path": null,
+  147	      "started": null,
+  148	      "status": "done",
+  149	      "title": "External-reviewer work (historical)"
+  150	    },
+  151	    {
+  152	      "closed": null,
+  153	      "created": "2026-05-19",
+  154	      "id": "P3",
+  155	      "notes": "",
+  156	      "phase_reviewer_chain": null,
+  157	      "plan_path": null,
+  158	      "planning_path": "docs/specs/2026-05-19-p3-phase-planning-design.md",
+  159	      "slices": [
+  160	        {
+  161	          "blocked_on": null,
+  162	          "closed": null,
+  163	          "created": "2026-05-19",
+  164	          "depends_on": [],
+  165	          "id": "S1",
+  166	          "notes": "",
+  167	          "parallel_group": "foundation",
+  168	          "plan_path": null,
+  169	          "planning_status": "ratified",
+  170	          "refs": [],
+  171	          "reviewer_chain": null,
+  172	          "started": null,
+  173	          "status": "ready",
+  174	          "tasks": [],
+  175	          "title": "Schema and validation foundation"
+  176	        },
+  177	        {
+  178	          "blocked_on": null,
+  179	          "closed": null,
+  180	          "created": "2026-05-19",
+  181	          "depends_on": [
+  182	            "P3.S1"
+  183	          ],
+  184	          "id": "S2",
+  185	          "notes": "",
+  186	          "parallel_group": "cli",
+  187	          "plan_path": null,
+  188	          "planning_status": "ratified",
+  189	          "refs": [],
+  190	          "reviewer_chain": null,
+  191	          "started": null,
+  192	          "status": "ready",
+  193	          "tasks": [],
+  194	          "title": "Scheduling CLI"
+  195	        },
+  196	        {
+  197	          "blocked_on": null,
+  198	          "closed": null,
+  199	          "created": "2026-05-19",
+  200	          "depends_on": [
+
+[truncated: 95 additional lines]
+
+<!-- superstar-prompt:end -->
\ No newline at end of file
diff --git a/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-sweep1-response.md b/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-sweep1-response.md
new file mode 100644
index 0000000..871ee7c
--- /dev/null
+++ b/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-sweep1-response.md
@@ -0,0 +1,83 @@
+# Review — 2026-05-19-p4-tasktool-coordination-lifecycle-design.md (post-phase, round 1)
+
+- Target: `docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md`
+- Request: `docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-sweep1-request.md`
+- Reviewer command: `reviewer-agent`
+- Reviewer provider: `claude`
+- Sandbox: repo read-only; scratch/output writable
+- Status: `ok`
+
+---
+
+# Post-Phase Review — P4 Tasktool Coordination and Lifecycle Authority
+
+## 1. Findings
+
+### F1 — Phase P4 is not actually closed or archived  **Severity: blocking**
+`docs/tasklist.json` shows P4 with `status: "ready"`, `closed: null`, `started: null`, `phase_reviewer_chain: null`, and no entry in `archived_phases`. Both slices are `done`, but the phase itself was never moved through `in_progress`/`done` and has not been archived. A post-phase gate cannot be closed in this state.
+- Required: `tasktool start P4` (or accept ready-close on the phase via `archive-phase`), `tasktool close P4 --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase`, then `tasktool archive-phase P4`.
+- Also: `phase_reviewer_chain` must be persisted to the post-phase chain dir (currently untracked).
+
+### F2 — P4.S1 was closed without a `started` marker  **Severity: important**
+`P4.S1.started: null`, `status: "done"`. The spec/plan added the enforcement only in P4.S2, so this happened under the older rules — not a code defect, but it is a tracker artifact that violates the invariant the phase just introduced. Two options, pick one and apply: (a) backfill `started` for P4.S1 with a one-time normalisation, or (b) add an explicit note recording it as a grandfathered close. Leaving it as-is means the canonical tracker contains a slice that fails the rule the phase exists to enforce — bad dogfooding signal.
+
+### F3 — `set --status done` bypass asymmetry vs `close`  **Severity: important**
+`commands.py:363-367` refuses `set --status done` on a never-started slice and tells the user to either `start` first or use `close --allow-ready-close --reason ...`. But `cmd_set` itself has no `--allow-ready-close/--reason` parameters (`commands.py:350`, `cli.py` set parser), so the suggested bypass is only reachable via `close`. Spec Acceptance: "`set P1.S1 --status done --reviewer-chain ...` uses the same two-root reviewer-gate contract as `close`" — the gate contract matches, but the ready-close override does not. Either: (a) document explicitly that `set --status done` has no bypass (and `close` is the only path) and update the error message to drop the misleading suggestion of a flag combination that doesn't exist on `set`, or (b) add matching `--allow-ready-close/--reason` to `set`. Option (a) is fine and cheaper.
+
+### F4 — This repo does not dogfood authoritative routing  **Severity: minor**
+There is no `.tasktool/config.json` at the repo root, so the project still mutates in `local` mode. P4 implemented the capability; consider committing `.tasktool/config.json` (via `tasktool config init-authority --branch main`) as part of phase closeout so superstar itself runs under the new rules going forward. The spec said existing projects don't need to migrate "abruptly," so this isn't a blocker, but the phase ships without ever proving the routing works on its own tasklist.
+
+### F5 — Post-phase reviewer chain directory is untracked  **Severity: minor**
+`docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/` shows in `git status` as untracked. Expected during the review round itself, but it must be committed before `archive-phase` so the archived note has a stable reviewer link.
+
+### F6 — Spec acceptance: validate + test evidence not produced in this review  **Severity: minor**
+Acceptance criteria require `tasktool validate --strict-format` to pass and the test matrix (authority config, worktree routing, lock contention, lifecycle start, ready-close) to be green. The relevant test files exist (`test_authority_config.py`, `test_worktree_authority.py`, `test_lifecycle_start.py`, `test_skill_tasktool_lifecycle_docs.py`) but I could not execute them in this plan-mode review session. Closeout must run them and record the result. See section 4.
+
+### F7 — `cmd_start` accepts phases per spec but lifecycle for phases is not exercised by tasklist  **Severity: nit**
+Spec says `start` accepts phases. The implementation accepts them, but `P4` itself was never started, and the close-time enforcement explicitly excludes phases. Confirm intent: either remove phase support from `start` (it is dead surface area) or actually require `tasktool start P4` at phase kickoff and document it in `phase-planning`/`writing-plans`. Right now both paths exist and neither is exercised.
+
+### F8 — Spec uses `planning_path` for the spec doc; `spec_path` left null  **Severity: nit**
+P4 record has `planning_path: "docs/specs/.../p4-...-design.md"` but `spec_path: null`. The same pattern exists for P3, so this seems intentional (`planning_path` is the umbrella). Worth flagging because the field name `spec_path` reads like "where the spec lives" — a future reader will be confused.
+
+## 2. Open Questions / Assumptions
+
+- Is it acceptable to grandfather P4.S1's missing `started` marker, or do you want `tasktool` to gain a one-time backfill helper? (F2)
+- Should `set --status done` ever support `--allow-ready-close`, or is the asymmetry deliberate to force the explicit `close` path? (F3)
+- Does the closeout intend to flip this repo to authoritative routing in the same commit, or defer? (F4)
+- Should `tasktool start <phase>` be retained as a real lifecycle hook for phases, or pruned? (F7)
+
+## 3. Suggested Document Edits
+
+- **Spec, Lifecycle Enforcement section:** add a sentence clarifying that the ready-close override is only exposed on `tasktool close`, not on `tasktool set --status done` (resolving F3 toward option (a)).
+- **Spec, Acceptance Criteria:** add an explicit criterion that the project running P4 commits `.tasktool/config.json` configured for `authoritative-checkout` as part of phase closeout, or note explicitly that superstar itself defers adoption.
+- **Spec, Phase lifecycle:** clarify whether phases are expected to pass through `tasktool start` (currently ambiguous: `start` accepts them but `close` does not require it).
+
+## 4. Verification Gaps / Commands To Run
+
+Plan-mode prevented me from executing these. They must be run before declaring the phase ready:
+
+```sh
+tools/tasktool/tasktool validate --strict-format
+python -m pytest tools/tasktool/tests -q
+# Spot checks against acceptance criteria:
+python -m pytest tools/tasktool/tests/test_authority_config.py \
+                 tools/tasktool/tests/test_worktree_authority.py \
+                 tools/tasktool/tests/test_lifecycle_start.py \
+                 tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -v
+```
+
+Closeout actions (also currently undone):
+
+```sh
+git add docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/
+# After verdict is "ready":
+tools/tasktool/tasktool close P4 \
+  --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase
+tools/tasktool/tasktool archive-phase P4
+```
+
+## 5. Overall Verdict
+
+**revise**
+
+The implementation and skill changes look coherent and the slice-level work landed cleanly, but the phase itself has not been closed or archived in `docs/tasklist.json`, P4.S1 carries `started: null` after the very rule the phase enforces, and the `set` vs `close` bypass asymmetry produces a misleading error message. Address F1–F3 (and run the verification commands in §4) and a follow-up round should reach "ready" quickly.
diff --git a/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-merged-findings.md b/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-merged-findings.md
new file mode 100644
index 0000000..a58e8c3
--- /dev/null
+++ b/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-merged-findings.md
@@ -0,0 +1,172 @@
+# Merged findings for r1
+
+## Primary
+
+# Review — 2026-05-19-p4-tasktool-coordination-lifecycle-design.md (post-phase, round 1)
+
+- Target: `docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md`
+- Request: `docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-primary-request.md`
+- Reviewer command: `reviewer-agent`
+- Reviewer provider: `claude`
+- Sandbox: repo read-only; scratch/output writable
+- Status: `ok`
+
+---
+
+# Post-Phase Review — P4 Tasktool Coordination and Lifecycle Authority
+
+- Target: `docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md`
+- Kind: post-phase
+- Verdict gate runs against tasklist + plan + implementation in this worktree.
+
+## 1. Findings
+
+**F1 — `set --status done` has no `--allow-ready-close` parity with `close`.** Severity: important
+`tools/tasktool/commands.py:363-367` rejects a never-started slice during `cmd_set` with a hard error and instructs the user to run `tasktool close ... --allow-ready-close --reason`. No equivalent flag exists on the `set` parser (`tools/tasktool/cli.py`) nor on `cmd_set`. The spec lists `tasktool set P1.S1 --status done --reviewer-chain ...` as using "the same two-root reviewer-gate contract as `tasktool close`" (spec §Acceptance, line 192) and the project intent is parity. Today, legacy or scripted callers that use `set --status done` cannot proceed at all once a slice predates the guard — they must switch commands. This is exactly the post-slice S1.F2 finding from the P4.S2 reviewer chain and it was not resolved before close. Either add `--allow-ready-close --reason` to `set`, or amend the spec to declare `close` the sole legacy-bypass path.
+
+**F2 — `validate` ordering of `started` not enforced.** Severity: minor
+`tools/tasktool/validate.py:45-55` (`_check_dates`) was extended in commit `3f98a3d` to add calendar-shape validation for `started`, but it does not assert `created <= started` or `started <= closed`. The commit message ("validate started lifecycle dates") overstates the change. Both P4.S2 post-slice reviewers flagged this (F1 / S1.F1). An import or manual edit can therefore produce a row with nonsensical ordering and pass `--strict-format`. Add the ordering check (and a test) alongside the existing `closed >= created` rule.
+
+**F3 — P4 phase tracker drift at archive time.** Severity: minor
+`docs/tasklist.json:241-291`: P4 is `status: ready`, `started: null`, `closed: null` despite both slices being `done`. The spec (§Lifecycle Enforcement) notes phases are gated by slice completion and does not require `tasktool start P4`, so this is by design — but it means once `tasktool archive-phase P4` runs, the archive will carry forward a phase whose own lifecycle dates were never stamped. If "phase started" is meant to be a meaningful marker (acceptance criterion line 194 mentions phases accept `start`), consider either auto-stamping `started` on first slice start or documenting that phase rows skip `started` by policy.
+
+**F4 — P4.S1 closed with `started: null` and no override audit note.** Severity: minor / informational
+`docs/tasklist.json:251-266`. P4.S1 was closed by commit `57dae31` before `fd59f7f` introduced the guard, so the close was legal at the time. However, the resulting row now violates the invariant P4.S2 was designed to enforce. There is no `ready-close override` audit trail in `notes` because the override didn't exist when the close ran. This is expected by the spec ("Existing files load with `started: null`") but worth recording in the phase archive notes so future readers understand why a `done` slice in the P4 phase carries no `started` date.
+
+**F5 — `unblock --resume` silently stamps `started`.** Severity: minor
+`tools/tasktool/commands.py:436` calls `_start_item(qid, item, resume=True)` from `cmd_unblock`. This was flagged in the P4.S2 primary reviewer (F4) and not documented in the spec, the plan, or `skills/tasklist-discipline/SKILL.md`. The behavior is plausibly correct (unblocking a slice should resume in-progress and stamp a start), but the side effect is invisible to anyone reading docs. Add a one-line note where `unblock --resume` is described.
+
+**F6 — `set --status in_progress` on a `done` item now errors.** Severity: nit
+`commands.py:368-369` unconditionally routes `IN_PROGRESS` transitions through `_start_item`, which refuses done items with "already done". Previously this was a direct status assignment. The spec doesn't address re-opening done items either way, so this is an unannounced behavior change. Either codify in skills/spec (re-opens require a separate path) or restore the prior direct-assignment for the `done -> in_progress` edge.
+
+**F7 — Plan file checkboxes remain unchecked.** Severity: nit
+`docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md` — every `- [ ]` under Tasks 4-7 and the closeout sections is still unchecked even though the git history (`b810698`, `dc09679`, `fd59f7f`, `6abf660`, `3f98a3d`, `ed40767`, `c4deda7`) shows the work shipped and the tasklist confirms `P4.S2` is `done`. Either flip them to `- [x]` as part of the archive commit or document that `docs/tasklist.json` is the canonical status surface and plan boxes are advisory only. The post-slice S1.F4 finding flagged this and it was not addressed.
+
+**F8 — No archive artifact for P4 yet.** Severity: informational
+`docs/archived-tasks/` only contains `P2-...md`. The plan's P4.S2 closeout (lines 1314-1326) calls for `tasktool archive-phase P4 --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase` after this review concludes. The reviewer chain directory exists untracked (per `git status`). This review is the gate; once it returns ready / ready-with-small-edits, run the archive step. Not a finding to fix; just confirming the closeout sequence is intact.
+
+**F9 — Acceptance coverage spot-checks.** No issue
+Routing matrix tests, lock contention, reviewer-chain-outside-repo refusal, fail-closed authority discovery, `start`, `set --status in_progress` alias, slice close guard, and skill regression for all five skills are all present (`tools/tasktool/tests/test_worktree_authority.py`, `test_lifecycle_start.py`, `test_skill_tasktool_lifecycle_docs.py`). The S1.F3 sweep claim ("only 3 of 5 skills tested") was inaccurate at the time of writing — current test pins all five.
+
+## 2. Open questions / assumptions
+
+- Assumed `python -m pytest tools/tasktool/tests -v` is green at HEAD (`c4deda7`). I could not execute the suite from this reviewer pass. The plan's Final Verification (lines 1330-1343) requires it; please paste the result in the chain before archiving.
+- Assumed `tasktool validate --strict-format` passes on the current tasklist. The only suspicious row is P4.S1 (`done` + `started: null`), which is allowed by the validator's current rules.
+- Assumed `archive-phase P4` works against a phase whose own status is `ready` (no `tasktool start P4` was run). Worth confirming on a dry-run before archive.
+
+## 3. Suggested document edits
+
+- Spec §Acceptance: clarify F1 — either add `set --status done --allow-ready-close --reason` to the contract or strike the "same contract as close" wording for done-via-set.
+- Spec §Lifecycle Enforcement and `skills/tasklist-discipline/SKILL.md`: add a sentence describing F5 (`unblock --resume` stamps `started`).
+- Spec §Lifecycle Enforcement: state whether phase rows are expected to carry `started` (F3) or are exempt.
+- Plan file: either flip Task 4-7 boxes to `[x]` as part of the archive commit, or add a closeout step "TASKLIST.json is canonical; plan checkboxes are not maintained post-implementation" (F7).
+- Phase archive note (`tasktool archive-phase P4` will materialize `docs/archived-tasks/P4-*.md`): include a sentence explaining P4.S1's `started: null` per F4.
+
+## 4. Verification gaps / commands to run
+
+```sh
+PYTHONPATH=tools python -m pytest tools/tasktool/tests -v
+tools/tasktool/tasktool validate --strict-format
+git status --short
+```
+
+Expected before archive:
+- All tasktool tests pass (including `test_lifecycle_start.py`, `test_worktree_authority.py`, `test_skill_tasktool_lifecycle_docs.py`).
+- `validate --strict-format` clean.
+- Only `docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/` dirty (will be staged by `archive-phase`).
+
+If F2 (validate ordering) is addressed, add a test asserting `started < created` and `closed < started` are rejected, then re-run `pytest tools/tasktool/tests/test_validate.py -v`.
+
+## 5. Overall verdict
+
+**ready with small edits**
+
+The phase delivers the spec end-to-end: authoritative-checkout routing for every mutating command with a shared lock, the two-root reviewer-gate contract, fail-closed authority discovery, the `started` field across all four item types, `tasktool start` with `--resume`, the `set --status in_progress` alias, the slice-close guard with `--allow-ready-close --reason` audit-noted escape, and skill rewrites covered by regression tests for all five targeted skills. Two carry-overs from the P4.S2 post-slice review remain unaddressed — F1 (set/close parity for `--allow-ready-close`) and F2 (validator ordering) — and several minor polish items (F3-F7) should be resolved or documented before `tasktool archive-phase P4` runs. None of them block the close; F1 is the one most worth resolving in this round because it leaves an inconsistent CLI surface that future legacy migrations will hit.
+
+
+## Sweep 1
+
+# Review — 2026-05-19-p4-tasktool-coordination-lifecycle-design.md (post-phase, round 1)
+
+- Target: `docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md`
+- Request: `docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-2026-05-19T2328-sweep1-request.md`
+- Reviewer command: `reviewer-agent`
+- Reviewer provider: `claude`
+- Sandbox: repo read-only; scratch/output writable
+- Status: `ok`
+
+---
+
+# Post-Phase Review — P4 Tasktool Coordination and Lifecycle Authority
+
+## 1. Findings
+
+### S1.F1 — Phase P4 is not actually closed or archived  **Severity: blocking**
+`docs/tasklist.json` shows P4 with `status: "ready"`, `closed: null`, `started: null`, `phase_reviewer_chain: null`, and no entry in `archived_phases`. Both slices are `done`, but the phase itself was never moved through `in_progress`/`done` and has not been archived. A post-phase gate cannot be closed in this state.
+- Required: `tasktool start P4` (or accept ready-close on the phase via `archive-phase`), `tasktool close P4 --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase`, then `tasktool archive-phase P4`.
+- Also: `phase_reviewer_chain` must be persisted to the post-phase chain dir (currently untracked).
+
+### S1.F2 — P4.S1 was closed without a `started` marker  **Severity: important**
+`P4.S1.started: null`, `status: "done"`. The spec/plan added the enforcement only in P4.S2, so this happened under the older rules — not a code defect, but it is a tracker artifact that violates the invariant the phase just introduced. Two options, pick one and apply: (a) backfill `started` for P4.S1 with a one-time normalisation, or (b) add an explicit note recording it as a grandfathered close. Leaving it as-is means the canonical tracker contains a slice that fails the rule the phase exists to enforce — bad dogfooding signal.
+
+### S1.F3 — `set --status done` bypass asymmetry vs `close`  **Severity: important**
+`commands.py:363-367` refuses `set --status done` on a never-started slice and tells the user to either `start` first or use `close --allow-ready-close --reason ...`. But `cmd_set` itself has no `--allow-ready-close/--reason` parameters (`commands.py:350`, `cli.py` set parser), so the suggested bypass is only reachable via `close`. Spec Acceptance: "`set P1.S1 --status done --reviewer-chain ...` uses the same two-root reviewer-gate contract as `close`" — the gate contract matches, but the ready-close override does not. Either: (a) document explicitly that `set --status done` has no bypass (and `close` is the only path) and update the error message to drop the misleading suggestion of a flag combination that doesn't exist on `set`, or (b) add matching `--allow-ready-close/--reason` to `set`. Option (a) is fine and cheaper.
+
+### S1.F4 — This repo does not dogfood authoritative routing  **Severity: minor**
+There is no `.tasktool/config.json` at the repo root, so the project still mutates in `local` mode. P4 implemented the capability; consider committing `.tasktool/config.json` (via `tasktool config init-authority --branch main`) as part of phase closeout so superstar itself runs under the new rules going forward. The spec said existing projects don't need to migrate "abruptly," so this isn't a blocker, but the phase ships without ever proving the routing works on its own tasklist.
+
+### S1.F5 — Post-phase reviewer chain directory is untracked  **Severity: minor**
+`docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/` shows in `git status` as untracked. Expected during the review round itself, but it must be committed before `archive-phase` so the archived note has a stable reviewer link.
+
+### S1.F6 — Spec acceptance: validate + test evidence not produced in this review  **Severity: minor**
+Acceptance criteria require `tasktool validate --strict-format` to pass and the test matrix (authority config, worktree routing, lock contention, lifecycle start, ready-close) to be green. The relevant test files exist (`test_authority_config.py`, `test_worktree_authority.py`, `test_lifecycle_start.py`, `test_skill_tasktool_lifecycle_docs.py`) but I could not execute them in this plan-mode review session. Closeout must run them and record the result. See section 4.
+
+### S1.F7 — `cmd_start` accepts phases per spec but lifecycle for phases is not exercised by tasklist  **Severity: nit**
+Spec says `start` accepts phases. The implementation accepts them, but `P4` itself was never started, and the close-time enforcement explicitly excludes phases. Confirm intent: either remove phase support from `start` (it is dead surface area) or actually require `tasktool start P4` at phase kickoff and document it in `phase-planning`/`writing-plans`. Right now both paths exist and neither is exercised.
+
+### S1.F8 — Spec uses `planning_path` for the spec doc; `spec_path` left null  **Severity: nit**
+P4 record has `planning_path: "docs/specs/.../p4-...-design.md"` but `spec_path: null`. The same pattern exists for P3, so this seems intentional (`planning_path` is the umbrella). Worth flagging because the field name `spec_path` reads like "where the spec lives" — a future reader will be confused.
+
+## 2. Open Questions / Assumptions
+
+- Is it acceptable to grandfather P4.S1's missing `started` marker, or do you want `tasktool` to gain a one-time backfill helper? (S1.F2)
+- Should `set --status done` ever support `--allow-ready-close`, or is the asymmetry deliberate to force the explicit `close` path? (S1.F3)
+- Does the closeout intend to flip this repo to authoritative routing in the same commit, or defer? (S1.F4)
+- Should `tasktool start <phase>` be retained as a real lifecycle hook for phases, or pruned? (S1.F7)
+
+## 3. Suggested Document Edits
+
+- **Spec, Lifecycle Enforcement section:** add a sentence clarifying that the ready-close override is only exposed on `tasktool close`, not on `tasktool set --status done` (resolving S1.F3 toward option (a)).
+- **Spec, Acceptance Criteria:** add an explicit criterion that the project running P4 commits `.tasktool/config.json` configured for `authoritative-checkout` as part of phase closeout, or note explicitly that superstar itself defers adoption.
+- **Spec, Phase lifecycle:** clarify whether phases are expected to pass through `tasktool start` (currently ambiguous: `start` accepts them but `close` does not require it).
+
+## 4. Verification Gaps / Commands To Run
+
+Plan-mode prevented me from executing these. They must be run before declaring the phase ready:
+
+```sh
+tools/tasktool/tasktool validate --strict-format
+python -m pytest tools/tasktool/tests -q
+# Spot checks against acceptance criteria:
+python -m pytest tools/tasktool/tests/test_authority_config.py \
+                 tools/tasktool/tests/test_worktree_authority.py \
+                 tools/tasktool/tests/test_lifecycle_start.py \
+                 tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -v
+```
+
+Closeout actions (also currently undone):
+
+```sh
+git add docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/
+# After verdict is "ready":
+tools/tasktool/tasktool close P4 \
+  --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase
+tools/tasktool/tasktool archive-phase P4
+```
+
+## 5. Overall Verdict
+
+**revise**
+
+The implementation and skill changes look coherent and the slice-level work landed cleanly, but the phase itself has not been closed or archived in `docs/tasklist.json`, P4.S1 carries `started: null` after the very rule the phase enforces, and the `set` vs `close` bypass asymmetry produces a misleading error message. Address S1.F1–S1.F3 (and run the verification commands in §4) and a follow-up round should reach "ready" quickly.
+
diff --git a/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-resolution.md b/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-resolution.md
new file mode 100644
index 0000000..2a12d14
--- /dev/null
+++ b/docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/r1-resolution.md
@@ -0,0 +1,114 @@
+# Resolution for r1
+
+Round 1 returned a primary verdict of `ready with small edits` and a sweep verdict of `revise`. This repair addresses the actionable lifecycle findings and records explicit waivers or deferrals for closeout-only items.
+
+Repair commit: this commit (`tasktool: resolve P4 post-phase lifecycle findings`)
+
+## F1
+Status: fixed
+Evidence:
+- Files: `tools/tasktool/cli.py`, `tools/tasktool/commands.py`, `tools/tasktool/tests/test_commands.py`, `tools/tasktool/tests/test_lifecycle_start.py`.
+- `tasktool set --status done` now accepts `--allow-ready-close` and `--reason`, applies the same ready-close audit note as `tasktool close`, and still refuses never-started slices when the override or reason is missing.
+- Verification: `python -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_lifecycle_start.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` -> `110 passed`.
+
+## F2
+Status: fixed
+Evidence:
+- Files: `tools/tasktool/validate.py`, `tools/tasktool/tests/test_validate.py`.
+- Validator now rejects `started < created` and `closed < started` after validating date shape and calendar validity.
+- Verification: same targeted pytest run -> `110 passed`.
+
+## F3
+Status: fixed
+Evidence:
+- Files: `docs/tasklist.json`.
+- Ran `tools/tasktool/tasktool start P4`; P4 now has `status: in_progress` and `started: 2026-05-19`, so the phase lifecycle marker exists before the next close/archive attempt.
+
+## F4
+Status: fixed
+Evidence:
+- Files: `docs/tasklist.json`.
+- Added a P4.S1 note through tasktool: "P4.S1 is grandfathered under pre-P4.S2 lifecycle rules: it was closed before the started-field close guard and ready-close override audit note existed, so started remains null intentionally."
+
+## F5
+Status: fixed
+Evidence:
+- Files: `skills/tasklist-discipline/SKILL.md`, `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`.
+- The skill now documents that `tasktool unblock <slice-id> --resume` resumes through the same lifecycle path and stamps `started` when needed.
+- Verification: same targeted pytest run -> `110 passed`.
+
+## F6
+Status: waived
+Evidence:
+- The current behavior is intentional lifecycle tightening: `set --status in_progress` routes through `_start_item`, and `_start_item` refuses already-done rows.
+- Reopening done work remains outside P4 scope; no separate reopen command or policy was specified in the P4 acceptance criteria.
+
+## F7
+Status: waived
+Evidence:
+- `docs/tasklist.json` is the canonical status surface for this repo; P4.S2 is already `done` there and the plan checkboxes are advisory implementation scaffolding.
+- No code or validation behavior depends on plan checkbox state.
+
+## F8
+Status: deferred
+Evidence:
+- Archive remains gated on the next post-phase review round. The current chain round has merged verdict `revise`, so closing or archiving P4 now would require bypassing the review gate.
+- This repair starts P4 and writes the resolution artifact required for the next round; archive should run after the post-phase chain returns `ready` or `ready with small edits`.
+
+## F9
+Status: waived
+Evidence:
+- Primary reviewer reported no issue. Existing acceptance coverage remains in the tasktool test suite, and the final verification set is rerun for this repair before commit.
+
+## S1.F1
+Status: deferred
+Evidence:
+- P4 has now been started via tasktool, addressing the unstamped phase lifecycle marker.
+- P4 close/archive is deferred until the post-phase reviewer chain no longer has merged verdict `revise`; bypassing the gate here would weaken the workflow P4 is validating.
+
+## S1.F2
+Status: fixed
+Evidence:
+- Same as F4. P4.S1 now has an explicit grandfathering note in `docs/tasklist.json`.
+
+## S1.F3
+Status: fixed
+Evidence:
+- Same as F1. `set --status done` now has ready-close override parity with `close`.
+
+## S1.F4
+Status: waived
+Evidence:
+- The P4 spec explicitly did not require abrupt migration of existing projects to authoritative mode.
+- Adding `.tasktool/config.json` would be a policy adoption step for the repo, not a repair for the lifecycle bugs found in this round.
+
+## S1.F5
+Status: fixed
+Evidence:
+- The post-phase reviewer chain directory and this `r1-resolution.md` are included in the repair commit.
+
+## S1.F6
+Status: fixed
+Evidence:
+- Verification commands are run and recorded before the repair commit.
+
+## S1.F7
+Status: fixed
+Evidence:
+- Same as F3. P4 now exercises `tasktool start P4` and carries a phase-level `started` marker.
+
+## S1.F8
+Status: waived
+Evidence:
+- The reviewer identified an existing field-naming ambiguity (`planning_path` holds the P4 design doc while `spec_path` is null). This is consistent with existing P3/P4 tasklist usage and is not part of the P4 lifecycle repair scope.
+
+## Verification
+
+Targeted red-green verification:
+- Initial targeted run failed for the new tests: validator ordering was not enforced and `set` did not accept `--allow-ready-close` / `--reason`.
+- After implementation: `python -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_lifecycle_start.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` -> `110 passed`.
+
+Final verification:
+- `tools/tasktool/tasktool validate --strict-format` -> `ok`
+- `python -m pytest tools/tasktool/tests/test_validate.py tools/tasktool/tests/test_lifecycle_start.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_cli_integration.py tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -v` -> `132 passed in 11.21s`
+- `python -m pytest tools/tasktool/tests -q` -> `253 passed in 22.22s`
diff --git a/docs/tasklist.json b/docs/tasklist.json
index 134a4ae..6cd77ee 100644
--- a/docs/tasklist.json
+++ b/docs/tasklist.json
@@ -253,7 +253,7 @@
           "created": "2026-05-19",
           "depends_on": [],
           "id": "S1",
-          "notes": "",
+          "notes": "P4.S1 is grandfathered under pre-P4.S2 lifecycle rules: it was closed before the started-field close guard and ready-close override audit note existed, so started remains null intentionally.",
           "parallel_group": "coordination",
           "plan_path": null,
           "planning_status": "ratified",
@@ -285,8 +285,8 @@
         }
       ],
       "spec_path": null,
-      "started": null,
-      "status": "ready",
+      "started": "2026-05-19",
+      "status": "in_progress",
       "title": "Tasktool coordination and lifecycle authority"
     }
   ],
diff --git a/skills/tasklist-discipline/SKILL.md b/skills/tasklist-discipline/SKILL.md
index 2a110e0..5c5defa 100644
--- a/skills/tasklist-discipline/SKILL.md
+++ b/skills/tasklist-discipline/SKILL.md
@@ -37,7 +37,7 @@ Onboarding has a hard setup boundary: after `[[project-setup]]` creates or impor
 
 IDs are assigned at birth and **never renumbered**. The `tasktool create` family does orphan-aware allocation (`max+1` across `docs/tasklist.json`, `docs/specs/`, `docs/plans/`, `docs/reviewer/`) and prints the new ID.
 
-Status enum: `ready | in_progress | blocked | done`. Only slices may take `blocked` (and only via `tasktool block <slice-id> --on …`). Emoji are a render concern; `tasktool render` and `tasktool brief` handle that. `tasktool start <slice-id>` is the normal way to enter `in_progress`; `tasktool set <id> --status in_progress` is a compatibility alias for older plans and ad-hoc rows. `done` requires `closed`; the CLI stamps it.
+Status enum: `ready | in_progress | blocked | done`. Only slices may take `blocked` (and only via `tasktool block <slice-id> --on …`). Emoji are a render concern; `tasktool render` and `tasktool brief` handle that. `tasktool start <slice-id>` is the normal way to enter `in_progress`; `tasktool set <id> --status in_progress` is a compatibility alias for older plans and ad-hoc rows. `tasktool unblock <slice-id> --resume` resumes through the same lifecycle path and stamps `started` when needed. `done` requires `closed`; the CLI stamps it.
 
 Phase planning uses separate scheduling metadata. `planning_path` points at the phase-scoped planning/design document. `depends_on` records planned slice sequencing; it is not the same as runtime `blocked_on`. `planning_status` is `proposed | ratified | superseded`, and `parallel_group` names slices intended to be planned or executed together.
 
diff --git a/tools/tasktool/cli.py b/tools/tasktool/cli.py
index a5cb897..332cc9f 100644
--- a/tools/tasktool/cli.py
+++ b/tools/tasktool/cli.py
@@ -64,6 +64,8 @@ def _build_parser() -> argparse.ArgumentParser:
                        choices=["ready", "in_progress", "done"])
     p_set.add_argument("--reviewer-chain", type=Path)
     p_set.add_argument("--skip-review-gate", action="store_true")
+    p_set.add_argument("--allow-ready-close", action="store_true")
+    p_set.add_argument("--reason")
 
     p_start = sub.add_parser("start")
     p_start.add_argument("id")
@@ -215,6 +217,7 @@ def main(argv: list[str]) -> int:
             commands.cmd_set(
                 repo_root=root, id=args.id, status=args.status,
                 reviewer_chain=args.reviewer_chain, skip_review_gate=args.skip_review_gate,
+                allow_ready_close=args.allow_ready_close, reason=args.reason,
             )
         elif args.cmd == "start":
             commands.cmd_start(repo_root=root, id=args.id, resume=args.resume)
diff --git a/tools/tasktool/commands.py b/tools/tasktool/commands.py
index 0a0d17c..aca1b14 100644
--- a/tools/tasktool/commands.py
+++ b/tools/tasktool/commands.py
@@ -338,6 +338,13 @@ def _start_item(qid: str, item, *, resume: bool = False) -> None:
     if getattr(item, "started", None) is None:
         item.started = _today()
 
+def _apply_ready_close_override(qid: str, item, *, reason: str | None) -> None:
+    if not reason or not reason.strip():
+        raise CommandError(f"{qid} ready-close override requires --reason")
+    ts = _dt.datetime.now().isoformat(timespec="seconds")
+    audit = f"[{ts}] ready-close override for {qid}: {reason.strip()}"
+    item.notes = (item.notes + "\n" + audit).strip() if item.notes else audit
+
 def cmd_start(*, repo_root: Path, id: str, resume: bool = False) -> None:
     with _write_context(repo_root) as write_root:
         p = _load(write_root)
@@ -350,6 +357,7 @@ def cmd_start(*, repo_root: Path, id: str, resume: bool = False) -> None:
 def cmd_set(
     *, repo_root: Path, id: str, status: str,
     reviewer_chain: Path | None = None, skip_review_gate: bool = False,
+    allow_ready_close: bool = False, reason: str | None = None,
 ) -> None:
     with _write_context(repo_root) as write_root:
         p = _load(write_root)
@@ -361,10 +369,12 @@ def cmd_set(
         if new_status == Status.DONE and kind in ("slice", "phase"):
             _apply_review_gate(repo_root, item, qid, kind, reviewer_chain, skip_review_gate)
         if new_status == Status.DONE and kind == "slice" and getattr(item, "started", None) is None:
-            raise CommandError(
-                f"{qid} must be started before close; run `tasktool start {qid}` first, "
-                f"or use `tasktool close {qid} --allow-ready-close --reason ...` if applicable"
-            )
+            if not allow_ready_close:
+                raise CommandError(
+                    f"{qid} must be started before close; run `tasktool start {qid}` first, "
[truncated: 183 additional lines]


---

You are acting as an independent senior engineering reviewer.

Review stance:
- Lead with findings, ordered by severity.
- Focus on correctness, consistency, implementation risk, missing acceptance
  gates, vague handoffs, ungrounded assumptions, unverified claims, and drift
  from the codebase.
- Give exact file/line references when possible.
- If the document is sound, say that clearly and list residual risks.
- Keep the review actionable. Avoid broad rewrites unless the current structure
  creates concrete risk.

Repository root:
/home/simon/Dev/sigreer/skills/superstar/.worktrees/p4-s2-lifecycle

Target kind:
post-phase

Review mode:
Post-phase review. Treat this as a closeout gate for a whole
phase. Compare the implementation, archive/TASKLIST updates, and verification
evidence against the phase spec/plan. Prioritize: unresolved acceptance
criteria, stale docs, missing archive notes, cross-cutting tracker drift,
deferred gates without justification, and regressions outside the phase scope.

Target document:
docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md

Additional context files:
- docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md
- docs/tasklist.json

Review output contract:
1. Findings
   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
     stable if this review is iterated in subsequent rounds.
   - Mark severity inline: `Severity: blocking | important | minor | nit`.
2. Open questions / assumptions
3. Suggested document edits
4. Verification gaps / commands that should be run, if any
5. Overall verdict: one of "ready", "ready with small edits", or "revise"

Read the files from disk. Do not rely only on the snippets in this prompt.


## Target Preview

### docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md

    1	# P4 — Tasktool Coordination and Lifecycle Authority
    2	
    3	**Status:** proposed
    4	**Date:** 2026-05-19
    5	**TASKLIST entry:** `P4` in `docs/tasklist.json`
    6	
    7	## Objective
    8	
    9	Make `tasktool` the enforced authority for two workflow rules that are currently left to agent discipline:
   10	
   11	1. Parallel implementation worktrees must not own `docs/tasklist.json` mutations.
   12	2. Active slices and tasks must pass through `in_progress` instead of jumping from `ready` to `done`.
   13	
   14	The intended outcome is that agents can keep using normal `tasktool` commands from whatever checkout they are working in, but the tool decides where writes land and which lifecycle transitions are valid.
   15	
   16	## Problem
   17	
   18	`docs/tasklist.json` is the single source of truth, but linked implementation worktrees currently mutate their local copy. When those branches merge back to `main`, tasklist updates from multiple agents collide as byte-level JSON diffs. This is predictable because each worktree was forked from a stale snapshot of the tracker.
   19	
   20	The same workflow has a status-quality issue: agents rarely mark slices or tasks `in_progress`. Rows remain `ready` until they are closed, which makes `tasktool list --open`, `phase-status`, and human progress scans much less useful.
   21	
   22	These are not independent usability nits. They expose the same architectural gap: `tasktool` has the canonical data model, but it does not yet enforce the coordinator lifecycle strongly enough.
   23	
   24	## Design Summary
   25	
   26	`tasktool` gains two linked capabilities:
   27	
   28	- **Authoritative checkout routing.** Mutating commands invoked from implementation worktrees are applied to a configured authoritative checkout, normally the project `main` checkout. Every authoritative-mode write uses the same lock, including commands invoked directly from the authoritative checkout. Worker worktrees treat `docs/tasklist.json` as a read-only mirror.
   29	- **Lifecycle start enforcement.** `tasktool start <id>` becomes the normal way to begin work. Slice close is allowed only after a slice has been observed `in_progress`, unless an explicit bypass is supplied and recorded.
   30	
   31	The skills are updated to describe the new command surface, but correctness does not depend on prose. The CLI enforces the rules.
   32	
   33	## Configuration
   34	
   35	Add a tracked project config file:
   36	
   37	```json
   38	{
   39	  "schema_version": 1,
   40	  "tasklist": {
   41	    "mutation_mode": "authoritative-checkout",
   42	    "authoritative_branch": "main"
   43	  }
   44	}
   45	```
   46	
   47	The default path is `.tasktool/config.json`. This file is intended to be committed because it contains project policy only, not machine-local absolute paths. If no config exists, current behavior remains unchanged so existing projects do not break abruptly.
   48	
   49	Field semantics:
   50	
   51	- `mutation_mode`
   52	  - `local`: existing behavior; mutate the current checkout.
   53	  - `authoritative-checkout`: route mutating commands from linked worktrees to `authoritative_root`.
   54	- `authoritative_branch`: branch the authoritative checkout must be on when accepting writes.
   55	
   56	Machine-local root discovery:
   57	
   58	1. If `TASKTOOL_AUTHORITY_ROOT` is set, use it.
   59	2. Otherwise inspect `git worktree list --porcelain` and find the checkout whose branch is `authoritative_branch`.
   60	3. If exactly one checkout matches, use it.
   61	4. If none or more than one match, fail closed and print the exact `TASKTOOL_AUTHORITY_ROOT=/path/to/checkout` override to use.
   62	
   63	`tasktool config init-authority --branch main` writes or updates `.tasktool/config.json`. It does not write absolute paths. A separate untracked `.tasktool/local.json` may be added later, but P4 should not require it.
   64	
   65	## Mutating Commands
   66	
   67	The routing layer applies to all commands that write `docs/tasklist.json`:
   68	
   69	- `init`
   70	- `create phase|slice|task|cross`
   71	- `set`
   72	- `start`
   73	- `close`
   74	- `block`
   75	- `unblock`
   76	- `deps`
   77	- `ratify`
   78	- `planning-path`
   79	- `note`
   80	- `ref`
   81	- `title`
   82	- `archive-phase`
   83	- `import`
   84	- `validate --normalise`
   85	
   86	Read commands keep using the current checkout by default, but they should warn when authoritative routing is configured and the current worktree copy is older than the authoritative copy. A follow-up may add `--source authoritative|local`; P4 does not need it.
   87	
   88	## Routing Rules
   89	
   90	For every mutating command:
   91	
   92	1. Discover the current repository root and git common directory.
   93	2. Load `.tasktool/config.json` if present.
   94	3. If `mutation_mode` is absent or `local`, mutate the current checkout.
   95	4. Resolve `authoritative_root` via the machine-local discovery rules.
   96	5. Acquire an exclusive lock under the common git directory before loading tasklist data.
   97	6. Validate that `authoritative_root` exists, is a git checkout for the same repository, is on `authoritative_branch`, and has no unresolved merge.
   98	7. Validate that `authoritative_root/docs/tasklist.json` is not dirty in a way that cannot be attributed to tasktool's own current command.
   99	8. Load and mutate `authoritative_root/docs/tasklist.json`, even if the invocation already came from that checkout.
  100	9. Save canonical JSON and best-effort stage the authoritative path.
  101	10. Print a concise routing message only when the invocation root differs from the authoritative root.
  102	
  103	The implementation should centralize this routing in one module so command functions do not each grow git-worktree logic.
  104	
  105	The lock is mandatory for every authoritative-mode mutation. Direct `main` checkout invocations and worker-routed invocations contend on the same lock, preventing interleaved read-modify-write cycles.
  106	
  107	## Two-Root Command Contract
  108	
  109	Commands in authoritative mode have two roots:
  110	
  111	- `invocation_root`: the checkout where the user or agent ran the command.
  112	- `write_root`: the authoritative checkout whose `docs/tasklist.json` is mutated.
  113	
  114	User-supplied file paths and reviewer-chain discovery are interpreted relative to `invocation_root`. Tasklist load/save/stage happens in `write_root`. This applies to `close` and to `set --status done`, because both routes can invoke review-gate checks.
  115	
  116	Explicit reviewer-chain paths may be absolute or relative, but they must resolve inside `invocation_root`. Paths outside the repository are refused. The value recorded into tasklist is always repo-relative from `invocation_root`.
  117	
  118	## Reviewer Chains From Worktrees
  119	
  120	`tasktool close <slice-id>` and `tasktool set <id> --status done` must preserve review-gate semantics when invoked from an implementation worktree.
  121	
  122	The gate should evaluate reviewer artifacts relative to the invocation checkout because that is where post-slice review was run. The resulting `reviewer_chain` recorded into the authoritative tasklist remains a repo-relative path, for example:
  123	
  124	```text
  125	docs/reviewer/p11-s4c-nav-footer-P11-S4c-post-slice
  126	```
  127	
  128	If the reviewer chain path is outside the repository, the command refuses it. If the same repo-relative reviewer chain does not exist in the authoritative checkout yet, close still records the relative path; merge-back will bring the artifacts over. The JSON record must not depend on absolute worktree paths.
  129	
  130	## Lifecycle Enforcement
  131	
  132	Add:
  133	
  134	```sh
  135	tasktool start <id>
  136	```
  137	
  138	Behavior:
  139	
  140	- Accepts phases, slices, tasks, and cross-cutting items.
  141	- Resolves short IDs exactly like `set`.
  142	- Refuses `done` items.
  143	- Refuses `blocked` slices unless `--resume` is supplied, in which case it clears `blocked_on` and sets `in_progress`.
  144	- Sets `status: in_progress`.
  145	- Records a machine-readable lifecycle marker that proves the item was started before close.
  146	
  147	The marker should be explicit rather than inferred from current status, because a row may later move from `in_progress` to `blocked` and back. Add `started: YYYY-MM-DD | null` to phase, slice, task, and cross-cutting records. Existing files load with `started: null`.
  148	
  149	`tasktool set <id> --status in_progress` becomes a compatibility alias for `tasktool start <id>`. It sets `started` using the same rules and notifications. This keeps older skill prose or human muscle memory from producing a visible `in_progress` state that later fails close because no start marker exists.
  150	

[truncated: 55 additional lines]

<!-- superstar-prompt:end -->