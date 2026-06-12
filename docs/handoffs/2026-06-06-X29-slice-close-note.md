# X29 slice-close note — evidence for post-slice review

Implementation of `docs/plans/2026-06-06-X29-timeline-generator.md` (14 TDD tasks) is complete on branch `worktree-x29-visual-work-history-timeline-generator`. Each task went through implementer → spec-compliance review → code-quality review. This note records the authorized deviations from the plan's verbatim code (all review-driven, all tested) and the acceptance evidence, so they are not mistaken for drift.

## Review-driven deviations from the plan's verbatim listings

1. **T5 (`model.py` replay merge)** — `closed` picks the LAST terminal transition via `reversed()`, making reopen sequences safe. Regression test added.
2. **T6 (`model.py` overrides)** — fail-loud validation of override value types: non-string/null dates, non-bool `exclude`, non-str `display_title` all `SystemExit`. Tests added.
3. **T10 (`render.py` HTML emission)** — close-ring label includes the phase title (`{key} — {title} {label} · {date}`). Necessary: a close-only phase renders only a ring, and the plan's own test asserts the title appears in the HTML; verified the plan-verbatim code fails its own test. Also one cosmetic, behaviorally-identical rewording (`strftime` call instead of f-string format spec) at the `span_text` line.
4. **T11 (`test_cli.py`)** — `test_end_to_end` pinned to `TZ=UTC` via a local `utc_tz` fixture (monkeypatch + `time.tzset()`, restored on teardown). The plan's test was empirically TZ-flaky: minute-precision upgrade depends on the replay timestamp's local calendar date, so the test failed deterministically at UTC+8 and beyond.
5. **T13 pre-fix (`backfill.py`)** — `_PHASE_HEAD_RE` backticks made optional: multistore's real legacy `P3-editor-grade-cms.md` heading has no backticks around `DONE 2026-05-04` and was silently dropped. Regression test added.
6. **T13 (`backfill.py` rewrite)** — two bugs in the plan's prescribed logic, found by empirical dry-runs against this repo and multistore:
   - started-fill could produce `started > closed` (clamp uses "latest close among all lower-numbered phases", wrong once phases ran in parallel; raw mined dates can also postdate retroactive closes). Guard added: skip the fill when the candidate exceeds the object's own `closed`. 6 real bad entries across the two repos eliminated; 3 regression tests.
   - `json.dumps` lacked `ensure_ascii=False`, deviating from tasktool's canonical serializer and churning untouched `—`/`✅` lines in dry-run diffs. Fixed; regression test.

### Acceptance-driven additions (human visual gate)

Post-Task-14 changes driven by the human partner's browser eyeball check; each was spec-reviewed and quality-reviewed in-loop:

- `267842e` — single-line slice cards with hover/click expansion.
- `e5c0594` — older-item bug fixes: phase_span slice-close fallback, anchor-aware quiet gaps, no dangling "started —", cancelled-rule regression tests.
- `c9d6cc0` — sequential layout pass + phase prominence.
- `ff2d02e` — direction toggle with newest-at-top default.

## Known, deliberately deferred limitations (documented, not bugs introduced)

- `_SLICE_HEAD_RE` only matches `## S<n> — title ✅ \`DONE date\``-style headings. Real multistore legacy archives also use h3 headings, alphanumeric slice IDs (`S2a`), and bullet-list slices, mostly date-less — those are not backfilled. Broadening was descoped as design work beyond a review fix; multistore backfill is dry-run-only in this repo and gated by the human eyeball checkpoint (plan Task 14 Step 5). Phase-level closes — the load-bearing datum — are recovered for 8/8 multistore legacy phases after deviation 5.
- Minor quality-review nits deferred as plan errata: malformed-overrides JSON and missing output dir produce raw tracebacks in `timeline.py`; `read_text`/`write_text` use locale default encoding in `backfill.py`; `test_existing_slices_not_touched` has a conditional assert; `plan_rewrites` docstring slightly over-narrows the started-fill scope.

## Acceptance evidence (plan Task 14)

- Timeline suite: 95/95 passed (73 plan tests + 22 review/acceptance-driven tests).
- Full default-discovery suite: the plan's Step 1 criterion (`python3 -m pytest -q` all PASS) is **met outright** — **1224 passed, 0 failed, 0 errors** (exit code 0) in a clean shell at worktree HEAD `ff2d02ef7066cb6373e62c8ec8f9f9dc3be4123f`. The earlier baseline-exception framing ("109 failed + 23 errors, byte-identical to main") is **superseded**: those failures were an environment artifact — the `SUPERSTAR_SUBAGENT_ROLE` env var (exported by the subagent-role protocol in the shells that ran the evidence) trips the tasktool mutation guard at `tools/tasktool/commands.py:880-888` inside the test processes. With the var unset the suite is fully green; with it set, exactly the 132 documented ids fail. The byte-identical-to-main comparison remains valid (the artifact affected both sides equally; zero failures in `tools/timeline` either way). Durable evidence with the correction and the clean-run summary: `docs/handoffs/2026-06-06-X29-acceptance-evidence/`.
- Rendered this repo (`/tmp/superstar-timeline.html`, exit 0) and multistore (`/tmp/multistore-timeline.html`, exit 0; minute-precision `15:51` present, `x-node` markup present). Multistore now renders with the post-acceptance sequential layout; renders were verified post-layout-change by the in-loop reviewers.
- Backfill dry-run vs multistore: 17 file diffs, zero `started > closed`, zero unicode-escape churn, both repos verified unmutated.
- Human browser eyeball of both HTML files: requested from the human partner, pending in parallel with this review.

## Hard-constraint conformance

- Python 3 stdlib only; git via subprocess. Verified no third-party imports.
- No skill, hook, CLAUDE.md, or tasktool-help reference to the tool.
- Output HTML single-file, self-contained (tested: no `http://`/`https://`/`src=`).
- `timeline.py` read-only (verified empirically); only `backfill.py --write` mutates archive files, and `--write` was never run against any real repo.
