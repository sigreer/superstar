from pathlib import Path
import json, os, subprocess

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
    env = {
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "AGENT_REVIEWER_PROVIDER": provider,
        "AGENT_REVIEWER_REPO_ROOT": str(repo),
        "AGENT_REVIEWER_RESPONSE_DIR": str(response_dir),
        "AGENT_REVIEWER_SCRATCH_DIR": str(scratch_dir),
        "AGENT_REVIEWER_TARGET_FILE": str(target),
    }
    return env


def _argv(calls):
    return json.loads(calls.read_text())["argv"]


def test_codex_receives_model_flag(tmp_path):
    calls = _fake_bin(tmp_path, "codex")
    env = _env(tmp_path, "codex")
    env["AGENT_REVIEWER_MODEL"] = "tier-model"
    r = subprocess.run([str(WRAPPER)], input="prompt", env=env, text=True,
                       capture_output=True, timeout=20)
    assert r.returncode == 0, r.stderr
    argv = _argv(calls)
    i = argv.index("-m")
    assert argv[i:i + 2] == ["-m", "tier-model"]


def test_codex_no_model_flag_when_unset(tmp_path):
    calls = _fake_bin(tmp_path, "codex")
    r = subprocess.run([str(WRAPPER)], input="prompt", env=_env(tmp_path, "codex"),
                       text=True, capture_output=True, timeout=20)
    assert r.returncode == 0, r.stderr
    assert "-m" not in _argv(calls)


def test_claude_receives_model_flag(tmp_path):
    calls = _fake_bin(tmp_path, "claude")
    env = _env(tmp_path, "claude")
    env["AGENT_REVIEWER_MODEL"] = "tier-model"
    r = subprocess.run([str(WRAPPER)], input="prompt", env=env, text=True,
                       capture_output=True, timeout=20)
    assert r.returncode == 0, r.stderr
    argv = _argv(calls)
    i = argv.index("--model")
    assert argv[i:i + 2] == ["--model", "tier-model"]


def test_claude_no_model_flag_when_unset(tmp_path):
    calls = _fake_bin(tmp_path, "claude")
    r = subprocess.run([str(WRAPPER)], input="prompt", env=_env(tmp_path, "claude"),
                       text=True, capture_output=True, timeout=20)
    assert r.returncode == 0, r.stderr
    assert "--model" not in _argv(calls)
