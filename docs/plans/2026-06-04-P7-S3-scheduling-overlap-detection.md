# P7.S3 — Scheduling overlap detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `tasktool`'s scheduling reporters surface-aware: `ready-slices` and `schedule` warn when sibling slices share an integration surface with no dependency or coordination link, a new `surface check <phase>` gives a dedicated read-only audit (unguarded overlaps, coordinated surfaces, reservation contention), and `ratify --parallel-group` warns when a slice is placed in a parallel group it shares a surface with. All additions are **warning-only** — no new blocks (reservation contention is already prevented at declaration time by S2).

**Architecture:** All logic lives in `tools/tasktool/commands.py`. A small set of pure helpers (`_dep_link`, `_shared_surfaces`, `_same_coord_group`, `_pair_surface_relation`, `_surface_overlap_map`, `_reservation_contention`, `_format_surface_relations`) classify the surface relationship between two slices; the existing reporters (`cmd_ready_slices`, `cmd_schedule`) and the new `cmd_surface_check` consume them. `cmd_ratify` gains a returned warning string emitted to stderr by the dispatch. CLI wiring (a `surface check` subparser + a ratify-warning print) goes in `tools/tasktool/cli.py`. Reads are non-mutating; only `ratify` writes (unchanged), so the new reporters use the bare `_load` pattern that `cmd_schedule` already uses.

**Tech Stack:** Python 3, argparse, pytest

---

## Scheduling

- **This slice is `P7.S3`.** It `depends_on` **`P7.S1`** (the schema-v3 data model: `Slice.integration_surfaces`, `Slice.coordination_group`, `Slice.reservations`, the `Reservation` type) **and `P7.S2`** (the `surface` / `reserve` / `coordinate` declaration commands that *write* the fields this slice reads — without them there is no data to warn on). Both deps are **`done`** as of this plan; confirmed against `tasktool schedule P7`. No dependency change is proposed; `depends_on` stays `[P7.S1, P7.S2]`.
- **No `parallel_group`.** S3 is serialized after S2 (it reports using the data S2 writes) and is the only ready slice that touches the scheduling reporters. It remains independently plannable/executable.
- **Surfaces this slice writes:** `commands` (it also adds a `surface check` subparser + ratify-warning print in `cli`, but the behavioural surface is `commands`, matching the spec's §5 table). **Reservations:** none.
- **Sibling-surface note (dog-fooding):** S3 shares **no** integration surface with any *currently ready* sibling. S6 later depends on S3 and writes `skills`; no overlap. Nothing to coordinate or serialize beyond the existing deps.
- **Ratify at close:** after plan review passes, `tasktool set P7.S3 --workflow-step implement`; at slice close the coordinator runs `tasktool ratify P7.S3` (no `--parallel-group`).

### First action before any source edit

- [ ] Run, from the repo root `/home/simon/Dev/sigreer/skills/superstar`:
  ```sh
  ./tools/tasktool/tasktool start P7.S3
  ```
  This creates/records the worktree and flips `P7.S3` to `in_progress`. `cd` into the printed worktree path and do all subsequent work there. (If the project is configured local-mode and the command prints `cd <path>`, follow it.)

---

## File Structure

| File | Responsibility (in this slice) |
|------|-------------------------------|
| `tools/tasktool/commands.py` | New pure helpers: `_dep_link`, `_shared_surfaces`, `_same_coord_group`, `_pair_surface_relation`, `_surface_overlap_map`, `_reservation_contention`, `_format_surface_relations`. New command `cmd_surface_check`. Enrich `cmd_ready_slices` and `cmd_schedule` rows with `surface_overlap` / `coordinated`. `cmd_ratify` returns a warning string; new helper `_ratify_parallel_group_warning`. |
| `tools/tasktool/cli.py` | New `surface check` sub-subcommand (phase_id + `--format`); dispatch branch. `ratify` dispatch writes the returned warning to stderr. |
| `tools/tasktool/tests/test_commands.py` | Unit tests calling the command functions directly (matches the file's `_Tmp` + `load_project` style): overlap warning emitted/suppressed (dep link, coordination group), `surface check` JSON+text shape (unguarded / coordinated / reservation contention), `ratify --parallel-group` warning. |
| `tools/tasktool/tests/test_cli_integration.py` | End-to-end CLI tests via the existing `run_cli` helper: `surface check --format json` exit 0 + shape; `ratify --parallel-group` prints the warning to stderr but still exits 0. |

**Source of truth is `tools/tasktool/`.** Do NOT edit the `plugins/superstar/` copy — it is synced at release. Every path below is relative to the repo root unless noted.

---

## Conventions you will reuse (read once before starting)

These already exist in `tools/tasktool/commands.py`; the new code must follow them exactly.

- **Read-only reporters use the bare load**, exactly as `cmd_schedule`/`cmd_ready_slices` do today: `p = _load(repo_root)` → `phase = _phase_by_id(p, phase_id)` → build string → return. No `_read_context`, no `_save`. `_phase_by_id` raises `CommandError(f"phase {phase_id} not found")` for an unknown phase — reuse it; do not re-implement the lookup.
- **Mutating commands** (only `cmd_ratify` here) keep the `with _write_context(repo_root) as write_root:` → `_load` → mutate → `_save` shape. Compute the warning string **inside** the context, after the mutation, before `_save`, and return it.
- **Terminal slices** are `done` or `cancelled`: `is_terminal(s.status)` (already imported from `tasktool.model`). A terminal slice is neither an overlap subject nor a candidate — a shipped or dropped slice cannot collide at execution time.
- **Qualified ids** are `f"{phase.id}.{s.id}"` (e.g. `P1.S3`). `depends_on` entries are qualified ids.
- **Errors:** raise `CommandError("...")`. `cli.main()` already catches it, prints `tasktool: <msg>` to stderr, exit 1.
- **JSON output:** mirror the neighbours — `import json as _j` locally (or use the module-level `_json`), `_j.dumps(obj, indent=2) + "\n"`.
- **`Phase`, `Slice`, `Status`, `is_terminal`, `Reservation`, `PlanningStatus`** are already imported at the top of `commands.py` (the `from tasktool.model import (...)` block). No new imports needed.
- **Test invocation:** from repo root,
  ```sh
  python -m pytest tools/tasktool/tests/test_commands.py -q
  ```
  (`pyproject.toml` sets `addopts = "--import-mode=importlib"`; `testpaths` includes `tools/tasktool/tests`.) If an import fails, prefix `PYTHONPATH=tools`.
- **CLI integration tests:** open `tools/tasktool/tests/test_cli_integration.py` and reuse its existing `run_cli(...)` helper and project-setup fixture verbatim — do not invent a new harness. Read the top of that file once to copy the exact call signature (it returns an object/tuple carrying exit code, stdout, stderr).

---

## Design reference — the surface-relation primitive

Every warning in this slice reduces to one question about an **ordered pair** of slices `(a, b)`: *do they share a write surface that nothing has reconciled?* The single primitive `_pair_surface_relation` answers it; everything else maps over pairs.

A pair is classified as:

- **`None`** — no shared surface, **or** a shared surface that is already reconciled by a `depends_on` link in either direction (they are serialized, so parallel execution is impossible — nothing to warn about).
- **`"coordinated"`** — shared surface, no dep link, **same non-None `coordination_group`** (an intentional, declared agreement to coordinate — reported, never warned).
- **`"overlap"`** — shared surface, no dep link, **different/absent** coordination group (the unguarded case the spec wants flagged).

Precedence is **dep-link first** (serialization fully reconciles), then coordination group, then overlap. This matches spec §4.C conditions (b) "no `depends_on` link in either direction" and (c) "not in the same `coordination_group`".

---

## Task 1 — Surface-relation helpers + `cmd_schedule` enrichment

**Files:**
- Modify: `tools/tasktool/commands.py` (add helpers immediately after `_is_slice_ready_for_work`, ~line 1996; edit `cmd_schedule`, ~line 2021)
- Test: `tools/tasktool/tests/test_commands.py`

- [ ] **Step 1: Write the failing tests**

Add a new test class at the end of `tools/tasktool/tests/test_commands.py`. It builds a phase with four slices and declares surfaces/links, then asserts on `cmd_schedule` JSON.

```python
class SurfaceOverlapSchedulingTests(unittest.TestCase):
    def setUp(self):
        self.t = _Tmp()
        commands.cmd_init(repo_root=self.t.root, project="demo")
        commands.cmd_create_phase(repo_root=self.t.root, title="P1")
        # S1, S2, S3, S4 all created at top level (no deps) unless added below.
        for _ in range(4):
            commands.cmd_create_slice(repo_root=self.t.root, phase_id="P1", title="s")

    def tearDown(self):
        self.t.cleanup()

    def _row(self, rows, qid):
        return next(r for r in rows if r["id"] == qid)

    def test_schedule_warns_unguarded_surface_overlap(self):
        # S1 and S2 both write cms-block-registry, no dep, no coordination group.
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        rows = json.loads(commands.cmd_schedule(
            repo_root=self.t.root, phase_id="P1", format="json"))
        s1 = self._row(rows, "P1.S1")
        self.assertEqual(
            s1["surface_overlap"],
            [{"sibling": "P1.S2", "surfaces": ["cms-block-registry"]}],
        )
        self.assertEqual(s1["coordinated"], [])
        # Symmetric: S2 also reports S1.
        self.assertEqual(
            self._row(rows, "P1.S2")["surface_overlap"],
            [{"sibling": "P1.S1", "surfaces": ["cms-block-registry"]}],
        )

    def test_schedule_dep_link_suppresses_overlap(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        commands.cmd_deps(repo_root=self.t.root, slice_id="P1.S2", add="P1.S1")
        rows = json.loads(commands.cmd_schedule(
            repo_root=self.t.root, phase_id="P1", format="json"))
        self.assertEqual(self._row(rows, "P1.S1")["surface_overlap"], [])
        self.assertEqual(self._row(rows, "P1.S2")["surface_overlap"], [])

    def test_schedule_coordination_group_reports_coordinated_not_warned(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        commands.cmd_coordinate(repo_root=self.t.root, slice_id="P1.S1", group="cms")
        commands.cmd_coordinate(repo_root=self.t.root, slice_id="P1.S2", group="cms")
        rows = json.loads(commands.cmd_schedule(
            repo_root=self.t.root, phase_id="P1", format="json"))
        s1 = self._row(rows, "P1.S1")
        self.assertEqual(s1["surface_overlap"], [])
        self.assertEqual(
            s1["coordinated"],
            [{"sibling": "P1.S2", "surfaces": ["cms-block-registry"], "group": "cms"}],
        )

    def test_schedule_text_shows_overlap_line(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        out = commands.cmd_schedule(repo_root=self.t.root, phase_id="P1")
        self.assertIn("surface_overlap: P1.S2 (cms-block-registry)", out)

    def test_schedule_done_slice_not_a_candidate(self):
        # A done slice that shares a surface must not be reported as an overlap.
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        commands.cmd_start(repo_root=self.t.root, id="P1.S2")
        commands.cmd_close(repo_root=self.t.root, id="P1.S2", skip_review_gate=True)
        rows = json.loads(commands.cmd_schedule(
            repo_root=self.t.root, phase_id="P1", format="json"))
        self.assertEqual(self._row(rows, "P1.S1")["surface_overlap"], [])

    def test_schedule_waiting_slice_is_candidate_not_subject(self):
        # S2 waits on S4 (not done) => not ready-for-work => not a warning SUBJECT,
        # but it is still a CANDIDATE a ready sibling (S1) can collide with.
        commands.cmd_deps(repo_root=self.t.root, slice_id="P1.S2", add="P1.S4")
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        rows = json.loads(commands.cmd_schedule(
            repo_root=self.t.root, phase_id="P1", format="json"))
        # S1 (ready subject) reports the overlap with not-yet-ready S2.
        self.assertEqual(
            self._row(rows, "P1.S1")["surface_overlap"],
            [{"sibling": "P1.S2", "surfaces": ["cms-block-registry"]}],
        )
        # S2 is not ready-for-work, so it is not a subject: no relations on its row.
        self.assertEqual(self._row(rows, "P1.S2")["surface_overlap"], [])
        self.assertEqual(self._row(rows, "P1.S2")["coordinated"], [])
```

> Note: `cmd_create_slice` with no `depends_on` makes top-level slices. There is no dep link between `P1.S1` and `P1.S2` (S2 depends on S4, not S1), so the surface overlap is genuinely unguarded. `json` is already imported at the top of `test_commands.py` (used by `test_schedule_emits_cancelled_deps`).

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/tasktool/tests/test_commands.py -k SurfaceOverlapScheduling -q`
Expected: FAIL — `KeyError: 'surface_overlap'` (the key does not exist yet).

- [ ] **Step 3: Add the helpers**

In `tools/tasktool/commands.py`, immediately **after** `_is_slice_ready_for_work` (the function ending at ~line 1996, just before `def cmd_ready_slices`), insert:

```python
def _dep_link(a_qid: str, a: Slice, b_qid: str, b: Slice) -> bool:
    """True if either slice declares the other as a dependency (link in either
    direction). A dep link serializes the pair, so a shared surface is reconciled."""
    return b_qid in (a.depends_on or []) or a_qid in (b.depends_on or [])


def _shared_surfaces(a: Slice, b: Slice) -> list[str]:
    """Sorted intersection of two slices' declared integration surfaces."""
    return sorted(set(a.integration_surfaces or []) & set(b.integration_surfaces or []))


def _same_coord_group(a: Slice, b: Slice) -> bool:
    """True if both slices name the same, non-None coordination_group."""
    return a.coordination_group is not None and a.coordination_group == b.coordination_group


def _pair_surface_relation(
    a_qid: str, a: Slice, b_qid: str, b: Slice,
) -> tuple[str | None, list[str]]:
    """Classify the surface relationship between two slices (spec 4.C).

    Returns (kind, shared_surfaces):
      - (None, [])           no shared surface
      - (None, [...])        shared surface but a depends_on link serializes them
      - ("coordinated", ...) shared surface, no dep link, same coordination_group
      - ("overlap", ...)     shared surface, no dep link, different/absent group

    Precedence is dep-link first (serialization fully reconciles), then
    coordination group, then unguarded overlap.
    """
    shared = _shared_surfaces(a, b)
    if not shared:
        return None, []
    if _dep_link(a_qid, a, b_qid, b):
        return None, shared
    if _same_coord_group(a, b):
        return "coordinated", shared
    return "overlap", shared


def _surface_overlap_map(phase: Phase) -> dict:
    """Classify surface relationships for the phase's scheduling reporters (spec
    4.C: "for each ready/in-progress slice ... other non-terminal slices").

    SUBJECTS are narrowed to the slices eligible for parallel dispatch right now —
    ready-for-work or in-progress. A blocked, dependency-waiting, superseded, or
    terminal slice is never a subject (it will not be dispatched now, so a warning
    on its row is noise). CANDIDATES are every non-terminal sibling, so a ready
    subject is still warned about a not-yet-ready sibling that writes the same
    surface.

    Returns subject_qid -> {"surface_overlap": [...], "coordinated": [...]} where
    each overlap entry is {"sibling": qid, "surfaces": [...]} and each coordinated
    entry additionally carries "group".
    """
    candidates = [
        (f"{phase.id}.{s.id}", s) for s in phase.slices if not is_terminal(s.status)
    ]
    out: dict = {}
    for s in phase.slices:
        # Subject predicate: ready-for-work (deps met, not terminal/blocked/
        # superseded — see _is_slice_ready_for_work) OR actively in progress.
        if not (s.status == Status.IN_PROGRESS or _is_slice_ready_for_work(phase, s)):
            continue
        a_qid = f"{phase.id}.{s.id}"
        overlap: list = []
        coordinated: list = []
        for b_qid, b in candidates:
            if b_qid == a_qid:
                continue
            kind, shared = _pair_surface_relation(a_qid, s, b_qid, b)
            if kind == "overlap":
                overlap.append({"sibling": b_qid, "surfaces": shared})
            elif kind == "coordinated":
                coordinated.append(
                    {"sibling": b_qid, "surfaces": shared, "group": s.coordination_group}
                )
        out[a_qid] = {"surface_overlap": overlap, "coordinated": coordinated}
    return out


def _format_surface_relations(row: dict) -> list[str]:
    """Indented text lines describing a scheduling row's surface relationships.
    Empty when the row has neither overlaps nor coordinated siblings."""
    lines: list[str] = []
    for e in row.get("surface_overlap", []):
        lines.append(
            f"    surface_overlap: {e['sibling']} ({', '.join(e['surfaces'])})"
        )
    for e in row.get("coordinated", []):
        lines.append(
            f"    coordinated: {e['sibling']} ({', '.join(e['surfaces'])}) "
            f"[group={e['group']}]"
        )
    return lines
```

- [ ] **Step 4: Enrich `cmd_schedule`**

Replace the body of `cmd_schedule` (currently ~lines 2021–2063) with this version. The changes: compute `overlap_map` once, attach `surface_overlap`/`coordinated` to each row, and append `_format_surface_relations(row)` lines under each text row.

```python
def cmd_schedule(*, repo_root: Path, phase_id: str, format: str = "text") -> str:
    p = _load(repo_root)
    phase = _phase_by_id(p, phase_id)
    done = _done_slice_ids(phase)
    cancelled = _cancelled_slice_ids(phase)
    overlap_map = _surface_overlap_map(phase)
    rows = []
    for s in phase.slices:
        waiting_on = [
            dep for dep in s.depends_on if dep not in done and dep not in cancelled
        ]
        cancelled_deps = [dep for dep in s.depends_on if dep in cancelled]
        ready = _is_slice_ready_for_work(phase, s) and not cancelled_deps
        qid = f"{phase.id}.{s.id}"
        rel = overlap_map.get(qid, {"surface_overlap": [], "coordinated": []})
        rows.append({
            "id": qid,
            "status": s.status.value,
            "planning_status": s.planning_status.value,
            "parallel_group": s.parallel_group,
            "depends_on": s.depends_on,
            "waiting_on": waiting_on,
            "cancelled_deps": cancelled_deps,
            "ready": ready,
            "title": s.title,
            "surface_overlap": rel["surface_overlap"],
            "coordinated": rel["coordinated"],
        })
    if format == "json":
        import json as _j
        return _j.dumps(rows, indent=2) + "\n"
    lines = [f"# {phase.id} — {phase.title}", ""]
    if phase.planning_path:
        lines.append(f"planning: {phase.planning_path}")
    for row in rows:
        ready = "ready" if row["ready"] else "waiting"
        deps = ", ".join(row["depends_on"]) if row["depends_on"] else "-"
        waits = ", ".join(row["waiting_on"]) if row["waiting_on"] else "-"
        cancelled_str = (
            ", ".join(row["cancelled_deps"]) if row["cancelled_deps"] else "-"
        )
        group = row["parallel_group"] or "-"
        lines.append(
            f"{row['id']}  [{row['status']}/{row['planning_status']}]  "
            f"group={group}  {ready}  deps={deps}  waiting_on={waits}  "
            f"cancelled_deps={cancelled_str}  {row['title']}"
        )
        lines.extend(_format_surface_relations(row))
    return "\n".join(lines).rstrip() + "\n"
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tools/tasktool/tests/test_commands.py -k SurfaceOverlapScheduling -q`
Expected: PASS (all five).

- [ ] **Step 6: Run the existing scheduling tests to confirm no regression**

Run: `python -m pytest tools/tasktool/tests/test_commands.py -k Scheduling -q`
Expected: PASS (the original `SchedulingTests` plus the new class). The added JSON keys and indented text lines are additive; the existing `assertIn`/`next(...)` assertions still hold.

- [ ] **Step 7: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
git commit -m "P7.S3: surface-relation helpers + schedule overlap warnings"
```

---

## Task 2 — `cmd_ready_slices` enrichment

**Files:**
- Modify: `tools/tasktool/commands.py` (`cmd_ready_slices`, ~line 1998)
- Test: `tools/tasktool/tests/test_commands.py`

- [ ] **Step 1: Write the failing test**

Add to `SurfaceOverlapSchedulingTests`:

```python
    def test_ready_slices_warns_unguarded_overlap(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        rows = json.loads(commands.cmd_ready_slices(
            repo_root=self.t.root, phase_id="P1", format="json"))
        s1 = self._row(rows, "P1.S1")
        self.assertEqual(
            s1["surface_overlap"],
            [{"sibling": "P1.S2", "surfaces": ["cms-block-registry"]}],
        )

    def test_ready_slices_text_shows_overlap_line(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        out = commands.cmd_ready_slices(repo_root=self.t.root, phase_id="P1")
        self.assertIn("P1.S1", out)
        self.assertIn("surface_overlap: P1.S2 (cms-block-registry)", out)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tools/tasktool/tests/test_commands.py -k "ready_slices_warns or ready_slices_text_shows" -q`
Expected: FAIL — `KeyError: 'surface_overlap'`.

- [ ] **Step 3: Enrich `cmd_ready_slices`**

Replace the body of `cmd_ready_slices` (currently ~lines 1998–2019) with:

```python
def cmd_ready_slices(*, repo_root: Path, phase_id: str, format: str = "text") -> str:
    p = _load(repo_root)
    phase = _phase_by_id(p, phase_id)
    overlap_map = _surface_overlap_map(phase)
    rows = []
    for s in phase.slices:
        if not _is_slice_ready_for_work(phase, s):
            continue
        qid = f"{phase.id}.{s.id}"
        rel = overlap_map.get(qid, {"surface_overlap": [], "coordinated": []})
        rows.append({
            "id": qid,
            "status": s.status.value,
            "planning_status": s.planning_status.value,
            "parallel_group": s.parallel_group,
            "title": s.title,
            "surface_overlap": rel["surface_overlap"],
            "coordinated": rel["coordinated"],
        })
    if format == "json":
        import json as _j
        return _j.dumps(rows, indent=2) + "\n"
    out_lines: list[str] = []
    for r in rows:
        out_lines.append(
            f"{r['id']}  [{r['status']}/{r['planning_status']}]  "
            f"{r['parallel_group'] or '-'}  {r['title']}"
        )
        out_lines.extend(_format_surface_relations(r))
    return ("\n".join(out_lines) + "\n") if out_lines else ""
```

> The original returned `"".join(f"…\n" …)`, i.e. `""` when there were no rows. The `("\n".join(...) + "\n") if out_lines else ""` form preserves both the per-line newline and the empty-output case.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tools/tasktool/tests/test_commands.py -k "ready_slices" -q`
Expected: PASS — both the new tests and the original `test_ready_slices_respects_dependencies` / `test_ready_slices_omits_slice_with_cancelled_dep` (which use `assertIn`/`assertNotIn` and are unaffected by the additive fields and reformatted-but-equivalent line).

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
git commit -m "P7.S3: ready-slices surface overlap warnings"
```

---

## Task 3 — `cmd_surface_check` + reservation-contention helper + CLI wiring

**Files:**
- Modify: `tools/tasktool/commands.py` (add `_reservation_contention` and `cmd_surface_check`, after `cmd_surface_list`, ~line 1407)
- Modify: `tools/tasktool/cli.py` (add `surface check` subparser ~line 196; dispatch ~line 497)
- Test: `tools/tasktool/tests/test_commands.py`, `tools/tasktool/tests/test_cli_integration.py`

- [ ] **Step 1: Write the failing tests (command level)**

Add to `SurfaceOverlapSchedulingTests`:

```python
    def test_surface_check_json_shape(self):
        # S1 <-> S2 unguarded overlap; S3 <-> S4 coordinated.
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S3",
                                 surfaces=["directus-schema"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S4",
                                 surfaces=["directus-schema"])
        commands.cmd_coordinate(repo_root=self.t.root, slice_id="P1.S3", group="cms")
        commands.cmd_coordinate(repo_root=self.t.root, slice_id="P1.S4", group="cms")
        report = json.loads(commands.cmd_surface_check(
            repo_root=self.t.root, phase_id="P1", format="json"))
        self.assertEqual(report["phase"], "P1")
        self.assertEqual(
            report["unguarded_overlaps"],
            [{"slices": ["P1.S1", "P1.S2"], "surfaces": ["cms-block-registry"]}],
        )
        self.assertEqual(
            report["coordinated_surfaces"],
            [{"slices": ["P1.S3", "P1.S4"], "surfaces": ["directus-schema"],
              "group": "cms"}],
        )
        self.assertEqual(report["reservation_contention"], [])

    def test_surface_check_reports_forced_reservation_contention(self):
        # A --force override is the only way two non-cancelled slices hold the
        # same resource:value; surface check surfaces it for audit.
        commands.cmd_reserve_add(repo_root=self.t.root, slice_id="P1.S1",
                                 resource_value="homepage-sort:15", scope="phase")
        commands.cmd_reserve_add(repo_root=self.t.root, slice_id="P1.S2",
                                 resource_value="homepage-sort:15", scope="phase",
                                 force=True, reason="intentional shared slot")
        report = json.loads(commands.cmd_surface_check(
            repo_root=self.t.root, phase_id="P1", format="json"))
        self.assertEqual(
            report["reservation_contention"],
            [{"resource": "homepage-sort", "value": "15",
              "slices": ["P1.S1", "P1.S2"]}],
        )

    def test_surface_check_same_slice_dual_scope_is_not_contention(self):
        # One slice may hold the same resource:value at BOTH phase and project
        # scope (S2 allows it). That is one holder, not contention — the qid is
        # de-duplicated per (resource, value), so reservation_contention stays empty.
        commands.cmd_reserve_add(repo_root=self.t.root, slice_id="P1.S1",
                                 resource_value="homepage-sort:15", scope="phase")
        commands.cmd_reserve_add(repo_root=self.t.root, slice_id="P1.S1",
                                 resource_value="homepage-sort:15", scope="project")
        report = json.loads(commands.cmd_surface_check(
            repo_root=self.t.root, phase_id="P1", format="json"))
        self.assertEqual(report["reservation_contention"], [])

    def test_surface_check_text_sections(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        out = commands.cmd_surface_check(repo_root=self.t.root, phase_id="P1")
        self.assertIn("Unguarded surface overlaps", out)
        self.assertIn("P1.S1, P1.S2: cms-block-registry", out)
        self.assertIn("(none)", out)  # coordinated + contention sections empty

    def test_surface_check_unknown_phase_raises(self):
        with self.assertRaises(commands.CommandError):
            commands.cmd_surface_check(repo_root=self.t.root, phase_id="P9")
```

> Confirm the `cmd_reserve_add` keyword signature against `commands.py` before relying on it: it is `cmd_reserve_add(*, repo_root, slice_id, resource_value, scope="phase", note=None, force=False, reason=None)`. If `--force` requires `reason` (it does — S2), pass both.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/tasktool/tests/test_commands.py -k surface_check -q`
Expected: FAIL — `AttributeError: module 'tasktool.commands' has no attribute 'cmd_surface_check'`.

- [ ] **Step 3: Add `_reservation_contention` and `cmd_surface_check`**

In `tools/tasktool/commands.py`, **after** `cmd_surface_list` (the function ending ~line 1407) and before `cmd_coordinate`, add:

```python
def _reservation_contention(phase: Phase) -> list:
    """Resource:value pairs claimed by more than one non-cancelled slice in `phase`.

    Empty under normal operation — `reserve add` refuses duplicates (S2). It is
    non-empty only when a `--force` override created a deliberate collision, which
    this audit surfaces. A single slice holding the same resource:value at both
    phase and project scope is NOT contention, so qids are de-duplicated per pair.
    """
    holders: dict = {}
    for s in phase.slices:
        if s.status == Status.CANCELLED:
            continue
        qid = f"{phase.id}.{s.id}"
        for r in s.reservations:
            qids = holders.setdefault((r.resource, r.value), [])
            if qid not in qids:
                qids.append(qid)
    return [
        {"resource": res, "value": val, "slices": qids}
        for (res, val), qids in holders.items()
        if len(qids) > 1
    ]


def cmd_surface_check(*, repo_root: Path, phase_id: str, format: str = "text") -> str:
    """Read-only audit (spec 4.C): unguarded surface overlaps, coordinated
    surfaces, and reservation contention within a phase. Warning surface only —
    never mutates, never refuses."""
    p = _load(repo_root)
    phase = _phase_by_id(p, phase_id)
    actives = [
        (f"{phase.id}.{s.id}", s) for s in phase.slices if not is_terminal(s.status)
    ]
    unguarded: list = []
    coordinated: list = []
    for i in range(len(actives)):
        a_qid, a = actives[i]
        for j in range(i + 1, len(actives)):
            b_qid, b = actives[j]
            kind, shared = _pair_surface_relation(a_qid, a, b_qid, b)
            if kind == "overlap":
                unguarded.append({"slices": [a_qid, b_qid], "surfaces": shared})
            elif kind == "coordinated":
                coordinated.append(
                    {"slices": [a_qid, b_qid], "surfaces": shared,
                     "group": a.coordination_group}
                )
    contention = _reservation_contention(phase)
    if format == "json":
        import json as _j
        return _j.dumps({
            "phase": phase.id,
            "unguarded_overlaps": unguarded,
            "coordinated_surfaces": coordinated,
            "reservation_contention": contention,
        }, indent=2) + "\n"
    lines = [f"# {phase.id} surface check", ""]
    lines.append("Unguarded surface overlaps (add a depends_on or coordination_group):")
    if unguarded:
        for e in unguarded:
            lines.append(f"  - {', '.join(e['slices'])}: {', '.join(e['surfaces'])}")
    else:
        lines.append("  (none)")
    lines.append("Coordinated surfaces (shared within a coordination_group):")
    if coordinated:
        for e in coordinated:
            lines.append(
                f"  - {', '.join(e['slices'])}: {', '.join(e['surfaces'])} "
                f"[group={e['group']}]"
            )
    else:
        lines.append("  (none)")
    lines.append("Reservation contention (expected empty unless --force was used):")
    if contention:
        for e in contention:
            lines.append(
                f"  - {e['resource']}:{e['value']} held by {', '.join(e['slices'])}"
            )
    else:
        lines.append("  (none)")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run the command-level tests to verify they pass**

Run: `python -m pytest tools/tasktool/tests/test_commands.py -k surface_check -q`
Expected: PASS (all four).

- [ ] **Step 5: Wire the `surface check` subcommand into `cli.py`**

In `tools/tasktool/cli.py`, after the `p_surface_list` block (~line 196, the `surface list` parser), add:

```python
    p_surface_check = surface_sub.add_parser("check")
    p_surface_check.add_argument("phase_id")
    p_surface_check.add_argument("--format", choices=["text", "json"], default="text")
```

Then in `main()`, inside the `elif args.cmd == "surface":` block, after the `list` branch (~line 497), add:

```python
            elif args.surface_cmd == "check":
                sys.stdout.write(commands.cmd_surface_check(
                    repo_root=root, phase_id=args.phase_id, format=args.format,
                ))
```

- [ ] **Step 6: Write the failing CLI integration test**

`tools/tasktool/tests/test_cli_integration.py` already provides `run_cli(*args, cwd=None) -> subprocess.CompletedProcess` (exposes `.returncode`, `.stdout`, `.stderr`) and the `_CliTmp` fixture (a temp project with `config init-local` already run). `json` is already imported in that file. Add a new test class at the end:

```python
class SurfaceCheckCliTests(unittest.TestCase):
    def _setup(self, t):
        self.assertEqual(run_cli("init", "--project", "demo", cwd=t.root).returncode, 0)
        run_cli("create", "phase", "--title", "P", cwd=t.root)
        run_cli("create", "slice", "P1", "--title", "a", cwd=t.root)
        run_cli("create", "slice", "P1", "--title", "b", cwd=t.root)

    def test_surface_check_cli_json(self):
        t = _CliTmp()
        try:
            self._setup(t)
            self.assertEqual(
                run_cli("surface", "add", "P1.S1", "cms-block-registry", cwd=t.root).returncode, 0)
            self.assertEqual(
                run_cli("surface", "add", "P1.S2", "cms-block-registry", cwd=t.root).returncode, 0)
            r = run_cli("surface", "check", "P1", "--format", "json", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)
            report = json.loads(r.stdout)
            self.assertEqual(
                report["unguarded_overlaps"],
                [{"slices": ["P1.S1", "P1.S2"], "surfaces": ["cms-block-registry"]}],
            )
        finally:
            t.cleanup()
```

- [ ] **Step 7: Run the integration test to verify it fails, then passes**

Run: `python -m pytest tools/tasktool/tests/test_cli_integration.py -k surface_check -q`
Expected: first FAIL if run before Step 5 wiring; after Step 5 it PASSES (exit 0, correct JSON).

- [ ] **Step 8: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_cli_integration.py
git commit -m "P7.S3: surface check audit command + CLI wiring"
```

---

## Task 4 — `ratify --parallel-group` overlap warning

**Files:**
- Modify: `tools/tasktool/commands.py` (`cmd_ratify`, ~line 1334; add `_ratify_parallel_group_warning`)
- Modify: `tools/tasktool/cli.py` (`ratify` dispatch, ~line 480)
- Test: `tools/tasktool/tests/test_commands.py`, `tools/tasktool/tests/test_cli_integration.py`

- [ ] **Step 1: Write the failing tests (command level)**

Add to `SurfaceOverlapSchedulingTests`:

```python
    def test_ratify_parallel_group_warns_on_surface_overlap(self):
        # S1 already in group 'core' with a shared surface; ratifying S2 into the
        # same group with the same surface and no dep/coordination link warns.
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        commands.cmd_ratify(repo_root=self.t.root, slice_id="P1.S1",
                            parallel_group="core")
        warning = commands.cmd_ratify(repo_root=self.t.root, slice_id="P1.S2",
                                      parallel_group="core")
        self.assertIsNotNone(warning)
        self.assertIn("P1.S2", warning)
        self.assertIn("P1.S1", warning)
        self.assertIn("cms-block-registry", warning)
        self.assertIn("core", warning)
        # The mutation still applied despite the warning.
        p = load_project(self.t.root / "docs/tasklist.json")
        s2 = p.phases[0].slices[1]
        self.assertEqual(s2.parallel_group, "core")
        self.assertEqual(s2.planning_status.value, "ratified")

    def test_ratify_no_warning_when_dep_link_present(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        commands.cmd_deps(repo_root=self.t.root, slice_id="P1.S2", add="P1.S1")
        commands.cmd_ratify(repo_root=self.t.root, slice_id="P1.S1",
                            parallel_group="core")
        warning = commands.cmd_ratify(repo_root=self.t.root, slice_id="P1.S2",
                                      parallel_group="core")
        self.assertIsNone(warning)

    def test_ratify_no_warning_without_parallel_group(self):
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S1",
                                 surfaces=["cms-block-registry"])
        commands.cmd_surface_add(repo_root=self.t.root, slice_id="P1.S2",
                                 surfaces=["cms-block-registry"])
        warning = commands.cmd_ratify(repo_root=self.t.root, slice_id="P1.S2")
        self.assertIsNone(warning)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tools/tasktool/tests/test_commands.py -k "ratify_parallel_group or ratify_no_warning" -q`
Expected: FAIL — `cmd_ratify` returns `None` today, so `assertIsNotNone(warning)` fails.

- [ ] **Step 3: Add the warning helper and return it from `cmd_ratify`**

In `tools/tasktool/commands.py`, replace the existing `cmd_ratify` (currently ~lines 1334–1347) with the version below, and add `_ratify_parallel_group_warning` immediately above it.

```python
def _ratify_parallel_group_warning(p: Project, qid: str, item: Slice) -> str | None:
    """If `item` now sits in a parallel_group alongside a sibling it shares an
    integration surface with — and they are not reconciled by a depends_on link or
    a shared coordination_group — return a steer warning (spec 4.C). parallel_group
    asserts independence; a shared write surface contradicts that. Warning only;
    ratify still succeeds. Returns None when there is nothing to warn about."""
    group = item.parallel_group
    if not group:
        return None
    phase_id = qid.split(".")[0]
    phase = _phase_by_id(p, phase_id)
    conflicts: list = []
    for s in phase.slices:
        s_qid = f"{phase_id}.{s.id}"
        if s_qid == qid or is_terminal(s.status):
            continue
        if s.parallel_group != group:
            continue
        kind, shared = _pair_surface_relation(qid, item, s_qid, s)
        if kind == "overlap":
            conflicts.append((s_qid, shared))
    if not conflicts:
        return None
    lines = [
        f"tasktool: ratify warning: {qid} shares an integration surface with "
        f"sibling(s) already in parallel_group {group!r}, with no depends_on or "
        f"coordination_group link:"
    ]
    for s_qid, shared in conflicts:
        lines.append(f"  - {s_qid}: {', '.join(shared)}")
    lines.append(
        "Either add a depends_on (serialize) or a coordination_group (coordinate); "
        "parallel_group asserts independence."
    )
    return "\n".join(lines) + "\n"


def cmd_ratify(
    *, repo_root: Path, slice_id: str,
    status: str = "ratified", parallel_group: str | None = None,
) -> str | None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, slice_id)
        if parse_id(qid)[0] != "slice":
            raise CommandError(f"ratify only works on slices; {qid} is a {parse_id(qid)[0]}")
        _refuse_if_cancelled(qid, item, "ratify")
        item.planning_status = PlanningStatus(status)
        if parallel_group is not None:
            item.parallel_group = parallel_group or None
        warning = _ratify_parallel_group_warning(p, qid, item)
        _save(write_root, p)
        return warning
```

- [ ] **Step 4: Run the command-level tests to verify they pass**

Run: `python -m pytest tools/tasktool/tests/test_commands.py -k ratify -q`
Expected: PASS — the new tests **and** the existing `test_ratify_sets_planning_status_and_group` / `test_cmd_ratify_refuses_cancelled` (both ignore the return value).

- [ ] **Step 5: Print the warning in the `ratify` dispatch**

In `tools/tasktool/cli.py`, replace the `ratify` dispatch branch (~lines 480–484) with:

```python
        elif args.cmd == "ratify":
            warning = commands.cmd_ratify(
                repo_root=root, slice_id=args.slice_id,
                status=args.status, parallel_group=args.parallel_group,
            )
            if warning:
                sys.stderr.write(warning)
```

- [ ] **Step 6: Add the CLI integration test (warning to stderr, exit 0)**

In `tools/tasktool/tests/test_cli_integration.py`, add a new test class (same `run_cli`/`_CliTmp` helpers as Task 3):

```python
class RatifyWarningCliTests(unittest.TestCase):
    def test_ratify_parallel_group_warning_to_stderr(self):
        t = _CliTmp()
        try:
            run_cli("init", "--project", "demo", cwd=t.root)
            run_cli("create", "phase", "--title", "P", cwd=t.root)
            run_cli("create", "slice", "P1", "--title", "a", cwd=t.root)
            run_cli("create", "slice", "P1", "--title", "b", cwd=t.root)
            run_cli("surface", "add", "P1.S1", "cms-block-registry", cwd=t.root)
            run_cli("surface", "add", "P1.S2", "cms-block-registry", cwd=t.root)
            run_cli("ratify", "P1.S1", "--parallel-group", "core", cwd=t.root)
            r = run_cli("ratify", "P1.S2", "--parallel-group", "core", cwd=t.root)
            self.assertEqual(r.returncode, 0, r.stderr)   # warning does NOT refuse
            self.assertIn("ratify warning", r.stderr)
            self.assertIn("cms-block-registry", r.stderr)
        finally:
            t.cleanup()
```

- [ ] **Step 7: Run the integration test to verify it passes**

Run: `python -m pytest tools/tasktool/tests/test_cli_integration.py -k ratify_parallel_group -q`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_cli_integration.py
git commit -m "P7.S3: ratify --parallel-group surface overlap warning"
```

---

## Task 5 — Full-suite verification, manual smoke, scheduling ratification, slice close

### 5.1 Run the focused suites, then the whole tasktool suite

- [ ] Run the two files this slice changed:
  ```sh
  python -m pytest tools/tasktool/tests/test_commands.py tools/tasktool/tests/test_cli_integration.py -q
  ```
  Expected: **all pass**.
- [ ] Run the entire tasktool suite:
  ```sh
  python -m pytest tools/tasktool/tests -q
  ```
  Expected: **all pass**. If `test_worktree_integration.py` fails on a surface field, that is an S4-owned helper (`cmd_worktree_status_integration` already reads `integration_surfaces`); this slice does not touch it, so a failure there means a merge/integration problem, not a S3 defect — re-check you are on an up-to-date base (see 5.4).

### 5.2 Whole-repo suite (catch cross-cutting regressions)

- [ ] Run:
  ```sh
  python -m pytest -q
  ```
  Expected: **all pass** (`testpaths` cover `scripts/tests`, `tools/tasktool/tests`, `skills/external-review/tests`).

### 5.3 Manual CLI smoke (evidence for the post-slice review)

- [ ] Exercise the warning paths in a **throwaway directory** — never against the real `docs/tasklist.json`. `TT` is the absolute path to the wrapper, and **every** invocation passes the global `--project-root "$SCRATCH"` flag so tasktool operates on the throwaway dir rather than walking up to the repo's authoritative tracker (a plain `cd "$SCRATCH"` is *not* enough: from inside the repo tree tasktool would still resolve and route to the configured repo root, exiting non-zero with an authoritative-routing error). If you have `SUPERSTAR_SUBAGENT_ROLE` set in your shell, unset it for these calls (`env -u SUPERSTAR_SUBAGENT_ROLE …`), since that var makes tasktool refuse mutations:
  ```sh
  TT="$PWD/tools/tasktool/tasktool"
  SCRATCH="$(mktemp -d)"
  (
    "$TT" --project-root "$SCRATCH" config init-local &&
    "$TT" --project-root "$SCRATCH" init --project smoke &&
    "$TT" --project-root "$SCRATCH" create phase --title "Smoke" &&
    "$TT" --project-root "$SCRATCH" create slice P1 --title "a" &&
    "$TT" --project-root "$SCRATCH" create slice P1 --title "b" &&
    "$TT" --project-root "$SCRATCH" surface add P1.S1 cms-block-registry &&
    "$TT" --project-root "$SCRATCH" surface add P1.S2 cms-block-registry &&
    echo "--- surface check (expect unguarded overlap P1.S1, P1.S2) ---" &&
    "$TT" --project-root "$SCRATCH" surface check P1 &&
    echo "--- schedule (expect surface_overlap lines) ---" &&
    "$TT" --project-root "$SCRATCH" schedule P1 &&
    echo "--- ratify into shared parallel_group (warning to stderr, must still exit 0) ---" &&
    "$TT" --project-root "$SCRATCH" ratify P1.S1 --parallel-group core &&
    "$TT" --project-root "$SCRATCH" ratify P1.S2 --parallel-group core
  )
  echo "smoke exit=$?"
  rm -rf "$SCRATCH"
  ```
  Expected: `surface check` lists `P1.S1, P1.S2: cms-block-registry` under "Unguarded surface overlaps"; `schedule` shows `surface_overlap: …` indented lines; the second `ratify` prints a `ratify warning` to **stderr** while still exiting 0, so the `&&` chain runs to completion and the final line prints `smoke exit=0`. A non-zero `smoke exit` means some command in the guarded chain failed — investigate before review. The temp dir is deleted, so the real tracker is untouched.

### 5.4 Integrate current main before review (per subagent-driven-development)

- [ ] Run `./tools/tasktool/tasktool worktree status P7.S3 --integration`. If a sibling has landed on base since this worktree's `worktree_base_sha`, integrate base (`tasktool worktree sync … --merge|--rebase`, or the documented raw-git fallback), then re-run 5.1–5.2 before requesting the review. (Even though no other P7 slice is currently in flight, this is the standing checkpoint.)

### 5.5 Confirm the scheduling contract is unchanged

- [ ] Verify deps are still `[P7.S1, P7.S2]` and that no `parallel_group` was added:
  ```sh
  ./tools/tasktool/tasktool show P7.S3
  ```
  Expected: `depends_on: P7.S1, P7.S2`; no parallel_group. The plan made no dependency-graph change, so no `tasktool deps` edit is needed.

### 5.6 Close the slice

- [ ] Hand off to `superstar:external-review --kind post-slice` per the project workflow. Once the verdict is `ready` / `ready with small edits`, the coordinator ratifies and closes:
  ```sh
  ./tools/tasktool/tasktool ratify P7.S3
  ./tools/tasktool/tasktool close P7.S3
  ```
  (Do **not** run a version bump or plugin re-sync here — those happen at phase close per the repo release policy.)

---

## Edge cases & invariants checklist (verify each is covered by a test above)

- [ ] **Symmetry:** an unguarded overlap is reported on **both** subjects (Task 1, `test_schedule_warns_unguarded_surface_overlap` asserts S1→S2 and S2→S1).
- [ ] **Dep-link suppression:** a shared surface with a `depends_on` link in either direction yields **no** warning (Task 1 `test_schedule_dep_link_suppresses_overlap`; Task 4 `test_ratify_no_warning_when_dep_link_present`).
- [ ] **Coordination-group reporting:** a shared surface inside one `coordination_group` is reported as `coordinated`, never as `surface_overlap` (Task 1 `test_schedule_coordination_group_reports_coordinated_not_warned`; Task 3 `surface check` `coordinated_surfaces`).
- [ ] **Terminal exclusion:** a `done`/`cancelled` slice is neither subject nor candidate (Task 1 `test_schedule_done_slice_not_a_candidate`).
- [ ] **Reporter subject predicate (spec §4.C):** only ready-for-work / in-progress slices are warning **subjects**; a dependency-waiting (or blocked) slice gets no relations on its own row but is still a **candidate** a ready sibling is warned about (Task 1 `test_schedule_waiting_slice_is_candidate_not_subject`). Note `cmd_ready_slices` rows are all ready-for-work, so this narrowing is a no-op there and only affects `cmd_schedule`'s full-row output.
- [ ] **Reservation contention is audit-only and normally empty:** populated only via a `--force` override (Task 3 `test_surface_check_reports_forced_reservation_contention`); a single slice holding the same `resource:value` at phase **and** project scope is **not** contention — the qid is de-duped per `(resource, value)` (Task 3 `test_surface_check_same_slice_dual_scope_is_not_contention`).
- [ ] **`surface check` unknown phase raises `CommandError`** via `_phase_by_id` (Task 3 `test_surface_check_unknown_phase_raises`).
- [ ] **Ratify warns but never blocks:** the mutation (`parallel_group`, `planning_status`) still applies; CLI exits 0 (Task 4 `test_ratify_parallel_group_warns_on_surface_overlap` + the CLI test asserting `returncode == 0`).
- [ ] **No warning without `--parallel-group`** (Task 4 `test_ratify_no_warning_without_parallel_group`).
- [ ] **Additive, non-breaking:** existing `SchedulingTests`, ratify, and surface/coordinate tests still pass (Tasks 1, 2, 4 regression runs).
```