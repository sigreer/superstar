# X22 — Add `cancelled` terminal status to tasktool

**Date:** 2026-05-23
**ID:** X22 (cross-cutting)
**Type:** Spec / design

## Problem

`tasktool` today models four statuses: `ready | in_progress | blocked | done`. There is no first-class way to record that a slice, cross-cutting item, or phase was **terminated without shipping** — scope dropped, deferred, superseded, or otherwise abandoned. Operators currently work around this by:

- Marking the row `done` (lies about completion; passes through the post-slice review gate it shouldn't),
- Leaving the row indefinitely in `ready` or `blocked` (clutters `--open` lists, distorts phase status), or
- Hand-editing notes (loses the structured signal).

Each workaround corrupts either the lifecycle audit trail, the post-slice/post-phase review gates, or the `list --open` / `phase-status` / `ready-slices` reports that downstream skills depend on.

This spec defines a fifth status, `cancelled`, as a peer of `done` (terminal but explicitly *not* shipped), and the supporting CLI verb, schema split, gate behavior, dependency semantics, archive handling, and render rules.

## Goals

1. Add `cancelled` as a terminal status applicable to **slices**, **cross-cutting items**, and **phases** — not tasks.
2. Provide a dedicated `tasktool cancel <id> --reason "<text>"` verb that is the only sanctioned path to enter the status.
3. Preserve correctness of existing gating, scheduling, and archive logic by introducing a single `is_terminal(status)` helper and routing the "is this row open vs finished?" sites through it (without converting sites where the intent is specifically "shipped").
4. Make dependency satisfaction strict: a `cancelled` dependency does **not** unblock downstream work.
5. Keep the `closed` field's `YYYY-MM-DD` shape; record precise audit data in `notes`.

## Non-goals

- Un-cancelling a row through a dedicated verb. The emergency path (`TASKTOOL_RAW=1` + `validate --normalise`) is acceptable; cancellation is meant to be deliberate.
- Adding a separate "cancellation report" artifact. The reason in `notes` is sufficient.
- Changing the meaning of `blocked` (still runtime-blocked) or `depends_on` (still planning-time precondition).
- Reverting prior decisions: tasks remain unaffected; their status enum stays `ready | in_progress | done`.

## Decisions

### Naming

- The status value is the string literal `"cancelled"` (British/U.S.-agnostic in tasktool; matches `cancel` verb).
- Enum constant: `Status.CANCELLED`.
- Emoji: `🚫`.

### Allowed scopes

| Item type | Status set after this change |
|-----------|------------------------------|
| Task | `ready \| in_progress \| done` (unchanged) |
| Slice | `ready \| in_progress \| blocked \| done \| cancelled` |
| Cross-cutting | `ready \| in_progress \| done \| cancelled` |
| Phase | `ready \| in_progress \| done \| cancelled` |

Rationale for excluding tasks: in-slice tasks are intra-slice bookkeeping. They roll up with the parent slice; cancelling a slice implicitly cancels its open tasks for the purposes of any caller that asks "is this row done?".

### Schema enums (`tools/tasktool/schema_gen.py`)

Replace the existing pair:

```python
slice_status_enum = ["ready", "in_progress", "blocked", "done"]
non_blocked_status_enum = ["ready", "in_progress", "done"]
```

with four explicit enums:

```python
task_status_enum  = ["ready", "in_progress", "done"]
phase_status_enum = ["ready", "in_progress", "done", "cancelled"]
cross_status_enum = ["ready", "in_progress", "done", "cancelled"]
slice_status_enum = ["ready", "in_progress", "blocked", "done", "cancelled"]
```

Update each schema reference site (task, slice, phase, cross-cutting) to use its own enum.

**Tasks must reject `cancelled` at every layer**, not only at the JSON-schema layer. `tasktool validate` today loads via `load_project()` and runs `validate_project()` without first invoking JSON-schema validation (`commands.py:1686-1689`); a raw row with `"status": "cancelled"` will parse through `Status(v)` in `serialize.py:75-84` because `Status.CANCELLED` exists on the shared enum. The plan **must** therefore:

1. Add a JSON-schema test asserting a task row with `status="cancelled"` fails schema validation (uses `task_status_enum`).
2. Amend `_check_task()` in `validate.py:69-76` to explicitly reject `Status.CANCELLED` regardless of `closed`, with a clear error (`task <id>: cancelled is not a valid task status; cancel the parent slice instead`).
3. Add a `validate_project()` test that constructs a `Task` with `status=Status.CANCELLED` and asserts the semantic validator rejects it.

Both gates (schema and semantic) must reject independently — the schema gate catches raw input; the semantic gate catches in-memory construction.

### CLI verb

```
tasktool cancel <id> --reason "<text>" [--cascade] [--no-archive]
```

- `<id>` accepts only phase, slice, and cross-cutting forms (`P2`, `P2.S3`, `X22`). Task IDs (e.g. `P2.S3.T1`) are **explicitly rejected** by `cmd_cancel` with a clear error (`cancel does not apply to tasks; cancel the parent slice instead`). The plan must add a test for this rejection.
- `--reason` is required; empty string is rejected with a clear error.
- `--cascade` is a phase-only flag (rejected for slice/X ids). When set on a phase, every slice in the phase whose status is **not** terminal (`done` or `cancelled`) is also cancelled, sharing the same reason text plus a suffix `(cascaded from <phase-id>)`.
- `--no-archive` is an X-only flag (rejected for slice/phase ids). Suppresses the default auto-archive behavior on cross-cutting cancellation (mirrors `close <x-id> --no-archive`).
- The verb stamps:
  - `status = Status.CANCELLED`
  - `closed = <today as YYYY-MM-DD>` (matches existing `_check_date` shape at `validate.py:62`)
  - Appends to `notes`: `Cancelled <ISO-8601 timestamp>: <reason>` on its own line. For cascaded children, the suffix `(cascaded from <phase-id>)` is appended to the same line.
- The verb refuses to run if the row is already terminal (`done` or `cancelled`), with a clear message.
- The verb bypasses the external-review gate entirely. Cancelled work never shipped; reviewer verdict is meaningless. This is documented in the help text and the `tasklist-discipline` skill.

### `set --status cancelled` rejection

`tools/tasktool/cli.py:91` today restricts `set --status` choices to `["ready", "in_progress", "done"]`. The implementation **must not** add `cancelled` to that list. Additionally, `cmd_set` must explicitly raise with a helpful hint (`use \`tasktool cancel <id>\` to cancel`) if a future contributor widens the choices, providing defense in depth.

### `tasktool close` interaction

`tasktool close <id>` refuses if the row is already `cancelled` (distinct verb, distinct path; do not silently overwrite).

### Other lifecycle-adjacent commands on cancelled rows

| Command | Behavior on a row with `status=cancelled` |
|---------|--------------------------------------------|
| `start` | Refuse — `is_terminal` rows cannot be started. (Already covered above.) |
| `set --status <ready\|in_progress\|done>` | Refuse — cancelled is a terminal sink; no reversal via `set`. Operator hint: "edit raw with `TASKTOOL_RAW=1` if you truly must revive." |
| `block` / `unblock` | Refuse — cancelled rows are not blockable. |
| `deps --add` / `deps --remove` | Refuse — planning edges on a cancelled row are frozen. |
| `ratify` | Refuse — planning status doesn't apply to terminal rows. |
| `note --append` | **Allow** — operators may add post-mortem context to a cancelled row. |
| `note --replace` | **Refuse** — the cancellation audit line lives in `notes`; allowing replacement would overwrite it. The error must mention `note --append` as the alternative. |
| `ref --add` / `ref --remove` | **Allow** — evidence can still be attached after cancellation (e.g. the PR that subsumed the cancelled work). |
| `title` | **Allow** — operators occasionally clarify a cancelled row's title for the archive. |
| `archive-cross <x-id>` | **Allow** — already-cancelled visible X items (created via `cancel --no-archive`) must be archivable later. The archive markdown writer must persist `status: cancelled`. |
| `archive-phase <p-id>` | **Allow** under the rules in the `archive-phase` section above (cancelled phase + all-terminal slices, gate skipped). |

The plan must add tests covering at least: `set` rejection (each from-status), `block`/`unblock`/`deps`/`ratify` rejection, `note --append` allow, `ref --add` allow, `archive-cross` of a `cancel --no-archive`-created X-item.

### Phase cancellation: cascade rules

- `tasktool cancel P2` (no `--cascade`) refuses when any slice in the phase is open (`ready`, `in_progress`, or `blocked`). The error message lists the open slice IDs. Already-cancelled and already-done slices do **not** count as open; a phase whose slices are all terminal (any mix of `done` and `cancelled`) can be cancelled without `--cascade`. The plan must add a test for the all-terminal-no-cascade case.
- `tasktool cancel P2 --cascade` cancels each open slice using the parent's reason plus `(cascaded from P2)`. Slices that are already `done` or already `cancelled` are **never touched**. The resulting phase legitimately shows mixed terminal children (e.g. `✅ S1, ✅ S2, 🚫 S3, 🚫 S4`).
- The phase's own row transitions to `cancelled` only after the cascade succeeds.

### `archive-phase` interaction

`tasktool archive-phase <phase-id>` is updated:

- Accepts a phase whose status is `done` **or** `cancelled`.
- Accepts the phase only when every slice is terminal — `done` or `cancelled` (using the new `is_terminal` helper).
- The post-phase external-review gate is skipped when the phase status is `cancelled`. The skip is recorded in the archive note (`Phase cancelled; post-phase review gate skipped`).
- The archive markdown emitted by `archive-phase` records the phase's actual status (`done` or `cancelled`), not a coerced value.

### Cross-cutting archive: `_archive_cross_at_root`

- Loosen the precondition from `status == Status.DONE` to `is_terminal(status)`.
- The archive markdown writer must read the row's actual status and emit `status: cancelled` in the archived stub when applicable. Today's writer hard-codes done semantics; this must be parameterized.
- Default behavior on `tasktool cancel <x-id>` is to auto-archive (mirrors `tasktool close <x-id>`); `--no-archive` keeps the row visible in `cross_cutting` with status `cancelled`.

### Terminal-vs-open helper

Introduce a single helper:

```python
# tools/tasktool/model.py or a new tools/tasktool/lifecycle.py
def is_terminal(status: Status) -> bool:
    return status in (Status.DONE, Status.CANCELLED)
```

The implementation plan must audit every `Status.DONE` reference and decide per site whether to convert to `is_terminal()` or to keep strict `== DONE`. Initial mapping (subject to plan-time review):

| Site | Current | Intended after change |
|------|---------|------------------------|
| `brief.py:78` (skip done tasks in render) | `is not Status.DONE` | `is not Status.DONE` — keep; tasks can't be cancelled |
| `commands.py:591` (`_start_item`: refuse already-done) | `== DONE` | Replace by `is_terminal()` (refuse already-terminal). Add a separate `BLOCKED` arm. |
| `commands.py:614` (`_archive_cross_at_root` precondition) | `!= DONE` | Replace by `not is_terminal()`. Archive writer must persist actual status. |
| `commands.py:812` (start path: terminal check) | `== DONE` | `is_terminal()` |
| `commands.py:953-995` (`cmd_set` done path) | `== DONE` | Keep strict (these are the "shipped" stamps) |
| `commands.py:971-1009` (`cmd_close` body) | `Status.DONE` stamp | Keep strict; add an explicit refuse-if-`is_terminal` precondition at function top |
| `commands.py:1456` (`_done_slice_ids` for `depends_on` satisfaction) | `== DONE` | **Keep strict** — cancelled does not satisfy a dep |
| `commands.py:1459` (skip rendering done/blocked) | `in (DONE, BLOCKED)` | `is_terminal(s.status) or s.status is BLOCKED` |
| `commands.py:1525-1526` (`phase-status` open lists) | `!= DONE` | `not is_terminal()` |
| `commands.py:1795` (`archive-phase` open-slice check) | `!= DONE` | `not is_terminal()` |
| `commands.py:1804-1805` (`archive-phase` stamps phase as DONE) | `!= DONE` then `= DONE` | Skip when already `cancelled`; only stamp done if not already terminal |
| `commands.py:2069` (worktree prune) | `!= DONE` | `not is_terminal()` |
| `validate.py:73,87,121,134` (status=done requires closed) | `== DONE` | Generalize to `is_terminal()` (cancelled also requires closed date) |
| `render.py:5,12,28` (STATUS_EMOJI lookups) | maps DONE | extend map with CANCELLED |
| `importer.py:30,103,128,152` (round-trip from markdown) | DONE | add CANCELLED entry to `EMOJI_TO_STATUS` and date-extraction paths |

This table is the spec contract; the plan must walk every row and either implement it or justify deviation.

### Dependency contract (`schedule`, `ready-slices`)

**Reference of current shape** (`commands.py:1488-1521`): each `schedule` row today emits

```json
{"id": "P2.S3", "status": "ready", "planning_status": "ratified",
 "parallel_group": null, "depends_on": ["P2.S1"], "waiting_on": ["P2.S1"],
 "ready": false, "title": "..."}
```

`waiting_on` is `[dep for dep in depends_on if dep not in done]`. `ready` is `_is_slice_ready_for_work(phase, s)`.

**Changes:**

- `_done_slice_ids` at `commands.py:1456` stays strict (`== Status.DONE`). Cancelled does **not** satisfy a dep.
- Add a new `_cancelled_slice_ids(phase)` helper returning the set of slice IDs whose status is `cancelled`.
- Each `schedule` row gains a new field `cancelled_deps: [<id>, ...]` populated as `[dep for dep in depends_on if dep in cancelled]`. The existing `waiting_on` field's meaning is **narrowed**: it now lists deps that are neither done nor cancelled (i.e. still recoverable). `ready` becomes `False` when either `waiting_on` or `cancelled_deps` is non-empty.
- Resulting JSON shape:

  ```json
  {"id": "P2.S3", "status": "ready", "planning_status": "ratified",
   "parallel_group": null, "depends_on": ["P2.S1", "P2.S2"],
   "waiting_on": ["P2.S1"], "cancelled_deps": ["P2.S2"],
   "ready": false, "title": "..."}
  ```

- Text rendering of `schedule` extends the existing per-slice line to append `cancelled_deps=<list-or-dash>`:

  ```
  P2.S3  [ready/ratified]  group=-  waiting  deps=P2.S1, P2.S2  waiting_on=P2.S1  cancelled_deps=P2.S2  <title>
  ```

  When `cancelled_deps` is empty, the segment renders `cancelled_deps=-`.

- `ready-slices` (`commands.py:1572` area; the CLI binding at `cli.py` resolves to a phase-scoped command). It **omits** any slice with non-empty `cancelled_deps`. The omission is documented in the command's help text. Implementation: change the inner filter to require both `waiting_on` empty and `cancelled_deps` empty before yielding.
- `phase-status` (global; `commands.py:1523-1569`) is **not** modified by this change. Cancelled-deps surfacing lives on `schedule` (which is phase-scoped and already iterates slice rows), not on `phase-status` (which deliberately only lists phase- and X-level rows).
- JSON contract bump: documented in `tasktool schedule --help`. Consumers that did not request `cancelled_deps` will see an additional field; pattern-matching consumers must tolerate it. The narrowing of `waiting_on` is a behaviour change for the corner case where a dep is cancelled — previously such a dep would appear in `waiting_on` indefinitely with no way to ship.

### Render and surfacing

- `STATUS_EMOJI[Status.CANCELLED] = "🚫"` in `render.py:5`.
- `render.py:12` and `:28` extend the "show closed date" branch to also fire for cancelled rows (since they too have a `closed` date).
- `list --open` excludes `cancelled` rows (treated as terminal, same as `done`).
- **Child-task suppression on terminal parents.** `cmd_list` today (`commands.py:1571-1604`) walks tasks independently and filters only on each task's own status. Tasks cannot themselves be cancelled, so without a containment rule a cancelled slice (or a cascaded cancelled phase) would leak its still-`ready`/`in_progress` child tasks into `tasktool list --open`. The implementation must add a containment rule to `cmd_list`'s task iteration: **skip every task whose parent slice's status `is_terminal()`**. This covers both `done` (already implicitly handled by users closing slices) and `cancelled` parents. Same containment rule applies anywhere else `_iter_items` is consumed for "open" reporting; the plan must audit `commands.py:1571-1577` and adjacent consumers.
  - The task row data is preserved verbatim — no status mutation on child tasks during slice cancellation. The suppression is purely report-side; `tasktool show <slice-id>` still displays the child task rows with their own statuses unchanged.
  - The plan must add tests: (a) `tasktool list --open` after `tasktool cancel <slice-id>` does not include the slice's child tasks; (b) the same after `tasktool cancel <phase-id> --cascade` for every cascaded slice's child tasks; (c) `tasktool show <slice-id>` on the cancelled slice still shows the tasks with their pre-cancel statuses.
- `brief` and `show`, when the row's status is `cancelled`, surface the cancellation reason at the top of the output. Implementation: scan `notes` for lines beginning with `Cancelled ` followed by an ISO-8601 timestamp and `: `; emit the first such block. If absent, fall back to the last non-empty line of `notes`. No structured parsing beyond the prefix.
- **Active vs archived rows.** Today `_find_item()` at `commands.py:532-539` only looks up active rows, so `tasktool show X22` against an auto-archived X returns "not found in active tasklist". The reason-surfacing rule applies **only to active rows** — slices and phases (which never auto-archive), and X-items created with `tasktool cancel <x-id> --no-archive`. For X-items archived as part of cancellation, the operator must read the archive markdown file (path is recorded in `archived_cross_cutting`) — the spec does not require teaching `show`/`brief` to read archives. The implementation plan must add a test asserting (a) active cancelled rows surface the reason, and (b) `show <x-id>` against an archived cancelled X returns the existing not-found error unchanged.
- `importer.EMOJI_TO_STATUS` adds the `🚫 → CANCELLED` entry so rendered markdown round-trips.

### Validation

- `validate.py` requires a `closed` date for any row whose status `is_terminal()` (currently only required for `DONE`). Update lines 73, 87, 121, 134 accordingly and refresh the error message text from `status=done requires closed date` to `status=<status> requires closed date`.
- Tasks with `status="cancelled"` must fail JSON-schema validation. Plan must include a test for this.

### Notifications

`notify.py tasktool-status` already accepts a STATUS argument and constructs a generic event message of shape `<id> <status>: <title>` (`notify.py:362-370`); playback prefers TTS, falling back to a generic `tasktool` ding (`notify.py:247-253`). There is no per-status audio cue today and this spec does not add one.

The implementation:

- Wires `cmd_cancel` to call the existing `tasktool-status` notifier path with `status="cancelled"`.
- Relies on the generic message format — the event payload becomes `X22 cancelled: <title>`, which TTS will speak verbatim. No title-prefix mutation, no special-case audio.
- The plan must add a test asserting the notifier is invoked with `status="cancelled"` exactly once per `cancel` call (and per cascaded child during phase cascade).

**`archive-phase` notification fix.** `commands.py:1857` today hard-codes `_notify_status(..., status=Status.DONE, ...)` after archiving a phase. With cancelled phases reaching `archive-phase` (per the rules above), this would emit a misleading "done" event for work that was explicitly cancelled. The implementation must:

- Read the phase's actual status at notify time and pass it through (`Status.DONE` for shipped phases, `Status.CANCELLED` for cancelled phases).
- Add a test asserting that archiving a cancelled phase emits a notifier event with `status="cancelled"`, never `status="done"`.

### Skill text updates

`skills/tasklist-discipline/SKILL.md` updates:

- Status enum line: add `cancelled` alongside `done` with a one-line explanation.
- Daily-commands table: insert `tasktool cancel <id> --reason "..."` with `--cascade` (phase) and `--no-archive` (X) notes.
- Red-flags table: add row "I'll mark this slice `done` to make it disappear" → "Use `cancel`, not `close`. `done` is a lie if the work never shipped."
- A new short section "Cancellation" explaining the dep-satisfaction rule (cancelled does not satisfy `depends_on`) and the cascade behavior for phases.

## Edge cases and risks

- **Existing tasklists in the wild without `cancelled`**: schema is forward-compatible — old data has no `cancelled` rows and parses fine. Reading a future tasklist with `cancelled` on an old tasktool would fail JSON-schema validation; this is acceptable since this is a personal fork and the bump version of the plugin advertises the change.
- **A row marked `cancelled` that also has `started=null`**: allowed. A slice can be cancelled before it ever started (deferred without beginning). Validation only requires `closed >= created`; `started` remains optional. Plan must add a test.
- **`tasktool deps --remove`** on a cancelled dep: today's behavior already works; cancelled deps remain real planning edges until removed.
- **Concurrent cancel under authoritative-checkout routing**: routes through the same shared lock as `close`/`set`. No new concurrency surface.
- **Re-running `tasktool cancel` on the same id**: refused (already terminal); operator sees clear error.

## Test plan (for the implementation plan to expand)

Behavior:

- Status enum extended; round-trips through serialize/deserialize/JSON schema.
- `tasktool cancel <slice-id> --reason "scope dropped"` stamps status, `closed` (date), and notes audit line of shape `Cancelled <ISO-ts>: scope dropped`.
- `tasktool cancel <slice-id>` (no reason) errors.
- `tasktool cancel <slice-id> --reason ""` errors.
- `tasktool cancel <phase-id>` with open slices errors with the slice list.
- `tasktool cancel <phase-id>` with all-terminal slices (mix of done + cancelled) succeeds without `--cascade`.
- `tasktool cancel <phase-id> --cascade` cancels open slices with `(cascaded from <phase-id>)` suffix, leaves done slices, stamps phase.
- `tasktool cancel <x-id>` auto-archives by default; archive markdown records `status: cancelled`.
- `tasktool cancel <x-id> --no-archive` keeps visible; subsequent `tasktool archive-cross <x-id>` succeeds and preserves `status: cancelled` in the archive.
- `tasktool cancel <slice-id>` without `started` succeeds (a slice can be cancelled before it ever started); `closed` is set, `started` remains null.

Rejections:

- `tasktool set --status cancelled` errors with hint pointing to `tasktool cancel`.
- `tasktool set --status ready|in_progress|done` on a cancelled row errors.
- `tasktool close <id>` on a cancelled row errors.
- `tasktool start <slice-id>` on a cancelled row errors.
- `tasktool block <slice-id>` / `unblock <slice-id>` on a cancelled row errors.
- `tasktool cancel <task-id>` errors with the "cancel does not apply to tasks" message.
- `tasktool list --open` after `tasktool cancel <slice-id>` omits the slice's child tasks (no leak through the task iteration path).
- `tasktool list --open` after `tasktool cancel <phase-id> --cascade` omits every cascaded slice's child tasks.
- `tasktool show <slice-id>` on a cancelled slice still emits its child task rows with their pre-cancel statuses (no mutation, only report-side suppression in `list --open`).
- `tasktool deps <slice-id> --add` / `--remove` on a cancelled row errors.
- `tasktool ratify <slice-id>` on a cancelled row errors.

Allowed on cancelled rows:

- `tasktool note <id> --append "<text>"` succeeds.
- `tasktool note <id> --replace "<text>"` on a cancelled row errors, with a hint pointing to `--append`.
- `tasktool ref <id> --add <path>` succeeds.
- `tasktool title <id> "<new>"` succeeds.

Gate and archive:

- `tasktool archive-phase <p-id>` accepts a cancelled phase with all-terminal slices and skips the post-phase review gate (notes record the skip).
- `tasktool archive-phase <p-id>` refuses a cancelled phase that still has open slices.

Dependencies:

- `_done_slice_ids` returns only `done` ids (cancelled excluded).
- `schedule` JSON includes `cancelled_deps` for affected slices; `waiting_on` excludes cancelled deps; `ready` is `false` when either list is non-empty.
- `schedule` text rendering includes the `cancelled_deps=` segment.
- `ready-slices` omits any slice with non-empty `cancelled_deps`.

Validation:

- Task JSON with `status="cancelled"` fails JSON-schema validation.
- `_check_task()` rejects a `Task(status=Status.CANCELLED)` even when `closed` is set.
- Cancelled slice/phase/X row with no `closed` date fails validation.
- Cancelled row with `closed < created` fails validation.

Render and import:

- `STATUS_EMOJI[Status.CANCELLED] == "🚫"`.
- `list --open` excludes cancelled rows.
- `brief` / `show` surface the cancellation reason at the top of the output for active cancelled rows; render falls back to the last notes line when no `Cancelled <ts>:` prefix is present.
- `show <x-id>` against an archived cancelled X returns the existing not-found error unchanged (no archive-read support added).
- Importer round-trips `🚫` ↔ `Status.CANCELLED`, including the date tag.

Notification:

- `cmd_cancel` invokes the `tasktool-status` notifier exactly once per call with `status="cancelled"`; once per cascaded child during phase cascade.
- `archive-phase` on a cancelled phase emits a notifier event with `status="cancelled"` (not `"done"`).

## Open questions

None at time of writing. All product decisions are locked above.

## References

- `tools/tasktool/model.py` — `Status` enum
- `tools/tasktool/schema_gen.py` — JSON schema generation
- `tools/tasktool/commands.py` — close, set, start, archive-phase, schedule, ready-slices
- `tools/tasktool/validate.py` — date and status-stamp validation
- `tools/tasktool/render.py`, `importer.py` — markdown emit and round-trip
- `skills/tasklist-discipline/SKILL.md` — skill prose
