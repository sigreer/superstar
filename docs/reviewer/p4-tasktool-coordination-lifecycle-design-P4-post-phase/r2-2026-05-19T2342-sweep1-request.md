<!-- superstar-prompt:start -->
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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/p4-s2-lifecycle

Target kind:
post-phase

Review mode:
Post-phase review. Treat this as a closeout gate for a whole
phase. Compare the implementation, archive/TASKLIST updates, and verification
evidence against the phase spec/plan. Prioritize: unresolved acceptance
criteria, stale docs, missing archive notes, cross-cutting tracker drift,
deferred gates without justification, and regressions outside the phase scope.

Target document:
docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md

Additional context files:
- docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md
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

### docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md

    1	# P4 — Tasktool Coordination and Lifecycle Authority
    2	
    3	**Status:** proposed
    4	**Date:** 2026-05-19
    5	**TASKLIST entry:** `P4` in `docs/tasklist.json`
    6	
    7	## Objective
    8	
    9	Make `tasktool` the enforced authority for two workflow rules that are currently left to agent discipline:
   10	
   11	1. Parallel implementation worktrees must not own `docs/tasklist.json` mutations.
   12	2. Active slices and tasks must pass through `in_progress` instead of jumping from `ready` to `done`.
   13	
   14	The intended outcome is that agents can keep using normal `tasktool` commands from whatever checkout they are working in, but the tool decides where writes land and which lifecycle transitions are valid.
   15	
   16	## Problem
   17	
   18	`docs/tasklist.json` is the single source of truth, but linked implementation worktrees currently mutate their local copy. When those branches merge back to `main`, tasklist updates from multiple agents collide as byte-level JSON diffs. This is predictable because each worktree was forked from a stale snapshot of the tracker.
   19	
   20	The same workflow has a status-quality issue: agents rarely mark slices or tasks `in_progress`. Rows remain `ready` until they are closed, which makes `tasktool list --open`, `phase-status`, and human progress scans much less useful.
   21	
   22	These are not independent usability nits. They expose the same architectural gap: `tasktool` has the canonical data model, but it does not yet enforce the coordinator lifecycle strongly enough.
   23	
   24	## Design Summary
   25	
   26	`tasktool` gains two linked capabilities:
   27	
   28	- **Authoritative checkout routing.** Mutating commands invoked from implementation worktrees are applied to a configured authoritative checkout, normally the project `main` checkout. Every authoritative-mode write uses the same lock, including commands invoked directly from the authoritative checkout. Worker worktrees treat `docs/tasklist.json` as a read-only mirror.
   29	- **Lifecycle start enforcement.** `tasktool start <id>` becomes the normal way to begin work. Slice close is allowed only after a slice has been observed `in_progress`, unless an explicit bypass is supplied and recorded.
   30	
   31	The skills are updated to describe the new command surface, but correctness does not depend on prose. The CLI enforces the rules.
   32	
   33	## Configuration
   34	
   35	Add a tracked project config file:
   36	
   37	```json
   38	{
   39	  "schema_version": 1,
   40	  "tasklist": {
   41	    "mutation_mode": "authoritative-checkout",
   42	    "authoritative_branch": "main"
   43	  }
   44	}
   45	```
   46	
   47	The default path is `.tasktool/config.json`. This file is intended to be committed because it contains project policy only, not machine-local absolute paths. If no config exists, current behavior remains unchanged so existing projects do not break abruptly.
   48	
   49	Field semantics:
   50	
   51	- `mutation_mode`
   52	  - `local`: existing behavior; mutate the current checkout.
   53	  - `authoritative-checkout`: route mutating commands from linked worktrees to `authoritative_root`.
   54	- `authoritative_branch`: branch the authoritative checkout must be on when accepting writes.
   55	
   56	Machine-local root discovery:
   57	
   58	1. If `TASKTOOL_AUTHORITY_ROOT` is set, use it.
   59	2. Otherwise inspect `git worktree list --porcelain` and find the checkout whose branch is `authoritative_branch`.
   60	3. If exactly one checkout matches, use it.
   61	4. If none or more than one match, fail closed and print the exact `TASKTOOL_AUTHORITY_ROOT=/path/to/checkout` override to use.
   62	
   63	`tasktool config init-authority --branch main` writes or updates `.tasktool/config.json`. It does not write absolute paths. A separate untracked `.tasktool/local.json` may be added later, but P4 should not require it.
   64	
   65	## Mutating Commands
   66	
   67	The routing layer applies to all commands that write `docs/tasklist.json`:
   68	
   69	- `init`
   70	- `create phase|slice|task|cross`
   71	- `set`
   72	- `start`
   73	- `close`
   74	- `block`
   75	- `unblock`
   76	- `deps`
   77	- `ratify`
   78	- `planning-path`
   79	- `note`
   80	- `ref`
   81	- `title`
   82	- `archive-phase`
   83	- `import`
   84	- `validate --normalise`
   85	
   86	Read commands keep using the current checkout by default, but they should warn when authoritative routing is configured and the current worktree copy is older than the authoritative copy. A follow-up may add `--source authoritative|local`; P4 does not need it.
   87	
   88	## Routing Rules
   89	
   90	For every mutating command:
   91	
   92	1. Discover the current repository root and git common directory.
   93	2. Load `.tasktool/config.json` if present.
   94	3. If `mutation_mode` is absent or `local`, mutate the current checkout.
   95	4. Resolve `authoritative_root` via the machine-local discovery rules.
   96	5. Acquire an exclusive lock under the common git directory before loading tasklist data.
   97	6. Validate that `authoritative_root` exists, is a git checkout for the same repository, is on `authoritative_branch`, and has no unresolved merge.
   98	7. Validate that `authoritative_root/docs/tasklist.json` is not dirty in a way that cannot be attributed to tasktool's own current command.
   99	8. Load and mutate `authoritative_root/docs/tasklist.json`, even if the invocation already came from that checkout.
  100	9. Save canonical JSON and best-effort stage the authoritative path.
  101	10. Print a concise routing message only when the invocation root differs from the authoritative root.
  102	
  103	The implementation should centralize this routing in one module so command functions do not each grow git-worktree logic.
  104	
  105	The lock is mandatory for every authoritative-mode mutation. Direct `main` checkout invocations and worker-routed invocations contend on the same lock, preventing interleaved read-modify-write cycles.
  106	
  107	## Two-Root Command Contract
  108	
  109	Commands in authoritative mode have two roots:
  110	
  111	- `invocation_root`: the checkout where the user or agent ran the command.
  112	- `write_root`: the authoritative checkout whose `docs/tasklist.json` is mutated.
  113	
  114	User-supplied file paths and reviewer-chain discovery are interpreted relative to `invocation_root`. Tasklist load/save/stage happens in `write_root`. This applies to `close` and to `set --status done`, because both routes can invoke review-gate checks.
  115	
  116	Explicit reviewer-chain paths may be absolute or relative, but they must resolve inside `invocation_root`. Paths outside the repository are refused. The value recorded into tasklist is always repo-relative from `invocation_root`.
  117	
  118	## Reviewer Chains From Worktrees
  119	
  120	`tasktool close <slice-id>` and `tasktool set <id> --status done` must preserve review-gate semantics when invoked from an implementation worktree.
  121	
  122	The gate should evaluate reviewer artifacts relative to the invocation checkout because that is where post-slice review was run. The resulting `reviewer_chain` recorded into the authoritative tasklist remains a repo-relative path, for example:
  123	
  124	```text
  125	docs/reviewer/p11-s4c-nav-footer-P11-S4c-post-slice
  126	```
  127	
  128	If the reviewer chain path is outside the repository, the command refuses it. If the same repo-relative reviewer chain does not exist in the authoritative checkout yet, close still records the relative path; merge-back will bring the artifacts over. The JSON record must not depend on absolute worktree paths.
  129	
  130	## Lifecycle Enforcement
  131	
  132	Add:
  133	
  134	```sh
  135	tasktool start <id>
  136	```
  137	
  138	Behavior:
  139	
  140	- Accepts phases, slices, tasks, and cross-cutting items.
  141	- Resolves short IDs exactly like `set`.
  142	- Refuses `done` items.
  143	- Refuses `blocked` slices unless `--resume` is supplied, in which case it clears `blocked_on` and sets `in_progress`.
  144	- Sets `status: in_progress`.
  145	- Records a machine-readable lifecycle marker that proves the item was started before close.
  146	
  147	The marker should be explicit rather than inferred from current status, because a row may later move from `in_progress` to `blocked` and back. Add `started: YYYY-MM-DD | null` to phase, slice, task, and cross-cutting records. Existing files load with `started: null`.
  148	
  149	`tasktool set <id> --status in_progress` becomes a compatibility alias for `tasktool start <id>`. It sets `started` using the same rules and notifications. This keeps older skill prose or human muscle memory from producing a visible `in_progress` state that later fails close because no start marker exists.
  150	
  151	Close behavior:
  152	
  153	- Closing tasks and cross-cutting items from `ready` remains allowed for now, because they are often small bookkeeping rows.
  154	- Closing slices from `ready` is refused unless `--allow-ready-close` is supplied.
  155	- `--allow-ready-close` appends an audit note with timestamp and reason.
  156	- Closing phases from `ready` remains allowed only through `archive-phase`; phase lifecycle is already gated by completed slices.
  157	
  158	This targets the recurring operational pain without making every tiny task transition noisy.
  159	
  160	## Skill Updates
  161	
  162	Update these skills:
  163	
  164	- `tasklist-discipline`: explain authoritative routing, `tasktool start`, and the `ready -> done` slice close guard.
  165	- `using-git-worktrees`: say worktrees may invoke tasktool mutations, but mutations route to the authoritative checkout when configured.
  166	- `subagent-driven-development`: after selecting a ready slice and before dispatching implementation subagents, run `tasktool start <slice-id>`.
  167	- `executing-plans`: replace the current prose-only "Mark as in_progress" step with `tasktool start <slice-id>`.
  168	- `writing-plans`: plans for slice execution should include `tasktool start <slice-id>` as the first execution step when `docs/tasklist.json` exists.
  169	
  170	The status problem is partly skill markdown today, especially in `subagent-driven-development`, but the P4 fix should not rely on skill wording alone.
  171	
  172	## Slices
  173	
  174	### P4.S1 — Authoritative Tasklist Mutations
  175	
  176	Add config loading, git worktree detection, lock acquisition, routing helpers, and command integration for all tasklist-writing commands. Worker worktrees stop committing `docs/tasklist.json` deltas.
  177	
  178	### P4.S2 — Lifecycle Status Enforcement
  179	
  180	Add `started` fields, `tasktool start`, close-time enforcement for slices, and skill updates that make lifecycle transitions visible and routine.
  181	
  182	Depends on: `P4.S1`, because lifecycle commands should use the same routed-write path.
  183	
  184	## Acceptance Criteria
  185	
  186	- `tasktool validate --strict-format` passes on existing tasklist files.
  187	- Tasktool unit and CLI tests cover local mode, authoritative mode, linked worktree routing, lock contention, unsafe authoritative checkout states, and reviewer-chain recording from a worker worktree.
  188	- A simulated worker worktree can run `tasktool close P1.S1 --reviewer-chain ...` and leave the worker copy of `docs/tasklist.json` unchanged while updating the authoritative checkout.
  189	- Direct authoritative-checkout writes and worker-routed writes contend on the same tasktool lock.
  190	- `tasktool config init-authority --branch main` creates tracked project policy without absolute paths.
  191	- A worker worktree with authoritative routing configured but no discoverable authoritative root fails closed instead of falling back to local mutation.
  192	- `tasktool set P1.S1 --status done --reviewer-chain ...` uses the same two-root reviewer-gate contract as `tasktool close`.
  193	- Explicit reviewer-chain paths outside the invocation repository are refused.
  194	- `tasktool start P1.S1` sets `status: in_progress` and `started`.
  195	- `tasktool set P1.S1 --status in_progress` sets the same `started` marker as `tasktool start`.
  196	- `tasktool close P1.S1` refuses a never-started slice unless `--allow-ready-close --reason "..."` is supplied.
  197	- Skills describe the enforced workflow without asking agents to hand-edit tasklist state.
  198	
  199	## Non-Goals
  200	
  201	- Do not build a semantic `tasktool merge` command in this phase. It is a fallback for a worse invariant.
  202	- Do not move task state outside the repository.
  203	- Do not add networked locking or a daemon.
  204	- Do not require all existing projects to adopt authoritative routing immediately.
  205	- Do not force every task row through `in_progress` before close in this phase.

## Context Previews

### docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md

    1	# P4 — Tasktool Coordination and Lifecycle Authority Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Make tasklist mutations safe under parallel worktrees and make active work visibly enter `in_progress` before slice close.
    6	
    7	**Architecture:** Add a tasktool runtime layer that resolves whether a write should mutate locally or through an authoritative checkout, guarded by a lock in the shared git directory for every authoritative-mode write. Then add explicit lifecycle state (`started`) and `tasktool start`, with `set --status in_progress` as a compatibility alias and close-time enforcement for slices. Skills become instructions for the enforced command path, not the only enforcement mechanism.
    8	
    9	**Tech Stack:** Python 3 stdlib (`tasktool`), Git CLI, JSON, markdown skills.
   10	
   11	**TASKLIST entry:** `P4` in `docs/tasklist.json`; slices `P4.S1` and `P4.S2`.
   12	
   13	---
   14	
   15	## Scheduling Contract
   16	
   17	`tasktool schedule P4` currently reports:
   18	
   19	```text
   20	P4.S1  [ready/ratified]  group=coordination  ready  deps=-  waiting_on=-  Authoritative tasklist mutations
   21	P4.S2  [ready/ratified]  group=lifecycle  waiting  deps=P4.S1  waiting_on=P4.S1  Lifecycle status enforcement
   22	```
   23	
   24	Execute `P4.S1` first. Do not start `P4.S2` until `P4.S1` has passed its post-slice review and `tasktool close P4.S1` succeeds.
   25	
   26	## File Map
   27	
   28	| Action | Path | Responsibility |
   29	|--------|------|----------------|
   30	| Create | `tools/tasktool/config.py` | Load/save `.tasktool/config.json`; define config dataclasses and validation. |
   31	| Create | `tools/tasktool/worktree.py` | Git repository/worktree discovery, authoritative checkout validation, lock acquisition. |
   32	| Modify | `tools/tasktool/commands.py` | Route mutating commands through a write context; add `cmd_config_init_authority`; later add `cmd_start` and lifecycle enforcement. |
   33	| Modify | `tools/tasktool/cli.py` | Add `config init-authority`, `start`, and `close --allow-ready-close --reason`. |
   34	| Modify | `tools/tasktool/model.py` | Add `started` fields to Phase/Slice/Task/CrossCutting in P4.S2. |
   35	| Modify | `tools/tasktool/serialize.py` | Backward-compatible load/save for `started`. |
   36	| Modify | `tools/tasktool/schema_gen.py` | Include `started` in generated schema. |
   37	| Modify | `tools/tasktool/render.py` and `tools/tasktool/brief.py` | Surface `started` where useful. |
   38	| Create | `tools/tasktool/tests/test_authority_config.py` | Config parsing and validation tests. |
   39	| Create | `tools/tasktool/tests/test_worktree_authority.py` | Git worktree routing, unsafe-state, and locking tests. |
   40	| Create | `tools/tasktool/tests/test_lifecycle_start.py` | `start`, `started`, and ready-close enforcement tests. |
   41	| Modify | `skills/tasklist-discipline/SKILL.md` | Document authoritative routing and lifecycle commands. |
   42	| Modify | `skills/using-git-worktrees/SKILL.md` | Explain routed tasktool writes from implementation worktrees. |
   43	| Modify | `skills/subagent-driven-development/SKILL.md` | Require `tasktool start <slice-id>` before dispatch. |
   44	| Modify | `skills/executing-plans/SKILL.md` | Replace prose-only in-progress step with `tasktool start`. |
   45	| Modify | `skills/writing-plans/SKILL.md` | Plans must include a concrete `tasktool start` execution step. |
   46	
   47	## P4.S1 — Authoritative Tasklist Mutations
   48	
   49	### Task 1: Config Model and CLI Initializer
   50	
   51	**Files:**
   52	- Create: `tools/tasktool/config.py`
   53	- Modify: `tools/tasktool/cli.py`
   54	- Modify: `tools/tasktool/commands.py`
   55	- Test: `tools/tasktool/tests/test_authority_config.py`
   56	
   57	- [ ] **Step 1: Write failing config tests**
   58	
   59	Create `tools/tasktool/tests/test_authority_config.py`:
   60	
   61	```python
   62	import json
   63	from pathlib import Path
   64	
   65	from tasktool.config import (
   66	    DEFAULT_CONFIG_REL,
   67	    TasktoolConfig,
   68	    TasklistConfig,
   69	    load_config,
   70	    save_config,
   71	)
   72	
   73	def test_missing_config_defaults_to_local(tmp_path):
   74	    cfg = load_config(tmp_path)
   75	    assert cfg.tasklist.mutation_mode == "local"
   76	
   77	def test_round_trip_authoritative_config(tmp_path):
   78	    cfg = TasktoolConfig(
   79	        tasklist=TasklistConfig(
   80	            mutation_mode="authoritative-checkout",
   81	            authoritative_branch="main",
   82	        )
   83	    )
   84	    save_config(tmp_path, cfg)
   85	    raw = json.loads((tmp_path / DEFAULT_CONFIG_REL).read_text())
   86	    assert raw["schema_version"] == 1
   87	    assert raw["tasklist"]["mutation_mode"] == "authoritative-checkout"
   88	    assert "authoritative_root" not in raw["tasklist"]
   89	    assert load_config(tmp_path) == cfg
   90	
   91	def test_invalid_mode_raises(tmp_path):
   92	    path = tmp_path / DEFAULT_CONFIG_REL
   93	    path.parent.mkdir()
   94	    path.write_text('{"schema_version":1,"tasklist":{"mutation_mode":"bad"}}')
   95	    try:
   96	        load_config(tmp_path)
   97	    except ValueError as exc:
   98	        assert "unknown mutation_mode" in str(exc)
   99	    else:
  100	        raise AssertionError("expected ValueError")
  101	```
  102	
  103	Run: `python -m pytest tools/tasktool/tests/test_authority_config.py -v`
  104	Expected: FAIL because `tasktool.config` does not exist.
  105	
  106	- [ ] **Step 2: Implement config module**
  107	
  108	Create `tools/tasktool/config.py`:
  109	
  110	```python
  111	from __future__ import annotations
  112	
  113	import json
  114	from dataclasses import dataclass, field
  115	from pathlib import Path
  116	
  117	DEFAULT_CONFIG_REL = Path(".tasktool/config.json")
  118	VALID_MUTATION_MODES = {"local", "authoritative-checkout"}
  119	
  120	@dataclass(frozen=True)
  121	class TasklistConfig:
  122	    mutation_mode: str = "local"
  123	    authoritative_branch: str = "main"
  124	
  125	@dataclass(frozen=True)
  126	class TasktoolConfig:
  127	    schema_version: int = 1
  128	    tasklist: TasklistConfig = field(default_factory=TasklistConfig)
  129	
  130	def _parse_tasklist(raw: dict) -> TasklistConfig:
  131	    mode = raw.get("mutation_mode", "local")
  132	    if mode not in VALID_MUTATION_MODES:
  133	        raise ValueError(f"unknown mutation_mode: {mode}")
  134	    return TasklistConfig(
  135	        mutation_mode=mode,
  136	        authoritative_branch=raw.get("authoritative_branch", "main"),
  137	    )
  138	
  139	def load_config(repo_root: Path) -> TasktoolConfig:
  140	    path = repo_root / DEFAULT_CONFIG_REL
  141	    if not path.exists():
  142	        return TasktoolConfig()
  143	    raw = json.loads(path.read_text(encoding="utf-8"))
  144	    if raw.get("schema_version", 1) != 1:
  145	        raise ValueError(f"unsupported tasktool config schema_version: {raw.get('schema_version')}")
  146	    return TasktoolConfig(
  147	        schema_version=1,
  148	        tasklist=_parse_tasklist(raw.get("tasklist", {})),
  149	    )
  150	
  151	def save_config(repo_root: Path, cfg: TasktoolConfig) -> None:
  152	    path = repo_root / DEFAULT_CONFIG_REL
  153	    path.parent.mkdir(parents=True, exist_ok=True)
  154	    body = {
  155	        "schema_version": cfg.schema_version,
  156	        "tasklist": {
  157	            "mutation_mode": cfg.tasklist.mutation_mode,
  158	            "authoritative_branch": cfg.tasklist.authoritative_branch,
  159	        },
  160	    }
  161	    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
  162	```
  163	
  164	Run: `python -m pytest tools/tasktool/tests/test_authority_config.py -v`
  165	Expected: PASS.
  166	
  167	- [ ] **Step 3: Add CLI initializer test**
  168	
  169	Append to `tools/tasktool/tests/test_cli_integration.py`:
  170	
  171	```python
  172	def test_config_init_authority_writes_project_config(tmp_path):
  173	    r = run_cli(
  174	        "config", "init-authority",
  175	        "--branch", "main",
  176	        cwd=tmp_path,
  177	    )
  178	    assert r.returncode == 0, r.stdout + r.stderr
  179	    data = json.loads((tmp_path / ".tasktool" / "config.json").read_text())
  180	    assert data["tasklist"]["mutation_mode"] == "authoritative-checkout"
  181	    assert "authoritative_root" not in data["tasklist"]
  182	    assert data["tasklist"]["authoritative_branch"] == "main"
  183	```
  184	
  185	Run: `python -m pytest tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_writes_project_config -v`
  186	Expected: FAIL because the command does not exist.
  187	
  188	- [ ] **Step 4: Add command and CLI plumbing**
  189	
  190	In `tools/tasktool/commands.py`, import config helpers and add:
  191	
  192	```python
  193	from tasktool.config import TasktoolConfig, TasklistConfig, save_config
  194	
  195	def cmd_config_init_authority(*, repo_root: Path, branch: str) -> None:
  196	    cfg = TasktoolConfig(
  197	        tasklist=TasklistConfig(
  198	            mutation_mode="authoritative-checkout",
  199	            authoritative_branch=branch,
  200	        )

[truncated: 1143 additional lines]
### docs/tasklist.json

    1	{
    2	  "archived_phases": [
    3	    {
    4	      "archived_date": "2026-05-18",
    5	      "archived_path": "docs/archived-tasks/P2-tasktool-json-backed-task-management-cli.md",
    6	      "id": "P2",
    7	      "title": "tasktool: JSON-backed task management CLI"
    8	    }
    9	  ],
   10	  "cross_cutting": [
   11	    {
   12	      "closed": "2026-05-18",
   13	      "created": "2026-05-18",
   14	      "id": "X1",
   15	      "notes": "Changed external-review default prompt transport from argv to stdin so the bundled Codex reviewer-agent receives prompts via codex exec '-' and avoids argv length failures.",
   16	      "refs": [],
   17	      "started": null,
   18	      "status": "done",
   19	      "title": "Default external-review prompt transport to stdin"
   20	    },
   21	    {
   22	      "closed": "2026-05-18",
   23	      "created": "2026-05-18",
   24	      "id": "X2",
   25	      "notes": "Added repo-local tools/tasktool/tasktool launcher, updated tasklist/project-setup docs to prefer it, and taught the pre-commit hook to use the repo-local launcher before falling back to a global tasktool shim.",
   26	      "refs": [],
   27	      "started": null,
   28	      "status": "done",
   29	      "title": "Add repo-local tasktool launcher"
   30	    },
   31	    {
   32	      "closed": "2026-05-19",
   33	      "created": "2026-05-19",
   34	      "id": "X3",
   35	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. External-review verdict parsing now accepts markdown-emphasized Overall Verdict headings such as **5. Overall Verdict** followed by ready/revise text.",
   36	      "refs": [
   37	        "skills/external-review/scripts/external-reviewer.py",
   38	        "skills/external-review/tests/test_heading_style_verdict.py"
   39	      ],
   40	      "started": null,
   41	      "status": "done",
   42	      "title": "Spot fix: parse bold external-review verdict headings"
   43	    },
   44	    {
   45	      "closed": "2026-05-19",
   46	      "created": "2026-05-19",
   47	      "id": "X4",
   48	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. Legacy markdown import now accepts fully-qualified slice IDs and additional cross-cutting forms including tagged done items, blocked cross rows coerced to ready, and archived cross rows treated as done.",
   49	      "refs": [
   50	        "tools/tasktool/importer.py"
   51	      ],
   52	      "started": null,
   53	      "status": "done",
   54	      "title": "Spot fix: broaden legacy tasklist importer compatibility"
   55	    },
   56	    {
   57	      "closed": "2026-05-19",
   58	      "created": "2026-05-19",
   59	      "id": "X5",
   60	      "notes": "User-requested hook update completed outside the normal workflow for speed. Adds Stop/SubagentStop finished-agent notifications, milestone message derivation from final agent text/transcript payloads, Hypr TTS config reuse with OPENAI_API_KEY fallback, and non-TTS ding fallbacks.\nSuperseded by X8: final-text milestone parsing was removed; agent hooks now emit generic dings and semantic spoken notifications come from tasktool status changes.",
   61	      "refs": [
   62	        "hooks/agent-finished",
   63	        "hooks/hooks.json",
   64	        "hooks/hooks-cursor.json",
   65	        "tests/claude-code/test-agent-finished-hook.sh"
   66	      ],
   67	      "started": null,
   68	      "status": "done",
   69	      "title": "Add finished-agent notification hook"
   70	    },
   71	    {
   72	      "closed": "2026-05-19",
   73	      "created": "2026-05-19",
   74	      "id": "X6",
   75	      "notes": "Codex startup skips Stop/SubagentStop notification hooks when hooks.json uses async=true; fix should preserve finished-agent notification behavior while avoiding unsupported async hook registration in Codex.\nSet finished-agent Stop/SubagentStop hook registrations to async=false for Codex compatibility. The hook now backgrounds real notification playback internally so synchronous hook registration returns quickly while dry-run tests remain foreground and deterministic.",
   76	      "refs": [
   77	        "hooks/hooks.json",
   78	        "hooks/agent-finished",
   79	        "tests/claude-code/test-hook-config.sh",
   80	        "tests/claude-code/test-agent-finished-hook.sh"
   81	      ],
   82	      "started": null,
   83	      "status": "done",
   84	      "title": "Fix Codex finished-agent hook compatibility"
   85	    },
   86	    {
   87	      "closed": "2026-05-19",
   88	      "created": "2026-05-19",
   89	      "id": "X7",
   90	      "notes": "Codex reported superstar/6.0.0 because the installable local marketplace payload under plugins/superstar still declared version 6.0.0 and the version bump audit did not track that embedded manifest.\n\nBumped the embedded Codex plugin payload manifest to 6.0.1 and added it to the version bump check. Reinstalled superstar@superstar-dev, then rebuilt the 6.0.1 runtime cache as a materialized copy of this checkout with .agents excluded so Codex sees the full skills/hooks tree while codex plugin list still reports installed/enabled. Final probe shows cache version 6.0.1, skills/hooks present, and no async-hook warning.",
   91	      "refs": [
   92	        ".version-bump.json",
   93	        "plugins/superstar/.codex-plugin/plugin.json",
   94	        ".agents/plugins/marketplace.json",
   95	        "tests/codex-plugin-sync/test-version-drift.sh",
   96	        "tests/codex-plugin-sync/test-local-marketplace.sh"
   97	      ],
   98	      "started": null,
   99	      "status": "done",
  100	      "title": "Fix Superstar Codex plugin payload version drift"
  101	    },
  102	    {
  103	      "closed": "2026-05-19",
  104	      "created": "2026-05-19",
  105	      "id": "X8",
  106	      "notes": "Move semantic spoken notifications to tasktool status transitions for ready/in_progress/blocked/done. Keep agent Stop/SubagentStop hooks as generic completion dings only, with different sound styles for Claude and Codex.\nAgent Stop/SubagentStop hooks now emit generic harness-specific dings only. Semantic spoken notifications moved to tasktool status events for ready, in_progress, blocked, and done, including create, set, close, block, unblock, and archive-phase paths.",
  107	      "refs": [
  108	        "hooks/agent-finished",
  109	        "tools/tasktool/notify.py",
  110	        "tools/tasktool/commands.py",
  111	        "tools/tasktool/tests/test_notify.py",
  112	        "tools/tasktool/tests/test_commands.py",
  113	        "tools/tasktool/tests/conftest.py",
  114	        "tests/claude-code/test-agent-finished-hook.sh"
  115	      ],
  116	      "started": null,
  117	      "status": "done",
  118	      "title": "Move semantic notifications from agent hooks to tasktool status changes"
  119	    },
  120	    {
  121	      "closed": "2026-05-19",
  122	      "created": "2026-05-19",
  123	      "id": "X9",
  124	      "notes": "Rapid tasktool status changes currently spawn independent notifier processes, causing overlapping TTS/audio. Add a single-audio queue with at most three queued tasktool events; overflow should collapse to a single 'multiple other events' summary and drop further items.\nAdded a file-backed notification queue shared by agent dings and tasktool TTS. Only one worker drains audio at a time. Queue capacity is three pending events; overflow keeps the first two pending items and replaces the rest with a single 'Multiple other events' summary, dropping further burst items while the summary remains queued.",
  125	      "refs": [
  126	        "tools/tasktool/notify.py",
  127	        "tools/tasktool/tests/test_notify.py"
  128	      ],
  129	      "started": null,
  130	      "status": "done",
  131	      "title": "Coalesce bursty tasktool audio notifications"
  132	    }
  133	  ],
  134	  "last_reviewed": "2026-05-18",
  135	  "north_star": "",
  136	  "phases": [
  137	    {
  138	      "closed": "2026-05-17",
  139	      "created": "2026-05-17",
  140	      "id": "P1",
  141	      "notes": "",
  142	      "phase_reviewer_chain": null,
  143	      "plan_path": null,
  144	      "planning_path": null,
  145	      "slices": [],
  146	      "spec_path": null,
  147	      "started": null,
  148	      "status": "done",
  149	      "title": "External-reviewer work (historical)"
  150	    },
  151	    {
  152	      "closed": null,
  153	      "created": "2026-05-19",
  154	      "id": "P3",
  155	      "notes": "",
  156	      "phase_reviewer_chain": null,
  157	      "plan_path": null,
  158	      "planning_path": "docs/specs/2026-05-19-p3-phase-planning-design.md",
  159	      "slices": [
  160	        {
  161	          "blocked_on": null,
  162	          "closed": null,
  163	          "created": "2026-05-19",
  164	          "depends_on": [],
  165	          "id": "S1",
  166	          "notes": "",
  167	          "parallel_group": "foundation",
  168	          "plan_path": null,
  169	          "planning_status": "ratified",
  170	          "refs": [],
  171	          "reviewer_chain": null,
  172	          "started": null,
  173	          "status": "ready",
  174	          "tasks": [],
  175	          "title": "Schema and validation foundation"
  176	        },
  177	        {
  178	          "blocked_on": null,
  179	          "closed": null,
  180	          "created": "2026-05-19",
  181	          "depends_on": [
  182	            "P3.S1"
  183	          ],
  184	          "id": "S2",
  185	          "notes": "",
  186	          "parallel_group": "cli",
  187	          "plan_path": null,
  188	          "planning_status": "ratified",
  189	          "refs": [],
  190	          "reviewer_chain": null,
  191	          "started": null,
  192	          "status": "ready",
  193	          "tasks": [],
  194	          "title": "Scheduling CLI"
  195	        },
  196	        {
  197	          "blocked_on": null,
  198	          "closed": null,
  199	          "created": "2026-05-19",
  200	          "depends_on": [

[truncated: 95 additional lines]

<!-- superstar-prompt:end -->