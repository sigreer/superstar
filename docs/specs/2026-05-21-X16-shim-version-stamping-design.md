# X16 — Stamp installed shims and enforce version drift refusal

**Status:** spec
**Work ID:** X16
**Created:** 2026-05-21

## Problem

Superstar installs executables outside the repo (`~/.local/bin/external-reviewer`, `~/.local/bin/reviewer-agent`, `~/.local/bin/tasktool`) and per-repo (`.git/hooks/pre-commit`). When the source code changes but those installed copies/shims don't get re-deployed, behaviour silently diverges: bumps appear to land everywhere, but the same errors keep firing because a stale shim is still being invoked. The current install scripts have no runtime self-check; the bump script has no concept of "files installed outside the repo"; and there is no diagnostic that surfaces drift.

A secondary problem: the four installed files use two different patterns. Three are bash redirect shims (cheap re-deploys), one (`reviewer-agent`) is a full content copy of a wrapper script (silent content drift on every change). The compat shim at `skills/project-setup/scripts/external-reviewer-shim.py` adds a third pattern (per-repo Python shim) without a clear benefit anymore now that the global `external-reviewer` is the canonical bridge.

## Goals

1. **Make stale installed shims fail loudly,** not silently invoke old code.
2. **Make the install patterns uniform** — all three global shims become thin bash redirects to source.
3. **Make bump-version.sh purely a source-state mutator.** No install side-effects. Existing deploy/publish scripts remain the only thing that mutates live machine entrypoints.
4. **Give the user a one-shot diagnostic** that surfaces source-vs-installed drift across all four files.
5. **Drop dead weight:** remove the project-setup compat shim and its scaffolding.

## Non-goals

- Auto-discovery of multiple Superstar checkouts. A shim's source root is fixed at install time; switching checkouts means re-running install.
- Stamping the materialized plugin cache `current/` trees as separately versioned artifacts. They are deploy outputs of `VERSION`, verified by `deploy.sh --check`, not stamped.
- A separate `tasktool doctor` command. Deferred — diagnostics live in `deploy.sh --check` for now.
- Changes to provider-bypass safety policy in `reviewer-agent`. The wrapper's runtime contract stays identical.

## Files in scope

| Path | Pattern after this change | Installer |
|---|---|---|
| `~/.local/bin/external-reviewer` | Bash redirect shim (unchanged pattern) | `skills/external-review/install.sh` |
| `~/.local/bin/reviewer-agent` | **Converted** from copy to bash redirect shim | New `skills/project-setup/install-reviewer-agent.sh` |
| `~/.local/bin/tasktool` | Bash redirect shim (unchanged pattern) | `tools/tasktool/install.sh` |
| `<repo>/.git/hooks/pre-commit` | Bash copy (necessarily — git enforces the path); stamped header, runtime checked by tasktool | `tools/tasktool/install.sh --hook` |

## Removals

- Delete `skills/project-setup/scripts/external-reviewer-shim.py`.
- Delete the project-setup precondition row 7b and its surrounding compat-shim language in `skills/project-setup/SKILL.md`.
- Delete `skills/external-review/tests/test_external_reviewer_compat_shim.py`.
- Old handoff documents that hardcode `python3 scripts/external-reviewer.py` are out of support. The break is intentional and loud.

## Design

### 1. Single source of truth: top-level `VERSION` file

Add a single-line plain-text file at the repo root:

```
6.3.2
```

(trailing newline; no whitespace).

`.version-bump.json` gains a new declared file with `"format": "plain"`:

```json
{ "path": "VERSION", "format": "plain" }
```

`scripts/bump-version.sh` learns two new code paths:

- `read_plain_field(file)` — `head -n1 "$file" | tr -d '[:space:]'`.
- `write_plain_field(file, value)` — `printf '%s\n' "$value" > "$file"`.

Both `--check` and `--audit` print VERSION as a normal row, not a special case. The existing "all declared files in sync" check includes it.

VERSION is the only file every shim reads at runtime. The JSON manifests stay where they are; they remain bumped in lock-step but are not consulted by shims.

### 2. Shim stamp header (uniform across all three installers)

Every generated shim carries this header block, with values interpolated at generation time:

```bash
#!/usr/bin/env bash
# superstar-shim
# superstar-shim-name: external-reviewer
# superstar-shim-version: 6.3.2
# superstar-shim-source-root: $HOME/Dev/sigreer/skills/superstar
# superstar-shim-installer: skills/external-review/install.sh
# superstar-shim-generated-at: 2026-05-21T14:23:07Z
```

Notes:
- `source-root` stores `$HOME/...` literally when the resolved root is under `$HOME`, mirroring the existing `external-reviewer` installer behaviour. This keeps the shim portable across user accounts.
- `generated-at` distinguishes "same version, regenerated against a different `current/` root" from "untouched since last bump" during diagnostics.
- `target` is intentionally omitted — redundant with the shim's own file path; diagnostics already know where they found the file.

### 3. Shared runtime check fragment

A template fragment lives at `scripts/lib/shim-version-check.sh`:

```bash
# Embedded into every generated Superstar shim.
# Hard-exits only if BOTH source VERSION and stamped shim version are readable
# AND they differ. Missing/unreadable VERSION is treated as 'cannot compare' and
# the shim execs normally (existing path-resolution errors handle the broken
# case more loudly than a spurious version warning would).
__superstar_check_version() {
    local shim_version="$1"
    local shim_name="$2"
    local source_root="$3"
    local installer="$4"

    local version_file="$source_root/VERSION"
    [[ -r "$version_file" ]] || return 0
    local src_version
    src_version="$(head -n1 "$version_file" 2>/dev/null | tr -d '[:space:]')"
    [[ -n "$src_version" && -n "$shim_version" ]] || return 0

    if [[ "$src_version" != "$shim_version" ]]; then
        printf 'ERROR: %s shim is %s but Superstar source is %s\n' \
            "$shim_name" "$shim_version" "$src_version" >&2
        printf 'Re-run: bash %s/%s\n' "$source_root" "$installer" >&2
        exit 1
    fi
}
```

Each installer reads this fragment and inlines it into the generated shim. The shim header values are passed as arguments to `__superstar_check_version` so the fragment itself contains no installer-specific values — one source of truth, three identical embeddings.

Generated shim shape (illustrative — external-reviewer):

```bash
#!/usr/bin/env bash
# superstar-shim
# superstar-shim-name: external-reviewer
# superstar-shim-version: 6.3.2
# superstar-shim-source-root: $HOME/Dev/sigreer/skills/superstar
# superstar-shim-installer: skills/external-review/install.sh
# superstar-shim-generated-at: 2026-05-21T14:23:07Z

<inlined __superstar_check_version function from scripts/lib/shim-version-check.sh>

__superstar_check_version \
    "6.3.2" \
    "external-reviewer" \
    "$HOME/Dev/sigreer/skills/superstar" \
    "skills/external-review/install.sh"

exec python3 "$HOME/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py" "$@"
```

### 4. Strict failure semantics

A shim hard-exits (status 1, no `exec`) **if and only if** all three hold:

1. `$SOURCE_ROOT/VERSION` is readable.
2. The stamped `shim-version` value is non-empty.
3. The two values differ after whitespace-trim.

Any other state — VERSION missing, VERSION empty, stamped value missing — and the shim execs as normal. The existing path-resolution errors (source script not found, etc.) are louder and more diagnostic than a half-informed version warning.

### 5. `reviewer-agent` migration

New file `skills/project-setup/install-reviewer-agent.sh`. Mirrors the structure of `skills/external-review/install.sh`:

- Resolves `SOURCE_ROOT` (with the same `current/` preference and `$HOME` literalization).
- Verifies `$SOURCE_ROOT/skills/project-setup/scripts/reviewer-agent` exists and is executable.
- Generates `${EXTERNAL_REVIEWER_BIN:-$HOME/.local/bin}/reviewer-agent` as a thin bash redirect:

```bash
#!/usr/bin/env bash
# superstar-shim
# superstar-shim-name: reviewer-agent
# superstar-shim-version: 6.3.2
# superstar-shim-source-root: $HOME/Dev/sigreer/skills/superstar
# superstar-shim-installer: skills/project-setup/install-reviewer-agent.sh
# superstar-shim-generated-at: 2026-05-21T14:23:07Z

<inlined __superstar_check_version>

__superstar_check_version "6.3.2" "reviewer-agent" "$HOME/Dev/sigreer/skills/superstar" "skills/project-setup/install-reviewer-agent.sh"

exec bash "$HOME/Dev/sigreer/skills/superstar/skills/project-setup/scripts/reviewer-agent" "$@"
```

- **Self-test:** `bash -n "$TARGET"` (syntax check) plus confirming the source script resolves and is executable. No live reviewer invocation. `reviewer-agent` has no `--help` mode and its body bails on missing env vars, so `--help` is not a viable self-test for this installer; `bash -n` is the correct tool here even where `external-reviewer`'s installer uses `--help`.

Existing copy-based installs at `~/.local/bin/reviewer-agent` are not version-stamped; the next `deploy.sh` (which re-runs all installers with `--force`) replaces them in place. The old copy disappears.

### 6. `tasktool` ↔ pre-commit hook handshake

Hook template `tools/tasktool/templates/pre-commit-tasktool` gains a stamped header block at install time. `tools/tasktool/install.sh --hook` interpolates the values, the same shape as a shim header but using `superstar-hook-*` keys to make the failure message obvious:

```bash
#!/usr/bin/env bash
# superstar-hook
# superstar-hook-name: tasktool-pre-commit
# superstar-hook-version: 6.3.2
# superstar-hook-source-root: $HOME/Dev/sigreer/skills/superstar
# superstar-hook-installer: tools/tasktool/install.sh --hook
# superstar-hook-generated-at: 2026-05-21T14:23:07Z
```

The Python `tasktool` entrypoint adds a startup check:

1. `git rev-parse --show-toplevel` — if not in a git repo, skip silently.
2. `<repo>/.git/hooks/pre-commit` exists? If not, skip silently.
3. Read first 16 lines, look for `superstar-hook-name: tasktool-pre-commit`. If not present, skip silently — the file is some other hook the user maintains (including legacy tasktool hooks that only carry the older `tasktool-pre-commit-hook` magic comment; see §6a for the migration policy).
4. Extract `superstar-hook-version` and `superstar-hook-source-root`. The extracted source-root must be passed through the header parser (§6b) so literal `$HOME/` or `~/` prefixes are expanded before any filesystem operation.
5. Read `$source_root/VERSION` (expanded). If unreadable, skip silently.
6. Compare. If they differ, hard-exit before doing any tasktool work:

```
ERROR: tasktool pre-commit hook is 6.3.1 but Superstar source is 6.3.2
Hook: /home/simon/Dev/sigreer/multistore/.git/hooks/pre-commit
Re-run: bash /home/simon/Dev/sigreer/skills/superstar/tools/tasktool/install.sh --hook --force
```

The re-run path is reconstructed from the stamped `superstar-hook-source-root` so the user can copy-paste it directly. If the stamped source root no longer exists on disk, fall back to printing the relative installer path (`tools/tasktool/install.sh --hook --force`) and a one-line note that the source root must be located first.

The repo path naming in the message is deliberate — unlike the three global shims, this is repo-local state and the user needs to know which repo to act on.

Cost budget: a couple of `subprocess.run("git rev-parse", check=False)`, two `Path.exists()` calls, and a short `read_text().splitlines()[:16]`. Negligible compared to existing tasktool startup.

The check runs on **every** tasktool invocation (silent unless drift is real). Discovering stale hook state when the user is already thinking about tasktool beats discovering it later during a commit. If a future subcommand needs to operate explicitly outside a repo, the check is already a no-op there because step 1 short-circuits.

### 6a. Hook installer marker migration

The current `tools/tasktool/install.sh --hook` recognizes existing hooks by grepping for the magic comment `tasktool-pre-commit-hook` before allowing a non-force reinstall (`tools/tasktool/install.sh:17-23`). This work introduces a new stamped header that uses `superstar-hook-name: tasktool-pre-commit` instead. Without an explicit migration policy, the second install of a newly-stamped hook could be refused as "not a tasktool hook," or already-installed legacy hooks would need an unnecessary `--force`.

**Installer behaviour:** `install.sh --hook` accepts an existing hook as "ours" if **either** of these markers is present in the file:

- Legacy: `tasktool-pre-commit-hook` anywhere in the file.
- New: `superstar-hook-name: tasktool-pre-commit` in the header block.

The installer always writes the new header on (re)install; legacy magic-comment files are overwritten in place by a normal (non-`--force`) install once recognized. `--force` is reserved for hooks that match **neither** marker.

`tools/tasktool/tests/test_pre_commit_hook.py` is updated to:

- Add a case asserting that a legacy hook (file containing `tasktool-pre-commit-hook` only) is accepted by a non-force reinstall and is replaced with the new stamped header.
- Keep the existing idempotency case: two consecutive non-force installs of an already-stamped new-style hook succeed without `--force`.
- Add: a non-tasktool hook (no marker) still requires `--force` to overwrite.

### 6b. Header parser (shared spec)

Every consumer that reads a stamped value from a shim or hook header — `deploy.sh --check`, the Python tasktool startup check, and any future diagnostic — must use the same parser rules:

1. **Comment extraction.** Read up to the first 32 lines. Match lines of the form `# superstar-<scope>-<key>: <value>` (with `<scope>` ∈ `{shim, hook}`). Anything else is ignored.
2. **Path expansion.** Before any filesystem operation or copy-pastable diagnostic output that uses a stamped path value, the parser MUST:
   - Substitute a leading literal `$HOME/` with the current `$HOME`.
   - Substitute a leading literal `~/` with the current `$HOME`.
   - Leave all other content untouched.
   The bash shim runtime check works automatically because the stamped value is interpolated into a double-quoted bash string at install time, so `$HOME` is expanded naturally on dereference. The Python tasktool check, the `deploy.sh --check` shell logic, and any other consumer must call the equivalent expansion explicitly (`os.path.expandvars` then `os.path.expanduser` in Python; `eval echo` is **not** acceptable in bash — use parameter substitution `${value/#\$HOME/$HOME}` then `${value/#\~/$HOME}` to avoid command-injection surface).
3. **Missing or malformed stamps.** If a required key is absent or the value is empty after trimming, the consumer treats the file as **MALFORMED**, not as DRIFT. Diagnostics print a distinct row (e.g. `MALFORMED (missing superstar-shim-version)`); the bash shim runtime check treats a missing stamped version as "cannot compare" and execs normally per §4.
4. **Raw value retention.** When displaying paths for human eyes (e.g. the `--check` table), show the **expanded** absolute path so users can copy-paste it. The raw `$HOME/...` form is not surfaced in diagnostics; it exists only to keep the on-disk shim file portable across user accounts.

### 7. `bump-version.sh` changes

Purely a source-state tagger. No install side-effects. Specific changes:

- Add `read_plain_field` / `write_plain_field` helpers (see §1).
- Switch the `declared_files()` reader to emit `path<TAB>field<TAB>format`, where `format` is `json` (default) or `plain`.
- Dispatch on format in `cmd_check` and `cmd_bump`.
- Print VERSION as a normal row in `--check` output (not "VERSION (n/a)" or hidden under audit).
- Surface VERSION in `--audit` the same way as any other declared file.

`.version-bump.json` gets one new entry. No new flags, no new commands.

### 8. Publish vs deploy: source-root policy

**Plugin payload must carry `VERSION`.** Add `plugins/superstar/VERSION` as a relative symlink to `../../VERSION` (the repo-root file). `rsync -aL --delete` (the existing publish flag) flattens the symlink into a real file at `<cache>/<version>/VERSION` and `<cache>/current/VERSION`. `bump-version.sh` still writes only the repo-root file; the symlink reflects it. This makes `$SOURCE_ROOT/VERSION` readable for **any** shim source root — repo checkout, codex `current/`, or claude `current/` — eliminating the silent-skip class F2 flagged.

**External-reviewer shim continues to be re-stamped by the publish scripts** against the freshly-materialised `current/`, preserving X14's "external-reviewer survives dev-checkout moves" property. The other two global shims (`reviewer-agent`, `tasktool`) only get re-stamped by `deploy.sh` and always source-root at the dev checkout — they have no plugin-cache complication to solve.

Refactor — no removal of operational entry points:

- `scripts/lib/publish-common.sh` (new) — extract the shared logic currently duplicated between `publish-to-local-codex.sh` and `publish-to-local-claude.sh`:
  - VERSION resolution from manifest.
  - `rsync -aL --delete` of plugin source into `<cache>/<version>/` and `<cache>/current/`.
  - hooks.json command-path rewriting.
  - manifest verification — **extended to assert `<cache>/<version>/VERSION` and `<cache>/current/VERSION` exist and equal the manifest version.** Added to the existing payload verification block alongside `skills/...`, `hooks/...`, `tools/...`.
  - At the end: re-run `skills/external-review/install.sh` with `EXTERNAL_REVIEWER_SOURCE_ROOT=$CURRENT_DIR` (the just-materialised cache `current/`), matching today's behaviour at `scripts/publish-to-local-codex.sh:164-165` and `scripts/publish-to-local-claude.sh:188-189`.
- `scripts/publish-to-local-codex.sh` — kept as documented entry point. Thin wrapper around `publish-common.sh`. Restamps `external-reviewer` against codex `current/`. Does **not** touch `reviewer-agent` or `tasktool` shims.
- `scripts/publish-to-local-claude.sh` — same treatment, restamps against claude `current/`.
- `scripts/deploy.sh` (new) — top-level "do everything for this machine":

```
deploy.sh           Full: codex publish + claude publish + re-run all installers + print check
deploy.sh --check   Read-only diagnostics; non-zero exit on DRIFT
deploy.sh --codex-only    Skip Claude publish; still re-run all installers
deploy.sh --claude-only   Skip Codex publish; still re-run all installers
```

Deploy sequence (when not `--check`):

1. Call `publish-common.sh` for codex (unless `--claude-only`). This restamps `external-reviewer` against codex `current/` as a side effect.
2. Call `publish-common.sh` for claude (unless `--codex-only`). This restamps `external-reviewer` against claude `current/`.
3. `bash skills/project-setup/install-reviewer-agent.sh --force` against the dev checkout.
4. `bash tools/tasktool/install.sh --force` against the dev checkout.
5. If invoked inside a git repo: `bash tools/tasktool/install.sh --hook --force`.
6. Print the diagnostic summary (same output as `--check`).

`deploy.sh --check` always inspects both Codex and Claude cache `current/` trees regardless of `--codex-only` / `--claude-only`; those flags filter publish/restamp steps, not diagnostic visibility.

**Source-root policy table.** What source root each scenario stamps into installed shims:

| Trigger | external-reviewer | reviewer-agent | tasktool | pre-commit hook |
|---|---|---|---|---|
| `publish-to-local-codex.sh` (direct) | codex `current/` (re-stamped) | unchanged | unchanged | unchanged |
| `publish-to-local-claude.sh` (direct) | claude `current/` (re-stamped) | unchanged | unchanged | unchanged |
| `deploy.sh` (full, default order) | claude `current/` (final stamp wins) | dev checkout | dev checkout | dev checkout, if in repo |
| `deploy.sh --codex-only` | codex `current/` | dev checkout | dev checkout | dev checkout, if in repo |
| `deploy.sh --claude-only` | claude `current/` | dev checkout | dev checkout | dev checkout, if in repo |
| `EXTERNAL_REVIEWER_SOURCE_ROOT=…` env set on install | env value | (env var only affects external-reviewer installer) | unchanged | unchanged |

"Dev checkout" = the working tree containing `.version-bump.json` and the canonical `VERSION` file at its root. `EXTERNAL_REVIEWER_SOURCE_ROOT` is an escape hatch for the `external-reviewer` shim only (existing behaviour preserved); it does not influence the other shims.

Because `external-reviewer` may be stamped against a cache `current/` while `reviewer-agent` and `tasktool` are stamped against the dev checkout, `deploy.sh --check` may legitimately report different `source-root` values across the three rows even though all show OK. That asymmetry is intentional and not flagged as drift.

### 9. `deploy.sh --check` diagnostics output

Single table, machine-readable but readable-by-humans:

```
Source VERSION: 6.3.2 (/home/simon/Dev/sigreer/skills/superstar/VERSION)

Global shims:
  external-reviewer    /home/simon/.local/bin/external-reviewer
    stamped version:   6.3.2                                                       OK
    source root:       /home/simon/Dev/sigreer/skills/superstar                    EXISTS
    source root file:  skills/external-review/scripts/external-reviewer.py         EXISTS
    generated-at:      2026-05-21T14:23:07Z

  reviewer-agent       /home/simon/.local/bin/reviewer-agent
    stamped version:   6.3.1                                                       DRIFT (source is 6.3.2)
    source root:       /home/simon/Dev/sigreer/skills/superstar                    EXISTS
    source root file:  skills/project-setup/scripts/reviewer-agent                 EXISTS
    generated-at:      2026-04-30T09:11:02Z

  tasktool             /home/simon/.local/bin/tasktool
    stamped version:   6.3.2                                                       OK
    ...

Plugin caches:
  codex     ~/.codex/plugins/cache/superstar-dev/superstar/current     VERSION: 6.3.2     OK
  claude    ~/.claude/plugins/cache/superstar-dev/superstar/current    VERSION: 6.3.2     OK

Pre-commit hook (current repo):
  /home/simon/Dev/sigreer/skills/superstar/.git/hooks/pre-commit
    stamped version:   6.3.2                                                       OK
    source root:       /home/simon/Dev/sigreer/skills/superstar                    EXISTS

3 of 4 installed files in sync. 1 drift.
```

**Status lattice and exit behaviour.** `deploy.sh --check` classifies each inspected row into one of these statuses and exits non-zero if any row is in a failing state:

| Row status | Meaning | Exit-impact |
|---|---|---|
| `OK` | Stamped version matches `$SOURCE_ROOT/VERSION`; all required stamp keys present; source-root path exists. | None. |
| `DRIFT` | Stamped version differs from `$SOURCE_ROOT/VERSION`. | **Fails** (exit non-zero). |
| `MALFORMED` | Required stamp key missing/empty, or header unparseable per §6b. | **Fails.** |
| `MISSING_TARGET` | The installed shim/hook file does not exist where deploy expects it (e.g. `~/.local/bin/reviewer-agent` absent after a `deploy.sh` that should have created it). | **Fails.** |
| `MISSING_SOURCE` | The stamped `source-root` path does not exist on disk (e.g. cache `current/` never materialised, dev checkout moved). | **Fails.** |
| `MISSING_CACHE_VERSION` | A plugin cache row has no readable `current/VERSION` (publish skipped or symlink not flattened). | **Fails.** |
| `SOURCE_ROOT_INFO` | Same stamped version across shims but different `source-root` values. Expected by design — `external-reviewer` may point at a cache `current/` while the others point at the dev checkout. | None. Surfaced for diagnostic clarity only. |

Each fail-class status flips the exit code to non-zero; `OK` and `SOURCE_ROOT_INFO` alone leave it at zero. `--check` prints all rows even when one or more fail so the operator sees the full picture in one pass. The failure summary at the bottom of the table is human-readable (e.g. `5 of 6 rows OK; 1 DRIFT, 0 MALFORMED`) and the exit code communicates pass/fail to scripts.

## Testing

New test file `scripts/tests/test_shim_stamping.sh` (bash + simple assertions; or pytest under `scripts/tests/test_shim_stamping.py` if matching existing conventions in `skills/external-review/tests/`):

1. **Happy path.** Build a fake `SOURCE_ROOT` with `VERSION=1.0.0` and a stub source script. Run each installer. Assert generated shim contains the expected stamp keys with correct values. Invoke the shim — it execs the source.
2. **Drift refusal.** Bump fake `VERSION` to `1.0.1` *without* re-running the installer. Invoke the shim. Assert exit code 1, stderr contains "shim is 1.0.0 but Superstar source is 1.0.1", and the source script was **not** executed (verify via a sentinel file the source writes if reached).
3. **Re-install fixes drift.** Re-run the installer against the fake source. Assert the new shim's stamp is `1.0.1` and the shim execs again.
4. **Missing VERSION → no refusal.** Delete the fake `VERSION`. Invoke shim. Assert it execs normally (no spurious error).
5. **Missing source root → no spurious version warning.** `rm -rf` the fake source root. Invoke shim. Assert it fails with the underlying path-resolution error (e.g. `python3: can't open file …`), not with a version-mismatch error.
6. **Same version, different source root.** Generate the shim against `/tmp/source-a/` at 1.0.0, then publish a fresh deploy that stamps a new shim pointing at `/tmp/source-b/` also at 1.0.0. Assert `deploy.sh --check` reports a source-root drift in the summary but exits 0 (informational).
7. **Pre-commit hook drift.** Install the hook against fake source 1.0.0. Bump source VERSION to 1.0.1 in place. Run any tasktool subcommand. Assert exit code 1, stderr contains the hook path and the re-run instruction, and the underlying subcommand did **not** execute.
8. **Pre-commit hook absent.** No hook installed. Run tasktool. Assert no spurious error.
9. **Pre-commit hook is some other hook (no `superstar-hook-name` marker).** Run tasktool. Assert no spurious error; tasktool proceeds.
10. **`bump-version.sh --check` includes VERSION.** Assert VERSION appears as its own row in the output and participates in the in-sync detection.
11. **`$HOME` literalisation round-trip.** Generate a shim whose stamped `source-root` is `$HOME/...`. Invoke the shim — assert it execs (bash expansion path). Then run `deploy.sh --check` — assert the displayed path is the expanded absolute form, not the literal `$HOME/...` string.
12. **Python hook handshake expands `$HOME`.** Stamp a hook with a `$HOME/...` source-root. Run tasktool — assert it reads `<expanded>/VERSION` and either succeeds or fails with the expanded path in the error message.
13. **Malformed stamp.** Hand-edit a shim to remove the `superstar-shim-version` line. Run the shim — assert it execs (cannot compare). Run `deploy.sh --check` — assert a `MALFORMED` row appears, distinct from `DRIFT`, **and `--check` exits non-zero**. Repeat for `MISSING_TARGET` (delete the shim file) and `MISSING_SOURCE` (rename the stamped source-root directory) — both must exit non-zero. Assert `SOURCE_ROOT_INFO` rows alone do **not** flip the exit code.
14. **Legacy hook accepted on reinstall.** Pre-place a hook file containing only the legacy `tasktool-pre-commit-hook` magic comment. Run `tools/tasktool/install.sh --hook` (no `--force`). Assert the install succeeds and the resulting file carries the new `superstar-hook-name: tasktool-pre-commit` header. Run it again. Assert idempotent success without `--force`.
15. **Non-tasktool hook still requires `--force`.** Pre-place a hook file that contains neither marker. Run `tools/tasktool/install.sh --hook` without `--force`. Assert refusal with the existing error.
16. **Plugin payload carries VERSION.** Run `publish-to-local-codex.sh` (and again for claude). Assert `<cache>/<version>/VERSION` and `<cache>/current/VERSION` exist, are real files (not symlinks after rsync), and equal the manifest version. Assert `publish-common.sh`'s manifest verification fails if VERSION is missing or mismatched.
17. **Direct publish restamps external-reviewer.** Run `publish-to-local-codex.sh`. Assert `~/.local/bin/external-reviewer` is regenerated and its `superstar-shim-source-root` points at the codex `current/`. Repeat for claude. Both must continue to work — this is the X14 regression guard.
18. **Direct publish does NOT touch reviewer-agent or tasktool shims.** Capture the pre-publish content of both shims. Run a direct publish. Assert both shim files are byte-identical to their pre-publish state.

Existing `skills/external-review/tests/test_external_reviewer_installer.py` updated:
- Assert the generated shim contains the new stamp header keys.
- Assert the embedded `__superstar_check_version` function is present.

Existing `tests/codex-plugin-sync/test-publish-to-local-codex.sh` and `tests/claude-code/test-publish-to-local-claude.sh` updated:
- Assert `current/VERSION` is materialised as a real file with the right contents.
- Keep the assertion that the generated shim points at `current/skills/external-review/scripts/external-reviewer.py`.

`skills/external-review/tests/test_external_reviewer_compat_shim.py` — deleted.

## Risks and mitigations

- **`bump-version.sh` errors on `VERSION` missing.** Mitigation: when `--check` runs against an old checkout that predates this work (no VERSION file, no entry in `.version-bump.json`), the existing `MISSING` row handles it gracefully. No code change needed beyond the new `format: plain` dispatch.
- **`scripts/lib/shim-version-check.sh` evolves and shims silently embed an old version of the check fragment.** Mitigation: this is exactly what the version check is for — the fragment lives inside the shim, but the shim's `version` stamp is bumped any time the fragment changes (since the fragment lives in the source tree and is touched by version-bumped releases). A bumped VERSION forces a `deploy.sh` which re-stamps every shim.
- **Existing per-repo `~/.local/bin/reviewer-agent` was hand-edited by the user.** Mitigation: `install-reviewer-agent.sh` refuses to overwrite without `--force` if the existing file lacks the `superstar-shim` marker (mirroring how `external-reviewer/install.sh` and `tasktool/install.sh` behave today). The user is told to inspect, then re-run with `--force`. `deploy.sh` always passes `--force`, so a deploy after this work lands wipes the old copy intentionally.
- **Tasktool startup cost.** Mitigation: the hook check skips inside <1ms when the hook is absent or unmarked (which is the common case — only repos that opted into the hook see the full check). The full check is still cheap: two filesystem stats and a short read. Below tasktool's existing JSON-load cost.
- **Out-of-tree shims (other users, other projects).** Mitigation: not in scope. The shim header convention is unique to Superstar (`superstar-shim` magic comment) and won't collide with other tooling. Other projects' shims under `~/.local/bin/` are untouched by `deploy.sh --check` because the scan keys on the `superstar-shim` magic line.

## Acceptance criteria

1. `VERSION` exists at repo root as a single-line plain-text file. `plugins/superstar/VERSION` exists as a relative symlink to `../../VERSION` so the publish flow materialises a real `VERSION` file in both Codex and Claude plugin caches.
2. `.version-bump.json` declares `VERSION` with `"format": "plain"`. `bump-version.sh --check` shows it in the table; `--audit` includes it; `bump-version.sh X.Y.Z` writes it.
3. All three global shims under `~/.local/bin/` carry the five stamp keys after `deploy.sh`. Their stamped `version` values are identical (= current `VERSION`). Their stamped `source-root` values may differ by design: `external-reviewer` may point at a plugin-cache `current/`, while `reviewer-agent` and `tasktool` point at the dev checkout.
4. Running a global shim while `$SOURCE_ROOT/VERSION` and the stamped version differ causes the shim to hard-exit with the documented error and **not** invoke the source. Tested. Works for both dev-checkout-stamped and cache-`current/`-stamped shims because the plugin payload now carries `VERSION`.
5. Running tasktool inside a repo whose `.git/hooks/pre-commit` carries the `superstar-hook-name: tasktool-pre-commit` marker with a mismatched version causes tasktool to hard-exit with the hook path and the reconstructed `bash <source-root>/tools/tasktool/install.sh --hook --force` instruction in the message, with `<source-root>` expanded from any literal `$HOME/` or `~/` prefix. Tested.
6. `scripts/publish-to-local-codex.sh` and `scripts/publish-to-local-claude.sh` still exist as entry points, share their implementation via `scripts/lib/publish-common.sh`, and continue to re-stamp the `external-reviewer` shim against the just-materialised `current/`. Other global shims and the pre-commit hook are not touched by direct publish.
7. `scripts/deploy.sh --check` parses shim/hook headers using the §6b parser rules, surfaces expanded absolute paths in the table, applies the §9 status lattice, and exits non-zero on any `DRIFT`, `MALFORMED`, `MISSING_TARGET`, `MISSING_SOURCE`, or `MISSING_CACHE_VERSION` row (and zero when only `OK` and `SOURCE_ROOT_INFO` rows appear).
8. `tools/tasktool/install.sh --hook` accepts a legacy hook carrying only `tasktool-pre-commit-hook` and replaces it with the new stamped header without `--force`. Hooks with neither marker still require `--force`. Idempotent reinstall of an already-new-stamped hook succeeds.
9. `skills/project-setup/scripts/external-reviewer-shim.py`, the corresponding test, and the project-setup row 7b that recommends it are removed.
10. The full Superstar test suite passes, including the new shim-stamping tests and the updated publish-script regression tests.
