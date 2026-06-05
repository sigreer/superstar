# P7.S7 — Plan ↔ tracker drift validation: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two non-fatal `tasktool validate` warnings so a slice's tracker-declared `integration_surfaces`/`reservations` cannot silently diverge from its plan document.

**Architecture:** One new pure helper `find_surface_drift_warnings(p, repo_root, *, include_plan_checks)` in `tools/tasktool/validate.py`, mirroring the existing `find_path_warnings`. It runs Check 1 (a slice in a `parallel_group` declaring no surfaces — always on) and, when `include_plan_checks` is true, Check 2 (a tracker-declared surface/reservation absent from the slice's plan file — substring presence, not table parsing). It is wired into `_cmd_validate_at_root` next to `find_path_warnings`, with Check 2 gated on `not no_path_warnings`. No model/schema/CLI change; warnings flow through the existing text/JSON `warnings` channel and never change the exit code.

**Tech Stack:** Python 3.11+, stdlib only. Tests with `unittest` under `tools/tasktool/tests/`.

**Spec:** [`docs/specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md`](../specs/2026-06-05-P7-S7-plan-tracker-drift-validation-design.md) (§4 is authoritative). Implements P7 spec §4.G.

---

## Scheduling contract

`tasktool show P7.S7` / `tasktool schedule P7` confirm:

- `depends_on = [P7.S1, P7.S6]` — both `done`. S1 added the `integration_surfaces`/`reservations`/`coordination_group` fields this plan reads; S6 established the plan-table convention this check audits.
- `parallel_group = none`, `coordination_group = none`. S7 is an independently-executable single slice.
- **Integration surfaces for S7 itself:** `validate` (it edits `validate.py` + its test). Disjoint from every other P7 slice's surfaces (`skills`, `worktree`, `commands`/`cli`), and all siblings are terminal anyway — no overlap, no coordination needed. The S7 row currently carries this only as a prose note; Task 5 declares it as a real `integration_surfaces` value (`tasktool surface add P7.S7 validate`) so the tracker is self-consistent before ratification — dogfooding the very check this slice ships.

No dependency-graph change is required. Task 5 declares S7's own write surface and then ratifies the row.

## How to run the tools

All `tasktool`/`pytest` commands run from the repo root unless noted. The test module is `tools/tasktool/tests/test_validate.py`; run focused tests with:

```bash
cd tools/tasktool && python -m pytest tests/test_validate.py -k drift -q
```

The package imports as `tasktool` (the `tools/tasktool/` dir is the package root on `sys.path` when invoked via the shim / from inside `tools/tasktool`).

## File structure

| File | Responsibility | Change |
|------|----------------|--------|
| `tools/tasktool/validate.py` | Structural validation + non-fatal warning helpers | **Modify** — add `find_surface_drift_warnings` (reuses `is_terminal`, already imported) |
| `tools/tasktool/commands.py` | `validate` command wiring (`_cmd_validate_at_root`) | **Modify** — import and call the new helper alongside `find_path_warnings` |
| `tools/tasktool/tests/test_validate.py` | Validation unit tests | **Modify** — add a `SurfaceDriftWarningTests` class; extend imports (`Reservation`, `Status`) |

The mirror copy under `plugins/superstar/tools/tasktool/` is produced by the publish/sync scripts at release time; **do not hand-edit it** in this slice.

---

## Task 1: Check 1 — no-surface-in-parallel-group nudge

Spec §4.B. Pure, no file I/O. A non-terminal slice with a `parallel_group` set but empty `integration_surfaces` warrants a nudge.

**Files:**
- Modify: `tools/tasktool/validate.py` (add `find_surface_drift_warnings`; `is_terminal` is already imported)
- Test: `tools/tasktool/tests/test_validate.py` (new `SurfaceDriftWarningTests`)

- [ ] **Step 1: Extend the test imports**

At the top of `tools/tasktool/tests/test_validate.py`, the model import currently ends with `Status,`. Add `Reservation,` to that `from tasktool.model import (...)` block (it already imports `Status`). The final block must include `Reservation` and `Status`:

```python
from tasktool.model import (
    ArchivedCrossCutting,
    Project,
    Phase,
    Slice,
    Task,
    CrossCutting,
    BlockedOn,
    Reservation,
    Status,
)
```

- [ ] **Step 2: Write the failing test for Check 1**

Append this class to `tools/tasktool/tests/test_validate.py`:

```python
class SurfaceDriftWarningTests(unittest.TestCase):
    def test_parallel_group_no_surfaces_warns(self):
        from tasktool.validate import find_surface_drift_warnings
        p = _project_with_slice(parallel_group="core")
        with tempfile.TemporaryDirectory() as td:
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=True
            )
        self.assertTrue(
            any("parallel_group" in w and "P1.S1" in w for w in warnings),
            warnings,
        )

    def test_parallel_group_with_surfaces_no_warn(self):
        from tasktool.validate import find_surface_drift_warnings
        p = _project_with_slice(
            parallel_group="core", integration_surfaces=["commands"]
        )
        with tempfile.TemporaryDirectory() as td:
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=True
            )
        self.assertEqual(
            [w for w in warnings if "parallel_group" in w], []
        )

    def test_no_parallel_group_no_surfaces_no_warn(self):
        from tasktool.validate import find_surface_drift_warnings
        p = _project_with_slice()  # no parallel_group, no surfaces
        with tempfile.TemporaryDirectory() as td:
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=True
            )
        self.assertEqual(warnings, [])

    def test_terminal_slice_in_parallel_group_no_warn(self):
        from tasktool.validate import find_surface_drift_warnings
        p = _project_with_slice(
            parallel_group="core",
            status=Status.DONE,
            closed="2026-05-18",
        )
        with tempfile.TemporaryDirectory() as td:
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=True
            )
        self.assertEqual(warnings, [])

    def test_check1_runs_even_when_plan_checks_disabled(self):
        from tasktool.validate import find_surface_drift_warnings
        p = _project_with_slice(parallel_group="core")
        with tempfile.TemporaryDirectory() as td:
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=False
            )
        self.assertTrue(
            any("parallel_group" in w for w in warnings), warnings
        )
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q`
Expected: FAIL — `ImportError: cannot import name 'find_surface_drift_warnings'`.

- [ ] **Step 4: Implement Check 1 in `find_surface_drift_warnings`**

First, extend the existing model import near the top of `tools/tasktool/validate.py`. It currently ends:

```python
from tasktool.model import (
    ArchivedCrossCutting,
    Project,
    Phase,
    Slice,
    Task,
    CrossCutting,
    Status,
    PlanningStatus,
    is_terminal,
)
```

`is_terminal` is already imported — no change needed there. Now add the new function after `find_path_warnings` (after its `return warnings`, around line 256):

```python
def find_surface_drift_warnings(
    p: Project, repo_root: Path, *, include_plan_checks: bool
) -> list[str]:
    """Non-fatal warnings that a slice's tracker-declared integration surfaces /
    reservations are not reflected in its plan (Check 2, gated by
    `include_plan_checks`), or that a slice in a parallel_group declares no surfaces
    at all (Check 1, always run). Pure and non-raising: returns [] when clean and
    swallows plan read errors to a skip. Mirrors find_path_warnings. See spec §4."""
    warnings: list[str] = []
    for ph in p.phases:
        for s in ph.slices:
            if is_terminal(s.status):
                continue
            scope = f"{ph.id}.{s.id}"
            # Check 1 — parallel_group slice with no declared surfaces.
            if s.parallel_group is not None and not s.integration_surfaces:
                warnings.append(
                    f"{scope}: in parallel_group {s.parallel_group!r} but declares "
                    f"no integration_surfaces — declare them with "
                    f"`tasktool surface add {scope} <surface>` or remove it from the "
                    f"parallel group"
                )
    return warnings
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q`
Expected: PASS (5 tests).

- [ ] **Step 6: Commit**

```bash
git add tools/tasktool/validate.py tools/tasktool/tests/test_validate.py
git commit -m "P7.S7: add no-surface-in-parallel-group validate nudge (Check 1)"
```

---

## Task 2: Check 2 — tracker-surface-absent-from-plan drift

Spec §4.C. For a non-terminal slice with a `plan_path` whose file exists and that declares ≥1 surface or reservation, warn when a declared value is not a (case-insensitive) substring of the plan text. Skips missing/unreadable plans silently; runs only when `include_plan_checks` is true.

**Files:**
- Modify: `tools/tasktool/validate.py` (`find_surface_drift_warnings` — add the Check 2 block)
- Test: `tools/tasktool/tests/test_validate.py` (`SurfaceDriftWarningTests`)

- [ ] **Step 1: Write the failing tests for Check 2**

Append these methods to `SurfaceDriftWarningTests`:

```python
    def _plan_repo(self, td, plan_text):
        """Create a repo root with a plan file and return (repo_root, plan_rel)."""
        plan_rel = "docs/plans/plan.md"
        plan_abs = Path(td) / plan_rel
        plan_abs.parent.mkdir(parents=True, exist_ok=True)
        plan_abs.write_text(plan_text, encoding="utf-8")
        return Path(td), plan_rel

    def test_surface_present_in_plan_no_warn(self):
        from tasktool.validate import find_surface_drift_warnings
        with tempfile.TemporaryDirectory() as td:
            root, plan_rel = self._plan_repo(td, "writes the commands surface")
            p = _project_with_slice(
                plan_path=plan_rel, integration_surfaces=["commands"]
            )
            warnings = find_surface_drift_warnings(
                p, root, include_plan_checks=True
            )
        self.assertEqual([w for w in warnings if "surface" in w], [])

    def test_surface_absent_from_plan_warns(self):
        from tasktool.validate import find_surface_drift_warnings
        with tempfile.TemporaryDirectory() as td:
            root, plan_rel = self._plan_repo(td, "this plan mentions nothing useful")
            p = _project_with_slice(
                plan_path=plan_rel, integration_surfaces=["commands"]
            )
            warnings = find_surface_drift_warnings(
                p, root, include_plan_checks=True
            )
        self.assertTrue(
            any("commands" in w and "does not appear in plan" in w for w in warnings),
            warnings,
        )

    def test_reservation_absent_from_plan_warns(self):
        from tasktool.validate import find_surface_drift_warnings
        with tempfile.TemporaryDirectory() as td:
            root, plan_rel = self._plan_repo(td, "no reservations here")
            p = _project_with_slice(
                plan_path=plan_rel,
                reservations=[Reservation(resource="homepage-sort", value="15")],
            )
            warnings = find_surface_drift_warnings(
                p, root, include_plan_checks=True
            )
        self.assertTrue(
            any("homepage-sort:15" in w for w in warnings), warnings
        )

    def test_surface_match_is_case_insensitive(self):
        from tasktool.validate import find_surface_drift_warnings
        with tempfile.TemporaryDirectory() as td:
            root, plan_rel = self._plan_repo(td, "uses the cms-block-registry here")
            p = _project_with_slice(
                plan_path=plan_rel,
                integration_surfaces=["CMS-Block-Registry"],
            )
            warnings = find_surface_drift_warnings(
                p, root, include_plan_checks=True
            )
        self.assertEqual([w for w in warnings if "surface" in w], [])

    def test_no_plan_path_no_check2_warning(self):
        from tasktool.validate import find_surface_drift_warnings
        p = _project_with_slice(integration_surfaces=["commands"])  # plan_path None
        with tempfile.TemporaryDirectory() as td:
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=True
            )
        self.assertEqual([w for w in warnings if "does not appear" in w], [])

    def test_missing_plan_file_no_check2_warning(self):
        from tasktool.validate import find_surface_drift_warnings
        p = _project_with_slice(
            plan_path="docs/plans/gone.md", integration_surfaces=["commands"]
        )
        with tempfile.TemporaryDirectory() as td:
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=True
            )
        self.assertEqual([w for w in warnings if "does not appear" in w], [])

    def test_non_utf8_plan_file_swallowed(self):
        from tasktool.validate import find_surface_drift_warnings
        with tempfile.TemporaryDirectory() as td:
            plan_rel = "docs/plans/plan.md"
            plan_abs = Path(td) / plan_rel
            plan_abs.parent.mkdir(parents=True, exist_ok=True)
            plan_abs.write_bytes(b"\xff\xfe invalid utf8 \x80")
            p = _project_with_slice(
                plan_path=plan_rel, integration_surfaces=["commands"]
            )
            # Must not raise; decode error becomes a skip (no Check 2 warning).
            warnings = find_surface_drift_warnings(
                p, Path(td), include_plan_checks=True
            )
        self.assertEqual([w for w in warnings if "does not appear" in w], [])

    def test_check2_suppressed_when_plan_checks_disabled(self):
        from tasktool.validate import find_surface_drift_warnings
        with tempfile.TemporaryDirectory() as td:
            root, plan_rel = self._plan_repo(td, "mentions nothing")
            p = _project_with_slice(
                plan_path=plan_rel, integration_surfaces=["commands"]
            )
            warnings = find_surface_drift_warnings(
                p, root, include_plan_checks=False
            )
        self.assertEqual([w for w in warnings if "does not appear" in w], [])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q`
Expected: FAIL — the new Check 2 tests fail because no surface/reservation plan scan exists yet (warnings list is empty where a warning is expected).

- [ ] **Step 3: Implement Check 2 inside `find_surface_drift_warnings`**

Insert the Check 2 block inside the per-slice loop in `find_surface_drift_warnings`, immediately after the Check 1 `if` block and before the loop continues:

```python
            # Check 2 — tracker-declared surfaces/reservations absent from the plan.
            if not include_plan_checks:
                continue
            if s.plan_path is None:
                continue
            if not (s.integration_surfaces or s.reservations):
                continue
            plan_file = repo_root / s.plan_path
            if not plan_file.exists():
                continue  # missing file already reported by find_path_warnings
            try:
                plan_text = plan_file.read_text(encoding="utf-8").lower()
            except (OSError, UnicodeDecodeError):
                continue  # best-effort nudge; unreadable plan is a skip, not a crash
            for surface in s.integration_surfaces:
                if surface.lower() not in plan_text:
                    warnings.append(
                        f"{scope}.surfaces: tracker declares surface {surface!r} "
                        f"but it does not appear in plan {s.plan_path} (plan may be stale)"
                    )
            for r in s.reservations:
                token = f"{r.resource}:{r.value}"
                if token.lower() not in plan_text:
                    warnings.append(
                        f"{scope}.reservations: tracker declares reservation {token!r} "
                        f"but it does not appear in plan {s.plan_path} (plan may be stale)"
                    )
```

Note: the `if not include_plan_checks: continue` guard sits *after* Check 1's append, so Check 1 still runs when `include_plan_checks=False` (Task 1's `test_check1_runs_even_when_plan_checks_disabled` proves this).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q`
Expected: PASS (all Task 1 + Task 2 tests, 13 total).

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/validate.py tools/tasktool/tests/test_validate.py
git commit -m "P7.S7: add tracker-surface-absent-from-plan drift warning (Check 2)"
```

---

## Task 3: Wire the helper into `tasktool validate`

Spec §4.D. Call `find_surface_drift_warnings` from `_cmd_validate_at_root` next to `find_path_warnings`, passing `include_plan_checks=not no_path_warnings`.

**Files:**
- Modify: `tools/tasktool/commands.py:2466` (import) and `:2481` (call site)
- Test: `tools/tasktool/tests/test_validate.py` (`SurfaceDriftWarningTests` — `cmd_validate` integration)

- [ ] **Step 1: Write the failing integration tests**

Append to `SurfaceDriftWarningTests`. These drive the real `cmd_validate` command against a temp repo containing `docs/tasklist.json` and a plan file:

```python
    def _write_project(self, root, project):
        from tasktool.serialize import save_project
        path = root / "docs" / "tasklist.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        save_project(project, path)

    def _drift_project(self, plan_rel):
        """A slice that triggers BOTH checks at once: parallel_group with NO
        surfaces (Check 1) plus a reservation absent from the plan text (Check 2).
        Using an empty integration_surfaces list is required — Check 1 only fires
        when surfaces are empty, so a fixture that declares surfaces would not
        exercise the nudge."""
        return _project_with_slice(
            plan_path=plan_rel,
            parallel_group="core",
            reservations=[Reservation(resource="homepage-sort", value="15")],
        )

    def test_cmd_validate_reports_drift_warning_rc0(self):
        import json
        from tasktool import commands
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            root_, plan_rel = self._plan_repo(td, "mentions nothing relevant")
            p = self._drift_project(plan_rel)
            self._write_project(root, p)
            rc, out = commands.cmd_validate(repo_root=root, format="json")
        payload = json.loads(out)
        self.assertEqual(rc, 0)  # drift never fails validation
        self.assertTrue(payload["ok"])
        joined = " ".join(payload["warnings"])
        self.assertIn("parallel_group", joined)   # Check 1 (no surfaces)
        self.assertIn("does not appear in plan", joined)  # Check 2 (reservation)

    def test_cmd_validate_no_path_warnings_suppresses_check2_only(self):
        import json
        from tasktool import commands
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            root_, plan_rel = self._plan_repo(td, "mentions nothing relevant")
            p = self._drift_project(plan_rel)
            self._write_project(root, p)
            rc, out = commands.cmd_validate(
                repo_root=root, format="json", no_path_warnings=True
            )
        payload = json.loads(out)
        joined = " ".join(payload["warnings"])
        self.assertIn("parallel_group", joined)        # Check 1 still runs
        self.assertNotIn("does not appear in plan", joined)  # Check 2 suppressed
```

These tests import `commands` locally, so no module-level test import change is required.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -k cmd_validate -q`
Expected: FAIL — `cmd_validate` does not yet emit drift warnings, so the `assertIn("parallel_group", ...)` assertions fail.

- [ ] **Step 3: Add the import in `commands.py`**

In `_cmd_validate_at_root`, the local import block (around line 2465) reads:

```python
    from tasktool.validate import (
        validate_project, ValidationError, strict_format_check, normalise_file,
        find_path_warnings, validate_orphan_filenames,
    )
```

Add `find_surface_drift_warnings`:

```python
    from tasktool.validate import (
        validate_project, ValidationError, strict_format_check, normalise_file,
        find_path_warnings, validate_orphan_filenames, find_surface_drift_warnings,
    )
```

- [ ] **Step 4: Add the call site in `commands.py`**

The block at lines 2480-2483 reads:

```python
    if project is not None and not errors:
        if not no_path_warnings:
            warnings.extend(find_path_warnings(project, repo_root))
        if check_orphans:
            errors.extend(validate_orphan_filenames(project, check_orphans))
```

Change it to call the drift helper (Check 1 always; Check 2 gated via the flag):

```python
    if project is not None and not errors:
        warnings.extend(
            find_surface_drift_warnings(
                project, repo_root, include_plan_checks=not no_path_warnings
            )
        )
        if not no_path_warnings:
            warnings.extend(find_path_warnings(project, repo_root))
        if check_orphans:
            errors.extend(validate_orphan_filenames(project, check_orphans))
```

- [ ] **Step 5: Run the integration tests to verify they pass**

Run: `cd tools/tasktool && python -m pytest tests/test_validate.py::SurfaceDriftWarningTests -q`
Expected: PASS (all drift tests, including the two `cmd_validate` integration tests).

- [ ] **Step 6: Run the full validate + commands suites for regressions**

Run: `cd tools/tasktool && python -m pytest tests/test_validate.py tests/test_commands.py -q`
Expected: PASS (no regressions; existing `validate` tests unaffected because clean projects produce no new warnings).

- [ ] **Step 7: Manual smoke check against the live tracker**

Run: `tasktool validate --format json`
Expected: `ok: true`, `rc 0`, and **no `surfaces`/`reservations`/`parallel_group` drift warnings**. The live tracker currently emits one unrelated, pre-existing path warning — `P7.S5.refs: path does not exist: docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice` — which originates from an uncommitted P7.S5 reviewer-chain directory; this is outside S7 scope and is NOT a surface-drift warning. The full S7 planning package (spec, plan, handoff) and S7's own `validate` surface declaration (Task 5) all exist, so there are no S7 path warnings. The live tracker's only `parallel_group` slices (P7.S2, P7.S4, `group=core-after-model`) are terminal (`done`), so Check 1 skips them, and S7's plan mentions every surface/reservation it declares, so Check 2 is silent. The acceptance bar is: **no `surfaces`/`reservations`/`parallel_group` drift warnings, and `rc 0`** (drift is never an error). If a surface-drift warning does appear, it is genuine drift — reconcile the tracker or plan before closing the slice. (Note: if Task 5's surface declaration has not yet run when you spot-check mid-implementation, S7 will not warn — it has no `parallel_group` and an empty surface list — so this remains clean throughout.)

- [ ] **Step 8: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/tests/test_validate.py
git commit -m "P7.S7: wire surface-drift warnings into tasktool validate"
```

---

## Task 4: Full test sweep + pre-commit hook check

Confirm the whole tasktool suite is green and the pre-commit hook path (which passes `--no-path-warnings`) behaves.

**Files:** none (verification only).

- [ ] **Step 1: Run the complete tasktool test suite**

Run: `cd tools/tasktool && python -m pytest -q`
Expected: PASS (entire suite green).

- [ ] **Step 2: Exercise the pre-commit-equivalent invocation**

Run: `tasktool validate --no-path-warnings --format json`
Expected: `ok: true`, `rc 0`. No `does not appear in plan` warnings (Check 2 and all path warnings are suppressed under `--no-path-warnings`). A Check 1 `parallel_group` warning would appear only for a **non-terminal** `parallel_group` slice with no surfaces — the live tracker has none (its only `parallel_group` slices are terminal), so expect a clean `ok: true` with no surface-drift warnings.

- [ ] **Step 3: Commit (only if Steps 1-2 produced fixes)**

If no changes were needed, skip. Otherwise:

```bash
git add -A
git commit -m "P7.S7: fix test/regression surfaced by full sweep"
```

---

## Task 5: Declare S7's own write surface, then ratify

The plan confirms the existing scheduling contract unchanged. Before ratifying, declare S7's own integration surface on the tracker so the row stops drifting from this plan (the S7 row currently only has a prose note "Surfaces: validate", not a real `integration_surfaces` value). Then ratify so coordinators can rely on `ready-slices`.

**Files:** `docs/tasklist.json` (via tasktool).

- [ ] **Step 1: Declare the `validate` surface on the S7 row**

Run: `tasktool surface add P7.S7 validate`
Expected: exit 0. Confirm with `tasktool show P7.S7` — `integration_surfaces` now lists `validate`. (This plan mentions `validate` throughout, so the new Check 2 raises no drift warning for S7 itself.)

- [ ] **Step 2: Ratify**

Run: `tasktool ratify P7.S7`
Expected: exit 0; `tasktool show P7.S7` now reports `planning_status: ratified`.

- [ ] **Step 3: Commit the tracker changes**

```bash
git add docs/tasklist.json
git commit -m "P7.S7: declare validate surface + ratify drift-validation slice"
```

---

## Definition of done

- `find_surface_drift_warnings` exists in `validate.py` with the binding signature and both checks (spec §4.A–§4.C).
- `tasktool validate` emits Check 1 always and Check 2 only when plan files are in scope (`not no_path_warnings`); neither changes the exit code (spec §4.D).
- All new tests in `SurfaceDriftWarningTests` pass; the full `tools/tasktool` suite is green.
- `tasktool validate` and `tasktool validate --no-path-warnings` both return `ok: true` against the live tracker, with **no S7 surface-drift warnings**. The `--no-path-warnings` invocation is fully clean (empty warnings); the plain invocation has only the unrelated pre-existing P7.S5 path warning (`P7.S5.refs: path does not exist: docs/reviewer/p7-s5-conservative-worktree-sync-P7-S5-post-slice`), which is outside S7 scope.
- No `model.py`/`serialize.py`/`migrate.py`/schema/CLI changes (spec §4.E, §6).
- The slice is ratified.

## Out of scope (per spec §3, §7)

- Strict markdown-table parsing or per-cell diffing.
- Reverse-direction drift (plan declares a surface the tracker lacks).
- `artifact status --strict` integration.
- Any skill-prose edit (S6 owns the plan-table convention).
- Editing the `plugins/superstar/tools/tasktool/` mirror by hand (release scripts handle it).
