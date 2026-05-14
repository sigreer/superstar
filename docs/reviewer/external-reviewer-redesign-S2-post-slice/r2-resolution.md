# Resolution for r2

Round 2 of the S2 chain. Reviewer returned `revise` with 2 findings
(0 blocking). Both findings are addressed below, along with a parser
gap surfaced while triaging the round.

- Verdict: `revise`
- Target: `docs/superstar/plans/2026-05-13-external-reviewer-redesign.md`
- Response: `docs/reviewer/external-reviewer-redesign-S2-post-slice/r2-2026-05-14T0228-response.md`

## F1
Status: fixed
Evidence:
- Commit: `b5d6181` (`docs(external-reviewer): retrofit resolution docs to spec-compliant format`)
- Files:
  - `docs/reviewer/external-reviewer-redesign-post-slice/r1-resolution.md`
  - `docs/reviewer/external-reviewer-redesign-post-slice/r2-resolution.md`
  - `docs/reviewer/external-reviewer-redesign-post-slice/r3-resolution.md`
  - `docs/reviewer/external-reviewer-redesign-post-slice/r4-resolution.md`
  - `docs/reviewer/external-reviewer-redesign-S2-post-slice/r1-resolution.md`
- Verification: each resolution now has `## F<n>` headings and
  `Status: fixed | waived | deferred` lines per finding, plus
  `Evidence:` blocks referencing commit SHAs. The Slice 3
  resolution-doc parser will be able to parse these.

Notes:
Resolution docs didn't follow the spec-mandated parseable contract.
The spec (`docs/superstar/specs/2026-05-13-external-reviewer-redesign-design.md`
lines 175 and 201) requires:
- One `## F<n>` heading per finding.
- A `Status: fixed | waived | deferred` line per finding.
- Optional `Evidence:` block.

The previous resolution docs used prose-only `**Resolution.**` /
`**Verdict:**`-bullet styles with no `Status:` lines. All five existing
resolution docs (S1 r1–r4 plus S2 r1) were rewritten to the spec
template. Existing prose was preserved as `Notes:` so context isn't
lost. The S2 r1 doc had four logical findings (F1, F2, F3, plus the
chain-routing fix); the routing fix is recorded as F4 so it has a
parseable Status line.

## F2
Status: fixed
Evidence:
- Commit: `a03ebab` (`docs(external-reviewer): backfill Slice 2 closeout note with doc commits`)
- Files: `docs/superstar/plans/2026-05-13-external-reviewer-redesign.md`
  (Slice 2 closeout note around line 3015)
- Verification: closeout note now lists `3aa3790` and `1df15e3` under
  a new "Documentation / closeout commits" subheading.

Notes:
Slice 2 closeout note missing commits. The closeout note listed the
three implementation commits and two post-review fix commits but
omitted `3aa3790` (Slice 2 checkbox flip + closeout note) and
`1df15e3` (S2 resolution doc). Both have been appended as
"Documentation / closeout commits". The test-count line was also
extended to note the post-r2-parser-fix count (`39 passed`).

## Parser fix
Status: fixed
Evidence:
- Commit: `50600d5` (`fix(external-reviewer): parse_findings accepts em-dash/hyphen/colon separators`)
- Files:
  - `skills/external-review/scripts/external-reviewer.py` (`PROSE_FINDING_RE`)
  - `skills/external-review/tests/test_findings.py` (three new tests)
  - `docs/reviewer/external-reviewer-redesign-S2-post-slice/chain.json`
    (round-2 `findings_count` / `blocking_findings_count` re-emitted)
- Verification:
  - `python3 -m pytest skills/external-review/tests/` → `39 passed`
    (up from 36).
  - `parse_findings` on the actual round-2 response now returns
    `(2, 0)`:
    ```bash
    python3 -c "
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location('er', 'skills/external-review/scripts/external-reviewer.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    print(m.parse_findings(Path('docs/reviewer/external-reviewer-redesign-S2-post-slice/r2-2026-05-14T0228-response.md').read_text()))
    "
    # (2, 0)
    ```

Notes:
Not a flagged finding but surfaced while triaging round 2. The
reviewer's round-2 response used `F1 — Important:` with an em-dash
separator. `PROSE_FINDING_RE` previously required a literal period+space
(`F1.`), so the response fell through to the unparseable branch and
the chain manifest recorded `findings_count: null`,
`blocking_findings_count: null`.

Fix: extend `PROSE_FINDING_RE` to accept `.`, `-`, `—`, or `:` as the
separator after the F-number (with optional surrounding whitespace).
Added three regression tests covering em-dash, hyphen, and colon
separators. Re-parsed the round-2 response and updated
`chain.json` so round 2 now records `findings_count: 2`,
`blocking_findings_count: 0` — matching this resolution's two
findings.

## Verification

```bash
python3 -m pytest skills/external-review/tests/
# 39 passed
```

```bash
python3 -c "
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('er', 'skills/external-review/scripts/external-reviewer.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(m.parse_findings(Path('docs/reviewer/external-reviewer-redesign-S2-post-slice/r2-2026-05-14T0228-response.md').read_text()))
"
# (2, 0)
```
