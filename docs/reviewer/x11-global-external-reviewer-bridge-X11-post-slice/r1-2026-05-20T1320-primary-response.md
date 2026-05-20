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
