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
/home/simon/Dev/sigreer/skills/superstar/.claude/worktrees/x16-shim-version-stamping

Target kind:
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-21-X16-shim-version-stamping.md

Additional context files:
- docs/specs/2026-05-21-X16-shim-version-stamping-design.md
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

### docs/plans/2026-05-21-X16-shim-version-stamping.md

    1	# Shim Version Stamping Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Stamp every Superstar-installed shim and hook with a version header, refuse to run when the source's `VERSION` file has drifted, and surface drift through a one-shot `scripts/deploy.sh --check` diagnostic. Eliminate the stale-shim class of bugs.
    6	
    7	**Architecture:** A new top-level `VERSION` file is the single source of truth, read at runtime by every shim. Each installer embeds a shared bash version-check fragment plus a stamped header. The Python `tasktool` entrypoint adds a startup handshake for the repo-local `pre-commit` hook (the one file that must be a content copy). `scripts/deploy.sh` ties publish + re-installation together and provides a `--check` diagnostic mode with a strict exit-status lattice. The `reviewer-agent` global file is converted from content copy to redirect shim, eliminating its content-drift class entirely.
    8	
    9	**Tech Stack:** bash (installers, shim runtime, deploy.sh, publish scripts), Python 3 (tasktool entrypoint + new test cases), pytest (test harness), `jq` (already a project dependency for JSON manipulation in bump-version.sh).
   10	
   11	**Work ID:** X16 (cross-cutting). No slice schedule — single linear delivery.
   12	
   13	---
   14	
   15	## File Structure
   16	
   17	**New files:**
   18	- `VERSION` (repo root) — single-line plain text, e.g. `6.3.2\n`. Single source of truth at runtime.
   19	- `plugins/superstar/VERSION` — relative symlink to `../../VERSION`. Flattens to a real file under `<cache>/<version>/VERSION` and `<cache>/current/VERSION` via `rsync -aL`.
   20	- `scripts/lib/shim-version-check.sh` — shared bash fragment defining `__superstar_check_version`, embedded into every generated shim by the installers.
   21	- `scripts/lib/publish-common.sh` — shared publish logic (rsync, hooks.json rewriting, manifest + VERSION verification) sourced by both `publish-to-local-codex.sh` and `publish-to-local-claude.sh`.
   22	- `scripts/deploy.sh` — top-level deploy + diagnostics entry point.
   23	- `skills/project-setup/install-reviewer-agent.sh` — new installer that emits a thin redirect shim for `~/.local/bin/reviewer-agent`.
   24	- `scripts/tests/__init__.py` and `scripts/tests/test_shim_stamping.py` — pytest module for cross-cutting shim/stamping tests.
   25	
   26	**Modified files:**
   27	- `.version-bump.json` — add `{path: "VERSION", format: "plain"}` and migrate the existing entries to the new format-aware shape.
   28	- `scripts/bump-version.sh` — add `read_plain_field` / `write_plain_field` helpers and a `format` column dispatch in `declared_files()`.
   29	- `skills/external-review/install.sh` — embed stamp header + shim-version-check fragment into the generated shim.
   30	- `skills/external-review/tests/test_external_reviewer_installer.py` — assert stamp keys + fragment present.
   31	- `scripts/publish-to-local-codex.sh` — convert to thin wrapper over `publish-common.sh`. Preserve the existing post-publish `external-reviewer/install.sh` re-run.
   32	- `scripts/publish-to-local-claude.sh` — same treatment.
   33	- `tools/tasktool/install.sh` — add stamp header + version-check fragment to the generated `~/.local/bin/tasktool` shim. Hook installer accepts legacy + new markers.
   34	- `tools/tasktool/templates/pre-commit-tasktool` — header gains stamped key/value lines while preserving the legacy `tasktool-pre-commit-hook v1` magic comment for backward recognition.
   35	- `tools/tasktool/cli.py` — add startup pre-commit-hook version handshake.
   36	- `tools/tasktool/tests/test_pre_commit_hook.py` — add cases for legacy-marker migration, header stamping, idempotency.
   37	- `skills/project-setup/SKILL.md` — delete row 7b and surrounding compat-shim language.
   38	- `tests/codex-plugin-sync/test-publish-to-local-codex.sh` — assert `current/VERSION` materialised; keep shim source-path assertion.
   39	- `tests/claude-code/test-publish-to-local-claude.sh` — same.
   40	
   41	**Deleted files:**
   42	- `skills/project-setup/scripts/external-reviewer-shim.py`
   43	- `skills/external-review/tests/test_external_reviewer_compat_shim.py`
   44	
   45	---
   46	
   47	## Task 1: VERSION file + bump-version plain format support
   48	
   49	**Files:**
   50	- Create: `VERSION` at repo root
   51	- Create: `plugins/superstar/VERSION` (symlink)
   52	- Modify: `.version-bump.json`
   53	- Modify: `scripts/bump-version.sh`
   54	
   55	- [ ] **Step 1.1: Capture current version from declared files**
   56	
   57	Read the current version (the value that bump-version.sh would consider canonical):
   58	
   59	```bash
   60	jq -r '.version' package.json
   61	```
   62	
   63	Expected: `6.3.2` (or whatever the current `package.json` version is — note it; subsequent steps reference it as `$CURRENT_VERSION`).
   64	
   65	- [ ] **Step 1.2: Create the repo-root `VERSION` file**
   66	
   67	```bash
   68	echo "6.3.2" > VERSION
   69	cat VERSION
   70	```
   71	
   72	Expected: single line `6.3.2` with trailing newline. Adjust `6.3.2` to match `$CURRENT_VERSION` from Step 1.1.
   73	
   74	- [ ] **Step 1.3: Add the plugin-payload `VERSION` symlink**
   75	
   76	```bash
   77	ln -s ../../VERSION plugins/superstar/VERSION
   78	ls -la plugins/superstar/VERSION
   79	cat plugins/superstar/VERSION
   80	```
   81	
   82	Expected: `lrwxrwxrwx ... plugins/superstar/VERSION -> ../../VERSION` and the contents match `6.3.2`. Symlink is **relative** so it stays valid inside the published cache trees after `rsync -aL` flattens it.
   83	
   84	- [ ] **Step 1.4: Write the failing bump-version plain-format test (new test file)**
   85	
   86	Create `scripts/tests/__init__.py` (empty) and `scripts/tests/test_bump_version_plain_format.py`:
   87	
   88	```python
   89	"""Tests for the plain-format support added to scripts/bump-version.sh."""
   90	from __future__ import annotations
   91	
   92	import json
   93	import subprocess
   94	from pathlib import Path
   95	
   96	import pytest
   97	
   98	REPO_ROOT = Path(__file__).resolve().parents[2]
   99	REAL_SCRIPT = REPO_ROOT / "scripts" / "bump-version.sh"
  100	
  101	
  102	def _seed_repo(tmp_path: Path, version: str) -> Path:
  103	    """Build an isolated fake repo so the script's own REPO_ROOT resolution
  104	    (`cd $SCRIPT_DIR/.. && pwd`) lands inside tmp_path and cannot mutate the
  105	    real checkout."""
  106	    (tmp_path / "package.json").write_text(json.dumps({"version": version}, indent=2) + "\n")
  107	    (tmp_path / "VERSION").write_text(version + "\n")
  108	    config = {
  109	        "files": [
  110	            {"path": "package.json", "field": "version"},
  111	            {"path": "VERSION", "format": "plain"},
  112	        ],
  113	        "audit": {"exclude": []},
  114	    }
  115	    (tmp_path / ".version-bump.json").write_text(json.dumps(config, indent=2) + "\n")
  116	    (tmp_path / "scripts").mkdir(exist_ok=True)
  117	    # Symlink the real bump-version.sh into the fake repo's scripts dir. We
  118	    # MUST invoke this symlinked path (not REAL_SCRIPT) so the script's
  119	    # `dirname "$0"` -> `cd $SCRIPT_DIR/..` resolves to tmp_path. Invoking
  120	    # REAL_SCRIPT directly would resolve to the real superstar checkout and
  121	    # mutate its declared files.
  122	    fake_script = tmp_path / "scripts" / "bump-version.sh"
  123	    fake_script.symlink_to(REAL_SCRIPT)
  124	    return tmp_path
  125	
  126	
  127	def _run(script_args: list[str], repo: Path) -> subprocess.CompletedProcess:
  128	    """Invoke the symlinked bump-version.sh inside `repo` so REPO_ROOT
  129	    resolution stays inside the fake repo."""
  130	    fake_script = repo / "scripts" / "bump-version.sh"
  131	    assert fake_script.exists(), "fake script symlink missing — call _seed_repo first"
  132	    return subprocess.run(
  133	        ["bash", str(fake_script), *script_args],
  134	        cwd=repo,
  135	        capture_output=True,
  136	        text=True,
  137	        check=False,
  138	    )
  139	
  140	
  141	def test_check_lists_plain_version(tmp_path: Path) -> None:
  142	    repo = _seed_repo(tmp_path, "1.2.3")
  143	    result = _run(["--check"], repo)
  144	    assert result.returncode == 0, result.stderr
  145	    assert "VERSION" in result.stdout
  146	    assert "1.2.3" in result.stdout
  147	
  148	
  149	def test_bump_writes_plain_version(tmp_path: Path) -> None:
  150	    repo = _seed_repo(tmp_path, "1.2.3")
  151	    result = _run(["1.2.4"], repo)
  152	    assert result.returncode == 0, result.stderr
  153	    assert (repo / "VERSION").read_text().strip() == "1.2.4"
  154	    assert json.loads((repo / "package.json").read_text())["version"] == "1.2.4"
  155	
  156	
  157	def test_check_detects_drift_between_plain_and_json(tmp_path: Path) -> None:
  158	    repo = _seed_repo(tmp_path, "1.2.3")
  159	    (repo / "VERSION").write_text("1.2.4\n")
  160	    result = _run(["--check"], repo)
  161	    assert result.returncode != 0
  162	    assert "DRIFT" in result.stdout
  163	```
  164	
  165	- [ ] **Step 1.5: Run the test to confirm it fails (script doesn't know `format: plain` yet)**
  166	
  167	```bash
  168	python3 -m pytest scripts/tests/test_bump_version_plain_format.py -v
  169	```
  170	
  171	Expected: at least one test fails — `bump-version.sh` does not yet read the `format` field and will silently skip the VERSION file (since `read_json_field` returns null) or error on `jq` trying to read `.version` from a non-JSON file.
  172	
  173	- [ ] **Step 1.6: Update `.version-bump.json` to declare VERSION first and add the format key**
  174	
  175	Replace the file at repo root with:
  176	
  177	```json
  178	{
  179	  "files": [
  180	    { "path": "VERSION", "format": "plain" },
  181	    { "path": "package.json", "field": "version" },
  182	    { "path": ".claude-plugin/plugin.json", "field": "version" },
  183	    { "path": ".cursor-plugin/plugin.json", "field": "version" },
  184	    { "path": ".codex-plugin/plugin.json", "field": "version" },
  185	    { "path": ".claude-plugin/marketplace.json", "field": "plugins.0.version" },
  186	    { "path": ".agents/plugins/marketplace.json", "field": "plugins.0.version" },
  187	    { "path": "plugins/superstar/.codex-plugin/plugin.json", "field": "version" },
  188	    { "path": "gemini-extension.json", "field": "version" }
  189	  ],
  190	  "audit": {
  191	    "exclude": [
  192	      "CHANGELOG.md",
  193	      "RELEASE-NOTES.md",
  194	      "node_modules",
  195	      ".git",
  196	      ".version-bump.json",
  197	      "scripts/bump-version.sh"
  198	    ]
  199	  }
  200	}
  201	```
  202	
  203	The JSON entries continue to carry `field`; the new VERSION entry carries `format` instead. `bump-version.sh` treats absence of `format` as the default (`"json"`).
  204	
  205	- [ ] **Step 1.7: Add plain-format helpers to `scripts/bump-version.sh`**
  206	
  207	Edit `scripts/bump-version.sh`. Add these two helpers immediately below `write_json_field` (~ line 38):
  208	
  209	```bash
  210	# Read a plain single-line VERSION-style file.
  211	read_plain_field() {
  212	  local file="$1"
  213	  head -n1 "$file" | tr -d '[:space:]'
  214	}
  215	
  216	# Write a plain single-line VERSION-style file (single trailing newline).
  217	write_plain_field() {
  218	  local file="$1" value="$2"
  219	  printf '%s\n' "$value" > "$file"
  220	}
  221	```
  222	
  223	- [ ] **Step 1.8: Update `declared_files()` to emit a `format` column**
  224	
  225	Replace the existing `declared_files()` function with:
  226	
  227	```bash
  228	# Read declared files from config.
  229	# Outputs lines of "path<TAB>field<TAB>format" where format defaults to "json".
  230	declared_files() {
  231	  jq -r '.files[] | "\(.path)\t\(.field // "")\t\(.format // "json")"' "$CONFIG"
  232	}
  233	```
  234	
  235	- [ ] **Step 1.9: Dispatch on format in `cmd_check`**
  236	
  237	Find the loop in `cmd_check` that reads each declared file and replace its inner body to dispatch:
  238	
  239	```bash
  240	  while IFS=$'\t' read -r path field format; do
  241	    local fullpath="$REPO_ROOT/$path"
  242	    if [[ ! -f "$fullpath" ]]; then
  243	      printf "  %-45s  MISSING\n" "$path"
  244	      has_drift=1
  245	      continue
  246	    fi
  247	    local ver label
  248	    if [[ "$format" == "plain" ]]; then
  249	      ver=$(read_plain_field "$fullpath")
  250	      label="$path (plain)"
  251	    else
  252	      ver=$(read_json_field "$fullpath" "$field")
  253	      label="$path ($field)"
  254	    fi
  255	    printf "  %-45s  %s\n" "$label" "$ver"
  256	    versions+=("$ver")
  257	  done < <(declared_files)
  258	```
  259	
  260	- [ ] **Step 1.10: Dispatch on format in `cmd_bump` and `cmd_audit`**
  261	
  262	Apply the same `format` dispatch inside the `while` loops in `cmd_bump` (writing) and inside the version-determination loop of `cmd_audit` (reading). The audit "most common version" computation should consume the same path/field/format tuple.
  263	
  264	For `cmd_bump`'s inner write block:
  265	
  266	```bash
  267	  while IFS=$'\t' read -r path field format; do
  268	    local fullpath="$REPO_ROOT/$path"
  269	    if [[ ! -f "$fullpath" ]]; then
  270	      echo "  SKIP (missing): $path"
  271	      continue
  272	    fi
  273	    local old_ver label
  274	    if [[ "$format" == "plain" ]]; then
  275	      old_ver=$(read_plain_field "$fullpath")
  276	      write_plain_field "$fullpath" "$new_version"
  277	      label="$path (plain)"
  278	    else
  279	      old_ver=$(read_json_field "$fullpath" "$field")
  280	      write_json_field "$fullpath" "$field" "$new_version"
  281	      label="$path ($field)"
  282	    fi
  283	    printf "  %-45s  %s -> %s\n" "$label" "$old_ver" "$new_version"
  284	  done < <(declared_files)
  285	```
  286	
  287	For `cmd_audit`'s version-detection block (the subshell that emits versions to `sort | uniq -c`):
  288	
  289	```bash
  290	    while IFS=$'\t' read -r path field format; do
  291	      local fullpath="$REPO_ROOT/$path"
  292	      if [[ ! -f "$fullpath" ]]; then continue; fi
  293	      if [[ "$format" == "plain" ]]; then
  294	        read_plain_field "$fullpath"
  295	      else
  296	        read_json_field "$fullpath" "$field"
  297	      fi
  298	    done < <(declared_files) | sort | uniq -c | sort -rn | head -1 | awk '{print $2}'
  299	```
  300	
  301	- [ ] **Step 1.11: Run the new tests to verify they pass**
  302	
  303	```bash
  304	python3 -m pytest scripts/tests/test_bump_version_plain_format.py -v
  305	```
  306	
  307	Expected: all three tests pass.
  308	
  309	- [ ] **Step 1.12: Run `--check` against the real repo to confirm no regressions**
  310	
  311	```bash
  312	bash scripts/bump-version.sh --check
  313	```
  314	
  315	Expected: VERSION listed as a row with `(plain)` annotation; all declared files show the same version; "All declared files are in sync at ..." line at the bottom; exit 0.
  316	
  317	- [ ] **Step 1.13: Run `--audit` to confirm no regressions**
  318	
  319	```bash
  320	bash scripts/bump-version.sh --audit
  321	```
  322	
  323	Expected: standard audit output; no Python tracebacks; either "No undeclared files contain the version string. All clear." or a list of already-known undeclared files (unchanged from before).
  324	
  325	- [ ] **Step 1.14: Commit**
  326	
  327	```bash
  328	git add VERSION plugins/superstar/VERSION .version-bump.json scripts/bump-version.sh \
  329	        scripts/tests/__init__.py scripts/tests/test_bump_version_plain_format.py
  330	git commit -m "X16.T1: add VERSION file + plain-format support in bump-version"
  331	```
  332	
  333	---
  334	
  335	## Task 2: Shared shim-version-check fragment
  336	
  337	**Files:**
  338	- Create: `scripts/lib/shim-version-check.sh`
  339	- Create: `scripts/tests/test_shim_version_check_fragment.py`
  340	
  341	- [ ] **Step 2.1: Write the failing fragment test**
  342	
  343	Create `scripts/tests/test_shim_version_check_fragment.py`:
  344	
  345	```python
  346	"""Direct tests for scripts/lib/shim-version-check.sh."""
  347	from __future__ import annotations
  348	
  349	import subprocess
  350	import textwrap
  351	from pathlib import Path
  352	
  353	REPO_ROOT = Path(__file__).resolve().parents[2]
  354	FRAGMENT = REPO_ROOT / "scripts" / "lib" / "shim-version-check.sh"
  355	
  356	
  357	def _run_fragment(tmp_path: Path, shim_version: str, source_version: str | None) -> subprocess.CompletedProcess:
  358	    """Source the fragment in a synthetic harness; call the function; return result."""
  359	    source_root = tmp_path / "fake-source"
  360	    source_root.mkdir()
  361	    if source_version is not None:
  362	        (source_root / "VERSION").write_text(source_version + "\n")
  363	    script = textwrap.dedent(f"""
  364	        #!/usr/bin/env bash
  365	        source "{FRAGMENT}"
  366	        __superstar_check_version "{shim_version}" "test-shim" "{source_root}" "skills/test/install.sh"
  367	        echo "REACHED_END"
  368	    """)
  369	    return subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=False)
  370	
  371	
  372	def test_versions_match_exec_continues(tmp_path: Path) -> None:
  373	    result = _run_fragment(tmp_path, "1.0.0", "1.0.0")
  374	    assert result.returncode == 0
  375	    assert "REACHED_END" in result.stdout
  376	
  377	
  378	def test_version_drift_hard_exits(tmp_path: Path) -> None:
  379	    result = _run_fragment(tmp_path, "1.0.0", "1.0.1")
  380	    assert result.returncode == 1
  381	    assert "REACHED_END" not in result.stdout
  382	    assert "test-shim shim is 1.0.0 but Superstar source is 1.0.1" in result.stderr
  383	    assert "skills/test/install.sh" in result.stderr
  384	
  385	
  386	def test_missing_version_file_exec_continues(tmp_path: Path) -> None:
  387	    """No VERSION file at the source root must NOT block exec."""
  388	    result = _run_fragment(tmp_path, "1.0.0", None)
  389	    assert result.returncode == 0
  390	    assert "REACHED_END" in result.stdout
  391	
  392	
  393	def test_empty_shim_version_exec_continues(tmp_path: Path) -> None:
  394	    result = _run_fragment(tmp_path, "", "1.0.0")
  395	    assert result.returncode == 0
  396	    assert "REACHED_END" in result.stdout
  397	```
  398	
  399	- [ ] **Step 2.2: Run test to verify it fails (fragment doesn't exist yet)**
  400	
  401	```bash
  402	python3 -m pytest scripts/tests/test_shim_version_check_fragment.py -v
  403	```
  404	
  405	Expected: errors with `bash: scripts/lib/shim-version-check.sh: No such file or directory` (or `source` failure).
  406	
  407	- [ ] **Step 2.3: Create the fragment**
  408	
  409	Create `scripts/lib/shim-version-check.sh`:
  410	
  411	```bash
  412	# scripts/lib/shim-version-check.sh
  413	#
  414	# Embedded by Superstar shim installers (skills/external-review/install.sh,
  415	# skills/project-setup/install-reviewer-agent.sh, tools/tasktool/install.sh).
  416	# Provides __superstar_check_version, which hard-exits the calling shim if
  417	# the stamped shim version differs from $SOURCE_ROOT/VERSION.
  418	#
  419	# Strict failure ONLY when BOTH sides are readable AND they differ. Missing or
  420	# unreadable VERSION, or an empty stamped value, means "cannot compare" and
  421	# the shim continues to exec normally.
  422	#
  423	# Args:
  424	#   $1  shim_version       e.g. "6.3.2"
  425	#   $2  shim_name          e.g. "external-reviewer"
  426	#   $3  source_root        absolute or $HOME/... path
  427	#   $4  installer          relative path under source_root, e.g.
  428	#                          "skills/external-review/install.sh"
  429	
  430	__superstar_check_version() {
  431	    local shim_version="$1"
  432	    local shim_name="$2"
  433	    local source_root="$3"
  434	    local installer="$4"
  435	
  436	    [[ -n "$shim_version" ]] || return 0
  437	    local version_file="$source_root/VERSION"
  438	    [[ -r "$version_file" ]] || return 0
  439	
  440	    local src_version
  441	    src_version="$(head -n1 "$version_file" 2>/dev/null | tr -d '[:space:]')"
  442	    [[ -n "$src_version" ]] || return 0
  443	
  444	    if [[ "$src_version" != "$shim_version" ]]; then
  445	        printf 'ERROR: %s shim is %s but Superstar source is %s\n' \
  446	            "$shim_name" "$shim_version" "$src_version" >&2
  447	        printf 'Re-run: bash %s/%s\n' "$source_root" "$installer" >&2
  448	        exit 1
  449	    fi
  450	}
  451	```
  452	
  453	- [ ] **Step 2.4: Run tests to verify they pass**
  454	
  455	```bash
  456	python3 -m pytest scripts/tests/test_shim_version_check_fragment.py -v
  457	```
  458	
  459	Expected: all four tests pass.
  460	
  461	- [ ] **Step 2.5: Commit**
  462	
  463	```bash
  464	git add scripts/lib/shim-version-check.sh scripts/tests/test_shim_version_check_fragment.py
  465	git commit -m "X16.T2: add shared shim-version-check fragment"
  466	```
  467	
  468	---
  469	
  470	## Task 3: External-reviewer installer — embed stamp and check
  471	
  472	**Files:**
  473	- Modify: `skills/external-review/install.sh`
  474	- Modify: `skills/external-review/tests/test_external_reviewer_installer.py`
  475	
  476	- [ ] **Step 3.1: Update the existing installer test to expect the new stamp**
  477	
  478	Edit `skills/external-review/tests/test_external_reviewer_installer.py`. Below the existing assertion that the generated shim contains `"external-reviewer shim"`, add three new test functions:
  479	
  480	```python
  481	def test_generated_shim_carries_stamp_header(tmp_path: Path) -> None:
  482	    bin_dir = tmp_path / "bin"
  483	    source_root = _seed_fake_source(tmp_path / "src", version="1.0.0")
  484	    _run_installer(source_root=source_root, bin_dir=bin_dir)
  485	    text = (bin_dir / "external-reviewer").read_text(encoding="utf-8")
  486	    assert "# superstar-shim" in text
  487	    assert "superstar-shim-name: external-reviewer" in text
  488	    assert "superstar-shim-version: 1.0.0" in text
  489	    assert "superstar-shim-source-root:" in text
  490	    assert "superstar-shim-installer: skills/external-review/install.sh" in text
  491	    assert "superstar-shim-generated-at:" in text
  492	
  493	
  494	def test_generated_shim_embeds_version_check_fragment(tmp_path: Path) -> None:
  495	    bin_dir = tmp_path / "bin"
  496	    source_root = _seed_fake_source(tmp_path / "src", version="1.0.0")
  497	    _run_installer(source_root=source_root, bin_dir=bin_dir)
  498	    text = (bin_dir / "external-reviewer").read_text(encoding="utf-8")
  499	    assert "__superstar_check_version()" in text
  500	    assert '__superstar_check_version "1.0.0"' in text
  501	
  502	
  503	def test_generated_shim_refuses_when_source_version_drifts(tmp_path: Path) -> None:
  504	    bin_dir = tmp_path / "bin"
  505	    source_root = _seed_fake_source(tmp_path / "src", version="1.0.0")
  506	    _run_installer(source_root=source_root, bin_dir=bin_dir)
  507	    # Bump VERSION at the source root without re-running the installer.
  508	    (source_root / "VERSION").write_text("1.0.1\n")
  509	    result = subprocess.run(
  510	        [str(bin_dir / "external-reviewer"), "--help"],
  511	        capture_output=True, text=True, check=False,
  512	    )
  513	    assert result.returncode == 1
  514	    assert "external-reviewer shim is 1.0.0 but Superstar source is 1.0.1" in result.stderr
  515	```
  516	
  517	You'll need helpers `_seed_fake_source(path, version)` (creates a fake `SOURCE_ROOT` with `skills/external-review/scripts/external-reviewer.py` stub that prints "STUB INVOKED" and a `VERSION` file) and `_run_installer(source_root, bin_dir)` (runs the installer with the right env vars). Add them at the top of the file if not present:
  518	
  519	```python
  520	def _seed_fake_source(path: Path, version: str) -> Path:
  521	    path.mkdir(parents=True, exist_ok=True)
  522	    (path / "VERSION").write_text(version + "\n")
  523	    script_dir = path / "skills" / "external-review" / "scripts"
  524	    script_dir.mkdir(parents=True)
  525	    stub = script_dir / "external-reviewer.py"
  526	    stub.write_text("#!/usr/bin/env python3\nimport sys\nprint('STUB INVOKED')\nsys.exit(0)\n")
  527	    stub.chmod(0o755)
  528	    # Required by install.sh (it sources scripts/lib/shim-version-check.sh).
  529	    lib_dir = path / "scripts" / "lib"
  530	    lib_dir.mkdir(parents=True)
  531	    real_fragment = REPO_ROOT / "scripts" / "lib" / "shim-version-check.sh"
  532	    (lib_dir / "shim-version-check.sh").write_text(real_fragment.read_text())
  533	    # Also copy the installer itself so the SCRIPT_DIR/PLUGIN_ROOT resolution works.
  534	    installer_dir = path / "skills" / "external-review"
  535	    real_installer = REPO_ROOT / "skills" / "external-review" / "install.sh"
  536	    (installer_dir / "install.sh").write_text(real_installer.read_text())
  537	    (installer_dir / "install.sh").chmod(0o755)
  538	    return path
  539	
  540	
  541	def _run_installer(*, source_root: Path, bin_dir: Path) -> subprocess.CompletedProcess:
  542	    return subprocess.run(
  543	        ["bash", str(source_root / "skills" / "external-review" / "install.sh")],
  544	        env={
  545	            "EXTERNAL_REVIEWER_SOURCE_ROOT": str(source_root),
  546	            "EXTERNAL_REVIEWER_BIN": str(bin_dir),
  547	            "HOME": str(bin_dir.parent),
  548	            "PATH": os.environ["PATH"],
  549	        },
  550	        capture_output=True, text=True, check=True,
  551	    )
  552	```
  553	
  554	(Adjust `REPO_ROOT` import to use the existing path constant in this file. Add `import os, subprocess` if not already imported.)
  555	
  556	- [ ] **Step 3.2: Run the new tests to verify they fail**
  557	
  558	```bash
  559	python3 -m pytest skills/external-review/tests/test_external_reviewer_installer.py -v
  560	```
  561	
  562	Expected: the three new tests fail; the generated shim does not yet carry the stamp or the embedded fragment.
  563	
  564	- [ ] **Step 3.3: Modify the installer to stamp and embed**
  565	
  566	Edit `skills/external-review/install.sh`. Replace the `cat > "$TARGET" <<EOF` block at the end with:
  567	
  568	```bash
  569	FRAGMENT="$SOURCE_ROOT/scripts/lib/shim-version-check.sh"
  570	if [[ ! -r "$FRAGMENT" ]]; then
  571	  echo "ERROR: shim-version-check fragment missing: $FRAGMENT" >&2
  572	  exit 1
  573	fi
  574	SRC_VERSION="$(head -n1 "$SOURCE_ROOT/VERSION" | tr -d '[:space:]')"
  575	if [[ -z "$SRC_VERSION" ]]; then
  576	  echo "ERROR: $SOURCE_ROOT/VERSION is missing or empty" >&2
  577	  exit 1
  578	fi
  579	GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  580	
  581	if [[ "$SOURCE_SCRIPT" == "$HOME/"* ]]; then
  582	  SOURCE_EXPR="\$HOME/${SOURCE_SCRIPT#"$HOME/"}"
  583	  STAMP_SOURCE_ROOT="\$HOME/${SOURCE_ROOT#"$HOME/"}"
  584	else
  585	  SOURCE_EXPR="$SOURCE_SCRIPT"
  586	  STAMP_SOURCE_ROOT="$SOURCE_ROOT"
  587	fi
  588	
  589	{
  590	  cat <<EOF
  591	#!/usr/bin/env bash
  592	# external-reviewer shim - generated by Superstar skills/external-review/install.sh
  593	# superstar-shim
  594	# superstar-shim-name: external-reviewer
  595	# superstar-shim-version: $SRC_VERSION
  596	# superstar-shim-source-root: $STAMP_SOURCE_ROOT
  597	# superstar-shim-installer: skills/external-review/install.sh
  598	# superstar-shim-generated-at: $GENERATED_AT
  599	
  600	EOF

[truncated: 1797 additional lines]

## Context Previews

### docs/specs/2026-05-21-X16-shim-version-stamping-design.md

    1	# X16 — Stamp installed shims and enforce version drift refusal
    2	
    3	**Status:** spec
    4	**Work ID:** X16
    5	**Created:** 2026-05-21
    6	
    7	## Problem
    8	
    9	Superstar installs executables outside the repo (`~/.local/bin/external-reviewer`, `~/.local/bin/reviewer-agent`, `~/.local/bin/tasktool`) and per-repo (`.git/hooks/pre-commit`). When the source code changes but those installed copies/shims don't get re-deployed, behaviour silently diverges: bumps appear to land everywhere, but the same errors keep firing because a stale shim is still being invoked. The current install scripts have no runtime self-check; the bump script has no concept of "files installed outside the repo"; and there is no diagnostic that surfaces drift.
   10	
   11	A secondary problem: the four installed files use two different patterns. Three are bash redirect shims (cheap re-deploys), one (`reviewer-agent`) is a full content copy of a wrapper script (silent content drift on every change). The compat shim at `skills/project-setup/scripts/external-reviewer-shim.py` adds a third pattern (per-repo Python shim) without a clear benefit anymore now that the global `external-reviewer` is the canonical bridge.
   12	
   13	## Goals
   14	
   15	1. **Make stale installed shims fail loudly,** not silently invoke old code.
   16	2. **Make the install patterns uniform** — all three global shims become thin bash redirects to source.
   17	3. **Make bump-version.sh purely a source-state mutator.** No install side-effects. Existing deploy/publish scripts remain the only thing that mutates live machine entrypoints.
   18	4. **Give the user a one-shot diagnostic** that surfaces source-vs-installed drift across all four files.
   19	5. **Drop dead weight:** remove the project-setup compat shim and its scaffolding.
   20	
   21	## Non-goals
   22	
   23	- Auto-discovery of multiple Superstar checkouts. A shim's source root is fixed at install time; switching checkouts means re-running install.
   24	- Stamping the materialized plugin cache `current/` trees as separately versioned artifacts. They are deploy outputs of `VERSION`, verified by `deploy.sh --check`, not stamped.
   25	- A separate `tasktool doctor` command. Deferred — diagnostics live in `deploy.sh --check` for now.
   26	- Changes to provider-bypass safety policy in `reviewer-agent`. The wrapper's runtime contract stays identical.
   27	
   28	## Files in scope
   29	
   30	| Path | Pattern after this change | Installer |
   31	|---|---|---|
   32	| `~/.local/bin/external-reviewer` | Bash redirect shim (unchanged pattern) | `skills/external-review/install.sh` |
   33	| `~/.local/bin/reviewer-agent` | **Converted** from copy to bash redirect shim | New `skills/project-setup/install-reviewer-agent.sh` |
   34	| `~/.local/bin/tasktool` | Bash redirect shim (unchanged pattern) | `tools/tasktool/install.sh` |
   35	| `<repo>/.git/hooks/pre-commit` | Bash copy (necessarily — git enforces the path); stamped header, runtime checked by tasktool | `tools/tasktool/install.sh --hook` |
   36	
   37	## Removals
   38	
   39	- Delete `skills/project-setup/scripts/external-reviewer-shim.py`.
   40	- Delete the project-setup precondition row 7b and its surrounding compat-shim language in `skills/project-setup/SKILL.md`.
   41	- Delete `skills/external-review/tests/test_external_reviewer_compat_shim.py`.
   42	- Old handoff documents that hardcode `python3 scripts/external-reviewer.py` are out of support. The break is intentional and loud.
   43	
   44	## Design
   45	
   46	### 1. Single source of truth: top-level `VERSION` file
   47	
   48	Add a single-line plain-text file at the repo root:
   49	
   50	```
   51	6.3.2
   52	```
   53	
   54	(trailing newline; no whitespace).
   55	
   56	`.version-bump.json` gains a new declared file with `"format": "plain"`:
   57	
   58	```json
   59	{ "path": "VERSION", "format": "plain" }
   60	```
   61	
   62	`scripts/bump-version.sh` learns two new code paths:
   63	
   64	- `read_plain_field(file)` — `head -n1 "$file" | tr -d '[:space:]'`.
   65	- `write_plain_field(file, value)` — `printf '%s\n' "$value" > "$file"`.
   66	
   67	Both `--check` and `--audit` print VERSION as a normal row, not a special case. The existing "all declared files in sync" check includes it.
   68	
   69	VERSION is the only file every shim reads at runtime. The JSON manifests stay where they are; they remain bumped in lock-step but are not consulted by shims.
   70	
   71	### 2. Shim stamp header (uniform across all three installers)
   72	
   73	Every generated shim carries this header block, with values interpolated at generation time:
   74	
   75	```bash
   76	#!/usr/bin/env bash
   77	# superstar-shim
   78	# superstar-shim-name: external-reviewer
   79	# superstar-shim-version: 6.3.2
   80	# superstar-shim-source-root: $HOME/Dev/sigreer/skills/superstar
   81	# superstar-shim-installer: skills/external-review/install.sh
   82	# superstar-shim-generated-at: 2026-05-21T14:23:07Z
   83	```
   84	
   85	Notes:
   86	- `source-root` stores `$HOME/...` literally when the resolved root is under `$HOME`, mirroring the existing `external-reviewer` installer behaviour. This keeps the shim portable across user accounts.
   87	- `generated-at` distinguishes "same version, regenerated against a different `current/` root" from "untouched since last bump" during diagnostics.
   88	- `target` is intentionally omitted — redundant with the shim's own file path; diagnostics already know where they found the file.
   89	
   90	### 3. Shared runtime check fragment
   91	
   92	A template fragment lives at `scripts/lib/shim-version-check.sh`:
   93	
   94	```bash
   95	# Embedded into every generated Superstar shim.
   96	# Hard-exits only if BOTH source VERSION and stamped shim version are readable
   97	# AND they differ. Missing/unreadable VERSION is treated as 'cannot compare' and
   98	# the shim execs normally (existing path-resolution errors handle the broken
   99	# case more loudly than a spurious version warning would).
  100	__superstar_check_version() {
  101	    local shim_version="$1"
  102	    local shim_name="$2"
  103	    local source_root="$3"
  104	    local installer="$4"
  105	
  106	    local version_file="$source_root/VERSION"
  107	    [[ -r "$version_file" ]] || return 0
  108	    local src_version
  109	    src_version="$(head -n1 "$version_file" 2>/dev/null | tr -d '[:space:]')"
  110	    [[ -n "$src_version" && -n "$shim_version" ]] || return 0
  111	
  112	    if [[ "$src_version" != "$shim_version" ]]; then
  113	        printf 'ERROR: %s shim is %s but Superstar source is %s\n' \
  114	            "$shim_name" "$shim_version" "$src_version" >&2
  115	        printf 'Re-run: bash %s/%s\n' "$source_root" "$installer" >&2
  116	        exit 1
  117	    fi
  118	}
  119	```
  120	
  121	Each installer reads this fragment and inlines it into the generated shim. The shim header values are passed as arguments to `__superstar_check_version` so the fragment itself contains no installer-specific values — one source of truth, three identical embeddings.
  122	
  123	Generated shim shape (illustrative — external-reviewer):
  124	
  125	```bash
  126	#!/usr/bin/env bash
  127	# superstar-shim
  128	# superstar-shim-name: external-reviewer
  129	# superstar-shim-version: 6.3.2
  130	# superstar-shim-source-root: $HOME/Dev/sigreer/skills/superstar
  131	# superstar-shim-installer: skills/external-review/install.sh
  132	# superstar-shim-generated-at: 2026-05-21T14:23:07Z
  133	
  134	<inlined __superstar_check_version function from scripts/lib/shim-version-check.sh>
  135	
  136	__superstar_check_version \
  137	    "6.3.2" \
  138	    "external-reviewer" \
  139	    "$HOME/Dev/sigreer/skills/superstar" \
  140	    "skills/external-review/install.sh"
  141	
  142	exec python3 "$HOME/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py" "$@"
  143	```
  144	
  145	### 4. Strict failure semantics
  146	
  147	A shim hard-exits (status 1, no `exec`) **if and only if** all three hold:
  148	
  149	1. `$SOURCE_ROOT/VERSION` is readable.
  150	2. The stamped `shim-version` value is non-empty.
  151	3. The two values differ after whitespace-trim.
  152	
  153	Any other state — VERSION missing, VERSION empty, stamped value missing — and the shim execs as normal. The existing path-resolution errors (source script not found, etc.) are louder and more diagnostic than a half-informed version warning.
  154	
  155	### 5. `reviewer-agent` migration
  156	
  157	New file `skills/project-setup/install-reviewer-agent.sh`. Mirrors the structure of `skills/external-review/install.sh`:
  158	
  159	- Resolves `SOURCE_ROOT` (with the same `current/` preference and `$HOME` literalization).
  160	- Verifies `$SOURCE_ROOT/skills/project-setup/scripts/reviewer-agent` exists and is executable.
  161	- Generates `${EXTERNAL_REVIEWER_BIN:-$HOME/.local/bin}/reviewer-agent` as a thin bash redirect:
  162	
  163	```bash
  164	#!/usr/bin/env bash
  165	# superstar-shim
  166	# superstar-shim-name: reviewer-agent
  167	# superstar-shim-version: 6.3.2
  168	# superstar-shim-source-root: $HOME/Dev/sigreer/skills/superstar
  169	# superstar-shim-installer: skills/project-setup/install-reviewer-agent.sh
  170	# superstar-shim-generated-at: 2026-05-21T14:23:07Z
  171	
  172	<inlined __superstar_check_version>
  173	
  174	__superstar_check_version "6.3.2" "reviewer-agent" "$HOME/Dev/sigreer/skills/superstar" "skills/project-setup/install-reviewer-agent.sh"
  175	
  176	exec bash "$HOME/Dev/sigreer/skills/superstar/skills/project-setup/scripts/reviewer-agent" "$@"
  177	```
  178	
  179	- **Self-test:** `bash -n "$TARGET"` (syntax check) plus confirming the source script resolves and is executable. No live reviewer invocation. `reviewer-agent` has no `--help` mode and its body bails on missing env vars, so `--help` is not a viable self-test for this installer; `bash -n` is the correct tool here even where `external-reviewer`'s installer uses `--help`.
  180	
  181	Existing copy-based installs at `~/.local/bin/reviewer-agent` are not version-stamped; the next `deploy.sh` (which re-runs all installers with `--force`) replaces them in place. The old copy disappears.
  182	
  183	### 6. `tasktool` ↔ pre-commit hook handshake
  184	
  185	Hook template `tools/tasktool/templates/pre-commit-tasktool` gains a stamped header block at install time. `tools/tasktool/install.sh --hook` interpolates the values, the same shape as a shim header but using `superstar-hook-*` keys to make the failure message obvious:
  186	
  187	```bash
  188	#!/usr/bin/env bash
  189	# superstar-hook
  190	# superstar-hook-name: tasktool-pre-commit
  191	# superstar-hook-version: 6.3.2
  192	# superstar-hook-source-root: $HOME/Dev/sigreer/skills/superstar
  193	# superstar-hook-installer: tools/tasktool/install.sh --hook
  194	# superstar-hook-generated-at: 2026-05-21T14:23:07Z
  195	```
  196	
  197	The Python `tasktool` entrypoint adds a startup check:
  198	
  199	1. `git rev-parse --show-toplevel` — if not in a git repo, skip silently.
  200	2. `<repo>/.git/hooks/pre-commit` exists? If not, skip silently.

[truncated: 215 additional lines]
### docs/tasklist.json

    1	{
    2	  "archived_cross_cutting": [
    3	    {
    4	      "archived_date": "2026-05-21",
    5	      "archived_path": "docs/archived-tasks/X15-archive-closed-cross-cutting-items.md",
    6	      "id": "X15",
    7	      "title": "Archive closed cross-cutting items"
    8	    }
    9	  ],
   10	  "archived_phases": [
   11	    {
   12	      "archived_date": "2026-05-18",
   13	      "archived_path": "docs/archived-tasks/P2-tasktool-json-backed-task-management-cli.md",
   14	      "id": "P2",
   15	      "title": "tasktool: JSON-backed task management CLI"
   16	    },
   17	    {
   18	      "archived_date": "2026-05-19",
   19	      "archived_path": "docs/archived-tasks/P4-tasktool-coordination-and-lifecycle-auth.md",
   20	      "id": "P4",
   21	      "title": "Tasktool coordination and lifecycle authority"
   22	    },
   23	    {
   24	      "archived_date": "2026-05-19",
   25	      "archived_path": "docs/archived-tasks/P3-phase-planning-workflow.md",
   26	      "id": "P3",
   27	      "title": "Phase planning workflow"
   28	    },
   29	    {
   30	      "archived_date": "2026-05-20",
   31	      "archived_path": "docs/archived-tasks/P1-external-reviewer-work-historical.md",
   32	      "id": "P1",
   33	      "title": "External-reviewer work (historical)"
   34	    }
   35	  ],
   36	  "cross_cutting": [
   37	    {
   38	      "closed": "2026-05-18",
   39	      "created": "2026-05-18",
   40	      "id": "X1",
   41	      "notes": "Changed external-review default prompt transport from argv to stdin so the bundled Codex reviewer-agent receives prompts via codex exec '-' and avoids argv length failures.",
   42	      "refs": [],
   43	      "started": null,
   44	      "status": "done",
   45	      "title": "Default external-review prompt transport to stdin"
   46	    },
   47	    {
   48	      "closed": "2026-05-18",
   49	      "created": "2026-05-18",
   50	      "id": "X2",
   51	      "notes": "Added repo-local tools/tasktool/tasktool launcher, updated tasklist/project-setup docs to prefer it, and taught the pre-commit hook to use the repo-local launcher before falling back to a global tasktool shim.",
   52	      "refs": [],
   53	      "started": null,
   54	      "status": "done",
   55	      "title": "Add repo-local tasktool launcher"
   56	    },
   57	    {
   58	      "closed": "2026-05-19",
   59	      "created": "2026-05-19",
   60	      "id": "X3",
   61	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. External-review verdict parsing now accepts markdown-emphasized Overall Verdict headings such as **5. Overall Verdict** followed by ready/revise text.",
   62	      "refs": [
   63	        "skills/external-review/scripts/external-reviewer.py",
   64	        "skills/external-review/tests/test_heading_style_verdict.py"
   65	      ],
   66	      "started": null,
   67	      "status": "done",
   68	      "title": "Spot fix: parse bold external-review verdict headings"
   69	    },
   70	    {
   71	      "closed": "2026-05-19",
   72	      "created": "2026-05-19",
   73	      "id": "X4",
   74	      "notes": "User-requested blocking spot fix completed outside the normal workflow for speed. Legacy markdown import now accepts fully-qualified slice IDs and additional cross-cutting forms including tagged done items, blocked cross rows coerced to ready, and archived cross rows treated as done.",
   75	      "refs": [
   76	        "tools/tasktool/importer.py"
   77	      ],
   78	      "started": null,
   79	      "status": "done",
   80	      "title": "Spot fix: broaden legacy tasklist importer compatibility"
   81	    },
   82	    {
   83	      "closed": "2026-05-19",
   84	      "created": "2026-05-19",
   85	      "id": "X5",
   86	      "notes": "User-requested hook update completed outside the normal workflow for speed. Adds Stop/SubagentStop finished-agent notifications, milestone message derivation from final agent text/transcript payloads, Hypr TTS config reuse with OPENAI_API_KEY fallback, and non-TTS ding fallbacks.\nSuperseded by X8: final-text milestone parsing was removed; agent hooks now emit generic dings and semantic spoken notifications come from tasktool status changes.",
   87	      "refs": [
   88	        "hooks/agent-finished",
   89	        "hooks/hooks.json",
   90	        "hooks/hooks-cursor.json",
   91	        "tests/claude-code/test-agent-finished-hook.sh"
   92	      ],
   93	      "started": null,
   94	      "status": "done",
   95	      "title": "Add finished-agent notification hook"
   96	    },
   97	    {
   98	      "closed": "2026-05-19",
   99	      "created": "2026-05-19",
  100	      "id": "X6",
  101	      "notes": "Codex startup skips Stop/SubagentStop notification hooks when hooks.json uses async=true; fix should preserve finished-agent notification behavior while avoiding unsupported async hook registration in Codex.\nSet finished-agent Stop/SubagentStop hook registrations to async=false for Codex compatibility. The hook now backgrounds real notification playback internally so synchronous hook registration returns quickly while dry-run tests remain foreground and deterministic.",
  102	      "refs": [
  103	        "hooks/hooks.json",
  104	        "hooks/agent-finished",
  105	        "tests/claude-code/test-hook-config.sh",
  106	        "tests/claude-code/test-agent-finished-hook.sh"
  107	      ],
  108	      "started": null,
  109	      "status": "done",
  110	      "title": "Fix Codex finished-agent hook compatibility"
  111	    },
  112	    {
  113	      "closed": "2026-05-19",
  114	      "created": "2026-05-19",
  115	      "id": "X7",
  116	      "notes": "Codex reported superstar/6.0.0 because the installable local marketplace payload under plugins/superstar still declared version 6.0.0 and the version bump audit did not track that embedded manifest.\n\nBumped the embedded Codex plugin payload manifest to 6.0.1 and added it to the version bump check. Reinstalled superstar@superstar-dev, then rebuilt the 6.0.1 runtime cache as a materialized copy of this checkout with .agents excluded so Codex sees the full skills/hooks tree while codex plugin list still reports installed/enabled. Final probe shows cache version 6.0.1, skills/hooks present, and no async-hook warning.",
  117	      "refs": [
  118	        ".version-bump.json",
  119	        "plugins/superstar/.codex-plugin/plugin.json",
  120	        ".agents/plugins/marketplace.json",
  121	        "tests/codex-plugin-sync/test-version-drift.sh",
  122	        "tests/codex-plugin-sync/test-local-marketplace.sh"
  123	      ],
  124	      "started": null,
  125	      "status": "done",
  126	      "title": "Fix Superstar Codex plugin payload version drift"
  127	    },
  128	    {
  129	      "closed": "2026-05-19",
  130	      "created": "2026-05-19",
  131	      "id": "X8",
  132	      "notes": "Move semantic spoken notifications to tasktool status transitions for ready/in_progress/blocked/done. Keep agent Stop/SubagentStop hooks as generic completion dings only, with different sound styles for Claude and Codex.\nAgent Stop/SubagentStop hooks now emit generic harness-specific dings only. Semantic spoken notifications moved to tasktool status events for ready, in_progress, blocked, and done, including create, set, close, block, unblock, and archive-phase paths.",
  133	      "refs": [
  134	        "hooks/agent-finished",
  135	        "tools/tasktool/notify.py",
  136	        "tools/tasktool/commands.py",
  137	        "tools/tasktool/tests/test_notify.py",
  138	        "tools/tasktool/tests/test_commands.py",
  139	        "tools/tasktool/tests/conftest.py",
  140	        "tests/claude-code/test-agent-finished-hook.sh"
  141	      ],
  142	      "started": null,
  143	      "status": "done",
  144	      "title": "Move semantic notifications from agent hooks to tasktool status changes"
  145	    },
  146	    {
  147	      "closed": "2026-05-19",
  148	      "created": "2026-05-19",
  149	      "id": "X9",
  150	      "notes": "Rapid tasktool status changes currently spawn independent notifier processes, causing overlapping TTS/audio. Add a single-audio queue with at most three queued tasktool events; overflow should collapse to a single 'multiple other events' summary and drop further items.\nAdded a file-backed notification queue shared by agent dings and tasktool TTS. Only one worker drains audio at a time. Queue capacity is three pending events; overflow keeps the first two pending items and replaces the rest with a single 'Multiple other events' summary, dropping further burst items while the summary remains queued.",
  151	      "refs": [
  152	        "tools/tasktool/notify.py",
  153	        "tools/tasktool/tests/test_notify.py"
  154	      ],
  155	      "started": null,
  156	      "status": "done",
  157	      "title": "Coalesce bursty tasktool audio notifications"
  158	    },
  159	    {
  160	      "closed": "2026-05-20",
  161	      "created": "2026-05-20",
  162	      "id": "X10",
  163	      "notes": "",
  164	      "refs": [
  165	        "docs/specs/2026-05-20-X10-verdict-parser-claude-formatting-design.md",
  166	        "docs/reviewer/x10-verdict-parser-claude-formatting-design-spec",
  167	        "docs/plans/2026-05-20-X10-verdict-parser-claude-formatting.md"
  168	      ],
  169	      "started": null,
  170	      "status": "done",
  171	      "title": "Harden external-review verdict parser and prompt against Claude formatting variants"
  172	    },
  173	    {
  174	      "closed": "2026-05-20",
  175	      "created": "2026-05-20",
  176	      "id": "X11",
  177	      "notes": "",
  178	      "refs": [
  179	        "docs/specs/2026-05-20-X11-global-external-reviewer-bridge-design.md",
  180	        "docs/reviewer/x11-global-external-reviewer-bridge-design-spec",
  181	        "docs/plans/2026-05-20-X11-global-external-reviewer-bridge.md",
  182	        "docs/reviewer/x11-global-external-reviewer-bridge-plan",
  183	        "docs/handoffs/2026-05-20-X11-global-external-reviewer-bridge-prompt.md"
  184	      ],
  185	      "started": "2026-05-20",
  186	      "status": "done",
  187	      "title": "Make external-review bridge global"
  188	    },
  189	    {
  190	      "closed": "2026-05-20",
  191	      "created": "2026-05-20",
  192	      "id": "X12",
  193	      "notes": "",
  194	      "refs": [
  195	        "docs/specs/2026-05-20-X12-tasktool-require-authoritative-routing-design.md",
  196	        "docs/plans/2026-05-20-X12-tasktool-require-authoritative-routing.md"
  197	      ],
  198	      "started": "2026-05-20",
  199	      "status": "done",
  200	      "title": "tasktool: require authoritative-checkout routing for mutations"

[truncated: 61 additional lines]

<!-- superstar-prompt:end -->