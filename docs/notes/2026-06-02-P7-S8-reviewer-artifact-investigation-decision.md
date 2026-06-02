# P7.S8 Investigation Decision — Reviewer-Artifact Collision

## VERDICT: DOES-NOT-REPRODUCE (Branch B)

The P20 post-mortem claimed that generated external-reviewer **request files**
(`docs/reviewer/.../rN-...-request.md`) add/add-conflict between sibling git
worktrees developed in parallel and later merged. Reproduced against the CURRENT
bridge (`skills/external-review/scripts/external-reviewer.py`), this claim is
**refuted** for the documented workflow. Collisions only occur when an operator
violates the per-slice `--work-id` contract (two siblings passing the *same*
work-id), which the keying scheme is explicitly designed to prevent, or in a
synthetic post-phase scenario the workflow never produces (two independent
post-phase reviews of one file).

## Confirmed line numbers (current bridge)

- `chain_folder_name` — **lines 727-733**. For kind ∈ {post-slice, post-phase}
  with non-empty `work_id` → folder `f"{base}-{work_id_slug}-{kind}"`
  (dots in work_id replaced by `-`); else `f"{base}-{kind}"`. For **post-phase**
  the work_id is a *phase* id (same for all sibling slices).
- `run_one_reviewer` request path — **lines 1406-1407**:
  `basename = f"r{round_num}-{timestamp}{suffix}"`;
  `request_path = chain_dir / f"{basename}-request.md"`. `suffix` is
  `-primary`/`-sweepN` only when namespaced (1403-1405).
- `next_round_number` — **lines 777-783** (per-chain; manifest rounds count or
  glob of `r*-*-request.md`).
- `timestamp` — **line 2575**, minute resolution `%Y-%m-%dT%H%M`.
- `main()` chain-dir resolution — **lines 2460-2473** (`new_slug` from
  `chain_folder_name`; legacy discovery; `chain_dir = existing or reviewer_root/new_slug`).
- `--work-id` guard — **lines 2439-2445** (post-slice/post-phase require
  `--work-id`, else exit 2).
- work-id-mismatch refusal — **lines 2510-2527** (stored manifest `work_id`
  is source of truth; mismatch → exit 6).
- response/scratch layout — **lines 1499-1503**, all under `chain_dir`
  (`.reviewer-output/rN-<role>` + tempdir scratch).
- `tools/tasktool/artifacts.py` `add_artifact_to_item` — **lines 150-156**
  writes `reviewer_chain`/`phase_reviewer_chain` onto the tasklist row. This is
  the **only** tasklist touch (Class B, out of scope).

## Existing test coverage

`test_chain_folder_name.py` and `test_work_id.py` only assert folder-name shape
and the work-id guard in isolation. **No existing test exercises two sibling
slices producing non-colliding request paths.**

## Probe outputs (verbatim)

### Probe 1 — distinct work-ids (normal workflow)
```
sibling A request paths: {'docs/reviewer/feature-plan-P2-S3-post-slice/r1-2026-06-02T2315-request.md'}
sibling B request paths: {'docs/reviewer/feature-plan-P2-S4-post-slice/r1-2026-06-02T2315-request.md'}
COLLISION: False (none)
```

### Probe 2 — same work-id, two fresh worktrees (operator misuse)
```
wtA: {'docs/reviewer/feature-plan-P2-S3-post-slice/r1-2026-06-02T2315-request.md'}
wtB: {'docs/reviewer/feature-plan-P2-S3-post-slice/r1-2026-06-02T2315-request.md'}
CROSS-WORKTREE COLLISION (same work-id): True {'docs/reviewer/feature-plan-P2-S3-post-slice/r1-2026-06-02T2315-request.md'}
```

### Probe 3 — post-phase, two slices, same phase id, same file
```
wtA: {'docs/reviewer/feature-plan-P2-post-phase/r1-2026-06-02T2316-request.md'}
wtB: {'docs/reviewer/feature-plan-P2-post-phase/r1-2026-06-02T2316-request.md'}
POST-PHASE COLLISION (same phase id): True {'docs/reviewer/feature-plan-P2-post-phase/r1-2026-06-02T2316-request.md'}
```

## Reasoning (Decision gate)

REPRODUCES requires BOTH (1) two distinct sibling invocations writing an
identical relative `*-request.md` path, AND (2) that pattern being reachable in
the documented workflow WITHOUT an operator violating the work-id contract.

- **Probe 1** is the normal workflow: each post-slice review passes its own slice
  id (P2.S3 vs P2.S4). The chain folder is keyed by `work_id_slug`
  (lines 730-732), so the folders diverge and the request paths cannot collide
  regardless of identical timestamp/round. → No collision.
- **Probe 2** collides, but ONLY because both worktrees pass the *same* work-id
  `P2.S3`. That is an operator error — a violation of the per-slice work-id
  contract the keying is built to prevent. Within a worktree the mismatch
  refusal (lines 2510-2527) would catch reuse of a chain for a different slice;
  across fresh worktrees there is no shared manifest to compare against, so the
  only remaining trigger is two same-minute starts with an identical (wrong)
  work-id. Not workflow-reachable.
- **Probe 3** collides synthetically, but the workflow produces **exactly one**
  post-phase review per phase (one phase → one post-phase gate on one file).
  Two independent post-phase reviews of the same file never coexist, so even
  though the paths *would* collide, the scenario is unreachable.

Neither reachable scenario produces a collision; the only collisions require an
operator violating the work-id contract or a workflow state that never occurs.
→ **DOES-NOT-REPRODUCE.**

## Residual (Class B — out of scope, owned by P7.S6 / spec §4.F)

A real residual conflict remains in **`docs/tasklist.json`**: when two sibling
slices both stamp `reviewer_chain` / `phase_reviewer_chain` on close
(`artifacts.py` lines 150-156), the JSON row churns and can merge-conflict. This
is **close-churn on the tasklist**, NOT a reviewer-artifact-naming problem, and
is owned by P7.S6 / spec §4.F. It must NOT be "fixed" by renaming request files.

`external-reviewer.py` was NOT modified.
