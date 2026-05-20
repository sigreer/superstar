1. Findings

F1 (Severity: blocking) `--dry-run` is specified and tested as policy-free, but the planned command body errors before reaching the dry-run branch. The spec says `--dry-run` stops after rendering the diff before conflict policy selection ([spec](docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md):101-106), and the plan test calls `migrate-from-local --dry-run` without `--accept-*` ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):1071-1079). The proposed implementation resolves `policy is None` first and raises in non-TTY contexts ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):1272-1280), so that test cannot pass. Move the dry-run return before policy resolution.

F2 (Severity: blocking) `migrate-from-local` does not honor existing authority config. The spec requires using `.tasktool/config.json` in `authority_root` when it specifies `mutation_mode` / `authoritative_branch` ([spec](docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md):80). The plan always uses `git_current_branch(authority_root)` and validates against that ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):1257-1268). That bypasses the configured authoritative branch and can migrate against the wrong branch. Load `load_config(authority_root)` first; if configured for `authoritative-checkout`, validate against that branch, otherwise derive from current branch and persist it.

F3 (Severity: blocking) The notification acceptance gate will fail because the plan passes a string into a helper that expects `Status`. Current `_notify_status` calls `status.value` ([commands.py](tools/tasktool/commands.py):69-75). The planned `_notify_status_transitions` passes `row.status.value` or `str(row.status)` ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):1358-1362). That raises inside `_notify_status` and is swallowed, so `test_migrate_emits_notify_events` ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):1176-1201) will not observe any event. Pass the enum object through, or change `_notify_status` to accept both `Status` and `str`.

F4 (Severity: important) The plan misses the spec’s “config file exists but omits `mutation_mode`” hard-error case. The spec says missing config or missing `mutation_mode` should become the sentinel unconfigured state ([spec](docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md):34-39). The plan’s replacement `_parse_tasklist` keeps `raw.get("mutation_mode", "local")` ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):139-146), so an incomplete config silently opts into local mode. Add a test for `.tasktool/config.json` with `{"tasklist": {}}` and make `_parse_tasklist` distinguish omitted from explicit `"local"`.

F5 (Severity: important) The command body references `same_repository` without adding it to imports. Current `commands.py` imports selected names from `tasktool.worktree` but not `same_repository` ([commands.py](tools/tasktool/commands.py):20-27); the planned function calls it directly ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):1240). Add it to the import block in the plan.

F6 (Severity: important) The concrete test tasks do not cover several spec-listed acceptance gates. The spec requires read-only commands beyond `render`/`validate` to work unconfigured, bootstrap `init-authority` before `init`, `init` before authority failing, `--local-root`, same-repository errors, full-field migration, and non-TTY policy behavior ([spec](docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md):143-159). The plan’s detailed tests only cover a subset ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):237-300, 1071-1201). Add explicit tests for the missing gates rather than relying on broad suite fallout.

2. Open questions / assumptions

Assumption: `migrate-from-local --dry-run` should remain usable without a policy flag, matching the spec’s ordering and the plan’s own test.

Question: Should `init-local` refuse any existing config, or only authoritative config? The plan only refuses overwriting authoritative mode ([plan](docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md):467-482), which is workable but should be stated as intentional.

3. Suggested document edits

Update Task 1 to make omitted `mutation_mode` unconfigured, not local.

Update Task 5 command body to load existing authority config, import `same_repository`, move dry-run before policy selection, and pass `Status` into `_notify_status`.

Add concrete tests for the missing spec gates listed in F6, especially `--local-root` and existing authority config branch handling.

4. Verification gaps / commands

Run:

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_authority_config.py tools/tasktool/tests/test_unconfigured_mutation.py tools/tasktool/tests/test_init_local.py tools/tasktool/tests/test_migrate.py tools/tasktool/tests/test_migrate_cli.py -v
PYTHONPATH=tools pytest tools/tasktool/tests/ -v
tools/tasktool/tasktool validate
```

Overall verdict: revise

