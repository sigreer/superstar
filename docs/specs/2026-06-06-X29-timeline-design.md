# X29 — Visual work-history timeline generator (`tools/timeline`)

**Date:** 2026-06-06
**Status:** draft
**Kind:** cross-cutting tool (human-facing; zero agent-context footprint)

## Purpose

A script that generates a browser-viewable visual timeline of completed work for any
tasktool-managed project, intended as a visual aid when discussing progress with
non-technical people. A vertical spine down the centre of a scrollable page represents
project time from start to latest activity; phases and slices are the major and minor
nodes on that spine, placed at their completion dates/times.

## Constraints (binding)

- **Zero agent-context overhead.** No skill, hook, CLAUDE.md entry, or tasktool help
  line references this tool. It is invoked only by humans or on explicit request in
  interactive sessions.
- **Zero dependencies.** Python 3 stdlib only; git accessed via `subprocess`. No
  third-party packages, matching the repo's zero-dependency philosophy.
- **Generic.** Works on any repo with `docs/tasklist.json` (current tasktool schema),
  not just this one. Primary target project today: `multistore`.
- **Static output.** A single self-contained HTML file (inline CSS/JS/data). Opens via
  `file://`, shareable as an attachment, no server.

## Placement & architecture

```
tools/timeline/
  timeline.py    # CLI entry
  extract.py     # git replay + live tasklist.json + archive JSON blocks → raw events
  model.py       # the ONE schema-aware module → normalized TimelineItem records
  render.py      # TimelineItem records → self-contained HTML
  backfill.py    # run-once legacy migrator (separate command; never invoked by timeline.py)
```

Sibling to `tools/tasktool`, **not** part of it (tasktool's CLI surface is unchanged).
`model.py` is the deliberate seam: it is the only module that knows the tracker schema.
If a shared tracker-model module is later extracted from tasktool, only `model.py`'s
internals are replaced; `extract.py` and `render.py` consume `TimelineItem` records and
do not move.

### CLI

```
python3 tools/timeline/timeline.py [--repo PATH] [-o timeline.html] [--show-x] [--overrides PATH]
python3 tools/timeline/backfill.py [--repo PATH] [--write]
```

- `--repo` defaults to the current working directory's repo root (`git rev-parse --show-toplevel`).
- `-o` defaults to `timeline.html` in the current directory.
- `--show-x` sets the X-item toggle's initial state to on (data is embedded either way).
- `--overrides` defaults to `docs/timeline-overrides.json` in the target repo if present.
- `backfill.py` is dry-run by default, printing a unified diff; `--write` applies it.

## Data model

```python
TimelineItem:
  key            # "P21", "P21.S4", "X13"
  kind           # phase | slice | x
  parent         # phase key for slices, None otherwise
  title          # verbatim tracker title
  display_title  # optional override relabel; renderer prefers it when present
  status         # done | cancelled | ready | in_progress | blocked ...
  created, started, closed   # each: (datetime|None, precision, source)
                             # precision: day | minute
                             # source:    field | replay | override
```

## Date resolution (precedence)

For each of `created`/`started`/`closed` on each item:

1. **Overrides file** (`docs/timeline-overrides.json`, optional) — always wins. Schema:

   ```json
   {
     "items": {
       "P14":    { "started": "2026-05-20" },
       "P21.S2": { "display_title": "Quiet-launch controls" },
       "X12":    { "exclude": true }
     }
   }
   ```

   Values: ISO date or datetime for the three date fields; `display_title` string;
   `exclude` boolean. Unknown keys in an item entry are an error (fail loud, not silent).

2. **Tracker JSON fields** — the authoritative *date* (day precision). Sources: the live
   `docs/tasklist.json` plus every archive file's fenced JSON block under
   `docs/archived-tasks/` — `## Full phase JSON` blocks for archived phases (a full
   project-shaped object whose `phases` array holds the phase) **and** `## Full
   cross-cutting JSON` blocks for archived X-items (a single item object). Both shapes
   are required reading; dropping the cross-cutting blocks would leave the X toggle
   mostly empty on mature projects. The placeholder `1970-01-01` is treated as absent.
   Where two archive files exist for the same phase (legacy + tasktool re-archive), the
   one with a parseable JSON block wins; pure-legacy markdown files are ignored by
   `timeline.py` (they are `backfill.py`'s input, not the renderer's).

3. **Git replay** — walk every commit touching `docs/tasklist.json` oldest→newest
   (`git log --reverse --format=%H %ct -- docs/tasklist.json`), parse the file at each
   revision (`git show SHA:docs/tasklist.json`), and record status transitions and date
   field changes per item with the commit timestamp. Replay:
   - upgrades a field date to **minute precision** when the replay-observed transition
     falls on the same calendar day;
   - fills a field that is null in the tracker (e.g. missing `started`: first transition
     to `in_progress`/`started`; missing phase `closed` is *not* invented — an open phase
     renders as open);
   - **ignores transitions observed at an item's first-appearance commit when the item
     appears already terminal** (import artifacts — e.g. the 2026-05-18 multistore
     migration commit where P1–P12 arrived `done`).

Validated against multistore: 226 commits replay with zero parse failures, yielding
minute-precision lifecycles for 108 items.

### Derived phase span

- Phase start for rendering = `started` if present, else earliest slice `started`, else
  phase `created`.
- Phase end = `closed` if present, else open (strand runs to the bottom edge labelled
  with the generation date).
- **Close-only items** (no resolvable start or create — e.g. legacy P1 with
  `created: 1970-01-01`, `started: null`, no slices): render as a close node only — a
  zero-length span with the hollow close ring and label, no strand segment. This is a
  supported display mode, not an error; backfill/overrides can later supply a start.

## Visual specification

Validated interactively against real multistore data (P20–P23).

- **Spine braid.** Vertical centre spine; one coloured strand per open phase. When N
  phases are open concurrently, N strands sit side-by-side. When no phase is open, a
  dotted grey strand bridges the gap with an "N quiet days" label. Phase colours come
  from a fixed palette cycled by phase number (stable across regenerations).
- **Nodes.** Phase start = filled disc in phase colour + bold title and start date.
  Phase close = hollow ring in phase colour (grey ring for cancelled phases) + "PNN
  complete · date" label. Slice completion = small filled disc in phase colour.
- **Cards.** Each slice gets an info card tinted with the parent phase colour
  (background tint + border), showing title (or `display_title`) and completion
  date/time. Day-precision dates show no time-of-day (never a fake "00:00").
  During solo stretches cards alternate left/right; during overlaps each open phase
  owns one side so a track reads as a column. With 3+ concurrent phases the braid
  gains strands; cards keep phase colours for attribution.
- **Click-to-expand.** Clicking a card expands it in place: full verbatim title, item
  ID, started/closed datetimes with precision markers, computed duration.
- **Time scale: proportional with guard rails.** Vertical distance is proportional to
  elapsed time, subject to (a) a minimum spacing between adjacent nodes — burst days
  expand locally to stay readable — and (b) a maximum rendered height for empty
  stretches — long gaps compress to a capped dotted segment with the quiet-days label.
- **Cancelled items.** A cancelled phase is omitted unless it has ≥1 `done` slice; when
  shown it renders normally (grey close ring), with only its completed slices.
  Cancelled slices are always omitted.
- **X-items.** First-class: always extracted and embedded. Rendered as neutral slate
  nodes/cards on the spine at their completion time (they have no parent phase colour).
  An in-page toggle shows/hides them instantly without regeneration; `--show-x` only
  sets the toggle's initial state. Open/never-completed X-items are not rendered.
- **Header.** Project name, overall date span, totals (phases completed, slices
  completed), generation timestamp, and a colour legend of phases.

## Legacy backfill (`backfill.py`)

One-time, per-project migration for items that predate the tracker. It exists so that
`timeline.py` never grows legacy parsing paths.

- **Input:** legacy archive markdown under `docs/archived-tasks/` (headings of the form
  `## S1 — title ✅ \`DONE 2026-04-29\``) and the repo's commit subjects.
- **Recovers:** slice titles and close dates from the markdown; phase/slice `started`
  dates from first-commit-mention mining (`\bP(\d+)(?:[.\-]?S(\d+))?\b` over subjects),
  cross-checked against the previous phase's close for the sequential legacy era.
- **Writes:** recovered slices and dates into the corresponding tasktool archive file's
  `## Full phase JSON` block — the canonical location `tasktool unarchive` understands.
  Phase-level fields already present are never overwritten.
- **Safety:** dry-run by default with a unified diff; `--write` applies; the human
  reviews and commits. Never invoked by `timeline.py`.

Multistore evidence: legacy P1–P12 have reliable close dates in archives; commit mining
dates P2–P12 starts cleanly; P1 has no commit mentions, so its `started` will need a
manual override entry (or remain start-unknown, rendering from its close date only).

## Error handling

- Not a git repo / no `docs/tasklist.json` → clear fatal error.
- A historical revision that fails JSON parsing → skipped with a stderr warning; replay
  continues (validated: 0/226 failures on multistore, but schema drift must not be fatal).
- Shallow clone → replay covers what exists; items degrade to day precision with a
  one-line warning.
- Unknown schema fields → ignored (tolerant reader); unknown override keys → fatal.
- Items with no resolvable dates at all → listed in a stderr summary so gaps are
  visible, omitted from the render. No silent drops.

## Testing

`tools/timeline/tests/` (pytest, mirroring tasktool's convention). **`tools/timeline/tests`
must be added to `testpaths` in the repo's `pyproject.toml`** so the default
`python3 -m pytest` gate discovers it — otherwise "all tests pass" is vacuously true.

- **Replay:** transition detection, minute-precision upgrade, null-fill, import-artifact
  suppression — against a fixture git repo built by the test (tmpdir, scripted commits).
- **Precedence:** override > field > replay; `1970-01-01` treated as absent; exclude.
- **Braid:** lane assignment for 1/2/3 concurrent phases; gap detection.
- **Scale:** guard-rail maths (min spacing under bursts, gap cap, proportionality
  between guards).
- **Backfill:** legacy heading parser; archive JSON block rewrite; dry-run diff output.
- **Smoke:** end-to-end render of the fixture repo; assert expected node/card markup
  and that the output is a single file with no external references.

Out of scope: pixel/visual regression testing — the multistore render is eyeballed.

## Non-goals

- No tasktool subcommand, no shared module extraction now (the `model.py` seam bounds
  that future change to one file).
- No live server, no auto-refresh.
- No LLM summarisation of titles (relabels are human-authored overrides).
- No editing of tracker data by `timeline.py` (read-only; only `backfill.py --write`
  mutates, and only archive files).

## Acceptance

1. `python3 tools/timeline/timeline.py --repo ../../multistore -o /tmp/t.html` produces
   a self-contained HTML that opens via `file://` and shows: coloured phase strands,
   the P14∥P16∥P17 overlap as adjacent strands, dotted quiet gaps, minute-precision
   times for tracker-era items, day-only labels for legacy items, X-item toggle.
2. After `backfill.py --write` + review in multistore, legacy P1–P12 appear with slice
   nodes and inferred starts without any legacy code path in `timeline.py`.
3. `python3 -m pytest` (with `tools/timeline/tests` in `testpaths`) passes, including a
   smoke assertion that an archived X-item sourced from a `## Full cross-cutting JSON`
   block appears when X-items are shown; the tool runs on a repo with no archives and
   on this repo unchanged.
