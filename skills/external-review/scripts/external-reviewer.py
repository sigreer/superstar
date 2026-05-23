#!/usr/bin/env python3
"""
File-based bridge for third-party spec/plan review.

The script is intentionally provider-neutral. It builds a review prompt around
one target document, calls a configured reviewer command, and stores both the
request and the response under a per-chain folder at
docs/reviewer/<target-stem-no-date>-<kind>/. Each invocation is a new round —
existing rounds are never overwritten. Round number is derived from the count
of rN-*-request.md files already in the chain folder.

Configuration:
  AGENT_REVIEWER_CMD='reviewer-agent'
  AGENT_REVIEWER_TRANSPORT='stdin'

If the command contains placeholders, it is executed through the shell after
substitution. If it contains no placeholders, the prompt is supplied according
to --prompt-transport: via stdin (default), as one argument, or as a prompt-file
path.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

# Self-register in sys.modules so @dataclass works when this script is loaded
# via importlib.util.spec_from_file_location without prior registration
# (Python 3.12+ dataclasses inspect sys.modules[cls.__module__]).
if __name__ not in sys.modules:
    import types as _types
    _self_mod = _types.ModuleType(__name__)
    _self_mod.__dict__.update(globals())
    sys.modules[__name__] = _self_mod


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

End your review with this exact line, as plain text on its own line:

    Overall verdict: <ready|ready with small edits|revise>

Do not bold, italicise, prefix with `##`, split across lines, or drop the
word "Overall". Do not write `**Verdict: ready**` or place the value on a
new line after a heading.

Read the files from disk. Do not rely only on the snippets in this prompt.
"""


MODE_GUIDANCE = {
    "spec": """Pre-implementation spec review. Check that the spec is complete,
internally consistent, grounded in the existing codebase, and specific enough to
drive an implementation plan. Do not review implemented code unless the spec
claims code already exists.""",
    "plan": """Pre-implementation plan review. Check that the plan faithfully
covers the associated spec, uses existing repo patterns, has executable tasks,
has realistic ordering, and includes concrete verification gates.""",
    "design": """Design artifact review. Check coverage, route/component mapping,
accessibility, responsive states, missing screens, and whether the design can be
implemented in the current repo without inventing unsupported abstractions.""",
    "implementation": """Implementation review. Check code changes against the
stated task, looking for behavioral regressions, missing tests, accidental
scope expansion, and repo-pattern drift.""",
    "post-slice": """Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.""",
    "post-phase": """Post-phase review. Treat this as a closeout gate for a whole
phase. Compare the implementation, archive/TASKLIST updates, and verification
evidence against the phase spec/plan. Prioritize: unresolved acceptance
criteria, stale docs, missing archive notes, cross-cutting tracker drift,
deferred gates without justification, and regressions outside the phase scope.""",
    "other": """General document/code review. Apply the standard reviewer stance
and tailor findings to the supplied target and context.""",
}


PROMPT_SENTINEL_START = "<!-- superstar-prompt:start -->"
PROMPT_SENTINEL_END = "<!-- superstar-prompt:end -->"


def strip_prompt_echo(text: str) -> str:
    """Remove any superstar-prompt-sentinel-delimited region from `text`.

    Handles three cases beyond the simple full-block case:
    - End marker present but no start marker → delete from start of stream
      through (and including) the end marker. Models a tail-truncated echo
      where the beginning was capped off but the end marker survived.
    - Start marker present but no end marker → delete from the start marker
      to end of stream. Models a head-truncated echo.
    - Multiple full blocks → all removed.
    """
    if not text:
        return text
    out = text
    # Repeatedly strip full blocks first (greedy non-overlapping).
    while True:
        s = out.find(PROMPT_SENTINEL_START)
        e = out.find(PROMPT_SENTINEL_END)
        if s != -1 and e != -1 and e > s:
            out = out[:s] + out[e + len(PROMPT_SENTINEL_END):]
            continue
        break
    # Truncated-end case: end marker without a preceding start marker.
    e = out.find(PROMPT_SENTINEL_END)
    if e != -1 and out.find(PROMPT_SENTINEL_START) == -1:
        out = out[e + len(PROMPT_SENTINEL_END):]
    # Truncated-start case: start marker without a following end marker.
    s = out.find(PROMPT_SENTINEL_START)
    if s != -1 and out.find(PROMPT_SENTINEL_END) == -1:
        out = out[:s]
    return out


def cap_with_elision(text: str, max_bytes: int = 80 * 1024) -> str:
    """Cap `text` to ~max_bytes, keeping head + tail with an elision marker.

    Returns the original text unchanged if under the cap. Otherwise returns
    the first 60% + a marker + the last 40% of `max_bytes`. Bytes count is
    on the encoded UTF-8 length; for purely ASCII content this equals
    character count.
    """
    if not text:
        return text
    raw = text.encode("utf-8")
    if len(raw) <= max_bytes:
        return text
    head_bytes = int(max_bytes * 0.6)
    tail_bytes = max_bytes - head_bytes
    head = raw[:head_bytes].decode("utf-8", errors="ignore")
    tail = raw[-tail_bytes:].decode("utf-8", errors="ignore")
    elided = len(raw) - head_bytes - tail_bytes
    marker = f"\n\n[… {elided} bytes elided to fit cap of {max_bytes} bytes …]\n\n"
    return head + marker + tail


DEFAULT_STATE_FILE = Path.home() / ".config" / "superstar" / "reviewer-state.json"


def state_file_path() -> Path:
    override = os.environ.get("AGENT_REVIEWER_STATE_FILE")
    if override:
        return Path(override)
    return DEFAULT_STATE_FILE


def _state_lock_path() -> Path:
    """Companion lock-file path for the state file. Using a separate companion
    avoids any chicken-and-egg issue when the state file itself is absent."""
    p = state_file_path()
    return p.with_suffix(p.suffix + ".lock")


def _ensure_state_parent_dir() -> None:
    path = state_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass  # best-effort; some filesystems disallow chmod


class _StateLock:
    """Context manager acquiring fcntl.LOCK_EX on the state-file lock companion.
    Both readers and writers acquire this lock so writes serialize across
    processes (spec line 79)."""

    def __init__(self) -> None:
        self._fd: int | None = None

    def __enter__(self) -> "_StateLock":
        _ensure_state_parent_dir()
        lock_path = _state_lock_path()
        # O_RDWR | O_CREAT, mode 0o600 — owner-only lock companion.
        self._fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(self._fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._fd is not None:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
            finally:
                os.close(self._fd)
                self._fd = None


def load_state() -> dict:
    """Read the reviewer state file. Fails open: missing/corrupt → empty state.
    Acquires fcntl.flock(LOCK_EX) on the lock companion so reads see a
    consistent snapshot relative to in-flight writers."""
    path = state_file_path()
    with _StateLock():
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


def save_state(state: dict) -> None:
    """Atomically write the reviewer state file. Uses flock on a lock companion
    + tmp-then-rename. Creates parent dir with mode 0o700 on first write."""
    path = state_file_path()
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(state, indent=2, sort_keys=True)
    with _StateLock():
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)


def _load_state_locked() -> dict:
    """Internal: read state assuming the caller already holds _StateLock."""
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


def _save_state_locked(state: dict) -> None:
    """Internal: write state assuming the caller already holds _StateLock."""
    path = state_file_path()
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(state, indent=2, sort_keys=True)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)


def update_state(mutator) -> dict:
    """Atomic read-modify-write under the state lock. `mutator(state)` may
    mutate the dict in place or return a new dict. Returns the final state.
    This is the recommended path for any caller that does a read followed by
    a dependent write, since plain load_state + save_state pairs are not
    atomic across processes."""
    with _StateLock():
        state = _load_state_locked()
        result = mutator(state)
        if result is not None and isinstance(result, dict):
            state = result
        _save_state_locked(state)
        return state


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


@dataclass
class ProviderResolution:
    provider: str
    caller_provider: str
    command: str


class ProviderResolutionError(Exception):
    pass


def _provider_from_process_tokens(tokens: list[str]) -> str | None:
    provider_names = {
        "claude": {"claude", "claude.exe", "claude-code", "claude-code.exe"},
        "codex": {"codex", "codex.exe", "codex.js"},
    }
    provider_prefixes = {
        "claude": ("claude-",),
        "codex": ("codex-",),
    }
    package_markers = {
        "claude": ("/@anthropic-ai/claude-code", "/anthropic-ai/claude-code"),
        "codex": ("/@openai/codex", "/openai/codex"),
    }

    hits: set[str] = set()
    for token in tokens:
        normalized = token.lower().replace("\\", "/")
        basename = Path(normalized).name
        for provider, names in provider_names.items():
            if basename in names or any(basename.startswith(prefix) for prefix in provider_prefixes[provider]):
                hits.add(provider)
            if any(marker in normalized for marker in package_markers[provider]):
                hits.add(provider)
    if len(hits) == 1:
        return next(iter(hits))
    return None


def _process_tokens_for_pid(pid: int) -> list[str]:
    proc = Path("/proc") / str(pid)
    try:
        raw = (proc / "cmdline").read_bytes()
    except OSError:
        raw = b""
    tokens = [part.decode("utf-8", errors="replace") for part in raw.split(b"\0") if part]
    if tokens:
        return tokens
    try:
        comm = (proc / "comm").read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        comm = ""
    return [comm] if comm else []


def _parent_pid_for_pid(pid: int) -> int | None:
    try:
        for line in (Path("/proc") / str(pid) / "status").read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("PPid:"):
                return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return None


def _detect_caller_provider_from_process_tree(*, start_pid: int | None = None, max_depth: int = 12) -> str:
    pid = start_pid if start_pid is not None else os.getppid()
    seen: set[int] = set()
    hits: set[str] = set()
    depth = 0
    while pid and pid > 1 and pid not in seen and depth < max_depth:
        seen.add(pid)
        hint = _provider_from_process_tokens(_process_tokens_for_pid(pid))
        if hint:
            hits.add(hint)
            if len(hits) > 1:
                return "unknown"
        parent = _parent_pid_for_pid(pid)
        if parent is None or parent == pid:
            break
        pid = parent
        depth += 1
    if len(hits) == 1:
        return next(iter(hits))
    return "unknown"


def detect_caller_provider(env: dict | None = None) -> str:
    env = env if env is not None else os.environ
    explicit = env.get("AGENT_REVIEWER_CALLER")
    if explicit in {"claude", "codex", "unknown"}:
        return explicit
    if env.get("CLAUDECODE") or env.get("CLAUDE_CODE"):
        return "claude"
    if env.get("CODEX_HOME") or env.get("OPENAI_CODEX"):
        return "codex"
    return _detect_caller_provider_from_process_tree()


def resolve_reviewer_provider(
    *,
    reviewer_provider: str,
    caller_provider: str,
    reviewer_cmd: str | None,
    env: dict | None = None,
) -> ProviderResolution:
    env = env if env is not None else os.environ
    provider = reviewer_provider or env.get("AGENT_REVIEWER_PROVIDER", "auto")
    caller = caller_provider or detect_caller_provider(env)
    if caller == "auto":
        caller = detect_caller_provider(env)

    explicit_cmd = reviewer_cmd or env.get("AGENT_REVIEWER_CMD")
    if explicit_cmd:
        return ProviderResolution(provider="custom", caller_provider=caller, command=explicit_cmd)

    if provider == "auto":
        if caller == "claude":
            provider = "codex"
        elif caller == "codex":
            provider = "claude"
        else:
            raise ProviderResolutionError(
                "Cannot auto-select reviewer: caller provider is unknown. "
                "Set AGENT_REVIEWER_PROVIDER or AGENT_REVIEWER_CMD."
            )

    if provider not in {"codex", "claude", "custom"}:
        raise ProviderResolutionError(f"Unknown reviewer provider: {provider}")
    if provider == "custom":
        raise ProviderResolutionError("provider=custom requires AGENT_REVIEWER_CMD or --reviewer-cmd")
    return ProviderResolution(provider=provider, caller_provider=caller, command="reviewer-agent")


def reviewer_cmd_basename() -> str:
    """Return the state-key for the configured reviewer command. Honours
    AGENT_REVIEWER_STATE_KEY override; else uses the first whitespace token of
    AGENT_REVIEWER_CMD; else the default 'reviewer-agent'."""
    override = os.environ.get("AGENT_REVIEWER_STATE_KEY")
    if override:
        return override.strip()
    cmd = os.environ.get("AGENT_REVIEWER_CMD", "reviewer-agent")
    return cmd.strip().split()[0] if cmd.strip() else "reviewer-agent"


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


_TIME_RE_AMPM = re.compile(r"^(\d{1,2}):(\d{2})\s*([AaPp][Mm])$")
_TIME_RE_24H = re.compile(r"^(\d{1,2}):(\d{2})$")


def _now_local() -> "dt.datetime":
    """Override hook for tests."""
    return dt.datetime.now()


def _fallback_reset_time() -> "dt.datetime":
    hours = int(os.environ.get("AGENT_REVIEWER_LIMIT_FALLBACK_HOURS", "4"))
    return (_now_local() + dt.timedelta(hours=hours)).replace(second=0, microsecond=0)


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


_BUDGET_SECTIONS = [
    ("target_preview", r"\n## Target Preview\n", [80 * 80, 40 * 80, 0]),
    ("diff_body", r"\n## Changes since prior round\n", [50 * 1024, 12 * 1024, 0]),
    ("resolution_body", r"\n## Resolution report for prior round\n", [20 * 1024, 8 * 1024, 2 * 1024]),
    ("prior_findings_body", r"\n## Prior-round findings\n", [40 * 1024, 16 * 1024, 8 * 1024]),
]


def _find_section_end(text: str, section_start: int) -> int:
    """Return the offset where a section ends: the start of the next known
    budget-section anchor, the sentinel end marker, or end-of-text —
    whichever comes first.

    Uses only the four known ``_BUDGET_SECTIONS`` patterns as boundaries
    (not any ``\\n## `` heading) so that nested sub-headings inside a
    section (e.g. ``### git diff base..HEAD`` inside "Changes since prior
    round") do not prematurely terminate the section.
    """
    import re
    candidates = []
    for _, pattern, _ in _BUDGET_SECTIONS:
        m = re.search(pattern, text[section_start:])
        if m:
            candidates.append(section_start + m.start())
    e = text.find(PROMPT_SENTINEL_END, section_start)
    if e != -1:
        candidates.append(e)
    if not candidates:
        return len(text)
    return min(candidates)


def apply_budget(text: str, budget_chars: int) -> str:
    """Trim prunable sections in priority order until `text` fits the budget.

    Preserved (never trimmed):
      - Sentinel markers
      - Chain summary table (`## Review chain summary`)
      - Review-mode preamble + REVIEW_PROMPT contract

    Pruning order (lowest priority dropped first):
      1. Target Preview        → 80 → 40 → 0 lines
      2. Diff body             → 50 KB → 12 KB → 0
      3. Resolution body       → 20 KB → 8 KB → 2 KB
      4. Prior findings body   → 40 KB → 16 KB → 8 KB

    Appends a `<!-- budget-applied: ... -->` HTML comment immediately before
    the end sentinel summarising trims.

    Note: the final string may exceed `budget_chars` by up to ~200 bytes — the
    trim loop fits content to the budget, then appends a diagnostic note.
    """
    import re
    if len(text) <= budget_chars:
        return text

    out = text
    trim_log: list[str] = []
    for name, pattern, levels in _BUDGET_SECTIONS:
        if len(out) <= budget_chars:
            break
        m = re.search(pattern, out)
        if not m:
            continue
        section_start = m.end()
        for level_bytes in levels:
            if len(out) <= budget_chars:
                break
            section_end = _find_section_end(out, section_start)
            section_body = out[section_start:section_end]
            if level_bytes == 0:
                replacement = f"\n[{name} dropped to fit budget]\n"
            else:
                replacement = "\n" + cap_with_elision(section_body, max_bytes=level_bytes) + "\n"
            if len(replacement) >= len(section_body):
                continue
            out = out[:section_start] + replacement + out[section_end:]
            trim_log.append(f"{name}:{level_bytes}")

    note = (
        f"\n<!-- budget-applied: budget={budget_chars} "
        f"trims=[{','.join(trim_log)}] final_size={len(out)} -->\n"
    )
    end_idx = out.rfind(PROMPT_SENTINEL_END)
    if end_idx != -1:
        out = out[:end_idx] + note + out[end_idx:]
    else:
        out = out + note
    return out


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


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def migrate_manifest_inplace(manifest: dict) -> None:
    """Add `status` and `returncode` keys to legacy round/reviewer entries.

    Legacy entries (pre-S1) lack these keys. We do not invent retroactive
    truth from `verdict_valid`: every legacy entry becomes `status: "unknown"`,
    `returncode: None`. Callers (preamble construction, resolution gate)
    treat `"unknown"` as untrusted-by-default per spec §S1.6.
    """
    if not isinstance(manifest, dict):
        return
    for r in manifest.get("rounds", []) or []:
        if "status" not in r:
            r["status"] = "unknown"
        if "returncode" not in r:
            r["returncode"] = None
        for rev in r.get("reviewers", []) or []:
            if "status" not in rev:
                rev["status"] = "unknown"
            if "returncode" not in rev:
                rev["returncode"] = None


def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=True,
    )
    return Path(result.stdout.strip())


def rel_or_abs(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path.resolve())


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "document"


DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")


def chain_folder_name(target: Path, kind: str, work_id: str | None = None) -> str:
    stem = DATE_PREFIX_RE.sub("", target.stem)
    base = slugify(stem)
    if kind in ("post-slice", "post-phase") and work_id:
        work_id_slug = work_id.replace(".", "-")
        return f"{base}-{work_id_slug}-{kind}"
    return f"{base}-{kind}"


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
            # Only treat as legacy candidate if there is no chain.json — a chain.json
            # marks a new-regime chain (potentially for a different work-id) and must
            # never be silently reused.
            if not (entry / "chain.json").exists():
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


def next_round_number(chain_dir: Path) -> int:
    if not chain_dir.exists():
        return 1
    manifest = read_manifest(chain_dir / "chain.json")
    if manifest and isinstance(manifest.get("rounds"), list):
        return len(manifest["rounds"]) + 1
    return len(list(chain_dir.glob("r*-*-request.md"))) + 1


def numbered_preview(path: Path, root: Path, max_lines: int) -> str:
    rel = rel_or_abs(path, root)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return f"### {rel}\n\n(binary or non-UTF-8 file omitted)\n"

    rendered = [f"### {rel}", ""]
    for idx, line in enumerate(lines[:max_lines], start=1):
        rendered.append(f"{idx:>5}\t{line}")
    if len(lines) > max_lines:
        rendered.append(f"\n[truncated: {len(lines) - max_lines} additional lines]")
    rendered.append("")
    return "\n".join(rendered)


def default_diff_paths(
    kind: str, target: Path, context: list, root: Path
) -> list | None:
    """Default scope for embedded diffs.

    Broad (all tracked changes) for post-slice/post-phase; for everything
    else, restrict to the target document plus any context files.
    """
    if kind in ("post-slice", "post-phase"):
        return None
    paths = [rel_or_abs(target, root)]
    for c in context:
        paths.append(rel_or_abs(c, root))
    return paths


def build_incremental_preamble(
    *,
    manifest: dict,
    chain_dir: Path,
    round_num: int,
    resolution_waiver: bool,
    legacy_first_round: bool,
    diff_section: str = "",
) -> str:
    chain = manifest.get("chain", "<unknown chain>")
    prior_rounds = manifest.get("rounds", [])
    summary_rows = ["| round | verdict | findings | blocking |", "|---|---|---|---|"]
    for r in prior_rounds:
        summary_rows.append(
            f"| {r['round']} | {r.get('merged_verdict') or r.get('verdict')} "
            f"| {r.get('findings_count')} | {r.get('blocking_findings_count')} |"
        )

    # Walk backward to the last round whose process status is "ok".
    # Skip rounds with status in BACKWARD_SKIP_STATUSES — "failed" (process error,
    # body is stderr-echo), "unknown" (legacy entries, untrusted by default),
    # or "rate-limited" (no reviewer output produced; not a real round).
    BACKWARD_SKIP_STATUSES = {"failed", "unknown", "rate-limited"}
    skipped_rounds: list[int] = []
    trusted = None
    for r in reversed(prior_rounds):
        if r.get("status") == "ok":
            trusted = r
            break
        if r.get("status") in BACKWARD_SKIP_STATUSES:
            skipped_rounds.append(r["round"])
            continue
        skipped_rounds.append(r["round"])
    skipped_rounds.reverse()

    prior_response_text = ""
    if trusted is not None:
        merged_findings_file = chain_dir / f"r{trusted['round']}-merged-findings.md"
        if merged_findings_file.exists():
            prior_response_text = cap_with_elision(
                merged_findings_file.read_text(encoding="utf-8")
            )
            prior_source = f"merged findings from r{trusted['round']} (authoritative)"
        elif trusted.get("response"):
            response_path = chain_dir / trusted["response"]
            if response_path.exists():
                prior_response_text = cap_with_elision(
                    response_path.read_text(encoding="utf-8")
                )
                prior_source = f"primary reviewer response from r{trusted['round']}"
            else:
                prior_source = f"r{trusted['round']} response file missing"
        else:
            prior_source = f"r{trusted['round']} has no response on record"
    else:
        prior_source = "no successful prior round; no prior review available"

    if skipped_rounds:
        skip_lo = skipped_rounds[0]
        skip_hi = skipped_rounds[-1]
        if skip_lo == skip_hi:
            skip_note = (
                f"\nNote: round {skip_lo} was a process failure, rate-limited, "
                f"or pre-S1 entry; skipped.\n"
            )
        else:
            skip_note = (
                f"\nNote: rounds {skip_lo}..{skip_hi} were process failures, "
                f"rate-limited, or pre-S1 entries; skipped.\n"
            )
        prior_response_text = skip_note + prior_response_text

    resolution_file = chain_dir / f"r{round_num - 1}-resolution.md"
    if resolution_file.exists():
        resolution_text = cap_with_elision(
            resolution_file.read_text(encoding="utf-8"),
            max_bytes=20 * 1024,  # tighter cap for resolution docs
        )
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

## Review chain summary

{chr(10).join(summary_rows)}

## Prior-round findings

Source: {prior_source}

{prior_response_text}

## Resolution report for prior round

{resolution_text}

## Changes since prior round

{diff_section or 'Changes since prior round: not available for this round.'}
"""


def make_prompt(
    *,
    root: Path,
    target: Path,
    kind: str,
    context: list[Path],
    max_lines: int,
    mode: str = "broad",
    incremental_preamble: str | None = None,
    incremental_budget_chars: int | None = None,
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
    effective_target_max = min(max_lines, 150) if mode == "incremental" else max_lines
    body += "\n\n## Target Preview\n\n"
    body += numbered_preview(target, root, max_lines=effective_target_max)
    if context and mode != "incremental":
        body += "\n## Context Previews\n\n"
        for ctx in context:
            body += numbered_preview(ctx, root, max_lines=max(80, max_lines // 3))
    assembled = f"{PROMPT_SENTINEL_START}\n{body}\n{PROMPT_SENTINEL_END}"
    if mode == "incremental" and incremental_budget_chars is not None:
        return apply_budget(assembled, budget_chars=incremental_budget_chars)
    return assembled


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
    repo_root: Path | None = None,
    response_dir: Path | None = None,
    scratch_dir: Path | None = None,
    request_file: Path | None = None,
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
        "repo_root": shlex.quote(str(repo_root)) if repo_root else "",
        "response_dir": shlex.quote(str(response_dir)) if response_dir else "",
        "scratch_dir": shlex.quote(str(scratch_dir)) if scratch_dir else "",
        "request_file": shlex.quote(str(request_file)) if request_file else "",
    }
    return template.format(**values)


def run_reviewer(
    *,
    command_template: str,
    prompt_file: Path,
    prompt_text: str,
    target_file: Path,
    kind: str,
    prompt_transport: str,
    timeout: int,
    chain_dir: Path,
    round_num: int,
    previous_response: Path | None,
    resolution_file: Path | None,
    session_file: Path,
    repo_root: Path | None = None,
    response_dir: Path | None = None,
    scratch_dir: Path | None = None,
    request_file: Path | None = None,
    extra_env: dict | None = None,
) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if extra_env:
        run_env.update(extra_env)
    if "{" in command_template and "}" in command_template:
        command = expand_command_template(
            command_template,
            prompt_file=prompt_file,
            prompt_text=prompt_text,
            target_file=target_file,
            kind=kind,
            chain_dir=chain_dir,
            round_num=round_num,
            previous_response=previous_response,
            resolution_file=resolution_file,
            session_file=session_file,
            repo_root=repo_root,
            response_dir=response_dir,
            scratch_dir=scratch_dir,
            request_file=request_file,
        )
        return subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout,
            env=run_env,
        )

    argv = shlex.split(command_template)
    stdin_text = None
    if prompt_transport == "arg":
        argv.append(prompt_text)
    elif prompt_transport == "file":
        argv.append(str(prompt_file))
    elif prompt_transport == "stdin":
        stdin_text = prompt_text
    else:
        raise ValueError(f"unknown prompt transport: {prompt_transport}")

    return subprocess.run(
        argv,
        input=stdin_text,
        text=True,
        capture_output=True,
        timeout=timeout,
        env=run_env,
    )


def write_review_artifact(
    *,
    root: Path,
    target: Path,
    kind: str,
    command_template: str,
    prompt_file: Path,
    response_file: Path,
    round_num: int,
    result: subprocess.CompletedProcess[str],
    provider: str = "custom",
    sandbox_summary: str = "custom command; bridge-provided scratch/output context",
) -> Path:
    # Sentinel-strip both streams in full BEFORE any size cap or tail operation.
    stdout = strip_prompt_echo(result.stdout or "").strip()
    stderr = strip_prompt_echo(result.stderr or "").strip()
    ok = result.returncode == 0
    status = "ok" if ok else f"failed ({result.returncode})"

    content = [
        f"# Review — {target.name} ({kind}, round {round_num})",
        "",
        f"- Target: `{rel_or_abs(target, root)}`",
        f"- Request: `{rel_or_abs(prompt_file, root)}`",
        f"- Reviewer command: `{command_template}`",
        f"- Reviewer provider: `{provider}`",
        f"- Sandbox: {sandbox_summary}",
        f"- Status: `{status}`",
        "",
        "---",
        "",
    ]

    if ok:
        content.append(stdout or "_Reviewer produced no stdout._")
        content.append("")
        if stderr:
            # Capped tail of sanitised stderr — diagnostic only.
            tail = stderr[-2048:]
            content.extend([
                "---", "", "## Reviewer stderr (tail)", "",
                "```text", tail, "```", "",
            ])
    else:
        # Failed: no stdout body, only a short sanitised stderr tail.
        tail = stderr[-4096:] if stderr else ""
        content.extend([
            "_Reviewer process failed; no stdout persisted._",
            "",
            "---", "", "## Reviewer stderr (tail, sanitised)", "",
            "```text", tail or "(no stderr captured)", "```", "",
        ])

    response_file.write_text("\n".join(content), encoding="utf-8")
    return response_file


def write_rate_limited_artifact(
    *,
    chain_dir: Path,
    round_num: int,
    timestamp: str,
    reviewer_cmd: str,
    reset_at: str,
    raw_stderr_tail: str,
) -> Path:
    """Persist a rate-limited round response artifact (<= 8 KB)."""
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


EXIT_CODE_RATE_LIMITED = 8


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
        "raw_stderr_tail": raw_stderr_tail[-2048:],
    }


def estimate_usage(prompt_text: str, response_text: str) -> dict:
    prompt_chars = len(prompt_text or "")
    response_chars = len(response_text or "")
    input_tokens = math.ceil(prompt_chars / 4)
    output_tokens = math.ceil(response_chars / 4)
    return {
        "formula": "ceil(chars / 4)",
        "prompt_chars": prompt_chars,
        "response_chars": response_chars,
        "estimated_input_tokens": input_tokens,
        "estimated_output_tokens": output_tokens,
        "estimated_total_tokens": input_tokens + output_tokens,
    }


def _normalize_exact_usage(raw: dict | None, *, provider: str, model: str | None = None) -> dict | None:
    if not isinstance(raw, dict):
        return None
    usage = dict(raw)
    if "total_tokens" not in usage:
        total = 0
        for key in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
            value = usage.get(key)
            if isinstance(value, (int, float)):
                total += int(value)
        if total:
            usage["total_tokens"] = total
    if "total_tokens" not in usage:
        return None
    usage.setdefault("provider", provider)
    if model:
        usage.setdefault("model", model)
    return usage


def _extract_claude_exact_usage(payload: dict, *, provider: str) -> tuple[dict | None, str | None]:
    model = payload.get("model") if isinstance(payload.get("model"), str) else None
    usage = payload.get("usage")
    if isinstance(usage, dict):
        return _normalize_exact_usage(usage, provider=provider, model=model), model
    return None, model


def _extract_codex_exact_usage(events_path: Path, *, provider: str) -> dict | None:
    if not events_path.exists():
        return None
    latest: dict | None = None
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        payload = event.get("token_count") if isinstance(event, dict) else None
        if payload is None and isinstance(event, dict) and event.get("type") == "token_count":
            payload = event
        if isinstance(payload, dict):
            latest = payload
    if latest is None:
        return None
    key_map = {
        "input": "input_tokens",
        "output": "output_tokens",
        "total": "total_tokens",
        "input_tokens": "input_tokens",
        "output_tokens": "output_tokens",
        "total_tokens": "total_tokens",
    }
    usage = {}
    for source, dest in key_map.items():
        if isinstance(latest.get(source), (int, float)):
            usage[dest] = int(latest[source])
    return _normalize_exact_usage(usage, provider=provider, model=latest.get("model"))


def load_usage_sidecar(response_dir: Path, *, provider: str) -> tuple[dict | None, str | None, str | None]:
    """Return (exact_usage, model, error) from optional wrapper sidecars."""
    metadata_path = response_dir / "reviewer-metadata.json"
    if not metadata_path.exists():
        return None, None, None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        sidecar_provider = metadata.get("provider") or provider
        model = metadata.get("model") if isinstance(metadata.get("model"), str) else None
        exact = _normalize_exact_usage(metadata.get("exact_usage"), provider=sidecar_provider, model=model)
        if exact:
            return exact, exact.get("model") or model, None
        if metadata.get("claude_output_file"):
            payload = json.loads((response_dir / metadata["claude_output_file"]).read_text(encoding="utf-8"))
            exact, claude_model = _extract_claude_exact_usage(payload, provider=sidecar_provider)
            return exact, claude_model or model, None
        if metadata.get("codex_events_file"):
            exact = _extract_codex_exact_usage(response_dir / metadata["codex_events_file"], provider=sidecar_provider)
            return exact, (exact or {}).get("model") or model, None
        return None, model, None
    except Exception as exc:
        return None, None, str(exc)


def build_usage_capture(
    *,
    prompt_text: str,
    response_text: str,
    response_dir: Path,
    provider: str,
) -> dict:
    estimated = estimate_usage(prompt_text, response_text)
    exact, model, error = load_usage_sidecar(response_dir, provider=provider)
    if error:
        status = "failed"
    elif exact:
        status = "exact"
    elif estimated:
        status = "estimated_only"
    else:
        status = "unavailable"
    return {
        "usage_capture_status": status,
        "estimated_usage": estimated,
        "exact_usage": exact,
        "model": model,
        "usage_capture_error": error,
    }


def resolve_mode(mode: str, *, round_num: int) -> str:
    if mode == "incremental" and round_num == 1:
        raise ValueError("--mode incremental is not valid on round 1")
    if mode == "auto":
        return "broad" if round_num == 1 else "incremental"
    return mode


@dataclass
class SweepPlan:
    sweep_count: int
    checkpoint: str | None  # "first-round" | "final-ready" | None


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
    status: str | None = None   # "ok" | "failed" | "rate-limited"; None → derive from returncode
    provider: str = "custom"
    caller_provider: str = "unknown"
    sandbox: dict | None = None
    started_at: str | None = None
    finished_at: str | None = None
    duration_ms: int | None = None
    model: str | None = None
    estimated_usage: dict | None = None
    exact_usage: dict | None = None
    usage_capture_status: str = "unavailable"
    usage_capture_error: str | None = None


@dataclass
class ReviewerInvocationContext:
    repo_root: Path
    chain_dir: Path
    request_file: Path
    response_dir: Path
    scratch_dir: Path
    target_file: Path
    kind: str
    role: str
    sweep_index: int | None
    provider: str
    caller_provider: str

    def env(self) -> dict:
        return {
            "AGENT_REVIEWER_REPO_ROOT": str(self.repo_root),
            "AGENT_REVIEWER_CHAIN_DIR": str(self.chain_dir),
            "AGENT_REVIEWER_REQUEST_FILE": str(self.request_file),
            "AGENT_REVIEWER_RESPONSE_DIR": str(self.response_dir),
            "AGENT_REVIEWER_SCRATCH_DIR": str(self.scratch_dir),
            "AGENT_REVIEWER_TARGET_FILE": str(self.target_file),
            "AGENT_REVIEWER_KIND": self.kind,
            "AGENT_REVIEWER_ROLE": self.role,
            "AGENT_REVIEWER_SWEEP_INDEX": "" if self.sweep_index is None else str(self.sweep_index),
            "AGENT_REVIEWER_PROVIDER": self.provider,
            "AGENT_REVIEWER_CALLER": self.caller_provider,
        }


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
    root: Path,
    namespaced: bool,
    previous_response: Path | None = None,
    resolution_file: Path | None = None,
) -> ReviewerResult:
    suffix = ""
    if namespaced:
        suffix = "-primary" if role == "primary" else f"-sweep{sweep_index}"
    basename = f"r{round_num}-{timestamp}{suffix}"
    request_path = chain_dir / f"{basename}-request.md"
    response_path = chain_dir / f"{basename}-response.md"
    request_path.write_text(prompt_text, encoding="utf-8")
    session_file = chain_dir / (
        "session.state" if role == "primary" else f"sweep{sweep_index}.session.state"
    )

    # Pre-spawn rate-limit check
    key = reviewer_cmd_basename()
    active = get_active_limit(key)
    if active is not None:
        _manifest_path = chain_dir / "chain.json"
        _manifest = read_manifest(_manifest_path)
        if _manifest is None:
            # Defensive: post-T2.0 eager-write should make this unreachable.
            _manifest = {"rounds": []}
        now_iso = _now_local().isoformat(timespec="seconds")
        rounds = _manifest.get("rounds", [])
        head = rounds[-1] if rounds else None
        if head is not None and head.get("status") == "rate-limited":
            # Coalesce onto the head rate-limited round.
            refused_at = list(head.get("refused_at", []))
            refused_at.append(now_iso)
            refused_at = refused_at[-20:]
            head["refused_at"] = refused_at
            head["last_refused_at"] = now_iso
            write_manifest(_manifest_path, _manifest)
            # Best-effort: remove the speculative request artifact we just wrote
            # so the chain dir doesn't accumulate junk per refusal.
            try:
                if request_path.exists():
                    request_path.unlink()
            except OSError:
                pass
            head_request_path = chain_dir / head.get("request", f"r{head['round']}-coalesced-request.md")
            if role == "sweep":
                # Sweep pre-spawn refusal: return rate-limited result without
                # raising; primary may still succeed and the round proceed.
                return ReviewerResult(
                    role=role, sweep_index=sweep_index,
                    request_path=request_path, response_path=head_request_path,
                    review_body="", verdict=None, verdict_valid=False,
                    returncode=0, status="rate-limited",
                )
            raise ReviewerRateLimited(
                reviewer_cmd=key, reset_at=active["reset_at"],
                reset_source=active.get("reset_source", "unknown"),
                chain=chain_dir.name, round_num=head["round"],
                request_path=str(head_request_path),
                raw_stderr_tail=active.get("raw_stderr_tail", ""),
            )
        # First refusal in this chain → write a rate-limited round artifact.
        artifact_path = write_rate_limited_artifact(
            chain_dir=chain_dir, round_num=round_num, timestamp=timestamp,
            reviewer_cmd=key, reset_at=active["reset_at"],
            raw_stderr_tail=active.get("raw_stderr_tail", ""),
        )
        if role == "sweep":
            # Sweep pre-spawn refusal (first in chain): persist artifact but no
            # chain.json round entry — caller records per-reviewer status.
            return ReviewerResult(
                role=role, sweep_index=sweep_index,
                request_path=request_path, response_path=artifact_path,
                review_body="", verdict=None, verdict_valid=False,
                returncode=0, status="rate-limited",
            )
        new_round = {
            "round": round_num,
            "status": "rate-limited",
            "returncode": None,
            "verdict": None,
            "verdict_valid": False,
            "merged_verdict": None,
            "reset_at": active["reset_at"],
            "reviewer_cmd": key,
            "request": request_path.name,
            "response": artifact_path.name,
            "limited_at": now_iso,
            "refused_at": [now_iso],
            "last_refused_at": now_iso,
        }
        _manifest.setdefault("rounds", []).append(new_round)
        write_manifest(_manifest_path, _manifest)
        raise ReviewerRateLimited(
            reviewer_cmd=key, reset_at=active["reset_at"],
            reset_source=active.get("reset_source", "unknown"),
            chain=chain_dir.name, round_num=round_num,
            request_path=str(request_path),
            raw_stderr_tail=active.get("raw_stderr_tail", ""),
        )

    role_name = "primary" if role == "primary" else f"sweep{sweep_index}"
    response_dir = chain_dir / ".reviewer-output" / f"r{round_num}-{role_name}"
    response_dir.mkdir(parents=True, exist_ok=True)
    scratch_dir = Path(tempfile.mkdtemp(
        prefix=f"superstar-reviewer-{chain_dir.name}-r{round_num}-{role_name}-"
    ))
    scratch_dir.chmod(0o700)
    provider_resolution = getattr(
        args, "provider_resolution",
        ProviderResolution("custom", "unknown", getattr(args, "reviewer_cmd", "reviewer-agent")),
    )
    invocation_context = ReviewerInvocationContext(
        repo_root=root,
        chain_dir=chain_dir,
        request_file=request_path,
        response_dir=response_dir,
        scratch_dir=scratch_dir,
        target_file=target,
        kind=args.kind,
        role=role,
        sweep_index=sweep_index,
        provider=provider_resolution.provider,
        caller_provider=provider_resolution.caller_provider,
    )
    sandbox_info = {
        "repo_root": str(root),
        "scratch_dir": str(scratch_dir),
        "response_dir": rel_or_abs(response_dir, root),
        "mode": (
            "custom" if invocation_context.provider == "custom"
            else "workspace-write-with-read-access" if invocation_context.provider == "codex"
            else "plan-read-only"
        ),
    }

    try:
        started_at = utc_now_iso()
        started_mono = time.monotonic()
        result = run_reviewer(
            command_template=args.reviewer_cmd,
            prompt_file=request_path, prompt_text=prompt_text,
            target_file=target, kind=args.kind,
            prompt_transport=args.prompt_transport, timeout=args.timeout,
            chain_dir=chain_dir, round_num=round_num,
            previous_response=previous_response, resolution_file=resolution_file,
            session_file=session_file,
            repo_root=root,
            response_dir=response_dir,
            scratch_dir=scratch_dir,
            request_file=request_path,
            extra_env=invocation_context.env(),
        )
        finished_at = utc_now_iso()
        duration_ms = max(0, int((time.monotonic() - started_mono) * 1000))
        # Rate-limit detection — runs only on non-zero exit
        if result.returncode != 0:
            matched, reset_at, pattern_name = detect_rate_limit(result.stderr or "")
            if matched:
                reset_at_iso = (reset_at or _fallback_reset_time()).isoformat(timespec="seconds")
                key = reviewer_cmd_basename()
                entry = {
                    "limited": True,
                    "limited_at": _now_local().isoformat(timespec="seconds"),
                    "reset_at": reset_at_iso,
                    "reset_source": f"regex:{pattern_name}" if pattern_name else "fallback",
                    "raw_stderr_tail": (result.stderr or "")[-2048:],
                    "chain": chain_dir.name,
                    "round": round_num,
                }

                def _record_limit(state, _entry=entry, _key=key):
                    state["limits"][_key] = _entry

                update_state(_record_limit)
                artifact_path = write_rate_limited_artifact(
                    chain_dir=chain_dir, round_num=round_num, timestamp=timestamp,
                    reviewer_cmd=key, reset_at=reset_at_iso,
                    raw_stderr_tail=result.stderr or "",
                )
                if role == "sweep":
                    return ReviewerResult(
                        role=role, sweep_index=sweep_index,
                        request_path=request_path, response_path=artifact_path,
                        review_body="", verdict=None, verdict_valid=False,
                        returncode=result.returncode, status="rate-limited",
                        provider=invocation_context.provider,
                        caller_provider=invocation_context.caller_provider,
                        sandbox=sandbox_info,
                    )
                _manifest_path = chain_dir / "chain.json"
                _manifest = read_manifest(_manifest_path)
                new_round = {
                    "round": round_num,
                    "status": "rate-limited",
                    "returncode": None,
                    "verdict": None,
                    "verdict_valid": False,
                    "merged_verdict": None,
                    "reset_at": reset_at_iso,
                    "reviewer_cmd": key,
                    "request": request_path.name,
                    "response": artifact_path.name,
                    "limited_at": _now_local().isoformat(timespec="seconds"),
                }
                _manifest["rounds"].append(new_round)
                write_manifest(_manifest_path, _manifest)
                raise ReviewerRateLimited(
                    reviewer_cmd=key, reset_at=reset_at_iso,
                    reset_source=f"regex:{pattern_name}" if pattern_name else "fallback",
                    chain=chain_dir.name, round_num=round_num,
                    request_path=str(request_path),
                    raw_stderr_tail=result.stderr or "",
                )
        write_review_artifact(
            root=root, target=target, kind=args.kind,
            command_template=args.reviewer_cmd,
            prompt_file=request_path, response_file=response_path,
            round_num=round_num, result=result,
            provider=invocation_context.provider,
            sandbox_summary=(
                "custom command; bridge-provided scratch/output context"
                if invocation_context.provider == "custom"
                else "repo read-only; scratch/output writable"
            ),
        )
        body = response_path.read_text(encoding="utf-8")
        usage_capture = build_usage_capture(
            prompt_text=prompt_text,
            response_text=body,
            response_dir=response_dir,
            provider=invocation_context.provider,
        )
        if result.returncode != 0:
            verdict, valid = None, False
        else:
            verdict, valid = parse_reformatted_verdict(body)
        return ReviewerResult(
            role=role, sweep_index=sweep_index,
            request_path=request_path, response_path=response_path,
            review_body=body, verdict=verdict, verdict_valid=valid,
            returncode=result.returncode,
            status="ok" if result.returncode == 0 else "failed",
            provider=invocation_context.provider,
            caller_provider=invocation_context.caller_provider,
            sandbox=sandbox_info,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            model=usage_capture["model"],
            estimated_usage=usage_capture["estimated_usage"],
            exact_usage=usage_capture["exact_usage"],
            usage_capture_status=usage_capture["usage_capture_status"],
            usage_capture_error=usage_capture["usage_capture_error"],
        )
    finally:
        if not getattr(args, "keep_reviewer_scratch", False):
            shutil.rmtree(scratch_dir, ignore_errors=True)


def _rv_attr(r, name, default=None):
    """Read an attribute from either a ReviewerResult dataclass or a dict."""
    if isinstance(r, dict):
        return r.get(name, default)
    return getattr(r, name, default)


def _rv_status(r) -> str:
    """Resolve the status of a reviewer entry.

    - Dicts and objects that explicitly set `status` win.
    - Otherwise derive from `returncode`: 0 → "ok", non-zero → "failed",
      None → "failed" (unknown / process never ran cleanly).
    """
    explicit = _rv_attr(r, "status", None)
    if explicit is not None:
        return explicit
    rc = _rv_attr(r, "returncode", None)
    return "ok" if rc == 0 else "failed"


def compute_merged_verdict(reviewer_results: list) -> str | None:
    """Merge per-reviewer verdicts per spec §S1.7.

    - If the primary reviewer's status is not "ok" (failed, rate-limited, etc.),
      return None: the round as a whole has no trustworthy verdict and the
      top-level status will be set accordingly.
    - Otherwise, aggregate only the reviewers whose status == "ok". Rate-limited
      reviewers are excluded from the merge — they neither vote nor poison the
      result. The status filter is more precise than a returncode==0 filter
      because a rate-limited round could in principle exit 0 while still
      lacking a trustworthy verdict.
    - Among the ok reviewers: any `revise` (or invalid verdict text) → revise;
      any `ready with small edits` → that; all `ready` → ready.
    """
    primary = next((r for r in reviewer_results if _rv_attr(r, "role") == "primary"), None)
    if primary is not None and _rv_status(primary) != "ok":
        return None
    ok = [r for r in reviewer_results if _rv_status(r) == "ok"]
    if not ok:
        return None
    if any((not _rv_attr(r, "verdict_valid")) or _rv_attr(r, "verdict") == "revise" for r in ok):
        return "revise"
    if any(_rv_attr(r, "verdict") == "ready with small edits" for r in ok):
        return "ready with small edits"
    if all(_rv_attr(r, "verdict") == "ready" for r in ok):
        return "ready"
    return None


def _renamespace_finding_ids(body: str, sweep_index: int) -> str:
    """Rewrite bare F<n> identifiers to S{k}.F<n>, leaving already-prefixed IDs alone."""
    return re.sub(r"(?<![.\w])F(\d+)\b", rf"S{sweep_index}.F\1", body)


def write_merged_findings(
    *,
    chain_dir: Path, round_num: int,
    primary: "ReviewerResult", sweeps: list,
) -> Path | None:
    """Concatenate successful reviewer bodies into a merged-findings artifact.

    Reviewers whose status is not "ok" (failed, rate-limited, etc.) are
    excluded entirely — their bodies are stderr tails / failure stubs / empty
    placeholders and would poison downstream parsing. If every reviewer in
    the round is non-ok, return None and write no file.
    """
    ok_reviewers = [r for r in [primary, *sweeps] if _rv_status(r) == "ok"]
    if not ok_reviewers:
        return None
    parts = [f"# Merged findings for r{round_num}\n"]
    primary_ok = next((r for r in ok_reviewers if _rv_attr(r, "role") == "primary"), None)
    if primary_ok is not None:
        parts += ["## Primary\n", _rv_attr(primary_ok, "review_body", ""), ""]
    for s in ok_reviewers:
        if _rv_attr(s, "role") == "sweep":
            sweep_index = _rv_attr(s, "sweep_index")
            parts += [
                f"## Sweep {sweep_index}\n",
                _renamespace_finding_ids(_rv_attr(s, "review_body", ""), sweep_index),
                "",
            ]
    path = chain_dir / f"r{round_num}-merged-findings.md"
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


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
    checkpoints: dict,
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a document to the configured reviewer.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sp_review = subparsers.add_parser(
        "review",
        help="Send a document to the configured reviewer.",
        description="Send a document to the configured reviewer.",
    )
    sp_review.add_argument("--file", required=True, help="Target spec/plan/document to review.")
    sp_review.add_argument(
        "--kind",
        required=True,
        choices=["spec", "plan", "design", "implementation", "post-slice", "post-phase", "other"],
        help="Review type, used in prompt and artifact name.",
    )
    sp_review.add_argument(
        "--context",
        action="append",
        default=[],
        help="Additional context file. May be supplied multiple times.",
    )
    sp_review.add_argument(
        "--reviewer-cmd",
        default=os.environ.get("AGENT_REVIEWER_CMD"),
        help="Custom command or template. When set, provider auto-selection is bypassed. Supports {prompt_file}, {prompt_text}, {target_file}, {kind}, {chain_dir}, {round}, {previous_response}, {resolution_file}, {session_file}, {repo_root}, {response_dir}, {scratch_dir}, {request_file}.",
    )
    sp_review.add_argument(
        "--reviewer-provider",
        choices=["auto", "codex", "claude", "custom"],
        default=os.environ.get("AGENT_REVIEWER_PROVIDER", "auto"),
        help="Reviewer provider to use. Default auto flips based on caller provider.",
    )
    sp_review.add_argument(
        "--caller-provider",
        choices=["auto", "claude", "codex", "unknown"],
        default=os.environ.get("AGENT_REVIEWER_CALLER", "auto"),
        help="Coordinator provider. Default auto detects known harness env vars.",
    )
    sp_review.add_argument(
        "--prompt-transport",
        choices=["arg", "file", "stdin"],
        default=os.environ.get("AGENT_REVIEWER_TRANSPORT"),
        help="How to pass the prompt when reviewer-cmd has no placeholders. "
             "If unset, defaults to 'stdin'. Use 'arg' or 'file' only for "
             "custom reviewer backends that require those transports.",
    )
    sp_review.add_argument(
        "--output-dir",
        default="docs/reviewer",
        help="Root directory for review chain folders.",
    )
    sp_review.add_argument(
        "--work-id",
        default=None,
        help="Stable slice/phase ID (e.g. P2.S3 or P2). Required for post-slice/post-phase.",
    )
    sp_review.add_argument(
        "--allow-missing-resolution",
        action="store_true",
        help="Waive the resolution-required gate for post-slice/post-phase round 2+.",
    )
    sp_review.add_argument(
        "--mode",
        choices=["auto", "broad", "incremental"],
        default="auto",
        help="Override the round-1-vs-N prompt mode. Default 'auto'.",
    )
    sp_review.add_argument("--review-depth", choices=["standard", "thorough", "exhaustive"],
                        default="standard")
    sp_review.add_argument("--independent-reviewers", type=int, default=None)
    sp_review.add_argument("--sweep-policy",
                        choices=["first-round", "final-ready", "both", "never"], default=None)
    sp_review.add_argument("--timeout", type=int, default=900)
    sp_review.add_argument("--max-lines", type=int, default=600)
    sp_review.add_argument(
        "--base-ref",
        default=None,
        help="Override auto-computed diff base for this round.",
    )
    sp_review.add_argument(
        "--no-diff",
        action="store_true",
        help="Suppress diff embedding in incremental rounds.",
    )
    sp_review.add_argument(
        "--changed-files",
        nargs="+",
        default=None,
        help="Limit embedded diff to these paths (overrides auto discovery).",
    )
    sp_review.add_argument(
        "--max-diff-lines",
        type=int,
        default=2000,
        help="Cap diff size. Truncation marker is embedded if exceeded.",
    )
    sp_review.add_argument(
        "--emit",
        choices=["paths", "review", "json"],
        default="paths",
        help="What to print to stdout after the reviewer finishes.",
    )
    sp_review.add_argument(
        "--incremental-budget-chars",
        type=int, default=400_000,
        help="Target cap on assembled prompt size for incremental rounds. "
             "Trims low-priority sections first; the final size is the trimmed "
             "budget plus a small diagnostic note (`<!-- budget-applied: ... -->`, "
             "~150 bytes). Default 400000.",
    )
    sp_review.add_argument(
        "--state-file",
        default=None,
        help="Override path to the reviewer state file (rate-limit tracking, etc.).",
    )
    sp_review.add_argument(
        "--keep-reviewer-scratch",
        action="store_true",
        help="Preserve the reviewer scratch directory for debugging.",
    )

    sp_manual = subparsers.add_parser("manual-approve", help="Mark a chain as manually approved")
    sp_manual.add_argument("--kind", required=True)
    sp_manual.add_argument("--file", required=True)
    sp_manual.add_argument("--work-id", required=False, default=None)
    sp_manual.add_argument("--note", required=True)
    sp_manual.add_argument("--state-file", default=None)

    sp_ingest = subparsers.add_parser("ingest-response", help="Ingest an externally-obtained reviewer response")
    sp_ingest.add_argument("--kind", required=True)
    sp_ingest.add_argument("--file", required=True)
    sp_ingest.add_argument("--work-id", required=False, default=None)
    src_group = sp_ingest.add_mutually_exclusive_group(required=True)
    src_group.add_argument("--from-paste", dest="from_paste", default=None)
    src_group.add_argument("--from-link", dest="from_link", default=None)
    sp_ingest.add_argument("--state-file", default=None)

    sp_show = subparsers.add_parser("show-limit", help="Print active reviewer limits")
    sp_show.add_argument("--state-file", default=None)
    sp_clear = subparsers.add_parser("clear-limit", help="Clear reviewer limit state")
    sp_clear.add_argument("--reviewer-cmd", default=None)
    sp_clear.add_argument("--state-file", default=None)
    sp_stats = subparsers.add_parser("stats", help="Summarize review-chain usage and timing metrics")
    sp_stats.add_argument("--output-dir", default="docs/reviewer")
    sp_stats.add_argument("--json", action="store_true", help="Emit normalized JSON instead of a text table")

    return parser.parse_args(argv)


def _git_identity() -> str:
    try:
        name = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True).stdout.strip()
        email = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True).stdout.strip()
        if name and email:
            return f"{name} <{email}>"
    except Exception:
        pass
    return os.environ.get("USER", "unknown") + "@" + os.uname().nodename


def run_manual_approve(args) -> int:
    root = repo_root()
    target = (root / args.file).resolve() if not Path(args.file).is_absolute() else Path(args.file).resolve()
    reviewer_root = (root / "docs/reviewer").resolve()
    new_slug = chain_folder_name(target, args.kind, args.work_id)
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
    if not chain_dir.exists():
        print(f"ERROR: chain dir not found: {chain_dir}", file=sys.stderr)
        return 2

    manifest_path = chain_dir / "chain.json"
    manifest = read_manifest(manifest_path)
    if manifest is None:
        print(f"ERROR: chain.json not found: {manifest_path}", file=sys.stderr)
        return 2

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
    write_manifest(manifest_path, manifest)
    print(f"Manual approval recorded for {chain_dir.name} r{next_round}")
    return 0


_OUTER_FENCE_RE = re.compile(r"^\s*```[a-zA-Z0-9_-]*\s*\n(.*?)\n```\s*$", re.DOTALL)
_VERDICT_HEADING_STYLE = re.compile(
    r"(?:\*+|_+)?((?:\d+\.\s+)?(?:Overall\s+)?Verdict)(?:\*+|_+)?\s*\n+\s*"
    r"(?:\*+|_+)?(ready with small edits|ready|revise)(?:\*+|_+)?",
    re.IGNORECASE,
)


def _reformat_response(raw: str) -> str:
    m = _OUTER_FENCE_RE.match(raw)
    if m:
        raw = m.group(1)
    raw = _VERDICT_HEADING_STYLE.sub(lambda m: f"{m.group(1)}: {m.group(2)}", raw)
    return raw


def run_ingest_response(args) -> int:
    src = args.from_paste or args.from_link
    raw = Path(src).read_text(encoding="utf-8")
    reformatted = _reformat_response(raw)

    root = repo_root()
    target = (root / args.file).resolve() if not Path(args.file).is_absolute() else Path(args.file).resolve()
    reviewer_root = (root / "docs/reviewer").resolve()
    new_slug = chain_folder_name(target, args.kind, args.work_id)
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
    if not chain_dir.exists():
        print(f"ERROR: chain dir not found: {chain_dir}", file=sys.stderr)
        return 2

    manifest_path = chain_dir / "chain.json"
    manifest = read_manifest(manifest_path)
    if manifest is None:
        print(f"ERROR: chain.json not found: {manifest_path}", file=sys.stderr)
        return 2

    head = manifest["rounds"][-1] if manifest["rounds"] else None
    next_round = (head["round"] + 1) if head else 1
    timestamp = _now_local().strftime("%Y-%m-%dT%H%M")
    response_path = chain_dir / f"r{next_round}-{timestamp}-response.md"
    response_path.write_text(reformatted, encoding="utf-8")

    verdict, valid = parse_reformatted_verdict(raw)
    bridger = _git_identity()
    now_iso = _now_local().isoformat(timespec="seconds")
    new_round = {
        "round": next_round,
        "status": "human-bridged",
        "verdict": verdict,
        "verdict_valid": valid,
        "merged_verdict": verdict,
        "response": response_path.name,
        "bridged_by": bridger,
        "bridged_at": now_iso,
    }
    manifest["rounds"].append(new_round)
    write_manifest(manifest_path, manifest)

    if not valid:
        print(f"WARNING: response ingested but verdict unparseable; {response_path}", file=sys.stderr)
        return 2
    print(f"Human-bridged response recorded: {chain_dir.name} r{next_round} verdict={verdict}")
    return 0


def run_show_limit(args) -> int:
    # Prune expired entries first so we never display stale data (S1.F3).
    # get_active_limit has the side-effect of removing expired/malformed
    # entries from the state file.
    state = load_state()
    for key in list(state["limits"].keys()):
        get_active_limit(key)
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


STATS_KINDS = ("spec", "plan", "post-slice", "post-phase", "implementation", "other")


def _empty_stats_group() -> dict:
    return {
        "round_count": 0,
        "first_round_count": 0,
        "follow_up_count": 0,
        "pass_count": 0,
        "revise_count": 0,
        "total_duration_ms": 0,
        "average_duration_ms": 0,
        "first_round_average_duration_ms": 0,
        "follow_up_average_duration_ms": 0,
        "_first_duration_ms": 0,
        "_follow_duration_ms": 0,
    }


def _round_passed(round_entry: dict) -> bool:
    verdict = round_entry.get("merged_verdict") or round_entry.get("verdict")
    return verdict in ("ready", "ready with small edits")


def _estimated_usage_for_stats(chain_dir: Path, round_entry: dict) -> dict | None:
    estimated = round_entry.get("estimated_usage")
    if isinstance(estimated, dict):
        return estimated
    request = round_entry.get("request")
    response = round_entry.get("response")
    if not request or not response:
        return None
    request_path = chain_dir / request
    response_path = chain_dir / response
    if not request_path.exists() or not response_path.exists():
        return None
    try:
        return estimate_usage(
            request_path.read_text(encoding="utf-8"),
            response_path.read_text(encoding="utf-8"),
        )
    except OSError:
        return None


def _provider_usage_records_for_stats(chain_dir: Path, round_entry: dict) -> list[dict]:
    reviewers = round_entry.get("reviewers")
    if isinstance(reviewers, list) and reviewers:
        sources = [r for r in reviewers if isinstance(r, dict)]
    else:
        sources = [round_entry]

    records = []
    for source in sources:
        exact_usage = source.get("exact_usage") if isinstance(source.get("exact_usage"), dict) else {}
        provider = exact_usage.get("provider") or source.get("provider")
        estimated = _estimated_usage_for_stats(chain_dir, source)
        if provider and isinstance(estimated, dict):
            records.append({
                "provider": provider,
                "estimated_usage": estimated,
                "duration_ms": source.get("duration_ms"),
            })
    return records


def collect_review_stats(output_dir: Path) -> dict:
    groups = {kind: _empty_stats_group() for kind in STATS_KINDS}
    providers: dict[str, dict] = {}
    chain_count = 0

    for manifest_path in sorted(output_dir.glob("**/chain.json")):
        try:
            manifest = read_manifest(manifest_path)
        except Exception:
            continue
        if not manifest:
            continue
        chain_count += 1
        kind = manifest.get("kind") if manifest.get("kind") in STATS_KINDS else "other"
        group = groups[kind]
        for round_entry in manifest.get("rounds", []) or []:
            group["round_count"] += 1
            duration = round_entry.get("duration_ms")
            if isinstance(duration, (int, float)):
                group["total_duration_ms"] += int(duration)
            if int(round_entry.get("round") or 0) <= 1:
                group["first_round_count"] += 1
                if isinstance(duration, (int, float)):
                    group["_first_duration_ms"] += int(duration)
            else:
                group["follow_up_count"] += 1
                if isinstance(duration, (int, float)):
                    group["_follow_duration_ms"] += int(duration)
            if _round_passed(round_entry):
                group["pass_count"] += 1
            elif (round_entry.get("merged_verdict") or round_entry.get("verdict")) == "revise":
                group["revise_count"] += 1

            for record in _provider_usage_records_for_stats(manifest_path.parent, round_entry):
                provider = record["provider"]
                estimated = record["estimated_usage"]
                invocation_duration = record["duration_ms"]
                provider_stats = providers.setdefault(provider, {
                    "round_count": 0,
                    "estimated_input_tokens": 0,
                    "estimated_output_tokens": 0,
                    "estimated_total_tokens": 0,
                    "total_duration_ms": 0,
                    "average_duration_ms": 0,
                })
                provider_stats["round_count"] += 1
                provider_stats["estimated_input_tokens"] += int(estimated.get("estimated_input_tokens") or 0)
                provider_stats["estimated_output_tokens"] += int(estimated.get("estimated_output_tokens") or 0)
                provider_stats["estimated_total_tokens"] += int(estimated.get("estimated_total_tokens") or 0)
                if isinstance(invocation_duration, (int, float)):
                    provider_stats["total_duration_ms"] += int(invocation_duration)

    for group in groups.values():
        if group["round_count"]:
            group["average_duration_ms"] = round(group["total_duration_ms"] / group["round_count"])
        if group["first_round_count"]:
            group["first_round_average_duration_ms"] = round(group["_first_duration_ms"] / group["first_round_count"])
        if group["follow_up_count"]:
            group["follow_up_average_duration_ms"] = round(group["_follow_duration_ms"] / group["follow_up_count"])
        group.pop("_first_duration_ms", None)
        group.pop("_follow_duration_ms", None)
    for provider_stats in providers.values():
        if provider_stats["round_count"]:
            provider_stats["average_duration_ms"] = round(
                provider_stats["total_duration_ms"] / provider_stats["round_count"]
            )
    return {
        "chain_count": chain_count,
        "round_count": sum(g["round_count"] for g in groups.values()),
        "groups": groups,
        "provider_comparison": providers,
    }


def print_stats_table(stats: dict) -> None:
    print("kind           rounds  first  follow  pass  revise  total_ms  avg_ms")
    for kind in STATS_KINDS:
        group = stats["groups"][kind]
        print(
            f"{kind:<14} {group['round_count']:>6} {group['first_round_count']:>6} "
            f"{group['follow_up_count']:>7} {group['pass_count']:>5} "
            f"{group['revise_count']:>7} {group['total_duration_ms']:>9} "
            f"{group['average_duration_ms']:>7}"
        )
    if stats["provider_comparison"]:
        print()
        print("provider       rounds  est_input  est_output  est_total  avg_ms")
        for provider, data in sorted(stats["provider_comparison"].items()):
            print(
                f"{provider:<14} {data['round_count']:>6} {data['estimated_input_tokens']:>10} "
                f"{data['estimated_output_tokens']:>11} {data['estimated_total_tokens']:>10} "
                f"{data['average_duration_ms']:>7}"
            )


def run_stats(args) -> int:
    stats = collect_review_stats(Path(args.output_dir))
    if args.json:
        print(json.dumps(stats, indent=2))
    else:
        print_stats_table(stats)
    return 0


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


def _cap_lines(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[:max_lines] + [f"[truncated: {len(lines) - max_lines} additional lines]"])


def compute_diff_section(
    root: Path,
    *,
    base_ref: str | None,
    paths: list[str] | None,
    max_lines: int,
) -> str:
    UNTRACKED_FILE_LIMIT = 10
    UNTRACKED_FILE_LINE_LIMIT = 200

    if base_ref is None:
        return "Changes since prior round: not available for this round (no base ref).\n"

    diff_args = ["git", "-C", str(root), "diff", f"{base_ref}..HEAD"]
    if paths:
        diff_args.append("--")
        diff_args.extend(paths)
    diff_proc = subprocess.run(diff_args, text=True, capture_output=True)
    diff_text = diff_proc.stdout

    status_args = ["git", "-C", str(root), "status", "--porcelain"]
    if paths:
        status_args.append("--")
        status_args.extend(paths)
    status = subprocess.run(status_args, text=True, capture_output=True).stdout
    dirty = bool(status.strip())

    parts = [
        f"Worktree status: {'dirty' if dirty else 'clean'}", "",
        "### git diff base..HEAD", "",
    ]
    parts.append(_cap_lines(diff_text, max_lines))

    if dirty:
        head_diff = subprocess.run(
            ["git", "-C", str(root), "diff", "HEAD"] + (["--"] + paths if paths else []),
            text=True, capture_output=True,
        ).stdout
        parts += ["", "### git diff HEAD (uncommitted)", "", _cap_lines(head_diff, max_lines)]

    untracked = [line[3:] for line in status.splitlines() if line.startswith("?? ")]
    if untracked:
        parts += ["", "### Untracked files", ""]
        for i, rel in enumerate(untracked):
            if i >= UNTRACKED_FILE_LIMIT:
                parts.append(
                    f"\n[… {len(untracked) - UNTRACKED_FILE_LIMIT} more untracked files "
                    f"elided (cap={UNTRACKED_FILE_LIMIT}) …]\n"
                )
                break
            abs_path = root / rel
            try:
                content = abs_path.read_text(encoding="utf-8")
                per_file_cap = min(max_lines, UNTRACKED_FILE_LINE_LIMIT)
                preview = _cap_lines(content, per_file_cap)
                parts += [f"### {rel}", "", "```", preview, "```", ""]
            except (UnicodeDecodeError, OSError):
                parts += [f"- {rel} (omitted: binary or unreadable)"]

    full = "\n".join(parts) + "\n"
    return cap_with_elision(full, max_bytes=max(max_lines * 80, 64 * 1024))


def main() -> int:
    args = parse_args()
    # --state-file is global: hoist to env so load_state()/save_state() honour it.
    if getattr(args, "state_file", None):
        os.environ["AGENT_REVIEWER_STATE_FILE"] = args.state_file
    # Provider resolution (review-only): for non-review subcommands, leave
    # AGENT_REVIEWER_CMD untouched. The provider resolution result becomes the
    # authoritative reviewer command and is hoisted into the env so
    # reviewer_cmd_basename() / load_state() see the same key.
    if args.command == "review":
        try:
            args.provider_resolution = resolve_reviewer_provider(
                reviewer_provider=getattr(args, "reviewer_provider", "auto"),
                caller_provider=getattr(args, "caller_provider", "auto"),
                reviewer_cmd=getattr(args, "reviewer_cmd", None),
                env=os.environ,
            )
        except ProviderResolutionError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        args.reviewer_cmd = args.provider_resolution.command
        os.environ["AGENT_REVIEWER_CMD"] = args.reviewer_cmd
        os.environ["AGENT_REVIEWER_PROVIDER"] = args.provider_resolution.provider
        os.environ["AGENT_REVIEWER_CALLER"] = args.provider_resolution.caller_provider

    # Dispatch non-review subcommands BEFORE accessing review-only args
    # (kind, file, context, output_dir).  show-limit/clear-limit don't define
    # those attrs; manual-approve/ingest-response don't define context/output_dir.
    if args.command == "manual-approve":
        return run_manual_approve(args)
    if args.command == "ingest-response":
        return run_ingest_response(args)
    if args.command == "show-limit":
        return run_show_limit(args)
    if args.command == "clear-limit":
        return run_clear_limit(args)
    if args.command == "stats":
        return run_stats(args)

    # From here on: args.command == "review"
    if args.kind in ("post-slice", "post-phase") and not args.work_id:
        print(
            f"ERROR: --work-id is required for --kind {args.kind}. "
            "Use the slice ID (e.g. P2.S3) or phase ID (e.g. P2).",
            file=sys.stderr,
        )
        return 2
    root = repo_root()
    target = (root / args.file).resolve() if not Path(args.file).is_absolute() else Path(args.file).resolve()
    if not target.exists():
        print(f"ERROR: target file not found: {target}", file=sys.stderr)
        return 2

    context: list[Path] = []
    for raw in args.context:
        path = (root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        if not path.exists():
            print(f"ERROR: context file not found: {path}", file=sys.stderr)
            return 2
        context.append(path)

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
    manifest_path = chain_dir / "chain.json"
    try:
        manifest = read_manifest(manifest_path)
    except ManifestSchemaTooNew as exc:
        print(
            f"ERROR: {rel_or_abs(manifest_path, root)}: {exc} "
            f"(supported schema_version: {SUPPORTED_SCHEMA_VERSION})",
            file=sys.stderr,
        )
        return 4
    if manifest is not None:
        migrate_manifest_inplace(manifest)
    if manifest is None and any(chain_dir.glob("r*-*-request.md")):
        manifest = synthesize_legacy_manifest(
            chain_dir=chain_dir,
            chain=chain_dir.name,
            kind=args.kind,
            target=rel_or_abs(target, root),
            work_id=args.work_id,
        )
        migrate_manifest_inplace(manifest)
        write_manifest(manifest_path, manifest)
    if manifest is None:
        manifest = {
            "schema_version": SUPPORTED_SCHEMA_VERSION,
            "chain": new_slug,
            "kind": args.kind,
            "target": rel_or_abs(target, root),
            "work_id": args.work_id,
            "legacy_migrated": False,
            "rounds": [],
            "sweep_checkpoints": {"first-round": "pending", "final-ready": "pending"},
        }
        # F3 (r3 fix): Eager-write so run_one_reviewer rate-limit paths can read
        # chain.json on the first round (before the normal post-reviewer write).
        write_manifest(manifest_path, manifest)
    else:
        # Existing manifest: refuse a work-id mismatch (someone trying to reuse a
        # chain folder for a different slice/phase). Stored work_id is the source
        # of truth; do not mutate it. Allow when stored work_id is None (legacy
        # synthesis path may have set it, or older manifests had None).
        stored_work_id = manifest.get("work_id")
        if (
            args.work_id is not None
            and stored_work_id is not None
            and stored_work_id != args.work_id
        ):
            print(
                f"ERROR: --work-id {args.work_id!r} does not match the stored "
                f"work_id {stored_work_id!r} in {rel_or_abs(manifest_path, root)}. "
                "Refusing to reuse this chain folder for a different slice/phase.",
                file=sys.stderr,
            )
            return 6
        # If the stored value is None and a CLI value was provided, backfill it.
        if stored_work_id is None and args.work_id is not None:
            manifest["work_id"] = args.work_id

    if (
        args.kind in ("post-slice", "post-phase")
        and manifest["rounds"]
        and not args.allow_missing_resolution
    ):
        prior = manifest["rounds"][-1]
        prior_round = prior["round"]
        prior_verdict = prior.get("merged_verdict") or prior.get("verdict")
        prior_valid = prior.get("verdict_valid", True)
        prior_status = prior.get("status")  # "ok" | "failed" | "rate-limited" | "unknown" | None
        BYPASS_STATUSES = {"failed", "rate-limited"}
        prior_bypasses_gate = prior_status in BYPASS_STATUSES
        needs_resolution = (
            (prior_verdict == "revise") or (prior_valid is False)
        ) and not prior_bypasses_gate
        if prior_bypasses_gate:
            print(
                f"Note: prior round r{prior_round} status={prior_status} "
                f"(returncode={prior.get('returncode')}); "
                "resolution gate bypassed.",
                file=sys.stderr,
            )
        if needs_resolution:
            resolution_path = chain_dir / f"r{prior_round}-resolution.md"
            if not resolution_path.exists():
                rel = rel_or_abs(resolution_path, root)
                response_rel = (
                    rel_or_abs(chain_dir / prior["response"], root)
                    if prior.get("response")
                    else "<missing>"
                )
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

    round_num = next_round_number(chain_dir)
    timestamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")

    resolution_file = chain_dir / f"r{round_num - 1}-resolution.md"
    resolution_attached = resolution_file.name if (round_num > 1 and resolution_file.exists()) else None

    resolution_waiver = bool(
        args.allow_missing_resolution and round_num > 1 and not resolution_attached
    )

    mode = resolve_mode(args.mode, round_num=round_num)
    if args.prompt_transport is None:
        args.prompt_transport = "stdin"
    diff_section = ""
    base_ref: str | None = None
    base_source: str | None = None
    if mode == "incremental":
        if args.no_diff:
            diff_section = "Changes since prior round: diff suppressed via --no-diff.\n"
            base_ref = None
            base_source = "suppressed"
        else:
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

    incremental_preamble = None
    if mode == "incremental":
        incremental_preamble = build_incremental_preamble(
            manifest=manifest,
            chain_dir=chain_dir,
            round_num=round_num,
            resolution_waiver=resolution_waiver,
            legacy_first_round=(
                manifest.get("legacy_migrated", False)
                and not any(r.get("head_sha_after_round") for r in manifest["rounds"])
            ),
            diff_section=diff_section,
        )

    prompt_text = make_prompt(
        root=root, target=target, kind=args.kind,
        context=context, max_lines=args.max_lines,
        mode=mode, incremental_preamble=incremental_preamble,
        incremental_budget_chars=args.incremental_budget_chars,
    )

    head_sha_at_request = current_head_sha(root)
    worktree_dirty_at_request = is_dirty(root)

    # Plan sweep dispatch. `first-round` policy depends only on round_num /
    # checkpoint state; `final-ready` requires the CURRENT primary's verdict,
    # so we plan it AFTER the primary runs.
    checkpoints = manifest.setdefault(
        "sweep_checkpoints", {"first-round": "pending", "final-ready": "pending"}
    )
    # Pre-run plan: covers first-round only (passes None for primary verdict so
    # final-ready can never fire here).
    pre_sweep_plan = plan_sweeps(
        depth=args.review_depth,
        policy=args.sweep_policy,
        count=args.independent_reviewers,
        round_num=round_num,
        checkpoints=checkpoints,
        primary_verdict_pre_run=None,
    )
    namespaced = pre_sweep_plan.sweep_count > 0

    # Prior-round artefacts for primary template anchoring (round N+1, S6 contract).
    # Sweeps remain isolated and continue to receive None.
    previous_response_path: Path | None = None
    resolution_for_template: Path | None = None
    if round_num > 1 and manifest["rounds"]:
        prior_round_entry = manifest["rounds"][-1]
        prior_response_name = prior_round_entry.get("response")
        if prior_response_name:
            candidate = chain_dir / prior_response_name
            if candidate.exists():
                previous_response_path = candidate
        if resolution_attached:
            resolution_for_template = resolution_file

    try:
        primary = run_one_reviewer(
            role="primary", sweep_index=None,
            chain_dir=chain_dir, round_num=round_num, timestamp=timestamp,
            prompt_text=prompt_text, args=args, target=target, root=root,
            namespaced=namespaced,
            previous_response=previous_response_path,
            resolution_file=resolution_for_template,
        )

        # Post-run plan: now that primary has a verdict, evaluate final-ready.
        sweep_plan = plan_sweeps(
            depth=args.review_depth,
            policy=args.sweep_policy,
            count=args.independent_reviewers,
            round_num=round_num,
            checkpoints=checkpoints,
            primary_verdict_pre_run=primary.verdict,
        )

        # If final-ready fires but we ran primary without namespacing, rename
        # primary artefacts to add the `-primary` suffix.
        if sweep_plan.sweep_count > 0 and not namespaced:
            new_suffix = "-primary"
            new_basename = f"r{round_num}-{timestamp}{new_suffix}"
            new_request = chain_dir / f"{new_basename}-request.md"
            new_response = chain_dir / f"{new_basename}-response.md"
            old_request_rel = rel_or_abs(primary.request_path, root)
            new_request_rel = rel_or_abs(new_request, root)
            primary.request_path.rename(new_request)
            primary.response_path.rename(new_response)
            # The response body was written before the rename and embeds the
            # old `Request:` path. Rewrite that header line so artifacts stay
            # internally consistent (the response must reference the request
            # file that actually exists on disk).
            response_text = new_response.read_text(encoding="utf-8")
            old_line = f"- Request: `{old_request_rel}`"
            new_line = f"- Request: `{new_request_rel}`"
            if old_line in response_text:
                response_text = response_text.replace(old_line, new_line, 1)
                new_response.write_text(response_text, encoding="utf-8")
            primary = ReviewerResult(
                role=primary.role, sweep_index=primary.sweep_index,
                request_path=new_request, response_path=new_response,
                review_body=response_text, verdict=primary.verdict,
                verdict_valid=primary.verdict_valid, returncode=primary.returncode,
                status=primary.status,
                provider=primary.provider,
                caller_provider=primary.caller_provider,
                sandbox=primary.sandbox,
                started_at=primary.started_at,
                finished_at=primary.finished_at,
                duration_ms=primary.duration_ms,
                model=primary.model,
                estimated_usage=primary.estimated_usage,
                exact_usage=primary.exact_usage,
                usage_capture_status=primary.usage_capture_status,
                usage_capture_error=primary.usage_capture_error,
            )
            namespaced = True

        sweeps: list = []
        for k in range(1, sweep_plan.sweep_count + 1):
            sweep_prompt = prompt_text
            if sweep_plan.checkpoint == "final-ready":
                sweep_prompt = make_prompt(
                    root=root, target=target, kind=args.kind,
                    context=context, max_lines=args.max_lines,
                    mode="broad", incremental_preamble=None,
                    incremental_budget_chars=args.incremental_budget_chars,
                )
            sweeps.append(run_one_reviewer(
                role="sweep", sweep_index=k,
                chain_dir=chain_dir, round_num=round_num, timestamp=timestamp,
                prompt_text=sweep_prompt, args=args, target=target, root=root,
                namespaced=True,
            ))
    except FileNotFoundError as exc:
        print(f"ERROR: reviewer command not found: {exc}", file=sys.stderr)
        print("Set AGENT_REVIEWER_CMD, e.g. AGENT_REVIEWER_CMD='reviewer {prompt_file}'", file=sys.stderr)
        return 127
    except subprocess.TimeoutExpired:
        print(f"ERROR: reviewer command timed out after {args.timeout}s", file=sys.stderr)
        return 124
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
        return EXIT_CODE_RATE_LIMITED

    reviewer_results = [primary] + sweeps
    if sweeps:
        merged_path = write_merged_findings(
            chain_dir=chain_dir, round_num=round_num,
            primary=primary, sweeps=sweeps,
        )
        # merged_path may be None if every reviewer in the round failed.
        merged_verdict = compute_merged_verdict(reviewer_results)
        if sweep_plan.checkpoint:
            manifest["sweep_checkpoints"][sweep_plan.checkpoint] = "completed"
    else:
        merged_path = None
        merged_verdict = primary.verdict if primary.returncode == 0 else None

    # Spec: failed primary reviewers must record findings_count = 0.
    # Echoed prompt fragments on stderr can otherwise yield false finding
    # counts even though verdict is invalidated. See
    # docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md.
    if primary.returncode == 0:
        findings_count, blocking_count = parse_findings(primary.review_body)
    else:
        findings_count, blocking_count = 0, 0

    head_sha_after_round = current_head_sha(root)
    resolution_parse = None
    if resolution_attached:
        parsed = parse_resolution(resolution_file.read_text(encoding="utf-8"))
        resolution_parse = parsed.status
    # Persist work_id on first creation / backfill.
    manifest["work_id"] = args.work_id or manifest.get("work_id")
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
                "returncode": r.returncode,
                "status": _rv_status(r),
                "provider": _rv_attr(r, "provider", "custom"),
                "caller_provider": _rv_attr(r, "caller_provider", "unknown"),
                "model": _rv_attr(r, "model", None),
                "sandbox": _rv_attr(r, "sandbox", None),
                "started_at": _rv_attr(r, "started_at", None),
                "finished_at": _rv_attr(r, "finished_at", None),
                "duration_ms": _rv_attr(r, "duration_ms", None),
                "estimated_usage": _rv_attr(r, "estimated_usage", None),
                "exact_usage": _rv_attr(r, "exact_usage", None),
                "usage_capture_status": _rv_attr(r, "usage_capture_status", "unavailable"),
                "usage_capture_error": _rv_attr(r, "usage_capture_error", None),
            }
            for r in reviewer_results
        ],
        "status": "ok" if primary.returncode == 0 else "failed",
        "returncode": primary.returncode,
        "started_at": primary.started_at,
        "finished_at": primary.finished_at,
        "duration_ms": primary.duration_ms,
        "provider": primary.provider,
        "caller_provider": primary.caller_provider,
        "model": primary.model,
        "estimated_usage": primary.estimated_usage,
        "exact_usage": primary.exact_usage,
        "usage_capture_status": primary.usage_capture_status,
        "usage_capture_error": primary.usage_capture_error,
        "merged_verdict": merged_verdict,
        "merged_findings": merged_path.name if merged_path else None,
        "request": primary.request_path.name,
        "response": primary.response_path.name,
        "resolution": resolution_attached,
        "resolution_parse_status": resolution_parse,
        "resolution_waiver": resolution_waiver,
        "head_sha_at_request": head_sha_at_request,
        "head_sha_after_round": head_sha_after_round,
        "worktree_dirty_at_request": worktree_dirty_at_request,
        "verdict": primary.verdict,
        "verdict_valid": primary.verdict_valid,
        "findings_count": findings_count,
        "blocking_findings_count": blocking_count,
        "base_ref": base_ref,
        "base_ref_source": base_source,
        "diff_included": base_source in ("auto", "explicit") and not args.no_diff and bool(diff_section),
    }
    manifest["rounds"].append(round_entry)
    write_manifest(manifest_path, manifest)

    review_rel = rel_or_abs(primary.response_path, root)
    prompt_rel = rel_or_abs(primary.request_path, root)
    if args.emit == "paths":
        print(f"REVIEW_PATH={review_rel}")
        print(f"PROMPT_PATH={prompt_rel}")
        print(f"ROUND={round_num}")
    elif args.emit == "review":
        print(primary.review_body)
    elif args.emit == "json":
        merged_findings_text = merged_path.read_text(encoding="utf-8") if merged_path else None
        top_review = merged_findings_text or primary.review_body
        print(json.dumps({
            "review_path": review_rel,
            "prompt_path": prompt_rel,
            "chain": manifest["chain"],
            "round": round_num,
            "kind": args.kind,
            "work_id": manifest.get("work_id"),
            "status": "ok" if primary.returncode == 0 else "failed",
            "returncode": primary.returncode,
            "started_at": round_entry["started_at"],
            "finished_at": round_entry["finished_at"],
            "duration_ms": round_entry["duration_ms"],
            "provider": round_entry["provider"],
            "caller_provider": round_entry["caller_provider"],
            "model": round_entry["model"],
            "estimated_usage": round_entry["estimated_usage"],
            "exact_usage": round_entry["exact_usage"],
            "usage_capture_status": round_entry["usage_capture_status"],
            "usage_capture_error": round_entry["usage_capture_error"],
            "verdict": merged_verdict if merged_verdict is not None else primary.verdict,
            "verdict_valid": primary.verdict_valid,
            "findings_count": findings_count,
            "blocking_findings_count": blocking_count,
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
                    "returncode": r.returncode,
                    "status": _rv_status(r),
                    "provider": _rv_attr(r, "provider", "custom"),
                    "caller_provider": _rv_attr(r, "caller_provider", "unknown"),
                    "model": _rv_attr(r, "model", None),
                    "duration_ms": _rv_attr(r, "duration_ms", None),
                    "estimated_usage": _rv_attr(r, "estimated_usage", None),
                    "exact_usage": _rv_attr(r, "exact_usage", None),
                    "usage_capture_status": _rv_attr(r, "usage_capture_status", "unavailable"),
                }
                for r in reviewer_results
            ],
            "merged_verdict": merged_verdict,
            "merged_findings_path": rel_or_abs(merged_path, root) if merged_path else None,
            "merged_findings": merged_findings_text,
            "review": top_review,
        }, indent=2))
    return primary.returncode


VERDICT_VALUES = ("ready with small edits", "ready", "revise")
VERDICT_LINE_RE = re.compile(
    r"overall\s+verdict\s*[`*_\"']*\s*[:\-]\s*[`*_\"'\s]*(ready with small edits|ready|revise)[`*_\"'.\s]*",
    re.IGNORECASE,
)


# Anchored, value-bounded bare `Verdict:` fallback. Used only when no
# `Overall verdict:` line matches. See X10 spec §Design.2b for the trailing-
# prose policy. Do NOT add re.VERBOSE — it strips literal whitespace from
# the alternation `ready with small edits` and silently breaks the regex.
VERDICT_LINE_BARE_RE = re.compile(
    r"^[\s>#*_`]*verdict\s*[`*_\"']*\s*[:\-]\s*[`*_\"'\s]*"
    r"(ready with small edits|ready|revise)"
    r"(?=[\s`*_\"'.]*(?:$|\n))",
    re.IGNORECASE | re.MULTILINE,
)


def parse_verdict(text: str) -> tuple[str | None, bool]:
    matches = list(VERDICT_LINE_RE.finditer(text))
    if not matches:
        matches = list(VERDICT_LINE_BARE_RE.finditer(text))
    if not matches:
        return None, False
    raw = matches[-1].group(1).strip().lower()
    if raw not in VERDICT_VALUES:
        return None, False
    return raw, True


def parse_reformatted_verdict(raw: str) -> tuple[str | None, bool]:
    """Compose `_reformat_response` and `parse_verdict`.

    Single chokepoint for response-body verdict extraction. Used by both the
    automated round path and the manual ingest path. NOT used by legacy
    manifest synthesis (`synthesize_manifest_from_legacy_files`) — that path
    parses historical bodies as-stored and must not rewrite them.
    """
    return parse_verdict(_reformat_response(raw))


HEADING_FINDING_RE = re.compile(r"^##\s+F(\d+)\b(.*)$", re.MULTILINE)
# Prose findings: `F<n>` followed by one of `.`, `-`, `—`, `:` separators, then
# the heading content. The heading content may be wrapped in markdown bold
# (`**...**`) and an explicit severity word may or may not be present
# immediately after the separator. We capture the rest of the line so the
# caller can inspect the paragraph for a `Blocking` marker.
PROSE_FINDING_RE = re.compile(
    r"^F(\d+)\s*[.\-—:]\s+(.*)$",
    re.MULTILINE,
)
PROSE_SEVERITY_RE = re.compile(
    r"\b(Blocking|Important|Minor|Critical|Major|Nit)\b",
    re.IGNORECASE,
)
PROSE_BLOCKING_PARAGRAPH_RE = re.compile(r"\bBlocking\b", re.IGNORECASE)
BULLET_FINDING_RE = re.compile(r"^\s*[-*]\s*\**F(\d+)\**[:\s\-](.*)$", re.MULTILINE)
INLINE_BLOCKING_RE = re.compile(r"\(blocking\)", re.IGNORECASE)
SEVERITY_BLOCKING_RE = re.compile(r"^severity\s*:\s*blocking", re.IGNORECASE | re.MULTILINE)
CRASH_SENTINEL_RE = re.compile(
    r"^(?:reviewer crashed|status\s*:\s*reviewer crashed)",
    re.IGNORECASE | re.MULTILINE,
)
# Recognised "explicit empty findings" markers. A reviewer that clearly
# declares zero findings (e.g. "## Findings\nnone" or "Findings: none") is
# parseable as (0, 0); anything else with no F-IDs is unparseable -> (None, None).
EMPTY_FINDINGS_RE = re.compile(
    r"(?:^##\s*Findings\s*\n+\s*(?:none|no findings|n/?a)\b"
    r"|^findings\s*:\s*(?:none|no findings|n/?a|0|zero)\b)",
    re.IGNORECASE | re.MULTILINE,
)


def _collect_findings(text: str) -> tuple[dict[str, bool], str]:
    """Return ({id: blocking?}, style) for the first style that yields matches.

    Style precedence: prose ('F1. Blocking: ...') > heading ('## F1') > bullet.
    Prose wins when present because real reviewer output uses it and may also
    incidentally contain heading/bullet shapes inside embedded previews.
    """
    findings: dict[str, bool] = {}
    # Collect prose matches with their span so we can scope each finding's
    # paragraph (up to the next prose finding, or end of text).
    prose_matches = list(PROSE_FINDING_RE.finditer(text))
    for idx, m in enumerate(prose_matches):
        fid = m.group(1)
        rest = m.group(2) or ""
        # Strip optional markdown-bold wrapper so a leading `**` does not hide
        # the severity word from the inline-severity check.
        rest_stripped = rest.lstrip()
        if rest_stripped.startswith("**"):
            rest_stripped = rest_stripped[2:]
        inline_sev = PROSE_SEVERITY_RE.match(rest_stripped)
        if inline_sev:
            is_blocking = inline_sev.group(1).lower() == "blocking"
        else:
            # No inline severity — inspect the finding's immediate paragraph
            # for a `Blocking` token. The paragraph runs from the finding's
            # heading line up to the first blank line (markdown paragraph
            # break) or the next prose finding, whichever comes first. This
            # keeps us from sweeping in unrelated `blocking` mentions that
            # appear in quoted previews further down the response.
            next_finding_start = (
                prose_matches[idx + 1].start()
                if idx + 1 < len(prose_matches)
                else len(text)
            )
            blank_line = re.search(r"\n\s*\n", text[m.end():next_finding_start])
            if blank_line:
                para_end = m.end() + blank_line.start()
            else:
                para_end = next_finding_start
            paragraph = text[m.start():para_end]
            is_blocking = bool(PROSE_BLOCKING_PARAGRAPH_RE.search(paragraph))
        # First occurrence wins; later duplicates from echoed/quoted content
        # do not change the blocking flag.
        if fid not in findings:
            findings[fid] = is_blocking
    if findings:
        return findings, "prose"

    for m in HEADING_FINDING_RE.finditer(text):
        fid = m.group(1)
        if fid not in findings:
            findings[fid] = False
    if findings:
        return findings, "heading"

    for m in BULLET_FINDING_RE.finditer(text):
        fid = m.group(1)
        rest = m.group(2) or ""
        if fid not in findings:
            findings[fid] = bool(INLINE_BLOCKING_RE.search(rest))
    return findings, "bullet"


def parse_findings(text: str) -> tuple[int | None, int | None]:
    """Return (findings_count, blocking_findings_count) per spec.

    Per docs/superstar/specs/2026-05-13-external-reviewer-redesign-design.md
    (Finding-count parsing): if no accepted finding form matches AND no
    explicit-empty marker is present, both counts are ``None`` and the
    coordinator inspects prose. A crash sentinel also yields ``(None, None)``.
    """
    if not text or text.strip() == "":
        return None, None
    # Crash sentinel short-circuits before everything else.
    if CRASH_SENTINEL_RE.search(text):
        return None, None
    findings, style = _collect_findings(text)
    if findings:
        n = len(findings)
        blocking = sum(1 for v in findings.values() if v)
        if style == "heading":
            # Heading style has no severity inline; fall back to severity-line
            # markers within the body.
            blocking = len(SEVERITY_BLOCKING_RE.findall(text))
        return n, blocking
    # No finding form matched. Honor explicit "no findings" declarations as
    # (0, 0); otherwise the response is unparseable for finding-count purposes.
    if EMPTY_FINDINGS_RE.search(text):
        return 0, 0
    return None, None


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


class ResolutionParseResult:
    """Result of parsing a resolution doc. status is one of ok|partial|unparseable."""

    __slots__ = ("status", "findings", "unmatched")

    def __init__(self, status: str, findings: dict | None = None, unmatched: list | None = None):
        self.status = status
        self.findings = findings if findings is not None else {}
        self.unmatched = unmatched if unmatched is not None else []

    def __repr__(self) -> str:
        return (
            f"ResolutionParseResult(status={self.status!r}, "
            f"findings={self.findings!r}, unmatched={self.unmatched!r})"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, ResolutionParseResult):
            return NotImplemented
        return (
            self.status == other.status
            and self.findings == other.findings
            and self.unmatched == other.unmatched
        )


RESOLUTION_HEADING_RE = re.compile(r"^##\s+(F\d+)\b", re.MULTILINE)
RESOLUTION_STATUS_RE = re.compile(
    r"^\s*status\s*:\s*(fixed|waived|deferred)\b", re.IGNORECASE | re.MULTILINE
)


def parse_resolution(text: str) -> ResolutionParseResult:
    headings = list(RESOLUTION_HEADING_RE.finditer(text))
    if not headings:
        return ResolutionParseResult(status="unparseable")

    findings: dict = {}
    unmatched: list = []
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

    status = "ok" if not unmatched else "partial"
    return ResolutionParseResult(status=status, findings=findings, unmatched=unmatched)


if __name__ == "__main__":
    raise SystemExit(main())
