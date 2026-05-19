#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

python3 - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
config_path = root / ".version-bump.json"
config = json.loads(config_path.read_text(encoding="utf-8"))

declared = {entry["path"]: entry["field"] for entry in config["files"]}
payload_manifest = "plugins/superstar/.codex-plugin/plugin.json"
assert payload_manifest in declared, f"{payload_manifest} is not tracked by .version-bump.json"

versions = {}
for rel_path, field in declared.items():
    data = json.loads((root / rel_path).read_text(encoding="utf-8"))
    value = data
    for part in field.split("."):
        value = value[int(part)] if part.isdigit() else value[part]
    versions[rel_path] = value

unique = set(versions.values())
assert len(unique) == 1, f"declared versions drift: {versions}"

print(f"PASS: {len(versions)} declared version fields are in sync at {next(iter(unique))}")
PY
