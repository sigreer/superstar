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
/home/simon/Dev/sigreer/skills/superstar/.worktrees/x11-global-external-reviewer-bridge

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-20-X11-global-external-reviewer-bridge.md

Additional context files:
- docs/specs/2026-05-20-X11-global-external-reviewer-bridge-design.md
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

### docs/plans/2026-05-20-X11-global-external-reviewer-bridge.md

    1	# Global External Reviewer Bridge Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Make `external-reviewer` the global canonical Superstar review-chain bridge command and remove full repo-local bridge vendoring from future workflows.
    6	
    7	**Architecture:** Add a source-tree global shim installer for `external-reviewer`, matching `tasktool`'s update model. Preserve backwards compatibility through a tiny repo-local Python shim that delegates to the global command, then update live skill guidance and static tests so new sessions no longer recommend `python3 scripts/external-reviewer.py`.
    8	
    9	**Tech Stack:** Bash installer, Python stdlib compatibility shim, pytest, shell static tests, Markdown skill docs.
   10	
   11	---
   12	
   13	## Preconditions
   14	
   15	- Spec: `docs/specs/2026-05-20-X11-global-external-reviewer-bridge-design.md`
   16	- Spec review chain: `docs/reviewer/x11-global-external-reviewer-bridge-design-spec`
   17	- Task ID: `X11`
   18	- First execution step after creating or entering the implementation worktree:
   19	  ```bash
   20	  tools/tasktool/tasktool set X11 --status in_progress
   21	  ```
   22	  Expected: `X11` moves to `in_progress`.
   23	- Worktree isolation: before editing, use `superstar:using-git-worktrees` and work from an implementation worktree unless Simon explicitly opts out in that session.
   24	
   25	## Task 0: Enter an Isolated Implementation Worktree
   26	
   27	**Files:**
   28	- No file edits.
   29	
   30	- [ ] **Step 1: Invoke the worktree skill**
   31	
   32	Use `superstar:using-git-worktrees` before editing. Create or enter an X11 implementation worktree rooted outside the normal checkout, then run the rest of this plan from that worktree.
   33	
   34	Expected: implementation edits and reviewer artifacts do not dirty the normal `main` checkout.
   35	
   36	- [ ] **Step 2: Mark X11 in progress from the worktree**
   37	
   38	Run:
   39	
   40	```bash
   41	tools/tasktool/tasktool set X11 --status in_progress
   42	```
   43	
   44	Expected: X11 status becomes `in_progress`.
   45	
   46	- [ ] **Step 3: Verify bridge help before installer tests depend on it**
   47	
   48	Run:
   49	
   50	```bash
   51	python3 skills/external-review/scripts/external-reviewer.py --help | head -20
   52	```
   53	
   54	Expected: exit 0 and the output includes the `review` subcommand.
   55	
   56	## File Map
   57	
   58	- Create: `skills/external-review/install.sh`
   59	  - Installs/updates the global `external-reviewer` shim.
   60	  - Supports `EXTERNAL_REVIEWER_BIN=<dir>` for tests.
   61	  - Self-locates the source script from the installer's own path.
   62	- Create: `skills/project-setup/scripts/external-reviewer-shim.py`
   63	  - Compatibility shim template for old `python3 scripts/external-reviewer.py ...` handoffs.
   64	  - Contains no review parser/state logic.
   65	- Create: `skills/external-review/tests/test_external_reviewer_installer.py`
   66	  - Verifies install target override, generated shim contents, overwrite guard, and `--help` smoke.
   67	- Create: `skills/external-review/tests/test_external_reviewer_compat_shim.py`
   68	  - Verifies compatibility shim delegation, missing global command failure, and self-loop guard.
   69	- Modify: `skills/external-review/SKILL.md`
   70	  - Uses `external-reviewer` as the canonical bridge command.
   71	- Modify: `skills/project-setup/SKILL.md`
   72	  - Audits global `external-reviewer`; treats non-shim repo-local bridges as legacy drift.
   73	- Modify: `skills/tasklist-discipline/SKILL.md`
   74	  - Removes wording that setup vendors `scripts/external-reviewer.py`.
   75	- No change expected: `tests/claude-code/test-autonomous-review-gates.sh`
   76	  - Run it as an existing review-gate regression after wording changes.
   77	- Create or modify: `tests/claude-code/test-external-reviewer-global-command.sh`
   78	  - Static/live command contract check for skill wording and installer smoke.
   79	- Modify: reusable handoff docs under `docs/handoffs/` only if they are current templates for future sessions.
   80	
   81	## Task 1: Add Installer Contract Tests
   82	
   83	**Files:**
   84	- Create: `skills/external-review/tests/test_external_reviewer_installer.py`
   85	- Create later in Task 2: `skills/external-review/install.sh`
   86	
   87	- [ ] **Step 1: Write failing pytest coverage for the installer**
   88	
   89	Create `skills/external-review/tests/test_external_reviewer_installer.py`:
   90	
   91	```python
   92	from __future__ import annotations
   93	
   94	import os
   95	import subprocess
   96	from pathlib import Path
   97	
   98	
   99	ROOT = Path(__file__).resolve().parents[3]
  100	INSTALLER = ROOT / "skills" / "external-review" / "install.sh"
  101	
  102	
  103	def run_installer(bin_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
  104	    env = os.environ.copy()
  105	    env["EXTERNAL_REVIEWER_BIN"] = str(bin_dir)
  106	    return subprocess.run(
  107	        ["bash", str(INSTALLER), *args],
  108	        cwd=ROOT,
  109	        env=env,
  110	        text=True,
  111	        stdout=subprocess.PIPE,
  112	        stderr=subprocess.PIPE,
  113	        check=False,
  114	    )
  115	
  116	
  117	def test_installer_writes_source_tree_shim_to_configured_bin(tmp_path: Path) -> None:
  118	    bin_dir = tmp_path / "bin"
  119	
  120	    result = run_installer(bin_dir)
  121	
  122	    assert result.returncode == 0, result.stderr
  123	    shim = bin_dir / "external-reviewer"
  124	    assert shim.exists()
  125	    assert os.access(shim, os.X_OK)
  126	
  127	    text = shim.read_text(encoding="utf-8")
  128	    assert "external-reviewer shim" in text
  129	    assert "skills/external-review/scripts/external-reviewer.py" in text
  130	    assert "/home/simon/" not in text
  131	    assert "Pointing at" in result.stdout
  132	
  133	
  134	def test_generated_external_reviewer_help_works_from_any_cwd(tmp_path: Path) -> None:
  135	    bin_dir = tmp_path / "bin"
  136	    install = run_installer(bin_dir)
  137	    assert install.returncode == 0, install.stderr
  138	
  139	    env = os.environ.copy()
  140	    env["PATH"] = f"{bin_dir}:{env['PATH']}"
  141	    other_cwd = tmp_path / "other"
  142	    other_cwd.mkdir()
  143	    result = subprocess.run(
  144	        ["external-reviewer", "--help"],
  145	        cwd=other_cwd,
  146	        env=env,
  147	        text=True,
  148	        stdout=subprocess.PIPE,
  149	        stderr=subprocess.PIPE,
  150	        check=False,
  151	    )
  152	
  153	    assert result.returncode == 0, result.stderr
  154	    assert "review" in result.stdout
  155	
  156	
  157	def test_installer_refuses_to_overwrite_unknown_command(tmp_path: Path) -> None:
  158	    bin_dir = tmp_path / "bin"
  159	    bin_dir.mkdir()
  160	    target = bin_dir / "external-reviewer"
  161	    target.write_text("#!/usr/bin/env bash\necho unknown\n", encoding="utf-8")
  162	    target.chmod(0o755)
  163	
  164	    result = run_installer(bin_dir)
  165	
  166	    assert result.returncode != 0
  167	    assert "not an external-reviewer shim" in result.stderr
  168	    assert "echo unknown" in target.read_text(encoding="utf-8")
  169	
  170	
  171	def test_installer_force_overwrites_unknown_command(tmp_path: Path) -> None:
  172	    bin_dir = tmp_path / "bin"
  173	    bin_dir.mkdir()
  174	    target = bin_dir / "external-reviewer"
  175	    target.write_text("#!/usr/bin/env bash\necho unknown\n", encoding="utf-8")
  176	    target.chmod(0o755)
  177	
  178	    result = run_installer(bin_dir, "--force")
  179	
  180	    assert result.returncode == 0, result.stderr
  181	    assert "external-reviewer shim" in target.read_text(encoding="utf-8")
  182	```
  183	
  184	- [ ] **Step 2: Run the installer tests and confirm they fail**
  185	
  186	Run:
  187	
  188	```bash
  189	python3 -m pytest skills/external-review/tests/test_external_reviewer_installer.py -q
  190	```
  191	
  192	Expected: FAIL because `skills/external-review/install.sh` does not exist.
  193	
  194	## Task 2: Implement Global Installer
  195	
  196	**Files:**
  197	- Create: `skills/external-review/install.sh`
  198	- Test: `skills/external-review/tests/test_external_reviewer_installer.py`
  199	
  200	- [ ] **Step 1: Add the installer script**
  201	
  202	Create `skills/external-review/install.sh`:
  203	
  204	```bash
  205	#!/usr/bin/env bash
  206	# skills/external-review/install.sh - install/update the external-reviewer shim.
  207	set -euo pipefail
  208	
  209	SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  210	SOURCE_SCRIPT="$SCRIPT_DIR/scripts/external-reviewer.py"
  211	TARGET_DIR="${EXTERNAL_REVIEWER_BIN:-${HOME}/.local/bin}"
  212	TARGET="$TARGET_DIR/external-reviewer"
  213	FORCE="${1:-}"
  214	
  215	if [[ ! -f "$SOURCE_SCRIPT" ]]; then
  216	  echo "ERROR: source bridge not found: $SOURCE_SCRIPT" >&2
  217	  exit 1
  218	fi
  219	
  220	mkdir -p "$TARGET_DIR"
  221	
  222	if [[ -f "$TARGET" && "$FORCE" != "--force" ]]; then
  223	  if grep -q "external-reviewer shim" "$TARGET" 2>/dev/null; then
  224	    echo "external-reviewer shim already installed. Updating source path..."
  225	    # Intentionally fall through and rewrite the shim with the current source path.
  226	  else
  227	    echo "ERROR: $TARGET exists and is not an external-reviewer shim. Re-run with --force to overwrite." >&2
  228	    exit 1
  229	  fi
  230	fi
  231	
  232	cat > "$TARGET" <<EOF
  233	#!/usr/bin/env bash
  234	# external-reviewer shim - generated by Superstar skills/external-review/install.sh
  235	exec python3 "$SOURCE_SCRIPT" "\$@"
  236	EOF
  237	chmod +x "$TARGET"
  238	
  239	echo "Installed $TARGET"
  240	echo "Pointing at $SOURCE_SCRIPT"
  241	"$TARGET" --help >/dev/null
  242	echo "Self-test passed."
  243	```
  244	
  245	- [ ] **Step 2: Run focused installer tests**
  246	
  247	Run:
  248	
  249	```bash
  250	python3 -m pytest skills/external-review/tests/test_external_reviewer_installer.py -q
  251	```
  252	
  253	Expected: PASS.
  254	
  255	- [ ] **Step 3: Commit installer work**
  256	
  257	Run:
  258	
  259	```bash
  260	git add skills/external-review/install.sh skills/external-review/tests/test_external_reviewer_installer.py
  261	git commit -m "external-review: add global bridge installer"
  262	```
  263	
  264	Expected: commit succeeds.
  265	
  266	## Task 3: Add Compatibility Shim Template and Tests
  267	
  268	**Files:**
  269	- Create: `skills/project-setup/scripts/external-reviewer-shim.py`
  270	- Create: `skills/external-review/tests/test_external_reviewer_compat_shim.py`
  271	
  272	- [ ] **Step 1: Write failing compatibility shim tests**
  273	
  274	Create `skills/external-review/tests/test_external_reviewer_compat_shim.py`:
  275	
  276	```python
  277	from __future__ import annotations
  278	
  279	import os
  280	import subprocess
  281	import sys
  282	from pathlib import Path
  283	
  284	
  285	ROOT = Path(__file__).resolve().parents[3]
  286	SHIM = ROOT / "skills" / "project-setup" / "scripts" / "external-reviewer-shim.py"
  287	
  288	
  289	def run_shim(path: str, *args: str) -> subprocess.CompletedProcess[str]:
  290	    env = os.environ.copy()
  291	    env["PATH"] = f"{path}:{env.get('PATH', '')}"
  292	    return subprocess.run(
  293	        [sys.executable, str(SHIM), *args],
  294	        cwd=ROOT,
  295	        env=env,
  296	        text=True,
  297	        stdout=subprocess.PIPE,
  298	        stderr=subprocess.PIPE,
  299	        check=False,
  300	    )
  301	
  302	
  303	def test_compat_shim_delegates_to_global_external_reviewer(tmp_path: Path) -> None:
  304	    bin_dir = tmp_path / "bin"
  305	    bin_dir.mkdir()
  306	    fake = bin_dir / "external-reviewer"
  307	    log = tmp_path / "args.txt"
  308	    fake.write_text(
  309	        "#!/usr/bin/env bash\n"
  310	        f"printf '%s\\n' \"$@\" > {log}\n"
  311	        "echo delegated\n",
  312	        encoding="utf-8",
  313	    )
  314	    fake.chmod(0o755)
  315	
  316	    result = run_shim(str(bin_dir), "review", "--kind", "spec")
  317	
  318	    assert result.returncode == 0
  319	    assert result.stdout.strip() == "delegated"
  320	    assert log.read_text(encoding="utf-8").splitlines() == ["review", "--kind", "spec"]
  321	
  322	
  323	def test_compat_shim_missing_global_command_exits_127(tmp_path: Path) -> None:
  324	    bin_dir = tmp_path / "empty"
  325	    bin_dir.mkdir()
  326	
  327	    result = run_shim(str(bin_dir), "review")
  328	
  329	    assert result.returncode == 127
  330	    assert "`external-reviewer` is not on PATH" in result.stderr
  331	    assert "skills/external-review/install.sh" in result.stderr
  332	
  333	
  334	def test_compat_shim_refuses_self_resolution(tmp_path: Path) -> None:
  335	    bin_dir = tmp_path / "bin"
  336	    bin_dir.mkdir()
  337	    fake = bin_dir / "external-reviewer"
  338	    fake.symlink_to(SHIM)
  339	
  340	    result = run_shim(str(bin_dir), "review")
  341	
  342	    assert result.returncode == 127
  343	    assert "resolved `external-reviewer` back to itself" in result.stderr
  344	```
  345	
  346	- [ ] **Step 2: Run compatibility tests and confirm they fail**
  347	
  348	Run:
  349	
  350	```bash
  351	python3 -m pytest skills/external-review/tests/test_external_reviewer_compat_shim.py -q
  352	```
  353	
  354	Expected: FAIL because `skills/project-setup/scripts/external-reviewer-shim.py` does not exist.
  355	
  356	- [ ] **Step 3: Add the compatibility shim template**
  357	
  358	Create `skills/project-setup/scripts/external-reviewer-shim.py`:
  359	
  360	```python
  361	#!/usr/bin/env python3
  362	"""Compatibility shim for old Superstar handoffs.
  363	
  364	The canonical bridge is the global `external-reviewer` command.
  365	"""
  366	
  367	from __future__ import annotations
  368	
  369	import os
  370	import shutil
  371	import sys
  372	
  373	
  374	def main() -> int:
  375	    target = shutil.which("external-reviewer")
  376	    if target is None:
  377	        print(
  378	            "scripts/external-reviewer.py is a compatibility shim, but "
  379	            "`external-reviewer` is not on PATH. Install it with Superstar's "
  380	            "skills/external-review/install.sh.",
  381	            file=sys.stderr,
  382	        )
  383	        return 127
  384	
  385	    script_path = os.path.realpath(__file__)
  386	    target_path = os.path.realpath(target)
  387	    if target_path == script_path:
  388	        print(
  389	            "scripts/external-reviewer.py resolved `external-reviewer` back to "
  390	            "itself. Fix PATH so the global Superstar bridge appears before "
  391	            "this repo-local compatibility shim.",
  392	            file=sys.stderr,
  393	        )
  394	        return 127
  395	
  396	    os.execvp(target, [target, *sys.argv[1:]])
  397	    return 127
  398	
  399	
  400	if __name__ == "__main__":
  401	    raise SystemExit(main())
  402	```
  403	
  404	- [ ] **Step 4: Run compatibility tests**
  405	
  406	Run:
  407	
  408	```bash
  409	python3 -m pytest skills/external-review/tests/test_external_reviewer_compat_shim.py -q
  410	```
  411	
  412	Expected: PASS.
  413	
  414	- [ ] **Step 5: Commit compatibility shim**
  415	
  416	Run:
  417	
  418	```bash
  419	git add skills/project-setup/scripts/external-reviewer-shim.py skills/external-review/tests/test_external_reviewer_compat_shim.py
  420	git commit -m "project-setup: add external-reviewer compatibility shim"
  421	```
  422	
  423	Expected: commit succeeds.
  424	
  425	## Task 4: Update Skill Guidance and Static Guards
  426	
  427	**Files:**
  428	- Modify: `skills/external-review/SKILL.md`
  429	- Modify: `skills/project-setup/SKILL.md`
  430	- Modify: `skills/tasklist-discipline/SKILL.md`
  431	- Modify: `tests/claude-code/test-autonomous-review-gates.sh`
  432	- Create: `tests/claude-code/test-external-reviewer-global-command.sh`
  433	
  434	- [ ] **Step 1: Add failing static guard for global command guidance**
  435	
  436	Create `tests/claude-code/test-external-reviewer-global-command.sh`:
  437	
  438	```bash
  439	#!/usr/bin/env bash
  440	# Static regression test for global external-reviewer command guidance.
  441	set -euo pipefail
  442	
  443	ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
  444	
  445	fail() {
  446	    echo "FAIL: $1" >&2
  447	    exit 1
  448	}
  449	
  450	EXTERNAL_REVIEW="$ROOT/skills/external-review/SKILL.md"
  451	PROJECT_SETUP="$ROOT/skills/project-setup/SKILL.md"
  452	TASKLIST="$ROOT/skills/tasklist-discipline/SKILL.md"
  453	
  454	grep -q "external-reviewer review" "$EXTERNAL_REVIEW" \
  455	    || fail "external-review must document external-reviewer review"
  456	
  457	grep -q "global canonical review-chain bridge command" "$EXTERNAL_REVIEW" \
  458	    || fail "external-review must define external-reviewer as canonical"
  459	
  460	if grep -q "python3 scripts/external-reviewer.py" "$EXTERNAL_REVIEW"; then
  461	    fail "external-review still recommends repo-local bridge invocation"
  462	fi
  463	
  464	grep -q "external-reviewer --help" "$PROJECT_SETUP" \
  465	    || fail "project-setup must audit global external-reviewer availability"
  466	
  467	grep -q "legacy drift" "$PROJECT_SETUP" \
  468	    || fail "project-setup must flag non-shim repo-local external-reviewer.py as legacy drift"
  469	
  470	grep -q "external-reviewer-shim.py" "$PROJECT_SETUP" \
  471	    || fail "project-setup must point at the compatibility shim template"
  472	
  473	if grep -q "Copy from.*skills/external-review/scripts/external-reviewer.py" "$PROJECT_SETUP"; then
  474	    fail "project-setup still says to copy the full bridge"
  475	fi
  476	
  477	if grep -q "vendors .scripts/external-reviewer.py" "$TASKLIST"; then
  478	    fail "tasklist-discipline still says setup vendors the bridge"
  479	fi
  480	
  481	echo "PASS: global external-reviewer command guidance is present"
  482	```
  483	
  484	Run:
  485	
  486	```bash
  487	bash tests/claude-code/test-external-reviewer-global-command.sh
  488	```
  489	
  490	Expected: FAIL on current wording.
  491	
  492	- [ ] **Step 2: Update `skills/external-review/SKILL.md` command model**
  493	
  494	Edit the opening section so it says:
  495	
  496	```markdown
  497	An independent reviewer (not the coordinating agent) reviews a target document or completed slice/phase. The bridge is the global `external-reviewer` command — provider-neutral, configured via `AGENT_REVIEWER_CMD`. Each round writes a `request.md` and `response.md` pair under a per-document chain folder so the iteration history is durable and committable.
  498	
  499	**Bridge command.** `external-reviewer` is the global canonical review-chain bridge command. It is installed by `skills/external-review/install.sh` and delegates to `skills/external-review/scripts/external-reviewer.py` in the active Superstar checkout. Do not run or copy a full repo-local `scripts/external-reviewer.py` bridge. Existing repos may keep a tiny compatibility shim at that path only so old handoffs continue to delegate to the global command.
  500	```
  501	
  502	Replace the existing `**Script location.**` paragraph entirely. The resulting file must not say that `[[project-setup]]` copies the bridge to `scripts/external-reviewer.py`, and it must not present `$CLAUDE_PLUGIN_DIR/.../external-reviewer.py` as the normal consuming-project fallback.
  503	
  504	Replace the main command block with:
  505	
  506	```bash
  507	external-reviewer review \
  508	    --kind <spec|plan|post-slice|post-phase> \
  509	    --file <path/to/target.md> \
  510	    --work-id <P2.S3 | P2>   # required for post-slice / post-phase
  511	    [--context <path>]... \
  512	    [--review-depth thorough] \
  513	    [--incremental-budget-chars 400000] \
  514	    --emit json
  515	```
  516	
  517	Replace subcommand examples so they use:
  518	
  519	```bash
  520	external-reviewer manual-approve ...
  521	external-reviewer ingest-response ...
  522	external-reviewer show-limit
  523	external-reviewer clear-limit
  524	```
  525	
  526	- [ ] **Step 3: Update `skills/project-setup/SKILL.md` audit table**
  527	
  528	Replace the reviewer bridge row with these rows:
  529	
  530	```markdown
  531	| 7 | Global `external-reviewer` bridge available | `command -v external-reviewer` succeeds and `external-reviewer --help` exits 0. | Run or print `bash <active-superstar-checkout>/skills/external-review/install.sh` after confirmation. |
  532	| 7b | Repo-local `scripts/external-reviewer.py` legacy drift | Pass if absent. Compatibility-pass if present and it contains `Compatibility shim for old Superstar handoffs` plus an `external-reviewer` delegation. Partial for any other local file. | Offer to replace it with `skills/project-setup/scripts/external-reviewer-shim.py`; do not copy the full bridge. |
  533	```
  534	
  535	Update the setup boundary classification list so it says:
  536	
  537	```markdown
  538	global `external-reviewer` shim installation, repo-local `scripts/external-reviewer.py` compatibility shim replacement
  539	```
  540	
  541	This edit applies to the existing setup/migration artifact classification list near the "Setup Boundary Before Implementation" section; preserve the surrounding sentence structure while qualifying `scripts/external-reviewer.py` as compatibility-shim replacement only.
  542	
  543	Update the integration sentence so it says:
  544	
  545	```markdown
  546	- `[[external-review]]` — provides the global bridge command contract and the `AGENT_REVIEWER_CMD` expectation.
  547	```
  548	
  549	- [ ] **Step 4: Update `skills/tasklist-discipline/SKILL.md` setup boundary wording**
  550	
  551	Replace:
  552	
  553	```markdown
  554	vendors `scripts/external-reviewer.py`
  555	```
  556	
  557	with:
  558	
  559	```markdown
  560	installs the global `external-reviewer` shim or replaces a legacy repo-local reviewer bridge with the compatibility shim
  561	```
  562	
  563	Preserve the surrounding sentence structure in `skills/tasklist-discipline/SKILL.md`; only replace the stale "vendors `scripts/external-reviewer.py`" clause.
  564	
  565	- [ ] **Step 5: Wire static guard into existing test runner if needed**
  566	
  567	If `tests/claude-code/run-skill-tests.sh` enumerates individual shell tests, add:
  568	
  569	```bash
  570	"$ROOT/tests/claude-code/test-external-reviewer-global-command.sh"
  571	```
  572	
  573	If it auto-discovers `test-*.sh`, no change is needed.
  574	
  575	- [ ] **Step 6: Run static guidance tests**
  576	
  577	Run:
  578	
  579	```bash
  580	bash tests/claude-code/test-external-reviewer-global-command.sh
  581	bash tests/claude-code/test-autonomous-review-gates.sh
  582	```
  583	
  584	Expected: both PASS.
  585	
  586	- [ ] **Step 7: Commit skill guidance**
  587	
  588	Run:
  589	
  590	```bash
  591	git add skills/external-review/SKILL.md skills/project-setup/SKILL.md skills/tasklist-discipline/SKILL.md tests/claude-code/test-external-reviewer-global-command.sh
  592	git commit -m "skills: prefer global external-reviewer bridge"
  593	```
  594	
  595	Expected: commit succeeds. `tests/claude-code/test-autonomous-review-gates.sh` is expected to be unchanged. If Step 5 proves the runner needs an explicit new entry, stage that runner change by exact path before committing. If `test-autonomous-review-gates.sh` fails, capture the failing assertion and investigate the skill wording; do not relax that test just to pass.
  596	
  597	## Task 5: Full Verification and X11 Closeout Prep
  598	
  599	**Files:**
  600	- Modify: `docs/tasklist.json`

[truncated: 128 additional lines]

## Context Previews

### docs/specs/2026-05-20-X11-global-external-reviewer-bridge-design.md

    1	# X11 - Make external-reviewer a global bridge command
    2	
    3	- **Status:** spec
    4	- **Tasktool ID:** X11 (cross-cutting)
    5	- **Date:** 2026-05-20
    6	- **Owner:** Simon Greer
    7	- **Touches:** `skills/external-review/SKILL.md`, `skills/project-setup/SKILL.md`, `skills/tasklist-discipline/SKILL.md`, `skills/external-review/tests/`, `skills/project-setup/scripts/`, `tests/claude-code/`, `docs/handoffs/`
    8	
    9	## Problem
   10	
   11	Superstar currently treats the external-review bridge as a project-vendored script. Consuming repos are instructed to run:
   12	
   13	```bash
   14	python3 scripts/external-reviewer.py review ...
   15	```
   16	
   17	That duplicates the bridge/parser/state-machine code into each project. When the source bridge changes in this repo, existing project copies can silently drift.
   18	
   19	The recent Multistore failure showed the operational cost. In `/home/simon/Dev/sigreer/multistore`, the chain `docs/reviewer/p13-s4-remove-8bit-variant-P13-S4-post-slice/` contained Claude-style bare bold verdict lines:
   20	
   21	- `r1-2026-05-20T1205-primary-response.md`: `**Verdict: revise**`
   22	- `r2-2026-05-20T1214-response.md`: `**Verdict: ready**`
   23	
   24	But `chain.json` persisted `verdict: null` and `verdict_valid: false` because Multistore was running its stale repo-local `scripts/external-reviewer.py`, not the current source bridge in Superstar.
   25	
   26	The runtime paths are different for each tool:
   27	
   28	- `tasktool` is already global. `/home/simon/.local/bin/tasktool` sets `PYTHONPATH=/home/simon/Dev/sigreer/skills/superstar/tools` and runs `python3 -m tasktool`, so tasktool fixes are immediately picked up after updating Superstar.
   29	- `reviewer-agent` is already global and is only the provider subprocess. The P13.S4 response headers confirm `Reviewer command: reviewer-agent` and `Reviewer provider: claude`.
   30	- `scripts/external-reviewer.py` is the stale duplicated component. It parses reviewer responses and writes `chain.json`.
   31	- `/home/simon/.local/bin/reviewer` is not a safe canonical command because, in Multistore, it can conditionally dispatch to legacy `scripts/third-party-review.py`.
   32	
   33	The failing path was:
   34	
   35	```text
   36	agent in Multistore
   37	-> python3 scripts/external-reviewer.py review ...
   38	   # repo-local stale bridge/parser
   39	-> /home/simon/.local/bin/reviewer-agent
   40	-> claude --print ...
   41	```
   42	
   43	## Goals
   44	
   45	- Make `external-reviewer` the global canonical review-chain bridge command.
   46	- Stop copying full `scripts/external-reviewer.py` bridge implementations into projects.
   47	- Preserve the current `docs/reviewer/...` chain storage format and gate behavior.
   48	- Keep `reviewer-agent` as the global provider runner used by the bridge.
   49	- Keep `tasktool` behavior global and unchanged.
   50	- Make stale repo-local `scripts/external-reviewer.py` copies visible as legacy drift during project setup/audit.
   51	- Provide a backwards-compatible transition path for old handoffs that still invoke `python3 scripts/external-reviewer.py`.
   52	
   53	## Non-goals
   54	
   55	- Rework verdict parsing. X10 owns the Claude bare-verdict parser fix.
   56	- Change `chain.json` schema, reviewer chain folder names, or tasktool reviewer-gate logic.
   57	- Replace or route through `/home/simon/.local/bin/reviewer`.
   58	- Change `reviewer-agent` provider selection, sandboxing, prompt transport, or rate-limit behavior.
   59	- Install third-party dependencies.
   60	- Automatically edit arbitrary downstream repos from this Superstar change.
   61	
   62	## Command Model
   63	
   64	The canonical runtime model is:
   65	
   66	```text
   67	tasktool          global task tracker CLI
   68	external-reviewer global Superstar review-chain bridge
   69	reviewer-agent    global provider subprocess used by external-reviewer
   70	```
   71	
   72	The canonical review invocation becomes:
   73	
   74	```bash
   75	external-reviewer review \
   76	  --kind <spec|plan|post-slice|post-phase> \
   77	  --file <path> \
   78	  --work-id <id> \
   79	  --emit json
   80	```
   81	
   82	`--work-id` is required for `post-slice` and `post-phase` reviews. It is optional for `spec` and `plan` reviews, but recommended when a tasktool ID already exists so the chain folder and metadata stay tied to the tracked work.
   83	
   84	`external-reviewer` owns:
   85	
   86	- prompt construction;
   87	- provider command invocation;
   88	- verdict parsing;
   89	- `docs/reviewer/...` request/response artifacts;
   90	- `chain.json` updates;
   91	- rate-limit/manual-approve/human-bridge subcommands.
   92	
   93	`reviewer-agent` owns:
   94	
   95	- launching the selected provider CLI;
   96	- honoring the sandbox/output environment supplied by the bridge;
   97	- returning provider output to the bridge.
   98	
   99	The command `/home/simon/.local/bin/reviewer` is explicitly non-canonical. It may remain for local legacy workflows, but Superstar skills and setup output must not recommend it.
  100	
  101	## Design
  102	
  103	### 1. Add a global `external-reviewer` installer
  104	
  105	Add an installer analogous to `tools/tasktool/install.sh`. The preferred location is:
  106	
  107	```text
  108	skills/external-review/install.sh
  109	```
  110	
  111	The installer writes:
  112	
  113	```text
  114	~/.local/bin/external-reviewer
  115	```
  116	
  117	with executable content equivalent to:
  118	
  119	```bash
  120	#!/usr/bin/env bash
  121	# external-reviewer shim - generated by Superstar
  122	exec python3 "<absolute path resolved from the installer>/scripts/external-reviewer.py" "$@"
  123	```
  124	
  125	The installer must self-locate like `tools/tasktool/install.sh:29-30`: compute `SCRIPT_DIR` from `${BASH_SOURCE[0]}`, then resolve the sibling source script as `$SCRIPT_DIR/scripts/external-reviewer.py`. The generated shim embeds the absolute path resolved at install time. It must not contain a hardcoded `/home/simon/...` string.
  126	
  127	This local fork should point at the source checkout by default, matching the current global `tasktool` semantics on Simon's machine. `tools/tasktool/install.sh:50-54` writes a shim that exports `PYTHONPATH="${PKG_ROOT}..."` where `PKG_ROOT` is resolved from the installer's own location, so fixing `tools/tasktool/...` in the source checkout immediately fixes future global `tasktool` invocations. The `external-reviewer` installer should mirror that source-tree update model for `skills/external-review/scripts/external-reviewer.py`.
  128	
  129	Release semantics remain simple:
  130	
  131	- The local-source shim is the default for this private fork.
  132	- Plugin-cache shims are not required for this change.
  133	- If a future release wants cache-pinned behavior, it can add an explicit `--target plugin-cache` mode. That is out of scope here because current `tasktool` already points at the source tree.
  134	
  135	Installer behavior should match `tasktool`'s guardrails:
  136	
  137	- Create `~/.local/bin` if needed.
  138	- Support `EXTERNAL_REVIEWER_BIN=<dir>` so tests and CI can install into a temporary bin directory without mutating the user's real `~/.local/bin`. If unset, default to `~/.local/bin`.
  139	- Refuse to overwrite a non-Superstar `external-reviewer` unless `--force` is passed.
  140	- Treat an existing generated shim as updatable.
  141	- Run `external-reviewer --help` as a self-test before reporting success.
  142	- Print a diagnostic equivalent to `Pointing at <source external-reviewer.py>` so operators can see which source checkout the shim follows.
  143	
  144	### 2. Update `external-review` skill guidance
  145	
  146	`skills/external-review/SKILL.md` should define `external-reviewer` as the canonical bridge command.
  147	
  148	Replace the current vendoring model:
  149	
  150	```text
  151	project-setup copies skills/external-review/scripts/external-reviewer.py to scripts/external-reviewer.py
  152	```
  153	
  154	with:
  155	
  156	```text
  157	external-reviewer is installed globally by skills/external-review/install.sh. Project setup audits that it is on PATH.
  158	```
  159	
  160	All examples should use:
  161	
  162	```bash
  163	external-reviewer review ...
  164	external-reviewer manual-approve ...
  165	external-reviewer ingest-response ...
  166	external-reviewer show-limit
  167	external-reviewer clear-limit
  168	```
  169	
  170	The skill should still mention the source script path as implementation detail for tests and local development, not as the normal consuming-project command. It should keep `reviewer-agent` as the default provider subprocess and keep all `AGENT_REVIEWER_*` environment semantics unchanged.
  171	
  172	### 3. Update `project-setup` audit and scaffold behavior
  173	
  174	`skills/project-setup/SKILL.md` should stop requiring a full repo-local bridge script.
  175	
  176	Replace the current row:
  177	
  178	```text
  179	scripts/external-reviewer.py present at repo root, or AGENT_REVIEWER_CMD is set
  180	```
  181	
  182	with two distinct checks:
  183	
  184	1. **Global external-reviewer bridge available**
  185	   - Pass: `command -v external-reviewer` succeeds and `external-reviewer --help` exits 0.
  186	   - Missing: offer to run or print `bash /home/simon/Dev/sigreer/skills/superstar/skills/external-review/install.sh` in this fork, or the equivalent path to the active Superstar checkout in another install.
  187	   - Scaffold action: install the global shim only after user confirmation.
  188	
  189	2. **Repo-local legacy bridge drift**
  190	   - Pass: no `scripts/external-reviewer.py` exists.
  191	   - Compatibility-pass: `scripts/external-reviewer.py` exists and matches the documented compatibility shim marker: it contains `Compatibility shim for old Superstar handoffs` and delegates to `external-reviewer`.
  192	   - Partial: `scripts/external-reviewer.py` exists but does not match the documented compatibility shim marker. Treat every other local file as legacy drift; do not try to distinguish full vendored copies from unknown scripts.
  193	   - Scaffold action for partial: offer to replace the file with the compatibility shim, not to copy source bridge code.
  194	
  195	The setup boundary classification should treat full repo-local `scripts/external-reviewer.py` as legacy drift. A generated compatibility shim is setup/migration artifact when newly created, but it is not considered parser drift after committed.
  196	
  197	`project-setup` should continue to audit `reviewer-agent` separately:
  198	
  199	- Pass: `AGENT_REVIEWER_CMD` is set, or `reviewer-agent` is on `PATH`.
  200	- Scaffold action: print or install the existing `skills/project-setup/scripts/reviewer-agent` wrapper after confirmation.

[truncated: 218 additional lines]
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
  146	      "closed": "2026-05-20",
  147	      "created": "2026-05-20",
  148	      "id": "X10",
  149	      "notes": "",
  150	      "refs": [
  151	        "docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md",
  152	        "docs/reviewer/x10-verdict-parser-claude-formatting-design-spec",
  153	        "docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md"
  154	      ],
  155	      "started": null,
  156	      "status": "done",
  157	      "title": "Harden external-review verdict parser and prompt against Claude formatting variants"
  158	    },
  159	    {
  160	      "closed": null,
  161	      "created": "2026-05-20",
  162	      "id": "X11",
  163	      "notes": "",
  164	      "refs": [
  165	        "docs/specs/2026-05-20-X11-global-external-reviewer-bridge-design.md",
  166	        "docs/reviewer/x11-global-external-reviewer-bridge-design-spec",
  167	        "docs/plans/2026-05-20-X11-global-external-reviewer-bridge.md",
  168	        "docs/reviewer/x11-global-external-reviewer-bridge-plan",
  169	        "docs/handoffs/2026-05-20-X11-global-external-reviewer-bridge-prompt.md"
  170	      ],
  171	      "started": "2026-05-20",
  172	      "status": "in_progress",
  173	      "title": "Make external-review bridge global"
  174	    }
  175	  ],
  176	  "last_reviewed": "2026-05-18",
  177	  "north_star": "",
  178	  "phases": [
  179	    {
  180	      "closed": "2026-05-17",
  181	      "created": "2026-05-17",
  182	      "id": "P1",
  183	      "notes": "",
  184	      "phase_reviewer_chain": null,
  185	      "plan_path": null,
  186	      "planning_path": null,
  187	      "slices": [],
  188	      "spec_path": null,
  189	      "started": null,
  190	      "status": "done",
  191	      "title": "External-reviewer work (historical)"
  192	    }
  193	  ],
  194	  "project": "superstar",
  195	  "schema_version": 1
  196	}

<!-- superstar-prompt:end -->