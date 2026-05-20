# X10 — Verdict Parser & Prompt Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate the rerun loop caused by Claude emitting `**Verdict: ready with small edits.**` (no "Overall" prefix), and centralise verdict-response normalisation behind one helper.

**Architecture:** One-file change to `skills/external-review/scripts/external-reviewer.py` plus a few targeted test additions. Two coordinated edits: (a) prompt instructs Claude to emit a literal trailerless verdict line; (b) parser gains an anchored, value-bounded fallback for bare `Verdict:` and a single `parse_reformatted_verdict(raw)` chokepoint used by both the automated round path (line 1403) and the manual ingest path (line 1814). Legacy manifest synthesis is deliberately excluded.

**Tech Stack:** Python 3 (stdlib `re`), pytest. No new dependencies.

**Spec:** [`docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md`](../specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md)

**Reviewer chain (spec):** `docs/reviewer/x10-verdict-parser-claude-formatting-design-spec/` (verdict `ready` at r5).

---

## Scheduling note

X10 is a cross-cutting item, not a phase/slice. No `tasktool schedule` / `tasktool ratify` / `tasktool start` cycle applies. The first execution step is to start a TodoWrite checklist and proceed directly to Task 1.

## File map

- Modify: `skills/external-review/scripts/external-reviewer.py` (one file)
  - `REVIEW_PROMPT` (lines 48–86): drop verdict from numbered list, add literal-format trailing paragraph.
  - `_VERDICT_HEADING_STYLE` (lines 1763–1767): make `Overall` optional.
  - `VERDICT_LINE_RE` (line 2425): unchanged (kept strict).
  - Add `VERDICT_LINE_BARE_RE` next to `VERDICT_LINE_RE`.
  - Add `parse_reformatted_verdict(raw)` helper next to `parse_verdict`.
  - Modify call site at line 1403 (automated round) to call `parse_reformatted_verdict(body)`.
  - Modify call site at line 1814 (manual ingest) to call `parse_reformatted_verdict(raw)`.
- Add: `skills/external-review/tests/fixtures/claude-bare-verdict-ready-with-small-edits.md` (copied verbatim).
- Add: `skills/external-review/tests/fixtures/claude-heading-revise.md` (copied verbatim).
- Modify: `skills/external-review/tests/test_verdict.py` — 10 new tests.
- Modify: `skills/external-review/tests/test_heading_style_verdict.py` — 1 new test.

---

## Task 1: Copy real-world fixtures into the repo

**Files:**
- Create: `skills/external-review/tests/fixtures/claude-bare-verdict-ready-with-small-edits.md`
- Create: `skills/external-review/tests/fixtures/claude-heading-revise.md`

- [ ] **Step 1: Create the fixtures directory and copy the bare-verdict fixture**

```bash
mkdir -p skills/external-review/tests/fixtures
cp /home/simon/Dev/sigreer/multistore/docs/reviewer/p11-s5-final-guardrails-and-documentation-plan/r2-2026-05-19T0054-response.md \
   skills/external-review/tests/fixtures/claude-bare-verdict-ready-with-small-edits.md
```

- [ ] **Step 2: Copy the heading-style fixture**

```bash
cp /home/simon/Dev/sigreer/multistore/docs/reviewer/p11-s5-final-guardrails-and-documentation-plan/r1-2026-05-19T0050-response.md \
   skills/external-review/tests/fixtures/claude-heading-revise.md
```

- [ ] **Step 3: Sanity-check the fixtures contain the expected verdict lines**

```bash
grep -i 'verdict' skills/external-review/tests/fixtures/claude-bare-verdict-ready-with-small-edits.md | tail -3
grep -i 'verdict' skills/external-review/tests/fixtures/claude-heading-revise.md | tail -3
```

Expected output for the bare fixture: a line containing `**Verdict: ready with small edits.**`. For the heading fixture: a `## Overall Verdict` heading and a `**revise** —` value line nearby.

- [ ] **Step 4: Commit**

```bash
git add skills/external-review/tests/fixtures/
git commit -m "X10: add real-world reviewer-response fixtures"
```

---

## Task 2: Write failing tests for bare `Verdict:` parsing

**Files:**
- Modify: `skills/external-review/tests/test_verdict.py`

- [ ] **Step 1: Append the new unit tests to `test_verdict.py`**

Append the following block to the end of `skills/external-review/tests/test_verdict.py` (the existing imports at lines 1–7 already expose `er`):

```python
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_bare_verdict_ready_with_small_edits():
    v, valid = er.parse_verdict("**Verdict: ready with small edits.**")
    assert v == "ready with small edits"
    assert valid is True


def test_bare_verdict_revise():
    v, valid = er.parse_verdict("**Verdict: revise.**")
    assert v == "revise"
    assert valid is True


def test_bare_verdict_not_matched_in_prose():
    body = "the previous round's verdict was revise, but this is just narrative.\n"
    v, valid = er.parse_verdict(body)
    assert v is None
    assert valid is False


def test_overall_preferred_over_bare():
    body = (
        "**Verdict: revise**\n\n"
        "...more prose...\n\n"
        "Overall verdict: ready\n"
    )
    v, valid = er.parse_verdict(body)
    assert v == "ready"
    assert valid is True


def test_bare_verdict_rejects_extra_words_after_value():
    v, valid = er.parse_verdict("**Verdict: ready for review**")
    assert v is None
    assert valid is False


def test_bare_verdict_rejects_hyphenated_value():
    v, valid = er.parse_verdict("Verdict: ready-ish")
    assert v is None
    assert valid is False


def test_bare_verdict_rejects_qualified_value():
    v, valid = er.parse_verdict("Verdict: ready with small edits pending changes")
    assert v is None
    assert valid is False


def test_bare_verdict_rejects_contradictory_same_line_prose():
    v, valid = er.parse_verdict("**Verdict: ready. Important findings remain unresolved.**")
    assert v is None
    assert valid is False


def test_bare_verdict_rejects_benign_same_line_prose():
    body = "**Verdict: ready with small edits.** Full review written to /tmp/foo.md."
    v, valid = er.parse_verdict(body)
    assert v is None
    assert valid is False


def test_parse_reformatted_verdict_helper():
    raw = "## Overall Verdict\n\n**revise** — text\n"
    v, valid = er.parse_reformatted_verdict(raw)
    assert v == "revise"
    assert valid is True


def test_parse_reformatted_verdict_fixture_bare():
    raw = (FIXTURES / "claude-bare-verdict-ready-with-small-edits.md").read_text()
    v, valid = er.parse_reformatted_verdict(raw)
    assert v == "ready with small edits"
    assert valid is True


def test_parse_reformatted_verdict_fixture_heading():
    raw = (FIXTURES / "claude-heading-revise.md").read_text()
    v, valid = er.parse_reformatted_verdict(raw)
    assert v == "revise"
    assert valid is True
```

- [ ] **Step 2: Run the new tests and verify they fail**

```bash
python3 -m pytest skills/external-review/tests/test_verdict.py -v
```

Expected: the six existing tests pass; the 12 new tests fail (most with `AttributeError: module 'external_reviewer' has no attribute 'parse_reformatted_verdict'` or with `assert None == "ready with small edits"` / similar).

- [ ] **Step 3: Add a failing test in `test_heading_style_verdict.py`**

Append to `skills/external-review/tests/test_heading_style_verdict.py` (after `FAKE_REVIEWER_BOLD_HEADING_STYLE`):

```python
FAKE_REVIEWER_BARE_HEADING_STYLE = """#!/usr/bin/env bash
cat <<'EOF'
## Findings
none

**Verdict**

ready with small edits
EOF
"""


def test_bare_heading_style_verdict_parses(tmp_path):
    """Claude commonly emits `**Verdict**\\n\\nvalue` (no `Overall`).

    The bare form must normalise the same way the `Overall verdict` heading
    style does, so end-to-end the round records verdict_valid=True.
    """
    payload = _run(FAKE_REVIEWER_BARE_HEADING_STYLE, tmp_path)
    assert payload["verdict"] == "ready with small edits"
    assert payload["verdict_valid"] is True
    assert payload["merged_verdict"] == "ready with small edits"
```

- [ ] **Step 4: Run the new heading test and verify it fails**

```bash
python3 -m pytest skills/external-review/tests/test_heading_style_verdict.py::test_bare_heading_style_verdict_parses -v
```

Expected: FAIL with `assert None == 'ready with small edits'` (the heading-style regex does not yet accept bare `**Verdict**`).

- [ ] **Step 5: Commit the failing tests**

```bash
git add skills/external-review/tests/test_verdict.py skills/external-review/tests/test_heading_style_verdict.py
git commit -m "X10: failing tests for bare Verdict parsing and helper"
```

---

## Task 3: Implement the parser changes

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`

- [ ] **Step 1: Extend `_VERDICT_HEADING_STYLE` to accept bare `Verdict`**

Replace lines 1763–1767 (`_VERDICT_HEADING_STYLE = re.compile(...)`):

```python
_VERDICT_HEADING_STYLE = re.compile(
    r"(?:\*+|_+)?((?:\d+\.\s+)?(?:Overall\s+)?Verdict)(?:\*+|_+)?\s*\n+\s*"
    r"(?:\*+|_+)?(ready with small edits|ready|revise)(?:\*+|_+)?",
    re.IGNORECASE,
)
```

The only change is inserting `(?:Overall\s+)?` so the qualifier is optional. `_reformat_response` (lines 1770–1775) already uses this regex; no change needed there.

- [ ] **Step 2: Add `VERDICT_LINE_BARE_RE` and a two-pass `parse_verdict`**

Replace the block at lines 2425–2438:

```python
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
```

- [ ] **Step 3: Run unit tests, expect the verdict tests to pass**

```bash
python3 -m pytest skills/external-review/tests/test_verdict.py -v
```

Expected: all 18 tests pass (6 original + 12 new).

- [ ] **Step 4: Run the heading-style suite**

```bash
python3 -m pytest skills/external-review/tests/test_heading_style_verdict.py -v
```

Expected: all three tests pass including the new `test_bare_heading_style_verdict_parses`.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py
git commit -m "X10: add bare Verdict regex, parse_reformatted_verdict helper"
```

---

## Task 4: Route both call sites through `parse_reformatted_verdict`

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`

- [ ] **Step 1: Update the automated round path**

Find lines 1400–1405 (currently):

```python
        if result.returncode != 0:
            verdict, valid = None, False
        else:
            verdict, valid = parse_verdict(_VERDICT_HEADING_STYLE.sub(
                lambda m: f"{m.group(1)}: {m.group(2)}", body
            ))
```

Replace with:

```python
        if result.returncode != 0:
            verdict, valid = None, False
        else:
            verdict, valid = parse_reformatted_verdict(body)
```

- [ ] **Step 2: Update the manual ingest path**

Find lines around 1813–1814 (inside `run_ingest_response`):

```python
    reformatted = _reformat_response(raw)
    ...
    verdict, valid = parse_verdict(reformatted)
```

Replace the two lines with a single call. Concretely: remove the `reformatted = _reformat_response(raw)` line, and change the `parse_verdict(reformatted)` line to `parse_reformatted_verdict(raw)`. Any other reference to `reformatted` in this function (e.g. when writing the response file to disk) must continue to use the reformatted body — keep the assignment if such a reference exists; otherwise remove it.

Inspect the function first:

```bash
grep -n 'reformatted' skills/external-review/scripts/external-reviewer.py
```

If `reformatted` is used in only one place (the `parse_verdict` call), collapse to:

```python
    verdict, valid = parse_reformatted_verdict(raw)
```

If it is used elsewhere (e.g. `response_path.write_text(reformatted)`), keep the `reformatted = _reformat_response(raw)` line and just change the `parse_verdict(reformatted)` call to `parse_reformatted_verdict(raw)`.

- [ ] **Step 3: Run the full external-review test suite**

```bash
python3 -m pytest skills/external-review/tests/ -q
```

Expected: 234 passed (222 original + 12 new) or close to it (count depends on parametrisation in the new tests). Zero failures.

- [ ] **Step 4: Acceptance criterion 3 — confirm single chokepoint**

```bash
grep -n 'parse_verdict\|parse_reformatted_verdict' skills/external-review/scripts/external-reviewer.py
```

Expected:
- One definition of `parse_verdict` and one definition of `parse_reformatted_verdict`.
- The automated round path (~line 1403) calls `parse_reformatted_verdict`.
- The manual ingest path (~line 1814) calls `parse_reformatted_verdict`.
- `synthesize_manifest_from_legacy_files` (around line 2598) still calls `parse_verdict` on raw legacy bodies (this is the documented exception).
- No other call to `parse_verdict` exists outside tests and the legacy synthesis function.

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py
git commit -m "X10: route both response-body call sites through parse_reformatted_verdict"
```

---

## Task 5: Tighten the prompt to discourage misformatted verdicts

**Files:**
- Modify: `skills/external-review/scripts/external-reviewer.py`

- [ ] **Step 1: Update `REVIEW_PROMPT`**

In `REVIEW_PROMPT` (the multi-line string at line 48), find the "Review output contract" list (lines ~75–83):

```
Review output contract:
1. Findings
   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
     stable if this review is iterated in subsequent rounds.
   - Mark severity inline: `Severity: blocking | important | minor | nit`.
2. Open questions / assumptions
3. Suggested document edits
4. Verification gaps / commands that should be run, if any
5. Overall verdict: one of "ready", "ready with small edits", or "revise"
```

Change to:

```
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
```

(The verdict moves out of the numbered list; the explicit don'ts are new.)

- [ ] **Step 2: Run the prompt-contract test**

```bash
python3 -m pytest skills/external-review/tests/test_prompt_contract.py -v
```

Expected: pass. If the test asserts the literal "5. Overall verdict" string is present in the prompt, it will fail — update the test to match the new wording (it should already test for `Overall verdict` presence, not the leading `5.`). Inspect the test if it fails before changing the prompt back; the new prompt is the intended behaviour.

- [ ] **Step 3: Run the full test suite as a final regression check**

```bash
python3 -m pytest skills/external-review/tests/ -q
```

Expected: zero failures.

- [ ] **Step 4: Manual acceptance replay (spec acceptance criterion 2)**

```bash
python3 -c "
import sys, importlib.util
spec = importlib.util.spec_from_file_location('er', 'skills/external-review/scripts/external-reviewer.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
for p in ['skills/external-review/tests/fixtures/claude-bare-verdict-ready-with-small-edits.md',
          'skills/external-review/tests/fixtures/claude-heading-revise.md']:
    raw = open(p).read()
    print(p, '->', m.parse_reformatted_verdict(raw))
"
```

Expected output:
```
skills/external-review/tests/fixtures/claude-bare-verdict-ready-with-small-edits.md -> ('ready with small edits', True)
skills/external-review/tests/fixtures/claude-heading-revise.md -> ('revise', True)
```

- [ ] **Step 5: Commit**

```bash
git add skills/external-review/scripts/external-reviewer.py
git commit -m "X10: tighten REVIEW_PROMPT to discourage heading-style verdicts"
```

---

## Task 6: Close out X10

- [ ] **Step 1: Add the plan and reviewer chain to X10's refs**

```bash
tasktool ref X10 --add docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md
```

- [ ] **Step 2: Run post-slice external review against the plan**

The coordinator invokes this; do **not** apply findings directly during execution — delegate to a fix subagent per `superstar:subagent-driven-development`.

```bash
python3 skills/external-review/scripts/external-reviewer.py review \
  --kind post-slice \
  --file docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md \
  --work-id X10 \
  --context docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md \
  --context docs/tasklist.json \
  --emit json
```

Iterate to `ready` or `ready with small edits`.

- [ ] **Step 3: Close X10 in tasktool**

```bash
tasktool close X10 --reviewer-chain docs/reviewer/<post-slice-chain-folder>
```

(`tasktool close` enforces the post-slice external-review gate; if the chain is missing or unresolved it will refuse.)

- [ ] **Step 4: Final commit (if anything was staged by tasktool)**

```bash
git status
git commit -m "X10: close" 2>/dev/null || echo "nothing to commit"
```

---

## Acceptance recap (mirrors spec §Acceptance)

1. `python3 -m pytest skills/external-review/tests/` — all existing + new tests pass (≥ 234 passing).
2. `parse_reformatted_verdict(open(p).read())` against `claude-bare-verdict-ready-with-small-edits.md` → `("ready with small edits", True)`; against `claude-heading-revise.md` → `("revise", True)`.
3. `parse_reformatted_verdict` is the only response-body normalisation+parse chokepoint outside legacy manifest synthesis.
4. No new dependencies, no new public CLI surface, no schema changes to `chain.json`.
