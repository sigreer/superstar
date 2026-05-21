#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$ROOT/scripts/publish-to-local-claude.sh"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

BIN="$TMPDIR/bin"
CACHE="$TMPDIR/cache"
LOG="$TMPDIR/claude.log"
mkdir -p "$BIN"

cat > "$BIN/claude" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "$LOG"
exit 0
EOF
chmod +x "$BIN/claude"

PATH="$BIN:$PATH" EXTERNAL_REVIEWER_BIN="$BIN" "$SCRIPT" --cache-root "$CACHE"

VERSION="$(python3 - "$ROOT/.claude-plugin/plugin.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as f:
    print(json.load(f)["version"])
PY
)"
CACHE_DIR="$CACHE/superstar-dev/superstar/$VERSION"
CURRENT_DIR="$CACHE/superstar-dev/superstar/current"

grep -qx "plugin update --scope user superstar@superstar-dev" "$LOG"
test -f "$CACHE_DIR/.claude-plugin/plugin.json"
test -f "$CACHE_DIR/skills/using-superstar/SKILL.md"
test -f "$CACHE_DIR/skills/project-setup/SKILL.md"
test -f "$CACHE_DIR/skills/external-review/scripts/external-reviewer.py"
test -f "$CACHE_DIR/hooks/run-hook.cmd"
test -f "$CACHE_DIR/hooks/agent-finished"
test -f "$CACHE_DIR/tools/tasktool/notify.py"
test -d "$CACHE_DIR/assets"
test ! -L "$CACHE_DIR/skills"
test ! -L "$CACHE_DIR/hooks"
test ! -L "$CACHE_DIR/tools"
test -d "$CURRENT_DIR"
test ! -L "$CURRENT_DIR"
test -f "$CURRENT_DIR/hooks/run-hook.cmd"
test ! -L "$CURRENT_DIR/hooks/run-hook.cmd"

test -f "$CACHE_DIR/VERSION" || { echo "FAIL: cache <version>/VERSION missing"; exit 1; }
test -f "$CURRENT_DIR/VERSION" || { echo "FAIL: cache current/VERSION missing"; exit 1; }
test ! -L "$CACHE_DIR/VERSION" || { echo "FAIL: cache <version>/VERSION is a symlink"; exit 1; }
test ! -L "$CURRENT_DIR/VERSION" || { echo "FAIL: cache current/VERSION is a symlink"; exit 1; }
diff <(cat "$ROOT/VERSION") "$CURRENT_DIR/VERSION" \
  || { echo "FAIL: cache current/VERSION differs from repo-root VERSION"; exit 1; }

stop_command="$(
  python3 - "$CACHE_DIR/hooks/hooks.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as f:
    config = json.load(f)
print(config["hooks"]["Stop"][0]["hooks"][0]["command"])
PY
)"

case "$stop_command" in
  *"/current/hooks/run-hook.cmd agent-finished") ;;
  *) echo "expected Stop hook to use stable current entrypoint, got: $stop_command" >&2; exit 1 ;;
esac

PROJECT_DIR="$TMPDIR/project"
mkdir -p "$PROJECT_DIR"
env -u CLAUDE_PLUGIN_ROOT SUPERSTAR_NOTIFY_DRY_RUN=1 \
  bash -lc 'cd "$1" && eval "$2" >/dev/null' _ "$PROJECT_DIR" "$stop_command"

NEXT_VERSION="999.999.999"
NEXT_DIR="$CACHE/superstar-dev/superstar/$NEXT_VERSION"
cp -a "$CACHE_DIR" "$NEXT_DIR"
rm -rf "$CACHE_DIR"
env -u CLAUDE_PLUGIN_ROOT SUPERSTAR_NOTIFY_DRY_RUN=1 \
  bash -lc 'cd "$1" && eval "$2" >/dev/null' _ "$PROJECT_DIR" "$stop_command"

grep -q "/current/skills/external-review/scripts/external-reviewer.py" "$BIN/external-reviewer"

echo "PASS: publish-to-local-claude materializes plugin cache"
