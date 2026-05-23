"""Tests for the TodoWrite/update_plan snapshot hook."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / "hooks" / "todo-snapshot"
HOOKS_CONFIG = REPO_ROOT / "hooks" / "hooks.json"


def _run_hook(payload: dict, home: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "HOME": str(home)}
    return subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def test_claude_todowrite_snapshot_shape(tmp_path: Path) -> None:
    payload = {
        "session_id": "claude-session",
        "cwd": "/tmp/example-project",
        "tool_name": "TodoWrite",
        "tool_input": {
            "todos": [
                {"content": "one", "status": "completed"},
                {"content": "two", "status": "in_progress"},
                {"content": "three", "status": "pending"},
            ],
        },
    }

    result = _run_hook(payload, tmp_path)

    assert result.returncode == 0, result.stderr
    snapshot = tmp_path / ".claude/projects/-tmp-example-project/claude-session/todos.json"
    data = json.loads(snapshot.read_text(encoding="utf-8"))
    assert data["source_tool"] == "TodoWrite"
    assert data["counts"] == {"done": 1, "in_progress": 1, "total": 3}
    assert data["todos"] == payload["tool_input"]["todos"]


def test_codex_update_plan_snapshot_shape(tmp_path: Path) -> None:
    payload = {
        "session_id": "codex-session",
        "cwd": "/tmp/example-project",
        "tool_name": "update_plan",
        "tool_input": {
            "plan": [
                {"step": "one", "status": "completed"},
                {"step": "two", "status": "in_progress"},
                {"step": "three", "status": "pending"},
            ],
        },
    }

    result = _run_hook(payload, tmp_path)

    assert result.returncode == 0, result.stderr
    snapshot = tmp_path / ".codex/projects/-tmp-example-project/codex-session/todos.json"
    data = json.loads(snapshot.read_text(encoding="utf-8"))
    assert data["source_tool"] == "update_plan"
    assert data["counts"] == {"done": 1, "in_progress": 1, "total": 3}
    assert data["todos"] == [
        {"content": "one", "status": "completed"},
        {"content": "two", "status": "in_progress"},
        {"content": "three", "status": "pending"},
    ]


def test_snapshot_hook_is_synchronous_for_codex() -> None:
    config = json.loads(HOOKS_CONFIG.read_text(encoding="utf-8"))
    post_tool_use = config["hooks"]["PostToolUse"][0]

    assert post_tool_use["matcher"] == "TodoWrite|update_plan|functions.update_plan"
    assert post_tool_use["hooks"][0]["command"].endswith(" todo-snapshot")
    assert post_tool_use["hooks"][0]["async"] is False
