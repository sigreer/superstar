# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md` §S1.8 ("Process-failed prior round gate behaviour")
- Change: added explicit subsection stating that `status: "failed"` prior rounds bypass the resolution-required gate silently with a stderr notice. `status: "unknown"` (legacy) does not bypass.
- Verification: `grep -n "S1.8" docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md` → §S1.8 present; §5 question 1 updated to point at §S1.8.

Notes:
The spec's earlier acceptance loop (failed r2 → fix → re-submit r3) was self-blocking under the existing `external-reviewer.py:871` gate. §S1.8 resolves by treating process failure as "no findings to resolve" and bypassing the gate. Distinction between `"failed"` (fresh, returncode-evidenced) and `"unknown"` (legacy migration) prevents silent leakage of poisoned legacy manifests.

## F2
Status: fixed
Evidence:
- Files: §S1 "Operation order for response persistence" preamble and §S1.3 ("Sanitise stdout and stderr on every round, success or failure")
- Change: success-path stderr handling now explicit — sentinel-strip first, drop or cap to 2 KB tail second. The pre-revision ambiguity ("write stdout as today") is removed.
- Verification: S3 item 5 ("success-stderr is dropped or capped") added with explicit assertion.

Notes:
The §1.3 self-demonstration (1.22 MB happy-path response) is now covered by the success-path branch in §S1.3.

## F3
Status: fixed
Evidence:
- Files: §S1 "Operation order for response persistence" (the 4-step ordering block at the top of S1), §S1.5 (sentinel stripper specification), S3 items 4 and 6.
- Change: operation order made explicit — sentinel-strip the full streams first, *then* cap. §S1.5 specifies behaviour when only one marker is present (truncated echo case). S3 item 6 asserts "strip-before-cap" by feeding 20 KB of echoed prompt and asserting no markers appear in the resulting 4 KB tail.
- Verification: S3 item 4 ("sentinel-stripping truncated echo") asserts the start-only and end-only marker cases.

Notes:
This addresses the reviewer's concern that a tail-cap could leave the end of an echo without its start marker. The stripper now handles single-marker streams by extending the deletion to the natural boundary (start or end of stream).

## F4
Status: fixed
Evidence:
- Files: §S1.1 and §S1.6
- Change: `status` field now has three values, with `"unknown"` reserved for legacy migrated entries. §S1.6 specifies that `"unknown"` is treated identically to `"failed"` in preamble construction (walk back, do not embed). §S1.8 specifies that `"unknown"` does **not** bypass the resolution gate (only fresh `"failed"` does), to prevent legacy chains from silently sidestepping operator review.
- Verification: S3 item 8 ("preamble treats `status: \"unknown\"` as untrusted") added.

Notes:
The deterministic rule "unknown == untrusted in preamble construction; unknown != gate-bypass in submission" makes legacy manifest handling predictable without inventing retroactive truth.

## F5
Status: fixed
Evidence:
- Files: §S1.7 "Multi-reviewer truth table"
- Change: explicit 5-row table covering primary ok / sweep ok-or-failed combinations, defining top-level `status`, `returncode`, `verdict_valid`, `merged_verdict`, and process exit. Preserves current `main()` behaviour (return primary's returncode) while adding per-reviewer truth.
- Verification: S3 item 2 ("failed sweep can't poison merged findings") now references §S1.7 explicitly.

Notes:
The "primary failure flips top-level; sweep failure is recorded per-reviewer only" rule keeps the JSON contract stable for consumers who only look at top-level `verdict_valid` / `returncode`.

## F6
Status: fixed
Evidence:
- Files: S3 introduction ("Numbering note"), and all S1/S2 acceptance references updated.
- Change: S3 renumbered 1-16, with explicit numbering-note stating that cross-references in S1/S2 are by item number. S1 acceptance now cites items 1, 9, 14 (with explanatory mapping). S2 acceptance now cites items 10, 11, 12, 13. The drifted references (§6.8, §6.10, §6.11) are gone.
- Verification: `grep -n "S3 item" docs/specs/2026-05-14-external-reviewer-context-optimisation-spec.md` shows the corrected references.

Notes:
Numbering-note in S3 makes future drift detectable in code review.
