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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/x10-verdict-parser

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md

Additional context files:
- docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md
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

### docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md

    1	# X10 — Verdict Parser & Prompt Hardening Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Eliminate the rerun loop caused by Claude emitting `**Verdict: ready with small edits.**` (no "Overall" prefix), and centralise verdict-response normalisation behind one helper.
    6	
    7	**Architecture:** One-file change to `skills/external-review/scripts/external-reviewer.py` plus a few targeted test additions. Two coordinated edits: (a) prompt instructs Claude to emit a literal trailerless verdict line; (b) parser gains an anchored, value-bounded fallback for bare `Verdict:` and a single `parse_reformatted_verdict(raw)` chokepoint used by both the automated round path (line 1403) and the manual ingest path (line 1814). Legacy manifest synthesis is deliberately excluded.
    8	
    9	**Tech Stack:** Python 3 (stdlib `re`), pytest. No new dependencies.
   10	
   11	**Spec:** [`docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md`](../specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md)
   12	
   13	**Reviewer chain (spec):** `docs/reviewer/x10-verdict-parser-claude-formatting-design-spec/` (verdict `ready` at r5).
   14	
   15	---
   16	
   17	## Scheduling note
   18	
   19	X10 is a cross-cutting item, not a phase/slice. No `tasktool schedule` / `tasktool ratify` / `tasktool start` cycle applies. The first execution step is to start a TodoWrite checklist and proceed directly to Task 1.
   20	
   21	## File map
   22	
   23	- Modify: `skills/external-review/scripts/external-reviewer.py` (one file)
   24	  - `REVIEW_PROMPT` (lines 48–86): drop verdict from numbered list, add literal-format trailing paragraph.
   25	  - `_VERDICT_HEADING_STYLE` (lines 1763–1767): make `Overall` optional.
   26	  - `VERDICT_LINE_RE` (line 2425): unchanged (kept strict).
   27	  - Add `VERDICT_LINE_BARE_RE` next to `VERDICT_LINE_RE`.
   28	  - Add `parse_reformatted_verdict(raw)` helper next to `parse_verdict`.
   29	  - Modify call site at line 1403 (automated round) to call `parse_reformatted_verdict(body)`.
   30	  - Modify call site at line 1814 (manual ingest) to call `parse_reformatted_verdict(raw)`.
   31	- Add: `skills/external-review/tests/fixtures/claude-bare-verdict-ready-with-small-edits.md` (copied verbatim).
   32	- Add: `skills/external-review/tests/fixtures/claude-heading-revise.md` (copied verbatim).
   33	- Modify: `skills/external-review/tests/test_verdict.py` — 12 new test functions (5 expected to fail before Task 3, 7 expected to pass already given current strict `parse_verdict` behaviour — they become live assertions after Task 3's regex changes).
   34	- Modify: `skills/external-review/tests/test_heading_style_verdict.py` — 1 new test.
   35	- Modify: `skills/external-review/tests/test_prompt_contract.py` — 1 new test asserting the new verdict-trailer wording is present and the old numbered-list form is absent.
   36	
   37	---
   38	
   39	## Task 1: Copy real-world fixtures into the repo
   40	
   41	**Files:**
   42	- Create: `skills/external-review/tests/fixtures/claude-bare-verdict-ready-with-small-edits.md`
   43	- Create: `skills/external-review/tests/fixtures/claude-heading-revise.md`
   44	
   45	- [ ] **Step 1: Create the fixtures directory and copy the bare-verdict fixture**
   46	
   47	```bash
   48	mkdir -p skills/external-review/tests/fixtures
   49	cp /home/simon/Dev/sigreer/multistore/docs/reviewer/p11-s5-final-guardrails-and-documentation-plan/r2-2026-05-19T0054-response.md \
   50	   skills/external-review/tests/fixtures/claude-bare-verdict-ready-with-small-edits.md
   51	```
   52	
   53	- [ ] **Step 2: Copy the heading-style fixture**
   54	
   55	```bash
   56	cp /home/simon/Dev/sigreer/multistore/docs/reviewer/p11-s5-final-guardrails-and-documentation-plan/r1-2026-05-19T0050-response.md \
   57	   skills/external-review/tests/fixtures/claude-heading-revise.md
   58	```
   59	
   60	- [ ] **Step 3: Sanity-check the fixtures contain the expected verdict lines**
   61	
   62	```bash
   63	grep -i 'verdict' skills/external-review/tests/fixtures/claude-bare-verdict-ready-with-small-edits.md | tail -3
   64	grep -i 'verdict' skills/external-review/tests/fixtures/claude-heading-revise.md | tail -3
   65	```
   66	
   67	Expected output for the bare fixture: a line containing `**Verdict: ready with small edits.**`. For the heading fixture: a `## Overall Verdict` heading and a `**revise** —` value line nearby.
   68	
   69	- [ ] **Step 4: Commit**
   70	
   71	```bash
   72	git add skills/external-review/tests/fixtures/
   73	git commit -m "X10: add real-world reviewer-response fixtures"
   74	```
   75	
   76	---
   77	
   78	## Task 2: Write failing tests for bare `Verdict:` parsing
   79	
   80	**Files:**
   81	- Modify: `skills/external-review/tests/test_verdict.py`
   82	
   83	- [ ] **Step 1: Append the new unit tests to `test_verdict.py`**
   84	
   85	Append the following block to the end of `skills/external-review/tests/test_verdict.py` (the existing imports at lines 1–7 already expose `er`):
   86	
   87	```python
   88	from pathlib import Path
   89	
   90	FIXTURES = Path(__file__).resolve().parent / "fixtures"
   91	
   92	
   93	def test_bare_verdict_ready_with_small_edits():
   94	    v, valid = er.parse_verdict("**Verdict: ready with small edits.**")
   95	    assert v == "ready with small edits"
   96	    assert valid is True
   97	
   98	
   99	def test_bare_verdict_revise():
  100	    v, valid = er.parse_verdict("**Verdict: revise.**")
  101	    assert v == "revise"
  102	    assert valid is True
  103	
  104	
  105	def test_bare_verdict_not_matched_in_prose():
  106	    body = "the previous round's verdict was revise, but this is just narrative.\n"
  107	    v, valid = er.parse_verdict(body)
  108	    assert v is None
  109	    assert valid is False
  110	
  111	
  112	def test_overall_preferred_over_bare():
  113	    body = (
  114	        "**Verdict: revise**\n\n"
  115	        "...more prose...\n\n"
  116	        "Overall verdict: ready\n"
  117	    )
  118	    v, valid = er.parse_verdict(body)
  119	    assert v == "ready"
  120	    assert valid is True
  121	
  122	
  123	def test_bare_verdict_rejects_extra_words_after_value():
  124	    v, valid = er.parse_verdict("**Verdict: ready for review**")
  125	    assert v is None
  126	    assert valid is False
  127	
  128	
  129	def test_bare_verdict_rejects_hyphenated_value():
  130	    v, valid = er.parse_verdict("Verdict: ready-ish")
  131	    assert v is None
  132	    assert valid is False
  133	
  134	
  135	def test_bare_verdict_rejects_qualified_value():
  136	    v, valid = er.parse_verdict("Verdict: ready with small edits pending changes")
  137	    assert v is None
  138	    assert valid is False
  139	
  140	
  141	def test_bare_verdict_rejects_contradictory_same_line_prose():
  142	    v, valid = er.parse_verdict("**Verdict: ready. Important findings remain unresolved.**")
  143	    assert v is None
  144	    assert valid is False
  145	
  146	
  147	def test_bare_verdict_rejects_benign_same_line_prose():
  148	    body = "**Verdict: ready with small edits.** Full review written to /tmp/foo.md."
  149	    v, valid = er.parse_verdict(body)
  150	    assert v is None
  151	    assert valid is False
  152	
  153	
  154	def test_parse_reformatted_verdict_helper():
  155	    raw = "## Overall Verdict\n\n**revise** — text\n"
  156	    v, valid = er.parse_reformatted_verdict(raw)
  157	    assert v == "revise"
  158	    assert valid is True
  159	
  160	
  161	def test_parse_reformatted_verdict_fixture_bare():
  162	    raw = (FIXTURES / "claude-bare-verdict-ready-with-small-edits.md").read_text()
  163	    v, valid = er.parse_reformatted_verdict(raw)
  164	    assert v == "ready with small edits"
  165	    assert valid is True
  166	
  167	
  168	def test_parse_reformatted_verdict_fixture_heading():
  169	    raw = (FIXTURES / "claude-heading-revise.md").read_text()
  170	    v, valid = er.parse_reformatted_verdict(raw)
  171	    assert v == "revise"
  172	    assert valid is True
  173	```
  174	
  175	- [ ] **Step 2: Run the new tests and observe the expected mixed pass/fail pattern**
  176	
  177	```bash
  178	python3 -m pytest skills/external-review/tests/test_verdict.py -v
  179	```
  180	
  181	Expected outcome (be specific — this is the TDD checkpoint):
  182	
  183	| Test | Result before Task 3 | Why |
  184	|---|---|---|
  185	| `test_bare_verdict_ready_with_small_edits` | **FAIL** | `parse_verdict` requires `Overall verdict`; bare returns `(None, False)`. |
  186	| `test_bare_verdict_revise` | **FAIL** | Same. |
  187	| `test_bare_verdict_not_matched_in_prose` | pass | Current parser already returns `(None, False)` for prose. |
  188	| `test_overall_preferred_over_bare` | pass | Current parser already picks the last `Overall verdict:` match. |
  189	| `test_bare_verdict_rejects_extra_words_after_value` | pass | Current parser returns `(None, False)` — no `Overall` prefix. |
  190	| `test_bare_verdict_rejects_hyphenated_value` | pass | Same. |
  191	| `test_bare_verdict_rejects_qualified_value` | pass | Same. |
  192	| `test_bare_verdict_rejects_contradictory_same_line_prose` | pass | Same. |
  193	| `test_bare_verdict_rejects_benign_same_line_prose` | pass | Same. |
  194	| `test_parse_reformatted_verdict_helper` | **FAIL** | `AttributeError: module 'external_reviewer' has no attribute 'parse_reformatted_verdict'`. |
  195	| `test_parse_reformatted_verdict_fixture_bare` | **FAIL** | Same. |
  196	| `test_parse_reformatted_verdict_fixture_heading` | **FAIL** | Same. |
  197	
  198	So expect **5 failures, 7 passes** among the 12 new tests, plus the 6 pre-existing tests passing. The 7 "passes" are *not* false positives — they assert no-op behaviour now and become live assertions after Task 3 introduces `VERDICT_LINE_BARE_RE`.
  199	
  200	- [ ] **Step 3: Add a failing test in `test_heading_style_verdict.py`**
  201	
  202	Append to `skills/external-review/tests/test_heading_style_verdict.py` (after `FAKE_REVIEWER_BOLD_HEADING_STYLE`):
  203	
  204	```python
  205	FAKE_REVIEWER_BARE_HEADING_STYLE = """#!/usr/bin/env bash
  206	cat <<'EOF'
  207	## Findings
  208	none
  209	
  210	**Verdict**
  211	
  212	ready with small edits
  213	EOF
  214	"""
  215	
  216	
  217	def test_bare_heading_style_verdict_parses(tmp_path):
  218	    """Claude commonly emits `**Verdict**\\n\\nvalue` (no `Overall`).
  219	
  220	    The bare form must normalise the same way the `Overall verdict` heading
  221	    style does, so end-to-end the round records verdict_valid=True.
  222	    """
  223	    payload = _run(FAKE_REVIEWER_BARE_HEADING_STYLE, tmp_path)
  224	    assert payload["verdict"] == "ready with small edits"
  225	    assert payload["verdict_valid"] is True
  226	    assert payload["merged_verdict"] == "ready with small edits"
  227	```
  228	
  229	- [ ] **Step 4: Run the new heading test and verify it fails**
  230	
  231	```bash
  232	python3 -m pytest skills/external-review/tests/test_heading_style_verdict.py::test_bare_heading_style_verdict_parses -v
  233	```
  234	
  235	Expected: FAIL with `assert None == 'ready with small edits'` (the heading-style regex does not yet accept bare `**Verdict**`).
  236	
  237	- [ ] **Step 5: Commit the failing tests**
  238	
  239	```bash
  240	git add skills/external-review/tests/test_verdict.py skills/external-review/tests/test_heading_style_verdict.py
  241	git commit -m "X10: failing tests for bare Verdict parsing and helper"
  242	```
  243	
  244	---
  245	
  246	## Task 3: Implement the parser changes
  247	
  248	**Files:**
  249	- Modify: `skills/external-review/scripts/external-reviewer.py`
  250	
  251	- [ ] **Step 1: Extend `_VERDICT_HEADING_STYLE` to accept bare `Verdict`**
  252	
  253	Replace lines 1763–1767 (`_VERDICT_HEADING_STYLE = re.compile(...)`):
  254	
  255	```python
  256	_VERDICT_HEADING_STYLE = re.compile(
  257	    r"(?:\*+|_+)?((?:\d+\.\s+)?(?:Overall\s+)?Verdict)(?:\*+|_+)?\s*\n+\s*"
  258	    r"(?:\*+|_+)?(ready with small edits|ready|revise)(?:\*+|_+)?",
  259	    re.IGNORECASE,
  260	)
  261	```
  262	
  263	The only change is inserting `(?:Overall\s+)?` so the qualifier is optional. `_reformat_response` (lines 1770–1775) already uses this regex; no change needed there.
  264	
  265	- [ ] **Step 2: Add `VERDICT_LINE_BARE_RE` and a two-pass `parse_verdict`**
  266	
  267	Replace the block at lines 2425–2438:
  268	
  269	```python
  270	VERDICT_LINE_RE = re.compile(
  271	    r"overall\s+verdict\s*[`*_\"']*\s*[:\-]\s*[`*_\"'\s]*(ready with small edits|ready|revise)[`*_\"'.\s]*",
  272	    re.IGNORECASE,
  273	)
  274	
  275	
  276	# Anchored, value-bounded bare `Verdict:` fallback. Used only when no
  277	# `Overall verdict:` line matches. See X10 spec §Design.2b for the trailing-
  278	# prose policy. Do NOT add re.VERBOSE — it strips literal whitespace from
  279	# the alternation `ready with small edits` and silently breaks the regex.
  280	VERDICT_LINE_BARE_RE = re.compile(
  281	    r"^[\s>#*_`]*verdict\s*[`*_\"']*\s*[:\-]\s*[`*_\"'\s]*"
  282	    r"(ready with small edits|ready|revise)"
  283	    r"(?=[\s`*_\"'.]*(?:$|\n))",
  284	    re.IGNORECASE | re.MULTILINE,
  285	)
  286	
  287	
  288	def parse_verdict(text: str) -> tuple[str | None, bool]:
  289	    matches = list(VERDICT_LINE_RE.finditer(text))
  290	    if not matches:
  291	        matches = list(VERDICT_LINE_BARE_RE.finditer(text))
  292	    if not matches:
  293	        return None, False
  294	    raw = matches[-1].group(1).strip().lower()
  295	    if raw not in VERDICT_VALUES:
  296	        return None, False
  297	    return raw, True
  298	
  299	
  300	def parse_reformatted_verdict(raw: str) -> tuple[str | None, bool]:
  301	    """Compose `_reformat_response` and `parse_verdict`.
  302	
  303	    Single chokepoint for response-body verdict extraction. Used by both the
  304	    automated round path and the manual ingest path. NOT used by legacy
  305	    manifest synthesis (`synthesize_manifest_from_legacy_files`) — that path
  306	    parses historical bodies as-stored and must not rewrite them.
  307	    """
  308	    return parse_verdict(_reformat_response(raw))
  309	```
  310	
  311	- [ ] **Step 3: Run unit tests, expect the verdict tests to pass**
  312	
  313	```bash
  314	python3 -m pytest skills/external-review/tests/test_verdict.py -v
  315	```
  316	
  317	Expected: all 18 tests pass (6 original + 12 new).
  318	
  319	- [ ] **Step 4: Run the heading-style suite**
  320	
  321	```bash
  322	python3 -m pytest skills/external-review/tests/test_heading_style_verdict.py -v
  323	```
  324	
  325	Expected: all three tests pass including the new `test_bare_heading_style_verdict_parses`.
  326	
  327	- [ ] **Step 5: Commit**
  328	
  329	```bash
  330	git add skills/external-review/scripts/external-reviewer.py
  331	git commit -m "X10: add bare Verdict regex, parse_reformatted_verdict helper"
  332	```
  333	
  334	---
  335	
  336	## Task 4: Route both call sites through `parse_reformatted_verdict`
  337	
  338	**Files:**
  339	- Modify: `skills/external-review/scripts/external-reviewer.py`
  340	
  341	- [ ] **Step 1: Update the automated round path**
  342	
  343	Find lines 1400–1405 (currently):
  344	
  345	```python
  346	        if result.returncode != 0:
  347	            verdict, valid = None, False
  348	        else:
  349	            verdict, valid = parse_verdict(_VERDICT_HEADING_STYLE.sub(
  350	                lambda m: f"{m.group(1)}: {m.group(2)}", body
  351	            ))
  352	```
  353	
  354	Replace with:
  355	
  356	```python
  357	        if result.returncode != 0:
  358	            verdict, valid = None, False
  359	        else:
  360	            verdict, valid = parse_reformatted_verdict(body)
  361	```
  362	
  363	- [ ] **Step 2: Update the manual ingest path**
  364	
  365	Find lines around 1813–1814 (inside `run_ingest_response`):
  366	
  367	```python
  368	    reformatted = _reformat_response(raw)
  369	    ...
  370	    verdict, valid = parse_verdict(reformatted)
  371	```
  372	
  373	Replace the two lines with a single call. Concretely: remove the `reformatted = _reformat_response(raw)` line, and change the `parse_verdict(reformatted)` line to `parse_reformatted_verdict(raw)`. Any other reference to `reformatted` in this function (e.g. when writing the response file to disk) must continue to use the reformatted body — keep the assignment if such a reference exists; otherwise remove it.
  374	
  375	Inspect the function first:
  376	
  377	```bash
  378	grep -n 'reformatted' skills/external-review/scripts/external-reviewer.py
  379	```
  380	
  381	If `reformatted` is used in only one place (the `parse_verdict` call), collapse to:
  382	
  383	```python
  384	    verdict, valid = parse_reformatted_verdict(raw)
  385	```
  386	
  387	If it is used elsewhere (e.g. `response_path.write_text(reformatted)`), keep the `reformatted = _reformat_response(raw)` line and just change the `parse_verdict(reformatted)` call to `parse_reformatted_verdict(raw)`.
  388	
  389	- [ ] **Step 3: Run the full external-review test suite**
  390	
  391	```bash
  392	python3 -m pytest skills/external-review/tests/ -q
  393	```
  394	
  395	Expected: 234 passed (222 original + 12 new) or close to it (count depends on parametrisation in the new tests). Zero failures.
  396	
  397	- [ ] **Step 4: Acceptance criterion 3 — confirm single chokepoint**
  398	
  399	```bash
  400	grep -n 'parse_verdict\|parse_reformatted_verdict' skills/external-review/scripts/external-reviewer.py
  401	```
  402	
  403	Expected:
  404	- One definition of `parse_verdict` and one definition of `parse_reformatted_verdict`.
  405	- The automated round path (~line 1403) calls `parse_reformatted_verdict`.
  406	- The manual ingest path (~line 1814) calls `parse_reformatted_verdict`.
  407	- `synthesize_manifest_from_legacy_files` (around line 2598) still calls `parse_verdict` on raw legacy bodies (this is the documented exception).
  408	- No other call to `parse_verdict` exists outside tests and the legacy synthesis function.
  409	
  410	- [ ] **Step 5: Commit**
  411	
  412	```bash
  413	git add skills/external-review/scripts/external-reviewer.py
  414	git commit -m "X10: route both response-body call sites through parse_reformatted_verdict"
  415	```
  416	
  417	---
  418	
  419	## Task 5: Tighten the prompt to discourage misformatted verdicts
  420	
  421	**Files:**
  422	- Modify: `skills/external-review/scripts/external-reviewer.py`
  423	
  424	- [ ] **Step 1: Update `REVIEW_PROMPT`**
  425	
  426	In `REVIEW_PROMPT` (the multi-line string at line 48), find the "Review output contract" list (lines ~75–83):
  427	
  428	```
  429	Review output contract:
  430	1. Findings
  431	   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
  432	     stable if this review is iterated in subsequent rounds.
  433	   - Mark severity inline: `Severity: blocking | important | minor | nit`.
  434	2. Open questions / assumptions
  435	3. Suggested document edits
  436	4. Verification gaps / commands that should be run, if any
  437	5. Overall verdict: one of "ready", "ready with small edits", or "revise"
  438	```
  439	
  440	Change to:
  441	
  442	```
  443	Review output contract:
  444	1. Findings
  445	   - Tag each finding with a stable ID: `F1`, `F2`, `F3`, …. IDs must remain
  446	     stable if this review is iterated in subsequent rounds.
  447	   - Mark severity inline: `Severity: blocking | important | minor | nit`.
  448	2. Open questions / assumptions
  449	3. Suggested document edits
  450	4. Verification gaps / commands that should be run, if any
  451	
  452	End your review with this exact line, as plain text on its own line:
  453	
  454	    Overall verdict: <ready|ready with small edits|revise>
  455	
  456	Do not bold, italicise, prefix with `##`, split across lines, or drop the
  457	word "Overall". Do not write `**Verdict: ready**` or place the value on a
  458	new line after a heading.
  459	```
  460	
  461	(The verdict moves out of the numbered list; the explicit don'ts are new.)
  462	
  463	- [ ] **Step 2: Add a prompt-contract assertion for the new wording**
  464	
  465	Append to `skills/external-review/tests/test_prompt_contract.py` (after `test_prompt_renders_with_all_kinds`):
  466	
  467	```python
  468	def test_prompt_has_literal_verdict_trailer(er):
  469	    """X10: the prompt must instruct the reviewer to emit a trailerless,
  470	    plain-text `Overall verdict:` line, with explicit don'ts against the
  471	    Claude-style heading / bare-Verdict variants.
  472	    """
  473	    prompt = er.REVIEW_PROMPT
  474	    # New trailer paragraph
  475	    assert "End your review with this exact line" in prompt
  476	    assert "Overall verdict: <ready|ready with small edits|revise>" in prompt
  477	    # Explicit don'ts
  478	    assert "Do not bold" in prompt
  479	    assert "**Verdict: ready**" in prompt
  480	    # Old numbered-list form is removed
  481	    assert "5. Overall verdict" not in prompt
  482	```
  483	
  484	- [ ] **Step 3: Run the prompt-contract test**
  485	
  486	```bash
  487	python3 -m pytest skills/external-review/tests/test_prompt_contract.py -v
  488	```
  489	
  490	Expected: all five tests pass (the four existing + the new `test_prompt_has_literal_verdict_trailer`).
  491	
  492	- [ ] **Step 4: Run the full test suite as a final regression check**
  493	
  494	```bash
  495	python3 -m pytest skills/external-review/tests/ -q
  496	```
  497	
  498	Expected: zero failures.
  499	
  500	- [ ] **Step 5: Manual acceptance replay (spec acceptance criterion 2)**
  501	
  502	```bash
  503	python3 -c "
  504	import sys, importlib.util
  505	spec = importlib.util.spec_from_file_location('er', 'skills/external-review/scripts/external-reviewer.py')
  506	m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
  507	for p in ['skills/external-review/tests/fixtures/claude-bare-verdict-ready-with-small-edits.md',
  508	          'skills/external-review/tests/fixtures/claude-heading-revise.md']:
  509	    raw = open(p).read()
  510	    print(p, '->', m.parse_reformatted_verdict(raw))
  511	"
  512	```
  513	
  514	Expected output:
  515	```
  516	skills/external-review/tests/fixtures/claude-bare-verdict-ready-with-small-edits.md -> ('ready with small edits', True)
  517	skills/external-review/tests/fixtures/claude-heading-revise.md -> ('revise', True)
  518	```
  519	
  520	- [ ] **Step 6: Commit**
  521	
  522	```bash
  523	git add skills/external-review/scripts/external-reviewer.py skills/external-review/tests/test_prompt_contract.py
  524	git commit -m "X10: tighten REVIEW_PROMPT and lock new wording with a test"
  525	```
  526	
  527	---
  528	
  529	## Task 6: Close out X10
  530	
  531	X10 is a `cross_cutting` tasktool item. **`tasktool close` does NOT enforce the post-slice external-review gate for `cross` IDs** (see `tools/tasktool/commands.py:397` — the review-gate branch is skipped for `cross`). The coordinator therefore enforces the gate manually before invoking `tasktool close`.
  532	
  533	- [ ] **Step 1: Add the plan to X10's refs**
  534	
  535	```bash
  536	tasktool ref X10 --add docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md
  537	```
  538	
  539	- [ ] **Step 2: Run post-slice external review against the plan (manual gate)**
  540	
  541	The coordinator invokes this; do **not** apply findings directly during execution — delegate to a fix subagent per `superstar:subagent-driven-development`.
  542	
  543	```bash
  544	python3 skills/external-review/scripts/external-reviewer.py review \
  545	  --kind post-slice \
  546	  --file docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md \
  547	  --work-id X10 \
  548	  --context docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md \
  549	  --context docs/tasklist.json \
  550	  --emit json
  551	```
  552	
  553	Iterate until `merged_verdict` ∈ {`ready`, `ready with small edits`}. The coordinator MUST NOT proceed to Step 3 until this verdict is reached — the gate is manual for `cross` items, but it is still required.
  554	
  555	- [ ] **Step 3: Close X10 in tasktool**
  556	
  557	```bash
  558	tasktool close X10
  559	```
  560	
  561	(`tasktool close` for a `cross` item simply marks it `done` without inspecting reviewer chains; the gate enforcement in Step 2 above is what makes the close legitimate. Do not pass `--reviewer-chain` — that flag is for phase/slice closeouts.)
  562	
  563	- [ ] **Step 4: Final commit (if anything was staged by tasktool)**
  564	
  565	```bash
  566	git status
  567	git diff --staged --quiet || git commit -m "X10: close"
  568	```
  569	
  570	---
  571	
  572	## Acceptance recap (mirrors spec §Acceptance)
  573	
  574	1. `python3 -m pytest skills/external-review/tests/` — all existing + new tests pass (≥ 234 passing).
  575	2. `parse_reformatted_verdict(open(p).read())` against `claude-bare-verdict-ready-with-small-edits.md` → `("ready with small edits", True)`; against `claude-heading-revise.md` → `("revise", True)`.
  576	3. `parse_reformatted_verdict` is the only response-body normalisation+parse chokepoint outside legacy manifest synthesis.
  577	4. No new dependencies, no new public CLI surface, no schema changes to `chain.json`.

## Context Previews

### docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md

    1	# X10 — Harden external-review verdict parser and prompt against Claude formatting variants
    2	
    3	- **Status:** spec
    4	- **Tasktool ID:** X10 (cross-cutting; continues the X3 line of verdict-parser fixes)
    5	- **Date:** 2026-05-20
    6	- **Owner:** Simon Greer
    7	- **Touches:** `skills/external-review/scripts/external-reviewer.py`, `skills/external-review/tests/`
    8	
    9	## Problem
   10	
   11	When Claude is the reviewing agent under `superstar:external-review`, runs are significantly slower and burn many more tokens than Codex runs. A primary cause: Claude returns a verdict in formats that the current parser does not recognise. The round records `verdict_valid=false`, the gate forces a rerun, and the same misformatted reply is produced again, multiplying cost.
   12	
   13	Direct evidence from `multistore/docs/reviewer/` (Claude-as-reviewer chains):
   14	
   15	1. **`p11-s5-final-guardrails-and-documentation-plan/chain.json`** records r1 and r2 with `verdict: null, verdict_valid: false, returncode: 0`. r1's body ends with the heading-style verdict `## Overall Verdict\n\n**revise** — primarily because…` (parses correctly today via `_VERDICT_HEADING_STYLE`). r2's body ends with `**Verdict: ready with small edits.**` — **bare `Verdict:`, no "Overall" prefix** — which `VERDICT_LINE_RE` cannot match. The chain only advanced after a human-bridged r3.
   16	
   17	2. **`p11-s2-primitive-convergence-design-spec/chain.json`** shows the same r1/r2 failure pattern.
   18	
   19	3. Frequency across `multistore/docs/reviewer/*/r*-response.md`:
   20	   - 61× `**Overall Verdict**` (value on next line; handled)
   21	   - 31× `## Overall Verdict` heading (handled)
   22	   - 7× `**Verdict: …**` / `**Verdict: ….**` (**not handled** — this is the failure mode)
   23	   - 0 bare `Verdict:` lines were found mid-prose; every occurrence is line-anchored after optional `**` / heading marks.
   24	
   25	## Goals
   26	
   27	- Eliminate the rerun loop caused by Claude's `**Verdict: …**` line.
   28	- Reduce the chance Claude produces a non-conforming verdict line in the first place.
   29	- Keep parser surface predictable: no loose-match recovery, no telemetry plumbing, no broader prompt rewrite.
   30	
   31	## Non-goals
   32	
   33	- Loose-match fallback that scans the last N lines (deferred; user opted strict-only).
   34	- Telemetry / `parser_recovery` flags in `chain.json`.
   35	- Changes to multi-reviewer (sweep) aggregation, rate-limit handling, or any other reviewer subsystem.
   36	- Reformatting unrelated sections of `REVIEW_PROMPT`.
   37	
   38	## Design
   39	
   40	Two coordinated changes.
   41	
   42	### Change 1 — Prompt: dedicated, literal verdict-format paragraph
   43	
   44	In `external-reviewer.py:48-86` (the `REVIEW_PROMPT` template), keep the existing "Review output contract" list but **remove the verdict from the numbered list** and replace it with a dedicated trailing paragraph that specifies the exact line. Numbered list items invite Claude to render them as headings; a free-standing instruction with a literal example does not.
   45	
   46	New trailing section (after the existing list 1–4):
   47	
   48	```
   49	End your review with this exact line, as plain text on its own line:
   50	
   51	    Overall verdict: <ready|ready with small edits|revise>
   52	
   53	Do not bold, italicise, prefix with `##`, split across lines, or drop the word
   54	"Overall". Do not write `**Verdict: ready**` or place the value on a new line
   55	after a heading.
   56	```
   57	
   58	Rationale: explicit don'ts override Claude's markdown reflex; abstract "use this format" instructions do not.
   59	
   60	### Change 2 — Parser: anchored bare-`Verdict:` fallback + DRY normalisation
   61	
   62	In `external-reviewer.py`:
   63	
   64	**2a. Centralise normalisation via a public helper.** Introduce `parse_reformatted_verdict(raw: str) -> tuple[str | None, bool]` which composes `_reformat_response` and `parse_verdict`. Both the automated round path (`external-reviewer.py:1403`) and the manual ingest path (`external-reviewer.py:1814`) MUST call this helper instead of composing the two functions by hand. `_reformat_response` already strips outer code fences and rewrites heading-style verdicts; co-locating the composition behind one named function gives a single chokepoint for future normalisations and removes the current divergence between the two call sites.
   65	
   66	**Legacy manifest synthesis is explicitly out of scope.** `synthesize_manifest_from_legacy_files` (around `external-reviewer.py:2598`) parses raw response bodies from historical pre-manifest chains. Updating it would re-write historical verdicts on first touch, which is undesirable. It continues to call `parse_verdict` directly on the raw body, by design.
   67	
   68	**2b. Add anchored, value-bounded bare-`Verdict:` matching.** Introduce a second regex `VERDICT_LINE_BARE_RE` that matches bare `Verdict:` **only when line-anchored** (after optional leading whitespace and markdown emphasis/heading marks) **and value-bounded** (nothing meaningful between the captured value and end-of-line beyond emphasis/punctuation/whitespace). Anchoring eliminates prose false-positives ("the previous round's verdict was revise"); value-bounding rejects malformed values like `Verdict: ready for review` or `Verdict: ready-ish` so they record as `(None, False)` rather than silently coercing to `ready`. Empirical confirmation: zero mid-prose matches found across the `multistore/docs/reviewer/` corpus.
   69	
   70	**Out of scope for line-anchoring:** list-bullet-prefixed verdict lines (`- Verdict: ready`, `1. Verdict: ready`). None appear in the observed Claude corpus. If they appear later, extend the leading character class then; do not pre-anchor for hypotheticals.
   71	
   72	Proposed shape:
   73	
   74	```python
   75	# Value boundary: rest of line is only emphasis marks, punctuation, and
   76	# whitespace, then end-of-line. Same-line trailing prose is rejected — see
   77	# "Trailing-prose policy" below.
   78	VERDICT_LINE_BARE_RE = re.compile(
   79	    r"^[\s>#*_`]*verdict\s*[`*_\"']*\s*[:\-]\s*[`*_\"'\s]*"
   80	    r"(ready with small edits|ready|revise)"
   81	    r"(?=[\s`*_\"'.]*(?:$|\n))",
   82	    re.IGNORECASE | re.MULTILINE,
   83	)
   84	```
   85	
   86	(Do **not** use `re.VERBOSE` — it strips literal whitespace from the alternation `ready with small edits`, silently breaking the regex.)
   87	
   88	The trailing lookahead enforces a single accepted shape: rest of line is only emphasis marks (`*`, `_`, `` ` ``, `"`, `'`), punctuation (`.`), and whitespace, then end-of-line. Covers the critical failure mode `**Verdict: ready with small edits.**` and rejects all malformed/contradictory variants.
   89	
   90	**Trailing-prose policy.** Lines like `**Verdict: ready with small edits.** Full review written to …` (3× in the `multistore` corpus, all from human-bridged rounds — not core parse-failure cases) are deliberately **not** accepted. The justification:
   91	
   92	1. The dominant failure mode is the *trailerless* `**Verdict: ready with small edits.**` — that single line is what caused the rerun loop in `p11-s5`. Boundary A handles it cleanly.
   93	2. A whitelist of "benign" trailer phrases is unbounded; a permissive trailer-accepting boundary risks accepting contradictory same-line prose like `**Verdict: ready.** Important findings remain unresolved.` and silently coercing it to `ready`.
   94	3. The user's stated preference for this ticket is strict-only. Loose-match recovery was explicitly deferred (§Non-goals).
   95	4. If a round ever lands with a real trailer, it will record `verdict_valid: false`, the coordinator will rerun, and the prompt change (§Change 1) tells Claude to emit a clean trailerless line — the second attempt should parse.
   96	
   97	Malformed values that match neither anchoring nor the boundary are rejected: `Verdict: ready for review`, `Verdict: ready-ish`, `Verdict: ready with small edits pending changes`, `**Verdict: ready.** Important findings remain unresolved.`, `**Verdict: ready with small edits.** Full review written to /tmp/foo.md.` (all return `(None, False)`).
   98	
   99	Update `parse_verdict` to:
  100	
  101	1. First scan with `VERDICT_LINE_RE` (the existing `Overall verdict` regex). If any match, return the last.
  102	2. If no match, scan with `VERDICT_LINE_BARE_RE`. If any match, return the last.
  103	3. Otherwise return `(None, False)`.
  104	
  105	This preserves the strict primary path. The bare form is only consulted when no `Overall verdict` line exists.
  106	
  107	**2c. Mirror the bare form in `_VERDICT_HEADING_STYLE`.** Today the heading-style regex requires the literal word "Overall". Extend it (or add a sibling) so two-line `**Verdict**\n\nrevise` is normalised to `Verdict: revise` before `VERDICT_LINE_BARE_RE` runs. The qualifier `(?:Overall\s+)?` directly in front of `verdict` is the smallest delta.
  108	
  109	### Worked examples
  110	
  111	After both changes:
  112	
  113	| Input | Normalised | Parse result |
  114	|---|---|---|
  115	| `**Overall verdict:** ready` | unchanged | ready (existing path) |
  116	| `## Overall Verdict\n\n**revise** — text` | `## Overall Verdict: revise — text` | revise (existing path) |
  117	| `**Verdict: ready with small edits.**` | unchanged | ready with small edits (new bare path) |
  118	| `**Verdict**\n\nrevise` | `**Verdict: revise` | revise (new bare path + heading mirror) |
  119	| `the previous round's verdict was revise` | unchanged | `(None, False)` — not line-anchored |
  120	| `Overall verdict: looks fine to me` | unchanged | `(None, False)` — unchanged invalid behaviour |
  121	
  122	## Tests
  123	
  124	All in `skills/external-review/tests/`.
  125	
  126	### New unit tests in `test_verdict.py`
  127	
  128	- `test_bare_verdict_ready_with_small_edits` — `**Verdict: ready with small edits.**` → `ready with small edits`, valid.
  129	- `test_bare_verdict_revise` — `**Verdict: revise.**` → `revise`, valid.
  130	- `test_bare_verdict_not_matched_in_prose` — body containing `the previous round's verdict was revise` (no line-anchored `Verdict:` and no `Overall verdict:` line) → `(None, False)`.
  131	- `test_overall_preferred_over_bare` — body containing both `**Verdict: revise**` near the top and `Overall verdict: ready` near the bottom → `ready` (Overall path wins, takes last match).
  132	- `test_bare_verdict_rejects_extra_words_after_value` — `**Verdict: ready for review**` → `(None, False)`.
  133	- `test_bare_verdict_rejects_hyphenated_value` — `Verdict: ready-ish` → `(None, False)`.
  134	- `test_bare_verdict_rejects_qualified_value` — `Verdict: ready with small edits pending changes` → `(None, False)`.
  135	- `test_bare_verdict_rejects_contradictory_same_line_prose` — `**Verdict: ready. Important findings remain unresolved.**` → `(None, False)` (trailing prose policy: any same-line content after the value beyond emphasis/punct/whitespace is rejected).
  136	- `test_bare_verdict_rejects_benign_same_line_prose` — `**Verdict: ready with small edits.** Full review written to /tmp/foo.md.` → `(None, False)`. Documents the deliberate strict-only choice: benign trailers are rejected because a permissive boundary would also admit contradictory ones.
  137	- `test_parse_reformatted_verdict_helper` — direct call on the new `parse_reformatted_verdict(raw)` helper with a fenced + heading-style fixture round-trips to `("revise", True)`.
  138	
  139	### New unit tests in `test_heading_style_verdict.py`
  140	
  141	- `test_bare_heading_style_verdict_parses` — fake reviewer emits `**Verdict**\n\nready with small edits` → `verdict_valid=True`, `verdict="ready with small edits"`.
  142	
  143	### Fixture-based regression
  144	
  145	Add the following fixture files under `skills/external-review/tests/fixtures/` (create the directory):
  146	
  147	- `claude-bare-verdict-ready-with-small-edits.md` — copied verbatim from `/home/simon/Dev/sigreer/multistore/docs/reviewer/p11-s5-final-guardrails-and-documentation-plan/r2-2026-05-19T0054-response.md`.
  148	- `claude-heading-revise.md` — copied verbatim from `/home/simon/Dev/sigreer/multistore/docs/reviewer/p11-s5-final-guardrails-and-documentation-plan/r1-2026-05-19T0050-response.md`.
  149	
  150	The implementer **must copy these into the repo**; do not reference them from the external `multistore` path at test time. Reference them in the new tests via `pathlib.Path` so future regressions are pinned to committed, version-controlled content.
  151	
  152	### Existing tests
  153	
  154	All 222 tests in `skills/external-review/tests/` must continue to pass without modification.
  155	
  156	## Acceptance criteria
  157	
  158	1. `python3 -m pytest skills/external-review/tests/` — all existing + new tests pass.
  159	2. Manual replay: running `parse_reformatted_verdict(open(p).read())` against the copied fixture `claude-bare-verdict-ready-with-small-edits.md` returns `("ready with small edits", True)`. Replay against `claude-heading-revise.md` returns `("revise", True)`.
  160	3. Single chokepoint: `parse_reformatted_verdict` exists and is called from both the automated round path (`external-reviewer.py:1403`) and the manual ingest path (`external-reviewer.py:1814`). Legacy manifest synthesis (`synthesize_manifest_from_legacy_files`) is documented as the one excluded call site.
  161	4. No new dependencies, no new public CLI surface, no schema changes to `chain.json`.
  162	
  163	## Risks & rollback
  164	
  165	- **Risk:** `VERDICT_LINE_BARE_RE` over-anchored such that some legitimate variant is missed. Mitigation: leading class `^[\s>#*_`]*` covers whitespace, blockquote, heading markers, and bold/italic/code emphasis — the forms observed in the corpus. List-bullet variants (`- Verdict: ready`) are intentionally not matched; if they appear later, the leading class is the single place to extend. The fixture suite locks in the observed real variants.
  166	- **Risk:** Two-pass parsing changes the verdict picked for a body containing both forms. Mitigation: `Overall verdict` is preferred; bare only used when Overall absent. Test `test_overall_preferred_over_bare` pins this.
  167	- **Rollback:** Revert the touched commit; behaviour returns to pre-X10 strict matching. No data migration.
  168	
  169	## Out of scope / follow-ups
  170	
  171	- If the prompt change does not materially reduce the rate of heading-style verdicts in subsequent Claude chains, consider a more invasive prompt restructure (separate ticket).
  172	- If a new unhandled variant appears, decide then whether to add it to the anchored regex or revisit the deferred loose-match fallback.
### docs/tasklist.json

    1	{
    2	  "archived_phases": [
    3	    {
    4	      "archived_date": "2026-05-18",
    5	      "archived_path": "docs/archived-tasks/P2-tasktool-json-backed-task-management-cli.md",
    6	      "id": "P2",
    7	      "title": "tasktool: JSON-backed task management CLI"
    8	    },
    9	    {
   10	      "archived_date": "2026-05-19",
   11	      "archived_path": "docs/archived-tasks/P4-tasktool-coordination-and-lifecycle-auth.md",
   12	      "id": "P4",
   13	      "title": "Tasktool coordination and lifecycle authority"
   14	    },
   15	    {
   16	      "archived_date": "2026-05-19",
   17	      "archived_path": "docs/archived-tasks/P3-phase-planning-workflow.md",
   18	      "id": "P3",
   19	      "title": "Phase planning workflow"
   20	    }
   21	  ],
   22	  "cross_cutting": [
   23	    {
   24	      "closed": "2026-05-18",
   25	      "created": "2026-05-18",
   26	      "id": "X1",
   27	      "notes": "Changed external-review default prompt transport from argv to stdin so the bundled Codex reviewer-agent receives prompts via codex exec '-' and avoids argv length failures.",
   28	      "refs": [],
   29	      "started": null,
   30	      "status": "done",
   31	      "title": "Default external-review prompt transport to stdin"
   32	    },
   33	    {
   34	      "closed": "2026-05-18",
   35	      "created": "2026-05-18",
   36	      "id": "X2",
   37	      "notes": "Added repo-local tools/tasktool/tasktool launcher, updated tasklist/project-setup docs to prefer it, and taught the pre-commit hook to use the repo-local launcher before falling back to a global tasktool shim.",
   38	      "refs": [],
   39	      "started": null,
   40	      "status": "done",
   41	      "title": "Add repo-local tasktool launcher"
   42	    },
   43	    {
   44	      "closed": "2026-05-19",
   45	      "created": "2026-05-19",
   46	      "id": "X3",
   47	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. External-review verdict parsing now accepts markdown-emphasized Overall Verdict headings such as **5. Overall Verdict** followed by ready/revise text.",
   48	      "refs": [
   49	        "skills/external-review/scripts/external-reviewer.py",
   50	        "skills/external-review/tests/test_heading_style_verdict.py"
   51	      ],
   52	      "started": null,
   53	      "status": "done",
   54	      "title": "Spot fix: parse bold external-review verdict headings"
   55	    },
   56	    {
   57	      "closed": "2026-05-19",
   58	      "created": "2026-05-19",
   59	      "id": "X4",
   60	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. Legacy markdown import now accepts fully-qualified slice IDs and additional cross-cutting forms including tagged done items, blocked cross rows coerced to ready, and archived cross rows treated as done.",
   61	      "refs": [
   62	        "tools/tasktool/importer.py"
   63	      ],
   64	      "started": null,
   65	      "status": "done",
   66	      "title": "Spot fix: broaden legacy tasklist importer compatibility"
   67	    },
   68	    {
   69	      "closed": "2026-05-19",
   70	      "created": "2026-05-19",
   71	      "id": "X5",
   72	      "notes": "User-requested hook update completed outside the normal workflow for speed. Adds Stop/SubagentStop finished-agent notifications, milestone message derivation from final agent text/transcript payloads, Hypr TTS config reuse with OPENAI_API_KEY fallback, and non-TTS ding fallbacks.\nSuperseded by X8: final-text milestone parsing was removed; agent hooks now emit generic dings and semantic spoken notifications come from tasktool status changes.",
   73	      "refs": [
   74	        "hooks/agent-finished",
   75	        "hooks/hooks.json",
   76	        "hooks/hooks-cursor.json",
   77	        "tests/claude-code/test-agent-finished-hook.sh"
   78	      ],
   79	      "started": null,
   80	      "status": "done",
   81	      "title": "Add finished-agent notification hook"
   82	    },
   83	    {
   84	      "closed": "2026-05-19",
   85	      "created": "2026-05-19",
   86	      "id": "X6",
   87	      "notes": "Codex startup skips Stop/SubagentStop notification hooks when hooks.json uses async=true; fix should preserve finished-agent notification behavior while avoiding unsupported async hook registration in Codex.\nSet finished-agent Stop/SubagentStop hook registrations to async=false for Codex compatibility. The hook now backgrounds real notification playback internally so synchronous hook registration returns quickly while dry-run tests remain foreground and deterministic.",
   88	      "refs": [
   89	        "hooks/hooks.json",
   90	        "hooks/agent-finished",
   91	        "tests/claude-code/test-hook-config.sh",
   92	        "tests/claude-code/test-agent-finished-hook.sh"
   93	      ],
   94	      "started": null,
   95	      "status": "done",
   96	      "title": "Fix Codex finished-agent hook compatibility"
   97	    },
   98	    {
   99	      "closed": "2026-05-19",
  100	      "created": "2026-05-19",
  101	      "id": "X7",
  102	      "notes": "Codex reported superstar/6.0.0 because the installable local marketplace payload under plugins/superstar still declared version 6.0.0 and the version bump audit did not track that embedded manifest.\n\nBumped the embedded Codex plugin payload manifest to 6.0.1 and added it to the version bump check. Reinstalled superstar@superstar-dev, then rebuilt the 6.0.1 runtime cache as a materialized copy of this checkout with .agents excluded so Codex sees the full skills/hooks tree while codex plugin list still reports installed/enabled. Final probe shows cache version 6.0.1, skills/hooks present, and no async-hook warning.",
  103	      "refs": [
  104	        ".version-bump.json",
  105	        "plugins/superstar/.codex-plugin/plugin.json",
  106	        ".agents/plugins/marketplace.json",
  107	        "tests/codex-plugin-sync/test-version-drift.sh",
  108	        "tests/codex-plugin-sync/test-local-marketplace.sh"
  109	      ],
  110	      "started": null,
  111	      "status": "done",
  112	      "title": "Fix Superstar Codex plugin payload version drift"
  113	    },
  114	    {
  115	      "closed": "2026-05-19",
  116	      "created": "2026-05-19",
  117	      "id": "X8",
  118	      "notes": "Move semantic spoken notifications to tasktool status transitions for ready/in_progress/blocked/done. Keep agent Stop/SubagentStop hooks as generic completion dings only, with different sound styles for Claude and Codex.\nAgent Stop/SubagentStop hooks now emit generic harness-specific dings only. Semantic spoken notifications moved to tasktool status events for ready, in_progress, blocked, and done, including create, set, close, block, unblock, and archive-phase paths.",
  119	      "refs": [
  120	        "hooks/agent-finished",
  121	        "tools/tasktool/notify.py",
  122	        "tools/tasktool/commands.py",
  123	        "tools/tasktool/tests/test_notify.py",
  124	        "tools/tasktool/tests/test_commands.py",
  125	        "tools/tasktool/tests/conftest.py",
  126	        "tests/claude-code/test-agent-finished-hook.sh"
  127	      ],
  128	      "started": null,
  129	      "status": "done",
  130	      "title": "Move semantic notifications from agent hooks to tasktool status changes"
  131	    },
  132	    {
  133	      "closed": "2026-05-19",
  134	      "created": "2026-05-19",
  135	      "id": "X9",
  136	      "notes": "Rapid tasktool status changes currently spawn independent notifier processes, causing overlapping TTS/audio. Add a single-audio queue with at most three queued tasktool events; overflow should collapse to a single 'multiple other events' summary and drop further items.\nAdded a file-backed notification queue shared by agent dings and tasktool TTS. Only one worker drains audio at a time. Queue capacity is three pending events; overflow keeps the first two pending items and replaces the rest with a single 'Multiple other events' summary, dropping further burst items while the summary remains queued.",
  137	      "refs": [
  138	        "tools/tasktool/notify.py",
  139	        "tools/tasktool/tests/test_notify.py"
  140	      ],
  141	      "started": null,
  142	      "status": "done",
  143	      "title": "Coalesce bursty tasktool audio notifications"
  144	    },
  145	    {
  146	      "closed": null,
  147	      "created": "2026-05-20",
  148	      "id": "X10",
  149	      "notes": "",
  150	      "refs": [
  151	        "docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md",
  152	        "docs/reviewer/x10-verdict-parser-claude-formatting-design-spec",
  153	        "docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md"
  154	      ],
  155	      "started": null,
  156	      "status": "ready",
  157	      "title": "Harden external-review verdict parser and prompt against Claude formatting variants"
  158	    }
  159	  ],
  160	  "last_reviewed": "2026-05-18",
  161	  "north_star": "",
  162	  "phases": [
  163	    {
  164	      "closed": "2026-05-17",
  165	      "created": "2026-05-17",
  166	      "id": "P1",
  167	      "notes": "",
  168	      "phase_reviewer_chain": null,
  169	      "plan_path": null,
  170	      "planning_path": null,
  171	      "slices": [],
  172	      "spec_path": null,
  173	      "started": null,
  174	      "status": "done",
  175	      "title": "External-reviewer work (historical)"
  176	    }
  177	  ],
  178	  "project": "superstar",
  179	  "schema_version": 1
  180	}

<!-- superstar-prompt:end -->