# scripts/lib/publish-common.sh - shared helpers for plugin publish scripts.
#
# Sourced by scripts/publish-to-local-codex.sh and
# scripts/publish-to-local-claude.sh. Not directly executable.

set -euo pipefail

# ss_publish_resolve_version <manifest>
# Print the .version field from a plugin manifest JSON file.
ss_publish_resolve_version() {
  local manifest="$1"
  python3 - "$manifest" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as f:
    print(json.load(f)["version"])
PY
}

# ss_publish_rsync_payload <source> <dest>
# mkdir -p the dest and rsync -aL --delete source/ -> dest/.
# Honours DRY_RUN=1 (prints commands instead of executing).
# Honours EXTRA_RSYNC_ARGS for additional flags (e.g. --exclude).
ss_publish_rsync_payload() {
  local source="$1"
  local dest="$2"
  local -a extra=()
  if [[ -n "${EXTRA_RSYNC_ARGS:-}" ]]; then
    # shellcheck disable=SC2206
    extra=(${EXTRA_RSYNC_ARGS})
  fi
  if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
    printf '+ mkdir -p %q\n' "$dest"
    printf '+ rsync -aL --delete'
    local arg
    for arg in "${extra[@]}"; do
      printf ' %q' "$arg"
    done
    printf ' %q %q\n' "$source/" "$dest/"
  else
    mkdir -p "$dest"
    rsync -aL --delete "${extra[@]}" "$source/" "$dest/"
  fi
}

# ss_publish_verify_version_file <cache> <current> <expected>
# Assert <cache>/VERSION and <current>/VERSION exist as real files
# (not symlinks) containing $expected.
ss_publish_verify_version_file() {
  local cache="$1"
  local current="$2"
  local expected="$3"
  local root
  for root in "$cache" "$current"; do
    local vf="$root/VERSION"
    if [[ ! -e "$vf" ]]; then
      echo "ERROR: $vf missing in published payload" >&2
      exit 1
    fi
    if [[ -L "$vf" ]]; then
      echo "ERROR: $vf is a symlink; expected materialized file" >&2
      exit 1
    fi
    local actual
    actual="$(head -n1 "$vf" | tr -d '[:space:]')"
    if [[ "$actual" != "$expected" ]]; then
      echo "ERROR: $vf contains '$actual', expected '$expected'" >&2
      exit 1
    fi
  done
  echo "PASS: VERSION file matches '$expected' in cache and current"
}

# ss_publish_rewrite_hooks <cache> <current>
# Rewrite hooks/hooks.json in both roots so hook commands point at
# <current>/hooks/run-hook.cmd absolutely.
ss_publish_rewrite_hooks() {
  local cache="$1"
  local current="$2"
  python3 - "$cache" "$current" <<'PY'
import json
import shlex
import sys
from pathlib import Path

cache = Path(sys.argv[1]).resolve()
current = Path(sys.argv[2]).resolve()
hook_runner = shlex.quote(str(current / "hooks" / "run-hook.cmd"))

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
                    command = command.replace(
                        '"${CLAUDE_PLUGIN_ROOT:-.}/hooks/run-hook.cmd"',
                        hook_runner,
                    )
                    command = command.replace(
                        '"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd"',
                        hook_runner,
                    )
                    hook["command"] = command
    hooks_json.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
PY
}

# ss_publish_verify_payload <cache> <current> <plugin> <expected> <manifest_subpath> <required_paths>
# required_paths: colon-separated list of relative paths that must exist in
# both cache and current.
ss_publish_verify_payload() {
  local cache="$1"
  local current="$2"
  local plugin="$3"
  local expected="$4"
  local manifest_subpath="$5"
  local required_paths="$6"
  python3 - "$cache" "$current" "$plugin" "$expected" "$manifest_subpath" "$required_paths" <<'PY'
import sys
import json
from pathlib import Path

cache = Path(sys.argv[1])
current = Path(sys.argv[2])
plugin = sys.argv[3]
expected = sys.argv[4]
manifest_subpath = sys.argv[5]
required_paths = [p for p in sys.argv[6].split(":") if p]

for root in (cache, current):
    manifest = root / manifest_subpath
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("name") != plugin:
        raise SystemExit(f"{root} manifest name mismatch: {data.get('name')!r} != {plugin!r}")
    if data.get("version") != expected:
        raise SystemExit(f"{root} manifest version mismatch: {data.get('version')!r} != {expected!r}")
    for rel in required_paths:
        if not (root / rel).exists():
            raise SystemExit(f"{root} missing required payload: {rel}")
    for rel in ("skills", "hooks", "tools", "assets"):
        if (root / rel).is_symlink():
            raise SystemExit(f"{root} {rel} payload is still a symlink; expected materialized path")

print(f"PASS: {plugin} cache is materialized at {cache}")
print(f"PASS: {plugin} current entrypoint is materialized at {current}")
PY
}

# ss_publish_restamp_external_reviewer <current>
# Re-run the external-reviewer installer pointed at <current> so the
# global shim re-stamps against the freshly published payload.
ss_publish_restamp_external_reviewer() {
  local current="$1"
  EXTERNAL_REVIEWER_SOURCE_ROOT="$current" \
    "$current/skills/external-review/install.sh"
}
