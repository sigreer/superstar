<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 2 of p2-s3-skill-rewrite-and-hook-P2-S3-post-slice.

In incremental mode:
- Verify whether prior findings are resolved per the resolution report below.
- Reuse the existing finding IDs (F1, F2, …). If a prior finding is resolved,
  mark it RESOLVED in your findings list with its original ID. If still
  unresolved, keep its ID.
- Only introduce new finding IDs for genuine regressions caused by the fix, or
  blocking issues clearly missed in earlier rounds. Do not reopen broad review
  unless prior fixes changed broad architecture.

## Review chain summary

| round | verdict | findings | blocking |
|---|---|---|---|
| 1 | revise | 4 | 1 |

## Prior-round findings

Source: merged findings from r1 (authoritative)

# Merged findings for r1

## Primary

# Review — 2026-05-18-p2-s3-skill-rewrite-and-hook.md (post-slice, round 1)

- Target: `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md`
- Request: `docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/r1-2026-05-18T1520-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: blocking — The slice is not in a clean, committable post-slice state. `git status --short --untracked-files=all` shows the target plan, handoff prompt, plan-review chain, and post-slice chain are all untracked. This is especially risky because `P2.S3` refs the plan at [docs/tasklist.json:60](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:60), but that referenced file is not tracked. Post-slice acceptance should not pass with unresolved untracked artifacts.

F2 — Severity: important — The target document’s state metadata is stale/inconsistent. The plan says `P2.S3` status is `ready` at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:11](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:11), but the actual tasklist has `reviewer_chain: null` and `status: "in_progress"` at [docs/tasklist.json:63](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:63). That makes the completion handoff ambiguous.

F3 — Severity: important — The plan still records acceptance work as incomplete. All checkboxes remain open, including the `using-superstar` sanity pass and end-to-end smoke at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:957](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:957) and [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:977](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:977). The code appears implemented, but the target document provides no durable evidence of which gates actually ran.

F4 — Severity: minor — The hook test covers raw edit plus `validate --normalise`, but not the literal `TASKTOOL_RAW=1` workflow called out in the plan’s file map and spec acceptance. See [tools/tasktool/tests/test_pre_commit_hook.py:83](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/tests/test_pre_commit_hook.py:83). Since `TASKTOOL_RAW` is not a hook bypass, this is mostly an acceptance-evidence gap.

2. Open questions / assumptions

I assume the plan/reviewer/handoff artifacts are intended to be committed if referenced by `docs/tasklist.json` or used as review evidence. If they are intentionally local-only, remove the tasklist ref or document that policy.

3. Suggested document edits

Update the plan with a short completion evidence section: commit SHAs for T1-T11, T12 no-op grep result, hook install confirmation, smoke-test result, and test command output. Also correct the line-11 tasklist status statement or remove it.

4. Verification gaps / commands

Already run:
`python -m pytest tools/tasktool/tests -q` → `174 passed in 8.24s`
`tasktool --project-root /home/simon/Dev/sigreer/skills/superstar validate --format json` → ok, no errors/warnings
`.git/hooks/pre-commit` matches `tools/tasktool/templates/pre-commit-tasktool`

Still needed before close:
`git status --short --untracked-files=all` should be clean except intentionally ignored local state.
Run or document the Task 13 smoke test.
Optionally add a test that sets `TASKTOOL_RAW=1` in the raw-edit normalise path.

5. Overall verdict: revise
1. Findings

F1 — Severity: blocking — The slice is not in a clean, committable post-slice state. `git status --short --untracked-files=all` shows the target plan, handoff prompt, plan-review chain, and post-slice chain are all untracked. This is especially risky because `P2.S3` refs the plan at [docs/tasklist.json:60](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:60), but that referenced file is not tracked. Post-slice acceptance should not pass with unresolved untracked artifacts.

F2 — Severity: important — The target document’s state metadata is stale/inconsistent. The plan says `P2.S3` status is `ready` at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:11](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:11), but the actual tasklist has `reviewer_chain: null` and `status: "in_progress"` at [docs/tasklist.json:63](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:63). That makes the completion handoff ambiguous.

F3 — Severity: important — The plan still records acceptance work as incomplete. All checkboxes remain open, including the `using-superstar` sanity pass and end-to-end smoke at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:957](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:957) and [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:977](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:977). The code appears implemented, but the target document provides no durable evidence of which gates actually ran.

F4 — Severity: minor — The hook test covers raw edit plus `validate --normalise`, but not the literal `TASKTOOL_RAW=1` workflow called out in the plan’s file map and spec acceptance. See [tools/tasktool/tests/test_pre_commit_hook.py:83](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/tests/test_pre_commit_hook.py:83). Since `TASKTOOL_RAW` is not a hook bypass, this is mostly an acceptance-evidence gap.

2. Open questions / assumptions

I assume the plan/reviewer/handoff artifacts are intended to be committed if referenced by `docs/tasklist.json` or used as review evidence. If they are intentionally local-only, remove the tasklist ref or document that policy.

3. Suggested document edits

Update the plan with a short completion evidence section: commit SHAs for T1-T11, T12 no-op grep result, hook install confirmation, smoke-test result, and test command output. Also correct the line-11 tasklist status statement or remove it.

4. Verification gaps / commands

Already run:
`python -m pytest tools/tasktool/tests -q` → `174 passed in 8.24s`
`tasktool --project-root /home/simon/Dev/sigreer/skills/superstar validate --format json` → ok, no errors/warnings
`.git/hooks/pre-commit` matches `tools/tasktool/templates/pre-commit-tasktool`

Still needed before close:
`git status --short --untracked-files=all` should be clean except intentionally ignored local state.
Run or document the Task 13 smoke test.
Optionally add a test that sets `TASKTOOL_RAW=1` in the raw-edit normalise path.

5. Overall verdict: revise

---

## Reviewer stderr (tail)

```text
g the `using-superstar` sanity pass and end-to-end smoke at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:957](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:957) and [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:977](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:977). The code appears implemented, but the target document provides no durable evidence of which gates actually ran.

F4 — Severity: minor — The hook test covers raw edit plus `validate --normalise`, but not the literal `TASKTOOL_RAW=1` workflow called out in the plan’s file map and spec acceptance. See [tools/tasktool/tests/test_pre_commit_hook.py:83](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/tests/test_pre_commit_hook.py:83). Since `TASKTOOL_RAW` is not a hook bypass, this is mostly an acceptance-evidence gap.

2. Open questions / assumptions

I assume the plan/reviewer/handoff artifacts are intended to be committed if referenced by `docs/tasklist.json` or used as review evidence. If they are intentionally local-only, remove the tasklist ref or document that policy.

3. Suggested document edits

Update the plan with a short completion evidence section: commit SHAs for T1-T11, T12 no-op grep result, hook install confirmation, smoke-test result, and test command output. Also correct the line-11 tasklist status statement or remove it.

4. Verification gaps / commands

Already run:
`python -m pytest tools/tasktool/tests -q` → `174 passed in 8.24s`
`tasktool --project-root /home/simon/Dev/sigreer/skills/superstar validate --format json` → ok, no errors/warnings
`.git/hooks/pre-commit` matches `tools/tasktool/templates/pre-commit-tasktool`

Still needed before close:
`git status --short --untracked-files=all` should be clean except intentionally ignored local state.
Run or document the Task 13 smoke test.
Optionally add a test that sets `TASKTOOL_RAW=1` in the raw-edit normalise path.

5. Overall verdict: revise
tokens used
65,858
```


## Sweep 1

# Review — 2026-05-18-p2-s3-skill-rewrite-and-hook.md (post-slice, round 1)

- Target: `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md`
- Request: `docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/r1-2026-05-18T1520-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

S1.F1 — Severity: blocking — The slice is not in a clean post-slice state. `git status --short --untracked-files=all` shows the target plan, handoff prompt, plan-review artifacts, and post-slice review artifacts are all untracked, including `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md`. This is a completion-gate blocker because `P2.S3` already references that plan in [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:60), but the artifact is not committed.

S1.F2 — Severity: blocking — `P2.S3` has not actually been closed. The tasklist still has `reviewer_chain: null` and `status: "in_progress"` at [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:63), while the post-slice `chain.json` is untracked and has empty `rounds`. The target plan also claims the entry is `ready` at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:11), which does not match repo state.

S1.F3 — Severity: important — The rewritten `tasklist-discipline` skill teaches the wrong fully qualified form for cross-cutting IDs: [skills/tasklist-discipline/SKILL.md](/home/simon/Dev/sigreer/skills/superstar/skills/tasklist-discipline/SKILL.md:27) says `X4` fully qualifies to `P2.X4`. The spec models cross-cutting IDs as top-level `X*` items, e.g. [docs/specs/2026-05-17-P2-tasktool-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:140), and the new orphan validator also treats `x4` filenames as top-level `X4` at [tools/tasktool/validate.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/validate.py:147). This can mislead agents into producing IDs or filenames the CLI rejects.

S1.F4 — Severity: important — The plan still records acceptance work as incomplete. All checkboxes remain open, including the `using-superstar` sanity pass at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:957) and the end-to-end smoke at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:977). The code commits exist, but the target document does not provide durable completion evidence.

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

S1.F1 — Severity: blocking — The slice is not in a clean post-slice state. `git status --short --untracked-files=all` shows the target plan, handoff prompt, plan-review artifacts, and post-slice review artifacts are all untracked, including `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md`. This is a completion-gate blocker because `P2.S3` already references that plan in [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:60), but the artifact is not committed.

S1.F2 — Severity: blocking — `P2.S3` has not actually been closed. The tasklist still has `reviewer_chain: null` and `status: "in_progress"` at [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:63), while the post-slice `chain.json` is untracked and has empty `rounds`. The target plan also claims the entry is `ready` at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:11), which does not match repo state.

S1.F3 — Severity: important — The rewritten `tasklist-discipline` skill teaches the wrong fully qualified form for cross-cutting IDs: [skills/tasklist-discipline/SKILL.md](/home/simon/Dev/sigreer/skills/superstar/skills/tasklist-discipline/SKILL.md:27) says `X4` fully qualifies to `P2.X4`. The spec models cross-cutting IDs as top-level `X*` items, e.g. [docs/specs/2026-05-17-P2-tasktool-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:140), and the new orphan validator also treats `x4` filenames as top-level `X4` at [tools/tasktool/validate.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/validate.py:147). This can mislead agents into producing IDs or filenames the CLI rejects.

S1.F4 — Severity: important — The plan still records acceptance work as incomplete. All checkboxes remain open, including the `using-superstar` sanity pass at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:957) and the end-to-end smoke at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:977). The code commits exist, but the target document does not provide durable completion evidence.

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



## Resolution report for prior round

# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md`, `docs/handoffs/2026-05-18-p2-s3-skill-rewrite-and-hook-prompt.md`, `docs/reviewer/p2-s3-skill-rewrite-and-hook-plan/`, `docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/`
- Verification: `git status --short --untracked-files=all` → clean after the post-slice resolution commit.

Notes:
All previously-untracked plan, handoff, and reviewer-chain artifacts are staged and committed alongside this resolution. The `docs/tasklist.json` `P2.S3.refs` entry now resolves to a tracked file.

## F2
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:11`
- Verification: line 11 now reads `(created 2026-05-18; current status set via tasktool during execution)`; no longer claims a hard-coded `status: ready`.

Notes:
The "Sweep" formulation of this finding additionally noted that the reviewer chain wasn't recorded on the tasklist row. The `reviewer_chain` field will be set by `tasktool close P2.S3` once the gate passes, which is the canonical way to attach the chain.

## F3 (primary)
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md` (all task checkboxes, plus a new "Completion evidence" appendix listing commit SHAs and verification commands).
- Verification: `grep -c '^- \[x\]' docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md` → 51 (all step checkboxes flipped).

Notes:
Added a `## Completion evidence` section mapping each task to its commit SHA (or the documented reason for no commit, in T4/T12/T13). The hook smoke test result is recorded.

## S1.F3 (sweep — cross-cutting ID fully-qualified form)
Status: fixed
Evidence:
- Files: `skills/tasklist-discipline/SKILL.md` (Conceptual model table row)
- Verification: row now reads `| Cross-cutting | X4 | X4 (top-level; not nested under a phase) |`. Matches the spec (§ cross-cutting are top-level X*) and the validator (`validate.py` treats `x4` filenames as top-level `X4`).

Notes:
The previous wording (`P2.X4`) would have misled agents into producing IDs and filenames the orphan validator rejects. Corrected.

## F4 (primary — TASKTOOL_RAW=1 evidence gap)
Status: deferred
Evidence:
- Files: `tools/tasktool/tests/test_pre_commit_hook.py::test_raw_edit_then_normalise_passes`
- Verification: the existing test exercises the documented recovery path (raw semantic edit + `validate --normalise` + commit succeeds). The literal `TASKTOOL_RAW=1` env var is editor-side scaffolding, not a hook behaviour — the hook never inspects it.

Notes:
The reviewer themselves rated this minor and noted "TASKTOOL_RAW is not a hook bypass". Recovery-path semantics are already covered by `test_raw_edit_then_normalise_passes`. Adding a test that merely runs an editor with the env var set would not exercise any hook code path. Deferring.


## Changes since prior round

Worktree status: clean

### git diff base..HEAD

diff --git a/docs/handoffs/2026-05-18-p2-s3-skill-rewrite-and-hook-prompt.md b/docs/handoffs/2026-05-18-p2-s3-skill-rewrite-and-hook-prompt.md
new file mode 100644
index 0000000..0d0e541
--- /dev/null
+++ b/docs/handoffs/2026-05-18-p2-s3-skill-rewrite-and-hook-prompt.md
@@ -0,0 +1,30 @@
+# Coordinator handoff — P2.S3 Skill rewrite & pre-commit hook
+
+You are the coordinator for implementing **P2.S3** of superstar at `/home/simon/Dev/sigreer/skills/superstar`.
+
+Your role is **strictly orchestration**. Use the `superstar:subagent-driven-development` skill with parallel agents where possible.
+
+## Inputs
+
+- tasktool entry: run `tasktool brief P2.S3` (or `PYTHONPATH=/home/simon/Dev/sigreer/skills/superstar/tools python3 -m tasktool brief P2.S3` if the shim is not on PATH yet).
+- Spec: [`docs/specs/2026-05-17-P2-tasktool-design.md`](docs/specs/2026-05-17-P2-tasktool-design.md)
+- Plan: [`docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md`](docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md)
+- Plan reviewer chain (passed `ready` at round 5): [`docs/reviewer/p2-s3-skill-rewrite-and-hook-plan/`](docs/reviewer/p2-s3-skill-rewrite-and-hook-plan/)
+- Post-slice reviewer chain folder (will be created on first review): `docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/`
+
+## Coordinator discipline (non-negotiable)
+
+- **Do not perform any fixes yourself** unless the fix is genuinely cheaper to implement than the process of delegating to a subagent. Tiebreak: delegate. The `tasktool brief` / `tasktool show` calls are coordinator-cheap; everything else is a subagent.
+- **Do not pollute your context.** Delegate investigations, file reads, and edits to subagents. Your context is for orchestration, not implementation detail.
+- **At the end of the slice**, invoke `superstar:external-review` with `--kind post-slice --work-id P2.S3 --file docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md --context docs/specs/2026-05-17-P2-tasktool-design.md --context docs/tasklist.json --prompt-transport stdin --review-depth thorough --emit json`.
+- **Do not perform reviewer-driven fixes yourself.** Pass each reviewer response to a fix subagent. Iterate until the verdict is `ready` or `ready with small edits`, or there is a genuine reason to escalate to the user.
+- **Close the slice via `tasktool close P2.S3`** — the CLI re-checks the reviewer chain and refuses on `revise`. The hook installed by Task 4 will also be in effect from that task onward; any reviewer-chain artifacts that get committed must satisfy it.
+- **At the end of the phase** (after the final slice closes — note P2 has only S1, S2, S3 currently; if no further slices are added, the phase closes when S3 closes), invoke `superstar:external-review` with `--kind post-phase` and then `tasktool archive-phase P2`. Same delegation rule.
+
+## Known parser caveat
+
+The plan-review chain for this slice's plan reached an explicit `Overall Verdict: ready` at round 5, but the JSON `merged_verdict`/`verdict` shows `None` because the reviewer wrapper duplicates its body in stdout and stderr, confusing the script's parser. P2.S2 hit and documented the same artifact. If the post-slice review hits it too, read the response body directly and use `--skip-review-gate` on `tasktool close` only after confirming the substantive verdict is unambiguous (record the bypass reason in the slice `notes` per spec §8.2). Do **not** routinely bypass the gate.
+
+## First action
+
+Read this file (the handoff prompt), run `tasktool brief P2.S3`, then read the spec and the plan. Then invoke `superstar:subagent-driven-development` and begin Task 1 of the plan.
diff --git a/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md b/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md
new file mode 100644
index 0000000..dbd9965
--- /dev/null
+++ b/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md
@@ -0,0 +1,1065 @@
+# P2.S3 — Skill rewrite & pre-commit hook Implementation Plan
+
+> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.
+
+**Goal:** Replace the markdown-era `tasklist-discipline` skill with a tasktool-centric version, install a per-project pre-commit hook that enforces canonical JSON / blocks orphans / blocks `TASKLIST.md` regressions, and update every sibling skill that still references `docs/TASKLIST.md`.
+
+**Architecture:** Tasktool already owns the data and the review gates (P2.S1, P2.S2). This slice moves the *prose* layer onto the same axis: the `tasklist-discipline` skill becomes a thin pointer to `tasktool` and the gating concepts; the pre-commit hook closes the in-session edit loophole (§8.1, §12 of the spec) by refusing non-canonical bytes, orphaned spec/plan filenames, and any commit that touches `docs/TASKLIST.md`. Sibling skills get surgical edits — every `docs/TASKLIST.md` reference becomes a `tasktool` invocation or a `docs/tasklist.json` reference.
+
+**Tech Stack:** Python 3 stdlib (`tasktool`), POSIX sh (pre-commit hook), markdown (skills).
+
+**TASKLIST entry:** `P2.S3` in `docs/tasklist.json` (created 2026-05-18; current status set via `tasktool` during execution).
+
+---
+
+## File map
+
+| Action | Path | Responsibility |
+|--------|------|----------------|
+| Modify | `tools/tasktool/validate.py` | Add `validate_no_orphans(repo_root, staged_specs, staged_plans)` — flags any spec/plan filename ID that has no matching TASKLIST row. |
+| Modify | `tools/tasktool/cli.py` | Add `validate --check-orphans <path>...` flag plumbing. |
+| Modify | `tools/tasktool/commands.py` | Wire `cmd_validate(check_orphans=…)` to call the new validator and merge findings into the existing text/json output. |
+| Create | `tools/tasktool/tests/test_validate_orphans.py` | Unit + CLI tests for the new orphan-scan flag. |
+| Create | `tools/tasktool/templates/pre-commit-tasktool` | POSIX sh hook template (per spec §8.1) — strict-format + full validate + orphan scan + TASKLIST.md block. |
+| Modify | `tools/tasktool/install.sh` | Add `install.sh --hook` mode that drops `.git/hooks/pre-commit` from the template, idempotent + `--force`. |
+| Create | `tools/tasktool/tests/test_pre_commit_hook.py` | Synthetic-repo hook tests: canonical commit passes; non-canonical bytes blocked; orphan staged spec blocked; staged `TASKLIST.md` blocked; `TASKTOOL_RAW=1` editor + `validate --normalise` round-trip passes. |
+| Rewrite | `skills/tasklist-discipline/SKILL.md` | Full rewrite around tasktool (per spec §9.1). |
+| Delete | `skills/tasklist-discipline/templates/TASKLIST.template.md` | Replaced by `tasktool init`. |
+| Modify | `skills/writing-plans/SKILL.md` | `docs/TASKLIST.md` → `docs/tasklist.json`; ID-existence check uses `tasktool show <id>`. |
+| Modify | `skills/writing-plans/handoff-prompt.template.md` | Replace TASKLIST.md link/instructions with `tasktool brief <id>` + `docs/tasklist.json`. |
+| Modify | `skills/brainstorming/SKILL.md` | Same swap; "create the row first" routes through `tasktool create`. |
+| Modify | `skills/external-review/SKILL.md` | Context column says `docs/tasklist.json` (or `tasktool render` output). |
+| Modify | `skills/subagent-driven-development/SKILL.md` | Slice/phase close steps call `tasktool close <id>` and `tasktool archive-phase <id>`; remove "flip in TASKLIST.md" prose. |
+| Modify | `skills/executing-plans/SKILL.md` | Same swap. |
+| Modify | `skills/project-setup/SKILL.md` | Audit table row 1 becomes `docs/tasklist.json` via `tasktool init`; row references the hook template; remove TASKLIST.md template reference. |
+| Modify | `skills/using-superstar/SKILL.md` | Cosmetic — none of the user-facing prose references `TASKLIST.md`; verify and no-op if clean. |
+
+---
+
+## Task 1: Orphan-aware validator
+
+**Files:**
+- Modify: `tools/tasktool/validate.py`
+- Modify: `tools/tasktool/cli.py:103-105`
+- Modify: `tools/tasktool/commands.py` (`cmd_validate`)
+- Test: `tools/tasktool/tests/test_validate_orphans.py`
+
+- [x] **Step 1: Write the failing test**
+
+```python
+# tools/tasktool/tests/test_validate_orphans.py
+import json, subprocess, sys
+from pathlib import Path
+
+TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
+
+def _run(root, *args):
+    return subprocess.run(
+        [sys.executable, str(TOOL), "--project-root", str(root), *args],
+        capture_output=True, text=True,
+    )
+
+def _seed(tmp_path):
+    (tmp_path / "docs").mkdir()
+    (tmp_path / "docs" / "specs").mkdir()
+    (tmp_path / "docs" / "plans").mkdir()
+    _run(tmp_path, "init", "--project", "demo")
+    pid = _run(tmp_path, "create", "phase", "--title", "Phase one").stdout.strip()
+    sid = _run(tmp_path, "create", "slice", pid, "--title", "Slice one").stdout.strip()
+    return pid, sid
+
+def test_orphan_spec_filename_is_flagged(tmp_path):
+    pid, sid = _seed(tmp_path)
+    orphan = tmp_path / "docs" / "specs" / "2026-05-18-P99-orphan-design.md"
+    orphan.write_text("# orphan\n")
+    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(orphan))
+    assert r.returncode == 1, r.stdout + r.stderr
+    payload = json.loads(r.stdout)
+    assert any("P99" in e for e in payload["errors"])
+
+def test_known_id_filename_passes(tmp_path):
+    pid, sid = _seed(tmp_path)
+    known = tmp_path / "docs" / "plans" / f"2026-05-18-{pid.lower()}-{sid.lower()}-thing.md"
+    known.write_text("# plan\n")
+    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(known))
+    assert r.returncode == 0, r.stdout + r.stderr
+```
+
+- [x] **Step 2: Run test to verify it fails**
+
+Run: `python -m pytest tools/tasktool/tests/test_validate_orphans.py -v`
+Expected: FAIL — `--check-orphans` is not a known flag (argparse error / exit 2).
+
+- [x] **Step 3: Add the validator function**
+
+The existing project filename convention is **dash-separated** (`2026-05-18-p2-s3-…`), not dot-separated. The regex and lookup must reflect that. In `tools/tasktool/validate.py`, add:
+
+```python
+import re
+from pathlib import Path
+
+# Matches dash-separated IDs at the start of plan/spec filenames. Two forms:
+#   Phase-rooted:    2026-05-18-p2-… | p2-s3-… | p2-s3a-… | p2-s3-t1-…
+#   Cross-cutting:   2026-05-18-x4-…
+# Note: cross-cutting IDs are top-level in the data model (e.g. `X4`, not `P2.X4`).
+# A filename of the form `p2-x4-…` is treated as "phase P2, slice/cross child X4 *under*
+# P2" only if such a row exists; otherwise it's flagged. In practice cross filenames
+# should use the top-level form.
+_FILENAME_ID_RE = re.compile(
+    r"^\d{4}-\d{2}-\d{2}-"
+    r"(?:(?P<cross>[Xx]\d+)"
+    r"|(?P<phase>[Pp]\d+)"
+      r"(?:-(?P<child>[SsXx]\d+[a-z]?))?"
+      r"(?:-(?P<task>[Tt]\d+))?"
+    r")-",
+)
+
+def _normalise_id(*, cross: str | None, phase: str | None,
+                  child: str | None, task: str | None) -> str:
+    if cross:
+        return cross.upper()
+    assert phase is not None
+    parts = [phase.upper()]
+    if child:
+        parts.append(child.upper())
+    if task:
+        parts.append(task.upper())
+    return ".".join(parts)
+
+def collect_known_ids(p) -> set[str]:
+    """Return the set of *fully-qualified* IDs that exist in this project.
+
+    Short forms are deliberately NOT included — orphan checking requires exact
+    fully-qualified matches (e.g. `P99.S1` must not pass merely because some
+    other phase has an `S1`).
+    """
+    ids: set[str] = set()
+    for ph in p.phases:
+        ids.add(ph.id)
+        for sl in ph.slices:
+            ids.add(f"{ph.id}.{sl.id}")
+            for t in sl.tasks:
+                ids.add(f"{ph.id}.{sl.id}.{t.id}")
+    for ph in getattr(p, "archived_phases", []) or []:
+        ids.add(ph.id if hasattr(ph, "id") else ph["id"])
+    for x in p.cross_cutting:
+        ids.add(x.id)  # Cross-cutting IDs are top-level (e.g. "X4").
+    return ids
+
+def validate_orphan_filenames(p, paths) -> list[str]:
+    known = collect_known_ids(p)
+    findings: list[str] = []
+    for path in paths:
+        name = Path(path).name
+        m = _FILENAME_ID_RE.match(name)
+        if not m:
+            continue
+        fq = _normalise_id(
+            cross=m.group("cross"),
+            phase=m.group("phase"),
+            child=m.group("child"),
+            task=m.group("task"),
+        )
+        if fq in known:
+            continue
+        findings.append(
+            f"{path}: filename references ID {fq} but no matching row in tasklist.json"
+        )
+    return findings
+```
+
+Extend the orphans test from Step 1 with a wrong-phase regression case:
+
+```python
+def test_cross_cutting_top_level_filename_passes(tmp_path):
+    """`2026-05-18-x4-…` resolves to top-level X4 and passes when X4 exists."""
+    _seed(tmp_path)
+    cid = _run(tmp_path, "create", "cross", "--title", "C4").stdout.strip()  # X1 → X4 depending on seed
+    f = tmp_path / "docs" / "specs" / f"2026-05-18-{cid.lower()}-design.md"
+    f.write_text("# cross spec\n")
+    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(f))
+    assert r.returncode == 0, r.stdout + r.stderr
+
+def test_cross_cutting_unknown_top_level_is_flagged(tmp_path):
+    _seed(tmp_path)
+    f = tmp_path / "docs" / "specs" / "2026-05-18-x99-design.md"
+    f.write_text("# nope\n")
+    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(f))
+    assert r.returncode == 1, r.stdout + r.stderr
+    payload = json.loads(r.stdout)
+    assert any("X99" in e for e in payload["errors"])
+
+def test_wrong_phase_qualified_id_is_flagged(tmp_path):
+    """`P99-S1-…` must NOT pass merely because some other phase has an `S1`."""
+    _seed(tmp_path)  # creates P1.S1
+    orphan = tmp_path / "docs" / "plans" / "2026-05-18-p99-s1-thing.md"
+    orphan.write_text("# wrong-phase\n")
+    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(orphan))
+    assert r.returncode == 1, r.stdout + r.stderr
+    payload = json.loads(r.stdout)
+    assert any("P99.S1" in e for e in payload["errors"])
+```
+
+- [x] **Step 4: Plumb the CLI flag**
+
+The existing `cmd_validate` contract is `(format=…, strict_format=…, normalise=…) -> tuple[int, str]` and the CLI writes the returned text — preserve it. The current JSON shape is `{"ok", "errors", "warnings"}` — extend it by appending orphan findings to `errors`.
+
+In `tools/tasktool/cli.py` (where `p_validate` is built):
+
+```python
+p_validate = sub.add_parser("validate")
+p_validate.add_argument("--format", choices=["text", "json"], default="text")
+p_validate.add_argument("--strict-format", action="store_true")
+p_validate.add_argument("--normalise", action="store_true")
+p_validate.add_argument("--check-orphans", nargs="*", default=None,
+                        help="Spec/plan filepaths to check against tasklist.json IDs.")
+```
+
+In the `args.cmd == "validate"` branch, preserve the existing `(rc, text)` write-through:
+
+```python
+elif args.cmd == "validate":
+    rc, text = commands.cmd_validate(
+        repo_root=root, format=args.format,
+        strict_format=args.strict_format, normalise=args.normalise,
+        check_orphans=args.check_orphans,
+    )
+    sys.stdout.write(text)
+    return rc
+```
+
+In `tools/tasktool/commands.py`, extend the existing `cmd_validate` (keep the `format=` kwarg name; return `(rc, text)`). After loading `project`, if `check_orphans` is provided run `validate_orphan_filenames(project, check_orphans)` and append each finding to the `errors` list (so the JSON shape stays `{"ok", "errors", "warnings"}` and the text mode prints them through the same loop). Tests assert against `payload["errors"]`, not `findings` — match the existing schema.
+
+- [x] **Step 5: Run test to verify it passes**
+
+Run: `python -m pytest tools/tasktool/tests/test_validate_orphans.py -v`
+Expected: PASS (both tests).
+
+- [x] **Step 6: Re-run the full tasktool suite**
+
+Run: `python -m pytest tools/tasktool/tests -q`
+Expected: PASS (no regressions).
+
+- [x] **Step 7: Commit**
+
+```bash
+git add tools/tasktool/validate.py tools/tasktool/cli.py tools/tasktool/commands.py tools/tasktool/tests/test_validate_orphans.py
+git commit -m "P2.S3.T1: tasktool validate --check-orphans"
+```
+
+---
+
+## Task 2: Pre-commit hook template
+
+**Files:**
+- Create: `tools/tasktool/templates/pre-commit-tasktool`
+- Test: covered by Task 3.
+
+The hook MUST validate **staged** content (the index), not the working tree — a clean worktree with stale staged bytes would otherwise sneak past `tasktool validate`. The strategy: materialise the staged blob into a temporary project root via `git checkout-index --prefix=`, then run `tasktool --project-root <tempdir>` against that copy. Orphan filename checks use `git diff --cached --name-only --diff-filter=ACMR` directly (filename-only, not content).
+
+- [x] **Step 1: Write the hook**
+
+Write `tools/tasktool/templates/pre-commit-tasktool` (mode 0755):
+
+```sh
+#!/usr/bin/env sh
+# tasktool-pre-commit-hook v1
+# Installed by `tools/tasktool/install.sh --hook`.
+# Validates the STAGED content (the index), not the working tree, so a clean
+# worktree with stale staged bytes cannot sneak past.
+#
+# Enforces:
+#   1. docs/TASKLIST.md must not be staged (project migrated to docs/tasklist.json).
+#   2. Staged docs/tasklist.json must be canonical (tasktool validate --strict-format).
+#   3. Staged docs/tasklist.json must pass full validation.
+#   4. Staged spec/plan filenames must reference an ID present in the staged tasklist.json.
+# Bypass for genuine emergencies: `git commit --no-verify` and document the reason.
+set -e
+
+STAGED="$(git diff --cached --name-only --diff-filter=ACMR)"
+
+# 1. Block docs/TASKLIST.md
+if printf '%s\n' "$STAGED" | grep -qx 'docs/TASKLIST.md'; then
+  echo "pre-commit: docs/TASKLIST.md is staged but this project migrated to docs/tasklist.json." >&2
+  echo "  Delete docs/TASKLIST.md or unstage it. Use tasktool to mutate docs/tasklist.json." >&2
+  exit 1
+fi
+
+# 1b. Block staged deletion of docs/tasklist.json — a tasktool-managed repo
+# must keep its canonical tracker.
+if git diff --cached --name-only --diff-filter=D | grep -qx 'docs/tasklist.json'; then
+  echo "pre-commit: docs/tasklist.json is staged for deletion. A tasktool-managed repo must keep its canonical tracker." >&2
+  echo "  Unstage the deletion (\`git restore --staged docs/tasklist.json\`) or use --no-verify with a written justification." >&2
+  exit 1
+fi
+
+# Determine whether docs/tasklist.json exists in the index.
+if git ls-files --cached --error-unmatch docs/tasklist.json >/dev/null 2>&1; then
+  HAS_INDEX_TASKLIST=1
+else
+  HAS_INDEX_TASKLIST=0
+fi
+
+if [ "$HAS_INDEX_TASKLIST" -eq 1 ]; then
+  # Materialise the staged blob into a temp project root.
+  TMP="$(mktemp -d 2>/dev/null || mktemp -d -t tasktool-precommit)"
+  trap 'rm -rf "$TMP"' EXIT
+  mkdir -p "$TMP/docs"
+  git show :docs/tasklist.json > "$TMP/docs/tasklist.json"
+
+  # 2 + 3. Validate the staged content. Strict-format only when tasklist.json
+  # is itself in the staged change set (the file is canonical at rest anyway,
+  # but we surface the canonical-format failure with the right message).
+  if printf '%s\n' "$STAGED" | grep -qx 'docs/tasklist.json'; then
+    tasktool --project-root "$TMP" validate --strict-format --format text
+  fi
+  tasktool --project-root "$TMP" validate --format text
+
+  # 4. Orphan scan over staged spec/plan filenames (filename-only, evaluated
+  # against the staged tasklist.json). Materialise staged specs/plans into
+  # $TMP so paths exist relative to --project-root.
+  ORPHAN_CANDIDATES="$(printf '%s\n' "$STAGED" | grep -E '^docs/(specs|plans)/[0-9]{4}-[0-9]{2}-[0-9]{2}-' || true)"
+  if [ -n "$ORPHAN_CANDIDATES" ]; then
+    for f in $ORPHAN_CANDIDATES; do
+      mkdir -p "$TMP/$(dirname "$f")"
+      git show ":$f" > "$TMP/$f" 2>/dev/null || true
+    done
+    # shellcheck disable=SC2086
+    (cd "$TMP" && tasktool validate --check-orphans $ORPHAN_CANDIDATES --format text)
+  fi
+fi
+```
+
+- [x] **Step 2: Commit the template**
+
+```bash
+chmod +x tools/tasktool/templates/pre-commit-tasktool
+git add tools/tasktool/templates/pre-commit-tasktool
+git commit -m "P2.S3.T2: pre-commit hook template (index-aware)"
+```
+
+---
+
+## Task 3: Hook installer + tests
+
+**Files:**
+- Modify: `tools/tasktool/install.sh`
+- Test: `tools/tasktool/tests/test_pre_commit_hook.py`
+
+- [x] **Step 1: Add `--hook` mode to install.sh**
+
+The existing `tools/tasktool/install.sh` is Bash (`#!/usr/bin/env bash`, `set -euo pipefail`, `${BASH_SOURCE[0]}`, `[[ … ]]`). The new `--hook` branch must run **before** the shim-install logic (which treats `$1` as a `--force` toggle), and must use Bash. All invocations from tests, docs, and the smoke task use `bash`, not `sh`.
+
+In `tools/tasktool/install.sh`, insert the `--hook` dispatch immediately after the `set -euo pipefail` line and before `SCRIPT_DIR=`:
+
+```bash
+# --- hook installer (must precede shim-install logic) ---------------------
+if [[ "${1:-}" == "--hook" ]]; then
+  shift
+  FORCE_HOOK=0
+  if [[ "${1:-}" == "--force" ]]; then FORCE_HOOK=1; shift; fi
+  REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
+  if [[ -z "$REPO_ROOT" ]]; then
+    echo "install.sh --hook: must be run inside a git working tree" >&2
+    exit 1
+  fi
+  HOOK_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/templates/pre-commit-tasktool"
+  HOOK_DEST="$REPO_ROOT/.git/hooks/pre-commit"
+  if [[ -f "$HOOK_DEST" && "$FORCE_HOOK" -ne 1 ]]; then
+    if ! grep -q 'tasktool-pre-commit-hook' "$HOOK_DEST" 2>/dev/null; then
+      echo "install.sh --hook: $HOOK_DEST exists and is not a tasktool hook. Re-run with --force to overwrite." >&2
+      exit 1
+    fi
+  fi
+  install -m 0755 "$HOOK_SRC" "$HOOK_DEST"
+  echo "Installed $HOOK_DEST"
+  exit 0
+fi
+# --------------------------------------------------------------------------
+```
+
+- [x] **Step 2: Write the failing test**
+
+```python
+# tools/tasktool/tests/test_pre_commit_hook.py
+import os, subprocess, sys, shutil, textwrap
+from pathlib import Path
+
+REPO = Path(__file__).resolve().parents[3]
+TOOL = REPO / "tools" / "tasktool" / "__main__.py"
+INSTALL = REPO / "tools" / "tasktool" / "install.sh"
+
+def _git(repo, *args, check=True, env=None):
+    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=check, env=env)
+
+def _tasktool(repo, *args, env=None):
+    return subprocess.run([sys.executable, str(TOOL), "--project-root", str(repo), *args],
+                          capture_output=True, text=True, env=env)
+
+def _seed_repo(tmp_path):
+    repo = tmp_path / "r"
+    repo.mkdir()
+    _git(repo, "init", "-q", "-b", "main")
+    _git(repo, "config", "user.email", "t@example.com")
+    _git(repo, "config", "user.name", "t")
+    (repo / "docs").mkdir()
+    (repo / "docs" / "specs").mkdir()
+    (repo / "docs" / "plans").mkdir()
+    _tasktool(repo, "init", "--project", "demo")
+    # Make `tasktool` callable from the hook's PATH:
+    bin_dir = tmp_path / "bin"
+    bin_dir.mkdir()
+    (bin_dir / "tasktool").write_text(f"#!/usr/bin/env sh\nexec {sys.executable} {TOOL} \"$@\"\n")
+    os.chmod(bin_dir / "tasktool", 0o755)
+    env = os.environ.copy()
+    env["PATH"] = f"{bin_dir}:{env['PATH']}"
+    # Install the hook (install.sh is bash):
+    subprocess.run(["bash", str(INSTALL), "--hook"], cwd=repo, check=True, env=env)
+    return repo, env
+
+def test_canonical_commit_passes(tmp_path):
+    repo, env = _seed_repo(tmp_path)
+    _git(repo, "add", "docs/tasklist.json", env=env)
+    r = _git(repo, "commit", "-m", "init", check=False, env=env)
+    assert r.returncode == 0, r.stdout + r.stderr
+
+def test_non_canonical_bytes_rejected(tmp_path):
+    repo, env = _seed_repo(tmp_path)
+    _git(repo, "add", "docs/tasklist.json", env=env)
+    _git(repo, "commit", "-m", "init", env=env)
+    # Append a stray newline → non-canonical.
+    with open(repo / "docs" / "tasklist.json", "a") as f:
+        f.write("\n")
+    _git(repo, "add", "docs/tasklist.json", env=env)
+    r = _git(repo, "commit", "-m", "tamper", check=False, env=env)
+    assert r.returncode != 0
+    assert "canonical" in (r.stdout + r.stderr).lower()
+
+def test_orphan_spec_filename_rejected(tmp_path):
+    repo, env = _seed_repo(tmp_path)
+    _git(repo, "add", "docs/tasklist.json", env=env)
+    _git(repo, "commit", "-m", "init", env=env)
+    orphan = repo / "docs" / "specs" / "2026-05-18-P99-orphan-design.md"
+    orphan.write_text("# orphan\n")
+    _git(repo, "add", str(orphan.relative_to(repo)), env=env)
+    r = _git(repo, "commit", "-m", "orphan", check=False, env=env)
+    assert r.returncode != 0
+    assert "P99" in (r.stdout + r.stderr)
+
+def test_tasklist_md_rejected(tmp_path):
+    repo, env = _seed_repo(tmp_path)
+    _git(repo, "add", "docs/tasklist.json", env=env)
+    _git(repo, "commit", "-m", "init", env=env)
+    legacy = repo / "docs" / "TASKLIST.md"
+    legacy.write_text("# legacy\n")
+    _git(repo, "add", "docs/TASKLIST.md", env=env)
+    r = _git(repo, "commit", "-m", "legacy", check=False, env=env)
+    assert r.returncode != 0
+    assert "TASKLIST.md" in (r.stdout + r.stderr)
+
+def test_raw_edit_then_normalise_passes(tmp_path):
+    repo, env = _seed_repo(tmp_path)
+    _git(repo, "add", "docs/tasklist.json", env=env)
+    _git(repo, "commit", "-m", "init", env=env)
+    p = repo / "docs" / "tasklist.json"
+    with open(p, "a") as f:
+        f.write("\n")
+    _tasktool(repo, "validate", "--normalise", env=env)
+    _git(repo, "add", "docs/tasklist.json", env=env)
+    r = _git(repo, "commit", "-m", "normalised", check=False, env=env)
+    assert r.returncode == 0, r.stdout + r.stderr
+
+def test_staged_bad_normalised_worktree_is_rejected(tmp_path):
+    """Stage non-canonical bytes, then normalise the worktree without re-staging.
+    The hook MUST reject because the index is what gets committed."""
+    repo, env = _seed_repo(tmp_path)
+    _git(repo, "add", "docs/tasklist.json", env=env)
+    _git(repo, "commit", "-m", "init", env=env)
+    p = repo / "docs" / "tasklist.json"
+    with open(p, "a") as f:
+        f.write("\n")
+    # Stage the bad bytes.
+    _git(repo, "add", "docs/tasklist.json", env=env)
+    # Now normalise the WORKTREE only (do not re-add).
+    _tasktool(repo, "validate", "--normalise", env=env)
+    r = _git(repo, "commit", "-m", "staged-bad-worktree-clean", check=False, env=env)
+    assert r.returncode != 0, (
+        "hook must validate the index, not the worktree, but commit succeeded: "
+        + r.stdout + r.stderr
+    )
+
+def test_tasklist_json_deletion_rejected(tmp_path):
+    """Staging the deletion of docs/tasklist.json must be refused."""
+    repo, env = _seed_repo(tmp_path)
+    _git(repo, "add", "docs/tasklist.json", env=env)
+    _git(repo, "commit", "-m", "init", env=env)
+    _git(repo, "rm", "docs/tasklist.json", env=env)
+    r = _git(repo, "commit", "-m", "delete tracker", check=False, env=env)
+    assert r.returncode != 0, "hook must refuse tasklist.json deletion: " + r.stdout + r.stderr
+    assert "deletion" in (r.stdout + r.stderr).lower() or "delete" in (r.stdout + r.stderr).lower()
+
+def test_hook_install_is_idempotent(tmp_path):
+    """Running `install.sh --hook` twice without --force must succeed both times."""
+    repo, env = _seed_repo(tmp_path)
+    # First install happened in _seed_repo. Run again:
+    r = subprocess.run(["bash", str(INSTALL), "--hook"], cwd=repo, capture_output=True, text=True, env=env)
+    assert r.returncode == 0, r.stdout + r.stderr
+
+def test_staged_good_dirty_worktree_passes(tmp_path):
+    """Stage canonical bytes, then dirty the worktree without re-staging.
+    The hook MUST pass — the index is canonical, the worktree dirt is irrelevant."""
+    repo, env = _seed_repo(tmp_path)
+    _git(repo, "add", "docs/tasklist.json", env=env)
+    _git(repo, "commit", "-m", "init", env=env)
+    # Stage a clean tasktool-mediated change.
+    _tasktool(repo, "create", "phase", "--title", "P", env=env)
+    _git(repo, "add", "docs/tasklist.json", env=env)
+    # Now dirty the worktree post-stage.
+    p = repo / "docs" / "tasklist.json"
+    with open(p, "a") as f:
+        f.write("\n")
+    r = _git(repo, "commit", "-m", "staged-good-dirty-worktree", check=False, env=env)
+    assert r.returncode == 0, (
+        "hook must accept canonical index regardless of worktree dirt: "
+        + r.stdout + r.stderr
+    )
+```
+
+- [x] **Step 3: Run test to verify it fails**
+
+Run: `python -m pytest tools/tasktool/tests/test_pre_commit_hook.py -v`
+Expected: FAIL — `install.sh --hook` does not yet branch correctly, or hook prerequisites missing.
+
+- [x] **Step 4: Iterate on install.sh + hook until tests pass**
+
+Run the test, read the failure, fix the hook or installer, repeat. Do not adjust the *tests* to match — adjust the implementation.
+
+- [x] **Step 5: Run the full suite**
+
+Run: `python -m pytest tools/tasktool/tests -q`
+Expected: PASS (all hook tests + all earlier tests).
+
+- [x] **Step 6: Commit**
+
+```bash
+git add tools/tasktool/install.sh tools/tasktool/tests/test_pre_commit_hook.py
+git commit -m "P2.S3.T3: install.sh --hook + pre-commit hook tests"
+```
+
+---
+
+## Task 4: Install the hook in this repo
+
+**Files:**
+- Create: `.git/hooks/pre-commit` (out-of-tree; not committed).
+
+- [x] **Step 1: Run the installer**
+
+```bash
+bash tools/tasktool/install.sh --hook
+```
+
+Expected stdout: `Installed /home/simon/Dev/sigreer/skills/superstar/.git/hooks/pre-commit`
+
+- [x] **Step 2: Smoke test the hook on the live repo**
+
+```bash
+echo "" >> docs/tasklist.json
+git add docs/tasklist.json
+git commit -m "should fail" || echo "rejected as expected"
+git restore --staged docs/tasklist.json
+git checkout -- docs/tasklist.json
+```
+
+Expected: commit refused with a canonical-format error; restore returns the file to clean state.
+
+- [x] **Step 3: No commit for this task** — the hook installation is operator-side state, not tree state.
+
+---
+
+## Task 5: Rewrite `tasklist-discipline` SKILL.md
+
+**Files:**
+- Rewrite: `skills/tasklist-discipline/SKILL.md`
+- Delete: `skills/tasklist-discipline/templates/TASKLIST.template.md`
+
+- [x] **Step 1: Replace the skill body**
+
+Overwrite `skills/tasklist-discipline/SKILL.md` with:
+
+````markdown
+---
+name: tasklist-discipline
+description: Use whenever planning, closing slices/phases, or referencing work items in a project that uses docs/tasklist.json. Teaches the tasktool CLI surface and the gating concepts; the CLI enforces the rules.
+---
+
+# TASKLIST Discipline
+
+A `docs/tasklist.json` file is the canonical, top-level tracker for the project. It groups work into **phases**, **slices**, **tasks**, and **cross-cutting** items, each with a stable, never-renumbered ID. All mutations flow through `tasktool`; a pre-commit hook refuses non-canonical bytes, orphaned spec/plan filenames, and any commit that touches the legacy `docs/TASKLIST.md`.
+
+**Announce at start:** "I'm using the tasklist-discipline skill to update docs/tasklist.json via tasktool."
+
+## When to use
+
+- About to plan or write a new spec → allocate an ID with `tasktool create phase|slice|task|cross …` **before** the spec file lands. The TASKLIST row is the allocation; the spec/plan/reviewer-chain filenames are downstream.
+- About to close a slice → `tasktool close <slice-id>`. The CLI enforces the post-slice external-review gate.
+- About to close a phase → `tasktool archive-phase <phase-id>`. The CLI enforces the post-phase gate and writes the archive note.
+- Entering a slice → `tasktool brief <slice-id>` instead of reading the JSON.
+- Onboarding a project — `[[project-setup]]` runs `tasktool init` and installs the hook.
+
+## Conceptual model
+
+| Scope | Short form | Fully-qualified |
+|-------|-----------|-----------------|
+| Phase | `P2` | `P2` |
+| Slice | `S1` (follow-up: `S5a`) | `P2.S1` (`P2.S5a`) |
+| Task | `T3` | `P2.S5.T3` |
+| Cross-cutting | `X4` | `P2.X4` |
+
+IDs are assigned at birth and **never renumbered**. The `tasktool create` family does orphan-aware allocation (`max+1` across `docs/tasklist.json`, `docs/specs/`, `docs/plans/`, `docs/reviewer/`) and prints the new ID.
+
+Status enum: `ready | in_progress | blocked | done`. Only slices may take `blocked` (and only via `tasktool block <slice-id> --on …`). Emoji are a render concern; `tasktool render` and `tasktool brief` handle that. `done` requires `closed`; the CLI stamps it.
+
+## Daily commands
+
+```sh
+tasktool brief <id>            # start-of-work primer for slice or phase
+tasktool show <id>             # full detail
+tasktool list --open           # everything ready / in_progress / blocked
+tasktool create slice <phase-id> --title "…"
+tasktool set <id> --status in_progress
+tasktool note <id> --append "…"
+tasktool ref <id> --add path/to/artifact
+tasktool block <slice-id> --on P2.S5
+tasktool close <slice-id>      # enforces post-slice review gate
+tasktool archive-phase <phase-id>  # enforces post-phase review gate
+tasktool validate              # full validation
+```
+
+Run `tasktool --help` (or `tasktool <cmd> --help`) for the full surface.
+
+## Gating concepts (why the CLI refuses you)
+
+- **Post-slice external review.** `tasktool close <slice-id>` reads `chain.json` from the slice's reviewer chain folder (`docs/reviewer/<slug>-post-slice/` by default; override with `--reviewer-chain`). It refuses unless the latest round's verdict ∈ {`ready`, `ready with small edits`}. Per-task internal reviews do not satisfy this gate.
+- **Post-phase external review.** `tasktool archive-phase <phase-id>` refuses until every slice is `done` *and* the phase's post-phase chain returns `ready` / `ready with small edits`.
+- **`--skip-review-gate`** exists for emergencies and is recorded in the slice/phase `notes` with a timestamp. Use it only when the operator has explicitly chosen to bypass.
+
+See `[[external-review]]` for how to drive the reviewer.
+
+## Hand-edits are an emergency path, not a workflow
+
+If a raw edit is genuinely needed:
+
+```sh
+TASKTOOL_RAW=1 $EDITOR docs/tasklist.json
+tasktool validate --normalise
+```
+
+`--normalise` re-serialises the file through the canonical formatter so the pre-commit hook accepts it. There is no `tasktool edit --raw` subcommand by design — the friction keeps agents on the sanctioned commands.
+
+## New work mid-slice
+
+| Scenario | Action |
+|----------|--------|
+| Incidental fix in the same area | `tasktool create task <slice-id> --title …` |
+| Real unit of work | `tasktool create slice <phase-id> --title …` (or `--follow-up <slice-id>` for a letter-suffix) |
+| Bug surfaced by review | Inline task if cheap; follow-up slice if it deserves its own scope. |
+| Cross-cutting, unscheduled | `tasktool create cross --title …` |
+
+## Referencing items in artifacts
+
+- Specs, plans, reviewer chain folders: fully-qualified ID at first mention (`P9.S3a`), short form afterwards.
+- Plan and spec filenames embed the ID: `YYYY-MM-DD-<id>-<slug>(-design).md`. The pre-commit hook rejects filenames whose ID has no `tasklist.json` row.
+- Commit messages may use either form; prefer fully-qualified for cross-phase commits.
+
+## Red flags
+
+| Thought | Reality |
+|---------|---------|
+| "I'll just edit `docs/tasklist.json` by hand quickly." | The hook will refuse non-canonical bytes; `tasktool` is faster than fighting the hook. Use the CLI. |
+| "I'll mark the slice `done` with `set` instead of `close` to skip the review gate." | `tasktool set --status done` routes through the same gate as `close`. The gate cannot be bypassed by reaching for a different subcommand. |
+| "I'll commit the spec now and add the row after." | The pre-commit hook rejects orphan spec/plan filenames. Allocate first. |
+| "`tasktool` says the verdict isn't ready, but the reviewer comments look fine." | Re-read the verdict line. `revise` is `revise`. If the reviewer chain is mis-parsed, fix the chain; do not pass `--skip-review-gate` casually. |
+| "I'll bring back `docs/TASKLIST.md` for readability." | The hook refuses commits that touch it. Use `tasktool render` if you want markdown. |
+| "I'll just renumber IDs to match execution order." | No. IDs are stable. Execution order lives in the array order; IDs preserve creation order. |
+
+## Integration
+
+- `[[writing-plans]]` — embeds slice IDs in plan filenames; calls `tasktool show <id>` for context.
+- `[[brainstorming]]` — allocates IDs via `tasktool create` before writing the spec.
+- `[[external-review]]` — passes `docs/tasklist.json` (or `tasktool render` output) as `--context`.
+- `[[subagent-driven-development]]` — calls `tasktool close <slice-id>` at slice end and `tasktool archive-phase` at phase end.
+- `[[project-setup]]` — runs `tasktool init` and `install.sh --hook`.
+````
+
+- [x] **Step 2: Delete the obsolete template**
+
+```bash
+git rm skills/tasklist-discipline/templates/TASKLIST.template.md
+rmdir skills/tasklist-discipline/templates 2>/dev/null || true
+```
+
+- [x] **Step 3: Commit**
+
+```bash
+git add skills/tasklist-discipline/SKILL.md
+git commit -m "P2.S3.T5: rewrite tasklist-discipline skill around tasktool"
+```
+
+---
+
+## Task 6: Touch up `writing-plans`
+
+**Files:**
+- Modify: `skills/writing-plans/SKILL.md:18-20`
+- Modify: `skills/writing-plans/handoff-prompt.template.md`
+
+- [x] **Step 1: Update the SKILL.md "Save plans to" block**
+
+Replace the existing paragraph block at `skills/writing-plans/SKILL.md:18-20` with:
+
+```markdown
+**Save plans to:** `docs/plans/YYYY-MM-DD-<id>-<slug>.md` where `<id>` is the tasktool ID for the work (e.g. `p2-s3a`). If the project has no `docs/tasklist.json`, omit the ID segment. User preferences for plan location override this default.
+
+**tasktool integration:** If `docs/tasklist.json` exists, this plan must correspond to a row in it. See [[tasklist-discipline]] for the ID scheme. **Before writing the plan file, verify the row for `<id>` exists** — run `tasktool show <id>` and confirm exit 0. If it doesn't (e.g. a spec was committed without a row, though the pre-commit hook should have caught that), stop and create the row via `tasktool create …` per [[tasklist-discipline]]. Never let the plan be the artifact that mints an ID.
+```
+
+- [x] **Step 2: Update the handoff template**
+
+Open `skills/writing-plans/handoff-prompt.template.md`. Replace every occurrence of `docs/TASKLIST.md` with `docs/tasklist.json` (`tasktool brief <PHASE-OR-SLICE-ID>` for the human-readable orientation). Replace the line:
+
+> Read this file (the handoff prompt), the TASKLIST entry, the spec, and the plan.
+
+with:
+
+> Read this file (the handoff prompt), then run `tasktool brief <PHASE-OR-SLICE-ID>`, and read the spec and the plan.
+
+Replace the "Update TASKLIST.md status in place" bullet with:
+
+> **Close the slice via `tasktool close <SLICE-ID>`** when the slice is reviewed; the CLI enforces the post-slice external-review gate. Archive the phase via `tasktool archive-phase <PHASE-ID>` when all slices are `done`.
+
+- [x] **Step 3: Commit**
+
+```bash
+git add skills/writing-plans/SKILL.md skills/writing-plans/handoff-prompt.template.md
+git commit -m "P2.S3.T6: writing-plans references tasktool"
+```
+
+---
+
+## Task 7: Touch up `brainstorming`
+
+**Files:**
+- Modify: `skills/brainstorming/SKILL.md:29,127`
+
+- [x] **Step 1: Update the spec-save instruction**
+
+Replace the relevant sentence at `skills/brainstorming/SKILL.md:29` with:
+
+> **Write design doc** — save to `docs/specs/YYYY-MM-DD-<id>-<topic>-design.md` (where `<id>` is the tasktool ID per [[tasklist-discipline]], omitted if the project has no `docs/tasklist.json`) and commit. **If no row exists for `<id>` in `docs/tasklist.json` yet, create it first** via `tasktool create phase|slice|cross …` (see [[tasklist-discipline]]) — the spec must not be the first artifact carrying the ID. The pre-commit hook rejects orphan filenames.
+
+- [x] **Step 2: Update the external-review context line**
+
+Replace the line at `skills/brainstorming/SKILL.md:127`:
+
+> Pass `docs/TASKLIST.md` as context when present, and iterate until the verdict is `ready` or `ready with small edits`.
+
+with:
+
+> Pass `docs/tasklist.json` (or `tasktool render` output) as context when present, and iterate until the verdict is `ready` or `ready with small edits`.
+
+- [x] **Step 3: Commit**
+
+```bash
+git add skills/brainstorming/SKILL.md
+git commit -m "P2.S3.T7: brainstorming references tasktool"
+```
+
+---
+
+## Task 8: Touch up `external-review`
+
+**Files:**
+- Modify: `skills/external-review/SKILL.md:250-255,340`
+
+- [x] **Step 1: Update the context table**
+
+Replace the four `docs/TASKLIST.md` cells in the table at lines 250–253 with `docs/tasklist.json` (suffix each one with " (or `tasktool render`)" where the row already says "if present", e.g. row 1 becomes `docs/tasklist.json` (if present)`).
+
+- [x] **Step 2: Update the substitute clause**
+
+Replace the sentence at line 255:
+
+> If the project has no TASKLIST.md, substitute its top-level tracker. Always pass *some* tracker as context so the reviewer sees how the artefact fits the broader plan.
+
+with:
+
+> If the project has no `docs/tasklist.json` (and no equivalent top-level tracker), substitute whatever the project uses. Always pass *some* tracker as context so the reviewer sees how the artefact fits the broader plan.
+
+- [x] **Step 3: Update the integration footnote**
+
+Replace the bullet at line 340:
+
+> `[[tasklist-discipline]]` — slice/phase boundaries are defined by TASKLIST.md status flips.
+
+with:
+
+> `[[tasklist-discipline]]` — slice/phase boundaries are defined by `tasktool close` / `tasktool archive-phase`, both of which enforce the relevant review gate before they accept the status change.
+
+- [x] **Step 4: Commit**
+
+```bash
+git add skills/external-review/SKILL.md
+git commit -m "P2.S3.T8: external-review references tasktool"
+```
+
+---
+
+## Task 9: Touch up `subagent-driven-development`
+
+**Files:**
+- Modify: `skills/subagent-driven-development/SKILL.md:27,43,46,49,51,105,110,135-136,142-143,309,348`
+
+- [x] **Step 1: Update the slice-close steps**
+
+At `:43`, replace:
+
+> 1. Invoke `[[external-review]]` with `--kind post-slice`, passing the plan as `--file` and the spec + TASKLIST.md as `--context`.
+
+with:
+
+> 1. Invoke `[[external-review]]` with `--kind post-slice`, passing the plan as `--file` and the spec + `docs/tasklist.json` as `--context`.
+
+At `:46`, replace:
+
+> 4. Once the verdict gates pass, flip the slice's status in TASKLIST.md per `[[tasklist-discipline]]`.
+
+with:
+
+> 4. Once the verdict gates pass, run `tasktool close <slice-id>` (the CLI re-checks the reviewer chain and refuses on `revise`). See `[[tasklist-discipline]]`.
+
+- [x] **Step 2: Update the phase-close steps**
+
+At `:49`, replace `the spec + plan + TASKLIST.md` with `the spec + plan + docs/tasklist.json`.
+
+At `:51`, replace:
+
+> 3. On verdict acceptance, archive the phase per `[[tasklist-discipline]]` and invoke `[[finishing-a-development-branch]]`.
+
+with:
+
+> 3. On verdict acceptance, run `tasktool archive-phase <phase-id>` (the CLI re-checks the post-phase chain), then invoke `[[finishing-a-development-branch]]`.
+
+- [x] **Step 3: Update the graph node labels**
+
+Replace `"Flip slice status per tasklist-discipline"` (lines 105, 135, 136) with `"tasktool close <slice-id>"`.
+
+Replace `"Archive phase per tasklist-discipline"` (lines 110, 142, 143) with `"tasktool archive-phase <phase-id>"`.
+
+- [x] **Step 4: Update the inline exception and red flag**
+
+At `:27`, replace `a TASKLIST status flip` with `a tasktool note/title tweak`.
+
+At `:309`, replace `TASKLIST is flipped afterward` with `tasktool close succeeds afterward`.
+
+- [x] **Step 5: Commit**
+
+```bash
+git add skills/subagent-driven-development/SKILL.md
+git commit -m "P2.S3.T9: subagent-driven-development references tasktool"
+```
+
+---
+
+## Task 10: Touch up `executing-plans`
+
+**Files:**
+- Modify: `skills/executing-plans/SKILL.md:38,40,50`
+
+- [x] **Step 1: Update the close steps**
+
+At `:38`, replace `the spec + TASKLIST.md as --context` with `the spec + docs/tasklist.json as --context`.
+
+At `:40`, replace `flip the slice status per [[tasklist-discipline]]` with `run tasktool close <slice-id> (the CLI re-checks the reviewer chain) — see [[tasklist-discipline]]`.
+
+At `:50`, replace `archive the phase per [[tasklist-discipline]]` with `run tasktool archive-phase <phase-id>; see [[tasklist-discipline]]`.
+
+- [x] **Step 2: Commit**
+
+```bash
+git add skills/executing-plans/SKILL.md
+git commit -m "P2.S3.T10: executing-plans references tasktool"
+```
+
+---
+
+## Task 11: Touch up `project-setup`
+
+**Files:**
+- Modify: `skills/project-setup/SKILL.md:3,15,26,34,46,150,157`
+
+- [x] **Step 1: Update the skill description (frontmatter)**
+
+At `:3`, replace `TASKLIST.md, doc dirs, reviewer CLI, hooks` with `docs/tasklist.json, doc dirs, reviewer CLI, pre-commit hook`.
+
+- [x] **Step 2: Update the discovery-trigger bullet**
+
+At `:15`, replace the reference to `update TASKLIST.md` with `update docs/tasklist.json via tasktool`.
+
+- [x] **Step 3: Replace audit table row 1**
+
+Replace the row at `:26` with:
+
+> | 1 | `docs/tasklist.json` | File exists, validates clean (`tasktool validate`). | `tasktool init --project <name>`. |
+
+- [x] **Step 4: Add / amend audit row for the pre-commit hook**
+
+Locate the audit-table row that mentions hooks (or insert a new row after row 1) so that the audit includes:
+
+> | N | `.git/hooks/pre-commit` | Tasktool hook installed (`grep -q 'tasktool-pre-commit-hook' .git/hooks/pre-commit`). | `bash tools/tasktool/install.sh --hook` (or set `TASKTOOL_HOME` and run the equivalent for non-superstar repos). |
+
+If the existing row 9 (`:34`) is about CLAUDE.md, leave it alone — just renumber later rows as needed and update the "skills referenced" list so it names `brainstorming`, `writing-plans`, `subagent-driven-development`, `external-review`, `tasklist-discipline`.
+
+- [x] **Step 5: Update the report-step prose**
+
+At `:46`, replace `editing the placeholder fields in TASKLIST.md` with `populating the north-star or first phase title via tasktool create`.
+
+- [x] **Step 6: Update the red-flag row**
+
+At `:150`, replace the `"TASKLIST.md is missing"` row with:
+
+> | "`docs/tasklist.json` is missing, I'll just create it" | Run the audit, present the table, ask. Don't `tasktool init` without consent. |
+
+- [x] **Step 7: Update the integration footnote**
+
+At `:157`, replace:
+
+> `[[tasklist-discipline]]` — provides the TASKLIST.md template.
+
+with:
+
+> `[[tasklist-discipline]]` — describes tasktool conventions; the CLI itself ships the canonical scaffold via `tasktool init`.
+
+- [x] **Step 8: Commit**
+
+```bash
+git add skills/project-setup/SKILL.md
+git commit -m "P2.S3.T11: project-setup references tasktool"
+```
+
+---
+
+## Task 12: Sanity-pass `using-superstar`
+
+**Files:**
+- Modify: `skills/using-superstar/SKILL.md` (only if a substantive reference exists)
+
+- [x] **Step 1: Re-grep**
+
+Run: `grep -n "TASKLIST\.md" skills/using-superstar/SKILL.md`
+Expected: no output. The earlier scan only matched `tasklist-discipline` (skill name, not file path). No edits required.
+
+- [x] **Step 2: If grep matched anything**, edit those lines to refer to `docs/tasklist.json`, then commit:
+
+```bash
+git add skills/using-superstar/SKILL.md
+git commit -m "P2.S3.T12: using-superstar reference cleanup"
+```
+
+Otherwise, skip the commit.
+
+---
+
+## Task 13: End-to-end smoke test
+
+**Files:** none (operational verification).
+
+- [x] **Step 1: Confirm the hook bites**
+
+Run:
+
+```bash
+mkdir -p /tmp/sssmoke && cd /tmp/sssmoke && rm -rf r && mkdir r && cd r
+git init -q -b main && git config user.email t@e && git config user.name t
+mkdir -p docs/specs docs/plans
+bash /home/simon/Dev/sigreer/skills/superstar/tools/tasktool/install.sh --hook
+tasktool init --project smoke
+PHID=$(tasktool create phase --title "P")
+SLID=$(tasktool create slice "$PHID" --title "S")
+git add docs/tasklist.json
+git commit -m "init smoke"
+
+# Should fail (TASKLIST.md):
+echo legacy > docs/TASKLIST.md
+git add docs/TASKLIST.md
+git commit -m "should fail" || echo PASS_legacy_block
+git restore --staged docs/TASKLIST.md && rm docs/TASKLIST.md
+
+# Should fail (orphan filename):
+echo orphan > docs/specs/2026-05-18-P99-orphan-design.md
+git add docs/specs/2026-05-18-P99-orphan-design.md
+git commit -m "should fail" || echo PASS_orphan_block
+git restore --staged docs/specs/2026-05-18-P99-orphan-design.md && rm docs/specs/2026-05-18-P99-orphan-design.md
+
+# Should pass (known ID filename):
+echo plan > docs/plans/2026-05-18-${PHID,,}-${SLID,,}-thing.md
+git add docs/plans/2026-05-18-${PHID,,}-${SLID,,}-thing.md
+git commit -m "known id plan" && echo PASS_known_id
+```
+
+Expected: three lines `PASS_legacy_block`, `PASS_orphan_block`, `PASS_known_id` printed in order.
+
+- [x] **Step 2: Cleanup**
+
+```bash
+rm -rf /tmp/sssmoke
+```
+
+- [x] **Step 3: No commit** — this is verification, not state.
+
+---
+
+## Self-review checklist
+
+Run these against the saved plan before invoking the plan-review gate.
+
+1. **Spec coverage.**
+   - §8.1 (pre-commit hook): Tasks 1–4.
+   - §9.1 (skill rewrite): Task 5.
+   - §9.2 (sibling touch-ups): Tasks 6–12.
+   - §11 (hook test): Task 3.
+   - §12 (in-session edit risk): Task 4 (hook lives in this repo).
+2. **Placeholders.** None — every step contains the file, the diff, and the command.
+3. **Type / name consistency.** `tasktool`, `docs/tasklist.json`, `docs/TASKLIST.md`, `--check-orphans`, `--strict-format`, `--normalise`, `--reviewer-chain`, `--skip-review-gate` used consistently throughout.
+4. **Handoff artifact.** Written in the Execution Handoff step after the plan-review gate.
+
+---
+
+## Completion evidence (post-slice round 1 → resolution)
+
+Recorded after the round-1 post-slice review flagged the absence of durable evidence.
+
+**Commits (in order):**
+
+| Task | Commit  | Subject                                                     |
+|------|---------|-------------------------------------------------------------|
+| T1   | f9cefb5 | tasktool validate --check-orphans                           |
+| T2   | 23659a3 | pre-commit hook template (index-aware)                      |
+| T3   | a887ff9 | install.sh --hook + pre-commit hook tests                   |
+| T4   | —       | local-only hook install (`bash tools/tasktool/install.sh --hook`); smoke confirmed canonical-bytes rejection |
+| T5   | 1a21d35 | rewrite tasklist-discipline skill around tasktool            |
+| T6   | 68e0bab | writing-plans references tasktool                            |
+| T7   | 37543b7 | brainstorming references tasktool                            |
+| T8   | 2878297 | external-review references tasktool                          |
+| T9   | ba1a09c | subagent-driven-development references tasktool              |
+| T10  | 1c74561 | executing-plans references tasktool                          |
+| T11  | fca32e3 | project-setup references tasktool                            |
+| T12  | —       | `grep TASKLIST\.md skills/using-superstar/SKILL.md` → clean; no commit per plan |
+| T13  | —       | end-to-end smoke in fresh repo: legacy block ✓, orphan block ✓, known-id plan accepted ✓ |
+
+**Verifications run:**
+
+- `python -m pytest tools/tasktool/tests -q` → `174 passed`.
+- `tasktool validate --format json` → ok, no errors.
+- `.git/hooks/pre-commit` matches `tools/tasktool/templates/pre-commit-tasktool` (sha256 of template confirmed by `install -m 0755`).
+- T13 smoke: legacy `docs/TASKLIST.md` → hook rejected with the documented message; orphan `docs/specs/2026-05-18-P99-orphan-design.md` → hook flagged `P99`; known-ID `docs/plans/2026-05-18-p1-s1-thing.md` → commit accepted.
diff --git a/docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/.reviewer-output/r1-primary/last-message.md b/docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/.reviewer-output/r1-primary/last-message.md
new file mode 100644
index 0000000..c6363dd
--- /dev/null
+++ b/docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/.reviewer-output/r1-primary/last-message.md
@@ -0,0 +1,31 @@
+1. Findings
+
+F1 — Severity: blocking — The slice is not in a clean, committable post-slice state. `git status --short --untracked-files=all` shows the target plan, handoff prompt, plan-review chain, and post-slice chain are all untracked. This is especially risky because `P2.S3` refs the plan at [docs/tasklist.json:60](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:60), but that referenced file is not tracked. Post-slice acceptance should not pass with unresolved untracked artifacts.
+
+F2 — Severity: important — The target document’s state metadata is stale/inconsistent. The plan says `P2.S3` status is `ready` at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:11](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:11), but the actual tasklist has `reviewer_chain: null` and `status: "in_progress"` at [docs/tasklist.json:63](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:63). That makes the completion handoff ambiguous.
+
+F3 — Severity: important — The plan still records acceptance work as incomplete. All checkboxes remain open, including the `using-superstar` sanity pass and end-to-end smoke at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:957](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:957) and [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:977](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:977). The code appears implemented, but the target document provides no durable evidence of which gates actually ran.
+
+F4 — Severity: minor — The hook test covers raw edit plus `validate --normalise`, but not the literal `TASKTOOL_RAW=1` workflow called out in the plan’s file map and spec acceptance. See [tools/tasktool/tests/test_pre_commit_hook.py:83](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/tests/test_pre_commit_hook.py:83). Since `TASKTOOL_RAW` is not a hook bypass, this is mostly an acceptance-evidence gap.
+
+2. Open questions / assumptions
+
+I assume the plan/reviewer/handoff artifacts are intended to be committed if referenced by `docs/tasklist.json` or used as review evidence. If they are intentionally local-only, remove the tasklist ref or document that policy.
+
+3. Suggested document edits
+
+Update the plan with a short completion evidence section: commit SHAs for T1-T11, T12 no-op grep result, hook install confirmation, smoke-test result, and test command output. Also correct the line-11 tasklist status statement or remove it.
+
+4. Verification gaps / commands
+
+Already run:
+`python -m pytest tools/tasktool/tests -q` → `174 passed in 8.24s`
+`tasktool --project-root /home/simon/Dev/sigreer/skills/superstar validate --format json` → ok, no errors/warnings
+`.git/hooks/pre-commit` matches `tools/tasktool/templates/pre-commit-tasktool`
+
+Still needed before close:
+`git status --short --untracked-files=all` should be clean except intentionally ignored local state.
+Run or document the Task 13 smoke test.
+Optionally add a test that sets `TASKTOOL_RAW=1` in the raw-edit normalise path.
+
+5. Overall verdict: revise
\ No newline at end of file
diff --git a/docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/.reviewer-output/r1-sweep1/last-message.md b/docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/.reviewer-output/r1-sweep1/last-message.md
new file mode 100644
index 0000000..272bb83
--- /dev/null
+++ b/docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/.reviewer-output/r1-sweep1/last-message.md
@@ -0,0 +1,31 @@
+1. Findings
+
+F1 — Severity: blocking — The slice is not in a clean post-slice state. `git status --short --untracked-files=all` shows the target plan, handoff prompt, plan-review artifacts, and post-slice review artifacts are all untracked, including `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md`. This is a completion-gate blocker because `P2.S3` already references that plan in [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:60), but the artifact is not committed.
+
+F2 — Severity: blocking — `P2.S3` has not actually been closed. The tasklist still has `reviewer_chain: null` and `status: "in_progress"` at [docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:63), while the post-slice `chain.json` is untracked and has empty `rounds`. The target plan also claims the entry is `ready` at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:11), which does not match repo state.
+
+F3 — Severity: important — The rewritten `tasklist-discipline` skill teaches the wrong fully qualified form for cross-cutting IDs: [skills/tasklist-discipline/SKILL.md](/home/simon/Dev/sigreer/skills/superstar/skills/tasklist-discipline/SKILL.md:27) says `X4` fully qualifies to `P2.X4`. The spec models cross-cutting IDs as top-level `X*` items, e.g. [docs/specs/2026-05-17-P2-tasktool-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:140), and the new orphan validator also treats `x4` filenames as top-level `X4` at [tools/tasktool/validate.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/validate.py:147). This can mislead agents into producing IDs or filenames the CLI rejects.
+
+F4 — Severity: important — The plan still records acceptance work as incomplete. All checkboxes remain open, including the `using-superstar` sanity pass at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:957) and the end-to-end smoke at [docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:977). The code commits exist, but the target document does not provide durable completion evidence.
+
+2. Open questions / assumptions
+
+I assume the plan, handoff, and reviewer artifacts are intended to be committed because they are referenced as slice evidence. If some reviewer output directories are intentionally local-only, that policy should be explicit and the tracked chain state should still be sufficient for `tasktool close`.
+
+3. Suggested document edits
+
+Update the plan with a completion evidence section: commit SHAs for `P2.S3.T1` through `T11`, the `using-superstar` no-op grep result, hook install confirmation, full test output, and smoke-test result. Correct the tasklist status line or remove it.
+
+Fix `skills/tasklist-discipline/SKILL.md` so cross-cutting fully-qualified IDs are shown as `X4`, not `P2.X4`.
+
+4. Verification gaps / commands
+
+I ran:
+
+`python -m pytest tools/tasktool/tests -q` → `174 passed in 8.26s`
+
+`tasktool --project-root /home/simon/Dev/sigreer/skills/superstar validate --format json` → ok, no errors or warnings.
+
+The Task 13 smoke succeeds under Bash, but the plan’s snippet fails under the repo’s default `zsh` because it uses Bash-only `${PHID,,}`. Either document `bash -lc` for that smoke or replace the lowercase conversion with a portable command.
+
+5. Overall verdict: revise
\ No newline at end of file
diff --git a/docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/chain.json b/docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/chain.json
new file mode 100644
index 0000000..dded716
--- /dev/null
+++ b/docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/chain.json
@@ -0,0 +1,76 @@
+{
+  "schema_version": 1,
+  "chain": "p2-s3-skill-rewrite-and-hook-P2-S3-post-slice",
+  "kind": "post-slice",
+  "target": "docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md",
+  "work_id": "P2.S3",
+  "legacy_migrated": false,
+  "rounds": [
+    {
+      "round": 1,
+      "reviewers": [
+        {
+          "role": "primary",
+          "sweep_group": null,
+          "parent_round": 1,
+          "request": "r1-2026-05-18T1520-primary-request.md",
+          "response": "r1-2026-05-18T1520-primary-response.md",
+          "verdict": "revise",
+          "verdict_valid": true,
+          "returncode": 0,
+          "status": "ok",
+          "provider": "codex",
+          "caller_provider": "claude",
+          "sandbox": {
+            "repo_root": "/home/simon/Dev/sigreer/skills/superstar",
+            "scratch_dir": "/tmp/superstar-reviewer-p2-s3-skill-rewrite-and-hook-P2-S3-post-slice-r1-primary-o4k5wka0",
+            "response_dir": "docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/.reviewer-output/r1-primary",
+            "mode": "workspace-write-with-read-access"
+          }
+        },
+        {
+          "role": "sweep",
+          "sweep_group": 1,
+          "parent_round": 1,
+          "request": "r1-2026-05-18T1520-sweep1-request.md",
+          "response": "r1-2026-05-18T1520-sweep1-response.md",
+          "verdict": "revise",
+          "verdict_valid": true,
+          "returncode": 0,
+          "status": "ok",
+          "provider": "codex",
+          "caller_provider": "claude",
+          "sandbox": {
+            "repo_root": "/home/simon/Dev/sigreer/skills/superstar",
+            "scratch_dir": "/tmp/superstar-reviewer-p2-s3-skill-rewrite-and-hook-P2-S3-post-slice-r1-sweep1-4als1sn7",
+            "response_dir": "docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/.reviewer-output/r1-sweep1",
+            "mode": "workspace-write-with-read-access"
+          }
+        }
+      ],
+      "status": "ok",
+      "returncode": 0,
+      "merged_verdict": "revise",
+      "merged_findings": "r1-merged-findings.md",
+      "request": "r1-2026-05-18T1520-primary-request.md",
+      "response": "r1-2026-05-18T1520-primary-response.md",
+      "resolution": null,
+      "resolution_parse_status": null,
+      "resolution_waiver": false,
+      "head_sha_at_request": "fca32e3dd6a4300a368b893d10c71ad45d56e0f1",
+      "head_sha_after_round": "fca32e3dd6a4300a368b893d10c71ad45d56e0f1",
+      "worktree_dirty_at_request": true,
+      "verdict": "revise",
+      "verdict_valid": true,
+      "findings_count": 4,
+      "blocking_findings_count": 1,
+      "base_ref": null,
+      "base_ref_source": null,
+      "diff_included": false
+    }
+  ],
+  "sweep_checkpoints": {
+    "first-round": "completed",
+    "final-ready": "pending"
+  }
+}
diff --git a/docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/r1-2026-05-18T1520-primary-request.md b/docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/r1-2026-05-18T1520-primary-request.md
new file mode 100644
index 0000000..3396bc9
--- /dev/null
+++ b/docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/r1-2026-05-18T1520-primary-request.md
@@ -0,0 +1,939 @@
+<!-- superstar-prompt:start -->
+You are acting as an independent senior engineering reviewer.
+
+Review stance:
+- Lead with findings, ordered by severity.
+- Focus on correctness, consistency, implementation risk, missing acceptance
+  gates, vague handoffs, ungrounded assumptions, unverified claims, and drift
+  from the codebase.
+- Give exact file/line references when possible.
+- If the document is sound, say that clearly and list residual risks.
+- Keep the review actionable. Avoid broad rewrites unless the current structure
+  creates concrete risk.
+
+Repository root:
+/home/simon/Dev/sigreer/skills/superstar
+
+Target kind:
+post-slice
+
+Review mode:
+Post-slice review. Treat this as a completion gate for one
+slice of work. Compare the completed changes and stated evidence against the
+slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
+untracked artifacts, missing tests, failing or skipped verification, broken
+cross-site behavior, and claims not supported by the repo state.
+
+Target document:
+docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md
+
+Additional context files:
+- docs/specs/2026-05-17-P2-tasktool-design.md
+- docs/tasklist.json
+
+Review output contract:
+1. Findings
+   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
+     stable if this review is iterated in subsequent rounds.
+   - Mark severity inline: `Severity: blocking | important | minor | nit`.
+2. Open questions / assumptions
+3. Suggested document edits
+4. Verification gaps / commands that should be run, if any
+5. Overall verdict: one of "ready", "ready with small edits", or "revise"
+
+Read the files from disk. Do not rely only on the snippets in this prompt.
+
+
+## Target Preview
+
+### docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md
+
+    1	# P2.S3 — Skill rewrite & pre-commit hook Implementation Plan
+    2	
+    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
+    4	
+    5	**Goal:** Replace the markdown-era `tasklist-discipline` skill with a tasktool-centric version, install a per-project pre-commit hook that enforces canonical JSON / blocks orphans / blocks `TASKLIST.md` regressions, and update every sibling skill that still references `docs/TASKLIST.md`.
+    6	
+    7	**Architecture:** Tasktool already owns the data and the review gates (P2.S1, P2.S2). This slice moves the *prose* layer onto the same axis: the `tasklist-discipline` skill becomes a thin pointer to `tasktool` and the gating concepts; the pre-commit hook closes the in-session edit loophole (§8.1, §12 of the spec) by refusing non-canonical bytes, orphaned spec/plan filenames, and any commit that touches `docs/TASKLIST.md`. Sibling skills get surgical edits — every `docs/TASKLIST.md` reference becomes a `tasktool` invocation or a `docs/tasklist.json` reference.
+    8	
+    9	**Tech Stack:** Python 3 stdlib (`tasktool`), POSIX sh (pre-commit hook), markdown (skills).
+   10	
+   11	**TASKLIST entry:** `P2.S3` in `docs/tasklist.json` (created 2026-05-18, status `ready`).
+   12	
+   13	---
+   14	
+   15	## File map
+   16	
+   17	| Action | Path | Responsibility |
+   18	|--------|------|----------------|
+   19	| Modify | `tools/tasktool/validate.py` | Add `validate_no_orphans(repo_root, staged_specs, staged_plans)` — flags any spec/plan filename ID that has no matching TASKLIST row. |
+   20	| Modify | `tools/tasktool/cli.py` | Add `validate --check-orphans <path>...` flag plumbing. |
+   21	| Modify | `tools/tasktool/commands.py` | Wire `cmd_validate(check_orphans=…)` to call the new validator and merge findings into the existing text/json output. |
+   22	| Create | `tools/tasktool/tests/test_validate_orphans.py` | Unit + CLI tests for the new orphan-scan flag. |
+   23	| Create | `tools/tasktool/templates/pre-commit-tasktool` | POSIX sh hook template (per spec §8.1) — strict-format + full validate + orphan scan + TASKLIST.md block. |
+   24	| Modify | `tools/tasktool/install.sh` | Add `install.sh --hook` mode that drops `.git/hooks/pre-commit` from the template, idempotent + `--force`. |
+   25	| Create | `tools/tasktool/tests/test_pre_commit_hook.py` | Synthetic-repo hook tests: canonical commit passes; non-canonical bytes blocked; orphan staged spec blocked; staged `TASKLIST.md` blocked; `TASKTOOL_RAW=1` editor + `validate --normalise` round-trip passes. |
+   26	| Rewrite | `skills/tasklist-discipline/SKILL.md` | Full rewrite around tasktool (per spec §9.1). |
+   27	| Delete | `skills/tasklist-discipline/templates/TASKLIST.template.md` | Replaced by `tasktool init`. |
+   28	| Modify | `skills/writing-plans/SKILL.md` | `docs/TASKLIST.md` → `docs/tasklist.json`; ID-existence check uses `tasktool show <id>`. |
+   29	| Modify | `skills/writing-plans/handoff-prompt.template.md` | Replace TASKLIST.md link/instructions with `tasktool brief <id>` + `docs/tasklist.json`. |
+   30	| Modify | `skills/brainstorming/SKILL.md` | Same swap; "create the row first" routes through `tasktool create`. |
+   31	| Modify | `skills/external-review/SKILL.md` | Context column says `docs/tasklist.json` (or `tasktool render` output). |
+   32	| Modify | `skills/subagent-driven-development/SKILL.md` | Slice/phase close steps call `tasktool close <id>` and `tasktool archive-phase <id>`; remove "flip in TASKLIST.md" prose. |
+   33	| Modify | `skills/executing-plans/SKILL.md` | Same swap. |
+   34	| Modify | `skills/project-setup/SKILL.md` | Audit table row 1 becomes `docs/tasklist.json` via `tasktool init`; row references the hook template; remove TASKLIST.md template reference. |
+   35	| Modify | `skills/using-superstar/SKILL.md` | Cosmetic — none of the user-facing prose references `TASKLIST.md`; verify and no-op if clean. |
+   36	
+   37	---
+   38	
+   39	## Task 1: Orphan-aware validator
+   40	
+   41	**Files:**
+   42	- Modify: `tools/tasktool/validate.py`
+   43	- Modify: `tools/tasktool/cli.py:103-105`
+   44	- Modify: `tools/tasktool/commands.py` (`cmd_validate`)
+   45	- Test: `tools/tasktool/tests/test_validate_orphans.py`
+   46	
+   47	- [ ] **Step 1: Write the failing test**
+   48	
+   49	```python
+   50	# tools/tasktool/tests/test_validate_orphans.py
+   51	import json, subprocess, sys
+   52	from pathlib import Path
+   53	
+   54	TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
+   55	
+   56	def _run(root, *args):
+   57	    return subprocess.run(
+   58	        [sys.executable, str(TOOL), "--project-root", str(root), *args],
+   59	        capture_output=True, text=True,
+   60	    )
+   61	
+   62	def _seed(tmp_path):
+   63	    (tmp_path / "docs").mkdir()
+   64	    (tmp_path / "docs" / "specs").mkdir()
+   65	    (tmp_path / "docs" / "plans").mkdir()
+   66	    _run(tmp_path, "init", "--project", "demo")
+   67	    pid = _run(tmp_path, "create", "phase", "--title", "Phase one").stdout.strip()
+   68	    sid = _run(tmp_path, "create", "slice", pid, "--title", "Slice one").stdout.strip()
+   69	    return pid, sid
+   70	
+   71	def test_orphan_spec_filename_is_flagged(tmp_path):
+   72	    pid, sid = _seed(tmp_path)
+   73	    orphan = tmp_path / "docs" / "specs" / "2026-05-18-P99-orphan-design.md"
+   74	    orphan.write_text("# orphan\n")
+   75	    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(orphan))
+   76	    assert r.returncode == 1, r.stdout + r.stderr
+   77	    payload = json.loads(r.stdout)
+   78	    assert any("P99" in e for e in payload["errors"])
+   79	
+   80	def test_known_id_filename_passes(tmp_path):
+   81	    pid, sid = _seed(tmp_path)
+   82	    known = tmp_path / "docs" / "plans" / f"2026-05-18-{pid.lower()}-{sid.lower()}-thing.md"
+   83	    known.write_text("# plan\n")
+   84	    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(known))
+   85	    assert r.returncode == 0, r.stdout + r.stderr
+   86	```
+   87	
+   88	- [ ] **Step 2: Run test to verify it fails**
+   89	
+   90	Run: `python -m pytest tools/tasktool/tests/test_validate_orphans.py -v`
+   91	Expected: FAIL — `--check-orphans` is not a known flag (argparse error / exit 2).
+   92	
+   93	- [ ] **Step 3: Add the validator function**
+   94	
+   95	The existing project filename convention is **dash-separated** (`2026-05-18-p2-s3-…`), not dot-separated. The regex and lookup must reflect that. In `tools/tasktool/validate.py`, add:
+   96	
+   97	```python
+   98	import re
+   99	from pathlib import Path
+  100	
+  101	# Matches dash-separated IDs at the start of plan/spec filenames. Two forms:
+  102	#   Phase-rooted:    2026-05-18-p2-… | p2-s3-… | p2-s3a-… | p2-s3-t1-…
+  103	#   Cross-cutting:   2026-05-18-x4-…
+  104	# Note: cross-cutting IDs are top-level in the data model (e.g. `X4`, not `P2.X4`).
+  105	# A filename of the form `p2-x4-…` is treated as "phase P2, slice/cross child X4 *under*
+  106	# P2" only if such a row exists; otherwise it's flagged. In practice cross filenames
+  107	# should use the top-level form.
+  108	_FILENAME_ID_RE = re.compile(
+  109	    r"^\d{4}-\d{2}-\d{2}-"
+  110	    r"(?:(?P<cross>[Xx]\d+)"
+  111	    r"|(?P<phase>[Pp]\d+)"
+  112	      r"(?:-(?P<child>[SsXx]\d+[a-z]?))?"
+  113	      r"(?:-(?P<task>[Tt]\d+))?"
+  114	    r")-",
+  115	)
+  116	
+  117	def _normalise_id(*, cross: str | None, phase: str | None,
+  118	                  child: str | None, task: str | None) -> str:
+  119	    if cross:
+  120	        return cross.upper()
+  121	    assert phase is not None
+  122	    parts = [phase.upper()]
+  123	    if child:
+  124	        parts.append(child.upper())
+  125	    if task:
+  126	        parts.append(task.upper())
+  127	    return ".".join(parts)
+  128	
+  129	def collect_known_ids(p) -> set[str]:
+  130	    """Return the set of *fully-qualified* IDs that exist in this project.
+  131	
+  132	    Short forms are deliberately NOT included — orphan checking requires exact
+  133	    fully-qualified matches (e.g. `P99.S1` must not pass merely because some
+  134	    other phase has an `S1`).
+  135	    """
+  136	    ids: set[str] = set()
+  137	    for ph in p.phases:
+  138	        ids.add(ph.id)
+  139	        for sl in ph.slices:
+  140	            ids.add(f"{ph.id}.{sl.id}")
+  141	            for t in sl.tasks:
+  142	                ids.add(f"{ph.id}.{sl.id}.{t.id}")
+  143	    for ph in getattr(p, "archived_phases", []) or []:
+  144	        ids.add(ph.id if hasattr(ph, "id") else ph["id"])
+  145	    for x in p.cross_cutting:
+  146	        ids.add(x.id)  # Cross-cutting IDs are top-level (e.g. "X4").
+  147	    return ids
+  148	
+  149	def validate_orphan_filenames(p, paths) -> list[str]:
+  150	    known = collect_known_ids(p)
+  151	    findings: list[str] = []
+  152	    for path in paths:
+  153	        name = Path(path).name
+  154	        m = _FILENAME_ID_RE.match(name)
+  155	        if not m:
+  156	            continue
+  157	        fq = _normalise_id(
+  158	            cross=m.group("cross"),
+  159	            phase=m.group("phase"),
+  160	            child=m.group("child"),
+  161	            task=m.group("task"),
+  162	        )
+  163	        if fq in known:
+  164	            continue
+  165	        findings.append(
+  166	            f"{path}: filename references ID {fq} but no matching row in tasklist.json"
+  167	        )
+  168	    return findings
+  169	```
+  170	
+  171	Extend the orphans test from Step 1 with a wrong-phase regression case:
+  172	
+  173	```python
+  174	def test_cross_cutting_top_level_filename_passes(tmp_path):
+  175	    """`2026-05-18-x4-…` resolves to top-level X4 and passes when X4 exists."""
+  176	    _seed(tmp_path)
+  177	    cid = _run(tmp_path, "create", "cross", "--title", "C4").stdout.strip()  # X1 → X4 depending on seed
+  178	    f = tmp_path / "docs" / "specs" / f"2026-05-18-{cid.lower()}-design.md"
+  179	    f.write_text("# cross spec\n")
+  180	    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(f))
+  181	    assert r.returncode == 0, r.stdout + r.stderr
+  182	
+  183	def test_cross_cutting_unknown_top_level_is_flagged(tmp_path):
+  184	    _seed(tmp_path)
+  185	    f = tmp_path / "docs" / "specs" / "2026-05-18-x99-design.md"
+  186	    f.write_text("# nope\n")
+  187	    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(f))
+  188	    assert r.returncode == 1, r.stdout + r.stderr
+  189	    payload = json.loads(r.stdout)
+  190	    assert any("X99" in e for e in payload["errors"])
+  191	
+  192	def test_wrong_phase_qualified_id_is_flagged(tmp_path):
+  193	    """`P99-S1-…` must NOT pass merely because some other phase has an `S1`."""
+  194	    _seed(tmp_path)  # creates P1.S1
+  195	    orphan = tmp_path / "docs" / "plans" / "2026-05-18-p99-s1-thing.md"
+  196	    orphan.write_text("# wrong-phase\n")
+  197	    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(orphan))
+  198	    assert r.returncode == 1, r.stdout + r.stderr
+  199	    payload = json.loads(r.stdout)
+  200	    assert any("P99.S1" in e for e in payload["errors"])
+  201	```
+  202	
+  203	- [ ] **Step 4: Plumb the CLI flag**
+  204	
+  205	The existing `cmd_validate` contract is `(format=…, strict_format=…, normalise=…) -> tuple[int, str]` and the CLI writes the returned text — preserve it. The current JSON shape is `{"ok", "errors", "warnings"}` — extend it by appending orphan findings to `errors`.
+  206	
+  207	In `tools/tasktool/cli.py` (where `p_validate` is built):
+  208	
+  209	```python
+  210	p_validate = sub.add_parser("validate")
+  211	p_validate.add_argument("--format", choices=["text", "json"], default="text")
+  212	p_validate.add_argument("--strict-format", action="store_true")
+  213	p_validate.add_argument("--normalise", action="store_true")
+  214	p_validate.add_argument("--check-orphans", nargs="*", default=None,
+  215	                        help="Spec/plan filepaths to check against tasklist.json IDs.")
+  216	```
+  217	
+  218	In the `args.cmd == "validate"` branch, preserve the existing `(rc, text)` write-through:
+  219	
+  220	```python
+  221	elif args.cmd == "validate":
+  222	    rc, text = commands.cmd_validate(
+  223	        repo_root=root, format=args.format,
+  224	        strict_format=args.strict_format, normalise=args.normalise,
+  225	        check_orphans=args.check_orphans,
+  226	    )
+  227	    sys.stdout.write(text)
+  228	    return rc
+  229	```
+  230	
+  231	In `tools/tasktool/commands.py`, extend the existing `cmd_validate` (keep the `format=` kwarg name; return `(rc, text)`). After loading `project`, if `check_orphans` is provided run `validate_orphan_filenames(project, check_orphans)` and append each finding to the `errors` list (so the JSON shape stays `{"ok", "errors", "warnings"}` and the text mode prints them through the same loop). Tests assert against `payload["errors"]`, not `findings` — match the existing schema.
+  232	
+  233	- [ ] **Step 5: Run test to verify it passes**
+  234	
+  235	Run: `python -m pytest tools/tasktool/tests/test_validate_orphans.py -v`
+  236	Expected: PASS (both tests).
+  237	
+  238	- [ ] **Step 6: Re-run the full tasktool suite**
+  239	
+  240	Run: `python -m pytest tools/tasktool/tests -q`
+  241	Expected: PASS (no regressions).
+  242	
+  243	- [ ] **Step 7: Commit**
+  244	
+  245	```bash
+  246	git add tools/tasktool/validate.py tools/tasktool/cli.py tools/tasktool/commands.py tools/tasktool/tests/test_validate_orphans.py
+  247	git commit -m "P2.S3.T1: tasktool validate --check-orphans"
+  248	```
+  249	
+  250	---
+  251	
+  252	## Task 2: Pre-commit hook template
+  253	
+  254	**Files:**
+  255	- Create: `tools/tasktool/templates/pre-commit-tasktool`
+  256	- Test: covered by Task 3.
+  257	
+  258	The hook MUST validate **staged** content (the index), not the working tree — a clean worktree with stale staged bytes would otherwise sneak past `tasktool validate`. The strategy: materialise the staged blob into a temporary project root via `git checkout-index --prefix=`, then run `tasktool --project-root <tempdir>` against that copy. Orphan filename checks use `git diff --cached --name-only --diff-filter=ACMR` directly (filename-only, not content).
+  259	
+  260	- [ ] **Step 1: Write the hook**
+  261	
+  262	Write `tools/tasktool/templates/pre-commit-tasktool` (mode 0755):
+  263	
+  264	```sh
+  265	#!/usr/bin/env sh
+  266	# tasktool-pre-commit-hook v1
+  267	# Installed by `tools/tasktool/install.sh --hook`.
+  268	# Validates the STAGED content (the index), not the working tree, so a clean
+  269	# worktree with stale staged bytes cannot sneak past.
+  270	#
+  271	# Enforces:
+  272	#   1. docs/TASKLIST.md must not be staged (project migrated to docs/tasklist.json).
+  273	#   2. Staged docs/tasklist.json must be canonical (tasktool validate --strict-format).
+  274	#   3. Staged docs/tasklist.json must pass full validation.
+  275	#   4. Staged spec/plan filenames must reference an ID present in the staged tasklist.json.
+  276	# Bypass for genuine emergencies: `git commit --no-verify` and document the reason.
+  277	set -e
+  278	
+  279	STAGED="$(git diff --cached --name-only --diff-filter=ACMR)"
+  280	
+  281	# 1. Block docs/TASKLIST.md
+  282	if printf '%s\n' "$STAGED" | grep -qx 'docs/TASKLIST.md'; then
+  283	  echo "pre-commit: docs/TASKLIST.md is staged but this project migrated to docs/tasklist.json." >&2
+  284	  echo "  Delete docs/TASKLIST.md or unstage it. Use tasktool to mutate docs/tasklist.json." >&2
+  285	  exit 1
+  286	fi
+  287	
+  288	# 1b. Block staged deletion of docs/tasklist.json — a tasktool-managed repo
+  289	# must keep its canonical tracker.
+  290	if git diff --cached --name-only --diff-filter=D | grep -qx 'docs/tasklist.json'; then
+  291	  echo "pre-commit: docs/tasklist.json is staged for deletion. A tasktool-managed repo must keep its canonical tracker." >&2
+  292	  echo "  Unstage the deletion (\`git restore --staged docs/tasklist.json\`) or use --no-verify with a written justification." >&2
+  293	  exit 1
+  294	fi
+  295	
+  296	# Determine whether docs/tasklist.json exists in the index.
+  297	if git ls-files --cached --error-unmatch docs/tasklist.json >/dev/null 2>&1; then
+  298	  HAS_INDEX_TASKLIST=1
+  299	else
+  300	  HAS_INDEX_TASKLIST=0
+  301	fi
+  302	
+  303	if [ "$HAS_INDEX_TASKLIST" -eq 1 ]; then
+  304	  # Materialise the staged blob into a temp project root.
+  305	  TMP="$(mktemp -d 2>/dev/null || mktemp -d -t tasktool-precommit)"
+  306	  trap 'rm -rf "$TMP"' EXIT
+  307	  mkdir -p "$TMP/docs"
+  308	  git show :docs/tasklist.json > "$TMP/docs/tasklist.json"
+  309	
+  310	  # 2 + 3. Validate the staged content. Strict-format only when tasklist.json
+  311	  # is itself in the staged change set (the file is canonical at rest anyway,
+  312	  # but we surface the canonical-format failure with the right message).
+  313	  if printf '%s\n' "$STAGED" | grep -qx 'docs/tasklist.json'; then
+  314	    tasktool --project-root "$TMP" validate --strict-format --format text
+  315	  fi
+  316	  tasktool --project-root "$TMP" validate --format text
+  317	
+  318	  # 4. Orphan scan over staged spec/plan filenames (filename-only, evaluated
+  319	  # against the staged tasklist.json). Materialise staged specs/plans into
+  320	  # $TMP so paths exist relative to --project-root.
+  321	  ORPHAN_CANDIDATES="$(printf '%s\n' "$STAGED" | grep -E '^docs/(specs|plans)/[0-9]{4}-[0-9]{2}-[0-9]{2}-' || true)"
+  322	  if [ -n "$ORPHAN_CANDIDATES" ]; then
+  323	    for f in $ORPHAN_CANDIDATES; do
+  324	      mkdir -p "$TMP/$(dirname "$f")"
+  325	      git show ":$f" > "$TMP/$f" 2>/dev/null || true
+  326	    done
+  327	    # shellcheck disable=SC2086
+  328	    (cd "$TMP" && tasktool validate --check-orphans $ORPHAN_CANDIDATES --format text)
+  329	  fi
+  330	fi
+  331	```
+  332	
+  333	- [ ] **Step 2: Commit the template**
+  334	
+  335	```bash
+  336	chmod +x tools/tasktool/templates/pre-commit-tasktool
+  337	git add tools/tasktool/templates/pre-commit-tasktool
+  338	git commit -m "P2.S3.T2: pre-commit hook template (index-aware)"
+  339	```
+  340	
+  341	---
+  342	
+  343	## Task 3: Hook installer + tests
+  344	
+  345	**Files:**
+  346	- Modify: `tools/tasktool/install.sh`
+  347	- Test: `tools/tasktool/tests/test_pre_commit_hook.py`
+  348	
+  349	- [ ] **Step 1: Add `--hook` mode to install.sh**
+  350	
+  351	The existing `tools/tasktool/install.sh` is Bash (`#!/usr/bin/env bash`, `set -euo pipefail`, `${BASH_SOURCE[0]}`, `[[ … ]]`). The new `--hook` branch must run **before** the shim-install logic (which treats `$1` as a `--force` toggle), and must use Bash. All invocations from tests, docs, and the smoke task use `bash`, not `sh`.
+  352	
+  353	In `tools/tasktool/install.sh`, insert the `--hook` dispatch immediately after the `set -euo pipefail` line and before `SCRIPT_DIR=`:
+  354	
+  355	```bash
+  356	# --- hook installer (must precede shim-install logic) ---------------------
+  357	if [[ "${1:-}" == "--hook" ]]; then
+  358	  shift
+  359	  FORCE_HOOK=0
+  360	  if [[ "${1:-}" == "--force" ]]; then FORCE_HOOK=1; shift; fi
+  361	  REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
+  362	  if [[ -z "$REPO_ROOT" ]]; then
+  363	    echo "install.sh --hook: must be run inside a git working tree" >&2
+  364	    exit 1
+  365	  fi
+  366	  HOOK_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/templates/pre-commit-tasktool"
+  367	  HOOK_DEST="$REPO_ROOT/.git/hooks/pre-commit"
+  368	  if [[ -f "$HOOK_DEST" && "$FORCE_HOOK" -ne 1 ]]; then
+  369	    if ! grep -q 'tasktool-pre-commit-hook' "$HOOK_DEST" 2>/dev/null; then
+  370	      echo "install.sh --hook: $HOOK_DEST exists and is not a tasktool hook. Re-run with --force to overwrite." >&2
+  371	      exit 1
+  372	    fi
+  373	  fi
+  374	  install -m 0755 "$HOOK_SRC" "$HOOK_DEST"
+  375	  echo "Installed $HOOK_DEST"
+  376	  exit 0
+  377	fi
+  378	# --------------------------------------------------------------------------
+  379	```
+  380	
+  381	- [ ] **Step 2: Write the failing test**
+  382	
+  383	```python
+  384	# tools/tasktool/tests/test_pre_commit_hook.py
+  385	import os, subprocess, sys, shutil, textwrap
+  386	from pathlib import Path
+  387	
+  388	REPO = Path(__file__).resolve().parents[3]
+  389	TOOL = REPO / "tools" / "tasktool" / "__main__.py"
+  390	INSTALL = REPO / "tools" / "tasktool" / "install.sh"
+  391	
+  392	def _git(repo, *args, check=True, env=None):
+  393	    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=check, env=env)
+  394	
+  395	def _tasktool(repo, *args, env=None):
+  396	    return subprocess.run([sys.executable, str(TOOL), "--project-root", str(repo), *args],
+  397	                          capture_output=True, text=True, env=env)
+  398	
+  399	def _seed_repo(tmp_path):
+  400	    repo = tmp_path / "r"
+  401	    repo.mkdir()
+  402	    _git(repo, "init", "-q", "-b", "main")
+  403	    _git(repo, "config", "user.email", "t@example.com")
+  404	    _git(repo, "config", "user.name", "t")
+  405	    (repo / "docs").mkdir()
+  406	    (repo / "docs" / "specs").mkdir()
+  407	    (repo / "docs" / "plans").mkdir()
+  408	    _tasktool(repo, "init", "--project", "demo")
+  409	    # Make `tasktool` callable from the hook's PATH:
+  410	    bin_dir = tmp_path / "bin"
+  411	    bin_dir.mkdir()
+  412	    (bin_dir / "tasktool").write_text(f"#!/usr/bin/env sh\nexec {sys.executable} {TOOL} \"$@\"\n")
+  413	    os.chmod(bin_dir / "tasktool", 0o755)
+  414	    env = os.environ.copy()
+  415	    env["PATH"] = f"{bin_dir}:{env['PATH']}"
+  416	    # Install the hook (install.sh is bash):
+  417	    subprocess.run(["bash", str(INSTALL), "--hook"], cwd=repo, check=True, env=env)
+  418	    return repo, env
+  419	
+  420	def test_canonical_commit_passes(tmp_path):
+  421	    repo, env = _seed_repo(tmp_path)
+  422	    _git(repo, "add", "docs/tasklist.json", env=env)
+  423	    r = _git(repo, "commit", "-m", "init", check=False, env=env)
+  424	    assert r.returncode == 0, r.stdout + r.stderr
+  425	
+  426	def test_non_canonical_bytes_rejected(tmp_path):
+  427	    repo, env = _seed_repo(tmp_path)
+  428	    _git(repo, "add", "docs/tasklist.json", env=env)
+  429	    _git(repo, "commit", "-m", "init", env=env)
+  430	    # Append a stray newline → non-canonical.
+  431	    with open(repo / "docs" / "tasklist.json", "a") as f:
+  432	        f.write("\n")
+  433	    _git(repo, "add", "docs/tasklist.json", env=env)
+  434	    r = _git(repo, "commit", "-m", "tamper", check=False, env=env)
+  435	    assert r.returncode != 0
+  436	    assert "canonical" in (r.stdout + r.stderr).lower()
+  437	
+  438	def test_orphan_spec_filename_rejected(tmp_path):
+  439	    repo, env = _seed_repo(tmp_path)
+  440	    _git(repo, "add", "docs/tasklist.json", env=env)
+  441	    _git(repo, "commit", "-m", "init", env=env)
+  442	    orphan = repo / "docs" / "specs" / "2026-05-18-P99-orphan-design.md"
+  443	    orphan.write_text("# orphan\n")
+  444	    _git(repo, "add", str(orphan.relative_to(repo)), env=env)
+  445	    r = _git(repo, "commit", "-m", "orphan", check=False, env=env)
+  446	    assert r.returncode != 0
+  447	    assert "P99" in (r.stdout + r.stderr)
+  448	
+  449	def test_tasklist_md_rejected(tmp_path):
+  450	    repo, env = _seed_repo(tmp_path)
+  451	    _git(repo, "add", "docs/tasklist.json", env=env)
+  452	    _git(repo, "commit", "-m", "init", env=env)
+  453	    legacy = repo / "docs" / "TASKLIST.md"
+  454	    legacy.write_text("# legacy\n")
+  455	    _git(repo, "add", "docs/TASKLIST.md", env=env)
+  456	    r = _git(repo, "commit", "-m", "legacy", check=False, env=env)
+  457	    assert r.returncode != 0
+  458	    assert "TASKLIST.md" in (r.stdout + r.stderr)
+  459	
+  460	def test_raw_edit_then_normalise_passes(tmp_path):
+  461	    repo, env = _seed_repo(tmp_path)
+  462	    _git(repo, "add", "docs/tasklist.json", env=env)
+  463	    _git(repo, "commit", "-m", "init", env=env)
+  464	    p = repo / "docs" / "tasklist.json"
+  465	    with open(p, "a") as f:
+  466	        f.write("\n")
+  467	    _tasktool(repo, "validate", "--normalise", env=env)
+  468	    _git(repo, "add", "docs/tasklist.json", env=env)
+  469	    r = _git(repo, "commit", "-m", "normalised", check=False, env=env)
+  470	    assert r.returncode == 0, r.stdout + r.stderr
+  471	
+  472	def test_staged_bad_normalised_worktree_is_rejected(tmp_path):
+  473	    """Stage non-canonical bytes, then normalise the worktree without re-staging.
+  474	    The hook MUST reject because the index is what gets committed."""
+  475	    repo, env = _seed_repo(tmp_path)
+  476	    _git(repo, "add", "docs/tasklist.json", env=env)
+  477	    _git(repo, "commit", "-m", "init", env=env)
+  478	    p = repo / "docs" / "tasklist.json"
+  479	    with open(p, "a") as f:
+  480	        f.write("\n")
+  481	    # Stage the bad bytes.
+  482	    _git(repo, "add", "docs/tasklist.json", env=env)
+  483	    # Now normalise the WORKTREE only (do not re-add).
+  484	    _tasktool(repo, "validate", "--normalise", env=env)
+  485	    r = _git(repo, "commit", "-m", "staged-bad-worktree-clean", check=False, env=env)
+  486	    assert r.returncode != 0, (
+  487	        "hook must validate the index, not the worktree, but commit succeeded: "
+  488	        + r.stdout + r.stderr
+  489	    )
+  490	
+  491	def test_tasklist_json_deletion_rejected(tmp_path):
+  492	    """Staging the deletion of docs/tasklist.json must be refused."""
+  493	    repo, env = _seed_repo(tmp_path)
+  494	    _git(repo, "add", "docs/tasklist.json", env=env)
+  495	    _git(repo, "commit", "-m", "init", env=env)
+  496	    _git(repo, "rm", "docs/tasklist.json", env=env)
+  497	    r = _git(repo, "commit", "-m", "delete tracker", check=False, env=env)
+  498	    assert r.returncode != 0, "hook must refuse tasklist.json deletion: " + r.stdout + r.stderr
+  499	    assert "deletion" in (r.stdout + r.stderr).lower() or "delete" in (r.stdout + r.stderr).lower()
+  500	
+  501	def test_hook_install_is_idempotent(tmp_path):
+  502	    """Running `install.sh --hook` twice without --force must succeed both times."""
+  503	    repo, env = _seed_repo(tmp_path)
+  504	    # First install happened in _seed_repo. Run again:
+  505	    r = subprocess.run(["bash", str(INSTALL), "--hook"], cwd=repo, capture_output=True, text=True, env=env)
+  506	    assert r.returncode == 0, r.stdout + r.stderr
+  507	
+  508	def test_staged_good_dirty_worktree_passes(tmp_path):
+  509	    """Stage canonical bytes, then dirty the worktree without re-staging.
+  510	    The hook MUST pass — the index is canonical, the worktree dirt is irrelevant."""
+  511	    repo, env = _seed_repo(tmp_path)
+  512	    _git(repo, "add", "docs/tasklist.json", env=env)
+  513	    _git(repo, "commit", "-m", "init", env=env)
+  514	    # Stage a clean tasktool-mediated change.
+  515	    _tasktool(repo, "create", "phase", "--title", "P", env=env)
+  516	    _git(repo, "add", "docs/tasklist.json", env=env)
+  517	    # Now dirty the worktree post-stage.
+  518	    p = repo / "docs" / "tasklist.json"
+  519	    with open(p, "a") as f:
+  520	        f.write("\n")
+  521	    r = _git(repo, "commit", "-m", "staged-good-dirty-worktree", check=False, env=env)
+  522	    assert r.returncode == 0, (
+  523	        "hook must accept canonical index regardless of worktree dirt: "
+  524	        + r.stdout + r.stderr
+  525	    )
+  526	```
+  527	
+  528	- [ ] **Step 3: Run test to verify it fails**
+  529	
+  530	Run: `python -m pytest tools/tasktool/tests/test_pre_commit_hook.py -v`
+  531	Expected: FAIL — `install.sh --hook` does not yet branch correctly, or hook prerequisites missing.
+  532	
+  533	- [ ] **Step 4: Iterate on install.sh + hook until tests pass**
+  534	
+  535	Run the test, read the failure, fix the hook or installer, repeat. Do not adjust the *tests* to match — adjust the implementation.
+  536	
+  537	- [ ] **Step 5: Run the full suite**
+  538	
+  539	Run: `python -m pytest tools/tasktool/tests -q`
+  540	Expected: PASS (all hook tests + all earlier tests).
+  541	
+  542	- [ ] **Step 6: Commit**
+  543	
+  544	```bash
+  545	git add tools/tasktool/install.sh tools/tasktool/tests/test_pre_commit_hook.py
+  546	git commit -m "P2.S3.T3: install.sh --hook + pre-commit hook tests"
+  547	```
+  548	
+  549	---
+  550	
+  551	## Task 4: Install the hook in this repo
+  552	
+  553	**Files:**
+  554	- Create: `.git/hooks/pre-commit` (out-of-tree; not committed).
+  555	
+  556	- [ ] **Step 1: Run the installer**
+  557	
+  558	```bash
+  559	bash tools/tasktool/install.sh --hook
+  560	```
+  561	
+  562	Expected stdout: `Installed /home/simon/Dev/sigreer/skills/superstar/.git/hooks/pre-commit`
+  563	
+  564	- [ ] **Step 2: Smoke test the hook on the live repo**
+  565	
+  566	```bash
+  567	echo "" >> docs/tasklist.json
+  568	git add docs/tasklist.json
+  569	git commit -m "should fail" || echo "rejected as expected"
+  570	git restore --staged docs/tasklist.json
+  571	git checkout -- docs/tasklist.json
+  572	```
+  573	
+  574	Expected: commit refused with a canonical-format error; restore returns the file to clean state.
+  575	
+  576	- [ ] **Step 3: No commit for this task** — the hook installation is operator-side state, not tree state.
+  577	
+  578	---
+  579	
+  580	## Task 5: Rewrite `tasklist-discipline` SKILL.md
+  581	
+  582	**Files:**
+  583	- Rewrite: `skills/tasklist-discipline/SKILL.md`
+  584	- Delete: `skills/tasklist-discipline/templates/TASKLIST.template.md`
+  585	
+  586	- [ ] **Step 1: Replace the skill body**
+  587	
+  588	Overwrite `skills/tasklist-discipline/SKILL.md` with:
+  589	
+  590	````markdown
+  591	---
+  592	name: tasklist-discipline
+  593	description: Use whenever planning, closing slices/phases, or referencing work items in a project that uses docs/tasklist.json. Teaches the tasktool CLI surface and the gating concepts; the CLI enforces the rules.
+  594	---
+  595	
+  596	# TASKLIST Discipline
+  597	
+  598	A `docs/tasklist.json` file is the canonical, top-level tracker for the project. It groups work into **phases**, **slices**, **tasks**, and **cross-cutting** items, each with a stable, never-renumbered ID. All mutations flow through `tasktool`; a pre-commit hook refuses non-canonical bytes, orphaned spec/plan filenames, and any commit that touches the legacy `docs/TASKLIST.md`.
+  599	
+  600	**Announce at start:** "I'm using the tasklist-discipline skill to update docs/tasklist.json via tasktool."
+
+[truncated: 434 additional lines]
+
+## Context Previews
+
+### docs/specs/2026-05-17-P2-tasktool-design.md
+
+    1	# P2 — tasktool: JSON-backed task management CLI
+    2	
+    3	**Status:** spec, awaiting external review
+    4	**Author:** Simon Greer (with AI brainstorming)
+    5	**Date:** 2026-05-17
+    6	**TASKLIST entry:** `P2` in [`docs/TASKLIST.md`](../TASKLIST.md)
+    7	
+    8	## 1. Problem
+    9	
+   10	`docs/TASKLIST.md` is the canonical project tracker in superstar's workflow. The format is enforced by prose (the `tasklist-discipline` skill), not by code:
+   11	
+   12	- Stable P/S/T/X IDs, never renumbered.
+   13	- Status emoji set (`✅` / `🚧` / `⏸` / `☐`) paired with status tags (`DONE YYYY-MM-DD`, `IN PROGRESS`, `BLOCKED on …`, `READY`).
+   14	- Specific date format, specific filename conventions, specific close-in-place / phase-archive rules.
+   15	
+   16	Two consequences:
+   17	
+   18	1. **Brittleness for downstream consumers.** The AGS sidebar, external reviewers, and any future dashboards have to re-parse a hand-edited markdown file whose shape is enforced only by an LLM following a skill. A single stray emoji or missing date breaks the consumer.
+   19	2. **Context bloat for agents.** The current pattern is "agent reads the entire TASKLIST.md to orient." Most of that content is irrelevant to the agent's current task. The agent absorbs the whole file because targeted queries do not exist.
+   20	
+   21	Conformity is enforced by repeatedly reminding agents of the rules. This works imperfectly and consumes context every time.
+   22	
+   23	## 2. Goals
+   24	
+   25	- **Eliminate hand-editing of the canonical tracker.** All mutations go through a single CLI that validates inputs at write time.
+   26	- **Reduce agent context burden.** Replace "read the whole file" with targeted queries (`tasktool brief <id>`, `tasktool show <id>`, `tasktool list --status open`).
+   27	- **Produce reliable structured data for downstream tools** (AGS sidebar, reviewers, future dashboards) without forcing them to re-parse markdown.
+   28	- **Preserve the existing mental model** (phases / slices / tasks / cross-cutting; stable IDs; close-in-place; phase archive; status gates).
+   29	- **Stay zero-dependency.** Python stdlib only. No package install required at the project level — a global shim points at this repo.
+   30	
+   31	## 3. Non-goals
+   32	
+   33	- **Cross-project querying.** Each project keeps its own JSON; there is no central store. AGS can read multiple per-project JSONs if it wants a cross-project view.
+   34	- **External-system sync.** No Linear, Jira, GitHub Projects integration. Out of scope.
+   35	- **Web UI.** Out of scope. The AGS sidebar is the user-facing view; the CLI is the agent-facing view.
+   36	- **Concurrent multi-writer correctness.** Single-user, single-machine. File-level write is atomic via tempfile + rename; no locking beyond that.
+   37	- **Backwards compatibility with the markdown shape.** `tasktool render` produces a readable markdown view but is not constrained to byte-match the prior hand-written format.
+   38	
+   39	## 4. Approach summary
+   40	
+   41	A Python stdlib CLI (`tasktool`) reads and writes a per-project `docs/tasklist.json`. The CLI is the only sanctioned mutation path; the `tasklist-discipline` skill is rewritten to teach the commands rather than the rules. A pre-commit hook enforces that `docs/tasklist.json` only changes via the CLI. The existing `docs/TASKLIST.md` is parsed by a one-shot importer and then deleted; downstream readers (AGS sidebar) consume the JSON directly or import the Python module.
+   42	
+   43	## 5. Architecture
+   44	
+   45	### 5.1 Code location & distribution
+   46	
+   47	- **Source:** `tools/tasktool/` in the superstar repo. Single Python package; entry point `tools/tasktool/__main__.py`.
+   48	- **Stdlib only:** `argparse`, `json`, `pathlib`, `dataclasses`, `datetime`, `re`, `sys`, `os`, `subprocess` (for git-staging the JSON after writes), `unittest`.
+   49	- **Global shim:** `~/.local/bin/tasktool` — one-line script: `exec python3 /home/simon/Dev/sigreer/skills/superstar/tools/tasktool/__main__.py "$@"`. Installed once per machine by `tools/tasktool/install.sh`. The installer is idempotent; it errors if a different shim already exists at the target path unless `--force` is passed.
+   50	- **No per-project install step.** Projects need only the per-project `docs/tasklist.json` and (optionally) the pre-commit hook.
+   51	
+   52	### 5.2 Per-project state
+   53	
+   54	- **`docs/tasklist.json`** — canonical, git-tracked.
+   55	- **No committed markdown.** `tasktool render` writes a markdown view to stdout on demand. The output is suitable for piping into a temp file for review or pasting into a PR description.
+   56	- **Schema version field** in the JSON enables future migrations.
+   57	
+   58	### 5.3 Integration with consumers
+   59	
+   60	- **AGS sidebar (Python):** `import tasktool` directly. The installer adds the package to a known site-packages-equivalent path (or symlinks). Functions like `load_project(path)`, `brief(project, id)` are exposed.
+   61	- **Other tools:** read `docs/tasklist.json` directly, validated against the schema emitted by `tasktool schema`.
+   62	- **External reviewer / skills:** call `tasktool render`, `tasktool show`, `tasktool brief` as needed.
+   63	
+   64	## 6. Data model
+   65	
+   66	### 6.1 Top-level shape (`docs/tasklist.json`)
+   67	
+   68	```json
+   69	{
+   70	  "schema_version": 1,
+   71	  "project": "superstar",
+   72	  "north_star": "Optional one-paragraph project intent.",
[truncated: 5987 additional lines]


---

You are acting as an independent senior engineering reviewer.

Review stance:
- Lead with findings, ordered by severity.
- Focus on correctness, consistency, implementation risk, missing acceptance
  gates, vague handoffs, ungrounded assumptions, unverified claims, and drift
  from the codebase.
- Give exact file/line references when possible.
- If the document is sound, say that clearly and list residual risks.
- Keep the review actionable. Avoid broad rewrites unless the current structure
  creates concrete risk.

Repository root:
/home/simon/Dev/sigreer/skills/superstar

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md

Additional context files:
- docs/specs/2026-05-17-P2-tasktool-design.md
- docs/tasklist.json

Review output contract:
1. Findings
   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
     stable if this review is iterated in subsequent rounds.
   - Mark severity inline: `Severity: blocking | important | minor | nit`.
2. Open questions / assumptions
3. Suggested document edits
4. Verification gaps / commands that should be run, if any
5. Overall verdict: one of "ready", "ready with small edits", or "revise"

Read the files from disk. Do not rely only on the snippets in this prompt.


## Target Preview

### docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md

    1	# P2.S3 — Skill rewrite & pre-commit hook Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.
    4	
    5	**Goal:** Replace the markdown-era `tasklist-discipline` skill with a tasktool-centric version, install a per-project pre-commit hook that enforces canonical JSON / blocks orphans / blocks `TASKLIST.md` regressions, and update every sibling skill that still references `docs/TASKLIST.md`.
    6	
    7	**Architecture:** Tasktool already owns the data and the review gates (P2.S1, P2.S2). This slice moves the *prose* layer onto the same axis: the `tasklist-discipline` skill becomes a thin pointer to `tasktool` and the gating concepts; the pre-commit hook closes the in-session edit loophole (§8.1, §12 of the spec) by refusing non-canonical bytes, orphaned spec/plan filenames, and any commit that touches `docs/TASKLIST.md`. Sibling skills get surgical edits — every `docs/TASKLIST.md` reference becomes a `tasktool` invocation or a `docs/tasklist.json` reference.
    8	
    9	**Tech Stack:** Python 3 stdlib (`tasktool`), POSIX sh (pre-commit hook), markdown (skills).
   10	
   11	**TASKLIST entry:** `P2.S3` in `docs/tasklist.json` (created 2026-05-18; current status set via `tasktool` during execution).
   12	
   13	---
   14	
   15	## File map
   16	
   17	| Action | Path | Responsibility |
   18	|--------|------|----------------|
   19	| Modify | `tools/tasktool/validate.py` | Add `validate_no_orphans(repo_root, staged_specs, staged_plans)` — flags any spec/plan filename ID that has no matching TASKLIST row. |
   20	| Modify | `tools/tasktool/cli.py` | Add `validate --check-orphans <path>...` flag plumbing. |
   21	| Modify | `tools/tasktool/commands.py` | Wire `cmd_validate(check_orphans=…)` to call the new validator and merge findings into the existing text/json output. |
   22	| Create | `tools/tasktool/tests/test_validate_orphans.py` | Unit + CLI tests for the new orphan-scan flag. |
   23	| Create | `tools/tasktool/templates/pre-commit-tasktool` | POSIX sh hook template (per spec §8.1) — strict-format + full validate + orphan scan + TASKLIST.md block. |
   24	| Modify | `tools/tasktool/install.sh` | Add `install.sh --hook` mode that drops `.git/hooks/pre-commit` from the template, idempotent + `--force`. |
   25	| Create | `tools/tasktool/tests/test_pre_commit_hook.py` | Synthetic-repo hook tests: canonical commit passes; non-canonical bytes blocked; orphan staged spec blocked; staged `TASKLIST.md` blocked; `TASKTOOL_RAW=1` editor + `validate --normalise` round-trip passes. |
   26	| Rewrite | `skills/tasklist-discipline/SKILL.md` | Full rewrite around tasktool (per spec §9.1). |
   27	| Delete | `skills/tasklist-discipline/templates/TASKLIST.template.md` | Replaced by `tasktool init`. |
   28	| Modify | `skills/writing-plans/SKILL.md` | `docs/TASKLIST.md` → `docs/tasklist.json`; ID-existence check uses `tasktool show <id>`. |
   29	| Modify | `skills/writing-plans/handoff-prompt.template.md` | Replace TASKLIST.md link/instructions with `tasktool brief <id>` + `docs/tasklist.json`. |
   30	| Modify | `skills/brainstorming/SKILL.md` | Same swap; "create the row first" routes through `tasktool create`. |
   31	| Modify | `skills/external-review/SKILL.md` | Context column says `docs/tasklist.json` (or `tasktool render` output). |
   32	| Modify | `skills/subagent-driven-development/SKILL.md` | Slice/phase close steps call `tasktool close <id>` and `tasktool archive-phase <id>`; remove "flip in TASKLIST.md" prose. |
   33	| Modify | `skills/executing-plans/SKILL.md` | Same swap. |
   34	| Modify | `skills/project-setup/SKILL.md` | Audit table row 1 becomes `docs/tasklist.json` via `tasktool init`; row references the hook template; remove TASKLIST.md template reference. |
   35	| Modify | `skills/using-superstar/SKILL.md` | Cosmetic — none of the user-facing prose references `TASKLIST.md`; verify and no-op if clean. |
   36	
   37	---
   38	
   39	## Task 1: Orphan-aware validator
   40	
   41	**Files:**
   42	- Modify: `tools/tasktool/validate.py`
   43	- Modify: `tools/tasktool/cli.py:103-105`
   44	- Modify: `tools/tasktool/commands.py` (`cmd_validate`)
   45	- Test: `tools/tasktool/tests/test_validate_orphans.py`
   46	
   47	- [x] **Step 1: Write the failing test**
   48	
   49	```python
   50	# tools/tasktool/tests/test_validate_orphans.py
   51	import json, subprocess, sys
   52	from pathlib import Path
   53	
   54	TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
   55	
   56	def _run(root, *args):
   57	    return subprocess.run(
   58	        [sys.executable, str(TOOL), "--project-root", str(root), *args],
   59	        capture_output=True, text=True,
   60	    )
   61	
   62	def _seed(tmp_path):
   63	    (tmp_path / "docs").mkdir()
   64	    (tmp_path / "docs" / "specs").mkdir()
   65	    (tmp_path / "docs" / "plans").mkdir()
   66	    _run(tmp_path, "init", "--project", "demo")
   67	    pid = _run(tmp_path, "create", "phase", "--title", "Phase one").stdout.strip()
   68	    sid = _run(tmp_path, "create", "slice", pid, "--title", "Slice one").stdout.strip()
   69	    return pid, sid
   70	
   71	def test_orphan_spec_filename_is_flagged(tmp_path):
   72	    pid, sid = _seed(tmp_path)
   73	    orphan = tmp_path / "docs" / "specs" / "2026-05-18-P99-orphan-design.md"
   74	    orphan.write_text("# orphan\n")
   75	    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(orphan))
   76	    assert r.returncode == 1, r.stdout + r.stderr
   77	    payload = json.loads(r.stdout)
   78	    assert any("P99" in e for e in payload["errors"])
   79	
   80	def test_known_id_filename_passes(tmp_path):
   81	    pid, sid = _seed(tmp_path)
   82	    known = tmp_path / "docs" / "plans" / f"2026-05-18-{pid.lower()}-{sid.lower()}-thing.md"
   83	    known.write_text("# plan\n")
   84	    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(known))
   85	    assert r.returncode == 0, r.stdout + r.stderr
   86	```
   87	
   88	- [x] **Step 2: Run test to verify it fails**
   89	
   90	Run: `python -m pytest tools/tasktool/tests/test_validate_orphans.py -v`
   91	Expected: FAIL — `--check-orphans` is not a known flag (argparse error / exit 2).
   92	
   93	- [x] **Step 3: Add the validator function**
   94	
   95	The existing project filename convention is **dash-separated** (`2026-05-18-p2-s3-…`), not dot-separated. The regex and lookup must reflect that. In `tools/tasktool/validate.py`, add:
   96	
   97	```python
   98	import re
   99	from pathlib import Path
  100	
  101	# Matches dash-separated IDs at the start of plan/spec filenames. Two forms:
  102	#   Phase-rooted:    2026-05-18-p2-… | p2-s3-… | p2-s3a-… | p2-s3-t1-…
  103	#   Cross-cutting:   2026-05-18-x4-…
  104	# Note: cross-cutting IDs are top-level in the data model (e.g. `X4`, not `P2.X4`).
  105	# A filename of the form `p2-x4-…` is treated as "phase P2, slice/cross child X4 *under*
  106	# P2" only if such a row exists; otherwise it's flagged. In practice cross filenames
  107	# should use the top-level form.
  108	_FILENAME_ID_RE = re.compile(
  109	    r"^\d{4}-\d{2}-\d{2}-"
  110	    r"(?:(?P<cross>[Xx]\d+)"
  111	    r"|(?P<phase>[Pp]\d+)"
  112	      r"(?:-(?P<child>[SsXx]\d+[a-z]?))?"
  113	      r"(?:-(?P<task>[Tt]\d+))?"
  114	    r")-",
  115	)
  116	
  117	def _normalise_id(*, cross: str | None, phase: str | None,
  118	                  child: str | None, task: str | None) -> str:
  119	    if cross:
  120	        return cross.upper()
  121	    assert phase is not None
  122	    parts = [phase.upper()]
  123	    if child:
  124	        parts.append(child.upper())
  125	    if task:
  126	        parts.append(task.upper())
  127	    return ".".join(parts)
  128	
  129	def collect_known_ids(p) -> set[str]:
  130	    """Return the set of *fully-qualified* IDs that exist in this project.
  131	
  132	    Short forms are deliberately NOT included — orphan checking requires exact
  133	    fully-qualified matches (e.g. `P99.S1` must not pass merely because some
  134	    other phase has an `S1`).
  135	    """
  136	    ids: set[str] = set()
  137	    for ph in p.phases:
  138	        ids.add(ph.id)
  139	        for sl in ph.slices:
  140	            ids.add(f"{ph.id}.{sl.id}")
  141	            for t in sl.tasks:
  142	                ids.add(f"{ph.id}.{sl.id}.{t.id}")
  143	    for ph in getattr(p, "archived_phases", []) or []:
  144	        ids.add(ph.id if hasattr(ph, "id") else ph["id"])
  145	    for x in p.cross_cutting:
  146	        ids.add(x.id)  # Cross-cutting IDs are top-level (e.g. "X4").
  147	    return ids
  148	
  149	def validate_orphan_filenames(p, paths) -> list[str]:
  150	    known = collect_known_ids(p)

[truncated: 915 additional lines]

<!-- superstar-prompt:end -->