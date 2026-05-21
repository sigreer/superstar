# Review — 2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md (post-slice, round 2)

- Target: `docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md`
- Request: `docs/reviewer/p5-s1-tasktool-worktree-lifecycle-core-P5-S1-post-slice/r2-2026-05-21T1613-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — Severity: blocking — `--adopt` accepts the main checkout as if it were an external linked worktree. The spec requires `--adopt <path>` to record an externally-created linked worktree, and auto-adopt only when cwd is already inside a linked worktree (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:117-119`). But `linked_worktree_branch()` returns a branch for any path in `git worktree list --porcelain`, including the primary checkout (`tools/tasktool/worktree_lifecycle.py:78-96`), and `_apply_start_adopt()` records that result without excluding the authoritative checkout (`tools/tasktool/commands.py:865-879`). I verified this in a temp repo: `tasktool start P1.S1 --adopt <repo-root>` exits 0 and records `worktree_path: "."`, `worktree_branch: "main"`. That breaks the one-slice-one-worktree authority model and can poison later status/prune behavior.

F2 — Severity: blocking — The post-slice completion gate is still not satisfied in repo state. The target checkout’s `docs/tasklist.json` still has `P5.S1` as `started: null`, `status: "ready"`, and the plan reviewer chain, not the post-slice chain (`docs/tasklist.json:263-280`). The authoritative checkout has only a staged start mutation to `in_progress`, not a committed close (`/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:264-280`, staged diff changes `started/status` only). The post-slice `chain.json` still records only round 1 with `merged_verdict: "revise"` and `final-ready: "pending"` (`docs/reviewer/p5-s1-tasktool-worktree-lifecycle-core-P5-S1-post-slice/chain.json:8-122`), while the whole post-slice reviewer directory is untracked. This is not closeable yet.

2. Open questions / assumptions

Assumption: the round-2 reviewer files currently present in the directory are in-progress artifacts and still need to be written into `chain.json` before `tasktool close P5.S1` is attempted.

3. Suggested document edits

Add a resolution note for the adopt-main-checkout defect and add tests that `start --adopt <authoritative-root>` / `worktree adopt <id> <authoritative-root>` are refused.

4. Verification gaps / commands that should be run, if any

Ran:
- `./tools/tasktool/tasktool validate --strict-format` — `ok`
- `./tools/tasktool/tasktool artifact status P5.S1 --strict` — `artifact status: ok`
- `./tools/tasktool/tasktool worktree status P5.S1` — `P5.S1: no worktree recorded`
- focused worktree tests — `43 passed`
- full tasktool suite — `462 passed`, with only a pytest cache warning due read-only `.pytest_cache`
- temp-repo adopt-main probe — reproduced the bug: return code 0, recorded `.` / `main`

Overall verdict: revise
