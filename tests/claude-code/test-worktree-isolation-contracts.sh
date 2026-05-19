#!/usr/bin/env bash
# Static regression test for implementation worktree isolation contracts.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

fail() {
    echo "FAIL: $1" >&2
    exit 1
}

EXECUTING_PLANS="$ROOT/skills/executing-plans/SKILL.md"
SDD="$ROOT/skills/subagent-driven-development/SKILL.md"
EXTERNAL_REVIEW="$ROOT/skills/external-review/SKILL.md"
TASKLIST="$ROOT/skills/tasklist-discipline/SKILL.md"
PROJECT_SETUP="$ROOT/skills/project-setup/SKILL.md"

grep -q "first executable gate" "$EXECUTING_PLANS" \
    || fail "executing-plans must verify using-git-worktrees before implementation"

grep -q "one isolated worktree per active slice" "$SDD" \
    || fail "subagent-driven-development must require one worktree per active slice"

grep -q "unrelated dirty files" "$EXTERNAL_REVIEW" \
    || fail "external-review post-slice preflight must block unrelated dirty files"

grep -q "does not authorize implementing that work in the current slice worktree" "$TASKLIST" \
    || fail "tasklist-discipline must warn follow-up allocation is not implementation permission"

grep -q "Implementation worktree location" "$PROJECT_SETUP" \
    || fail "project-setup must audit the implementation worktree location"

grep -q "Do not create per-slice worktrees here" "$PROJECT_SETUP" \
    || fail "project-setup must leave per-slice worktree creation to using-git-worktrees"

echo "PASS: worktree isolation contract wording is present"
