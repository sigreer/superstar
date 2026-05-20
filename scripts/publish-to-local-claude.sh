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

VERSION="$(
  python3 - "$MANIFEST" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as f:
    print(json.load(f)["version"])
PY
)"

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
run mkdir -p "$CACHE_DIR"
run rsync -aL --delete \
  --exclude ".git/" \
  --exclude ".worktrees/" \
  --exclude ".agents/" \
  --exclude ".pytest_cache/" \
  --exclude "__pycache__/" \
  --exclude "docs/reviewer/" \
  "$REPO_ROOT/" "$CACHE_DIR/"
run mkdir -p "$CURRENT_DIR"
run rsync -aL --delete \
  --exclude ".git/" \
  --exclude ".worktrees/" \
  --exclude ".agents/" \
  --exclude ".pytest_cache/" \
  --exclude "__pycache__/" \
  --exclude "docs/reviewer/" \
  "$REPO_ROOT/" "$CURRENT_DIR/"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry run complete."
  exit 0
fi

python3 - "$CACHE_DIR" "$CURRENT_DIR" <<'PY'
import json
import shlex
import sys
from pathlib import Path

cache = Path(sys.argv[1]).resolve()
current = Path(sys.argv[2]).resolve()
hook_runner = shlex.quote(str(current / "hooks" / "run-hook.cmd"))

for root in (cache, current):
    hooks_json = root / "hooks" / "hooks.json"
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

python3 - "$CACHE_DIR" "$CURRENT_DIR" "$PLUGIN" "$VERSION" <<'PY'
import json
import sys
from pathlib import Path

cache = Path(sys.argv[1])
current = Path(sys.argv[2])
plugin = sys.argv[3]
expected = sys.argv[4]

for root in (cache, current):
    manifest = root / ".claude-plugin" / "plugin.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("name") != plugin:
        raise SystemExit(f"{root} manifest name mismatch: {data.get('name')!r} != {plugin!r}")
    if data.get("version") != expected:
        raise SystemExit(f"{root} manifest version mismatch: {data.get('version')!r} != {expected!r}")
    for rel in (
        "skills/using-superstar/SKILL.md",
        "skills/project-setup/SKILL.md",
        "skills/using-git-worktrees/SKILL.md",
        "skills/external-review/scripts/external-reviewer.py",
        "hooks/run-hook.cmd",
        "hooks/agent-finished",
        "tools/tasktool/notify.py",
        "assets",
    ):
        if not (root / rel).exists():
            raise SystemExit(f"{root} missing required payload: {rel}")
    for rel in ("skills", "hooks", "tools", "assets"):
        if (root / rel).is_symlink():
            raise SystemExit(f"{root} {rel} payload is still a symlink; expected materialized path")

print(f"PASS: {plugin} cache is materialized at {cache}")
print(f"PASS: {plugin} current entrypoint is materialized at {current}")
PY

EXTERNAL_REVIEWER_SOURCE_ROOT="$CURRENT_DIR" \
  "$CURRENT_DIR/skills/external-review/install.sh"
