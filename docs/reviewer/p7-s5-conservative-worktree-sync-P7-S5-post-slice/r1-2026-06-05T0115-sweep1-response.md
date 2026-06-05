# Review — 2026-06-04-P7-S5-conservative-worktree-sync.md (post-slice, round 1)

- Target: `docs/plans/2026-06-04-P7-S5-conservative-worktree-sync.md`
- Request: `docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice/r1-2026-06-05T0115-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

I have enough to produce the review. Repo state verified: all five implementation commits present, code matches spec, tests are well-formed and comprehensive. Plan-mode/sandbox blocked me from executing the suite, so I'll flag that as a verification gap rather than a code defect.

---

Findings

F1 — No visible evidence the full verification gate (Task 6.1/6.2) actually passed. Severity: important
The slice's own acceptance gate requires `python -m pytest tools/tasktool/tests -q` (full suite, not just the focused file) and `tasktool validate` to be green (plan lines 640–654; spec §9). The reviewer chain `chain.json` shows `"rounds": []` and `sweep_checkpoints` both `pending`, and there is no committed run output. I could not execute the suite from the review environment (sandbox denied `pytest`). The focused tests `tools/tasktool/tests/test_worktree_sync.py` are well-formed and the implementation is internally consistent, so this is a *gap in evidence*, not a demonstrated failure — but it must be closed (full suite + `tasktool validate` shown green, plus the `worktree status P7.S5 --integration` dogfood in 6.3) before `tasktool close P7.S5`. This is the only item standing between the slice and a clean close.

F2 — Plan text (Task 2.3) no longer matches the shipped dirty-check predicate. Severity: minor
Plan lines 250–256 specify the staged-only test as `code[0] != " " and code[1] == " "`. The shipped helper (`tools/tasktool/worktree.py:231-235`) instead uses `code in {"A ", "M "}`, introduced by the extra commit `aa3531f "tighten staged tasklist sync allowance"` that is not represented in the plan. The shipped version is *stricter and better* (it correctly keeps staged renames/deletes/`MM`/`R ` dirty, matching the comment at `worktree.py:248-249` and the refusal test `test_dirty_helper_refuses_unstaged_tasklist_and_untracked_files`). No code change needed; this is plan/implementation drift on a historical artifact. Worth a one-line note in the plan or closeout so the divergence is intentional and recorded, not silent.

F3 — `_run_sync_git` hard-overrides `GIT_EDITOR`/`GIT_SEQUENCE_EDITOR` rather than `setdefault`. Severity: nit (positive divergence — confirm intent)
Plan line 495 used `env.setdefault("GIT_EDITOR", "true")`. Shipped code (`commands.py:2927-2929`) uses unconditional `env["GIT_EDITOR"] = "true"` plus `env["GIT_SEQUENCE_EDITOR"] = "true"`. This is the correct call: the test harness exports `GIT_EDITOR=false` (plan line 71), which `setdefault` would have left in place and could wedge a non-`--no-edit` path. Flagging only so the divergence from the plan is acknowledged as deliberate hardening, consistent with spec §6 ("a subprocess environment that cannot open an editor").

F4 — In-place sync with base genuinely ahead *and* staged `docs/tasklist.json` is an untested edge. Severity: minor
The in-place success test (`test_sync_in_place_allows_staged_tasklist_and_advances_base_sha`) exercises only the already-up-to-date merge (`commands.py` path where `git merge` is a no-op and never touches the index). If the in-place checkout were actually behind base *and* base modified `docs/tasklist.json` while a staged tasklist change sat in the index, `git merge` would abort with "Your local changes would be overwritten." That is a safe failure (non-zero exit → `worktree_base_sha` unchanged via the F-invariant), so there is no correctness hole, but the behavior is undocumented and unverified. Acceptable to leave as a noted residual risk; spec §5/§6 don't promise to handle it.

F5 — Live slice status is not observable from this branch (authoritative-routing artifact, not a defect). Severity: nit
The committed `docs/tasklist.json` in this worktree shows `P7.S5` as `"status": "ready"`, `"started": null`, no `worktree_base_sha`. That is expected: `tasktool start` writes status/`worktree_base_sha` to the authoritative checkout (`/home/simon/Dev/sigreer/skills/superstar`, on `main`), which is outside this review's sandbox and so cannot be inspected here. `git diff main...HEAD` correctly shows zero tasklist changes (4 files, +420). No drift — noting it so the "ready/null" row is not misread as the slice never having been started.

Positive confirmations (no action):
- CLI parser and dispatch are wired correctly: required mutually-exclusive `--merge`/`--rebase` (`cli.py:132-136`), dispatch writes command output to stdout (`cli.py:451-459`).
- Refusal ladder matches spec §5 rules 1–8: non-slice (`commands.py:2958`), missing `worktree_base_sha` (`2905-2907`), unresolvable base (`2908-2911`), unhealthy linked worktree (`_sync_target_path` via `_health_for`, `2894-2897`), unmerged paths (`2912-2913`), dirty target (`2915-2920`), unstaged authoritative tasklist (`2921-2922`).
- Success path integrates the captured pre-op SHA (`current_branch_head_sha`), runs exactly one non-interactive git op without holding the lock, then re-enters `_write_context` to set `worktree_base_sha = base_head` — faithful to spec §6 "integrate the SHA, not the moving ref."
- Failure invariant holds: `_run_sync_git` raises before the `_write_context` block, so `worktree_base_sha` cannot advance on conflict; covered by both merge and rebase conflict tests (`test_worktree_sync.py:225-240` and the merge equivalent).
- Test coverage maps onto every item of spec §9 (parser both/neither, merge success, rebase success, in-place + staged tasklist, missing base sha, dirty refusal, unstaged-vs-staged tasklist, conflict no-advance, post-sync `--integration` window clears).
- All five implementation commits (`8019daf`, `e6f3cf3`/`aa3531f`, `90551b1`, `aeebf0b`, `da89931`) are present and scoped to the four declared files.

Open questions / assumptions
- I assume the focused `test_worktree_sync.py` passes as written; I could not run it (sandbox denied `pytest`). F1 asks the implementer to supply that evidence plus the full-suite/`validate` run.
- I assume `parse_id("P7.S5")[0] == "slice"` and `parse_id("P1")[0] != "slice"`; this underpins the non-slice refusal and is exercised by `test_sync_refuses_non_slice_id`, but unconfirmed without a run.
- I assume the authoritative checkout on `main` records `P7.S5` as `in_progress` with a `worktree_base_sha`; not inspectable from this sandbox (F5).

Suggested document edits
- Plan: add a short note under Task 2 that the shipped staged-tasklist predicate was tightened to `code in {"A ", "M "}` (commit `aa3531f`) so renames/deletes/partially-staged tasklist stay dirty (F2).
- Plan: note that `_run_sync_git` hard-sets `GIT_EDITOR`/`GIT_SEQUENCE_EDITOR` (not `setdefault`) to stay non-interactive even when the caller exports an editor (F3).
- Spec §5/§6 (optional): one sentence acknowledging that an in-place sync which is behind base and carries a staged tasklist change will safe-fail on `git merge` rather than auto-stash (F4).

Verification gaps / commands to run before close
- `python -m pytest tools/tasktool/tests/test_worktree_sync.py -q` (focused — expect all pass)
- `python -m pytest tools/tasktool/tests -q` (full suite — Task 6.2, currently unevidenced)
- `tasktool validate` (Task 6.2 — expect no errors)
- `tasktool worktree status P7.S5 --integration` (Task 6.3 dogfood)
- Then Task 6.4–6.5: register the reviewer chain artifact, `tasktool artifact status P7.S5 --strict`, and `tasktool close P7.S5`.

The implementation is complete, faithful to the spec, and well-tested by inspection; the only thing missing for a clean close is the recorded full-suite + `validate` verification evidence (F1), with two small plan-text reconciliations (F2, F3).

Overall verdict: ready with small edits
