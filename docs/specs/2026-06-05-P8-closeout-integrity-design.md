# P8 — Closeout integrity: landed-branch close gate + lifecycle auto-commit

**Status:** phase shaping (provisional — slice spec/plan writers ratify)
**Phase row:** `P8` · Slices: `P8.S1`, `P8.S2`
**Motivating incident:** P7 closeout (2026-06-05). P7.S5 and P7.S6 passed post-slice review and ran `tasktool close` → `status: done`, but neither session merged its worktree branch to `main`. The tracker said *done* while the deliverables existed only on unmerged `worktree-p7-s5/s6-*` branches; the P7 post-phase review returned `revise: S5/S6 unintegrated` and the human partner had to paste both sessions' transcripts into the S7-closeout session to untangle. Compounding it, both closeout agents saw each other's co-staged tracker mutations on the shared authoritative checkout and halted ("politeness deadlock"), and the recovery's `worktree prune --force` silently skipped the `landed_base_sha` stamp.

## Phase objectives

Make "done-but-not-landed" unrepresentable in practice, and remove the two behaviours that let it arise:

1. **Close gate (tooling).** `tasktool close <slice-id>` refuses when the slice has a recorded `worktree_branch` that is not an ancestor of the base branch — i.e. the implementation has not landed. Escape hatch: `--allow-unlanded --reason "..."` (recorded on the row), mirroring the existing `reserve --force --reason` convention. Slices with `worktree_in_place: true` (no worktree) are unaffected.
2. **Lifecycle auto-commit (tooling).** Tracker lifecycle mutations that today linger staged-but-uncommitted on the authoritative checkout (`close`, prune finalization) commit the tracker immediately as a scoped whole-file commit (`docs/tasklist.json` only). Rationale (human partner's ruling, 2026-06-05): the tracker is bookkeeping, not a body of work; both siblings' states are true regardless of which commit carries them, and lingering staged state is what triggered the concurrent-closeout deadlock.
3. **Skill alignment (docs).** The slice-end sequence in `subagent-driven-development` gains a merge-back step (via `[[finishing-a-development-branch]]`) **before** `tasktool close`, in the same session; prune guidance says clean untracked files and never `--force` (a forced prune sets `merged_proven=False` and deliberately skips the `landed_base_sha` stamp, with no CLI path to stamp afterwards); `tasklist-discipline` distinguishes *sibling work artifacts* (hands-off) from *sibling tracker state in the shared canonical file* (safe to commit) so concurrent closeouts stop deadlocking.

## Closeout goals

- A slice with an unlanded worktree branch cannot reach `status: done` without an explicit, reasoned override.
- `tasktool close` leaves the authoritative checkout clean (tracker committed), so a concurrent closeout never sees a sibling's staged mutation.
- The documented slice-end sequence is: verification → post-slice review `ready` → merge-back to base → `close` (auto-commits) → clean prune (stamps `landed_base_sha`).
- Docs-lifecycle test asserts the new prose; tasktool test suite covers the gate, the escape hatch, and the auto-commit.

## Prospective slices and acceptance intent

### P8.S1 — tasktool close gate + lifecycle auto-commit

- `cmd_close` checks `worktree_branch` ancestry against the base branch (reusing P7.S4's landed-detection helpers in `worktree.py`); refusal message names the branch and prints the merge-back commands. `--allow-unlanded --reason` records the override on the row.
- Close (and prune finalization) commit `docs/tasklist.json` as a scoped whole-file commit on the authoritative checkout; commit message `"<id>: close slice (status=done)"` / `"<id>: finalize worktree prune"`. A `--no-commit` flag preserves the old behaviour for callers that batch.
- TDD against `tools/tasktool/tests/` (close-gate refusal, in-place exemption, escape hatch recording, auto-commit content/scoping, `--no-commit`).
- **Acceptance:** full tasktool suite green; a synthetic unlanded-branch close refuses with actionable output; close on a landed branch leaves `git status` clean for `docs/tasklist.json`.

### P8.S2 — skill updates (depends on S1)

- `subagent-driven-development` slice-end sequence: insert merge-back step before close; close described as auto-committing; prune step says non-`--force` and why.
- `tasklist-discipline`: shared-tracker vs sibling-artifact boundary paragraph + red-flag row ("A sibling's close is co-staged, so I must stop" → the tracker is whole-file bookkeeping; commit it, leave sibling *artifacts* alone — and after S1, close auto-commits so this state should not persist).
- `using-git-worktrees` / `finishing-a-development-branch` touched only if their prose contradicts the new sequence.
- String-assertion tests appended to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` (same pattern as P7.S6).
- **Acceptance:** docs-lifecycle test green including new assertions; no contradiction between the close-gate behaviour shipped in S1 and the documented sequence.

## Dependency assumptions and likely blockers

- `P8.S2 depends_on P8.S1` — the skills must document shipped behaviour, not aspiration. **Slice plan writers must re-ratify this dependency** (or supersede it if S1's scope changes).
- S1 assumes P7.S4's ancestry/landed helpers (`commit_is_in_range`, integration detection) are reusable from `cmd_close`; if not, S1 grows a small refactor, not a new slice.
- Likely blocker: auto-commit interacting with the pre-commit hook's validation path — the hook validates staged tasklist; the auto-commit must stage + commit through the same canonical-serialization path (`serialize.py` atomic write) so the hook passes. Surface in the S1 spec.
- Open design question for S1's brainstorm: should `start` also auto-commit? (P7 evidence says staged-start state was harmless; scope may stay close-only. Decide at spec time, do not pre-commit to it here.)

## Parallelization

None. Serial chain S1 → S2; no `parallel_group`s, no `coordination_group`s, no reservations. `tasktool surface check P8` reports no unguarded overlaps (S1 = `lifecycle`; S2 = `skills`, `lifecycle-docs-test`).

## Surface/reservation table

| Slice | integration_surfaces | reservations | coordination_group |
|-------|---------------------|--------------|--------------------|
| P8.S1 | `lifecycle` (tasktool close/prune path: `commands.py`, `worktree.py`, tasktool tests) | (none) | (none) |
| P8.S2 | `skills` (SKILL.md files), `lifecycle-docs-test` (`test_skill_tasktool_lifecycle_docs.py`) | (none) | (none) |

## Schedule (at shaping time)

```
P8.S1  [ready/proposed]  group=-  ready    deps=-      waiting_on=-
P8.S2  [ready/proposed]  group=-  waiting  deps=P8.S1  waiting_on=P8.S1
```

## Ratification notes for slice spec/plan writers

- Ratify `P8.S1` independent (`tasktool ratify P8.S1`) once its plan passes review.
- Ratify `P8.S2` keeping `depends_on = [P8.S1]`; do not start S2 until S1 is `done` *and landed* (dogfood the new gate).
- Both slices are implementation slices: isolated worktrees, no `--in-place`.
