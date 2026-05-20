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

**2a. Centralise normalisation.** Today, `_reformat_response` is called only from the manual `run_ingest_response` path (line 1781). The automated round path at line 1403 inlines just `_VERDICT_HEADING_STYLE.sub(...)`. Make both paths go through one normaliser. Concretely: change line 1403–1405 to `verdict, valid = parse_verdict(_reformat_response(body))`. `_reformat_response` already strips outer code fences and rewrites heading-style verdicts; sharing it gives a single place for future normalisations.

**2b. Add anchored bare-`Verdict:` matching.** Introduce a second regex `VERDICT_LINE_BARE_RE` that matches bare `Verdict:` **only when line-anchored** (after optional leading whitespace and markdown emphasis/heading marks). Anchoring eliminates the prose false-positive risk (e.g. "the previous round's verdict was revise"). Empirical confirmation: zero mid-prose matches were found across the `multistore/docs/reviewer/` corpus.

Proposed shape:

```python
VERDICT_LINE_BARE_RE = re.compile(
    r"^[\s>#*_`]*verdict\s*[`*_\"']*\s*[:\-]\s*[`*_\"'\s]*"
    r"(ready with small edits|ready|revise)[`*_\"'.\s]*",
    re.IGNORECASE | re.MULTILINE,
)
```

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

### New unit tests in `test_heading_style_verdict.py`

- `test_bare_heading_style_verdict_parses` — fake reviewer emits `**Verdict**\n\nready with small edits` → `verdict_valid=True`, `verdict="ready with small edits"`.

### Fixture-based regression

Add `tests/fixtures/claude-bare-verdict-revise.md` and `claude-heading-revise.md` captured (verbatim or trimmed) from the failed `multistore` rounds. Reference them in the new tests via `pathlib.Path` so future regressions are pinned to real-world content.

### Existing tests

All 222 tests in `skills/external-review/tests/` must continue to pass without modification.

## Acceptance criteria

1. `python3 -m pytest skills/external-review/tests/` — all existing + new tests pass.
2. Manual replay: running `parse_verdict(_reformat_response(open(p).read()))` against the captured `r2-2026-05-19T0054-response.md` returns `("ready with small edits", True)`. Replay against `r1-2026-05-19T0050-response.md` still returns `("revise", True)`.
3. Single chokepoint: there is only one call site that combines normalisation + `parse_verdict` for response bodies (the manual ingest and automated round paths share it).
4. No new dependencies, no new public CLI surface, no schema changes to `chain.json`.

## Risks & rollback

- **Risk:** `VERDICT_LINE_BARE_RE` over-anchored such that some legitimate variant is missed. Mitigation: anchoring uses `^[\s>#*_`]*` which matches list bullets, heading markers, and bold emphasis. The fixture suite locks in the observed real variants.
- **Risk:** Two-pass parsing changes the verdict picked for a body containing both forms. Mitigation: `Overall verdict` is preferred; bare only used when Overall absent. Test `test_overall_preferred_over_bare` pins this.
- **Rollback:** Revert the touched commit; behaviour returns to pre-X10 strict matching. No data migration.

## Out of scope / follow-ups

- If the prompt change does not materially reduce the rate of heading-style verdicts in subsequent Claude chains, consider a more invasive prompt restructure (separate ticket).
- If a new unhandled variant appears, decide then whether to add it to the anchored regex or revisit the deferred loose-match fallback.
