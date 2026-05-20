**Findings**

F1 Severity: important  
The proposed `VERDICT_LINE_BARE_RE` is line-anchored, but not value-boundary anchored, so it will accept malformed bare verdict lines such as `Verdict: ready for review` or `Verdict: ready-ish` as `ready`. The spec presents anchoring as eliminating false-positive risk at [docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x10-verdict-parser/docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md:66), and includes the regex at line 71, but the acceptance tests do not cover malformed line-anchored values. Since this expands matching from the existing `Overall verdict` contract to a looser bare `Verdict` label, the spec should require an end-of-line/value-boundary constraint and tests like `Verdict: ready for review` and `Verdict: ready-ish` returning invalid.

F2 Severity: important  
The “single chokepoint” acceptance criterion is inconsistent with the current implementation. The spec says there should be only one call site combining normalization and `parse_verdict` for response bodies at [line 129](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x10-verdict-parser/docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md:129), but current code has automated parsing at [external-reviewer.py:1403](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x10-verdict-parser/skills/external-review/scripts/external-reviewer.py:1403), manual ingest parsing at [external-reviewer.py:1814](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x10-verdict-parser/skills/external-review/scripts/external-reviewer.py:1814), and legacy manifest synthesis parsing raw response bodies at [external-reviewer.py:2598](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x10-verdict-parser/skills/external-review/scripts/external-reviewer.py:2598). Either the spec needs to exclude legacy synthesis explicitly, or require a helper such as `parse_reformatted_verdict(raw)` and use it everywhere response bodies are parsed.

F3 Severity: minor  
The regex/risk text claims the proposed leading class matches “list bullets” at [line 134](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x10-verdict-parser/docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md:134), but the proposed class `^[\s>#*_`]*` at [line 72](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x10-verdict-parser/docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md:72) does not match `- Verdict: ready` or `1. Verdict: ready`. If list bullets are intentionally out of scope, say that. If they are intended, add `[-\d.\s]` carefully and test it.

F4 Severity: minor  
The replay acceptance criterion names `r2-2026-05-19T0054-response.md` and `r1-2026-05-19T0050-response.md` at [line 128](/home/simon/Dev/sigreer/skills/superstar/.worktrees/x10-verdict-parser/docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md:128), but does not give the full source path or state whether the implementation should copy them into repo-local fixtures first. The files exist under `/home/simon/Dev/sigreer/multistore/docs/reviewer/p11-s5-final-guardrails-and-documentation-plan/`, but the spec should not leave that discovery to the implementer.

**Open Questions / Assumptions**

I assume strict parsing remains the desired direction and loose last-N-line recovery is still intentionally deferred. I also assume legacy chain migration should not silently lag behind the new normalization unless the spec says so.

**Suggested Document Edits**

Add a parser helper requirement: “Introduce `parse_reformatted_verdict(raw: str)` or equivalent; automated review, manual ingest, and legacy synthesis must use it, unless legacy synthesis is explicitly documented as excluded.”

Tighten the bare regex requirement to reject extra words after the allowed value, while still permitting punctuation/emphasis and the observed `Full review written...` case only if that same-line trailer is deliberately accepted.

Add tests for malformed line-anchored bare verdicts: `Verdict: ready for review`, `Verdict: ready-ish`, and `Verdict: ready with small edits pending changes`.

Clarify whether bullet-prefixed verdict lines are in or out of scope.

Replace the replay criterion with explicit full paths and fixture names copied into `skills/external-review/tests/fixtures/`.

**Verification Gaps / Commands**

Run:

```sh
python3 -m pytest skills/external-review/tests/
```

Also add a small direct replay command against both copied fixtures using the final public helper, not a hand-composed `parse_verdict(_reformat_response(...))` expression.

Overall verdict: revise

