# X10 — Harden external-review verdict parser and prompt against Claude formatting variants

- **Status:** spec
- **Tasktool ID:** X10 (cross-cutting; continues the X3 line of verdict-parser fixes)
- **Date:** 2026-05-20
- **Owner:** Simon Greer
- **Touches:** `skills/external-review/scripts/external-reviewer.py`, `skills/external-review/tests/`

## Problem

When Claude is the reviewing agent under `superstar:external-review`, runs are significantly slower and burn many more tokens than Codex runs. A primary cause: Claude returns a verdict in formats that the current parser does not recognise. The round records `verdict_valid=false`, the gate forces a rerun, and the same misformatted reply is produced again, multiplying cost.

Direct evidence from `multistore/docs/reviewer/` (Claude-as-reviewer chains):

1. **`p11-s5-final-guardrails-and-documentation-plan/chain.json`** records r1 and r2 with `verdict: null, verdict_valid: false, returncode: 0`. r1's body ends with the heading-style verdict `## Overall Verdict\n\n**revise** — primarily because…` (parses correctly today via `_VERDICT_HEADING_STYLE`). r2's body ends with `**Verdict: ready with small edits.**` — **bare `Verdict:`, no "Overall" prefix** — which `VERDICT_LINE_RE` cannot match. The chain only advanced after a human-bridged r3.

2. **`p11-s2-primitive-convergence-design-spec/chain.json`** shows the same r1/r2 failure pattern.

3. Frequency across `multistore/docs/reviewer/*/r*-response.md`:
   - 61× `**Overall Verdict**` (value on next line; handled)
   - 31× `## Overall Verdict` heading (handled)
   - 7× `**Verdict: …**` / `**Verdict: ….**` (**not handled** — this is the failure mode)
   - 0 bare `Verdict:` lines were found mid-prose; every occurrence is line-anchored after optional `**` / heading marks.

## Goals

- Eliminate the rerun loop caused by Claude's `**Verdict: …**` line.
- Reduce the chance Claude produces a non-conforming verdict line in the first place.
- Keep parser surface predictable: no loose-match recovery, no telemetry plumbing, no broader prompt rewrite.

## Non-goals

- Loose-match fallback that scans the last N lines (deferred; user opted strict-only).
- Telemetry / `parser_recovery` flags in `chain.json`.
- Changes to multi-reviewer (sweep) aggregation, rate-limit handling, or any other reviewer subsystem.
- Reformatting unrelated sections of `REVIEW_PROMPT`.

## Design

Two coordinated changes.

### Change 1 — Prompt: dedicated, literal verdict-format paragraph

In `external-reviewer.py:48-86` (the `REVIEW_PROMPT` template), keep the existing "Review output contract" list but **remove the verdict from the numbered list** and replace it with a dedicated trailing paragraph that specifies the exact line. Numbered list items invite Claude to render them as headings; a free-standing instruction with a literal example does not.

New trailing section (after the existing list 1–4):

```
End your review with this exact line, as plain text on its own line:

    Overall verdict: <ready|ready with small edits|revise>

Do not bold, italicise, prefix with `##`, split across lines, or drop the word
"Overall". Do not write `**Verdict: ready**` or place the value on a new line
after a heading.
```

Rationale: explicit don'ts override Claude's markdown reflex; abstract "use this format" instructions do not.

### Change 2 — Parser: anchored bare-`Verdict:` fallback + DRY normalisation

In `external-reviewer.py`:

**2a. Centralise normalisation via a public helper.** Introduce `parse_reformatted_verdict(raw: str) -> tuple[str | None, bool]` which composes `_reformat_response` and `parse_verdict`. Both the automated round path (`external-reviewer.py:1403`) and the manual ingest path (`external-reviewer.py:1814`) MUST call this helper instead of composing the two functions by hand. `_reformat_response` already strips outer code fences and rewrites heading-style verdicts; co-locating the composition behind one named function gives a single chokepoint for future normalisations and removes the current divergence between the two call sites.

**Legacy manifest synthesis is explicitly out of scope.** `synthesize_manifest_from_legacy_files` (around `external-reviewer.py:2598`) parses raw response bodies from historical pre-manifest chains. Updating it would re-write historical verdicts on first touch, which is undesirable. It continues to call `parse_verdict` directly on the raw body, by design.

**2b. Add anchored, value-bounded bare-`Verdict:` matching.** Introduce a second regex `VERDICT_LINE_BARE_RE` that matches bare `Verdict:` **only when line-anchored** (after optional leading whitespace and markdown emphasis/heading marks) **and value-bounded** (nothing meaningful between the captured value and end-of-line beyond emphasis/punctuation/whitespace). Anchoring eliminates prose false-positives ("the previous round's verdict was revise"); value-bounding rejects malformed values like `Verdict: ready for review` or `Verdict: ready-ish` so they record as `(None, False)` rather than silently coercing to `ready`. Empirical confirmation: zero mid-prose matches found across the `multistore/docs/reviewer/` corpus.

**Out of scope for line-anchoring:** list-bullet-prefixed verdict lines (`- Verdict: ready`, `1. Verdict: ready`). None appear in the observed Claude corpus. If they appear later, extend the leading character class then; do not pre-anchor for hypotheticals.

Proposed shape:

```python
# Boundary A: end-of-line, emphasis/punct only.
# Boundary B: period (possibly emphasis-wrapped) + whitespace (handles trailing prose).
VERDICT_LINE_BARE_RE = re.compile(
    r"^[\s>#*_`]*verdict\s*[`*_\"']*\s*[:\-]\s*[`*_\"'\s]*"
    r"(ready with small edits|ready|revise)"
    r"(?=[\s`*_\"'.]*(?:$|\n)|[`*_\"']*\.[`*_\"']*\s)",
    re.IGNORECASE | re.MULTILINE,
)
```

(Do **not** use `re.VERBOSE` — it strips literal whitespace from the alternation `ready with small edits`, which silently breaks the regex.)

The trailing lookahead enforces value boundary with two accepted shapes:

- **Boundary A** (`[\s`*_\"'.]*(?:$|\n)`): rest of line is only emphasis marks, punctuation, and whitespace, then end-of-line. Covers `**Verdict: ready with small edits.**` and similar.
- **Boundary B** (`[`*_\"']*\.[`*_\"']*\s`): the value is followed by a sentence-terminating period (possibly wrapped in emphasis) and then whitespace. Covers `**Verdict: ready with small edits.** Full review written to …` — a real Claude variant observed 3× in the corpus.

Malformed values that match neither boundary are rejected: `Verdict: ready for review` (no period before ` for`), `Verdict: ready-ish` (hyphen is not `.` and `-` is not in boundary A's character class), `Verdict: ready with small edits pending changes` (after the longest alternation match `ready with small edits`, ` pending` matches neither boundary).

Update `parse_verdict` to:

1. First scan with `VERDICT_LINE_RE` (the existing `Overall verdict` regex). If any match, return the last.
2. If no match, scan with `VERDICT_LINE_BARE_RE`. If any match, return the last.
3. Otherwise return `(None, False)`.

This preserves the strict primary path. The bare form is only consulted when no `Overall verdict` line exists.

**2c. Mirror the bare form in `_VERDICT_HEADING_STYLE`.** Today the heading-style regex requires the literal word "Overall". Extend it (or add a sibling) so two-line `**Verdict**\n\nrevise` is normalised to `Verdict: revise` before `VERDICT_LINE_BARE_RE` runs. The qualifier `(?:Overall\s+)?` directly in front of `verdict` is the smallest delta.

### Worked examples

After both changes:

| Input | Normalised | Parse result |
|---|---|---|
| `**Overall verdict:** ready` | unchanged | ready (existing path) |
| `## Overall Verdict\n\n**revise** — text` | `## Overall Verdict: revise — text` | revise (existing path) |
| `**Verdict: ready with small edits.**` | unchanged | ready with small edits (new bare path) |
| `**Verdict**\n\nrevise` | `**Verdict: revise` | revise (new bare path + heading mirror) |
| `the previous round's verdict was revise` | unchanged | `(None, False)` — not line-anchored |
| `Overall verdict: looks fine to me` | unchanged | `(None, False)` — unchanged invalid behaviour |

## Tests

All in `skills/external-review/tests/`.

### New unit tests in `test_verdict.py`

- `test_bare_verdict_ready_with_small_edits` — `**Verdict: ready with small edits.**` → `ready with small edits`, valid.
- `test_bare_verdict_revise` — `**Verdict: revise.**` → `revise`, valid.
- `test_bare_verdict_with_trailing_prose` — `**Verdict: ready with small edits.** Full review written to /tmp/foo.md.` → `ready with small edits`, valid (mirrors a real fixture).
- `test_bare_verdict_not_matched_in_prose` — body containing `the previous round's verdict was revise` (no line-anchored `Verdict:` and no `Overall verdict:` line) → `(None, False)`.
- `test_overall_preferred_over_bare` — body containing both `**Verdict: revise**` near the top and `Overall verdict: ready` near the bottom → `ready` (Overall path wins, takes last match).
- `test_bare_verdict_rejects_extra_words_after_value` — `**Verdict: ready for review**` → `(None, False)` (value boundary violated by trailing word).
- `test_bare_verdict_rejects_hyphenated_value` — `Verdict: ready-ish` → `(None, False)`.
- `test_bare_verdict_rejects_qualified_value` — `Verdict: ready with small edits pending changes` → `(None, False)` (longest alternation matches `ready with small edits`, but trailing ` pending changes` fails the value-boundary lookahead).
- `test_parse_reformatted_verdict_helper` — direct call on the new `parse_reformatted_verdict(raw)` helper with a fenced + heading-style fixture round-trips to `("revise", True)`.

### New unit tests in `test_heading_style_verdict.py`

- `test_bare_heading_style_verdict_parses` — fake reviewer emits `**Verdict**\n\nready with small edits` → `verdict_valid=True`, `verdict="ready with small edits"`.

### Fixture-based regression

Add the following fixture files under `skills/external-review/tests/fixtures/` (create the directory):

- `claude-bare-verdict-ready-with-small-edits.md` — copied verbatim from `/home/simon/Dev/sigreer/multistore/docs/reviewer/p11-s5-final-guardrails-and-documentation-plan/r2-2026-05-19T0054-response.md`.
- `claude-heading-revise.md` — copied verbatim from `/home/simon/Dev/sigreer/multistore/docs/reviewer/p11-s5-final-guardrails-and-documentation-plan/r1-2026-05-19T0050-response.md`.

The implementer **must copy these into the repo**; do not reference them from the external `multistore` path at test time. Reference them in the new tests via `pathlib.Path` so future regressions are pinned to committed, version-controlled content.

### Existing tests

All 222 tests in `skills/external-review/tests/` must continue to pass without modification.

## Acceptance criteria

1. `python3 -m pytest skills/external-review/tests/` — all existing + new tests pass.
2. Manual replay: running `parse_reformatted_verdict(open(p).read())` against the copied fixture `claude-bare-verdict-ready-with-small-edits.md` returns `("ready with small edits", True)`. Replay against `claude-heading-revise.md` returns `("revise", True)`.
3. Single chokepoint: `parse_reformatted_verdict` exists and is called from both the automated round path (`external-reviewer.py:1403`) and the manual ingest path (`external-reviewer.py:1814`). Legacy manifest synthesis (`synthesize_manifest_from_legacy_files`) is documented as the one excluded call site.
4. No new dependencies, no new public CLI surface, no schema changes to `chain.json`.

## Risks & rollback

- **Risk:** `VERDICT_LINE_BARE_RE` over-anchored such that some legitimate variant is missed. Mitigation: leading class `^[\s>#*_`]*` covers whitespace, blockquote, heading markers, and bold/italic/code emphasis — the forms observed in the corpus. List-bullet variants (`- Verdict: ready`) are intentionally not matched; if they appear later, the leading class is the single place to extend. The fixture suite locks in the observed real variants.
- **Risk:** Two-pass parsing changes the verdict picked for a body containing both forms. Mitigation: `Overall verdict` is preferred; bare only used when Overall absent. Test `test_overall_preferred_over_bare` pins this.
- **Rollback:** Revert the touched commit; behaviour returns to pre-X10 strict matching. No data migration.

## Out of scope / follow-ups

- If the prompt change does not materially reduce the rate of heading-style verdicts in subsequent Claude chains, consider a more invasive prompt restructure (separate ticket).
- If a new unhandled variant appears, decide then whether to add it to the anchored regex or revisit the deferred loose-match fallback.
