1. Findings

F1 — RESOLVED — The spec keeps the distinct `LedgerReservation` owner fields and archived-holder refusal path (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:112`, `:155`).

F2 — RESOLVED — `landed_base_sha` remains the authoritative landed signal, with branch-ancestry and unknown fallbacks (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:219`-`:243`).

F3 — RESOLVED — `reserve add --force` requires `--reason`, records the override note, and mutates only the reserving slice (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:157`-`:163`).

F4 — RESOLVED — S8 remains investigation-first and does not assume a current reviewer-artifact bug (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:314`-`:335`).

F5 — RESOLVED — The omit-when-default serialization rule is explicit for all new default-valued fields (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:124`-`:130`).

F6 — Severity: important — RESOLVED — The spec now prevents false `landed_base_sha` stamping by requiring a `done` slice, the normal guarded prune path, a passed branch-merged guard, no `--force`, and no finalize-only cleanup unless the same prune already proved merged state (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:228`-`:236`). This is grounded against the current code, where prune otherwise accepts terminal `done` or `cancelled` rows and `--force` bypasses the merge guard (`tools/tasktool/commands.py:2358`-`:2373`), and finalize records prune audit fields without rechecking merge status (`tools/tasktool/commands.py:2428`-`:2454`). The testing strategy also covers cancelled, force-unmerged, and finalize-only non-stamping (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:391`-`:394`).

F7 — Severity: minor — RESOLVED — The ledger dedupe key is now `resource:value:scope:owner_id`, preserving multiple forced holders while keeping re-archive idempotent for the same owner (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:170`-`:177`). The CLI tests explicitly require both forced holders to survive archive and re-archive to remain idempotent (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md:377`-`:382`).

2. Open questions / assumptions

None.

3. Suggested document edits

None required.

4. Verification gaps / commands that should be run, if any

I ran `tasktool validate --format json`; it returned `ok: true` with no errors or warnings. Before implementation, the plan should preserve the spec’s focused test gates for prune stamping and forced duplicate project-ledger archive behavior.

Overall verdict: ready