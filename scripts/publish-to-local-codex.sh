#!/usr/bin/env bash
#
# Publish the repo-local Superstar marketplace payload into Codex's local cache.
#
# Codex's local marketplace installer currently does not materialize symlinked
# payload directories reliably. This wrapper installs the plugin, then copies the
# local wrapper payload with symlinks followed so the versioned cache contains
# real skills/assets for new Codex sessions.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

MARKETPLACE="superstar-dev"
PLUGIN="superstar"
DRY_RUN=0
SKIP_CODEX_ADD=0
CACHE_ROOT="${CODEX_HOME:-$HOME/.codex}/plugins/cache"

usage() {
  cat <<'EOF'
Usage: scripts/publish-to-local-codex.sh [options]

Options:
  --marketplace NAME   Marketplace name (default: superstar-dev)
  --plugin NAME        Plugin name (default: superstar)
  --cache-root PATH    Codex plugin cache root (default: $CODEX_HOME/plugins/cache or ~/.codex/plugins/cache)
  --skip-codex-add     Skip `codex plugin add`; only materialize and verify cache
  -n, --dry-run        Print actions without writing
  -h, --help           Show this help

Publishes plugins/superstar into:
  <cache-root>/<marketplace>/<plugin>/<version>/

The script follows symlinks so cache/<version>/skills is a real directory.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --marketplace) MARKETPLACE="$2"; shift 2 ;;
    --plugin) PLUGIN="$2"; shift 2 ;;
    --cache-root) CACHE_ROOT="$2"; shift 2 ;;
    --skip-codex-add) SKIP_CODEX_ADD=1; shift ;;
    -n|--dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage >&2; exit 2 ;;
  esac
done

SOURCE="$REPO_ROOT/plugins/$PLUGIN"
MANIFEST="$SOURCE/.codex-plugin/plugin.json"

[[ -d "$SOURCE" ]] || { echo "ERROR: source plugin not found: $SOURCE" >&2; exit 1; }
[[ -f "$MANIFEST" ]] || { echo "ERROR: source manifest not found: $MANIFEST" >&2; exit 1; }

VERSION="$(
  python3 - "$MANIFEST" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as f:
    print(json.load(f)["version"])
PY
)"

CACHE_DIR="$CACHE_ROOT/$MARKETPLACE/$PLUGIN/$VERSION"

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '+ %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

echo "Publishing $PLUGIN@$MARKETPLACE version $VERSION"
echo "Source: $SOURCE"
echo "Cache:  $CACHE_DIR"

if [[ "$SKIP_CODEX_ADD" -eq 0 ]]; then
  command -v codex >/dev/null || { echo "ERROR: codex CLI not found" >&2; exit 1; }
  run codex plugin add "$PLUGIN@$MARKETPLACE"
fi

command -v rsync >/dev/null || { echo "ERROR: rsync not found" >&2; exit 1; }
run mkdir -p "$CACHE_DIR"
run rsync -aL --delete "$SOURCE/" "$CACHE_DIR/"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run complete."
  exit 0
fi

python3 - "$CACHE_DIR" "$PLUGIN" "$VERSION" <<'PY'
import json
import sys
from pathlib import Path

cache = Path(sys.argv[1])
plugin = sys.argv[2]
expected = sys.argv[3]
manifest = cache / ".codex-plugin" / "plugin.json"
data = json.loads(manifest.read_text(encoding="utf-8"))
if data.get("name") != plugin:
    raise SystemExit(f"cache manifest name mismatch: {data.get('name')!r} != {plugin!r}")
if data.get("version") != expected:
    raise SystemExit(f"cache manifest version mismatch: {data.get('version')!r} != {expected!r}")
for rel in ("skills/using-superstar/SKILL.md", "skills/project-setup/SKILL.md", "skills/using-git-worktrees/SKILL.md", "assets"):
    if not (cache / rel).exists():
        raise SystemExit(f"cache missing required payload: {rel}")
if (cache / "skills").is_symlink():
    raise SystemExit("cache skills payload is still a symlink; expected materialized directory")
print(f"PASS: {plugin} cache is materialized at {cache}")
PY
