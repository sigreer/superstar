#!/usr/bin/env bash
#
# Publish this Superstar checkout into Claude Code's local plugin cache.
#
# The script keeps a versioned cache directory and a stable materialized
# `current/` directory in sync. Hook commands and the global external-reviewer
# shim point at `current/`, so future version bumps do not require project-level
# script updates.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=scripts/lib/publish-common.sh
. "$REPO_ROOT/scripts/lib/publish-common.sh"

MARKETPLACE="superstar-dev"
PLUGIN="superstar"
SCOPE="user"
DRY_RUN=0
SKIP_CLAUDE_UPDATE=0
CACHE_ROOT="${CLAUDE_HOME:-$HOME/.claude}/plugins/cache"

usage() {
  cat <<'EOF'
Usage: scripts/publish-to-local-claude.sh [options]

Options:
  --marketplace NAME     Marketplace name (default: superstar-dev)
  --plugin NAME          Plugin name (default: superstar)
  --scope SCOPE          Claude install/update scope (default: user)
  --cache-root PATH      Claude plugin cache root (default: $CLAUDE_HOME/plugins/cache or ~/.claude/plugins/cache)
  --skip-claude-update   Skip `claude plugin update/install`; only materialize and verify cache
  -n, --dry-run          Print actions without writing
  -h, --help             Show this help

Publishes this checkout into:
  <cache-root>/<marketplace>/<plugin>/<version>/
  <cache-root>/<marketplace>/<plugin>/current/

Both directories are real materialized copies, not symlinks. Hook commands and
the global external-reviewer command are rewritten to use current/.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --marketplace) MARKETPLACE="$2"; shift 2 ;;
    --plugin) PLUGIN="$2"; shift 2 ;;
    --scope) SCOPE="$2"; shift 2 ;;
    --cache-root) CACHE_ROOT="$2"; shift 2 ;;
    --skip-claude-update) SKIP_CLAUDE_UPDATE=1; shift ;;
    -n|--dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage >&2; exit 2 ;;
  esac
done

MANIFEST="$REPO_ROOT/.claude-plugin/plugin.json"

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
echo "Source:  $REPO_ROOT"
echo "Cache:   $CACHE_DIR"
echo "Current: $CURRENT_DIR"

if [[ "$SKIP_CLAUDE_UPDATE" -eq 0 ]]; then
  command -v claude >/dev/null || { echo "ERROR: claude CLI not found" >&2; exit 1; }
  if ! run claude plugin update --scope "$SCOPE" "$PLUGIN@$MARKETPLACE"; then
    run claude plugin install --scope "$SCOPE" "$PLUGIN@$MARKETPLACE"
  fi
fi

command -v rsync >/dev/null || { echo "ERROR: rsync not found" >&2; exit 1; }

REQUIRED_PATHS="skills/using-superstar/SKILL.md:skills/project-setup/SKILL.md:skills/using-git-worktrees/SKILL.md:skills/external-review/scripts/external-reviewer.py:hooks/hooks.json:hooks/run-hook.cmd:hooks/agent-finished:hooks/todo-snapshot:tools/tasktool/notify.py:assets:VERSION"

export EXTRA_RSYNC_ARGS="--exclude .git/ --exclude .worktrees/ --exclude .agents/ --exclude .pytest_cache/ --exclude __pycache__/ --exclude docs/reviewer/"

DRY_RUN="$DRY_RUN" ss_publish_rsync_payload "$REPO_ROOT" "$CACHE_DIR"
DRY_RUN="$DRY_RUN" ss_publish_rsync_payload "$REPO_ROOT" "$CURRENT_DIR"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run complete."
  exit 0
fi

ss_publish_rewrite_hooks "$CACHE_DIR" "$CURRENT_DIR"
ss_publish_verify_payload "$CACHE_DIR" "$CURRENT_DIR" "$PLUGIN" "$VERSION" \
    ".claude-plugin/plugin.json" "$REQUIRED_PATHS"
ss_publish_verify_version_file "$CACHE_DIR" "$CURRENT_DIR" "$VERSION"
ss_publish_restamp_external_reviewer "$CURRENT_DIR"
