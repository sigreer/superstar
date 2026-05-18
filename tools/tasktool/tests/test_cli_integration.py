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

import tempfile, json
from pathlib import Path

class _CliTmp:
    def __init__(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        (self.root / "docs").mkdir()
    def cleanup(self):
        self._td.cleanup()

class CliEndToEndTests(unittest.TestCase):
    def test_init_then_create_then_show(self):
        t = _CliTmp()
        try:
            r = run_cli("init", "--project", "demo", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("create", "phase", "--title", "First", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("P1", r.stdout)
            r = run_cli("create", "slice", "P1", "--title", "Slice", cwd=t.root)
            self.assertIn("S1", r.stdout)
            r = run_cli("show", "P1", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("First", r.stdout)
            self.assertIn("S1", r.stdout)
        finally:
            t.cleanup()

    def test_validate_exits_zero_on_fresh_init(self):
        t = _CliTmp()
        try:
            run_cli("init", "--project", "demo", cwd=t.root)
            r = run_cli("validate", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            t.cleanup()

    def test_init_without_project_flag_works(self):
        """Spec acceptance path: `tasktool init && tasktool create phase ...` round-trips."""
        t = _CliTmp()
        try:
            r = run_cli("init", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("create", "phase", "--title", "First", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("show", "P1", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("First", r.stdout)
        finally:
            t.cleanup()

    def test_schema_is_valid_json(self):
        r = run_cli("schema")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertIn("properties", data)
