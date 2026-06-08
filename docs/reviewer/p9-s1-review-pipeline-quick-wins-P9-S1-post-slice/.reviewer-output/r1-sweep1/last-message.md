1. Findings

F1. Severity: blocking — `git diff --check main..HEAD` fails on a committed whitespace error: `skills/external-review/tests/test_resolution_gate.py:55: new blank line at EOF.` This contradicts the claimed clean verification and leaves a standard completion gate failing, even though the pytest suite passes.

F2. Severity: minor — Some guidance still describes the resolution bypass/gate as post-slice/post-phase-specific after the implementation made it kind-independent. See `skills/external-review/SKILL.md:132` and `skills/subagent-driven-development/SKILL.md:331`. The canonical resolution section is updated at `skills/external-review/SKILL.md:247`, but these stale lines can mislead future spec/plan review retries.

2. Open questions / assumptions

No open questions. I treated the unchecked boxes in the plan as implementation instructions, not a live completion checklist.

3. Suggested document edits

Update the stale guidance lines to say process-failure bypass and resolution-gate refusal apply to round 2+ for any kind, while post-slice/post-phase still use fix subagents.

4. Verification gaps / commands that should be run, if any

Verified:
- `python -m pytest skills/external-review/tests -q` -> `297 passed`
- `tasktool artifact status P9.S1 --strict` -> `artifact status: ok`
- `tasktool validate` -> `ok`

Must rerun after fixing F1:
- `git diff --check main..HEAD`
- optionally `python -m pytest skills/external-review/tests/test_resolution_gate.py -q`

Overall verdict: revise