1. Findings

F2 Severity: important — UNRESOLVED  
The target-slug orphan scan still does not faithfully cover reviewer-chain directories. The spec requires `docs/reviewer/` matching by slug plus review-kind suffix (`docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md:171-175`). The plan’s helper instead checks only `row_id in rel and slug in rel` (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:1010-1021`). That is case-sensitive and does not encode the review-kind suffix rule, so common chain names like lowercase `x17-...-plan` can be missed. The only regression test covers a dated plan orphan, not reviewer-chain orphans (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:908-923`).

F6 Severity: important — NEW  
The reviewer-directory status fix creates false positives for registered reviewer chains. `_workflow_files` returns both reviewer directories and their child files (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:739-747`), while `referenced_paths_for_item` only marks the registered directory as referenced (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:690-696`). The global unreferenced scan then reports every `docs/reviewer/.../chain.json` child because `rel.startswith("docs/reviewer/")` is always true (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:783-786`). A correctly registered chain directory can therefore still make `artifact status --strict` fail.

F1 Severity: blocking — RESOLVED  
The plan now distinguishes staged index state from unstaged worktree state. `referenced_artifact_is_unstaged` accepts cleanly staged paths and rejects untracked or unstaged worktree changes (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:680-719`), with explicit staged-reference coverage (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:558-570`).

F3 Severity: important — RESOLVED  
`--allow-missing` is now constrained to spec, plan, and handoff artifacts in normalization (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:221-222`) and covered by a reviewer rejection test (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:360-376`).

F4 Severity: important — RESOLVED, with follow-up in F6  
The plan now treats reviewer-chain directories as first-class workflow artifacts (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:739-747`) and adds a directory orphan test (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:573-583`). The remaining problem is the child-file false positive described in F6.

F5 Severity: important — RESOLVED  
The dirty-tasklist diagnostic is now included in status logic (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:771-782`) and has a strict-status regression test (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:586-598`).

2. Open questions / assumptions

I assume reviewer-chain refs are intended to be directory refs, and that registering `docs/reviewer/<chain>/` should cover the chain’s `chain.json` and round files.

3. Suggested document edits

Update `same_slug_orphans` to normalize row IDs/case and implement the spec’s reviewer-chain rule directly: reviewer directories should match by slug plus `-spec` / `-plan` review suffix, not by raw `row_id in rel`.

Change `_workflow_files` or the unreferenced filter so a referenced reviewer directory suppresses all descendants. Add a regression where `docs/reviewer/x1-artifact-plan/` is registered and `artifact status --strict` does not report `docs/reviewer/x1-artifact-plan/chain.json`.

4. Verification gaps / commands that should be run

Add targeted tests for:
- `artifact commit` refusing an unreferenced same-slug reviewer-chain directory.
- `artifact status --strict` accepting a registered reviewer-chain directory with `chain.json`.

Then keep the planned gates:

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_artifacts.py tools/tasktool/tests/test_artifact_cli.py tools/tasktool/tests/test_worktree_authority.py -q
PYTHONPATH=tools pytest tools/tasktool/tests -q
tools/tasktool/tasktool validate --strict-format
git diff --check
```

Overall verdict: revise