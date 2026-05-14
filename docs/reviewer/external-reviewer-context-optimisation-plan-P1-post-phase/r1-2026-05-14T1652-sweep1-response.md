# Review — 2026-05-14-external-reviewer-context-optimisation-plan.md (post-phase, round 1)

- Target: `docs/plans/2026-05-14-external-reviewer-context-optimisation-plan.md`
- Request: `docs/reviewer/external-reviewer-context-optimisation-plan-P1-post-phase/r1-2026-05-14T1652-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Status: `failed (1)`

---

_Reviewer process failed; no stdout persisted._

---

## Reviewer stderr (tail, sanitised)

```text
ncremental_preamble`, cap `prior_response_text`, `merged_findings_text`, and `resolution_text` reads to 80 KB each (head + tail with a `[…N bytes elided…]` marker in between). Apply caps *after* §S1.6's failed-round skipping.
  129	4. **Global cap with deterministic preservation priority.** Add `--incremental-budget-chars` (default 400_000). Applied as the final step in `make_prompt` on incremental rounds. If the assembled prompt exceeds budget, sections are dropped/truncated in this order (lowest-priority dropped first):
  130	   1. Target preview (cut to 80 lines, then 40, then 0)
  131	   2. Diff body (cut to half, quarter, then 0; preserve the diff header note)
  132	   3. Resolution body (cut to 20 KB, then 8 KB)
  133	   4. Prior findings body (cut to 40 KB, then 16 KB)
  134	   5. **Never dropped:** review-mode preamble, chain summary table, finding-ID list, sentinel markers, REVIEW_PROMPT contract.
  135	   The result includes a trailing `<!-- budget-applied: ... -->` note describing what got trimmed. Tested by S3 item 13.
  136	5. **Tighten diff caps.** `compute_diff_section` enforces a single global cap on the whole diff block (already `--max-diff-lines`, default 2000) rather than per-subsection. Add a cap on untracked-file count (default 10) and per-untracked-file line cap (default 200).
  137	
  138	**Acceptance:** on a synthetic chain with spec + plan + TASKLIST as context, a 50 KB merged-findings file, a 4 KB resolution, and a 500-line diff, the round-2 prompt is under 200 KB. Tested by S3 item 13 (budget cap), item 12 (prior-text caps), item 10 (context-preview drop on incremental), and item 11 (target-preview trim on incremental).
  139	
  140	### S3 — Tests, docs, and skill update
  141	
  142	**Numbering note:** items here are referenced from S1/S2 acceptance gates by their item number. Renumbering during implementation requires a corresponding spec edit; do not silently re-order.
  143	
  144	1. **Test: failed-process verdict suppression** — simulate `reviewer-agent` returncode=1 with stderr containing the full prompt; assert `chain.json` round entry has `verdict_valid: false`, `returncode: 1`, `status: "failed"`, `merged_verdict: null`, and that the persisted response file is under 8 KB.
  145	2. **Test: failed sweep can't poison merged findings** — `--review-depth thorough` run where the sweep returncode=1 (stderr contains echoed prompt); assert `merged_findings` is built from the primary only, the sweep's body is not concatenated, and per the S1.7 truth table the top-level `status` remains `"ok"`.
  146	3. **Test: sentinel-stripping happy path** — feed reviewer stdout that begins with `actual review here`; assert the persisted response body contains only `actual review here` (no markers, no echoed prompt).
  147	4. **Test: sentinel-stripping truncated echo** — feed reviewer stderr containing only the **end** marker followed by trailing text (simulating a tail-truncated echo); assert the stripper deletes everything from the start of the stream up to and including the end marker. Symmetric case: stream contains only the start marker followed by content; assert deletion from start marker to end of stream.
  148	5. **Test: success-stderr is dropped or capped** — simulate a successful (returncode=0) reviewer run whose stderr contains the full prompt; assert the persisted response file does **not** contain the full prompt and the `## Reviewer stderr (tail)` section, if present, is ≤ 2 KB and has been sentinel-stripped first.
  149	6. **Test: failed-stderr cap is applied after sentinel-stripping** — simulate a failed reviewer run whose stderr is 20 KB of echoed prompt; assert the persisted stub's stderr-tail section is ≤ 4 KB **and** contains no `
ERROR: You've hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at 6:48 PM.
ERROR: You've hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at 6:48 PM.
```
