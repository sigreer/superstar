# P7.S8 — Reviewer-Artifact Collision Investigation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. NOTE: this is an INVESTIGATION slice — its first deliverable is a reproduce-or-refute decision, not a feature.

**Goal:** Reproduce-or-refute the P20-reported claim that generated external-reviewer request files add/add-conflict between sibling worktrees, against the *current* `external-reviewer.py` bridge, and either ship a targeted fix + regression test (if reproduced) or document-and-drop the slice (if not).

**Architecture:** The investigation reads the path/filename generation in `skills/external-review/scripts/external-reviewer.py`, then constructs a deterministic simulation of two sibling worktrees each running a `post-slice` review and diffs the produced filesystem paths. A single decision gate (§ "Decision gate") routes to one of two fully-specified branches: a fix branch (make any shared path per-slice/round-unique, add a regression test built from the reproduced scenario) or a document-and-drop branch (write a phase-archive note explaining why the original report does not reproduce against the current bridge, and record that the residual `docs/tasklist.json` close-churn conflict is owned by the integrate-current-main checkpoint, P7.S6 / spec §4.F, not by reviewer-artifact naming).

**Tech Stack:** Python 3, git, pytest

---

## Scheduling

- **Slice ID:** `P7.S8`
- **depends_on:** none. Independently executable.
- **Parallel-safe:** yes. Disjoint write surface (`external-review`, `reviewer-artifacts`); shares nothing with the rest of P7 (`model`/`serialize`/`migrate`/`cli`/`commands`/`worktree`/`skills`/`validate`). Spec §5 lists S7 and S8 as parallel on disjoint surfaces.
- **Decision branch:** This slice may legitimately terminate with **no source change** (document-and-drop). That is a success outcome, not an incomplete one.

---

## Background context for the engineer (zero project knowledge assumed)

The external reviewer is a file-based CLI bridge. `external-reviewer.py review --kind <kind> --file <target> [--work-id <id>]` creates a *chain folder* under `docs/reviewer/` and writes one request file (and later a response file) per review *round*. The P20 post-mortem (spec §1, item 4; §4.H) claimed these generated request files add/add-conflicted when sibling slices were developed in parallel git worktrees and later merged.

The current bridge already has three mitigations that the spec (§4.H) cites by line:

1. **Chain folder keyed by `work_id`** — `chain_folder_name()` at `skills/external-review/scripts/external-reviewer.py:727`. For `post-slice`/`post-phase` with a `work_id`, the folder name is `f"{base}-{work_id_slug}-{kind}"` (dots in the work-id replaced by hyphens, line 730–732). So slice `P2.S3` reviewing `2026-05-13-feature-plan.md` gets folder `feature-plan-P2-S3-post-slice`, while sibling `P2.S4` gets `feature-plan-P2-S4-post-slice`. Confirmed by `skills/external-review/tests/test_chain_folder_name.py`.
2. **Round/role-unique request filenames** — `run_one_reviewer()` at `:1403`. The basename is `f"r{round_num}-{timestamp}{suffix}"` where `suffix` is empty, `-primary`, or `-sweep{N}` (lines 1403–1407), and `timestamp = _now_local().strftime("%Y-%m-%dT%H%M")` (minute resolution, set at `:2575`/`:2049`/`:1974` call sites and passed in).
3. **`--work-id` required for post-slice/post-phase** — main() at `:2439`. Without it, the command exits 2 before any folder is created.

So the spec does **not** assume a current bug. Item 4 of the P20 report may have come from (a) an *older* bridge that did not key the folder by `work_id`; (b) `docs/tasklist.json` close-time churn (a *different* conflict class — see below) mis-attributed to request files; or (c) a genuinely shared phase-level path. This slice's job is to determine which.

**Two distinct conflict classes — keep them separate throughout:**

- **Class A — request/response file collision.** Two sibling worktrees write the *same path* under `docs/reviewer/.../rN-...-request.md`, producing a git add/add conflict on merge. This is what §4.H is about and what this slice investigates.
- **Class B — `docs/tasklist.json` close-churn.** When a slice's review chain is registered, `tools/tasktool/artifacts.py` (`register`, lines ~151–156) writes the chain's relative path onto the slice/phase row as `reviewer_chain` / `phase_reviewer_chain`. Two siblings closing near-simultaneously both rewrite `docs/tasklist.json`, producing an ordinary line-level merge conflict in that file. This is **not** a request-file-naming problem and is explicitly **out of scope** for S8: spec §4.H and §4.F assign it to the integrate-current-main checkpoint (P7.S6). The plan must not "fix" Class B by renaming request files.

---

## Investigation steps

### Setup

- [ ] **Step 0 — Start the slice.** Run, from repo root `/home/simon/Dev/sigreer/skills/superstar`:
  ```sh
  tasktool start P7.S8
  ```
  Do no other work until this succeeds.

- [ ] **Step 1 — Create a scratch workspace** outside the repo to hold the simulation and notes:
  ```sh
  mkdir -p /tmp/p7s8 && cd /tmp/p7s8
  ```
  All simulation artifacts live here; nothing is committed except (conditionally) the fix and test in Step 8.

### Read the real code (confirm or correct the spec's claims)

- [ ] **Step 2 — Read `chain_folder_name`** at `skills/external-review/scripts/external-reviewer.py:727-733`. Confirm: for `kind ∈ {post-slice, post-phase}` **and** a non-empty `work_id`, the folder is `f"{base}-{work_id_slug}-{kind}"`; otherwise `f"{base}-{kind}"`. Record the exact branch conditions. **Red flag to look for:** for `post-phase`, the `work_id` is a *phase* ID (e.g. `P2`), which is identical for every sibling slice in that phase — so two slices that each run `post-phase` against the **same target file with the same phase work-id** would resolve to the **same folder**. Note whether the workflow ever has two distinct slices invoking `post-phase` on the same file (normally only one post-phase review happens per phase; flag if otherwise).

- [ ] **Step 3 — Read `run_one_reviewer`** at `:1388-1412`. Confirm the request path is `chain_dir / f"r{round_num}-{timestamp}{suffix}-request.md"`. Record: (a) `round_num` comes from `next_round_number(chain_dir)` (`:777`), which counts existing rounds in *that chain folder* — so it is per-chain, not global; (b) `timestamp` is **minute-resolution** (`strftime("%Y-%m-%dT%H%M")`). Note the consequence: within a *single shared* chain folder, two rounds started in the same minute with the same `round_num` and same `suffix` would collide — but across *distinct* work-id-keyed folders this is irrelevant.

- [ ] **Step 4 — Read the chain-dir resolution in `main()`** at `:2446-2473`. Confirm `reviewer_root = root / args.output_dir` (default `docs/reviewer`, `:1831-1832`), `new_slug = chain_folder_name(...)` (`:2460`), and `chain_dir = existing or (reviewer_root / new_slug)` (`:2472`). Confirm the `--work-id` guard at `:2439-2445` fires for post-slice/post-phase. Note the work-id-mismatch refusal at `:2510-2528` (an existing chain with a different stored `work_id` is refused, not silently reused) — this prevents two slices from *sharing* a folder by accident.

- [ ] **Step 5 — Read the response/scratch layout** at `:1499-1525`: `response_dir = chain_dir / ".reviewer-output" / f"r{round_num}-{role_name}"` and `scratch_dir = tempfile.mkdtemp(...)`. Confirm these are all *under* `chain_dir` (so they inherit the work-id keying) and that `scratch_dir` is an OS temp dir (never committed). Conclusion to record: if `chain_dir` is unique per slice, every derived path is too.

- [ ] **Step 6 — Read `register` in `tools/tasktool/artifacts.py`** lines ~119–156 and ~300–390. Confirm it writes `item.reviewer_chain` / `item.phase_reviewer_chain` onto the tasklist row (Class B), and that this is the *only* place the reviewer chain touches `docs/tasklist.json`. Record this explicitly so the final note can state that Class B is real but out of scope.

- [ ] **Step 7 — Survey existing tests.** Confirm coverage of path generation already exists at `skills/external-review/tests/test_chain_folder_name.py` (folder naming) and `skills/external-review/tests/test_work_id.py` (work-id requirement + mismatch). Note that **no** existing test exercises *two sibling slices producing non-colliding request paths* — that is the gap the regression test (Step 8, fix branch) would fill. Confirm the test idiom: `test_chain_folder_name.py` imports the module directly via `importlib`; `test_work_id.py` shells out with a stub `stub.sh` reviewer that echoes `Overall verdict: ready`.

### Reproduce or refute (the core experiment)

- [ ] **Step 8 — Simulate two sibling worktrees and diff the produced paths.** Write `/tmp/p7s8/repro.py` that drives the *real* script twice — once per simulated sibling slice — and asserts whether their request paths collide. Use the proven idiom from `test_work_id.py` (git-init a temp repo, a `stub.sh` reviewer). The simulation does **not** need real worktrees: an add/add conflict is purely a function of whether the two branches write the **same relative path**, so producing both review chains in the same repo and comparing the relative paths under `docs/reviewer/` is sufficient and faithful.

  ```python
  # /tmp/p7s8/repro.py  — run: python /tmp/p7s8/repro.py
  import subprocess, sys, os
  from pathlib import Path

  REPO_ROOT = Path("/home/simon/Dev/sigreer/skills/superstar")
  SCRIPT = REPO_ROOT / "skills/external-review/scripts/external-reviewer.py"

  def init_repo(d: Path) -> Path:
      d.mkdir(parents=True)
      run = lambda *a: subprocess.run(["git", "-C", str(d), *a], check=True,
                                      capture_output=True)
      run("init", "-q"); run("config", "user.email", "t@t"); run("config", "user.name", "T")
      (d / "2026-06-02-feature-plan.md").write_text("# plan\n")
      run("add", "-A"); run("commit", "-q", "-m", "init")
      stub = d / "stub.sh"
      stub.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
      stub.chmod(0o755)
      return d

  def _request_paths(repo: Path) -> set[str]:
      base = repo / "docs/reviewer"
      if not base.exists():
          return set()
      return {str(p.relative_to(repo)) for p in base.rglob("*-request.md")}

  def review(repo: Path, work_id: str) -> set[str]:
      # CRITICAL: return only the request files THIS invocation created (the delta),
      # not every request file in the repo. A naive "return all *-request.md" makes a
      # later invocation's result set contain the earlier invocation's files, so
      # set(a) & set(b) would intersect on A's own paths and report a false collision.
      before = _request_paths(repo)
      env = os.environ.copy(); env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
      r = subprocess.run(
          [sys.executable, str(SCRIPT), "review", "--kind", "post-slice",
           "--file", "2026-06-02-feature-plan.md", "--work-id", work_id, "--emit", "json"],
          cwd=repo, env=env, capture_output=True, text=True)
      assert r.returncode == 0, r.stderr
      after = _request_paths(repo)
      return after - before  # delta: only paths created by this invocation

  base = Path("/tmp/p7s8/work"); 
  if base.exists():
      import shutil; shutil.rmtree(base)
  repo = init_repo(base)
  # Sibling A reviews as P2.S3, sibling B as P2.S4 — same target plan file.
  a = review(repo, "P2.S3")
  b = review(repo, "P2.S4")
  print("sibling A request paths:", a)
  print("sibling B request paths:", b)
  collisions = set(a) & set(b)
  print("COLLISION:" , bool(collisions), collisions or "(none)")
  ```
  Run it:
  ```sh
  python /tmp/p7s8/repro.py | tee /tmp/p7s8/repro-distinct-workid.txt
  ```
  **Expected (per code read):** A's paths live under `docs/reviewer/feature-plan-P2-S3-post-slice/` and B's under `docs/reviewer/feature-plan-P2-S4-post-slice/` → `COLLISION: False`. Distinct work-ids ⇒ distinct folders ⇒ no add/add. Record the actual output.

- [ ] **Step 9 — Probe the misuse / phase-level cases** that could still collide. Re-run the simulation in two extra configurations and capture each output:
  1. **Same work-id (operator misuse):** call `review(repo, "P2.S3")` twice. Both resolve to the same folder; whether the *second round's* request path collides with the first depends on `next_round_number` incrementing (so `r2-...` vs `r1-...`). Record whether the two invocations produce `r1` and `r2` (no collision *within one repo*), and reason about the cross-worktree case: two **separate** worktrees that both branched before either review, each running with the **same** work-id, would each independently compute `next_round_number == 1` (each sees an empty chain) and each write `r1-<same-minute>-request.md` → **add/add collision**. Note this requires (a) identical work-id across siblings (a workflow error the §4.H folder keying is meant to prevent) and (b) same-minute start. Capture this as the *only* reproduced Class-A path, if any.
     ```sh
     python - <<'PY' | tee /tmp/p7s8/repro-same-workid-fresh.txt
     # Simulate two FRESH worktrees (each an independent clone) running the same work-id.
     import subprocess, sys, os, shutil
     from pathlib import Path
     REPO=Path("/home/simon/Dev/sigreer/skills/superstar")
     SCRIPT=REPO/"skills/external-review/scripts/external-reviewer.py"
     def mk(d):
         d.mkdir(parents=True)
         g=lambda *a: subprocess.run(["git","-C",str(d),*a],check=True,capture_output=True)
         g("init","-q"); g("config","user.email","t@t"); g("config","user.name","T")
         (d/"2026-06-02-feature-plan.md").write_text("# plan\n"); g("add","-A"); g("commit","-q","-m","i")
         s=d/"stub.sh"; s.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n"); s.chmod(0o755); return d
     def paths(d):
         b=d/"docs/reviewer"
         return {str(p.relative_to(d)) for p in b.rglob("*-request.md")} if b.exists() else set()
     def rev(d, kind="post-slice", work_id="P2.S3"):
         before=paths(d)  # delta only — each fresh worktree starts empty, but stay faithful
         e=os.environ.copy(); e["AGENT_REVIEWER_CMD"]=str(d/"stub.sh")
         r=subprocess.run([sys.executable,str(SCRIPT),"review","--kind",kind,
             "--file","2026-06-02-feature-plan.md","--work-id",work_id,"--emit","json"],
             cwd=d,env=e,capture_output=True,text=True); assert r.returncode==0,r.stderr
         return paths(d)-before
     root=Path("/tmp/p7s8/fresh"); shutil.rmtree(root,ignore_errors=True)
     wa=rev(mk(root/"wtA")); wb=rev(mk(root/"wtB"))
     print("wtA:",wa); print("wtB:",wb)
     print("CROSS-WORKTREE COLLISION (same work-id):", bool(wa&wb), (wa&wb) or "(none)")
     PY
     ```
  2. **Post-phase, two slices, same phase id, same target file:** two fresh worktrees both run `--kind post-phase --work-id P2` against the same plan file. Both resolve to folder `feature-plan-P2-post-phase` and both write `r1-<minute>-request.md` → potential collision. The snippet reuses the exact `mk`/`paths`/`rev` helpers from Step 9.1 (now parameterized on `kind`/`work_id`), so there is no execution drift between the two probes:
     ```sh
     python - <<'PY' | tee /tmp/p7s8/repro-post-phase.txt
     # Reuses the Step 9.1 helpers verbatim; only the rev() call differs (post-phase, phase id).
     import subprocess, sys, os, shutil
     from pathlib import Path
     REPO=Path("/home/simon/Dev/sigreer/skills/superstar")
     SCRIPT=REPO/"skills/external-review/scripts/external-reviewer.py"
     def mk(d):
         d.mkdir(parents=True)
         g=lambda *a: subprocess.run(["git","-C",str(d),*a],check=True,capture_output=True)
         g("init","-q"); g("config","user.email","t@t"); g("config","user.name","T")
         (d/"2026-06-02-feature-plan.md").write_text("# plan\n"); g("add","-A"); g("commit","-q","-m","i")
         s=d/"stub.sh"; s.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n"); s.chmod(0o755); return d
     def paths(d):
         b=d/"docs/reviewer"
         return {str(p.relative_to(d)) for p in b.rglob("*-request.md")} if b.exists() else set()
     def rev(d, kind="post-slice", work_id="P2.S3"):
         before=paths(d)
         e=os.environ.copy(); e["AGENT_REVIEWER_CMD"]=str(d/"stub.sh")
         r=subprocess.run([sys.executable,str(SCRIPT),"review","--kind",kind,
             "--file","2026-06-02-feature-plan.md","--work-id",work_id,"--emit","json"],
             cwd=d,env=e,capture_output=True,text=True); assert r.returncode==0,r.stderr
         return paths(d)-before
     root=Path("/tmp/p7s8/postphase"); shutil.rmtree(root,ignore_errors=True)
     wa=rev(mk(root/"wtA"), kind="post-phase", work_id="P2")
     wb=rev(mk(root/"wtB"), kind="post-phase", work_id="P2")
     print("wtA:",wa); print("wtB:",wb)
     print("CROSS-WORKTREE COLLISION (post-phase, same phase id):", bool(wa&wb), (wa&wb) or "(none)")
     PY
     ```
     Record the result, then determine whether the workflow ever produces two such invocations: normally exactly one post-phase review exists per phase, so even if the paths collide *in this synthetic probe* the case is not reachable in practice. If the workflow guarantees a single post-phase reviewer, note that this collision is unreachable and does not, on its own, satisfy the Decision gate's "workflow-reachable" criterion.

### Decision gate (apply criteria from the "Decision gate" section)

- [ ] **Step 10 — Classify the result** using the criteria below. Write the verdict and the captured outputs to `/tmp/p7s8/decision.md`. The verdict is exactly one of `REPRODUCES` or `DOES-NOT-REPRODUCE`.

### Branch A — REPRODUCES (CONDITIONAL — only execute if Step 9 found a real, workflow-reachable Class-A collision)

> **Conditional-branch framing.** The investigation's *expected* outcome is Branch B (no reproduction against the current bridge — see the Decision gate). Do **not** start Branch A unless the Decision gate selects `REPRODUCES`. When you do, the fix recipe below must be applied in full: it covers **both** basename-construction sites (`run_one_reviewer` *and* the late final-ready primary rename) and a deterministic test that pins both the unique token and the timestamp. A partial fix that touches only `run_one_reviewer` is incomplete — the rename path at `:2692-2698` would reopen the same collision class for sweep-enabled runs (see edit (c) and F4 below).

- [ ] **Step 11A — Specify the fix.** Make the colliding component per-slice/round-unique, AND make basename + timestamp generation unit-testable so the regression test does not depend on wall-clock minute boundaries. Four coordinated edits to `skills/external-review/scripts/external-reviewer.py`:

  **(a) Factor basename generation into a module-level helper** with a test-mode token override. Add near the other helpers (e.g. just below `next_round_number`, ~`:784`):
  ```python
  import uuid  # at module top with the other stdlib imports, not inline

  def request_basename(round_num: int, timestamp: str, suffix: str, *, unique: str | None = None) -> str:
      """Build the per-round request/response basename.

      `unique` is a short per-invocation token that guarantees two sibling
      worktrees which resolve to the SAME chain folder (same work-id) and start in
      the SAME minute cannot write the same request path → no add/add merge conflict.
      A None default generates a fresh uuid4; callers (and tests) may inject a fixed
      token for determinism. An AGENT_REVIEWER_FAKE_UNIQUE env var, when set, pins
      the token in test mode so the basename is fully deterministic.
      """
      if unique is None:
          unique = os.environ.get("AGENT_REVIEWER_FAKE_UNIQUE") or uuid.uuid4().hex[:8]
      return f"r{round_num}-{timestamp}{suffix}-{unique}"
  ```

  **(b) Add a test-mode timestamp override** at the single generation site (`:2575`), so the regression test can pin the minute deterministically instead of hoping both subprocesses land in the same wall-clock minute:
  ```python
  # BEFORE (:2575)
  timestamp = dt.datetime.now().strftime("%Y-%m-%dT%H%M")

  # AFTER — honour AGENT_REVIEWER_FAKE_TIMESTAMP in test mode; production is unchanged.
  timestamp = os.environ.get("AGENT_REVIEWER_FAKE_TIMESTAMP") or dt.datetime.now().strftime("%Y-%m-%dT%H%M")
  ```
  This `timestamp` is the value threaded into both `run_one_reviewer` and the final-ready rename below, so a single override pins every basename in the run.

  **(c) Call the helper from `run_one_reviewer`** at `:1403-1408`:
  ```python
  # BEFORE (:1403-1408)
  suffix = ""
  if namespaced:
      suffix = "-primary" if role == "primary" else f"-sweep{sweep_index}"
  basename = f"r{round_num}-{timestamp}{suffix}"

  # AFTER
  suffix = ""
  if namespaced:
      suffix = "-primary" if role == "primary" else f"-sweep{sweep_index}"
  basename = request_basename(round_num, timestamp, suffix)
  ```

  **(d) Route the final-ready primary rename through the unique helper** (F4). When a sweep-enabled run (`--review-depth thorough`/`exhaustive` → `sweep_plan.sweep_count > 0`) ran the primary *un-namespaced*, the script renames the primary artefacts to add a `-primary` suffix at `:2692-2698`, reconstructing the basename as `f"r{round_num}-{timestamp}{new_suffix}"` — **without** the uuid token. That rename re-collapses a uuid-bearing primary request back to a non-unique `rN-<minute>-primary-request.md`, reopening the exact collision class edit (c) closed. The rename target must use the **same** unique token the original request carried, so derive it from the existing filename rather than minting a new one (a new token would orphan the response's `Request:` back-reference and break `next_round_number` glob expectations). Edit `:2694-2698`:
  ```python
  # BEFORE (:2694-2698)
  if sweep_plan.sweep_count > 0 and not namespaced:
      new_suffix = "-primary"
      new_basename = f"r{round_num}-{timestamp}{new_suffix}"
      new_request = chain_dir / f"{new_basename}-request.md"
      new_response = chain_dir / f"{new_basename}-response.md"

  # AFTER — preserve the original request's unique token so the renamed primary stays
  # collision-safe. The original basename is `r{round_num}-{timestamp}-{unique}` (no
  # suffix, since this branch only runs when the primary was NOT namespaced); recover
  # `{unique}` from the existing filename and re-insert the `-primary` suffix BEFORE it.
  if sweep_plan.sweep_count > 0 and not namespaced:
      orig_stem = primary.request_path.name[: -len("-request.md")]   # r{n}-{ts}-{unique}
      prefix = f"r{round_num}-{timestamp}"
      unique = orig_stem[len(prefix) + 1:] if orig_stem.startswith(prefix + "-") else None
      new_basename = request_basename(round_num, timestamp, "-primary", unique=unique)
      new_request = chain_dir / f"{new_basename}-request.md"
      new_response = chain_dir / f"{new_basename}-response.md"
  ```
  (If `unique` cannot be recovered — `None` — `request_basename` mints a fresh token, which is still collision-safe; it merely changes the token across the rename, which is acceptable because the response back-reference is rewritten immediately below at `:2707-2712`.)

  Note the trade-off and resolve it before coding: the uuid token keeps `next_round_number`'s glob-based fallback (`:783`, `glob("r*-*-request.md")`) matching (pattern is `r*-*`), and the manifest-based round count is unaffected. The residual risk the token closes is precisely the *same-folder same-round same-minute* cross-worktree case from Step 9.1, in **both** the initial-write path (edit c) and the sweep final-ready rename path (edit d). Confirm by re-running `repro-same-workid-fresh.txt` after the edits and asserting `COLLISION: False`.

- [ ] **Step 12A — Add a regression test** built from the reproduced scenario at `skills/external-review/tests/test_sibling_request_paths.py`. It has two layers: a fast deterministic unit test on `request_basename` (no clock dependence), and end-to-end sibling tests whose collision check is made fully deterministic by injecting **both** the unique token (`AGENT_REVIEWER_FAKE_UNIQUE`, edit a) **and** the minute timestamp (`AGENT_REVIEWER_FAKE_TIMESTAMP`, edit b) — so neither the random token nor a wall-clock minute boundary can mask or fabricate a collision. The end-to-end layer covers the initial-write path, the same-work-id cross-worktree case, a deterministic negative control, and the sweep final-ready primary-rename path (edit d / F4).
  ```python
  from pathlib import Path
  import subprocess, sys, os, importlib.util

  SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
  _spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
  er = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(er)

  # --- Layer 1: deterministic unit test on the basename helper (no subprocess, no clock) ---
  def test_request_basename_unique_with_injected_token():
      a = er.request_basename(1, "2026-06-02T1200", "", unique="aaaaaaaa")
      b = er.request_basename(1, "2026-06-02T1200", "", unique="bbbbbbbb")
      assert a != b                      # same round/minute, different token => distinct
      assert a == "r1-2026-06-02T1200-aaaaaaaa"

  def test_request_basename_default_token_is_random(monkeypatch):
      monkeypatch.delenv("AGENT_REVIEWER_FAKE_UNIQUE", raising=False)
      a = er.request_basename(1, "2026-06-02T1200", "")
      b = er.request_basename(1, "2026-06-02T1200", "")
      assert a != b                      # two default invocations never collide

  # --- Layer 2: end-to-end sibling simulation (delta-only, deterministic clock) ---
  def _init(d: Path) -> Path:
      d.mkdir(parents=True)
      g = lambda *a: subprocess.run(["git", "-C", str(d), *a], check=True, capture_output=True)
      g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "T")
      (d / "2026-06-02-feature-plan.md").write_text("# plan\n"); g("add", "-A"); g("commit", "-q", "-m", "i")
      s = d / "stub.sh"; s.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n"); s.chmod(0o755)
      return d

  def _request_paths(d: Path) -> set:
      base = d / "docs/reviewer"
      return {str(p.relative_to(d)) for p in base.rglob("*-request.md")} if base.exists() else set()

  PINNED_TS = "2026-06-02T1200"  # arbitrary fixed minute for deterministic tests

  def _review(d: Path, work_id: str, *, fake_unique: str | None = None,
              fake_timestamp: str | None = None, depth: str | None = None) -> set:
      # Return ONLY the delta this invocation created — never the whole repo's set,
      # or a later sibling's result would intersect an earlier sibling's own paths
      # and report a false collision (F1).
      before = _request_paths(d)
      env = os.environ.copy(); env["AGENT_REVIEWER_CMD"] = str(d / "stub.sh")
      if fake_unique is not None:
          env["AGENT_REVIEWER_FAKE_UNIQUE"] = fake_unique        # pin token (edit a)
      if fake_timestamp is not None:
          env["AGENT_REVIEWER_FAKE_TIMESTAMP"] = fake_timestamp  # pin minute (edit b)
      cmd = [sys.executable, str(SCRIPTS / "external-reviewer.py"),
             "review", "--kind", "post-slice", "--file", "2026-06-02-feature-plan.md",
             "--work-id", work_id, "--emit", "json"]
      if depth is not None:
          cmd += ["--review-depth", depth]   # exercise the sweep final-ready rename path
      r = subprocess.run(cmd, cwd=d, env=env, capture_output=True, text=True)
      assert r.returncode == 0, r.stderr
      return _request_paths(d) - before

  def test_distinct_workid_siblings_dont_collide(tmp_path):
      repo = _init(tmp_path / "r")
      a = _review(repo, "P2.S3"); b = _review(repo, "P2.S4")
      assert not (a & b), f"add/add collision: {a & b}"

  def test_same_workid_fresh_worktrees_dont_collide(tmp_path):
      # Two independent worktrees, identical work-id, same target, SAME pinned minute.
      # The ONLY remaining differentiator is the production uuid4 token (no fake token
      # injected), so this passes only because edit (c) adds that token — proving the
      # fix. Pinning the timestamp removes the wall-clock minute boundary as a source
      # of accidental (non-fix) distinctness (F2).
      a = _review(_init(tmp_path / "wtA"), "P2.S3", fake_timestamp=PINNED_TS)
      b = _review(_init(tmp_path / "wtB"), "P2.S3", fake_timestamp=PINNED_TS)
      assert not (a & b), f"add/add collision: {a & b}"

  def test_same_workid_same_token_and_minute_would_collide_without_fix(tmp_path):
      # Deterministic negative control: pin BOTH the token AND the minute identical
      # across two worktrees. The basenames are then byte-identical, proving the
      # collision is real and that the production uuid4 token is exactly what
      # prevents it. Pinning the timestamp (not just the token) is required — without
      # it, two subprocesses straddling a minute boundary would get different `-{ts}-`
      # segments and NOT collide even with the same token, making the assertion flaky.
      a = _review(_init(tmp_path / "wtA"), "P2.S3", fake_unique="deadbeef", fake_timestamp=PINNED_TS)
      b = _review(_init(tmp_path / "wtB"), "P2.S3", fake_unique="deadbeef", fake_timestamp=PINNED_TS)
      assert a & b, "expected identical basenames when token+minute+work-id+target are all pinned"

  def test_sweep_primary_rename_stays_unique(tmp_path):
      # F4: the final-ready primary rename (:2692-2698) must preserve the unique token.
      # Run two same-work-id worktrees with a sweep-enabled depth and the SAME pinned
      # minute, but DISTINCT pinned tokens (mimicking two real production uuids). After
      # the rename to `-primary`, the basenames must remain distinct. Pre-fix (rename
      # rebuilds `rN-<minute>-primary` with no token) these collide; post-fix (edit d
      # preserves the token) they do not. If the stub reviewer cannot trigger a sweep,
      # skip rather than pass vacuously.
      a = _review(_init(tmp_path / "wtA"), "P2.S3", fake_unique="aaaaaaaa",
                  fake_timestamp=PINNED_TS, depth="thorough")
      b = _review(_init(tmp_path / "wtB"), "P2.S3", fake_unique="bbbbbbbb",
                  fake_timestamp=PINNED_TS, depth="thorough")
      # Assert a sweep actually renamed a primary artefact; otherwise the path is
      # untested and the test must not pass silently.
      assert any("-primary-request.md" in p for p in (a | b)), \
          "sweep did not produce a -primary rename; adjust depth/stub to exercise :2692-2698"
      assert not (a & b), f"primary-rename add/add collision: {a & b}"
  ```
  Run `python -m pytest skills/external-review/tests/test_sibling_request_paths.py -q` and confirm: the Layer-1 unit tests, `test_distinct_workid_siblings_dont_collide`, `test_same_workid_fresh_worktrees_dont_collide`, and `test_sweep_primary_rename_stays_unique` all pass after Step 11A's four edits; `test_same_workid_same_token_and_minute_would_collide_without_fix` is the deterministic negative control documenting the exact collision condition the token removes.

  **Sweep-trigger caveat (resolve before relying on `test_sweep_primary_rename_stays_unique`).** Whether `--review-depth thorough` actually drives `sweep_plan.sweep_count > 0` with the trivial `stub.sh` reviewer depends on `plan_sweeps`/`--independent-reviewers`/`--sweep-policy` and the primary verdict. During Branch A, first confirm the rename path fires by inspecting the produced filenames (the `assert any(... "-primary-request.md" ...)` guard above enforces this — it converts a non-firing sweep into an explicit failure, not a false pass). If the stub cannot trigger a sweep in this harness, either (i) pass the needed `--independent-reviewers N`/`--sweep-policy` flags through `_review` and a stub that returns a sweep-eligible verdict, or (ii) **scope the fix**: if `:2692-2698` is provably unreachable for `post-slice` reviews as actually invoked by the workflow, document that constraint here and cover the rename via a focused unit test that calls the rename basename construction directly with two distinct tokens and asserts distinct results — do not leave the path uncovered.

- [ ] **Step 13A — Full regression.** Run `python -m pytest skills/external-review/tests -q` and `python -m pytest tools/tasktool/tests -q`; confirm green. Update the slice's plan/tracker and proceed to close per `subagent-driven-development`. Ask the user about a version bump before committing (CLAUDE.md release policy), since this changes shipped code under `skills/`.

### Branch B — DOES-NOT-REPRODUCE (the expected outcome per the code read)

- [ ] **Step 11B — Make no source change.** Do not edit `external-reviewer.py`. Do not add a renaming "fix."

- [ ] **Step 12B — Write the phase-archive note** to `/tmp/p7s8/decision.md` (to be folded into the P7 phase archive note at phase close by the closing session). Content, concretely:
  > **P7.S8 — reviewer-artifact collision: investigated, dropped.** The P20 report (spec §1.4) claimed generated reviewer-request files add/add-conflict between sibling worktrees. Reproduction against the current bridge (`skills/external-review/scripts/external-reviewer.py`) refutes this for the normal workflow: `chain_folder_name` (:727) keys the post-slice/post-phase chain folder by `work_id` (`feature-plan-P2-S3-post-slice` vs `…-P2-S4-post-slice`), request basenames are round/role-unique (:1403), and `--work-id` is mandatory for post-slice/post-phase (:2439) with a mismatch-refusal guard (:2510) preventing accidental folder sharing. The simulation in Step 8 produced `COLLISION: False` for distinct sibling work-ids [paste exact output]. The only path that can still collide (Step 9.1) requires two siblings to run with the *identical* work-id from same-minute starts — an operator error the work-id keying is specifically designed to prevent, not a defect in the naming scheme. The P20 conflict on "reviewer artifacts" is therefore attributable to either an older bridge or to Class B below. **S8 is dropped with no code change.**
  >
  > **Residual: `docs/tasklist.json` reviewer-chain close-churn (Class B).** Real but out of scope for S8. `tools/tasktool/artifacts.py register` (~:151) stamps `reviewer_chain`/`phase_reviewer_chain` onto the slice/phase row; two siblings closing near-simultaneously both rewrite `docs/tasklist.json` and conflict at the line level. This is ordinary tasklist close-churn, **not** a request-file-naming problem, and is owned by the integrate-current-main checkpoint (P7.S6 / spec §4.F), which has each slice integrate current `main` before its post-slice review/merge, serializing the tasklist rewrite. No reviewer-artifact change addresses it.

- [ ] **Step 13B — Cancel the slice (do not close it).** Branch B ships no code, so `done` would be a lie and `tasktool close` would run the post-slice review gate against work that never shipped. Per `tasklist-discipline` (status enum: `cancelled` is the terminal status for intentionally-unshipped work; `done`/`close` is gated), the sanctioned drop path is `cancel`, which bypasses the post-slice gate. First preserve the decision artifact in the repo so the cancellation reason can point at it, then cancel:
  ```sh
  # 1. Persist the investigation findings inside the repo (not just /tmp), so the
  #    decision survives and the P7 phase archive can fold it in at phase close.
  mkdir -p docs/notes
  cp /tmp/p7s8/decision.md docs/notes/2026-06-02-P7-S8-reviewer-artifact-investigation-decision.md

  # 2. Cancel the slice, citing the persisted artifact. cancel bypasses the
  #    post-slice review gate (nothing shipped) and records the reason in notes.
  tasktool cancel P7.S8 --reason "investigation: reviewer-artifact add/add collision does not reproduce against the current bridge (work-id-keyed chain folders); residual docs/tasklist.json close-churn is owned by P7.S6 integrate-current-main, not by reviewer-artifact naming. See docs/notes/2026-06-02-P7-S8-reviewer-artifact-investigation-decision.md"
  ```
  No version bump is required (no shipped-code change). The persisted note at `docs/notes/2026-06-02-P7-S8-reviewer-artifact-investigation-decision.md` is the durable decision artifact; ensure its substance reaches the P7 phase archive note at phase close (the closing session folds it into the archive). A cancelled P7.S8 does not satisfy any downstream `depends_on` — confirm nothing in P7 depends on S8 (spec §5: S8 has no dependents) so no `schedule` `cancelled_deps` cleanup is needed.

---

## Decision gate

Run after Steps 8–9. Verdict is exactly one of two values; pick by these crisp criteria.

**REPRODUCES** — choose Branch A only if **all** hold:
1. The simulation produced at least one *identical relative path* under `docs/reviewer/.../*-request.md` written by two distinct sibling invocations (`COLLISION: True` in any of Steps 8, 9.1, 9.2), **and**
2. that colliding invocation pattern is **reachable in the documented workflow** — i.e. it does not require an operator to violate the work-id contract (each slice must pass its own slice ID as `--work-id`). A collision that only occurs when two *different* slices deliberately pass the *same* `--work-id`, or two distinct slices run independent `post-phase` reviews on the same file, counts as reachable only if Step 9 found the workflow actually does this. If it requires misuse, treat the uniqueness hardening (Step 11A) as a cheap defensive win **only if** the user wants it; otherwise it is Branch B.

**DOES-NOT-REPRODUCE** — choose Branch B if:
- Step 8 shows `COLLISION: False` for distinct sibling work-ids (the expected result), **and**
- the only collisions found in Step 9 require identical work-ids across siblings or duplicate post-phase reviews that the workflow does not actually produce.

In the DOES-NOT-REPRODUCE case the slice closes with **no source edit** and the archive note from Step 12B. That is a complete, successful outcome for an investigation slice — the deliverable was the decision, and the decision is "the current bridge already prevents this; the residual conflict is Class B, owned by P7.S6."
