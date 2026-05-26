#!/usr/bin/env bash
#
# Publish the repo-local Superstar marketplace payload into Codex's local cache.
#
# Codex's local marketplace installer currently does not materialize symlinked
# payload directories reliably. This wrapper installs the plugin, then copies the
# local wrapper payload with symlinks followed so the versioned cache contains
# real skills, hooks, tools, and assets for new Codex sessions.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=scripts/lib/publish-common.sh
. "$REPO_ROOT/scripts/lib/publish-common.sh"

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
  <cache-root>/<marketplace>/<plugin>/current/

The script follows symlinks so cache/<version> and cache/current contain real
directories/files.
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

VERSION="$(ss_publish_resolve_version "$MANIFEST")"

PLUGIN_CACHE_ROOT="$CACHE_ROOT/$MARKETPLACE/$PLUGIN"
CACHE_DIR="$PLUGIN_CACHE_ROOT/$VERSION"
CURRENT_DIR="$PLUGIN_CACHE_ROOT/current"

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
echo "Current: $CURRENT_DIR"

if [[ "$SKIP_CODEX_ADD" -eq 0 ]]; then
  command -v codex >/dev/null || { echo "ERROR: codex CLI not found" >&2; exit 1; }
  run codex plugin add "$PLUGIN@$MARKETPLACE"
fi

command -v rsync >/dev/null || { echo "ERROR: rsync not found" >&2; exit 1; }

REQUIRED_PATHS="skills/using-superstar/SKILL.md:skills/project-setup/SKILL.md:skills/using-git-worktrees/SKILL.md:hooks/hooks.json:hooks/run-hook.cmd:hooks/agent-finished:hooks/todo-snapshot:tools/tasktool/notify.py:assets:VERSION:scripts/lib/shim-version-check.sh"

DRY_RUN="$DRY_RUN" ss_publish_rsync_payload "$SOURCE" "$CACHE_DIR"
DRY_RUN="$DRY_RUN" ss_publish_rsync_payload "$SOURCE" "$CURRENT_DIR"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run complete."
  exit 0
fi

ss_publish_rewrite_hooks "$CACHE_DIR" "$CURRENT_DIR"
ss_publish_verify_payload "$CACHE_DIR" "$CURRENT_DIR" "$PLUGIN" "$VERSION" \
    ".codex-plugin/plugin.json" "$REQUIRED_PATHS"
ss_publish_verify_version_file "$CACHE_DIR" "$CURRENT_DIR" "$VERSION"
ss_publish_restamp_external_reviewer "$CURRENT_DIR"
