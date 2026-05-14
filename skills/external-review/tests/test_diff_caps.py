from pathlib import Path
import subprocess
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def _git_init(repo: Path):
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "seed.txt").write_text("seed\n")
    subprocess.run(["git", "-C", str(repo), "add", "seed.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)


def test_untracked_file_count_capped_at_10(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    _git_init(repo)
    base_ref = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    for i in range(15):
        (repo / f"u{i}.txt").write_text(f"untracked {i}\n")
    diff = er.compute_diff_section(repo, base_ref=base_ref, paths=None, max_lines=500)
    assert "more untracked files elided" in diff
    assert diff.count("\n### u") <= 10


def test_oversized_untracked_file_line_capped(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    _git_init(repo)
    base_ref = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    (repo / "big.txt").write_text("\n".join(f"line {i}" for i in range(500)))
    diff = er.compute_diff_section(repo, base_ref=base_ref, paths=None, max_lines=500)
    assert "line 50" in diff
    assert "line 400" not in diff


def test_global_diff_cap_applies(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    _git_init(repo)
    base_ref = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    for i in range(8):
        (repo / f"u{i}.txt").write_text(("x" * 80 + "\n") * 200)
    diff = er.compute_diff_section(repo, base_ref=base_ref, paths=None, max_lines=200)
    assert "bytes elided" in diff
