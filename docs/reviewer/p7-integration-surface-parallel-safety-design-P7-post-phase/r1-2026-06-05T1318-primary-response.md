# Review — 2026-06-02-P7-integration-surface-parallel-safety-design.md (post-phase, round 1)

- Target: `docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md`
- Request: `docs/reviewer/p7-integration-surface-parallel-safety-design-P7-post-phase/r1-2026-06-05T1318-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: blocking — S5/S6 are marked `done`, but their shipped scope is not present in this checkout.
`docs/tasklist.json:365-398` marks P7.S5 done and claims conservative `worktree sync`; `docs/tasklist.json:400-430` marks P7.S6 done and claims the skill/playbook changes. The phase spec requires those deliverables at `docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:249-302` and `:358-396`. In the current tree, `tools/tasktool/cli.py:122-145` has no `worktree sync` subcommand, and `skills/subagent-driven-development/references/registry-merge-playbook.md` does not exist. The S6 skill files also still contain the old guidance, e.g. `skills/subagent-driven-development/SKILL.md:41` says parallel slices are candidates when “file scopes do not overlap,” with no `surface check` gate or integrate-current-main checkpoint. Git confirms the S5/S6 implementation commits exist only on sibling branches and are not ancestors of `HEAD` (`s5_ancestor=1`, `s6_ancestor=1`). This is a phase-closeout blocker.

F2 — Severity: blocking — The tracker has a stale/missing artifact reference for S5.
`docs/tasklist.json:380-386` references `docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice`, but `tasktool validate --format json` reports `P7.S5.refs: path does not exist: docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice`. A post-phase closeout cannot rely on a tracker whose referenced post-slice evidence is missing from the reviewed tree.

F3 — Severity: important — P7 is not archived/closed yet, so the phase closeout record is incomplete.
`docs/tasklist.json:246-253` and `:490-493` still show P7 as an active phase with `status: "ready"` and no phase close/archive note. `tasktool phase-status` also lists P7 under open phases. If this review is intentionally the pre-archive post-phase gate, that is acceptable procedurally, but the closeout cannot be called complete until the blocking merge/evidence issues are fixed, post-phase review passes, and `tasktool archive-phase P7` records the archive entry.

2. Open questions / assumptions

I assume the current branch is the candidate being reviewed, not the sibling S5/S6 worktrees. If the intent was to review an aggregate branch, merge/cherry-pick the S5 and S6 implementation commits into this branch first.

3. Suggested document edits

Do not edit the phase spec to weaken acceptance. Instead, update the closeout/tracker state after integrating S5/S6:
- Restore/merge S5 implementation and its reviewer chain.
- Restore/merge S6 skill edits, tests, and `registry-merge-playbook.md`.
- Re-run validation and phase verification.
- Archive P7 only after the post-phase gate passes.

4. Verification gaps / commands that should be run

Run these after integrating the missing slice branches:
- `git merge-base --is-ancestor <latest-S5-commit> HEAD`
- `git merge-base --is-ancestor <latest-S6-commit> HEAD`
- `tasktool validate --format json`
- `python -m pytest tools/tasktool/tests/test_worktree_sync.py tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py tools/tasktool/tests/test_validate.py -q`
- `tasktool archive-phase P7` after a ready post-phase verdict

I ran:
- `tasktool validate --format json` → `ok: true` but one P7.S5 missing-ref warning.
- `tasktool show P7`, `tasktool schedule P7`, `tasktool artifact status P7 --strict`.
- `python -m pytest tools/tasktool/tests/test_validate.py::SurfaceDriftWarningTests tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` → 27 passed, but this did not cover missing S5/S6 implementation because the relevant commits are absent from this checkout.

Overall verdict: revise
