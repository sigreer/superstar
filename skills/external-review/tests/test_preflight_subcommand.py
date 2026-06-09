from pathlib import Path
import json, subprocess, sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "external-reviewer.py"


def _repo(tmp_path):
    # run_preflight() calls repo_root() (git rev-parse, check=True), so the
    # cwd must be a git repo — init one, matching the review subprocess harness.
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    return repo


def _pf(repo, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "preflight", *args],
        cwd=repo, capture_output=True, text=True,
    )


def test_clean_doc_exit_0(tmp_path):
    repo = _repo(tmp_path)
    (repo / "doc.md").write_text(
        "# Spec\n\n## Acceptance criteria\n\n1. A grounded criterion.\n")
    r = _pf(repo, "--kind", "spec", "--file", "doc.md")
    assert r.returncode == 0, r.stderr + r.stdout


def test_failure_doc_exit_4(tmp_path):
    repo = _repo(tmp_path)
    (repo / "doc.md").write_text("# Spec\n\nNo criteria, and a TODO marker.\n")
    r = _pf(repo, "--kind", "spec", "--file", "doc.md")
    assert r.returncode == 4, r.stderr + r.stdout


def test_emit_json_shape(tmp_path):
    repo = _repo(tmp_path)
    (repo / "doc.md").write_text("# Spec\n\nNo criteria here. TODO.\n")
    r = _pf(repo, "--kind", "spec", "--file", "doc.md", "--emit", "json")
    assert r.returncode == 4
    payload = json.loads(r.stdout)
    assert payload["ok"] is False
    assert isinstance(payload["failures"], list) and payload["failures"]
    assert "warnings" in payload
    assert {"check", "severity", "message"} <= set(payload["failures"][0])


def test_warning_only_exit_0(tmp_path):
    repo = _repo(tmp_path)
    (repo / "doc.md").write_text(
        "# Spec\n\n## Acceptance criteria\n\nSee `skills/gone/x.py` (dangling, warns).\n")
    r = _pf(repo, "--kind", "spec", "--file", "doc.md", "--emit", "json")
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert payload["ok"] is True
    assert payload["warnings"]


# --- AC2: each check class exercised THROUGH the standalone subcommand ---
def _checks(payload, severity):
    return {f["check"] for f in payload[severity]}


def test_subcommand_placeholder_failure(tmp_path):
    repo = _repo(tmp_path)
    (repo / "doc.md").write_text("# Spec\n\n## Acceptance criteria\n\nstill TODO here\n")
    r = _pf(repo, "--kind", "spec", "--file", "doc.md", "--emit", "json")
    assert r.returncode == 4
    assert "placeholder" in _checks(json.loads(r.stdout), "failures")


def test_subcommand_dangling_link_failure(tmp_path):
    repo = _repo(tmp_path)
    (repo / "doc.md").write_text(
        "# Spec\n\n## Acceptance criteria\n\nSee [x](docs/gone/missing.md).\n")
    r = _pf(repo, "--kind", "spec", "--file", "doc.md", "--emit", "json")
    assert r.returncode == 4
    assert "dangling-link" in _checks(json.loads(r.stdout), "failures")


def test_subcommand_dangling_backtick_warning(tmp_path):
    repo = _repo(tmp_path)
    (repo / "doc.md").write_text(
        "# Spec\n\n## Acceptance criteria\n\nLook at `skills/gone/x.py` here.\n")
    r = _pf(repo, "--kind", "spec", "--file", "doc.md", "--emit", "json")
    assert r.returncode == 0
    assert "dangling-path" in _checks(json.loads(r.stdout), "warnings")


def test_subcommand_missing_section_failure(tmp_path):
    repo = _repo(tmp_path)
    (repo / "doc.md").write_text("# Spec\n\nProse only, no criteria heading.\n")
    r = _pf(repo, "--kind", "spec", "--file", "doc.md", "--emit", "json")
    assert r.returncode == 4
    assert "missing-section" in _checks(json.loads(r.stdout), "failures")


def test_subcommand_missing_context_failure(tmp_path):
    repo = _repo(tmp_path)
    (repo / "doc.md").write_text("# Spec\n\n## Acceptance criteria\n\nok\n")
    r = _pf(repo, "--kind", "spec", "--file", "doc.md",
            "--context", "nope-ctx.md", "--emit", "json")
    assert r.returncode == 4
    assert "context" in _checks(json.loads(r.stdout), "failures")


def test_subcommand_oversized_context_warning(tmp_path):
    repo = _repo(tmp_path)
    (repo / "doc.md").write_text("# Spec\n\n## Acceptance criteria\n\nok\n")
    (repo / "big.json").write_text("x" * (17 * 1024))
    r = _pf(repo, "--kind", "spec", "--file", "doc.md",
            "--context", "big.json", "--emit", "json")
    assert r.returncode == 0
    assert "context" in _checks(json.loads(r.stdout), "warnings")
