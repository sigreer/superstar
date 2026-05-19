# Merged findings for r1

## Primary

# Review — 2026-05-19-p4-tasktool-coordination-lifecycle.md (post-slice, round 1)

- Target: `docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md`
- Request: `docs/reviewer/p4-tasktool-coordination-lifecycle-P4-S1-post-slice/r1-2026-05-19T2233-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

# Post-Slice Review — P4.S1 Authoritative Tasklist Mutations

## 1. Findings

**F1. Slice never observed `in_progress` start marker — out of scope but worth flagging. Severity: minor**
P4.S1 currently has `status: in_progress` in `docs/tasklist.json:247` (staged). This was set manually via `set --status in_progress`, which under the P4.S2 design will become an alias for `tasktool start` and also seed the new `started` marker. Since P4.S1 itself ships before the `started` field exists, P4.S1 will be closeable today without tripping the ready-close guard. Plan Task 6 Step 0 (`tasktool start P4.S2`) anticipates this for P4.S2. No action required for this slice; flagging so reviewer-of-reviewer understands the staged change is intentional.

**F2. `cmd_config_init_authority` bypasses `_write_context`. Severity: minor**
`tools/tasktool/commands.py:118-126` writes `.tasktool/config.json` directly to the invocation root, never routing through the authoritative checkout. That is reasonable for first-time bootstrap (no config means no routing yet), but if a worker invokes `config init-authority` after the config already exists on `main`, the worker writes a second copy that diverges until rebased. The acceptance criterion ("creates tracked project policy without absolute paths") is satisfied, but consider either documenting "run from `main` only" in the skill update (P4.S2) or adding a guard that refuses re-init from a non-authoritative checkout when a config already exists.

**F3. `_apply_review_gate` has a dead `write_root` parameter. Severity: nit**
`tools/tasktool/commands.py:280-311` takes `write_root: Path` but never uses it; the loaded project comes from the caller and `check_gate` runs against `invocation_root`. Remove the parameter or use it (e.g. to log the routed write target). Pure cleanup.

**F4. Branch and worktree resolution occurs outside the lock. Severity: minor**
`_resolve_write_root` (`commands.py:79-92`) calls `find_authoritative_root` and `validate_authoritative_checkout` before `tasktool_lock` is acquired in `_write_context` (lines 94-114). A concurrent `git checkout` on the authoritative checkout between resolve and lock could let a write proceed against a checkout that was momentarily on the expected branch. The race window is small and recovery is benign (worst case: the write proceeds and the user notices the branch later), but consider moving the branch validation inside the lock for safety.

**F5. `find_authoritative_root` env path is uncovered. Severity: nit**
`worktree.py:59-69` honors `TASKTOOL_AUTHORITY_ROOT` first. Tests cover the failure-closed path and the auto-discovery success path, but not the explicit env-override success path. Add one short test that points `TASKTOOL_AUTHORITY_ROOT` at the real authority and asserts the resolved root.

**F6. `test_routed_validate_normalise_updates_authority_only` diverges from the plan but is stronger. Severity: nit**
Plan Step 5 writes the compact JSON into the worker; the implementation (`test_worktree_authority.py:254-263`) writes it into the authority and stages it. This is actually correct — normalisation should touch the authority — but flag the deviation so future readers don't think the plan was skipped.

**F7. No explicit test that `same_repository(left, right)` returns False for unrelated repos. Severity: nit**
`worktree.py:34-38` is exercised only through the linked-worktree positive path. Add a negative test (two independent `git init`s) so the early-out in `validate_authoritative_checkout` (line 105-106) has coverage.

**F8. Plan documents `tasklist_dirty()` helper that exists but is unused. Severity: nit**
`worktree.py:77-79` defines `tasklist_dirty` but nothing in `commands.py` calls it; only `tasklist_has_unsafe_dirty_state` is used. Either drop the helper or note in the spec that it's a public utility for future commands.

**F9. Reviewer chain for this review is staged but incomplete. Severity: minor (process)**
`docs/reviewer/p4-tasktool-coordination-lifecycle-P4-S1-post-slice/` contains `chain.json` and a single primary request; no merged verdict file is present yet. The close command will refuse until the reviewer chain reflects a `ready` (or `ready with small edits`) verdict. This is expected at this stage — flagging only so the closeout script in Plan §P4.S1 Closeout Step 3 won't be run prematurely.

## 2. Open questions / assumptions

- Assumption: `tasktool validate --strict-format` and the full pytest suite were run before this review request was emitted. I could not execute them in plan mode; verify before close.
- Assumption: The decision to ship P4.S1 without configuring `.tasktool/config.json` for the superstar repo itself is intentional (the file is absent at `repo_root/.tasktool/`). If you want the routing live in this very repo, `tasktool config init-authority --branch main` from the `main` checkout still needs to run as a separate post-merge step.

## 3. Suggested document edits

- Plan, Task 1 Step 4 / Task 3 Step 2: add a sentence noting that `cmd_config_init_authority` intentionally does not route, and document the implication (re-init from a worker is currently allowed and produces a divergent file).
- Plan, Task 2: drop or annotate the now-unused `tasklist_dirty` helper.
- Plan, Task 3 Step 5: update the `validate --normalise` test snippet to match the as-implemented variant (write compact to authority, stage, then run from worker).

## 4. Verification gaps / commands

Run before `tasktool close P4.S1`:

```sh
python -m pytest tools/tasktool/tests -q
tools/tasktool/tasktool validate --strict-format
```

Add coverage (small):
- `TASKTOOL_AUTHORITY_ROOT` env-override happy path.
- `same_repository` negative case across two unrelated `git init`s.

Optional manual smoke from a fresh tmpdir: `config init-authority` → `git worktree add` → run every mutating subcommand from the worker and confirm the worker's `docs/tasklist.json` byte-equals its pre-write state. The existing `test_routed_create_note_ref_title_block_unblock_deps_ratify_and_planning_path` already covers this in CI; the manual run is to satisfy yourself before close.

## 5. Overall verdict

**ready with small edits** — the slice meets every P4.S1 acceptance criterion in the spec, the implementation tracks the plan closely, and routing/lock/two-root semantics are wired through every mutating command including `archive-phase` and `import`. The findings above are non-blocking cleanups and one cautionary note about `cmd_config_init_authority` re-init semantics. Address F2 and F3 as small follow-ups (in this slice or rolled into P4.S2's skill-doc commit), run the verification commands in §4, then proceed to close.


## Sweep 1

# Review — 2026-05-19-p4-tasktool-coordination-lifecycle.md (post-slice, round 1)

- Target: `docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md`
- Request: `docs/reviewer/p4-tasktool-coordination-lifecycle-P4-S1-post-slice/r1-2026-05-19T2233-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

Producing the post-slice review now. Plan mode blocks me from running the test suite, so verification gaps will be noted.

---

# Post-Slice Review — P4.S1 (Authoritative Tasklist Mutations)

## 1. Findings

### S1.F1 — Authoritative validation runs outside the lock (TOCTOU window). Severity: minor
`_write_context` in `tools/tasktool/commands.py:94–114` calls `_resolve_write_root` *first*, which performs `find_authoritative_root` + `validate_authoritative_checkout` (branch, repo identity, merge state). Only afterward is `tasktool_lock` acquired and the dirty-state check repeated. Between validation and lock acquisition, another process can switch branches or introduce a merge conflict on the authoritative checkout. The dirty-state recheck under the lock is good; the branch/merge recheck is missing. For full safety, the validation that depends on shared mutable state (`git_current_branch`, `has_unmerged_paths`) should also be re-executed inside the lock.

### S1.F2 — `cmd_config_init_authority` writes config without verifying it's running on the authoritative branch. Severity: minor
`tools/tasktool/commands.py:118–126` writes `.tasktool/config.json` into `repo_root` regardless of which checkout invoked it, then best-effort stages it. If invoked from an implementation worktree, the config gets committed onto that worktree's branch instead of `main`. This is recoverable but easy to do by accident and contradicts the spec's "tracked project policy" intent. A guard ("refuse unless current branch == `--branch` or `--force`") would close the foot-gun.

### S1.F3 — `tasklist_has_unsafe_dirty_state` accepts untracked tasklist as "clean". Severity: minor
`tools/tasktool/worktree.py:82–93` walks `git status --porcelain` and only flags lines whose worktree column (`line[1]`) is not space. An untracked `docs/tasklist.json` produces `?? docs/tasklist.json`, where `line[1] == '?'`, which is treated as unsafe — that's correct. But a previously-committed-then-deleted file produces ` D` and is also flagged unsafe — that probably matches intent. Mostly fine. However, the parser also assumes `len(line) >= 2`; rename entries (`R `) have additional pathspec semantics. Unlikely to bite docs/tasklist.json in practice. Worth a brief comment that this is path-specific output, not whole-tree.

### S1.F4 — `find_authoritative_root` honors `TASKTOOL_AUTHORITY_ROOT` without verifying it's the authoritative branch. Severity: minor
`worktree.py:59–69` returns the env override unconditionally. `validate_authoritative_checkout` then catches the branch/repo mismatch, so it's not exploitable; but the env override also bypasses the "same repository" check until validation. Acceptable since validation runs immediately after — flagging only for clarity. The plan's spec wording "fail closed" is honored.

### S1.F5 — `docs/tasklist.json` is staged-uncommitted at the post-slice gate. Severity: minor / workflow
`git status` shows `M  docs/tasklist.json`. This is the leftover of `tasktool create phase/slice` for P4 (visible in `git diff main HEAD`). On the authoritative `main` checkout this is allowed by `tasklist_has_unsafe_dirty_state`, but it should not be left dangling at slice close — either commit it with the closeout commit or note explicitly why it remains staged. The branch is the `p4-s1-tasktool-authority` worktree, not `main`, so the new routing logic would refuse subsequent worker writes against this state.

### S1.F6 — P4.S1 never recorded `in_progress`. Severity: minor (S2 territory)
`docs/tasklist.json` shows `P4.S1.status == "ready"` and there is no slice `started` field yet (that's P4.S2). The spec calls out this lifecycle gap as a known issue, and P4.S1 was not chartered to fix it — so this is not blocking for P4.S1 close, but the closeout commands in the plan (`tasktool close P4.S1 --reviewer-chain …`) will close directly from `ready`. Reasonable for this slice but worth noting for the reviewer ledger.

### S1.F7 — `.tasktool/config.json` is not present in this repo. Severity: minor
P4.S1 ships the code to consume the config, but the repo itself never opts in. That's intentional (the spec says "If no config exists, current behavior remains unchanged"), and an explicit `tasktool config init-authority --branch main` should be a separate commit. Mentioning here so reviewers don't expect the new routing to be exercised yet in this very worktree.

### S1.F8 — Plan checkboxes never ticked. Severity: nit
All `- [ ]` items in `docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md` for Tasks 1–3 remain unchecked despite the corresponding commits landing (`318838f`, `6ddfaef`, `1903de5`). Not load-bearing, but the plan acts as a checklist and is inconsistent with reality.

### S1.F9 — `_resolve_write_root` loads config twice. Severity: nit
`_resolve_write_root` calls `load_config`; `_write_context` then uses the returned `mode`. The earlier draft in the plan called `load_config` a second time inside `_write_context` — current code is cleaner (single load via the tuple return). Just noting that the plan text in the markdown does not match the implemented code (the plan still shows the older double-load shape).

### S1.F10 — Empty `docs/tasklist.json` mirror in worker is not enforced. Severity: minor
Spec §"Routing Rules" treats `docs/tasklist.json` in worker worktrees as a read-only mirror. Nothing in the implementation prevents a worker from manually editing it; only mutating *tasktool* commands route. That's consistent with what the spec promises ("Worker worktrees treat … as a read-only mirror" — by convention, not file ACLs). Acceptable, but consider a docs note: drift between worker and authoritative copies will silently diverge until merge.

## 2. Open questions / assumptions

- Q1: Should `cmd_config_init_authority` refuse to run from a non-authoritative checkout, or is the assumption that humans always init from `main`?
- Q2: Should the lock cover `git_current_branch` re-check (S1.F1)? In practice slices won't switch branches mid-run, but the spec says "Validate that authoritative_root … is on `authoritative_branch`" without specifying ordering vs. the lock.
- Q3: Tests cover linked-worktree routing but not the `TASKTOOL_AUTHORITY_ROOT` env override path end-to-end. Is that intentional?

Assumption: the test suite passes (could not run in plan mode — see §4).

## 3. Suggested document edits

- Tick `- [ ]` boxes for Task 1–3 steps that have been committed (S1.F8).
- Update Task 3 Step 2 code block in the plan to match the actual single-load `_resolve_write_root` returning `(path, routed, mode)` (S1.F9).
- Add a sentence to the spec / plan note that `validate` without `--normalise` reads from the invocation checkout in routed mode (currently implicit — `cmd_validate` only routes when `normalise=True`).
- Add a "Closeout commit hygiene" bullet to P4.S1 closeout: ensure `docs/tasklist.json` is committed (no staged-only deltas at gate time) (S1.F5).

## 4. Verification gaps / commands to run

- `python -m pytest tools/tasktool/tests -v` — could not run under plan mode; confirm green before close.
- `python -m pytest tools/tasktool/tests/test_worktree_authority.py -v` specifically.
- `tools/tasktool/tasktool validate --strict-format` — required by closeout checklist.
- Manual smoke: run `tasktool config init-authority --branch main` *from* `.worktrees/p4-s1-tasktool-authority/` and observe that the file lands in the worktree directory rather than `main` — verifies the S1.F2 concern empirically.
- Lock-contention test under real parallel invocations (the existing test simulates by pre-creating the lock file; consider one that races two `tasktool set` processes).

## 5. Overall verdict

**ready with small edits**

P4.S1 delivers the spec's mandatory pieces: a config module, worktree detection, fail-closed authority discovery, a shared lock under `git_common_dir`, and routing of every mutating command (including `archive-phase`, `import`, `validate --normalise`, and the reviewer-gate path). Tests directly cover each acceptance criterion called out in the spec for S1. Remaining issues are hardening (S1.F1, S1.F2), documentation hygiene (S1.F5, S1.F8, S1.F9), and one un-exercised happy path (Q3). None are blocking for the slice to close; address S1.F1/S1.F2 either inside this slice or as a small follow-up before P4.S2 builds on top.

