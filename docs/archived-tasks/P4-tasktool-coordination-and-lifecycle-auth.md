# P4 — Tasktool coordination and lifecycle authority

status: done
closed: 2026-05-19
planning: docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md

## Slices

- **S1** [done/ratified] — closed 2026-05-19 — Authoritative tasklist mutations
- **S2** [done/ratified] — closed 2026-05-19 — depends on P4.S1 — Lifecycle status enforcement

## Full phase JSON (for tasktool unarchive)

```json
{
  "archived_phases": [],
  "cross_cutting": [],
  "last_reviewed": null,
  "north_star": "",
  "phases": [
    {
      "closed": "2026-05-19",
      "created": "2026-05-19",
      "id": "P4",
      "notes": "",
      "phase_reviewer_chain": "docs/reviewer/p4-tasktool-coordination-lifecycle-design-P4-post-phase",
      "plan_path": null,
      "planning_path": "docs/specs/2026-05-19-p4-tasktool-coordination-lifecycle-design.md",
      "slices": [
        {
          "blocked_on": null,
          "closed": "2026-05-19",
          "created": "2026-05-19",
          "depends_on": [],
          "id": "S1",
          "notes": "P4.S1 is grandfathered under pre-P4.S2 lifecycle rules: it was closed before the started-field close guard and ready-close override audit note existed, so started remains null intentionally.",
          "parallel_group": "coordination",
          "plan_path": null,
          "planning_status": "ratified",
          "refs": [],
          "reviewer_chain": "docs/reviewer/p4-tasktool-coordination-lifecycle-P4-S1-post-slice",
          "started": null,
          "status": "done",
          "tasks": [],
          "title": "Authoritative tasklist mutations"
        },
        {
          "blocked_on": null,
          "closed": "2026-05-19",
          "created": "2026-05-19",
          "depends_on": [
            "P4.S1"
          ],
          "id": "S2",
          "notes": "",
          "parallel_group": "lifecycle",
          "plan_path": null,
          "planning_status": "ratified",
          "refs": [],
          "reviewer_chain": "docs/reviewer/p4-tasktool-coordination-lifecycle-P4-S2-post-slice",
          "started": "2026-05-19",
          "status": "done",
          "tasks": [],
          "title": "Lifecycle status enforcement"
        }
      ],
      "spec_path": null,
      "started": "2026-05-19",
      "status": "done",
      "title": "Tasktool coordination and lifecycle authority"
    }
  ],
  "project": "superstar",
  "schema_version": 1
}
```
