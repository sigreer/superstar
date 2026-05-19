#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

python3 - "$ROOT/hooks/hooks.json" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    config = json.load(f)

hooks = config["hooks"]
for event_name in ("Stop", "SubagentStop"):
    event_entries = hooks.get(event_name, [])
    assert event_entries, f"{event_name} hook is missing"
    for entry in event_entries:
        for hook in entry.get("hooks", []):
            assert hook.get("async") is not True, f"{event_name} hook uses unsupported async=true"
            assert "agent-finished" in hook.get("command", ""), f"{event_name} hook does not call agent-finished"

print("PASS: Stop/SubagentStop hooks are Codex-compatible")
PY
