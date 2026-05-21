# Resolution for r1

## F1
Status: deferred
Evidence:
- See F2; root cause is the historical-row rewrite. Fixed F2 resolves the dirty authoritative state. The `tasktool close P5.S1` step is intentionally deferred until r2 returns ready.

Notes:
F1 is circular at request time — the post-slice chain did not yet exist, and close happens after a passing verdict. The dirty-authoritative portion of F1 is driven entirely by F2.

## F2
Status: fixed
Evidence:
- Commit: 48ead69
- Files: `tools/tasktool/serialize.py`, `tools/tasktool/tests/test_serialize.py`, `tools/tasktool/tests/test_start_worktree.py`, `docs/tasklist.json`
- Verification: `cd tools && python -m pytest tasktool/tests -q` (462 passed); `git diff main -- docs/tasklist.json` returns empty — every spurious worktree_* default added by commit 46c94ed to historical rows has been removed via serializer round-trip.

Notes:
to_dict now omits worktree_* keys whose values equal dataclass defaults (None for the path/branch/pruned_at trio, False for the in_place/prune_pending booleans). Historical rows in docs/tasklist.json reverted by round-tripping through the corrected serializer (load_project → save_project). Two pre-existing tests in test_start_worktree.py that asserted `sl["worktree_path"] is None` were updated to use `.get()` to reflect the new default-omission behaviour. New test_serialize.py tests assert default rows emit no worktree_* keys and non-default values (e.g. worktree_in_place=True) still round-trip.

## F3
Status: fixed
Evidence:
- Commit: 48ead69
- Files: `tools/tasktool/commands.py`, `tools/tasktool/tests/test_worktree_subcommands.py`
- Verification: `./tools/tasktool/tasktool worktree list` and `./tools/tasktool/tasktool worktree status P5.S1` both exit 0 from inside the linked worktree; new test `test_worktree_list_and_status_are_readonly_under_dirty_authoritative` asserts both commands succeed when the authoritative tasklist is dirty (a precondition that fails under `_write_context`).

Notes:
Added `_read_context` alongside `_write_context` in `tools/tasktool/commands.py`. It resolves the authoritative checkout and validates the branch but acquires no lock and does not call `_ensure_authoritative_tasklist_clean`. `cmd_worktree_list` and `cmd_worktree_status` switched from `_write_context` to `_read_context`.
