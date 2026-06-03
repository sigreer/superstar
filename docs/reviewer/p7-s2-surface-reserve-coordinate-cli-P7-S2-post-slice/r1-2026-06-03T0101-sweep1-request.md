<!-- superstar-prompt:start -->
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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-p7-s2-surface-reserve-coordinate-cli

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-02-P7-S2-surface-reserve-coordinate-cli.md

Additional context files:
- docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md
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

### docs/plans/2026-06-02-P7-S2-surface-reserve-coordinate-cli.md

    1	# P7.S2 — surface / reserve / coordinate CLI Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Add the `tasktool surface`, `tasktool reserve`, and `tasktool coordinate` declaration commands plus reservation-collision refusal (phase + project scope), `--force --reason` override, and `archive-phase` ledger population, so planners can declare integration surfaces and hard-block duplicate scarce-resource allocations at planning time.
    6	
    7	**Architecture:** New command functions live in `tools/tasktool/commands.py` (declaration/mutation logic, refusal logic, ledger population), wired into argparse subparsers + dispatch in `tools/tasktool/cli.py`. They reuse the existing `_write_context`/`_load`/`_save` transaction helpers, `_find_item` for ID resolution, `_refuse_if_cancelled`, and `_dt`/`_today` for note timestamps. Ledger population hooks into the existing `_cmd_archive_phase_at_root`. All reads/writes operate on the S1 dataclasses (`Slice.integration_surfaces`, `Slice.reservations`, `Slice.coordination_group`, `Project.reservations_ledger`, the `Reservation` and `LedgerReservation` types).
    8	
    9	**Tech Stack:** Python 3, argparse, pytest
   10	
   11	---
   12	
   13	## Scheduling
   14	
   15	- **This slice is `P7.S2`.** It `depends_on` `P7.S1` (the schema-v3 data model: the `Slice.integration_surfaces` / `Slice.reservations` / `Slice.coordination_group` fields, the `Reservation` and `LedgerReservation` dataclasses, and `Project.reservations_ledger`). It **must not start before S1's fields exist** — every task here reads or writes those fields. If you open `tools/tasktool/model.py` and it still has `SCHEMA_VERSION = 2` with no `integration_surfaces` field on `Slice`, **stop**: S1 is not merged. Do not stub the model in this slice.
   16	- **This slice blocks `P7.S3`** (scheduling overlap detection reads the surfaces/reservations/coordination_group this slice writes) **and `P7.S6`** (skill docs that document these commands).
   17	- It shares **no** integration surface with `P7.S4` (`cli`/`commands` here vs `worktree` there); the two are genuinely parallel once S1 lands.
   18	- **Surfaces this slice writes:** `cli`, `commands`. **Reservations:** none.
   19	
   20	### First action before any source edit
   21	
   22	- [ ] Run, from the repo root `/home/simon/Dev/sigreer/skills/superstar`:
   23	  ```sh
   24	  ./tools/tasktool/tasktool start P7.S2
   25	  ```
   26	  This creates/records the worktree and flips `P7.S2` to `in_progress`. `cd` into the printed worktree path and do all subsequent work there. (If the project is configured local-mode and the command prints `cd <path>`, follow it.)
   27	
   28	---
   29	
   30	## File Structure
   31	
   32	| File | Responsibility (in this slice) |
   33	|------|-------------------------------|
   34	| `tools/tasktool/commands.py` | New command functions: `cmd_surface_add`, `cmd_surface_remove`, `cmd_surface_list`, `cmd_reserve_add`, `cmd_reserve_remove`, `cmd_reserve_list`, `cmd_coordinate`. New private helpers: `_parse_resource_value`, `_iter_phase_slices`, `_phase_scope_holder`, `_project_scope_holder`, `_format_ledger_holder`. New ledger-population block inside `_cmd_archive_phase_at_root`. |
   35	| `tools/tasktool/cli.py` | New `surface`, `reserve`, `coordinate` subparsers (with their sub-subcommands and flags) + dispatch branches in `main()` that call the new command functions. |
   36	| `tools/tasktool/tests/test_commands.py` | Unit tests calling the command functions directly (matches the file's `_Tmp` + `load_project` style). Covers surface add/remove/list, reserve add/remove/list, refusal (phase scope incl. done slices, project scope incl. ledger), `--force`/`--reason`, override note, coordinate set/clear, ledger population/dedupe/cancelled-exclusion/idempotent re-archive. |
   37	| `tools/tasktool/tests/test_cli_integration.py` | End-to-end CLI tests via `run_cli(...)` asserting exit codes (refusal exits non-zero; `--force` without `--reason` exits non-zero) and stdout/stderr text. |
   38	
   39	**Source of truth is `tools/tasktool/`.** Do NOT edit the `plugins/superstar/` copy — it is synced at release. Every path below is relative to the repo root unless noted.
   40	
   41	---
   42	
   43	## Conventions you will reuse (read once before starting)
   44	
   45	These already exist in `tools/tasktool/commands.py`; the new commands must follow them exactly.
   46	
   47	- **Transaction wrapper:** every mutating command is `with _write_context(repo_root) as write_root:` → `p = _load(write_root)` → mutate → `_save(write_root, p)`. Read-only commands (the `*_list` ones) use `with _read_context(repo_root) as write_root:` → `p = _load(write_root)` → build string → return.
   48	- **ID resolution:** `qid, _container, item = _find_item(p, slice_id)`. After resolution, guard the kind with `if parse_id(qid)[0] != "slice": raise CommandError(...)` (see `cmd_deps`, `cmd_ratify`).
   49	- **Cancelled guard:** mutating a row → `_refuse_if_cancelled(qid, item, "<verb>")`.
   50	- **Errors:** raise `CommandError("...")`. `cli.main()` already catches `CommandError`, prints `tasktool: <msg>` to stderr, and returns exit code 1. Argparse usage errors exit 2.
   51	- **Timestamped notes:** `ts = _dt.datetime.now().isoformat(timespec="seconds")` then append `item.notes = (item.notes + "\n" + line).strip() if item.notes else line` (see `_apply_ready_close_override`).
   52	- **Listing rows of a phase:** iterate `phase.slices`; phase lookup is `phase = next((ph for ph in p.phases if ph.id == phase_id), None)`.
   53	- **Test invocation:** from repo root, run a single test file with
   54	  ```sh
   55	  python -m pytest tools/tasktool/tests/test_commands.py -q
   56	  ```
   57	  (`pyproject.toml` sets `addopts = "--import-mode=importlib"`; `testpaths` includes `tools/tasktool/tests`.) Tests import `from tasktool import commands` — the package resolves because pytest runs from repo root with `tools/` on the path via the wrapper; if an import fails, run with `PYTHONPATH=tools python -m pytest ...`.
   58	
   59	---
   60	
   61	## Task 1 — `surface add` / `surface remove` (declaration only)
   62	
   63	### 1.1 Failing test for `surface add`
   64	
   65	- [ ] Add to `tools/tasktool/tests/test_commands.py` a new test class near the other declaration tests:
   66	  ```python
   67	  class SurfaceCommandTests(unittest.TestCase):
   68	      def _setup_phase_with_slice(self, t):
   69	          commands.cmd_init(repo_root=t.root, project="demo")
   70	          pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
   71	          sid = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="slice")
   72	          return pid, sid
   73	
   74	      def test_surface_add_appends_unique_sorted(self):
   75	          t = _Tmp()
   76	          try:
   77	              pid, sid = self._setup_phase_with_slice(t)
   78	              commands.cmd_surface_add(
   79	                  repo_root=t.root, slice_id=f"{pid}.{sid}",
   80	                  surfaces=["cms-block-registry", "directus-schema", "cms-block-registry"],
   81	              )
   82	              p = load_project(t.root / "docs/tasklist.json")
   83	              slc = p.phases[0].slices[0]
   84	              self.assertEqual(slc.integration_surfaces, ["cms-block-registry", "directus-schema"])
   85	          finally:
   86	              t.cleanup()
   87	  ```
   88	
   89	### 1.2 Run it — expect FAIL
   90	
   91	- [ ] Run:
   92	  ```sh
   93	  python -m pytest tools/tasktool/tests/test_commands.py::SurfaceCommandTests::test_surface_add_appends_unique_sorted -q
   94	  ```
   95	  Expected: **FAIL** with `AttributeError: module 'tasktool.commands' has no attribute 'cmd_surface_add'`.
   96	
   97	### 1.3 Implement `cmd_surface_add` and `cmd_surface_remove`
   98	
   99	- [ ] Add to `tools/tasktool/commands.py` after `cmd_ratify` (around line 1320), a new section:
  100	  ```python
  101	  # ───── surface / reserve / coordinate (P7.S2) ─────
  102	
  103	  def _require_slice(p: Project, slice_id: str, verb: str):
  104	      """Resolve `slice_id` to a slice row, refusing non-slice ids and cancelled rows.
  105	      Returns (qid, item)."""
  106	      qid, _container, item = _find_item(p, slice_id)
  107	      if parse_id(qid)[0] != "slice":
  108	          raise CommandError(f"{verb} only works on slices; {qid} is a {parse_id(qid)[0]}")
  109	      _refuse_if_cancelled(qid, item, verb)
  110	      return qid, item
  111	
  112	
  113	  def cmd_surface_add(*, repo_root: Path, slice_id: str, surfaces: list[str]) -> None:
  114	      cleaned = [s.strip() for s in surfaces if s and s.strip()]
  115	      if not cleaned:
  116	          raise CommandError("surface add requires at least one non-empty surface")
  117	      with _write_context(repo_root) as write_root:
  118	          p = _load(write_root)
  119	          _qid, item = _require_slice(p, slice_id, "surface add")
  120	          for s in cleaned:
  121	              if s not in item.integration_surfaces:
  122	                  item.integration_surfaces.append(s)
  123	          _save(write_root, p)
  124	
  125	
  126	  def cmd_surface_remove(*, repo_root: Path, slice_id: str, surface: str) -> None:
  127	      surface = (surface or "").strip()
  128	      if not surface:
  129	          raise CommandError("surface remove requires a non-empty surface")
  130	      with _write_context(repo_root) as write_root:
  131	          p = _load(write_root)
  132	          _qid, item = _require_slice(p, slice_id, "surface remove")
  133	          if surface in item.integration_surfaces:
  134	              item.integration_surfaces.remove(surface)
  135	          _save(write_root, p)
  136	  ```
  137	  Note: the test asserts order `["cms-block-registry", "directus-schema"]`, which is **insertion order with dedupe** (not alpha-sort). The implementation preserves first-seen order. Keep the test assertion matching insertion order.
  138	
  139	### 1.4 Run it — expect PASS
  140	
  141	- [ ] Run:
  142	  ```sh
  143	  python -m pytest tools/tasktool/tests/test_commands.py::SurfaceCommandTests::test_surface_add_appends_unique_sorted -q
  144	  ```
  145	  Expected: **PASS** (1 passed).
  146	
  147	### 1.5 Failing test for `surface remove`
  148	
  149	- [ ] Add to `SurfaceCommandTests`:
  150	  ```python
  151	      def test_surface_remove_drops_one(self):
  152	          t = _Tmp()
  153	          try:
  154	              pid, sid = self._setup_phase_with_slice(t)
  155	              commands.cmd_surface_add(
  156	                  repo_root=t.root, slice_id=f"{pid}.{sid}",
  157	                  surfaces=["cms-block-registry", "directus-schema"],
  158	              )
  159	              commands.cmd_surface_remove(
  160	                  repo_root=t.root, slice_id=f"{pid}.{sid}", surface="directus-schema",
  161	              )
  162	              p = load_project(t.root / "docs/tasklist.json")
  163	              self.assertEqual(p.phases[0].slices[0].integration_surfaces, ["cms-block-registry"])
  164	          finally:
  165	              t.cleanup()
  166	
  167	      def test_surface_add_refuses_cancelled_slice(self):
  168	          t = _Tmp()
  169	          try:
  170	              pid, sid = self._setup_phase_with_slice(t)
  171	              commands.cmd_cancel(repo_root=t.root, id=f"{pid}.{sid}", reason="dropped")
  172	              with self.assertRaises(commands.CommandError):
  173	                  commands.cmd_surface_add(
  174	                      repo_root=t.root, slice_id=f"{pid}.{sid}", surfaces=["x"],
  175	                  )
  176	          finally:
  177	              t.cleanup()
  178	  ```
  179	
  180	### 1.6 Run — expect PASS
  181	
  182	- [ ] Run:
  183	  ```sh
  184	  python -m pytest "tools/tasktool/tests/test_commands.py::SurfaceCommandTests" -q
  185	  ```
  186	  Expected: **PASS** (3 passed). `cmd_surface_remove` and the cancelled-guard are already implemented in 1.3, so these pass without new impl.
  187	
  188	### 1.7 Commit
  189	
  190	- [ ] Run:
  191	  ```sh
  192	  git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
  193	  git commit -m "P7.S2: surface add/remove declaration commands"
  194	  ```
  195	
  196	---
  197	
  198	## Task 2 — `surface list`
  199	
  200	### 2.1 Failing test
  201	
  202	- [ ] Add to `SurfaceCommandTests`:
  203	  ```python
  204	      def test_surface_list_renders_phase_slices(self):
  205	          t = _Tmp()
  206	          try:
  207	              pid, sid = self._setup_phase_with_slice(t)
  208	              commands.cmd_surface_add(
  209	                  repo_root=t.root, slice_id=f"{pid}.{sid}",
  210	                  surfaces=["cms-block-registry", "directus-schema"],
  211	              )
  212	              out = commands.cmd_surface_list(repo_root=t.root, phase_id=pid)
  213	              self.assertIn(f"{pid}.{sid}", out)
  214	              self.assertIn("cms-block-registry", out)
  215	              self.assertIn("directus-schema", out)
  216	          finally:
  217	              t.cleanup()
  218	
  219	      def test_surface_list_all_phases_when_omitted(self):
  220	          t = _Tmp()
  221	          try:
  222	              pid, sid = self._setup_phase_with_slice(t)
  223	              commands.cmd_surface_add(
  224	                  repo_root=t.root, slice_id=f"{pid}.{sid}", surfaces=["theme-tail-css"],
  225	              )
  226	              out = commands.cmd_surface_list(repo_root=t.root, phase_id=None)
  227	              self.assertIn("theme-tail-css", out)
  228	          finally:
  229	              t.cleanup()
  230	  ```
  231	
  232	### 2.2 Run — expect FAIL
  233	
  234	- [ ] Run:
  235	  ```sh
  236	  python -m pytest tools/tasktool/tests/test_commands.py::SurfaceCommandTests::test_surface_list_renders_phase_slices -q
  237	  ```
  238	  Expected: **FAIL** with `AttributeError: ... has no attribute 'cmd_surface_list'`.
  239	
  240	### 2.3 Implement `cmd_surface_list` (+ shared iterator helper)
  241	
  242	- [ ] Add to `tools/tasktool/commands.py` in the same section:
  243	  ```python
  244	  def _iter_phase_slices(p: Project, phase_id: str | None):
  245	      """Yield (phase, slice) for the given phase, or all active phases if None."""
  246	      for ph in p.phases:
  247	          if phase_id is not None and ph.id != phase_id:
  248	              continue
  249	          for slc in ph.slices:
  250	              yield ph, slc
  251	
  252	
  253	  def cmd_surface_list(*, repo_root: Path, phase_id: str | None) -> str:
  254	      with _read_context(repo_root) as write_root:
  255	          p = _load(write_root)
  256	          if phase_id is not None and not any(ph.id == phase_id for ph in p.phases):
  257	              raise CommandError(f"phase {phase_id} not found")
  258	          lines: list[str] = []
  259	          for ph, slc in _iter_phase_slices(p, phase_id):
  260	              surfaces = ", ".join(slc.integration_surfaces) if slc.integration_surfaces else "(none)"
  261	              lines.append(f"{ph.id}.{slc.id}  [{slc.status.value}]  {surfaces}")
  262	          if not lines:
  263	              return "(no slices)\n"
  264	          return "\n".join(lines) + "\n"
  265	  ```
  266	
  267	### 2.4 Run — expect PASS
  268	
  269	- [ ] Run:
  270	  ```sh
  271	  python -m pytest "tools/tasktool/tests/test_commands.py::SurfaceCommandTests" -q
  272	  ```
  273	  Expected: **PASS** (5 passed).
  274	
  275	### 2.5 Commit
  276	
  277	- [ ] Run:
  278	  ```sh
  279	  git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
  280	  git commit -m "P7.S2: surface list report"
  281	  ```
  282	
  283	---
  284	
  285	## Task 3 — `coordinate` set / clear
  286	
  287	### 3.1 Failing test
  288	
  289	- [ ] Add a new test class to `tools/tasktool/tests/test_commands.py`:
  290	  ```python
  291	  class CoordinateCommandTests(unittest.TestCase):
  292	      def _setup(self, t):
  293	          commands.cmd_init(repo_root=t.root, project="demo")
  294	          pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
  295	          sid = commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title="slice")
  296	          return pid, sid
  297	
  298	      def test_coordinate_sets_group(self):
  299	          t = _Tmp()
  300	          try:
  301	              pid, sid = self._setup(t)
  302	              commands.cmd_coordinate(repo_root=t.root, slice_id=f"{pid}.{sid}", group="cms")
  303	              p = load_project(t.root / "docs/tasklist.json")
  304	              self.assertEqual(p.phases[0].slices[0].coordination_group, "cms")
  305	          finally:
  306	              t.cleanup()
  307	
  308	      def test_coordinate_clear_resets_to_none(self):
  309	          t = _Tmp()
  310	          try:
  311	              pid, sid = self._setup(t)
  312	              commands.cmd_coordinate(repo_root=t.root, slice_id=f"{pid}.{sid}", group="cms")
  313	              commands.cmd_coordinate(repo_root=t.root, slice_id=f"{pid}.{sid}", clear=True)
  314	              p = load_project(t.root / "docs/tasklist.json")
  315	              self.assertIsNone(p.phases[0].slices[0].coordination_group)
  316	          finally:
  317	              t.cleanup()
  318	
  319	      def test_coordinate_requires_group_or_clear(self):
  320	          t = _Tmp()
  321	          try:
  322	              pid, sid = self._setup(t)
  323	              with self.assertRaises(commands.CommandError):
  324	                  commands.cmd_coordinate(repo_root=t.root, slice_id=f"{pid}.{sid}")
  325	          finally:
  326	              t.cleanup()
  327	
  328	      def test_coordinate_refuses_cancelled_slice(self):
  329	          # A valid --group is passed so the flag-validation guard is satisfied and
  330	          # the cancelled-slice guard inside `_require_slice` is the thing under test.
  331	          t = _Tmp()
  332	          try:
  333	              pid, sid = self._setup(t)
  334	              commands.cmd_cancel(repo_root=t.root, id=f"{pid}.{sid}", reason="dropped")
  335	              with self.assertRaises(commands.CommandError):
  336	                  commands.cmd_coordinate(repo_root=t.root, slice_id=f"{pid}.{sid}", group="cms")
  337	          finally:
  338	              t.cleanup()
  339	  ```
  340	
  341	### 3.2 Run — expect FAIL
  342	
  343	- [ ] Run:
  344	  ```sh
  345	  python -m pytest tools/tasktool/tests/test_commands.py::CoordinateCommandTests::test_coordinate_sets_group -q
  346	  ```
  347	  Expected: **FAIL** with `AttributeError: ... has no attribute 'cmd_coordinate'`.
  348	
  349	### 3.3 Implement `cmd_coordinate`
  350	
  351	- [ ] Add to `tools/tasktool/commands.py`:
  352	  ```python
  353	  def cmd_coordinate(
  354	      *, repo_root: Path, slice_id: str,
  355	      group: str | None = None, clear: bool = False,
  356	  ) -> None:
  357	      if clear and group is not None:
  358	          raise CommandError("coordinate: --group and --clear are mutually exclusive")
  359	      if not clear and (group is None or not group.strip()):
  360	          raise CommandError("coordinate requires --group <name> or --clear")
  361	      with _write_context(repo_root) as write_root:
  362	          p = _load(write_root)
  363	          _qid, item = _require_slice(p, slice_id, "coordinate")
  364	          item.coordination_group = None if clear else group.strip()
  365	          _save(write_root, p)
  366	  ```
  367	
  368	### 3.4 Run — expect PASS
  369	
  370	- [ ] Run:
  371	  ```sh
  372	  python -m pytest "tools/tasktool/tests/test_commands.py::CoordinateCommandTests" -q
  373	  ```
  374	  Expected: **PASS** (4 passed). `test_coordinate_refuses_cancelled_slice` passes without extra impl — `_require_slice` calls `_refuse_if_cancelled`.
  375	
  376	### 3.5 Commit
  377	
  378	- [ ] Run:
  379	  ```sh
  380	  git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
  381	  git commit -m "P7.S2: coordinate set/clear command"
  382	  ```
  383	
  384	---
  385	
  386	## Task 4 — `reserve add` happy path + `resource:value` parsing
  387	
  388	### 4.1 Failing test
  389	
  390	- [ ] Add a new test class to `tools/tasktool/tests/test_commands.py`:
  391	  ```python
  392	  class ReserveCommandTests(unittest.TestCase):
  393	      def _phase(self, t, n_slices=1):
  394	          commands.cmd_init(repo_root=t.root, project="demo")
  395	          pid = commands.cmd_create_phase(repo_root=t.root, title="phase")
  396	          sids = [
  397	              commands.cmd_create_slice(repo_root=t.root, phase_id=pid, title=f"slice{i}")
  398	              for i in range(n_slices)
  399	          ]
  400	          return pid, sids
  401	
  402	      def test_reserve_add_records_reservation(self):
  403	          t = _Tmp()
  404	          try:
  405	              pid, (sid,) = self._phase(t, 1)
  406	              commands.cmd_reserve_add(
  407	                  repo_root=t.root, slice_id=f"{pid}.{sid}",
  408	                  resource_value="homepage-sort:15", scope="phase", note="hero band",
  409	              )
  410	              p = load_project(t.root / "docs/tasklist.json")
  411	              res = p.phases[0].slices[0].reservations
  412	              self.assertEqual(len(res), 1)
  413	              self.assertEqual(res[0].resource, "homepage-sort")
  414	              self.assertEqual(res[0].value, "15")
  415	              self.assertEqual(res[0].scope, "phase")
  416	              self.assertEqual(res[0].note, "hero band")
  417	          finally:
  418	              t.cleanup()
  419	
  420	      def test_reserve_add_rejects_malformed_resource_value(self):
  421	          t = _Tmp()
  422	          try:
  423	              pid, (sid,) = self._phase(t, 1)
  424	              with self.assertRaises(commands.CommandError):
  425	                  commands.cmd_reserve_add(
  426	                      repo_root=t.root, slice_id=f"{pid}.{sid}",
  427	                      resource_value="no-colon-here", scope="phase",
  428	                  )
  429	          finally:
  430	              t.cleanup()
  431	  ```
  432	  Note `resource:value` splits on the **first** colon only, so `route-slug:/offers` parses to `("route-slug", "/offers")`.
  433	
  434	### 4.2 Run — expect FAIL
  435	
  436	- [ ] Run:
  437	  ```sh
  438	  python -m pytest tools/tasktool/tests/test_commands.py::ReserveCommandTests::test_reserve_add_records_reservation -q
  439	  ```
  440	  Expected: **FAIL** with `AttributeError: ... has no attribute 'cmd_reserve_add'`.
  441	
  442	### 4.3 Implement parser helper + minimal `cmd_reserve_add`
  443	
  444	- [ ] Add to `tools/tasktool/commands.py`. Import the S1 `Reservation` type at the top-of-file `from tasktool.model import (...)` block (add `Reservation` and `LedgerReservation` to the existing import list). Then:
  445	  ```python
  446	  def _parse_resource_value(raw: str) -> tuple[str, str]:
  447	      """Split `<resource>:<value>` on the FIRST colon. Both halves must be non-empty."""
  448	      if ":" not in raw:
  449	          raise CommandError(
  450	              f"reservation must be <resource>:<value>, got {raw!r}"
  451	          )
  452	      resource, value = raw.split(":", 1)
  453	      resource, value = resource.strip(), value.strip()
  454	      if not resource or not value:
  455	          raise CommandError(
  456	              f"reservation must be <resource>:<value> with non-empty halves, got {raw!r}"
  457	          )
  458	      return resource, value
  459	
  460	
  461	  def cmd_reserve_add(
  462	      *, repo_root: Path, slice_id: str, resource_value: str,
  463	      scope: str = "phase", note: str | None = None,
  464	      force: bool = False, reason: str | None = None,
  465	  ) -> None:
  466	      if scope not in ("phase", "project"):
  467	          raise CommandError(f"reserve add: --scope must be phase or project, got {scope!r}")
  468	      resource, value = _parse_resource_value(resource_value)
  469	      with _write_context(repo_root) as write_root:
  470	          p = _load(write_root)
  471	          qid, item = _require_slice(p, slice_id, "reserve add")
  472	          # (collision refusal added in Task 5; happy path only for now)
  473	          item.reservations.append(
  474	              Reservation(resource=resource, value=value, scope=scope, note=note)
  475	          )
  476	          _save(write_root, p)
  477	  ```
  478	
  479	### 4.4 Run — expect PASS
  480	
  481	- [ ] Run:
  482	  ```sh
  483	  python -m pytest "tools/tasktool/tests/test_commands.py::ReserveCommandTests" -q
  484	  ```
  485	  Expected: **PASS** (2 passed).
  486	
  487	### 4.5 Commit
  488	
  489	- [ ] Run:
  490	  ```sh
  491	  git add tools/tasktool/commands.py tools/tasktool/tests/test_commands.py
  492	  git commit -m "P7.S2: reserve add happy path + resource:value parsing"
  493	  ```
  494	
  495	---
  496	
  497	## Task 5 — `reserve add` phase-scope collision refusal (incl. done slices)
  498	
  499	### 5.1 Failing tests
  500	
  501	- [ ] Add to `ReserveCommandTests`:
  502	  ```python
  503	      def test_reserve_add_refuses_phase_scope_collision(self):
  504	          t = _Tmp()
  505	          try:
  506	              pid, (s0, s1) = self._phase(t, 2)
  507	              commands.cmd_reserve_add(
  508	                  repo_root=t.root, slice_id=f"{pid}.{s0}",
  509	                  resource_value="homepage-sort:15", scope="phase",
  510	              )
  511	              with self.assertRaises(commands.CommandError) as cm:
  512	                  commands.cmd_reserve_add(
  513	                      repo_root=t.root, slice_id=f"{pid}.{s1}",
  514	                      resource_value="homepage-sort:15", scope="phase",
  515	                  )
  516	              msg = str(cm.exception)
  517	              self.assertIn("homepage-sort:15", msg)
  518	              self.assertIn(f"{pid}.{s0}", msg)
  519	          finally:
  520	              t.cleanup()
  521	
  522	      def test_reserve_add_collision_counts_done_holder(self):
  523	          t = _Tmp()
  524	          try:
  525	              pid, (s0, s1) = self._phase(t, 2)
  526	              commands.cmd_reserve_add(
  527	                  repo_root=t.root, slice_id=f"{pid}.{s0}",
  528	                  resource_value="homepage-sort:15", scope="phase",
  529	              )
  530	              commands.cmd_start(repo_root=t.root, id=f"{pid}.{s0}")
  531	              commands.cmd_close(repo_root=t.root, id=f"{pid}.{s0}", skip_review_gate=True)
  532	              # s0 is now done; the slot stays taken.
  533	              with self.assertRaises(commands.CommandError):
  534	                  commands.cmd_reserve_add(
  535	                      repo_root=t.root, slice_id=f"{pid}.{s1}",
  536	                      resource_value="homepage-sort:15", scope="phase",
  537	                  )
  538	          finally:
  539	              t.cleanup()
  540	
  541	      def test_reserve_add_ignores_cancelled_holder(self):
  542	          t = _Tmp()
  543	          try:
  544	              pid, (s0, s1) = self._phase(t, 2)
  545	              commands.cmd_reserve_add(
  546	                  repo_root=t.root, slice_id=f"{pid}.{s0}",
  547	                  resource_value="homepage-sort:15", scope="phase",
  548	              )
  549	              commands.cmd_cancel(repo_root=t.root, id=f"{pid}.{s0}", reason="dropped")
  550	              # s0 cancelled → slot released → no refusal.
  551	              commands.cmd_reserve_add(
  552	                  repo_root=t.root, slice_id=f"{pid}.{s1}",
  553	                  resource_value="homepage-sort:15", scope="phase",
  554	              )
  555	              p = load_project(t.root / "docs/tasklist.json")
  556	              s1_row = next(s for s in p.phases[0].slices if s.id == s1)
  557	              self.assertEqual(len(s1_row.reservations), 1)
  558	          finally:
  559	              t.cleanup()
  560	
  561	      def test_reserve_add_same_slice_no_self_collision(self):
  562	          t = _Tmp()
  563	          try:
  564	              pid, (s0,) = self._phase(t, 1)
  565	              commands.cmd_reserve_add(
  566	                  repo_root=t.root, slice_id=f"{pid}.{s0}",
  567	                  resource_value="homepage-sort:15", scope="phase",
  568	              )
  569	              # Re-adding the SAME value to the SAME slice is idempotent, not a collision.
  570	              commands.cmd_reserve_add(
  571	                  repo_root=t.root, slice_id=f"{pid}.{s0}",
  572	                  resource_value="homepage-sort:15", scope="phase",
  573	              )
  574	              p = load_project(t.root / "docs/tasklist.json")
  575	              self.assertEqual(len(p.phases[0].slices[0].reservations), 1)
  576	          finally:
  577	              t.cleanup()
  578	
  579	      def test_reserve_add_same_slice_phase_and_project_both_held(self):
  580	          # Self-dedupe must key on (resource, value, scope): a slice may hold the
  581	          # same resource:value at BOTH phase and project scope. Only the
  582	          # project-scoped one is laddered (Task 9), so a scope-blind self-dedupe
  583	          # would silently drop the reservation that must reach the ledger.
  584	          t = _Tmp()
  585	          try:
  586	              pid, (s0,) = self._phase(t, 1)
  587	              commands.cmd_reserve_add(
  588	                  repo_root=t.root, slice_id=f"{pid}.{s0}",
  589	                  resource_value="route-slug:/offers", scope="phase",
  590	              )
  591	              commands.cmd_reserve_add(
  592	                  repo_root=t.root, slice_id=f"{pid}.{s0}",
  593	                  resource_value="route-slug:/offers", scope="project",
  594	              )
  595	              p = load_project(t.root / "docs/tasklist.json")
  596	              res = p.phases[0].slices[0].reservations
  597	              scopes = sorted(r.scope for r in res if r.resource == "route-slug" and r.value == "/offers")
  598	              self.assertEqual(scopes, ["phase", "project"])
  599	          finally:
  600	              t.cleanup()

[truncated: 959 additional lines]

## Context Previews

### docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md

    1	# P7 — Integration-surface-aware parallel slice safety
    2	
    3	**Status:** design (spec)
    4	**Date:** 2026-06-02
    5	**Phase ID:** `P7`
    6	
    7	## 1. Problem
    8	
    9	`tasktool` decides whether slices may run in parallel from **declared feature
   10	dependencies** (`Slice.depends_on`) and the `parallel_group` tag. Those answer
   11	"does S4's feature need S3's feature first?" They do **not** answer the question
   12	that actually governs safe parallel execution: **what shared write surface does
   13	each slice mutate?**
   14	
   15	This gap produced a real failure in the `multistore` project, phase P20. Four
   16	storefront-marketing slices (`P20.S2`–`P20.S5`) each declared a dependency only
   17	on the bootstrap slice `P20.S1`, so `tasktool ready-slices`/`schedule` reported
   18	them as independently executable. They were feature-distinct (slider, promo
   19	bands, overlays, blog) but **integration-overlapping**: every one of them wrote
   20	the same centralized CMS-block machinery — block contracts, parser allowlists,
   21	Directus schema/seed files, renderer dispatch, theme CSS tails, and the homepage
   22	ordering array.
   23	
   24	The observed consequences:
   25	
   26	1. **Conflict-bomb merges.** `P20.S4`'s merge conflicted across `page-renderer.tsx`,
   27	   theme CSS, reviewer-request artifacts, `docs/tasklist.json`, Directus
   28	   bootstrap/schema/seed files, content-contract schemas/types, and parser tests.
   29	2. **Stale-base merges.** `P20.S4` was completed in a worktree that branched from
   30	   `main` *before* `P20.S2`/`P20.S3` and their cleanup landed. The worktree
   31	   snapshot was older than `main`, so the merge replayed churn that was already
   32	   integrated.
   33	3. **A real semantic collision, not just textual churn.** `P20.S3` and `P20.S4`
   34	   independently chose homepage sort slot `15`. Nothing forced the second slice
   35	   onto a free slot at planning time; the collision was discovered and resolved
   36	   at merge.
   37	4. **Merge-unsafe reviewer artifacts.** Generated reviewer-request files
   38	   add/add-conflicted despite not being behavioral code.
   39	
   40	The root cause is **dependency modeling by feature intent rather than by
   41	integration surface.** "Slider" and "promo bands" were non-dependent product
   42	slices, but they both wrote the same registry, schema, seed arrays, ordering
   43	slots, parser unions, and theme areas. The tool allowed parallel execution
   44	because the declared dependencies were technically satisfied.
   45	
   46	## 2. Goals
   47	
   48	1. **Prevention.** Let planning declare, per slice, the **integration surfaces**
   49	   it writes and the **scarce resources** it allocates. `tasktool` warns when
   50	   sibling ready/in-progress slices share a surface with no dependency or
   51	   coordination link, and *refuses* a duplicate scarce-resource allocation.
   52	2. **Recovery.** When a sibling slice has landed on the base branch since a
   53	   slice's worktree branched, surface that fact reliably and provide a
   54	   conservative "integrate current main" path before the post-slice review/merge,
   55	   plus a documented centralized-registry merge playbook.
   56	3. **Merge-safe reviewer artifacts.** Generated reviewer-request files must never
   57	   add/add-conflict between sibling worktrees.
   58	4. **Plan ↔ tracker coherence.** Declared surfaces/reservations must be reflected
   59	   in planning artifacts so the plan and the tracker cannot silently diverge.
   60	
   61	## 3. Non-goals (explicit)
   62	
   63	- **Directus-specific verifier diagnostics and stale-token handling.** These were
   64	  real `multistore` pain points (a stale `DIRECTUS_ADMIN_TOKEN` shadowing valid
   65	  admin credentials made a non-code problem look like a schema failure), but they
   66	  are project-specific. Superstar core is general-purpose and zero-dependency;
   67	  Directus tooling belongs in the `multistore` project, not here.
   68	- **Automatic merge-conflict resolution.** The tooling detects and routes; it does
   69	  not auto-merge semantic conflicts.
   70	- **Path-glob surface *inference* as the primary model.** Explicit declaration is
   71	  the source of truth. A path-glob comparison survives only as a deferred,
   72	  warning-only post-implementation *audit* (§4.G), never as the planning model.
   73	- **A "touches existing resource" reservation kind.** Reservations model scarce
   74	  *allocations* (claiming a new value). Modifying a shared existing resource is a
   75	  *surface/coordination* concern, not an allocation, so maintenance work is not
   76	  falsely blocked. A future "touches-existing" field is noted, not built here.
   77	- **`worktree sync` as an unconditional command.** Detection ships first; the
   78	  mutating sync command is gated behind strict preconditions and is the explicit
   79	  deferral candidate if scope tightens.
   80	
   81	## 4. Design
   82	
   83	### 4.A Data model (`model.py`, schema `v2 → v3`; `migrate.py`)
   84	
   85	Add to `Slice`:
   86	
   87	- `integration_surfaces: list[str]` — conventional surface tags naming shared
   88	  write areas the slice mutates. Free-form strings, but a recommended vocabulary
   89	  is documented in `tasklist-discipline` (e.g. `cms-block-registry`,
   90	  `directus-schema`, `page-renderer-dispatch`, `theme-tail-css`,
   91	  `content-contract-types`, `reviewer-artifacts`). Default `[]`.
   92	- `reservations: list[Reservation]` where
   93	  `Reservation = {resource: str, value: str, scope: "phase" | "project", note: str | None}`.
   94	  A reservation is a **scarce allocation claim** on a single value
   95	  (`homepage-sort:15`, `directus-collection:homepage_slider`, `route-slug:/offers`,
   96	  `block-kind:slider`, `cache-tag:home`). Default `[]`.
   97	- `coordination_group: str | None` — names a set of slices that *intentionally*
   98	  share an integration surface and agree to coordinate (serialize reviews,
   99	  designate an integration owner, run the registry merge playbook). Distinct from
  100	  `parallel_group`, which asserts independent parallelism. Default `None`.
  101	- `worktree_base_sha: str | None` — the base-branch commit the slice's worktree
  102	  was created from, recorded at `tasktool start`. Enables reliable
  103	  "a sibling landed since this slice branched" detection that survives later
  104	  rebases/merges, instead of fragile merge-base inference. Default `None`.
  105	- `landed_base_sha: str | None` — the base-branch commit at which this slice's
  106	  work landed, recorded at post-merge prune (see §4.D). This is the authoritative
  107	  "this slice shipped to base" signal that `closed` (a date) cannot provide.
  108	  Default `None`.
  109	
  110	Add to `Project`:
  111	
  112	- `reservations_ledger: list[LedgerReservation]` where
  113	  `LedgerReservation = Reservation + {owner_id: str, owner_phase_id: str, archived_date: str}`.
  114	  Project-scoped reservations are copied here when their owning phase is archived,
  115	  so project-scope uniqueness checks — and the refusal message that must name the
  116	  holder (§4.B) — survive removal of shipped phases from the active tracker. The
  117	  extra fields preserve the owning slice/phase and archive date for the refusal
  118	  message and audit trail. Default `[]`.
  119	
  120	Schema bump to `v3`. Migration is additive: missing fields default to empty/`None`
  121	and `reservations_ledger` to `[]`. Round-trip and v1/v2 compatibility tests
  122	extended.
  123	
  124	**Serialization rule (F5).** New fields follow the existing omit-when-default
  125	convention in `serialize.py`: an empty `integration_surfaces`/`reservations`,
  126	a `None` `coordination_group`/`worktree_base_sha`/`landed_base_sha`, and an empty
  127	`Project.reservations_ledger` are **omitted** on serialization, exactly as
  128	default-valued worktree/workflow keys are today. Historical rows therefore gain no
  129	churn on round-trip; a row's bytes change only once it actually declares a surface,
  130	reservation, coordination group, or base SHA.
  131	
  132	### 4.B Declaration CLI (`cli.py` + `commands.py`)
  133	
  134	```sh
  135	tasktool surface add <slice-id> <surface> [<surface>...]
  136	tasktool surface remove <slice-id> <surface>
  137	tasktool surface list [<phase-id>]
  138	
  139	tasktool reserve add <slice-id> <resource>:<value> [--scope phase|project] [--note "..."] [--force --reason "..."]
  140	tasktool reserve remove <slice-id> <resource>:<value>
  141	tasktool reserve list [<phase-id>]
  142	
  143	tasktool coordinate <slice-id> --group <name>     # set coordination_group
  144	tasktool coordinate <slice-id> --clear
  145	```
  146	
  147	- `surface`/`coordinate` are declaration-only; they never refuse.
  148	- **`reserve add` refuses** when the same `resource:value` is already held by
  149	  another **non-cancelled** slice within the relevant scope:
  150	  - `scope: phase` (default) — checks other non-cancelled slices in the same
  151	    phase. Done slices count: a done slice shipped that value to `main`, so the
  152	    slot is taken.
  153	  - `scope: project` — checks all non-cancelled slices across **active** phases
  154	    *and* `Project.reservations_ledger`.
  155	  The refusal names the holding slice (from the slice row, or from the ledger's
  156	  `owner_id`/`owner_phase_id`/`archived_date` for archived holders) and the value.
  157	- **Override (F3).** `--force` is the only way to add a colliding reservation and
  158	  **requires** `--reason "<text>"`. It mutates **only the reserving slice**: it
  159	  appends the reservation and records a timestamped note
  160	  `Reservation-override <ISO-ts>: <resource>:<value> over <holder-id> — <reason>`.
  161	  The holder slice is **not** mutated. `--force` without `--reason` is refused.
  162	  Without `--force`, a collision is a hard refusal (exit non-zero). This refusal
  163	  is the gate that would have forced `P20.S4` off slot `15` at planning time.
  164	- **Cancelled work never enters the ledger.** On `tasktool archive-phase`,
  165	  project-scoped reservations from the phase's **non-cancelled (`done`)** slices
  166	  are appended to `Project.reservations_ledger` as `LedgerReservation`s, carrying
  167	  `owner_id`/`owner_phase_id`/`archived_date`. Cancelled slices ship nothing, so
  168	  their reservations — including `--force` overrides — are released and never
  169	  laddered.
  170	- **Ledger dedupe preserves every holder (F7).** Dedup is keyed on
  171	  `resource:value:scope:owner_id`, **not** `resource:value:scope`. Re-archiving the
  172	  same phase is idempotent (same owner ⇒ same key), but two distinct `done` slices
  173	  that intentionally `--force`-shared a project-scoped value both survive in the
  174	  ledger, so the owner-metadata audit trail is never silently collapsed to one
  175	  holder. A project-scope `reserve add` collision check that matches any ledger
  176	  entry on `resource:value:scope` (regardless of owner) still refuses — multiple
  177	  recorded holders strengthen, not weaken, the refusal message.
  178	
  179	### 4.C Scheduling overlap detection (`commands.py`)
  180	
  181	Augment the existing scheduling reporters; **surface overlap is a warning, not a
  182	block** (surfaces are coarse — two slices may touch the same registry in
  183	non-conflicting ways), while **reservation contention is already prevented at
  184	declaration time**.
  185	
  186	- `cmd_ready_slices` and `cmd_schedule`: for each ready/in-progress slice, compute
  187	  the set of other non-terminal slices that (a) share ≥1 integration surface,
  188	  (b) have **no** `depends_on` link in either direction, and (c) are **not** in
  189	  the same `coordination_group`. Emit a `surface_overlap` field/warning listing
  190	  the sibling(s) and shared surface(s). Slices in a shared `coordination_group`
  191	  are reported as `coordinated`, not warned.
  192	- New `tasktool surface check <phase-id>` — a dedicated read-only report:
  193	  - every unguarded surface overlap (siblings sharing a surface without a dep or
  194	    coordination link),
  195	  - every coordinated surface (shared surface within a `coordination_group`),
  196	  - reservation contention within the phase (should be empty if `reserve add`
  197	    refusal held; surfaced for audit and for `--force` overrides).
  198	  Text and `--format json`. Intended to be run during ratification and before
  199	  parallel dispatch.
  200	- `cmd_ratify --parallel-group <g>`: when adding a slice whose surfaces overlap

[truncated: 211 additional lines]
### docs/tasklist.json

    1	{
    2	  "archived_cross_cutting": [
    3	    {
    4	      "archived_date": "2026-05-21",
    5	      "archived_path": "docs/archived-tasks/X15-archive-closed-cross-cutting-items.md",
    6	      "id": "X15",
    7	      "title": "Archive closed cross-cutting items"
    8	    },
    9	    {
   10	      "archived_date": "2026-05-21",
   11	      "archived_path": "docs/archived-tasks/X16-stamp-installed-shims-and-enforce-versio.md",
   12	      "id": "X16",
   13	      "title": "Stamp installed shims and enforce version drift refusal"
   14	    },
   15	    {
   16	      "archived_date": "2026-05-23",
   17	      "archived_path": "docs/archived-tasks/X18-harden-external-reviewer-caller-detectio.md",
   18	      "id": "X18",
   19	      "title": "Harden external reviewer caller detection for Codex"
   20	    },
   21	    {
   22	      "archived_date": "2026-05-23",
   23	      "archived_path": "docs/archived-tasks/X20-install-codex-todo-snapshot-hook.md",
   24	      "id": "X20",
   25	      "title": "Install Codex todo snapshot hook"
   26	    },
   27	    {
   28	      "archived_date": "2026-05-23",
   29	      "archived_path": "docs/archived-tasks/X19-install-todowrite-snapshot-hook-via-depl.md",
   30	      "id": "X19",
   31	      "title": "Install TodoWrite snapshot hook via deploy.sh"
   32	    },
   33	    {
   34	      "archived_date": "2026-05-23",
   35	      "archived_path": "docs/archived-tasks/X21-fix-codex-todo-snapshot-async-hook-regis.md",
   36	      "id": "X21",
   37	      "title": "Fix Codex todo snapshot async hook registration"
   38	    },
   39	    {
   40	      "archived_date": "2026-05-24",
   41	      "archived_path": "docs/archived-tasks/X22-add-cancelled-terminal-status-to-tasktoo.md",
   42	      "id": "X22",
   43	      "title": "Add cancelled terminal status to tasktool"
   44	    },
   45	    {
   46	      "archived_date": "2026-05-24",
   47	      "archived_path": "docs/archived-tasks/X23-document-cancelled-lifecycle-and-admin-c.md",
   48	      "id": "X23",
   49	      "title": "Document cancelled lifecycle and admin closeout guidance"
   50	    },
   51	    {
   52	      "archived_date": "2026-05-26",
   53	      "archived_path": "docs/archived-tasks/X24-use-global-tasktool-shim-in-superstar-gu.md",
   54	      "id": "X24",
   55	      "title": "Use global tasktool shim in Superstar guidance"
   56	    },
   57	    {
   58	      "archived_date": "2026-05-26",
   59	      "archived_path": "docs/archived-tasks/X25-duck-media-audio-during-tasktool-tts-and.md",
   60	      "id": "X25",
   61	      "title": "Duck media audio during tasktool TTS and verify Codex plugin payload"
   62	    },
   63	    {
   64	      "archived_date": "2026-05-26",
   65	      "archived_path": "docs/archived-tasks/X26-fix-codex-marketplace-payload-refresh-fo.md",
   66	      "id": "X26",
   67	      "title": "Fix Codex marketplace payload refresh for Superstar"
   68	    },
   69	    {
   70	      "archived_date": "2026-05-26",
   71	      "archived_path": "docs/archived-tasks/X1-default-external-review-prompt-transport.md",
   72	      "id": "X1",
   73	      "title": "Default external-review prompt transport to stdin"
   74	    },
   75	    {
   76	      "archived_date": "2026-05-26",
   77	      "archived_path": "docs/archived-tasks/X2-add-repo-local-tasktool-launcher.md",
   78	      "id": "X2",
   79	      "title": "Add repo-local tasktool launcher"
   80	    },
   81	    {
   82	      "archived_date": "2026-05-26",
   83	      "archived_path": "docs/archived-tasks/X3-spot-fix-parse-bold-external-review-verd.md",
   84	      "id": "X3",
   85	      "title": "Spot fix: parse bold external-review verdict headings"
   86	    },
   87	    {
   88	      "archived_date": "2026-05-26",
   89	      "archived_path": "docs/archived-tasks/X4-spot-fix-broaden-legacy-tasklist-importe.md",
   90	      "id": "X4",
   91	      "title": "Spot fix: broaden legacy tasklist importer compatibility"
   92	    },
   93	    {
   94	      "archived_date": "2026-05-26",
   95	      "archived_path": "docs/archived-tasks/X5-add-finished-agent-notification-hook.md",
   96	      "id": "X5",
   97	      "title": "Add finished-agent notification hook"
   98	    },
   99	    {
  100	      "archived_date": "2026-05-26",
  101	      "archived_path": "docs/archived-tasks/X6-fix-codex-finished-agent-hook-compatibil.md",
  102	      "id": "X6",
  103	      "title": "Fix Codex finished-agent hook compatibility"
  104	    },
  105	    {
  106	      "archived_date": "2026-05-26",
  107	      "archived_path": "docs/archived-tasks/X7-fix-superstar-codex-plugin-payload-versi.md",
  108	      "id": "X7",
  109	      "title": "Fix Superstar Codex plugin payload version drift"
  110	    },
  111	    {
  112	      "archived_date": "2026-05-26",
  113	      "archived_path": "docs/archived-tasks/X8-move-semantic-notifications-from-agent-h.md",
  114	      "id": "X8",
  115	      "title": "Move semantic notifications from agent hooks to tasktool status changes"
  116	    },
  117	    {
  118	      "archived_date": "2026-05-26",
  119	      "archived_path": "docs/archived-tasks/X9-coalesce-bursty-tasktool-audio-notificat.md",
  120	      "id": "X9",
  121	      "title": "Coalesce bursty tasktool audio notifications"
  122	    },
  123	    {
  124	      "archived_date": "2026-05-26",
  125	      "archived_path": "docs/archived-tasks/X10-harden-external-review-verdict-parser-an.md",
  126	      "id": "X10",
  127	      "title": "Harden external-review verdict parser and prompt against Claude formatting variants"
  128	    },
  129	    {
  130	      "archived_date": "2026-05-26",
  131	      "archived_path": "docs/archived-tasks/X11-make-external-review-bridge-global.md",
  132	      "id": "X11",
  133	      "title": "Make external-review bridge global"
  134	    },
  135	    {
  136	      "archived_date": "2026-05-26",
  137	      "archived_path": "docs/archived-tasks/X12-tasktool-require-authoritative-checkout-.md",
  138	      "id": "X12",
  139	      "title": "tasktool: require authoritative-checkout routing for mutations"
  140	    },
  141	    {
  142	      "archived_date": "2026-05-26",
  143	      "archived_path": "docs/archived-tasks/X13-fix-tasktool-close-repeated-refs-parsing.md",
  144	      "id": "X13",
  145	      "title": "Fix tasktool close repeated refs parsing"
  146	    },
  147	    {
  148	      "archived_date": "2026-05-26",
  149	      "archived_path": "docs/archived-tasks/X14-stabilize-local-claude-codex-plugin-curr.md",
  150	      "id": "X14",
  151	      "title": "Stabilize local Claude/Codex plugin current entrypoints"
  152	    },
  153	    {
  154	      "archived_date": "2026-05-26",
  155	      "archived_path": "docs/archived-tasks/X17-make-spec-and-plan-artifact-handling-tra.md",
  156	      "id": "X17",
  157	      "title": "Make spec and plan artifact handling transactional"
  158	    },
  159	    {
  160	      "archived_date": "2026-05-26",
  161	      "archived_path": "docs/archived-tasks/X27-add-tasktool-tts-for-workflow-artifacts-.md",
  162	      "id": "X27",
  163	      "title": "Add tasktool TTS for workflow artifacts and step changes"
  164	    },
  165	    {
  166	      "archived_date": "2026-05-26",
  167	      "archived_path": "docs/archived-tasks/X28-prefer-explicit-notification-ding-sound-.md",
  168	      "id": "X28",
  169	      "title": "Prefer explicit notification ding sound file"
  170	    }
  171	  ],
  172	  "archived_phases": [
  173	    {
  174	      "archived_date": "2026-05-18",
  175	      "archived_path": "docs/archived-tasks/P2-tasktool-json-backed-task-management-cli.md",
  176	      "id": "P2",
  177	      "title": "tasktool: JSON-backed task management CLI"
  178	    },
  179	    {
  180	      "archived_date": "2026-05-19",
  181	      "archived_path": "docs/archived-tasks/P4-tasktool-coordination-and-lifecycle-auth.md",
  182	      "id": "P4",
  183	      "title": "Tasktool coordination and lifecycle authority"
  184	    },
  185	    {
  186	      "archived_date": "2026-05-19",
  187	      "archived_path": "docs/archived-tasks/P3-phase-planning-workflow.md",
  188	      "id": "P3",
  189	      "title": "Phase planning workflow"
  190	    },
  191	    {
  192	      "archived_date": "2026-05-20",
  193	      "archived_path": "docs/archived-tasks/P1-external-reviewer-work-historical.md",
  194	      "id": "P1",
  195	      "title": "External-reviewer work (historical)"
  196	    },
  197	    {
  198	      "archived_date": "2026-05-21",
  199	      "archived_path": "docs/archived-tasks/P5-tasktool-owned-worktree-lifecycle-using-.md",
  200	      "id": "P5",

[truncated: 244 additional lines]

<!-- superstar-prompt:end -->