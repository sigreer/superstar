1. Findings

F1 — Severity: blocking — The Task 1 bump-version tests do not run against the temporary repo and can mutate the real checkout. The test defines `SCRIPT = REPO_ROOT / "scripts" / "bump-version.sh` and invokes that absolute path directly, while the comment-created symlink at `tmp_path/scripts/bump-version.sh` is never used ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:98), [docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:102), [docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:124)). The existing script resolves `REPO_ROOT` from `dirname "$0"`, not from `cwd` ([scripts/bump-version.sh](/home/simon/Dev/sigreer/skills/superstar/scripts/bump-version.sh:13)), so `test_bump_writes_plain_version` would run `bash /real/repo/scripts/bump-version.sh 1.2.4` and rewrite the real repo’s declared files, not `tmp_path` ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:139)). Fix the harness to invoke `tmp_path/scripts/bump-version.sh`, or add an explicit env/flag override for `REPO_ROOT` before relying on these tests.

F2 — Severity: blocking — The Task 7 plan asserts the hook handshake runs on `tasktool --help`, but the proposed wiring places the check after `parser.parse_args(argv)` ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1475)). In argparse, `--help` exits during `parse_args`, so the planned integration test expecting `python3 -m tasktool --help` to return `1` on drift cannot pass ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1505), [docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1511)). Either move the check before parsing, or change the tests/spec claim that `--help` participates in the handshake.

F3 — Severity: important — The publish-common extraction is underspecified for Claude and the concrete snippet would regress it. `ss_publish_verify_payload` hardcodes `.codex-plugin/plugin.json` ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1677)), but the current Claude publisher verifies `.claude-plugin/plugin.json` ([scripts/publish-to-local-claude.sh](/home/simon/Dev/sigreer/skills/superstar/scripts/publish-to-local-claude.sh:145)). The shared hook rewrite snippet also preserves only the Codex-style replacement, while the existing Claude script handles both `"${CLAUDE_PLUGIN_ROOT:-.}/hooks/run-hook.cmd"` and `"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd"` ([scripts/publish-to-local-claude.sh](/home/simon/Dev/sigreer/skills/superstar/scripts/publish-to-local-claude.sh:115)). Parameterize manifest path/type and preserve both rewrite variants before extracting.

F4 — Severity: important — Task 6’s proposed tests do not match the existing test structure and seed the wrong `VERSION`. The plan says to assume a `test_repo` fixture and `_install_hook` helper exist ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1074)), but the current file uses `_seed_repo(tmp_path)` and no such fixture exists. More importantly, the test writes `VERSION` into the consumer repo ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1078)), while the installer snippet reads `SOURCE_ROOT/VERSION` from the Superstar source checkout ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1183), [docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1196)). Adapt these tests to the existing `_seed_repo` style and assert the actual source `VERSION`, or create a fake installer/source-root harness.

F5 — Severity: important — The reviewer-agent installer implementation does not preserve the spec’s `current/` preference. The spec says the new installer should resolve `SOURCE_ROOT` “with the same `current/` preference” as external-reviewer ([docs/specs/2026-05-21-X16-shim-version-stamping-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-21-X16-shim-version-stamping-design.md:157)), but the plan’s installer sets `SOURCE_ROOT="${EXTERNAL_REVIEWER_SOURCE_ROOT:-$PLUGIN_ROOT}"` and stops there ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:763)). If this installer is ever run from a versioned plugin cache, it can stamp a moving versioned directory instead of stable `current/`, unlike the existing external-reviewer installer pattern ([skills/external-review/install.sh](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/install.sh:10)). Add the same cache-root detection or explicitly revise the spec/source-root policy.

2. Open questions / assumptions

Is `deploy.sh --check` intentionally comparing every shim against the dev checkout’s `VERSION`, or should each shim be compared against its own stamped `source-root/VERSION`? The spec’s status lattice says “stamped version matches `$SOURCE_ROOT/VERSION`,” which reads like the stamped source root, but the plan’s concrete `deploy.sh` snippet compares all shims to `REPO_ROOT/VERSION`.

Should `tasktool --help` be blocked by stale hook drift? The plan currently says yes via the integration test, but the proposed implementation says no by construction.

3. Suggested document edits

Update Task 1’s test harness to invoke the temp symlink path, or introduce a supported `SUPERSTAR_REPO_ROOT`/`VERSION_BUMP_CONFIG` test override and document that in the implementation steps.

Revise Task 7 so the handshake placement and `--help` tests agree.

Rewrite Task 8’s `publish-common.sh` design around provider-specific inputs: source root, manifest path, manifest subpath, required payload list, hook rewrite variants, and CLI update command.

Rewrite Task 6 tests against the actual `tools/tasktool/tests/test_pre_commit_hook.py` helpers instead of hypothetical fixtures.

4. Verification gaps / commands that should be run

Run these after editing the plan snippets:

```bash
python3 -m pytest scripts/tests/test_bump_version_plain_format.py -v
python3 -m pytest tools/tasktool/tests/test_pre_commit_hook.py -v
python3 -m pytest tools/tasktool/tests/test_hook_handshake.py -v
bash tests/codex-plugin-sync/test-publish-to-local-codex.sh
bash tests/claude-code/test-publish-to-local-claude.sh
```

Also add a dry-run/manual guard before any bump-version test that can write declared files, because the current proposed test can rewrite the real checkout.

Overall verdict: revise