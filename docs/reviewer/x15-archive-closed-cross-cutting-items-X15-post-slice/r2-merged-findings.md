# Merged findings for r2

## Primary

# Review — 2026-05-21-X15-archive-closed-cross-cutting-items.md (post-slice, round 2)

- Target: `docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md`
- Request: `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/r2-2026-05-21T0205-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

Plan mode blocks me from running the verification commands, so I'm reviewing from diff inspection and the resolution report's claims.

# Post-slice review — X15 Archive Closed Cross-Cutting Items (round 2)

## Findings

**F1. Slice work item is still not started or closed. Severity: important — UNRESOLVED.**
`docs/tasklist.json:213-225` still has `X15` with `status: ready`, `started: null`, `closed: null`. The resolution report acknowledges this and defers it to the main checkout. That's acceptable as a process decision, but the slice still has not been mutated through the lifecycle the plan defines (Execution Setup Step 1: `tasktool start X15`; Task 5 Step 4: `tasktool close X15`). For this review to act as a final gate, the reviewer needs to know whether closure will be performed before merge. Flagging as still-open process gap, not a code defect.

**F2. All implementation changes remain uncommitted. Severity: important — UNRESOLVED.**
`git status` shows the same 19 modified files plus 5 untracked artifacts; `git log` head is still `91261f1 X16: …`. The plan's Task 5 Step 5 calls for a single commit before close. Resolution did not address this. Again, acceptable to defer if the team has agreed, but the reviewer cannot certify "completed" against a working tree that can drift.

**F3. Doc-test enforcement now in place. Severity: important — RESOLVED.**
`tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py:24-27` adds the four required assertions (`tasktool close <x-id>`, `--no-archive`, `archive-cross`, plus the archived-X-IDs-reserved assertion). The SKILL.md edits at `skills/tasklist-discipline/SKILL.md:22,40,64-66,77` contain all of those strings. Drift guard is in place.

**F4. External post-slice review chain. Severity: important — IN PROGRESS.**
The current round (this review) is being executed. Verdict and chain artifact recording is owed before close. Not a code finding.

**F5. Test suite execution evidence. Severity: important — PARTIALLY RESOLVED.**
The resolution report states `python3 -m pytest tools/tasktool/tests -q` -> `335 passed`. I cannot independently re-run under plan-mode constraints. The numbers are plausible against the diff (new tests added: ~12 in `test_commands.py`, 3 in `test_cli_integration.py`, 3 in `test_migrate.py`, 1 in `test_render.py`, 1 in `test_serialize.py`, 4 in `test_validate.py`, 1 file `test_schema_gen.py`). Recommend the operator paste the pytest tail into the next round artifact so this is durable evidence rather than chat assertion.

**F6. Archive-cross archived-id error message. Severity: minor — RESOLVED.**
`tools/tasktool/commands.py:cmd_archive_cross` now adds a precheck:
```python
if any(a.id == id for a in p.archived_cross_cutting):
    raise CommandError(f"cross-cutting {id} is already archived")
```
called before `_find_item`. This now correctly emits the spec §4 message `cross-cutting X1 is already archived` for `archive-cross` on archived IDs, while `close` retains the "may already be archived" hint via `_find_item`. New test `test_archive_cross_archived_id_reports_archived_error` covers it.

**F7. Strict on-disk atomicity of archive file write. Severity: nit — UNCHANGED.**
`_archive_cross_at_root` still writes the archive markdown *before* `_save` writes `docs/tasklist.json`. Test `test_archive_cross_atomicity_no_orphan_file_on_validation_failure` only covers the pre-save validation-failure case. If `_save` fails after the markdown is on disk, an orphan archive file remains. Same shape as phase archive, accepted by spec; logging only.

**F8. `cmd_archive_cross` active-membership coverage. Severity: minor — UNCHANGED.**
Still no positive test for `archive-cross` invoked on an X-id only present in `archived_cross_cutting` via the resolver path (the new precheck short-circuits before `_find_item`, which is good, and `test_archive_cross_archived_id_reports_archived_error` exercises the precheck). Net: the resolver-path concern is moot now that the precheck exists. Effectively resolved.

**F9. Reviewer chain naming. Severity: nit — UNCHANGED.**
Cosmetic only.

**S1.F1. Tests evidence — see F5.**

**S1.F2. archive-cross error message — RESOLVED (see F6).**

**S1.F3. Cross-command archived-hint scope. Severity: minor — UNRESOLVED but acceptable.**
`_find_item`'s archived-id hint at `tools/tasktool/commands.py:481-484` still applies to every command (`start`, `set`, `block`, `unblock`, `note`, `ref`, `brief`), not just `close`. SKILL.md does not document this. Low-impact usability surface; flag-only.

**S1.F4. `skip_review_gate=True` filler. Severity: minor — RESOLVED.**
Removed in `test_close_no_archive_rejects_non_cross_items`.

**S1.F5–S1.F7. Closeout / on-disk atomicity / archived-ID reservation note. — RESOLVED.**
SKILL.md line 40 documents `Archived X IDs are still reserved`. The closeout items (S1.F5) overlap F1/F2 above.

## New findings (round 2 regressions / misses)

None observed. The fixes are targeted and do not introduce new behavior.

## Open questions / assumptions

- Will `tasktool start X15` / `tasktool close X15` be run before merge, and will the implementation be committed (F1, F2)? If yes, this review's verdict can stand as `ready with small edits`. If the team intends to merge with these still pending, that breaks the lifecycle the plan itself defines.
- Test suite green output — confirm by pasting the pytest tail into `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/r2-*.md`.

## Suggested document edits

- None for the plan or spec. The plan's Task 5 closeout steps already cover F1/F2.

## Verification gaps / commands that should be run

```sh
tools/tasktool/tasktool validate --strict-format
python3 -m pytest tools/tasktool/tests -q
tools/tasktool/tasktool render | rg -n "Cross-cutting|Archived cross-cutting|X15"
tools/tasktool/tasktool archive-cross X1   # should fail: not done / already archived
```

Capture the tail of each under the round-2 reviewer artifact.

Overall verdict: ready with small edits


## Sweep 1

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

**S1.F1. Slice work item still `ready`. Severity: important.**
`docs/tasklist.json:213-226` shows `X15` with `status: ready`, `started: null`, `closed: null`. Execution Setup Step 1 requires `tasktool start X15`; Task 5 Step 4 requires `tasktool close X15 [--no-archive]`. The r1-resolution note explains the deferral (authoritative `docs/tasklist.json` blocks the lifecycle mutation from this worktree). That is a process workaround, not a satisfied gate — the slice's own definition of "done" is unmet at review time. Carry this into closeout: either (a) perform `start`/`close X15` from the authoritative checkout before this gate clears, or (b) explicitly waive Task 5 Step 4 in the chain rather than leave it implicitly skipped.

**S1.F2. All implementation changes uncommitted. Severity: important.**
`git status` shows 19 modified files + 5 untracked artifacts; `git log -1` is `91261f1 X16: …`. Task 5 Step 5 calls for a single commit titled `tasktool: archive closed cross-cutting items`. Reviewer evidence depends on a non-drifting worktree; until the commit lands, this review certifies a snapshot only.

**S1.F3. Sweep round 2 not closed. Severity: important.**
`docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/` contains `r2-…-sweep1-request.md` with no matching response, and `chain.json` does not yet record round 2 (last recorded round is r1 with `merged_verdict: revise`). The chain must be brought to terminal state with `merged_verdict ∈ {ready, ready with small edits}` and `sweep_checkpoints.final-ready = completed` before this slice can close.

**S1.F4. Verification evidence not captured in chain. Severity: important.**
`r1-resolution.md` reports `python3 -m pytest tools/tasktool/tests -q -> 335 passed` and `validate --strict-format -> ok`, but the tail/log of each run is not stored under the chain folder. Both r1 and r2 reviewers asked for this. With ~600 LOC added and 20+ new behavioral tests, the green run is the load-bearing claim — paste the tail into `r2-pytest.log` (or similar) before closing.

**S1.F5. `_find_item` archived-hint scope is broader than spec. Severity: minor.**
`tools/tasktool/commands.py:481-484` emits the archived-X hint from `_find_item`, so every command that goes through the resolver (`start`, `set`, `block`, `unblock`, `note`, `ref`, `brief`) inherits the hint. Spec §4 "Error handling" scopes this language to `close`; `archive-cross` was reconciled in r1-resolution by adding an explicit precheck (`commands.py:709`) that fires before `_find_item`. Behavior is correct; documentation is not updated. Either add a one-liner to `skills/tasklist-discipline/SKILL.md` ("any tasktool command run against an archived X-id reports a may-already-be-archived hint") or narrow the hint to `close`/`archive-cross` only.

**S1.F6. Atomicity residual. Severity: nit.**
`_archive_cross_at_root` orders: mutate → `validate_project(p)` → `archive_path.write_text(...)`; caller then runs `_save`. Validation failure leaves no orphan file (good; covered by `test_archive_cross_atomicity_no_orphan_file_on_validation_failure`). A `_save` IO failure after `write_text` does leave an orphan markdown on disk while `docs/tasklist.json` is unchanged. Matches phase archive behavior, accepted by spec; flagging only.

**S1.F7. `X15` ref list missing reviewer chain. Severity: nit.**
`docs/tasklist.json:218-222` lists spec/plan/handoff but not `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/`. Other completed X-items in this fork (X10, X11) include the reviewer folder in `refs`. Add it at closeout.

**S1.F8. Reviewer chain naming. Severity: nit.**
Folder `x15-archive-closed-cross-cutting-items-X15-post-slice` repeats `X15`. Matches the chain naming pattern set elsewhere in the repo; informational only.

## Open questions / assumptions

- Will `start`/`close X15` execute against the authoritative checkout before merge, or is the lifecycle waived for this slice? (S1.F1)
- Is round-2 sweep1 in flight, or will it be invoked manually before close? (S1.F3)
- Are r1-resolution's "335 passed" and `validate ok` reproducible on the current worktree state? Re-running and capturing output into the chain would close S1.F4.

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
