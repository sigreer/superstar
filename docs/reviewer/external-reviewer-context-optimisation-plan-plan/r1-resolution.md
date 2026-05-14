# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md` Task 1.11 Step 4.
- Change: rewrote the Step 4 replacement block against the *actual* variable names in the script (`prior` for the dict at `external-reviewer.py:876`, `prior_round` for its integer round number at `external-reviewer.py:877`). The plan now patches the existing predicate construction (`prior_verdict`, `prior_valid`, `prior_status`, `prior_was_process_failure`) and the Note-printing branch, preserving the existing ERROR-printing block below verbatim.
- Verification: `grep -A 20 "prior = manifest\[.rounds.\]\[-1\]" docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md` shows the rewritten block aligning with the script's existing names.

Notes:
The reviewer correctly caught that `prior_round.get(...)` would have raised `AttributeError: 'int' object has no attribute 'get'`. The fix preserves the existing variable layout.

## F2
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md` Task 1.9 Step 3 (Path A + Path B), Step 4 (new test).
- Change: Task 1.9 now wires `migrate_manifest_inplace()` into both manifest-entry paths — after `read_manifest()` (existing chain.json) AND after `synthesize_legacy_manifest()` (legacy on-disk artifacts with no chain.json, at `external-reviewer.py:830`). The synthesised path runs the migrator *before* the manifest is persisted with `write_manifest()`, so synthesised rounds get `status: "unknown"` and `returncode: null` and cannot leak the untrusted `verdict_valid: true` that `synthesize_legacy_manifest` would otherwise derive from echoed prompt text at `external-reviewer.py:1331`.
- A new test (`test_synthesized_legacy_manifest_marks_rounds_unknown`) constructs a chain folder with on-disk `r1-*-request.md` / `r1-*-response.md` files but no `chain.json`, runs the script, and asserts that the resulting `chain.json` has the synthesised r1 round with `status: "unknown"` and `returncode: null`.

Notes:
This addresses the full class of legacy-state poisoning, not just the live-failure echo case.

## F3
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md` Task 1.10 Step 4 (new stable section headings), Task 2.4 Steps 4-7 (proper parameter + CLI integration test).
- Changes:
  - Task 1.10 Step 4: added a new step that replaces the prose labels in `build_incremental_preamble`'s returned f-string with stable markdown subheadings (`## Review chain summary`, `## Prior-round findings`, `## Resolution report for prior round`, `## Changes since prior round`). These are the regex-friendly anchors `apply_budget` relies on.
  - Task 2.4 Step 4: `_BUDGET_SECTIONS` regexes are rewritten to match the new `\n## ...\n` heading anchors. A new `_find_section_end` helper bounds each section by the next `\n## ` heading OR the sentinel end marker OR end-of-text, eliminating the original "trim across boundaries" risk.
  - Task 2.4 Step 5: `make_prompt` gains an explicit `incremental_budget_chars: int | None = None` parameter. The previous `make_prompt._budget_chars_override` hidden attribute is removed.
  - Task 2.4 Step 6: `main()` passes `args.incremental_budget_chars` through to `make_prompt` at *both* call sites (primary + sweep dispatch).
  - Task 2.4 Step 7: a CLI-level integration test spawns the script with `--incremental-budget-chars 20000`, injects a 60 KB merged-findings file, runs an incremental round, and asserts the persisted `r2-*-request.md` carries the `<!-- budget-applied: -->` note and stays within the budget. This is the proof the flag has real effect on actual prompts, not just on the unit-tested `apply_budget()` helper.

Notes:
The hidden-state criticism was correct — that approach was test-pleasing rather than implementation-pleasing. The proper-parameter route is straightforward and the new CLI test prevents future regressions from skipping the wiring.

## F4
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md` Task 2.5 Step 1 (new), Step 2 (run-to-fail), with the implementation step renumbered to Step 3.
- Change: Task 2.5 now creates `skills/external-review/tests/test_diff_caps.py` with three explicit failing tests covering the new behaviour — untracked-file count cap (15 files → ≤ 10 headings + "more untracked files elided"), per-untracked-file line cap (500 lines → line 400 absent), and global `cap_with_elision` activation on oversized assembled output ("bytes elided" marker). Step 2 runs them to verify they fail before the implementation lands in Step 3. Step 4 runs the new + existing tests together.
- Verification: the three tests in `test_diff_caps.py` are concrete, use `subprocess` to drive real git fixtures, and pin the exact assertions called out in the spec.

Notes:
TDD discipline restored to Task 2.5.

## F5
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md` Task 1.8 Step 3 (new), Step 5 (emit JSON).
- Changes:
  - Task 1.8 Step 3 (new test step): appends two tests to `test_returncode_status_persisted.py` asserting that the top-level emitted JSON `reviewers[]` entries carry `status` and `returncode` on the ok-reviewer case and the failed-reviewer case. The failed case also re-asserts that `verdict_valid` is false on the per-reviewer entry.
  - Task 1.8 Step 5 (new implementation step): edits the JSON-emit block at `external-reviewer.py:1140-1149` to add `"returncode": r.returncode` and `"status": "ok" if r.returncode == 0 else "failed"` to each per-reviewer dict in the emitted `reviewers[]` list.
  - All subsequent step numbers in Task 1.8 are bumped (Step 4 → 6, Step 5 → 7).

Notes:
This makes failed-sweep observability work end-to-end: a JSON consumer can iterate `payload["reviewers"]`, see one reviewer with `status: "failed"` while the top-level `status` remains `"ok"`, and verify the sweep-truth-table contract from spec §S1.7 without inspecting `chain.json`.
