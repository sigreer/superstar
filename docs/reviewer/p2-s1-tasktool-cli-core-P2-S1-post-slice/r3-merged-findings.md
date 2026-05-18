# Merged findings for r3

## Primary

# Review — 2026-05-17-p2-s1-tasktool-cli-core.md (post-slice, round 3)

- Target: `docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md`
- Request: `docs/reviewer/p2-s1-tasktool-cli-core-P2-S1-post-slice/r3-2026-05-18T1112-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

**Findings**

F1 — RESOLVED — Relative `--reviewer-chain` paths now resolve against `repo_root` before validation in `tools/tasktool/reviewer_gate.py:28-34`, with CLI regression coverage in `tools/tasktool/tests/test_cli_integration.py:191`.

F2 — RESOLVED — Chain discovery now uses hyphen-bounded token matching in `tools/tasktool/reviewer_gate.py:20-23` and applies it after stripping the `-post-slice` suffix at `tools/tasktool/reviewer_gate.py:39-42`. Regression tests cover `p1-s1` vs `p1-s10`.

F3 — RESOLVED — `tasktool set --status blocked` is no longer accepted by argparse; choices are now `ready`, `in_progress`, `done` in `tools/tasktool/cli.py:50-53`, with clean-error regression coverage.

F4 — RESOLVED — The plan now includes post-implementation evidence at `docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:3130-3138`, including 131 passing tests and deferred S2/S3 scope.

**Open Questions / Assumptions**

No remaining questions. The only dirty worktree item I saw was the current r3 reviewer request file, which is expected review-chain output.

**Suggested Document Edits**

None.

**Verification**

Ran:

`PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`  
Result: 131 tests passed.

Also ran `bash -n tools/tasktool/install.sh` and schema JSON validation successfully.

**Overall verdict: ready**
**Findings**

F1 — RESOLVED — Relative `--reviewer-chain` paths now resolve against `repo_root` before validation in `tools/tasktool/reviewer_gate.py:28-34`, with CLI regression coverage in `tools/tasktool/tests/test_cli_integration.py:191`.

F2 — RESOLVED — Chain discovery now uses hyphen-bounded token matching in `tools/tasktool/reviewer_gate.py:20-23` and applies it after stripping the `-post-slice` suffix at `tools/tasktool/reviewer_gate.py:39-42`. Regression tests cover `p1-s1` vs `p1-s10`.

F3 — RESOLVED — `tasktool set --status blocked` is no longer accepted by argparse; choices are now `ready`, `in_progress`, `done` in `tools/tasktool/cli.py:50-53`, with clean-error regression coverage.

F4 — RESOLVED — The plan now includes post-implementation evidence at `docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:3130-3138`, including 131 passing tests and deferred S2/S3 scope.

**Open Questions / Assumptions**

No remaining questions. The only dirty worktree item I saw was the current r3 reviewer request file, which is expected review-chain output.

**Suggested Document Edits**

None.

**Verification**

Ran:

`PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`  
Result: 131 tests passed.

Also ran `bash -n tools/tasktool/install.sh` and schema JSON validation successfully.

**Overall verdict: ready**

---

## Reviewer stderr (tail)

```text
        root = Path(td)
   110	            _write_chain(root, "p1-s1-post-slice", "ready")
   111	            correct = _write_chain(root, "p1-s10-post-slice", "ready")
   112	            found = discover_chain(root, "P1.S10", "post-slice")
   113	            self.assertEqual(found, correct)
   114	
   115	    def test_p1_s1_prefix_only_no_false_ambiguity(self):
   116	        """p1-s1 and p1-s10 both exist; P1.S1 must resolve to exactly one."""
   117	        with tempfile.TemporaryDirectory() as td:
   118	            root = Path(td)
   119	            _write_chain(root, "p1-s1-post-slice", "ready")
   120	            _write_chain(root, "p1-s10-post-slice", "ready")

codex
**Findings**

F1 — RESOLVED — Relative `--reviewer-chain` paths now resolve against `repo_root` before validation in `tools/tasktool/reviewer_gate.py:28-34`, with CLI regression coverage in `tools/tasktool/tests/test_cli_integration.py:191`.

F2 — RESOLVED — Chain discovery now uses hyphen-bounded token matching in `tools/tasktool/reviewer_gate.py:20-23` and applies it after stripping the `-post-slice` suffix at `tools/tasktool/reviewer_gate.py:39-42`. Regression tests cover `p1-s1` vs `p1-s10`.

F3 — RESOLVED — `tasktool set --status blocked` is no longer accepted by argparse; choices are now `ready`, `in_progress`, `done` in `tools/tasktool/cli.py:50-53`, with clean-error regression coverage.

F4 — RESOLVED — The plan now includes post-implementation evidence at `docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:3130-3138`, including 131 passing tests and deferred S2/S3 scope.

**Open Questions / Assumptions**

No remaining questions. The only dirty worktree item I saw was the current r3 reviewer request file, which is expected review-chain output.

**Suggested Document Edits**

None.

**Verification**

Ran:

`PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`  
Result: 131 tests passed.

Also ran `bash -n tools/tasktool/install.sh` and schema JSON validation successfully.

**Overall verdict: ready**
tokens used
90,852
```


## Sweep 1

# Review — 2026-05-17-p2-s1-tasktool-cli-core.md (post-slice, round 3)

- Target: `docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md`
- Request: `docs/reviewer/p2-s1-tasktool-cli-core-P2-S1-post-slice/r3-2026-05-18T1112-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

S1.F1. Severity: important — Orphan-aware allocation misses existing lowercase plan/reviewer IDs, so it can reallocate IDs that already exist in this repo’s artifact names. [allocate.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/allocate.py:7) uses case-sensitive `P/S/T/X` regexes, while current artifacts include lowercase names like `docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md` and reviewer folders. A quick repro with lowercase `p2-s1` / `p2-s3` artifacts returned no slice orphans and allocated `S1`. This conflicts with the slice’s orphan-aware allocation goal in [the plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:26) and with existing TASKLIST P2 slices in [TASKLIST.md](/home/simon/Dev/sigreer/skills/superstar/docs/TASKLIST.md:52). Fix by scanning case-insensitively and adding lowercase artifact regression tests.

S1.F2. Severity: important — The emitted schema accepts `blocked` for phases, tasks, and cross-cutting items even though the spec says only slices may be blocked. [schema_gen.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/schema_gen.py:8), [schema_gen.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/schema_gen.py:32), [schema_gen.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/schema_gen.py:64), and [schema_gen.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/schema_gen.py:81) reuse the full status enum everywhere. The spec explicitly makes blocking slice-scoped in [2026-05-17-P2-tasktool-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:156), and downstream tools are expected to validate JSON against `tasktool schema` in [2026-05-17-P2-tasktool-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:61). Tighten schema enums per item kind, or document that schema is intentionally looser than validator.

S1.F3. Severity: minor — The package public API promised by the plan/spec is not exposed. [__init__.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/__init__.py:1) only defines `__version__`, while the plan calls it the public API surface in [the plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:19), and the spec says consumers can `import tasktool` and use functions like `load_project` in [the spec](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:60). Export at least `load_project`, `save_project`, and model types now; leave `brief` deferred if intended.

2. Open questions / assumptions

I’m treating lowercase artifact names as in-scope because this repo already uses them for P2/S1 plan and reviewer paths. I’m also treating schema correctness as in-scope because `tasktool schema` shipped in S1.

3. Suggested document edits

Update the post-implementation evidence to mention any new fix commits and add explicit notes for the public API status: either “exported in S1” or “deferred to S2,” matching the actual code.

4. Verification gaps / commands

Already run and passing:

`PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`

Result: 131 tests pass.

Add targeted tests for lowercase orphan scanning and schema status enums before closing.

5. Overall verdict

revise
1. Findings

S1.F1. Severity: important — Orphan-aware allocation misses existing lowercase plan/reviewer IDs, so it can reallocate IDs that already exist in this repo’s artifact names. [allocate.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/allocate.py:7) uses case-sensitive `P/S/T/X` regexes, while current artifacts include lowercase names like `docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md` and reviewer folders. A quick repro with lowercase `p2-s1` / `p2-s3` artifacts returned no slice orphans and allocated `S1`. This conflicts with the slice’s orphan-aware allocation goal in [the plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:26) and with existing TASKLIST P2 slices in [TASKLIST.md](/home/simon/Dev/sigreer/skills/superstar/docs/TASKLIST.md:52). Fix by scanning case-insensitively and adding lowercase artifact regression tests.

S1.F2. Severity: important — The emitted schema accepts `blocked` for phases, tasks, and cross-cutting items even though the spec says only slices may be blocked. [schema_gen.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/schema_gen.py:8), [schema_gen.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/schema_gen.py:32), [schema_gen.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/schema_gen.py:64), and [schema_gen.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/schema_gen.py:81) reuse the full status enum everywhere. The spec explicitly makes blocking slice-scoped in [2026-05-17-P2-tasktool-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:156), and downstream tools are expected to validate JSON against `tasktool schema` in [2026-05-17-P2-tasktool-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:61). Tighten schema enums per item kind, or document that schema is intentionally looser than validator.

S1.F3. Severity: minor — The package public API promised by the plan/spec is not exposed. [__init__.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/__init__.py:1) only defines `__version__`, while the plan calls it the public API surface in [the plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:19), and the spec says consumers can `import tasktool` and use functions like `load_project` in [the spec](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:60). Export at least `load_project`, `save_project`, and model types now; leave `brief` deferred if intended.

2. Open questions / assumptions

I’m treating lowercase artifact names as in-scope because this repo already uses them for P2/S1 plan and reviewer paths. I’m also treating schema correctness as in-scope because `tasktool schema` shipped in S1.

3. Suggested document edits

Update the post-implementation evidence to mention any new fix commits and add explicit notes for the public API status: either “exported in S1” or “deferred to S2,” matching the actual code.

4. Verification gaps / commands

Already run and passing:

`PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`

Result: 131 tests pass.

Add targeted tests for lowercase orphan scanning and schema status enums before closing.

5. Overall verdict

revise

---

## Reviewer stderr (tail)

```text
ema_gen.py:64), and [schema_gen.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/schema_gen.py:81) reuse the full status enum everywhere. The spec explicitly makes blocking slice-scoped in [2026-05-17-P2-tasktool-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:156), and downstream tools are expected to validate JSON against `tasktool schema` in [2026-05-17-P2-tasktool-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:61). Tighten schema enums per item kind, or document that schema is intentionally looser than validator.

S1.F3. Severity: minor — The package public API promised by the plan/spec is not exposed. [__init__.py](/home/simon/Dev/sigreer/skills/superstar/tools/tasktool/__init__.py:1) only defines `__version__`, while the plan calls it the public API surface in [the plan](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:19), and the spec says consumers can `import tasktool` and use functions like `load_project` in [the spec](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:60). Export at least `load_project`, `save_project`, and model types now; leave `brief` deferred if intended.

2. Open questions / assumptions

I’m treating lowercase artifact names as in-scope because this repo already uses them for P2/S1 plan and reviewer paths. I’m also treating schema correctness as in-scope because `tasktool schema` shipped in S1.

3. Suggested document edits

Update the post-implementation evidence to mention any new fix commits and add explicit notes for the public API status: either “exported in S1” or “deferred to S2,” matching the actual code.

4. Verification gaps / commands

Already run and passing:

`PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`

Result: 131 tests pass.

Add targeted tests for lowercase orphan scanning and schema status enums before closing.

5. Overall verdict

revise
tokens used
61,542
```

