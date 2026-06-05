1. Findings

F1 Severity: important - Two verification commands are not shell-executable as written because the `-k` expression is unquoted. In `docs/plans/2026-06-05-P8.S1-close-gate-lifecycle-auto-commit.md:424` and `:689`, the shell passes `or` / trailing terms as pytest path arguments; I verified this fails with `ERROR: file or directory not found: or`. Use `-k 'set_done or set_non'` and `-k 'autocommit or no_commit or commit_failure'`.

F2 Severity: important - The plan does not add command-level coverage for the spec’s `--no-stage` acceptance case. The spec requires `--no-stage` to mean “no staging and no commit” (`docs/specs/2026-06-05-P8.S1-close-gate-lifecycle-auto-commit-design.md:71`, `:120`), but the plan only tests `_git_commit_scoped` with `STAGE_AFTER_WRITE = False` directly (`docs/plans/2026-06-05-P8.S1-close-gate-lifecycle-auto-commit.md:535-543`). That misses CLI plumbing and close/prune call-site behavior.

2. Open questions / assumptions

No open questions. I verified the live `P8.S1` row, `tasktool schedule P8`, and `tasktool surface check P8`; the scheduling/surface claims in the plan match current tracker output.

3. Suggested document edits

- Quote the two pytest `-k` expressions on lines 424 and 689.
- Add at least one CLI-level `--no-stage` test for close, and preferably prune too:
  - `tasktool --no-stage close P1.S1 --skip-review-gate`
  - assert status persisted in the worktree file, `git diff --cached --name-only` does not include `docs/tasklist.json`, and the last commit remains the previous one.
- Optionally mention that the `--no-stage` test protects the global CLI flag path in `cli.py:42` / `cli.py:359`, not only the helper.

4. Verification gaps / commands

Run after edits:

```bash
python -m pytest tools/tasktool/tests/test_close_gate.py -v -k 'set_done or set_non'
python -m pytest tools/tasktool/tests/test_close_gate.py -v -k 'autocommit or no_commit or commit_failure'
python -m pytest tools/tasktool/tests/test_close_gate.py -v -k 'no_stage or commit_scoped'
python -m pytest tools/tasktool/tests -q
```

Overall verdict: ready with small edits

