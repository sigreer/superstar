from __future__ import annotations
import unittest
from tasktool.ids import (
    IdParseError, parse_id, fully_qualify, kind_of, is_slice_id, split_qualified,
)

class ParseIdTests(unittest.TestCase):
    def test_phase(self):
        self.assertEqual(parse_id("P2"), ("phase", "P2"))
    def test_slice(self):
        self.assertEqual(parse_id("S3"), ("slice", "S3"))
    def test_slice_letter_suffix(self):
        self.assertEqual(parse_id("S5a"), ("slice", "S5a"))
    def test_task(self):
        self.assertEqual(parse_id("T1"), ("task", "T1"))
    def test_cross(self):
        self.assertEqual(parse_id("X4"), ("cross", "X4"))
    def test_qualified_phase_slice(self):
        self.assertEqual(parse_id("P2.S3"), ("slice", "P2.S3"))
    def test_qualified_phase_slice_task(self):
        self.assertEqual(parse_id("P2.S3.T1"), ("task", "P2.S3.T1"))
    def test_rejects_lowercase_phase(self):
        with self.assertRaises(IdParseError):
            parse_id("p2")
    def test_rejects_empty(self):
        with self.assertRaises(IdParseError):
            parse_id("")
    def test_rejects_garbage(self):
        with self.assertRaises(IdParseError):
            parse_id("P2..S1")

class KindTests(unittest.TestCase):
    def test_kind_of_short(self):
        self.assertEqual(kind_of("P2"), "phase")
        self.assertEqual(kind_of("S3a"), "slice")
        self.assertEqual(kind_of("T1"), "task")
        self.assertEqual(kind_of("X4"), "cross")
    def test_kind_of_qualified(self):
        self.assertEqual(kind_of("P2.S3.T1"), "task")
    def test_is_slice_id(self):
        self.assertTrue(is_slice_id("S3"))
        self.assertTrue(is_slice_id("P2.S3a"))
        self.assertFalse(is_slice_id("T1"))
        self.assertFalse(is_slice_id("P2"))

class QualifyTests(unittest.TestCase):
    def test_qualify_slice_under_phase(self):
        self.assertEqual(fully_qualify("S3", phase="P2"), "P2.S3")
    def test_qualify_task_under_slice(self):
        self.assertEqual(fully_qualify("T1", phase="P2", slice="S3"), "P2.S3.T1")
    def test_qualify_already_qualified(self):
        self.assertEqual(fully_qualify("P2.S3", phase="P9"), "P2.S3")

class SplitTests(unittest.TestCase):
    def test_split_task(self):
        self.assertEqual(split_qualified("P2.S3.T1"), ("P2", "S3", "T1"))
    def test_split_slice(self):
        self.assertEqual(split_qualified("P2.S3"), ("P2", "S3", None))
    def test_split_phase(self):
        self.assertEqual(split_qualified("P2"), ("P2", None, None))
    def test_split_short_phase(self):
        self.assertEqual(split_qualified("S3"), (None, "S3", None))
