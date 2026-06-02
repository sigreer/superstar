# P7.S4 — Worktree Integration Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record the base-branch SHA a slice's worktree branched from at `tasktool start`, stamp the landed base SHA at the normal guarded `worktree prune` only when the merge is proven, and add a `worktree status --integration` mode that reports staleness and surface-sharing siblings that have landed since the worktree branched.

**Architecture:** Three behaviors land in `tools/tasktool/`. (1) `cmd_start`'s helpers (`_apply_start_default`, `_apply_start_in_place`, `_apply_start_adopt`) capture `worktree_base_sha` from the base-branch HEAD (or merge-base for `--adopt`) right where the worktree is created/recorded. (2) `cmd_worktree_prune` stamps `landed_base_sha` = base-branch HEAD only when all stamping preconditions hold (done status, branch-merged guard passed, not `--force`, not `--finalize`-only without proven merge). (3) A new `--integration` flag on `worktree status` reports commits base is ahead of `worktree_base_sha`, which sibling slices in the same phase landed since then (authoritative `landed_base_sha` → branch-ancestry fallback → `unknown`), and whether any landed sibling shares an `integration_surface` with this slice. All git work uses plumbing via the existing `worktree.py._git` helper / `subprocess`.

**Tech Stack:** Python 3, git plumbing, pytest

---

## Scheduling

- **depends_on:** P7.S1 (model fields `worktree_base_sha`, `landed_base_sha`, `integration_surfaces`, schema v3 migration + serialize omit-when-default). This slice assumes those fields already exist on `Slice` and round-trip cleanly. If S1 is not yet merged into the base branch this slice's worktree branched from, integrate it first (`tasktool worktree status P7.S4 --integration`, then a base integration) before writing code that reads the new fields.
- **blocks:** P7.S5 (`worktree sync` advances `worktree_base_sha` — needs the field captured here) and P7.S6 (skill changes document the `--integration` checkpoint added here).
- **parallel-eligible with:** P7.S2 (declaration CLI). Disjoint surfaces: S2 writes `cli`/`commands` declaration handlers (`surface`/`reserve`/`coordinate`); S4 writes `worktree`-facing code (`cmd_start` helpers, `cmd_worktree_prune`, `cmd_worktree_status`) plus a narrow `cli.py` flag add. The only shared file is `commands.py`, but the edited regions are disjoint (S2 adds new `cmd_surface_*`/`cmd_reserve_*` functions; S4 edits the worktree command block). Coordinate the `cli.py` subparser additions if both land near the same lines.

## File Structure

| File | Responsibility (this slice) |
|------|------------------------------|
| `tools/tasktool/worktree.py` | Add pure git plumbing helpers: `current_branch_head_sha(root, branch)` (resolve a branch's HEAD SHA), `merge_base_sha(root, a, b)` (merge-base of two committishes), `rev_list_count(root, base, head)` and `rev_list_shas(root, base, head)` (commits in the half-open `base..head`), `commit_is_in_range(root, sha, *, base, head)` (is `sha` reachable from `head` but not `base`). All use the existing `_git` wrapper. No tasklist mutation. |
| `tools/tasktool/commands.py` | (a) `_apply_start_default` / `_apply_start_in_place` / `_apply_start_adopt`: capture `worktree_base_sha`. (b) `cmd_worktree_prune` / `_worktree_finalize`: stamp `landed_base_sha` under preconditions. (c) New `cmd_worktree_status_integration(repo_root, id)` and an `--integration` branch in `cmd_worktree_status`. (d) `cmd_show`: render the two new SHAs when present. |
| `tools/tasktool/cli.py` | Add `--integration` flag to the `worktree status` subparser; route to the new code path in the `worktree`/`status` dispatch block. |
| `tools/tasktool/config.py` | (read-only) `authoritative_branch` is already exposed via `load_config(root).tasklist.authoritative_branch`; reused, not modified. |
| `tools/tasktool/tests/test_start_worktree.py` | Tests for base-sha capture on `start` (default / `--in-place` / `--adopt`). |
| `tools/tasktool/tests/test_worktree_prune.py` | Tests for landed-sha stamping + the non-stamping cases (cancelled, `--force` unmerged, `--finalize`-only). |
| `tools/tasktool/tests/test_worktree_integration.py` | **New file.** Tests for `worktree status --integration` across the three landed signals and surface-overlap reporting. |

### Reference facts the implementer must rely on (verified against current code)

- **Base branch name** comes from `load_config(write_root).tasklist.authoritative_branch` (default `"main"`). Helper `_authoritative_parent_branch(write_root, qid)` in `commands.py` already returns it; reuse it.
- **`_apply_start_default`** (commands.py ~L935) runs `git worktree add -b <branch> <path>` from `write_root`. At that moment the new branch points at the current base-branch HEAD's commit (git creates the branch from HEAD of the repo's current branch, which in the authoritative checkout is `authoritative_branch`). Capture `worktree_base_sha = current_branch_head_sha(write_root, authoritative_branch)` **before** the `git worktree add` call (the value is identical before/after, but capturing first avoids any ambiguity). Also handle the `CONSISTENT` (idempotent re-`start`) early-return and the `return` when no `.git` exists — in those paths leave `worktree_base_sha` unchanged (do not overwrite a value already recorded; do not set one when there is no git repo).
- **`_apply_start_in_place`** (commands.py ~L1004): no worktree on disk; record `worktree_base_sha = current_branch_head_sha(write_root, authoritative_branch)` (the base HEAD the in-place work starts from). It does not call `git worktree add`. Pass `write_root` into this helper (currently it only takes `(qid, item)`) so it can read config + HEAD.
- **`_apply_start_adopt`** (commands.py ~L1014): the adopted branch is `linked_worktree_branch(write_root, adopt_path)`. Record `worktree_base_sha = merge_base_sha(write_root, branch, authoritative_branch)` — the point the adopted branch forked from base.
- **`cmd_worktree_prune`** (commands.py ~L2327): guards are (1) terminal status unless `--force`; (2) `wt.branch_is_merged(write_root, branch=branch, into=parent)` unless `--force`; (3) clean tree unless `--force`. The destructive step runs after the prune-from-inside check. Stamp `landed_base_sha` in the non-`--finalize`, non-pending, normal destructive path, gated on the preconditions below.
- **`_worktree_finalize`** (commands.py ~L2428) is the `--finalize`-only path. It must **not** stamp `landed_base_sha` unless the merged state was already proven and stamped in the originating prune (it was not — the pending path defers before stamping). So `_worktree_finalize` leaves `landed_base_sha` as-is.
- **`cmd_worktree_status`** (commands.py ~L2220) uses `_read_context` (no lock, read-only). The new `--integration` path also uses `_read_context`.
- **Serialize omit-when-default** (`serialize.py` `_WORKTREE_DEFAULT_OMIT`) is S1's responsibility; this slice assumes `worktree_base_sha`/`landed_base_sha` default `None` and are omitted when `None`. The deserializer reads them via `_strict_opt_str`. Do not re-implement; if a round-trip test here fails because S1's omit list is missing these keys, that is an S1 defect — report it, do not patch serialize.py from this slice.

---

## Task 1 — Slice setup + git plumbing helpers in `worktree.py`

### 1.1 Start the slice (REQUIRED FIRST — before any source edit)

- [ ] Run, from the repo root (`/home/simon/Dev/sigreer/skills/superstar`):
  ```sh
  ./tools/tasktool/tasktool start P7.S4
  ```
  Expected: prints a `cd .worktrees/worktree-p7-s4-...` line and records `worktree_path`/`worktree_branch` on the P7.S4 row. **No `worktree_base_sha` is recorded yet** — the start code that captures it is the feature this slice builds (Task 2/3), and a slice cannot record a field whose code does not exist when it starts (chicken-and-egg). `cd` into the printed worktree path and do all subsequent work there. If P7.S4 is configured `--in-place` for this project, run `./tools/tasktool/tasktool start P7.S4 --in-place` instead and work in the current checkout.

  > **Own-row base-sha backfill (read Task 2 first, act after it lands).** Because this slice's own `start` predates the capture code, the P7.S4 row will carry no `worktree_base_sha`, so the dogfood checkpoint at Task 11.7 cannot compute staleness for *this* slice. After Task 2's `_apply_start_default` capture is implemented and committed, backfill the slice's own row once, from the authoritative checkout, so the checkpoint has a base SHA to compare against:
  > ```sh
  > # From the worktree, capture the base-branch HEAD this worktree actually branched from.
  > # `git merge-base HEAD <base-branch>` is the fork point even after base has advanced.
  > # There is no `tasktool config show` subcommand — read the base branch from
  > # .tasktool/config.json (tasklist.authoritative_branch), defaulting to "main".
  > BASE_BRANCH="$(python3 -c 'import json,pathlib; p=pathlib.Path(".tasktool/config.json"); print((json.loads(p.read_text()).get("tasklist",{}) if p.exists() else {}).get("authoritative_branch","main"))')"
  > BASE_SHA="$(git merge-base HEAD "$BASE_BRANCH")"
  > ./tools/tasktool/tasktool note P7.S4 --append "worktree_base_sha backfill: $BASE_SHA"
  > ```
  > tasktool has no `set --worktree-base-sha` command (and adding one is out of scope for S4), so record the fork point as an audit note and, if you want the live checkpoint at 11.7 to exercise the real field, set the P7.S4 row's `worktree_base_sha` to `$BASE_SHA` via the **sanctioned raw-edit path** from `tasklist-discipline`: make the one-time bootstrap edit to `docs/tasklist.json` under `TASKTOOL_RAW=1`, then run `tasktool validate --normalise` to canonicalise and re-stage it (do **not** hand-write the JSON without the normalise step). If you prefer not to touch the tracker, **accept that the P7.S4 row has no `worktree_base_sha`** and treat Task 11.7 as "ran the command, confirmed it degrades gracefully via the `<not recorded>` path" rather than a full staleness check — see the adjusted 11.7 below.

### 1.2 Failing test: `current_branch_head_sha` resolves a branch HEAD

- [ ] Append to `tools/tasktool/tests/test_worktree_prune.py` (it already has the `_init_repo`/`_add_worktree`/`_run` helpers used here):
  ```python
  def test_current_branch_head_sha_matches_rev_parse(tmp_path):
      from tasktool.worktree import current_branch_head_sha
      root = _init_repo(tmp_path / "r")
      expected = _run(root, "git", "rev-parse", "main").strip()
      assert current_branch_head_sha(root, "main") == expected
      assert len(current_branch_head_sha(root, "main")) == 40
  ```

### 1.3 Run it — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_prune.py::test_current_branch_head_sha_matches_rev_parse -q
  ```
  Expected: FAIL with `ImportError: cannot import name 'current_branch_head_sha'`.

### 1.4 Minimal impl: add `current_branch_head_sha`

- [ ] In `tools/tasktool/worktree.py`, after `git_current_branch` (~L31), add:
  ```python
  def current_branch_head_sha(root: Path, branch: str) -> str:
      """Return the full 40-char commit SHA at the tip of `branch`."""
      return _git(root, "rev-parse", "--verify", f"refs/heads/{branch}").stdout.strip()
  ```

### 1.5 Run it — expect PASS

- [ ] Run the same command as 1.3. Expected: `1 passed`.

### 1.6 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/worktree.py tools/tasktool/tests/test_worktree_prune.py
  git commit -m "P7.S4: add current_branch_head_sha git helper"
  ```

### 1.7 Failing test: `merge_base_sha`

- [ ] Append to `tools/tasktool/tests/test_worktree_prune.py`:
  ```python
  def test_merge_base_sha_returns_fork_point(tmp_path):
      from tasktool.worktree import merge_base_sha
      root = _init_repo(tmp_path / "r")
      fork = _run(root, "git", "rev-parse", "main").strip()
      _run(root, "git", "checkout", "-q", "-b", "feat")
      (root / "a").write_text("a")
      _run(root, "git", "add", "a")
      _run(root, "git", "commit", "-q", "-m", "feat work")
      _run(root, "git", "checkout", "-q", "main")
      (root / "b").write_text("b")
      _run(root, "git", "add", "b")
      _run(root, "git", "commit", "-q", "-m", "main work")
      assert merge_base_sha(root, "feat", "main") == fork
  ```

### 1.8 Run it — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_prune.py::test_merge_base_sha_returns_fork_point -q
  ```
  Expected: FAIL with `ImportError: cannot import name 'merge_base_sha'`.

### 1.9 Minimal impl: add `merge_base_sha`

- [ ] In `tools/tasktool/worktree.py`, after `current_branch_head_sha`, add:
  ```python
  def merge_base_sha(root: Path, a: str, b: str) -> str | None:
      """Return the merge-base SHA of `a` and `b`, or None if they share no history."""
      res = _git(root, "merge-base", a, b, check=False)
      out = res.stdout.strip()
      return out or None
  ```

### 1.10 Run it — expect PASS

- [ ] Run the same command as 1.8. Expected: `1 passed`.

### 1.11 Failing test: `rev_list_count`, `rev_list_shas`, `commit_is_in_range`

- [ ] Append to `tools/tasktool/tests/test_worktree_prune.py`:
  ```python
  def test_rev_list_helpers_count_window_and_membership(tmp_path):
      from tasktool.worktree import rev_list_count, rev_list_shas, commit_is_in_range
      root = _init_repo(tmp_path / "r")
      base = _run(root, "git", "rev-parse", "main").strip()
      (root / "c1").write_text("1")
      _run(root, "git", "add", "c1")
      _run(root, "git", "commit", "-q", "-m", "c1")
      mid = _run(root, "git", "rev-parse", "main").strip()
      (root / "c2").write_text("2")
      _run(root, "git", "add", "c2")
      _run(root, "git", "commit", "-q", "-m", "c2")
      head = _run(root, "git", "rev-parse", "main").strip()
      # base..head spans exactly the two new commits.
      assert rev_list_count(root, base, head) == 2
      shas = rev_list_shas(root, base, head)
      assert head in shas and mid in shas and base not in shas
      # `mid` is reachable from head but not from base -> in range.
      assert commit_is_in_range(root, mid, base=base, head=head) is True
      # `base` itself is excluded by the half-open A..B window.
      assert commit_is_in_range(root, base, base=base, head=head) is False
  ```

### 1.12 Run it — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_prune.py::test_rev_list_helpers_count_window_and_membership -q
  ```
  Expected: FAIL with `ImportError: cannot import name 'rev_list_count'`.

### 1.13 Minimal impl: add the rev-list helpers

- [ ] In `tools/tasktool/worktree.py`, after `merge_base_sha`, add:
  ```python
  def rev_list_shas(root: Path, base: str, head: str) -> list[str]:
      """Commits reachable from `head` but not `base` (the half-open `base..head`)."""
      res = _git(root, "rev-list", f"{base}..{head}", check=False)
      return [line.strip() for line in res.stdout.splitlines() if line.strip()]


  def rev_list_count(root: Path, base: str, head: str) -> int:
      return len(rev_list_shas(root, base, head))


  def commit_is_in_range(root: Path, sha: str, *, base: str, head: str) -> bool:
      """True iff `sha` is reachable from `head` but not from `base`."""
      reachable_from_head = _git(
          root, "merge-base", "--is-ancestor", sha, head, check=False
      ).returncode == 0
      reachable_from_base = _git(
          root, "merge-base", "--is-ancestor", sha, base, check=False
      ).returncode == 0
      return reachable_from_head and not reachable_from_base
  ```
  Note: `commit_is_in_range` uses ancestry rather than membership in `rev_list_shas` so it survives squash/rebase reordering and works even when `sha` is the exact `head` commit (an ancestor of itself).

### 1.14 Run it — expect PASS

- [ ] Run the same command as 1.12. Expected: `1 passed`.

### 1.15 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/worktree.py tools/tasktool/tests/test_worktree_prune.py
  git commit -m "P7.S4: add merge-base and rev-list git helpers for integration detection"
  ```

---

## Task 2 — Capture `worktree_base_sha` at `tasktool start` (default path)

### 2.1 Failing test: default `start` records `worktree_base_sha` = base HEAD

- [ ] Append to `tools/tasktool/tests/test_start_worktree.py` (reuses `seed_repo`, `run`, `_git`, `tasklist`):
  ```python
  def test_start_records_worktree_base_sha_for_default(tmp_path):
      root = seed_repo(tmp_path)
      base_head = _git(root, "rev-parse", "main").stdout.strip()
      r = run(root, "start", "P1.S1")
      assert r.returncode == 0, r.stdout + r.stderr
      sl = tasklist(root)["phases"][0]["slices"][0]
      assert sl["worktree_base_sha"] == base_head
  ```

### 2.2 Run it — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_start_worktree.py::test_start_records_worktree_base_sha_for_default -q
  ```
  Expected: FAIL with `KeyError: 'worktree_base_sha'` (the field is omitted because still `None`).

### 2.3 Minimal impl: capture base SHA in `_apply_start_default`

- [ ] In `tools/tasktool/commands.py`, inside `_apply_start_default` (~L935), in the `ABSENT` branch immediately before the `git worktree add` subprocess call (after the out-of-band path/branch refusals, before `canonical_path.parent.mkdir(...)`), add:
  ```python
  from tasktool.config import load_config
  from tasktool.worktree import current_branch_head_sha
  base_branch = load_config(write_root).tasklist.authoritative_branch
  try:
      item.worktree_base_sha = current_branch_head_sha(write_root, base_branch)
  except _subprocess.CalledProcessError:
      item.worktree_base_sha = None
  ```
  Leave the early `CONSISTENT`/`no-.git` returns untouched so a re-`start` does not overwrite or fabricate the field.

### 2.4 Run it — expect PASS

- [ ] Run the same command as 2.2. Expected: `1 passed`.

### 2.5 Regression check: existing start tests still pass

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_start_worktree.py -q
  ```
  Expected: all pass (the existing `test_start_records_worktree_path_and_branch...` and idempotency tests are unaffected).

### 2.6 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_start_worktree.py
  git commit -m "P7.S4: record worktree_base_sha on default start"
  ```

---

## Task 3 — Capture `worktree_base_sha` for `--in-place` and `--adopt`

### 3.1 Failing test: `--in-place` records base HEAD

- [ ] Append to `tools/tasktool/tests/test_start_worktree.py`:
  ```python
  def test_start_in_place_records_worktree_base_sha(tmp_path):
      root = seed_repo(tmp_path)
      base_head = _git(root, "rev-parse", "main").stdout.strip()
      r = run(root, "start", "P1.S1", "--in-place")
      assert r.returncode == 0, r.stdout + r.stderr
      sl = tasklist(root)["phases"][0]["slices"][0]
      assert sl["worktree_in_place"] is True
      assert sl["worktree_base_sha"] == base_head
  ```

### 3.2 Run it — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_start_worktree.py::test_start_in_place_records_worktree_base_sha -q
  ```
  Expected: FAIL with `KeyError: 'worktree_base_sha'`.

### 3.3 Minimal impl: thread `write_root` into `_apply_start_in_place` and capture

- [ ] In `tools/tasktool/commands.py`, change the call site in `cmd_start` (~L886) from:
  ```python
          if in_place:
              _apply_start_in_place(qid, item)
  ```
  to:
  ```python
          if in_place:
              _apply_start_in_place(write_root, qid, item)
  ```
- [ ] Change `_apply_start_in_place` (~L1004) signature and body to:
  ```python
  def _apply_start_in_place(write_root: Path, qid: str, item) -> None:
      if item.worktree_path is not None:
          raise CommandError(
              f"{qid}: --in-place refused; slice already has a recorded worktree at {item.worktree_path!r}."
          )
      item.worktree_in_place = True
      item.worktree_path = None
      item.worktree_branch = None
      if (write_root / ".git").exists():
          from tasktool.config import load_config
          from tasktool.worktree import current_branch_head_sha
          base_branch = load_config(write_root).tasklist.authoritative_branch
          try:
              item.worktree_base_sha = current_branch_head_sha(write_root, base_branch)
          except _subprocess.CalledProcessError:
              item.worktree_base_sha = None
  ```

### 3.4 Run it — expect PASS

- [ ] Run the same command as 3.2. Expected: `1 passed`.

### 3.5 Failing test: `--adopt` records merge-base of adopted branch with base

- [ ] Append to `tools/tasktool/tests/test_start_worktree.py`:
  ```python
  def test_start_adopt_records_merge_base_as_worktree_base_sha(tmp_path):
      root = seed_repo(tmp_path)
      # Fork point is current main HEAD.
      fork = _git(root, "rev-parse", "main").stdout.strip()
      external = tmp_path / "external"
      _git(root, "worktree", "add", "-b", "manual-branch", str(external))
      # Advance the adopted branch and main independently so HEAD != fork on both.
      (external / "f").write_text("x")
      _git(external, "add", "f")
      _git(external, "commit", "-m", "branch work")
      (root / "g").write_text("y")
      _git(root, "add", "g")
      _git(root, "commit", "-m", "main work")
      r = run(root, "start", "P1.S1", "--adopt", str(external))
      assert r.returncode == 0, r.stdout + r.stderr
      sl = tasklist(root)["phases"][0]["slices"][0]
      assert sl["worktree_base_sha"] == fork
  ```

### 3.6 Run it — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_start_worktree.py::test_start_adopt_records_merge_base_as_worktree_base_sha -q
  ```
  Expected: FAIL with `KeyError: 'worktree_base_sha'`.

### 3.7 Minimal impl: capture merge-base in `_apply_start_adopt`

- [ ] In `tools/tasktool/commands.py`, inside `_apply_start_adopt` (~L1014), after `item.worktree_branch = branch` / `item.worktree_in_place = False` are set (just before the final `print(f"cd {adopt_path}")`), add:
  ```python
      from tasktool.config import load_config
      from tasktool.worktree import merge_base_sha
      base_branch = load_config(write_root).tasklist.authoritative_branch
      try:
          item.worktree_base_sha = merge_base_sha(write_root, branch, base_branch)
      except _subprocess.CalledProcessError:
          item.worktree_base_sha = None
  ```

### 3.8 Run it — expect PASS

- [ ] Run the same command as 3.6. Expected: `1 passed`.

### 3.9 Regression check

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_start_worktree.py -q
  ```
  Expected: all pass (including `test_start_adopt_records_external_worktree`, `test_start_in_place_marks_slice`, auto-adopt tests).

### 3.10 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_start_worktree.py
  git commit -m "P7.S4: record worktree_base_sha for --in-place and --adopt starts"
  ```

---

## Task 4 — Render the new SHAs in `tasktool show`

### 4.1 Failing test: `show` displays `worktree_base_sha`

- [ ] Append to `tools/tasktool/tests/test_start_worktree.py`:
  ```python
  def test_show_renders_worktree_base_sha(tmp_path):
      root = seed_repo(tmp_path)
      assert run(root, "start", "P1.S1").returncode == 0
      out = run(root, "show", "P1.S1").stdout
      assert "worktree_base_sha:" in out
  ```

### 4.2 Run it — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_start_worktree.py::test_show_renders_worktree_base_sha -q
  ```
  Expected: FAIL (`assert "worktree_base_sha:" in out`).

### 4.3 Minimal impl: render in `cmd_show`

- [ ] In `tools/tasktool/commands.py`, inside `cmd_show` (~L1675, after the `worktree_pruned_at` block, before `worktree_prune_pending`), add:
  ```python
      if getattr(item, "worktree_base_sha", None):
          lines.append(f"worktree_base_sha: {item.worktree_base_sha}")
      if getattr(item, "landed_base_sha", None):
          lines.append(f"landed_base_sha: {item.landed_base_sha}")
  ```

### 4.4 Run it — expect PASS

- [ ] Run the same command as 4.2. Expected: `1 passed`.

### 4.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_start_worktree.py
  git commit -m "P7.S4: render worktree_base_sha and landed_base_sha in show"
  ```

---

## Task 5 — Stamp `landed_base_sha` on the normal guarded prune

### 5.1 Failing test: happy-path prune of a done, merged slice stamps `landed_base_sha`

- [ ] Append to `tools/tasktool/tests/test_worktree_prune.py`:
  ```python
  def test_prune_stamps_landed_base_sha_on_merged_done_slice(project_with_worktree):
      repo, wt = project_with_worktree
      _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
      _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
           "worktree-p1-s1-first-slice")
      base_head = _run(repo, "git", "rev-parse", "main").strip()
      res = _tasktool(repo, "worktree", "prune", "P1.S1")
      assert res.returncode == 0
      show = _tasktool(repo, "show", "P1.S1").stdout
      assert f"landed_base_sha: {base_head}" in show
  ```

### 5.2 Run it — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_prune.py::test_prune_stamps_landed_base_sha_on_merged_done_slice -q
  ```
  Expected: FAIL (`landed_base_sha:` absent from `show`).

### 5.3 Minimal impl: stamp under preconditions in `cmd_worktree_prune`

- [ ] In `tools/tasktool/commands.py`, in `cmd_worktree_prune` (~L2327): the guards run only when `not force`. To know whether the merged guard *passed* (vs was skipped by `--force`), introduce a flag. Replace the guard block so that after the three `if not force:` guards, you compute:
  ```python
          merged_proven = False
          if not force:
              # (existing Guard 1: terminal status)
              # (existing Guard 2: branch merged) — record that it passed:
              parent = _authoritative_parent_branch(write_root, qid)
              if not wt.branch_is_merged(write_root, branch=branch, into=parent):
                  raise CommandError(
                      f"{qid}: branch {branch!r} is not merged into {parent!r}; "
                      f"merge first or pass --force"
                  )
              merged_proven = True
              # (existing Guard 3: clean tree)
  ```
  (Keep the existing terminal-status and clean-tree guards exactly as they are; the only structural change is setting `merged_proven = True` immediately after Guard 2's check passes, and hoisting `parent` if needed.)
- [ ] Then, in the **destructive step** (after the prune-from-inside early return, where `item.worktree_pruned_at = _today()` is set, ~L2418), add the stamp gated on all preconditions:
  ```python
          # Stamp landed_base_sha only when the merge is proven (§4.D F6):
          #  (a) done status (never cancelled), (b) the branch-merged guard passed,
          #  (c) not a --force prune. Otherwise leave landed_base_sha None.
          if (
              merged_proven
              and getattr(item, "status", None) == Status.DONE
          ):
              from tasktool.worktree import current_branch_head_sha
              parent = _authoritative_parent_branch(write_root, qid)
              try:
                  item.landed_base_sha = current_branch_head_sha(write_root, parent)
              except _subprocess.CalledProcessError:
                  item.landed_base_sha = None
  ```
  `merged_proven` is `False` whenever `--force` was passed, so `--force` never stamps. `status == Status.DONE` excludes cancelled slices even when their branch happens to be merged.

### 5.4 Run it — expect PASS

- [ ] Run the same command as 5.2. Expected: `1 passed`.

### 5.5 Regression: prune-from-inside (pending) must NOT stamp before finalize

- [ ] Confirm the existing `test_prune_from_inside_sets_pending_marker_and_skips_remove` still passes (the pending path returns before the destructive step, so no stamp):
  ```sh
  python -m pytest "tools/tasktool/tests/test_worktree_prune.py::test_prune_from_inside_sets_pending_marker_and_skips_remove" -q
  ```
  Expected: `1 passed`.

### 5.6 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_worktree_prune.py
  git commit -m "P7.S4: stamp landed_base_sha on normal guarded prune of merged done slice"
  ```

---

## Task 6 — Prove the non-stamping cases (cancelled / --force-unmerged / finalize-only)

### 6.1 Failing test: cancelled-slice prune does NOT stamp

- [ ] Append to `tools/tasktool/tests/test_worktree_prune.py`:
  ```python
  def test_prune_does_not_stamp_landed_base_sha_for_cancelled_slice(project_with_worktree):
      repo, wt = project_with_worktree
      # Merge so the branch-merged guard would pass, then cancel (not close).
      _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
           "worktree-p1-s1-first-slice")
      _tasktool(repo, "cancel", "P1.S1", "--reason", "dropped")
      res = _tasktool(repo, "worktree", "prune", "P1.S1")
      assert res.returncode == 0
      show = _tasktool(repo, "show", "P1.S1").stdout
      assert "landed_base_sha:" not in show
  ```

### 6.2 Failing test: `--force` prune of an unmerged branch does NOT stamp

- [ ] Append (reuses module-level `_project_with_closed_unmerged`):
  ```python
  def test_force_prune_unmerged_does_not_stamp_landed_base_sha(tmp_path):
      repo, wt = _project_with_closed_unmerged(tmp_path)  # done but branch unmerged
      res = _tasktool(repo, "worktree", "prune", "P1.S1", "--force")
      assert res.returncode == 0
      show = _tasktool(repo, "show", "P1.S1").stdout
      assert "landed_base_sha:" not in show
  ```

### 6.3 Failing test: `--finalize`-only path does NOT stamp

- [ ] Append:
  ```python
  def test_finalize_only_does_not_stamp_landed_base_sha(project_with_worktree):
      repo, wt = project_with_worktree
      _tasktool(repo, "close", "P1.S1", "--skip-review-gate")
      _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m",
           "worktree-p1-s1-first-slice")
      # Trigger the prune-from-inside pending path (defers, never stamps).
      subprocess.run(
          [str(TASKTOOL), "--project-root", str(repo),
           "worktree", "prune", "P1.S1"],
          cwd=wt, text=True, capture_output=True, check=True,
      )
      # Caller performs the destructive removal out-of-band, then finalizes.
      _run(repo, "git", "worktree", "remove", str(wt))
      res = _tasktool(repo, "worktree", "prune", "P1.S1", "--finalize")
      assert res.returncode == 0
      show = _tasktool(repo, "show", "P1.S1").stdout
      assert "landed_base_sha:" not in show
  ```

### 6.4 Run all three — expect PASS (the impl from Task 5 already satisfies them)

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_prune.py -k "does_not_stamp or finalize_only_does_not_stamp" -q
  ```
  Expected: `3 passed`. These are guard-proving tests; the Task 5 implementation should already make them green. If `test_prune_does_not_stamp_landed_base_sha_for_cancelled_slice` FAILS, the `status == Status.DONE` check is missing or wrong — fix it in `cmd_worktree_prune`, do not loosen the test. If `test_force_prune_unmerged_does_not_stamp_landed_base_sha` FAILS, `merged_proven` is being set under `--force` — ensure it is only set inside the `if not force:` block.

### 6.5 Regression: full prune suite

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_prune.py -q
  ```
  Expected: all pass.

### 6.6 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/tests/test_worktree_prune.py
  git commit -m "P7.S4: prove cancelled/force-unmerged/finalize-only prune does not stamp landed_base_sha"
  ```

---

## Task 7 — `worktree status --integration` CLI wiring + base-ahead reporting

### 7.1 Failing test: `--integration` flag is accepted and reports base-ahead count

- [ ] Create `tools/tasktool/tests/test_worktree_integration.py` with this header + first test:
  ```python
  from __future__ import annotations

  import json
  import subprocess
  from pathlib import Path

  TASKTOOL = Path(__file__).resolve().parents[1] / "tasktool"


  def _run(cwd: Path, *args: str) -> str:
      return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True).stdout


  def _tasktool(repo: Path, *args: str, check: bool = True):
      return subprocess.run(
          [str(TASKTOOL), "--project-root", str(repo), *args],
          text=True, capture_output=True, check=check,
      )


  def _init_repo(root: Path) -> Path:
      root.mkdir(parents=True, exist_ok=True)
      _run(root, "git", "init", "-q", "-b", "main")
      _run(root, "git", "config", "user.email", "t@example.com")
      _run(root, "git", "config", "user.name", "t")
      (root / "README").write_text("init\n")
      _run(root, "git", "add", "README")
      _run(root, "git", "commit", "-q", "-m", "init")
      return root


  def _seed(repo: Path, *slice_titles: str) -> None:
      (repo / "docs").mkdir(exist_ok=True)
      _tasktool(repo, "config", "init-local")
      _tasktool(repo, "init", "--project", "demo")
      _tasktool(repo, "create", "phase", "--title", "Phase 1")
      for title in slice_titles:
          _tasktool(repo, "create", "slice", "P1", "--title", title)
      _run(repo, "git", "add", "-A")
      _run(repo, "git", "commit", "-q", "-m", "seed")


  def test_integration_reports_base_ahead_count(tmp_path):
      repo = _init_repo(tmp_path / "proj")
      _seed(repo, "First slice")
      _tasktool(repo, "start", "P1.S1")  # records worktree_base_sha at current main
      # Advance main by two commits after the worktree branched.
      (repo / "x").write_text("1")
      _run(repo, "git", "add", "x")
      _run(repo, "git", "commit", "-q", "-m", "x")
      (repo / "y").write_text("2")
      _run(repo, "git", "add", "y")
      _run(repo, "git", "commit", "-q", "-m", "y")
      out = _tasktool(repo, "worktree", "status", "P1.S1", "--integration").stdout
      assert "base ahead of worktree_base_sha: 2 commit" in out
  ```

### 7.2 Run it — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_integration.py::test_integration_reports_base_ahead_count -q
  ```
  Expected: FAIL — argparse rejects `--integration` (`error: unrecognized arguments: --integration`), nonzero exit, `subprocess.CalledProcessError`.

### 7.3 Minimal impl: add `--integration` flag and dispatch

- [ ] In `tools/tasktool/cli.py`, where `worktree status` is registered (~L126):
  ```python
      p_wt_status = wt_sub.add_parser("status")
      p_wt_status.add_argument("id")
      p_wt_status.add_argument("--integration", action="store_true")
  ```
- [ ] In the dispatch block (~L396), change:
  ```python
              elif args.wt_cmd == "status":
                  sys.stdout.write(commands.cmd_worktree_status(repo_root=root, id=args.id))
  ```
  to:
  ```python
              elif args.wt_cmd == "status":
                  if args.integration:
                      sys.stdout.write(
                          commands.cmd_worktree_status_integration(repo_root=root, id=args.id)
                      )
                  else:
                      sys.stdout.write(
                          commands.cmd_worktree_status(repo_root=root, id=args.id)
                      )
  ```
- [ ] In `tools/tasktool/commands.py`, add the new command after `cmd_worktree_status` (~L2263):
  ```python
  def cmd_worktree_status_integration(*, repo_root: Path, id: str) -> str:
      from tasktool.config import load_config
      from tasktool import worktree as wt
      with _read_context(repo_root) as write_root:
          p = _load(write_root)
          qid, _container, item = _find_item(p, id)
          phase_id = qid.split(".")[0]
          base_branch = load_config(write_root).tasklist.authoritative_branch
          base_sha = getattr(item, "worktree_base_sha", None)
          lines = [f"{qid}: integration vs {base_branch}"]
          if base_sha is None:
              lines.append("worktree_base_sha: <not recorded> — cannot compute staleness")
              return "\n".join(lines) + "\n"
          lines.append(f"worktree_base_sha: {base_sha}")
          try:
              base_head = wt.current_branch_head_sha(write_root, base_branch)
          except _subprocess.CalledProcessError:
              lines.append(f"base HEAD: <unresolved branch {base_branch!r}>")
              return "\n".join(lines) + "\n"
          ahead = wt.rev_list_count(write_root, base_sha, base_head)
          lines.append(
              f"base ahead of worktree_base_sha: {ahead} commit"
              + ("" if ahead == 1 else "s")
          )
          # Sibling landed-since reporting is added in Task 8/9.
          return "\n".join(lines) + "\n"
  ```

### 7.4 Run it — expect PASS

- [ ] Run the same command as 7.2. Expected: `1 passed`.

### 7.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/cli.py tools/tasktool/commands.py tools/tasktool/tests/test_worktree_integration.py
  git commit -m "P7.S4: add worktree status --integration with base-ahead reporting"
  ```

---

## Task 8 — Landed-sibling detection: authoritative (`landed_base_sha`) signal

### 8.1 Failing test: a sibling with `landed_base_sha` in the since-window is reported as landed (authoritative)

- [ ] Append to `tools/tasktool/tests/test_worktree_integration.py` a helper to build two sibling worktrees and a test:
  ```python
  def _start_worktree(repo: Path, slice_qid: str) -> Path:
      out = _tasktool(repo, "start", slice_qid).stdout
      # `start` prints `cd <path>`; recover the path from tasklist.json instead.
      data = json.loads((repo / "docs" / "tasklist.json").read_text())
      slc = next(
          s for ph in data["phases"] for s in ph["slices"]
          if f"{ph['id']}.{s['id']}" == slice_qid
      )
      return (repo / slc["worktree_path"]).resolve()


  def _land_sibling(repo: Path, sibling_qid: str) -> None:
      """Close + merge + prune a sibling so it stamps landed_base_sha."""
      data = json.loads((repo / "docs" / "tasklist.json").read_text())
      slc = next(
          s for ph in data["phases"] for s in ph["slices"]
          if f"{ph['id']}.{s['id']}" == sibling_qid
      )
      branch = slc["worktree_branch"]
      wt_path = (repo / slc["worktree_path"]).resolve()
      # Make a real commit on the sibling branch so the merge is non-empty.
      (wt_path / "sibling-work").write_text("x")
      _run(wt_path, "git", "add", "sibling-work")
      _run(wt_path, "git", "commit", "-q", "-m", "sibling work")
      _tasktool(repo, "close", sibling_qid, "--skip-review-gate")
      _run(repo, "git", "merge", "--no-ff", "-q", "-m", f"merge {branch}", branch)
      _tasktool(repo, "worktree", "prune", sibling_qid)


  def test_integration_reports_landed_sibling_via_landed_base_sha(tmp_path):
      repo = _init_repo(tmp_path / "proj")
      _seed(repo, "This slice", "Sibling slice")
      # Start this slice first so its worktree_base_sha predates the sibling landing.
      _start_worktree(repo, "P1.S1")
      _start_worktree(repo, "P1.S2")
      _land_sibling(repo, "P1.S2")  # stamps landed_base_sha = main HEAD after merge
      out = _tasktool(repo, "worktree", "status", "P1.S1", "--integration").stdout
      assert "landed since worktree_base_sha:" in out
      assert "P1.S2" in out
      assert "(authoritative)" in out
  ```

### 8.2 Run it — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_integration.py::test_integration_reports_landed_sibling_via_landed_base_sha -q
  ```
  Expected: FAIL (`assert "landed since worktree_base_sha:" in out`).

### 8.3 Minimal impl: sibling iteration + authoritative landed signal

- [ ] In `tools/tasktool/commands.py`, replace the `# Sibling landed-since reporting is added in Task 8/9.` placeholder in `cmd_worktree_status_integration` with sibling computation. First add a helper above the command:
  ```python
  def _phase_siblings(p, phase_id: str, exclude_slice_qid: str):
      """Yield (sibling_qid, sibling_item) for every slice in `phase_id` except the
      named one. Qualified ids are `<phase>.<slice>`."""
      for ph in p.phases:
          if ph.id != phase_id:
              continue
          for s in ph.slices:
              sib_qid = f"{ph.id}.{s.id}"
              if sib_qid != exclude_slice_qid:
                  yield sib_qid, s


  def _sibling_landed_signal(write_root: Path, sib_item, *, base_sha: str, base_head: str):
      """Return (landed: bool, signal: str) for a sibling slice.

      Both the authoritative and the ancestry signal are gated by the SAME
      half-open "since worktree_base_sha" window (spec §4.D): the relevant
      commit must be reachable from `base_head` AND NOT reachable from
      `base_sha`. A sibling that was already integrated before THIS worktree
      branched is NOT "landed since" — reporting it would re-surface work that
      was already present at branch time.

      Priority (§4.D F2):
        1. non-null landed_base_sha in the half-open `base_sha..base_head`
           window                                                  -> authoritative
        2. done + existing branch whose TIP is in the same half-open
           window (reachable from base_head, not from base_sha)    -> ancestry (weaker)
        3. otherwise                                               -> unknown
      """
      from tasktool import worktree as wt
      from tasktool.model import Status
      landed_sha = getattr(sib_item, "landed_base_sha", None)
      if landed_sha:
          if wt.commit_is_in_range(write_root, landed_sha, base=base_sha, head=base_head):
              return True, "authoritative"
          # Landed, but before this worktree branched — not "since".
          return False, "landed-before-window"
      status = getattr(sib_item, "status", None)
      branch = getattr(sib_item, "worktree_branch", None)
      if status == Status.DONE and branch and wt.branch_exists(write_root, branch):
          # Resolve the sibling branch's tip SHA, then apply the half-open window.
          # `branch_is_merged(..., into=base_head)` alone is INSUFFICIENT: it is
          # true even when the branch merged BEFORE base_sha, which violates the
          # "since" window. Require the tip to be in `base_sha..base_head`.
          try:
              tip = wt.current_branch_head_sha(write_root, branch)
          except _subprocess.CalledProcessError:
              return False, "unknown"
          if wt.commit_is_in_range(write_root, tip, base=base_sha, head=base_head):
              return True, "ancestry"
          # Tip reachable from base_head but also from base_sha => merged before
          # this worktree branched; not landed-since. Tip not reachable from
          # base_head at all => not merged into base yet.
          if wt.branch_is_merged(write_root, branch=branch, into=base_head):
              return False, "merged-before-window"
          return False, "unmerged-branch"
      if status == Status.DONE:
          return False, "unknown"
      return False, "not-done"
  ```
  Note: `_subprocess` is the module-level alias for `subprocess` already imported at the top of `commands.py` (`import subprocess as _subprocess`); reuse it.
- [ ] In `cmd_worktree_status_integration`, after the `base ahead ...` line, add:
  ```python
          landed = []
          for sib_qid, sib_item in _phase_siblings(p, phase_id, qid):
              did_land, signal = _sibling_landed_signal(
                  write_root, sib_item, base_sha=base_sha, base_head=base_head
              )
              if did_land:
                  landed.append((sib_qid, signal, sib_item))
          if landed:
              lines.append("landed since worktree_base_sha:")
              for sib_qid, signal, _sib in landed:
                  lines.append(f"  - {sib_qid} ({signal})")
          else:
              lines.append("landed since worktree_base_sha: (none)")
  ```

### 8.4 Run it — expect PASS

- [ ] Run the same command as 8.2. Expected: `1 passed`.

### 8.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_worktree_integration.py
  git commit -m "P7.S4: report landed siblings via authoritative landed_base_sha signal"
  ```

---

## Task 9 — Ancestry-fallback and `unknown` landed signals

### 9.1 Failing test: a done sibling merged outside the prune path is reported via ancestry

- [ ] Append to `tools/tasktool/tests/test_worktree_integration.py`:
  ```python
  def test_integration_reports_landed_sibling_via_ancestry_fallback(tmp_path):
      repo = _init_repo(tmp_path / "proj")
      _seed(repo, "This slice", "Sibling slice")
      _start_worktree(repo, "P1.S1")
      sib_wt = _start_worktree(repo, "P1.S2")
      data = json.loads((repo / "docs" / "tasklist.json").read_text())
      sib = next(s for s in data["phases"][0]["slices"] if s["id"] == "S2")
      branch = sib["worktree_branch"]
      # Real commit, close, merge — but DO NOT prune (so no landed_base_sha stamp).
      (sib_wt / "w").write_text("x")
      _run(sib_wt, "git", "add", "w")
      _run(sib_wt, "git", "commit", "-q", "-m", "w")
      _tasktool(repo, "close", "P1.S2", "--skip-review-gate")
      _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m", branch)
      out = _tasktool(repo, "worktree", "status", "P1.S1", "--integration").stdout
      assert "P1.S2 (ancestry)" in out


  def test_integration_reports_unknown_for_done_sibling_without_branch_or_sha(tmp_path):
      repo = _init_repo(tmp_path / "proj")
      _seed(repo, "This slice", "Sibling slice")
      _start_worktree(repo, "P1.S1")
      # Sibling was started in-place (no branch) and closed; neither signal exists.
      _tasktool(repo, "start", "P1.S2", "--in-place")
      _tasktool(repo, "close", "P1.S2", "--skip-review-gate")
      out = _tasktool(repo, "worktree", "status", "P1.S1", "--integration").stdout
      # Not silently treated as landed: it must NOT appear in the landed list.
      assert "P1.S2 (authoritative)" not in out
      assert "P1.S2 (ancestry)" not in out
      # And the unknown state is surfaced.
      assert "P1.S2 (unknown)" in out


  def test_integration_ancestry_not_landed_when_sibling_merged_before_base_sha(tmp_path):
      """F2 negative case: a done sibling whose branch is already an ancestor of
      THIS slice's worktree_base_sha (it merged BEFORE this worktree branched)
      must be reported NOT landed-since — `branch_is_merged(into=base_head)` is
      true for it, so the half-open window is what excludes it."""
      repo = _init_repo(tmp_path / "proj")
      _seed(repo, "This slice", "Sibling slice")
      # Start the SIBLING first, do its work, and MERGE it into main — all BEFORE
      # this slice's worktree branches.
      sib_wt = _start_worktree(repo, "P1.S2")
      data = json.loads((repo / "docs" / "tasklist.json").read_text())
      sib = next(s for s in data["phases"][0]["slices"] if s["id"] == "S2")
      branch = sib["worktree_branch"]
      (sib_wt / "w").write_text("x")
      _run(sib_wt, "git", "add", "w")
      _run(sib_wt, "git", "commit", "-q", "-m", "w")
      _tasktool(repo, "close", "P1.S2", "--skip-review-gate")
      _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m", branch)
      # NOTE: do NOT prune S2, so it has no landed_base_sha and falls to the
      # ancestry branch. Its branch ref still exists and IS an ancestor of main.
      # NOW this slice branches — base_sha = main HEAD, which already contains S2.
      _start_worktree(repo, "P1.S1")
      out = _tasktool(repo, "worktree", "status", "P1.S1", "--integration").stdout
      # S2 merged before P1.S1 branched: it is NOT "landed since worktree_base_sha".
      assert "P1.S2 (ancestry)" not in out
      assert "P1.S2 (authoritative)" not in out
      # It is also not "undetermined": its branch is genuinely merged into base,
      # just outside the window. It must not appear in the landed list at all.
      # (The signal `merged-before-window` is non-landed and not surfaced.)
  ```

### 9.2 Run them — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_integration.py -k "ancestry_fallback or unknown_for_done_sibling or ancestry_not_landed" -q
  ```
  Expected: the ancestry-fallback positive test passes (Task 8 impl included the windowed ancestry branch); `test_integration_ancestry_not_landed_when_sibling_merged_before_base_sha` passes only once the half-open gate from Task 8.3 is in place (it FAILS against a naive `branch_is_merged(into=base_head)` ancestry check — this is the F2 regression guard); the `unknown` test FAILS because `unknown`-signal siblings are not surfaced yet.

### 9.3 Minimal impl: surface non-landed `unknown`/diagnostic siblings

- [ ] In `cmd_worktree_status_integration`, extend the sibling loop to also collect non-landed siblings whose signal is diagnostically interesting (`unknown`, `unmerged-branch`), and print them so a coordinator sees the gap rather than silence:
  ```python
          landed = []
          undetermined = []
          for sib_qid, sib_item in _phase_siblings(p, phase_id, qid):
              did_land, signal = _sibling_landed_signal(
                  write_root, sib_item, base_sha=base_sha, base_head=base_head
              )
              if did_land:
                  landed.append((sib_qid, signal, sib_item))
              elif signal in {"unknown", "unmerged-branch"}:
                  undetermined.append((sib_qid, signal, sib_item))
          if landed:
              lines.append("landed since worktree_base_sha:")
              for sib_qid, signal, _sib in landed:
                  lines.append(f"  - {sib_qid} ({signal})")
          else:
              lines.append("landed since worktree_base_sha: (none)")
          if undetermined:
              lines.append("undetermined siblings (could not prove landed):")
              for sib_qid, signal, _sib in undetermined:
                  lines.append(f"  - {sib_qid} ({signal})")
  ```

### 9.4 Run them — expect PASS

- [ ] Run the same command as 9.2. Expected: `3 passed` (`...via_ancestry_fallback`, `...ancestry_not_landed_when_sibling_merged_before_base_sha`, `...unknown_for_done_sibling_without_branch_or_sha`).

### 9.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_worktree_integration.py
  git commit -m "P7.S4: report ancestry-fallback and surface undetermined (unknown) siblings"
  ```

---

## Task 10 — Surface-overlap reporting for landed siblings

### 10.1 Failing test: a landed sibling sharing an integration surface is flagged

- [ ] Append to `tools/tasktool/tests/test_worktree_integration.py`. This test sets `integration_surfaces` on both slices via direct tasklist edit (the `surface add` CLI is S2's responsibility and may not exist yet; setting the field directly keeps this slice decoupled):
  ```python
  def _set_surfaces(repo: Path, slice_id: str, surfaces: list[str]) -> None:
      path = repo / "docs" / "tasklist.json"
      data = json.loads(path.read_text())
      for ph in data["phases"]:
          for s in ph["slices"]:
              if s["id"] == slice_id:
                  s["integration_surfaces"] = surfaces
      path.write_text(json.dumps(data, indent=2) + "\n")


  def test_integration_flags_surface_overlap_with_landed_sibling(tmp_path):
      repo = _init_repo(tmp_path / "proj")
      _seed(repo, "This slice", "Sibling slice")
      _set_surfaces(repo, "S1", ["cms-block-registry", "theme-tail-css"])
      _set_surfaces(repo, "S2", ["cms-block-registry"])
      _run(repo, "git", "add", "-A")
      _run(repo, "git", "commit", "-q", "-m", "surfaces")
      _start_worktree(repo, "P1.S1")
      _start_worktree(repo, "P1.S2")
      _land_sibling(repo, "P1.S2")
      out = _tasktool(repo, "worktree", "status", "P1.S1", "--integration").stdout
      assert "shared integration surface" in out
      assert "cms-block-registry" in out
      assert "theme-tail-css" not in out  # not shared


  def test_integration_no_surface_overlap_when_disjoint(tmp_path):
      repo = _init_repo(tmp_path / "proj")
      _seed(repo, "This slice", "Sibling slice")
      _set_surfaces(repo, "S1", ["theme-tail-css"])
      _set_surfaces(repo, "S2", ["directus-schema"])
      _run(repo, "git", "add", "-A")
      _run(repo, "git", "commit", "-q", "-m", "surfaces")
      _start_worktree(repo, "P1.S1")
      _start_worktree(repo, "P1.S2")
      _land_sibling(repo, "P1.S2")
      out = _tasktool(repo, "worktree", "status", "P1.S1", "--integration").stdout
      assert "shared integration surface" not in out
  ```

### 10.2 Run them — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_integration.py -k "surface_overlap" -q
  ```
  Expected: the overlap test FAILS (`assert "shared integration surface" in out`); the disjoint test may pass vacuously.

### 10.3 Minimal impl: compute and report shared surfaces for landed siblings

- [ ] In `cmd_worktree_status_integration`, after building the `landed` list, compute overlaps against `this slice`'s surfaces:
  ```python
          my_surfaces = set(getattr(item, "integration_surfaces", []) or [])
          if landed:
              lines.append("landed since worktree_base_sha:")
              for sib_qid, signal, sib in landed:
                  sib_surfaces = set(getattr(sib, "integration_surfaces", []) or [])
                  shared = sorted(my_surfaces & sib_surfaces)
                  suffix = (
                      f" — shared integration surface: {', '.join(shared)}"
                      if shared else ""
                  )
                  lines.append(f"  - {sib_qid} ({signal}){suffix}")
          else:
              lines.append("landed since worktree_base_sha: (none)")
  ```
  (Replace the plain landed-printing loop from Task 9 with this surface-aware one; keep the `undetermined` block unchanged.)

### 10.4 Run them — expect PASS

- [ ] Run the same command as 10.2. Expected: `2 passed`.

### 10.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_worktree_integration.py
  git commit -m "P7.S4: flag shared integration surfaces against landed siblings"
  ```

---

## Task 11 — Edge cases + full-suite verification + slice close

### 11.1 Failing test: `--integration` on a slice with no recorded base SHA degrades gracefully

- [ ] Append to `tools/tasktool/tests/test_worktree_integration.py`:
  ```python
  def test_integration_handles_missing_base_sha(tmp_path):
      repo = _init_repo(tmp_path / "proj")
      _seed(repo, "This slice")
      # Never started -> no worktree_base_sha recorded.
      res = _tasktool(repo, "worktree", "status", "P1.S1", "--integration", check=False)
      assert res.returncode == 0
      assert "worktree_base_sha: <not recorded>" in res.stdout
  ```

### 11.2 Run it — expect PASS

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_integration.py::test_integration_handles_missing_base_sha -q
  ```
  Expected: `1 passed` (handled by the early return added in Task 7.3). If it FAILS, the early `if base_sha is None` guard regressed.

### 11.3 Failing test: in-place slice with recorded base SHA still reports

- [ ] Append:
  ```python
  def test_integration_works_for_in_place_slice(tmp_path):
      repo = _init_repo(tmp_path / "proj")
      _seed(repo, "This slice")
      _tasktool(repo, "start", "P1.S1", "--in-place")  # records base_sha, no worktree dir
      (repo / "z").write_text("z")
      _run(repo, "git", "add", "z")
      _run(repo, "git", "commit", "-q", "-m", "z")
      out = _tasktool(repo, "worktree", "status", "P1.S1", "--integration").stdout
      assert "base ahead of worktree_base_sha: 1 commit" in out
  ```

### 11.4 Run it — expect PASS or FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_worktree_integration.py::test_integration_works_for_in_place_slice -q
  ```
  Expected: `1 passed` (the `--integration` path keys off `worktree_base_sha`, not on a worktree dir existing, so in-place works). If it FAILS because `cmd_worktree_status_integration` short-circuits on `worktree_in_place`, remove that short-circuit — the integration report is valid for in-place slices.

### 11.5 Focused F2 regression gate, then full tasktool test suite — expect all PASS

- [ ] First re-run the half-open-window ancestry regression guard explicitly, to confirm the F2 over-reporting fix holds:
  ```sh
  python -m pytest "tools/tasktool/tests/test_worktree_integration.py::test_integration_ancestry_not_landed_when_sibling_merged_before_base_sha" -q
  ```
  Expected: `1 passed`. This is the test that fails against a naive `branch_is_merged(into=base_head)` ancestry check; its passing proves the half-open window gates the ancestry fallback.
- [ ] Then run the full suite:
  ```sh
  python -m pytest tools/tasktool/tests -q
  ```
  Expected: all pass, including the pre-existing `test_start_worktree.py`, `test_worktree_prune.py`, `test_worktree_lifecycle.py`, `test_worktree_repair.py`, `test_worktree_authority.py`, `test_worktree_naming.py`, `test_serialize.py`, `test_model.py`. If any pre-existing test now fails, treat it as a regression introduced by this slice (use superstar:systematic-debugging) — do not edit the failing test to accommodate new behavior unless the test was asserting the absence of the new fields.

### 11.6 Commit edge-case tests

- [ ] Run:
  ```sh
  git add tools/tasktool/tests/test_worktree_integration.py
  git commit -m "P7.S4: cover missing-base-sha and in-place integration edge cases"
  ```

### 11.7 Integration checkpoint before review (per subagent-driven-development)

- [ ] Run `./tools/tasktool/tasktool worktree status P7.S4 --integration` (dog-fooding the feature you just built).
  - **If you backfilled the P7.S4 row's `worktree_base_sha` per Task 1.1:** this performs a real staleness check. If a sibling slice (e.g. P7.S1) has landed since this worktree's `worktree_base_sha` and shares a surface, integrate the current base branch (merge/rebase), re-run `python -m pytest tools/tasktool/tests -q`, and only then proceed to review.
  - **If you did NOT backfill** (the P7.S4 row has no `worktree_base_sha` because its own `start` predated the capture code): the command will print `worktree_base_sha: <not recorded> — cannot compute staleness` and exit 0. That is the expected, graceful-degradation path; confirm it exits 0 and treat the checkpoint as satisfied by the manual-integration habit rather than the tool. Either way, before review still manually confirm the base branch has no unintegrated sibling work that touches files this slice changed (`worktree.py`, the worktree block of `commands.py`, `cli.py`); if it does, integrate and re-run the suite first.

### 11.8 Post-slice review + close

- [ ] Run `superstar:external-review --kind post-slice` for P7.S4. Apply any reviewer-driven fixes via the same TDD loop (delegated to a subagent if using subagent-driven-development). Iterate until the verdict is `ready` or `ready with small edits`.
- [ ] Close the slice:
  ```sh
  ./tools/tasktool/tasktool close P7.S4 --reviewer-chain <chain-from-review>
  ```
  (Do not bump the plugin version or run release scripts from this slice — version bump + plugin re-sync happen at phase close per the repo release policy.)

---

## Notes for the implementer

- **Do not edit `plugins/superstar/`.** It is a release-time synced copy of `tools/tasktool/`. Edit only `tools/tasktool/`.
- **`Status` import:** `cmd_worktree_prune` and the new helpers reference `Status.DONE`. `Status` is already imported at the top of `commands.py` (`from tasktool.model import (... Status ...)`); the helper `_sibling_landed_signal` imports it locally to keep the function self-contained — either is fine, prefer the module-level import already present.
- **`worktree_base_sha` on idempotent re-`start`:** the `CONSISTENT` early-return in `_apply_start_default` means a second `start` does not recompute the SHA. That is correct — the base the worktree branched from does not change just because you re-ran `start`. P7.S5's `worktree sync` is the only command that advances `worktree_base_sha`.
- **Half-open window semantics:** `worktree_base_sha..base-HEAD` excludes `worktree_base_sha` itself. A sibling whose `landed_base_sha` equals the *exact* commit this worktree branched from is **not** "landed since" — it was already integrated when this worktree was created. `commit_is_in_range` enforces this (reachable from head, not from base).
- **JSON output is out of scope** for S4 (the spec's `--integration` is described as a human report; `surface check --format json` belongs to S3). Keep the output text-only; do not add a `--format json` flag here.
