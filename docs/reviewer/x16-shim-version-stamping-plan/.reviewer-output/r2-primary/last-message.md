1. Findings

F6 — Severity: important — The Task 8 publish-common conversion breaks `--dry-run` safety for both publishers. The existing scripts wrap mutating `mkdir`/`rsync` calls in `run()`, which only prints commands under `DRY_RUN=1` ([scripts/publish-to-local-codex.sh](/home/simon/Dev/sigreer/skills/superstar/scripts/publish-to-local-codex.sh:73), [scripts/publish-to-local-claude.sh](/home/simon/Dev/sigreer/skills/superstar/scripts/publish-to-local-claude.sh:74)). The plan’s replacement calls `ss_publish_rsync_payload` before checking `DRY_RUN`, and that function runs `mkdir -p` plus `rsync -aL --delete` directly ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1658), [docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1777), [docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1807)). This means `publish-to-local-*.sh --dry-run` would still mutate cache directories. Preserve the existing `run` wrapper semantics or make `ss_publish_rsync_payload` dry-run aware.

F7 — Severity: important — The concrete Claude publish snippet drops existing excludes for `.worktrees/` and `.agents/`. The live Claude publisher excludes `.git/`, `.worktrees/`, `.agents/`, `.pytest_cache/`, `__pycache__/`, and `docs/reviewer/` for both cache copies ([scripts/publish-to-local-claude.sh](/home/simon/Dev/sigreer/skills/superstar/scripts/publish-to-local-claude.sh:97), [scripts/publish-to-local-claude.sh](/home/simon/Dev/sigreer/skills/superstar/scripts/publish-to-local-claude.sh:106)). The plan’s `EXTRA_RSYNC_ARGS` omits `.worktrees/` and `.agents/` ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1805)). The following prose says to cross-check and append missing excludes, but the executable snippet should be corrected directly because copying worktrees or agent metadata into the Claude cache is a concrete regression risk.

F1 — RESOLVED — The bump-version test now invokes the symlinked script inside `tmp_path/scripts/bump-version.sh`, so the script’s own `dirname "$0"` root resolution lands in the fake repo rather than the real checkout ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:117), [docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:127)).

F2 — RESOLVED — The hook handshake is now explicitly wired before `parser.parse_args(argv)`, matching the `--help` integration test expectation ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1510), [docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1524)).

F3 — RESOLVED — The publish-common design now parameterizes manifest subpath and required payloads, and the hook rewrite handles both Claude command variants ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1700), [docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1722), [docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1815)). F6/F7 are new regressions in the same task, not a continuation of the prior F3 issue.

F4 — RESOLVED — Task 6 now references the actual `_seed_repo(tmp_path)` test style and asserts against `REPO / "VERSION"` rather than a fabricated consumer-repo `VERSION` ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1098), [docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:1103)).

F5 — RESOLVED — The reviewer-agent installer now mirrors the external-reviewer cache-root `current/` preference before stamping the source root ([docs/plans/2026-05-21-X16-shim-version-stamping.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-21-X16-shim-version-stamping.md:775)).

2. Open questions / assumptions

No remaining open questions from round 1. The deploy check ambiguity was resolved by comparing each shim against its own stamped source root’s `VERSION` while keeping plugin cache checks tied to the dev checkout version.

3. Suggested document edits

Update `ss_publish_rsync_payload` to accept a runner function or honor `DRY_RUN=1` internally, and add a regression assertion that `--dry-run` does not create or modify cache directories.

Replace the Claude `EXTRA_RSYNC_ARGS` snippet with the full existing exclude set: `.git/`, `.worktrees/`, `.agents/`, `.pytest_cache/`, `__pycache__/`, and `docs/reviewer/`.

4. Verification gaps / commands that should be run

Add dry-run checks around:

```bash
bash scripts/publish-to-local-codex.sh --skip-codex-add --cache-root "$tmp/cache" --dry-run
bash scripts/publish-to-local-claude.sh --skip-claude-update --cache-root "$tmp/cache" --dry-run
```

Then run the planned publish regressions:

```bash
bash tests/codex-plugin-sync/test-publish-to-local-codex.sh
bash tests/claude-code/test-publish-to-local-claude.sh
```

Overall verdict: revise

