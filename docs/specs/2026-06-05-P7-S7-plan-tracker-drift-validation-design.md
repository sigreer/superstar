# P7.S7 — Plan ↔ tracker drift validation

**Status:** design (spec)
**Date:** 2026-06-05
**Slice ID:** `P7.S7`
**Parent phase:** [`P7 — Integration-surface-aware parallel slice safety`](2026-06-02-P7-integration-surface-parallel-safety-design.md)
**Implements:** P7 spec §4.G ("Plan ↔ tracker drift enforcement").
**Depends on:** P7.S1 (the `integration_surfaces`/`reservations`/`coordination_group` fields exist), P7.S6 (the skills now tell planners to emit a surface/reservation table in each plan, so there is something to check against).

## 1. Problem

P7 added a per-slice integration-surface model to the tracker: a slice declares the
shared write `integration_surfaces` it mutates, the scarce `reservations` it
allocates, and an optional `coordination_group` (P7.S1 data model, P7.S2 CLI). The
workflow skills (P7.S6) now instruct planners to **emit a surface/reservation table
in each slice plan** and to declare the same facts on the tracker before ratifying a
parallel group.

Nothing keeps those two records honest. A planner can:

- declare `integration_surfaces` / `reservations` on the tracker (`tasktool surface
  add` / `tasktool reserve add`) but never mention them in the plan document, or
  amend the tracker after the plan was written — so the plan silently understates
  what the slice writes; or
- place a slice in a `parallel_group` (asserting it is independently mergeable) while
  declaring **no** surfaces at all — the exact "we never thought about write surface"
  omission that produced the `multistore` P20 conflict-bomb the whole phase exists to
  prevent.

The plan and the tracker are the two artifacts a coordinator reads when deciding
whether slices may run in parallel. When they disagree, the safety the rest of P7
provides is undermined: `surface check` reasons over the tracker, humans reason over
the plan, and a gap between them reintroduces the original failure mode.

## 2. Goals

1. **Catch tracker→plan drift.** When a slice declares a surface or reservation on
   the tracker that does **not** appear anywhere in its plan document, surface it as
   a non-fatal `tasktool validate` warning so the planner reconciles the two.
2. **Catch the "forgot entirely" omission.** When a non-terminal slice sits in a
   `parallel_group` but declares **no** `integration_surfaces`, nudge the planner to
   declare them (or drop the parallel grouping) — the spec's documented minimum bar
   (P7 spec §4.G).
3. **Stay non-fatal and opt-in.** No new refusals, no exit-code changes, no model or
   schema change. Projects that declare nothing behave exactly as today. Warnings
   flow through the existing `tasktool validate` text/JSON `warnings` channel.
4. **Be robust to plan format.** The detection must not depend on parsing a
   rigidly-structured markdown table, because P7.S6 specifies the surface/reservation
   table only loosely (no fixed headers or column order). A lenient "is this value
   mentioned in the plan at all?" check is deliberately preferred over a brittle
   table parser.

## 3. Non-goals (explicit)

- **Strict markdown-table parsing.** Extracting per-slice rows/cells from the plan's
  surface/reservation table and diffing each cell is explicitly **not** built. The
  P7 spec (§3, §4.G) already rules path-glob/structured *inference* out as the
  planning model and authorizes a lenient minimum bar where table parsing "is too
  brittle for this phase." S7 honours that: it does a substring presence check, not a
  table parse.
- **Reverse-direction drift (plan declares, tracker missing).** Detecting a surface
  that a plan's table lists but the tracker does not carry requires actually parsing
  the plan to know what it *declares* versus merely *mentions*. That is deferred to a
  future slice (recorded in §7), because it cannot be done without the brittle parser
  this slice intentionally avoids.
- **Blocking / refusal.** Drift is a warning, never an error. `tasktool validate`
  exit code is unchanged by these checks (it remains driven by structural validation
  errors only). This mirrors `find_path_warnings`, which is also non-fatal.
- **Checking terminal slices.** `done`/`cancelled` slices shipped (or abandoned)
  whatever they declared; re-litigating their plans adds only noise. Both checks
  consider non-terminal slices only.
- **New CLI surface.** No new subcommand. The checks ride the existing `tasktool
  validate` command. `artifact status --strict` is intentionally left untouched so
  the drift logic lives in exactly one place.
- **Skill edits.** P7.S6 owns the plan-table convention and the planner-facing
  guidance. S7 is pure tooling (`validate.py`); it adds no skill prose.

## 4. Design

All behaviour lives in `tools/tasktool/validate.py` and its wiring in
`tools/tasktool/commands.py`. No `model.py`, `serialize.py`, or `migrate.py` change;
no schema bump.

### 4.A New function: `find_surface_drift_warnings`

Add a module-level function mirroring the existing `find_path_warnings` shape (same
file, same return contract — a list of human-readable warning strings, never
raising):

```python
def find_surface_drift_warnings(
    p: Project, repo_root: Path, *, include_plan_checks: bool
) -> list[str]:
    """Return non-fatal warnings where a slice's tracker-declared integration
    surfaces / reservations are not reflected in its plan, or where a slice in a
    parallel_group declares no surfaces at all. Mirrors find_path_warnings: pure,
    non-raising, returns [] when clean. `include_plan_checks` gates the file-reading
    half (Check 2, §4.C); Check 1 (§4.B) runs regardless. See §4.D for the flag's
    binding contract."""
```

It walks every phase's slices, skipping terminal slices (`is_terminal(s.status)`),
and applies the two checks below. Warning strings are scoped `P{ph}.{S}` to match the
existing warning style (e.g. `P7.S3.surfaces: ...`).

### 4.B Check 1 — no-surface-in-parallel-group nudge (pure, no file I/O)

For each **non-terminal** slice with `s.parallel_group is not None` and
`s.integration_surfaces == []`:

```
P7.S5: in parallel_group 'core' but declares no integration_surfaces —
  declare them with `tasktool surface add P7.S5 <surface>` or remove it from the parallel group
```

Rationale: a slice that asserts parallel-independence (`parallel_group`) without
naming a single write surface is the "we forgot to think about merge safety" smell.
This is the spec's documented minimum bar and requires no plan file, so it always
runs (it is not gated by `--no-path-warnings`; see §4.D). The check keys on
`integration_surfaces` only — absence of a `reservation` is not a smell (most slices
allocate no scarce resource), so reservations do not trigger this nudge.

### 4.C Check 2 — tracker-surface-absent-from-plan drift (lenient parse)

For each **non-terminal** slice that has a `plan_path`, where that plan file **exists
on disk**, and that declares ≥1 surface or reservation: read the plan text once
(UTF-8), lowercase it, and for each declared item check substring presence
(case-insensitive):

- for each `surface` in `s.integration_surfaces`: warn if `surface.lower()` is not a
  substring of the plan text:

  ```
  P7.S3.surfaces: tracker declares surface 'commands' but it does not appear in
    plan docs/plans/2026-06-04-P7-S3-scheduling-overlap-detection.md (plan may be stale)
  ```

- for each `reservation` in `s.reservations`: form the token `f"{resource}:{value}"`
  and warn if that token (lowercased) is not a substring of the plan text:

  ```
  P7.S5.reservations: tracker declares reservation 'homepage-sort:15' but it does
    not appear in plan docs/plans/...md (plan may be stale)
  ```

Skip conditions (no warning, no crash):

- `plan_path is None` → the slice has no plan to check; skip Check 2 for it.
- `plan_path` set but the file does not exist on disk → **skip** (do not emit a Check 2
  warning). The missing file is already reported by the existing
  `find_path_warnings` (`{scope}.plan_path: path does not exist`); S7 must not
  double-warn. A read error (e.g. permissions) is likewise swallowed to a skip — this
  is a best-effort nudge, not a gate.
- slice declares no surfaces and no reservations → nothing to check.

The substring bar is deliberately loose: the value need only be **mentioned
somewhere** in the plan (a table cell, a prose sentence, a code fence). The goal is
"did the planner account for this surface at all?", not "is the table perfectly
formatted." False negatives (the plan mentions the surface only in unrelated prose)
are an accepted cost of avoiding the brittle table parser §3 rejects.

### 4.D Wiring in `commands.py`

In `_cmd_validate_at_root`, alongside the existing `find_path_warnings` call. The new
function takes one flag, `include_plan_checks`, that gates the file-reading half:

```python
if project is not None and not errors:
    # Check 1 always runs; Check 2 (reads plan files) only when plan files are present.
    warnings.extend(
        find_surface_drift_warnings(
            project, repo_root, include_plan_checks=not no_path_warnings
        )
    )
    if not no_path_warnings:
        warnings.extend(find_path_warnings(project, repo_root))
```

Behaviour contract:

- **Check 1** (no file I/O) runs **always** — it is safe in any context, so
  `find_surface_drift_warnings` emits it regardless of `include_plan_checks`.
- **Check 2** (reads plan files) runs **only** when `include_plan_checks` is true,
  i.e. `not no_path_warnings`. The pre-commit hook passes `--no-path-warnings` because
  it validates a **sandboxed copy** of `docs/tasklist.json` whose referenced plan
  files are not present in the sandbox; running Check 2 there would emit false "does
  not appear in plan" warnings for every declared surface. Gating Check 2 on the same
  flag as `find_path_warnings` keeps the two file-dependent checks consistent.

The binding signature is `find_surface_drift_warnings(p: Project, repo_root: Path, *,
include_plan_checks: bool) -> list[str]`, matching the §4.A sketch.

Warnings are appended to the same `warnings` list the command already builds, so they
appear in both the text output (`warning: <msg>`) and the JSON output
(`{"warnings": [...]}`), and they **do not** change `rc` (which stays driven by
`errors`).

### 4.E What does *not* change

- No `model.py` / `serialize.py` / `migrate.py` edit; no schema version bump.
- No new CLI subcommand or flag (`validate` already has `--format`, `--strict-format`,
  `--normalise`, `--check-orphans`, `--no-path-warnings`).
- `validate_project` (the structural, *raising* validator) is untouched — drift is a
  warning channel, not a structural rule, exactly like `find_path_warnings`.
- `artifact status --strict` is untouched.

## 5. Testing strategy

All in `tools/tasktool/tests/test_validate.py`, following the existing fixture style
(construct `Project`/`Phase`/`Slice` objects or load a temp `tasklist.json`, write
plan files under a `tmp_path` repo root).

**Check 1 (no-surface-in-parallel-group):**

- non-terminal slice with `parallel_group="core"` and empty `integration_surfaces` →
  warning present, naming the slice and group;
- same slice but with ≥1 surface → no Check 1 warning;
- non-terminal slice with **no** `parallel_group` and no surfaces → no warning
  (only parallel-group slices are nudged);
- **terminal** (`done`) slice in a parallel group with no surfaces → no warning;
- Check 1 fires even when `no_path_warnings=True` (it is not gated).

**Check 2 (tracker-surface-absent-from-plan):**

- slice with `plan_path` whose file **contains** the declared surface text → no
  warning;
- slice whose plan file **omits** a declared surface → warning naming slice, surface,
  and plan path;
- slice whose plan file omits a declared reservation `resource:value` token → warning;
- case-insensitive match: surface declared `CMS-Block-Registry`, plan contains
  `cms-block-registry` → no warning;
- slice with `plan_path is None` → no Check 2 warning, no crash;
- slice with a `plan_path` that does not exist on disk → no Check 2 warning (and the
  existing path-warning still fires from `find_path_warnings`), no crash;
- slice whose plan file is unreadable / non-UTF-8 (decode error) → no Check 2 warning,
  no crash (the read error is swallowed to a skip per §4.C);
- Check 2 is **suppressed** when `no_path_warnings=True`.

**Integration through `cmd_validate`:**

- a project exercising both checks yields the warnings in the JSON `warnings` array
  with `ok: true` / `rc == 0` (drift never fails validation);
- the pre-commit path (`--no-path-warnings`) yields Check 1 warnings only, no Check 2
  warnings.

## 6. Rollout & compatibility

- No migration, no schema bump, no model change — purely additive validation logic.
- All new output is non-fatal warnings on an existing command; no caller's exit code
  changes.
- Projects that declare no surfaces/reservations and use no `parallel_group` see no
  new output. The check is effectively opt-in via the P7 declaration model.
- Version bump / plugin re-sync handled at phase close per the repo release policy,
  not during this slice.

## 7. Deferred / future (recorded, not built)

- **Reverse-direction drift** (plan's table lists a surface the tracker lacks): needs
  a real table parser to distinguish "declared in plan" from "mentioned in prose";
  deferred until/if the loose-table convention is tightened into a parseable format.
- **Structured table extraction**: if a future slice fixes the surface/reservation
  table to a canonical column layout, Check 2 could be upgraded from substring
  presence to per-cell equality, enabling exact bidirectional diffs. Out of scope here.
- **`artifact status --strict` integration**: surfacing drift at artifact-commit time
  as well as at `validate` time, if the single-command placement proves insufficient.
