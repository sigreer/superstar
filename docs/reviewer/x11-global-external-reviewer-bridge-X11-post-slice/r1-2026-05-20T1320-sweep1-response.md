# Review — 2026-05-20-X11-global-external-reviewer-bridge.md (post-slice, round 1)

- Target: `docs/plans/2026-05-20-X11-global-external-reviewer-bridge.md`
- Request: `docs/reviewer/x11-global-external-reviewer-bridge-X11-post-slice/r1-2026-05-20T1320-sweep1-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

# Post-slice review: X11 — Global external-reviewer bridge

## Findings

**F1. Installer diverges from plan snippet (undocumented `$HOME` substitution). Severity: minor**

`skills/external-review/install.sh:28-37` substitutes the `$HOME` prefix in the generated shim's source path. The plan snippet (Task 2 Step 1) shows a literal `exec python3 "$SOURCE_SCRIPT" "$@"` with no substitution. The substitution is necessary to satisfy `test_installer_writes_source_tree_shim_to_configured_bin`'s assertion `"/home/simon/" not in text`, which the plan's literal code would have failed. The implementation choice is sound but the plan and resulting code disagree, which is the kind of silent drift the spec was written to prevent. Either:
- update the plan/spec to call out that the shim must use `$HOME/...` when the source lies under `$HOME` (and document why), or
- accept it as a Task 5 docs-cleanup edit.

**F2. `--reviewer-provider` / `--caller-provider` not documented. Severity: minor**

Task 5 Step 6 invokes `external-reviewer review` with `--reviewer-provider claude --caller-provider codex`, but the main command block in `skills/external-review/SKILL.md:90-99` does not list these flags. Either prune them from the plan's invocation (they are not strictly necessary) or extend the documented command surface so future operators understand them.

**F3. Compatibility-shim audit row doesn't define `Partial` vs `Compatibility-pass` resolution. Severity: minor**

`skills/project-setup/SKILL.md:37` (row 7b) says "Partial for any other local file. … Offer to replace it with `skills/project-setup/scripts/external-reviewer-shim.py`; do not copy the full bridge." The spec (lines 188-195) explicitly defines three states (`Pass`, `Compatibility-pass`, `Partial`); the audit row collapses Pass and Compatibility-pass into one prose line and only labels Partial. A reviewer/auditor reading the table cannot tell at a glance how to mark a confirming compatibility shim. Consider explicit triple-state phrasing.

**F4. Uncommitted `docs/tasklist.json` and untracked chain folder. Severity: nit (expected)**

`git status` shows `M docs/tasklist.json` (`started`/`status` flipped to `in_progress`) and an untracked `docs/reviewer/x11-global-external-reviewer-bridge-X11-post-slice/`. Both are expected for Task 5 Step 6; they will be committed in Step 7. Flagging only so the closeout commit does not silently include unrelated changes.

**F5. Fixture file matches a stale-pattern grep. Severity: nit**

`skills/external-review/tests/fixtures/claude-heading-revise.md:100` contains the literal string `python3 scripts/external-reviewer.py`. It is clearly historical-reviewer fixture content (not guidance), but the plan's broader Step 4 grep will surface it. The plan already covers this case ("Fixture or historical-review occurrences are acceptable"). No action needed beyond not deleting the fixture.

## Open questions / assumptions

- Assumed Task 5 Steps 1-3 (focused tests, broader verification, installer smoke) were run by the implementer prior to opening this post-slice round. The chain has `r1-…-primary-request.md` and `…-sweep1-request.md` but `chain.json` shows `rounds: []`, which is consistent with a round in flight rather than a missed test pass. Verification commands below should be confirmed.
- Assumed the `$HOME`-prefixed shim works on Codex/CI hosts where `$HOME` may resolve via realpath differently from the worktree's literal prefix. Not exercised by the test suite.

## Suggested document edits

- Plan Task 2 Step 1: replace the literal heredoc with the actual installer behavior (including the `$HOME` substitution branch), or add a one-line note explaining why the literal shim differs from what gets written.
- Plan Task 5 Step 6: either drop `--reviewer-provider claude --caller-provider codex` or add a one-line rationale; document the flags in `skills/external-review/SKILL.md` if they are intended to be visible.
- `skills/project-setup/SKILL.md:37`: split row 7b verdicts into three explicit clauses (Pass / Compatibility-pass / Partial) so audit output is unambiguous.

## Verification gaps / commands to run

The reviewer cannot execute commands from this gate. Confirm before closing X11:

```bash
python3 -m pytest skills/external-review/tests/test_external_reviewer_installer.py skills/external-review/tests/test_external_reviewer_compat_shim.py -q
bash tests/claude-code/test-external-reviewer-global-command.sh
bash tests/claude-code/test-autonomous-review-gates.sh
tools/tasktool/tasktool validate
tmp_bin="$(mktemp -d)"; EXTERNAL_REVIEWER_BIN="$tmp_bin" bash skills/external-review/install.sh && PATH="$tmp_bin:$PATH" external-reviewer --help >/dev/null && echo SMOKE_OK
```

Spot check (not in plan) — confirm the generated shim still works when `SOURCE_SCRIPT` is outside `$HOME`:

```bash
sudo -E env HOME=/nonexistent EXTERNAL_REVIEWER_BIN=/tmp/bin bash skills/external-review/install.sh   # informational only
```

(Optional; failure here would only matter for atypical deployments.)

Overall verdict: ready with small edits
