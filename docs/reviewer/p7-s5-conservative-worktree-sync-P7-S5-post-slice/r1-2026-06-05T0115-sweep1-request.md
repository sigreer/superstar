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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s5-conservative-worktree-sync-strict

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-04-P7-S5-conservative-worktree-sync.md

Additional context files:
- docs/specs/2026-06-04-P7-S5-conservative-worktree-sync-design.md
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

### docs/plans/2026-06-04-P7-S5-conservative-worktree-sync.md

    1	# P7.S5 — Conservative worktree sync Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Add `tasktool worktree sync <slice-id> (--merge | --rebase)` so a stale slice worktree can explicitly integrate the configured base branch and advance `worktree_base_sha` only after a successful git operation.
    6	
    7	**Architecture:** The command is a conservative mutating worktree operation. It performs read-only preflight against the resolved authoritative checkout, runs exactly one non-interactive git operation in the target worktree without holding the tasktool lock, then re-enters the locked authoritative write path to update `worktree_base_sha` to the captured base SHA. Refusals are strict: no missing base SHA, no unhealthy linked worktree, no unresolved merge state, no unsafe target dirt, and no unstaged authoritative `docs/tasklist.json` drift.
    8	
    9	**Tech Stack:** Python 3, argparse, git plumbing, pytest
   10	
   11	---
   12	
   13	## Scheduling
   14	
   15	- **Slice:** `P7.S5`.
   16	- **depends_on:** `P7.S4`, which already records `worktree_base_sha`, stamps `landed_base_sha`, and provides `worktree status --integration`.
   17	- **parallel_group:** none.
   18	- **integration surfaces:** `worktree`.
   19	- **reservations:** none.
   20	- **independent execution:** yes, now that `P7.S4` is done. Do not parallel-dispatch this with another open slice that writes `worktree` unless a dependency or `coordination_group` is declared.
   21	- **test scope note:** most worktree tests in this repo use `config init-local`, matching existing `test_worktree_integration.py` fixtures. The implementation still uses `_write_context` for the row update so authoritative-checkout mode takes the normal lock/route path; full routed-mode behavior is covered indirectly by existing tasktool routing tests and the final real-slice dogfood step.
   22	
   23	Before editing implementation files, run:
   24	
   25	```sh
   26	./tools/tasktool/tasktool start P7.S5
   27	```
   28	
   29	Expected: tasktool records/prints the worktree path, flips `P7.S5` to `in_progress`, and records `worktree_base_sha`. `cd` into the printed worktree path and do all source edits there.
   30	
   31	## File Structure
   32	
   33	| File | Responsibility |
   34	|------|----------------|
   35	| `tools/tasktool/cli.py` | Add `worktree sync <id>` parser with required mutually exclusive `--merge` / `--rebase`, and dispatch to `commands.cmd_worktree_sync`. |
   36	| `tools/tasktool/worktree.py` | Add one helper that reports worktree dirt while allowing staged-only `docs/tasklist.json` for in-place authoritative sync. Reuse `has_unmerged_paths`, `current_branch_head_sha`, and `_git`. |
   37	| `tools/tasktool/commands.py` | Add target resolution and `cmd_worktree_sync`: preflight, run git without the tasktool lock, then update `worktree_base_sha` through `_write_context`. |
   38	| `tools/tasktool/tests/test_worktree_sync.py` | New focused CLI tests for parser behavior, merge/rebase success, refusal cases, conflict no-advance, and post-sync integration status. |
   39	
   40	## Task 1 — Start the slice and add parser coverage
   41	
   42	### 1.1 Start the slice
   43	
   44	- [ ] Run:
   45	  ```sh
   46	  ./tools/tasktool/tasktool start P7.S5
   47	  ```
   48	  Expected: output includes `cd .worktrees/worktree-p7-s5-...`. Change into that path before continuing.
   49	
   50	### 1.2 Create failing parser tests
   51	
   52	- [ ] Create `tools/tasktool/tests/test_worktree_sync.py`:
   53	  ```python
   54	  from __future__ import annotations
   55	
   56	  import json
   57	  import os
   58	  import subprocess
   59	  import sys
   60	  from pathlib import Path
   61	
   62	  TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
   63	  PYTHONPATH = str(Path(__file__).resolve().parents[2])
   64	
   65	
   66	  def run(root: Path, *args: str):
   67	      env = os.environ.copy()
   68	      env["PYTHONPATH"] = PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
   69	      env["GIT_EDITOR"] = "false"
   70	      return subprocess.run(
   71	          [sys.executable, str(TOOL), "--project-root", str(root), *args],
   72	          text=True,
   73	          capture_output=True,
   74	          env=env,
   75	      )
   76	
   77	
   78	  def git(cwd: Path, *args: str) -> str:
   79	      return subprocess.run(
   80	          ["git", *args], cwd=cwd, text=True, capture_output=True, check=True
   81	      ).stdout
   82	
   83	
   84	  def init_repo(root: Path) -> Path:
   85	      root.mkdir()
   86	      git(root, "init", "-q", "-b", "main")
   87	      git(root, "config", "user.email", "t@example.invalid")
   88	      git(root, "config", "user.name", "T")
   89	      (root / "docs").mkdir()
   90	      assert run(root, "config", "init-local").returncode == 0
   91	      assert run(root, "init", "--project", "demo").returncode == 0
   92	      git(root, "add", "-A")
   93	      git(root, "commit", "-q", "-m", "init")
   94	      assert run(root, "create", "phase", "--title", "Phase 1").returncode == 0
   95	      assert run(root, "create", "slice", "P1", "--title", "Sync target").returncode == 0
   96	      git(root, "add", "-A")
   97	      git(root, "commit", "-q", "-m", "seed slice")
   98	      return root
   99	
  100	
  101	  def slice_row(repo: Path, qid: str = "P1.S1") -> dict:
  102	      data = json.loads((repo / "docs" / "tasklist.json").read_text())
  103	      return next(
  104	          s for ph in data["phases"] for s in ph["slices"]
  105	          if f"{ph['id']}.{s['id']}" == qid
  106	      )
  107	
  108	
  109	  def start_linked(repo: Path) -> Path:
  110	      r = run(repo, "start", "P1.S1")
  111	      assert r.returncode == 0, r.stdout + r.stderr
  112	      return (repo / slice_row(repo)["worktree_path"]).resolve()
  113	
  114	
  115	  def advance_main(repo: Path, name: str, content: str = "x") -> str:
  116	      (repo / name).write_text(content + "\n")
  117	      git(repo, "add", name)
  118	      git(repo, "commit", "-q", "-m", f"main {name}")
  119	      return git(repo, "rev-parse", "main").strip()
  120	
  121	
  122	  def test_sync_requires_exactly_one_strategy(tmp_path):
  123	      repo = init_repo(tmp_path / "repo")
  124	      no_strategy = run(repo, "worktree", "sync", "P1.S1")
  125	      assert no_strategy.returncode != 0
  126	      assert "one of the arguments --merge --rebase is required" in no_strategy.stderr
  127	      both = run(repo, "worktree", "sync", "P1.S1", "--merge", "--rebase")
  128	      assert both.returncode != 0
  129	      assert "not allowed with argument" in both.stderr
  130	  ```
  131	
  132	### 1.3 Run parser test, expect FAIL
  133	
  134	- [ ] Run:
  135	  ```sh
  136	  python -m pytest tools/tasktool/tests/test_worktree_sync.py::test_sync_requires_exactly_one_strategy -q
  137	  ```
  138	  Expected: FAIL because `worktree sync` is not a known subcommand.
  139	
  140	### 1.4 Add CLI parser and dispatch
  141	
  142	- [ ] Modify `tools/tasktool/cli.py` near the other `worktree` subcommands:
  143	  ```python
  144	      p_wt_sync = wt_sub.add_parser("sync")
  145	      p_wt_sync.add_argument("id")
  146	      sync_mode = p_wt_sync.add_mutually_exclusive_group(required=True)
  147	      sync_mode.add_argument("--merge", action="store_true")
  148	      sync_mode.add_argument("--rebase", action="store_true")
  149	  ```
  150	
  151	- [ ] Modify the `elif args.cmd == "worktree":` dispatch block:
  152	  ```python
  153	              elif args.wt_cmd == "sync":
  154	                  sys.stdout.write(
  155	                      commands.cmd_worktree_sync(
  156	                          repo_root=root,
  157	                          id=args.id,
  158	                          merge=args.merge,
  159	                          rebase=args.rebase,
  160	                      )
  161	                  )
  162	  ```
  163	
  164	### 1.5 Add command stub
  165	
  166	- [ ] Add this stub in `tools/tasktool/commands.py` before `cmd_worktree_adopt`:
  167	  ```python
  168	  def cmd_worktree_sync(
  169	      *, repo_root: Path, id: str, merge: bool = False, rebase: bool = False
  170	  ) -> str:
  171	      raise CommandError("worktree sync is not implemented yet")
  172	  ```
  173	
  174	### 1.6 Run parser test, expect PASS
  175	
  176	- [ ] Run:
  177	  ```sh
  178	  python -m pytest tools/tasktool/tests/test_worktree_sync.py::test_sync_requires_exactly_one_strategy -q
  179	  ```
  180	  Expected: PASS.
  181	
  182	### 1.7 Commit
  183	
  184	- [ ] Run:
  185	  ```sh
  186	  git add tools/tasktool/cli.py tools/tasktool/commands.py tools/tasktool/tests/test_worktree_sync.py
  187	  git commit -m "P7.S5: add worktree sync parser"
  188	  ```
  189	
  190	## Task 2 — Dirty-state helper with staged-tasklist allowance
  191	
  192	### 2.1 Add failing helper tests
  193	
  194	- [ ] Append to `tools/tasktool/tests/test_worktree_sync.py`:
  195	  ```python
  196	  def test_dirty_helper_allows_staged_tasklist_only(tmp_path):
  197	      from tasktool.worktree import working_tree_dirty_for_sync
  198	      repo = init_repo(tmp_path / "repo")
  199	      data = json.loads((repo / "docs" / "tasklist.json").read_text())
  200	      data["north_star"] = "staged tracker update"
  201	      (repo / "docs" / "tasklist.json").write_text(json.dumps(data, indent=2) + "\n")
  202	      git(repo, "add", "docs/tasklist.json")
  203	      dirty, items = working_tree_dirty_for_sync(repo, allow_staged_tasklist=True)
  204	      assert dirty is False, items
  205	
  206	
  207	  def test_dirty_helper_refuses_unstaged_tasklist_and_untracked_files(tmp_path):
  208	      from tasktool.worktree import working_tree_dirty_for_sync
  209	      repo = init_repo(tmp_path / "repo")
  210	      data = json.loads((repo / "docs" / "tasklist.json").read_text())
  211	      data["north_star"] = "unstaged tracker update"
  212	      (repo / "docs" / "tasklist.json").write_text(json.dumps(data, indent=2) + "\n")
  213	      dirty, items = working_tree_dirty_for_sync(repo, allow_staged_tasklist=True)
  214	      assert dirty is True
  215	      assert "docs/tasklist.json" in items
  216	      git(repo, "add", "docs/tasklist.json")
  217	      (repo / "scratch.txt").write_text("scratch\n")
  218	      dirty, items = working_tree_dirty_for_sync(repo, allow_staged_tasklist=True)
  219	      assert dirty is True
  220	      assert "scratch.txt" in items
  221	  ```
  222	
  223	### 2.2 Run helper tests, expect FAIL
  224	
  225	- [ ] Run:
  226	  ```sh
  227	  python -m pytest tools/tasktool/tests/test_worktree_sync.py::test_dirty_helper_allows_staged_tasklist_only tools/tasktool/tests/test_worktree_sync.py::test_dirty_helper_refuses_unstaged_tasklist_and_untracked_files -q
  228	  ```
  229	  Expected: FAIL with `ImportError: cannot import name 'working_tree_dirty_for_sync'`.
  230	
  231	### 2.3 Implement helper
  232	
  233	- [ ] Add to `tools/tasktool/worktree.py` after `working_tree_dirty`:
  234	  ```python
  235	  def working_tree_dirty_for_sync(
  236	      root: Path, *, allow_staged_tasklist: bool = False
  237	  ) -> tuple[bool, list[str]]:
  238	      """Dirty check for worktree sync.
  239	
  240	      When syncing an in-place slice in the authoritative checkout, staged-only
  241	      docs/tasklist.json is safe tasktool state. Unstaged tasklist bytes and all
  242	      other dirt still refuse.
  243	      """
  244	      items: list[str] = []
  245	      status = _git(root, "status", "--porcelain", check=False).stdout.splitlines()
  246	      for line in status:
  247	          if not line.strip():
  248	              continue
  249	          code = line[:2]
  250	          path = line[3:]
  251	          staged_only_tasklist = (
  252	              allow_staged_tasklist
  253	              and path == "docs/tasklist.json"
  254	              and code[0] != " "
  255	              and code[1] == " "
  256	          )
  257	          if staged_only_tasklist:
  258	              continue
  259	          items.append(path)
  260	
  261	      branch = git_current_branch(root)
  262	      if branch:
  263	          stash = _git(root, "stash", "list", check=False).stdout.splitlines()
  264	          marker_wip = f"WIP on {branch}:"
  265	          marker_on = f"On {branch}:"
  266	          for line in stash:
  267	              if marker_wip in line or marker_on in line:
  268	                  items.append(f"stash: {line}")
  269	      # The staged-tasklist allowance intentionally recognizes only plain
  270	      # add/modify status lines. Renames, deletes, and quoted paths stay dirty.
  271	      return (bool(items), items)
  272	  ```
  273	
  274	### 2.4 Run helper tests, expect PASS
  275	
  276	- [ ] Run the same command as 2.2. Expected: `2 passed`.
  277	
  278	### 2.5 Commit
  279	
  280	- [ ] Run:
  281	  ```sh
  282	  git add tools/tasktool/worktree.py tools/tasktool/tests/test_worktree_sync.py
  283	  git commit -m "P7.S5: allow staged tasklist during in-place sync"
  284	  ```
  285	
  286	## Task 3 — Implement strict sync preflight
  287	
  288	### 3.1 Add failing refusal tests
  289	
  290	- [ ] Append to `tools/tasktool/tests/test_worktree_sync.py`:
  291	  ```python
  292	  def test_sync_refuses_missing_worktree_base_sha(tmp_path):
  293	      repo = init_repo(tmp_path / "repo")
  294	      start_linked(repo)
  295	      path = repo / "docs" / "tasklist.json"
  296	      data = json.loads(path.read_text())
  297	      data["phases"][0]["slices"][0].pop("worktree_base_sha", None)
  298	      path.write_text(json.dumps(data, indent=2) + "\n")
  299	      git(repo, "add", "docs/tasklist.json")
  300	      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
  301	      assert r.returncode != 0
  302	      assert "worktree_base_sha" in (r.stdout + r.stderr)
  303	
  304	
  305	  def test_sync_refuses_non_slice_id(tmp_path):
  306	      repo = init_repo(tmp_path / "repo")
  307	      r = run(repo, "worktree", "sync", "P1", "--merge")
  308	      assert r.returncode != 0
  309	      assert "worktree sync only supports slices" in (r.stdout + r.stderr)
  310	
  311	
  312	  def test_sync_refuses_unhealthy_recorded_worktree(tmp_path):
  313	      repo = init_repo(tmp_path / "repo")
  314	      wt = start_linked(repo)
  315	      git(repo, "worktree", "remove", "--force", str(wt))
  316	      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
  317	      assert r.returncode != 0
  318	      assert "recorded worktree is not live" in (r.stdout + r.stderr)
  319	
  320	
  321	  def test_sync_refuses_dirty_linked_worktree(tmp_path):
  322	      repo = init_repo(tmp_path / "repo")
  323	      wt = start_linked(repo)
  324	      advance_main(repo, "base-change")
  325	      (wt / "dirty.txt").write_text("dirty\n")
  326	      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
  327	      assert r.returncode != 0
  328	      assert "not clean" in (r.stdout + r.stderr)
  329	      assert "dirty.txt" in (r.stdout + r.stderr)
  330	
  331	
  332	  def test_sync_refuses_unstaged_authoritative_tasklist(tmp_path):
  333	      repo = init_repo(tmp_path / "repo")
  334	      start_linked(repo)
  335	      advance_main(repo, "base-change")
  336	      data = json.loads((repo / "docs" / "tasklist.json").read_text())
  337	      data["north_star"] = "unstaged"
  338	      (repo / "docs" / "tasklist.json").write_text(json.dumps(data, indent=2) + "\n")
  339	      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
  340	      assert r.returncode != 0
  341	      assert "docs/tasklist.json has unstaged changes" in (r.stdout + r.stderr)
  342	  ```
  343	
  344	### 3.2 Run refusal tests, expect FAIL
  345	
  346	- [ ] Run:
  347	  ```sh
  348	  python -m pytest tools/tasktool/tests/test_worktree_sync.py::test_sync_refuses_missing_worktree_base_sha tools/tasktool/tests/test_worktree_sync.py::test_sync_refuses_non_slice_id tools/tasktool/tests/test_worktree_sync.py::test_sync_refuses_unhealthy_recorded_worktree tools/tasktool/tests/test_worktree_sync.py::test_sync_refuses_dirty_linked_worktree tools/tasktool/tests/test_worktree_sync.py::test_sync_refuses_unstaged_authoritative_tasklist -q
  349	  ```
  350	  Expected: FAIL because the stub always says not implemented.
  351	
  352	### 3.3 Implement target resolution and preflight
  353	
  354	- [ ] Replace the stub in `tools/tasktool/commands.py` with this implementation shell:
  355	  ```python
  356	  def _sync_target_path(write_root: Path, qid: str, item) -> Path:
  357	      if getattr(item, "worktree_in_place", False):
  358	          return write_root
  359	      path_str = getattr(item, "worktree_path", None)
  360	      if not path_str:
  361	          raise CommandError(f"{qid}: no recorded worktree to sync")
  362	      if _health_for(write_root, item) != "live":
  363	          raise CommandError(f"{qid}: recorded worktree is not live; run `tasktool worktree status {qid}`")
  364	      return (write_root / path_str).resolve()
  365	
  366	
  367	  def _preflight_worktree_sync(
  368	      *, write_root: Path, qid: str, item, target: Path, base_branch: str
  369	  ) -> str:
  370	      from tasktool import worktree as wt
  371	      base_sha = getattr(item, "worktree_base_sha", None)
  372	      if not base_sha:
  373	          raise CommandError(f"{qid}: worktree_base_sha is not recorded; cannot sync safely")
  374	      try:
  375	          base_head = wt.current_branch_head_sha(write_root, base_branch)
  376	      except _subprocess.CalledProcessError as exc:
  377	          raise CommandError(f"{qid}: cannot resolve base branch {base_branch!r}") from exc
  378	      if wt.has_unmerged_paths(target):
  379	          raise CommandError(f"{qid}: target worktree has unresolved merge entries")
  380	      allow_staged_tasklist = target.resolve() == write_root.resolve()
  381	      dirty, items = wt.working_tree_dirty_for_sync(
  382	          target, allow_staged_tasklist=allow_staged_tasklist
  383	      )
  384	      if dirty:
  385	          pretty = ", ".join(items[:5]) + (" ..." if len(items) > 5 else "")
  386	          raise CommandError(f"{qid}: target worktree is not clean: {pretty}")
  387	      if wt.tasklist_has_unsafe_dirty_state(write_root):
  388	          raise CommandError("authoritative docs/tasklist.json has unstaged changes")
  389	      return base_head
  390	
  391	
  392	  def cmd_worktree_sync(
  393	      *, repo_root: Path, id: str, merge: bool = False, rebase: bool = False
  394	  ) -> str:
  395	      if merge == rebase:
  396	          raise CommandError("choose exactly one of --merge or --rebase")
  397	      with _read_context(repo_root) as write_root:
  398	          p = _load(write_root)
  399	          qid, _container, item = _find_item(p, id)
  400	          if parse_id(qid)[0] != "slice":
  401	              raise CommandError(f"{qid}: worktree sync only supports slices")
  402	          base_branch = _authoritative_parent_branch(write_root, qid)
  403	          target = _sync_target_path(write_root, qid, item)
  404	          previous_base = getattr(item, "worktree_base_sha", None)
  405	          base_head = _preflight_worktree_sync(
  406	              write_root=write_root,
  407	              qid=qid,
  408	              item=item,
  409	              target=target,
  410	              base_branch=base_branch,
  411	          )
  412	      # Git mutation is added in Task 4.
  413	      return (
  414	          f"{qid}: sync preflight passed ({'merge' if merge else 'rebase'} {base_head})\n"
  415	          f"previous worktree_base_sha: {previous_base}\n"
  416	      )
  417	  ```
  418	
  419	### 3.4 Run refusal tests, expect PASS
  420	
  421	- [ ] Run the same command as 3.2. Expected: `5 passed`.
  422	
  423	### 3.5 Commit
  424	
  425	- [ ] Run:
  426	  ```sh
  427	  git add tools/tasktool/commands.py tools/tasktool/tests/test_worktree_sync.py
  428	  git commit -m "P7.S5: add sync preflight refusals"
  429	  ```
  430	
  431	## Task 4 — Merge/rebase success and base-SHA update
  432	
  433	### 4.1 Add failing success tests
  434	
  435	- [ ] Append to `tools/tasktool/tests/test_worktree_sync.py`:
  436	  ```python
  437	  def test_sync_merge_integrates_captured_base_sha_and_advances_row(tmp_path):
  438	      repo = init_repo(tmp_path / "repo")
  439	      wt = start_linked(repo)
  440	      base_head = advance_main(repo, "base-change", "base")
  441	      (wt / "slice-work").write_text("slice\n")
  442	      git(wt, "add", "slice-work")
  443	      git(wt, "commit", "-q", "-m", "slice work")
  444	      old_base = slice_row(repo)["worktree_base_sha"]
  445	      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
  446	      assert r.returncode == 0, r.stdout + r.stderr
  447	      assert f"integrated main at {base_head}" in r.stdout
  448	      assert slice_row(repo)["worktree_base_sha"] == base_head
  449	      assert slice_row(repo)["worktree_base_sha"] != old_base
  450	      assert (wt / "base-change").read_text() == "base\n"
  451	
  452	
  453	  def test_sync_rebase_integrates_captured_base_sha_and_advances_row(tmp_path):
  454	      repo = init_repo(tmp_path / "repo")
  455	      wt = start_linked(repo)
  456	      base_head = advance_main(repo, "base-change", "base")
  457	      (wt / "slice-work").write_text("slice\n")
  458	      git(wt, "add", "slice-work")
  459	      git(wt, "commit", "-q", "-m", "slice work")
  460	      r = run(repo, "worktree", "sync", "P1.S1", "--rebase")
  461	      assert r.returncode == 0, r.stdout + r.stderr
  462	      assert f"integrated main at {base_head}" in r.stdout
  463	      assert slice_row(repo)["worktree_base_sha"] == base_head
  464	      assert (wt / "base-change").read_text() == "base\n"
  465	
  466	
  467	  def test_sync_merge_non_fast_forward_is_non_interactive(tmp_path):
  468	      repo = init_repo(tmp_path / "repo")
  469	      wt = start_linked(repo)
  470	      advance_main(repo, "main-only", "base")
  471	      (wt / "slice-only").write_text("slice\n")
  472	      git(wt, "add", "slice-only")
  473	      git(wt, "commit", "-q", "-m", "slice work")
  474	      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
  475	      assert r.returncode == 0, r.stdout + r.stderr
  476	      assert "follow-up:" in r.stdout
  477	      log = git(wt, "log", "-1", "--format=%s").strip()
  478	      assert log.startswith("Merge")
  479	  ```
  480	
  481	### 4.2 Run success tests, expect FAIL
  482	
  483	- [ ] Run:
  484	  ```sh
  485	  python -m pytest tools/tasktool/tests/test_worktree_sync.py::test_sync_merge_integrates_captured_base_sha_and_advances_row tools/tasktool/tests/test_worktree_sync.py::test_sync_rebase_integrates_captured_base_sha_and_advances_row tools/tasktool/tests/test_worktree_sync.py::test_sync_merge_non_fast_forward_is_non_interactive -q
  486	  ```
  487	  Expected: FAIL because Task 3 only prints preflight and does not run git/update the row.
  488	
  489	### 4.3 Implement git operation and locked row update
  490	
  491	- [ ] Add in `tools/tasktool/commands.py` near `_preflight_worktree_sync`:
  492	  ```python
  493	  def _run_sync_git(*, target: Path, strategy: str, base_head: str) -> None:
  494	      env = _os.environ.copy()
  495	      env.setdefault("GIT_EDITOR", "true")
  496	      if strategy == "merge":
  497	          args = ["git", "merge", "--no-edit", base_head]
  498	      else:
  499	          args = ["git", "rebase", base_head]
  500	      try:
  501	          _subprocess.run(args, cwd=target, text=True, capture_output=True, check=True, env=env)
  502	      except _subprocess.CalledProcessError as exc:
  503	          detail = (exc.stderr or exc.stdout or "").strip()
  504	          raise CommandError(f"git {strategy} failed; resolve or abort git state, then rerun sync: {detail}") from exc
  505	  ```
  506	
  507	- [ ] Replace the final body of `cmd_worktree_sync` after preflight with:
  508	  ```python
  509	      strategy = "merge" if merge else "rebase"
  510	      _run_sync_git(target=target, strategy=strategy, base_head=base_head)
  511	
  512	      with _write_context(repo_root) as write_root:
  513	          p = _load(write_root)
  514	          qid, _container, item = _find_item(p, id)
  515	          item.worktree_base_sha = base_head
  516	          _save(write_root, p)
  517	
  518	      return (
  519	          f"{qid}: synchronized by {strategy}; integrated {base_branch} at {base_head}\n"
  520	          f"previous worktree_base_sha: {previous_base}\n"
  521	          f"new worktree_base_sha: {base_head}\n"
  522	          "follow-up:\n"
  523	          f"  tasktool worktree status {qid} --integration\n"
  524	          "  rerun focused verification for files changed by the base integration\n"
  525	          "  regenerate derived artifacts if this project has snapshots, checksums, schemas, or lock files\n"
  526	      )
  527	  ```
  528	
  529	### 4.4 Run success tests, expect PASS
  530	
  531	- [ ] Run the same command as 4.2. Expected: `3 passed`.
  532	
  533	### 4.5 Commit
  534	
  535	- [ ] Run:
  536	  ```sh
  537	  git add tools/tasktool/commands.py tools/tasktool/tests/test_worktree_sync.py
  538	  git commit -m "P7.S5: sync worktree and advance base sha"
  539	  ```
  540	
  541	## Task 5 — Failure semantics and in-place coverage
  542	
  543	### 5.1 Add failing failure/in-place tests
  544	
  545	- [ ] Append to `tools/tasktool/tests/test_worktree_sync.py`:
  546	  ```python
  547	  def test_sync_conflict_leaves_worktree_base_sha_unchanged(tmp_path):
  548	      repo = init_repo(tmp_path / "repo")
  549	      wt = start_linked(repo)
  550	      old_base = slice_row(repo)["worktree_base_sha"]
  551	      (wt / "conflict.txt").write_text("slice\n")
  552	      git(wt, "add", "conflict.txt")
  553	      git(wt, "commit", "-q", "-m", "slice conflict")
  554	      (repo / "conflict.txt").write_text("base\n")
  555	      git(repo, "add", "conflict.txt")
  556	      git(repo, "commit", "-q", "-m", "base conflict")
  557	      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
  558	      assert r.returncode != 0
  559	      assert "git merge failed" in (r.stdout + r.stderr)
  560	      assert slice_row(repo)["worktree_base_sha"] == old_base
  561	
  562	
  563	  def test_sync_rebase_conflict_leaves_worktree_base_sha_unchanged(tmp_path):
  564	      repo = init_repo(tmp_path / "repo")
  565	      wt = start_linked(repo)
  566	      old_base = slice_row(repo)["worktree_base_sha"]
  567	      (wt / "conflict.txt").write_text("slice\n")
  568	      git(wt, "add", "conflict.txt")
  569	      git(wt, "commit", "-q", "-m", "slice conflict")
  570	      (repo / "conflict.txt").write_text("base\n")
  571	      git(repo, "add", "conflict.txt")
  572	      git(repo, "commit", "-q", "-m", "base conflict")
  573	      r = run(repo, "worktree", "sync", "P1.S1", "--rebase")
  574	      assert r.returncode != 0
  575	      assert "git rebase failed" in (r.stdout + r.stderr)
  576	      assert slice_row(repo)["worktree_base_sha"] == old_base
  577	
  578	
  579	  def test_sync_in_place_allows_staged_tasklist_and_advances_base_sha(tmp_path):
  580	      repo = init_repo(tmp_path / "repo")
  581	      assert run(repo, "start", "P1.S1", "--in-place").returncode == 0
  582	      base_head = advance_main(repo, "base-change", "base")
  583	      # Simulate routine tasktool staged tracker state in the authoritative checkout.
  584	      data = json.loads((repo / "docs" / "tasklist.json").read_text())
  585	      data["north_star"] = "staged tracker update"
  586	      (repo / "docs" / "tasklist.json").write_text(json.dumps(data, indent=2) + "\n")
  587	      git(repo, "add", "docs/tasklist.json")
  588	      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
  589	      assert r.returncode == 0, r.stdout + r.stderr
  590	      assert slice_row(repo)["worktree_base_sha"] == base_head
  591	      # This is an up-to-date merge of HEAD into itself while staged tracker
  592	      # bytes exist; git exits zero before requiring a clean index.
  593	      assert "synchronized by merge" in r.stdout
  594	  ```
  595	
  596	### 5.2 Run tests, expect FAIL if edge cases are missing
  597	
  598	- [ ] Run:
  599	  ```sh
  600	  python -m pytest tools/tasktool/tests/test_worktree_sync.py::test_sync_conflict_leaves_worktree_base_sha_unchanged tools/tasktool/tests/test_worktree_sync.py::test_sync_rebase_conflict_leaves_worktree_base_sha_unchanged tools/tasktool/tests/test_worktree_sync.py::test_sync_in_place_allows_staged_tasklist_and_advances_base_sha -q

[truncated: 93 additional lines]

## Context Previews

### docs/specs/2026-06-04-P7-S5-conservative-worktree-sync-design.md

    1	# P7.S5 — Conservative worktree sync
    2	
    3	**Status:** design (spec)
    4	**Date:** 2026-06-04
    5	**Slice ID:** `P7.S5`
    6	**Parent phase:** `P7 — Integration-surface-aware parallel slice safety`
    7	
    8	## 1. Problem
    9	
   10	`P7.S4` made stale worktrees visible: `tasktool worktree status <slice-id> --integration`
   11	reports when the configured base branch has advanced since a slice recorded
   12	`worktree_base_sha`, and whether sibling slices landed in that window. That
   13	is enough to detect risk, but the recovery step is still raw git.
   14	
   15	Raw git is too easy to run from the wrong checkout, against the wrong base, or
   16	with unresolved tracker drift. The phase design intentionally rejects an
   17	unconditional sync command; the mutating recovery path must be explicit,
   18	conservative, and auditable.
   19	
   20	## 2. Goals
   21	
   22	1. Add `tasktool worktree sync <slice-id> (--merge | --rebase)`.
   23	2. Refuse unless the slice has a recorded worktree or is explicitly in-place.
   24	3. Refuse unless `worktree_base_sha` is present and the configured authoritative
   25	   base branch resolves.
   26	4. Refuse unless the implementation worktree is clean and has no unresolved
   27	   merge state, with the staged-tasklist exception described below.
   28	5. Refuse if `docs/tasklist.json` has unsafe unstaged tasklist drift in the
   29	   authoritative checkout.
   30	6. On a successful merge or rebase, advance the slice's `worktree_base_sha` to
   31	   the base-branch HEAD that was integrated.
   32	7. Print follow-up instructions to rerun `worktree status --integration`,
   33	   regenerate derived artifacts, and rerun verification.
   34	
   35	## 3. Non-goals
   36	
   37	- No automatic conflict resolution. If merge or rebase conflicts, git stops and
   38	  `tasktool` must leave `worktree_base_sha` unchanged.
   39	- No default strategy. The caller must choose `--merge` or `--rebase`.
   40	- No remote fetching. The command integrates the local configured base branch.
   41	- No lifecycle status changes. Sync does not start, close, block, or ratify a
   42	  slice.
   43	- No skill-document updates. `P7.S6` owns the end-of-slice checkpoint and skill
   44	  wording.
   45	
   46	## 4. Command contract
   47	
   48	```sh
   49	tasktool worktree sync <slice-id> --merge
   50	tasktool worktree sync <slice-id> --rebase
   51	```
   52	
   53	`--merge` and `--rebase` are mutually exclusive and one is required.
   54	
   55	The command resolves the row through the existing authoritative routing used by
   56	other tasktool writes. The base branch comes only from
   57	`.tasktool/config.json` / `load_config(write_root).tasklist.authoritative_branch`;
   58	there is no hard-coded `main` fallback in command logic beyond the config
   59	default.
   60	
   61	## 5. Refusal rules
   62	
   63	The command refuses before invoking mutating git when any of these are true:
   64	
   65	1. The ID is not a slice.
   66	2. The slice has neither `worktree_in_place` nor a recorded `worktree_path`.
   67	3. A recorded linked worktree is not live and consistent according to the
   68	   existing `_health_for` classification.
   69	4. `worktree_base_sha` is missing.
   70	5. The configured base branch cannot be resolved to a commit SHA.
   71	6. The target worktree has uncommitted tracked changes, untracked files, or a
   72	   stash attributable to its current branch, using the existing
   73	   `worktree.working_tree_dirty` helper. When the target worktree is the
   74	   authoritative checkout, staged-only `docs/tasklist.json` is excluded from
   75	   this dirty check because tasktool itself commonly stages serialized tracker
   76	   mutations there.
   77	7. The target worktree has unresolved merge entries, detected with
   78	   `worktree.has_unmerged_paths(target_worktree)`.
   79	8. The authoritative checkout has unsafe unstaged `docs/tasklist.json` drift,
   80	   using `worktree.tasklist_has_unsafe_dirty_state(write_root)`.
   81	
   82	Staged-only `docs/tasklist.json` changes in the authoritative checkout are
   83	allowed. Existing tasktool commands commonly stage serialized tracker mutations;
   84	sync should not reject that safe state. Unstaged `docs/tasklist.json` bytes are
   85	still refused.
   86	
   87	For a linked worktree, git operations run in the resolved linked worktree path
   88	and tasklist writes run in the authoritative checkout. For an in-place slice,
   89	the target worktree is the repo root; if that checkout is already on the base
   90	branch, syncing base into itself is a no-op git operation that can still advance
   91	`worktree_base_sha` to the current base SHA.
   92	
   93	## 6. Success semantics
   94	
   95	Before running git, capture:
   96	
   97	- `base_branch` from config,
   98	- `base_head_before` from `current_branch_head_sha(write_root, base_branch)`,
   99	- `previous_worktree_base_sha` from the slice row.
  100	
  101	Run exactly one git operation in the target worktree, integrating the captured
  102	SHA rather than the moving branch ref:
  103	
  104	- `git merge --no-edit <base_head_before>` for `--merge`;
  105	- `git rebase <base_head_before>` for `--rebase`.
  106	
  107	After the operation succeeds, set `slice.worktree_base_sha = base_head_before`
  108	and save the tasklist. The command advances to the SHA it actually attempted to
  109	integrate, not a later base tip that may appear after the git command started.
  110	That makes the integrated SHA and the recorded SHA identical by construction.
  111	
  112	The git operation must not hold the tasktool lock. The implementation performs
  113	the git merge/rebase first, then re-enters the normal locked authoritative write
  114	path to re-read the row, set `worktree_base_sha`, and save. `git merge` must be
  115	non-interactive; use `--no-edit` and a subprocess environment that cannot open
  116	an editor.
  117	
  118	Output includes:
  119	
  120	- the slice ID,
  121	- the strategy used,
  122	- the base branch and integrated SHA,
  123	- the previous and new `worktree_base_sha`,
  124	- follow-up commands:
  125	  - `tasktool worktree status <slice-id> --integration`,
  126	  - project verification commands chosen by the implementer,
  127	  - regenerate derived artifacts when the project has generated snapshots,
  128	    checksums, schemas, or lock files.
  129	
  130	## 7. Failure semantics
  131	
  132	If git returns non-zero, the command raises a tasktool error and leaves
  133	`worktree_base_sha` unchanged. The user resolves or aborts the git state with
  134	normal git commands. If the user manually resolves and commits the merge or
  135	rebase outside tasktool, they should rerun the same
  136	`tasktool worktree sync ...` command afterward; git should report the captured
  137	base as already integrated, and the successful tasktool run can then advance
  138	`worktree_base_sha`.
  139	
  140	The command does not try to detect whether a failed merge/rebase partially
  141	integrated commits. The invariant is simple: `worktree_base_sha` advances only
  142	after the selected git command exits zero.
  143	
  144	`--rebase` rewrites the slice branch's commits. Callers should avoid it when
  145	another system already references the old commit SHAs, such as an in-flight
  146	review or pull request.
  147	
  148	## 8. File responsibilities
  149	
  150	| File | Responsibility |
  151	|------|----------------|
  152	| `tools/tasktool/cli.py` | Add the `worktree sync` subparser with required mutually exclusive `--merge` / `--rebase` flags and route it to commands. |
  153	| `tools/tasktool/commands.py` | Implement `cmd_worktree_sync`, row lookup, precondition checks, target worktree resolution, git invocation, base-SHA update, save, and human-readable output. |
  154	| `tools/tasktool/worktree.py` | Add small git helpers only if needed for clean sync implementation. Reuse existing helpers for branch resolution, dirty checks, and unresolved merge detection where possible. |
  155	| `tools/tasktool/tests/test_worktree_sync.py` | New focused tests for CLI contract, refusal cases, merge/rebase success, git-failure no-advance behavior, and staged-vs-unstaged tasklist drift. |
  156	
  157	## 9. Testing strategy
  158	
  159	Tests should build small local git repositories with `tasktool init-local`,
  160	phase/slice rows, and linked or in-place worktrees, following the style of
  161	`test_worktree_integration.py` and `test_worktree_prune.py`.
  162	
  163	Required coverage:
  164	
  165	1. Parser rejects `worktree sync` with neither strategy and with both strategies.
  166	2. A clean linked worktree can `--merge` the configured base branch and advances
  167	   `worktree_base_sha` to the pre-operation base head.
  168	3. A clean linked worktree can `--rebase` the configured base branch and advances
  169	   `worktree_base_sha` to the pre-operation base head.
  170	4. An in-place slice in a single-checkout repo syncs in the repo root and
  171	   advances `worktree_base_sha`, including when staged-only `docs/tasklist.json`
  172	   tracker bytes are present.
  173	5. Missing `worktree_base_sha` refuses before git mutation.
  174	6. Dirty target worktree refuses before git mutation.
  175	7. Unstaged authoritative `docs/tasklist.json` drift refuses; staged-only
  176	   tasklist changes do not.
  177	8. A merge conflict returns non-zero and leaves `worktree_base_sha` unchanged.
  178	9. `worktree status --integration` after a successful sync no longer reports
  179	   already-integrated base commits as ahead of `worktree_base_sha`.
  180	
  181	## 10. Scheduling
  182	
  183	`P7.S5` depends on `P7.S4` because it mutates the `worktree_base_sha` field that
  184	S4 records and uses S4's integration detection as its post-sync verification.
  185	It writes the `worktree` integration surface. It does not need to wait for
  186	`P7.S6` skill changes, because S6 documents this command after it lands.
  187	
  188	The slice remains independently plannable and executable now that `P7.S4` is
  189	done. It should not be parallel-dispatched with any other open slice that writes
  190	the `worktree` surface unless a dependency or `coordination_group` is declared.
### docs/tasklist.json

    1	{
    2	  "archived_cross_cutting": [
    3	    {
    4	      "archived_date": "2026-05-21",
    5	      "archived_path": "docs/archived-tasks/X15-archive-closed-cross-cutting-items.md",
    6	      "id": "X15",
    7	      "title": "Archive closed cross-cutting items"
    8	    },
    9	    {
   10	      "archived_date": "2026-05-21",
   11	      "archived_path": "docs/archived-tasks/X16-stamp-installed-shims-and-enforce-versio.md",
   12	      "id": "X16",
   13	      "title": "Stamp installed shims and enforce version drift refusal"
   14	    },
   15	    {
   16	      "archived_date": "2026-05-23",
   17	      "archived_path": "docs/archived-tasks/X18-harden-external-reviewer-caller-detectio.md",
   18	      "id": "X18",
   19	      "title": "Harden external reviewer caller detection for Codex"
   20	    },
   21	    {
   22	      "archived_date": "2026-05-23",
   23	      "archived_path": "docs/archived-tasks/X20-install-codex-todo-snapshot-hook.md",
   24	      "id": "X20",
   25	      "title": "Install Codex todo snapshot hook"
   26	    },
   27	    {
   28	      "archived_date": "2026-05-23",
   29	      "archived_path": "docs/archived-tasks/X19-install-todowrite-snapshot-hook-via-depl.md",
   30	      "id": "X19",
   31	      "title": "Install TodoWrite snapshot hook via deploy.sh"
   32	    },
   33	    {
   34	      "archived_date": "2026-05-23",
   35	      "archived_path": "docs/archived-tasks/X21-fix-codex-todo-snapshot-async-hook-regis.md",
   36	      "id": "X21",
   37	      "title": "Fix Codex todo snapshot async hook registration"
   38	    },
   39	    {
   40	      "archived_date": "2026-05-24",
   41	      "archived_path": "docs/archived-tasks/X22-add-cancelled-terminal-status-to-tasktoo.md",
   42	      "id": "X22",
   43	      "title": "Add cancelled terminal status to tasktool"
   44	    },
   45	    {
   46	      "archived_date": "2026-05-24",
   47	      "archived_path": "docs/archived-tasks/X23-document-cancelled-lifecycle-and-admin-c.md",
   48	      "id": "X23",
   49	      "title": "Document cancelled lifecycle and admin closeout guidance"
   50	    },
   51	    {
   52	      "archived_date": "2026-05-26",
   53	      "archived_path": "docs/archived-tasks/X24-use-global-tasktool-shim-in-superstar-gu.md",
   54	      "id": "X24",
   55	      "title": "Use global tasktool shim in Superstar guidance"
   56	    },
   57	    {
   58	      "archived_date": "2026-05-26",
   59	      "archived_path": "docs/archived-tasks/X25-duck-media-audio-during-tasktool-tts-and.md",
   60	      "id": "X25",
   61	      "title": "Duck media audio during tasktool TTS and verify Codex plugin payload"
   62	    },
   63	    {
   64	      "archived_date": "2026-05-26",
   65	      "archived_path": "docs/archived-tasks/X26-fix-codex-marketplace-payload-refresh-fo.md",
   66	      "id": "X26",
   67	      "title": "Fix Codex marketplace payload refresh for Superstar"
   68	    },
   69	    {
   70	      "archived_date": "2026-05-26",
   71	      "archived_path": "docs/archived-tasks/X1-default-external-review-prompt-transport.md",
   72	      "id": "X1",
   73	      "title": "Default external-review prompt transport to stdin"
   74	    },
   75	    {
   76	      "archived_date": "2026-05-26",
   77	      "archived_path": "docs/archived-tasks/X2-add-repo-local-tasktool-launcher.md",
   78	      "id": "X2",
   79	      "title": "Add repo-local tasktool launcher"
   80	    },
   81	    {
   82	      "archived_date": "2026-05-26",
   83	      "archived_path": "docs/archived-tasks/X3-spot-fix-parse-bold-external-review-verd.md",
   84	      "id": "X3",
   85	      "title": "Spot fix: parse bold external-review verdict headings"
   86	    },
   87	    {
   88	      "archived_date": "2026-05-26",
   89	      "archived_path": "docs/archived-tasks/X4-spot-fix-broaden-legacy-tasklist-importe.md",
   90	      "id": "X4",
   91	      "title": "Spot fix: broaden legacy tasklist importer compatibility"
   92	    },
   93	    {
   94	      "archived_date": "2026-05-26",
   95	      "archived_path": "docs/archived-tasks/X5-add-finished-agent-notification-hook.md",
   96	      "id": "X5",
   97	      "title": "Add finished-agent notification hook"
   98	    },
   99	    {
  100	      "archived_date": "2026-05-26",
  101	      "archived_path": "docs/archived-tasks/X6-fix-codex-finished-agent-hook-compatibil.md",
  102	      "id": "X6",
  103	      "title": "Fix Codex finished-agent hook compatibility"
  104	    },
  105	    {
  106	      "archived_date": "2026-05-26",
  107	      "archived_path": "docs/archived-tasks/X7-fix-superstar-codex-plugin-payload-versi.md",
  108	      "id": "X7",
  109	      "title": "Fix Superstar Codex plugin payload version drift"
  110	    },
  111	    {
  112	      "archived_date": "2026-05-26",
  113	      "archived_path": "docs/archived-tasks/X8-move-semantic-notifications-from-agent-h.md",
  114	      "id": "X8",
  115	      "title": "Move semantic notifications from agent hooks to tasktool status changes"
  116	    },
  117	    {
  118	      "archived_date": "2026-05-26",
  119	      "archived_path": "docs/archived-tasks/X9-coalesce-bursty-tasktool-audio-notificat.md",
  120	      "id": "X9",
  121	      "title": "Coalesce bursty tasktool audio notifications"
  122	    },
  123	    {
  124	      "archived_date": "2026-05-26",
  125	      "archived_path": "docs/archived-tasks/X10-harden-external-review-verdict-parser-an.md",
  126	      "id": "X10",
  127	      "title": "Harden external-review verdict parser and prompt against Claude formatting variants"
  128	    },
  129	    {
  130	      "archived_date": "2026-05-26",
  131	      "archived_path": "docs/archived-tasks/X11-make-external-review-bridge-global.md",
  132	      "id": "X11",
  133	      "title": "Make external-review bridge global"
  134	    },
  135	    {
  136	      "archived_date": "2026-05-26",
  137	      "archived_path": "docs/archived-tasks/X12-tasktool-require-authoritative-checkout-.md",
  138	      "id": "X12",
  139	      "title": "tasktool: require authoritative-checkout routing for mutations"
  140	    },
  141	    {
  142	      "archived_date": "2026-05-26",
  143	      "archived_path": "docs/archived-tasks/X13-fix-tasktool-close-repeated-refs-parsing.md",
  144	      "id": "X13",
  145	      "title": "Fix tasktool close repeated refs parsing"
  146	    },
  147	    {
  148	      "archived_date": "2026-05-26",
  149	      "archived_path": "docs/archived-tasks/X14-stabilize-local-claude-codex-plugin-curr.md",
  150	      "id": "X14",
  151	      "title": "Stabilize local Claude/Codex plugin current entrypoints"
  152	    },
  153	    {
  154	      "archived_date": "2026-05-26",
  155	      "archived_path": "docs/archived-tasks/X17-make-spec-and-plan-artifact-handling-tra.md",
  156	      "id": "X17",
  157	      "title": "Make spec and plan artifact handling transactional"
  158	    },
  159	    {
  160	      "archived_date": "2026-05-26",
  161	      "archived_path": "docs/archived-tasks/X27-add-tasktool-tts-for-workflow-artifacts-.md",
  162	      "id": "X27",
  163	      "title": "Add tasktool TTS for workflow artifacts and step changes"
  164	    },
  165	    {
  166	      "archived_date": "2026-05-26",
  167	      "archived_path": "docs/archived-tasks/X28-prefer-explicit-notification-ding-sound-.md",
  168	      "id": "X28",
  169	      "title": "Prefer explicit notification ding sound file"
  170	    }
  171	  ],
  172	  "archived_phases": [
  173	    {
  174	      "archived_date": "2026-05-18",
  175	      "archived_path": "docs/archived-tasks/P2-tasktool-json-backed-task-management-cli.md",
  176	      "id": "P2",
  177	      "title": "tasktool: JSON-backed task management CLI"
  178	    },
  179	    {
  180	      "archived_date": "2026-05-19",
  181	      "archived_path": "docs/archived-tasks/P4-tasktool-coordination-and-lifecycle-auth.md",
  182	      "id": "P4",
  183	      "title": "Tasktool coordination and lifecycle authority"
  184	    },
  185	    {
  186	      "archived_date": "2026-05-19",
  187	      "archived_path": "docs/archived-tasks/P3-phase-planning-workflow.md",
  188	      "id": "P3",
  189	      "title": "Phase planning workflow"
  190	    },
  191	    {
  192	      "archived_date": "2026-05-20",
  193	      "archived_path": "docs/archived-tasks/P1-external-reviewer-work-historical.md",
  194	      "id": "P1",
  195	      "title": "External-reviewer work (historical)"
  196	    },
  197	    {
  198	      "archived_date": "2026-05-21",
  199	      "archived_path": "docs/archived-tasks/P5-tasktool-owned-worktree-lifecycle-using-.md",
  200	      "id": "P5",

[truncated: 272 additional lines]

<!-- superstar-prompt:end -->