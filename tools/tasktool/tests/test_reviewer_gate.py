# tools/tasktool/tests/test_reviewer_gate.py
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from tasktool.reviewer_gate import (
    discover_chain, read_latest_verdict, check_gate, GateError, GatePass,
)

def _write_chain(root: Path, name: str, verdict: str | None) -> Path:
    chain = root / "docs/reviewer" / name
    chain.mkdir(parents=True)
    manifest = {"rounds": [{"round": 1, "merged_verdict": verdict, "status": "ok"}]}
    (chain / "chain.json").write_text(json.dumps(manifest), encoding="utf-8")
    return chain

class DiscoveryTests(unittest.TestCase):
    def test_discover_by_explicit_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            chain = _write_chain(root, "p2-s1-post-slice", "ready")
            found = discover_chain(root, "P2.S1", "post-slice", explicit=chain)
            self.assertEqual(found, chain)

    def test_discover_by_id_suffix(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            chain = _write_chain(root, "foo-p2-s1-post-slice", "ready")
            found = discover_chain(root, "P2.S1", "post-slice")
            self.assertEqual(found, chain)

    def test_discover_zero_matches_raises(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(GateError):
                discover_chain(Path(td), "P2.S1", "post-slice")

    def test_discover_multiple_matches_raises(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_chain(root, "a-p2-s1-post-slice", "ready")
            _write_chain(root, "b-p2-s1-post-slice", "ready")
            with self.assertRaises(GateError):
                discover_chain(root, "P2.S1", "post-slice")

class VerdictTests(unittest.TestCase):
    def test_ready_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            chain = _write_chain(root, "p2-s1-post-slice", "ready")
            result = check_gate(root, "P2.S1", "post-slice")
            self.assertIsInstance(result, GatePass)
            self.assertEqual(result.verdict, "ready")

    def test_ready_with_small_edits_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_chain(root, "p2-s1-post-slice", "ready with small edits")
            result = check_gate(root, "P2.S1", "post-slice")
            self.assertEqual(result.verdict, "ready with small edits")

    def test_revise_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_chain(root, "p2-s1-post-slice", "revise")
            with self.assertRaises(GateError):
                check_gate(root, "P2.S1", "post-slice")

    def test_null_verdict_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_chain(root, "p2-s1-post-slice", None)
            with self.assertRaises(GateError):
                check_gate(root, "P2.S1", "post-slice")

class RelativeExplicitPathTests(unittest.TestCase):
    """F1 regression: relative --reviewer-chain paths must not raise ValueError."""

    def test_relative_explicit_path_resolves(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_chain(root, "p1-s1-post-slice", "ready")
            # Pass a relative path (relative to repo_root) as explicit
            rel = Path("docs/reviewer/p1-s1-post-slice")
            found = discover_chain(root, "P1.S1", "post-slice", explicit=rel)
            self.assertEqual(found, (root / rel).resolve())

    def test_relative_explicit_path_in_check_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_chain(root, "p1-s1-post-slice", "ready")
            rel = Path("docs/reviewer/p1-s1-post-slice")
            result = check_gate(root, "P1.S1", "post-slice", explicit=rel)
            self.assertEqual(result.verdict, "ready")

class BoundaryMatchTests(unittest.TestCase):
    """F2 regression: p1-s1 token must not match p1-s10-post-slice."""

    def test_p1_s1_does_not_match_p1_s10(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            correct = _write_chain(root, "p1-s1-post-slice", "ready")
            _write_chain(root, "p1-s10-post-slice", "ready")
            found = discover_chain(root, "P1.S1", "post-slice")
            self.assertEqual(found, correct)

    def test_p1_s10_does_not_match_p1_s1(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_chain(root, "p1-s1-post-slice", "ready")
            correct = _write_chain(root, "p1-s10-post-slice", "ready")
            found = discover_chain(root, "P1.S10", "post-slice")
            self.assertEqual(found, correct)

    def test_p1_s1_prefix_only_no_false_ambiguity(self):
        """p1-s1 and p1-s10 both exist; P1.S1 must resolve to exactly one."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_chain(root, "p1-s1-post-slice", "ready")
            _write_chain(root, "p1-s10-post-slice", "ready")
            # Should not raise — exactly one match expected.
            result = check_gate(root, "P1.S1", "post-slice")
            self.assertEqual(result.verdict, "ready")
