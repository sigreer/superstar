# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-09-P9.S3-combined-spec-plan-gate.md` (Task 1 Step 1 tests; Task 1 Step 2 expectation)
- Verification: Task 1 tests now assert `"unrecognized arguments" not in r.stderr` and the specific validation messages (`"only valid with --kind plan"`, `"not found"` + `"nope.md"`). Task 1 Step 2's expected-fail rationale updated to explain that, pre-flag, argparse prints `unrecognized arguments: --combined-gate`, so the tightened asserts fail — proving the tests exercise the new validation path, not argparse's default rejection.

Notes:
The previous asserts (`"combined-gate" in stderr.lower()`, "no chain folder") were satisfied by argparse's own exit-2, so they did not prove the new behaviour. Now discriminated.

## F2
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-09-P9.S3-combined-spec-plan-gate.md` (Task 2 Step 3)
- Verification: Task 2 Step 3 no longer writes `combined_gate_spec` into the manifest literal. It sets the key conditionally only when `combined_gate_explicit is not None`, after the eager `write_manifest`, with a second write for combined chains only. Standalone chains omit the key entirely, matching the spec's "absent on standalone" contract and `test_standalone_plan_has_no_combined_keys` (`"combined_gate_spec" not in m`).

Notes:
Confirms the byte-stability claim for standalone/non-plan rounds.

## F3
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-09-P9.S3-combined-spec-plan-gate.md` (Task 2 Step 1: `test_combined_gate_attaches_spec_to_context`, `test_combined_gate_dedupes_spec_in_context`; Task 3 Step 1: `test_round2_reattaches_guidance_without_flag`; Task 2/Task 3 Step 2 `-k` filters updated)
- Verification: New tests assert (a) round-1 broad request previews the attached spec ("Acceptance criteria" appears only in spec.md, not plan.md); (b) dedup — spec supplied via both `--combined-gate` and `--context` is previewed exactly once (`request.count("Acceptance criteria") == 1`); (c) round 2 without the flag re-applies the guidance ("did not receive a standalone review") and still lists `spec.md` in the prompt's context files. This satisfies spec AC8's round-2 fixture requirement.

Notes:
Round-2 prompts are incremental, so the full spec preview is intentionally not re-embedded (incremental mode omits context previews by design); the spec remains attached in the prompt's context-file list and the guidance is always present. The test asserts those two re-attachment signals rather than a re-embedded preview.

## F4
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-09-P9.S3-combined-spec-plan-gate.md` (Task 6 Step 4)
- Verification: Task 6 Step 4 replaced the whole-file grep (which false-fails because the skill files legitimately contain `TODO`/`TBD`/`FIXME`/`{{` as checklist examples) with a diff-scoped check: `git diff -- <files> | grep -E '^\+' | grep -nE "TODO|TBD|FIXME|\{\{"`, scanning only newly added lines.

Notes:
The check now flags only placeholders introduced by this task's new prose.
