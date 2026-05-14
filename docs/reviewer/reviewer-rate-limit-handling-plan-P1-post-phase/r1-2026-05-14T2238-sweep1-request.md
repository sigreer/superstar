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
/home/simon/Dev/sigreer/skills/superstar

Target kind:
post-phase

Review mode:
Post-phase review. Treat this as a closeout gate for a whole
phase. Compare the implementation, archive/TASKLIST updates, and verification
evidence against the phase spec/plan. Prioritize: unresolved acceptance
criteria, stale docs, missing archive notes, cross-cutting tracker drift,
deferred gates without justification, and regressions outside the phase scope.

Target document:
docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md

Additional context files:
- docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md

Review output contract:
1. Findings
   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
     stable if this review is iterated in subsequent rounds.
   - Mark severity inline: `Severity: blocking | important | minor | nit`.
2. Open questions / assumptions
3. Suggested document edits
4. Verification gaps / commands that should be run, if any
5. Overall verdict: one of "ready", "ready with small edits", or "revise"

Read the files from disk. Do not rely only on the snippets in this prompt.


## Target Preview

### docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md

    1	# Reviewer rate-limit handling — implementation plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Make `external-reviewer.py` detect third-party reviewer usage caps, persist a global flag across sessions, refuse to spawn while limited, and give the operator three named recovery paths plus a hold.
    6	
    7	**Architecture:** Two layers. CLI layer detects/persists/refuses and exits with a new code 8 carrying a JSON payload. Coordinator layer in `SKILL.md` documents the four-option menu and dispatches each path. Rate-limited rounds are first-class chain entries that bypass the resolution gate, get skipped by preamble walk-back, and are excluded from merged verdicts — symmetrically with the existing `failed` round treatment.
    8	
    9	**Tech Stack:** Python stdlib only (`fcntl`, `json`, `re`, `datetime`, `argparse`, `pathlib`). pytest for testing.
   10	
   11	**Reference:** Spec at `docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md`. The spec is authoritative; this plan implements it task-by-task.
   12	
   13	---
   14	
   15	## Files at a glance
   16	
   17	| Path | Action | Purpose |
   18	|---|---|---|
   19	| `skills/external-review/scripts/external-reviewer.py` | Modify | Add state primitives, detection, pre-spawn check, exit-8, four new subcommands, 4-site status semantics, refusal coalescing. |
   20	| `skills/external-review/SKILL.md` | Modify | Document the new exit code, the menu, dispatch paths. |
   21	| `skills/external-review/tests/test_state_file.py` | Create | State file primitives. |
   22	| `skills/external-review/tests/test_rate_limit_detection.py` | Create | `detect_rate_limit` regex coverage. |
   23	| `skills/external-review/tests/test_reset_time_parser.py` | Create | Reset-time parser corner cases. |
   24	| `skills/external-review/tests/test_exit_code_8.py` | Create | End-to-end rate-limit detection → exit 8 → state. |
   25	| `skills/external-review/tests/test_subsequent_invocation_refused.py` | Create | Pre-spawn refusal path. |
   26	| `skills/external-review/tests/test_refusal_coalescing.py` | Create | Coalescing onto head rate-limited round. |
   27	| `skills/external-review/tests/test_rate_limited_status_semantics.py` | Create | Resolution gate, preamble walk-back, merged-verdict filter, write_merged_findings. |
   28	| `skills/external-review/tests/test_sweep_partial_rate_limit.py` | Create | Primary ok, sweep rate-limited → round still ok, state written. |
   29	| `skills/external-review/tests/test_manual_approve_subcommand.py` | Create | manual-approve subcommand. |
   30	| `skills/external-review/tests/test_ingest_response_subcommand.py` | Create | ingest-response with paste + link, reformat rules. |
   31	| `skills/external-review/tests/test_show_clear_limit.py` | Create | show-limit + clear-limit subcommands. |
   32	
   33	## Conventions used throughout the plan
   34	
   35	- **TDD-first.** Every task writes a failing test, runs it, sees it fail, implements minimal code, runs it, sees it pass, commits.
   36	- **Importing the script.** All new tests use the existing fixture pattern (the script has a hyphen in its filename so it can't be imported directly):
   37	  ```python
   38	  from pathlib import Path
   39	  import sys, importlib.util
   40	  SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
   41	  sys.path.insert(0, str(SCRIPTS))
   42	  spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
   43	  er = importlib.util.module_from_spec(spec)
   44	  spec.loader.exec_module(er)
   45	  ```
   46	- **State file isolation.** Every test that touches state MUST set `AGENT_REVIEWER_STATE_FILE` to a `tmp_path`-scoped file before importing/invoking script code:
   47	  ```python
   48	  @pytest.fixture(autouse=True)
   49	  def _isolated_state(tmp_path, monkeypatch):
   50	      monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "reviewer-state.json"))
   51	  ```
   52	  This fixture goes at the top of every new test file. Existing tests don't need it (they don't touch state).
   53	- **Commit cadence.** Each task ends in exactly one commit. Commit messages follow the existing `external-reviewer: <imperative summary>` style.
   54	- **No push.** This work is local-only until the user explicitly asks.
   55	
   56	## Spec → Plan mapping
   57	
   58	| Spec section | Implemented by |
   59	|---|---|
   60	| §5 State file (path, override, expiry, flock) | S1 Tasks 1.1–1.3 |
   61	| §6 Detection + reset-time parsing | S1 Tasks 1.4–1.5 |
   62	| §5 `--state-file` on `review` subcommand (argparse refactor) | S2 Task 2.0 (new) |
   63	| §7.1 Pre-spawn check | S2 Tasks 2.1–2.2 (renumbered from 2.1–2.2, shifted by T2.0) |
   64	| §7.2 Post-failure detection | S2 Task 2.3 (was 2.3) |
   65	| §7.3 Exit code 8 JSON payload | S2 Tasks 2.1 + 2.5 |
   66	| §7.4 Rate-limited status semantics | S3 (Tasks 3.1–3.4) |
   67	| §7.5 Coalescing | S4 (Tasks 4.1–4.2) |
   68	| §7.6 Subcommands | S5 (Tasks 5.1–5.5) |
   69	| §8 Coordinator integration / SKILL.md | S6 (Tasks 6.1–6.3) |
   70	| §9 Tests | Threaded through every slice |
   71	| §11 Acceptance | S7 (Tasks 7.1–7.2) |
   72	
   73	**Numbering note (r2 fixes):** A new Task 2.0 was inserted at the start of Slice 2. Existing tasks 2.1–2.5 retain their numbers. The new task adds ~2 tests; test-count progressions throughout the plan are updated accordingly.
   74	
   75	---
   76	
   77	## Slice 1 — State file primitives + detection
   78	
   79	This slice produces pure functions with unit tests. The script's existing behaviour is unchanged at slice close.
   80	
   81	### Task 1.1: State file load with env-var override + fail-open
   82	
   83	**Files:**
   84	- Modify: `skills/external-review/scripts/external-reviewer.py` (add module-level helpers near the top, immediately after the existing `cap_with_elision` definition)
   85	- Create: `skills/external-review/tests/test_state_file.py`
   86	
   87	- [x] **Step 1: Write the failing test**
   88	
   89	```python
   90	# skills/external-review/tests/test_state_file.py
   91	import json
   92	import os
   93	from pathlib import Path
   94	import sys
   95	import importlib.util
   96	import pytest
   97	
   98	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
   99	sys.path.insert(0, str(SCRIPTS))
  100	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
  101	er = importlib.util.module_from_spec(spec)
  102	spec.loader.exec_module(er)
  103	
  104	
  105	@pytest.fixture(autouse=True)
  106	def _isolated_state(tmp_path, monkeypatch):
  107	    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(tmp_path / "reviewer-state.json"))
  108	
  109	
  110	def test_state_path_uses_env_override(tmp_path, monkeypatch):
  111	    target = tmp_path / "custom-state.json"
  112	    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(target))
  113	    assert er.state_file_path() == target
  114	
  115	
  116	def test_load_state_missing_file_returns_empty():
  117	    state = er.load_state()
  118	    assert state == {"schema_version": 1, "limits": {}}
  119	
  120	
  121	def test_load_state_round_trip(tmp_path):
  122	    target = Path(os.environ["AGENT_REVIEWER_STATE_FILE"])
  123	    target.write_text(json.dumps({"schema_version": 1, "limits": {"reviewer-agent": {"limited": True}}}))
  124	    state = er.load_state()
  125	    assert state["limits"]["reviewer-agent"]["limited"] is True
  126	
  127	
  128	def test_load_state_corrupt_file_fails_open(capsys, tmp_path):
  129	    target = Path(os.environ["AGENT_REVIEWER_STATE_FILE"])
  130	    target.write_text("{not json")
  131	    state = er.load_state()
  132	    assert state == {"schema_version": 1, "limits": {}}
  133	    captured = capsys.readouterr()
  134	    assert "reviewer-state.json" in captured.err  # warning surfaced
  135	```
  136	
  137	- [x] **Step 2: Run tests to verify they fail**
  138	
  139	Run: `python3 -m pytest skills/external-review/tests/test_state_file.py -v`
  140	Expected: AttributeError — `state_file_path` and `load_state` don't exist.
  141	
  142	- [x] **Step 3: Implement `state_file_path` and `load_state`**
  143	
  144	In `skills/external-review/scripts/external-reviewer.py`, immediately after the `cap_with_elision` function, add:
  145	
  146	```python
  147	DEFAULT_STATE_FILE = Path.home() / ".config" / "superstar" / "reviewer-state.json"
  148	
  149	
  150	def state_file_path() -> Path:
  151	    override = os.environ.get("AGENT_REVIEWER_STATE_FILE")
  152	    if override:
  153	        return Path(override)
  154	    return DEFAULT_STATE_FILE
  155	
  156	
  157	def load_state() -> dict:
  158	    """Read the reviewer state file. Fails open: missing/corrupt → empty state."""
  159	    path = state_file_path()
  160	    if not path.exists():
  161	        return {"schema_version": 1, "limits": {}}
  162	    try:
  163	        data = json.loads(path.read_text(encoding="utf-8"))
  164	        if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("limits"), dict):
  165	            raise ValueError("schema mismatch")
  166	        return data
  167	    except (json.JSONDecodeError, ValueError, OSError) as e:
  168	        print(f"WARNING: reviewer-state.json at {path} unreadable ({e}); treating as empty", file=sys.stderr)
  169	        return {"schema_version": 1, "limits": {}}
  170	```
  171	
  172	If `os` or `json` aren't already imported at module top, add them.
  173	
  174	- [x] **Step 4: Run tests**
  175	
  176	Run: `python3 -m pytest skills/external-review/tests/test_state_file.py -v`
  177	Expected: 4 passed.
  178	
  179	- [x] **Step 5: Commit**
  180	
  181	```bash
  182	git add skills/external-review/scripts/external-reviewer.py \
  183	        skills/external-review/tests/test_state_file.py
  184	git commit -m "external-reviewer: state file primitive (load with env override, fail-open)"
  185	```
  186	
  187	---
  188	
  189	### Task 1.2: State file save with flock + atomic write + 0700 parent
  190	
  191	**Files:**
  192	- Modify: `skills/external-review/scripts/external-reviewer.py` (continue in the state-primitives block)
  193	- Modify: `skills/external-review/tests/test_state_file.py`
  194	
  195	- [x] **Step 1: Write the failing tests** (append to `test_state_file.py`)
  196	
  197	```python
  198	def test_save_state_creates_parent_dir_0700(tmp_path, monkeypatch):
  199	    target = tmp_path / "nested" / "deep" / "state.json"
  200	    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(target))
  201	    er.save_state({"schema_version": 1, "limits": {"reviewer-agent": {"limited": True}}})
  202	    assert target.exists()
  203	    # Parent dir permissions: 0o700 (owner rwx, nothing else)
  204	    parent_mode = oct(target.parent.stat().st_mode & 0o777)
  205	    assert parent_mode == "0o700"
  206	
  207	
  208	def test_save_state_round_trip():
  209	    er.save_state({"schema_version": 1, "limits": {"reviewer-agent": {"limited": True, "reset_at": "2026-05-14T18:48:00"}}})
  210	    out = er.load_state()
  211	    assert out["limits"]["reviewer-agent"]["reset_at"] == "2026-05-14T18:48:00"
  212	
  213	
  214	def test_save_state_atomic_via_tmp_rename(tmp_path, monkeypatch):
  215	    """Writing should go through a .tmp file then rename, so a crash mid-write
  216	    can never corrupt the on-disk state."""
  217	    target = tmp_path / "state.json"
  218	    monkeypatch.setenv("AGENT_REVIEWER_STATE_FILE", str(target))
  219	    target.write_text('{"schema_version": 1, "limits": {"reviewer-agent": {"limited": false}}}')
  220	    er.save_state({"schema_version": 1, "limits": {"reviewer-agent": {"limited": True}}})
  221	    # After save, no orphan .tmp file remains
  222	    assert not (tmp_path / "state.json.tmp").exists()
  223	    assert er.load_state()["limits"]["reviewer-agent"]["limited"] is True
  224	```
  225	
  226	- [x] **Step 2: Verify they fail**
  227	
  228	Run: `python3 -m pytest skills/external-review/tests/test_state_file.py -v`
  229	Expected: 3 new tests fail (`save_state` doesn't exist).
  230	
  231	- [x] **Step 3: Implement `save_state`**
  232	
  233	Append to the state-primitives block in `external-reviewer.py`:
  234	
  235	```python
  236	import fcntl  # add at module top if not already present
  237	
  238	def save_state(state: dict) -> None:
  239	    """Atomically write the reviewer state file. Uses flock + tmp-then-rename.
  240	    Creates parent dir with mode 0o700 on first write."""
  241	    path = state_file_path()
  242	    path.parent.mkdir(parents=True, exist_ok=True)
  243	    try:
  244	        path.parent.chmod(0o700)
  245	    except OSError:
  246	        pass  # best-effort; some filesystems disallow chmod
  247	    tmp_path = path.with_suffix(path.suffix + ".tmp")
  248	    payload = json.dumps(state, indent=2, sort_keys=True)
  249	    with open(tmp_path, "w", encoding="utf-8") as f:
  250	        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
  251	        f.write(payload)
  252	        f.flush()
  253	        os.fsync(f.fileno())
  254	        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
  255	    os.replace(tmp_path, path)
  256	```
  257	
  258	- [x] **Step 4: Run tests**
  259	
  260	Run: `python3 -m pytest skills/external-review/tests/test_state_file.py -v`
  261	Expected: all 7 pass.
  262	
  263	- [x] **Step 5: Commit**
  264	
  265	```bash
  266	git add skills/external-review/scripts/external-reviewer.py \
  267	        skills/external-review/tests/test_state_file.py
  268	git commit -m "external-reviewer: state file atomic save with flock + 0700 parent"
  269	```
  270	
  271	---
  272	
  273	### Task 1.3: State expiry-on-read
  274	
  275	**Files:**
  276	- Modify: `skills/external-review/scripts/external-reviewer.py`
  277	- Modify: `skills/external-review/tests/test_state_file.py`
  278	
  279	- [x] **Step 1: Write the failing test**
  280	
  281	Append to `test_state_file.py`:
  282	
  283	```python
  284	import datetime as dt
  285	
  286	
  287	def test_get_active_limit_expires_past_reset(monkeypatch):
  288	    past = (dt.datetime.now() - dt.timedelta(hours=1)).isoformat(timespec="seconds")
  289	    er.save_state({"schema_version": 1, "limits": {"reviewer-agent": {
  290	        "limited": True, "reset_at": past, "limited_at": past, "reset_source": "test",
  291	        "raw_stderr_tail": "", "chain": "x", "round": 1
  292	    }}})
  293	    # get_active_limit clears expired entries in-place and returns None.
  294	    assert er.get_active_limit("reviewer-agent") is None
  295	    # The state file should now show limits={} for reviewer-agent (entry removed).
  296	    assert "reviewer-agent" not in er.load_state()["limits"]
  297	
  298	
  299	def test_get_active_limit_returns_live_entry():
  300	    future = (dt.datetime.now() + dt.timedelta(hours=1)).isoformat(timespec="seconds")
  301	    er.save_state({"schema_version": 1, "limits": {"reviewer-agent": {
  302	        "limited": True, "reset_at": future, "limited_at": "x", "reset_source": "t",
  303	        "raw_stderr_tail": "", "chain": "c", "round": 1
  304	    }}})
  305	    entry = er.get_active_limit("reviewer-agent")
  306	    assert entry is not None
  307	    assert entry["reset_at"] == future
  308	
  309	
  310	def test_get_active_limit_no_entry_returns_none():
  311	    assert er.get_active_limit("reviewer-agent") is None
  312	```
  313	
  314	- [x] **Step 2: Verify they fail**
  315	
  316	Run: `python3 -m pytest skills/external-review/tests/test_state_file.py -v`
  317	Expected: 3 new tests fail (`get_active_limit` doesn't exist).
  318	
  319	- [x] **Step 3: Implement `get_active_limit`**
  320	
  321	Append:
  322	
  323	```python
  324	def get_active_limit(reviewer_cmd_basename: str) -> dict | None:
  325	    """Return the limit entry for the given reviewer if it's still active.
  326	    Side effect: if the entry exists but `reset_at <= now()`, clear it from
  327	    the state file and return None.
  328	    """
  329	    state = load_state()
  330	    entry = state["limits"].get(reviewer_cmd_basename)
  331	    if not entry or not entry.get("limited"):
  332	        return None
  333	    try:
  334	        reset_at = dt.datetime.fromisoformat(entry["reset_at"])
  335	    except (KeyError, ValueError, TypeError):
  336	        # Treat malformed entries as expired, prune them.
  337	        state["limits"].pop(reviewer_cmd_basename, None)
  338	        save_state(state)
  339	        return None
  340	    if reset_at <= dt.datetime.now():
  341	        state["limits"].pop(reviewer_cmd_basename, None)
  342	        save_state(state)
  343	        return None
  344	    return entry
  345	```
  346	
  347	Add `import datetime as dt` at module top if not already present.
  348	
  349	- [x] **Step 4: Run tests**
  350	
  351	Expected: 10 passed in `test_state_file.py`.
  352	
  353	- [x] **Step 5: Commit**
  354	
  355	```bash
  356	git add skills/external-review/scripts/external-reviewer.py \
  357	        skills/external-review/tests/test_state_file.py
  358	git commit -m "external-reviewer: state expiry-on-read prunes stale limits"
  359	```
  360	
  361	---
  362	
  363	### Task 1.4: `detect_rate_limit` with built-in patterns + env extension
  364	
  365	**Files:**
  366	- Modify: `skills/external-review/scripts/external-reviewer.py`
  367	- Create: `skills/external-review/tests/test_rate_limit_detection.py`
  368	
  369	- [x] **Step 1: Write the failing tests**
  370	
  371	```python
  372	# skills/external-review/tests/test_rate_limit_detection.py
  373	from pathlib import Path
  374	import sys, importlib.util
  375	import pytest
  376	
  377	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
  378	sys.path.insert(0, str(SCRIPTS))
  379	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
  380	er = importlib.util.module_from_spec(spec)
  381	spec.loader.exec_module(er)
  382	
  383	
  384	CODEX_STDERR = (
  385	    "ERROR: You've hit your usage limit. Upgrade to Pro "
  386	    "(https://chatgpt.com/explore/pro), visit https://chatgpt.com/codex/settings/usage "
  387	    "to purchase more credits or try again at 6:48 PM.\n"
  388	)
  389	
  390	
  391	def test_codex_sample_matches():
  392	    matched, _reset_at, name = er.detect_rate_limit(CODEX_STDERR)
  393	    assert matched is True
  394	    assert name == "codex_usage_limit"
  395	
  396	
  397	def test_codex_sample_extracts_time_group():
  398	    matched, reset_at, _ = er.detect_rate_limit(CODEX_STDERR)
  399	    assert matched is True
  400	    # 6:48 PM → 18:48 in 24h
  401	    assert reset_at.hour == 18
  402	    assert reset_at.minute == 48
  403	
  404	
  405	def test_unmatched_stderr_returns_falsey():
  406	    matched, reset_at, name = er.detect_rate_limit("Traceback ...\nValueError: foo\n")
  407	    assert matched is False
  408	    assert reset_at is None
  409	    assert name is None
  410	
  411	
  412	def test_user_pattern_via_env(monkeypatch):
  413	    monkeypatch.setenv(
  414	        "AGENT_REVIEWER_RATE_LIMIT_PATTERNS",
  415	        r"my_backend=ERROR limit hit until (\d{1,2}:\d{2})",
  416	    )
  417	    matched, reset_at, name = er.detect_rate_limit("ERROR limit hit until 14:30")
  418	    assert matched is True
  419	    assert name == "my_backend"
  420	    assert reset_at is not None and reset_at.hour == 14 and reset_at.minute == 30
  421	```
  422	
  423	- [x] **Step 2: Verify they fail**
  424	
  425	Run: `python3 -m pytest skills/external-review/tests/test_rate_limit_detection.py -v`
  426	Expected: AttributeError — `detect_rate_limit` doesn't exist.
  427	
  428	- [x] **Step 3: Implement `detect_rate_limit`**
  429	
  430	Append to `external-reviewer.py` (after the state primitives):
  431	
  432	```python
  433	RATE_LIMIT_BUILTIN_PATTERNS = [
  434	    ("codex_usage_limit",
  435	     re.compile(r"You've hit your usage limit.*?try again at (\d{1,2}:\d{2}\s*(?:AM|PM)?)", re.IGNORECASE | re.DOTALL)),
  436	    ("claude_cli_rate_limit",
  437	     re.compile(r"(?:rate limit|rate-limited).*?reset (?:at|in)? ?(.+?)$", re.IGNORECASE | re.MULTILINE)),
  438	    ("gemini_cli_rate_limit",
  439	     re.compile(r"quota exceeded.*?retry (?:after|at) (.+?)$", re.IGNORECASE | re.MULTILINE)),
  440	]
  441	
  442	
  443	def _user_patterns_from_env() -> list[tuple[str, re.Pattern]]:
  444	    raw = os.environ.get("AGENT_REVIEWER_RATE_LIMIT_PATTERNS", "")
  445	    if not raw:
  446	        return []
  447	    pairs = []
  448	    for chunk in raw.split(";"):
  449	        chunk = chunk.strip()
  450	        if "=" not in chunk:
  451	            continue
  452	        name, pattern = chunk.split("=", 1)
  453	        try:
  454	            pairs.append((name.strip(), re.compile(pattern.strip(), re.IGNORECASE | re.DOTALL)))
  455	        except re.error:
  456	            print(f"WARNING: invalid user rate-limit pattern '{name}': skipping", file=sys.stderr)
  457	    return pairs
  458	
  459	
  460	def detect_rate_limit(stderr_text: str) -> tuple[bool, "dt.datetime | None", "str | None"]:
  461	    """Inspect reviewer stderr for a rate-limit signature.
  462	    Returns (matched, reset_at_local, pattern_name)."""
  463	    patterns = RATE_LIMIT_BUILTIN_PATTERNS + _user_patterns_from_env()
  464	    for name, pat in patterns:
  465	        m = pat.search(stderr_text)
  466	        if m:
  467	            time_group = m.group(1) if m.groups() else None
  468	            reset_at = _parse_reset_time(time_group) if time_group else _fallback_reset_time()
  469	            return True, reset_at, name
  470	    return False, None, None
  471	
  472	
  473	def _fallback_reset_time() -> "dt.datetime":
  474	    hours = int(os.environ.get("AGENT_REVIEWER_LIMIT_FALLBACK_HOURS", "4"))
  475	    return (dt.datetime.now() + dt.timedelta(hours=hours)).replace(second=0, microsecond=0)
  476	```
  477	
  478	Note: `_parse_reset_time` is implemented in Task 1.5. For now, add a stub:
  479	
  480	```python
  481	def _parse_reset_time(s: str) -> "dt.datetime":
  482	    return _fallback_reset_time()  # placeholder; refined in Task 1.5
  483	```
  484	
  485	Ensure `re` is imported at module top.
  486	
  487	- [x] **Step 4: Run tests**
  488	
  489	Run: `python3 -m pytest skills/external-review/tests/test_rate_limit_detection.py -v`
  490	Expected: the user-pattern test may parse `14:30` as fallback (since stub `_parse_reset_time` returns fallback). That test's `assert reset_at.hour == 14` will FAIL with the stub. That's expected — Task 1.5 fixes it. Mark this test xfail for now:
  491	
  492	In the test, wrap the failing assertion:
  493	
  494	```python
  495	def test_user_pattern_via_env(monkeypatch):
  496	    monkeypatch.setenv(
  497	        "AGENT_REVIEWER_RATE_LIMIT_PATTERNS",
  498	        r"my_backend=ERROR limit hit until (\d{1,2}:\d{2})",
  499	    )
  500	    matched, reset_at, name = er.detect_rate_limit("ERROR limit hit until 14:30")
  501	    assert matched is True
  502	    assert name == "my_backend"
  503	    # reset_at parsing is wired up properly in Task 1.5; for now just assert non-None.
  504	    assert reset_at is not None
  505	```
  506	
  507	Same change applies to `test_codex_sample_extracts_time_group` — relax to `assert reset_at is not None` for this task; Task 1.5 strengthens it.
  508	
  509	Re-run: 4 passed.
  510	
  511	- [x] **Step 5: Commit**
  512	
  513	```bash
  514	git add skills/external-review/scripts/external-reviewer.py \
  515	        skills/external-review/tests/test_rate_limit_detection.py
  516	git commit -m "external-reviewer: detect_rate_limit with built-in + env-extension patterns"
  517	```
  518	
  519	---
  520	
  521	### Task 1.5: `_parse_reset_time` (HH:MM, AM/PM, 24h, past-time wraps, no-time fallback)
  522	
  523	**Files:**
  524	- Modify: `skills/external-review/scripts/external-reviewer.py` (replace stub)
  525	- Create: `skills/external-review/tests/test_reset_time_parser.py`
  526	- Modify: `skills/external-review/tests/test_rate_limit_detection.py` (strengthen relaxed assertions back to spec)
  527	
  528	- [x] **Step 1: Write the failing tests**
  529	
  530	```python
  531	# skills/external-review/tests/test_reset_time_parser.py
  532	import datetime as dt
  533	from pathlib import Path
  534	import sys, importlib.util
  535	import pytest
  536	
  537	SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
  538	sys.path.insert(0, str(SCRIPTS))
  539	spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
  540	er = importlib.util.module_from_spec(spec)
  541	spec.loader.exec_module(er)
  542	
  543	
  544	def test_parse_pm_clock(monkeypatch):
  545	    # Freeze "now" to a moment before 6:48 PM today.
  546	    fixed = dt.datetime(2026, 5, 14, 17, 0, 0)
  547	    monkeypatch.setattr(er, "_now_local", lambda: fixed)
  548	    out = er._parse_reset_time("6:48 PM")
  549	    assert out == dt.datetime(2026, 5, 14, 18, 48, 0)
  550	
  551	
  552	def test_parse_am_clock(monkeypatch):
  553	    fixed = dt.datetime(2026, 5, 14, 17, 0, 0)
  554	    monkeypatch.setattr(er, "_now_local", lambda: fixed)
  555	    out = er._parse_reset_time("9:15 AM")
  556	    # 9:15 AM today is in the past relative to 17:00 → wrap to tomorrow.
  557	    assert out == dt.datetime(2026, 5, 15, 9, 15, 0)
  558	
  559	
  560	def test_parse_24h_clock(monkeypatch):
  561	    fixed = dt.datetime(2026, 5, 14, 17, 0, 0)
  562	    monkeypatch.setattr(er, "_now_local", lambda: fixed)
  563	    out = er._parse_reset_time("19:30")
  564	    assert out == dt.datetime(2026, 5, 14, 19, 30, 0)
  565	
  566	
  567	def test_parse_past_24h_wraps(monkeypatch):
  568	    fixed = dt.datetime(2026, 5, 14, 17, 0, 0)
  569	    monkeypatch.setattr(er, "_now_local", lambda: fixed)
  570	    out = er._parse_reset_time("08:00")
  571	    assert out == dt.datetime(2026, 5, 15, 8, 0, 0)
  572	
  573	
  574	def test_parse_unparseable_falls_back(monkeypatch):
  575	    fixed = dt.datetime(2026, 5, 14, 17, 0, 0)
  576	    monkeypatch.setattr(er, "_now_local", lambda: fixed)
  577	    monkeypatch.setenv("AGENT_REVIEWER_LIMIT_FALLBACK_HOURS", "4")
  578	    out = er._parse_reset_time("some_weird_string")
  579	    # Fallback: now + 4h
  580	    assert out == dt.datetime(2026, 5, 14, 21, 0, 0)
  581	```
  582	
  583	- [x] **Step 2: Verify they fail**
  584	
  585	Run: `python3 -m pytest skills/external-review/tests/test_reset_time_parser.py -v`
  586	Expected: failures across the board (stub returns fallback for everything; the AM/PM and 24h tests fail on parsing).
  587	
  588	- [x] **Step 3: Implement `_parse_reset_time`**
  589	
  590	In `external-reviewer.py`, replace the stub:
  591	
  592	```python
  593	_TIME_RE_AMPM = re.compile(r"^(\d{1,2}):(\d{2})\s*([AaPp][Mm])$")
  594	_TIME_RE_24H = re.compile(r"^(\d{1,2}):(\d{2})$")
  595	
  596	
  597	def _now_local() -> "dt.datetime":
  598	    """Override hook for tests."""
  599	    return dt.datetime.now()
  600	

[truncated: 2390 additional lines]

## Context Previews

### docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md

    1	# Reviewer rate-limit handling — design spec
    2	
    3	- Status: draft (external-review gate bypassed for this session per user instruction)
    4	- Date: 2026-05-14
    5	- Owner: Simon Greer
    6	- Related: `skills/external-review/scripts/external-reviewer.py`, `skills/external-review/SKILL.md`
    7	
    8	## 1. Problem
    9	
   10	When the third-party reviewer CLI (`codex`, `claude`, `gemini`, etc.) hits its provider usage cap, the subprocess exits non-zero with a stderr message like:
   11	
   12	```
   13	ERROR: You've hit your usage limit. Upgrade to Pro (...), visit ... or try again at 6:48 PM.
   14	```
   15	
   16	Today, `external-reviewer.py` records this as a generic process-failure round. The coordinator's next move is to re-submit — but the reviewer is still rate-limited, so the next round also fails. Without operator intervention the workflow stalls indefinitely (and burns chain rounds that don't progress the work).
   17	
   18	This spec adds first-class rate-limit handling: detect the failure mode, persist the reset window across sessions, and give the user three clear paths forward (manually approve, schedule a retry, or hand-bridge a response from an external reviewer).
   19	
   20	## 2. Goals
   21	
   22	- Detect rate-limit failures distinctly from other reviewer crashes.
   23	- Persist a global "limited until T" flag per reviewer binary so other sessions/repos honour it.
   24	- Refuse to spawn the reviewer subprocess while limited; instead surface a structured exit code + JSON payload.
   25	- Offer the operator three named paths (manual approval, scheduled retry, human bridge), plus a "hold" escape hatch so they're never railroaded.
   26	- Keep the chain history honest: a manual approval is a round in the chain, not a fabricated reviewer response.
   27	
   28	## 3. Non-goals
   29	
   30	- Auto-switching to a different reviewer backend on limit.
   31	- Pre-emptive limit prediction (no quota probe).
   32	- Multi-coordinator coordination beyond a brief `flock` on the state file.
   33	- Persisting the *contents* of scheduled tasks beyond what the `schedule` skill itself handles.
   34	
   35	## 4. Architecture
   36	
   37	Two layers:
   38	
   39	**CLI layer** (`skills/external-review/scripts/external-reviewer.py`)
   40	- Detects rate-limit via stderr regex.
   41	- Writes/reads `~/.config/superstar/reviewer-state.json` (a global, per-user state file).
   42	- Refuses spawn while limited; exits **code 8** with a JSON payload describing the limit.
   43	- Four new subcommands: `manual-approve`, `ingest-response`, `show-limit`, `clear-limit`.
   44	
   45	**Skill / coordinator layer** (`skills/external-review/SKILL.md`)
   46	- Documents exit 8 + the three-option menu.
   47	- Coordinator presents the menu via `AskUserQuestion` on every limited invocation (no auto-pick).
   48	- Coordinator dispatches each path directly (no subagent — manual approval is too consequential to delegate; the other two are tightly UI-coupled to the operator).
   49	
   50	## 5. State file
   51	
   52	Path: `~/.config/superstar/reviewer-state.json` by default. **Overridable** via the env var `AGENT_REVIEWER_STATE_FILE` (absolute path) or the CLI flag `--state-file PATH` on every subcommand that touches state (`review`, `manual-approve`, `ingest-response`, `show-limit`, `clear-limit`). Tests MUST set the env var to a `tmp_path`-scoped file so they never touch the developer's real state.
   53	
   54	The parent dir is created with `0700` permissions on first write.
   55	
   56	Shape:
   57	
   58	```json
   59	{
   60	  "schema_version": 1,
   61	  "limits": {
   62	    "<reviewer_cmd_basename>": {
   63	      "limited": true,
   64	      "limited_at":  "2026-05-14T17:00:00",
   65	      "reset_at":    "2026-05-14T18:48:00",
   66	      "reset_source": "regex:codex_usage_limit",
   67	      "raw_stderr_tail": "ERROR: You've hit your usage limit. ... try again at 6:48 PM.",
   68	      "chain":  "external-reviewer-context-optimisation-plan-P1-post-phase",
   69	      "round":  2
   70	    }
   71	  }
   72	}
   73	```
   74	
   75	- The key is the basename of `AGENT_REVIEWER_CMD` (defaulting to `"reviewer-agent"`). Different backends limit independently.
   76	- `reset_at` is ISO 8601 local-time (no TZ suffix). Comparisons use `datetime.now()` against the parsed value.
   77	- All timestamps strip seconds for stability.
   78	- On read, if `reset_at <= now()`, the entry is cleared in-place and the script proceeds normally (limit treated as expired).
   79	- Read/write uses `fcntl.flock(LOCK_EX)` on the file handle. Reads are short-lived; writes serialise across processes.
   80	- Missing file → empty state, no error.
   81	- Schema violations → log a warning to stderr, behave as if no state existed (fail-open, never block work on a corrupt state file).
   82	
   83	## 6. Detection + reset-time parsing
   84	
   85	New module-level helper in `external-reviewer.py`:
   86	
   87	```python
   88	def detect_rate_limit(stderr_text: str) -> tuple[bool, datetime | None, str | None]:
   89	    """Return (matched, reset_at_local, pattern_name)."""
   90	```
   91	
   92	Built-in patterns (compiled at import):
   93	
   94	| name                     | regex (Python)                                                                     |
   95	|--------------------------|------------------------------------------------------------------------------------|
   96	| `codex_usage_limit`      | `r"You've hit your usage limit.*?try again at (\d{1,2}:\d{2}\s*(?:AM|PM)?)"` (the pipe is regex alternation; spec table escaping is incidental — the actual compiled pattern uses an unescaped `|`) |
   97	| `claude_cli_rate_limit`  | stub — `r"(rate limit|rate-limited).*?reset (?:at|in)? ?(.+?)$"` (best-effort)     |
   98	| `gemini_cli_rate_limit`  | stub — `r"quota exceeded.*?retry (?:after|at) (.+?)$"` (best-effort)               |
   99	
  100	The stub patterns are extensible slots; we ship them as conservative matchers but expect real samples to refine them.
  101	
  102	Plus a user-supplied extension via env var:
  103	
  104	```
  105	AGENT_REVIEWER_RATE_LIMIT_PATTERNS="my_backend=ERROR limit hit until (.+);other_backend=..."
  106	```
  107	
  108	Parsed at startup; each pair adds another regex to the dispatch list.
  109	
  110	Reset-time parsing rules:
  111	1. If a regex group captures a clock time (`HH:MM`, optional `AM`/`PM`, or 24h), parse it as local time today.
  112	2. If the resulting timestamp is in the past, add 1 day (assume tomorrow).
  113	3. If the pattern matched but no time group (or the group fails to parse), fall back to `now + AGENT_REVIEWER_LIMIT_FALLBACK_HOURS` (default `4`).
  114	4. The agent presents the parsed `reset_at` to the user for confirmation before using it to schedule anything (option 2). The user can override.
  115	
  116	## 7. CLI behaviour change
  117	
  118	### 7.1 Pre-spawn check (`run_one_reviewer`)
  119	
  120	```
  121	1. Read state file. If state[reviewer_cmd_basename].limited is True and reset_at > now():
  122	     - Synthesise a "rate-limited" round artifact (≤8 KB, same shape as the existing
  123	       failed-round stub: header + status + the raw_stderr_tail + a one-line
  124	       "Reviewer rate-limited until <reset_at>; rerun after that or use the menu" body).
  125	     - chain.json round entry: status="rate-limited", returncode=null, verdict=null,
  126	       verdict_valid=false, reset_at=<iso>, reviewer_cmd=<basename>.
  127	     - Print JSON payload to stdout (see 7.3).
  128	     - Exit code 8.
  129	2. If reset_at <= now(): clear the entry, write state, continue normally.
  130	3. No state → continue normally.
  131	```
  132	
  133	### 7.2 Post-failure detection
  134	
  135	After the reviewer subprocess exits non-zero:
  136	
  137	```
  138	1. Call detect_rate_limit(stderr_text).
  139	2. If matched:
  140	     - Compute reset_at via §6 rules.
  141	     - Acquire flock on state file, set limits[<reviewer_cmd_basename>] = { ... }, release.
  142	     - Write the rate-limited round artifact (replacing the would-be failed-round artifact).
  143	     - Print JSON payload to stdout. Exit code 8.
  144	3. If not matched: existing failed-round path (status="failed", exit with reviewer's own returncode).
  145	```
  146	
  147	The `--review-depth thorough` case: when only the **primary** reviewer is rate-limited, the round is rate-limited (no sweep needed). When a sweep is rate-limited and the primary succeeded, the sweep is recorded as a per-reviewer rate-limited entry inside `chain.json`'s `reviewers[]` and the round otherwise behaves like the existing "some sweeps failed" case (merged verdict computed from ok reviewers only). The state file is still written so subsequent invocations against the same reviewer_cmd refuse.
  148	
  149	### 7.3 Exit code 8 JSON payload
  150	
  151	```json
  152	{
  153	  "rate_limited": true,
  154	  "reviewer_cmd": "reviewer-agent",
  155	  "reset_at":     "2026-05-14T18:48:00",
  156	  "reset_source": "regex:codex_usage_limit",
  157	  "chain":        "external-reviewer-context-optimisation-plan-P1-post-phase",
  158	  "round":        2,
  159	  "request_path": "docs/reviewer/.../r2-...-request.md",
  160	  "raw_stderr_tail": "ERROR: ..."
  161	}
  162	```
  163	
  164	`--emit json` (already a flag) emits this on the same stdout the success path uses, so the existing parsing code in callers can branch on the `rate_limited` key.
  165	
  166	### 7.4 Rate-limited status semantics (interaction with existing logic)
  167	
  168	The introduction of `status: "rate-limited"` requires updates at four sites in the existing script. Each is enumerated here so the plan can land them as small, named tasks.
  169	
  170	| Site | Current behaviour | Required change |
  171	|---|---|---|
  172	| **Resolution gate** (`post-slice` / `post-phase` requires `r{N-1}-resolution.md` unless prior round was `status="failed"`) | Bypasses only on `"failed"` | Also bypass on `"rate-limited"`. A rate-limited round has no findings to resolve. |
  173	| **`build_incremental_preamble` walk-back** (skips `status ∈ {failed, unknown}` to find the last trusted round) | Skips `failed`/`unknown` | Also skip `rate-limited`. The "Note: rounds N..K were ... skipped" annotation lists all three classes. |
  174	| **`compute_merged_verdict` reviewer filter** (aggregates only over `returncode == 0` reviewers) | Excludes failed reviewers | Also exclude rate-limited reviewers (`status == "rate-limited"`). A round that is fully rate-limited (no successful reviewer) produces `merged_verdict: null`, mirroring the all-failed case. |
  175	| **`write_merged_findings`** (returns None if all failed) | Returns None when all failed | Also return None when all reviewers are rate-limited (or any mix of failed/rate-limited). No partial findings file. |
  176	
  177	`manual-approved` rounds do **not** need bypass treatment — they have a real `verdict: "ready"` and `verdict_valid: true`, so the existing gating machinery accepts them as-is.
  178	
  179	### 7.5 Coalescing repeated refusals
  180	
  181	Pre-spawn refusals (§7.1) do NOT each append a new chain round. Instead:
  182	
  183	1. The first detection of the limit (either via post-failure regex match in §7.2, OR the first pre-spawn refusal when state was set by a *prior session* and the chain has no rate-limited round yet) writes one new round with `status: "rate-limited"`.
  184	2. Subsequent pre-spawn refusals against the *same chain* while the limit is still active find that round at the head and **update its `last_refused_at` timestamp** (and append the new refusal time to a bounded `refused_at[]` list — capped at 20 entries; older entries elided) instead of writing a new round. They still emit the exit-8 JSON and print the menu.
  185	3. Once the limit clears (state's `reset_at <= now()`), the next invocation proceeds normally and writes a fresh round as it always has. The dangling `rate-limited` round at the head is left in place as audit history.
  186	4. If the user picks `manual-approve` or `ingest-response` while the rate-limited round is still at the head, those subcommands write a *new* round (status `manual-approved` or `human-bridged`) immediately after it. The chain advances; the rate-limited round remains as the audit trail of why this happened.
  187	
  188	### 7.6 New subcommands
  189	
  190	**`manual-approve`**
  191	
  192	```
  193	external-reviewer.py manual-approve \
  194	  --kind <kind> --file <target> --work-id <id> \
  195	  --note "operator note"
  196	```
  197	
  198	Effects:
  199	- Writes `r{N}-response.md` (next-round-N for the chain) containing:
  200	  ```

[truncated: 125 additional lines]

<!-- superstar-prompt:end -->