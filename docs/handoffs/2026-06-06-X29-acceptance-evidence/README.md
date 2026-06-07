# X29 full-suite baseline evidence (post-slice review r1 — F2 / S1.F1)

Durable proof that the X29 worktree's full default-discovery pytest failures are
byte-identical to a clean clone of `main` — all pre-existing, none in
`tools/timeline`, zero introduced by X29.

## Root cause (correction, 2026-06-07)

**The 132 "pre-existing failures" recorded below were an environment artifact,
not real breakage.** `tools/tasktool/commands.py:880-888` contains a mutation
guard that trips on ANY non-empty `SUPERSTAR_SUBAGENT_ROLE` environment
variable. The evidence runs below were executed from shells carrying that
export (per the subagent-role protocol), so the var leaked into the test
processes and tripped the guard inside the tasktool worktree/tracker suites.

Re-verified at worktree HEAD `ff2d02ef7066cb6373e62c8ec8f9f9dc3be4123f`:

- **Clean environment** (`env -u SUPERSTAR_SUBAGENT_ROLE python3 -m pytest -q
  --tb=no -rfE -p no:cacheprovider`): **1224 passed, 0 failed, 0 errors**,
  exit code 0. Only a pre-existing DeprecationWarning in
  `external-reviewer.py` (utcnow), unrelated to X29. Tail captured in
  `worktree-suite-clean-summary.txt`.
- **With the var set** (same command, `SUPERSTAR_SUBAGENT_ROLE=implementer`):
  109 failed + 23 errors, and the sorted failing-id set is **byte-identical**
  to the committed `failing-ids-worktree.txt` (132/132 ids match).

The byte-identical-to-main comparison below remains valid: the artifact
affected both sides equally (both runs carried the var), and zero failures
were in `tools/timeline` either way. The original lists and summaries are kept
unchanged for the audit trail.

## Compared SHAs

- Worktree HEAD (`worktree-x29-visual-work-history-timeline-generator`): `267842e0d0b897ba2f97e454d550a05b742d3460`
- `main`: `92eefc100e843a977321ce031d6178aa5e1d4762`

## Commands (run 2026-06-07)

Baseline clone (local only, no network):

```bash
git clone --no-hardlinks -b main /home/simon/Dev/sigreer/skills/superstar /tmp/x29-baseline-main
cd /tmp/x29-baseline-main
python3 -m pytest -q --tb=no -rfE -p no:cacheprovider   # exit code 1
```

Worktree, same command from the worktree root:

```bash
cd /home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-x29-visual-work-history-timeline-generator
python3 -m pytest -q --tb=no -rfE -p no:cacheprovider   # exit code 1
```

Failing/erroring test ids extracted from each run's short test summary
(`FAILED `/`ERROR ` lines), sorted:

```bash
grep -E '^(FAILED|ERROR) ' <log> | awk '{print $1" "$2}' | sort > failing-ids-<side>.txt
```

## Results

| Side | Passed | Failed | Errors | Collected |
|---|---|---|---|---|
| `main` clone (`92eefc1`) | 997 | 109 | 23 | 1129 |
| X29 worktree (`267842e`) | 1074 | 109 | 23 | 1206 |

- `diff failing-ids-main.txt failing-ids-worktree.txt` → **empty**: the
  failing/erroring id set difference is empty in **both** directions
  (132 ids each side = 109 FAILED + 23 ERROR, byte-identical).
- `grep -c 'tools/timeline' failing-ids-worktree.txt` → **0**: no failing or
  erroring id is under `tools/timeline`.
- Collection delta is **+77**, exactly `tools/timeline/tests`
  (`python3 -m pytest tools/timeline/tests -q --collect-only` → 77 tests;
  1206 − 1129 = 77; all 77 pass — 1074 − 997 = 77 passed delta, 0 timeline
  failures). Note: the slice-close note's earlier "73/73" tally predates four
  review-driven regression tests added inside `tools/timeline/tests`; the
  current suite is 77/77.

All 132 failures/errors on both sides are pre-existing `main` failures in the
tasktool worktree/tracker suites (`scripts/tests`, `tools/tasktool/tests`).

## Files

- `main-suite-summary.txt` / `worktree-suite-summary.txt` — pytest `-rfE`
  short test summary plus final tally line for each side.
- `failing-ids-main.txt` / `failing-ids-worktree.txt` — sorted
  `FAILED|ERROR <test-id>` lists; `diff` between them is empty.
- `worktree-suite-clean-summary.txt` — tail of the clean-environment re-run at
  HEAD `ff2d02e` (1224 passed, 0 failed; see "Root cause" above).
