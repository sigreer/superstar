# external-reviewer context optimisation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate the recursive prompt-echo loop in external-reviewer chains and bound incremental-round prompt size, while preserving the JSON output contract and exit codes.

**Architecture:** Three slices: (S1) make failure truthful — failed reviewer turns can never produce a fake verdict, prompt echoes never reach disk, preambles walk past failed rounds; (S2) put incremental-mode prompts on a diet — drop context previews, trim target preview, cap prior-text reads, add a single budget knob with deterministic preservation priority; (S3) update `skills/external-review/SKILL.md` with the new behaviour. All changes target a single file (`skills/external-review/scripts/external-reviewer.py`) and its test suite (`skills/external-review/tests/`).

**Tech Stack:** Python 3 standard library only (no new deps). Test framework: pytest. Module loaded via importlib because the script has a hyphen in its filename.

**Source spec:** `docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md` (status: `ready`).

**Spec → Plan mapping for the test items.** The spec's S3 lists 15 tests plus a docs item; this plan pairs each test with its implementation under TDD discipline. The mapping is:

| Spec S3 item | Plan task |
|---|---|
| 1. failed-process verdict suppression | Task 1.5 |
| 2. failed sweep can't poison merged findings | Task 1.6 |
| 3. sentinel-stripping happy path | Task 1.1 |
| 4. sentinel-stripping truncated echo | Task 1.1 |
| 5. success-stderr dropped or capped | Task 1.3 |
| 6. failed-stderr cap after sentinel-stripping | Task 1.4 |
| 7. preamble walks back past failed rounds | Task 1.10 |
| 8. preamble treats `status: "unknown"` as untrusted | Task 1.10 |
| 9. process-failed prior round bypasses resolution gate | Task 1.11 |
| 10. incremental drops context previews | Task 2.1 |
| 11. target preview trimmed on incremental | Task 2.2 |
| 12. prior-text caps applied | Task 2.3 |
| 13. budget cap preserves priority order | Task 2.4 |
| 14. r3-request bounded after simulated failed r2 | Task 1.12 |
| 15. chain.json soft-migration | Task 1.9 |
| 16. SKILL.md docs update | Task 3.1 |

---

## Files at a glance

- **Modified:** `skills/external-review/scripts/external-reviewer.py` — all code changes live here.
- **Modified:** `skills/external-review/SKILL.md` — docs update in S3.
- **Created (tests):** `skills/external-review/tests/test_sentinel_stripper.py`, `test_response_artifact.py`, `test_failed_round_truth.py`, `test_merged_findings_skips_failed.py`, `test_returncode_status_persisted.py`, `test_preamble_skips_failed.py`, `test_resolution_gate_bypass.py`, `test_failed_r2_bounded_r3.py`, `test_chain_soft_migration.py`, `test_incremental_drops_context.py`, `test_target_preview_trim.py`, `test_prior_text_caps.py`, `test_incremental_budget.py`, `test_diff_caps.py`.
- **Untouched:** every other file in the repo.

## Test-file boilerplate

Every new test file in this plan starts with the same import block as the existing tests in `skills/external-review/tests/`:

```python
from pathlib import Path
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)
```

Reference: `skills/external-review/tests/test_manifest.py:1-13`. Re-paste this block at the top of every new test file in the steps below — do not abbreviate it.

## Conventions used throughout the plan

- All file paths are relative to the repo root `/home/simon/Dev/sigreer/skills/superstar/`.
- All `python3 -m pytest` invocations should be run from the repo root.
- Each task ends in a commit. Commit messages follow `<scope>: <change>`; `<scope>` is `external-reviewer`.
- Line-number anchors (e.g. `external-reviewer.py:451`) reflect the script *before* this plan's edits. As the plan proceeds, line numbers will drift; the surrounding context strings in each step's `Edit` blocks are what makes the edit unambiguous, not the anchors.

---

## Slice 1 — Failure-truth + echo containment

This is the keystone slice. Without it, any size optimisation only delays the corruption. Do not begin Slice 2 until every task in Slice 1 is committed and the test suite is green.

### Task 1.1: Sentinel stripper

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (add module-level constants near the top, add helper near `parse_verdict`)
- Create: `skills/external-review/tests/test_sentinel_stripper.py`

- [x] **Step 1: Write the failing tests**

Create `skills/external-review/tests/test_sentinel_stripper.py`:

```python
from pathlib import Path
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def test_strip_removes_full_marker_block():
    text = (
        "preamble\n"
        f"{er.PROMPT_SENTINEL_START}\nechoed prompt body\n{er.PROMPT_SENTINEL_END}\n"
        "actual review\n"
    )
    out = er.strip_prompt_echo(text)
    assert "echoed prompt body" not in out
    assert er.PROMPT_SENTINEL_START not in out
    assert er.PROMPT_SENTINEL_END not in out
    assert "preamble" in out
    assert "actual review" in out


def test_strip_end_only_deletes_from_start_of_stream():
    text = f"truncated echo tail here\n{er.PROMPT_SENTINEL_END}\nactual review\n"
    out = er.strip_prompt_echo(text)
    assert "truncated echo tail here" not in out
    assert er.PROMPT_SENTINEL_END not in out
    assert out.strip().startswith("actual review")


def test_strip_start_only_deletes_to_end_of_stream():
    text = f"preamble\n{er.PROMPT_SENTINEL_START}\nprompt body leaks to end\n"
    out = er.strip_prompt_echo(text)
    assert "prompt body leaks to end" not in out
    assert er.PROMPT_SENTINEL_START not in out
    assert out.strip() == "preamble"


def test_strip_no_markers_passes_text_through():
    text = "a clean review with no echo at all"
    assert er.strip_prompt_echo(text) == text


def test_strip_handles_empty_string():
    assert er.strip_prompt_echo("") == ""


def test_strip_handles_multiple_blocks():
    text = (
        f"head\n{er.PROMPT_SENTINEL_START}\nblock1\n{er.PROMPT_SENTINEL_END}\n"
        f"middle\n{er.PROMPT_SENTINEL_START}\nblock2\n{er.PROMPT_SENTINEL_END}\n"
        "tail"
    )
    out = er.strip_prompt_echo(text)
    assert "block1" not in out
    assert "block2" not in out
    assert "head" in out and "middle" in out and "tail" in out
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest skills/external-review/tests/test_sentinel_stripper.py -v`
Expected: all six tests fail with `AttributeError: module 'external_reviewer' has no attribute 'PROMPT_SENTINEL_START'`.

- [x] **Step 3: Add constants and helper to the script**

In `skills/external-review/scripts/external-reviewer.py`, immediately before the line `SUPPORTED_SCHEMA_VERSION = 1`, insert:

```python
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
```

- [x] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest skills/external-review/tests/test_sentinel_stripper.py -v`
Expected: all six tests pass.

- [x] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_sentinel_stripper.py
git commit -m "external-reviewer: add prompt-echo sentinel stripper"
```

### Task 1.2: Wire sentinel markers into make_prompt

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`make_prompt`, around lines 328-354)

- [x] **Step 1: Write the failing test**

Append to `skills/external-review/tests/test_sentinel_stripper.py`:

```python
def test_make_prompt_wraps_body_in_sentinels(tmp_path, monkeypatch):
    root = tmp_path
    target = root / "plan.md"
    target.write_text("# plan\nbody\n")
    monkeypatch.chdir(root)
    out = er.make_prompt(
        root=root, target=target, kind="plan",
        context=[], max_lines=10, mode="broad", incremental_preamble=None,
    )
    assert out.startswith(er.PROMPT_SENTINEL_START)
    assert out.rstrip().endswith(er.PROMPT_SENTINEL_END)
    # Round-trip: stripping should remove the entire prompt.
    assert er.strip_prompt_echo(out).strip() == ""
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest skills/external-review/tests/test_sentinel_stripper.py::test_make_prompt_wraps_body_in_sentinels -v`
Expected: AssertionError — the prompt does not start with the sentinel.

- [x] **Step 3: Wrap the prompt body**

In `skills/external-review/scripts/external-reviewer.py`, edit `make_prompt`. Find:

```python
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

Replace with:

```python
    if mode == "incremental" and incremental_preamble:
        body = incremental_preamble + "\n---\n\n" + body
    body += "\n\n## Target Preview\n\n"
    body += numbered_preview(target, root, max_lines=max_lines)
    if context:
        body += "\n## Context Previews\n\n"
        for ctx in context:
            body += numbered_preview(ctx, root, max_lines=max(80, max_lines // 3))
    return f"{PROMPT_SENTINEL_START}\n{body}\n{PROMPT_SENTINEL_END}"
```

- [x] **Step 4: Run the full test suite**

Run: `python3 -m pytest skills/external-review/tests/ -v`
Expected: the new test passes. Other tests may break if they inspect the raw prompt body — fix any breakages by stripping the markers in the assertion (using `er.strip_prompt_echo`) before comparing. Common likely failure: `test_incremental_prompt.py` and `test_prompt_contract.py`.

If a pre-existing test breaks because it asserts the prompt starts with something other than the sentinel, change that assertion to: `assert er.strip_prompt_echo(out).startswith(...)`. Do not weaken the assertion in any other way.

- [x] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_sentinel_stripper.py \
        skills/external-review/tests/test_incremental_prompt.py \
        skills/external-review/tests/test_prompt_contract.py
git commit -m "external-reviewer: wrap make_prompt body in echo-strip sentinels"
```

(Only stage test files that you actually had to change in Step 4. Do not stage files you did not touch.)

### Task 1.3: write_review_artifact — success path drops/caps stderr

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`write_review_artifact`, around lines 440-473)
- Create: `skills/external-review/tests/test_response_artifact.py`

- [x] **Step 1: Write the failing test**

Create `skills/external-review/tests/test_response_artifact.py`:

```python
from pathlib import Path
import subprocess
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def _fake_result(returncode: int, stdout: str, stderr: str):
    return subprocess.CompletedProcess(
        args=["fake"], returncode=returncode, stdout=stdout, stderr=stderr,
    )


def test_success_stderr_with_full_prompt_echo_does_not_persist_prompt(tmp_path):
    """Success path: stderr containing the entire echoed prompt must not be written."""
    prompt_text = f"{er.PROMPT_SENTINEL_START}\n" + ("X" * 50_000) + f"\n{er.PROMPT_SENTINEL_END}"
    result = _fake_result(
        returncode=0,
        stdout="# Review\nactual review body\nOverall verdict: ready",
        stderr=f"banner line\n{prompt_text}\nmore banner",
    )
    response_path = tmp_path / "r1-response.md"
    prompt_path = tmp_path / "r1-request.md"
    prompt_path.write_text("ignored")
    target = tmp_path / "plan.md"
    target.write_text("ignored")
    er.write_review_artifact(
        root=tmp_path, target=target, kind="plan",
        command_template="fake", prompt_file=prompt_path,
        response_file=response_path, round_num=1, result=result,
    )
    body = response_path.read_text()
    assert er.PROMPT_SENTINEL_START not in body
    assert er.PROMPT_SENTINEL_END not in body
    assert "X" * 1000 not in body  # the 50 KB of echoed payload must not appear
    assert "actual review body" in body
    assert response_path.stat().st_size < 8 * 1024  # under 8 KB


def test_success_with_short_clean_stderr_keeps_tail_capped(tmp_path):
    """Success path: short stderr (no echo) may be retained but capped to 2 KB."""
    result = _fake_result(
        returncode=0,
        stdout="# Review\nbody\nOverall verdict: ready",
        stderr="harmless banner\nsession info\n",
    )
    response_path = tmp_path / "r1-response.md"
    prompt_path = tmp_path / "r1-request.md"
    prompt_path.write_text("ignored")
    target = tmp_path / "plan.md"
    target.write_text("ignored")
    er.write_review_artifact(
        root=tmp_path, target=target, kind="plan",
        command_template="fake", prompt_file=prompt_path,
        response_file=response_path, round_num=1, result=result,
    )
    body = response_path.read_text()
    assert "body" in body
    # The stderr-tail section, if present, must not exceed 2 KB
    if "## Reviewer stderr (tail)" in body:
        tail = body.split("## Reviewer stderr (tail)", 1)[1]
        assert len(tail) <= 2 * 1024 + 200  # 200 bytes of fenced-block scaffolding
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest skills/external-review/tests/test_response_artifact.py -v`
Expected: `test_success_stderr_with_full_prompt_echo_does_not_persist_prompt` fails (the full stderr currently leaks); the short-clean test may pass or fail depending on current behaviour.

- [x] **Step 3: Implement the success path**

In `skills/external-review/scripts/external-reviewer.py`, replace the body of `write_review_artifact` (currently lines ~440-473):

```python
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
```

- [x] **Step 4: Run tests to verify success path passes**

Run: `python3 -m pytest skills/external-review/tests/test_response_artifact.py -v`
Expected: both tests pass. Run the full suite once: `python3 -m pytest skills/external-review/tests/`. Other tests may break if they parse the response body assuming the old format. Fix any breakages by updating the assertion to look for the new headings (`## Reviewer stderr (tail)`).

- [x] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_response_artifact.py
git commit -m "external-reviewer: drop/cap success stderr after sentinel strip"
```

### Task 1.4: write_review_artifact — failed path, 4 KB stderr tail, no stdout

The previous task already wrote the failed-path branch. This task adds the dedicated test for "strip-before-cap ordering with 20 KB echo input."

**Files:**
- Modify: `skills/external-review/tests/test_response_artifact.py`

- [x] **Step 1: Append the failing test**

Append to `skills/external-review/tests/test_response_artifact.py`:

```python
def test_failed_stderr_strip_then_cap_ordering(tmp_path):
    """Failed path: 20 KB of echoed prompt on stderr → tail ≤ 4 KB and no markers leak."""
    huge_echo = f"{er.PROMPT_SENTINEL_START}\n" + ("Y" * 20_000) + f"\n{er.PROMPT_SENTINEL_END}"
    result = _fake_result(
        returncode=1, stdout="",
        stderr=f"banner\n{huge_echo}\nerror: turn/start failed",
    )
    response_path = tmp_path / "r2-response.md"
    prompt_path = tmp_path / "r2-request.md"
    prompt_path.write_text("ignored")
    target = tmp_path / "plan.md"
    target.write_text("ignored")
    er.write_review_artifact(
        root=tmp_path, target=target, kind="plan",
        command_template="fake", prompt_file=prompt_path,
        response_file=response_path, round_num=2, result=result,
    )
    body = response_path.read_text()
    assert er.PROMPT_SENTINEL_START not in body
    assert er.PROMPT_SENTINEL_END not in body
    assert "Y" * 1000 not in body
    # Total file ≤ 8 KB (headers + ≤ 4 KB tail)
    assert response_path.stat().st_size < 8 * 1024
    # Diagnostic substring survives the tail cap
    assert "error: turn/start failed" in body


def test_failed_path_does_not_persist_stdout(tmp_path):
    """Failed path: stdout (if any) is dropped — only stderr tail is persisted."""
    result = _fake_result(
        returncode=1,
        stdout="this should not appear",
        stderr="short stderr",
    )
    response_path = tmp_path / "r1-response.md"
    prompt_path = tmp_path / "r1-request.md"
    prompt_path.write_text("ignored")
    target = tmp_path / "plan.md"
    target.write_text("ignored")
    er.write_review_artifact(
        root=tmp_path, target=target, kind="plan",
        command_template="fake", prompt_file=prompt_path,
        response_file=response_path, round_num=1, result=result,
    )
    body = response_path.read_text()
    assert "this should not appear" not in body
    assert "short stderr" in body
```

- [x] **Step 2: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_response_artifact.py -v`
Expected: both new tests pass (implementation was already done in Task 1.3).

- [x] **Step 3: Commit**

```bash
git add skills/external-review/tests/test_response_artifact.py
git commit -m "external-reviewer: test strip-before-cap and stdout-drop on failed turns"
```

### Task 1.5: Failed reviewers force verdict=None / verdict_valid=False

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`run_one_reviewer`, around line 542)
- Create: `skills/external-review/tests/test_failed_round_truth.py`

- [x] **Step 1: Write the failing test**

Create `skills/external-review/tests/test_failed_round_truth.py`:

```python
from pathlib import Path
import os
import subprocess
import sys
import json
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


FAKE_FAILED_WITH_ECHOED_VERDICT = """#!/usr/bin/env bash
# Echo a prompt-looking blob on stderr that contains plausible verdict text,
# then exit non-zero. This is the multistore failure mode.
cat 1>&2 <<'EOF'
Reading prompt from stdin...
OpenAI Codex v0.130.0
user
You are continuing an existing review chain.
... (echoed) ...
Overall verdict: revise
EOF
exit 1
"""


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    return repo


def test_failed_reviewer_with_echoed_verdict_is_not_trusted(tmp_path):
    repo = _init_repo(tmp_path)
    reviewer = repo / "fake.sh"
    reviewer.write_text(FAKE_FAILED_WITH_ECHOED_VERDICT)
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    # Process should exit with the reviewer's non-zero code, not 0.
    assert result.returncode != 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["verdict_valid"] is False
    assert payload["verdict"] is None
    assert payload["status"] == "failed"
    assert payload["returncode"] != 0
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest skills/external-review/tests/test_failed_round_truth.py -v`
Expected: failure. Today, the script parses the echoed `Overall verdict: revise` and records `verdict_valid: True`.

- [x] **Step 3: Force the verdict in `run_one_reviewer`**

In `skills/external-review/scripts/external-reviewer.py`, find the end of `run_one_reviewer` where the `ReviewerResult` is constructed (around line 542-549):

```python
    body = response_path.read_text(encoding="utf-8")
    verdict, valid = parse_verdict(body)
    return ReviewerResult(
        role=role,
        sweep_index=sweep_index,
        request_path=request_path,
        response_path=response_path,
        review_body=body,
        verdict=verdict,
        verdict_valid=valid,
        returncode=result.returncode,
    )
```

Replace with:

```python
    body = response_path.read_text(encoding="utf-8")
    if result.returncode != 0:
        # Process failures cannot produce a valid verdict, regardless of what
        # parse_verdict extracts from echoed prompt text. See spec §S1.2.
        verdict, valid = None, False
    else:
        verdict, valid = parse_verdict(body)
    return ReviewerResult(
        role=role,
        sweep_index=sweep_index,
        request_path=request_path,
        response_path=response_path,
        review_body=body,
        verdict=verdict,
        verdict_valid=valid,
        returncode=result.returncode,
    )
```

- [x] **Step 4: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_failed_round_truth.py -v`
Expected: the new test passes. The reviewer process exit is reflected in the top-level JSON correctly (see Task 1.8 for full persistence). Some part of the test may still fail if `status`/`returncode` are not yet in the top-level payload — if so, mark it `xfail` with reason `pending Task 1.8` and proceed; remove the xfail after Task 1.8.

- [x] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_failed_round_truth.py
git commit -m "external-reviewer: failed turn forces verdict=None/valid=False"
```

### Task 1.6: write_merged_findings skips failed reviewers

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`write_merged_findings`, around line 567; caller at line ~1055)
- Create: `skills/external-review/tests/test_merged_findings_skips_failed.py`

- [x] **Step 1: Write the failing test**

Create `skills/external-review/tests/test_merged_findings_skips_failed.py`:

```python
from pathlib import Path
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def _r(role, idx, body, returncode):
    return er.ReviewerResult(
        role=role, sweep_index=idx,
        request_path=Path("/tmp/req"), response_path=Path("/tmp/resp"),
        review_body=body,
        verdict="revise" if returncode == 0 else None,
        verdict_valid=(returncode == 0),
        returncode=returncode,
    )


def test_failed_sweep_excluded_from_merged_findings(tmp_path):
    primary = _r("primary", None, "## F1\nSeverity: blocking\nReal primary finding.\n", 0)
    bad_sweep = _r("sweep", 1, "ECHOED PROMPT TEXT WITH FAKE VERDICT", 1)
    path = er.write_merged_findings(
        chain_dir=tmp_path, round_num=1, primary=primary, sweeps=[bad_sweep],
    )
    content = path.read_text()
    assert "Real primary finding" in content
    assert "ECHOED PROMPT TEXT" not in content
    # The "## Sweep 1" heading should not appear because the sweep was failed.
    assert "## Sweep 1" not in content


def test_all_failed_writes_no_merged_findings(tmp_path):
    primary = _r("primary", None, "bad", 1)
    sweep = _r("sweep", 1, "bad", 1)
    path = er.write_merged_findings(
        chain_dir=tmp_path, round_num=1, primary=primary, sweeps=[sweep],
    )
    assert path is None
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest skills/external-review/tests/test_merged_findings_skips_failed.py -v`
Expected: failure — current `write_merged_findings` concatenates all reviewer bodies unconditionally.

- [x] **Step 3: Update write_merged_findings**

In `skills/external-review/scripts/external-reviewer.py`, replace `write_merged_findings`:

```python
def write_merged_findings(
    *,
    chain_dir: Path, round_num: int,
    primary: "ReviewerResult", sweeps: list,
) -> Path | None:
    """Concatenate successful reviewer bodies into a merged-findings artifact.

    Reviewers with non-zero returncode are excluded entirely — their bodies
    are stderr tails / failure stubs and would poison downstream parsing.
    If every reviewer in the round failed, return None and write no file.
    """
    ok_reviewers = [r for r in [primary, *sweeps] if r.returncode == 0]
    if not ok_reviewers:
        return None
    parts = [f"# Merged findings for r{round_num}\n"]
    primary_ok = next((r for r in ok_reviewers if r.role == "primary"), None)
    if primary_ok is not None:
        parts += ["## Primary\n", primary_ok.review_body, ""]
    for s in ok_reviewers:
        if s.role == "sweep":
            parts += [
                f"## Sweep {s.sweep_index}\n",
                _renamespace_finding_ids(s.review_body, s.sweep_index),
                "",
            ]
    path = chain_dir / f"r{round_num}-merged-findings.md"
    path.write_text("\n".join(parts), encoding="utf-8")
    return path
```

- [x] **Step 4: Update the caller to handle None merged_path**

In `skills/external-review/scripts/external-reviewer.py`, find (around line 1054-1064):

```python
    if sweeps:
        merged_path = write_merged_findings(
            chain_dir=chain_dir, round_num=round_num,
            primary=primary, sweeps=sweeps,
        )
        merged_verdict = compute_merged_verdict(reviewer_results)
        if sweep_plan.checkpoint:
            manifest["sweep_checkpoints"][sweep_plan.checkpoint] = "completed"
    else:
        merged_path = None
        merged_verdict = primary.verdict
```

Replace with:

```python
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
```

- [x] **Step 5: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_merged_findings_skips_failed.py skills/external-review/tests/test_sweep_dispatch.py -v`
Expected: new tests pass; existing sweep-dispatch tests still pass.

- [x] **Step 6: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_merged_findings_skips_failed.py
git commit -m "external-reviewer: exclude failed reviewers from merged findings"
```

### Task 1.7: Multi-reviewer truth table in aggregation

Implement spec §S1.7: primary failure flips top-level status; sweep failure is per-reviewer only. The current `compute_merged_verdict` already returns `revise` if any reviewer has `verdict_valid=False`, which under the new rules (failed → `verdict_valid=False`) would falsely flip the merged verdict to `revise` when a sweep fails but primary succeeded. Fix: ignore failed reviewers in `compute_merged_verdict`.

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`compute_merged_verdict`, around line 552)
- Modify: `skills/external-review/tests/test_merged_findings_skips_failed.py`

- [x] **Step 1: Append the failing test**

Append to `skills/external-review/tests/test_merged_findings_skips_failed.py`:

```python
def test_merged_verdict_ignores_failed_reviewers():
    ok_primary = _r("primary", None, "x", 0)
    ok_primary.verdict = "ready"
    ok_primary.verdict_valid = True
    failed_sweep = _r("sweep", 1, "x", 1)
    # compute_merged_verdict should produce "ready" because the failed sweep
    # is excluded from aggregation per spec §S1.7.
    assert er.compute_merged_verdict([ok_primary, failed_sweep]) == "ready"


def test_merged_verdict_revise_when_primary_failed():
    failed_primary = _r("primary", None, "x", 1)
    ok_sweep = _r("sweep", 1, "x", 0)
    ok_sweep.verdict = "ready"
    ok_sweep.verdict_valid = True
    # Primary failed → no merged verdict (spec §S1.7 row 4/5).
    assert er.compute_merged_verdict([failed_primary, ok_sweep]) is None
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest skills/external-review/tests/test_merged_findings_skips_failed.py::test_merged_verdict_ignores_failed_reviewers -v`
Expected: fails — current `compute_merged_verdict` returns `revise` when any reviewer has `verdict_valid=False`.

- [x] **Step 3: Update compute_merged_verdict**

In `skills/external-review/scripts/external-reviewer.py`, replace `compute_merged_verdict`:

```python
def compute_merged_verdict(reviewer_results: list) -> str | None:
    """Merge per-reviewer verdicts per spec §S1.7.

    - If the primary reviewer failed (returncode != 0), return None: the round
      as a whole has no trustworthy verdict and the top-level status will be
      `failed`.
    - Otherwise, aggregate only the reviewers whose process succeeded.
    - Among the successful reviewers: any `revise` (or invalid verdict text)
      → revise; any `ready with small edits` → that; all `ready` → ready.
    """
    primary = next((r for r in reviewer_results if r.role == "primary"), None)
    if primary is not None and primary.returncode != 0:
        return None
    ok = [r for r in reviewer_results if r.returncode == 0]
    if not ok:
        return None
    if any((not r.verdict_valid) or r.verdict == "revise" for r in ok):
        return "revise"
    if any(r.verdict == "ready with small edits" for r in ok):
        return "ready with small edits"
    if all(r.verdict == "ready" for r in ok):
        return "ready"
    return None
```

- [x] **Step 4: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_merged_findings_skips_failed.py skills/external-review/tests/test_gate_merged_verdict.py -v`
Expected: new tests pass; existing gate/merged-verdict tests pass.

- [x] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_merged_findings_skips_failed.py
git commit -m "external-reviewer: aggregate merged verdict only over ok reviewers"
```

### Task 1.8: Persist returncode + status in chain.json

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (round entry construction around lines 1075-1106, top-level JSON emit around lines 1118-1140)
- Create: `skills/external-review/tests/test_returncode_status_persisted.py`

- [x] **Step 1: Write the failing test**

Create `skills/external-review/tests/test_returncode_status_persisted.py`:

```python
from pathlib import Path
import os, subprocess, sys, json, importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


FAKE_OK = """#!/usr/bin/env bash
echo "## F1"
echo "Severity: blocking"
echo "stub"
echo "Overall verdict: revise"
"""

FAKE_FAIL = """#!/usr/bin/env bash
echo "noise on stderr" 1>&2
exit 1
"""


def _init(tmp_path, reviewer_src):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    reviewer = repo / "fake.sh"; reviewer.write_text(reviewer_src); reviewer.chmod(0o755)
    return repo, reviewer


def _run(repo, reviewer):
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )


def test_ok_round_persists_status_and_returncode(tmp_path):
    repo, reviewer = _init(tmp_path, FAKE_OK)
    result = _run(repo, reviewer)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["returncode"] == 0
    manifest = json.loads((repo / "docs/reviewer/plan-plan/chain.json").read_text())
    round1 = manifest["rounds"][0]
    assert round1["status"] == "ok"
    assert round1["returncode"] == 0
    assert round1["reviewers"][0]["status"] == "ok"
    assert round1["reviewers"][0]["returncode"] == 0


def test_failed_round_persists_status_failed(tmp_path):
    repo, reviewer = _init(tmp_path, FAKE_FAIL)
    result = _run(repo, reviewer)
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "failed"
    assert payload["returncode"] != 0
    assert payload["verdict_valid"] is False
    manifest = json.loads((repo / "docs/reviewer/plan-plan/chain.json").read_text())
    round1 = manifest["rounds"][0]
    assert round1["status"] == "failed"
    assert round1["returncode"] != 0
    assert round1["verdict_valid"] is False
    assert round1["reviewers"][0]["status"] == "failed"
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest skills/external-review/tests/test_returncode_status_persisted.py -v`
Expected: failures — `status` and `returncode` are not yet on the round entry or per-reviewer entry.

- [x] **Step 3: Extend the test to cover emitted JSON `reviewers[]`**

Append to `skills/external-review/tests/test_returncode_status_persisted.py`:

```python
def test_emitted_json_reviewers_carry_status_and_returncode(tmp_path):
    repo, reviewer = _init(tmp_path, FAKE_OK)
    result = _run(repo, reviewer)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    # Every reviewer entry in the top-level emitted JSON must carry status + returncode.
    assert payload["reviewers"], "expected at least one reviewer"
    for r in payload["reviewers"]:
        assert r["status"] == "ok"
        assert r["returncode"] == 0


def test_emitted_json_reviewers_show_failure(tmp_path):
    repo, reviewer = _init(tmp_path, FAKE_FAIL)
    result = _run(repo, reviewer)
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    for r in payload["reviewers"]:
        assert r["status"] == "failed"
        assert r["returncode"] != 0
        assert r["verdict_valid"] is False
```

- [x] **Step 4: Add status + returncode to round entry construction**

In `skills/external-review/scripts/external-reviewer.py`, find the `round_entry = {...}` block (around line 1075):

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
```

Replace the `"reviewers"` list comprehension and add top-level `status`/`returncode` keys:

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
                "returncode": r.returncode,
                "status": "ok" if r.returncode == 0 else "failed",
            }
            for r in reviewer_results
        ],
        "status": "ok" if primary.returncode == 0 else "failed",
        "returncode": primary.returncode,
```

(Continue with the rest of the existing keys: `"merged_verdict": merged_verdict, ...`.)

- [x] **Step 5: Add status + returncode to the emitted JSON `reviewers[]`**

In `skills/external-review/scripts/external-reviewer.py`, find the JSON emit (around line 1140-1149):

```python
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
```

Replace with:

```python
            "reviewers": [
                {
                    "role": r.role,
                    "verdict": r.verdict,
                    "verdict_valid": r.verdict_valid,
                    "review_path": rel_or_abs(r.response_path, root),
                    "review": r.review_body,
                    "returncode": r.returncode,
                    "status": "ok" if r.returncode == 0 else "failed",
                }
                for r in reviewer_results
            ],
```

- [x] **Step 6: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_returncode_status_persisted.py skills/external-review/tests/test_main_round_writes_manifest.py -v`
Expected: all four tests in `test_returncode_status_persisted.py` pass; existing tests pass.

- [x] **Step 7: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_returncode_status_persisted.py
git commit -m "external-reviewer: persist returncode + status on rounds, reviewers, and JSON"
```

### Task 1.9: Soft-migrate legacy chain.json entries to status: "unknown"

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (manifest read path around lines 821-845)
- Create: `skills/external-review/tests/test_chain_soft_migration.py`

- [x] **Step 1: Write the failing test**

Create `skills/external-review/tests/test_chain_soft_migration.py`:

```python
from pathlib import Path
import os, subprocess, sys, json, importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def _init(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    return repo


def test_legacy_chain_entries_treated_as_unknown(tmp_path):
    repo = _init(tmp_path)
    chain_dir = repo / "docs" / "reviewer" / "plan-plan"
    chain_dir.mkdir(parents=True)
    # Hand-write a pre-S1 chain.json: one round with no returncode/status.
    legacy = {
        "schema_version": 1,
        "chain": "plan-plan",
        "kind": "plan",
        "target": "plan.md",
        "work_id": None,
        "legacy_migrated": False,
        "rounds": [{
            "round": 1,
            "reviewers": [{
                "role": "primary", "sweep_group": None, "parent_round": 1,
                "request": "r1-request.md", "response": "r1-response.md",
                "verdict": "revise", "verdict_valid": True,
            }],
            "merged_verdict": "revise",
            "merged_findings": None,
            "request": "r1-request.md",
            "response": "r1-response.md",
            "resolution": None,
            "resolution_parse_status": None,
            "resolution_waiver": False,
            "head_sha_at_request": None,
            "head_sha_after_round": None,
            "worktree_dirty_at_request": False,
            "verdict": "revise",
            "verdict_valid": True,
            "findings_count": 1,
            "blocking_findings_count": 1,
            "base_ref": None,
            "base_ref_source": None,
            "diff_included": False,
        }],
        "sweep_checkpoints": {"first-round": "pending", "final-ready": "pending"},
    }
    (chain_dir / "chain.json").write_text(json.dumps(legacy))
    # Stub the response file with whatever, it won't be loaded by the migrator.
    (chain_dir / "r1-response.md").write_text("# old response\nOverall verdict: revise\n")
    (chain_dir / "r1-request.md").write_text("old request")

    loaded = er.read_manifest(chain_dir / "chain.json")
    er.migrate_manifest_inplace(loaded)
    # After migration: legacy round has status "unknown" and returncode None.
    round1 = loaded["rounds"][0]
    assert round1.get("status") == "unknown"
    assert round1.get("returncode") is None
    assert round1["reviewers"][0]["status"] == "unknown"
    assert round1["reviewers"][0]["returncode"] is None
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest skills/external-review/tests/test_chain_soft_migration.py -v`
Expected: failure — `migrate_manifest_inplace` does not exist.

- [x] **Step 3: Implement the migrator**

In `skills/external-review/scripts/external-reviewer.py`, immediately after the `write_manifest` function (around line 138), add:

```python
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
```

Then wire it into both manifest entry paths.

**Path A: existing chain.json** — find (around line 821):

```python
        manifest = read_manifest(manifest_path)
```

Add immediately after:

```python
        manifest = read_manifest(manifest_path)
        if manifest is not None:
            migrate_manifest_inplace(manifest)
```

**Path B: synthesized legacy manifest** — find (around line 829-837):

```python
    if manifest is None and any(chain_dir.glob("r*-*-request.md")):
        manifest = synthesize_legacy_manifest(
            chain_dir=chain_dir,
            chain=chain_dir.name,
            kind=args.kind,
            target=rel_or_abs(target, root),
            work_id=args.work_id,
        )
        write_manifest(manifest_path, manifest)
```

Replace with:

```python
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
```

This ensures synthesized rounds (built from on-disk legacy `r*-request.md` / `r*-response.md` files where `chain.json` never existed) get `status: "unknown"` and `returncode: null` before being persisted, instead of inheriting the (untrusted) `verdict_valid: true` that `synthesize_legacy_manifest` currently derives from echoed prompt text.

- [x] **Step 4: Add a second test for synthesized chains**

Append to `skills/external-review/tests/test_chain_soft_migration.py`:

```python
def test_synthesized_legacy_manifest_marks_rounds_unknown(tmp_path):
    """Chain with on-disk r1-* artifacts but no chain.json: synthesize + migrate."""
    repo = _init(tmp_path)
    chain_dir = repo / "docs" / "reviewer" / "plan-plan"
    chain_dir.mkdir(parents=True)
    # No chain.json. But there's a legacy r1-*-request.md / response.md pair.
    (chain_dir / "r1-2025-01-01T0000-request.md").write_text("legacy request")
    (chain_dir / "r1-2025-01-01T0000-response.md").write_text(
        "# old response\nOverall verdict: revise\n"
    )

    # Drive the script through main() so synthesis + migration both run.
    import os, subprocess, sys
    reviewer = repo / "ok.sh"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json",
         "--allow-missing-resolution"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr

    manifest = json.loads((chain_dir / "chain.json").read_text())
    # The synthesized r1 round must be status: "unknown"; the freshly-run r2 must be "ok".
    rounds = manifest["rounds"]
    assert len(rounds) == 2
    assert rounds[0]["round"] == 1 and rounds[0]["status"] == "unknown"
    assert rounds[0]["returncode"] is None
    assert rounds[1]["status"] == "ok"
```

- [x] **Step 5: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_chain_soft_migration.py skills/external-review/tests/test_legacy_migration.py -v`
Expected: both new tests pass; existing legacy-migration tests pass.

- [x] **Step 6: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_chain_soft_migration.py
git commit -m "external-reviewer: soft-migrate legacy rounds (read + synthesis) to unknown"
```

### Task 1.10: Preamble walks back past failed/unknown rounds

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`build_incremental_preamble`, around lines 257-325)
- Create: `skills/external-review/tests/test_preamble_skips_failed.py`

- [x] **Step 1: Write the failing tests**

Create `skills/external-review/tests/test_preamble_skips_failed.py`:

```python
from pathlib import Path
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def _round(n, status, verdict="revise", merged="r-merged.md", response="r-response.md", findings=1, blocking=0):
    return {
        "round": n, "status": status,
        "merged_verdict": verdict, "verdict": verdict, "verdict_valid": True,
        "findings_count": findings, "blocking_findings_count": blocking,
        "response": response, "merged_findings": merged,
    }


def test_preamble_walks_back_past_failed(tmp_path):
    # r1 ok with a real merged-findings; r2 failed; r3 building.
    (tmp_path / "r1-merged-findings.md").write_text("REAL R1 FINDINGS")
    (tmp_path / "r2-2026-response.md").write_text("ECHOED PROMPT GARBAGE")
    manifest = {
        "chain": "demo", "rounds": [
            _round(1, "ok", merged="r1-merged-findings.md"),
            _round(2, "failed", verdict=None, response="r2-2026-response.md", merged=None),
        ],
    }
    out = er.build_incremental_preamble(
        manifest=manifest, chain_dir=tmp_path, round_num=3,
        resolution_waiver=False, legacy_first_round=False, diff_section="",
    )
    assert "REAL R1 FINDINGS" in out
    assert "ECHOED PROMPT GARBAGE" not in out
    assert "skipped" in out.lower()


def test_preamble_walks_back_past_unknown(tmp_path):
    # r1 unknown (legacy); r2 ok; r3 building.
    (tmp_path / "r1-response.md").write_text("LEGACY OF DUBIOUS ORIGIN")
    (tmp_path / "r2-merged-findings.md").write_text("REAL R2 FINDINGS")
    manifest = {
        "chain": "demo", "rounds": [
            _round(1, "unknown", response="r1-response.md", merged=None),
            _round(2, "ok", merged="r2-merged-findings.md"),
        ],
    }
    out = er.build_incremental_preamble(
        manifest=manifest, chain_dir=tmp_path, round_num=3,
        resolution_waiver=False, legacy_first_round=False, diff_section="",
    )
    assert "REAL R2 FINDINGS" in out
    assert "LEGACY OF DUBIOUS ORIGIN" not in out


def test_preamble_no_successful_prior_round(tmp_path):
    # r1 failed; r2 building. Fall back to chain summary only.
    (tmp_path / "r1-response.md").write_text("ECHO")
    manifest = {
        "chain": "demo", "rounds": [
            _round(1, "failed", verdict=None, response="r1-response.md", merged=None),
        ],
    }
    out = er.build_incremental_preamble(
        manifest=manifest, chain_dir=tmp_path, round_num=2,
        resolution_waiver=False, legacy_first_round=False, diff_section="",
    )
    assert "ECHO" not in out
    assert "no prior review available" in out.lower() or "no successful prior" in out.lower()
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest skills/external-review/tests/test_preamble_skips_failed.py -v`
Expected: failures — current preamble always embeds the immediate prior round's body.

- [x] **Step 3: Update build_incremental_preamble**

In `skills/external-review/scripts/external-reviewer.py`, replace the prior-response selection logic in `build_incremental_preamble`. Find (around line 275-285):

```python
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
```

Replace with:

```python
    # Walk backward to the last round whose process status is "ok".
    # Skip rounds with status "failed" (process error, body is stderr-echo)
    # or "unknown" (legacy entries, untrusted by default).
    skipped_rounds: list[int] = []
    trusted = None
    for r in reversed(prior_rounds):
        if r.get("status") == "ok":
            trusted = r
            break
        skipped_rounds.append(r["round"])
    skipped_rounds.reverse()

    prior_response_text = ""
    if trusted is not None:
        merged_findings_file = chain_dir / f"r{trusted['round']}-merged-findings.md"
        if merged_findings_file.exists():
            prior_response_text = merged_findings_file.read_text(encoding="utf-8")
            prior_source = f"merged findings from r{trusted['round']} (authoritative)"
        elif trusted.get("response"):
            response_path = chain_dir / trusted["response"]
            if response_path.exists():
                prior_response_text = response_path.read_text(encoding="utf-8")
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
                f"\nNote: round {skip_lo} was a process failure or pre-S1 entry; skipped.\n"
            )
        else:
            skip_note = (
                f"\nNote: rounds {skip_lo}..{skip_hi} were process failures or "
                f"pre-S1 entries; skipped.\n"
            )
        prior_response_text = skip_note + prior_response_text
```

- [x] **Step 4: Add stable section headings to the returned preamble**

The current `build_incremental_preamble` returns a body whose sub-section labels are plain prose (e.g. `Prior-round findings ({prior_source}):`). Task 2.4's budget trimmer needs stable, regex-friendly anchors. In the f-string `return` of `build_incremental_preamble` (around lines 300-325 of the script), replace the labels with markdown subheadings:

```python
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
```

(The `## ` subheadings are new; the body content under each is unchanged.)

- [x] **Step 5: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_preamble_skips_failed.py skills/external-review/tests/test_incremental_prompt.py -v`
Expected: new tests pass; existing incremental-prompt tests pass (they use `status: "ok"` rounds by default; if any synthesise a round dict without `status`, run `migrate_manifest_inplace` on the manifest in those tests or add `"status": "ok"`). If `test_incremental_prompt.py` asserts the old label strings (`"Prior-round findings ("`), update those assertions to the new `## Prior-round findings` heading.

- [x] **Step 6: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_preamble_skips_failed.py \
        skills/external-review/tests/test_incremental_prompt.py
git commit -m "external-reviewer: preamble walks back past failed/unknown rounds"
```

(Stage `test_incremental_prompt.py` only if you needed to edit it in Step 5.)

### Task 1.11: Resolution gate bypass on prior round with status: "failed"

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (the resolution-required gate at line ~871)
- Create: `skills/external-review/tests/test_resolution_gate_bypass.py`

- [x] **Step 1: Locate the gate**

Run: `grep -n "verdict_valid is False\|allow_missing_resolution\|resolution-required" skills/external-review/scripts/external-reviewer.py | head -10`
Note the exact line numbers; the gate is around line 871.

- [x] **Step 2: Write the failing tests**

Create `skills/external-review/tests/test_resolution_gate_bypass.py`:

```python
from pathlib import Path
import os, subprocess, sys, json, importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


FAKE_OK = """#!/usr/bin/env bash
echo "## F1"
echo "Severity: blocking"
echo "Stub finding."
echo "Overall verdict: revise"
"""

FAKE_FAIL = """#!/usr/bin/env bash
echo "stderr noise" 1>&2
exit 1
"""


def _init(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    return repo


def _run(repo, reviewer_src):
    reviewer = repo / "fake.sh"; reviewer.write_text(reviewer_src); reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--file", "plan.md",
         "--work-id", "P1.S1", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )


def test_failed_prior_round_bypasses_resolution_gate(tmp_path):
    repo = _init(tmp_path)
    # r1: real revise verdict (OK reviewer).
    r1 = _run(repo, FAKE_OK)
    assert r1.returncode == 0, r1.stderr
    # r2: process failure.
    r2 = _run(repo, FAKE_FAIL)
    assert r2.returncode != 0
    # r3: submit again without --allow-missing-resolution and without r2-resolution.md
    # Expected: exit code is NOT 3 (resolution-gate violation).
    r3 = _run(repo, FAKE_OK)
    # r3 may succeed (returncode 0) or fail with the reviewer's exit code,
    # but it must NOT exit with code 3 (the resolution gate).
    assert r3.returncode != 3, (
        f"resolution gate fired despite failed prior round; "
        f"stderr: {r3.stderr}"
    )


def test_unknown_prior_round_does_not_bypass_gate(tmp_path):
    repo = _init(tmp_path)
    # Run r1 ok, then mutate chain.json to flip r1 to status: "unknown"
    # to simulate a legacy entry; build r1-resolution requirement by leaving
    # no resolution file and ensuring r1's verdict was revise.
    _run(repo, FAKE_OK)
    chain_path = repo / "docs/reviewer/plan-P1.S1-post-slice/chain.json"
    manifest = json.loads(chain_path.read_text())
    manifest["rounds"][0]["status"] = "unknown"
    chain_path.write_text(json.dumps(manifest))
    # Now submit r2 — gate should fire because the prior round's status is unknown.
    r2 = _run(repo, FAKE_OK)
    assert r2.returncode == 3, (
        f"resolution gate did not fire on unknown prior; rc={r2.returncode} "
        f"stderr={r2.stderr}"
    )
```

- [x] **Step 3: Run tests to verify they fail**

Run: `python3 -m pytest skills/external-review/tests/test_resolution_gate_bypass.py -v`
Expected: failure — failed prior round currently has no special treatment, so the gate fires with exit 3.

- [x] **Step 4: Update the resolution gate**

In `skills/external-review/scripts/external-reviewer.py`, locate the resolution-required gate (the block starting around line 871). The current code uses the variable name `prior` for the prior round's dict and `prior_round` for its integer round number — keep those names. The current code:

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
                ...
                return 3
```

Replace the inner `needs_resolution` predicate construction and the file-missing branch with:

```python
        prior = manifest["rounds"][-1]
        prior_round = prior["round"]
        prior_verdict = prior.get("merged_verdict") or prior.get("verdict")
        prior_valid = prior.get("verdict_valid", True)
        prior_status = prior.get("status")  # "ok" | "failed" | "unknown" | None (very-old legacy)
        prior_was_process_failure = prior_status == "failed"
        needs_resolution = (
            (prior_verdict == "revise") or (prior_valid is False)
        ) and not prior_was_process_failure
        if prior_was_process_failure:
            print(
                f"Note: prior round r{prior_round} was a process failure "
                f"(returncode={prior.get('returncode')}); "
                "resolution gate bypassed.",
                file=sys.stderr,
            )
        if needs_resolution:
            resolution_path = chain_dir / f"r{prior_round}-resolution.md"
            if not resolution_path.exists():
                # ... preserve the existing ERROR-printing branch verbatim ...
                return 3
```

(Preserve every line below the `if not resolution_path.exists():` check exactly as it is — the ERROR-printing block, the rel/response_rel computation, all of it. Only the predicate and the new `prior_was_process_failure` Note-printing branch are new.)

- [x] **Step 5: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_resolution_gate_bypass.py skills/external-review/tests/test_resolution_gate.py -v`
Expected: both bypass tests pass; the existing resolution-gate tests pass.

- [x] **Step 6: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_resolution_gate_bypass.py
git commit -m "external-reviewer: bypass resolution gate on failed prior round"
```

### Task 1.12: End-to-end fixture — failed r2 yields bounded r3

This is the integration test that pins the spec's primary acceptance gate. All sentinel-stripping, persistence, walk-back, and gate-bypass behaviour must compose correctly.

**Files:**
- Create: `skills/external-review/tests/test_failed_r2_bounded_r3.py`

- [x] **Step 1: Write the test**

Create `skills/external-review/tests/test_failed_r2_bounded_r3.py`:

```python
from pathlib import Path
import os, subprocess, sys, json, importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


# r1: produces a LARGE merged-findings body (simulate the multistore 600 KB chain).
FAKE_R1_LARGE = """#!/usr/bin/env bash
cat <<'EOF'
## F1
Severity: blocking
EOF
# Pad to ~150 KB of plausible review prose to stress the diet.
python3 -c "print(('finding-body-line ' * 12) + '\\n', end='')" \
  | awk 'BEGIN { for (i=0;i<8000;i++) print "finding-body-line filler text "; }'
cat <<'EOF'

Overall verdict: revise
EOF
"""

# r2: process failure that echoes the entire incoming prompt on stderr,
# faithfully reproducing the OpenAI Codex echo-on-error behaviour.
FAKE_R2_ECHO_FAIL = """#!/usr/bin/env bash
echo "Reading prompt from stdin..." 1>&2
cat 1>&2
exit 1
"""

# r3: produce a small ready verdict if r3's prompt is well-formed.
FAKE_R3_READY = """#!/usr/bin/env bash
echo "review body"
echo "Overall verdict: ready"
"""


def _init(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n" + ("body line\n" * 200))
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    return repo


def _run(repo, reviewer_src, *extra_args):
    reviewer = repo / "fake.sh"; reviewer.write_text(reviewer_src); reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--file", "plan.md",
         "--work-id", "P1.S1", "--prompt-transport", "stdin", "--emit", "json",
         *extra_args],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )


def test_failed_r2_yields_bounded_and_clean_r3_request(tmp_path):
    repo = _init(tmp_path)
    # r1 — large, ok
    r1 = _run(repo, FAKE_R1_LARGE)
    assert r1.returncode == 0, r1.stderr
    # r2 — failure with echoed prompt
    r2 = _run(repo, FAKE_R2_ECHO_FAIL)
    assert r2.returncode != 0
    payload = json.loads(r2.stdout)
    assert payload["status"] == "failed"
    assert payload["verdict_valid"] is False
    # r2 response file is ≤ 8 KB total
    chain_dir = repo / "docs/reviewer/plan-P1.S1-post-slice"
    r2_response = next(chain_dir.glob("r2-*-response.md"))
    assert r2_response.stat().st_size < 8 * 1024, r2_response.stat().st_size
    assert er.PROMPT_SENTINEL_START not in r2_response.read_text()
    # r3 — submit without resolution file; the gate must bypass because r2 was a failure
    r3 = _run(repo, FAKE_R3_READY)
    assert r3.returncode == 0, (
        f"r3 did not succeed; rc={r3.returncode} stderr={r3.stderr}"
    )
    # r3 request must be bounded
    r3_request = next(chain_dir.glob("r3-*-request.md"))
    assert r3_request.stat().st_size < 250 * 1024, (
        f"r3 request bytes={r3_request.stat().st_size}; expected < 250 KB"
    )
    # r3 request must NOT contain the echoed-prompt phrase that the failed r2 produced.
    body = r3_request.read_text()
    assert "Reading prompt from stdin..." not in body
```

- [x] **Step 2: Run the test**

Run: `python3 -m pytest skills/external-review/tests/test_failed_r2_bounded_r3.py -v`

Expected: depending on whether Slice 2's diet has been applied, r3 may be under 250 KB already (Task 1.10's walk-back skips r2 entirely; r1's 150 KB merged-findings is the dominant body). If the test fails on r3 size, do not implement the diet here — mark the size assertion `xfail` with reason `"size guarantee tightens after Slice 2"` and proceed. Remove the xfail in Task 2.4. Status, gate-bypass, and sentinel assertions must pass now.

- [x] **Step 3: Commit**

```bash
git add skills/external-review/tests/test_failed_r2_bounded_r3.py
git commit -m "external-reviewer: e2e test — failed r2 yields bounded clean r3"
```

### Task 1.13: Run the full suite, snapshot baseline

- [x] **Step 1: Run the suite**

Run: `python3 -m pytest skills/external-review/tests/ -v 2>&1 | tail -30`
Expected: all tests pass (or only the Task 1.12 size assertion is `xfail`). If any pre-existing test fails because of the changes in this slice, fix it in this task before moving on — the slice does not close on a red suite.

- [x] **Step 2: Confirm count**

Run: `python3 -m pytest skills/external-review/tests/ -q 2>&1 | tail -5`
Note the passed/failed/xfailed counts in chat to the operator at slice close.

- [x] **Step 3: Commit any test fixes**

If you needed to fix any pre-existing tests for the new contract:

```bash
git add skills/external-review/tests/
git commit -m "external-reviewer: align legacy tests with new failure semantics"
```

Slice 1 acceptance is met when:
- `python3 -m pytest skills/external-review/tests/` is green (or has only the Task 1.12 size `xfail` pending Slice 2).
- The simulated failed-r2 fixture produces a `≤ 8 KB` r2-response, a `chain.json` with `status: "failed"` and `verdict_valid: false`, and an r3 that submits without resolution-gate violation.

→ Invoke `superstar:external-review --kind post-slice --file docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md --work-id S1 --context docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md --review-depth thorough` to gate slice close.

---

## Slice 2 — Incremental prompt diet

Independent correctness of S1 must hold before this slice begins. The diet is pure size optimisation; if anything here breaks correctness, Slice 1's behaviours are still in place to prevent compounding.

### Task 2.1: Drop context previews on incremental rounds

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`make_prompt`)
- Create: `skills/external-review/tests/test_incremental_drops_context.py`

- [ ] **Step 1: Write the failing test**

Create `skills/external-review/tests/test_incremental_drops_context.py`:

```python
from pathlib import Path
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def _setup(tmp_path):
    target = tmp_path / "plan.md"; target.write_text("# plan\nbody\n")
    ctx1 = tmp_path / "spec.md"; ctx1.write_text("# spec\nx\n")
    ctx2 = tmp_path / "TASKLIST.md"; ctx2.write_text("# tasks\ny\n")
    return target, [ctx1, ctx2]


def test_broad_mode_includes_context_previews(tmp_path, monkeypatch):
    target, context = _setup(tmp_path)
    monkeypatch.chdir(tmp_path)
    out = er.make_prompt(
        root=tmp_path, target=target, kind="plan",
        context=context, max_lines=10, mode="broad",
        incremental_preamble=None,
    )
    assert "## Context Previews" in out


def test_incremental_mode_excludes_context_previews(tmp_path, monkeypatch):
    target, context = _setup(tmp_path)
    monkeypatch.chdir(tmp_path)
    out = er.make_prompt(
        root=tmp_path, target=target, kind="plan",
        context=context, max_lines=10, mode="incremental",
        incremental_preamble="prior preamble",
    )
    assert "## Context Previews" not in out
    # Context files are still NAMED in the preamble or body.
    assert "spec.md" in out
    assert "TASKLIST.md" in out
```

- [ ] **Step 2: Run tests to verify the incremental one fails**

Run: `python3 -m pytest skills/external-review/tests/test_incremental_drops_context.py -v`
Expected: `test_broad_mode_includes_context_previews` passes; `test_incremental_mode_excludes_context_previews` fails.

- [ ] **Step 3: Skip the block on incremental**

In `skills/external-review/scripts/external-reviewer.py`, find in `make_prompt`:

```python
    if context:
        body += "\n## Context Previews\n\n"
        for ctx in context:
            body += numbered_preview(ctx, root, max_lines=max(80, max_lines // 3))
```

Replace with:

```python
    if context and mode != "incremental":
        body += "\n## Context Previews\n\n"
        for ctx in context:
            body += numbered_preview(ctx, root, max_lines=max(80, max_lines // 3))
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_incremental_drops_context.py skills/external-review/tests/test_prompt_contract.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_incremental_drops_context.py
git commit -m "external-reviewer: drop context previews on incremental rounds"
```

### Task 2.2: Trim target preview on incremental

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`make_prompt`)
- Create: `skills/external-review/tests/test_target_preview_trim.py`

- [ ] **Step 1: Write the failing test**

Create `skills/external-review/tests/test_target_preview_trim.py`:

```python
from pathlib import Path
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def _setup(tmp_path, n_lines=600):
    target = tmp_path / "plan.md"
    target.write_text("\n".join(f"line {i}" for i in range(n_lines)) + "\n")
    return target


def test_broad_mode_target_preview_uses_max_lines(tmp_path, monkeypatch):
    target = _setup(tmp_path)
    monkeypatch.chdir(tmp_path)
    out = er.make_prompt(
        root=tmp_path, target=target, kind="plan", context=[],
        max_lines=600, mode="broad", incremental_preamble=None,
    )
    assert "line 500" in out  # broad mode renders up to max_lines


def test_incremental_mode_target_preview_trimmed_to_150(tmp_path, monkeypatch):
    target = _setup(tmp_path)
    monkeypatch.chdir(tmp_path)
    out = er.make_prompt(
        root=tmp_path, target=target, kind="plan", context=[],
        max_lines=600, mode="incremental", incremental_preamble="x",
    )
    assert "line 100" in out      # within trim window
    assert "line 200" not in out  # past 150-line trim
```

- [ ] **Step 2: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_target_preview_trim.py -v`
Expected: `test_incremental_mode_target_preview_trimmed_to_150` fails (current code uses full `max_lines` regardless of mode).

- [ ] **Step 3: Apply the trim**

In `skills/external-review/scripts/external-reviewer.py`, find:

```python
    body += "\n\n## Target Preview\n\n"
    body += numbered_preview(target, root, max_lines=max_lines)
```

Replace with:

```python
    effective_target_max = min(max_lines, 150) if mode == "incremental" else max_lines
    body += "\n\n## Target Preview\n\n"
    body += numbered_preview(target, root, max_lines=effective_target_max)
```

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_target_preview_trim.py -v`
Expected: both pass.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_target_preview_trim.py
git commit -m "external-reviewer: trim target preview to 150 lines on incremental"
```

### Task 2.3: Cap prior-text reads in build_incremental_preamble

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`build_incremental_preamble`)
- Create: `skills/external-review/tests/test_prior_text_caps.py`

- [ ] **Step 1: Add the cap helper**

In `skills/external-review/scripts/external-reviewer.py`, immediately after the `strip_prompt_echo` function added in Task 1.1, add:

```python
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
```

- [ ] **Step 2: Write the failing test**

Create `skills/external-review/tests/test_prior_text_caps.py`:

```python
from pathlib import Path
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def test_cap_with_elision_passthrough_small():
    text = "small body"
    assert er.cap_with_elision(text, max_bytes=1000) == text


def test_cap_with_elision_truncates_large():
    text = "X" * 200_000
    out = er.cap_with_elision(text, max_bytes=80 * 1024)
    assert len(out.encode("utf-8")) <= 80 * 1024 + 200  # marker scaffolding
    assert "bytes elided" in out


def test_preamble_caps_prior_response_text(tmp_path):
    # 200 KB merged findings → must be capped to ≤ 80 KB in the preamble.
    big = tmp_path / "r1-merged-findings.md"
    big.write_text("M" * 200_000)
    manifest = {
        "chain": "demo",
        "rounds": [{
            "round": 1, "status": "ok",
            "verdict": "revise", "verdict_valid": True,
            "merged_verdict": "revise",
            "findings_count": 1, "blocking_findings_count": 1,
            "response": "r1-response.md",
            "merged_findings": "r1-merged-findings.md",
        }],
    }
    out = er.build_incremental_preamble(
        manifest=manifest, chain_dir=tmp_path, round_num=2,
        resolution_waiver=False, legacy_first_round=False, diff_section="",
    )
    # The total preamble text contains the capped merged-findings inline.
    # Assert "M" sequence is shorter than the raw 200 KB and that the elision
    # marker is present.
    assert len(out) < 200_000
    assert "bytes elided" in out
```

- [ ] **Step 3: Run tests to verify the preamble-cap test fails**

Run: `python3 -m pytest skills/external-review/tests/test_prior_text_caps.py -v`
Expected: the cap helper tests pass; the preamble integration test fails (the preamble does not yet apply the cap).

- [ ] **Step 4: Apply the cap in build_incremental_preamble**

In `build_incremental_preamble`, find the three places that read text whole (the merged-findings/response read added in Task 1.10, and the resolution read). Wrap each read with `cap_with_elision`:

```python
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
```

And the resolution block (originally around lines 287-298 of the script):

```python
    resolution_file = chain_dir / f"r{round_num - 1}-resolution.md"
    if resolution_file.exists():
        resolution_text = cap_with_elision(
            resolution_file.read_text(encoding="utf-8"),
            max_bytes=20 * 1024,  # tighter cap for resolution docs
        )
    elif resolution_waiver:
        ...
```

(Keep the existing `elif` branches unchanged.)

- [ ] **Step 5: Run tests**

Run: `python3 -m pytest skills/external-review/tests/test_prior_text_caps.py skills/external-review/tests/test_preamble_skips_failed.py -v`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_prior_text_caps.py
git commit -m "external-reviewer: cap prior-text reads with head+tail elision"
```

### Task 2.4: Add --incremental-budget-chars with priority-order truncation

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (argparse, `make_prompt`)
- Create: `skills/external-review/tests/test_incremental_budget.py`

- [ ] **Step 1: Add the budget flag**

In `skills/external-review/scripts/external-reviewer.py`, in the argparse setup (around lines 620-700), add:

```python
    parser.add_argument(
        "--incremental-budget-chars",
        type=int, default=400_000,
        help="Global cap on assembled prompt size for incremental rounds. "
             "When exceeded, low-priority sections are trimmed first "
             "(target preview, diff body, resolution body, prior findings) "
             "before any user-required content. Default 400000.",
    )
```

- [ ] **Step 2: Write the failing test**

Create `skills/external-review/tests/test_incremental_budget.py`:

```python
from pathlib import Path
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def test_apply_budget_preserves_priority_under_cap():
    # Synthesise a prompt with the section headers in the documented order.
    # Headings match the stable anchors emitted by build_incremental_preamble
    # (Task 1.10 Step 4) and make_prompt's Target Preview.
    body = (
        f"{er.PROMPT_SENTINEL_START}\n"
        "## Review chain summary\n\n| round | verdict |\n| 1 | revise |\n\n"
        "## Prior-round findings\n\nF1: blocking, F2: important\n" + ("P" * 80_000) + "\n"
        "## Resolution report for prior round\n\n" + ("R" * 50_000) + "\n"
        "## Changes since prior round\n\n" + ("D" * 100_000) + "\n"
        "## Target Preview\n\n" + ("T" * 60_000) + "\n"
        f"{er.PROMPT_SENTINEL_END}\n"
    )
    out = er.apply_budget(body, budget_chars=120_000)
    # Sentinels and chain-summary heading must survive.
    assert er.PROMPT_SENTINEL_START in out
    assert er.PROMPT_SENTINEL_END in out
    assert "## Review chain summary" in out
    # Finding-ID list survives — it sits in the prior-findings section but is
    # at the head, so head+tail elision preserves it.
    assert "F1: blocking, F2: important" in out
    # Total must be under budget (allow 500 bytes for the budget-applied note).
    assert len(out) <= 120_000 + 500
    # A budget-applied note is appended.
    assert "<!-- budget-applied:" in out


def test_apply_budget_passthrough_under_cap():
    body = "small body"
    assert er.apply_budget(body, budget_chars=10_000) == body
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python3 -m pytest skills/external-review/tests/test_incremental_budget.py -v`
Expected: failure — `apply_budget` does not exist yet.

- [ ] **Step 4: Implement apply_budget**

In `skills/external-review/scripts/external-reviewer.py`, add immediately after the `cap_with_elision` function:

```python
# Section anchors used by apply_budget. The patterns match the headings emitted
# by build_incremental_preamble (after Task 1.10 step 4) and make_prompt's
# Target Preview header. Bounds are the next `\n## ` heading, the sentinel
# end marker, or end-of-string — whichever comes first.
_BUDGET_SECTIONS = [
    # (name, anchor regex, trim levels in bytes; final 0 means drop the body)
    ("target_preview", r"\n## Target Preview\n", [80 * 80, 40 * 80, 0]),
    ("diff_body", r"\n## Changes since prior round\n", [50 * 1024, 12 * 1024, 0]),
    ("resolution_body", r"\n## Resolution report for prior round\n", [20 * 1024, 8 * 1024, 2 * 1024]),
    ("prior_findings_body", r"\n## Prior-round findings\n", [40 * 1024, 16 * 1024, 8 * 1024]),
]


def _find_section_end(text: str, section_start: int) -> int:
    """Return the offset where a section ends: next `\\n## ` heading, the
    sentinel end marker, or end-of-text. Whichever comes first."""
    import re
    candidates = []
    m = re.search(r"\n## ", text[section_start:])
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
        # Try progressively smaller levels for THIS section until the whole
        # text fits the budget OR the section is exhausted (level 0 = drop).
        # Re-extract section_body each pass so subsequent levels operate on
        # the already-trimmed text.
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
```

- [ ] **Step 5: Wire apply_budget through make_prompt as a real parameter**

In `make_prompt`, add a new optional parameter `incremental_budget_chars: int | None = None` to the signature. Find the current signature:

```python
def make_prompt(
    *,
    root: Path,
    target: Path,
    kind: str,
    context: list[Path],
    max_lines: int,
    mode: str = "broad",
    incremental_preamble: str | None = None,
) -> str:
```

Replace with:

```python
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
```

Then change the final `return` line. Find:

```python
    return f"{PROMPT_SENTINEL_START}\n{body}\n{PROMPT_SENTINEL_END}"
```

Replace with:

```python
    assembled = f"{PROMPT_SENTINEL_START}\n{body}\n{PROMPT_SENTINEL_END}"
    if mode == "incremental" and incremental_budget_chars is not None:
        return apply_budget(assembled, budget_chars=incremental_budget_chars)
    return assembled
```

- [ ] **Step 6: Pass the flag from main() into make_prompt**

In `main()`, find the call site of `make_prompt`. The current call (around line 948-952) looks like:

```python
    prompt_text = make_prompt(
        root=root, target=target, kind=args.kind,
        context=context, max_lines=args.max_lines,
        mode=mode, incremental_preamble=incremental_preamble,
    )
```

Replace with:

```python
    prompt_text = make_prompt(
        root=root, target=target, kind=args.kind,
        context=context, max_lines=args.max_lines,
        mode=mode, incremental_preamble=incremental_preamble,
        incremental_budget_chars=args.incremental_budget_chars,
    )
```

If there is a second `make_prompt` call site in `main()` (e.g. inside a sweep dispatch branch around line 1033), update it identically.

- [ ] **Step 7: Add a CLI-level integration test**

Append to `skills/external-review/tests/test_incremental_budget.py`:

```python
def test_cli_budget_trims_actual_request(tmp_path):
    """End-to-end: spawn the script with a tiny --incremental-budget-chars
    and confirm the persisted request file carries the budget-applied note
    and stays within the budget."""
    import os, subprocess, sys, json
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n" + ("body line\n" * 50))
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    reviewer = repo / "fake.sh"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)

    # r1 — broad, generates a real merged-findings via the chain.
    r1 = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    assert r1.returncode == 0, r1.stderr

    # Inject a large merged-findings to force budget activity on r2.
    chain_dir = repo / "docs/reviewer/plan-plan"
    (chain_dir / "r1-merged-findings.md").write_text("M" * 60_000)

    # r2 — incremental with a tiny budget.
    r2 = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md",
         "--mode", "incremental", "--incremental-budget-chars", "20000",
         "--emit", "json"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    assert r2.returncode == 0, r2.stderr

    request_file = next(chain_dir.glob("r2-*-request.md"))
    body = request_file.read_text()
    assert "<!-- budget-applied:" in body
    assert len(body) <= 20_000 + 500  # +500 bytes scaffolding allowance
```

- [ ] **Step 8: Run tests, including the Task 1.12 fixture**

Run: `python3 -m pytest skills/external-review/tests/test_incremental_budget.py skills/external-review/tests/test_failed_r2_bounded_r3.py -v`
Expected: all budget tests pass; the CLI integration test asserts that the budget flag has real effect on the persisted request. If `test_failed_r2_bounded_r3` was marked `xfail` for the size assertion in Task 1.12, remove the `xfail` marker now and confirm it passes.

- [ ] **Step 9: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_incremental_budget.py \
        skills/external-review/tests/test_failed_r2_bounded_r3.py
git commit -m "external-reviewer: add --incremental-budget-chars (proper param + CLI test)"
```

### Task 2.5: Tighten diff caps

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py` (`compute_diff_section`, around lines 733-779)
- Create: `skills/external-review/tests/test_diff_caps.py`

- [ ] **Step 1: Write the failing tests**

Create `skills/external-review/tests/test_diff_caps.py`:

```python
from pathlib import Path
import subprocess
import sys
import importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


def _git_init(repo: Path):
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "seed.txt").write_text("seed\n")
    subprocess.run(["git", "-C", str(repo), "add", "seed.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)


def test_untracked_file_count_capped_at_10(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    _git_init(repo)
    base_ref = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    # Create 15 untracked files.
    for i in range(15):
        (repo / f"u{i}.txt").write_text(f"untracked {i}\n")
    diff = er.compute_diff_section(repo, base_ref=base_ref, paths=None, max_lines=500)
    # Cap message present.
    assert "more untracked files elided" in diff
    # At most 10 untracked-file headings ("### " entries) appear.
    assert diff.count("\n### u") <= 10


def test_oversized_untracked_file_line_capped(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    _git_init(repo)
    base_ref = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    # Single untracked file with 500 lines; per-file cap is min(max_lines, 200).
    (repo / "big.txt").write_text("\n".join(f"line {i}" for i in range(500)))
    diff = er.compute_diff_section(repo, base_ref=base_ref, paths=None, max_lines=500)
    # The cap-200 floor truncates at line 199 — line 400 should not be present.
    assert "line 50" in diff
    assert "line 400" not in diff


def test_global_diff_cap_applies(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    _git_init(repo)
    base_ref = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    # Eight untracked files, each genuinely 200 lines × 80 chars + newline.
    # Raw per-file body: ~16 KB. Total raw across 8 files: ~128 KB.
    # `compute_diff_section` caps each untracked file's preview at
    # `min(max_lines, 200)` lines. With max_lines=200 each preview keeps all
    # 200 lines (~16 KB). The global cap floor is `max(max_lines * 80, 64 KB)`
    # = 64 KB, well below the assembled ~128 KB → global elision must fire.
    for i in range(8):
        (repo / f"u{i}.txt").write_text(("x" * 80 + "\n") * 200)
    diff = er.compute_diff_section(repo, base_ref=base_ref, paths=None, max_lines=200)
    # cap_with_elision marker should be present.
    assert "bytes elided" in diff
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest skills/external-review/tests/test_diff_caps.py -v`
Expected: all three fail — current `compute_diff_section` has no untracked-count cap, no per-file extra cap, and no global cap.

- [ ] **Step 3: Replace compute_diff_section**

In `skills/external-review/scripts/external-reviewer.py`, replace the body of `compute_diff_section` (the version with `parts = [...]` building three subsections with independent `_cap_lines` calls):

```python
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
        "## git diff base..HEAD", "",
    ]
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
    # Global cap: ~80 chars per line worth of bytes, floor 64 KB.
    return cap_with_elision(full, max_bytes=max(max_lines * 80, 64 * 1024))
```

- [ ] **Step 4: Run all diff tests**

Run: `python3 -m pytest skills/external-review/tests/test_diff_caps.py skills/external-review/tests/test_diff.py skills/external-review/tests/test_diff_wiring.py -v`
Expected: the three new cap tests pass; existing diff tests still pass. The structural changes are: an untracked-file count cap, a per-untracked-file line cap of `min(max_lines, 200)`, and a final global `cap_with_elision`.

If a pre-existing diff test breaks, inspect its fixture. A test with > 10 untracked files or with more than `max_lines` per untracked file is asserting against a behaviour this slice deliberately tightens — update the test to match the new caps.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py \
        skills/external-review/tests/test_diff_caps.py
git commit -m "external-reviewer: global diff cap, untracked-file count + line limits"
```

### Task 2.6: Slice 2 acceptance check

- [ ] **Step 1: Run the full suite**

Run: `python3 -m pytest skills/external-review/tests/ -v 2>&1 | tail -30`
Expected: all green. No `xfail`s should remain related to this work.

- [ ] **Step 2: Synthetic large-chain manual check**

This is a documented manual verification, not a test:

```bash
cd /tmp && rm -rf budget-smoke && mkdir budget-smoke && cd budget-smoke
git init -q && git commit -q --allow-empty -m init
mkdir docs && printf '# plan\n%s\n' "$(yes "body line" | head -200)" > plan.md
git add . && git commit -qm plan
# Stage a fake 80 KB merged-findings file under a fresh chain
mkdir -p docs/reviewer/plan-plan
cat > docs/reviewer/plan-plan/chain.json <<'EOF'
{"schema_version":1,"chain":"plan-plan","kind":"plan","target":"plan.md",
 "work_id":null,"legacy_migrated":false,
 "rounds":[{"round":1,"status":"ok","verdict":"revise","verdict_valid":true,
            "merged_verdict":"revise","findings_count":1,"blocking_findings_count":1,
            "response":"r1-response.md","merged_findings":"r1-merged-findings.md"}],
 "sweep_checkpoints":{"first-round":"pending","final-ready":"pending"}}
EOF
python3 -c "open('docs/reviewer/plan-plan/r1-merged-findings.md','w').write('M' * 80000)"
echo > docs/reviewer/plan-plan/r1-response.md
AGENT_REVIEWER_CMD="bash -c 'echo Overall verdict: ready'" \
  python3 /home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py \
  review --kind plan --file plan.md --emit json --mode incremental
ls -la docs/reviewer/plan-plan/r2-*-request.md
```

Expected: the round-2 request file is under 200 KB.

- [ ] **Step 3: Commit any final fixes**

If you needed to adjust anything during the manual check, commit it:

```bash
git add skills/external-review/scripts/external-reviewer.py
git commit -m "external-reviewer: slice-2 polish"
```

Slice 2 acceptance is met when:
- All tests pass with no related `xfail`.
- The synthetic large-chain check produces an r2-request under 200 KB.

→ Invoke `superstar:external-review --kind post-slice --file docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md --work-id S2 --context docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md --review-depth thorough`.

---

## Slice 3 — SKILL.md documentation update

### Task 3.1: Update skills/external-review/SKILL.md

**Files:**
- Modify: `skills/external-review/SKILL.md`

- [ ] **Step 1: Add the new flag to "Configuration"**

In `skills/external-review/SKILL.md`, after the existing `--prompt-transport` documentation (around line 35-39 of the current SKILL.md), append:

```markdown
- A global `--incremental-budget-chars` cap (default `400000`) applies on incremental rounds. The assembled prompt is pruned in priority order — target preview, diff body, resolution body, prior findings body — to fit the cap. Sentinel markers, chain summary, and finding-ID lists are never trimmed. The resulting prompt carries a trailing `<!-- budget-applied: ... -->` note summarising trims.
```

- [ ] **Step 2: Add a "Failure handling" section**

In `skills/external-review/SKILL.md`, immediately before the "## Reading the response" section, add:

```markdown
## Failure handling

When the configured reviewer command exits non-zero, the round is recorded as a **process failure**, not as a verdict:

- The persisted response file is a short stub (≤ 8 KB total): header, status, and the sentinel-stripped tail of the reviewer's stderr capped at 4 KB. No stdout is written.
- `chain.json` records `status: "failed"`, `returncode: <rc>`, `verdict: null`, `verdict_valid: false` on both the round entry and the per-reviewer entry.
- For `post-slice` / `post-phase`, the next round's resolution-required gate is **bypassed silently** with a stderr notice. A process failure has no findings to resolve; the next round is a re-attempt of the same review, not a fix-and-re-review.
- The next round's preamble walks backward past `status: "failed"` (and legacy `status: "unknown"`) rounds and embeds the merged-findings from the most recent `status: "ok"` round, prefixed with a `Note: rounds N..K were process failures...; skipped.` line. If no successful prior round exists, only the chain summary table is embedded.

**Sentinel-wrapped prompts.** Every prompt is wrapped in `<!-- superstar-prompt:start -->` / `<!-- superstar-prompt:end -->` markers. If a reviewer echoes the prompt on stdout or stderr, the markers let the script strip the echo before persisting to disk, eliminating the recursive prompt-bloat class.

### Multi-reviewer truth (sweeps)

When `--review-depth thorough` or `exhaustive` runs sweeps alongside the primary:

| Primary | Sweeps | Top-level `status` | `verdict_valid` | `merged_verdict` | Process exit |
|---|---|---|---|---|---|
| ok | all ok | `ok` | per merged | computed | `0` |
| ok | some failed | `ok` | per merged (ok reviewers only) | computed from ok | `0` |
| ok | all failed | `ok` | per primary | primary's verdict | `0` |
| failed | any/all | `failed` | `false` | `null` | primary's returncode |

Failed sweeps are excluded from merged-findings and do not flip the top-level status.
```

- [ ] **Step 3: Update the "Exit codes" table preface**

In `skills/external-review/SKILL.md`, immediately above the "## Exit codes" heading, add a one-line note:

```markdown
*No new exit codes are introduced by failure handling — a failed reviewer exits with the reviewer's own non-zero code (typically `1`), exactly as it did before. The resolution-required gate (exit `3`) is bypassed on process failures.*
```

- [ ] **Step 4: Update the precursor "How a round runs" example**

In `skills/external-review/SKILL.md`, find the example command (around line 43-50):

```bash
python3 scripts/external-reviewer.py review \
    --kind <spec|plan|post-slice|post-phase> \
    --file <path/to/target.md> \
    --work-id <P2.S3 | P2>   # required for post-slice / post-phase
    [--context <path>]... \
    [--review-depth thorough] \
    --emit json
```

Replace with:

```bash
python3 scripts/external-reviewer.py review \
    --kind <spec|plan|post-slice|post-phase> \
    --file <path/to/target.md> \
    --work-id <P2.S3 | P2>   # required for post-slice / post-phase
    [--context <path>]... \
    [--review-depth thorough] \
    [--incremental-budget-chars 400000] \
    --emit json
```

- [ ] **Step 5: Sanity-read**

Run: `python3 -m pytest skills/external-review/tests/ -q 2>&1 | tail -5`
Expected: still all green; no test depends on SKILL.md content.

Open `skills/external-review/SKILL.md` and skim it end-to-end. Confirm the new sections fit the existing tone (terse, sectioned, no marketing language).

- [ ] **Step 6: Commit**

```bash
git add skills/external-review/SKILL.md
git commit -m "external-review: document failure handling, sweep truth table, budget flag"
```

Slice 3 acceptance is met when:
- SKILL.md describes the new failure-handling behaviour, the sweep truth table, and the budget flag.
- `python3 -m pytest skills/external-review/tests/` remains green.

→ Invoke `superstar:external-review --kind post-slice --file docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md --work-id S3 --context docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md --review-depth thorough`.

---

## Phase close

After Slice 3 closes:

- [ ] **Step 1: Full suite final run**

Run: `python3 -m pytest skills/external-review/tests/ -v 2>&1 | tail -30`
Expected: 100% green. Capture the pass count for the phase-close note.

- [ ] **Step 2: Real-chain dry-run (optional but recommended)**

Against the actual broken multistore chain — pure read-only verification that the new script produces a clean r5 even with the existing poisoned r2-r4 files in place:

```bash
cd /home/simon/Dev/sigreer/multistore
python3 /home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py \
  review --kind post-slice \
  --file docs/plans/2026-05-13-p10-s3-x39-tailwind-screen-aliases.md \
  --work-id P10.S3 \
  --context docs/TASKLIST.md \
  --review-depth standard \
  --mode incremental \
  --prompt-transport stdin \
  --emit json 2>&1 | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print('verdict:',d['verdict'],'valid:',d['verdict_valid'],'status:',d['status'])"
```

Note in the close-out: the actual r5-request size, the verdict (should be a real verdict not a fabricated one), and whether the gate-bypass note appeared on stderr.

- [ ] **Step 3: Invoke external-review for post-phase**

`superstar:external-review --kind post-phase --file docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md --context docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md --review-depth thorough`

Iterate until `ready` or `ready with small edits`.
