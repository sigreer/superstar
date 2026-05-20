#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$ROOT/scripts/publish-to-local-codex.sh"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

BIN="$TMPDIR/bin"
CACHE="$TMPDIR/cache"
LOG="$TMPDIR/codex.log"
mkdir -p "$BIN"

cat > "$BIN/codex" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >> "$LOG"
exit 0
EOF
chmod +x "$BIN/codex"

PATH="$BIN:$PATH" "$SCRIPT" --cache-root "$CACHE"

VERSION="$(python3 - "$ROOT/plugins/superstar/.codex-plugin/plugin.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as f:
    print(json.load(f)["version"])
PY
)"
CACHE_DIR="$CACHE/superstar-dev/superstar/$VERSION"

grep -qx "plugin add superstar@superstar-dev" "$LOG"
test -f "$CACHE_DIR/.codex-plugin/plugin.json"
test -f "$CACHE_DIR/skills/using-superstar/SKILL.md"
test -f "$CACHE_DIR/skills/project-setup/SKILL.md"
test -f "$CACHE_DIR/hooks/run-hook.cmd"
test -f "$CACHE_DIR/hooks/agent-finished"
test -f "$CACHE_DIR/tools/tasktool/notify.py"
test -d "$CACHE_DIR/assets"
test ! -L "$CACHE_DIR/skills"
test ! -L "$CACHE_DIR/hooks"
test ! -L "$CACHE_DIR/tools"

stop_command="$(
  python3 - "$CACHE_DIR/hooks/hooks.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as f:
    config = json.load(f)
print(config["hooks"]["Stop"][0]["hooks"][0]["command"])
PY
)"

PROJECT_DIR="$TMPDIR/project"
mkdir -p "$PROJECT_DIR"
env -u CLAUDE_PLUGIN_ROOT SUPERSTAR_NOTIFY_DRY_RUN=1 \
  bash -lc 'cd "$1" && eval "$2" >/dev/null' _ "$PROJECT_DIR" "$stop_command"

echo "PASS: publish-to-local-codex materializes plugin cache"
