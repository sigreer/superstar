# Merged findings for r1

## Primary

# Review — 2026-05-19-p4-tasktool-coordination-lifecycle.md (post-slice, round 1)

- Target: `docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md`
- Request: `docs/reviewer/p4-tasktool-coordination-lifecycle-P4-S2-post-slice/r1-2026-05-19T2321-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

# Post-Slice Review — P4.S2 (Lifecycle Status Enforcement)

## 1. Findings

**F1 — `validate_project` does not enforce `started >= created`** · Severity: minor
`tools/tasktool/validate.py:45-55` only checks `closed < created`. A row where `started` precedes `created` would pass. The spec requires a `started` marker that "proves the item was started", so an ordering invariant fits naturally. Not blocking; consider adding alongside the closed/created check.

**F2 — `set --status in_progress` on a `done` item raises "already done"** · Severity: nit
`commands.py:368-369` unconditionally routes `IN_PROGRESS` through `_start_item`, which refuses done items. Previously this transition would simply assign the status. The new behavior is arguably correct (a re-open should be explicit), but it's an undocumented behavior change. Mention it in the skill prose or add `--resume`-style affordance if intended.

**F3 — `cmd_close` audit-note ordering** · Severity: nit
`commands.py:394-409` appends the ready-close audit to `item.notes` first, then later appends `--note` content. The plan didn't specify ordering, but the user-supplied note ends up *after* the audit, which can read oddly when humans scan notes. Cosmetic; not a defect.

**F4 — `unblock --resume` quietly stamps `started`** · Severity: minor
`commands.py:436` calls `_start_item(_qid, item, resume=True)` from `cmd_unblock`. The spec covers this for `start --resume`, but `unblock --resume` is a separate command path and the side-effect of stamping `started` is not documented in the spec or in `skills/tasklist-discipline/SKILL.md`. Add a one-liner where unblock is described, or downgrade to nit.

**F5 — `set --status done` error message references `close` flags** · Severity: nit
`commands.py:364-367` tells the user to run `tasktool close <id> --allow-ready-close --reason …`, which is correct (the override is only wired on `close`, not `set`). Slightly surprising UX (the user is using `set`), but the hint is accurate. Consider adding `--allow-ready-close` to `set` for symmetry — out of scope for this slice.

**F6 — P4.S1 already closed with `started: null`** · Severity: nit / informational
`docs/tasklist.json:252-265`. P4.S1 was closed before the lifecycle guard landed (commit `57dae31` predates `fd59f7f`). No `ready-close override` audit note is present because the rule did not yet exist. This is by-design per the spec ("Existing files load with `started: null`") and not actionable, but worth flagging so reviewers don't mistake it for a missed enforcement.

**F7 — Reviewer chain `chain.json` shows no completed rounds** · Severity: informational
`docs/reviewer/p4-tasktool-coordination-lifecycle-P4-S2-post-slice/chain.json` has `"rounds": []`. Expected for an in-flight review; the slice close gate will require at least one ready round before `tasktool close P4.S2` succeeds.

**F8 — Skill coverage matches plan** · No issue
All five targeted skills (`tasklist-discipline`, `using-git-worktrees`, `subagent-driven-development`, `executing-plans`, `writing-plans`) now reference `tasktool start <slice-id>` and/or authoritative-checkout routing. Regression tests in `test_skill_tasktool_lifecycle_docs.py` exist.

## 2. Open questions / assumptions

- Assumed the full `pytest tools/tasktool/tests` suite passes — could not execute tests under plan-mode restrictions. The plan's Closeout Step 1 requires this; please confirm in the chain.
- Is `unblock --resume` stamping `started` intentional, or should it only set status and leave `started` to `start`? (F4)

## 3. Suggested document edits

- Plan / spec: explicitly note that `unblock --resume` also stamps `started`.
- `tools/tasktool/validate.py`: add `started < created` rejection alongside the existing `closed < created` check (F1).
- Consider an audit-note ordering tweak in `cmd_close` so the user-supplied `--note` appears before the override audit, or document the chosen order.

## 4. Verification gaps / commands

Please run and paste results before close:

```sh
PYTHONPATH=tools python -m pytest tools/tasktool/tests -q
tools/tasktool/tasktool validate --strict-format
git status --short
```

These are the closeout gates in the plan (lines 1284-1290 and 1334-1343). The first verifies all new lifecycle/skill tests pass; the second confirms `docs/tasklist.json` is canonical with the new `started` field; the third confirms only the in-flight reviewer chain is dirty.

## 5. Overall verdict

**ready with small edits**

The slice meets every P4.S2 acceptance criterion: `tasktool start`, the `set --status in_progress` alias, the slice-close start-required guard with `--allow-ready-close --reason` override and audit note, the `started` field round-trip in model/serialize/schema/render/brief, the skill rewrites, and matching regression tests. The findings above are polish, not blockers. Confirm the full test suite + `validate --strict-format` are clean, then close.


## Sweep 1

# Review — 2026-05-19-p4-tasktool-coordination-lifecycle.md (post-slice, round 1)

- Target: `docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md`
- Request: `docs/reviewer/p4-tasktool-coordination-lifecycle-P4-S2-post-slice/r1-2026-05-19T2321-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

# Post-Slice Review: P4.S2 — Lifecycle Status Enforcement

## 1. Findings

### S1.F1 — Lifecycle date ordering is not enforced. Severity: minor
`tools/tasktool/validate.py:45-55` (`_check_dates`) validates that `started` is a calendar date and that `closed >= created`, but it does not enforce `created <= started` or `started <= closed`. A row can therefore carry e.g. `created: 2026-05-19`, `started: 2025-01-01`, `closed: 2026-05-19` and pass `validate --strict-format`. Because `_start_item` only writes `_today()`, normal flows can't produce drift, but an import or manual edit can, and the spec's intent is that `started` is a real lifecycle marker. Tighten with `started >= created` and `closed >= started` (when both present).

### S1.F2 — `tasktool set --status done` has no ready-close escape valve. Severity: minor
`cmd_close` accepts `--allow-ready-close --reason` (commands.py:382, 394-401) and refuses a never-started slice without it. `cmd_set` enforces the same guard for `--status done` (commands.py:363-367) but offers no override and the CLI parser for `set` has no `--allow-ready-close` flag (cli.py:61-66). Per the spec ("`tasktool set P1.S1 --status done` uses the same two-root reviewer-gate contract as `tasktool close`"), the two close paths are intended to be equivalent. Decide: either drop ready-close support from `set` and document `close` as the only legacy escape, or add the same flags to `set`. The spec leans toward parity.

### S1.F3 — Skill-doc regression test only covers three of five updated skills. Severity: nit
`tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` asserts content in `subagent-driven-development`, `executing-plans`, and `tasklist-discipline`. The plan also requires `using-git-worktrees` and `writing-plans` to be updated (which they are — verified at `skills/using-git-worktrees/SKILL.md:16` and `skills/writing-plans/SKILL.md:22`), but no regression test pins those phrases. They are the skills most likely to drift back to prose-only guidance.

### S1.F4 — Plan checkboxes still unchecked. Severity: nit
`docs/plans/2026-05-19-p4-tasktool-coordination-lifecycle.md` retains `- [ ]` on every step in P4.S2 (Tasks 4-7 and the closeout). Git history shows the commits exist (`b810698` field, `dc09679` start, `fd59f7f` close guard, `6abf660` set-done guard, `3f98a3d` validate, `ed40767` skills), and the tasklist correctly shows P4.S2 as `in_progress` with `started: 2026-05-19`. But the plan file itself does not reflect completion — readers can't tell from the plan what is done. Either mark steps `[x]` as Task 7-style closeout, or note convention that subagent-driven-development tracks completion in `docs/tasklist.json` rather than in plan checkboxes.

### S1.F5 — Reviewer chain dir untracked, no rounds yet. Severity: nit (informational)
`docs/reviewer/p4-tasktool-coordination-lifecycle-P4-S2-post-slice/chain.json` shows `rounds: []`. This is normal — the round-1 request files are present and this very review will be the first response. No action needed beyond the close-time staging that `tasktool close` will perform.

## 2. Open questions / assumptions

- **Assumption:** P4.S2 closeout intentionally runs only post-slice review (not post-phase); post-phase review of P4 is queued by the plan's "P4.S2 Closeout → Step 3" and will follow this slice's close. If the workflow expects P4 to remain `ready` (parent phase) until both slices are done, that matches current tasklist state (P4 status=`ready`, started=null), which is consistent — only slices and tasks have been started so far.
- **Assumption:** No project-wide migration was needed to backfill `started` on previously-closed rows (P1, P2 archive, X1..X9, P4.S1). The serializer defaults missing `started` to `null` (model.py:29-73, serialize.py:32-72), which is the documented behavior in the spec. Verified in the live `docs/tasklist.json`.
- **Question:** Is `tasktool set <id> --status in_progress` expected to also work for tasks/cross-cutting (not just slices)? Code path allows it (`_start_item` is item-agnostic). Spec says "Accepts phases, slices, tasks, and cross-cutting items." Looks intended; flagging only to confirm.

## 3. Suggested document edits

- Add to the plan, P4.S2 closeout: "On close, mark each completed `- [ ]` in Tasks 4-7 as `- [x]`" — or remove the boxes to avoid the stale-state ambiguity in S1.F4.
- In the spec Acceptance Criteria, clarify whether `set --status done --allow-ready-close --reason "..."` is required or whether close is the only legacy bypass (resolves S1.F2).

## 4. Verification gaps / commands to run

I was unable to run shells from this reviewer pass; please confirm the following before closing:

```sh
./tools/tasktool/tasktool validate --strict-format
python -m pytest tools/tasktool/tests -v
git status --short
```

Expected:
- `validate --strict-format` clean.
- `tools/tasktool/tests/test_lifecycle_start.py` (11 tests visible) and `test_skill_tasktool_lifecycle_docs.py` pass.
- Only intentional dirty paths: `docs/reviewer/p4-tasktool-coordination-lifecycle-P4-S2-post-slice/` (will be staged on close).

If S1.F1 is addressed, also exercise:

```sh
python -m pytest tools/tasktool/tests/test_validate.py -v
```

with a new case asserting `started < created` and `closed < started` are rejected.

## 5. Overall verdict

**ready with small edits**

The slice delivers the spec's lifecycle gate end-to-end: `started` field across all four item types, `tasktool start` (with `--resume`), `set --status in_progress` aliased to `_start_item`, slice close refused without `started` (with `--allow-ready-close --reason` audit-noted escape), set-done guard, validator extended for `started`, and all five required skills updated with regression coverage on three of them. P4.S2's own lifecycle is correctly stamped (`started: 2026-05-19`, `status: in_progress`) so the new guard doesn't trip on its own closeout. S1.F1 and S1.F2 are worth a tightening pass but don't block the slice; S1.F3-S1.F5 are cosmetic.

