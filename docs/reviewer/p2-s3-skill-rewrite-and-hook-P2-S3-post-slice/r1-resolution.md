# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md`, `docs/handoffs/2026-05-18-p2-s3-skill-rewrite-and-hook-prompt.md`, `docs/reviewer/p2-s3-skill-rewrite-and-hook-plan/`, `docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice/`
- Verification: `git status --short --untracked-files=all` → clean after the post-slice resolution commit.

Notes:
All previously-untracked plan, handoff, and reviewer-chain artifacts are staged and committed alongside this resolution. The `docs/tasklist.json` `P2.S3.refs` entry now resolves to a tracked file.

## F2
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:11`
- Verification: line 11 now reads `(created 2026-05-18; current status set via tasktool during execution)`; no longer claims a hard-coded `status: ready`.

Notes:
The "Sweep" formulation of this finding additionally noted that the reviewer chain wasn't recorded on the tasklist row. The `reviewer_chain` field will be set by `tasktool close P2.S3` once the gate passes, which is the canonical way to attach the chain.

## F3 (primary)
Status: fixed
Evidence:
- Files: `docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md` (all task checkboxes, plus a new "Completion evidence" appendix listing commit SHAs and verification commands).
- Verification: `grep -c '^- \[x\]' docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md` → 51 (all step checkboxes flipped).

Notes:
Added a `## Completion evidence` section mapping each task to its commit SHA (or the documented reason for no commit, in T4/T12/T13). The hook smoke test result is recorded.

## S1.F3 (sweep — cross-cutting ID fully-qualified form)
Status: fixed
Evidence:
- Files: `skills/tasklist-discipline/SKILL.md` (Conceptual model table row)
- Verification: row now reads `| Cross-cutting | X4 | X4 (top-level; not nested under a phase) |`. Matches the spec (§ cross-cutting are top-level X*) and the validator (`validate.py` treats `x4` filenames as top-level `X4`).

Notes:
The previous wording (`P2.X4`) would have misled agents into producing IDs and filenames the orphan validator rejects. Corrected.

## F4 (primary — TASKTOOL_RAW=1 evidence gap)
Status: deferred
Evidence:
- Files: `tools/tasktool/tests/test_pre_commit_hook.py::test_raw_edit_then_normalise_passes`
- Verification: the existing test exercises the documented recovery path (raw semantic edit + `validate --normalise` + commit succeeds). The literal `TASKTOOL_RAW=1` env var is editor-side scaffolding, not a hook behaviour — the hook never inspects it.

Notes:
The reviewer themselves rated this minor and noted "TASKTOOL_RAW is not a hook bypass". Recovery-path semantics are already covered by `test_raw_edit_then_normalise_passes`. Adding a test that merely runs an editor with the env var set would not exercise any hook code path. Deferring.
