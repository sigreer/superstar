# P7.S5 — Conservative worktree sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `tasktool worktree sync <slice-id> (--merge | --rebase)` so a stale slice worktree can explicitly integrate the configured base branch and advance `worktree_base_sha` only after a successful git operation.

**Architecture:** The command is a conservative mutating worktree operation. It performs read-only preflight against the resolved authoritative checkout, runs exactly one non-interactive git operation in the target worktree without holding the tasktool lock, then re-enters the locked authoritative write path to update `worktree_base_sha` to the captured base SHA. Refusals are strict: no missing base SHA, no unhealthy linked worktree, no unresolved merge state, no unsafe target dirt, and no unstaged authoritative `docs/tasklist.json` drift.

**Tech Stack:** Python 3, argparse, git plumbing, pytest

---

## Scheduling

- **Slice:** `P7.S5`.
- **depends_on:** `P7.S4`, which already records `worktree_base_sha`, stamps `landed_base_sha`, and provides `worktree status --integration`.
- **parallel_group:** none.
- **integration surfaces:** `worktree`.
- **reservations:** none.
- **independent execution:** yes, now that `P7.S4` is done. Do not parallel-dispatch this with another open slice that writes `worktree` unless a dependency or `coordination_group` is declared.
- **test scope note:** most worktree tests in this repo use `config init-local`, matching existing `test_worktree_integration.py` fixtures. The implementation still uses `_write_context` for the row update so authoritative-checkout mode takes the normal lock/route path; full routed-mode behavior is covered indirectly by existing tasktool routing tests and the final real-slice dogfood step.

Before editing implementation files, run:

```sh
./tools/tasktool/tasktool start P7.S5
```

Expected: tasktool records/prints the worktree path, flips `P7.S5` to `in_progress`, and records `worktree_base_sha`. `cd` into the printed worktree path and do all source edits there.

## File Structure

| File | Responsibility |
|------|----------------|
| `tools/tasktool/cli.py` | Add `worktree sync <id>` parser with required mutually exclusive `--merge` / `--rebase`, and dispatch to `commands.cmd_worktree_sync`. |
| `tools/tasktool/worktree.py` | Add one helper that reports worktree dirt while allowing staged-only `docs/tasklist.json` for in-place authoritative sync. Reuse `has_unmerged_paths`, `current_branch_head_sha`, and `_git`. |
| `tools/tasktool/commands.py` | Add target resolution and `cmd_worktree_sync`: preflight, run git without the tasktool lock, then update `worktree_base_sha` through `_write_context`. |
| `tools/tasktool/tests/test_worktree_sync.py` | New focused CLI tests for parser behavior, merge/rebase success, refusal cases, conflict no-advance, and post-sync integration status. |

## Task 1 — Start the slice and add parser coverage

### 1.1 Start the slice

- [ ] Run:
  ```sh
  ./tools/tasktool/tasktool start P7.S5
  ```
  Expected: output includes `cd .worktrees/worktree-p7-s5-...`. Change into that path before continuing.

### 1.2 Create failing parser tests

- [ ] Create `tools/tasktool/tests/test_worktree_sync.py`:
  ```python
  from __future__ import annotations

  import json
  import os
  import subprocess
  import sys
  from pathlib import Path

  TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
  PYTHONPATH = str(Path(__file__).resolve().parents[2])


  def run(root: Path, *args: str):
      env = os.environ.copy()
      env["PYTHONPATH"] = PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
      env["GIT_EDITOR"] = "false"
      return subprocess.run(
          [sys.executable, str(TOOL), "--project-root", str(root), *args],
          text=True,
          capture_output=True,
          env=env,
      )


  def git(cwd: Path, *args: str) -> str:
      return subprocess.run(
          ["git", *args], cwd=cwd, text=True, capture_output=True, check=True
      ).stdout


  def init_repo(root: Path) -> Path:
      root.mkdir()
      git(root, "init", "-q", "-b", "main")
      git(root, "config", "user.email", "t@example.invalid")
      git(root, "config", "user.name", "T")
      (root / "docs").mkdir()
      assert run(root, "config", "init-local").returncode == 0
      assert run(root, "init", "--project", "demo").returncode == 0
      git(root, "add", "-A")
      git(root, "commit", "-q", "-m", "init")
      assert run(root, "create", "phase", "--title", "Phase 1").returncode == 0
      assert run(root, "create", "slice", "P1", "--title", "Sync target").returncode == 0
      git(root, "add", "-A")
      git(root, "commit", "-q", "-m", "seed slice")
      return root


  def slice_row(repo: Path, qid: str = "P1.S1") -> dict:
      data = json.loads((repo / "docs" / "tasklist.json").read_text())
      return next(
          s for ph in data["phases"] for s in ph["slices"]
          if f"{ph['id']}.{s['id']}" == qid
      )


  def start_linked(repo: Path) -> Path:
      r = run(repo, "start", "P1.S1")
      assert r.returncode == 0, r.stdout + r.stderr
      return (repo / slice_row(repo)["worktree_path"]).resolve()


  def advance_main(repo: Path, name: str, content: str = "x") -> str:
      (repo / name).write_text(content + "\n")
      git(repo, "add", name)
      git(repo, "commit", "-q", "-m", f"main {name}")
      return git(repo, "rev-parse", "main").strip()


  def test_sync_requires_exactly_one_strategy(tmp_path):
      repo = init_repo(tmp_path / "repo")
      no_strategy = run(repo, "worktree", "sync", "P1.S1")
      assert no_strategy.returncode != 0
      assert "one of the arguments --merge --rebase is required" in no_strategy.stderr
      both = run(repo, "worktree", "sync", "P1.S1", "--merge", "--rebase")
      assert both.returncode != 0
      assert "not allowed with argument" in both.stderr
  ```

### 1.3 Run parser test, expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_sync.py::test_sync_requires_exactly_one_strategy -q
  ```
  Expected: FAIL because `worktree sync` is not a known subcommand.

### 1.4 Add CLI parser and dispatch

- [ ] Modify `tools/tasktool/cli.py` near the other `worktree` subcommands:
  ```python
      p_wt_sync = wt_sub.add_parser("sync")
      p_wt_sync.add_argument("id")
      sync_mode = p_wt_sync.add_mutually_exclusive_group(required=True)
      sync_mode.add_argument("--merge", action="store_true")
      sync_mode.add_argument("--rebase", action="store_true")
  ```

- [ ] Modify the `elif args.cmd == "worktree":` dispatch block:
  ```python
              elif args.wt_cmd == "sync":
                  sys.stdout.write(
                      commands.cmd_worktree_sync(
                          repo_root=root,
                          id=args.id,
                          merge=args.merge,
                          rebase=args.rebase,
                      )
                  )
  ```

### 1.5 Add command stub

- [ ] Add this stub in `tools/tasktool/commands.py` before `cmd_worktree_adopt`:
  ```python
  def cmd_worktree_sync(
      *, repo_root: Path, id: str, merge: bool = False, rebase: bool = False
  ) -> str:
      raise CommandError("worktree sync is not implemented yet")
  ```

### 1.6 Run parser test, expect PASS

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_sync.py::test_sync_requires_exactly_one_strategy -q
  ```
  Expected: PASS.

### 1.7 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/cli.py tools/tasktool/commands.py tools/tasktool/tests/test_worktree_sync.py
  git commit -m "P7.S5: add worktree sync parser"
  ```

## Task 2 — Dirty-state helper with staged-tasklist allowance

### 2.1 Add failing helper tests

- [ ] Append to `tools/tasktool/tests/test_worktree_sync.py`:
  ```python
  def test_dirty_helper_allows_staged_tasklist_only(tmp_path):
      from tasktool.worktree import working_tree_dirty_for_sync
      repo = init_repo(tmp_path / "repo")
      data = json.loads((repo / "docs" / "tasklist.json").read_text())
      data["north_star"] = "staged tracker update"
      (repo / "docs" / "tasklist.json").write_text(json.dumps(data, indent=2) + "\n")
      git(repo, "add", "docs/tasklist.json")
      dirty, items = working_tree_dirty_for_sync(repo, allow_staged_tasklist=True)
      assert dirty is False, items


  def test_dirty_helper_refuses_unstaged_tasklist_and_untracked_files(tmp_path):
      from tasktool.worktree import working_tree_dirty_for_sync
      repo = init_repo(tmp_path / "repo")
      data = json.loads((repo / "docs" / "tasklist.json").read_text())
      data["north_star"] = "unstaged tracker update"
      (repo / "docs" / "tasklist.json").write_text(json.dumps(data, indent=2) + "\n")
      dirty, items = working_tree_dirty_for_sync(repo, allow_staged_tasklist=True)
      assert dirty is True
      assert "docs/tasklist.json" in items
      git(repo, "add", "docs/tasklist.json")
      (repo / "scratch.txt").write_text("scratch\n")
      dirty, items = working_tree_dirty_for_sync(repo, allow_staged_tasklist=True)
      assert dirty is True
      assert "scratch.txt" in items
  ```

### 2.2 Run helper tests, expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_sync.py::test_dirty_helper_allows_staged_tasklist_only tools/tasktool/tests/test_worktree_sync.py::test_dirty_helper_refuses_unstaged_tasklist_and_untracked_files -q
  ```
  Expected: FAIL with `ImportError: cannot import name 'working_tree_dirty_for_sync'`.

### 2.3 Implement helper

- [ ] Add to `tools/tasktool/worktree.py` after `working_tree_dirty`:
  ```python
  def working_tree_dirty_for_sync(
      root: Path, *, allow_staged_tasklist: bool = False
  ) -> tuple[bool, list[str]]:
      """Dirty check for worktree sync.

      When syncing an in-place slice in the authoritative checkout, staged-only
      docs/tasklist.json is safe tasktool state. Unstaged tasklist bytes and all
      other dirt still refuse.
      """
      items: list[str] = []
      status = _git(root, "status", "--porcelain", check=False).stdout.splitlines()
      for line in status:
          if not line.strip():
              continue
          code = line[:2]
          path = line[3:]
          staged_only_tasklist = (
              allow_staged_tasklist
              and path == "docs/tasklist.json"
              and code[0] != " "
              and code[1] == " "
          )
          if staged_only_tasklist:
              continue
          items.append(path)

      branch = git_current_branch(root)
      if branch:
          stash = _git(root, "stash", "list", check=False).stdout.splitlines()
          marker_wip = f"WIP on {branch}:"
          marker_on = f"On {branch}:"
          for line in stash:
              if marker_wip in line or marker_on in line:
                  items.append(f"stash: {line}")
      # The staged-tasklist allowance intentionally recognizes only plain
      # add/modify status lines. Renames, deletes, and quoted paths stay dirty.
      return (bool(items), items)
  ```

### 2.4 Run helper tests, expect PASS

- [ ] Run the same command as 2.2. Expected: `2 passed`.

### 2.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/worktree.py tools/tasktool/tests/test_worktree_sync.py
  git commit -m "P7.S5: allow staged tasklist during in-place sync"
  ```

## Task 3 — Implement strict sync preflight

### 3.1 Add failing refusal tests

- [ ] Append to `tools/tasktool/tests/test_worktree_sync.py`:
  ```python
  def test_sync_refuses_missing_worktree_base_sha(tmp_path):
      repo = init_repo(tmp_path / "repo")
      start_linked(repo)
      path = repo / "docs" / "tasklist.json"
      data = json.loads(path.read_text())
      data["phases"][0]["slices"][0].pop("worktree_base_sha", None)
      path.write_text(json.dumps(data, indent=2) + "\n")
      git(repo, "add", "docs/tasklist.json")
      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
      assert r.returncode != 0
      assert "worktree_base_sha" in (r.stdout + r.stderr)


  def test_sync_refuses_non_slice_id(tmp_path):
      repo = init_repo(tmp_path / "repo")
      r = run(repo, "worktree", "sync", "P1", "--merge")
      assert r.returncode != 0
      assert "worktree sync only supports slices" in (r.stdout + r.stderr)


  def test_sync_refuses_unhealthy_recorded_worktree(tmp_path):
      repo = init_repo(tmp_path / "repo")
      wt = start_linked(repo)
      git(repo, "worktree", "remove", "--force", str(wt))
      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
      assert r.returncode != 0
      assert "recorded worktree is not live" in (r.stdout + r.stderr)


  def test_sync_refuses_dirty_linked_worktree(tmp_path):
      repo = init_repo(tmp_path / "repo")
      wt = start_linked(repo)
      advance_main(repo, "base-change")
      (wt / "dirty.txt").write_text("dirty\n")
      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
      assert r.returncode != 0
      assert "not clean" in (r.stdout + r.stderr)
      assert "dirty.txt" in (r.stdout + r.stderr)


  def test_sync_refuses_unstaged_authoritative_tasklist(tmp_path):
      repo = init_repo(tmp_path / "repo")
      start_linked(repo)
      advance_main(repo, "base-change")
      data = json.loads((repo / "docs" / "tasklist.json").read_text())
      data["north_star"] = "unstaged"
      (repo / "docs" / "tasklist.json").write_text(json.dumps(data, indent=2) + "\n")
      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
      assert r.returncode != 0
      assert "docs/tasklist.json has unstaged changes" in (r.stdout + r.stderr)
  ```

### 3.2 Run refusal tests, expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_sync.py::test_sync_refuses_missing_worktree_base_sha tools/tasktool/tests/test_worktree_sync.py::test_sync_refuses_non_slice_id tools/tasktool/tests/test_worktree_sync.py::test_sync_refuses_unhealthy_recorded_worktree tools/tasktool/tests/test_worktree_sync.py::test_sync_refuses_dirty_linked_worktree tools/tasktool/tests/test_worktree_sync.py::test_sync_refuses_unstaged_authoritative_tasklist -q
  ```
  Expected: FAIL because the stub always says not implemented.

### 3.3 Implement target resolution and preflight

- [ ] Replace the stub in `tools/tasktool/commands.py` with this implementation shell:
  ```python
  def _sync_target_path(write_root: Path, qid: str, item) -> Path:
      if getattr(item, "worktree_in_place", False):
          return write_root
      path_str = getattr(item, "worktree_path", None)
      if not path_str:
          raise CommandError(f"{qid}: no recorded worktree to sync")
      if _health_for(write_root, item) != "live":
          raise CommandError(f"{qid}: recorded worktree is not live; run `tasktool worktree status {qid}`")
      return (write_root / path_str).resolve()


  def _preflight_worktree_sync(
      *, write_root: Path, qid: str, item, target: Path, base_branch: str
  ) -> str:
      from tasktool import worktree as wt
      base_sha = getattr(item, "worktree_base_sha", None)
      if not base_sha:
          raise CommandError(f"{qid}: worktree_base_sha is not recorded; cannot sync safely")
      try:
          base_head = wt.current_branch_head_sha(write_root, base_branch)
      except _subprocess.CalledProcessError as exc:
          raise CommandError(f"{qid}: cannot resolve base branch {base_branch!r}") from exc
      if wt.has_unmerged_paths(target):
          raise CommandError(f"{qid}: target worktree has unresolved merge entries")
      allow_staged_tasklist = target.resolve() == write_root.resolve()
      dirty, items = wt.working_tree_dirty_for_sync(
          target, allow_staged_tasklist=allow_staged_tasklist
      )
      if dirty:
          pretty = ", ".join(items[:5]) + (" ..." if len(items) > 5 else "")
          raise CommandError(f"{qid}: target worktree is not clean: {pretty}")
      if wt.tasklist_has_unsafe_dirty_state(write_root):
          raise CommandError("authoritative docs/tasklist.json has unstaged changes")
      return base_head


  def cmd_worktree_sync(
      *, repo_root: Path, id: str, merge: bool = False, rebase: bool = False
  ) -> str:
      if merge == rebase:
          raise CommandError("choose exactly one of --merge or --rebase")
      with _read_context(repo_root) as write_root:
          p = _load(write_root)
          qid, _container, item = _find_item(p, id)
          if parse_id(qid)[0] != "slice":
              raise CommandError(f"{qid}: worktree sync only supports slices")
          base_branch = _authoritative_parent_branch(write_root, qid)
          target = _sync_target_path(write_root, qid, item)
          previous_base = getattr(item, "worktree_base_sha", None)
          base_head = _preflight_worktree_sync(
              write_root=write_root,
              qid=qid,
              item=item,
              target=target,
              base_branch=base_branch,
          )
      # Git mutation is added in Task 4.
      return (
          f"{qid}: sync preflight passed ({'merge' if merge else 'rebase'} {base_head})\n"
          f"previous worktree_base_sha: {previous_base}\n"
      )
  ```

### 3.4 Run refusal tests, expect PASS

- [ ] Run the same command as 3.2. Expected: `5 passed`.

### 3.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_worktree_sync.py
  git commit -m "P7.S5: add sync preflight refusals"
  ```

## Task 4 — Merge/rebase success and base-SHA update

### 4.1 Add failing success tests

- [ ] Append to `tools/tasktool/tests/test_worktree_sync.py`:
  ```python
  def test_sync_merge_integrates_captured_base_sha_and_advances_row(tmp_path):
      repo = init_repo(tmp_path / "repo")
      wt = start_linked(repo)
      base_head = advance_main(repo, "base-change", "base")
      (wt / "slice-work").write_text("slice\n")
      git(wt, "add", "slice-work")
      git(wt, "commit", "-q", "-m", "slice work")
      old_base = slice_row(repo)["worktree_base_sha"]
      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
      assert r.returncode == 0, r.stdout + r.stderr
      assert f"integrated main at {base_head}" in r.stdout
      assert slice_row(repo)["worktree_base_sha"] == base_head
      assert slice_row(repo)["worktree_base_sha"] != old_base
      assert (wt / "base-change").read_text() == "base\n"


  def test_sync_rebase_integrates_captured_base_sha_and_advances_row(tmp_path):
      repo = init_repo(tmp_path / "repo")
      wt = start_linked(repo)
      base_head = advance_main(repo, "base-change", "base")
      (wt / "slice-work").write_text("slice\n")
      git(wt, "add", "slice-work")
      git(wt, "commit", "-q", "-m", "slice work")
      r = run(repo, "worktree", "sync", "P1.S1", "--rebase")
      assert r.returncode == 0, r.stdout + r.stderr
      assert f"integrated main at {base_head}" in r.stdout
      assert slice_row(repo)["worktree_base_sha"] == base_head
      assert (wt / "base-change").read_text() == "base\n"


  def test_sync_merge_non_fast_forward_is_non_interactive(tmp_path):
      repo = init_repo(tmp_path / "repo")
      wt = start_linked(repo)
      advance_main(repo, "main-only", "base")
      (wt / "slice-only").write_text("slice\n")
      git(wt, "add", "slice-only")
      git(wt, "commit", "-q", "-m", "slice work")
      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
      assert r.returncode == 0, r.stdout + r.stderr
      assert "follow-up:" in r.stdout
      log = git(wt, "log", "-1", "--format=%s").strip()
      assert log.startswith("Merge")
  ```

### 4.2 Run success tests, expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_sync.py::test_sync_merge_integrates_captured_base_sha_and_advances_row tools/tasktool/tests/test_worktree_sync.py::test_sync_rebase_integrates_captured_base_sha_and_advances_row tools/tasktool/tests/test_worktree_sync.py::test_sync_merge_non_fast_forward_is_non_interactive -q
  ```
  Expected: FAIL because Task 3 only prints preflight and does not run git/update the row.

### 4.3 Implement git operation and locked row update

- [ ] Add in `tools/tasktool/commands.py` near `_preflight_worktree_sync`:
  ```python
  def _run_sync_git(*, target: Path, strategy: str, base_head: str) -> None:
      env = _os.environ.copy()
      env.setdefault("GIT_EDITOR", "true")
      if strategy == "merge":
          args = ["git", "merge", "--no-edit", base_head]
      else:
          args = ["git", "rebase", base_head]
      try:
          _subprocess.run(args, cwd=target, text=True, capture_output=True, check=True, env=env)
      except _subprocess.CalledProcessError as exc:
          detail = (exc.stderr or exc.stdout or "").strip()
          raise CommandError(f"git {strategy} failed; resolve or abort git state, then rerun sync: {detail}") from exc
  ```

- [ ] Replace the final body of `cmd_worktree_sync` after preflight with:
  ```python
      strategy = "merge" if merge else "rebase"
      _run_sync_git(target=target, strategy=strategy, base_head=base_head)

      with _write_context(repo_root) as write_root:
          p = _load(write_root)
          qid, _container, item = _find_item(p, id)
          item.worktree_base_sha = base_head
          _save(write_root, p)

      return (
          f"{qid}: synchronized by {strategy}; integrated {base_branch} at {base_head}\n"
          f"previous worktree_base_sha: {previous_base}\n"
          f"new worktree_base_sha: {base_head}\n"
          "follow-up:\n"
          f"  tasktool worktree status {qid} --integration\n"
          "  rerun focused verification for files changed by the base integration\n"
          "  regenerate derived artifacts if this project has snapshots, checksums, schemas, or lock files\n"
      )
  ```

### 4.4 Run success tests, expect PASS

- [ ] Run the same command as 4.2. Expected: `3 passed`.

### 4.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_worktree_sync.py
  git commit -m "P7.S5: sync worktree and advance base sha"
  ```

## Task 5 — Failure semantics and in-place coverage

### 5.1 Add failing failure/in-place tests

- [ ] Append to `tools/tasktool/tests/test_worktree_sync.py`:
  ```python
  def test_sync_conflict_leaves_worktree_base_sha_unchanged(tmp_path):
      repo = init_repo(tmp_path / "repo")
      wt = start_linked(repo)
      old_base = slice_row(repo)["worktree_base_sha"]
      (wt / "conflict.txt").write_text("slice\n")
      git(wt, "add", "conflict.txt")
      git(wt, "commit", "-q", "-m", "slice conflict")
      (repo / "conflict.txt").write_text("base\n")
      git(repo, "add", "conflict.txt")
      git(repo, "commit", "-q", "-m", "base conflict")
      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
      assert r.returncode != 0
      assert "git merge failed" in (r.stdout + r.stderr)
      assert slice_row(repo)["worktree_base_sha"] == old_base


  def test_sync_rebase_conflict_leaves_worktree_base_sha_unchanged(tmp_path):
      repo = init_repo(tmp_path / "repo")
      wt = start_linked(repo)
      old_base = slice_row(repo)["worktree_base_sha"]
      (wt / "conflict.txt").write_text("slice\n")
      git(wt, "add", "conflict.txt")
      git(wt, "commit", "-q", "-m", "slice conflict")
      (repo / "conflict.txt").write_text("base\n")
      git(repo, "add", "conflict.txt")
      git(repo, "commit", "-q", "-m", "base conflict")
      r = run(repo, "worktree", "sync", "P1.S1", "--rebase")
      assert r.returncode != 0
      assert "git rebase failed" in (r.stdout + r.stderr)
      assert slice_row(repo)["worktree_base_sha"] == old_base


  def test_sync_in_place_allows_staged_tasklist_and_advances_base_sha(tmp_path):
      repo = init_repo(tmp_path / "repo")
      assert run(repo, "start", "P1.S1", "--in-place").returncode == 0
      base_head = advance_main(repo, "base-change", "base")
      # Simulate routine tasktool staged tracker state in the authoritative checkout.
      data = json.loads((repo / "docs" / "tasklist.json").read_text())
      data["north_star"] = "staged tracker update"
      (repo / "docs" / "tasklist.json").write_text(json.dumps(data, indent=2) + "\n")
      git(repo, "add", "docs/tasklist.json")
      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
      assert r.returncode == 0, r.stdout + r.stderr
      assert slice_row(repo)["worktree_base_sha"] == base_head
      # This is an up-to-date merge of HEAD into itself while staged tracker
      # bytes exist; git exits zero before requiring a clean index.
      assert "synchronized by merge" in r.stdout
  ```

### 5.2 Run tests, expect FAIL if edge cases are missing

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_sync.py::test_sync_conflict_leaves_worktree_base_sha_unchanged tools/tasktool/tests/test_worktree_sync.py::test_sync_rebase_conflict_leaves_worktree_base_sha_unchanged tools/tasktool/tests/test_worktree_sync.py::test_sync_in_place_allows_staged_tasklist_and_advances_base_sha -q
  ```
  Expected: PASS if Tasks 2-4 were implemented exactly; otherwise fix the command until all three pass.

### 5.3 Verify post-sync integration status

- [ ] Append:
  ```python
  def test_sync_clears_already_integrated_status_window(tmp_path):
      repo = init_repo(tmp_path / "repo")
      start_linked(repo)
      advance_main(repo, "base-change", "base")
      before = run(repo, "worktree", "status", "P1.S1", "--integration")
      assert "base ahead of worktree_base_sha: 1 commit" in before.stdout
      r = run(repo, "worktree", "sync", "P1.S1", "--merge")
      assert r.returncode == 0, r.stdout + r.stderr
      after = run(repo, "worktree", "status", "P1.S1", "--integration")
      assert "base ahead of worktree_base_sha: 0 commits" in after.stdout
  ```

### 5.4 Run status-window test

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_sync.py::test_sync_clears_already_integrated_status_window -q
  ```
  Expected: PASS.

### 5.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/worktree.py tools/tasktool/tests/test_worktree_sync.py
  git commit -m "P7.S5: preserve sync failure invariants"
  ```

## Task 6 — Full verification and slice closeout

### 6.1 Run focused tests

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_sync.py -q
  python -m pytest tools/tasktool/tests/test_worktree_integration.py tools/tasktool/tests/test_worktree_prune.py tools/tasktool/tests/test_worktree_subcommands.py -q
  ```
  Expected: all selected tests pass.

### 6.2 Run broader tasktool verification

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests -q
  tasktool validate
  ```
  Expected: all tests pass and `tasktool validate` reports no errors.

### 6.3 Dogfood the integration checkpoint

- [ ] Run:
  ```sh
  tasktool worktree status P7.S5 --integration
  ```
  Expected: the command succeeds. If it reports base ahead or landed siblings since `worktree_base_sha`, run:
  ```sh
  tasktool worktree sync P7.S5 --merge
  tasktool worktree status P7.S5 --integration
  python -m pytest tools/tasktool/tests/test_worktree_sync.py -q
  ```

### 6.4 Post-slice review and close

- [ ] Run external post-slice review from the P7.S5 implementation worktree:
  ```sh
  external-reviewer review \
    --kind post-slice \
    --file docs/plans/2026-06-04-P7-S5-conservative-worktree-sync.md \
    --work-id P7.S5 \
    --context docs/specs/2026-06-04-P7-S5-conservative-worktree-sync-design.md \
    --emit json
  ```
  Expected: verdict `ready` or `ready with small edits`. If verdict is `revise`, delegate fixes, write the required resolution artifact under the P7.S5 post-slice chain, and rerun review.

- [ ] Register the post-slice reviewer chain and close:
  ```sh
  tasktool artifact add P7.S5 --kind reviewer --path docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice/
  tasktool artifact status P7.S5 --strict
  tasktool close P7.S5
  ```

### 6.5 Final commit/push boundary

- [ ] Commit slice closeout artifacts with the files changed by this slice only.
  If unrelated staged files exist, stop and report the exact blocker rather than
  unstaging or committing them.
