# Review — 2026-05-18-p2-s3-skill-rewrite-and-hook.md (post-slice, round 1)

- Target: `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md`
- Request: `docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/r1-2026-05-18T1520-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: blocking — The slice is not in a clean post-slice state. `git status --short --untracked-files=all` shows the target plan, handoff prompt, plan-review artifacts, and post-slice review artifacts are all untracked, including `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md`. This is a completion-gate blocker because `P2.S3` already references that plan in [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:60), but the artifact is not committed.

F2 — Severity: blocking — `P2.S3` has not actually been closed. The tasklist still has `reviewer_chain: null` and `status: "in_progress"` at [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:63), while the post-slice `chain.json` is untracked and has empty `rounds`. The target plan also claims the entry is `ready` at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:11), which does not match repo state.

F3 — Severity: important — The rewritten `tasklist-discipline` skill teaches the wrong fully qualified form for cross-cutting IDs: [skills/tasklist-discipline/SKILL.md](/home/simon/Dev/sigreer/skills/superstar/skills/tasklist-discipline/SKILL.md:27) says `X4` fully qualifies to `P2.X4`. The spec models cross-cutting IDs as top-level `X*` items, e.g. [docs/specs/2026-05-17-P2-tasktool-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:140), and the new orphan validator also treats `x4` filenames as top-level `X4` at [tools/tasktool/validate.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/validate.py:147). This can mislead agents into producing IDs or filenames the CLI rejects.

F4 — Severity: important — The plan still records acceptance work as incomplete. All checkboxes remain open, including the `using-superstar` sanity pass at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:957) and the end-to-end smoke at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:977). The code commits exist, but the target document does not provide durable completion evidence.

2. Open questions / assumptions

I assume the plan, handoff, and reviewer artifacts are intended to be committed because they are referenced as slice evidence. If some reviewer output directories are intentionally local-only, that policy should be explicit and the tracked chain state should still be sufficient for `tasktool close`.

3. Suggested document edits

Update the plan with a completion evidence section: commit SHAs for `P2.S3.T1` through `T11`, the `using-superstar` no-op grep result, hook install confirmation, full test output, and smoke-test result. Correct the tasklist status line or remove it.

Fix `skills/tasklist-discipline/SKILL.md` so cross-cutting fully-qualified IDs are shown as `X4`, not `P2.X4`.

4. Verification gaps / commands

I ran:

`python -m pytest tools/tasktool/tests -q` → `174 passed in 8.26s`

`tasktool --project-root /home/simon/Dev/sigreer/skills/superstar validate --format json` → ok, no errors or warnings.

The Task 13 smoke succeeds under Bash, but the plan’s snippet fails under the repo’s default `zsh` because it uses Bash-only `${PHID,,}`. Either document `bash -lc` for that smoke or replace the lowercase conversion with a portable command.

5. Overall verdict: revise
1. Findings

F1 — Severity: blocking — The slice is not in a clean post-slice state. `git status --short --untracked-files=all` shows the target plan, handoff prompt, plan-review artifacts, and post-slice review artifacts are all untracked, including `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md`. This is a completion-gate blocker because `P2.S3` already references that plan in [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:60), but the artifact is not committed.

F2 — Severity: blocking — `P2.S3` has not actually been closed. The tasklist still has `reviewer_chain: null` and `status: "in_progress"` at [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:63), while the post-slice `chain.json` is untracked and has empty `rounds`. The target plan also claims the entry is `ready` at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:11), which does not match repo state.

F3 — Severity: important — The rewritten `tasklist-discipline` skill teaches the wrong fully qualified form for cross-cutting IDs: [skills/tasklist-discipline/SKILL.md](/home/simon/Dev/sigreer/skills/superstar/skills/tasklist-discipline/SKILL.md:27) says `X4` fully qualifies to `P2.X4`. The spec models cross-cutting IDs as top-level `X*` items, e.g. [docs/specs/2026-05-17-P2-tasktool-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:140), and the new orphan validator also treats `x4` filenames as top-level `X4` at [tools/tasktool/validate.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/validate.py:147). This can mislead agents into producing IDs or filenames the CLI rejects.

F4 — Severity: important — The plan still records acceptance work as incomplete. All checkboxes remain open, including the `using-superstar` sanity pass at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:957) and the end-to-end smoke at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:977). The code commits exist, but the target document does not provide durable completion evidence.

2. Open questions / assumptions

I assume the plan, handoff, and reviewer artifacts are intended to be committed because they are referenced as slice evidence. If some reviewer output directories are intentionally local-only, that policy should be explicit and the tracked chain state should still be sufficient for `tasktool close`.

3. Suggested document edits

Update the plan with a completion evidence section: commit SHAs for `P2.S3.T1` through `T11`, the `using-superstar` no-op grep result, hook install confirmation, full test output, and smoke-test result. Correct the tasklist status line or remove it.

Fix `skills/tasklist-discipline/SKILL.md` so cross-cutting fully-qualified IDs are shown as `X4`, not `P2.X4`.

4. Verification gaps / commands

I ran:

`python -m pytest tools/tasktool/tests -q` → `174 passed in 8.26s`

`tasktool --project-root /home/simon/Dev/sigreer/skills/superstar validate --format json` → ok, no errors or warnings.

The Task 13 smoke succeeds under Bash, but the plan’s snippet fails under the repo’s default `zsh` because it uses Bash-only `${PHID,,}`. Either document `bash -lc` for that smoke or replace the lowercase conversion with a portable command.

5. Overall verdict: revise

---

## Reviewer stderr (tail)

```text
="$(git diff --cached --name-only --diff-filter=ACMR)"

# 1. Block docs/TASKLIST.md
if printf '%s\n' "$STAGED" | grep -qx 'docs/TASKLIST.md'; then
  echo "pre-commit: docs/TASKLIST.md is staged but this project migrated to docs/tasklist.json." >&2
  echo "  Delete docs/TASKLIST.md or unstage it. Use tasktool to mutate docs/tasklist.json." >&2
  exit 1
fi

# 1b. Block staged deletion of docs/tasklist.json.
if git diff --cached --name-only --diff-filter=D | grep -qx 'docs/tasklist.json'; then
  echo "pre-commit: docs/tasklist.json is staged for deletion. A tasktool-managed repo must keep its canonical tracker." >&2
  echo "  Unstage the deletion (\`git restore --staged docs/tasklist.json\`) or use --no-verify with a written justification." >&2
  exit 1
fi

if git ls-files --cached --error-unmatch docs/tasklist.json >/dev/null 2>&1; then
  HAS_INDEX_TASKLIST=1
else
  HAS_INDEX_TASKLIST=0
fi

if [ "$HAS_INDEX_TASKLIST" -eq 1 ]; then
  TMP="$(mktemp -d 2>/dev/null || mktemp -d -t tasktool-precommit)"
  trap 'rm -rf "$TMP"' EXIT
  mkdir -p "$TMP/docs"
  git show :docs/tasklist.json > "$TMP/docs/tasklist.json"

  if printf '%s\n' "$STAGED" | grep -qx 'docs/tasklist.json'; then
    tasktool --project-root "$TMP" validate --strict-format --format text
  fi
  tasktool --project-root "$TMP" validate --format text

  ORPHAN_CANDIDATES="$(printf '%s\n' "$STAGED" | grep -E '^docs/(specs|plans)/[0-9]{4}-[0-9]{2}-[0-9]{2}-' || true)"
  if [ -n "$ORPHAN_CANDIDATES" ]; then
    for f in $ORPHAN_CANDIDATES; do
      mkdir -p "$TMP/$(dirname "$f")"
      git show ":$f" > "$TMP/$f" 2>/dev/null || true
    done
    # shellcheck disable=SC2086
    (cd "$TMP" && tasktool validate --check-orphans $ORPHAN_CANDIDATES --format text)
  fi
fi

exec
/usr/bin/zsh -lc "find docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice -maxdepth 2 -type f -print -exec sed -n '1,120p' {} \\;" in /home/simon/Dev/sigreer/skills/superstar
 succeeded in 0ms:
docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/r1-2026-05-18T1520-sweep1-request.md
```
