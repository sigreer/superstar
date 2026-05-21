# Shim Version Stamping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stamp every Superstar-installed shim and hook with a version header, refuse to run when the source's `VERSION` file has drifted, and surface drift through a one-shot `scripts/deploy.sh --check` diagnostic. Eliminate the stale-shim class of bugs.

**Architecture:** A new top-level `VERSION` file is the single source of truth, read at runtime by every shim. Each installer embeds a shared bash version-check fragment plus a stamped header. The Python `tasktool` entrypoint adds a startup handshake for the repo-local `pre-commit` hook (the one file that must be a content copy). `scripts/deploy.sh` ties publish + re-installation together and provides a `--check` diagnostic mode with a strict exit-status lattice. The `reviewer-agent` global file is converted from content copy to redirect shim, eliminating its content-drift class entirely.

**Tech Stack:** bash (installers, shim runtime, deploy.sh, publish scripts), Python 3 (tasktool entrypoint + new test cases), pytest (test harness), `jq` (already a project dependency for JSON manipulation in bump-version.sh).

**Work ID:** X16 (cross-cutting). No slice schedule — single linear delivery.

---

## File Structure

**New files:**
- `VERSION` (repo root) — single-line plain text, e.g. `6.3.2\n`. Single source of truth at runtime.
- `plugins/superstar/VERSION` — relative symlink to `../../VERSION`. Flattens to a real file under `<cache>/<version>/VERSION` and `<cache>/current/VERSION` via `rsync -aL`.
- `scripts/lib/shim-version-check.sh` — shared bash fragment defining `__superstar_check_version`, embedded into every generated shim by the installers.
- `scripts/lib/publish-common.sh` — shared publish logic (rsync, hooks.json rewriting, manifest + VERSION verification) sourced by both `publish-to-local-codex.sh` and `publish-to-local-claude.sh`.
- `scripts/deploy.sh` — top-level deploy + diagnostics entry point.
- `skills/project-setup/install-reviewer-agent.sh` — new installer that emits a thin redirect shim for `~/.local/bin/reviewer-agent`.
- `scripts/tests/__init__.py` and `scripts/tests/test_shim_stamping.py` — pytest module for cross-cutting shim/stamping tests.

**Modified files:**
- `.version-bump.json` — add `{path: "VERSION", format: "plain"}` and migrate the existing entries to the new format-aware shape.
- `scripts/bump-version.sh` — add `read_plain_field` / `write_plain_field` helpers and a `format` column dispatch in `declared_files()`.
- `skills/external-review/install.sh` — embed stamp header + shim-version-check fragment into the generated shim.
- `skills/external-review/tests/test_external_reviewer_installer.py` — assert stamp keys + fragment present.
- `scripts/publish-to-local-codex.sh` — convert to thin wrapper over `publish-common.sh`. Preserve the existing post-publish `external-reviewer/install.sh` re-run.
- `scripts/publish-to-local-claude.sh` — same treatment.
- `tools/tasktool/install.sh` — add stamp header + version-check fragment to the generated `~/.local/bin/tasktool` shim. Hook installer accepts legacy + new markers.
- `tools/tasktool/templates/pre-commit-tasktool` — header gains stamped key/value lines while preserving the legacy `tasktool-pre-commit-hook v1` magic comment for backward recognition.
- `tools/tasktool/cli.py` — add startup pre-commit-hook version handshake.
- `tools/tasktool/tests/test_pre_commit_hook.py` — add cases for legacy-marker migration, header stamping, idempotency.
- `skills/project-setup/SKILL.md` — delete row 7b and surrounding compat-shim language.
- `tests/codex-plugin-sync/test-publish-to-local-codex.sh` — assert `current/VERSION` materialised; keep shim source-path assertion.
- `tests/claude-code/test-publish-to-local-claude.sh` — same.

**Deleted files:**
- `skills/project-setup/scripts/external-reviewer-shim.py`
- `skills/external-review/tests/test_external_reviewer_compat_shim.py`

---

## Task 1: VERSION file + bump-version plain format support

**Files:**
- Create: `VERSION` at repo root
- Create: `plugins/superstar/VERSION` (symlink)
- Modify: `.version-bump.json`
- Modify: `scripts/bump-version.sh`

- [ ] **Step 1.1: Capture current version from declared files**

Read the current version (the value that bump-version.sh would consider canonical):

```bash
jq -r '.version' package.json
```

Expected: `6.3.2` (or whatever the current `package.json` version is — note it; subsequent steps reference it as `$CURRENT_VERSION`).

- [ ] **Step 1.2: Create the repo-root `VERSION` file**

```bash
echo "6.3.2" > VERSION
cat VERSION
```

Expected: single line `6.3.2` with trailing newline. Adjust `6.3.2` to match `$CURRENT_VERSION` from Step 1.1.

- [ ] **Step 1.3: Add the plugin-payload `VERSION` symlink**

```bash
ln -s ../../VERSION plugins/superstar/VERSION
ls -la plugins/superstar/VERSION
cat plugins/superstar/VERSION
```

Expected: `lrwxrwxrwx ... plugins/superstar/VERSION -> ../../VERSION` and the contents match `6.3.2`. Symlink is **relative** so it stays valid inside the published cache trees after `rsync -aL` flattens it.

- [ ] **Step 1.4: Write the failing bump-version plain-format test (new test file)**

Create `scripts/tests/__init__.py` (empty) and `scripts/tests/test_bump_version_plain_format.py`:

```python
"""Tests for the plain-format support added to scripts/bump-version.sh."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_SCRIPT = REPO_ROOT / "scripts" / "bump-version.sh"


def _seed_repo(tmp_path: Path, version: str) -> Path:
    """Build an isolated fake repo so the script's own REPO_ROOT resolution
    (`cd $SCRIPT_DIR/.. && pwd`) lands inside tmp_path and cannot mutate the
    real checkout."""
    (tmp_path / "package.json").write_text(json.dumps({"version": version}, indent=2) + "\n")
    (tmp_path / "VERSION").write_text(version + "\n")
    config = {
        "files": [
            {"path": "package.json", "field": "version"},
            {"path": "VERSION", "format": "plain"},
        ],
        "audit": {"exclude": []},
    }
    (tmp_path / ".version-bump.json").write_text(json.dumps(config, indent=2) + "\n")
    (tmp_path / "scripts").mkdir(exist_ok=True)
    # Symlink the real bump-version.sh into the fake repo's scripts dir. We
    # MUST invoke this symlinked path (not REAL_SCRIPT) so the script's
    # `dirname "$0"` -> `cd $SCRIPT_DIR/..` resolves to tmp_path. Invoking
    # REAL_SCRIPT directly would resolve to the real superstar checkout and
    # mutate its declared files.
    fake_script = tmp_path / "scripts" / "bump-version.sh"
    fake_script.symlink_to(REAL_SCRIPT)
    return tmp_path


def _run(script_args: list[str], repo: Path) -> subprocess.CompletedProcess:
    """Invoke the symlinked bump-version.sh inside `repo` so REPO_ROOT
    resolution stays inside the fake repo."""
    fake_script = repo / "scripts" / "bump-version.sh"
    assert fake_script.exists(), "fake script symlink missing — call _seed_repo first"
    return subprocess.run(
        ["bash", str(fake_script), *script_args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def test_check_lists_plain_version(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path, "1.2.3")
    result = _run(["--check"], repo)
    assert result.returncode == 0, result.stderr
    assert "VERSION" in result.stdout
    assert "1.2.3" in result.stdout


def test_bump_writes_plain_version(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path, "1.2.3")
    result = _run(["1.2.4"], repo)
    assert result.returncode == 0, result.stderr
    assert (repo / "VERSION").read_text().strip() == "1.2.4"
    assert json.loads((repo / "package.json").read_text())["version"] == "1.2.4"


def test_check_detects_drift_between_plain_and_json(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path, "1.2.3")
    (repo / "VERSION").write_text("1.2.4\n")
    result = _run(["--check"], repo)
    assert result.returncode != 0
    assert "DRIFT" in result.stdout
```

- [ ] **Step 1.5: Run the test to confirm it fails (script doesn't know `format: plain` yet)**

```bash
python3 -m pytest scripts/tests/test_bump_version_plain_format.py -v
```

Expected: at least one test fails — `bump-version.sh` does not yet read the `format` field and will silently skip the VERSION file (since `read_json_field` returns null) or error on `jq` trying to read `.version` from a non-JSON file.

- [ ] **Step 1.6: Update `.version-bump.json` to declare VERSION first and add the format key**

Replace the file at repo root with:

```json
{
  "files": [
    { "path": "VERSION", "format": "plain" },
    { "path": "package.json", "field": "version" },
    { "path": ".claude-plugin/plugin.json", "field": "version" },
    { "path": ".cursor-plugin/plugin.json", "field": "version" },
    { "path": ".codex-plugin/plugin.json", "field": "version" },
    { "path": ".claude-plugin/marketplace.json", "field": "plugins.0.version" },
    { "path": ".agents/plugins/marketplace.json", "field": "plugins.0.version" },
    { "path": "plugins/superstar/.codex-plugin/plugin.json", "field": "version" },
    { "path": "gemini-extension.json", "field": "version" }
  ],
  "audit": {
    "exclude": [
      "CHANGELOG.md",
      "RELEASE-NOTES.md",
      "node_modules",
      ".git",
      ".version-bump.json",
      "scripts/bump-version.sh"
    ]
  }
}
```

The JSON entries continue to carry `field`; the new VERSION entry carries `format` instead. `bump-version.sh` treats absence of `format` as the default (`"json"`).

- [ ] **Step 1.7: Add plain-format helpers to `scripts/bump-version.sh`**

Edit `scripts/bump-version.sh`. Add these two helpers immediately below `write_json_field` (~ line 38):

```bash
# Read a plain single-line VERSION-style file.
read_plain_field() {
  local file="$1"
  head -n1 "$file" | tr -d '[:space:]'
}

# Write a plain single-line VERSION-style file (single trailing newline).
write_plain_field() {
  local file="$1" value="$2"
  printf '%s\n' "$value" > "$file"
}
```

- [ ] **Step 1.8: Update `declared_files()` to emit a `format` column**

Replace the existing `declared_files()` function with:

```bash
# Read declared files from config.
# Outputs lines of "path<TAB>field<TAB>format" where format defaults to "json".
declared_files() {
  jq -r '.files[] | "\(.path)\t\(.field // "")\t\(.format // "json")"' "$CONFIG"
}
```

- [ ] **Step 1.9: Dispatch on format in `cmd_check`**

Find the loop in `cmd_check` that reads each declared file and replace its inner body to dispatch:

```bash
  while IFS=$'\t' read -r path field format; do
    local fullpath="$REPO_ROOT/$path"
    if [[ ! -f "$fullpath" ]]; then
      printf "  %-45s  MISSING\n" "$path"
      has_drift=1
      continue
    fi
    local ver label
    if [[ "$format" == "plain" ]]; then
      ver=$(read_plain_field "$fullpath")
      label="$path (plain)"
    else
      ver=$(read_json_field "$fullpath" "$field")
      label="$path ($field)"
    fi
    printf "  %-45s  %s\n" "$label" "$ver"
    versions+=("$ver")
  done < <(declared_files)
```

- [ ] **Step 1.10: Dispatch on format in `cmd_bump` and `cmd_audit`**

Apply the same `format` dispatch inside the `while` loops in `cmd_bump` (writing) and inside the version-determination loop of `cmd_audit` (reading). The audit "most common version" computation should consume the same path/field/format tuple.

For `cmd_bump`'s inner write block:

```bash
  while IFS=$'\t' read -r path field format; do
    local fullpath="$REPO_ROOT/$path"
    if [[ ! -f "$fullpath" ]]; then
      echo "  SKIP (missing): $path"
      continue
    fi
    local old_ver label
    if [[ "$format" == "plain" ]]; then
      old_ver=$(read_plain_field "$fullpath")
      write_plain_field "$fullpath" "$new_version"
      label="$path (plain)"
    else
      old_ver=$(read_json_field "$fullpath" "$field")
      write_json_field "$fullpath" "$field" "$new_version"
      label="$path ($field)"
    fi
    printf "  %-45s  %s -> %s\n" "$label" "$old_ver" "$new_version"
  done < <(declared_files)
```

For `cmd_audit`'s version-detection block (the subshell that emits versions to `sort | uniq -c`):

```bash
    while IFS=$'\t' read -r path field format; do
      local fullpath="$REPO_ROOT/$path"
      if [[ ! -f "$fullpath" ]]; then continue; fi
      if [[ "$format" == "plain" ]]; then
        read_plain_field "$fullpath"
      else
        read_json_field "$fullpath" "$field"
      fi
    done < <(declared_files) | sort | uniq -c | sort -rn | head -1 | awk '{print $2}'
```

- [ ] **Step 1.11: Run the new tests to verify they pass**

```bash
python3 -m pytest scripts/tests/test_bump_version_plain_format.py -v
```

Expected: all three tests pass.

- [ ] **Step 1.12: Run `--check` against the real repo to confirm no regressions**

```bash
bash scripts/bump-version.sh --check
```

Expected: VERSION listed as a row with `(plain)` annotation; all declared files show the same version; "All declared files are in sync at ..." line at the bottom; exit 0.

- [ ] **Step 1.13: Run `--audit` to confirm no regressions**

```bash
bash scripts/bump-version.sh --audit
```

Expected: standard audit output; no Python tracebacks; either "No undeclared files contain the version string. All clear." or a list of already-known undeclared files (unchanged from before).

- [ ] **Step 1.14: Commit**

```bash
git add VERSION plugins/superstar/VERSION .version-bump.json scripts/bump-version.sh \
        scripts/tests/__init__.py scripts/tests/test_bump_version_plain_format.py
git commit -m "X16.T1: add VERSION file + plain-format support in bump-version"
```

---

## Task 2: Shared shim-version-check fragment

**Files:**
- Create: `scripts/lib/shim-version-check.sh`
- Create: `scripts/tests/test_shim_version_check_fragment.py`

- [ ] **Step 2.1: Write the failing fragment test**

Create `scripts/tests/test_shim_version_check_fragment.py`:

```python
"""Direct tests for scripts/lib/shim-version-check.sh."""
from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FRAGMENT = REPO_ROOT / "scripts" / "lib" / "shim-version-check.sh"


def _run_fragment(tmp_path: Path, shim_version: str, source_version: str | None) -> subprocess.CompletedProcess:
    """Source the fragment in a synthetic harness; call the function; return result."""
    source_root = tmp_path / "fake-source"
    source_root.mkdir()
    if source_version is not None:
        (source_root / "VERSION").write_text(source_version + "\n")
    script = textwrap.dedent(f"""
        #!/usr/bin/env bash
        source "{FRAGMENT}"
        __superstar_check_version "{shim_version}" "test-shim" "{source_root}" "skills/test/install.sh"
        echo "REACHED_END"
    """)
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=False)


def test_versions_match_exec_continues(tmp_path: Path) -> None:
    result = _run_fragment(tmp_path, "1.0.0", "1.0.0")
    assert result.returncode == 0
    assert "REACHED_END" in result.stdout


def test_version_drift_hard_exits(tmp_path: Path) -> None:
    result = _run_fragment(tmp_path, "1.0.0", "1.0.1")
    assert result.returncode == 1
    assert "REACHED_END" not in result.stdout
    assert "test-shim shim is 1.0.0 but Superstar source is 1.0.1" in result.stderr
    assert "skills/test/install.sh" in result.stderr


def test_missing_version_file_exec_continues(tmp_path: Path) -> None:
    """No VERSION file at the source root must NOT block exec."""
    result = _run_fragment(tmp_path, "1.0.0", None)
    assert result.returncode == 0
    assert "REACHED_END" in result.stdout


def test_empty_shim_version_exec_continues(tmp_path: Path) -> None:
    result = _run_fragment(tmp_path, "", "1.0.0")
    assert result.returncode == 0
    assert "REACHED_END" in result.stdout
```

- [ ] **Step 2.2: Run test to verify it fails (fragment doesn't exist yet)**

```bash
python3 -m pytest scripts/tests/test_shim_version_check_fragment.py -v
```

Expected: errors with `bash: scripts/lib/shim-version-check.sh: No such file or directory` (or `source` failure).

- [ ] **Step 2.3: Create the fragment**

Create `scripts/lib/shim-version-check.sh`:

```bash
# scripts/lib/shim-version-check.sh
#
# Embedded by Superstar shim installers (skills/external-review/install.sh,
# skills/project-setup/install-reviewer-agent.sh, tools/tasktool/install.sh).
# Provides __superstar_check_version, which hard-exits the calling shim if
# the stamped shim version differs from $SOURCE_ROOT/VERSION.
#
# Strict failure ONLY when BOTH sides are readable AND they differ. Missing or
# unreadable VERSION, or an empty stamped value, means "cannot compare" and
# the shim continues to exec normally.
#
# Args:
#   $1  shim_version       e.g. "6.3.2"
#   $2  shim_name          e.g. "external-reviewer"
#   $3  source_root        absolute or $HOME/... path
#   $4  installer          relative path under source_root, e.g.
#                          "skills/external-review/install.sh"

__superstar_check_version() {
    local shim_version="$1"
    local shim_name="$2"
    local source_root="$3"
    local installer="$4"

    [[ -n "$shim_version" ]] || return 0
    local version_file="$source_root/VERSION"
    [[ -r "$version_file" ]] || return 0

    local src_version
    src_version="$(head -n1 "$version_file" 2>/dev/null | tr -d '[:space:]')"
    [[ -n "$src_version" ]] || return 0

    if [[ "$src_version" != "$shim_version" ]]; then
        printf 'ERROR: %s shim is %s but Superstar source is %s\n' \
            "$shim_name" "$shim_version" "$src_version" >&2
        printf 'Re-run: bash %s/%s\n' "$source_root" "$installer" >&2
        exit 1
    fi
}
```

- [ ] **Step 2.4: Run tests to verify they pass**

```bash
python3 -m pytest scripts/tests/test_shim_version_check_fragment.py -v
```

Expected: all four tests pass.

- [ ] **Step 2.5: Commit**

```bash
git add scripts/lib/shim-version-check.sh scripts/tests/test_shim_version_check_fragment.py
git commit -m "X16.T2: add shared shim-version-check fragment"
```

---

## Task 3: External-reviewer installer — embed stamp and check

**Files:**
- Modify: `skills/external-review/install.sh`
- Modify: `skills/external-review/tests/test_external_reviewer_installer.py`

- [ ] **Step 3.1: Update the existing installer test to expect the new stamp**

Edit `skills/external-review/tests/test_external_reviewer_installer.py`. Below the existing assertion that the generated shim contains `"external-reviewer shim"`, add three new test functions:

```python
def test_generated_shim_carries_stamp_header(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    source_root = _seed_fake_source(tmp_path / "src", version="1.0.0")
    _run_installer(source_root=source_root, bin_dir=bin_dir)
    text = (bin_dir / "external-reviewer").read_text(encoding="utf-8")
    assert "# superstar-shim" in text
    assert "superstar-shim-name: external-reviewer" in text
    assert "superstar-shim-version: 1.0.0" in text
    assert "superstar-shim-source-root:" in text
    assert "superstar-shim-installer: skills/external-review/install.sh" in text
    assert "superstar-shim-generated-at:" in text


def test_generated_shim_embeds_version_check_fragment(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    source_root = _seed_fake_source(tmp_path / "src", version="1.0.0")
    _run_installer(source_root=source_root, bin_dir=bin_dir)
    text = (bin_dir / "external-reviewer").read_text(encoding="utf-8")
    assert "__superstar_check_version()" in text
    assert '__superstar_check_version "1.0.0"' in text


def test_generated_shim_refuses_when_source_version_drifts(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    source_root = _seed_fake_source(tmp_path / "src", version="1.0.0")
    _run_installer(source_root=source_root, bin_dir=bin_dir)
    # Bump VERSION at the source root without re-running the installer.
    (source_root / "VERSION").write_text("1.0.1\n")
    result = subprocess.run(
        [str(bin_dir / "external-reviewer"), "--help"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert "external-reviewer shim is 1.0.0 but Superstar source is 1.0.1" in result.stderr
```

You'll need helpers `_seed_fake_source(path, version)` (creates a fake `SOURCE_ROOT` with `skills/external-review/scripts/external-reviewer.py` stub that prints "STUB INVOKED" and a `VERSION` file) and `_run_installer(source_root, bin_dir)` (runs the installer with the right env vars). Add them at the top of the file if not present:

```python
def _seed_fake_source(path: Path, version: str) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "VERSION").write_text(version + "\n")
    script_dir = path / "skills" / "external-review" / "scripts"
    script_dir.mkdir(parents=True)
    stub = script_dir / "external-reviewer.py"
    stub.write_text("#!/usr/bin/env python3\nimport sys\nprint('STUB INVOKED')\nsys.exit(0)\n")
    stub.chmod(0o755)
    # Required by install.sh (it sources scripts/lib/shim-version-check.sh).
    lib_dir = path / "scripts" / "lib"
    lib_dir.mkdir(parents=True)
    real_fragment = REPO_ROOT / "scripts" / "lib" / "shim-version-check.sh"
    (lib_dir / "shim-version-check.sh").write_text(real_fragment.read_text())
    # Also copy the installer itself so the SCRIPT_DIR/PLUGIN_ROOT resolution works.
    installer_dir = path / "skills" / "external-review"
    real_installer = REPO_ROOT / "skills" / "external-review" / "install.sh"
    (installer_dir / "install.sh").write_text(real_installer.read_text())
    (installer_dir / "install.sh").chmod(0o755)
    return path


def _run_installer(*, source_root: Path, bin_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(source_root / "skills" / "external-review" / "install.sh")],
        env={
            "EXTERNAL_REVIEWER_SOURCE_ROOT": str(source_root),
            "EXTERNAL_REVIEWER_BIN": str(bin_dir),
            "HOME": str(bin_dir.parent),
            "PATH": os.environ["PATH"],
        },
        capture_output=True, text=True, check=True,
    )
```

(Adjust `REPO_ROOT` import to use the existing path constant in this file. Add `import os, subprocess` if not already imported.)

- [ ] **Step 3.2: Run the new tests to verify they fail**

```bash
python3 -m pytest skills/external-review/tests/test_external_reviewer_installer.py -v
```

Expected: the three new tests fail; the generated shim does not yet carry the stamp or the embedded fragment.

- [ ] **Step 3.3: Modify the installer to stamp and embed**

Edit `skills/external-review/install.sh`. Replace the `cat > "$TARGET" <<EOF` block at the end with:

```bash
FRAGMENT="$SOURCE_ROOT/scripts/lib/shim-version-check.sh"
if [[ ! -r "$FRAGMENT" ]]; then
  echo "ERROR: shim-version-check fragment missing: $FRAGMENT" >&2
  exit 1
fi
SRC_VERSION="$(head -n1 "$SOURCE_ROOT/VERSION" | tr -d '[:space:]')"
if [[ -z "$SRC_VERSION" ]]; then
  echo "ERROR: $SOURCE_ROOT/VERSION is missing or empty" >&2
  exit 1
fi
GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [[ "$SOURCE_SCRIPT" == "$HOME/"* ]]; then
  SOURCE_EXPR="\$HOME/${SOURCE_SCRIPT#"$HOME/"}"
  STAMP_SOURCE_ROOT="\$HOME/${SOURCE_ROOT#"$HOME/"}"
else
  SOURCE_EXPR="$SOURCE_SCRIPT"
  STAMP_SOURCE_ROOT="$SOURCE_ROOT"
fi

{
  cat <<EOF
#!/usr/bin/env bash
# external-reviewer shim - generated by Superstar skills/external-review/install.sh
# superstar-shim
# superstar-shim-name: external-reviewer
# superstar-shim-version: $SRC_VERSION
# superstar-shim-source-root: $STAMP_SOURCE_ROOT
# superstar-shim-installer: skills/external-review/install.sh
# superstar-shim-generated-at: $GENERATED_AT

EOF
  cat "$FRAGMENT"
  cat <<EOF

__superstar_check_version \\
    "$SRC_VERSION" \\
    "external-reviewer" \\
    "$STAMP_SOURCE_ROOT" \\
    "skills/external-review/install.sh"

exec python3 "$SOURCE_EXPR" "\$@"
EOF
} > "$TARGET"

chmod +x "$TARGET"
```

- [ ] **Step 3.4: Run tests to verify they pass**

```bash
python3 -m pytest skills/external-review/tests/test_external_reviewer_installer.py -v
```

Expected: all tests pass, including the existing ones (the stamped shim must still execute the source script when versions match).

- [ ] **Step 3.5: Smoke-test against the real repo**

```bash
bash skills/external-review/install.sh
~/.local/bin/external-reviewer --help | head -5
grep "superstar-shim-version" ~/.local/bin/external-reviewer
```

Expected: `--help` exits 0 and prints the external-reviewer help text. Grep returns one line with the current `VERSION` value.

- [ ] **Step 3.6: Commit**

```bash
git add skills/external-review/install.sh skills/external-review/tests/test_external_reviewer_installer.py
git commit -m "X16.T3: stamp external-reviewer shim with version header + drift check"
```

---

## Task 4: New reviewer-agent installer (redirect shim)

**Files:**
- Create: `skills/project-setup/install-reviewer-agent.sh`
- Create: `scripts/tests/test_install_reviewer_agent.py`

- [ ] **Step 4.1: Write the failing installer test**

Create `scripts/tests/test_install_reviewer_agent.py`:

```python
"""Tests for skills/project-setup/install-reviewer-agent.sh."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER = REPO_ROOT / "skills" / "project-setup" / "install-reviewer-agent.sh"
FRAGMENT = REPO_ROOT / "scripts" / "lib" / "shim-version-check.sh"


def _seed_source(path: Path, version: str) -> Path:
    path.mkdir(parents=True)
    (path / "VERSION").write_text(version + "\n")
    script_dir = path / "skills" / "project-setup" / "scripts"
    script_dir.mkdir(parents=True)
    real = REPO_ROOT / "skills" / "project-setup" / "scripts" / "reviewer-agent"
    (script_dir / "reviewer-agent").write_text(real.read_text())
    (script_dir / "reviewer-agent").chmod(0o755)
    lib_dir = path / "scripts" / "lib"
    lib_dir.mkdir(parents=True)
    (lib_dir / "shim-version-check.sh").write_text(FRAGMENT.read_text())
    return path


def _run(source_root: Path, bin_dir: Path, *, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    env = {
        "EXTERNAL_REVIEWER_SOURCE_ROOT": str(source_root),
        "EXTERNAL_REVIEWER_BIN": str(bin_dir),
        "HOME": str(bin_dir.parent),
        "PATH": os.environ["PATH"],
    }
    return subprocess.run(
        ["bash", str(INSTALLER), *(extra_args or [])],
        env=env, capture_output=True, text=True, check=False,
    )


def test_install_writes_redirect_shim(tmp_path: Path) -> None:
    source = _seed_source(tmp_path / "src", "1.0.0")
    bin_dir = tmp_path / "bin"
    result = _run(source, bin_dir)
    assert result.returncode == 0, result.stderr
    target = bin_dir / "reviewer-agent"
    assert target.exists()
    text = target.read_text()
    assert "superstar-shim-name: reviewer-agent" in text
    assert "superstar-shim-version: 1.0.0" in text
    assert "skills/project-setup/scripts/reviewer-agent" in text
    assert os.access(target, os.X_OK)


def test_install_passes_bash_n_syntax_check(tmp_path: Path) -> None:
    source = _seed_source(tmp_path / "src", "1.0.0")
    bin_dir = tmp_path / "bin"
    _run(source, bin_dir)
    target = bin_dir / "reviewer-agent"
    # Self-test the installer runs is `bash -n` of the generated shim.
    result = subprocess.run(["bash", "-n", str(target)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_install_refuses_to_overwrite_unstamped_file(tmp_path: Path) -> None:
    source = _seed_source(tmp_path / "src", "1.0.0")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "reviewer-agent").write_text("#!/usr/bin/env bash\necho hand-edited\n")
    (bin_dir / "reviewer-agent").chmod(0o755)
    result = _run(source, bin_dir)
    assert result.returncode != 0
    assert "not a reviewer-agent shim" in result.stderr or "not a superstar-shim" in result.stderr


def test_install_overwrites_unstamped_file_with_force(tmp_path: Path) -> None:
    source = _seed_source(tmp_path / "src", "1.0.0")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "reviewer-agent").write_text("#!/usr/bin/env bash\necho hand-edited\n")
    (bin_dir / "reviewer-agent").chmod(0o755)
    result = _run(source, bin_dir, extra_args=["--force"])
    assert result.returncode == 0, result.stderr
    assert "superstar-shim-name: reviewer-agent" in (bin_dir / "reviewer-agent").read_text()


def test_generated_shim_refuses_on_version_drift(tmp_path: Path) -> None:
    source = _seed_source(tmp_path / "src", "1.0.0")
    bin_dir = tmp_path / "bin"
    _run(source, bin_dir)
    (source / "VERSION").write_text("1.0.1\n")
    result = subprocess.run(
        [str(bin_dir / "reviewer-agent")],
        env={"PATH": os.environ["PATH"]},
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert "reviewer-agent shim is 1.0.0 but Superstar source is 1.0.1" in result.stderr
```

- [ ] **Step 4.2: Run tests to verify they fail (installer doesn't exist yet)**

```bash
python3 -m pytest scripts/tests/test_install_reviewer_agent.py -v
```

Expected: errors with `No such file or directory: skills/project-setup/install-reviewer-agent.sh`.

- [ ] **Step 4.3: Create the installer**

Create `skills/project-setup/install-reviewer-agent.sh`:

```bash
#!/usr/bin/env bash
# skills/project-setup/install-reviewer-agent.sh
# Generate a thin redirect shim at $EXTERNAL_REVIEWER_BIN/reviewer-agent that
# execs the bash source at $SOURCE_ROOT/skills/project-setup/scripts/reviewer-agent.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SOURCE_ROOT="${EXTERNAL_REVIEWER_SOURCE_ROOT:-}"
if [[ -z "$SOURCE_ROOT" ]]; then
  SOURCE_ROOT="$PLUGIN_ROOT"
  # When invoked from a versioned plugin cache, prefer the stable `current/`
  # entrypoint so the stamped shim survives cache version bumps. Mirrors
  # skills/external-review/install.sh.
  case "$PLUGIN_ROOT" in
    */plugins/cache/*/*/*)
      STABLE_ROOT="$(dirname "$PLUGIN_ROOT")/current"
      if [[ -f "$STABLE_ROOT/skills/project-setup/scripts/reviewer-agent" ]]; then
        SOURCE_ROOT="$STABLE_ROOT"
      fi
      ;;
  esac
fi
SOURCE_SCRIPT="$SOURCE_ROOT/skills/project-setup/scripts/reviewer-agent"
TARGET_DIR="${EXTERNAL_REVIEWER_BIN:-${HOME}/.local/bin}"
TARGET="$TARGET_DIR/reviewer-agent"
FORCE="${1:-}"

if [[ ! -x "$SOURCE_SCRIPT" ]]; then
  echo "ERROR: source wrapper not found or not executable: $SOURCE_SCRIPT" >&2
  exit 1
fi

FRAGMENT="$SOURCE_ROOT/scripts/lib/shim-version-check.sh"
if [[ ! -r "$FRAGMENT" ]]; then
  echo "ERROR: shim-version-check fragment missing: $FRAGMENT" >&2
  exit 1
fi
SRC_VERSION="$(head -n1 "$SOURCE_ROOT/VERSION" | tr -d '[:space:]')"
if [[ -z "$SRC_VERSION" ]]; then
  echo "ERROR: $SOURCE_ROOT/VERSION is missing or empty" >&2
  exit 1
fi
GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

mkdir -p "$TARGET_DIR"

if [[ -f "$TARGET" && "$FORCE" != "--force" ]]; then
  if ! grep -q "superstar-shim-name: reviewer-agent" "$TARGET" 2>/dev/null; then
    echo "ERROR: $TARGET exists and is not a reviewer-agent shim. Re-run with --force to overwrite." >&2
    exit 1
  fi
fi

if [[ "$SOURCE_SCRIPT" == "$HOME/"* ]]; then
  SOURCE_EXPR="\$HOME/${SOURCE_SCRIPT#"$HOME/"}"
  STAMP_SOURCE_ROOT="\$HOME/${SOURCE_ROOT#"$HOME/"}"
else
  SOURCE_EXPR="$SOURCE_SCRIPT"
  STAMP_SOURCE_ROOT="$SOURCE_ROOT"
fi

{
  cat <<EOF
#!/usr/bin/env bash
# reviewer-agent shim - generated by Superstar skills/project-setup/install-reviewer-agent.sh
# superstar-shim
# superstar-shim-name: reviewer-agent
# superstar-shim-version: $SRC_VERSION
# superstar-shim-source-root: $STAMP_SOURCE_ROOT
# superstar-shim-installer: skills/project-setup/install-reviewer-agent.sh
# superstar-shim-generated-at: $GENERATED_AT

EOF
  cat "$FRAGMENT"
  cat <<EOF

__superstar_check_version \\
    "$SRC_VERSION" \\
    "reviewer-agent" \\
    "$STAMP_SOURCE_ROOT" \\
    "skills/project-setup/install-reviewer-agent.sh"

exec bash "$SOURCE_EXPR" "\$@"
EOF
} > "$TARGET"

chmod +x "$TARGET"

# Self-test: syntax-check the generated shim. We cannot run the shim because
# reviewer-agent itself bails on missing AGENT_REVIEWER_* env vars.
bash -n "$TARGET"

echo "Installed $TARGET"
echo "Pointing at $SOURCE_SCRIPT"
echo "Self-test passed (bash -n)."
```

- [ ] **Step 4.4: Make the installer executable**

```bash
chmod +x skills/project-setup/install-reviewer-agent.sh
```

- [ ] **Step 4.5: Run tests to verify they pass**

```bash
python3 -m pytest scripts/tests/test_install_reviewer_agent.py -v
```

Expected: all five tests pass.

- [ ] **Step 4.6: Real-repo smoke test**

```bash
bash skills/project-setup/install-reviewer-agent.sh --force
head -10 ~/.local/bin/reviewer-agent
```

Expected: header shows `superstar-shim-name: reviewer-agent` and the current `VERSION`. The previous hand-installed copy (full content) is replaced by the redirect shim — `--force` was needed only because the prior file lacks the marker. Subsequent re-installs without `--force` will work.

- [ ] **Step 4.7: Commit**

```bash
git add skills/project-setup/install-reviewer-agent.sh scripts/tests/test_install_reviewer_agent.py
git commit -m "X16.T4: convert reviewer-agent to redirect shim with version stamp"
```

---

## Task 5: Tasktool shim — embed stamp and check

**Files:**
- Modify: `tools/tasktool/install.sh`
- Modify: `tools/tasktool/tests/test_pre_commit_hook.py` (the existing tests will reference the new install structure but the shim test is new — add a new test file)
- Create: `tools/tasktool/tests/test_tasktool_shim_install.py`

- [ ] **Step 5.1: Write the failing tasktool-shim test**

Create `tools/tasktool/tests/test_tasktool_shim_install.py`:

```python
"""Tests for tools/tasktool/install.sh (shim install path, not the hook path)."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
INSTALLER = REPO_ROOT / "tools" / "tasktool" / "install.sh"
FRAGMENT = REPO_ROOT / "scripts" / "lib" / "shim-version-check.sh"


def _seed_source(path: Path, version: str) -> Path:
    path.mkdir(parents=True)
    (path / "VERSION").write_text(version + "\n")
    tools = path / "tools" / "tasktool"
    tools.mkdir(parents=True)
    (tools / "__init__.py").write_text("")
    (tools / "__main__.py").write_text("print('STUB INVOKED')\n")
    install_target = tools / "install.sh"
    install_target.write_text((REPO_ROOT / "tools" / "tasktool" / "install.sh").read_text())
    install_target.chmod(0o755)
    lib_dir = path / "scripts" / "lib"
    lib_dir.mkdir(parents=True)
    (lib_dir / "shim-version-check.sh").write_text(FRAGMENT.read_text())
    return path


def _run(source: Path, home: Path) -> subprocess.CompletedProcess:
    env = {
        "HOME": str(home),
        "PATH": os.environ["PATH"],
    }
    return subprocess.run(
        ["bash", str(source / "tools" / "tasktool" / "install.sh")],
        env=env, capture_output=True, text=True, check=False,
    )


def test_install_writes_stamped_shim(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".local" / "bin").mkdir(parents=True)
    source = _seed_source(tmp_path / "src", "1.0.0")
    result = _run(source, home)
    assert result.returncode == 0, result.stderr
    target = home / ".local" / "bin" / "tasktool"
    text = target.read_text()
    assert "superstar-shim-name: tasktool" in text
    assert "superstar-shim-version: 1.0.0" in text


def test_shim_refuses_on_drift(tmp_path: Path) -> None:
    home = tmp_path / "home"
    (home / ".local" / "bin").mkdir(parents=True)
    source = _seed_source(tmp_path / "src", "1.0.0")
    _run(source, home)
    (source / "VERSION").write_text("1.0.1\n")
    result = subprocess.run(
        [str(home / ".local" / "bin" / "tasktool")],
        env={"PATH": os.environ["PATH"]},
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert "tasktool shim is 1.0.0 but Superstar source is 1.0.1" in result.stderr
```

- [ ] **Step 5.2: Run test to verify it fails**

```bash
python3 -m pytest tools/tasktool/tests/test_tasktool_shim_install.py -v
```

Expected: failure — current installer doesn't stamp the shim.

- [ ] **Step 5.3: Modify the tasktool installer to stamp and embed**

Edit `tools/tasktool/install.sh`. Replace the final `cat > "$TARGET" <<EOF` block with the stamped version. Keep the `--hook` mode at the top of the file unchanged (Task 6 modifies that).

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"   # → tools/
SOURCE_ROOT="$(cd "$PKG_ROOT/.." && pwd)"  # → repo root
TARGET="${HOME}/.local/bin/tasktool"
FORCE="${1:-}"

FRAGMENT="$SOURCE_ROOT/scripts/lib/shim-version-check.sh"
if [[ ! -r "$FRAGMENT" ]]; then
  echo "ERROR: shim-version-check fragment missing: $FRAGMENT" >&2
  exit 1
fi
SRC_VERSION="$(head -n1 "$SOURCE_ROOT/VERSION" | tr -d '[:space:]')"
if [[ -z "$SRC_VERSION" ]]; then
  echo "ERROR: $SOURCE_ROOT/VERSION is missing or empty" >&2
  exit 1
fi
GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [[ "$PKG_ROOT" == "$HOME/"* ]]; then
  STAMP_SOURCE_ROOT="\$HOME/${SOURCE_ROOT#"$HOME/"}"
  PKG_EXPR="\$HOME/${PKG_ROOT#"$HOME/"}"
else
  STAMP_SOURCE_ROOT="$SOURCE_ROOT"
  PKG_EXPR="$PKG_ROOT"
fi

mkdir -p "$(dirname "$TARGET")"

if [[ -f "$TARGET" ]] && [[ "$FORCE" != "--force" ]]; then
  current="$(cat "$TARGET")"
  if grep -q "tasktool shim" "$TARGET" 2>/dev/null || grep -q "superstar-shim-name: tasktool" "$TARGET" 2>/dev/null; then
    : # ours; rewrite below
  else
    echo "ERROR: $TARGET exists and is not a tasktool shim. Re-run with --force to overwrite." >&2
    exit 1
  fi
fi

{
  cat <<EOF
#!/usr/bin/env bash
# tasktool shim — generated by tasktool/install.sh
# superstar-shim
# superstar-shim-name: tasktool
# superstar-shim-version: $SRC_VERSION
# superstar-shim-source-root: $STAMP_SOURCE_ROOT
# superstar-shim-installer: tools/tasktool/install.sh
# superstar-shim-generated-at: $GENERATED_AT

EOF
  cat "$FRAGMENT"
  cat <<EOF

__superstar_check_version \\
    "$SRC_VERSION" \\
    "tasktool" \\
    "$STAMP_SOURCE_ROOT" \\
    "tools/tasktool/install.sh"

export PYTHONPATH="$PKG_EXPR\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 -m tasktool "\$@"
EOF
} > "$TARGET"

chmod +x "$TARGET"

echo "Installed $TARGET"
echo "Pointing at $PKG_ROOT/tasktool"
"$TARGET" --help >/dev/null
echo "Self-test passed."
```

Note: this preserves the existing `--hook` path at the top of the file (lines 5-29 in the current file). Do not modify that block in this task.

- [ ] **Step 5.4: Run shim tests**

```bash
python3 -m pytest tools/tasktool/tests/test_tasktool_shim_install.py -v
```

Expected: both new tests pass.

- [ ] **Step 5.5: Real-repo smoke test**

```bash
bash tools/tasktool/install.sh
tasktool --help | head -3
grep "superstar-shim-version" ~/.local/bin/tasktool
```

Expected: tasktool works; the shim's stamp matches `cat VERSION`.

- [ ] **Step 5.6: Commit**

```bash
git add tools/tasktool/install.sh tools/tasktool/tests/test_tasktool_shim_install.py
git commit -m "X16.T5: stamp tasktool shim with version header + drift check"
```

---

## Task 6: Pre-commit hook stamping + legacy marker migration

**Files:**
- Modify: `tools/tasktool/templates/pre-commit-tasktool`
- Modify: `tools/tasktool/install.sh` (the `--hook` block at the top)
- Modify: `tools/tasktool/tests/test_pre_commit_hook.py`

- [ ] **Step 6.1: Write the failing migration tests**

The existing `tools/tasktool/tests/test_pre_commit_hook.py` uses module-level constants `REPO`, `INSTALL`, `PKG_DIR` (see lines 5–8) and the `_seed_repo(tmp_path)` helper that returns `(repo, env)` (line 20). Tests follow the `test_NAME(tmp_path)` signature. **The installer reads `VERSION` from the real Superstar source root (`REPO`), not the consumer repo** — so the tests must assert against the real source's current version, not a fabricated one.

Add a helper at the top of the file (next to `_tasktool`):

```python
def _read_source_version() -> str:
    """Return the Superstar source VERSION (single line)."""
    return (REPO / "VERSION").read_text().splitlines()[0].strip()


def _install_hook_only(repo: Path, *, force: bool = False, check: bool = True) -> subprocess.CompletedProcess:
    """Direct install.sh --hook invocation without going through _seed_repo,
    used for tests that pre-place a hook file."""
    args = ["bash", str(INSTALL), "--hook"]
    if force:
        args.append("--force")
    result = subprocess.run(args, cwd=repo, capture_output=True, text=True, check=False)
    if check:
        assert result.returncode == 0, result.stdout + result.stderr
    return result
```

Then add these new tests at the end of the file:

```python
def test_hook_install_writes_stamped_header(tmp_path):
    repo, _env = _seed_repo(tmp_path)  # _seed_repo already ran install.sh --hook
    hook = repo / ".git" / "hooks" / "pre-commit"
    text = hook.read_text()
    src_version = _read_source_version()
    assert "superstar-hook-name: tasktool-pre-commit" in text
    assert f"superstar-hook-version: {src_version}" in text
    assert "superstar-hook-source-root:" in text
    assert "superstar-hook-installer: tools/tasktool/install.sh --hook" in text
    assert "superstar-hook-generated-at:" in text
    # Legacy magic comment is preserved for back-compat with consumers that grep it.
    assert "tasktool-pre-commit-hook" in text


def test_hook_install_accepts_legacy_marker_without_force(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    # Pre-place a legacy-style hook (magic comment only, no superstar-hook header).
    hook.write_text("#!/usr/bin/env sh\n# tasktool-pre-commit-hook v1\nexit 0\n")
    hook.chmod(0o755)
    # Reinstall without --force should succeed and upgrade the header.
    result = _install_hook_only(repo, force=False)
    assert result.returncode == 0
    text = hook.read_text()
    assert "superstar-hook-name: tasktool-pre-commit" in text
    src_version = _read_source_version()
    assert f"superstar-hook-version: {src_version}" in text


def test_hook_install_refuses_non_tasktool_hook_without_force(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/usr/bin/env sh\n# someone-elses-hook\nexit 0\n")
    hook.chmod(0o755)
    result = _install_hook_only(repo, force=False, check=False)
    assert result.returncode != 0
    assert "not a tasktool hook" in result.stderr
```

The existing `test_hook_install_is_idempotent` (currently around line 131 in the file) must continue to pass — it does two consecutive `--hook` installs and asserts both succeed without `--force`. After Task 6's installer changes, the second invocation should still see the new `superstar-hook-name` marker and accept itself as "ours".

- [ ] **Step 6.2: Run tests to verify they fail**

```bash
python3 -m pytest tools/tasktool/tests/test_pre_commit_hook.py -v
```

Expected: the three new tests fail. Existing tests may also fail if they assert old marker behavior verbatim.

- [ ] **Step 6.3: Update the hook template to carry stamp placeholders**

Edit `tools/tasktool/templates/pre-commit-tasktool`. Replace the top of the file (everything before `set -e`) with:

```sh
#!/usr/bin/env sh
# tasktool-pre-commit-hook v1
# superstar-hook
# superstar-hook-name: tasktool-pre-commit
# superstar-hook-version: __SUPERSTAR_HOOK_VERSION__
# superstar-hook-source-root: __SUPERSTAR_HOOK_SOURCE_ROOT__
# superstar-hook-installer: tools/tasktool/install.sh --hook
# superstar-hook-generated-at: __SUPERSTAR_HOOK_GENERATED_AT__
#
# Installed by `tools/tasktool/install.sh --hook`.
# Validates the STAGED content (the index), not the working tree, so a clean
# worktree with stale staged bytes cannot sneak past.
#
# Enforces:
#   1. docs/TASKLIST.md must not be staged (project migrated to docs/tasklist.json).
#   2. Staged docs/tasklist.json must be canonical (tasktool validate --strict-format).
#   3. Staged docs/tasklist.json must pass full validation.
#   4. Staged spec/plan filenames must reference an ID present in the staged tasklist.json.
# Bypass for genuine emergencies: `git commit --no-verify` and document the reason.
```

The `__SUPERSTAR_*__` placeholders are replaced at install time. The legacy `tasktool-pre-commit-hook v1` line is preserved so consumers that grep for it (and any in-the-wild docs) keep working.

- [ ] **Step 6.4: Rewrite the `--hook` block in `tools/tasktool/install.sh` to accept both markers and stamp**

Replace the existing `--hook` block (currently lines 5–29) with:

```bash
# --- hook installer (must precede shim-install logic) ---------------------
if [[ "${1:-}" == "--hook" ]]; then
  shift
  FORCE_HOOK=0
  if [[ "${1:-}" == "--force" ]]; then FORCE_HOOK=1; shift; fi
  REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [[ -z "$REPO_ROOT" ]]; then
    echo "install.sh --hook: must be run inside a git working tree" >&2
    exit 1
  fi
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  SOURCE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"   # → superstar repo root
  HOOK_SRC="$SCRIPT_DIR/templates/pre-commit-tasktool"
  HOOK_DEST="$REPO_ROOT/.git/hooks/pre-commit"
  if [[ -f "$HOOK_DEST" && "$FORCE_HOOK" -ne 1 ]]; then
    if grep -q 'tasktool-pre-commit-hook' "$HOOK_DEST" 2>/dev/null \
       || grep -q 'superstar-hook-name: tasktool-pre-commit' "$HOOK_DEST" 2>/dev/null; then
      : # ours; rewrite below
    else
      echo "install.sh --hook: $HOOK_DEST exists and is not a tasktool hook. Re-run with --force to overwrite." >&2
      exit 1
    fi
  fi
  SRC_VERSION="$(head -n1 "$SOURCE_ROOT/VERSION" | tr -d '[:space:]')"
  if [[ -z "$SRC_VERSION" ]]; then
    echo "install.sh --hook: $SOURCE_ROOT/VERSION is missing or empty" >&2
    exit 1
  fi
  GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if [[ "$SOURCE_ROOT" == "$HOME/"* ]]; then
    STAMP_SOURCE_ROOT="\$HOME/${SOURCE_ROOT#"$HOME/"}"
  else
    STAMP_SOURCE_ROOT="$SOURCE_ROOT"
  fi
  TMP="$(mktemp)"
  sed \
    -e "s|__SUPERSTAR_HOOK_VERSION__|$SRC_VERSION|" \
    -e "s|__SUPERSTAR_HOOK_SOURCE_ROOT__|${STAMP_SOURCE_ROOT//|/\\|}|" \
    -e "s|__SUPERSTAR_HOOK_GENERATED_AT__|$GENERATED_AT|" \
    "$HOOK_SRC" > "$TMP"
  install -m 0755 "$TMP" "$HOOK_DEST"
  rm -f "$TMP"
  echo "Installed $HOOK_DEST"
  exit 0
fi
# --------------------------------------------------------------------------
```

- [ ] **Step 6.5: Run hook tests**

```bash
python3 -m pytest tools/tasktool/tests/test_pre_commit_hook.py -v
```

Expected: all tests pass — new tests and the existing idempotency test.

- [ ] **Step 6.6: Real-repo smoke test**

```bash
bash tools/tasktool/install.sh --hook --force
head -10 .git/hooks/pre-commit
```

Expected: hook file contains both `tasktool-pre-commit-hook v1` and the new stamped header.

- [ ] **Step 6.7: Commit**

```bash
git add tools/tasktool/install.sh tools/tasktool/templates/pre-commit-tasktool tools/tasktool/tests/test_pre_commit_hook.py
git commit -m "X16.T6: stamp pre-commit hook with version header + accept legacy marker"
```

---

## Task 7: Tasktool startup hook handshake

**Files:**
- Create: `tools/tasktool/hook_handshake.py`
- Modify: `tools/tasktool/cli.py`
- Create: `tools/tasktool/tests/test_hook_handshake.py`

- [ ] **Step 7.1: Write the failing handshake tests**

Create `tools/tasktool/tests/test_hook_handshake.py`:

```python
"""Tests for tools/tasktool/hook_handshake.py."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tasktool import hook_handshake

REPO_ROOT = Path(__file__).resolve().parents[3]


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)


def _write_hook(repo: Path, *, version: str, source_root: str) -> Path:
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text(
        "#!/usr/bin/env sh\n"
        "# tasktool-pre-commit-hook v1\n"
        "# superstar-hook\n"
        "# superstar-hook-name: tasktool-pre-commit\n"
        f"# superstar-hook-version: {version}\n"
        f"# superstar-hook-source-root: {source_root}\n"
        "# superstar-hook-installer: tools/tasktool/install.sh --hook\n"
        "# superstar-hook-generated-at: 2026-05-21T00:00:00Z\n"
        "exit 0\n"
    )
    hook.chmod(0o755)
    return hook


def test_no_git_repo_silent(tmp_path: Path) -> None:
    # cwd is not a git repo
    assert hook_handshake.check_pre_commit_hook(cwd=tmp_path) is None


def test_no_hook_silent(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    assert hook_handshake.check_pre_commit_hook(cwd=tmp_path) is None


def test_non_tasktool_hook_silent(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/usr/bin/env sh\n# someone-elses-hook\nexit 0\n")
    hook.chmod(0o755)
    assert hook_handshake.check_pre_commit_hook(cwd=tmp_path) is None


def test_matching_version_silent(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    _write_hook(tmp_path, version="1.0.0", source_root=str(source))
    assert hook_handshake.check_pre_commit_hook(cwd=tmp_path) is None


def test_drift_returns_error(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "VERSION").write_text("1.0.1\n")
    hook = _write_hook(tmp_path, version="1.0.0", source_root=str(source))
    msg = hook_handshake.check_pre_commit_hook(cwd=tmp_path)
    assert msg is not None
    assert "tasktool pre-commit hook is 1.0.0 but Superstar source is 1.0.1" in msg
    assert str(hook) in msg
    assert str(source / "tools" / "tasktool" / "install.sh") in msg


def test_home_expansion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """$HOME/ in the stamped source-root must be expanded before reading VERSION."""
    _init_git_repo(tmp_path)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    source = fake_home / "src"
    source.mkdir()
    (source / "VERSION").write_text("1.0.1\n")
    _write_hook(tmp_path, version="1.0.0", source_root="$HOME/src")
    msg = hook_handshake.check_pre_commit_hook(cwd=tmp_path)
    assert msg is not None
    # Expanded path appears in the message, not the literal $HOME/...
    assert str(source) in msg


def test_missing_source_version_silent(tmp_path: Path) -> None:
    """If stamped source-root has no VERSION (moved/deleted), do not block."""
    _init_git_repo(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    # No VERSION file.
    _write_hook(tmp_path, version="1.0.0", source_root=str(source))
    assert hook_handshake.check_pre_commit_hook(cwd=tmp_path) is None
```

- [ ] **Step 7.2: Run tests to verify they fail**

```bash
python3 -m pytest tools/tasktool/tests/test_hook_handshake.py -v
```

Expected: `ModuleNotFoundError: No module named 'tasktool.hook_handshake'`.

- [ ] **Step 7.3: Create `tools/tasktool/hook_handshake.py`**

```python
"""Startup handshake for the tasktool ↔ pre-commit hook version stamp.

Returns an error message string if the installed hook is stale relative to the
Superstar source declared in its stamped header. Returns None for all other
states (no repo, no hook, non-tasktool hook, missing source VERSION).

Cheap: a couple of subprocess.run + Path.exists + a short read_text. Called
unconditionally from cli.main; silent on the happy path.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Optional

_HEADER_KEYS = (
    "superstar-hook-name",
    "superstar-hook-version",
    "superstar-hook-source-root",
)
_HEADER_RE = re.compile(r"^#\s*([a-z][a-z0-9-]*):\s*(.+?)\s*$")


def _git_top(cwd: Path) -> Optional[Path]:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def _parse_header(text: str) -> dict[str, str]:
    """Parse the leading shim/hook stamp header. Reads up to 32 lines."""
    out: dict[str, str] = {}
    for line in text.splitlines()[:32]:
        m = _HEADER_RE.match(line)
        if not m:
            continue
        out[m.group(1)] = m.group(2)
    return out


def _expand_path(value: str) -> str:
    """§6b parser rule: expand leading $HOME/ and ~/ before any filesystem op."""
    return os.path.expanduser(os.path.expandvars(value))


def check_pre_commit_hook(cwd: Optional[Path] = None) -> Optional[str]:
    """Return a stderr-ready error message string on drift, else None."""
    cwd = cwd or Path.cwd()
    repo_top = _git_top(cwd)
    if repo_top is None:
        return None
    hook_path = repo_top / ".git" / "hooks" / "pre-commit"
    if not hook_path.exists():
        return None
    try:
        header = _parse_header(hook_path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return None
    if header.get("superstar-hook-name") != "tasktool-pre-commit":
        return None
    hook_version = header.get("superstar-hook-version", "").strip()
    source_root_raw = header.get("superstar-hook-source-root", "").strip()
    if not hook_version or not source_root_raw:
        return None
    source_root = Path(_expand_path(source_root_raw))
    version_file = source_root / "VERSION"
    try:
        src_version = version_file.read_text(encoding="utf-8").splitlines()[0].strip()
    except (OSError, IndexError):
        return None
    if not src_version or src_version == hook_version:
        return None
    return (
        f"ERROR: tasktool pre-commit hook is {hook_version} but Superstar source is {src_version}\n"
        f"Hook: {hook_path}\n"
        f"Re-run: bash {source_root}/tools/tasktool/install.sh --hook --force"
    )
```

- [ ] **Step 7.4: Run handshake tests to verify they pass**

```bash
python3 -m pytest tools/tasktool/tests/test_hook_handshake.py -v
```

Expected: all seven tests pass.

- [ ] **Step 7.5: Wire the handshake into `tasktool/cli.py:main`**

Open `tools/tasktool/cli.py`. Add an import near the top of the file (next to the existing `from tasktool import commands`):

```python
from tasktool import hook_handshake
```

Then modify `main()` to call the check **before** `parser.parse_args(argv)`. This matters because argparse's `--help` action raises `SystemExit` during `parse_args`, which would bypass any check placed after. Drift must block every tasktool invocation — including `--help` — until the operator re-runs the installer.

Find this block (~ line 211):

```python
def main(argv: list[str]) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    root = _resolve_project_root(args)
```

Replace with:

```python
def main(argv: list[str]) -> int:
    hook_drift_msg = hook_handshake.check_pre_commit_hook()
    if hook_drift_msg is not None:
        print(hook_drift_msg, file=sys.stderr)
        return 1
    parser = _build_parser()
    args = parser.parse_args(argv)
    root = _resolve_project_root(args)
```

- [ ] **Step 7.6: Add an integration test that invokes `tasktool` end-to-end**

Append to `tools/tasktool/tests/test_hook_handshake.py`:

```python
def test_tasktool_main_exits_on_hook_drift(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "VERSION").write_text("1.0.1\n")
    _write_hook(tmp_path, version="1.0.0", source_root=str(source))
    result = subprocess.run(
        ["python3", "-m", "tasktool", "--help"],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "tools")},
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert "tasktool pre-commit hook is 1.0.0 but Superstar source is 1.0.1" in result.stderr


def test_tasktool_main_runs_normally_when_hook_ok(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    source = tmp_path / "src"
    source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    _write_hook(tmp_path, version="1.0.0", source_root=str(source))
    result = subprocess.run(
        ["python3", "-m", "tasktool", "--help"],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "tools")},
        capture_output=True, text=True, check=False,
    )
    # --help is handled by argparse and exits 0.
    assert result.returncode == 0
```

Add `import os` at the top if not already present.

- [ ] **Step 7.7: Run all tasktool tests**

```bash
python3 -m pytest tools/tasktool/tests/ -v
```

Expected: every test passes. The handshake check runs on `--help` and is silent in the happy case.

- [ ] **Step 7.8: Commit**

```bash
git add tools/tasktool/hook_handshake.py tools/tasktool/cli.py tools/tasktool/tests/test_hook_handshake.py
git commit -m "X16.T7: tasktool startup handshake refuses on stale pre-commit hook"
```

---

## Task 8: publish-common.sh + VERSION payload verification

**Files:**
- Create: `scripts/lib/publish-common.sh`
- Modify: `scripts/publish-to-local-codex.sh`
- Modify: `scripts/publish-to-local-claude.sh`
- Modify: `tests/codex-plugin-sync/test-publish-to-local-codex.sh`
- Modify: `tests/claude-code/test-publish-to-local-claude.sh`

- [ ] **Step 8.1: Update existing publish regression tests to expect `current/VERSION`**

Edit `tests/codex-plugin-sync/test-publish-to-local-codex.sh`. Find the block that verifies cache contents and add a `VERSION` assertion. The exact lines depend on the current file shape; the new assertion should be something like:

```bash
test -f "$CACHE_ROOT/$VERSION/VERSION" || { echo "FAIL: cache <version>/VERSION missing"; exit 1; }
test -f "$CACHE_ROOT/current/VERSION" || { echo "FAIL: cache current/VERSION missing"; exit 1; }
diff <(cat "$REPO_ROOT/VERSION") "$CACHE_ROOT/current/VERSION" \
  || { echo "FAIL: cache current/VERSION differs from repo-root VERSION"; exit 1; }
```

Repeat for `tests/claude-code/test-publish-to-local-claude.sh`.

Keep the existing assertion that the generated shim points at `current/skills/external-review/scripts/external-reviewer.py`. That's the X14 regression guard.

- [ ] **Step 8.2: Run the updated publish tests to confirm they fail**

```bash
bash tests/codex-plugin-sync/test-publish-to-local-codex.sh
```

Expected: failure at the new `VERSION` assertion (publish doesn't materialize VERSION into the cache yet, although the `plugins/superstar/VERSION` symlink already exists in the working tree). Actually — the symlink was added in Task 1, so `rsync -aL` already flattens it. The test should pass at the new VERSION assertion since the symlink is already in place. Verify this; if it passes already, move on. If not, debug the rsync flag.

```bash
bash tests/claude-code/test-publish-to-local-claude.sh
```

Same expectation.

- [ ] **Step 8.3: Extract `publish-common.sh`**

The Codex and Claude publishers differ in three concrete ways that the shared library must parameterize:

1. **Source layout.** Codex rsyncs `plugins/superstar/` (a subdirectory); Claude rsyncs `$REPO_ROOT/` (the whole repo, with excludes). The caller passes the source root.
2. **Manifest subpath.** Codex uses `.codex-plugin/plugin.json`; Claude uses `.claude-plugin/plugin.json`. Passed as an arg.
3. **Required payload list.** Identical except Claude requires `skills/external-review/scripts/external-reviewer.py` to exist in the cache (because the cache *is* the repo for Claude). Passed as a colon-separated list.
4. **Hook command rewriting.** Both publishers rewrite the same two `${CLAUDE_PLUGIN_ROOT...}/hooks/run-hook.cmd` patterns. Identical logic.
5. **VERSION file.** Codex needs the `plugins/superstar/VERSION` symlink (added in T1) so `rsync -aL` materializes a real file at `<cache>/VERSION`. Claude rsyncs the repo root so VERSION is already there. Both code paths reach the same end state: `<cache>/VERSION` and `<cache>/current/VERSION` are real files matching `$REPO_ROOT/VERSION`.

Create `scripts/lib/publish-common.sh`:

```bash
# scripts/lib/publish-common.sh — shared logic for publish-to-local-* scripts.
# All functions return non-zero on error; callers can `set -e`.

set -euo pipefail

# Resolve a "version" field from a JSON manifest.
ss_publish_resolve_version() {
  local manifest="$1"
  python3 - "$manifest" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    print(json.load(f)["version"])
PY
}

# rsync a payload into both <cache>/<version>/ and <cache>/current/. The caller
# supplies any --exclude args via the EXTRA_RSYNC_ARGS env var (space-sep).
ss_publish_rsync_payload() {
  local source="$1" dest="$2"
  mkdir -p "$dest"
  # shellcheck disable=SC2086
  rsync -aL --delete ${EXTRA_RSYNC_ARGS:-} "$source/" "$dest/"
}

# Verify <cache>/VERSION and <cache>/current/VERSION are materialized real files
# matching the expected value. Common across providers.
ss_publish_verify_version_file() {
  local cache="$1" current="$2" expected="$3"
  for root in "$cache" "$current"; do
    local f="$root/VERSION"
    if [[ ! -f "$f" || -L "$f" ]]; then
      echo "ERROR: $f is missing or still a symlink (expected materialized file)" >&2
      return 1
    fi
    local actual
    actual="$(head -n1 "$f" | tr -d '[:space:]')"
    if [[ "$actual" != "$expected" ]]; then
      echo "ERROR: $f content '$actual' != expected '$expected'" >&2
      return 1
    fi
  done
}

# Rewrite hook command-paths in <cache>/hooks/hooks.json and
# <current>/hooks/hooks.json. Handles BOTH "${CLAUDE_PLUGIN_ROOT:-.}/..."
# and "${CLAUDE_PLUGIN_ROOT}/..." variants so the Claude publisher's behaviour
# is preserved.
ss_publish_rewrite_hooks() {
  local cache="$1" current="$2"
  python3 - "$cache" "$current" <<'PY'
import json
import shlex
import sys
from pathlib import Path

cache = Path(sys.argv[1]).resolve()
current = Path(sys.argv[2]).resolve()
hook_runner = shlex.quote(str(current / "hooks" / "run-hook.cmd"))

PATTERNS = (
    '"${CLAUDE_PLUGIN_ROOT:-.}/hooks/run-hook.cmd"',
    '"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd"',
)

for root in (cache, current):
    hooks_json = root / "hooks" / "hooks.json"
    if not hooks_json.exists():
        continue
    config = json.loads(hooks_json.read_text(encoding="utf-8"))
    for event_entries in config.get("hooks", {}).values():
        for entry in event_entries:
            for hook in entry.get("hooks", []):
                command = hook.get("command")
                if isinstance(command, str):
                    for pattern in PATTERNS:
                        command = command.replace(pattern, hook_runner)
                    hook["command"] = command
    hooks_json.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
PY
}

# Verify cache + current have the expected manifest and required payload paths.
# manifest_subpath is e.g. ".codex-plugin/plugin.json" or ".claude-plugin/plugin.json".
# required_paths is a colon-separated list of paths relative to each root.
ss_publish_verify_payload() {
  local cache="$1" current="$2" plugin="$3" expected="$4"
  local manifest_subpath="$5" required_paths="$6"
  python3 - "$cache" "$current" "$plugin" "$expected" "$manifest_subpath" "$required_paths" <<'PY'
import json
import sys
from pathlib import Path

cache, current = Path(sys.argv[1]), Path(sys.argv[2])
plugin, expected = sys.argv[3], sys.argv[4]
manifest_subpath = sys.argv[5]
required = sys.argv[6].split(":")

for root in (cache, current):
    manifest = root / manifest_subpath
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("name") != plugin:
        raise SystemExit(f"{root} manifest name mismatch: {data.get('name')!r} != {plugin!r}")
    if data.get("version") != expected:
        raise SystemExit(f"{root} manifest version mismatch: {data.get('version')!r} != {expected!r}")
    for rel in required:
        if not rel:
            continue
        if not (root / rel).exists():
            raise SystemExit(f"{root} missing required payload: {rel}")
    for rel in ("skills", "hooks", "tools", "assets"):
        if (root / rel).exists() and (root / rel).is_symlink():
            raise SystemExit(f"{root} {rel} payload is still a symlink; expected materialized path")
print(f"PASS: {plugin} cache + current materialized")
PY
}

# Restamp the external-reviewer shim against the just-materialised current/.
# This preserves X14's "external-reviewer survives dev-checkout moves" property.
ss_publish_restamp_external_reviewer() {
  local current="$1"
  EXTERNAL_REVIEWER_SOURCE_ROOT="$current" \
    "$current/skills/external-review/install.sh"
}
```

- [ ] **Step 8.4: Convert `publish-to-local-codex.sh` to use `publish-common.sh`**

Source the lib early, set the codex-specific params, and replace the inline blocks at the end. The Codex publisher rsyncs `plugins/superstar/` so its required-payload list does **not** include `skills/external-review/scripts/external-reviewer.py` (that lives outside the plugin payload).

```bash
SCRIPT_LIB="$REPO_ROOT/scripts/lib/publish-common.sh"
# shellcheck source=scripts/lib/publish-common.sh
. "$SCRIPT_LIB"

REQUIRED_PATHS="skills/using-superstar/SKILL.md:skills/project-setup/SKILL.md:skills/using-git-worktrees/SKILL.md:hooks/run-hook.cmd:hooks/agent-finished:tools/tasktool/notify.py:assets:VERSION"

ss_publish_rsync_payload "$SOURCE" "$CACHE_DIR"
ss_publish_rsync_payload "$SOURCE" "$CURRENT_DIR"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run complete."
  exit 0
fi

ss_publish_rewrite_hooks "$CACHE_DIR" "$CURRENT_DIR"
ss_publish_verify_payload "$CACHE_DIR" "$CURRENT_DIR" "$PLUGIN" "$VERSION" \
    ".codex-plugin/plugin.json" "$REQUIRED_PATHS"
ss_publish_verify_version_file "$CACHE_DIR" "$CURRENT_DIR" "$VERSION"
ss_publish_restamp_external_reviewer "$CURRENT_DIR"
```

Keep the argument-parsing prelude and the dry-run path checks above this block.

- [ ] **Step 8.5: Convert `publish-to-local-claude.sh` to use `publish-common.sh`**

Claude's rsync source is `$REPO_ROOT/` with existing `--exclude` args; required-payload list adds `skills/external-review/scripts/external-reviewer.py` (which lives at this path in the dev tree the Claude cache mirrors). Set `EXTRA_RSYNC_ARGS` to carry over the existing excludes.

```bash
SCRIPT_LIB="$REPO_ROOT/scripts/lib/publish-common.sh"
# shellcheck source=scripts/lib/publish-common.sh
. "$SCRIPT_LIB"

REQUIRED_PATHS="skills/using-superstar/SKILL.md:skills/project-setup/SKILL.md:skills/using-git-worktrees/SKILL.md:skills/external-review/scripts/external-reviewer.py:hooks/run-hook.cmd:hooks/agent-finished:tools/tasktool/notify.py:assets:VERSION"

export EXTRA_RSYNC_ARGS="--exclude .git/ --exclude .pytest_cache/ --exclude __pycache__/ --exclude docs/reviewer/"

ss_publish_rsync_payload "$REPO_ROOT" "$CACHE_DIR"
ss_publish_rsync_payload "$REPO_ROOT" "$CURRENT_DIR"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run complete."
  exit 0
fi

ss_publish_rewrite_hooks "$CACHE_DIR" "$CURRENT_DIR"
ss_publish_verify_payload "$CACHE_DIR" "$CURRENT_DIR" "$PLUGIN" "$VERSION" \
    ".claude-plugin/plugin.json" "$REQUIRED_PATHS"
ss_publish_verify_version_file "$CACHE_DIR" "$CURRENT_DIR" "$VERSION"
ss_publish_restamp_external_reviewer "$CURRENT_DIR"
```

Cross-check the existing `--exclude` list in `scripts/publish-to-local-claude.sh:108-113` against what's set in `EXTRA_RSYNC_ARGS` above — if the live file has more excludes, append them to the env value verbatim.

- [ ] **Step 8.6: Run publish regression tests**

```bash
bash tests/codex-plugin-sync/test-publish-to-local-codex.sh
bash tests/claude-code/test-publish-to-local-claude.sh
```

Expected: both pass, including the new VERSION assertions.

- [ ] **Step 8.7: Real-repo smoke test**

```bash
bash scripts/publish-to-local-codex.sh
test -f ~/.codex/plugins/cache/superstar-dev/superstar/current/VERSION && \
  cat ~/.codex/plugins/cache/superstar-dev/superstar/current/VERSION
```

Expected: file exists; content matches `cat VERSION`.

- [ ] **Step 8.8: Commit**

```bash
git add scripts/lib/publish-common.sh scripts/publish-to-local-codex.sh \
        scripts/publish-to-local-claude.sh \
        tests/codex-plugin-sync/test-publish-to-local-codex.sh \
        tests/claude-code/test-publish-to-local-claude.sh
git commit -m "X16.T8: extract publish-common.sh + verify VERSION in plugin caches"
```

---

## Task 9: scripts/deploy.sh + --check diagnostics

**Files:**
- Create: `scripts/deploy.sh`
- Create: `scripts/tests/test_deploy_check.py`

- [ ] **Step 9.1: Write the failing diagnostic test**

Create `scripts/tests/test_deploy_check.py`:

```python
"""Tests for scripts/deploy.sh --check status lattice."""
from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEPLOY = REPO_ROOT / "scripts" / "deploy.sh"


def _make_stamped_shim(path: Path, *, name: str, version: str, source_root: str, installer: str = "skills/external-review/install.sh") -> None:
    path.write_text(textwrap.dedent(f"""\
        #!/usr/bin/env bash
        # superstar-shim
        # superstar-shim-name: {name}
        # superstar-shim-version: {version}
        # superstar-shim-source-root: {source_root}
        # superstar-shim-installer: {installer}
        # superstar-shim-generated-at: 2026-05-21T00:00:00Z
        exec true
    """))
    path.chmod(0o755)


def _run_check(home: Path, source_root: Path) -> subprocess.CompletedProcess:
    env = {
        "HOME": str(home),
        "SUPERSTAR_SOURCE_ROOT": str(source_root),
        "PATH": os.environ["PATH"],
    }
    return subprocess.run(
        ["bash", str(DEPLOY), "--check"],
        env=env, capture_output=True, text=True, check=False,
    )


def test_check_exits_zero_when_all_ok(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    for name in ("external-reviewer", "reviewer-agent", "tasktool"):
        _make_stamped_shim(home / ".local" / "bin" / name, name=name, version="1.0.0", source_root=str(source))
    result = _run_check(home, source)
    assert result.returncode == 0, result.stdout + result.stderr


def test_check_exits_nonzero_on_drift(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    _make_stamped_shim(home / ".local" / "bin" / "external-reviewer", name="external-reviewer", version="0.9.0", source_root=str(source))
    _make_stamped_shim(home / ".local" / "bin" / "reviewer-agent", name="reviewer-agent", version="1.0.0", source_root=str(source))
    _make_stamped_shim(home / ".local" / "bin" / "tasktool", name="tasktool", version="1.0.0", source_root=str(source))
    result = _run_check(home, source)
    assert result.returncode != 0
    assert "DRIFT" in result.stdout


def test_check_exits_nonzero_on_malformed(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    # external-reviewer is missing the version stamp line.
    (home / ".local" / "bin" / "external-reviewer").write_text(
        "#!/usr/bin/env bash\n# superstar-shim\n# superstar-shim-name: external-reviewer\nexec true\n"
    )
    (home / ".local" / "bin" / "external-reviewer").chmod(0o755)
    _make_stamped_shim(home / ".local" / "bin" / "reviewer-agent", name="reviewer-agent", version="1.0.0", source_root=str(source))
    _make_stamped_shim(home / ".local" / "bin" / "tasktool", name="tasktool", version="1.0.0", source_root=str(source))
    result = _run_check(home, source)
    assert result.returncode != 0
    assert "MALFORMED" in result.stdout


def test_check_exits_nonzero_on_missing_target(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    # Only two of three shims installed.
    _make_stamped_shim(home / ".local" / "bin" / "external-reviewer", name="external-reviewer", version="1.0.0", source_root=str(source))
    _make_stamped_shim(home / ".local" / "bin" / "reviewer-agent", name="reviewer-agent", version="1.0.0", source_root=str(source))
    # tasktool deliberately absent.
    result = _run_check(home, source)
    assert result.returncode != 0
    assert "MISSING_TARGET" in result.stdout


def test_check_exits_nonzero_on_missing_source(tmp_path: Path) -> None:
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = tmp_path / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    for name in ("external-reviewer", "reviewer-agent", "tasktool"):
        _make_stamped_shim(home / ".local" / "bin" / name, name=name, version="1.0.0", source_root="/nonexistent/path")
    result = _run_check(home, source)
    assert result.returncode != 0
    assert "MISSING_SOURCE" in result.stdout


def test_check_zero_on_source_root_info_only(tmp_path: Path) -> None:
    """Same version across shims, different source-root values, no other issues -> exit 0."""
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source_a = tmp_path / "src-a"; source_a.mkdir(); (source_a / "VERSION").write_text("1.0.0\n")
    source_b = tmp_path / "src-b"; source_b.mkdir(); (source_b / "VERSION").write_text("1.0.0\n")
    _make_stamped_shim(home / ".local" / "bin" / "external-reviewer", name="external-reviewer", version="1.0.0", source_root=str(source_a))
    _make_stamped_shim(home / ".local" / "bin" / "reviewer-agent", name="reviewer-agent", version="1.0.0", source_root=str(source_b))
    _make_stamped_shim(home / ".local" / "bin" / "tasktool", name="tasktool", version="1.0.0", source_root=str(source_b))
    result = _run_check(home, source_a)
    assert result.returncode == 0, result.stdout + result.stderr
    # Diagnostic still mentions the asymmetry.
    assert "SOURCE_ROOT_INFO" in result.stdout or "source-root differs" in result.stdout.lower()


def test_check_home_literal_expanded_in_output(tmp_path: Path) -> None:
    """$HOME/ in stamped values must be expanded when printed."""
    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
    source = home / "src"; source.mkdir()
    (source / "VERSION").write_text("1.0.0\n")
    for name in ("external-reviewer", "reviewer-agent", "tasktool"):
        _make_stamped_shim(home / ".local" / "bin" / name, name=name, version="1.0.0", source_root="$HOME/src")
    result = _run_check(home, source)
    assert "$HOME/" not in result.stdout  # not surfaced literally
    assert str(source) in result.stdout  # expanded form is
```

- [ ] **Step 9.2: Run to verify it fails**

```bash
python3 -m pytest scripts/tests/test_deploy_check.py -v
```

Expected: failures — `scripts/deploy.sh` doesn't exist.

- [ ] **Step 9.3: Create `scripts/deploy.sh`**

```bash
#!/usr/bin/env bash
# scripts/deploy.sh — top-level Superstar deploy + drift diagnostic.
#
# Modes:
#   deploy.sh            Full: codex publish + claude publish + re-run all installers + print --check
#   deploy.sh --check    Read-only diagnostics. Non-zero exit on DRIFT/MALFORMED/MISSING_*.
#   deploy.sh --codex-only    Skip Claude publish; still re-run installers
#   deploy.sh --claude-only   Skip Codex publish; still re-run installers
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SUPERSTAR_SOURCE_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

MODE="deploy"
SKIP_CODEX=0
SKIP_CLAUDE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) MODE="check"; shift ;;
    --codex-only) SKIP_CLAUDE=1; shift ;;
    --claude-only) SKIP_CODEX=1; shift ;;
    -h|--help)
      sed -n '2,/^set -euo pipefail/{/^set -euo pipefail/d; p;}' "$0"
      exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

BIN_DIR="${HOME}/.local/bin"
CODEX_CURRENT="${HOME}/.codex/plugins/cache/superstar-dev/superstar/current"
CLAUDE_CURRENT="${HOME}/.claude/plugins/cache/superstar-dev/superstar/current"

EXPAND_PATH() {
  # §6b parser: expand leading $HOME/ and ~/ in stamped path values.
  local v="$1"
  v="${v/#\$HOME/$HOME}"
  v="${v/#\~/$HOME}"
  printf '%s\n' "$v"
}

PARSE_HEADER() {
  # $1 = file path; reads up to 32 lines and emits "key=value" lines for the keys we care about.
  local file="$1"
  awk 'NR<=32 && /^#[[:space:]]*superstar-(shim|hook)-/ {
        sub(/^#[[:space:]]*/, "", $0);
        n = index($0, ":");
        if (n>0) {
          key = substr($0, 1, n-1);
          val = substr($0, n+1);
          sub(/^[[:space:]]+/, "", val);
          sub(/[[:space:]]+$/, "", val);
          printf "%s=%s\n", key, val;
        }
      }' "$file"
}

# Diagnostics ----------------------------------------------------------------

run_check() {
  local exit_code=0
  local dev_version
  if [[ -r "$REPO_ROOT/VERSION" ]]; then
    dev_version="$(head -n1 "$REPO_ROOT/VERSION" | tr -d '[:space:]')"
  else
    echo "ERROR: $REPO_ROOT/VERSION not readable" >&2
    return 1
  fi
  echo "Dev-checkout VERSION: $dev_version ($REPO_ROOT/VERSION)"
  echo "(Each shim is compared against its OWN stamped source-root's VERSION,"
  echo " not the dev checkout — external-reviewer may legitimately be stamped"
  echo " against a plugin-cache current/ instead.)"
  echo ""

  echo "Global shims:"
  local source_roots=()
  for name in external-reviewer reviewer-agent tasktool; do
    local target="$BIN_DIR/$name"
    printf "  %-20s %s\n" "$name" "$target"
    if [[ ! -f "$target" ]]; then
      printf "    status: MISSING_TARGET\n"
      exit_code=1
      continue
    fi
    local header
    header="$(PARSE_HEADER "$target")"
    local shim_version shim_root
    shim_version="$(printf '%s\n' "$header" | sed -n 's/^superstar-shim-version=//p')"
    shim_root="$(printf '%s\n' "$header" | sed -n 's/^superstar-shim-source-root=//p')"
    if [[ -z "$shim_version" || -z "$shim_root" ]]; then
      printf "    status: MALFORMED\n"
      exit_code=1
      continue
    fi
    local expanded_root
    expanded_root="$(EXPAND_PATH "$shim_root")"
    if [[ ! -d "$expanded_root" ]]; then
      printf "    stamped source-root: %s\n" "$expanded_root"
      printf "    status: MISSING_SOURCE\n"
      exit_code=1
      continue
    fi
    # Compare against the shim's OWN stamped source-root, not the dev checkout.
    local shim_src_vfile="$expanded_root/VERSION"
    if [[ ! -r "$shim_src_vfile" ]]; then
      printf "    stamped source-root: %s\n" "$expanded_root"
      printf "    status: MISSING_SOURCE (source-root has no readable VERSION)\n"
      exit_code=1
      continue
    fi
    local shim_src_version
    shim_src_version="$(head -n1 "$shim_src_vfile" | tr -d '[:space:]')"
    if [[ "$shim_version" != "$shim_src_version" ]]; then
      printf "    stamped version: %s\n" "$shim_version"
      printf "    source root: %s\n" "$expanded_root"
      printf "    status: DRIFT (source-root has %s)\n" "$shim_src_version"
      exit_code=1
      continue
    fi
    source_roots+=("$expanded_root")
    printf "    stamped version: %s\n" "$shim_version"
    printf "    source root: %s (VERSION=%s)\n" "$expanded_root" "$shim_src_version"
    printf "    status: OK\n"
  done

  echo ""
  echo "Plugin caches:"
  for entry in "codex:$CODEX_CURRENT" "claude:$CLAUDE_CURRENT"; do
    local label="${entry%%:*}"
    local dir="${entry#*:}"
    if [[ ! -d "$dir" ]]; then
      # Not failing — the user may not have published this cache yet.
      printf "  %-10s %s     status: NOT_DEPLOYED (informational)\n" "$label" "$dir"
      continue
    fi
    local vf="$dir/VERSION"
    if [[ ! -r "$vf" ]]; then
      printf "  %-10s %s     status: MISSING_CACHE_VERSION (cache present but VERSION absent)\n" "$label" "$dir"
      exit_code=1
      continue
    fi
    local v
    v="$(head -n1 "$vf" | tr -d '[:space:]')"
    # Plugin caches are deploy outputs of the dev checkout; they should match dev_version.
    if [[ "$v" != "$dev_version" ]]; then
      printf "  %-10s %s     version: %s     status: DRIFT (dev is %s)\n" "$label" "$dir" "$v" "$dev_version"
      exit_code=1
    else
      printf "  %-10s %s     version: %s     status: OK\n" "$label" "$dir" "$v"
    fi
  done

  # Source-root info row (informational only)
  if [[ ${#source_roots[@]} -gt 1 ]]; then
    local first="${source_roots[0]}"
    local mismatch=0
    for r in "${source_roots[@]}"; do
      [[ "$r" != "$first" ]] && mismatch=1
    done
    if [[ "$mismatch" -eq 1 ]]; then
      echo ""
      echo "SOURCE_ROOT_INFO: shims point at different source roots (informational, not a failure)"
    fi
  fi

  echo ""
  if [[ "$exit_code" -eq 0 ]]; then
    echo "All checked rows OK."
  else
    echo "One or more rows failed; see statuses above."
  fi
  return "$exit_code"
}

# Deploy ---------------------------------------------------------------------

run_deploy() {
  if [[ "$SKIP_CODEX" -eq 0 ]]; then
    bash "$REPO_ROOT/scripts/publish-to-local-codex.sh"
  fi
  if [[ "$SKIP_CLAUDE" -eq 0 ]]; then
    bash "$REPO_ROOT/scripts/publish-to-local-claude.sh"
  fi
  bash "$REPO_ROOT/skills/project-setup/install-reviewer-agent.sh" --force
  bash "$REPO_ROOT/tools/tasktool/install.sh" --force
  if git -C "$REPO_ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
    bash "$REPO_ROOT/tools/tasktool/install.sh" --hook --force
  fi
  echo ""
  run_check
}

case "$MODE" in
  check) run_check ;;
  deploy) run_deploy ;;
esac
```

Make it executable: `chmod +x scripts/deploy.sh`.

- [ ] **Step 9.4: Run diagnostic tests**

```bash
python3 -m pytest scripts/tests/test_deploy_check.py -v
```

Expected: all eight tests pass.

- [ ] **Step 9.5: Real-repo smoke test**

```bash
bash scripts/deploy.sh --check
echo "exit code: $?"
```

Expected: tables showing each shim and cache. Exit code 0 if the repo is clean; non-zero if any shim or cache currently has drift (which would be a pre-existing issue worth fixing).

- [ ] **Step 9.6: Commit**

```bash
git add scripts/deploy.sh scripts/tests/test_deploy_check.py
git commit -m "X16.T9: scripts/deploy.sh with --check status lattice"
```

---

## Task 10: Remove compat shim + project-setup docs row

**Files:**
- Delete: `skills/project-setup/scripts/external-reviewer-shim.py`
- Delete: `skills/external-review/tests/test_external_reviewer_compat_shim.py`
- Modify: `skills/project-setup/SKILL.md`

- [ ] **Step 10.1: Delete the compat shim and its test**

```bash
git rm skills/project-setup/scripts/external-reviewer-shim.py
git rm skills/external-review/tests/test_external_reviewer_compat_shim.py
```

- [ ] **Step 10.2: Remove row 7b from `skills/project-setup/SKILL.md`**

Open `skills/project-setup/SKILL.md`. Find the line beginning `| 7b |` (the row that describes the legacy `scripts/external-reviewer.py` compat shim) and delete that entire table row. Also delete any surrounding paragraphs that reference `external-reviewer-shim.py` (the SKILL has at least one mention in the "Safe reviewer wrapper" or precondition discussion — remove the sentence, not the whole section). Search and verify:

```bash
grep -n "external-reviewer-shim\|row 7b\|compatibility shim" skills/project-setup/SKILL.md
```

Expected: zero matches after the edit.

- [ ] **Step 10.3: Confirm the test suite still passes**

```bash
python3 -m pytest skills/external-review/tests/ -v
python3 -m pytest skills/project-setup/tests/ -v 2>/dev/null || true
```

Expected: no test referencing the deleted compat shim. All remaining tests pass.

- [ ] **Step 10.4: Commit**

```bash
git add skills/project-setup/SKILL.md
git commit -m "X16.T10: remove external-reviewer compat shim and its scaffolding"
```

(The `git rm` commands in Step 10.1 already staged the deletions; this commit captures everything together with the SKILL.md edit.)

---

## Task 11: External plan review + close X16

**Files:**
- None new; gating step only.

- [ ] **Step 11.1: Run the full test suite end-to-end**

```bash
python3 -m pytest scripts/tests/ tools/tasktool/tests/ skills/external-review/tests/ -v
bash tests/codex-plugin-sync/test-publish-to-local-codex.sh
bash tests/claude-code/test-publish-to-local-claude.sh
```

Expected: every test passes.

- [ ] **Step 11.2: Run `deploy.sh --check` and confirm exit 0**

```bash
bash scripts/deploy.sh --check
```

Expected: every row OK, exit 0. If any row is DRIFT/MALFORMED/MISSING_*, fix before proceeding.

- [ ] **Step 11.3: Ask the user about the version bump**

Per `CLAUDE.md`'s binding rule: "Before committing finished work that ships to users — skill changes, hook changes, tooling changes, anything in `plugins/superstar/`, `skills/`, `hooks/`, or `tools/` — ask the user whether to bump the version."

This work touches `skills/`, `tools/`, and adds top-level `VERSION` machinery. **Do not bump unilaterally.** Surface the question:

> "X16 is ready to close. Bump the version before deploying? Current is X.Y.Z → patch X.Y.(Z+1) / minor X.(Y+1).0 / no bump."

If the user says yes, run:

```bash
bash scripts/bump-version.sh <new-version>
git add -A
git commit -m "Bump Superstar to <new-version>"
```

If no, proceed without bumping.

- [ ] **Step 11.4: Run `deploy.sh` (full)**

```bash
bash scripts/deploy.sh
```

Expected: codex publish + claude publish + all installers re-run + `--check` summary shows everything OK.

- [ ] **Step 11.5: External plan review**

```bash
external-reviewer review --kind plan \
    --file docs/plans/2026-05-21-X16-shim-version-stamping.md \
    --work-id X16 \
    --context docs/specs/2026-05-21-X16-shim-version-stamping-design.md \
    --context docs/tasklist.json \
    --emit json
```

Iterate until verdict is `ready` or `ready with small edits`. Apply findings inline (no parallel implementation subagents at plan stage; coordinator may edit directly per the external-review skill rules).

- [ ] **Step 11.6: Close X16**

```bash
tasktool close X16
```

Expected: tasktool advances X16 to closed status. The pre-commit hook validates the closeout commit.

- [ ] **Step 11.7: Final commit**

```bash
git add docs/tasklist.json docs/reviewer/x16-shim-version-stamping/
git commit -m "X16: close — shim version stamping landed"
```

---

## Self-review checklist (run before invoking external plan review)

- **Spec coverage.** Every spec section maps to a task:
  - §1 (VERSION) → T1
  - §2 (shim header) → embedded in T3, T4, T5
  - §3 (shared fragment) → T2
  - §4 (strict failure semantics) → fragment (T2) + tests in T3/T4/T5
  - §5 (reviewer-agent migration) → T4
  - §6 (hook handshake) → T6 + T7
  - §6a (legacy marker migration) → T6
  - §6b (header parser) → T7 (`hook_handshake._parse_header` + `_expand_path`); T9 (deploy.sh `PARSE_HEADER` + `EXPAND_PATH`)
  - §7 (bump-version plain format) → T1
  - §8 (publish/deploy + source-root policy) → T8 + T9
  - §9 (diagnostics + status lattice) → T9
  - Removals (compat shim) → T10
  - Acceptance criteria #1–#10 each mapped to a test in T1–T9.

- **Placeholder scan.** No "TBD", "TODO", "implement later". Every code step contains the actual code. Every command step contains the exact command.

- **Type/name consistency.** `__superstar_check_version` used identically in T2/T3/T4/T5. `check_pre_commit_hook` used identically in T7 cli wiring and tests. `PARSE_HEADER` / `EXPAND_PATH` used internally in deploy.sh only.

- **Scheduling.** X16 is cross-cutting (no slice graph). Confirmed via `tasktool show X16` — single row, no `depends_on`/`parallel_group`/`ratify` needed.