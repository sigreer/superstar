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

### F1 — Authoritative validation runs outside the lock (TOCTOU window). Severity: minor
`_write_context` in `tools/tasktool/commands.py:94–114` calls `_resolve_write_root` *first*, which performs `find_authoritative_root` + `validate_authoritative_checkout` (branch, repo identity, merge state). Only afterward is `tasktool_lock` acquired and the dirty-state check repeated. Between validation and lock acquisition, another process can switch branches or introduce a merge conflict on the authoritative checkout. The dirty-state recheck under the lock is good; the branch/merge recheck is missing. For full safety, the validation that depends on shared mutable state (`git_current_branch`, `has_unmerged_paths`) should also be re-executed inside the lock.

### F2 — `cmd_config_init_authority` writes config without verifying it's running on the authoritative branch. Severity: minor
`tools/tasktool/commands.py:118–126` writes `.tasktool/config.json` into `repo_root` regardless of which checkout invoked it, then best-effort stages it. If invoked from an implementation worktree, the config gets committed onto that worktree's branch instead of `main`. This is recoverable but easy to do by accident and contradicts the spec's "tracked project policy" intent. A guard ("refuse unless current branch == `--branch` or `--force`") would close the foot-gun.

### F3 — `tasklist_has_unsafe_dirty_state` accepts untracked tasklist as "clean". Severity: minor
`tools/tasktool/worktree.py:82–93` walks `git status --porcelain` and only flags lines whose worktree column (`line[1]`) is not space. An untracked `docs/tasklist.json` produces `?? docs/tasklist.json`, where `line[1] == '?'`, which is treated as unsafe — that's correct. But a previously-committed-then-deleted file produces ` D` and is also flagged unsafe — that probably matches intent. Mostly fine. However, the parser also assumes `len(line) >= 2`; rename entries (`R `) have additional pathspec semantics. Unlikely to bite docs/tasklist.json in practice. Worth a brief comment that this is path-specific output, not whole-tree.

### F4 — `find_authoritative_root` honors `TASKTOOL_AUTHORITY_ROOT` without verifying it's the authoritative branch. Severity: minor
`worktree.py:59–69` returns the env override unconditionally. `validate_authoritative_checkout` then catches the branch/repo mismatch, so it's not exploitable; but the env override also bypasses the "same repository" check until validation. Acceptable since validation runs immediately after — flagging only for clarity. The plan's spec wording "fail closed" is honored.

### F5 — `docs/tasklist.json` is staged-uncommitted at the post-slice gate. Severity: minor / workflow
`git status` shows `M  docs/tasklist.json`. This is the leftover of `tasktool create phase/slice` for P4 (visible in `git diff main HEAD`). On the authoritative `main` checkout this is allowed by `tasklist_has_unsafe_dirty_state`, but it should not be left dangling at slice close — either commit it with the closeout commit or note explicitly why it remains staged. The branch is the `p4-s1-tasktool-authority` worktree, not `main`, so the new routing logic would refuse subsequent worker writes against this state.

### F6 — P4.S1 never recorded `in_progress`. Severity: minor (S2 territory)
`docs/tasklist.json` shows `P4.S1.status == "ready"` and there is no slice `started` field yet (that's P4.S2). The spec calls out this lifecycle gap as a known issue, and P4.S1 was not chartered to fix it — so this is not blocking for P4.S1 close, but the closeout commands in the plan (`tasktool close P4.S1 --reviewer-chain …`) will close directly from `ready`. Reasonable for this slice but worth noting for the reviewer ledger.

### F7 — `.tasktool/config.json` is not present in this repo. Severity: minor
P4.S1 ships the code to consume the config, but the repo itself never opts in. That's intentional (the spec says "If no config exists, current behavior remains unchanged"), and an explicit `tasktool config init-authority --branch main` should be a separate commit. Mentioning here so reviewers don't expect the new routing to be exercised yet in this very worktree.

### F8 — Plan checkboxes never ticked. Severity: nit
All `- [ ]` items in `docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md` for Tasks 1–3 remain unchecked despite the corresponding commits landing (`318838f`, `6ddfaef`, `1903de5`). Not load-bearing, but the plan acts as a checklist and is inconsistent with reality.

### F9 — `_resolve_write_root` loads config twice. Severity: nit
`_resolve_write_root` calls `load_config`; `_write_context` then uses the returned `mode`. The earlier draft in the plan called `load_config` a second time inside `_write_context` — current code is cleaner (single load via the tuple return). Just noting that the plan text in the markdown does not match the implemented code (the plan still shows the older double-load shape).

### F10 — Empty `docs/tasklist.json` mirror in worker is not enforced. Severity: minor
Spec §"Routing Rules" treats `docs/tasklist.json` in worker worktrees as a read-only mirror. Nothing in the implementation prevents a worker from manually editing it; only mutating *tasktool* commands route. That's consistent with what the spec promises ("Worker worktrees treat … as a read-only mirror" — by convention, not file ACLs). Acceptable, but consider a docs note: drift between worker and authoritative copies will silently diverge until merge.

## 2. Open questions / assumptions

- Q1: Should `cmd_config_init_authority` refuse to run from a non-authoritative checkout, or is the assumption that humans always init from `main`?
- Q2: Should the lock cover `git_current_branch` re-check (F1)? In practice slices won't switch branches mid-run, but the spec says "Validate that authoritative_root … is on `authoritative_branch`" without specifying ordering vs. the lock.
- Q3: Tests cover linked-worktree routing but not the `TASKTOOL_AUTHORITY_ROOT` env override path end-to-end. Is that intentional?

Assumption: the test suite passes (could not run in plan mode — see §4).

## 3. Suggested document edits

- Tick `- [ ]` boxes for Task 1–3 steps that have been committed (F8).
- Update Task 3 Step 2 code block in the plan to match the actual single-load `_resolve_write_root` returning `(path, routed, mode)` (F9).
- Add a sentence to the spec / plan note that `validate` without `--normalise` reads from the invocation checkout in routed mode (currently implicit — `cmd_validate` only routes when `normalise=True`).
- Add a "Closeout commit hygiene" bullet to P4.S1 closeout: ensure `docs/tasklist.json` is committed (no staged-only deltas at gate time) (F5).

## 4. Verification gaps / commands to run

- `python -m pytest tools/tasktool/tests -v` — could not run under plan mode; confirm green before close.
- `python -m pytest tools/tasktool/tests/test_worktree_authority.py -v` specifically.
- `tools/tasktool/tasktool validate --strict-format` — required by closeout checklist.
- Manual smoke: run `tasktool config init-authority --branch main` *from* `.worktrees/p4-s1-tasktool-authority/` and observe that the file lands in the worktree directory rather than `main` — verifies the F2 concern empirically.
- Lock-contention test under real parallel invocations (the existing test simulates by pre-creating the lock file; consider one that races two `tasktool set` processes).

## 5. Overall verdict

**ready with small edits**

P4.S1 delivers the spec's mandatory pieces: a config module, worktree detection, fail-closed authority discovery, a shared lock under `git_common_dir`, and routing of every mutating command (including `archive-phase`, `import`, `validate --normalise`, and the reviewer-gate path). Tests directly cover each acceptance criterion called out in the spec for S1. Remaining issues are hardening (F1, F2), documentation hygiene (F5, F8, F9), and one un-exercised happy path (Q3). None are blocking for the slice to close; address F1/F2 either inside this slice or as a small follow-up before P4.S2 builds on top.
