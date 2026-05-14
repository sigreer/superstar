# External-Review Script Redesign — Design

**Date:** 2026-05-13
**Target:** `skills/external-review/scripts/external-reviewer.py` and `skills/external-review/SKILL.md`
**Motivation:** A self-review of the external-reviewer flow surfaced five concrete failure modes that cause review loops to balloon to 7–10 rounds and lose continuity between rounds. This spec redesigns the script and skill to make rounds incremental, durable, and machine-readable.

---

## Goals

1. **Round N+1 is incremental, not a re-review.** The reviewer is given prior findings, the fixer's resolution report, and a focused diff — and is instructed to verify resolution rather than reopen broad review.
2. **Verdict is machine-readable.** JSON output exposes a parsed `verdict`, `verdict_valid`, and finding counts, so coordinators don't have to parse prose.
3. **Post-slice / post-phase chains are uniquely keyed.** `--work-id` is required for both so that multi-slice plans don't collapse into one chain.
4. **Resolution artifacts are durable and structured-enough-to-parse.** Required headers, free-form bodies, stable finding IDs across rounds.
5. **Optional session resume.** Provider-specific wrappers can plug into placeholders if the underlying reviewer CLI supports session IDs.
6. **Legacy chains keep working.** Soft-migrate on first new round; preserve existing folder names and audit history.
7. **Review depth is explicit.** The default chain uses one primary incremental reviewer, but callers can request bounded independent sweep reviewers at high-risk checkpoints to preserve fresh-eye coverage without unbounded serial churn.

## Non-goals

- Replacing the chain-folder layout for new chains. The folder-naming scheme gains a `--work-id` segment for post-slice/post-phase, but the round-file scheme is unchanged.
- Making the script aware of any specific reviewer CLI. The script remains provider-neutral via `AGENT_REVIEWER_CMD`.
- Auto-dispatching the fixer subagent. The script enforces the resolution gate but does not invoke fixers; that stays in the coordinator's loop, governed by `subagent-driven-development`.

## Invariants

- **A review chain is single-writer.** Running two rounds concurrently against the same chain is unsupported and may corrupt `chain.json`. The script does not lock; callers are expected to serialise.
- **Existing rounds are immutable.** Once written, `rN-*-request.md`, `rN-*-response.md`, and `rN-resolution.md` are never overwritten. Manifest entries for past rounds are append-only.

## Architecture

Three implementation passes, all designed in this spec:

- **Pass 1 — Core.** Chain manifest, verdict parsing, `--work-id`, prior-round context injection, incremental round prompts, resolution-artifact contract and gate, automatic diff embedding, JSON output enrichment, legacy migration.
- **Pass 2 — Session resume.** Optional placeholders (`{chain_dir}`, `{round}`, `{previous_response}`, `{resolution_file}`, `{session_file}`) exposed via the existing `AGENT_REVIEWER_CMD` template mechanism. A provider-specific wrapper can use `{session_file}` to persist and resume reviewer sessions. The script provides a stable path (`chain_dir/session.state`) and ensures the parent directory exists; wrappers own the file's contents. The script never reads `session.state`.
- **Pass 3 — Review depth / independent sweeps.** Adds `--review-depth`, `--independent-reviewers`, `--sweep-policy` flags. Independent sweep reviewers run without seeing the primary reviewer's findings on their first pass (to avoid anchoring), and their findings are merged into the same resolution checklist afterward. Depends on Pass 1's manifest and verdict parsing; does not depend on Pass 2.

### Chain manifest

`docs/reviewer/<chain>/chain.json` is the single source of truth for round metadata. The `rN-*-request.md` / `rN-*-response.md` / `rN-resolution.md` files remain for human readability and git history; the script reads and writes manifest entries when computing round numbers, base refs, and verdicts.

```json
{
  "schema_version": 1,
  "chain": "feature-plan-P2-S3-post-slice",
  "kind": "post-slice",
  "target": "docs/superstar/plans/feature-plan.md",
  "work_id": "P2.S3",
  "legacy_migrated": false,
  "rounds": [
    {
      "round": 1,
      "request": "r1-2026-05-13T1012-request.md",
      "response": "r1-2026-05-13T1020-response.md",
      "resolution": null,
      "head_sha_at_request": "abc1234",
      "head_sha_after_round": "abc1234",
      "worktree_dirty_at_request": false,
      "verdict": "revise",
      "verdict_valid": true,
      "findings_count": 4,
      "blocking_findings_count": 2
    },
    {
      "round": 2,
      "request": "r2-2026-05-13T1130-request.md",
      "response": null,
      "resolution": "r1-resolution.md",
      "base_ref": "abc1234",
      "base_ref_source": "auto",
      "head_sha_at_request": "def5678",
      "worktree_dirty_at_request": false,
      "diff_included": true,
      "resolution_parse_status": "ok",
      "resolution_waiver": false
    }
  ]
}
```

#### Manifest versioning

- `schema_version: 1` is the initial version introduced by this redesign.
- Unknown future `schema_version` values cause the script to error with a clear message: `ERROR: chain.json schema_version <N> is newer than this script supports. Upgrade external-reviewer.py.` This prevents silent corruption.
- Older `schema_version` values (currently none) get best-effort migration on read, recorded as `schema_migrated_from: <prior>` in the manifest.

### Naming

- **Chain folder slug:** `<target-stem-no-leading-date>-<work-id-dotless>-<kind>` for post-slice/post-phase; `<target-stem-no-leading-date>-<kind>` otherwise. Dots in work IDs are replaced with dashes in the folder slug only — the manifest preserves the canonical form.
  - Example: `--work-id P2.S3` → folder `feature-plan-P2-S3-post-slice`, manifest `"work_id": "P2.S3"`.
- **Round files:** `r{N}-<YYYY-MM-DDTHHMM>-request.md`, `r{N}-<YYYY-MM-DDTHHMM>-response.md`. Unchanged from current behavior.
- **Resolution files:** `r{N}-resolution.md`, where `N` is the round whose response is being addressed. Round `N+1` consumes `r{N}-resolution.md`. Worked example: after `r1-response.md` returns `revise`, the fixer writes `r1-resolution.md`; round 2 reads `r1-resolution.md` and embeds it in the round-2 prompt.

## CLI surface (new flags)

| Flag | Kinds | Purpose |
|---|---|---|
| `--work-id <id>` | required for `post-slice`, `post-phase`; optional otherwise | Stable slice/phase ID (e.g., `P2.S3` for post-slice, `P2` for post-phase). Becomes part of chain folder name (dots → dashes) and is stored verbatim in the manifest. |
| `--base-ref <sha\|ref>` | any | Override auto-computed diff base for this round. |
| `--no-diff` | any | Suppress diff embedding even on round N+1. |
| `--allow-missing-resolution` | post-slice, post-phase | Waive the resolution-required gate. Logged in manifest as `resolution_waiver: true`. |
| `--changed-files <path>...` | any | Override automatic changed-file discovery and limit the embedded diff to the supplied paths. |
| `--mode <auto\|broad\|incremental>` | any | Override the round-1-vs-N prompt mode. Default `auto` (round 1 → broad; round 2+ → incremental). |
| `--max-diff-lines <int>` | any | Cap diff size. Default 2000. Truncation marker is embedded if exceeded. |
| `--review-depth <standard\|thorough\|exhaustive>` | post-slice, post-phase | Controls whether independent sweep reviewers are run in addition to the primary chain reviewer. Default `standard`. |
| `--independent-reviewers <int>` | post-slice, post-phase | Override reviewer count for independent sweeps. Default derived from `--review-depth`. |
| `--sweep-policy <first-round\|final-ready\|both\|never>` | post-slice, post-phase | When to run fresh-context sweep reviews. Default derived from `--review-depth`. |

### `--work-id` enforcement

- `post-slice` or `post-phase` invoked without `--work-id` → exit 2 with operational error.
- For `post-phase`, the expected form is the phase ID alone (`P2`), not a slice ID. The script does not enforce a regex; it documents the convention.
- For other kinds, `--work-id` is optional; if provided, it is recorded in the manifest but does not affect the folder slug.

## Reviewer prompt — round 1 vs round N+

### Round 1: broad

The existing broad prompt, with the output contract revised to require **stable finding IDs**:

```
1. Findings
   - Each finding tagged `F<n>` (e.g., F1, F2, F3). IDs must be stable across rounds.
   - Severity: blocking | important | minor | nit
2. Open questions / assumptions
3. Suggested document edits
4. Verification gaps
5. Overall verdict: ready | ready with small edits | revise
```

### Round N+: incremental

Prepended to the existing prompt body:

```
You are continuing an existing review chain. This is round {N} of {chain_id}.

In incremental mode:
- Verify whether prior findings are resolved per the resolution report below.
- Reuse the existing finding IDs (F1, F2, …). If a prior finding is resolved,
  mark it RESOLVED in your findings list with its original ID. If still
  unresolved, keep its ID.
- Only introduce new finding IDs for genuine regressions caused by the fix, or
  blocking issues clearly missed in earlier rounds. Do not reopen broad review
  unless prior fixes changed broad architecture.

Review chain summary:
{per-round table: round, verdict, findings_count, blocking_findings_count}

Prior-round findings (authoritative):
{if r{N-1}-merged-findings.md exists: its verbatim contents — this replaces
 individual reviewer response files as the prior-finding list of record}
{else: a summary of the prior round's primary response, with finding IDs intact}

Resolution report for prior round:
{verbatim contents of r{N-1}-resolution.md}
{or "MISSING — explicitly waived by caller via --allow-missing-resolution"}
{or "MISSING — chain migrated from legacy artifacts; please verify whether changes occurred from the diff below"}

Resolution parse summary (best-effort):
{structured: per-finding-ID → status, or "unparseable"}

Changes since prior round:
{git diff <base_ref>..HEAD -- <scoped paths>}
{if dirty: appended `git diff HEAD` section, both labeled}
{if no base: "not available for this round (legacy chain / first round / --no-diff)"}
```

`--mode broad` forces round-1-style on later rounds (rare; for cases where the fix changed architecture). `--mode incremental` on round 1 is rejected with a clear error.

## Resolution artifact contract

**Path:** `docs/reviewer/<chain>/r{N}-resolution.md`, where `N` is the round whose response is being addressed. Authored by the fix subagent between round N (response) and round N+1 (resubmit).

**Required parseable shape:**

```markdown
# Resolution for r{N}

## F1
Status: fixed
Evidence:
- Commit: abc1234
- Files: `src/foo.ts:42`, `tests/foo.test.ts:18`
- Verification: `npm test -- foo.test.ts` passed

Notes:
Changed the validation path to reject empty IDs before persistence.

## F2
Status: waived
Evidence:
- No code change
- Reason: reviewer assumed X, but the plan explicitly excludes X in
  `docs/superstar/specs/foo-design.md:77`

Notes:
No implementation change because this would expand slice scope.
```

**Parser contract:**

- One `## F<id>` heading per addressed finding.
- One `Status: fixed | waived | deferred` line per finding (case-insensitive).
- Optional `Evidence:` block, parsed as free-form.
- Everything else is prose.

**Parser behavior:**

- Best-effort. Missing or malformed sections do not block the workflow.
- The manifest records `resolution_parse_status: ok | partial | unparseable` plus a list of unmatched finding IDs.
- The round N+1 prompt includes the resolution verbatim plus the parser's structured summary, so the reviewer sees both.

**Resolution gate:**

- The gate condition uses the round's authoritative verdict:
  - **Multi-reviewer rounds (Pass 3):** the gate fires if the prior round's `merged_verdict == revise` OR any of its reviewers had `verdict_valid == false`.
  - **Single-reviewer rounds (default `--review-depth standard` and legacy chains):** the gate fires if the prior round's primary `verdict == revise` OR primary `verdict_valid == false`.
- If the gate fires AND `kind in {post-slice, post-phase}` AND no `r{N-1}-resolution.md` exists AND `--allow-missing-resolution` is not set → exit 3 with an operational error:

  ```
  ERROR: Previous post-slice round returned revise, but
  docs/reviewer/<chain>/r{N-1}-resolution.md is missing.

  Dispatch a fixer subagent with:
    - previous response: docs/reviewer/<chain>/r{N-1}-response.md
    - required output:   docs/reviewer/<chain>/r{N-1}-resolution.md

  Then re-run this review.
  Use --allow-missing-resolution only if you intentionally fixed outside the
  standard workflow.
  ```

- `--allow-missing-resolution` is recorded in the round-N+1 manifest entry as `resolution_waiver: true` and surfaced in the round prompt.
- Spec/plan reviews never trigger this gate, because coordinators may apply spec/plan fixes directly during planning (no parallel implementation subagents exist at that stage).
- `ready with small edits` does not trigger the gate; the resolution doc is only required when the prior verdict was a hard `revise` or unparseable (`verdict_valid == false`, which is treated as `revise`).

## Diff embedding

- **Base ref:** defaults to the previous round's `head_sha_after_round`. `--base-ref` overrides. `--no-diff` suppresses.
- **Scope:**
  - For `post-slice` and `post-phase`: **all tracked changes** in `base_ref..HEAD` (i.e., `git diff <base>..HEAD` with no path filter), plus the dirty/untracked surface described below. This is the default because the fixer's changes are almost always in code/test files, not in the plan document — restricting the diff to target + context files would hide most of what the reviewer needs to verify.
  - For `spec`, `plan`, `design`, `implementation`, `other`: target file + all `--context` files. (These reviews are about a single document; broad code diffs are not what the reviewer is being asked to evaluate.)
  - In all cases, `--changed-files` overrides the default and limits the embedded diff to the supplied paths.
  - Capped at `--max-diff-lines` (default 2000) with an explicit truncation marker.
- **Untracked files.** `git diff` misses untracked files. To surface them:
  - Always include the output of `git status --porcelain` scoped to the diff paths.
  - For each untracked text file inside the scoped paths, append a capped preview (using the same line cap as the diff) via `git diff --no-index /dev/null <file>`.
  - Binary or oversized untracked files are listed by name only with a `(omitted: binary or > <cap> lines)` marker.
- **Dirty worktree handling.** If `git status --porcelain` is non-empty, the diff section contains both `git diff <base>..HEAD -- <paths>` and `git diff HEAD -- <paths>`, each clearly labeled. The manifest records `worktree_dirty_at_request: true`.
- **Legacy / missing base.** If no prior round has a recorded SHA (legacy chains' first new round, or first round overall, or `--no-diff`), the prompt says `Changes since prior round: not available for this round.`

## JSON output schema

`--emit json` returns:

```json
{
  "review_path": "docs/reviewer/.../r2-...-response.md",
  "prompt_path": "docs/reviewer/.../r2-...-request.md",
  "chain": "feature-plan-P2-S3-post-slice",
  "round": 2,
  "kind": "post-slice",
  "work_id": "P2.S3",
  "status": "ok",
  "returncode": 0,
  "verdict": "ready with small edits",
  "verdict_valid": true,
  "findings_count": 1,
  "blocking_findings_count": 0,
  "resolution_parse_status": "ok",
  "resolution_waiver": false,
  "diff_included": true,
  "base_ref": "abc1234",
  "worktree_dirty_at_request": false,
  "review_depth": "standard",
  "reviewers": [
    {
      "role": "primary",
      "verdict": "ready with small edits",
      "verdict_valid": true,
      "review_path": "docs/reviewer/.../r2-...-response.md",
      "review": "<primary reviewer text>"
    }
  ],
  "merged_verdict": "ready with small edits",
  "merged_findings_path": null,
  "merged_findings": null,
  "review": "<single-reviewer rounds: same as reviewers[0].review; multi-reviewer rounds: contents of merged_findings if present>"
}
```

### Multi-reviewer JSON payload

When a round has more than one reviewer:

- `reviewers[]` contains one entry per reviewer with its own `verdict`, `verdict_valid`, `review_path`, and `review` text. The primary is always `reviewers[0]`.
- `merged_findings_path` points at `r{N}-merged-findings.md` and `merged_findings` contains its contents.
- The top-level `review` field becomes the merged-findings text (so a coordinator that only reads `review` still sees every reviewer's findings, not just the primary's).
- `merged_verdict` is the authoritative verdict for gating; the coordinator MUST use `merged_verdict`, not `reviewers[0].verdict`.

For single-reviewer rounds, `reviewers[]` has one entry, `merged_findings_path` and `merged_findings` are `null`, and the top-level `review` mirrors `reviewers[0].review` for backwards compatibility.

### Verdict parsing rules

- Search the response (case-insensitive) for `Overall verdict:` followed by one of the three accepted values. Trailing punctuation and surrounding markdown formatting (backticks, asterisks) are stripped.
- Multiple matches → take the last (reviewers sometimes restate verdicts in summaries).
- No match or unrecognized value → `verdict: null`, `verdict_valid: false`. The skill MUST treat `verdict_valid: false` as `revise`.

### Finding-count parsing

Real reviewers may emit findings as prose paragraphs, headings, or bullets. Parser accepts three styles (see `parse_findings` / `_collect_findings` in `skills/external-review/scripts/external-reviewer.py:503`):

- Prose: `^F\d+\.\s+(Blocking|Important|Minor|Critical|Major|Nit)?\b...` — severity word is captured inline and `Blocking` (case-insensitive) marks the finding as blocking.
- Heading: `^##\s+F\d+\b` — heading-only matches are not blocking by default; blocking is derived from a subsequent `Severity: blocking` line or inline `(blocking)` marker.
- Bullet: `^\s*[-*]?\s*\**F\d+\**[:\s\-]` — blocking is derived from an inline `(blocking)` marker.

Style precedence is prose > heading > bullet: the first style that yields any matches wins, so embedded preview blocks in a prose-style response do not double-count. Findings are de-duplicated by ID (first occurrence wins for the blocking flag).

If no style matches, `findings_count` and `blocking_findings_count` are `null` and the coordinator inspects prose. An explicit "no findings" sentinel (`## Findings\nnone`, `Findings: none|n/a|0|zero`) is parsed as `(0, 0)`.

## Pass 2 — session resume placeholders

The existing template-substitution mechanism in `AGENT_REVIEWER_CMD` is extended with new placeholders the script substitutes when they appear in the command template:

| Placeholder | Substituted with |
|---|---|
| `{chain_dir}` | Absolute path to the chain folder. |
| `{round}` | Current round number. |
| `{previous_response}` | Path to `r{N-1}-response.md`, or empty string for round 1. |
| `{resolution_file}` | Path to `r{N-1}-resolution.md`, or empty string. |
| `{session_file}` | Path to `chain_dir/session.state`. The script ensures the directory exists; the file may be absent on round 1. |
| `{prompt_file}`, `{prompt_text}`, `{target_file}`, `{kind}` | Unchanged from current behavior. |

A wrapper like `claude-reviewer --session-from {session_file} --prompt-file {prompt_file}` can persist a session ID into `session.state` and resume it next round. The script itself never reads `session.state`; it only ensures the path is stable across rounds and passes it to the wrapper. Bridges that don't use session resume simply omit the new placeholders.

## Pass 3 — Review depth and independent sweeps

The primary chain reviewer accumulates context across rounds, which is the core continuity win of this redesign. But a context-rich reviewer also anchors on prior framing and can miss issues a fresh-eye pass would catch. Pass 3 reintroduces fresh-eye coverage, bounded, at explicit checkpoints.

### Modes

- **`--review-depth standard`** (CLI default, for backwards compatibility). One primary reviewer; round 2+ incremental. No independent sweeps. Cheapest. Use when extra fresh-eye assurance is not warranted, or for ad-hoc / non-gating reviews.
- **`--review-depth thorough`** (recommended workflow default for `post-slice` and `post-phase`). One independent sweep on round 1 (in parallel with the primary), and one fresh sweep when the primary first returns `ready` or `ready with small edits`. Catches issues that a context-accumulating primary can miss without doubling the cost on every revise iteration.
- **`--review-depth exhaustive`**. Two independent sweeps on round 1, and one or two at first-ready. Use for risky phases (architecture changes, security-relevant work, irreversible migrations).

The CLI default is `standard` to keep existing callers working without change. The skill (`external-review/SKILL.md`) recommends invoking with `--review-depth thorough` for `post-slice` and `post-phase` checkpoints, and the skill's example invocations pass it explicitly. Workflows that need lower cost can opt down to `standard`; workflows that need higher assurance opt up to `exhaustive`.

`--independent-reviewers <int>` and `--sweep-policy <first-round|final-ready|both|never>` override the depth defaults for cases that don't fit the three preset depths.

### Anchoring avoidance

Independent sweep reviewers **must not see** the primary reviewer's findings on their first pass. They receive the same target and context the primary received, plus the diff, but not the primary's `response.md`. Otherwise they anchor on the primary's framing and the value of the fresh-eye pass collapses.

After all reviewers in a checkpoint have produced their independent responses, the script merges them:

- Each sweep reviewer's findings are renamed to a sweep-namespaced ID (e.g., `S1.F1`, `S2.F1`) to avoid colliding with the primary chain's `F<n>` IDs.
- Merged findings are written to a single `r{N}-merged-findings.md` artifact in the chain folder, grouped by reviewer.
- The resolution checklist for the next round addresses both the primary's findings and the sweep findings, using the merged IDs.
- A merged verdict is computed: `revise` if any reviewer returned `revise` (or `verdict_valid == false`); `ready with small edits` if any returned that and the rest are `ready`; `ready` only if all reviewers returned `ready`.

### Manifest extensions

Each round entry gains:

```json
{
  "round": 1,
  "reviewers": [
    {"role": "primary", "response": "r1-2026-05-14T0900-primary-response.md", "verdict": "revise", "verdict_valid": true},
    {"role": "sweep", "sweep_group": 1, "parent_round": 1, "response": "r1-2026-05-14T0902-sweep1-response.md", "verdict": "ready with small edits", "verdict_valid": true}
  ],
  "merged_verdict": "revise",
  "merged_findings": "r1-merged-findings.md"
}
```

`reviewers[0]` is always the primary. Sweep entries carry `role: sweep`, a `sweep_group` integer, and a `parent_round` pointing back to the round whose primary they sweep against.

### Filenames

When a round has only one reviewer (the `standard` depth default), filenames stay non-namespaced:

- `r{N}-<timestamp>-request.md` / `r{N}-<timestamp>-response.md`

When a round has more than one reviewer (any depth above `standard`, or when `--independent-reviewers > 0`), per-reviewer files are namespaced:

- `r{N}-<timestamp>-primary-request.md` / `r{N}-<timestamp>-primary-response.md`
- `r{N}-<timestamp>-sweep{K}-request.md` / `r{N}-<timestamp>-sweep{K}-response.md`

The merged findings file (only written when there are multiple reviewers) is `r{N}-merged-findings.md`. Resolution files remain `r{N}-resolution.md` (one per round, addressing either the single reviewer's findings or the merged findings).

In all cases the manifest's `reviewers[]` array is the structural source of truth — file names are conveniences for humans reading the chain folder.

### Sweep policy semantics

- `first-round`: independent sweep(s) run on round 1 only.
- `final-ready`: independent sweep(s) run when the primary **first** returns `ready` or `ready with small edits`. Runs once per chain, even if the primary returns to `ready` again in a later round after a sweep-driven `revise`.
- `both`: both of the above. This is the `thorough` and `exhaustive` defaults.
- `never`: standard depth; equivalent to `--review-depth standard`.

### Sweep checkpoint state

To prevent repeated firing of `final-ready` (or `first-round`) sweeps across rounds, the manifest carries a chain-level state field:

```json
{
  "sweep_checkpoints": {
    "first-round": "completed",
    "final-ready": "pending"
  }
}
```

Values: `pending` (not yet fired), `completed` (fired in some prior round). The script checks this map before dispatching sweeps and flips entries to `completed` only after the corresponding sweep round writes its merged findings. `--sweep-policy` overrides the depth defaults but cannot re-fire a `completed` checkpoint without an explicit `--force-resweep <first-round|final-ready>` flag (out of scope for this redesign — documented as a future affordance).

### Cost note

Sweep reviewers double or triple the reviewer-invocation cost for the rounds where they run. The defaults are tuned to spend that cost only at checkpoint boundaries (round 1 and first-ready), not on every revise iteration.

## Legacy migration

On any invocation, if the chain folder exists but lacks `chain.json`:

1. Scan `rN-*-request.md` / `rN-*-response.md`. Sort by parsed round number first, mtime second.
2. Parse verdicts from response files where possible; `null` where not.
3. Synthesize a manifest with `legacy_migrated: true`, `migrated_at: <ISO timestamp>`, and one `rounds[]` entry per detected round with `legacy: true` and `head_sha_after_round: null`.
4. Preserve the existing chain folder name. If the caller supplies `--work-id` and the legacy folder name lacks it, the work-id is stored in the manifest only — no folder rename. This avoids breaking links already written into TASKLIST.md, plans, or handoff docs.
5. The first new round after migration:
   - Embeds no auto-diff (no historical base ref to diff from).
   - Prompt explicitly notes: `This chain was migrated from legacy artifacts. No reliable previous HEAD SHA is available, so no automatic inter-round diff is included for this round.`
6. From the next round onward, the full new flow applies.

### Legacy chain discovery

When `--work-id` is supplied for a post-slice/post-phase invocation, the script:

1. First looks for the exact new folder slug (e.g., `feature-plan-P2-S3-post-slice`). If present, use it.
2. If not, search for legacy folders matching `<target-stem-no-date>-<kind>` (the old naming scheme).
3. If exactly one such folder exists AND it has no manifest (or its manifest's `work_id` matches or is null), treat it as the chain to migrate. Run the migration described above and record the work-id.
4. If multiple legacy candidates exist, error out: `ERROR: Multiple legacy chains match <target-stem>-<kind>. Migrate manually or specify --chain-dir.` (A future `--chain-dir` flag is reserved for this case but is out of scope for this redesign.)
5. If no legacy candidate exists, create a new chain folder using the new naming scheme.

## Exit codes

| Code | Meaning | Action |
|---|---|---|
| 0 | Reviewer succeeded. | Apply feedback. |
| 2 | Target / context file not found, or required `--work-id` missing. | Fix the path or pass `--work-id`. |
| 3 | Resolution-required gate violated. | Author the resolution doc and re-run, or pass `--allow-missing-resolution`. |
| 4 | `chain.json` schema_version newer than supported. | Upgrade `external-reviewer.py`. |
| 5 | Ambiguous legacy-chain match. | Migrate manually or disambiguate. |
| 124 | Reviewer timed out. | Raise `--timeout`, or split the target. |
| 127 | Reviewer command not found. | Set `AGENT_REVIEWER_CMD` or run `project-setup`. |
| other | Reviewer's own non-zero exit. | A response file was still written. Read it and surface the issue. |

## Skill documentation updates

### `skills/external-review/SKILL.md`

- New **"Round mode"** section explaining round 1 (broad) vs round N+ (incremental), and when to use `--mode broad` override.
- New **"Resolution artifact"** section documenting the contract and pointing at the fix subagent's responsibility (with a cross-link to `subagent-driven-development`).
- Updated **"How a round runs"** example showing `--work-id`.
- Updated **"Exit codes"** table.
- Updated **"Reading the response"** section pointing at the parsed JSON `verdict` field as the source of truth; the prose verdict is for humans.
- New **"Chain manifest"** section briefly describing `chain.json` and the single-writer invariant.

### `skills/subagent-driven-development/SKILL.md`

- The fix-subagent dispatch step (currently "dispatch a fix subagent with the response file as input") gets a concrete output requirement: `Write rN-resolution.md per the contract in [[external-review]] before signaling completion.`
- The slice-boundary process diagram is updated so the post-slice resubmission node depends on the resolution file existing.

## Risk notes

- **Verdict-parsing brittleness.** If the configured reviewer doesn't emit `Overall verdict:` cleanly, `verdict_valid` flips false and the agent treats the round as `revise`. Acceptable failure mode — better than a false-positive `ready`.
- **Manifest race conditions.** Single-writer assumed (no parallel rounds on the same chain). Documented as an invariant; the script does not lock.
- **Large diffs.** Capped at `--max-diff-lines`; truncation marker tells the reviewer to inspect the working tree if needed.
- **Soft parse of resolution.md.** If a fixer subagent produces sloppy resolution files, `resolution_parse_status: partial` is the safety valve; the reviewer still sees the prose verbatim.
- **Legacy folder collisions.** A repo with two old chains matching the same `<target-stem>-<kind>` pattern will hit the ambiguous-migration error. Operator must disambiguate manually. Considered acceptable; this is rare.

## Implementation slicing (suggested for the writing-plans handoff)

Ordered so prompt behavior — the core behavioral fix — lands before diff embedding (which is an enhancement on top).

- **S1 — Manifest & verdict parsing.** Introduce `chain.json`, parse verdicts on read, emit enriched JSON. Backwards-compatible: legacy chains still work; manifest is synthesized on touch.
- **S2 — `--work-id` and folder naming.** Enforce for post-slice/post-phase; folder rename for new chains only. Legacy-chain discovery logic.
- **S3 — Resolution artifact & gate.** Parser, gate, error message, manifest field, `--allow-missing-resolution`.
- **S4 — Incremental prompt mode & finding-ID contract.** Reviewer prompt revision, `--mode` flag, round-1-vs-N branching, resolution embedding in prompt.
- **S5 — Diff embedding.** `--base-ref`, `--no-diff`, `--changed-files`, untracked-file handling, dirty-worktree labeling. Manifest records base refs.
- **S6 — Pass 2 placeholders.** Session-file plumbing for `{chain_dir}`, `{round}`, `{previous_response}`, `{resolution_file}`, `{session_file}`.
- **S7 — Pass 3 review depth.** `--review-depth`, `--independent-reviewers`, `--sweep-policy` flags; parallel sweep dispatch; merged-findings artifact; manifest `reviewers[]` extension; merged-verdict computation. Independent of S6.
- **S8 — Skill doc updates.** `external-review/SKILL.md` and `subagent-driven-development/SKILL.md` changes covering all of the above.
