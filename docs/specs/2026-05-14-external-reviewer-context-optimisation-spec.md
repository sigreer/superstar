# Spec — external-reviewer context optimisation & chain integrity

- **Status:** ready (incorporates `--kind spec` r1 + r2 review findings; r2 verdict `ready with small edits` applied)
- **Created:** 2026-05-14
- **Owner:** sigreer
- **Target component:** `skills/external-review/scripts/external-reviewer.py` (+ `skills/external-review/SKILL.md`, `skills/external-review/tests/`)
- **Related artefacts:**
  - Draft brief: `docs/_drafts/context-optimisation-brief.md`
  - Brief review chain: `docs/reviewer/context-optimisation-brief-design/`
  - Smoking-gun chain: `/home/simon/Dev/sigreer/multistore/docs/reviewer/p10-s3-x39-tailwind-screen-aliases-P10-S3-post-slice/`

## 1. Problem

Incremental rounds in an external-review chain currently fail in two compounding ways:

### 1.1 Chain semantic corruption (primary defect)

When the configured reviewer command exits non-zero, `write_review_artifact` (`external-reviewer.py:440-473`) writes `result.stdout` and the full `result.stderr` verbatim into the round's response file. The OpenAI Codex–backed `reviewer-agent` emits its session banner and the **entire echoed input prompt** on stderr. The next stage of the script then:

1. Parses the response body for a verdict (`run_one_reviewer` → `parse_verdict`).
2. Records the parsed verdict, `verdict_valid`, and `merged_verdict` into `chain.json` with no awareness that the process exited non-zero.
3. Persists no `returncode` or `status` field on the round entry.

The downstream effect, observed empirically on the multistore chain `p10-s3-x39-tailwind-screen-aliases-P10-S3-post-slice`:

```
round=2  verdict=revise  valid=True  ← reviewer process FAILED (exit 1)
round=3  verdict=revise  valid=True  ← reviewer process FAILED
round=4  verdict=revise  valid=True  ← reviewer process FAILED
```

Every "verdict" past r1 was extracted from echoed prompt text. The chain looks healthy to any consumer of `chain.json` while being entirely fabricated.

### 1.2 Recursive prompt bloat (secondary defect)

The corrupted response files are then slurped whole into the next round's preamble:

- `build_incremental_preamble` (`external-reviewer.py:277-285`) reads `r{N-1}-merged-findings.md` (preferred) or `r{N-1}-response` (fallback) with no size cap.
- `make_prompt` (`external-reviewer.py:348-353`) re-embeds the full target preview and every `--context` file preview on every incremental round, on top of the preamble.
- `compute_diff_section` caps each subsection independently — no global cap on the diff block, no cap on number of untracked files.

Observed size progression on the same chain (one failed r2 was enough to poison the whole chain):

| File | Bytes |
|---|---|
| `r1-merged-findings.md` | 594,637 |
| `r1-resolution.md` | 4,155 |
| `r2-…-request.md` | 886,686 |
| `r2-…-response.md` (failed, stderr-echoed) | 887,637 |
| `r3-…-request.md` | 1,293,203 (exceeds OpenAI's 1,048,576 limit) |
| `r4-…-request.md` | 1,938,265 |

The literal prompt phrase `"You are continuing an existing review chain"` (one occurrence in the template) appears 0 / 0 / 2 / 6 / **14** times across r1-primary / r1-sweep1 / r2 / r3 / r4 response files — confirming 2× compounding per round.

### 1.3 Self-demonstration

The very `--kind design` review that vetted the precursor brief for this spec produced a **1.22 MB response file** for a successful (returncode 0) round. Codex echoed the entire stdin on stderr; `write_review_artifact` dumped it whole. This bug fires even on the happy path — only the prompt-size symptom is gated by a non-zero exit.

## 2. Goals

1. **Chain integrity:** a failed reviewer process can never produce a recorded verdict, valid finding, or trusted merged_verdict in `chain.json`. Failed bodies never enter merged findings or downstream parsing.
2. **Prompt size:** typical incremental round (round 2+) on a 3-context chain stays under 250 KB regardless of chain depth. Failed-round artefacts contribute O(KB), not O(MB).
3. **Backwards compatibility:** JSON output contract and exit codes unchanged. Existing chain folders continue to work (soft-migration where needed). No new env vars; one new flag (`--incremental-budget-chars`) with auto default.
4. **Self-evidencing tests:** the failure modes from §1 are reproduced and asserted against in unit tests.

## 3. Non-goals

- Changes to broad-round (r1) prompt structure or `--max-lines` defaults. Round 1 is not broken.
- New env vars (`AGENT_REVIEWER_TRANSPORT` already exists; no more).
- Changes to JSON output keys or exit-code values. New keys may be added under `reviewers[]` and `rounds[]` but existing keys keep their semantics.
- New third-party dependencies.
- Changes to `reviewer-agent` itself — the bridge must remain backend-agnostic.

## 4. Scope (3 slices)

### S1 — Failure-truth + echo containment (root-cause fix)

The keystone slice. Without this, any size optimisation only delays the corruption.

**Operation order for response persistence (applies to every reviewer invocation, success or failure):**

1. Capture raw `result.stdout` and `result.stderr` from `subprocess.CompletedProcess`.
2. Apply sentinel-stripping (item S1.5) to **both** streams in full — *before* any size cap, tail, or truncation. This ensures a tail-cap operation cannot leave the end of an echoed prompt without its `:start -->` marker.
3. Apply size caps per the rules below.
4. Write the assembled response file.

Now the specific items:

1. **Persist process status in `chain.json`.** Extend each `reviewers[]` entry and each `rounds[]` entry with three new keys: `returncode: int | null`, `status: "ok" | "failed" | "unknown"`. The `"unknown"` value is reserved for legacy entries migrated from pre-S1 manifests. New entries always record `"ok"` or `"failed"` based on `result.returncode`. Soft-migrate older entries on first touch: missing `returncode` becomes `null` and `status` becomes `"unknown"`; do not infer retroactive truth from existing `verdict_valid` flags.
2. **Failed rounds force `verdict_valid: false`.** In `run_one_reviewer`, if `result.returncode != 0`: set the reviewer's `verdict = null`, `verdict_valid = false`, `findings_count = 0`, regardless of what `parse_verdict` extracts from the body. The same applies to `merged_verdict` aggregation per the truth table below. (This is stricter than the current `verdict_valid: false → treat as revise` policy, which assumes the reviewer at least produced a real response.)
3. **Sanitise stdout and stderr on every round, success or failure.** In `write_review_artifact`:
   - **Success (`returncode == 0`):** persist sentinel-stripped stdout as the review body. Stderr is dropped entirely *unless* it remains non-empty after sentinel-stripping, in which case its **tail is capped at 2 KB** and appended under `## Reviewer stderr (tail)`. Rationale: the self-demonstration in §1.3 shows even successful runs echo the prompt on stderr; storing the full stderr serves no diagnostic purpose once sentinels are stripped.
   - **Failure (`returncode != 0`):** persist a short failure stub — header, returncode, `## Reviewer stderr (tail, sanitised)` with the **sentinel-stripped stderr tail capped at 4 KB**, and no stdout body. Successful reviewers attach their review under their own heading; failed reviewers attach only the stderr tail.
4. **Skip failed bodies in merged-findings construction.** `write_merged_findings` (`external-reviewer.py:572`-ish) only concatenates bodies from reviewers with `status == "ok"`. If every reviewer in the round failed, no merged-findings file is written and `chain.json` records `merged_findings: null`.
5. **Sentinel-wrap the prompt.** `make_prompt` emits `<!-- superstar-prompt:start -->` and `<!-- superstar-prompt:end -->` markers at the very top and very bottom of the assembled prompt body. The stripper removes any range of text bounded by those markers (inclusive of the markers themselves) from a reviewer output stream. If only an end marker is found with no start marker (e.g. tail-truncated echo) the stripper deletes from the beginning of the stream up to and including the end marker. If only a start marker is found, it deletes from the start marker to the end of the stream. This makes the stripper robust against arbitrary truncation.
6. **Skip parsing failed artefacts in preamble construction.** `build_incremental_preamble` consults `chain.json` for the prior round's `status`. If `status` is `"failed"` or `"unknown"`, walk backward to the last `status: "ok"` round and embed *that* round's merged-findings instead, prefixed with a short note: `Note: rounds {N-1}...{K+1} were process failures or pre-S1 entries; skipped.`. If no successful prior round exists, fall back to the chain summary table only. `"unknown"` is treated as untrusted by default to prevent legacy poisoned manifests from leaking through.

#### S1.7 — Multi-reviewer truth table

When `--review-depth thorough` or `exhaustive` runs sweeps alongside the primary, top-level JSON aggregation and process exit are governed by this table:

| Primary status | Sweep status(es) | Top-level `status` | Top-level `returncode` | `verdict_valid` | `merged_verdict` | Process exit |
|---|---|---|---|---|---|---|
| ok | all ok | `ok` | 0 | per merged verdict | computed | 0 |
| ok | some failed | `ok` | 0 | per merged verdict computed over ok reviewers only | computed (ok reviewers only) | 0 |
| ok | all failed | `ok` | 0 | per primary verdict | primary's verdict | 0 |
| failed | any | `failed` | primary's returncode | `false` | `null` | primary's returncode |
| failed | all | `failed` | primary's returncode | `false` | `null` | primary's returncode |

Rule of thumb: **primary failure is the only condition that flips top-level status to `failed`.** A sweep failure is recorded per-reviewer and excluded from merged-findings, but the round as a whole remains valid if the primary succeeded. This preserves the current `main()` behaviour at `external-reviewer.py:1155` (return `primary.returncode`) while adding correct per-reviewer truth.

#### S1.8 — Process-failed prior round gate behaviour

The existing resolution-required gate at `external-reviewer.py:871` blocks round N+1 on `post-slice` / `post-phase` chains when the prior round has `verdict_valid: false`, unless `r{N-1}-resolution.md` exists or `--allow-missing-resolution` is passed. A process failure has no findings to resolve, so without specific handling the chain would deadlock.

**Rule:** when the prior round's `status` is `"failed"` (i.e. the reviewer process failed, not "the reviewer returned `revise`"), the resolution-required gate is **bypassed** for the next round. The script emits a one-line stderr notice: `Note: prior round r{N-1} was a process failure (returncode={rc}); resolution gate bypassed.`. The next round proceeds as a re-attempt at the same review, not as a fix-and-re-review. No new exit code, no new flag.

Distinction from `"unknown"`: legacy entries with `status: "unknown"` do **not** bypass the gate — the operator must inspect the legacy state explicitly and pass `--allow-missing-resolution` if appropriate. Only fresh `"failed"` entries (with a recorded `returncode != 0`) earn the bypass.

**Acceptance:** the tests added in S3 items 1, 9, and 14 pass — item 1 asserts `chain.json` records `verdict_valid: false`, `returncode != 0`, `status: "failed"` after a failed reviewer turn; item 9 asserts r3 submission proceeds without `--allow-missing-resolution` after a `status: "failed"` r2; item 14 asserts r3-request bytes < 250 KB and contains no echoed-prompt phrase. Items 3, 4, 5, 6 cover sentinel-stripping under success, failure, and truncation. Item 2 covers multi-reviewer truth-table behaviour for sweeps.

### S2 — Incremental prompt diet

Independent of S1's correctness fixes; reduces typical size further. Ship after S1 lands.

1. **Drop context previews on incremental.** In `make_prompt`, when `mode == "incremental"`, skip the `## Context Previews` block (`external-reviewer.py:350-353`) entirely. The preamble already names context files by path and the REVIEW_PROMPT body tells the reviewer to read from disk.
2. **Trim target preview on incremental.** Cap the target preview to `min(max_lines, 150)` lines when `mode == "incremental"`. Broad-round behaviour unchanged.
3. **Cap prior-text reads.** In `build_incremental_preamble`, cap `prior_response_text`, `merged_findings_text`, and `resolution_text` reads to 80 KB each (head + tail with a `[…N bytes elided…]` marker in between). Apply caps *after* §S1.6's failed-round skipping.
4. **Global cap with deterministic preservation priority.** Add `--incremental-budget-chars` (default 400_000). Applied as the final step in `make_prompt` on incremental rounds. If the assembled prompt exceeds budget, sections are dropped/truncated in this order (lowest-priority dropped first):
   1. Target preview (cut to 80 lines, then 40, then 0)
   2. Diff body (cut to half, quarter, then 0; preserve the diff header note)
   3. Resolution body (cut to 20 KB, then 8 KB)
   4. Prior findings body (cut to 40 KB, then 16 KB)
   5. **Never dropped:** review-mode preamble, chain summary table, finding-ID list, sentinel markers, REVIEW_PROMPT contract.
   The result includes a trailing `<!-- budget-applied: ... -->` note describing what got trimmed. Tested by S3 item 13.
5. **Tighten diff caps.** `compute_diff_section` enforces a single global cap on the whole diff block (already `--max-diff-lines`, default 2000) rather than per-subsection. Add a cap on untracked-file count (default 10) and per-untracked-file line cap (default 200).

**Acceptance:** on a synthetic chain with spec + plan + TASKLIST as context, a 50 KB merged-findings file, a 4 KB resolution, and a 500-line diff, the round-2 prompt is under 200 KB. Tested by S3 item 13 (budget cap), item 12 (prior-text caps), item 10 (context-preview drop on incremental), and item 11 (target-preview trim on incremental).

### S3 — Tests, docs, and skill update

**Numbering note:** items here are referenced from S1/S2 acceptance gates by their item number. Renumbering during implementation requires a corresponding spec edit; do not silently re-order.

1. **Test: failed-process verdict suppression** — simulate `reviewer-agent` returncode=1 with stderr containing the full prompt; assert `chain.json` round entry has `verdict_valid: false`, `returncode: 1`, `status: "failed"`, `merged_verdict: null`, and that the persisted response file is under 8 KB.
2. **Test: failed sweep can't poison merged findings** — `--review-depth thorough` run where the sweep returncode=1 (stderr contains echoed prompt); assert `merged_findings` is built from the primary only, the sweep's body is not concatenated, and per the S1.7 truth table the top-level `status` remains `"ok"`.
3. **Test: sentinel-stripping happy path** — feed reviewer stdout that begins with `<!-- superstar-prompt:start -->...<!-- superstar-prompt:end -->actual review here`; assert the persisted response body contains only `actual review here` (no markers, no echoed prompt).
4. **Test: sentinel-stripping truncated echo** — feed reviewer stderr containing only the **end** marker followed by trailing text (simulating a tail-truncated echo); assert the stripper deletes everything from the start of the stream up to and including the end marker. Symmetric case: stream contains only the start marker followed by content; assert deletion from start marker to end of stream.
5. **Test: success-stderr is dropped or capped** — simulate a successful (returncode=0) reviewer run whose stderr contains the full prompt; assert the persisted response file does **not** contain the full prompt and the `## Reviewer stderr (tail)` section, if present, is ≤ 2 KB and has been sentinel-stripped first.
6. **Test: failed-stderr cap is applied after sentinel-stripping** — simulate a failed reviewer run whose stderr is 20 KB of echoed prompt; assert the persisted stub's stderr-tail section is ≤ 4 KB **and** contains no `<!-- superstar-prompt:start -->` / `:end -->` markers (proves strip-before-cap ordering).
7. **Test: preamble walks back past failed rounds** — chain with r1 ok, r2 failed (returncode=1), r3 building; assert r3 preamble cites r1's merged-findings with the "skipped failures" note, not r2's response.
8. **Test: preamble treats `status: "unknown"` as untrusted** — chain.json with a legacy entry (no `returncode`, no `status` → migrated to `status: "unknown"`); assert the preamble does **not** embed that round's response body and emits the same skip note.
9. **Test: process-failed prior round bypasses resolution gate** — post-slice chain where r2 has `status: "failed"`; submit r3 without `--allow-missing-resolution` and without `r2-resolution.md`; assert exit code is not 3 and the gate-bypass notice appears on stderr.
10. **Test: incremental prompt drops context previews** — assert `## Context Previews` heading absent in `mode=="incremental"` prompts; assert it is still present in `mode=="broad"`.
11. **Test: target preview trimmed on incremental** — assert preview ≤ 150 lines on incremental; broad round preview ≤ default `max_lines`.
12. **Test: prior-text caps applied** — feed a 1 MB merged-findings file; assert embedded segment ≤ 80 KB with the elision marker present.
13. **Test: budget cap preserves priority order** — assemble a prompt that exceeds `--incremental-budget-chars`; assert REVIEW_PROMPT contract, chain summary table, sentinel markers, and finding-ID list are intact; assert the lowest-priority sections are the ones trimmed in the documented order.
14. **Test: r3-request size bounded after simulated failed r2** — end-to-end fixture with r1 ok (large merged-findings, ~600 KB) and a forced failed r2; assert r3-request bytes < 250 KB and contains no echoed-prompt phrase.
15. **Test: chain.json soft-migration** — load a pre-S1 chain.json with no `returncode` / `status` keys; assert the script does not error, treats existing rounds as `status: "unknown"`, and writes new rounds with the new keys.
16. **Docs: `skills/external-review/SKILL.md`** — document `--incremental-budget-chars`, the new failure handling (failed rounds → `verdict_valid: false`, response file is a stub, resolution gate bypassed, preamble walks back), the sentinel-stripping behaviour, and the multi-reviewer truth table from S1.7. Update the "Exit codes" table only if a new exit code is added (preferred: do not add one; preserve existing semantics).

## 5. Open design questions

These were initially open at draft and have been resolved in §4. Captured here for traceability.

1. ~~**Hard error on chain with any prior failure?**~~ **Resolved (§S1.8):** failed prior rounds bypass the resolution-required gate silently and emit a stderr notice. No new exit code, no new flag. Rationale: hard error adds a knob to every consumer and the bypass behaviour is observable in `chain.json` (`status: "failed"`, `returncode != 0`), so operators retain visibility without forced acknowledgement.
2. ~~**Sentinel stripping placement.**~~ **Resolved (§S1, operation order):** write-time stripping is the primary mechanism. Belt-and-braces read-path stripping in `build_incremental_preamble` is not required because S1.6 walks past failed/unknown rounds entirely rather than embedding their bodies. Successful prior-round bodies that pre-date this fix will retain echoed prompt text on disk; they are not modified, but their re-embed is capped by S2.3.
3. ~~**`AGENT_REVIEWER_BUDGET_CHARS` env var?**~~ **Resolved (§3 non-goal):** flag only. If demand emerges, a follow-up can revisit.
4. **Round entries — do we want a stable `attempt` counter alongside `round`?** Out of scope for this spec, flagged for follow-up. The script's existing invariant (`next_round_number()` returns `len(rounds)+1`; rounds are never overwritten) is preserved by this spec: a failed reviewer turn occupies its own round number, and the "re-attempt" after a process failure advances to the next round number within the same review chain. Today consumers distinguish attempts via the round number sequence in `chain.json`; an explicit `attempt` field on each round could later make "this was a retry of the previous failed round" semantically explicit, but is not required for the goals in §2.

## 6. Acceptance gate

The spec is considered complete and ready for plan-writing when:

- `python3 -m pytest skills/external-review/tests/` passes with all S3 tests added.
- A live re-run of the failing chain at `/home/simon/Dev/sigreer/multistore/docs/reviewer/p10-s3-x39-tailwind-screen-aliases-P10-S3-post-slice/` (with the patched script) completes a next-round invocation either successfully or as a clearly-failed round (`returncode != 0`, `verdict_valid: false`, `status: "failed"`, persisted response file ≤ 8 KB total with the stderr-tail section itself ≤ 4 KB), and the following round runs against a prompt < 250 KB.
- `skills/external-review/SKILL.md` documents the new behaviour and the new flag.
- `--kind spec` external review on this document returns `ready` or `ready with small edits`.

## 7. Rollout

- S1 and S2 land in separate commits in this repo.
- After landing, downstream consumers re-vendor `external-reviewer.py` via the `[[project-setup]]` skill. Existing chain folders are soft-migrated (missing `returncode` treated as `null`); no destructive rewrite.
- The poisoned `multistore` chain is left intact for forensic value; a fresh chain or `--mode broad` reset is the operator's call.

## 8. References

- Empirical chain: `/home/simon/Dev/sigreer/multistore/docs/reviewer/p10-s3-x39-tailwind-screen-aliases-P10-S3-post-slice/`
- Draft brief (precursor to this spec): `docs/_drafts/context-optimisation-brief.md`
- Brief review (4 findings, verdict `revise`): `docs/reviewer/context-optimisation-brief-design/r1-2026-05-14T1411-response.md`
- Script under modification: `skills/external-review/scripts/external-reviewer.py`
- Skill doc to update: `skills/external-review/SKILL.md`
