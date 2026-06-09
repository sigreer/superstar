# P8 — Closeout integrity: landed-branch close gate + lifecycle auto-commit

status: done
closed: 2026-06-09
spec: docs/specs/2026-06-05-P8-closeout-integrity-design.md
planning: docs/specs/2026-06-05-P8-closeout-integrity-design.md

## Slices

- **S1** [done/ratified] — closed 2026-06-05 — tasktool close gate: refuse done when worktree branch is unlanded (--allow-unlanded escape hatch) + auto-commit tracker lifecycle mutations at close
- **S2** [done/ratified] — closed 2026-06-09 — depends on P8.S1 — Skill updates: merge-back before close in slice-end sequence; clean (non-force) prune guidance; shared-tracker vs sibling-artifact boundary clarification

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
      "closed": "2026-06-09",
      "created": "2026-06-05",
      "id": "P8",
      "notes": "",
      "phase_reviewer_chain": "docs/reviewer/p8-closeout-integrity-design-P8-post-phase",
      "plan_path": null,
      "planning_path": "docs/specs/2026-06-05-P8-closeout-integrity-design.md",
      "slices": [
        {
          "blocked_on": null,
          "closed": "2026-06-05",
          "created": "2026-06-05",
          "depends_on": [],
          "id": "S1",
          "integration_surfaces": [
            "lifecycle"
          ],
          "landed_base_sha": "6c587f0ced8f6b10f4385b3b1c0f9d379325bf2a",
          "notes": "",
          "parallel_group": null,
          "plan_path": "docs/plans/2026-06-05-P8.S1-close-gate-lifecycle-auto-commit.md",
          "planning_status": "ratified",
          "refs": [
            "docs/specs/2026-06-05-P8.S1-close-gate-lifecycle-auto-commit-design.md",
            "docs/reviewer/p8-s1-close-gate-lifecycle-auto-commit-design-spec",
            "docs/plans/2026-06-05-P8.S1-close-gate-lifecycle-auto-commit.md",
            "docs/handoffs/2026-06-05-P8.S1-close-gate-lifecycle-auto-commit-prompt.md",
            "docs/reviewer/p8-s1-close-gate-lifecycle-auto-commit-plan",
            "docs/reviewer/p8-s1-close-gate-lifecycle-auto-commit-P8-S1-post-slice"
          ],
          "reviewer_chain": "docs/reviewer/p8-s1-close-gate-lifecycle-auto-commit-P8-S1-post-slice",
          "started": "2026-06-05",
          "status": "done",
          "tasks": [],
          "title": "tasktool close gate: refuse done when worktree branch is unlanded (--allow-unlanded escape hatch) + auto-commit tracker lifecycle mutations at close",
          "workflow_step": "done",
          "worktree_base_sha": "dbbd602797b99a1ad63fbd70899885d79fa152a3",
          "worktree_pruned_at": "2026-06-05"
        },
        {
          "blocked_on": null,
          "closed": "2026-06-09",
          "created": "2026-06-05",
          "depends_on": [
            "P8.S1"
          ],
          "id": "S2",
          "integration_surfaces": [
            "skills",
            "lifecycle-docs-test"
          ],
          "landed_base_sha": "267cfa9d1d2be3e2685be698da41ee2a8a86f168",
          "notes": "",
          "parallel_group": null,
          "plan_path": "docs/plans/2026-06-05-P8.S2-skill-closeout-sequence.md",
          "planning_status": "ratified",
          "refs": [
            "docs/specs/2026-06-05-P8.S2-skill-closeout-sequence-design.md",
            "docs/reviewer/p8-s2-skill-closeout-sequence-design-spec",
            "docs/plans/2026-06-05-P8.S2-skill-closeout-sequence.md",
            "docs/handoffs/2026-06-05-P8.S2-skill-closeout-sequence-prompt.md",
            "docs/reviewer/p8-s2-skill-closeout-sequence-plan"
          ],
          "reviewer_chain": "docs/reviewer/p8-s2-skill-closeout-sequence-P8-S2-post-slice",
          "started": "2026-06-08",
          "status": "done",
          "tasks": [],
          "title": "Skill updates: merge-back before close in slice-end sequence; clean (non-force) prune guidance; shared-tracker vs sibling-artifact boundary clarification",
          "workflow_step": "done",
          "worktree_base_sha": "6f8c66c0bd517be30a46b530fb1c561ac258b98d",
          "worktree_pruned_at": "2026-06-09"
        }
      ],
      "spec_path": "docs/specs/2026-06-05-P8-closeout-integrity-design.md",
      "started": null,
      "status": "done",
      "title": "Closeout integrity: landed-branch close gate + lifecycle auto-commit"
    }
  ],
  "project": "superstar",
  "schema_version": 3
}
```
