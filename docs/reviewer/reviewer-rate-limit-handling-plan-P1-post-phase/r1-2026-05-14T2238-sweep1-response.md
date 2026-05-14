# Review — 2026-05-14-reviewer-rate-limit-handling-plan.md (post-phase, round 1)

- Target: `docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md`
- Request: `docs/reviewer/reviewer-rate-limit-handling-plan-P1-post-phase/r1-2026-05-14T2238-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Status: `ok`

---

1. **Findings**

F1 — Severity: blocking — State-file locking still does not meet the spec’s global cross-session requirement. The spec requires `fcntl.flock(LOCK_EX)` on the state file for reads/writes and serialized writers ([docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md:79)). Current `load_state()` reads with `path.read_text()` and no lock, while `save_state()` locks only the temporary file before `os.replace()` ([external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:185), [external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:200)). Two sessions updating different reviewer keys can still lose updates.

F2 — Severity: important — `--reviewer-cmd` is ignored for state-key resolution, so CLI-selected backends can collide under `reviewer-agent`. The script exposes `--reviewer-cmd` as the configured reviewer command ([external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:1320)), but `reviewer_cmd_basename()` only reads `AGENT_REVIEWER_CMD` / `AGENT_REVIEWER_STATE_KEY` and falls back to `"reviewer-agent"` ([external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:243)). This violates the spec’s per-reviewer-binary state key intent ([design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md:75)) when operators pass reviewer commands via CLI.

F3 — Severity: important — Expiry-on-read is not applied uniformly to state reads. The spec says expired `reset_at` entries are cleared on read ([design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md:78)). Current expiry logic exists only in `get_active_limit()` ([external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:220)); `show-limit` calls `load_state()` directly and can display expired entries as active ([external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:1569)).

F4 — Severity: minor — Phase close says finishing integration was invoked, but the commit evidence says it was only ready for that step. The plan marks “Invoke `superstar:finishing-a-development-branch`” complete ([plan.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md:2984)); `HEAD` commit message ends “Ready for finishing-a-development-branch.” I also found no `TASKLIST.md` or archive update in the repo tree.

2. **Open questions / assumptions**

I assume concurrent sessions remain in scope because the feature persists a global per-user state file. I also assume `--reviewer-cmd` is a supported production path, not just a test hook, because SKILL.md documents env-or-flag configuration.

3. **Suggested document edits**

Add closeout notes for the unresolved state-locking and state-key issues, or reopen the relevant tasks. If TASKLIST/archive is intentionally absent in this fork, add a short waiver note to the phase close.

4. **Verification gaps / commands**

Fresh verification run:

```bash
python3 -m pytest skills/external-review/tests/ -q
# 194 passed, 1 warning
```

Add targeted tests for concurrent writes preserving multiple reviewer keys, `--reviewer-cmd` state-keying, and `show-limit` pruning expired limits.

5. **Overall verdict**

revise. The suite is green, but the phase still misses core acceptance behavior around global state correctness.

---

## Reviewer stderr (tail)

```text
d uniformly to state reads. The spec says expired `reset_at` entries are cleared on read ([design.md](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md:78)). Current expiry logic exists only in `get_active_limit()` ([external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:220)); `show-limit` calls `load_state()` directly and can display expired entries as active ([external-reviewer.py](/home/simon/Dev/sigreer/skills/superstar/skills/external-review/scripts/external-reviewer.py:1569)).

F4 — Severity: minor — Phase close says finishing integration was invoked, but the commit evidence says it was only ready for that step. The plan marks “Invoke `superstar:finishing-a-development-branch`” complete ([plan.md](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md:2984)); `HEAD` commit message ends “Ready for finishing-a-development-branch.” I also found no `TASKLIST.md` or archive update in the repo tree.

2. **Open questions / assumptions**

I assume concurrent sessions remain in scope because the feature persists a global per-user state file. I also assume `--reviewer-cmd` is a supported production path, not just a test hook, because SKILL.md documents env-or-flag configuration.

3. **Suggested document edits**

Add closeout notes for the unresolved state-locking and state-key issues, or reopen the relevant tasks. If TASKLIST/archive is intentionally absent in this fork, add a short waiver note to the phase close.

4. **Verification gaps / commands**

Fresh verification run:

```bash
python3 -m pytest skills/external-review/tests/ -q
# 194 passed, 1 warning
```

Add targeted tests for concurrent writes preserving multiple reviewer keys, `--reviewer-cmd` state-keying, and `show-limit` pruning expired limits.

5. **Overall verdict**

revise. The suite is green, but the phase still misses core acceptance behavior around global state correctness.
tokens used
101,842
```
