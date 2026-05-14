# Design brief — external-reviewer incremental prompt context optimisation

## Status

Draft for `--kind design` ad-hoc review. Not a spec or plan yet. Reviewer is asked to validate the diagnosis, challenge the proposed fix priorities, and surface anything missed before this becomes a real spec.

## Problem (empirical, not theoretical)

On a real `post-slice` chain in a consuming project (`multistore`), incremental round prompts grew exponentially and breached OpenAI's 1,048,576-char input limit:

| File | Bytes |
|---|---|
| `r1-merged-findings.md` | 594,637 |
| `r1-resolution.md` | 4,155 |
| `r2-…-request.md` | 886,686 |
| `r2-…-response.md` | 887,637 |
| `r3-…-request.md` | 1,293,203 (exceeds 1M) |
| `r4-…-request.md` | 1,938,265 |

Count of the literal string `"You are continuing an existing review chain"` (which appears exactly once in the prompt template) inside the response files: r1=0, r2=2, r3=6, r4=14 — compounding **2× per round**.

## Root cause

Confirmed by reading `skills/external-review/scripts/external-reviewer.py` and the chain artifacts:

1. **`write_review_artifact` (L470) writes `result.stderr` verbatim into the response file when the reviewer fails.** The OpenAI Codex–backed `reviewer-agent` prints its full session banner *including the echoed input prompt* on stderr. So a failed reviewer turn produces a response file whose body is the entire prompt, repeated.
2. **`build_incremental_preamble` (L281) falls back to the prior round's full response file** when no `r{N-1}-merged-findings.md` exists (which is the case after a failed round). It slurps the whole file with no size cap.
3. Combined: one failed reviewer turn poisons every subsequent round. r2 fails → r2-response = the prompt echoed back → r3-preamble embeds it whole → r3 prompt is 1.5× larger → r3 fails the same way → r4 is 2× larger again.

## Secondary contributors (bloat even without the bug)

- `make_prompt` (L348-353) re-embeds full target preview + every `--context` file preview on incremental rounds, on top of the preamble. The reviewer already saw these in round 1 and the preamble names them by path. Saves ~30-60% on chains with spec + plan + TASKLIST context.
- `build_incremental_preamble` reads `r{N-1}-merged-findings.md`, `r{N-1}-response`, and `r{N-1}-resolution.md` whole, uncapped (L277-298).
- `compute_diff_section` caps each subsection (`base..HEAD`, working-tree, each untracked file) independently — no global cap on the diff block.

## Proposed scope (three slices)

### S1 — Kill the recursive-echo class (must-fix; root cause)

1. `write_review_artifact`: on `returncode != 0`, store stderr **tail** only (cap to e.g. 4KB), never full stderr. Drop stdout for failed turns or cap similarly. The response file should never contain the full prompt.
2. `build_incremental_preamble`: when the prior round is recorded as failed in `chain.json`, do not embed its response. Walk backward to the last successful round; if none, fall back to the chain summary table + "no prior review available" notice.
3. Wrap the prompt body with sentinel markers (e.g. `<!-- superstar-prompt:start -->` / `:end -->`) in `make_prompt`. In `write_review_artifact`, strip any content between sentinels from reviewer output before write. Defense in depth for backends that echo on stdout instead of stderr.

### S2 — Incremental-mode prompt diet

4. In `make_prompt`, skip the context-preview block when `mode == "incremental"`. Keep the target preview but trim to ~150 lines (vs broad's 600).
5. Cap `prior_response_text`, merged-findings text, and `resolution_text` reads in `build_incremental_preamble` (e.g. 80KB each, head + tail with a truncation marker).
6. Add a single `--incremental-budget-chars` (default 400_000) global cap on the assembled prompt with a tail-truncation marker — safety net only, well below 1M.
7. Tighten `compute_diff_section`: global cap on the whole diff block, cap untracked file count (e.g. 10).

### S3 — Tests + docs

8. Unit test: simulate a failed r2 (returncode != 0, stderr = "[full prompt]") and assert r3's request size stays bounded.
9. Unit test: sentinel-stripping removes echoed prompt blocks from reviewer output.
10. Unit test: incremental prompt with `mode=incremental` does not contain context-preview headings.
11. Update `skills/external-review/SKILL.md` to document the new flag and the failure-handling behaviour.

## Non-goals / explicitly out of scope

- Changing broad-round (r1) prompt structure or default `--max-lines`. Round 1 is not the problem.
- New env vars. Prefer flags with sensible auto defaults.
- Changing the JSON output contract or exit codes.
- Adding any third-party dependency.

## Questions for the reviewer

1. Is the slicing right? Is S1 genuinely independently shippable, or does it need parts of S2 to land together?
2. Sentinel-stripping at write-time vs preamble-build time vs both — which is the right belt-and-braces strategy?
3. Should failed-round handling also surface as a hard error (exit non-zero) when the caller is in a chain that has had ≥1 failed round, forcing them to investigate, instead of silently walking back?
4. Anything in `make_prompt` / `build_incremental_preamble` we've missed as a bloat source?

## Reference paths (read these first)

- Bridge script: `skills/external-review/scripts/external-reviewer.py`
- Bloating chain (real evidence): `/home/simon/Dev/sigreer/multistore/docs/reviewer/p10-s3-x39-tailwind-screen-aliases-P10-S3-post-slice/` — especially `r2-…-response.md` (the smoking gun: failed turn, stderr-echo dumped into response body).
