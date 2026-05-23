from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tasktool import notify


class NotifyTests(unittest.TestCase):
    def test_tasktool_status_dry_run_writes_message(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "notify.jsonl"
            with patch.dict(
                os.environ,
                {"SUPERSTAR_NOTIFY_DISABLE": "0", "SUPERSTAR_NOTIFY_DRY_RUN": "1", "SUPERSTAR_NOTIFY_LOG": str(log)},
            ):
                notify.notify_tasktool_status(
                    work_id="P1.S2",
                    kind="slice",
                    status="in_progress",
                    title="Queued slice",
                )
            event = json.loads(log.read_text(encoding="utf-8"))
        self.assertEqual(event["type"], "tasktool-status")
        self.assertEqual(event["message"], "P1.S2 in progress: Queued slice")

    def test_tasktool_status_cancelled_dispatches(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "notify.jsonl"
            with patch.dict(
                os.environ,
                {"SUPERSTAR_NOTIFY_DISABLE": "0", "SUPERSTAR_NOTIFY_DRY_RUN": "1", "SUPERSTAR_NOTIFY_LOG": str(log)},
            ):
                notify.notify_tasktool_status(
                    work_id="P1.S2",
                    kind="slice",
                    status="cancelled",
                    title="Abandoned slice",
                )
            event = json.loads(log.read_text(encoding="utf-8"))
        self.assertEqual(event["type"], "tasktool-status")
        self.assertEqual(event["status"], "cancelled")
        self.assertEqual(event["message"], "P1.S2 cancelled: Abandoned slice")

    def test_agent_ding_style_detects_codex(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "notify.jsonl"
            with patch.dict(
                os.environ,
                {
                    "SUPERSTAR_NOTIFY_DISABLE": "0",
                    "SUPERSTAR_NOTIFY_DRY_RUN": "1",
                    "SUPERSTAR_NOTIFY_LOG": str(log),
                    "CODEX_HOME": "/tmp/codex",
                },
                clear=True,
            ):
                notify.notify_agent_finished()
            event = json.loads(log.read_text(encoding="utf-8"))
        self.assertEqual(event["type"], "agent-ding")
        self.assertEqual(event["style"], "codex")

    def test_agent_ding_style_detects_claude(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "notify.jsonl"
            with patch.dict(
                os.environ,
                {
                    "SUPERSTAR_NOTIFY_DISABLE": "0",
                    "SUPERSTAR_NOTIFY_DRY_RUN": "1",
                    "SUPERSTAR_NOTIFY_LOG": str(log),
                    "CLAUDE_PLUGIN_ROOT": "/tmp/claude-plugin",
                },
                clear=True,
            ):
                notify.notify_agent_finished()
            event = json.loads(log.read_text(encoding="utf-8"))
        self.assertEqual(event["type"], "agent-ding")
        self.assertEqual(event["style"], "claude")

    def test_tasktool_queue_caps_overflow_with_summary(self):
        with tempfile.TemporaryDirectory() as td:
            queue_dir = Path(td) / "queue"
            events = [
                notify._tasktool_event(
                    work_id=f"X{i}",
                    kind="cross",
                    status="ready",
                    title=f"Item {i}",
                )
                for i in range(1, 6)
            ]
            with patch.dict(os.environ, {"SUPERSTAR_NOTIFY_QUEUE_DIR": str(queue_dir)}):
                for event in events:
                    notify._enqueue_event(event)
                queued = notify._read_queue()

        self.assertEqual(len(queued), 3)
        self.assertEqual([event["id"] for event in queued[:2]], ["X1", "X2"])
        self.assertEqual(queued[2]["type"], "tasktool-status")
        self.assertEqual(queued[2]["id"], "multiple")
        self.assertEqual(queued[2]["message"], "Multiple other events")

    def test_worker_drains_queued_events_in_order(self):
        with tempfile.TemporaryDirectory() as td:
            queue_dir = Path(td) / "queue"
            played: list[str] = []
            events = [
                notify._tasktool_event(
                    work_id=f"X{i}",
                    kind="cross",
                    status="ready",
                    title=f"Item {i}",
                )
                for i in range(1, 4)
            ]
            with patch.dict(os.environ, {"SUPERSTAR_NOTIFY_QUEUE_DIR": str(queue_dir)}):
                for event in events:
                    notify._enqueue_event(event)
                with patch.object(
                    notify,
                    "_play_event",
                    side_effect=lambda event: played.append(event["id"]),
                ):
                    notify._worker_loop()

        self.assertEqual(played, ["X1", "X2", "X3"])
