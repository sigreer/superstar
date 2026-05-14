# Reviewer rate-limit handling — design spec

- Status: draft (external-review gate bypassed for this session per user instruction)
- Date: 2026-05-14
- Owner: Simon Greer
- Related: `skills/external-review/scripts/external-reviewer.py`, `skills/external-review/SKILL.md`

## 1. Problem

When the third-party reviewer CLI (`codex`, `claude`, `gemini`, etc.) hits its provider usage cap, the subprocess exits non-zero with a stderr message like:

```
ERROR: You've hit your usage limit. Upgrade to Pro (...), visit ... or try again at 6:48 PM.
```

Today, `external-reviewer.py` records this as a generic process-failure round. The coordinator's next move is to re-submit — but the reviewer is still rate-limited, so the next round also fails. Without operator intervention the workflow stalls indefinitely (and burns chain rounds that don't progress the work).

This spec adds first-class rate-limit handling: detect the failure mode, persist the reset window across sessions, and give the user three clear paths forward (manually approve, schedule a retry, or hand-bridge a response from an external reviewer).

## 2. Goals

- Detect rate-limit failures distinctly from other reviewer crashes.
- Persist a global "limited until T" flag per reviewer binary so other sessions/repos honour it.
- Refuse to spawn the reviewer subprocess while limited; instead surface a structured exit code + JSON payload.
- Offer the operator three named paths (manual approval, scheduled retry, human bridge), plus a "hold" escape hatch so they're never railroaded.
- Keep the chain history honest: a manual approval is a round in the chain, not a fabricated reviewer response.

## 3. Non-goals

- Auto-switching to a different reviewer backend on limit.
- Pre-emptive limit prediction (no quota probe).
- Multi-coordinator coordination beyond a brief `flock` on the state file.
- Persisting the *contents* of scheduled tasks beyond what the `schedule` skill itself handles.

## 4. Architecture

Two layers:

**CLI layer** (`skills/external-review/scripts/external-reviewer.py`)
- Detects rate-limit via stderr regex.
- Writes/reads `~/.config/superstar/reviewer-state.json` (a global, per-user state file).
- Refuses spawn while limited; exits **code 8** with a JSON payload describing the limit.
- Four new subcommands: `manual-approve`, `ingest-response`, `show-limit`, `clear-limit`.

**Skill / coordinator layer** (`skills/external-review/SKILL.md`)
- Documents exit 8 + the three-option menu.
- Coordinator presents the menu via `AskUserQuestion` on every limited invocation (no auto-pick).
- Coordinator dispatches each path directly (no subagent — manual approval is too consequential to delegate; the other two are tightly UI-coupled to the operator).

## 5. State file

Path: `~/.config/superstar/reviewer-state.json` by default. **Overridable** via the env var `AGENT_REVIEWER_STATE_FILE` (absolute path) or the CLI flag `--state-file PATH` on every subcommand that touches state (`review`, `manual-approve`, `ingest-response`, `show-limit`, `clear-limit`). Tests MUST set the env var to a `tmp_path`-scoped file so they never touch the developer's real state.

The parent dir is created with `0700` permissions on first write.

Shape:

```json
{
  "schema_version": 1,
  "limits": {
    "<reviewer_cmd_basename>": {
      "limited": true,
      "limited_at":  "2026-05-14T17:00:00",
      "reset_at":    "2026-05-14T18:48:00",
      "reset_source": "regex:codex_usage_limit",
      "raw_stderr_tail": "ERROR: You've hit your usage limit. ... try again at 6:48 PM.",
      "chain":  "external-reviewer-context-optimisation-plan-P1-post-phase",
      "round":  2
    }
  }
}
```

- The key is the basename of `AGENT_REVIEWER_CMD` (defaulting to `"reviewer-agent"`). Different backends limit independently.
- `reset_at` is ISO 8601 local-time (no TZ suffix). Comparisons use `datetime.now()` against the parsed value.
- All timestamps strip seconds for stability.
- On read, if `reset_at <= now()`, the entry is cleared in-place and the script proceeds normally (limit treated as expired).
- Read/write uses `fcntl.flock(LOCK_EX)` on the file handle. Reads are short-lived; writes serialise across processes.
- Missing file → empty state, no error.
- Schema violations → log a warning to stderr, behave as if no state existed (fail-open, never block work on a corrupt state file).

## 6. Detection + reset-time parsing

New module-level helper in `external-reviewer.py`:

```python
def detect_rate_limit(stderr_text: str) -> tuple[bool, datetime | None, str | None]:
    """Return (matched, reset_at_local, pattern_name)."""
```

Built-in patterns (compiled at import):

| name                     | regex (Python)                                                                     |
|--------------------------|------------------------------------------------------------------------------------|
| `codex_usage_limit`      | `r"You've hit your usage limit.*?try again at (\d{1,2}:\d{2}\s*(?:AM|PM)?)"` (the pipe is regex alternation; spec table escaping is incidental — the actual compiled pattern uses an unescaped `|`) |
| `claude_cli_rate_limit`  | stub — `r"(rate limit|rate-limited).*?reset (?:at|in)? ?(.+?)$"` (best-effort)     |
| `gemini_cli_rate_limit`  | stub — `r"quota exceeded.*?retry (?:after|at) (.+?)$"` (best-effort)               |

The stub patterns are extensible slots; we ship them as conservative matchers but expect real samples to refine them.

Plus a user-supplied extension via env var:

```
AGENT_REVIEWER_RATE_LIMIT_PATTERNS="my_backend=ERROR limit hit until (.+);other_backend=..."
```

Parsed at startup; each pair adds another regex to the dispatch list.

Reset-time parsing rules:
1. If a regex group captures a clock time (`HH:MM`, optional `AM`/`PM`, or 24h), parse it as local time today.
2. If the resulting timestamp is in the past, add 1 day (assume tomorrow).
3. If the pattern matched but no time group (or the group fails to parse), fall back to `now + AGENT_REVIEWER_LIMIT_FALLBACK_HOURS` (default `4`).
4. The agent presents the parsed `reset_at` to the user for confirmation before using it to schedule anything (option 2). The user can override.

## 7. CLI behaviour change

### 7.1 Pre-spawn check (`run_one_reviewer`)

```
1. Read state file. If state[reviewer_cmd_basename].limited is True and reset_at > now():
     - Synthesise a "rate-limited" round artifact (≤8 KB, same shape as the existing
       failed-round stub: header + status + the raw_stderr_tail + a one-line
       "Reviewer rate-limited until <reset_at>; rerun after that or use the menu" body).
     - chain.json round entry: status="rate-limited", returncode=null, verdict=null,
       verdict_valid=false, reset_at=<iso>, reviewer_cmd=<basename>.
     - Print JSON payload to stdout (see 7.3).
     - Exit code 8.
2. If reset_at <= now(): clear the entry, write state, continue normally.
3. No state → continue normally.
```

### 7.2 Post-failure detection

After the reviewer subprocess exits non-zero:

```
1. Call detect_rate_limit(stderr_text).
2. If matched:
     - Compute reset_at via §6 rules.
     - Acquire flock on state file, set limits[<reviewer_cmd_basename>] = { ... }, release.
     - Write the rate-limited round artifact (replacing the would-be failed-round artifact).
     - Print JSON payload to stdout. Exit code 8.
3. If not matched: existing failed-round path (status="failed", exit with reviewer's own returncode).
```

The `--review-depth thorough` case: when only the **primary** reviewer is rate-limited, the round is rate-limited (no sweep needed). When a sweep is rate-limited and the primary succeeded, the sweep is recorded as a per-reviewer rate-limited entry inside `chain.json`'s `reviewers[]` and the round otherwise behaves like the existing "some sweeps failed" case (merged verdict computed from ok reviewers only). The state file is still written so subsequent invocations against the same reviewer_cmd refuse.

### 7.3 Exit code 8 JSON payload

```json
{
  "rate_limited": true,
  "reviewer_cmd": "reviewer-agent",
  "reset_at":     "2026-05-14T18:48:00",
  "reset_source": "regex:codex_usage_limit",
  "chain":        "external-reviewer-context-optimisation-plan-P1-post-phase",
  "round":        2,
  "request_path": "docs/reviewer/.../r2-...-request.md",
  "raw_stderr_tail": "ERROR: ..."
}
```

`--emit json` (already a flag) emits this on the same stdout the success path uses, so the existing parsing code in callers can branch on the `rate_limited` key.

### 7.4 Rate-limited status semantics (interaction with existing logic)

The introduction of `status: "rate-limited"` requires updates at four sites in the existing script. Each is enumerated here so the plan can land them as small, named tasks.

| Site | Current behaviour | Required change |
|---|---|---|
| **Resolution gate** (`post-slice` / `post-phase` requires `r{N-1}-resolution.md` unless prior round was `status="failed"`) | Bypasses only on `"failed"` | Also bypass on `"rate-limited"`. A rate-limited round has no findings to resolve. |
| **`build_incremental_preamble` walk-back** (skips `status ∈ {failed, unknown}` to find the last trusted round) | Skips `failed`/`unknown` | Also skip `rate-limited`. The "Note: rounds N..K were ... skipped" annotation lists all three classes. |
| **`compute_merged_verdict` reviewer filter** (aggregates only over `returncode == 0` reviewers) | Excludes failed reviewers | Also exclude rate-limited reviewers (`status == "rate-limited"`). A round that is fully rate-limited (no successful reviewer) produces `merged_verdict: null`, mirroring the all-failed case. |
| **`write_merged_findings`** (returns None if all failed) | Returns None when all failed | Also return None when all reviewers are rate-limited (or any mix of failed/rate-limited). No partial findings file. |

`manual-approved` rounds do **not** need bypass treatment — they have a real `verdict: "ready"` and `verdict_valid: true`, so the existing gating machinery accepts them as-is.

### 7.5 Coalescing repeated refusals

Pre-spawn refusals (§7.1) do NOT each append a new chain round. Instead:

1. The first detection of the limit (either via post-failure regex match in §7.2, OR the first pre-spawn refusal when state was set by a *prior session* and the chain has no rate-limited round yet) writes one new round with `status: "rate-limited"`.
2. Subsequent pre-spawn refusals against the *same chain* while the limit is still active find that round at the head and **update its `last_refused_at` timestamp** (and append the new refusal time to a bounded `refused_at[]` list — capped at 20 entries; older entries elided) instead of writing a new round. They still emit the exit-8 JSON and print the menu.
3. Once the limit clears (state's `reset_at <= now()`), the next invocation proceeds normally and writes a fresh round as it always has. The dangling `rate-limited` round at the head is left in place as audit history.
4. If the user picks `manual-approve` or `ingest-response` while the rate-limited round is still at the head, those subcommands write a *new* round (status `manual-approved` or `human-bridged`) immediately after it. The chain advances; the rate-limited round remains as the audit trail of why this happened.

### 7.6 New subcommands

**`manual-approve`**

```
external-reviewer.py manual-approve \
  --kind <kind> --file <target> --work-id <id> \
  --note "operator note"
```

Effects:
- Writes `r{N}-response.md` (next-round-N for the chain) containing:
  ```
  # Manual approval — <chain> r{N}

  Approved by: <git user.name> <git user.email>
  Approved at: <ISO timestamp>

  ## Note
  <operator note>

  ---

  Overall verdict: ready (manual approval)
  ```
- Updates `chain.json` with a new round entry: `status: "manual-approved"`, `verdict: "ready"`, `verdict_valid: true`, `approved_by`, `approved_at`, `approval_note`. The merged-verdict path treats `manual-approved` rounds as `ready` for gating.
- Exits 0.

**`ingest-response`**

```
external-reviewer.py ingest-response \
  --kind <kind> --file <target> --work-id <id> \
  ( --from-paste <FILE> | --from-link <PATH> )
```

- `--from-paste FILE` — the file already contains the user-pasted text (coordinator writes a temp file from chat input).
- `--from-link PATH` — `PATH` is a path/URL to an existing file containing the response. Local files are read directly; remote URLs are out of scope for v1 (the coordinator can `curl` and pass the local copy to `--from-paste`).
- "Reformat if necessary" means:
  1. Strip a single outer ```` ``` ```` fence pair if the entire content is wrapped in one.
  2. Ensure the verdict line is parseable; if the content contains `Overall verdict\n\n<X>` on separate lines (the format that confused the parser this session), rewrite to `Overall verdict: <X>` inline.
  3. Otherwise preserve verbatim.
- Writes the (possibly reformatted) text to `r{N}-response.md`.
- Re-runs the existing verdict parser; updates `chain.json` round entry with the parsed verdict, status `"human-bridged"`, `bridged_by`, `bridged_at`.
- Exits 0 on success, 2 on parse failure (response written but verdict couldn't be parsed; coordinator decides next step).

**`show-limit`**

Reads the state file and pretty-prints it (or `(no active limits)` if absent/empty).

**`clear-limit`**

```
external-reviewer.py clear-limit [--reviewer-cmd <basename>]
```

Removes the entry for the given basename (or all entries if omitted). Idempotent.

## 8. Skill / coordinator integration

`SKILL.md` gains a new section **"Rate-limit handling"** describing:

### 8.1 What the coordinator sees

The `review` subcommand exits **8** with a JSON payload (§7.3). The coordinator parses it, then presents the menu.

### 8.2 The menu

Always presented via `AskUserQuestion` on every rate-limited invocation while the window is open (no auto-pick, no auto-defer):

| Option | Header | Description |
|---|---|---|
| Mark as manually approved | `Manual approve` | Skip the review step; record approval in the chain with the operator's note. |
| Schedule a retry           | `Schedule retry` | Register a Claude scheduled task at `reset_at + 5 min` (buffer configurable) that re-invokes the same `review` command. |
| Human-bridge a response    | `Human bridge`  | Operator manually obtains a response from an external reviewer and pastes / links it back into chat. |
| Hold off                   | `Hold`          | Do nothing this round; exit and let the user decide later. (Always available so the user isn't railroaded.) |

### 8.3 Dispatch

- **Manual approve.** Coordinator collects a one-line operator note via a follow-up `AskUserQuestion`, then runs `external-reviewer.py manual-approve ...`. Commits the resulting chain artifacts at round close-out (same convention as today). Slice/phase advances.
- **Schedule retry.** Coordinator confirms `reset_at` with the user (showing the parsed value + raw stderr tail), then invokes the **harness-level `schedule` skill** (this is a Claude Code harness skill — auto-discovered in the available-skills list at session start; it is not a file in this repo's `skills/` tree) to register a one-shot routine. Routine name: `reviewer-retry-<chain-slug>-r<N>`. Routine prompt: literal re-invocation of the original `external-reviewer.py review ...` command. The coordinator then exits the current chain gate as "deferred" — the in-loop work pauses. When the scheduled task fires, the routine runs in a fresh session and proceeds. **Fallback if the `schedule` skill is unavailable** in the user's harness: the coordinator falls back to printing a one-line `at`/`cron`-suitable command and the absolute path of the original invocation, leaving the user to schedule it themselves. The scheduled-retry path therefore degrades to an instruction rather than failing outright.
- **Human bridge.** Coordinator prints the absolute path to `r{N}-request.md` and asks the user to paste the response in chat OR provide a local file path containing the response. Two intake forms:
  - Paste: coordinator writes the chat text to a tmp file, then runs `ingest-response --from-paste <tmp>`.
  - Link: coordinator runs `ingest-response --from-link <path>` where `<path>` is a local filesystem path. Remote URLs are out of scope for v1 — if the user has only a URL, they fetch it themselves (e.g. via `curl`) and pass the local copy.
  After `ingest-response` exits 0, the chain advances. Exit 2 (parse failure) → coordinator surfaces the issue and asks the user to revise the response.
- **Hold.** Coordinator marks the in-session task pending and stops. State file is unchanged; next session will see the same limit.

### 8.4 Refusal cadence

The script refuses spawn on every invocation while the limit window is open (§7.1). Each refusal triggers the menu — no caching of prior choices, no auto-defer. The user might want a different option per call (different chain, different criticality).

## 9. Tests (TDD)

| Test file | What it covers |
|---|---|
| `test_rate_limit_detection.py`         | Regex match/no-match across at least three stderr fixtures (codex sample + two synthetic). |
| `test_reset_time_parser.py`            | PM/AM, 24-hour, past-time-today wraps to tomorrow, no-time-group fallback. |
| `test_state_file.py`                   | Roundtrip, missing-file noop, expiry-on-read, schema mismatch fail-open, flock acquire/release. |
| `test_exit_code_8.py`                  | Faked rate-limit stderr → exit 8 + JSON payload on stdout + state file written + rate-limited round artifact written. |
| `test_subsequent_invocation_refused.py`| Pre-spawn state check refuses without spawn; expired entry self-clears. |
| `test_sweep_partial_rate_limit.py`     | Primary ok, sweep rate-limited → round still ok (sweep excluded from merged verdict), state file written. |
| `test_manual_approve_subcommand.py`    | Writes synthetic response, updates chain, verdict ready, exits 0. |
| `test_ingest_response_subcommand.py`   | `--from-paste` and `--from-link`; reformat strips single outer fence pair; rewrites stray `Overall verdict\n\n<X>` to inline form; preserves verbatim otherwise. Exit 2 on unparseable. |
| `test_show_clear_limit.py`             | `show-limit` prints state; `clear-limit` removes entry; `--reviewer-cmd` filter works; idempotent. |
| `test_rate_limited_status_semantics.py`| Resolution gate bypasses on `rate-limited` predecessor; preamble walk-back skips `rate-limited` rounds; merged-verdict excludes rate-limited reviewers; `write_merged_findings` returns None when all reviewers are rate-limited/failed. |
| `test_refusal_coalescing.py`           | First refusal writes a `rate-limited` round; subsequent refusals on the same chain update `last_refused_at`/`refused_at[]` and DO NOT append a new round; cap at 20 entries respected. |

All tests MUST set `AGENT_REVIEWER_STATE_FILE` to a `tmp_path`-scoped file so they never touch the developer's real `~/.config/superstar/reviewer-state.json`.

Existing 142 tests must remain green.

## 10. Edge cases + decisions captured

- **Local-time TZ.** The reviewer's error message has no timezone; we interpret it in the host's local time. Documented in SKILL.md; the user-confirmation step before scheduling is the safety valve.
- **`AGENT_REVIEWER_CMD` is a template (e.g. `bash -c 'reviewer ...'`).** The basename used for state-keying is the first whitespace-separated token (`bash` in this example). Coarse but predictable. Users with multiple distinct backends behind shell wrappers can set `AGENT_REVIEWER_STATE_KEY` to override the key explicitly.
- **No git user.name configured.** Manual-approve falls back to `$USER@$HOSTNAME`. Never blocks.
- **Coordinator forgets the menu.** The `SKILL.md` red-flags table gains an entry: "Saw exit 8, retried without surfacing the menu." Documentation only.
- **Scheduled task fires while another session is already running a different chain through the same reviewer.** The scheduled task's `review` invocation does its own pre-spawn check; if the limit was reset and the reviewer is now available, it runs. If it's still limited (unlikely if the schedule offset > reset time), it exits 8 in its own session — the user can pick again from that session.

## 11. Acceptance gate

- Existing test suite green (142 → 142+11 with new tests).
- `detect_rate_limit` correctly identifies the codex sample stderr captured in this session.
- A faked rate-limit run produces: exit 8, JSON payload with parseable `reset_at`, state file written under `~/.config/superstar/`, rate-limited round artifact written to the chain.
- A subsequent run with the state file still active refuses without spawn (verified by counting subprocess calls in the test).
- `manual-approve` writes a synthetic round whose verdict is `ready` and whose `chain.json` entry round status is `manual-approved`.
- `ingest-response --from-paste` and `--from-link` both produce a chain-advancing response.md and a parseable verdict.
- SKILL.md documents the exit code, the menu, and the three dispatch paths.
- Resolution gate bypasses on `rate-limited` predecessor (verified by test).
- All tests use `AGENT_REVIEWER_STATE_FILE` override; the developer's real `~/.config/superstar/reviewer-state.json` is never touched by the suite.

## 12. Open questions

None at spec time. Any new ambiguity discovered during planning gets flagged before code lands.

## 13. Out-of-band note

External-review (the skill that would normally gate this spec) is bypassed for this work session per user instruction — the reviewer CLI is itself rate-limited. The spec and downstream plan/implementation will proceed without the `--kind spec` / `--kind plan` / `--kind post-slice` / `--kind post-phase` gates. Subagents dispatched during implementation will receive explicit instructions NOT to invoke `superstar:external-review` for any reason. This bypass ends when the rate-limit clears OR when this feature lands (after which future work will use the new menu instead of bypassing).
