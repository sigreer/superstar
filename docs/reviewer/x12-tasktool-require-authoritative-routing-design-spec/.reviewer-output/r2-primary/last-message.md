1. Findings

F1 — Severity: blocking — RESOLVED  
The migration bootstrap deadlock is addressed. The spec now requires `migrate-from-local --authority-root <path>` and makes `--local-root` explicit/defaulted to CWD, so the drifted no-config worktree can be read while the authority checkout is written without first requiring config in either tree. See `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md:67-80` and the acceptance test at `:149`.

F2 — Severity: important — RESOLVED  
The setup order is now consistent: `config init-authority --branch <branch>` before `tasktool init`, including the project-setup skill change and rollout example. See `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md:43`, `:115`, and `:186-193`.

F3 — Severity: important — RESOLVED  
The spec now consistently uses the existing `--branch <branch>` syntax for `init-authority`, matching `tools/tasktool/cli.py:29-30`.

F4 — Severity: important — RESOLVED  
The migration surface now covers `Project`, `Phase`, `Slice`, `Task`, `CrossCutting`, and `ArchivedPhase` via dataclass traversal, including the previously omitted fields and nested task rows. See `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md:82-90` and tests at `:155-157`.

F5 — Severity: minor — RESOLVED  
`validate --normalise` is now listed as mutating while plain `validate` remains read-only. See `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md:41`, `:45`, and `:143`.

F6 — Severity: minor  
The conflict-policy wording is internally inconsistent. The spec says `--accept-local` is “default” at `docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md:103`, but immediately says no flag prompts in a TTY and errors in non-TTY contexts at `:105-106`. The error-handling bullet at `:136` also says “with `--accept-local` and no TTY when prompt would be needed,” but a prompt is only needed when neither accept flag is supplied. This is easy to misread when implementing CLI defaults.

2. Open questions / assumptions

- I assume “authoritative-only row → conflict” should not silently delete rows under `--accept-local`; the spec says it is flagged as conflict, but the detailed resolution behavior for row add/delete conflicts is still implicit.

3. Suggested document edits

- Change `--accept-local (default)` to something like: “`--accept-local`: local copy wins when explicitly selected.”
- Change the error-handling bullet to: “`migrate-from-local` with neither accept flag and non-TTY stdin: `CommandError`, demand explicit `--accept-local` or `--accept-authoritative`.”

4. Verification gaps / commands that should be run

- Add one migration test where the authoritative tasklist has an extra row missing locally, to assert the conflict behavior does not accidentally delete main-ahead work.
- Run `PYTHONPATH=tools pytest tools/tasktool/tests` after implementation.

Overall verdict: ready with small edits