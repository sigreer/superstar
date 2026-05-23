from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _disable_notifications_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPERSTAR_NOTIFY_DISABLE", "1")


@pytest.fixture
def tmp_project_with_p6_s1(tmp_path: Path) -> Path:
    # NB: persisted slice IDs are SHORT (`S1`), qualified to `P6.S1` only at the CLI boundary.
    # See `tools/tasktool/schema_gen.py` (pattern ^S\d+[a-z]?$) and `_find_item` in commands.py.
    from tasktool import commands

    (tmp_path / "docs").mkdir()
    commands.cmd_config_init_local(repo_root=tmp_path)
    raw = {
        "project": "test",
        "schema_version": 2,
        "phases": [
            {
                "id": "P6",
                "title": "t",
                "created": "2026-05-23",
                "status": "ready",
                "slices": [
                    {"id": "S1", "title": "t", "created": "2026-05-23", "status": "ready"}
                ],
            }
        ],
        "cross_cutting": [],
        "archived_phases": [],
        "archived_cross_cutting": [],
    }
    (tmp_path / "docs" / "tasklist.json").write_text(json.dumps(raw))
    return tmp_path


@pytest.fixture
def tmp_project_with_p6_s1_and_x1(tmp_path: Path) -> Path:
    """Mirror of `tmp_project_with_p6_s1` plus a cross-cutting `X1` row."""
    from tasktool import commands

    (tmp_path / "docs").mkdir()
    commands.cmd_config_init_local(repo_root=tmp_path)
    raw = {
        "project": "test",
        "schema_version": 2,
        "phases": [
            {
                "id": "P6",
                "title": "t",
                "created": "2026-05-23",
                "status": "ready",
                "slices": [
                    {"id": "S1", "title": "t", "created": "2026-05-23", "status": "ready"}
                ],
            }
        ],
        "cross_cutting": [
            {"id": "X1", "title": "t", "created": "2026-05-23", "status": "ready"}
        ],
        "archived_phases": [],
        "archived_cross_cutting": [],
    }
    (tmp_path / "docs" / "tasklist.json").write_text(json.dumps(raw))
    return tmp_path
