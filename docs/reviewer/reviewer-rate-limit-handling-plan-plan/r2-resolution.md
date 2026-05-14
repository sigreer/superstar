# Resolution for r2

## F1
Status: fixed
Evidence:
- Files: docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md §Slice 2 Task 2.0 (new)
- Verification: search the plan for `--state-file` inside the Task 2.0 block — it appears on the `review` subparser (`sp_review.add_argument("--state-file", ...)`). Also verify in `main()` step 3: `if getattr(args, "state_file", None): os.environ["AGENT_REVIEWER_STATE_FILE"] = args.state_file` is added immediately after `args = parse_args()`, before any state access.

Notes: The `--state-file` flag is added to the `review` subparser inside the new Task 2.0 (argparse refactor). Since Task 2.0 must land before any Slice 5 work, all subcommands gain `--state-file` as part of their individual `subparsers.add_parser(...)` additions in Tasks 5.1–5.3. The test file `test_argparse_review_subparser.py` asserts `--state-file` appears in `review --help`.

## F2
Status: fixed
Evidence:
- Files: docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md §Slice 2 Task 2.0 (argparse refactor), §5.1 (manual-approve), §5.2 (ingest-response)
- Verification:
  - `resolve_chain_dir`: does not exist in the script. All occurrences in Tasks 5.1 and 5.2 replaced with inline chain resolution using `chain_folder_name(target, kind, work_id)` + `discover_legacy_chain(...)` — the same pattern as `main()` lines 1101–1113. Comments in the plan cite the real helper names and line numbers.
  - `write_manifest`: real signature is `write_manifest(path: Path, data: dict)` (line 285). All snippets corrected to `write_manifest(chain_dir / "chain.json", manifest)`. Notes added at each call site.
  - `read_manifest`: real signature is `read_manifest(path: Path)` (line 272). All snippets corrected to `read_manifest(chain_dir / "chain.json")`.
  - `parse_verdict`: real return shape is `tuple[str | None, bool]` (line 1503). Task 5.2 `run_ingest_response` corrected to `verdict, valid = parse_verdict(reformatted)`, using `valid` (not `verdict is not None`) for the `verdict_valid` field.
  - `add_subparsers()`: Task 2.0 creates the `subparsers` object. Tasks 5.1–5.3 now reference the `subparsers` object from T2.0 (comments added to each snippet).

## F3
Status: fixed
Evidence:
- Files: docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md §Task 2.4 (Step 3), §Task 2.5 (Step 3), §Task 4.1 (Step 3)
- Verification:
  - Task 2.4 (post-failure detection): after saving state, the code now reads `chain_dir / "chain.json"`, appends a new round entry with `status: "rate-limited"`, `returncode: None`, `verdict: None`, `verdict_valid: False`, `reset_at`, `reviewer_cmd`, `request`, `response`, `limited_at`, then writes the manifest back — BEFORE raising `ReviewerRateLimited`.
  - Task 2.5 (pre-spawn check): same structure — the first-refusal branch appends a new round to chain.json before raising. The coalesced path in T4.1 updates the head round in place.
  - Task 4.1 (coalescing): the existing manifest read/write logic was present; corrected the helper call shapes (`read_manifest(manifest_path)`, `write_manifest(manifest_path, chain_manifest)`) and noted the first-refusal vs coalescing branch distinction per spec §7.5.

Notes: The exact round entry shape used matches the spec §5 and §7.1 required fields. `returncode: None` is used in both pre-spawn (subprocess never ran) and post-failure (subprocess ran but returncode isn't authoritative for the rate-limited interpretation). The `response` field points to the artifact written by `write_rate_limited_artifact`.

## F4
Status: fixed
Evidence:
- Files: docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md §Task 5.4 (fully rewritten)
- Verification:
  - Confirmed from script lines 1353–1368: sweeps are `run_one_reviewer(role="sweep", sweep_index=k, ...)` calls in a for-loop. No `REVIEWER_ROLE` env var is set anywhere in the script.
  - The test now uses a sentinel-file approach: a single reviewer script that succeeds on the first invocation (primary) and emits a rate-limit error on the second (sweep1). This uses only mechanisms the real script exposes.
  - The implementation now branches inside `run_one_reviewer` on `role`: when `role == "sweep"` and rate-limit is detected, it saves state and returns a `ReviewerResult` with `status="rate-limited"` instead of raising `ReviewerRateLimited`. A `status: str` field is added to the `ReviewerResult` dataclass so the round-entry builder can record it correctly.
  - The old fictional `for sweep_idx, sweep_cmd in enumerate(sweeps, ...)` loop referencing a non-existent `sweeps` variable has been removed.

Notes: The implementation sketch's `reviewers_record.append(...)` reference was also fictional (there is no such variable in the script's sweep path). The plan now correctly targets `run_one_reviewer`'s return value since that function returns `ReviewerResult` to `main()`'s sweep loop.
