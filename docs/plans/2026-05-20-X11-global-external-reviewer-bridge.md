# Global External Reviewer Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `external-reviewer` the global canonical Superstar review-chain bridge command and remove full repo-local bridge vendoring from future workflows.

**Architecture:** Add a source-tree global shim installer for `external-reviewer`, matching `tasktool`'s update model. Preserve backwards compatibility through a tiny repo-local Python shim that delegates to the global command, then update live skill guidance and static tests so new sessions no longer recommend `python3 scripts/external-reviewer.py`.

**Tech Stack:** Bash installer, Python stdlib compatibility shim, pytest, shell static tests, Markdown skill docs.

---

## Preconditions

- Spec: `docs/specs/2026-05-20-X11-global-external-reviewer-bridge-design.md`
- Spec review chain: `docs/reviewer/x11-global-external-reviewer-bridge-design-spec`
- Task ID: `X11`
- First execution step:
  ```bash
  tools/tasktool/tasktool set X11 --status in_progress
  ```
  Expected: `X11` moves to `in_progress`.
- Worktree isolation: before editing, use `superstar:using-git-worktrees` and work from an implementation worktree unless Simon explicitly opts out in that session.

## File Map

- Create: `skills/external-review/install.sh`
  - Installs/updates the global `external-reviewer` shim.
  - Supports `EXTERNAL_REVIEWER_BIN=<dir>` for tests.
  - Self-locates the source script from the installer's own path.
- Create: `skills/project-setup/scripts/external-reviewer-shim.py`
  - Compatibility shim template for old `python3 scripts/external-reviewer.py ...` handoffs.
  - Contains no review parser/state logic.
- Create: `skills/external-review/tests/test_external_reviewer_installer.py`
  - Verifies install target override, generated shim contents, overwrite guard, and `--help` smoke.
- Create: `skills/external-review/tests/test_external_reviewer_compat_shim.py`
  - Verifies compatibility shim delegation, missing global command failure, and self-loop guard.
- Modify: `skills/external-review/SKILL.md`
  - Uses `external-reviewer` as the canonical bridge command.
- Modify: `skills/project-setup/SKILL.md`
  - Audits global `external-reviewer`; treats non-shim repo-local bridges as legacy drift.
- Modify: `skills/tasklist-discipline/SKILL.md`
  - Removes wording that setup vendors `scripts/external-reviewer.py`.
- No change expected: `tests/claude-code/test-autonomous-review-gates.sh`
  - Run it as an existing review-gate regression after wording changes.
- Create or modify: `tests/claude-code/test-external-reviewer-global-command.sh`
  - Static/live command contract check for skill wording and installer smoke.
- Modify: reusable handoff docs under `docs/handoffs/` only if they are current templates for future sessions.

## Task 1: Add Installer Contract Tests

**Files:**
- Create: `skills/external-review/tests/test_external_reviewer_installer.py`
- Create later in Task 2: `skills/external-review/install.sh`

- [ ] **Step 1: Write failing pytest coverage for the installer**

Create `skills/external-review/tests/test_external_reviewer_installer.py`:

```python
from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INSTALLER = ROOT / "skills" / "external-review" / "install.sh"


def run_installer(bin_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["EXTERNAL_REVIEWER_BIN"] = str(bin_dir)
    return subprocess.run(
        ["bash", str(INSTALLER), *args],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_installer_writes_source_tree_shim_to_configured_bin(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"

    result = run_installer(bin_dir)

    assert result.returncode == 0, result.stderr
    shim = bin_dir / "external-reviewer"
    assert shim.exists()
    assert os.access(shim, os.X_OK)

    text = shim.read_text(encoding="utf-8")
    assert "external-reviewer shim" in text
    assert "skills/external-review/scripts/external-reviewer.py" in text
    assert "/home/simon/" not in text
    assert "Pointing at" in result.stdout


def test_generated_external_reviewer_help_works_from_any_cwd(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    install = run_installer(bin_dir)
    assert install.returncode == 0, install.stderr

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    other_cwd = tmp_path / "other"
    other_cwd.mkdir()
    result = subprocess.run(
        ["external-reviewer", "--help"],
        cwd=other_cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "review" in result.stdout


def test_installer_refuses_to_overwrite_unknown_command(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    target = bin_dir / "external-reviewer"
    target.write_text("#!/usr/bin/env bash\necho unknown\n", encoding="utf-8")
    target.chmod(0o755)

    result = run_installer(bin_dir)

    assert result.returncode != 0
    assert "not an external-reviewer shim" in result.stderr
    assert "echo unknown" in target.read_text(encoding="utf-8")


def test_installer_force_overwrites_unknown_command(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    target = bin_dir / "external-reviewer"
    target.write_text("#!/usr/bin/env bash\necho unknown\n", encoding="utf-8")
    target.chmod(0o755)

    result = run_installer(bin_dir, "--force")

    assert result.returncode == 0, result.stderr
    assert "external-reviewer shim" in target.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run the installer tests and confirm they fail**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_external_reviewer_installer.py -q
```

Expected: FAIL because `skills/external-review/install.sh` does not exist.

## Task 2: Implement Global Installer

**Files:**
- Create: `skills/external-review/install.sh`
- Test: `skills/external-review/tests/test_external_reviewer_installer.py`

- [ ] **Step 1: Add the installer script**

Create `skills/external-review/install.sh`:

```bash
#!/usr/bin/env bash
# skills/external-review/install.sh - install/update the external-reviewer shim.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_SCRIPT="$SCRIPT_DIR/scripts/external-reviewer.py"
TARGET_DIR="${EXTERNAL_REVIEWER_BIN:-${HOME}/.local/bin}"
TARGET="$TARGET_DIR/external-reviewer"
FORCE="${1:-}"

if [[ ! -f "$SOURCE_SCRIPT" ]]; then
  echo "ERROR: source bridge not found: $SOURCE_SCRIPT" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"

if [[ -f "$TARGET" && "$FORCE" != "--force" ]]; then
  if grep -q "external-reviewer shim" "$TARGET" 2>/dev/null; then
    echo "external-reviewer shim already installed. Updating source path..."
  else
    echo "ERROR: $TARGET exists and is not an external-reviewer shim. Re-run with --force to overwrite." >&2
    exit 1
  fi
fi

cat > "$TARGET" <<EOF
#!/usr/bin/env bash
# external-reviewer shim - generated by Superstar skills/external-review/install.sh
exec python3 "$SOURCE_SCRIPT" "\$@"
EOF
chmod +x "$TARGET"

echo "Installed $TARGET"
echo "Pointing at $SOURCE_SCRIPT"
"$TARGET" --help >/dev/null
echo "Self-test passed."
```

- [ ] **Step 2: Run focused installer tests**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_external_reviewer_installer.py -q
```

Expected: PASS.

- [ ] **Step 3: Commit installer work**

Run:

```bash
git add skills/external-review/install.sh skills/external-review/tests/test_external_reviewer_installer.py
git commit -m "external-review: add global bridge installer"
```

Expected: commit succeeds.

## Task 3: Add Compatibility Shim Template and Tests

**Files:**
- Create: `skills/project-setup/scripts/external-reviewer-shim.py`
- Create: `skills/external-review/tests/test_external_reviewer_compat_shim.py`

- [ ] **Step 1: Write failing compatibility shim tests**

Create `skills/external-review/tests/test_external_reviewer_compat_shim.py`:

```python
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SHIM = ROOT / "skills" / "project-setup" / "scripts" / "external-reviewer-shim.py"


def run_shim(path: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATH"] = path
    return subprocess.run(
        [sys.executable, str(SHIM), *args],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_compat_shim_delegates_to_global_external_reviewer(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "external-reviewer"
    log = tmp_path / "args.txt"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        f"printf '%s\\n' \"$@\" > {log}\n"
        "echo delegated\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)

    result = run_shim(str(bin_dir), "review", "--kind", "spec")

    assert result.returncode == 0
    assert result.stdout.strip() == "delegated"
    assert log.read_text(encoding="utf-8").splitlines() == ["review", "--kind", "spec"]


def test_compat_shim_missing_global_command_exits_127(tmp_path: Path) -> None:
    bin_dir = tmp_path / "empty"
    bin_dir.mkdir()

    result = run_shim(str(bin_dir), "review")

    assert result.returncode == 127
    assert "`external-reviewer` is not on PATH" in result.stderr
    assert "skills/external-review/install.sh" in result.stderr


def test_compat_shim_refuses_self_resolution(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "external-reviewer"
    fake.symlink_to(SHIM)

    result = run_shim(str(bin_dir), "review")

    assert result.returncode == 127
    assert "resolved `external-reviewer` back to itself" in result.stderr
```

- [ ] **Step 2: Run compatibility tests and confirm they fail**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_external_reviewer_compat_shim.py -q
```

Expected: FAIL because `skills/project-setup/scripts/external-reviewer-shim.py` does not exist.

- [ ] **Step 3: Add the compatibility shim template**

Create `skills/project-setup/scripts/external-reviewer-shim.py`:

```python
#!/usr/bin/env python3
"""Compatibility shim for old Superstar handoffs.

The canonical bridge is the global `external-reviewer` command.
"""

from __future__ import annotations

import os
import shutil
import sys


def main() -> int:
    target = shutil.which("external-reviewer")
    if target is None:
        print(
            "scripts/external-reviewer.py is a compatibility shim, but "
            "`external-reviewer` is not on PATH. Install it with Superstar's "
            "skills/external-review/install.sh.",
            file=sys.stderr,
        )
        return 127

    script_path = os.path.realpath(__file__)
    target_path = os.path.realpath(target)
    if target_path == script_path:
        print(
            "scripts/external-reviewer.py resolved `external-reviewer` back to "
            "itself. Fix PATH so the global Superstar bridge appears before "
            "this repo-local compatibility shim.",
            file=sys.stderr,
        )
        return 127

    os.execvp(target, [target, *sys.argv[1:]])
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run compatibility tests**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_external_reviewer_compat_shim.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit compatibility shim**

Run:

```bash
git add skills/project-setup/scripts/external-reviewer-shim.py skills/external-review/tests/test_external_reviewer_compat_shim.py
git commit -m "project-setup: add external-reviewer compatibility shim"
```

Expected: commit succeeds.

## Task 4: Update Skill Guidance and Static Guards

**Files:**
- Modify: `skills/external-review/SKILL.md`
- Modify: `skills/project-setup/SKILL.md`
- Modify: `skills/tasklist-discipline/SKILL.md`
- Modify: `tests/claude-code/test-autonomous-review-gates.sh`
- Create: `tests/claude-code/test-external-reviewer-global-command.sh`

- [ ] **Step 1: Add failing static guard for global command guidance**

Create `tests/claude-code/test-external-reviewer-global-command.sh`:

```bash
#!/usr/bin/env bash
# Static regression test for global external-reviewer command guidance.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

fail() {
    echo "FAIL: $1" >&2
    exit 1
}

EXTERNAL_REVIEW="$ROOT/skills/external-review/SKILL.md"
PROJECT_SETUP="$ROOT/skills/project-setup/SKILL.md"
TASKLIST="$ROOT/skills/tasklist-discipline/SKILL.md"

grep -q "external-reviewer review" "$EXTERNAL_REVIEW" \
    || fail "external-review must document external-reviewer review"

grep -q "global canonical review-chain bridge command" "$EXTERNAL_REVIEW" \
    || fail "external-review must define external-reviewer as canonical"

if grep -q "python3 scripts/external-reviewer.py" "$EXTERNAL_REVIEW"; then
    fail "external-review still recommends repo-local bridge invocation"
fi

grep -q "external-reviewer --help" "$PROJECT_SETUP" \
    || fail "project-setup must audit global external-reviewer availability"

grep -q "legacy drift" "$PROJECT_SETUP" \
    || fail "project-setup must flag non-shim repo-local external-reviewer.py as legacy drift"

grep -q "external-reviewer-shim.py" "$PROJECT_SETUP" \
    || fail "project-setup must point at the compatibility shim template"

if grep -q "Copy from.*skills/external-review/scripts/external-reviewer.py" "$PROJECT_SETUP"; then
    fail "project-setup still says to copy the full bridge"
fi

if grep -q "vendors .scripts/external-reviewer.py" "$TASKLIST"; then
    fail "tasklist-discipline still says setup vendors the bridge"
fi

echo "PASS: global external-reviewer command guidance is present"
```

Run:

```bash
bash tests/claude-code/test-external-reviewer-global-command.sh
```

Expected: FAIL on current wording.

- [ ] **Step 2: Update `skills/external-review/SKILL.md` command model**

Edit the opening section so it says:

```markdown
An independent reviewer (not the coordinating agent) reviews a target document or completed slice/phase. The bridge is the global `external-reviewer` command — provider-neutral, configured via `AGENT_REVIEWER_CMD`. Each round writes a `request.md` and `response.md` pair under a per-document chain folder so the iteration history is durable and committable.

**Bridge command.** `external-reviewer` is the global canonical review-chain bridge command. It is installed by `skills/external-review/install.sh` and delegates to `skills/external-review/scripts/external-reviewer.py` in the active Superstar checkout. Do not run or copy a full repo-local `scripts/external-reviewer.py` bridge. Existing repos may keep a tiny compatibility shim at that path only so old handoffs continue to delegate to the global command.
```

Replace the main command block with:

```bash
external-reviewer review \
    --kind <spec|plan|post-slice|post-phase> \
    --file <path/to/target.md> \
    --work-id <P2.S3 | P2>   # required for post-slice / post-phase
    [--context <path>]... \
    [--review-depth thorough] \
    [--incremental-budget-chars 400000] \
    --emit json
```

Replace subcommand examples so they use:

```bash
external-reviewer manual-approve ...
external-reviewer ingest-response ...
external-reviewer show-limit
external-reviewer clear-limit
```

- [ ] **Step 3: Update `skills/project-setup/SKILL.md` audit table**

Replace the reviewer bridge row with these rows:

```markdown
| 7 | Global `external-reviewer` bridge available | `command -v external-reviewer` succeeds and `external-reviewer --help` exits 0. | Run or print `bash <active-superstar-checkout>/skills/external-review/install.sh` after confirmation. |
| 7b | Repo-local `scripts/external-reviewer.py` legacy drift | Pass if absent. Compatibility-pass if present and it contains `Compatibility shim for old Superstar handoffs` plus an `external-reviewer` delegation. Partial for any other local file. | Offer to replace it with `skills/project-setup/scripts/external-reviewer-shim.py`; do not copy the full bridge. |
```

Update the setup boundary classification list so it says:

```markdown
global `external-reviewer` shim installation, repo-local `scripts/external-reviewer.py` compatibility shim replacement
```

Update the integration sentence so it says:

```markdown
- `[[external-review]]` — provides the global bridge command contract and the `AGENT_REVIEWER_CMD` expectation.
```

- [ ] **Step 4: Update `skills/tasklist-discipline/SKILL.md` setup boundary wording**

Replace:

```markdown
vendors `scripts/external-reviewer.py`
```

with:

```markdown
installs the global `external-reviewer` shim or replaces a legacy repo-local reviewer bridge with the compatibility shim
```

- [ ] **Step 5: Wire static guard into existing test runner if needed**

If `tests/claude-code/run-skill-tests.sh` enumerates individual shell tests, add:

```bash
"$ROOT/tests/claude-code/test-external-reviewer-global-command.sh"
```

If it auto-discovers `test-*.sh`, no change is needed.

- [ ] **Step 6: Run static guidance tests**

Run:

```bash
bash tests/claude-code/test-external-reviewer-global-command.sh
bash tests/claude-code/test-autonomous-review-gates.sh
```

Expected: both PASS.

- [ ] **Step 7: Commit skill guidance**

Run:

```bash
git add skills/external-review/SKILL.md skills/project-setup/SKILL.md skills/tasklist-discipline/SKILL.md tests/claude-code/test-external-reviewer-global-command.sh tests/claude-code/test-autonomous-review-gates.sh
git commit -m "skills: prefer global external-reviewer bridge"
```

Expected: commit succeeds. If `tests/claude-code/test-autonomous-review-gates.sh` was unchanged, omit it from `git add`.

## Task 5: Full Verification and X11 Closeout Prep

**Files:**
- Modify: `docs/tasklist.json`
- Create: `docs/reviewer/x11-global-external-reviewer-bridge-X11-post-slice/` during post-slice review

- [ ] **Step 1: Run focused tests**

Run:

```bash
python3 -m pytest skills/external-review/tests/test_external_reviewer_installer.py -q
python3 -m pytest skills/external-review/tests/test_external_reviewer_compat_shim.py -q
bash tests/claude-code/test-external-reviewer-global-command.sh
```

Expected: all PASS.

- [ ] **Step 2: Run broader verification**

Run:

```bash
tools/tasktool/tasktool validate
python3 -m pytest skills/external-review/tests -q
python3 -m pytest tools/tasktool/tests -q
bash tests/claude-code/test-autonomous-review-gates.sh
```

Expected: all PASS.

- [ ] **Step 3: Run installer smoke without touching real `~/.local/bin`**

Run:

```bash
tmp_bin="$(mktemp -d)"
EXTERNAL_REVIEWER_BIN="$tmp_bin" bash skills/external-review/install.sh
PATH="$tmp_bin:$PATH" external-reviewer --help
```

Expected:

```text
Installed <tmp>/external-reviewer
Pointing at <repo>/skills/external-review/scripts/external-reviewer.py
Self-test passed.
```

`external-reviewer --help` exits 0 and prints the bridge help.

- [ ] **Step 4: Inspect remaining live references**

Run:

```bash
rg -n 'python3 scripts/external-reviewer\.py|scripts/external-reviewer\.py|external-reviewer\.py review' skills tests tools/tasktool/tests docs/handoffs
```

Expected: no live skill/test/handoff guidance recommends `python3 scripts/external-reviewer.py`. Fixture or historical-review occurrences are acceptable only when they are clearly committed as past reviewer content.

- [ ] **Step 5: Commit any final docs/test cleanup**

If Step 4 required cleanup, inspect the exact dirty paths:

```bash
git status --short
```

Expected: only files intentionally changed by X11 cleanup are dirty. Stage those exact files by name, then run:

```bash
git commit -m "docs: remove stale external-reviewer bridge guidance"
```

Expected: commit succeeds. If Step 4 found no cleanup work, skip this step.

- [ ] **Step 6: Run post-slice external review for X11**

After implementation is complete and all tests pass, run:

```bash
external-reviewer review \
  --kind post-slice \
  --file docs/plans/2026-05-20-X11-global-external-reviewer-bridge.md \
  --work-id X11 \
  --context docs/specs/2026-05-20-X11-global-external-reviewer-bridge-design.md \
  --context docs/tasklist.json \
  --review-depth thorough \
  --reviewer-provider claude \
  --caller-provider codex \
  --emit json
```

Expected: `merged_verdict` is `ready` or `ready with small edits`.

- [ ] **Step 7: Close X11**

Run:

```bash
tools/tasktool/tasktool close X11 --reviewer-chain docs/reviewer/x11-global-external-reviewer-bridge-X11-post-slice
tools/tasktool/tasktool validate
git add docs/tasklist.json docs/reviewer/x11-global-external-reviewer-bridge-X11-post-slice
git commit -m "X11: close global external-reviewer bridge"
```

Expected: X11 closes only after the post-slice reviewer chain is parser-valid and ready.
