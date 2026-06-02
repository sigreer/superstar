<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 2 of p7-s1-data-model-migration-P7-S1-post-slice.

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
| 1 | revise | 1 | 0 |

## Prior-round findings

Source: merged findings from r1 (authoritative)

# Merged findings for r1

## Primary

# Review — 2026-06-02-P7-S1-data-model-migration.md (post-slice, round 1)

- Target: `docs/plans/2026-06-02-P7-S1-data-model-migration.md`
- Request: `docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/r1-2026-06-02T2356-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1. Severity: important — Slice lifecycle evidence is not reflected in the tracker. The plan requires `tasktool start P7.S1` before source edits, expecting the slice to be marked `in_progress` and tied to the implementation worktree (`docs/plans/2026-06-02-P7-S1-data-model-migration.md:52-56`). The checked-in tracker still has `started: null` and `status: "ready"` for `P7.S1` (`docs/tasklist.json:271-272`), and its refs/reviewer chain still point only at the plan review (`docs/tasklist.json:265-270`). For a post-slice completion gate, this leaves the lifecycle state inconsistent with the completed implementation.

2. Open questions / assumptions

I assume the reviewed `docs/tasklist.json` is the intended tracker state for this worktree. If authoritative-checkout routing updated a different checkout, that state needs to be reconciled or attached as evidence before closeout.

3. Suggested document edits

Update/register the slice lifecycle evidence through `tasktool` so `P7.S1` no longer appears unstarted in the tracker. After this post-slice round is recorded, add the post-slice reviewer chain ref as the closeout evidence.

4. Verification gaps / commands that should be run, if any

I ran:
- `python -m pytest tools/tasktool/tests/test_model.py tools/tasktool/tests/test_serialize.py tools/tasktool/tests/test_migrate.py tools/tasktool/tests/test_v1_compat.py tools/tasktool/tests/test_schema_gen.py -q` — 105 passed
- `python -m pytest tools/tasktool/tests -q` — 700 passed
- `python -m pytest -q` — 992 passed
- `tasktool validate` — ok
- `rg -n "schema_version.*2|SCHEMA_VERSION == 2|const.*2" tools/tasktool/tests` — only raw v2 fixtures

Code acceptance looks satisfied; the remaining blocker is tracker/lifecycle evidence consistency.

Overall verdict: revise


## Sweep 1

# Review — 2026-06-02-P7-S1-data-model-migration.md (post-slice, round 1)

- Target: `docs/plans/2026-06-02-P7-S1-data-model-migration.md`
- Request: `docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/r1-2026-06-02T2356-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

S1.F1. Severity: blocking — The slice lifecycle state does not support a post-slice completion gate. The plan requires `tasktool start P7.S1` before source edits and expects the slice to be marked `in_progress` with worktree evidence (`docs/plans/2026-06-02-P7-S1-data-model-migration.md:52-56`). The tracker still shows `P7.S1` with `started: null`, `closed: null`, and `status: "ready"` (`docs/tasklist.json:257`, `docs/tasklist.json:271-272`). This makes the completed implementation commits inconsistent with the authoritative slice row.

S1.F2. Severity: blocking — The post-slice reviewer chain is not recorded as closeout evidence. `docs/tasklist.json` still points `reviewer_chain` at the plan review and refs only include the plan/handoff/plan-review paths (`docs/tasklist.json:265-270`). The post-slice chain file exists, but has `"rounds": []` and pending checkpoints (`docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/chain.json:8-11`), and the entire post-slice reviewer directory is untracked in `git status`. `tasktool close P7.S1` will not have durable post-slice evidence to satisfy the gate.

2. Open questions / assumptions

I assume this worktree’s `docs/tasklist.json` is the repo state being reviewed. If authoritative-checkout routing updated another checkout, that state needs to be reconciled into this branch or provided as explicit evidence.

3. Suggested document edits

No implementation-plan rewrite is needed. The code and tests satisfy the functional acceptance criteria I checked. The required edits are closeout/evidence updates: run the proper lifecycle/registration path so `P7.S1` no longer appears unstarted, and register/commit the post-slice reviewer chain evidence before close.

4. Verification gaps / commands that should be run, if any

I ran:

- `python -m pytest tools/tasktool/tests/test_model.py tools/tasktool/tests/test_serialize.py tools/tasktool/tests/test_migrate.py tools/tasktool/tests/test_v1_compat.py tools/tasktool/tests/test_schema_gen.py -q` — 105 passed
- `python -m pytest tools/tasktool/tests -q` — 700 passed
- `python -m pytest -q` — 992 passed
- `tasktool validate` — ok
- `rg -n "schema_version.*2|SCHEMA_VERSION == 2|const.*2" tools/tasktool/tests` — only raw v2 fixture inputs
- `git diff --name-only d54b9bb..HEAD | rg '^plugins/superstar/tools/tasktool/' || true` — no plugin-copy edits

The only remaining gaps are lifecycle/tracker/reviewer-chain durability, not code behavior.

Overall verdict: revise



## Resolution report for prior round

# Resolution for r1

## F1
Status: fixed
Evidence:
- Commit: f44bda5d614fd2e5d429ccf30fefe510aaddb3ce
- Files: `docs/tasklist.json`
- Verification: `tasktool brief P7.S1` now shows status=in_progress, started=2026-06-02, worktree recorded
Notes:
Root cause: `tasktool start P7.S1` ran on the authoritative main checkout; this worktree branched before that tracker commit and carried a stale copy. Integrated current main into the worktree branch (integrate-current-main checkpoint), reconciling the lifecycle state. Code was already certified acceptable by both reviewers.

## S1.F1
Status: fixed
Evidence:
- Commit: f44bda5d614fd2e5d429ccf30fefe510aaddb3ce
- Files: `docs/tasklist.json`
- Verification: `tasktool brief P7.S1` -> in_progress with worktree evidence
Notes:
Same root cause and fix as F1 (the sweep reviewer raised the identical lifecycle inconsistency at blocking severity).

## S1.F2
Status: fixed
Evidence:
- Commit: b0162ad47d987efbe8f45e970d6ddcf1939ddd0c
- Files: `docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/`
- Verification: `git ls-files docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/` lists the committed r1 chain
Notes:
The post-slice reviewer chain (r1 request/response, merged-findings, chain.json) is now committed as durable closeout evidence. The `tasktool close P7.S1` step (run by the coordinator after the next review round passes) will register the chain ref on the slice row.


## Changes since prior round

Worktree status: clean

### git diff base..HEAD

diff --git a/docs/notes/2026-06-02-P7-S8-reviewer-artifact-investigation-decision.md b/docs/notes/2026-06-02-P7-S8-reviewer-artifact-investigation-decision.md
new file mode 100644
index 0000000..4277871
--- /dev/null
+++ b/docs/notes/2026-06-02-P7-S8-reviewer-artifact-investigation-decision.md
@@ -0,0 +1,103 @@
+# P7.S8 Investigation Decision — Reviewer-Artifact Collision
+
+## VERDICT: DOES-NOT-REPRODUCE (Branch B)
+
+The P20 post-mortem claimed that generated external-reviewer **request files**
+(`docs/reviewer/.../rN-...-request.md`) add/add-conflict between sibling git
+worktrees developed in parallel and later merged. Reproduced against the CURRENT
+bridge (`skills/external-review/scripts/external-reviewer.py`), this claim is
+**refuted** for the documented workflow. Collisions only occur when an operator
+violates the per-slice `--work-id` contract (two siblings passing the *same*
+work-id), which the keying scheme is explicitly designed to prevent, or in a
+synthetic post-phase scenario the workflow never produces (two independent
+post-phase reviews of one file).
+
+## Confirmed line numbers (current bridge)
+
+- `chain_folder_name` — **lines 727-733**. For kind ∈ {post-slice, post-phase}
+  with non-empty `work_id` → folder `f"{base}-{work_id_slug}-{kind}"`
+  (dots in work_id replaced by `-`); else `f"{base}-{kind}"`. For **post-phase**
+  the work_id is a *phase* id (same for all sibling slices).
+- `run_one_reviewer` request path — **lines 1406-1407**:
+  `basename = f"r{round_num}-{timestamp}{suffix}"`;
+  `request_path = chain_dir / f"{basename}-request.md"`. `suffix` is
+  `-primary`/`-sweepN` only when namespaced (1403-1405).
+- `next_round_number` — **lines 777-783** (per-chain; manifest rounds count or
+  glob of `r*-*-request.md`).
+- `timestamp` — **line 2575**, minute resolution `%Y-%m-%dT%H%M`.
+- `main()` chain-dir resolution — **lines 2460-2473** (`new_slug` from
+  `chain_folder_name`; legacy discovery; `chain_dir = existing or reviewer_root/new_slug`).
+- `--work-id` guard — **lines 2439-2445** (post-slice/post-phase require
+  `--work-id`, else exit 2).
+- work-id-mismatch refusal — **lines 2510-2527** (stored manifest `work_id`
+  is source of truth; mismatch → exit 6).
+- response/scratch layout — **lines 1499-1503**, all under `chain_dir`
+  (`.reviewer-output/rN-<role>` + tempdir scratch).
+- `tools/tasktool/artifacts.py` `add_artifact_to_item` — **lines 150-156**
+  writes `reviewer_chain`/`phase_reviewer_chain` onto the tasklist row. This is
+  the **only** tasklist touch (Class B, out of scope).
+
+## Existing test coverage
+
+`test_chain_folder_name.py` and `test_work_id.py` only assert folder-name shape
+and the work-id guard in isolation. **No existing test exercises two sibling
+slices producing non-colliding request paths.**
+
+## Probe outputs (verbatim)
+
+### Probe 1 — distinct work-ids (normal workflow)
+```
+sibling A request paths: {'docs/reviewer/feature-plan-P2-S3-post-slice/r1-2026-06-02T2315-request.md'}
+sibling B request paths: {'docs/reviewer/feature-plan-P2-S4-post-slice/r1-2026-06-02T2315-request.md'}
+COLLISION: False (none)
+```
+
+### Probe 2 — same work-id, two fresh worktrees (operator misuse)
+```
+wtA: {'docs/reviewer/feature-plan-P2-S3-post-slice/r1-2026-06-02T2315-request.md'}
+wtB: {'docs/reviewer/feature-plan-P2-S3-post-slice/r1-2026-06-02T2315-request.md'}
+CROSS-WORKTREE COLLISION (same work-id): True {'docs/reviewer/feature-plan-P2-S3-post-slice/r1-2026-06-02T2315-request.md'}
+```
+
+### Probe 3 — post-phase, two slices, same phase id, same file
+```
+wtA: {'docs/reviewer/feature-plan-P2-post-phase/r1-2026-06-02T2316-request.md'}
+wtB: {'docs/reviewer/feature-plan-P2-post-phase/r1-2026-06-02T2316-request.md'}
+POST-PHASE COLLISION (same phase id): True {'docs/reviewer/feature-plan-P2-post-phase/r1-2026-06-02T2316-request.md'}
+```
+
+## Reasoning (Decision gate)
+
+REPRODUCES requires BOTH (1) two distinct sibling invocations writing an
+identical relative `*-request.md` path, AND (2) that pattern being reachable in
+the documented workflow WITHOUT an operator violating the work-id contract.
+
+- **Probe 1** is the normal workflow: each post-slice review passes its own slice
+  id (P2.S3 vs P2.S4). The chain folder is keyed by `work_id_slug`
+  (lines 730-732), so the folders diverge and the request paths cannot collide
+  regardless of identical timestamp/round. → No collision.
+- **Probe 2** collides, but ONLY because both worktrees pass the *same* work-id
+  `P2.S3`. That is an operator error — a violation of the per-slice work-id
+  contract the keying is built to prevent. Within a worktree the mismatch
+  refusal (lines 2510-2527) would catch reuse of a chain for a different slice;
+  across fresh worktrees there is no shared manifest to compare against, so the
+  only remaining trigger is two same-minute starts with an identical (wrong)
+  work-id. Not workflow-reachable.
+- **Probe 3** collides synthetically, but the workflow produces **exactly one**
+  post-phase review per phase (one phase → one post-phase gate on one file).
+  Two independent post-phase reviews of the same file never coexist, so even
+  though the paths *would* collide, the scenario is unreachable.
+
+Neither reachable scenario produces a collision; the only collisions require an
+operator violating the work-id contract or a workflow state that never occurs.
+→ **DOES-NOT-REPRODUCE.**
+
+## Residual (Class B — out of scope, owned by P7.S6 / spec §4.F)
+
+A real residual conflict remains in **`docs/tasklist.json`**: when two sibling
+slices both stamp `reviewer_chain` / `phase_reviewer_chain` on close
+(`artifacts.py` lines 150-156), the JSON row churns and can merge-conflict. This
+is **close-churn on the tasklist**, NOT a reviewer-artifact-naming problem, and
+is owned by P7.S6 / spec §4.F. It must NOT be "fixed" by renaming request files.
+
+`external-reviewer.py` was NOT modified.
diff --git a/docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/.reviewer-output/r1-primary/codex-events.jsonl b/docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/.reviewer-output/r1-primary/codex-events.jsonl
new file mode 100644
index 0000000..2c10746
--- /dev/null
+++ b/docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/.reviewer-output/r1-primary/codex-events.jsonl
@@ -0,0 +1,70 @@
+{"type":"thread.started","thread_id":"019e8a8d-5bf6-74e1-acac-9b02e7614cf5"}
+{"type":"turn.started"}
+{"type":"item.completed","item":{"id":"item_0","type":"agent_message","text":"Using `superstar:tasklist-discipline` for the tracker-aware review context, then I’ll read the target files and repo state directly before writing findings."}}
+{"type":"item.started","item":{"id":"item_1","type":"command_execution","command":"/usr/bin/zsh -lc \"sed -n '1,220p' /home/simon/.codex/plugins/cache/superstar-dev/superstar/6.8.5/skills/tasklist-discipline/SKILL.md && rg -n \\\"P7|data model|schema v3|reservations_ledger\\\" /home/simon/.codex/memories/MEMORY.md\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_1","type":"command_execution","command":"/usr/bin/zsh -lc \"sed -n '1,220p' /home/simon/.codex/plugins/cache/superstar-dev/superstar/6.8.5/skills/tasklist-discipline/SKILL.md && rg -n \\\"P7|data model|schema v3|reservations_ledger\\\" /home/simon/.codex/memories/MEMORY.md\"","aggregated_output":"---\nname: tasklist-discipline\ndescription: Use whenever planning, closing slices/phases, or referencing work items in a project that uses docs/tasklist.json. Teaches the tasktool CLI surface and the gating concepts; the CLI enforces the rules.\n---\n\n# TASKLIST Discipline\n\nA `docs/tasklist.json` file is the canonical, top-level tracker for the project. It groups work into **phases**, **slices**, **tasks**, and **cross-cutting** items, each with a stable, never-renumbered ID. All mutations flow through `tasktool`; a pre-commit hook refuses non-canonical bytes, orphaned spec/plan filenames, and any commit that touches the legacy `docs/TASKLIST.md`.\n\nUse the global `tasktool` shim installed by `bash <active-superstar-checkout>/tools/tasktool/install.sh`. If `tasktool` is missing or reports a shim/source version mismatch, reinstall that shim from the active Superstar checkout before continuing.\n\n`.tasktool/config.json` must set `tasklist.mutation_mode` to `authoritative-checkout` for normal superstar work. Mutating commands route through the configured authoritative checkout instead of editing the local worktree's `docs/tasklist.json` directly. Treat that routing as the source of truth: run `tasktool` from the implementation worktree, let the tool acquire the shared lock and update the authoritative checkout, then continue from the same implementation worktree. If a mutating command reports that no authoritative-checkout routing is configured, stop and run `tasktool config init-authority --branch <main-branch>` from the authoritative checkout before retrying; use `tasktool config init-local` only for explicit local-only test fixtures or non-workflow throwaway repos.\n\n**Announce at start:** \"I'm using the tasklist-discipline skill to update docs/tasklist.json via tasktool.\"\n\n## When to use\n\n- About to plan or write a new spec → allocate an ID with `tasktool create phase|slice|task|cross …` **before** the spec file lands. The TASKLIST row is the allocation; the spec/plan/reviewer-chain filenames are downstream.\n- About to start implementation for a slice → `tasktool start <slice-id>`. This records the lifecycle start and moves the row to `in_progress`; do this before dispatching implementation or editing implementation files.\n- About to close a slice → `tasktool close <slice-id>`. The CLI enforces the post-slice external-review gate.\n- About to close a phase → `tasktool archive-phase <phase-id>`. For `done` phases the CLI enforces the post-phase gate and writes the archive note; for `cancelled` phases it archives without a post-phase review because nothing shipped.\n- About to close a cross-cutting item → `tasktool close <x-id>`. The CLI marks it done and archives it by default. Use `--no-archive` only when the closed X-item must remain visible temporarily; later run `tasktool archive-cross <x-id>`.\n- Entering a slice → `tasktool brief <slice-id>` instead of reading the JSON.\n- Onboarding a project — `[[project-setup]]` runs `tasktool init` and installs the hook.\n\nOnboarding has a hard setup boundary: after `[[project-setup]]` configures `.tasktool/config.json` with authoritative routing, creates or imports `docs/tasklist.json`, installs hooks, installs the global `external-reviewer` shim or replaces a legacy repo-local reviewer bridge with the compatibility shim, moves legacy `docs/superpowers/` files, or edits `CLAUDE.md` / `AGENTS.md`, that setup/migration must be committed, stashed, or explicitly paused before implementation work begins.\n\n**Implementation isolation boundary:** If tasklist work is tied to starting, continuing, reviewing, or closing an implementation slice, invoke `[[using-git-worktrees]]` before tasktool status/ref/note/close mutations for an active implementation slice. `tasktool start`, `tasktool set`, `tasktool ref`, `tasktool note`, `tasktool close`, and reviewer-chain registration are not harmless bookkeeping when run from a shared checkout: they dirty the slice evidence set. A normal `main`/`master` checkout is planning/setup/read-only by default unless the user explicitly opts out of isolation in the current turn. Invoke `tasktool` from the active implementation worktree; authoritative routing sends the mutation to the configured checkout.\n\n**Administrative closeout exception:** Pure lifecycle bookkeeping for already-superseded planning rows may run from the authoritative checkout without creating a new implementation worktree. Examples: `tasktool cancel <phase-id> --cascade --reason \"…\"`, `tasktool archive-phase <phase-id>` on that cancelled phase, or adding refs/notes that explain the cancellation. Do not use this exception to edit implementation files, close shipped slices, register reviewer evidence for active implementation work, or mix new product changes into the bookkeeping commit.\n\n**Subagent rule (load-bearing).** Parents create or adopt worktrees via `tasktool start <slice-id>`. Dispatched subagents inherit the parent's cwd and **must not** call `tasktool start` — implementation work happens inside the parent's already-recorded worktree, and a subagent starting a slice double-counts the lifecycle row and corrupts the slice's worktree fields. Tasktool refuses `tasktool start` when it observes a dispatched-subagent signal (`SUPERSTAR_SUBAGENT_ROLE`, `CLAUDE_AGENT_ROLE`, or the test-only `SUPERSTAR_FORCE_SUBAGENT=1`). The runtime guard is detection-dependent — a coordinator that loses its env (e.g. `env -i`) will look like a top-level invocation — so **this prose rule is the load-bearing guard**; the env signals are belt-and-braces.\n\n## Conceptual model\n\n| Scope | Short form | Fully-qualified |\n|-------|-----------|-----------------|\n| Phase | `P2` | `P2` |\n| Slice | `S1` (follow-up: `S5a`) | `P2.S1` (`P2.S5a`) |\n| Task | `T3` | `P2.S5.T3` |\n| Cross-cutting | `X4` | `X4` (top-level; not nested under a phase) |\n\nIDs are assigned at birth and **never renumbered**. The `tasktool create` family does orphan-aware allocation (`max+1` across `docs/tasklist.json`, `docs/specs/`, `docs/plans/`, `docs/reviewer/`) and prints the new ID.\nArchived X IDs are still reserved, so a new cross-cutting item will not reuse an ID that has moved to `archived_cross_cutting`.\nCommands run against an archived X-id report a may-already-be-archived hint because archive files are evidence, not part of the active tasklist workflow surface.\n\nStatus enum: `ready | in_progress | blocked | done | cancelled`. Only slices may take `blocked`. `cancelled` is a terminal status (peer of `done`) recording work that was intentionally not shipped — cancelled, deferred, abandoned, superseded. It is set only via `tasktool cancel <id> --reason \"…\"`; the `set` verb does not accept it. Tasks cannot be `cancelled`; cancel the parent slice instead.\n\n`blocked` is only set via `tasktool block <slice-id> --on …`. Emoji are a render concern; `tasktool render` and `tasktool brief` handle that. `tasktool start <slice-id>` is the normal way to enter `in_progress`; `tasktool set <id> --status in_progress` is a compatibility alias for older plans and ad-hoc rows. `tasktool unblock <slice-id> --resume` resumes through the same lifecycle path and stamps `started` when needed. `done` requires `closed`; the CLI stamps it.\n\nPhase planning uses separate scheduling metadata. `planning_path` points at the phase-scoped planning/design document. `depends_on` records planned slice sequencing; it is not the same as runtime `blocked_on`. `planning_status` is `proposed | ratified | superseded`, and `parallel_group` names slices intended to be planned or executed together.\n\n## Daily commands\n\n```sh\ntasktool brief <id>            # start-of-work primer for slice or phase\ntasktool show <id>             # full detail\ntasktool list --open           # everything ready / in_progress / blocked\ntasktool create slice <phase-id> --title \"...\"\ntasktool prepare existing <id> --plan path/to/plan.md\ntasktool artifact add <id> --kind spec --path path/to/spec.md\ntasktool artifact status <id> --strict\ntasktool artifact commit <id> --message \"...\"\ntasktool start <slice-id>      # lifecycle start + in_progress\ntasktool set <id> --status in_progress  # compatibility alias\ntasktool note <id> --append \"...\"\ntasktool ref <id> --add path/to/artifact\ntasktool block <slice-id> --on P2.S5\ntasktool deps <slice-id> --add P2.S1\ntasktool ratify <slice-id> --parallel-group bootstrap\ntasktool schedule <phase-id>\ntasktool ready-slices <phase-id>\ntasktool phase-status\ntasktool close <slice-id>      # enforces post-slice review gate\ntasktool close <x-id>          # closes and archives cross-cutting by default\ntasktool close <x-id> --no-archive\ntasktool cancel <id> --reason \"<text>\"           # terminate without shipping\ntasktool cancel <phase-id> --reason \"...\" --cascade  # cancel a phase + its open slices\ntasktool cancel <x-id> --reason \"...\" --no-archive   # keep cancelled X visible\ntasktool archive-cross <x-id>  # archive a done visible cross-cutting item\ntasktool archive-phase <phase-id>  # done phases require post-phase review; cancelled phases bypass it\ntasktool validate              # full validation\n```\n\nRun `tasktool --help` (or `tasktool <cmd> --help`) for the full surface.\n\n## Gating concepts (why the CLI refuses you)\n\n- **Post-slice external review.** `tasktool close <slice-id>` reads `chain.json` from the slice's reviewer chain folder (`docs/reviewer/<slug>-post-slice/` by default; override with `--reviewer-chain`). It refuses unless the latest round's verdict ∈ {`ready`, `ready with small edits`}. Per-task internal reviews do not satisfy this gate.\n- **Post-phase external review.** `tasktool archive-phase <phase-id>` refuses until every slice is `done` *and* the phase's post-phase chain returns `ready` / `ready with small edits`. If the phase itself is `cancelled`, archive still requires every child slice to be terminal, but it bypasses the post-phase chain because cancelled work never shipped.\n- **Cross-cutting archive.** `tasktool close <x-id>` is ungated by external review and moves the completed X-item out of active `cross_cutting` into `archived_cross_cutting`, with a lossless markdown archive under `docs/archived-tasks/`. `--no-archive` leaves it visible as `done`; `tasktool archive-cross <x-id>` moves it later without sending another done notification.\n- **`--skip-review-gate`** exists for emergencies and is recorded in the slice/phase `notes` with a timestamp. Use it only when the operator has explicitly chosen to bypass.\n\nSee `[[external-review]]` for how to drive the reviewer.\n\n## Cancellation\n\n- `tasktool cancel <id> --reason \"<text>\"` is the only sanctioned path. Applies to phases, slices, and cross-cutting items. Tasks cannot be cancelled — cancel the parent slice.\n- The reason is required and is recorded in `notes` as `Cancelled <ISO-ts>: <reason>` (and `(cascaded from <phase-id>)` for child slices cancelled via `--cascade`).\n- Cancellation **bypasses** the post-slice and post-phase external-review gates — cancelled work never shipped. A cancelled phase may be archived with `tasktool archive-phase <phase-id>` without `--skip-review-gate` or a post-phase reviewer chain.\n- A cancelled slice does **not** satisfy a downstream `depends_on`. `tasktool schedule <phase-id>` emits `cancelled_deps` for affected slices; `ready-slices` omits them. Cancel the downstream too or remove the dependency.\n- Cancelled cross-cutting items auto-archive by default. Use `--no-archive` to keep the cancelled row visible in the active list; archive later with `archive-cross`.\n- Phase cancellation refuses if any slice is still open. Use `--cascade` to cancel open slices in one call; already-done slices are never touched.\n- Edits on cancelled rows: `note --append`, `ref`, and `title` are allowed (post-mortem context); `set`, `close`, `start`, `block`, `unblock`, `deps`, `ratify`, and `note --replace` are refused.\n\n## Hand-edits are an emergency path, not a workflow\n\nIf a raw edit is genuinely needed:\n\n```sh\nTASKTOOL_RAW=1 $EDITOR docs/tasklist.json\ntasktool validate --normalise\n```\n\n`--normalise` re-serialises the file through the canonical formatter so the pre-commit hook accepts it. There is no `tasktool edit --raw` subcommand by design — the friction keeps agents on the sanctioned commands.\n\n## New work mid-slice\n\n| Scenario | Action |\n|----------|--------|\n| Incidental fix in the same area | `tasktool create task <slice-id> --title ...` |\n| Real unit of work | `tasktool create slice <phase-id> --title ...` (or `--follow-up <slice-id>` for a letter-suffix) |\n| Bug surfaced by review | Inline task if cheap; follow-up slice if it deserves its own scope. |\n| Cross-cutting, unscheduled | `tasktool create cross --title ...` |\n\nCreating a new slice or X-item is allocation/tracking only. It does not authorize implementing that work in the current slice worktree. If the discovery is truly incidental to the active slice, add an in-slice task and keep going. If it is real follow-up work, record it and defer until the current slice closes, or create a separate isolated worktree for that follow-up after the current slice boundary is clean.\n\n## Referencing items in artifacts\n\n- Specs, plans, reviewer chain folders: fully-qualified ID at first mention (`P9.S3a`), short form afterwards.\n- Plan and spec filenames embed the ID: `YYYY-MM-DD-<id>-<slug>(-design).md`. The pre-commit hook rejects filenames whose ID has no `tasklist.json` row.\n- Phase planning docs should be registered through `planning_path` once supported. During bootstrap or migration, either attach the document to `spec_path` for the phase ID or keep unregistered drafts outside orphan-checked paths such as `docs/_drafts/`.\n- Commit messages may use either form; prefer fully-qualified for cross-phase commits.\n\n## Workflow artifacts\n\nSpec, plan, handoff, reviewer-chain, and archived-task paths are workflow artifacts. Register them through `tasktool artifact add` or `tasktool prepare`; do not hand-edit `docs/tasklist.json` refs for these paths. Use `tasktool artifact status <id> --strict` before handing work to another agent.\n\n## workflow_step\n\nSlices and phases carry an optional `workflow_step` field that tracks where the row is in the spec → plan → implement → done sequence. The two enums are intentionally different:\n\n- **Slice steps:** `spec | plan | implement | done`. Set manually as the slice progresses through its lifecycle.\n- **Phase steps:** `spec | ready | in_progress | done`. Set manually for `spec` / `ready`; `in_progress` / `done` are observable from child slice status and surface in `tasktool infer-step`.\n- **Cross-cutting (`X*`) rows have no `workflow_step`** — they skip the spec/plan loop.\n\nIn this revision the field is **informational only**. No tasktool command auto-advances it; no operation is refused based on its value. Future slices in `P6 — Programmatic Workflow Enhancements` will introduce auto-advance and downstream automation (statusline / session-rename).\n\n### Setting it manually\n\n```bash\ntasktool set P6.S1 --workflow-step plan\ntasktool set P6 --workflow-step ready\ntasktool set P6.S1 --clear-workflow-step\n```\n\n### Inspecting inferred values\n\n```bash\ntasktool infer-step P6.S1                 # text\ntasktool infer-step P6.S1 --format json   # structured\ntasktool infer-step --all --diff          # rows where stored != inferred (exit 1 if drift, 0 otherwise)\n```\n\n`infer-step` is read-only — it never mutates state. Use it to sanity-check what the field *would* be if you set it manually.\n\n### Transient slice review block\n\nThe external-reviewer script writes a small transient block (`review_active`, `review_stage`) on slices when a plan or post-slice review is in progress. The block is cleared when the slice's `workflow_step` changes or when the review finishes. Agents and skills should not write these fields directly.\n\n## Red flags\n\n| Thought | Reality |\n|---------|---------|\n| \"I'll just edit `docs/tasklist.json` by hand quickly.\" | The hook will refuse non-canonical bytes; `tasktool` is faster than fighting the hook. Use the CLI. |\n| \"I'll mark the slice `done` with `set` instead of `close` to skip the review gate.\" | `tasktool set --status done` routes through the same gate as `close`. The gate cannot be bypassed by reaching for a different subcommand. |\n| \"I'll mark this slice `done` to make it disappear.\" | Use `cancel`, not `close`. `done` is a lie if the work never shipped — and `close` runs the post-slice review gate, which is meaningless on cancelled work. |\n| \"I'll commit the spec now and add the row after.\" | The pre-commit hook rejects orphan spec/plan filenames. Allocate first. |\n| \"`tasktool` says the verdict isn't ready, but the reviewer comments look fine.\" | Re-read the verdict line. `revise` is `revise`. If the reviewer chain is mis-parsed, fix the chain; do not pass `--skip-review-gate` casually. |\n| \"I'll bring back `docs/TASKLIST.md` for readability.\" | The hook refuses commits that touch it. Use `tasktool render` if you want markdown. |\n| \"I'll just renumber IDs to match execution order.\" | No. IDs are stable. Execution order lives in the array order; IDs preserve creation order. |\n| \"Setup files are just scaffolding; I'll leave them dirty while implementing.\" | No. Setup/migration artifacts make post-slice review scope ambiguous. Resolve the setup boundary first. |\n| \"I created a follow-up slice/X-item, so I can knock it out in this worktree.\" | No. Allocation is not implementation permission. Follow-up work gets deferred or gets its own isolated worktree. |\n| \"I only need to add refs or flip the row before creating the worktree.\" | No. For an active implementation slice, tasktool refs/status/notes are part of the slice artifact set. Isolate first. |\n| \"The slice is currently blocked, so I'll add `blocked_on` to model the phase plan.\" | No. Use `depends_on` for planned sequencing. Use `blocked_on` only for active runtime blockers. |\n\n## Integration\n\n- `[[writing-plans]]` — embeds slice IDs in plan filenames; calls `tasktool show <id>` for context.\n- `[[brainstorming]]` — allocates IDs via `tasktool create` before writing the spec.\n- `[[external-review]]` — passes `docs/tasklist.json` (or `tasktool render` output) as `--context`.\n- `[[subagent-driven-development]]` — calls `tasktool close <slice-id>` at slice end and `tasktool archive-phase` at phase end.\n- `[[project-setup]]` — runs `tasktool init` and `install.sh --hook`.\n","exit_code":1,"status":"failed"}}
+{"type":"item.completed","item":{"id":"item_2","type":"agent_message","text":"I’m reading the implementation, tracker row, and current git state now. For a post-slice gate, I’m checking both behavior and whether the completion evidence is actually present in the worktree."}}
+{"type":"item.started","item":{"id":"item_3","type":"command_execution","command":"/usr/bin/zsh -lc 'git status --short && git log --oneline --decorate -8'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_3","type":"command_execution","command":"/usr/bin/zsh -lc 'git status --short && git log --oneline --decorate -8'","aggregated_output":"?? docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/\n67aa290 (HEAD -> worktree-p7-s1-data-model-migration-schema-v3-surfaces) P7.S1: v1/v2 to v3 compat — historical rows gain no churn\n7ac304b P7.S1: prove v1/v2 to v3 additive migration + drift-walker coverage\ne79ccc1 P7.S1: ledger-aware drift merge — never erase archived reservations\n5d4043b P7.S1: add P7 slice/project fields to JSON schema\nc814be2 P7.S1: deserialize P7 slice/project fields with missing-key tolerance\n709939d P7.S1: omit P7 slice/project fields when default on serialize\nb73aa87 P7.S1: export Reservation/LedgerReservation from tasktool package\n5b74cd5 P7.S1: add Reservation/LedgerReservation, Slice/Project fields, bump schema v3\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_4","type":"command_execution","command":"/usr/bin/zsh -lc \"sed -n '260,620p' docs/plans/2026-06-02-P7-S1-data-model-migration.md\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_4","type":"command_execution","command":"/usr/bin/zsh -lc \"sed -n '260,620p' docs/plans/2026-06-02-P7-S1-data-model-migration.md\"","aggregated_output":"\n### Step 1b.5 — Commit\n\n- [ ] Run:\n  ```sh\n  git add tools/tasktool/__init__.py tools/tasktool/tests/test_model.py\n  git commit -m \"P7.S1: export Reservation/LedgerReservation from tasktool package\"\n  ```\n\n---\n\n## Task 2 — Serialize: omit-when-default for the new fields + nested reservation (de)serialization\n\n### Step 2.1 — Write failing test: omit-when-default on serialize\n\n- [ ] Open `tools/tasktool/tests/test_serialize.py`. Append at end of file:\n  ```python\n  class P7OmitWhenDefaultTests(unittest.TestCase):\n      def test_default_slice_omits_new_keys(self):\n          p = Project(project=\"demo\")\n          ph = Phase(id=\"P1\", title=\"phase\", created=\"2026-06-02\")\n          ph.slices.append(Slice(id=\"S1\", title=\"slice\", created=\"2026-06-02\"))\n          p.phases.append(ph)\n          out = to_dict(p)\n          slc = out[\"phases\"][0][\"slices\"][0]\n          for key in (\n              \"integration_surfaces\", \"reservations\", \"coordination_group\",\n              \"worktree_base_sha\", \"landed_base_sha\",\n          ):\n              self.assertNotIn(key, slc, f\"{key} should be omitted when default\")\n\n      def test_default_project_omits_reservations_ledger(self):\n          p = Project(project=\"demo\")\n          out = to_dict(p)\n          self.assertNotIn(\"reservations_ledger\", out)\n\n      def test_schema_version_serialized_as_3(self):\n          p = Project(project=\"demo\")\n          out = to_dict(p)\n          self.assertEqual(out[\"schema_version\"], 3)\n\n      def test_non_default_slice_keys_are_kept(self):\n          from tasktool.model import Reservation\n          p = Project(project=\"demo\")\n          ph = Phase(id=\"P1\", title=\"phase\", created=\"2026-06-02\")\n          s = Slice(\n              id=\"S1\", title=\"slice\", created=\"2026-06-02\",\n              integration_surfaces=[\"cms-block-registry\"],\n              reservations=[Reservation(\n                  resource=\"homepage-sort\", value=\"15\", scope=\"phase\",\n                  note=\"hero slot\",\n              )],\n              coordination_group=\"cms\",\n              worktree_base_sha=\"abc123\",\n              landed_base_sha=\"def456\",\n          )\n          ph.slices.append(s)\n          p.phases.append(ph)\n          slc = to_dict(p)[\"phases\"][0][\"slices\"][0]\n          self.assertEqual(slc[\"integration_surfaces\"], [\"cms-block-registry\"])\n          self.assertEqual(slc[\"reservations\"], [{\n              \"resource\": \"homepage-sort\", \"value\": \"15\",\n              \"scope\": \"phase\", \"note\": \"hero slot\",\n          }])\n          self.assertEqual(slc[\"coordination_group\"], \"cms\")\n          self.assertEqual(slc[\"worktree_base_sha\"], \"abc123\")\n          self.assertEqual(slc[\"landed_base_sha\"], \"def456\")\n\n      def test_non_default_reservations_ledger_is_kept(self):\n          from tasktool.model import LedgerReservation\n          p = Project(project=\"demo\")\n          p.reservations_ledger.append(LedgerReservation(\n              resource=\"route-slug\", value=\"/offers\", scope=\"project\",\n              note=None, owner_id=\"P20.S3\", owner_phase_id=\"P20\",\n              archived_date=\"2026-06-02\",\n          ))\n          out = to_dict(p)\n          self.assertEqual(out[\"reservations_ledger\"], [{\n              \"resource\": \"route-slug\", \"value\": \"/offers\", \"scope\": \"project\",\n              \"note\": None, \"owner_id\": \"P20.S3\", \"owner_phase_id\": \"P20\",\n              \"archived_date\": \"2026-06-02\",\n          }])\n  ```\n\n### Step 2.2 — Run the failing test (expected FAIL)\n\n- [ ] Run:\n  ```sh\n  python -m pytest tools/tasktool/tests/test_serialize.py::P7OmitWhenDefaultTests -q\n  ```\n  Expected: **FAIL** — `test_default_slice_omits_new_keys` and `test_default_project_omits_reservations_ledger` fail because `asdict()` currently emits the new default-valued keys, and `test_schema_version_serialized_as_3` would already pass via SCHEMA_VERSION but the omit tests fail. (`test_non_default_*` may already pass since `asdict` serializes nested dataclasses, but the omit tests gate this task.)\n\n### Step 2.3 — Implement: extend the slice omit map\n\n- [ ] In `tools/tasktool/serialize.py`, **after** the `_WORKFLOW_DEFAULT_OMIT` dict (currently ends line 39) and its `_strip_workflow_defaults` function (ends line 50), add a new omit map + stripper for the P7 fields:\n  ```python\n  _P7_DEFAULT_OMIT = {\n      \"coordination_group\": None,\n      \"worktree_base_sha\": None,\n      \"landed_base_sha\": None,\n  }\n\n\n  def _strip_p7_defaults(d: dict) -> dict:\n      \"\"\"Drop P7 slice keys whose values equal their dataclass default.\n\n      Empty integration_surfaces / reservations lists and None scalar fields\n      are omitted so historical rows gain no churn on round-trip (spec §4.A F5).\n      \"\"\"\n      for field, default in _P7_DEFAULT_OMIT.items():\n          if field in d and d[field] == default:\n              del d[field]\n      if d.get(\"integration_surfaces\") == []:\n          d.pop(\"integration_surfaces\", None)\n      if d.get(\"reservations\") == []:\n          d.pop(\"reservations\", None)\n      return d\n  ```\n\n### Step 2.4 — Implement: call the slice stripper + strip empty `reservations_ledger`\n\n- [ ] In `tools/tasktool/serialize.py`, inside `to_dict`, in the per-slice loop (currently lines 73–74), add the new stripper call so the loop reads:\n  ```python\n          for slc in phase.get(\"slices\", []):\n              _strip_worktree_defaults(slc)\n              _strip_workflow_defaults(slc)\n              _strip_p7_defaults(slc)\n  ```\n- [ ] In the same `to_dict`, **before** the `out[\"schema_version\"] = SCHEMA_VERSION` line (currently line 79), add the project-level ledger strip:\n  ```python\n      # Omit reservations_ledger when empty so historical projects gain no churn.\n      if out.get(\"reservations_ledger\") == []:\n          del out[\"reservations_ledger\"]\n  ```\n\n### Step 2.5 — Run the test (expected PASS)\n\n- [ ] Run:\n  ```sh\n  python -m pytest tools/tasktool/tests/test_serialize.py::P7OmitWhenDefaultTests -q\n  ```\n  Expected: **PASS** (5 passed).\n\n### Step 2.6 — Commit\n\n- [ ] Run:\n  ```sh\n  git add tools/tasktool/serialize.py tools/tasktool/tests/test_serialize.py\n  git commit -m \"P7.S1: omit P7 slice/project fields when default on serialize\"\n  ```\n\n---\n\n## Task 3 — Deserialize: tolerant `from_dict` for the new fields + round-trip\n\n### Step 3.1 — Write failing test: deserialize tolerance + round-trip\n\n- [ ] Open `tools/tasktool/tests/test_serialize.py`. Append at end of file:\n  ```python\n  class P7DeserializeTests(unittest.TestCase):\n      def test_missing_keys_default_on_deserialize(self):\n          # A row with none of the new keys (the v1/v2 historical shape).\n          raw = {\n              \"project\": \"demo\", \"schema_version\": 3,\n              \"phases\": [{\n                  \"id\": \"P1\", \"title\": \"t\", \"created\": \"2026-06-02\", \"status\": \"ready\",\n                  \"slices\": [{\n                      \"id\": \"S1\", \"title\": \"t\", \"created\": \"2026-06-02\",\n                      \"status\": \"ready\",\n                  }],\n              }],\n              \"cross_cutting\": [], \"archived_phases\": [], \"archived_cross_cutting\": [],\n          }\n          p = from_dict(raw)\n          s = p.phases[0].slices[0]\n          self.assertEqual(s.integration_surfaces, [])\n          self.assertEqual(s.reservations, [])\n          self.assertIsNone(s.coordination_group)\n          self.assertIsNone(s.worktree_base_sha)\n          self.assertIsNone(s.landed_base_sha)\n          self.assertEqual(p.reservations_ledger, [])\n\n      def test_present_keys_deserialize_to_objects(self):\n          from tasktool.model import Reservation, LedgerReservation\n          raw = {\n              \"project\": \"demo\", \"schema_version\": 3,\n              \"phases\": [{\n                  \"id\": \"P1\", \"title\": \"t\", \"created\": \"2026-06-02\", \"status\": \"ready\",\n                  \"slices\": [{\n                      \"id\": \"S1\", \"title\": \"t\", \"created\": \"2026-06-02\",\n                      \"status\": \"ready\",\n                      \"integration_surfaces\": [\"cms-block-registry\", \"theme-tail-css\"],\n                      \"reservations\": [\n                          {\"resource\": \"homepage-sort\", \"value\": \"15\",\n                           \"scope\": \"phase\", \"note\": \"hero\"},\n                          {\"resource\": \"route-slug\", \"value\": \"/offers\",\n                           \"scope\": \"project\", \"note\": None},\n                      ],\n                      \"coordination_group\": \"cms\",\n                      \"worktree_base_sha\": \"abc123\",\n                      \"landed_base_sha\": \"def456\",\n                  }],\n              }],\n              \"cross_cutting\": [], \"archived_phases\": [], \"archived_cross_cutting\": [],\n              \"reservations_ledger\": [\n                  {\"resource\": \"block-kind\", \"value\": \"slider\", \"scope\": \"project\",\n                   \"note\": None, \"owner_id\": \"P20.S2\", \"owner_phase_id\": \"P20\",\n                   \"archived_date\": \"2026-06-01\"},\n              ],\n          }\n          p = from_dict(raw)\n          s = p.phases[0].slices[0]\n          self.assertEqual(s.integration_surfaces, [\"cms-block-registry\", \"theme-tail-css\"])\n          self.assertEqual(s.reservations[0], Reservation(\n              resource=\"homepage-sort\", value=\"15\", scope=\"phase\", note=\"hero\"))\n          self.assertEqual(s.reservations[1], Reservation(\n              resource=\"route-slug\", value=\"/offers\", scope=\"project\", note=None))\n          self.assertEqual(s.coordination_group, \"cms\")\n          self.assertEqual(s.worktree_base_sha, \"abc123\")\n          self.assertEqual(s.landed_base_sha, \"def456\")\n          self.assertEqual(p.reservations_ledger[0], LedgerReservation(\n              resource=\"block-kind\", value=\"slider\", scope=\"project\", note=None,\n              owner_id=\"P20.S2\", owner_phase_id=\"P20\", archived_date=\"2026-06-01\"))\n\n      def test_full_roundtrip_with_p7_fields(self):\n          from tasktool.model import Reservation, LedgerReservation\n          p = Project(project=\"demo\")\n          ph = Phase(id=\"P1\", title=\"phase\", created=\"2026-06-02\")\n          ph.slices.append(Slice(\n              id=\"S1\", title=\"slice\", created=\"2026-06-02\",\n              integration_surfaces=[\"cms-block-registry\"],\n              reservations=[Reservation(\n                  resource=\"homepage-sort\", value=\"15\", scope=\"phase\", note=\"hero\")],\n              coordination_group=\"cms\",\n              worktree_base_sha=\"abc123\",\n              landed_base_sha=\"def456\",\n          ))\n          p.phases.append(ph)\n          p.reservations_ledger.append(LedgerReservation(\n              resource=\"block-kind\", value=\"slider\", scope=\"project\", note=None,\n              owner_id=\"P20.S2\", owner_phase_id=\"P20\", archived_date=\"2026-06-01\"))\n          back = from_dict(to_dict(p))\n          self.assertEqual(back, p)\n\n      def test_default_roundtrip_equality(self):\n          # A wholly-default project must round-trip to an equal object even\n          # though the new keys are omitted on serialize.\n          p = Project(project=\"demo\")\n          ph = Phase(id=\"P1\", title=\"phase\", created=\"2026-06-02\")\n          ph.slices.append(Slice(id=\"S1\", title=\"slice\", created=\"2026-06-02\"))\n          p.phases.append(ph)\n          back = from_dict(to_dict(p))\n          self.assertEqual(back, p)\n  ```\n\n### Step 3.2 — Run the failing test (expected FAIL)\n\n- [ ] Run:\n  ```sh\n  python -m pytest tools/tasktool/tests/test_serialize.py::P7DeserializeTests -q\n  ```\n  Expected: **FAIL** — `from_dict` does not yet read the new keys, so deserialized `Slice` objects lack the attributes / they are dropped, and `Project` has no `reservations_ledger` argument (`TypeError` or attribute mismatch on equality).\n\n### Step 3.3 — Implement: reservation/ledger deserialization helpers\n\n- [ ] In `tools/tasktool/serialize.py`, update the model import (currently lines 5–10) to add `Reservation` and `LedgerReservation`:\n  ```python\n  from tasktool.model import (\n      Project, Phase, Slice, Task, CrossCutting, ArchivedPhase,\n      ArchivedCrossCutting, BlockedOn, Reservation, LedgerReservation,\n      Status, PlanningStatus, SCHEMA_VERSION,\n      SliceWorkflowStep, PhaseWorkflowStep, ReviewStage,\n  )\n  ```\n- [ ] In `from_dict`, **before** the `_slice` inner function (currently defined at line 122), add two helpers (place them after `_blocked`, currently line 121):\n  ```python\n      def _reservation(rd):\n          return Reservation(\n              resource=rd[\"resource\"], value=rd[\"value\"],\n              scope=rd.get(\"scope\", \"phase\"), note=rd.get(\"note\"),\n          )\n      def _ledger_reservation(rd):\n          return LedgerReservation(\n              resource=rd[\"resource\"], value=rd[\"value\"], scope=rd[\"scope\"],\n              note=rd.get(\"note\"), owner_id=rd[\"owner_id\"],\n              owner_phase_id=rd[\"owner_phase_id\"], archived_date=rd[\"archived_date\"],\n          )\n  ```\n\n### Step 3.4 — Implement: populate the new `Slice` fields in `_slice`\n\n- [ ] In `from_dict`'s `_slice` function, **after** the `worktree_prune_pending_at=...` keyword argument (currently line 146) and before the closing `)`, add:\n  ```python\n              integration_surfaces=list(sd.get(\"integration_surfaces\", [])),\n              reservations=[_reservation(r) for r in sd.get(\"reservations\", [])],\n              coordination_group=sd.get(\"coordination_group\"),\n              worktree_base_sha=_strict_opt_str(sd.get(\"worktree_base_sha\"), scope=scope, field=\"worktree_base_sha\"),\n              landed_base_sha=_strict_opt_str(sd.get(\"landed_base_sha\"), scope=scope, field=\"landed_base_sha\"),\n  ```\n\n### Step 3.5 — Implement: populate `Project.reservations_ledger`\n\n- [ ] In `from_dict`'s final `return Project(...)` (currently lines 188–199), add the ledger argument after `archived_cross_cutting=[...]`:\n  ```python\n          reservations_ledger=[\n              _ledger_reservation(r) for r in d.get(\"reservations_ledger\", [])\n          ],\n  ```\n\n### Step 3.6 — Run the test (expected PASS)\n\n- [ ] Run:\n  ```sh\n  python -m pytest tools/tasktool/tests/test_serialize.py::P7DeserializeTests -q\n  ```\n  Expected: **PASS** (4 passed).\n\n### Step 3.7 — Run the full serialize suite (regression check)\n\n- [ ] Run:\n  ```sh\n  python -m pytest tools/tasktool/tests/test_serialize.py -q\n  ```\n  Expected: **PASS** — all pre-existing serialize tests plus the new `P7OmitWhenDefaultTests` and `P7DeserializeTests` classes.\n\n### Step 3.8 — Commit\n\n- [ ] Run:\n  ```sh\n  git add tools/tasktool/serialize.py tools/tasktool/tests/test_serialize.py\n  git commit -m \"P7.S1: deserialize P7 slice/project fields with missing-key tolerance\"\n  ```\n\n---\n\n## Task 4 — JSON Schema: add new fields to `schema_gen.py`\n\n> Why this task is required: `test_v1_compat.py::test_v1_validates_against_v3_schema_after_save` (renamed from `..._v2_...` in Task 6) and `test_schema_gen.py` validate serialized output against `build_schema()`, which uses `additionalProperties: False`. Without schema entries for the new keys, any project that *declares* a surface/reservation would fail schema validation. The schema must enumerate the new keys.\n\n### Step 4.1 — Write failing test: schema admits the new fields\n\n- [ ] Open `tools/tasktool/tests/test_schema_gen.py`. First read its existing style (`python -m pytest tools/tasktool/tests/test_schema_gen.py -q` to confirm it passes today). Append a test that builds the schema and validates a project carrying the new fields. Add at end of file:\n  ```python\n  def test_schema_version_const_is_3():\n      from tasktool.schema_gen import build_schema\n      schema = build_schema()\n      assert schema[\"properties\"][\"schema_version\"] == {\"const\": 3}\n\n\n  def test_schema_admits_p7_fields():\n      # NB: NO conditional skip. jsonschema is a required test dependency for\n      # this slice's schema gate (it is present in the repo dev environment —\n      # jsonschema 4.26.0 — and the existing test_v1_compat / test_schema_gen\n      # suites already validate against build_schema()). A plain top-level\n      # import makes a missing dependency a hard ERROR, not a silent skip, so\n      # the schema gate cannot be quietly bypassed offline.\n      import jsonschema\n      from tasktool.schema_gen import build_schema\n      from tasktool.serialize import to_dict\n      from tasktool.model import (\n          Project, Phase, Slice, Reservation, LedgerReservation,\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_5","type":"command_execution","command":"/usr/bin/zsh -lc \"sed -n '620,980p' docs/plans/2026-06-02-P7-S1-data-model-migration.md\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_5","type":"command_execution","command":"/usr/bin/zsh -lc \"sed -n '620,980p' docs/plans/2026-06-02-P7-S1-data-model-migration.md\"","aggregated_output":"          Project, Phase, Slice, Reservation, LedgerReservation,\n      )\n      p = Project(project=\"demo\")\n      ph = Phase(id=\"P1\", title=\"t\", created=\"2026-06-02\")\n      ph.slices.append(Slice(\n          id=\"S1\", title=\"t\", created=\"2026-06-02\",\n          integration_surfaces=[\"cms-block-registry\"],\n          reservations=[Reservation(\n              resource=\"homepage-sort\", value=\"15\", scope=\"phase\", note=\"hero\")],\n          coordination_group=\"cms\",\n          worktree_base_sha=\"abc123\",\n          landed_base_sha=\"def456\",\n      ))\n      p.phases.append(ph)\n      p.reservations_ledger.append(LedgerReservation(\n          resource=\"block-kind\", value=\"slider\", scope=\"project\", note=None,\n          owner_id=\"P20.S2\", owner_phase_id=\"P20\", archived_date=\"2026-06-01\"))\n      jsonschema.validate(instance=to_dict(p), schema=build_schema())\n  ```\n\n> If `test_schema_gen.py` does not exist or uses a different harness shape, mirror its actual imports — but the two assertions above are self-contained and only depend on `build_schema()` + `to_dict()`.\n\n### Step 4.1a — Update the existing stale schema-const assertion (REQUIRED)\n\n- [ ] In `tools/tasktool/tests/test_schema_gen.py`, there is a pre-existing test (around line 108) that pins the **old** schema const:\n  ```python\n  def test_schema_version_bumped_to_2():\n      schema = build_schema()\n      assert schema[\"properties\"][\"schema_version\"][\"const\"] == 2\n  ```\n  This will fail once `SCHEMA_VERSION` is 3. **Rename and update it** to track v3 (do not leave it alongside the new `test_schema_version_const_is_3` with a now-false assertion):\n  ```python\n  def test_schema_version_bumped_to_3():\n      schema = build_schema()\n      assert schema[\"properties\"][\"schema_version\"][\"const\"] == 3\n  ```\n  (This is functionally equivalent to the appended `test_schema_version_const_is_3` — both are fine; the point is that **no surviving test asserts `== 2`**. If you prefer, delete this redundant renamed test entirely and rely on `test_schema_version_const_is_3`; the binding requirement is that the stale `== 2` assertion is gone.)\n\n### Step 4.2 — Run the failing test (expected FAIL)\n\n- [ ] Run:\n  ```sh\n  python -m pytest tools/tasktool/tests/test_schema_gen.py -q\n  ```\n  Expected: **FAIL** — `test_schema_version_const_is_3` and the renamed `test_schema_version_bumped_to_3` already pass (driven by `SCHEMA_VERSION`, which Task 1 bumped to 3), but `test_schema_admits_p7_fields` fails: `jsonschema.exceptions.ValidationError` (`Additional properties are not allowed ('integration_surfaces', 'reservations', ... were unexpected)`). Confirm there is **no** surviving `test_schema_version_bumped_to_2` asserting `== 2` (it was renamed/removed in Step 4.1a). The test imports `jsonschema` at the top with no skip guard; if `jsonschema` were absent the run would ERROR (a hard, visible gate failure), not skip — confirm the failure is the `ValidationError` above (meaning `jsonschema` is present and actually validating), not a `ModuleNotFoundError`. If you see `ModuleNotFoundError: No module named 'jsonschema'`, the dev environment is misconfigured: install `jsonschema` into it (it is already present in the maintained dev env at 4.26.0) and re-run so the schema validation is genuinely exercised before proceeding. Do **not** convert the test back to a conditional skip.\n\n> **Schema-gate dependency policy.** The repo's `pyproject.toml` declares only pytest config (no `[project].dependencies`), so test dependencies are ambient in the dev environment rather than pinned in a manifest. `jsonschema` (4.26.0) is present there and is already relied on by `test_v1_compat.py` and `test_schema_gen.py`. This slice's schema gate therefore runs in that same environment — record the passing `python -m pytest tools/tasktool/tests/test_schema_gen.py -q` output as the evidence the schema admits the new fields. If a future environment lacks `jsonschema`, add it to the dev environment; never weaken the gate to a skip.\n\n### Step 4.3 — Implement: define reservation sub-schemas\n\n- [ ] In `tools/tasktool/schema_gen.py`, inside `build_schema()`, **after** the `blocked_on = {...}` definition (currently ends line 28) and **before** `task = {...}` (line 29), add:\n  ```python\n      reservation = {\n          \"type\": \"object\",\n          \"required\": [\"resource\", \"value\"],\n          \"properties\": {\n              \"resource\": {\"type\": \"string\"},\n              \"value\": {\"type\": \"string\"},\n              \"scope\": {\"enum\": [\"phase\", \"project\"]},\n              \"note\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n          },\n          \"additionalProperties\": False,\n      }\n      ledger_reservation = {\n          \"type\": \"object\",\n          \"required\": [\n              \"resource\", \"value\", \"scope\", \"owner_id\",\n              \"owner_phase_id\", \"archived_date\",\n          ],\n          \"properties\": {\n              \"resource\": {\"type\": \"string\"},\n              \"value\": {\"type\": \"string\"},\n              \"scope\": {\"enum\": [\"phase\", \"project\"]},\n              \"note\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n              \"owner_id\": {\"type\": \"string\"},\n              \"owner_phase_id\": {\"type\": \"string\"},\n              \"archived_date\": date_str,\n          },\n          \"additionalProperties\": False,\n      }\n  ```\n\n### Step 4.4 — Implement: add the five slice properties\n\n- [ ] In `schema_gen.py`, in the `slice_` object's `\"properties\"` (currently the `review_stage` entry ends at line 77, before `},` closing properties on line 78), add after the `review_stage` property:\n  ```python\n              \"integration_surfaces\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}},\n              \"reservations\": {\"type\": \"array\", \"items\": reservation},\n              \"coordination_group\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n              \"worktree_base_sha\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n              \"landed_base_sha\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n  ```\n\n### Step 4.5 — Implement: add `reservations_ledger` to the project schema\n\n- [ ] In `schema_gen.py`, in the top-level return object's `\"properties\"` (currently `archived_cross_cutting` entry on line 160), add after it:\n  ```python\n              \"reservations_ledger\": {\"type\": \"array\", \"items\": ledger_reservation},\n  ```\n\n### Step 4.6 — Run the test (expected PASS)\n\n- [ ] Run:\n  ```sh\n  python -m pytest tools/tasktool/tests/test_schema_gen.py -q\n  ```\n  Expected: **PASS** — including `test_schema_admits_p7_fields`.\n\n### Step 4.7 — Commit\n\n- [ ] Run:\n  ```sh\n  git add tools/tasktool/schema_gen.py tools/tasktool/tests/test_schema_gen.py\n  git commit -m \"P7.S1: add P7 slice/project fields to JSON schema\"\n  ```\n\n---\n\n## Task 5a — Ledger-aware drift merge (BLOCKING safety fix)\n\n> **Why this is required and load-bearing.** `migrate.py` reconciles a local checkout against the authoritative tasklist (`compute_deltas` → `apply_deltas`). Its `_PROJECT_COLLECTIONS` (`migrate.py:20`) names the project-level collections that get *structural, additive* merge handling (`phases`, `cross_cutting`, `archived_phases`, `archived_cross_cutting`); everything else on `Project` is treated as a **scalar** by `_project_scalar_fields()` (`migrate.py:100`). Scalar project deltas are applied by direct `setattr` in `_apply_local` (`migrate.py:247–249`). If `reservations_ledger` is left scalar, then under `accept-local` reconciliation a **stale local checkout with `reservations_ledger == []`** produces a scalar delta `[] != <authoritative ledger>` and **overwrites the authoritative ledger with `[]`**, erasing archived project-scoped reservations. That directly violates the spec guarantee that project-scoped reservations survive phase archival (§4.A ~line 112, §4.B ~line 170) and re-opens the exact `P20` collision the phase exists to prevent. The ledger has **no `.id`**, so the generic `_diff_collection`/`_apply_collection` (which key on `row.id`) cannot be reused as-is; the ledger's identity key is the composite `resource:value:scope:owner_id` (the spec's F7 dedupe key). This task registers the ledger as a merge-aware collection and gives it a bespoke, identity-keyed, union (never-delete) merge.\n\n### Step 5a.1 — Write failing test: ledger is preserved and union-merged under drift reconciliation\n\n- [ ] Open `tools/tasktool/tests/test_migrate.py`. Add a helper that builds a `LedgerReservation` and three tests, appended at end of file:\n  ```python\n  def _ledger(resource=\"route-slug\", value=\"/offers\", scope=\"project\",\n              note=None, owner_id=\"P20.S3\", owner_phase_id=\"P20\",\n              archived_date=\"2026-06-01\"):\n      from tasktool.model import LedgerReservation\n      return LedgerReservation(\n          resource=resource, value=value, scope=scope, note=note,\n          owner_id=owner_id, owner_phase_id=owner_phase_id,\n          archived_date=archived_date,\n      )\n\n\n  def test_stale_local_empty_ledger_does_not_erase_authoritative_ledger():\n      # Authoritative holds an archived reservation; local checkout is stale\n      # and has an empty ledger. accept-local reconciliation MUST preserve it.\n      local = _project_with_slice()\n      authoritative = _project_with_slice()\n      authoritative.reservations_ledger.append(_ledger())\n\n      deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)\n      merged = apply_deltas(\n          authoritative=authoritative, local=local,\n          deltas=deltas, conflicts=conflicts, policy=\"accept-local\",\n      )\n\n      assert len(merged.reservations_ledger) == 1\n      assert merged.reservations_ledger[0] == _ledger()\n\n\n  def test_local_adds_distinct_ledger_holder_unions_both():\n      # Authoritative has holder A; local has A plus a distinct holder B.\n      # Merge must contain BOTH, deduped on resource:value:scope:owner_id.\n      holder_a = _ledger(owner_id=\"P20.S3\")\n      holder_b = _ledger(owner_id=\"P20.S4\")  # same resource:value:scope, diff owner\n      authoritative = _project_with_slice()\n      authoritative.reservations_ledger.append(holder_a)\n      local = _project_with_slice()\n      local.reservations_ledger.append(holder_a)\n      local.reservations_ledger.append(holder_b)\n\n      deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)\n      merged = apply_deltas(\n          authoritative=authoritative, local=local,\n          deltas=deltas, conflicts=conflicts, policy=\"accept-local\",\n      )\n\n      keys = {\n          (r.resource, r.value, r.scope, r.owner_id)\n          for r in merged.reservations_ledger\n      }\n      assert keys == {\n          (\"route-slug\", \"/offers\", \"project\", \"P20.S3\"),\n          (\"route-slug\", \"/offers\", \"project\", \"P20.S4\"),\n      }\n      # No duplicate of holder_a despite it existing in both sides.\n      assert len(merged.reservations_ledger) == 2\n\n\n  def test_identical_ledger_on_both_sides_yields_no_duplicate():\n      holder_a = _ledger()\n      authoritative = _project_with_slice()\n      authoritative.reservations_ledger.append(holder_a)\n      local = _project_with_slice()\n      local.reservations_ledger.append(_ledger())  # same composite key\n\n      deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)\n      merged = apply_deltas(\n          authoritative=authoritative, local=local,\n          deltas=deltas, conflicts=conflicts, policy=\"accept-local\",\n      )\n      assert len(merged.reservations_ledger) == 1\n  ```\n\n### Step 5a.2 — Run the failing test (expected FAIL)\n\n- [ ] Run:\n  ```sh\n  python -m pytest tools/tasktool/tests/test_migrate.py -k ledger -q\n  ```\n  Expected: **FAIL** — `test_stale_local_empty_ledger_does_not_erase_authoritative_ledger` fails because, with `reservations_ledger` still scalar, `compute_deltas` emits a `<project>`/`reservations_ledger` field delta (`[]` vs the authoritative list) and `accept-local` `setattr`s the empty list, leaving `merged.reservations_ledger == []` (assert `len == 1` fails). The union test fails for the same root cause (local list replaces authoritative wholesale rather than unioning).\n\n### Step 5a.3 — Implement: register the ledger as merge-aware (remove from scalar handling)\n\n- [ ] In `tools/tasktool/migrate.py`, add a dedicated constant for the ledger's composite identity key, just below `_PROJECT_COLLECTIONS` (currently lines 20–25):\n  ```python\n  # reservations_ledger rows have no `.id`; their identity is this composite.\n  _LEDGER_KEY_FIELDS = (\"resource\", \"value\", \"scope\", \"owner_id\")\n  ```\n- [ ] Exclude `reservations_ledger` from scalar treatment **and** keep it in the walker's covered set. Change `_project_scalar_fields()` (currently lines 100–105) so it excludes both the structural collections and the ledger:\n  ```python\n  def _project_scalar_fields() -> tuple[str, ...]:\n      handled = set(_PROJECT_COLLECTIONS) | {\"reservations_ledger\"}\n      return tuple(\n          field.name\n          for field in fields(Project)\n          if field.name not in handled\n      )\n  ```\n- [ ] Update `walker_field_coverage()` (currently lines 86–97) so the `Project` entry still reports full coverage including the ledger. Change its `\"Project\"` line to:\n  ```python\n          \"Project\": (\n              set(_project_scalar_fields())\n              | set(_PROJECT_COLLECTIONS)\n              | {\"reservations_ledger\"}\n          ),\n  ```\n  (This keeps `test_walker_covers_every_dataclass_field` green: every `Project` field — scalars, structural collections, and the ledger — is accounted for.)\n\n### Step 5a.4 — Implement: ledger diff + union-merge helpers\n\n- [ ] In `tools/tasktool/migrate.py`, add a ledger key helper and a union-merge applier. Place them near the other module-level helpers (e.g. immediately before `_qualify`, currently line 337):\n  ```python\n  def _ledger_key(row) -> tuple:\n      return tuple(getattr(row, name) for name in _LEDGER_KEY_FIELDS)\n\n\n  def _ledger_has_local_additions(local, authoritative) -> bool:\n      authoritative_keys = {_ledger_key(r) for r in authoritative.reservations_ledger}\n      return any(\n          _ledger_key(r) not in authoritative_keys\n          for r in local.reservations_ledger\n      )\n\n\n  def _union_ledger(authoritative, local) -> list:\n      \"\"\"Union authoritative + local ledger rows, deduped on the composite key.\n\n      Authoritative rows are NEVER dropped (a stale-local empty ledger cannot\n      erase archived reservations); local-only rows are appended. The first\n      occurrence of each composite key wins, so authoritative metadata is\n      authoritative for shared keys.\n      \"\"\"\n      merged: list = []\n      seen: set = set()\n      for row in list(authoritative.reservations_ledger) + list(local.reservations_ledger):\n          key = _ledger_key(row)\n          if key in seen:\n              continue\n          seen.add(key)\n          merged.append(copy.deepcopy(row))\n      return merged\n  ```\n\n### Step 5a.5 — Implement: surface ledger additions as a delta in `_diff_project`\n\n- [ ] In `_diff_project` (currently lines 108–158), after the scalar-field loop and before the `_diff_collection(... local.phases ...)` call, emit a single additive marker delta when local introduces ledger rows the authoritative side lacks. Insert:\n  ```python\n      if _ledger_has_local_additions(local, authoritative):\n          deltas.append(\n              Delta(\n                  kind=\"add\",\n                  row_id=\"<project>.reservations_ledger\",\n                  field=None,\n                  local_value=list(local.reservations_ledger),\n                  authoritative_value=list(authoritative.reservations_ledger),\n              )\n          )\n  ```\n  (Because `reservations_ledger` is no longer a scalar field, the scalar loop no longer emits a destructive `setattr` delta for it — so a stale empty local ledger produces **no** delta and cannot erase anything. A delta is emitted only when local *adds* holders.)\n\n### Step 5a.6 — Implement: apply the ledger union in `_apply_local`\n\n- [ ] In `_apply_local` (currently lines 244–279), after `merged = copy.deepcopy(authoritative)` and the existing `<project>` scalar loop, and before the `_apply_collection(... merged.phases ...)` call, add the union step:\n  ```python\n      merged.reservations_ledger = _union_ledger(authoritative, local)\n  ```\n  This runs unconditionally on `accept-local`: it preserves every authoritative ledger row and appends any distinct local additions, deduped on `resource:value:scope:owner_id`. (`accept-authoritative` returns `authoritative` unchanged via the early return at `migrate.py:60–61`, so the authoritative ledger is trivially preserved there.)\n\n### Step 5a.7 — Run the test (expected PASS)\n\n- [ ] Run:\n  ```sh\n  python -m pytest tools/tasktool/tests/test_migrate.py -k ledger -q\n  ```\n  Expected: **PASS** (3 passed) — stale empty local ledger preserves authoritative holders; distinct local holder unions both; identical row on both sides dedupes to one.\n\n### Step 5a.8 — Run the full migrate suite (regression: walker coverage + per-field acceptance)\n\n- [ ] Run:\n  ```sh\n  python -m pytest tools/tasktool/tests/test_migrate.py -q\n  ```\n  Expected: **PASS** — including `test_walker_covers_every_dataclass_field` (the `Project` coverage set now explicitly includes `reservations_ledger`). The pre-existing `test_per_field_migration_acceptance_for_non_identity_non_collection_fields` parametrization (Task 5) intentionally does **not** exercise `reservations_ledger` (Step 5.1 leaves it without a value pair, so it falls through to `(None, None)` and is skipped) because the ledger's merge contract is union/never-delete, not setattr-replace — that contract is covered by this task's three dedicated tests.\n\n### Step 5a.9 — Commit\n\n- [ ] Run:\n  ```sh\n  git add tools/tasktool/migrate.py tools/tasktool/tests/test_migrate.py\n  git commit -m \"P7.S1: ledger-aware drift merge — never erase archived reservations\"\n  ```\n\n---\n\n## Task 5 — Migration: v1→v3 / v2→v3 additivity + drift-walker coverage\n\n> The repository's `migrate.py` is a *drift merge* walker (local↔authoritative), not a schema-version transformer; schema-version \"migration\" is performed implicitly by `from_dict` defaulting missing keys + `to_dict` re-stamping `SCHEMA_VERSION` (the existing v1→v2 pattern). This task proves both: (a) the drift walker still covers every field of `Slice`/`Project` (the existing `test_walker_covers_every_dataclass_field` would fail if the walker missed the new fields — it enumerates `fields(...)` dynamically, so it should already pass, but we add per-field migration acceptance pairs), and (b) v1- and v2-shaped raw rows load into a v3 model with the new fields defaulted, and re-serialize without churn.\n\n### Step 5.1 — Write failing test: per-field drift migration for the new fields\n\n- [ ] Open `tools/tasktool/tests/test_migrate.py`. In `_value_pair_for_field`, add new branches **before** the final `return (None, None)`:\n  ```python\n      if field.name == \"integration_surfaces\":\n          return ([], [\"cms-block-registry\"])\n      if field.name == \"reservations\":\n          from tasktool.model import Reservation\n          return ([], [Reservation(resource=\"homepage-sort\", value=\"15\", scope=\"phase\")])\n      if field.name == \"coordination_group\":\n          return (None, \"cms\")\n      if field.name in {\"worktree_base_sha\", \"landed_base_sha\"}:\n          return (None, \"abc123\")\n      # NB: reservations_ledger is deliberately NOT given a value pair here.\n      # The generic acceptance test asserts a scalar setattr-style merge\n      # (`get_on(merged) == local_val`), but the ledger uses bespoke\n      # union/never-delete semantics (Task 5a). Returning (None, None) makes\n      # the parametrized test skip it; its merge behavior is covered by the\n      # dedicated ledger tests in Task 5a. Leave it to fall through to the\n      # function's final `return (None, None)`.\n  ```\n\n> Why `reservations_ledger` is intentionally excluded from this generic value-pair: the parametrized acceptance test (`test_per_field_migration_acceptance_for_non_identity_non_collection_fields`) treats a field's merge as \"local value wins via setattr\" and asserts `get_on(merged) == local_val`. That contract is **false** for the ledger after Task 5a (it unions authoritative + local rather than replacing). Forcing a value pair here would either pass for the wrong reason (the `auth=[]` case happens to equal the union) or fail once authoritative holds rows. The ledger's real merge contract is asserted by the three dedicated tests in Task 5a.\n- [ ] Also append a dedicated v1→v3 / v2→v3 additive-load test at end of file:\n  ```python\n  def test_v1_and_v2_raw_load_into_v3_defaults():\n      from tasktool.serialize import from_dict, to_dict\n      for version in (1, 2):\n          raw = {\n              \"project\": \"x\", \"schema_version\": version, \"north_star\": \"\",\n              \"phases\": [{\n                  \"id\": \"P1\", \"title\": \"t\", \"created\": \"2026-05-01\", \"status\": \"ready\",\n                  \"slices\": [{\n                      \"id\": \"S1\", \"title\": \"t\", \"created\": \"2026-05-01\",\n                      \"status\": \"ready\",\n                  }],\n              }],\n              \"cross_cutting\": [], \"archived_phases\": [], \"archived_cross_cutting\": [],\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_6","type":"command_execution","command":"/usr/bin/zsh -lc \"sed -n '1,260p' docs/plans/2026-06-02-P7-S1-data-model-migration.md\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_6","type":"command_execution","command":"/usr/bin/zsh -lc \"sed -n '1,260p' docs/plans/2026-06-02-P7-S1-data-model-migration.md\"","aggregated_output":"# P7.S1 — Data Model + Migration (schema v3) Implementation Plan\n\n> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.\n\n**Goal:** Add integration-surface, scarce-reservation, coordination-group, and worktree base/landed-SHA fields to the `tasktool` data model and bump the on-disk schema to v3, with additive v1→v3 / v2→v3 migration and omit-when-default serialization so historical `tasklist.json` rows gain zero churn.\n\n**Architecture:** The change is in the model/serialization/drift-merge layer of the `tasktool` CLI (`tools/tasktool/`). New value objects `Reservation` and `LedgerReservation` are added as `@dataclass(slots=True)` types alongside the existing `BlockedOn`; five new fields are appended to `Slice` and one collection field to `Project`, and both new types are re-exported from the package `__init__`. Serialization mirrors the existing `_strip_worktree_defaults` / `_strip_workflow_defaults` omit-when-default convention so default-valued rows serialize byte-identically to today; deserialization is tolerant of missing keys (the additive migration path). The JSON Schema (`schema_gen.py`) is extended to admit the new keys, and the drift-merge walker (`migrate.py`) is extended to treat `reservations_ledger` as a **merge-aware, union/never-delete collection** (not a scalar) so reconciliation can never erase archived project-scoped reservations — keeping validation and drift-migration in lockstep, which the test suite enforces.\n\n**Tech Stack:** Python 3, dataclasses, pytest\n\n---\n\n## Scheduling\n\nP7.S1 has **no `depends_on`** — it is the foundation slice for phase P7. Per the governing spec (§5 slice decomposition table), S1 blocks S2, S3, S4, S6, and S7 (each of those declares `S1` among its dependencies). S1 itself depends on nothing, so it is **independently plannable and independently executable right now**: it only touches `model.py`, `__init__.py`, `serialize.py`, `schema_gen.py`, `migrate.py`, and their tests, none of which are being modified by a sibling slice in flight. No coordination group or reservation is required for S1 itself. Confirm before starting that no other P7 slice has begun mutating these source files (`tasktool worktree list --all`); if all clear, proceed.\n\nThis slice writes **no** CLI commands, **no** scheduling/overlap logic, and **no** worktree base-SHA *recording* — it only defines the fields those later slices populate. `worktree_base_sha` / `landed_base_sha` are added as inert `None`-default fields here; the logic that stamps them ships in S4.\n\n---\n\n## File Structure\n\n| File | Responsibility | Change in this slice |\n|------|----------------|----------------------|\n| `tools/tasktool/model.py` | Dataclass definitions + `SCHEMA_VERSION` constant | Add `Reservation` and `LedgerReservation` dataclasses; add 5 fields to `Slice`; add `reservations_ledger` to `Project`; bump `SCHEMA_VERSION` 2 → 3 |\n| `tools/tasktool/__init__.py` | Public package API (`from tasktool import ...`) + `__all__` | Export `Reservation` and `LedgerReservation` (mirrors how the other model dataclasses are re-exported at lines 4–16 / 22–34) |\n| `tools/tasktool/serialize.py` | `to_dict` / `from_dict`, omit-when-default stripping, canonical dump/load | Strip new default-valued keys on serialize; deserialize new keys tolerantly (default when absent); nest `Reservation`/`LedgerReservation` (de)serialization |\n| `tools/tasktool/schema_gen.py` | JSON Schema generator validated against on save | Add `integration_surfaces`, `reservations`, `coordination_group`, `worktree_base_sha`, `landed_base_sha` to the slice object; add `reservations_ledger` to the project object; define `reservation` / `ledger_reservation` sub-schemas |\n| `tools/tasktool/migrate.py` | Drift diff/merge walker (`compute_deltas` / `apply_deltas`) + `walker_field_coverage()` | **Structural change required:** register `reservations_ledger` as a merge-aware collection (it is currently mis-classified as a *scalar* project field, which makes drift reconciliation able to erase archived reservations — see Task 5a). Add ledger-aware diff/merge keyed/deduped on `resource:value:scope:owner_id`. The `Slice`-field walker remains dynamic (`fields(Slice)`), so `test_walker_covers_every_dataclass_field` still passes for the slice fields |\n| `tools/tasktool/tests/test_model.py` | Dataclass default / construction tests | New tests for the new dataclasses, new `Slice` field defaults, new `Project` field default, and `SCHEMA_VERSION == 3` |\n| `tools/tasktool/tests/test_serialize.py` | Round-trip + omit-when-default + deserialize-tolerance tests | New round-trip, omit-when-default, and missing-key tolerance tests |\n| `tools/tasktool/tests/test_migrate.py` | Drift-walker coverage + per-field migration acceptance | New per-field value pairs for the added fields so the parametrized acceptance test exercises them |\n| `tools/tasktool/tests/test_v1_compat.py` | v1 legacy-row load + promotion compat | New v1→v3 and v2→v3 no-churn compat assertions |\n\n> **Source-of-truth note:** Edit **only** `tools/tasktool/`. `plugins/superstar/tools/tasktool/` is a synced copy maintained by release scripts — do **not** touch it in this slice.\n\n> **Test invocation (verified working from repo root):**\n> ```sh\n> python -m pytest tools/tasktool/tests/<file> -q\n> ```\n> Root `pyproject.toml` sets `addopts = \"--import-mode=importlib\"` and `testpaths` includes `tools/tasktool/tests`, so `tasktool` imports resolve without a `PYTHONPATH` export. Run all five touched test files together at the end with:\n> ```sh\n> python -m pytest tools/tasktool/tests/test_model.py tools/tasktool/tests/test_serialize.py tools/tasktool/tests/test_migrate.py tools/tasktool/tests/test_v1_compat.py tools/tasktool/tests/test_schema_gen.py -q\n> ```\n\n---\n\n## Task 1 — Lifecycle start + model: new dataclasses and `SCHEMA_VERSION` bump\n\n### Step 1.1 — Start the slice worktree (before any source edit)\n\n- [ ] Run the lifecycle start command so all implementation happens in an isolated worktree:\n  ```sh\n  tasktool start P7.S1\n  ```\n  Expected: the command creates (or resumes) a worktree branch for `P7.S1`, prints the worktree path and branch, and marks the slice `in_progress`. **All subsequent edits and commits in this plan happen inside that worktree**, not in the main checkout. If `tasktool start` reports the slice is already in progress in an existing worktree, `cd` into that worktree and continue there.\n\n> Note: S1 does **not** add base-SHA *recording* logic to `start` — that is S4's scope. Here `tasktool start` is used purely as the normal lifecycle entry point.\n\n### Step 1.2 — Write failing test: new dataclasses + `Slice`/`Project` defaults + schema version\n\n- [ ] Open `tools/tasktool/tests/test_model.py`. Append the following test class at end of file:\n  ```python\n  class P7DataModelTests(unittest.TestCase):\n      def test_schema_version_is_3(self):\n          self.assertEqual(SCHEMA_VERSION, 3)\n\n      def test_reservation_dataclass(self):\n          from tasktool.model import Reservation\n          r = Reservation(resource=\"homepage-sort\", value=\"15\", scope=\"phase\")\n          self.assertEqual(r.resource, \"homepage-sort\")\n          self.assertEqual(r.value, \"15\")\n          self.assertEqual(r.scope, \"phase\")\n          self.assertIsNone(r.note)\n          r2 = Reservation(\n              resource=\"route-slug\", value=\"/offers\",\n              scope=\"project\", note=\"landing route\",\n          )\n          self.assertEqual(r2.note, \"landing route\")\n\n      def test_ledger_reservation_dataclass(self):\n          from tasktool.model import LedgerReservation\n          lr = LedgerReservation(\n              resource=\"homepage-sort\", value=\"15\", scope=\"project\",\n              note=None, owner_id=\"P20.S3\", owner_phase_id=\"P20\",\n              archived_date=\"2026-06-02\",\n          )\n          self.assertEqual(lr.owner_id, \"P20.S3\")\n          self.assertEqual(lr.owner_phase_id, \"P20\")\n          self.assertEqual(lr.archived_date, \"2026-06-02\")\n\n      def test_slice_p7_field_defaults(self):\n          s = Slice(id=\"S1\", title=\"x\", created=\"2026-06-02\")\n          self.assertEqual(s.integration_surfaces, [])\n          self.assertEqual(s.reservations, [])\n          self.assertIsNone(s.coordination_group)\n          self.assertIsNone(s.worktree_base_sha)\n          self.assertIsNone(s.landed_base_sha)\n\n      def test_slice_p7_fields_are_independent_lists(self):\n          a = Slice(id=\"S1\", title=\"x\", created=\"2026-06-02\")\n          b = Slice(id=\"S2\", title=\"y\", created=\"2026-06-02\")\n          a.integration_surfaces.append(\"cms-block-registry\")\n          a.reservations.append(\n              __import__(\"tasktool.model\", fromlist=[\"Reservation\"]).Reservation(\n                  resource=\"block-kind\", value=\"slider\", scope=\"phase\",\n              )\n          )\n          self.assertEqual(b.integration_surfaces, [])\n          self.assertEqual(b.reservations, [])\n\n      def test_project_reservations_ledger_default(self):\n          p = Project(project=\"demo\")\n          self.assertEqual(p.reservations_ledger, [])\n  ```\n\n### Step 1.2a — Update the existing stale schema-version assertion (REQUIRED)\n\n- [ ] In `tools/tasktool/tests/test_model.py`, there is a pre-existing module-level test (around line 107) that pins the **old** version:\n  ```python\n  def test_schema_version_is_2():\n      assert SCHEMA_VERSION == 2\n  ```\n  This will fail after the bump. **Rename and update it** so the existing current-version assertion tracks v3 (do not just leave the new `P7DataModelTests.test_schema_version_is_3` to coexist with a now-false sibling):\n  ```python\n  def test_schema_version_is_3():\n      assert SCHEMA_VERSION == 3\n  ```\n  (The bump itself is made in Step 1.4; authoring this edit now keeps the test red-then-green with the rest of Task 1.)\n\n### Step 1.3 — Run the failing test (expected FAIL)\n\n- [ ] Run:\n  ```sh\n  python -m pytest tools/tasktool/tests/test_model.py -q\n  ```\n  Expected: **FAIL** — `ImportError`/`AttributeError` for `Reservation` / `LedgerReservation`, `AssertionError: 2 != 3` for `SCHEMA_VERSION` (from both the new `P7DataModelTests.test_schema_version_is_3` and the renamed module-level `test_schema_version_is_3`), and `AttributeError` for the new `Slice`/`Project` attributes. Running the **whole file** (not just `::P7DataModelTests`) is required so the renamed module-level test is exercised too.\n\n### Step 1.4 — Implement: bump `SCHEMA_VERSION` in `model.py`\n\n- [ ] In `tools/tasktool/model.py`, change line 7:\n  ```python\n  SCHEMA_VERSION = 2\n  ```\n  to:\n  ```python\n  SCHEMA_VERSION = 3\n  ```\n\n### Step 1.5 — Implement: add `Reservation` and `LedgerReservation` dataclasses\n\n- [ ] In `tools/tasktool/model.py`, immediately **after** the `BlockedOn` dataclass (currently lines 58–61, ending before `@dataclass(slots=True)\\nclass Task:`), insert:\n  ```python\n  @dataclass(slots=True)\n  class Reservation:\n      resource: str\n      value: str\n      scope: Literal[\"phase\", \"project\"] = \"phase\"\n      note: str | None = None\n\n  @dataclass(slots=True)\n  class LedgerReservation:\n      resource: str\n      value: str\n      scope: Literal[\"phase\", \"project\"]\n      note: str | None\n      owner_id: str\n      owner_phase_id: str\n      archived_date: str\n  ```\n\n> Design note: `LedgerReservation` is `Reservation` + `{owner_id, owner_phase_id, archived_date}`. It is kept as a flat dataclass (not subclassing `Reservation`) because `slots=True` dataclass inheritance is fragile and the project's existing dataclasses (`Slice`, `CrossCutting`) likewise duplicate fields rather than subclass. The ledger fields are required (no defaults) — a ledger row is only ever constructed at archive time when all five identity fields are known (§4.A / §4.B), so there is no \"missing owner\" case to default.\n\n### Step 1.6 — Implement: add five `Slice` fields\n\n- [ ] In `tools/tasktool/model.py`, in the `Slice` dataclass, **after** the last worktree field (`worktree_prune_pending_at: str | None = None`, currently line 99), append:\n  ```python\n      integration_surfaces: list[str] = field(default_factory=list)\n      reservations: list[Reservation] = field(default_factory=list)\n      coordination_group: str | None = None\n      worktree_base_sha: str | None = None\n      landed_base_sha: str | None = None\n  ```\n\n### Step 1.7 — Implement: add `Project.reservations_ledger`\n\n- [ ] In `tools/tasktool/model.py`, in the `Project` dataclass, **after** `archived_cross_cutting: list[ArchivedCrossCutting] = field(default_factory=list)` (currently line 157), append:\n  ```python\n      reservations_ledger: list[LedgerReservation] = field(default_factory=list)\n  ```\n\n### Step 1.8 — Run the test (expected PASS)\n\n- [ ] Run the whole file so both the new class and the renamed module-level `test_schema_version_is_3` are exercised:\n  ```sh\n  python -m pytest tools/tasktool/tests/test_model.py -q\n  ```\n  Expected: **PASS** — including `P7DataModelTests` (6 tests) and the renamed module-level `test_schema_version_is_3`. Confirm there is **no** surviving `test_schema_version_is_2` (it was renamed in Step 1.2a, not duplicated).\n\n### Step 1.9 — Commit\n\n- [ ] Run:\n  ```sh\n  git add tools/tasktool/model.py tools/tasktool/tests/test_model.py\n  git commit -m \"P7.S1: add Reservation/LedgerReservation, Slice/Project fields, bump schema v3\"\n  ```\n\n---\n\n## Task 1b — Public API: export `Reservation` / `LedgerReservation`\n\n> Why: `tools/tasktool/__init__.py` re-exports every model dataclass (lines 4–16, `__all__` at 22–34) and `test_model.py::test_all_exports_present` asserts the public surface. The two new dataclasses must join that surface so downstream code can `from tasktool import Reservation, LedgerReservation` and the export test stays meaningful.\n\n### Step 1b.1 — Write failing test: new types are exported\n\n- [ ] Open `tools/tasktool/tests/test_model.py`. Find `test_all_exports_present` (around line 80) and add the two new names to its checked list so the loop reads:\n  ```python\n      def test_all_exports_present(self):\n          import tasktool\n          for name in [\n              \"load_project\", \"save_project\", \"dumps_canonical\", \"loads_project\",\n              \"Project\", \"Phase\", \"Slice\", \"Task\", \"CrossCutting\", \"BlockedOn\",\n              \"Status\", \"PlanningStatus\", \"ArchivedPhase\", \"ArchivedCrossCutting\",\n              \"SCHEMA_VERSION\", \"Reservation\", \"LedgerReservation\",\n          ]:\n              self.assertTrue(hasattr(tasktool, name), f\"tasktool.{name} missing\")\n  ```\n\n### Step 1b.2 — Run the failing test (expected FAIL)\n\n- [ ] Run:\n  ```sh\n  python -m pytest \"tools/tasktool/tests/test_model.py::PublicApiTests::test_all_exports_present\" -q\n  ```\n  (If the enclosing class is named differently, run the whole file: `python -m pytest tools/tasktool/tests/test_model.py -q`.)\n  Expected: **FAIL** — `AssertionError: tasktool.Reservation missing` (the names are not yet re-exported from `__init__.py`).\n\n### Step 1b.3 — Implement: add exports to `__init__.py`\n\n- [ ] In `tools/tasktool/__init__.py`, extend the `from tasktool.model import (...)` block (currently lines 4–16) to include the two new names, e.g. after `BlockedOn,`:\n  ```python\n      BlockedOn,\n      Reservation,\n      LedgerReservation,\n  ```\n- [ ] In the same file, extend `__all__` (currently lines 22–42) to include the two names, e.g. after `\"BlockedOn\",`:\n  ```python\n      \"BlockedOn\",\n      \"Reservation\",\n      \"LedgerReservation\",\n  ```\n\n### Step 1b.4 — Run the test (expected PASS)\n\n- [ ] Run:\n  ```sh\n  python -m pytest tools/tasktool/tests/test_model.py -q\n  ```\n  Expected: **PASS** — including `test_all_exports_present`.\n\n","exit_code":0,"status":"completed"}}
+{"type":"item.completed","item":{"id":"item_7","type":"agent_message","text":"The plan is long, and the implementation has eight slice commits plus an untracked reviewer chain. I’m narrowing next on the changed source/tests and the actual tracker status so findings are based on the finished code, not just the plan prose."}}
+{"type":"item.started","item":{"id":"item_8","type":"command_execution","command":"/usr/bin/zsh -lc 'git diff --stat main...HEAD && git diff --name-only main...HEAD'","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_8","type":"command_execution","command":"/usr/bin/zsh -lc 'git diff --stat main...HEAD && git diff --name-only main...HEAD'","aggregated_output":" tools/tasktool/__init__.py              |   4 +\n tools/tasktool/migrate.py               |  56 ++++++++++-\n tools/tasktool/model.py                 |  25 ++++-\n tools/tasktool/schema_gen.py            |  34 +++++++\n tools/tasktool/serialize.py             |  48 +++++++++-\n tools/tasktool/tests/test_migrate.py    | 123 ++++++++++++++++++++++++\n tools/tasktool/tests/test_model.py      |  59 +++++++++++-\n tools/tasktool/tests/test_schema_gen.py |  41 +++++++-\n tools/tasktool/tests/test_serialize.py  | 163 ++++++++++++++++++++++++++++++++\n tools/tasktool/tests/test_v1_compat.py  |  51 +++++++++-\n 10 files changed, 591 insertions(+), 13 deletions(-)\ntools/tasktool/__init__.py\ntools/tasktool/migrate.py\ntools/tasktool/model.py\ntools/tasktool/schema_gen.py\ntools/tasktool/serialize.py\ntools/tasktool/tests/test_migrate.py\ntools/tasktool/tests/test_model.py\ntools/tasktool/tests/test_schema_gen.py\ntools/tasktool/tests/test_serialize.py\ntools/tasktool/tests/test_v1_compat.py\n","exit_code":0,"status":"completed"}}
+{"type":"item.started","item":{"id":"item_9","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba tools/tasktool/model.py | sed -n '1,230p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.started","item":{"id":"item_10","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba tools/tasktool/migrate.py | sed -n '1,380p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.started","item":{"id":"item_11","type":"command_execution","command":"/usr/bin/zsh -lc \"python - <<'PY'\nimport json\nfrom pathlib import Path\np=json.loads(Path('docs/tasklist.json').read_text())\nfor ph in p.get('phases',[]):\n  if ph.get('id')=='P7':\n    print(json.dumps(ph, indent=2))\nPY\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.started","item":{"id":"item_12","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba tools/tasktool/serialize.py | sed -n '1,260p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.started","item":{"id":"item_13","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba tools/tasktool/schema_gen.py | sed -n '1,260p'\"","aggregated_output":"","exit_code":null,"status":"in_progress"}}
+{"type":"item.completed","item":{"id":"item_13","type":"command_execution","command":"/usr/bin/zsh -lc \"nl -ba tools/tasktool/schema_gen.py | sed -n '1,260p'\"","aggregated_output":"     1\t# tools/tasktool/schema_gen.py\n     2\t\"\"\"Generate a JSON Schema (draft 2020-12) describing tasklist.json.\"\"\"\n     3\tfrom __future__ import annotations\n     4\timport json\n     5\tfrom tasktool.model import SCHEMA_VERSION\n     6\t\n     7\tdef build_schema() -> dict:\n     8\t    task_status_enum = [\"ready\", \"in_progress\", \"done\"]\n     9\t    phase_status_enum = [\"ready\", \"in_progress\", \"done\", \"cancelled\"]\n    10\t    cross_status_enum = [\"ready\", \"in_progress\", \"done\", \"cancelled\"]\n    11\t    slice_status_enum = [\"ready\", \"in_progress\", \"blocked\", \"done\", \"cancelled\"]\n    12\t    planning_status_enum = [\"proposed\", \"ratified\", \"superseded\"]\n    13\t    date_str = {\"type\": \"string\", \"pattern\": r\"^\\d{4}-\\d{2}-\\d{2}$\"}\n    14\t    nullable_date = {\"oneOf\": [date_str, {\"type\": \"null\"}]}\n    15\t    blocked_on = {\n    16\t        \"oneOf\": [\n    17\t            {\"type\": \"null\"},\n    18\t            {\n    19\t                \"type\": \"object\",\n    20\t                \"required\": [\"kind\", \"value\"],\n    21\t                \"properties\": {\n    22\t                    \"kind\": {\"enum\": [\"id\", \"external\"]},\n    23\t                    \"value\": {\"type\": \"string\"},\n    24\t                },\n    25\t                \"additionalProperties\": False,\n    26\t            },\n    27\t        ],\n    28\t    }\n    29\t    reservation = {\n    30\t        \"type\": \"object\",\n    31\t        \"required\": [\"resource\", \"value\"],\n    32\t        \"properties\": {\n    33\t            \"resource\": {\"type\": \"string\"},\n    34\t            \"value\": {\"type\": \"string\"},\n    35\t            \"scope\": {\"enum\": [\"phase\", \"project\"]},\n    36\t            \"note\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n    37\t        },\n    38\t        \"additionalProperties\": False,\n    39\t    }\n    40\t    ledger_reservation = {\n    41\t        \"type\": \"object\",\n    42\t        \"required\": [\n    43\t            \"resource\", \"value\", \"scope\", \"owner_id\",\n    44\t            \"owner_phase_id\", \"archived_date\",\n    45\t        ],\n    46\t        \"properties\": {\n    47\t            \"resource\": {\"type\": \"string\"},\n    48\t            \"value\": {\"type\": \"string\"},\n    49\t            \"scope\": {\"enum\": [\"phase\", \"project\"]},\n    50\t            \"note\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n    51\t            \"owner_id\": {\"type\": \"string\"},\n    52\t            \"owner_phase_id\": {\"type\": \"string\"},\n    53\t            \"archived_date\": date_str,\n    54\t        },\n    55\t        \"additionalProperties\": False,\n    56\t    }\n    57\t    task = {\n    58\t        \"type\": \"object\",\n    59\t        \"required\": [\"id\", \"title\", \"created\", \"status\"],\n    60\t        \"properties\": {\n    61\t            \"id\": {\"type\": \"string\", \"pattern\": r\"^T\\d+$\"},\n    62\t            \"title\": {\"type\": \"string\"},\n    63\t            \"created\": date_str,\n    64\t            \"started\": nullable_date,\n    65\t            \"status\": {\"enum\": task_status_enum},\n    66\t            \"closed\": nullable_date,\n    67\t            \"refs\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}},\n    68\t            \"notes\": {\"type\": \"string\"},\n    69\t        },\n    70\t        \"additionalProperties\": False,\n    71\t    }\n    72\t    slice_ = {\n    73\t        \"type\": \"object\",\n    74\t        \"required\": [\"id\", \"title\", \"created\", \"status\"],\n    75\t        \"properties\": {\n    76\t            \"id\": {\"type\": \"string\", \"pattern\": r\"^S\\d+[a-z]?$\"},\n    77\t            \"title\": {\"type\": \"string\"},\n    78\t            \"created\": date_str,\n    79\t            \"started\": nullable_date,\n    80\t            \"status\": {\"enum\": slice_status_enum},\n    81\t            \"closed\": nullable_date,\n    82\t            \"blocked_on\": blocked_on,\n    83\t            \"depends_on\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}},\n    84\t            \"planning_status\": {\"enum\": planning_status_enum},\n    85\t            \"parallel_group\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n    86\t            \"plan_path\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n    87\t            \"refs\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}},\n    88\t            \"notes\": {\"type\": \"string\"},\n    89\t            \"reviewer_chain\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n    90\t            \"tasks\": {\"type\": \"array\", \"items\": task},\n    91\t            \"worktree_path\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n    92\t            \"worktree_branch\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n    93\t            \"worktree_in_place\": {\"type\": \"boolean\"},\n    94\t            \"worktree_pruned_at\": {\"oneOf\": [date_str, {\"type\": \"null\"}]},\n    95\t            \"worktree_prune_pending\": {\"type\": \"boolean\"},\n    96\t            \"worktree_prune_pending_at\": {\"oneOf\": [date_str, {\"type\": \"null\"}]},\n    97\t            \"workflow_step\": {\"oneOf\": [\n    98\t                {\"enum\": [\"spec\", \"plan\", \"implement\", \"done\"]},\n    99\t                {\"type\": \"null\"},\n   100\t            ]},\n   101\t            \"review_active\": {\"type\": \"boolean\"},\n   102\t            \"review_stage\": {\"oneOf\": [\n   103\t                {\"enum\": [\"awaiting_response\", \"applying_fixes\", \"passed\"]},\n   104\t                {\"type\": \"null\"},\n   105\t            ]},\n   106\t            \"integration_surfaces\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}},\n   107\t            \"reservations\": {\"type\": \"array\", \"items\": reservation},\n   108\t            \"coordination_group\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n   109\t            \"worktree_base_sha\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n   110\t            \"landed_base_sha\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n   111\t        },\n   112\t        \"additionalProperties\": False,\n   113\t    }\n   114\t    phase = {\n   115\t        \"type\": \"object\",\n   116\t        \"required\": [\"id\", \"title\", \"created\", \"status\"],\n   117\t        \"properties\": {\n   118\t            \"id\": {\"type\": \"string\", \"pattern\": r\"^P\\d+$\"},\n   119\t            \"title\": {\"type\": \"string\"},\n   120\t            \"created\": date_str,\n   121\t            \"started\": nullable_date,\n   122\t            \"status\": {\"enum\": phase_status_enum},\n   123\t            \"closed\": nullable_date,\n   124\t            \"spec_path\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n   125\t            \"plan_path\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n   126\t            \"planning_path\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n   127\t            \"phase_reviewer_chain\": {\"oneOf\": [{\"type\": \"string\"}, {\"type\": \"null\"}]},\n   128\t            \"notes\": {\"type\": \"string\"},\n   129\t            \"slices\": {\"type\": \"array\", \"items\": slice_},\n   130\t            \"workflow_step\": {\"oneOf\": [\n   131\t                {\"enum\": [\"spec\", \"ready\", \"in_progress\", \"done\"]},\n   132\t                {\"type\": \"null\"},\n   133\t            ]},\n   134\t        },\n   135\t        \"additionalProperties\": False,\n   136\t    }\n   137\t    cross = {\n   138\t        \"type\": \"object\",\n   139\t        \"required\": [\"id\", \"title\", \"created\", \"status\"],\n   140\t        \"properties\": {\n   141\t            \"id\": {\"type\": \"string\", \"pattern\": r\"^X\\d+$\"},\n   142\t            \"title\": {\"type\": \"string\"},\n   143\t            \"created\": date_str,\n   144\t            \"started\": nullable_date,\n   145\t            \"status\": {\"enum\": cross_status_enum},\n   146\t            \"closed\": nullable_date,\n   147\t            \"refs\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}},\n   148\t            \"

[… 303841 bytes elided to fit cap of 160000 bytes …]

 slot",
+  323	          }])
+  324	          self.assertEqual(slc["coordination_group"], "cms")
+  325	          self.assertEqual(slc["worktree_base_sha"], "abc123")
+  326	          self.assertEqual(slc["landed_base_sha"], "def456")
+  327	
+  328	      def test_non_default_reservations_ledger_is_kept(self):
+  329	          from tasktool.model import LedgerReservation
+  330	          p = Project(project="demo")
+  331	          p.reservations_ledger.append(LedgerReservation(
+  332	              resource="route-slug", value="/offers", scope="project",
+  333	              note=None, owner_id="P20.S3", owner_phase_id="P20",
+  334	              archived_date="2026-06-02",
+  335	          ))
+  336	          out = to_dict(p)
+  337	          self.assertEqual(out["reservations_ledger"], [{
+  338	              "resource": "route-slug", "value": "/offers", "scope": "project",
+  339	              "note": None, "owner_id": "P20.S3", "owner_phase_id": "P20",
+  340	              "archived_date": "2026-06-02",
+  341	          }])
+  342	  ```
+  343	
+  344	### Step 2.2 — Run the failing test (expected FAIL)
+  345	
+  346	- [ ] Run:
+  347	  ```sh
+  348	  python -m pytest tools/tasktool/tests/test_serialize.py::P7OmitWhenDefaultTests -q
+  349	  ```
+  350	  Expected: **FAIL** — `test_default_slice_omits_new_keys` and `test_default_project_omits_reservations_ledger` fail because `asdict()` currently emits the new default-valued keys, and `test_schema_version_serialized_as_3` would already pass via SCHEMA_VERSION but the omit tests fail. (`test_non_default_*` may already pass since `asdict` serializes nested dataclasses, but the omit tests gate this task.)
+  351	
+  352	### Step 2.3 — Implement: extend the slice omit map
+  353	
+  354	- [ ] In `tools/tasktool/serialize.py`, **after** the `_WORKFLOW_DEFAULT_OMIT` dict (currently ends line 39) and its `_strip_workflow_defaults` function (ends line 50), add a new omit map + stripper for the P7 fields:
+  355	  ```python
+  356	  _P7_DEFAULT_OMIT = {
+  357	      "coordination_group": None,
+  358	      "worktree_base_sha": None,
+  359	      "landed_base_sha": None,
+  360	  }
+  361	
+  362	
+  363	  def _strip_p7_defaults(d: dict) -> dict:
+  364	      """Drop P7 slice keys whose values equal their dataclass default.
+  365	
+  366	      Empty integration_surfaces / reservations lists and None scalar fields
+  367	      are omitted so historical rows gain no churn on round-trip (spec §4.A F5).
+  368	      """
+  369	      for field, default in _P7_DEFAULT_OMIT.items():
+  370	          if field in d and d[field] == default:
+  371	              del d[field]
+  372	      if d.get("integration_surfaces") == []:
+  373	          d.pop("integration_surfaces", None)
+  374	      if d.get("reservations") == []:
+  375	          d.pop("reservations", None)
+  376	      return d
+  377	  ```
+  378	
+  379	### Step 2.4 — Implement: call the slice stripper + strip empty `reservations_ledger`
+  380	
+  381	- [ ] In `tools/tasktool/serialize.py`, inside `to_dict`, in the per-slice loop (currently lines 73–74), add the new stripper call so the loop reads:
+  382	  ```python
+  383	          for slc in phase.get("slices", []):
+  384	              _strip_worktree_defaults(slc)
+  385	              _strip_workflow_defaults(slc)
+  386	              _strip_p7_defaults(slc)
+  387	  ```
+  388	- [ ] In the same `to_dict`, **before** the `out["schema_version"] = SCHEMA_VERSION` line (currently line 79), add the project-level ledger strip:
+  389	  ```python
+  390	      # Omit reservations_ledger when empty so historical projects gain no churn.
+  391	      if out.get("reservations_ledger") == []:
+  392	          del out["reservations_ledger"]
+  393	  ```
+  394	
+  395	### Step 2.5 — Run the test (expected PASS)
+  396	
+  397	- [ ] Run:
+  398	  ```sh
+  399	  python -m pytest tools/tasktool/tests/test_serialize.py::P7OmitWhenDefaultTests -q
+  400	  ```
+  401	  Expected: **PASS** (5 passed).
+  402	
+  403	### Step 2.6 — Commit
+  404	
+  405	- [ ] Run:
+  406	  ```sh
+  407	  git add tools/tasktool/serialize.py tools/tasktool/tests/test_serialize.py
+  408	  git commit -m "P7.S1: omit P7 slice/project fields when default on serialize"
+  409	  ```
+  410	
+  411	---
+  412	
+  413	## Task 3 — Deserialize: tolerant `from_dict` for the new fields + round-trip
+  414	
+  415	### Step 3.1 — Write failing test: deserialize tolerance + round-trip
+  416	
+  417	- [ ] Open `tools/tasktool/tests/test_serialize.py`. Append at end of file:
+  418	  ```python
+  419	  class P7DeserializeTests(unittest.TestCase):
+  420	      def test_missing_keys_default_on_deserialize(self):
+  421	          # A row with none of the new keys (the v1/v2 historical shape).
+  422	          raw = {
+  423	              "project": "demo", "schema_version": 3,
+  424	              "phases": [{
+  425	                  "id": "P1", "title": "t", "created": "2026-06-02", "status": "ready",
+  426	                  "slices": [{
+  427	                      "id": "S1", "title": "t", "created": "2026-06-02",
+  428	                      "status": "ready",
+  429	                  }],
+  430	              }],
+  431	              "cross_cutting": [], "archived_phases": [], "archived_cross_cutting": [],
+  432	          }
+  433	          p = from_dict(raw)
+  434	          s = p.phases[0].slices[0]
+  435	          self.assertEqual(s.integration_surfaces, [])
+  436	          self.assertEqual(s.reservations, [])
+  437	          self.assertIsNone(s.coordination_group)
+  438	          self.assertIsNone(s.worktree_base_sha)
+  439	          self.assertIsNone(s.landed_base_sha)
+  440	          self.assertEqual(p.reservations_ledger, [])
+  441	
+  442	      def test_present_keys_deserialize_to_objects(self):
+  443	          from tasktool.model import Reservation, LedgerReservation
+  444	          raw = {
+  445	              "project": "demo", "schema_version": 3,
+  446	              "phases": [{
+  447	                  "id": "P1", "title": "t", "created": "2026-06-02", "status": "ready",
+  448	                  "slices": [{
+  449	                      "id": "S1", "title": "t", "created": "2026-06-02",
+  450	                      "status": "ready",
+  451	                      "integration_surfaces": ["cms-block-registry", "theme-tail-css"],
+  452	                      "reservations": [
+  453	                          {"resource": "homepage-sort", "value": "15",
+  454	                           "scope": "phase", "note": "hero"},
+  455	                          {"resource": "route-slug", "value": "/offers",
+  456	                           "scope": "project", "note": None},
+  457	                      ],
+  458	                      "coordination_group": "cms",
+  459	                      "worktree_base_sha": "abc123",
+  460	                      "landed_base_sha": "def456",
+  461	                  }],
+  462	              }],
+  463	              "cross_cutting": [], "archived_phases": [], "archived_cross_cutting": [],
+  464	              "reservations_ledger": [
+  465	                  {"resource": "block-kind", "value": "slider", "scope": "project",
+  466	                   "note": None, "owner_id": "P20.S2", "owner_phase_id": "P20",
+  467	                   "archived_date": "2026-06-01"},
+  468	              ],
+  469	          }
+  470	          p = from_dict(raw)
+  471	          s = p.phases[0].slices[0]
+  472	          self.assertEqual(s.integration_surfaces, ["cms-block-registry", "theme-tail-css"])
+  473	          self.assertEqual(s.reservations[0], Reservation(
+  474	              resource="homepage-sort", value="15", scope="phase", note="hero"))
+  475	          self.assertEqual(s.reservations[1], Reservation(
+  476	              resource="route-slug", value="/offers", scope="project", note=None))
+  477	          self.assertEqual(s.coordination_group, "cms")
+  478	          self.assertEqual(s.worktree_base_sha, "abc123")
+  479	          self.assertEqual(s.landed_base_sha, "def456")
+  480	          self.assertEqual(p.reservations_ledger[0], LedgerReservation(
+  481	              resource="block-kind", value="slider", scope="project", note=None,
+  482	              owner_id="P20.S2", owner_phase_id="P20", archived_date="2026-06-01"))
+  483	
+  484	      def test_full_roundtrip_with_p7_fields(self):
+  485	          from tasktool.model import Reservation, LedgerReservation
+  486	          p = Project(project="demo")
+  487	          ph = Phase(id="P1", title="phase", created="2026-06-02")
+  488	          ph.slices.append(Slice(
+  489	              id="S1", title="slice", created="2026-06-02",
+  490	              integration_surfaces=["cms-block-registry"],
+  491	              reservations=[Reservation(
+  492	                  resource="homepage-sort", value="15", scope="phase", note="hero")],
+  493	              coordination_group="cms",
+  494	              worktree_base_sha="abc123",
+  495	              landed_base_sha="def456",
+  496	          ))
+  497	          p.phases.append(ph)
+  498	          p.reservations_ledger.append(LedgerReservation(
+  499	              resource="block-kind", value="slider", scope="project", note=None,
+  500	              owner_id="P20.S2", owner_phase_id="P20", archived_date="2026-06-01"))
+  501	          back = from_dict(to_dict(p))
+  502	          self.assertEqual(back, p)
+  503	
+  504	      def test_default_roundtrip_equality(self):
+  505	          # A wholly-default project must round-trip to an equal object even
+  506	          # though the new keys are omitted on serialize.
+  507	          p = Project(project="demo")
+  508	          ph = Phase(id="P1", title="phase", created="2026-06-02")
+  509	          ph.slices.append(Slice(id="S1", title="slice", created="2026-06-02"))
+  510	          p.phases.append(ph)
+  511	          back = from_dict(to_dict(p))
+  512	          self.assertEqual(back, p)
+  513	  ```
+  514	
+  515	### Step 3.2 — Run the failing test (expected FAIL)
+  516	
+  517	- [ ] Run:
+  518	  ```sh
+  519	  python -m pytest tools/tasktool/tests/test_serialize.py::P7DeserializeTests -q
+  520	  ```
+  521	  Expected: **FAIL** — `from_dict` does not yet read the new keys, so deserialized `Slice` objects lack the attributes / they are dropped, and `Project` has no `reservations_ledger` argument (`TypeError` or attribute mismatch on equality).
+  522	
+  523	### Step 3.3 — Implement: reservation/ledger deserialization helpers
+  524	
+  525	- [ ] In `tools/tasktool/serialize.py`, update the model import (currently lines 5–10) to add `Reservation` and `LedgerReservation`:
+  526	  ```python
+  527	  from tasktool.model import (
+  528	      Project, Phase, Slice, Task, CrossCutting, ArchivedPhase,
+  529	      ArchivedCrossCutting, BlockedOn, Reservation, LedgerReservation,
+  530	      Status, PlanningStatus, SCHEMA_VERSION,
+  531	      SliceWorkflowStep, PhaseWorkflowStep, ReviewStage,
+  532	  )
+  533	  ```
+  534	- [ ] In `from_dict`, **before** the `_slice` inner function (currently defined at line 122), add two helpers (place them after `_blocked`, currently line 121):
+  535	  ```python
+  536	      def _reservation(rd):
+  537	          return Reservation(
+  538	              resource=rd["resource"], value=rd["value"],
+  539	              scope=rd.get("scope", "phase"), note=rd.get("note"),
+  540	          )
+  541	      def _ledger_reservation(rd):
+  542	          return LedgerReservation(
+  543	              resource=rd["resource"], value=rd["value"], scope=rd["scope"],
+  544	              note=rd.get("note"), owner_id=rd["owner_id"],
+  545	              owner_phase_id=rd["owner_phase_id"], archived_date=rd["archived_date"],
+  546	          )
+  547	  ```
+  548	
+  549	### Step 3.4 — Implement: populate the new `Slice` fields in `_slice`
+  550	
+  551	- [ ] In `from_dict`'s `_slice` function, **after** the `worktree_prune_pending_at=...` keyword argument (currently line 146) and before the closing `)`, add:
+  552	  ```python
+  553	              integration_surfaces=list(sd.get("integration_surfaces", [])),
+  554	              reservations=[_reservation(r) for r in sd.get("reservations", [])],
+  555	              coordination_group=sd.get("coordination_group"),
+  556	              worktree_base_sha=_strict_opt_str(sd.get("worktree_base_sha"), scope=scope, field="worktree_base_sha"),
+  557	              landed_base_sha=_strict_opt_str(sd.get("landed_base_sha"), scope=scope, field="landed_base_sha"),
+  558	  ```
+  559	
+  560	### Step 3.5 — Implement: populate `Project.reservations_ledger`
+  561	
+  562	- [ ] In `from_dict`'s final `return Project(...)` (currently lines 188–199), add the ledger argument after `archived_cross_cutting=[...]`:
+  563	  ```python
+  564	          reservations_ledger=[
+  565	              _ledger_reservation(r) for r in d.get("reservations_ledger", [])
+  566	          ],
+  567	  ```
+  568	
+  569	### Step 3.6 — Run the test (expected PASS)
+  570	
+  571	- [ ] Run:
+  572	  ```sh
+  573	  python -m pytest tools/tasktool/tests/test_serialize.py::P7DeserializeTests -q
+  574	  ```
+  575	  Expected: **PASS** (4 passed).
+  576	
+  577	### Step 3.7 — Run the full serialize suite (regression check)
+  578	
+  579	- [ ] Run:
+  580	  ```sh
+  581	  python -m pytest tools/tasktool/tests/test_serialize.py -q
+  582	  ```
+  583	  Expected: **PASS** — all pre-existing serialize tests plus the new `P7OmitWhenDefaultTests` and `P7DeserializeTests` classes.
+  584	
+  585	### Step 3.8 — Commit
+  586	
+  587	- [ ] Run:
+  588	  ```sh
+  589	  git add tools/tasktool/serialize.py tools/tasktool/tests/test_serialize.py
+  590	  git commit -m "P7.S1: deserialize P7 slice/project fields with missing-key tolerance"
+  591	  ```
+  592	
+  593	---
+  594	
+  595	## Task 4 — JSON Schema: add new fields to `schema_gen.py`
+  596	
+  597	> Why this task is required: `test_v1_compat.py::test_v1_validates_against_v3_schema_after_save` (renamed from `..._v2_...` in Task 6) and `test_schema_gen.py` validate serialized output against `build_schema()`, which uses `additionalProperties: False`. Without schema entries for the new keys, any project that *declares* a surface/reservation would fail schema validation. The schema must enumerate the new keys.
+  598	
+  599	### Step 4.1 — Write failing test: schema admits the new fields
+  600	
+
+[truncated: 602 additional lines]
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
+[truncated: 236 additional lines]
+
+<!-- superstar-prompt:end -->
\ No newline at end of file
diff --git a/docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/r1-2026-06-02T2356-primary-response.md b/docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/r1-2026-06-02T2356-primary-response.md
new file mode 100644
index 0000000..a2a7399
--- /dev/null
+++ b/docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/r1-2026-06-02T2356-primary-response.md
@@ -0,0 +1,35 @@
+# Review — 2026-06-02-P7-S1-data-model-migration.md (post-slice, round 1)
+
+- Target: `docs/plans/2026-06-02-P7-S1-data-model-migration.md`
+- Request: `docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/r1-2026-06-02T2356-primary-request.md`
+- Reviewer command: `reviewer-agent`
+- Reviewer provider: `codex`
+- Sandbox: repo read-only; scratch/output writable
+- Status: `ok`
+
+---
+
+1. Findings
+
+F1. Severity: important — Slice lifecycle evidence is not reflected in the tracker. The plan requires `tasktool start P7.S1` before source edits, expecting the slice to be marked `in_progress` and tied to the implementation worktree (`docs/plans/2026-06-02-P7-S1-data-model-migration.md:52-56`). The checked-in tracker still has `started: null` and `status: "ready"` for `P7.S1` (`docs/tasklist.json:271-272`), and its refs/reviewer chain still point only at the plan review (`docs/tasklist.json:265-270`). For a post-slice completion gate, this leaves the lifecycle state inconsistent with the completed implementation.
+
+2. Open questions / assumptions
+
+I assume the reviewed `docs/tasklist.json` is the intended tracker state for this worktree. If authoritative-checkout routing updated a different checkout, that state needs to be reconciled or attached as evidence before closeout.
+
+3. Suggested document edits
+
+Update/register the slice lifecycle evidence through `tasktool` so `P7.S1` no longer appears unstarted in the tracker. After this post-slice round is recorded, add the post-slice reviewer chain ref as the closeout evidence.
+
+4. Verification gaps / commands that should be run, if any
+
+I ran:
+- `python -m pytest tools/tasktool/tests/test_model.py tools/tasktool/tests/test_serialize.py tools/tasktool/tests/test_migrate.py tools/tasktool/tests/test_v1_compat.py tools/tasktool/tests/test_schema_gen.py -q` — 105 passed
+- `python -m pytest tools/tasktool/tests -q` — 700 passed
+- `python -m pytest -q` — 992 passed
+- `tasktool validate` — ok
+- `rg -n "schema_version.*2|SCHEMA_VERSION == 2|const.*2" tools/tasktool/tests` — only raw v2 fixtures
+
+Code acceptance looks satisfied; the remaining blocker is tracker/lifecycle evidence consistency.
+
+Overall verdict: revise
diff --git a/docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/r1-2026-06-02T2356-sweep1-request.md b/docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/r1-2026-06-02T2356-sweep1-request.md
new file mode 100644
index 0000000..f794c0d
--- /dev/null
+++ b/docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice/r1-2026-06-02T2356-sweep1-request.md
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
+/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s1-data-model-migration-schema-v3-surfaces
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
+docs/plans/2026-06-02-P7-S1-data-model-migration.md
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
+### docs/plans/2026-06-02-P7-S1-data-model-migration.md
+
+    1	# P7.S1 — Data Model + Migration (schema v3) Implementation Plan
+    2	
+    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
+    4	
+    5	**Goal:** Add integration-surface, scarce-reservation, coordination-group, and worktree base/landed-SHA fields to the `tasktool` data model and bump the on-disk schema to v3, with additive v1→v3 / v2→v3 migration and omit-when-default serialization so historical `tasklist.json` rows gain zero churn.
+    6	
+    7	**Architecture:** The change is in the model/serialization/drift-merge layer of the `tasktool` CLI (`tools/tasktool/`). New value objects `Reservation` and `LedgerReservation` are added as `@dataclass(slots=True)` types alongside the existing `BlockedOn`; five new fields are appended to `Slice` and one collection field to `Project`, and both new types are re-exported from the package `__init__`. Serialization mirrors the existing `_strip_worktree_defaults` / `_strip_workflow_defaults` omit-when-default convention so default-valued rows serialize byte-identically to today; deserialization is tolerant of missing keys (the additive migration path). The JSON Schema (`schema_gen.py`) is extended to admit the new keys, and the drift-merge walker (`migrate.py`) is extended to treat `reservations_ledger` as a **merge-aware, union/never-delete collection** (not a scalar) so reconciliation can never erase archived project-scoped reservations — keeping validation and drift-migration in lockstep, which the test suite enforces.
+    8	
+    9	**Tech Stack:** Python 3, dataclasses, pytest
+   10	
+   11	---
+   12	
+   13	## Scheduling
+   14	
+   15	P7.S1 has **no `depends_on`** — it is the foundation slice for phase P7. Per the governing spec (§5 slice decomposition table), S1 blocks S2, S3, S4, S6, and S7 (each of those declares `S1` among its dependencies). S1 itself depends on nothing, so it is **independently plannable and independently executable right now**: it only touches `model.py`, `__init__.py`, `serialize.py`, `schema_gen.py`, `migrate.py`, and their tests, none of which are being modified by a sibling slice in flight. No coordination group or reservation is required for S1 itself. Confirm before starting that no other P7 slice has begun mutating these source files (`tasktool worktree list --all`); if all clear, proceed.
+   16	
+   17	This slice writes **no** CLI commands, **no** scheduling/overlap logic, and **no** worktree base-SHA *recording* — it only defines the fields those later slices populate. `worktree_base_sha` / `landed_base_sha` are added as inert `None`-default fields here; the logic that stamps them ships in S4.
+   18	
+   19	---
+   20	
+   21	## File Structure
+   22	
+   23	| File | Responsibility | Change in this slice |
+   24	|------|----------------|----------------------|
+   25	| `tools/tasktool/model.py` | Dataclass definitions + `SCHEMA_VERSION` constant | Add `Reservation` and `LedgerReservation` dataclasses; add 5 fields to `Slice`; add `reservations_ledger` to `Project`; bump `SCHEMA_VERSION` 2 → 3 |
+   26	| `tools/tasktool/__init__.py` | Public package API (`from tasktool import ...`) + `__all__` | Export `Reservation` and `LedgerReservation` (mirrors how the other model dataclasses are re-exported at lines 4–16 / 22–34) |
+   27	| `tools/tasktool/serialize.py` | `to_dict` / `from_dict`, omit-when-default stripping, canonical dump/load | Strip new default-valued keys on serialize; deserialize new keys tolerantly (default when absent); nest `Reservation`/`LedgerReservation` (de)serialization |
+   28	| `tools/tasktool/schema_gen.py` | JSON Schema generator validated against on save | Add `integration_surfaces`, `reservations`, `coordination_group`, `worktree_base_sha`, `landed_base_sha` to the slice object; add `reservations_ledger` to the project object; define `reservation` / `ledger_reservation` sub-schemas |
+   29	| `tools/tasktool/migrate.py` | Drift diff/merge walker (`compute_deltas` / `apply_deltas`) + `walker_field_coverage()` | **Structural change required:** register `reservations_ledger` as a merge-aware collection (it is currently mis-classified as a *scalar* project field, which makes drift reconciliation able to erase archived reservations — see Task 5a). Add ledger-aware diff/merge keyed/deduped on `resource:value:scope:owner_id`. The `Slice`-field walker remains dynamic (`fields(Slice)`), so `test_walker_covers_every_dataclass_field` still passes for the slice fields |
+   30	| `tools/tasktool/tests/test_model.py` | Dataclass default / construction tests | New tests for the new dataclasses, new `Slice` field defaults, new `Project` field default, and `SCHEMA_VERSION == 3` |
+   31	| `tools/tasktool/tests/test_serialize.py` | Round-trip + omit-when-default + deserialize-tolerance tests | New round-trip, omit-when-default, and missing-key tolerance tests |
+   32	| `tools/tasktool/tests/test_migrate.py` | Drift-walker coverage + per-field migration acceptance | New per-field value pairs for the added fields so the parametrized acceptance test exercises them |
+   33	| `tools/tasktool/tests/test_v1_compat.py` | v1 legacy-row load + promotion compat | New v1→v3 and v2→v3 no-churn compat assertions |
+   34	
+   35	> **Source-of-truth note:** Edit **only** `tools/tasktool/`. `plugins/superstar/tools/tasktool/` is a synced copy maintained by release scripts — do **not** touch it in this slice.
+   36	
+   37	> **Test invocation (verified working from repo root):**
+   38	> ```sh
+   39	> python -m pytest tools/tasktool/tests/<file> -q
+   40	> ```
+   41	> Root `pyproject.toml` sets `addopts = "--import-mode=importlib"` and `testpaths` includes `tools/tasktool/tests`, so `tasktool` imports resolve without a `PYTHONPATH` export. Run all five touched test files together at the end with:
+   42	> ```sh
+   43	> python -m pytest tools/tasktool/tests/test_model.py tools/tasktool/tests/test_serialize.py tools/tasktool/tests/test_migrate.py tools/tasktool/tests/test_v1_compat.py tools/tasktool/tests/test_schema_gen.py -q
+   44	> ```
+   45	
+   46	---
+   47	
+   48	## Task 1 — Lifecycle start + model: new dataclasses and `SCHEMA_VERSION` bump
+   49	
+   50	### Step 1.1 — Start the slice worktree (before any source edit)
+   51	
+   52	- [ ] Run the lifecycle start command so all implementation happens in an isolated worktree:
+   53	  ```sh
+   54	  tasktool start P7.S1
+   55	  ```
+   56	  Expected: the command creates (or resumes) a worktree branch for `P7.S1`, prints the worktree path and branch, and marks the slice `in_progress`. **All subsequent edits and commits in this plan happen inside that worktree**, not in the main checkout. If `tasktool start` reports the slice is already in progress in an existing worktree, `cd` into that worktree and continue there.
+   57	
+   58	> Note: S1 does **not** add base-SHA *recording* logic to `start` — that is S4's scope. Here `tasktool start` is used purely as the normal lifecycle entry point.
+   59	
+   60	### Step 1.2 — Write failing test: new dataclasses + `Slice`/`Project` defaults + schema version
+   61	
+   62	- [ ] Open `tools/tasktool/tests/test_model.py`. Append the following test class at end of file:
+   63	  ```python
+   64	  class P7DataModelTests(unittest.TestCase):
+   65	      def test_schema_version_is_3(self):
+   66	          self.assertEqual(SCHEMA_VERSION, 3)
+   67	
+   68	      def test_reservation_dataclass(self):
+   69	          from tasktool.model import Reservation
+   70	          r = Reservation(resource="homepage-sort", value="15", scope="phase")
+   71	          self.assertEqual(r.resource, "homepage-sort")
+   72	          self.assertEqual(r.value, "15")
+   73	          self.assertEqual(r.scope, "phase")
+   74	          self.assertIsNone(r.note)
+   75	          r2 = Reservation(
+   76	              resource="route-slug", value="/offers",
+   77	              scope="project", note="landing route",
+   78	          )
+   79	          self.assertEqual(r2.note, "landing route")
+   80	
+   81	      def test_ledger_reservation_dataclass(self):
+   82	          from tasktool.model import LedgerReservation
+   83	          lr = LedgerReservation(
+   84	              resource="homepage-sort", value="15", scope="project",
+   85	              note=None, owner_id="P20.S3", owner_phase_id="P20",
+   86	              archived_date="2026-06-02",
+   87	          )
+   88	          self.assertEqual(lr.owner_id, "P20.S3")
+   89	          self.assertEqual(lr.owner_phase_id, "P20")
+   90	          self.assertEqual(lr.archived_date, "2026-06-02")
+   91	
+   92	      def test_slice_p7_field_defaults(self):
+   93	          s = Slice(id="S1", title="x", created="2026-06-02")
+   94	          self.assertEqual(s.integration_surfaces, [])
+   95	          self.assertEqual(s.reservations, [])
+   96	          self.assertIsNone(s.coordination_group)
+   97	          self.assertIsNone(s.worktree_base_sha)
+   98	          self.assertIsNone(s.landed_base_sha)
+   99	
+  100	      def test_slice_p7_fields_are_independent_lists(self):
+  101	          a = Slice(id="S1", title="x", created="2026-06-02")
+  102	          b = Slice(id="S2", title="y", created="2026-06-02")
+  103	          a.integration_surfaces.append("cms-block-registry")
+  104	          a.reservations.append(
+  105	              __import__("tasktool.model", fromlist=["Reservation"]).Reservation(
+  106	                  resource="block-kind", value="slider", scope="phase",
+  107	              )
+  108	          )
+  109	          self.assertEqual(b.integration_surfaces, [])
+  110	          self.assertEqual(b.reservations, [])
+  111	
+  112	      def test_project_reservations_ledger_default(self):
+  113	          p = Project(project="demo")
+  114	          self.assertEqual(p.reservations_ledger, [])
+  115	  ```
+  116	
+  117	### Step 1.2a — Update the existing stale schema-version assertion (REQUIRED)
+  118	
+  119	- [ ] In `tools/tasktool/tests/test_model.py`, there is a pre-existing module-level test (around line 107) that pins the **old** version:
+  120	  ```python
+  121	  def test_schema_version_is_2():
+  122	      assert SCHEMA_VERSION == 2
+  123	  ```
+  124	  This will fail after the bump. **Rename and update it** so the existing current-version assertion tracks v3 (do not just leave the new `P7DataModelTests.test_schema_version_is_3` to coexist with a now-false sibling):
+  125	  ```python
+  126	  def test_schema_version_is_3():
+  127	      assert SCHEMA_VERSION == 3
+  128	  ```
+  129	  (The bump itself is made in Step 1.4; authoring this edit now keeps the test red-then-green with the rest of Task 1.)
+  130	
+  131	### Step 1.3 — Run the failing test (expected FAIL)
+  132	
+  133	- [ ] Run:
+  134	  ```sh
+  135	  python -m pytest tools/tasktool/tests/test_model.py -q
+  136	  ```
+  137	  Expected: **FAIL** — `ImportError`/`AttributeError` for `Reservation` / `LedgerReservation`, `AssertionError: 2 != 3` for `SCHEMA_VERSION` (from both the new `P7DataModelTests.test_schema_version_is_3` and the renamed module-level `test_schema_version_is_3`), and `AttributeError` for the new `Slice`/`Project` attributes. Running the **whole file** (not just `::P7DataModelTests`) is required so the renamed module-level test is exercised too.
+  138	
+  139	### Step 1.4 — Implement: bump `SCHEMA_VERSION` in `model.py`
+  140	
+  141	- [ ] In `tools/tasktool/model.py`, change line 7:
+  142	  ```python
+  143	  SCHEMA_VERSION = 2
+  144	  ```
+  145	  to:
+  146	  ```python
+  147	  SCHEMA_VERSION = 3
+  148	  ```
+  149	
+  150	### Step 1.5 — Implement: add `Reservation` and `LedgerReservation` dataclasses
+  151	
+  152	- [ ] In `tools/tasktool/model.py`, immediately **after** the `BlockedOn` dataclass (currently lines 58–61, ending before `@dataclass(slots=True)\nclass Task:`), insert:
+  153	  ```python
+  154	  @dataclass(slots=True)
+  155	  class Reservation:
+  156	      resource: str
+  157	      value: str
+  158	      scope: Literal["phase", "project"] = "phase"
+  159	      note: str | None = None
+  160	
+  161	  @dataclass(slots=True)
+  162	  class LedgerReservation:
+  163	      resource: str
+  164	      value: str
+  165	      scope: Literal["phase", "project"]
+  166	      note: str | None
+  167	      owner_id: str
+  168	      owner_phase_id: str
+  169	      archived_date: str
+  170	  ```
+  171	
+  172	> Design note: `LedgerReservation` is `Reservation` + `{owner_id, owner_phase_id, archived_date}`. It is kept as a flat dataclass (not subclassing `Reservation`) because `slots=True` dataclass inheritance is fragile and the project's existing dataclasses (`Slice`, `CrossCutting`) likewise duplicate fields rather than subclass. The ledger fields are required (no defaults) — a ledger row is only ever constructed at archive time when all five identity fields are known (§4.A / §4.B), so there is no "missing owner" case to default.
+  173	
+  174	### Step 1.6 — Implement: add five `Slice` fields
+  175	
+  176	- [ ] In `tools/tasktool/model.py`, in the `Slice` dataclass, **after** the last worktree field (`worktree_prune_pending_at: str | None = None`, currently line 99), append:
+  177	  ```python
+  178	      integration_surfaces: list[str] = field(default_factory=list)
+  179	      reservations: list[Reservation] = field(default_factory=list)
+  180	      coordination_group: str | None = None
+  181	      worktree_base_sha: str | None = None
+  182	      landed_base_sha: str | None = None
+  183	  ```
+  184	
+  185	### Step 1.7 — Implement: add `Project.reservations_ledger`
+  186	
+  187	- [ ] In `tools/tasktool/model.py`, in the `Project` dataclass, **after** `archived_cross_cutting: list[ArchivedCrossCutting] = field(default_factory=list)` (currently line 157), append:
+  188	  ```python
+  189	      reservations_ledger: list[LedgerReservation] = field(default_factory=list)
+  190	  ```
+  191	
+  192	### Step 1.8 — Run the test (expected PASS)
+  193	
+  194	- [ ] Run the whole file so both the new class and the renamed module-level `test_schema_version_is_3` are exercised:
+  195	  ```sh
+  196	  python -m pytest tools/tasktool/tests/test_model.py -q
+  197	  ```
+  198	  Expected: **PASS** — including `P7DataModelTests` (6 tests) and the renamed module-level `test_schema_version_is_3`. Confirm there is **no** surviving `test_schema_version_is_2` (it was renamed in Step 1.2a, not duplicated).
+  199	
+  200	### Step 1.9 — Commit
+  201	
+  202	- [ ] Run:
+  203	  ```sh
+  204	  git add tools/tasktool/model.py tools/tasktool/tests/test_model.py
+  205	  git commit -m "P7.S1: add Reservation/LedgerReservation, Slice/Project fields, bump schema v3"
+  206	  ```
+  207	
+  208	---
+  209	
+  210	## Task 1b — Public API: export `Reservation` / `LedgerReservation`
+  211	
+  212	> Why: `tools/tasktool/__init__.py` re-exports every model dataclass (lines 4–16, `__all__` at 22–34) and `test_model.py::test_all_exports_present` asserts the public surface. The two new dataclasses must join that surface so downstream code can `from tasktool import Reservation, LedgerReservation` and the export test stays meaningful.
+  213	
+  214	### Step 1b.1 — Write failing test: new types are exported
+  215	
+  216	- [ ] Open `tools/tasktool/tests/test_model.py`. Find `test_all_exports_present` (around line 80) and add the two new names to its checked list so the loop reads:
+  217	  ```python
+  218	      def test_all_exports_present(self):
+  219	          import tasktool
+  220	          for name in [
+  221	              "load_project", "save_project", "dumps_canonical", "loads_project",
+  222	              "Project", "Phase", "Slice", "Task", "CrossCutting", "BlockedOn",
+  223	              "Status", "PlanningStatus", "ArchivedPhase", "ArchivedCrossCutting",
+  224	              "SCHEMA_VERSION", "Reservation", "LedgerReservation",
+  225	          ]:
+  226	              self.assertTrue(hasattr(tasktool, name), f"tasktool.{name} missing")
+  227	  ```
+  228	
+  229	### Step 1b.2 — Run the failing test (expected FAIL)
+  230	
+  231	- [ ] Run:
+  232	  ```sh
+  233	  python -m pytest "tools/tasktool/tests/test_model.py::PublicApiTests::test_all_exports_present" -q
+  234	  ```
+  235	  (If the enclosing class is named differently, run the whole file: `python -m pytest tools/tasktool/tests/test_model.py -q`.)
+  236	  Expected: **FAIL** — `AssertionError: tasktool.Reservation missing` (the names are not yet re-exported from `__init__.py`).
+  237	
+  238	### Step 1b.3 — Implement: add exports to `__init__.py`
+  239	
+  240	- [ ] In `tools/tasktool/__init__.py`, extend the `from tasktool.model import (...)` block (currently lines 4–16) to include the two new names, e.g. after `BlockedOn,`:
+  241	  ```python
+  242	      BlockedOn,
+  243	      Reservation,
+  244	      LedgerReservation,
+  245	  ```
+  246	- [ ] In the same file, extend `__all__` (currently lines 22–42) to include the two names, e.g. after `"BlockedOn",`:
+  247	  ```python
+  248	      "BlockedOn",
+  249	      "Reservation",
+  250	      "LedgerReservation",
+  251	  ```
+  252	
+  253	### Step 1b.4 — Run the test (expected PASS)
+  254	
+  255	- [ ] Run:
+  256	  ```sh
+  257	  python -m pytest tools/tasktool/tests/test_model.py -q
+  258	  ```
+  259	  Expected: **PASS** — including `test_all_exports_present`.
+  260	
+  261	### Step 1b.5 — Commit
+  262	
+  263	- [ ] Run:
+  264	  ```sh
+  265	  git add tools/tasktool/__init__.py tools/tasktool/tests/test_model.py
+  266	  git commit -m "P7.S1: export Reservation/LedgerReservation from tasktool package"
+  267	  ```
+  268	
+  269	---
+  270	
+  271	## Task 2 — Serialize: omit-when-default for the new fields + nested reservation (de)serialization
+  272	
+  273	### Step 2.1 — Write failing test: omit-when-default on serialize
+  274	
+  275	- [ ] Open `tools/tasktool/tests/test_serialize.py`. Append at end of file:
+  276	  ```python
+  277	  class P7OmitWhenDefaultTests(unittest.TestCase):
+  278	      def test_default_slice_omits_new_keys(self):
+  279	          p = Project(project="demo")
+  280	          ph = Phase(id="P1", title="phase", created="2026-06-02")
+  281	          ph.slices.append(Slice(id="S1", title="slice", created="2026-06-02"))
+  282	          p.phases.append(ph)
+  283	          out = to_dict(p)
+  284	          slc = out["phases"][0]["slices"][0]
+  285	          for key in (
+  286	              "integration_surfaces", "reservations", "coordination_group",
+  287	              "worktree_base_sha", "landed_base_sha",
+  288	          ):
+  289	              self.assertNotIn(key, slc, f"{key} should be omitted when default")
+  290	
+  291	      def test_default_project_omits_reservations_ledger(self):
+  292	          p = Project(project="demo")
+  293	          out = to_dict(p)
+  294	          self.assertNotIn("reservations_ledger", out)
+  295	
+  296	      def test_schema_version_serialized_as_3(self):
+  297	          p = Project(project="demo")
+  298	          out = to_dict(p)
+  299	          self.assertEqual(out["schema_version"], 3)
+  300	
+  301	      def test_non_default_slice_keys_are_kept(self):
+  302	          from tasktool.model import Reservation
+  303	          p = Project(project="demo")
+  304	          ph = Phase(id="P1", title="phase", created="2026-06-02")
+  305	          s = Slice(
+  306	              id="S1", title="slice", created="2026-06-02",
+  307	              integration_surfaces=["cms-block-registry"],
+  308	              reservations=[Reservation(
+  309	                  resource="homepage-sort", value="15", scope="phase",
+  310	                  note="hero slot",
+  311	              )],
+  312	              coordination_group="cms",
+  313	              worktree_base_sha="abc123",
+  314	              landed_base_sha="def456",
+  315	          )
+  316	          ph.slices.append(s)
+  317	          p.phases.append(ph)
+  318	          slc = to_dict(p)["phases"][0]["slices"][0]
+  319	          self.assertEqual(slc["integration_surfaces"], ["cms-block-registry"])
+  320	          self.assertEqual(slc["reservations"], [{
+  321	              "resource": "homepage-sort", "value": "15",
+  322	              "scope": "phase", "note": "hero slot",
+  323	          }])
+  324	          self.assertEqual(slc["coordination_group"], "cms")
+  325	          self.assertEqual(slc["worktree_base_sha"], "abc123")
+  326	          self.assertEqual(slc["landed_base_sha"], "def456")
+  327	
+  328	      def test_non_default_reservations_ledger_is_kept(self):
+  329	          from tasktool.model import LedgerReservation
+  330	          p = Project(project="demo")
+  331	          p.reservations_ledger.append(LedgerReservation(
+  332	              resource="route-slug", value="/offers", scope="project",
+  333	              note=None, owner_id="P20.S3", owner_phase_id="P20",
+  334	              archived_date="2026-06-02",
+  335	          ))
+  336	          out = to_dict(p)
+  337	          self.assertEqual(out["reservations_ledger"], [{
+  338	              "resource": "route-slug", "value": "/offers", "scope": "project",
+  339	              "note": None, "owner_id": "P20.S3", "owner_phase_id": "P20",
+  340	              "archived_date": "2026-06-02",
+  341	          }])
+  342	  ```
+  343	
+  344	### Step 2.2 — Run the failing test (expected FAIL)
+  345	
+  346	- [ ] Run:
+  347	  ```sh
+  348	  python -m pytest tools/tasktool/tests/test_serialize.py::P7OmitWhenDefaultTests -q
+  349	  ```
+  350	  Expected: **FAIL** — `test_default_slice_omits_new_keys` and `test_default_project_omits_reservations_ledger` fail because `asdict()` currently emits the new default-valued keys, and `test_schema_version_serialized_as_3` would already pass via SCHEMA_VERSION but the omit tests fail. (`test_non_default_*` may already pass since `asdict` serializes nested dataclasses, but the omit tests gate this task.)
+  351	
[truncated: 884 additional lines]


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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s1-data-model-migration-schema-v3-surfaces

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-02-P7-S1-data-model-migration.md

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

### docs/plans/2026-06-02-P7-S1-data-model-migration.md

    1	# P7.S1 — Data Model + Migration (schema v3) Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Add integration-surface, scarce-reservation, coordination-group, and worktree base/landed-SHA fields to the `tasktool` data model and bump the on-disk schema to v3, with additive v1→v3 / v2→v3 migration and omit-when-default serialization so historical `tasklist.json` rows gain zero churn.
    6	
    7	**Architecture:** The change is in the model/serialization/drift-merge layer of the `tasktool` CLI (`tools/tasktool/`). New value objects `Reservation` and `LedgerReservation` are added as `@dataclass(slots=True)` types alongside the existing `BlockedOn`; five new fields are appended to `Slice` and one collection field to `Project`, and both new types are re-exported from the package `__init__`. Serialization mirrors the existing `_strip_worktree_defaults` / `_strip_workflow_defaults` omit-when-default convention so default-valued rows serialize byte-identically to today; deserialization is tolerant of missing keys (the additive migration path). The JSON Schema (`schema_gen.py`) is extended to admit the new keys, and the drift-merge walker (`migrate.py`) is extended to treat `reservations_ledger` as a **merge-aware, union/never-delete collection** (not a scalar) so reconciliation can never erase archived project-scoped reservations — keeping validation and drift-migration in lockstep, which the test suite enforces.
    8	
    9	**Tech Stack:** Python 3, dataclasses, pytest
   10	
   11	---
   12	
   13	## Scheduling
   14	
   15	P7.S1 has **no `depends_on`** — it is the foundation slice for phase P7. Per the governing spec (§5 slice decomposition table), S1 blocks S2, S3, S4, S6, and S7 (each of those declares `S1` among its dependencies). S1 itself depends on nothing, so it is **independently plannable and independently executable right now**: it only touches `model.py`, `__init__.py`, `serialize.py`, `schema_gen.py`, `migrate.py`, and their tests, none of which are being modified by a sibling slice in flight. No coordination group or reservation is required for S1 itself. Confirm before starting that no other P7 slice has begun mutating these source files (`tasktool worktree list --all`); if all clear, proceed.
   16	
   17	This slice writes **no** CLI commands, **no** scheduling/overlap logic, and **no** worktree base-SHA *recording* — it only defines the fields those later slices populate. `worktree_base_sha` / `landed_base_sha` are added as inert `None`-default fields here; the logic that stamps them ships in S4.
   18	
   19	---
   20	
   21	## File Structure
   22	
   23	| File | Responsibility | Change in this slice |
   24	|------|----------------|----------------------|
   25	| `tools/tasktool/model.py` | Dataclass definitions + `SCHEMA_VERSION` constant | Add `Reservation` and `LedgerReservation` dataclasses; add 5 fields to `Slice`; add `reservations_ledger` to `Project`; bump `SCHEMA_VERSION` 2 → 3 |
   26	| `tools/tasktool/__init__.py` | Public package API (`from tasktool import ...`) + `__all__` | Export `Reservation` and `LedgerReservation` (mirrors how the other model dataclasses are re-exported at lines 4–16 / 22–34) |
   27	| `tools/tasktool/serialize.py` | `to_dict` / `from_dict`, omit-when-default stripping, canonical dump/load | Strip new default-valued keys on serialize; deserialize new keys tolerantly (default when absent); nest `Reservation`/`LedgerReservation` (de)serialization |
   28	| `tools/tasktool/schema_gen.py` | JSON Schema generator validated against on save | Add `integration_surfaces`, `reservations`, `coordination_group`, `worktree_base_sha`, `landed_base_sha` to the slice object; add `reservations_ledger` to the project object; define `reservation` / `ledger_reservation` sub-schemas |
   29	| `tools/tasktool/migrate.py` | Drift diff/merge walker (`compute_deltas` / `apply_deltas`) + `walker_field_coverage()` | **Structural change required:** register `reservations_ledger` as a merge-aware collection (it is currently mis-classified as a *scalar* project field, which makes drift reconciliation able to erase archived reservations — see Task 5a). Add ledger-aware diff/merge keyed/deduped on `resource:value:scope:owner_id`. The `Slice`-field walker remains dynamic (`fields(Slice)`), so `test_walker_covers_every_dataclass_field` still passes for the slice fields |
   30	| `tools/tasktool/tests/test_model.py` | Dataclass default / construction tests | New tests for the new dataclasses, new `Slice` field defaults, new `Project` field default, and `SCHEMA_VERSION == 3` |
   31	| `tools/tasktool/tests/test_serialize.py` | Round-trip + omit-when-default + deserialize-tolerance tests | New round-trip, omit-when-default, and missing-key tolerance tests |
   32	| `tools/tasktool/tests/test_migrate.py` | Drift-walker coverage + per-field migration acceptance | New per-field value pairs for the added fields so the parametrized acceptance test exercises them |
   33	| `tools/tasktool/tests/test_v1_compat.py` | v1 legacy-row load + promotion compat | New v1→v3 and v2→v3 no-churn compat assertions |
   34	
   35	> **Source-of-truth note:** Edit **only** `tools/tasktool/`. `plugins/superstar/tools/tasktool/` is a synced copy maintained by release scripts — do **not** touch it in this slice.
   36	
   37	> **Test invocation (verified working from repo root):**
   38	> ```sh
   39	> python -m pytest tools/tasktool/tests/<file> -q
   40	> ```
   41	> Root `pyproject.toml` sets `addopts = "--import-mode=importlib"` and `testpaths` includes `tools/tasktool/tests`, so `tasktool` imports resolve without a `PYTHONPATH` export. Run all five touched test files together at the end with:
   42	> ```sh
   43	> python -m pytest tools/tasktool/tests/test_model.py tools/tasktool/tests/test_serialize.py tools/tasktool/tests/test_migrate.py tools/tasktool/tests/test_v1_compat.py tools/tasktool/tests/test_schema_gen.py -q
   44	> ```
   45	
   46	---
   47	
   48	## Task 1 — Lifecycle start + model: new dataclasses and `SCHEMA_VERSION` bump
   49	
   50	### Step 1.1 — Start the slice worktree (before any source edit)
   51	
   52	- [ ] Run the lifecycle start command so all implementation happens in an isolated worktree:
   53	  ```sh
   54	  tasktool start P7.S1
   55	  ```
   56	  Expected: the command creates (or resumes) a worktree branch for `P7.S1`, prints the worktree path and branch, and marks the slice `in_progress`. **All subsequent edits and commits in this plan happen inside that worktree**, not in the main checkout. If `tasktool start` reports the slice is already in progress in an existing worktree, `cd` into that worktree and continue there.
   57	
   58	> Note: S1 does **not** add base-SHA *recording* logic to `start` — that is S4's scope. Here `tasktool start` is used purely as the normal lifecycle entry point.
   59	
   60	### Step 1.2 — Write failing test: new dataclasses + `Slice`/`Project` defaults + schema version
   61	
   62	- [ ] Open `tools/tasktool/tests/test_model.py`. Append the following test class at end of file:
   63	  ```python
   64	  class P7DataModelTests(unittest.TestCase):
   65	      def test_schema_version_is_3(self):
   66	          self.assertEqual(SCHEMA_VERSION, 3)
   67	
   68	      def test_reservation_dataclass(self):
   69	          from tasktool.model import Reservation
   70	          r = Reservation(resource="homepage-sort", value="15", scope="phase")
   71	          self.assertEqual(r.resource, "homepage-sort")
   72	          self.assertEqual(r.value, "15")
   73	          self.assertEqual(r.scope, "phase")
   74	          self.assertIsNone(r.note)
   75	          r2 = Reservation(
   76	              resource="route-slug", value="/offers",
   77	              scope="project", note="landing route",
   78	          )
   79	          self.assertEqual(r2.note, "landing route")
   80	
   81	      def test_ledger_reservation_dataclass(self):
   82	          from tasktool.model import LedgerReservation
   83	          lr = LedgerReservation(
   84	              resource="homepage-sort", value="15", scope="project",
   85	              note=None, owner_id="P20.S3", owner_phase_id="P20",
   86	              archived_date="2026-06-02",
   87	          )
   88	          self.assertEqual(lr.owner_id, "P20.S3")
   89	          self.assertEqual(lr.owner_phase_id, "P20")
   90	          self.assertEqual(lr.archived_date, "2026-06-02")
   91	
   92	      def test_slice_p7_field_defaults(self):
   93	          s = Slice(id="S1", title="x", created="2026-06-02")
   94	          self.assertEqual(s.integration_surfaces, [])
   95	          self.assertEqual(s.reservations, [])
   96	          self.assertIsNone(s.coordination_group)
   97	          self.assertIsNone(s.worktree_base_sha)
   98	          self.assertIsNone(s.landed_base_sha)
   99	
  100	      def test_slice_p7_fields_are_independent_lists(self):
  101	          a = Slice(id="S1", title="x", created="2026-06-02")
  102	          b = Slice(id="S2", title="y", created="2026-06-02")
  103	          a.integration_surfaces.append("cms-block-registry")
  104	          a.reservations.append(
  105	              __import__("tasktool.model", fromlist=["Reservation"]).Reservation(
  106	                  resource="block-kind", value="slider", scope="phase",
  107	              )
  108	          )
  109	          self.assertEqual(b.integration_surfaces, [])
  110	          self.assertEqual(b.reservations, [])
  111	
  112	      def test_project_reservations_ledger_default(self):
  113	          p = Project(project="demo")
  114	          self.assertEqual(p.reservations_ledger, [])
  115	  ```
  116	
  117	### Step 1.2a — Update the existing stale schema-version assertion (REQUIRED)
  118	
  119	- [ ] In `tools/tasktool/tests/test_model.py`, there is a pre-existing module-level test (around line 107) that pins the **old** version:
  120	  ```python
  121	  def test_schema_version_is_2():
  122	      assert SCHEMA_VERSION == 2
  123	  ```
  124	  This will fail after the bump. **Rename and update it** so the existing current-version assertion tracks v3 (do not just leave the new `P7DataModelTests.test_schema_version_is_3` to coexist with a now-false sibling):
  125	  ```python
  126	  def test_schema_version_is_3():
  127	      assert SCHEMA_VERSION == 3
  128	  ```
  129	  (The bump itself is made in Step 1.4; authoring this edit now keeps the test red-then-green with the rest of Task 1.)
  130	
  131	### Step 1.3 — Run the failing test (expected FAIL)
  132	
  133	- [ ] Run:
  134	  ```sh
  135	  python -m pytest tools/tasktool/tests/test_model.py -q
  136	  ```
  137	  Expected: **FAIL** — `ImportError`/`AttributeError` for `Reservation` / `LedgerReservation`, `AssertionError: 2 != 3` for `SCHEMA_VERSION` (from both the new `P7DataModelTests.test_schema_version_is_3` and the renamed module-level `test_schema_version_is_3`), and `AttributeError` for the new `Slice`/`Project` attributes. Running the **whole file** (not just `::P7DataModelTests`) is required so the renamed module-level test is exercised too.
  138	
  139	### Step 1.4 — Implement: bump `SCHEMA_VERSION` in `model.py`
  140	
  141	- [ ] In `tools/tasktool/model.py`, change line 7:
  142	  ```python
  143	  SCHEMA_VERSION = 2
  144	  ```
  145	  to:
  146	  ```python
  147	  SCHEMA_VERSION = 3
  148	  ```
  149	
  150	### Step 1.5 — Implement: add `Reservation` and `LedgerReservation` dataclasses

[truncated: 1052 additional lines]

<!-- superstar-prompt:end -->