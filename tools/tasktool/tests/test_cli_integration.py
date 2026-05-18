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

class ReviewGateE2ETests(unittest.TestCase):
    def test_close_slice_requires_chain(self):
        t = _CliTmp()
        try:
            run_cli("init", "--project", "demo", cwd=t.root)
            run_cli("create", "phase", "--title", "P", cwd=t.root)
            run_cli("create", "slice", "P1", "--title", "S", cwd=t.root)
            r = run_cli("close", "P1.S1", cwd=t.root)
            self.assertEqual(r.returncode, 1)
            self.assertIn("review gate", r.stderr.lower())
        finally:
            t.cleanup()

    def test_close_slice_with_passing_chain(self):
        t = _CliTmp()
        try:
            run_cli("init", "--project", "demo", cwd=t.root)
            run_cli("create", "phase", "--title", "P", cwd=t.root)
            run_cli("create", "slice", "P1", "--title", "S", cwd=t.root)
            chain = t.root / "docs/reviewer/p1-s1-post-slice"
            chain.mkdir(parents=True)
            (chain / "chain.json").write_text(
                '{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}',
                encoding="utf-8",
            )
            r = run_cli("close", "P1.S1", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            t.cleanup()

    def test_skip_review_gate(self):
        t = _CliTmp()
        try:
            run_cli("init", "--project", "demo", cwd=t.root)
            run_cli("create", "phase", "--title", "P", cwd=t.root)
            run_cli("create", "slice", "P1", "--title", "S", cwd=t.root)
            r = run_cli("close", "P1.S1", "--skip-review-gate", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            t.cleanup()

    def test_short_id_close_resolves_to_qualified_for_gate(self):
        """F8 regression: closing a short slice ID must not match historical
        same-named chains under a different phase."""
        t = _CliTmp()
        try:
            run_cli("init", "--project", "demo", cwd=t.root)
            # Two phases each with their own S1.
            run_cli("create", "phase", "--title", "old", cwd=t.root)
            run_cli("create", "slice", "P1", "--title", "old s", cwd=t.root)
            run_cli("create", "phase", "--title", "new", cwd=t.root)
            run_cli("create", "slice", "P2", "--title", "new s", cwd=t.root)
            # A historical post-slice chain for P1.S1, plus the correct one for P2.S1.
            for name in ("p1-s1-post-slice", "p2-s1-post-slice"):
                chain = t.root / "docs/reviewer" / name
                chain.mkdir(parents=True)
                (chain / "chain.json").write_text(
                    '{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}',
                    encoding="utf-8",
                )
            # `close S1` would be ambiguous (two slices named S1 exist) — expect
            # an unambiguous-id error, not a phantom multi-chain match.
            r = run_cli("close", "S1", cwd=t.root)
            self.assertEqual(r.returncode, 1)
            self.assertIn("ambiguous", r.stderr.lower())
            # `close P2.S1` is unambiguous; the qualified id must hit p2-s1-post-slice
            # exclusively, not also match p1-s1-post-slice.
            r = run_cli("close", "P2.S1", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            t.cleanup()

    def test_short_id_unambiguous_in_project_but_chains_collide(self):
        """The exact F8 regression: the project has only one slice named S1 (so the
        short ID is unambiguous *in the data*), but a stale historical chain folder
        `p1-s1-post-slice` exists on disk alongside the current `p2-s1-post-slice`.
        Pre-fix, `close S1` tokenised to the short 's1' and matched both chain folders.
        Post-fix, the resolved qualified id `P2.S1` tokenises to 'p2-s1' which matches
        only the correct chain."""
        t = _CliTmp()
        try:
            run_cli("init", "--project", "demo", cwd=t.root)
            # Project currently knows only about P2 / P2.S1.
            run_cli("create", "phase", "--title", "p1-historical", cwd=t.root)
            # Mark P1 done immediately so the project effectively has one active slice.
            # (We don't create a P1 slice — only P1 the phase, so S1 in the project is unambiguous.)
            run_cli("create", "phase", "--title", "p2-current", cwd=t.root)
            run_cli("create", "slice", "P2", "--title", "current s", cwd=t.root)
            # Both chains exist on disk.
            for name in ("p1-s1-post-slice", "p2-s1-post-slice"):
                chain = t.root / "docs/reviewer" / name
                chain.mkdir(parents=True)
                (chain / "chain.json").write_text(
                    '{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}',
                    encoding="utf-8",
                )
            # `close S1` resolves to P2.S1 (the only S1 in the data), then the gate
            # searches with token 'p2-s1' and finds exactly one chain. Pre-fix this
            # would have searched with 's1' and matched both → spurious ambiguity.
            r = run_cli("close", "S1", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            t.cleanup()

    def test_close_slice_with_relative_reviewer_chain(self):
        """F1 regression: passing a relative --reviewer-chain path must not crash."""
        t = _CliTmp()
        try:
            run_cli("init", "--project", "demo", cwd=t.root)
            run_cli("create", "phase", "--title", "P", cwd=t.root)
            run_cli("create", "slice", "P1", "--title", "S", cwd=t.root)
            chain = t.root / "docs/reviewer/p1-s1-post-slice"
            chain.mkdir(parents=True)
            (chain / "chain.json").write_text(
                '{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}',
                encoding="utf-8",
            )
            # Pass a relative path — should succeed without ValueError traceback.
            r = run_cli("close", "P1.S1", "--reviewer-chain", "docs/reviewer/p1-s1-post-slice",
                        cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            t.cleanup()

class ImportCliTests(unittest.TestCase):
    def test_import_creates_tasklist_json(self):
        t = _CliTmp()
        try:
            (t.root / "TASKLIST.md").write_text(
                "## P2 — Demo 🚧 `IN PROGRESS`\n\n- ✅ **S1** `DONE 2026-01-01` — done.\n"
            )
            r = run_cli("import", str(t.root / "TASKLIST.md"), cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue((t.root / "docs" / "tasklist.json").exists())
            r2 = run_cli("show", "P2.S1", cwd=t.root)
            self.assertEqual(r2.returncode, 0, r2.stderr)
            self.assertIn("done", r2.stdout)
        finally:
            t.cleanup()

    def test_import_dry_run(self):
        t = _CliTmp()
        try:
            (t.root / "TASKLIST.md").write_text("## P2 — Demo 🚧 `IN PROGRESS`\n")
            r = run_cli("import", str(t.root / "TASKLIST.md"), "--dry-run", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse((t.root / "docs" / "tasklist.json").exists())
            self.assertIn('"id": "P2"', r.stdout)
        finally:
            t.cleanup()


class RenderCliTests(unittest.TestCase):
    def test_render_outputs_markdown(self):
        t = _CliTmp()
        try:
            r = run_cli("init", "--project", "demo", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("create", "phase", "--title", "Demo phase", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("render", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("## P1 — Demo phase", r.stdout)
        finally:
            t.cleanup()


class SetStatusTests(unittest.TestCase):
    """F3 regression: `set --status blocked` must be rejected by argparse."""

    def test_set_blocked_exits_nonzero_with_argparse_error(self):
        """blocked is no longer a valid choice; argparse must reject it cleanly."""
        t = _CliTmp()
        try:
            run_cli("init", "--project", "demo", cwd=t.root)
            run_cli("create", "phase", "--title", "P", cwd=t.root)
            run_cli("create", "slice", "P1", "--title", "S", cwd=t.root)
            r = run_cli("set", "P1.S1", "--status", "blocked", cwd=t.root)
            self.assertNotEqual(r.returncode, 0)
            # argparse exits with code 2 and prints to stderr — no Python traceback.
            self.assertNotIn("Traceback", r.stderr)
            self.assertNotIn("ValidationError", r.stderr)
        finally:
            t.cleanup()
