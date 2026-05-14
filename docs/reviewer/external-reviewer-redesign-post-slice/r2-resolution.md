# Round 2 resolution

## F1 — parse_findings bugs (prose style + crash sentinel over-trigger)
- **Verdict:** fixed
- **What changed:**
  - `skills/external-review/scripts/external-reviewer.py`: replaced the two-regex parser with `_collect_findings()`, which now recognises three styles:
    1. **Prose style** (`F1. Blocking: ...`, `F2. Important: ...`) — the form the live reviewer actually produces. Severity is captured inline from the same line, so blocking count is derived per-finding, not by a global re-scan.
    2. **Heading style** (`## F1`) — retained; blocking count falls back to `^Severity:\s*blocking` lines, matching pre-existing test fixtures.
    3. **Bullet style** (`- F1: ...`) — retained as the last-resort form; tightened from `[-*]?` to `[-*]` so prose lines aren't mis-classified as bullets.
  - Findings are now keyed by F-number and de-duplicated within a single response. This matters because real reviewer responses echo their own prompt content, so `F1./F2./F3.` typically appears twice in the artefact — once as the live finding, once inside an embedded preview. De-duplication makes the count reflect distinct findings.
  - Style precedence is now **prose → heading → bullet**. Previous order was heading-first, which caused live responses (where `## F1` appears inside echoed test fixtures or embedded plan content) to be parsed as heading-style and miscount.
  - The `"reviewer crashed"` sentinel was anchored: the new `CRASH_SENTINEL_RE` requires the phrase at the start of a line (optionally prefixed by `Status:`). It only fires when no findings were parsed in any style. This stops it from triggering when the phrase appears inside fenced code blocks or quoted excerpts (the script source contains the literal string).
- **Tests added** (`skills/external-review/tests/test_findings.py`):
  - `test_prose_style_findings_counted` — asserts `F1. Blocking / F2. Blocking / F3. Important` → `(3, 2)`.
  - `test_crash_phrase_in_quoted_content_does_not_block_parse` — embeds `'reviewer crashed'` inside a fenced code block alongside real prose findings, asserts the findings are still counted.
- **Verification on real artefacts:** ran `parse_findings` against both completed response files:
  - `r1-2026-05-14T0124-response.md` → `(3, 2)` ✅
  - `r2-2026-05-14T0129-response.md` → `(3, 2)` ✅
- **chain.json re-emission:** the round-1 entry's `findings_count` / `blocking_findings_count` were `null` because the bug was present when round 1 was recorded. After the parser fix, both rounds in `docs/reviewer/external-reviewer-redesign-post-slice/chain.json` were re-parsed and updated in place; both now read `findings_count: 3`, `blocking_findings_count: 2`.
- **Test suite:** `python3 -m pytest skills/external-review/tests/` → `21 passed` (19 baseline + 2 new).
- **Commit:** `43f0aff` (parser fix + tests bundled in the same commit).

## F2 — untracked planning artefacts
- **Verdict:** fixed
- **What changed:**
  - Committed `docs/superstar/specs/2026-05-13-external-reviewer-redesign-design.md` (the Slice 1 design spec) and `docs/handoffs/2026-05-13-external-reviewer-redesign-prompt.md` (the coordinator handoff). Both were intentional Slice 1 deliverables that remained untracked through round 1.
  - The Slice 1 closeout note in the plan was updated to disclose these commits explicitly.
  - The current in-flight round's `r2-*-request.md` / `r2-*-response.md` are deliberately **not** committed in this resolution — they will be committed alongside this resolution doc once the round 2 fix work lands as a single coherent commit. This matches the chain-folder convention used in round 1.
- **By-design note:** F2 also flagged that `r2-*request.md` isn't in `chain.json`. That is expected: `chain.json` is appended to only after the reviewer finishes a round (the request file is written before the reviewer runs, the manifest entry is written after). During an in-flight round the request file may appear untracked with no manifest entry; this resolves when the round closes. The Slice 1 closeout note was extended to document this expectation.
- **Commit:** `591a20c` (planning artefacts + closeout-note edits + Slice 1 checkbox ticks bundled).

## F3 — Slice 1 checkboxes visually incomplete
- **Verdict:** fixed
- **What changed:** ticked all 31 `- [ ]` step checkboxes inside Slice 1 (tasks 1.1 through 1.6) in `docs/superstar/plans/2026-05-13-external-reviewer-redesign.md`, switching them to `- [x]`. Slice 2+ checkboxes are intentionally left open.
- **Commit:** `591a20c` (bundled with the F2 planning-artefact commit).
