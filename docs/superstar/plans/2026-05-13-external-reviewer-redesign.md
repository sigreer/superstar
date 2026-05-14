# External-Reviewer Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `skills/external-review/scripts/external-reviewer.py` so review chains are incremental, durable, machine-readable, and support optional independent sweep reviewers — per `docs/superstar/specs/2026-05-13-external-reviewer-redesign-design.md`.

**Architecture:** A persistent `chain.json` manifest per review chain becomes the source of truth for round metadata. The script gains verdict parsing, work-ID-keyed chain folders, a resolution-artifact contract and gate, incremental round prompts with embedded diffs, optional session-resume placeholders, and Pass-3 independent sweep reviewers. Skill documentation is updated to match.

**Tech Stack:** Python 3.9+ standard library only (no external deps), `pytest` for tests, `git` CLI for diff and SHA capture.

---

## Pre-flight

- [ ] **Step 1: Verify working directory and branch**

Run:

```bash
cd /home/simon/Dev/sigreer/skills/superstar
git status --short
git rev-parse --abbrev-ref HEAD
```

Expected: clean tree, branch is a feature branch (not `main`). If on `main`, stop and create a branch via `superstar:using-git-worktrees`.

- [ ] **Step 2: Confirm test runner**

Run:

```bash
python3 -c "import pytest; print(pytest.__version__)"
```

Expected: prints a version string. If `ModuleNotFoundError`, install pytest:

```bash
python3 -m pip install --user pytest
```

- [ ] **Step 3: Set up the test directory**

Create the directory tests will live in:

```bash
mkdir -p skills/external-review/tests
touch skills/external-review/tests/__init__.py
```

Commit:

```bash
git add skills/external-review/tests/__init__.py
git commit -m "scaffold: tests dir for external-reviewer redesign"
```

---

## Slice 1: Chain manifest & verdict parsing

**Goal:** Introduce `chain.json` as the round-metadata source of truth, parse verdicts and finding counts from response text, and emit them in the JSON output. Backwards-compatible: legacy chains synthesize a manifest on first touch.

### Task 1.1: Manifest read/write helpers

**Files:**
- Create: `skills/external-review/tests/test_manifest.py`
- Modify: `skills/external-review/scripts/external-reviewer.py`

- [x] **Step 1: Write the failing tests**

`skills/external-review/tests/test_manifest.py`:

```python
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
```

- [x] **Step 2: Run the tests; confirm they fail**

```bash
python3 -m pytest skills/external-review/tests/test_manifest.py -v
```

Expected: 3 failures (`read_manifest`, `write_manifest`, `ManifestSchemaTooNew` all undefined).

- [x] **Step 3: Add manifest helpers to the script**

Append to `skills/external-review/scripts/external-reviewer.py` (after the existing module-level constants, before `repo_root()`):

```python
SUPPORTED_SCHEMA_VERSION = 1


class ManifestSchemaTooNew(Exception):
    """Raised when chain.json declares a schema_version newer than this script supports."""


def read_manifest(path: Path) -> dict | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    version = data.get("schema_version")
    if isinstance(version, int) and version > SUPPORTED_SCHEMA_VERSION:
        raise ManifestSchemaTooNew(
            f"chain.json schema_version {version} is newer than this script supports "
            f"(max {SUPPORTED_SCHEMA_VERSION}). Upgrade external-reviewer.py."
        )
    return data


def write_manifest(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
```

- [x] **Step 4: Run the tests; confirm they pass**

```bash
python3 -m pytest skills/external-review/tests/test_manifest.py -v
```

Expected: 3 passed.

- [x] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_manifest.py
git commit -m "feat(external-reviewer): chain.json read/write helpers with schema versioning"
```

### Task 1.2: Verdict parsing

**Files:**
- Create: `skills/external-review/tests/test_verdict.py`
- Modify: `skills/external-review/scripts/external-reviewer.py`

- [x] **Step 1: Write the failing tests**

`skills/external-review/tests/test_verdict.py`:

```python
from pathlib import Path
import sys, importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_verdict_ready():
    v, valid = er.parse_verdict("Findings: ok\n\nOverall verdict: ready\n")
    assert v == "ready"
    assert valid is True


def test_verdict_ready_with_small_edits_markdown():
    body = "**Overall verdict:** `ready with small edits`."
    v, valid = er.parse_verdict(body)
    assert v == "ready with small edits"
    assert valid is True


def test_verdict_revise_case_insensitive():
    v, valid = er.parse_verdict("OVERALL VERDICT: Revise")
    assert v == "revise"
    assert valid is True


def test_verdict_takes_last_match():
    body = "Overall verdict: ready\n\n...later...\n\nOverall verdict: revise"
    v, valid = er.parse_verdict(body)
    assert v == "revise"


def test_verdict_unknown_returns_invalid():
    v, valid = er.parse_verdict("Overall verdict: looks fine to me")
    assert v is None
    assert valid is False


def test_verdict_missing_returns_invalid():
    v, valid = er.parse_verdict("Some review prose with no verdict line.")
    assert v is None
    assert valid is False
```

- [x] **Step 2: Run the tests; confirm they fail**

```bash
python3 -m pytest skills/external-review/tests/test_verdict.py -v
```

Expected: 6 failures (`parse_verdict` undefined).

- [x] **Step 3: Add the verdict parser**

Append to `skills/external-review/scripts/external-reviewer.py`:

```python
VERDICT_VALUES = ("ready with small edits", "ready", "revise")
VERDICT_LINE_RE = re.compile(
    r"overall\s+verdict\s*[:\-]\s*[`*_\"']*\s*(ready with small edits|ready|revise)\s*[`*_\"'.]*",
    re.IGNORECASE,
)


def parse_verdict(text: str) -> tuple[str | None, bool]:
    matches = list(VERDICT_LINE_RE.finditer(text))
    if not matches:
        return None, False
    raw = matches[-1].group(1).strip().lower()
    if raw not in VERDICT_VALUES:
        return None, False
    return raw, True
```

Note: regex prefers `ready with small edits` over `ready` because of ordering in the alternation.

- [x] **Step 4: Run the tests; confirm they pass**

```bash
python3 -m pytest skills/external-review/tests/test_verdict.py -v
```

Expected: 6 passed.

- [x] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_verdict.py
git commit -m "feat(external-reviewer): parse_verdict with markdown/case tolerance"
```

### Task 1.3: Finding-count parsing

**Files:**
- Create: `skills/external-review/tests/test_findings.py`
- Modify: `skills/external-review/scripts/external-reviewer.py`

- [x] **Step 1: Write the failing tests**

`skills/external-review/tests/test_findings.py`:

```python
from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_heading_findings_counted():
    body = "## F1\nSeverity: blocking\n\n## F2\nSeverity: minor\n\n## F3\nSeverity: blocking"
    n, blocking = er.parse_findings(body)
    assert n == 3
    assert blocking == 2


def test_bullet_findings_counted():
    body = "- F1: something blocking (blocking)\n- F2 minor thing"
    n, blocking = er.parse_findings(body)
    assert n == 2
    assert blocking == 1


def test_no_findings_returns_zero():
    body = "Overall verdict: ready\n\nNo findings."
    n, blocking = er.parse_findings(body)
    assert n == 0
    assert blocking == 0


def test_unparseable_returns_none():
    body = "Reviewer crashed: connection reset"
    n, blocking = er.parse_findings(body)
    assert n is None
    assert blocking is None
```

- [x] **Step 2: Run the tests; confirm they fail**

```bash
python3 -m pytest skills/external-review/tests/test_findings.py -v
```

Expected: 4 failures.

- [x] **Step 3: Add the parser**

Append to `skills/external-review/scripts/external-reviewer.py`:

```python
HEADING_FINDING_RE = re.compile(r"^##\s+F\d+\b", re.MULTILINE)
BULLET_FINDING_RE = re.compile(r"^\s*[-*]?\s*\**F\d+\**[:\s\-]", re.MULTILINE)
BLOCKING_MARKER_RE = re.compile(r"(?:^|\s)\(blocking\)|^severity\s*:\s*blocking", re.IGNORECASE | re.MULTILINE)


def parse_findings(text: str) -> tuple[int | None, int | None]:
    if not text or text.strip() == "" or "reviewer crashed" in text.lower():
        return None, None
    heading_count = len(HEADING_FINDING_RE.findall(text))
    if heading_count > 0:
        n = heading_count
    else:
        n = len(BULLET_FINDING_RE.findall(text))
    blocking = len(BLOCKING_MARKER_RE.findall(text))
    return n, blocking
```

- [x] **Step 4: Run the tests; confirm they pass**

```bash
python3 -m pytest skills/external-review/tests/test_findings.py -v
```

Expected: 4 passed.

- [x] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_findings.py
git commit -m "feat(external-reviewer): parse_findings (heading + bullet, blocking count)"
```

### Task 1.4: Round-number derivation reads manifest first

**Files:**
- Create: `skills/external-review/tests/test_round_number.py`
- Modify: `skills/external-review/scripts/external-reviewer.py` (`next_round_number`)

- [x] **Step 1: Write the failing tests**

`skills/external-review/tests/test_round_number.py`:

```python
from pathlib import Path
import json, sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_no_chain_dir_round_is_one(tmp_path):
    assert er.next_round_number(tmp_path / "absent") == 1


def test_manifest_present_takes_precedence(tmp_path):
    d = tmp_path / "chain"; d.mkdir()
    er.write_manifest(d / "chain.json", {
        "schema_version": 1, "rounds": [{"round": 1}, {"round": 2}]
    })
    assert er.next_round_number(d) == 3


def test_legacy_dir_no_manifest_falls_back_to_filename_scan(tmp_path):
    d = tmp_path / "chain"; d.mkdir()
    (d / "r1-2026-05-01T0900-request.md").write_text("")
    (d / "r2-2026-05-02T0900-request.md").write_text("")
    assert er.next_round_number(d) == 3
```

- [x] **Step 2: Run the tests; confirm they fail**

```bash
python3 -m pytest skills/external-review/tests/test_round_number.py -v
```

Expected: test 2 fails (no manifest awareness), tests 1 and 3 may pass if current behavior already handles them.

- [x] **Step 3: Update `next_round_number`**

Replace the existing function:

```python
def next_round_number(chain_dir: Path) -> int:
    if not chain_dir.exists():
        return 1
    manifest = read_manifest(chain_dir / "chain.json")
    if manifest and isinstance(manifest.get("rounds"), list):
        return len(manifest["rounds"]) + 1
    return len(list(chain_dir.glob("r*-*-request.md"))) + 1
```

- [x] **Step 4: Run the tests**

```bash
python3 -m pytest skills/external-review/tests/test_round_number.py -v
```

Expected: 3 passed.

- [x] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_round_number.py
git commit -m "feat(external-reviewer): next_round_number consults chain.json"
```

### Task 1.5: Legacy manifest synthesis

**Files:**
- Create: `skills/external-review/tests/test_legacy_migration.py`
- Modify: `skills/external-review/scripts/external-reviewer.py`

- [x] **Step 1: Write the failing tests**

`skills/external-review/tests/test_legacy_migration.py`:

```python
from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_synthesize_manifest_from_legacy_files(tmp_path):
    d = tmp_path / "old-chain"; d.mkdir()
    (d / "r1-2026-04-01T0900-request.md").write_text("prompt body")
    (d / "r1-2026-04-01T0905-response.md").write_text(
        "## F1\nSeverity: blocking\n\nOverall verdict: revise\n"
    )
    (d / "r2-2026-04-02T1200-request.md").write_text("prompt body 2")

    manifest = er.synthesize_legacy_manifest(
        chain_dir=d, chain="old-chain", kind="post-slice",
        target="docs/plans/old.md", work_id="P1.S1",
    )

    assert manifest["legacy_migrated"] is True
    assert manifest["work_id"] == "P1.S1"
    assert len(manifest["rounds"]) == 2
    r1, r2 = manifest["rounds"]
    assert r1["legacy"] is True
    assert r1["verdict"] == "revise"
    assert r1["verdict_valid"] is True
    assert r1["findings_count"] == 1
    assert r1["blocking_findings_count"] == 1
    assert r1["head_sha_after_round"] is None
    assert r2["response"] is None  # only request file existed
```

- [x] **Step 2: Run the tests; confirm they fail**

```bash
python3 -m pytest skills/external-review/tests/test_legacy_migration.py -v
```

Expected: 1 failure.

- [x] **Step 3: Add the synthesizer**

Append to `skills/external-review/scripts/external-reviewer.py`:

```python
LEGACY_ROUND_FILE_RE = re.compile(r"^r(\d+)-([0-9T\-]+)-(request|response)\.md$")


def synthesize_legacy_manifest(
    *, chain_dir: Path, chain: str, kind: str, target: str, work_id: str | None
) -> dict:
    rounds_map: dict[int, dict] = {}
    for path in sorted(chain_dir.iterdir()):
        m = LEGACY_ROUND_FILE_RE.match(path.name)
        if not m:
            continue
        round_num = int(m.group(1))
        role = m.group(3)
        entry = rounds_map.setdefault(
            round_num,
            {
                "round": round_num,
                "request": None,
                "response": None,
                "resolution": None,
                "verdict": None,
                "verdict_valid": False,
                "findings_count": None,
                "blocking_findings_count": None,
                "head_sha_at_request": None,
                "head_sha_after_round": None,
                "worktree_dirty_at_request": None,
                "legacy": True,
            },
        )
        entry[role] = path.name
        if role == "response":
            body = path.read_text(encoding="utf-8", errors="replace")
            v, valid = parse_verdict(body)
            entry["verdict"], entry["verdict_valid"] = v, valid
            n, blocking = parse_findings(body)
            entry["findings_count"], entry["blocking_findings_count"] = n, blocking

    return {
        "schema_version": SUPPORTED_SCHEMA_VERSION,
        "chain": chain,
        "kind": kind,
        "target": target,
        "work_id": work_id,
        "legacy_migrated": True,
        "migrated_at": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rounds": [rounds_map[k] for k in sorted(rounds_map)],
        "sweep_checkpoints": {"first-round": "pending", "final-ready": "pending"},
    }
```

- [x] **Step 4: Run the tests; confirm they pass**

```bash
python3 -m pytest skills/external-review/tests/test_legacy_migration.py -v
```

Expected: 1 passed.

- [x] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_legacy_migration.py
git commit -m "feat(external-reviewer): synthesize_legacy_manifest from rN-* files"
```

### Task 1.6: Wire manifest into `main()` for single-reviewer rounds

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`main` function)
- Create: `skills/external-review/tests/test_main_round_writes_manifest.py`

- [x] **Step 1: Write the failing test**

`skills/external-review/tests/test_main_round_writes_manifest.py`:

```python
from pathlib import Path
import subprocess, sys, json, importlib.util, os

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


FAKE_REVIEWER = """#!/usr/bin/env bash
cat <<'EOF'
## F1
Severity: blocking
Stub finding.

Overall verdict: revise
EOF
"""


def test_main_writes_manifest_entry(tmp_path, monkeypatch):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    reviewer = repo / "stub-reviewer.sh"
    reviewer.write_text(FAKE_REVIEWER); reviewer.chmod(0o755)

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert payload["verdict"] == "revise"
    assert payload["verdict_valid"] is True
    assert payload["round"] == 1

    chain_dir = repo / "docs" / "reviewer" / "plan-plan"
    manifest = json.loads((chain_dir / "chain.json").read_text())
    assert manifest["schema_version"] == 1
    assert len(manifest["rounds"]) == 1
    assert manifest["rounds"][0]["verdict"] == "revise"
```

- [x] **Step 2: Run the test; confirm it fails**

```bash
python3 -m pytest skills/external-review/tests/test_main_round_writes_manifest.py -v
```

Expected: failure — no manifest written by `main()` yet.

- [x] **Step 3: Update `main()` to manage the manifest**

In `skills/external-review/scripts/external-reviewer.py`, locate the `main()` function. After `chain_dir.mkdir(parents=True, exist_ok=True)`, add manifest setup. After the reviewer runs and `write_review_artifact` is called, append the round entry to the manifest and write it back. Replace the body of `main()` from the line `chain_dir = (root / args.output_dir / chain_folder_name(target, args.kind)).resolve()` through the end of `main()` with:

```python
    chain_dir = (root / args.output_dir / chain_folder_name(target, args.kind)).resolve()
    chain_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = chain_dir / "chain.json"
    manifest = read_manifest(manifest_path)
    if manifest is None and any(chain_dir.glob("r*-*-request.md")):
        manifest = synthesize_legacy_manifest(
            chain_dir=chain_dir,
            chain=chain_folder_name(target, args.kind),
            kind=args.kind,
            target=rel_or_abs(target, root),
            work_id=None,
        )
        write_manifest(manifest_path, manifest)
    if manifest is None:
        manifest = {
            "schema_version": SUPPORTED_SCHEMA_VERSION,
            "chain": chain_folder_name(target, args.kind),
            "kind": args.kind,
            "target": rel_or_abs(target, root),
            "work_id": None,
            "legacy_migrated": False,
            "rounds": [],
            "sweep_checkpoints": {"first-round": "pending", "final-ready": "pending"},
        }
    round_num = next_round_number(chain_dir)
    timestamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    basename = f"r{round_num}-{timestamp}"
    prompt_file = chain_dir / f"{basename}-request.md"
    response_file = chain_dir / f"{basename}-response.md"
    prompt_text = make_prompt(
        root=root, target=target, kind=args.kind,
        context=context, max_lines=args.max_lines,
    )
    prompt_file.write_text(prompt_text, encoding="utf-8")

    try:
        result = run_reviewer(
            command_template=args.reviewer_cmd,
            prompt_file=prompt_file, prompt_text=prompt_text,
            target_file=target, kind=args.kind,
            prompt_transport=args.prompt_transport, timeout=args.timeout,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: reviewer command not found: {exc}", file=sys.stderr)
        print("Set AGENT_REVIEWER_CMD, e.g. AGENT_REVIEWER_CMD='reviewer {prompt_file}'", file=sys.stderr)
        return 127
    except subprocess.TimeoutExpired:
        print(f"ERROR: reviewer command timed out after {args.timeout}s", file=sys.stderr)
        return 124

    review_path = write_review_artifact(
        root=root, target=target, kind=args.kind,
        command_template=args.reviewer_cmd,
        prompt_file=prompt_file, response_file=response_file,
        round_num=round_num, result=result,
    )
    review_body = review_path.read_text(encoding="utf-8")
    verdict, verdict_valid = parse_verdict(review_body)
    findings_count, blocking_count = parse_findings(review_body)

    head_sha = current_head_sha(root)
    round_entry = {
        "round": round_num,
        "request": prompt_file.name,
        "response": response_file.name,
        "resolution": None,
        "head_sha_at_request": head_sha,
        "head_sha_after_round": head_sha,
        "worktree_dirty_at_request": is_dirty(root),
        "verdict": verdict,
        "verdict_valid": verdict_valid,
        "findings_count": findings_count,
        "blocking_findings_count": blocking_count,
    }
    manifest["rounds"].append(round_entry)
    write_manifest(manifest_path, manifest)

    review_rel = rel_or_abs(review_path, root)
    prompt_rel = rel_or_abs(prompt_file, root)
    if args.emit == "paths":
        print(f"REVIEW_PATH={review_rel}")
        print(f"PROMPT_PATH={prompt_rel}")
        print(f"ROUND={round_num}")
    elif args.emit == "review":
        print(review_body)
    elif args.emit == "json":
        print(json.dumps({
            "review_path": review_rel,
            "prompt_path": prompt_rel,
            "chain": manifest["chain"],
            "round": round_num,
            "kind": args.kind,
            "work_id": manifest.get("work_id"),
            "status": "ok" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "verdict": verdict,
            "verdict_valid": verdict_valid,
            "findings_count": findings_count,
            "blocking_findings_count": blocking_count,
            "review_depth": "standard",
            "reviewers": [{
                "role": "primary",
                "verdict": verdict,
                "verdict_valid": verdict_valid,
                "review_path": review_rel,
                "review": review_body,
            }],
            "merged_verdict": verdict,
            "merged_findings_path": None,
            "merged_findings": None,
            "review": review_body,
        }, indent=2))
    return result.returncode
```

Add the helper functions above `main()`:

```python
def current_head_sha(root: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True, capture_output=True, check=True,
        )
        return out.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None


def is_dirty(root: Path) -> bool:
    out = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        text=True, capture_output=True,
    )
    return bool(out.stdout.strip())
```

- [x] **Step 4: Run the test; confirm it passes**

```bash
python3 -m pytest skills/external-review/tests/test_main_round_writes_manifest.py -v
```

Expected: 1 passed.

- [x] **Step 5: Run the full test suite**

```bash
python3 -m pytest skills/external-review/tests/ -v
```

Expected: all passed.

- [x] **Step 6: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_main_round_writes_manifest.py
git commit -m "feat(external-reviewer): wire manifest + verdict/finding parsing into main()"
```

---

## Slice 2: --work-id and folder naming

**Goal:** `--work-id` is required for `post-slice` and `post-phase`; the chain folder slug encodes the work ID (dots → dashes); legacy folders are discovered and reused.

### Task 2.1: `--work-id` parsing and enforcement

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`parse_args`, `main`)
- Create: `skills/external-review/tests/test_work_id.py`

- [x] **Step 1: Write the failing tests**

`skills/external-review/tests/test_work_id.py`:

```python
from pathlib import Path
import subprocess, sys, os

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    reviewer = repo / "stub.sh"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)
    return repo


def test_post_slice_without_work_id_errors(tmp_path):
    repo = _init_repo(tmp_path)
    env = os.environ.copy(); env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True,
    )
    assert r.returncode == 2
    assert "--work-id" in r.stderr


def test_post_phase_without_work_id_errors(tmp_path):
    repo = _init_repo(tmp_path)
    env = os.environ.copy(); env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-phase", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True,
    )
    assert r.returncode == 2


def test_spec_without_work_id_ok(tmp_path):
    repo = _init_repo(tmp_path)
    env = os.environ.copy(); env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "spec", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
```

- [x] **Step 2: Run the tests; confirm they fail**

```bash
python3 -m pytest skills/external-review/tests/test_work_id.py -v
```

Expected: 2 failures (`post-slice`, `post-phase` not enforced); 1 pass.

- [x] **Step 3: Add `--work-id` to argparse and enforce**

In `parse_args()`, add:

```python
    parser.add_argument(
        "--work-id",
        default=None,
        help="Stable slice/phase ID (e.g. P2.S3 or P2). Required for post-slice/post-phase.",
    )
```

In `main()`, immediately after `args = parse_args()`, add:

```python
    if args.kind in ("post-slice", "post-phase") and not args.work_id:
        print(
            f"ERROR: --work-id is required for --kind {args.kind}. "
            "Use the slice ID (e.g. P2.S3) or phase ID (e.g. P2).",
            file=sys.stderr,
        )
        return 2
```

- [x] **Step 4: Run the tests; confirm they pass**

```bash
python3 -m pytest skills/external-review/tests/test_work_id.py -v
```

Expected: 3 passed.

- [x] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_work_id.py
git commit -m "feat(external-reviewer): enforce --work-id for post-slice/post-phase"
```

### Task 2.2: Folder slug encodes work ID

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`chain_folder_name`)
- Create: `skills/external-review/tests/test_chain_folder_name.py`

- [x] **Step 1: Write the failing tests**

```python
# skills/external-review/tests/test_chain_folder_name.py
from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_post_slice_includes_work_id_dotless(tmp_path):
    target = tmp_path / "2026-05-13-feature-plan.md"; target.write_text("x")
    assert er.chain_folder_name(target, "post-slice", "P2.S3") == "feature-plan-P2-S3-post-slice"


def test_post_phase_phase_id(tmp_path):
    target = tmp_path / "feature.md"; target.write_text("x")
    assert er.chain_folder_name(target, "post-phase", "P2") == "feature-P2-post-phase"


def test_spec_ignores_work_id(tmp_path):
    target = tmp_path / "feature.md"; target.write_text("x")
    assert er.chain_folder_name(target, "spec", "P2.S3") == "feature-spec"


def test_no_work_id_for_spec_unchanged(tmp_path):
    target = tmp_path / "feature.md"; target.write_text("x")
    assert er.chain_folder_name(target, "spec", None) == "feature-spec"
```

- [x] **Step 2: Run the tests; confirm they fail**

```bash
python3 -m pytest skills/external-review/tests/test_chain_folder_name.py -v
```

Expected: 4 failures (signature mismatch — function takes 2 args).

- [x] **Step 3: Update `chain_folder_name`**

Replace:

```python
def chain_folder_name(target: Path, kind: str, work_id: str | None = None) -> str:
    stem = DATE_PREFIX_RE.sub("", target.stem)
    base = slugify(stem)
    if kind in ("post-slice", "post-phase") and work_id:
        work_id_slug = work_id.replace(".", "-")
        return f"{base}-{work_id_slug}-{kind}"
    return f"{base}-{kind}"
```

Update every call site in `main()` to pass `args.work_id`:

```python
chain_dir = (root / args.output_dir / chain_folder_name(target, args.kind, args.work_id)).resolve()
```

(There are also call sites in the synthesized-manifest branch — update those too, passing `args.work_id`.)

- [x] **Step 4: Run the tests; confirm they pass**

```bash
python3 -m pytest skills/external-review/tests/test_chain_folder_name.py -v
python3 -m pytest skills/external-review/tests/ -v
```

Expected: all passed.

- [x] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_chain_folder_name.py
git commit -m "feat(external-reviewer): folder slug encodes work_id with dots replaced"
```

### Task 2.3: Legacy chain discovery

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Create: `skills/external-review/tests/test_legacy_discovery.py`

- [x] **Step 1: Write the failing tests**

`skills/external-review/tests/test_legacy_discovery.py`:

```python
from pathlib import Path
import sys, importlib.util, json
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_finds_legacy_folder_matching_old_naming(tmp_path):
    reviewer_root = tmp_path / "docs" / "reviewer"
    legacy = reviewer_root / "feature-post-slice"; legacy.mkdir(parents=True)
    (legacy / "r1-2026-04-01T0900-request.md").write_text("")

    found = er.discover_legacy_chain(
        reviewer_root=reviewer_root,
        target_stem="feature",
        kind="post-slice",
        new_slug="feature-P2-S3-post-slice",
    )
    assert found == legacy


def test_no_match_returns_none(tmp_path):
    root = tmp_path / "docs" / "reviewer"; root.mkdir(parents=True)
    assert er.discover_legacy_chain(root, "feature", "post-slice", "feature-P2-S3-post-slice") is None


def test_ambiguous_match_raises(tmp_path):
    root = tmp_path / "docs" / "reviewer"
    (root / "feature-post-slice").mkdir(parents=True)
    (root / "feature-post-slice").joinpath("r1-2026-04-01T0900-request.md").write_text("")
    (root / "feature-X-post-slice").mkdir()
    (root / "feature-X-post-slice").joinpath("r1-2026-04-01T0900-request.md").write_text("")

    # Both fold to base prefix "feature" — ambiguous when new naming arrives.
    import pytest
    with pytest.raises(er.AmbiguousLegacyChain):
        er.discover_legacy_chain(root, "feature", "post-slice", "feature-P2-S3-post-slice")
```

- [x] **Step 2: Run the tests; confirm they fail**

```bash
python3 -m pytest skills/external-review/tests/test_legacy_discovery.py -v
```

Expected: 3 failures (`discover_legacy_chain` and `AmbiguousLegacyChain` not defined).

- [x] **Step 3: Add legacy discovery**

```python
class AmbiguousLegacyChain(Exception):
    pass


def discover_legacy_chain(
    reviewer_root: Path,
    target_stem: str,
    kind: str,
    new_slug: str,
) -> Path | None:
    new_path = reviewer_root / new_slug
    if new_path.exists():
        return new_path
    if not reviewer_root.exists():
        return None
    legacy_old_name = f"{slugify(target_stem)}-{kind}"
    candidates = []
    for entry in reviewer_root.iterdir():
        if not entry.is_dir():
            continue
        if entry.name == legacy_old_name:
            candidates.append(entry)
        elif entry.name.startswith(f"{slugify(target_stem)}-") and entry.name.endswith(f"-{kind}"):
            # Legacy with embedded suffix (e.g. an interim variant). Treat as candidate.
            if entry.name != new_slug and not (entry / "chain.json").exists():
                candidates.append(entry)
    if not candidates:
        return None
    if len(candidates) > 1:
        names = ", ".join(c.name for c in candidates)
        raise AmbiguousLegacyChain(
            f"Multiple legacy chains match {slugify(target_stem)}-{kind}: {names}. "
            "Migrate manually or specify --chain-dir."
        )
    return candidates[0]
```

In `main()`, replace the line that computes `chain_dir` (and the immediate `chain_dir.mkdir(...)`) with:

```python
    new_slug = chain_folder_name(target, args.kind, args.work_id)
    reviewer_root = (root / args.output_dir).resolve()
    try:
        existing = discover_legacy_chain(
            reviewer_root=reviewer_root,
            target_stem=DATE_PREFIX_RE.sub("", target.stem),
            kind=args.kind,
            new_slug=new_slug,
        )
    except AmbiguousLegacyChain as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 5
    chain_dir = existing if existing else (reviewer_root / new_slug)
    chain_dir.mkdir(parents=True, exist_ok=True)
```

- [x] **Step 4: Run the tests; confirm they pass**

```bash
python3 -m pytest skills/external-review/tests/test_legacy_discovery.py -v
python3 -m pytest skills/external-review/tests/ -v
```

Expected: all passed.

- [x] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_legacy_discovery.py
git commit -m "feat(external-reviewer): discover and reuse legacy chain folders"
```

---

## Slice 3: Resolution artifact & gate

**Goal:** Parse `rN-resolution.md` per the contract; gate post-slice/post-phase round N+1 on its existence when the prior verdict was `revise` or unparseable; honour `--allow-missing-resolution`.

### Task 3.1: Resolution doc parser

**Files:**
- Create: `skills/external-review/tests/test_resolution.py`
- Modify: `skills/external-review/scripts/external-reviewer.py`

- [x] **Step 1: Write the failing tests**

```python
# skills/external-review/tests/test_resolution.py
from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


SAMPLE = """# Resolution for r1

## F1
Status: fixed
Evidence:
- Commit: abc1234
- Verification: pytest passed

Notes:
Did the thing.

## F2
Status: waived
Evidence:
- No code change
"""


def test_parse_resolution_extracts_statuses():
    result = er.parse_resolution(SAMPLE)
    assert result.status == "ok"
    assert result.findings == {"F1": "fixed", "F2": "waived"}


def test_parse_resolution_partial_when_missing_status():
    body = "## F1\nNotes only, no Status line"
    result = er.parse_resolution(body)
    assert result.status == "partial"
    assert "F1" in result.unmatched


def test_parse_resolution_unparseable_when_no_headings():
    body = "just prose, no headings"
    result = er.parse_resolution(body)
    assert result.status == "unparseable"
    assert result.findings == {}
```

- [x] **Step 2: Run the tests; confirm they fail**

```bash
python3 -m pytest skills/external-review/tests/test_resolution.py -v
```

Expected: 3 failures.

- [x] **Step 3: Add the parser**

```python
from dataclasses import dataclass, field


@dataclass
class ResolutionParseResult:
    status: str  # "ok" | "partial" | "unparseable"
    findings: dict[str, str] = field(default_factory=dict)
    unmatched: list[str] = field(default_factory=list)


RESOLUTION_HEADING_RE = re.compile(r"^##\s+(F\d+)\b", re.MULTILINE)
RESOLUTION_STATUS_RE = re.compile(
    r"^\s*status\s*:\s*(fixed|waived|deferred)\b", re.IGNORECASE | re.MULTILINE
)


def parse_resolution(text: str) -> ResolutionParseResult:
    headings = list(RESOLUTION_HEADING_RE.finditer(text))
    if not headings:
        return ResolutionParseResult(status="unparseable")

    findings: dict[str, str] = {}
    unmatched: list[str] = []
    spans = []
    for i, m in enumerate(headings):
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        spans.append((m.group(1), text[start:end]))

    for fid, body in spans:
        sm = RESOLUTION_STATUS_RE.search(body)
        if sm:
            findings[fid] = sm.group(1).lower()
        else:
            unmatched.append(fid)

    if not findings:
        return ResolutionParseResult(status="unparseable", unmatched=unmatched)
    status = "ok" if not unmatched else "partial"
    return ResolutionParseResult(status=status, findings=findings, unmatched=unmatched)
```

- [x] **Step 4: Run the tests; confirm they pass**

```bash
python3 -m pytest skills/external-review/tests/test_resolution.py -v
```

Expected: 3 passed.

- [x] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_resolution.py
git commit -m "feat(external-reviewer): parse_resolution (headings + status lines)"
```

### Task 3.2: Gate enforcement

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`main`, `parse_args`)
- Create: `skills/external-review/tests/test_resolution_gate.py`

- [x] **Step 1: Write the failing test**

```python
# skills/external-review/tests/test_resolution_gate.py
from pathlib import Path
import subprocess, sys, os, json

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _init_repo(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    reviewer = repo / "stub.sh"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: revise'\n")
    reviewer.chmod(0o755)
    return repo


def _run(repo, *args, env=None):
    base_env = os.environ.copy()
    if env: base_env.update(env)
    base_env.setdefault("AGENT_REVIEWER_CMD", str(repo / "stub.sh"))
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"), "review", *args],
        cwd=repo, env=base_env, capture_output=True, text=True,
    )


def test_post_slice_round_2_blocked_without_resolution(tmp_path):
    repo = _init_repo(tmp_path)
    r1 = _run(repo, "--kind", "post-slice", "--work-id", "P1.S1",
              "--file", "plan.md", "--emit", "json")
    assert r1.returncode == 0, r1.stderr

    r2 = _run(repo, "--kind", "post-slice", "--work-id", "P1.S1",
              "--file", "plan.md", "--emit", "json")
    assert r2.returncode == 3, r2.stderr + r2.stdout
    assert "r1-resolution.md" in r2.stderr


def test_post_slice_round_2_proceeds_with_waiver(tmp_path):
    repo = _init_repo(tmp_path)
    r1 = _run(repo, "--kind", "post-slice", "--work-id", "P1.S1",
              "--file", "plan.md", "--emit", "json")
    assert r1.returncode == 0

    r2 = _run(repo, "--kind", "post-slice", "--work-id", "P1.S1",
              "--file", "plan.md", "--emit", "json",
              "--allow-missing-resolution")
    assert r2.returncode == 0, r2.stderr


def test_spec_round_2_never_gated(tmp_path):
    repo = _init_repo(tmp_path)
    r1 = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
    r2 = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
    assert r2.returncode == 0, r2.stderr
```

- [x] **Step 2: Run the tests; confirm they fail**

```bash
python3 -m pytest skills/external-review/tests/test_resolution_gate.py -v
```

Expected: 3 failures.

- [x] **Step 3: Add the flag and the gate**

In `parse_args()`:

```python
    parser.add_argument(
        "--allow-missing-resolution",
        action="store_true",
        help="Waive the resolution-required gate for post-slice/post-phase round 2+.",
    )
```

In `main()`, immediately after computing `manifest` (and before computing `round_num`), add:

```python
    if (
        args.kind in ("post-slice", "post-phase")
        and manifest["rounds"]
        and not args.allow_missing_resolution
    ):
        prior = manifest["rounds"][-1]
        prior_round = prior["round"]
        prior_verdict = prior.get("merged_verdict") or prior.get("verdict")
        prior_valid = prior.get("verdict_valid", True)
        needs_resolution = (prior_verdict == "revise") or (prior_valid is False)
        if needs_resolution:
            resolution_path = chain_dir / f"r{prior_round}-resolution.md"
            if not resolution_path.exists():
                rel = rel_or_abs(resolution_path, root)
                response_rel = rel_or_abs(chain_dir / prior["response"], root) if prior.get("response") else "<missing>"
                print(
                    f"ERROR: Previous {args.kind} round returned revise, but {rel} is missing.\n\n"
                    f"Dispatch a fixer subagent with:\n"
                    f"  - previous response: {response_rel}\n"
                    f"  - required output:   {rel}\n\n"
                    f"Then re-run this review.\n"
                    f"Use --allow-missing-resolution only if you intentionally fixed outside the standard workflow.",
                    file=sys.stderr,
                )
                return 3
```

Then update the round entry to record:

```python
    resolution_file = chain_dir / f"r{round_num - 1}-resolution.md"
    resolution_attached = resolution_file.name if resolution_file.exists() else None
    resolution_waiver = args.allow_missing_resolution and round_num > 1 and not resolution_attached
    resolution_parse = None
    if resolution_attached:
        parsed = parse_resolution(resolution_file.read_text(encoding="utf-8"))
        resolution_parse = parsed.status

    round_entry = {
        "round": round_num,
        "request": prompt_file.name,
        "response": response_file.name,
        "resolution": resolution_attached,
        "resolution_parse_status": resolution_parse,
        "resolution_waiver": resolution_waiver,
        "head_sha_at_request": head_sha,
        "head_sha_after_round": head_sha,
        "worktree_dirty_at_request": is_dirty(root),
        "verdict": verdict,
        "verdict_valid": verdict_valid,
        "findings_count": findings_count,
        "blocking_findings_count": blocking_count,
    }
```

And in the JSON emit branch, add fields:

```python
    "resolution_parse_status": resolution_parse,
    "resolution_waiver": resolution_waiver,
```

- [x] **Step 4: Run the tests; confirm they pass**

```bash
python3 -m pytest skills/external-review/tests/test_resolution_gate.py -v
python3 -m pytest skills/external-review/tests/ -v
```

Expected: all passed.

- [x] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_resolution_gate.py
git commit -m "feat(external-reviewer): resolution-required gate with --allow-missing-resolution"
```

---

## Slice 4: Incremental prompt mode & finding-ID contract

**Goal:** Round 1 prompt instructs the reviewer to emit stable `F<n>` IDs and a severity tag. Round 2+ prompts switch to incremental mode: include chain summary, prior-round response (or merged findings if present), resolution doc, and explicit guidance against reopening broad review. `--mode auto|broad|incremental` overrides.

### Task 4.1: Prompt contract — stable finding IDs

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`REVIEW_PROMPT`)

- [ ] **Step 1: Update the round-1 prompt contract**

Replace the existing `REVIEW_PROMPT` constant with:

```python
REVIEW_PROMPT = """You are acting as an independent senior engineering reviewer.

Review stance:
- Lead with findings, ordered by severity.
- Focus on correctness, consistency, implementation risk, missing acceptance
  gates, vague handoffs, ungrounded assumptions, unverified claims, and drift
  from the codebase.
- Give exact file/line references when possible.
- If the document is sound, say that clearly and list residual risks.
- Keep the review actionable. Avoid broad rewrites unless the current structure
  creates concrete risk.

Repository root:
{repo_root}

Target kind:
{kind}

Review mode:
{mode_guidance}

Target document:
{target_file}

Additional context files:
{context_files}

Review output contract:
1. Findings
   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
     stable if this review is iterated in subsequent rounds.
   - Mark severity inline: `Severity: blocking | important | minor | nit`.
2. Open questions / assumptions
3. Suggested document edits
4. Verification gaps / commands that should be run, if any
5. Overall verdict: one of "ready", "ready with small edits", or "revise"

Read the files from disk. Do not rely only on the snippets in this prompt.
"""
```

- [ ] **Step 2: Sanity-check prompt rendering**

```bash
python3 -c "
import importlib.util, sys
from pathlib import Path
SCRIPTS = Path('skills/external-review/scripts').resolve()
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('er', SCRIPTS / 'external-reviewer.py')
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)
print('OK' if 'F1' in er.REVIEW_PROMPT else 'FAIL')
"
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py
git commit -m "feat(external-reviewer): round-1 prompt requires stable F<n> finding IDs"
```

### Task 4.2: `--mode` flag and round-aware prompt mode

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`parse_args`, `make_prompt`, `main`)
- Create: `skills/external-review/tests/test_mode.py`

- [ ] **Step 1: Write the failing test**

```python
# skills/external-review/tests/test_mode.py
from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_resolve_mode_round_1_auto_is_broad():
    assert er.resolve_mode("auto", round_num=1) == "broad"


def test_resolve_mode_round_n_auto_is_incremental():
    assert er.resolve_mode("auto", round_num=2) == "incremental"
    assert er.resolve_mode("auto", round_num=5) == "incremental"


def test_resolve_mode_explicit_broad_round_n():
    assert er.resolve_mode("broad", round_num=3) == "broad"


def test_resolve_mode_incremental_round_1_raises():
    import pytest
    with pytest.raises(ValueError):
        er.resolve_mode("incremental", round_num=1)
```

- [ ] **Step 2: Run the tests; confirm they fail**

```bash
python3 -m pytest skills/external-review/tests/test_mode.py -v
```

Expected: 4 failures.

- [ ] **Step 3: Add the resolver and flag**

In `parse_args()`:

```python
    parser.add_argument(
        "--mode",
        choices=["auto", "broad", "incremental"],
        default="auto",
        help="Override the round-1-vs-N prompt mode. Default 'auto'.",
    )
```

Add the resolver:

```python
def resolve_mode(mode: str, *, round_num: int) -> str:
    if mode == "incremental" and round_num == 1:
        raise ValueError("--mode incremental is not valid on round 1")
    if mode == "auto":
        return "broad" if round_num == 1 else "incremental"
    return mode
```

- [ ] **Step 4: Run the tests; confirm they pass**

```bash
python3 -m pytest skills/external-review/tests/test_mode.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_mode.py
git commit -m "feat(external-reviewer): --mode flag + resolve_mode(round_num)"
```

### Task 4.3: Build incremental-round prompt body

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`make_prompt`, add `build_incremental_preamble`)
- Create: `skills/external-review/tests/test_incremental_prompt.py`

- [ ] **Step 1: Write the failing test**

```python
# skills/external-review/tests/test_incremental_prompt.py
from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_incremental_preamble_includes_chain_summary_and_resolution(tmp_path):
    manifest = {
        "schema_version": 1, "chain": "demo-P1-S1-post-slice",
        "rounds": [
            {"round": 1, "verdict": "revise", "verdict_valid": True,
             "findings_count": 3, "blocking_findings_count": 1,
             "response": "r1-response.md"},
        ],
    }
    chain_dir = tmp_path / "chain"; chain_dir.mkdir()
    (chain_dir / "r1-response.md").write_text("## F1\nSeverity: blocking\nOverall verdict: revise")
    (chain_dir / "r1-resolution.md").write_text("# Resolution for r1\n\n## F1\nStatus: fixed\n")

    preamble = er.build_incremental_preamble(
        manifest=manifest, chain_dir=chain_dir, round_num=2,
        resolution_waiver=False, legacy_first_round=False,
    )

    assert "round 2 of demo-P1-S1-post-slice" in preamble
    assert "F1" in preamble
    assert "Resolution report" in preamble
    assert "Status: fixed" in preamble


def test_incremental_preamble_with_waiver_text(tmp_path):
    manifest = {"chain": "demo", "rounds": [{"round": 1, "response": "r1-response.md", "verdict": "revise", "verdict_valid": True}]}
    chain_dir = tmp_path / "chain"; chain_dir.mkdir()
    (chain_dir / "r1-response.md").write_text("Overall verdict: revise")
    preamble = er.build_incremental_preamble(
        manifest=manifest, chain_dir=chain_dir, round_num=2,
        resolution_waiver=True, legacy_first_round=False,
    )
    assert "MISSING — explicitly waived" in preamble
```

- [ ] **Step 2: Run the tests; confirm they fail**

```bash
python3 -m pytest skills/external-review/tests/test_incremental_prompt.py -v
```

Expected: 2 failures.

- [ ] **Step 3: Add the preamble builder**

```python
def build_incremental_preamble(
    *,
    manifest: dict,
    chain_dir: Path,
    round_num: int,
    resolution_waiver: bool,
    legacy_first_round: bool,
) -> str:
    chain = manifest.get("chain", "<unknown chain>")
    prior_rounds = manifest.get("rounds", [])
    summary_rows = ["| round | verdict | findings | blocking |", "|---|---|---|---|"]
    for r in prior_rounds:
        summary_rows.append(
            f"| {r['round']} | {r.get('merged_verdict') or r.get('verdict')} "
            f"| {r.get('findings_count')} | {r.get('blocking_findings_count')} |"
        )

    prior = prior_rounds[-1] if prior_rounds else None
    prior_response_text = ""
    merged_findings_file = chain_dir / f"r{round_num - 1}-merged-findings.md"
    if merged_findings_file.exists():
        prior_response_text = merged_findings_file.read_text(encoding="utf-8")
        prior_source = "merged findings (authoritative)"
    elif prior and prior.get("response"):
        prior_response_text = (chain_dir / prior["response"]).read_text(encoding="utf-8")
        prior_source = "primary reviewer response"
    else:
        prior_source = "no prior response available"

    resolution_file = chain_dir / f"r{round_num - 1}-resolution.md"
    if resolution_file.exists():
        resolution_text = resolution_file.read_text(encoding="utf-8")
    elif resolution_waiver:
        resolution_text = "MISSING — explicitly waived by caller via --allow-missing-resolution"
    elif legacy_first_round:
        resolution_text = (
            "MISSING — chain migrated from legacy artifacts; please verify whether "
            "changes occurred from the diff below."
        )
    else:
        resolution_text = "MISSING — please verify whether changes occurred."

    return f"""You are continuing an existing review chain. This is round {round_num} of {chain}.

In incremental mode:
- Verify whether prior findings are resolved per the resolution report below.
- Reuse the existing finding IDs (F1, F2, …). If a prior finding is resolved,
  mark it RESOLVED in your findings list with its original ID. If still
  unresolved, keep its ID.
- Only introduce new finding IDs for genuine regressions caused by the fix, or
  blocking issues clearly missed in earlier rounds. Do not reopen broad review
  unless prior fixes changed broad architecture.

Review chain summary:
{chr(10).join(summary_rows)}

Prior-round findings ({prior_source}):

{prior_response_text}

Resolution report for prior round:

{resolution_text}
"""
```

- [ ] **Step 4: Wire the preamble into `make_prompt`**

Update `make_prompt`'s signature and body:

```python
def make_prompt(
    *,
    root: Path,
    target: Path,
    kind: str,
    context: list[Path],
    max_lines: int,
    mode: str,
    incremental_preamble: str | None = None,
) -> str:
    context_display = "\n".join(f"- {rel_or_abs(p, root)}" for p in context) or "- none"
    body = REVIEW_PROMPT.format(
        repo_root=root,
        kind=kind,
        mode_guidance=MODE_GUIDANCE[kind],
        target_file=rel_or_abs(target, root),
        context_files=context_display,
    )
    if mode == "incremental" and incremental_preamble:
        body = incremental_preamble + "\n---\n\n" + body
    body += "\n\n## Target Preview\n\n"
    body += numbered_preview(target, root, max_lines=max_lines)
    if context:
        body += "\n## Context Previews\n\n"
        for ctx in context:
            body += numbered_preview(ctx, root, max_lines=max(80, max_lines // 3))
    return body
```

And in `main()`, replace the existing `prompt_text = make_prompt(...)` block with:

```python
    mode = resolve_mode(args.mode, round_num=round_num)
    incremental_preamble = None
    if mode == "incremental":
        incremental_preamble = build_incremental_preamble(
            manifest=manifest,
            chain_dir=chain_dir,
            round_num=round_num,
            resolution_waiver=resolution_waiver if "resolution_waiver" in locals() else False,
            legacy_first_round=manifest.get("legacy_migrated", False)
                and not any(r.get("head_sha_after_round") for r in manifest["rounds"]),
        )

    prompt_text = make_prompt(
        root=root, target=target, kind=args.kind,
        context=context, max_lines=args.max_lines,
        mode=mode, incremental_preamble=incremental_preamble,
    )
```

(Note: `resolution_waiver` is computed later in `main()`; if not yet bound here, default to `False`. The conditional above handles that. Reorder so `resolution_waiver` is computed before this block — move the resolution-attached/waiver computation up immediately after the gate logic.)

- [ ] **Step 5: Run the tests**

```bash
python3 -m pytest skills/external-review/tests/test_incremental_prompt.py -v
python3 -m pytest skills/external-review/tests/ -v
```

Expected: all passed.

- [ ] **Step 6: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_incremental_prompt.py
git commit -m "feat(external-reviewer): incremental round preamble (chain summary + prior + resolution)"
```

---

## Slice 5: Diff embedding

**Goal:** Round 2+ prompts include a diff between the previous round's HEAD and the current HEAD. Default scope is broad for `post-slice`/`post-phase` (all tracked changes) and document-only for spec/plan/etc. `--base-ref`, `--no-diff`, `--changed-files`, `--max-diff-lines` give override control. Dirty worktrees and untracked files are surfaced.

### Task 5.1: Compute diff and untracked listing

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Create: `skills/external-review/tests/test_diff.py`

- [ ] **Step 1: Write the failing tests**

```python
# skills/external-review/tests/test_diff.py
from pathlib import Path
import subprocess, sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def _repo(tmp_path):
    repo = tmp_path / "r"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    return repo


def test_diff_between_two_commits(tmp_path):
    repo = _repo(tmp_path)
    (repo / "a.txt").write_text("one\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "1"], check=True)
    base = er.current_head_sha(repo)
    (repo / "a.txt").write_text("one\ntwo\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "2"], check=True)

    out = er.compute_diff_section(repo, base_ref=base, paths=None, max_lines=200)
    assert "+two" in out
    assert "Worktree status: clean" in out


def test_untracked_files_surfaced(tmp_path):
    repo = _repo(tmp_path)
    (repo / "a.txt").write_text("one\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "1"], check=True)
    base = er.current_head_sha(repo)
    (repo / "new.txt").write_text("brand new\nfile\n")

    out = er.compute_diff_section(repo, base_ref=base, paths=None, max_lines=200)
    assert "Untracked files" in out
    assert "new.txt" in out
    assert "brand new" in out
    assert "Worktree status: dirty" in out


def test_no_diff_when_base_ref_none(tmp_path):
    repo = _repo(tmp_path)
    out = er.compute_diff_section(repo, base_ref=None, paths=None, max_lines=200)
    assert "not available" in out
```

- [ ] **Step 2: Run the tests; confirm they fail**

```bash
python3 -m pytest skills/external-review/tests/test_diff.py -v
```

Expected: 3 failures.

- [ ] **Step 3: Implement `compute_diff_section`**

```python
def compute_diff_section(
    root: Path,
    *,
    base_ref: str | None,
    paths: list[str] | None,
    max_lines: int,
) -> str:
    if base_ref is None:
        return "Changes since prior round: not available for this round (no base ref).\n"

    diff_args = ["git", "-C", str(root), "diff", f"{base_ref}..HEAD"]
    if paths:
        diff_args.append("--")
        diff_args.extend(paths)
    diff_proc = subprocess.run(diff_args, text=True, capture_output=True)
    diff_text = diff_proc.stdout

    status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain"],
        text=True, capture_output=True,
    ).stdout
    dirty = bool(status.strip())

    parts = [f"Worktree status: {'dirty' if dirty else 'clean'}", "", "## git diff base..HEAD", ""]
    parts.append(_cap_lines(diff_text, max_lines))

    if dirty:
        head_diff = subprocess.run(
            ["git", "-C", str(root), "diff", "HEAD"] + (["--"] + paths if paths else []),
            text=True, capture_output=True,
        ).stdout
        parts += ["", "## git diff HEAD (uncommitted)", "", _cap_lines(head_diff, max_lines)]

    untracked = [line[3:] for line in status.splitlines() if line.startswith("?? ")]
    if untracked:
        parts += ["", "## Untracked files", ""]
        for rel in untracked:
            abs_path = root / rel
            try:
                content = abs_path.read_text(encoding="utf-8")
                preview = _cap_lines(content, max_lines)
                parts += [f"### {rel}", "", "```", preview, "```", ""]
            except (UnicodeDecodeError, OSError):
                parts += [f"- {rel} (omitted: binary or unreadable)"]

    return "\n".join(parts) + "\n"


def _cap_lines(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[:max_lines] + [f"[truncated: {len(lines) - max_lines} additional lines]"])
```

- [ ] **Step 4: Run the tests; confirm they pass**

```bash
python3 -m pytest skills/external-review/tests/test_diff.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_diff.py
git commit -m "feat(external-reviewer): compute_diff_section (diff + dirty + untracked)"
```

### Task 5.2: CLI flags `--base-ref`, `--no-diff`, `--changed-files`, `--max-diff-lines`, and wiring

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`parse_args`, `main`, `build_incremental_preamble`)

- [ ] **Step 1: Add the flags**

In `parse_args()`:

```python
    parser.add_argument("--base-ref", default=None,
                        help="Override auto-computed diff base for this round.")
    parser.add_argument("--no-diff", action="store_true",
                        help="Suppress diff embedding.")
    parser.add_argument("--changed-files", nargs="+", default=None,
                        help="Limit embedded diff to these paths (overrides auto discovery).")
    parser.add_argument("--max-diff-lines", type=int, default=2000,
                        help="Cap diff size. Truncation marker is embedded if exceeded.")
```

- [ ] **Step 2: Decide the diff scope per kind**

Add helper:

```python
def default_diff_paths(kind: str, target: Path, context: list[Path], root: Path) -> list[str] | None:
    if kind in ("post-slice", "post-phase"):
        return None  # all tracked changes
    files = [rel_or_abs(target, root)] + [rel_or_abs(c, root) for c in context]
    return files
```

- [ ] **Step 3: Wire into `main()`**

After resolving the mode and before building the preamble:

```python
    diff_section = ""
    if mode == "incremental" and not args.no_diff:
        if args.base_ref:
            base_ref = args.base_ref
            base_source = "explicit"
        else:
            prior_with_sha = next(
                (r for r in reversed(manifest["rounds"]) if r.get("head_sha_after_round")),
                None,
            )
            base_ref = prior_with_sha["head_sha_after_round"] if prior_with_sha else None
            base_source = "auto" if base_ref else "unavailable"
        paths = args.changed_files or default_diff_paths(args.kind, target, context, root)
        diff_section = compute_diff_section(
            root, base_ref=base_ref, paths=paths, max_lines=args.max_diff_lines,
        )
    elif args.no_diff:
        diff_section = "Changes since prior round: diff suppressed via --no-diff.\n"
        base_ref = None
        base_source = "suppressed"
    else:
        base_ref = None
        base_source = None
```

Extend `build_incremental_preamble` to take and append `diff_section`. Update the call:

```python
        incremental_preamble = build_incremental_preamble(
            manifest=manifest,
            chain_dir=chain_dir,
            round_num=round_num,
            resolution_waiver=resolution_waiver,
            legacy_first_round=...,
            diff_section=diff_section,
        )
```

And in `build_incremental_preamble`, append:

```python
    return f"""...preceding sections...

Changes since prior round:

{diff_section or 'Changes since prior round: not available for this round.'}
"""
```

(Make `diff_section` an optional kwarg with default `""`.)

Record on the round entry:

```python
    round_entry["base_ref"] = base_ref
    round_entry["base_ref_source"] = base_source
    round_entry["diff_included"] = bool(diff_section) and not args.no_diff
```

And expose in JSON:

```python
    "diff_included": round_entry["diff_included"],
    "base_ref": base_ref,
```

- [ ] **Step 4: Run the full suite**

```bash
python3 -m pytest skills/external-review/tests/ -v
```

Expected: all passed (no regressions; existing tests still pass).

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py
git commit -m "feat(external-reviewer): --base-ref / --no-diff / --changed-files / --max-diff-lines"
```

---

## Slice 6: Pass 2 — session-resume placeholders

**Goal:** Extend the existing `AGENT_REVIEWER_CMD` template substitution so a provider-specific wrapper can persist and resume reviewer sessions. The script provides stable paths and ensures the parent directory exists; it never reads `session.state`.

### Task 6.1: Substitute new placeholders

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`run_reviewer`)
- Create: `skills/external-review/tests/test_placeholders.py`

- [ ] **Step 1: Write the failing test**

```python
# skills/external-review/tests/test_placeholders.py
from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_substitute_all_new_placeholders(tmp_path):
    chain_dir = tmp_path / "chain"; chain_dir.mkdir()
    prev = chain_dir / "r1-response.md"; prev.write_text("x")
    res = chain_dir / "r1-resolution.md"; res.write_text("y")
    session = chain_dir / "session.state"

    out = er.expand_command_template(
        "echo {chain_dir} {round} {previous_response} {resolution_file} {session_file}",
        prompt_file=chain_dir / "r2-request.md",
        prompt_text="prompt",
        target_file=Path("plan.md"),
        kind="post-slice",
        chain_dir=chain_dir,
        round_num=2,
        previous_response=prev,
        resolution_file=res,
        session_file=session,
    )
    assert str(chain_dir) in out
    assert "2" in out
    assert str(prev) in out
    assert str(res) in out
    assert str(session) in out
```

- [ ] **Step 2: Run the test; confirm it fails**

```bash
python3 -m pytest skills/external-review/tests/test_placeholders.py -v
```

Expected: failure (`expand_command_template` not defined).

- [ ] **Step 3: Extract template expansion**

Refactor the substitution block in `run_reviewer` into a helper:

```python
def expand_command_template(
    template: str,
    *,
    prompt_file: Path,
    prompt_text: str,
    target_file: Path,
    kind: str,
    chain_dir: Path,
    round_num: int,
    previous_response: Path | None,
    resolution_file: Path | None,
    session_file: Path,
) -> str:
    values = {
        "prompt_file": shlex.quote(str(prompt_file)),
        "prompt_text": shlex.quote(prompt_text),
        "target_file": shlex.quote(str(target_file)),
        "kind": shlex.quote(kind),
        "chain_dir": shlex.quote(str(chain_dir)),
        "round": str(round_num),
        "previous_response": shlex.quote(str(previous_response)) if previous_response else "",
        "resolution_file": shlex.quote(str(resolution_file)) if resolution_file else "",
        "session_file": shlex.quote(str(session_file)),
    }
    return template.format(**values)
```

Update `run_reviewer` to accept and pass these args, calling `expand_command_template` instead of the inline `.format(**values)`. Ensure `session_file = chain_dir / "session.state"` is computed once in `main()` and its parent directory is guaranteed to exist (it is — chain_dir is mkdir'd already).

- [ ] **Step 4: Run the tests**

```bash
python3 -m pytest skills/external-review/tests/test_placeholders.py -v
python3 -m pytest skills/external-review/tests/ -v
```

Expected: all passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_placeholders.py
git commit -m "feat(external-reviewer): {chain_dir}/{round}/{previous_response}/{resolution_file}/{session_file} placeholders"
```

---

## Slice 7: Pass 3 — review depth and independent sweeps

**Goal:** `--review-depth standard|thorough|exhaustive`, `--independent-reviewers <int>`, `--sweep-policy <first-round|final-ready|both|never>` control whether independent sweep reviewers run alongside the primary. Anchoring is avoided: sweep reviewers never see primary findings on their first pass. Findings are merged and a merged verdict gates progress. Sweep-checkpoint state in the manifest prevents duplicate firings.

### Task 7.1: Depth/policy flags and defaults

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`parse_args`, add helpers)
- Create: `skills/external-review/tests/test_review_depth.py`

- [ ] **Step 1: Write the failing tests**

```python
# skills/external-review/tests/test_review_depth.py
from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_resolve_depth_standard_no_sweeps():
    plan = er.plan_sweeps(depth="standard", policy=None, count=None,
                          round_num=1, checkpoints={"first-round": "pending", "final-ready": "pending"},
                          primary_verdict_pre_run=None)
    assert plan.sweep_count == 0


def test_resolve_depth_thorough_first_round():
    plan = er.plan_sweeps(depth="thorough", policy=None, count=None,
                          round_num=1, checkpoints={"first-round": "pending", "final-ready": "pending"},
                          primary_verdict_pre_run=None)
    assert plan.sweep_count == 1
    assert plan.checkpoint == "first-round"


def test_thorough_final_ready_fires_once(tmp_path):
    # round 2, prior primary returned 'ready' for the first time; final-ready not yet done.
    plan = er.plan_sweeps(depth="thorough", policy=None, count=None,
                          round_num=2, checkpoints={"first-round": "completed", "final-ready": "pending"},
                          primary_verdict_pre_run="ready")
    assert plan.sweep_count == 1
    assert plan.checkpoint == "final-ready"


def test_final_ready_skipped_when_already_completed():
    plan = er.plan_sweeps(depth="thorough", policy=None, count=None,
                          round_num=3, checkpoints={"first-round": "completed", "final-ready": "completed"},
                          primary_verdict_pre_run="ready")
    assert plan.sweep_count == 0


def test_exhaustive_first_round_two_sweeps():
    plan = er.plan_sweeps(depth="exhaustive", policy=None, count=None,
                          round_num=1, checkpoints={"first-round": "pending", "final-ready": "pending"},
                          primary_verdict_pre_run=None)
    assert plan.sweep_count == 2
```

- [ ] **Step 2: Run the tests; confirm they fail**

```bash
python3 -m pytest skills/external-review/tests/test_review_depth.py -v
```

Expected: 5 failures.

- [ ] **Step 3: Add the flags and the planner**

In `parse_args()`:

```python
    parser.add_argument("--review-depth", choices=["standard", "thorough", "exhaustive"],
                        default="standard")
    parser.add_argument("--independent-reviewers", type=int, default=None)
    parser.add_argument("--sweep-policy",
                        choices=["first-round", "final-ready", "both", "never"], default=None)
```

Add the planner:

```python
@dataclass
class SweepPlan:
    sweep_count: int
    checkpoint: str | None  # "first-round" | "final-ready" | None


DEPTH_DEFAULTS = {
    "standard":   {"policy": "never",       "count_first": 0, "count_final": 0},
    "thorough":   {"policy": "both",        "count_first": 1, "count_final": 1},
    "exhaustive": {"policy": "both",        "count_first": 2, "count_final": 2},
}


def plan_sweeps(
    *,
    depth: str,
    policy: str | None,
    count: int | None,
    round_num: int,
    checkpoints: dict[str, str],
    primary_verdict_pre_run: str | None,
) -> SweepPlan:
    cfg = DEPTH_DEFAULTS[depth]
    effective_policy = policy or cfg["policy"]
    if effective_policy == "never":
        return SweepPlan(sweep_count=0, checkpoint=None)

    if round_num == 1 and effective_policy in ("first-round", "both"):
        if checkpoints.get("first-round") == "completed":
            return SweepPlan(sweep_count=0, checkpoint=None)
        n = count if count is not None else cfg["count_first"]
        return SweepPlan(sweep_count=n, checkpoint="first-round")

    if (
        round_num > 1
        and effective_policy in ("final-ready", "both")
        and primary_verdict_pre_run in ("ready", "ready with small edits")
        and checkpoints.get("final-ready") != "completed"
    ):
        n = count if count is not None else cfg["count_final"]
        return SweepPlan(sweep_count=n, checkpoint="final-ready")

    return SweepPlan(sweep_count=0, checkpoint=None)
```

- [ ] **Step 4: Run the tests; confirm they pass**

```bash
python3 -m pytest skills/external-review/tests/test_review_depth.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_review_depth.py
git commit -m "feat(external-reviewer): plan_sweeps + depth/policy/count flags"
```

### Task 7.2: Dispatch primary + sweep reviewers, namespaced filenames

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`main`)
- Create: `skills/external-review/tests/test_sweep_dispatch.py`

- [ ] **Step 1: Write the failing test**

```python
# skills/external-review/tests/test_sweep_dispatch.py
from pathlib import Path
import subprocess, sys, os, json

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _repo(tmp_path):
    repo = tmp_path / "r"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    rev = repo / "stub.sh"; rev.write_text(
        "#!/usr/bin/env bash\n"
        "echo \"## F1\nSeverity: minor\nOverall verdict: ready with small edits\"\n"
    )
    rev.chmod(0o755)
    return repo


def test_thorough_round_1_writes_primary_and_sweep_files(tmp_path):
    repo = _repo(tmp_path)
    env = os.environ.copy(); env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--work-id", "P1.S1",
         "--file", "plan.md", "--review-depth", "thorough", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 0, r.stderr

    chain = repo / "docs" / "reviewer" / "plan-P1-S1-post-slice"
    primary = list(chain.glob("r1-*-primary-response.md"))
    sweeps = list(chain.glob("r1-*-sweep1-response.md"))
    merged = chain / "r1-merged-findings.md"
    assert primary
    assert sweeps
    assert merged.exists()

    payload = json.loads(r.stdout)
    assert payload["review_depth"] == "thorough"
    assert len(payload["reviewers"]) == 2
    assert payload["reviewers"][0]["role"] == "primary"
    assert payload["reviewers"][1]["role"] == "sweep"
    assert payload["merged_findings_path"] is not None
```

- [ ] **Step 2: Run the test; confirm it fails**

```bash
python3 -m pytest skills/external-review/tests/test_sweep_dispatch.py -v
```

Expected: failure.

- [ ] **Step 3: Refactor a single-reviewer invocation into a helper, then dispatch the plan**

Add a helper that runs one reviewer and writes one pair of files:

```python
@dataclass
class ReviewerResult:
    role: str            # "primary" | "sweep"
    sweep_index: int | None
    request_path: Path
    response_path: Path
    review_body: str
    verdict: str | None
    verdict_valid: bool
    returncode: int


def run_one_reviewer(
    *,
    role: str,
    sweep_index: int | None,
    chain_dir: Path,
    round_num: int,
    timestamp: str,
    prompt_text: str,
    args,
    target: Path,
    namespaced: bool,
) -> ReviewerResult:
    suffix = ""
    if namespaced:
        suffix = f"-{role}" if role == "primary" else f"-sweep{sweep_index}"
    basename = f"r{round_num}-{timestamp}{suffix}"
    request_path = chain_dir / f"{basename}-request.md"
    response_path = chain_dir / f"{basename}-response.md"
    request_path.write_text(prompt_text, encoding="utf-8")
    session_file = chain_dir / ("session.state" if role == "primary" else f"sweep{sweep_index}.session.state")

    result = run_reviewer(
        command_template=args.reviewer_cmd,
        prompt_file=request_path, prompt_text=prompt_text,
        target_file=target, kind=args.kind,
        prompt_transport=args.prompt_transport, timeout=args.timeout,
        chain_dir=chain_dir, round_num=round_num,
        previous_response=None, resolution_file=None,
        session_file=session_file,
    )
    write_review_artifact(
        root=repo_root(), target=target, kind=args.kind,
        command_template=args.reviewer_cmd,
        prompt_file=request_path, response_file=response_path,
        round_num=round_num, result=result,
    )
    body = response_path.read_text(encoding="utf-8")
    verdict, valid = parse_verdict(body)
    return ReviewerResult(
        role=role, sweep_index=sweep_index,
        request_path=request_path, response_path=response_path,
        review_body=body, verdict=verdict, verdict_valid=valid,
        returncode=result.returncode,
    )
```

(Update `run_reviewer` to accept the new placeholder kwargs and pass through to `expand_command_template` from Task 6.1.)

In `main()`, after computing `mode`, `prompt_text`, and the sweep plan:

```python
    primary_verdict_pre_run = None
    if manifest["rounds"]:
        primary_verdict_pre_run = manifest["rounds"][-1].get("merged_verdict") or manifest["rounds"][-1].get("verdict")
    sweep_plan = plan_sweeps(
        depth=args.review_depth, policy=args.sweep_policy, count=args.independent_reviewers,
        round_num=round_num,
        checkpoints=manifest.setdefault("sweep_checkpoints", {"first-round": "pending", "final-ready": "pending"}),
        primary_verdict_pre_run=primary_verdict_pre_run,
    )
    namespaced = sweep_plan.sweep_count > 0

    primary = run_one_reviewer(
        role="primary", sweep_index=None,
        chain_dir=chain_dir, round_num=round_num, timestamp=timestamp,
        prompt_text=prompt_text, args=args, target=target, namespaced=namespaced,
    )
    sweeps: list[ReviewerResult] = []
    for k in range(1, sweep_plan.sweep_count + 1):
        # Sweep reviewers receive the *same* prompt as primary on first-round (no anchoring).
        # For final-ready, prompt is round-1-style broad to act as a fresh sweep.
        sweep_prompt = prompt_text
        if sweep_plan.checkpoint == "final-ready":
            sweep_prompt = make_prompt(
                root=root, target=target, kind=args.kind,
                context=context, max_lines=args.max_lines,
                mode="broad", incremental_preamble=None,
            )
        sweeps.append(run_one_reviewer(
            role="sweep", sweep_index=k,
            chain_dir=chain_dir, round_num=round_num, timestamp=timestamp,
            prompt_text=sweep_prompt, args=args, target=target, namespaced=True,
        ))
```

- [ ] **Step 4: Compute merged findings and verdict**

Add helpers:

```python
def compute_merged_verdict(reviewer_results: list[ReviewerResult]) -> str | None:
    if any((not r.verdict_valid) or r.verdict == "revise" for r in reviewer_results):
        return "revise"
    if any(r.verdict == "ready with small edits" for r in reviewer_results):
        return "ready with small edits"
    if all(r.verdict == "ready" for r in reviewer_results):
        return "ready"
    return None


def write_merged_findings(
    *,
    chain_dir: Path, round_num: int,
    primary: ReviewerResult, sweeps: list[ReviewerResult],
) -> Path:
    parts = [f"# Merged findings for r{round_num}\n", "## Primary\n", primary.review_body, ""]
    for s in sweeps:
        parts += [f"## Sweep {s.sweep_index}\n", _renamespace_finding_ids(s.review_body, s.sweep_index), ""]
    path = chain_dir / f"r{round_num}-merged-findings.md"
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def _renamespace_finding_ids(body: str, sweep_index: int) -> str:
    # Rewrite `## F<n>` and bullet `F<n>` to `S<k>.F<n>` to avoid collision with primary IDs.
    body = re.sub(r"^(##\s+)F(\d+)\b", rf"\1S{sweep_index}.F\2", body, flags=re.MULTILINE)
    body = re.sub(r"(\bF)(\d+)\b", rf"S{sweep_index}.F\2", body)
    return body
```

In `main()`, after dispatching:

```python
    reviewer_results = [primary] + sweeps
    if sweeps:
        merged_path = write_merged_findings(
            chain_dir=chain_dir, round_num=round_num, primary=primary, sweeps=sweeps,
        )
        merged_verdict = compute_merged_verdict(reviewer_results)
        if sweep_plan.checkpoint:
            manifest["sweep_checkpoints"][sweep_plan.checkpoint] = "completed"
    else:
        merged_path = None
        merged_verdict = primary.verdict
```

- [ ] **Step 5: Write enriched manifest entry + JSON output**

Replace the single-reviewer `round_entry` block with:

```python
    round_entry = {
        "round": round_num,
        "reviewers": [
            {
                "role": r.role,
                "sweep_group": r.sweep_index,
                "parent_round": round_num,
                "request": r.request_path.name,
                "response": r.response_path.name,
                "verdict": r.verdict,
                "verdict_valid": r.verdict_valid,
            }
            for r in reviewer_results
        ],
        "merged_verdict": merged_verdict,
        "merged_findings": merged_path.name if merged_path else None,
        "resolution": resolution_attached,
        "resolution_parse_status": resolution_parse,
        "resolution_waiver": resolution_waiver,
        "head_sha_at_request": head_sha,
        "head_sha_after_round": current_head_sha(root),
        "worktree_dirty_at_request": is_dirty(root),
        "verdict": primary.verdict,
        "verdict_valid": primary.verdict_valid,
        "findings_count": parse_findings(primary.review_body)[0],
        "blocking_findings_count": parse_findings(primary.review_body)[1],
        "base_ref": base_ref,
        "base_ref_source": base_source,
        "diff_included": bool(diff_section) and not args.no_diff,
    }
    manifest["rounds"].append(round_entry)
    write_manifest(manifest_path, manifest)
```

Update the JSON emit branch to produce the Pass-3 schema:

```python
    elif args.emit == "json":
        merged_findings_text = merged_path.read_text(encoding="utf-8") if merged_path else None
        top_review = merged_findings_text or primary.review_body
        print(json.dumps({
            "review_path": rel_or_abs(primary.response_path, root),
            "prompt_path": rel_or_abs(primary.request_path, root),
            "chain": manifest["chain"],
            "round": round_num,
            "kind": args.kind,
            "work_id": manifest.get("work_id"),
            "status": "ok" if primary.returncode == 0 else "failed",
            "returncode": primary.returncode,
            "verdict": primary.verdict,
            "verdict_valid": primary.verdict_valid,
            "findings_count": round_entry["findings_count"],
            "blocking_findings_count": round_entry["blocking_findings_count"],
            "resolution_parse_status": resolution_parse,
            "resolution_waiver": resolution_waiver,
            "diff_included": round_entry["diff_included"],
            "base_ref": base_ref,
            "worktree_dirty_at_request": round_entry["worktree_dirty_at_request"],
            "review_depth": args.review_depth,
            "reviewers": [
                {
                    "role": r.role,
                    "verdict": r.verdict,
                    "verdict_valid": r.verdict_valid,
                    "review_path": rel_or_abs(r.response_path, root),
                    "review": r.review_body,
                }
                for r in reviewer_results
            ],
            "merged_verdict": merged_verdict,
            "merged_findings_path": rel_or_abs(merged_path, root) if merged_path else None,
            "merged_findings": merged_findings_text,
            "review": top_review,
        }, indent=2))
```

Also persist `work_id` into the manifest on first creation:

```python
    manifest["work_id"] = args.work_id or manifest.get("work_id")
```

- [ ] **Step 6: Run the tests**

```bash
python3 -m pytest skills/external-review/tests/test_sweep_dispatch.py -v
python3 -m pytest skills/external-review/tests/ -v
```

Expected: all passed.

- [ ] **Step 7: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_sweep_dispatch.py
git commit -m "feat(external-reviewer): dispatch primary + sweep reviewers; merged findings + verdict"
```

### Task 7.3: Gate uses merged_verdict when present

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (gate logic in `main`)
- Create: `skills/external-review/tests/test_gate_merged_verdict.py`

- [ ] **Step 1: Write the failing test**

```python
# skills/external-review/tests/test_gate_merged_verdict.py
import subprocess, sys, os, json
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def test_gate_fires_when_merged_verdict_is_revise_even_if_primary_ready(tmp_path):
    repo = tmp_path / "r"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    # Stub reviewer that alternates: primary returns ready, sweep returns revise.
    rev = repo / "stub.sh"; rev.write_text(
        '#!/usr/bin/env bash\n'
        'PROMPT="$1"\n'
        'if grep -q "sweep" "$PROMPT" 2>/dev/null; then\n'
        '  echo "## F1\\nSeverity: blocking\\nOverall verdict: revise"\n'
        'else\n'
        '  echo "Overall verdict: ready"\n'
        'fi\n'
    ); rev.chmod(0o755)

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = f'{rev} {{prompt_file}}'
    # Round 1: thorough → sweep returns revise → merged_verdict revise.
    r1 = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--work-id", "P1.S1",
         "--file", "plan.md", "--review-depth", "thorough", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert r1.returncode == 0
    p1 = json.loads(r1.stdout)
    assert p1["merged_verdict"] == "revise"

    # Round 2 without resolution: gate must fire.
    r2 = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--work-id", "P1.S1",
         "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert r2.returncode == 3, r2.stderr
```

- [ ] **Step 2: Run the test; confirm it fails (or already passes if gate logic was correct)**

```bash
python3 -m pytest skills/external-review/tests/test_gate_merged_verdict.py -v
```

If it passes, the gate is already merged-verdict-aware from Task 3.2's `prior.get("merged_verdict") or prior.get("verdict")` expression. If it fails, refine the gate. Either way, the test now documents the intended behavior.

- [ ] **Step 3: Confirm the gate condition explicitly considers `verdict_valid`**

Verify the gate fragment in `main()` reads:

```python
        prior_verdict = prior.get("merged_verdict") or prior.get("verdict")
        prior_valid = prior.get("verdict_valid", True)
        needs_resolution = (prior_verdict == "revise") or (prior_valid is False)
```

(This was added in Task 3.2 — confirm it's still in place after the Pass-3 refactor in 7.2.)

- [ ] **Step 4: Run the full suite**

```bash
python3 -m pytest skills/external-review/tests/ -v
```

Expected: all passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_gate_merged_verdict.py
git commit -m "test(external-reviewer): gate fires on merged_verdict=revise from sweep"
```

---

## Slice 8: Skill documentation updates

**Goal:** `external-review/SKILL.md` and `subagent-driven-development/SKILL.md` accurately describe the new flow.

### Task 8.1: Update `external-review/SKILL.md`

**Files:**
- Modify: `skills/external-review/SKILL.md`

- [ ] **Step 1: Update the "How a round runs" block**

Replace the existing example with:

````markdown
## How a round runs

```bash
python3 scripts/external-reviewer.py review \
    --kind <spec|plan|post-slice|post-phase> \
    --file <path/to/target.md> \
    --work-id <P2.S3 | P2>   # required for post-slice / post-phase
    [--context <path>]... \
    [--review-depth thorough] \
    --emit json
```

- Output folder: `docs/reviewer/<target-stem-no-date>[-<work-id-dotless>]-<kind>/`
- Round number, base ref, and prior verdict are read from `chain.json` in the chain folder.
- Each round emits `r{N}-{timestamp}-request.md` and `r{N}-{timestamp}-response.md`. When `--review-depth thorough` or `exhaustive` runs sweep reviewers, filenames become `r{N}-{ts}-primary-*.md` and `r{N}-{ts}-sweep{K}-*.md`, plus a `r{N}-merged-findings.md`.
- `--emit json` returns the structured payload described in "Reading the response". Always use `--emit json` from this skill — agents consume the JSON, not paths or human prose.
````

- [ ] **Step 2: Replace the "Reading the response" section**

````markdown
## Reading the response

The JSON output (always use `--emit json`) is the source of truth. Agents MUST consult:

- `merged_verdict` — authoritative for gating slice/phase progress.
- `verdict_valid` — if `false`, treat as `revise`.
- `resolution_parse_status` — `ok` | `partial` | `unparseable` | `null`.
- `reviewers[]` — per-reviewer verdicts and review text.
- `review` — for multi-reviewer rounds, this contains the merged findings; for single-reviewer rounds, the primary review.

Verdict values: `ready`, `ready with small edits`, `revise` (or `null` if unparseable).
````

- [ ] **Step 3: Add a "Round mode" section**

````markdown
## Round mode

- **Round 1** is **broad**: the reviewer reads target and context from scratch and emits findings tagged with stable IDs (`F1`, `F2`, …).
- **Round N+** is **incremental** by default: the prompt embeds the prior round's findings (or merged findings), the fixer's `r{N-1}-resolution.md`, and a diff. The reviewer verifies whether prior findings are resolved, reusing the same IDs.
- `--mode broad` forces round-1-style on a later round (rare; only when fixes changed broad architecture).
- `--mode incremental` on round 1 is rejected.
````

- [ ] **Step 4: Add a "Review depth" section**

````markdown
## Review depth

`--review-depth` controls whether independent sweep reviewers run alongside the primary chain reviewer at high-risk checkpoints.

- `standard` (CLI default; cheapest). One primary reviewer. Round 2+ incremental. No sweeps.
- `thorough` (**recommended for `post-slice` and `post-phase`**). One sweep on round 1; one fresh sweep when the primary first returns `ready` / `ready with small edits`.
- `exhaustive`. Two sweeps at each checkpoint. Use for risky phases.

Sweep reviewers do not see the primary reviewer's findings on their first pass (anti-anchoring). Findings are merged into `r{N}-merged-findings.md` and a `merged_verdict` is computed: `revise` if any reviewer (or `verdict_valid: false`) says so; `ready with small edits` if any does and the rest are `ready`; `ready` only if every reviewer is `ready`.

Checkpoint state (`first-round`, `final-ready`) is persisted in `chain.json` so sweeps fire once per chain.
````

- [ ] **Step 5: Add the "Resolution artifact" section**

````markdown
## Resolution artifact

When a post-slice or post-phase round returns `merged_verdict: revise`, the fix subagent MUST write `docs/reviewer/<chain>/r{N}-resolution.md` before the next round is submitted. The script's gate refuses round N+1 without it (exit code 3) unless `--allow-missing-resolution` is passed.

Required parseable shape:

```markdown
# Resolution for r{N}

## F1
Status: fixed | waived | deferred
Evidence:
- Commit: <sha>
- Files: `path:line`
- Verification: `command and result`

Notes:
Free-form prose.

## F2
Status: ...
```

- One `## F<id>` heading per addressed finding.
- One `Status:` line per finding (case-insensitive).
- Sweep findings use namespaced IDs like `S1.F1`; reference them with the same form in the resolution doc.

Parse failures soft-fail: `resolution_parse_status: partial` or `unparseable` is reported in the JSON, but the reviewer still receives the prose verbatim in the next round's prompt.
````

- [ ] **Step 6: Update the "Exit codes" table**

````markdown
## Exit codes

| Code | Meaning | Action |
|---|---|---|
| 0 | Reviewer succeeded. | Apply feedback. |
| 2 | Target / context file not found, or required `--work-id` missing. | Fix the path or pass `--work-id`. |
| 3 | Resolution-required gate violated. | Author the resolution doc and re-run, or pass `--allow-missing-resolution`. |
| 4 | `chain.json` schema_version newer than supported. | Upgrade `external-reviewer.py`. |
| 5 | Ambiguous legacy-chain match. | Migrate manually. |
| 124 | Reviewer timed out. | Raise `--timeout`, or split the target. |
| 127 | Reviewer command not found. | Set `AGENT_REVIEWER_CMD` or run `project-setup`. |
| other | Reviewer's own non-zero exit. | A response file was still written. Read it and surface the issue. |
````

- [ ] **Step 7: Add a "Chain manifest" section**

````markdown
## Chain manifest

Each chain folder contains a `chain.json` manifest that records every round's metadata: round number, request/response paths, head SHAs, verdicts (primary and merged), reviewers, sweep checkpoint state, and resolution attachment. The script reads it on every invocation; existing chains without a manifest are soft-migrated on first touch.

**Invariant:** a review chain is single-writer. Do not run two rounds concurrently against the same chain — `chain.json` is not locked and may be corrupted.
````

- [ ] **Step 8: Commit**

```bash
git add skills/external-review/SKILL.md
git commit -m "docs(external-review): SKILL.md for work-id/manifest/depth/resolution/incremental"
```

### Task 8.2: Update `subagent-driven-development/SKILL.md`

**Files:**
- Modify: `skills/subagent-driven-development/SKILL.md`

- [ ] **Step 1: Strengthen the fix-subagent contract**

Find the "Slice and phase boundaries" section. Replace the bullet describing the fix-subagent dispatch with:

```markdown
3. On `merged_verdict: revise` (or `verdict_valid: false`), **dispatch a fix subagent** with the previous response file as input. The fix subagent MUST write `docs/reviewer/<chain>/r{N}-resolution.md` per the contract in `[[external-review]]` before signaling completion. Wait for completion. Re-submit. Iterate.
```

- [ ] **Step 2: Add a row to the Red Flags table**

```markdown
| "I'll resubmit without the resolution file, the reviewer will figure it out" | No. Post-slice/post-phase round N+1 exits 3 without `r{N-1}-resolution.md` or `--allow-missing-resolution`. |
```

- [ ] **Step 3: Commit**

```bash
git add skills/subagent-driven-development/SKILL.md
git commit -m "docs(subagent-driven-development): fix subagent must write rN-resolution.md"
```

---

## Final verification

- [ ] **Step 1: Run the full test suite**

```bash
python3 -m pytest skills/external-review/tests/ -v
```

Expected: all tests pass.

- [ ] **Step 2: Smoke-test against the live spec**

Use the script to run a real `--kind plan` review against the freshly written plan, against the spec context:

```bash
python3 skills/external-review/scripts/external-reviewer.py review \
  --kind plan \
  --file docs/superstar/plans/2026-05-13-external-reviewer-redesign.md \
  --context docs/superstar/specs/2026-05-13-external-reviewer-redesign-design.md \
  --emit json | python3 -m json.tool | head -50
```

Expected: a `chain.json` is created under `docs/reviewer/external-reviewer-redesign-plan/` with one round entry, a parsed `verdict`, and `review_depth: "standard"`.

- [ ] **Step 3: Confirm no regressions on existing chains in the repo**

```bash
ls docs/reviewer/ 2>/dev/null
```

If pre-existing chain folders exist, run a fresh round against one of their original targets (with `--work-id` if applicable) and confirm the manifest is synthesized without losing prior `rN-*` files.

- [ ] **Step 4: Run skill round-trip**

If the spec or skill changes affect downstream skills, dry-run the `external-review` skill once by hand to confirm the JSON payload is consumed correctly. (Subagent-driven-development invokes external-review at slice boundaries — verifying that consumer path is part of S8 documentation, not S1–S7 implementation.)

---

## Self-review against the spec

| Spec section | Implemented in |
|---|---|
| Goal 1 (incremental rounds) | S4 |
| Goal 2 (machine-readable verdict) | S1 (parser), S1.6 / S7.2 (JSON output) |
| Goal 3 (work-id keyed chains) | S2 |
| Goal 4 (resolution artifacts) | S3 |
| Goal 5 (session resume) | S6 |
| Goal 6 (legacy chains) | S1.5, S2.3 |
| Goal 7 (review depth) | S7 |
| Architecture: Pass 1 | S1–S5 |
| Architecture: Pass 2 | S6 |
| Architecture: Pass 3 | S7 |
| CLI flags table | S2, S3, S4, S5, S7 |
| Round 1 prompt contract | S4.1 |
| Round N+ incremental prompt | S4.3 |
| Resolution doc parser + gate | S3 |
| Diff embedding (kind-aware default, untracked, dirty) | S5 |
| JSON output schema | S7.2 (full Pass-3 form), earlier slices add fields incrementally |
| Sweep checkpoint state | S7.1 (planner), S7.2 (persist) |
| Legacy migration + discovery | S1.5, S2.3 |
| Exit codes | S2.1 (2), S2.3 (5), S3.2 (3), S1.1 (4 — schema check is in `read_manifest`) |
| `external-review/SKILL.md` updates | S8.1 |
| `subagent-driven-development/SKILL.md` updates | S8.2 |

No spec requirement is unimplemented. All task signatures match across tasks (`parse_verdict`, `parse_findings`, `parse_resolution`, `read_manifest`, `write_manifest`, `compute_diff_section`, `plan_sweeps`, `run_one_reviewer`, `compute_merged_verdict`, `write_merged_findings`, `expand_command_template`, `current_head_sha`, `is_dirty`).

---

## Slice 1 closeout note (2026-05-14)

**Commits comprising Slice 1:**
- `50d92d4` scaffold: tests dir for external-reviewer redesign
- `8e18ef7` feat(external-reviewer): chain.json read/write helpers with schema versioning
- `2a2f4e3` feat(external-reviewer): parse_verdict with markdown/case tolerance
- `3417eea` feat(external-reviewer): parse_findings (heading + bullet, blocking count)
- `1d20020` feat(external-reviewer): next_round_number consults chain.json
- `012e3c1` feat(external-reviewer): synthesize_legacy_manifest from rN-* files
- `5404a2d` feat(external-reviewer): wire manifest + verdict/finding parsing into main()

Plus the post-review fix commits:
- Round 1 resolution at `docs/reviewer/external-reviewer-redesign-post-slice/r1-resolution.md`.
- Round 2 resolution at `docs/reviewer/external-reviewer-redesign-post-slice/r2-resolution.md`.
- Round 3 fix commits: `5cbb0fb` (committed r2 + r3 chain artefacts — F2 round 3), `6bc9289` (`parse_findings` spec drift fix + tests — F3 round 3), `062dccb` (F4 backfill: named SHAs in r2-resolution.md), `a8e6127` (backfilled F4's own SHA into r3-resolution.md); resolution at `docs/reviewer/external-reviewer-redesign-post-slice/r3-resolution.md`.
- Round 4 returned `ready with small edits`, closing the post-slice review gate; resolution at `docs/reviewer/external-reviewer-redesign-post-slice/r4-resolution.md`. The two small doc edits (this closeout note + the spec's finding-count parsing section) plus committing the r4 chain artefacts were applied in this commit.

**Final test result:** `23 passed` (21 after round 2 + 2 new round-3 parser tests for prose-style spec drift) — `python3 -m pytest skills/external-review/tests/`.

**Pre-flight override:** the plan's pre-flight branch-check was overridden by user direction; Slice 1 was implemented directly on `main`.

**Script location:** the reviewer bridge lives at `skills/external-review/scripts/external-reviewer.py`. The previous root-level `scripts/external-reviewer.py` was deleted as part of round 1's F1 fix.

**Planning artefacts committed during round 2:** `docs/superstar/specs/2026-05-13-external-reviewer-redesign-design.md` (the design spec) and `docs/handoffs/2026-05-13-external-reviewer-redesign-prompt.md` (the coordinator handoff) were intentional Slice 1 deliverables that remained untracked through round 1. They are committed as part of the round 2 F2 fix.

**Round-1 chain.json correction:** after the round-2 parser fix, the round-1 entry in `docs/reviewer/external-reviewer-redesign-post-slice/chain.json` was re-emitted so `findings_count` / `blocking_findings_count` reflect the corrected parse (`3` / `2`). The round-2 entry was already populated correctly using the fixed parser.

**By design — in-flight round artefacts:** the current round's `rN-*-request.md` is created before the reviewer runs but is only recorded in `chain.json` after the reviewer returns. During an in-progress round the request file may appear untracked while no corresponding manifest entry exists yet; this is expected and resolves when the round closes.

**Unrelated dirty files (out of Slice 1 scope, intentionally left untouched):** `CLAUDE.md`, `skills/executing-plans/SKILL.md`, `skills/finishing-a-development-branch/SKILL.md`, `skills/subagent-driven-development/SKILL.md`, `skills/tasklist-discipline/SKILL.md`.

## Slice 2 closeout note (2026-05-14)

**Commits comprising Slice 2:**
- `6700937` feat(external-reviewer): enforce --work-id for post-slice/post-phase
- `64ecb51` feat(external-reviewer): folder slug encodes work_id with dots replaced
- `d05056f` feat(external-reviewer): discover and reuse legacy chain folders

**Post-review fix commits (post-slice round 1 in the S2 chain):**
- `cc07bf5` fix(external-reviewer): persist work_id in manifest; guard legacy match by chain.json absence
- `8743c63` chore(external-reviewer): migrate misrouted Slice-2 post-slice round to S2 chain

**Documentation / closeout commits:**
- `3aa3790` docs(external-reviewer): tick Slice 2 checkboxes; add Slice 2 closeout note
- `1df15e3` docs(external-reviewer): r1-resolution for S2 post-slice chain

**Final test result:** `36 passed` — `python3 -m pytest skills/external-review/tests/` (39 after the round-2 parser fix).

**Chain-routing defect found and fixed during this review.** The original Slice-2 post-slice review was invoked with `--work-id S2` but landed in the existing Slice-1 chain folder (`docs/reviewer/external-reviewer-redesign-post-slice/`) as round 5, because `discover_legacy_chain` matched the bare legacy slug (`<target>-<kind>`) without first checking whether the candidate already contained a `chain.json`. Fix in `cc07bf5`: a candidate folder only qualifies as a legacy chain if it has no `chain.json`. Migration in `8743c63`: the misrouted artefacts were moved to `docs/reviewer/external-reviewer-redesign-S2-post-slice/` as round 1, a fresh `chain.json` was written for the S2 chain, and round 5 was dropped from the Slice-1 chain manifest. The post-slice gate for Slice 2 now lives in the correct work-id-keyed chain folder.

**Slice 2 review round 1 (in the S2 chain):** verdict `revise` with 3 findings (2 blocking). Resolution at `docs/reviewer/external-reviewer-redesign-S2-post-slice/r1-resolution.md`.

**Post-r2 fix commits:**
- `50600d5` fix(external-reviewer): parse_findings accepts em-dash/hyphen/colon separators (+ tests + S2 chain.json round-2 re-emit)
- `b5d6181` docs(external-reviewer): retrofit resolution docs to spec-compliant format
- `a03ebab` docs(external-reviewer): backfill Slice 2 closeout note with doc commits (r1 chain artefacts `3aa3790` + `1df15e3`)
- `f56c896` docs(external-reviewer): r2-resolution for S2 post-slice chain
- `bb679ad` chore(external-reviewer): record r2-resolution.md in S2 chain manifest

**Unrelated dirty files (out of Slice 2 scope, intentionally left untouched):** `CLAUDE.md`, `skills/executing-plans/SKILL.md`, `skills/finishing-a-development-branch/SKILL.md`, `skills/subagent-driven-development/SKILL.md`, `skills/tasklist-discipline/SKILL.md` (authorised by the human partner to remain across Slice 1 and Slice 2 closeouts).

**Slice 2 closed by judgment after round 4 (2026-05-14).** The S2 post-slice review chain ran to four rounds. Substantive review feedback was addressed across rounds 1–3:

- **Round 1** (verdict `revise`, 3 findings, 2 blocking): manifest `work_id` persistence and chain-routing defect identified and fixed; resolution at `docs/reviewer/external-reviewer-redesign-S2-post-slice/r1-resolution.md`.
- **Round 2** (verdict `revise`, 2 findings, 0 blocking): parser robustness for em-dash separator in finding headings, resolution-doc format compliance retrofitted, closeout-note backfill of r1 doc commits; resolution at `docs/reviewer/external-reviewer-redesign-S2-post-slice/r2-resolution.md`. Test count rose to 39.
- **Round 3** (verdict `revise`, 2 findings, 0 blocking): parser robustness extended to markdown-bold finding headings (`F1. **<heading>**` form), closeout-note backfill of post-r2 fix commits up through `bb679ad`; resolution at `docs/reviewer/external-reviewer-redesign-S2-post-slice/r3-resolution.md`, recorded in `35cacd6`. Test count rose to 41.
- **Round 4** (verdict `revise`, 2 findings, 1 blocking): both findings (F1, F2) are self-referential procedural artefacts of running review-during-iteration — F1 is the gate-hasn't-passed-yet tautology against a snapshot where the round is still in flight; F2 is the infinite regress of demanding the closeout note describe its own not-yet-existent commit. Neither is a technical defect in the delivered Slice 2 work. The human partner authorised closing Slice 2 by judgment rather than iterating further. Full reasoning at `docs/reviewer/external-reviewer-redesign-S2-post-slice/r4-resolution.md`.

**Final test result:** `python3 -m pytest skills/external-review/tests/` → `41 passed`.

**Slice 2 tasks 2.1, 2.2, 2.3 are functionally complete.** The post-slice gate is closed by judgment with this commit.

## Slice 3 closeout note (2026-05-14)

**Slice 3 closed by human-partner judgment without external post-slice review.** The external post-slice review step was skipped after Slice 2's experience with self-referential review-during-iteration noise (see Slice 2 round-4 reasoning above).

**Commits comprising Slice 3:**
- `ea8bac6` S3.1 resolution-doc parser (`parse_resolution`) + tests
- `c510324` S3.2 resolution-required gate + `--allow-missing-resolution` flag + tests

Both commits passed in-loop spec compliance and code-quality reviews via subagents before landing.

**Final test result:** `python3 -m pytest skills/external-review/tests/` → `47 passed`.
