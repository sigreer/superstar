#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

python3 - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
marketplace = json.loads((root / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
plugin = marketplace["plugins"][0]

assert plugin["name"] == "superstar", "local marketplace should expose superstar"
source_path = plugin["source"]["path"]
assert source_path == "./plugins/superstar", (
    f"local superstar-dev marketplace must expose the embedded Codex plugin payload, got {source_path!r}"
)

for required in (
    "plugins/superstar/.codex-plugin/plugin.json",
    "plugins/superstar/skills/using-superstar/SKILL.md",
    "plugins/superstar/hooks/hooks.json",
    "plugins/superstar/tools/tasktool/notify.py",
    "plugins/superstar/assets",
):
    path = root / required
    assert path.exists(), f"local marketplace source is missing {required}"
    assert not path.is_symlink(), f"local marketplace source must be materialized, got symlink: {required}"

print("PASS: local superstar-dev marketplace exposes the Codex plugin payload")
PY
