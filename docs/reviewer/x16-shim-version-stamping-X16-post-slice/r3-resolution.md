# Resolution for r3

## S1.F4
Status: fixed
Evidence:
- Commit: 8bfbc225e5df5d5a50ca8b567172db1e75259c2f
- Files: pyproject.toml (new)
- Verification: `python3 -m pytest scripts/tests/ tools/tasktool/tests/ skills/external-review/tests/ -v` (exit 0, 666 tests collected and passing)
- Standalone runs verified: `python3 -m pytest scripts/tests/` passes (25 tests). `bash scripts/deploy.sh --check` and `bash scripts/bump-version.sh --check` remain clean at v6.5.0.

Notes:
Took Option A: added a minimal `pyproject.toml` configuring pytest's `--import-mode=importlib` (plus `testpaths`). This bypasses the `tests` top-level package collision caused by the three empty `__init__.py` markers without deleting them, so each test file is imported by path rather than under a shared `tests.` namespace. No test code changes were needed.
