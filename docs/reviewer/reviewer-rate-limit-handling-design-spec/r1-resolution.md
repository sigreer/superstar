# Resolution for r1

## F1
Status: fixed
Evidence:
- Files: `docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md` §6 patterns table
- Verification: visual inspection of the three regex entries — the pipes inside `(?:AM|PM)`, `(?:at|in)`, `(?:after|at)` are no longer escaped.

Notes:
The escaped pipes were a markdown-table artifact. The codex regex now correctly alternates `AM`/`PM`. The two stub patterns (claude/gemini) had the same artifact in their `(?:at|in)` / `(?:after|at)` groups and were fixed at the same time. The codex regex entry also adds a parenthetical clarifying that the compiled pattern uses an unescaped pipe regardless of how it renders in the table.

## F2
Status: fixed
Evidence:
- Files: `docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md` new §7.4 ("Rate-limited status semantics") and §7.5 ("Coalescing repeated refusals"); §9 adds two new test files.
- Verification: §7.4 enumerates the four script sites that need updates (resolution gate, preamble walk-back, merged-verdict reviewer filter, write_merged_findings). §7.5 specifies that pre-spawn refusals coalesce onto the head rate-limited round rather than appending fresh rounds — addressing the reviewer's open question about repeated-hold noise.

Notes:
The four sites mirror the treatment of `status: "failed"` that S1 already shipped. `manual-approved` rounds do not need bypass treatment because they carry a real `ready` verdict.

## F3
Status: fixed
Evidence:
- Files: `docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md` §8.3 schedule-retry paragraph
- Verification: section now explicitly states `schedule` is a Claude Code harness skill (auto-discovered in the available-skills list at session start, not a repo skill file), and documents a fallback path when the harness skill is unavailable: print an at/cron-suitable command for the user to run.

Notes:
The `schedule` skill is visible in this session's available-skills list. It's a harness-level skill, not under `skills/`. The fallback ensures the spec degrades to "instruction for the user" rather than failing if the harness lacks the skill (e.g. another harness running this same external-review code).

## F4
Status: fixed
Evidence:
- Files: `docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md` §5 (state-file location)
- Verification: §5 now specifies `AGENT_REVIEWER_STATE_FILE` env var AND a `--state-file PATH` CLI flag on every subcommand that touches state. §9 adds a sentence requiring all tests use the env var override.

Notes:
Both env-var and CLI-flag overrides are specified so tests can use whichever is most convenient. §11 acceptance gate updated to require that the suite never touches the developer's real state file.

## F5
Status: fixed
Evidence:
- Files: `docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md` §4 architecture summary
- Verification: "Three new subcommands" → "Four new subcommands". The list following it already named four; this was a count typo.

## Open question (reviewer)
The reviewer asked whether every refused invocation appends a new chain round. Answered explicitly in §7.5: NO — repeated refusals coalesce onto the head rate-limited round via `last_refused_at` / `refused_at[]`. Cap at 20 refusal timestamps (older entries elided) to bound the growth.
