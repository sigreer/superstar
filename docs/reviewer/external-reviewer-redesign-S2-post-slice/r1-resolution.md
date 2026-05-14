# Resolution for r1

Round 1 of the S2 chain. Reviewer returned `revise` with 3 findings
(2 blocking). All findings — plus a chain-routing defect observed by
the coordinator — are addressed below.

## Provenance note

This round was originally misrouted into the Slice-1 chain folder
(`docs/reviewer/external-reviewer-redesign-post-slice/`) as round 5,
because `discover_legacy_chain` matched the bare legacy slug regardless
of whether the candidate folder already contained a `chain.json`. After
the routing fix (`cc07bf5`) the artefacts were relocated to this
S2-keyed chain folder (`8743c63`) and recorded as round 1 here. The
Slice-1 chain manifest is restored to end at round 4.

## F1
Status: fixed
Evidence:
- Commit: `cc07bf5` (`fix(external-reviewer): persist work_id in manifest; guard legacy match by chain.json absence`)
- Files: `skills/external-review/scripts/external-reviewer.py`,
  `skills/external-review/tests/test_work_id_persisted.py`
- Verification: end-to-end test asserts both JSON output AND on-disk
  `chain.json` contain `"work_id": "S1"`; mismatched stored `work_id`
  causes exit code 6.

Notes:
`work_id` not stored in manifest. `external-reviewer.py` initialised
new manifests with `"work_id": None`, so the JSON output also reported
`null` even when `--work-id S1` was supplied. This violated the spec
(design.md lines 89, 98) which requires `--work-id` to be stored
verbatim.
- Fresh manifests now set `"work_id": args.work_id` (still `None` for
  kinds that don't require it — `spec`, `plan`, etc., which is fine).
- For an existing manifest whose stored `work_id` differs from the CLI
  `--work-id`, the script now emits a clear stderr error and exits
  with code 6 (new). This prevents accidental cross-slice chain reuse
  via a hand-edited or mismatched invocation.
- If a stored `work_id` is `None` (legacy synthesis path or older
  manifest) and the caller supplies a value, the manifest is
  backfilled.
- The synthesized-legacy path already passed `args.work_id` per the
  existing Task 2.3 implementation; verified unchanged.

Tests added in `skills/external-review/tests/test_work_id_persisted.py`:
1. `test_work_id_persisted_in_manifest_and_json` — runs the script
   end-to-end via subprocess against a temp repo with `--work-id S1`
   and asserts both the JSON output AND on-disk `chain.json` contain
   `"work_id": "S1"`.
2. `test_work_id_mismatch_refuses_reuse` — asserts a mismatched
   stored `work_id` causes exit code 6 with a "does not match" stderr
   message.
3. `test_existing_chain_folder_with_chain_json_not_reused_as_legacy` —
   see chain-routing fix below.

## F2
Status: fixed
Evidence:
- Commits: `8743c63` (chain-folder migration), `3aa3790`
  (closeout note + checkbox tick)
- Files: `docs/reviewer/external-reviewer-redesign-post-slice/*` (round
  5 entries reverted), `docs/reviewer/external-reviewer-redesign-S2-post-slice/*`
  (new chain folder), `docs/superstar/plans/2026-05-13-external-reviewer-redesign.md`
- Verification: post-slice gate landed in correct S2 chain folder;
  Slice-1 manifest restored to round 4.

Notes:
Workspace cleanliness. Five modified tracked files plus the untracked
round-5 reviewer artefact left the worktree in a half-written state.
- The five modified tracked files (`CLAUDE.md`, four `skills/*/SKILL.md`
  files) were authorised by the human partner to remain across Slice 1
  and Slice 2 closeouts; both closeout notes record this. They are
  not part of Slice 2 and are intentionally left untouched.
- The untracked round-5 request/response have been relocated to the
  correct S2 chain folder as round 1 (commit `8743c63`) and the chain
  manifest written.
- The Slice 2 closeout note has been added to the plan
  (`3aa3790`) and records the commit SHAs (`6700937`, `64ecb51`,
  `d05056f`), the chain-routing defect and its fix, and confirmation
  that the post-slice gate landed in the correct S2 chain folder.

## F3
Status: fixed
Evidence:
- Commit: `3aa3790`
- Files: `docs/superstar/plans/2026-05-13-external-reviewer-redesign.md`
- Verification: all 15 Slice 2 `- [ ]` entries flipped to `- [x]`;
  Slice 3+ checkboxes unchanged.

Notes:
Slice 2 checkboxes. All `- [ ]` checkboxes for Slice 2 tasks (2.1,
2.2, 2.3) remained unchecked even though the work was implemented and
committed. Commit `3aa3790`: all 15 Slice 2 `- [ ]` entries are now
`- [x]`. Slice 3+ checkboxes are unchanged.

## F4
Status: fixed
Evidence:
- Commits: `cc07bf5` (parser guard), `8743c63` (migration)
- Files: `skills/external-review/scripts/external-reviewer.py`,
  `skills/external-review/tests/test_work_id_persisted.py`,
  `docs/reviewer/external-reviewer-redesign-post-slice/chain.json`,
  `docs/reviewer/external-reviewer-redesign-S2-post-slice/*`
- Verification: new test
  `test_existing_chain_folder_with_chain_json_not_reused_as_legacy`
  creates a sibling chain folder named exactly `<target>-<kind>` with a
  `chain.json` for `work_id=S1`, then runs the script with `--work-id S2`
  and asserts a fresh `<target>-S2-<kind>` folder is created and the
  S1 folder is not touched.

Notes:
Chain-routing defect (related to F1; not a numbered reviewer finding,
treated here as F4 so it has a parseable Status line).
- Defect. Reviewer ran for Slice 2 with `--work-id S2`. The expected
  chain folder was `external-reviewer-redesign-S2-post-slice/`. The
  artefacts instead landed inside the existing Slice-1 chain folder
  (`external-reviewer-redesign-post-slice/`, which already had a
  `chain.json`) as round 5.
- Root cause. In `discover_legacy_chain`, the exact-name legacy branch
  (`entry.name == legacy_old_name`) appended the folder to
  `candidates` without checking for the presence of `chain.json`. Only
  the embedded-suffix branch had that guard. So a new-regime chain
  whose folder name happened to equal `<target>-<kind>` was matched as
  a legacy candidate and reused.
- Fix (`cc07bf5`). The exact-name branch now also requires
  `not (entry / "chain.json").exists()` before treating the folder as
  legacy. A folder with a `chain.json` is a new-regime chain and must
  never be silently reused for a different work-id.
- Migration (`8743c63`).
  - `git mv` of the request file from
    `docs/reviewer/external-reviewer-redesign-post-slice/r5-2026-05-14T0221-request.md`
    to
    `docs/reviewer/external-reviewer-redesign-S2-post-slice/r1-2026-05-14T0221-request.md`.
  - Same for the response file (was untracked in the S1 folder; now
    committed under the S2 folder as round 1).
  - Fresh `chain.json` written for the S2 chain with the round
    recorded as round 1 (verdict `revise`, findings `3`, blocking `2`,
    head SHA `d05056fdde59906ceb557dc15bb627b9afc55130` at request
    time) and an origin-note recording the migration.
  - The previously-staged round-5 entry in
    `docs/reviewer/external-reviewer-redesign-post-slice/chain.json`
    was reverted (`git checkout --`) so the Slice-1 chain manifest
    correctly ends at round 4.

## Commit summary

| Step | Commit | Description |
|------|--------|-------------|
| Code fix (F1 + routing + tests) | `cc07bf5` | Persist `work_id`; guard legacy match by `chain.json` absence; new exit code 6 for mismatch; 3 new end-to-end tests |
| Chain-folder migration | `8743c63` | Move misrouted r5 artefacts to S2 chain as r1; write fresh `chain.json`; drop round 5 from S1 manifest |
| Plan edits | `3aa3790` | Tick all Slice 2 checkboxes; append Slice 2 closeout note |
| Resolution doc | `1df15e3` | This file (original prose form); see r2-resolution for the spec-compliant retrofit |

## Verification

```bash
python3 -m pytest skills/external-review/tests/
# 36 passed (at the time this round closed; 39 passed after r2 parser fix)
```

S2 chain folder exists and is well-formed:

```
docs/reviewer/external-reviewer-redesign-S2-post-slice/
├── chain.json                        # work_id="S2", rounds[0] = round 1
├── r1-2026-05-14T0221-request.md     # moved from S1 chain r5
├── r1-2026-05-14T0221-response.md    # moved from S1 chain r5
└── r1-resolution.md                  # this file
```

S1 chain manifest ends at round 4 (round-5 entry removed).
