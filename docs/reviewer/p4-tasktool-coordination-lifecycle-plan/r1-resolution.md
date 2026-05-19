# Round 1 Resolution

Resolved reviewer findings from `r1-2026-05-19T2201-response.md`.

- F1: Added an executable dirty-state rule to the plan: authoritative-mode writes refuse unstaged `docs/tasklist.json` changes before loading project data, while staged-only canonical tasktool state remains usable. Added tests for the detector and refusal path.
- F2: Added a routed mutation matrix covering command families beyond `set` and `close`, including `create`, `note`, `ref`, `title`, `block`, `unblock`, `deps`, `ratify`, `planning-path`, `validate --normalise`, `import`, and `archive-phase`. Clarified that `archive-phase` writes archive artifacts in the authoritative checkout.
- F3: Added a P4.S2 self-start step after `tasktool start` exists and before ready-close enforcement lands.
- F4: Updated the planned git test repo helper to configure local `user.email` and `user.name` before commits.
