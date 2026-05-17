from pathlib import Path
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[3]
WRAPPER = ROOT / "skills" / "project-setup" / "scripts" / "reviewer-agent"


def _fake_bin(tmp_path, name):
    calls = tmp_path / f"{name}-calls.json"
    exe = tmp_path / name
    exe.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, pathlib, sys\n"
        f"calls = pathlib.Path({str(calls)!r})\n"
        "calls.write_text(json.dumps({'argv': sys.argv[1:], 'stdin': sys.stdin.read()}))\n"
        "out = os.environ.get('AGENT_REVIEWER_RESPONSE_DIR')\n"
        "if out:\n"
        "    pathlib.Path(out).mkdir(parents=True, exist_ok=True)\n"
        "    pathlib.Path(out, 'last-message.md').write_text('Overall verdict: ready\\n')\n"
        "print('Overall verdict: ready')\n"
    )
    exe.chmod(0o755)
    return calls


def _env(tmp_path, provider):
    response_dir = tmp_path / "response"
    scratch_dir = tmp_path / "scratch"
    repo = tmp_path / "repo"
    target = repo / "plan.md"
    for p in (response_dir, scratch_dir, repo):
        p.mkdir(parents=True, exist_ok=True)
    target.write_text("# Plan\n")
    env = os.environ.copy()
    env.update({
        "PATH": f"{tmp_path}:{env['PATH']}",
        "AGENT_REVIEWER_PROVIDER": provider,
        "AGENT_REVIEWER_REPO_ROOT": str(repo),
        "AGENT_REVIEWER_RESPONSE_DIR": str(response_dir),
        "AGENT_REVIEWER_SCRATCH_DIR": str(scratch_dir),
        "AGENT_REVIEWER_TARGET_FILE": str(target),
    })
    return env


def test_codex_wrapper_uses_sandbox_and_never_bypass(tmp_path):
    calls = _fake_bin(tmp_path, "codex")
    env = _env(tmp_path, "codex")
    result = subprocess.run([str(WRAPPER)], input="review prompt", env=env, text=True, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr
    call = json.loads(calls.read_text())
    argv = call["argv"]
    assert argv[:1] == ["exec"]
    assert "--dangerously-bypass-approvals-and-sandbox" not in argv
    assert "--sandbox" in argv and "workspace-write" in argv
    assert "--ephemeral" in argv
    assert "--cd" in argv and env["AGENT_REVIEWER_SCRATCH_DIR"] in argv
    assert "--add-dir" in argv and env["AGENT_REVIEWER_RESPONSE_DIR"] in argv
    assert Path(env["AGENT_REVIEWER_SCRATCH_DIR"]).is_absolute()
    assert Path(env["AGENT_REVIEWER_RESPONSE_DIR"]).is_absolute()
    assert "--output-last-message" in argv
    assert "disk-full-read-access" in " ".join(argv)


def test_claude_wrapper_uses_print_and_plan_mode(tmp_path):
    calls = _fake_bin(tmp_path, "claude")
    env = _env(tmp_path, "claude")
    result = subprocess.run([str(WRAPPER)], input="review prompt", env=env, text=True, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr
    call = json.loads(calls.read_text())
    argv = call["argv"]
    assert "--print" in argv
    assert "--permission-mode" in argv and "plan" in argv
    assert "--dangerously-skip-permissions" not in argv
    assert "--add-dir" in argv
    assert env["AGENT_REVIEWER_REPO_ROOT"] in argv


def test_wrapper_fails_when_required_env_missing(tmp_path):
    _fake_bin(tmp_path, "codex")
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    env["AGENT_REVIEWER_PROVIDER"] = "codex"
    result = subprocess.run([str(WRAPPER)], input="x", env=env, text=True, capture_output=True, timeout=20)
    assert result.returncode == 2
    assert "AGENT_REVIEWER_REPO_ROOT" in result.stderr
