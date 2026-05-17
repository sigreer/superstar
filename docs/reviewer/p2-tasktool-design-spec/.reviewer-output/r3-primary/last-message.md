**Findings**

F1. RESOLVED — Blocking is now explicitly slice-scoped.  
[docs/specs/2026-05-17-P2-tasktool-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:156) says only slices carry `blocked_on` and may take `blocked`, and [lines 220-224](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:220) restrict `block` / `unblock` to slice IDs.

F2. RESOLVED — The hash sentinel design was replaced with valid JSON canonical-format enforcement.  
[lines 276-280](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:276) now use `tasktool validate --strict-format` and explicitly keep `docs/tasklist.json` as pure JSON.

F3. Severity: important — Review gates can still be bypassed through the generic status setter.  
The new review-gate section covers `tasktool close <slice-id>` and `tasktool archive-phase <phase-id>` ([lines 286-300](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:286)), but the CLI still exposes `tasktool set <id> --status ...` as a generic mutator ([lines 212-213](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:212)). As written, an implementation can set a slice or phase directly to `done` with auto-stamped `closed` and never run the post-slice/post-phase gate. That contradicts [line 304](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:304), which says the CLI is the single chokepoint for workflow gating.

**Open Questions / Assumptions**

Assumption: direct `set --status done` is intended to remain available for tasks and cross-cutting items, but not as a gate bypass for slices/phases.

**Suggested Document Edits**

Clarify `tasktool set <id> --status done` semantics: either reject it for slices/phases and require `close` / `archive-phase`, or make it call the same review-gate path and accept the same `--reviewer-chain` / `--skip-review-gate` options.

Also clean up two minor consistency points while editing: [line 318](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:318) still says skill gating rules are unchanged, while [line 304](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:304) says the skill no longer needs to remind agents; [line 349](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:349) still calls `TASKTOOL_RAW=1` an override even though §8.1 now says there is no bypass, only normalisation.

**Verification Gaps / Commands**

No implementation commands are required for this spec round. I read the target spec, `docs/TASKLIST.md`, and `skills/tasklist-discipline/SKILL.md`, plus sampled existing `chain.json` manifests to verify review-gate terminology.

**Overall Verdict**

revise