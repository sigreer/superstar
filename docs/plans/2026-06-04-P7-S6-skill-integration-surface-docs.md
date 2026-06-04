# P7.S6 — Skill changes for integration-surface-aware parallel safety: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach the workflow skills the integration-surface model shipped in P7.S2–S4 so coordinators declare surfaces/reservations, run `surface check` before parallel dispatch, and integrate current `main` before each post-slice review.

**Architecture:** Pure documentation slice. It edits four `SKILL.md` files and adds one reference file, and is guarded by string-assertion tests in the existing docs-lifecycle test (`tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`). No tasktool Python behaviour changes — the CLI surface (`surface`/`reserve`/`coordinate`/`surface check`/`worktree status --integration`) already exists. TDD here means: add a failing doc-content assertion, run it red, edit the skill prose to make it green, commit.

**Tech Stack:** Markdown skill files under `skills/`; pytest doc-content assertions under `tools/tasktool/tests/`.

---

## Spec reference

This slice implements **§4.F** of the P7 spec (`docs/specs/2026-06-02-P7-integration-surface-parallel-safety-design.md`) and its testing line in **§6 (`S6`)**: *"docs lifecycle test extended to assert the new commands and the integrate-main checkpoint are documented; playbook file exists."*

§4.F deliverables:
- **`subagent-driven-development`** — (1) run `tasktool surface check <phase-id>` after `ready-slices` and do not parallel-dispatch surface-sharing slices without a `depends_on` or `coordination_group`; (2) an *integrate-current-main* checkpoint before `external-review --kind post-slice`; (3) a new `references/registry-merge-playbook.md`.
- **`tasklist-discipline`** — document `surface`/`reserve`/`coordinate` in the conceptual model and daily-commands list; the recommended surface vocabulary; the `coordination_group` vs `parallel_group` distinction; three new red-flag rows.
- **`phase-planning` / `writing-plans`** — declare surfaces/reservations when proposing parallel groups, emit a **surface/reservation table** in the plan, and run `tasktool surface check <phase-id>` before ratifying parallel groups.

## Scheduling contract (confirmed before drafting)

- `tasktool show P7.S6`: status `ready`, `depends_on = [P7.S2, P7.S3, P7.S4]` (all `done`), no `parallel_group`, `planning_status = proposed`.
- `tasktool ready-slices P7` lists `P7.S6` as ready.
- No dependency change is needed. This plan **does not** depend on P7.S5 (`worktree sync`); the integrate-current-main checkpoint therefore documents `worktree sync` as the preferred path *when available* plus a raw-git fallback, exactly as §4.F specifies.
- The slice is ratified at **plan-settle** — in this planning session, immediately after the plan review passes — with `tasktool ratify P7.S6` (keeps `depends_on = [P7.S2, P7.S3, P7.S4]`, adds no parallel group). Execution does **not** re-ratify; by the time Task 0 runs, `planning_status` is already `ratified` and committed.

## File Structure

| File | Responsibility | Action |
|------|----------------|--------|
| `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` | Doc-content regression for all workflow skills | **Modify** — add 5 assertion functions |
| `skills/subagent-driven-development/references/registry-merge-playbook.md` | Centralized-registry merge recipe referenced from the integrate-main checkpoint | **Create** |
| `skills/subagent-driven-development/SKILL.md` | Coordinator orchestration loop | **Modify** — surface check before dispatch, integrate-main checkpoint, playbook reference |
| `skills/tasklist-discipline/SKILL.md` | tasktool CLI surface + conceptual model | **Modify** — conceptual model paragraph, daily-commands block, 3 red-flag rows |
| `skills/phase-planning/SKILL.md` | Phase shaping + scheduling graph | **Modify** — declaration step, surface/reservation table requirement, red flag |
| `skills/writing-plans/SKILL.md` | Slice plan authoring | **Modify** — surface/reservation table requirement in scheduling ratification |

The five test functions are split one-per-skill-area so each implementation task has a dedicated red→green pair.

---

## Task 0: Start the slice

**Files:**
- No source changes; lifecycle only.

This is the mandatory first execution step from `[[writing-plans]]`: record the slice lifecycle start (and the worktree base SHA) before editing any files. The row is already `ratified` from the planning session — Task 0 only moves it to `in_progress`.

- [ ] **Step 1: Verify you are in the slice's isolated worktree**

Run: `git status --short`
Expected: a clean tree (no unrelated dirty files). If this is a shared `main`/`master` checkout and the human partner has not opted out of isolation, stop and create the slice worktree via `[[using-git-worktrees]]` first.

- [ ] **Step 2: Start the slice**

Run: `tasktool start P7.S6`
Expected: the row moves to `in_progress` and the worktree base SHA is recorded.

- [ ] **Step 3: Confirm the lifecycle state**

Run: `tasktool show P7.S6`
Expected: `status: in_progress`, `planning_status: ratified`, `depends_on: P7.S2, P7.S3, P7.S4`.

---

## Task 1: Registry merge playbook reference file

**Files:**
- Create: `skills/subagent-driven-development/references/registry-merge-playbook.md`
- Test: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`

- [ ] **Step 1: Write the failing test**

Append to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:

```python
def test_registry_merge_playbook_exists() -> None:
    playbook = (
        ROOT
        / "skills"
        / "subagent-driven-development"
        / "references"
        / "registry-merge-playbook.md"
    )
    assert playbook.is_file(), f"registry merge playbook must exist at {playbook}"
    body = playbook.read_text(encoding="utf-8")
    # The playbook's load-bearing instructions.
    assert "preserve both" in body.lower()
    assert "regenerate" in body.lower()
    assert "rerun" in body.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py::test_registry_merge_playbook_exists -q`
Expected: FAIL — `AssertionError: registry merge playbook must exist at …` (file does not exist yet).

- [ ] **Step 3: Create the playbook file**

Create `skills/subagent-driven-development/references/registry-merge-playbook.md` with this exact content:

```markdown
# Centralized-registry merge playbook

Use this when a slice's worktree must integrate the current base branch and a
**coordinated sibling slice has already landed on a shared integration surface**
— a central registry, a parser allowlist/union, a schema or seed file, a renderer
dispatch table, a theme CSS tail, or a homepage/ordering array. These surfaces
collect *additive* entries from multiple slices, so a textual merge that keeps
only one side silently drops a sibling's feature.

This is invoked from the **integrate-current-main checkpoint** in
`[[subagent-driven-development]]`, before the post-slice external review.

## Rule: preserve both semantic additions

When base and your worktree both added to the same registry/array/union, the
merge result must contain **both** additions, not whichever side won the textual
conflict. Read both sides and reconstruct the union by hand:

1. **Identify the surface and the additions.** For each conflicting hunk, name
   what each side added (a block contract, a parser case, a schema/seed row, a
   dispatch entry, a CSS block, an ordering slot).
2. **Keep both additions.** Reassemble the registry/array/union so every sibling's
   entry survives. If two siblings added entries that must be ordered, apply the
   declared ordering; if they collide on a scarce slot (e.g. two `homepage-sort:15`),
   that is a reservation collision that should have been caught by `tasktool reserve
   add` — resolve it now by moving one side to a free value and recording why.
3. **Do not invent a merge the tool can do.** This playbook resolves *semantic*
   additive conflicts only. It does not auto-resolve genuine logic conflicts —
   escalate those.

## Rule: regenerate derived artifacts

Any file derived from the surface must be regenerated *after* the union is
correct, never hand-merged:

- checksums / lockfiles / content hashes,
- snapshot fixtures,
- generated types or generated indexes.

A hand-merged checksum is a lie; regenerate it from the merged source.

## Rule: rerun focused tests, then integrated verification

1. Rerun the **focused** parser / schema / seed tests for the surface you merged.
2. Then rerun the slice's **full** verification command, so the integrated tree
   (your work + the landed sibling) is proven green before the post-slice review.

If any focused test fails, the union was reconstructed wrong — return to "preserve
both semantic additions" before rerunning the full suite.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py::test_registry_merge_playbook_exists -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/references/registry-merge-playbook.md \
        tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
git commit -m "P7.S6: add centralized-registry merge playbook reference"
```

---

## Task 2: subagent-driven-development — surface check, integrate-main checkpoint, playbook reference

**Files:**
- Modify: `skills/subagent-driven-development/SKILL.md`
- Test: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`

- [ ] **Step 1: Write the failing test**

Append to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:

```python
def test_subagent_driven_development_runs_surface_check_before_parallel_dispatch() -> None:
    text = skill_text("subagent-driven-development")
    assert "tasktool surface check <phase-id>" in text
    assert "Do not parallel-dispatch slices that share an integration surface" in text
    # surface check is described alongside ready-slices, before dispatch
    rs = text.index("tasktool ready-slices <phase-id>")
    sc = text.index("tasktool surface check <phase-id>")
    assert rs < sc, "surface check must be documented after ready-slices"


def test_subagent_driven_development_has_integrate_main_checkpoint() -> None:
    text = skill_text("subagent-driven-development")
    assert "tasktool worktree status <slice-id> --integration" in text
    assert "Integrate-current-main checkpoint" in text
    assert "references/registry-merge-playbook.md" in text
    # the checkpoint precedes the close gate in the slice-end sequence
    integ = text.index("tasktool worktree status <slice-id> --integration")
    close = text.index("tasktool close <slice-id>")
    assert integ < close, "integrate-main checkpoint must precede the close gate"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -k "surface_check_before_parallel_dispatch or integrate_main" -q`
Expected: FAIL — both assert the new strings are absent from the skill.

- [ ] **Step 3a: Add the surface-check paragraph before parallel dispatch**

In `skills/subagent-driven-development/SKILL.md`, find the paragraph that begins `Before dispatching implementation work for a phase, run` (currently line 41). **Immediately after** that paragraph (before the `Parallel slices must run in separate worktrees.` paragraph), insert this new paragraph:

```markdown
After `tasktool ready-slices <phase-id>`, run `tasktool surface check <phase-id>` before dispatching any slices in parallel. **Do not parallel-dispatch slices that share an integration surface without a declared `depends_on` or a shared `coordination_group`.** A shared write surface — a central registry, a schema/seed file, a renderer dispatch table, a parser union, a theme CSS tail, an ordering array — is what actually governs merge safety; feature independence does not. When `surface check` reports an unguarded `surface_overlap`, either **serialize** the slices (`tasktool deps <later-slice-id> --add <earlier-slice-id>`) or **coordinate** them (`tasktool coordinate <slice-id> --group <name>`, designate one slice as the integration owner, and plan to run the centralized-registry merge playbook at merge). Slices reported as `coordinated` may proceed in parallel; unguarded overlaps must be resolved first.
```

- [ ] **Step 3b: Add the integrate-current-main checkpoint to the slice-end sequence**

In the same file, find the `At the end of each slice` numbered list (currently lines 54–59). It currently reads:

```markdown
- **At the end of each slice** (all the slice's tasks closed, in-loop internal reviews passed):
  1. Run `git status --short`. If setup/migration artifacts, unrelated reviewer chains, legacy path moves, unrelated tasklist mutations, files from another slice, or other dirty files outside the slice scope are present, stop and resolve that boundary before review.
  2. Invoke `[[external-review]]` with `--kind post-slice`, passing the plan as `--file` and the spec + `docs/tasklist.json` as `--context`.
  3. Read the verdict. On `ready` / `ready with small edits`, proceed.
  4. On `merged_verdict: revise` (or `verdict_valid: false`), **dispatch a fix subagent** with the previous response file as input. The fix subagent MUST write `docs/reviewer/<chain>/r{N}-resolution.md` per the contract in `[[external-review]]` before signaling completion. Wait for completion. Re-submit. Iterate.
  5. Once the verdict gates pass, run `tasktool close <slice-id>` (the CLI re-checks the reviewer chain and refuses on `revise`). See `[[tasklist-discipline]]`.
```

Replace it with this (a new step 2 is inserted; the rest renumber to 3–6):

```markdown
- **At the end of each slice** (all the slice's tasks closed, in-loop internal reviews passed):
  1. Run `git status --short`. If setup/migration artifacts, unrelated reviewer chains, legacy path moves, unrelated tasklist mutations, files from another slice, or other dirty files outside the slice scope are present, stop and resolve that boundary before review.
  2. **Integrate-current-main checkpoint.** Run `tasktool worktree status <slice-id> --integration`. If a sibling slice has landed on the base branch since this slice's `worktree_base_sha` — especially one that shares an integration surface with this slice — integrate the current base branch into the worktree **before** the post-slice review: run `tasktool worktree sync <slice-id> --merge` (or `--rebase`) when that command is available, otherwise merge the base branch with raw git (`git merge <base-branch>`). Resolve any registry / schema / seed / ordering conflicts with the centralized-registry merge playbook (`references/registry-merge-playbook.md`), regenerate derived artifacts (checksums, snapshots), and rerun verification. Only then proceed. Skipping this replays already-integrated churn and produces stale-base merges. If `worktree status --integration` reports `landed: unknown` for a sibling, treat it as possibly-landed and inspect before proceeding.
  3. Invoke `[[external-review]]` with `--kind post-slice`, passing the plan as `--file` and the spec + `docs/tasklist.json` as `--context`.
  4. Read the verdict. On `ready` / `ready with small edits`, proceed.
  5. On `merged_verdict: revise` (or `verdict_valid: false`), **dispatch a fix subagent** with the previous response file as input. The fix subagent MUST write `docs/reviewer/<chain>/r{N}-resolution.md` per the contract in `[[external-review]]` before signaling completion. Wait for completion. Re-submit. Iterate.
  6. Once the verdict gates pass, run `tasktool close <slice-id>` (the CLI re-checks the reviewer chain and refuses on `revise`). See `[[tasklist-discipline]]`.
```

- [ ] **Step 3c: Add the integrate-main node to the process digraph**

In the same file, in the `digraph process` block, find this edge (currently line 145):

```dot
    "Last task in slice?" -> "Invoke external-review --kind post-slice" [label="yes"];
```

Replace it with a node insertion that routes through the checkpoint:

```dot
    "Integrate current main (worktree status --integration)" [shape=box];
    "Last task in slice?" -> "Integrate current main (worktree status --integration)" [label="yes"];
    "Integrate current main (worktree status --integration)" -> "Invoke external-review --kind post-slice";
```

- [ ] **Step 3d: Reference the playbook in a References section**

In the same file, find the `## Prompt Templates` section (currently lines 197–201). **Immediately after** that section's bullet list, insert:

```markdown
## References

- `./references/registry-merge-playbook.md` — how to merge centralized-registry / schema / seed / ordering conflicts when a coordinated sibling slice has landed before this slice's post-slice review: preserve **both** semantic additions, regenerate derived artifacts, rerun focused parser/schema/seed tests, then rerun integrated verification.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -k "surface_check_before_parallel_dispatch or integrate_main" -q`
Expected: PASS (2 passed).

Also confirm the pre-existing ordering test still holds:
Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py::test_subagent_driven_development_starts_slice_before_dispatch -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/subagent-driven-development/SKILL.md \
        tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
git commit -m "P7.S6: surface-check gate + integrate-current-main checkpoint in subagent-driven-development"
```

---

## Task 3: tasklist-discipline — surface/reserve/coordinate model, commands, red flags

**Files:**
- Modify: `skills/tasklist-discipline/SKILL.md`
- Test: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`

- [ ] **Step 1: Write the failing test**

Append to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:

```python
def test_tasklist_discipline_documents_surface_reserve_coordinate() -> None:
    text = skill_text("tasklist-discipline")
    # daily-commands surface
    assert "tasktool surface add <slice-id>" in text
    assert "tasktool surface check <phase-id>" in text
    assert "tasktool reserve add <slice-id>" in text
    assert "tasktool coordinate <slice-id> --group" in text
    # conceptual model + vocabulary
    assert "integration_surfaces" in text
    assert "reservations" in text
    assert "cms-block-registry" in text
    # coordination_group vs parallel_group distinction is spelled out
    assert "coordination_group" in text
    assert "parallel_group" in text
    # the three new red-flag claims
    assert "feature independence" in text
    assert "duplicate" in text.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py::test_tasklist_discipline_documents_surface_reserve_coordinate -q`
Expected: FAIL — new strings absent.

- [ ] **Step 3a: Add the integration-surface paragraph to the conceptual model**

In `skills/tasklist-discipline/SKILL.md`, find the paragraph that begins `Phase planning uses separate scheduling metadata.` (currently line 51). **Immediately after** it, insert this new paragraph:

```markdown
Integration-surface metadata models **parallel-execution safety by write surface**, not by feature intent. `integration_surfaces` is a list of conventional tags naming the shared write areas a slice mutates (recommended vocabulary: `cms-block-registry`, `directus-schema`, `page-renderer-dispatch`, `theme-tail-css`, `content-contract-types`, `reviewer-artifacts` — extend per project). `reservations` are scarce-allocation claims on a single value (`homepage-sort:15`, `route-slug:/offers`, `block-kind:slider`), each scoped `phase` (default) or `project`; `tasktool reserve add` **refuses a duplicate allocation** within scope. `coordination_group` names a set of slices that *intentionally* share a surface and agree to coordinate — serialize reviews, designate an integration owner, run the centralized-registry merge playbook. It is the opposite of `parallel_group`, which asserts the slices are independent: a shared surface needs a `coordination_group` or a `depends_on`, never a `parallel_group`.
```

- [ ] **Step 3b: Add the commands to the daily-commands block**

In the same file, find the `tasktool ratify <slice-id> --parallel-group bootstrap` line inside the ```sh ... ``` daily-commands block (currently line 70). **Immediately after** that line, insert these lines (inside the same code fence):

```sh
tasktool surface add <slice-id> <surface> [<surface>...]   # declare shared write surfaces
tasktool surface remove <slice-id> <surface>
tasktool surface list [<phase-id>]
tasktool surface check <phase-id>            # unguarded overlaps + coordinated surfaces + reservation contention
tasktool reserve add <slice-id> <resource>:<value> [--scope phase|project] [--note "..."] [--force --reason "..."]
tasktool reserve remove <slice-id> <resource>:<value>
tasktool reserve list [<phase-id>]
tasktool coordinate <slice-id> --group <name>   # mark intentional shared-surface coordination
tasktool coordinate <slice-id> --clear
```

- [ ] **Step 3c: Add the three red-flag rows**

In the same file, find the `## Red flags` table. The last data row currently is the `"The slice is currently blocked, so I'll add blocked_on to model the phase plan."` row (line 185). **Immediately after** that row, append these three rows:

```markdown
| "These slices are feature-independent, so they're parallel-safe." | Parallel safety is about **write surface**, not feature independence. Declare `integration_surfaces` and run `tasktool surface check <phase-id>` before dispatching them together. |
| "I'll pick a sort slot / collection name / route slug freely." | **Reserve** it (`tasktool reserve add`) so siblings cannot collide; for project-global resources use `--scope project`. The tool refuses a duplicate allocation. |
| "We both need the CMS registry, so I'll just `parallel_group` them." | A shared surface needs a `coordination_group` (coordinate) or a `depends_on` (serialize), not a `parallel_group` — which asserts independence the slices do not have. |
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py::test_tasklist_discipline_documents_surface_reserve_coordinate -q`
Expected: PASS.

Also confirm the pre-existing tasklist-discipline tests still hold:
Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -k "tasklist_discipline or global_tasktool_shim" -q`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add skills/tasklist-discipline/SKILL.md \
        tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
git commit -m "P7.S6: document surface/reserve/coordinate in tasklist-discipline"
```

---

## Task 4: phase-planning & writing-plans — surface/reservation tables

**Files:**
- Modify: `skills/phase-planning/SKILL.md`
- Modify: `skills/writing-plans/SKILL.md`
- Test: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`

- [ ] **Step 1: Write the failing test**

Append to `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`:

```python
def test_phase_planning_and_writing_plans_document_surface_tables() -> None:
    for skill in ["phase-planning", "writing-plans"]:
        text = skill_text(skill)
        assert "surface/reservation table" in text, (
            f"{skill} must require a surface/reservation table"
        )
        assert "tasktool surface check <phase-id>" in text, (
            f"{skill} must tell the author to run surface check before ratifying"
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py::test_phase_planning_and_writing_plans_document_surface_tables -q`
Expected: FAIL — strings absent from both skills.

- [ ] **Step 3a: phase-planning — add a declaration step in Phase Shaping**

In `skills/phase-planning/SKILL.md`, in the `### Phase Shaping` numbered list, find step 6 (currently line 35):

```markdown
6. Run `tasktool schedule <phase-id>` and include the output or a concise summary in the phase planning document.
```

Replace it with these two steps (a new step 6 is inserted; the old step 6 becomes 7):

```markdown
6. Declare each slice's write surfaces and scarce reservations: `tasktool surface add <slice-id> <surface>...` and `tasktool reserve add <slice-id> <resource>:<value> [--scope phase|project]`. **Before ratifying any `parallel_group`, run `tasktool surface check <phase-id>`** and resolve every unguarded surface overlap — add a `depends_on` to serialize, or a `coordination_group` to coordinate. A `parallel_group` must not contain slices that share an integration surface without one of those links.
7. Run `tasktool schedule <phase-id>` and include the output or a concise summary in the phase planning document.
```

- [ ] **Step 3b: phase-planning — require the table in the document**

In the same file, find the `The document must include:` bulleted list (currently lines 37–42). **Immediately after** the `- explicit notes on which dependencies must be ratified by slice spec/plan writers.` bullet, insert:

```markdown
- a **surface/reservation table**: one row per prospective slice listing its `integration_surfaces`, `reservations` (`resource:value` + scope), and `coordination_group`.
```

- [ ] **Step 3c: phase-planning — add a red-flag row**

In the same file, find the `## Red Flags` table. After the last row (`"The first sketch is final."` row, line 68), append:

```markdown
| "These slices are in different features, so I'll `parallel_group` them." | Parallel groups are about shared **write surface**, not feature boundaries. Declare `integration_surfaces` and run `tasktool surface check <phase-id>` before ratifying a parallel group. |
```

- [ ] **Step 3d: writing-plans — add the surface/reservation requirement**

In `skills/writing-plans/SKILL.md`, find the `**Scheduling ratification:**` paragraph (currently line 26). **Immediately after** that paragraph, insert this new paragraph:

```markdown
**Integration surfaces & reservations:** A slice plan that may run in parallel with siblings must include a **surface/reservation table** — for this slice (and any sibling it could overlap), list `integration_surfaces`, `reservations` (`resource:value` + scope), and `coordination_group`. Declare them on the tracker with `tasktool surface add` / `tasktool reserve add` / `tasktool coordinate`, then run `tasktool surface check <phase-id>` before ratifying. Do not place slices that share a surface in the same `parallel_group` without a `depends_on` (serialize) or a `coordination_group` (coordinate). A duplicate scarce-resource allocation is refused at declaration time — pick a free value rather than `--force`, unless you genuinely intend a coordinated shared allocation and record the reason.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py::test_phase_planning_and_writing_plans_document_surface_tables -q`
Expected: PASS.

Confirm the pre-existing writing-plans tests still hold:
Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -k "writing_plans or artifact_transactions" -q`
Expected: PASS (all).

- [ ] **Step 5: Commit**

```bash
git add skills/phase-planning/SKILL.md skills/writing-plans/SKILL.md \
        tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
git commit -m "P7.S6: require surface/reservation tables in phase-planning and writing-plans"
```

---

## Task 5: Full-suite verification

**Files:**
- No source changes; verification only. (The slice was ratified at plan-settle; execution does not re-ratify or mutate the tracker here.)

- [ ] **Step 1: Run the full docs-lifecycle test file**

Run: `cd tools/tasktool && python -m pytest tests/test_skill_tasktool_lifecycle_docs.py -q`
Expected: PASS — all pre-existing tests plus the 5 new functions (Task 1–4) green.

- [ ] **Step 2: Run the full tasktool test suite**

Run: `cd tools/tasktool && python -m pytest -q`
Expected: PASS — no regressions. (This slice changes no Python; the only new tests are the doc-content assertions above.)

- [ ] **Step 3: Sanity-check the referenced commands exist**

Run:
```bash
tasktool surface check --help
tasktool reserve add --help
tasktool coordinate --help
tasktool worktree status --help
```
Expected: each prints usage (no `invalid choice`), confirming the prose references real CLI surface shipped by P7.S2–S4.

- [ ] **Step 4: Confirm the scheduling contract is intact (read-only)**

Run: `tasktool show P7.S6`
Expected: `planning_status: ratified` (set at plan-settle), `depends_on: P7.S2, P7.S3, P7.S4`, no parallel group. This step is read-only — do **not** mutate or commit the tracker from the implementation worktree here; the ratification and its commit already happened in the planning session.

---

## Self-review notes (author checklist, already run)

- **Spec coverage:** §4.F `subagent-driven-development` (surface check → Task 2 Step 3a; integrate-main checkpoint → Task 2 Steps 3b–3c; playbook → Task 1 + Task 2 Step 3d). §4.F `tasklist-discipline` (commands + vocabulary + coordination/parallel distinction + 3 red flags → Task 3). §4.F `phase-planning`/`writing-plans` (surface/reservation tables + `surface check` before ratify → Task 4). §6 `S6` testing line (docs lifecycle test extended; playbook file exists → Task 1 + the four new assertion functions). No §4.F item is unaddressed. (Plan ↔ tracker drift validation is **§4.G / P7.S7**, out of scope here.)
- **Dependency on P7.S5:** intentionally avoided — the integrate-main checkpoint documents `worktree sync` as "when available" plus a raw-git fallback, so S6 lands correctly whether or not S5 ships.
- **No placeholders:** every doc edit shows the exact insert/replace text; every test step shows the exact assertion and command.
- **String consistency:** each new test assertion's substring is reproduced verbatim in the corresponding skill edit (`tasktool surface check <phase-id>`, `Integrate-current-main checkpoint`, `references/registry-merge-playbook.md`, `surface/reservation table`, `cms-block-registry`, `feature independence`).
- **Regression guard:** Tasks 2–4 each re-run the relevant pre-existing assertions to prove the edits did not disturb `test_subagent_driven_development_starts_slice_before_dispatch`, the tasklist-discipline authority test, or the writing-plans start-step test.
