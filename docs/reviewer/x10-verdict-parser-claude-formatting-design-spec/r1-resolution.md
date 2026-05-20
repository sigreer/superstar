# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md` §Design.2b
- Verification: regex now includes a value-boundary lookahead `(?=[\s`*_\"'.]*(?:$|\n))` that rejects malformed values; spec §Tests adds three negative tests (`test_bare_verdict_rejects_extra_words_after_value`, `test_bare_verdict_rejects_hyphenated_value`, `test_bare_verdict_rejects_qualified_value`).

Notes:
The trailing class explicitly enumerates the punctuation/emphasis characters allowed after the captured value. The spec also documents the real-world trailing-prose case (`**Verdict: ready.** Full review written to …`) and clarifies how the lookahead handles it.

## F2
Status: fixed
Evidence:
- Files: `docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md` §Design.2a, §Acceptance
- Verification: spec now requires a `parse_reformatted_verdict(raw)` helper used at both the automated round path and the manual ingest path. Legacy manifest synthesis is explicitly excluded with a stated rationale (would re-write historical verdicts on first touch).

Notes:
A new test `test_parse_reformatted_verdict_helper` exercises the helper directly.

## F3
Status: fixed
Evidence:
- Files: `docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md` §Design.2b "Out of scope" note; §Risks
- Verification: risk text no longer claims list-bullet support. The "Out of scope" note states bullet-prefixed verdicts are not handled, with a single-point-of-extension comment for future need.

## F4
Status: fixed
Evidence:
- Files: `docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md` §Tests "Fixture-based regression"; §Acceptance criterion 2
- Verification: spec now names full source paths (`/home/simon/Dev/sigreer/multistore/docs/reviewer/p11-s5-final-guardrails-and-documentation-plan/r{1,2}-...response.md`) and explicit destination filenames under `skills/external-review/tests/fixtures/`. Acceptance criterion 2 references the copied fixtures by name, not the external path.
