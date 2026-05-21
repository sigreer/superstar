# Round 1 resolution

Addressed the actionable review findings from `r1-merged-findings.md`.

## Changes made

- Added tasklist-discipline regression assertions for cross-cutting close/archive docs in `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`.
- Added the archived-ID reservation note to `skills/tasklist-discipline/SKILL.md`.
- Added an `archive-cross` precheck so an already archived X-item reports `cross-cutting X1 is already archived`.
- Added command coverage for the already-archived `archive-cross` error path.
- Removed the unnecessary `skip_review_gate=True` argument from the non-cross `--no-archive` rejection test.

## Verification

- `tools/tasktool/tasktool validate --strict-format` -> ok
- `git diff --check` -> ok
- `tools/tasktool/tasktool render | rg -n "Cross-cutting|Archived cross-cutting|X15"` -> showed the active Cross-cutting section and X15 row
- `python3 -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py tools/tasktool/tests/test_commands.py -q` -> 67 passed
- `python3 -m pytest tools/tasktool/tests -q` -> 335 passed

## Notes

The X15 task row is present in this implementation worktree so review can inspect the planned work item, but lifecycle mutation through `tasktool start/close X15` remains blocked by unstaged authoritative `docs/tasklist.json` changes in the main checkout. Those main-checkout changes include the existing P1 archive cleanup that the handoff explicitly said to preserve rather than fold into this implementation branch.
