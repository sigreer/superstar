1. Findings

F1. RESOLVED — Test commands consistently include `PYTHONPATH=tools`.

F2. RESOLVED — `init --project` is optional and the CLI acceptance flow covers init/create/show.

F3. RESOLVED — `_resolve_id()` and short-ID tests are present for note/create paths and ambiguity rejection.

F4. Severity: important — Still partially unresolved: date validation now rejects impossible calendar dates, but it no longer enforces the spec’s literal `YYYY-MM-DD` shape. The spec says ISO 8601 date `YYYY-MM-DD` at [docs/specs/2026-05-17-P2-tasktool-design.md:160](/home/simon/Dev/sigreer/skills/superstar/docs/specs/2026-05-17-P2-tasktool-design.md:160). The plan uses only `_dt.date.fromisoformat(value)` at [docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:897](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:897), which on Python 3.11 accepts values such as `20260228` and `2026-W09-6`. Those pass validation despite not matching `YYYY-MM-DD`, and they also make the later string comparison at line 912 unsafe. Keep the real-date check, but pair it with a strict `^\d{4}-\d{2}-\d{2}$` shape check.

F5. RESOLVED — Global flags and `--no-stage` handling are covered.

F6. RESOLVED — Task 13 and final full-suite commands use explicit discovery with `PYTHONPATH=tools`.

F7. RESOLVED — Task 8 no longer calls `_resolve_id()` before it exists; Task 9 defines `_resolve_id()` before the replacement `cmd_create_task()`.

F8. Severity: important — New short-ID regression in review-gated `set` / `close`: `_find_item()` resolves short IDs internally, but `cmd_set()` and `cmd_close()` discard the resolved qualified ID and pass the original `id` into `_apply_review_gate()` at [docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:1893](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:1893), [1899](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:1899), [1912](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:1912), and [1917](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:1917). Reviewer discovery tokenizes the passed work ID at [1344-1362](/home/simon/Dev/sigreer/skills/superstar/docs/plans/2026-05-17-p2-s1-tasktool-cli-core.md:1344), so `tasktool close S1` can search for broad token `s1` instead of `p2-s1`, causing false multiple matches when historical `p1-s1-post-slice` chains exist. Return the qualified ID from `_find_item()` or resolve once in `cmd_set()` / `cmd_close()` and pass the qualified ID to the gate.

2. Open questions / assumptions

- I’m treating `YYYY-MM-DD` as a strict persisted format, not any Python-supported ISO date variant.
- I’m assuming `docs/reviewer/` can contain historical chains for archived or prior phases, which makes short review-gate IDs unsafe unless normalized to qualified IDs.

3. Suggested document edits

- In `_check_date()`, first require `re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)`, then call `date.fromisoformat(value)`.
- Add tests rejecting `20260228` and `2026-W09-6`.
- Change `_find_item()` to return `(qid, container_list, item)` or have callers call `_resolve_id()` once and pass `qid` through to `_apply_review_gate()`.
- Add a command test for closing an unambiguous short slice when both `p1-s1-post-slice` and the correct `p2-s1-post-slice` folders exist.

4. Verification gaps / commands

- `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_validate -v`
- `PYTHONPATH=tools python3 -m unittest tools.tasktool.tests.test_commands -v`
- `PYTHONPATH=tools python3 -m unittest discover -s tools/tasktool/tests -v`

5. Overall verdict: revise