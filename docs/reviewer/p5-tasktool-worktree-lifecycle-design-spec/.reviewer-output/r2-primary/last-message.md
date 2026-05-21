1. Findings

F1 Severity: blocking — RESOLVED. The revised spec now preserves `tasktool close` semantics and moves destructive cleanup to `tasktool worktree prune` after merge-back (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:131`-`150`, `187`-`193`). That resolves the prior workflow contradiction.

F2 Severity: important — UNRESOLVED. Canonical naming is mostly fixed, but the schema example still records uppercase `worktree-P5-S1-...` even though the normative naming function lowercases IDs/titles and the examples are lowercase (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:50`-`76`, `87`-`88`, `286`). Because branch name must equal basename, this remaining mismatch can still produce incompatible implementations.

F3 Severity: important — RESOLVED. The spec now explicitly says `close` retains `worktree_path`, `worktree_branch`, and `worktree_in_place`; prune/finalize nulls fields and records `worktree_pruned_at` (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:131`-`157`, `173`-`185`).

F4 Severity: important — RESOLVED. Subagent detection for `tasktool start` now names concrete signals, precedence, fallback behavior, and tests (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:119`-`129`, `253`-`260`).

F5 Severity: minor — RESOLVED. Legacy migration policy is now consistently “warn, no automatic migration” (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:37`, `195`-`199`, `284`).

F6 Severity: blocking — The ad-hoc design is not implementable against the current tasktool model as written. The spec says `tasktool start ... --ad-hoc` allocates `AH<n>`, writes a real `cross_cutting` row, and auto-archives it on `tasktool close <AH-id>` (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:98`, `117`). Current tasktool ID parsing and validation only accept `X\d+` for cross-cutting IDs (`tools/tasktool/ids.py:10`-`15`, `34`-`38`; `tools/tasktool/validate.py:110`-`118`), and archived cross-cutting rows only retain `id`, `title`, `archived_path`, and `archived_date` (`tools/tasktool/model.py:87`-`91`). That means the plan either has to extend the ID grammar/archive schema/listing logic for `AH` rows, or use normal `X<n>` rows and define when worktree fields survive close/prune.

F7 Severity: blocking — The “no detached or in-flight subagent tasks reference the worktree” prune guard is still not specific enough to implement or test. It is one of the four destructive-prune guards (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:141`-`146`, `265`), but P5.S2 only says to implement it and has no fixture for it (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:232`-`247`). The concrete env-var signals in P5.S3 only apply to `start`; they do not provide a durable registry or lease that prune can inspect after subagents are dispatched. This needs a defined source of truth, or the guard should be explicitly downgraded to best-effort and removed from acceptance as an independently testable safety gate.

2. Open questions / assumptions

- Should ad-hoc work use existing `X<n>` cross-cutting IDs, or is `AH<n>` intended to become a first-class ID family across parser, schema, validation, render, archive, and orphan scanning?
- If ad-hoc rows are auto-archived on close, where does tasktool retain `worktree_path` / `worktree_branch` until prune completes?
- What concrete mechanism proves no subagent is still using a worktree: tasktool-managed leases, shim-maintained process records, lock files, or only a best-effort warning?

3. Suggested document edits

- Change the schema example to lowercase: `.worktrees/worktree-p5-s1-tasktool-worktree-core` and `worktree-p5-s1-tasktool-worktree-core`.
- Replace the ad-hoc paragraph with a storage-compatible design. Either allocate normal `X<n>` rows and keep them active until prune, or explicitly add `AH<n>` to the tasktool ID/schema/archive model and list the required code areas.
- Add a state-table row for ad-hoc close/prune, including whether the row remains active, archived, or recoverable by `worktree list --all`.
- Define the in-flight-subagent guard’s data source and add at least one P5.S2 test for refusal and one for successful prune after the reference clears.
- Fix `tasktool worktree prune`’s subcommand description saying “Same guards as `close`’s prune step” because `close` no longer has a prune step (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:166`).

4. Verification gaps / commands

I ran:

- `tools/tasktool/tasktool validate --strict-format` — passed.
- `python -m pytest tools/tasktool/tests -q` — 391 passed, with one pytest cache warning caused by read-only `.pytest_cache` write access.

Still needed before implementation planning:

- Schema-generation and validation tests for the chosen `worktree_*` fields.
- CLI integration tests for authoritative-checkout routing from inside linked worktrees.
- New tests for ad-hoc lifecycle storage and the in-flight-subagent prune guard once those semantics are defined.

Overall verdict: revise