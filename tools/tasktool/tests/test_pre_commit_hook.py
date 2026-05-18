# tools/tasktool/tests/test_pre_commit_hook.py
import os, subprocess, sys, shutil, textwrap
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
