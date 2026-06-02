1. Findings

F1. Severity: blocking — RESOLVED. Step 8’s helper now captures `before`, runs the reviewer, captures `after`, and returns only `after - before`, so the distinct-work-id collision check no longer self-intersects on earlier artifacts. See `docs/plans/2026-06-02-P7-S8-reviewer-artifact-investigation.md:101-114`.

F2. Severity: important — RESOLVED. Branch A now specifies a timestamp override and threads it into the proposed test helper via `fake_timestamp`, so the same-work-id regression tests no longer depend on crossing or not crossing a wall-clock minute boundary. See `docs/plans/2026-06-02-P7-S8-reviewer-artifact-investigation.md:196-204` and `:283-327`.

F3. Severity: important — RESOLVED. Branch B still uses the sanctioned no-code lifecycle: persist the decision artifact, then `tasktool cancel P7.S8 --reason ...`. See `docs/plans/2026-06-02-P7-S8-reviewer-artifact-investigation.md:362-373`.

F4. Severity: important — RESOLVED. Branch A now covers the late final-ready primary rename path at `external-reviewer.py:2694-2698`, derives the original unique token from the current request filename, and requires coverage for that path or an explicit reachability constraint. See `docs/plans/2026-06-02-P7-S8-reviewer-artifact-investigation.md:221-244` and `:329-349`.

F5. Severity: minor — Step 9.2 asks the implementer to capture post-phase output but does not provide an executable harness like Step 9.1 does. The existing helper in Step 9.1 hard-codes `--kind post-slice` at `docs/plans/2026-06-02-P7-S8-reviewer-artifact-investigation.md:155`, while Step 9.2 only describes `kind="post-phase"` in prose at `:165`. This is not blocking, but adding the concrete command or parameterizing the snippet would reduce execution drift.

2. Open questions / assumptions

I assume Branch A remains conditional and should only be executed if the investigation finds a workflow-reachable Class A collision, matching the decision gate at `docs/plans/2026-06-02-P7-S8-reviewer-artifact-investigation.md:381-387`.

3. Suggested document edits

- Add a short runnable Step 9.2 snippet or update the Step 9.1 helper to accept `kind` and `work_id`, then show the exact `post-phase` invocation.
- Optionally change the line 18 wording from “close with no source change” to “terminate with no source change” to avoid conflicting with the later, more precise `cancel` instruction.

4. Verification gaps / commands that should be run

- The plan’s required gates are appropriate: Step 8 distinct-work-id repro, Step 9 misuse/post-phase probes, Branch A targeted tests if selected, and full `python -m pytest skills/external-review/tests -q` plus `python -m pytest tools/tasktool/tests -q` if code changes ship.
- No additional blocking verification gap found for the plan itself.

Overall verdict: ready with small edits

