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
post-phase

Review mode:
Post-phase review. Treat this as a closeout gate for a whole
phase. Compare the implementation, archive/TASKLIST updates, and verification
evidence against the phase spec/plan. Prioritize: unresolved acceptance
criteria, stale docs, missing archive notes, cross-cutting tracker drift,
deferred gates without justification, and regressions outside the phase scope.

Target document:
docs/specs/2026-05-17-P2-tasktool-design.md

Additional context files:
- docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md
- docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md
- docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md
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
  201	    Allocates next S{n} under the given phase; with --follow-up <Sn>, allocates Sn+next-letter.
  202	
  203	tasktool create task <slice-id> --title TEXT
  204	
  205	tasktool create cross --title TEXT
  206	    Allocates next X{n}.
  207	```
  208	
  209	### 7.3 Mutate
  210	
  211	```
  212	tasktool set <id> --status (ready|in_progress|blocked|done) [--reviewer-chain PATH] [--skip-review-gate]
  213	    Validates transition. For tasks and cross-cutting items, --status done auto-stamps
  214	    closed and writes immediately. For slices and phases, --status done routes through
  215	    the same review-gate machinery as `close` / `archive-phase` (§8.2) — the gate cannot
  216	    be bypassed by reaching for `set` instead of `close`. `blocked` is rejected on
  217	    non-slice IDs (§6.6).
  218	
  219	tasktool close <id> [--refs PATH[,PATH...]] [--closed-date YYYY-MM-DD] [--note TEXT]
  220	                    [--reviewer-chain PATH] [--skip-review-gate]
  221	    Convenience: sets status=done, stamps closed (today by default), appends refs and note.
  222	    Enforces the review gate (§8.2) for slice and phase IDs; see that section for behaviour and overrides.
  223	
  224	tasktool block <slice-id> --on (<slice-id>|external:TEXT)
  225	    Slices only. Errors on phase, task, or cross-cutting IDs.
  226	
  227	tasktool unblock <slice-id>
  228	    Clears blocked_on, sets status back to ready (or in_progress if --resume). Slices only.
  229	
  230	tasktool note <id> --append TEXT | --replace TEXT
  231	
  232	tasktool ref <id> (--add PATH | --remove PATH)
  233	
  234	tasktool title <id> --set TEXT
  235	
  236	tasktool archive-phase <phase-id> [--reviewer-chain PATH] [--skip-review-gate]
  237	    Refuses unless every slice in the phase is done AND the phase's post-phase review gate
  238	    is satisfied (§8.2). Moves the phase to archived_phases[] and writes a markdown summary
  239	    (with the full phase JSON in a fenced code block, to enable a future tasktool unarchive)
  240	    to docs/archived-tasks/P{n}-<slug>.md.
  241	```
  242	
  243	### 7.4 Read
  244	
  245	```
  246	tasktool show <id>
  247	    Full detail for one item.
  248	
  249	tasktool brief <id>
  250	    The "start-of-work primer". For a slice: slice detail + parent phase summary + sibling slice statuses + open tasks in this slice. For a phase: phase summary + slice statuses. This is what agents call instead of reading the whole file.
  251	
  252	tasktool list [--phase <id>] [--status STATE[,STATE]] [--kind slice|task|cross|phase] [--open] [--format text|json]
  253	    Filtered listing. --open is shorthand for --status ready,in_progress,blocked.
  254	
  255	tasktool render [--format markdown]
  256	    Emit the full markdown view to stdout. Approximates the old TASKLIST.md shape; not byte-identical.
  257	
  258	tasktool next-id (--kind phase | --kind slice --phase <id> | --kind task --slice <id> | --kind cross)
  259	    Print what ID the next create would allocate. Used by external tools (e.g., reviewer chain folder creation that needs an ID before the artifact exists).
  260	
  261	tasktool validate [--format text|json] [--strict-format] [--normalise]
  262	    Runs all validation rules. Exit 0 on clean, 1 on errors. Findings as text or JSON.
  263	    --strict-format additionally checks that the file is byte-for-byte identical to the
  264	    canonical serialisation (§8.1) — used by the pre-commit hook.
  265	    --normalise rewrites the file into canonical format after successful validation —
  266	    used by the TASKTOOL_RAW=1 editor workflow (§8.3) to make a hand-edited file
  267	    hook-acceptable.
  268	```
  269	
  270	### 7.5 Global flags
  271	
  272	- `--project-root PATH` — defaults to walking up from cwd for `docs/tasklist.json`.
  273	- `--quiet` / `--verbose`.
  274	- `--no-stage` — skip `git add` after write.
  275	
  276	## 8. Enforcement
  277	
  278	### 8.1 Pre-commit hook
  279	
  280	Installed per-project; template lives at `tools/tasktool/templates/pre-commit-tasktool`.
  281	
  282	Behaviour:
  283	
  284	1. If `docs/tasklist.json` is staged, check that the file matches the CLI's canonical serialisation of its own content:
  285	   - Mechanism: `tasktool validate --strict-format`. This loads the JSON, re-serialises it with the CLI's canonical formatter (UTF-8, `json.dumps(..., indent=2, sort_keys=True, ensure_ascii=False)` plus a single trailing newline), and compares byte-for-byte against the file on disk. Mismatch → exit non-zero. The file remains pure JSON at all times — no embedded sentinels — preserving the direct-consumer contract in §5.3.
  286	   - The CLI's write path uses the same canonical formatter, so any file produced by `tasktool` passes the check trivially.
  287	   - Escape hatch: `TASKTOOL_RAW=1 $EDITOR docs/tasklist.json && tasktool validate --normalise` rewrites the edited file through the canonical formatter, after which the hook accepts it. The escape hatch is the user explicitly choosing to normalise; there is no bypass that lets non-canonical bytes through.
  288	2. Always run `tasktool validate --format json` (full validation, not just format). Non-zero exit blocks the commit; output is printed verbatim.
  289	
  290	### 8.2 Review-gate enforcement (close & archive-phase)
  291	
  292	`tasktool` enforces the post-slice and post-phase external-review gates, not just data integrity. This is a deliberate scope expansion past "data validator" — without it, the skill-prose gate is bypassable simply by calling `tasktool close` without running `external-review` first, and the conformity win is incomplete.
  293	
  294	**Slice close (`tasktool close <slice-id>`):**
  295	
  296	1. Resolve the post-slice reviewer chain folder:
  297	   - If `--reviewer-chain PATH` is given, use it.
  298	   - Otherwise, auto-discover: `docs/reviewer/<slice-id-dotless>-post-slice/` or any folder under `docs/reviewer/` whose name matches the slice ID and ends in `-post-slice`. Multiple matches → error; zero matches → error (unless `--skip-review-gate`).
  299	2. Read `chain.json` from the chain folder. Refuse unless the latest round's `merged_verdict` (falling back to primary `verdict` if no merge) is `ready` or `ready with small edits`.
  300	3. On success, persist the chain folder path into the slice's `reviewer_chain` field.
  301	4. `--skip-review-gate` bypasses steps 1–3 with a stderr warning ("review gate skipped for <id>"). Recorded in the slice's `notes` field with a timestamp so the bypass is auditable.
  302	
  303	**Phase archive (`tasktool archive-phase <phase-id>`):**
  304	
  305	1. Refuse unless every slice in the phase has `status: done`.
  306	2. Resolve the post-phase reviewer chain folder (same discovery rules with suffix `-post-phase`; field on Phase is `phase_reviewer_chain`).
  307	3. Refuse unless the latest round's verdict is `ready` or `ready with small edits`.
  308	4. `--skip-review-gate` behaves as above; the bypass is recorded in the archive's notes.
  309	
  310	**The data model adds a `phase_reviewer_chain` field on Phase** (mirrors `reviewer_chain` on Slice). Update §6.2 accordingly when implementing.
  311	
  312	The CLI is now the single chokepoint for both data shape and workflow gating. The `tasklist-discipline` skill no longer needs to remind agents "run external-review before close" — `tasktool close` will refuse without it.
  313	
  314	### 8.3 No raw-edit subcommand
  315	
  316	The CLI intentionally exposes no `tasktool edit --raw` or similar. The friction-ful path for emergency hand-edits is `TASKTOOL_RAW=1 $EDITOR docs/tasklist.json && tasktool validate --normalise` (re-canonicalises the edited file so the hook accepts it). `TASKTOOL_RAW=1` is not a hook bypass — see §8.1 — it is a flag for the editor convenience workflow that signals the user is intentionally editing raw JSON. The hook still demands canonical bytes either way. This is by design: removing a low-friction path keeps agents on the sanctioned commands.
  317	
  318	## 9. Skill integration
  319	
  320	### 9.1 `tasklist-discipline` rewrite
  321	
  322	The skill shrinks substantially. Replaces prose-encoded rules with:
  323	
  324	- A short conceptual primer (phases / slices / tasks / cross-cutting; stable IDs; close-in-place; phase archive).
  325	- A command cheatsheet pointing at `tasktool --help` for full surface.
  326	- The gating concepts (post-slice / post-phase external review before close). The rules themselves move into the CLI — `tasktool close` and `archive-phase` refuse without a passing reviewer chain (§8.2). The skill describes *why* the gate exists; the CLI enforces it.
  327	- The agent's start-of-work primer call: "Run `tasktool brief <id>` when entering a slice; do not read the JSON directly."
  328	
  329	Removed from the skill: ID-allocation prose (CLI does it), status emoji/tag table (render concern), date format rules (CLI does it), the orphan-scan procedure (`tasktool next-id` does it).
  330	
  331	### 9.2 Sibling skill touch-ups
  332	
  333	Skills that reference `docs/TASKLIST.md` get small edits:
  334	
  335	- `writing-plans` — references `tasktool show <phase-id>` for context; embeds slice IDs in plan filenames as today.
  336	- `external-review` — passes `docs/tasklist.json` (or `tasktool render` output) as `--context` for spec / plan / post-slice / post-phase reviews.
  337	- `project-setup` — runs `tasktool init` instead of scaffolding TASKLIST.md from the template, and installs the pre-commit hook.
  338	- `brainstorming` — calls `tasktool show` / `tasktool brief` instead of telling the agent to read TASKLIST.md.
  339	- `subagent-driven-development` — calls `tasktool close <slice-id>` at slice end; calls `tasktool archive-phase` at phase end.
  340	
  341	## 10. Migration plan (for this repo)
  342	
  343	1. Land CLI core (S1) with `init`, `create`, `set`, `close`, `show`, `list`, `validate`, `schema` and a test suite.
  344	2. Land `import`, `render`, `brief` (S2).
  345	3. Run `tasktool import docs/TASKLIST.md`. Diff `tasktool render` output against the original markdown; fix parser/data until the diff is acceptable (semantic equivalence, not byte-identity).
  346	4. `git rm docs/TASKLIST.md`. Commit `docs/tasklist.json` plus the pre-commit hook.
  347	5. Rewrite `tasklist-discipline` skill (S3). Touch up sibling skills' references.
  348	6. Run the full suite of skills against a synthetic task (e.g., add a trivial cross-cutting item, close a slice) to verify the workflow end-to-end.
  349	
  350	For other projects: same sequence after the global shim is installed.
  351	
  352	## 11. Testing
  353	
  354	- **Unit tests** for the data model, validators, ID allocation, status transitions, parsers. Stdlib `unittest`.
  355	- **CLI integration tests** that invoke `tasktool` as a subprocess against a temp directory; assert exit codes, stdout, and resulting JSON state.
  356	- **Importer fixture tests**: a handful of real-world TASKLIST.md examples (this repo's once it exists, plus a synthetic edge-case file with all emoji/status combinations) round-trip through `import` → `render` and the output is compared for semantic equivalence.
  357	- **Hook test**: synthetic git repo with the hook installed; commits with non-canonical bytes in `docs/tasklist.json` are rejected; commits via the CLI succeed; `TASKTOOL_RAW=1 ... && tasktool validate --normalise` round-trip produces a hook-passing commit.
  358	
  359	## 12. Risks & open questions
  360	
  361	- **Risk: AGS sidebar Python import path.** Depends on how the installer makes `tasktool` importable. Likely a symlink into a user site-packages dir, or a PYTHONPATH addition in the AGS launcher. To be confirmed during S1 against the actual AGS environment.
  362	- **Risk: agents bypass the CLI by editing JSON directly anyway.** The hook catches commits but not in-session edits. Mitigation: the skill rewrite is explicit; the validator output names what changed. Worst case, add a file-watcher or `tasktool diff` to spot un-CLI-attributed changes.
  363	- **Open question: AGS read API.** Is `import tasktool; tasktool.brief(...)` the right surface, or should AGS shell out to `tasktool brief --format json`? Probably both work; settle during S1.
  364	
  365	## 13. Acceptance
  366	
  367	The spec is acceptance-ready when:
  368	
  369	- All major design choices above are settled (architecture, data model, CLI surface, enforcement, skill integration).
  370	- Open questions in §12 are either resolved or explicitly deferred to the plan.
  371	- External reviewer verdict is `ready` or `ready with small edits`.

## Context Previews

### docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md

    1	# P2.S1 — tasktool CLI core Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Build the Python stdlib CLI core for `tasktool` — data model, canonical serializer, validation, ID allocation, reviewer-gate, and the mutation/read commands. End state: `tasktool init && tasktool create phase --title "..." && tasktool show P1` round-trips cleanly, `tasktool validate --strict-format` blocks non-canonical commits.
    6	
    7	**Architecture:** Single Python package `tools/tasktool/` (stdlib only). Layered: `ids` / `model` / `serialize` / `validate` / `allocate` / `reviewer_gate` are pure, side-effect-free modules; `commands` orchestrates them and is the only layer that touches disk-as-side-effect; `cli` is argparse glue. Tests under `tools/tasktool/tests/` use `unittest` with tmpdir fixtures.
    8	
    9	**Tech Stack:** Python 3.11+ (dataclasses, pathlib, json, argparse, datetime, re, subprocess, hashlib, unittest). Zero third-party dependencies.
   10	
   11	---
   12	
   13	## File structure
   14	
   15	Created in this slice:
   16	
   17	```
   18	tools/tasktool/
   19	├── __init__.py            # public API surface: load_project, save_project, brief, etc.
   20	├── __main__.py            # `python -m tasktool` entry; defers to cli.main()
   21	├── cli.py                 # argparse definition + dispatcher
   22	├── ids.py                 # ID regex, parse, fully-qualify, kind detection
   23	├── model.py               # dataclasses: Project, Phase, Slice, Task, CrossCutting, BlockedOn
   24	├── serialize.py           # canonical JSON load/save (sort_keys=True, indent=2, trailing \n)
   25	├── validate.py            # validation rules + strict-format + normalise
   26	├── allocate.py            # orphan-aware next-ID across TASKLIST/specs/plans/reviewer
   27	├── reviewer_gate.py       # chain folder discovery + chain.json verdict check
   28	├── commands.py            # one function per subcommand; called by cli.dispatch
   29	├── schema_gen.py          # generate JSON Schema from dataclasses
   30	├── install.sh             # idempotent installer for ~/.local/bin/tasktool shim
   31	└── tests/
   32	    ├── __init__.py
   33	    ├── test_ids.py
   34	    ├── test_model.py
   35	    ├── test_serialize.py
   36	    ├── test_validate.py
   37	    ├── test_allocate.py
   38	    ├── test_reviewer_gate.py
   39	    ├── test_commands.py
   40	    └── test_cli_integration.py
   41	```
   42	
   43	Not touched in this slice: `tools/tasktool/templates/pre-commit-tasktool` (S3), `importer.py` / `render.py` / `brief.py` (S2), any sibling skills (S3).
   44	
   45	---
   46	
   47	## Conventions used throughout
   48	
   49	- **TDD:** every task writes the failing test, runs it red, implements the minimum, runs it green, commits. Commits per task, not per step.
   50	- **Commit message prefix:** `P2.S1:` followed by an imperative one-liner.
   51	- **Run tests via:** `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`. The `tools/` directory must be on `PYTHONPATH` because the package lives at `tools/tasktool/`. Once the installer (Task 15) has been run, the shim sets `PYTHONPATH` automatically — but the raw command shown in every test gate is what an agent will run before installing.
   52	- **No third-party deps.** If you reach for `pytest`, `pydantic`, `click`, stop — stdlib only.
   53	- **Python style:** dataclasses with `slots=True`; `from __future__ import annotations` everywhere; type hints required on public functions.
   54	
   55	---
   56	
   57	## Task 1: Project skeleton + smoke test
   58	
   59	**Files:**
   60	- Create: `tools/tasktool/__init__.py`
   61	- Create: `tools/tasktool/__main__.py`
   62	- Create: `tools/tasktool/cli.py`
   63	- Create: `tools/tasktool/tests/__init__.py`
   64	- Create: `tools/tasktool/tests/test_cli_integration.py`
   65	
   66	- [ ] **Step 1: Create empty package skeleton**
   67	
   68	```python
   69	# tools/tasktool/__init__.py
   70	"""tasktool — JSON-backed task management CLI."""
   71	__version__ = "0.1.0"
   72	```
   73	
   74	```python
   75	# tools/tasktool/__main__.py
   76	from tasktool.cli import main
   77	import sys
   78	if __name__ == "__main__":
   79	    sys.exit(main(sys.argv[1:]))
   80	```
   81	
   82	```python
   83	# tools/tasktool/cli.py
   84	from __future__ import annotations
   85	
   86	def main(argv: list[str]) -> int:
   87	    if not argv or argv[0] in ("-h", "--help"):
   88	        print("tasktool — see docs/specs/2026-05-17-P2-tasktool-design.md")
   89	        return 0
   90	    print(f"tasktool: unknown command: {argv[0]}", flush=True)
   91	    return 2
   92	```
   93	
   94	```python
   95	# tools/tasktool/tests/__init__.py
   96	```
   97	
   98	- [ ] **Step 2: Write the smoke test**
   99	
  100	```python
  101	# tools/tasktool/tests/test_cli_integration.py
  102	from __future__ import annotations
  103	import subprocess
  104	import sys
  105	import unittest
  106	from pathlib import Path
  107	
  108	REPO_ROOT = Path(__file__).resolve().parents[3]
  109	PKG_DIR = REPO_ROOT / "tools"
  110	
  111	def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
  112	    import os
  113	    env = os.environ.copy()
  114	    env["PYTHONPATH"] = str(PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")
  115	    return subprocess.run(
  116	        [sys.executable, "-m", "tasktool", *args],
  117	        capture_output=True, text=True, cwd=cwd or REPO_ROOT, env=env,
  118	    )
  119	
  120	class SmokeTests(unittest.TestCase):
  121	    def test_help_prints_and_exits_zero(self):
  122	        result = run_cli("--help")
  123	        self.assertEqual(result.returncode, 0)
  124	        self.assertIn("tasktool", result.stdout)
  125	
  126	    def test_unknown_command_exits_two(self):
  127	        result = run_cli("nope")
  128	        self.assertEqual(result.returncode, 2)
  129	```
  130	
  131	- [ ] **Step 3: Run tests**
  132	
  133	Run: `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`
  134	Expected: 2 tests pass.
  135	
  136	- [ ] **Step 4: Commit**
  137	
  138	```bash
  139	git add tools/tasktool/
  140	git commit -m "P2.S1: scaffold tasktool package and smoke test"
  141	```
  142	
  143	---
  144	
  145	## Task 2: ID parsing module (ids.py)
  146	
  147	**Files:**
  148	- Create: `tools/tasktool/ids.py`
  149	- Create: `tools/tasktool/tests/test_ids.py`
  150	
  151	- [ ] **Step 1: Write failing tests**
  152	
  153	```python
  154	# tools/tasktool/tests/test_ids.py
  155	from __future__ import annotations
  156	import unittest
  157	from tasktool.ids import (
  158	    IdParseError, parse_id, fully_qualify, kind_of, is_slice_id, split_qualified,
  159	)
  160	
  161	class ParseIdTests(unittest.TestCase):
  162	    def test_phase(self):
  163	        self.assertEqual(parse_id("P2"), ("phase", "P2"))
  164	    def test_slice(self):
  165	        self.assertEqual(parse_id("S3"), ("slice", "S3"))
  166	    def test_slice_letter_suffix(self):
  167	        self.assertEqual(parse_id("S5a"), ("slice", "S5a"))
  168	    def test_task(self):
  169	        self.assertEqual(parse_id("T1"), ("task", "T1"))
  170	    def test_cross(self):
  171	        self.assertEqual(parse_id("X4"), ("cross", "X4"))
  172	    def test_qualified_phase_slice(self):
  173	        self.assertEqual(parse_id("P2.S3"), ("slice", "P2.S3"))
  174	    def test_qualified_phase_slice_task(self):
  175	        self.assertEqual(parse_id("P2.S3.T1"), ("task", "P2.S3.T1"))
  176	    def test_rejects_lowercase_phase(self):
  177	        with self.assertRaises(IdParseError):
  178	            parse_id("p2")
  179	    def test_rejects_empty(self):
  180	        with self.assertRaises(IdParseError):
  181	            parse_id("")
  182	    def test_rejects_garbage(self):
  183	        with self.assertRaises(IdParseError):
  184	            parse_id("P2..S1")
  185	
  186	class KindTests(unittest.TestCase):
  187	    def test_kind_of_short(self):
  188	        self.assertEqual(kind_of("P2"), "phase")
  189	        self.assertEqual(kind_of("S3a"), "slice")
  190	        self.assertEqual(kind_of("T1"), "task")
  191	        self.assertEqual(kind_of("X4"), "cross")
  192	    def test_kind_of_qualified(self):
  193	        self.assertEqual(kind_of("P2.S3.T1"), "task")
  194	    def test_is_slice_id(self):
  195	        self.assertTrue(is_slice_id("S3"))
  196	        self.assertTrue(is_slice_id("P2.S3a"))
  197	        self.assertFalse(is_slice_id("T1"))
  198	        self.assertFalse(is_slice_id("P2"))
  199	
  200	class QualifyTests(unittest.TestCase):

[truncated: 2947 additional lines]
### docs/plans/2026-05-17-p2-s2-tasktool-importer-render-brief-archive.md

    1	# P2.S2 — tasktool importer / render / brief / archive-phase Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
    4	
    5	**Goal:** Add the four S2 commands to `tasktool` (`import`, `render`, `brief`, `archive-phase`), then migrate this repository from `docs/TASKLIST.md` to `docs/tasklist.json`. End state: `docs/TASKLIST.md` is deleted, `docs/tasklist.json` is the canonical tracker, `tasktool render` reproduces a semantically-equivalent markdown view on demand, and `tasktool brief P2.S2` returns the start-of-work primer for the next agent that picks up work in this phase.
    6	
    7	**Architecture:** Three new pure modules under `tools/tasktool/` — `importer.py` (markdown→Project), `render.py` (Project→markdown), `brief.py` (Project→primer markdown). `commands.py` grows four new `cmd_*` functions; `cli.py` grows four subparsers. The new modules follow the S1 layering rule: pure, side-effect-free, tested in isolation; `commands` is the only disk-touching orchestrator. `archive-phase` extends `commands` with a new orchestrator that reuses `reviewer_gate.check_gate` (via `_apply_review_gate`'s `phase` branch) and adds an `ArchivedPhase` record alongside writing a markdown summary.
    8	
    9	**Tech Stack:** Python 3.11+ (stdlib only — `re`, `pathlib`, `json`, `datetime`, `argparse`, `unittest`). Zero third-party deps. Same conventions as S1.
   10	
   11	---
   12	
   13	## File structure
   14	
   15	Created in this slice:
   16	
   17	```
   18	tools/tasktool/
   19	├── importer.py             # parse TASKLIST.md → Project (best-effort, lossy-by-design)
   20	├── render.py               # Project → markdown view (not byte-identical to old TASKLIST.md)
   21	├── brief.py                # Project + id → start-of-work primer markdown
   22	└── tests/
   23	    ├── test_importer.py
   24	    ├── test_render.py
   25	    └── test_brief.py
   26	```
   27	
   28	Modified in this slice:
   29	
   30	```
   31	tools/tasktool/
   32	├── commands.py             # +cmd_import / +cmd_render / +cmd_brief / +cmd_archive_phase
   33	├── cli.py                  # +import / +render / +brief / +archive-phase subparsers
   34	├── __init__.py             # re-export importer.parse_tasklist_md, render.render_project, brief.brief
   35	└── tests/
   36	    ├── test_commands.py    # +cmd_archive_phase tests
   37	    └── test_cli_integration.py   # +import/render/brief/archive-phase CLI tests
   38	```
   39	
   40	Repo files touched at migration time (Task 11):
   41	
   42	```
   43	docs/
   44	├── tasklist.json           # NEW, canonical
   45	├── TASKLIST.md             # DELETED
   46	└── archived-tasks/         # may receive P1 summary if --archive-historical is used
   47	```
   48	
   49	Not touched in this slice: `tools/tasktool/templates/pre-commit-tasktool` (S3); any sibling skills (S3).
   50	
   51	---
   52	
   53	## Conventions used throughout
   54	
   55	- **TDD:** every task writes the failing test, runs it red, implements the minimum, runs it green, commits. Commits per task, not per step.
   56	- **Commit message prefix:** `P2.S2:` followed by an imperative one-liner.
   57	- **Run tests via:** `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`.
   58	- **No third-party deps.** Stdlib only.
   59	- **Python style:** dataclasses with `slots=True`; `from __future__ import annotations` everywhere; type hints on public functions.
   60	- **Pure modules return data; commands print/save.** `importer.parse_tasklist_md(text) -> ParseResult`, `render.render_project(p) -> str`, `brief.brief(p, qid) -> str`. None of those touch disk.
   61	- **Status emoji table** — applies *by kind*. The data model only allows `blocked` on slices (spec §6.6, enforced by `validate.py`). Importer/renderer must respect this:
   62	
   63	  | emoji | status        | extra tag suffix              | valid on   |
   64	  |-------|---------------|-------------------------------|------------|
   65	  | ✅    | `done`        | `DONE YYYY-MM-DD`             | phase/slice/task/cross |
   66	  | 🚧    | `in_progress` | `IN PROGRESS`                 | phase/slice/task/cross |
   67	  | ⏸     | `blocked`     | `BLOCKED on <text>`           | **slice only** |
   68	  | ☐     | `ready`       | `READY` / `TODO` (interchangeable on import; render emits `READY`) | phase/slice/task/cross |
   69	
   70	  **Importer rule:** a `⏸ blocked` marker on a phase or cross-cutting bullet emits a warning (`f"line {lineno}: blocked status not allowed on {kind}; coerced to ready"`) and the parser falls back to `Status.READY`. **Render rule:** `_phase_tag` and the cross-cutting render branch only emit a `BLOCKED on …` tag for slices; on a phase/cross the function returns `""` even if status somehow == blocked (the validator rejects that on save, but the renderer must also never produce invalid markdown).
   71	
   72	---
   73	
   74	## Task 1: Importer — phase header parsing
   75	
   76	**Files:**
   77	- Create: `tools/tasktool/importer.py`
   78	- Create: `tools/tasktool/tests/test_importer.py`
   79	
   80	The importer is the riskiest module because the input is hand-written markdown. We build it incrementally: phases first, then slices, then cross-cutting, then archived references. Each task adds one parser concern with fixtures.
   81	
   82	`parse_tasklist_md(text: str) -> ParseResult` returns:
   83	
   84	```python
   85	@dataclass(slots=True)
   86	class ParseResult:
   87	    project: Project           # parsed model (may be partial on errors)
   88	    warnings: list[str]        # unparsed lines / ambiguous tokens
   89	```
   90	
   91	The parser is **forgiving**: it never raises on malformed input. Anything it cannot interpret becomes a warning (line number + offending text). The caller decides whether to abort.
   92	
   93	- [ ] **Step 1: Write the failing test**
   94	
   95	```python
   96	# tools/tasktool/tests/test_importer.py
   97	from __future__ import annotations
   98	import unittest
   99	from tasktool.importer import parse_tasklist_md
  100	from tasktool.model import Status
  101	
  102	PHASE_HEADER = """\
  103	# Project Task List
  104	
  105	## P2 — tasktool: JSON-backed task management CLI 🚧 `IN PROGRESS`
  106	
  107	Spec: [`docs/specs/2026-05-17-P2-tasktool-design.md`](specs/2026-05-17-P2-tasktool-design.md). Plan: _pending_.
  108	"""
  109	
  110	PHASE_HEADER_DONE = """\
  111	## P1 — Old phase ✅ `DONE 2026-05-17`
  112	
  113	Closed; see archive.
  114	"""
  115	
  116	class TestImporterPhase(unittest.TestCase):
  117	    def test_phase_header_basic(self):
  118	        r = parse_tasklist_md(PHASE_HEADER)
  119	        self.assertEqual(len(r.project.phases), 1)
  120	        ph = r.project.phases[0]
  121	        self.assertEqual(ph.id, "P2")
  122	        self.assertEqual(ph.title, "tasktool: JSON-backed task management CLI")
  123	        self.assertEqual(ph.status, Status.IN_PROGRESS)
  124	        self.assertEqual(ph.spec_path, "docs/specs/2026-05-17-P2-tasktool-design.md")
  125	        self.assertIsNone(ph.plan_path)  # "_pending_" → None
  126	
  127	    def test_phase_done_tag_sets_closed(self):
  128	        r = parse_tasklist_md(PHASE_HEADER_DONE)
  129	        self.assertEqual(len(r.project.phases), 1)
  130	        ph = r.project.phases[0]
  131	        self.assertEqual(ph.id, "P1")
  132	        self.assertEqual(ph.status, Status.DONE)
  133	        self.assertEqual(ph.closed, "2026-05-17")  # required for validator pass
  134	```
  135	
  136	- [ ] **Step 2: Run test to verify it fails**
  137	
  138	Run: `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_importer -v`
  139	Expected: FAIL with `ModuleNotFoundError: No module named 'tasktool.importer'`.
  140	
  141	- [ ] **Step 3: Write minimal implementation**
  142	
  143	```python
  144	# tools/tasktool/importer.py
  145	from __future__ import annotations
  146	import re
  147	from dataclasses import dataclass, field
  148	from tasktool.model import Project, Phase, Status
  149	
  150	EMOJI_TO_STATUS = {
  151	    "✅": Status.DONE,
  152	    "🚧": Status.IN_PROGRESS,
  153	    "⏸": Status.BLOCKED,
  154	    "☐": Status.READY,
  155	}
  156	
  157	PHASE_HEADER_RE = re.compile(
  158	    r"^##\s+(?P<id>P\d+)\s+—\s+(?P<title>.+?)\s+"
  159	    r"(?P<emoji>[✅🚧☐])(?:\s+`(?P<tag>[^`]+)`)?\s*$"
  160	)
  161	# Phase headers may NOT use ⏸ (blocked is slice-only — spec §6.6).
  162	# A `⏸ Pn …` line matches the fallback below, which records the item
  163	# under `phases[]` with status=READY and emits an explicit warning.
  164	PHASE_HEADER_BLOCKED_RE = re.compile(
  165	    r"^##\s+(?P<id>P\d+)\s+—\s+(?P<title>.+?)\s+"
  166	    r"⏸(?:\s+`(?P<tag>[^`]+)`)?\s*$"
  167	)
  168	PHASE_DONE_TAG_RE = re.compile(r"^DONE\s+(?P<date>\d{4}-\d{2}-\d{2})$")
  169	SPEC_RE = re.compile(r"Spec:\s*\[`(?P<path>[^`]+)`\]\([^)]+\)")
  170	PLAN_RE = re.compile(r"Plan:\s*(?:\[`(?P<path>[^`]+)`\]\([^)]+\)|_pending_)")
  171	
  172	@dataclass(slots=True)
  173	class ParseResult:
  174	    project: Project
  175	    warnings: list[str] = field(default_factory=list)
  176	
  177	def _apply_phase_tag(phase: Phase, tag: str | None) -> None:
  178	    """Translate the optional `\`...\`` tag suffix into model fields."""
  179	    if not tag:
  180	        return
  181	    dm = PHASE_DONE_TAG_RE.match(tag)
  182	    if dm:
  183	        phase.closed = dm.group("date")
  184	    # `IN PROGRESS` adds no extra field beyond the emoji-derived status.
  185	    # Other tag forms are ignored (warnings are emitted elsewhere only
  186	    # for clearly-invalid statuses like blocked-on-phase).
  187	
  188	def parse_tasklist_md(text: str) -> ParseResult:
  189	    project = Project(project="<imported>", schema_version=1)
  190	    warnings: list[str] = []
  191	    current_phase: Phase | None = None
  192	    for lineno, raw in enumerate(text.splitlines(), start=1):
  193	        m = PHASE_HEADER_RE.match(raw)
  194	        if m:
  195	            current_phase = Phase(
  196	                id=m.group("id"),
  197	                title=m.group("title").strip(),
  198	                created="1970-01-01",  # placeholder; importer cannot recover real created dates
  199	                status=EMOJI_TO_STATUS[m.group("emoji")],
  200	            )

[truncated: 1232 additional lines]
### docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md

    1	# P2.S3 — Skill rewrite & pre-commit hook Implementation Plan
    2	
    3	> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.
    4	
    5	**Goal:** Replace the markdown-era `tasklist-discipline` skill with a tasktool-centric version, install a per-project pre-commit hook that enforces canonical JSON / blocks orphans / blocks `TASKLIST.md` regressions, and update every sibling skill that still references `docs/TASKLIST.md`.
    6	
    7	**Architecture:** Tasktool already owns the data and the review gates (P2.S1, P2.S2). This slice moves the *prose* layer onto the same axis: the `tasklist-discipline` skill becomes a thin pointer to `tasktool` and the gating concepts; the pre-commit hook closes the in-session edit loophole (§8.1, §12 of the spec) by refusing non-canonical bytes, orphaned spec/plan filenames, and any commit that touches `docs/TASKLIST.md`. Sibling skills get surgical edits — every `docs/TASKLIST.md` reference becomes a `tasktool` invocation or a `docs/tasklist.json` reference.
    8	
    9	**Tech Stack:** Python 3 stdlib (`tasktool`), POSIX sh (pre-commit hook), markdown (skills).
   10	
   11	**TASKLIST entry:** `P2.S3` in `docs/tasklist.json` (created 2026-05-18; current status set via `tasktool` during execution).
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
   25	| Create | `tools/tasktool/tests/test_pre_commit_hook.py` | Synthetic-repo hook tests: canonical commit passes; non-canonical bytes blocked; orphan staged spec blocked; staged `TASKLIST.md` blocked; raw semantic edit + `validate --normalise` round-trip passes. (`TASKTOOL_RAW=1` is editor-side scaffolding only — the hook never inspects it, so the test exercises the recovery path with a direct edit instead.) |
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
   47	- [x] **Step 1: Write the failing test**
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
   88	- [x] **Step 2: Run test to verify it fails**
   89	
   90	Run: `python -m pytest tools/tasktool/tests/test_validate_orphans.py -v`
   91	Expected: FAIL — `--check-orphans` is not a known flag (argparse error / exit 2).
   92	
   93	- [x] **Step 3: Add the validator function**
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

[truncated: 865 additional lines]
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
   55	          "closed": "2026-05-18",
   56	          "created": "2026-05-18",
   57	          "id": "S3",
   58	          "notes": "Plan: docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md (recorded via ref; plan_path field remains null — tasktool has no edit-slice-plan-path command in S1/S2)",
   59	          "plan_path": null,
   60	          "refs": [
   61	            "docs/plans/2026-05-18-p2-s3-skill-rewrite-and-hook.md"
   62	          ],
   63	          "reviewer_chain": "docs/reviewer/p2-s3-skill-rewrite-and-hook-P2-S3-post-slice",
   64	          "status": "done",
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