"""Regression test: set --workflow-step plan from spec requires no gate.

P9.S3 combined-gate spec (S3.c) verified that _validate_set_flags in
commands.py only checks workflow_step value membership — it does NOT enforce
ordering. This test pins that behaviour so future changes cannot silently
introduce a spec-review-passed precondition between spec and plan.
"""

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
    """Run tasktool in a child process, stripping ambient subagent-guard vars."""
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


def test_workflow_step_spec_to_plan_no_precondition(tmp_path):
    """spec -> plan transition must succeed without any intervening review gate."""
    seed(tmp_path)

    r_spec = run(tmp_path, "set", "P1.S1", "--workflow-step", "spec")
    assert r_spec.returncode == 0, r_spec.stderr

    r_plan = run(tmp_path, "set", "P1.S1", "--workflow-step", "plan")
    assert r_plan.returncode == 0, r_plan.stderr

    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["workflow_step"] == "plan"
