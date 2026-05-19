#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOK="$ROOT/hooks/agent-finished"

run_case() {
  local name="$1"
  local expected_style="$2"
  local payload="$3"
  local actual

  actual="$(SUPERSTAR_NOTIFY_DRY_RUN=1 CLAUDE_PLUGIN_ROOT="$ROOT" "$HOOK" <<<"$payload")"
  if ! python3 - "$actual" "$expected_style" <<'PY'
import json
import sys
event = json.loads(sys.argv[1])
expected_style = sys.argv[2]
assert event["type"] == "agent-ding"
assert event["style"] == expected_style
PY
  then
    echo "FAIL: $name" >&2
    echo "expected style: $expected_style" >&2
    echo "actual:   $actual" >&2
    exit 1
  fi
  echo "PASS: $name"
}

run_case \
  "claude style" \
  "claude" \
  '{"hook_event_name":"Stop","message":"Agent finished."}'

actual="$(SUPERSTAR_NOTIFY_DRY_RUN=1 CODEX_HOME=/tmp/codex "$HOOK" <<<'{"hook_event_name":"Stop","last_assistant_message":"All done."}')"
python3 - "$actual" <<'PY'
import json
import sys
event = json.loads(sys.argv[1])
assert event["type"] == "agent-ding"
assert event["style"] == "codex"
PY
echo "PASS: codex style"

run_case \
  "payload ignored" \
  "claude" \
  '{"hook_event_name":"SubagentStop","agent_type":"worker","last_assistant_message":"Slice completed and review passed.","transcript_path":"/tmp/ignored"}'
