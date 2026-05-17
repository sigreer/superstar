**Findings**

F4. Severity: minor — `validate` flags used by enforcement are not listed in the CLI surface.  
[docs/specs/2026-05-17-P2-tasktool-design.md:261](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:261) documents `tasktool validate` with only `--format json`, but enforcement and tests depend on `tasktool validate --strict-format` and `tasktool validate --normalise` at [lines 281-284](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:281), [line 312](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:312), and [line 353](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:353). This is small, but it leaves implementers guessing whether these are official command flags, hook-only internals, or hidden aliases.

F1. RESOLVED — Blocking remains explicitly slice-scoped.  
[Line 156](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:156) restricts `blocked` and `blocked_on` to slices, and [lines 224-228](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:224) keep `block` / `unblock` slice-only.

F2. RESOLVED — The sentinel issue remains fixed with canonical JSON validation.  
[Lines 280-283](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:280) keep `docs/tasklist.json` pure JSON and enforce canonical bytes via `validate --strict-format`.

F3. RESOLVED — The generic status setter no longer bypasses review gates.  
[Lines 212-217](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:212) now say `set --status done` for slices/phases routes through the same review-gate machinery as `close` / `archive-phase`, with the same reviewer-chain and skip options.

**Open Questions / Assumptions**

Assumption: `--strict-format` and `--normalise` are intended supported `validate` flags, not private hook-only behavior.

**Suggested Document Edits**

Update §7.4 to document:

`tasktool validate [--format text|json] [--strict-format] [--normalise]`

Then add one sentence that `--strict-format` checks byte-for-byte canonical formatting and `--normalise` rewrites the file into canonical format after successful validation.

**Verification Gaps / Commands**

I read the target spec and `docs/TASKLIST.md` from disk. No implementation commands are required for this spec-only round.

**Overall Verdict**

ready with small edits