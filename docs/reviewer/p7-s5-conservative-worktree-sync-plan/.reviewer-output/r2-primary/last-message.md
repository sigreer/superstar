I've read the plan, the spec, and grounded every prior finding against the actual source (`commands.py`, `worktree.py`, `ids.py`). The on-disk plan has been substantially revised since round 1 (the resolution report was "MISSING", but the file itself now contains the fixes). Here is my round-2 incremental review.

---

Review — 2026-06-04-P7-S5-conservative-worktree-sync.md (plan, round 2)

- Target: `docs/plans/2026-06-04-P7-S5-conservative-worktree-sync.md`
- Mode: incremental verification of r1 findings F1–F7
- Status: `ok`

Findings

F1 — RESOLVED (was: blocking). `test_sync_refuses_missing_worktree_base_sha` (plan lines 292–302) now calls `start_linked(repo)` first, then pops `worktree_base_sha` from the slice row and re-stages the tasklist. I traced the flow: `start_linked` records a live worktree, so `_sync_target_path` (plan 356–364) returns the live path rather than raising "no recorded worktree", and `_preflight_worktree_sync` reaches its first guard — the missing-base-SHA check (plan 372–373) — which raises `"{qid}: worktree_base_sha is not recorded..."`. The assertion `"worktree_base_sha" in (r.stdout + r.stderr)` now matches the branch it names. The 3.4 expectation ("5 passed") is consistent with the five refusal tests in 3.1.

F2 — RESOLVED (was: important). The slice-kind refusal is hoisted above target resolution: `cmd_worktree_sync` (plan 400–401) runs `if parse_id(qid)[0] != "slice"` before `_sync_target_path` (plan 403). I confirmed `_find_item` (`commands.py:619–655`) resolves a phase id `P1` to `qid="P1"` with `parse_id[0]=="phase"`, so `test_sync_refuses_non_slice_id` (plan 305–309) reaches the dedicated `"worktree sync only supports slices"` message — it is no longer dead code. Rule 3 is also now tested: `test_sync_refuses_unhealthy_recorded_worktree` (plan 312–318) removes the worktree dir, and I verified `_health_for` (`commands.py:2674–2695`) returns `"missing-path"` for a removed recorded path, so `_sync_target_path` raises `"recorded worktree is not live"` as asserted.

F3 — RESOLVED (was: minor). The Scheduling section's "test scope note" (plan line 21) now states that routed/authoritative-checkout locking is out of test scope and why, with the row update still going through `_write_context`. This matches the convention in `test_worktree_integration.py`.

F4 — RESOLVED (was: minor). `working_tree_dirty_for_sync` carries the comment (plan 269–271) that the staged-tasklist allowance recognizes only plain add/modify; renames/deletes/quoted paths stay dirty. I checked the porcelain parse logic against the staged-only predicate (`code[0] != " " and code[1] == " "`) — staged-only `M ` is skipped, ` M`/`MM`/`??` are correctly retained.

F5 — RESIDUAL nit (unchanged, non-blocking). The preflight still raises `"authoritative docs/tasklist.json has unstaged changes"` (plan 388) while `_ensure_authoritative_tasklist_clean` (`commands.py:184–186`) owns a longer variant. Harmless duplication — in local test mode only the preflight string fires. No action required; a one-line "see also" comment would be a courtesy, not a gate.

F6 — RESOLVED (was: minor). `test_sync_in_place_allows_staged_tasklist_and_advances_base_sha` (plan 579–593) now carries the explicit note (591–593) that this is an up-to-date merge of HEAD into itself with staged tracker bytes present. I verified the assumption holds: `_apply_start_in_place` (`commands.py:1015–1030`) leaves the repo on `main` (no slice branch), records base SHA, and does not switch branches. After `advance_main` commits to `main` in the repo root, the captured `base_head` equals repo HEAD, so `git merge --no-edit <HEAD>` is an "Already up to date" no-op that exits 0 before any index check — the staged tasklist does not block it.

F7 — RESOLVED (was: minor). `test_sync_rebase_conflict_leaves_worktree_base_sha_unchanged` (plan 563–576) is added alongside the merge-conflict test, asserting `"git rebase failed"` and unchanged `worktree_base_sha`. The error string is produced by `_run_sync_git` (`f"git {strategy} failed; ..."`, plan 504), and the base-SHA write happens only after a zero-exit git op, so the invariant holds for both strategies.

Regression scan (fixes did not break the success path)

I verified two cross-cutting assumptions the success/conflict tests depend on, both sound:
- `_save` (`commands.py:195–199`) stages `docs/tasklist.json` on every write, so after `start` the authoritative tracker is staged-only — `tasklist_has_unsafe_dirty_state` (`worktree.py:110`) treats that as safe, and rule 8 does not spuriously reject the merge/rebase success tests.
- `_authoritative_parent_branch` (`commands.py:3102–3111`) returns the config default `"main"`, so the success assertions `"integrated main at {base_head}"` (plan 447, 462) match the output template at plan 519.

All reused helpers the new code references exist with the assumed names: `working_tree_dirty`, `has_unmerged_paths`, `current_branch_head_sha`, `tasklist_has_unsafe_dirty_state`, `git_current_branch`, `_git` (`worktree.py:186,105,34,110,30,14`). No new finding IDs are warranted.

Open questions / assumptions
- None blocking. The one local-environment assumption (in-place no-op merge exits 0 with a dirty index, F6) is now documented in the test and consistent with git's up-to-date early return; worth a single local confirmation during implementation but not a plan defect.

Suggested document edits
- Optional only: add a one-line "duplicate of `_ensure_authoritative_tasklist_clean` prefix; intentional" comment at the preflight raise (plan 388) to close the F5 nit. Not required for approval.

Verification gaps / commands that should be run
- The per-task pass counts are now internally consistent (3.4 → 5 passed; 4.4 → 3 passed; 5.2 → 3 passed). Implementer should still run the Task 6.2 full gate (`python -m pytest tools/tasktool/tests -q` + `tasktool validate`) as written.

Overall verdict: ready