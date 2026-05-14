from pathlib import Path
import subprocess, sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def _repo(tmp_path):
    repo = tmp_path / "r"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    return repo


def test_diff_between_two_commits(tmp_path):
    repo = _repo(tmp_path)
    (repo / "a.txt").write_text("one\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "1"], check=True)
    base = er.current_head_sha(repo)
    (repo / "a.txt").write_text("one\ntwo\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "2"], check=True)

    out = er.compute_diff_section(repo, base_ref=base, paths=None, max_lines=200)
    assert "+two" in out
    assert "Worktree status: clean" in out


def test_untracked_files_surfaced(tmp_path):
    repo = _repo(tmp_path)
    (repo / "a.txt").write_text("one\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "1"], check=True)
    base = er.current_head_sha(repo)
    (repo / "new.txt").write_text("brand new\nfile\n")

    out = er.compute_diff_section(repo, base_ref=base, paths=None, max_lines=200)
    assert "Untracked files" in out
    assert "new.txt" in out
    assert "brand new" in out
    assert "Worktree status: dirty" in out


def test_no_diff_when_base_ref_none(tmp_path):
    repo = _repo(tmp_path)
    out = er.compute_diff_section(repo, base_ref=None, paths=None, max_lines=200)
    assert "not available" in out


def test_paths_scope_excludes_unrelated_untracked(tmp_path):
    repo = _repo(tmp_path)
    (repo / "plan.md").write_text("plan v1\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "1"], check=True)
    base = er.current_head_sha(repo)
    (repo / "plan.md").write_text("plan v1\nplan v2\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "2"], check=True)
    # Unrelated untracked file outside scoped paths
    (repo / "unrelated.txt").write_text("should not leak\n")

    out = er.compute_diff_section(repo, base_ref=base, paths=["plan.md"], max_lines=200)
    assert "+plan v2" in out
    assert "unrelated.txt" not in out
    assert "should not leak" not in out
    assert "Worktree status: clean" in out


def test_paths_scope_includes_in_scope_untracked(tmp_path):
    repo = _repo(tmp_path)
    (repo / "plan.md").write_text("plan v1\n")
    (repo / "keep.md").write_text("keep v1\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "1"], check=True)
    base = er.current_head_sha(repo)
    (repo / "scoped.md").write_text("scoped untracked\n")
    (repo / "other.txt").write_text("out of scope\n")

    out = er.compute_diff_section(repo, base_ref=base, paths=["scoped.md", "keep.md"], max_lines=200)
    assert "scoped.md" in out
    assert "scoped untracked" in out
    assert "other.txt" not in out
    assert "out of scope" not in out
