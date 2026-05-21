<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 3 of x16-shim-version-stamping-X16-post-slice.

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
| 1 | None | 0 | 0 |
| 2 | revise | 3 | 2 |

## Prior-round findings

Source: primary reviewer response from r2

# Review — 2026-05-21-X16-shim-version-stamping.md (post-slice, round 2)

- Target: `docs/plans/2026-05-21-X16-shim-version-stamping.md`
- Request: `docs/reviewer/x16-shim-version-stamping-X16-post-slice/r2-2026-05-21T0510-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: blocking — X16 is not closed in the canonical tracker. `docs/tasklist.json` still has `X16` as `"status": "ready"`, with `"started": null`, `"closed": null`, empty notes, and only the spec ref registered at `docs/tasklist.json:226`. This contradicts the plan’s closeout requirement to run `tasktool close X16` at `docs/plans/2026-05-21-X16-shim-version-stamping.md:2359` and leaves the post-slice gate unsatisfied.

F2 — Severity: blocking — `deploy.sh --check` does not inspect the pre-commit hook, despite the spec requiring shim/hook header parsing and hook status in the diagnostic. The acceptance criterion says `deploy.sh --check` must parse shim/hook headers and apply the status lattice at `docs/specs/2026-05-21-X16-shim-version-stamping-design.md:412`, and the expected output includes “Pre-commit hook (current repo)” at `docs/specs/2026-05-21-X16-shim-version-stamping-design.md:341`. The implementation only checks three global shims and plugin caches at `scripts/deploy.sh:177` and `scripts/deploy.sh:199`, so a stale hook can be missed while `--check` exits 0.

F3 — Severity: important — The tasktool hook handshake misses linked worktrees. `check_pre_commit_hook()` locates the hook as `repo_top / ".git" / "hooks" / "pre-commit"` at `tools/tasktool/hook_handshake.py:56`, but in a linked worktree `.git` is a file and the actual hook path must come from `git rev-parse --git-path hooks/pre-commit`. I reproduced this in `/tmp`: a stale stamped hook in the real `git-path` hook location returned `message=None`. The existing tests only write hooks under `repo/.git/hooks` (`tools/tasktool/tests/test_hook_handshake.py:19`), so this common Superstar workflow is uncovered.

2. Open questions / assumptions

I assume X16 is being reviewed as a completion gate, not as a WIP checkpoint. If that is wrong, the task tracker still needs to say so explicitly because the current tracker state presents the work as not started.

3. Suggested document edits

Add a resolution note or closeout evidence that includes the post-slice reviewer chain, `tasktool close X16`, and the final verification commands. If `deploy.sh --check` intentionally excludes the hook, the spec and acceptance criteria must be changed; otherwise implement the hook row.

4. Verification gaps / commands that should be run

Run or add coverage for:

```bash
python3 -m pytest tools/tasktool/tests/test_hook_handshake.py -v
python3 -m pytest scripts/tests/test_deploy_check.py -v
bash scripts/deploy.sh --check
tools/tasktool/tasktool show X16
tools/tasktool/tasktool close X16 --reviewer-chain docs/reviewer/x16-shim-version-stamping-X16-post-slice
```

Fresh checks I ran: `tasktool validate --strict-format` passed, `tasktool artifact status X16 --strict` passed, and `bash scripts/deploy.sh --check` exited 0 but showed no pre-commit hook section.

Overall verdict: revise


## Resolution report for prior round

# Resolution for r2

## F1
Status: deferred
Notes:
Closeout (`tasktool close X16`) is the explicit final step after the post-slice review passes. The plan's Task 11 / T11 schedules this step; the coordinator runs it after r3+ verdict is `ready`. Not in scope for this fix round.

## F2
Status: fixed
Evidence:
- Commit: f618c6e
- Files: `scripts/deploy.sh:130` (new `check_hook`), `scripts/deploy.sh:272` (call site between Global shims and Plugin caches), `scripts/tests/test_deploy_check.py:131` (six new cases) and helper updates at `scripts/tests/test_deploy_check.py:28`.
- Verification:
  - `python3 -m pytest scripts/tests/test_deploy_check.py -v` → 13 passed.
  - `bash scripts/deploy.sh --check` against the real repo prints a new "Pre-commit hook" section with row `pre-commit  OK  v6.5.0 root=<repo>` and exits 0.

Notes:
Added a Pre-commit hook diagnostic section between Global shims and Plugin caches in `run_check`. The new `check_hook` function resolves the hook path via `git rev-parse --git-path hooks/pre-commit` (worktree-safe, matches the install.sh --hook resolution), then emits one of `OK / MISSING_TARGET / MALFORMED / DRIFT / MISSING_SOURCE / NOT_DEPLOYED` with the same exit-code semantics as the shim section. Foreign (non-tasktool) hooks and the absence of a git working tree emit `NOT_DEPLOYED` without flipping the exit code. Reuses the existing `PARSE_HEADER` awk (which already matches both `superstar-shim-*` and `superstar-hook-*` keys) and `EXPAND_PATH`. The test helper `_run_check` now accepts an optional `cwd` (and defaults to `home` so existing tests don't accidentally see the surrounding repo's hook), and the new cases create a fresh `git init` directory under `tmp_path` and exercise each lattice state.

## F3
Status: fixed
Evidence:
- Commit: f618c6e
- Files: `tools/tasktool/hook_handshake.py:26` (new `_git_hook_path` helper) and `tools/tasktool/hook_handshake.py:75` (replaced hardcoded path); `tools/tasktool/tests/test_hook_handshake.py:128` (new `test_drift_returns_error_in_worktree`).
- Verification: `python3 -m pytest tools/tasktool/tests/test_hook_handshake.py tools/tasktool/tests/test_pre_commit_hook.py -v` → 23 passed.

Notes:
Replaced the hardcoded `repo_top / ".git" / "hooks" / "pre-commit"` path with a `git rev-parse --git-path hooks/pre-commit` resolution and absolute-path normalization (relative results are joined with `repo_top`). This mirrors the worktree-safe resolution already in `tools/tasktool/install.sh --hook`. The new test creates a real linked worktree via `git worktree add`, sanity-checks that `.git` inside the worktree is a file (gitdir pointer), then writes a stale stamped hook at the path that `git rev-parse --git-path` reports (the common-dir hooks/ of the primary repo). The handshake correctly returns the drift message when invoked from inside the worktree — proving the previous hardcoded path would have silently missed it.


## Changes since prior round

Worktree status: dirty

### git diff base..HEAD

diff --git a/docs/reviewer/x16-shim-version-stamping-X16-post-slice/r2-resolution.md b/docs/reviewer/x16-shim-version-stamping-X16-post-slice/r2-resolution.md
new file mode 100644
index 0000000..dd46453
--- /dev/null
+++ b/docs/reviewer/x16-shim-version-stamping-X16-post-slice/r2-resolution.md
@@ -0,0 +1,28 @@
+# Resolution for r2
+
+## F1
+Status: deferred
+Notes:
+Closeout (`tasktool close X16`) is the explicit final step after the post-slice review passes. The plan's Task 11 / T11 schedules this step; the coordinator runs it after r3+ verdict is `ready`. Not in scope for this fix round.
+
+## F2
+Status: fixed
+Evidence:
+- Commit: f618c6e
+- Files: `scripts/deploy.sh:130` (new `check_hook`), `scripts/deploy.sh:272` (call site between Global shims and Plugin caches), `scripts/tests/test_deploy_check.py:131` (six new cases) and helper updates at `scripts/tests/test_deploy_check.py:28`.
+- Verification:
+  - `python3 -m pytest scripts/tests/test_deploy_check.py -v` → 13 passed.
+  - `bash scripts/deploy.sh --check` against the real repo prints a new "Pre-commit hook" section with row `pre-commit  OK  v6.5.0 root=<repo>` and exits 0.
+
+Notes:
+Added a Pre-commit hook diagnostic section between Global shims and Plugin caches in `run_check`. The new `check_hook` function resolves the hook path via `git rev-parse --git-path hooks/pre-commit` (worktree-safe, matches the install.sh --hook resolution), then emits one of `OK / MISSING_TARGET / MALFORMED / DRIFT / MISSING_SOURCE / NOT_DEPLOYED` with the same exit-code semantics as the shim section. Foreign (non-tasktool) hooks and the absence of a git working tree emit `NOT_DEPLOYED` without flipping the exit code. Reuses the existing `PARSE_HEADER` awk (which already matches both `superstar-shim-*` and `superstar-hook-*` keys) and `EXPAND_PATH`. The test helper `_run_check` now accepts an optional `cwd` (and defaults to `home` so existing tests don't accidentally see the surrounding repo's hook), and the new cases create a fresh `git init` directory under `tmp_path` and exercise each lattice state.
+
+## F3
+Status: fixed
+Evidence:
+- Commit: f618c6e
+- Files: `tools/tasktool/hook_handshake.py:26` (new `_git_hook_path` helper) and `tools/tasktool/hook_handshake.py:75` (replaced hardcoded path); `tools/tasktool/tests/test_hook_handshake.py:128` (new `test_drift_returns_error_in_worktree`).
+- Verification: `python3 -m pytest tools/tasktool/tests/test_hook_handshake.py tools/tasktool/tests/test_pre_commit_hook.py -v` → 23 passed.
+
+Notes:
+Replaced the hardcoded `repo_top / ".git" / "hooks" / "pre-commit"` path with a `git rev-parse --git-path hooks/pre-commit` resolution and absolute-path normalization (relative results are joined with `repo_top`). This mirrors the worktree-safe resolution already in `tools/tasktool/install.sh --hook`. The new test creates a real linked worktree via `git worktree add`, sanity-checks that `.git` inside the worktree is a file (gitdir pointer), then writes a stale stamped hook at the path that `git rev-parse --git-path` reports (the common-dir hooks/ of the primary repo). The handshake correctly returns the drift message when invoked from inside the worktree — proving the previous hardcoded path would have silently missed it.
diff --git a/scripts/deploy.sh b/scripts/deploy.sh
index 9012474..50bb199 100755
--- a/scripts/deploy.sh
+++ b/scripts/deploy.sh
@@ -127,6 +127,77 @@ check_shim() {
     SHIM_SOURCE_ROOTS["$name"]="$expanded_root"
 }
 
+check_hook() {
+    # Resolve git hooks path for the current working tree (worktree-safe).
+    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
+        print_row "pre-commit" "NOT_DEPLOYED" "(not in a git working tree)"
+        return
+    fi
+
+    local repo_top
+    repo_top="$(git rev-parse --show-toplevel 2>/dev/null || true)"
+    local hook_path
+    hook_path="$(git rev-parse --git-path hooks/pre-commit 2>/dev/null || true)"
+    if [[ -z "$hook_path" ]]; then
+        print_row "pre-commit" "NOT_DEPLOYED" "(failed to resolve git hooks path)"
+        return
+    fi
+    case "$hook_path" in
+        /*) ;;
+        *) hook_path="$repo_top/$hook_path" ;;
+    esac
+
+    if [[ ! -f "$hook_path" ]]; then
+        EXIT_CODE=1
+        print_row "pre-commit" "MISSING_TARGET" "$hook_path"
+        return
+    fi
+
+    local header
+    header="$(PARSE_HEADER "$hook_path")"
+
+    local hook_name="" hook_version="" hook_source_root=""
+    while IFS= read -r line; do
+        [[ -z "$line" ]] && continue
+        case "$line" in
+            superstar-hook-name=*) hook_name="${line#superstar-hook-name=}" ;;
+            superstar-hook-version=*) hook_version="${line#superstar-hook-version=}" ;;
+            superstar-hook-source-root=*) hook_source_root="${line#superstar-hook-source-root=}" ;;
+        esac
+    done <<< "$header"
+
+    if [[ "$hook_name" != "tasktool-pre-commit" ]]; then
+        print_row "pre-commit" "NOT_DEPLOYED" "(not a tasktool hook) $hook_path"
+        return
+    fi
+
+    if [[ -z "$hook_version" || -z "$hook_source_root" ]]; then
+        EXIT_CODE=1
+        print_row "pre-commit" "MALFORMED" "$hook_path (missing version/source-root header)"
+        return
+    fi
+
+    local expanded_root
+    expanded_root="$(EXPAND_PATH "$hook_source_root")"
+
+    if [[ ! -d "$expanded_root" || ! -r "$expanded_root/VERSION" ]]; then
+        EXIT_CODE=1
+        print_row "pre-commit" "MISSING_SOURCE" "$expanded_root (no readable VERSION)"
+        return
+    fi
+
+    local src_version
+    src_version="$(tr -d '[:space:]' < "$expanded_root/VERSION")"
+
+    if [[ "$hook_version" != "$src_version" ]]; then
+        EXIT_CODE=1
+        print_row "pre-commit" "DRIFT" "hook=$hook_version source-root has $src_version root=$expanded_root"
+        return
+    fi
+
+    print_row "pre-commit" "OK" "v$hook_version root=$expanded_root"
+}
+
 check_cache() {
     local name="$1" cache_dir="$2" dev_version="$3"
     local status="" detail=""
@@ -196,6 +267,10 @@ run_check() {
         print_row "source-roots" "SOURCE_ROOT_INFO" "shims point at differing source roots:$unique_roots (informational)"
     fi
 
+    echo
+    echo "Pre-commit hook:"
+    check_hook
+
     echo
     echo "Plugin caches:"
     local dev_version=""
diff --git a/scripts/tests/test_deploy_check.py b/scripts/tests/test_deploy_check.py
index d28f112..6813bfe 100644
--- a/scripts/tests/test_deploy_check.py
+++ b/scripts/tests/test_deploy_check.py
@@ -25,18 +25,47 @@ def _make_stamped_shim(path: Path, *, name: str, version: str, source_root: str,
     path.chmod(0o755)
 
 
-def _run_check(home: Path, source_root: Path) -> subprocess.CompletedProcess:
+def _run_check(home: Path, source_root: Path, cwd: Path | None = None) -> subprocess.CompletedProcess:
     env = {
         "HOME": str(home),
         "SUPERSTAR_SOURCE_ROOT": str(source_root),
         "PATH": os.environ["PATH"],
     }
+    # Default cwd to HOME (a non-git tmp dir) so the new pre-commit hook
+    # section doesn't see the surrounding repository's hook by accident.
+    effective_cwd = cwd if cwd is not None else home
     return subprocess.run(
         ["bash", str(DEPLOY), "--check"],
         env=env, capture_output=True, text=True, check=False,
+        cwd=str(effective_cwd),
     )
 
 
+def _make_stamped_hook(path: Path, *, version: str, source_root: str) -> None:
+    path.parent.mkdir(parents=True, exist_ok=True)
+    path.write_text(textwrap.dedent(f"""\
+        #!/usr/bin/env sh
+        # tasktool-pre-commit-hook v1
+        # superstar-hook
+        # superstar-hook-name: tasktool-pre-commit
+        # superstar-hook-version: {version}
+        # superstar-hook-source-root: {source_root}
+        # superstar-hook-installer: tools/tasktool/install.sh --hook
+        # superstar-hook-generated-at: 2026-05-21T00:00:00Z
+        exit 0
+    """))
+    path.chmod(0o755)
+
+
+def _init_git_repo(path: Path) -> None:
+    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
+
+
+def _all_ok_shims(home: Path, source: Path) -> None:
+    for name in ("external-reviewer", "reviewer-agent", "tasktool"):
+        _make_stamped_shim(home / ".local" / "bin" / name, name=name, version="1.0.0", source_root=str(source))
+
+
 def test_check_exits_zero_when_all_ok(tmp_path: Path) -> None:
     home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
     source = tmp_path / "src"; source.mkdir()
@@ -117,3 +146,96 @@ def test_check_home_literal_expanded_in_output(tmp_path: Path) -> None:
     result = _run_check(home, source)
     assert "$HOME/" not in result.stdout
     assert str(source) in result.stdout
+
+
+# --- Pre-commit hook row tests ---
+
+def test_check_hook_ok(tmp_path: Path) -> None:
+    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
+    source = tmp_path / "src"; source.mkdir()
+    (source / "VERSION").write_text("1.0.0\n")
+    _all_ok_shims(home, source)
+    repo = tmp_path / "repo"; repo.mkdir()
+    _init_git_repo(repo)
+    _make_stamped_hook(repo / ".git" / "hooks" / "pre-commit", version="1.0.0", source_root=str(source))
+    result = _run_check(home, source, cwd=repo)
+    assert result.returncode == 0, result.stdout + result.stderr
+    assert "Pre-commit hook" in result.stdout
+    assert "pre-commit" in result.stdout
+    assert "OK" in result.stdout
+
+
+def test_check_hook_drift(tmp_path: Path) -> None:
+    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
+    source = tmp_path / "src"; source.mkdir()
+    (source / "VERSION").write_text("1.0.0\n")
+    _all_ok_shims(home, source)
+    repo = tmp_path / "repo"; repo.mkdir()
+    _init_git_repo(repo)
+    _make_stamped_hook(repo / ".git" / "hooks" / "pre-commit", version="0.9.0", source_root=str(source))
+    result = _run_check(home, source, cwd=repo)
+    assert result.returncode != 0
+    assert "DRIFT" in result.stdout
+    assert "source-root has 1.0.0" in result.stdout
+
+
+def test_check_hook_malformed(tmp_path: Path) -> None:
+    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
+    source = tmp_path / "src"; source.mkdir()
+    (source / "VERSION").write_text("1.0.0\n")
+    _all_ok_shims(home, source)
+    repo = tmp_path / "repo"; repo.mkdir()
+    _init_git_repo(repo)
+    hook = repo / ".git" / "hooks" / "pre-commit"
+    hook.parent.mkdir(parents=True, exist_ok=True)
+    hook.write_text(
+        "#!/usr/bin/env sh\n"
+        "# superstar-hook\n"
+        "# superstar-hook-name: tasktool-pre-commit\n"
+        "exit 0\n"
+    )
+    hook.chmod(0o755)
+    result = _run_check(home, source, cwd=repo)
+    assert result.returncode != 0
+    assert "MALFORMED" in result.stdout
+
+
+def test_check_hook_missing_target(tmp_path: Path) -> None:
+    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
+    source = tmp_path / "src"; source.mkdir()
+    (source / "VERSION").write_text("1.0.0\n")
+    _all_ok_shims(home, source)
+    repo = tmp_path / "repo"; repo.mkdir()
+    _init_git_repo(repo)
+    # no hook installed
+    result = _run_check(home, source, cwd=repo)
+    assert result.returncode != 0
+    assert "MISSING_TARGET" in result.stdout
+
+
+def test_check_hook_not_deployed_when_not_tasktool(tmp_path: Path) -> None:
+    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
+    source = tmp_path / "src"; source.mkdir()
+    (source / "VERSION").write_text("1.0.0\n")
+    _all_ok_shims(home, source)
+    repo = tmp_path / "repo"; repo.mkdir()
+    _init_git_repo(repo)
+    hook = repo / ".git" / "hooks" / "pre-commit"
+    hook.parent.mkdir(parents=True, exist_ok=True)
+    hook.write_text("#!/usr/bin/env sh\n# someone-elses-hook\nexit 0\n")
+    hook.chmod(0o755)
+    result = _run_check(home, source, cwd=repo)
+    assert result.returncode == 0, result.stdout + result.stderr
+    assert "NOT_DEPLOYED" in result.stdout
+
+
+def test_check_hook_not_deployed_when_not_in_git(tmp_path: Path) -> None:
+    home = tmp_path / "home"; (home / ".local" / "bin").mkdir(parents=True)
+    source = tmp_path / "src"; source.mkdir()
+    (source / "VERSION").write_text("1.0.0\n")
+    _all_ok_shims(home, source)
+    not_git = tmp_path / "not-git"; not_git.mkdir()
+    result = _run_check(home, source, cwd=not_git)
+    assert result.returncode == 0, result.stdout + result.stderr
+    assert "NOT_DEPLOYED" in result.stdout
+    assert "not in a git working tree" in result.stdout
diff --git a/tools/tasktool/hook_handshake.py b/tools/tasktool/hook_handshake.py
index 4b4daae..fd3cbb5 100644
--- a/tools/tasktool/hook_handshake.py
+++ b/tools/tasktool/hook_handshake.py
@@ -34,6 +34,30 @@ def _git_top(cwd: Path) -> Optional[Path]:
     return Path(result.stdout.strip())
 
 
+def _git_hook_path(cwd: Path, repo_top: Path) -> Optional[Path]:
+    """Resolve the pre-commit hook path via `git rev-parse --git-path`.
+
+    Worktree-safe: in a linked worktree `.git` is a file, and hooks live in
+    the common-dir of the parent repo. `git rev-parse --git-path hooks/<n>`
+    correctly resolves to that path. The output may be relative; resolve to
+    absolute by joining with `repo_top`.
+    """
+    result = subprocess.run(
+        ["git", "rev-parse", "--git-path", "hooks/pre-commit"],
+        cwd=cwd,
+        capture_output=True, text=True, check=False,
+    )
+    if result.returncode != 0:
+        return None
+    raw = result.stdout.strip()
+    if not raw:
+        return None
+    path = Path(raw)
+    if not path.is_absolute():
+        path = repo_top / path
+    return path
+
+
 def _parse_header(text: str) -> dict[str, str]:
     out: dict[str, str] = {}
     for line in text.splitlines()[:32]:
@@ -53,7 +77,9 @@ def check_pre_commit_hook(cwd: Optional[Path] = None) -> Optional[str]:
     repo_top = _git_top(cwd)
     if repo_top is None:
         return None
-    hook_path = repo_top / ".git" / "hooks" / "pre-commit"
+    hook_path = _git_hook_path(cwd, repo_top)
+    if hook_path is None:
+        return None
     if not hook_path.exists():
         return None
     try:
diff --git a/tools/tasktool/tests/test_hook_handshake.py b/tools/tasktool/tests/test_hook_handshake.py
index 3a43d52..b7e000c 100644
--- a/tools/tasktool/tests/test_hook_handshake.py
+++ b/tools/tasktool/tests/test_hook_handshake.py
@@ -110,6 +110,66 @@ def test_tasktool_main_exits_on_hook_drift(tmp_path: Path) -> None:
     assert "tasktool pre-commit hook is 1.0.0 but Superstar source is 1.0.1" in result.stderr
 
 
+def test_drift_returns_error_in_worktree(tmp_path: Path) -> None:
+    # Create a primary git repo, make a commit so a branch exists, then add a
+    # linked worktree. The pre-commit hook lives in the common-dir of the
+    # primary repo (resolved via `git rev-parse --git-path hooks/pre-commit`
+    # from inside the linked worktree).
+    primary = tmp_path / "primary"
+    primary.mkdir()
+    _init_git_repo(primary)
+    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=primary, check=True)
+    subprocess.run(["git", "config", "user.name", "Test"], cwd=primary, check=True)
+    (primary / "README").write_text("hi\n")
+    subprocess.run(["git", "add", "README"], cwd=primary, check=True)
+    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=primary, check=True)
+
+    worktree = tmp_path / "wt"
+    subprocess.run(
+        ["git", "worktree", "add", "-q", "-b", "feat", str(worktree)],
+        cwd=primary, check=True,
+    )
+
+    # Sanity-check: from inside the worktree, .git is a file (gitdir pointer).
+    assert (worktree / ".git").is_file()
+
+    source = tmp_path / "src"
+    source.mkdir()
+    (source / "VERSION").write_text("1.0.1\n")
+
+    # Resolve the hook path the same way handshake does and write a stale
+    # stamped hook there (in the primary repo's common-dir hooks/).
+    git_path = subprocess.run(
+        ["git", "rev-parse", "--git-path", "hooks/pre-commit"],
+        cwd=worktree, capture_output=True, text=True, check=True,
+    ).stdout.strip()
+    hook_path = Path(git_path)
+    if not hook_path.is_absolute():
+        # repo_top from inside the worktree should be the worktree path
+        repo_top = subprocess.run(
+            ["git", "rev-parse", "--show-toplevel"],
+            cwd=worktree, capture_output=True, text=True, check=True,
+        ).stdout.strip()
+        hook_path = Path(repo_top) / hook_path
+    hook_path.parent.mkdir(parents=True, exist_ok=True)
+    hook_path.write_text(
+        "#!/usr/bin/env sh\n"
+        "# tasktool-pre-commit-hook v1\n"
+        "# superstar-hook\n"
+        "# superstar-hook-name: tasktool-pre-commit\n"
+        "# superstar-hook-version: 1.0.0\n"
+        f"# superstar-hook-source-root: {source}\n"
+        "# superstar-hook-installer: tools/tasktool/install.sh --hook\n"
+        "# superstar-hook-generated-at: 2026-05-21T00:00:00Z\n"
+        "exit 0\n"
+    )
+    hook_path.chmod(0o755)
+
+    msg = hook_handshake.check_pre_commit_hook(cwd=worktree)
+    assert msg is not None, f"expected drift message; got None. hook_path={hook_path}"
+    assert "tasktool pre-commit hook is 1.0.0 but Superstar source is 1.0.1" in msg
+
+
 def test_tasktool_main_runs_normally_when_hook_ok(tmp_path: Path) -> None:
     _init_git_repo(tmp_path)
     source = tmp_path / "src"


### git diff HEAD (uncommitted)



### Untracked files

- docs/reviewer/x16-shim-version-stamping-X16-post-slice/.reviewer-output/ (omitted: binary or unreadable)
### docs/reviewer/x16-shim-version-stamping-X16-post-slice/chain.json

```
{
  "schema_version": 1,
  "chain": "x16-shim-version-stamping-X16-post-slice",
  "kind": "post-slice",
  "target": "docs/plans/2026-05-21-X16-shim-version-stamping.md",
  "work_id": "X16",
  "legacy_migrated": false,
  "rounds": [
    {
      "round": 1,
      "reviewers": [
        {
          "role": "primary",
          "sweep_group": null,
          "parent_round": 1,
          "request": "r1-2026-05-21T0510-primary-request.md",
          "response": "r1-2026-05-21T0510-primary-response.md",
          "verdict": null,
          "verdict_valid": false,
          "returncode": 1,
          "status": "failed",
          "provider": "codex",
          "caller_provider": "claude",
          "model": null,
          "sandbox": {
            "repo_root": "/home/simon/Dev/sigreer/skills/superstar/.claude/worktrees/x16-shim-version-stamping",
            "scratch_dir": "/tmp/superstar-reviewer-x16-shim-version-stamping-X16-post-slice-r1-primary-4d0vwfzf",
            "response_dir": "docs/reviewer/x16-shim-version-stamping-X16-post-slice/.reviewer-output/r1-primary",
            "mode": "workspace-write-with-read-access"
          },
          "started_at": "2026-05-21T04:10:07.050Z",
          "finished_at": "2026-05-21T04:10:07.054Z",
          "duration_ms": 3,
          "estimated_usage": {
            "formula": "ceil(chars / 4)",
            "prompt_chars": 51933,
            "response_chars": 704,
            "estimated_input_tokens": 12984,
            "estimated_output_tokens": 176,
            "estimated_total_tokens": 13160
          },
          "exact_usage": null,
          "usage_capture_status": "estimated_only",
          "usage_capture_error": null
        },
        {
          "role": "sweep",
          "sweep_group": 1,
          "parent_round": 1,
          "request": "r1-2026-05-21T0510-sweep1-request.md",
          "response": "r1-2026-05-21T0510-sweep1-response.md",
          "verdict": null,
          "verdict_valid": false,
          "returncode": 1,
          "status": "failed",
          "provider": "codex",
          "caller_provider": "claude",
          "model": null,
          "sandbox": {
            "repo_root": "/home/simon/Dev/sigreer/skills/superstar/.claude/worktrees/x16-shim-version-stamping",
            "scratch_dir": "/tmp/superstar-reviewer-x16-shim-version-stamping-X16-post-slice-r1-sweep1-8oijae1k",
            "response_dir": "docs/reviewer/x16-shim-version-stamping-X16-post-slice/.reviewer-output/r1-sweep1",
            "mode": "workspace-write-with-read-access"
          },
          "started_at": "2026-05-21T04:10:07.054Z",
          "finished_at": "2026-05-21T04:10:07.058Z",
          "duration_ms": 3,
          "estimated_usage": {
            "formula": "ceil(chars / 4)",
            "prompt_chars": 51933,
            "response_chars": 703,
            "estimated_input_tokens": 12984,
            "estimated_output_tokens": 176,
            "estimated_total_tokens": 13160
          },
          "exact_usage": null,
          "usage_capture_status": "estimated_only",
          "usage_capture_error": null
        }
      ],
      "status": "failed",
      "returncode": 1,
      "started_at": "2026-05-21T04:10:07.050Z",
      "finished_at": "2026-05-21T04:10:07.054Z",
      "duration_ms": 3,
      "provider": "codex",
      "caller_provider": "claude",
      "model": null,
      "estimated_usage": {
        "formula": "ceil(chars / 4)",
        "prompt_chars": 51933,
        "response_chars": 704,
        "estimated_input_tokens": 12984,
        "estimated_output_tokens": 176,
        "estimated_total_tokens": 13160
      },
      "exact_usage": null,
      "usage_capture_status": "estimated_only",
      "usage_capture_error": null,
      "merged_verdict": null,
      "merged_findings": null,
      "request": "r1-2026-05-21T0510-primary-request.md",
      "response": "r1-2026-05-21T0510-primary-response.md",
      "resolution": null,
      "resolution_parse_status": null,
      "resolution_waiver": false,
      "head_sha_at_request": "1387cca3c514f33874f2bba9339c027896c5d344",
      "head_sha_after_round": "1387cca3c514f33874f2bba9339c027896c5d344",
      "worktree_dirty_at_request": true,
      "verdict": null,
      "verdict_valid": false,
      "findings_count": 0,
      "blocking_findings_count": 0,
      "base_ref": null,
      "base_ref_source": null,
      "diff_included": false
    },
    {
      "round": 2,
      "reviewers": [
        {
          "role": "primary",
          "sweep_group": null,
          "parent_round": 2,
          "request": "r2-2026-05-21T0510-request.md",
          "response": "r2-2026-05-21T0510-response.md",
          "verdict": "revise",
          "verdict_valid": true,
          "returncode": 0,
          "status": "ok",
          "provider": "codex",
          "caller_provider": "claude",
          "model": null,
          "sandbox": {
            "repo_root": "/home/simon/Dev/sigreer/skills/superstar/.claude/worktrees/x16-shim-version-stamping",
            "scratch_dir": "/tmp/superstar-reviewer-x16-shim-version-stamping-X16-post-slice-r2-primary-atr2lwsa",
            "response_dir": "docs/reviewer/x16-shim-version-stamping-X16-post-slice/.reviewer-output/r2-primary",
            "mode": "workspace-write-with-read-access"
          },
          "started_at": "2026-05-21T04:10:24.884Z",
          "finished_at": "2026-05-21T04:13:23.208Z",
          "duration_ms": 178323,
          "estimated_usage": {
            "formula": "ceil(chars / 4)",
            "prompt_chars": 12013,
            "response_chars": 3260,
            "estimated_input_tokens": 3004,
            "estimated_output_tokens": 815,
            "estimated_total_tokens": 3819
          },
          "exact_usage": null,
          "usage_capture_status": "estimated_only",
          "usage_capture_error": null
        }
      ],
      "status": "ok",
      "returncode": 0,
      "started_at": "2026-05-21T04:10:24.884Z",
      "finished_at": "2026-05-21T04:13:23.208Z",
      "duration_ms": 178323,
      "provider": "codex",
      "caller_provider": "claude",
      "model": null,
      "estimated_usage": {
        "formula": "ceil(chars / 4)",
        "prompt_chars": 12013,
        "response_chars": 3260,
        "estimated_input_tokens": 3004,
        "estimated_output_tokens": 815,
        "estimated_total_tokens": 3819
      },
      "exact_usage": null,
      "usage_capture_status": "estimated_only",
      "usage_capture_error": null,
      "merged_verdict": "revise",
      "merged_findings": null,
      "request": "r2-2026-05-21T0510-request.md",
      "response": "r2-2026-05-21T0510-response.md",
      "resolution": null,
      "resolution_parse_status": null,
      "resolution_waiver": false,
      "head_sha_at_request": "1387cca3c514f33874f2bba9339c027896c5d344",
      "head_sha_after_round": "1387cca3c514f33874f2bba9339c027896c5d344",
      "worktree_dirty_at_request": true,
      "verdict": "revise",
      "verdict_valid": true,
      "findings_count": 3,
      "blocking_findings_count": 2,
      "base_ref": "1387cca3c514f33874f2bba9339c027896c5d344",
      "base_ref_source": "auto",
      "diff_included": true
    }
  ],
  "sweep_checkpoints": {
    "first-round": "completed",
    "final-ready": "pending"
  }
}

```

### docs/reviewer/x16-shim-version-stamping-X16-post-slice/r1-2026-05-21T0510-primary-request.md

```
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
/home/simon/Dev/sigreer/skills/superstar/.claude/worktrees/x16-shim-version-stamping

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-21-X16-shim-version-stamping.md

Additional context files:
- docs/specs/2026-05-21-X16-shim-version-stamping-design.md
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

### docs/plans/2026-05-21-X16-shim-version-stamping.md

    1	# Shim Version Stamping Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Stamp every Superstar-installed shim and hook with a version header, refuse to run when the source's `VERSION` file has drifted, and surface drift through a one-shot `scripts/deploy.sh --check` diagnostic. Eliminate the stale-shim class of bugs.
    6	
    7	**Architecture:** A new top-level `VERSION` file is the single source of truth, read at runtime by every shim. Each installer embeds a shared bash version-check fragment plus a stamped header. The Python `tasktool` entrypoint adds a startup handshake for the repo-local `pre-commit` hook (the one file that must be a content copy). `scripts/deploy.sh` ties publish + re-installation together and provides a `--check` diagnostic mode with a strict exit-status lattice. The `reviewer-agent` global file is converted from content copy to redirect shim, eliminating its content-drift class entirely.
    8	
    9	**Tech Stack:** bash (installers, shim runtime, deploy.sh, publish scripts), Python 3 (tasktool entrypoint + new test cases), pytest (test harness), `jq` (already a project dependency for JSON manipulation in bump-version.sh).
   10	
   11	**Work ID:** X16 (cross-cutting). No slice schedule — single linear delivery.
   12	
   13	---
   14	
   15	## File Structure
   16	
   17	**New files:**
   18	- `VERSION` (repo root) — single-line plain text, e.g. `6.3.2\n`. Single source of truth at runtime.
   19	- `plugins/superstar/VERSION` — relative symlink to `../../VERSION`. Flattens to a real file under `<cache>/<version>/VERSION` and `<cache>/current/VERSION` via `rsync -aL`.
   20	- `scripts/lib/shim-version-check.sh` — shared bash fragment defining `__superstar_check_version`, embedded into every generated shim by the installers.
   21	- `scripts/lib/publish-common.sh` — shared publish logic (rsync, hooks.json rewriting, manifest + VERSION verification) sourced by both `publish-to-local-codex.sh` and `publish-to-local-claude.sh`.
   22	- `scripts/deploy.sh` — top-level deploy + diagnostics entry point.
   23	- `skills/project-setup/install-reviewer-agent.sh` — new installer that emits a thin redirect shim for `~/.local/bin/reviewer-agent`.
   24	- `scripts/tests/__init__.py` and `scripts/tests/test_shim_stamping.py` — pytest module for cross-cutting shim/stamping tests.
   25	
   26	**Modified files:**
   27	- `.version-bump.json` — add `{path: "VERSION", format: "plain"}` and migrate the existing entries to the new format-aware shape.
   28	- `scripts/bump-version.sh` — add `read_plain_field` / `write_plain_field` helpers and a `format` column dispatch in `declared_files()`.
   29	- `skills/external-review/install.sh` — embed stamp header + shim-version-check fragment into the generated shim.
   30	- `skills/external-review/tests/test_external_reviewer_installer.py` — assert stamp keys + fragment present.
   31	- `scripts/publish-to-local-codex.sh` — convert to thin wrapper over `publish-common.sh`. Preserve the existing post-publish `external-reviewer/install.sh` re-run.
   32	- `scripts/publish-to-local-claude.sh` — same treatment.
   33	- `tools/tasktool/install.sh` — add stamp header + version-check fragment to the generated `~/.local/bin/tasktool` shim. Hook installer accepts legacy + new markers.
   34	- `tools/tasktool/templates/pre-commit-tasktool` — header gains stamped key/value lines while preserving the legacy `tasktool-pre-commit-hook v1` magic comment for backward recognition.
   35	- `tools/tasktool/cli.py` — add startup pre-commit-hook version handshake.
   36	- `tools/tasktool/tests/test_pre_commit_hook.py` — add cases for legacy-marker migration, header stamping, idempotency.
   37	- `skills/project-setup/SKILL.md` — delete row 7b and surrounding compat-shim language.
   38	- `tests/codex-plugin-sync/test-publish-to-local-codex.sh` — assert `current/VERSION` materialised; keep shim source-path assertion.
   39	- `tests/claude-code/test-publish-to-local-claude.sh` — same.
   40	
   41	**Deleted files:**
   42	- `skills/project-setup/scripts/external-reviewer-shim.py`
   43	- `skills/external-review/tests/test_external_reviewer_compat_shim.py`
   44	
   45	---
   46	
   47	## Task 1: VERSION file + bump-version plain format support
   48	
   49	**Files:**
   50	- Create: `VERSION` at repo root
   51	- Create: `plugins/superstar/VERSION` (symlink)
   52	- Modify: `.version-bump.json`
   53	- Modify: `scripts/bump-version.sh`
   54	
   55	- [ ] **Step 1.1: Capture current version from declared files**
   56	
   57	Read the current version (the value that bump-version.sh would consider canonical):
   58	
   59	```bash
   60	jq -r '.version' package.json
   61	```
   62	
   63	Expected: `6.3.2` (or whatever the current `package.json` version is — note it; subsequent steps reference it as `$CURRENT_VERSION`).
   64	
   65	- [ ] **Step 1.2: Create the repo-root `VERSION` file**
   66	
   67	```bash
   68	echo "6.3.2" > VERSION
   69	cat VERSION
   70	```
   71	
   72	Expected: single line `6.3.2` with trailing newline. Adjust `6.3.2` to match `$CURRENT_VERSION` from Step 1.1.
   73	
   74	- [ ] **Step 1.3: Add the plugin-payload `VERSION` symlink**
   75	
   76	```bash
   77	ln -s ../../VERSION plugins/superstar/VERSION
   78	ls -la plugins/superstar/VERSION
   79	cat plugins/superstar/VERSION
   80	```
   81	
   82	Expected: `lrwxrwxrwx ... plugins/superstar/VERSION -> ../../VERSION` and the contents match `6.3.2`. Symlink is **relative** so it stays valid inside the published cache trees after `rsync -aL` flattens it.
   83	
   84	- [ ] **Step 1.4: Write the failing bump-version plain-format test (new test file)**
   85	
   86	Create `scripts/tests/__init__.py` (empty) and `scripts/tests/test_bump_version_plain_format.py`:
   87	
   88	```python
   89	"""Tests for the plain-format support added to scripts/bump-version.sh."""
   90	from __future__ import annotations
   91	
   92	import json
   93	import subprocess
   94	from pathlib import Path
   95	
   96	import pytest
   97	
   98	REPO_ROOT = Path(__file__).resolve().parents[2]
   99	REAL_SCRIPT = REPO_ROOT / "scripts" / "bump-version.sh"
  100	
  101	
  102	def _seed_repo(tmp_path: Path, version: str) -> Path:
  103	    """Build an isolated fake repo so the script's own REPO_ROOT resolution
  104	    (`cd $SCRIPT_DIR/.. && pwd`) lands inside tmp_path and cannot mutate the
  105	    real checkout."""
  106	    (tmp_path / "package.json").write_text(json.dumps({"version": version}, indent=2) + "\n")
  107	    (tmp_path / "VERSION").write_text(version + "\n")
  108	    config = {
  109	        "files": [
  110	            {"path": "package.json", "field": "version"},
  111	            {"path": "VERSION", "format": "plain"},
  112	        ],
  113	        "audit": {"exclude": []},
  114	    }
  115	    (tmp_path / ".version-bump.json").write_text(json.dumps(config, indent=2) + "\n")
  116	    (tmp_path / "scripts").mkdir(exist_ok=True)
  117	    # Symlink the real bump-version.sh into the fake repo's scripts dir. We
  118	    # MUST invoke this symlinked path (not REAL_SCRIPT) so the script's
  119	    # `dirname "$0"` -> `cd $SCRIPT_DIR/..` resolves to tmp_path. Invoking
  120	    # REAL_SCRIPT directly would resolve to the real superstar checkout and
  121	    # mutate its declared files.
  122	    fake_script = tmp_path / "scripts" / "bump-version.sh"
  123	    fake_script.symlink_to(REAL_SCRIPT)
  124	    return tmp_path
  125	
  126	
  127	def _run(script_args: list[str], repo: Path) -> subprocess.CompletedProcess:
  128	    """Invoke the symlinked bump-version.sh inside `repo` so REPO_ROOT
  129	    resolution stays inside the fake repo."""
  130	    fake_script = repo / "scripts" / "bump-version.sh"
  131	    assert fake_script.exists(), "fake script symlink missing — call _seed_repo first"
  132	    return subprocess.run(
  133	        ["bash", str(fake_script), *script_args],
  134	        cwd=repo,
  135	        capture_output=True,
  136	        text=True,
  137	        check=False,
  138	    )
  139	
  140	
  141	def test_check_lists_plain_version(tmp_path: Path) -> None:
  142	    repo = _seed_repo(tmp_path, "1.2.3")
  143	    result = _run(["--check"], repo)
[truncated: 872 additional lines]
```

### docs/reviewer/x16-shim-version-stamping-X16-post-slice/r1-2026-05-21T0510-primary-response.md

```
# Review — 2026-05-21-X16-shim-version-stamping.md (post-slice, round 1)

- Target: `docs/plans/2026-05-21-X16-shim-version-stamping.md`
- Request: `docs/reviewer/x16-shim-version-stamping-X16-post-slice/r1-2026-05-21T0510-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `failed (1)`

---

_Reviewer process failed; no stdout persisted._

---

## Reviewer stderr (tail, sanitised)

```text
ERROR: reviewer-agent shim is 6.4.1 but Superstar source is 6.5.0
Re-run: bash /home/simon/Dev/sigreer/skills/superstar/.claude/worktrees/x16-shim-version-stamping/skills/project-setup/install-reviewer-agent.sh
```

```

### docs/reviewer/x16-shim-version-stamping-X16-post-slice/r1-2026-05-21T0510-sweep1-request.md

```
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
/home/simon/Dev/sigreer/skills/superstar/.claude/worktrees/x16-shim-version-stamping

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-21-X16-shim-version-stamping.md

Additional context files:
- docs/specs/2026-05-21-X16-shim-version-stamping-design.md
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

### docs/plans/2026-05-21-X16-shim-version-stamping.md

    1	# Shim Version Stamping Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Stamp every Superstar-installed shim and hook with a version header, refuse to run when the source's `VERSION` file has drifted, and surface drift through a one-shot `scripts/deploy.sh --check` diagnostic. Eliminate the stale-shim class of bugs.
    6	
    7	**Architecture:** A new top-level `VERSION` file is the single source of truth, read at runtime by every shim. Each installer embeds a shared bash version-check fragment plus a stamped header. The Python `tasktool` entrypoint adds a startup handshake for the repo-local `pre-commit` hook (the one file that must be a content copy). `scripts/deploy.sh` ties publish + re-installation together and provides a `--check` diagnostic mode with a strict exit-status lattice. The `reviewer-agent` global file is converted from content copy to redirect shim, eliminating its content-drift class entirely.
    8	
    9	**Tech Stack:** bash (installers, shim runtime, deploy.sh, publish scripts), Python 3 (tasktool entrypoint + new test cases), pytest (test harness), `jq` (already a project dependency for JSON manipulation in bump-version.sh).
   10	
   11	**Work ID:** X16 (cross-cutting). No slice schedule — single linear delivery.
   12	
   13	---
   14	
   15	## File Structure
   16	
   17	**New files:**
   18	- `VERSION` (repo root) — single-line plain text, e.g. `6.3.2\n`. Single source of truth at runtime.
   19	- `plugins/superstar/VERSION` — relative symlink to `../../VERSION`. Flattens to a real file under `<cache>/<version>/VERSION` and `<cache>/current/VERSION` via `rsync -aL`.
   20	- `scripts/lib/shim-version-check.sh` — shared bash fragment defining `__superstar_check_version`, embedded into every generated shim by the installers.
   21	- `scripts/lib/publish-common.sh` — shared publish logic (rsync, hooks.json rewriting, manifest + VERSION verification) sourced by both `publish-to-local-codex.sh` and `publish-to-local-claude.sh`.
   22	- `scripts/deploy.sh` — top-level deploy + diagnostics entry point.
   23	- `skills/project-setup/install-reviewer-agent.sh` — new installer that emits a thin redirect shim for `~/.local/bin/reviewer-agent`.
   24	- `scripts/tests/__init__.py` and `scripts/tests/test_shim_stamping.py` — pytest module for cross-cutting shim/stamping tests.
   25	
   26	**Modified files:**
   27	- `.version-bump.json` — add `{path: "VERSION", format: "plain"}` and migrate the existing entries to the new format-aware shape.
   28	- `scripts/bump-version.sh` — add `read_plain_field` / `write_plain_field` helpers and a `format` column dispatch in `declared_files()`.
   29	- `skills/external-review/install.sh` — embed stamp header + shim-version-check fragment into the generated shim.
   30	- `skills/external-review/tests/test_external_reviewer_installer.py` — assert stamp keys + fragment present.
   31	- `scripts/publish-to-local-codex.sh` — convert to thin wrapper over `publish-common.sh`. Preserve the existing post-publish `external-reviewer/install.sh` re-run.
   32	- `scripts/publish-to-local-claude.sh` — same treatment.
   33	- `tools/tasktool/install.sh` — add stamp header + version-check fragment to the generated `~/.local/bin/tasktool` shim. Hook installer accepts legacy + new markers.
   34	- `tools/tasktool/templates/pre-commit-tasktool` — header gains stamped key/value lines while preserving the legacy `tasktool-pre-commit-hook v1` magic comment for backward recognition.
   35	- `tools/tasktool/cli.py` — add startup pre-commit-hook version handshake.
   36	- `tools/tasktool/tests/test_pre_commit_hook.py` — add cases for legacy-marker migration, header stamping, idempotency.
   37	- `skills/project-setup/SKILL.md` — delete row 7b and surrounding compat-shim language.
   38	- `tests/codex-plugin-sync/test-publish-to-local-codex.sh` — assert `current/VERSION` materialised; keep shim source-path assertion.
   39	- `tests/claude-code/test-publish-to-local-claude.sh` — same.
   40	
   41	**Deleted files:**
   42	- `skills/project-setup/scripts/external-reviewer-shim.py`
   43	- `skills/external-review/tests/test_external_reviewer_compat_shim.py`
   44	
   45	---
   46	
   47	## Task 1: VERSION file + bump-version plain format support
   48	
   49	**Files:**
   50	- Create: `VERSION` at repo root
   51	- Create: `plugins/superstar/VERSION` (symlink)
   52	- Modify: `.version-bump.json`
   53	- Modify: `scripts/bump-version.sh`
   54	
   55	- [ ] **Step 1.1: Capture current version from declared files**
   56	
   57	Read the current version (the value that bump-version.sh would consider canonical):
   58	
   59	```bash
   60	jq -r '.version' package.json
   61	```
   62	
   63	Expected: `6.3.2` (or whatever the current `package.json` version is — note it; subsequent steps reference it as `$CURRENT_VERSION`).
   64	
   65	- [ ] **Step 1.2: Create the repo-root `VERSION` file**
   66	
   67	```bash
   68	echo "6.3.2" > VERSION
   69	cat VERSION
   70	```
   71	
   72	Expected: single line `6.3.2` with trailing newline. Adjust `6.3.2` to match `$CURRENT_VERSION` from Step 1.1.
   73	
   74	- [ ] **Step 1.3: Add the plugin-payload `VERSION` symlink**
   75	
   76	```bash
   77	ln -s ../../VERSION plugins/superstar/VERSION
   78	ls -la plugins/superstar/VERSION
   79	cat plugins/superstar/VERSION
   80	```
   81	
   82	Expected: `lrwxrwxrwx ... plugins/superstar/VERSION -> ../../VERSION` and the contents match `6.3.2`. Symlink is **relative** so it stays valid inside the published cache trees after `rsync -aL` flattens it.
   83	
   84	- [ ] **Step 1.4: Write the failing bump-version plain-format test (new test file)**
   85	
   86	Create `scripts/tests/__init__.py` (empty) and `scripts/tests/test_bump_version_plain_format.py`:
   87	
   88	```python
   89	"""Tests for the plain-format support added to scripts/bump-version.sh."""
   90	from __future__ import annotations
   91	
   92	import json
   93	import subprocess
   94	from pathlib import Path
   95	
   96	import pytest
   97	
   98	REPO_ROOT = Path(__file__).resolve().parents[2]
   99	REAL_SCRIPT = REPO_ROOT / "scripts" / "bump-version.sh"
  100	
  101	
  102	def _seed_repo(tmp_path: Path, version: str) -> Path:
  103	    """Build an isolated fake repo so the script's own REPO_ROOT resolution
  104	    (`cd $SCRIPT_DIR/.. && pwd`) lands inside tmp_path and cannot mutate the
  105	    real checkout."""
  106	    (tmp_path / "package.json").write_text(json.dumps({"version": version}, indent=2) + "\n")
  107	    (tmp_path / "VERSION").write_text(version + "\n")
  108	    config = {
  109	        "files": [
  110	            {"path": "package.json", "field": "version"},
  111	            {"path": "VERSION", "format": "plain"},
  112	        ],
  113	        "audit": {"exclude": []},
  114	    }
  115	    (tmp_path / ".version-bump.json").write_text(json.dumps(config, indent=2) + "\n")
  116	    (tmp_path / "scripts").mkdir(exist_ok=True)
  117	    # Symlink the real bump-version.sh into the fake repo's scripts dir. We
  118	    # MUST invoke this symlinked path (not REAL_SCRIPT) so the script's
  119	    # `dirname "$0"` -> `cd $SCRIPT_DIR/..` resolves to tmp_path. Invoking
  120	    # REAL_SCRIPT directly would resolve to the real superstar checkout and
  121	    # mutate its declared files.
  122	    fake_script = tmp_path / "scripts" / "bump-version.sh"
  123	    fake_script.symlink_to(REAL_SCRIPT)
  124	    return tmp_path
  125	
  126	
  127	def _run(script_args: list[str], repo: Path) -> subprocess.CompletedProcess:
  128	    """Invoke the symlinked bump-version.sh inside `repo` so REPO_ROOT
  129	    resolution stays inside the fake repo."""
  130	    fake_script = repo / "scripts" / "bump-version.sh"
  131	    assert fake_script.exists(), "fake script symlink missing — call _seed_repo first"
  132	    return subprocess.run(
  133	        ["bash", str(fake_script), *script_args],
  134	        cwd=repo,
  135	        capture_output=True,
  136	        text=True,
  137	        check=False,
  138	    )
  139	
  140	
  141	def test_check_lists_plain_version(tmp_path: Path) -> None:
  142	    repo = _seed_repo(tmp_path, "1.2.3")
  143	    result = _run(["--check"], repo)
[truncated: 872 additional lines]
```

### docs/reviewer/x16-shim-version-stamping-X16-post-slice/r1-2026-05-21T0510-sweep1-response.md

```
# Review — 2026-05-21-X16-shim-version-stamping.md (post-slice, round 1)

- Target: `docs/plans/2026-05-21-X16-shim-version-stamping.md`
- Request: `docs/reviewer/x16-shim-version-stamping-X16-post-slice/r1-2026-05-21T0510-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `failed (1)`

---

_Reviewer process failed; no stdout persisted._

---

## Reviewer stderr (tail, sanitised)

```text
ERROR: reviewer-agent shim is 6.4.1 but Superstar source is 6.5.0
Re-run: bash /home/simon/Dev/sigreer/skills/superstar/.claude/worktrees/x16-shim-version-stamping/skills/project-setup/install-reviewer-agent.sh
```

```

### docs/reviewer/x16-shim-version-stamping-X16-post-slice/r2-2026-05-21T0510-request.md

```
<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 2 of x16-shim-version-stamping-X16-post-slice.

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
| 1 | None | 0 | 0 |

## Prior-round findings

Source: no successful prior round; no prior review available


Note: round 1 was a process failure, rate-limited, or pre-S1 entry; skipped.


## Resolution report for prior round

MISSING — please verify whether changes occurred.

## Changes since prior round

Worktree status: dirty

### git diff base..HEAD



### git diff HEAD (uncommitted)



### Untracked files

- docs/reviewer/x16-shim-version-stamping-X16-post-slice/ (omitted: binary or unreadable)


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
/home/simon/Dev/sigreer/skills/superstar/.claude/worktrees/x16-shim-version-stamping

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-21-X16-shim-version-stamping.md

Additional context files:
- docs/specs/2026-05-21-X16-shim-version-stamping-design.md
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

### docs/plans/2026-05-21-X16-shim-version-stamping.md

    1	# Shim Version Stamping Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Stamp every Superstar-installed shim and hook with a version header, refuse to run when the source's `VERSION` file has drifted, and surface drift through a one-shot `scripts/deploy.sh --check` diagnostic. Eliminate the stale-shim class of bugs.
    6	
    7	**Architecture:** A new top-level `VERSION` file is the single source of truth, read at runtime by every shim. Each installer embeds a shared bash version-check fragment plus a stamped header. The Python `tasktool` entrypoint adds a startup handshake for the repo-local `pre-commit` hook (the one file that must be a content copy). `scripts/deploy.sh` ties publish + re-installation together and provides a `--check` diagnostic mode with a strict exit-status lattice. The `reviewer-agent` global file is converted from content copy to redirect shim, eliminating its content-drift class entirely.
    8	
    9	**Tech Stack:** bash (installers, shim runtime, deploy.sh, publish scripts), Python 3 (tasktool entrypoint + new test cases), pytest (test harness), `jq` (already a project dependency for JSON manipulation in bump-version.sh).
   10	
   11	**Work ID:** X16 (cross-cutting). No slice schedule — single linear delivery.
   12	
   13	---
   14	
   15	## File Structure
   16	
   17	**New files:**
   18	- `VERSION` (repo root) — single-line plain text, e.g. `6.3.2\n`. Single source of truth at runtime.
   19	- `plugins/superstar/VERSION` — relative symlink to `../../VERSION`. Flattens to a real file under `<cache>/<version>/VERSION` and `<cache>/current/VERSION` via `rsync -aL`.
   20	- `scripts/lib/shim-version-check.sh` — shared bash fragment defining `__superstar_check_version`, embedded into every generated shim by the installers.
   21	- `scripts/lib/publish-common.sh` — shared publish logic (rsync, hooks.json rewriting, manifest + VERSION verification) sourced by both `publish-to-local-codex.sh` and `publish-to-local-claude.sh`.
   22	- `scripts/deploy.sh` — top-level deploy + diagnostics entry point.
   23	- `skills/project-setup/install-reviewer-agent.sh` — new installer that emits a thin redirect shim for `~/.local/bin/reviewer-agent`.
   24	- `scripts/tests/__init__.py` and `scripts/tests/test_shim_stamping.py` — pytest module for cross-cutting shim/stamping tests.
   25	
   26	**Modified files:**
   27	- `.version-bump.json` — add `{path: "VERSION", format: "plain"}` and migrate the existing entries to the new format-aware shape.
   28	- `scripts/bump-version.sh` — add `read_plain_field` / `write_plain_field` helpers and a `format` column dispatch in `declared_files()`.
   29	- `skills/external-review/install.sh` — embed stamp header + shim-version-check fragment into the generated shim.
   30	- `skills/external-review/tests/test_external_reviewer_installer.py` — assert stamp keys + fragment present.
   31	- `scripts/publish-to-local-codex.sh` — convert to thin wrapper over `publish-common.sh`. Preserve the existing post-publish `external-reviewer/install.sh` re-run.
   32	- `scripts/publish-to-local-claude.sh` — same treatment.
   33	- `tools/tasktool/install.sh` — add stamp header + version-check fragment to the generated `~/.local/bin/tasktool` shim. Hook installer accepts legacy + new markers.
   34	- `tools/tasktool/templates/pre-commit-tasktool` — header gains stamped key/value lines while preserving the legacy `tasktool-pre-commit-hook v1` magic comment for backward recognition.
   35	- `tools/tasktool/cli.py` — add startup pre-commit-hook version handshake.
   36	- `tools/tasktool/tests/test_pre_commit_hook.py` — add cases for legacy-marker migration, header stamping, idempotency.
   37	- `skills/project-setup/SKILL.md` — delete row 7b and surrounding compat-shim language.
   38	- `tests/codex-plugin-sync/test-publish-to-local-codex.sh` — assert `current/VERSION` materialised; keep shim source-path assertion.
   39	- `tests/claude-code/test-publish-to-local-claude.sh` — same.
   40	
   41	**Deleted files:**
   42	- `skills/project-setup/scripts/external-reviewer-shim.py`
   43	- `skills/external-review/tests/test_external_reviewer_compat_shim.py`
   44	
   45	---
   46	
   47	## Task 1: VERSION file + bump-version plain format support
   48	
   49	**Files:**
   50	- Create: `VERSION` at repo root
   51	- Create: `plugins/superstar/VERSION` (symlink)
   52	- Modify: `.version-bump.json`
   53	- Modify: `scripts/bump-version.sh`
   54	
   55	- [ ] **Step 1.1: Capture current version from declared files**
   56	
   57	Read the current version (the value that bump-version.sh would consider canonical):
   58	
   59	```bash
   60	jq -r '.version' package.json
   61	```
   62	
   63	Expected: `6.3.2` (or whatever the current `package.json` version is — note it; subsequent steps reference it as `$CURRENT_VERSION`).
   64	
   65	- [ ] **Step 1.2: Create the repo-root `VERSION` file**
   66	
   67	```bash
   68	echo "6.3.2" > VERSION
   69	cat VERSION
   70	```
   71	
   72	Expected: single line `6.3.2` with trailing newline. Adjust `6.3.2` to match `$CURRENT_VERSION` from Step 1.1.
   73	
   74	- [ ] **Step 1.3: Add the plugin-payload `VERSION` symlink**
   75	
   76	```bash
   77	ln -s ../../VERSION plugins/superstar/VERSION
   78	ls -la plugins/superstar/VERSION
   79	cat plugins/superstar/VERSION
   80	```
   81	
   82	Expected: `lrwxrwxrwx ... plugins/superstar/VERSION -> ../../VERSION` and the contents match `6.3.2`. Symlink is **relative** so it stays valid inside the published cache trees after `rsync -aL` flattens it.
   83	
   84	- [ ] **Step 1.4: Write the failing bump-version plain-format test (new test file)**
   85	
   86	Create `scripts/tests/__init__.py` (empty) and `scripts/tests/test_bump_version_plain_format.py`:
   87	
   88	```python
   89	"""Tests for the plain-format support added to scripts/bump-version.sh."""
   90	from __future__ import annotations
   91	
   92	import json
   93	import subprocess
   94	from pathlib import Path
   95	
[truncated: 59 additional lines]
```

### docs/reviewer/x16-shim-version-stamping-X16-post-slice/r2-2026-05-21T0510-response.md

```
# Review — 2026-05-21-X16-shim-version-stamping.md (post-slice, round 2)

- Target: `docs/plans/2026-05-21-X16-shim-version-stamping.md`
- Request: `docs/reviewer/x16-shim-version-stamping-X16-post-slice/r2-2026-05-21T0510-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: blocking — X16 is not closed in the canonical tracker. `docs/tasklist.json` still has `X16` as `"status": "ready"`, with `"started": null`, `"closed": null`, empty notes, and only the spec ref registered at `docs/tasklist.json:226`. This contradicts the plan’s closeout requirement to run `tasktool close X16` at `docs/plans/2026-05-21-X16-shim-version-stamping.md:2359` and leaves the post-slice gate unsatisfied.

F2 — Severity: blocking — `deploy.sh --check` does not inspect the pre-commit hook, despite the spec requiring shim/hook header parsing and hook status in the diagnostic. The acceptance criterion says `deploy.sh --check` must parse shim/hook headers and apply the status lattice at `docs/specs/2026-05-21-X16-shim-version-stamping-design.md:412`, and the expected output includes “Pre-commit hook (current repo)” at `docs/specs/2026-05-21-X16-shim-version-stamping-design.md:341`. The implementation only checks three global shims and plugin caches at `scripts/deploy.sh:177` and `scripts/deploy.sh:199`, so a stale hook can be missed while `--check` exits 0.

F3 — Severity: important — The tasktool hook handshake misses linked worktrees. `check_pre_commit_hook()` locates the hook as `repo_top / ".git" / "hooks" / "pre-commit"` at `tools/tasktool/hook_handshake.py:56`, but in a linked worktree `.git` is a file and the actual hook path must come from `git rev-parse --git-path hooks/pre-commit`. I reproduced this in `/tmp`: a stale stamped hook in the real `git-path` hook location returned `message=None`. The existing tests only write hooks under `repo/.git/hooks` (`tools/tasktool/tests/test_hook_handshake.py:19`), so this common Superstar workflow is uncovered.

2. Open questions / assumptions

I assume X16 is being reviewed as a completion gate, not as a WIP checkpoint. If that is wrong, the task tracker still needs to say so explicitly because the current tracker state presents the work as not started.

3. Suggested document edits

Add a resolution note or closeout evidence that includes the post-slice reviewer chain, `tasktool close X16`, and the final verification commands. If `deploy.sh --check` intentionally excludes the hook, the spec and acceptance criteria must be changed; otherwise implement the hook row.

4. Verification gaps / commands that should be run

Run or add coverage for:

```bash
python3 -m pytest tools/tasktool/tests/test_hook_handshake.py -v
python3 -m pytest scripts/tests/test_deploy_check.py -v
bash scripts/deploy.sh --check
tools/tasktool/tasktool show X16
tools/tasktool/tasktool close X16 --reviewer-chain docs/reviewer/x16-shim-version-stamping-X16-post-slice
```

Fresh checks I ran: `tasktool validate --strict-format` passed, `tasktool artifact status X16 --strict` passed, and `bash scripts/deploy.sh --check` exited 0 but showed no pre-commit hook section.

Overall verdict: revise

```



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
/home/simon/Dev/sigreer/skills/superstar/.claude/worktrees/x16-shim-version-stamping

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-21-X16-shim-version-stamping.md

Additional context files:
- docs/specs/2026-05-21-X16-shim-version-stamping-design.md
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

### docs/plans/2026-05-21-X16-shim-version-stamping.md

    1	# Shim Version Stamping Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Stamp every Superstar-installed shim and hook with a version header, refuse to run when the source's `VERSION` file has drifted, and surface drift through a one-shot `scripts/deploy.sh --check` diagnostic. Eliminate the stale-shim class of bugs.
    6	
    7	**Architecture:** A new top-level `VERSION` file is the single source of truth, read at runtime by every shim. Each installer embeds a shared bash version-check fragment plus a stamped header. The Python `tasktool` entrypoint adds a startup handshake for the repo-local `pre-commit` hook (the one file that must be a content copy). `scripts/deploy.sh` ties publish + re-installation together and provides a `--check` diagnostic mode with a strict exit-status lattice. The `reviewer-agent` global file is converted from content copy to redirect shim, eliminating its content-drift class entirely.
    8	
    9	**Tech Stack:** bash (installers, shim runtime, deploy.sh, publish scripts), Python 3 (tasktool entrypoint + new test cases), pytest (test harness), `jq` (already a project dependency for JSON manipulation in bump-version.sh).
   10	
   11	**Work ID:** X16 (cross-cutting). No slice schedule — single linear delivery.
   12	
   13	---
   14	
   15	## File Structure
   16	
   17	**New files:**
   18	- `VERSION` (repo root) — single-line plain text, e.g. `6.3.2\n`. Single source of truth at runtime.
   19	- `plugins/superstar/VERSION` — relative symlink to `../../VERSION`. Flattens to a real file under `<cache>/<version>/VERSION` and `<cache>/current/VERSION` via `rsync -aL`.
   20	- `scripts/lib/shim-version-check.sh` — shared bash fragment defining `__superstar_check_version`, embedded into every generated shim by the installers.
   21	- `scripts/lib/publish-common.sh` — shared publish logic (rsync, hooks.json rewriting, manifest + VERSION verification) sourced by both `publish-to-local-codex.sh` and `publish-to-local-claude.sh`.
   22	- `scripts/deploy.sh` — top-level deploy + diagnostics entry point.
   23	- `skills/project-setup/install-reviewer-agent.sh` — new installer that emits a thin redirect shim for `~/.local/bin/reviewer-agent`.
   24	- `scripts/tests/__init__.py` and `scripts/tests/test_shim_stamping.py` — pytest module for cross-cutting shim/stamping tests.
   25	
   26	**Modified files:**
   27	- `.version-bump.json` — add `{path: "VERSION", format: "plain"}` and migrate the existing entries to the new format-aware shape.
   28	- `scripts/bump-version.sh` — add `read_plain_field` / `write_plain_field` helpers and a `format` column dispatch in `declared_files()`.
   29	- `skills/external-review/install.sh` — embed stamp header + shim-version-check fragment into the generated shim.
   30	- `skills/external-review/tests/test_external_reviewer_installer.py` — assert stamp keys + fragment present.
   31	- `scripts/publish-to-local-codex.sh` — convert to thin wrapper over `publish-common.sh`. Preserve the existing post-publish `external-reviewer/install.sh` re-run.
   32	- `scripts/publish-to-local-claude.sh` — same treatment.
   33	- `tools/tasktool/install.sh` — add stamp header + version-check fragment to the generated `~/.local/bin/tasktool` shim. Hook installer accepts legacy + new markers.
   34	- `tools/tasktool/templates/pre-commit-tasktool` — header gains stamped key/value lines while preserving the legacy `tasktool-pre-commit-hook v1` magic comment for backward recognition.
   35	- `tools/tasktool/cli.py` — add startup pre-commit-hook version handshake.
   36	- `tools/tasktool/tests/test_pre_commit_hook.py` — add cases for legacy-marker migration, header stamping, idempotency.
   37	- `skills/project-setup/SKILL.md` — delete row 7b and surrounding compat-shim language.
   38	- `tests/codex-plugin-sync/test-publish-to-local-codex.sh` — assert `current/VERSION` materialised; keep shim source-path assertion.
   39	- `tests/claude-code/test-publish-to-local-claude.sh` — same.
   40	
   41	**Deleted files:**
   42	- `skills/project-setup/scripts/external-reviewer-shim.py`
   43	- `skills/external-review/tests/test_external_reviewer_compat_shim.py`
   44	
   45	---
   46	
   47	## Task 1: VERSION file + bump-version plain format support
   48	
   49	**Files:**
   50	- Create: `VERSION` at repo root
   51	- Create: `plugins/superstar/VERSION` (symlink)
   52	- Modify: `.version-bump.json`
   53	- Modify: `scripts/bump-version.sh`
   54	
   55	- [ ] **Step 1.1: Capture current version from declared files**
   56	
   57	Read the current version (the value that bump-version.sh would consider canonical):
   58	
   59	```bash
   60	jq -r '.version' package.json
   61	```
   62	
   63	Expected: `6.3.2` (or whatever the current `package.json` version is — note it; subsequent steps reference it as `$CURRENT_VERSION`).
   64	
   65	- [ ] **Step 1.2: Create the repo-root `VERSION` file**
   66	
   67	```bash
   68	echo "6.3.2" > VERSION
   69	cat VERSION
   70	```
   71	
   72	Expected: single line `6.3.2` with trailing newline. Adjust `6.3.2` to match `$CURRENT_VERSION` from Step 1.1.
   73	
   74	- [ ] **Step 1.3: Add the plugin-payload `VERSION` symlink**
   75	
   76	```bash
   77	ln -s ../../VERSION plugins/superstar/VERSION
   78	ls -la plugins/superstar/VERSION
   79	cat plugins/superstar/VERSION
   80	```
   81	
   82	Expected: `lrwxrwxrwx ... plugins/superstar/VERSION -> ../../VERSION` and the contents match `6.3.2`. Symlink is **relative** so it stays valid inside the published cache trees after `rsync -aL` flattens it.
   83	
   84	- [ ] **Step 1.4: Write the failing bump-version plain-format test (new test file)**
   85	
   86	Create `scripts/tests/__init__.py` (empty) and `scripts/tests/test_bump_version_plain_format.py`:
   87	
   88	```python
   89	"""Tests for the plain-format support added to scripts/bump-version.sh."""
   90	from __future__ import annotations
   91	
   92	import json
   93	import subprocess
   94	from pathlib import Path
   95	
   96	import pytest
   97	
   98	REPO_ROOT = Path(__file__).resolve().parents[2]
   99	REAL_SCRIPT = REPO_ROOT / "scripts" / "bump-version.sh"
  100	
  101	
  102	def _seed_repo(tmp_path: Path, version: str) -> Path:
  103	    """Build an isolated fake repo so the script's own REPO_ROOT resolution
  104	    (`cd $SCRIPT_DIR/.. && pwd`) lands inside tmp_path and cannot mutate the
  105	    real checkout."""
  106	    (tmp_path / "package.json").write_text(json.dumps({"version": version}, indent=2) + "\n")
  107	    (tmp_path / "VERSION").write_text(version + "\n")
  108	    config = {
  109	        "files": [
  110	            {"path": "package.json", "field": "version"},
  111	            {"path": "VERSION", "format": "plain"},
  112	        ],
  113	        "audit": {"exclude": []},
  114	    }
  115	    (tmp_path / ".version-bump.json").write_text(json.dumps(config, indent=2) + "\n")
  116	    (tmp_path / "scripts").mkdir(exist_ok=True)
  117	    # Symlink the real bump-version.sh into the fake repo's scripts dir. We
  118	    # MUST invoke this symlinked path (not REAL_SCRIPT) so the script's
  119	    # `dirname "$0"` -> `cd $SCRIPT_DIR/..` resolves to tmp_path. Invoking
  120	    # REAL_SCRIPT directly would resolve to the real superstar checkout and
  121	    # mutate its declared files.
  122	    fake_script = tmp_path / "scripts" / "bump-version.sh"
  123	    fake_script.symlink_to(REAL_SCRIPT)
  124	    return tmp_path
  125	
  126	
  127	def _run(script_args: list[str], repo: Path) -> subprocess.CompletedProcess:
  128	    """Invoke the symlinked bump-version.sh inside `repo` so REPO_ROOT
  129	    resolution stays inside the fake repo."""
  130	    fake_script = repo / "scripts" / "bump-version.sh"
  131	    assert fake_script.exists(), "fake script symlink missing — call _seed_repo first"
  132	    return subprocess.run(
  133	        ["bash", str(fake_script), *script_args],
  134	        cwd=repo,
  135	        capture_output=True,
  136	        text=True,
  137	        check=False,
  138	    )
  139	
  140	
  141	def test_check_lists_plain_version(tmp_path: Path) -> None:
  142	    repo = _seed_repo(tmp_path, "1.2.3")
  143	    result = _run(["--check"], repo)
  144	    assert result.returncode == 0, result.stderr
  145	    assert "VERSION" in result.stdout
  146	    assert "1.2.3" in result.stdout
  147	
  148	
  149	def test_bump_writes_plain_version(tmp_path: Path) -> None:
  150	    repo = _seed_repo(tmp_path, "1.2.3")

[truncated: 2247 additional lines]

<!-- superstar-prompt:end -->