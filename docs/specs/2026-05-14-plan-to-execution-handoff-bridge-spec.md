# Spec — Plan-to-execution handoff bridge

**Status:** draft / parked — captured for later. Not sent for external review.
**Date:** 2026-05-14
**Owner:** Simon

## Problem

At the end of `superstar:writing-plans`, the skill currently offers two
execution paths in the *current* Claude Code session:

1. Subagent-Driven (recommended) — coordinator in this session.
2. Inline Execution — `executing-plans` in this session.

Both options keep work in the current session. That is wrong for option 1:
a subagent-driven coordinator is context-heavy (plan, spec, reviewer chains,
per-task orchestration) and shouldn't start its life on top of an already-warm
planning context. In practice the user always answers "new session" manually:
`/clear`, then paste the handoff prompt from
`docs/handoffs/<plan-stem>-prompt.md`.

The desired experience is **one keystroke** to clear context and start the new
session with the handoff prompt pre-loaded.

## Goals

- Collapse the post-plan offer to two options that match real usage:
  - **(1) New session, subagent-driven** (default / recommended)
  - **(2) Current session, inline**
- Provide a bridging shell script that, given the handoff prompt as input
  (env var preferred), terminates the current Claude Code session and
  launches a new one with the handoff prompt as its initial user message —
  in the same terminal, no manual paste.
- Keep the existing `docs/handoffs/<plan-stem>-prompt.md` artifact (it is
  the source of truth for the prompt and survives the session swap).

## Non-goals

- Multi-terminal orchestration. Single-terminal handoff only.
- Cross-platform support beyond Linux + zsh (the user's environment).
- Tying to a specific terminal emulator (Ghostty, etc.). The bridge should
  work in whatever terminal `claude` is currently running in.
- Auto-modifying the user's shell rc files. If a shell hook is required,
  it must be a one-time manual paste shown to the user, not silently
  installed.

## User flow (target)

1. `writing-plans` completes; spec + plan reviewed; handoff prompt written
   to `docs/handoffs/<plan-stem>-prompt.md`.
2. Skill prints the two-option offer.
3. User picks option 1.
4. Skill prints a single shell command, e.g.
   `!HANDOFF_PROMPT_FILE=docs/handoffs/<plan-stem>-prompt.md superstar-handoff`.
5. User invokes it (one keystroke + Enter via the `!` shell-out).
6. Current Claude Code session terminates; same terminal immediately
   re-launches `claude` with the handoff prompt as its initial user message;
   coordinator session begins with no manual `/clear` and no paste.

## Constraints / facts that shape the design

- Claude Code's `Bash` tool runs commands as a **child** of the claude
  process. A child cannot cleanly "replace" its parent. Naïve `exec claude`
  from inside the bash tool ends up parented to init or detached from the
  TTY.
- `claude` CLI accepts an initial prompt argument:
  `claude "$(cat handoff.md)"`. This is the launch primitive.
- Env vars set inside claude's bash tool do **not** persist to the parent
  shell after claude exits. So "set env var, then run command after exit"
  only works if the var is exported in the outer shell **before** claude
  was launched, or if the bridge writes state to disk.
- The user runs zsh on Linux.

## Candidate mechanisms (discussed)

### (a) Kill-parent-and-exec from within the bash tool

Script walks up `$PPID` to find the claude PID, `kill -TERM` it, then
`exec claude "$(cat $HANDOFF_PROMPT_FILE)"`.

- Pro: single `!` invocation, no shell rc changes.
- Con: when the parent claude dies, the script (its child) may lose the
  controlling TTY or be reparented to init before `exec claude` re-attaches.
  Fragile. Possibly recoverable with `setsid` + explicit `/dev/tty`
  reattachment, but brittle.

### (b) Script + zshrc hook (recommended candidate at time of parking)

- Script `scripts/superstar-handoff` (or installed to `~/.local/bin`):
  - reads `HANDOFF_PROMPT_FILE` from env;
  - copies its contents to `~/.cache/superstar/pending-handoff.md`
    (atomic write);
  - walks `$PPID` chain to find the parent claude PID and sends `SIGTERM`.
- One-time zshrc snippet (shown once, user pastes):
  ```zsh
  superstar_resume_handoff() {
    local f=~/.cache/superstar/pending-handoff.md
    [[ -f $f ]] || return
    local tmp=$(mktemp)
    mv "$f" "$tmp"
    claude "$(cat "$tmp")"
    rm -f "$tmp"
  }
  precmd_functions+=(superstar_resume_handoff)
  ```
- Flow: user runs the `!` command → script writes marker, kills claude →
  shell prompt returns → `precmd` hook fires → new claude starts with the
  handoff prompt → marker is consumed (single-shot).

Pros: reliable; no TTY hacks; idempotent (marker is consumed once).
Cons: requires one-time rc edit.

### (c) New-terminal launcher

Script spawns a fresh terminal window (e.g. Ghostty) running
`claude "$(cat …)"`, then signals the parent claude to exit. Drifts
toward multi-window, which the user has rejected for this flow.

### (d) Script + two-step (no zshrc)

Script reads env var and execs `claude` with the prompt. User must first
`/exit` the current session, then run the script (or it's invoked via a
shell alias). No process-tree hacks, but the experience is two keystrokes
instead of one.

## Open questions

- Mechanism choice: (b) gives the cleanest UX at the cost of a one-time
  rc edit. (a) attempts true one-shot in-place handoff with `setsid` +
  TTY reattachment — worth a spike to see if it can be made robust.
- Installation: vendored at `scripts/superstar-handoff` and the user adds
  it to `PATH`, vs. published to `~/.local/bin` by an installer step.
- Should the bridge be generic to *any* prompt file (not just plan
  handoffs)? If so, it lives outside `writing-plans` and other skills can
  use it too (e.g. external-review hand-offs, slice closeouts).
- Handling failure: if `claude` exits abnormally after relaunch, should
  the marker be re-applied or discarded? Current sketch discards (atomic
  move before launch).

## Touch points if/when picked up

- `skills/writing-plans/SKILL.md` — replace the Step C offer block with
  the two-option version and a single launcher command line.
- `scripts/superstar-handoff` (new) — the bridge script.
- `docs/SETUP.md` or equivalent — the one-time zshrc snippet, if (b) is
  chosen.
- `superstar:project-setup` — could optionally offer to print the
  zshrc snippet during init.

## Decision parked

Mechanism not selected. Spec captures intent and the three viable designs.
Pick this up when ready to implement; no external review until then.
