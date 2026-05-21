1. Findings

F1. Severity: blocking. The spec is ambiguous and partly regressive about whether the documented publish scripts still refresh the live `external-reviewer` shim. Today both publishers end by reinstalling the shim against `current/` (`scripts/publish-to-local-codex.sh:164-165`, `scripts/publish-to-local-claude.sh:188-189`), and existing regression tests assert the generated shim points at `/current/skills/external-review/scripts/external-reviewer.py` (`tests/codex-plugin-sync/test-publish-to-local-codex.sh:76`, `tests/claude-code/test-publish-to-local-claude.sh:77`). The spec says the wrappers become thin `publish-common.sh` callers (`docs/specs/2026-05-21-X16-shim-version-stamping-design.md:236-242`), then says `deploy.sh` reruns installers (`docs/specs/2026-05-21-X16-shim-version-stamping-design.md:252-260`), and then claims default deploy points shims at the dev checkout (`docs/specs/2026-05-21-X16-shim-version-stamping-design.md:262`). That leaves implementers free to remove the currently tested publish-side refresh, which reintroduces the stale-shim path X14 just fixed. Specify whether direct `publish-to-local-*` still restamps `external-reviewer`, and define one source-root policy for deploy vs direct publish.

F2. Severity: blocking. `VERSION` is specified as a repo-root file and as the only runtime source consulted by shims (`docs/specs/2026-05-21-X16-shim-version-stamping-design.md:46-69`), but the Codex publisher currently publishes `plugins/superstar` as its source (`scripts/publish-to-local-codex.sh:54-55`), not the repo root. That payload has the manifest plus symlinked `skills`, `hooks`, `tools`, and `assets`, but no top-level `VERSION` path is specified. As written, `deploy.sh --check` promises to read `~/.codex/plugins/cache/.../current VERSION` (`docs/specs/2026-05-21-X16-shim-version-stamping-design.md:288-290`), while a shim pointed at Codex `current/` would skip drift refusal because `$SOURCE_ROOT/VERSION` is unreadable. Add an explicit Codex-payload rule: either publish/copy root `VERSION` into `plugins/superstar` caches, add a symlink/file under `plugins/superstar/VERSION`, or forbid Codex `current/` as a shim source root.

F3. Severity: important. `$HOME` literalization is specified for stamped `source-root` (`docs/specs/2026-05-21-X16-shim-version-stamping-design.md:85-87`), but the diagnostics and Python hook handshake do not say to expand that literal before filesystem checks or rerun-path construction. The hook flow extracts `superstar-hook-source-root`, reads `$source_root/VERSION`, and reconstructs `bash <source-root>/tools/tasktool/install.sh --hook --force` (`docs/specs/2026-05-21-X16-shim-version-stamping-design.md:197-212`). If Python treats `$HOME/Dev/...` as a literal path, the check silently skips or prints an uncopyable rerun path. Add a required parser rule for headers: expand leading `$HOME/` and `~/` for reads, existence checks, and displayed absolute paths, while preserving the raw stamped value if needed for diagnostics.

F4. Severity: important. The hook marker migration is under-specified. Current `install.sh --hook` only recognizes existing hooks by grepping `tasktool-pre-commit-hook` before allowing a non-force reinstall (`tools/tasktool/install.sh:17-23`), and current tests require repeated non-force installs to remain idempotent (`tools/tasktool/tests/test_pre_commit_hook.py:131-136`). The new template marker switches to `# superstar-hook` / `superstar-hook-name: tasktool-pre-commit` (`docs/specs/2026-05-21-X16-shim-version-stamping-design.md:185-195`). Without an explicit installer migration rule, the second install of a newly stamped hook can be refused as “not a tasktool hook,” or old hooks may need unnecessary `--force`. Specify that the installer accepts both old and new markers during migration and that the idempotency test is updated.

2. Open questions / assumptions

- Is the desired long-term shim source root the dev checkout, Claude/Codex `current/`, or configurable per deploy mode? The spec currently says all three in different places.
- Should `deploy.sh --check` inspect both Codex and Claude cache `current/` trees even when `--codex-only` or `--claude-only` is used?
- Should `VERSION` be included in plugin payload verification lists, alongside `skills/...`, `hooks/...`, and `tools/...`?

3. Suggested document edits

- In section 8, add a “source-root policy” subsection with a truth table for direct Codex publish, direct Claude publish, full deploy, `--codex-only`, `--claude-only`, and `EXTERNAL_REVIEWER_SOURCE_ROOT`.
- Add `VERSION` to the publish payload contract and to the publish tests for both cache roots.
- Add header parsing rules for diagnostics: parse key/value comments, expand `$HOME`, report malformed or missing stamp fields distinctly from `DRIFT`.
- Add hook installer migration requirements: accept old `tasktool-pre-commit-hook` and new `superstar-hook-name` markers, preserve non-force idempotency, and update tests.

4. Verification gaps / commands

- `bash tests/codex-plugin-sync/test-publish-to-local-codex.sh`
- `bash tests/claude-code/test-publish-to-local-claude.sh`
- `python3 -m pytest skills/external-review/tests/test_external_reviewer_installer.py tools/tasktool/tests/test_pre_commit_hook.py -q`
- New tests should explicitly cover Codex `current/VERSION`, `$HOME` expansion in `deploy.sh --check`, direct publish shim restamping, and hook reinstall idempotency across old and new markers.

Overall verdict: revise

