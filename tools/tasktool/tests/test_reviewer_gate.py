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
