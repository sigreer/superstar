---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - ensures an isolated workspace exists via native tools or git worktree fallback
---

<SUBAGENT-STOP>
You were dispatched as a subagent. The parent coordinator has already created or adopted the worktree for the active slice and `cd`d you into it. Do not read or apply the rest of this skill, and do not call `tasktool start`. If `git rev-parse --git-dir` differs from `git rev-parse --git-common-dir` (and you are not inside a submodule — see `references/submodules.md` if uncertain), you are inside the parent's linked worktree; proceed with your task. If they match, you are in a plain checkout; ask the parent before editing files.
</SUBAGENT-STOP>

# Using Git Worktrees

**Announce at start:** "I'm using the using-git-worktrees skill to enter the slice worktree."

**Rule:** Implementation slice/task work runs in an isolated linked worktree owned by tasktool. A plain `main`/`master` checkout is planning/read-only by default unless the human partner opts out of isolation in the current turn.

**Run:** `tasktool start <slice-id>` from the authoritative checkout (or from an already-linked worktree of the same repo — tasktool will auto-adopt). It creates the worktree at `.worktrees/worktree-<id>-<slug>`, records the path and branch on the slice row, and prints the `cd` line. Idempotent: a consistent recorded path is a no-op. See `[[tasklist-discipline]]` for the lifecycle commands and the routing rules.

**Dependencies:** A fresh linked worktree has **no installed dependencies** — `node_modules/`, `.venv/`, `vendor/`, `target/` are per-checkout and never inherited from the main checkout. **Run the project's install command (e.g. `bun install`) inside the new worktree before running any test or verification gate.** Skipping this makes dependency resolution fall through to the main checkout and surfaces spurious failures — missing workspace-package symlinks, named-export link errors (`Export named 'X' not found in module …`), etc. — that look like real defects but vanish once dependencies are installed. `tasktool start` prints a stderr reminder on fresh creation; treat any such gate failure in a just-created worktree as missing-deps until you have confirmed `node_modules/` (or the equivalent) exists.

**Opt-out:** For planning, spec, or design slices that touch no code, run `tasktool start <slice-id> --in-place`. The slice row records `worktree_in_place: true`; later `close` and `worktree prune` treat the slice as having no worktree.

**Drift:** If `tasktool start` reports a conflict (path missing, branch mismatched, plain-dir collision), run the exact `tasktool worktree {adopt,repair,prune --force}` command it prints. Do not improvise with raw `git worktree` invocations; do not delete `.worktrees/` directories by hand.

For submodule-vs-worktree disambiguation, see `references/submodules.md`.
