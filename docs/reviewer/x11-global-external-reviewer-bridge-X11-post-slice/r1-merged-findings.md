# Merged findings for r1

## Primary

# Review — 2026-05-20-X11-global-external-reviewer-bridge.md (post-slice, round 1)

- Target: `docs/plans/2026-05-20-X11-global-external-reviewer-bridge.md`
- Request: `docs/reviewer/x11-global-external-reviewer-bridge-X11-post-slice/r1-2026-05-20T1320-primary-request.md`
- Reviewer command: `reviewer-agent`
- Reviewer provider: `claude`
- Sandbox: repo read-only; scratch/output writable
- Status: `ok`

---

# Post-slice review: X11 global external-reviewer bridge

## Findings

**F1 — `test_compat_shim_missing_global_command_exits_127` is environment-leaky.** Severity: minor
The test at `skills/external-review/tests/test_external_reviewer_compat_shim.py:47-55` builds `env["PATH"] = f"{path}:{env.get('PATH', '')}"`, prepending an empty `tmp_path/empty` directory but keeping the inherited `PATH`. If the developer running the suite has already executed `skills/external-review/install.sh` against the default `~/.local/bin` (the very thing this slice teaches users to do), `shutil.which("external-reviewer")` will resolve to the real shim and the test will fall through to delegation instead of failing with exit 127. Fix by setting `env["PATH"] = str(path)` (or explicitly only the temporary bin + `/usr/bin:/bin`). Same fragility does not affect `test_compat_shim_refuses_self_resolution` because the symlinked fake takes priority.

**F2 — `install.sh` `$HOME` substitution is undocumented and diverges from the plan.** Severity: minor
The plan (`docs/plans/2026-05-20-X11-global-external-reviewer-bridge.md:232-237`) shows the shim being written with the absolute `$SOURCE_SCRIPT` interpolated literally. The actual `skills/external-review/install.sh:28-38` adds a `$HOME/`-relative rewrite so the test assertion `"/home/simon/" not in text` (line 39 of the installer test) passes. The change is correct (the spec required no hardcoded `/home/simon/...`) but neither spec §1 nor plan Task 2 documents that the shim contains a literal `$HOME` token that bash re-expands at run time. Add one line to the spec/plan and to `skills/external-review/SKILL.md` so a future maintainer doesn't "simplify" the substitution back out and re-fail the installer test.

**F3 — Plan Task 5 Step 4 narrow sweep still hits the X11 handoff.** Severity: minor
`docs/handoffs/2026-05-20-X11-global-external-reviewer-bridge-prompt.md:31` contains `python3 scripts/external-reviewer.py` as anti-guidance ("Do not route new guidance through …"). The plan's broader sweep tolerates fixture / historical hits but the narrower pattern in Task 5 Step 4 (`python3 scripts/external-reviewer\.py|python3 [^ ]*external-reviewer\.py review`) also matches this anti-guidance line. The handoff doc is committed (commit `2ac8f2f`), so the slice is consistent, but a literal reading of the plan's "Expected for the narrower check: no live guidance hits" would flag this. Either tighten the regex to require an invocation context (e.g. `^[^>#-]*python3 scripts/external-reviewer\.py`) or amend the plan to whitelist anti-guidance in handoffs.

**F4 — Uncommitted `docs/tasklist.json` and untracked chain folder are expected, but the slice has not closed.** Severity: nit
`git status` shows `M docs/tasklist.json` (X11 → `in_progress`) and `?? docs/reviewer/x11-global-external-reviewer-bridge-X11-post-slice/`. These are the in-scope artifacts for the current closeout. They are not yet committed because Task 5 Step 7 explicitly bundles them with the closeout commit. Calling that out so the next reviewer round does not treat the dirty state as drift.

**F5 — Plan Task 0 Step 1 says "work from an implementation worktree" but does not name one.** Severity: nit
The current cwd `/home/simon/Dev/sigreer/skills/superstar/.worktrees/x11-global-external-reviewer-bridge` is correctly an X11 worktree, so the slice satisfies the intent. Plan wording could be tightened (`.worktrees/x11-global-external-reviewer-bridge`) so future executions don't have to infer it. Not blocking.

**F6 — No persisted evidence that Task 5 Steps 1–3 actually passed.** Severity: nit
The plan only states "Expected: PASS". Because tests were not committed alongside captured logs, this review cannot verify pytest / static-guard / installer-smoke results from disk; I can only confirm the inputs (installer, shim, SKILL edits, test files) are wired correctly. The post-slice review is itself the live chain-writing smoke (per plan Step 6), so this is acceptable for the gate, but consider adding an explicit `--emit json` log capture to the closeout commit message in future slices.

## Open questions / assumptions

- Assumption: pytest for `test_external_reviewer_installer.py` and `test_external_reviewer_compat_shim.py` was run from this worktree's root and passed. I could not execute them under plan-mode tool constraints. If F1 turns out to fail on the developer's machine, surface that before closing X11.
- Assumption: `tools/tasktool/tasktool validate` was run after the X11 → `in_progress` flip and produced a clean tree.

## Suggested document edits

- `docs/plans/2026-05-20-X11-global-external-reviewer-bridge.md` Task 2 Step 1: add a sentence explaining the `$HOME`-relative substitution and why the installer test depends on it.
- `docs/specs/2026-05-20-X11-global-external-reviewer-bridge-design.md` §1: replace "embeds the absolute path resolved at install time" with "embeds the absolute path resolved at install time, rewriting any `$HOME` prefix to a literal `$HOME` token so generated shims do not pin to a specific user's home directory."
- `skills/external-review/tests/test_external_reviewer_compat_shim.py:48-51`: scrub `PATH` instead of prepending, so the test cannot be poisoned by a real install.

## Verification gaps / commands that should be run

Run from this worktree before `tasktool close X11`:

```
python3 -m pytest skills/external-review/tests/test_external_reviewer_installer.py skills/external-review/tests/test_external_reviewer_compat_shim.py -q
bash tests/claude-code/test-external-reviewer-global-command.sh
bash tests/claude-code/test-autonomous-review-gates.sh
tools/tasktool/tasktool validate
tmp_bin="$(mktemp -d)"; EXTERNAL_REVIEWER_BIN="$tmp_bin" bash skills/external-review/install.sh && PATH="$tmp_bin:$PATH" external-reviewer --help >/dev/null
```

If F1 is fixed before close, also confirm `test_compat_shim_missing_global_command_exits_127` still passes on a developer machine that already has `~/.local/bin/external-reviewer` installed.

Overall verdict: ready with small edits


## Sweep 1

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

**S1.F1. Installer diverges from plan snippet (undocumented `$HOME` substitution). Severity: minor**

`skills/external-review/install.sh:28-37` substitutes the `$HOME` prefix in the generated shim's source path. The plan snippet (Task 2 Step 1) shows a literal `exec python3 "$SOURCE_SCRIPT" "$@"` with no substitution. The substitution is necessary to satisfy `test_installer_writes_source_tree_shim_to_configured_bin`'s assertion `"/home/simon/" not in text`, which the plan's literal code would have failed. The implementation choice is sound but the plan and resulting code disagree, which is the kind of silent drift the spec was written to prevent. Either:
- update the plan/spec to call out that the shim must use `$HOME/...` when the source lies under `$HOME` (and document why), or
- accept it as a Task 5 docs-cleanup edit.

**S1.F2. `--reviewer-provider` / `--caller-provider` not documented. Severity: minor**

Task 5 Step 6 invokes `external-reviewer review` with `--reviewer-provider claude --caller-provider codex`, but the main command block in `skills/external-review/SKILL.md:90-99` does not list these flags. Either prune them from the plan's invocation (they are not strictly necessary) or extend the documented command surface so future operators understand them.

**S1.F3. Compatibility-shim audit row doesn't define `Partial` vs `Compatibility-pass` resolution. Severity: minor**

`skills/project-setup/SKILL.md:37` (row 7b) says "Partial for any other local file. … Offer to replace it with `skills/project-setup/scripts/external-reviewer-shim.py`; do not copy the full bridge." The spec (lines 188-195) explicitly defines three states (`Pass`, `Compatibility-pass`, `Partial`); the audit row collapses Pass and Compatibility-pass into one prose line and only labels Partial. A reviewer/auditor reading the table cannot tell at a glance how to mark a confirming compatibility shim. Consider explicit triple-state phrasing.

**S1.F4. Uncommitted `docs/tasklist.json` and untracked chain folder. Severity: nit (expected)**

`git status` shows `M docs/tasklist.json` (`started`/`status` flipped to `in_progress`) and an untracked `docs/reviewer/x11-global-external-reviewer-bridge-X11-post-slice/`. Both are expected for Task 5 Step 6; they will be committed in Step 7. Flagging only so the closeout commit does not silently include unrelated changes.

**S1.F5. Fixture file matches a stale-pattern grep. Severity: nit**

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

