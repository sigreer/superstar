# `using-git-worktrees` Skill Audit & Token-Cost Analysis

**Date:** 2026-05-21
**Scope:** Skill content at `skills/using-git-worktrees/SKILL.md`, and the multistore project's worktree setup (`~/Dev/sigreer/multistore`).
**Question being answered:** Why does Claude Code usage telemetry attribute ~33% of session tokens to this skill, and is it operating against a project that's actually set up the way the skill assumes?

---

## 1. Skill content audit — `skills/using-git-worktrees/SKILL.md`

226 lines / ~10 KB. Not enormous on its own, but it gets loaded much more often than you'd think — see §3. Specific waste inside the file:

- **Heavy redundancy.** The "implementation work requires isolation, no opt-out, never in main" rule is stated four times: Overview ("Implementation rule"), Step 0, the Quick Reference table, and the Red Flags / Always block. Each repeat is ~50–100 tokens.
- **Quick Reference table (15 rows) + Common Mistakes + Red Flags Always/Never** overlap by ~70%. Three encodings of the same conditional logic.
- **Step numbering jumps 0 → 1 → 3 → 4** (no Step 2). Minor, but it makes Claude pause to reconcile the structure.
- **Submodule guard** (lines 30–35) costs lines in every load even though almost no project hits this branch. Could live in `references/` and load only on conflict.
- **Step 1a / native-tool branch** (`EnterWorktree`, `WorktreeCreate`, `/worktree`). In Claude Code, `EnterWorktree` is a *deferred* tool — its schema is not loaded by default. Practically every Claude session ends up at Step 1b after spending tokens reasoning about Step 1a, then sometimes running `ToolSearch` to check, then deciding to fall back. Pure overhead.
- **Tasktool paragraph (line 16)** belongs in `tasklist-discipline`, not here. It mixes two concerns and forces a second mental model on every load.
- **Two parallel directory-selection pipelines** — explicit user preference vs filesystem detection vs global legacy vs default. Four-way decision tree, with a verification step that often re-runs `git check-ignore` even when the dir is plainly tracked already.

---

## 2. Multistore reality vs the skill

This is where I think most of your token bleed actually comes from.

```text
$ cd ~/Dev/sigreer/multistore
$ git worktree list
/home/simon/Dev/sigreer/multistore  7b886bfc [main]   ← only main, no live worktrees
$ ls .worktrees .claude/worktrees
.worktrees:        (empty)
.claude/worktrees: (empty)
$ grep -i worktree .gitignore
.worktrees/
.claude/worktrees/
.codex/worktrees/
```

Observations:

- **Three ignored candidate dirs**, only two known to the skill. The skill's filesystem priority sees `.worktrees/` and uses it; `.claude/worktrees/` and `.codex/worktrees/` are dead drops the skill never references. So every session that starts in Claude Code rederives "OK, `.worktrees/` wins" rather than seeing a documented choice.
- **No active worktrees**, despite `git reflog` showing dozens of past `worktree-p13-*` / `worktree-x38-*` merges. Each new slice starts from zero — full detection + creation cycle, every time.
- **No project-level worktree convention.** `multistore/CLAUDE.md` is ~17 KB but contains zero text about worktree placement or naming. The historical pattern from reflog is clearly `worktree-<task-id>-<slug>` but it's nowhere documented, so the agent re-invents a name each time it creates one (and may pick a different scheme depending on the session).
- **Tasktool config is correct** (`authoritative-checkout`, branch `main`). That part works.

So yes: the skill *describes* a setup that the multistore project only partially implements. The agent ends up filling the gaps with reasoning, every session.

---

## 3. Why this skill shows up as 33% of session tokens

A few amplifiers that compound:

1. **Subagent re-loading.** `subagent-driven-development` fans out N subagents per slice. Each subagent receives the full `using-superstar` bootstrap + likely loads `using-git-worktrees` itself (the skill list is in every system reminder). 4 subagents = 5× skill text. Claude Code's usage telemetry rolls subagent tokens up to the parent session, which is exactly why this skill looks oversized — it isn't loaded 33% more, it's loaded 5–10× more.
2. **Subagents that are already inside the worktree still run Step 0.** A subagent dispatched into `.worktrees/x16-shim/...` re-runs `git rev-parse --git-dir`, reasons through the four-branch decision tree, and concludes "already isolated, skip to Step 3" — burning ~400–600 output tokens to reach a conclusion the parent already knew. Multiplied across all subagents per slice, that's the bulk of the cost.
3. **TodoWrite-per-checklist.** The `using-superstar` flow says: if a skill has a checklist, create a Todo per item. Subagents dutifully create 4–5 worktree-related todos that are no-ops in their context.
4. **Step 1a tool-search loop.** Claude sees `EnterWorktree` in the deferred tool list, may run `ToolSearch` to check whether to use it, decides no, falls back to Step 1b. Repeated per session.
5. **Codex asymmetry.** Codex's bootstrap is leaner and doesn't reload the full skill metadata each turn. So even when Codex is in first-person doing the same work, the per-turn overhead is smaller — exactly the 2× gap you're seeing.

**The skill isn't pathologically large; it's pathologically re-entered.**

---

## 4. Recommended fixes (ordered by impact)

### A. Add a subagent early-exit at the top of the skill — biggest win

`using-superstar` already has a `<SUBAGENT-STOP>` for dispatched subagents. Add the analogous block at the top of `using-git-worktrees`:

```text
<SUBAGENT-STOP>
If you were dispatched as a subagent and your cwd is already inside a linked worktree
(`git rev-parse --git-dir` differs from `--git-common-dir`), skip this skill entirely.
Your parent has done Step 0–4. Do NOT re-run detection, baseline tests, or TodoWrite.
</SUBAGENT-STOP>
```

This alone probably cuts the skill's effective cost by half in implementation slices, because subagents are the dominant multiplier.

### B. Add a multistore-level worktree convention doc

A 15-line `docs/instructions-and-workflows/worktrees.md` (and a one-line pointer in `CLAUDE.md`) that says:

```text
- Location: .worktrees/ (canonical). Ignore-only; never commit.
- Branch + dirname: worktree-<task-id>-<slug>, e.g. worktree-p15-s2-checkout-rewrite
- Authority: tasktool routes mutations through main checkout via .tasktool/config.json
- Cleanup: after merge, `git worktree remove .worktrees/<name>`
```

Pre-decides everything the skill currently asks the agent to derive.

### C. Drop or consolidate the two unused ignored dirs

Remove `.claude/worktrees/` and `.codex/worktrees/` from `.gitignore` (and delete the empty dirs) unless you actively want per-harness isolation — in which case document it. Right now they're confusing noise that the skill doesn't reference.

### D. Shrink the skill body to ~80 lines

Concrete cuts:

- Delete the Quick Reference table (it duplicates Red Flags).
- Fold Common Mistakes into Red Flags (one Never/Always block).
- Move the submodule guard to `references/submodules.md`, link only.
- Move the tasktool paragraph to `tasklist-discipline`.
- Compress Step 1a to one sentence: *"If your harness has a native worktree tool (e.g. `EnterWorktree`), use it; otherwise:"*

Estimated: 226 → ~90 lines. ~60% reduction in per-load cost.

### E. Reorder so Step 0's most common outcome is first

"Already isolated → skip" should be the first sentence after the headline, not after three paragraphs of preamble. Most loads hit this branch.

---

## 5. What was *not* changed by this audit

No files have been edited. This is analysis only.

Recommended landing order if you want me to ship the changes:

1. **(A)** — single-file edit to `skills/using-git-worktrees/SKILL.md`, highest leverage.
2. **(D)** — same file, content trim. Bundle with (A) into one slice.
3. **(B)** + **(C)** — a follow-up slice scoped to the multistore repo, not this one.

(E) is a stylistic improvement that can ride along with (D).

---

## 6. Post-discussion update — tasktool as worktree-lifecycle owner

The §4 recommendations above frame worktrees as a *skill* concern (with a per-project doc in (B)). Subsequent discussion rejected that framing. The corrected direction:

**Worktree lifecycle is a tasktool concern, not a skill or per-project concern.** All Superstar projects follow the same strict methodology; the convention should be enforced by the only command that creates the resource, not by prose the agent re-interprets each session. (B) and (C) from §4 are therefore deprecated as written.

### Why tasktool is the right owner

- Tasktool already knows everything required to derive a worktree: slice ID, slug, parent branch, authority config. The current skill asks the agent to re-derive these from context every session.
- Worktree state and slice state are already coupled in reality — every worktree exists *because* of a slice. They drift today (audit found `.worktrees/` empty in multistore despite reflog showing dozens of past `worktree-p13-*` merges). Coupling them in tasktool means closure cleans up automatically and stale worktrees cannot accumulate.
- The skill body collapses to roughly 30 lines: *"Run `tasktool start <slice-id>`. It handles isolation. If you are already in a linked worktree, you are done."* Massive token win on top of (A).

### Proposed tasktool surface

- `tasktool start <id>` — default creates `.worktrees/worktree-<id>-<slug>` on a branch of the same name, sets slice → `in_progress`, records `worktree_path` in tasklist state, prints the `cd` line.
- `tasktool start <id> --in-place` — explicit opt-out (planning/spec slices that do not touch code).
- `tasktool start <id> --adopt <path>` — for harnesses that created the worktree themselves (e.g. `EnterWorktree`); tasktool just tracks the path.
- `tasktool start --ad-hoc <slug>` — throwaway IDs for hotfixes / exploration outside a tracked slice (keeps all paths routed through tasktool).
- `tasktool close <id>` — guards: branch merged into authority, no uncommitted/stashed changes, no untracked files. Then prunes the worktree. `--keep-worktree` opts out of the prune; `--force` overrides guards.
- `tasktool worktree list / prune / adopt` — explicit management.
- Installer / migration ensures `.gitignore` covers `.worktrees/`, warns on legacy `.claude/worktrees/` and `.codex/worktrees/`, deprecates the global `~/.config/superstar/worktrees/<project>` path with a one-version warning.

### Design points to settle during spec

1. **Subagents must not call `tasktool start`.** Parent creates; subagents inherit cwd. `tasklist-discipline` needs to spell this out, otherwise races and duplicate worktrees.
2. **Destructive close needs guards** (above). A surprise `git worktree remove` that nukes uncommitted work would be a real foot-gun.
3. **Native-tool interop.** Tasktool should detect when it is already inside a harness-managed worktree and switch to `--adopt` mode automatically, not fight it.
4. **Schema migration.** `tasklist.json` gains an optional `worktree_path` field per slice. Existing entries default to null; tasktool backfills on next `start`.
5. **Canonical path is `.worktrees/<branch-name>`** at repo root. Single location for all Superstar projects.
6. **Branch + dirname convention** is `worktree-<task-id>-<slug>` (matches historical reflog naming in multistore).

### Revised landing order (replaces §5)

- **Slice 1:** tasktool gains worktree-aware `start` / `close` + `worktree list/prune/adopt` + schema migration. Installer ensures `.gitignore` covers `.worktrees/`.
- **Slice 2:** rewrite `using-git-worktrees` skill as a thin pointer to the tasktool commands. Subagent early-exit (A) stays. Quick Reference / Common Mistakes / Red Flags collapse to one short block.
- (A), (D), (E) from §4 fold into Slice 2. (B) and (C) are replaced by the installer behaviour in Slice 1.

This is the current state of thinking and the starting point for the P5 phase outline.
