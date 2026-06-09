# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md` — Acceptance criteria, AC4
- Verification: AC4 rewritten as four sub-bullets that match the S2.a check-3 design. It now states explicitly that placeholder tokens are exempt inside fenced **and** inline code; paths are exempt only inside fenced code; a dangling repo-relative path inside an inline-code span produces a `warning` (scanned, not suppressed); and glob/`docs/reviewer/`/URL paths are always exempt. The contradiction (inline backtick path being both "warning" and "no finding") is removed.

Notes:
The design body (S2.a, check 3) was already correct — backtick paths warn, fenced paths are exempt. Only the AC restated it wrongly by lumping placeholders and paths together under one inline-code exemption. AC4 now mirrors the body.

## F2
Status: fixed
Evidence:
- Files: `docs/specs/2026-06-09-P9.S2-preflight-gate-self-review-design.md` — S2.a "Output and exit codes" paragraph and S2.b ordering paragraphs
- Verification: removed the incorrect "preflight runs before the manifest is read" claim. S2.b now gives the explicit six-step `review` sequence: resolve paths → read manifest (schema-too-new aborts exit 4 here) → resolution gate → determine round → round-1 preflight (exit 4 on failure) → spawn reviewer. The exit-4 paragraph now states the two exit-4 causes are sequential (manifest read precedes preflight), so a schema-too-new manifest aborts before preflight can run and cannot be masked.

Notes:
Also resolved the reviewer's open question about the chain folder: a new paragraph documents that the chain folder is created and the manifest eager-written before round determination, so a round-1 preflight failure leaves an inert empty chain folder (no round/request/response artifacts), reused on re-run. This matches the current code's `chain_dir.mkdir` + eager-write ordering rather than fighting it. AC8 was also extended to require a regression test pinning the manifest-read-before-preflight ordering and the inline-code-path warning vs fenced-path exemption distinction.
