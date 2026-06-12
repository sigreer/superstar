# Review — 2026-06-06-X29-timeline-generator.md (post-slice, round 1)

- Target: `docs/plans/2026-06-06-X29-timeline-generator.md`
- Request: `docs/reviewer/x29-timeline-generator-X29-post-slice/r1-2026-06-06T2353-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1. Severity: blocking  
The visual acceptance gate is still open. The close note says the browser eyeball check is “pending in parallel with this review” (`docs/handoffs/2026-06-06-X29-slice-close-note.md:27`), but Task 14 explicitly requires the human partner to open both generated HTML files and check braid/cards/gaps/X toggle/click expansion (`docs/plans/2026-06-06-X29-timeline-generator.md:2319-2322`). The spec intentionally makes this the substitute for pixel/visual regression testing (`docs/specs/2026-06-06-X29-timeline-design.md:212`). Do not close X29 until that check is completed or explicitly waived.

F2. Severity: important  
The default-suite acceptance criterion is not met as written. The plan says `python3 -m pytest -q` should pass (`docs/plans/2026-06-06-X29-timeline-generator.md:2299-2302`), while the close note records `1070 passed, 109 failed + 23 errors` and asserts the failures are byte-identical to `main` (`docs/handoffs/2026-06-06-X29-slice-close-note.md:23-24`). That may be an acceptable baseline exception, but the repo artifact does not include durable proof of the comparison. Either attach the baseline command/output artifact or edit the close note to identify where that evidence lives.

2. Open questions / assumptions

I assume the untracked `docs/reviewer/x29-timeline-generator-X29-post-slice/` files are this active review chain and are expected to be registered after the verdict. I also assume the dirty `multistore` deletion (`docs/agent-prompts/planner.md`) was pre-existing; the backfill dry-run I ran did not write files.

3. Suggested document edits

Update the close note’s acceptance section to record the completed human browser check with date/person and any observations, or state an explicit waiver.

Add a short evidence pointer for the default-suite baseline comparison, for example a log path or exact clean-clone command/output summary, so the “pre-existing failures” claim is auditable.

4. Verification gaps / commands that should be run

I ran:

```bash
python3 -m pytest tools/timeline/tests -q
# 73 passed, 1 pytest cache warning due read-only cache path

python3 -m pytest -q --collect-only
# 1202 tests collected, including tools/timeline/tests

python3 tools/timeline/timeline.py --repo . -o /tmp/superstar-timeline-review.html
python3 tools/timeline/timeline.py --repo /home/simon/Dev/sigreer/multistore -o /tmp/multistore-timeline-review.html
# multistore smoke: phase-node 13, 15:51 1, x-node 19

python3 tools/timeline/backfill.py --repo /home/simon/Dev/sigreer/multistore
# dry-run produced 17 file diffs
```

Still needed: the human browser eyeball check, and durable proof for the full-suite baseline exception.

Overall verdict: revise
