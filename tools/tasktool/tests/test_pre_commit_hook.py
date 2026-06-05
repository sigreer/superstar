# tools/tasktool/tests/test_pre_commit_hook.py
import json, os, subprocess, shlex, sys, shutil, textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TOOL = REPO / "tools" / "tasktool" / "__main__.py"
INSTALL = REPO / "tools" / "tasktool" / "install.sh"
PKG_DIR = REPO / "tools"

def _git(repo, *args, check=True, env=None):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=check, env=env)

def _tasktool(repo, *args, env=None):
    if env is None:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run([sys.executable, str(TOOL), "--project-root", str(repo), *args],
                          capture_output=True, text=True, env=env)

def _read_source_version() -> str:
    """Return the Superstar source VERSION (single line)."""
    return (REPO / "VERSION").read_text().splitlines()[0].strip()


def _install_hook_only(repo, *, force: bool = False, check: bool = True):
    args = ["bash", str(INSTALL), "--hook"]
    if force:
        args.append("--force")
    result = subprocess.run(args, cwd=repo, capture_output=True, text=True, check=False)
    if check:
        assert result.returncode == 0, result.stdout + result.stderr
    return result


def _seed_repo(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "docs").mkdir()
    (repo / "docs" / "specs").mkdir()
    (repo / "docs" / "plans").mkdir()
    # Build env with PYTHONPATH so the package is importable, plus a shim
    # on PATH so the hook's `tasktool` invocation resolves.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "tasktool").write_text(f"#!/usr/bin/env sh\nexec {sys.executable} {TOOL} \"$@\"\n")
    os.chmod(bin_dir / "tasktool", 0o755)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["PYTHONPATH"] = str(PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    r = _tasktool(repo, "config", "init-local", env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    _tasktool(repo, "init", "--project", "demo", env=env)
    # Install the hook (install.sh is bash):
    subprocess.run(["bash", str(INSTALL), "--hook"], cwd=repo, check=True, env=env)
    return repo, env

def test_canonical_commit_passes(tmp_path):
    repo, env = _seed_repo(tmp_path)
    _git(repo, "add", "docs/tasklist.json", env=env)
    r = _git(repo, "commit", "-m", "init", check=False, env=env)
    assert r.returncode == 0, r.stdout + r.stderr

def test_non_canonical_bytes_rejected(tmp_path):
    repo, env = _seed_repo(tmp_path)
    _git(repo, "add", "docs/tasklist.json", env=env)
    _git(repo, "commit", "-m", "init", env=env)
    # Append a stray newline → non-canonical.
    with open(repo / "docs" / "tasklist.json", "a") as f:
        f.write("\n")
    _git(repo, "add", "docs/tasklist.json", env=env)
    r = _git(repo, "commit", "-m", "tamper", check=False, env=env)
    assert r.returncode != 0
    assert "canonical" in (r.stdout + r.stderr).lower()

def test_orphan_spec_filename_rejected(tmp_path):
    repo, env = _seed_repo(tmp_path)
    _git(repo, "add", "docs/tasklist.json", env=env)
    _git(repo, "commit", "-m", "init", env=env)
    orphan = repo / "docs" / "specs" / "2026-05-18-P99-orphan-design.md"
    orphan.write_text("# orphan\n")
    _git(repo, "add", str(orphan.relative_to(repo)), env=env)
    r = _git(repo, "commit", "-m", "orphan", check=False, env=env)
    assert r.returncode != 0
    assert "P99" in (r.stdout + r.stderr)

def test_tasklist_md_rejected(tmp_path):
    repo, env = _seed_repo(tmp_path)
    _git(repo, "add", "docs/tasklist.json", env=env)
    _git(repo, "commit", "-m", "init", env=env)
    legacy = repo / "docs" / "TASKLIST.md"
    legacy.write_text("# legacy\n")
    _git(repo, "add", "docs/TASKLIST.md", env=env)
    r = _git(repo, "commit", "-m", "legacy", check=False, env=env)
    assert r.returncode != 0
    assert "TASKLIST.md" in (r.stdout + r.stderr)

def test_raw_edit_then_normalise_passes(tmp_path):
    """Raw edit (semantic change) + validate --normalise → canonical commit accepted."""
    import json as _json
    repo, env = _seed_repo(tmp_path)
    _git(repo, "add", "docs/tasklist.json", env=env)
    _git(repo, "commit", "-m", "init", env=env)
    p = repo / "docs" / "tasklist.json"
    # Raw-edit: change a string field and write back in non-canonical form
    # (extra whitespace), simulating an editor session.
    data = _json.loads(p.read_text())
    data["project"] = "demo-edited"
    p.write_text(_json.dumps(data, indent=4) + "\n\n")  # non-canonical formatting
    _tasktool(repo, "validate", "--normalise", env=env)
    _git(repo, "add", "docs/tasklist.json", env=env)
    r = _git(repo, "commit", "-m", "normalised", check=False, env=env)
    assert r.returncode == 0, r.stdout + r.stderr

def test_staged_bad_normalised_worktree_is_rejected(tmp_path):
    """Stage non-canonical bytes, then normalise the worktree without re-staging.
    The hook MUST reject because the index is what gets committed."""
    repo, env = _seed_repo(tmp_path)
    _git(repo, "add", "docs/tasklist.json", env=env)
    _git(repo, "commit", "-m", "init", env=env)
    p = repo / "docs" / "tasklist.json"
    with open(p, "a") as f:
        f.write("\n")
    # Stage the bad bytes.
    _git(repo, "add", "docs/tasklist.json", env=env)
    # Now normalise the WORKTREE only (do not re-add).
    _tasktool(repo, "validate", "--normalise", env=env)
    r = _git(repo, "commit", "-m", "staged-bad-worktree-clean", check=False, env=env)
    assert r.returncode != 0, (
        "hook must validate the index, not the worktree, but commit succeeded: "
        + r.stdout + r.stderr
    )

def test_tasklist_json_deletion_rejected(tmp_path):
    """Staging the deletion of docs/tasklist.json must be refused."""
    repo, env = _seed_repo(tmp_path)
    _git(repo, "add", "docs/tasklist.json", env=env)
    _git(repo, "commit", "-m", "init", env=env)
    _git(repo, "rm", "docs/tasklist.json", env=env)
    r = _git(repo, "commit", "-m", "delete tracker", check=False, env=env)
    assert r.returncode != 0, "hook must refuse tasklist.json deletion: " + r.stdout + r.stderr
    assert "deletion" in (r.stdout + r.stderr).lower() or "delete" in (r.stdout + r.stderr).lower()

def test_hook_install_is_idempotent(tmp_path):
    """Running `install.sh --hook` twice without --force must succeed both times."""
    repo, env = _seed_repo(tmp_path)
    # First install happened in _seed_repo. Run again:
    r = subprocess.run(["bash", str(INSTALL), "--hook"], cwd=repo, capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr

def test_hook_uses_global_tasktool_even_when_repo_local_wrapper_exists(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "docs").mkdir()
    (repo / "docs" / "tasklist.json").write_text(
        '{"schema_version":1,"project":"demo","north_star":"","last_reviewed":null,'
        '"phases":[],"cross_cutting":[],"archived_phases":[]}\n',
        encoding="utf-8",
    )
    wrapper = repo / "tools" / "tasktool" / "tasktool"
    wrapper.parent.mkdir(parents=True)
    local_log = repo / "local-wrapper.log"
    wrapper.write_text(
        "#!/usr/bin/env sh\n"
        f"printf '%s\\n' \"$*\" >> {local_log}\n"
        "exit 99\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    global_log = repo / "global-shim.log"
    global_shim = bin_dir / "tasktool"
    global_shim.write_text(
        "#!/usr/bin/env sh\n"
        f"printf '%s\\n' \"$*\" >> {global_log}\n"
        "exit 0\n",
        encoding="utf-8",
    )
    global_shim.chmod(0o755)
    _git(repo, "add", "docs/tasklist.json")
    subprocess.run(["bash", str(INSTALL), "--hook"], cwd=repo, check=True)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:/usr/bin:/bin"
    r = _git(repo, "commit", "-m", "init", check=False, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "--project-root" in global_log.read_text(encoding="utf-8")
    assert not local_log.exists()

def test_staged_good_dirty_worktree_passes(tmp_path):
    """Stage canonical bytes, then dirty the worktree without re-staging.
    The hook MUST pass — the index is canonical, the worktree dirt is irrelevant."""
    repo, env = _seed_repo(tmp_path)
    _git(repo, "add", "docs/tasklist.json", env=env)
    _git(repo, "commit", "-m", "init", env=env)
    # Stage a clean tasktool-mediated change.
    _tasktool(repo, "create", "phase", "--title", "P", env=env)
    _git(repo, "add", "docs/tasklist.json", env=env)
    # Now dirty the worktree post-stage.
    p = repo / "docs" / "tasklist.json"
    with open(p, "a") as f:
        f.write("\n")
    r = _git(repo, "commit", "-m", "staged-good-dirty-worktree", check=False, env=env)
    assert r.returncode == 0, (
        "hook must accept canonical index regardless of worktree dirt: "
        + r.stdout + r.stderr
    )


def test_lifecycle_autocommit_passes_real_hook(tmp_path):
    """P8.S1: close auto-commit runs through the installed hook and passes."""
    repo, env = _seed_repo(tmp_path)
    hook_log = repo / "tasktool-hook.log"
    (tmp_path / "bin" / "tasktool").write_text(
        "#!/usr/bin/env sh\n"
        f"printf '%s\\n' \"$*\" >> {shlex.quote(str(hook_log))}\n"
        f"exec {shlex.quote(sys.executable)} {shlex.quote(str(TOOL))} \"$@\"\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A", env=env)
    _git(repo, "commit", "-m", "seed", env=env)
    r = _tasktool(repo, "create", "phase", "--title", "P", env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    r = _tasktool(repo, "create", "slice", "P1", "--title", "S", env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    _git(repo, "add", "docs/tasklist.json", env=env)
    _git(repo, "commit", "-m", "rows", env=env)

    r = _tasktool(repo, "start", "P1.S1", env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads((repo / "docs" / "tasklist.json").read_text())
    sl = data["phases"][0]["slices"][0]
    branch = sl["worktree_branch"]
    wt = repo / sl["worktree_path"]
    assert branch
    assert wt.is_dir()
    _git(repo, "add", "docs/tasklist.json", env=env)
    _git(repo, "commit", "-m", "start", env=env)

    (wt / "work.txt").write_text("payload\n")
    _git(wt, "add", "-A", env=env)
    _git(wt, "commit", "-m", "work", env=env)
    _git(repo, "merge", "--no-ff", "-m", "land", branch, env=env)

    hook_invocations_before_close = hook_log.read_text(encoding="utf-8").splitlines()
    r = _tasktool(repo, "close", "P1.S1", "--skip-review-gate", env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "auto-commit failed" not in r.stderr
    hook_invocations_after_close = hook_log.read_text(encoding="utf-8").splitlines()
    close_hook_invocations = hook_invocations_after_close[len(hook_invocations_before_close):]
    assert any(
        " validate --strict-format --no-path-warnings --format text" in invocation
        for invocation in close_hook_invocations
    ), close_hook_invocations
    assert any(
        " validate --no-path-warnings --format text" in invocation
        for invocation in close_hook_invocations
    ), close_hook_invocations
    log = _git(repo, "log", "-1", "--format=%s", env=env).stdout.strip()
    assert log == "P1.S1: close slice (status=done)"


def test_hook_install_writes_stamped_header(tmp_path):
    repo, _env = _seed_repo(tmp_path)  # _seed_repo already ran install.sh --hook
    hook = repo / ".git" / "hooks" / "pre-commit"
    text = hook.read_text()
    src_version = _read_source_version()
    assert "superstar-hook-name: tasktool-pre-commit" in text
    assert f"superstar-hook-version: {src_version}" in text
    assert "superstar-hook-source-root:" in text
    assert "superstar-hook-installer: tools/tasktool/install.sh --hook" in text
    assert "superstar-hook-generated-at:" in text
    assert "tasktool-pre-commit-hook" in text


def test_hook_install_accepts_legacy_marker_without_force(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/usr/bin/env sh\n# tasktool-pre-commit-hook v1\nexit 0\n")
    hook.chmod(0o755)
    result = _install_hook_only(repo, force=False)
    assert result.returncode == 0
    text = hook.read_text()
    assert "superstar-hook-name: tasktool-pre-commit" in text
    src_version = _read_source_version()
    assert f"superstar-hook-version: {src_version}" in text


def test_hook_install_refuses_non_tasktool_hook_without_force(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/usr/bin/env sh\n# someone-elses-hook\nexit 0\n")
    hook.chmod(0o755)
    result = _install_hook_only(repo, force=False, check=False)
    assert result.returncode != 0
    assert "not a tasktool hook" in result.stderr
