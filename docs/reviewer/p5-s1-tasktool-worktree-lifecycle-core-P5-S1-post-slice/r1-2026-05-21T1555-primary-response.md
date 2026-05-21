# Review — 2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md (post-slice, round 1)

- Target: `docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md`
- Request: `docs/reviewer/p5-s1-tasktool-worktree-lifecycle-core-P5-S1-post-slice/r1-2026-05-21T1555-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: blocking — The post-slice completion gate is not satisfied. The authoritative tracker still has `P5.S1` as `in_progress`, not `done`, at `/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:367-368`. The only recorded `reviewer_chain` for the row is still the plan review chain, not the post-slice chain, at `/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:363-366`. The new post-slice chain has no review rounds (`rounds: []`) and pending sweep checkpoints in `docs/reviewer/p5-s1-tasktool-worktree-lifecycle-core-P5-S1-post-slice/chain.json:8-11`, and that whole post-slice reviewer directory is untracked in the implementation worktree. `tasktool artifact status P5.S1 --strict` currently fails with `unstaged-tasklist-with-workflow-artifacts`.

F2 — Severity: blocking — The schema implementation rewrites existing tasklist rows, contradicting the spec’s migration constraint. The spec says existing entries are not rewritten and `tasktool start` backfills on first invocation (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:92`). But `serialize.to_dict()` serializes every dataclass default via `asdict` (`tools/tasktool/serialize.py:11-23`), so a save adds `worktree_*` fields to unrelated historical rows. The dirty authoritative `docs/tasklist.json` shows this happening, for example on existing `X12` at `/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:273-278`. This is not just churn: it is the direct source of the dirty authoritative artifact state blocking closeout.

F3 — Severity: important — Read-only worktree commands are wired through the mutating write context. `cmd_worktree_list` and `cmd_worktree_status` enter `_write_context` (`tools/tasktool/commands.py:1807-1809`, `tools/tasktool/commands.py:1837-1839`), which takes a tasktool lock and enforces authoritative checkout cleanliness (`tools/tasktool/commands.py:160-172`). In this review environment both `tasktool worktree list` and `tasktool worktree status P5.S1` fail before producing output because they try to create `.git/tasktool.lock`. Even outside this sandbox, read-only status/list should not be blocked by dirty authoritative mutation preconditions.

2. Open questions / assumptions

None needed for the gate decision. The slice is not ready to close until the tracker/artifact state is clean and the post-slice review chain contains a parser-valid ready verdict.

3. Suggested document edits

- Add a resolution note to the plan or review chain explaining how the existing-row rewrite issue is fixed or intentionally accepted. Right now it conflicts with the spec.
- Register and commit the post-slice reviewer chain only after it contains an actual completed review round.
- If read-only `worktree list/status` intentionally require the write lock, document that tradeoff; otherwise switch them to a read/routing context.

4. Verification gaps / commands that should be run

I ran:
- `./tools/tasktool/tasktool validate --strict-format` — passed with `ok`.
- `cd tools && python -m pytest tasktool/tests -q` — 458 passed, with only a pytest cache write warning from the read-only sandbox.
- `cd tools && python -m pytest tasktool/tests/test_worktree_naming.py tasktool/tests/test_worktree_lifecycle.py tasktool/tests/test_start_worktree.py tasktool/tests/test_worktree_subcommands.py tasktool/tests/test_project_setup_gitignore.py -q` — 57 passed, same cache warning.
- `./tools/tasktool/tasktool artifact status P5.S1 --strict` — failed.
- `./tools/tasktool/tasktool worktree list` and `./tools/tasktool/tasktool worktree status P5.S1` — failed due lock creation through the write context.

Overall verdict: revise
