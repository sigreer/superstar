# P2 — tasktool: JSON-backed task management CLI

**Status:** implemented (P2.S1, P2.S2, P2.S3 closed; post-phase review in progress 2026-05-18)
**Author:** Simon Greer (with AI brainstorming)
**Date:** 2026-05-17
**TASKLIST entry:** `P2` in [`docs/tasklist.json`](../tasklist.json) — view via `tasktool show P2`

## 1. Problem

`docs/TASKLIST.md` was the canonical project tracker in superstar's workflow before this phase. The format was enforced by prose (the `tasklist-discipline` skill), not by code:

- Stable P/S/T/X IDs, never renumbered.
- Status emoji set (`✅` / `🚧` / `⏸` / `☐`) paired with status tags (`DONE YYYY-MM-DD`, `IN PROGRESS`, `BLOCKED on …`, `READY`).
- Specific date format, specific filename conventions, specific close-in-place / phase-archive rules.

Two consequences:

1. **Brittleness for downstream consumers.** The AGS sidebar, external reviewers, and any future dashboards have to re-parse a hand-edited markdown file whose shape is enforced only by an LLM following a skill. A single stray emoji or missing date breaks the consumer.
2. **Context bloat for agents.** The current pattern is "agent reads the entire TASKLIST.md to orient." Most of that content is irrelevant to the agent's current task. The agent absorbs the whole file because targeted queries do not exist.

Conformity is enforced by repeatedly reminding agents of the rules. This works imperfectly and consumes context every time.

## 2. Goals

- **Eliminate hand-editing of the canonical tracker.** All mutations go through a single CLI that validates inputs at write time.
- **Reduce agent context burden.** Replace "read the whole file" with targeted queries (`tasktool brief <id>`, `tasktool show <id>`, `tasktool list --status open`).
- **Produce reliable structured data for downstream tools** (AGS sidebar, reviewers, future dashboards) without forcing them to re-parse markdown.
- **Preserve the existing mental model** (phases / slices / tasks / cross-cutting; stable IDs; close-in-place; phase archive; status gates).
- **Stay zero-dependency.** Python stdlib only. No package install required at the project level — a global shim points at this repo.

## 3. Non-goals

- **Cross-project querying.** Each project keeps its own JSON; there is no central store. AGS can read multiple per-project JSONs if it wants a cross-project view.
- **External-system sync.** No Linear, Jira, GitHub Projects integration. Out of scope.
- **Web UI.** Out of scope. The AGS sidebar is the user-facing view; the CLI is the agent-facing view.
- **Concurrent multi-writer correctness.** Single-user, single-machine. File-level write is atomic via tempfile + rename; no locking beyond that.
- **Backwards compatibility with the markdown shape.** `tasktool render` produces a readable markdown view but is not constrained to byte-match the prior hand-written format.

## 4. Approach summary

A Python stdlib CLI (`tasktool`) reads and writes a per-project `docs/tasklist.json`. The CLI is the only sanctioned mutation path; the `tasklist-discipline` skill is rewritten to teach the commands rather than the rules. A pre-commit hook enforces that `docs/tasklist.json` only changes via the CLI. The existing `docs/TASKLIST.md` is parsed by a one-shot importer and then deleted; downstream readers (AGS sidebar) consume the JSON directly or import the Python module.

## 5. Architecture

### 5.1 Code location & distribution

- **Source:** `tools/tasktool/` in the superstar repo. Single Python package; entry point `tools/tasktool/__main__.py`.
- **Stdlib only:** `argparse`, `json`, `pathlib`, `dataclasses`, `datetime`, `re`, `sys`, `os`, `subprocess` (for git-staging the JSON after writes), `unittest`.
- **Global shim:** `~/.local/bin/tasktool` — one-line script: `exec python3 /home/simon/Dev/sigreer/skills/superstar/tools/tasktool/__main__.py "$@"`. Installed once per machine by `tools/tasktool/install.sh`. The installer is idempotent; it errors if a different shim already exists at the target path unless `--force` is passed.
- **No per-project install step.** Projects need only the per-project `docs/tasklist.json` and (optionally) the pre-commit hook.

### 5.2 Per-project state

- **`docs/tasklist.json`** — canonical, git-tracked.
- **No committed markdown.** `tasktool render` writes a markdown view to stdout on demand. The output is suitable for piping into a temp file for review or pasting into a PR description.
- **Schema version field** in the JSON enables future migrations.

### 5.3 Integration with consumers

- **AGS sidebar (Python):** `import tasktool` directly. The installer adds the package to a known site-packages-equivalent path (or symlinks). Functions like `load_project(path)`, `brief(project, id)` are exposed.
- **Other tools:** read `docs/tasklist.json` directly, validated against the schema emitted by `tasktool schema`.
- **External reviewer / skills:** call `tasktool render`, `tasktool show`, `tasktool brief` as needed.

## 6. Data model

### 6.1 Top-level shape (`docs/tasklist.json`)

```json
{
  "schema_version": 1,
  "project": "superstar",
  "north_star": "Optional one-paragraph project intent.",
  "last_reviewed": "2026-05-17",
  "phases": [ /* Phase[] */ ],
  "cross_cutting": [ /* CrossCuttingItem[] */ ],
  "archived_phases": [ /* { id, title, archived_path, archived_date } */ ]
}
```

### 6.2 Phase

```json
{
  "id": "P2",
  "title": "tasktool: JSON-backed task management CLI",
  "status": "in_progress",
  "created": "2026-05-17",
  "closed": null,
  "spec_path": "docs/specs/2026-05-17-P2-tasktool-design.md",
  "plan_path": null,
  "phase_reviewer_chain": null,
  "notes": "",
  "slices": [ /* Slice[] */ ]
}
```

### 6.3 Slice

```json
{
  "id": "S1",
  "title": "CLI core",
  "status": "ready",
  "created": "2026-05-17",
  "closed": null,
  "blocked_on": null,
  "plan_path": null,
  "refs": [],
  "notes": "",
  "reviewer_chain": null,
  "tasks": [ /* Task[] */ ]
}
```

- `id` is the short form within its phase (`S1`, `S5a`).
- Follow-up slices use a letter suffix (`S5a`); the suffix is part of the ID string. Ordering within `slices[]` is execution order; ID order is creation order.
- `blocked_on` is `null` or `{ "kind": "id" | "external", "value": "P2.S1" | "vendor X" }`.
- `reviewer_chain` is the relative path to the post-slice reviewer chain folder once one exists.

### 6.4 Task

```json
{
  "id": "T1",
  "title": "Implement data model module",
  "status": "ready",
  "created": "2026-05-17",
  "closed": null,
  "refs": [],
  "notes": ""
}
```

Inline follow-ons that used to be unstructured bullets become first-class tasks with their own `T{n}` IDs.

### 6.5 Cross-cutting

```json
{
  "id": "X1",
  "title": "...",
  "status": "ready",
  "created": "...",
  "closed": null,
  "refs": [],
  "notes": ""
}
```

### 6.6 Status enum

`done | in_progress | blocked | ready`

Stored as a plain string. Emoji is a render concern. `done` requires a non-null `closed` date (validator enforces).

**Blocking is slice-scoped.** Only slices carry `blocked_on` and may take status `blocked`. Phases, tasks, and cross-cutting items use `ready | in_progress | done` only. Rationale: at the granularity of phases and tasks, "blocked" conflates with "waiting" and "deferred" without adding signal; at the slice boundary it has a clear meaning (a unit of work that cannot proceed until another finishes). The validator rejects `blocked` status on phases/tasks/cross-cutting and rejects a non-null `blocked_on` on the same. The `tasktool block` / `unblock` commands accept only slice IDs and error otherwise.

### 6.7 Dates

ISO 8601 date (`YYYY-MM-DD`). `closed` is auto-stamped to today at the moment of status→done; the user can backdate via `--closed-date YYYY-MM-DD`. `created` is auto-stamped at create time and is read-only thereafter (no `tasktool` command edits it; raw-edit escape hatch only).

### 6.8 Fully-qualified IDs

Stored as short form (`S2`, `T1`); fully-qualified form (`P2.S1.T1`) is derived for display and CLI arguments. The CLI accepts both forms in arguments; ambiguous short forms (e.g., `S1` without a phase context) are rejected with a clear error.

### 6.9 Validation rules

- ID format: `P\d+`, `S\d+[a-z]?`, `T\d+`, `X\d+`.
- IDs unique within their scope.
- `done` requires `closed != null`.
- `blocked` requires `blocked_on != null`.
- `closed >= created` when both set.
- `spec_path`, `plan_path`, `refs[]` are checked for filesystem existence by `tasktool validate` (warning, not error, since paths may be deleted in branches).
- `reviewer_chain` directory must exist at slice close time when post-slice review is required.

## 7. CLI surface

Conventions: arguments named `<id>` accept fully-qualified (`P2.S1`) or short form when unambiguous. Mutating commands write atomically (tempfile + rename) and `git add` the file (best-effort; non-fatal if not a git repo).

### 7.1 Lifecycle

```
tasktool init [--project NAME] [--north-star TEXT]
    Create empty docs/tasklist.json. Errors if file exists unless --force.

tasktool import PATH_TO_TASKLIST_MD [--dry-run]
    One-shot migration from existing TASKLIST.md. Prints unparsed lines as warnings.
    --dry-run prints the JSON it would write without touching disk.

tasktool schema
    Emit the JSON Schema for tasklist.json to stdout.
```

### 7.2 Create

```
tasktool create phase --title TEXT [--spec PATH] [--plan PATH]
    Allocates next P{n}, taking the orphan-aware max+1 across the file plus docs/specs/, docs/plans/, docs/reviewer/ filename prefixes. Prints the new ID.

tasktool create slice <phase-id> --title TEXT [--follow-up <slice-id>] [--plan PATH]
    Allocates next S{n} under the given phase; with --follow-up <Sn>, allocates Sn+next-letter.

tasktool create task <slice-id> --title TEXT

tasktool create cross --title TEXT
    Allocates next X{n}.
```

### 7.3 Mutate

```
tasktool set <id> --status (ready|in_progress|done) [--reviewer-chain PATH] [--skip-review-gate]
    Validates transition. For tasks and cross-cutting items, --status done auto-stamps
    closed and writes immediately. For slices and phases, --status done routes through
    the same review-gate machinery as `close` / `archive-phase` (§8.2) — the gate cannot
    be bypassed by reaching for `set` instead of `close`. **Implementation note:**
    `blocked` is deliberately not a value of `set --status`; routing all block/unblock
    transitions through `tasktool block` / `tasktool unblock` keeps the dependency
    metadata (`blocked_on`, audit trail) under a single command surface (§6.6).

tasktool close <id> [--refs PATH[,PATH...]] [--closed-date YYYY-MM-DD] [--note TEXT]
                    [--reviewer-chain PATH] [--skip-review-gate]
    Convenience: sets status=done, stamps closed (today by default), appends refs and note.
    Enforces the review gate (§8.2) for slice and phase IDs; see that section for behaviour and overrides.

tasktool block <slice-id> --on (<slice-id>|external:TEXT)
    Slices only. Errors on phase, task, or cross-cutting IDs.

tasktool unblock <slice-id>
    Clears blocked_on, sets status back to ready (or in_progress if --resume). Slices only.

tasktool note <id> --append TEXT | --replace TEXT

tasktool ref <id> (--add PATH | --remove PATH)

tasktool title <id> --set TEXT

tasktool archive-phase <phase-id> [--reviewer-chain PATH] [--skip-review-gate]
    Refuses unless every slice in the phase is done AND the phase's post-phase review gate
    is satisfied (§8.2). Moves the phase to archived_phases[] and writes a markdown summary
    (with the full phase JSON in a fenced code block, to enable a future tasktool unarchive)
    to docs/archived-tasks/P{n}-<slug>.md.
```

### 7.4 Read

```
tasktool show <id>
    Full detail for one item.

tasktool brief <id>
    The "start-of-work primer". For a slice: slice detail + parent phase summary + sibling slice statuses + open tasks in this slice. For a phase: phase summary + slice statuses. This is what agents call instead of reading the whole file.

tasktool list [--phase <id>] [--status STATE[,STATE]] [--kind slice|task|cross|phase] [--open] [--format text|json]
    Filtered listing. --open is shorthand for --status ready,in_progress,blocked.

tasktool render [--format markdown]
    Emit the full markdown view to stdout. Approximates the old TASKLIST.md shape; not byte-identical.

tasktool next-id (--kind phase | --kind slice --phase <id> | --kind task --slice <id> | --kind cross)
    Print what ID the next create would allocate. Used by external tools (e.g., reviewer chain folder creation that needs an ID before the artifact exists).

tasktool validate [--format text|json] [--strict-format] [--normalise]
    Runs all validation rules. Exit 0 on clean, 1 on errors. Findings as text or JSON.
    --strict-format additionally checks that the file is byte-for-byte identical to the
    canonical serialisation (§8.1) — used by the pre-commit hook.
    --normalise rewrites the file into canonical format after successful validation —
    used by the TASKTOOL_RAW=1 editor workflow (§8.3) to make a hand-edited file
    hook-acceptable.
```

### 7.5 Global flags

- `--project-root PATH` — defaults to walking up from cwd for `docs/tasklist.json`.
- `--quiet` / `--verbose`.
- `--no-stage` — skip `git add` after write.

## 8. Enforcement

### 8.1 Pre-commit hook

Installed per-project; template lives at `tools/tasktool/templates/pre-commit-tasktool`.

Behaviour:

1. If `docs/tasklist.json` is staged, check that the file matches the CLI's canonical serialisation of its own content:
   - Mechanism: `tasktool validate --strict-format`. This loads the JSON, re-serialises it with the CLI's canonical formatter (UTF-8, `json.dumps(..., indent=2, sort_keys=True, ensure_ascii=False)` plus a single trailing newline), and compares byte-for-byte against the file on disk. Mismatch → exit non-zero. The file remains pure JSON at all times — no embedded sentinels — preserving the direct-consumer contract in §5.3.
   - The CLI's write path uses the same canonical formatter, so any file produced by `tasktool` passes the check trivially.
   - Escape hatch: `TASKTOOL_RAW=1 $EDITOR docs/tasklist.json && tasktool validate --normalise` rewrites the edited file through the canonical formatter, after which the hook accepts it. The escape hatch is the user explicitly choosing to normalise; there is no bypass that lets non-canonical bytes through.
2. Always run `tasktool validate --format json` (full validation, not just format). Non-zero exit blocks the commit; output is printed verbatim.

### 8.2 Review-gate enforcement (close & archive-phase)

`tasktool` enforces the post-slice and post-phase external-review gates, not just data integrity. This is a deliberate scope expansion past "data validator" — without it, the skill-prose gate is bypassable simply by calling `tasktool close` without running `external-review` first, and the conformity win is incomplete.

**Slice close (`tasktool close <slice-id>`):**

1. Resolve the post-slice reviewer chain folder:
   - If `--reviewer-chain PATH` is given, use it.
   - Otherwise, auto-discover: `docs/reviewer/<slice-id-dotless>-post-slice/` or any folder under `docs/reviewer/` whose name matches the slice ID and ends in `-post-slice`. Multiple matches → error; zero matches → error (unless `--skip-review-gate`).
2. Read `chain.json` from the chain folder. Refuse unless the latest round's `merged_verdict` (falling back to primary `verdict` if no merge) is `ready` or `ready with small edits`.
3. On success, persist the chain folder path into the slice's `reviewer_chain` field.
4. `--skip-review-gate` bypasses steps 1–3 with a stderr warning ("review gate skipped for <id>"). Recorded in the slice's `notes` field with a timestamp so the bypass is auditable.

**Phase archive (`tasktool archive-phase <phase-id>`):**

1. Refuse unless every slice in the phase has `status: done`.
2. Resolve the post-phase reviewer chain folder (same discovery rules with suffix `-post-phase`; field on Phase is `phase_reviewer_chain`).
3. Refuse unless the latest round's verdict is `ready` or `ready with small edits`.
4. `--skip-review-gate` behaves as above; the bypass is recorded in the archive's notes.

**The data model adds a `phase_reviewer_chain` field on Phase** (mirrors `reviewer_chain` on Slice). Update §6.2 accordingly when implementing.

The CLI is now the single chokepoint for both data shape and workflow gating. The `tasklist-discipline` skill no longer needs to remind agents "run external-review before close" — `tasktool close` will refuse without it.

### 8.3 No raw-edit subcommand

The CLI intentionally exposes no `tasktool edit --raw` or similar. The friction-ful path for emergency hand-edits is `TASKTOOL_RAW=1 $EDITOR docs/tasklist.json && tasktool validate --normalise` (re-canonicalises the edited file so the hook accepts it). `TASKTOOL_RAW=1` is not a hook bypass — see §8.1 — it is a flag for the editor convenience workflow that signals the user is intentionally editing raw JSON. The hook still demands canonical bytes either way. This is by design: removing a low-friction path keeps agents on the sanctioned commands.

## 9. Skill integration

### 9.1 `tasklist-discipline` rewrite

The skill shrinks substantially. Replaces prose-encoded rules with:

- A short conceptual primer (phases / slices / tasks / cross-cutting; stable IDs; close-in-place; phase archive).
- A command cheatsheet pointing at `tasktool --help` for full surface.
- The gating concepts (post-slice / post-phase external review before close). The rules themselves move into the CLI — `tasktool close` and `archive-phase` refuse without a passing reviewer chain (§8.2). The skill describes *why* the gate exists; the CLI enforces it.
- The agent's start-of-work primer call: "Run `tasktool brief <id>` when entering a slice; do not read the JSON directly."

Removed from the skill: ID-allocation prose (CLI does it), status emoji/tag table (render concern), date format rules (CLI does it), the orphan-scan procedure (`tasktool next-id` does it).

### 9.2 Sibling skill touch-ups

Skills that reference `docs/TASKLIST.md` get small edits:

- `writing-plans` — references `tasktool show <phase-id>` for context; embeds slice IDs in plan filenames as today.
- `external-review` — passes `docs/tasklist.json` (or `tasktool render` output) as `--context` for spec / plan / post-slice / post-phase reviews.
- `project-setup` — runs `tasktool init` instead of scaffolding TASKLIST.md from the template, and installs the pre-commit hook.
- `brainstorming` — calls `tasktool show` / `tasktool brief` instead of telling the agent to read TASKLIST.md.
- `subagent-driven-development` — calls `tasktool close <slice-id>` at slice end; calls `tasktool archive-phase` at phase end.

## 10. Migration plan (for this repo)

1. Land CLI core (S1) with `init`, `create`, `set`, `close`, `show`, `list`, `validate`, `schema` and a test suite.
2. Land `import`, `render`, `brief` (S2).
3. Run `tasktool import docs/TASKLIST.md`. Diff `tasktool render` output against the original markdown; fix parser/data until the diff is acceptable (semantic equivalence, not byte-identity).
4. `git rm docs/TASKLIST.md`. Commit `docs/tasklist.json` plus the pre-commit hook.
5. Rewrite `tasklist-discipline` skill (S3). Touch up sibling skills' references.
6. Run the full suite of skills against a synthetic task (e.g., add a trivial cross-cutting item, close a slice) to verify the workflow end-to-end.

For other projects: same sequence after the global shim is installed.

## 11. Testing

- **Unit tests** for the data model, validators, ID allocation, status transitions, parsers. Stdlib `unittest`.
- **CLI integration tests** that invoke `tasktool` as a subprocess against a temp directory; assert exit codes, stdout, and resulting JSON state.
- **Importer fixture tests**: a handful of real-world TASKLIST.md examples (this repo's once it exists, plus a synthetic edge-case file with all emoji/status combinations) round-trip through `import` → `render` and the output is compared for semantic equivalence.
- **Hook test**: synthetic git repo with the hook installed; commits with non-canonical bytes in `docs/tasklist.json` are rejected; commits via the CLI succeed; `TASKTOOL_RAW=1 ... && tasktool validate --normalise` round-trip produces a hook-passing commit.

## 12. Risks & open questions

- **Risk: AGS sidebar Python import path.** Depends on how the installer makes `tasktool` importable. **Resolved (post-implementation, 2026-05-18):** `tools/tasktool/install.sh` installs a shim at `~/.local/bin/tasktool` and exposes the package via `PYTHONPATH=tools/`. AGS widgets that want in-process access can do `sys.path.insert(0, '<repo>/tools'); import tasktool.commands as t; t.load_project(...)`. The shim path also satisfies CLI consumers.
- **Risk: agents bypass the CLI by editing JSON directly anyway.** The hook catches commits but not in-session edits. **Mitigation in place:** P2.S3 installed a per-project pre-commit hook (`tools/tasktool/templates/pre-commit-tasktool`) that refuses non-canonical bytes, orphan spec/plan filenames, and any commit that touches `docs/TASKLIST.md`. In-session edits remain possible but cannot land on disk via git without normalisation.
- **Open question: AGS read API.** Is `import tasktool; tasktool.brief(...)` the right surface, or should AGS shell out to the `tasktool` CLI? **Deferred to AGS integration work (out of scope for P2):** in-process callers can use `commands.cmd_brief` / `commands.cmd_show`; shell-out callers can use `tasktool brief <id>` (text) or read `docs/tasklist.json` directly (it is canonical JSON). A future `--format json` flag for `brief` itself is intentionally not on this phase's surface — add when an AGS widget actually needs it.

## 13. Acceptance

The spec is acceptance-ready when:

- All major design choices above are settled (architecture, data model, CLI surface, enforcement, skill integration).
- Open questions in §12 are either resolved or explicitly deferred to the plan.
- External reviewer verdict is `ready` or `ready with small edits`.
