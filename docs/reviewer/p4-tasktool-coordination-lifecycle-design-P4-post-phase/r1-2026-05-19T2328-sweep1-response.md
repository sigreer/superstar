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

### F1 — Phase P4 is not actually closed or archived  **Severity: blocking**
`docs/tasklist.json` shows P4 with `status: "ready"`, `closed: null`, `started: null`, `phase_reviewer_chain: null`, and no entry in `archived_phases`. Both slices are `done`, but the phase itself was never moved through `in_progress`/`done` and has not been archived. A post-phase gate cannot be closed in this state.
- Required: `tasktool start P4` (or accept ready-close on the phase via `archive-phase`), `tasktool close P4 --reviewer-chain docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase`, then `tasktool archive-phase P4`.
- Also: `phase_reviewer_chain` must be persisted to the post-phase chain dir (currently untracked).

### F2 — P4.S1 was closed without a `started` marker  **Severity: important**
`P4.S1.started: null`, `status: "done"`. The spec/plan added the enforcement only in P4.S2, so this happened under the older rules — not a code defect, but it is a tracker artifact that violates the invariant the phase just introduced. Two options, pick one and apply: (a) backfill `started` for P4.S1 with a one-time normalisation, or (b) add an explicit note recording it as a grandfathered close. Leaving it as-is means the canonical tracker contains a slice that fails the rule the phase exists to enforce — bad dogfooding signal.

### F3 — `set --status done` bypass asymmetry vs `close`  **Severity: important**
`commands.py:363-367` refuses `set --status done` on a never-started slice and tells the user to either `start` first or use `close --allow-ready-close --reason ...`. But `cmd_set` itself has no `--allow-ready-close/--reason` parameters (`commands.py:350`, `cli.py` set parser), so the suggested bypass is only reachable via `close`. Spec Acceptance: "`set P1.S1 --status done --reviewer-chain ...` uses the same two-root reviewer-gate contract as `close`" — the gate contract matches, but the ready-close override does not. Either: (a) document explicitly that `set --status done` has no bypass (and `close` is the only path) and update the error message to drop the misleading suggestion of a flag combination that doesn't exist on `set`, or (b) add matching `--allow-ready-close/--reason` to `set`. Option (a) is fine and cheaper.

### F4 — This repo does not dogfood authoritative routing  **Severity: minor**
There is no `.tasktool/config.json` at the repo root, so the project still mutates in `local` mode. P4 implemented the capability; consider committing `.tasktool/config.json` (via `tasktool config init-authority --branch main`) as part of phase closeout so superstar itself runs under the new rules going forward. The spec said existing projects don't need to migrate "abruptly," so this isn't a blocker, but the phase ships without ever proving the routing works on its own tasklist.

### F5 — Post-phase reviewer chain directory is untracked  **Severity: minor**
`docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase/` shows in `git status` as untracked. Expected during the review round itself, but it must be committed before `archive-phase` so the archived note has a stable reviewer link.

### F6 — Spec acceptance: validate + test evidence not produced in this review  **Severity: minor**
Acceptance criteria require `tasktool validate --strict-format` to pass and the test matrix (authority config, worktree routing, lock contention, lifecycle start, ready-close) to be green. The relevant test files exist (`test_authority_config.py`, `test_worktree_authority.py`, `test_lifecycle_start.py`, `test_skill_tasktool_lifecycle_docs.py`) but I could not execute them in this plan-mode review session. Closeout must run them and record the result. See section 4.

### F7 — `cmd_start` accepts phases per spec but lifecycle for phases is not exercised by tasklist  **Severity: nit**
Spec says `start` accepts phases. The implementation accepts them, but `P4` itself was never started, and the close-time enforcement explicitly excludes phases. Confirm intent: either remove phase support from `start` (it is dead surface area) or actually require `tasktool start P4` at phase kickoff and document it in `phase-planning`/`writing-plans`. Right now both paths exist and neither is exercised.

### F8 — Spec uses `planning_path` for the spec doc; `spec_path` left null  **Severity: nit**
P4 record has `planning_path: "docs/specs/.../p4-...-design.md"` but `spec_path: null`. The same pattern exists for P3, so this seems intentional (`planning_path` is the umbrella). Worth flagging because the field name `spec_path` reads like "where the spec lives" — a future reader will be confused.

## 2. Open Questions / Assumptions

- Is it acceptable to grandfather P4.S1's missing `started` marker, or do you want `tasktool` to gain a one-time backfill helper? (F2)
- Should `set --status done` ever support `--allow-ready-close`, or is the asymmetry deliberate to force the explicit `close` path? (F3)
- Does the closeout intend to flip this repo to authoritative routing in the same commit, or defer? (F4)
- Should `tasktool start <phase>` be retained as a real lifecycle hook for phases, or pruned? (F7)

## 3. Suggested Document Edits

- **Spec, Lifecycle Enforcement section:** add a sentence clarifying that the ready-close override is only exposed on `tasktool close`, not on `tasktool set --status done` (resolving F3 toward option (a)).
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

The implementation and skill changes look coherent and the slice-level work landed cleanly, but the phase itself has not been closed or archived in `docs/tasklist.json`, P4.S1 carries `started: null` after the very rule the phase enforces, and the `set` vs `close` bypass asymmetry produces a misleading error message. Address F1–F3 (and run the verification commands in §4) and a follow-up round should reach "ready" quickly.
