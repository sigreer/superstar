# P7 — Integration-surface-aware parallel slice safety

status: done
closed: 2026-06-05
spec: docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md
planning: docs/handoffs/2026-06-02-P7-phase-coordinator-prompt.md

## Slices

- **S1** [done/ratified] — closed 2026-06-03 — Data model + migration (schema v3): surfaces, reservations, coordination_group, base/landed SHAs, LedgerReservation
- **S2** [done/ratified] — closed 2026-06-03 — depends on P7.S1 — surface / reserve / coordinate CLI; reservation refusal + --force --reason; ledger population on archive
- **S3** [done/ratified] — closed 2026-06-04 — depends on P7.S1, P7.S2 — Scheduling overlap detection: ready-slices/schedule warnings, surface check, ratify warning, coordination suppression
- **S4** [done/ratified] — closed 2026-06-03 — depends on P7.S1 — worktree start base-sha + prune landed-sha stamping + worktree status --integration
- **S5** [done/ratified] — closed 2026-06-05 — depends on P7.S4 — Conservative worktree sync (strict preconditions; advances base-sha)
- **S6** [done/ratified] — closed 2026-06-05 — depends on P7.S2, P7.S3, P7.S4 — Skill changes: subagent-driven-development checkpoint + registry-merge-playbook; tasklist-discipline; phase-planning/writing-plans tables
- **S7** [done/ratified] — closed 2026-06-05 — depends on P7.S1, P7.S6 — Plan-tracker drift validation (declared surfaces/reservations reflected in plan)
- **S8** [cancelled/ratified] — closed 2026-06-02 — Investigate reviewer-artifact collision vs current bridge; fix only if reproduced, else drop

## Full phase JSON (for tasktool unarchive)

```json
{
  "archived_cross_cutting": [],
  "archived_phases": [],
  "cross_cutting": [],
  "last_reviewed": null,
  "north_star": "",
  "phases": [
    {
      "closed": "2026-06-05",
      "created": "2026-06-02",
      "id": "P7",
      "notes": "",
      "phase_reviewer_chain": "docs/reviewer/p7-integration-surface-parallel-safety-design-P7-post-phase",
      "plan_path": null,
      "planning_path": "docs/handoffs/2026-06-02-P7-phase-coordinator-prompt.md",
      "slices": [
        {
          "blocked_on": null,
          "closed": "2026-06-03",
          "created": "2026-06-02",
          "depends_on": [],
          "id": "S1",
          "notes": "Spec §4.A. Intended integration surfaces (recorded here until the surface CLI exists): model, serialize, migrate. No deps. Schema v2→v3, omit-when-default serialization.",
          "parallel_group": null,
          "plan_path": "docs/plans/2026-06-02-P7-S1-data-model-migration.md",
          "planning_status": "ratified",
          "refs": [
            "docs/plans/2026-06-02-P7-S1-data-model-migration.md",
            "docs/handoffs/2026-06-02-P7-S1-data-model-migration-prompt.md",
            "docs/reviewer/p7-s1-data-model-migration-plan"
          ],
          "reviewer_chain": "docs/reviewer/p7-s1-data-model-migration-P7-S1-post-slice",
          "started": "2026-06-02",
          "status": "done",
          "tasks": [],
          "title": "Data model + migration (schema v3): surfaces, reservations, coordination_group, base/landed SHAs, LedgerReservation",
          "workflow_step": "done",
          "worktree_pruned_at": "2026-06-03"
        },
        {
          "blocked_on": null,
          "closed": "2026-06-03",
          "created": "2026-06-02",
          "depends_on": [
            "P7.S1"
          ],
          "id": "S2",
          "notes": "Spec §4.B. Surfaces: cli, commands. reserve add refusal (phase+project scope incl. ledger); --force requires --reason, mutates only reserving slice; ledger LedgerReservation population on archive-phase (done slices only), dedupe resource:value:scope:owner_id.",
          "parallel_group": "core-after-model",
          "plan_path": "docs/plans/2026-06-02-P7-S2-surface-reserve-coordinate-cli.md",
          "planning_status": "ratified",
          "refs": [
            "docs/plans/2026-06-02-P7-S2-surface-reserve-coordinate-cli.md",
            "docs/handoffs/2026-06-02-P7-S2-surface-reserve-coordinate-cli-prompt.md",
            "docs/reviewer/p7-s2-surface-reserve-coordinate-cli-plan"
          ],
          "reviewer_chain": "docs/reviewer/p7-s2-surface-reserve-coordinate-cli-P7-S2-post-slice",
          "started": "2026-06-03",
          "status": "done",
          "tasks": [],
          "title": "surface / reserve / coordinate CLI; reservation refusal + --force --reason; ledger population on archive",
          "workflow_step": "done",
          "worktree_pruned_at": "2026-06-03"
        },
        {
          "blocked_on": null,
          "closed": "2026-06-04",
          "created": "2026-06-02",
          "depends_on": [
            "P7.S1",
            "P7.S2"
          ],
          "id": "S3",
          "landed_base_sha": "7ea69b453fc70d3faf3abf93979217b56e2a2d92",
          "notes": "Spec §4.C. Surfaces: commands. ready-slices/schedule surface_overlap warnings; surface check <phase>; ratify --parallel-group warning; coordination_group suppression. Warning-only (no block).",
          "parallel_group": null,
          "plan_path": "docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md",
          "planning_status": "ratified",
          "refs": [
            "docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md",
            "docs/handoffs/2026-06-04-P7-S3-scheduling-overlap-detection-prompt.md",
            "docs/reviewer/p7-s3-scheduling-overlap-detection-plan"
          ],
          "reviewer_chain": "docs/reviewer/p7-s3-scheduling-overlap-detection-P7-S3-post-slice",
          "started": "2026-06-04",
          "status": "done",
          "tasks": [],
          "title": "Scheduling overlap detection: ready-slices/schedule warnings, surface check, ratify warning, coordination suppression",
          "workflow_step": "done",
          "worktree_base_sha": "a8e3661b602076becadaa8c6f216a3ef030330b2",
          "worktree_pruned_at": "2026-06-04"
        },
        {
          "blocked_on": null,
          "closed": "2026-06-03",
          "created": "2026-06-02",
          "depends_on": [
            "P7.S1"
          ],
          "id": "S4",
          "landed_base_sha": "04973057889afff000c3f71ea4251cb49a665883",
          "notes": "Spec §4.D. Surfaces: commands, worktree. Record worktree_base_sha on start; stamp landed_base_sha on guarded merged-branch prune of a done slice only; worktree status --integration (landed_base_sha authoritative, branch-ancestry fallback, landed:unknown).",
          "parallel_group": "core-after-model",
          "plan_path": "docs/plans/2026-06-02-P7-S4-worktree-integration-detection.md",
          "planning_status": "ratified",
          "refs": [
            "docs/plans/2026-06-02-P7-S4-worktree-integration-detection.md",
            "docs/handoffs/2026-06-02-P7-S4-worktree-integration-detection-prompt.md",
            "docs/reviewer/p7-s4-worktree-integration-detection-plan"
          ],
          "reviewer_chain": "docs/reviewer/p7-s4-worktree-integration-detection-P7-S4-post-slice",
          "started": "2026-06-03",
          "status": "done",
          "tasks": [],
          "title": "worktree start base-sha + prune landed-sha stamping + worktree status --integration",
          "workflow_step": "done",
          "worktree_pruned_at": "2026-06-03"
        },
        {
          "blocked_on": null,
          "closed": "2026-06-05",
          "created": "2026-06-02",
          "depends_on": [
            "P7.S4"
          ],
          "id": "S5",
          "integration_surfaces": [
            "worktree"
          ],
          "landed_base_sha": "68fc7e4d73f4dbaebedeacad52a7b897e5f643fd",
          "notes": "Spec §4.E. Surfaces: worktree. Conservative worktree sync: clean-tree + known base + explicit --merge/--rebase + no tasklist drift; advances worktree_base_sha on success. Deferral candidate if scope tightens.",
          "parallel_group": null,
          "plan_path": "docs/plans/2026-06-04-P7-S5-conservative-worktree-sync.md",
          "planning_status": "ratified",
          "refs": [
            "docs/specs/2026-06-04-P7-S5-conservative-worktree-sync-design.md",
            "docs/reviewer/p7-s5-conservative-worktree-sync-design-spec",
            "docs/plans/2026-06-04-P7-S5-conservative-worktree-sync.md",
            "docs/handoffs/2026-06-04-P7-S5-conservative-worktree-sync-prompt.md",
            "docs/reviewer/p7-s5-conservative-worktree-sync-plan",
            "docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice"
          ],
          "reviewer_chain": "docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice",
          "started": "2026-06-05",
          "status": "done",
          "tasks": [],
          "title": "Conservative worktree sync (strict preconditions; advances base-sha)",
          "workflow_step": "done",
          "worktree_base_sha": "0290ebd94333f9c197c8f718ca85c9df539c51fc",
          "worktree_pruned_at": "2026-06-05"
        },
        {
          "blocked_on": null,
          "closed": "2026-06-05",
          "created": "2026-06-02",
          "depends_on": [
            "P7.S2",
            "P7.S3",
            "P7.S4"
          ],
          "id": "S6",
          "landed_base_sha": "68fc7e4d73f4dbaebedeacad52a7b897e5f643fd",
          "notes": "Spec §4.F. Surfaces: skills. subagent-driven-development: surface check before parallel dispatch + integrate-current-main checkpoint before post-slice review + references/registry-merge-playbook.md. tasklist-discipline command docs + red flags. phase-planning/writing-plans surface/reservation tables.",
          "parallel_group": null,
          "plan_path": "docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md",
          "planning_status": "ratified",
          "refs": [
            "docs/plans/2026-06-04-P7-S6-skill-integration-surface-docs.md",
            "docs/handoffs/2026-06-04-P7-S6-skill-integration-surface-docs-prompt.md",
            "docs/reviewer/p7-s6-skill-integration-surface-docs-plan"
          ],
          "reviewer_chain": "docs/reviewer/p7-s6-skill-integration-surface-docs-P7-S6-post-slice",
          "started": "2026-06-05",
          "status": "done",
          "tasks": [],
          "title": "Skill changes: subagent-driven-development checkpoint + registry-merge-playbook; tasklist-discipline; phase-planning/writing-plans tables",
          "workflow_step": "done",
          "worktree_base_sha": "0290ebd94333f9c197c8f718ca85c9df539c51fc",
          "worktree_pruned_at": "2026-06-05"
        },
        {
          "blocked_on": null,
          "closed": "2026-06-05",
          "created": "2026-06-02",
          "depends_on": [
            "P7.S1",
            "P7.S6"
          ],
          "id": "S7",
          "integration_surfaces": [
            "validate"
          ],
          "landed_base_sha": "68fc7e4d73f4dbaebedeacad52a7b897e5f643fd",
          "notes": "Spec §4.G. Surfaces: validate. tasktool validate / artifact-status check that declared surfaces/reservations are reflected in plan table; min bar = warn when a parallel_group slice declares no surfaces.",
          "parallel_group": null,
          "plan_path": "docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md",
          "planning_status": "ratified",
          "refs": [
            "docs/specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md",
            "docs/reviewer/p7-s7-plan-tracker-drift-validation-design-spec",
            "docs/plans/2026-06-05-P7-S7-plan-tracker-drift-validation.md",
            "docs/handoffs/2026-06-05-P7-S7-plan-tracker-drift-validation-prompt.md",
            "docs/reviewer/p7-s7-plan-tracker-drift-validation-plan"
          ],
          "reviewer_chain": "docs/reviewer/p7-s7-plan-tracker-drift-validation-P7-S7-post-slice",
          "started": "2026-06-05",
          "status": "done",
          "tasks": [],
          "title": "Plan-tracker drift validation (declared surfaces/reservations reflected in plan)",
          "workflow_step": "done",
          "worktree_base_sha": "65acbcbbb849509088a9625088322dfe12ef7a4b",
          "worktree_pruned_at": "2026-06-05"
        },
        {
          "blocked_on": null,
          "closed": "2026-06-02",
          "created": "2026-06-02",
          "depends_on": [],
          "id": "S8",
          "notes": "Spec §4.H. Surfaces: external-review. INVESTIGATION-FIRST: reproduce reported add/add reviewer-artifact collision vs CURRENT bridge (already work_id-scopes chains + round/role-unique request files). Fix only if reproduced; else document + drop. No deps.\nCancelled 2026-06-02T23:23:25: investigation: reviewer-artifact add/add collision does not reproduce against the current bridge (work-id-keyed chain folders, round/role-unique basenames, mandatory --work-id with mismatch refusal); residual docs/tasklist.json close-churn is owned by P7.S6 integrate-current-main, not by reviewer-artifact naming. See docs/notes/2026-06-02-P7-S8-reviewer-artifact-investigation-decision.md",
          "parallel_group": null,
          "plan_path": "docs/plans/2026-06-02-P7-S8-reviewer-artifact-investigation.md",
          "planning_status": "ratified",
          "refs": [
            "docs/plans/2026-06-02-P7-S8-reviewer-artifact-investigation.md",
            "docs/handoffs/2026-06-02-P7-S8-reviewer-artifact-investigation-prompt.md",
            "docs/reviewer/p7-s8-reviewer-artifact-investigation-plan"
          ],
          "reviewer_chain": "docs/reviewer/p7-s8-reviewer-artifact-investigation-plan",
          "started": "2026-06-02",
          "status": "cancelled",
          "tasks": [],
          "title": "Investigate reviewer-artifact collision vs current bridge; fix only if reproduced, else drop",
          "workflow_step": "implement",
          "worktree_pruned_at": "2026-06-02"
        }
      ],
      "spec_path": "docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md",
      "started": null,
      "status": "done",
      "title": "Integration-surface-aware parallel slice safety"
    }
  ],
  "project": "superstar",
  "schema_version": 3
}
```
