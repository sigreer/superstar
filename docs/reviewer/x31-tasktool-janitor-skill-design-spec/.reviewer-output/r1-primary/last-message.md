I have enough grounding. Producing the review.

---

Findings

F1 — `close` on cross-cutting rows passes through the landed gate; the spec presents `tasktool close XNN` as an unconditional command. Severity: important
In `commands.py:1319-1327`, `cmd_close` runs `_apply_landed_gate(...)` for both `slice` and `cross` kinds. So a `close` recommendation against an `X` row that has a recorded worktree branch not yet landed on base will be *refused* unless `--allow-unlanded --reason "..."` is passed. The spec's section 5 shows the bare form `tasktool close XNN` (lines 132-139) and only covers the failure procedurally ("Stop and report if tasktool refuses a mutation", line 144). That fallback prevents the worst outcome, but the skill will be materially stronger if it anticipates this: note that `close` on a cross row applies a landed gate, and defer the exact override flags (`--allow-unlanded`/`--reason`) to `tasklist-discipline` rather than discovering them at mutation time. (For context: review gate does NOT apply to cross rows — `commands.py:1309-1310` — so the only gate the janitor will hit on X rows is the landed gate.)

F2 — `close`/`cancel` auto-commit the tracker; this collides with the "preserve unrelated dirty/staged work" instruction when `docs/tasklist.json` itself is already dirty/staged. Severity: important
`cmd_close` performs a scoped git commit of the tracker (and any archive file) unless `--no-commit` is passed (`commands.py:1342-1351`); `cmd_cancel` behaves analogously. The spec is aware that "tasktool writes may touch shared tracker files" (line 63) and says "Preserve unrelated dirty/staged work" (line 143), but the wording is too vague to protect against the concrete hazard: if `docs/tasklist.json` is *itself* already staged/dirty with unrelated edits, the scoped auto-commit will fold those edits into the `close`/`cancel` commit. This is precisely the co-staged-tracker failure mode this fork has hit before. Recommend the skill state explicitly: before any mutation, check whether `docs/tasklist.json` is itself dirty/staged; if so, resolve or stash it first, and note that `tasktool close --no-commit` exists for when the tracker must stay staged. Section 1's generic "extra care before mutation" should be made this specific.

F3 — The "generic across stale tracker entries" framing slightly over-promises versus `cancel`'s actual surface. Severity: minor
`cmd_cancel` rejects tasks outright (`commands.py:1380-1383`: "cancel does not apply to tasks; cancel the parent slice instead") and `--cascade` is phase-only. The dossier enum (lines 103, 112-118) offers `cancel` for "every audited row," and the frontmatter/triggers advertise "stale tracker entries" broadly (line 46), not just `X*` rows. The spec's center of gravity is correctly cross-cutting `X` rows, where `cancel`/`close` work cleanly — but the generic framing implies a janitor could `cancel` an arbitrary stale row, which fails for tasks and behaves differently for slices/phases. Either narrow the advertised scope to cross-cutting/phase/slice rows, or add a one-line caveat that non-cross kinds have additional `tasktool` semantics owned by `tasklist-discipline`.

F4 — Delegation threshold has a gap between "small coherent set" and "20+ rows." Severity: minor
Section 2 gives three signals: "more than a small coherent set" (line 67), "bounded batch of 4-6 rows" (line 69), and "must not review 20+ heterogeneous rows alone" (line 73). The 7-19 range and the meaning of "small" are undefined, so two agents could reasonably disagree on whether to delegate 10 rows. Tighten to a single operational rule (e.g., "delegate when the candidate set exceeds N rows OR spans more than one theme") so the guardrail is testable and not judgment-soup.

F5 — `promote` has no operational follow-through defined. Severity: minor
The dossier requires `Proposed command: <exact tasktool command, or "none">` (line 106) and `promote` necessarily maps to "none." Non-Goal line 31 correctly forbids inline implementation, but the spec never says what a `promote` outcome *produces* — a `tasktool note`/`ref` recording the decision, a handoff line, or just a chat recommendation. Without this, `promote` rows risk being audited and then dropped on the floor. Add one sentence on what the coordinator does with `promote` rows (record in the audit artifact and/or hand to the normal spec/plan loop), consistent with section 6.

F6 — Test strategy under-specifies the frontmatter assertion, risking a brittle or vacuous test. Severity: nit
The test strategy says assert "the expected frontmatter trigger" (line 187) but doesn't name the exact substring to pin. The existing pattern in `test_skill_tasktool_lifecycle_docs.py` pins precise strings (e.g. `assert "tasktool close <x-id>" in text`, line 24). Name the exact substrings the new tests should pin (e.g. `name: tasktool-janitor` and a stable phrase from the description like `cleaning up open tasktool rows`) so the implementer doesn't invent ambiguous assertions.

F7 — Canonical-source/test-location coupling is correct; flagging as a verification note, not a defect. Severity: nit
The test helper `skill_text(name)` reads `ROOT/skills/<name>/SKILL.md` where `ROOT = parents[3]` (the repo root) — `test_skill_tasktool_lifecycle_docs.py:6-10`. This matches the spec's claim that canonical source is top-level `skills/` (line 5) and that the plugin mirror is generated (line 39). So the new `SKILL.md` MUST land at `skills/tasktool-janitor/SKILL.md` (not the mirror) for the tests to find it — which the spec already states (line 37). No change needed; just confirming the coupling holds.

Open questions / assumptions
- Assumption: most `X*` rows targeted for cleanup have no recorded worktree branch, so the F1 landed gate is usually a no-op. If the multistore validation set includes X rows with recorded unlanded branches, F1 becomes load-bearing rather than edge-case. Worth confirming during the optional dry run (line 198).
- Open question: when the janitor's mutation batch *also* archives a cross row (`cmd_close` archives cross rows by default unless `--no-archive`, `commands.py:1337-1338`), should the audit artifact record the archive path? Section 6's "final state after mutation" (line 154) probably covers it, but archiving is a side effect worth naming explicitly.

Suggested document edits
1. Section 5 (Mutation Discipline): add a bullet — "`tasktool close XNN` on a cross row passes a landed-branch gate; if the row has a recorded unlanded worktree branch the close is refused. Do not improvise flags — consult `tasklist-discipline` for the sanctioned override and `--reason`." (addresses F1)
2. Section 1 and Section 5: replace the vague "extra care before mutation" with a concrete pre-mutation check — "Before any `close`/`cancel`, confirm `docs/tasklist.json` is not itself dirty or staged with unrelated edits; `tasktool close`/`cancel` auto-commit the tracker (scoped), and a pre-dirtied tracker will be folded into the commit. Resolve or stash it first; `tasktool close --no-commit` exists if the tracker must remain staged." (addresses F2)
3. Section "Skill Name and Placement" / Goals: add a caveat that `cancel` is for cross/phase/slice rows and does not apply to tasks; defer non-cross lifecycle nuances to `tasklist-discipline`. (addresses F3)
4. Section 2: collapse the delegation signals into one rule with explicit thresholds. (addresses F4)
5. Dossier / Section 4: add one sentence on what a `promote` outcome produces. (addresses F5)
6. Test Strategy: name the exact frontmatter substrings the tests pin. (addresses F6)

Verification gaps / commands to run
- During implementation, run the new string-level tests via the repo's existing harness (the same module already runs): `python -m pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`.
- Optional dry run (per spec line 198) in `/home/simon/Dev/sigreer/multistore`: `tasktool list --open` then produce dossiers for `X*` rows with zero mutating commands; specifically check whether any candidate X row has a recorded worktree branch (relevant to F1) before trusting bare `tasktool close`.

The spec is well-grounded: every CLI command it relies on exists (`list --open` `cli.py:329`, `show` `:307`, `close` `:161`, `cancel --reason` `:185-187`, `set`/`note`/`ref`, `validate` `:334`), the cited test file and its `skill_text` pattern are real, all referenced docs dirs (`specs`, `plans`, `handoffs`, `reviewer`, `archived-tasks`) and composing skills (`tasklist-discipline`, `dispatching-parallel-agents`) exist, and the read-only-then-approve-then-mutate spine is sound. The findings are refinements, not structural problems — the two `important` ones are about anticipating real `tasktool` gate/commit behavior so the skill doesn't send agents into avoidable refusals or tracker-commit accidents.

Overall verdict: ready with small edits