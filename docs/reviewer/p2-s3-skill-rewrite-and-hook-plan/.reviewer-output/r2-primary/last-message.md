**Findings**

F1 — Severity: blocking — The installer instructions are not executable against the current `install.sh`. The plan says to append a `--hook` branch and runs it via `sh` in tests and smoke steps, but the existing script is Bash-only (`set -euo pipefail`, `${BASH_SOURCE[0]}`, `[[ ... ]]`) and has no early argument dispatch. Running `sh tools/tasktool/install.sh --hook` will fail before the appended branch; appending after the existing shim install would also treat `--hook` as the shim “force” argument first. See [plan lines 245-265](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:245), [plan line 304](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:304), [plan line 391](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:391), and current [install.sh line 1](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/install.sh:1). Put the hook branch at the top of the Bash script and invoke it with `bash`, or explicitly convert the whole installer to POSIX sh.

F2 — Severity: important — The proposed orphan check accepts false positives for fully-qualified IDs under the wrong phase. The code adds short slice IDs like `S1` to `known`, then accepts `raw.split(".", 1)[-1] in known`; therefore a filename like `2026-05-18-P99.S1-thing.md` passes if any `S1` exists, even though `P99.S1` has no tasklist row. That undermines the hook’s orphan protection. See [plan lines 107-130](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:107). Fully-qualified filename IDs should require exact fully-qualified matches; short IDs should either be resolved with the same ambiguity rules as `tasktool show`, or only allowed where the filename convention truly permits them.

F3 — Severity: important — The hook validates the working tree, not the staged content being committed. `tasktool validate --strict-format` reads `docs/tasklist.json` from disk, while the hook is supposed to protect the index. A user can stage non-canonical bytes, then normalize only the worktree before committing, and the hook will validate the normalized worktree while committing the stale staged blob. It can also block a clean staged blob because of unstaged worktree dirt. See [plan lines 211-216](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:211). The plan needs an index-aware check, for example exporting `git show :docs/tasklist.json` to a temp file and validating that exact file, or adding a tasktool mode that validates staged content.

F4 — Severity: important — The Task 1 CLI plumbing does not match the existing `cmd_validate` contract. The current function signature is `cmd_validate(..., format=...) -> tuple[int, str]`, and the CLI writes the returned text. The plan snippet calls `commands.cmd_validate(..., fmt=args.format, ...)`, returns only `rc`, and drops stdout; the new test also expects JSON under `payload["findings"]`, while current JSON output is `{"ok", "errors", "warnings"}`. See [plan lines 75-78](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:75), [plan lines 151-157](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md:151), and current [commands.py line 401](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/commands.py:401). The plan should preserve `(rc, text)`, use `format=`, and either adapt tests to `errors` or explicitly migrate the validate JSON schema everywhere.

F5 — Severity: minor — `docs/tasklist.json` says the S3 plan was “set as plan_path”, but `plan_path` is still `null` and the plan is only in `refs`. See [tasklist line 58](/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:58). This is not a plan logic blocker, but it will make `tasktool show/brief` less useful for workers.

**Open Questions / Assumptions**

No prior findings exist to mark resolved or unresolved.

I assume the hook is intended to protect committed/staged content, not merely current worktree bytes.

**Suggested Document Edits**

Update Task 3 to add an early Bash `--hook` branch before shim installation, and change all installer invocations from `sh .../install.sh --hook` to `bash .../install.sh --hook`, unless the script is intentionally rewritten to POSIX sh.

Revise the orphan validator pseudocode so exact fully-qualified IDs are required when the filename contains a phase prefix, and add a regression test for `P99.S1` when `P1.S1` exists.

Add staged/worktree mismatch hook tests: staged non-canonical plus normalized worktree must fail; staged canonical plus dirty non-canonical worktree should pass or have explicitly documented behavior.

Align `cmd_validate` examples and tests with the existing `(rc, text)` and `format` contract.

**Verification Gaps**

Add tests beyond the current plan:
`python -m pytest tools/tasktool/tests/test_validate_orphans.py -v`
with a wrong-phase qualified ID case.

`python -m pytest tools/tasktool/tests/test_pre_commit_hook.py -v`
with staged/worktree divergence cases.

Run the full tasktool suite:
`python -m pytest tools/tasktool/tests -q`

**Overall Verdict**

revise