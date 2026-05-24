1. Findings

F1 — Severity: blocking  
`infer-step` does not implement the slice inference contract from the reviewed spec. The spec says a slice with `phase.spec_path` absent must infer `spec` regardless of `slice.plan_path` (`docs/specs/2026-05-23-P6-programmatic-workflow-enhancements-design.md:102-108`). The plan’s implementation snippet also includes `has_phase_spec` and returns `spec` when it is absent (`docs/plans/2026-05-23-P6.S1-workflow-step-field.md:942-950`). The committed code ignores `phase.spec_path` and infers from `slice.plan_path` alone (`tools/tasktool/commands.py:2352-2368`). I reproduced the mismatch with a project containing no phase spec and a ratified slice plan; `commands.infer_step_for_id(..., "P6.S1")` returned `{'step': 'implement', 'blocked': False}`. The tasklist note explicitly records this as an intentional deviation (`docs/tasklist.json:316`), so this needs either a code/test fix to honor the spec or a reviewed spec/plan amendment before the slice can pass.

2. Open questions / assumptions

I’m treating the spec as authoritative over the internally contradictory plan tests because this is a post-slice gate against the accepted design. If the desired product behavior is actually “slice plan implies past spec even when the phase has no spec,” update the spec and acceptance criteria explicitly.

3. Suggested document edits

Add a resolution note to the plan or tasklist after fixing F1, including the exact inference rule chosen and the regression test added. If the implementation keeps the current behavior, amend `docs/specs/2026-05-23-P6-programmatic-workflow-enhancements-design.md:102-108` and the plan snippet at `docs/plans/2026-05-23-P6.S1-workflow-step-field.md:942-950` so future agents do not inherit two different contracts.

4. Verification gaps / commands that should be run

I ran:

`python -m pytest tools/tasktool/tests/test_model.py tools/tasktool/tests/test_serialize.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_render.py tools/tasktool/tests/test_brief.py tools/tasktool/tests/test_schema_gen.py tools/tasktool/tests/test_cli_integration.py tools/tasktool/tests/test_v1_compat.py skills/external-review/tests/test_workflow_block_calls.py -q`  
Result: `201 passed`, with one `.pytest_cache` read-only warning.

`tools/tasktool/tasktool validate`  
Result: `ok`.

`tools/tasktool/tasktool infer-step P6.S1 --format json`, `tools/tasktool/tasktool infer-step P6 --format json`, and `tools/tasktool/tasktool infer-step --all --diff --format json`  
Result: no drift, but that does not cover the missing-phase-spec edge case in F1.

Add/run a regression test for: phase has no `spec_path`, slice has `plan_path`, slice planning status is `ratified`; expected result must match the resolved contract.

Overall verdict: revise

