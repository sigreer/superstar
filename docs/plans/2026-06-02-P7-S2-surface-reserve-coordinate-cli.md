# P7.S2 — surface / reserve / coordinate CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `tasktool surface`, `tasktool reserve`, and `tasktool coordinate` declaration commands plus reservation-collision refusal (phase + project scope), `--force --reason` override, and `archive-phase` ledger population, so planners can declare integration surfaces and hard-block duplicate scarce-resource allocations at planning time.

**Architecture:** New command functions live in `tools/tasktool/commands.py` (declaration/mutation logic, refusal logic, ledger population), wired into argparse subparsers + dispatch in `tools/tasktool/cli.py`. They reuse the existing `_write_context`/`_load`/`_save` transaction helpers, `_find_item` for ID resolution, `_refuse_if_cancelled`, and `_dt`/`_today` for note timestamps. Ledger population hooks into the existing `_cmd_archive_phase_at_root`. All reads/writes operate on the S1 dataclasses (`Slice.integration_surfaces`, `Slice.reservations`, `Slice.coordination_group`, `Project.reservations_ledger`, the `Reservation` and `LedgerReservation` types).

**Tech Stack:** Python 3, argparse, pytest

---

## Scheduling

- **This slice is `P7.S2`.** It `depends_on` `P7.S1` (the schema-v3 data model: the `Slice.integration_surfaces` / `Slice.reservations` / `Slice.coordination_group` fields, the `Reservation` and `LedgerReservation` dataclasses, and `Project.reservations_ledger`). It **must not start before S1's fields exist** — every task here reads or writes those fields. If you open `tools/tasktool/model.py` and it still has `SCHEMA_VERSION = 2` with no `integration_surfaces` field on `Slice`, **stop**: S1 is not merged. Do not stub the model in this slice.
- **This slice blocks `P7.S3`** (scheduling overlap detection reads the surfaces/reservations/coordination_group this slice writes) **and `P7.S6`** (skill docs that document these commands).
- It shares **no** integration surface with `P7.S4` (`cli`/`commands` here vs `worktree` there); the two are genuinely parallel once S1 lands.
- **Surfaces this slice writes:** `cli`, `commands`. **Reservations:** none.

### First action before any source edit

- [ ] Run, from the repo root `/home/simon/Dev/sigreer/skills/superstar`:
  ```sh
  ./tools/tasktool/tasktool start P7.S2
  ```
  This creates/records the worktree and flips `P7.S2` to `in_progress`. `cd` into the printed worktree path and do all subsequent work there. (If the project is configured local-mode and the command prints `cd <path>`, follow it.)

---

## File Structure

| File | Responsibility (in this slice) |
|------|-------------------------------|
| `tools/tasktool/commands.py` | New command functions: `cmd_surface_add`, `cmd_surface_remove`, `cmd_surface_list`, `cmd_reserve_add`, `cmd_reserve_remove`, `cmd_reserve_list`, `cmd_coordinate`. New private helpers: `_parse_resource_value`, `_iter_phase_slices`, `_phase_scope_holder`, `_project_scope_holder`, `_format_ledger_holder`. New ledger-population block inside `_cmd_archive_phase_at_root`. |
| `tools/tasktool/cli.py` | New `surface`, `reserve`, `coordinate` subparsers (with their sub-subcommands and flags) + dispatch branches in `main()` that call the new command functions. |
| `tools/tasktool/tests/test_commands.py` | Unit tests calling the command functions directly (matches the file's `_Tmp` + `load_project` style). Covers surface add/remove/list, reserve add/remove/list, refusal (phase scope incl. done slices, project scope incl. ledger), `--force`/`--reason`, override note, coordinate set/clear, ledger population/dedupe/cancelled-exclusion/idempotent re-archive. |
| `tools/tasktool/tests/test_cli_integration.py` | End-to-end CLI tests via `run_cli(...)` asserting exit codes (refusal exits non-zero; `--force` without `--reason` exits non-zero) and stdout/stderr text. |

**Source of truth is `tools/tasktool/`.** Do NOT edit the `plugins/superstar/` copy — it is synced at release. Every path below is relative to the repo root unless noted.

---

## Conventions you will reuse (read once before starting)

These already exist in `tools/tasktool/commands.py`; the new commands must follow them exactly.

- **Transaction wrapper:** every mutating command is `with _write_context(repo_root) as write_root:` → `p = _load(write_root)` → mutate → `_save(write_root, p)`. Read-only commands (the `*_list` ones) use `with _read_context(repo_root) as write_root:` → `p = _load(write_root)` → build string → return.
- **ID resolution:** `qid, _container, item = _find_item(p, slice_id)`. After resolution, guard the kind with `if parse_id(qid)[0] != "slice": raise CommandError(...)` (see `cmd_deps`, `cmd_ratify`).
- **Cancelled guard:** mutating a row → `_refuse_if_cancelled(qid, item, "<verb>")`.
- **Errors:** raise `CommandError("...")`. `cli.main()` already catches `CommandError`, prints `tasktool: <msg>` to stderr, and returns exit code 1. Argparse usage errors exit 2.
- **Timestamped notes:** `ts = _dt.datetime.now().isoformat(timespec="seconds")` then append `item.notes = (item.notes + "\n" + line).strip() if item.notes else line` (see `_apply_ready_close_override`).
- **Listing rows of a phase:** iterate `phase.slices`; phase lookup is `phase = next((ph for ph in p.phases if ph.id == phase_id), None)`.
- **Test invocation:** from repo root, run a single test file with
  ```sh
  python -m pytest tools/tasktool/tests/test_commands.py -q
  ```
  (`pyproject.toml` sets `addopts = "--import-mode=importlib"`; `testpaths` includes `tools/tasktool/tests`.) Tests import `from tasktool import commands` — the package resolves because pytest runs from repo root with `tools/` on the path via the wrapper; if an import fails, run with `PYTHONPATH=tools python -m pytest ...`.

---

## Task 1 — `surface add` / `surface remove` (declaration only)

### 1.1 Failing test for `surface add`

- [ ] Add to `tools/tasktool/tests/test_commands.py` a new test class near the other declaration tests:
  ```python
  class SurfaceCommandTests(unittest.TestCase):
      def _setup_phase_with_slice(self, t):
          commands.cmd_init(repo_root=t.root, project="demo")
          pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
          sid = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="slice")
          return pid, sid

      def test_surface_add_appends_unique_sorted(self):
          t = _Tmp()
          try:
              pid, sid = self._setup_phase_with_slice(t)
              commands.cmd_surface_add(
                  repo_root=t.root, slice_id=f"{pid}.{sid}",
                  surfaces=["cms-block-registry", "directus-schema", "cms-block-registry"],
              )
              p = load_project(t.root / "docs/tasklist.json")
              slc = p.phases[0].slices[0]
              self.assertEqual(slc.integration_surfaces, ["cms-block-registry", "directus-schema"])
          finally:
              t.cleanup()
  ```

### 1.2 Run it — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_commands.py::SurfaceCommandTests::test_surface_add_appends_unique_sorted -q
  ```
  Expected: **FAIL** with `AttributeError: module 'tasktool.commands' has no attribute 'cmd_surface_add'`.

### 1.3 Implement `cmd_surface_add` and `cmd_surface_remove`

- [ ] Add to `tools/tasktool/commands.py` after `cmd_ratify` (around line 1320), a new section:
  ```python
  # ───── surface / reserve / coordinate (P7.S2) ─────

  def _require_slice(p: Project, slice_id: str, verb: str):
      """Resolve `slice_id` to a slice row, refusing non-slice ids and cancelled rows.
      Returns (qid, item)."""
      qid, _container, item = _find_item(p, slice_id)
      if parse_id(qid)[0] != "slice":
          raise CommandError(f"{verb} only works on slices; {qid} is a {parse_id(qid)[0]}")
      _refuse_if_cancelled(qid, item, verb)
      return qid, item


  def cmd_surface_add(*, repo_root: Path, slice_id: str, surfaces: list[str]) -> None:
      cleaned = [s.strip() for s in surfaces if s and s.strip()]
      if not cleaned:
          raise CommandError("surface add requires at least one non-empty surface")
      with _write_context(repo_root) as write_root:
          p = _load(write_root)
          _qid, item = _require_slice(p, slice_id, "surface add")
          for s in cleaned:
              if s not in item.integration_surfaces:
                  item.integration_surfaces.append(s)
          _save(write_root, p)


  def cmd_surface_remove(*, repo_root: Path, slice_id: str, surface: str) -> None:
      surface = (surface or "").strip()
      if not surface:
          raise CommandError("surface remove requires a non-empty surface")
      with _write_context(repo_root) as write_root:
          p = _load(write_root)
          _qid, item = _require_slice(p, slice_id, "surface remove")
          if surface in item.integration_surfaces:
              item.integration_surfaces.remove(surface)
          _save(write_root, p)
  ```
  Note: the test asserts order `["cms-block-registry", "directus-schema"]`, which is **insertion order with dedupe** (not alpha-sort). The implementation preserves first-seen order. Keep the test assertion matching insertion order.

### 1.4 Run it — expect PASS

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_commands.py::SurfaceCommandTests::test_surface_add_appends_unique_sorted -q
  ```
  Expected: **PASS** (1 passed).

### 1.5 Failing test for `surface remove`

- [ ] Add to `SurfaceCommandTests`:
  ```python
      def test_surface_remove_drops_one(self):
          t = _Tmp()
          try:
              pid, sid = self._setup_phase_with_slice(t)
              commands.cmd_surface_add(
                  repo_root=t.root, slice_id=f"{pid}.{sid}",
                  surfaces=["cms-block-registry", "directus-schema"],
              )
              commands.cmd_surface_remove(
                  repo_root=t.root, slice_id=f"{pid}.{sid}", surface="directus-schema",
              )
              p = load_project(t.root / "docs/tasklist.json")
              self.assertEqual(p.phases[0].slices[0].integration_surfaces, ["cms-block-registry"])
          finally:
              t.cleanup()

      def test_surface_add_refuses_cancelled_slice(self):
          t = _Tmp()
          try:
              pid, sid = self._setup_phase_with_slice(t)
              commands.cmd_cancel(repo_root=t.root, id=f"{pid}.{sid}", reason="dropped")
              with self.assertRaises(commands.CommandError):
                  commands.cmd_surface_add(
                      repo_root=t.root, slice_id=f"{pid}.{sid}", surfaces=["x"],
                  )
          finally:
              t.cleanup()
  ```

### 1.6 Run — expect PASS

- [ ] Run:
  ```sh
  python -m pytest "tools/tasktool/tests/test_commands.py::SurfaceCommandTests" -q
  ```
  Expected: **PASS** (3 passed). `cmd_surface_remove` and the cancelled-guard are already implemented in 1.3, so these pass without new impl.

### 1.7 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
  git commit -m "P7.S2: surface add/remove declaration commands"
  ```

---

## Task 2 — `surface list`

### 2.1 Failing test

- [ ] Add to `SurfaceCommandTests`:
  ```python
      def test_surface_list_renders_phase_slices(self):
          t = _Tmp()
          try:
              pid, sid = self._setup_phase_with_slice(t)
              commands.cmd_surface_add(
                  repo_root=t.root, slice_id=f"{pid}.{sid}",
                  surfaces=["cms-block-registry", "directus-schema"],
              )
              out = commands.cmd_surface_list(repo_root=t.root, phase_id=pid)
              self.assertIn(f"{pid}.{sid}", out)
              self.assertIn("cms-block-registry", out)
              self.assertIn("directus-schema", out)
          finally:
              t.cleanup()

      def test_surface_list_all_phases_when_omitted(self):
          t = _Tmp()
          try:
              pid, sid = self._setup_phase_with_slice(t)
              commands.cmd_surface_add(
                  repo_root=t.root, slice_id=f"{pid}.{sid}", surfaces=["theme-tail-css"],
              )
              out = commands.cmd_surface_list(repo_root=t.root, phase_id=None)
              self.assertIn("theme-tail-css", out)
          finally:
              t.cleanup()
  ```

### 2.2 Run — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_commands.py::SurfaceCommandTests::test_surface_list_renders_phase_slices -q
  ```
  Expected: **FAIL** with `AttributeError: ... has no attribute 'cmd_surface_list'`.

### 2.3 Implement `cmd_surface_list` (+ shared iterator helper)

- [ ] Add to `tools/tasktool/commands.py` in the same section:
  ```python
  def _iter_phase_slices(p: Project, phase_id: str | None):
      """Yield (phase, slice) for the given phase, or all active phases if None."""
      for ph in p.phases:
          if phase_id is not None and ph.id != phase_id:
              continue
          for slc in ph.slices:
              yield ph, slc


  def cmd_surface_list(*, repo_root: Path, phase_id: str | None) -> str:
      with _read_context(repo_root) as write_root:
          p = _load(write_root)
          if phase_id is not None and not any(ph.id == phase_id for ph in p.phases):
              raise CommandError(f"phase {phase_id} not found")
          lines: list[str] = []
          for ph, slc in _iter_phase_slices(p, phase_id):
              surfaces = ", ".join(slc.integration_surfaces) if slc.integration_surfaces else "(none)"
              lines.append(f"{ph.id}.{slc.id}  [{slc.status.value}]  {surfaces}")
          if not lines:
              return "(no slices)\n"
          return "\n".join(lines) + "\n"
  ```

### 2.4 Run — expect PASS

- [ ] Run:
  ```sh
  python -m pytest "tools/tasktool/tests/test_commands.py::SurfaceCommandTests" -q
  ```
  Expected: **PASS** (5 passed).

### 2.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
  git commit -m "P7.S2: surface list report"
  ```

---

## Task 3 — `coordinate` set / clear

### 3.1 Failing test

- [ ] Add a new test class to `tools/tasktool/tests/test_commands.py`:
  ```python
  class CoordinateCommandTests(unittest.TestCase):
      def _setup(self, t):
          commands.cmd_init(repo_root=t.root, project="demo")
          pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
          sid = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="slice")
          return pid, sid

      def test_coordinate_sets_group(self):
          t = _Tmp()
          try:
              pid, sid = self._setup(t)
              commands.cmd_coordinate(repo_root=t.root, slice_id=f"{pid}.{sid}", group="cms")
              p = load_project(t.root / "docs/tasklist.json")
              self.assertEqual(p.phases[0].slices[0].coordination_group, "cms")
          finally:
              t.cleanup()

      def test_coordinate_clear_resets_to_none(self):
          t = _Tmp()
          try:
              pid, sid = self._setup(t)
              commands.cmd_coordinate(repo_root=t.root, slice_id=f"{pid}.{sid}", group="cms")
              commands.cmd_coordinate(repo_root=t.root, slice_id=f"{pid}.{sid}", clear=True)
              p = load_project(t.root / "docs/tasklist.json")
              self.assertIsNone(p.phases[0].slices[0].coordination_group)
          finally:
              t.cleanup()

      def test_coordinate_requires_group_or_clear(self):
          t = _Tmp()
          try:
              pid, sid = self._setup(t)
              with self.assertRaises(commands.CommandError):
                  commands.cmd_coordinate(repo_root=t.root, slice_id=f"{pid}.{sid}")
          finally:
              t.cleanup()

      def test_coordinate_refuses_cancelled_slice(self):
          # A valid --group is passed so the flag-validation guard is satisfied and
          # the cancelled-slice guard inside `_require_slice` is the thing under test.
          t = _Tmp()
          try:
              pid, sid = self._setup(t)
              commands.cmd_cancel(repo_root=t.root, id=f"{pid}.{sid}", reason="dropped")
              with self.assertRaises(commands.CommandError):
                  commands.cmd_coordinate(repo_root=t.root, slice_id=f"{pid}.{sid}", group="cms")
          finally:
              t.cleanup()
  ```

### 3.2 Run — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_commands.py::CoordinateCommandTests::test_coordinate_sets_group -q
  ```
  Expected: **FAIL** with `AttributeError: ... has no attribute 'cmd_coordinate'`.

### 3.3 Implement `cmd_coordinate`

- [ ] Add to `tools/tasktool/commands.py`:
  ```python
  def cmd_coordinate(
      *, repo_root: Path, slice_id: str,
      group: str | None = None, clear: bool = False,
  ) -> None:
      if clear and group is not None:
          raise CommandError("coordinate: --group and --clear are mutually exclusive")
      if not clear and (group is None or not group.strip()):
          raise CommandError("coordinate requires --group <name> or --clear")
      with _write_context(repo_root) as write_root:
          p = _load(write_root)
          _qid, item = _require_slice(p, slice_id, "coordinate")
          item.coordination_group = None if clear else group.strip()
          _save(write_root, p)
  ```

### 3.4 Run — expect PASS

- [ ] Run:
  ```sh
  python -m pytest "tools/tasktool/tests/test_commands.py::CoordinateCommandTests" -q
  ```
  Expected: **PASS** (4 passed). `test_coordinate_refuses_cancelled_slice` passes without extra impl — `_require_slice` calls `_refuse_if_cancelled`.

### 3.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
  git commit -m "P7.S2: coordinate set/clear command"
  ```

---

## Task 4 — `reserve add` happy path + `resource:value` parsing

### 4.1 Failing test

- [ ] Add a new test class to `tools/tasktool/tests/test_commands.py`:
  ```python
  class ReserveCommandTests(unittest.TestCase):
      def _phase(self, t, n_slices=1):
          commands.cmd_init(repo_root=t.root, project="demo")
          pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
          sids = [
              commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title=f"slice{i}")
              for i in range(n_slices)
          ]
          return pid, sids

      def test_reserve_add_records_reservation(self):
          t = _Tmp()
          try:
              pid, (sid,) = self._phase(t, 1)
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{sid}",
                  resource_value="homepage-sort:15", scope="phase", note="hero band",
              )
              p = load_project(t.root / "docs/tasklist.json")
              res = p.phases[0].slices[0].reservations
              self.assertEqual(len(res), 1)
              self.assertEqual(res[0].resource, "homepage-sort")
              self.assertEqual(res[0].value, "15")
              self.assertEqual(res[0].scope, "phase")
              self.assertEqual(res[0].note, "hero band")
          finally:
              t.cleanup()

      def test_reserve_add_rejects_malformed_resource_value(self):
          t = _Tmp()
          try:
              pid, (sid,) = self._phase(t, 1)
              with self.assertRaises(commands.CommandError):
                  commands.cmd_reserve_add(
                      repo_root=t.root, slice_id=f"{pid}.{sid}",
                      resource_value="no-colon-here", scope="phase",
                  )
          finally:
              t.cleanup()
  ```
  Note `resource:value` splits on the **first** colon only, so `route-slug:/offers` parses to `("route-slug", "/offers")`.

### 4.2 Run — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_commands.py::ReserveCommandTests::test_reserve_add_records_reservation -q
  ```
  Expected: **FAIL** with `AttributeError: ... has no attribute 'cmd_reserve_add'`.

### 4.3 Implement parser helper + minimal `cmd_reserve_add`

- [ ] Add to `tools/tasktool/commands.py`. Import the S1 `Reservation` type at the top-of-file `from tasktool.model import (...)` block (add `Reservation` and `LedgerReservation` to the existing import list). Then:
  ```python
  def _parse_resource_value(raw: str) -> tuple[str, str]:
      """Split `<resource>:<value>` on the FIRST colon. Both halves must be non-empty."""
      if ":" not in raw:
          raise CommandError(
              f"reservation must be <resource>:<value>, got {raw!r}"
          )
      resource, value = raw.split(":", 1)
      resource, value = resource.strip(), value.strip()
      if not resource or not value:
          raise CommandError(
              f"reservation must be <resource>:<value> with non-empty halves, got {raw!r}"
          )
      return resource, value


  def cmd_reserve_add(
      *, repo_root: Path, slice_id: str, resource_value: str,
      scope: str = "phase", note: str | None = None,
      force: bool = False, reason: str | None = None,
  ) -> None:
      if scope not in ("phase", "project"):
          raise CommandError(f"reserve add: --scope must be phase or project, got {scope!r}")
      resource, value = _parse_resource_value(resource_value)
      with _write_context(repo_root) as write_root:
          p = _load(write_root)
          qid, item = _require_slice(p, slice_id, "reserve add")
          # (collision refusal added in Task 5; happy path only for now)
          item.reservations.append(
              Reservation(resource=resource, value=value, scope=scope, note=note)
          )
          _save(write_root, p)
  ```

### 4.4 Run — expect PASS

- [ ] Run:
  ```sh
  python -m pytest "tools/tasktool/tests/test_commands.py::ReserveCommandTests" -q
  ```
  Expected: **PASS** (2 passed).

### 4.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
  git commit -m "P7.S2: reserve add happy path + resource:value parsing"
  ```

---

## Task 5 — `reserve add` phase-scope collision refusal (incl. done slices)

### 5.1 Failing tests

- [ ] Add to `ReserveCommandTests`:
  ```python
      def test_reserve_add_refuses_phase_scope_collision(self):
          t = _Tmp()
          try:
              pid, (s0, s1) = self._phase(t, 2)
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s0}",
                  resource_value="homepage-sort:15", scope="phase",
              )
              with self.assertRaises(commands.CommandError) as cm:
                  commands.cmd_reserve_add(
                      repo_root=t.root, slice_id=f"{pid}.{s1}",
                      resource_value="homepage-sort:15", scope="phase",
                  )
              msg = str(cm.exception)
              self.assertIn("homepage-sort:15", msg)
              self.assertIn(f"{pid}.{s0}", msg)
          finally:
              t.cleanup()

      def test_reserve_add_collision_counts_done_holder(self):
          t = _Tmp()
          try:
              pid, (s0, s1) = self._phase(t, 2)
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s0}",
                  resource_value="homepage-sort:15", scope="phase",
              )
              commands.cmd_start(repo_root=t.root, id=f"{pid}.{s0}")
              commands.cmd_close(repo_root=t.root, id=f"{pid}.{s0}", skip_review_gate=True)
              # s0 is now done; the slot stays taken.
              with self.assertRaises(commands.CommandError):
                  commands.cmd_reserve_add(
                      repo_root=t.root, slice_id=f"{pid}.{s1}",
                      resource_value="homepage-sort:15", scope="phase",
                  )
          finally:
              t.cleanup()

      def test_reserve_add_ignores_cancelled_holder(self):
          t = _Tmp()
          try:
              pid, (s0, s1) = self._phase(t, 2)
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s0}",
                  resource_value="homepage-sort:15", scope="phase",
              )
              commands.cmd_cancel(repo_root=t.root, id=f"{pid}.{s0}", reason="dropped")
              # s0 cancelled → slot released → no refusal.
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s1}",
                  resource_value="homepage-sort:15", scope="phase",
              )
              p = load_project(t.root / "docs/tasklist.json")
              s1_row = next(s for s in p.phases[0].slices if s.id == s1)
              self.assertEqual(len(s1_row.reservations), 1)
          finally:
              t.cleanup()

      def test_reserve_add_same_slice_no_self_collision(self):
          t = _Tmp()
          try:
              pid, (s0,) = self._phase(t, 1)
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s0}",
                  resource_value="homepage-sort:15", scope="phase",
              )
              # Re-adding the SAME value to the SAME slice is idempotent, not a collision.
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s0}",
                  resource_value="homepage-sort:15", scope="phase",
              )
              p = load_project(t.root / "docs/tasklist.json")
              self.assertEqual(len(p.phases[0].slices[0].reservations), 1)
          finally:
              t.cleanup()

      def test_reserve_add_same_slice_phase_and_project_both_held(self):
          # Self-dedupe must key on (resource, value, scope): a slice may hold the
          # same resource:value at BOTH phase and project scope. Only the
          # project-scoped one is laddered (Task 9), so a scope-blind self-dedupe
          # would silently drop the reservation that must reach the ledger.
          t = _Tmp()
          try:
              pid, (s0,) = self._phase(t, 1)
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s0}",
                  resource_value="route-slug:/offers", scope="phase",
              )
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s0}",
                  resource_value="route-slug:/offers", scope="project",
              )
              p = load_project(t.root / "docs/tasklist.json")
              res = p.phases[0].slices[0].reservations
              scopes = sorted(r.scope for r in res if r.resource == "route-slug" and r.value == "/offers")
              self.assertEqual(scopes, ["phase", "project"])
          finally:
              t.cleanup()
  ```

### 5.2 Run — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_commands.py::ReserveCommandTests::test_reserve_add_refuses_phase_scope_collision -q
  ```
  Expected: **FAIL** — no `CommandError` is raised (the happy-path impl from Task 4 appends unconditionally), so `assertRaises` fails.

### 5.3 Implement phase-scope collision detection + self-dedupe

- [ ] Add the holder-lookup helper to `tools/tasktool/commands.py`:
  ```python
  def _phase_of_slice(p: Project, qid: str):
      """Return the Phase containing the qualified slice id `qid`."""
      phase_part, _slice_part, _ = split_qualified(qid)
      return next((ph for ph in p.phases if ph.id == phase_part), None)


  def _phase_scope_holder(p: Project, phase, reserving_qid: str, resource: str, value: str):
      """Return the qualified id of a non-cancelled slice in `phase` (other than the
      reserving slice) that already holds `resource:value`, or None. Done slices count."""
      for slc in phase.slices:
          slc_qid = f"{phase.id}.{slc.id}"
          if slc_qid == reserving_qid:
              continue
          if slc.status == Status.CANCELLED:
              continue
          for r in slc.reservations:
              if r.resource == resource and r.value == value:
                  return slc_qid
      return None
  ```

- [ ] Replace the placeholder comment in `cmd_reserve_add` (added in Task 4) so the body becomes:
  ```python
  with _write_context(repo_root) as write_root:
      p = _load(write_root)
      qid, item = _require_slice(p, slice_id, "reserve add")
      # Idempotent: the same slice re-declaring the SAME (resource, value, scope)
      # is a no-op. The scope MUST be part of the key — a slice may legitimately
      # hold the same resource:value at both phase and project scope (only the
      # project-scoped one is laddered), so a scope-blind check would wrongly
      # suppress the second add.
      if any(
          r.resource == resource and r.value == value and r.scope == scope
          for r in item.reservations
      ):
          return
      phase = _phase_of_slice(p, qid)
      holder = _phase_scope_holder(p, phase, qid, resource, value)
      # project-scope holder check is added in Task 6.
      if holder is not None and not force:
          raise CommandError(
              f"reserve add: {resource}:{value} is already reserved by {holder} "
              f"in phase {phase.id}; use --force --reason \"...\" to override"
          )
      if force:
          # --force handling (requires --reason) is added in Task 7.
          pass
      item.reservations.append(
          Reservation(resource=resource, value=value, scope=scope, note=note)
      )
      _save(write_root, p)
  ```
  (The `phase` variable will also drive the project-scope branch in Task 6. For phase scope, the holder check only consults `phase.slices`.)

### 5.4 Run — expect PASS

- [ ] Run:
  ```sh
  python -m pytest "tools/tasktool/tests/test_commands.py::ReserveCommandTests" -q
  ```
  Expected: **PASS** (7 passed: the 2 from Task 4 plus the 5 new). Note `test_reserve_add_same_slice_phase_and_project_both_held` passes already under the phase-scope-only implementation: the project-scoped add finds no phase-scope holder (the reserving slice is excluded from `_phase_scope_holder`) and appends, while the scope-aware self-dedupe lets the second add through.

### 5.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
  git commit -m "P7.S2: reserve add phase-scope collision refusal (incl. done, excl. cancelled)"
  ```

---

## Task 6 — `reserve add` project-scope refusal (active phases + ledger)

### 6.1 Failing tests

- [ ] Add to `ReserveCommandTests`. The first test crosses two **active** phases; the second seeds the `Project.reservations_ledger` directly (simulating an archived holder) and asserts the refusal names the ledger owner.
  ```python
      def test_reserve_add_project_scope_collides_across_active_phases(self):
          t = _Tmp()
          try:
              commands.cmd_init(repo_root=t.root, project="demo")
              p1 = commands.cmd_create_phase(repo_root=t.root, title="phase1")
              a = commands.cmd_create_slice(repo_root=t.root, phase_id=p1, title="a")
              p2 = commands.cmd_create_phase(repo_root=t.root, title="phase2")
              b = commands.cmd_create_slice(repo_root=t.root, phase_id=p2, title="b")
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{p1}.{a}",
                  resource_value="directus-collection:home_slider", scope="project",
              )
              with self.assertRaises(commands.CommandError) as cm:
                  commands.cmd_reserve_add(
                      repo_root=t.root, slice_id=f"{p2}.{b}",
                      resource_value="directus-collection:home_slider", scope="project",
                  )
              self.assertIn(f"{p1}.{a}", str(cm.exception))
          finally:
              t.cleanup()

      def test_reserve_add_project_scope_collides_with_ledger(self):
          t = _Tmp()
          try:
              commands.cmd_init(repo_root=t.root, project="demo")
              pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
              sid = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="s")
              # Seed an archived holder into the ledger directly.
              from tasktool.model import LedgerReservation
              from tasktool.serialize import load_project, save_project
              proj = load_project(t.root / "docs/tasklist.json")
              proj.reservations_ledger.append(LedgerReservation(
                  resource="route-slug", value="/offers", scope="project",
                  note=None, owner_id="P3.S4", owner_phase_id="P3",
                  archived_date="2026-05-01",
              ))
              save_project(proj, t.root / "docs/tasklist.json")
              with self.assertRaises(commands.CommandError) as cm:
                  commands.cmd_reserve_add(
                      repo_root=t.root, slice_id=f"{pid}.{sid}",
                      resource_value="route-slug:/offers", scope="project",
                  )
              msg = str(cm.exception)
              self.assertIn("route-slug:/offers", msg)
              self.assertIn("P3.S4", msg)
          finally:
              t.cleanup()

      def test_reserve_add_phase_scope_does_not_consult_ledger(self):
          t = _Tmp()
          try:
              commands.cmd_init(repo_root=t.root, project="demo")
              pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
              sid = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="s")
              from tasktool.model import LedgerReservation
              from tasktool.serialize import load_project, save_project
              proj = load_project(t.root / "docs/tasklist.json")
              proj.reservations_ledger.append(LedgerReservation(
                  resource="route-slug", value="/offers", scope="project",
                  note=None, owner_id="P3.S4", owner_phase_id="P3",
                  archived_date="2026-05-01",
              ))
              save_project(proj, t.root / "docs/tasklist.json")
              # phase-scope add of the same value must NOT be blocked by the project ledger.
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{sid}",
                  resource_value="route-slug:/offers", scope="phase",
              )
          finally:
              t.cleanup()
  ```

### 6.2 Run — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_commands.py::ReserveCommandTests::test_reserve_add_project_scope_collides_across_active_phases -q
  ```
  Expected: **FAIL** — the current `cmd_reserve_add` only checks `phase.slices`, so a cross-phase collision is not detected and no `CommandError` is raised.

### 6.3 Implement project-scope holder lookup

- [ ] Add to `tools/tasktool/commands.py`:
  ```python
  def _project_scope_holder(p: Project, reserving_qid: str, resource: str, value: str):
      """Return the holder id (qualified slice id, or a ledger owner descriptor) of a
      project-scoped `resource:value` collision, or None.

      Checks (a) every non-cancelled slice across ALL active phases except the
      reserving slice, then (b) `Project.reservations_ledger` (archived holders).
      A ledger match is reported via `_format_ledger_holder`."""
      for ph in p.phases:
          for slc in ph.slices:
              slc_qid = f"{ph.id}.{slc.id}"
              if slc_qid == reserving_qid:
                  continue
              if slc.status == Status.CANCELLED:
                  continue
              for r in slc.reservations:
                  if r.resource == resource and r.value == value:
                      return slc_qid
      for lr in p.reservations_ledger:
          if lr.resource == resource and lr.value == value:
              return _format_ledger_holder(lr)
      return None


  def _format_ledger_holder(lr) -> str:
      """Holder descriptor for a ledger entry, naming owner + archive date."""
      return f"{lr.owner_id} (archived {lr.archived_date} from phase {lr.owner_phase_id})"
  ```
  **Scope comparison rule (binding — matches spec §4.B; resolves the cross-phase open question).** A collision is computed on `resource:value` over the **holder set selected by the NEW reservation's scope**, NOT by the holder's own declared scope:
  - A **phase-scoped** add checks only its own phase's non-cancelled slices (`_phase_scope_holder`).
  - A **project-scoped** add checks every non-cancelled slice across **all active phases** plus the `reservations_ledger` (`_project_scope_holder`).
  - The holder's own declared scope does **not** filter the comparison. Two different phases both claiming `route-slug:/offers` IS a real collision under a project-scoped add, even if one holder declared it at phase scope. The match is therefore on `resource == ... and value == ...` only — never on `r.scope`. This is why `test_reserve_add_project_scope_collides_across_active_phases` (Task 6.1) asserts a project-scoped add collides with a same-value holder in a **different** phase.

- [ ] Update `cmd_reserve_add`'s holder resolution so scope drives which lookup runs. Replace the holder lines from Task 5 with:
  ```python
      phase = _phase_of_slice(p, qid)
      if scope == "project":
          holder = _project_scope_holder(p, qid, resource, value)
          holder_context = "project scope"
      else:
          holder = _phase_scope_holder(p, phase, qid, resource, value)
          holder_context = f"phase {phase.id}"
      if holder is not None and not force:
          raise CommandError(
              f"reserve add: {resource}:{value} is already reserved by {holder} "
              f"in {holder_context}; use --force --reason \"...\" to override"
          )
  ```
  (The phase-scope refusal message text changes slightly — update the Task 5 assertion only if it checked exact wording. It asserts `assertIn(f"{pid}.{s0}", msg)` and `assertIn("homepage-sort:15", msg)`, both of which still hold.)

### 6.4 Run — expect PASS

- [ ] Run:
  ```sh
  python -m pytest "tools/tasktool/tests/test_commands.py::ReserveCommandTests" -q
  ```
  Expected: **PASS** (10 passed).

### 6.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
  git commit -m "P7.S2: reserve add project-scope refusal (active phases + ledger)"
  ```

---

## Task 7 — `--force` override (requires `--reason`, mutates only reserving slice, override note)

### 7.1 Failing tests

- [ ] Add to `ReserveCommandTests`:
  ```python
      def test_force_requires_reason(self):
          t = _Tmp()
          try:
              pid, (s0, s1) = self._phase(t, 2)
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s0}",
                  resource_value="homepage-sort:15", scope="phase",
              )
              with self.assertRaises(commands.CommandError) as cm:
                  commands.cmd_reserve_add(
                      repo_root=t.root, slice_id=f"{pid}.{s1}",
                      resource_value="homepage-sort:15", scope="phase",
                      force=True,  # no reason
                  )
              self.assertIn("--reason", str(cm.exception))
          finally:
              t.cleanup()

      def test_force_with_reason_overrides_and_records_note(self):
          t = _Tmp()
          try:
              pid, (s0, s1) = self._phase(t, 2)
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s0}",
                  resource_value="homepage-sort:15", scope="phase",
              )
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s1}",
                  resource_value="homepage-sort:15", scope="phase",
                  force=True, reason="intentional shared band",
              )
              p = load_project(t.root / "docs/tasklist.json")
              s0_row = next(s for s in p.phases[0].slices if s.id == s0)
              s1_row = next(s for s in p.phases[0].slices if s.id == s1)
              # Reserving slice gained the reservation + an override note.
              self.assertEqual(len(s1_row.reservations), 1)
              self.assertIn("Reservation-override", s1_row.notes)
              self.assertIn("homepage-sort:15", s1_row.notes)
              self.assertIn(f"{pid}.{s0}", s1_row.notes)
              self.assertIn("intentional shared band", s1_row.notes)
              # Holder slice is NOT mutated.
              self.assertEqual(len(s0_row.reservations), 1)
              self.assertEqual(s0_row.notes, "")
          finally:
              t.cleanup()

      def test_force_without_collision_still_requires_reason(self):
          t = _Tmp()
          try:
              pid, (s0,) = self._phase(t, 1)
              with self.assertRaises(commands.CommandError):
                  commands.cmd_reserve_add(
                      repo_root=t.root, slice_id=f"{pid}.{s0}",
                      resource_value="homepage-sort:9", scope="phase",
                      force=True,  # force always requires reason
                  )
          finally:
              t.cleanup()
  ```

### 7.2 Run — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_commands.py::ReserveCommandTests::test_force_requires_reason -q
  ```
  Expected: **FAIL** — current code's `if force: pass` accepts force with no reason, so no `CommandError`.

### 7.3 Implement `--force` semantics

- [ ] This is the **final, complete** body of `cmd_reserve_add`'s `with` block. Replace everything from the scope-aware self-dedupe (added in Task 5) through `_save(...)` with the block below, so the last-shown code is correct and self-contained. **Do not drop the self-dedupe** — it must remain the first guard inside the block (regressing it breaks `test_reserve_add_same_slice_no_self_collision` and `test_reserve_add_same_slice_phase_and_project_both_held`):
  ```python
  with _write_context(repo_root) as write_root:
      p = _load(write_root)
      qid, item = _require_slice(p, slice_id, "reserve add")
      # Self-dedupe keyed on (resource, value, scope): re-declaring the same
      # tuple on the same slice is a no-op, but the SAME resource:value at a
      # DIFFERENT scope (phase vs project) is a distinct, allowed reservation.
      if any(
          r.resource == resource and r.value == value and r.scope == scope
          for r in item.reservations
      ):
          return
      phase = _phase_of_slice(p, qid)
      if scope == "project":
          holder = _project_scope_holder(p, qid, resource, value)
          holder_context = "project scope"
      else:
          holder = _phase_scope_holder(p, phase, qid, resource, value)
          holder_context = f"phase {phase.id}"
      if force:
          if reason is None or not reason.strip():
              raise CommandError("reserve add --force requires --reason \"...\"")
      elif holder is not None:
          raise CommandError(
              f"reserve add: {resource}:{value} is already reserved by {holder} "
              f"in {holder_context}; use --force --reason \"...\" to override"
          )
      item.reservations.append(
          Reservation(resource=resource, value=value, scope=scope, note=note)
      )
      if force and holder is not None:
          ts = _dt.datetime.now().isoformat(timespec="seconds")
          line = (
              f"Reservation-override {ts}: {resource}:{value} over {holder} "
              f"— {reason.strip()}"
          )
          item.notes = (item.notes + "\n" + line).strip() if item.notes else line
      _save(write_root, p)
  ```
  Key points enforced by this block, matching the spec:
  - The **scope-aware self-dedupe** from Task 5 is preserved verbatim as the first guard.
  - `--force` **always** requires `--reason` (even with no collision — see `test_force_without_collision_still_requires_reason`).
  - The override note is **only** appended when force overrode an actual collision (`holder is not None`); a forced non-colliding add records no override note (the reservation alone suffices).
  - **Only the reserving slice (`item`) is mutated** — the holder slice is never touched.
  - The note format is exactly `Reservation-override <ISO-ts>: <resource>:<value> over <holder-id> — <reason>`.

### 7.4 Run — expect PASS

- [ ] Run:
  ```sh
  python -m pytest "tools/tasktool/tests/test_commands.py::ReserveCommandTests" -q
  ```
  Expected: **PASS** (13 passed).

### 7.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
  git commit -m "P7.S2: reserve add --force --reason override + override note"
  ```

---

## Task 8 — `reserve remove` and `reserve list`

### 8.1 Failing tests

- [ ] Add to `ReserveCommandTests`:
  ```python
      def test_reserve_remove_drops_matching(self):
          t = _Tmp()
          try:
              pid, (s0,) = self._phase(t, 1)
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s0}",
                  resource_value="homepage-sort:15", scope="phase",
              )
              commands.cmd_reserve_remove(
                  repo_root=t.root, slice_id=f"{pid}.{s0}",
                  resource_value="homepage-sort:15",
              )
              p = load_project(t.root / "docs/tasklist.json")
              self.assertEqual(p.phases[0].slices[0].reservations, [])
          finally:
              t.cleanup()

      def test_reserve_remove_releases_slot_for_sibling(self):
          t = _Tmp()
          try:
              pid, (s0, s1) = self._phase(t, 2)
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s0}",
                  resource_value="homepage-sort:15", scope="phase",
              )
              commands.cmd_reserve_remove(
                  repo_root=t.root, slice_id=f"{pid}.{s0}",
                  resource_value="homepage-sort:15",
              )
              # slot freed → sibling may now claim it
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s1}",
                  resource_value="homepage-sort:15", scope="phase",
              )
          finally:
              t.cleanup()

      def test_reserve_list_renders(self):
          t = _Tmp()
          try:
              pid, (s0,) = self._phase(t, 1)
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s0}",
                  resource_value="homepage-sort:15", scope="phase",
              )
              out = commands.cmd_reserve_list(repo_root=t.root, phase_id=pid)
              self.assertIn(f"{pid}.{s0}", out)
              self.assertIn("homepage-sort:15", out)
              self.assertIn("phase", out)
          finally:
              t.cleanup()

      def test_reserve_add_refuses_cancelled_slice(self):
          t = _Tmp()
          try:
              pid, (s0,) = self._phase(t, 1)
              commands.cmd_cancel(repo_root=t.root, id=f"{pid}.{s0}", reason="dropped")
              with self.assertRaises(commands.CommandError):
                  commands.cmd_reserve_add(
                      repo_root=t.root, slice_id=f"{pid}.{s0}",
                      resource_value="homepage-sort:15", scope="phase",
                  )
          finally:
              t.cleanup()

      def test_reserve_remove_refuses_cancelled_slice(self):
          t = _Tmp()
          try:
              pid, (s0,) = self._phase(t, 1)
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s0}",
                  resource_value="homepage-sort:15", scope="phase",
              )
              commands.cmd_cancel(repo_root=t.root, id=f"{pid}.{s0}", reason="dropped")
              with self.assertRaises(commands.CommandError):
                  commands.cmd_reserve_remove(
                      repo_root=t.root, slice_id=f"{pid}.{s0}",
                      resource_value="homepage-sort:15",
                  )
          finally:
              t.cleanup()
  ```

### 8.2 Run — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_commands.py::ReserveCommandTests::test_reserve_remove_drops_matching -q
  ```
  Expected: **FAIL** with `AttributeError: ... has no attribute 'cmd_reserve_remove'`.

### 8.3 Implement `cmd_reserve_remove` and `cmd_reserve_list`

- [ ] Add to `tools/tasktool/commands.py`:
  ```python
  def cmd_reserve_remove(*, repo_root: Path, slice_id: str, resource_value: str) -> None:
      resource, value = _parse_resource_value(resource_value)
      with _write_context(repo_root) as write_root:
          p = _load(write_root)
          _qid, item = _require_slice(p, slice_id, "reserve remove")
          item.reservations = [
              r for r in item.reservations
              if not (r.resource == resource and r.value == value)
          ]
          _save(write_root, p)


  def cmd_reserve_list(*, repo_root: Path, phase_id: str | None) -> str:
      with _read_context(repo_root) as write_root:
          p = _load(write_root)
          if phase_id is not None and not any(ph.id == phase_id for ph in p.phases):
              raise CommandError(f"phase {phase_id} not found")
          lines: list[str] = []
          for ph, slc in _iter_phase_slices(p, phase_id):
              for r in slc.reservations:
                  note = f"  — {r.note}" if r.note else ""
                  lines.append(f"{ph.id}.{slc.id}  {r.resource}:{r.value}  [{r.scope}]{note}")
          if not lines:
              return "(no reservations)\n"
          return "\n".join(lines) + "\n"
  ```

### 8.4 Run — expect PASS

- [ ] Run:
  ```sh
  python -m pytest "tools/tasktool/tests/test_commands.py::ReserveCommandTests" -q
  ```
  Expected: **PASS** (18 passed). The two cancelled-slice tests pass without new impl — `_require_slice` already calls `_refuse_if_cancelled`.

### 8.5 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
  git commit -m "P7.S2: reserve remove + reserve list"
  ```

---

## Task 9 — Ledger population on `archive-phase` (dedupe + cancelled-exclusion + idempotency)

### 9.1 Failing tests

- [ ] Add a new test class to `tools/tasktool/tests/test_commands.py`:
  ```python
  class LedgerPopulationTests(unittest.TestCase):
      def _archive_ready(self, t, pid, sid, *, cancel=False):
          if cancel:
              commands.cmd_cancel(repo_root=t.root, id=f"{pid}.{sid}", reason="dropped")
          else:
              commands.cmd_start(repo_root=t.root, id=f"{pid}.{sid}")
              commands.cmd_close(repo_root=t.root, id=f"{pid}.{sid}", skip_review_gate=True)

      def test_archive_phase_ladders_project_reservations_from_done_slices(self):
          t = _Tmp()
          try:
              commands.cmd_init(repo_root=t.root, project="demo")
              pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
              sid = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="s")
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{sid}",
                  resource_value="route-slug:/offers", scope="project",
              )
              # phase-scoped reservation must NOT be laddered
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{sid}",
                  resource_value="homepage-sort:15", scope="phase",
              )
              self._archive_ready(t, pid, sid)
              commands.cmd_archive_phase(repo_root=t.root, phase_id=pid, skip_review_gate=True)
              p = load_project(t.root / "docs/tasklist.json")
              ledger = p.reservations_ledger
              self.assertEqual(len(ledger), 1)
              lr = ledger[0]
              self.assertEqual((lr.resource, lr.value, lr.scope), ("route-slug", "/offers", "project"))
              self.assertEqual(lr.owner_id, f"{pid}.{sid}")
              self.assertEqual(lr.owner_phase_id, pid)
              self.assertTrue(lr.archived_date)
          finally:
              t.cleanup()

      def test_archive_phase_excludes_cancelled_slice_reservations(self):
          t = _Tmp()
          try:
              commands.cmd_init(repo_root=t.root, project="demo")
              pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
              s_done = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="done")
              s_cx = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="cancelled")
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s_done}",
                  resource_value="route-slug:/a", scope="project",
              )
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{s_cx}",
                  resource_value="route-slug:/b", scope="project",
              )
              self._archive_ready(t, pid, s_cx, cancel=True)
              self._archive_ready(t, pid, s_done)
              commands.cmd_archive_phase(repo_root=t.root, phase_id=pid, skip_review_gate=True)
              p = load_project(t.root / "docs/tasklist.json")
              values = {(lr.resource, lr.value) for lr in p.reservations_ledger}
              self.assertEqual(values, {("route-slug", "/a")})
          finally:
              t.cleanup()

      def test_archive_phase_dedupes_on_resource_value_scope_owner(self):
          t = _Tmp()
          try:
              commands.cmd_init(repo_root=t.root, project="demo")
              pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
              a = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="a")
              b = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="b")
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{a}",
                  resource_value="cache-tag:home", scope="project",
              )
              # b force-shares the same project value → two distinct owners
              commands.cmd_reserve_add(
                  repo_root=t.root, slice_id=f"{pid}.{b}",
                  resource_value="cache-tag:home", scope="project",
                  force=True, reason="shared cache tag",
              )
              self._archive_ready(t, pid, a)
              self._archive_ready(t, pid, b)
              commands.cmd_archive_phase(repo_root=t.root, phase_id=pid, skip_review_gate=True)
              p = load_project(t.root / "docs/tasklist.json")
              owners = sorted(lr.owner_id for lr in p.reservations_ledger)
              self.assertEqual(owners, sorted([f"{pid}.{a}", f"{pid}.{b}"]))
              self.assertEqual(len(p.reservations_ledger), 2)
          finally:
              t.cleanup()
  ```
  - For idempotent re-archive: archiving a phase removes it from `p.phases`, so a second `archive-phase` on the same id raises "phase not found" — re-archive of the *same phase row* cannot recur through the normal path. The idempotency the spec requires is **dedupe-on-key when the same owner reservation would be added twice**. Cover it with a unit test that calls the population helper directly:
  ```python
      def test_ledger_population_helper_is_idempotent_on_repeat(self):
          from tasktool.commands import _ladder_project_reservations
          from tasktool.model import Project, Phase, Slice, Reservation, Status
          proj = Project(project="demo")
          slc = Slice(id="S1", title="s", created="2026-06-02", status=Status.DONE)
          slc.reservations.append(Reservation(resource="route-slug", value="/x", scope="project", note=None))
          phase = Phase(id="P1", title="p", created="2026-06-02")
          phase.slices.append(slc)
          _ladder_project_reservations(proj, phase, archived_date="2026-06-02")
          _ladder_project_reservations(proj, phase, archived_date="2026-06-02")
          self.assertEqual(len(proj.reservations_ledger), 1)
  ```

### 9.2 Run — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_commands.py::LedgerPopulationTests::test_archive_phase_ladders_project_reservations_from_done_slices -q
  ```
  Expected: **FAIL** — `archive-phase` does not yet populate the ledger, so `p.reservations_ledger` is empty and `assertEqual(len(ledger), 1)` fails.

### 9.3 Implement the ladder helper

- [ ] Add to `tools/tasktool/commands.py` (near the other P7.S2 helpers). Ensure `LedgerReservation` is imported at the top (added in Task 4):
  ```python
  def _ladder_project_reservations(p: Project, phase, *, archived_date: str) -> None:
      """Append project-scoped reservations from the phase's NON-CANCELLED (done) slices
      to `Project.reservations_ledger` as LedgerReservations.

      Deduped on (resource, value, scope, owner_id): re-running is idempotent (same owner
      ⇒ same key), and two distinct done slices that --force-shared a value both survive.
      Cancelled slices contribute nothing."""
      existing = {
          (lr.resource, lr.value, lr.scope, lr.owner_id)
          for lr in p.reservations_ledger
      }
      for slc in phase.slices:
          if slc.status == Status.CANCELLED:
              continue
          owner_id = f"{phase.id}.{slc.id}"
          for r in slc.reservations:
              if r.scope != "project":
                  continue
              key = (r.resource, r.value, r.scope, owner_id)
              if key in existing:
                  continue
              existing.add(key)
              p.reservations_ledger.append(LedgerReservation(
                  resource=r.resource, value=r.value, scope=r.scope, note=r.note,
                  owner_id=owner_id, owner_phase_id=phase.id, archived_date=archived_date,
              ))
  ```

### 9.4 Hook it into `_cmd_archive_phase_at_root`

- [ ] In `_cmd_archive_phase_at_root`, the ledger must be populated **before** the phase is removed from `p.phases` and **before** `validate_project(p)`. Insert the call immediately after the `phase.closed = phase.closed or _today()` lines and before the archive-content build (around line 2098, just before `slug = _slugify(phase.title)`):
  ```python
      _ladder_project_reservations(p, phase, archived_date=_today())
  ```
  This runs while `phase` still references the live phase object and its slices' reservations, and `p.reservations_ledger` is the project the rest of the function will `_save`.

### 9.5 Run — expect PASS

- [ ] Run:
  ```sh
  python -m pytest "tools/tasktool/tests/test_commands.py::LedgerPopulationTests" -q
  ```
  Expected: **PASS** (4 passed).

### 9.6 Run the full archive-phase suite to confirm no regressions

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_commands.py -q -k "archive_phase or Ledger or Reserve or Surface or Coordinate"
  ```
  Expected: **PASS** (all selected tests green).

### 9.7 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
  git commit -m "P7.S2: ledger population on archive-phase (dedupe, exclude cancelled)"
  ```

---

## Task 10 — Wire `surface` / `reserve` / `coordinate` into the CLI (argparse + dispatch)

### 10.1 Failing CLI integration tests

- [ ] Add to `tools/tasktool/tests/test_cli_integration.py` a new test class (uses the existing `_CliTmp` + `run_cli` helpers):
  ```python
  class SurfaceReserveCoordinateCliTests(unittest.TestCase):
      def _phase_with_slices(self, t, n):
          self.assertEqual(run_cli("init", "--project", "demo", cwd=t.root).returncode, 0)
          self.assertEqual(run_cli("create", "phase", "--title", "P", cwd=t.root).returncode, 0)
          for _ in range(n):
              self.assertEqual(run_cli("create", "slice", "P1", "--title", "s", cwd=t.root).returncode, 0)

      def test_surface_add_and_list_via_cli(self):
          t = _CliTmp()
          try:
              self._phase_with_slices(t, 1)
              r = run_cli("surface", "add", "P1.S1", "cms-block-registry", "directus-schema", cwd=t.root)
              self.assertEqual(r.returncode, 0, r.stderr)
              r = run_cli("surface", "list", "P1", cwd=t.root)
              self.assertEqual(r.returncode, 0, r.stderr)
              self.assertIn("cms-block-registry", r.stdout)
          finally:
              t.cleanup()

      def test_reserve_collision_exits_nonzero(self):
          t = _CliTmp()
          try:
              self._phase_with_slices(t, 2)
              r = run_cli("reserve", "add", "P1.S1", "homepage-sort:15", cwd=t.root)
              self.assertEqual(r.returncode, 0, r.stderr)
              r = run_cli("reserve", "add", "P1.S2", "homepage-sort:15", cwd=t.root)
              self.assertNotEqual(r.returncode, 0)
              self.assertIn("homepage-sort:15", r.stderr)
              self.assertIn("P1.S1", r.stderr)
          finally:
              t.cleanup()

      def test_force_without_reason_exits_nonzero(self):
          t = _CliTmp()
          try:
              self._phase_with_slices(t, 2)
              run_cli("reserve", "add", "P1.S1", "homepage-sort:15", cwd=t.root)
              r = run_cli("reserve", "add", "P1.S2", "homepage-sort:15", "--force", cwd=t.root)
              self.assertNotEqual(r.returncode, 0)
          finally:
              t.cleanup()

      def test_force_with_reason_succeeds_via_cli(self):
          t = _CliTmp()
          try:
              self._phase_with_slices(t, 2)
              run_cli("reserve", "add", "P1.S1", "homepage-sort:15", cwd=t.root)
              r = run_cli(
                  "reserve", "add", "P1.S2", "homepage-sort:15",
                  "--force", "--reason", "shared band", cwd=t.root,
              )
              self.assertEqual(r.returncode, 0, r.stderr)
          finally:
              t.cleanup()

      def test_coordinate_set_and_clear_via_cli(self):
          t = _CliTmp()
          try:
              self._phase_with_slices(t, 1)
              self.assertEqual(run_cli("coordinate", "P1.S1", "--group", "cms", cwd=t.root).returncode, 0)
              self.assertEqual(run_cli("coordinate", "P1.S1", "--clear", cwd=t.root).returncode, 0)
          finally:
              t.cleanup()
  ```

### 10.2 Run — expect FAIL

- [ ] Run:
  ```sh
  python -m pytest tools/tasktool/tests/test_cli_integration.py::SurfaceReserveCoordinateCliTests::test_surface_add_and_list_via_cli -q
  ```
  Expected: **FAIL** — `surface` is not a known subcommand, so `run_cli` exits 2 and `assertEqual(r.returncode, 0)` fails.

### 10.3 Add argparse subparsers

- [ ] In `tools/tasktool/cli.py`, inside `_build_parser()`, after the `p_ratify` block (around line 183), add:
  ```python
      # ── surface (P7.S2) ──
      p_surface = sub.add_parser("surface")
      surface_sub = p_surface.add_subparsers(dest="surface_cmd", required=True)
      p_surface_add = surface_sub.add_parser("add")
      p_surface_add.add_argument("slice_id")
      p_surface_add.add_argument("surfaces", nargs="+")
      p_surface_remove = surface_sub.add_parser("remove")
      p_surface_remove.add_argument("slice_id")
      p_surface_remove.add_argument("surface")
      p_surface_list = surface_sub.add_parser("list")
      p_surface_list.add_argument("phase_id", nargs="?")

      # ── reserve (P7.S2) ──
      p_reserve = sub.add_parser("reserve")
      reserve_sub = p_reserve.add_subparsers(dest="reserve_cmd", required=True)
      p_reserve_add = reserve_sub.add_parser("add")
      p_reserve_add.add_argument("slice_id")
      p_reserve_add.add_argument("resource_value", metavar="resource:value")
      p_reserve_add.add_argument("--scope", choices=["phase", "project"], default="phase")
      p_reserve_add.add_argument("--note")
      p_reserve_add.add_argument("--force", action="store_true")
      p_reserve_add.add_argument("--reason")
      p_reserve_remove = reserve_sub.add_parser("remove")
      p_reserve_remove.add_argument("slice_id")
      p_reserve_remove.add_argument("resource_value", metavar="resource:value")
      p_reserve_list = reserve_sub.add_parser("list")
      p_reserve_list.add_argument("phase_id", nargs="?")

      # ── coordinate (P7.S2) ──
      p_coordinate = sub.add_parser("coordinate")
      p_coordinate.add_argument("slice_id")
      coord_excl = p_coordinate.add_mutually_exclusive_group(required=True)
      coord_excl.add_argument("--group")
      coord_excl.add_argument("--clear", action="store_true")
  ```

### 10.4 Add dispatch branches

- [ ] In `tools/tasktool/cli.py`, inside `main()`, after the `elif args.cmd == "ratify":` block (around line 441), add:
  ```python
          elif args.cmd == "surface":
              if args.surface_cmd == "add":
                  commands.cmd_surface_add(
                      repo_root=root, slice_id=args.slice_id, surfaces=args.surfaces,
                  )
              elif args.surface_cmd == "remove":
                  commands.cmd_surface_remove(
                      repo_root=root, slice_id=args.slice_id, surface=args.surface,
                  )
              elif args.surface_cmd == "list":
                  sys.stdout.write(commands.cmd_surface_list(
                      repo_root=root, phase_id=args.phase_id,
                  ))
          elif args.cmd == "reserve":
              if args.reserve_cmd == "add":
                  commands.cmd_reserve_add(
                      repo_root=root, slice_id=args.slice_id,
                      resource_value=args.resource_value, scope=args.scope,
                      note=args.note, force=args.force, reason=args.reason,
                  )
              elif args.reserve_cmd == "remove":
                  commands.cmd_reserve_remove(
                      repo_root=root, slice_id=args.slice_id,
                      resource_value=args.resource_value,
                  )
              elif args.reserve_cmd == "list":
                  sys.stdout.write(commands.cmd_reserve_list(
                      repo_root=root, phase_id=args.phase_id,
                  ))
          elif args.cmd == "coordinate":
              commands.cmd_coordinate(
                  repo_root=root, slice_id=args.slice_id,
                  group=args.group, clear=args.clear,
              )
  ```
  Note: `args.surfaces`, `args.phase_id` (with `nargs="?"` → `None` when omitted), `args.scope`, etc. all resolve from the parser above. The `coordinate` mutually-exclusive group is `required=True`, so argparse rejects "neither --group nor --clear" with exit 2 before reaching `cmd_coordinate`; the command-level `CommandError` guard remains as defense in depth for direct Python callers.

### 10.5 Run — expect PASS

- [ ] Run:
  ```sh
  python -m pytest "tools/tasktool/tests/test_cli_integration.py::SurfaceReserveCoordinateCliTests" -q
  ```
  Expected: **PASS** (5 passed).

### 10.6 Commit

- [ ] Run:
  ```sh
  git add tools/tasktool/cli.py tools/tasktool/tests/test_cli_integration.py
  git commit -m "P7.S2: wire surface/reserve/coordinate into CLI"
  ```

---

## Task 11 — Full-suite verification + slice close

### 11.1 Run the focused command + CLI suites, then the entire tasktool suite

- [ ] First run the two files this slice changed (matches the reviewer's post-edit gate):
  ```sh
  python -m pytest tools/tasktool/tests/test_commands.py -q tools/tasktool/tests/test_cli_integration.py -q
  ```
  Expected: **all pass**.
- [ ] Then run the entire tasktool suite, from the repo root:
  ```sh
  python -m pytest tools/tasktool/tests -q
  ```
  Expected: **all pass**. Pay attention to `test_serialize.py`, `test_v1_compat.py`, and `test_migrate.py` — if any fail, the cause is almost certainly an S1 gap (the new fields must round-trip and be omitted-when-default). Surface-related serialization belongs to S1; if a serialize test fails purely on the new fields, confirm S1 is fully merged before debugging here.

### 11.2 Run the whole project test suite (catch cross-cutting regressions)

- [ ] Run:
  ```sh
  python -m pytest -q
  ```
  Expected: **all pass** (the repo's `testpaths` cover `scripts/tests`, `tools/tasktool/tests`, `skills/external-review/tests`).

### 11.3 Manual CLI smoke (evidence for the post-slice review)

- [ ] Exercise the refusal path entirely inside a **throwaway directory** — never against the real `docs/tasklist.json`. The repo-root wrapper `./tools/tasktool/tasktool` works from any cwd via cwd resolution or `--project-root`; here we point it at a temp project created from scratch. Run, capturing exit codes (`TT` is the absolute path to the wrapper):
  ```sh
  TT="$PWD/tools/tasktool/tasktool"
  SCRATCH="$(mktemp -d)"
  mkdir -p "$SCRATCH/docs"
  ( cd "$SCRATCH" \
    && "$TT" config init-local \
    && "$TT" init --project smoke \
    && "$TT" create phase --title "Smoke" \
    && "$TT" create slice P1 --title "a" \
    && "$TT" create slice P1 --title "b" \
    && echo "--- clean add (expect exit=0) ---" \
    && "$TT" reserve add P1.S1 homepage-sort:15 --scope phase; echo "exit=$?" \
    && echo "--- colliding add (expect refusal + exit=1) ---"; \
    "$TT" reserve add P1.S2 homepage-sort:15 --scope phase; echo "exit=$?" )
  rm -rf "$SCRATCH"
  ```
  Expected: the clean add on `P1.S1` prints `exit=0`; the colliding add on `P1.S2` prints a `tasktool: reserve add: homepage-sort:15 is already reserved by P1.S1 ...` refusal on stderr and `exit=1`. The temp dir is deleted afterward, so the real tracker is never touched.

### 11.4 Close the slice

- [ ] Hand off to `superstar:external-review --kind post-slice` per the project workflow, then once the verdict is `ready` / `ready with small edits`, close:
  ```sh
  ./tools/tasktool/tasktool close P7.S2
  ```
  (Do **not** run a version bump or plugin re-sync here — those happen at phase close per the repo release policy.)

---

## Edge cases & invariants checklist (verify each is covered by a test above)

- [ ] `surface add` dedupes and preserves insertion order (Task 1).
- [ ] `surface`/`coordinate` never refuse on collision — they are declaration-only (Tasks 1, 3).
- [ ] Mutating a **cancelled** slice is refused for **every** command via the shared `_require_slice` guard, with a direct test for each: `surface add` (Task 1, `test_surface_add_refuses_cancelled_slice`), `reserve add` + `reserve remove` (Task 8, `test_reserve_add_refuses_cancelled_slice` / `test_reserve_remove_refuses_cancelled_slice`), and `coordinate` (Task 3, `test_coordinate_refuses_cancelled_slice`).
- [ ] `reserve add` parses `<resource>:<value>` on the **first** colon; rejects missing/empty halves (Task 4).
- [ ] Self-dedupe keys on `(resource, value, scope)`: a slice may hold the same `resource:value` at BOTH phase and project scope, and only the project-scoped one is laddered (Task 5, `test_reserve_add_same_slice_phase_and_project_both_held`; reinforced in the final Task 7 block).
- [ ] Phase-scope refusal counts **done** holders, ignores **cancelled** holders, and never self-collides on the reserving slice (Task 5).
- [ ] Phase-scope refusal does **not** consult the project ledger (Task 6, `test_reserve_add_phase_scope_does_not_consult_ledger`).
- [ ] Project-scope refusal checks all active phases **and** the ledger, and the message names the ledger owner (Task 6).
- [ ] `--force` requires `--reason` always; refused without it; mutates **only** the reserving slice; records the exact `Reservation-override <ts>: <resource>:<value> over <holder-id> — <reason>` note; holder slice untouched (Task 7).
- [ ] `reserve remove` releases the slot so a sibling may reclaim it (Task 8).
- [ ] Ledger population on `archive-phase`: only project-scoped, only non-cancelled (done) slices, owner metadata stamped, phase-scoped reservations excluded (Task 9).
- [ ] Ledger dedupe keyed on `(resource, value, scope, owner_id)` — two `--force`-shared owners both survive; re-running the helper is idempotent (Task 9).
- [ ] Collision refusal exits **non-zero** via the CLI; `--force` without `--reason` exits non-zero; clean add exits zero (Task 10).
