# Resolution for r3

Round 3 of the S2 chain. Reviewer returned `revise` with 2 findings
(0 blocking). F1 is a self-referential procedural complaint that
resolves naturally when this round closes ready; F2 is a substantive
staleness item addressed below. A parser robustness gap surfaced while
triaging the round is also recorded.

- Verdict: `revise`
- Target: `docs/superstar/plans/2026-05-13-external-reviewer-redesign.md`
- Response: `docs/reviewer/external-reviewer-redesign-S2-post-slice/r3-2026-05-14T0236-response.md`

## F1
Status: addressed-by-next-round
Evidence:
- The finding states "Slice 2 is not closed: latest S2 review verdict
  is still `revise`, and round 3 is only an untracked request." This
  is structurally self-referential: by definition the request cannot
  be tracked nor a round-3 manifest entry populated until a response
  has been received and resolved. Once round 4 returns
  `ready` / `ready with small edits` and this resolution is wired into
  the manifest, the closeout condition F1 describes will hold.
- The r3 request and response are now both tracked, this resolution
  doc populates the round-3 manifest `resolution` slot, and the round
  3 `findings_count` / `blocking_findings_count` are emitted as
  `(2, 0)` after the parser fix below.

Notes:
The reviewer is increasingly raising self-referential procedural
complaints across rounds (the round cannot be closed because the round
is open). Per the round-3 fix-subagent brief, no further action is
required for F1 — it will resolve when the next round returns ready.

## F2
Status: fixed
Evidence:
- Commit: this round's bundle.
- Files: `docs/superstar/plans/2026-05-13-external-reviewer-redesign.md`
  (Slice 2 closeout note, new "Post-r2 fix commits" sub-heading).
- Verification: the closeout note now records the five
  post-round-2-resolution commits the reviewer flagged as missing
  (`50600d5`, `b5d6181`, `a03ebab`, `f56c896`, `bb679ad`) under a
  dedicated sub-heading so the chain's evolution is visible in the
  plan.

Notes:
F2 reads: "The Slice 2 closeout note is stale relative to the repo
state." The closeout note previously listed only the round-1
resolution and stopped there, so it read as if round 1 had been the
final post-slice gate. The five commits produced between the round-1
resolution and the round-3 request have been appended under a new
"Post-r2 fix commits" sub-heading.

## Parser fix
Status: fixed
Evidence:
- Commit: this round's bundle.
- Files:
  - `skills/external-review/scripts/external-reviewer.py`
    (`PROSE_FINDING_RE`, `_collect_findings`)
  - `skills/external-review/tests/test_findings.py` (two new tests)
  - `docs/reviewer/external-reviewer-redesign-S2-post-slice/chain.json`
    (round-3 `findings_count` / `blocking_findings_count` populated)
- Verification:
  - `python3 -m pytest skills/external-review/tests/` → `41 passed`
    (up from 39).
  - `parse_findings` on the actual round-3 response now returns
    `(2, 0)`:
    ```bash
    python3 -c "
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location('er', 'skills/external-review/scripts/external-reviewer.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    print(m.parse_findings(Path('docs/reviewer/external-reviewer-redesign-S2-post-slice/r3-2026-05-14T0236-response.md').read_text()))
    "
    # (2, 0)
    ```

Notes:
Not a flagged finding but surfaced while triaging round 3. The
reviewer's r3 response used `F1. **<heading>**` — `F<n>.` followed by a
markdown-bold heading with no severity word in between. The previous
`PROSE_FINDING_RE` required `(Blocking|Important|Minor|...)` followed
by `\b` after the separator, and the leading `**` defeated the
optional-severity branch (no word boundary between the separator
whitespace and the `*` glyph). The response therefore fell through to
the unparseable branch and the manifest recorded
`findings_count: null` / `blocking_findings_count: null`.

Fix:
- Relax `PROSE_FINDING_RE` to `^F(\d+)\s*[.\-—:]\s+(.*)$` — the
  separator alternatives are preserved, and the trailing capture
  group is unconstrained so any heading text (including a markdown-
  bold wrapper) matches. The severity assumption is removed from the
  regex.
- In `_collect_findings`, strip an optional leading `**` from the
  captured rest of the line and re-check for an inline severity word
  via `PROSE_SEVERITY_RE`. If no inline severity is found, scope the
  finding's paragraph from its heading line up to the first blank
  line (markdown paragraph break) or the next prose finding, and
  scan that scoped paragraph for `Blocking`. The tight paragraph
  scope avoids sweeping in `blocking` mentions from quoted previews
  further down the response.
- Two new regression tests cover the markdown-bold heading form:
  one with no inline severity (asserts `(2, 0)`), and one with an
  immediately-following `Blocking:` line in the paragraph body
  (asserts `(2, 1)`).
- Re-parsed the round-3 response and updated `chain.json` so round 3
  now records `findings_count: 2`, `blocking_findings_count: 0`,
  matching this resolution's two findings.

## Verification

```bash
python3 -m pytest skills/external-review/tests/
# 41 passed
```

```bash
python3 -c "
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('er', 'skills/external-review/scripts/external-reviewer.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(m.parse_findings(Path('docs/reviewer/external-reviewer-redesign-S2-post-slice/r3-2026-05-14T0236-response.md').read_text()))
"
# (2, 0)
```
