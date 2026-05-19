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
