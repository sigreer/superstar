# External Reviewer Provider Sandboxing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make external review choose the opposite reviewer provider by default and run reviewers with repository read-only access plus narrowly scoped scratch/output write access.

**Architecture:** The bridge owns invocation context: repo root, chain dir, role, scratch dir, response-output dir, provider, and caller. Provider wrappers own CLI-specific sandbox flags. The existing `AGENT_REVIEWER_CMD` override remains available, but the default path becomes provider-aware and fail-closed when caller identity cannot be determined.

**Tech Stack:** Python stdlib only for `external-reviewer.py` and pytest for tests. Bash for the `reviewer-agent` wrapper template.

**Source spec:** `docs/specs/2026-05-17-external-reviewer-provider-sandboxing-spec.md`.

**Safety note:** Do not run the current live `reviewer-agent` as part of this plan until the wrapper has been replaced or the command is overridden with a fake reviewer. The current installed wrapper uses `codex exec --dangerously-bypass-approvals-and-sandbox`.

---

## Files At A Glance

| Path | Action | Purpose |
|---|---|---|
| `skills/external-review/scripts/external-reviewer.py` | Modify | Provider resolution, reviewer context env vars, scratch/output dirs, new placeholders, metadata. |
| `skills/external-review/tests/test_provider_selection.py` | Create | Unit tests for caller/provider resolution and custom override behavior. |
| `skills/external-review/tests/test_reviewer_invocation_context.py` | Create | Unit/subprocess tests for env injection, scratch cleanup, role-specific dirs, placeholders. |
| `skills/external-review/tests/test_reviewer_sandbox_metadata.py` | Create | End-to-end fake-reviewer tests for chain metadata and response artifact headers. |
| `skills/external-review/tests/test_reviewer_agent_wrapper.py` | Create | Fake `codex`/`claude` PATH tests for wrapper argv contracts. |
| `skills/project-setup/scripts/reviewer-agent` | Create | Provider-aware reviewer wrapper template. |
| `skills/project-setup/SKILL.md` | Modify | Setup checklist points to the safe wrapper template and no-bypass policy. |
| `skills/external-review/SKILL.md` | Modify | Documents provider flipping, forcing providers, custom commands, sandbox contract. |
| `~/.local/bin/reviewer-agent` | Replace after tests | Local installed wrapper. Replace once fake wrapper tests and focused bridge tests pass. |

## Conventions

- Run all commands from repo root: `/home/simon/Dev/sigreer/skills/superstar`.
- Test import boilerplate for `external-reviewer.py`:

```python
from pathlib import Path
import importlib.util
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
sys.modules["external_reviewer"] = er
spec.loader.exec_module(er)
```

- Every subprocess test that invokes `review` must set `AGENT_REVIEWER_STATE_FILE` to a `tmp_path` file so tests never touch `~/.config/superstar/reviewer-state.json`.
- `AGENT_REVIEWER_CMD` is an explicit custom override. Tests for provider auto-selection must clear it with `monkeypatch.delenv("AGENT_REVIEWER_CMD", raising=False)`.
- Commit after each task.

## Spec To Plan Mapping

| Spec requirement | Plan task |
|---|---|
| No bypass flag in default wrapper | Task 4.1, Task 4.2 |
| Repo read-only, scratch/output writable | Task 2.1, Task 2.2, Task 4.1, Task 6.2 |
| Bridge passes path context | Task 2.1 |
| New placeholders | Task 2.3 |
| Provider flip based on caller | Task 1.1, Task 1.2 |
| `AGENT_REVIEWER_CMD` remains override | Task 1.1 |
| Metadata visible in manifest/artifact | Task 3.1 |
| Env-var authority and sweep-index semantics | Task 2.1, Task 2.4 |
| Stale scratch cleanup guidance | Task 2.4 |
| Docs/project setup updates | Task 2.4, Task 4.2, Task 5.1 |
| Replace dangerous installed wrapper promptly | Task 4.3 |
| Live safety smoke | Task 6.2, Task 6.3 |

---

## Slice 1 - Provider Resolution

This slice is pure logic and argparse wiring. No reviewer subprocess behavior changes yet.

### Task 1.1: Add provider resolution helpers

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Create: `skills/external-review/tests/test_provider_selection.py`

- [ ] **Step 1: Write the failing tests**

Create `skills/external-review/tests/test_provider_selection.py`:

```python
from pathlib import Path
import importlib.util
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
sys.modules["external_reviewer"] = er
spec.loader.exec_module(er)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for key in (
        "AGENT_REVIEWER_CMD",
        "AGENT_REVIEWER_PROVIDER",
        "AGENT_REVIEWER_CALLER",
        "CLAUDECODE",
        "CLAUDE_CODE",
        "CODEX_HOME",
    ):
        monkeypatch.delenv(key, raising=False)


def test_custom_reviewer_cmd_wins(monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_CMD", "/tmp/my-reviewer")
    resolved = er.resolve_reviewer_provider(
        reviewer_provider="auto",
        caller_provider="claude",
        reviewer_cmd="/tmp/my-reviewer",
        env=dict(),
    )
    assert resolved.provider == "custom"
    assert resolved.caller_provider == "claude"
    assert resolved.command == "/tmp/my-reviewer"


def test_claude_caller_auto_selects_codex():
    resolved = er.resolve_reviewer_provider(
        reviewer_provider="auto",
        caller_provider="claude",
        reviewer_cmd=None,
        env=dict(),
    )
    assert resolved.provider == "codex"
    assert resolved.command == "reviewer-agent"


def test_codex_caller_auto_selects_claude():
    resolved = er.resolve_reviewer_provider(
        reviewer_provider="auto",
        caller_provider="codex",
        reviewer_cmd=None,
        env=dict(),
    )
    assert resolved.provider == "claude"
    assert resolved.command == "reviewer-agent"


def test_unknown_caller_auto_fails_closed():
    with pytest.raises(er.ProviderResolutionError, match="caller provider"):
        er.resolve_reviewer_provider(
            reviewer_provider="auto",
            caller_provider="unknown",
            reviewer_cmd=None,
            env=dict(),
        )


def test_explicit_provider_uses_reviewer_agent_command():
    resolved = er.resolve_reviewer_provider(
        reviewer_provider="codex",
        caller_provider="unknown",
        reviewer_cmd=None,
        env=dict(),
    )
    assert resolved.provider == "codex"
    assert resolved.command == "reviewer-agent"
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_provider_selection.py -v
```

Expected: FAIL with `AttributeError: module 'external_reviewer' has no attribute 'resolve_reviewer_provider'`.

- [ ] **Step 3: Implement the helpers**

In `skills/external-review/scripts/external-reviewer.py`, add `ProviderResolution` near the existing dataclasses:

```python
@dataclass
class ProviderResolution:
    provider: str
    caller_provider: str
    command: str


class ProviderResolutionError(Exception):
    pass
```

Add these helpers near `reviewer_cmd_basename()`:

```python
def detect_caller_provider(env: dict[str, str] | None = None) -> str:
    env = env or os.environ
    explicit = env.get("AGENT_REVIEWER_CALLER")
    if explicit in {"claude", "codex", "unknown"}:
        return explicit
    if env.get("CLAUDECODE") or env.get("CLAUDE_CODE"):
        return "claude"
    if env.get("CODEX_HOME") or env.get("OPENAI_CODEX"):
        return "codex"
    return "unknown"


def resolve_reviewer_provider(
    *,
    reviewer_provider: str,
    caller_provider: str,
    reviewer_cmd: str | None,
    env: dict[str, str] | None = None,
) -> ProviderResolution:
    env = env or os.environ
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
```

- [ ] **Step 4: Run the tests**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_provider_selection.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_provider_selection.py
git commit -m "external-reviewer: add reviewer provider resolution"
```

### Task 1.2: Wire provider flags into argparse and main

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Modify: `skills/external-review/tests/test_provider_selection.py`

- [ ] **Step 1: Write the failing CLI tests**

Append to `skills/external-review/tests/test_provider_selection.py`:

```python
def test_parse_args_accepts_provider_flags():
    args = er.parse_args([
        "review",
        "--kind", "spec",
        "--file", "docs/specs/example.md",
        "--reviewer-provider", "codex",
        "--caller-provider", "claude",
    ])
    assert args.reviewer_provider == "codex"
    assert args.caller_provider == "claude"


def test_env_provider_default_is_auto(monkeypatch):
    monkeypatch.delenv("AGENT_REVIEWER_PROVIDER", raising=False)
    args = er.parse_args(["review", "--kind", "spec", "--file", "x.md"])
    assert args.reviewer_provider == "auto"


def test_reviewer_cmd_default_is_none_without_env(monkeypatch):
    monkeypatch.delenv("AGENT_REVIEWER_CMD", raising=False)
    args = er.parse_args(["review", "--kind", "spec", "--file", "x.md"])
    assert args.reviewer_cmd is None


def test_reviewer_cmd_reads_env_override(monkeypatch):
    monkeypatch.setenv("AGENT_REVIEWER_CMD", "/tmp/custom-reviewer")
    args = er.parse_args(["review", "--kind", "spec", "--file", "x.md"])
    assert args.reviewer_cmd == "/tmp/custom-reviewer"
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_provider_selection.py -v
```

Expected: FAIL because `parse_args()` does not accept an argv argument and the new flags do not exist.

- [ ] **Step 3: Make `parse_args` testable and add flags**

Change `parse_args` signature from:

```python
def parse_args():
```

to:

```python
def parse_args(argv: list[str] | None = None):
```

Change the final parse call to:

```python
return parser.parse_args(argv)
```

In the `review` subparser, change `--reviewer-cmd` so the default is only the env var, not the literal `reviewer-agent`:

```python
sp_review.add_argument(
    "--reviewer-cmd",
    default=os.environ.get("AGENT_REVIEWER_CMD"),
    help="Custom command or template. When set, provider auto-selection is bypassed. Supports {prompt_file}, {prompt_text}, {target_file}, {kind}, {chain_dir}, {round}, {previous_response}, {resolution_file}, {session_file}, {repo_root}, {response_dir}, {scratch_dir}, {request_file}.",
)
```

Then add:

```python
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
```

Leave `--reviewer-cmd` in place for backward compatibility.

- [ ] **Step 4: Run the tests**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_provider_selection.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_provider_selection.py
git commit -m "external-reviewer: expose reviewer provider flags"
```

---

## Slice 2 - Reviewer Invocation Context

This slice gives wrappers the path context needed to enforce sandboxing.

### Task 2.1: Create scratch/output context and pass env to subprocesses

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Create: `skills/external-review/tests/test_reviewer_invocation_context.py`

- [ ] **Step 1: Write the failing end-to-end env test**

Create `skills/external-review/tests/test_reviewer_invocation_context.py`:

```python
from pathlib import Path
import json
import os
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    (repo / "plan.md").write_text("# Plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    return repo


def test_reviewer_receives_sandbox_context_env(tmp_path):
    repo = _repo(tmp_path)
    reviewer = repo / "fake-reviewer.py"
    reviewer.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os\n"
        "keys = [\n"
        "  'AGENT_REVIEWER_REPO_ROOT', 'AGENT_REVIEWER_CHAIN_DIR',\n"
        "  'AGENT_REVIEWER_REQUEST_FILE', 'AGENT_REVIEWER_RESPONSE_DIR',\n"
        "  'AGENT_REVIEWER_SCRATCH_DIR', 'AGENT_REVIEWER_TARGET_FILE',\n"
        "  'AGENT_REVIEWER_KIND', 'AGENT_REVIEWER_ROLE', 'AGENT_REVIEWER_SWEEP_INDEX',\n"
        "  'AGENT_REVIEWER_PROVIDER', 'AGENT_REVIEWER_CALLER',\n"
        "]\n"
        "print(json.dumps({k: os.environ.get(k, '') for k in keys}, sort_keys=True))\n"
        "print('Overall verdict: ready')\n"
    )
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "state.json")
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "external-reviewer.py"),
            "review",
            "--kind", "post-slice",
            "--work-id", "P1.S1",
            "--file", "plan.md",
            "--emit", "json",
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    review = payload["review"]
    start = review.index("{")
    end = review.index("}", start) + 1
    seen = json.loads(review[start:end])
    assert seen["AGENT_REVIEWER_REPO_ROOT"] == str(repo)
    assert seen["AGENT_REVIEWER_KIND"] == "post-slice"
    assert seen["AGENT_REVIEWER_ROLE"] == "primary"
    assert seen["AGENT_REVIEWER_PROVIDER"] == "custom"
    assert seen["AGENT_REVIEWER_CALLER"] in {"auto", "unknown", ""}
    assert seen["AGENT_REVIEWER_SWEEP_INDEX"] == ""
    assert Path(seen["AGENT_REVIEWER_RESPONSE_DIR"]).is_dir()
    assert seen["AGENT_REVIEWER_REQUEST_FILE"].endswith("-request.md")
    assert seen["AGENT_REVIEWER_TARGET_FILE"] == str(repo / "plan.md")
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_reviewer_invocation_context.py::test_reviewer_receives_sandbox_context_env -v
```

Expected: FAIL because the env vars are absent.

- [ ] **Step 3: Implement invocation context**

In `external-reviewer.py`, add imports:

```python
import tempfile
import shutil
```

Add a dataclass near `ReviewerResult`:

```python
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

    def env(self) -> dict[str, str]:
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
```

Change `run_reviewer` to accept `extra_env: dict[str, str] | None = None` and pass it to both `subprocess.run` calls:

```python
run_env = os.environ.copy()
if extra_env:
    run_env.update(extra_env)
```

Then add `env=run_env` to both `subprocess.run(...)` calls inside `run_reviewer`.

In `run_one_reviewer`, after `request_path.write_text(...)`, create:

```python
role_name = "primary" if role == "primary" else f"sweep{sweep_index}"
response_dir = chain_dir / ".reviewer-output" / f"r{round_num}-{role_name}"
response_dir.mkdir(parents=True, exist_ok=True)
scratch_dir = Path(tempfile.mkdtemp(prefix=f"superstar-reviewer-{chain_dir.name}-r{round_num}-{role_name}-"))
scratch_dir.chmod(0o700)
provider_resolution = getattr(args, "provider_resolution", ProviderResolution("custom", "unknown", args.reviewer_cmd))
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
```

Wrap the actual `run_reviewer(...)` call and subsequent rate-limit/artifact handling in `try: ... finally:`:

```python
try:
    result = run_reviewer(
        ...
        extra_env=invocation_context.env(),
    )
finally:
    if not getattr(args, "keep_reviewer_scratch", False):
        shutil.rmtree(scratch_dir, ignore_errors=True)
```

Do not remove `response_dir`.

In `main()`, remove the old early hoist block that treats the argparse default as `AGENT_REVIEWER_CMD`:

```python
cli_reviewer_cmd = getattr(args, "reviewer_cmd", None)
if cli_reviewer_cmd and cli_reviewer_cmd != os.environ.get("AGENT_REVIEWER_CMD"):
    os.environ["AGENT_REVIEWER_CMD"] = cli_reviewer_cmd
```

Replace it with provider resolution after target/context validation and before rate-limit checks or reviewer subprocesses:

```python
try:
    args.provider_resolution = resolve_reviewer_provider(
        reviewer_provider=args.reviewer_provider,
        caller_provider=args.caller_provider,
        reviewer_cmd=args.reviewer_cmd,
        env=os.environ,
    )
    args.reviewer_cmd = args.provider_resolution.command
    os.environ["AGENT_REVIEWER_CMD"] = args.reviewer_cmd
    os.environ["AGENT_REVIEWER_PROVIDER"] = args.provider_resolution.provider
    os.environ["AGENT_REVIEWER_CALLER"] = args.provider_resolution.caller_provider
except ProviderResolutionError as exc:
    print(f"ERROR: {exc}", file=sys.stderr)
    return 2
```

This preserves explicit env/CLI custom command behavior while using `reviewer-agent` for provider defaults. It also keeps `reviewer_cmd_basename()` aligned with the resolved command for rate-limit state keys.

- [ ] **Step 4: Run the test**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_reviewer_invocation_context.py::test_reviewer_receives_sandbox_context_env -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_reviewer_invocation_context.py
git commit -m "external-reviewer: pass sandbox context to reviewers"
```

### Task 2.2: Add scratch retention flag and cleanup tests

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Modify: `skills/external-review/tests/test_reviewer_invocation_context.py`

- [ ] **Step 1: Write cleanup tests**

Append:

```python
def test_reviewer_scratch_is_removed_by_default(tmp_path):
    repo = _repo(tmp_path)
    marker = repo / "scratch-path.txt"
    reviewer = repo / "fake-reviewer.py"
    reviewer.write_text(
        "#!/usr/bin/env python3\n"
        "import os, pathlib\n"
        f"pathlib.Path({str(marker)!r}).write_text(os.environ['AGENT_REVIEWER_SCRATCH_DIR'])\n"
        "print('Overall verdict: ready')\n"
    )
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "state.json")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"), "review", "--kind", "spec", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    scratch = Path(marker.read_text())
    assert not scratch.exists()


def test_reviewer_scratch_directory_is_private_0700(tmp_path):
    repo = _repo(tmp_path)
    marker = repo / "scratch-mode.txt"
    reviewer = repo / "fake-reviewer.py"
    reviewer.write_text(
        "#!/usr/bin/env python3\n"
        "import os, pathlib\n"
        "scratch = pathlib.Path(os.environ['AGENT_REVIEWER_SCRATCH_DIR'])\n"
        f"pathlib.Path({str(marker)!r}).write_text(oct(scratch.stat().st_mode & 0o777))\n"
        "print('Overall verdict: ready')\n"
    )
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "state.json")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"), "review", "--kind", "spec", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert marker.read_text() == "0o700"


def test_keep_reviewer_scratch_preserves_directory(tmp_path):
    repo = _repo(tmp_path)
    marker = repo / "scratch-path.txt"
    reviewer = repo / "fake-reviewer.py"
    reviewer.write_text(
        "#!/usr/bin/env python3\n"
        "import os, pathlib\n"
        "scratch = pathlib.Path(os.environ['AGENT_REVIEWER_SCRATCH_DIR'])\n"
        "(scratch / 'note.txt').write_text('kept')\n"
        f"pathlib.Path({str(marker)!r}).write_text(str(scratch))\n"
        "print('Overall verdict: ready')\n"
    )
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "state.json")
    result = subprocess.run(
        [
            sys.executable, str(SCRIPTS / "external-reviewer.py"),
            "review", "--kind", "spec", "--file", "plan.md",
            "--keep-reviewer-scratch",
            "--emit", "json",
        ],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    scratch = Path(marker.read_text())
    assert (scratch / "note.txt").read_text() == "kept"
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_reviewer_invocation_context.py -v
```

Expected: the keep-scratch test fails because the flag is not defined.

- [ ] **Step 3: Add the flag**

In the review subparser, add:

```python
sp_review.add_argument(
    "--keep-reviewer-scratch",
    action="store_true",
    help="Preserve the reviewer scratch directory for debugging.",
)
```

The cleanup implementation from Task 2.1 already reads `args.keep_reviewer_scratch`.

- [ ] **Step 4: Run tests**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_reviewer_invocation_context.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_reviewer_invocation_context.py
git commit -m "external-reviewer: manage reviewer scratch lifecycle"
```

### Task 2.3: Add new template placeholders

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Modify: `skills/external-review/tests/test_reviewer_invocation_context.py`

- [ ] **Step 1: Write the failing placeholder test**

Append:

```python
def test_new_command_template_placeholders(tmp_path):
    from pathlib import Path
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
    er = importlib.util.module_from_spec(spec)
    sys.modules["external_reviewer"] = er
    spec.loader.exec_module(er)

    prompt_file = tmp_path / "prompt.md"
    target_file = tmp_path / "target.md"
    chain_dir = tmp_path / "chain"
    response_dir = chain_dir / ".reviewer-output" / "r1-primary"
    scratch_dir = tmp_path / "scratch"
    request_file = chain_dir / "r1-request.md"
    for path in (prompt_file, target_file, request_file):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x")
    response_dir.mkdir(parents=True)
    scratch_dir.mkdir()
    out = er.expand_command_template(
        "tool {repo_root} {response_dir} {scratch_dir} {request_file}",
        prompt_file=prompt_file,
        prompt_text="hello",
        target_file=target_file,
        kind="spec",
        chain_dir=chain_dir,
        round_num=1,
        previous_response=None,
        resolution_file=None,
        session_file=chain_dir / "session.state",
        repo_root=tmp_path,
        response_dir=response_dir,
        scratch_dir=scratch_dir,
        request_file=request_file,
    )
    assert str(tmp_path) in out
    assert str(response_dir) in out
    assert str(scratch_dir) in out
    assert str(request_file) in out
```

- [ ] **Step 2: Run failing test**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_reviewer_invocation_context.py::test_new_command_template_placeholders -v
```

Expected: FAIL because `expand_command_template` does not accept the new keyword args.

- [ ] **Step 3: Extend `expand_command_template` and call sites**

Add parameters to `expand_command_template`:

```python
    repo_root: Path,
    response_dir: Path,
    scratch_dir: Path,
    request_file: Path,
```

Add values:

```python
        "repo_root": shlex.quote(str(repo_root)),
        "response_dir": shlex.quote(str(response_dir)),
        "scratch_dir": shlex.quote(str(scratch_dir)),
        "request_file": shlex.quote(str(request_file)),
```

Add matching parameters to `run_reviewer` and pass them to `expand_command_template`. From `run_one_reviewer`, pass:

```python
repo_root=root,
response_dir=response_dir,
scratch_dir=scratch_dir,
request_file=request_path,
```

- [ ] **Step 4: Run tests**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_reviewer_invocation_context.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_reviewer_invocation_context.py
git commit -m "external-reviewer: expose sandbox command placeholders"
```

### Task 2.4: Document env authority and stale scratch cleanup

**Files:**
- Modify: `skills/external-review/SKILL.md`

- [ ] **Step 1: Add reviewer context contract docs**

In `skills/external-review/SKILL.md`, add this paragraph to the configuration section:

```markdown
The bridge exports `AGENT_REVIEWER_REPO_ROOT`, `AGENT_REVIEWER_CHAIN_DIR`, `AGENT_REVIEWER_REQUEST_FILE`, `AGENT_REVIEWER_RESPONSE_DIR`, `AGENT_REVIEWER_SCRATCH_DIR`, `AGENT_REVIEWER_TARGET_FILE`, `AGENT_REVIEWER_KIND`, `AGENT_REVIEWER_ROLE`, and `AGENT_REVIEWER_SWEEP_INDEX` for every reviewer process. `AGENT_REVIEWER_SWEEP_INDEX` is always set: empty for primary, numeric for sweeps. These env vars are authoritative; command placeholders are convenience sugar derived from the same values.
```

Add this cleanup note:

````markdown
Scratch directories are owner-only and normally removed by the bridge. If a process is killed before cleanup, remove stale dirs with:

```bash
find "${TMPDIR:-/tmp}" -maxdepth 1 -type d -name 'superstar-reviewer-*' -mtime +1 -prune -exec rm -rf -- {} +
```
````

- [ ] **Step 2: Verify the docs contain the semantics**

Run:

```bash
rg -n "AGENT_REVIEWER_SWEEP_INDEX|authoritative|superstar-reviewer-\\*" skills/external-review/SKILL.md
```

Expected: all terms are present.

- [ ] **Step 3: Commit**

```bash
git add skills/external-review/SKILL.md
git commit -m "external-review: document reviewer context contract"
```

---

## Slice 3 - Metadata And Artifact Visibility

### Task 3.1: Record provider/sandbox metadata in artifacts and manifest

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`
- Create: `skills/external-review/tests/test_reviewer_sandbox_metadata.py`

- [ ] **Step 1: Write failing metadata tests**

Create `skills/external-review/tests/test_reviewer_sandbox_metadata.py`:

```python
from pathlib import Path
import json
import os
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    (repo / "plan.md").write_text("# Plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    reviewer = repo / "fake-reviewer.sh"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)
    return repo, reviewer


def test_manifest_records_provider_and_sandbox(tmp_path):
    repo, reviewer = _repo(tmp_path)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "state.json")
    result = subprocess.run(
        [
            sys.executable, str(SCRIPTS / "external-reviewer.py"),
            "review", "--kind", "post-slice", "--work-id", "P1.S1",
            "--file", "plan.md", "--emit", "json",
        ],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    chain = repo / "docs" / "reviewer" / "plan-P1-S1-post-slice"
    manifest = json.loads((chain / "chain.json").read_text())
    reviewer_entry = manifest["rounds"][0]["reviewers"][0]
    assert reviewer_entry["provider"] == "custom"
    assert reviewer_entry["sandbox"]["repo_root"] == str(repo)
    assert reviewer_entry["sandbox"]["mode"] == "custom"
    assert reviewer_entry["sandbox"]["response_dir"].endswith(".reviewer-output/r1-primary")
    assert "scratch_dir" in reviewer_entry["sandbox"]


def test_response_artifact_mentions_provider_and_sandbox(tmp_path):
    repo, reviewer = _repo(tmp_path)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    env["AGENT_REVIEWER_STATE_FILE"] = str(tmp_path / "state.json")
    result = subprocess.run(
        [
            sys.executable, str(SCRIPTS / "external-reviewer.py"),
            "review", "--kind", "spec", "--file", "plan.md", "--emit", "json",
        ],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    response_text = Path(payload["response_path"]).read_text()
    assert "- Reviewer provider: `custom`" in response_text
    assert "- Sandbox: " in response_text
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_reviewer_sandbox_metadata.py -v
```

Expected: FAIL because manifest reviewer entries and response artifacts lack provider/sandbox metadata.

- [ ] **Step 3: Add metadata fields**

Extend `ReviewerResult` with:

```python
    provider: str = "custom"
    caller_provider: str = "unknown"
    sandbox: dict | None = None
```

In `run_one_reviewer`, when returning `ReviewerResult`, pass:

```python
provider=invocation_context.provider,
caller_provider=invocation_context.caller_provider,
sandbox={
    "repo_root": str(root),
    "scratch_dir": str(scratch_dir),
    "response_dir": rel_or_abs(response_dir, root),
    "mode": "custom" if invocation_context.provider == "custom" else (
        "workspace-write-with-read-access" if invocation_context.provider == "codex" else "plan-read-only"
    ),
},
```

Update any rate-limited/failed sweep `ReviewerResult` construction in `run_one_reviewer` to include the same provider/sandbox values when `invocation_context` exists.

In the function that builds manifest reviewer entries, add:

```python
"provider": _rv_attr(r, "provider", "custom"),
"caller_provider": _rv_attr(r, "caller_provider", "unknown"),
"sandbox": _rv_attr(r, "sandbox", None),
```

Change `write_review_artifact` to accept `provider: str` and `sandbox_summary: str`, and add these lines to the `content` list after reviewer command:

```python
        f"- Reviewer provider: `{provider}`",
        f"- Sandbox: {sandbox_summary}",
```

Pass:

```python
provider=invocation_context.provider,
sandbox_summary="repo read-only; scratch/output writable" if invocation_context.provider != "custom" else "custom command; bridge-provided scratch/output context",
```

- [ ] **Step 4: Run metadata tests**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_reviewer_sandbox_metadata.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_reviewer_sandbox_metadata.py
git commit -m "external-reviewer: record reviewer sandbox metadata"
```

---

## Slice 4 - Provider-Aware Wrapper Template

This slice adds a safe wrapper template and tests its argv without invoking real Codex or Claude.

### Task 4.1: Add wrapper contract tests

**Files:**
- Create: `skills/external-review/tests/test_reviewer_agent_wrapper.py`
- Create: `skills/project-setup/scripts/reviewer-agent`

- [ ] **Step 1: Write the failing wrapper tests**

Create `skills/external-review/tests/test_reviewer_agent_wrapper.py`:

```python
from pathlib import Path
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[3]
WRAPPER = ROOT / "skills" / "project-setup" / "scripts" / "reviewer-agent"


def _fake_bin(tmp_path, name):
    calls = tmp_path / f"{name}-calls.json"
    exe = tmp_path / name
    exe.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, pathlib, sys\n"
        f"calls = pathlib.Path({str(calls)!r})\n"
        "calls.write_text(json.dumps({'argv': sys.argv[1:], 'stdin': sys.stdin.read()}))\n"
        "out = os.environ.get('AGENT_REVIEWER_RESPONSE_DIR')\n"
        "if out:\n"
        "    pathlib.Path(out).mkdir(parents=True, exist_ok=True)\n"
        "    pathlib.Path(out, 'last-message.md').write_text('Overall verdict: ready\\n')\n"
        "print('Overall verdict: ready')\n"
    )
    exe.chmod(0o755)
    return calls


def _env(tmp_path, provider):
    response_dir = tmp_path / "response"
    scratch_dir = tmp_path / "scratch"
    repo = tmp_path / "repo"
    target = repo / "plan.md"
    for p in (response_dir, scratch_dir, repo):
        p.mkdir(parents=True, exist_ok=True)
    target.write_text("# Plan\n")
    env = os.environ.copy()
    env.update({
        "PATH": f"{tmp_path}:{env['PATH']}",
        "AGENT_REVIEWER_PROVIDER": provider,
        "AGENT_REVIEWER_REPO_ROOT": str(repo),
        "AGENT_REVIEWER_RESPONSE_DIR": str(response_dir),
        "AGENT_REVIEWER_SCRATCH_DIR": str(scratch_dir),
        "AGENT_REVIEWER_TARGET_FILE": str(target),
    })
    return env


def test_codex_wrapper_uses_sandbox_and_never_bypass(tmp_path):
    calls = _fake_bin(tmp_path, "codex")
    env = _env(tmp_path, "codex")
    result = subprocess.run([str(WRAPPER)], input="review prompt", env=env, text=True, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr
    call = json.loads(calls.read_text())
    argv = call["argv"]
    assert argv[:1] == ["exec"]
    assert "--dangerously-bypass-approvals-and-sandbox" not in argv
    assert "--sandbox" in argv and "workspace-write" in argv
    assert "--ask-for-approval" in argv and "never" in argv
    assert "--ephemeral" in argv
    assert "--cd" in argv and env["AGENT_REVIEWER_SCRATCH_DIR"] in argv
    assert "--add-dir" in argv and env["AGENT_REVIEWER_RESPONSE_DIR"] in argv
    assert Path(env["AGENT_REVIEWER_SCRATCH_DIR"]).is_absolute()
    assert Path(env["AGENT_REVIEWER_RESPONSE_DIR"]).is_absolute()
    assert "--output-last-message" in argv
    assert "disk-full-read-access" in " ".join(argv)


def test_claude_wrapper_uses_print_and_plan_mode(tmp_path):
    calls = _fake_bin(tmp_path, "claude")
    env = _env(tmp_path, "claude")
    result = subprocess.run([str(WRAPPER)], input="review prompt", env=env, text=True, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr
    call = json.loads(calls.read_text())
    argv = call["argv"]
    assert "--print" in argv
    assert "--permission-mode" in argv and "plan" in argv
    assert "--dangerously-skip-permissions" not in argv
    assert "--add-dir" in argv
    assert env["AGENT_REVIEWER_REPO_ROOT"] in argv


def test_wrapper_fails_when_required_env_missing(tmp_path):
    _fake_bin(tmp_path, "codex")
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    env["AGENT_REVIEWER_PROVIDER"] = "codex"
    result = subprocess.run([str(WRAPPER)], input="x", env=env, text=True, capture_output=True, timeout=20)
    assert result.returncode == 2
    assert "AGENT_REVIEWER_REPO_ROOT" in result.stderr
```

- [ ] **Step 2: Run failing tests**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_reviewer_agent_wrapper.py -v
```

Expected: FAIL because `skills/project-setup/scripts/reviewer-agent` does not exist.

- [ ] **Step 3: Create the wrapper template**

Create `skills/project-setup/scripts/reviewer-agent`:

```bash
#!/usr/bin/env bash
set -euo pipefail

provider="${AGENT_REVIEWER_PROVIDER:-}"
if [[ -z "$provider" || "$provider" == "custom" ]]; then
  provider="codex"
fi

required=(
  AGENT_REVIEWER_REPO_ROOT
  AGENT_REVIEWER_RESPONSE_DIR
  AGENT_REVIEWER_SCRATCH_DIR
  AGENT_REVIEWER_TARGET_FILE
)

for key in "${required[@]}"; do
  if [[ -z "${!key:-}" ]]; then
    echo "reviewer-agent: missing required env var: $key" >&2
    exit 2
  fi
done

mkdir -p "$AGENT_REVIEWER_RESPONSE_DIR" "$AGENT_REVIEWER_SCRATCH_DIR"

case "$provider" in
  codex)
    output_file="$AGENT_REVIEWER_RESPONSE_DIR/last-message.md"
    codex exec \
      --sandbox workspace-write \
      --ask-for-approval never \
      --ephemeral \
      --cd "$AGENT_REVIEWER_SCRATCH_DIR" \
      --add-dir "$AGENT_REVIEWER_RESPONSE_DIR" \
      -c 'sandbox_permissions=["disk-full-read-access"]' \
      --output-last-message "$output_file" \
      -
    if [[ -s "$output_file" ]]; then
      cat "$output_file"
    fi
    ;;
  claude)
    claude --print \
      --permission-mode plan \
      --add-dir "$AGENT_REVIEWER_REPO_ROOT" \
      --add-dir "$AGENT_REVIEWER_RESPONSE_DIR"
    ;;
  *)
    echo "reviewer-agent: unknown AGENT_REVIEWER_PROVIDER: $provider" >&2
    exit 2
    ;;
esac
```

Make it executable:

```bash
chmod +x skills/project-setup/scripts/reviewer-agent
```

- [ ] **Step 4: Run wrapper tests**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_reviewer_agent_wrapper.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/project-setup/scripts/reviewer-agent \
        skills/external-review/tests/test_reviewer_agent_wrapper.py
git commit -m "project-setup: add safe reviewer-agent wrapper template"
```

### Task 4.2: Point project setup at the wrapper template

**Files:**
- Modify: `skills/project-setup/SKILL.md`

- [ ] **Step 1: Write the docs check command**

Run:

```bash
rg -n "dangerously-bypass|dangerously-skip|reviewer-agent|AGENT_REVIEWER_CMD" skills/project-setup/SKILL.md skills/project-setup/scripts/reviewer-agent
```

Expected before edits: `skills/project-setup/SKILL.md` still says to print wrapper install instructions but does not mention the new template or the no-bypass rule.

- [ ] **Step 2: Update check 8 in project setup**

In `skills/project-setup/SKILL.md`, change checklist row 8 scaffold action to:

```markdown
Print the exact command to install `skills/project-setup/scripts/reviewer-agent` to a user-chosen bin dir, or the exact `AGENT_REVIEWER_CMD` override. Do **not** install third-party tools or edit shell config without confirmation. The wrapper must not use provider bypass/no-sandbox flags.
```

Add this paragraph after the checklist:

```markdown
**Safe reviewer wrapper.** The bundled template at `skills/project-setup/scripts/reviewer-agent` is the default recommendation. It expects `external-reviewer.py` to pass `AGENT_REVIEWER_PROVIDER`, `AGENT_REVIEWER_REPO_ROOT`, `AGENT_REVIEWER_RESPONSE_DIR`, `AGENT_REVIEWER_SCRATCH_DIR`, and `AGENT_REVIEWER_TARGET_FILE`. Do not recommend wrappers that call Codex with `--dangerously-bypass-approvals-and-sandbox` or Claude with `--dangerously-skip-permissions`.
```

- [ ] **Step 3: Verify wording**

Run:

```bash
rg -n "dangerously-bypass|dangerously-skip|Safe reviewer wrapper|scripts/reviewer-agent" skills/project-setup/SKILL.md
```

Expected: the only dangerous-flag mentions are in the prohibition sentence.

- [ ] **Step 4: Commit**

```bash
git add skills/project-setup/SKILL.md
git commit -m "project-setup: document safe reviewer wrapper"
```

### Task 4.3: Replace the local installed wrapper after fake tests pass

**Files:**
- Replace local file: `~/.local/bin/reviewer-agent`

- [ ] **Step 1: Re-run the fake wrapper tests immediately before replacement**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_reviewer_agent_wrapper.py -v
```

Expected: PASS.

- [ ] **Step 2: Back up the current unsafe wrapper**

Run:

```bash
mkdir -p ~/.local/bin/reviewer-agent-backups
cp ~/.local/bin/reviewer-agent ~/.local/bin/reviewer-agent-backups/reviewer-agent.$(date +%Y%m%dT%H%M%S)
```

Expected: commands exit 0.

- [ ] **Step 3: Install the safe wrapper**

Run:

```bash
install -m 0755 skills/project-setup/scripts/reviewer-agent ~/.local/bin/reviewer-agent
```

Expected: command exits 0.

- [ ] **Step 4: Verify the installed wrapper no longer contains bypass flags**

Run:

```bash
rg -n "dangerously-bypass|dangerously-skip" ~/.local/bin/reviewer-agent || true
```

Expected: no output.

---

## Slice 5 - External Review Docs

### Task 5.1: Document provider flipping and sandbox contract

**Files:**
- Modify: `skills/external-review/SKILL.md`

- [ ] **Step 1: Inspect current configuration section**

Run:

```bash
sed -n '30,80p' skills/external-review/SKILL.md
```

Expected: section says default command is `reviewer-agent` and describes only `AGENT_REVIEWER_CMD` / `--reviewer-cmd`.

- [ ] **Step 2: Replace the configuration section content**

In `skills/external-review/SKILL.md`, under `## Configuration`, replace the first paragraph and bullet list with:

```markdown
By default the bridge chooses the opposite reviewer provider from the caller:

| Caller | Default reviewer |
|---|---|
| Claude | Codex |
| Codex | Claude |

Provider selection is controlled by `--reviewer-provider auto|codex|claude|custom` or `AGENT_REVIEWER_PROVIDER`. Caller detection is controlled by `--caller-provider auto|claude|codex|unknown` or `AGENT_REVIEWER_CALLER`. If both are `auto` and the caller cannot be detected, the bridge fails closed and asks for an explicit provider or command.

The reviewer command is still overrideable via `AGENT_REVIEWER_CMD` or `--reviewer-cmd`. Any explicit reviewer command is treated as `custom` and bypasses provider auto-selection. Custom wrappers are responsible for their own sandboxing.

The default command remains `reviewer-agent`. The safe wrapper contract is:

- reviewed repo is readable but not writable;
- `AGENT_REVIEWER_SCRATCH_DIR` is writable and short-lived;
- `AGENT_REVIEWER_RESPONSE_DIR` is writable for final-message handoff;
- wrappers must not use Codex `--dangerously-bypass-approvals-and-sandbox` or Claude `--dangerously-skip-permissions` unless the operator has supplied an external OS sandbox and chosen a custom command.
- Codex currently uses `disk-full-read-access`, which may expose files outside the repo for reading. This fork accepts that read-side risk to keep the write-side mitigation simple.

The command may be:

- A bare executable (`reviewer-agent`) — the prompt is supplied per `--prompt-transport` (`arg` | `file` | `stdin`, default `arg`).
- A template with placeholders (`{prompt_file}`, `{prompt_text}`, `{target_file}`, `{kind}`, `{chain_dir}`, `{round}`, `{previous_response}`, `{resolution_file}`, `{session_file}`, `{repo_root}`, `{response_dir}`, `{scratch_dir}`, `{request_file}`) — substituted and run through the shell. Env vars are authoritative; placeholders are derived convenience values.

The bridge exports `AGENT_REVIEWER_REPO_ROOT`, `AGENT_REVIEWER_CHAIN_DIR`, `AGENT_REVIEWER_REQUEST_FILE`, `AGENT_REVIEWER_RESPONSE_DIR`, `AGENT_REVIEWER_SCRATCH_DIR`, `AGENT_REVIEWER_TARGET_FILE`, `AGENT_REVIEWER_KIND`, `AGENT_REVIEWER_ROLE`, and `AGENT_REVIEWER_SWEEP_INDEX` for every reviewer process. `AGENT_REVIEWER_SWEEP_INDEX` is always set: empty for primary, numeric for sweeps. These env vars are authoritative; command placeholders are convenience sugar derived from the same values.

Scratch directories are owner-only and normally removed by the bridge. If a process is killed before cleanup, remove stale dirs with:

```bash
find "${TMPDIR:-/tmp}" -maxdepth 1 -type d -name 'superstar-reviewer-*' -mtime +1 -prune -exec rm -rf -- {} +
```
```

- [ ] **Step 3: Add safety note near review-depth sweeps**

In the `## Review depth` section, append:

```markdown
Each primary/sweep reviewer receives its own `AGENT_REVIEWER_RESPONSE_DIR` and `AGENT_REVIEWER_SCRATCH_DIR`, so parallel reviewer roles cannot overwrite one another's scratch/output files.
```

- [ ] **Step 4: Verify docs mention all new flags/env**

Run:

```bash
rg -n "reviewer-provider|caller-provider|AGENT_REVIEWER_PROVIDER|AGENT_REVIEWER_CALLER|AGENT_REVIEWER_SCRATCH_DIR|AGENT_REVIEWER_RESPONSE_DIR|AGENT_REVIEWER_SWEEP_INDEX|superstar-reviewer-\\*|dangerously-bypass" skills/external-review/SKILL.md
```

Expected: all terms are present; dangerous flag appears only as a prohibition.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/SKILL.md
git commit -m "external-review: document provider sandboxing"
```

---

## Slice 6 - Final Verification And Safety Smoke

### Task 6.1: Run focused and full tests

**Files:** none expected.

- [ ] **Step 1: Run focused external-review tests**

Run:

```bash
python3 -m pytest \
  skills/external-review/tests/test_provider_selection.py \
  skills/external-review/tests/test_reviewer_invocation_context.py \
  skills/external-review/tests/test_reviewer_sandbox_metadata.py \
  skills/external-review/tests/test_reviewer_agent_wrapper.py \
  -v
```

Expected: PASS.

- [ ] **Step 2: Run full external-review test suite**

Run:

```bash
python3 -m pytest skills/external-review/tests -v
```

Expected: PASS. If unrelated pre-existing tests fail, stop and record exact failures before deciding whether they are in scope.

- [ ] **Step 3: Run recent rate-limit/status regression tests explicitly**

Run:

```bash
python3 -m pytest \
  skills/external-review/tests/test_rate_limited_status_semantics.py \
  skills/external-review/tests/test_rate_limit_detection.py \
  skills/external-review/tests/test_exit_code_8.py \
  skills/external-review/tests/test_sweep_partial_rate_limit.py \
  skills/external-review/tests/test_heading_style_verdict.py \
  -v
```

Expected: PASS.

- [ ] **Step 4: Commit any test-only fixes**

Only if Step 1, Step 2, or Step 3 required fixes:

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests \
        skills/project-setup/scripts/reviewer-agent \
        skills/project-setup/SKILL.md \
        skills/external-review/SKILL.md
git commit -m "external-reviewer: stabilize provider sandbox tests"
```

### Task 6.2: Live Codex sandbox smoke test

**Files:** none expected unless a safety bug is found.

- [ ] **Step 1: Create a disposable repo**

Run:

```bash
tmp="$(mktemp -d)"
repo="$tmp/repo"
fake_home="$tmp/home"
mkdir -p "$repo" "$fake_home/.config"
git -C "$repo" init -q
git -C "$repo" config user.email t@example.com
git -C "$repo" config user.name Test
printf '# Plan\n' > "$repo/plan.md"
git -C "$repo" add .
git -C "$repo" commit -q -m init
```

Expected: commands exit 0.

- [ ] **Step 2: Run a direct wrapper smoke with Codex**

Run:

```bash
export AGENT_REVIEWER_PROVIDER=codex
export AGENT_REVIEWER_REPO_ROOT="$repo"
export AGENT_REVIEWER_RESPONSE_DIR="$tmp/response"
export AGENT_REVIEWER_SCRATCH_DIR="$tmp/scratch"
export AGENT_REVIEWER_TARGET_FILE="$repo/plan.md"
HOME="$fake_home" skills/project-setup/scripts/reviewer-agent <<'PROMPT'
You are a sandbox smoke tester. Try these exact shell commands and then report which succeeded:
1. `printf repo-write > "$AGENT_REVIEWER_REPO_ROOT/should-not-write.txt"`
2. `printf home-write > "$HOME/.config/should-not-write.txt"`
3. `printf scratch-write > "$AGENT_REVIEWER_SCRATCH_DIR/ok.txt"`
4. `printf response-write > "$AGENT_REVIEWER_RESPONSE_DIR/ok.txt"`

Expected final verdict text must include "Overall verdict: ready".
PROMPT
```

Expected:

- wrapper exits 0;
- final output contains `Overall verdict: ready`;
- Codex reports repo/home writes failed and scratch/response writes succeeded.

- [ ] **Step 3: Verify filesystem effects**

Run:

```bash
test ! -e "$repo/should-not-write.txt"
test ! -e "$fake_home/.config/should-not-write.txt"
test -e "$tmp/scratch/ok.txt"
test -e "$tmp/response/ok.txt" || test -e "$tmp/response/last-message.md"
```

Expected: all commands exit 0.

- [ ] **Step 4: Clean up**

Run:

```bash
rm -rf "$tmp"
unset AGENT_REVIEWER_PROVIDER AGENT_REVIEWER_REPO_ROOT AGENT_REVIEWER_RESPONSE_DIR AGENT_REVIEWER_SCRATCH_DIR AGENT_REVIEWER_TARGET_FILE
```

Expected: commands exit 0.

### Task 6.3: Live Claude wrapper smoke test

**Files:** none expected unless a safety bug is found.

- [ ] **Step 1: Run the Claude branch with a disposable repo**

Run:

```bash
tmp="$(mktemp -d)"
repo="$tmp/repo"
fake_home="$tmp/home"
mkdir -p "$repo" "$tmp/response" "$tmp/scratch" "$fake_home/.config"
git -C "$repo" init -q
git -C "$repo" config user.email t@example.com
git -C "$repo" config user.name Test
printf '# Plan\n' > "$repo/plan.md"
git -C "$repo" add .
git -C "$repo" commit -q -m init
export AGENT_REVIEWER_PROVIDER=claude
export AGENT_REVIEWER_REPO_ROOT="$repo"
export AGENT_REVIEWER_RESPONSE_DIR="$tmp/response"
export AGENT_REVIEWER_SCRATCH_DIR="$tmp/scratch"
export AGENT_REVIEWER_TARGET_FILE="$repo/plan.md"
HOME="$fake_home" skills/project-setup/scripts/reviewer-agent <<'PROMPT'
Read plan.md and report a minimal review. Attempt these shell writes first if tools are available, then report whether they succeeded:
1. `printf repo-write > "$AGENT_REVIEWER_REPO_ROOT/should-not-write.txt"`
2. `printf home-write > "$HOME/.config/should-not-write.txt"`
Do not edit files through edit tools. End with:
Overall verdict: ready
PROMPT
```

Expected: wrapper exits 0 and output contains `Overall verdict: ready`. The reported shell writes must fail or be denied.

- [ ] **Step 2: Verify no repo or home writes**

Run:

```bash
git -C "$repo" status --short
test ! -e "$repo/should-not-write.txt"
test ! -e "$fake_home/.config/should-not-write.txt"
rm -rf "$tmp"
unset AGENT_REVIEWER_PROVIDER AGENT_REVIEWER_REPO_ROOT AGENT_REVIEWER_RESPONSE_DIR AGENT_REVIEWER_SCRATCH_DIR AGENT_REVIEWER_TARGET_FILE
```

Expected: `git status --short` prints no tracked or untracked repo changes; both `test ! -e ...` commands exit 0.

### Task 6.4: Final closeout commit

**Files:** none expected.

- [ ] **Step 1: Check worktree**

Run:

```bash
git status --short
```

Expected: clean, except for known unrelated user changes that predated this plan.

- [ ] **Step 2: Commit any final documentation/test correction**

Only if Task 6 discovered and fixed issues:

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests \
        skills/project-setup/scripts/reviewer-agent \
        skills/project-setup/SKILL.md \
        skills/external-review/SKILL.md
git commit -m "external-reviewer: finalize provider sandboxing"
```

---

## Self-Review Checklist

- [x] Provider flip from Claude to Codex and Codex to Claude is covered by Task 1.1.
- [x] Unknown caller fail-closed behavior is covered by Task 1.1.
- [x] Custom `AGENT_REVIEWER_CMD` compatibility is covered by Task 1.1 and bridge tests.
- [x] Scratch/output path env vars are covered by Task 2.1.
- [x] Scratch cleanup avoids shell env-variable cleanup and is covered by Task 2.2.
- [x] Scratch directory privacy is covered by Task 2.2.
- [x] Env-var authority and sweep index semantics are covered by Task 2.4.
- [x] New command placeholders are covered by Task 2.3.
- [x] Manifest/artifact visibility is covered by Task 3.1.
- [x] Wrapper no-bypass behavior is covered by Task 4.1.
- [x] Prompt replacement of the installed dangerous wrapper is covered by Task 4.3.
- [x] Docs/project setup updates are covered by Tasks 2.4, 4.2, and 5.1.
- [x] Live Codex and Claude smoke tests are covered by Tasks 6.2 and 6.3.

## Execution Handoff

Implement this plan with `superstar:subagent-driven-development` unless the user explicitly asks for inline execution. Recommended slice ownership:

- Slice 1: provider resolution and argparse.
- Slice 2: invocation context and placeholders.
- Slice 3: metadata.
- Slice 4: wrapper template and wrapper tests.
- Slice 5: docs.
- Slice 6: verification and live smoke tests.
