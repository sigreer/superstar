# Resolution for r2

## F1
Status: fixed
Evidence:
- Files: `docs/plans/2026-06-06-X29-timeline-generator.md:1793`, `docs/plans/2026-06-06-X29-timeline-generator.md:1948` (both shims now `parents[1]  # tools/`); new subprocess test `test_direct_script_invocation` in Task 11's `test_cli.py` runs `python3 tools/timeline/timeline.py --repo <fixture> -o <out>` from the repo root and asserts exit 0 + rendered content.
- Verification: `grep -n "parents\[" docs/plans/2026-06-06-X29-timeline-generator.md` shows only `parents[1]` in the two shims (plus test-internal path derivation).

Notes:
Root cause of the r1→r2 miss: the r1 fix script's shim anchors contained the pre-edit import text, which an earlier global replace in the same script had already rewritten, so the shim replacement silently never matched. The r2 fix asserts on occurrence counts.
