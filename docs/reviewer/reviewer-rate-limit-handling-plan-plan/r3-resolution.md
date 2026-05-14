# r3 Resolution — 2026-05-14-reviewer-rate-limit-handling-plan.md

- Round: r3
- Response: r3-2026-05-14T1957-response.md
- Resolved by: plan-document edits only (no code changes; session-level rate-limit bypass active)

---

## F1

Status: fixed (prior round — carried forward as resolved)

Already fixed in r2. No further changes needed.

---

## F2

Status: fixed

**Evidence:**

Task 2.0 "In `main()`" instruction completely replaced. The new block specifies the complete top-of-main() structure: `args = parse_args()` → `--state-file` hoist → dispatch all four non-`review` subcommands (`manual-approve`, `ingest-response`, `show-limit`, `clear-limit`) BEFORE any access to `args.kind`, `args.file`, `args.context`, or `args.output_dir`. The rationale (which attrs are missing on which subcommands) is spelled out explicitly so a worker cannot place the dispatch in the wrong location.

Tasks 5.1, 5.2, 5.3 dispatch snippets (`if args.command == "manual-approve": ...` etc.) each replaced with a single-line note: "Do NOT add a dispatch branch in main() here — dispatch is defined once in Task 2.0." Each task now only adds its argparse sub-parser and handler function.

---

## F3

Status: fixed

**Evidence:**

Task 2.0 now includes a second instruction block specifying approach (a): after the `if manifest is None:` manifest initialisation block, call `write_manifest(manifest_path, manifest)` immediately — before the first `run_one_reviewer` call. The rationale (chain.json doesn't exist on round 1; rate-limit handlers read it) is stated. The exact code block is provided.

Tasks 2.4 and 2.5 `_manifest = read_manifest(...)` / `if _manifest is not None:` guards both replaced with a direct read + unconditional append, citing "chain.json is guaranteed by Task 2.0 eager-write; no None guard needed."

---

## F4

Status: fixed

**Evidence:**

1. `--sweep-policy always` changed to `--sweep-policy first-round` in the Task 5.4 test snippet. The step-3 description updated to note that `always` is not a valid choice and to list the real choices.

2. The `ReviewerResult(...)` return in the sweep branch now includes `status="rate-limited"` as an explicit keyword argument with an inline comment "CRITICAL — overrides the dataclass default 'ok'". Field-by-field instantiation used (no positional args).

3. The `else:` branch (primary rate-limited) had `new_round = { ... }` and `raise ReviewerRateLimited(...)` placeholder ellipses. Both replaced with verbatim concrete forms: the full `new_round` dict (identical shape to Task 2.4) and the full `ReviewerRateLimited(...)` kwargs (identical to Task 2.4).

---

## Notes

- The `--independent-reviewers 1` + `--sweep-policy first-round` combination triggers a sweep on round 1. The test uses a sentinel file to make the primary succeed and the sweep fail; this is the approach described in Task 5.4 step 1 and is consistent with the "Option A" dispatch mechanism note.
- No test-count progression numbers needed updating — the Task 2.0 changes add no new test files; they only modify existing implementation instructions.
