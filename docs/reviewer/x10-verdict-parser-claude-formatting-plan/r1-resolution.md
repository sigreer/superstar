# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md` Task 5 Step 2
- Verification: added a new `test_prompt_has_literal_verdict_trailer` to `test_prompt_contract.py` that asserts (a) the new trailer paragraph is present, (b) the don'ts including the literal `**Verdict: ready**` example are present, (c) the old `5. Overall verdict` numbered-list form is absent. This makes the prompt change verifiable from CI.

## F2
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md` Task 6 (header + Step 2 + Step 3)
- Verification: Task 6 now explicitly states that `tasktool close` skips the review gate for `cross` items (citing `tools/tasktool/commands.py:397`) and that the coordinator enforces the gate manually before invoking close. The `--reviewer-chain` flag is removed from the close command (it is phase/slice-only).

## F3
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md` Task 2 Step 2
- Verification: replaced the "12 tests fail" claim with a per-test table that correctly identifies 5 expected failures (2 positive bare-verdict tests + 3 `parse_reformatted_verdict` helper/fixture tests) and 7 tests that pass under the current strict parser. Explains why the negatives are no-ops now and become live assertions after Task 3.

## F4
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md` File map
- Verification: file map updated to "12 new test functions" with the 5-fail/7-pass split, and a new entry for `test_prompt_contract.py` (+1 test for the new wording).
