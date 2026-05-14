import json
from pathlib import Path

import pytest

import sys
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import importlib.util
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
external_reviewer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(external_reviewer)


def test_read_manifest_returns_none_for_missing(tmp_path):
    assert external_reviewer.read_manifest(tmp_path / "missing.json") is None


def test_write_then_read_manifest_roundtrips(tmp_path):
    path = tmp_path / "chain.json"
    data = {
        "schema_version": 1,
        "chain": "demo-post-slice",
        "kind": "post-slice",
        "target": "docs/plans/demo.md",
        "work_id": "P1.S1",
        "legacy_migrated": False,
        "rounds": [],
        "sweep_checkpoints": {"first-round": "pending", "final-ready": "pending"},
    }
    external_reviewer.write_manifest(path, data)
    loaded = external_reviewer.read_manifest(path)
    assert loaded == data


def test_read_manifest_rejects_newer_schema(tmp_path):
    path = tmp_path / "chain.json"
    path.write_text(json.dumps({"schema_version": 99}))
    with pytest.raises(external_reviewer.ManifestSchemaTooNew):
        external_reviewer.read_manifest(path)
