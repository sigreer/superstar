**Findings**

F1 — RESOLVED — Relative `--reviewer-chain` paths now resolve against `repo_root` before validation in `tools/tasktool/reviewer_gate.py:28-34`, with CLI regression coverage in `tools/tasktool/tests/test_cli_integration.py:191`.

F2 — RESOLVED — Chain discovery now uses hyphen-bounded token matching in `tools/tasktool/reviewer_gate.py:20-23` and applies it after stripping the `-post-slice` suffix at `tools/tasktool/reviewer_gate.py:39-42`. Regression tests cover `p1-s1` vs `p1-s10`.

F3 — RESOLVED — `tasktool set --status blocked` is no longer accepted by argparse; choices are now `ready`, `in_progress`, `done` in `tools/tasktool/cli.py:50-53`, with clean-error regression coverage.

F4 — RESOLVED — The plan now includes post-implementation evidence at `docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:3130-3138`, including 131 passing tests and deferred S2/S3 scope.

**Open Questions / Assumptions**

No remaining questions. The only dirty worktree item I saw was the current r3 reviewer request file, which is expected review-chain output.

**Suggested Document Edits**

None.

**Verification**

Ran:

`PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`  
Result: 131 tests passed.

Also ran `bash -n tools/tasktool/install.sh` and schema JSON validation successfully.

**Overall verdict: ready**