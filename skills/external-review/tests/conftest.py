"""Per-test isolation for external-reviewer state files.

The bridge writes to ~/.config/superstar/reviewer-state.json[.lock] by default,
which is unwritable in restricted sandboxes (CI, reviewer environments). Pinning
AGENT_REVIEWER_STATE_FILE to tmp_path keeps each test self-contained.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_reviewer_state(tmp_path, monkeypatch):
    state_file = tmp_path / "reviewer-state.json"
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(state_file))
    yield
