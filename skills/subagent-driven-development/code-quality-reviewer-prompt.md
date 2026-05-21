# Code Quality Reviewer Prompt Template

Use this template when dispatching a code quality reviewer subagent.

**Purpose:** Verify implementation is well-built (clean, tested, maintainable)

**Only dispatch after spec compliance review passes.**

```
Task tool (general-purpose):
  Use template at requesting-internal-review/code-reviewer.md

  ## Subagent Role (mandatory)

  You were dispatched by a coordinator. The first command you run in any
  shell you open MUST be:

  ```sh
  export SUPERSTAR_SUBAGENT_ROLE=code-quality-reviewer
  ```

  This is a load-bearing signal. The tasktool CLI uses it to refuse
  `tasktool start <id>` (slice creation belongs to the parent). Do not
  unset it; do not start the slice yourself; do not run `tasktool start`
  at all. If you need to record progress, use `tasktool note`,
  `tasktool ref`, or ask the coordinator.

  DESCRIPTION: [task summary, from implementer's report]
  PLAN_OR_REQUIREMENTS: Task N from [plan-file]
  BASE_SHA: [commit before task]
  HEAD_SHA: [current commit]
```

**In addition to standard code quality concerns, the reviewer should check:**
- Does each file have one clear responsibility with a well-defined interface?
- Are units decomposed so they can be understood and tested independently?
- Is the implementation following the file structure from the plan?
- Did this implementation create new files that are already large, or significantly grow existing files? (Don't flag pre-existing file sizes — focus on what this change contributed.)

**Code reviewer returns:** Strengths, Issues (Critical/Important/Minor), Assessment
