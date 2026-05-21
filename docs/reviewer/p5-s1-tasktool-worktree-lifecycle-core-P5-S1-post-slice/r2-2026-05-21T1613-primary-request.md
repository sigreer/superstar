<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 2 of p5-s1-tasktool-worktree-lifecycle-core-P5-S1-post-slice.

In incremental mode:
- Verify whether prior findings are resolved per the resolution report below.
- Reuse the existing finding IDs (F1, F2, …). If a prior finding is resolved,
  mark it RESOLVED in your findings list with its original ID. If still
  unresolved, keep its ID.
- Only introduce new finding IDs for genuine regressions caused by the fix, or
  blocking issues clearly missed in earlier rounds. Do not reopen broad review
  unless prior fixes changed broad architecture.

## Review chain summary

| round | verdict | findings | blocking |
|---|---|---|---|
| 1 | revise | 3 | 2 |

## Prior-round findings

Source: merged findings from r1 (authoritative)

# Merged findings for r1

## Primary

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


## Sweep 1

# Review — 2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md (post-slice, round 1)

- Target: `docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md`
- Request: `docs/reviewer/p5-s1-tasktool-worktree-lifecycle-core-P5-S1-post-slice/r1-2026-05-21T1555-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

S1.F1 — Severity: blocking — The slice completion gate is not satisfied. In the target checkout, `P5.S1` is still not started or closed: `closed: null`, `started: null`, `status: "ready"`, and no recorded worktree path at `docs/tasklist.json:354-373`. The authoritative checkout is also not closed: `/home/simon/Dev/sigreer/skills/superstar/docs/tasklist.json:354-373` has `status: "in_progress"`, `closed: null`, `reviewer_chain` still pointing at the plan chain, and null worktree fields. The post-slice chain itself is not usable: `docs/reviewer/p5-s1-tasktool-worktree-lifecycle-core-P5-S1-post-slice/chain.json:8-12` has `rounds: []` and pending checkpoints, and the whole post-slice reviewer directory is untracked. `tasktool artifact status P5.S1 --strict` fails.

S1.F2 — Severity: blocking — The implementation rewrites existing tasklist rows, contradicting the spec’s migration constraint. The spec says existing entries are not rewritten and fields are backfilled on first `tasktool start` (`docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md:92`). But `to_dict()` serializes every dataclass default through `asdict` (`tools/tasktool/serialize.py:11-23`), and the diff adds null/default `worktree_*` fields to historical rows. Example: existing `X12` now has six new worktree fields at `docs/tasklist.json:273-278`. This is a real spec drift, not just formatting churn.

S1.F3 — Severity: important — Read-only worktree commands go through the mutating write context. `cmd_worktree_list` and `cmd_worktree_status` enter `_write_context` at `tools/tasktool/commands.py:1807-1809` and `tools/tasktool/commands.py:1837-1839`, which takes a tasktool lock and enforces authoritative mutation preconditions (`tools/tasktool/commands.py:160-172`). In this review environment both `tasktool worktree list` and `tasktool worktree status P5.S1` fail before producing output because they try to create `.git/tasktool.lock`. These commands should use a read/routing context unless the write lock is intentional and documented.

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



## Resolution report for prior round

# Resolution for r1

## F1
Status: deferred
Evidence:
- See F2; root cause is the historical-row rewrite. Fixed F2 resolves the dirty authoritative state. The `tasktool close P5.S1` step is intentionally deferred until r2 returns ready.

Notes:
F1 is circular at request time — the post-slice chain did not yet exist, and close happens after a passing verdict. The dirty-authoritative portion of F1 is driven entirely by F2.

## F2
Status: fixed
Evidence:
- Commit: 48ead69
- Files: `tools/tasktool/serialize.py`, `tools/tasktool/tests/test_serialize.py`, `tools/tasktool/tests/test_start_worktree.py`, `docs/tasklist.json`
- Verification: `cd tools && python -m pytest tasktool/tests -q` (462 passed); `git diff main -- docs/tasklist.json` returns empty — every spurious worktree_* default added by commit 46c94ed to historical rows has been removed via serializer round-trip.

Notes:
to_dict now omits worktree_* keys whose values equal dataclass defaults (None for the path/branch/pruned_at trio, False for the in_place/prune_pending booleans). Historical rows in docs/tasklist.json reverted by round-tripping through the corrected serializer (load_project → save_project). Two pre-existing tests in test_start_worktree.py that asserted `sl["worktree_path"] is None` were updated to use `.get()` to reflect the new default-omission behaviour. New test_serialize.py tests assert default rows emit no worktree_* keys and non-default values (e.g. worktree_in_place=True) still round-trip.

## F3
Status: fixed
Evidence:
- Commit: 48ead69
- Files: `tools/tasktool/commands.py`, `tools/tasktool/tests/test_worktree_subcommands.py`
- Verification: `./tools/tasktool/tasktool worktree list` and `./tools/tasktool/tasktool worktree status P5.S1` both exit 0 from inside the linked worktree; new test `test_worktree_list_and_status_are_readonly_under_dirty_authoritative` asserts both commands succeed when the authoritative tasklist is dirty (a precondition that fails under `_write_context`).

Notes:
Added `_read_context` alongside `_write_context` in `tools/tasktool/commands.py`. It resolves the authoritative checkout and validates the branch but acquires no lock and does not call `_ensure_authoritative_tasklist_clean`. `cmd_worktree_list` and `cmd_worktree_status` switched from `_write_context` to `_read_context`.


## Changes since prior round

Worktree status: dirty

### git diff base..HEAD

diff --git a/docs/tasklist.json b/docs/tasklist.json
index bcd19de..1206cad 100644
--- a/docs/tasklist.json
+++ b/docs/tasklist.json
@@ -48,13 +48,7 @@
       "refs": [],
       "started": null,
       "status": "done",
-      "title": "Default external-review prompt transport to stdin",
-      "worktree_branch": null,
-      "worktree_in_place": false,
-      "worktree_path": null,
-      "worktree_prune_pending": false,
-      "worktree_prune_pending_at": null,
-      "worktree_pruned_at": null
+      "title": "Default external-review prompt transport to stdin"
     },
     {
       "closed": "2026-05-18",
@@ -64,13 +58,7 @@
       "refs": [],
       "started": null,
       "status": "done",
-      "title": "Add repo-local tasktool launcher",
-      "worktree_branch": null,
-      "worktree_in_place": false,
-      "worktree_path": null,
-      "worktree_prune_pending": false,
-      "worktree_prune_pending_at": null,
-      "worktree_pruned_at": null
+      "title": "Add repo-local tasktool launcher"
     },
     {
       "closed": "2026-05-19",
@@ -83,13 +71,7 @@
       ],
       "started": null,
       "status": "done",
-      "title": "Spot fix: parse bold external-review verdict headings",
-      "worktree_branch": null,
-      "worktree_in_place": false,
-      "worktree_path": null,
-      "worktree_prune_pending": false,
-      "worktree_prune_pending_at": null,
-      "worktree_pruned_at": null
+      "title": "Spot fix: parse bold external-review verdict headings"
     },
     {
       "closed": "2026-05-19",
@@ -101,13 +83,7 @@
       ],
       "started": null,
       "status": "done",
-      "title": "Spot fix: broaden legacy tasklist importer compatibility",
-      "worktree_branch": null,
-      "worktree_in_place": false,
-      "worktree_path": null,
-      "worktree_prune_pending": false,
-      "worktree_prune_pending_at": null,
-      "worktree_pruned_at": null
+      "title": "Spot fix: broaden legacy tasklist importer compatibility"
     },
     {
       "closed": "2026-05-19",
@@ -122,13 +98,7 @@
       ],
       "started": null,
       "status": "done",
-      "title": "Add finished-agent notification hook",
-      "worktree_branch": null,
-      "worktree_in_place": false,
-      "worktree_path": null,
-      "worktree_prune_pending": false,
-      "worktree_prune_pending_at": null,
-      "worktree_pruned_at": null
+      "title": "Add finished-agent notification hook"
     },
     {
       "closed": "2026-05-19",
@@ -143,13 +113,7 @@
       ],
       "started": null,
       "status": "done",
-      "title": "Fix Codex finished-agent hook compatibility",
-      "worktree_branch": null,
-      "worktree_in_place": false,
-      "worktree_path": null,
-      "worktree_prune_pending": false,
-      "worktree_prune_pending_at": null,
-      "worktree_pruned_at": null
+      "title": "Fix Codex finished-agent hook compatibility"
     },
     {
       "closed": "2026-05-19",
@@ -165,13 +129,7 @@
       ],
       "started": null,
       "status": "done",
-      "title": "Fix Superstar Codex plugin payload version drift",
-      "worktree_branch": null,
-      "worktree_in_place": false,
-      "worktree_path": null,
-      "worktree_prune_pending": false,
-      "worktree_prune_pending_at": null,
-      "worktree_pruned_at": null
+      "title": "Fix Superstar Codex plugin payload version drift"
     },
     {
       "closed": "2026-05-19",
@@ -189,13 +147,7 @@
       ],
       "started": null,
       "status": "done",
-      "title": "Move semantic notifications from agent hooks to tasktool status changes",
-      "worktree_branch": null,
-      "worktree_in_place": false,
-      "worktree_path": null,
-      "worktree_prune_pending": false,
-      "worktree_prune_pending_at": null,
-      "worktree_pruned_at": null
+      "title": "Move semantic notifications from agent hooks to tasktool status changes"
     },
     {
       "closed": "2026-05-19",
@@ -208,13 +160,7 @@
       ],
       "started": null,
       "status": "done",
-      "title": "Coalesce bursty tasktool audio notifications",
-      "worktree_branch": null,
-      "worktree_in_place": false,
-      "worktree_path": null,
-      "worktree_prune_pending": false,
-      "worktree_prune_pending_at": null,
-      "worktree_pruned_at": null
+      "title": "Coalesce bursty tasktool audio notifications"
     },
     {
       "closed": "2026-05-20",
@@ -228,13 +174,7 @@
       ],
       "started": null,
       "status": "done",
-      "title": "Harden external-review verdict parser and prompt against Claude formatting variants",
-      "worktree_branch": null,
-      "worktree_in_place": false,
-      "worktree_path": null,
-      "worktree_prune_pending": false,
-      "worktree_prune_pending_at": null,
-      "worktree_pruned_at": null
+      "title": "Harden external-review verdict parser and prompt against Claude formatting variants"
     },
     {
       "closed": "2026-05-20",
@@ -250,13 +190,7 @@
       ],
       "started": "2026-05-20",
       "status": "done",
-      "title": "Make external-review bridge global",
-      "worktree_branch": null,
-      "worktree_in_place": false,
-      "worktree_path": null,
-      "worktree_prune_pending": false,
-      "worktree_prune_pending_at": null,
-      "worktree_pruned_at": null
+      "title": "Make external-review bridge global"
     },
     {
       "closed": "2026-05-20",
@@ -269,13 +203,7 @@
       ],
       "started": "2026-05-20",
       "status": "done",
-      "title": "tasktool: require authoritative-checkout routing for mutations",
-      "worktree_branch": null,
-      "worktree_in_place": false,
-      "worktree_path": null,
-      "worktree_prune_pending": false,
-      "worktree_prune_pending_at": null,
-      "worktree_pruned_at": null
+      "title": "tasktool: require authoritative-checkout routing for mutations"
     },
     {
       "closed": "2026-05-20",
@@ -289,13 +217,7 @@
       ],
       "started": "2026-05-20",
       "status": "done",
-      "title": "Fix tasktool close repeated refs parsing",
-      "worktree_branch": null,
-      "worktree_in_place": false,
-      "worktree_path": null,
-      "worktree_prune_pending": false,
-      "worktree_prune_pending_at": null,
-      "worktree_pruned_at": null
+      "title": "Fix tasktool close repeated refs parsing"
     },
     {
       "closed": "2026-05-20",
@@ -305,13 +227,7 @@
       "refs": [],
       "started": "2026-05-20",
       "status": "done",
-      "title": "Stabilize local Claude/Codex plugin current entrypoints",
-      "worktree_branch": null,
-      "worktree_in_place": false,
-      "worktree_path": null,
-      "worktree_prune_pending": false,
-      "worktree_prune_pending_at": null,
-      "worktree_pruned_at": null
+      "title": "Stabilize local Claude/Codex plugin current entrypoints"
     },
     {
       "closed": "2026-05-21",
@@ -328,13 +244,7 @@
       ],
       "started": "2026-05-21",
       "status": "done",
-      "title": "Make spec and plan artifact handling transactional",
-      "worktree_branch": null,
-      "worktree_in_place": false,
-      "worktree_path": null,
-      "worktree_prune_pending": false,
-      "worktree_prune_pending_at": null,
-      "worktree_pruned_at": null
+      "title": "Make spec and plan artifact handling transactional"
     }
   ],
   "last_reviewed": "2026-05-18",
@@ -367,13 +277,7 @@
           "started": null,
           "status": "ready",
           "tasks": [],
-          "title": "Tasktool worktree lifecycle core",
-          "worktree_branch": null,
-          "worktree_in_place": false,
-          "worktree_path": null,
-          "worktree_prune_pending": false,
-          "worktree_prune_pending_at": null,
-          "worktree_pruned_at": null
+          "title": "Tasktool worktree lifecycle core"
         },
         {
           "blocked_on": null,
@@ -395,13 +299,7 @@
           "started": null,
           "status": "ready",
           "tasks": [],
-          "title": "Prune + repair",
-          "worktree_branch": null,
-          "worktree_in_place": false,
-          "worktree_path": null,
-          "worktree_prune_pending": false,
-          "worktree_prune_pending_at": null,
-          "worktree_pruned_at": null
+          "title": "Prune + repair"
         },
         {
           "blocked_on": null,
@@ -424,13 +322,7 @@
           "started": null,
           "status": "ready",
           "tasks": [],
-          "title": "Skill rewrite + subagent guard + workflow updates",
-          "worktree_branch": null,
-          "worktree_in_place": false,
-          "worktree_path": null,
-          "worktree_prune_pending": false,
-          "worktree_prune_pending_at": null,
-          "worktree_pruned_at": null
+          "title": "Skill rewrite + subagent guard + workflow updates"
         }
       ],
       "spec_path": "docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md",
diff --git a/tools/tasktool/commands.py b/tools/tasktool/commands.py
index 3b92cd9..d148544 100644
--- a/tools/tasktool/commands.py
+++ b/tools/tasktool/commands.py
@@ -157,6 +157,27 @@ def _resolve_write_root(repo_root: Path) -> tuple[Path, bool, str, str]:
         cfg.tasklist.authoritative_branch,
     )
 
+@contextmanager
+def _read_context(repo_root: Path):
+    """Read-only equivalent of `_write_context`.
+
+    Resolves the authoritative checkout for read purposes without acquiring
+    `.git/tasktool.lock` or enforcing authoritative cleanliness. Use this for
+    commands that only inspect state (e.g. `worktree list`, `worktree status`).
+    """
+    write_root, _routed, mode, authoritative_branch = _resolve_write_root(repo_root)
+    if mode == "authoritative-checkout":
+        try:
+            validate_authoritative_checkout(
+                write_root,
+                expected_branch=authoritative_branch,
+                caller_root=repo_root,
+            )
+        except AuthorityError as exc:
+            raise CommandError(str(exc)) from exc
+    yield write_root
+
+
 @contextmanager
 def _write_context(repo_root: Path):
     write_root, routed, mode, authoritative_branch = _resolve_write_root(repo_root)
@@ -1805,7 +1826,7 @@ def _health_for(write_root: Path, item) -> str:
 
 
 def cmd_worktree_list(*, repo_root: Path, show_all: bool = False) -> str:
-    with _write_context(repo_root) as write_root:
+    with _read_context(repo_root) as write_root:
         p = _load(write_root)
         rows = []
         for qid, item in _iter_worktree_rows(p):
@@ -1835,7 +1856,7 @@ def cmd_worktree_list(*, repo_root: Path, show_all: bool = False) -> str:
 
 
 def cmd_worktree_status(*, repo_root: Path, id: str) -> str:
-    with _write_context(repo_root) as write_root:
+    with _read_context(repo_root) as write_root:
         p = _load(write_root)
         qid, _container, item = _find_item(p, id)
         if item.worktree_in_place:
diff --git a/tools/tasktool/serialize.py b/tools/tasktool/serialize.py
index 3c547ae..e1a3c0f 100644
--- a/tools/tasktool/serialize.py
+++ b/tools/tasktool/serialize.py
@@ -8,6 +8,29 @@ from tasktool.model import (
     Status, PlanningStatus, SCHEMA_VERSION,
 )
 
+_WORKTREE_DEFAULT_OMIT = {
+    # field -> default value to omit on
+    "worktree_path": None,
+    "worktree_branch": None,
+    "worktree_pruned_at": None,
+    "worktree_prune_pending_at": None,
+    "worktree_in_place": False,
+    "worktree_prune_pending": False,
+}
+
+
+def _strip_worktree_defaults(d: dict) -> dict:
+    """Drop worktree_* keys whose values equal their dataclass default.
+
+    Historical rows that never set worktree_* fields must NOT gain those keys
+    when re-serialised. Rows that explicitly set non-default values keep them.
+    """
+    for field, default in _WORKTREE_DEFAULT_OMIT.items():
+        if field in d and d[field] == default:
+            del d[field]
+    return d
+
+
 def to_dict(p: Project) -> dict:
     def _coerce(obj):
         if isinstance(obj, (Status, PlanningStatus)):
@@ -20,7 +43,15 @@ def to_dict(p: Project) -> dict:
         if isinstance(node, list):
             return [walk(v) for v in node]
         return _coerce(node)
-    return walk(raw)
+    out = walk(raw)
+    # Omit worktree_* fields whose values equal dataclass defaults from
+    # serialised slice and cross-cutting rows.
+    for phase in out.get("phases", []):
+        for slc in phase.get("slices", []):
+            _strip_worktree_defaults(slc)
+    for cross in out.get("cross_cutting", []):
+        _strip_worktree_defaults(cross)
+    return out
 
 def _strict_bool(value, *, scope: str, field: str, default: bool = False) -> bool:
     if value is None:
diff --git a/tools/tasktool/tests/test_serialize.py b/tools/tasktool/tests/test_serialize.py
index 1857ede..1669e04 100644
--- a/tools/tasktool/tests/test_serialize.py
+++ b/tools/tasktool/tests/test_serialize.py
@@ -137,7 +137,9 @@ def test_slice_worktree_fields_round_trip():
     s = out["phases"][0]["slices"][0]
     assert s["worktree_path"] == ".worktrees/worktree-p1-s1-s"
     assert s["worktree_branch"] == "worktree-p1-s1-s"
-    assert s["worktree_in_place"] is False
+    # Default-valued worktree_in_place (False) is omitted from serialised form
+    # so historical rows do not gain new keys on round-trip.
+    assert "worktree_in_place" not in s
 
 
 def test_slice_worktree_fields_default_null_when_absent():
@@ -160,6 +162,70 @@ def test_slice_worktree_fields_default_null_when_absent():
     assert s.worktree_prune_pending_at is None
 
 
+def test_slice_without_worktree_fields_emits_no_worktree_keys():
+    """Historical rows that never set worktree_* fields must round-trip without
+    gaining those keys. Defaults must be omitted on serialise."""
+    from tasktool.serialize import from_dict, to_dict
+    raw = {
+        "project": "demo", "schema_version": 1,
+        "phases": [{
+            "id": "P1", "title": "P", "created": "2026-05-21", "status": "ready",
+            "slices": [{"id": "S1", "title": "S", "created": "2026-05-21", "status": "ready"}],
+        }],
+        "cross_cutting": [], "archived_phases": [], "archived_cross_cutting": [],
+    }
+    p = from_dict(raw)
+    out = to_dict(p)
+    s = out["phases"][0]["slices"][0]
+    for key in (
+        "worktree_path", "worktree_branch", "worktree_in_place",
+        "worktree_pruned_at", "worktree_prune_pending", "worktree_prune_pending_at",
+    ):
+        assert key not in s, f"unexpected default key {key!r} in serialised slice"
+
+
+def test_cross_without_worktree_fields_emits_no_worktree_keys():
+    from tasktool.serialize import from_dict, to_dict
+    raw = {
+        "project": "demo", "schema_version": 1,
+        "phases": [],
+        "cross_cutting": [{
+            "id": "X9", "title": "x", "created": "2026-05-21", "status": "ready",
+        }],
+        "archived_phases": [], "archived_cross_cutting": [],
+    }
+    p = from_dict(raw)
+    out = to_dict(p)
+    c = out["cross_cutting"][0]
+    for key in (
+        "worktree_path", "worktree_branch", "worktree_in_place",
+        "worktree_pruned_at", "worktree_prune_pending", "worktree_prune_pending_at",
+    ):
+        assert key not in c
+
+
+def test_slice_non_default_worktree_fields_are_preserved():
+    from tasktool.serialize import from_dict, to_dict
+    raw = {
+        "project": "demo", "schema_version": 1,
+        "phases": [{
+            "id": "P1", "title": "P", "created": "2026-05-21", "status": "ready",
+            "slices": [{
+                "id": "S1", "title": "S", "created": "2026-05-21", "status": "ready",
+                "worktree_in_place": True,
+            }],
+        }],
+        "cross_cutting": [], "archived_phases": [], "archived_cross_cutting": [],
+    }
+    p = from_dict(raw)
+    out = to_dict(p)
+    s = out["phases"][0]["slices"][0]
+    assert s["worktree_in_place"] is True
+    # The other defaults must still be omitted.
+    assert "worktree_path" not in s
+    assert "worktree_branch" not in s
+
+
 def test_cross_worktree_fields_round_trip():
     from tasktool.serialize import from_dict, to_dict
     raw = {
diff --git a/tools/tasktool/tests/test_start_worktree.py b/tools/tasktool/tests/test_start_worktree.py
index 90b47d1..77d445a 100644
--- a/tools/tasktool/tests/test_start_worktree.py
+++ b/tools/tasktool/tests/test_start_worktree.py
@@ -51,7 +51,7 @@ def test_start_records_worktree_path_and_branch_and_creates_dir(tmp_path):
     expected_name = "worktree-p1-s1-lifecycle-core"
     assert sl["worktree_path"] == f".worktrees/{expected_name}"
     assert sl["worktree_branch"] == expected_name
-    assert sl["worktree_in_place"] is False
+    assert sl.get("worktree_in_place", False) is False
     assert (root / ".worktrees" / expected_name).is_dir()
     # Branch exists
     branches = _git(root, "branch", "--list", expected_name).stdout
@@ -163,8 +163,8 @@ def test_start_in_place_marks_slice(tmp_path):
     assert r.returncode == 0, r.stdout + r.stderr
     sl = tasklist(root)["phases"][0]["slices"][0]
     assert sl["worktree_in_place"] is True
-    assert sl["worktree_path"] is None
-    assert sl["worktree_branch"] is None
+    assert sl.get("worktree_path") is None
+    assert sl.get("worktree_branch") is None
     # No .worktrees directory created
     assert not (root / ".worktrees" / "worktree-p1-s1-lifecycle-core").exists()
 
@@ -269,7 +269,7 @@ def test_start_in_place_then_normal_start_is_refused(tmp_path):
     assert r.returncode == 0, r.stdout + r.stderr
     sl = tasklist(root)["phases"][0]["slices"][0]
     assert sl["worktree_in_place"] is True
-    assert sl["worktree_path"] is None
+    assert sl.get("worktree_path") is None
 
 
 def test_start_ad_hoc_creates_X_row_and_worktree(tmp_path):
diff --git a/tools/tasktool/tests/test_worktree_subcommands.py b/tools/tasktool/tests/test_worktree_subcommands.py
index 127fb78..1b02650 100644
--- a/tools/tasktool/tests/test_worktree_subcommands.py
+++ b/tools/tasktool/tests/test_worktree_subcommands.py
@@ -199,6 +199,39 @@ def test_worktree_check_legacy_via_cli(tmp_path, monkeypatch):
     assert ".claude/worktrees" in r2.stdout
 
 
+def test_worktree_list_and_status_are_readonly_under_dirty_authoritative(tmp_path):
+    """F3: read-only commands must not gate on authoritative cleanliness or
+    acquire the write lock. Dirty authoritative tasklist must not block them."""
+    root = tmp_path / "repo"
+    root.mkdir()
+    _git(root, "init", "-b", "main")
+    _git(root, "config", "user.email", "t@example.invalid")
+    _git(root, "config", "user.name", "T")
+    (root / "docs").mkdir()
+    assert run(root, "config", "init-authority", "--branch", "main").returncode == 0
+    assert run(root, "init", "--project", "demo").returncode == 0
+    _git(root, "add", "-A")
+    _git(root, "commit", "-m", "init")
+    assert run(root, "create", "phase", "--title", "P").returncode == 0
+    assert run(root, "create", "slice", "P1", "--title", "Slice").returncode == 0
+    _git(root, "add", "-A")
+    _git(root, "commit", "-m", "seed slice")
+    assert run(root, "start", "P1.S1").returncode == 0
+    _git(root, "add", "-A")
+    _git(root, "commit", "-m", "start")
+    # Make the authoritative docs/tasklist.json dirty: write to it directly.
+    tl = root / "docs" / "tasklist.json"
+    data = json.loads(tl.read_text())
+    data["north_star"] = "dirty edit"
+    tl.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
+    r_list = run(root, "worktree", "list")
+    assert r_list.returncode == 0, r_list.stdout + r_list.stderr
+    assert "P1.S1" in r_list.stdout
+    r_status = run(root, "worktree", "status", "P1.S1")
+    assert r_status.returncode == 0, r_status.stdout + r_status.stderr
+    assert "P1.S1" in r_status.stdout
+
+
 def test_worktree_adopt_overwrites_dead_record(tmp_path):
     root = seed_with_started_slice(tmp_path)
     # Kill the live worktree but keep the branch


### git diff HEAD (uncommitted)



### Untracked files

- docs/reviewer/p5-s1-tasktool-worktree-lifecycle-core-P5-S1-post-slice/ (omitted: binary or unreadable)


---

You are acting as an independent senior engineering reviewer.

Review stance:
- Lead with findings, ordered by severity.
- Focus on correctness, consistency, implementation risk, missing acceptance
  gates, vague handoffs, ungrounded assumptions, unverified claims, and drift
  from the codebase.
- Give exact file/line references when possible.
- If the document is sound, say that clearly and list residual risks.
- Keep the review actionable. Avoid broad rewrites unless the current structure
  creates concrete risk.

Repository root:
/home/simon/Dev/sigreer/skills/superstar/.claude/worktrees/p5-s1-tasktool-worktree-lifecycle-core

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md

Additional context files:
- docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md
- docs/tasklist.json

Review output contract:
1. Findings
   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
     stable if this review is iterated in subsequent rounds.
   - Mark severity inline: `Severity: blocking | important | minor | nit`.
2. Open questions / assumptions
3. Suggested document edits
4. Verification gaps / commands that should be run, if any

End your review with this exact line, as plain text on its own line:

    Overall verdict: <ready|ready with small edits|revise>

Do not bold, italicise, prefix with `##`, split across lines, or drop the
word "Overall". Do not write `**Verdict: ready**` or place the value on a
new line after a heading.

Read the files from disk. Do not rely only on the snippets in this prompt.


## Target Preview

### docs/plans/2026-05-21-P5-S1-tasktool-worktree-lifecycle-core.md

    1	# P5.S1 — Tasktool Worktree Lifecycle Core Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Make tasktool the lifecycle authority for per-slice git worktrees by adding canonical naming, schema fields, `start` (default / `--in-place` / `--adopt` / `--ad-hoc`), `worktree list|status|adopt`, and installer/project-setup wiring. Prune, repair, finalize, skill rewrite, and subagent guard are explicitly out of scope (P5.S2 / P5.S3).
    6	
    7	**Architecture:** Add a focused `tools/tasktool/worktree_lifecycle.py` module with three pure parts — the canonical naming function (`worktree_name`), worktree-aware filesystem inspectors (`inspect_recorded_state`, `linked_worktree_branch`, `is_inside_linked_worktree`), and idempotent-reuse decision (`classify_recorded_state`). Wire it through `commands.py` (extended `cmd_start`, new `cmd_worktree_list / status / adopt`, ad-hoc allocation reusing existing `cmd_create_cross`) and `cli.py` (new `--in-place`, `--adopt`, `--ad-hoc` flags on `start`; new `worktree` subparser group). Schema fields (`worktree_path`, `worktree_branch`, `worktree_in_place`, `worktree_pruned_at`, `worktree_prune_pending`, `worktree_prune_pending_at`) are added to `Slice` and `CrossCutting` dataclasses with `serialize.py`, `schema_gen.py`, and `validate.py` round-trip support. P5.S1 reserves the `_pruned_at` / `_prune_pending*` field names so P5.S2 can write to them without a second schema migration. Project-setup's existing row 1d gains a one-line legacy-dir warning.
    8	
    9	**Tech Stack:** Python 3.11, argparse, dataclasses, pytest, `git worktree` CLI helpers already used by `tools/tasktool/worktree.py`.
   10	
   11	**Spec:** `docs/specs/2026-05-21-P5-tasktool-worktree-lifecycle-design.md`
   12	
   13	**Tasktool row:** `P5.S1` (slice). The first execution step is `tools/tasktool/tasktool start P5.S1` from the authoritative checkout (or an existing linked worktree). Schedule already shows `P5.S1` is independently ready with no dependencies; no `tasktool deps` / `ratify` change required for this slice (the coordinator handles ratification when committing the plan).
   14	
   15	---
   16	
   17	## File Structure
   18	
   19	Files to create:
   20	- `tools/tasktool/worktree_lifecycle.py` — canonical naming, recorded-state inspection, idempotent-reuse classifier.
   21	- `tools/tasktool/tests/test_worktree_naming.py` — unit tests for `worktree_name` (table-driven, matches spec §5.1).
   22	- `tools/tasktool/tests/test_worktree_lifecycle.py` — unit tests for the classifier and inspectors (uses real `git worktree` against `tmp_path`, following `test_worktree_authority.py` style).
   23	- `tools/tasktool/tests/test_start_worktree.py` — CLI integration tests for `tasktool start` default / `--in-place` / `--adopt` / `--ad-hoc` paths.
   24	- `tools/tasktool/tests/test_worktree_subcommands.py` — CLI tests for `tasktool worktree list`, `status`, `adopt`.
   25	- `tools/tasktool/tests/test_project_setup_gitignore.py` — covers the project-setup audit row for `.worktrees/` and the legacy-dir warning (calls the same audit helper, no subprocess against an external installer).
   26	
   27	Files to modify:
   28	- `tools/tasktool/model.py` — add six optional fields to `Slice` and `CrossCutting`.
   29	- `tools/tasktool/serialize.py` — round-trip the new fields in `_slice` and `_cross`.
   30	- `tools/tasktool/schema_gen.py` — extend the `slice_` and `cross` JSON Schema blocks.
   31	- `tools/tasktool/validate.py` — strict format checks for the new fields (`worktree_in_place` is `bool|absent`; `worktree_path` and `worktree_branch` are `string|null`; null-consistency between path and `--in-place`).
   32	- `tools/tasktool/commands.py` — extend `cmd_start` with mode flags and reuse classifier; add `cmd_worktree_list`, `cmd_worktree_status`, `cmd_worktree_adopt`; add ad-hoc allocator helper that wraps `cmd_create_cross`.
   33	- `tools/tasktool/cli.py` — extend `start` parser with `--in-place`, `--adopt PATH`, `--ad-hoc SLUG`; add `worktree` subparser group with `list [--all]`, `status <id>`, `adopt <id> <path>`.
   34	- `skills/project-setup/SKILL.md` — extend row 1d audit step to also warn (not fix) on detection of legacy `.claude/worktrees/`, `.codex/worktrees/`, `~/.config/superstar/worktrees/<project>` directories.
   35	
   36	**Installer ownership (clarification per reviewer F4).** Spec §5.4 is headed "Installer / `project-setup` changes" and lists `.gitignore` + legacy-dir warnings as the two installer obligations. In this fork there is no separate shell installer that owns `.gitignore` edits: `tools/tasktool/install.sh` only installs the shim and pre-commit hook. The `project-setup` skill (row 1d) is the operator-facing surface that enforces `.gitignore` containing `.worktrees/` (via `git check-ignore -q .worktrees/`) and offers to scaffold the entry when missing. **This plan treats `project-setup` as the installer for §5.4** and adds explicit Task 11 coverage for the idempotence claim ("entry appears exactly once even if the audit runs twice"). No changes to `tools/tasktool/install.sh` are made in this slice.
   37	
   38	Files **not** modified in S1 (deferred to S2/S3):
   39	- `skills/using-git-worktrees/SKILL.md` (rewritten in S3).
   40	- `skills/tasklist-discipline/SKILL.md` (subagent paragraph in S3).
   41	- `skills/finishing-a-development-branch/SKILL.md` (prune step in S2).
   42	- Anything that introduces `worktree prune`, `worktree repair`, `--finalize`, or the subagent env-var guard.
   43	
   44	---
   45	
   46	## Task 1: Canonical naming function
   47	
   48	**Files:**
   49	- Create: `tools/tasktool/worktree_lifecycle.py`
   50	- Create: `tools/tasktool/tests/test_worktree_naming.py`
   51	
   52	- [ ] **Step 1: Write the failing tests**
   53	
   54	Create `tools/tasktool/tests/test_worktree_naming.py`:
   55	
   56	```python
   57	import pytest
   58	
   59	from tasktool.worktree_lifecycle import worktree_name
   60	
   61	
   62	@pytest.mark.parametrize(
   63	    "id_, title, expected",
   64	    [
   65	        ("P5.S1", "Tasktool worktree lifecycle core",
   66	         "worktree-p5-s1-tasktool-worktree-lifecycle-core"),
   67	        ("X42", "Hotfix: shim drift",
   68	         "worktree-x42-hotfix-shim-drift"),
   69	        ("P13.S2", "Checkout rewrite",
   70	         "worktree-p13-s2-checkout-rewrite"),
   71	        # Whitespace + underscore collapse
   72	        ("P1.S1", "  Foo   bar__baz  ",
   73	         "worktree-p1-s1-foo-bar-baz"),
   74	        # Non-ascii / punctuation stripped
   75	        ("P1.S1", "Café — déjà vu!",
   76	         "worktree-p1-s1-caf-d-j-vu"),
   77	        # Repeated dashes collapsed
   78	        ("P1.S1", "a---b",
   79	         "worktree-p1-s1-a-b"),
   80	        # Slice followup letter preserved
   81	        ("P2.S3a", "Follow up",
   82	         "worktree-p2-s3a-follow-up"),
   83	    ],
   84	)
   85	def test_worktree_name_table(id_, title, expected):
   86	    assert worktree_name(id_, title) == expected
   87	
   88	
   89	def test_worktree_name_truncates_long_title_at_dash_boundary():
   90	    long_title = "alpha bravo charlie delta echo foxtrot golf hotel india juliet"
   91	    out = worktree_name("P1.S1", long_title)
   92	    # slug portion (after "worktree-p1-s1-") must be <= 40 chars and end on a dash boundary
   93	    slug = out.removeprefix("worktree-p1-s1-")
   94	    assert len(slug) <= 40
   95	    assert not slug.endswith("-")
   96	    # truncation must not introduce a trailing partial word
   97	    assert out.startswith("worktree-p1-s1-alpha-bravo-charlie-delta-echo")
   98	
   99	
  100	def test_worktree_name_empty_title_keeps_id_segment():
  101	    # Empty/all-stripped title must still produce a stable name (no trailing dash, no collision risk)
  102	    out = worktree_name("X9", "!!!")
  103	    assert out == "worktree-x9"
  104	
  105	
  106	def test_worktree_name_rejects_malformed_id():
  107	    from tasktool.ids import IdParseError
  108	    with pytest.raises(IdParseError):
  109	        worktree_name("not-an-id", "title")
  110	```
  111	
  112	- [ ] **Step 2: Run tests, confirm they fail**
  113	
  114	Run: `cd tools && python -m pytest tasktool/tests/test_worktree_naming.py -v`
  115	Expected: FAIL — `ModuleNotFoundError: No module named 'tasktool.worktree_lifecycle'`.
  116	
  117	- [ ] **Step 3: Implement `worktree_name`**
  118	
  119	Create `tools/tasktool/worktree_lifecycle.py`:
  120	
  121	```python
  122	"""Per-slice worktree lifecycle policy (P5.S1).
  123	
  124	Pure helpers only — no git mutation, no tasklist mutation. Higher-level
  125	command code in `commands.py` wires these together.
  126	"""
  127	from __future__ import annotations
  128	
  129	import re
  130	import subprocess
  131	from dataclasses import dataclass
  132	from pathlib import Path
  133	from typing import Literal
  134	
  135	from tasktool.ids import parse_id
  136	
  137	_TITLE_TRUNCATE = 40
  138	
  139	
  140	def _slugify_id(id_value: str) -> str:
  141	    # parse_id raises IdParseError on garbage; do this first so callers get a
  142	    # clean error before we attempt to slugify.
  143	    parse_id(id_value)
  144	    s = id_value.lower().replace(".", "-")
  145	    s = re.sub(r"[^a-z0-9-]", "", s)
  146	    s = re.sub(r"-+", "-", s).strip("-")
  147	    return s
  148	
  149	
  150	def _slugify_title(title: str) -> str:

[truncated: 2111 additional lines]

<!-- superstar-prompt:end -->