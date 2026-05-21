# Review — 2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md (post-slice, round 1)

- Target: `docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md`
- Request: `docs/reviewer/p5-s1-tasktool-worktree-lifecycle-core-P5-S1-post-slice/r1-2026-05-21T1555-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: blocking — The slice completion gate is not satisfied. In the target checkout, `P5.S1` is still not started or closed: `closed: null`, `started: null`, `status: "ready"`, and no recorded worktree path at `docs/tasklist.json:354-373`. The authoritative checkout is also not closed: `/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:354-373` has `status: "in_progress"`, `closed: null`, `reviewer_chain` still pointing at the plan chain, and null worktree fields. The post-slice chain itself is not usable: `docs/reviewer/p5-s1-tasktool-worktree-lifecycle-core-P5-S1-post-slice/chain.json:8-12` has `rounds: []` and pending checkpoints, and the whole post-slice reviewer directory is untracked. `tasktool artifact status P5.S1 --strict` fails.

F2 — Severity: blocking — The implementation rewrites existing tasklist rows, contradicting the spec’s migration constraint. The spec says existing entries are not rewritten and fields are backfilled on first `tasktool start` (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:92`). But `to_dict()` serializes every dataclass default through `asdict` (`tools/tasktool/serialize.py:11-23`), and the diff adds null/default `worktree_*` fields to historical rows. Example: existing `X12` now has six new worktree fields at `docs/tasklist.json:273-278`. This is a real spec drift, not just formatting churn.

F3 — Severity: important — Read-only worktree commands go through the mutating write context. `cmd_worktree_list` and `cmd_worktree_status` enter `_write_context` at `tools/tasktool/commands.py:1807-1809` and `tools/tasktool/commands.py:1837-1839`, which takes a tasktool lock and enforces authoritative mutation preconditions (`tools/tasktool/commands.py:160-172`). In this review environment both `tasktool worktree list` and `tasktool worktree status P5.S1` fail before producing output because they try to create `.git/tasktool.lock`. These commands should use a read/routing context unless the write lock is intentional and documented.

2. Open questions / assumptions

None needed for the gate decision. The slice is not ready until the tracker, reviewer chain, and artifact state are clean.

3. Suggested document edits

- Record the post-slice review chain as the slice reviewer chain only after it contains a parser-valid ready or ready-with-small-edits round.
- Add a resolution note or follow-up task for the existing-row rewrite issue if the intended behavior changed from the spec.
- If `worktree list/status` intentionally require the write lock, document that operational constraint; otherwise update the implementation.

4. Verification gaps / commands that should be run, if any

I ran:
- `./tools/tasktool/tasktool validate --strict-format` — passed.
- `cd tools && python -m pytest tasktool/tests -q` — `458 passed`, one pytest cache warning due read-only sandbox.
- `./tools/tasktool/tasktool artifact status P5.S1 --strict` — failed.
- `./tools/tasktool/tasktool worktree list` — failed due write-lock creation.
- `./tools/tasktool/tasktool worktree status P5.S1` — failed due write-lock creation.

Overall verdict: revise
