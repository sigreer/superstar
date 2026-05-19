from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _disable_notifications_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPERSTAR_NOTIFY_DISABLE", "1")
