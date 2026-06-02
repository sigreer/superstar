1. Findings

F1 — RESOLVED — `Project.reservations_ledger` now has a distinct `LedgerReservation` with `owner_id`, `owner_phase_id`, and `archived_date`, and the refusal path explicitly uses those fields for archived holders (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:112`, `:155`).

F2 — RESOLVED — The spec now defines `landed_base_sha` as the authoritative landed signal, plus branch-ancestry and unknown fallbacks for `worktree status --integration` (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:105`, `:211`).

F3 — RESOLVED — The override CLI now includes `[--force --reason "..."]`, requires a reason, defines the exact note, and says only the reserving slice is mutated (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:139`, `:157`).

F4 — RESOLVED — S8 is now correctly framed as investigation-first and grounded in current `external-reviewer` behavior: work-id chain folders, unique request filenames, and required `--work-id` for post-slice/post-phase (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:297`). That matches the current code at `skills/external-review/scripts/external-reviewer.py:727`, `:1403`, and `:2439`.

F5 — RESOLVED — The spec now states the omit-when-default serialization rule for all new default fields (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:124`).

F6 — Severity: important — `landed_base_sha` still needs guard conditions so it cannot be stamped by non-landed prune paths.
The spec says a non-null `landed_base_sha` is “definitive proof the slice shipped to base” and is recorded at `tasktool worktree prune <slice-id>` after merge (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:214`). But existing prune semantics also allow cancelled slices and forced/unmerged prunes (`tools/tasktool/commands.py:2358`, `:2367`). If S4 simply stamps during prune, a cancelled slice or `--force` cleanup can become a false “landed” signal. Specify that `landed_base_sha` is stamped only for `done` slices on the normal merged-branch prune path, not for cancelled slices, `--force`, failed ancestry checks, or finalize-only cleanup unless the merged state was already proven.

F7 — Severity: minor — Forced duplicate project reservations conflict with the ledger dedupe rule.
`--force` appends a colliding reservation to the reserving slice and records the override (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:157`), but archive appends ledger entries “deduped on `resource:value:scope`” (`:164`). If two done slices intentionally force the same project-scoped value, deduping on that key drops one holder from the ledger, weakening the audit trail promised by the owner metadata (`:112`). Either preserve all forced holders, add an override marker to the ledger key, or state that only the first holder is retained and subsequent forced holders live only in slice notes.

2. Open questions / assumptions

- I assume `landed_base_sha` is intended to represent “merged to base,” not merely “worktree lifecycle complete.”
- I assume forced project-scope duplicate reservations are rare but valid, since the spec allows `--force` rather than limiting it to phase scope.

3. Suggested document edits

- In §4.D, add explicit stamping preconditions for `landed_base_sha`: slice status `done`, branch proven merged into base, normal prune path, and no `--force` bypass.
- In §6, add worktree tests for cancelled prune, force-prune of an unmerged branch, and finalize paths asserting `landed_base_sha` is not stamped.
- In §4.B, clarify whether forced duplicate project reservations create multiple ledger entries or whether the ledger intentionally keeps only the original holder.

4. Verification gaps / commands that should be run, if any

I ran `tasktool validate --format json`; it returned `ok: true` with no warnings. Before implementation planning, add focused tests around prune stamping semantics and forced duplicate project-ledger archive behavior.

Overall verdict: revise

