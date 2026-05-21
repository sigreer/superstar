# Merged findings for r3

## Primary

# Review — 2026-05-21-X16-shim-version-stamping.md (post-slice, round 3)

- Target: `docs/plans/2026-05-21-X16-shim-version-stamping.md`
- Request: `docs/reviewer/x16-shim-version-stamping-X16-post-slice/r3-2026-05-21T0517-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F1 — RESOLVED — The tracker still shows X16 as `ready`, but the r2 resolution correctly treats `tasktool close X16` as the coordinator’s next step after this review returns `ready`. The plan explicitly sequences review iteration before closeout at `docs/plans/2026-05-21-X16-shim-version-stamping.md:2357` and runs `tasktool close X16` at `docs/plans/2026-05-21-X16-shim-version-stamping.md:2362`. I no longer consider this a blocking review finding.

F2 — RESOLVED — `scripts/deploy.sh --check` now includes a `Pre-commit hook:` section and calls `check_hook` from `run_check` at `scripts/deploy.sh:270`. The implementation resolves the hook path with `git rev-parse --git-path hooks/pre-commit`, parses stamped hook headers, and applies failing statuses for missing/malformed/drift/source-missing states at `scripts/deploy.sh:130`. Focused coverage exists in `scripts/tests/test_deploy_check.py:153`.

F3 — RESOLVED — `check_pre_commit_hook()` now resolves the hook path through `_git_hook_path()` using `git rev-parse --git-path hooks/pre-commit` at `tools/tasktool/hook_handshake.py:37` and uses it at `tools/tasktool/hook_handshake.py:80`. The linked-worktree regression is covered by `tools/tasktool/tests/test_hook_handshake.py:113`.

2. Open questions / assumptions

I assume the coordinator will run the documented closeout immediately after this ready verdict, then commit the reviewer-chain artifacts and tracker mutation together as the final closeout evidence.

3. Suggested document edits

No blocking edits. The r2 resolution is sufficient.

4. Verification gaps / commands that should be run

Fresh verification I ran:

```bash
python3 -m pytest scripts/tests/test_deploy_check.py -v
# 13 passed

python3 -m pytest tools/tasktool/tests/test_hook_handshake.py tools/tasktool/tests/test_pre_commit_hook.py -v
# 23 passed

bash scripts/deploy.sh --check
# exited 0 and printed Pre-commit hook: pre-commit OK v6.5.0

tools/tasktool/tasktool show X16
# still ready, as expected before coordinator closeout
```

Overall verdict: ready


## Sweep 1

# Review — 2026-05-21-X16-shim-version-stamping.md (post-slice, round 3)

- Target: `docs/plans/2026-05-21-X16-shim-version-stamping.md`
- Request: `docs/reviewer/x16-shim-version-stamping-X16-post-slice/r3-2026-05-21T0517-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

S1.F4 — Severity: blocking — The documented full test gate does not pass. The plan’s closeout command requires `python3 -m pytest scripts/tests/ tools/tasktool/tests/ skills/external-review/tests/ -v` and expects every test to pass at `docs/plans/2026-05-21-X16-shim-version-stamping.md:2305`. Running that command fails during collection with 62 `ModuleNotFoundError: No module named 'tests.test_...'` errors for `skills/external-review/tests/*`. This appears caused by the newly added package marker `scripts/tests/__init__.py` colliding with the existing `tests` packages under other subtrees. Focused files pass individually, but the required aggregate gate is broken.

2. Open questions / assumptions

I assume `tasktool close X16` remains intentionally deferred until this review returns ready; `tasktool show X16` still reports `status: ready`.

3. Suggested document edits

No document-only edit is enough for S1.F4. Fix the pytest package collision, likely by removing `scripts/tests/__init__.py` if it is not needed, or by adding a repo-level pytest import-mode/configuration that makes the exact Step 11 command pass.

4. Verification gaps / commands that should be run

I ran:
```bash
bash scripts/deploy.sh --check
tools/tasktool/tasktool validate --strict-format
tools/tasktool/tasktool artifact status X16 --strict
bash scripts/bump-version.sh --check
python3 -m pytest scripts/tests/test_deploy_check.py tools/tasktool/tests/test_hook_handshake.py tools/tasktool/tests/test_pre_commit_hook.py -q
python3 -m pytest skills/external-review/tests/test_external_reviewer_installer.py -q
python3 -m pytest scripts/tests/test_bump_version_plain_format.py scripts/tests/test_shim_version_check_fragment.py scripts/tests/test_install_reviewer_agent.py tools/tasktool/tests/test_tasktool_shim_install.py -q
```

The exact full pytest gate from Step 11 fails and must be rerun after the fix:
```bash
python3 -m pytest scripts/tests/ tools/tasktool/tests/ skills/external-review/tests/ -v
```

Overall verdict: revise

