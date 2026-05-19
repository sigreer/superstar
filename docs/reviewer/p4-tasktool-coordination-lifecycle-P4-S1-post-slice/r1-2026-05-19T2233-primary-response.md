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
