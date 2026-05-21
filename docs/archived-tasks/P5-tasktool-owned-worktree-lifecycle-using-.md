# P5 — Tasktool-owned worktree lifecycle & using-git-worktrees skill collapse

status: done
closed: 2026-05-21
spec: docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md

## Slices

- **S1** [done/proposed] — closed 2026-05-21 — Tasktool worktree lifecycle core
- **S2** [done/ratified] — closed 2026-05-21 — depends on P5.S1 — Prune + repair
- **S3** [done/proposed] — closed 2026-05-21 — depends on P5.S1, P5.S2 — Skill rewrite + subagent guard + workflow updates

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
      "closed": "2026-05-21",
      "created": "2026-05-21",
      "id": "P5",
      "notes": "",
      "phase_reviewer_chain": "docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-post-phase",
      "plan_path": null,
      "planning_path": null,
      "slices": [
        {
          "blocked_on": null,
          "closed": "2026-05-21",
          "created": "2026-05-21",
          "depends_on": [],
          "id": "S1",
          "notes": "",
          "parallel_group": null,
          "plan_path": "docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md",
          "planning_status": "proposed",
          "refs": [
            "docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md",
            "docs/reviewer/p5-s1-tasktool-worktree-lifecycle-core-plan"
          ],
          "reviewer_chain": "docs/reviewer/p5-s1-tasktool-worktree-lifecycle-core-P5-S1-post-slice",
          "started": "2026-05-21",
          "status": "done",
          "tasks": [],
          "title": "Tasktool worktree lifecycle core"
        },
        {
          "blocked_on": null,
          "closed": "2026-05-21",
          "created": "2026-05-21",
          "depends_on": [
            "P5.S1"
          ],
          "id": "S2",
          "notes": "",
          "parallel_group": null,
          "plan_path": "docs/plans/2026-05-21-P5-S2-prune-and-repair.md",
          "planning_status": "ratified",
          "refs": [
            "docs/plans/2026-05-21-P5-S2-prune-and-repair.md",
            "docs/reviewer/p5-s2-prune-and-repair-plan",
            "docs/reviewer/p5-s2-prune-and-repair-P5-S2-post-slice"
          ],
          "reviewer_chain": "docs/reviewer/p5-s2-prune-and-repair-P5-S2-post-slice",
          "started": "2026-05-21",
          "status": "done",
          "tasks": [],
          "title": "Prune + repair",
          "worktree_pruned_at": "2026-05-21"
        },
        {
          "blocked_on": null,
          "closed": "2026-05-21",
          "created": "2026-05-21",
          "depends_on": [
            "P5.S1",
            "P5.S2"
          ],
          "id": "S3",
          "notes": "",
          "parallel_group": null,
          "plan_path": "docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md",
          "planning_status": "proposed",
          "refs": [
            "docs/plans/2026-05-21-P5-S3-skill-rewrite-and-subagent-guard.md",
            "docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-plan",
            "docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice"
          ],
          "reviewer_chain": "docs/reviewer/p5-s3-skill-rewrite-and-subagent-guard-P5-S3-post-slice",
          "started": "2026-05-21",
          "status": "done",
          "tasks": [],
          "title": "Skill rewrite + subagent guard + workflow updates",
          "worktree_pruned_at": "2026-05-21"
        }
      ],
      "spec_path": "docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md",
      "started": null,
      "status": "done",
      "title": "Tasktool-owned worktree lifecycle & using-git-worktrees skill collapse"
    }
  ],
  "project": "superstar",
  "schema_version": 1
}
```
