#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOK="$ROOT/hooks/agent-finished"

run_case() {
  local name="$1"
  local expected="$2"
  local payload="$3"
  local actual

  actual="$(SUPERSTAR_NOTIFY_DRY_RUN=1 "$HOOK" <<<"$payload")"
  if [[ "$actual" != "$expected" ]]; then
    echo "FAIL: $name" >&2
    echo "expected: $expected" >&2
    echo "actual:   $actual" >&2
    exit 1
  fi
  echo "PASS: $name"
}

run_case \
  "spec phase" \
  "Spec complete for P11" \
  '{"hook_event_name":"Stop","message":"Spec complete for P11 after external review."}'

run_case \
  "plan slice" \
  "Plan complete for P11.S2" \
  '{"hook_event_name":"Stop","result":"Plan complete for P11.S2 and handoff reviewed."}'

run_case \
  "slice complete" \
  "Completed slice P11.S3" \
  '{"hook_event_name":"SubagentStop","summary":"Completed slice P11.S3 with post-slice review ready."}'

run_case \
  "questions" \
  "Questions for P11.S3" \
  '{"hook_event_name":"SubagentStop","text":"Questions for P11.S3: should this include docs?"}'

run_case \
  "generic task" \
  "Finished P11.S3.T2" \
  '{"hook_event_name":"SubagentStop","text":"Implemented P11.S3.T2 and left notes."}'

no_id="$(SUPERSTAR_NOTIFY_DRY_RUN=1 "$HOOK" <<<'{"hook_event_name":"Stop","last_assistant_message":"All done."}')"
if [[ -n "$no_id" ]]; then
  echo "FAIL: no milestone id should be silent" >&2
  echo "actual: $no_id" >&2
  exit 1
fi
echo "PASS: no milestone id"

run_case \
  "last assistant field" \
  "Completed slice P11.S4" \
  '{"hook_event_name":"SubagentStop","agent_type":"worker","last_assistant_message":"Slice P11.S4 completed and review passed.","transcript_path":"/tmp/ignored"}'
