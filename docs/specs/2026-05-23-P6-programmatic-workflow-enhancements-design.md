# P6 — Programmatic Workflow Enhancements (Design)

**Phase ID:** P6
**Date:** 2026-05-23
**Status:** spec (awaiting external review)

## 1. Motivation

The tasktool data model and skill suite already encode a multi-step workflow per slice — brainstorm a spec, write a plan, implement, review, close — but the *step* itself is never stored. Skills and humans infer "where in the workflow am I?" from a combination of `spec_path`, `plan_path`, `planning_status`, `status`, `started`, `closed`, and the presence of a `reviewer_chain` folder. That inference is reliable enough today, but:

- Downstream consumers that want to *react* to the current step (session-rename hooks, statuslines, future automation) have no first-class field to read.
- The relationship between fields is implicit in skill prose and the reviewer-gate code, not in the model.
- Future enhancements (auto-advance, transition gating, worktree automation, refusing operations on the wrong step) are blocked on having an authoritative step value.

This phase introduces `workflow_step` as a first-class field on `Slice` and `Phase`, plus a transient *review block* on `Slice` populated by the external-reviewer script. The first slice ships only the storage, manual setter, and a read-only inference command — no automation, no migration. Subsequent slices in this phase build on that foundation.

## 2. Scope

### In scope (this phase)

- **S1 (designed in detail below):** Add `workflow_step` field on `Slice` and `Phase`; add transient review block on `Slice`; add `tasktool set --workflow-step`; add `tasktool infer-step` (read-only); update render / show / brief to surface the field; update skill markdown to point at it; ship a small change to the external-reviewer script so it writes the review block.
- **S2 (sketched):** Auto-advance `workflow_step` on existing transition commands (`prepare`, `artifact add`, `start`, `close`). One-shot migration backfill of existing rows.
- **S3 (sketched):** Session-rename hook — reads the slice's `workflow_step` and writes `<agent>-<Pn.Sm>-<step>` to the harness session label (Claude Code `/rename` equivalent on the underlying JSONL summary; Codex equivalent).

### Out of scope (recorded as future slices or follow-up items)

- Adding a `cancelled` status / flag on slices.
- Refusing operations when `workflow_step` is wrong (e.g., refusing `start` if step != `implement`).
- Collapsing `planning_status` into `workflow_step`.
- Collapsing `Phase.status` into `Phase.workflow_step`.
- Worktree automation triggered off step transitions.
- A phase-level *review block* analogous to the slice-level one.
- Reorganising tasktool's CLI surface around workflow verbs rather than the current command set.
- CrossCutting (`X*`) workflow steps — these items skip spec/plan and the step model adds little value.

## 3. Design — S1: Add `workflow_step` field and read-only inference

### 3.1 Model changes

In `tools/tasktool/model.py`:

```python
class SliceWorkflowStep(str, Enum):
    SPEC = "spec"
    PLAN = "plan"
    IMPLEMENT = "implement"
    DONE = "done"

class PhaseWorkflowStep(str, Enum):
    SPEC = "spec"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class ReviewStage(str, Enum):
    AWAITING_RESPONSE = "awaiting_response"
    APPLYING_FIXES = "applying_fixes"
    PASSED = "passed"
```

Field additions:

- `Slice.workflow_step: SliceWorkflowStep | None = None`
- `Slice.review_active: bool = False`
- `Slice.review_stage: ReviewStage | None = None`
- `Phase.workflow_step: PhaseWorkflowStep | None = None`

`CrossCutting` is unchanged.

`SCHEMA_VERSION` bumps from `1` to `2`. Serialise enum values as plain lowercase strings. `None` is legal and means "not set" — for `workflow_step` this is the default for existing rows; for the review fields it means "no review currently active".

### 3.2 CLI surface

New / changed commands:

- `tasktool set <id> --workflow-step <value>` — value must match the row kind (`spec|plan|implement|done` for slices; `spec|ready|in_progress|done` for phases). `--clear-workflow-step` to unset.
- `tasktool set <id> --review-active <bool>` and `--review-stage <value>` — owned by the external-reviewer script. Skills/agents should not write these directly. Calling `--review-active false` clears `--review-stage` too. Only valid against slice rows.

**Argument shape changes to `tasktool set`.** Today `tasktool set` requires `--status` (`tools/tasktool/cli.py:88`, `tools/tasktool/commands.py:941`). S1 relaxes this so the command accepts any non-empty subset of `{--status, --workflow-step, --clear-workflow-step, --review-active, --review-stage}` plus existing flags like `--blocked-on` / `--depends-on`. Validation rules:

- At least one mutating flag must be present (no-op invocations are rejected).
- `--workflow-step` and `--clear-workflow-step` are mutually exclusive.
- `--review-active false` implicitly clears `--review-stage`; passing `--review-stage <value>` together with `--review-active false` is rejected.
- `--review-active` and `--review-stage` against non-slice rows are rejected.
- `--workflow-step` values are validated against the row's kind enum (slice vs phase).
- All other existing single-flag behaviour (`tasktool set --status …`) keeps working unchanged.
- `tasktool infer-step <id>` — print the inferred step for a single row (text by default; `--format json` for structured).
- `tasktool infer-step --all` — print one line per row (slices + phases) with current vs inferred step.
- `tasktool infer-step --all --diff` — same as `--all` but only emits rows where stored ≠ inferred.
- `tasktool list --workflow-step <value>` — filter by stored step.

Surfaced in existing commands:

- `tasktool show <id>` — print `workflow_step` next to `status`; print the review block iff `review_active == true`.
- `tasktool render` — show step glyph or column for slices/phases where space allows; review block only when active.
- `tasktool brief <id>` — include step in the heading, review block only when active.

### 3.3 Inference rules (read-only in S1)

**For a slice:**

```
slice.plan_path absent                                        → spec
slice.plan_path present and slice.planning_status != ratified → plan
slice.plan_path present and slice.planning_status == ratified → implement
status == done                                                → done (overrides all)
```

Rationale: `slice.plan_path` is the authoritative signal that the slice has moved past the spec phase. In real workflows a ratified plan cannot exist without a prior spec phase, so consulting `phase.spec_path` at the slice level is redundant and creates false drift for slices whose phase spec is tracked outside the in-tree `spec_path` (e.g. accepted out-of-band). Phase-level inference still consults `phase.spec_path` (§3.3 phase rules) to surface phases that genuinely never wrote a spec.

**Blocked slices.** `Status.BLOCKED` is an orthogonal overlay on the workflow step, not a step itself. The inference rules above are applied as if `status == in_progress` (i.e., the blocker doesn't change which step the work is in), and the result is annotated:

- Text output: inferred step suffixed with `(blocked)`, e.g. `plan (blocked)`.
- JSON output: `{"step": "plan", "blocked": true}`.

`status == done` always wins regardless of any earlier state — a closed slice infers `done` even if other fields would imply something earlier (the precedence is: `done` > any computed value).

**`infer-step --all --diff` exit code.** Exits `0` when every row matches its stored value or has no stored value. Exits `1` when any row differs (informational; the command itself never writes). Process errors (file not found, etc.) use `2` per existing tasktool convention.

**For a phase.** Rules are evaluated top-to-bottom; the first match wins. They are total over the slice-status alphabet `{ready, in_progress, blocked, done}`.

```
1. phase.spec_path absent                                    → spec
2. phase.spec_path present, no child slices                  → spec
3. child slices exist, every slice.status == done            → done
4. any child slice.status in {in_progress, blocked, done}    → in_progress
5. otherwise (every child slice.status == ready)             → ready
```

Rationale: rule 3 takes precedence over rule 4 so a phase whose current children are all closed always lands on `done`. If new non-`done` slices are later added to that phase, rule 3 stops matching and rule 4 takes over — the phase becomes `in_progress` again. Rule 4 collapses every mixed state ("some started, some not", "some done, some still pending", "one slice is blocked but the rest aren't started") into `in_progress`: once the phase has begun in any way, it is in progress. Rule 5 fires only when no work has begun at all on any child.

**Phase blocked annotation.** When rule 4 matches *and* any child slice has `status == blocked`, the inference output carries a `(blocked)` annotation in text form and `blocked: true` in JSON — symmetric with the slice-level annotation in §3.3. The base step remains `in_progress`. Rule 3 (all done) ignores the blocked overlay because no slice can be both `done` and `blocked`.

**For cross-cutting:** inference returns `n/a`; `--diff` ignores these rows.

### 3.4 Transient review block (slice)

**Scope of ownership.** In the current model, *spec review is phase-owned* — `Phase` carries `spec_path` and `phase_reviewer_chain`; slices have no `spec_path`. The slice-level review block introduced here therefore covers only **slice-owned reviews**: plan review (review of `slice.plan_path`) and post-slice review (review of completed slice work). Phase-level spec/plan reviews remain tracked through `Phase.phase_reviewer_chain` only; a phase-level transient review block is explicit future scope and is **not** added in S1 (see §6).

This means the review block on a slice is only populated when the slice's `workflow_step ∈ {plan, implement}` — i.e., during plan review or post-slice review. When a slice is in `workflow_step == spec`, the active review (if any) belongs to the parent phase, not the slice; the slice's review block stays empty.

Owned by the external-reviewer script (`skills/external-review/scripts/external-reviewer.py`), not by skills or agents:

| Field | Type | Set when |
|---|---|---|
| `review_active` | bool | Reviewer starts a chain on this slice's current step (plan or post-slice). `true` until the round completes or the step advances. |
| `review_stage` | enum: `awaiting_response \| applying_fixes \| passed` | `awaiting_response` while the reviewer is being called; `applying_fixes` once a `revise` verdict comes back and fixes are in progress; `passed` after a `ready` / `ready with small edits` verdict. Cleared when `review_active` becomes `false`. |

JSON serialisation: when `review_active == false` and `review_stage` is unset (the default), both fields are **omitted** from the serialised row, the same way `worktree_*` defaults are elided today. This keeps `tasklist.json` token-clean for rows not under active review.

**Mapping from `external-reviewer review` to a slice ID.** Today the bridge only requires `--work-id` for `post-slice` and `post-phase`. For the new tasktool calls in S1, the script writes the review block only when `--work-id` resolves to a slice row; it is a no-op when `--work-id` is absent or resolves to a phase / cross-cutting row. Concretely:

- `--kind plan` invocations with `--work-id <Pn.Sm>` → write block to that slice.
- `--kind post-slice` invocations with `--work-id <Pn.Sm>` → write block to that slice.
- All other invocations (`--kind spec`, `--kind post-phase`, missing/non-slice `--work-id`) → no tasktool write; phase-owned reviews are out of scope for the slice block in S1.

Lifecycle (slice-owned reviews only):

1. External-reviewer is invoked with `--work-id <Pn.Sm>` → calls `tasktool set <id> --review-active true --review-stage awaiting_response`.
2. Reviewer responds → if verdict is `revise`, call `--review-stage applying_fixes`. If verdict is `ready`/`ready_with_small_edits`, call `--review-stage passed`.
3. Agent reaches the next step → calls `tasktool set <id> --workflow-step <next>`. This implicitly clears `review_active`, `review_stage`.
4. If the slice's `workflow_step` reaches `done`, the review block is permanently absent.

Render policy: `render`, `brief`, `show` print the review block only when `review_active == true`. Steady-state token cost: zero for rows not under review.

### 3.5 Skill markdown updates

All updates are light-touch in S1: pointing at the field, scoping it correctly, explicitly noting that the field is informational in S1 and will drive automation in later slices. No skill *requires* the field to be set.

- **`skills/tasklist-discipline/SKILL.md`** *(primary update)*: Add a `workflow_step` section listing the slice and phase enum values, when to set them manually, and that automation comes later. Show example commands. Cite the read-only `infer-step` command for sanity-checking. Explicit scoping line: *"`workflow_step` tracks where a slice or phase is in the spec → plan → implement → done sequence. The two enums are intentionally different: slices step through spec/plan/implement/done; phases step through spec/ready/in_progress/done. Cross-cutting items (`X*`) do not have a `workflow_step` — they skip the spec/plan loop."*
- **`skills/brainstorming/SKILL.md`**: At the spec-commit step, a one-liner: after `tasktool artifact add … --kind spec`, suggest `tasktool set <id> --workflow-step spec` if not already set. After spec review passes, the skill prose mentions that the agent should set `--workflow-step plan` before invoking writing-plans.
- **`skills/writing-plans/SKILL.md`**: At the plan-commit step, mirror pattern. After plan review passes, set `--workflow-step implement`.
- **`skills/subagent-driven-development/SKILL.md`** and **`skills/executing-plans/SKILL.md`**: Note that the slice's `workflow_step` should be `implement` when work starts and `done` only after post-slice review passes.
- **`skills/external-review/SKILL.md`**: Brief note that the reviewer script writes the transient review block automatically — no agent action required.
- **`skills/project-setup/SKILL.md`**: No changes in S1.

The shared framing across all updates: *"The field is informational in S1. Setting it correctly now means S2 can take it from here."*

### 3.6 External-reviewer script change

`skills/external-review/scripts/external-reviewer.py` (or equivalent bridge) gains three small calls:

- On chain start: `tasktool set <id> --review-active true --review-stage awaiting_response`.
- After reviewer responds with a non-ready verdict: `tasktool set <id> --review-stage applying_fixes`.
- After reviewer responds with a ready / ready-with-small-edits verdict: `tasktool set <id> --review-stage passed`.

Best-effort: failures to update tasktool (e.g., row not found, tasktool not installed) log a warning but do not block the review.

### 3.7 Files touched (S1)

- `tools/tasktool/model.py` — enums, fields, schema bump.
- `tools/tasktool/serialize.py` — round-trip + validation.
- `tools/tasktool/commands.py` — `set` (new flags), `infer-step` (new command), filters on `list`, render output in `show`/`render`/`brief`.
- `tools/tasktool/cli.py` — argparse wiring.
- `tools/tasktool/schema_gen.py` — schema bump + new enum types.
- `tools/tasktool/render.py` — workflow_step column + review block.
- `tools/tasktool/brief.py` — heading + review block.
- `tools/tasktool/tests/` — round-trip, inference rules, CLI tests.
- `skills/tasklist-discipline/SKILL.md` — new `workflow_step` section.
- `skills/brainstorming/SKILL.md`, `skills/writing-plans/SKILL.md`, `skills/subagent-driven-development/SKILL.md`, `skills/executing-plans/SKILL.md`, `skills/external-review/SKILL.md` — short pointers.
- `skills/external-review/scripts/external-reviewer.py` — three best-effort tasktool calls.
- `docs/tasklist.json` — P6 phase row already created during spec phase; S1 slice row is created during the writing-plans step (not here).

### 3.8 Acceptance criteria (S1)

1. `tasktool set <slice-id> --workflow-step plan` updates the field and survives a round-trip through `tasklist.json`.
2. `tasktool show <slice-id>` displays `workflow_step` near `status`.
3. `tasktool infer-step <slice-id>` returns the inferred step per §3.3 without modifying any state.
4. `tasktool infer-step --all --diff` lists every row where stored ≠ inferred and exits 0 when none differ.
5. After external-reviewer is invoked with `--kind plan --work-id <slice-id>` against a slice, `tasktool show <slice-id>` displays `review_active: true, review_stage: awaiting_response` (and the documented later transitions). Equivalent behaviour for `--kind post-slice`.
6. Setting `--workflow-step` to a new value clears `review_active` and `review_stage` for that row.
7. `tasktool render` does not print the review block when `review_active == false` (steady-state token-neutral); JSON serialisation omits the fields entirely when they are at their defaults.
8. Schema version is `2`; existing repos load with `workflow_step` defaulting to `None` and no review block.
9. Every skill listed in §3.5 has the documented update and explicitly scopes the feature.
10. Pre-existing tasktool tests still pass; new tests cover inference rules, round-trip, and the review-block lifecycle.
11. `tasktool set` argument validation: rejects no-op invocations; rejects `--workflow-step` together with `--clear-workflow-step`; rejects `--review-active false --review-stage <anything>`; rejects `--review-active` / `--review-stage` against non-slice rows; rejects `--workflow-step` values that don't match the row's kind enum.
12. Blocked slices: `tasktool infer-step <id>` of a `status == blocked` slice reports the computed step (per the "as if in_progress" rule) plus the `(blocked)` annotation in text and `blocked: true` in JSON. `status == done` overrides any computed step.
13. `tasktool infer-step --all --diff` exits `0` on no drift, `1` on drift, `2` on process errors. Never writes.
14. External-reviewer writes the review block only when `--work-id` resolves to a slice row; `--kind spec` and `--kind post-phase` invocations do not mutate the slice block.
15. Phase inference is total over the slice-status alphabet. Tests cover at minimum: no slices (→ `spec`), all `ready` (→ `ready`), one `in_progress` + rest `ready` (→ `in_progress`), one `blocked` + rest `ready` (→ `in_progress (blocked)`), `done + ready` mix (→ `in_progress`), `done + blocked` mix (→ `in_progress (blocked)`), all `done` (→ `done`).
16. `tasktool infer-step --all` and `--diff` emit `n/a` for cross-cutting (`X*`) rows and never flag them as drift.

## 4. Sketch — S2: Auto-advance and migration

Once S1 is bedded in and the inference rules are trusted, S2 wires inference into existing mutation commands so the field self-maintains:

- `tasktool prepare ... --spec <path>` ⇒ set `workflow_step = spec` if unset.
- `tasktool artifact add ... --kind spec` followed by reviewer ready ⇒ `workflow_step = plan` advance proposed by tasktool, applied manually or via a `--advance-step` flag on the relevant command (TBD in S2 design).
- `tasktool artifact add ... --kind plan` after plan review ready ⇒ `workflow_step = implement`.
- `tasktool start <id>` ⇒ `workflow_step = implement` if unset.
- `tasktool close <id>` ⇒ `workflow_step = done`.
- One-shot migration: `tasktool migrate workflow-step` backfills every existing row using the §3.3 inference. Run once at upgrade, then never again.

Manual `tasktool set --workflow-step` always wins over auto-advance.

S2 needs its own spec when scheduled, including the explicit advance semantics for ambiguous cases (e.g., `--advance-step` flag vs implicit).

## 5. Sketch — S3: Session-rename hook

Using the `workflow_step` field plus the slice's `Pn.Sm` ID, write the harness session label to match `<agent>-<Pn.Sm>-<step>`. Concretely:

- Detect the active slice: a small persistent file (e.g., `~/.claude/projects/<slug>/<session_id>/superstar-focus.json`) records which slice the session is working on. Set on `tasktool start` or via a `tasktool focus <id>` command.
- On `workflow_step` change for the focused slice, the hook rewrites the session's `summary` field in the harness JSONL — the same field Claude Code's `/rename` updates. Codex equivalent path.
- Agent prefix derived from session metadata (Claude / Codex distinguishable from harness home directory).

S3 needs its own spec, including: how the focused-slice link is established and persisted, how the rename interacts with manual `/rename` overrides (lose to manual, or always overwrite?), and what happens to multi-slice sessions.

## 6. Future scope (recorded, not scheduled)

- Add a `cancelled` slice status (or `cancelled: bool` flag). Generalise phase-`done` inference to "all slices `done` or `cancelled`".
- Collapse `planning_status` into `workflow_step` (the two encode largely overlapping information).
- Collapse `Phase.status` into `Phase.workflow_step` (phase blocking expressed as a separate `blocked: bool`).
- Refuse mutating commands when `workflow_step` is wrong for the operation (e.g., refuse `start` if step != `implement`).
- Worktree automation: create the worktree on transition to `implement`; mark prune-pending on transition to `done`.
- Phase-level *review block* mirroring the slice-level transient block, scoped to phase spec review.
- A `tasktool review-history <id>` command that lazily reads `chain.json` from the reviewer folder for richer history rendering — without denormalising any of that data into `tasklist.json`.

## 7. Open questions (none blocking S1)

- The exact text rendering of `workflow_step` in `tasktool render` (glyph vs short word vs full word). Decided at implementation time; render output is not part of any external contract.
- Whether the external-reviewer script's three new tasktool calls should be guarded by a config flag (off by default until S1 is verified to land cleanly). Leaning yes; finalise during implementation.

## 8. Round-1 review resolution log

R1 returned `revise` with four findings. Resolutions applied in this revision:

- **F1 (blocking) — slice-owned spec review block conflict.** §3.4 now restricts the slice review block to slice-owned reviews (`--kind plan`, `--kind post-slice`) and is explicit that spec/phase reviews are phase-owned and out of scope in S1. The mapping from `external-reviewer` invocations to the slice block is spelled out. AC 5 rewritten to test `--kind plan --work-id <slice>` rather than spec review.
- **F2 (important) — blocked-slice inference underspecified.** §3.3 now treats `Status.BLOCKED` as an orthogonal overlay (inference proceeds as if `in_progress`, with `(blocked)` / `blocked: true` annotations) and gives `status == done` explicit precedence over any computed value. AC 12 covers this.
- **F3 (important) — `tasktool set --status` currently required.** §3.2 adds an "Argument shape changes" subsection that makes `--status` optional, defines the legal flag combinations, and rejects invalid mixes. AC 11 covers validation.
- **F4 (minor) — S1 slice row claim mismatched the tasklist.** §3.7 reworded so the file-touched list reflects that the P6 phase row already exists and the S1 slice row is created during the writing-plans step, not during spec.

Open question Q2 from the reviewer (default review-field omission from JSON) resolved in §3.4 (`review_active=false` defaults are elided like worktree defaults). Q3 (`--diff` exit code) resolved in §3.3 (`0` no drift, `1` drift, `2` process error).

R2 returned a fresh finding F5 (blocking) on phase inference completeness, plus two open questions on phase-level blocked handling and `done + ready` semantics. Resolutions:

- **F5 (blocking) — phase inference incomplete for mixed slice statuses.** §3.3 phase rules rewritten as a total ordered match over `{ready, in_progress, blocked, done}`. Rule 3 (all `done` → `done`) takes precedence over rule 4 (any non-`ready` child → `in_progress`); rule 5 (all `ready` → `ready`) is the residual. Once any work has begun in any way (a child is `in_progress`, `blocked`, or `done`) the phase is `in_progress`. AC 15 enumerates the test cases.
- **R2 open Q1 (phase blocked overlay).** Resolved: when rule 4 matches and any child is `blocked`, the phase carries a `(blocked)` annotation symmetric with the slice-level overlay; the base step stays `in_progress`.
- **R2 open Q2 (`done + ready` semantics).** Resolved: `done + ready` matches rule 4 and infers `in_progress`. Once a child has finished, the phase has begun, even if other children haven't started.

R3 returned `revise` with one blocking finding F1 (slice inference contradicts plan tests). Resolution: spec amended (this section) to drop the `phase.spec_path` precondition for slice inference; `slice.plan_path` is now the authoritative signal for moving past the spec step. The plan tests already encoded this contract; the spec rule was over-precise. Phase-level inference still honors `phase.spec_path`.
