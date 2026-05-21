<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 2 of p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice.

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
| 1 | revise | 2 | 1 |

## Prior-round findings

Source: merged findings from r1 (authoritative)

# Merged findings for r1

## Primary

# Review — 2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md (post-slice, round 1)

- Target: `docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md`
- Request: `docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/r1-2026-05-21T2120-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: blocking — P5.S3 implementation happened without the required tasktool lifecycle start. The plan makes `tasktool start P5.S3` the lifecycle gate and says it must flip the row to `in_progress` before implementation ([plan:84](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:84), [plan:90](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:90)). The repo has seven `P5.S3` commits on the slice branch, but `docs/tasklist.json` still records P5.S3 as `status: ready`, `started: null`, `planning_status: proposed`, and its `reviewer_chain` still points at the plan chain rather than a post-slice chain ([tasklist:307](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/tasklist.json:307), [tasklist:319](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/tasklist.json:319), [tasklist:324](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/tasklist.json:324), [tasklist:325](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/tasklist.json:325), [tasklist:326](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/tasklist.json:326)). This breaks the slice evidence trail and should be corrected before close.

F2 — Severity: important — The post-slice review chain artifact is present but not durably recorded. `git status --short` reports `?? docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/`; its `chain.json` has `rounds: []` and both checkpoints pending ([chain:8](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/chain.json:8), [chain:9](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/chain.json:9)). The plan requires handing back “`git status` clean” before close ([plan:1084](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1084)). Commit/register the actual review chain output before treating the slice as closeable.

2. Open questions / assumptions

I assume the best-effort prompt-template shim was accepted during plan review, despite the spec’s literal “Claude shim and Codex shim integration tests” language. The implementation is explicit about that limitation in the plan and in tests, so I am not treating it as a blocker here.

3. Suggested document edits

Update `docs/tasklist.json` through `tasktool` lifecycle commands, not by hand: P5.S3 should reflect the actual started state and post-slice reviewer chain before close. Also include the post-slice reviewer chain path in refs once the review round is materialized.

4. Verification gaps / commands that should be run

Already run during this review:
`tools/tasktool/tasktool validate --strict-format` → `ok`
`python -m pytest tools/tasktool/tests -q` → `526 passed, 1 warning in 94.17s`

After fixing lifecycle/reviewer artifacts, rerun:
`tools/tasktool/tasktool show P5.S3`
`git status --short`
`tools/tasktool/tasktool validate --strict-format`

Overall verdict: revise


## Sweep 1

# Review — 2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md (post-slice, round 1)

- Target: `docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md`
- Request: `docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/r1-2026-05-21T2120-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

S1.F1 — Severity: blocking — P5.S3 lifecycle state is split and not durably closeable. The plan requires `tasktool start P5.S3` as the lifecycle gate and expects the row to flip to `in_progress` before implementation ([plan](</home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:84>), [plan](</home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:90>)). The target checkout’s `docs/tasklist.json` still has `started: null`, `status: ready`, and no recorded worktree fields for P5.S3 ([tasklist](</home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/tasklist.json:315>), [tasklist](</home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/tasklist.json:325>)). The authoritative checkout also has a staged, uncommitted `docs/tasklist.json` diff that adds `started`, `status: in_progress`, `worktree_branch`, and `worktree_path`, so the lifecycle evidence is currently dirty and not reflected in normal `tasktool show P5.S3` output.

S1.F2 — Severity: important — The post-slice reviewer chain is untracked/incomplete. `git status --short` reports `?? docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/`, and `chain.json` still has `rounds: []` with both sweep checkpoints pending ([chain](</home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/chain.json:8>), [chain](</home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/chain.json:9>)). The plan’s final handoff requires `git status` clean before close ([plan](</home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1084>)).

2. Open questions / assumptions

Assumption: the staged authoritative `docs/tasklist.json` mutation is from `tasktool start P5.S3`, but it has not been committed or normalized into a clean durable workflow state.

3. Suggested document edits

Update lifecycle state through the tasktool workflow so P5.S3 has committed, authoritative start/worktree evidence. Register and commit the post-slice reviewer chain once this review round is materialized. Do not hand-edit `docs/tasklist.json`.

4. Verification gaps / commands that should be run

Already run during this review:

`tools/tasktool/tasktool validate --strict-format` → `ok`

`python -m pytest tools/tasktool/tests -q` → `526 passed, 1 warning in 94.23s`

`wc -l skills/using-git-worktrees/SKILL.md` → `22`

Still needed before close: clean `git status` in the target worktree and authoritative checkout, plus `tools/tasktool/tasktool show P5.S3` reflecting the intended lifecycle state.

Overall verdict: revise



## Resolution report for prior round

# Resolution for r1

## F1
Status: fixed
Evidence:
- Commit: da98412 (authoritative checkout, main branch) — "P5.S3: record tasktool start lifecycle (in_progress + worktree fields)"
- Files: `docs/tasklist.json` (P5.S3 row now records `started: 2026-05-21`, `status: in_progress`, `worktree_branch`, `worktree_path`)
- Verification: `tools/tasktool/tasktool show P5.S3` reports `status: in_progress`, `started: 2026-05-21`, `worktree_path: .worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow`.

Notes:
The `tasktool start P5.S3` mutation was performed at slice start but the resulting staged diff in the authoritative checkout was not committed before the post-slice review ran. The slice worktree therefore read a stale copy of `docs/tasklist.json` (from `main` at slice-branch base). Mutation has now been committed in the authoritative checkout; subsequent `tasktool show P5.S3` reflects the intended lifecycle state.

## F2
Status: fixed
Evidence:
- Files: `docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/` — round 1 request/response/merged-findings/chain.json committed in the slice worktree; chain registered on the P5.S3 row via `tasktool artifact add P5.S3 --kind reviewer --path docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/`.
- Verification: `git status --short` clean in both worktree and authoritative checkout after these commits.

Notes:
The reviewer chain folder was untracked at the time of the round-1 review (the bridge had just materialized it). It is now committed on the slice branch and registered as a reviewer artifact on the P5.S3 row.


## Changes since prior round

Worktree status: clean

### git diff base..HEAD

diff --git a/docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/.reviewer-output/r1-primary/codex-events.jsonl b/docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/.reviewer-output/r1-primary/codex-events.jsonl
new file mode 100644
index 0000000..50630e8
--- /dev/null
+++ b/docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/.reviewer-output/r1-primary/codex-events.jsonl
@@ -0,0 +1,50 @@
+{"type":"thread.started","thread_id":"019e4c32-02e6-7781-8260-e9c83e0f9ba8"}
+{"type":"turn.started"}
+{"type":"item.completed","item":{"id":"item_0","type":"agent_message","text":"Using the review workflow directly from the prompt, and I’ll ground the gate decision in the live checkout rather than the preview. I’ll inspect the target plan, spec, tasklist, git state, and verification evidence before writing findings."}}
+{"type":"item.started","item":{"id":"item_1","type":"command_execution","command":"/usr/bin/zsh -lc 'pwd && git status --short && git rev-parse --show-toplevel && git branch --show-current'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_1","type":"command_execution","command":"/usr/bin/zsh -lc 'pwd && git status --short && git rev-parse --show-toplevel && git branch --show-current'","aggregated_output":"/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow\n?? docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/\n/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow\nworktree-p5-s3-skill-rewrite-subagent-guard-workflow\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_2","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md | sed -n '1,260p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_2","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md | sed -n '1,260p'\"","aggregated_output":"     1\t# P5.S3 — Skill rewrite + subagent guard + workflow updates — Implementation Plan\n     2\t\n     3\t> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.\n     4\t\n     5\t**Goal:** Collapse `using-git-worktrees` to ≤40 lines around a subagent early-exit, teach `tasktool start` to refuse dispatched subagents via three env signals, and update the coordinator's dispatch prompt templates to instruct subagents to export `SUPERSTAR_SUBAGENT_ROLE` so the runtime guard has the highest practical chance of firing when subagents follow the directive.\n     6\t\n     7\t**Architecture:** Five disjoint edit clusters:\n     8\t1. Skill rewrite (`using-git-worktrees/SKILL.md` shrunk; long-form submodule guard relocated to `references/submodules.md`).\n     9\t2. Subagent guard inside `tools/tasktool/commands.py::cmd_start` (three env signals with declared precedence, single refusal message, no fingerprinting).\n    10\t3. Workflow cross-reference updates in `tasklist-discipline`, `executing-plans`, `subagent-driven-development` (no touch to `finishing-a-development-branch` — that belongs to P5.S2).\n    11\t4. Coordinator-facing dispatch prompt updates: extend `skills/subagent-driven-development/implementer-prompt.md` (and the spec-reviewer / code-quality-reviewer prompt templates) to instruct each dispatched subagent to export `SUPERSTAR_SUBAGENT_ROLE=<role>` as its first shell command. This is a best-effort prose directive (Superstar does not wrap the harness's native dispatch tool), backed by the runtime guard in step 2 and the load-bearing prose rule in step 3. Tests assert the directive is present in every template and that a simulated `env -i bash` dispatch is correctly refused.\n    12\t5. Tests: signal-precedence and plain-shell false-negative coverage for the guard, template fixture tests for the shim directive, a token-budget regression fixture for the skill body, and a doc-shape test for the rewritten skill (≤40 lines, `<SUBAGENT-STOP>` block present).\n    13\t\n    14\t**Tech Stack:** Python (3.10+) for tasktool, pytest for tests, bash for fixtures, plain Markdown for skill / template edits.\n    15\t\n    16\t**Out of scope (handled elsewhere):**\n    17\t- Schema field reads/writes for `worktree_path` / `worktree_branch` / `worktree_in_place` — owned by P5.S1.\n    18\t- Worktree creation, adoption, prune, repair, finalize — owned by P5.S1 / P5.S2.\n    19\t- `finishing-a-development-branch` edits (post-merge prune step) — owned by P5.S2 per spec §5.3.2 (`:212-214`). The spec's P5.S3 slice paragraph at §6 (`:275-277`) lists all three workflow skills, but §5.3.2 splits ownership and assigns the prune step to P5.S2. Treat §5.3.2 as authoritative; this slice does not modify `finishing-a-development-branch`. Task 1.5 below verifies P5.S2 actually shipped the prune step before this slice starts so the workflow gap is not silently left open.\n    20\t- Removal of legacy `.claude/worktrees/` / `.codex/worktrees/` paths — deferred per spec §4.\n    21\t\n    22\t**Shim scope (read this before Task 8).** The spec at `:137` and `:286` says \"the Claude shim and Codex shim\" export `SUPERSTAR_SUBAGENT_ROLE`. The Superstar repo does not currently wrap the harness's native dispatch tool (Claude Code's `Task`, Codex's `spawn_agent`) — there is no Python or JS interceptor between the harness and the subagent process where an env var could be injected programmatically. The honest implementation is therefore a **best-effort prose guard**: the coordinator's dispatch prompt templates instruct the subagent to export the variable as its first shell command. The runtime guard in `tasktool start` (Task 7) is the load-bearing safety net; the prose rule in `tasklist-discipline` (Task 9) is the load-bearing *cultural* rule. The prompt-template directive (Task 8) raises the probability that the runtime guard fires in real use, but does not guarantee it. Task 8 acknowledges this explicitly and adds a simulated-harness transcript test (Task 8 Step 8.5) to prove the dispatch-time refusal actually works in a realistic shell when the directive is followed. If a future harness change exposes a real env-injection point, that integration can be wired in without breaking either the runtime guard or the prose rule.\n    23\t\n    24\t**Scheduling preconditions (verify before starting):**\n    25\t\n    26\t```sh\n    27\ttools/tasktool/tasktool show P5.S3\n    28\ttools/tasktool/tasktool schedule P5\n    29\t```\n    30\t\n    31\tExpected: `P5.S3` exists with `status: ready`, `depends_on: [P5.S1, P5.S2]`, `planning_status: proposed`. After plan-review passes, the writing-plans flow will ratify (coordinator-side `tasktool ratify P5.S3 --parallel-group …` is **not** part of this plan — the coordinator owns ratification).\n    32\t\n    33\t**Verification baseline (must pass against `main` before slice start, per spec §10):**\n    34\t\n    35\t```sh\n    36\ttools/tasktool/tasktool validate --strict-format\n    37\tpython -m pytest tools/tasktool/tests -q\n    38\t```\n    39\t\n    40\t---\n    41\t\n    42\t## File Structure\n    43\t\n    44\t| File | Status | Responsibility |\n    45\t|---|---|---|\n    46\t| `skills/using-git-worktrees/SKILL.md` | rewrite (226 → ≤40 lines) | Subagent early-exit block + 4 one-line rules. |\n    47\t| `skills/using-git-worktrees/references/submodules.md` | create | Submodule guard lifted from current SKILL.md §0; loaded on demand. |\n    48\t| `skills/tasklist-discipline/SKILL.md` | append paragraph | Subagents must inherit cwd; never call `tasktool start`. |\n    49\t| `skills/executing-plans/SKILL.md` | minor edits | Add cross-reference to the rewritten skill's early-exit; mention parent-creates-worktree pattern. |\n    50\t| `skills/subagent-driven-development/SKILL.md` | minor edits | One-line reminder that subagents inherit cwd and never call `tasktool start`. |\n    51\t| `skills/subagent-driven-development/implementer-prompt.md` | minor edits | Add explicit `SUPERSTAR_SUBAGENT_ROLE=implementer` directive in the dispatch template. |\n    52\t| `skills/subagent-driven-development/spec-reviewer-prompt.md` | minor edits | Same directive, role=`spec-reviewer`. |\n    53\t| `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | minor edits | Same directive, role=`code-quality-reviewer`. |\n    54\t| `tools/tasktool/commands.py` | extend `cmd_start` | Three-signal subagent guard with declared precedence; refusal message verbatim from spec §5.3. |\n    55\t| `tools/tasktool/tests/test_lifecycle_start.py` | extend | Add guard tests (precedence, refusal message, plain-shell false-negative). |\n    56\t| `tools/tasktool/tests/fixtures/p5_s3_skill_body.txt` | create | Frozen copy of the rewritten skill body for the token-budget regression test. |\n    57\t| `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` | extend | Skill-shape tests: ≤40 lines, contains `<SUBAGENT-STOP>` block, contains `tasktool start` reference, references `references/submodules.md`. |\n    58\t| `tools/tasktool/tests/test_subagent_prompt_shim.py` | create | Assert each of the three subagent-prompt templates exports `SUPERSTAR_SUBAGENT_ROLE=<expected>`. |\n    59\t\n    60\t---\n    61\t\n    62\t## Task 1: Establish baseline + lifecycle start\n    63\t\n    64\t**Files:** none — verification + tasktool lifecycle only.\n    65\t\n    66\t- [ ] **Step 1.1: Verify scheduling preconditions**\n    67\t\n    68\t```sh\n    69\ttools/tasktool/tasktool show P5.S3\n    70\ttools/tasktool/tasktool schedule P5\n    71\t```\n    72\t\n    73\tExpected: `P5.S3` exists with `depends_on: [P5.S1, P5.S2]`. If absent or differs, stop — coordinator needs to fix the row before this plan can execute.\n    74\t\n    75\t- [ ] **Step 1.2: Verify baseline tests pass**\n    76\t\n    77\t```sh\n    78\ttools/tasktool/tasktool validate --strict-format\n    79\tpython -m pytest tools/tasktool/tests -q\n    80\t```\n    81\t\n    82\tExpected: both exit 0. If anything fails on `main`, stop and report — do not start the slice over a red baseline.\n    83\t\n    84\t- [ ] **Step 1.3: Start the slice**\n    85\t\n    86\t```sh\n    87\ttools/tasktool/tasktool start P5.S3\n    88\t```\n    89\t\n    90\tExpected: status flips to `in_progress`. This is the lifecycle gate; do not substitute prose, TodoWrite, or hand JSON edits.\n    91\t\n    92\t- [ ] **Step 1.4: Verify P5.S2 shipped the `finishing-a-development-branch` prune step**\n    93\t\n    94\tThis slice deliberately does not modify `finishing-a-development-branch` (spec §5.3.2 assigns the prune step to P5.S2). Confirm P5.S2 actually delivered that edit before this slice begins, so the workflow gap is not silently left open:\n    95\t\n    96\t```sh\n    97\ttools/tasktool/tasktool show P5.S2\n    98\tgrep -nE \"tasktool worktree prune\" skills/finishing-a-development-branch/SKILL.md\n    99\t```\n   100\t\n   101\tExpected: `P5.S2` status is `done` (closed by P5.S2's external review gate), and `grep` returns at least one match showing the post-merge prune step. If `P5.S2` is not done, **stop** — this slice waits on it. If `P5.S2` is done but `finishing-a-development-branch` does not mention `tasktool worktree prune`, stop and surface the gap to the coordinator (this would be a P5.S2 closeout defect, not a P5.S3 problem to paper over).\n   102\t\n   103\t- [ ] **Step 1.5: No commit yet.**\n   104\t\n   105\tThis task produces no diff. Proceed to Task 2.\n   106\t\n   107\t---\n   108\t\n   109\t## Task 2: Extract submodule guard to `references/submodules.md`\n   110\t\n   111\t**Files:**\n   112\t- Create: `skills/using-git-worktrees/references/submodules.md`\n   113\t\n   114\t- [ ] **Step 2.1: Create the references directory and submodules reference**\n   115\t\n   116\t```sh\n   117\tmkdir -p skills/using-git-worktrees/references\n   118\t```\n   119\t\n   120\tWrite `skills/using-git-worktrees/references/submodules.md` with this content:\n   121\t\n   122\t```markdown\n   123\t# Submodule guard for using-git-worktrees\n   124\t\n   125\tLoad this reference **only** when `tasktool start` reports a worktree-detection conflict caused by a submodule, or when the early-exit block in `SKILL.md` cannot decide whether the current directory is a linked worktree or a submodule checkout.\n   126\t\n   127\t## Why this matters\n   128\t\n   129\t`GIT_DIR != GIT_COMMON_DIR` is true in two distinct situations:\n   130\t\n   131\t1. The current directory is a linked git worktree (e.g. `.worktrees/worktree-p5-s3-…`).\n   132\t2. The current directory is a git submodule checkout.\n   133\t\n   134\tThe submodule case must **not** be treated as a worktree. Treating a submodule as a linked worktree skips legitimate worktree creation and corrupts the slice's evidence boundary.\n   135\t\n   136\t## Disambiguating\n   137\t\n   138\tRun:\n   139\t\n   140\t```sh\n   141\tgit rev-parse --show-superproject-working-tree 2>/dev/null\n   142\t```\n   143\t\n   144\t- Empty output (or non-zero exit): you are **not** in a submodule. The `GIT_DIR != GIT_COMMON_DIR` signal is genuine — treat the directory as a linked worktree.\n   145\t- Non-empty output (a path): you are inside a submodule of that superproject. Treat the directory as a normal repo checkout and do not skip the worktree creation step.\n   146\t\n   147\t## What to do\n   148\t\n   149\tIf you discover you are in a submodule and tasktool refuses to proceed, leave the submodule (`cd` to the superproject root, or to the authoritative checkout) and re-run `tasktool start <id>` from there. Do not attempt to nest a worktree inside the submodule.\n   150\t```\n   151\t\n   152\t- [ ] **Step 2.2: Stage the new file**\n   153\t\n   154\t```sh\n   155\tgit add skills/using-git-worktrees/references/submodules.md\n   156\t```\n   157\t\n   158\t- [ ] **Step 2.3: Defer commit until the skill rewrite lands (Task 3).** This keeps the rewrite atomic.\n   159\t\n   160\t---\n   161\t\n   162\t## Task 3: Rewrite `using-git-worktrees/SKILL.md`\n   163\t\n   164\t**Files:**\n   165\t- Modify: `skills/using-git-worktrees/SKILL.md` (current 226 lines → target ≤40 lines including frontmatter, per spec §5.5)\n   166\t\n   167\t- [ ] **Step 3.1: Replace the entire file with the rewritten body**\n   168\t\n   169\tWrite `skills/using-git-worktrees/SKILL.md` with exactly this content:\n   170\t\n   171\t```markdown\n   172\t---\n   173\tname: using-git-worktrees\n   174\tdescription: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - ensures an isolated workspace exists via native tools or git worktree fallback\n   175\t---\n   176\t\n   177\t<SUBAGENT-STOP>\n   178\tYou were dispatched as a subagent. The parent coordinator has already created or adopted the worktree for the active slice and `cd`d you into it. Do not read or apply the rest of this skill, and do not call `tasktool start`. If `git rev-parse --git-dir` differs from `git rev-parse --git-common-dir` (and you are not inside a submodule — see `references/submodules.md` if uncertain), you are inside the parent's linked worktree; proceed with your task. If they match, you are in a plain checkout; ask the parent before editing files.\n   179\t</SUBAGENT-STOP>\n   180\t\n   181\t# Using Git Worktrees\n   182\t\n   183\t**Announce at start:** \"I'm using the using-git-worktrees skill to enter the slice worktree.\"\n   184\t\n   185\t**Rule:** Implementation slice/task work runs in an isolated linked worktree owned by tasktool. A plain `main`/`master` checkout is planning/read-only by default unless the human partner opts out of isolation in the current turn.\n   186\t\n   187\t**Run:** `tasktool start <slice-id>` from the authoritative checkout (or from an already-linked worktree of the same repo — tasktool will auto-adopt). It creates the worktree at `.worktrees/worktree-<id>-<slug>`, records the path and branch on the slice row, and prints the `cd` line. Idempotent: a consistent recorded path is a no-op. See `[[tasklist-discipline]]` for the lifecycle commands and the routing rules.\n   188\t\n   189\t**Opt-out:** For planning, spec, or design slices that touch no code, run `tasktool start <slice-id> --in-place`. The slice row records `worktree_in_place: true`; later `close` and `worktree prune` treat the slice as having no worktree.\n   190\t\n   191\t**Drift:** If `tasktool start` reports a conflict (path missing, branch mismatched, plain-dir collision), run the exact `tasktool worktree {adopt,repair,prune --force}` command it prints. Do not improvise with raw `git worktree` invocations; do not delete `.worktrees/` directories by hand.\n   192\t\n   193\tFor submodule-vs-worktree disambiguation, see `references/submodules.md`.\n   194\t```\n   195\t\n   196\t- [ ] **Step 3.2: Verify length ≤ 40 lines including frontmatter**\n   197\t\n   198\t```sh\n   199\twc -l skills/using-git-worktrees/SKILL.md\n   200\t```\n   201\t\n   202\tExpected: ≤ 40. If over, tighten the body — do not add a Quick Reference table, Common Mistakes section, Red Flags table, or decision tree to bring it back under target; those are deliberately forbidden by §5.5.\n   203\t\n   204\t- [ ] **Step 3.3: Verify the `<SUBAGENT-STOP>` block is the first content after frontmatter**\n   205\t\n   206\t```sh\n   207\tgrep -n \"<SUBAGENT-STOP>\\|</SUBAGENT-STOP>\" skills/using-git-worktrees/SKILL.md\n   208\t```\n   209\t\n   210\tExpected: opening tag near line 6, closing tag before the `# Using Git Worktrees` heading.\n   211\t\n   212\t- [ ] **Step 3.4: Commit Tasks 2 + 3 atomically**\n   213\t\n   214\t```sh\n   215\tgit add skills/using-git-worktrees/SKILL.md skills/using-git-worktrees/references/submodules.md\n   216\tgit commit -m \"P5.S3: rewrite using-git-worktrees skill to subagent early-exit + tasktool pointer\"\n   217\t```\n   218\t\n   219\t---\n   220\t\n   221\t## Task 4: Write failing skill-shape tests\n   222\t\n   223\t**Files:**\n   224\t- Modify: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` (append tests)\n   225\t\n   226\t- [ ] **Step 4.1: Read the existing module to understand the helper conventions**\n   227\t\n   228\t```sh\n   229\tsed -n '1,40p' tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py\n   230\t```\n   231\t\n   232\tExpected: a `skill_text(name)` helper exists. (If the helper signature differs, adapt the snippets below to match; do not rename the helper.)\n   233\t\n   234\t- [ ] **Step 4.2: Append the skill-shape tests**\n   235\t\n   236\tAppend these tests to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:\n   237\t\n   238\t```python\n   239\tdef test_using_git_worktrees_is_thin_and_has_subagent_stop_block() -> None:\n   240\t    text = skill_text(\"using-git-worktrees\")\n   241\t    lines = text.splitlines()\n   242\t    assert len(lines) <= 40, (\n   243\t        f\"using-git-worktrees SKILL.md must be <=40 lines (spec §5.5); \"\n   244\t        f\"got {len(lines)}\"\n   245\t    )\n   246\t    assert \"<SUBAGENT-STOP>\" in text, \"missing <SUBAGENT-STOP> opening tag\"\n   247\t    assert \"</SUBAGENT-STOP>\" in text, \"missing </SUBAGENT-STOP> closing tag\"\n   248\t    # The block must precede the human-facing heading.\n   249\t    assert text.index(\"<SUBAGENT-STOP>\") < text.index(\"# Using Git Worktrees\")\n   250\t\n   251\t\n   252\tdef test_using_git_worktrees_points_at_tasktool_start() -> None:\n   253\t    text = skill_text(\"using-git-worktrees\")\n   254\t    assert \"tasktool start\" in text, \"skill must instruct calling tasktool start\"\n   255\t    assert \"--in-place\" in text, \"skill must document the --in-place opt-out\"\n   256\t\n   257\t\n   258\tdef test_using_git_worktrees_has_no_forbidden_sections() -> None:\n   259\t    text = skill_text(\"using-git-worktrees\")\n   260\t    forbidden = [\"## Quick Reference\", \"## Common Mistakes\", \"## Red Flags\",\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_3","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/tasklist.json | sed -n '250,390p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_3","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/tasklist.json | sed -n '250,390p'\"","aggregated_output":"   250\t  \"last_reviewed\": \"2026-05-18\",\n   251\t  \"north_star\": \"\",\n   252\t  \"phases\": [\n   253\t    {\n   254\t      \"closed\": null,\n   255\t      \"created\": \"2026-05-21\",\n   256\t      \"id\": \"P5\",\n   257\t      \"notes\": \"\",\n   258\t      \"phase_reviewer_chain\": \"docs/reviewer/p5-tasktool-worktree-lifecycle-design-spec\",\n   259\t      \"plan_path\": null,\n   260\t      \"planning_path\": null,\n   261\t      \"slices\": [\n   262\t        {\n   263\t          \"blocked_on\": null,\n   264\t          \"closed\": \"2026-05-21\",\n   265\t          \"created\": \"2026-05-21\",\n   266\t          \"depends_on\": [],\n   267\t          \"id\": \"S1\",\n   268\t          \"notes\": \"\",\n   269\t          \"parallel_group\": null,\n   270\t          \"plan_path\": \"docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md\",\n   271\t          \"planning_status\": \"proposed\",\n   272\t          \"refs\": [\n   273\t            \"docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md\",\n   274\t            \"docs/reviewer/p5-s1-tasktool-worktree-lifecycle-core-plan\"\n   275\t          ],\n   276\t          \"reviewer_chain\": \"docs/reviewer/p5-s1-tasktool-worktree-lifecycle-core-P5-S1-post-slice\",\n   277\t          \"started\": \"2026-05-21\",\n   278\t          \"status\": \"done\",\n   279\t          \"tasks\": [],\n   280\t          \"title\": \"Tasktool worktree lifecycle core\"\n   281\t        },\n   282\t        {\n   283\t          \"blocked_on\": null,\n   284\t          \"closed\": \"2026-05-21\",\n   285\t          \"created\": \"2026-05-21\",\n   286\t          \"depends_on\": [\n   287\t            \"P5.S1\"\n   288\t          ],\n   289\t          \"id\": \"S2\",\n   290\t          \"notes\": \"\",\n   291\t          \"parallel_group\": null,\n   292\t          \"plan_path\": \"docs/plans/2026-05-21-P5-S2-prune-and-repair.md\",\n   293\t          \"planning_status\": \"ratified\",\n   294\t          \"refs\": [\n   295\t            \"docs/plans/2026-05-21-P5-S2-prune-and-repair.md\",\n   296\t            \"docs/reviewer/p5-s2-prune-and-repair-plan\",\n   297\t            \"docs/reviewer/p5-s2-prune-and-repair-P5-S2-post-slice\"\n   298\t          ],\n   299\t          \"reviewer_chain\": \"docs/reviewer/p5-s2-prune-and-repair-P5-S2-post-slice\",\n   300\t          \"started\": \"2026-05-21\",\n   301\t          \"status\": \"done\",\n   302\t          \"tasks\": [],\n   303\t          \"title\": \"Prune + repair\",\n   304\t          \"worktree_branch\": \"worktree-P5.S2-prune-and-repair\",\n   305\t          \"worktree_path\": \".claude/worktrees/P5.S2-prune-and-repair\"\n   306\t        },\n   307\t        {\n   308\t          \"blocked_on\": null,\n   309\t          \"closed\": null,\n   310\t          \"created\": \"2026-05-21\",\n   311\t          \"depends_on\": [\n   312\t            \"P5.S1\",\n   313\t            \"P5.S2\"\n   314\t          ],\n   315\t          \"id\": \"S3\",\n   316\t          \"notes\": \"\",\n   317\t          \"parallel_group\": null,\n   318\t          \"plan_path\": \"docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md\",\n   319\t          \"planning_status\": \"proposed\",\n   320\t          \"refs\": [\n   321\t            \"docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md\",\n   322\t            \"docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-plan\"\n   323\t          ],\n   324\t          \"reviewer_chain\": \"docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-plan\",\n   325\t          \"started\": null,\n   326\t          \"status\": \"ready\",\n   327\t          \"tasks\": [],\n   328\t          \"title\": \"Skill rewrite + subagent guard + workflow updates\"\n   329\t        }\n   330\t      ],\n   331\t      \"spec_path\": \"docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md\",\n   332\t      \"started\": null,\n   333\t      \"status\": \"ready\",\n   334\t      \"title\": \"Tasktool-owned worktree lifecycle & using-git-worktrees skill collapse\"\n   335\t    }\n   336\t  ],\n   337\t  \"project\": \"superstar\",\n   338\t  \"schema_version\": 1\n   339\t}\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_4","type":"command_execution","command":"/usr/bin/zsh -lc 'rg -n \"P5.S3|Overall verdict|Verification|pytest|tasktool validate|tasktool close|worktree prune|SUPERSTAR_SUBAGENT_ROLE|Subagents must inherit\" docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md docs/tasklist.json'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_4","type":"command_execution","command":"/usr/bin/zsh -lc 'rg -n \"P5.S3|Overall verdict|Verification|pytest|tasktool validate|tasktool close|worktree prune|SUPERSTAR_SUBAGENT_ROLE|Subagents must inherit\" docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md docs/tasklist.json'","aggregated_output":"docs/tasklist.json:212:      \"notes\": \"Fixed tasktool close --refs parsing so repeated flags and comma-separated refs both record every path. Verified with focused red/green regressions and full tasktool test suite.\",\ndocs/tasklist.json:220:      \"title\": \"Fix tasktool close repeated refs parsing\"\ndocs/tasklist.json:226:      \"notes\": \"Publish scripts now maintain materialized versioned and current plugin cache directories for Claude and Codex, rewrite hook commands to current/, and refresh the global external-reviewer shim so project-level scripts do not need updating after version bumps.\\nImplemented stable materialized current/ entrypoints for local Claude and Codex plugin caches, updated external-reviewer shim installation to target current/, and verified Codex/Claude publish tests plus installer pytest and tasktool validate.\",\ndocs/tasklist.json:318:          \"plan_path\": \"docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md\",\ndocs/tasklist.json:321:            \"docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md\",\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:112:| Path present but not a linked worktree (e.g. plain dir) | Fail. Do not overwrite. Suggest `tasktool worktree prune <id> --force` then re-`start`. |\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:121:   1. `tasktool close <Xn> --no-archive` — required for ad-hoc rows. Flips status to `done` and leaves the row in `cross_cutting` with `worktree_path` / `worktree_branch` intact. **Defaulting `close` to auto-archive (current behavior for cross-cutting rows) would delete the row before prune could find it; the spec requires `--no-archive` rather than changing the existing default.**\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:122:   2. `tasktool worktree prune <Xn>` — standard three-guard prune; nulls worktree fields and records `worktree_pruned_at`.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:129:1. `SUPERSTAR_SUBAGENT_ROLE` env var set to any non-empty value. Set by the Superstar shim when a coordinator dispatches a subagent via the Claude `Task` tool or Codex `subagent` equivalent. This is the supported, harness-set signal.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:131:3. `SUPERSTAR_FORCE_SUBAGENT=1` env var. Test-only override; documented and used by P5.S3 fixtures.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:133:On any positive signal, `start` exits non-zero with: `\"Subagents must inherit the parent's worktree; call the parent or 'cd' into the existing recorded path: <worktree_path>.\"`\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:137:`SUPERSTAR_SUBAGENT_ROLE` is added to the Claude shim and Codex shim as part of P5.S3.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:139:#### `tasktool close <id>` — unchanged worktree semantics\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:141:**`tasktool close` does not touch the worktree.** Its existing meaning — review-gated slice closure run at slice boundary, before merge-back — is preserved unchanged. The slice's `worktree_path` / `worktree_branch` / `worktree_in_place` fields are retained verbatim across `close`, so `worktree list` continues to see the slice's worktree as a closed-but-retained row until it is explicitly pruned post-merge.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:143:This split is deliberate. `close` runs *before* merge-back in the established workflow (see `[[executing-plans]]`, `[[finishing-a-development-branch]]`), so it cannot enforce a merged-branch guard without breaking that workflow. Destructive cleanup is a separate operation owned by `tasktool worktree prune`.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:145:#### `tasktool worktree prune <id> [--keep-branch | --force]`\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:153:If any guard fails, prune is refused with a precise reason. **`--force` overrides prune guards only.** It does not affect `tasktool close`, slice status, review gates, dependency gates, or any other lifecycle concern — those keep their existing semantics. `--force` is the destructive escape hatch for the cleanup step alone.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:165:4. Prints the exact follow-up command to chat: `cd <authoritative-root> && git worktree remove <path> && tasktool worktree prune <id> --finalize`.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:169:1. `worktree_prune_pending: true` is set on the slice. Without it, `--finalize` refuses with: \"no pending prune to finalize; run `tasktool worktree prune <id>` first.\"\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:184:- `tasktool worktree prune <id> [--keep-branch | --force | --finalize]` — remove the recorded worktree. Applies the three guards described under `tasktool worktree prune` above (slice-done, branch-merged, clean-tree). `--force` overrides prune guards only; `--keep-branch` removes the directory but leaves the branch; `--finalize` records the post-prune field nulling without re-running guards when the directory was already removed externally (the prune-from-inside two-step).\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:198:| `worktree prune` (success) | nulled | nulled | unchanged | set to now | worktree removed; branch removed unless `--keep-branch` |\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:199:| `worktree prune` (prune-from-inside, before `--finalize`) | unchanged | unchanged | unchanged | absent | worktree still present; `worktree_prune_pending: true` set on slice |\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:200:| `worktree prune --finalize` (preconditions met) | nulled | nulled | unchanged | set to now | (caller already removed the worktree); `worktree_prune_pending` cleared |\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:201:| `worktree prune` on `--in-place` slice | unchanged (null) | unchanged (null) | unchanged (`true`) | set to now | no-op on disk |\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:206:| `worktree prune <ad-hoc-Xn>` | nulled | nulled | unchanged | set to now | worktree removed; row may later be archived via `archive-cross` |\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:210:This spec affects three existing skills. Updates land in P5.S3 alongside the `using-git-worktrees` rewrite:\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:212:- **`executing-plans`** — current text says \"run `tasktool close <slice-id>` at slice boundary.\" Unchanged in semantics; `close` still runs there and still does not touch the worktree. No edit required beyond cross-references.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:213:- **`finishing-a-development-branch`** — gains an explicit step: after the slice/phase branch is merged into the authoritative parent, run `tasktool worktree prune <id>` for each merged slice. The skill already runs at the right moment in the workflow; this adds the cleanup call.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:255:`tasktool worktree prune <id>` with all three guards (slice done, branch merged, clean tree). `--keep-branch` and `--force` (scoped to prune guards only). Prune-from-inside-worktree detection and the `--finalize` two-step. `tasktool worktree repair <id>`. Audit timestamp (`worktree_pruned_at`) on successful prune. Update `finishing-a-development-branch` to invoke `worktree prune` after merge-back.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:264:- `--force` overrides each prune guard individually; verify it does **not** affect `tasktool close`, slice status, or review gates.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:266:- Prune from inside the doomed worktree sets `worktree_prune_pending: true`, prints the exact `cd … && git worktree remove … && tasktool worktree prune <id> --finalize` line, and skips the destructive call.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:271:- Ad-hoc lifecycle end-to-end: `start --ad-hoc <slug>` creates an `X<n>` row, `close <Xn>` (without `--no-archive`) auto-archives and is blocked from being followed by prune (covers the foot-gun); `close <Xn> --no-archive` keeps the row active, `worktree prune <Xn>` succeeds, then `archive-cross <Xn>` archives the now-pruned row.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:275:### P5.S3 — Skill rewrite + subagent guard + workflow updates\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:277:Collapse `using-git-worktrees` to the structure in §5.5. Add the `tasklist-discipline` paragraph from §5.6. Apply the workflow updates from §5.3.2 to `executing-plans`, `finishing-a-development-branch`, and `subagent-driven-development`. Implement tasktool's three-signal subagent detection from §5.3 and the refusal message. Set `SUPERSTAR_SUBAGENT_ROLE` from the Claude shim and Codex shim when dispatching subagents. Move submodule guidance to `references/submodules.md`.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:281:- `tasktool start` refuses with the documented message when `SUPERSTAR_SUBAGENT_ROLE` is set.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:285:- Signal precedence: `SUPERSTAR_SUBAGENT_ROLE` wins over the other two when multiple are set.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:286:- Claude shim and Codex shim integration tests confirm `SUPERSTAR_SUBAGENT_ROLE` is exported in dispatched subagents and absent in coordinator sessions.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:308:3. `tasktool close <id>` is unchanged in semantics and never touches the worktree. Destructive cleanup happens only via `tasktool worktree prune <id>`.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:309:4. `tasktool worktree prune` cannot silently destroy uncommitted work. Each of the three guards (slice-done, branch-merged, clean-tree) is independently testable and `--force` is scoped to prune guards only — it never affects `close`, slice status, review gates, or dependency gates. The deferred in-flight-subagent concern is acknowledged in §8 and is not part of P5's safety claims.\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:315:## 10. Verification before implementation planning\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:319:- `tools/tasktool/tasktool validate --strict-format`\ndocs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:320:- `python -m pytest tools/tasktool/tests -q`\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1:# P5.S3 — Skill rewrite + subagent guard + workflow updates — Implementation Plan\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:5:**Goal:** Collapse `using-git-worktrees` to ≤40 lines around a subagent early-exit, teach `tasktool start` to refuse dispatched subagents via three env signals, and update the coordinator's dispatch prompt templates to instruct subagents to export `SUPERSTAR_SUBAGENT_ROLE` so the runtime guard has the highest practical chance of firing when subagents follow the directive.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:11:4. Coordinator-facing dispatch prompt updates: extend `skills/subagent-driven-development/implementer-prompt.md` (and the spec-reviewer / code-quality-reviewer prompt templates) to instruct each dispatched subagent to export `SUPERSTAR_SUBAGENT_ROLE=<role>` as its first shell command. This is a best-effort prose directive (Superstar does not wrap the harness's native dispatch tool), backed by the runtime guard in step 2 and the load-bearing prose rule in step 3. Tests assert the directive is present in every template and that a simulated `env -i bash` dispatch is correctly refused.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:14:**Tech Stack:** Python (3.10+) for tasktool, pytest for tests, bash for fixtures, plain Markdown for skill / template edits.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:19:- `finishing-a-development-branch` edits (post-merge prune step) — owned by P5.S2 per spec §5.3.2 (`:212-214`). The spec's P5.S3 slice paragraph at §6 (`:275-277`) lists all three workflow skills, but §5.3.2 splits ownership and assigns the prune step to P5.S2. Treat §5.3.2 as authoritative; this slice does not modify `finishing-a-development-branch`. Task 1.5 below verifies P5.S2 actually shipped the prune step before this slice starts so the workflow gap is not silently left open.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:22:**Shim scope (read this before Task 8).** The spec at `:137` and `:286` says \"the Claude shim and Codex shim\" export `SUPERSTAR_SUBAGENT_ROLE`. The Superstar repo does not currently wrap the harness's native dispatch tool (Claude Code's `Task`, Codex's `spawn_agent`) — there is no Python or JS interceptor between the harness and the subagent process where an env var could be injected programmatically. The honest implementation is therefore a **best-effort prose guard**: the coordinator's dispatch prompt templates instruct the subagent to export the variable as its first shell command. The runtime guard in `tasktool start` (Task 7) is the load-bearing safety net; the prose rule in `tasklist-discipline` (Task 9) is the load-bearing *cultural* rule. The prompt-template directive (Task 8) raises the probability that the runtime guard fires in real use, but does not guarantee it. Task 8 acknowledges this explicitly and adds a simulated-harness transcript test (Task 8 Step 8.5) to prove the dispatch-time refusal actually works in a realistic shell when the directive is followed. If a future harness change exposes a real env-injection point, that integration can be wired in without breaking either the runtime guard or the prose rule.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:27:tools/tasktool/tasktool show P5.S3\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:31:Expected: `P5.S3` exists with `status: ready`, `depends_on: [P5.S1, P5.S2]`, `planning_status: proposed`. After plan-review passes, the writing-plans flow will ratify (coordinator-side `tasktool ratify P5.S3 --parallel-group …` is **not** part of this plan — the coordinator owns ratification).\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:33:**Verification baseline (must pass against `main` before slice start, per spec §10):**\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:36:tools/tasktool/tasktool validate --strict-format\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:37:python -m pytest tools/tasktool/tests -q\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:48:| `skills/tasklist-discipline/SKILL.md` | append paragraph | Subagents must inherit cwd; never call `tasktool start`. |\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:51:| `skills/subagent-driven-development/implementer-prompt.md` | minor edits | Add explicit `SUPERSTAR_SUBAGENT_ROLE=implementer` directive in the dispatch template. |\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:58:| `tools/tasktool/tests/test_subagent_prompt_shim.py` | create | Assert each of the three subagent-prompt templates exports `SUPERSTAR_SUBAGENT_ROLE=<expected>`. |\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:69:tools/tasktool/tasktool show P5.S3\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:73:Expected: `P5.S3` exists with `depends_on: [P5.S1, P5.S2]`. If absent or differs, stop — coordinator needs to fix the row before this plan can execute.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:78:tools/tasktool/tasktool validate --strict-format\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:79:python -m pytest tools/tasktool/tests -q\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:87:tools/tasktool/tasktool start P5.S3\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:98:grep -nE \"tasktool worktree prune\" skills/finishing-a-development-branch/SKILL.md\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:101:Expected: `P5.S2` status is `done` (closed by P5.S2's external review gate), and `grep` returns at least one match showing the post-merge prune step. If `P5.S2` is not done, **stop** — this slice waits on it. If `P5.S2` is done but `finishing-a-development-branch` does not mention `tasktool worktree prune`, stop and surface the gap to the coordinator (this would be a P5.S2 closeout defect, not a P5.S3 problem to paper over).\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:189:**Opt-out:** For planning, spec, or design slices that touch no code, run `tasktool start <slice-id> --in-place`. The slice row records `worktree_in_place: true`; later `close` and `worktree prune` treat the slice as having no worktree.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:216:git commit -m \"P5.S3: rewrite using-git-worktrees skill to subagent early-exit + tasktool pointer\"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:281:python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -v\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:290:git commit -m \"P5.S3: test using-git-worktrees skill shape (length, stop-block, no forbidden sections)\"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:301:The spec §6 P5.S3 requires a concrete token-budget regression fixture so future edits cannot silently regrow the skill. Mechanism: freeze the post-rewrite body as a fixture file and assert the live skill matches it byte-for-byte, except for trailing whitespace normalisation. Future edits must consciously update the fixture, which is the audit trail.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:317:    in the same commit so the diff is visible in review. Spec P5.S3 §6.\"\"\"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:327:        \"using-git-worktrees SKILL.md drifted from the P5.S3 token-budget \"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:336:python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py::test_using_git_worktrees_matches_token_budget_fixture -v\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:345:git commit -m \"P5.S3: freeze using-git-worktrees skill body as token-budget regression fixture\"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:352:Spec §6 P5.S3 also asks for \"a representative subagent transcript that previously loaded the full skill now loads only the early-exit block.\" Task 5 covers the byte-for-byte body freeze (silent-growth detection); this task covers the **transcript-side behavior**: the bytes a subagent actually consumes when it follows the early-exit instruction.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:384:    \"\"\"Spec §6 P5.S3 transcript regression. A compliant subagent loads only\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:402:        \"subagent early-exit span drifted from the P5.S3 transcript fixture. \"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:421:python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py::test_subagent_early_exit_load_matches_fixture -v\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:430:git commit -m \"P5.S3: subagent early-exit transcript fixture + behavior regression test\"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:447:REFUSAL_MARKER = \"Subagents must inherit the parent's worktree\"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:452:    \"Subagents must inherit the parent's worktree; call the parent or \"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:480:        extra_env={\"SUPERSTAR_SUBAGENT_ROLE\": \"implementer\"},\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:491:            \"SUPERSTAR_SUBAGENT_ROLE\": None,\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:504:            \"SUPERSTAR_SUBAGENT_ROLE\": None,\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:516:            \"SUPERSTAR_SUBAGENT_ROLE\": None,\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:528:            \"SUPERSTAR_SUBAGENT_ROLE\": None,\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:544:            \"SUPERSTAR_SUBAGENT_ROLE\": None,\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:553:    \"\"\"When SUPERSTAR_SUBAGENT_ROLE is set, the refusal message must mention\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:560:            \"SUPERSTAR_SUBAGENT_ROLE\": \"implementer\",\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:565:        \"SUPERSTAR_SUBAGENT_ROLE must win over CLAUDE_AGENT_ROLE=coordinator\"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:578:        extra_env={\"SUPERSTAR_SUBAGENT_ROLE\": \"implementer\"},\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:597:    environment beyond PATH + PYTHONPATH. Spec §6 P5.S3 'no false positives\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:615:python -m pytest tools/tasktool/tests/test_lifecycle_start.py -k \"subagent or precedence or env_i_bash or plain_shell\" -v\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:637:    \"Subagents must inherit the parent's worktree; call the parent or \"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:647:      1. SUPERSTAR_SUBAGENT_ROLE  -- any non-empty value\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:653:    role = _os.environ.get(\"SUPERSTAR_SUBAGENT_ROLE\", \"\")\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:655:        return \"SUPERSTAR_SUBAGENT_ROLE\"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:701:- The spec's refusal sentence (`Subagents must inherit the parent's worktree; call the parent or 'cd' into the existing recorded path: <worktree_path>.`) is preserved **verbatim, including the trailing period**, as a substring of the emitted error. A `[signal: <name>]` suffix is appended after the period as structured diagnostics. The verbatim-substring assertion in Task 6 (`test_start_refusal_message_matches_spec_verbatim`) gates against drift on the spec sentence itself.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:706:python -m pytest tools/tasktool/tests/test_lifecycle_start.py -v\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:714:python -m pytest tools/tasktool/tests -q\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:717:Expected: green. If a pre-existing test that calls `tasktool start` in a fixture that happens to have `CLAUDE_AGENT_ROLE` set in the test runner's env starts failing, fix the test by setting `SUPERSTAR_SUBAGENT_ROLE`/`CLAUDE_AGENT_ROLE` to `None` in its env explicitly — the guard is intentionally strict.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:723:git commit -m \"P5.S3: refuse tasktool start when invoked as a dispatched subagent (three env signals)\"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:728:## Task 8: Update subagent-dispatch prompt templates to export `SUPERSTAR_SUBAGENT_ROLE`\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:736:Background: there is no native env-injection point on Claude Code's `Task` tool. The closest analogue to a \"shim\" in this repo is the coordinator-facing prompt template in `skills/subagent-driven-development/*-prompt.md`. We extend those templates with an explicit directive: the dispatched subagent exports `SUPERSTAR_SUBAGENT_ROLE=<role>` in its shell session before running tooling. The shim test asserts the directive is present and names a non-empty role; the runtime guard in Task 7 catches the env var when it is set.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:749:    export SUPERSTAR_SUBAGENT_ROLE=implementer\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:765:export SUPERSTAR_SUBAGENT_ROLE=spec-reviewer\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:771:export SUPERSTAR_SUBAGENT_ROLE=code-quality-reviewer\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:779:\"\"\"Spec §6 P5.S3 \"Claude shim and Codex shim integration tests confirm\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:780:SUPERSTAR_SUBAGENT_ROLE is exported in dispatched subagents and absent in\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:786:to export SUPERSTAR_SUBAGENT_ROLE=<role> as their first shell command. These\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:806:        expected = f\"export SUPERSTAR_SUBAGENT_ROLE={role}\"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:826:    \"\"\"The coordinator must NOT export SUPERSTAR_SUBAGENT_ROLE in its own\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:830:    assert \"export SUPERSTAR_SUBAGENT_ROLE\" not in skill, (\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:832:        \"coordinator to export SUPERSTAR_SUBAGENT_ROLE for itself\"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:854:    2. The subagent runs `export SUPERSTAR_SUBAGENT_ROLE=implementer` as its\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:882:        f\"export SUPERSTAR_SUBAGENT_ROLE=implementer && \"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:898:        \"Subagents must inherit the parent's worktree; call the parent or \"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:909:    SUPERSTAR_SUBAGENT_ROLE (i.e. did not run the dispatched-subagent\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:911:    down 'absent in coordinator sessions' from spec §6 P5.S3.\"\"\"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:938:        f\"coordinator (no SUPERSTAR_SUBAGENT_ROLE) should have proceeded; \"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:948:python -m pytest tools/tasktool/tests/test_subagent_prompt_shim.py -v\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:960:git commit -m \"P5.S3: dispatched-subagent prompts export SUPERSTAR_SUBAGENT_ROLE; add shim presence tests\"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:973:**Subagent rule (load-bearing).** Parents create or adopt worktrees via `tasktool start <slice-id>`. Dispatched subagents inherit the parent's cwd and **must not** call `tasktool start` — implementation work happens inside the parent's already-recorded worktree, and a subagent starting a slice double-counts the lifecycle row and corrupts the slice's worktree fields. Tasktool refuses `tasktool start` when it observes a dispatched-subagent signal (`SUPERSTAR_SUBAGENT_ROLE`, `CLAUDE_AGENT_ROLE`, or the test-only `SUPERSTAR_FORCE_SUBAGENT=1`). The runtime guard is detection-dependent — a coordinator that loses its env (e.g. `env -i`) will look like a top-level invocation — so **this prose rule is the load-bearing guard**; the env signals are belt-and-braces.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:992:git commit -m \"P5.S3: tasklist-discipline forbids subagent tasktool start (load-bearing prose rule)\"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1027:**Subagents inherit your cwd and must not call `tasktool start`.** The implementer/spec-reviewer/code-quality-reviewer prompt templates already export `SUPERSTAR_SUBAGENT_ROLE` so tasktool refuses subagent-side `start` calls; see `[[tasklist-discipline]]` \"Subagent rule\" for the load-bearing prose rule.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1038:- [ ] **Step 10.4: Run the full pytest suite once more**\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1041:python -m pytest tools/tasktool/tests -q\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1050:git commit -m \"P5.S3: cross-reference rewritten using-git-worktrees skill from executing-plans and subagent-driven-development\"\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1059:- [ ] **Step 11.1: Re-run validate and the full pytest suite**\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1062:tools/tasktool/tasktool validate --strict-format\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1063:python -m pytest tools/tasktool/tests -q\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1075:grep -c \"export SUPERSTAR_SUBAGENT_ROLE=implementer\" skills/subagent-driven-development/implementer-prompt.md\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1076:grep -c \"export SUPERSTAR_SUBAGENT_ROLE=spec-reviewer\" skills/subagent-driven-development/spec-reviewer-prompt.md\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1077:grep -c \"export SUPERSTAR_SUBAGENT_ROLE=code-quality-reviewer\" skills/subagent-driven-development/code-quality-reviewer-prompt.md\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1084:Do **not** run `tasktool close P5.S3` yet. Slice close is gated by `[[external-review]] --kind post-slice` per the coordinator's workflow, which happens outside this implementation plan. Hand the slice back to the coordinator with a summary of the commits and `git status` clean.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1104:| §5.3 `SUPERSTAR_SUBAGENT_ROLE` shim export | Task 8 (best-effort prose guard via prompt templates + presence tests + simulated dispatch transcript test). See \"Shim scope\" preamble for the limits of this implementation. |\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1105:| §6 P5.S3 skill body ≤ 40 lines + `<SUBAGENT-STOP>` test | Task 4 |\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1106:| §6 P5.S3 token-budget regression — silent-growth detection | Task 5 (`tools/tasktool/tests/fixtures/p5_s3_skill_body.txt` + byte-for-byte diff test) |\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1107:| §6 P5.S3 token-budget regression — subagent transcript behavior | Task 5b (`tools/tasktool/tests/fixtures/p5_s3_subagent_load.txt` + early-exit span behavior test) |\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1108:| §6 P5.S3 \"exported in dispatched subagents, absent in coordinator\" | Task 8 Step 8.5 (`test_simulated_subagent_dispatch_refuses_tasktool_start` + `test_simulated_coordinator_dispatch_proceeds`) |\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1114:**4. Scheduling check:** `tasktool show P5.S3` confirms `depends_on: [P5.S1, P5.S2]`, `planning_status: proposed`. The plan does not change the dependency graph; no `tasktool deps` mutation is required. Ratification (`tasktool ratify`) is the coordinator's responsibility after this plan passes external review.\ndocs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1121:- §5.3.2 of the spec (`:212-214`) and the P5.S3 slice description (`:275-277`) disagree about who owns the `finishing-a-development-branch` edit. The plan treats §5.3.2 as authoritative (P5.S2 owns it) and adds Task 1.4 to verify P5.S2 actually shipped that edit before this slice runs. If P5.S2 closed without it, this slice stops and surfaces the gap rather than papering over it.\n","exit_code":0,"status":"completed"}}
+{"type":"item.completed","item":{"id":"item_5","type":"agent_message","text":"I found the worktree itself has an untracked reviewer output directory, and the tasklist still shows P5.S3 as `ready` with the plan reviewer chain, not a closed post-slice chain. I’m checking the actual implementation files next to distinguish a review artifact issue from an incomplete slice."}}
+{"type":"item.started","item":{"id":"item_6","type":"command_execution","command":"/usr/bin/zsh -lc 'git log --oneline --decorate -12'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_6","type":"command_execution","command":"/usr/bin/zsh -lc 'git log --oneline --decorate -12'","aggregated_output":"dc72ac8 (HEAD -> worktree-p5-s3-skill-rewrite-subagent-guard-workflow) P5.S3: cross-reference rewritten using-git-worktrees skill from executing-plans and subagent-driven-development\nd9ba7c0 P5.S3: tasklist-discipline forbids subagent tasktool start (load-bearing prose rule)\n8d021ed P5.S3: dispatched-subagent prompts export SUPERSTAR_SUBAGENT_ROLE; add shim presence tests\n0c14583 P5.S3: refuse tasktool start when invoked as a dispatched subagent (three env signals)\n9151183 P5.S3: freeze using-git-worktrees skill body + subagent early-exit span as regression fixtures\n204f76f P5.S3: test using-git-worktrees skill shape (length, stop-block, no forbidden sections)\n1d1eeb7 P5.S3: rewrite using-git-worktrees skill to subagent early-exit + tasktool pointer\n946b6ad (main) Merge P5.S2: prune + repair\nb7fa0af P5.S2: close slice\nb946205 P5.S2: post-slice review chain (r1 revise → r3 ready w/ small edits)\n1a5e738 P5.S2: tasklist — ratify + start mutations\n377f93d P5.S2: post-slice r3 — ready with small edits (no required edits)\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_7","type":"command_execution","command":"/usr/bin/zsh -lc \"rg --files skills/using-git-worktrees skills/tasklist-discipline skills/executing-plans skills/subagent-driven-development tools/tasktool/tests tools/tasktool | rg 'using-git-worktrees|subagent_prompt|lifecycle_start|skill_tasktool|commands.py|prompt.md|p5_s3'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_7","type":"command_execution","command":"/usr/bin/zsh -lc \"rg --files skills/using-git-worktrees skills/tasklist-discipline skills/executing-plans skills/subagent-driven-development tools/tasktool/tests tools/tasktool | rg 'using-git-worktrees|subagent_prompt|lifecycle_start|skill_tasktool|commands.py|prompt.md|p5_s3'\"","aggregated_output":"skills/subagent-driven-development/code-quality-reviewer-prompt.md\nskills/subagent-driven-development/implementer-prompt.md\nskills/subagent-driven-development/spec-reviewer-prompt.md\ntools/tasktool/commands.py\nskills/using-git-worktrees/SKILL.md\nskills/using-git-worktrees/references/submodules.md\ntools/tasktool/tests/test_subagent_prompt_shim.py\ntools/tasktool/tests/test_commands.py\ntools/tasktool/tests/test_commands.py\ntools/tasktool/tests/test_subagent_prompt_shim.py\ntools/tasktool/tests/test_lifecycle_start.py\ntools/tasktool/tests/test_worktree_subcommands.py\ntools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py\ntools/tasktool/tests/test_lifecycle_start.py\ntools/tasktool/tests/test_worktree_subcommands.py\ntools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py\ntools/tasktool/tests/fixtures/p5_s3_skill_body.txt\ntools/tasktool/tests/fixtures/p5_s3_subagent_load.txt\ntools/tasktool/tests/fixtures/p5_s3_subagent_load.txt\ntools/tasktool/tests/fixtures/p5_s3_skill_body.txt\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_8","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba skills/using-git-worktrees/SKILL.md && wc -l skills/using-git-worktrees/SKILL.md && nl -ba skills/using-git-worktrees/references/submodules.md | sed -n '1,120p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_8","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba skills/using-git-worktrees/SKILL.md && wc -l skills/using-git-worktrees/SKILL.md && nl -ba skills/using-git-worktrees/references/submodules.md | sed -n '1,120p'\"","aggregated_output":"     1\t---\n     2\tname: using-git-worktrees\n     3\tdescription: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - ensures an isolated workspace exists via native tools or git worktree fallback\n     4\t---\n     5\t\n     6\t<SUBAGENT-STOP>\n     7\tYou were dispatched as a subagent. The parent coordinator has already created or adopted the worktree for the active slice and `cd`d you into it. Do not read or apply the rest of this skill, and do not call `tasktool start`. If `git rev-parse --git-dir` differs from `git rev-parse --git-common-dir` (and you are not inside a submodule — see `references/submodules.md` if uncertain), you are inside the parent's linked worktree; proceed with your task. If they match, you are in a plain checkout; ask the parent before editing files.\n     8\t</SUBAGENT-STOP>\n     9\t\n    10\t# Using Git Worktrees\n    11\t\n    12\t**Announce at start:** \"I'm using the using-git-worktrees skill to enter the slice worktree.\"\n    13\t\n    14\t**Rule:** Implementation slice/task work runs in an isolated linked worktree owned by tasktool. A plain `main`/`master` checkout is planning/read-only by default unless the human partner opts out of isolation in the current turn.\n    15\t\n    16\t**Run:** `tasktool start <slice-id>` from the authoritative checkout (or from an already-linked worktree of the same repo — tasktool will auto-adopt). It creates the worktree at `.worktrees/worktree-<id>-<slug>`, records the path and branch on the slice row, and prints the `cd` line. Idempotent: a consistent recorded path is a no-op. See `[[tasklist-discipline]]` for the lifecycle commands and the routing rules.\n    17\t\n    18\t**Opt-out:** For planning, spec, or design slices that touch no code, run `tasktool start <slice-id> --in-place`. The slice row records `worktree_in_place: true`; later `close` and `worktree prune` treat the slice as having no worktree.\n    19\t\n    20\t**Drift:** If `tasktool start` reports a conflict (path missing, branch mismatched, plain-dir collision), run the exact `tasktool worktree {adopt,repair,prune --force}` command it prints. Do not improvise with raw `git worktree` invocations; do not delete `.worktrees/` directories by hand.\n    21\t\n    22\tFor submodule-vs-worktree disambiguation, see `references/submodules.md`.\n22 skills/using-git-worktrees/SKILL.md\n     1\t# Submodule guard for using-git-worktrees\n     2\t\n     3\tLoad this reference **only** when `tasktool start` reports a worktree-detection conflict caused by a submodule, or when the early-exit block in `SKILL.md` cannot decide whether the current directory is a linked worktree or a submodule checkout.\n     4\t\n     5\t## Why this matters\n     6\t\n     7\t`GIT_DIR != GIT_COMMON_DIR` is true in two distinct situations:\n     8\t\n     9\t1. The current directory is a linked git worktree (e.g. `.worktrees/worktree-p5-s3-…`).\n    10\t2. The current directory is a git submodule checkout.\n    11\t\n    12\tThe submodule case must **not** be treated as a worktree. Treating a submodule as a linked worktree skips legitimate worktree creation and corrupts the slice's evidence boundary.\n    13\t\n    14\t## Disambiguating\n    15\t\n    16\tRun:\n    17\t\n    18\t```sh\n    19\tgit rev-parse --show-superproject-working-tree 2>/dev/null\n    20\t```\n    21\t\n    22\t- Empty output (or non-zero exit): you are **not** in a submodule. The `GIT_DIR != GIT_COMMON_DIR` signal is genuine — treat the directory as a linked worktree.\n    23\t- Non-empty output (a path): you are inside a submodule of that superproject. Treat the directory as a normal repo checkout and do not skip the worktree creation step.\n    24\t\n    25\t## What to do\n    26\t\n    27\tIf you discover you are in a submodule and tasktool refuses to proceed, leave the submodule (`cd` to the superproject root, or to the authoritative checkout) and re-run `tasktool start <id>` from there. Do not attempt to nest a worktree inside the submodule.\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_9","type":"command_execution","command":"/usr/bin/zsh -lc 'rg -n \"SUPERSTAR_SUBAGENT_ROLE|CLAUDE_AGENT_ROLE|SUPERSTAR_FORCE_SUBAGENT|Subagents must inherit|_detect_subagent|tasktool start\" tools/tasktool/commands.py tools/tasktool/tests/test_lifecycle_start.py tools/tasktool/tests/test_subagent_prompt_shim.py skills/tasklist-discipline/SKILL.md skills/executing-plans/SKILL.md skills/subagent-driven-development/SKILL.md skills/subagent-driven-development/*-prompt.md'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_9","type":"command_execution","command":"/usr/bin/zsh -lc 'rg -n \"SUPERSTAR_SUBAGENT_ROLE|CLAUDE_AGENT_ROLE|SUPERSTAR_FORCE_SUBAGENT|Subagents must inherit|_detect_subagent|tasktool start\" tools/tasktool/commands.py tools/tasktool/tests/test_lifecycle_start.py tools/tasktool/tests/test_subagent_prompt_shim.py skills/tasklist-discipline/SKILL.md skills/executing-plans/SKILL.md skills/subagent-driven-development/SKILL.md skills/subagent-driven-development/*-prompt.md'","aggregated_output":"skills/subagent-driven-development/spec-reviewer-prompt.md:19:    export SUPERSTAR_SUBAGENT_ROLE=spec-reviewer\nskills/subagent-driven-development/spec-reviewer-prompt.md:23:    `tasktool start <id>` (slice creation belongs to the parent). Do not\nskills/subagent-driven-development/spec-reviewer-prompt.md:24:    unset it; do not start the slice yourself; do not run `tasktool start`\nskills/subagent-driven-development/code-quality-reviewer-prompt.md:19:  export SUPERSTAR_SUBAGENT_ROLE=code-quality-reviewer\nskills/subagent-driven-development/code-quality-reviewer-prompt.md:23:  `tasktool start <id>` (slice creation belongs to the parent). Do not\nskills/subagent-driven-development/code-quality-reviewer-prompt.md:24:  unset it; do not start the slice yourself; do not run `tasktool start`\nskills/subagent-driven-development/implementer-prompt.md:25:    export SUPERSTAR_SUBAGENT_ROLE=implementer\nskills/subagent-driven-development/implementer-prompt.md:29:    `tasktool start <id>` (slice creation belongs to the parent). Do not\nskills/subagent-driven-development/implementer-prompt.md:30:    unset it; do not start the slice yourself; do not run `tasktool start`\nskills/subagent-driven-development/SKILL.md:33:For each active slice, the coordinator must run `tasktool start <slice-id>` before dispatching implementation. This is the lifecycle gate that records the start and moves the row to `in_progress`; do not substitute prose notes, TodoWrite state, or manual JSON edits.\nskills/subagent-driven-development/SKILL.md:37:**Subagents inherit your cwd and must not call `tasktool start`.** The implementer/spec-reviewer/code-quality-reviewer prompt templates already export `SUPERSTAR_SUBAGENT_ROLE` so tasktool refuses subagent-side `start` calls; see `[[tasklist-discipline]]` \"Subagent rule\" for the load-bearing prose rule.\nskills/executing-plans/SKILL.md:20:Before reading the plan as executable work, run `[[using-git-worktrees]]` as the first executable gate. The parent coordinator (you) creates or adopts the slice worktree via `tasktool start <slice-id>` — that single command is the lifecycle gate. Verify one of these is true:\nskills/executing-plans/SKILL.md:23:- You ran `tasktool start <slice-id>` and `cd`d into the printed path.\nskills/executing-plans/SKILL.md:25:Subagents dispatched by you inherit cwd and must not call `tasktool start` themselves — see `[[tasklist-discipline]]` \"Subagent rule (load-bearing)\" and the `<SUBAGENT-STOP>` block at the top of `[[using-git-worktrees]]`.\nskills/executing-plans/SKILL.md:42:1. If this is the first task for a slice, run `tasktool start <slice-id>` before implementation\nskills/tasklist-discipline/SKILL.md:19:- About to start implementation for a slice → `tasktool start <slice-id>`. This records the lifecycle start and moves the row to `in_progress`; do this before dispatching implementation or editing implementation files.\nskills/tasklist-discipline/SKILL.md:28:**Implementation isolation boundary:** If tasklist work is tied to starting, continuing, reviewing, or closing an implementation slice, invoke `[[using-git-worktrees]]` before tasktool status/ref/note/close mutations for an active implementation slice. `tasktool start`, `tasktool set`, `tasktool ref`, `tasktool note`, `tasktool close`, and reviewer-chain registration are not harmless bookkeeping when run from a shared checkout: they dirty the slice evidence set. A normal `main`/`master` checkout is planning/setup/read-only by default unless the user explicitly opts out of isolation in the current turn. Invoke `tasktool` from the active implementation worktree; authoritative routing sends the mutation to the configured checkout.\nskills/tasklist-discipline/SKILL.md:30:**Subagent rule (load-bearing).** Parents create or adopt worktrees via `tasktool start <slice-id>`. Dispatched subagents inherit the parent's cwd and **must not** call `tasktool start` — implementation work happens inside the parent's already-recorded worktree, and a subagent starting a slice double-counts the lifecycle row and corrupts the slice's worktree fields. Tasktool refuses `tasktool start` when it observes a dispatched-subagent signal (`SUPERSTAR_SUBAGENT_ROLE`, `CLAUDE_AGENT_ROLE`, or the test-only `SUPERSTAR_FORCE_SUBAGENT=1`). The runtime guard is detection-dependent — a coordinator that loses its env (e.g. `env -i`) will look like a top-level invocation — so **this prose rule is the load-bearing guard**; the env signals are belt-and-braces.\nskills/tasklist-discipline/SKILL.md:45:Status enum: `ready | in_progress | blocked | done`. Only slices may take `blocked` (and only via `tasktool block <slice-id> --on …`). Emoji are a render concern; `tasktool render` and `tasktool brief` handle that. `tasktool start <slice-id>` is the normal way to enter `in_progress`; `tasktool set <id> --status in_progress` is a compatibility alias for older plans and ad-hoc rows. `tasktool unblock <slice-id> --resume` resumes through the same lifecycle path and stamps `started` when needed. `done` requires `closed`; the CLI stamps it.\nskills/tasklist-discipline/SKILL.md:60:tools/tasktool/tasktool start <slice-id>      # lifecycle start + in_progress\ntools/tasktool/tests/test_subagent_prompt_shim.py:2:the subagent to export SUPERSTAR_SUBAGENT_ROLE, and that the coordinator's\ntools/tasktool/tests/test_subagent_prompt_shim.py:23:        expected = f\"export SUPERSTAR_SUBAGENT_ROLE={role}\"\ntools/tasktool/tests/test_subagent_prompt_shim.py:33:        assert (\"do not run `tasktool start`\" in text or\ntools/tasktool/tests/test_subagent_prompt_shim.py:34:                \"do not call `tasktool start`\" in text or\ntools/tasktool/tests/test_subagent_prompt_shim.py:37:            f\"calling tasktool start\"\ntools/tasktool/tests/test_subagent_prompt_shim.py:43:    assert \"export SUPERSTAR_SUBAGENT_ROLE\" not in skill, (\ntools/tasktool/tests/test_subagent_prompt_shim.py:45:        \"coordinator to export SUPERSTAR_SUBAGENT_ROLE for itself\"\ntools/tasktool/tests/test_subagent_prompt_shim.py:73:        f\"export SUPERSTAR_SUBAGENT_ROLE=implementer && \"\ntools/tasktool/tests/test_subagent_prompt_shim.py:89:        \"Subagents must inherit the parent's worktree; call the parent or \"\ntools/tasktool/tests/test_subagent_prompt_shim.py:112:        f\"coordinator (no SUPERSTAR_SUBAGENT_ROLE) should have proceeded; \"\ntools/tasktool/commands.py:682:    \"Subagents must inherit the parent's worktree; call the parent or \"\ntools/tasktool/commands.py:692:      1. SUPERSTAR_SUBAGENT_ROLE  -- any non-empty value\ntools/tasktool/commands.py:693:      2. CLAUDE_AGENT_ROLE        -- any value other than 'coordinator' / 'main'\ntools/tasktool/commands.py:694:      3. SUPERSTAR_FORCE_SUBAGENT -- value == '1' (test-only override)\ntools/tasktool/commands.py:698:    role = _os.environ.get(\"SUPERSTAR_SUBAGENT_ROLE\", \"\")\ntools/tasktool/commands.py:700:        return \"SUPERSTAR_SUBAGENT_ROLE\"\ntools/tasktool/commands.py:701:    claude_role = _os.environ.get(\"CLAUDE_AGENT_ROLE\", \"\").strip().lower()\ntools/tasktool/commands.py:703:        return \"CLAUDE_AGENT_ROLE\"\ntools/tasktool/commands.py:704:    if _os.environ.get(\"SUPERSTAR_FORCE_SUBAGENT\", \"\") == \"1\":\ntools/tasktool/commands.py:705:        return \"SUPERSTAR_FORCE_SUBAGENT\"\ntools/tasktool/commands.py:958:                    f\"{qid} must be started before close; run `tasktool start {qid}` first, \"\ntools/tasktool/commands.py:993:                raise CommandError(f\"{qid} must be started before close; run `tasktool start {qid}` first\")\ntools/tasktool/tests/test_lifecycle_start.py:147:    assert \"tasktool start P1.S1\" in r.stderr\ntools/tasktool/tests/test_lifecycle_start.py:209:REFUSAL_MARKER = \"Subagents must inherit the parent's worktree\"\ntools/tasktool/tests/test_lifecycle_start.py:212:    \"Subagents must inherit the parent's worktree; call the parent or \"\ntools/tasktool/tests/test_lifecycle_start.py:238:        extra_env={\"SUPERSTAR_SUBAGENT_ROLE\": \"implementer\"},\ntools/tasktool/tests/test_lifecycle_start.py:249:            \"SUPERSTAR_SUBAGENT_ROLE\": None,\ntools/tasktool/tests/test_lifecycle_start.py:250:            \"CLAUDE_AGENT_ROLE\": \"subagent\",\ntools/tasktool/tests/test_lifecycle_start.py:262:            \"SUPERSTAR_SUBAGENT_ROLE\": None,\ntools/tasktool/tests/test_lifecycle_start.py:263:            \"CLAUDE_AGENT_ROLE\": \"coordinator\",\ntools/tasktool/tests/test_lifecycle_start.py:274:            \"SUPERSTAR_SUBAGENT_ROLE\": None,\ntools/tasktool/tests/test_lifecycle_start.py:275:            \"CLAUDE_AGENT_ROLE\": \"main\",\ntools/tasktool/tests/test_lifecycle_start.py:286:            \"SUPERSTAR_SUBAGENT_ROLE\": None,\ntools/tasktool/tests/test_lifecycle_start.py:287:            \"CLAUDE_AGENT_ROLE\": None,\ntools/tasktool/tests/test_lifecycle_start.py:288:            \"SUPERSTAR_FORCE_SUBAGENT\": \"1\",\ntools/tasktool/tests/test_lifecycle_start.py:300:            \"SUPERSTAR_SUBAGENT_ROLE\": None,\ntools/tasktool/tests/test_lifecycle_start.py:301:            \"CLAUDE_AGENT_ROLE\": None,\ntools/tasktool/tests/test_lifecycle_start.py:302:            \"SUPERSTAR_FORCE_SUBAGENT\": None,\ntools/tasktool/tests/test_lifecycle_start.py:313:            \"SUPERSTAR_SUBAGENT_ROLE\": \"implementer\",\ntools/tasktool/tests/test_lifecycle_start.py:314:            \"CLAUDE_AGENT_ROLE\": \"coordinator\",\ntools/tasktool/tests/test_lifecycle_start.py:318:        \"SUPERSTAR_SUBAGENT_ROLE must win over CLAUDE_AGENT_ROLE=coordinator\"\ntools/tasktool/tests/test_lifecycle_start.py:327:        extra_env={\"SUPERSTAR_SUBAGENT_ROLE\": \"implementer\"},\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_10","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba tools/tasktool/tests/test_subagent_prompt_shim.py | sed -n '1,140p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_10","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba tools/tasktool/tests/test_subagent_prompt_shim.py | sed -n '1,140p'\"","aggregated_output":"     1\t\"\"\"Spec §6 P5.S3: assert each dispatched-subagent prompt template instructs\n     2\tthe subagent to export SUPERSTAR_SUBAGENT_ROLE, and that the coordinator's\n     3\town SKILL.md does NOT set the same variable for itself.\"\"\"\n     4\tfrom __future__ import annotations\n     5\tfrom pathlib import Path\n     6\t\n     7\timport os\n     8\timport subprocess\n     9\timport sys\n    10\t\n    11\tPROMPTS = Path(__file__).resolve().parents[3] / \"skills\" / \"subagent-driven-development\"\n    12\t\n    13\tEXPECTED = {\n    14\t    \"implementer-prompt.md\": \"implementer\",\n    15\t    \"spec-reviewer-prompt.md\": \"spec-reviewer\",\n    16\t    \"code-quality-reviewer-prompt.md\": \"code-quality-reviewer\",\n    17\t}\n    18\t\n    19\t\n    20\tdef test_each_subagent_prompt_exports_subagent_role():\n    21\t    for fname, role in EXPECTED.items():\n    22\t        text = (PROMPTS / fname).read_text()\n    23\t        expected = f\"export SUPERSTAR_SUBAGENT_ROLE={role}\"\n    24\t        assert expected in text, (\n    25\t            f\"{fname} must contain `{expected}` so dispatched subagents \"\n    26\t            f\"trigger the tasktool subagent guard (spec §5.3).\"\n    27\t        )\n    28\t\n    29\t\n    30\tdef test_each_subagent_prompt_forbids_calling_tasktool_start():\n    31\t    for fname in EXPECTED:\n    32\t        text = (PROMPTS / fname).read_text().lower()\n    33\t        assert (\"do not run `tasktool start`\" in text or\n    34\t                \"do not call `tasktool start`\" in text or\n    35\t                \"do not start the slice yourself\" in text), (\n    36\t            f\"{fname} must explicitly forbid the dispatched subagent from \"\n    37\t            f\"calling tasktool start\"\n    38\t        )\n    39\t\n    40\t\n    41\tdef test_coordinator_skill_does_not_set_subagent_role_for_itself():\n    42\t    skill = (PROMPTS / \"SKILL.md\").read_text()\n    43\t    assert \"export SUPERSTAR_SUBAGENT_ROLE\" not in skill, (\n    44\t        \"subagent-driven-development SKILL.md must not instruct the \"\n    45\t        \"coordinator to export SUPERSTAR_SUBAGENT_ROLE for itself\"\n    46\t    )\n    47\t\n    48\t\n    49\tPYTHONPATH_REPO = str(Path(__file__).resolve().parents[2])\n    50\tTASKTOOL_MAIN = Path(__file__).resolve().parents[2] / \"tasktool\" / \"__main__.py\"\n    51\t\n    52\t\n    53\tdef _seed_tmp(tmp_path, env_extra=None):\n    54\t    (tmp_path / \"docs\").mkdir()\n    55\t    def _seed(*args):\n    56\t        env = {\"PATH\": os.environ.get(\"PATH\", \"\"), \"PYTHONPATH\": PYTHONPATH_REPO}\n    57\t        if env_extra:\n    58\t            env.update(env_extra)\n    59\t        return subprocess.run(\n    60\t            [sys.executable, str(TASKTOOL_MAIN),\n    61\t             \"--project-root\", str(tmp_path), *args],\n    62\t            env=env, text=True, capture_output=True,\n    63\t        )\n    64\t    assert _seed(\"config\", \"init-local\").returncode == 0\n    65\t    assert _seed(\"init\", \"--project\", \"demo\").returncode == 0\n    66\t    assert _seed(\"create\", \"phase\", \"--title\", \"Phase\").returncode == 0\n    67\t    assert _seed(\"create\", \"slice\", \"P1\", \"--title\", \"Slice\").returncode == 0\n    68\t\n    69\t\n    70\tdef test_simulated_subagent_dispatch_refuses_tasktool_start(tmp_path):\n    71\t    _seed_tmp(tmp_path)\n    72\t    script = (\n    73\t        f\"export SUPERSTAR_SUBAGENT_ROLE=implementer && \"\n    74\t        f\"{sys.executable} {TASKTOOL_MAIN} \"\n    75\t        f\"--project-root {tmp_path} start P1.S1\"\n    76\t    )\n    77\t    r = subprocess.run(\n    78\t        [\"env\", \"-i\",\n    79\t         f\"PATH={os.environ.get('PATH','')}\",\n    80\t         f\"PYTHONPATH={PYTHONPATH_REPO}\",\n    81\t         \"bash\", \"-c\", script],\n    82\t        text=True, capture_output=True,\n    83\t    )\n    84\t    assert r.returncode != 0, (\n    85\t        f\"simulated subagent should have been refused; stdout={r.stdout!r} \"\n    86\t        f\"stderr={r.stderr!r}\"\n    87\t    )\n    88\t    spec_sentence = (\n    89\t        \"Subagents must inherit the parent's worktree; call the parent or \"\n    90\t        \"'cd' into the existing recorded path: <not recorded>.\"\n    91\t    )\n    92\t    assert spec_sentence in (r.stdout + r.stderr), (\n    93\t        f\"refusal did not carry the spec sentence verbatim; \"\n    94\t        f\"got: {r.stdout + r.stderr!r}\"\n    95\t    )\n    96\t\n    97\t\n    98\tdef test_simulated_coordinator_dispatch_proceeds(tmp_path):\n    99\t    _seed_tmp(tmp_path)\n   100\t    script = (\n   101\t        f\"{sys.executable} {TASKTOOL_MAIN} \"\n   102\t        f\"--project-root {tmp_path} start P1.S1\"\n   103\t    )\n   104\t    r = subprocess.run(\n   105\t        [\"env\", \"-i\",\n   106\t         f\"PATH={os.environ.get('PATH','')}\",\n   107\t         f\"PYTHONPATH={PYTHONPATH_REPO}\",\n   108\t         \"bash\", \"-c\", script],\n   109\t        text=True, capture_output=True,\n   110\t    )\n   111\t    assert r.returncode == 0, (\n   112\t        f\"coordinator (no SUPERSTAR_SUBAGENT_ROLE) should have proceeded; \"\n   113\t        f\"stdout={r.stdout!r} stderr={r.stderr!r}\"\n   114\t    )\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_11","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba tools/tasktool/commands.py | sed -n '670,735p' && nl -ba tools/tasktool/commands.py | sed -n '760,830p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_11","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba tools/tasktool/commands.py | sed -n '670,735p' && nl -ba tools/tasktool/commands.py | sed -n '760,830p'\"","aggregated_output":"   670\t            id=item.id,\n   671\t            title=item.title,\n   672\t            archived_path=archive_rel,\n   673\t            archived_date=_today(),\n   674\t        )\n   675\t    )\n   676\t    validate_project(p)\n   677\t    archive_path.parent.mkdir(parents=True, exist_ok=True)\n   678\t    archive_path.write_text(\"\\n\".join(summary_lines), encoding=\"utf-8\")\n   679\t    return archive_path, archive_rel\n   680\t\n   681\t_SUBAGENT_REFUSAL = (\n   682\t    \"Subagents must inherit the parent's worktree; call the parent or \"\n   683\t    \"'cd' into the existing recorded path: {worktree_path}.\"\n   684\t)\n   685\t\n   686\t\n   687\tdef _subagent_signal() -> str | None:\n   688\t    \"\"\"Return the name of the first env signal indicating dispatched-subagent\n   689\t    status, in precedence order, or None if no signal is present.\n   690\t\n   691\t    Precedence (spec §5.3):\n   692\t      1. SUPERSTAR_SUBAGENT_ROLE  -- any non-empty value\n   693\t      2. CLAUDE_AGENT_ROLE        -- any value other than 'coordinator' / 'main'\n   694\t      3. SUPERSTAR_FORCE_SUBAGENT -- value == '1' (test-only override)\n   695\t\n   696\t    No fingerprinting fallback. Absence of all three signals = not a subagent.\n   697\t    \"\"\"\n   698\t    role = _os.environ.get(\"SUPERSTAR_SUBAGENT_ROLE\", \"\")\n   699\t    if role.strip():\n   700\t        return \"SUPERSTAR_SUBAGENT_ROLE\"\n   701\t    claude_role = _os.environ.get(\"CLAUDE_AGENT_ROLE\", \"\").strip().lower()\n   702\t    if claude_role and claude_role not in {\"coordinator\", \"main\"}:\n   703\t        return \"CLAUDE_AGENT_ROLE\"\n   704\t    if _os.environ.get(\"SUPERSTAR_FORCE_SUBAGENT\", \"\") == \"1\":\n   705\t        return \"SUPERSTAR_FORCE_SUBAGENT\"\n   706\t    return None\n   707\t\n   708\t\n   709\tdef _lookup_worktree_path_for_refusal(repo_root: Path, id: str | None) -> str:\n   710\t    \"\"\"Best-effort lookup of the slice's recorded worktree_path for inclusion\n   711\t    in the subagent refusal message. Never raises; returns '<not recorded>' on\n   712\t    any failure.\"\"\"\n   713\t    if not id:\n   714\t        return \"<not recorded>\"\n   715\t    try:\n   716\t        with _write_context(repo_root) as write_root:\n   717\t            p = _load(write_root)\n   718\t            _qid, _container, item = _find_item(p, id)\n   719\t            return getattr(item, \"worktree_path\", None) or \"<not recorded>\"\n   720\t    except Exception:\n   721\t        return \"<not recorded>\"\n   722\t\n   723\t\n   724\tdef cmd_start(\n   725\t    *,\n   726\t    repo_root: Path,\n   727\t    id: str,\n   728\t    resume: bool = False,\n   729\t    in_place: bool = False,\n   730\t    adopt: str | None = None,\n   731\t    ad_hoc: str | None = None,\n   732\t) -> None:\n   733\t    signal = _subagent_signal()\n   734\t    if signal is not None:\n   735\t        worktree_path = _lookup_worktree_path_for_refusal(repo_root, id)\n   760\t    effective_root = repo_root\n   761\t    if adopt is None and not in_place and ad_hoc is None and is_inside_linked_worktree(repo_root):\n   762\t        auto_adopt_path = repo_root.resolve()\n   763\t        # In local mode, _resolve_write_root would write to the linked worktree's\n   764\t        # tasklist.json. Retarget to the main checkout (common-dir's parent) so\n   765\t        # the slice row in the canonical tasklist gets the worktree fields. In\n   766\t        # authoritative-checkout mode, _resolve_write_root already routes; do\n   767\t        # not retarget there.\n   768\t        try:\n   769\t            cfg = load_config(repo_root)\n   770\t            if cfg.tasklist.mutation_mode == \"local\":\n   771\t                common = _subprocess.run(\n   772\t                    [\"git\", \"rev-parse\", \"--git-common-dir\"], cwd=repo_root,\n   773\t                    text=True, capture_output=True, check=True,\n   774\t                ).stdout.strip()\n   775\t                main_checkout = Path(common).resolve().parent\n   776\t                effective_root = main_checkout\n   777\t        except (_subprocess.CalledProcessError, Exception):\n   778\t            pass\n   779\t    with _write_context(effective_root) as write_root:\n   780\t        p = _load(write_root)\n   781\t        qid, _container, item = _find_item(p, id)\n   782\t        kind = parse_id(qid)[0]\n   783\t        # ─── Lifecycle preflight FIRST. No git/worktree mutation may run if the\n   784\t        # row is DONE, or BLOCKED without --resume. _preflight_start raises before\n   785\t        # we touch the filesystem.\n   786\t        _preflight_start(qid, item, resume=resume)\n   787\t        if in_place:\n   788\t            _apply_start_in_place(qid, item)\n   789\t        else:\n   790\t            adopt_path: Path | None = Path(adopt).expanduser().resolve() if adopt else None\n   791\t            if adopt_path is None and auto_adopt_path is not None:\n   792\t                adopt_path = auto_adopt_path\n   793\t            if adopt_path is not None:\n   794\t                _apply_start_adopt(write_root, qid, item, adopt_path)\n   795\t            else:\n   796\t                _apply_start_default(write_root, qid, item, resume=resume)\n   797\t        # _start_item now only mutates status/blocked_on/started; refusals already\n   798\t        # happened in _preflight_start, so this call cannot raise after side effects.\n   799\t        _start_item(qid, item, resume=resume)\n   800\t        _save(write_root, p)\n   801\t        _notify_status(qid=qid, kind=kind, status=item.status, title=item.title)\n   802\t\n   803\t\n   804\tdef _preflight_start(qid: str, item, *, resume: bool) -> None:\n   805\t    \"\"\"Lifecycle refusals from `_start_item` lifted to run BEFORE any disk mutation.\n   806\t\n   807\t    `_start_item` itself is kept unchanged so callers like `cmd_set` / `cmd_unblock`\n   808\t    that don't touch worktrees continue to work; this preflight just runs the same\n   809\t    checks earlier so the worktree branch of `cmd_start` can't leave dangling\n   810\t    on-disk state after a refusal.\n   811\t    \"\"\"\n   812\t    if item.status == Status.DONE:\n   813\t        raise CommandError(f\"{qid} is already done\")\n   814\t    if item.status == Status.BLOCKED and not resume:\n   815\t        raise CommandError(f\"{qid} is blocked; use start --resume to clear blocked_on\")\n   816\t\n   817\t\n   818\tdef _start_ad_hoc(*, repo_root: Path, slug: str) -> None:\n   819\t    slug = (slug or \"\").strip()\n   820\t    if not slug:\n   821\t        raise CommandError(\"--ad-hoc requires a non-empty <slug>\")\n   822\t    title = f\"Ad-hoc: {slug}\"\n   823\t    with _write_context(repo_root) as write_root:\n   824\t        p = _load(write_root)\n   825\t        new_id = next_cross_id(p, write_root)\n   826\t        item = CrossCutting(\n   827\t            id=new_id, title=title, created=_today(),\n   828\t            status=Status.IN_PROGRESS, started=_today(), notes=\"ad-hoc\",\n   829\t        )\n   830\t        p.cross_cutting.append(item)\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_12","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba tools/tasktool/tests/test_lifecycle_start.py | sed -n '200,370p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_12","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba tools/tasktool/tests/test_lifecycle_start.py | sed -n '200,370p'\"","aggregated_output":"   200\t    chain = ready_chain(tmp_path)\n   201\t    assert run(tmp_path, \"start\", \"P1.S1\").returncode == 0\n   202\t    r = run(tmp_path, \"set\", \"P1.S1\", \"--status\", \"done\", \"--reviewer-chain\", str(chain))\n   203\t    assert r.returncode == 0, r.stdout + r.stderr\n   204\t    sl = tasklist(tmp_path)[\"phases\"][0][\"slices\"][0]\n   205\t    assert sl[\"status\"] == \"done\"\n   206\t    assert sl[\"reviewer_chain\"] == \"docs/reviewer/p1-s1-post-slice\"\n   207\t\n   208\t\n   209\tREFUSAL_MARKER = \"Subagents must inherit the parent's worktree\"\n   210\t\n   211\tREFUSAL_SPEC_SENTENCE_TEMPLATE = (\n   212\t    \"Subagents must inherit the parent's worktree; call the parent or \"\n   213\t    \"'cd' into the existing recorded path: {worktree_path}.\"\n   214\t)\n   215\t\n   216\t\n   217\tdef _run_with_env(root, *args, extra_env=None):\n   218\t    env = os.environ.copy()\n   219\t    env[\"PYTHONPATH\"] = PYTHONPATH + os.pathsep + env.get(\"PYTHONPATH\", \"\")\n   220\t    if extra_env:\n   221\t        for k, v in extra_env.items():\n   222\t            if v is None:\n   223\t                env.pop(k, None)\n   224\t            else:\n   225\t                env[k] = v\n   226\t    return subprocess.run(\n   227\t        [sys.executable, str(TOOL), \"--project-root\", str(root), *args],\n   228\t        text=True,\n   229\t        capture_output=True,\n   230\t        env=env,\n   231\t    )\n   232\t\n   233\t\n   234\tdef test_start_refuses_when_superstar_subagent_role_set(tmp_path):\n   235\t    seed(tmp_path)\n   236\t    r = _run_with_env(\n   237\t        tmp_path, \"start\", \"P1.S1\",\n   238\t        extra_env={\"SUPERSTAR_SUBAGENT_ROLE\": \"implementer\"},\n   239\t    )\n   240\t    assert r.returncode != 0, r.stdout + r.stderr\n   241\t    assert REFUSAL_MARKER in (r.stderr + r.stdout)\n   242\t\n   243\t\n   244\tdef test_start_refuses_when_claude_agent_role_is_subagent(tmp_path):\n   245\t    seed(tmp_path)\n   246\t    r = _run_with_env(\n   247\t        tmp_path, \"start\", \"P1.S1\",\n   248\t        extra_env={\n   249\t            \"SUPERSTAR_SUBAGENT_ROLE\": None,\n   250\t            \"CLAUDE_AGENT_ROLE\": \"subagent\",\n   251\t        },\n   252\t    )\n   253\t    assert r.returncode != 0, r.stdout + r.stderr\n   254\t    assert REFUSAL_MARKER in (r.stderr + r.stdout)\n   255\t\n   256\t\n   257\tdef test_start_proceeds_when_claude_agent_role_is_coordinator(tmp_path):\n   258\t    seed(tmp_path)\n   259\t    r = _run_with_env(\n   260\t        tmp_path, \"start\", \"P1.S1\",\n   261\t        extra_env={\n   262\t            \"SUPERSTAR_SUBAGENT_ROLE\": None,\n   263\t            \"CLAUDE_AGENT_ROLE\": \"coordinator\",\n   264\t        },\n   265\t    )\n   266\t    assert r.returncode == 0, r.stdout + r.stderr\n   267\t\n   268\t\n   269\tdef test_start_proceeds_when_claude_agent_role_is_main(tmp_path):\n   270\t    seed(tmp_path)\n   271\t    r = _run_with_env(\n   272\t        tmp_path, \"start\", \"P1.S1\",\n   273\t        extra_env={\n   274\t            \"SUPERSTAR_SUBAGENT_ROLE\": None,\n   275\t            \"CLAUDE_AGENT_ROLE\": \"main\",\n   276\t        },\n   277\t    )\n   278\t    assert r.returncode == 0, r.stdout + r.stderr\n   279\t\n   280\t\n   281\tdef test_start_refuses_when_force_subagent_set(tmp_path):\n   282\t    seed(tmp_path)\n   283\t    r = _run_with_env(\n   284\t        tmp_path, \"start\", \"P1.S1\",\n   285\t        extra_env={\n   286\t            \"SUPERSTAR_SUBAGENT_ROLE\": None,\n   287\t            \"CLAUDE_AGENT_ROLE\": None,\n   288\t            \"SUPERSTAR_FORCE_SUBAGENT\": \"1\",\n   289\t        },\n   290\t    )\n   291\t    assert r.returncode != 0, r.stdout + r.stderr\n   292\t    assert REFUSAL_MARKER in (r.stderr + r.stdout)\n   293\t\n   294\t\n   295\tdef test_start_proceeds_in_plain_shell(tmp_path):\n   296\t    seed(tmp_path)\n   297\t    r = _run_with_env(\n   298\t        tmp_path, \"start\", \"P1.S1\",\n   299\t        extra_env={\n   300\t            \"SUPERSTAR_SUBAGENT_ROLE\": None,\n   301\t            \"CLAUDE_AGENT_ROLE\": None,\n   302\t            \"SUPERSTAR_FORCE_SUBAGENT\": None,\n   303\t        },\n   304\t    )\n   305\t    assert r.returncode == 0, r.stdout + r.stderr\n   306\t\n   307\t\n   308\tdef test_start_signal_precedence_superstar_wins(tmp_path):\n   309\t    seed(tmp_path)\n   310\t    r = _run_with_env(\n   311\t        tmp_path, \"start\", \"P1.S1\",\n   312\t        extra_env={\n   313\t            \"SUPERSTAR_SUBAGENT_ROLE\": \"implementer\",\n   314\t            \"CLAUDE_AGENT_ROLE\": \"coordinator\",\n   315\t        },\n   316\t    )\n   317\t    assert r.returncode != 0, (\n   318\t        \"SUPERSTAR_SUBAGENT_ROLE must win over

[… 216919 bytes elided to fit cap of 160000 bytes …]

e, whether the work is implementation-bound — but does not own the worktree. This spec moves that ownership to tasktool.
+   20	
+   21	## 2. Thesis
+   22	
+   23	**P5 is not "make the skill shorter."** Shrinking the skill is a side effect. The work is to **remove the recurring decision from agent cognition** and make tasktool the lifecycle authority for worktrees. Once that is true, the skill collapses naturally to a thin pointer and a subagent early-exit.
+   24	
+   25	## 3. Goals
+   26	
+   27	1. **Authority shift.** Tasktool creates, adopts, tracks, and cleans up worktrees. The skill stops describing how to do any of those things.
+   28	2. **Deterministic convention.** One canonical path (`.worktrees/worktree-<id>-<slug>`), one branch name (matches dir name), one `.gitignore` entry, enforced by the installer.
+   29	3. **Drift elimination.** Slice state and worktree state are co-located in `tasklist.json`. Stale worktrees cannot accumulate silently; missing worktrees cannot be papered over.
+   30	4. **Subagent token reduction.** Dispatched subagents already inside a linked worktree skip the skill entirely.
+   31	5. **Native-harness coexistence.** When a harness creates its own worktree (e.g. `EnterWorktree`), tasktool adopts and tracks rather than fighting.
+   32	
+   33	## 4. Non-goals
+   34	
+   35	- Multi-worktree-per-slice. One slice → one worktree.
+   36	- Remote-worktree management or cross-project worktree sharing.
+   37	- Per-harness worktree directories. `.claude/worktrees/` and `.codex/worktrees/` are deprecated; the installer warns on detection but performs no automatic migration. Removal of the legacy paths is scheduled one minor version after P5 ships.
+   38	- Replacing `git worktree` for ad-hoc human use outside the slice model. `tasktool worktree …` is slice-scoped tooling, not a generic git wrapper.
+   39	
+   40	## 5. Design
+   41	
+   42	### 5.1 Canonical layout
+   43	
+   44	- **Location:** `.worktrees/` at the authoritative repo root. Always git-ignored. The installer adds the entry if absent.
+   45	- **Per-slice path:** `.worktrees/worktree-<id-slug>-<title-slug>`. See the canonical naming function below.
+   46	- **Branch name:** identical to the directory base name. Eliminates the path/branch ambiguity that prune logic would otherwise face.
+   47	
+   48	#### Canonical naming function (normative)
+   49	
+   50	```
+   51	worktree_name(id, title) =
+   52	    "worktree-" + slugify_id(id) + "-" + slugify_title(title)
+   53	
+   54	slugify_id(id):
+   55	    lowercase(id)
+   56	    replace "." with "-"
+   57	    strip any character not in [a-z0-9-]
+   58	    collapse repeated "-" into single "-"
+   59	    strip leading/trailing "-"
+   60	
+   61	slugify_title(title):
+   62	    lowercase(title)
+   63	    replace whitespace and "_" with "-"
+   64	    strip any character not in [a-z0-9-]
+   65	    collapse repeated "-" into single "-"
+   66	    strip leading/trailing "-"
+   67	    truncate to 40 characters at a "-" boundary if longer
+   68	```
+   69	
+   70	Worked examples:
+   71	
+   72	| ID      | Title                                  | Directory & branch                                        |
+   73	|---------|----------------------------------------|-----------------------------------------------------------|
+   74	| `P5.S1` | "Tasktool worktree lifecycle core"     | `worktree-p5-s1-tasktool-worktree-lifecycle-core`         |
+   75	| `X42`   | "Hotfix: shim drift"                   | `worktree-x42-hotfix-shim-drift`                          |
+   76	| `P13.S2`| "Checkout rewrite"                     | `worktree-p13-s2-checkout-rewrite`                        |
+   77	
+   78	**Collision handling.** If the computed path or branch already exists and is not the recorded worktree for this slice, `start` fails with repair guidance (see §5.3 reuse rules). Tasktool never silently appends a suffix.
+   79	- **Legacy paths:** `.claude/worktrees/`, `.codex/worktrees/`, and the global `~/.config/superstar/worktrees/<project>` path are deprecated. Installer warns on detection; removal one minor version after this phase ships.
+   80	
+   81	### 5.2 Schema additions (`docs/tasklist.json`)
+   82	
+   83	Each slice (and each cross-cutting item that runs implementation work) gains two optional fields:
+   84	
+   85	```json
+   86	{
+   87	  "worktree_path": ".worktrees/worktree-p5-s1-tasktool-worktree-core",
+   88	  "worktree_branch": "worktree-p5-s1-tasktool-worktree-core"
+   89	}
+   90	```
+   91	
+   92	- Both fields default to `null`. Existing entries are not rewritten; `tasktool start` backfills on first invocation.
+   93	- **Both** are stored (not just path) because prune guards need a stable branch reference even if the directory has been manually deleted, and start needs a stable path even if the branch has been force-renamed.
+   94	- An `--in-place` start records `worktree_path: null` plus a `worktree_in_place: true` audit marker on the slice, so a later `close` does not interpret missing-worktree as broken state.
+   95	- Additional audit fields written by lifecycle commands: `worktree_pruned_at` (set by successful `prune` / `prune --finalize`), `worktree_prune_pending: true` and `worktree_prune_pending_at` (set by prune-from-inside, cleared by `--finalize`). All are optional and null/absent by default.
+   96	
+   97	### 5.3 Tasktool CLI surface
+   98	
+   99	#### `tasktool start <id> [--in-place | --adopt <path>]` &nbsp;·&nbsp; `tasktool start --ad-hoc <slug>`
+  100	
+  101	Two syntaxes. The first takes a known tasklist ID. The second omits `<id>` because the ID is allocated by tasktool from the cross-cutting namespace as part of the call.
+  102	
+  103	Default behavior: create `.worktrees/worktree-<id>-<slug>` on a branch of the same name (forked from the slice's parent branch per existing tasktool rules), set slice → `in_progress`, record `worktree_path` and `worktree_branch`, print the `cd` line for the user.
+  104	
+  105	**Idempotent reuse rules.** If `worktree_path` is already recorded, tasktool checks the live state and chooses:
+  106	
+  107	| State | Behavior |
+  108	|-------|----------|
+  109	| Path exists, is a linked worktree, branch matches | Print the `cd` line. No-op. |
+  110	| Path missing entirely, branch missing | Fail with repair guidance: `tasktool worktree repair <id>` will recreate from recorded fields. |
+  111	| Path missing, branch still present | Fail with repair guidance pointing at `tasktool worktree adopt <id> <new-path>` or `tasktool worktree repair <id>`. |
+  112	| Path present but not a linked worktree (e.g. plain dir) | Fail. Do not overwrite. Suggest `tasktool worktree prune <id> --force` then re-`start`. |
+  113	| Path present, branch mismatched | Fail. This is genuinely ambiguous — refuse rather than guess. |
+  114	
+  115	Tasktool never silently recreates over ambiguous state. Repair is always an explicit command.
+  116	
+  117	**Flags:**
+  118	- `--in-place` — explicit opt-out for planning/spec slices that do not touch code. Sets the `worktree_in_place` audit marker; subsequent `close` will not search for a worktree.
+  119	- `--adopt <path>` — record an externally-created worktree (e.g. one created by `EnterWorktree`). Tasktool verifies the path is a linked worktree and that its branch is appropriate, then stores both fields. Auto-detect: if the caller's cwd is already inside a linked worktree of the parent repo, `start` switches to adopt mode automatically and uses the detected path.
+  120	- `--ad-hoc <slug>` — throwaway worktrees for hotfixes / exploration outside a phase plan. Allocates a normal cross-cutting `X<n>` row (using existing `tasktool create cross` machinery and the existing `X\d+` ID grammar — no new ID family, no schema change to `archived_cross_cutting`), with `status: in_progress`, `title: "Ad-hoc: <slug>"`, `notes: "ad-hoc"`, and the standard `worktree_path` / `worktree_branch` fields. The row uses a deliberately non-default close path so worktree fields survive long enough for prune to run:
+  121	   1. `tasktool close <Xn> --no-archive` — required for ad-hoc rows. Flips status to `done` and leaves the row in `cross_cutting` with `worktree_path` / `worktree_branch` intact. **Defaulting `close` to auto-archive (current behavior for cross-cutting rows) would delete the row before prune could find it; the spec requires `--no-archive` rather than changing the existing default.**
+  122	   2. `tasktool worktree prune <Xn>` — standard three-guard prune; nulls worktree fields and records `worktree_pruned_at`.
+  123	   3. `tasktool archive-cross <Xn>` — archives the now-pruned row via the existing workflow.
+  124	
+  125	  Ad-hoc rows are tagged with `notes: "ad-hoc"` so `tasktool list` can hide them by default (visible under `tasktool list --all`). The skill / `tasklist-discipline` doc spells out the three-step sequence; tasktool itself does not enforce the ordering beyond the existing close/archive command surface.
+  126	
+  127	**Subagent guard.** Tasktool refuses `start` when any of the following signals indicate the caller is a dispatched subagent. Signals are checked in this order; the first present wins:
+  128	
+  129	1. `SUPERSTAR_SUBAGENT_ROLE` env var set to any non-empty value. Set by the Superstar shim when a coordinator dispatches a subagent via the Claude `Task` tool or Codex `subagent` equivalent. This is the supported, harness-set signal.
+  130	2. `CLAUDE_AGENT_ROLE` env var set to any value other than `coordinator` or `main`. Forward-compat hook for harness-native subagent signals when those become available.
+  131	3. `SUPERSTAR_FORCE_SUBAGENT=1` env var. Test-only override; documented and used by P5.S3 fixtures.
+  132	
+  133	On any positive signal, `start` exits non-zero with: `"Subagents must inherit the parent's worktree; call the parent or 'cd' into the existing recorded path: <worktree_path>."`
+  134	
+  135	**Absence of all three signals is treated as "not a subagent."** Tasktool will not infer subagent status from parent-process fingerprinting, cwd heuristics, or pty introspection — those produce too many false positives in plain shells. This means a coordinator that loses its env (e.g. via `env -i`) will look like a top-level invocation and `start` will proceed; the `tasklist-discipline` doc rule is the load-bearing guard for that case and is documented as such.
+  136	
+  137	`SUPERSTAR_SUBAGENT_ROLE` is added to the Claude shim and Codex shim as part of P5.S3.
+  138	
+  139	#### `tasktool close <id>` — unchanged worktree semantics
+  140	
+  141	**`tasktool close` does not touch the worktree.** Its existing meaning — review-gated slice closure run at slice boundary, before merge-back — is preserved unchanged. The slice's `worktree_path` / `worktree_branch` / `worktree_in_place` fields are retained verbatim across `close`, so `worktree list` continues to see the slice's worktree as a closed-but-retained row until it is explicitly pruned post-merge.
+  142	
+  143	This split is deliberate. `close` runs *before* merge-back in the established workflow (see `[[executing-plans]]`, `[[finishing-a-development-branch]]`), so it cannot enforce a merged-branch guard without breaking that workflow. Destructive cleanup is a separate operation owned by `tasktool worktree prune`.
+  144	
+  145	#### `tasktool worktree prune <id> [--keep-branch | --force]`
+  146	
+  147	Removes the recorded worktree. Invoked post-merge (typically from `[[finishing-a-development-branch]]` after the slice's branch lands on the authoritative parent). Guards (three, all durably observable from filesystem and tasklist state):
+  148	
+  149	1. Slice status is `done` (i.e. `close` has already run and the review gates passed).
+  150	2. Branch is merged into the slice's authoritative parent (e.g. `main`).
+  151	3. Working tree is clean: no uncommitted, untracked, or stashed changes in the worktree.
+  152	
+  153	If any guard fails, prune is refused with a precise reason. **`--force` overrides prune guards only.** It does not affect `tasktool close`, slice status, review gates, dependency gates, or any other lifecycle concern — those keep their existing semantics. `--force` is the destructive escape hatch for the cleanup step alone.
+  154	
+  155	**In-flight subagent detection is explicitly out of scope for P5.** A robust check would require a tasktool-managed lease/lock file written on subagent dispatch and cleared on exit. That mechanism is deferred to a follow-up (tracked under §8). For P5, prune relies on the clean-tree guard plus operator discipline: subagents that exit cleanly leave a clean tree; subagents that are abandoned leave dirty/untracked state that the clean-tree guard catches. Prune emits a non-blocking informational note when it observes a worktree whose `HEAD` has moved within the last 60 seconds, but does not refuse on that basis.
+  156	
+  157	`--keep-branch` removes the worktree directory but leaves the branch in place (useful when the branch will be referenced by tags/releases).
+  158	
+  159	After a successful prune (or `--force` prune), tasktool nulls `worktree_path` and `worktree_branch` on the slice and records a `worktree_pruned_at` audit timestamp. `worktree_in_place: true` slices have no worktree to prune; `prune` is a no-op that records the audit timestamp.
+  160	
+  161	**Prune from inside the worktree being removed.** Detected via `git rev-parse --git-dir` vs `--git-common-dir`. Tasktool:
+  162	1. Performs every non-destructive action (guards, audit log).
+  163	2. Sets a `worktree_prune_pending: true` marker on the slice (and records `worktree_prune_pending_at: <timestamp>`), pinning the staged path so `--finalize` can verify it later. Worktree fields are **not** nulled at this step.
+  164	3. Skips the `git worktree remove` call.
+  165	4. Prints the exact follow-up command to chat: `cd <authoritative-root> && git worktree remove <path> && tasktool worktree prune <id> --finalize`.
+  166	
+  167	`--finalize` (run from outside the worktree) performs the field nulling and audit timestamp. It is guard-light (does not re-run the three destructive guards) but enforces three preconditions before mutating state:
+  168	
+  169	1. `worktree_prune_pending: true` is set on the slice. Without it, `--finalize` refuses with: "no pending prune to finalize; run `tasktool worktree prune <id>` first."
+  170	2. The previously recorded `worktree_path` is no longer a registered git worktree (per `git worktree list --porcelain`).
+  171	3. No directory exists at the previously recorded `worktree_path`.
+  172	
+  173	If preconditions 2 or 3 fail, `--finalize` refuses with the specific reason and does not null the fields — this prevents hiding a still-live or partially-removed worktree from `worktree list`. On success, `--finalize` clears `worktree_prune_pending`, nulls `worktree_path` and `worktree_branch`, and sets `worktree_pruned_at`.
+  174	
+  175	No chdir magic, no re-exec.
+  176	
+  177	#### `tasktool worktree <subcommand>`
+  178	
+  179	Slice-scoped, not a generic git-worktree wrapper. All subcommands except `list` take a slice ID.
+  180	
+  181	- `tasktool worktree list [--all]` — by default, lists every slice that currently has a non-null `worktree_path` (active + closed-but-not-yet-pruned). `--all` additionally includes `--in-place` slices and slices with a `worktree_pruned_at` audit timestamp but no surviving fields. Output columns: ID, status, path, branch, health (`live` / `missing-path` / `missing-branch` / `mismatched` / `in-place` / `pruned`).
+  182	- `tasktool worktree status <id>` — detailed health for one slice's worktree: path, branch, ahead/behind parent, dirty state, last activity.
+  183	- `tasktool worktree adopt <id> <path>` — record an existing linked worktree against a slice. Used when the harness or human created the worktree out-of-band, or when repairing state after a path rename.
+  184	- `tasktool worktree prune <id> [--keep-branch | --force | --finalize]` — remove the recorded worktree. Applies the three guards described under `tasktool worktree prune` above (slice-done, branch-merged, clean-tree). `--force` overrides prune guards only; `--keep-branch` removes the directory but leaves the branch; `--finalize` records the post-prune field nulling without re-running guards when the directory was already removed externally (the prune-from-inside two-step).
+  185	- `tasktool worktree repair <id>` — recreate a missing worktree from recorded `worktree_path` + `worktree_branch` fields. Refuses if the branch is also missing (use `adopt` after creating one manually, or restart the slice).
+  186	
+  187	### 5.3.1 Lifecycle state table
+  188	
+  189	Persisted field values for each command, assuming the slice was created normally (not `--in-place` or `--ad-hoc` unless noted).
+  190	
+  191	| Command | `worktree_path` | `worktree_branch` | `worktree_in_place` | `worktree_pruned_at` | Disk state |
+  192	|---|---|---|---|---|---|
+  193	| `start` (fresh) | recorded | recorded | absent | absent | linked worktree created |
+  194	| `start` (idempotent reuse, consistent) | unchanged | unchanged | unchanged | unchanged | unchanged |
+  195	| `start --in-place` | null | null | `true` | absent | nothing on disk |
+  196	| `start --adopt <path>` | recorded (= path) | recorded (from path's branch) | absent | absent | linked worktree pre-existed |
+  197	| `close` | unchanged | unchanged | unchanged | unchanged | unchanged |
+  198	| `worktree prune` (success) | nulled | nulled | unchanged | set to now | worktree removed; branch removed unless `--keep-branch` |
+  199	| `worktree prune` (prune-from-inside, before `--finalize`) | unchanged | unchanged | unchanged | absent | worktree still present; `worktree_prune_pending: true` set on slice |
+  200	| `worktree prune --finalize` (preconditions met) | nulled | nulled | unchanged | set to now | (caller already removed the worktree); `worktree_prune_pending` cleared |
+
+[truncated: 125 additional lines]
+### docs/tasklist.json
+
+    1	{
+    2	  "archived_cross_cutting": [
+    3	    {
+    4	      "archived_date": "2026-05-21",
+    5	      "archived_path": "docs/archived-tasks/X15-archive-closed-cross-cutting-items.md",
+    6	      "id": "X15",
+    7	      "title": "Archive closed cross-cutting items"
+    8	    },
+    9	    {
+   10	      "archived_date": "2026-05-21",
+   11	      "archived_path": "docs/archived-tasks/X16-stamp-installed-shims-and-enforce-versio.md",
+   12	      "id": "X16",
+   13	      "title": "Stamp installed shims and enforce version drift refusal"
+   14	    }
+   15	  ],
+   16	  "archived_phases": [
+   17	    {
+   18	      "archived_date": "2026-05-18",
+   19	      "archived_path": "docs/archived-tasks/P2-tasktool-json-backed-task-management-cli.md",
+   20	      "id": "P2",
+   21	      "title": "tasktool: JSON-backed task management CLI"
+   22	    },
+   23	    {
+   24	      "archived_date": "2026-05-19",
+   25	      "archived_path": "docs/archived-tasks/P4-tasktool-coordination-and-lifecycle-auth.md",
+   26	      "id": "P4",
+   27	      "title": "Tasktool coordination and lifecycle authority"
+   28	    },
+   29	    {
+   30	      "archived_date": "2026-05-19",
+   31	      "archived_path": "docs/archived-tasks/P3-phase-planning-workflow.md",
+   32	      "id": "P3",
+   33	      "title": "Phase planning workflow"
+   34	    },
+   35	    {
+   36	      "archived_date": "2026-05-20",
+   37	      "archived_path": "docs/archived-tasks/P1-external-reviewer-work-historical.md",
+   38	      "id": "P1",
+   39	      "title": "External-reviewer work (historical)"
+   40	    }
+   41	  ],
+   42	  "cross_cutting": [
+   43	    {
+   44	      "closed": "2026-05-18",
+   45	      "created": "2026-05-18",
+   46	      "id": "X1",
+   47	      "notes": "Changed external-review default prompt transport from argv to stdin so the bundled Codex reviewer-agent receives prompts via codex exec '-' and avoids argv length failures.",
+   48	      "refs": [],
+   49	      "started": null,
+   50	      "status": "done",
+   51	      "title": "Default external-review prompt transport to stdin"
+   52	    },
+   53	    {
+   54	      "closed": "2026-05-18",
+   55	      "created": "2026-05-18",
+   56	      "id": "X2",
+   57	      "notes": "Added repo-local tools/tasktool/tasktool launcher, updated tasklist/project-setup docs to prefer it, and taught the pre-commit hook to use the repo-local launcher before falling back to a global tasktool shim.",
+   58	      "refs": [],
+   59	      "started": null,
+   60	      "status": "done",
+   61	      "title": "Add repo-local tasktool launcher"
+   62	    },
+   63	    {
+   64	      "closed": "2026-05-19",
+   65	      "created": "2026-05-19",
+   66	      "id": "X3",
+   67	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. External-review verdict parsing now accepts markdown-emphasized Overall Verdict headings such as **5. Overall Verdict** followed by ready/revise text.",
+   68	      "refs": [
+   69	        "skills/external-review/scripts/external-reviewer.py",
+   70	        "skills/external-review/tests/test_heading_style_verdict.py"
+   71	      ],
+   72	      "started": null,
+   73	      "status": "done",
+   74	      "title": "Spot fix: parse bold external-review verdict headings"
+   75	    },
+   76	    {
+   77	      "closed": "2026-05-19",
+   78	      "created": "2026-05-19",
+   79	      "id": "X4",
+   80	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. Legacy markdown import now accepts fully-qualified slice IDs and additional cross-cutting forms including tagged done items, blocked cross rows coerced to ready, and archived cross rows treated as done.",
+   81	      "refs": [
+   82	        "tools/tasktool/importer.py"
+   83	      ],
+   84	      "started": null,
+   85	      "status": "done",
+   86	      "title": "Spot fix: broaden legacy tasklist importer compatibility"
+   87	    },
+   88	    {
+   89	      "closed": "2026-05-19",
+   90	      "created": "2026-05-19",
+   91	      "id": "X5",
+   92	      "notes": "User-requested hook update completed outside the normal workflow for speed. Adds Stop/SubagentStop finished-agent notifications, milestone message derivation from final agent text/transcript payloads, Hypr TTS config reuse with OPENAI_API_KEY fallback, and non-TTS ding fallbacks.\nSuperseded by X8: final-text milestone parsing was removed; agent hooks now emit generic dings and semantic spoken notifications come from tasktool status changes.",
+   93	      "refs": [
+   94	        "hooks/agent-finished",
+   95	        "hooks/hooks.json",
+   96	        "hooks/hooks-cursor.json",
+   97	        "tests/claude-code/test-agent-finished-hook.sh"
+   98	      ],
+   99	      "started": null,
+  100	      "status": "done",
+  101	      "title": "Add finished-agent notification hook"
+  102	    },
+  103	    {
+  104	      "closed": "2026-05-19",
+  105	      "created": "2026-05-19",
+  106	      "id": "X6",
+  107	      "notes": "Codex startup skips Stop/SubagentStop notification hooks when hooks.json uses async=true; fix should preserve finished-agent notification behavior while avoiding unsupported async hook registration in Codex.\nSet finished-agent Stop/SubagentStop hook registrations to async=false for Codex compatibility. The hook now backgrounds real notification playback internally so synchronous hook registration returns quickly while dry-run tests remain foreground and deterministic.",
+  108	      "refs": [
+  109	        "hooks/hooks.json",
+  110	        "hooks/agent-finished",
+  111	        "tests/claude-code/test-hook-config.sh",
+  112	        "tests/claude-code/test-agent-finished-hook.sh"
+  113	      ],
+  114	      "started": null,
+  115	      "status": "done",
+  116	      "title": "Fix Codex finished-agent hook compatibility"
+  117	    },
+  118	    {
+  119	      "closed": "2026-05-19",
+  120	      "created": "2026-05-19",
+  121	      "id": "X7",
+  122	      "notes": "Codex reported superstar/6.0.0 because the installable local marketplace payload under plugins/superstar still declared version 6.0.0 and the version bump audit did not track that embedded manifest.\n\nBumped the embedded Codex plugin payload manifest to 6.0.1 and added it to the version bump check. Reinstalled superstar@superstar-dev, then rebuilt the 6.0.1 runtime cache as a materialized copy of this checkout with .agents excluded so Codex sees the full skills/hooks tree while codex plugin list still reports installed/enabled. Final probe shows cache version 6.0.1, skills/hooks present, and no async-hook warning.",
+  123	      "refs": [
+  124	        ".version-bump.json",
+  125	        "plugins/superstar/.codex-plugin/plugin.json",
+  126	        ".agents/plugins/marketplace.json",
+  127	        "tests/codex-plugin-sync/test-version-drift.sh",
+  128	        "tests/codex-plugin-sync/test-local-marketplace.sh"
+  129	      ],
+  130	      "started": null,
+  131	      "status": "done",
+  132	      "title": "Fix Superstar Codex plugin payload version drift"
+  133	    },
+  134	    {
+  135	      "closed": "2026-05-19",
+  136	      "created": "2026-05-19",
+  137	      "id": "X8",
+  138	      "notes": "Move semantic spoken notifications to tasktool status transitions for ready/in_progress/blocked/done. Keep agent Stop/SubagentStop hooks as generic completion dings only, with different sound styles for Claude and Codex.\nAgent Stop/SubagentStop hooks now emit generic harness-specific dings only. Semantic spoken notifications moved to tasktool status events for ready, in_progress, blocked, and done, including create, set, close, block, unblock, and archive-phase paths.",
+  139	      "refs": [
+  140	        "hooks/agent-finished",
+  141	        "tools/tasktool/notify.py",
+  142	        "tools/tasktool/commands.py",
+  143	        "tools/tasktool/tests/test_notify.py",
+  144	        "tools/tasktool/tests/test_commands.py",
+  145	        "tools/tasktool/tests/conftest.py",
+  146	        "tests/claude-code/test-agent-finished-hook.sh"
+  147	      ],
+  148	      "started": null,
+  149	      "status": "done",
+  150	      "title": "Move semantic notifications from agent hooks to tasktool status changes"
+  151	    },
+  152	    {
+  153	      "closed": "2026-05-19",
+  154	      "created": "2026-05-19",
+  155	      "id": "X9",
+  156	      "notes": "Rapid tasktool status changes currently spawn independent notifier processes, causing overlapping TTS/audio. Add a single-audio queue with at most three queued tasktool events; overflow should collapse to a single 'multiple other events' summary and drop further items.\nAdded a file-backed notification queue shared by agent dings and tasktool TTS. Only one worker drains audio at a time. Queue capacity is three pending events; overflow keeps the first two pending items and replaces the rest with a single 'Multiple other events' summary, dropping further burst items while the summary remains queued.",
+  157	      "refs": [
+  158	        "tools/tasktool/notify.py",
+  159	        "tools/tasktool/tests/test_notify.py"
+  160	      ],
+  161	      "started": null,
+  162	      "status": "done",
+  163	      "title": "Coalesce bursty tasktool audio notifications"
+  164	    },
+  165	    {
+  166	      "closed": "2026-05-20",
+  167	      "created": "2026-05-20",
+  168	      "id": "X10",
+  169	      "notes": "",
+  170	      "refs": [
+  171	        "docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md",
+  172	        "docs/reviewer/x10-verdict-parser-claude-formatting-design-spec",
+  173	        "docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md"
+  174	      ],
+  175	      "started": null,
+  176	      "status": "done",
+  177	      "title": "Harden external-review verdict parser and prompt against Claude formatting variants"
+  178	    },
+  179	    {
+  180	      "closed": "2026-05-20",
+  181	      "created": "2026-05-20",
+  182	      "id": "X11",
+  183	      "notes": "",
+  184	      "refs": [
+  185	        "docs/specs/2026-05-20-X11-global-external-reviewer-bridge-design.md",
+  186	        "docs/reviewer/x11-global-external-reviewer-bridge-design-spec",
+  187	        "docs/plans/2026-05-20-X11-global-external-reviewer-bridge.md",
+  188	        "docs/reviewer/x11-global-external-reviewer-bridge-plan",
+  189	        "docs/handoffs/2026-05-20-X11-global-external-reviewer-bridge-prompt.md"
+  190	      ],
+  191	      "started": "2026-05-20",
+  192	      "status": "done",
+  193	      "title": "Make external-review bridge global"
+  194	    },
+  195	    {
+  196	      "closed": "2026-05-20",
+  197	      "created": "2026-05-20",
+  198	      "id": "X12",
+  199	      "notes": "",
+  200	      "refs": [
+
+[truncated: 139 additional lines]
+
+<!-- superstar-prompt:end -->
\ No newline at end of file
diff --git a/docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/r1-2026-05-21T2120-primary-response.md b/docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/r1-2026-05-21T2120-primary-response.md
new file mode 100644
index 0000000..8ab39a8
--- /dev/null
+++ b/docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/r1-2026-05-21T2120-primary-response.md
@@ -0,0 +1,37 @@
+# Review — 2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md (post-slice, round 1)
+
+- Target: `docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md`
+- Request: `docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/r1-2026-05-21T2120-primary-request.md`
+- Reviewer command: `reviewer-agent`
+- Reviewer provider: `codex`
+- Sandbox: repo read-only; scratch/output writable
+- Status: `ok`
+
+---
+
+1. Findings
+
+F1 — Severity: blocking — P5.S3 implementation happened without the required tasktool lifecycle start. The plan makes `tasktool start P5.S3` the lifecycle gate and says it must flip the row to `in_progress` before implementation ([plan:84](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:84), [plan:90](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:90)). The repo has seven `P5.S3` commits on the slice branch, but `docs/tasklist.json` still records P5.S3 as `status: ready`, `started: null`, `planning_status: proposed`, and its `reviewer_chain` still points at the plan chain rather than a post-slice chain ([tasklist:307](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/tasklist.json:307), [tasklist:319](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/tasklist.json:319), [tasklist:324](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/tasklist.json:324), [tasklist:325](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/tasklist.json:325), [tasklist:326](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/tasklist.json:326)). This breaks the slice evidence trail and should be corrected before close.
+
+F2 — Severity: important — The post-slice review chain artifact is present but not durably recorded. `git status --short` reports `?? docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/`; its `chain.json` has `rounds: []` and both checkpoints pending ([chain:8](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/chain.json:8), [chain:9](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/chain.json:9)). The plan requires handing back “`git status` clean” before close ([plan:1084](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow/docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md:1084)). Commit/register the actual review chain output before treating the slice as closeable.
+
+2. Open questions / assumptions
+
+I assume the best-effort prompt-template shim was accepted during plan review, despite the spec’s literal “Claude shim and Codex shim integration tests” language. The implementation is explicit about that limitation in the plan and in tests, so I am not treating it as a blocker here.
+
+3. Suggested document edits
+
+Update `docs/tasklist.json` through `tasktool` lifecycle commands, not by hand: P5.S3 should reflect the actual started state and post-slice reviewer chain before close. Also include the post-slice reviewer chain path in refs once the review round is materialized.
+
+4. Verification gaps / commands that should be run
+
+Already run during this review:
+`tools/tasktool/tasktool validate --strict-format` → `ok`
+`python -m pytest tools/tasktool/tests -q` → `526 passed, 1 warning in 94.17s`
+
+After fixing lifecycle/reviewer artifacts, rerun:
+`tools/tasktool/tasktool show P5.S3`
+`git status --short`
+`tools/tasktool/tasktool validate --strict-format`
+
+Overall verdict: revise
diff --git a/docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/r1-2026-05-21T2120-sweep1-request.md b/docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/r1-2026-05-21T2120-sweep1-request.md
new file mode 100644
index 0000000..104de67
--- /dev/null
+++ b/docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice/r1-2026-05-21T2120-sweep1-request.md
@@ -0,0 +1,1072 @@
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
+/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow
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
+docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md
+
+Additional context files:
+- docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md
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
+
+End your review with this exact line, as plain text on its own line:
+
+    Overall verdict: <ready|ready with small edits|revise>
+
+Do not bold, italicise, prefix with `##`, split across lines, or drop the
+word "Overall". Do not write `**Verdict: ready**` or place the value on a
+new line after a heading.
+
+Read the files from disk. Do not rely only on the snippets in this prompt.
+
+
+## Target Preview
+
+### docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md
+
+    1	# P5.S3 — Skill rewrite + subagent guard + workflow updates — Implementation Plan
+    2	
+    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
+    4	
+    5	**Goal:** Collapse `using-git-worktrees` to ≤40 lines around a subagent early-exit, teach `tasktool start` to refuse dispatched subagents via three env signals, and update the coordinator's dispatch prompt templates to instruct subagents to export `SUPERSTAR_SUBAGENT_ROLE` so the runtime guard has the highest practical chance of firing when subagents follow the directive.
+    6	
+    7	**Architecture:** Five disjoint edit clusters:
+    8	1. Skill rewrite (`using-git-worktrees/SKILL.md` shrunk; long-form submodule guard relocated to `references/submodules.md`).
+    9	2. Subagent guard inside `tools/tasktool/commands.py::cmd_start` (three env signals with declared precedence, single refusal message, no fingerprinting).
+   10	3. Workflow cross-reference updates in `tasklist-discipline`, `executing-plans`, `subagent-driven-development` (no touch to `finishing-a-development-branch` — that belongs to P5.S2).
+   11	4. Coordinator-facing dispatch prompt updates: extend `skills/subagent-driven-development/implementer-prompt.md` (and the spec-reviewer / code-quality-reviewer prompt templates) to instruct each dispatched subagent to export `SUPERSTAR_SUBAGENT_ROLE=<role>` as its first shell command. This is a best-effort prose directive (Superstar does not wrap the harness's native dispatch tool), backed by the runtime guard in step 2 and the load-bearing prose rule in step 3. Tests assert the directive is present in every template and that a simulated `env -i bash` dispatch is correctly refused.
+   12	5. Tests: signal-precedence and plain-shell false-negative coverage for the guard, template fixture tests for the shim directive, a token-budget regression fixture for the skill body, and a doc-shape test for the rewritten skill (≤40 lines, `<SUBAGENT-STOP>` block present).
+   13	
+   14	**Tech Stack:** Python (3.10+) for tasktool, pytest for tests, bash for fixtures, plain Markdown for skill / template edits.
+   15	
+   16	**Out of scope (handled elsewhere):**
+   17	- Schema field reads/writes for `worktree_path` / `worktree_branch` / `worktree_in_place` — owned by P5.S1.
+   18	- Worktree creation, adoption, prune, repair, finalize — owned by P5.S1 / P5.S2.
+   19	- `finishing-a-development-branch` edits (post-merge prune step) — owned by P5.S2 per spec §5.3.2 (`:212-214`). The spec's P5.S3 slice paragraph at §6 (`:275-277`) lists all three workflow skills, but §5.3.2 splits ownership and assigns the prune step to P5.S2. Treat §5.3.2 as authoritative; this slice does not modify `finishing-a-development-branch`. Task 1.5 below verifies P5.S2 actually shipped the prune step before this slice starts so the workflow gap is not silently left open.
+   20	- Removal of legacy `.claude/worktrees/` / `.codex/worktrees/` paths — deferred per spec §4.
+   21	
+   22	**Shim scope (read this before Task 8).** The spec at `:137` and `:286` says "the Claude shim and Codex shim" export `SUPERSTAR_SUBAGENT_ROLE`. The Superstar repo does not currently wrap the harness's native dispatch tool (Claude Code's `Task`, Codex's `spawn_agent`) — there is no Python or JS interceptor between the harness and the subagent process where an env var could be injected programmatically. The honest implementation is therefore a **best-effort prose guard**: the coordinator's dispatch prompt templates instruct the subagent to export the variable as its first shell command. The runtime guard in `tasktool start` (Task 7) is the load-bearing safety net; the prose rule in `tasklist-discipline` (Task 9) is the load-bearing *cultural* rule. The prompt-template directive (Task 8) raises the probability that the runtime guard fires in real use, but does not guarantee it. Task 8 acknowledges this explicitly and adds a simulated-harness transcript test (Task 8 Step 8.5) to prove the dispatch-time refusal actually works in a realistic shell when the directive is followed. If a future harness change exposes a real env-injection point, that integration can be wired in without breaking either the runtime guard or the prose rule.
+   23	
+   24	**Scheduling preconditions (verify before starting):**
+   25	
+   26	```sh
+   27	tools/tasktool/tasktool show P5.S3
+   28	tools/tasktool/tasktool schedule P5
+   29	```
+   30	
+   31	Expected: `P5.S3` exists with `status: ready`, `depends_on: [P5.S1, P5.S2]`, `planning_status: proposed`. After plan-review passes, the writing-plans flow will ratify (coordinator-side `tasktool ratify P5.S3 --parallel-group …` is **not** part of this plan — the coordinator owns ratification).
+   32	
+   33	**Verification baseline (must pass against `main` before slice start, per spec §10):**
+   34	
+   35	```sh
+   36	tools/tasktool/tasktool validate --strict-format
+   37	python -m pytest tools/tasktool/tests -q
+   38	```
+   39	
+   40	---
+   41	
+   42	## File Structure
+   43	
+   44	| File | Status | Responsibility |
+   45	|---|---|---|
+   46	| `skills/using-git-worktrees/SKILL.md` | rewrite (226 → ≤40 lines) | Subagent early-exit block + 4 one-line rules. |
+   47	| `skills/using-git-worktrees/references/submodules.md` | create | Submodule guard lifted from current SKILL.md §0; loaded on demand. |
+   48	| `skills/tasklist-discipline/SKILL.md` | append paragraph | Subagents must inherit cwd; never call `tasktool start`. |
+   49	| `skills/executing-plans/SKILL.md` | minor edits | Add cross-reference to the rewritten skill's early-exit; mention parent-creates-worktree pattern. |
+   50	| `skills/subagent-driven-development/SKILL.md` | minor edits | One-line reminder that subagents inherit cwd and never call `tasktool start`. |
+   51	| `skills/subagent-driven-development/implementer-prompt.md` | minor edits | Add explicit `SUPERSTAR_SUBAGENT_ROLE=implementer` directive in the dispatch template. |
+   52	| `skills/subagent-driven-development/spec-reviewer-prompt.md` | minor edits | Same directive, role=`spec-reviewer`. |
+   53	| `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | minor edits | Same directive, role=`code-quality-reviewer`. |
+   54	| `tools/tasktool/commands.py` | extend `cmd_start` | Three-signal subagent guard with declared precedence; refusal message verbatim from spec §5.3. |
+   55	| `tools/tasktool/tests/test_lifecycle_start.py` | extend | Add guard tests (precedence, refusal message, plain-shell false-negative). |
+   56	| `tools/tasktool/tests/fixtures/p5_s3_skill_body.txt` | create | Frozen copy of the rewritten skill body for the token-budget regression test. |
+   57	| `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` | extend | Skill-shape tests: ≤40 lines, contains `<SUBAGENT-STOP>` block, contains `tasktool start` reference, references `references/submodules.md`. |
+   58	| `tools/tasktool/tests/test_subagent_prompt_shim.py` | create | Assert each of the three subagent-prompt templates exports `SUPERSTAR_SUBAGENT_ROLE=<expected>`. |
+   59	
+   60	---
+   61	
+   62	## Task 1: Establish baseline + lifecycle start
+   63	
+   64	**Files:** none — verification + tasktool lifecycle only.
+   65	
+   66	- [ ] **Step 1.1: Verify scheduling preconditions**
+   67	
+   68	```sh
+   69	tools/tasktool/tasktool show P5.S3
+   70	tools/tasktool/tasktool schedule P5
+   71	```
+   72	
+   73	Expected: `P5.S3` exists with `depends_on: [P5.S1, P5.S2]`. If absent or differs, stop — coordinator needs to fix the row before this plan can execute.
+   74	
+   75	- [ ] **Step 1.2: Verify baseline tests pass**
+   76	
+   77	```sh
+   78	tools/tasktool/tasktool validate --strict-format
+   79	python -m pytest tools/tasktool/tests -q
+   80	```
+   81	
+   82	Expected: both exit 0. If anything fails on `main`, stop and report — do not start the slice over a red baseline.
+   83	
+   84	- [ ] **Step 1.3: Start the slice**
+   85	
+   86	```sh
+   87	tools/tasktool/tasktool start P5.S3
+   88	```
+   89	
+   90	Expected: status flips to `in_progress`. This is the lifecycle gate; do not substitute prose, TodoWrite, or hand JSON edits.
+   91	
+   92	- [ ] **Step 1.4: Verify P5.S2 shipped the `finishing-a-development-branch` prune step**
+   93	
+   94	This slice deliberately does not modify `finishing-a-development-branch` (spec §5.3.2 assigns the prune step to P5.S2). Confirm P5.S2 actually delivered that edit before this slice begins, so the workflow gap is not silently left open:
+   95	
+   96	```sh
+   97	tools/tasktool/tasktool show P5.S2
+   98	grep -nE "tasktool worktree prune" skills/finishing-a-development-branch/SKILL.md
+   99	```
+  100	
+  101	Expected: `P5.S2` status is `done` (closed by P5.S2's external review gate), and `grep` returns at least one match showing the post-merge prune step. If `P5.S2` is not done, **stop** — this slice waits on it. If `P5.S2` is done but `finishing-a-development-branch` does not mention `tasktool worktree prune`, stop and surface the gap to the coordinator (this would be a P5.S2 closeout defect, not a P5.S3 problem to paper over).
+  102	
+  103	- [ ] **Step 1.5: No commit yet.**
+  104	
+  105	This task produces no diff. Proceed to Task 2.
+  106	
+  107	---
+  108	
+  109	## Task 2: Extract submodule guard to `references/submodules.md`
+  110	
+  111	**Files:**
+  112	- Create: `skills/using-git-worktrees/references/submodules.md`
+  113	
+  114	- [ ] **Step 2.1: Create the references directory and submodules reference**
+  115	
+  116	```sh
+  117	mkdir -p skills/using-git-worktrees/references
+  118	```
+  119	
+  120	Write `skills/using-git-worktrees/references/submodules.md` with this content:
+  121	
+  122	```markdown
+  123	# Submodule guard for using-git-worktrees
+  124	
+  125	Load this reference **only** when `tasktool start` reports a worktree-detection conflict caused by a submodule, or when the early-exit block in `SKILL.md` cannot decide whether the current directory is a linked worktree or a submodule checkout.
+  126	
+  127	## Why this matters
+  128	
+  129	`GIT_DIR != GIT_COMMON_DIR` is true in two distinct situations:
+  130	
+  131	1. The current directory is a linked git worktree (e.g. `.worktrees/worktree-p5-s3-…`).
+  132	2. The current directory is a git submodule checkout.
+  133	
+  134	The submodule case must **not** be treated as a worktree. Treating a submodule as a linked worktree skips legitimate worktree creation and corrupts the slice's evidence boundary.
+  135	
+  136	## Disambiguating
+  137	
+  138	Run:
+  139	
+  140	```sh
+  141	git rev-parse --show-superproject-working-tree 2>/dev/null
+  142	```
+  143	
+  144	- Empty output (or non-zero exit): you are **not** in a submodule. The `GIT_DIR != GIT_COMMON_DIR` signal is genuine — treat the directory as a linked worktree.
+  145	- Non-empty output (a path): you are inside a submodule of that superproject. Treat the directory as a normal repo checkout and do not skip the worktree creation step.
+  146	
+  147	## What to do
+  148	
+  149	If you discover you are in a submodule and tasktool refuses to proceed, leave the submodule (`cd` to the superproject root, or to the authoritative checkout) and re-run `tasktool start <id>` from there. Do not attempt to nest a worktree inside the submodule.
+  150	```
+  151	
+  152	- [ ] **Step 2.2: Stage the new file**
+  153	
+  154	```sh
+  155	git add skills/using-git-worktrees/references/submodules.md
+  156	```
+  157	
+  158	- [ ] **Step 2.3: Defer commit until the skill rewrite lands (Task 3).** This keeps the rewrite atomic.
+  159	
+  160	---
+  161	
+  162	## Task 3: Rewrite `using-git-worktrees/SKILL.md`
+  163	
+  164	**Files:**
+  165	- Modify: `skills/using-git-worktrees/SKILL.md` (current 226 lines → target ≤40 lines including frontmatter, per spec §5.5)
+  166	
+  167	- [ ] **Step 3.1: Replace the entire file with the rewritten body**
+  168	
+  169	Write `skills/using-git-worktrees/SKILL.md` with exactly this content:
+  170	
+  171	```markdown
+  172	---
+  173	name: using-git-worktrees
+  174	description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - ensures an isolated workspace exists via native tools or git worktree fallback
+  175	---
+  176	
+  177	<SUBAGENT-STOP>
+  178	You were dispatched as a subagent. The parent coordinator has already created or adopted the worktree for the active slice and `cd`d you into it. Do not read or apply the rest of this skill, and do not call `tasktool start`. If `git rev-parse --git-dir` differs from `git rev-parse --git-common-dir` (and you are not inside a submodule — see `references/submodules.md` if uncertain), you are inside the parent's linked worktree; proceed with your task. If they match, you are in a plain checkout; ask the parent before editing files.
+  179	</SUBAGENT-STOP>
+  180	
+  181	# Using Git Worktrees
+  182	
+  183	**Announce at start:** "I'm using the using-git-worktrees skill to enter the slice worktree."
+  184	
+  185	**Rule:** Implementation slice/task work runs in an isolated linked worktree owned by tasktool. A plain `main`/`master` checkout is planning/read-only by default unless the human partner opts out of isolation in the current turn.
+  186	
+  187	**Run:** `tasktool start <slice-id>` from the authoritative checkout (or from an already-linked worktree of the same repo — tasktool will auto-adopt). It creates the worktree at `.worktrees/worktree-<id>-<slug>`, records the path and branch on the slice row, and prints the `cd` line. Idempotent: a consistent recorded path is a no-op. See `[[tasklist-discipline]]` for the lifecycle commands and the routing rules.
+  188	
+  189	**Opt-out:** For planning, spec, or design slices that touch no code, run `tasktool start <slice-id> --in-place`. The slice row records `worktree_in_place: true`; later `close` and `worktree prune` treat the slice as having no worktree.
+  190	
+  191	**Drift:** If `tasktool start` reports a conflict (path missing, branch mismatched, plain-dir collision), run the exact `tasktool worktree {adopt,repair,prune --force}` command it prints. Do not improvise with raw `git worktree` invocations; do not delete `.worktrees/` directories by hand.
+  192	
+  193	For submodule-vs-worktree disambiguation, see `references/submodules.md`.
+  194	```
+  195	
+  196	- [ ] **Step 3.2: Verify length ≤ 40 lines including frontmatter**
+  197	
+  198	```sh
+  199	wc -l skills/using-git-worktrees/SKILL.md
+  200	```
+  201	
+  202	Expected: ≤ 40. If over, tighten the body — do not add a Quick Reference table, Common Mistakes section, Red Flags table, or decision tree to bring it back under target; those are deliberately forbidden by §5.5.
+  203	
+  204	- [ ] **Step 3.3: Verify the `<SUBAGENT-STOP>` block is the first content after frontmatter**
+  205	
+  206	```sh
+  207	grep -n "<SUBAGENT-STOP>\|</SUBAGENT-STOP>" skills/using-git-worktrees/SKILL.md
+  208	```
+  209	
+  210	Expected: opening tag near line 6, closing tag before the `# Using Git Worktrees` heading.
+  211	
+  212	- [ ] **Step 3.4: Commit Tasks 2 + 3 atomically**
+  213	
+  214	```sh
+  215	git add skills/using-git-worktrees/SKILL.md skills/using-git-worktrees/references/submodules.md
+  216	git commit -m "P5.S3: rewrite using-git-worktrees skill to subagent early-exit + tasktool pointer"
+  217	```
+  218	
+  219	---
+  220	
+  221	## Task 4: Write failing skill-shape tests
+  222	
+  223	**Files:**
+  224	- Modify: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` (append tests)
+  225	
+  226	- [ ] **Step 4.1: Read the existing module to understand the helper conventions**
+  227	
+  228	```sh
+  229	sed -n '1,40p' tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
+  230	```
+  231	
+  232	Expected: a `skill_text(name)` helper exists. (If the helper signature differs, adapt the snippets below to match; do not rename the helper.)
+  233	
+  234	- [ ] **Step 4.2: Append the skill-shape tests**
+  235	
+  236	Append these tests to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:
+  237	
+  238	```python
+  239	def test_using_git_worktrees_is_thin_and_has_subagent_stop_block() -> None:
+  240	    text = skill_text("using-git-worktrees")
+  241	    lines = text.splitlines()
+  242	    assert len(lines) <= 40, (
+  243	        f"using-git-worktrees SKILL.md must be <=40 lines (spec §5.5); "
+  244	        f"got {len(lines)}"
+  245	    )
+  246	    assert "<SUBAGENT-STOP>" in text, "missing <SUBAGENT-STOP> opening tag"
+  247	    assert "</SUBAGENT-STOP>" in text, "missing </SUBAGENT-STOP> closing tag"
+  248	    # The block must precede the human-facing heading.
+  249	    assert text.index("<SUBAGENT-STOP>") < text.index("# Using Git Worktrees")
+  250	
+  251	
+  252	def test_using_git_worktrees_points_at_tasktool_start() -> None:
+  253	    text = skill_text("using-git-worktrees")
+  254	    assert "tasktool start" in text, "skill must instruct calling tasktool start"
+  255	    assert "--in-place" in text, "skill must document the --in-place opt-out"
+  256	
+  257	
+  258	def test_using_git_worktrees_has_no_forbidden_sections() -> None:
+  259	    text = skill_text("using-git-worktrees")
+  260	    forbidden = ["## Quick Reference", "## Common Mistakes", "## Red Flags",
+  261	                 "### 1a.", "### 1b.", "## Step 0", "## Step 1", "## Step 3", "## Step 4"]
+  262	    for marker in forbidden:
+  263	        assert marker not in text, (
+  264	            f"forbidden section/heading present (spec §5.5 forbids it): {marker!r}"
+  265	        )
+  266	
+  267	
+  268	def test_using_git_worktrees_references_submodules_doc() -> None:
+  269	    text = skill_text("using-git-worktrees")
+  270	    assert "references/submodules.md" in text, (
+  271	        "skill must point at references/submodules.md for the submodule guard"
+  272	    )
+  273	    from pathlib import Path
+  274	    submod = Path(__file__).resolve().parents[3] / "skills" / "using-git-worktrees" / "references" / "submodules.md"
+  275	    assert submod.is_file(), f"references/submodules.md must exist at {submod}"
+  276	```
+  277	
+  278	- [ ] **Step 4.3: Run the new tests; verify they pass against the rewritten skill**
+  279	
+  280	```sh
+  281	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -v
+  282	```
+  283	
+  284	Expected: the four new tests pass. (If the skill was rewritten correctly in Task 3 they should be green on first run; this is a guard-rail, not TDD red→green for the skill itself.)
+  285	
+  286	- [ ] **Step 4.4: Commit**
+  287	
+  288	```sh
+  289	git add tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
+  290	git commit -m "P5.S3: test using-git-worktrees skill shape (length, stop-block, no forbidden sections)"
+  291	```
+  292	
+  293	---
+  294	
+  295	## Task 5: Capture token-budget regression fixture
+  296	
+  297	**Files:**
+  298	- Create: `tools/tasktool/tests/fixtures/p5_s3_skill_body.txt`
+  299	- Modify: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` (append regression test)
+  300	
+  301	The spec §6 P5.S3 requires a concrete token-budget regression fixture so future edits cannot silently regrow the skill. Mechanism: freeze the post-rewrite body as a fixture file and assert the live skill matches it byte-for-byte, except for trailing whitespace normalisation. Future edits must consciously update the fixture, which is the audit trail.
+  302	
+  303	- [ ] **Step 5.1: Capture the frozen fixture**
+  304	
+  305	```sh
+  306	mkdir -p tools/tasktool/tests/fixtures
+  307	cp skills/using-git-worktrees/SKILL.md tools/tasktool/tests/fixtures/p5_s3_skill_body.txt
+  308	```
+  309	
+  310	- [ ] **Step 5.2: Append the regression test**
+  311	
+  312	Append this test to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:
+  313	
+  314	```python
+  315	def test_using_git_worktrees_matches_token_budget_fixture() -> None:
+  316	    """Token-budget regression. If you must edit the skill, update the fixture
+  317	    in the same commit so the diff is visible in review. Spec P5.S3 §6."""
+  318	    from pathlib import Path
+  319	    live = (Path(__file__).resolve().parents[3]
+  320	            / "skills" / "using-git-worktrees" / "SKILL.md").read_text()
+  321	    fixture = (Path(__file__).resolve().parent / "fixtures"
+  322	               / "p5_s3_skill_body.txt").read_text()
+  323	    # Normalise trailing whitespace on each line; preserve structure otherwise.
+  324	    def norm(s: str) -> str:
+  325	        return "\n".join(line.rstrip() for line in s.splitlines())
+  326	    assert norm(live) == norm(fixture), (
+  327	        "using-git-worktrees SKILL.md drifted from the P5.S3 token-budget "
+  328	        "fixture. If this is intentional, update "
+  329	        "tools/tasktool/tests/fixtures/p5_s3_skill_body.txt in the same commit."
+  330	    )
+  331	```
+  332	
+  333	- [ ] **Step 5.3: Run the regression test**
+  334	
+  335	```sh
+  336	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py::test_using_git_worktrees_matches_token_budget_fixture -v
+  337	```
+  338	
+  339	Expected: PASS.
+  340	
+  341	- [ ] **Step 5.4: Commit**
+  342	
+  343	```sh
+  344	git add tools/tasktool/tests/fixtures/p5_s3_skill_body.txt tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
+  345	git commit -m "P5.S3: freeze using-git-worktrees skill body as token-budget regression fixture"
+  346	```
+  347	
+  348	---
+  349	
+  350	## Task 5b: Subagent early-exit transcript fixture
+  351	
+  352	Spec §6 P5.S3 also asks for "a representative subagent transcript that previously loaded the full skill now loads only the early-exit block." Task 5 covers the byte-for-byte body freeze (silent-growth detection); this task covers the **transcript-side behavior**: the bytes a subagent actually consumes when it follows the early-exit instruction.
+  353	
+  354	**Files:**
+  355	- Create: `tools/tasktool/tests/fixtures/p5_s3_subagent_load.txt`
+  356	- Modify: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` (append transcript test)
+  357	
+  358	- [ ] **Step 5b.1: Define the load contract**
+  359	
+  360	A dispatched subagent that honours the `<SUBAGENT-STOP>` block should consume only the bytes between the opening and closing tags (inclusive of the tags themselves), and zero bytes from anywhere else in the skill. Capture that span as a fixture so a future edit that breaks the early-exit (e.g. moves content above the `<SUBAGENT-STOP>` tag, inlines the submodule reference back into the body, or renames the tag) makes the test fail visibly.
+  361	
+  362	- [ ] **Step 5b.2: Extract the early-exit span**
+  363	
+  364	```sh
+  365	python3 - <<'PY'
+  366	from pathlib import Path
+  367	text = Path("skills/using-git-worktrees/SKILL.md").read_text()
+  368	start = text.index("<SUBAGENT-STOP>")
+  369	end   = text.index("</SUBAGENT-STOP>") + len("</SUBAGENT-STOP>")
+  370	span  = text[start:end]
+  371	Path("tools/tasktool/tests/fixtures/p5_s3_subagent_load.txt").write_text(span)
+  372	print(f"captured {len(span)} chars, {span.count(chr(10))+1} lines")
+  373	PY
+  374	```
+  375	
+  376	Expected: prints something like `captured ~700 chars, ~3 lines`. The fixture file now contains exactly the bytes a compliant subagent loads.
+  377	
+  378	- [ ] **Step 5b.3: Append the transcript test**
+  379	
+  380	Append to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:
+  381	
+  382	```python
+  383	def test_subagent_early_exit_load_matches_fixture() -> None:
+  384	    """Spec §6 P5.S3 transcript regression. A compliant subagent loads only
+  385	    the bytes inside the <SUBAGENT-STOP> ... </SUBAGENT-STOP> block. This
+  386	    test reconstructs that span from the live skill and asserts it matches
+  387	    the frozen fixture, so any edit that displaces, renames, or splits the
+  388	    early-exit block surfaces here."""
+  389	    from pathlib import Path
+  390	    live = (Path(__file__).resolve().parents[3]
+  391	            / "skills" / "using-git-worktrees" / "SKILL.md").read_text()
+  392	    start_tag = "<SUBAGENT-STOP>"
+  393	    end_tag = "</SUBAGENT-STOP>"
+  394	    assert start_tag in live and end_tag in live, "early-exit tags missing"
+  395	    start = live.index(start_tag)
+  396	    end = live.index(end_tag) + len(end_tag)
+  397	    span = live[start:end]
+  398	
+  399	    fixture = (Path(__file__).resolve().parent / "fixtures"
+  400	               / "p5_s3_subagent_load.txt").read_text()
+  401	    assert span == fixture, (
+  402	        "subagent early-exit span drifted from the P5.S3 transcript fixture. "
+  403	        "Update tools/tasktool/tests/fixtures/p5_s3_subagent_load.txt in the "
+  404	        "same commit and explain the behavior change in the commit message."
+  405	    )
+  406	
+  407	    # Sanity: the early-exit block must be substantially smaller than the
+  408	    # full skill. If they were the same size, the load budget would be
+  409	    # unchanged from the rewritten skill body (which is already tiny but
+  410	    # still larger than the early-exit subset).
+  411	    assert len(span) < len(live), "early-exit span must be a proper subset"
+  412	    # The early-exit block must instruct against running tasktool start.
+  413	    assert "tasktool start" in span and (
+  414	        "do not call" in span.lower() or "do not" in span.lower()
+  415	    ), "early-exit block must forbid `tasktool start` from a subagent"
+  416	```
+  417	
+  418	- [ ] **Step 5b.4: Run the transcript test**
+  419	
+  420	```sh
+  421	python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py::test_subagent_early_exit_load_matches_fixture -v
+  422	```
+  423	
+  424	Expected: PASS.
+  425	
+  426	- [ ] **Step 5b.5: Commit**
+  427	
+  428	```sh
+  429	git add tools/tasktool/tests/fixtures/p5_s3_subagent_load.txt tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
+  430	git commit -m "P5.S3: subagent early-exit transcript fixture + behavior regression test"
+  431	```
+  432	
+  433	---
+  434	
+  435	## Task 6: Write failing subagent-guard tests for `tasktool start`
+  436	
+  437	**Files:**
+  438	- Modify: `tools/tasktool/tests/test_lifecycle_start.py` (append tests)
+  439	
+  440	Existing scaffolding (`run`, `seed`, `tasklist`, `ready_chain` helpers and the `tasktool start` `subprocess.run(...)` pattern) is already in place — use it.
+  441	
+  442	- [ ] **Step 6.1: Append the guard tests**
+  443	
+  444	Append these tests to `tools/tasktool/tests/test_lifecycle_start.py`:
+  445	
+  446	```python
+  447	REFUSAL_MARKER = "Subagents must inherit the parent's worktree"
+  448	
+  449	# Spec §5.3 verbatim sentence; the trailing period is load-bearing and
+  450	# asserted by test_start_refusal_message_matches_spec_verbatim.
+  451	REFUSAL_SPEC_SENTENCE_TEMPLATE = (
+  452	    "Subagents must inherit the parent's worktree; call the parent or "
+  453	    "'cd' into the existing recorded path: {worktree_path}."
+  454	)
+  455	
+  456	
+  457	def _run_with_env(root, *args, extra_env=None):
+  458	    """Like the module-level `run` but allows injecting / replacing env vars."""
+  459	    env = os.environ.copy()
+  460	    env["PYTHONPATH"] = PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
[truncated: 742 additional lines]


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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p5-s3-skill-rewrite-subagent-guard-workflow

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md

Additional context files:
- docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md
- docs/tasklist.json

Review output contract:
1. Findings
   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
     stable if this review is iterated in subsequent rounds.
   - Mark severity inline: `Severity: blocking | important | minor | nit`.
2. Open questions / assumptions
3. Suggested document edits
4. Verification gaps / commands that should be run, if any

End your review with this exact line, as plain text on its own line:

    Overall verdict: <ready|ready with small edits|revise>

Do not bold, italicise, prefix with `##`, split across lines, or drop the
word "Overall". Do not write `**Verdict: ready**` or place the value on a
new line after a heading.

Read the files from disk. Do not rely only on the snippets in this prompt.


## Target Preview

### docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md

    1	# P5.S3 — Skill rewrite + subagent guard + workflow updates — Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Collapse `using-git-worktrees` to ≤40 lines around a subagent early-exit, teach `tasktool start` to refuse dispatched subagents via three env signals, and update the coordinator's dispatch prompt templates to instruct subagents to export `SUPERSTAR_SUBAGENT_ROLE` so the runtime guard has the highest practical chance of firing when subagents follow the directive.
    6	
    7	**Architecture:** Five disjoint edit clusters:
    8	1. Skill rewrite (`using-git-worktrees/SKILL.md` shrunk; long-form submodule guard relocated to `references/submodules.md`).
    9	2. Subagent guard inside `tools/tasktool/commands.py::cmd_start` (three env signals with declared precedence, single refusal message, no fingerprinting).
   10	3. Workflow cross-reference updates in `tasklist-discipline`, `executing-plans`, `subagent-driven-development` (no touch to `finishing-a-development-branch` — that belongs to P5.S2).
   11	4. Coordinator-facing dispatch prompt updates: extend `skills/subagent-driven-development/implementer-prompt.md` (and the spec-reviewer / code-quality-reviewer prompt templates) to instruct each dispatched subagent to export `SUPERSTAR_SUBAGENT_ROLE=<role>` as its first shell command. This is a best-effort prose directive (Superstar does not wrap the harness's native dispatch tool), backed by the runtime guard in step 2 and the load-bearing prose rule in step 3. Tests assert the directive is present in every template and that a simulated `env -i bash` dispatch is correctly refused.
   12	5. Tests: signal-precedence and plain-shell false-negative coverage for the guard, template fixture tests for the shim directive, a token-budget regression fixture for the skill body, and a doc-shape test for the rewritten skill (≤40 lines, `<SUBAGENT-STOP>` block present).
   13	
   14	**Tech Stack:** Python (3.10+) for tasktool, pytest for tests, bash for fixtures, plain Markdown for skill / template edits.
   15	
   16	**Out of scope (handled elsewhere):**
   17	- Schema field reads/writes for `worktree_path` / `worktree_branch` / `worktree_in_place` — owned by P5.S1.
   18	- Worktree creation, adoption, prune, repair, finalize — owned by P5.S1 / P5.S2.
   19	- `finishing-a-development-branch` edits (post-merge prune step) — owned by P5.S2 per spec §5.3.2 (`:212-214`). The spec's P5.S3 slice paragraph at §6 (`:275-277`) lists all three workflow skills, but §5.3.2 splits ownership and assigns the prune step to P5.S2. Treat §5.3.2 as authoritative; this slice does not modify `finishing-a-development-branch`. Task 1.5 below verifies P5.S2 actually shipped the prune step before this slice starts so the workflow gap is not silently left open.
   20	- Removal of legacy `.claude/worktrees/` / `.codex/worktrees/` paths — deferred per spec §4.
   21	
   22	**Shim scope (read this before Task 8).** The spec at `:137` and `:286` says "the Claude shim and Codex shim" export `SUPERSTAR_SUBAGENT_ROLE`. The Superstar repo does not currently wrap the harness's native dispatch tool (Claude Code's `Task`, Codex's `spawn_agent`) — there is no Python or JS interceptor between the harness and the subagent process where an env var could be injected programmatically. The honest implementation is therefore a **best-effort prose guard**: the coordinator's dispatch prompt templates instruct the subagent to export the variable as its first shell command. The runtime guard in `tasktool start` (Task 7) is the load-bearing safety net; the prose rule in `tasklist-discipline` (Task 9) is the load-bearing *cultural* rule. The prompt-template directive (Task 8) raises the probability that the runtime guard fires in real use, but does not guarantee it. Task 8 acknowledges this explicitly and adds a simulated-harness transcript test (Task 8 Step 8.5) to prove the dispatch-time refusal actually works in a realistic shell when the directive is followed. If a future harness change exposes a real env-injection point, that integration can be wired in without breaking either the runtime guard or the prose rule.
   23	
   24	**Scheduling preconditions (verify before starting):**
   25	
   26	```sh
   27	tools/tasktool/tasktool show P5.S3
   28	tools/tasktool/tasktool schedule P5
   29	```
   30	
   31	Expected: `P5.S3` exists with `status: ready`, `depends_on: [P5.S1, P5.S2]`, `planning_status: proposed`. After plan-review passes, the writing-plans flow will ratify (coordinator-side `tasktool ratify P5.S3 --parallel-group …` is **not** part of this plan — the coordinator owns ratification).
   32	
   33	**Verification baseline (must pass against `main` before slice start, per spec §10):**
   34	
   35	```sh
   36	tools/tasktool/tasktool validate --strict-format
   37	python -m pytest tools/tasktool/tests -q
   38	```
   39	
   40	---
   41	
   42	## File Structure
   43	
   44	| File | Status | Responsibility |
   45	|---|---|---|
   46	| `skills/using-git-worktrees/SKILL.md` | rewrite (226 → ≤40 lines) | Subagent early-exit block + 4 one-line rules. |
   47	| `skills/using-git-worktrees/references/submodules.md` | create | Submodule guard lifted from current SKILL.md §0; loaded on demand. |
   48	| `skills/tasklist-discipline/SKILL.md` | append paragraph | Subagents must inherit cwd; never call `tasktool start`. |
   49	| `skills/executing-plans/SKILL.md` | minor edits | Add cross-reference to the rewritten skill's early-exit; mention parent-creates-worktree pattern. |
   50	| `skills/subagent-driven-development/SKILL.md` | minor edits | One-line reminder that subagents inherit cwd and never call `tasktool start`. |
   51	| `skills/subagent-driven-development/implementer-prompt.md` | minor edits | Add explicit `SUPERSTAR_SUBAGENT_ROLE=implementer` directive in the dispatch template. |
   52	| `skills/subagent-driven-development/spec-reviewer-prompt.md` | minor edits | Same directive, role=`spec-reviewer`. |
   53	| `skills/subagent-driven-development/code-quality-reviewer-prompt.md` | minor edits | Same directive, role=`code-quality-reviewer`. |
   54	| `tools/tasktool/commands.py` | extend `cmd_start` | Three-signal subagent guard with declared precedence; refusal message verbatim from spec §5.3. |
   55	| `tools/tasktool/tests/test_lifecycle_start.py` | extend | Add guard tests (precedence, refusal message, plain-shell false-negative). |
   56	| `tools/tasktool/tests/fixtures/p5_s3_skill_body.txt` | create | Frozen copy of the rewritten skill body for the token-budget regression test. |
   57	| `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` | extend | Skill-shape tests: ≤40 lines, contains `<SUBAGENT-STOP>` block, contains `tasktool start` reference, references `references/submodules.md`. |
   58	| `tools/tasktool/tests/test_subagent_prompt_shim.py` | create | Assert each of the three subagent-prompt templates exports `SUPERSTAR_SUBAGENT_ROLE=<expected>`. |
   59	
   60	---
   61	
   62	## Task 1: Establish baseline + lifecycle start
   63	
   64	**Files:** none — verification + tasktool lifecycle only.
   65	
   66	- [ ] **Step 1.1: Verify scheduling preconditions**
   67	
   68	```sh
   69	tools/tasktool/tasktool show P5.S3
   70	tools/tasktool/tasktool schedule P5
   71	```
   72	
   73	Expected: `P5.S3` exists with `depends_on: [P5.S1, P5.S2]`. If absent or differs, stop — coordinator needs to fix the row before this plan can execute.
   74	
   75	- [ ] **Step 1.2: Verify baseline tests pass**
   76	
   77	```sh
   78	tools/tasktool/tasktool validate --strict-format
   79	python -m pytest tools/tasktool/tests -q
   80	```
   81	
   82	Expected: both exit 0. If anything fails on `main`, stop and report — do not start the slice over a red baseline.
   83	
   84	- [ ] **Step 1.3: Start the slice**
   85	
   86	```sh
   87	tools/tasktool/tasktool start P5.S3
   88	```
   89	
   90	Expected: status flips to `in_progress`. This is the lifecycle gate; do not substitute prose, TodoWrite, or hand JSON edits.
   91	
   92	- [ ] **Step 1.4: Verify P5.S2 shipped the `finishing-a-development-branch` prune step**
   93	
   94	This slice deliberately does not modify `finishing-a-development-branch` (spec §5.3.2 assigns the prune step to P5.S2). Confirm P5.S2 actually delivered that edit before this slice begins, so the workflow gap is not silently left open:
   95	
   96	```sh
   97	tools/tasktool/tasktool show P5.S2
   98	grep -nE "tasktool worktree prune" skills/finishing-a-development-branch/SKILL.md
   99	```
  100	
  101	Expected: `P5.S2` status is `done` (closed by P5.S2's external review gate), and `grep` returns at least one match showing the post-merge prune step. If `P5.S2` is not done, **stop** — this slice waits on it. If `P5.S2` is done but `finishing-a-development-branch` does not mention `tasktool worktree prune`, stop and surface the gap to the coordinator (this would be a P5.S2 closeout defect, not a P5.S3 problem to paper over).
  102	
  103	- [ ] **Step 1.5: No commit yet.**
  104	
  105	This task produces no diff. Proceed to Task 2.
  106	
  107	---
  108	
  109	## Task 2: Extract submodule guard to `references/submodules.md`
  110	
  111	**Files:**
  112	- Create: `skills/using-git-worktrees/references/submodules.md`
  113	
  114	- [ ] **Step 2.1: Create the references directory and submodules reference**
  115	
  116	```sh
  117	mkdir -p skills/using-git-worktrees/references
  118	```
  119	
  120	Write `skills/using-git-worktrees/references/submodules.md` with this content:
  121	
  122	```markdown
  123	# Submodule guard for using-git-worktrees
  124	
  125	Load this reference **only** when `tasktool start` reports a worktree-detection conflict caused by a submodule, or when the early-exit block in `SKILL.md` cannot decide whether the current directory is a linked worktree or a submodule checkout.
  126	
  127	## Why this matters
  128	
  129	`GIT_DIR != GIT_COMMON_DIR` is true in two distinct situations:
  130	
  131	1. The current directory is a linked git worktree (e.g. `.worktrees/worktree-p5-s3-…`).
  132	2. The current directory is a git submodule checkout.
  133	
  134	The submodule case must **not** be treated as a worktree. Treating a submodule as a linked worktree skips legitimate worktree creation and corrupts the slice's evidence boundary.
  135	
  136	## Disambiguating
  137	
  138	Run:
  139	
  140	```sh
  141	git rev-parse --show-superproject-working-tree 2>/dev/null
  142	```
  143	
  144	- Empty output (or non-zero exit): you are **not** in a submodule. The `GIT_DIR != GIT_COMMON_DIR` signal is genuine — treat the directory as a linked worktree.
  145	- Non-empty output (a path): you are inside a submodule of that superproject. Treat the directory as a normal repo checkout and do not skip the worktree creation step.
  146	
  147	## What to do
  148	
  149	If you discover you are in a submodule and tasktool refuses to proceed, leave the submodule (`cd` to the superproject root, or to the authoritative checkout) and re-run `tasktool start <id>` from there. Do not attempt to nest a worktree inside the submodule.
  150	```

[truncated: 971 additional lines]

<!-- superstar-prompt:end -->