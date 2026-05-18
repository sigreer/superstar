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
post-slice

Review mode:
Post-slice review. Treat this as a completion gate for one
slice of work. Compare the completed changes and stated evidence against the
slice acceptance criteria. Prioritize: incomplete tasks, uncommitted or
untracked artifacts, missing tests, failing or skipped verification, broken
cross-site behavior, and claims not supported by the repo state.

Target document:
docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md

Additional context files:
- docs/specs/2026-05-17-P2-tasktool-design.md
- docs/tasklist.json

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

### docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md

    1	# P2.S3 — Skill rewrite & pre-commit hook Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Replace the markdown-era `tasklist-discipline` skill with a tasktool-centric version, install a per-project pre-commit hook that enforces canonical JSON / blocks orphans / blocks `TASKLIST.md` regressions, and update every sibling skill that still references `docs/TASKLIST.md`.
    6	
    7	**Architecture:** Tasktool already owns the data and the review gates (P2.S1, P2.S2). This slice moves the *prose* layer onto the same axis: the `tasklist-discipline` skill becomes a thin pointer to `tasktool` and the gating concepts; the pre-commit hook closes the in-session edit loophole (§8.1, §12 of the spec) by refusing non-canonical bytes, orphaned spec/plan filenames, and any commit that touches `docs/TASKLIST.md`. Sibling skills get surgical edits — every `docs/TASKLIST.md` reference becomes a `tasktool` invocation or a `docs/tasklist.json` reference.
    8	
    9	**Tech Stack:** Python 3 stdlib (`tasktool`), POSIX sh (pre-commit hook), markdown (skills).
   10	
   11	**TASKLIST entry:** `P2.S3` in `docs/tasklist.json` (created 2026-05-18, status `ready`).
   12	
   13	---
   14	
   15	## File map
   16	
   17	| Action | Path | Responsibility |
   18	|--------|------|----------------|
   19	| Modify | `tools/tasktool/validate.py` | Add `validate_no_orphans(repo_root, staged_specs, staged_plans)` — flags any spec/plan filename ID that has no matching TASKLIST row. |
   20	| Modify | `tools/tasktool/cli.py` | Add `validate --check-orphans <path>...` flag plumbing. |
   21	| Modify | `tools/tasktool/commands.py` | Wire `cmd_validate(check_orphans=…)` to call the new validator and merge findings into the existing text/json output. |
   22	| Create | `tools/tasktool/tests/test_validate_orphans.py` | Unit + CLI tests for the new orphan-scan flag. |
   23	| Create | `tools/tasktool/templates/pre-commit-tasktool` | POSIX sh hook template (per spec §8.1) — strict-format + full validate + orphan scan + TASKLIST.md block. |
   24	| Modify | `tools/tasktool/install.sh` | Add `install.sh --hook` mode that drops `.git/hooks/pre-commit` from the template, idempotent + `--force`. |
   25	| Create | `tools/tasktool/tests/test_pre_commit_hook.py` | Synthetic-repo hook tests: canonical commit passes; non-canonical bytes blocked; orphan staged spec blocked; staged `TASKLIST.md` blocked; `TASKTOOL_RAW=1` editor + `validate --normalise` round-trip passes. |
   26	| Rewrite | `skills/tasklist-discipline/SKILL.md` | Full rewrite around tasktool (per spec §9.1). |
   27	| Delete | `skills/tasklist-discipline/templates/TASKLIST.template.md` | Replaced by `tasktool init`. |
   28	| Modify | `skills/writing-plans/SKILL.md` | `docs/TASKLIST.md` → `docs/tasklist.json`; ID-existence check uses `tasktool show <id>`. |
   29	| Modify | `skills/writing-plans/handoff-prompt.template.md` | Replace TASKLIST.md link/instructions with `tasktool brief <id>` + `docs/tasklist.json`. |
   30	| Modify | `skills/brainstorming/SKILL.md` | Same swap; "create the row first" routes through `tasktool create`. |
   31	| Modify | `skills/external-review/SKILL.md` | Context column says `docs/tasklist.json` (or `tasktool render` output). |
   32	| Modify | `skills/subagent-driven-development/SKILL.md` | Slice/phase close steps call `tasktool close <id>` and `tasktool archive-phase <id>`; remove "flip in TASKLIST.md" prose. |
   33	| Modify | `skills/executing-plans/SKILL.md` | Same swap. |
   34	| Modify | `skills/project-setup/SKILL.md` | Audit table row 1 becomes `docs/tasklist.json` via `tasktool init`; row references the hook template; remove TASKLIST.md template reference. |
   35	| Modify | `skills/using-superstar/SKILL.md` | Cosmetic — none of the user-facing prose references `TASKLIST.md`; verify and no-op if clean. |
   36	
   37	---
   38	
   39	## Task 1: Orphan-aware validator
   40	
   41	**Files:**
   42	- Modify: `tools/tasktool/validate.py`
   43	- Modify: `tools/tasktool/cli.py:103-105`
   44	- Modify: `tools/tasktool/commands.py` (`cmd_validate`)
   45	- Test: `tools/tasktool/tests/test_validate_orphans.py`
   46	
   47	- [ ] **Step 1: Write the failing test**
   48	
   49	```python
   50	# tools/tasktool/tests/test_validate_orphans.py
   51	import json, subprocess, sys
   52	from pathlib import Path
   53	
   54	TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
   55	
   56	def _run(root, *args):
   57	    return subprocess.run(
   58	        [sys.executable, str(TOOL), "--project-root", str(root), *args],
   59	        capture_output=True, text=True,
   60	    )
   61	
   62	def _seed(tmp_path):
   63	    (tmp_path / "docs").mkdir()
   64	    (tmp_path / "docs" / "specs").mkdir()
   65	    (tmp_path / "docs" / "plans").mkdir()
   66	    _run(tmp_path, "init", "--project", "demo")
   67	    pid = _run(tmp_path, "create", "phase", "--title", "Phase one").stdout.strip()
   68	    sid = _run(tmp_path, "create", "slice", pid, "--title", "Slice one").stdout.strip()
   69	    return pid, sid
   70	
   71	def test_orphan_spec_filename_is_flagged(tmp_path):
   72	    pid, sid = _seed(tmp_path)
   73	    orphan = tmp_path / "docs" / "specs" / "2026-05-18-P99-orphan-design.md"
   74	    orphan.write_text("# orphan\n")
   75	    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(orphan))
   76	    assert r.returncode == 1, r.stdout + r.stderr
   77	    payload = json.loads(r.stdout)
   78	    assert any("P99" in e for e in payload["errors"])
   79	
   80	def test_known_id_filename_passes(tmp_path):
   81	    pid, sid = _seed(tmp_path)
   82	    known = tmp_path / "docs" / "plans" / f"2026-05-18-{pid.lower()}-{sid.lower()}-thing.md"
   83	    known.write_text("# plan\n")
   84	    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(known))
   85	    assert r.returncode == 0, r.stdout + r.stderr
   86	```
   87	
   88	- [ ] **Step 2: Run test to verify it fails**
   89	
   90	Run: `python -m pytest tools/tasktool/tests/test_validate_orphans.py -v`
   91	Expected: FAIL — `--check-orphans` is not a known flag (argparse error / exit 2).
   92	
   93	- [ ] **Step 3: Add the validator function**
   94	
   95	The existing project filename convention is **dash-separated** (`2026-05-18-p2-s3-…`), not dot-separated. The regex and lookup must reflect that. In `tools/tasktool/validate.py`, add:
   96	
   97	```python
   98	import re
   99	from pathlib import Path
  100	
  101	# Matches dash-separated IDs at the start of plan/spec filenames. Two forms:
  102	#   Phase-rooted:    2026-05-18-p2-… | p2-s3-… | p2-s3a-… | p2-s3-t1-…
  103	#   Cross-cutting:   2026-05-18-x4-…
  104	# Note: cross-cutting IDs are top-level in the data model (e.g. `X4`, not `P2.X4`).
  105	# A filename of the form `p2-x4-…` is treated as "phase P2, slice/cross child X4 *under*
  106	# P2" only if such a row exists; otherwise it's flagged. In practice cross filenames
  107	# should use the top-level form.
  108	_FILENAME_ID_RE = re.compile(
  109	    r"^\d{4}-\d{2}-\d{2}-"
  110	    r"(?:(?P<cross>[Xx]\d+)"
  111	    r"|(?P<phase>[Pp]\d+)"
  112	      r"(?:-(?P<child>[SsXx]\d+[a-z]?))?"
  113	      r"(?:-(?P<task>[Tt]\d+))?"
  114	    r")-",
  115	)
  116	
  117	def _normalise_id(*, cross: str | None, phase: str | None,
  118	                  child: str | None, task: str | None) -> str:
  119	    if cross:
  120	        return cross.upper()
  121	    assert phase is not None
  122	    parts = [phase.upper()]
  123	    if child:
  124	        parts.append(child.upper())
  125	    if task:
  126	        parts.append(task.upper())
  127	    return ".".join(parts)
  128	
  129	def collect_known_ids(p) -> set[str]:
  130	    """Return the set of *fully-qualified* IDs that exist in this project.
  131	
  132	    Short forms are deliberately NOT included — orphan checking requires exact
  133	    fully-qualified matches (e.g. `P99.S1` must not pass merely because some
  134	    other phase has an `S1`).
  135	    """
  136	    ids: set[str] = set()
  137	    for ph in p.phases:
  138	        ids.add(ph.id)
  139	        for sl in ph.slices:
  140	            ids.add(f"{ph.id}.{sl.id}")
  141	            for t in sl.tasks:
  142	                ids.add(f"{ph.id}.{sl.id}.{t.id}")
  143	    for ph in getattr(p, "archived_phases", []) or []:
  144	        ids.add(ph.id if hasattr(ph, "id") else ph["id"])
  145	    for x in p.cross_cutting:
  146	        ids.add(x.id)  # Cross-cutting IDs are top-level (e.g. "X4").
  147	    return ids
  148	
  149	def validate_orphan_filenames(p, paths) -> list[str]:
  150	    known = collect_known_ids(p)
  151	    findings: list[str] = []
  152	    for path in paths:
  153	        name = Path(path).name
  154	        m = _FILENAME_ID_RE.match(name)
  155	        if not m:
  156	            continue
  157	        fq = _normalise_id(
  158	            cross=m.group("cross"),
  159	            phase=m.group("phase"),
  160	            child=m.group("child"),
  161	            task=m.group("task"),
  162	        )
  163	        if fq in known:
  164	            continue
  165	        findings.append(
  166	            f"{path}: filename references ID {fq} but no matching row in tasklist.json"
  167	        )
  168	    return findings
  169	```
  170	
  171	Extend the orphans test from Step 1 with a wrong-phase regression case:
  172	
  173	```python
  174	def test_cross_cutting_top_level_filename_passes(tmp_path):
  175	    """`2026-05-18-x4-…` resolves to top-level X4 and passes when X4 exists."""
  176	    _seed(tmp_path)
  177	    cid = _run(tmp_path, "create", "cross", "--title", "C4").stdout.strip()  # X1 → X4 depending on seed
  178	    f = tmp_path / "docs" / "specs" / f"2026-05-18-{cid.lower()}-design.md"
  179	    f.write_text("# cross spec\n")
  180	    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(f))
  181	    assert r.returncode == 0, r.stdout + r.stderr
  182	
  183	def test_cross_cutting_unknown_top_level_is_flagged(tmp_path):
  184	    _seed(tmp_path)
  185	    f = tmp_path / "docs" / "specs" / "2026-05-18-x99-design.md"
  186	    f.write_text("# nope\n")
  187	    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(f))
  188	    assert r.returncode == 1, r.stdout + r.stderr
  189	    payload = json.loads(r.stdout)
  190	    assert any("X99" in e for e in payload["errors"])
  191	
  192	def test_wrong_phase_qualified_id_is_flagged(tmp_path):
  193	    """`P99-S1-…` must NOT pass merely because some other phase has an `S1`."""
  194	    _seed(tmp_path)  # creates P1.S1
  195	    orphan = tmp_path / "docs" / "plans" / "2026-05-18-p99-s1-thing.md"
  196	    orphan.write_text("# wrong-phase\n")
  197	    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(orphan))
  198	    assert r.returncode == 1, r.stdout + r.stderr
  199	    payload = json.loads(r.stdout)
  200	    assert any("P99.S1" in e for e in payload["errors"])
  201	```
  202	
  203	- [ ] **Step 4: Plumb the CLI flag**
  204	
  205	The existing `cmd_validate` contract is `(format=…, strict_format=…, normalise=…) -> tuple[int, str]` and the CLI writes the returned text — preserve it. The current JSON shape is `{"ok", "errors", "warnings"}` — extend it by appending orphan findings to `errors`.
  206	
  207	In `tools/tasktool/cli.py` (where `p_validate` is built):
  208	
  209	```python
  210	p_validate = sub.add_parser("validate")
  211	p_validate.add_argument("--format", choices=["text", "json"], default="text")
  212	p_validate.add_argument("--strict-format", action="store_true")
  213	p_validate.add_argument("--normalise", action="store_true")
  214	p_validate.add_argument("--check-orphans", nargs="*", default=None,
  215	                        help="Spec/plan filepaths to check against tasklist.json IDs.")
  216	```
  217	
  218	In the `args.cmd == "validate"` branch, preserve the existing `(rc, text)` write-through:
  219	
  220	```python
  221	elif args.cmd == "validate":
  222	    rc, text = commands.cmd_validate(
  223	        repo_root=root, format=args.format,
  224	        strict_format=args.strict_format, normalise=args.normalise,
  225	        check_orphans=args.check_orphans,
  226	    )
  227	    sys.stdout.write(text)
  228	    return rc
  229	```
  230	
  231	In `tools/tasktool/commands.py`, extend the existing `cmd_validate` (keep the `format=` kwarg name; return `(rc, text)`). After loading `project`, if `check_orphans` is provided run `validate_orphan_filenames(project, check_orphans)` and append each finding to the `errors` list (so the JSON shape stays `{"ok", "errors", "warnings"}` and the text mode prints them through the same loop). Tests assert against `payload["errors"]`, not `findings` — match the existing schema.
  232	
  233	- [ ] **Step 5: Run test to verify it passes**
  234	
  235	Run: `python -m pytest tools/tasktool/tests/test_validate_orphans.py -v`
  236	Expected: PASS (both tests).
  237	
  238	- [ ] **Step 6: Re-run the full tasktool suite**
  239	
  240	Run: `python -m pytest tools/tasktool/tests -q`
  241	Expected: PASS (no regressions).
  242	
  243	- [ ] **Step 7: Commit**
  244	
  245	```bash
  246	git add tools/tasktool/validate.py tools/tasktool/cli.py tools/tasktool/commands.py tools/tasktool/tests/test_validate_orphans.py
  247	git commit -m "P2.S3.T1: tasktool validate --check-orphans"
  248	```
  249	
  250	---
  251	
  252	## Task 2: Pre-commit hook template
  253	
  254	**Files:**
  255	- Create: `tools/tasktool/templates/pre-commit-tasktool`
  256	- Test: covered by Task 3.
  257	
  258	The hook MUST validate **staged** content (the index), not the working tree — a clean worktree with stale staged bytes would otherwise sneak past `tasktool validate`. The strategy: materialise the staged blob into a temporary project root via `git checkout-index --prefix=`, then run `tasktool --project-root <tempdir>` against that copy. Orphan filename checks use `git diff --cached --name-only --diff-filter=ACMR` directly (filename-only, not content).
  259	
  260	- [ ] **Step 1: Write the hook**
  261	
  262	Write `tools/tasktool/templates/pre-commit-tasktool` (mode 0755):
  263	
  264	```sh
  265	#!/usr/bin/env sh
  266	# tasktool-pre-commit-hook v1
  267	# Installed by `tools/tasktool/install.sh --hook`.
  268	# Validates the STAGED content (the index), not the working tree, so a clean
  269	# worktree with stale staged bytes cannot sneak past.
  270	#
  271	# Enforces:
  272	#   1. docs/TASKLIST.md must not be staged (project migrated to docs/tasklist.json).
  273	#   2. Staged docs/tasklist.json must be canonical (tasktool validate --strict-format).
  274	#   3. Staged docs/tasklist.json must pass full validation.
  275	#   4. Staged spec/plan filenames must reference an ID present in the staged tasklist.json.
  276	# Bypass for genuine emergencies: `git commit --no-verify` and document the reason.
  277	set -e
  278	
  279	STAGED="$(git diff --cached --name-only --diff-filter=ACMR)"
  280	
  281	# 1. Block docs/TASKLIST.md
  282	if printf '%s\n' "$STAGED" | grep -qx 'docs/TASKLIST.md'; then
  283	  echo "pre-commit: docs/TASKLIST.md is staged but this project migrated to docs/tasklist.json." >&2
  284	  echo "  Delete docs/TASKLIST.md or unstage it. Use tasktool to mutate docs/tasklist.json." >&2
  285	  exit 1
  286	fi
  287	
  288	# 1b. Block staged deletion of docs/tasklist.json — a tasktool-managed repo
  289	# must keep its canonical tracker.
  290	if git diff --cached --name-only --diff-filter=D | grep -qx 'docs/tasklist.json'; then
  291	  echo "pre-commit: docs/tasklist.json is staged for deletion. A tasktool-managed repo must keep its canonical tracker." >&2
  292	  echo "  Unstage the deletion (\`git restore --staged docs/tasklist.json\`) or use --no-verify with a written justification." >&2
  293	  exit 1
  294	fi
  295	
  296	# Determine whether docs/tasklist.json exists in the index.
  297	if git ls-files --cached --error-unmatch docs/tasklist.json >/dev/null 2>&1; then
  298	  HAS_INDEX_TASKLIST=1
  299	else
  300	  HAS_INDEX_TASKLIST=0
  301	fi
  302	
  303	if [ "$HAS_INDEX_TASKLIST" -eq 1 ]; then
  304	  # Materialise the staged blob into a temp project root.
  305	  TMP="$(mktemp -d 2>/dev/null || mktemp -d -t tasktool-precommit)"
  306	  trap 'rm -rf "$TMP"' EXIT
  307	  mkdir -p "$TMP/docs"
  308	  git show :docs/tasklist.json > "$TMP/docs/tasklist.json"
  309	
  310	  # 2 + 3. Validate the staged content. Strict-format only when tasklist.json
  311	  # is itself in the staged change set (the file is canonical at rest anyway,
  312	  # but we surface the canonical-format failure with the right message).
  313	  if printf '%s\n' "$STAGED" | grep -qx 'docs/tasklist.json'; then
  314	    tasktool --project-root "$TMP" validate --strict-format --format text
  315	  fi
  316	  tasktool --project-root "$TMP" validate --format text
  317	
  318	  # 4. Orphan scan over staged spec/plan filenames (filename-only, evaluated
  319	  # against the staged tasklist.json). Materialise staged specs/plans into
  320	  # $TMP so paths exist relative to --project-root.
  321	  ORPHAN_CANDIDATES="$(printf '%s\n' "$STAGED" | grep -E '^docs/(specs|plans)/[0-9]{4}-[0-9]{2}-[0-9]{2}-' || true)"
  322	  if [ -n "$ORPHAN_CANDIDATES" ]; then
  323	    for f in $ORPHAN_CANDIDATES; do
  324	      mkdir -p "$TMP/$(dirname "$f")"
  325	      git show ":$f" > "$TMP/$f" 2>/dev/null || true
  326	    done
  327	    # shellcheck disable=SC2086
  328	    (cd "$TMP" && tasktool validate --check-orphans $ORPHAN_CANDIDATES --format text)
  329	  fi
  330	fi
  331	```
  332	
  333	- [ ] **Step 2: Commit the template**
  334	
  335	```bash
  336	chmod +x tools/tasktool/templates/pre-commit-tasktool
  337	git add tools/tasktool/templates/pre-commit-tasktool
  338	git commit -m "P2.S3.T2: pre-commit hook template (index-aware)"
  339	```
  340	
  341	---
  342	
  343	## Task 3: Hook installer + tests
  344	
  345	**Files:**
  346	- Modify: `tools/tasktool/install.sh`
  347	- Test: `tools/tasktool/tests/test_pre_commit_hook.py`
  348	
  349	- [ ] **Step 1: Add `--hook` mode to install.sh**
  350	
  351	The existing `tools/tasktool/install.sh` is Bash (`#!/usr/bin/env bash`, `set -euo pipefail`, `${BASH_SOURCE[0]}`, `[[ … ]]`). The new `--hook` branch must run **before** the shim-install logic (which treats `$1` as a `--force` toggle), and must use Bash. All invocations from tests, docs, and the smoke task use `bash`, not `sh`.
  352	
  353	In `tools/tasktool/install.sh`, insert the `--hook` dispatch immediately after the `set -euo pipefail` line and before `SCRIPT_DIR=`:
  354	
  355	```bash
  356	# --- hook installer (must precede shim-install logic) ---------------------
  357	if [[ "${1:-}" == "--hook" ]]; then
  358	  shift
  359	  FORCE_HOOK=0
  360	  if [[ "${1:-}" == "--force" ]]; then FORCE_HOOK=1; shift; fi
  361	  REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  362	  if [[ -z "$REPO_ROOT" ]]; then
  363	    echo "install.sh --hook: must be run inside a git working tree" >&2
  364	    exit 1
  365	  fi
  366	  HOOK_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/templates/pre-commit-tasktool"
  367	  HOOK_DEST="$REPO_ROOT/.git/hooks/pre-commit"
  368	  if [[ -f "$HOOK_DEST" && "$FORCE_HOOK" -ne 1 ]]; then
  369	    if ! grep -q 'tasktool-pre-commit-hook' "$HOOK_DEST" 2>/dev/null; then
  370	      echo "install.sh --hook: $HOOK_DEST exists and is not a tasktool hook. Re-run with --force to overwrite." >&2
  371	      exit 1
  372	    fi
  373	  fi
  374	  install -m 0755 "$HOOK_SRC" "$HOOK_DEST"
  375	  echo "Installed $HOOK_DEST"
  376	  exit 0
  377	fi
  378	# --------------------------------------------------------------------------
  379	```
  380	
  381	- [ ] **Step 2: Write the failing test**
  382	
  383	```python
  384	# tools/tasktool/tests/test_pre_commit_hook.py
  385	import os, subprocess, sys, shutil, textwrap
  386	from pathlib import Path
  387	
  388	REPO = Path(__file__).resolve().parents[3]
  389	TOOL = REPO / "tools" / "tasktool" / "__main__.py"
  390	INSTALL = REPO / "tools" / "tasktool" / "install.sh"
  391	
  392	def _git(repo, *args, check=True, env=None):
  393	    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=check, env=env)
  394	
  395	def _tasktool(repo, *args, env=None):
  396	    return subprocess.run([sys.executable, str(TOOL), "--project-root", str(repo), *args],
  397	                          capture_output=True, text=True, env=env)
  398	
  399	def _seed_repo(tmp_path):
  400	    repo = tmp_path / "r"
  401	    repo.mkdir()
  402	    _git(repo, "init", "-q", "-b", "main")
  403	    _git(repo, "config", "user.email", "t@example.com")
  404	    _git(repo, "config", "user.name", "t")
  405	    (repo / "docs").mkdir()
  406	    (repo / "docs" / "specs").mkdir()
  407	    (repo / "docs" / "plans").mkdir()
  408	    _tasktool(repo, "init", "--project", "demo")
  409	    # Make `tasktool` callable from the hook's PATH:
  410	    bin_dir = tmp_path / "bin"
  411	    bin_dir.mkdir()
  412	    (bin_dir / "tasktool").write_text(f"#!/usr/bin/env sh\nexec {sys.executable} {TOOL} \"$@\"\n")
  413	    os.chmod(bin_dir / "tasktool", 0o755)
  414	    env = os.environ.copy()
  415	    env["PATH"] = f"{bin_dir}:{env['PATH']}"
  416	    # Install the hook (install.sh is bash):
  417	    subprocess.run(["bash", str(INSTALL), "--hook"], cwd=repo, check=True, env=env)
  418	    return repo, env
  419	
  420	def test_canonical_commit_passes(tmp_path):
  421	    repo, env = _seed_repo(tmp_path)
  422	    _git(repo, "add", "docs/tasklist.json", env=env)
  423	    r = _git(repo, "commit", "-m", "init", check=False, env=env)
  424	    assert r.returncode == 0, r.stdout + r.stderr
  425	
  426	def test_non_canonical_bytes_rejected(tmp_path):
  427	    repo, env = _seed_repo(tmp_path)
  428	    _git(repo, "add", "docs/tasklist.json", env=env)
  429	    _git(repo, "commit", "-m", "init", env=env)
  430	    # Append a stray newline → non-canonical.
  431	    with open(repo / "docs" / "tasklist.json", "a") as f:
  432	        f.write("\n")
  433	    _git(repo, "add", "docs/tasklist.json", env=env)
  434	    r = _git(repo, "commit", "-m", "tamper", check=False, env=env)
  435	    assert r.returncode != 0
  436	    assert "canonical" in (r.stdout + r.stderr).lower()
  437	
  438	def test_orphan_spec_filename_rejected(tmp_path):
  439	    repo, env = _seed_repo(tmp_path)
  440	    _git(repo, "add", "docs/tasklist.json", env=env)
  441	    _git(repo, "commit", "-m", "init", env=env)
  442	    orphan = repo / "docs" / "specs" / "2026-05-18-P99-orphan-design.md"
  443	    orphan.write_text("# orphan\n")
  444	    _git(repo, "add", str(orphan.relative_to(repo)), env=env)
  445	    r = _git(repo, "commit", "-m", "orphan", check=False, env=env)
  446	    assert r.returncode != 0
  447	    assert "P99" in (r.stdout + r.stderr)
  448	
  449	def test_tasklist_md_rejected(tmp_path):
  450	    repo, env = _seed_repo(tmp_path)
  451	    _git(repo, "add", "docs/tasklist.json", env=env)
  452	    _git(repo, "commit", "-m", "init", env=env)
  453	    legacy = repo / "docs" / "TASKLIST.md"
  454	    legacy.write_text("# legacy\n")
  455	    _git(repo, "add", "docs/TASKLIST.md", env=env)
  456	    r = _git(repo, "commit", "-m", "legacy", check=False, env=env)
  457	    assert r.returncode != 0
  458	    assert "TASKLIST.md" in (r.stdout + r.stderr)
  459	
  460	def test_raw_edit_then_normalise_passes(tmp_path):
  461	    repo, env = _seed_repo(tmp_path)
  462	    _git(repo, "add", "docs/tasklist.json", env=env)
  463	    _git(repo, "commit", "-m", "init", env=env)
  464	    p = repo / "docs" / "tasklist.json"
  465	    with open(p, "a") as f:
  466	        f.write("\n")
  467	    _tasktool(repo, "validate", "--normalise", env=env)
  468	    _git(repo, "add", "docs/tasklist.json", env=env)
  469	    r = _git(repo, "commit", "-m", "normalised", check=False, env=env)
  470	    assert r.returncode == 0, r.stdout + r.stderr
  471	
  472	def test_staged_bad_normalised_worktree_is_rejected(tmp_path):
  473	    """Stage non-canonical bytes, then normalise the worktree without re-staging.
  474	    The hook MUST reject because the index is what gets committed."""
  475	    repo, env = _seed_repo(tmp_path)
  476	    _git(repo, "add", "docs/tasklist.json", env=env)
  477	    _git(repo, "commit", "-m", "init", env=env)
  478	    p = repo / "docs" / "tasklist.json"
  479	    with open(p, "a") as f:
  480	        f.write("\n")
  481	    # Stage the bad bytes.
  482	    _git(repo, "add", "docs/tasklist.json", env=env)
  483	    # Now normalise the WORKTREE only (do not re-add).
  484	    _tasktool(repo, "validate", "--normalise", env=env)
  485	    r = _git(repo, "commit", "-m", "staged-bad-worktree-clean", check=False, env=env)
  486	    assert r.returncode != 0, (
  487	        "hook must validate the index, not the worktree, but commit succeeded: "
  488	        + r.stdout + r.stderr
  489	    )
  490	
  491	def test_tasklist_json_deletion_rejected(tmp_path):
  492	    """Staging the deletion of docs/tasklist.json must be refused."""
  493	    repo, env = _seed_repo(tmp_path)
  494	    _git(repo, "add", "docs/tasklist.json", env=env)
  495	    _git(repo, "commit", "-m", "init", env=env)
  496	    _git(repo, "rm", "docs/tasklist.json", env=env)
  497	    r = _git(repo, "commit", "-m", "delete tracker", check=False, env=env)
  498	    assert r.returncode != 0, "hook must refuse tasklist.json deletion: " + r.stdout + r.stderr
  499	    assert "deletion" in (r.stdout + r.stderr).lower() or "delete" in (r.stdout + r.stderr).lower()
  500	
  501	def test_hook_install_is_idempotent(tmp_path):
  502	    """Running `install.sh --hook` twice without --force must succeed both times."""
  503	    repo, env = _seed_repo(tmp_path)
  504	    # First install happened in _seed_repo. Run again:
  505	    r = subprocess.run(["bash", str(INSTALL), "--hook"], cwd=repo, capture_output=True, text=True, env=env)
  506	    assert r.returncode == 0, r.stdout + r.stderr
  507	
  508	def test_staged_good_dirty_worktree_passes(tmp_path):
  509	    """Stage canonical bytes, then dirty the worktree without re-staging.
  510	    The hook MUST pass — the index is canonical, the worktree dirt is irrelevant."""
  511	    repo, env = _seed_repo(tmp_path)
  512	    _git(repo, "add", "docs/tasklist.json", env=env)
  513	    _git(repo, "commit", "-m", "init", env=env)
  514	    # Stage a clean tasktool-mediated change.
  515	    _tasktool(repo, "create", "phase", "--title", "P", env=env)
  516	    _git(repo, "add", "docs/tasklist.json", env=env)
  517	    # Now dirty the worktree post-stage.
  518	    p = repo / "docs" / "tasklist.json"
  519	    with open(p, "a") as f:
  520	        f.write("\n")
  521	    r = _git(repo, "commit", "-m", "staged-good-dirty-worktree", check=False, env=env)
  522	    assert r.returncode == 0, (
  523	        "hook must accept canonical index regardless of worktree dirt: "
  524	        + r.stdout + r.stderr
  525	    )
  526	```
  527	
  528	- [ ] **Step 3: Run test to verify it fails**
  529	
  530	Run: `python -m pytest tools/tasktool/tests/test_pre_commit_hook.py -v`
  531	Expected: FAIL — `install.sh --hook` does not yet branch correctly, or hook prerequisites missing.
  532	
  533	- [ ] **Step 4: Iterate on install.sh + hook until tests pass**
  534	
  535	Run the test, read the failure, fix the hook or installer, repeat. Do not adjust the *tests* to match — adjust the implementation.
  536	
  537	- [ ] **Step 5: Run the full suite**
  538	
  539	Run: `python -m pytest tools/tasktool/tests -q`
  540	Expected: PASS (all hook tests + all earlier tests).
  541	
  542	- [ ] **Step 6: Commit**
  543	
  544	```bash
  545	git add tools/tasktool/install.sh tools/tasktool/tests/test_pre_commit_hook.py
  546	git commit -m "P2.S3.T3: install.sh --hook + pre-commit hook tests"
  547	```
  548	
  549	---
  550	
  551	## Task 4: Install the hook in this repo
  552	
  553	**Files:**
  554	- Create: `.git/hooks/pre-commit` (out-of-tree; not committed).
  555	
  556	- [ ] **Step 1: Run the installer**
  557	
  558	```bash
  559	bash tools/tasktool/install.sh --hook
  560	```
  561	
  562	Expected stdout: `Installed /home/simon/Dev/sigreer/skills/superstar/.git/hooks/pre-commit`
  563	
  564	- [ ] **Step 2: Smoke test the hook on the live repo**
  565	
  566	```bash
  567	echo "" >> docs/tasklist.json
  568	git add docs/tasklist.json
  569	git commit -m "should fail" || echo "rejected as expected"
  570	git restore --staged docs/tasklist.json
  571	git checkout -- docs/tasklist.json
  572	```
  573	
  574	Expected: commit refused with a canonical-format error; restore returns the file to clean state.
  575	
  576	- [ ] **Step 3: No commit for this task** — the hook installation is operator-side state, not tree state.
  577	
  578	---
  579	
  580	## Task 5: Rewrite `tasklist-discipline` SKILL.md
  581	
  582	**Files:**
  583	- Rewrite: `skills/tasklist-discipline/SKILL.md`
  584	- Delete: `skills/tasklist-discipline/templates/TASKLIST.template.md`
  585	
  586	- [ ] **Step 1: Replace the skill body**
  587	
  588	Overwrite `skills/tasklist-discipline/SKILL.md` with:
  589	
  590	````markdown
  591	---
  592	name: tasklist-discipline
  593	description: Use whenever planning, closing slices/phases, or referencing work items in a project that uses docs/tasklist.json. Teaches the tasktool CLI surface and the gating concepts; the CLI enforces the rules.
  594	---
  595	
  596	# TASKLIST Discipline
  597	
  598	A `docs/tasklist.json` file is the canonical, top-level tracker for the project. It groups work into **phases**, **slices**, **tasks**, and **cross-cutting** items, each with a stable, never-renumbered ID. All mutations flow through `tasktool`; a pre-commit hook refuses non-canonical bytes, orphaned spec/plan filenames, and any commit that touches the legacy `docs/TASKLIST.md`.
  599	
  600	**Announce at start:** "I'm using the tasklist-discipline skill to update docs/tasklist.json via tasktool."

[truncated: 434 additional lines]

## Context Previews

### docs/specs/2026-05-17-P2-tasktool-design.md

    1	# P2 — tasktool: JSON-backed task management CLI
    2	
    3	**Status:** spec, awaiting external review
    4	**Author:** Simon Greer (with AI brainstorming)
    5	**Date:** 2026-05-17
    6	**TASKLIST entry:** `P2` in [`docs/TASKLIST.md`](../TASKLIST.md)
    7	
    8	## 1. Problem
    9	
   10	`docs/TASKLIST.md` is the canonical project tracker in superstar's workflow. The format is enforced by prose (the `tasklist-discipline` skill), not by code:
   11	
   12	- Stable P/S/T/X IDs, never renumbered.
   13	- Status emoji set (`✅` / `🚧` / `⏸` / `☐`) paired with status tags (`DONE YYYY-MM-DD`, `IN PROGRESS`, `BLOCKED on …`, `READY`).
   14	- Specific date format, specific filename conventions, specific close-in-place / phase-archive rules.
   15	
   16	Two consequences:
   17	
   18	1. **Brittleness for downstream consumers.** The AGS sidebar, external reviewers, and any future dashboards have to re-parse a hand-edited markdown file whose shape is enforced only by an LLM following a skill. A single stray emoji or missing date breaks the consumer.
   19	2. **Context bloat for agents.** The current pattern is "agent reads the entire TASKLIST.md to orient." Most of that content is irrelevant to the agent's current task. The agent absorbs the whole file because targeted queries do not exist.
   20	
   21	Conformity is enforced by repeatedly reminding agents of the rules. This works imperfectly and consumes context every time.
   22	
   23	## 2. Goals
   24	
   25	- **Eliminate hand-editing of the canonical tracker.** All mutations go through a single CLI that validates inputs at write time.
   26	- **Reduce agent context burden.** Replace "read the whole file" with targeted queries (`tasktool brief <id>`, `tasktool show <id>`, `tasktool list --status open`).
   27	- **Produce reliable structured data for downstream tools** (AGS sidebar, reviewers, future dashboards) without forcing them to re-parse markdown.
   28	- **Preserve the existing mental model** (phases / slices / tasks / cross-cutting; stable IDs; close-in-place; phase archive; status gates).
   29	- **Stay zero-dependency.** Python stdlib only. No package install required at the project level — a global shim points at this repo.
   30	
   31	## 3. Non-goals
   32	
   33	- **Cross-project querying.** Each project keeps its own JSON; there is no central store. AGS can read multiple per-project JSONs if it wants a cross-project view.
   34	- **External-system sync.** No Linear, Jira, GitHub Projects integration. Out of scope.
   35	- **Web UI.** Out of scope. The AGS sidebar is the user-facing view; the CLI is the agent-facing view.
   36	- **Concurrent multi-writer correctness.** Single-user, single-machine. File-level write is atomic via tempfile + rename; no locking beyond that.
   37	- **Backwards compatibility with the markdown shape.** `tasktool render` produces a readable markdown view but is not constrained to byte-match the prior hand-written format.
   38	
   39	## 4. Approach summary
   40	
   41	A Python stdlib CLI (`tasktool`) reads and writes a per-project `docs/tasklist.json`. The CLI is the only sanctioned mutation path; the `tasklist-discipline` skill is rewritten to teach the commands rather than the rules. A pre-commit hook enforces that `docs/tasklist.json` only changes via the CLI. The existing `docs/TASKLIST.md` is parsed by a one-shot importer and then deleted; downstream readers (AGS sidebar) consume the JSON directly or import the Python module.
   42	
   43	## 5. Architecture
   44	
   45	### 5.1 Code location & distribution
   46	
   47	- **Source:** `tools/tasktool/` in the superstar repo. Single Python package; entry point `tools/tasktool/__main__.py`.
   48	- **Stdlib only:** `argparse`, `json`, `pathlib`, `dataclasses`, `datetime`, `re`, `sys`, `os`, `subprocess` (for git-staging the JSON after writes), `unittest`.
   49	- **Global shim:** `~/.local/bin/tasktool` — one-line script: `exec python3 /home/simon/Dev/sigreer/skills/superstar/tools/tasktool/__main__.py "$@"`. Installed once per machine by `tools/tasktool/install.sh`. The installer is idempotent; it errors if a different shim already exists at the target path unless `--force` is passed.
   50	- **No per-project install step.** Projects need only the per-project `docs/tasklist.json` and (optionally) the pre-commit hook.
   51	
   52	### 5.2 Per-project state
   53	
   54	- **`docs/tasklist.json`** — canonical, git-tracked.
   55	- **No committed markdown.** `tasktool render` writes a markdown view to stdout on demand. The output is suitable for piping into a temp file for review or pasting into a PR description.
   56	- **Schema version field** in the JSON enables future migrations.
   57	
   58	### 5.3 Integration with consumers
   59	
   60	- **AGS sidebar (Python):** `import tasktool` directly. The installer adds the package to a known site-packages-equivalent path (or symlinks). Functions like `load_project(path)`, `brief(project, id)` are exposed.
   61	- **Other tools:** read `docs/tasklist.json` directly, validated against the schema emitted by `tasktool schema`.
   62	- **External reviewer / skills:** call `tasktool render`, `tasktool show`, `tasktool brief` as needed.
   63	
   64	## 6. Data model
   65	
   66	### 6.1 Top-level shape (`docs/tasklist.json`)
   67	
   68	```json
   69	{
   70	  "schema_version": 1,
   71	  "project": "superstar",
   72	  "north_star": "Optional one-paragraph project intent.",
   73	  "last_reviewed": "2026-05-17",
   74	  "phases": [ /* Phase[] */ ],
   75	  "cross_cutting": [ /* CrossCuttingItem[] */ ],
   76	  "archived_phases": [ /* { id, title, archived_path, archived_date } */ ]
   77	}
   78	```
   79	
   80	### 6.2 Phase
   81	
   82	```json
   83	{
   84	  "id": "P2",
   85	  "title": "tasktool: JSON-backed task management CLI",
   86	  "status": "in_progress",
   87	  "created": "2026-05-17",
   88	  "closed": null,
   89	  "spec_path": "docs/specs/2026-05-17-P2-tasktool-design.md",
   90	  "plan_path": null,
   91	  "phase_reviewer_chain": null,
   92	  "notes": "",
   93	  "slices": [ /* Slice[] */ ]
   94	}
   95	```
   96	
   97	### 6.3 Slice
   98	
   99	```json
  100	{
  101	  "id": "S1",
  102	  "title": "CLI core",
  103	  "status": "ready",
  104	  "created": "2026-05-17",
  105	  "closed": null,
  106	  "blocked_on": null,
  107	  "plan_path": null,
  108	  "refs": [],
  109	  "notes": "",
  110	  "reviewer_chain": null,
  111	  "tasks": [ /* Task[] */ ]
  112	}
  113	```
  114	
  115	- `id` is the short form within its phase (`S1`, `S5a`).
  116	- Follow-up slices use a letter suffix (`S5a`); the suffix is part of the ID string. Ordering within `slices[]` is execution order; ID order is creation order.
  117	- `blocked_on` is `null` or `{ "kind": "id" | "external", "value": "P2.S1" | "vendor X" }`.
  118	- `reviewer_chain` is the relative path to the post-slice reviewer chain folder once one exists.
  119	
  120	### 6.4 Task
  121	
  122	```json
  123	{
  124	  "id": "T1",
  125	  "title": "Implement data model module",
  126	  "status": "ready",
  127	  "created": "2026-05-17",
  128	  "closed": null,
  129	  "refs": [],
  130	  "notes": ""
  131	}
  132	```
  133	
  134	Inline follow-ons that used to be unstructured bullets become first-class tasks with their own `T{n}` IDs.
  135	
  136	### 6.5 Cross-cutting
  137	
  138	```json
  139	{
  140	  "id": "X1",
  141	  "title": "...",
  142	  "status": "ready",
  143	  "created": "...",
  144	  "closed": null,
  145	  "refs": [],
  146	  "notes": ""
  147	}
  148	```
  149	
  150	### 6.6 Status enum
  151	
  152	`done | in_progress | blocked | ready`
  153	
  154	Stored as a plain string. Emoji is a render concern. `done` requires a non-null `closed` date (validator enforces).
  155	
  156	**Blocking is slice-scoped.** Only slices carry `blocked_on` and may take status `blocked`. Phases, tasks, and cross-cutting items use `ready | in_progress | done` only. Rationale: at the granularity of phases and tasks, "blocked" conflates with "waiting" and "deferred" without adding signal; at the slice boundary it has a clear meaning (a unit of work that cannot proceed until another finishes). The validator rejects `blocked` status on phases/tasks/cross-cutting and rejects a non-null `blocked_on` on the same. The `tasktool block` / `unblock` commands accept only slice IDs and error otherwise.
  157	
  158	### 6.7 Dates
  159	
  160	ISO 8601 date (`YYYY-MM-DD`). `closed` is auto-stamped to today at the moment of status→done; the user can backdate via `--closed-date YYYY-MM-DD`. `created` is auto-stamped at create time and is read-only thereafter (no `tasktool` command edits it; raw-edit escape hatch only).
  161	
  162	### 6.8 Fully-qualified IDs
  163	
  164	Stored as short form (`S2`, `T1`); fully-qualified form (`P2.S1.T1`) is derived for display and CLI arguments. The CLI accepts both forms in arguments; ambiguous short forms (e.g., `S1` without a phase context) are rejected with a clear error.
  165	
  166	### 6.9 Validation rules
  167	
  168	- ID format: `P\d+`, `S\d+[a-z]?`, `T\d+`, `X\d+`.
  169	- IDs unique within their scope.
  170	- `done` requires `closed != null`.
  171	- `blocked` requires `blocked_on != null`.
  172	- `closed >= created` when both set.
  173	- `spec_path`, `plan_path`, `refs[]` are checked for filesystem existence by `tasktool validate` (warning, not error, since paths may be deleted in branches).
  174	- `reviewer_chain` directory must exist at slice close time when post-slice review is required.
  175	
  176	## 7. CLI surface
  177	
  178	Conventions: arguments named `<id>` accept fully-qualified (`P2.S1`) or short form when unambiguous. Mutating commands write atomically (tempfile + rename) and `git add` the file (best-effort; non-fatal if not a git repo).
  179	
  180	### 7.1 Lifecycle
  181	
  182	```
  183	tasktool init [--project NAME] [--north-star TEXT]
  184	    Create empty docs/tasklist.json. Errors if file exists unless --force.
  185	
  186	tasktool import PATH_TO_TASKLIST_MD [--dry-run]
  187	    One-shot migration from existing TASKLIST.md. Prints unparsed lines as warnings.
  188	    --dry-run prints the JSON it would write without touching disk.
  189	
  190	tasktool schema
  191	    Emit the JSON Schema for tasklist.json to stdout.
  192	```
  193	
  194	### 7.2 Create
  195	
  196	```
  197	tasktool create phase --title TEXT [--spec PATH] [--plan PATH]
  198	    Allocates next P{n}, taking the orphan-aware max+1 across the file plus docs/specs/, docs/plans/, docs/reviewer/ filename prefixes. Prints the new ID.
  199	
  200	tasktool create slice <phase-id> --title TEXT [--follow-up <slice-id>] [--plan PATH]

[truncated: 171 additional lines]
### docs/tasklist.json

    1	{
    2	  "archived_phases": [],
    3	  "cross_cutting": [],
    4	  "last_reviewed": "2026-05-18",
    5	  "north_star": "",
    6	  "phases": [
    7	    {
    8	      "closed": "2026-05-17",
    9	      "created": "2026-05-17",
   10	      "id": "P1",
   11	      "notes": "",
   12	      "phase_reviewer_chain": null,
   13	      "plan_path": null,
   14	      "slices": [],
   15	      "spec_path": null,
   16	      "status": "done",
   17	      "title": "External-reviewer work (historical)"
   18	    },
   19	    {
   20	      "closed": null,
   21	      "created": "2026-05-17",
   22	      "id": "P2",
   23	      "notes": "",
   24	      "phase_reviewer_chain": null,
   25	      "plan_path": null,
   26	      "slices": [
   27	        {
   28	          "blocked_on": null,
   29	          "closed": "2026-05-18",
   30	          "created": "2026-05-17",
   31	          "id": "S1",
   32	          "notes": "",
   33	          "plan_path": "docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md",
   34	          "refs": [],
   35	          "reviewer_chain": "docs/reviewer/p2-s1-tasktool-cli-core-P2-S1-post-slice/",
   36	          "status": "done",
   37	          "tasks": [],
   38	          "title": "CLI core: data model, canonical serializer, allocation, validation, reviewer-gate, and the create/set/close/block/note/ref/title/show/list/validate/schema/next-id/init commands"
   39	        },
   40	        {
   41	          "blocked_on": null,
   42	          "closed": "2026-05-18",
   43	          "created": "2026-05-18",
   44	          "id": "S2",
   45	          "notes": "[2026-05-18T12:42:29] review gate skipped for P2.S2\npost-slice external review reached verdict 'ready' at round 3 (reviewer body was duplicated by the codex wrapper, confusing the script's verdict parser; substantive verdict is unambiguous in r3 response). Close used --skip-review-gate to bypass the parser artifact.",
   46	          "plan_path": "docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md",
   47	          "refs": [],
   48	          "reviewer_chain": null,
   49	          "status": "done",
   50	          "tasks": [],
   51	          "title": "Importer, render, brief, archive-phase; migrate this repo from `TASKLIST.md` to `tasklist.json`"
   52	        },
   53	        {
   54	          "blocked_on": null,
   55	          "closed": null,
   56	          "created": "2026-05-18",
   57	          "id": "S3",
   58	          "notes": "Plan: docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md (recorded via ref; plan_path field remains null — tasktool has no edit-slice-plan-path command in S1/S2)",
   59	          "plan_path": null,
   60	          "refs": [
   61	            "docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md"
   62	          ],
   63	          "reviewer_chain": null,
   64	          "status": "in_progress",
   65	          "tasks": [],
   66	          "title": "Rewrite `tasklist-discipline` skill; install pre-commit hook; touch up sibling skills (`writing-plans`, `external-review`, `project-setup`, `brainstorming`, `subagent-driven-development`)"
   67	        }
   68	      ],
   69	      "spec_path": "docs/specs/2026-05-17-P2-tasktool-design.md",
   70	      "status": "in_progress",
   71	      "title": "tasktool: JSON-backed task management CLI"
   72	    }
   73	  ],
   74	  "project": "superstar",
   75	  "schema_version": 1
   76	}

<!-- superstar-prompt:end -->