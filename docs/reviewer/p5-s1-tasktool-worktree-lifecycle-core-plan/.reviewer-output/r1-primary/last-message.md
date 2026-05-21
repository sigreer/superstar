1. Findings

F1 (Severity: blocking) `cmd_start` is ordered so disk mutation happens before lifecycle refusal checks. The plan calls `_apply_start_*` before `_start_item` in `cmd_start` (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:813-827`), while the existing `_start_item` is where `DONE` and blocked-without-`--resume` refusals happen (`tools/tasktool/commands.py:569-578`). That means `tasktool start P1.S1` on a blocked or done row can create/adopt a worktree and only then raise, leaving an unrecorded branch/worktree behind. Move lifecycle preflight before any git mutation, and add tests for blocked and done rows with no created `.worktrees/` entry or branch.

F2 (Severity: blocking) The auto-adopt test plan is not executable and does not cover the spec’s routed authoritative-checkout requirement. The spec requires CLI integration for routed authoritative checkout and invocation from inside a linked worktree (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:322-325`). The plan’s fixture uses `config init-local` (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:744-745`) and then creates the slice after the initial commit (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:746-749`). The auto-adopt test then runs from a new linked worktree (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:1103-1114`), but that linked worktree is based on `HEAD` and will not contain the uncommitted tasklist row. It should set up an authoritative main checkout, commit or route the tasklist state, create a linked worker, and assert the mutation lands in the authoritative `docs/tasklist.json`.

F3 (Severity: important) `worktree status` hardcodes `main` instead of the configured authoritative parent branch. The spec says the branch is forked from the slice’s parent branch per existing tasktool rules (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:103`) and status reports ahead/behind parent (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:182`). The planned implementation uses `"main..." + item.worktree_branch` (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:1545-1556`), while the current command layer already resolves `authoritative_branch` from config (`tools/tasktool/commands.py:138-158`). Use that configured branch and add a non-`main` fixture.

F4 (Severity: important) The installer acceptance gate is not actually planned. The spec says `.worktrees/` is git-ignored and the installer adds it if absent (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:44`, `docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:216-220`), and P5.S1 tests include “Installer adds `.gitignore` entry exactly once” (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:244-252`). The plan only edits `skills/project-setup/SKILL.md` and adds a legacy-dir helper (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:1710-1808`); `tools/tasktool/install.sh` has no `.gitignore` handling (`tools/tasktool/install.sh:1-130`). Either add installer work/tests to S1 or revise the spec/acceptance language to make project-setup, not the installer, the owner.

F5 (Severity: important) The planned strict validation does not actually enforce raw JSON types. The plan says `validate.py` will strictly check `worktree_in_place` as `bool|absent` (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:31`) but the proposed deserializer coerces with `bool(sd.get(...))` (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:315-320`, `docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:330-335`). Current validation runs after `load_project()` (`tools/tasktool/commands.py:1394-1397`), so `"worktree_in_place": "false"` becomes `True` before validation can reject it. Add raw schema validation or remove coercion and test malformed raw tasklist JSON.

F6 (Severity: minor) Several implementation snippets call `subprocess.run`, but `commands.py` currently imports subprocess only as `_subprocess` (`tools/tasktool/commands.py:6`). Planned snippets use bare `subprocess` in `_apply_start_default` and `cmd_worktree_status` (`docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:876-889`, `docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md:1547-1565`). The plan should explicitly add `import subprocess` or use `_subprocess`; otherwise the first new path will fail with `NameError`.

2. Open questions / assumptions

- Is `.worktrees/` creation meant to be owned by `tools/tasktool/install.sh --hook`, by global shim installation, or only by `project-setup`? The spec says installer, but the plan implements only project-setup wording.
- Should `tasktool start` on a blocked row with `--resume` create the worktree before or after clearing `blocked_on`? The current semantics imply lifecycle state should be validated first, then git mutation.

3. Suggested document edits

- Reorder Task 4’s `cmd_start` pseudocode so `_start_item` or a non-mutating equivalent preflight runs before `_apply_start_default`, `_apply_start_adopt`, or `_apply_start_in_place`.
- Replace the auto-adopt fixture with an authoritative-routing fixture: main checkout configured with `init-authority`, linked worker checkout, command run from worker, assertion against main checkout’s tasklist.
- Add a Task 11 subtask for installer `.gitignore` behavior, or explicitly remove installer claims from the S1 plan/spec.
- Add malformed raw JSON validation tests for `worktree_in_place`, `worktree_path`, `worktree_branch`, and audit-date fields.

4. Verification gaps / commands that should be run

- `cd tools && python -m pytest tasktool/tests/test_lifecycle_start.py -v`
- New tests for blocked/done `start` with no branch/path side effects.
- New authoritative-routing auto-adopt test from inside a linked worktree.
- `./tools/tasktool/tasktool validate --strict-format` against a tasklist containing intentionally malformed `worktree_*` raw values.

Overall verdict: revise

