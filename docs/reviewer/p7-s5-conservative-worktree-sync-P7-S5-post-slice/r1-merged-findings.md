# Merged findings for r1

## Primary

# Review — 2026-06-04-P7-S5-conservative-worktree-sync.md (post-slice, round 1)

- Target: `docs/plans/2026-06-04-P7-S5-conservative-worktree-sync.md`
- Request: `docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice/r1-2026-06-05T0115-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

I have enough to complete the post-slice review. The implementation, tests, spec alignment, and repo/tracker state are all examined. Here is my review.

---

Findings

F1 — P7.S5 was never advanced through the tasktool lifecycle; `worktree_base_sha` is unrecorded for the very slice that manages it. Severity: important
The committed authoritative tasklist (both this branch and `git show main:docs/tasklist.json`) shows the `P7.S5` row at `docs/tasklist.json:372` with `status: "ready"`, `started: null`, no `worktree_base_sha`, no `worktree_path`/`worktree_branch`, and `reviewer_chain` still pointing at the *plan* chain (`docs/reviewer/p7-s5-conservative-worktree-sync-plan`, line 387). The plan's Scheduling preamble and Task 1.1 require `tasktool start P7.S5`, which should flip the row to `in_progress` and record `worktree_base_sha` (the sibling `P7.S4` row has one at `docs/tasklist.json:334`; `P7.S5` has none). Consequences: (a) the documented closeout in Task 6.5 (`tasktool close P7.S5`) will *refuse* — `cmd_close` raises "must be started before close" when `started is None` (`tools/tasktool/commands.py:1181`) unless `--allow-ready-close --reason` is used; (b) the slice that exists to advance `worktree_base_sha` never had its own recorded. Caveat bounding this: a `tasktool start` write stages but does not auto-commit, so it is *possible* the start mutation is sitting uncommitted in the main checkout's working tree where I cannot see it from this worktree. Action: verify the authoritative checkout, reconcile the lifecycle (start/adopt so `worktree_base_sha` is recorded, or record the in-place/ready-close rationale), and re-point `reviewer_chain` to the post-slice chain before close.

F2 — Post-slice reviewer artifact directory is untracked. Severity: minor
`docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice/` (chain.json + r1 prompt) is present but untracked (`git status` shows `??`). This is expected at the review gate (Task 6.4 just produced it; Task 6.x registers it via `tasktool artifact add` and commits). No action beyond ensuring it is registered and committed within the slice-only file boundary that Task 6.5 mandates.

F3 — Verification was not executed in this review pass. Severity: minor (verification gap)
This review ran in a read-only/plan context; `python -m pytest tools/tasktool/tests/test_worktree_sync.py` and the broader suite (`tools/tasktool/tests`) plus `tasktool validate` (Tasks 6.1–6.2) were not run here. By inspection the 14 tests in `test_worktree_sync.py` are correct and cover the spec's required matrix (parser, merge/rebase success advancing to the captured base head, both conflict no-advance cases, dirty/missing-base/non-slice/unhealthy/unstaged-authoritative refusals, in-place staged-tasklist advance, and the §9 integration-window clearing test). The implementer must run the full suite and `tasktool validate` before close; this review cannot substitute for that evidence.

F4 — Two spec refusal paths have no direct test. Severity: nit
Refusal rule §5.7 (`has_unmerged_paths(target)` → "unresolved merge entries", `commands.py:2912`) and the branch-attributed stash arm of `working_tree_dirty_for_sync` (`worktree.py:240-247`) are implemented but not exercised by a dedicated test. The spec's §9 required-coverage list does not mandate them, so this is not blocking, but a one-line test for each would lock the behavior against regression.

F5 — Implementation diverges from the plan stubs in benign, unrecorded ways. Severity: nit (traceability)
The shipped code improves on the plan's literal stubs: `_run_sync_git` sets both `GIT_EDITOR="true"` and `GIT_SEQUENCE_EDITOR="true"` (rebase non-interactivity, vs. the plan's `setdefault` GIT_EDITOR only — `commands.py:2926-2929`), and the staged-tasklist allowance was tightened from the plan's "`code[0]!=' ' and code[1]==' '`" to an explicit `{"A ", "M "}` whitelist (extra commit `aa3531f`, with a new `test_dirty_helper_refuses_staged_tasklist_deletion` covering staged `D `). These are correct hardening choices; flagging only because they are not reflected in the plan text and the commit sequence has one more commit than the plan enumerates.

Non-issues confirmed (no action):
- Architecture matches spec §6: git runs *outside* the lock — preflight under `_read_context`, the merge/rebase between contexts, then row update under `_write_context` (`commands.py:2955-2977`). The captured `base_head` SHA is integrated and recorded (not the moving ref), so integrated==recorded by construction.
- Failure semantics (§7): on non-zero git, `_run_sync_git` raises before the `_write_context` block, leaving `worktree_base_sha` unchanged — matched by both conflict tests.
- Base branch comes only from config via `_authoritative_parent_branch` (`commands.py:3204`); no hard-coded `main` in command logic beyond `TasklistConfig`'s default.
- Follow-up output references `tasktool worktree status <id> --integration`, which exists (`cmd_worktree_status_integration`, wired at `cli.py:441`).
- Implementation commits (`8019daf`…`da89931`) are on the slice branch and not yet on `main` (main is at the plan commit `0290ebd`) — normal for a branch awaiting integration, not a defect.

Open questions / assumptions
1. Was `tasktool start P7.S5` ever run? The committed tracker says no; confirm whether a start mutation is uncommitted in the authoritative (main) checkout, or whether the worktree was created out-of-band. This determines whether F1 is a real lifecycle gap or just an uncommitted-stage artifact.
2. Will closeout use a genuine `start` (recording `worktree_base_sha`) or `--allow-ready-close --reason`? The former is preferable given this slice's subject matter.
3. Assumption: the `.worktrees/worktree-p7-s5-conservative-worktree-sync-strict` checkout is the intended implementation worktree for this slice (its name is not recorded in the row).

Suggested document edits
- None to the plan or spec — both are accurate and the implementation faithfully follows them. The plan's commit list (Tasks 1.7–5.5) could optionally note the extra `aa3531f` "tighten staged tasklist sync allowance" commit and the `GIT_SEQUENCE_EDITOR` addition for traceability, but this is cosmetic.

Verification gaps / commands to run before close
- `python -m pytest tools/tasktool/tests/test_worktree_sync.py -q` (expect 14 passed)
- `python -m pytest tools/tasktool/tests/test_worktree_integration.py tools/tasktool/tests/test_worktree_prune.py tools/tasktool/tests/test_worktree_subcommands.py -q`
- `python -m pytest tools/tasktool/tests -q` and `tasktool validate`
- Reconcile the `P7.S5` tracker lifecycle (F1), then `tasktool artifact add P7.S5 --kind reviewer --path docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice/`, `tasktool artifact status P7.S5 --strict`, and close on the slice-only file boundary.

The code for this slice is complete, spec-faithful, and well-tested by inspection; the remaining items are tracker-lifecycle reconciliation and running the verification suite, not code changes.

Overall verdict: ready with small edits


## Sweep 1

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

S1.F1 — No visible evidence the full verification gate (Task 6.1/6.2) actually passed. Severity: important
The slice's own acceptance gate requires `python -m pytest tools/tasktool/tests -q` (full suite, not just the focused file) and `tasktool validate` to be green (plan lines 640–654; spec §9). The reviewer chain `chain.json` shows `"rounds": []` and `sweep_checkpoints` both `pending`, and there is no committed run output. I could not execute the suite from the review environment (sandbox denied `pytest`). The focused tests `tools/tasktool/tests/test_worktree_sync.py` are well-formed and the implementation is internally consistent, so this is a *gap in evidence*, not a demonstrated failure — but it must be closed (full suite + `tasktool validate` shown green, plus the `worktree status P7.S5 --integration` dogfood in 6.3) before `tasktool close P7.S5`. This is the only item standing between the slice and a clean close.

S1.F2 — Plan text (Task 2.3) no longer matches the shipped dirty-check predicate. Severity: minor
Plan lines 250–256 specify the staged-only test as `code[0] != " " and code[1] == " "`. The shipped helper (`tools/tasktool/worktree.py:231-235`) instead uses `code in {"A ", "M "}`, introduced by the extra commit `aa3531f "tighten staged tasklist sync allowance"` that is not represented in the plan. The shipped version is *stricter and better* (it correctly keeps staged renames/deletes/`MM`/`R ` dirty, matching the comment at `worktree.py:248-249` and the refusal test `test_dirty_helper_refuses_unstaged_tasklist_and_untracked_files`). No code change needed; this is plan/implementation drift on a historical artifact. Worth a one-line note in the plan or closeout so the divergence is intentional and recorded, not silent.

S1.F3 — `_run_sync_git` hard-overrides `GIT_EDITOR`/`GIT_SEQUENCE_EDITOR` rather than `setdefault`. Severity: nit (positive divergence — confirm intent)
Plan line 495 used `env.setdefault("GIT_EDITOR", "true")`. Shipped code (`commands.py:2927-2929`) uses unconditional `env["GIT_EDITOR"] = "true"` plus `env["GIT_SEQUENCE_EDITOR"] = "true"`. This is the correct call: the test harness exports `GIT_EDITOR=false` (plan line 71), which `setdefault` would have left in place and could wedge a non-`--no-edit` path. Flagging only so the divergence from the plan is acknowledged as deliberate hardening, consistent with spec §6 ("a subprocess environment that cannot open an editor").

S1.F4 — In-place sync with base genuinely ahead *and* staged `docs/tasklist.json` is an untested edge. Severity: minor
The in-place success test (`test_sync_in_place_allows_staged_tasklist_and_advances_base_sha`) exercises only the already-up-to-date merge (`commands.py` path where `git merge` is a no-op and never touches the index). If the in-place checkout were actually behind base *and* base modified `docs/tasklist.json` while a staged tasklist change sat in the index, `git merge` would abort with "Your local changes would be overwritten." That is a safe failure (non-zero exit → `worktree_base_sha` unchanged via the F-invariant), so there is no correctness hole, but the behavior is undocumented and unverified. Acceptable to leave as a noted residual risk; spec §5/§6 don't promise to handle it.

S1.F5 — Live slice status is not observable from this branch (authoritative-routing artifact, not a defect). Severity: nit
The committed `docs/tasklist.json` in this worktree shows `P7.S5` as `"status": "ready"`, `"started": null`, no `worktree_base_sha`. That is expected: `tasktool start` writes status/`worktree_base_sha` to the authoritative checkout (`/home/simon/Dev/sigreer/skills/superstar`, on `main`), which is outside this review's sandbox and so cannot be inspected here. `git diff main...HEAD` correctly shows zero tasklist changes (4 files, +420). No drift — noting it so the "ready/null" row is not misread as the slice never having been started.

Positive confirmations (no action):
- CLI parser and dispatch are wired correctly: required mutually-exclusive `--merge`/`--rebase` (`cli.py:132-136`), dispatch writes command output to stdout (`cli.py:451-459`).
- Refusal ladder matches spec §5 rules 1–8: non-slice (`commands.py:2958`), missing `worktree_base_sha` (`2905-2907`), unresolvable base (`2908-2911`), unhealthy linked worktree (`_sync_target_path` via `_health_for`, `2894-2897`), unmerged paths (`2912-2913`), dirty target (`2915-2920`), unstaged authoritative tasklist (`2921-2922`).
- Success path integrates the captured pre-op SHA (`current_branch_head_sha`), runs exactly one non-interactive git op without holding the lock, then re-enters `_write_context` to set `worktree_base_sha = base_head` — faithful to spec §6 "integrate the SHA, not the moving ref."
- Failure invariant holds: `_run_sync_git` raises before the `_write_context` block, so `worktree_base_sha` cannot advance on conflict; covered by both merge and rebase conflict tests (`test_worktree_sync.py:225-240` and the merge equivalent).
- Test coverage maps onto every item of spec §9 (parser both/neither, merge success, rebase success, in-place + staged tasklist, missing base sha, dirty refusal, unstaged-vs-staged tasklist, conflict no-advance, post-sync `--integration` window clears).
- All five implementation commits (`8019daf`, `e6f3cf3`/`aa3531f`, `90551b1`, `aeebf0b`, `da89931`) are present and scoped to the four declared files.

Open questions / assumptions
- I assume the focused `test_worktree_sync.py` passes as written; I could not run it (sandbox denied `pytest`). S1.F1 asks the implementer to supply that evidence plus the full-suite/`validate` run.
- I assume `parse_id("P7.S5")[0] == "slice"` and `parse_id("P1")[0] != "slice"`; this underpins the non-slice refusal and is exercised by `test_sync_refuses_non_slice_id`, but unconfirmed without a run.
- I assume the authoritative checkout on `main` records `P7.S5` as `in_progress` with a `worktree_base_sha`; not inspectable from this sandbox (S1.F5).

Suggested document edits
- Plan: add a short note under Task 2 that the shipped staged-tasklist predicate was tightened to `code in {"A ", "M "}` (commit `aa3531f`) so renames/deletes/partially-staged tasklist stay dirty (S1.F2).
- Plan: note that `_run_sync_git` hard-sets `GIT_EDITOR`/`GIT_SEQUENCE_EDITOR` (not `setdefault`) to stay non-interactive even when the caller exports an editor (S1.F3).
- Spec §5/§6 (optional): one sentence acknowledging that an in-place sync which is behind base and carries a staged tasklist change will safe-fail on `git merge` rather than auto-stash (S1.F4).

Verification gaps / commands to run before close
- `python -m pytest tools/tasktool/tests/test_worktree_sync.py -q` (focused — expect all pass)
- `python -m pytest tools/tasktool/tests -q` (full suite — Task 6.2, currently unevidenced)
- `tasktool validate` (Task 6.2 — expect no errors)
- `tasktool worktree status P7.S5 --integration` (Task 6.3 dogfood)
- Then Task 6.4–6.5: register the reviewer chain artifact, `tasktool artifact status P7.S5 --strict`, and `tasktool close P7.S5`.

The implementation is complete, faithful to the spec, and well-tested by inspection; the only thing missing for a clean close is the recorded full-suite + `validate` verification evidence (S1.F1), with two small plan-text reconciliations (S1.F2, S1.F3).

Overall verdict: ready with small edits

