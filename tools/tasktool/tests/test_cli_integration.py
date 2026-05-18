from __future__ import annotations
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_DIR = REPO_ROOT / "tools"

def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "tasktool", *args],
        capture_output=True, text=True, cwd=cwd or REPO_ROOT, env=env,
    )

class SmokeTests(unittest.TestCase):
    def test_help_prints_and_exits_zero(self):
        result = run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("tasktool", result.stdout)

    def test_unknown_command_exits_two(self):
        result = run_cli("nope")
        self.assertEqual(result.returncode, 2)
