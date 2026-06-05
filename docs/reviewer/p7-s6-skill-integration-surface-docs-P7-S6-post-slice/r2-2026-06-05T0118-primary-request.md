<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 2 of p7-s6-skill-integration-surface-docs-P7-S6-post-slice.

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
| 1 | revise | 1 | 1 |

## Prior-round findings

Source: merged findings from r1 (authoritative)

# Merged findings for r1

## Primary

# Review — 2026-06-04-P7-S6-skill-integration-surface-docs.md (post-slice, round 1)

- Target: `docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md`
- Request: `docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/r1-2026-06-05T0106-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: blocking  
The slice lifecycle start was not completed. The plan makes Task 0 mandatory and says `tasktool start P7.S6` must move the row to `in_progress` and record the worktree base SHA before edits ([docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven/docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md:49), lines 56-64). Live tracker state still has `"started": null` and `"status": "ready"` ([docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven/docs/tasklist.json:414)). This is not just bookkeeping: P7.S6’s new integrate-current-main guidance depends on `worktree_base_sha`, so the slice cannot truthfully pass the completion gate until lifecycle state is repaired or explicitly documented with a corrective note.

2. Open questions / assumptions

I assume this review is intended to gate the implementation commits currently on `worktree-p7-s6-skill-changes-subagent-driven` at `84cc48e`, ahead of `main` at `0290ebd`.

3. Suggested document edits

No plan/prose edits are needed for the implemented skill changes. The docs match the spec’s §4.F requirements: playbook, surface check before dispatch, integrate-current-main checkpoint, tasklist-discipline command/model docs, and phase/writing plan surface table requirements are present.

4. Verification gaps / commands that should be run

Already verified:
`cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -q` → 17 passed.  
`cd tools/tasktool && python -m pytest -q` → 779 passed.  
`tasktool surface check --help`, `tasktool reserve add --help`, `tasktool coordinate --help`, and `tasktool worktree status --help` all print usage.

Still required before close:
Repair/record the P7.S6 lifecycle state so `tasktool show P7.S6` no longer reports `status: ready` / `started: null`, then rerun `tasktool worktree status P7.S6 --integration` before accepting the post-slice gate.

Overall verdict: revise


## Sweep 1

# Review — 2026-06-04-P7-S6-skill-integration-surface-docs.md (post-slice, round 1)

- Target: `docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md`
- Request: `docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/r1-2026-06-05T0106-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

S1.F1. Severity: blocking. P7.S6 was implemented without completing the slice lifecycle start gate. The plan requires `tasktool start P7.S6` before edits and expects the row to move to `in_progress` ([docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md:56-64](</home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven/docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md:56>)). The live tracker still has `"started": null` and `"status": "ready"` for S6 ([docs/tasklist.json:414](</home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven/docs/tasklist.json:414>), [docs/tasklist.json:415](</home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven/docs/tasklist.json:415>)), and `tasktool show P7.S6` also reports `status: ready`. That means the post-slice completion gate is reviewing committed implementation work for a slice the tracker still says has not started.

2. Open questions / assumptions

None for the document implementation itself. I treated the untracked `docs/reviewer/...post-slice/` path as the active review chain output, not as an author-owned missing artifact.

3. Suggested document edits

No changes needed to the skill docs or test assertions. The implemented prose matches the §4.F deliverables: surface check before dispatch, integrate-current-main checkpoint before post-slice review, playbook reference, tasklist-discipline command/model docs, and phase/writing plan surface table requirements.

Required fix is tracker/lifecycle, not prose: run the proper slice lifecycle mutation so P7.S6 is no longer `ready` with `started: null`, then commit that tracker mutation before re-requesting the gate.

4. Verification gaps / commands that should be run

Already run during review:
- `python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` -> 17 passed
- `cd tools/tasktool && python -m pytest -q` -> 779 passed
- `tasktool surface check --help`, `tasktool reserve add --help`, `tasktool coordinate --help`, `tasktool worktree status --help` -> all usage commands resolved
- `tasktool worktree status P7.S6 --integration` -> base ahead 0 commits; landed since base none; P7.S1/P7.S2 undetermined

Still needed after fixing S1.F1:
- `tasktool show P7.S6`
- `git status --short`
- Re-run at least `python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q` if the tracker commit touches only lifecycle state; full suite is optional but defensible.

Overall verdict: revise



## Resolution report for prior round

# Resolution for r1

Both reviewers (primary + sweep) raised the same single blocking finding and
explicitly confirmed the §4.F skill/prose deliverables are complete and all
tests pass. Only the lifecycle/tracker state needed repair.

## F1
Status: fixed
Evidence:
- Root cause: `tasktool start P7.S6` stamped `status=in_progress`, `started`,
  and `worktree_base_sha` on the canonical tracker (the `tasktool start`
  output confirmed it "routed mutation to authoritative checkout"), but the
  mutation was left **staged and uncommitted** on `main`. The slice worktree's
  committed copy of `docs/tasklist.json` therefore still showed
  `status: ready` / `started: null`, which is what the reviewer read.
- Fix: committed the staged lifecycle stamps on the authoritative checkout —
  Commit `35f5171` ("P7: record S5/S6 slice lifecycle start (in_progress +
  base SHA)"), then ran the slice's own integrate-current-main checkpoint from
  the worktree (`tasktool worktree status P7.S6 --integration` → base ahead 1
  commit; clean `git merge main`, merge commit `102536b`).
- Verification:
  - `tasktool show P7.S6` (from the slice worktree, post-merge) → `status: in_progress`, `started: 2026-06-05`.
  - `tasktool worktree status P7.S6 --integration` → `worktree_base_sha: 0290ebd…`, base now level after merge; no landed siblings sharing this slice's surface.
  - `docs/tasklist.json` in the worktree now matches the canonical tracker (S6 `in_progress` with `worktree_base_sha` recorded).

Notes:
The integrate-current-main checkpoint is the very procedure this slice adds to
`subagent-driven-development`; resolving F1 dogfooded it. The base advanced by
exactly one commit (the tracker lifecycle commit); the merge touched only
`docs/tasklist.json` with no conflicts, so no registry-merge-playbook handling
was required. P7.S1/P7.S2 report `unknown` in the integration status because
the landing heuristic could not prove them landed, but both are `done`
ancestors already contained in the base history and share no surface with this
docs-only slice — nothing to integrate.

## S1.F1
Status: fixed
Evidence:
- Same finding as F1 (sweep-reviewer's namespaced ID). Resolved by the same
  commit `35f5171` + integrate-current-main merge `102536b`. See F1 above for
  full evidence and verification.

Notes:
Sweep reviewer's "still needed" list is satisfied: `tasktool show P7.S6`
reports `in_progress`; `git status --short` is clean in the worktree; the
docs-lifecycle test file still passes (17 passed) and the full tasktool suite
was green (779 passed) at the reviewed commit `84cc48e`, unchanged by the
tracker-only merge.


## Changes since prior round

Worktree status: clean

### git diff base..HEAD

diff --git a/docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/.reviewer-output/r1-primary/codex-events.jsonl b/docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/.reviewer-output/r1-primary/codex-events.jsonl
new file mode 100644
index 0000000..bd951ff
--- /dev/null
+++ b/docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/.reviewer-output/r1-primary/codex-events.jsonl
@@ -0,0 +1,66 @@
+{"type":"thread.started","thread_id":"019e951a-5a22-7971-bf7e-0082751e0a90"}
+{"type":"turn.started"}
+{"type":"item.completed","item":{"id":"item_0","type":"agent_message","text":"Using `tasklist-discipline` context for this review because the target is a tasktool-managed slice completion gate. I’ll read the live repo state and compare it against the plan/spec acceptance criteria before giving findings."}}
+{"type":"item.started","item":{"id":"item_1","type":"command_execution","command":"/usr/bin/zsh -lc \"sed -n '1,220p' /home/simon/.codex/plugins/cache/superstar-dev/superstar/6.8.5/skills/tasklist-discipline/SKILL.md\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_1","type":"command_execution","command":"/usr/bin/zsh -lc \"sed -n '1,220p' /home/simon/.codex/plugins/cache/superstar-dev/superstar/6.8.5/skills/tasklist-discipline/SKILL.md\"","aggregated_output":"---\nname: tasklist-discipline\ndescription: Use whenever planning, closing slices/phases, or referencing work items in a project that uses docs/tasklist.json. Teaches the tasktool CLI surface and the gating concepts; the CLI enforces the rules.\n---\n\n# TASKLIST Discipline\n\nA `docs/tasklist.json` file is the canonical, top-level tracker for the project. It groups work into **phases**, **slices**, **tasks**, and **cross-cutting** items, each with a stable, never-renumbered ID. All mutations flow through `tasktool`; a pre-commit hook refuses non-canonical bytes, orphaned spec/plan filenames, and any commit that touches the legacy `docs/TASKLIST.md`.\n\nUse the global `tasktool` shim installed by `bash <active-superstar-checkout>/tools/tasktool/install.sh`. If `tasktool` is missing or reports a shim/source version mismatch, reinstall that shim from the active Superstar checkout before continuing.\n\n`.tasktool/config.json` must set `tasklist.mutation_mode` to `authoritative-checkout` for normal superstar work. Mutating commands route through the configured authoritative checkout instead of editing the local worktree's `docs/tasklist.json` directly. Treat that routing as the source of truth: run `tasktool` from the implementation worktree, let the tool acquire the shared lock and update the authoritative checkout, then continue from the same implementation worktree. If a mutating command reports that no authoritative-checkout routing is configured, stop and run `tasktool config init-authority --branch <main-branch>` from the authoritative checkout before retrying; use `tasktool config init-local` only for explicit local-only test fixtures or non-workflow throwaway repos.\n\n**Announce at start:** \"I'm using the tasklist-discipline skill to update docs/tasklist.json via tasktool.\"\n\n## When to use\n\n- About to plan or write a new spec → allocate an ID with `tasktool create phase|slice|task|cross …` **before** the spec file lands. The TASKLIST row is the allocation; the spec/plan/reviewer-chain filenames are downstream.\n- About to start implementation for a slice → `tasktool start <slice-id>`. This records the lifecycle start and moves the row to `in_progress`; do this before dispatching implementation or editing implementation files.\n- About to close a slice → `tasktool close <slice-id>`. The CLI enforces the post-slice external-review gate.\n- About to close a phase → `tasktool archive-phase <phase-id>`. For `done` phases the CLI enforces the post-phase gate and writes the archive note; for `cancelled` phases it archives without a post-phase review because nothing shipped.\n- About to close a cross-cutting item → `tasktool close <x-id>`. The CLI marks it done and archives it by default. Use `--no-archive` only when the closed X-item must remain visible temporarily; later run `tasktool archive-cross <x-id>`.\n- Entering a slice → `tasktool brief <slice-id>` instead of reading the JSON.\n- Onboarding a project — `[[project-setup]]` runs `tasktool init` and installs the hook.\n\nOnboarding has a hard setup boundary: after `[[project-setup]]` configures `.tasktool/config.json` with authoritative routing, creates or imports `docs/tasklist.json`, installs hooks, installs the global `external-reviewer` shim or replaces a legacy repo-local reviewer bridge with the compatibility shim, moves legacy `docs/superpowers/` files, or edits `CLAUDE.md` / `AGENTS.md`, that setup/migration must be committed, stashed, or explicitly paused before implementation work begins.\n\n**Implementation isolation boundary:** If tasklist work is tied to starting, continuing, reviewing, or closing an implementation slice, invoke `[[using-git-worktrees]]` before tasktool status/ref/note/close mutations for an active implementation slice. `tasktool start`, `tasktool set`, `tasktool ref`, `tasktool note`, `tasktool close`, and reviewer-chain registration are not harmless bookkeeping when run from a shared checkout: they dirty the slice evidence set. A normal `main`/`master` checkout is planning/setup/read-only by default unless the user explicitly opts out of isolation in the current turn. Invoke `tasktool` from the active implementation worktree; authoritative routing sends the mutation to the configured checkout.\n\n**Administrative closeout exception:** Pure lifecycle bookkeeping for already-superseded planning rows may run from the authoritative checkout without creating a new implementation worktree. Examples: `tasktool cancel <phase-id> --cascade --reason \"…\"`, `tasktool archive-phase <phase-id>` on that cancelled phase, or adding refs/notes that explain the cancellation. Do not use this exception to edit implementation files, close shipped slices, register reviewer evidence for active implementation work, or mix new product changes into the bookkeeping commit.\n\n**Subagent rule (load-bearing).** Parents create or adopt worktrees via `tasktool start <slice-id>`. Dispatched subagents inherit the parent's cwd and **must not** call `tasktool start` — implementation work happens inside the parent's already-recorded worktree, and a subagent starting a slice double-counts the lifecycle row and corrupts the slice's worktree fields. Tasktool refuses `tasktool start` when it observes a dispatched-subagent signal (`SUPERSTAR_SUBAGENT_ROLE`, `CLAUDE_AGENT_ROLE`, or the test-only `SUPERSTAR_FORCE_SUBAGENT=1`). The runtime guard is detection-dependent — a coordinator that loses its env (e.g. `env -i`) will look like a top-level invocation — so **this prose rule is the load-bearing guard**; the env signals are belt-and-braces.\n\n## Conceptual model\n\n| Scope | Short form | Fully-qualified |\n|-------|-----------|-----------------|\n| Phase | `P2` | `P2` |\n| Slice | `S1` (follow-up: `S5a`) | `P2.S1` (`P2.S5a`) |\n| Task | `T3` | `P2.S5.T3` |\n| Cross-cutting | `X4` | `X4` (top-level; not nested under a phase) |\n\nIDs are assigned at birth and **never renumbered**. The `tasktool create` family does orphan-aware allocation (`max+1` across `docs/tasklist.json`, `docs/specs/`, `docs/plans/`, `docs/reviewer/`) and prints the new ID.\nArchived X IDs are still reserved, so a new cross-cutting item will not reuse an ID that has moved to `archived_cross_cutting`.\nCommands run against an archived X-id report a may-already-be-archived hint because archive files are evidence, not part of the active tasklist workflow surface.\n\nStatus enum: `ready | in_progress | blocked | done | cancelled`. Only slices may take `blocked`. `cancelled` is a terminal status (peer of `done`) recording work that was intentionally not shipped — cancelled, deferred, abandoned, superseded. It is set only via `tasktool cancel <id> --reason \"…\"`; the `set` verb does not accept it. Tasks cannot be `cancelled`; cancel the parent slice instead.\n\n`blocked` is only set via `tasktool block <slice-id> --on …`. Emoji are a render concern; `tasktool render` and `tasktool brief` handle that. `tasktool start <slice-id>` is the normal way to enter `in_progress`; `tasktool set <id> --status in_progress` is a compatibility alias for older plans and ad-hoc rows. `tasktool unblock <slice-id> --resume` resumes through the same lifecycle path and stamps `started` when needed. `done` requires `closed`; the CLI stamps it.\n\nPhase planning uses separate scheduling metadata. `planning_path` points at the phase-scoped planning/design document. `depends_on` records planned slice sequencing; it is not the same as runtime `blocked_on`. `planning_status` is `proposed | ratified | superseded`, and `parallel_group` names slices intended to be planned or executed together.\n\n## Daily commands\n\n```sh\ntasktool brief <id>            # start-of-work primer for slice or phase\ntasktool show <id>             # full detail\ntasktool list --open           # everything ready / in_progress / blocked\ntasktool create slice <phase-id> --title \"...\"\ntasktool prepare existing <id> --plan path/to/plan.md\ntasktool artifact add <id> --kind spec --path path/to/spec.md\ntasktool artifact status <id> --strict\ntasktool artifact commit <id> --message \"...\"\ntasktool start <slice-id>      # lifecycle start + in_progress\ntasktool set <id> --status in_progress  # compatibility alias\ntasktool note <id> --append \"...\"\ntasktool ref <id> --add path/to/artifact\ntasktool block <slice-id> --on P2.S5\ntasktool deps <slice-id> --add P2.S1\ntasktool ratify <slice-id> --parallel-group bootstrap\ntasktool schedule <phase-id>\ntasktool ready-slices <phase-id>\ntasktool phase-status\ntasktool close <slice-id>      # enforces post-slice review gate\ntasktool close <x-id>          # closes and archives cross-cutting by default\ntasktool close <x-id> --no-archive\ntasktool cancel <id> --reason \"<text>\"           # terminate without shipping\ntasktool cancel <phase-id> --reason \"...\" --cascade  # cancel a phase + its open slices\ntasktool cancel <x-id> --reason \"...\" --no-archive   # keep cancelled X visible\ntasktool archive-cross <x-id>  # archive a done visible cross-cutting item\ntasktool archive-phase <phase-id>  # done phases require post-phase review; cancelled phases bypass it\ntasktool validate              # full validation\n```\n\nRun `tasktool --help` (or `tasktool <cmd> --help`) for the full surface.\n\n## Gating concepts (why the CLI refuses you)\n\n- **Post-slice external review.** `tasktool close <slice-id>` reads `chain.json` from the slice's reviewer chain folder (`docs/reviewer/<slug>-post-slice/` by default; override with `--reviewer-chain`). It refuses unless the latest round's verdict ∈ {`ready`, `ready with small edits`}. Per-task internal reviews do not satisfy this gate.\n- **Post-phase external review.** `tasktool archive-phase <phase-id>` refuses until every slice is `done` *and* the phase's post-phase chain returns `ready` / `ready with small edits`. If the phase itself is `cancelled`, archive still requires every child slice to be terminal, but it bypasses the post-phase chain because cancelled work never shipped.\n- **Cross-cutting archive.** `tasktool close <x-id>` is ungated by external review and moves the completed X-item out of active `cross_cutting` into `archived_cross_cutting`, with a lossless markdown archive under `docs/archived-tasks/`. `--no-archive` leaves it visible as `done`; `tasktool archive-cross <x-id>` moves it later without sending another done notification.\n- **`--skip-review-gate`** exists for emergencies and is recorded in the slice/phase `notes` with a timestamp. Use it only when the operator has explicitly chosen to bypass.\n\nSee `[[external-review]]` for how to drive the reviewer.\n\n## Cancellation\n\n- `tasktool cancel <id> --reason \"<text>\"` is the only sanctioned path. Applies to phases, slices, and cross-cutting items. Tasks cannot be cancelled — cancel the parent slice.\n- The reason is required and is recorded in `notes` as `Cancelled <ISO-ts>: <reason>` (and `(cascaded from <phase-id>)` for child slices cancelled via `--cascade`).\n- Cancellation **bypasses** the post-slice and post-phase external-review gates — cancelled work never shipped. A cancelled phase may be archived with `tasktool archive-phase <phase-id>` without `--skip-review-gate` or a post-phase reviewer chain.\n- A cancelled slice does **not** satisfy a downstream `depends_on`. `tasktool schedule <phase-id>` emits `cancelled_deps` for affected slices; `ready-slices` omits them. Cancel the downstream too or remove the dependency.\n- Cancelled cross-cutting items auto-archive by default. Use `--no-archive` to keep the cancelled row visible in the active list; archive later with `archive-cross`.\n- Phase cancellation refuses if any slice is still open. Use `--cascade` to cancel open slices in one call; already-done slices are never touched.\n- Edits on cancelled rows: `note --append`, `ref`, and `title` are allowed (post-mortem context); `set`, `close`, `start`, `block`, `unblock`, `deps`, `ratify`, and `note --replace` are refused.\n\n## Hand-edits are an emergency path, not a workflow\n\nIf a raw edit is genuinely needed:\n\n```sh\nTASKTOOL_RAW=1 $EDITOR docs/tasklist.json\ntasktool validate --normalise\n```\n\n`--normalise` re-serialises the file through the canonical formatter so the pre-commit hook accepts it. There is no `tasktool edit --raw` subcommand by design — the friction keeps agents on the sanctioned commands.\n\n## New work mid-slice\n\n| Scenario | Action |\n|----------|--------|\n| Incidental fix in the same area | `tasktool create task <slice-id> --title ...` |\n| Real unit of work | `tasktool create slice <phase-id> --title ...` (or `--follow-up <slice-id>` for a letter-suffix) |\n| Bug surfaced by review | Inline task if cheap; follow-up slice if it deserves its own scope. |\n| Cross-cutting, unscheduled | `tasktool create cross --title ...` |\n\nCreating a new slice or X-item is allocation/tracking only. It does not authorize implementing that work in the current slice worktree. If the discovery is truly incidental to the active slice, add an in-slice task and keep going. If it is real follow-up work, record it and defer until the current slice closes, or create a separate isolated worktree for that follow-up after the current slice boundary is clean.\n\n## Referencing items in artifacts\n\n- Specs, plans, reviewer chain folders: fully-qualified ID at first mention (`P9.S3a`), short form afterwards.\n- Plan and spec filenames embed the ID: `YYYY-MM-DD-<id>-<slug>(-design).md`. The pre-commit hook rejects filenames whose ID has no `tasklist.json` row.\n- Phase planning docs should be registered through `planning_path` once supported. During bootstrap or migration, either attach the document to `spec_path` for the phase ID or keep unregistered drafts outside orphan-checked paths such as `docs/_drafts/`.\n- Commit messages may use either form; prefer fully-qualified for cross-phase commits.\n\n## Workflow artifacts\n\nSpec, plan, handoff, reviewer-chain, and archived-task paths are workflow artifacts. Register them through `tasktool artifact add` or `tasktool prepare`; do not hand-edit `docs/tasklist.json` refs for these paths. Use `tasktool artifact status <id> --strict` before handing work to another agent.\n\n## workflow_step\n\nSlices and phases carry an optional `workflow_step` field that tracks where the row is in the spec → plan → implement → done sequence. The two enums are intentionally different:\n\n- **Slice steps:** `spec | plan | implement | done`. Set manually as the slice progresses through its lifecycle.\n- **Phase steps:** `spec | ready | in_progress | done`. Set manually for `spec` / `ready`; `in_progress` / `done` are observable from child slice status and surface in `tasktool infer-step`.\n- **Cross-cutting (`X*`) rows have no `workflow_step`** — they skip the spec/plan loop.\n\nIn this revision the field is **informational only**. No tasktool command auto-advances it; no operation is refused based on its value. Future slices in `P6 — Programmatic Workflow Enhancements` will introduce auto-advance and downstream automation (statusline / session-rename).\n\n### Setting it manually\n\n```bash\ntasktool set P6.S1 --workflow-step plan\ntasktool set P6 --workflow-step ready\ntasktool set P6.S1 --clear-workflow-step\n```\n\n### Inspecting inferred values\n\n```bash\ntasktool infer-step P6.S1                 # text\ntasktool infer-step P6.S1 --format json   # structured\ntasktool infer-step --all --diff          # rows where stored != inferred (exit 1 if drift, 0 otherwise)\n```\n\n`infer-step` is read-only — it never mutates state. Use it to sanity-check what the field *would* be if you set it manually.\n\n### Transient slice review block\n\nThe external-reviewer script writes a small transient block (`review_active`, `review_stage`) on slices when a plan or post-slice review is in progress. The block is cleared when the slice's `workflow_step` changes or when the review finishes. Agents and skills should not write these fields directly.\n\n## Red flags\n\n| Thought | Reality |\n|---------|---------|\n| \"I'll just edit `docs/tasklist.json` by hand quickly.\" | The hook will refuse non-canonical bytes; `tasktool` is faster than fighting the hook. Use the CLI. |\n| \"I'll mark the slice `done` with `set` instead of `close` to skip the review gate.\" | `tasktool set --status done` routes through the same gate as `close`. The gate cannot be bypassed by reaching for a different subcommand. |\n| \"I'll mark this slice `done` to make it disappear.\" | Use `cancel`, not `close`. `done` is a lie if the work never shipped — and `close` runs the post-slice review gate, which is meaningless on cancelled work. |\n| \"I'll commit the spec now and add the row after.\" | The pre-commit hook rejects orphan spec/plan filenames. Allocate first. |\n| \"`tasktool` says the verdict isn't ready, but the reviewer comments look fine.\" | Re-read the verdict line. `revise` is `revise`. If the reviewer chain is mis-parsed, fix the chain; do not pass `--skip-review-gate` casually. |\n| \"I'll bring back `docs/TASKLIST.md` for readability.\" | The hook refuses commits that touch it. Use `tasktool render` if you want markdown. |\n| \"I'll just renumber IDs to match execution order.\" | No. IDs are stable. Execution order lives in the array order; IDs preserve creation order. |\n| \"Setup files are just scaffolding; I'll leave them dirty while implementing.\" | No. Setup/migration artifacts make post-slice review scope ambiguous. Resolve the setup boundary first. |\n| \"I created a follow-up slice/X-item, so I can knock it out in this worktree.\" | No. Allocation is not implementation permission. Follow-up work gets deferred or gets its own isolated worktree. |\n| \"I only need to add refs or flip the row before creating the worktree.\" | No. For an active implementation slice, tasktool refs/status/notes are part of the slice artifact set. Isolate first. |\n| \"The slice is currently blocked, so I'll add `blocked_on` to model the phase plan.\" | No. Use `depends_on` for planned sequencing. Use `blocked_on` only for active runtime blockers. |\n\n## Integration\n\n- `[[writing-plans]]` — embeds slice IDs in plan filenames; calls `tasktool show <id>` for context.\n- `[[brainstorming]]` — allocates IDs via `tasktool create` before writing the spec.\n- `[[external-review]]` — passes `docs/tasklist.json` (or `tasktool render` output) as `--context`.\n- `[[subagent-driven-development]]` — calls `tasktool close <slice-id>` at slice end and `tasktool archive-phase` at phase end.\n- `[[project-setup]]` — runs `tasktool init` and `install.sh --hook`.\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_2","type":"command_execution","command":"/usr/bin/zsh -lc 'rg -n \"P7.S6|skill integration|integration-surface|surface/reservation|registry-merge\" /home/simon/.codex/memories/MEMORY.md'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_2","type":"command_execution","command":"/usr/bin/zsh -lc 'rg -n \"P7.S6|skill integration|integration-surface|surface/reservation|registry-merge\" /home/simon/.codex/memories/MEMORY.md'","aggregated_output":"","exit_code":1,"status":"failed"}}
+{"type":"item.completed","item":{"id":"item_3","type":"agent_message","text":"The memory quick pass did not surface a specific prior note for this slice, so I’m treating the live repo as authoritative. Next I’m checking the actual changed files, tracker row, and verification evidence rather than the preview text."}}
+{"type":"item.started","item":{"id":"item_4","type":"command_execution","command":"/usr/bin/zsh -lc 'git status --short'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_4","type":"command_execution","command":"/usr/bin/zsh -lc 'git status --short'","aggregated_output":"?? docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_5","type":"command_execution","command":"/usr/bin/zsh -lc 'git log --oneline --decorate -8'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_5","type":"command_execution","command":"/usr/bin/zsh -lc 'git log --oneline --decorate -8'","aggregated_output":"84cc48e (HEAD -> worktree-p7-s6-skill-changes-subagent-driven) P7.S6: require surface/reservation tables in phase-planning and writing-plans\n6dc8312 P7.S6: document surface/reserve/coordinate in tasklist-discipline\n4140bb5 P7.S6: surface-check gate + integrate-current-main checkpoint in subagent-driven-development\n6e9f0bf P7.S6: add centralized-registry merge playbook reference\n0290ebd (main) P7.S5: add conservative worktree sync plan\n0b66d8d P7.S6: set workflow-step=implement after plan review\n1d55df5 P7.S6: add skill-integration-surface plan + handoff (plan review ready)\n9c17373 P7.S3: record worktree prune in tracker\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_6","type":"command_execution","command":"/usr/bin/zsh -lc 'rg -n \"test_registry_merge_playbook_exists|test_subagent_driven_development_runs_surface_check_before_parallel_dispatch|test_subagent_driven_development_has_integrate_main_checkpoint|test_tasklist_discipline_documents_surface_reserve_coordinate|test_phase_planning_and_writing_plans_document_surface_tables\" tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_6","type":"command_execution","command":"/usr/bin/zsh -lc 'rg -n \"test_registry_merge_playbook_exists|test_subagent_driven_development_runs_surface_check_before_parallel_dispatch|test_subagent_driven_development_has_integrate_main_checkpoint|test_tasklist_discipline_documents_surface_reserve_coordinate|test_phase_planning_and_writing_plans_document_surface_tables\" tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py'","aggregated_output":"167:def test_registry_merge_playbook_exists() -> None:\n183:def test_subagent_driven_development_runs_surface_check_before_parallel_dispatch() -> None:\n193:def test_subagent_driven_development_has_integrate_main_checkpoint() -> None:\n204:def test_tasklist_discipline_documents_surface_reserve_coordinate() -> None:\n223:def test_phase_planning_and_writing_plans_document_surface_tables() -> None:\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_7","type":"command_execution","command":"/usr/bin/zsh -lc 'tasktool show P7.S6'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_7","type":"command_execution","command":"/usr/bin/zsh -lc 'tasktool show P7.S6'","aggregated_output":"# P7.S6 — Skill changes: subagent-driven-development checkpoint + registry-merge-playbook; tasklist-discipline; phase-planning/writing-plans tables\nstatus: ready\nworkflow_step: implement\ndepends_on:\n  - P7.S2\n  - P7.S3\n  - P7.S4\nplanning_status: ratified\nrefs:\n  - docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md\n  - docs/handoffs/2026-06-04-P7-S6-skill-integration-surface-docs-prompt.md\n  - docs/reviewer/p7-s6-skill-integration-surface-docs-plan\nnotes:\nSpec §4.F. Surfaces: skills. subagent-driven-development: surface check before parallel dispatch + integrate-current-main checkpoint before post-slice review + references/registry-merge-playbook.md. tasklist-discipline command docs + red flags. phase-planning/writing-plans surface/reservation tables.\n\nTasks:\n","exit_code":0,"status":"completed"}}
+{"type":"item.completed","item":{"id":"item_8","type":"agent_message","text":"One concrete issue is already visible: implementation commits exist on the worktree branch, but the tracker row still reports `status: ready`, which conflicts with the plan’s mandatory lifecycle start. I’m checking whether there are additional acceptance gaps in the docs/tests before writing the review."}}
+{"type":"item.started","item":{"id":"item_9","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/tasklist.json | sed -n '/\\\"id\\\": \\\"P7.S6\\\"/,+45p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_9","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/tasklist.json | sed -n '/\\\"id\\\": \\\"P7.S6\\\"/,+45p'\"","aggregated_output":"","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_10","type":"command_execution","command":"/usr/bin/zsh -lc 'find docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice -maxdepth 2 -type f -print'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_10","type":"command_execution","command":"/usr/bin/zsh -lc 'find docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice -maxdepth 2 -type f -print'","aggregated_output":"docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/r1-2026-06-05T0106-primary-request.md\ndocs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/chain.json\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_11","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba skills/subagent-driven-development/SKILL.md | sed -n '35,90p;135,160p;210,240p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_11","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba skills/subagent-driven-development/SKILL.md | sed -n '35,90p;135,160p;210,240p'\"","aggregated_output":"    35\tThe slice's `workflow_step` should be `implement` when execution begins and only advance to `done` after the post-slice review verdict is `ready` / `ready with small edits`. See [[tasklist-discipline]].\n    36\t\n    37\tBefore dispatching any implementation subagent, run `[[using-git-worktrees]]` as the first executable gate and verify the coordinator is operating from an isolated worktree for the active slice. Implementation requires one isolated worktree per active slice unless the human partner explicitly opts out in the current turn. A normal repo checkout on `main`/`master` is read-only/planning-only by default: do not edit files, run artifact-producing tests, write reviewer chains, or mutate tasktool status for an implementation slice there without that explicit opt-out.\n    38\t\n    39\t**Subagents inherit your cwd and must not call `tasktool start`.** The implementer/spec-reviewer/code-quality-reviewer prompt templates already export `SUPERSTAR_SUBAGENT_ROLE` so tasktool refuses subagent-side `start` calls; see `[[tasklist-discipline]]` \"Subagent rule\" for the load-bearing prose rule.\n    40\t\n    41\tBefore dispatching implementation work for a phase, run `tasktool schedule <phase-id>` and `tasktool ready-slices <phase-id>`. Only dispatch slices returned by `ready-slices`; they have no unfinished `depends_on` entries and are not runtime-blocked. Slices sharing a `parallel_group` are candidates for parallel execution when their file scopes do not overlap. If implementation discovers a real sequencing dependency, stop dispatch for the affected slice and update the row with `tasktool deps`; do not encode planned sequencing as `blocked_on`.\n    42\t\n    43\tAfter `tasktool ready-slices <phase-id>`, run `tasktool surface check <phase-id>` before dispatching any slices in parallel. **Do not parallel-dispatch slices that share an integration surface without a declared `depends_on` or a shared `coordination_group`.** A shared write surface — a central registry, a schema/seed file, a renderer dispatch table, a parser union, a theme CSS tail, an ordering array — is what actually governs merge safety; feature independence does not. When `surface check` reports an unguarded `surface_overlap`, either **serialize** the slices (`tasktool deps <later-slice-id> --add <earlier-slice-id>`) or **coordinate** them (`tasktool coordinate <slice-id> --group <name>`, designate one slice as the integration owner, and plan to run the centralized-registry merge playbook at merge). Slices reported as `coordinated` may proceed in parallel; unguarded overlaps must be resolved first.\n    44\t\n    45\tParallel slices must run in separate worktrees. Same repo, different branch, or different TodoWrite entry is not isolation if the filesystem checkout is shared. When two slices are both active, each slice's implementers, reviewer-chain writes, verification artifacts, and tasktool status mutations stay inside that slice's worktree until merge-back.\n    46\t\n    47\t**Two reviews, two scopes — do not conflate them:**\n    48\t\n    49\t| Review | Scope | Reviewer | When | Gate? |\n    50\t|---|---|---|---|---|\n    51\t| Internal (`[[requesting-internal-review]]`) | Per task | In-session subagent (spec compliance, then code quality) | After each task | Gates task close |\n    52\t| External (`[[external-review]]`) | Per slice and per phase | Out-of-loop third-party CLI | At slice and phase boundaries | Gates slice/phase close |\n    53\t\n    54\tThe per-task internal reviews approving every task in a slice **does not** satisfy the slice-boundary external review. They have different scopes (one task vs. the whole slice) and different reviewers. Both are required.\n    55\t\n    56\t- **At the end of each slice** (all the slice's tasks closed, in-loop internal reviews passed):\n    57\t  1. Run `git status --short`. If setup/migration artifacts, unrelated reviewer chains, legacy path moves, unrelated tasklist mutations, files from another slice, or other dirty files outside the slice scope are present, stop and resolve that boundary before review.\n    58\t  2. **Integrate-current-main checkpoint.** Run `tasktool worktree status <slice-id> --integration`. If a sibling slice has landed on the base branch since this slice's `worktree_base_sha` — especially one that shares an integration surface with this slice — integrate the current base branch into the worktree **before** the post-slice review: run `tasktool worktree sync <slice-id> --merge` (or `--rebase`) when that command is available, otherwise merge the base branch with raw git (`git merge <base-branch>`). Resolve any registry / schema / seed / ordering conflicts with the centralized-registry merge playbook (`references/registry-merge-playbook.md`), regenerate derived artifacts (checksums, snapshots), and rerun verification. Only then proceed. Skipping this replays already-integrated churn and produces stale-base merges. If `worktree status --integration` reports `landed: unknown` for a sibling, treat it as possibly-landed and inspect before proceeding.\n    59\t  3. Invoke `[[external-review]]` with `--kind post-slice`, passing the plan as `--file` and the spec + `docs/tasklist.json` as `--context`.\n    60\t  4. Read the verdict. On `ready` / `ready with small edits`, proceed.\n    61\t  5. On `merged_verdict: revise` (or `verdict_valid: false`), **dispatch a fix subagent** with the previous response file as input. The fix subagent MUST write `docs/reviewer/<chain>/r{N}-resolution.md` per the contract in `[[external-review]]` before signaling completion. Wait for completion. Re-submit. Iterate.\n    62\t  6. Once the verdict gates pass, run `tasktool close <slice-id>` (the CLI re-checks the reviewer chain and refuses on `revise`). See `[[tasklist-discipline]]`.\n    63\t\n    64\t- **At the end of the phase** (the last slice in the phase closes):\n    65\t  1. Run the same `git status --short` scope preflight.\n    66\t  2. Invoke `[[external-review]]` with `--kind post-phase`, passing the phase plan or archive note as `--file` and the spec + plan + `docs/tasklist.json` as `--context`.\n    67\t  3. Same delegation rule — coordinator does not apply findings directly.\n    68\t  4. On verdict acceptance, run `tasktool archive-phase <phase-id>` (the CLI re-checks the post-phase chain), then invoke `[[finishing-a-development-branch]]`.\n    69\t\n    70\t## When to Use\n    71\t\n    72\t```dot\n    73\tdigraph when_to_use {\n    74\t    \"Have implementation plan?\" [shape=diamond];\n    75\t    \"Tasks mostly independent?\" [shape=diamond];\n    76\t    \"Stay in this session?\" [shape=diamond];\n    77\t    \"subagent-driven-development\" [shape=box];\n    78\t    \"executing-plans\" [shape=box];\n    79\t    \"Manual execution or brainstorm first\" [shape=box];\n    80\t\n    81\t    \"Have implementation plan?\" -> \"Tasks mostly independent?\" [label=\"yes\"];\n    82\t    \"Have implementation plan?\" -> \"Manual execution or brainstorm first\" [label=\"no\"];\n    83\t    \"Tasks mostly independent?\" -> \"Stay in this session?\" [label=\"yes\"];\n    84\t    \"Tasks mostly independent?\" -> \"Manual execution or brainstorm first\" [label=\"no - tightly coupled\"];\n    85\t    \"Stay in this session?\" -> \"subagent-driven-development\" [label=\"yes\"];\n    86\t    \"Stay in this session?\" -> \"executing-plans\" [label=\"no - parallel session\"];\n    87\t}\n    88\t```\n    89\t\n    90\t**vs. Executing Plans (parallel session):**\n   135\t    \"Answer questions, provide context\" -> \"Dispatch implementer subagent (./implementer-prompt.md)\";\n   136\t    \"Implementer subagent asks questions?\" -> \"Implementer subagent implements, tests, commits, self-reviews\" [label=\"no\"];\n   137\t    \"Implementer subagent implements, tests, commits, self-reviews\" -> \"Dispatch spec reviewer subagent (./spec-reviewer-prompt.md)\";\n   138\t    \"Dispatch spec reviewer subagent (./spec-reviewer-prompt.md)\" -> \"Spec reviewer subagent confirms code matches spec?\";\n   139\t    \"Spec reviewer subagent confirms code matches spec?\" -> \"Implementer subagent fixes spec gaps\" [label=\"no\"];\n   140\t    \"Implementer subagent fixes spec gaps\" -> \"Dispatch spec reviewer subagent (./spec-reviewer-prompt.md)\" [label=\"re-review\"];\n   141\t    \"Spec reviewer subagent confirms code matches spec?\" -> \"Dispatch code quality reviewer subagent (./code-quality-reviewer-prompt.md)\" [label=\"yes\"];\n   142\t    \"Dispatch code quality reviewer subagent (./code-quality-reviewer-prompt.md)\" -> \"Code quality reviewer subagent approves?\";\n   143\t    \"Code quality reviewer subagent approves?\" -> \"Implementer subagent fixes quality issues\" [label=\"no\"];\n   144\t    \"Implementer subagent fixes quality issues\" -> \"Dispatch code quality reviewer subagent (./code-quality-reviewer-prompt.md)\" [label=\"re-review\"];\n   145\t    \"Code quality reviewer subagent approves?\" -> \"Mark task complete in TodoWrite\" [label=\"yes\"];\n   146\t    \"Mark task complete in TodoWrite\" -> \"Last task in slice?\";\n   147\t    \"Last task in slice?\" -> \"More tasks remain?\" [label=\"no\"];\n   148\t    \"Integrate current main (worktree status --integration)\" [shape=box];\n   149\t    \"Last task in slice?\" -> \"Integrate current main (worktree status --integration)\" [label=\"yes\"];\n   150\t    \"Integrate current main (worktree status --integration)\" -> \"Invoke external-review --kind post-slice\";\n   151\t    \"Invoke external-review --kind post-slice\" -> \"post-slice verdict ready?\";\n   152\t    \"post-slice verdict ready?\" -> \"Dispatch fix subagent with reviewer response\" [label=\"revise\"];\n   153\t    \"Dispatch fix subagent with reviewer response\" -> \"Invoke external-review --kind post-slice\" [label=\"re-submit\"];\n   154\t    \"post-slice verdict ready?\" -> \"tasktool close <slice-id>\" [label=\"ready\"];\n   155\t    \"tasktool close <slice-id>\" -> \"Last slice in phase?\";\n   156\t    \"Last slice in phase?\" -> \"More tasks remain?\" [label=\"no\"];\n   157\t    \"Last slice in phase?\" -> \"Invoke external-review --kind post-phase\" [label=\"yes\"];\n   158\t    \"Invoke external-review --kind post-phase\" -> \"post-phase verdict ready?\";\n   159\t    \"post-phase verdict ready?\" -> \"Dispatch fix subagent (post-phase findings)\" [label=\"revise\"];\n   160\t    \"Dispatch fix subagent (post-phase findings)\" -> \"Invoke external-review --kind post-phase\" [label=\"re-submit\"];\n   210\t- `./references/registry-merge-playbook.md` — how to merge centralized-registry / schema / seed / ordering conflicts when a coordinated sibling slice has landed before this slice's post-slice review: preserve **both** semantic additions, regenerate derived artifacts, rerun focused parser/schema/seed tests, then rerun integrated verification.\n   211\t\n   212\t## Example Workflow\n   213\t\n   214\t```\n   215\tYou: I'm using Subagent-Driven Development to execute this plan.\n   216\t\n   217\t[Read plan file once: docs/superstar/plans/feature-plan.md]\n   218\t[Extract all 5 tasks with full text and context]\n   219\t[Create TodoWrite with all tasks]\n   220\t\n   221\tTask 1: Hook installation script\n   222\t\n   223\t[Get Task 1 text and context (already extracted)]\n   224\t[Dispatch implementation subagent with full task text + context]\n   225\t\n   226\tImplementer: \"Before I begin - should the hook be installed at user or system level?\"\n   227\t\n   228\tYou: \"User level (~/.config/superstar/hooks/)\"\n   229\t\n   230\tImplementer: \"Got it. Implementing now...\"\n   231\t[Later] Implementer:\n   232\t  - Implemented install-hook command\n   233\t  - Added tests, 5/5 passing\n   234\t  - Self-review: Found I missed --force flag, added it\n   235\t  - Committed\n   236\t\n   237\t[Dispatch spec compliance reviewer]\n   238\tSpec reviewer: ✅ Spec compliant - all requirements met, nothing extra\n   239\t\n   240\t[Get git SHAs, dispatch code quality reviewer]\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_12","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py | sed -n '150,245p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_12","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py | sed -n '150,245p'\"","aggregated_output":"   150\t    end = live.index(end_tag) + len(end_tag)\n   151\t    span = live[start:end]\n   152\t\n   153\t    fixture = (Path(__file__).resolve().parent / \"fixtures\"\n   154\t               / \"p5_s3_subagent_load.txt\").read_text()\n   155\t    assert span == fixture, (\n   156\t        \"subagent early-exit span drifted from the P5.S3 transcript fixture. \"\n   157\t        \"Update tools/tasktool/tests/fixtures/p5_s3_subagent_load.txt in the \"\n   158\t        \"same commit and explain the behavior change in the commit message.\"\n   159\t    )\n   160\t\n   161\t    assert len(span) < len(live), \"early-exit span must be a proper subset\"\n   162\t    assert \"tasktool start\" in span and (\n   163\t        \"do not call\" in span.lower() or \"do not\" in span.lower()\n   164\t    ), \"early-exit block must forbid `tasktool start` from a subagent\"\n   165\t\n   166\t\n   167\tdef test_registry_merge_playbook_exists() -> None:\n   168\t    playbook = (\n   169\t        ROOT\n   170\t        / \"skills\"\n   171\t        / \"subagent-driven-development\"\n   172\t        / \"references\"\n   173\t        / \"registry-merge-playbook.md\"\n   174\t    )\n   175\t    assert playbook.is_file(), f\"registry merge playbook must exist at {playbook}\"\n   176\t    body = playbook.read_text(encoding=\"utf-8\")\n   177\t    # The playbook's load-bearing instructions.\n   178\t    assert \"preserve both\" in body.lower()\n   179\t    assert \"regenerate\" in body.lower()\n   180\t    assert \"rerun\" in body.lower()\n   181\t\n   182\t\n   183\tdef test_subagent_driven_development_runs_surface_check_before_parallel_dispatch() -> None:\n   184\t    text = skill_text(\"subagent-driven-development\")\n   185\t    assert \"tasktool surface check <phase-id>\" in text\n   186\t    assert \"Do not parallel-dispatch slices that share an integration surface\" in text\n   187\t    # surface check is described alongside ready-slices, before dispatch\n   188\t    rs = text.index(\"tasktool ready-slices <phase-id>\")\n   189\t    sc = text.index(\"tasktool surface check <phase-id>\")\n   190\t    assert rs < sc, \"surface check must be documented after ready-slices\"\n   191\t\n   192\t\n   193\tdef test_subagent_driven_development_has_integrate_main_checkpoint() -> None:\n   194\t    text = skill_text(\"subagent-driven-development\")\n   195\t    assert \"tasktool worktree status <slice-id> --integration\" in text\n   196\t    assert \"Integrate-current-main checkpoint\" in text\n   197\t    assert \"references/registry-merge-playbook.md\" in text\n   198\t    # the checkpoint precedes the close gate in the slice-end sequence\n   199\t    integ = text.index(\"tasktool worktree status <slice-id> --integration\")\n   200\t    close = text.index(\"tasktool close <slice-id>\")\n   201\t    assert integ < close, \"integrate-main checkpoint must precede the close gate\"\n   202\t\n   203\t\n   204\tdef test_tasklist_discipline_documents_surface_reserve_coordinate() -> None:\n   205\t    text = skill_text(\"tasklist-discipline\")\n   206\t    # daily-commands surface\n   207\t    assert \"tasktool surface add <slice-id>\" in text\n   208\t    assert \"tasktool surface check <phase-id>\" in text\n   209\t    assert \"tasktool reserve add <slice-id>\" in text\n   210\t    assert \"tasktool coordinate <slice-id> --group\" in text\n   211\t    # conceptual model + vocabulary\n   212\t    assert \"integration_surfaces\" in text\n   213\t    assert \"reservations\" in text\n   214\t    assert \"cms-block-registry\" in text\n   215\t    # coordination_group vs parallel_group distinction is spelled out\n   216\t    assert \"coordination_group\" in text\n   217\t    assert \"parallel_group\" in text\n   218\t    # the three new red-flag claims\n   219\t    assert \"feature independence\" in text\n   220\t    assert \"duplicate\" in text.lower()\n   221\t\n   222\t\n   223\tdef test_phase_planning_and_writing_plans_document_surface_tables() -> None:\n   224\t    for skill in [\"phase-planning\", \"writing-plans\"]:\n   225\t        text = skill_text(skill)\n   226\t        assert \"surface/reservation table\" in text, (\n   227\t            f\"{skill} must require a surface/reservation table\"\n   228\t        )\n   229\t        assert \"tasktool surface check <phase-id>\" in text, (\n   230\t            f\"{skill} must tell the author to run surface check before ratifying\"\n   231\t        )\n","exit_code":0,"status":"completed"}}
+{"type":"item.completed","item":{"id":"item_13","type":"agent_message","text":"The added doc assertions and the subagent skill edits are present. The live tracker lookup via `tasktool show` remains the main lifecycle concern, and I’m checking the JSON location plus the actual verification commands now."}}
+{"type":"item.started","item":{"id":"item_14","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba skills/tasklist-discipline/SKILL.md | sed -n '45,90p;185,210p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_14","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba skills/tasklist-discipline/SKILL.md | sed -n '45,90p;185,210p'\"","aggregated_output":"    45\tCommands run against an archived X-id report a may-already-be-archived hint because archive files are evidence, not part of the active tasklist workflow surface.\n    46\t\n    47\tStatus enum: `ready | in_progress | blocked | done | cancelled`. Only slices may take `blocked`. `cancelled` is a terminal status (peer of `done`) recording work that was intentionally not shipped — cancelled, deferred, abandoned, superseded. It is set only via `tasktool cancel <id> --reason \"…\"`; the `set` verb does not accept it. Tasks cannot be `cancelled`; cancel the parent slice instead.\n    48\t\n    49\t`blocked` is only set via `tasktool block <slice-id> --on …`. Emoji are a render concern; `tasktool render` and `tasktool brief` handle that. `tasktool start <slice-id>` is the normal way to enter `in_progress`; `tasktool set <id> --status in_progress` is a compatibility alias for older plans and ad-hoc rows. `tasktool unblock <slice-id> --resume` resumes through the same lifecycle path and stamps `started` when needed. `done` requires `closed`; the CLI stamps it.\n    50\t\n    51\tPhase planning uses separate scheduling metadata. `planning_path` points at the phase-scoped planning/design document. `depends_on` records planned slice sequencing; it is not the same as runtime `blocked_on`. `planning_status` is `proposed | ratified | superseded`, and `parallel_group` names slices intended to be planned or executed together.\n    52\t\n    53\tIntegration-surface metadata models **parallel-execution safety by write surface**, not by feature intent. `integration_surfaces` is a list of conventional tags naming the shared write areas a slice mutates (recommended vocabulary: `cms-block-registry`, `directus-schema`, `page-renderer-dispatch`, `theme-tail-css`, `content-contract-types`, `reviewer-artifacts` — extend per project). `reservations` are scarce-allocation claims on a single value (`homepage-sort:15`, `route-slug:/offers`, `block-kind:slider`), each scoped `phase` (default) or `project`; `tasktool reserve add` **refuses a duplicate allocation** within scope. `coordination_group` names a set of slices that *intentionally* share a surface and agree to coordinate — serialize reviews, designate an integration owner, run the centralized-registry merge playbook. It is the opposite of `parallel_group`, which asserts the slices are independent: a shared surface needs a `coordination_group` or a `depends_on`, never a `parallel_group`.\n    54\t\n    55\t## Daily commands\n    56\t\n    57\t```sh\n    58\ttasktool brief <id>            # start-of-work primer for slice or phase\n    59\ttasktool show <id>             # full detail\n    60\ttasktool list --open           # everything ready / in_progress / blocked\n    61\ttasktool create slice <phase-id> --title \"...\"\n    62\ttasktool prepare existing <id> --plan path/to/plan.md\n    63\ttasktool artifact add <id> --kind spec --path path/to/spec.md\n    64\ttasktool artifact status <id> --strict\n    65\ttasktool artifact commit <id> --message \"...\"\n    66\ttasktool start <slice-id>      # lifecycle start + in_progress\n    67\ttasktool set <id> --status in_progress  # compatibility alias\n    68\ttasktool note <id> --append \"...\"\n    69\ttasktool ref <id> --add path/to/artifact\n    70\ttasktool block <slice-id> --on P2.S5\n    71\ttasktool deps <slice-id> --add P2.S1\n    72\ttasktool ratify <slice-id> --parallel-group bootstrap\n    73\ttasktool surface add <slice-id> <surface> [<surface>...]   # declare shared write surfaces\n    74\ttasktool surface remove <slice-id> <surface>\n    75\ttasktool surface list [<phase-id>]\n    76\ttasktool surface check <phase-id>            # unguarded overlaps + coordinated surfaces + reservation contention\n    77\ttasktool reserve add <slice-id> <resource>:<value> [--scope phase|project] [--note \"...\"] [--force --reason \"...\"]\n    78\ttasktool reserve remove <slice-id> <resource>:<value>\n    79\ttasktool reserve list [<phase-id>]\n    80\ttasktool coordinate <slice-id> --group <name>   # mark intentional shared-surface coordination\n    81\ttasktool coordinate <slice-id> --clear\n    82\ttasktool schedule <phase-id>\n    83\ttasktool ready-slices <phase-id>\n    84\ttasktool phase-status\n    85\ttasktool close <slice-id>      # enforces post-slice review gate\n    86\ttasktool close <x-id>          # closes and archives cross-cutting by default\n    87\ttasktool close <x-id> --no-archive\n    88\ttasktool cancel <id> --reason \"<text>\"           # terminate without shipping\n    89\ttasktool cancel <phase-id> --reason \"...\" --cascade  # cancel a phase + its open slices\n    90\ttasktool cancel <x-id> --reason \"...\" --no-archive   # keep cancelled X visible\n   185\t|---------|---------|\n   186\t| \"I'll just edit `docs/tasklist.json` by hand quickly.\" | The hook will refuse non-canonical bytes; `tasktool` is faster than fighting the hook. Use the CLI. |\n   187\t| \"I'll mark the slice `done` with `set` instead of `close` to skip the review gate.\" | `tasktool set --status done` routes through the same gate as `close`. The gate cannot be bypassed by reaching for a different subcommand. |\n   188\t| \"I'll mark this slice `done` to make it disappear.\" | Use `cancel`, not `close`. `done` is a lie if the work never shipped — and `close` runs the post-slice review gate, which is meaningless on cancelled work. |\n   189\t| \"I'll commit the spec now and add the row after.\" | The pre-commit hook rejects orphan spec/plan filenames. Allocate first. |\n   190\t| \"`tasktool` says the verdict isn't ready, but the reviewer comments look fine.\" | Re-read the verdict line. `revise` is `revise`. If the reviewer chain is mis-parsed, fix the chain; do not pass `--skip-review-gate` casually. |\n   191\t| \"I'll bring back `docs/TASKLIST.md` for readability.\" | The hook refuses commits that touch it. Use `tasktool render` if you want markdown. |\n   192\t| \"I'll just renumber IDs to match execution order.\" | No. IDs are stable. Execution order lives in the array order; IDs preserve creation order. |\n   193\t| \"Setup files are just scaffolding; I'll leave them dirty while implementing.\" | No. Setup/migration artifacts make post-slice review scope ambiguous. Resolve the setup boundary first. |\n   194\t| \"I created a follow-up slice/X-item, so I can knock it out in this worktree.\" | No. Allocation is not implementation permission. Follow-up work gets deferred or gets its own isolated worktree. |\n   195\t| \"I only need to add refs or flip the row before creating the worktree.\" | No. For an active implementation slice, tasktool refs/status/notes are part of the slice artifact set. Isolate first. |\n   196\t| \"The slice is currently blocked, so I'll add `blocked_on` to model the phase plan.\" | No. Use `depends_on` for planned sequencing. Use `blocked_on` only for active runtime blockers. |\n   197\t| \"These slices are feature-independent, so they're parallel-safe.\" | Parallel safety is about **write surface**, not feature independence. Declare `integration_surfaces` and run `tasktool surface check <phase-id>` before dispatching them together. |\n   198\t| \"I'll pick a sort slot / collection name / route slug freely.\" | **Reserve** it (`tasktool reserve add`) so siblings cannot collide; for project-global resources use `--scope project`. The tool refuses a duplicate allocation. |\n   199\t| \"We both need the CMS registry, so I'll just `parallel_group` them.\" | A shared surface needs a `coordination_group` (coordinate) or a `depends_on` (serialize), not a `parallel_group` — which asserts independence the slices do not have. |\n   200\t\n   201\t## Integration\n   202\t\n   203\t- `[[writing-plans]]` — embeds slice IDs in plan filenames; calls `tasktool show <id>` for context.\n   204\t- `[[brainstorming]]` — allocates IDs via `tasktool create` before writing the spec.\n   205\t- `[[external-review]]` — passes `docs/tasklist.json` (or `tasktool render` output) as `--context`.\n   206\t- `[[subagent-driven-development]]` — calls `tasktool close <slice-id>` at slice end and `tasktool archive-phase` at phase end.\n   207\t- `[[project-setup]]` — runs `tasktool init` and `install.sh --hook`.\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_15","type":"command_execution","command":"/usr/bin/zsh -lc \"rg -n 'P7\\\\.S6|Skill changes: subagent' docs/tasklist.json\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_15","type":"command_execution","command":"/usr/bin/zsh -lc \"rg -n 'P7\\\\.S6|Skill changes: subagent' docs/tasklist.json\"","aggregated_output":"417:          \"title\": \"Skill changes: subagent-driven-development checkpoint + registry-merge-playbook; tasklist-discipline; phase-planning/writing-plans tables\",\n426:            \"P7.S6\"\n446:          \"notes\": \"Spec §4.H. Surfaces: external-review. INVESTIGATION-FIRST: reproduce reported add/add reviewer-artifact collision vs CURRENT bridge (already work_id-scopes chains + round/role-unique request files). Fix only if reproduced; else document + drop. No deps.\\nCancelled 2026-06-02T23:23:25: investigation: reviewer-artifact add/add collision does not reproduce against the current bridge (work-id-keyed chain folders, round/role-unique basenames, mandatory --work-id with mismatch refusal); residual docs/tasklist.json close-churn is owned by P7.S6 integrate-current-main, not by reviewer-artifact naming. See docs/notes/2026-06-02-P7-S8-reviewer-artifact-investigation-decision.md\",\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_16","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba skills/writing-plans/SKILL.md | sed -n '18,42p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_16","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba skills/writing-plans/SKILL.md | sed -n '18,42p'\"","aggregated_output":"    18\t**Save plans to:** `docs/plans/YYYY-MM-DD-<id>-<slug>.md` where `<id>` is the tasktool ID for the work (e.g. `p2-s3a`). If the project has no `docs/tasklist.json`, omit the ID segment. User preferences for plan location override this default.\n    19\t\n    20\t**tasktool integration:** If `docs/tasklist.json` exists, this plan must correspond to a row in it. See [[tasklist-discipline]] for the ID scheme. **Before writing the plan file, verify the row for `<id>` exists** — run `tasktool show <id>` and confirm exit 0. If it doesn't (e.g. a spec was committed without a row, though the pre-commit hook should have caught that), stop and create the row via `tasktool create …` per [[tasklist-discipline]]. Never let the plan be the artifact that mints an ID.\n    21\t\n    22\t**Artifact transaction:** Before writing the plan and handoff, register future paths with `tasktool prepare existing <id> --plan <plan-path> --handoff <handoff-path>`. After writing each file, run `tasktool artifact add <id> --kind plan --path <plan-path>` and `tasktool artifact add <id> --kind handoff --path <handoff-path>`. After plan review passes, register the reviewer chain, run `tasktool artifact status <id> --strict`, and use `tasktool artifact commit <id> --message \"<id>: add <slug> plan\"` unless the user explicitly asked not to commit.\n    23\t\n    24\t**Lifecycle start step:** When docs/tasklist.json exists and the plan executes a slice, the first execution step must be `tasktool start <slice-id>` before dispatching or editing implementation files. Use the concrete slice ID in generated plans, not the placeholder. This is separate from TodoWrite and from prose status updates.\n    25\t\n    26\t**Scheduling ratification:** For slice plans, inspect `tasktool show <slice-id>` and `tasktool schedule <phase-id>` before drafting. The plan must explicitly confirm or update `depends_on`, `parallel_group`, and whether the slice remains independently plannable/executable. If the spec/plan work discovers a dependency change, update it with `tasktool deps`; when the plan settles, run `tasktool ratify <slice-id>` so coordinators can rely on `tasktool ready-slices <phase-id>`.\n    27\t\n    28\t**Integration surfaces & reservations:** A slice plan that may run in parallel with siblings must include a **surface/reservation table** — for this slice (and any sibling it could overlap), list `integration_surfaces`, `reservations` (`resource:value` + scope), and `coordination_group`. Declare them on the tracker with `tasktool surface add` / `tasktool reserve add` / `tasktool coordinate`, then run `tasktool surface check <phase-id>` before ratifying. Do not place slices that share a surface in the same `parallel_group` without a `depends_on` (serialize) or a `coordination_group` (coordinate). A duplicate scarce-resource allocation is refused at declaration time — pick a free value rather than `--force`, unless you genuinely intend a coordinated shared allocation and record the reason.\n    29\t\n    30\t## Scope Check\n    31\t\n    32\tIf the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.\n    33\t\n    34\t## File Structure\n    35\t\n    36\tBefore defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.\n    37\t\n    38\t- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.\n    39\t- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.\n    40\t- Files that change together should live together. Split by responsibility, not by technical layer.\n    41\t- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.\n    42\t\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_17","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba skills/phase-planning/SKILL.md | sed -n '25,80p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_17","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba skills/phase-planning/SKILL.md | sed -n '25,80p'\"","aggregated_output":"    25\t\n    26\t### Phase Shaping\n    27\t\n    28\tUse when the human partner has conceptually agreed a phase.\n    29\t\n    30\t1. Create or confirm a phase row via `tasktool create phase`.\n    31\t2. Write one phase-scoped planning document. Prefer `docs/specs/YYYY-MM-DD-<phase-id>-<slug>-design.md` for bootstrap compatibility, then set `planning_path` with `tasktool planning-path <phase-id> --set <path>`.\n    32\t3. Register prospective slices with `tasktool create slice <phase-id> --title ...`.\n    33\t4. Record planned dependencies with `tasktool deps <slice-id> --add <dependency-slice-id>`.\n    34\t5. Record intended planning/execution lanes with `tasktool ratify <slice-id> --status proposed --parallel-group <group>`.\n    35\t6. Declare each slice's write surfaces and scarce reservations: `tasktool surface add <slice-id> <surface>...` and `tasktool reserve add <slice-id> <resource>:<value> [--scope phase|project]`. **Before ratifying any `parallel_group`, run `tasktool surface check <phase-id>`** and resolve every unguarded surface overlap — add a `depends_on` to serialize, or a `coordination_group` to coordinate. A `parallel_group` must not contain slices that share an integration surface without one of those links.\n    36\t7. Run `tasktool schedule <phase-id>` and include the output or a concise summary in the phase planning document.\n    37\t\n    38\tThe document must include:\n    39\t- phase objectives and closeout goals;\n    40\t- prospective slices and acceptance intent;\n    41\t- dependency assumptions and likely blockers;\n    42\t- parallel planning/execution opportunities;\n    43\t- explicit notes on which dependencies must be ratified by slice spec/plan writers.\n    44\t- a **surface/reservation table**: one row per prospective slice listing its `integration_surfaces`, `reservations` (`resource:value` + scope), and `coordination_group`.\n    45\t\n    46\t## Worktree And Hook Hygiene\n    47\t\n    48\t`docs/tasklist.json` is canonical and the pre-commit hook rejects orphan dated spec/plan filenames. If a planning document pollutes the worktree before tasktool can reference it:\n    49\t\n    50\t- If it has a phase ID, register that ID first and attach the file as `spec_path` or `planning_path`.\n    51\t- If it has no registered ID, keep it outside orphan-checked paths such as `docs/_drafts/`.\n    52\t- Do not stage unregistered dated files under `docs/specs/` or `docs/plans/`.\n    53\t- Do not close a slice or phase while unrelated dirty files make review scope ambiguous.\n    54\t\n    55\t## Ratification Contract\n    56\t\n    57\tPhase shaping records best-known scheduling. Slice spec and plan writers must ratify it later:\n    58\t\n    59\t- If the slice remains independent, run `tasktool ratify <slice-id>`.\n    60\t- If it depends on another slice, update `depends_on` with `tasktool deps` before plan review.\n    61\t- If it is superseded, run `tasktool ratify <slice-id> --status superseded` and explain the replacement in the phase planning document or slice notes.\n    62\t\n    63\t## Red Flags\n    64\t\n    65\t| Thought | Reality |\n    66\t|---------|---------|\n    67\t| \"I'll just put dependency notes in the phase doc.\" | Tools cannot schedule prose. Put durable dependencies in `depends_on`. |\n    68\t| \"This slice is not ready yet, so mark it blocked.\" | Planned sequencing is `depends_on`; runtime interruption is `blocked_on`. |\n    69\t| \"The phase plan can live as an untracked draft in `docs/specs/`.\" | Dated spec/plan filenames are hook-checked. Register the ID or keep drafts elsewhere. |\n    70\t| \"The first sketch is final.\" | Phase shaping is provisional. Slice plans ratify or update the graph. |\n    71\t| \"These slices are in different features, so I'll `parallel_group` them.\" | Parallel groups are about shared **write surface**, not feature boundaries. Declare `integration_surfaces` and run `tasktool surface check <phase-id>` before ratifying a parallel group. |\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_18","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/tasklist.json | sed -n '400,435p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_18","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/tasklist.json | sed -n '400,435p'\"","aggregated_output":"   400\t            \"P7.S3\",\n   401\t            \"P7.S4\"\n   402\t          ],\n   403\t          \"id\": \"S6\",\n   404\t          \"notes\": \"Spec §4.F. Surfaces: skills. subagent-driven-development: surface check before parallel dispatch + integrate-current-main checkpoint before post-slice review + references/registry-merge-playbook.md. tasklist-discipline command docs + red flags. phase-planning/writing-plans surface/reservation tables.\",\n   405\t          \"parallel_group\": null,\n   406\t          \"plan_path\": \"docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md\",\n   407\t          \"planning_status\": \"ratified\",\n   408\t          \"refs\": [\n   409\t            \"docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md\",\n   410\t            \"docs/handoffs/2026-06-04-P7-S6-skill-integration-surface-docs-prompt.md\",\n   411\t            \"docs/reviewer/p7-s6-skill-integration-surface-docs-plan\"\n   412\t          ],\n   413\t          \"reviewer_chain\": \"docs/reviewer/p7-s6-skill-integration-surface-docs-plan\",\n   414\t          \"started\": null,\n   415\t          \"status\": \"ready\",\n   416\t          \"tasks\": [],\n   417\t          \"title\": \"Skill changes: subagent-driven-development checkpoint + registry-merge-playbook; tasklist-discipline; phase-planning/writing-plans tables\",\n   418\t          \"workflow_step\": \"implement\"\n   419\t        },\n   420\t        {\n   421\t          \"blocked_on\": null,\n   422\t          \"closed\": null,\n   423\t          \"created\": \"2026-06-02\",\n   424\t          \"depends_on\": [\n   425\t            \"P7.S1\",\n   426\t            \"P7.S6\"\n   427\t          ],\n   428\t          \"id\": \"S7\",\n   429\t          \"notes\": \"Spec §4.G. Surfaces: validate. tasktool validate / artifact-status check that declared surfaces/reservations are reflected in plan table; min bar = warn when a parallel_group slice declares no surfaces.\",\n   430\t          \"parallel_group\": null,\n   431\t          \"plan_path\": null,\n   432\t          \"planning_status\": \"proposed\",\n   433\t          \"refs\": [],\n   434\t          \"reviewer_chain\": null,\n   435\t          \"started\": null,\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_19","type":"command_execution","command":"/usr/bin/zsh -lc 'cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -q'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.started","item":{"id":"item_20","type":"command_execution","command":"/usr/bin/zsh -lc \"for cmd in 'tasktool surface check --help' 'tasktool reserve add --help' 'tasktool coordinate --help' 'tasktool worktree status --help' 'tasktool worktree sync --help'; do \"'$cmd >/tmp/help.out 2>/tmp/help.err; rc=$?; printf '\"'%s -> %s\\\\n' \\\"\"'$cmd\" \"$rc\"; if [ $rc -ne 0 ]; then sed -n '\"'1,4p' /tmp/help.err; fi; done\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_20","type":"command_execution","command":"/usr/bin/zsh -lc \"for cmd in 'tasktool surface check --help' 'tasktool reserve add --help' 'tasktool coordinate --help' 'tasktool worktree status --help' 'tasktool worktree sync --help'; do \"'$cmd >/tmp/help.out 2>/tmp/help.err; rc=$?; printf '\"'%s -> %s\\\\n' \\\"\"'$cmd\" \"$rc\"; if [ $rc -ne 0 ]; then sed -n '\"'1,4p' /tmp/help.err; fi; done\"","aggregated_output":"tasktool surface check --help -> 127\nzsh:1: command not found: tasktool surface check --help\ntasktool reserve add --help -> 127\nzsh:1: command not found: tasktool reserve add --help\ntasktool coordinate --help -> 127\nzsh:1: command not found: tasktool coordinate --help\ntasktool worktree status --help -> 127\nzsh:1: command not found: tasktool worktree status --help\ntasktool worktree sync --help -> 127\nzsh:1: command not found: tasktool worktree sync --help\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_21","type":"command_execution","command":"/usr/bin/zsh -lc 'cd tools/tasktool && python -m pytest -q'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_19","type":"command_execution","command":"/usr/bin/zsh -lc 'cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -q'","aggregated_output":".................                                                        [100%]\n=============================== warnings summary ===============================\n../../../../../../../../../../usr/lib/python3.14/site-packages/_pytest/cacheprovider.py:475\n  /usr/lib/python3.14/site-packages/_pytest/cacheprovider.py:475: PytestCacheWarning: cache could not write path /home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven/.pytest_cache/v/cache/nodeids: [Errno 30] Read-only file system: '/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven/.pytest_cache/v/cache/nodeids'\n    config.cache.set(\"cache/nodeids\", sorted(self.cached_nodeids))\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n17 passed, 1 warning in 0.03s\n","exit_code":0,"status":"completed"}}
+{"type":"item.completed","item":{"id":"item_22","type":"agent_message","text":"The docs-lifecycle test file passes locally. My first help-command sanity check was malformed because it tried to execute the whole quoted string as a binary, so I’m rerunning that correctly while the full tasktool suite continues."}}
+{"type":"item.started","item":{"id":"item_23","type":"command_execution","command":"/usr/bin/zsh -lc \"tasktool surface check --help >/tmp/surface_check_help.out && echo 'surface check ok'; tasktool reserve add --help >/tmp/reserve_add_help.out && echo 'reserve add ok'; tasktool coordinate --help >/tmp/coordinate_help.out && echo 'coordinate ok'; tasktool worktree status --help >/tmp/worktree_status_help.out && echo 'worktree status ok'; tasktool worktree sync --help >/tmp/worktree_sync_help.out && echo 'worktree sync ok'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_23","type":"command_execution","command":"/usr/bin/zsh -lc \"tasktool surface check --help >/tmp/surface_check_help.out && echo 'surface check ok'; tasktool reserve add --help >/tmp/reserve_add_help.out && echo 'reserve add ok'; tasktool coordinate --help >/tmp/coordinate_help.out && echo 'coordinate ok'; tasktool worktree status --help >/tmp/worktree_status_help.out && echo 'worktree status ok'; tasktool worktree sync --help >/tmp/worktree_sync_help.out && echo 'worktree sync ok'\"","aggregated_output":"surface check ok\nreserve add ok\ncoordinate ok\nworktree status ok\nusage: tasktool worktree [-h]\n                         {list,status,adopt,ensure-gitignore,check-legacy,prune,repair} ...\ntasktool worktree: error: argument wt_cmd: invalid choice: 'sync' (choose from 'list', 'status', 'adopt', 'ensure-gitignore', 'check-legacy', 'prune', 'repair')\n","exit_code":2,"status":"failed"}}
+{"type":"item.completed","item":{"id":"item_24","type":"agent_message","text":"The shipped CLI help exists for `surface check`, `reserve add`, `coordinate`, and `worktree status`. `worktree sync` is not available in this checkout, which matches the plan’s “when available” wording and fallback requirement rather than a failure by itself."}}
+{"type":"item.completed","item":{"id":"item_25","type":"agent_message","text":"The full tasktool suite is still running and is past 90%; I’m waiting for the final result so the verification section reflects actual output, not assumptions."}}
+{"type":"item.completed","item":{"id":"item_21","type":"command_execution","command":"/usr/bin/zsh -lc 'cd tools/tasktool && python -m pytest -q'","aggregated_output":"........................................................................ [  9%]\n........................................................................ [ 18%]\n........................................................................ [ 27%]\n........................................................................ [ 36%]\n........................................................................ [ 46%]\n........................................................................ [ 55%]\n........................................................................ [ 64%]\n........................................................................ [ 73%]\n........................................................................ [ 83%]\n........................................................................ [ 92%]\n...........................................................              [100%]\n=============================== warnings summary ===============================\n../../../../../../../../../../usr/lib/python3.14/site-packages/_pytest/cacheprovider.py:475\n  /usr/lib/python3.14/site-packages/_pytest/cacheprovider.py:475: PytestCacheWarning: cache could not write path /home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven/.pytest_cache/v/cache/nodeids: [Errno 30] Read-only file system: '/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven/.pytest_cache/v/cache/nodeids'\n    config.cache.set(\"cache/nodeids\", sorted(self.cached_nodeids))\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n779 passed, 1 warning in 114.73s (0:01:54)\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_26","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md | sed -n '44,65p;460,489p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.started","item":{"id":"item_27","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md | sed -n '300,360p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_26","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md | sed -n '44,65p;460,489p'\"","aggregated_output":"    44\t## Task 0: Start the slice\n    45\t\n    46\t**Files:**\n    47\t- No source changes; lifecycle only.\n    48\t\n    49\tThis is the mandatory first execution step from `[[writing-plans]]`: record the slice lifecycle start (and the worktree base SHA) before editing any files. The row is already `ratified` from the planning session — Task 0 only moves it to `in_progress`.\n    50\t\n    51\t- [ ] **Step 1: Verify you are in the slice's isolated worktree**\n    52\t\n    53\tRun: `git status --short`\n    54\tExpected: a clean tree (no unrelated dirty files). If this is a shared `main`/`master` checkout and the human partner has not opted out of isolation, stop and create the slice worktree via `[[using-git-worktrees]]` first.\n    55\t\n    56\t- [ ] **Step 2: Start the slice**\n    57\t\n    58\tRun: `tasktool start P7.S6`\n    59\tExpected: the row moves to `in_progress` and the worktree base SHA is recorded.\n    60\t\n    61\t- [ ] **Step 3: Confirm the lifecycle state**\n    62\t\n    63\tRun: `tasktool show P7.S6`\n    64\tExpected: `status: in_progress`, `planning_status: ratified`, `depends_on: P7.S2, P7.S3, P7.S4`.\n    65\t\n   460\t## Task 5: Full-suite verification\n   461\t\n   462\t**Files:**\n   463\t- No source changes; verification only. (The slice was ratified at plan-settle; execution does not re-ratify or mutate the tracker here.)\n   464\t\n   465\t- [ ] **Step 1: Run the full docs-lifecycle test file**\n   466\t\n   467\tRun: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -q`\n   468\tExpected: PASS — all pre-existing tests plus the 5 new functions (Task 1–4) green.\n   469\t\n   470\t- [ ] **Step 2: Run the full tasktool test suite**\n   471\t\n   472\tRun: `cd tools/tasktool && python -m pytest -q`\n   473\tExpected: PASS — no regressions. (This slice changes no Python; the only new tests are the doc-content assertions above.)\n   474\t\n   475\t- [ ] **Step 3: Sanity-check the referenced commands exist**\n   476\t\n   477\tRun:\n   478\t```bash\n   479\ttasktool surface check --help\n   480\ttasktool reserve add --help\n   481\ttasktool coordinate --help\n   482\ttasktool worktree status --help\n   483\t```\n   484\tExpected: each prints usage (no `invalid choice`), confirming the prose references real CLI surface shipped by P7.S2–S4.\n   485\t\n   486\t- [ ] **Step 4: Confirm the scheduling contract is intact (read-only)**\n   487\t\n   488\tRun: `tasktool show P7.S6`\n   489\tExpected: `planning_status: ratified` (set at plan-settle), `depends_on: P7.S2, P7.S3, P7.S4`, no parallel group. This step is read-only — do **not** mutate or commit the tracker from the implementation worktree here; the ratification and its commit already happened in the planning session.\n","exit_code":0,"status":"completed"}}
+{"type":"item.completed","item":{"id":"item_27","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md | sed -n '300,360p'\"","aggregated_output":"   300\t  each slice's integration surfaces and reservations and emit a **surface/\n   301\t  reservation table** in the plan; run `tasktool surface check <phase-id>` before\n   302\t  ratifying parallel groups.\n   303\t\n   304\t### 4.G Plan ↔ tracker drift enforcement (`validate.py`, skills) — partial defer OK\n   305\t\n   306\t- Plans (and phase-planning docs) include a structured **surface/reservation\n   307\t  table** per slice (enforced by the skills in §4.F).\n   308\t- `tasktool validate` (or `artifact status --strict`) gains a check that declared\n   309\t  `integration_surfaces`/`reservations` on a slice are reflected in its plan's\n   310\t  table, flagging drift. Where parsing the plan table is too brittle for this\n   311\t  phase, the minimum bar is a `validate` warning when a slice in a `parallel_group`\n   312\t  declares **no** surfaces at all (the \"you forgot to think about this\" nudge).\n   313\t\n   314\t### 4.H Merge-safe reviewer artifacts (`external-review`) — investigate-first, deferral candidate\n   315\t\n   316\tThe P20 report cited reviewer-request files as add/add-conflicting. **Current\n   317\t`external-reviewer` already mitigates the obvious cause**: post-slice/post-phase\n   318\tchain folders are keyed by `work_id`\n   319\t(`skills/external-review/scripts/external-reviewer.py:727`), request files are\n   320\tround/role-unique (`…:1403`), and `--work-id` is required for post-slice/post-phase\n   321\t(`…:2439`). So the spec does **not** assume a current bug.\n   322\t\n   323\tS8 is therefore an **investigation slice, not a fix slice**: reproduce the reported\n   324\tcollision against *current* `external-reviewer` (the P20 conflict may have come from\n   325\tan older bridge, from `docs/tasklist.json` close churn rather than request files, or\n   326\tfrom a phase-level shared path). Decide one of:\n   327\t\n   328\t- **Reproduces** → fix with per-slice/round-unique paths or an append/merge-safe\n   329\t  format, with the reproduced scenario as the regression test.\n   330\t- **Does not reproduce** → document why in the phase archive note and **drop S8**;\n   331\t  the residual `docs/tasklist.json` close-churn conflict is already addressed by the\n   332\t  integrate-current-main checkpoint (§4.F), not by reviewer-artifact naming.\n   333\t\n   334\tS8 carries no behavioural commitment beyond the investigation until the collision is\n   335\tgrounded.\n   336\t\n   337\t### 4.I Deferred / future (recorded, not built)\n   338\t\n   339\t- `tasktool surface audit <slice-id>` — compares the slice branch diff to\n   340\t  configurable path globs and warns on **undeclared** surfaces (\"you touched\n   341\t  `infra/directus/**` but did not declare `directus-schema`\"). Warning-only safety\n   342\t  net; complements but does not replace explicit declaration.\n   343\t- A `reservation.touches_existing` distinction for maintenance edits to shared\n   344\t  resources.\n   345\t- Cross-project (multi-repo) reservation registries.\n   346\t\n   347\t## 5. Recommended slice decomposition\n   348\t\n   349\tThe implementation plan (writing-plans) will detail tasks; this is the proposed\n   350\tshape, dependencies, and parallel/coordination assumptions.\n   351\t\n   352\t| Slice | Scope | depends_on | Surfaces (this phase) |\n   353\t|-------|-------|-----------|------------------------|\n   354\t| `S1` | Data model + migration (schema v3): surfaces, reservations{resource,value,scope,note}, coordination_group, worktree_base_sha, landed_base_sha, project reservations_ledger (LedgerReservation) | — | `model`, `serialize`, `migrate` |\n   355\t| `S2` | `surface` / `reserve` / `coordinate` CLI; reservation allocation refusal (phase + project scope) + `--force --reason`; ledger population on archive | `S1` | `cli`, `commands` |\n   356\t| `S3` | Scheduling overlap detection: `ready-slices`/`schedule` warnings, `surface check`, `ratify` warning, coordination-group suppression | `S1`, `S2` | `commands` |\n   357\t| `S4` | `worktree start` base-sha recording + `worktree prune` landed-sha stamping + `worktree status --integration` | `S1` | `commands`, `worktree` |\n   358\t| `S5` | Conservative `worktree sync` (advances base-sha; deferral candidate) | `S4` | `worktree` |\n   359\t| `S6` | Skill changes: `subagent-driven-development` checkpoint + registry-merge-playbook; `tasklist-discipline`; `phase-planning`/`writing-plans` tables | `S2`, `S3`, `S4` | `skills` |\n   360\t| `S7` | Plan ↔ tracker drift validation | `S1`, `S6` | `validate` |\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_28","type":"command_execution","command":"/usr/bin/zsh -lc 'git status --short --untracked-files=all'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_28","type":"command_execution","command":"/usr/bin/zsh -lc 'git status --short --untracked-files=all'","aggregated_output":"?? docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/.reviewer-output/r1-primary/codex-events.jsonl\n?? docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/.reviewer-output/r1-primary/reviewer-metadata.json\n?? docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/chain.json\n?? docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/r1-2026-06-05T0106-primary-request.md\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_29","type":"command_execution","command":"/usr/bin/zsh -lc 'git diff --stat main..HEAD && git diff --name-status main..HEAD'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_29","type":"command_execution","command":"/usr/bin/zsh -lc 'git diff --stat main..HEAD && git diff --name-status main..HEAD'","aggregated_output":" skills/phase-planning/SKILL.md                     |  5 +-\n skills/subagent-driven-development/SKILL.md        | 19 ++++--\n .../references/registry-merge-playbook.md          | 49 ++++++++++++++++\n skills/tasklist-discipline/SKILL.md                | 14 +++++\n skills/writing-plans/SKILL.md                      |  2 +\n .../tests/test_skill_tasktool_lifecycle_docs.py    | 67 ++++++++++++++++++++++\n 6 files changed, 150 insertions(+), 6 deletions(-)\nM\tskills/phase-planning/SKILL.md\nM\tskills/subagent-driven-development/SKILL.md\nA\tskills/subagent-driven-development/references/registry-merge-playbook.md\nM\tskills/tasklist-discipline/SKILL.md\nM\tskills/writing-plans/SKILL.md\nM\ttools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py\n","exit_code":0,"status":"completed"}}
+{"type":"item.completed","item":{"id":"item_30","type":"agent_message","text":"The implementation diff is scoped to the expected six files, and both planned pytest commands pass. I’m doing one final pass for line-anchored acceptance mismatches; so far the only blocking mismatch is tracker lifecycle state."}}
+{"type":"item.started","item":{"id":"item_31","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md | sed -n '282,302p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_31","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md | sed -n '282,302p'\"","aggregated_output":"   282\t     verification, **then** run the post-slice review.\n   283\t  3. Reference a new **centralized-registry merge playbook**\n   284\t     (`skills/subagent-driven-development/references/registry-merge-playbook.md`):\n   285\t     preserve **both** semantic additions, regenerate checksums/snapshots, rerun\n   286\t     focused parser/schema/seed tests, then rerun integrated verification.\n   287\t- **`tasklist-discipline`:** document `surface`/`reserve`/`coordinate` in the\n   288\t  conceptual model and daily-commands list; document the recommended surface\n   289\t  vocabulary and the `coordination_group` vs `parallel_group` distinction; add\n   290\t  red-flag rows:\n   291\t  - \"These slices are feature-independent, so they're parallel-safe\" → parallel\n   292\t    safety is about **write surface**, not feature independence; declare surfaces\n   293\t    and run `surface check`.\n   294\t  - \"I'll pick a sort slot / collection name / route slug freely\" → **reserve** it\n   295\t    so siblings cannot collide; for project-global resources use `--scope project`.\n   296\t  - \"We both need the CMS registry, so I'll just `parallel_group` them\" → shared\n   297\t    surface needs a `coordination_group` (coordinate) or a `depends_on`\n   298\t    (serialize), not a `parallel_group` (which asserts independence).\n   299\t- **`phase-planning` / `writing-plans`:** when proposing parallel groups, declare\n   300\t  each slice's integration surfaces and reservations and emit a **surface/\n   301\t  reservation table** in the plan; run `tasktool surface check <phase-id>` before\n   302\t  ratifying parallel groups.\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_32","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba skills/subagent-driven-development/references/registry-merge-playbook.md | sed -n '1,80p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_32","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba skills/subagent-driven-development/references/registry-merge-playbook.md | sed -n '1,80p'\"","aggregated_output":"     1\t# Centralized-registry merge playbook\n     2\t\n     3\tUse this when a slice's worktree must integrate the current base branch and a\n     4\t**coordinated sibling slice has already landed on a shared integration surface**\n     5\t— a central registry, a parser allowlist/union, a schema or seed file, a renderer\n     6\tdispatch table, a theme CSS tail, or a homepage/ordering array. These surfaces\n     7\tcollect *additive* entries from multiple slices, so a textual merge that keeps\n     8\tonly one side silently drops a sibling's feature.\n     9\t\n    10\tThis is invoked from the **integrate-current-main checkpoint** in\n    11\t`[[subagent-driven-development]]`, before the post-slice external review.\n    12\t\n    13\t## Rule: preserve both semantic additions\n    14\t\n    15\tWhen base and your worktree both added to the same registry/array/union, the\n    16\tmerge result must contain **both** additions, not whichever side won the textual\n    17\tconflict. Read both sides and reconstruct the union by hand:\n    18\t\n    19\t1. **Identify the surface and the additions.** For each conflicting hunk, name\n    20\t   what each side added (a block contract, a parser case, a schema/seed row, a\n    21\t   dispatch entry, a CSS block, an ordering slot).\n    22\t2. **Keep both additions.** Reassemble the registry/array/union so every sibling's\n    23\t   entry survives. If two siblings added entries that must be ordered, apply the\n    24\t   declared ordering; if they collide on a scarce slot (e.g. two `homepage-sort:15`),\n    25\t   that is a reservation collision that should have been caught by `tasktool reserve\n    26\t   add` — resolve it now by moving one side to a free value and recording why.\n    27\t3. **Do not invent a merge the tool can do.** This playbook resolves *semantic*\n    28\t   additive conflicts only. It does not auto-resolve genuine logic conflicts —\n    29\t   escalate those.\n    30\t\n    31\t## Rule: regenerate derived artifacts\n    32\t\n    33\tAny file derived from the surface must be regenerated *after* the union is\n    34\tcorrect, never hand-merged:\n    35\t\n    36\t- checksums / lockfiles / content hashes,\n    37\t- snapshot fixtures,\n    38\t- generated types or generated indexes.\n    39\t\n    40\tA hand-merged checksum is a lie; regenerate it from the merged source.\n    41\t\n    42\t## Rule: rerun focused tests, then integrated verification\n    43\t\n    44\t1. Rerun the **focused** parser / schema / seed tests for the surface you merged.\n    45\t2. Then rerun the slice's **full** verification command, so the integrated tree\n    46\t   (your work + the landed sibling) is proven green before the post-slice review.\n    47\t\n    48\tIf any focused test fails, the union was reconstructed wrong — return to \"preserve\n    49\tboth semantic additions\" before rerunning the full suite.\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_33","type":"command_execution","command":"/usr/bin/zsh -lc 'git branch --show-current && git rev-parse --short main && git rev-parse --short HEAD'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_33","type":"command_execution","command":"/usr/bin/zsh -lc 'git branch --show-current && git rev-parse --short main && git rev-parse --short HEAD'","aggregated_output":"worktree-p7-s6-skill-changes-subagent-driven\n0290ebd\n84cc48e\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_34","type":"command_execution","command":"/usr/bin/zsh -lc 'git show --stat --oneline --decorate HEAD && git show --stat --oneline --decorate 6e9f0bf'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_34","type":"command_execution","command":"/usr/bin/zsh -lc 'git show --stat --oneline --decorate HEAD && git show --stat --oneline --decorate 6e9f0bf'","aggregated_output":"84cc48e (HEAD -> worktree-p7-s6-skill-changes-subagent-driven) P7.S6: require surface/reservation tables in phase-planning and writing-plans\n skills/phase-planning/SKILL.md                             |  5 ++++-\n skills/writing-plans/SKILL.md                              |  2 ++\n tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py | 11 +++++++++++\n 3 files changed, 17 insertions(+), 1 deletion(-)\n6e9f0bf P7.S6: add centralized-registry merge playbook reference\n .../references/registry-merge-playbook.md          | 49 ++++++++++++++++++++++\n .../tests/test_skill_tasktool_lifecycle_docs.py    | 16 +++++++\n 2 files changed, 65 insertions(+)\n","exit_code":0,"status":"completed"}}
+{"type":"item.completed","item":{"id":"item_35","type":"agent_message","text":"1. Findings\n\nF1 — Severity: blocking  \nThe slice lifecycle start was not completed. The plan makes Task 0 mandatory and says `tasktool start P7.S6` must move the row to `in_progress` and record the worktree base SHA before edits ([docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven/docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md:49), lines 56-64). Live tracker state still has `\"started\": null` and `\"status\": \"ready\"` ([docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven/docs/tasklist.json:414)). This is not just bookkeeping: P7.S6’s new integrate-current-main guidance depends on `worktree_base_sha`, so the slice cannot truthfully pass the completion gate until lifecycle state is repaired or explicitly documented with a corrective note.\n\n2. Open questions / assumptions\n\nI assume this review is intended to gate the implementation commits currently on `worktree-p7-s6-skill-changes-subagent-driven` at `84cc48e`, ahead of `main` at `0290ebd`.\n\n3. Suggested document edits\n\nNo plan/prose edits are needed for the implemented skill changes. The docs match the spec’s §4.F requirements: playbook, surface check before dispatch, integrate-current-main checkpoint, tasklist-discipline command/model docs, and phase/writing plan surface table requirements are present.\n\n4. Verification gaps / commands that should be run\n\nAlready verified:\n`cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -q` → 17 passed.  \n`cd tools/tasktool && python -m pytest -q` → 779 passed.  \n`tasktool surface check --help`, `tasktool reserve add --help`, `tasktool coordinate --help`, and `tasktool worktree status --help` all print usage.\n\nStill required before close:\nRepair/record the P7.S6 lifecycle state so `tasktool show P7.S6` no longer reports `status: ready` / `started: null`, then rerun `tasktool worktree status P7.S6 --integration` before accepting the post-slice gate.\n\nOverall verdict: revise"}}
+{"type":"turn.completed","usage":{"input_tokens":666128,"cached_input_tokens":614016,"output_tokens":5382,"reasoning_output_tokens":1639}}
diff --git a/docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/.reviewer-output/r1-primary/last-message.md b/docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/.reviewer-output/r1-primary/last-message.md
new file mode 100644
index 0000000..6c49d87
--- /dev/null
+++ b/docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/.reviewer-output/r1-primary/last-message.md
@@ -0,0 +1,24 @@
+1. Findings
+
+F1 — Severity: blocking  
+The slice lifecycle start was not completed. The plan makes Task 0 mandatory and says `tasktool start P7.S6` must move the row to `in_progress` and record the worktree base SHA before edits ([docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven/docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md:49), lines 56-64). Live tracker state still has `"started": null` and `"status": "ready"` ([docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven/docs/tasklist.json:414)). This is not just bookkeeping: P7.S6’s new integrate-current-main guidance depends on `worktree_base_sha`, so the slice cannot truthfully pass the completion gate until lifecycle state is repaired or explicitly documented with a corrective note.
+
+2. Open questions / assumptions
+
+I assume this review is intended to gate the implementation commits currentl

[… 153181 bytes elided to fit cap of 160000 bytes …]

ly diverge.
+   60	
+   61	## 3. Non-goals (explicit)
+   62	
+   63	- **Directus-specific verifier diagnostics and stale-token handling.** These were
+   64	  real `multistore` pain points (a stale `DIRECTUS_ADMIN_TOKEN` shadowing valid
+   65	  admin credentials made a non-code problem look like a schema failure), but they
+   66	  are project-specific. Superstar core is general-purpose and zero-dependency;
+   67	  Directus tooling belongs in the `multistore` project, not here.
+   68	- **Automatic merge-conflict resolution.** The tooling detects and routes; it does
+   69	  not auto-merge semantic conflicts.
+   70	- **Path-glob surface *inference* as the primary model.** Explicit declaration is
+   71	  the source of truth. A path-glob comparison survives only as a deferred,
+   72	  warning-only post-implementation *audit* (§4.G), never as the planning model.
+   73	- **A "touches existing resource" reservation kind.** Reservations model scarce
+   74	  *allocations* (claiming a new value). Modifying a shared existing resource is a
+   75	  *surface/coordination* concern, not an allocation, so maintenance work is not
+   76	  falsely blocked. A future "touches-existing" field is noted, not built here.
+   77	- **`worktree sync` as an unconditional command.** Detection ships first; the
+   78	  mutating sync command is gated behind strict preconditions and is the explicit
+   79	  deferral candidate if scope tightens.
+   80	
+   81	## 4. Design
+   82	
+   83	### 4.A Data model (`model.py`, schema `v2 → v3`; `migrate.py`)
+   84	
+   85	Add to `Slice`:
+   86	
+   87	- `integration_surfaces: list[str]` — conventional surface tags naming shared
+   88	  write areas the slice mutates. Free-form strings, but a recommended vocabulary
+   89	  is documented in `tasklist-discipline` (e.g. `cms-block-registry`,
+   90	  `directus-schema`, `page-renderer-dispatch`, `theme-tail-css`,
+   91	  `content-contract-types`, `reviewer-artifacts`). Default `[]`.
+   92	- `reservations: list[Reservation]` where
+   93	  `Reservation = {resource: str, value: str, scope: "phase" | "project", note: str | None}`.
+   94	  A reservation is a **scarce allocation claim** on a single value
+   95	  (`homepage-sort:15`, `directus-collection:homepage_slider`, `route-slug:/offers`,
+   96	  `block-kind:slider`, `cache-tag:home`). Default `[]`.
+   97	- `coordination_group: str | None` — names a set of slices that *intentionally*
+   98	  share an integration surface and agree to coordinate (serialize reviews,
+   99	  designate an integration owner, run the registry merge playbook). Distinct from
+  100	  `parallel_group`, which asserts independent parallelism. Default `None`.
+  101	- `worktree_base_sha: str | None` — the base-branch commit the slice's worktree
+  102	  was created from, recorded at `tasktool start`. Enables reliable
+  103	  "a sibling landed since this slice branched" detection that survives later
+  104	  rebases/merges, instead of fragile merge-base inference. Default `None`.
+  105	- `landed_base_sha: str | None` — the base-branch commit at which this slice's
+  106	  work landed, recorded at post-merge prune (see §4.D). This is the authoritative
+  107	  "this slice shipped to base" signal that `closed` (a date) cannot provide.
+  108	  Default `None`.
+  109	
+  110	Add to `Project`:
+  111	
+  112	- `reservations_ledger: list[LedgerReservation]` where
+  113	  `LedgerReservation = Reservation + {owner_id: str, owner_phase_id: str, archived_date: str}`.
+  114	  Project-scoped reservations are copied here when their owning phase is archived,
+  115	  so project-scope uniqueness checks — and the refusal message that must name the
+  116	  holder (§4.B) — survive removal of shipped phases from the active tracker. The
+  117	  extra fields preserve the owning slice/phase and archive date for the refusal
+  118	  message and audit trail. Default `[]`.
+  119	
+  120	Schema bump to `v3`. Migration is additive: missing fields default to empty/`None`
+  121	and `reservations_ledger` to `[]`. Round-trip and v1/v2 compatibility tests
+  122	extended.
+  123	
+  124	**Serialization rule (F5).** New fields follow the existing omit-when-default
+  125	convention in `serialize.py`: an empty `integration_surfaces`/`reservations`,
+  126	a `None` `coordination_group`/`worktree_base_sha`/`landed_base_sha`, and an empty
+  127	`Project.reservations_ledger` are **omitted** on serialization, exactly as
+  128	default-valued worktree/workflow keys are today. Historical rows therefore gain no
+  129	churn on round-trip; a row's bytes change only once it actually declares a surface,
+  130	reservation, coordination group, or base SHA.
+  131	
+  132	### 4.B Declaration CLI (`cli.py` + `commands.py`)
+  133	
+  134	```sh
+  135	tasktool surface add <slice-id> <surface> [<surface>...]
+  136	tasktool surface remove <slice-id> <surface>
+  137	tasktool surface list [<phase-id>]
+  138	
+  139	tasktool reserve add <slice-id> <resource>:<value> [--scope phase|project] [--note "..."] [--force --reason "..."]
+  140	tasktool reserve remove <slice-id> <resource>:<value>
+  141	tasktool reserve list [<phase-id>]
+  142	
+  143	tasktool coordinate <slice-id> --group <name>     # set coordination_group
+  144	tasktool coordinate <slice-id> --clear
+  145	```
+  146	
+  147	- `surface`/`coordinate` are declaration-only; they never refuse.
+  148	- **`reserve add` refuses** when the same `resource:value` is already held by
+  149	  another **non-cancelled** slice within the relevant scope:
+  150	  - `scope: phase` (default) — checks other non-cancelled slices in the same
+  151	    phase. Done slices count: a done slice shipped that value to `main`, so the
+  152	    slot is taken.
+  153	  - `scope: project` — checks all non-cancelled slices across **active** phases
+  154	    *and* `Project.reservations_ledger`.
+  155	  The refusal names the holding slice (from the slice row, or from the ledger's
+  156	  `owner_id`/`owner_phase_id`/`archived_date` for archived holders) and the value.
+  157	- **Override (F3).** `--force` is the only way to add a colliding reservation and
+  158	  **requires** `--reason "<text>"`. It mutates **only the reserving slice**: it
+  159	  appends the reservation and records a timestamped note
+  160	  `Reservation-override <ISO-ts>: <resource>:<value> over <holder-id> — <reason>`.
+  161	  The holder slice is **not** mutated. `--force` without `--reason` is refused.
+  162	  Without `--force`, a collision is a hard refusal (exit non-zero). This refusal
+  163	  is the gate that would have forced `P20.S4` off slot `15` at planning time.
+  164	- **Cancelled work never enters the ledger.** On `tasktool archive-phase`,
+  165	  project-scoped reservations from the phase's **non-cancelled (`done`)** slices
+  166	  are appended to `Project.reservations_ledger` as `LedgerReservation`s, carrying
+  167	  `owner_id`/`owner_phase_id`/`archived_date`. Cancelled slices ship nothing, so
+  168	  their reservations — including `--force` overrides — are released and never
+  169	  laddered.
+  170	- **Ledger dedupe preserves every holder (F7).** Dedup is keyed on
+  171	  `resource:value:scope:owner_id`, **not** `resource:value:scope`. Re-archiving the
+  172	  same phase is idempotent (same owner ⇒ same key), but two distinct `done` slices
+  173	  that intentionally `--force`-shared a project-scoped value both survive in the
+  174	  ledger, so the owner-metadata audit trail is never silently collapsed to one
+  175	  holder. A project-scope `reserve add` collision check that matches any ledger
+  176	  entry on `resource:value:scope` (regardless of owner) still refuses — multiple
+  177	  recorded holders strengthen, not weaken, the refusal message.
+  178	
+  179	### 4.C Scheduling overlap detection (`commands.py`)
+  180	
+  181	Augment the existing scheduling reporters; **surface overlap is a warning, not a
+  182	block** (surfaces are coarse — two slices may touch the same registry in
+  183	non-conflicting ways), while **reservation contention is already prevented at
+  184	declaration time**.
+  185	
+  186	- `cmd_ready_slices` and `cmd_schedule`: for each ready/in-progress slice, compute
+  187	  the set of other non-terminal slices that (a) share ≥1 integration surface,
+  188	  (b) have **no** `depends_on` link in either direction, and (c) are **not** in
+  189	  the same `coordination_group`. Emit a `surface_overlap` field/warning listing
+  190	  the sibling(s) and shared surface(s). Slices in a shared `coordination_group`
+  191	  are reported as `coordinated`, not warned.
+  192	- New `tasktool surface check <phase-id>` — a dedicated read-only report:
+  193	  - every unguarded surface overlap (siblings sharing a surface without a dep or
+  194	    coordination link),
+  195	  - every coordinated surface (shared surface within a `coordination_group`),
+  196	  - reservation contention within the phase (should be empty if `reserve add`
+  197	    refusal held; surfaced for audit and for `--force` overrides).
+  198	  Text and `--format json`. Intended to be run during ratification and before
+  199	  parallel dispatch.
+  200	- `cmd_ratify --parallel-group <g>`: when adding a slice whose surfaces overlap
+
+[truncated: 211 additional lines]
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
+   14	    },
+   15	    {
+   16	      "archived_date": "2026-05-23",
+   17	      "archived_path": "docs/archived-tasks/X18-harden-external-reviewer-caller-detectio.md",
+   18	      "id": "X18",
+   19	      "title": "Harden external reviewer caller detection for Codex"
+   20	    },
+   21	    {
+   22	      "archived_date": "2026-05-23",
+   23	      "archived_path": "docs/archived-tasks/X20-install-codex-todo-snapshot-hook.md",
+   24	      "id": "X20",
+   25	      "title": "Install Codex todo snapshot hook"
+   26	    },
+   27	    {
+   28	      "archived_date": "2026-05-23",
+   29	      "archived_path": "docs/archived-tasks/X19-install-todowrite-snapshot-hook-via-depl.md",
+   30	      "id": "X19",
+   31	      "title": "Install TodoWrite snapshot hook via deploy.sh"
+   32	    },
+   33	    {
+   34	      "archived_date": "2026-05-23",
+   35	      "archived_path": "docs/archived-tasks/X21-fix-codex-todo-snapshot-async-hook-regis.md",
+   36	      "id": "X21",
+   37	      "title": "Fix Codex todo snapshot async hook registration"
+   38	    },
+   39	    {
+   40	      "archived_date": "2026-05-24",
+   41	      "archived_path": "docs/archived-tasks/X22-add-cancelled-terminal-status-to-tasktoo.md",
+   42	      "id": "X22",
+   43	      "title": "Add cancelled terminal status to tasktool"
+   44	    },
+   45	    {
+   46	      "archived_date": "2026-05-24",
+   47	      "archived_path": "docs/archived-tasks/X23-document-cancelled-lifecycle-and-admin-c.md",
+   48	      "id": "X23",
+   49	      "title": "Document cancelled lifecycle and admin closeout guidance"
+   50	    },
+   51	    {
+   52	      "archived_date": "2026-05-26",
+   53	      "archived_path": "docs/archived-tasks/X24-use-global-tasktool-shim-in-superstar-gu.md",
+   54	      "id": "X24",
+   55	      "title": "Use global tasktool shim in Superstar guidance"
+   56	    },
+   57	    {
+   58	      "archived_date": "2026-05-26",
+   59	      "archived_path": "docs/archived-tasks/X25-duck-media-audio-during-tasktool-tts-and.md",
+   60	      "id": "X25",
+   61	      "title": "Duck media audio during tasktool TTS and verify Codex plugin payload"
+   62	    },
+   63	    {
+   64	      "archived_date": "2026-05-26",
+   65	      "archived_path": "docs/archived-tasks/X26-fix-codex-marketplace-payload-refresh-fo.md",
+   66	      "id": "X26",
+   67	      "title": "Fix Codex marketplace payload refresh for Superstar"
+   68	    },
+   69	    {
+   70	      "archived_date": "2026-05-26",
+   71	      "archived_path": "docs/archived-tasks/X1-default-external-review-prompt-transport.md",
+   72	      "id": "X1",
+   73	      "title": "Default external-review prompt transport to stdin"
+   74	    },
+   75	    {
+   76	      "archived_date": "2026-05-26",
+   77	      "archived_path": "docs/archived-tasks/X2-add-repo-local-tasktool-launcher.md",
+   78	      "id": "X2",
+   79	      "title": "Add repo-local tasktool launcher"
+   80	    },
+   81	    {
+   82	      "archived_date": "2026-05-26",
+   83	      "archived_path": "docs/archived-tasks/X3-spot-fix-parse-bold-external-review-verd.md",
+   84	      "id": "X3",
+   85	      "title": "Spot fix: parse bold external-review verdict headings"
+   86	    },
+   87	    {
+   88	      "archived_date": "2026-05-26",
+   89	      "archived_path": "docs/archived-tasks/X4-spot-fix-broaden-legacy-tasklist-importe.md",
+   90	      "id": "X4",
+   91	      "title": "Spot fix: broaden legacy tasklist importer compatibility"
+   92	    },
+   93	    {
+   94	      "archived_date": "2026-05-26",
+   95	      "archived_path": "docs/archived-tasks/X5-add-finished-agent-notification-hook.md",
+   96	      "id": "X5",
+   97	      "title": "Add finished-agent notification hook"
+   98	    },
+   99	    {
+  100	      "archived_date": "2026-05-26",
+  101	      "archived_path": "docs/archived-tasks/X6-fix-codex-finished-agent-hook-compatibil.md",
+  102	      "id": "X6",
+  103	      "title": "Fix Codex finished-agent hook compatibility"
+  104	    },
+  105	    {
+  106	      "archived_date": "2026-05-26",
+  107	      "archived_path": "docs/archived-tasks/X7-fix-superstar-codex-plugin-payload-versi.md",
+  108	      "id": "X7",
+  109	      "title": "Fix Superstar Codex plugin payload version drift"
+  110	    },
+  111	    {
+  112	      "archived_date": "2026-05-26",
+  113	      "archived_path": "docs/archived-tasks/X8-move-semantic-notifications-from-agent-h.md",
+  114	      "id": "X8",
+  115	      "title": "Move semantic notifications from agent hooks to tasktool status changes"
+  116	    },
+  117	    {
+  118	      "archived_date": "2026-05-26",
+  119	      "archived_path": "docs/archived-tasks/X9-coalesce-bursty-tasktool-audio-notificat.md",
+  120	      "id": "X9",
+  121	      "title": "Coalesce bursty tasktool audio notifications"
+  122	    },
+  123	    {
+  124	      "archived_date": "2026-05-26",
+  125	      "archived_path": "docs/archived-tasks/X10-harden-external-review-verdict-parser-an.md",
+  126	      "id": "X10",
+  127	      "title": "Harden external-review verdict parser and prompt against Claude formatting variants"
+  128	    },
+  129	    {
+  130	      "archived_date": "2026-05-26",
+  131	      "archived_path": "docs/archived-tasks/X11-make-external-review-bridge-global.md",
+  132	      "id": "X11",
+  133	      "title": "Make external-review bridge global"
+  134	    },
+  135	    {
+  136	      "archived_date": "2026-05-26",
+  137	      "archived_path": "docs/archived-tasks/X12-tasktool-require-authoritative-checkout-.md",
+  138	      "id": "X12",
+  139	      "title": "tasktool: require authoritative-checkout routing for mutations"
+  140	    },
+  141	    {
+  142	      "archived_date": "2026-05-26",
+  143	      "archived_path": "docs/archived-tasks/X13-fix-tasktool-close-repeated-refs-parsing.md",
+  144	      "id": "X13",
+  145	      "title": "Fix tasktool close repeated refs parsing"
+  146	    },
+  147	    {
+  148	      "archived_date": "2026-05-26",
+  149	      "archived_path": "docs/archived-tasks/X14-stabilize-local-claude-codex-plugin-curr.md",
+  150	      "id": "X14",
+  151	      "title": "Stabilize local Claude/Codex plugin current entrypoints"
+  152	    },
+  153	    {
+  154	      "archived_date": "2026-05-26",
+  155	      "archived_path": "docs/archived-tasks/X17-make-spec-and-plan-artifact-handling-tra.md",
+  156	      "id": "X17",
+  157	      "title": "Make spec and plan artifact handling transactional"
+  158	    },
+  159	    {
+  160	      "archived_date": "2026-05-26",
+  161	      "archived_path": "docs/archived-tasks/X27-add-tasktool-tts-for-workflow-artifacts-.md",
+  162	      "id": "X27",
+  163	      "title": "Add tasktool TTS for workflow artifacts and step changes"
+  164	    },
+  165	    {
+  166	      "archived_date": "2026-05-26",
+  167	      "archived_path": "docs/archived-tasks/X28-prefer-explicit-notification-ding-sound-.md",
+  168	      "id": "X28",
+  169	      "title": "Prefer explicit notification ding sound file"
+  170	    }
+  171	  ],
+  172	  "archived_phases": [
+  173	    {
+  174	      "archived_date": "2026-05-18",
+  175	      "archived_path": "docs/archived-tasks/P2-tasktool-json-backed-task-management-cli.md",
+  176	      "id": "P2",
+  177	      "title": "tasktool: JSON-backed task management CLI"
+  178	    },
+  179	    {
+  180	      "archived_date": "2026-05-19",
+  181	      "archived_path": "docs/archived-tasks/P4-tasktool-coordination-and-lifecycle-auth.md",
+  182	      "id": "P4",
+  183	      "title": "Tasktool coordination and lifecycle authority"
+  184	    },
+  185	    {
+  186	      "archived_date": "2026-05-19",
+  187	      "archived_path": "docs/archived-tasks/P3-phase-planning-workflow.md",
+  188	      "id": "P3",
+  189	      "title": "Phase planning workflow"
+  190	    },
+  191	    {
+  192	      "archived_date": "2026-05-20",
+  193	      "archived_path": "docs/archived-tasks/P1-external-reviewer-work-historical.md",
+  194	      "id": "P1",
+  195	      "title": "External-reviewer work (historical)"
+  196	    },
+  197	    {
+  198	      "archived_date": "2026-05-21",
+  199	      "archived_path": "docs/archived-tasks/P5-tasktool-owned-worktree-lifecycle-using-.md",
+  200	      "id": "P5",
+
+[truncated: 272 additional lines]
+
+<!-- superstar-prompt:end -->
\ No newline at end of file
diff --git a/docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/r1-2026-06-05T0106-primary-response.md b/docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/r1-2026-06-05T0106-primary-response.md
new file mode 100644
index 0000000..ab3f31e
--- /dev/null
+++ b/docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/r1-2026-06-05T0106-primary-response.md
@@ -0,0 +1,35 @@
+# Review — 2026-06-04-P7-S6-skill-integration-surface-docs.md (post-slice, round 1)
+
+- Target: `docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md`
+- Request: `docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/r1-2026-06-05T0106-primary-request.md`
+- Reviewer command: `reviewer-agent`
+- Reviewer provider: `codex`
+- Sandbox: repo read-only; scratch/output writable
+- Status: `ok`
+
+---
+
+1. Findings
+
+F1 — Severity: blocking  
+The slice lifecycle start was not completed. The plan makes Task 0 mandatory and says `tasktool start P7.S6` must move the row to `in_progress` and record the worktree base SHA before edits ([docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven/docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md:49), lines 56-64). Live tracker state still has `"started": null` and `"status": "ready"` ([docs/tasklist.json](/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven/docs/tasklist.json:414)). This is not just bookkeeping: P7.S6’s new integrate-current-main guidance depends on `worktree_base_sha`, so the slice cannot truthfully pass the completion gate until lifecycle state is repaired or explicitly documented with a corrective note.
+
+2. Open questions / assumptions
+
+I assume this review is intended to gate the implementation commits currently on `worktree-p7-s6-skill-changes-subagent-driven` at `84cc48e`, ahead of `main` at `0290ebd`.
+
+3. Suggested document edits
+
+No plan/prose edits are needed for the implemented skill changes. The docs match the spec’s §4.F requirements: playbook, surface check before dispatch, integrate-current-main checkpoint, tasklist-discipline command/model docs, and phase/writing plan surface table requirements are present.
+
+4. Verification gaps / commands that should be run
+
+Already verified:
+`cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -q` → 17 passed.  
+`cd tools/tasktool && python -m pytest -q` → 779 passed.  
+`tasktool surface check --help`, `tasktool reserve add --help`, `tasktool coordinate --help`, and `tasktool worktree status --help` all print usage.
+
+Still required before close:
+Repair/record the P7.S6 lifecycle state so `tasktool show P7.S6` no longer reports `status: ready` / `started: null`, then rerun `tasktool worktree status P7.S6 --integration` before accepting the post-slice gate.
+
+Overall verdict: revise
diff --git a/docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/r1-2026-06-05T0106-sweep1-request.md b/docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/r1-2026-06-05T0106-sweep1-request.md
new file mode 100644
index 0000000..6ceb3d3
--- /dev/null
+++ b/docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice/r1-2026-06-05T0106-sweep1-request.md
@@ -0,0 +1,969 @@
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
+/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven
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
+docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md
+
+Additional context files:
+- docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md
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
+### docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md
+
+    1	# P7.S6 — Skill changes for integration-surface-aware parallel safety: Implementation Plan
+    2	
+    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
+    4	
+    5	**Goal:** Teach the workflow skills the integration-surface model shipped in P7.S2–S4 so coordinators declare surfaces/reservations, run `surface check` before parallel dispatch, and integrate current `main` before each post-slice review.
+    6	
+    7	**Architecture:** Pure documentation slice. It edits four `SKILL.md` files and adds one reference file, and is guarded by string-assertion tests in the existing docs-lifecycle test (`tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`). No tasktool Python behaviour changes — the CLI surface (`surface`/`reserve`/`coordinate`/`surface check`/`worktree status --integration`) already exists. TDD here means: add a failing doc-content assertion, run it red, edit the skill prose to make it green, commit.
+    8	
+    9	**Tech Stack:** Markdown skill files under `skills/`; pytest doc-content assertions under `tools/tasktool/tests/`.
+   10	
+   11	---
+   12	
+   13	## Spec reference
+   14	
+   15	This slice implements **§4.F** of the P7 spec (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md`) and its testing line in **§6 (`S6`)**: *"docs lifecycle test extended to assert the new commands and the integrate-main checkpoint are documented; playbook file exists."*
+   16	
+   17	§4.F deliverables:
+   18	- **`subagent-driven-development`** — (1) run `tasktool surface check <phase-id>` after `ready-slices` and do not parallel-dispatch surface-sharing slices without a `depends_on` or `coordination_group`; (2) an *integrate-current-main* checkpoint before `external-review --kind post-slice`; (3) a new `references/registry-merge-playbook.md`.
+   19	- **`tasklist-discipline`** — document `surface`/`reserve`/`coordinate` in the conceptual model and daily-commands list; the recommended surface vocabulary; the `coordination_group` vs `parallel_group` distinction; three new red-flag rows.
+   20	- **`phase-planning` / `writing-plans`** — declare surfaces/reservations when proposing parallel groups, emit a **surface/reservation table** in the plan, and run `tasktool surface check <phase-id>` before ratifying parallel groups.
+   21	
+   22	## Scheduling contract (confirmed before drafting)
+   23	
+   24	- `tasktool show P7.S6`: status `ready`, `depends_on = [P7.S2, P7.S3, P7.S4]` (all `done`), no `parallel_group`, `planning_status = proposed`.
+   25	- `tasktool ready-slices P7` lists `P7.S6` as ready.
+   26	- No dependency change is needed. This plan **does not** depend on P7.S5 (`worktree sync`); the integrate-current-main checkpoint therefore documents `worktree sync` as the preferred path *when available* plus a raw-git fallback, exactly as §4.F specifies.
+   27	- The slice is ratified at **plan-settle** — in this planning session, immediately after the plan review passes — with `tasktool ratify P7.S6` (keeps `depends_on = [P7.S2, P7.S3, P7.S4]`, adds no parallel group). Execution does **not** re-ratify; by the time Task 0 runs, `planning_status` is already `ratified` and committed.
+   28	
+   29	## File Structure
+   30	
+   31	| File | Responsibility | Action |
+   32	|------|----------------|--------|
+   33	| `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` | Doc-content regression for all workflow skills | **Modify** — add 5 assertion functions |
+   34	| `skills/subagent-driven-development/references/registry-merge-playbook.md` | Centralized-registry merge recipe referenced from the integrate-main checkpoint | **Create** |
+   35	| `skills/subagent-driven-development/SKILL.md` | Coordinator orchestration loop | **Modify** — surface check before dispatch, integrate-main checkpoint, playbook reference |
+   36	| `skills/tasklist-discipline/SKILL.md` | tasktool CLI surface + conceptual model | **Modify** — conceptual model paragraph, daily-commands block, 3 red-flag rows |
+   37	| `skills/phase-planning/SKILL.md` | Phase shaping + scheduling graph | **Modify** — declaration step, surface/reservation table requirement, red flag |
+   38	| `skills/writing-plans/SKILL.md` | Slice plan authoring | **Modify** — surface/reservation table requirement in scheduling ratification |
+   39	
+   40	The five test functions are split one-per-skill-area so each implementation task has a dedicated red→green pair.
+   41	
+   42	---
+   43	
+   44	## Task 0: Start the slice
+   45	
+   46	**Files:**
+   47	- No source changes; lifecycle only.
+   48	
+   49	This is the mandatory first execution step from `[[writing-plans]]`: record the slice lifecycle start (and the worktree base SHA) before editing any files. The row is already `ratified` from the planning session — Task 0 only moves it to `in_progress`.
+   50	
+   51	- [ ] **Step 1: Verify you are in the slice's isolated worktree**
+   52	
+   53	Run: `git status --short`
+   54	Expected: a clean tree (no unrelated dirty files). If this is a shared `main`/`master` checkout and the human partner has not opted out of isolation, stop and create the slice worktree via `[[using-git-worktrees]]` first.
+   55	
+   56	- [ ] **Step 2: Start the slice**
+   57	
+   58	Run: `tasktool start P7.S6`
+   59	Expected: the row moves to `in_progress` and the worktree base SHA is recorded.
+   60	
+   61	- [ ] **Step 3: Confirm the lifecycle state**
+   62	
+   63	Run: `tasktool show P7.S6`
+   64	Expected: `status: in_progress`, `planning_status: ratified`, `depends_on: P7.S2, P7.S3, P7.S4`.
+   65	
+   66	---
+   67	
+   68	## Task 1: Registry merge playbook reference file
+   69	
+   70	**Files:**
+   71	- Create: `skills/subagent-driven-development/references/registry-merge-playbook.md`
+   72	- Test: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`
+   73	
+   74	- [ ] **Step 1: Write the failing test**
+   75	
+   76	Append to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:
+   77	
+   78	```python
+   79	def test_registry_merge_playbook_exists() -> None:
+   80	    playbook = (
+   81	        ROOT
+   82	        / "skills"
+   83	        / "subagent-driven-development"
+   84	        / "references"
+   85	        / "registry-merge-playbook.md"
+   86	    )
+   87	    assert playbook.is_file(), f"registry merge playbook must exist at {playbook}"
+   88	    body = playbook.read_text(encoding="utf-8")
+   89	    # The playbook's load-bearing instructions.
+   90	    assert "preserve both" in body.lower()
+   91	    assert "regenerate" in body.lower()
+   92	    assert "rerun" in body.lower()
+   93	```
+   94	
+   95	- [ ] **Step 2: Run test to verify it fails**
+   96	
+   97	Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py::test_registry_merge_playbook_exists -q`
+   98	Expected: FAIL — `AssertionError: registry merge playbook must exist at …` (file does not exist yet).
+   99	
+  100	- [ ] **Step 3: Create the playbook file**
+  101	
+  102	Create `skills/subagent-driven-development/references/registry-merge-playbook.md` with this exact content:
+  103	
+  104	```markdown
+  105	# Centralized-registry merge playbook
+  106	
+  107	Use this when a slice's worktree must integrate the current base branch and a
+  108	**coordinated sibling slice has already landed on a shared integration surface**
+  109	— a central registry, a parser allowlist/union, a schema or seed file, a renderer
+  110	dispatch table, a theme CSS tail, or a homepage/ordering array. These surfaces
+  111	collect *additive* entries from multiple slices, so a textual merge that keeps
+  112	only one side silently drops a sibling's feature.
+  113	
+  114	This is invoked from the **integrate-current-main checkpoint** in
+  115	`[[subagent-driven-development]]`, before the post-slice external review.
+  116	
+  117	## Rule: preserve both semantic additions
+  118	
+  119	When base and your worktree both added to the same registry/array/union, the
+  120	merge result must contain **both** additions, not whichever side won the textual
+  121	conflict. Read both sides and reconstruct the union by hand:
+  122	
+  123	1. **Identify the surface and the additions.** For each conflicting hunk, name
+  124	   what each side added (a block contract, a parser case, a schema/seed row, a
+  125	   dispatch entry, a CSS block, an ordering slot).
+  126	2. **Keep both additions.** Reassemble the registry/array/union so every sibling's
+  127	   entry survives. If two siblings added entries that must be ordered, apply the
+  128	   declared ordering; if they collide on a scarce slot (e.g. two `homepage-sort:15`),
+  129	   that is a reservation collision that should have been caught by `tasktool reserve
+  130	   add` — resolve it now by moving one side to a free value and recording why.
+  131	3. **Do not invent a merge the tool can do.** This playbook resolves *semantic*
+  132	   additive conflicts only. It does not auto-resolve genuine logic conflicts —
+  133	   escalate those.
+  134	
+  135	## Rule: regenerate derived artifacts
+  136	
+  137	Any file derived from the surface must be regenerated *after* the union is
+  138	correct, never hand-merged:
+  139	
+  140	- checksums / lockfiles / content hashes,
+  141	- snapshot fixtures,
+  142	- generated types or generated indexes.
+  143	
+  144	A hand-merged checksum is a lie; regenerate it from the merged source.
+  145	
+  146	## Rule: rerun focused tests, then integrated verification
+  147	
+  148	1. Rerun the **focused** parser / schema / seed tests for the surface you merged.
+  149	2. Then rerun the slice's **full** verification command, so the integrated tree
+  150	   (your work + the landed sibling) is proven green before the post-slice review.
+  151	
+  152	If any focused test fails, the union was reconstructed wrong — return to "preserve
+  153	both semantic additions" before rerunning the full suite.
+  154	```
+  155	
+  156	- [ ] **Step 4: Run test to verify it passes**
+  157	
+  158	Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py::test_registry_merge_playbook_exists -q`
+  159	Expected: PASS.
+  160	
+  161	- [ ] **Step 5: Commit**
+  162	
+  163	```bash
+  164	git add skills/subagent-driven-development/references/registry-merge-playbook.md \
+  165	        tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
+  166	git commit -m "P7.S6: add centralized-registry merge playbook reference"
+  167	```
+  168	
+  169	---
+  170	
+  171	## Task 2: subagent-driven-development — surface check, integrate-main checkpoint, playbook reference
+  172	
+  173	**Files:**
+  174	- Modify: `skills/subagent-driven-development/SKILL.md`
+  175	- Test: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`
+  176	
+  177	- [ ] **Step 1: Write the failing test**
+  178	
+  179	Append to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:
+  180	
+  181	```python
+  182	def test_subagent_driven_development_runs_surface_check_before_parallel_dispatch() -> None:
+  183	    text = skill_text("subagent-driven-development")
+  184	    assert "tasktool surface check <phase-id>" in text
+  185	    assert "Do not parallel-dispatch slices that share an integration surface" in text
+  186	    # surface check is described alongside ready-slices, before dispatch
+  187	    rs = text.index("tasktool ready-slices <phase-id>")
+  188	    sc = text.index("tasktool surface check <phase-id>")
+  189	    assert rs < sc, "surface check must be documented after ready-slices"
+  190	
+  191	
+  192	def test_subagent_driven_development_has_integrate_main_checkpoint() -> None:
+  193	    text = skill_text("subagent-driven-development")
+  194	    assert "tasktool worktree status <slice-id> --integration" in text
+  195	    assert "Integrate-current-main checkpoint" in text
+  196	    assert "references/registry-merge-playbook.md" in text
+  197	    # the checkpoint precedes the close gate in the slice-end sequence
+  198	    integ = text.index("tasktool worktree status <slice-id> --integration")
+  199	    close = text.index("tasktool close <slice-id>")
+  200	    assert integ < close, "integrate-main checkpoint must precede the close gate"
+  201	```
+  202	
+  203	- [ ] **Step 2: Run tests to verify they fail**
+  204	
+  205	Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -k "surface_check_before_parallel_dispatch or integrate_main" -q`
+  206	Expected: FAIL — both assert the new strings are absent from the skill.
+  207	
+  208	- [ ] **Step 3a: Add the surface-check paragraph before parallel dispatch**
+  209	
+  210	In `skills/subagent-driven-development/SKILL.md`, find the paragraph that begins `Before dispatching implementation work for a phase, run` (currently line 41). **Immediately after** that paragraph (before the `Parallel slices must run in separate worktrees.` paragraph), insert this new paragraph:
+  211	
+  212	```markdown
+  213	After `tasktool ready-slices <phase-id>`, run `tasktool surface check <phase-id>` before dispatching any slices in parallel. **Do not parallel-dispatch slices that share an integration surface without a declared `depends_on` or a shared `coordination_group`.** A shared write surface — a central registry, a schema/seed file, a renderer dispatch table, a parser union, a theme CSS tail, an ordering array — is what actually governs merge safety; feature independence does not. When `surface check` reports an unguarded `surface_overlap`, either **serialize** the slices (`tasktool deps <later-slice-id> --add <earlier-slice-id>`) or **coordinate** them (`tasktool coordinate <slice-id> --group <name>`, designate one slice as the integration owner, and plan to run the centralized-registry merge playbook at merge). Slices reported as `coordinated` may proceed in parallel; unguarded overlaps must be resolved first.
+  214	```
+  215	
+  216	- [ ] **Step 3b: Add the integrate-current-main checkpoint to the slice-end sequence**
+  217	
+  218	In the same file, find the `At the end of each slice` numbered list (currently lines 54–59). It currently reads:
+  219	
+  220	```markdown
+  221	- **At the end of each slice** (all the slice's tasks closed, in-loop internal reviews passed):
+  222	  1. Run `git status --short`. If setup/migration artifacts, unrelated reviewer chains, legacy path moves, unrelated tasklist mutations, files from another slice, or other dirty files outside the slice scope are present, stop and resolve that boundary before review.
+  223	  2. Invoke `[[external-review]]` with `--kind post-slice`, passing the plan as `--file` and the spec + `docs/tasklist.json` as `--context`.
+  224	  3. Read the verdict. On `ready` / `ready with small edits`, proceed.
+  225	  4. On `merged_verdict: revise` (or `verdict_valid: false`), **dispatch a fix subagent** with the previous response file as input. The fix subagent MUST write `docs/reviewer/<chain>/r{N}-resolution.md` per the contract in `[[external-review]]` before signaling completion. Wait for completion. Re-submit. Iterate.
+  226	  5. Once the verdict gates pass, run `tasktool close <slice-id>` (the CLI re-checks the reviewer chain and refuses on `revise`). See `[[tasklist-discipline]]`.
+  227	```
+  228	
+  229	Replace it with this (a new step 2 is inserted; the rest renumber to 3–6):
+  230	
+  231	```markdown
+  232	- **At the end of each slice** (all the slice's tasks closed, in-loop internal reviews passed):
+  233	  1. Run `git status --short`. If setup/migration artifacts, unrelated reviewer chains, legacy path moves, unrelated tasklist mutations, files from another slice, or other dirty files outside the slice scope are present, stop and resolve that boundary before review.
+  234	  2. **Integrate-current-main checkpoint.** Run `tasktool worktree status <slice-id> --integration`. If a sibling slice has landed on the base branch since this slice's `worktree_base_sha` — especially one that shares an integration surface with this slice — integrate the current base branch into the worktree **before** the post-slice review: run `tasktool worktree sync <slice-id> --merge` (or `--rebase`) when that command is available, otherwise merge the base branch with raw git (`git merge <base-branch>`). Resolve any registry / schema / seed / ordering conflicts with the centralized-registry merge playbook (`references/registry-merge-playbook.md`), regenerate derived artifacts (checksums, snapshots), and rerun verification. Only then proceed. Skipping this replays already-integrated churn and produces stale-base merges. If `worktree status --integration` reports `landed: unknown` for a sibling, treat it as possibly-landed and inspect before proceeding.
+  235	  3. Invoke `[[external-review]]` with `--kind post-slice`, passing the plan as `--file` and the spec + `docs/tasklist.json` as `--context`.
+  236	  4. Read the verdict. On `ready` / `ready with small edits`, proceed.
+  237	  5. On `merged_verdict: revise` (or `verdict_valid: false`), **dispatch a fix subagent** with the previous response file as input. The fix subagent MUST write `docs/reviewer/<chain>/r{N}-resolution.md` per the contract in `[[external-review]]` before signaling completion. Wait for completion. Re-submit. Iterate.
+  238	  6. Once the verdict gates pass, run `tasktool close <slice-id>` (the CLI re-checks the reviewer chain and refuses on `revise`). See `[[tasklist-discipline]]`.
+  239	```
+  240	
+  241	- [ ] **Step 3c: Add the integrate-main node to the process digraph**
+  242	
+  243	In the same file, in the `digraph process` block, find this edge (currently line 145):
+  244	
+  245	```dot
+  246	    "Last task in slice?" -> "Invoke external-review --kind post-slice" [label="yes"];
+  247	```
+  248	
+  249	Replace it with a node insertion that routes through the checkpoint:
+  250	
+  251	```dot
+  252	    "Integrate current main (worktree status --integration)" [shape=box];
+  253	    "Last task in slice?" -> "Integrate current main (worktree status --integration)" [label="yes"];
+  254	    "Integrate current main (worktree status --integration)" -> "Invoke external-review --kind post-slice";
+  255	```
+  256	
+  257	- [ ] **Step 3d: Reference the playbook in a References section**
+  258	
+  259	In the same file, find the `## Prompt Templates` section (currently lines 197–201). **Immediately after** that section's bullet list, insert:
+  260	
+  261	```markdown
+  262	## References
+  263	
+  264	- `./references/registry-merge-playbook.md` — how to merge centralized-registry / schema / seed / ordering conflicts when a coordinated sibling slice has landed before this slice's post-slice review: preserve **both** semantic additions, regenerate derived artifacts, rerun focused parser/schema/seed tests, then rerun integrated verification.
+  265	```
+  266	
+  267	- [ ] **Step 4: Run tests to verify they pass**
+  268	
+  269	Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -k "surface_check_before_parallel_dispatch or integrate_main" -q`
+  270	Expected: PASS (2 passed).
+  271	
+  272	Also confirm the pre-existing ordering test still holds:
+  273	Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py::test_subagent_driven_development_starts_slice_before_dispatch -q`
+  274	Expected: PASS.
+  275	
+  276	- [ ] **Step 5: Commit**
+  277	
+  278	```bash
+  279	git add skills/subagent-driven-development/SKILL.md \
+  280	        tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
+  281	git commit -m "P7.S6: surface-check gate + integrate-current-main checkpoint in subagent-driven-development"
+  282	```
+  283	
+  284	---
+  285	
+  286	## Task 3: tasklist-discipline — surface/reserve/coordinate model, commands, red flags
+  287	
+  288	**Files:**
+  289	- Modify: `skills/tasklist-discipline/SKILL.md`
+  290	- Test: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`
+  291	
+  292	- [ ] **Step 1: Write the failing test**
+  293	
+  294	Append to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:
+  295	
+  296	```python
+  297	def test_tasklist_discipline_documents_surface_reserve_coordinate() -> None:
+  298	    text = skill_text("tasklist-discipline")
+  299	    # daily-commands surface
+  300	    assert "tasktool surface add <slice-id>" in text
+  301	    assert "tasktool surface check <phase-id>" in text
+  302	    assert "tasktool reserve add <slice-id>" in text
+  303	    assert "tasktool coordinate <slice-id> --group" in text
+  304	    # conceptual model + vocabulary
+  305	    assert "integration_surfaces" in text
+  306	    assert "reservations" in text
+  307	    assert "cms-block-registry" in text
+  308	    # coordination_group vs parallel_group distinction is spelled out
+  309	    assert "coordination_group" in text
+  310	    assert "parallel_group" in text
+  311	    # the three new red-flag claims
+  312	    assert "feature independence" in text
+  313	    assert "duplicate" in text.lower()
+  314	```
+  315	
+  316	- [ ] **Step 2: Run test to verify it fails**
+  317	
+  318	Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py::test_tasklist_discipline_documents_surface_reserve_coordinate -q`
+  319	Expected: FAIL — new strings absent.
+  320	
+  321	- [ ] **Step 3a: Add the integration-surface paragraph to the conceptual model**
+  322	
+  323	In `skills/tasklist-discipline/SKILL.md`, find the paragraph that begins `Phase planning uses separate scheduling metadata.` (currently line 51). **Immediately after** it, insert this new paragraph:
+  324	
+  325	```markdown
+  326	Integration-surface metadata models **parallel-execution safety by write surface**, not by feature intent. `integration_surfaces` is a list of conventional tags naming the shared write areas a slice mutates (recommended vocabulary: `cms-block-registry`, `directus-schema`, `page-renderer-dispatch`, `theme-tail-css`, `content-contract-types`, `reviewer-artifacts` — extend per project). `reservations` are scarce-allocation claims on a single value (`homepage-sort:15`, `route-slug:/offers`, `block-kind:slider`), each scoped `phase` (default) or `project`; `tasktool reserve add` **refuses a duplicate allocation** within scope. `coordination_group` names a set of slices that *intentionally* share a surface and agree to coordinate — serialize reviews, designate an integration owner, run the centralized-registry merge playbook. It is the opposite of `parallel_group`, which asserts the slices are independent: a shared surface needs a `coordination_group` or a `depends_on`, never a `parallel_group`.
+  327	```
+  328	
+  329	- [ ] **Step 3b: Add the commands to the daily-commands block**
+  330	
+  331	In the same file, find the `tasktool ratify <slice-id> --parallel-group bootstrap` line inside the ```sh ... ``` daily-commands block (currently line 70). **Immediately after** that line, insert these lines (inside the same code fence):
+  332	
+  333	```sh
+  334	tasktool surface add <slice-id> <surface> [<surface>...]   # declare shared write surfaces
+  335	tasktool surface remove <slice-id> <surface>
+  336	tasktool surface list [<phase-id>]
+  337	tasktool surface check <phase-id>            # unguarded overlaps + coordinated surfaces + reservation contention
+  338	tasktool reserve add <slice-id> <resource>:<value> [--scope phase|project] [--note "..."] [--force --reason "..."]
+  339	tasktool reserve remove <slice-id> <resource>:<value>
+  340	tasktool reserve list [<phase-id>]
+  341	tasktool coordinate <slice-id> --group <name>   # mark intentional shared-surface coordination
+  342	tasktool coordinate <slice-id> --clear
+  343	```
+  344	
+  345	- [ ] **Step 3c: Add the three red-flag rows**
+  346	
+  347	In the same file, find the `## Red flags` table. The last data row currently is the `"The slice is currently blocked, so I'll add blocked_on to model the phase plan."` row (line 185). **Immediately after** that row, append these three rows:
+  348	
+  349	```markdown
+  350	| "These slices are feature-independent, so they're parallel-safe." | Parallel safety is about **write surface**, not feature independence. Declare `integration_surfaces` and run `tasktool surface check <phase-id>` before dispatching them together. |
+  351	| "I'll pick a sort slot / collection name / route slug freely." | **Reserve** it (`tasktool reserve add`) so siblings cannot collide; for project-global resources use `--scope project`. The tool refuses a duplicate allocation. |
+  352	| "We both need the CMS registry, so I'll just `parallel_group` them." | A shared surface needs a `coordination_group` (coordinate) or a `depends_on` (serialize), not a `parallel_group` — which asserts independence the slices do not have. |
+  353	```
+  354	
+  355	- [ ] **Step 4: Run test to verify it passes**
+  356	
+  357	Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py::test_tasklist_discipline_documents_surface_reserve_coordinate -q`
+  358	Expected: PASS.
+  359	
+  360	Also confirm the pre-existing tasklist-discipline tests still hold:
+  361	Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -k "tasklist_discipline or global_tasktool_shim" -q`
+  362	Expected: PASS (all).
+  363	
+  364	- [ ] **Step 5: Commit**
+  365	
+  366	```bash
+  367	git add skills/tasklist-discipline/SKILL.md \
+  368	        tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
+  369	git commit -m "P7.S6: document surface/reserve/coordinate in tasklist-discipline"
+  370	```
+  371	
+  372	---
+  373	
+  374	## Task 4: phase-planning & writing-plans — surface/reservation tables
+  375	
+  376	**Files:**
+  377	- Modify: `skills/phase-planning/SKILL.md`
+  378	- Modify: `skills/writing-plans/SKILL.md`
+  379	- Test: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`
+  380	
+  381	- [ ] **Step 1: Write the failing test**
+  382	
+  383	Append to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:
+  384	
+  385	```python
+  386	def test_phase_planning_and_writing_plans_document_surface_tables() -> None:
+  387	    for skill in ["phase-planning", "writing-plans"]:
+  388	        text = skill_text(skill)
+  389	        assert "surface/reservation table" in text, (
+  390	            f"{skill} must require a surface/reservation table"
+  391	        )
+  392	        assert "tasktool surface check <phase-id>" in text, (
+  393	            f"{skill} must tell the author to run surface check before ratifying"
+  394	        )
+  395	```
+  396	
+  397	- [ ] **Step 2: Run test to verify it fails**
+  398	
+  399	Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py::test_phase_planning_and_writing_plans_document_surface_tables -q`
+  400	Expected: FAIL — strings absent from both skills.
+  401	
+  402	- [ ] **Step 3a: phase-planning — add a declaration step in Phase Shaping**
+  403	
+  404	In `skills/phase-planning/SKILL.md`, in the `### Phase Shaping` numbered list, find step 6 (currently line 35):
+  405	
+  406	```markdown
+  407	6. Run `tasktool schedule <phase-id>` and include the output or a concise summary in the phase planning document.
+  408	```
+  409	
+  410	Replace it with these two steps (a new step 6 is inserted; the old step 6 becomes 7):
+  411	
+  412	```markdown
+  413	6. Declare each slice's write surfaces and scarce reservations: `tasktool surface add <slice-id> <surface>...` and `tasktool reserve add <slice-id> <resource>:<value> [--scope phase|project]`. **Before ratifying any `parallel_group`, run `tasktool surface check <phase-id>`** and resolve every unguarded surface overlap — add a `depends_on` to serialize, or a `coordination_group` to coordinate. A `parallel_group` must not contain slices that share an integration surface without one of those links.
+  414	7. Run `tasktool schedule <phase-id>` and include the output or a concise summary in the phase planning document.
+  415	```
+  416	
+  417	- [ ] **Step 3b: phase-planning — require the table in the document**
+  418	
+  419	In the same file, find the `The document must include:` bulleted list (currently lines 37–42). **Immediately after** the `- explicit notes on which dependencies must be ratified by slice spec/plan writers.` bullet, insert:
+  420	
+  421	```markdown
+  422	- a **surface/reservation table**: one row per prospective slice listing its `integration_surfaces`, `reservations` (`resource:value` + scope), and `coordination_group`.
+  423	```
+  424	
+  425	- [ ] **Step 3c: phase-planning — add a red-flag row**
+  426	
+  427	In the same file, find the `## Red Flags` table. After the last row (`"The first sketch is final."` row, line 68), append:
+  428	
+  429	```markdown
+  430	| "These slices are in different features, so I'll `parallel_group` them." | Parallel groups are about shared **write surface**, not feature boundaries. Declare `integration_surfaces` and run `tasktool surface check <phase-id>` before ratifying a parallel group. |
+  431	```
+  432	
+  433	- [ ] **Step 3d: writing-plans — add the surface/reservation requirement**
+  434	
+  435	In `skills/writing-plans/SKILL.md`, find the `**Scheduling ratification:**` paragraph (currently line 26). **Immediately after** that paragraph, insert this new paragraph:
+  436	
+  437	```markdown
+  438	**Integration surfaces & reservations:** A slice plan that may run in parallel with siblings must include a **surface/reservation table** — for this slice (and any sibling it could overlap), list `integration_surfaces`, `reservations` (`resource:value` + scope), and `coordination_group`. Declare them on the tracker with `tasktool surface add` / `tasktool reserve add` / `tasktool coordinate`, then run `tasktool surface check <phase-id>` before ratifying. Do not place slices that share a surface in the same `parallel_group` without a `depends_on` (serialize) or a `coordination_group` (coordinate). A duplicate scarce-resource allocation is refused at declaration time — pick a free value rather than `--force`, unless you genuinely intend a coordinated shared allocation and record the reason.
+  439	```
+  440	
+  441	- [ ] **Step 4: Run test to verify it passes**
+  442	
+  443	Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py::test_phase_planning_and_writing_plans_document_surface_tables -q`
+  444	Expected: PASS.
+  445	
+  446	Confirm the pre-existing writing-plans tests still hold:
+  447	Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -k "writing_plans or artifact_transactions" -q`
+  448	Expected: PASS (all).
+  449	
+  450	- [ ] **Step 5: Commit**
+  451	
+  452	```bash
+  453	git add skills/phase-planning/SKILL.md skills/writing-plans/SKILL.md \
+  454	        tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
+  455	git commit -m "P7.S6: require surface/reservation tables in phase-planning and writing-plans"
+  456	```
+  457	
+  458	---
+  459	
+  460	## Task 5: Full-suite verification
+  461	
+  462	**Files:**
+  463	- No source changes; verification only. (The slice was ratified at plan-settle; execution does not re-ratify or mutate the tracker here.)
+  464	
+  465	- [ ] **Step 1: Run the full docs-lifecycle test file**
+  466	
+  467	Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -q`
+  468	Expected: PASS — all pre-existing tests plus the 5 new functions (Task 1–4) green.
+  469	
+  470	- [ ] **Step 2: Run the full tasktool test suite**
+  471	
+  472	Run: `cd tools/tasktool && python -m pytest -q`
+  473	Expected: PASS — no regressions. (This slice changes no Python; the only new tests are the doc-content assertions above.)
+  474	
+  475	- [ ] **Step 3: Sanity-check the referenced commands exist**
+  476	
+  477	Run:
+  478	```bash
+  479	tasktool surface check --help
+  480	tasktool reserve add --help
+  481	tasktool coordinate --help
+  482	tasktool worktree status --help
+  483	```
+  484	Expected: each prints usage (no `invalid choice`), confirming the prose references real CLI surface shipped by P7.S2–S4.
+  485	
+  486	- [ ] **Step 4: Confirm the scheduling contract is intact (read-only)**
+  487	
+  488	Run: `tasktool show P7.S6`
+  489	Expected: `planning_status: ratified` (set at plan-settle), `depends_on: P7.S2, P7.S3, P7.S4`, no parallel group. This step is read-only — do **not** mutate or commit the tracker from the implementation worktree here; the ratification and its commit already happened in the planning session.
+  490	
+  491	---
+  492	
+  493	## Self-review notes (author checklist, already run)
+  494	
+  495	- **Spec coverage:** §4.F `subagent-driven-development` (surface check → Task 2 Step 3a; integrate-main checkpoint → Task 2 Steps 3b–3c; playbook → Task 1 + Task 2 Step 3d). §4.F `tasklist-discipline` (commands + vocabulary + coordination/parallel distinction + 3 red flags → Task 3). §4.F `phase-planning`/`writing-plans` (surface/reservation tables + `surface check` before ratify → Task 4). §6 `S6` testing line (docs lifecycle test extended; playbook file exists → Task 1 + the four new assertion functions). No §4.F item is unaddressed. (Plan ↔ tracker drift validation is **§4.G / P7.S7**, out of scope here.)
+  496	- **Dependency on P7.S5:** intentionally avoided — the integrate-main checkpoint documents `worktree sync` as "when available" plus a raw-git fallback, so S6 lands correctly whether or not S5 ships.
+  497	- **No placeholders:** every doc edit shows the exact insert/replace text; every test step shows the exact assertion and command.
+  498	- **String consistency:** each new test assertion's substring is reproduced verbatim in the corresponding skill edit (`tasktool surface check <phase-id>`, `Integrate-current-main checkpoint`, `references/registry-merge-playbook.md`, `surface/reservation table`, `cms-block-registry`, `feature independence`).
+  499	- **Regression guard:** Tasks 2–4 each re-run the relevant pre-existing assertions to prove the edits did not disturb `test_subagent_driven_development_starts_slice_before_dispatch`, the tasklist-discipline authority test, or the writing-plans start-step test.
+
+## Context Previews
+
+### docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md
+
+    1	# P7 — Integration-surface-aware parallel slice safety
+    2	
+    3	**Status:** design (spec)
+    4	**Date:** 2026-06-02
+    5	**Phase ID:** `P7`
+    6	
+    7	## 1. Problem
+    8	
+    9	`tasktool` decides whether slices may run in parallel from **declared feature
+   10	dependencies** (`Slice.depends_on`) and the `parallel_group` tag. Those answer
+   11	"does S4's feature need S3's feature first?" They do **not** answer the question
+   12	that actually governs safe parallel execution: **what shared write surface does
+   13	each slice mutate?**
+   14	
+   15	This gap produced a real failure in the `multistore` project, phase P20. Four
+   16	storefront-marketing slices (`P20.S2`–`P20.S5`) each declared a dependency only
+   17	on the bootstrap slice `P20.S1`, so `tasktool ready-slices`/`schedule` reported
+   18	them as independently executable. They were feature-distinct (slider, promo
+   19	bands, overlays, blog) but **integration-overlapping**: every one of them wrote
+   20	the same centralized CMS-block machinery — block contracts, parser allowlists,
+   21	Directus schema/seed files, renderer dispatch, theme CSS tails, and the homepage
+   22	ordering array.
+   23	
+   24	The observed consequences:
+   25	
+   26	1. **Conflict-bomb merges.** `P20.S4`'s merge conflicted across `page-renderer.tsx`,
+   27	   theme CSS, reviewer-request artifacts, `docs/tasklist.json`, Directus
+   28	   bootstrap/schema/seed files, content-contract schemas/types, and parser tests.
+   29	2. **Stale-base merges.** `P20.S4` was completed in a worktree that branched from
+   30	   `main` *before* `P20.S2`/`P20.S3` and their cleanup landed. The worktree
+   31	   snapshot was older than `main`, so the merge replayed churn that was already
+   32	   integrated.
+   33	3. **A real semantic collision, not just textual churn.** `P20.S3` and `P20.S4`
+   34	   independently chose homepage sort slot `15`. Nothing forced the second slice
+   35	   onto a free slot at planning time; the collision was discovered and resolved
+   36	   at merge.
+   37	4. **Merge-unsafe reviewer artifacts.** Generated reviewer-request files
+   38	   add/add-conflicted despite not being behavioral code.
+   39	
+   40	The root cause is **dependency modeling by feature intent rather than by
+   41	integration surface.** "Slider" and "promo bands" were non-dependent product
+   42	slices, but they both wrote the same registry, schema, seed arrays, ordering
+   43	slots, parser unions, and theme areas. The tool allowed parallel execution
+   44	because the declared dependencies were technically satisfied.
+   45	
+   46	## 2. Goals
+   47	
+   48	1. **Prevention.** Let planning declare, per slice, the **integration surfaces**
+   49	   it writes and the **scarce resources** it allocates. `tasktool` warns when
+   50	   sibling ready/in-progress slices share a surface with no dependency or
+   51	   coordination link, and *refuses* a duplicate scarce-resource allocation.
+   52	2. **Recovery.** When a sibling slice has landed on the base branch since a
+   53	   slice's worktree branched, surface that fact reliably and provide a
+   54	   conservative "integrate current main" path before the post-slice review/merge,
+   55	   plus a documented centralized-registry merge playbook.
+   56	3. **Merge-safe reviewer artifacts.** Generated reviewer-request files must never
+   57	   add/add-conflict between sibling worktrees.
+   58	4. **Plan ↔ tracker coherence.** Declared surfaces/reservations must be reflected
+   59	   in planning artifacts so the plan and the tracker cannot silently diverge.
+   60	
+   61	## 3. Non-goals (explicit)
+   62	
+   63	- **Directus-specific verifier diagnostics and stale-token handling.** These were
+   64	  real `multistore` pain points (a stale `DIRECTUS_ADMIN_TOKEN` shadowing valid
+   65	  admin credentials made a non-code problem look like a schema failure), but they
+   66	  are project-specific. Superstar core is general-purpose and zero-dependency;
+   67	  Directus tooling belongs in the `multistore` project, not here.
+   68	- **Automatic merge-conflict resolution.** The tooling detects and routes; it does
+   69	  not auto-merge semantic conflicts.
+   70	- **Path-glob surface *inference* as the primary model.** Explicit declaration is
+   71	  the source of truth. A path-glob comparison survives only as a deferred,
+   72	  warning-only post-implementation *audit* (§4.G), never as the planning model.
+   73	- **A "touches existing resource" reservation kind.** Reservations model scarce
+   74	  *allocations* (claiming a new value). Modifying a shared existing resource is a
+   75	  *surface/coordination* concern, not an allocation, so maintenance work is not
+   76	  falsely blocked. A future "touches-existing" field is noted, not built here.
+   77	- **`worktree sync` as an unconditional command.** Detection ships first; the
+   78	  mutating sync command is gated behind strict preconditions and is the explicit
+   79	  deferral candidate if scope tightens.
+   80	
+   81	## 4. Design
+   82	
+   83	### 4.A Data model (`model.py`, schema `v2 → v3`; `migrate.py`)
+   84	
+   85	Add to `Slice`:
+   86	
+   87	- `integration_surfaces: list[str]` — conventional surface tags naming shared
[truncated: 556 additional lines]


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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s6-skill-changes-subagent-driven

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md

Additional context files:
- docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md
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

### docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md

    1	# P7.S6 — Skill changes for integration-surface-aware parallel safety: Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Teach the workflow skills the integration-surface model shipped in P7.S2–S4 so coordinators declare surfaces/reservations, run `surface check` before parallel dispatch, and integrate current `main` before each post-slice review.
    6	
    7	**Architecture:** Pure documentation slice. It edits four `SKILL.md` files and adds one reference file, and is guarded by string-assertion tests in the existing docs-lifecycle test (`tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`). No tasktool Python behaviour changes — the CLI surface (`surface`/`reserve`/`coordinate`/`surface check`/`worktree status --integration`) already exists. TDD here means: add a failing doc-content assertion, run it red, edit the skill prose to make it green, commit.
    8	
    9	**Tech Stack:** Markdown skill files under `skills/`; pytest doc-content assertions under `tools/tasktool/tests/`.
   10	
   11	---
   12	
   13	## Spec reference
   14	
   15	This slice implements **§4.F** of the P7 spec (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md`) and its testing line in **§6 (`S6`)**: *"docs lifecycle test extended to assert the new commands and the integrate-main checkpoint are documented; playbook file exists."*
   16	
   17	§4.F deliverables:
   18	- **`subagent-driven-development`** — (1) run `tasktool surface check <phase-id>` after `ready-slices` and do not parallel-dispatch surface-sharing slices without a `depends_on` or `coordination_group`; (2) an *integrate-current-main* checkpoint before `external-review --kind post-slice`; (3) a new `references/registry-merge-playbook.md`.
   19	- **`tasklist-discipline`** — document `surface`/`reserve`/`coordinate` in the conceptual model and daily-commands list; the recommended surface vocabulary; the `coordination_group` vs `parallel_group` distinction; three new red-flag rows.
   20	- **`phase-planning` / `writing-plans`** — declare surfaces/reservations when proposing parallel groups, emit a **surface/reservation table** in the plan, and run `tasktool surface check <phase-id>` before ratifying parallel groups.
   21	
   22	## Scheduling contract (confirmed before drafting)
   23	
   24	- `tasktool show P7.S6`: status `ready`, `depends_on = [P7.S2, P7.S3, P7.S4]` (all `done`), no `parallel_group`, `planning_status = proposed`.
   25	- `tasktool ready-slices P7` lists `P7.S6` as ready.
   26	- No dependency change is needed. This plan **does not** depend on P7.S5 (`worktree sync`); the integrate-current-main checkpoint therefore documents `worktree sync` as the preferred path *when available* plus a raw-git fallback, exactly as §4.F specifies.
   27	- The slice is ratified at **plan-settle** — in this planning session, immediately after the plan review passes — with `tasktool ratify P7.S6` (keeps `depends_on = [P7.S2, P7.S3, P7.S4]`, adds no parallel group). Execution does **not** re-ratify; by the time Task 0 runs, `planning_status` is already `ratified` and committed.
   28	
   29	## File Structure
   30	
   31	| File | Responsibility | Action |
   32	|------|----------------|--------|
   33	| `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` | Doc-content regression for all workflow skills | **Modify** — add 5 assertion functions |
   34	| `skills/subagent-driven-development/references/registry-merge-playbook.md` | Centralized-registry merge recipe referenced from the integrate-main checkpoint | **Create** |
   35	| `skills/subagent-driven-development/SKILL.md` | Coordinator orchestration loop | **Modify** — surface check before dispatch, integrate-main checkpoint, playbook reference |
   36	| `skills/tasklist-discipline/SKILL.md` | tasktool CLI surface + conceptual model | **Modify** — conceptual model paragraph, daily-commands block, 3 red-flag rows |
   37	| `skills/phase-planning/SKILL.md` | Phase shaping + scheduling graph | **Modify** — declaration step, surface/reservation table requirement, red flag |
   38	| `skills/writing-plans/SKILL.md` | Slice plan authoring | **Modify** — surface/reservation table requirement in scheduling ratification |
   39	
   40	The five test functions are split one-per-skill-area so each implementation task has a dedicated red→green pair.
   41	
   42	---
   43	
   44	## Task 0: Start the slice
   45	
   46	**Files:**
   47	- No source changes; lifecycle only.
   48	
   49	This is the mandatory first execution step from `[[writing-plans]]`: record the slice lifecycle start (and the worktree base SHA) before editing any files. The row is already `ratified` from the planning session — Task 0 only moves it to `in_progress`.
   50	
   51	- [ ] **Step 1: Verify you are in the slice's isolated worktree**
   52	
   53	Run: `git status --short`
   54	Expected: a clean tree (no unrelated dirty files). If this is a shared `main`/`master` checkout and the human partner has not opted out of isolation, stop and create the slice worktree via `[[using-git-worktrees]]` first.
   55	
   56	- [ ] **Step 2: Start the slice**
   57	
   58	Run: `tasktool start P7.S6`
   59	Expected: the row moves to `in_progress` and the worktree base SHA is recorded.
   60	
   61	- [ ] **Step 3: Confirm the lifecycle state**
   62	
   63	Run: `tasktool show P7.S6`
   64	Expected: `status: in_progress`, `planning_status: ratified`, `depends_on: P7.S2, P7.S3, P7.S4`.
   65	
   66	---
   67	
   68	## Task 1: Registry merge playbook reference file
   69	
   70	**Files:**
   71	- Create: `skills/subagent-driven-development/references/registry-merge-playbook.md`
   72	- Test: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`
   73	
   74	- [ ] **Step 1: Write the failing test**
   75	
   76	Append to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:
   77	
   78	```python
   79	def test_registry_merge_playbook_exists() -> None:
   80	    playbook = (
   81	        ROOT
   82	        / "skills"
   83	        / "subagent-driven-development"
   84	        / "references"
   85	        / "registry-merge-playbook.md"
   86	    )
   87	    assert playbook.is_file(), f"registry merge playbook must exist at {playbook}"
   88	    body = playbook.read_text(encoding="utf-8")
   89	    # The playbook's load-bearing instructions.
   90	    assert "preserve both" in body.lower()
   91	    assert "regenerate" in body.lower()
   92	    assert "rerun" in body.lower()
   93	```
   94	
   95	- [ ] **Step 2: Run test to verify it fails**
   96	
   97	Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py::test_registry_merge_playbook_exists -q`
   98	Expected: FAIL — `AssertionError: registry merge playbook must exist at …` (file does not exist yet).
   99	
  100	- [ ] **Step 3: Create the playbook file**
  101	
  102	Create `skills/subagent-driven-development/references/registry-merge-playbook.md` with this exact content:
  103	
  104	```markdown
  105	# Centralized-registry merge playbook
  106	
  107	Use this when a slice's worktree must integrate the current base branch and a
  108	**coordinated sibling slice has already landed on a shared integration surface**
  109	— a central registry, a parser allowlist/union, a schema or seed file, a renderer
  110	dispatch table, a theme CSS tail, or a homepage/ordering array. These surfaces
  111	collect *additive* entries from multiple slices, so a textual merge that keeps
  112	only one side silently drops a sibling's feature.
  113	
  114	This is invoked from the **integrate-current-main checkpoint** in
  115	`[[subagent-driven-development]]`, before the post-slice external review.
  116	
  117	## Rule: preserve both semantic additions
  118	
  119	When base and your worktree both added to the same registry/array/union, the
  120	merge result must contain **both** additions, not whichever side won the textual
  121	conflict. Read both sides and reconstruct the union by hand:
  122	
  123	1. **Identify the surface and the additions.** For each conflicting hunk, name
  124	   what each side added (a block contract, a parser case, a schema/seed row, a
  125	   dispatch entry, a CSS block, an ordering slot).
  126	2. **Keep both additions.** Reassemble the registry/array/union so every sibling's
  127	   entry survives. If two siblings added entries that must be ordered, apply the
  128	   declared ordering; if they collide on a scarce slot (e.g. two `homepage-sort:15`),
  129	   that is a reservation collision that should have been caught by `tasktool reserve
  130	   add` — resolve it now by moving one side to a free value and recording why.
  131	3. **Do not invent a merge the tool can do.** This playbook resolves *semantic*
  132	   additive conflicts only. It does not auto-resolve genuine logic conflicts —
  133	   escalate those.
  134	
  135	## Rule: regenerate derived artifacts
  136	
  137	Any file derived from the surface must be regenerated *after* the union is
  138	correct, never hand-merged:
  139	
  140	- checksums / lockfiles / content hashes,
  141	- snapshot fixtures,
  142	- generated types or generated indexes.
  143	
  144	A hand-merged checksum is a lie; regenerate it from the merged source.
  145	
  146	## Rule: rerun focused tests, then integrated verification
  147	
  148	1. Rerun the **focused** parser / schema / seed tests for the surface you merged.
  149	2. Then rerun the slice's **full** verification command, so the integrated tree
  150	   (your work + the landed sibling) is proven green before the post-slice review.

[truncated: 349 additional lines]

<!-- superstar-prompt:end -->