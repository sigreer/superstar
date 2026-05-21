1. Findings

F1. RESOLVED. Severity: blocking. The spec still defines invocation root, authoritative write root, stored path, write-root existence checks, implementation-worktree refusal, and write-root staging at `docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md:66-88`.

F2. RESOLVED. Severity: important. `artifact status` defines `--strict`, exit behavior, JSON problem shape, and machine-readable problem fields at `docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md:90-138`.

F3. RESOLVED. Severity: important. `tasktool prepare` has explicit grammar for `cross`, `phase`, `slice <phase-id>`, and `existing <id>`, and rejects top-level `--id` mode at `docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md:177-205`.

F4. RESOLVED. Severity: important. `artifact commit` defines target-slug derivation, scan scope, reviewer-directory matching, and archive handling at `docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md:168-175`.

F5. RESOLVED. Severity: important. The rollout now stages the newly written spec with `tasktool artifact add XNN --kind spec --path ...` before review/status/commit, and the test matrix covers `prepare --spec`, creating the file, strict status reporting `referenced-artifact-unstaged`, and remediation through `artifact add` or `artifact commit`: `docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md:111-115`, `:261`, `:275-288`.

F6. Severity: important. `artifact commit` is internally inconsistent for the same unstaged referenced-artifact case. The status section says `artifact status <id> --strict` must fail when a referenced artifact exists but is untracked/unstaged, and its remediation text names `tasktool artifact commit <id> --message ...`: `docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md:111-115`. The testing section also says `artifact commit` can stage that prepared future artifact: `:261`. But the `artifact commit` algorithm says it first runs `artifact status <id> --strict` before staging every referenced artifact: `:150-154`. If implemented literally, `artifact commit` will refuse before it can perform the staging that the diagnostic and test promise.

2. Open questions / assumptions

- I assume `artifact commit` is intended to be a valid closeout shortcut for already referenced but unstaged artifacts, not only a commit wrapper after every artifact has already been staged by `artifact add`.

3. Suggested document edits

- Change `artifact commit` ordering to stage `docs/tasklist.json` and referenced existing artifacts before running the strict status check, while still refusing missing references and unrelated staged paths.
- Or, if `artifact commit` should not remediate unstaged artifacts, remove it from the `referenced-artifact-unstaged` remediation message and update test 16 accordingly.

4. Verification gaps / commands that should be run

I ran:

```bash
PYTHONPATH=tools tools/tasktool/tasktool validate --strict-format
git diff --check
```

Both passed.

Implementation planning should still include:

```bash
PYTHONPATH=tools pytest tools/tasktool/tests -q
```

Overall verdict: revise