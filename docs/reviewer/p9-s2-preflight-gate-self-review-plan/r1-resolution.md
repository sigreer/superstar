# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md` — Task 2 Step 1 `_repo()` helper
- Verification: `_repo()` now runs `git init -q` before invoking the script, so `run_preflight` → `repo_root()` (`git rev-parse --show-toplevel`, `check=True`) succeeds. A comment documents why the git repo is required. This matches the review subprocess harness convention.

Notes:
Kept `preflight` using the existing `repo_root()` convention (the reviewer's open question) rather than allowing a non-git cwd — consistent with every other subcommand, and paths are resolved relative to the repo root by design.

## F2
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md` — Task 2 Step 1, new "AC2: each check class exercised THROUGH the standalone subcommand" test group
- Verification: added six focused subprocess tests, one per AC2 check class: `test_subcommand_placeholder_failure`, `test_subcommand_dangling_link_failure`, `test_subcommand_dangling_backtick_warning`, `test_subcommand_missing_section_failure`, `test_subcommand_missing_context_failure`, `test_subcommand_oversized_context_warning`. Each asserts the exit code and that the expected `check` value appears in the JSON failures/warnings.

## F3
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-09-P9.S2-preflight-gate-self-review.md` — Task 3 Step 1, new `test_schema_too_new_aborts_before_preflight`
- Verification: the test pre-seeds the `plan-spec` chain folder with `chain.json` `schema_version: 999` and a target that would also trip preflight, then asserts the review aborts with exit 4 carrying the `schema_version` message (not preflight findings) — proving manifest-read-before-preflight ordering. Also addressed the reviewer's suggested edit: Task 3 Step 7 now instructs staging any modified `review` fixtures alongside the new test file.

Notes:
Both schema-too-new and preflight failures return exit 4, so the test distinguishes them by stderr content (`schema_version` present, `preflight` absent) rather than by exit code, which matches the spec's "shared code, sequential" design.
