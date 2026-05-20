#!/usr/bin/env bash
# Static regression test for global external-reviewer command guidance.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

fail() {
    echo "FAIL: $1" >&2
    exit 1
}

EXTERNAL_REVIEW="$ROOT/skills/external-review/SKILL.md"
PROJECT_SETUP="$ROOT/skills/project-setup/SKILL.md"
TASKLIST="$ROOT/skills/tasklist-discipline/SKILL.md"

grep -q "external-reviewer review" "$EXTERNAL_REVIEW" \
    || fail "external-review must document external-reviewer review"

grep -q "global canonical review-chain bridge command" "$EXTERNAL_REVIEW" \
    || fail "external-review must define external-reviewer as canonical"

if grep -q "python3 scripts/external-reviewer.py" "$EXTERNAL_REVIEW"; then
    fail "external-review still recommends repo-local bridge invocation"
fi

grep -q "external-reviewer --help" "$PROJECT_SETUP" \
    || fail "project-setup must audit global external-reviewer availability"

grep -q "legacy drift" "$PROJECT_SETUP" \
    || fail "project-setup must flag non-shim repo-local external-reviewer.py as legacy drift"

grep -q "external-reviewer-shim.py" "$PROJECT_SETUP" \
    || fail "project-setup must point at the compatibility shim template"

if grep -q "Copy from.*skills/external-review/scripts/external-reviewer.py" "$PROJECT_SETUP"; then
    fail "project-setup still says to copy the full bridge"
fi

if grep -q "vendors .scripts/external-reviewer.py" "$TASKLIST"; then
    fail "tasklist-discipline still says setup vendors the bridge"
fi

echo "PASS: global external-reviewer command guidance is present"
