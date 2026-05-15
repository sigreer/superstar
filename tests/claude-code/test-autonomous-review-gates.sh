#!/usr/bin/env bash
# Static regression test for autonomous spec/plan/slice review gates.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

fail() {
    echo "FAIL: $1" >&2
    exit 1
}

BRAINSTORMING="$ROOT/skills/brainstorming/SKILL.md"
WRITING_PLANS="$ROOT/skills/writing-plans/SKILL.md"
SDD="$ROOT/skills/subagent-driven-development/SKILL.md"

grep -q "External spec review" "$BRAINSTORMING" \
    || fail "brainstorming must route written specs to external review"

grep -q "Do not ask the user before implementation planning" "$BRAINSTORMING" \
    || fail "brainstorming must not pause for user review after spec save"

if grep -q "User Review Gate" "$BRAINSTORMING" || grep -q "User reviews written spec" "$BRAINSTORMING"; then
    fail "brainstorming still contains the old user spec-review gate"
fi

grep -q "whether it lives under" "$WRITING_PLANS" \
    || fail "writing-plans must review specs regardless of spec directory"

grep -q "Do not ask the user before this review unless blocked" "$WRITING_PLANS" \
    || fail "writing-plans must not pause before mandatory review gates"

grep -q "required slice/phase external-review gates" "$SDD" \
    || fail "SDD completion must include slice/phase external-review gates"

grep -q "plan's final close-out task ran" "$SDD" \
    || fail "SDD must cover the close-out-before-post-slice rationalization"

echo "PASS: autonomous review gate wording is present"
