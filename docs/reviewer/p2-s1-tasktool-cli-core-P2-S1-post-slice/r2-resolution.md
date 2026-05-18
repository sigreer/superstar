# Resolution for r2

## F1
Status: fixed
Evidence:
- Files: `tools/tasktool/reviewer_gate.py` — `discover_chain`: if `explicit` is not absolute, resolve it as `(repo_root / explicit).resolve()` before validation
- Tests: `test_reviewer_gate.RelativeExplicitPathTests.test_relative_explicit_path_resolves`, `test_relative_explicit_path_in_check_gate` (both pass)
- CLI regression: `test_cli_integration.ReviewGateE2ETests.test_close_slice_with_relative_reviewer_chain` — passes a relative `docs/reviewer/p1-s1-post-slice` path and expects exit code 0

Notes:
Relative paths passed as `--reviewer-chain` are now resolved against `repo_root` inside `discover_chain` so `relative_to(repo_root)` in `commands.py` never sees an unresolvable path.

## F2
Status: fixed
Evidence:
- Files: `tools/tasktool/reviewer_gate.py` — added `_token_matches_name(token, name)` using `re.search(rf"(^|-){re.escape(token)}(-|$)", name)`; `discover_chain` now strips the kind suffix from the directory name before matching so the boundary regex works correctly
- Tests: `test_reviewer_gate.BoundaryMatchTests.test_p1_s1_does_not_match_p1_s10`, `test_p1_s10_does_not_match_p1_s1`, `test_p1_s1_prefix_only_no_false_ambiguity` (all pass)

Notes:
Substring `in` replaced by a hyphen-boundary regex match on the slug portion (after stripping the kind suffix), so `p1-s1` matches `p1-s1-post-slice` but not `p1-s10-post-slice`.

## F3
Status: fixed
Evidence:
- Files: `tools/tasktool/cli.py` line 53 — removed `"blocked"` from `set --status` argparse choices; valid choices are now `["ready", "in_progress", "done"]`
- Test: `test_cli_integration.SetStatusTests.test_set_blocked_exits_nonzero_with_argparse_error` — confirms non-zero exit and absence of `Traceback`/`ValidationError` in stderr

Notes:
`blocked` is set exclusively via `tasktool block --on`; removing it from `set --status` choices produces a clean argparse error message instead of an uncaught `ValidationError` traceback.

## F4
Status: fixed
Evidence:
- File: `docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md` — appended "## Post-implementation evidence" section at end of file
- Contents: 131 tests passing, commit range c363e8f→HEAD, deferred S2/S3 items, list of r2 bugfix commits

Notes:
Section appended after the "Out of scope" block. Test count updated from the reviewer's baseline of 124 to 131 (reflecting the 7 new regression tests from this round).
