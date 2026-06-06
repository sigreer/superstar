# Resolution for r1

## S1.F1
Status: fixed
Evidence:
- Commit: 7a0f9541cd1778458605d7de6f7e0e2238b9118a
- Files: `skills/external-review/tests/test_resolution_gate.py:55`
- Verification: `git diff --check main..HEAD` → exit 0 (clean); `python -m pytest skills/external-review/tests/test_resolution_gate.py -q` → 2 passed in 0.89s

Notes:
Removed the stray trailing blank line left by the Task 2 test deletion. The committed HEAD had a double newline at EOF (`\n\n`); fixed to a single newline (`\n`).

## S1.F2
Status: fixed
Evidence:
- Commit: 7a0f9541cd1778458605d7de6f7e0e2238b9118a
- Files: `skills/external-review/SKILL.md:132`, `skills/subagent-driven-development/SKILL.md:331`
- Verification:
  - `skills/external-review/SKILL.md:132`: "For any kind, the next round's resolution-required gate is **bypassed** with a stderr notice. A process failure has no findings to resolve; the next round is a re-attempt of the same review, not a fix-and-re-review. For `post-slice` / `post-phase`, a fix subagent is still used when the retry itself returns findings."
  - `skills/subagent-driven-development/SKILL.md:331`: "Round N+1 of any kind exits 3 without `r{N-1}-resolution.md` or `--allow-missing-resolution`; post-slice/post-phase still delegate fixes to a subagent."

Notes:
Updated both stale lines to state the gate/bypass applies to round 2+ of any kind; post-slice/post-phase delegation language preserved.
