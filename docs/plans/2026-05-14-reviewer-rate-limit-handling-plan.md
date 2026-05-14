# Reviewer rate-limit handling — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `external-reviewer.py` detect third-party reviewer usage caps, persist a global flag across sessions, refuse to spawn while limited, and give the operator three named recovery paths plus a hold.

**Architecture:** Two layers. CLI layer detects/persists/refuses and exits with a new code 8 carrying a JSON payload. Coordinator layer in `SKILL.md` documents the four-option menu and dispatches each path. Rate-limited rounds are first-class chain entries that bypass the resolution gate, get skipped by preamble walk-back, and are excluded from merged verdicts — symmetrically with the existing `failed` round treatment.

**Tech Stack:** Python stdlib only (`fcntl`, `json`, `re`, `datetime`, `argparse`, `pathlib`). pytest for testing.

**Reference:** Spec at `docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md`. The spec is authoritative; this plan implements it task-by-task.

---

## Files at a glance

| Path | Action | Purpose |
|---|---|---|
| `skills/external-review/scripts/external-reviewer.py` | Modify | Add state primitives, detection, pre-spawn check, exit-8, four new subcommands, 4-site status semantics, refusal coalescing. |
| `skills/external-review/SKILL.md` | Modify | Document the new exit code, the menu, dispatch paths. |
| `skills/external-review/tests/test_state_file.py` | Create | State file primitives. |
| `skills/external-review/tests/test_rate_limit_detection.py` | Create | `detect_rate_limit` regex coverage. |
| `skills/external-review/tests/test_reset_time_parser.py` | Create | Reset-time parser corner cases. |
| `skills/external-review/tests/test_exit_code_8.py` | Create | End-to-end rate-limit detection → exit 8 → state. |
| `skills/external-review/tests/test_subsequent_invocation_refused.py` | Create | Pre-spawn refusal path. |
| `skills/external-review/tests/test_refusal_coalescing.py` | Create | Coalescing onto head rate-limited round. |
| `skills/external-review/tests/test_rate_limited_status_semantics.py` | Create | Resolution gate, preamble walk-back, merged-verdict filter, write_merged_findings. |
| `skills/external-review/tests/test_sweep_partial_rate_limit.py` | Create | Primary ok, sweep rate-limited → round still ok, state written. |
| `skills/external-review/tests/test_manual_approve_subcommand.py` | Create | manual-approve subcommand. |
| `skills/external-review/tests/test_ingest_response_subcommand.py` | Create | ingest-response with paste + link, reformat rules. |
| `skills/external-review/tests/test_show_clear_limit.py` | Create | show-limit + clear-limit subcommands. |

## Conventions used throughout the plan

- **TDD-first.** Every task writes a failing test, runs it, sees it fail, implements minimal code, runs it, sees it pass, commits.
- **Importing the script.** All new tests use the existing fixture pattern (the script has a hyphen in its filename so it can't be imported directly):
  ```python
  from pathlib import Path
  import sys, importlib.util
  SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
  sys.path.insert(0, str(SCRIPTS))
  spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
  er = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(er)
  ```
- **State file isolation.** Every test that touches state MUST set `AGENT_REVIEWER_STATE_FILE` to a `tmp_path`-scoped file before importing/invoking script code:
  ```python
  @pytest.fixture(autouse=True)
  def _isolated_state(tmp_path, monkeypatch):
      monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "reviewer-state.json"))
  ```
  This fixture goes at the top of every new test file. Existing tests don't need it (they don't touch state).
- **Commit cadence.** Each task ends in exactly one commit. Commit messages follow the existing `external-reviewer: <imperative summary>` style.
- **No push.** This work is local-only until the user explicitly asks.

## Spec → Plan mapping

| Spec section | Implemented by |
|---|---|
| §5 State file (path, override, expiry, flock) | S1 Tasks 1.1–1.3 |
| §6 Detection + reset-time parsing | S1 Tasks 1.4–1.5 |
| §7.1 Pre-spawn check | S2 Tasks 2.1–2.2 |
| §7.2 Post-failure detection | S2 Task 2.3 |
| §7.3 Exit code 8 JSON payload | S2 Tasks 2.1 + 2.5 |
| §7.4 Rate-limited status semantics | S3 (Tasks 3.1–3.4) |
| §7.5 Coalescing | S4 (Tasks 4.1–4.2) |
| §7.6 Subcommands | S5 (Tasks 5.1–5.5) |
| §8 Coordinator integration / SKILL.md | S6 (Tasks 6.1–6.3) |
| §9 Tests | Threaded through every slice |
| §11 Acceptance | S7 (Tasks 7.1–7.2) |

---

## Slice 1 — State file primitives + detection

This slice produces pure functions with unit tests. The script's existing behaviour is unchanged at slice close.

### Task 1.1: State file load with env-var override + fail-open

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (add module-level helpers near the top, immediately after the existing `cap_with_elision` definition)
- Create: `skills/external-review/tests/test_state_file.py`

- [ ] **Step 1: Write the failing test**

```python
# skills/external-review/tests/test_state_file.py
import json
import os
from pathlib import Path
import sys
import importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "reviewer-state.json"))


def test_state_path_uses_env_override(tmp_path, monkeypatch):
    target = tmp_path / "custom-state.json"
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(target))
    assert er.state_file_path() == target


def test_load_state_missing_file_returns_empty():
    state = er.load_state()
    assert state == {"schema_version": 1, "limits": {}}


def test_load_state_round_trip(tmp_path):
    target = Path(os.environ["AGENT_REVIEWER_STATE_FILE"])
    target.write_text(json.dumps({"schema_version": 1, "limits": {"reviewer-agent": {"limited": True}}}))
    state = er.load_state()
    assert state["limits"]["reviewer-agent"]["limited"] is True


def test_load_state_corrupt_file_fails_open(capsys, tmp_path):
    target = Path(os.environ["AGENT_REVIEWER_STATE_FILE"])
    target.write_text("{not json")
    state = er.load_state()
    assert state == {"schema_version": 1, "limits": {}}
    captured = capsys.readouterr()
    assert "reviewer-state.json" in captured.err  # warning surfaced
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest skills/external-review/tests/test_state_file.py -v`
Expected: AttributeError — `state_file_path` and `load_state` don't exist.

- [ ] **Step 3: Implement `state_file_path` and `load_state`**

In `skills/external-review/scripts/external-reviewer.py`, immediately after the `cap_with_elision` function, add:

```python
DEFAULT_STATE_FILE = Path.home() / ".config" / "superstar" / "reviewer-state.json"


def state_file_path() -> Path:
    override = os.environ.get("AGENT_REVIEWER_STATE_FILE")
    if override:
        return Path(override)
    return DEFAULT_STATE_FILE


def load_state() -> dict:
    """Read the reviewer state file. Fails open: missing/corrupt → empty state."""
    path = state_file_path()
    if not path.exists():
        return {"schema_version": 1, "limits": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("limits"), dict):
            raise ValueError("schema mismatch")
        return data
    except (json.JSONDecodeError, ValueError, OSError) as e:
        print(f"WARNING: reviewer-state.json at {path} unreadable ({e}); treating as empty", file=sys.stderr)
        return {"schema_version": 1, "limits": {}}
```

If `os` or `json` aren't already imported at module top, add them.

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_state_file.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_state_file.py
git commit -m "external-reviewer: state file primitive (load with env override, fail-open)"
```

---

### Task 1.2: State file save with flock + atomic write + 0700 parent

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (continue in the state-primitives block)
- Modify: `skills/external-review/tests/test_state_file.py`

- [ ] **Step 1: Write the failing tests** (append to `test_state_file.py`)

```python
def test_save_state_creates_parent_dir_0700(tmp_path, monkeypatch):
    target = tmp_path / "nested" / "deep" / "state.json"
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(target))
    er.save_state({"schema_version": 1, "limits": {"reviewer-agent": {"limited": True}}})
    assert target.exists()
    # Parent dir permissions: 0o700 (owner rwx, nothing else)
    parent_mode = oct(target.parent.stat().st_mode & 0o777)
    assert parent_mode == "0o700"


def test_save_state_round_trip():
    er.save_state({"schema_version": 1, "limits": {"reviewer-agent": {"limited": True, "reset_at": "2026-05-14T18:48:00"}}})
    out = er.load_state()
    assert out["limits"]["reviewer-agent"]["reset_at"] == "2026-05-14T18:48:00"


def test_save_state_atomic_via_tmp_rename(tmp_path, monkeypatch):
    """Writing should go through a .tmp file then rename, so a crash mid-write
    can never corrupt the on-disk state."""
    target = tmp_path / "state.json"
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(target))
    target.write_text('{"schema_version": 1, "limits": {"reviewer-agent": {"limited": false}}}')
    er.save_state({"schema_version": 1, "limits": {"reviewer-agent": {"limited": True}}})
    # After save, no orphan .tmp file remains
    assert not (tmp_path / "state.json.tmp").exists()
    assert er.load_state()["limits"]["reviewer-agent"]["limited"] is True
```

- [ ] **Step 2: Verify they fail**

Run: `python3 -m pytest skills/external-review/tests/test_state_file.py -v`
Expected: 3 new tests fail (`save_state` doesn't exist).

- [ ] **Step 3: Implement `save_state`**

Append to the state-primitives block in `external-reviewer.py`:

```python
import fcntl  # add at module top if not already present

def save_state(state: dict) -> None:
    """Atomically write the reviewer state file. Uses flock + tmp-then-rename.
    Creates parent dir with mode 0o700 on first write."""
    path = state_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass  # best-effort; some filesystems disallow chmod
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(state, indent=2, sort_keys=True)
    with open(tmp_path, "w", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    os.replace(tmp_path, path)
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_state_file.py -v`
Expected: all 7 pass.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_state_file.py
git commit -m "external-reviewer: state file atomic save with flock + 0700 parent"
```

---

### Task 1.3: State expiry-on-read

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Modify: `skills/external-review/tests/test_state_file.py`

- [ ] **Step 1: Write the failing test**

Append to `test_state_file.py`:

```python
import datetime as dt


def test_get_active_limit_expires_past_reset(monkeypatch):
    past = (dt.datetime.now() - dt.timedelta(hours=1)).isoformat(timespec="seconds")
    er.save_state({"schema_version": 1, "limits": {"reviewer-agent": {
        "limited": True, "reset_at": past, "limited_at": past, "reset_source": "test",
        "raw_stderr_tail": "", "chain": "x", "round": 1
    }}})
    # get_active_limit clears expired entries in-place and returns None.
    assert er.get_active_limit("reviewer-agent") is None
    # The state file should now show limits={} for reviewer-agent (entry removed).
    assert "reviewer-agent" not in er.load_state()["limits"]


def test_get_active_limit_returns_live_entry():
    future = (dt.datetime.now() + dt.timedelta(hours=1)).isoformat(timespec="seconds")
    er.save_state({"schema_version": 1, "limits": {"reviewer-agent": {
        "limited": True, "reset_at": future, "limited_at": "x", "reset_source": "t",
        "raw_stderr_tail": "", "chain": "c", "round": 1
    }}})
    entry = er.get_active_limit("reviewer-agent")
    assert entry is not None
    assert entry["reset_at"] == future


def test_get_active_limit_no_entry_returns_none():
    assert er.get_active_limit("reviewer-agent") is None
```

- [ ] **Step 2: Verify they fail**

Run: `python3 -m pytest skills/external-review/tests/test_state_file.py -v`
Expected: 3 new tests fail (`get_active_limit` doesn't exist).

- [ ] **Step 3: Implement `get_active_limit`**

Append:

```python
def get_active_limit(reviewer_cmd_basename: str) -> dict | None:
    """Return the limit entry for the given reviewer if it's still active.
    Side effect: if the entry exists but `reset_at <= now()`, clear it from
    the state file and return None.
    """
    state = load_state()
    entry = state["limits"].get(reviewer_cmd_basename)
    if not entry or not entry.get("limited"):
        return None
    try:
        reset_at = dt.datetime.fromisoformat(entry["reset_at"])
    except (KeyError, ValueError, TypeError):
        # Treat malformed entries as expired, prune them.
        state["limits"].pop(reviewer_cmd_basename, None)
        save_state(state)
        return None
    if reset_at <= dt.datetime.now():
        state["limits"].pop(reviewer_cmd_basename, None)
        save_state(state)
        return None
    return entry
```

Add `import datetime as dt` at module top if not already present.

- [ ] **Step 4: Run tests**

Expected: 10 passed in `test_state_file.py`.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_state_file.py
git commit -m "external-reviewer: state expiry-on-read prunes stale limits"
```

---

### Task 1.4: `detect_rate_limit` with built-in patterns + env extension

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Create: `skills/external-review/tests/test_rate_limit_detection.py`

- [ ] **Step 1: Write the failing tests**

```python
# skills/external-review/tests/test_rate_limit_detection.py
from pathlib import Path
import sys, importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


CODEX_STDERR = (
    "ERROR: You've hit your usage limit. Upgrade to Pro "
    "(https://chatgpt.com/explore/pro), visit https://chatgpt.com/codex/settings/usage "
    "to purchase more credits or try again at 6:48 PM.\n"
)


def test_codex_sample_matches():
    matched, _reset_at, name = er.detect_rate_limit(CODEX_STDERR)
    assert matched is True
    assert name == "codex_usage_limit"


def test_codex_sample_extracts_time_group():
    matched, reset_at, _ = er.detect_rate_limit(CODEX_STDERR)
    assert matched is True
    # 6:48 PM → 18:48 in 24h
    assert reset_at.hour == 18
    assert reset_at.minute == 48


def test_unmatched_stderr_returns_falsey():
    matched, reset_at, name = er.detect_rate_limit("Traceback ...\nValueError: foo\n")
    assert matched is False
    assert reset_at is None
    assert name is None


def test_user_pattern_via_env(monkeypatch):
    monkeypatch.setenv(
        "AGENT_REVIEWER_RATE_LIMIT_PATTERNS",
        r"my_backend=ERROR limit hit until (\d{1,2}:\d{2})",
    )
    matched, reset_at, name = er.detect_rate_limit("ERROR limit hit until 14:30")
    assert matched is True
    assert name == "my_backend"
    assert reset_at is not None and reset_at.hour == 14 and reset_at.minute == 30
```

- [ ] **Step 2: Verify they fail**

Run: `python3 -m pytest skills/external-review/tests/test_rate_limit_detection.py -v`
Expected: AttributeError — `detect_rate_limit` doesn't exist.

- [ ] **Step 3: Implement `detect_rate_limit`**

Append to `external-reviewer.py` (after the state primitives):

```python
RATE_LIMIT_BUILTIN_PATTERNS = [
    ("codex_usage_limit",
     re.compile(r"You've hit your usage limit.*?try again at (\d{1,2}:\d{2}\s*(?:AM|PM)?)", re.IGNORECASE | re.DOTALL)),
    ("claude_cli_rate_limit",
     re.compile(r"(?:rate limit|rate-limited).*?reset (?:at|in)? ?(.+?)$", re.IGNORECASE | re.MULTILINE)),
    ("gemini_cli_rate_limit",
     re.compile(r"quota exceeded.*?retry (?:after|at) (.+?)$", re.IGNORECASE | re.MULTILINE)),
]


def _user_patterns_from_env() -> list[tuple[str, re.Pattern]]:
    raw = os.environ.get("AGENT_REVIEWER_RATE_LIMIT_PATTERNS", "")
    if not raw:
        return []
    pairs = []
    for chunk in raw.split(";"):
        chunk = chunk.strip()
        if "=" not in chunk:
            continue
        name, pattern = chunk.split("=", 1)
        try:
            pairs.append((name.strip(), re.compile(pattern.strip(), re.IGNORECASE | re.DOTALL)))
        except re.error:
            print(f"WARNING: invalid user rate-limit pattern '{name}': skipping", file=sys.stderr)
    return pairs


def detect_rate_limit(stderr_text: str) -> tuple[bool, "dt.datetime | None", "str | None"]:
    """Inspect reviewer stderr for a rate-limit signature.
    Returns (matched, reset_at_local, pattern_name)."""
    patterns = RATE_LIMIT_BUILTIN_PATTERNS + _user_patterns_from_env()
    for name, pat in patterns:
        m = pat.search(stderr_text)
        if m:
            time_group = m.group(1) if m.groups() else None
            reset_at = _parse_reset_time(time_group) if time_group else _fallback_reset_time()
            return True, reset_at, name
    return False, None, None


def _fallback_reset_time() -> "dt.datetime":
    hours = int(os.environ.get("AGENT_REVIEWER_LIMIT_FALLBACK_HOURS", "4"))
    return (dt.datetime.now() + dt.timedelta(hours=hours)).replace(second=0, microsecond=0)
```

Note: `_parse_reset_time` is implemented in Task 1.5. For now, add a stub:

```python
def _parse_reset_time(s: str) -> "dt.datetime":
    return _fallback_reset_time()  # placeholder; refined in Task 1.5
```

Ensure `re` is imported at module top.

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_rate_limit_detection.py -v`
Expected: the user-pattern test may parse `14:30` as fallback (since stub `_parse_reset_time` returns fallback). That test's `assert reset_at.hour == 14` will FAIL with the stub. That's expected — Task 1.5 fixes it. Mark this test xfail for now:

In the test, wrap the failing assertion:

```python
def test_user_pattern_via_env(monkeypatch):
    monkeypatch.setenv(
        "AGENT_REVIEWER_RATE_LIMIT_PATTERNS",
        r"my_backend=ERROR limit hit until (\d{1,2}:\d{2})",
    )
    matched, reset_at, name = er.detect_rate_limit("ERROR limit hit until 14:30")
    assert matched is True
    assert name == "my_backend"
    # reset_at parsing is wired up properly in Task 1.5; for now just assert non-None.
    assert reset_at is not None
```

Same change applies to `test_codex_sample_extracts_time_group` — relax to `assert reset_at is not None` for this task; Task 1.5 strengthens it.

Re-run: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_rate_limit_detection.py
git commit -m "external-reviewer: detect_rate_limit with built-in + env-extension patterns"
```

---

### Task 1.5: `_parse_reset_time` (HH:MM, AM/PM, 24h, past-time wraps, no-time fallback)

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (replace stub)
- Create: `skills/external-review/tests/test_reset_time_parser.py`
- Modify: `skills/external-review/tests/test_rate_limit_detection.py` (strengthen relaxed assertions back to spec)

- [ ] **Step 1: Write the failing tests**

```python
# skills/external-review/tests/test_reset_time_parser.py
import datetime as dt
from pathlib import Path
import sys, importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def test_parse_pm_clock(monkeypatch):
    # Freeze "now" to a moment before 6:48 PM today.
    fixed = dt.datetime(2026, 5, 14, 17, 0, 0)
    monkeypatch.setattr(er, "_now_local", lambda: fixed)
    out = er._parse_reset_time("6:48 PM")
    assert out == dt.datetime(2026, 5, 14, 18, 48, 0)


def test_parse_am_clock(monkeypatch):
    fixed = dt.datetime(2026, 5, 14, 17, 0, 0)
    monkeypatch.setattr(er, "_now_local", lambda: fixed)
    out = er._parse_reset_time("9:15 AM")
    # 9:15 AM today is in the past relative to 17:00 → wrap to tomorrow.
    assert out == dt.datetime(2026, 5, 15, 9, 15, 0)


def test_parse_24h_clock(monkeypatch):
    fixed = dt.datetime(2026, 5, 14, 17, 0, 0)
    monkeypatch.setattr(er, "_now_local", lambda: fixed)
    out = er._parse_reset_time("19:30")
    assert out == dt.datetime(2026, 5, 14, 19, 30, 0)


def test_parse_past_24h_wraps(monkeypatch):
    fixed = dt.datetime(2026, 5, 14, 17, 0, 0)
    monkeypatch.setattr(er, "_now_local", lambda: fixed)
    out = er._parse_reset_time("08:00")
    assert out == dt.datetime(2026, 5, 15, 8, 0, 0)


def test_parse_unparseable_falls_back(monkeypatch):
    fixed = dt.datetime(2026, 5, 14, 17, 0, 0)
    monkeypatch.setattr(er, "_now_local", lambda: fixed)
    monkeypatch.setenv("AGENT_REVIEWER_LIMIT_FALLBACK_HOURS", "4")
    out = er._parse_reset_time("some_weird_string")
    # Fallback: now + 4h
    assert out == dt.datetime(2026, 5, 14, 21, 0, 0)
```

- [ ] **Step 2: Verify they fail**

Run: `python3 -m pytest skills/external-review/tests/test_reset_time_parser.py -v`
Expected: failures across the board (stub returns fallback for everything; the AM/PM and 24h tests fail on parsing).

- [ ] **Step 3: Implement `_parse_reset_time`**

In `external-reviewer.py`, replace the stub:

```python
_TIME_RE_AMPM = re.compile(r"^(\d{1,2}):(\d{2})\s*([AaPp][Mm])$")
_TIME_RE_24H = re.compile(r"^(\d{1,2}):(\d{2})$")


def _now_local() -> "dt.datetime":
    """Override hook for tests."""
    return dt.datetime.now()


def _parse_reset_time(s: str) -> "dt.datetime":
    """Parse a clock time (HH:MM with optional AM/PM, or 24-hour) as local time.
    If the parsed time is in the past relative to now, add one day."""
    s = (s or "").strip()
    hour, minute = None, None
    m = _TIME_RE_AMPM.match(s)
    if m:
        hour, minute = int(m.group(1)), int(m.group(2))
        suffix = m.group(3).upper()
        if suffix == "PM" and hour < 12:
            hour += 12
        elif suffix == "AM" and hour == 12:
            hour = 0
    else:
        m = _TIME_RE_24H.match(s)
        if m:
            hour, minute = int(m.group(1)), int(m.group(2))
    if hour is None or not (0 <= hour <= 23) or not (0 <= minute <= 59):
        return _fallback_reset_time()
    now = _now_local()
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now:
        candidate += dt.timedelta(days=1)
    return candidate
```

Update `_fallback_reset_time` to use `_now_local`:

```python
def _fallback_reset_time() -> "dt.datetime":
    hours = int(os.environ.get("AGENT_REVIEWER_LIMIT_FALLBACK_HOURS", "4"))
    return (_now_local() + dt.timedelta(hours=hours)).replace(second=0, microsecond=0)
```

- [ ] **Step 4: Strengthen the relaxed detection tests**

In `skills/external-review/tests/test_rate_limit_detection.py`:

```python
def test_codex_sample_extracts_time_group():
    matched, reset_at, _ = er.detect_rate_limit(CODEX_STDERR)
    assert matched is True
    assert reset_at is not None
    assert reset_at.hour == 18
    assert reset_at.minute == 48


def test_user_pattern_via_env(monkeypatch):
    monkeypatch.setenv(
        "AGENT_REVIEWER_RATE_LIMIT_PATTERNS",
        r"my_backend=ERROR limit hit until (\d{1,2}:\d{2})",
    )
    matched, reset_at, name = er.detect_rate_limit("ERROR limit hit until 14:30")
    assert matched is True
    assert name == "my_backend"
    assert reset_at is not None and reset_at.hour == 14 and reset_at.minute == 30
```

(Note: `test_codex_sample_extracts_time_group` may fail intermittently around midnight if the parsed `18:48` is in the past — for stability, freeze `_now_local` in this test too, similar to the parser tests.)

Strengthened version:

```python
def test_codex_sample_extracts_time_group(monkeypatch):
    monkeypatch.setattr(er, "_now_local", lambda: dt.datetime(2026, 5, 14, 17, 0, 0))
    matched, reset_at, _ = er.detect_rate_limit(CODEX_STDERR)
    assert matched is True
    assert reset_at == dt.datetime(2026, 5, 14, 18, 48, 0)
```

Import `datetime as dt` at the top of the detection test file.

- [ ] **Step 5: Run all reset/detect tests**

Run: `python3 -m pytest skills/external-review/tests/test_reset_time_parser.py skills/external-review/tests/test_rate_limit_detection.py -v`
Expected: 5 + 4 = 9 passed.

Run full suite:
`python3 -m pytest skills/external-review/tests/ -q`
Expected: 142 baseline + 10 new state-file + 4 detection + 5 parser = 161 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_reset_time_parser.py \
        skills/external-review/tests/test_rate_limit_detection.py
git commit -m "external-reviewer: reset-time parser (AM/PM, 24h, past-wrap, fallback)"
```

→ Invoke `superstar:external-review --kind post-slice --file docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md --work-id S1 --context docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md` to gate slice close (depth: standard — pure-function slice, low risk).

**Caveat:** External-review may be bypassed for this work per the active session policy. If the user has waived gates for this plan, skip the invocation and move to S2. The coordinator confirms with the user at slice close.

---

## Slice 2 — CLI integration (pre-spawn check, post-failure, exit 8)

### Task 2.1: `reviewer_cmd_basename` helper + state key resolution

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Modify: `skills/external-review/tests/test_state_file.py`

- [ ] **Step 1: Write the failing test**

Append to `test_state_file.py`:

```python
def test_reviewer_cmd_basename_simple(monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_CMD", "reviewer-agent")
    assert er.reviewer_cmd_basename() == "reviewer-agent"


def test_reviewer_cmd_basename_template(monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_CMD", "bash -c 'reviewer-agent {prompt_file}'")
    assert er.reviewer_cmd_basename() == "bash"


def test_reviewer_cmd_basename_state_key_override(monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_CMD", "bash -c 'foo'")
    monkeypatch.setenv("AGENT_REVIEWER_STATE_KEY", "codex")
    assert er.reviewer_cmd_basename() == "codex"


def test_reviewer_cmd_basename_default(monkeypatch):
    monkeypatch.delenv("AGENT_REVIEWER_CMD", raising=False)
    monkeypatch.delenv("AGENT_REVIEWER_STATE_KEY", raising=False)
    assert er.reviewer_cmd_basename() == "reviewer-agent"
```

- [ ] **Step 2: Verify they fail**

Run: `python3 -m pytest skills/external-review/tests/test_state_file.py -v`
Expected: 4 new tests fail.

- [ ] **Step 3: Implement**

In `external-reviewer.py`, after the state primitives:

```python
def reviewer_cmd_basename() -> str:
    """Return the state-key for the configured reviewer command. Honours
    AGENT_REVIEWER_STATE_KEY override; else uses the first whitespace token of
    AGENT_REVIEWER_CMD; else the default 'reviewer-agent'."""
    override = os.environ.get("AGENT_REVIEWER_STATE_KEY")
    if override:
        return override.strip()
    cmd = os.environ.get("AGENT_REVIEWER_CMD", "reviewer-agent")
    return cmd.strip().split()[0] if cmd.strip() else "reviewer-agent"
```

- [ ] **Step 4: Run tests**

Expected: 14 passed in `test_state_file.py`.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_state_file.py
git commit -m "external-reviewer: reviewer_cmd_basename for state keying"
```

---

### Task 2.2: Rate-limited round artifact writer

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Create: `skills/external-review/tests/test_rate_limited_artifact.py`

- [ ] **Step 1: Write the failing test**

```python
# skills/external-review/tests/test_rate_limited_artifact.py
import json
from pathlib import Path
import sys, importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "rs.json"))


def test_rate_limited_artifact_shape(tmp_path):
    chain_dir = tmp_path / "chain"
    chain_dir.mkdir()
    out_path = er.write_rate_limited_artifact(
        chain_dir=chain_dir,
        round_num=2,
        timestamp="2026-05-14T1800",
        reviewer_cmd="reviewer-agent",
        reset_at="2026-05-14T18:48:00",
        raw_stderr_tail="ERROR: You've hit your usage limit. ...",
    )
    body = out_path.read_text(encoding="utf-8")
    assert out_path.exists()
    # Cap: ≤ 8 KB (same as failed-round)
    assert len(body.encode("utf-8")) <= 8 * 1024
    # Required fields
    assert "Status: `rate-limited`" in body
    assert "2026-05-14T18:48:00" in body
    assert "ERROR: You've hit your usage limit" in body
    # Note pointing user to the menu / retry
    assert "rerun after that or use the menu" in body
```

- [ ] **Step 2: Verify it fails**

Run: `python3 -m pytest skills/external-review/tests/test_rate_limited_artifact.py -v`
Expected: AttributeError.

- [ ] **Step 3: Implement**

In `external-reviewer.py`, near the existing `write_review_artifact` function (which writes failed-round stubs), add:

```python
def write_rate_limited_artifact(
    *,
    chain_dir: Path,
    round_num: int,
    timestamp: str,
    reviewer_cmd: str,
    reset_at: str,
    raw_stderr_tail: str,
) -> Path:
    """Persist a rate-limited round response artifact (≤ 8 KB)."""
    out_path = chain_dir / f"r{round_num}-{timestamp}-response.md"
    # Cap stderr tail to ~4 KB to keep the whole artifact under 8 KB.
    stderr_tail_capped = cap_with_elision(raw_stderr_tail or "", max_bytes=4 * 1024)
    body = (
        f"# Reviewer rate-limited — r{round_num}\n\n"
        f"- Status: `rate-limited`\n"
        f"- Reviewer command: `{reviewer_cmd}`\n"
        f"- Reset at: `{reset_at}`\n\n"
        f"Reviewer rate-limited until {reset_at}; rerun after that or use the menu "
        f"(see SKILL.md → Rate-limit handling).\n\n"
        f"## Reviewer stderr (tail)\n\n```text\n{stderr_tail_capped}\n```\n"
    )
    out_path.write_text(body, encoding="utf-8")
    return out_path
```

- [ ] **Step 4: Run tests**

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_rate_limited_artifact.py
git commit -m "external-reviewer: rate-limited round artifact writer (≤8 KB)"
```

---

### Task 2.3: Exit-8 JSON payload helper

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Create: `skills/external-review/tests/test_exit_code_8.py`

- [ ] **Step 1: Write the failing test**

```python
# skills/external-review/tests/test_exit_code_8.py
import json
from pathlib import Path
import sys, importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "rs.json"))


def test_rate_limit_payload_shape():
    payload = er.make_rate_limit_payload(
        reviewer_cmd="reviewer-agent",
        reset_at="2026-05-14T18:48:00",
        reset_source="regex:codex_usage_limit",
        chain="some-chain",
        round_num=2,
        request_path="docs/reviewer/some-chain/r2-...-request.md",
        raw_stderr_tail="ERROR: You've hit your usage limit ...",
    )
    assert payload["rate_limited"] is True
    assert payload["reviewer_cmd"] == "reviewer-agent"
    assert payload["reset_at"] == "2026-05-14T18:48:00"
    assert payload["reset_source"] == "regex:codex_usage_limit"
    assert payload["chain"] == "some-chain"
    assert payload["round"] == 2
    assert payload["request_path"].endswith("r2-...-request.md")
    assert "raw_stderr_tail" in payload


def test_rate_limit_payload_serialises_to_json():
    payload = er.make_rate_limit_payload(
        reviewer_cmd="reviewer-agent",
        reset_at="2026-05-14T18:48:00",
        reset_source="regex:codex_usage_limit",
        chain="c", round_num=2, request_path="r", raw_stderr_tail="t",
    )
    s = json.dumps(payload)
    assert "rate_limited" in s
```

- [ ] **Step 2: Verify failure**

Run: expected AttributeError.

- [ ] **Step 3: Implement**

```python
EXIT_CODE_RATE_LIMITED = 8


def make_rate_limit_payload(
    *,
    reviewer_cmd: str,
    reset_at: str,
    reset_source: str,
    chain: str,
    round_num: int,
    request_path: str,
    raw_stderr_tail: str,
) -> dict:
    """Build the JSON payload emitted on exit 8."""
    return {
        "rate_limited": True,
        "reviewer_cmd": reviewer_cmd,
        "reset_at": reset_at,
        "reset_source": reset_source,
        "chain": chain,
        "round": round_num,
        "request_path": request_path,
        "raw_stderr_tail": raw_stderr_tail[-2048:],  # cap inline; full tail in artifact
    }
```

- [ ] **Step 4: Run tests**

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_exit_code_8.py
git commit -m "external-reviewer: exit-8 rate-limit JSON payload helper"
```

---

### Task 2.4: Post-failure detection wired into `run_one_reviewer`

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Modify: `skills/external-review/tests/test_exit_code_8.py`

- [ ] **Step 1: Write the failing test (end-to-end)**

Append to `test_exit_code_8.py`:

```python
import os, subprocess


def test_failed_reviewer_with_rate_limit_stderr_triggers_state_write(tmp_path, monkeypatch):
    """A reviewer subprocess that exits non-zero with rate-limit stderr must:
       - cause the script to exit 8
       - write a state entry
       - emit the rate-limit JSON payload on stdout
    """
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\nbody\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    # Reviewer simulator: prints rate-limit error to stderr, exits 1.
    reviewer = repo / "fake.sh"
    reviewer.write_text(
        "#!/usr/bin/env bash\n"
        "echo \"ERROR: You've hit your usage limit. Try again at 6:48 PM.\" >&2\n"
        "exit 1\n"
    )
    reviewer.chmod(0o755)

    state_file = tmp_path / "state.json"
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(state_file)

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == er.EXIT_CODE_RATE_LIMITED, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["rate_limited"] is True
    assert "reset_at" in payload
    # State file written
    state = json.loads(state_file.read_text())
    key = reviewer.name
    assert state["limits"][key]["limited"] is True
```

- [ ] **Step 2: Verify failure**

Run: `python3 -m pytest skills/external-review/tests/test_exit_code_8.py -v`
Expected: returncode is the reviewer's `1`, not `8` — script doesn't yet branch on rate-limit detection.

- [ ] **Step 3: Wire detection into `run_one_reviewer`**

Find `run_one_reviewer` in `external-reviewer.py`. After the subprocess completes and before the existing failed-round artifact is written, add:

```python
    # Rate-limit detection — runs only on non-zero exit
    if result.returncode != 0:
        matched, reset_at, pattern_name = detect_rate_limit(result.stderr or "")
        if matched:
            reset_at_iso = (reset_at or _fallback_reset_time()).isoformat(timespec="seconds")
            state = load_state()
            key = reviewer_cmd_basename()
            state["limits"][key] = {
                "limited": True,
                "limited_at": _now_local().isoformat(timespec="seconds"),
                "reset_at": reset_at_iso,
                "reset_source": f"regex:{pattern_name}" if pattern_name else "fallback",
                "raw_stderr_tail": (result.stderr or "")[-2048:],
                "chain": chain_name,
                "round": round_num,
            }
            save_state(state)
            # Write the rate-limited artifact instead of the failed-round stub
            artifact_path = write_rate_limited_artifact(
                chain_dir=chain_dir, round_num=round_num, timestamp=timestamp,
                reviewer_cmd=key, reset_at=reset_at_iso,
                raw_stderr_tail=result.stderr or "",
            )
            # Signal up to main(): use a dedicated exception type
            raise ReviewerRateLimited(
                reviewer_cmd=key, reset_at=reset_at_iso,
                reset_source=f"regex:{pattern_name}" if pattern_name else "fallback",
                chain=chain_name, round_num=round_num,
                request_path=str(request_path),
                raw_stderr_tail=result.stderr or "",
            )
```

Define `ReviewerRateLimited` at module top:

```python
class ReviewerRateLimited(Exception):
    def __init__(self, *, reviewer_cmd, reset_at, reset_source, chain, round_num, request_path, raw_stderr_tail):
        super().__init__(f"Reviewer {reviewer_cmd} rate-limited until {reset_at}")
        self.reviewer_cmd = reviewer_cmd
        self.reset_at = reset_at
        self.reset_source = reset_source
        self.chain = chain
        self.round_num = round_num
        self.request_path = request_path
        self.raw_stderr_tail = raw_stderr_tail
```

In `main()` (the `review` subcommand dispatch), wrap the call to `run_one_reviewer` to catch this exception and exit 8:

```python
    try:
        # ... existing call to run_one_reviewer (or write_review_artifact wrapping it)
        ...
    except ReviewerRateLimited as exc:
        payload = make_rate_limit_payload(
            reviewer_cmd=exc.reviewer_cmd, reset_at=exc.reset_at,
            reset_source=exc.reset_source, chain=exc.chain, round_num=exc.round_num,
            request_path=exc.request_path, raw_stderr_tail=exc.raw_stderr_tail,
        )
        if args.emit == "json":
            print(json.dumps(payload, indent=2))
        else:
            print(f"Reviewer rate-limited until {exc.reset_at}. See {exc.request_path}.")
        sys.exit(EXIT_CODE_RATE_LIMITED)
```

Adjust variable names to match what `run_one_reviewer` already has in scope (chain_name, chain_dir, request_path, round_num, timestamp). If `chain_name` isn't a local, derive it from `chain_dir.name`.

**Note:** the existing failed-round path remains — it only fires when the rate-limit detection did NOT match.

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_exit_code_8.py -v`
Expected: 3 passed.

Full suite: `python3 -m pytest skills/external-review/tests/ -q`
Expected: 161 baseline + 4 (state) + 1 (artifact) + 3 (exit-8) = 169 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_exit_code_8.py
git commit -m "external-reviewer: detect rate-limit on subprocess failure, exit 8"
```

---

### Task 2.5: Pre-spawn check refuses when state is still active

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Create: `skills/external-review/tests/test_subsequent_invocation_refused.py`

- [ ] **Step 1: Write the failing test**

```python
# skills/external-review/tests/test_subsequent_invocation_refused.py
import json, os, subprocess, sys
from pathlib import Path
import datetime as dt
import importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "rs.json"))


def _make_repo(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\nbody\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    return repo


def test_active_limit_refuses_spawn(tmp_path, monkeypatch):
    """When state shows an active limit, the script must exit 8 without spawning."""
    state_file = tmp_path / "state.json"
    future = (dt.datetime.now() + dt.timedelta(hours=1)).isoformat(timespec="seconds")
    state_file.write_text(json.dumps({"schema_version": 1, "limits": {
        "fake-reviewer": {
            "limited": True, "limited_at": "x", "reset_at": future, "reset_source": "test",
            "raw_stderr_tail": "", "chain": "c", "round": 1,
        }
    }}))

    repo = _make_repo(tmp_path)
    # Reviewer simulator that would normally succeed — but the pre-spawn check
    # must refuse before it ever runs.
    sentinel = repo / "spawn-evidence.txt"
    reviewer = repo / "fake-reviewer"
    reviewer.write_text(f"#!/usr/bin/env bash\ntouch '{sentinel}'\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(state_file)

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == er.EXIT_CODE_RATE_LIMITED
    payload = json.loads(proc.stdout)
    assert payload["rate_limited"] is True
    # No spawn happened
    assert not sentinel.exists()


def test_expired_limit_clears_and_proceeds(tmp_path):
    """When reset_at is in the past, pre-spawn check clears the entry and proceeds."""
    state_file = tmp_path / "state.json"
    past = (dt.datetime.now() - dt.timedelta(hours=1)).isoformat(timespec="seconds")
    state_file.write_text(json.dumps({"schema_version": 1, "limits": {
        "fake-reviewer": {
            "limited": True, "limited_at": "x", "reset_at": past, "reset_source": "test",
            "raw_stderr_tail": "", "chain": "c", "round": 1,
        }
    }}))

    repo = _make_repo(tmp_path)
    reviewer = repo / "fake-reviewer"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(state_file)

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    # Entry should be removed from state
    state = json.loads(state_file.read_text())
    assert "fake-reviewer" not in state.get("limits", {})
```

- [ ] **Step 2: Verify failure**

Run: expected first test fails (spawn happens, exit code is 0 instead of 8).

- [ ] **Step 3: Add pre-spawn check in `run_one_reviewer`**

In `run_one_reviewer`, BEFORE the subprocess is built (i.e., before `subprocess.run([...])`):

```python
    # Pre-spawn rate-limit check
    key = reviewer_cmd_basename()
    active = get_active_limit(key)
    if active is not None:
        # First refusal in this chain → write a rate-limited round artifact.
        # (Coalescing onto an existing head round is handled in Slice 4.)
        write_rate_limited_artifact(
            chain_dir=chain_dir, round_num=round_num, timestamp=timestamp,
            reviewer_cmd=key, reset_at=active["reset_at"],
            raw_stderr_tail=active.get("raw_stderr_tail", ""),
        )
        raise ReviewerRateLimited(
            reviewer_cmd=key, reset_at=active["reset_at"],
            reset_source=active.get("reset_source", "unknown"),
            chain=chain_name, round_num=round_num,
            request_path=str(request_path),
            raw_stderr_tail=active.get("raw_stderr_tail", ""),
        )
```

Place this AFTER the request file is written (so `request_path` is in scope) but BEFORE the subprocess call.

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_subsequent_invocation_refused.py -v`
Expected: 2 passed.

Full suite:
`python3 -m pytest skills/external-review/tests/ -q`
Expected: 171 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_subsequent_invocation_refused.py
git commit -m "external-reviewer: pre-spawn check refuses when state shows active limit"
```

→ Invoke `superstar:external-review --kind post-slice --file <plan> --work-id S2 --review-depth thorough` (touches hot paths — `run_one_reviewer`) at slice close. Subject to the session-level bypass policy.

---

## Slice 3 — Rate-limited status semantics (4 sites)

### Task 3.1: Resolution gate bypasses `rate-limited` predecessor

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (find the resolution-gate check; in S1 it lives in `main()` around the post-slice/post-phase dispatch and checks `prior.get("status") == "failed"`)
- Create: `skills/external-review/tests/test_rate_limited_status_semantics.py`

- [ ] **Step 1: Write the failing test**

```python
# skills/external-review/tests/test_rate_limited_status_semantics.py
import json, os, subprocess, sys
from pathlib import Path
import datetime as dt
import importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "rs.json"))


def test_resolution_gate_bypasses_on_rate_limited_prior(tmp_path):
    """post-slice r2 must NOT demand a resolution doc if r1 was rate-limited."""
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    chain_dir = repo / "docs/reviewer/plan-X-post-slice"
    chain_dir.mkdir(parents=True)
    (chain_dir / "chain.json").write_text(json.dumps({
        "schema_version": 1, "chain": "plan-X-post-slice", "kind": "post-slice",
        "target": "plan.md", "work_id": "X", "legacy_migrated": False,
        "rounds": [{
            "round": 1, "status": "rate-limited", "verdict": None, "verdict_valid": False,
            "merged_verdict": None, "returncode": None,
        }],
        "sweep_checkpoints": {"first-round": "pending", "final-ready": "pending"},
    }))

    reviewer = repo / "fake.sh"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "rs.json")

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--file", "plan.md", "--work-id", "X", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    # Must succeed — bypass gate, no exit 3
    assert proc.returncode == 0, proc.stderr
```

- [ ] **Step 2: Verify failure**

Expected: returncode 3 (resolution-required gate).

- [ ] **Step 3: Update the resolution-gate check**

In `external-reviewer.py`, find the gate (look for the existing string `"failed"` near the resolution check; it'll look something like `if prior.get("status") == "failed": ... else: if not resolution_file.exists() ...`). Change to:

```python
    BYPASS_STATUSES = {"failed", "rate-limited"}
    if prior is not None and prior.get("status") in BYPASS_STATUSES:
        # Resolution gate bypassed — no findings to resolve on a process failure
        # or a rate-limited round.
        print(f"NOTE: resolution gate bypassed (prior round status={prior['status']})", file=sys.stderr)
    else:
        # existing resolution-required check
        ...
```

If the existing gate uses `if not file.exists(): exit(3)`, wrap accordingly.

- [ ] **Step 4: Run tests**

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_rate_limited_status_semantics.py
git commit -m "external-reviewer: bypass resolution gate on rate-limited predecessor"
```

---

### Task 3.2: Preamble walk-back skips `rate-limited` rounds

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`build_incremental_preamble`)
- Modify: `skills/external-review/tests/test_rate_limited_status_semantics.py`

- [ ] **Step 1: Write the failing test**

Append to `test_rate_limited_status_semantics.py`:

```python
def test_preamble_walks_back_past_rate_limited(tmp_path):
    """build_incremental_preamble should skip rate-limited rounds when finding
    the last trusted round, just like it does for failed/unknown."""
    chain_dir = tmp_path / "chain"; chain_dir.mkdir()
    (chain_dir / "r1-merged-findings.md").write_text("trusted r1 findings F1: ...\n")
    manifest = {
        "schema_version": 1, "chain": "demo", "kind": "post-slice", "target": "x",
        "work_id": None, "legacy_migrated": False,
        "rounds": [
            {"round": 1, "status": "ok", "verdict": "revise", "verdict_valid": True,
             "merged_verdict": "revise", "findings_count": 1, "blocking_findings_count": 1,
             "response": "r1-response.md", "merged_findings": "r1-merged-findings.md"},
            {"round": 2, "status": "rate-limited", "verdict": None, "verdict_valid": False,
             "merged_verdict": None, "returncode": None},
        ],
        "sweep_checkpoints": {"first-round": "done", "final-ready": "pending"},
    }
    out = er.build_incremental_preamble(
        manifest=manifest, chain_dir=chain_dir, round_num=3,
        resolution_waiver=True, legacy_first_round=False, diff_section="",
    )
    # Trusted round is r1 — its merged findings are embedded.
    assert "trusted r1 findings" in out
    # Annotation about skipped rounds mentions rate-limited
    assert "rounds 2..2 were" in out or "rate-limited" in out.lower()
```

- [ ] **Step 2: Verify failure**

Expected: trusted-finding text might be missing or skip annotation absent.

- [ ] **Step 3: Update `build_incremental_preamble`**

In `build_incremental_preamble`, find the walk-back loop. It already excludes `{"failed", "unknown"}`. Extend to include `"rate-limited"`:

```python
    BACKWARD_SKIP_STATUSES = {"failed", "unknown", "rate-limited"}
    # ... existing loop:
    # while trusted is not None and trusted.get("status") in BACKWARD_SKIP_STATUSES:
    #     trusted = ... (next-older round)
```

And the annotation string emitted to the preamble (currently mentions "process failures"):

```python
    if skipped_rounds:
        first, last = skipped_rounds[0], skipped_rounds[-1]
        annotation = (
            f"Note: rounds {first}..{last} were process failures, rate-limited, "
            f"or pre-S1 entries; skipped.\n"
        )
        preamble_parts.append(annotation)
```

- [ ] **Step 4: Run tests**

Expected: 2 passed in this file.

Full suite: should be 173 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_rate_limited_status_semantics.py
git commit -m "external-reviewer: preamble walk-back skips rate-limited rounds"
```

---

### Task 3.3: `compute_merged_verdict` excludes rate-limited reviewers

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Modify: `skills/external-review/tests/test_rate_limited_status_semantics.py`

- [ ] **Step 1: Write the failing test**

Append:

```python
def test_merged_verdict_excludes_rate_limited_reviewers():
    """If primary is ok and a sweep is rate-limited, merged verdict comes from primary only."""
    reviewers = [
        {"role": "primary", "verdict": "ready", "verdict_valid": True, "returncode": 0, "status": "ok"},
        {"role": "sweep",   "verdict": None,    "verdict_valid": False, "returncode": None, "status": "rate-limited"},
    ]
    merged = er.compute_merged_verdict(reviewers)
    assert merged == "ready"


def test_merged_verdict_all_rate_limited_returns_none():
    reviewers = [
        {"role": "primary", "verdict": None, "verdict_valid": False, "returncode": None, "status": "rate-limited"},
        {"role": "sweep",   "verdict": None, "verdict_valid": False, "returncode": None, "status": "rate-limited"},
    ]
    assert er.compute_merged_verdict(reviewers) is None
```

- [ ] **Step 2: Verify failure**

Expected: function currently filters only on `returncode == 0`; the rate-limited entry has `returncode: None` so it's already filtered out — test 1 may pass. Test 2 depends on whether the function currently handles "no ok reviewers" via returning None.

- [ ] **Step 3: Update `compute_merged_verdict`**

In `external-reviewer.py`, find the filter. Change to be status-aware:

```python
def compute_merged_verdict(reviewers: list[dict]) -> str | None:
    # Exclude reviewers whose status is failed or rate-limited (no real verdict).
    ok = [r for r in reviewers if r.get("status") == "ok" and r.get("verdict_valid")]
    if not ok:
        return None
    verdicts = [r.get("verdict") for r in ok]
    if any(v == "revise" for v in verdicts) or any(not r.get("verdict_valid") for r in ok):
        return "revise"
    if any(v == "ready with small edits" for v in verdicts):
        return "ready with small edits"
    if all(v == "ready" for v in verdicts):
        return "ready"
    return "revise"
```

(Adjust to whatever the existing logic does; the key change is filtering on `status == "ok"` not just `returncode == 0`. The two are usually equivalent today, but rate-limited rounds may have `returncode == 1` (the reviewer's own exit code), so the status filter is more precise.)

- [ ] **Step 4: Run tests**

Expected: 4 passed in this file.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_rate_limited_status_semantics.py
git commit -m "external-reviewer: merged verdict filter on status=='ok' (excludes rate-limited)"
```

---

### Task 3.4: `write_merged_findings` returns None when all reviewers are non-ok

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Modify: `skills/external-review/tests/test_rate_limited_status_semantics.py`

- [ ] **Step 1: Write the failing test**

Append:

```python
def test_write_merged_findings_returns_none_when_all_rate_limited(tmp_path):
    reviewers = [
        {"role": "primary", "status": "rate-limited", "review_path": str(tmp_path / "p.md"), "review": "..."},
        {"role": "sweep",   "status": "rate-limited", "review_path": str(tmp_path / "s.md"), "review": "..."},
    ]
    out_path = er.write_merged_findings(
        chain_dir=tmp_path, round_num=1, reviewers=reviewers,
    )
    assert out_path is None


def test_write_merged_findings_returns_path_when_one_ok(tmp_path):
    (tmp_path / "p.md").write_text("primary review body\n## verdict\nready\n")
    reviewers = [
        {"role": "primary", "status": "ok", "review_path": str(tmp_path / "p.md"), "review": "primary review body"},
        {"role": "sweep",   "status": "rate-limited", "review_path": "", "review": ""},
    ]
    out_path = er.write_merged_findings(
        chain_dir=tmp_path, round_num=1, reviewers=reviewers,
    )
    assert out_path is not None
    assert out_path.exists()
    body = out_path.read_text()
    # Only the ok reviewer's body appears
    assert "primary review body" in body
```

- [ ] **Step 2: Verify failure**

Expected: existing logic may include non-ok reviewers or fail differently.

- [ ] **Step 3: Update `write_merged_findings`**

```python
def write_merged_findings(*, chain_dir, round_num, reviewers, ...):
    ok = [r for r in reviewers if r.get("status") == "ok"]
    if not ok:
        return None
    # ... existing concatenation logic, but iterate over `ok` instead of `reviewers`
```

- [ ] **Step 4: Run tests**

Expected: 6 passed in this file.

Full suite: 177 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_rate_limited_status_semantics.py
git commit -m "external-reviewer: merged findings excludes non-ok reviewers (rate-limited + failed)"
```

→ Invoke `superstar:external-review --kind post-slice --work-id S3 --review-depth thorough` (status-semantics is hot-path correctness). Subject to bypass.

---

## Slice 4 — Refusal coalescing

### Task 4.1: Coalesce repeated pre-spawn refusals onto head round

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`run_one_reviewer` pre-spawn check)
- Create: `skills/external-review/tests/test_refusal_coalescing.py`

- [ ] **Step 1: Write the failing test**

```python
# skills/external-review/tests/test_refusal_coalescing.py
import json, os, subprocess, sys
from pathlib import Path
import datetime as dt
import importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "rs.json"))


def _setup(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    state_file = tmp_path / "state.json"
    future = (dt.datetime.now() + dt.timedelta(hours=1)).isoformat(timespec="seconds")
    state_file.write_text(json.dumps({"schema_version": 1, "limits": {
        "fake": {"limited": True, "limited_at": "x", "reset_at": future,
                 "reset_source": "test", "raw_stderr_tail": "", "chain": "c", "round": 1}
    }}))
    reviewer = repo / "fake"
    reviewer.write_text("#!/usr/bin/env bash\necho ready\n")
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(state_file)
    return repo, env


def _invoke(repo, env, args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py")] + args,
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )


def test_two_refusals_coalesce_into_one_round(tmp_path):
    repo, env = _setup(tmp_path)
    # First call → writes r1 as rate-limited
    p1 = _invoke(repo, env, ["review", "--kind", "plan", "--file", "plan.md", "--emit", "json"])
    assert p1.returncode == er.EXIT_CODE_RATE_LIMITED
    chain_dir = next((repo / "docs/reviewer").iterdir())
    manifest = json.loads((chain_dir / "chain.json").read_text())
    assert len(manifest["rounds"]) == 1
    # Second call → must NOT append a second round
    p2 = _invoke(repo, env, ["review", "--kind", "plan", "--file", "plan.md", "--emit", "json"])
    assert p2.returncode == er.EXIT_CODE_RATE_LIMITED
    manifest = json.loads((chain_dir / "chain.json").read_text())
    assert len(manifest["rounds"]) == 1
    # last_refused_at and refused_at[] updated on the head round
    head = manifest["rounds"][-1]
    assert head["status"] == "rate-limited"
    assert "last_refused_at" in head
    assert len(head.get("refused_at", [])) >= 2


def test_refused_at_caps_at_20(tmp_path):
    repo, env = _setup(tmp_path)
    for _ in range(25):
        _invoke(repo, env, ["review", "--kind", "plan", "--file", "plan.md", "--emit", "json"])
    chain_dir = next((repo / "docs/reviewer").iterdir())
    manifest = json.loads((chain_dir / "chain.json").read_text())
    head = manifest["rounds"][-1]
    assert len(head["refused_at"]) <= 20
```

- [ ] **Step 2: Verify failure**

Expected: each call appends a new round; manifest grows.

- [ ] **Step 3: Update pre-spawn check to coalesce**

Replace the body of the pre-spawn block (Task 2.5's addition) with:

```python
    # Pre-spawn rate-limit check (with coalescing)
    key = reviewer_cmd_basename()
    active = get_active_limit(key)
    if active is not None:
        chain_manifest = read_manifest(chain_dir)  # existing helper
        head = chain_manifest["rounds"][-1] if chain_manifest["rounds"] else None
        if head and head.get("status") == "rate-limited":
            # Coalesce onto head round
            head.setdefault("refused_at", []).append(_now_local().isoformat(timespec="seconds"))
            head["refused_at"] = head["refused_at"][-20:]  # cap
            head["last_refused_at"] = head["refused_at"][-1]
            write_manifest(chain_dir, chain_manifest)
            raise ReviewerRateLimited(
                reviewer_cmd=key, reset_at=active["reset_at"],
                reset_source=active.get("reset_source", "unknown"),
                chain=chain_dir.name, round_num=head["round"],
                request_path=str(chain_dir / f"r{head['round']}-coalesced-request.md"),  # synthetic; no new request file
                raw_stderr_tail=active.get("raw_stderr_tail", ""),
            )
        else:
            # First refusal in this chain — append a new rate-limited round
            write_rate_limited_artifact(...)
            # Append to chain_manifest with status=rate-limited
            new_round = {
                "round": (head["round"] + 1) if head else 1,
                "status": "rate-limited",
                "verdict": None, "verdict_valid": False, "merged_verdict": None,
                "reset_at": active["reset_at"],
                "limited_at": _now_local().isoformat(timespec="seconds"),
                "refused_at": [_now_local().isoformat(timespec="seconds")],
                "last_refused_at": _now_local().isoformat(timespec="seconds"),
                "reviewer_cmd": key,
            }
            chain_manifest["rounds"].append(new_round)
            write_manifest(chain_dir, chain_manifest)
            raise ReviewerRateLimited(...)
```

(Adjust `read_manifest`/`write_manifest` names to match the existing helpers in the script.)

- [ ] **Step 4: Run tests**

Expected: 2 passed in `test_refusal_coalescing.py`.
Plus regression check on `test_subsequent_invocation_refused.py`: should still pass (it only invokes once).

Full suite: 179 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_refusal_coalescing.py
git commit -m "external-reviewer: coalesce repeated rate-limit refusals onto head round"
```

→ Invoke `superstar:external-review --kind post-slice --work-id S4 --review-depth standard`. Subject to bypass.

---

## Slice 5 — New subcommands

### Task 5.1: `manual-approve` subcommand

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (argparse + handler)
- Create: `skills/external-review/tests/test_manual_approve_subcommand.py`

- [ ] **Step 1: Write the failing test**

```python
# skills/external-review/tests/test_manual_approve_subcommand.py
import json, os, subprocess, sys
from pathlib import Path
import importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "rs.json"))


def _setup_chain(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    chain_dir = repo / "docs/reviewer/plan-X-post-slice"
    chain_dir.mkdir(parents=True)
    (chain_dir / "chain.json").write_text(json.dumps({
        "schema_version": 1, "chain": "plan-X-post-slice", "kind": "post-slice",
        "target": "plan.md", "work_id": "X", "legacy_migrated": False,
        "rounds": [{"round": 1, "status": "rate-limited", "verdict": None, "verdict_valid": False}],
        "sweep_checkpoints": {"first-round": "pending", "final-ready": "pending"},
    }))
    return repo, chain_dir


def test_manual_approve_writes_synthetic_round(tmp_path):
    repo, chain_dir = _setup_chain(tmp_path)
    env = os.environ.copy()
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "rs.json")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "manual-approve", "--kind", "post-slice", "--file", "plan.md",
         "--work-id", "X", "--note", "Approved at standup — codex still down."],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((chain_dir / "chain.json").read_text())
    head = manifest["rounds"][-1]
    assert head["status"] == "manual-approved"
    assert head["verdict"] == "ready"
    assert head["verdict_valid"] is True
    assert head["approval_note"] == "Approved at standup — codex still down."
    assert "approved_by" in head and head["approved_by"]
    # Response file exists and contains the note + verdict line
    r2 = chain_dir / f"r{head['round']}-response.md"
    # Filename may include a timestamp; tolerate either
    candidates = list(chain_dir.glob(f"r{head['round']}-*response.md"))
    assert candidates
    body = candidates[0].read_text()
    assert "Approved at standup — codex still down." in body
    assert "Overall verdict: ready (manual approval)" in body
```

- [ ] **Step 2: Verify failure**

Expected: argparse rejects `manual-approve` subcommand.

- [ ] **Step 3: Implement the subcommand**

In `external-reviewer.py`'s argparse setup, add a sub-parser:

```python
    sp_manual = subparsers.add_parser("manual-approve", help="Mark a chain as manually approved")
    sp_manual.add_argument("--kind", required=True)
    sp_manual.add_argument("--file", required=True)
    sp_manual.add_argument("--work-id", required=False, default=None)
    sp_manual.add_argument("--note", required=True)
    sp_manual.add_argument("--state-file", default=None)
```

In `main()`, add the dispatch branch:

```python
    if args.command == "manual-approve":
        if args.state_file:
            os.environ["AGENT_REVIEWER_STATE_FILE"] = args.state_file
        return run_manual_approve(args)
```

Implement `run_manual_approve`:

```python
def run_manual_approve(args) -> int:
    target = Path(args.file).resolve()
    chain_dir = resolve_chain_dir(target=target, kind=args.kind, work_id=args.work_id)  # existing helper
    manifest = read_manifest(chain_dir)
    head = manifest["rounds"][-1] if manifest["rounds"] else None
    next_round = (head["round"] + 1) if head else 1
    approver = _git_identity()
    now_iso = _now_local().isoformat(timespec="seconds")
    timestamp = _now_local().strftime("%Y-%m-%dT%H%M")
    response_path = chain_dir / f"r{next_round}-{timestamp}-response.md"
    response_body = (
        f"# Manual approval — {chain_dir.name} r{next_round}\n\n"
        f"Approved by: {approver}\n"
        f"Approved at: {now_iso}\n\n"
        f"## Note\n{args.note}\n\n---\n\n"
        f"Overall verdict: ready (manual approval)\n"
    )
    response_path.write_text(response_body, encoding="utf-8")
    new_round = {
        "round": next_round,
        "status": "manual-approved",
        "verdict": "ready",
        "verdict_valid": True,
        "merged_verdict": "ready",
        "response": response_path.name,
        "approved_by": approver,
        "approved_at": now_iso,
        "approval_note": args.note,
    }
    manifest["rounds"].append(new_round)
    write_manifest(chain_dir, manifest)
    print(f"Manual approval recorded for {chain_dir.name} r{next_round}")
    return 0


def _git_identity() -> str:
    try:
        name = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True).stdout.strip()
        email = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True).stdout.strip()
        if name and email:
            return f"{name} <{email}>"
    except Exception:
        pass
    return os.environ.get("USER", "unknown") + "@" + os.uname().nodename
```

- [ ] **Step 4: Run tests**

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_manual_approve_subcommand.py
git commit -m "external-reviewer: manual-approve subcommand"
```

---

### Task 5.2: `ingest-response` subcommand (paste + link, with reformat)

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Create: `skills/external-review/tests/test_ingest_response_subcommand.py`

- [ ] **Step 1: Write the failing tests**

```python
# skills/external-review/tests/test_ingest_response_subcommand.py
import json, os, subprocess, sys
from pathlib import Path
import importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "rs.json"))


def _setup_chain(tmp_path):
    # Same shape as in test_manual_approve_subcommand
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    chain_dir = repo / "docs/reviewer/plan-X-post-slice"
    chain_dir.mkdir(parents=True)
    (chain_dir / "chain.json").write_text(json.dumps({
        "schema_version": 1, "chain": "plan-X-post-slice", "kind": "post-slice",
        "target": "plan.md", "work_id": "X", "legacy_migrated": False,
        "rounds": [{"round": 1, "status": "rate-limited", "verdict": None, "verdict_valid": False}],
        "sweep_checkpoints": {"first-round": "pending", "final-ready": "pending"},
    }))
    return repo, chain_dir


VALID_RESPONSE = """# External reviewer response
Some findings...
Overall verdict: ready with small edits
"""


def test_ingest_response_from_paste(tmp_path):
    repo, chain_dir = _setup_chain(tmp_path)
    paste_file = tmp_path / "pasted.md"
    paste_file.write_text(VALID_RESPONSE)
    env = os.environ.copy()
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "rs.json")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "ingest-response", "--kind", "post-slice", "--file", "plan.md",
         "--work-id", "X", "--from-paste", str(paste_file)],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((chain_dir / "chain.json").read_text())
    head = manifest["rounds"][-1]
    assert head["status"] == "human-bridged"
    assert head["verdict"] == "ready with small edits"
    candidates = list(chain_dir.glob(f"r{head['round']}-*response.md"))
    assert candidates
    body = candidates[0].read_text()
    assert "Overall verdict: ready with small edits" in body


def test_ingest_response_from_link_strips_outer_fence(tmp_path):
    repo, chain_dir = _setup_chain(tmp_path)
    linked = tmp_path / "fenced.md"
    fenced = f"```\n{VALID_RESPONSE}\n```\n"
    linked.write_text(fenced)
    env = os.environ.copy()
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "rs.json")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "ingest-response", "--kind", "post-slice", "--file", "plan.md",
         "--work-id", "X", "--from-link", str(linked)],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, proc.stderr
    candidates = list(chain_dir.glob("r*-response.md"))
    body = candidates[0].read_text()
    assert "Overall verdict: ready with small edits" in body
    # Outer fence stripped
    assert not body.startswith("```")


def test_ingest_response_rewrites_heading_style_verdict(tmp_path):
    repo, chain_dir = _setup_chain(tmp_path)
    weird = tmp_path / "weird.md"
    # The format that confused the parser this session
    weird.write_text("# foo\n\nfindings ...\n\n5. Overall verdict\n\nready\n")
    env = os.environ.copy()
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "rs.json")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "ingest-response", "--kind", "post-slice", "--file", "plan.md",
         "--work-id", "X", "--from-paste", str(weird)],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0
    manifest = json.loads((chain_dir / "chain.json").read_text())
    head = manifest["rounds"][-1]
    assert head["verdict"] == "ready"


def test_ingest_response_unparseable_exits_2(tmp_path):
    repo, chain_dir = _setup_chain(tmp_path)
    bad = tmp_path / "bad.md"
    bad.write_text("some text without a verdict line\n")
    env = os.environ.copy()
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "rs.json")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "ingest-response", "--kind", "post-slice", "--file", "plan.md",
         "--work-id", "X", "--from-paste", str(bad)],
        cwd=repo, env=env, capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 2
    # Response file STILL written
    candidates = list(chain_dir.glob("r*-response.md"))
    assert candidates
```

- [ ] **Step 2: Verify failure**

Expected: argparse rejects `ingest-response`.

- [ ] **Step 3: Implement the subcommand**

Argparse:

```python
    sp_ingest = subparsers.add_parser("ingest-response", help="Ingest an externally-obtained reviewer response")
    sp_ingest.add_argument("--kind", required=True)
    sp_ingest.add_argument("--file", required=True)
    sp_ingest.add_argument("--work-id", required=False, default=None)
    src_group = sp_ingest.add_mutually_exclusive_group(required=True)
    src_group.add_argument("--from-paste", dest="from_paste", default=None)
    src_group.add_argument("--from-link", dest="from_link", default=None)
    sp_ingest.add_argument("--state-file", default=None)
```

Dispatch:

```python
    if args.command == "ingest-response":
        if args.state_file:
            os.environ["AGENT_REVIEWER_STATE_FILE"] = args.state_file
        return run_ingest_response(args)
```

Implementation:

```python
_OUTER_FENCE_RE = re.compile(r"^\s*```[a-zA-Z0-9_-]*\s*\n(.*?)\n```\s*$", re.DOTALL)
_VERDICT_HEADING_STYLE = re.compile(
    r"((?:\d+\.\s+)?Overall verdict)\s*\n+\s*(ready(?: with small edits)?|revise|ready)",
    re.IGNORECASE,
)


def _reformat_response(raw: str) -> str:
    # Strip a single outer fence pair
    m = _OUTER_FENCE_RE.match(raw)
    if m:
        raw = m.group(1)
    # Heading-style "Overall verdict\n\nX" → inline
    raw = _VERDICT_HEADING_STYLE.sub(lambda m: f"{m.group(1)}: {m.group(2)}", raw)
    return raw


def run_ingest_response(args) -> int:
    src = args.from_paste or args.from_link
    raw = Path(src).read_text(encoding="utf-8")
    reformatted = _reformat_response(raw)

    target = Path(args.file).resolve()
    chain_dir = resolve_chain_dir(target=target, kind=args.kind, work_id=args.work_id)
    manifest = read_manifest(chain_dir)
    head = manifest["rounds"][-1] if manifest["rounds"] else None
    next_round = (head["round"] + 1) if head else 1
    timestamp = _now_local().strftime("%Y-%m-%dT%H%M")
    response_path = chain_dir / f"r{next_round}-{timestamp}-response.md"
    response_path.write_text(reformatted, encoding="utf-8")

    verdict = parse_verdict(reformatted)  # existing helper
    bridger = _git_identity()
    now_iso = _now_local().isoformat(timespec="seconds")
    new_round = {
        "round": next_round,
        "status": "human-bridged",
        "verdict": verdict,
        "verdict_valid": verdict is not None,
        "merged_verdict": verdict,
        "response": response_path.name,
        "bridged_by": bridger,
        "bridged_at": now_iso,
    }
    manifest["rounds"].append(new_round)
    write_manifest(chain_dir, manifest)

    if verdict is None:
        print(f"WARNING: response ingested but verdict unparseable; {response_path}", file=sys.stderr)
        return 2
    print(f"Human-bridged response recorded: {chain_dir.name} r{next_round} verdict={verdict}")
    return 0
```

- [ ] **Step 4: Run tests**

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_ingest_response_subcommand.py
git commit -m "external-reviewer: ingest-response subcommand (paste/link, reformat)"
```

---

### Task 5.3: `show-limit` + `clear-limit` subcommands

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Create: `skills/external-review/tests/test_show_clear_limit.py`

- [ ] **Step 1: Write the failing tests**

```python
# skills/external-review/tests/test_show_clear_limit.py
import json, os, subprocess, sys
from pathlib import Path
import datetime as dt
import importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "rs.json"))


def _populate(state_file, key="codex"):
    future = (dt.datetime.now() + dt.timedelta(hours=1)).isoformat(timespec="seconds")
    Path(state_file).write_text(json.dumps({"schema_version": 1, "limits": {
        key: {"limited": True, "limited_at": "x", "reset_at": future,
              "reset_source": "test", "raw_stderr_tail": "...", "chain": "c", "round": 1}
    }}))


def _run(args, env):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py")] + args,
        env=env, capture_output=True, text=True, timeout=10,
    )


def test_show_limit_with_entry(tmp_path):
    state_file = tmp_path / "rs.json"
    _populate(state_file)
    env = os.environ.copy(); env["AGENT_REVIEWER_STATE_FILE"] = str(state_file)
    proc = _run(["show-limit"], env)
    assert proc.returncode == 0
    assert "codex" in proc.stdout
    assert "limited" in proc.stdout


def test_show_limit_empty(tmp_path):
    env = os.environ.copy(); env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "absent.json")
    proc = _run(["show-limit"], env)
    assert proc.returncode == 0
    assert "no active limits" in proc.stdout.lower()


def test_clear_limit_removes_entry(tmp_path):
    state_file = tmp_path / "rs.json"
    _populate(state_file, key="codex")
    env = os.environ.copy(); env["AGENT_REVIEWER_STATE_FILE"] = str(state_file)
    proc = _run(["clear-limit", "--reviewer-cmd", "codex"], env)
    assert proc.returncode == 0
    state = json.loads(state_file.read_text())
    assert "codex" not in state["limits"]


def test_clear_limit_all_when_no_filter(tmp_path):
    state_file = tmp_path / "rs.json"
    future = (dt.datetime.now() + dt.timedelta(hours=1)).isoformat(timespec="seconds")
    state_file.write_text(json.dumps({"schema_version": 1, "limits": {
        "codex": {"limited": True, "reset_at": future, "limited_at": "x", "reset_source": "t", "raw_stderr_tail": "", "chain": "c", "round": 1},
        "claude": {"limited": True, "reset_at": future, "limited_at": "x", "reset_source": "t", "raw_stderr_tail": "", "chain": "c", "round": 1},
    }}))
    env = os.environ.copy(); env["AGENT_REVIEWER_STATE_FILE"] = str(state_file)
    proc = _run(["clear-limit"], env)
    assert proc.returncode == 0
    assert json.loads(state_file.read_text())["limits"] == {}


def test_clear_limit_idempotent_on_missing(tmp_path):
    env = os.environ.copy(); env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "absent.json")
    proc = _run(["clear-limit", "--reviewer-cmd", "codex"], env)
    assert proc.returncode == 0
```

- [ ] **Step 2: Verify failure**

Expected: argparse rejects both subcommands.

- [ ] **Step 3: Implement**

Argparse:

```python
    sp_show = subparsers.add_parser("show-limit", help="Print active reviewer limits")
    sp_show.add_argument("--state-file", default=None)
    sp_clear = subparsers.add_parser("clear-limit", help="Clear reviewer limit state")
    sp_clear.add_argument("--reviewer-cmd", default=None)
    sp_clear.add_argument("--state-file", default=None)
```

Handlers:

```python
def run_show_limit(args) -> int:
    state = load_state()
    if not state["limits"]:
        print("(no active limits)")
        return 0
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0


def run_clear_limit(args) -> int:
    state = load_state()
    if args.reviewer_cmd:
        state["limits"].pop(args.reviewer_cmd, None)
    else:
        state["limits"] = {}
    save_state(state)
    return 0
```

Dispatch in `main()`:

```python
    if args.command == "show-limit":
        if args.state_file:
            os.environ["AGENT_REVIEWER_STATE_FILE"] = args.state_file
        return run_show_limit(args)
    if args.command == "clear-limit":
        if args.state_file:
            os.environ["AGENT_REVIEWER_STATE_FILE"] = args.state_file
        return run_clear_limit(args)
```

- [ ] **Step 4: Run tests**

Expected: 5 passed.

Full suite: 189 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_show_clear_limit.py
git commit -m "external-reviewer: show-limit + clear-limit subcommands"
```

---

### Task 5.4: Sweep partial rate-limit case

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (sweep handling within `run_one_reviewer` when a single reviewer's subprocess fails with rate-limit but others succeed)
- Create: `skills/external-review/tests/test_sweep_partial_rate_limit.py`

- [ ] **Step 1: Write the failing test**

```python
# skills/external-review/tests/test_sweep_partial_rate_limit.py
import json, os, subprocess, sys
from pathlib import Path
import importlib.util
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "rs.json"))


def test_sweep_rate_limited_primary_ok_round_still_succeeds(tmp_path):
    """When the primary succeeds and a sweep is rate-limited, the round still
    returns the primary's verdict; the sweep is recorded as status=rate-limited
    in reviewers[]; state file IS written so subsequent runs refuse pre-spawn."""
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    # The reviewer command is invoked once per role (primary, sweep1) with
    # different env hints (existing sweep dispatch convention). Simulate by
    # making the binary check $REVIEWER_ROLE and behave differently.
    reviewer = repo / "reviewer.sh"
    reviewer.write_text(
        "#!/usr/bin/env bash\n"
        "if [ \"$REVIEWER_ROLE\" = \"sweep1\" ]; then\n"
        "  echo \"ERROR: You've hit your usage limit. Try again at 11:59 PM.\" >&2\n"
        "  exit 1\n"
        "else\n"
        "  echo 'Overall verdict: ready'\n"
        "  exit 0\n"
        "fi\n"
    )
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "rs.json")

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md",
         "--review-depth", "thorough", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    # Round succeeded (primary was ok)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["merged_verdict"] == "ready"
    roles = {r["role"]: r["status"] for r in payload["reviewers"]}
    assert roles.get("primary") == "ok"
    # The sweep entry has status=rate-limited (sweep code may differ; this is the contract)
    sweep_status = [v for k, v in roles.items() if k.startswith("sweep")]
    assert sweep_status and sweep_status[0] == "rate-limited"
    # State file written
    state_file = tmp_path / "rs.json"
    state = json.loads(state_file.read_text())
    assert state["limits"]  # not empty
```

(Note: the env-var-based role hint `REVIEWER_ROLE` is a stand-in. If the script doesn't pass such a hint today, this test needs to mock the sweep dispatch a different way. Implementation note in Step 3 explains.)

- [ ] **Step 2: Verify failure**

Expected: either the round fails outright (primary's failed-round logic propagates), or the sweep's failure is recorded as `status="failed"`, not `"rate-limited"`.

- [ ] **Step 3: Update sweep handling**

In the sweep dispatch within `run_one_reviewer` (or wherever each sweep reviewer is invoked), apply the same rate-limit detection logic per-reviewer:

```python
    for sweep_idx, sweep_cmd in enumerate(sweeps, start=1):
        sweep_result = subprocess.run(sweep_cmd, ...)
        if sweep_result.returncode != 0:
            matched, reset_at, pattern_name = detect_rate_limit(sweep_result.stderr or "")
            if matched:
                # Record this sweep as rate-limited; write state; do NOT propagate
                # ReviewerRateLimited (the primary may have succeeded — round can still close).
                key = reviewer_cmd_basename()
                reset_iso = (reset_at or _fallback_reset_time()).isoformat(timespec="seconds")
                state = load_state()
                state["limits"][key] = {
                    "limited": True, "limited_at": _now_local().isoformat(timespec="seconds"),
                    "reset_at": reset_iso,
                    "reset_source": f"regex:{pattern_name}" if pattern_name else "fallback",
                    "raw_stderr_tail": (sweep_result.stderr or "")[-2048:],
                    "chain": chain_name, "round": round_num,
                }
                save_state(state)
                reviewers_record.append({
                    "role": f"sweep{sweep_idx}", "status": "rate-limited",
                    "verdict": None, "verdict_valid": False, "returncode": sweep_result.returncode,
                    "review_path": "", "review": "",
                })
                continue
            # else: existing failed-sweep path
        # else: existing ok-sweep path
```

If `chain_name` isn't in scope, derive from `chain_dir.name`.

- [ ] **Step 4: Run tests**

Expected: 1 passed.

Full suite: 190 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_sweep_partial_rate_limit.py
git commit -m "external-reviewer: partial rate-limit on sweep records per-reviewer status"
```

→ Invoke `superstar:external-review --kind post-slice --work-id S5 --review-depth standard`. Subject to bypass.

---

## Slice 6 — SKILL.md updates

### Task 6.1: Add "Rate-limit handling" section to SKILL.md

**Files:**
- Modify: `skills/external-review/SKILL.md`

- [ ] **Step 1: Add the new section**

In `skills/external-review/SKILL.md`, immediately before the existing "## Reporting back to the user" section (or in a logical place — find where the "Failure handling" section currently lives and add this just after it), insert:

```markdown
## Rate-limit handling

When the reviewer's provider rate-limits the configured command (e.g. codex usage cap, Claude API quota), the script detects the failure mode distinctly from a generic crash and stops to ask the operator.

**Exit code 8** signals "reviewer rate-limited; pick a recovery path." On exit 8 the script emits this JSON on stdout:

```json
{
  "rate_limited": true,
  "reviewer_cmd": "<basename>",
  "reset_at":    "<ISO local time>",
  "reset_source": "regex:<pattern-name>",
  "chain":  "<chain folder name>",
  "round":  <int>,
  "request_path": "<absolute path>",
  "raw_stderr_tail": "<last 2 KB of reviewer stderr>"
}
```

Persistent state lives at `~/.config/superstar/reviewer-state.json` (override via `AGENT_REVIEWER_STATE_FILE` or `--state-file`). Subsequent invocations against any chain refuse to spawn until `reset_at` passes.

### The recovery menu

On exit 8 the coordinator MUST present this menu via `AskUserQuestion` (no auto-pick):

| Option | Mechanism |
|---|---|
| **Manual approve** | Coordinator collects a one-line note, then runs `external-reviewer.py manual-approve --kind X --file Y --work-id Z --note "..."`. Writes a synthetic round with `status: "manual-approved"`, `verdict: "ready"`. Chain advances. |
| **Schedule retry** | Coordinator invokes the **harness-level `schedule` skill** to register a one-shot routine at `reset_at + 5 min` re-invoking the same `review` command. If the harness lacks `schedule`, falls back to printing an `at`/`cron`-suitable command for the operator. Current chain gate pauses. |
| **Human bridge** | Coordinator prints `r{N}-request.md` path. Operator obtains a response from an external reviewer (web UI, manual reading, etc.) and either pastes the text in chat or provides a local file path. Coordinator runs `external-reviewer.py ingest-response --kind X --file Y --work-id Z (--from-paste FILE \| --from-link PATH)`. Writes the response with status `human-bridged`. |
| **Hold** | Do nothing. Exit the current gate. State persists; next session sees the same limit. |

Repeated refusals against the **same chain** while the limit is open do NOT append new rounds — they coalesce onto the head rate-limited round via `last_refused_at` / `refused_at[]` (capped at 20).

### Status semantics

A `status: "rate-limited"` round is treated symmetrically with `status: "failed"`:
- The resolution-required gate is bypassed for the next round.
- `build_incremental_preamble` walks back past it to find the last `ok` round.
- It is excluded from `merged_verdict` and `write_merged_findings` aggregation.

Manual-approved (`status: "manual-approved"`) and human-bridged (`status: "human-bridged"`) rounds carry real verdicts and pass through the existing gating machinery unchanged.

### Subcommands at a glance

| Subcommand | Purpose |
|---|---|
| `manual-approve` | Record an operator-approved closure on the chain. |
| `ingest-response` | Write an externally-obtained reviewer response into the chain. |
| `show-limit` | Print the current `~/.config/superstar/reviewer-state.json` content. |
| `clear-limit [--reviewer-cmd X]` | Clear the limit entry (for a single reviewer or all). Idempotent. |
```

- [ ] **Step 2: Update the "Exit codes" table**

Find the exit-codes table in SKILL.md. Add the row:

```
| 8 | Reviewer rate-limited. | Read the JSON payload; pick a recovery path from the menu in "Rate-limit handling". |
```

- [ ] **Step 3: Update the "Red flags" table**

In SKILL.md's red-flags table, add:

```
| "Saw exit 8, retried without surfacing the menu" | The menu must be presented every time exit 8 fires. Coordinator does not auto-pick. |
```

- [ ] **Step 4: Run tests + sanity-read**

`python3 -m pytest skills/external-review/tests/ -q` — confirm still 190 passed (no test depends on SKILL.md content).

Skim the whole SKILL.md file. The new section should fit the existing terse, sectioned tone.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/SKILL.md
git commit -m "external-review: document rate-limit handling (exit 8, menu, subcommands)"
```

→ Invoke `superstar:external-review --kind post-slice --work-id S6 --review-depth standard` (docs-only). Subject to bypass.

---

## Slice 7 — Acceptance

### Task 7.1: Full suite + acceptance checks

- [ ] **Step 1: Run the full suite**

`python3 -m pytest skills/external-review/tests/ -v 2>&1 | tail -30`
Expected: 190 passed (142 baseline + 48 added across S1–S5; adjust if some new tests collapsed during implementation). No `xfail`s.

Record the actual pass count for the close-out note.

- [ ] **Step 2: End-to-end smoke check**

Run, from /home/simon/Dev/sigreer/skills/superstar:

```bash
cd /tmp && rm -rf rl-smoke && mkdir rl-smoke && cd rl-smoke
git init -q && git commit -q --allow-empty -m init
printf '# plan\n' > plan.md && git add . && git commit -qm plan

# Step A: simulate rate-limit on first review
cat > fake.sh <<'EOF'
#!/usr/bin/env bash
echo "ERROR: You've hit your usage limit. Try again at 11:59 PM." >&2
exit 1
EOF
chmod +x fake.sh
export AGENT_REVIEWER_CMD="$PWD/fake.sh"
export AGENT_REVIEWER_STATE_FILE="$PWD/rs.json"

python3 /home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py \
  review --kind plan --file plan.md --emit json
echo "exit=$?"
# Expected: exit=8

# Step B: verify state file written
cat rs.json | python3 -m json.tool

# Step C: subsequent invocation refused without spawning
rm -f spawn-evidence
cat > fake.sh <<'EOF'
#!/usr/bin/env bash
touch spawn-evidence
echo "Overall verdict: ready"
EOF
chmod +x fake.sh
python3 /home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py \
  review --kind plan --file plan.md --emit json
echo "exit=$?"
test -f spawn-evidence && echo "FAIL: reviewer spawned" || echo "OK: no spawn"

# Step D: manual-approve closes the chain
python3 /home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py \
  manual-approve --kind plan --file plan.md --note "smoke-test approval"
echo "exit=$?"
# Expected: exit=0

# Cleanup
unset AGENT_REVIEWER_CMD AGENT_REVIEWER_STATE_FILE
```

Expected outcomes inline above. Record any deviation in the close-out commit.

- [ ] **Step 3: Commit any final fixes**

If the smoke check surfaced anything broken, commit the fix:

```bash
git add <files>
git commit -m "external-reviewer: rate-limit phase-close polish"
```

Slice 7 acceptance is met when:
- All 190+ tests green, no related xfail.
- Smoke check exit codes match the expected values.

→ Invoke `superstar:external-review --kind post-phase --file <plan> --context <spec>` to gate phase close. Subject to bypass.

---

## Phase close

After Slice 7:

- [ ] **Step 1: Final test count recorded** in the phase-close commit message.
- [ ] **Step 2: SKILL.md final sanity-read** — confirm "Rate-limit handling" section reads well and table cells render correctly.
- [ ] **Step 3: Invoke `superstar:finishing-a-development-branch`** to integrate the work.

---

## Bypass note

External-review gates at slice and phase boundaries are part of the project's normal workflow. If the user has bypassed external-review for this work session (because the reviewer is itself rate-limited, or because that's been explicitly requested), the coordinator skips those invocations and proceeds. Subagents dispatched during implementation MUST receive explicit instructions NOT to invoke `superstar:external-review` for any reason, since they would otherwise auto-apply the gate.
