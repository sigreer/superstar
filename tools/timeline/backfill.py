#!/usr/bin/env python3
"""Run-once legacy backfill: migrate pre-tasktool archive markdown into the
canonical 'Full phase JSON' blocks so timeline.py never needs legacy parsing.

Dry-run by default (prints a unified diff); --write applies. Never invoked by
timeline.py.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # tools/
    from timeline import extract
else:
    from . import extract

_PHASE_HEAD_RE = re.compile(
    r"^# (P\d+)\s+[—-]\s+(.+?)\s+✅\s+`?DONE (\d{4}-\d{2}-\d{2})`?", re.M)
_SLICE_HEAD_RE = re.compile(
    r"^## (S\d+)\s+[—-]\s+(.+?)\s+✅\s+`DONE (\d{4}-\d{2}-\d{2})`", re.M)
_MENTION_RE = re.compile(r"\b[pP](\d{1,2})(?:[.\-]?[sS](\d{1,2}))?\b")


@dataclass
class LegacySlice:
    sid: str
    title: str
    closed: str


@dataclass
class LegacyPhase:
    phase_id: str
    title: str
    closed: str
    slices: list


def parse_legacy(text):
    """Parse a pure-legacy archive markdown file. None if not legacy format."""
    head = _PHASE_HEAD_RE.search(text)
    if not head:
        return None
    slices = [LegacySlice(m.group(1), m.group(2), m.group(3))
              for m in _SLICE_HEAD_RE.finditer(text)]
    return LegacyPhase(head.group(1), head.group(2), head.group(3), slices)


def first_mentions(subjects):
    """subjects: iterable of (ts, subject). -> {key: first_ts} where key is
    'P<n>' or 'P<n>.S<m>'. A phase's first mention is the earliest of its own
    and any of its slices' mentions."""
    first = {}
    for ts, subject in subjects:
        for m in _MENTION_RE.finditer(subject):
            pid = f"P{m.group(1)}"
            keys = [pid]
            if m.group(2):
                keys.append(f"{pid}.S{int(m.group(2))}")
            for key in keys:
                if key not in first or ts < first[key]:
                    first[key] = ts
    return first


def commit_subjects(repo):
    out = extract.git(repo, "log", "--reverse", "--format=%ct%x01%s")
    pairs = []
    for line in out.splitlines():
        if "\x01" in line:
            ts, subject = line.split("\x01", 1)
            pairs.append((int(ts), subject))
    return pairs
