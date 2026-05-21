import json
import os
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
PYTHONPATH = str(Path(__file__).resolve().parents[2])


_SUBAGENT_GUARD_VARS = (
    "SUPERSTAR_SUBAGENT_ROLE",
    "CLAUDE_AGENT_ROLE",
    "SUPERSTAR_FORCE_SUBAGENT",
)


def run(root, *args):
    """Run tasktool in a child process. Strips ambient subagent-guard env vars
    so positive lifecycle tests pass even when invoked from a shell that
    followed the dispatched-subagent prompt directive (e.g. an implementer
    subagent that exported SUPERSTAR_SUBAGENT_ROLE=implementer before running
    pytest). Tests that need to exercise the guard use `_run_with_env`."""
    env = os.environ.copy()
    for k in _SUBAGENT_GUARD_VARS:
        env.pop(k, None)
    env["PYTHONPATH"] = PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, str(TOOL), "--project-root", str(root), *args],
        text=True,
        capture_output=True,
        env=env,
    )


def seed(root):
    (root / "docs").mkdir()
    assert run(root, "config", "init-local").returncode == 0
    assert run(root, "init", "--project", "demo").returncode == 0
    assert run(root, "create", "phase", "--title", "Phase").returncode == 0
    assert run(root, "create", "slice", "P1", "--title", "Slice").returncode == 0
    assert run(root, "create", "task", "P1.S1", "--title", "Task").returncode == 0


def tasklist(root):
    return json.loads((root / "docs" / "tasklist.json").read_text())


def ready_chain(root):
    chain = root / "docs" / "reviewer" / "p1-s1-post-slice"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}')
    return chain


def test_start_slice_sets_in_progress_and_started(tmp_path):
    seed(tmp_path)
    r = run(tmp_path, "start", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "in_progress"
    assert sl["started"]


def test_set_in_progress_sets_started(tmp_path):
    seed(tmp_path)
    r = run(tmp_path, "set", "P1.S1", "--status", "in_progress")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "in_progress"
    assert sl["started"]


def test_start_blocked_item_requires_resume(tmp_path):
    seed(tmp_path)
    assert run(tmp_path, "block", "P1.S1", "--on", "external:waiting").returncode == 0
    r = run(tmp_path, "start", "P1.S1")
    assert r.returncode == 1
    assert "use start --resume" in r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "blocked"
    assert sl["blocked_on"] == {"kind": "external", "value": "waiting"}


def test_start_resume_clears_blocked_on_and_sets_started(tmp_path):
    seed(tmp_path)
    assert run(tmp_path, "block", "P1.S1", "--on", "external:waiting").returncode == 0
    r = run(tmp_path, "start", "P1.S1", "--resume")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "in_progress"
    assert sl["blocked_on"] is None
    assert sl["started"]


def test_set_in_progress_on_blocked_item_refuses_without_resume(tmp_path):
    seed(tmp_path)
    assert run(tmp_path, "block", "P1.S1", "--on", "external:waiting").returncode == 0
    r = run(tmp_path, "set", "P1.S1", "--status", "in_progress")
    assert r.returncode == 1
    assert "use start --resume" in r.stderr


def test_start_done_item_refuses(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    assert run(tmp_path, "start", "P1.S1").returncode == 0
    assert run(tmp_path, "close", "P1.S1", "--reviewer-chain", str(chain)).returncode == 0
    r = run(tmp_path, "start", "P1.S1")
    assert r.returncode == 1
    assert "already done" in r.stderr


def test_close_ready_slice_refuses_without_override(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    r = run(tmp_path, "close", "P1.S1", "--reviewer-chain", str(chain))
    assert r.returncode == 1
    assert "must be started before close" in r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "ready"
    assert sl["closed"] is None


def test_close_ready_slice_override_requires_reason(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    r = run(tmp_path, "close", "P1.S1", "--reviewer-chain", str(chain), "--allow-ready-close")
    assert r.returncode == 1
    assert "requires --reason" in r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "ready"
    assert sl["closed"] is None


def test_close_ready_slice_override_records_note(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    r = run(
        tmp_path,
        "close",
        "P1.S1",
        "--reviewer-chain",
        str(chain),
        "--allow-ready-close",
        "--reason",
        "legacy slice closed before start existed",
    )
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "done"
    assert "ready-close override for P1.S1: legacy slice closed before start existed" in sl["notes"]


def test_set_done_ready_slice_refuses_without_start(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    r = run(tmp_path, "set", "P1.S1", "--status", "done", "--reviewer-chain", str(chain))
    assert r.returncode == 1
    assert "must be started before close" in r.stderr
    assert "tasktool start P1.S1" in r.stderr
    assert "tasktool set P1.S1 --status done --allow-ready-close --reason" in r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "ready"
    assert sl["closed"] is None


def test_set_done_ready_slice_override_requires_reason(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    r = run(
        tmp_path,
        "set",
        "P1.S1",
        "--status",
        "done",
        "--reviewer-chain",
        str(chain),
        "--allow-ready-close",
    )
    assert r.returncode == 1
    assert "requires --reason" in r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "ready"
    assert sl["closed"] is None


def test_set_done_ready_slice_override_records_note(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    r = run(
        tmp_path,
        "set",
        "P1.S1",
        "--status",
        "done",
        "--reviewer-chain",
        str(chain),
        "--allow-ready-close",
        "--reason",
        "legacy scripted close before start existed",
    )
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "done"
    assert sl["started"] is None
    assert sl["closed"]
    assert "ready-close override for P1.S1: legacy scripted close before start existed" in sl["notes"]
    assert sl["reviewer_chain"] == "docs/reviewer/p1-s1-post-slice"


def test_set_done_started_slice_records_reviewer_chain(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    assert run(tmp_path, "start", "P1.S1").returncode == 0
    r = run(tmp_path, "set", "P1.S1", "--status", "done", "--reviewer-chain", str(chain))
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "done"
    assert sl["reviewer_chain"] == "docs/reviewer/p1-s1-post-slice"


REFUSAL_MARKER = "Subagents must inherit the parent's worktree"

REFUSAL_SPEC_SENTENCE_TEMPLATE = (
    "Subagents must inherit the parent's worktree; call the parent or "
    "'cd' into the existing recorded path: {worktree_path}."
)


def _run_with_env(root, *args, extra_env=None):
    env = os.environ.copy()
    env["PYTHONPATH"] = PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
    if extra_env:
        for k, v in extra_env.items():
            if v is None:
                env.pop(k, None)
            else:
                env[k] = v
    return subprocess.run(
        [sys.executable, str(TOOL), "--project-root", str(root), *args],
        text=True,
        capture_output=True,
        env=env,
    )


def test_start_refuses_when_superstar_subagent_role_set(tmp_path):
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={"SUPERSTAR_SUBAGENT_ROLE": "implementer"},
    )
    assert r.returncode != 0, r.stdout + r.stderr
    assert REFUSAL_MARKER in (r.stderr + r.stdout)


def test_start_refuses_when_claude_agent_role_is_subagent(tmp_path):
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={
            "SUPERSTAR_SUBAGENT_ROLE": None,
            "CLAUDE_AGENT_ROLE": "subagent",
        },
    )
    assert r.returncode != 0, r.stdout + r.stderr
    assert REFUSAL_MARKER in (r.stderr + r.stdout)


def test_start_proceeds_when_claude_agent_role_is_coordinator(tmp_path):
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={
            "SUPERSTAR_SUBAGENT_ROLE": None,
            "CLAUDE_AGENT_ROLE": "coordinator",
        },
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_start_proceeds_when_claude_agent_role_is_main(tmp_path):
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={
            "SUPERSTAR_SUBAGENT_ROLE": None,
            "CLAUDE_AGENT_ROLE": "main",
        },
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_start_refuses_when_force_subagent_set(tmp_path):
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={
            "SUPERSTAR_SUBAGENT_ROLE": None,
            "CLAUDE_AGENT_ROLE": None,
            "SUPERSTAR_FORCE_SUBAGENT": "1",
        },
    )
    assert r.returncode != 0, r.stdout + r.stderr
    assert REFUSAL_MARKER in (r.stderr + r.stdout)


def test_start_proceeds_in_plain_shell(tmp_path):
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={
            "SUPERSTAR_SUBAGENT_ROLE": None,
            "CLAUDE_AGENT_ROLE": None,
            "SUPERSTAR_FORCE_SUBAGENT": None,
        },
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_start_signal_precedence_superstar_wins(tmp_path):
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={
            "SUPERSTAR_SUBAGENT_ROLE": "implementer",
            "CLAUDE_AGENT_ROLE": "coordinator",
        },
    )
    assert r.returncode != 0, (
        "SUPERSTAR_SUBAGENT_ROLE must win over CLAUDE_AGENT_ROLE=coordinator"
    )
    assert REFUSAL_MARKER in (r.stderr + r.stdout)


def test_start_refusal_message_matches_spec_verbatim(tmp_path):
    seed(tmp_path)
    r = _run_with_env(
        tmp_path, "start", "P1.S1",
        extra_env={"SUPERSTAR_SUBAGENT_ROLE": "implementer"},
    )
    assert r.returncode != 0
    expected_sentence = REFUSAL_SPEC_SENTENCE_TEMPLATE.format(
        worktree_path="<not recorded>"
    )
    combined = r.stderr + r.stdout
    assert expected_sentence in combined, (
        f"refusal message must contain the spec sentence verbatim "
        f"(including trailing period). Looking for:\n  {expected_sentence!r}\n"
        f"Got:\n{combined!r}"
    )


def test_start_env_i_bash_subshell_proceeds(tmp_path):
    seed(tmp_path)
    cmd = (
        f"PATH={os.environ.get('PATH','')} "
        f"PYTHONPATH={PYTHONPATH} "
        f"{sys.executable} {TOOL} --project-root {tmp_path} start P1.S1"
    )
    r = subprocess.run(
        ["env", "-i", "bash", "-c", cmd],
        text=True, capture_output=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_run_helper_strips_ambient_subagent_guard_env(tmp_path, monkeypatch):
    """Regression: a dispatched subagent that follows the prompt directive
    `export SUPERSTAR_SUBAGENT_ROLE=implementer` and then runs pytest should
    still see positive lifecycle tests pass. The `run` helper scrubs the
    three guard env vars so the test subprocess does not inherit them.
    Sweep S1.F1 (post-slice r2)."""
    monkeypatch.setenv("SUPERSTAR_SUBAGENT_ROLE", "implementer")
    monkeypatch.setenv("CLAUDE_AGENT_ROLE", "subagent")
    monkeypatch.setenv("SUPERSTAR_FORCE_SUBAGENT", "1")
    seed(tmp_path)
    r = run(tmp_path, "start", "P1.S1")
    assert r.returncode == 0, (
        f"`run` helper must strip ambient subagent-guard env so positive "
        f"lifecycle tests pass under a dispatched-subagent shell. "
        f"stdout={r.stdout!r} stderr={r.stderr!r}"
    )
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "in_progress"
