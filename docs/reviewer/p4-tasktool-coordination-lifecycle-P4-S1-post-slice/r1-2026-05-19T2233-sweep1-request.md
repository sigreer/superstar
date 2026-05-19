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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/p4-s1-tasktool-authority

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md

Additional context files:
- docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md
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
  201	    )
  202	    save_config(repo_root, cfg)
  203	    _git_stage(repo_root, repo_root / ".tasktool" / "config.json")
  204	```
  205	
  206	In `tools/tasktool/cli.py`, add a `config` command group:
  207	
  208	```python
  209	p_config = sub.add_parser("config")
  210	config_sub = p_config.add_subparsers(dest="config_cmd", required=True)
  211	p_config_auth = config_sub.add_parser("init-authority")
  212	p_config_auth.add_argument("--branch", default="main")
  213	```
  214	
  215	And dispatch:
  216	
  217	```python
  218	elif args.cmd == "config":
  219	    if args.config_cmd == "init-authority":
  220	        commands.cmd_config_init_authority(
  221	            repo_root=root,
  222	            branch=args.branch,
  223	        )
  224	```
  225	
  226	Run:
  227	
  228	```sh
  229	python -m pytest tools/tasktool/tests/test_authority_config.py tools/tasktool/tests/test_cli_integration.py::test_config_init_authority_writes_project_config -v
  230	```
  231	
  232	Expected: PASS.
  233	
  234	- [ ] **Step 5: Commit**
  235	
  236	```sh
  237	git add tools/tasktool/config.py tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/tests/test_authority_config.py tools/tasktool/tests/test_cli_integration.py
  238	git commit -m "tasktool: add authoritative checkout config"
  239	```
  240	
  241	### Task 2: Git Worktree Authority Detection
  242	
  243	**Files:**
  244	- Create: `tools/tasktool/worktree.py`
  245	- Test: `tools/tasktool/tests/test_worktree_authority.py`
  246	
  247	- [ ] **Step 1: Write failing worktree helper tests**
  248	
  249	Create `tools/tasktool/tests/test_worktree_authority.py`:
  250	
  251	```python
  252	import os
  253	import subprocess
  254	from pathlib import Path
  255	
  256	from tasktool.worktree import (
  257	    AuthorityError,
  258	    find_authoritative_root,
  259	    git_common_dir,
  260	    git_current_branch,
  261	    same_repository,
  262	    tasklist_has_unsafe_dirty_state,
  263	    validate_authoritative_checkout,
  264	)
  265	
  266	def _git(cwd, *args):
  267	    return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True)
  268	
  269	def _repo(tmp_path):
  270	    root = tmp_path / "repo"
  271	    root.mkdir()
  272	    _git(root, "init", "-b", "main")
  273	    _git(root, "config", "user.email", "tasktool-tests@example.invalid")
  274	    _git(root, "config", "user.name", "Tasktool Tests")
  275	    (root / "README.md").write_text("x\n")
  276	    _git(root, "add", "README.md")
  277	    _git(root, "commit", "-m", "init")
  278	    return root
  279	
  280	def test_git_common_dir_is_shared_by_linked_worktree(tmp_path):
  281	    root = _repo(tmp_path)
  282	    worker = tmp_path / "worker"
  283	    _git(root, "worktree", "add", "-b", "worker", str(worker))
  284	    assert git_common_dir(root) == git_common_dir(worker)
  285	
  286	def test_validate_authoritative_checkout_rejects_wrong_branch(tmp_path):
  287	    root = _repo(tmp_path)
  288	    _git(root, "checkout", "-b", "other")
  289	    try:
  290	        validate_authoritative_checkout(root, expected_branch="main", caller_root=root)
  291	    except AuthorityError as exc:
  292	        assert "expected branch main" in str(exc)
  293	    else:
  294	        raise AssertionError("expected AuthorityError")
  295	
  296	def test_same_repository_true_for_linked_worktree(tmp_path):
  297	    root = _repo(tmp_path)
  298	    worker = tmp_path / "worker"
  299	    _git(root, "worktree", "add", "-b", "worker", str(worker))
  300	    assert same_repository(root, worker)
  301	
  302	def test_find_authoritative_root_uses_branch_worktree(tmp_path):
  303	    root = _repo(tmp_path)
  304	    worker = tmp_path / "worker"
  305	    _git(root, "worktree", "add", "-b", "worker", str(worker))
  306	    assert find_authoritative_root(worker, branch="main") == root
  307	
  308	def test_find_authoritative_root_fails_closed_when_missing(tmp_path):
  309	    root = _repo(tmp_path)
  310	    _git(root, "checkout", "-b", "feature")
  311	    try:
  312	        find_authoritative_root(root, branch="main")
  313	    except AuthorityError as exc:
  314	        assert "TASKTOOL_AUTHORITY_ROOT" in str(exc)
  315	    else:
  316	        raise AssertionError("expected AuthorityError")
  317	```
  318	
  319	Run: `python -m pytest tools/tasktool/tests/test_worktree_authority.py -v`
  320	Expected: FAIL because `tasktool.worktree` does not exist.
  321	
  322	- [ ] **Step 2: Implement worktree helpers**
  323	
  324	Create `tools/tasktool/worktree.py`:
  325	
  326	```python
  327	from __future__ import annotations
  328	
  329	import contextlib
  330	import os
  331	import subprocess
  332	import time
  333	from pathlib import Path
  334	
  335	class AuthorityError(RuntimeError):
  336	    pass
  337	
  338	def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
  339	    return subprocess.run(
  340	        ["git", *args],
  341	        cwd=root,
  342	        text=True,
  343	        capture_output=True,
  344	        check=check,
  345	    )
  346	
  347	def git_common_dir(root: Path) -> Path:
  348	    out = _git(root, "rev-parse", "--git-common-dir").stdout.strip()
  349	    path = Path(out)
  350	    return path if path.is_absolute() else (root / path).resolve()
  351	
  352	def git_current_branch(root: Path) -> str:
  353	    return _git(root, "branch", "--show-current").stdout.strip()
  354	
  355	def same_repository(left: Path, right: Path) -> bool:
  356	    try:
  357	        return git_common_dir(left) == git_common_dir(right)
  358	    except subprocess.CalledProcessError:
  359	        return False
  360	
  361	def worktree_roots(root: Path) -> list[tuple[Path, str]]:
  362	    result = _git(root, "worktree", "list", "--porcelain")
  363	    rows: list[tuple[Path, str]] = []
  364	    current_path: Path | None = None
  365	    current_branch = ""
  366	    for line in result.stdout.splitlines():
  367	        if line.startswith("worktree "):
  368	            if current_path is not None:
  369	                rows.append((current_path, current_branch))
  370	            current_path = Path(line.removeprefix("worktree ")).resolve()
  371	            current_branch = ""
  372	        elif line.startswith("branch "):
  373	            current_branch = line.removeprefix("branch refs/heads/")
  374	    if current_path is not None:
  375	        rows.append((current_path, current_branch))
  376	    return rows
  377	
  378	def find_authoritative_root(caller_root: Path, *, branch: str) -> Path:
  379	    env_root = os.environ.get("TASKTOOL_AUTHORITY_ROOT")
  380	    if env_root:
  381	        return Path(env_root).expanduser().resolve()
  382	    matches = [path for path, item_branch in worktree_roots(caller_root) if item_branch == branch]
  383	    if len(matches) == 1:
  384	        return matches[0]
  385	    raise AuthorityError(
  386	        f"cannot determine authoritative checkout for branch {branch}; "
  387	        "set TASKTOOL_AUTHORITY_ROOT=/absolute/path"
  388	    )
  389	
  390	def has_unmerged_paths(root: Path) -> bool:
  391	    out = _git(root, "ls-files", "-u").stdout.strip()
  392	    return bool(out)
  393	
  394	def tasklist_dirty(root: Path) -> bool:
  395	    result = _git(root, "status", "--porcelain", "--", "docs/tasklist.json", check=False)
  396	    return bool(result.stdout.strip())
  397	
  398	def tasklist_has_unsafe_dirty_state(root: Path) -> bool:
  399	    """Return True when tasklist has unstaged changes.
  400	
  401	    Staged-only tasklist changes are allowed: they are the serialized pending
  402	    state from earlier tasktool commands in the same authoritative checkout.
  403	    Unstaged tasklist bytes are refused because tasktool cannot attribute them.
  404	    """
  405	    result = _git(root, "status", "--porcelain", "--", "docs/tasklist.json", check=False)
  406	    for line in result.stdout.splitlines():
  407	        if len(line) >= 2 and line[1] != " ":
  408	            return True
  409	    return False
  410	
  411	def validate_authoritative_checkout(
  412	    root: Path,
  413	    *,
  414	    expected_branch: str,
  415	    caller_root: Path,
  416	) -> None:
  417	    root = root.resolve()
  418	    if not (root / ".git").exists() and not (root / ".git").is_file():
  419	        raise AuthorityError(f"authoritative_root is not a git checkout: {root}")
  420	    if not same_repository(root, caller_root):
  421	        raise AuthorityError("authoritative_root is not the same repository as caller")
  422	    branch = git_current_branch(root)
  423	    if branch != expected_branch:
  424	        raise AuthorityError(f"authoritative checkout is on {branch!r}; expected branch {expected_branch}")
  425	    if has_unmerged_paths(root):
  426	        raise AuthorityError("authoritative checkout has unresolved merge conflicts")
  427	
  428	@contextlib.contextmanager
  429	def tasktool_lock(repo_root: Path, timeout_seconds: float = 30.0):
  430	    timeout_seconds = float(os.environ.get("TASKTOOL_LOCK_TIMEOUT", timeout_seconds))
  431	    lock_path = git_common_dir(repo_root) / "tasktool.lock"
  432	    start = time.monotonic()
  433	    fd = None
  434	    while True:
  435	        try:
  436	            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
  437	            os.write(fd, str(os.getpid()).encode("ascii"))
  438	            break
  439	        except FileExistsError:
  440	            if time.monotonic() - start > timeout_seconds:
  441	                raise AuthorityError(f"timed out waiting for tasktool lock: {lock_path}")
  442	            time.sleep(0.05)
  443	    try:
  444	        yield
  445	    finally:
  446	        if fd is not None:
  447	            os.close(fd)
  448	        with contextlib.suppress(FileNotFoundError):
  449	            lock_path.unlink()
  450	```
  451	
  452	Run: `python -m pytest tools/tasktool/tests/test_worktree_authority.py -v`
  453	Expected: PASS.
  454	
  455	- [ ] **Step 3: Add dirty tasklist validation test**
  456	
  457	Append:
  458	
  459	```python
  460	def test_validate_authoritative_checkout_permits_dirty_tasklist_check_to_caller(tmp_path):
  461	    root = _repo(tmp_path)
  462	    (root / "docs").mkdir()
  463	    (root / "docs" / "tasklist.json").write_text("{}\n")
  464	    assert validate_authoritative_checkout(root, expected_branch="main", caller_root=root) is None
  465	```
  466	
  467	Staged-only tasklist changes are allowed, but unstaged tasklist bytes are unsafe. Add this test:
  468	
  469	```python
  470	def test_unsafe_tasklist_dirty_state_detects_unstaged_bytes(tmp_path):
  471	    root = _repo(tmp_path)
  472	    (root / "docs").mkdir()
  473	    (root / "docs" / "tasklist.json").write_text("{}\n")
  474	    _git(root, "add", "docs/tasklist.json")
  475	    assert tasklist_has_unsafe_dirty_state(root) is False
  476	    (root / "docs" / "tasklist.json").write_text('{"changed":true}\n')
  477	    assert tasklist_has_unsafe_dirty_state(root) is True
  478	```
  479	
  480	- [ ] **Step 4: Commit**
  481	
  482	```sh
  483	git add tools/tasktool/worktree.py tools/tasktool/tests/test_worktree_authority.py
  484	git commit -m "tasktool: add git worktree authority helpers"
  485	```
  486	
  487	### Task 3: Route Mutating Commands Through Authority
  488	
  489	**Files:**
  490	- Modify: `tools/tasktool/commands.py`
  491	- Test: `tools/tasktool/tests/test_worktree_authority.py`
  492	- Test: `tools/tasktool/tests/test_cli_integration.py`
  493	
  494	- [ ] **Step 1: Write failing routing integration test**
  495	
  496	Append to `tools/tasktool/tests/test_worktree_authority.py`:
  497	
  498	```python
  499	import json
  500	import sys
  501	
  502	TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
  503	
  504	def _tasktool(cwd, *args):
  505	    return subprocess.run(
  506	        [sys.executable, str(TOOL), *args],
  507	        cwd=cwd,
  508	        text=True,
  509	        capture_output=True,
  510	    )
  511	
  512	def _seed_tasktool_repo(tmp_path):
  513	    root = _repo(tmp_path)
  514	    (root / "docs").mkdir()
  515	    r = _tasktool(root, "init", "--project", "demo")
  516	    assert r.returncode == 0, r.stdout + r.stderr
  517	    r = _tasktool(root, "create", "phase", "--title", "P")
  518	    assert r.returncode == 0, r.stdout + r.stderr
  519	    r = _tasktool(root, "create", "slice", "P1", "--title", "S")
  520	    assert r.returncode == 0, r.stdout + r.stderr
  521	    _git(root, "add", ".")
  522	    _git(root, "commit", "-m", "tasklist")
  523	    return root
  524	
  525	def test_worker_mutation_updates_authority_not_worker(tmp_path):
  526	    root = _seed_tasktool_repo(tmp_path)
  527	    r = _tasktool(root, "config", "init-authority", "--branch", "main")
  528	    assert r.returncode == 0, r.stdout + r.stderr
  529	    _git(root, "add", ".tasktool/config.json")
  530	    _git(root, "commit", "-m", "configure tasktool authority")
  531	
  532	    worker = tmp_path / "worker"
  533	    _git(root, "worktree", "add", "-b", "worker", str(worker))
  534	    before_worker = (worker / "docs/tasklist.json").read_text()
  535	
  536	    r = _tasktool(worker, "set", "P1.S1", "--status", "in_progress")
  537	    assert r.returncode == 0, r.stdout + r.stderr
  538	    assert "authoritative checkout" in r.stderr
  539	    assert (worker / "docs/tasklist.json").read_text() == before_worker
  540	
  541	    authority = json.loads((root / "docs/tasklist.json").read_text())
  542	    assert authority["phases"][0]["slices"][0]["status"] == "in_progress"
  543	
  544	def test_authoritative_checkout_write_uses_same_lock(tmp_path):
  545	    root = _seed_tasktool_repo(tmp_path)
  546	    r = _tasktool(root, "config", "init-authority", "--branch", "main")
  547	    assert r.returncode == 0, r.stdout + r.stderr
  548	    common = git_common_dir(root)
  549	    (common / "tasktool.lock").write_text("held")
  550	    r = subprocess.run(
  551	        [sys.executable, str(TOOL), "set", "P1.S1", "--status", "in_progress"],
  552	        cwd=root,
  553	        text=True,
  554	        capture_output=True,
  555	        env={**os.environ, "TASKTOOL_LOCK_TIMEOUT": "0.1"},
  556	    )
  557	    assert r.returncode == 1
  558	    assert "timed out waiting for tasktool lock" in r.stderr
  559	
  560	def test_authoritative_unstaged_tasklist_refuses_before_mutation(tmp_path):
  561	    root = _seed_tasktool_repo(tmp_path)
  562	    r = _tasktool(root, "config", "init-authority", "--branch", "main")
  563	    assert r.returncode == 0, r.stdout + r.stderr
  564	    _git(root, "add", ".")
  565	    _git(root, "commit", "-m", "authority")
  566	    (root / "docs/tasklist.json").write_text('{"manual":"edit"}\n')
  567	    r = _tasktool(root, "set", "P1.S1", "--status", "in_progress")
  568	    assert r.returncode == 1
  569	    assert "unstaged changes" in r.stderr
  570	```
  571	
  572	Run: `python -m pytest tools/tasktool/tests/test_worktree_authority.py::test_worker_mutation_updates_authority_not_worker -v`
  573	Expected: FAIL because commands still mutate the current checkout.
  574	
  575	- [ ] **Step 2: Add write root resolution**
  576	
  577	In `tools/tasktool/commands.py`, add imports:
  578	
  579	```python
  580	import sys
  581	from contextlib import contextmanager
  582	from tasktool.config import load_config
  583	from tasktool.worktree import (
  584	    AuthorityError,
  585	    find_authoritative_root,
  586	    same_repository,
  587	    tasklist_has_unsafe_dirty_state,
  588	    tasktool_lock,
  589	    validate_authoritative_checkout,
  590	)
  591	```
  592	
  593	Add helper:
  594	
  595	```python
  596	def _resolve_write_root(repo_root: Path) -> tuple[Path, bool]:
  597	    cfg = load_config(repo_root)
  598	    if cfg.tasklist.mutation_mode == "local":
  599	        return repo_root, False
  600	    authoritative = find_authoritative_root(repo_root, branch=cfg.tasklist.authoritative_branch)

[truncated: 743 additional lines]

## Context Previews

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

[truncated: 5 additional lines]
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
   17	      "status": "done",
   18	      "title": "Default external-review prompt transport to stdin"
   19	    },
   20	    {
   21	      "closed": "2026-05-18",
   22	      "created": "2026-05-18",
   23	      "id": "X2",
   24	      "notes": "Added repo-local tools/tasktool/tasktool launcher, updated tasklist/project-setup docs to prefer it, and taught the pre-commit hook to use the repo-local launcher before falling back to a global tasktool shim.",
   25	      "refs": [],
   26	      "status": "done",
   27	      "title": "Add repo-local tasktool launcher"
   28	    },
   29	    {
   30	      "closed": "2026-05-19",
   31	      "created": "2026-05-19",
   32	      "id": "X3",
   33	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. External-review verdict parsing now accepts markdown-emphasized Overall Verdict headings such as **5. Overall Verdict** followed by ready/revise text.",
   34	      "refs": [
   35	        "skills/external-review/scripts/external-reviewer.py",
   36	        "skills/external-review/tests/test_heading_style_verdict.py"
   37	      ],
   38	      "status": "done",
   39	      "title": "Spot fix: parse bold external-review verdict headings"
   40	    },
   41	    {
   42	      "closed": "2026-05-19",
   43	      "created": "2026-05-19",
   44	      "id": "X4",
   45	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. Legacy markdown import now accepts fully-qualified slice IDs and additional cross-cutting forms including tagged done items, blocked cross rows coerced to ready, and archived cross rows treated as done.",
   46	      "refs": [
   47	        "tools/tasktool/importer.py"
   48	      ],
   49	      "status": "done",
   50	      "title": "Spot fix: broaden legacy tasklist importer compatibility"
   51	    },
   52	    {
   53	      "closed": "2026-05-19",
   54	      "created": "2026-05-19",
   55	      "id": "X5",
   56	      "notes": "User-requested hook update completed outside the normal workflow for speed. Adds Stop/SubagentStop finished-agent notifications, milestone message derivation from final agent text/transcript payloads, Hypr TTS config reuse with OPENAI_API_KEY fallback, and non-TTS ding fallbacks.\nSuperseded by X8: final-text milestone parsing was removed; agent hooks now emit generic dings and semantic spoken notifications come from tasktool status changes.",
   57	      "refs": [
   58	        "hooks/agent-finished",
   59	        "hooks/hooks.json",
   60	        "hooks/hooks-cursor.json",
   61	        "tests/claude-code/test-agent-finished-hook.sh"
   62	      ],
   63	      "status": "done",
   64	      "title": "Add finished-agent notification hook"
   65	    },
   66	    {
   67	      "closed": "2026-05-19",
   68	      "created": "2026-05-19",
   69	      "id": "X6",
   70	      "notes": "Codex startup skips Stop/SubagentStop notification hooks when hooks.json uses async=true; fix should preserve finished-agent notification behavior while avoiding unsupported async hook registration in Codex.\nSet finished-agent Stop/SubagentStop hook registrations to async=false for Codex compatibility. The hook now backgrounds real notification playback internally so synchronous hook registration returns quickly while dry-run tests remain foreground and deterministic.",
   71	      "refs": [
   72	        "hooks/hooks.json",
   73	        "hooks/agent-finished",
   74	        "tests/claude-code/test-hook-config.sh",
   75	        "tests/claude-code/test-agent-finished-hook.sh"
   76	      ],
   77	      "status": "done",
   78	      "title": "Fix Codex finished-agent hook compatibility"
   79	    },
   80	    {
   81	      "closed": "2026-05-19",
   82	      "created": "2026-05-19",
   83	      "id": "X7",
   84	      "notes": "Codex reported superstar/6.0.0 because the installable local marketplace payload under plugins/superstar still declared version 6.0.0 and the version bump audit did not track that embedded manifest.\n\nBumped the embedded Codex plugin payload manifest to 6.0.1 and added it to the version bump check. Reinstalled superstar@superstar-dev, then rebuilt the 6.0.1 runtime cache as a materialized copy of this checkout with .agents excluded so Codex sees the full skills/hooks tree while codex plugin list still reports installed/enabled. Final probe shows cache version 6.0.1, skills/hooks present, and no async-hook warning.",
   85	      "refs": [
   86	        ".version-bump.json",
   87	        "plugins/superstar/.codex-plugin/plugin.json",
   88	        ".agents/plugins/marketplace.json",
   89	        "tests/codex-plugin-sync/test-version-drift.sh",
   90	        "tests/codex-plugin-sync/test-local-marketplace.sh"
   91	      ],
   92	      "status": "done",
   93	      "title": "Fix Superstar Codex plugin payload version drift"
   94	    },
   95	    {
   96	      "closed": "2026-05-19",
   97	      "created": "2026-05-19",
   98	      "id": "X8",
   99	      "notes": "Move semantic spoken notifications to tasktool status transitions for ready/in_progress/blocked/done. Keep agent Stop/SubagentStop hooks as generic completion dings only, with different sound styles for Claude and Codex.\nAgent Stop/SubagentStop hooks now emit generic harness-specific dings only. Semantic spoken notifications moved to tasktool status events for ready, in_progress, blocked, and done, including create, set, close, block, unblock, and archive-phase paths.",
  100	      "refs": [
  101	        "hooks/agent-finished",
  102	        "tools/tasktool/notify.py",
  103	        "tools/tasktool/commands.py",
  104	        "tools/tasktool/tests/test_notify.py",
  105	        "tools/tasktool/tests/test_commands.py",
  106	        "tools/tasktool/tests/conftest.py",
  107	        "tests/claude-code/test-agent-finished-hook.sh"
  108	      ],
  109	      "status": "done",
  110	      "title": "Move semantic notifications from agent hooks to tasktool status changes"
  111	    },
  112	    {
  113	      "closed": "2026-05-19",
  114	      "created": "2026-05-19",
  115	      "id": "X9",
  116	      "notes": "Rapid tasktool status changes currently spawn independent notifier processes, causing overlapping TTS/audio. Add a single-audio queue with at most three queued tasktool events; overflow should collapse to a single 'multiple other events' summary and drop further items.\nAdded a file-backed notification queue shared by agent dings and tasktool TTS. Only one worker drains audio at a time. Queue capacity is three pending events; overflow keeps the first two pending items and replaces the rest with a single 'Multiple other events' summary, dropping further burst items while the summary remains queued.",
  117	      "refs": [
  118	        "tools/tasktool/notify.py",
  119	        "tools/tasktool/tests/test_notify.py"
  120	      ],
  121	      "status": "done",
  122	      "title": "Coalesce bursty tasktool audio notifications"
  123	    }
  124	  ],
  125	  "last_reviewed": "2026-05-18",
  126	  "north_star": "",
  127	  "phases": [
  128	    {
  129	      "closed": "2026-05-17",
  130	      "created": "2026-05-17",
  131	      "id": "P1",
  132	      "notes": "",
  133	      "phase_reviewer_chain": null,
  134	      "plan_path": null,
  135	      "planning_path": null,
  136	      "slices": [],
  137	      "spec_path": null,
  138	      "status": "done",
  139	      "title": "External-reviewer work (historical)"
  140	    },
  141	    {
  142	      "closed": null,
  143	      "created": "2026-05-19",
  144	      "id": "P3",
  145	      "notes": "",
  146	      "phase_reviewer_chain": null,
  147	      "plan_path": null,
  148	      "planning_path": "docs/specs/2026-05-19-p3-phase-planning-design.md",
  149	      "slices": [
  150	        {
  151	          "blocked_on": null,
  152	          "closed": null,
  153	          "created": "2026-05-19",
  154	          "depends_on": [],
  155	          "id": "S1",
  156	          "notes": "",
  157	          "parallel_group": "foundation",
  158	          "plan_path": null,
  159	          "planning_status": "ratified",
  160	          "refs": [],
  161	          "reviewer_chain": null,
  162	          "status": "ready",
  163	          "tasks": [],
  164	          "title": "Schema and validation foundation"
  165	        },
  166	        {
  167	          "blocked_on": null,
  168	          "closed": null,
  169	          "created": "2026-05-19",
  170	          "depends_on": [
  171	            "P3.S1"
  172	          ],
  173	          "id": "S2",
  174	          "notes": "",
  175	          "parallel_group": "cli",
  176	          "plan_path": null,
  177	          "planning_status": "ratified",
  178	          "refs": [],
  179	          "reviewer_chain": null,
  180	          "status": "ready",
  181	          "tasks": [],
  182	          "title": "Scheduling CLI"
  183	        },
  184	        {
  185	          "blocked_on": null,
  186	          "closed": null,
  187	          "created": "2026-05-19",
  188	          "depends_on": [
  189	            "P3.S1"
  190	          ],
  191	          "id": "S3",
  192	          "notes": "",
  193	          "parallel_group": "workflow",
  194	          "plan_path": null,
  195	          "planning_status": "ratified",
  196	          "refs": [],
  197	          "reviewer_chain": null,
  198	          "status": "ready",
  199	          "tasks": [],
  200	          "title": "Workflow skill and integration docs"

[truncated: 77 additional lines]

<!-- superstar-prompt:end -->