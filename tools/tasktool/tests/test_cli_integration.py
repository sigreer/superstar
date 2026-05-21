from __future__ import annotations
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tasktool.model import Status
from tasktool.serialize import load_project

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_DIR = REPO_ROOT / "tools"
WRAPPER = REPO_ROOT / "tools" / "tasktool" / "tasktool"

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

    def test_repo_local_wrapper_works_without_pythonpath(self):
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [str(WRAPPER), "--help"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("tasktool", result.stdout)

import tempfile, json
from pathlib import Path

class _CliTmp:
    def __init__(self):
        self._td = tempfile.TemporaryDirectory()
        self.root = Path(self._td.name)
        (self.root / "docs").mkdir()
        r = run_cli("config", "init-local", cwd=self.root)
        assert r.returncode == 0, r.stderr
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

    def test_scheduling_commands_round_trip(self):
        t = _CliTmp()
        try:
            self.assertEqual(run_cli("init", "--project", "demo", cwd=t.root).returncode, 0)
            r = run_cli(
                "create", "phase", "--title", "P",
                "--planning", "docs/specs/p1-phase-plan.md",
                cwd=t.root,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            run_cli(
                "create", "slice", "P1", "--title", "S1",
                "--parallel-group", "bootstrap", cwd=t.root,
            )
            run_cli(
                "create", "slice", "P1", "--title", "S2",
                "--depends-on", "P1.S1", cwd=t.root,
            )
            run_cli("create", "slice", "P1", "--title", "S3", cwd=t.root)
            r = run_cli(
                "create", "slice", "P1", "--title", "S4",
                "--depends-on", "P1.S1", "--depends-on", "P1.S3",
                cwd=t.root,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("ready-slices", "P1", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("P1.S1", r.stdout)
            self.assertNotIn("P1.S2", r.stdout)
            self.assertNotIn("P1.S4", r.stdout)
            r = run_cli("ratify", "P1.S1", "--parallel-group", "core", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("schedule", "P1", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("P1.S2", r.stdout)
            self.assertIn("waiting_on=P1.S1", r.stdout)
            r = run_cli("deps", "P1.S2", "--remove", "P1.S1", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("ready-slices", "P1", cwd=t.root)
            self.assertIn("P1.S2", r.stdout)
            r = run_cli("phase-status", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Open phases", r.stdout)
        finally:
            t.cleanup()

    def test_close_cross_no_archive_keeps_visible(self):
        t = _CliTmp()
        try:
            self.assertEqual(run_cli("init", "--project", "demo", cwd=t.root).returncode, 0)
            run_cli("create", "cross", "--title", "visible", cwd=t.root)

            r = run_cli("close", "X1", "--no-archive", cwd=t.root)

            self.assertEqual(r.returncode, 0, r.stderr)
            project = load_project(t.root / "docs/tasklist.json")
            self.assertEqual(project.cross_cutting[0].id, "X1")
            self.assertEqual(project.cross_cutting[0].status, Status.DONE)
            self.assertEqual(project.archived_cross_cutting, [])
        finally:
            t.cleanup()

    def test_archive_cross_moves_done_item(self):
        t = _CliTmp()
        try:
            self.assertEqual(run_cli("init", "--project", "demo", cwd=t.root).returncode, 0)
            run_cli("create", "cross", "--title", "later", cwd=t.root)
            run_cli("close", "X1", "--no-archive", cwd=t.root)

            r = run_cli("archive-cross", "X1", cwd=t.root)

            self.assertEqual(r.returncode, 0, r.stderr)
            project = load_project(t.root / "docs/tasklist.json")
            self.assertEqual(project.cross_cutting, [])
            self.assertEqual(project.archived_cross_cutting[0].id, "X1")
        finally:
            t.cleanup()

    def test_list_kind_cross_excludes_archived_items(self):
        t = _CliTmp()
        try:
            self.assertEqual(run_cli("init", "--project", "demo", cwd=t.root).returncode, 0)
            run_cli("create", "cross", "--title", "archived", cwd=t.root)
            run_cli("create", "cross", "--title", "active", cwd=t.root)
            run_cli("close", "X1", cwd=t.root)

            r = run_cli("list", "--kind", "cross", cwd=t.root)

            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn("X1", r.stdout)
            self.assertIn("X2", r.stdout)
        finally:
            t.cleanup()

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
            run_cli("start", "P1.S1", cwd=t.root)
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
            run_cli("start", "P1.S1", cwd=t.root)
            r = run_cli("close", "P1.S1", "--skip-review-gate", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
        finally:
            t.cleanup()

    def test_close_repeated_refs_records_all_values(self):
        t = _CliTmp()
        try:
            run_cli("init", "--project", "demo", cwd=t.root)
            run_cli("create", "phase", "--title", "P", cwd=t.root)
            run_cli("create", "slice", "P1", "--title", "S", cwd=t.root)
            run_cli("start", "P1.S1", cwd=t.root)
            r = run_cli(
                "close", "P1.S1", "--skip-review-gate",
                "--refs", "docs/a.md", "--refs", "docs/b.md",
                cwd=t.root,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("show", "P1.S1", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("  - docs/a.md", r.stdout)
            self.assertIn("  - docs/b.md", r.stdout)
        finally:
            t.cleanup()

    def test_archive_phase_cli(self):
        t = _CliTmp()
        try:
            run_cli("init", "--project", "demo", cwd=t.root)
            run_cli("create", "phase", "--title", "Phase to archive", cwd=t.root)
            run_cli("create", "slice", "P1", "--title", "Slice", cwd=t.root)
            run_cli("start", "P1.S1", cwd=t.root)
            run_cli("close", "P1.S1", "--skip-review-gate", cwd=t.root)
            r = run_cli("archive-phase", "P1", "--skip-review-gate", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("review gate skipped for P1", r.stderr)
            self.assertTrue((t.root / "docs" / "archived-tasks").exists())
            md = list((t.root / "docs" / "archived-tasks").glob("P1-*.md"))
            self.assertEqual(len(md), 1)
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
            run_cli("start", "P2.S1", cwd=t.root)
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
            run_cli("start", "S1", cwd=t.root)
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
            run_cli("start", "P1.S1", cwd=t.root)
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


class BriefCliTests(unittest.TestCase):
    def test_brief_slice(self):
        t = _CliTmp()
        try:
            r = run_cli("init", "--project", "demo", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("create", "phase", "--title", "Phase", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("create", "slice", "P1", "--title", "Slice", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("create", "task", "P1.S1", "--title", "Task A", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = run_cli("brief", "P1.S1", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("# P1.S1 — Slice", r.stdout)
            self.assertIn("Parent phase: P1", r.stdout)
            self.assertIn("Open tasks:", r.stdout)
            self.assertIn("Task A", r.stdout)
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


def test_config_init_authority_writes_project_config(tmp_path):
    r = run_cli(
        "config", "init-authority",
        "--branch", "main",
        cwd=tmp_path,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads((tmp_path / ".tasktool" / "config.json").read_text())
    assert data["tasklist"]["mutation_mode"] == "authoritative-checkout"
    assert "authoritative_root" not in data["tasklist"]
    assert data["tasklist"]["authoritative_branch"] == "main"


def test_config_init_authority_ignores_ambient_ancestor_git_repo(tmp_path):
    ambient = tmp_path / "ambient"
    ambient.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=ambient, check=True, text=True, capture_output=True)
    project = ambient / "nested-project"
    project.mkdir()

    r = run_cli(
        "config", "init-authority",
        "--branch", "main",
        cwd=project,
    )

    assert r.returncode == 0, r.stdout + r.stderr
    assert (project / ".tasktool" / "config.json").exists()
    assert not (ambient / ".tasktool" / "config.json").exists()


def test_config_init_authority_rejects_wrong_checkout_branch(tmp_path):
    subprocess.run(["git", "init", "-b", "feature"], cwd=tmp_path, check=True, text=True, capture_output=True)
    r = run_cli(
        "config", "init-authority",
        "--branch", "main",
        cwd=tmp_path,
    )
    assert r.returncode == 1
    assert "expected branch main" in r.stderr
    assert not (tmp_path / ".tasktool" / "config.json").exists()
