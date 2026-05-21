1. Findings

F7 Severity: important — NEW  
Referenced reviewer-chain directories still do not get dirty-child status checks. The spec requires `artifact status` to report workflow artifact files that are unstaged and referenced artifact paths that are untracked or unstaged (`docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md:103-111`). The plan now makes `_workflow_files` return only the reviewer directory for `docs/reviewer/` (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:753-762`), but `cmd_artifact_status` checks dirt only by exact referenced path via `status_map.get(rel)` (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:783-789`). Git porcelain reports dirty/untracked children like `docs/reviewer/x1-artifact-plan/chain.json`, not the directory path, so a referenced reviewer directory can contain untracked or modified review files and still pass `artifact status <id> --strict`. The new regression only covers a registered chain after committing `chain.json` (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:586-597`), so this loose-reviewer-artifact case remains untested.

F2 Severity: important — RESOLVED  
The target-slug orphan scan now lowercases row ID/slug matching and implements the reviewer suffix rule with `-spec` / `-plan` (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:1046-1065`). The plan also adds same-slug reviewer-chain orphan coverage (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:944-958`).

F6 Severity: important — RESOLVED  
The reviewer-directory false-positive path is addressed by making `_workflow_files` treat reviewer chains as first-class directories instead of returning their children (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:753-762`), with a regression that a registered chain containing `chain.json` passes strict global status (`docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md:586-597`).

F1 Severity: blocking — RESOLVED  
No regression found from the prior resolution.

F3 Severity: important — RESOLVED  
No regression found from the prior resolution.

F4 Severity: important — RESOLVED  
No regression found from the prior resolution; the prior follow-up is covered by F6.

F5 Severity: important — RESOLVED  
No regression found from the prior resolution.

2. Open questions / assumptions

I assume a reviewer-chain directory reference is intended to cover the directory transactionally, including `chain.json`, round files, and resolution files under that directory.

3. Suggested document edits

Add a helper that checks a referenced directory path against all git status entries at or below that path, for example treating any `status_path == rel` or `status_path.startswith(rel.rstrip("/") + "/")` as relevant to `referenced-artifact-unstaged`.

Add a regression where `docs/reviewer/x1-artifact-plan/` is referenced, `chain.json` is untracked or modified after the reference exists, and `tasktool artifact status X1 --strict` reports `referenced-artifact-unstaged`.

4. Verification gaps / commands that should be run

Keep the planned gates, after adding the reviewer-directory dirty-child test:

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_artifacts.py tools/tasktool/tests/test_artifact_cli.py tools/tasktool/tests/test_worktree_authority.py -q
PYTHONPATH=tools pytest tools/tasktool/tests -q
tools/tasktool/tasktool validate --strict-format
git diff --check
```

Overall verdict: revise

