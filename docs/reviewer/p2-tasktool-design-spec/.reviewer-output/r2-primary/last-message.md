**Findings**

F1. Severity: important — `blocked` is specified for every item, but only `Slice` has `blocked_on`.  
[docs/specs/2026-05-17-P2-tasktool-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:121) defines `Task` without `blocked_on`, and [line 137](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:137) defines `CrossCutting` without it, while [line 151](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:151) makes `blocked` a global status and [line 215](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:215) exposes generic `tasktool block <id>`. Implementers will either reject blocking tasks/cross items despite the CLI surface, or write invalid objects. Specify whether `blocked_on` belongs on every blockable kind, or restrict `blocked`/`block` to slices only.

F2. Severity: important — The hash sentinel enforcement is not compatible with “direct JSON consumers” as written.  
The spec says other tools can read `docs/tasklist.json` directly ([line 61](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:61)), but the hook mechanism writes “a trailing newline plus a hash sentinel” to the JSON file ([line 269](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:269)). If the sentinel is outside the JSON value, the file is no longer valid JSON. If it is inside the JSON, the schema and validation rules need to include it. The risk section defers this choice to S1 ([line 320](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:320)), but the acceptance criteria require major design choices to be settled.

F3. Severity: important — Review-gate enforcement is underspecified for close/archive commands.  
The existing workflow requires post-slice review before closing slices and post-phase review before archiving phases ([TASKLIST line 69](/home/simon/Dev/sigreer/skills/superstar/docs/TASKLIST.md:69), [tasklist-discipline line 62](/home/simon/Dev/sigreer/skills/superstar/skills/tasklist-discipline/SKILL.md:62)). The spec says `reviewer_chain` must exist at slice close time “when post-slice review is required” ([line 171](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:171)), but `tasktool close` has no `--reviewer-chain` option and no rule for deriving/validating the external-review verdict. `archive-phase` only refuses unless slices are done ([line 226](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:226)); it does not specify the post-phase review gate. This leaves a core “preserve status gates” goal dependent on skill prose instead of the new canonical mutation path.

**Open Questions / Assumptions**

No prior findings existed to resolve; round 1 failed before producing review findings.

Assumption: `tasktool` is expected to enforce workflow-critical gates, not just data shape. If that is false, the spec should explicitly say the CLI validates data integrity only and the skills remain responsible for review gates.

**Suggested Document Edits**

Clarify blockability per kind: either add `blocked_on` to `Phase`, `Task`, and `CrossCutting`, or narrow `blocked`/`block` to slices.

Replace the sentinel design with a valid-JSON mechanism, for example a reserved `_meta.tasktool_hash` field, or switch to a normalisation check (`validate --strict-format`) and remove the trailing sentinel.

Define review-gate behavior for `close` and `archive-phase`: required chain path, expected `chain.json` status/verdict, bypass/manual-approval handling, and whether phase closure records a post-phase chain separately from slice `reviewer_chain`.

**Verification Gaps / Commands**

No implementation commands are required yet. Before planning, run a consistency pass after edits:

`python3 -m pytest skills/external-review/tests/ -q` only becomes relevant if the spec changes expected reviewer-chain semantics.

**Overall Verdict**

revise