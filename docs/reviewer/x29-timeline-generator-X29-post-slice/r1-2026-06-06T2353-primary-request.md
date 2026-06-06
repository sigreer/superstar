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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/worktree-x29-visual-work-history-timeline-generator

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-06-06-X29-timeline-generator.md

Additional context files:
- docs/specs/2026-06-06-X29-timeline-design.md
- docs/tasklist.json
- docs/handoffs/2026-06-06-X29-slice-close-note.md

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

### docs/plans/2026-06-06-X29-timeline-generator.md

    1	# X29 — Visual Work-History Timeline Generator Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** A zero-dependency Python tool (`tools/timeline/`) that renders any tasktool-managed repo's phase/slice/X-item history as a single self-contained, browser-viewable HTML timeline, plus a run-once legacy backfill utility.
    6	
    7	**Architecture:** Four-layer pipeline — `extract.py` (git replay + live tracker + archive JSON blocks), `model.py` (the only schema-aware module; normalizes to `TimelineItem`), `render.py` (braided centre-spine HTML), `timeline.py` (CLI). `backfill.py` is a separate run-once migrator. Spec: `docs/specs/2026-06-06-X29-timeline-design.md`.
    8	
    9	**Tech Stack:** Python 3 stdlib only. Git via `subprocess`. Tests with pytest (fixture git repos built in tmpdir).
   10	
   11	**Tracker row:** `X29` (cross-cutting). First execution step: `tasktool set X29 --status in_progress`. Commit messages prefixed `X29:`. Execution should run from an isolated worktree per `superstar:using-git-worktrees`.
   12	
   13	**Scheduling:** Cross-cutting row — no `depends_on`/`parallel_group`/surface reservations apply. No sibling slices can overlap this work; it touches only `tools/timeline/**` and one line in `pyproject.toml`.
   14	
   15	---
   16	
   17	### Task 1: Scaffolding and pytest discovery
   18	
   19	**Files:**
   20	- Create: `tools/timeline/__init__.py` (empty)
   21	- Create: `tools/timeline/tests/__init__.py` (empty)
   22	- Create: `tools/timeline/tests/helpers.py`
   23	- Modify: `pyproject.toml:3`
   24	
   25	- [ ] **Step 1: Create the package skeleton**
   26	
   27	```bash
   28	mkdir -p tools/timeline/tests
   29	touch tools/timeline/__init__.py tools/timeline/tests/__init__.py
   30	```
   31	
   32	- [ ] **Step 2: Add `tools/timeline/tests` to pytest discovery**
   33	
   34	In `pyproject.toml`, change the `[tool.pytest.ini_options]` table to:
   35	
   36	```toml
   37	[tool.pytest.ini_options]
   38	addopts = "--import-mode=importlib"
   39	testpaths = ["scripts/tests", "tools/tasktool/tests", "skills/external-review/tests", "tools/timeline/tests"]
   40	pythonpath = ["tools"]
   41	```
   42	
   43	This makes the import strategy explicit: tests import `from timeline import ...`
   44	with `tools` on `sys.path` (the same convention `tasktool` tests rely on
   45	implicitly), and the CLI entrypoints insert `tools` themselves when run as
   46	scripts. `pythonpath` is additive — it does not disturb the existing
   47	`scripts/tests` and `skills/external-review/tests` suites.
   48	
   49	- [ ] **Step 3: Write the shared test helpers**
   50	
   51	Create `tools/timeline/tests/helpers.py`:
   52	
   53	```python
   54	"""Shared fixture builders for timeline tests."""
   55	
   56	import json
   57	import os
   58	import subprocess
   59	
   60	
   61	def doc(phases=None, cross=None):
   62	    return {
   63	        "schema_version": 1,
   64	        "project": "fixture",
   65	        "north_star": "",
   66	        "last_reviewed": None,
   67	        "phases": phases or [],
   68	        "cross_cutting": cross or [],
   69	        "archived_phases": [],
   70	        "archived_cross_cutting": [],
   71	    }
   72	
   73	
   74	def phase(pid, status="ready", created=None, started=None, closed=None,
   75	          slices=None, title=None):
   76	    return {
   77	        "id": pid, "status": status, "created": created, "started": started,
   78	        "closed": closed, "title": title or f"Phase {pid}",
   79	        "slices": slices or [], "notes": "",
   80	    }
   81	
   82	
   83	def slice_(sid, status="ready", created=None, started=None, closed=None, title=None):
   84	    return {
   85	        "id": sid, "status": status, "created": created, "started": started,
   86	        "closed": closed, "title": title or f"Slice {sid}",
   87	        "tasks": [], "refs": [], "notes": "",
   88	    }
   89	
   90	
   91	def x(xid, status="ready", created=None, started=None, closed=None, title=None):
   92	    return {
   93	        "id": xid, "status": status, "created": created, "started": started,
   94	        "closed": closed, "title": title or f"Cross {xid}", "notes": "",
   95	    }
   96	
   97	
   98	def make_repo(tmp_path, snapshots):
   99	    """Create a git repo with one commit of docs/tasklist.json per snapshot.
  100	
  101	    snapshots: list of (iso_datetime_with_offset, doc_dict),
  102	               e.g. ("2026-06-01T10:00:00 +0000", doc(...)).
  103	    Returns the repo path.
  104	    """
  105	    repo = tmp_path / "repo"
  106	    (repo / "docs").mkdir(parents=True)
  107	    run = lambda *a, **kw: subprocess.run(a, cwd=repo, check=True,
  108	                                          capture_output=True, **kw)
  109	    run("git", "init", "-q")
  110	    run("git", "config", "user.email", "test@test")
  111	    run("git", "config", "user.name", "test")
  112	    for iso, d in snapshots:
  113	        (repo / "docs" / "tasklist.json").write_text(json.dumps(d, indent=2))
  114	        env = {**os.environ, "GIT_AUTHOR_DATE": iso, "GIT_COMMITTER_DATE": iso}
  115	        run("git", "add", "-A")
  116	        subprocess.run(["git", "commit", "-q", "-m", "snap"], cwd=repo,
  117	                       check=True, capture_output=True, env=env)
  118	    return repo
  119	```
  120	
  121	- [ ] **Step 4: Verify pytest discovers the (empty) test dir without error**
  122	
  123	Run: `python3 -m pytest tools/timeline/tests -q`
  124	Expected: `no tests ran` (exit code 5 is fine at this stage)
  125	
  126	- [ ] **Step 5: Commit**
  127	
  128	```bash
  129	git add tools/timeline pyproject.toml
  130	git commit -m "X29: scaffold tools/timeline package and pytest discovery"
  131	```
  132	
  133	---
  134	
  135	### Task 2: `model.py` — date parsing and item construction
  136	
  137	**Files:**
  138	- Create: `tools/timeline/model.py`
  139	- Test: `tools/timeline/tests/test_model.py`
  140	
  141	- [ ] **Step 1: Write the failing tests**
  142	
  143	Create `tools/timeline/tests/test_model.py`:
  144	
  145	```python
  146	import datetime as dt
  147	
  148	import pytest
  149	
  150	from timeline import model
  151	from timeline.tests.helpers import doc, phase, slice_, x
  152	
  153	
  154	def test_parse_tracker_date_day():
  155	    when, precision = model.parse_tracker_date("2026-05-20")
  156	    assert when == dt.datetime(2026, 5, 20)
  157	    assert precision == "day"
  158	
  159	
  160	def test_parse_tracker_date_minute():
  161	    when, precision = model.parse_tracker_date("2026-05-20T14:30:00")
  162	    assert when == dt.datetime(2026, 5, 20, 14, 30)
  163	    assert precision == "minute"
  164	
  165	
  166	def test_parse_tracker_date_absent_and_epoch():
  167	    assert model.parse_tracker_date(None) == (None, "day")
  168	    assert model.parse_tracker_date("") == (None, "day")
  169	    assert model.parse_tracker_date("1970-01-01") == (None, "day")
  170	
  171	
  172	def test_items_from_project_walks_phases_slices_cross():
  173	    d = doc(
  174	        phases=[phase("P1", status="done", closed="2026-05-01",
  175	                      slices=[slice_("S1", status="done", closed="2026-05-01")])],
  176	        cross=[x("X1", status="done", closed="2026-05-02")],
  177	    )
  178	    items = {i.key: i for i in model.items_from_project(d)}
  179	    assert set(items) == {"P1", "P1.S1", "X1"}
  180	    assert items["P1"].kind == "phase" and items["P1"].parent is None
  181	    assert items["P1.S1"].kind == "slice" and items["P1.S1"].parent == "P1"
  182	    assert items["X1"].kind == "x"
  183	    assert items["P1.S1"].closed.when == dt.datetime(2026, 5, 1)
  184	    assert items["P1.S1"].closed.source == "field"
  185	
  186	
  187	def test_item_from_cross():
  188	    it = model.item_from_cross(x("X9", status="done", closed="2026-05-03"))
  189	    assert (it.key, it.kind, it.status) == ("X9", "x", "done")
  190	
  191	
  192	def test_collect_dedup_first_wins():
  193	    live = doc(phases=[phase("P2", status="ready", created="2026-06-01")])
  194	    arch = doc(phases=[phase("P2", status="done", closed="2026-05-30")])
  195	    items = model.collect(live, [arch], [])
  196	    p2 = [i for i in items if i.key == "P2"]
  197	    assert len(p2) == 1 and p2[0].status == "ready"  # live wins
  198	
  199	
  200	def test_label_prefers_display_title():
  201	    it = model.item_from_cross(x("X9", title="raw jargon title"))
  202	    assert it.label() == "raw jargon title"
  203	    it.display_title = "Friendly name"
  204	    assert it.label() == "Friendly name"
  205	```
  206	
  207	- [ ] **Step 2: Run tests to verify they fail**
  208	
  209	Run: `python3 -m pytest tools/timeline/tests/test_model.py -q`
  210	Expected: FAIL — `ModuleNotFoundError` on `timeline.model` (run from the repo root)
  211	
  212	- [ ] **Step 3: Implement `model.py` (construction half)**
  213	
  214	Create `tools/timeline/model.py`:
  215	
  216	```python
  217	"""Normalized tracker model for the timeline generator.
  218	
  219	This is the ONLY module that knows the docs/tasklist.json schema. If a shared
  220	tracker-model module is later extracted from tasktool, replace this module's
  221	internals; TimelineItem is the seam consumed by extract/render/timeline.
  222	"""
  223	
  224	from __future__ import annotations
  225	
  226	import datetime as dt
  227	from dataclasses import dataclass, field
  228	
  229	EPOCH_PLACEHOLDER = "1970-01-01"
  230	TERMINAL_STATUSES = {"done", "cancelled"}
  231	START_STATUSES = {"in_progress", "started"}
  232	
  233	
  234	def parse_tracker_date(raw):
  235	    """ISO 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM[:SS]' -> (datetime|None, precision)."""
  236	    if not raw or raw == EPOCH_PLACEHOLDER:
  237	        return None, "day"
  238	    if "T" in raw:
  239	        return dt.datetime.fromisoformat(raw), "minute"
  240	    d = dt.date.fromisoformat(raw)
  241	    return dt.datetime(d.year, d.month, d.day), "day"
  242	
  243	
  244	@dataclass
  245	class DateValue:
  246	    when: dt.datetime | None = None
  247	    precision: str = "day"      # "day" | "minute"
  248	    source: str = "field"       # "field" | "replay" | "override"
  249	
  250	
  251	@dataclass
  252	class TimelineItem:
  253	    key: str                    # "P21", "P21.S4", "X13"
  254	    kind: str                   # "phase" | "slice" | "x"
  255	    parent: str | None
  256	    title: str
  257	    status: str
  258	    display_title: str | None = None
  259	    created: DateValue = field(default_factory=DateValue)
  260	    started: DateValue = field(default_factory=DateValue)
  261	    closed: DateValue = field(default_factory=DateValue)
  262	    excluded: bool = False
  263	
  264	    def label(self):
  265	        return self.display_title or self.title
  266	
  267	
  268	def _date_value(obj, name):
  269	    when, precision = parse_tracker_date(obj.get(name))
  270	    return DateValue(when, precision, "field")
  271	
  272	
  273	def _item(key, kind, parent, obj):
  274	    return TimelineItem(
  275	        key=key, kind=kind, parent=parent,
  276	        title=obj.get("title") or key,
  277	        status=obj.get("status", "unknown"),
  278	        created=_date_value(obj, "created"),
  279	        started=_date_value(obj, "started"),
  280	        closed=_date_value(obj, "closed"),
  281	    )
  282	
  283	
  284	def items_from_project(doc):
  285	    """Walk a project-shaped dict (live tasklist.json or an archived
  286	    '## Full phase JSON' block) into TimelineItem records."""
  287	    items = []
  288	    for p in doc.get("phases", []):
  289	        pk = p["id"]
  290	        items.append(_item(pk, "phase", None, p))
  291	        for s in p.get("slices", []):
  292	            items.append(_item(f"{pk}.{s['id']}", "slice", pk, s))
  293	    for c in doc.get("cross_cutting", []):
  294	        items.append(_item(c["id"], "x", None, c))
  295	    return items
  296	
  297	
  298	def item_from_cross(obj):
  299	    """A single archived cross-cutting item object
  300	    (from a '## Full cross-cutting JSON' block)."""
  301	    return _item(obj["id"], "x", None, obj)
  302	
  303	
  304	def collect(live_doc, archive_project_docs, archive_x_objects):
  305	    """Merge all sources into one item list. First occurrence of a key wins,
  306	    and live is read first, so live data shadows any stale archive copy."""
  307	    seen, items = set(), []
  308	    sources = [items_from_project(live_doc)]
  309	    sources += [items_from_project(d) for d in archive_project_docs]
  310	    sources += [[item_from_cross(o)] for o in archive_x_objects]
  311	    for source in sources:
  312	        for it in source:
  313	            if it.key not in seen:
  314	                seen.add(it.key)
  315	                items.append(it)
  316	    return items
  317	```
  318	
  319	- [ ] **Step 4: Run tests to verify they pass**
  320	
  321	Run: `python3 -m pytest tools/timeline/tests/test_model.py -q`
  322	Expected: all PASS
  323	
  324	- [ ] **Step 5: Commit**
  325	
  326	```bash
  327	git add tools/timeline
  328	git commit -m "X29: model.py — tracker date parsing and TimelineItem construction"
  329	```
  330	
  331	---
  332	
  333	### Task 3: `extract.py` — archive JSON block reading
  334	
  335	**Files:**
  336	- Create: `tools/timeline/extract.py`
  337	- Test: `tools/timeline/tests/test_extract_archives.py`
  338	
  339	- [ ] **Step 1: Write the failing tests**
  340	
  341	Create `tools/timeline/tests/test_extract_archives.py`:
  342	
  343	````python
  344	import json
  345	
  346	from timeline import extract
  347	from timeline.tests.helpers import doc, phase, x
  348	
  349	PHASE_MD = """# P3 — Old phase
  350	
  351	status: done
  352	closed: 2026-05-04
  353	
  354	## Slices
  355	
  356	- **S1** [done] — closed 2026-05-04 — something
  357	
  358	## Full phase JSON (for tasktool unarchive)
  359	
  360	```json
  361	{}
  362	```
  363	"""
  364	
  365	CROSS_MD = """# X7 — Old cross item
  366	
  367	status: done
  368	
  369	## Full cross-cutting JSON (for tasktool unarchive)
  370	
  371	```json
  372	{}
  373	```
  374	"""
  375	
  376	LEGACY_MD = """# P1 — Legacy phase ✅ `DONE 2026-04-29`
  377	
  378	## S1 — Old slice ✅ `DONE 2026-04-29`
  379	"""
  380	
  381	BROKEN_MD = """# P9 — Broken
  382	
  383	## Full phase JSON (for tasktool unarchive)
  384	
  385	```json
  386	{ this is not json
  387	```
  388	"""
  389	
  390	
  391	def _write_archives(tmp_path, files):
  392	    arch = tmp_path / "docs" / "archived-tasks"
  393	    arch.mkdir(parents=True)
  394	    for name, text in files.items():
  395	        (arch / name).write_text(text)
  396	    return tmp_path
  397	
  398	
  399	def test_reads_phase_and_cross_blocks(tmp_path):
  400	    p3 = doc(phases=[phase("P3", status="done", closed="2026-05-04")])
  401	    x7 = x("X7", status="done", closed="2026-05-05")
  402	    _write_archives(tmp_path, {
  403	        "P3-old.md": PHASE_MD.format(json.dumps(p3, indent=2)),
  404	        "X7-old.md": CROSS_MD.format(json.dumps(x7, indent=2)),
  405	        "P1-legacy.md": LEGACY_MD,
  406	    })
  407	    project_docs, x_objects, warnings = extract.read_archives(tmp_path)
  408	    assert [d["phases"][0]["id"] for d in project_docs] == ["P3"]
  409	    assert [o["id"] for o in x_objects] == ["X7"]
  410	    assert warnings == []  # legacy file silently ignored — it has no JSON block
  411	
  412	
  413	def test_unparseable_block_warns_not_fatal(tmp_path):
  414	    _write_archives(tmp_path, {"P9-broken.md": BROKEN_MD})
  415	    project_docs, x_objects, warnings = extract.read_archives(tmp_path)
  416	    assert project_docs == [] and x_objects == []
  417	    assert len(warnings) == 1 and "P9-broken.md" in warnings[0]
  418	
  419	
  420	def test_no_archive_dir_is_fine(tmp_path):
  421	    project_docs, x_objects, warnings = extract.read_archives(tmp_path)
  422	    assert (project_docs, x_objects, warnings) == ([], [], [])
  423	````
  424	
  425	- [ ] **Step 2: Run tests to verify they fail**
  426	
  427	Run: `python3 -m pytest tools/timeline/tests/test_extract_archives.py -q`
  428	Expected: FAIL — `ModuleNotFoundError` on `timeline.extract`
  429	
  430	- [ ] **Step 3: Implement the archive reader in `extract.py`**
  431	
  432	Create `tools/timeline/extract.py`:
  433	
  434	````python
  435	"""Read tracker data out of a repo: live file, archive JSON blocks, git replay."""
  436	
  437	from __future__ import annotations
  438	
  439	import json
  440	import re
  441	import subprocess
  442	from dataclasses import dataclass, field
  443	from pathlib import Path
  444	
  445	TRACKER = "docs/tasklist.json"
  446	
  447	_PHASE_BLOCK_RE = re.compile(
  448	    r"^## Full phase JSON.*?^```json\n(.*?)^```", re.S | re.M)
  449	_CROSS_BLOCK_RE = re.compile(
  450	    r"^## Full cross-cutting JSON.*?^```json\n(.*?)^```", re.S | re.M)
  451	
  452	
  453	def git(repo, *args, check=True):
  454	    proc = subprocess.run(["git", "-C", str(repo), *args],
  455	                          capture_output=True, text=True)
  456	    if check and proc.returncode != 0:
  457	        raise SystemExit(f"timeline: git {' '.join(args)} failed: "
  458	                         f"{proc.stderr.strip()}")
  459	    return proc.stdout
  460	
  461	
  462	def repo_root(path):
  463	    return Path(git(path, "rev-parse", "--show-toplevel").strip())
  464	
  465	
  466	def read_live(repo):
  467	    p = Path(repo) / TRACKER
  468	    if not p.exists():
  469	        raise SystemExit(f"timeline: {p} not found — not a tasktool project")
  470	    return json.loads(p.read_text())
  471	
  472	
  473	def read_archives(repo):
  474	    """-> (project_docs, x_objects, warnings).
  475	
  476	    Reads both '## Full phase JSON' blocks (a project-shaped object whose
  477	    `phases` array holds the archived phase) and '## Full cross-cutting JSON'
  478	    blocks (a single item object). Files with neither block (pure-legacy
  479	    markdown) are ignored — they are backfill.py's input, not ours.
  480	    """
  481	    project_docs, x_objects, warnings = [], [], []
  482	    arch = Path(repo) / "docs" / "archived-tasks"
  483	    files = sorted(arch.glob("*.md")) if arch.is_dir() else []
  484	    for f in files:
  485	        text = f.read_text()
  486	        pm = _PHASE_BLOCK_RE.search(text)
  487	        cm = _CROSS_BLOCK_RE.search(text)
  488	        try:
  489	            if pm:
  490	                project_docs.append(json.loads(pm.group(1)))
  491	            elif cm:
  492	                x_objects.append(json.loads(cm.group(1)))
  493	        except json.JSONDecodeError as e:
  494	            warnings.append(f"{f.name}: unparseable JSON block: {e}")
  495	    return project_docs, x_objects, warnings
  496	````
  497	
  498	- [ ] **Step 4: Run tests to verify they pass**
  499	
  500	Run: `python3 -m pytest tools/timeline/tests/test_extract_archives.py -q`
  501	Expected: all PASS
  502	
  503	- [ ] **Step 5: Commit**
  504	
  505	```bash
  506	git add tools/timeline
  507	git commit -m "X29: extract.py — archive phase and cross-cutting JSON block reader"
  508	```
  509	
  510	---
  511	
  512	### Task 4: `extract.py` — git replay
  513	
  514	**Files:**
  515	- Modify: `tools/timeline/extract.py` (append)
  516	- Test: `tools/timeline/tests/test_extract_replay.py`
  517	
  518	- [ ] **Step 1: Write the failing tests**
  519	
  520	Create `tools/timeline/tests/test_extract_replay.py`:
  521	
  522	```python
  523	import datetime as dt
  524	
  525	from timeline import extract
  526	from timeline.tests.helpers import doc, make_repo, phase, slice_, x
  527	
  528	
  529	def test_replay_records_transitions_with_commit_times(tmp_path):
  530	    s_ready = slice_("S1", status="ready", created="2026-06-01")
  531	    s_prog = slice_("S1", status="in_progress", created="2026-06-01")
  532	    s_done = slice_("S1", status="done", created="2026-06-01", closed="2026-06-02")
  533	    repo = make_repo(tmp_path, [
  534	        ("2026-06-01T10:00:00 +0000", doc(phases=[phase("P1", slices=[s_ready])])),
  535	        ("2026-06-01T15:30:00 +0000", doc(phases=[phase("P1", slices=[s_prog])])),
  536	        ("2026-06-02T09:45:00 +0000", doc(phases=[phase("P1", slices=[s_done])])),
  537	    ])
  538	    histories, warnings = extract.replay(repo)
  539	    assert warnings == []
  540	    ts = [(t.old, t.new) for t in histories["P1.S1"].transitions]
  541	    assert ts == [(None, "ready"), ("ready", "in_progress"), ("in_progress", "done")]
  542	    done = histories["P1.S1"].transitions[-1]
  543	    expected = int(dt.datetime(2026, 6, 2, 9, 45,
  544	                               tzinfo=dt.timezone.utc).timestamp())
  545	    assert done.ts == expected
  546	
  547	
  548	def test_replay_suppresses_import_artifacts(tmp_path):
  549	    # P0 arrives already done in the first commit: no usable transition.
  550	    imported = phase("P0", status="done", closed="2026-05-01")
  551	    repo = make_repo(tmp_path, [
  552	        ("2026-06-01T10:00:00 +0000", doc(phases=[imported])),
  553	    ])
  554	    histories, _ = extract.replay(repo)
  555	    assert "P0" not in histories
  556	
  557	
  558	def test_replay_skips_unparseable_revision(tmp_path):
  559	    repo = make_repo(tmp_path, [
  560	        ("2026-06-01T10:00:00 +0000", doc(phases=[phase("P1", status="ready")])),
  561	    ])
  562	    # Hand-commit a broken revision, then a good one.
  563	    import subprocess, os, json
  564	    (repo / "docs" / "tasklist.json").write_text("{ broken")
  565	    env = {**os.environ, "GIT_AUTHOR_DATE": "2026-06-01T11:00:00 +0000",
  566	           "GIT_COMMITTER_DATE": "2026-06-01T11:00:00 +0000"}
  567	    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
  568	    subprocess.run(["git", "commit", "-q", "-m", "broken"], cwd=repo, check=True,
  569	                   capture_output=True, env=env)
  570	    good = doc(phases=[phase("P1", status="done", closed="2026-06-01")])
  571	    (repo / "docs" / "tasklist.json").write_text(json.dumps(good))
  572	    env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = "2026-06-01T12:00:00 +0000"
  573	    subprocess.run(["git", "add", "-A"], cwd=repo, check=True, capture_output=True)
  574	    subprocess.run(["git", "commit", "-q", "-m", "good"], cwd=repo, check=True,
  575	                   capture_output=True, env=env)
  576	
  577	    histories, warnings = extract.replay(repo)
  578	    assert len(warnings) == 1 and "skipped unparseable" in warnings[0]
  579	    assert [t.new for t in histories["P1"].transitions] == ["ready", "done"]
  580	
  581	
  582	def test_replay_tracks_cross_items(tmp_path):
  583	    repo = make_repo(tmp_path, [
  584	        ("2026-06-01T10:00:00 +0000", doc(cross=[x("X1", status="ready")])),
  585	        ("2026-06-03T16:20:00 +0000",
  586	         doc(cross=[x("X1", status="done", closed="2026-06-03")])),
  587	    ])
  588	    histories, _ = extract.replay(repo)
  589	    assert [t.new for t in histories["X1"].transitions] == ["ready", "done"]
  590	```
  591	
  592	- [ ] **Step 2: Run tests to verify they fail**
  593	
  594	Run: `python3 -m pytest tools/timeline/tests/test_extract_replay.py -q`
  595	Expected: FAIL — `AttributeError: module ... has no attribute 'replay'`
  596	
  597	- [ ] **Step 3: Append the replayer to `extract.py`**
  598	
  599	```python
  600	@dataclass

[truncated: 1734 additional lines]

## Context Previews

### docs/specs/2026-06-06-X29-timeline-design.md

    1	# X29 — Visual work-history timeline generator (`tools/timeline`)
    2	
    3	**Date:** 2026-06-06
    4	**Status:** draft
    5	**Kind:** cross-cutting tool (human-facing; zero agent-context footprint)
    6	
    7	## Purpose
    8	
    9	A script that generates a browser-viewable visual timeline of completed work for any
   10	tasktool-managed project, intended as a visual aid when discussing progress with
   11	non-technical people. A vertical spine down the centre of a scrollable page represents
   12	project time from start to latest activity; phases and slices are the major and minor
   13	nodes on that spine, placed at their completion dates/times.
   14	
   15	## Constraints (binding)
   16	
   17	- **Zero agent-context overhead.** No skill, hook, CLAUDE.md entry, or tasktool help
   18	  line references this tool. It is invoked only by humans or on explicit request in
   19	  interactive sessions.
   20	- **Zero dependencies.** Python 3 stdlib only; git accessed via `subprocess`. No
   21	  third-party packages, matching the repo's zero-dependency philosophy.
   22	- **Generic.** Works on any repo with `docs/tasklist.json` (current tasktool schema),
   23	  not just this one. Primary target project today: `multistore`.
   24	- **Static output.** A single self-contained HTML file (inline CSS/JS/data). Opens via
   25	  `file://`, shareable as an attachment, no server.
   26	
   27	## Placement & architecture
   28	
   29	```
   30	tools/timeline/
   31	  timeline.py    # CLI entry
   32	  extract.py     # git replay + live tasklist.json + archive JSON blocks → raw events
   33	  model.py       # the ONE schema-aware module → normalized TimelineItem records
   34	  render.py      # TimelineItem records → self-contained HTML
   35	  backfill.py    # run-once legacy migrator (separate command; never invoked by timeline.py)
   36	```
   37	
   38	Sibling to `tools/tasktool`, **not** part of it (tasktool's CLI surface is unchanged).
   39	`model.py` is the deliberate seam: it is the only module that knows the tracker schema.
   40	If a shared tracker-model module is later extracted from tasktool, only `model.py`'s
   41	internals are replaced; `extract.py` and `render.py` consume `TimelineItem` records and
   42	do not move.
   43	
   44	### CLI
   45	
   46	```
   47	python3 tools/timeline/timeline.py [--repo PATH] [-o timeline.html] [--show-x] [--overrides PATH]
   48	python3 tools/timeline/backfill.py [--repo PATH] [--write]
   49	```
   50	
   51	- `--repo` defaults to the current working directory's repo root (`git rev-parse --show-toplevel`).
   52	- `-o` defaults to `timeline.html` in the current directory.
   53	- `--show-x` sets the X-item toggle's initial state to on (data is embedded either way).
   54	- `--overrides` defaults to `docs/timeline-overrides.json` in the target repo if present.
   55	- `backfill.py` is dry-run by default, printing a unified diff; `--write` applies it.
   56	
   57	## Data model
   58	
   59	```python
   60	TimelineItem:
   61	  key            # "P21", "P21.S4", "X13"
   62	  kind           # phase | slice | x
   63	  parent         # phase key for slices, None otherwise
   64	  title          # verbatim tracker title
   65	  display_title  # optional override relabel; renderer prefers it when present
   66	  status         # done | cancelled | ready | in_progress | blocked ...
   67	  created, started, closed   # each: (datetime|None, precision, source)
   68	                             # precision: day | minute
   69	                             # source:    field | replay | override
   70	```
   71	
   72	## Date resolution (precedence)
   73	
   74	For each of `created`/`started`/`closed` on each item:
   75	
   76	1. **Overrides file** (`docs/timeline-overrides.json`, optional) — always wins. Schema:
   77	
   78	   ```json
   79	   {
   80	     "items": {
   81	       "P14":    { "started": "2026-05-20" },
   82	       "P21.S2": { "display_title": "Quiet-launch controls" },
   83	       "X12":    { "exclude": true }
   84	     }
   85	   }
   86	   ```
   87	
   88	   Values: ISO date or datetime for the three date fields; `display_title` string;
   89	   `exclude` boolean. Unknown keys in an item entry are an error (fail loud, not silent).
   90	
   91	2. **Tracker JSON fields** — the authoritative *date* (day precision). Sources: the live
   92	   `docs/tasklist.json` plus every archive file's fenced JSON block under
   93	   `docs/archived-tasks/` — `## Full phase JSON` blocks for archived phases (a full
   94	   project-shaped object whose `phases` array holds the phase) **and** `## Full
   95	   cross-cutting JSON` blocks for archived X-items (a single item object). Both shapes
   96	   are required reading; dropping the cross-cutting blocks would leave the X toggle
   97	   mostly empty on mature projects. The placeholder `1970-01-01` is treated as absent.
   98	   Where two archive files exist for the same phase (legacy + tasktool re-archive), the
   99	   one with a parseable JSON block wins; pure-legacy markdown files are ignored by
  100	   `timeline.py` (they are `backfill.py`'s input, not the renderer's).
  101	
  102	3. **Git replay** — walk every commit touching `docs/tasklist.json` oldest→newest
  103	   (`git log --reverse --format=%H %ct -- docs/tasklist.json`), parse the file at each
  104	   revision (`git show SHA:docs/tasklist.json`), and record **status transitions** per
  105	   item with the commit timestamp. Date *fields* are deliberately not change-tracked:
  106	   their final values are read once from the current file (rule 2) and are already
  107	   authoritative for the date — replay's only job is supplying transition timing.
  108	   Replay:
  109	   - upgrades a field date to **minute precision** when the replay-observed transition
  110	     falls on the same calendar day;
  111	   - fills a field that is null in the tracker (e.g. missing `started`: first transition
  112	     to `in_progress`/`started`; missing phase `closed` is *not* invented — an open phase
  113	     renders as open);
  114	   - **ignores transitions observed at an item's first-appearance commit when the item
  115	     appears already terminal** (import artifacts — e.g. the 2026-05-18 multistore
  116	     migration commit where P1–P12 arrived `done`).
  117	
  118	Validated against multistore: 226 commits replay with zero parse failures, yielding
  119	minute-precision lifecycles for 108 items.
  120	
  121	### Derived phase span
  122	
  123	- Phase start for rendering = `started` if present, else earliest slice `started`, else
  124	  phase `created`.
  125	- Phase end = `closed` if present, else open (strand runs to the bottom edge labelled
  126	  with the generation date).
  127	- **Close-only items** (no resolvable start or create — e.g. legacy P1 with
  128	  `created: 1970-01-01`, `started: null`, no slices): render as a close node only — a
  129	  zero-length span with the hollow close ring and label, no strand segment. This is a
  130	  supported display mode, not an error; backfill/overrides can later supply a start.
  131	
  132	## Visual specification
  133	
  134	Validated interactively against real multistore data (P20–P23).
  135	
  136	- **Spine braid.** Vertical centre spine; one coloured strand per open phase. When N
  137	  phases are open concurrently, N strands sit side-by-side. When no phase is open, a
  138	  dotted grey strand bridges the gap with an "N quiet days" label. Phase colours come
  139	  from a fixed palette cycled by phase number (stable across regenerations).
  140	- **Nodes.** Phase start = filled disc in phase colour + bold title and start date.
  141	  Phase close = hollow ring in phase colour (grey ring for cancelled phases) + "PNN
  142	  complete · date" label. Slice completion = small filled disc in phase colour.
  143	- **Cards.** Each slice gets an info card tinted with the parent phase colour
  144	  (background tint + border), showing title (or `display_title`) and completion
  145	  date/time. Day-precision dates show no time-of-day (never a fake "00:00").
  146	  During solo stretches cards alternate left/right; during overlaps each open phase
  147	  owns one side so a track reads as a column. With 3+ concurrent phases the braid
  148	  gains strands; cards keep phase colours for attribution.
  149	- **Click-to-expand.** Clicking a card expands it in place: full verbatim title, item
  150	  ID, started/closed datetimes with precision markers, computed duration.
  151	- **Time scale: proportional with guard rails.** Vertical distance is proportional to
  152	  elapsed time, subject to (a) a minimum spacing between adjacent nodes — burst days
  153	  expand locally to stay readable — and (b) a maximum rendered height for empty
  154	  stretches — long gaps compress to a capped dotted segment with the quiet-days label.
  155	- **Cancelled items.** A cancelled phase is omitted unless it has ≥1 `done` slice; when
  156	  shown it renders normally (grey close ring), with only its completed slices.
  157	  Cancelled slices are always omitted.
  158	- **X-items.** First-class: always extracted and embedded. Rendered as neutral slate
  159	  nodes/cards on the spine at their completion time (they have no parent phase colour).
  160	  An in-page toggle shows/hides them instantly without regeneration; `--show-x` only
  161	  sets the toggle's initial state. Open/never-completed X-items are not rendered.
  162	- **Header.** Project name, overall date span, totals (phases completed, slices
  163	  completed), generation timestamp, and a colour legend of phases.
  164	
  165	## Legacy backfill (`backfill.py`)
  166	
  167	One-time, per-project migration for items that predate the tracker. It exists so that
  168	`timeline.py` never grows legacy parsing paths.
  169	
  170	- **Input:** legacy archive markdown under `docs/archived-tasks/` (headings of the form
  171	  `## S1 — title ✅ \`DONE 2026-04-29\``) and the repo's commit subjects.
  172	- **Recovers:** slice titles and close dates from the markdown; phase/slice `started`
  173	  dates from first-commit-mention mining (`\bP(\d+)(?:[.\-]?S(\d+))?\b` over subjects),
  174	  cross-checked against the previous phase's close for the sequential legacy era.
  175	- **Writes:** recovered slices and dates into the corresponding tasktool archive file's
  176	  `## Full phase JSON` block — the canonical location `tasktool unarchive` understands.
  177	  Phase-level fields already present are never overwritten.
  178	- **Safety:** dry-run by default with a unified diff; `--write` applies; the human
  179	  reviews and commits. Never invoked by `timeline.py`.
  180	
  181	Multistore evidence: legacy P1–P12 have reliable close dates in archives; commit mining
  182	dates P2–P12 starts cleanly; P1 has no commit mentions, so its `started` will need a
  183	manual override entry (or remain start-unknown, rendering from its close date only).
  184	
  185	## Error handling
  186	
  187	- Not a git repo / no `docs/tasklist.json` → clear fatal error.
  188	- A historical revision that fails JSON parsing → skipped with a stderr warning; replay
  189	  continues (validated: 0/226 failures on multistore, but schema drift must not be fatal).
  190	- Shallow clone → replay covers what exists; items degrade to day precision with a
  191	  one-line warning.
  192	- Unknown schema fields → ignored (tolerant reader); unknown override keys → fatal.
  193	- Items with no resolvable dates at all → listed in a stderr summary so gaps are
  194	  visible, omitted from the render. No silent drops.
  195	
  196	## Testing
  197	
  198	`tools/timeline/tests/` (pytest, mirroring tasktool's convention). **`tools/timeline/tests`
  199	must be added to `testpaths` in the repo's `pyproject.toml`** so the default
  200	`python3 -m pytest` gate discovers it — otherwise "all tests pass" is vacuously true.

[truncated: 34 additional lines]
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

[truncated: 239 additional lines]
### docs/handoffs/2026-06-06-X29-slice-close-note.md

    1	# X29 slice-close note — evidence for post-slice review
    2	
    3	Implementation of `docs/plans/2026-06-06-X29-timeline-generator.md` (14 TDD tasks) is complete on branch `worktree-x29-visual-work-history-timeline-generator`. Each task went through implementer → spec-compliance review → code-quality review. This note records the authorized deviations from the plan's verbatim code (all review-driven, all tested) and the acceptance evidence, so they are not mistaken for drift.
    4	
    5	## Review-driven deviations from the plan's verbatim listings
    6	
    7	1. **T5 (`model.py` replay merge)** — `closed` picks the LAST terminal transition via `reversed()`, making reopen sequences safe. Regression test added.
    8	2. **T6 (`model.py` overrides)** — fail-loud validation of override value types: non-string/null dates, non-bool `exclude`, non-str `display_title` all `SystemExit`. Tests added.
    9	3. **T10 (`render.py` HTML emission)** — close-ring label includes the phase title (`{key} — {title} {label} · {date}`). Necessary: a close-only phase renders only a ring, and the plan's own test asserts the title appears in the HTML; verified the plan-verbatim code fails its own test. Also one cosmetic, behaviorally-identical rewording (`strftime` call instead of f-string format spec) at the `span_text` line.
   10	4. **T11 (`test_cli.py`)** — `test_end_to_end` pinned to `TZ=UTC` via a local `utc_tz` fixture (monkeypatch + `time.tzset()`, restored on teardown). The plan's test was empirically TZ-flaky: minute-precision upgrade depends on the replay timestamp's local calendar date, so the test failed deterministically at UTC+8 and beyond.
   11	5. **T13 pre-fix (`backfill.py`)** — `_PHASE_HEAD_RE` backticks made optional: multistore's real legacy `P3-editor-grade-cms.md` heading has no backticks around `DONE 2026-05-04` and was silently dropped. Regression test added.
   12	6. **T13 (`backfill.py` rewrite)** — two bugs in the plan's prescribed logic, found by empirical dry-runs against this repo and multistore:
   13	   - started-fill could produce `started > closed` (clamp uses "latest close among all lower-numbered phases", wrong once phases ran in parallel; raw mined dates can also postdate retroactive closes). Guard added: skip the fill when the candidate exceeds the object's own `closed`. 6 real bad entries across the two repos eliminated; 3 regression tests.
   14	   - `json.dumps` lacked `ensure_ascii=False`, deviating from tasktool's canonical serializer and churning untouched `—`/`✅` lines in dry-run diffs. Fixed; regression test.
   15	
   16	## Known, deliberately deferred limitations (documented, not bugs introduced)
   17	
   18	- `_SLICE_HEAD_RE` only matches `## S<n> — title ✅ \`DONE date\``-style headings. Real multistore legacy archives also use h3 headings, alphanumeric slice IDs (`S2a`), and bullet-list slices, mostly date-less — those are not backfilled. Broadening was descoped as design work beyond a review fix; multistore backfill is dry-run-only in this repo and gated by the human eyeball checkpoint (plan Task 14 Step 5). Phase-level closes — the load-bearing datum — are recovered for 8/8 multistore legacy phases after deviation 5.
   19	- Minor quality-review nits deferred as plan errata: malformed-overrides JSON and missing output dir produce raw tracebacks in `timeline.py`; `read_text`/`write_text` use locale default encoding in `backfill.py`; `test_existing_slices_not_touched` has a conditional assert; `plan_rewrites` docstring slightly over-narrows the started-fill scope.
   20	
   21	## Acceptance evidence (plan Task 14)
   22	
   23	- Timeline suite: 73/73 passed.
   24	- Full default-discovery suite from the worktree: 1070 passed, 109 failed + 23 errors — **byte-identical failing set to a clean clone of `main`** (independently verified): all pre-existing in tasktool worktree/tracker suites, none in `tools/timeline`, zero X29-introduced. X29's only non-`tools/timeline/` change is the pyproject `testpaths`/`pythonpath` addition, whose collection delta is exactly the 73 new tests.
   25	- Rendered this repo (`/tmp/superstar-timeline.html`, exit 0) and multistore (`/tmp/multistore-timeline.html`, exit 0; 13 `phase-node`s ≥ 10, minute-precision `15:51` present, `x-node` markup present).
   26	- Backfill dry-run vs multistore: 17 file diffs, zero `started > closed`, zero unicode-escape churn, both repos verified unmutated.
   27	- Human browser eyeball of both HTML files: requested from the human partner, pending in parallel with this review.
   28	
   29	## Hard-constraint conformance
   30	
   31	- Python 3 stdlib only; git via subprocess. Verified no third-party imports.
   32	- No skill, hook, CLAUDE.md, or tasktool-help reference to the tool.
   33	- Output HTML single-file, self-contained (tested: no `http://`/`https://`/`src=`).
   34	- `timeline.py` read-only (verified empirically); only `backfill.py --write` mutates archive files, and `--write` was never run against any real repo.

<!-- superstar-prompt:end -->