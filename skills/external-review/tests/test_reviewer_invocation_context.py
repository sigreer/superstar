from pathlib import Path
import json
import os
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    (repo / "plan.md").write_text("# Plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    return repo


def test_reviewer_receives_sandbox_context_env(tmp_path):
    repo = _repo(tmp_path)
    reviewer = repo / "fake-reviewer.py"
    reviewer.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os\n"
        "keys = [\n"
        "  'AGENT_REVIEWER_REPO_ROOT', 'AGENT_REVIEWER_CHAIN_DIR',\n"
        "  'AGENT_REVIEWER_REQUEST_FILE', 'AGENT_REVIEWER_RESPONSE_DIR',\n"
        "  'AGENT_REVIEWER_SCRATCH_DIR', 'AGENT_REVIEWER_TARGET_FILE',\n"
        "  'AGENT_REVIEWER_KIND', 'AGENT_REVIEWER_ROLE', 'AGENT_REVIEWER_SWEEP_INDEX',\n"
        "  'AGENT_REVIEWER_PROVIDER', 'AGENT_REVIEWER_CALLER',\n"
        "]\n"
        "print(json.dumps({k: os.environ.get(k, '') for k in keys}, sort_keys=True))\n"
        "print('Overall verdict: ready')\n"
    )
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "state.json")
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "external-reviewer.py"),
            "review",
            "--kind", "post-slice",
            "--work-id", "P1.S1",
            "--file", "plan.md",
            "--emit", "json",
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    review = payload["review"]
    start = review.index("{")
    end = review.index("}", start) + 1
    seen = json.loads(review[start:end])
    assert seen["AGENT_REVIEWER_REPO_ROOT"] == str(repo)
    assert seen["AGENT_REVIEWER_KIND"] == "post-slice"
    assert seen["AGENT_REVIEWER_ROLE"] == "primary"
    assert seen["AGENT_REVIEWER_PROVIDER"] == "custom"
    assert seen["AGENT_REVIEWER_CALLER"] in {"auto", "unknown", "claude", "codex", ""}
    assert seen["AGENT_REVIEWER_SWEEP_INDEX"] == ""
    assert Path(seen["AGENT_REVIEWER_RESPONSE_DIR"]).is_dir()
    assert seen["AGENT_REVIEWER_REQUEST_FILE"].endswith("-request.md")
    assert seen["AGENT_REVIEWER_TARGET_FILE"] == str(repo / "plan.md")


def test_reviewer_scratch_is_removed_by_default(tmp_path):
    repo = _repo(tmp_path)
    marker = repo / "scratch-path.txt"
    reviewer = repo / "fake-reviewer.py"
    reviewer.write_text(
        "#!/usr/bin/env python3\n"
        "import os, pathlib\n"
        f"pathlib.Path({str(marker)!r}).write_text(os.environ['AGENT_REVIEWER_SCRATCH_DIR'])\n"
        "print('Overall verdict: ready')\n"
    )
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "state.json")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"), "review", "--kind", "spec", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    scratch = Path(marker.read_text())
    assert not scratch.exists()


def test_reviewer_scratch_directory_is_private_0700(tmp_path):
    repo = _repo(tmp_path)
    marker = repo / "scratch-mode.txt"
    reviewer = repo / "fake-reviewer.py"
    reviewer.write_text(
        "#!/usr/bin/env python3\n"
        "import os, pathlib\n"
        "scratch = pathlib.Path(os.environ['AGENT_REVIEWER_SCRATCH_DIR'])\n"
        f"pathlib.Path({str(marker)!r}).write_text(oct(scratch.stat().st_mode & 0o777))\n"
        "print('Overall verdict: ready')\n"
    )
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "state.json")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"), "review", "--kind", "spec", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert marker.read_text() == "0o700"


def test_keep_reviewer_scratch_preserves_directory(tmp_path):
    repo = _repo(tmp_path)
    marker = repo / "scratch-path.txt"
    reviewer = repo / "fake-reviewer.py"
    reviewer.write_text(
        "#!/usr/bin/env python3\n"
        "import os, pathlib\n"
        "scratch = pathlib.Path(os.environ['AGENT_REVIEWER_SCRATCH_DIR'])\n"
        "(scratch / 'note.txt').write_text('kept')\n"
        f"pathlib.Path({str(marker)!r}).write_text(str(scratch))\n"
        "print('Overall verdict: ready')\n"
    )
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "state.json")
    result = subprocess.run(
        [
            sys.executable, str(SCRIPTS / "external-reviewer.py"),
            "review", "--kind", "spec", "--file", "plan.md",
            "--keep-reviewer-scratch",
            "--emit", "json",
        ],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    scratch = Path(marker.read_text())
    assert (scratch / "note.txt").read_text() == "kept"


def test_new_command_template_placeholders(tmp_path):
    from pathlib import Path
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
    er = importlib.util.module_from_spec(spec)
    sys.modules["external_reviewer"] = er
    spec.loader.exec_module(er)

    prompt_file = tmp_path / "prompt.md"
    target_file = tmp_path / "target.md"
    chain_dir = tmp_path / "chain"
    response_dir = chain_dir / ".reviewer-output" / "r1-primary"
    scratch_dir = tmp_path / "scratch"
    request_file = chain_dir / "r1-request.md"
    for path in (prompt_file, target_file, request_file):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")
    response_dir.mkdir(parents=True)
    scratch_dir.mkdir()
    out = er.expand_command_template(
        "tool {repo_root} {response_dir} {scratch_dir} {request_file}",
        prompt_file=prompt_file,
        prompt_text="hello",
        target_file=target_file,
        kind="spec",
        chain_dir=chain_dir,
        round_num=1,
        previous_response=None,
        resolution_file=None,
        session_file=chain_dir / "session.state",
        repo_root=tmp_path,
        response_dir=response_dir,
        scratch_dir=scratch_dir,
        request_file=request_file,
    )
    assert str(tmp_path) in out
    assert str(response_dir) in out
    assert str(scratch_dir) in out
    assert str(request_file) in out
