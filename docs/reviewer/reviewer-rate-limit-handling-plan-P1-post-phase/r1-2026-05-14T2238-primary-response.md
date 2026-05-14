# Review — 2026-05-14-reviewer-rate-limit-handling-plan.md (post-phase, round 1)

- Target: `docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md`
- Request: `docs/reviewer/reviewer-rate-limit-handling-plan-P1-post-phase/r1-2026-05-14T2238-primary-request.md`
- Reviewer command: `reviewer-agent`
- Status: `ok`

---

1. **Findings**

F1 — Severity: important — State locking does not satisfy the spec’s cross-session safety requirement.  
Spec says reads/writes use `fcntl.flock(LOCK_EX)` on the state file and writes serialize across processes ([spec line 79](docs/specs/2026-05-14-reviewer-rate-limit-handling-design.md:79)). Implementation reads with `path.read_text()` and no lock, and writes under a lock on `reviewer-state.json.tmp`, not the shared state file ([external-reviewer.py:185](skills/external-review/scripts/external-reviewer.py:185), [external-reviewer.py:200](skills/external-review/scripts/external-reviewer.py:200)). Concurrent writers can race and overwrite each other’s `limits` map.

F2 — Severity: important — Claude rate-limit reset parsing uses the wrong capture group.  
`detect_rate_limit()` always parses `m.group(1)` ([external-reviewer.py:281](skills/external-review/scripts/external-reviewer.py:281)), but the Claude built-in regex captures `(rate limit|rate-limited)` as group 1 and the reset text as group 2 ([external-reviewer.py:257](skills/external-review/scripts/external-reviewer.py:257)). A Claude message with `reset at 18:30` will be detected but scheduled from fallback time, not the actual reset. Use a non-capturing alternation or select the last non-empty group.

F3 — Severity: minor — Phase close claims the branch-finishing step was invoked, but the repository evidence does not show that closeout happened.  
The plan marks “Invoke `superstar:finishing-a-development-branch`” complete ([plan line 2984](docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md:2984)), while the closeout commit message says “Ready for finishing-a-development-branch,” not that it ran. I also found no `docs/TASKLIST.md` or archive update. If this repo intentionally has no tracker, document that waiver; otherwise this is closeout drift.

2. **Open Questions / Assumptions**

- I assume concurrent sessions are in scope because the spec explicitly calls out global state and flock behavior.
- I assume the missing TASKLIST/archive is either a known repo setup gap or a bypass, but the plan should say so.

3. **Suggested Document Edits**

- Add a closeout note recording the actual verification evidence directly in the plan, not only in the commit message: `194 passed, 1 warning`, smoke exit codes `8/8/0`, and no spawn evidence.
- Add a short waiver note for missing `docs/TASKLIST.md` / archive, or perform the archive update if the tracker exists elsewhere.
- Add a task or follow-up item for state-file locking and Claude capture-group correction.

4. **Verification Gaps / Commands**

Already run locally:

```bash
python3 -m pytest skills/external-review/tests/ -q
# 194 passed, 1 warning
```

I also ran the rate-limit smoke path successfully: first review exited `8`, second refused pre-spawn with exit `8`, `spawn-evidence` was absent, and `manual-approve` exited `0`.

Add targeted tests for:
- concurrent state writes preserving multiple reviewer keys;
- `detect_rate_limit("rate limit ... reset at 18:30")` parsing `18:30` for the Claude pattern.

5. **Overall Verdict**

**revise**. The feature is largely implemented and verified, but the state-file locking mismatch is a real spec violation for the global cross-session behavior.

---

## Reviewer stderr (tail)

```text
52:                returncode=0, status="rate-limited",
1056:            "status": "rate-limited",
1111:                # Spec §7.4/§7.5: a rate-limited sweep does NOT abort the round.
1114:                # status="rate-limited" in the round-entry by the caller.
1122:                    returncode=result.returncode, status="rate-limited",
1129:                "status": "rate-limited",
1195:    - If the primary reviewer's status is not "ok" (failed, rate-limited, etc.),
1201:      because a rate-limited round could in principle exit 0 while still
1233:    Reviewers whose status is not "ok" (failed, rate-limited, etc.) are
1297:def parse_args() -> argparse.Namespace:
1438:def run_manual_approve(args) -> int:
1480:        "status": "manual-approved",
1510:def run_ingest_response(args) -> int:
1551:        "status": "human-bridged",
1569:def run_show_limit(args) -> int:
1578:def run_clear_limit(args) -> int:
1677:def main() -> int:
1680:    if getattr(args, "state_file", None):
1681:        os.environ["AGENT_REVIEWER_STATE_FILE"] = args.state_file
1798:        prior_status = prior.get("status")  # "ok" | "failed" | "rate-limited" | "unknown" | None
1799:        BYPASS_STATUSES = {"failed", "rate-limited"}
2006:            print(f"Reviewer rate-limited until {exc.reset_at}. See {exc.request_path}.")

exec
/usr/bin/zsh -lc "nl -ba docs/reviewer/reviewer-rate-limit-handling-plan-P1-post-phase/chain.json && nl -ba docs/reviewer/reviewer-rate-limit-handling-plan-P1-post-phase/r1-2026-05-14T2238-primary-request.md | sed -n '1,220p'" in /home/simon/Dev/sigreer/skills/superstar
 succeeded in 0ms:
     1	{
     2	  "schema_version": 1,
     3	  "chain": "reviewer-rate-limit-handling-plan-P1-post-phase",
     4	  "kind": "post-phase",
     5	  "target": "docs/plans/2026-05-14-reviewer-rate-limit-handling-plan.md",
     6	  "work_id": "P1",
     7	  "legacy_migrated": false,
     8	  "rounds": [],
     9	  "sweep_checkpoints": {
    10	    "first-round": "pending",
    11	    "final-ready": "pending"
    12	  }
    13	}
     1
```
