"""Tests for round-1 prompt contract (Task 4.1).

The prompt must instruct the reviewer to tag findings with stable IDs
(F1, F2, F3, ...) that remain stable across iterative rounds, and to
mark severity inline with the canonical severity set.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


@pytest.fixture(scope="module")
def er():
    spec = importlib.util.spec_from_file_location(
        "external_reviewer", SCRIPTS / "external-reviewer.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["external_reviewer"] = module
    spec.loader.exec_module(module)
    return module


def test_prompt_mentions_stable_finding_ids(er):
    prompt = er.REVIEW_PROMPT
    assert "F1" in prompt
    assert "F2" in prompt
    assert "F3" in prompt


def test_prompt_requires_ids_remain_stable_across_rounds(er):
    prompt = er.REVIEW_PROMPT.lower()
    assert "stable" in prompt
    # Must call out that IDs persist across iterative review rounds.
    assert "subsequent rounds" in prompt or "across rounds" in prompt


def test_prompt_specifies_severity_set(er):
    prompt = er.REVIEW_PROMPT
    assert "Severity:" in prompt
    for level in ("blocking", "important", "minor", "nit"):
        assert level in prompt, f"missing severity level: {level}"


def test_prompt_renders_with_all_kinds(er, tmp_path):
    target = tmp_path / "doc.md"
    target.write_text("# doc\n")
    for kind in er.MODE_GUIDANCE:
        rendered = er.make_prompt(
            root=tmp_path,
            target=target,
            kind=kind,
            context=[],
            max_lines=10,
        )
        assert "F1" in rendered
        assert "Severity:" in rendered
