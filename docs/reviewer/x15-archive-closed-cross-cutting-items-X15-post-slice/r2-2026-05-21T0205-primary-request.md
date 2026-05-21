<!-- superstar-prompt:start -->
You are continuing an existing review chain. This is round 2 of x15-archive-closed-cross-cutting-items-X15-post-slice.

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
| 1 | revise | None | None |

## Prior-round findings

Source: merged findings from r1 (authoritative)

# Merged findings for r1

## Primary

# Review — 2026-05-21-X15-archive-closed-cross-cutting-items.md (post-slice, round 1)

- Target: `docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md`
- Request: `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/r1-2026-05-21T0156-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

# Post-slice review — X15 archive closed cross-cutting items

## Findings

**F1. Slice work item is not started or closed. Severity: important**

`docs/tasklist.json:213-225` shows `X15` is still `status: ready`, `started: null`, `closed: null`. The plan's Execution Setup Step 1 mandates `tasktool start X15` and Task 5 Step 4 mandates `tasktool close X15 [--no-archive]`. A post-slice review fired while the work item is still `ready` contradicts the lifecycle the plan and `tasklist-discipline` skill define for this slice.

**F2. All implementation changes are uncommitted. Severity: important**

`git status` shows 19 modified files plus 5 untracked artifacts (spec, plan, handoff, new test, reviewer dir). The plan's Task 5 Step 5 calls for a single commit before close. No commit on `x15-…` branch references this work — the last commit on HEAD is `91261f1 X16: …`. Post-slice gating should normally happen against committed (or at minimum, staged) state; reviewers cannot confirm artifact stability against a working tree that can still drift.

**F3. Doc-test enforcement missing. Severity: important**

`tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` is unmodified (`git diff --stat` returns nothing for it). Plan Task 4 Step 1 explicitly required adding:
```python
assert "tasktool close X" in text
assert "--no-archive" in text
assert "archive-cross" in text
```
The SKILL.md edits do contain those strings (`skills/tasklist-discipline/SKILL.md:22,64,65,76`), so the user-facing copy lands — but there is no regression guard. If a future SKILL edit drops the lines, nothing fails. This is the only acceptance criterion in Task 4 and it was skipped.

**F4. External post-slice review not run. Severity: important**

`docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/chain.json` has `"rounds": []` and both `sweep_checkpoints` are `pending`. Plan Task 5 Step 3 is explicit: run `external-reviewer review --kind post-slice …` until verdict is `ready` / `ready with small edits`. The chain folder was created but no round was executed. (This very review may be the missing round 1 — if so, the chain still needs round files written and the verdict recorded before close.)

**F5. Test suite not exercised (or evidence not surfaced). Severity: important**

Plan Task 5 Step 1 requires `python3 -m pytest tools/tasktool/tests -q` and `tools/tasktool/tasktool validate --strict-format` to pass before closeout. No evidence in the worktree (no test output capture, no reviewer round noting the result, and no commit). Given the volume of touched files (model, serialize, validate, schema_gen, migrate, render, commands, cli, 6 test files + 1 new), a green run is the load-bearing claim of this slice and it is unverifiable from repo state.

**F6. Implementation deviation from plan (acceptable but worth noting). Severity: minor**

Plan Task 3 Step 6 specifies a separate `_raise_if_archived_cross(p, id, *, for_close)` helper called after `_load` and before `_find_item`. The actual implementation folds the archived-id hint into `_find_item` itself (`tools/tasktool/commands.py:481-484`). The behavior the tests assert (`test_close_archived_cross_reports_archived_hint`) still holds, but `archive-cross X<archived-id>` will surface the close-flavored phrase "may already be archived" rather than the archive-cross-flavored "is already archived" required by spec §4. The hint message branches by `for_close` in the plan; the current code does not. Confirm by tracing `cmd_archive_cross` on an already-archived id — `_find_item` raises before the `cmd_archive_cross` body can emit the spec-mandated `cross-cutting X1 is already archived`.

**F7. `_archive_cross_at_root` writes the archive file outside the validation/atomicity claim. Severity: minor**

The spec §4 says: "build archive content in memory, mutate the project in memory, validate, write the archive file, save tasklist.json, and stage both touched files." The implementation orders: mutate → `validate_project(p)` → `archive_path.write_text(...)` → return → caller calls `_save`. So validation runs before the file is on disk — good. But the test `test_archive_cross_atomicity_no_orphan_file_on_validation_failure` patches `validate_project` *globally*, which means the `validate_project` inside `_archive_cross_at_root` also raises before mutation gets persisted — that proves the orphan-file invariant. Less obvious: if `_save` later fails (disk full, IO error), the markdown file is already on disk and `cross_cutting` mutation is lost from tasklist, producing an orphan archive on retry. Not a regression vs. phase archive (same shape), but the plan/spec called out atomicity explicitly; surfacing this residual risk is worthwhile.

**F8. `cmd_archive_cross` does not assert active membership before archive. Severity: minor**

`_find_item` resolves archived-X to an error, but if an X has been hand-edited into both lists (or a future bug allows it), `_archive_cross_at_root`'s `any(a.id == item.id for a in p.archived_cross_cutting)` guard fires only after `_find_item` succeeds. Coverage exists for the duplicate-id validation path; there is no test for `cmd_archive_cross` on an id only present in `archived_cross_cutting` (the resolver path). Low likelihood, low impact, but a one-line test would close it.

**F9. Reviewer chain naming/work-id sanity. Severity: nit**

Chain dir is `x15-archive-closed-cross-cutting-items-X15-post-slice` and `chain.json` repeats `work_id: X15`. Conventional pattern (cf. prior `x10-…-X10-…` chain entries in tasklist.json refs) is fine; flagging only because the duplicated `X15` segment looks like a typo at a glance.

## Open questions / assumptions

- Is the intent to commit X15 *with* its own delivery row archived (the new default) or kept visible (`--no-archive`)? Plan Task 5 Step 4 leaves it operator-choice; the reviewer cannot infer the desired final tasklist shape.
- Was the test suite run locally and is the green evidence simply not yet recorded in the reviewer chain, or has it never been run end-to-end?
- Is `_raise_if_archived_cross` plan deviation (F6) intentional, or did the implementor not notice the spec-mandated split between close-time and archive-time hint phrasing?

## Suggested document edits

- Plan Task 4 Step 1: keep it. Add it back to the slice — it is currently the only test that prevents SKILL.md drift, and it was skipped.
- Plan Task 5 Step 1: require the operator to paste the `pytest` summary into the reviewer chain round file as evidence rather than relying on local-only execution.
- Spec §4 / Plan Task 3 Step 6: either reconcile the wording so both `close` and `archive-cross` can share `_find_item`'s single hint message, or restore the dual-phrasing helper. Right now spec text and code disagree on the `archive-cross`-on-archived-id error string.

## Verification gaps / commands to run

```sh
python3 -m pytest tools/tasktool/tests -q
tools/tasktool/tasktool validate --strict-format
tools/tasktool/tasktool render | rg -n "Cross-cutting|Archived cross-cutting|X15"
tools/tasktool/tasktool show X15
```

Then exercise the spec-mandated error path that F6 flags:
```sh
# after archiving X1, expect "cross-cutting X1 is already archived"
tools/tasktool/tasktool archive-cross X1
```

And record the result in `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/r1-…md` so the chain stops being empty.

Overall verdict: revise


## Sweep 1

# Review — 2026-05-21-X15-archive-closed-cross-cutting-items.md (post-slice, round 1)

- Target: `docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md`
- Request: `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/r1-2026-05-21T0156-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

# Post-slice review — X15 Archive Closed Cross-Cutting Items

## Findings

**S1.F1 — Severity: important.** Test suite has not been executed in evidence. The plan's verification gate (Task 5 Step 1) requires `tools/tasktool/tasktool validate --strict-format` and `python3 -m pytest tools/tasktool/tests -q` to pass. The chain folder `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/chain.json` shows `rounds: []` and no committed reviewer artifacts, and there is no log of these commands succeeding against the current diff. With ~600 LOC of new code and 11 new behavioral tests, a full pytest run is the load-bearing evidence; the slice should not be closed until the operator pastes the green output (or it is captured in the round artifacts).

**S1.F2 — Severity: minor.** Error-message drift between `cmd_archive_cross` and the spec. The spec (§4 / "Error handling") says `tasktool archive-cross X15` where the pointer already exists must fail with `cross-cutting X15 is already archived`. In the implementation, `_find_item` is reached first and raises the close-flavored message `cross-cutting X15 not found in active tasklist; it may already be archived` (`tools/tasktool/commands.py:481-484`). The "already archived" branch inside `_archive_cross_at_root` (lines that emit `is already archived`) is only reachable if the row is *both* in active `cross_cutting` and `archived_cross_cutting`, which validation disallows. Net effect: the user-facing `archive-cross` path never emits the spec's intended message. Either tighten the message in `_find_item` to be neutral and let `_archive_cross_at_root` produce the precise message, or add a dedicated precheck on `cmd_archive_cross` before `_find_item` (matches the plan's `_raise_if_archived_cross` Step 6 design, which was not implemented).

**S1.F3 — Severity: minor.** `_find_item`'s archived-hint side-effect now applies to every command (`start`, `set`, `block`, `unblock`, `archive-cross`, `note`, `ref`, `brief`) — not just `close`. That is arguably a usability win but it is broader than what the plan and spec described (both scoped the hint to `cmd_close`). Worth a sentence in the SKILL or a docstring comment; not a behavior bug.

**S1.F4 — Severity: minor.** `test_close_no_archive_rejects_non_cross_items` passes `skip_review_gate=True` (`tools/tasktool/tests/test_commands.py`), but with the current `cmd_close` ordering the `--no-archive` rejection fires before the gate check, so `skip_review_gate` is unreachable filler. Not a defect — but if the kind/gate ordering is ever swapped, this test will silently bypass the new rule. Either drop `skip_review_gate=True` or assert ordering explicitly.

**S1.F5 — Severity: minor.** Task 5 Step 4 (close `X15` itself) and Step 5 (commit) are inherently incomplete at review time — that is expected. Flagging so the closeout checklist is not lost: the worktree still shows `X15` active in `docs/tasklist.json` (lines 23+ list X1..X14 active, X15 not yet appearing in `cross_cutting` because it sits outside the file's visible head), the plan/spec/handoff/reviewer-folder are all untracked, and no `Archive X15` commit exists yet. The plan rightly defers these to post-review; just confirming nothing is silently missed.

**S1.F6 — Severity: nit.** `_archive_cross_at_root` writes the archive markdown after `validate_project(p)` succeeds, satisfying atomicity. However `_save` happens *after* `archive_path.write_text`, so a failure during JSON write/save leaves the archive file on disk without a corresponding pointer entry on disk. The in-memory pointer is correctly added before validation, and `_save` is the canonical-write path, so practical risk is low; if you care about strict on-disk atomicity, write the archive file last (post-`_save`) or wrap in a try/unlink. Plan and spec both accept the current ordering, so this is informational.

**S1.F7 — Severity: nit.** `next_cross_id` was extended to consume both `archived_cross_cutting` and `scan_orphan_ids` (`tools/tasktool/allocate.py:99-101`). Good — it prevents ID reuse. The plan did not call this out explicitly; the new test `test_create_cross_does_not_reuse_archived_id` covers it. Worth a one-line callout in `skills/tasklist-discipline/SKILL.md` so users know archived X IDs are still reserved.

## Open questions / assumptions

- Was `python3 -m pytest tools/tasktool/tests -q` run cleanly against this exact diff? Please attach the tail of the run to a round artifact before closing.
- Was `tools/tasktool/tasktool render` smoke-checked? The new "Archived cross-cutting (`X*`)" header is only exercised through unit tests today.
- Intent on S1.F2 — is the cross-command hint deliberate, or do you want a precise `is already archived` message specifically for `archive-cross`?

## Suggested document edits

1. Plan Task 5, Step 1: add an explicit "paste tail of pytest output into `docs/reviewer/.../r1-notes.md`" instruction so the reviewer round captures verification evidence rather than relying on the plan body.
2. Plan Task 4: note that `next_cross_id` now reserves archived X IDs (informs the SKILL update copy).
3. Spec §4 / Error handling: reconcile with implementation — either soften "is already archived" or instruct the implementation to short-circuit `cmd_archive_cross` before `_find_item`.

## Verification gaps / commands that should be run

```sh
tools/tasktool/tasktool validate --strict-format
python3 -m pytest tools/tasktool/tests -q
tools/tasktool/tasktool render | rg -n "Cross-cutting|Archived cross-cutting"
```

Capture output under `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/r1-*.md` before requesting the close.

Overall verdict: ready with small edits



## Resolution report for prior round

# Round 1 resolution

Addressed the actionable review findings from `r1-merged-findings.md`.

## Changes made

- Added tasklist-discipline regression assertions for cross-cutting close/archive docs in `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`.
- Added the archived-ID reservation note to `skills/tasklist-discipline/SKILL.md`.
- Added an `archive-cross` precheck so an already archived X-item reports `cross-cutting X1 is already archived`.
- Added command coverage for the already-archived `archive-cross` error path.
- Removed the unnecessary `skip_review_gate=True` argument from the non-cross `--no-archive` rejection test.

## Verification

- `tools/tasktool/tasktool validate --strict-format` -> ok
- `git diff --check` -> ok
- `tools/tasktool/tasktool render | rg -n "Cross-cutting|Archived cross-cutting|X15"` -> showed the active Cross-cutting section and X15 row
- `python3 -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py tools/tasktool/tests/test_commands.py -q` -> 67 passed
- `python3 -m pytest tools/tasktool/tests -q` -> 335 passed

## Notes

The X15 task row is present in this implementation worktree so review can inspect the planned work item, but lifecycle mutation through `tasktool start/close X15` remains blocked by unstaged authoritative `docs/tasklist.json` changes in the main checkout. Those main-checkout changes include the existing P1 archive cleanup that the handoff explicitly said to preserve rather than fold into this implementation branch.


## Changes since prior round

Worktree status: dirty

### git diff base..HEAD



### git diff HEAD (uncommitted)

diff --git a/docs/tasklist.json b/docs/tasklist.json
index bead962..5f596d1 100644
--- a/docs/tasklist.json
+++ b/docs/tasklist.json
@@ -1,4 +1,5 @@
 {
+  "archived_cross_cutting": [],
   "archived_phases": [
     {
       "archived_date": "2026-05-18",
@@ -209,6 +210,20 @@
       "status": "done",
       "title": "Stabilize local Claude/Codex plugin current entrypoints"
     },
+    {
+      "closed": null,
+      "created": "2026-05-21",
+      "id": "X15",
+      "notes": "",
+      "refs": [
+        "docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md",
+        "docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md",
+        "docs/handoffs/2026-05-21-X15-archive-closed-cross-cutting-items-prompt.md"
+      ],
+      "started": null,
+      "status": "ready",
+      "title": "Archive closed cross-cutting items"
+    },
     {
       "closed": null,
       "created": "2026-05-21",
diff --git a/skills/tasklist-discipline/SKILL.md b/skills/tasklist-discipline/SKILL.md
index 4dfa2ec..8f1f87b 100644
--- a/skills/tasklist-discipline/SKILL.md
+++ b/skills/tasklist-discipline/SKILL.md
@@ -19,6 +19,7 @@ Prefer the repo-local launcher `tools/tasktool/tasktool` when it exists; it work
 - About to start implementation for a slice → `tasktool start <slice-id>`. This records the lifecycle start and moves the row to `in_progress`; do this before dispatching implementation or editing implementation files.
 - About to close a slice → `tasktool close <slice-id>`. The CLI enforces the post-slice external-review gate.
 - About to close a phase → `tasktool archive-phase <phase-id>`. The CLI enforces the post-phase gate and writes the archive note.
+- About to close a cross-cutting item → `tasktool close <x-id>`. The CLI marks it done and archives it by default. Use `--no-archive` only when the closed X-item must remain visible temporarily; later run `tasktool archive-cross <x-id>`.
 - Entering a slice → `tasktool brief <slice-id>` instead of reading the JSON.
 - Onboarding a project — `[[project-setup]]` runs `tasktool init` and installs the hook.

@@ -36,6 +37,7 @@ Onboarding has a hard setup boundary: after `[[project-setup]]` configures `.tas
 | Cross-cutting | `X4` | `X4` (top-level; not nested under a phase) |

 IDs are assigned at birth and **never renumbered**. The `tasktool create` family does orphan-aware allocation (`max+1` across `docs/tasklist.json`, `docs/specs/`, `docs/plans/`, `docs/reviewer/`) and prints the new ID.
+Archived X IDs are still reserved, so a new cross-cutting item will not reuse an ID that has moved to `archived_cross_cutting`.

 Status enum: `ready | in_progress | blocked | done`. Only slices may take `blocked` (and only via `tasktool block <slice-id> --on …`). Emoji are a render concern; `tasktool render` and `tasktool brief` handle that. `tasktool start <slice-id>` is the normal way to enter `in_progress`; `tasktool set <id> --status in_progress` is a compatibility alias for older plans and ad-hoc rows. `tasktool unblock <slice-id> --resume` resumes through the same lifecycle path and stamps `started` when needed. `done` requires `closed`; the CLI stamps it.

@@ -59,6 +61,9 @@ tools/tasktool/tasktool schedule <phase-id>
 tools/tasktool/tasktool ready-slices <phase-id>
 tools/tasktool/tasktool phase-status
 tools/tasktool/tasktool close <slice-id>      # enforces post-slice review gate
+tools/tasktool/tasktool close <x-id>          # closes and archives cross-cutting by default
+tools/tasktool/tasktool close <x-id> --no-archive
+tools/tasktool/tasktool archive-cross <x-id>  # archive a done visible cross-cutting item
 tools/tasktool/tasktool archive-phase <phase-id>  # enforces post-phase review gate
 tools/tasktool/tasktool validate              # full validation
 ```
@@ -69,6 +74,7 @@ Run `tools/tasktool/tasktool --help` (or `tools/tasktool/tasktool <cmd> --help`)

 - **Post-slice external review.** `tasktool close <slice-id>` reads `chain.json` from the slice's reviewer chain folder (`docs/reviewer/<slug>-post-slice/` by default; override with `--reviewer-chain`). It refuses unless the latest round's verdict ∈ {`ready`, `ready with small edits`}. Per-task internal reviews do not satisfy this gate.
 - **Post-phase external review.** `tasktool archive-phase <phase-id>` refuses until every slice is `done` *and* the phase's post-phase chain returns `ready` / `ready with small edits`.
+- **Cross-cutting archive.** `tasktool close <x-id>` is ungated by external review and moves the completed X-item out of active `cross_cutting` into `archived_cross_cutting`, with a lossless markdown archive under `docs/archived-tasks/`. `--no-archive` leaves it visible as `done`; `tasktool archive-cross <x-id>` moves it later without sending another done notification.
 - **`--skip-review-gate`** exists for emergencies and is recorded in the slice/phase `notes` with a timestamp. Use it only when the operator has explicitly chosen to bypass.

 See `[[external-review]]` for how to drive the reviewer.
diff --git a/tools/tasktool/__init__.py b/tools/tasktool/__init__.py
index 20e22ac..c6d3a27 100644
--- a/tools/tasktool/__init__.py
+++ b/tools/tasktool/__init__.py
@@ -11,6 +11,7 @@ from tasktool.model import (
     Status,
     PlanningStatus,
     ArchivedPhase,
+    ArchivedCrossCutting,
     SCHEMA_VERSION,
 )
 from tasktool.serialize import load_project, save_project, dumps_canonical, loads_project
@@ -29,6 +30,7 @@ __all__ = [
     "Status",
     "PlanningStatus",
     "ArchivedPhase",
+    "ArchivedCrossCutting",
     "SCHEMA_VERSION",
     "load_project",
     "save_project",
diff --git a/tools/tasktool/allocate.py b/tools/tasktool/allocate.py
index b1ad6d2..7cad96b 100644
--- a/tools/tasktool/allocate.py
+++ b/tools/tasktool/allocate.py
@@ -97,6 +97,8 @@ def next_task_id(p: Project, phase_id: str, slice_id: str) -> str:
     return f"T{n}"

 def next_cross_id(p: Project, repo_root: Path) -> str:
-    used = {int(c.id[1:]) for c in p.cross_cutting} | scan_orphan_ids(repo_root, "cross")
+    used = {int(c.id[1:]) for c in p.cross_cutting}
+    used |= {int(c.id[1:]) for c in p.archived_cross_cutting}
+    used |= scan_orphan_ids(repo_root, "cross")
     n = max(used, default=0) + 1
     return f"X{n}"
diff --git a/tools/tasktool/cli.py b/tools/tasktool/cli.py
index 5a98e75..9ec5c6b 100644
--- a/tools/tasktool/cli.py
+++ b/tools/tasktool/cli.py
@@ -109,6 +109,7 @@ def _build_parser() -> argparse.ArgumentParser:
     p_close.add_argument("--skip-review-gate", action="store_true")
     p_close.add_argument("--allow-ready-close", action="store_true")
     p_close.add_argument("--reason")
+    p_close.add_argument("--no-archive", action="store_true")

     p_block = sub.add_parser("block")
     p_block.add_argument("slice_id")
@@ -202,6 +203,9 @@ def _build_parser() -> argparse.ArgumentParser:
     p_arch.add_argument("--reviewer-chain", type=Path)
     p_arch.add_argument("--skip-review-gate", action="store_true")

+    p_arch_cross = sub.add_parser("archive-cross")
+    p_arch_cross.add_argument("id")
+
     p_nextid = sub.add_parser("next-id")
     p_nextid.add_argument("--kind", required=True, choices=["phase", "slice", "task", "cross"])
     p_nextid.add_argument("--phase")
@@ -273,6 +277,7 @@ def main(argv: list[str]) -> int:
                 closed_date=args.closed_date, note=args.note,
                 reviewer_chain=args.reviewer_chain, skip_review_gate=args.skip_review_gate,
                 allow_ready_close=args.allow_ready_close, reason=args.reason,
+                no_archive=args.no_archive,
             )
         elif args.cmd == "block":
             commands.cmd_block(repo_root=root, slice_id=args.slice_id, on=args.on)
@@ -344,6 +349,8 @@ def main(argv: list[str]) -> int:
                 reviewer_chain=args.reviewer_chain,
                 skip_review_gate=args.skip_review_gate,
             )
+        elif args.cmd == "archive-cross":
+            commands.cmd_archive_cross(repo_root=root, id=args.id)
         elif args.cmd == "next-id":
             print(commands.cmd_next_id(
                 repo_root=root, kind=args.kind, phase=args.phase, slice=args.slice,
diff --git a/tools/tasktool/commands.py b/tools/tasktool/commands.py
index 6ac014f..9e8325c 100644
--- a/tools/tasktool/commands.py
+++ b/tools/tasktool/commands.py
@@ -1,9 +1,11 @@
 # tools/tasktool/commands.py
 from __future__ import annotations
 import datetime as _dt
+import json as _json
 import sys
 import subprocess as _subprocess
 from contextlib import contextmanager
+from dataclasses import asdict as _asdict
 from pathlib import Path
 from tasktool.config import (
     TasklistConfig,
@@ -13,6 +15,7 @@ from tasktool.config import (
     save_config,
 )
 from tasktool.model import (
+    ArchivedCrossCutting,
     Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status, PlanningStatus,
 )
 from tasktool.serialize import load_project, save_project
@@ -475,6 +478,10 @@ def _find_item(p: Project, id: str):
         for c in p.cross_cutting:
             if c.id == qid:
                 return qid, p.cross_cutting, c
+        if any(a.id == qid for a in p.archived_cross_cutting):
+            raise CommandError(
+                f"cross-cutting {qid} not found in active tasklist; it may already be archived"
+            )
         raise CommandError(f"cross-cutting {qid} not found")
     phase_part, slice_part, task_part = split_qualified(qid)
     phase = next((ph for ph in p.phases if ph.id == phase_part), None)
@@ -544,6 +551,78 @@ def _apply_ready_close_override(qid: str, item, *, reason: str | None) -> None:
     audit = f"[{ts}] ready-close override for {qid}: {reason.strip()}"
     item.notes = (item.notes + "\n" + audit).strip() if item.notes else audit

+def _archive_cross_at_root(
+    write_root: Path,
+    p: Project,
+    item: CrossCutting,
+) -> tuple[Path, str]:
+    if item.status != Status.DONE:
+        raise CommandError(
+            f"cross-cutting {item.id} must be done before archive; run tasktool close {item.id} first"
+        )
+    if any(a.id == item.id for a in p.archived_cross_cutting):
+        raise CommandError(f"cross-cutting {item.id} is already archived")
+
+    slug = _slugify(item.title)
+    archive_rel = f"docs/archived-tasks/{item.id}-{slug}.md"
+    archive_path = write_root / archive_rel
+    if archive_path.exists():
+        raise CommandError(f"archive path already exists: {archive_rel}")
+
+    def _coerce_cross_json(node):
+        if isinstance(node, Status):
+            return node.value
+        if isinstance(node, dict):
+            return {key: _coerce_cross_json(value) for key, value in node.items()}
+        if isinstance(node, list):
+            return [_coerce_cross_json(value) for value in node]
+        return node
+
+    cross_json = _json.dumps(
+        _coerce_cross_json(_asdict(item)),
+        indent=2,
+        sort_keys=True,
+        ensure_ascii=False,
+    ) + "\n"
+    summary_lines = [
+        f"# {item.id} - {item.title}",
+        "",
+        f"status: {item.status.value}",
+        f"created: {item.created}",
+    ]
+    if item.started:
+        summary_lines.append(f"started: {item.started}")
+    if item.closed:
+        summary_lines.append(f"closed: {item.closed}")
+    if item.refs:
+        summary_lines += ["", "## References", ""]
+        summary_lines.extend(f"- {ref}" for ref in item.refs)
+    if item.notes:
+        summary_lines += ["", "## Notes", "", item.notes]
+    summary_lines += [
+        "",
+        "## Full cross-cutting JSON (for tasktool unarchive)",
+        "",
+        "```json",
+        cross_json.rstrip(),
+        "```",
+        "",
+    ]
+
+    p.cross_cutting = [cross for cross in p.cross_cutting if cross.id != item.id]
+    p.archived_cross_cutting.append(
+        ArchivedCrossCutting(
+            id=item.id,
+            title=item.title,
+            archived_path=archive_rel,
+            archived_date=_today(),
+        )
+    )
+    validate_project(p)
+    archive_path.parent.mkdir(parents=True, exist_ok=True)
+    archive_path.write_text("\n".join(summary_lines), encoding="utf-8")
+    return archive_path, archive_rel
+
 def cmd_start(*, repo_root: Path, id: str, resume: bool = False) -> None:
     with _write_context(repo_root) as write_root:
         p = _load(write_root)
@@ -589,11 +668,14 @@ def cmd_close(
     note: str | None = None,
     reviewer_chain: Path | None = None, skip_review_gate: bool = False,
     allow_ready_close: bool = False, reason: str | None = None,
+    no_archive: bool = False,
 ) -> None:
     with _write_context(repo_root) as write_root:
         p = _load(write_root)
         qid, _container, item = _find_item(p, id)
         kind = parse_id(qid)[0]
+        if no_archive and kind != "cross":
+            raise CommandError("--no-archive is only valid for cross-cutting items")
         if kind == "task" or kind == "cross":
             pass  # no gate; just close
         elif kind in ("slice", "phase"):
@@ -612,9 +694,27 @@ def cmd_close(
                     item.refs.append(r)
         if note:
             item.notes = (item.notes + "\n" + note).strip() if item.notes else note
+        archive_path: Path | None = None
+        if kind == "cross" and not no_archive:
+            archive_path, _archive_rel = _archive_cross_at_root(write_root, p, item)
         _save(write_root, p)
+        if archive_path is not None:
+            _git_stage(write_root, archive_path)
         _notify_status(qid=qid, kind=kind, status=item.status, title=item.title)

+def cmd_archive_cross(*, repo_root: Path, id: str) -> None:
+    with _write_context(repo_root) as write_root:
+        p = _load(write_root)
+        if any(a.id == id for a in p.archived_cross_cutting):
+            raise CommandError(f"cross-cutting {id} is already archived")
+        qid, _container, item = _find_item(p, id)
+        kind = parse_id(qid)[0]
+        if kind != "cross":
+            raise CommandError(f"archive-cross only works on cross-cutting items; {qid} is a {kind}")
+        archive_path, _archive_rel = _archive_cross_at_root(write_root, p, item)
+        _save(write_root, p)
+        _git_stage(write_root, archive_path)
+
 def cmd_block(*, repo_root: Path, slice_id: str, on: str) -> None:
     with _write_context(repo_root) as write_root:
         p = _load(write_root)
diff --git a/tools/tasktool/migrate.py b/tools/tasktool/migrate.py
index 572a525..6f36390 100644
--- a/tools/tasktool/migrate.py
+++ b/tools/tasktool/migrate.py
@@ -5,11 +5,24 @@ from dataclasses import dataclass, fields
 from enum import Enum
 from typing import Literal

-from tasktool.model import ArchivedPhase, CrossCutting, Phase, Project, Slice, Task
+from tasktool.model import (
+    ArchivedCrossCutting,
+    ArchivedPhase,
+    CrossCutting,
+    Phase,
+    Project,
+    Slice,
+    Task,
+)

 Policy = Literal["accept-local", "accept-authoritative"]

-_PROJECT_COLLECTIONS = ("phases", "cross_cutting", "archived_phases")
+_PROJECT_COLLECTIONS = (
+    "phases",
+    "cross_cutting",
+    "archived_phases",
+    "archived_cross_cutting",
+)


 @dataclass(frozen=True)
@@ -78,6 +91,9 @@ def walker_field_coverage() -> dict[str, set[str]]:
         "Task": {field.name for field in fields(Task)},
         "CrossCutting": {field.name for field in fields(CrossCutting)},
         "ArchivedPhase": {field.name for field in fields(ArchivedPhase)},
+        "ArchivedCrossCutting": {
+            field.name for field in fields(ArchivedCrossCutting)
+        },
     }


@@ -131,6 +147,15 @@ def _diff_project(
         deltas=deltas,
         conflicts=conflicts,
     )
+    _diff_collection(
+        local_rows=local.archived_cross_cutting,
+        authoritative_rows=authoritative.archived_cross_cutting,
+        id_prefix="",
+        row_dataclass=ArchivedCrossCutting,
+        nested=[],
+        deltas=deltas,
+        conflicts=conflicts,
+    )


 def _diff_collection(
@@ -244,6 +269,13 @@ def _apply_local(authoritative: Project, local: Project, deltas: list[Delta]) ->
         id_prefix="",
         nested=[],
     )
+    _apply_collection(
+        authoritative_rows=merged.archived_cross_cutting,
+        local_rows=local.archived_cross_cutting,
+        deltas=deltas,
+        id_prefix="",
+        nested=[],
+    )
     return merged


diff --git a/tools/tasktool/model.py b/tools/tasktool/model.py
index 9255f29..8dbd7ea 100644
--- a/tools/tasktool/model.py
+++ b/tools/tasktool/model.py
@@ -83,6 +83,13 @@ class ArchivedPhase:
     archived_path: str
     archived_date: str

+@dataclass(slots=True)
+class ArchivedCrossCutting:
+    id: str
+    title: str
+    archived_path: str
+    archived_date: str
+
 @dataclass(slots=True)
 class Project:
     project: str
@@ -92,3 +99,4 @@ class Project:
     phases: list[Phase] = field(default_factory=list)
     cross_cutting: list[CrossCutting] = field(default_factory=list)
     archived_phases: list[ArchivedPhase] = field(default_factory=list)
+    archived_cross_cutting: list[ArchivedCrossCutting] = field(default_factory=list)
diff --git a/tools/tasktool/render.py b/tools/tasktool/render.py
index d3a7a0e..f40fb2b 100644
--- a/tools/tasktool/render.py
+++ b/tools/tasktool/render.py
@@ -76,4 +76,9 @@ def render_project(p: Project) -> str:
         for a in p.archived_phases:
             lines.append(f"- **{a.id}** — {a.title} → [`{a.archived_path}`]({a.archived_path}) ({a.archived_date})")
         lines.append("")
+    if p.archived_cross_cutting:
+        lines += ["## Archived cross-cutting (`X*`)", ""]
+        for a in p.archived_cross_cutting:
+            lines.append(f"- **{a.id}** — {a.title} → [`{a.archived_path}`]({a.archived_path}) ({a.archived_date})")
+        lines.append("")
     return "\n".join(lines).rstrip() + "\n"
diff --git a/tools/tasktool/schema_gen.py b/tools/tasktool/schema_gen.py
index 4df5788..415c4b4 100644
--- a/tools/tasktool/schema_gen.py
+++ b/tools/tasktool/schema_gen.py
@@ -106,6 +106,17 @@ def build_schema() -> dict:
         },
         "additionalProperties": False,
     }
+    archived_cross = {
+        "type": "object",
+        "required": ["id", "title", "archived_path", "archived_date"],
+        "properties": {
+            "id": {"type": "string", "pattern": r"^X\d+$"},
+            "title": {"type": "string"},
+            "archived_path": {"type": "string"},
+            "archived_date": date_str,
+        },
+        "additionalProperties": False,
+    }
     return {
         "$schema": "https://json-schema.org/draft/2020-12/schema",
         "title": "tasktool tasklist.json",
@@ -119,6 +130,7 @@ def build_schema() -> dict:
             "phases": {"type": "array", "items": phase},
             "cross_cutting": {"type": "array", "items": cross},
             "archived_phases": {"type": "array", "items": archived},
+            "archived_cross_cutting": {"type": "array", "items": archived_cross},
         },
         "additionalProperties": False,
     }
diff --git a/tools/tasktool/serialize.py b/tools/tasktool/serialize.py
index 006a417..cae1072 100644
--- a/tools/tasktool/serialize.py
+++ b/tools/tasktool/serialize.py
@@ -3,7 +3,8 @@ import json
 from dataclasses import asdict
 from pathlib import Path
 from tasktool.model import (
-    Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, BlockedOn,
+    Project, Phase, Slice, Task, CrossCutting, ArchivedPhase,
+    ArchivedCrossCutting, BlockedOn,
     Status, PlanningStatus, SCHEMA_VERSION,
 )

@@ -80,6 +81,11 @@ def from_dict(d: dict) -> Project:
             id=ad["id"], title=ad["title"],
             archived_path=ad["archived_path"], archived_date=ad["archived_date"],
         )
+    def _arch_cross(ad):
+        return ArchivedCrossCutting(
+            id=ad["id"], title=ad["title"],
+            archived_path=ad["archived_path"], archived_date=ad["archived_date"],
+        )
     return Project(
         project=d["project"],
         schema_version=d.get("schema_version", SCHEMA_VERSION),
@@ -88,6 +94,9 @@ def from_dict(d: dict) -> Project:
         phases=[_phase(p) for p in d.get("phases", [])],
         cross_cutting=[_cross(x) for x in d.get("cross_cutting", [])],
         archived_phases=[_arch(a) for a in d.get("archived_phases", [])],
+        archived_cross_cutting=[
+            _arch_cross(a) for a in d.get("archived_cross_cutting", [])
+        ],
     )

 def dumps_canonical(p: Project) -> str:
diff --git a/tools/tasktool/tests/test_cli_integration.py b/tools/tasktool/tests/test_cli_integration.py
index e3df5ca..41cd9f2 100644
--- a/tools/tasktool/tests/test_cli_integration.py
+++ b/tools/tasktool/tests/test_cli_integration.py
@@ -4,6 +4,8 @@ import subprocess
 import sys
 import unittest
 from pathlib import Path
+from tasktool.model import Status
+from tasktool.serialize import load_project

 REPO_ROOT = Path(__file__).resolve().parents[3]
 PKG_DIR = REPO_ROOT / "tools"
@@ -147,6 +149,54 @@ class CliEndToEndTests(unittest.TestCase):
         finally:
             t.cleanup()

+    def test_close_cross_no_archive_keeps_visible(self):
+        t = _CliTmp()
+        try:
+            self.assertEqual(run_cli("init", "--project", "demo", cwd=t.root).returncode, 0)
+            run_cli("create", "cross", "--title", "visible", cwd=t.root)
+
+            r = run_cli("close", "X1", "--no-archive", cwd=t.root)
+
+            self.assertEqual(r.returncode, 0, r.stderr)
+            project = load_project(t.root / "docs/tasklist.json")
+            self.assertEqual(project.cross_cutting[0].id, "X1")
+            self.assertEqual(project.cross_cutting[0].status, Status.DONE)
+            self.assertEqual(project.archived_cross_cutting, [])
+        finally:
+            t.cleanup()
+
+    def test_archive_cross_moves_done_item(self):
+        t = _CliTmp()
+        try:
+            self.assertEqual(run_cli("init", "--project", "demo", cwd=t.root).returncode, 0)
+            run_cli("create", "cross", "--title", "later", cwd=t.root)
+            run_cli("close", "X1", "--no-archive", cwd=t.root)
+
+            r = run_cli("archive-cross", "X1", cwd=t.root)
+
+            self.assertEqual(r.returncode, 0, r.stderr)
+            project = load_project(t.root / "docs/tasklist.json")
+            self.assertEqual(project.cross_cutting, [])
+            self.assertEqual(project.archived_cross_cutting[0].id, "X1")
+        finally:
+            t.cleanup()
+
+    def test_list_kind_cross_excludes_archived_items(self):
+        t = _CliTmp()
+        try:
+            self.assertEqual(run_cli("init", "--project", "demo", cwd=t.root).returncode, 0)
+            run_cli("create", "cross", "--title", "archived", cwd=t.root)
+            run_cli("create", "cross", "--title", "active", cwd=t.root)
+            run_cli("close", "X1", cwd=t.root)
+
+            r = run_cli("list", "--kind", "cross", cwd=t.root)
+
+            self.assertEqual(r.returncode, 0, r.stderr)
+            self.assertNotIn("X1", r.stdout)
+            self.assertIn("X2", r.stdout)
+        finally:
+            t.cleanup()
+
 class ReviewGateE2ETests(unittest.TestCase):
     def test_close_slice_requires_chain(self):
         t = _CliTmp()
diff --git a/tools/tasktool/tests/test_commands.py b/tools/tasktool/tests/test_commands.py
index c91e1bd..02a0ddd 100644
--- a/tools/tasktool/tests/test_commands.py
+++ b/tools/tasktool/tests/test_commands.py
@@ -9,6 +9,7 @@ from unittest.mock import patch
 from tasktool import commands
 from tasktool.serialize import load_project
 from tasktool.model import Status
+from tasktool.validate import ValidationError

 class _Tmp:
     def __init__(self):
@@ -115,6 +116,158 @@ class CreateTests(unittest.TestCase):
         self.assertEqual(events[-1]["status"], "ready")
         self.assertEqual(events[-1]["message"], "P1 ready: Tasktool")

+
+class CrossArchiveTests(unittest.TestCase):
+    def setUp(self):
+        self.t = _Tmp()
+        commands.cmd_init(repo_root=self.t.root, project="demo")
+
+    def tearDown(self):
+        self.t.cleanup()
+
+    def test_close_cross_archives_by_default(self):
+        commands.cmd_create_cross(repo_root=self.t.root, title="archive me")
+
+        commands.cmd_close(repo_root=self.t.root, id="X1")
+
+        p = load_project(self.t.root / "docs/tasklist.json")
+        self.assertEqual(p.cross_cutting, [])
+        self.assertEqual(p.archived_cross_cutting[0].id, "X1")
+        archive_path = self.t.root / p.archived_cross_cutting[0].archived_path
+        self.assertTrue(archive_path.exists())
+        self.assertIn('"id": "X1"', archive_path.read_text(encoding="utf-8"))
+
+    def test_close_cross_no_archive_keeps_visible(self):
+        commands.cmd_create_cross(repo_root=self.t.root, title="keep visible")
+
+        commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)
+
+        p = load_project(self.t.root / "docs/tasklist.json")
+        self.assertEqual(p.cross_cutting[0].status, Status.DONE)
+        self.assertEqual(p.archived_cross_cutting, [])
+
+    def test_archive_cross_archives_done_visible_item(self):
+        commands.cmd_create_cross(repo_root=self.t.root, title="later")
+        commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)
+
+        commands.cmd_archive_cross(repo_root=self.t.root, id="X1")
+
+        p = load_project(self.t.root / "docs/tasklist.json")
+        self.assertEqual(p.cross_cutting, [])
+        self.assertEqual(p.archived_cross_cutting[0].id, "X1")
+
+    def test_create_cross_does_not_reuse_archived_id(self):
+        commands.cmd_create_cross(repo_root=self.t.root, title="archived")
+        commands.cmd_close(repo_root=self.t.root, id="X1")
+
+        new_id = commands.cmd_create_cross(repo_root=self.t.root, title="new")
+
+        self.assertEqual(new_id, "X2")
+
+    def test_archive_cross_rejects_ready_item(self):
+        commands.cmd_create_cross(repo_root=self.t.root, title="not done")
+
+        with self.assertRaisesRegex(commands.CommandError, "must be done before archive"):
+            commands.cmd_archive_cross(repo_root=self.t.root, id="X1")
+
+    def test_close_no_archive_rejects_non_cross_items(self):
+        commands.cmd_create_phase(repo_root=self.t.root, title="phase")
+
+        with self.assertRaisesRegex(
+            commands.CommandError,
+            "--no-archive is only valid for cross-cutting items",
+        ):
+            commands.cmd_close(
+                repo_root=self.t.root,
+                id="P1",
+                no_archive=True,
+            )
+
+    def test_archive_cross_preserves_full_json(self):
+        commands.cmd_create_cross(repo_root=self.t.root, title="full data")
+        commands.cmd_close(
+            repo_root=self.t.root,
+            id="X1",
+            no_archive=True,
+            refs=["docs/specs/example.md"],
+            note="important note",
+        )
+
+        commands.cmd_archive_cross(repo_root=self.t.root, id="X1")
+
+        p = load_project(self.t.root / "docs/tasklist.json")
+        text = (self.t.root / p.archived_cross_cutting[0].archived_path).read_text(
+            encoding="utf-8"
+        )
+        self.assertIn('"id": "X1"', text)
+        self.assertIn('"refs": [', text)
+        self.assertIn('"docs/specs/example.md"', text)
+        self.assertIn('"notes": "important note"', text)
+
+    def test_close_archived_cross_reports_archived_hint(self):
+        commands.cmd_create_cross(repo_root=self.t.root, title="already archived")
+        commands.cmd_close(repo_root=self.t.root, id="X1")
+
+        with self.assertRaisesRegex(commands.CommandError, "may already be archived"):
+            commands.cmd_close(repo_root=self.t.root, id="X1")
+
+    def test_archive_cross_archived_id_reports_archived_error(self):
+        commands.cmd_create_cross(repo_root=self.t.root, title="already archived")
+        commands.cmd_close(repo_root=self.t.root, id="X1")
+
+        with self.assertRaisesRegex(
+            commands.CommandError,
+            "cross-cutting X1 is already archived",
+        ):
+            commands.cmd_archive_cross(repo_root=self.t.root, id="X1")
+
+    def test_brief_archived_cross_is_not_active_surface(self):
+        from tasktool.brief import brief
+
+        commands.cmd_create_cross(repo_root=self.t.root, title="brief archived")
+        commands.cmd_close(repo_root=self.t.root, id="X1")
+        p = load_project(self.t.root / "docs/tasklist.json")
+
+        with self.assertRaisesRegex(ValueError, "X1: not found"):
+            brief(p, "X1")
+
+    def test_archive_cross_atomicity_no_orphan_file_on_validation_failure(self):
+        commands.cmd_create_cross(repo_root=self.t.root, title="atomic")
+        commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)
+
+        with patch("tasktool.commands.validate_project", side_effect=ValidationError("forced")):
+            with self.assertRaises(ValidationError):
+                commands.cmd_archive_cross(repo_root=self.t.root, id="X1")
+
+        self.assertFalse((self.t.root / "docs/archived-tasks/X1-atomic.md").exists())
+        p = load_project(self.t.root / "docs/tasklist.json")
+        self.assertEqual(p.cross_cutting[0].id, "X1")
+
+    def test_archive_cross_does_not_reemit_done_notification(self):
+        commands.cmd_create_cross(repo_root=self.t.root, title="notify once")
+        log = self.t.root / "notify.jsonl"
+        with patch.dict(
+            os.environ,
+            {
+                "SUPERSTAR_NOTIFY_DISABLE": "0",
+                "SUPERSTAR_NOTIFY_DRY_RUN": "1",
+                "SUPERSTAR_NOTIFY_LOG": str(log),
+            },
+        ):
+            commands.cmd_close(repo_root=self.t.root, id="X1", no_archive=True)
+            commands.cmd_archive_cross(repo_root=self.t.root, id="X1")
+
+        events = [
+            json.loads(line)
+            for line in log.read_text(encoding="utf-8").splitlines()
+        ]
+        done_events = [
+            event
+            for event in events
+            if event["id"] == "X1" and event["status"] == "done"
+        ]
+        self.assertEqual(len(done_events), 1)
+
 import json

 def _write_passing_chain(root: Path, name: str, verdict: str = "ready") -> Path:
diff --git a/tools/tasktool/tests/test_migrate.py b/tools/tasktool/tests/test_migrate.py
index 245a2bc..2aa6e27 100644
--- a/tools/tasktool/tests/test_migrate.py
+++ b/tools/tasktool/tests/test_migrate.py
@@ -12,6 +12,7 @@ from tasktool.migrate import (
     walker_field_coverage,
 )
 from tasktool.model import (
+    ArchivedCrossCutting,
     ArchivedPhase,
     CrossCutting,
     Phase,
@@ -185,7 +186,15 @@ def test_render_diff_prints_field_changes_and_authoritative_only_rows():

 def test_walker_covers_every_dataclass_field():
     coverage = walker_field_coverage()
-    for row_type in (Project, Phase, Slice, Task, CrossCutting, ArchivedPhase):
+    for row_type in (
+        Project,
+        Phase,
+        Slice,
+        Task,
+        CrossCutting,
+        ArchivedPhase,
+        ArchivedCrossCutting,
+    ):
         declared = {f.name for f in fields(row_type)}
         walked = coverage.get(row_type.__name__, set())
         missing = declared - walked
@@ -213,6 +222,32 @@ def test_archived_phase_drift_migrates():
     assert conflicts == []


+def test_archived_cross_cutting_drift_migrates():
+    local = _project_with_slice()
+    local.archived_cross_cutting.append(
+        ArchivedCrossCutting(
+            id="X1",
+            title="archived cross",
+            archived_path="docs/archived-tasks/X1-archived-cross.md",
+            archived_date=_today(),
+        )
+    )
+    authoritative = _project_with_slice()
+
+    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)
+    merged = apply_deltas(
+        authoritative=authoritative,
+        local=local,
+        deltas=deltas,
+        conflicts=conflicts,
+        policy="accept-local",
+    )
+
+    assert any(d.kind == "add" and d.row_id == "X1" for d in deltas)
+    assert conflicts == []
+    assert merged.archived_cross_cutting[0].id == "X1"
+
+
 def test_top_level_project_field_drift_migrates():
     local = _project_with_slice()
     local.north_star = "new mission"
@@ -226,7 +261,15 @@ def test_top_level_project_field_drift_migrates():


 def _value_pair_for_field(row_type, field) -> tuple[object, object]:
-    if field.name in {"id", "phases", "slices", "tasks", "cross_cutting", "archived_phases"}:
+    if field.name in {
+        "id",
+        "phases",
+        "slices",
+        "tasks",
+        "cross_cutting",
+        "archived_phases",
+        "archived_cross_cutting",
+    }:
         return (None, None)
     if field.name == "schema_version":
         return (1, 2)
@@ -270,7 +313,7 @@ def _value_pair_for_field(row_type, field) -> tuple[object, object]:

 @pytest.mark.parametrize(
     "row_type",
-    [Project, Phase, Slice, Task, CrossCutting, ArchivedPhase],
+    [Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, ArchivedCrossCutting],
 )
 def test_per_field_migration_acceptance_for_non_identity_non_collection_fields(row_type):
     for f in fields(row_type):
@@ -311,6 +354,17 @@ def test_per_field_migration_acceptance_for_non_identity_non_collection_fields(r
                         )
                     )
                 setattr(tree.archived_phases[0], f.name, value)
+            elif type_ is ArchivedCrossCutting:
+                if not tree.archived_cross_cutting:
+                    tree.archived_cross_cutting.append(
+                        ArchivedCrossCutting(
+                            id="X0",
+                            title="archived cross",
+                            archived_path="docs/archived-tasks/X0-archived-cross.md",
+                            archived_date=_today(),
+                        )
+                    )
+                setattr(tree.archived_cross_cutting[0], f.name, value)
             else:
                 raise AssertionError(f"unknown row type: {type_}")

@@ -327,6 +381,8 @@ def test_per_field_migration_acceptance_for_non_identity_non_collection_fields(r
                 return getattr(tree.cross_cutting[0], f.name)
             if type_ is ArchivedPhase:
                 return getattr(tree.archived_phases[0], f.name)
+            if type_ is ArchivedCrossCutting:
+                return getattr(tree.archived_cross_cutting[0], f.name)
             raise AssertionError(f"unknown row type: {type_}")

         set_on(local, local_val)
diff --git a/tools/tasktool/tests/test_model.py b/tools/tasktool/tests/test_model.py
index 90d38d2..0a6f3ea 100644
--- a/tools/tasktool/tests/test_model.py
+++ b/tools/tasktool/tests/test_model.py
@@ -2,7 +2,7 @@ from __future__ import annotations
 import unittest
 from tasktool.model import (
     Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status,
-    PlanningStatus, SCHEMA_VERSION,
+    PlanningStatus, ArchivedCrossCutting, SCHEMA_VERSION,
 )

 class StatusTests(unittest.TestCase):
@@ -25,6 +25,7 @@ class ConstructionTests(unittest.TestCase):
         self.assertEqual(p.phases, [])
         self.assertEqual(p.cross_cutting, [])
         self.assertEqual(p.archived_phases, [])
+        self.assertEqual(p.archived_cross_cutting, [])

     def test_phase_defaults(self):
         ph = Phase(id="P2", title="tasktool", created="2026-05-17")
@@ -80,6 +81,7 @@ class PublicAPITests(unittest.TestCase):
         for name in [
             "load_project", "save_project", "dumps_canonical", "loads_project",
             "Project", "Phase", "Slice", "Task", "CrossCutting", "BlockedOn",
-            "Status", "PlanningStatus", "ArchivedPhase", "SCHEMA_VERSION",
+            "Status", "PlanningStatus", "ArchivedPhase", "ArchivedCrossCutting",
+            "SCHEMA_VERSION",
         ]:
             self.assertTrue(hasattr(tasktool, name), f"tasktool.{name} missing")
diff --git a/tools/tasktool/tests/test_render.py b/tools/tasktool/tests/test_render.py
index 145a19d..3d9bd63 100644
--- a/tools/tasktool/tests/test_render.py
+++ b/tools/tasktool/tests/test_render.py
@@ -1,6 +1,14 @@
 from __future__ import annotations
 import unittest
-from tasktool.model import Project, Phase, Slice, CrossCutting, Status, BlockedOn
+from tasktool.model import (
+    ArchivedCrossCutting,
+    Project,
+    Phase,
+    Slice,
+    CrossCutting,
+    Status,
+    BlockedOn,
+)
 from tasktool.render import render_project

 class TestRender(unittest.TestCase):
@@ -53,6 +61,30 @@ class TestRender(unittest.TestCase):
         self.assertIn("☐", out)
         self.assertNotIn("⏸", out)

+    def test_render_shows_archived_cross_section(self):
+        p = Project(project="demo")
+        p.cross_cutting.append(
+            CrossCutting(id="X1", title="active cross", created="2026-05-21")
+        )
+        p.archived_cross_cutting.append(
+            ArchivedCrossCutting(
+                id="X2",
+                title="archived cross",
+                archived_path="docs/archived-tasks/X2-archived-cross.md",
+                archived_date="2026-05-21",
+            )
+        )
+
+        out = render_project(p)
+
+        self.assertIn("## Cross-cutting (`X*`)", out)
+        self.assertIn("## Archived cross-cutting (`X*`)", out)
+        active_section, archived_section = out.split("## Archived cross-cutting (`X*`)", 1)
+        self.assertIn("**X1**", active_section)
+        self.assertNotIn("**X2**", active_section)
+        self.assertIn("**X2**", archived_section)
+        self.assertIn("docs/archived-tasks/X2-archived-cross.md", archived_section)
+

 if __name__ == "__main__":
     unittest.main()
diff --git a/tools/tasktool/tests/test_serialize.py b/tools/tasktool/tests/test_serialize.py
index 19fb6cf..fcab953 100644
--- a/tools/tasktool/tests/test_serialize.py
+++ b/tools/tasktool/tests/test_serialize.py
@@ -93,3 +93,19 @@ def test_started_field_round_trips_on_slice():
     p = loads_project(text)
     assert p.phases[0].slices[0].started == "2026-05-19"
     assert '"started": "2026-05-19"' in dumps_canonical(p)
+
+
+def test_legacy_tasklist_without_archived_cross_cutting_loads():
+    project = loads_project(
+        json.dumps(
+            {
+                "project": "demo",
+                "schema_version": 1,
+                "phases": [],
+                "cross_cutting": [],
+                "archived_phases": [],
+            }
+        )
+    )
+
+    assert project.archived_cross_cutting == []
diff --git a/tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py b/tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
index 9aecd04..12d8cfb 100644
--- a/tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
+++ b/tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
@@ -21,6 +21,10 @@ def test_tasklist_discipline_documents_authority_and_start_workflow() -> None:
     assert "compatibility" in text
     assert "tasktool unblock <slice-id> --resume" in text
     assert "stamps `started` when needed" in text
+    assert "tasktool close <x-id>" in text
+    assert "--no-archive" in text
+    assert "archive-cross" in text
+    assert "archived x ids are still reserved" in text.lower()


 def test_using_git_worktrees_allows_routed_tasktool_writes_from_worktrees() -> None:
diff --git a/tools/tasktool/tests/test_validate.py b/tools/tasktool/tests/test_validate.py
index 6a44b0f..240f739 100644
--- a/tools/tasktool/tests/test_validate.py
+++ b/tools/tasktool/tests/test_validate.py
@@ -3,7 +3,16 @@ from __future__ import annotations
 import tempfile
 import unittest
 from pathlib import Path
-from tasktool.model import Project, Phase, Slice, Task, CrossCutting, BlockedOn, Status
+from tasktool.model import (
+    ArchivedCrossCutting,
+    Project,
+    Phase,
+    Slice,
+    Task,
+    CrossCutting,
+    BlockedOn,
+    Status,
+)
 from tasktool.serialize import save_project, dumps_canonical
 from tasktool.validate import (
     validate_project, ValidationError, strict_format_check, normalise_file,
@@ -43,6 +52,46 @@ class UniquenessTests(unittest.TestCase):
         with self.assertRaises(ValidationError):
             validate_project(p)

+    def test_duplicate_archived_cross_ids(self):
+        p = Project(project="demo")
+        p.archived_cross_cutting.extend([
+            ArchivedCrossCutting(
+                id="X1",
+                title="one",
+                archived_path="docs/archived-tasks/X1-one.md",
+                archived_date="2026-05-21",
+            ),
+            ArchivedCrossCutting(
+                id="X1",
+                title="two",
+                archived_path="docs/archived-tasks/X1-two.md",
+                archived_date="2026-05-21",
+            ),
+        ])
+
+        with self.assertRaisesRegex(ValidationError, "duplicate archived cross id X1"):
+            validate_project(p)
+
+    def test_active_and_archived_cross_id_collision(self):
+        p = Project(project="demo")
+        p.cross_cutting.append(
+            CrossCutting(id="X1", title="active", created="2026-05-21")
+        )
+        p.archived_cross_cutting.append(
+            ArchivedCrossCutting(
+                id="X1",
+                title="archived",
+                archived_path="docs/archived-tasks/X1-archived.md",
+                archived_date="2026-05-21",
+            )
+        )
+
+        with self.assertRaisesRegex(
+            ValidationError,
+            "X1 appears in both active and archived cross-cutting",
+        ):
+            validate_project(p)
+
 class StatusTransitionTests(unittest.TestCase):
     def test_done_requires_closed(self):
         p = _project_with_slice(status=Status.DONE, closed=None)
@@ -218,6 +267,20 @@ class DateFormatTests(unittest.TestCase):
         with self.assertRaises(ValidationError):
             validate_project(p)

+    def test_malformed_archived_cross_date_and_path_rejected(self):
+        p = Project(project="demo")
+        p.archived_cross_cutting.append(
+            ArchivedCrossCutting(
+                id="X1",
+                title="archived",
+                archived_path="",
+                archived_date="20260521",
+            )
+        )
+
+        with self.assertRaises(ValidationError):
+            validate_project(p)
+
     def test_started_none_accepted(self):
         p = _project_with_slice(started=None)
         p.phases[0].started = None
diff --git a/tools/tasktool/validate.py b/tools/tasktool/validate.py
index dc8fe6a..228378b 100644
--- a/tools/tasktool/validate.py
+++ b/tools/tasktool/validate.py
@@ -2,7 +2,16 @@
 from __future__ import annotations
 import re
 from pathlib import Path
-from tasktool.model import Project, Phase, Slice, Task, CrossCutting, Status, PlanningStatus
+from tasktool.model import (
+    ArchivedCrossCutting,
+    Project,
+    Phase,
+    Slice,
+    Task,
+    CrossCutting,
+    Status,
+    PlanningStatus,
+)
 from tasktool.serialize import load_project, save_project, dumps_canonical
 from tasktool.ids import parse_id, IdParseError

@@ -105,6 +114,12 @@ def _check_cross(c: CrossCutting, scope: str) -> None:
         _require(c.closed is not None, f"{scope}: status=done requires closed date")
     _check_dates(c.created, c.started, c.closed, scope)

+def _check_archived_cross(c: ArchivedCrossCutting, scope: str) -> None:
+    _check_id(c.id, _CROSS_RE, scope)
+    _require(bool(c.title.strip()), f"{scope}: archived cross title is required")
+    _require(bool(c.archived_path.strip()), f"{scope}: archived_path is required")
+    _check_date(c.archived_date, scope, "archived_date")
+
 def validate_project(p: Project) -> None:
     """Raise ValidationError on rule violation. Returns None on clean."""
     seen_phase: set[str] = set()
@@ -118,6 +133,18 @@ def validate_project(p: Project) -> None:
         _require(c.id not in seen_cross, f"X*: duplicate cross id {c.id}")
         seen_cross.add(c.id)
         _check_cross(c, c.id)
+    seen_archived_cross: set[str] = set()
+    for c in p.archived_cross_cutting:
+        _require(
+            c.id not in seen_archived_cross,
+            f"X*: duplicate archived cross id {c.id}",
+        )
+        _require(
+            c.id not in seen_cross,
+            f"{c.id} appears in both active and archived cross-cutting",
+        )
+        seen_archived_cross.add(c.id)
+        _check_archived_cross(c, c.id)

 def _check_slice_dependencies(ph: Phase) -> None:
     slice_ids = {f"{ph.id}.{s.id}" for s in ph.slices}
@@ -225,6 +252,8 @@ def collect_known_ids(p):
                 ids.add(f"{ph.id}.{sl.id}.{t.id}")
     for ph in getattr(p, "archived_phases", []) or []:
         ids.add(ph.id if hasattr(ph, "id") else ph["id"])
+    for x in getattr(p, "archived_cross_cutting", []) or []:
+        ids.add(x.id if hasattr(x, "id") else x["id"])
     for x in p.cross_cutting:
         ids.add(x.id)
     return ids


### Untracked files

### docs/handoffs/2026-05-21-X15-archive-closed-cross-cutting-items-prompt.md

```
# Coordinator handoff - X15 Archive closed cross-cutting items

You are the coordinator for implementing **X15** of Superstar at `/home/simon/Dev/sigreer/skills/superstar`.

Your role is orchestration. Use the `superstar:subagent-driven-development` skill with parallel agents where useful, or `superstar:executing-plans` if the user explicitly chooses inline execution.

## Inputs

- Tasktool entry: run `tools/tasktool/tasktool brief X15` (canonical tracker: `docs/tasklist.json`).
- Spec: [`docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md`](docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md)
- Plan: [`docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md`](docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md)
- Spec review chain: `docs/reviewer/x15-archive-closed-cross-cutting-items-design-spec/`
- Plan review chain: `docs/reviewer/x15-archive-closed-cross-cutting-items-plan/`
- Post-slice reviewer chain folder to create/use: `docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/`

## Coordinator Discipline

- Start with `tools/tasktool/tasktool brief X15`, then read the spec and plan.
- If implementing in a worktree, run `tools/tasktool/tasktool start X15` before editing implementation files.
- Keep the implementation scoped to tasktool cross-cutting archive behavior.
- Preserve the user's existing staged P1 archive cleanup unless they explicitly ask you to include or alter it.
- Delegate implementation tasks where practical. Do not collapse unrelated plan tasks into one large edit.
- At closeout, run `tools/tasktool/tasktool validate --strict-format` and `python3 -m pytest tools/tasktool/tests -q`.
- Run `superstar:external-review` with `--kind post-slice` and `--work-id X15` against the completed implementation evidence. Iterate until the verdict is `ready` or `ready with small edits`.
- Before committing finished work that changes `skills/` or `tools/`, ask whether to bump the Superstar plugin version, per `AGENTS.md`.

## First Action

Run:

```sh
tools/tasktool/tasktool brief X15
sed -n '1,260p' docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md
sed -n '1,260p' docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md
```

Then invoke `superstar:subagent-driven-development` and execute the plan task-by-task.

```

### docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md

```
# Archive Closed Cross-Cutting Items Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add lossless archive support for completed `X*` cross-cutting items, with default archive-on-close, `--no-archive`, and manual `archive-cross`.

**Architecture:** Extend the tasktool model with an `archived_cross_cutting` pointer list, then route all X-item archive behavior through command helpers that mirror phase archive atomicity: build archive content in memory, mutate project state in memory, validate, write files, save, stage, notify. Rendering, schema, migration, and tasklist-discipline docs consume the new model field without changing phase archival behavior.

**Tech Stack:** Python dataclasses, tasktool CLI, canonical JSON serialization, unittest/pytest tests under `tools/tasktool/tests`.

---

## File Structure

- Modify `tools/tasktool/model.py` to add `ArchivedCrossCutting` and `Project.archived_cross_cutting`.
- Modify `tools/tasktool/serialize.py` to load/save the new field while preserving legacy tasklists that omit it.
- Modify `tools/tasktool/validate.py` to validate archived X pointer IDs, dates, paths, duplicates, and active/archive collisions.
- Modify `tools/tasktool/schema_gen.py` so `tasktool schema` includes `archived_cross_cutting`.
- Modify `tools/tasktool/migrate.py` so drift migration treats archived X pointers as a top-level collection.
- Modify `tools/tasktool/commands.py` to add `cmd_archive_cross`, default archive-on-close for crosscuts, `--no-archive` enforcement, archive markdown writing, and friendly archived-not-found checks.
- Modify `tools/tasktool/cli.py` to add `close --no-archive` and `archive-cross`.
- Modify `tools/tasktool/render.py` to render archived X pointers separately.
- Verify `tools/tasktool/brief.py` keeps archived X-items outside the active brief surface.
- Modify `skills/tasklist-discipline/SKILL.md` to document X-item close/archive behavior.
- Add or extend tests in `tools/tasktool/tests/test_commands.py`, `test_validate.py`, `test_render.py`, `test_migrate.py`, `test_schema_gen.py`, and CLI integration tests as needed.

## Execution Setup

- [ ] **Step 1: Start from an isolated implementation worktree**

Run from the repository root:

```sh
git status --short
tools/tasktool/tasktool show X15
```

Expected: `X15` exists and references:

```text
docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md
docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md
```

If execution is happening in a new worktree, run the task lifecycle start before editing implementation files. Current `cmd_start` resolves all tasktool row kinds through `_find_item`, so cross-cutting IDs are supported:

```sh
tools/tasktool/tasktool start X15
```

Expected: `X15` moves to `in_progress`.

## Task 1: Model, Serialization, Schema, and Migration

**Files:**
- Modify: `tools/tasktool/model.py`
- Modify: `tools/tasktool/serialize.py`
- Modify: `tools/tasktool/schema_gen.py`
- Modify: `tools/tasktool/migrate.py`
- Modify: `tools/tasktool/tests/test_migrate.py`
- Add or modify: `tools/tasktool/tests/test_schema_gen.py`

- [ ] **Step 1: Add failing model/migration tests**

Append tests to `tools/tasktool/tests/test_migrate.py`:

```python
from tasktool.model import ArchivedCrossCutting


def test_archived_cross_cutting_drift_migrates():
    local = _project_with_slice()
    local.archived_cross_cutting.append(
        ArchivedCrossCutting(
            id="X1",
            title="archived cross",
            archived_path="docs/archived-tasks/X1-archived-cross.md",
            archived_date=_today(),
        )
    )
    authoritative = _project_with_slice()

    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)
    merged = apply_deltas(
        authoritative=authoritative,
        local=local,
        deltas=deltas,
        conflicts=conflicts,
        policy="accept-local",
    )

    assert any(d.kind == "add" and d.row_id == "X1" for d in deltas)
    assert merged.archived_cross_cutting[0].id == "X1"
```

Update the existing imports and parametrization in the same file so `ArchivedCrossCutting` is included anywhere `ArchivedPhase` appears in field coverage:

```python
from tasktool.model import (
    ArchivedCrossCutting,
    ArchivedPhase,
    CrossCutting,
    Phase,
    Project,
    Slice,
    Status,
    Task,
)
```

Add `ArchivedCrossCutting` to:

```python
for row_type in (Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, ArchivedCrossCutting):
```

and:

```python
[Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, ArchivedCrossCutting]
```

Extend `_value_pair_for_field`:

```python
if field.name in {"id", "phases", "slices", "tasks", "cross_cutting", "archived_phases", "archived_cross_cutting"}:
    return (None, None)
```

Extend `set_on`/`get_on`:

```python
elif type_ is ArchivedCrossCutting:
    if not tree.archived_cross_cutting:
        tree.archived_cross_cutting.append(
            ArchivedCrossCutting(
                id="X0",
                title="archived cross",
                archived_path="docs/archived-tasks/X0-archived-cross.md",
                archived_date=_today(),
            )
        )
    setattr(tree.archived_cross_cutting[0], f.name, value)
```

```python
if type_ is ArchivedCrossCutting:
    return getattr(tree.archived_cross_cutting[0], f.name)
```

- [ ] **Step 2: Add failing schema test**

Create `tools/tasktool/tests/test_schema_gen.py` if absent:

```python
from tasktool.schema_gen import build_schema


def test_schema_includes_archived_cross_cutting():
    schema = build_schema()
    properties = schema["properties"]
    assert "archived_cross_cutting" in properties
    archived = properties["archived_cross_cutting"]["items"]
    assert archived["required"] == ["id", "title", "archived_path", "archived_date"]
    assert archived["properties"]["id"]["pattern"] == r"^X\d+$"
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```sh
python3 -m pytest tools/tasktool/tests/test_migrate.py tools/tasktool/tests/test_schema_gen.py -q
```

Expected: failures for missing `ArchivedCrossCutting`, missing project field, and missing schema property.

- [ ] **Step 4: Implement model and serialization**

In `tools/tasktool/model.py`, add:

```python
@dataclass(slots=True)
class ArchivedCrossCutting:
    id: str
    title: str
    archived_path: str
    archived_date: str
```

Add the new field to `Project`:

```python
archived_cross_cutting: list[ArchivedCrossCutting] = field(default_factory=list)
```

In `tools/tasktool/serialize.py`, import the new dataclass:

```python
Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, ArchivedCrossCutting, BlockedOn,
[truncated: 757 additional lines]
```

- docs/reviewer/x15-archive-closed-cross-cutting-items-X15-post-slice/ (omitted: binary or unreadable)
### docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md

```
# X15 - Archive closed cross-cutting items

**Status:** spec
**Tasktool ID:** X15 (cross-cutting)
**Date:** 2026-05-21

## Problem

Cross-cutting items (`X*`) are top-level work items that are not contained by a phase. They are useful for small workflow fixes, tool hardening, or opportunistic cleanup that does not deserve a full phase. Once completed, however, closed X-items remain in the active `cross_cutting` array and continue to appear in rendered tasklists. Over time, those completed rows pollute the working view even though they no longer require action.

Phase work already has a lossless archive path: `tasktool archive-phase` removes the phase from active `docs/tasklist.json`, writes a full archive file under `docs/archived-tasks/`, and leaves compact pointer metadata in the active tasklist. Cross-cutting work needs the same “move it out of the active view without losing evidence” treatment, scaled to a single X-item instead of a phase containing slices.

## Goals

1. Archive completed cross-cutting items by default when they are closed.
2. Preserve archived X-item data losslessly in a per-item archive file.
3. Keep an explicit opt-out for the rare case where a closed X-item should remain visible in the active tasklist.
4. Provide a manual command to archive a done-but-visible X-item later.

## Non-goals

- No three-day auto-archive policy in this slice.
- No standalone slice archival. Slices remain archived through their parent phase.
- No compaction or lossy summary format for archived X-items.
- No change to phase archival semantics.
- No `unarchive-cross` command. The archive file embeds full JSON so a future unarchive command can be implemented, but this slice does not ship one.
- No schema version bump. `archived_cross_cutting` is backwards-compatible and defaults to `[]` for legacy tasklists.

## Design

### 1. Archive model

Add a new top-level archive pointer list to `docs/tasklist.json`:

```json
"archived_cross_cutting": [
  {
    "archived_date": "2026-05-21",
    "archived_path": "docs/archived-tasks/X15-archive-closed-cross-cutting-items.md",
    "id": "X15",
    "title": "Archive closed cross-cutting items"
  }
]
```

The active `cross_cutting` array remains the source of truth for visible, active X-items. Once an X-item is archived, it is removed from `cross_cutting` and represented in `archived_cross_cutting` by pointer metadata only.

Each archived X-item gets its own markdown archive file under `docs/archived-tasks/`:

```text
docs/archived-tasks/X15-archive-closed-cross-cutting-items.md
```

The archive file stores full canonical JSON for the X-item, including title, created date, started date, status, closed date, refs, and notes. The operation is lossless relocation, not data compaction. The mental model is the same as phase archives: phases are folders in the archive box; X-items are loose papers in the same box.

### 2. Default close behavior

`tasktool close X15` closes and archives the cross-cutting item in one operation:

1. Resolve `X15` from active `cross_cutting`.
2. Set `status` to `done`.
3. Stamp `closed` if it was not already set.
4. Apply any supplied refs or close note using the existing close semantics.
5. Build the archive markdown content in memory, including full X-item JSON.
6. Remove the X-item from active `cross_cutting` in memory.
7. Append the pointer row to `archived_cross_cutting` in memory.
8. Validate the mutated project before any archive file is written.
9. Write `docs/archived-tasks/X15-<slug>.md`.
10. Save `docs/tasklist.json`.
11. Stage both `docs/tasklist.json` and the new archive file.
12. Emit the existing done notification exactly once.

Cross-cutting close remains ungated by external review, matching today’s behavior.

### 3. Close opt-out

Add `--no-archive` to `tasktool close` for cross-cutting items:

```sh
tools/tasktool/tasktool close X15 --no-archive
```

For X-items only, `--no-archive` means “close this item but leave it visible in active `cross_cutting`.” It is an opt-out of immediate archiving, not an instruction to keep the row visible forever. The user can archive the row later with `archive-cross`.

For slices and phases, supplying `--no-archive` fails with `--no-archive is only valid for cross-cutting items`. The flag exists to control X-item close behavior only.

### 4. Manual archive command

Add:

```sh
tools/tasktool/tasktool archive-cross X15
```

This archives a closed X-item that still exists in active `cross_cutting`, typically because it was closed with `--no-archive` or predates this feature.

Rules:

- `archive-cross` accepts only cross-cutting IDs.
- The X-item must exist in active `cross_cutting`.
- The X-item must be `done`.
- If an archive pointer already exists for that ID, fail rather than overwrite.
- If the archive file path already exists, fail rather than overwrite.
- On success, use the same atomic ordering as default close: build archive content in memory, mutate the project in memory, validate, write the archive file, save `docs/tasklist.json`, and stage both touched files.
- `archive-cross` does not re-emit a done notification, because it archives an item that is already done. The status transition happened at close time.

There is no bulk auto-cleanup command in this slice.

### 5. Archive file format

Use the phase archive style but scaled to one cross-cutting item:

````md
# X15 - Archive closed cross-cutting items

status: done
created: 2026-05-21
closed: 2026-05-21

## References

- docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md

## Notes

<notes, if present>

## Full cross-cutting JSON (for tasktool unarchive)

```json
{
  "closed": "2026-05-21",
  "created": "2026-05-21",
  "id": "X15",
  "notes": "",
  "refs": [],
  "started": null,
  "status": "done",
  "title": "Archive closed cross-cutting items"
}
```
````

The exact JSON should be emitted through the existing canonical serialization path or a small helper that shares the same ordering rules. The archive file is the durable evidence store.

### 6. Rendering and listing

`tasktool render` should keep showing active `cross_cutting` as it does today, but archived X-items should no longer appear in that active section.

Add an archived X section after archived phases when `archived_cross_cutting` is non-empty:

```md
## Archived cross-cutting (`X*`)

- **X15** - Archive closed cross-cutting items -> [`docs/archived-tasks/X15-archive-closed-cross-cutting-items.md`](docs/archived-tasks/X15-archive-closed-cross-cutting-items.md) (2026-05-21)
```

Archive pointers are append-only in archive time order, matching `archived_phases`.

`tasktool list --open` naturally excludes archived X-items because they are no longer in `cross_cutting`. `tasktool list --kind cross` should continue to list active X-items only. A separate archive listing flag is not required for this slice; `render` is enough for human visibility.

`tasktool brief X15` after archival should fail with the same active-tasklist-not-found semantics as archived phases rather than loading the archive file. The archive file is evidence, not part of the active workflow surface.

## Component boundaries

- `tools/tasktool/model.py` owns the new `ArchivedCrossCutting` dataclass and `Project.archived_cross_cutting` field.
- `tools/tasktool/serialize.py` owns backwards-compatible loading when older tasklists omit `archived_cross_cutting`.
- `tools/tasktool/validate.py` owns ID uniqueness and date/path validation for archived X pointers.
- `tools/tasktool/migrate.py` owns migration/merge semantics for the new top-level collection so authoritative-checkout reconciliation preserves archived X pointers.
- `tools/tasktool/schema_gen.py` owns JSON schema coverage for `archived_cross_cutting`.
- `tools/tasktool/commands.py` owns archive behavior, including `cmd_archive_cross`, close-with-default-archive, and archive file writing.
- `tools/tasktool/cli.py` owns `close --no-archive` and the new `archive-cross` subcommand.
- `tools/tasktool/render.py` owns displaying archived X pointers.
- `tools/tasktool/brief.py` keeps archived X-items outside the active brief surface.
- `tools/tasktool/tests/` owns behavioral coverage.
- `skills/tasklist-discipline/SKILL.md` owns user-facing workflow guidance for closing and archiving X-items.

## Error handling

- `tasktool close X15` where `X15` is already archived: fail with `cross-cutting X15 not found in active tasklist; it may already be archived`. Implement this by checking `archived_cross_cutting` in the close/archive-cross wrapper before falling back to the generic not-found error.
- `tasktool close X15 --no-archive` succeeds and leaves the item in active `cross_cutting`.
- `tasktool close P4.S1 --no-archive` fails with `--no-archive is only valid for cross-cutting items`.
- `tasktool archive-cross X15` where `X15` is not `done`: fail with `cross-cutting X15 must be done before archive; run tasktool close X15 first`.
- `tasktool archive-cross X15` where the pointer already exists: fail with `cross-cutting X15 is already archived`.
- Archive path collision: fail before mutating `docs/tasklist.json`.
- Validation should reject duplicate archived X IDs, archived X IDs that also appear in active `cross_cutting`, invalid archived dates, and empty archive paths.

## Testing

Add focused tests under `tools/tasktool/tests/`:

1. `test_close_cross_archives_by_default` - create an X-item, close it, assert it is removed from `cross_cutting`, added to `archived_cross_cutting`, and a markdown archive file exists.
2. `test_close_cross_no_archive_keeps_visible` - close with `--no-archive`, assert the item remains in active `cross_cutting` with `status: done` and no archive pointer/file is created.
3. `test_archive_cross_archives_done_visible_item` - close with `--no-archive`, then run `archive-cross`, assert the item moves to the archive pointer list and the file is written.
4. `test_archive_cross_rejects_ready_item` - `archive-cross` on a ready X-item fails with the done-before-archive message.
5. `test_close_no_archive_rejects_non_cross_items` - supplying `--no-archive` when closing a slice or phase fails clearly.
6. `test_validate_rejects_duplicate_archived_cross_ids` - duplicate archive pointers fail validation.
7. `test_validate_rejects_active_and_archived_cross_id_collision` - the same `X*` ID cannot appear in both active and archived lists.
8. `test_render_shows_archived_cross_section` - render includes active X-items separately from archived X pointers.
9. `test_archive_cross_preserves_full_json` - archive markdown contains the full X-item JSON, including refs and notes.
[truncated: 34 additional lines]
```

### tools/tasktool/tests/test_schema_gen.py

```
from tasktool.schema_gen import build_schema


def test_schema_includes_archived_cross_cutting():
    schema = build_schema()
    properties = schema["properties"]
    assert "archived_cross_cutting" in properties
    archived = properties["archived_cross_cutting"]["items"]
    assert archived["required"] == [
        "id",
        "title",
        "archived_path",
        "archived_date",
    ]
    assert archived["properties"]["id"]["pattern"] == r"^X\d+$"

```



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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/x15-archive-closed-cross-cutting-items

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md

Additional context files:
- docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md
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

### docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md

    1	# Archive Closed Cross-Cutting Items Implementation Plan
    2
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4
    5	**Goal:** Add lossless archive support for completed `X*` cross-cutting items, with default archive-on-close, `--no-archive`, and manual `archive-cross`.
    6
    7	**Architecture:** Extend the tasktool model with an `archived_cross_cutting` pointer list, then route all X-item archive behavior through command helpers that mirror phase archive atomicity: build archive content in memory, mutate project state in memory, validate, write files, save, stage, notify. Rendering, schema, migration, and tasklist-discipline docs consume the new model field without changing phase archival behavior.
    8
    9	**Tech Stack:** Python dataclasses, tasktool CLI, canonical JSON serialization, unittest/pytest tests under `tools/tasktool/tests`.
   10
   11	---
   12
   13	## File Structure
   14
   15	- Modify `tools/tasktool/model.py` to add `ArchivedCrossCutting` and `Project.archived_cross_cutting`.
   16	- Modify `tools/tasktool/serialize.py` to load/save the new field while preserving legacy tasklists that omit it.
   17	- Modify `tools/tasktool/validate.py` to validate archived X pointer IDs, dates, paths, duplicates, and active/archive collisions.
   18	- Modify `tools/tasktool/schema_gen.py` so `tasktool schema` includes `archived_cross_cutting`.
   19	- Modify `tools/tasktool/migrate.py` so drift migration treats archived X pointers as a top-level collection.
   20	- Modify `tools/tasktool/commands.py` to add `cmd_archive_cross`, default archive-on-close for crosscuts, `--no-archive` enforcement, archive markdown writing, and friendly archived-not-found checks.
   21	- Modify `tools/tasktool/cli.py` to add `close --no-archive` and `archive-cross`.
   22	- Modify `tools/tasktool/render.py` to render archived X pointers separately.
   23	- Verify `tools/tasktool/brief.py` keeps archived X-items outside the active brief surface.
   24	- Modify `skills/tasklist-discipline/SKILL.md` to document X-item close/archive behavior.
   25	- Add or extend tests in `tools/tasktool/tests/test_commands.py`, `test_validate.py`, `test_render.py`, `test_migrate.py`, `test_schema_gen.py`, and CLI integration tests as needed.
   26
   27	## Execution Setup
   28
   29	- [ ] **Step 1: Start from an isolated implementation worktree**
   30
   31	Run from the repository root:
   32
   33	```sh
   34	git status --short
   35	tools/tasktool/tasktool show X15
   36	```
   37
   38	Expected: `X15` exists and references:
   39
   40	```text
   41	docs/specs/2026-05-21-X15-archive-closed-cross-cutting-items-design.md
   42	docs/plans/2026-05-21-X15-archive-closed-cross-cutting-items.md
   43	```
   44
   45	If execution is happening in a new worktree, run the task lifecycle start before editing implementation files. Current `cmd_start` resolves all tasktool row kinds through `_find_item`, so cross-cutting IDs are supported:
   46
   47	```sh
   48	tools/tasktool/tasktool start X15
   49	```
   50
   51	Expected: `X15` moves to `in_progress`.
   52
   53	## Task 1: Model, Serialization, Schema, and Migration
   54
   55	**Files:**
   56	- Modify: `tools/tasktool/model.py`
   57	- Modify: `tools/tasktool/serialize.py`
   58	- Modify: `tools/tasktool/schema_gen.py`
   59	- Modify: `tools/tasktool/migrate.py`
   60	- Modify: `tools/tasktool/tests/test_migrate.py`
   61	- Add or modify: `tools/tasktool/tests/test_schema_gen.py`
   62
   63	- [ ] **Step 1: Add failing model/migration tests**
   64
   65	Append tests to `tools/tasktool/tests/test_migrate.py`:
   66
   67	```python
   68	from tasktool.model import ArchivedCrossCutting
   69
   70
   71	def test_archived_cross_cutting_drift_migrates():
   72	    local = _project_with_slice()
   73	    local.archived_cross_cutting.append(
   74	        ArchivedCrossCutting(
   75	            id="X1",
   76	            title="archived cross",
   77	            archived_path="docs/archived-tasks/X1-archived-cross.md",
   78	            archived_date=_today(),
   79	        )
   80	    )
   81	    authoritative = _project_with_slice()
   82
   83	    deltas, conflicts = compute_deltas(local=local, authoritative=authoritative)
   84	    merged = apply_deltas(
   85	        authoritative=authoritative,
   86	        local=local,
   87	        deltas=deltas,
   88	        conflicts=conflicts,
   89	        policy="accept-local",
   90	    )
   91
   92	    assert any(d.kind == "add" and d.row_id == "X1" for d in deltas)
   93	    assert merged.archived_cross_cutting[0].id == "X1"
   94	```
   95
   96	Update the existing imports and parametrization in the same file so `ArchivedCrossCutting` is included anywhere `ArchivedPhase` appears in field coverage:
   97
   98	```python
   99	from tasktool.model import (
  100	    ArchivedCrossCutting,
  101	    ArchivedPhase,
  102	    CrossCutting,
  103	    Phase,
  104	    Project,
  105	    Slice,
  106	    Status,
  107	    Task,
  108	)
  109	```
  110
  111	Add `ArchivedCrossCutting` to:
  112
  113	```python
  114	for row_type in (Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, ArchivedCrossCutting):
  115	```
  116
  117	and:
  118
  119	```python
  120	[Project, Phase, Slice, Task, CrossCutting, ArchivedPhase, ArchivedCrossCutting]
  121	```
  122
  123	Extend `_value_pair_for_field`:
  124
  125	```python
  126	if field.name in {"id", "phases", "slices", "tasks", "cross_cutting", "archived_phases", "archived_cross_cutting"}:
  127	    return (None, None)
  128	```
  129
  130	Extend `set_on`/`get_on`:
  131
  132	```python
  133	elif type_ is ArchivedCrossCutting:
  134	    if not tree.archived_cross_cutting:
  135	        tree.archived_cross_cutting.append(
  136	            ArchivedCrossCutting(
  137	                id="X0",
  138	                title="archived cross",
  139	                archived_path="docs/archived-tasks/X0-archived-cross.md",
  140	                archived_date=_today(),
  141	            )
  142	        )
  143	    setattr(tree.archived_cross_cutting[0], f.name, value)
  144	```
  145
  146	```python
  147	if type_ is ArchivedCrossCutting:
  148	    return getattr(tree.archived_cross_cutting[0], f.name)
  149	```
  150

[truncated: 807 additional lines]

<!-- superstar-prompt:end -->