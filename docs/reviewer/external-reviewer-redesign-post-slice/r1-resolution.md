# Round 1 resolution

## F1 — skill entrypoint mismatch
- **Verdict:** fixed
- **What changed:** `skills/external-review/SKILL.md` updated at lines 8 and 43 to reference `skills/external-review/scripts/external-reviewer.py` (the canonical location) instead of the obsolete root-level `scripts/external-reviewer.py`. The root-level script was staged for deletion (it had already been removed from disk in commit `544bf51` when `project-setup` extracted the migration helper; the working-tree deletion was untracked until now). Audited remaining references: `skills/project-setup/SKILL.md` already pointed to the correct path; design spec and round-1 request/response files reference the path historically and were not modified.
- **Commit:** `57fd2cd`

## F2 — workspace cleanliness
- **Verdict:** fixed (within scope of staying on `main`)
- **What changed:**
  - `.gitignore` extended to cover `__pycache__/` and `*.pyc`.
  - Slice 1 chain artefacts under `docs/reviewer/external-reviewer-redesign-post-slice/` committed (round-1 request + response + this resolution doc).
  - Plan file updated with a "Slice 1 closeout note" enumerating the seven Slice 1 commits, the final test count (`19 passed`), the pre-flight override on `main`, and the new script location.
  - Unrelated dirty files (`CLAUDE.md`, four other SKILL.md edits) deliberately left in place — they predate Slice 1 and are outside scope, as called out in the closeout note.
- **Commit:** `c9b1ca3`

## F3 — head_sha capture timing
- **Verdict:** fixed
- **What changed:** In `skills/external-review/scripts/external-reviewer.py`, `current_head_sha(root)` and `is_dirty(root)` are now invoked *before* `run_reviewer` (immediately after the prompt file is written) and stored as `head_sha_at_request` / `worktree_dirty_at_request`. A second `current_head_sha(root)` call after the reviewer returns supplies `head_sha_after_round`. The manifest round entry now records distinct values when the reviewer mutates repo state. New test `skills/external-review/tests/test_head_sha_capture_timing.py` uses a stub reviewer that creates a commit mid-review and asserts the two fields differ and match the expected before/after SHAs. Full suite: `19 passed`.
- **Commit:** `57fd2cd`
