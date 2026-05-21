# Review — 2026-05-21-X16-shim-version-stamping.md (post-slice, round 3)

- Target: `docs/plans/2026-05-21-X16-shim-version-stamping.md`
- Request: `docs/reviewer/x16-shim-version-stamping-X16-post-slice/r3-2026-05-21T0517-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `codex`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

1. Findings

F4 — Severity: blocking — The documented full test gate does not pass. The plan’s closeout command requires `python3 -m pytest scripts/tests/ tools/tasktool/tests/ skills/external-review/tests/ -v` and expects every test to pass at `docs/plans/2026-05-21-X16-shim-version-stamping.md:2305`. Running that command fails during collection with 62 `ModuleNotFoundError: No module named 'tests.test_...'` errors for `skills/external-review/tests/*`. This appears caused by the newly added package marker `scripts/tests/__init__.py` colliding with the existing `tests` packages under other subtrees. Focused files pass individually, but the required aggregate gate is broken.

2. Open questions / assumptions

I assume `tasktool close X16` remains intentionally deferred until this review returns ready; `tasktool show X16` still reports `status: ready`.

3. Suggested document edits

No document-only edit is enough for F4. Fix the pytest package collision, likely by removing `scripts/tests/__init__.py` if it is not needed, or by adding a repo-level pytest import-mode/configuration that makes the exact Step 11 command pass.

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
