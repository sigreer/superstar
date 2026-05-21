# Review — 2026-05-21-X15-archive-closed-cross-cutting-items.md (post-slice, round 2)

- Target: `docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md`
- Request: `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/r2-2026-05-21T0205-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

# Post-slice review — X15 Archive Closed Cross-Cutting Items

- Target: `docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md`
- Kind: post-slice
- Reviewer mode: file inspection (test execution gated by approval); the in-tree round-1 chain artifacts and round-2 primary response were consulted but treated as evidence, not authority

## Findings

**F1. Slice work item still `ready`. Severity: important.**
`docs/tasklist.json:213-226` shows `X15` with `status: ready`, `started: null`, `closed: null`. Execution Setup Step 1 requires `tasktool start X15`; Task 5 Step 4 requires `tasktool close X15 [--no-archive]`. The r1-resolution note explains the deferral (authoritative `docs/tasklist.json` blocks the lifecycle mutation from this worktree). That is a process workaround, not a satisfied gate — the slice's own definition of "done" is unmet at review time. Carry this into closeout: either (a) perform `start`/`close X15` from the authoritative checkout before this gate clears, or (b) explicitly waive Task 5 Step 4 in the chain rather than leave it implicitly skipped.

**F2. All implementation changes uncommitted. Severity: important.**
`git status` shows 19 modified files + 5 untracked artifacts; `git log -1` is `91261f1 X16: …`. Task 5 Step 5 calls for a single commit titled `tasktool: archive closed cross-cutting items`. Reviewer evidence depends on a non-drifting worktree; until the commit lands, this review certifies a snapshot only.

**F3. Sweep round 2 not closed. Severity: important.**
`docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/` contains `r2-…-sweep1-request.md` with no matching response, and `chain.json` does not yet record round 2 (last recorded round is r1 with `merged_verdict: revise`). The chain must be brought to terminal state with `merged_verdict ∈ {ready, ready with small edits}` and `sweep_checkpoints.final-ready = completed` before this slice can close.

**F4. Verification evidence not captured in chain. Severity: important.**
`r1-resolution.md` reports `python3 -m pytest tools/tasktool/tests -q -> 335 passed` and `validate --strict-format -> ok`, but the tail/log of each run is not stored under the chain folder. Both r1 and r2 reviewers asked for this. With ~600 LOC added and 20+ new behavioral tests, the green run is the load-bearing claim — paste the tail into `r2-pytest.log` (or similar) before closing.

**F5. `_find_item` archived-hint scope is broader than spec. Severity: minor.**
`tools/tasktool/commands.py:481-484` emits the archived-X hint from `_find_item`, so every command that goes through the resolver (`start`, `set`, `block`, `unblock`, `note`, `ref`, `brief`) inherits the hint. Spec §4 "Error handling" scopes this language to `close`; `archive-cross` was reconciled in r1-resolution by adding an explicit precheck (`commands.py:709`) that fires before `_find_item`. Behavior is correct; documentation is not updated. Either add a one-liner to `skills/tasklist-discipline/SKILL.md` ("any tasktool command run against an archived X-id reports a may-already-be-archived hint") or narrow the hint to `close`/`archive-cross` only.

**F6. Atomicity residual. Severity: nit.**
`_archive_cross_at_root` orders: mutate → `validate_project(p)` → `archive_path.write_text(...)`; caller then runs `_save`. Validation failure leaves no orphan file (good; covered by `test_archive_cross_atomicity_no_orphan_file_on_validation_failure`). A `_save` IO failure after `write_text` does leave an orphan markdown on disk while `docs/tasklist.json` is unchanged. Matches phase archive behavior, accepted by spec; flagging only.

**F7. `X15` ref list missing reviewer chain. Severity: nit.**
`docs/tasklist.json:218-222` lists spec/plan/handoff but not `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/`. Other completed X-items in this fork (X10, X11) include the reviewer folder in `refs`. Add it at closeout.

**F8. Reviewer chain naming. Severity: nit.**
Folder `x15-archive-closed-cross-cutting-items-X15-post-slice` repeats `X15`. Matches the chain naming pattern set elsewhere in the repo; informational only.

## Open questions / assumptions

- Will `start`/`close X15` execute against the authoritative checkout before merge, or is the lifecycle waived for this slice? (F1)
- Is round-2 sweep1 in flight, or will it be invoked manually before close? (F3)
- Are r1-resolution's "335 passed" and `validate ok` reproducible on the current worktree state? Re-running and capturing output into the chain would close F4.

## Suggested document edits

- Plan Task 5 Step 1: require pasting the `pytest` and `validate --strict-format` tails into the round artifact (e.g., `r2-verification.md`), not just running them locally.
- Plan Task 5 Step 4: state explicitly whether `X15` will be closed from this worktree or the authoritative checkout, since the worktree cannot mutate the row today.
- `skills/tasklist-discipline/SKILL.md`: add one line noting the archived-X hint surfaces on any command that resolves an archived X-id, not only `close`.

## Verification gaps / commands to run

```sh
tools/tasktool/tasktool validate --strict-format
python3 -m pytest tools/tasktool/tests -q
tools/tasktool/tasktool render | rg -n "Cross-cutting|Archived cross-cutting|X15"
tools/tasktool/tasktool archive-cross X1    # expect: "cross-cutting X1 is already archived"
tools/tasktool/tasktool show X15
```

Capture each tail under `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/r2-*.md`, complete the round-2 sweep1 response, then update `chain.json` to record the round-2 merged verdict.

Overall verdict: ready with small edits
