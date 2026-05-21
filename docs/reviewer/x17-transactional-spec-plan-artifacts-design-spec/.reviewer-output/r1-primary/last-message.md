1. Findings

F1. Severity: blocking. The spec leaves path resolution ambiguous under authoritative routing. It says `artifact add` routes through `_write_context`, accepts absolute paths inside the invocation repository, requires existence, and stages the artifact path, while also requiring the worktree-routing test to stage the authoritative checkout, not the worktree copy: `docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md:51`, `:54`, `:55`, `:61`, `:181`. In the current code, routed mutations clearly separate invocation root from write root (`tools/tasktool/commands.py:124-145`), and existing review-chain handling resolves explicit paths against the invocation root (`tools/tasktool/commands.py:501-523`). The spec must define whether artifact paths are interpreted and existence-checked against the invocation root or authoritative write root, and how files created in a linked worktree are handled. Otherwise the core transaction can validate one checkout and stage another.

F2. Severity: important. `artifact status --strict` is part of the required tests and rollout flow but is absent from the command contract. The syntax only lists `tasktool artifact status [<id>] [--format text|json]`, while later sections require `--strict` and non-zero exit behavior: `docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md:70-72`, `:176`, `:205`, `:212`. Add `--strict` to the design, define exit codes, and specify whether JSON output includes machine-readable problem severities.

F3. Severity: important. `tasktool prepare` is underspecified and internally inconsistent enough to make CLI implementation guessy. The example only shows `prepare cross`, the prose says it can create `cross`, `phase`, or `slice`, error handling mentions `--id`, and tests use `prepare --id X17 --spec ...` without a kind subcommand: `docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md:117-128`, `:163`, `:180`. The spec needs an explicit grammar for create-new versus register-existing, including required `phase_id` for slices and whether existing-row mode is `prepare --id` or `prepare cross --id`.

F4. Severity: important. `artifact commit` depends on “unreferenced dated artifacts for that ID's slug,” but neither “ID's slug” nor the scan scope is defined, and it conflicts with the prior statement that `artifact status <id>` is limited to that row and its references: `docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md:82`, `:98`. Define the slug source, filename matching rules, and which directories are searched, or remove that refusal from commit and leave orphan detection to global status.

2. Open questions / assumptions

- Should `artifact add` ever copy or move an artifact from an implementation worktree into the authoritative checkout, or must the artifact already exist in the authoritative checkout?
- Are archived phase files first-class registerable artifacts for active rows, or should archive handling stay owned by `archive-phase`?
- Should `artifact commit` allow already staged unrelated workflow docs for a different ID, or refuse any staged path not belonging to the target row?

3. Suggested document edits

- Add a “Path resolution and routed writes” subsection defining invocation root, authoritative write root, repo-relative storage, existence checks, and staging behavior.
- Replace the `prepare` section with a concrete CLI grammar for `prepare cross`, `prepare phase`, `prepare slice`, and existing-row registration.
- Add `--strict` to `artifact status` syntax and define return codes for text and JSON modes.
- Define artifact slug matching rules for commit/status, especially for reviewer chains and dated handoff/plan files.

4. Verification gaps / commands that should be run

I ran `PYTHONPATH=tools tools/tasktool/tasktool validate --strict-format` in `/home/simon/Dev/sigreer/skills/superstar`; it returned `ok`.

Implementation planning should still include:
- `PYTHONPATH=tools pytest tools/tasktool/tests -q`
- `tools/tasktool/tasktool validate --strict-format`
- `git diff --check`
- A routed-worktree fixture that proves path interpretation and staging happen in the checkout the spec intends.

Overall verdict: revise

