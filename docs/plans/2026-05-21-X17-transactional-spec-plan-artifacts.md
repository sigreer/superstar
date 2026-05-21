# Transactional Spec and Plan Artifact Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superstar:subagent-driven-development (recommended) or superstar:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add tasktool-owned artifact registration, status, prepare, and commit commands so spec/plan/handoff/reviewer artifacts cannot be left as loose workflow state on the authoritative checkout.

**Architecture:** Add a focused `tools/tasktool/artifacts.py` module for workflow artifact path classification, row reference mapping, status reports, and commit-path calculations. Wire it through `commands.py` and `cli.py` using existing authoritative `_write_context`, `_find_item`, `_save`, and git staging helpers. Update the workflow skills so spec/plan agents use the new tasktool transaction path before and after external review.

**Tech Stack:** Python 3.11, argparse, dataclasses/model helpers already in `tools/tasktool`, pytest, git CLI helpers used by existing tasktool tests.

**Spec:** `docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md`

**Tasktool row:** X17 (cross-cutting). The row currently exists with refs to the spec and spec-review chain. Implementation must start with `tools/tasktool/tasktool start X17` from the authoritative checkout or the implementation worktree; routed tasktool state remains authoritative on `main`.

---

## File Structure

Files to create:
- `tools/tasktool/artifacts.py` — pure artifact policy: kind/path validation, invocation/write-root path resolution, row reference updates, status problem discovery, JSON/text report rendering helpers, and commit path allowlist helpers.
- `tools/tasktool/tests/test_artifacts.py` — unit tests for artifact policy helpers without invoking the CLI.
- `tools/tasktool/tests/test_artifact_cli.py` — CLI tests for `artifact add`, `artifact status`, `artifact commit`, and `prepare`.

Files to modify:
- `tools/tasktool/cli.py` — add `artifact` subcommands and `prepare` parser.
- `tools/tasktool/commands.py` — add command functions that call `artifacts.py` and reuse authoritative routing/staging.
- `tools/tasktool/tests/test_worktree_authority.py` — add routed-worktree coverage for artifact writes and invocation-only artifact refusal.
- `skills/brainstorming/SKILL.md` — register/stage/commit spec artifacts transactionally.
- `skills/writing-plans/SKILL.md` — register/stage/commit plan and handoff artifacts transactionally.
- `skills/tasklist-discipline/SKILL.md` — document workflow artifacts and preferred commands.
- `skills/external-review/SKILL.md` — register reviewer chains after successful spec/plan review.

---

## Task 1: Add artifact policy helpers

**Files:**
- Create: `tools/tasktool/artifacts.py`
- Create: `tools/tasktool/tests/test_artifacts.py`

- [ ] **Step 1: Write tests for path kind validation**

Create `tools/tasktool/tests/test_artifacts.py` with:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from tasktool.artifacts import ArtifactError, ArtifactKind, normalize_artifact_path


def test_spec_path_must_live_under_docs_specs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "docs" / "specs").mkdir(parents=True)
    path = repo / "docs" / "specs" / "2026-05-21-X17-example-design.md"
    path.write_text("# spec\n", encoding="utf-8")

    result = normalize_artifact_path(
        invocation_root=repo,
        write_root=repo,
        raw_path=Path("docs/specs/2026-05-21-X17-example-design.md"),
        kind=ArtifactKind.SPEC,
        allow_missing=False,
    )

    assert result.relative_path == "docs/specs/2026-05-21-X17-example-design.md"
    assert result.write_path == path


def test_plan_path_rejects_docs_specs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "docs" / "specs").mkdir(parents=True)
    path = repo / "docs" / "specs" / "wrong.md"
    path.write_text("# wrong\n", encoding="utf-8")

    with pytest.raises(ArtifactError, match="plan artifacts must live under docs/plans/"):
        normalize_artifact_path(
            invocation_root=repo,
            write_root=repo,
            raw_path=Path("docs/specs/wrong.md"),
            kind=ArtifactKind.PLAN,
            allow_missing=False,
        )


def test_path_outside_invocation_repo_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("x\n", encoding="utf-8")

    with pytest.raises(ArtifactError, match="artifact path is outside repository"):
        normalize_artifact_path(
            invocation_root=repo,
            write_root=repo,
            raw_path=outside,
            kind=ArtifactKind.SPEC,
            allow_missing=False,
        )


def test_missing_path_allowed_for_future_artifact(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    result = normalize_artifact_path(
        invocation_root=repo,
        write_root=repo,
        raw_path=Path("docs/specs/future.md"),
        kind=ArtifactKind.SPEC,
        allow_missing=True,
    )

    assert result.relative_path == "docs/specs/future.md"


def test_invocation_only_artifact_is_rejected_for_routed_write(tmp_path: Path) -> None:
    invocation = tmp_path / "worker"
    write_root = tmp_path / "main"
    invocation.mkdir()
    write_root.mkdir()
    (invocation / "docs" / "specs").mkdir(parents=True)
    (write_root / "docs" / "specs").mkdir(parents=True)
    (invocation / "docs" / "specs" / "only-worker.md").write_text("# spec\n", encoding="utf-8")

    with pytest.raises(ArtifactError, match="artifact exists in invocation checkout but not authoritative checkout"):
        normalize_artifact_path(
            invocation_root=invocation,
            write_root=write_root,
            raw_path=Path("docs/specs/only-worker.md"),
            kind=ArtifactKind.SPEC,
            allow_missing=False,
        )
```

- [ ] **Step 2: Run the tests and confirm they fail**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_artifacts.py -q
```

Expected: import failure because `tasktool.artifacts` does not exist yet.

- [ ] **Step 3: Implement artifact kinds and path normalization**

Create `tools/tasktool/artifacts.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ArtifactError(RuntimeError):
    pass


class ArtifactKind(str, Enum):
    SPEC = "spec"
    PLAN = "plan"
    HANDOFF = "handoff"
    REVIEWER = "reviewer"
    ARCHIVE = "archive"


KIND_PREFIXES = {
    ArtifactKind.SPEC: "docs/specs/",
    ArtifactKind.PLAN: "docs/plans/",
    ArtifactKind.HANDOFF: "docs/handoffs/",
    ArtifactKind.REVIEWER: "docs/reviewer/",
    ArtifactKind.ARCHIVE: "docs/archived-tasks/",
}


@dataclass(frozen=True)
class NormalizedArtifact:
    kind: ArtifactKind
    relative_path: str
    invocation_path: Path
    write_path: Path
    exists_in_write_root: bool


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _relative_to_invocation(invocation_root: Path, raw_path: Path) -> tuple[str, Path]:
    candidate = raw_path.expanduser()
    if not candidate.is_absolute():
        candidate = invocation_root / candidate
    candidate = candidate.resolve()
    if not _inside(invocation_root, candidate):
        raise ArtifactError(f"artifact path is outside repository: {raw_path}")
    return candidate.relative_to(invocation_root.resolve()).as_posix(), candidate


def normalize_artifact_path(
    *,
    invocation_root: Path,
    write_root: Path,
    raw_path: Path,
    kind: ArtifactKind,
    allow_missing: bool,
) -> NormalizedArtifact:
    relative, invocation_path = _relative_to_invocation(invocation_root, raw_path)
    prefix = KIND_PREFIXES[kind]
    if not relative.startswith(prefix):
        raise ArtifactError(f"{kind.value} artifacts must live under {prefix}")
    if allow_missing and kind not in {ArtifactKind.SPEC, ArtifactKind.PLAN, ArtifactKind.HANDOFF}:
        raise ArtifactError("--allow-missing is only valid for spec, plan, and handoff artifacts")
    write_path = (write_root / relative).resolve()
    exists_in_write = write_path.exists()
    if not allow_missing and not exists_in_write:
        if invocation_path.exists() and invocation_root.resolve() != write_root.resolve():
            raise ArtifactError(
                "artifact exists in invocation checkout but not authoritative checkout; "
                "create or copy it to the authoritative checkout before registering"
            )
        raise ArtifactError(f"artifact path does not exist: {relative}")
    return NormalizedArtifact(
        kind=kind,
        relative_path=relative,
        invocation_path=invocation_path,
        write_path=write_path,
        exists_in_write_root=exists_in_write,
    )
```

- [ ] **Step 4: Run artifact helper tests**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_artifacts.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tools/tasktool/artifacts.py tools/tasktool/tests/test_artifacts.py
git commit -m "X17: add tasktool artifact path helpers"
```

---

## Task 2: Implement `tasktool artifact add`

**Files:**
- Modify: `tools/tasktool/artifacts.py`
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/cli.py`
- Create/modify: `tools/tasktool/tests/test_artifact_cli.py`

- [ ] **Step 1: Add CLI tests for registering artifacts**

Create `tools/tasktool/tests/test_artifact_cli.py` with the shared runner pattern from `test_cli_integration.py`:

```python
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=check)


def _tasktool(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2]) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run([sys.executable, str(TOOL), *args], cwd=cwd, text=True, capture_output=True, env=env)


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _git(root, "config", "user.email", "tasktool-tests@example.invalid")
    _git(root, "config", "user.name", "Tasktool Tests")
    (root / "README.md").write_text("x\n", encoding="utf-8")
    _git(root, "add", "README.md")
    _git(root, "commit", "-m", "init")
    (root / "docs").mkdir()
    assert _tasktool(root, "config", "init-authority", "--branch", "main").returncode == 0
    assert _tasktool(root, "init", "--project", "demo").returncode == 0
    assert _tasktool(root, "create", "cross", "--title", "Artifact work").returncode == 0
    _git(root, "add", ".")
    _git(root, "commit", "-m", "tasklist")
    return root


def test_artifact_add_registers_and_stages_spec(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    spec = root / "docs" / "specs" / "2026-05-21-X1-artifact-design.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("# spec\n", encoding="utf-8")

    r = _tasktool(root, "artifact", "add", "X1", "--kind", "spec", "--path", str(spec.relative_to(root)))

    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads((root / "docs/tasklist.json").read_text(encoding="utf-8"))
    assert "docs/specs/2026-05-21-X1-artifact-design.md" in data["cross_cutting"][0]["refs"]
    status = _git(root, "status", "--porcelain").stdout
    assert "A  docs/specs/2026-05-21-X1-artifact-design.md" in status
    assert "M  docs/tasklist.json" in status


def test_artifact_add_allow_missing_registers_future_spec(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    r = _tasktool(
        root,
        "artifact",
        "add",
        "X1",
        "--kind",
        "spec",
        "--path",
        "docs/specs/future.md",
        "--allow-missing",
    )

    assert r.returncode == 0, r.stdout + r.stderr
    status = _git(root, "status", "--porcelain").stdout
    assert "M  docs/tasklist.json" in status
    assert "future.md" not in status


def test_artifact_add_rejects_wrong_kind_directory(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    path = root / "docs" / "specs" / "wrong.md"
    path.parent.mkdir(parents=True)
    path.write_text("# wrong\n", encoding="utf-8")

    r = _tasktool(root, "artifact", "add", "X1", "--kind", "plan", "--path", "docs/specs/wrong.md")

    assert r.returncode == 1
    assert "plan artifacts must live under docs/plans/" in r.stderr


def test_artifact_add_rejects_allow_missing_for_reviewer(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    r = _tasktool(
        root,
        "artifact",
        "add",
        "X1",
        "--kind",
        "reviewer",
        "--path",
        "docs/reviewer/future-chain",
        "--allow-missing",
    )

    assert r.returncode == 1
    assert "--allow-missing is only valid for spec, plan, and handoff artifacts" in r.stderr
```

- [ ] **Step 2: Run tests and confirm parser failure**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_artifact_cli.py -q
```

Expected: failures because `artifact` is not a recognized command.

- [ ] **Step 3: Add row reference helper**

Extend `tools/tasktool/artifacts.py`:

```python
def add_artifact_to_item(item, artifact: NormalizedArtifact) -> bool:
    refs = getattr(item, "refs", None)
    if refs is None:
        raise ArtifactError("this item kind does not have refs")
    added = False
    if artifact.relative_path not in refs:
        refs.append(artifact.relative_path)
        added = True
    if artifact.kind == ArtifactKind.SPEC and hasattr(item, "spec_path"):
        item.spec_path = artifact.relative_path
    elif artifact.kind == ArtifactKind.PLAN and hasattr(item, "plan_path"):
        item.plan_path = artifact.relative_path
    elif artifact.kind == ArtifactKind.REVIEWER:
        if hasattr(item, "reviewer_chain"):
            item.reviewer_chain = artifact.relative_path
        elif hasattr(item, "phase_reviewer_chain"):
            item.phase_reviewer_chain = artifact.relative_path
    return added
```

- [ ] **Step 4: Add command implementation**

In `tools/tasktool/commands.py`, import `ArtifactError`, `ArtifactKind`, `add_artifact_to_item`, and `normalize_artifact_path`. Add:

```python
def _git_stage_rel(repo_root: Path, rel: str) -> None:
    if not STAGE_AFTER_WRITE:
        return
    try:
        _subprocess.run(
            ["git", "add", "--", rel],
            cwd=repo_root,
            check=False,
            stdout=_subprocess.DEVNULL,
            stderr=_subprocess.DEVNULL,
        )
    except OSError:
        pass


def cmd_artifact_add(
    *,
    repo_root: Path,
    id: str,
    kind: str,
    path: Path,
    allow_missing: bool = False,
) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        try:
            artifact = normalize_artifact_path(
                invocation_root=repo_root,
                write_root=write_root,
                raw_path=path,
                kind=ArtifactKind(kind),
                allow_missing=allow_missing,
            )
            added = add_artifact_to_item(item, artifact)
        except ArtifactError as exc:
            raise CommandError(str(exc)) from exc
        _save(write_root, p)
        if artifact.exists_in_write_root:
            _git_stage_rel(write_root, artifact.relative_path)
        state = "added" if added else "already present"
        print(f"{qid}: {state} {artifact.relative_path}")
```

- [ ] **Step 5: Add CLI parser and dispatch**

In `tools/tasktool/cli.py`, add:

```python
p_artifact = sub.add_parser("artifact")
artifact_sub = p_artifact.add_subparsers(dest="artifact_cmd", required=True)
p_artifact_add = artifact_sub.add_parser("add")
p_artifact_add.add_argument("id")
p_artifact_add.add_argument("--kind", required=True, choices=["spec", "plan", "handoff", "reviewer", "archive"])
p_artifact_add.add_argument("--path", required=True, type=Path)
p_artifact_add.add_argument("--allow-missing", action="store_true")
```

Dispatch:

```python
elif args.cmd == "artifact":
    if args.artifact_cmd == "add":
        commands.cmd_artifact_add(
            repo_root=root,
            id=args.id,
            kind=args.kind,
            path=args.path,
            allow_missing=args.allow_missing,
        )
```

- [ ] **Step 6: Run focused tests**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_artifacts.py tools/tasktool/tests/test_artifact_cli.py -q
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add tools/tasktool/artifacts.py tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/tests/test_artifact_cli.py
git commit -m "X17: add tasktool artifact registration command"
```

---

## Task 3: Add artifact status and prepare

**Files:**
- Modify: `tools/tasktool/artifacts.py`
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/cli.py`
- Modify: `tools/tasktool/tests/test_artifacts.py`
- Modify: `tools/tasktool/tests/test_artifact_cli.py`

- [ ] **Step 1: Add failing tests for status**

Append to `test_artifact_cli.py`:

```python
def test_artifact_status_reports_unreferenced_dated_spec(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    spec = root / "docs" / "specs" / "2026-05-21-X99-orphan-design.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("# orphan\n", encoding="utf-8")

    r = _tasktool(root, "artifact", "status", "--strict")

    assert r.returncode == 1
    assert "unreferenced workflow artifact" in r.stdout
    assert "docs/specs/2026-05-21-X99-orphan-design.md" in r.stdout


def test_artifact_status_reports_missing_referenced_file(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert _tasktool(root, "artifact", "add", "X1", "--kind", "spec", "--path", "docs/specs/missing.md", "--allow-missing").returncode == 0

    r = _tasktool(root, "artifact", "status", "X1", "--strict")

    assert r.returncode == 1
    assert "missing-referenced-artifact" in r.stdout


def test_artifact_status_reports_unstaged_referenced_file(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert _tasktool(root, "artifact", "add", "X1", "--kind", "spec", "--path", "docs/specs/future.md", "--allow-missing").returncode == 0
    _git(root, "add", "docs/tasklist.json")
    _git(root, "commit", "-m", "register future")
    spec = root / "docs" / "specs" / "future.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("# future\n", encoding="utf-8")

    r = _tasktool(root, "artifact", "status", "X1", "--strict")

    assert r.returncode == 1
    assert "referenced-artifact-unstaged" in r.stdout


def test_artifact_status_accepts_staged_referenced_file(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert _tasktool(root, "artifact", "add", "X1", "--kind", "spec", "--path", "docs/specs/future.md", "--allow-missing").returncode == 0
    _git(root, "add", "docs/tasklist.json")
    _git(root, "commit", "-m", "register future")
    spec = root / "docs" / "specs" / "future.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("# future\n", encoding="utf-8")
    _git(root, "add", "docs/specs/future.md")

    r = _tasktool(root, "artifact", "status", "X1", "--strict")

    assert r.returncode == 0, r.stdout + r.stderr


def test_artifact_status_reports_unreferenced_reviewer_directory(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    chain = root / "docs" / "reviewer" / "x1-plan"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[]}\n', encoding="utf-8")

    r = _tasktool(root, "artifact", "status", "--strict")

    assert r.returncode == 1
    assert "unreferenced-workflow-artifact" in r.stdout
    assert "docs/reviewer/x1-plan" in r.stdout


def test_artifact_status_accepts_registered_reviewer_directory_children(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    chain = root / "docs" / "reviewer" / "x1-artifact-plan"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[]}\n', encoding="utf-8")
    assert _tasktool(root, "artifact", "add", "X1", "--kind", "reviewer", "--path", "docs/reviewer/x1-artifact-plan").returncode == 0
    _git(root, "add", ".")
    _git(root, "commit", "-m", "register reviewer chain")

    r = _tasktool(root, "artifact", "status", "--strict")

    assert r.returncode == 0, r.stdout + r.stderr


def test_artifact_status_reports_dirty_child_of_registered_reviewer_directory(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    chain = root / "docs" / "reviewer" / "x1-artifact-plan"
    chain.mkdir(parents=True)
    assert _tasktool(root, "artifact", "add", "X1", "--kind", "reviewer", "--path", "docs/reviewer/x1-artifact-plan").returncode == 0
    _git(root, "add", ".")
    _git(root, "commit", "-m", "register reviewer chain")
    (chain / "chain.json").write_text('{"rounds":[]}\n', encoding="utf-8")

    r = _tasktool(root, "artifact", "status", "X1", "--strict")

    assert r.returncode == 1
    assert "referenced-artifact-unstaged" in r.stdout
    assert "docs/reviewer/x1-artifact-plan" in r.stdout


def test_artifact_status_reports_unstaged_tasklist_with_workflow_artifact(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    spec = root / "docs" / "specs" / "2026-05-21-X99-orphan-design.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("# orphan\n", encoding="utf-8")
    data = json.loads((root / "docs/tasklist.json").read_text(encoding="utf-8"))
    data["cross_cutting"][0]["notes"] = "manual edit"
    (root / "docs/tasklist.json").write_text(json.dumps(data), encoding="utf-8")

    r = _tasktool(root, "artifact", "status", "--strict")

    assert r.returncode == 1
    assert "unstaged-tasklist-with-workflow-artifacts" in r.stdout
```

- [ ] **Step 2: Add failing tests for prepare**

Append:

```python
def test_prepare_cross_allocates_and_registers_future_spec(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    r = _tasktool(
        root,
        "prepare",
        "cross",
        "--title",
        "Prepared artifact work",
        "--spec",
        "docs/specs/2026-05-21-X2-prepared-design.md",
    )

    assert r.returncode == 0, r.stdout + r.stderr
    assert "X2" in r.stdout
    data = json.loads((root / "docs/tasklist.json").read_text(encoding="utf-8"))
    assert data["cross_cutting"][1]["id"] == "X2"
    assert "docs/specs/2026-05-21-X2-prepared-design.md" in data["cross_cutting"][1]["refs"]


def test_prepare_existing_registers_plan_without_allocating(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    r = _tasktool(
        root,
        "prepare",
        "existing",
        "X1",
        "--plan",
        "docs/plans/2026-05-21-X1-plan.md",
    )

    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads((root / "docs/tasklist.json").read_text(encoding="utf-8"))
    assert len(data["cross_cutting"]) == 1
    assert "docs/plans/2026-05-21-X1-plan.md" in data["cross_cutting"][0]["refs"]
```

- [ ] **Step 3: Implement status problem model**

In `artifacts.py`, add:

```python
import json
import subprocess
from dataclasses import asdict
from typing import Iterable

WORKFLOW_DIRS = {
    "docs/specs": ArtifactKind.SPEC,
    "docs/plans": ArtifactKind.PLAN,
    "docs/handoffs": ArtifactKind.HANDOFF,
    "docs/reviewer": ArtifactKind.REVIEWER,
    "docs/archived-tasks": ArtifactKind.ARCHIVE,
}


@dataclass(frozen=True)
class ArtifactProblem:
    severity: str
    code: str
    id: str | None
    path: str
    message: str


@dataclass(frozen=True)
class GitPathStatus:
    index: str
    worktree: str

    @property
    def is_untracked(self) -> bool:
        return self.index == "?" and self.worktree == "?"

    @property
    def has_unstaged_worktree_change(self) -> bool:
        return self.worktree not in {" ", "?"}

    @property
    def has_staged_change(self) -> bool:
        return self.index not in {" ", "?"}


def referenced_paths_for_item(item) -> set[str]:
    paths = set(getattr(item, "refs", []) or [])
    for attr in ("spec_path", "plan_path", "planning_path", "reviewer_chain", "phase_reviewer_chain"):
        value = getattr(item, attr, None)
        if value:
            paths.add(value)
    return paths


def git_status_map(repo_root: Path) -> dict[str, GitPathStatus]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    statuses: dict[str, GitPathStatus] = {}
    for line in result.stdout.splitlines():
        if len(line) >= 4:
            statuses[line[3:]] = GitPathStatus(index=line[0], worktree=line[1])
    return statuses


def referenced_artifact_is_unstaged(status: GitPathStatus | None) -> bool:
    if status is None:
        return False
    if status.is_untracked:
        return True
    return status.has_unstaged_worktree_change


def referenced_path_is_unstaged(rel: str, status_map: dict[str, GitPathStatus]) -> bool:
    direct = status_map.get(rel)
    if referenced_artifact_is_unstaged(direct):
        return True
    prefix = rel.rstrip("/") + "/"
    for status_path, status in status_map.items():
        if status_path.startswith(prefix) and referenced_artifact_is_unstaged(status):
            return True
    return False


def render_status_text(problems: Iterable[ArtifactProblem]) -> str:
    rows = list(problems)
    if not rows:
        return "artifact status: ok\n"
    return "".join(f"{p.severity} {p.code} {p.path}: {p.message}\n" for p in rows)


def render_status_json(problems: Iterable[ArtifactProblem]) -> str:
    rows = list(problems)
    return json.dumps({"ok": not rows, "problems": [asdict(p) for p in rows]}, indent=2, sort_keys=True) + "\n"
```

- [ ] **Step 4: Implement artifact scanning and status command**

In `artifacts.py`, add a helper that enumerates workflow artifact files and first-class reviewer-chain directories:

```python
def _workflow_files(root: Path) -> set[str]:
    found: set[str] = set()
    for base in ("docs/specs", "docs/plans", "docs/handoffs", "docs/reviewer", "docs/archived-tasks"):
        path = root / base
        if path.exists():
            if base == "docs/reviewer":
                for child in path.iterdir():
                    if child.is_dir():
                        found.add(child.relative_to(root).as_posix())
                continue
            for child in path.rglob("*"):
                if child.is_file():
                    found.add(child.relative_to(root).as_posix())
    return found
```

Then add `cmd_artifact_status`:

```python
def cmd_artifact_status(*, repo_root: Path, id: str | None, strict: bool, format: str) -> int:
    p = _load(repo_root)
    status_map = git_status_map(repo_root)
    referenced: set[str] = set()
    problems: list[ArtifactProblem] = []
    scoped: list[tuple[str, object]]
    if id:
        qid, _container, item = _find_item(p, id)
        scoped = [(qid, item)]
    else:
        scoped = [(qid, item) for qid, _kind, _title, item in _iter_project_rows(p) if qid != "<project>"]
    for qid, item in scoped:
        for rel in referenced_paths_for_item(item):
            referenced.add(rel)
            if not (repo_root / rel).exists():
                problems.append(ArtifactProblem("error", "missing-referenced-artifact", qid, rel, "referenced artifact path does not exist"))
            elif referenced_path_is_unstaged(rel, status_map):
                problems.append(
                    ArtifactProblem(
                        "error",
                        "referenced-artifact-unstaged",
                        qid,
                        rel,
                        f"referenced artifact exists but is not staged; run tasktool artifact add {qid} --kind <kind> --path {rel} or tasktool artifact commit {qid} --message ...",
                    )
                )
    has_workflow_artifacts = any((repo_root / rel).exists() for rel in _workflow_files(repo_root))
    tasklist_status = status_map.get("docs/tasklist.json")
    if has_workflow_artifacts and tasklist_status and tasklist_status.has_unstaged_worktree_change:
        problems.append(
            ArtifactProblem(
                "error",
                "unstaged-tasklist-with-workflow-artifacts",
                None,
                "docs/tasklist.json",
                "docs/tasklist.json has unstaged changes while workflow artifacts are present",
            )
        )
    if id is None:
        for rel in sorted(_workflow_files(repo_root) - referenced):
            if rel.endswith(".md") or rel.startswith("docs/reviewer/"):
                problems.append(ArtifactProblem("warning", "unreferenced-workflow-artifact", None, rel, "unreferenced workflow artifact"))
    out = render_status_json(problems) if format == "json" else render_status_text(problems)
    sys.stdout.write(out)
    return 1 if strict and problems else 0
```

Dispatch must return this code from `cli.main`.

- [ ] **Step 5: Implement prepare**

In `commands.py`, add:

```python
def _artifact_specs_from_args(spec: str | None, plan: str | None, handoff: str | None) -> list[tuple[str, Path]]:
    pairs: list[tuple[str, Path]] = []
    if spec:
        pairs.append(("spec", Path(spec)))
    if plan:
        pairs.append(("plan", Path(plan)))
    if handoff:
        pairs.append(("handoff", Path(handoff)))
    return pairs


def cmd_prepare(
    *,
    repo_root: Path,
    mode: str,
    id: str | None = None,
    phase_id: str | None = None,
    title: str | None = None,
    spec: str | None = None,
    plan: str | None = None,
    handoff: str | None = None,
) -> None:
    if mode == "existing":
        if id is None:
            raise CommandError("prepare existing requires an id")
        target_id = id
    elif mode == "cross":
        if not title:
            raise CommandError("prepare cross requires --title")
        target_id = cmd_create_cross(repo_root=repo_root, title=title)
    elif mode == "phase":
        if not title:
            raise CommandError("prepare phase requires --title")
        target_id = cmd_create_phase(repo_root=repo_root, title=title)
    elif mode == "slice":
        if not title or not phase_id:
            raise CommandError("prepare slice requires <phase-id> and --title")
        target_id = f"{phase_id}.{cmd_create_slice(repo_root=repo_root, phase_id=phase_id, title=title)}"
    else:
        raise CommandError(f"unknown prepare mode: {mode}")
    for kind, artifact_path in _artifact_specs_from_args(spec, plan, handoff):
        cmd_artifact_add(repo_root=repo_root, id=target_id, kind=kind, path=artifact_path, allow_missing=True)
    print(target_id)
```

Note: this composes command functions and will acquire the tasktool lock multiple times. That is acceptable for X17; a future optimization can batch under one lock if needed.

- [ ] **Step 6: Wire CLI parser**

Add `artifact status` and `prepare` parsers in `cli.py` exactly matching the spec grammar.

- [ ] **Step 7: Run focused tests**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_artifacts.py tools/tasktool/tests/test_artifact_cli.py -q
```

Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add tools/tasktool/artifacts.py tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/tests/test_artifact_cli.py
git commit -m "X17: add artifact status and prepare commands"
```

---

## Task 4: Add artifact commit and routed worktree coverage

**Files:**
- Modify: `tools/tasktool/artifacts.py`
- Modify: `tools/tasktool/commands.py`
- Modify: `tools/tasktool/cli.py`
- Modify: `tools/tasktool/tests/test_artifact_cli.py`
- Modify: `tools/tasktool/tests/test_worktree_authority.py`

- [ ] **Step 1: Add commit tests**

Append to `test_artifact_cli.py`:

```python
def test_artifact_commit_stages_referenced_existing_artifact_and_commits(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert _tasktool(root, "artifact", "add", "X1", "--kind", "spec", "--path", "docs/specs/future.md", "--allow-missing").returncode == 0
    spec = root / "docs" / "specs" / "future.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("# future\n", encoding="utf-8")

    r = _tasktool(root, "artifact", "commit", "X1", "--message", "X1: add future spec")

    assert r.returncode == 0, r.stdout + r.stderr
    assert _git(root, "status", "--porcelain").stdout == ""
    assert "X1: add future spec" in _git(root, "log", "--oneline", "-1").stdout


def test_artifact_commit_refuses_unrelated_staged_code(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    code = root / "code.py"
    code.write_text("print('x')\n", encoding="utf-8")
    _git(root, "add", "code.py")

    r = _tasktool(root, "artifact", "commit", "X1", "--message", "X1: artifacts")

    assert r.returncode == 1
    assert "unrelated staged paths" in r.stderr
    assert "code.py" in r.stderr


def test_artifact_commit_refuses_same_slug_orphan(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    spec = root / "docs" / "specs" / "2026-05-21-X1-artifact-design.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("# spec\n", encoding="utf-8")
    orphan = root / "docs" / "plans" / "2026-05-21-X1-artifact.md"
    orphan.parent.mkdir(parents=True)
    orphan.write_text("# orphan plan\n", encoding="utf-8")
    assert _tasktool(root, "artifact", "add", "X1", "--kind", "spec", "--path", "docs/specs/2026-05-21-X1-artifact-design.md").returncode == 0

    r = _tasktool(root, "artifact", "commit", "X1", "--message", "X1: add artifact spec")

    assert r.returncode == 1
    assert "unreferenced same-slug workflow artifacts" in r.stderr
    assert "docs/plans/2026-05-21-X1-artifact.md" in r.stderr


def test_artifact_commit_refuses_same_slug_reviewer_chain_orphan(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    spec = root / "docs" / "specs" / "2026-05-21-X1-artifact-design.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("# spec\n", encoding="utf-8")
    chain = root / "docs" / "reviewer" / "x1-artifact-plan"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[]}\n', encoding="utf-8")
    assert _tasktool(root, "artifact", "add", "X1", "--kind", "spec", "--path", "docs/specs/2026-05-21-X1-artifact-design.md").returncode == 0

    r = _tasktool(root, "artifact", "commit", "X1", "--message", "X1: add artifact spec")

    assert r.returncode == 1
    assert "unreferenced same-slug workflow artifacts" in r.stderr
    assert "docs/reviewer/x1-artifact-plan" in r.stderr
```

- [ ] **Step 2: Add routed worktree tests**

Append to `test_worktree_authority.py`:

```python
def test_worker_artifact_add_updates_authority_not_worker(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    r = _tasktool(root, "create", "cross", "--title", "Artifact")
    assert r.returncode == 0, r.stdout + r.stderr
    (root / "docs" / "specs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "specs" / "x1.md").write_text("# spec\n")
    before_worker = (worker / "docs/tasklist.json").read_text()

    r = _tasktool(worker, "artifact", "add", "X1", "--kind", "spec", "--path", "docs/specs/x1.md")

    assert r.returncode == 0, r.stdout + r.stderr
    assert (worker / "docs/tasklist.json").read_text() == before_worker
    data = json.loads((root / "docs/tasklist.json").read_text())
    assert "docs/specs/x1.md" in data["cross_cutting"][0]["refs"]


def test_worker_artifact_add_refuses_invocation_only_file(tmp_path):
    root, worker = _authority_with_worker(tmp_path)
    r = _tasktool(root, "create", "cross", "--title", "Artifact")
    assert r.returncode == 0, r.stdout + r.stderr
    (worker / "docs" / "specs").mkdir(parents=True, exist_ok=True)
    (worker / "docs" / "specs" / "worker-only.md").write_text("# spec\n")

    r = _tasktool(worker, "artifact", "add", "X1", "--kind", "spec", "--path", "docs/specs/worker-only.md")

    assert r.returncode == 1
    assert "artifact exists in invocation checkout but not authoritative checkout" in r.stderr
```

- [ ] **Step 3: Implement commit helpers**

In `artifacts.py`, add:

```python
ALLOWED_COMMIT_PREFIXES = (
    "docs/tasklist.json",
    ".tasktool/config.json",
    "docs/specs/",
    "docs/plans/",
    "docs/handoffs/",
    "docs/reviewer/",
    "docs/archived-tasks/",
)


def disallowed_staged_paths(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    bad = []
    for rel in result.stdout.splitlines():
        if rel == "docs/tasklist.json" or rel == ".tasktool/config.json":
            continue
        if not any(rel.startswith(prefix) for prefix in ALLOWED_COMMIT_PREFIXES if prefix.endswith("/")):
            bad.append(rel)
    return bad


def derive_target_slug(paths: set[str], row_id: str) -> str | None:
    for rel in sorted(paths):
        name = Path(rel).name
        if not name.endswith(".md"):
            continue
        stem = name.removesuffix(".md")
        parts = stem.split("-")
        if len(parts) >= 4 and parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit():
            stem = "-".join(parts[3:])
        prefix = f"{row_id}-"
        if stem.startswith(prefix):
            stem = stem[len(prefix):]
        stem = stem.removesuffix("-design").removesuffix("-prompt")
        if stem:
            return stem
    return None


def same_slug_orphans(repo_root: Path, *, row_id: str, referenced: set[str]) -> list[str]:
    slug = derive_target_slug(referenced, row_id)
    if not slug:
        return []
    row_id_l = row_id.lower()
    slug_l = slug.lower()
    orphans = []
    for rel in _workflow_files(repo_root):
        if rel in referenced:
            continue
        if rel.startswith("docs/archived-tasks/"):
            continue
        rel_l = rel.lower()
        if rel_l.startswith("docs/reviewer/"):
            if slug_l in rel_l and (rel_l.endswith("-spec") or rel_l.endswith("-plan")):
                orphans.append(rel)
            continue
        if row_id_l in rel_l and slug_l in rel_l:
            orphans.append(rel)
    return sorted(orphans)
```

- [ ] **Step 4: Implement `cmd_artifact_commit`**

In `commands.py`, add:

```python
def cmd_artifact_commit(*, repo_root: Path, id: str, message: str) -> None:
    with _write_context(repo_root) as write_root:
        p = _load(write_root)
        qid, _container, item = _find_item(p, id)
        paths = sorted(referenced_paths_for_item(item))
        missing = [rel for rel in paths if not (write_root / rel).exists()]
        if missing:
            raise CommandError("missing referenced artifacts: " + ", ".join(missing))
        _git_stage_rel(write_root, "docs/tasklist.json")
        for rel in paths:
            _git_stage_rel(write_root, rel)
        status_code = cmd_artifact_status(repo_root=write_root, id=qid, strict=True, format="text")
        if status_code != 0:
            raise CommandError("artifact status is not clean")
        orphans = same_slug_orphans(write_root, row_id=qid, referenced=set(paths))
        if orphans:
            raise CommandError("unreferenced same-slug workflow artifacts: " + ", ".join(orphans))
        bad = disallowed_staged_paths(write_root)
        if bad:
            raise CommandError("unrelated staged paths: " + ", ".join(bad))
        result = _subprocess.run(
            ["git", "commit", "-m", message],
            cwd=write_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise CommandError(result.stderr.strip() or result.stdout.strip() or "git commit failed")
        print(result.stdout.strip())
```

- [ ] **Step 5: Wire CLI parser**

Add:

```python
p_artifact_commit = artifact_sub.add_parser("commit")
p_artifact_commit.add_argument("id")
p_artifact_commit.add_argument("--message", required=True)
```

Dispatch to `cmd_artifact_commit`.

- [ ] **Step 6: Run focused tests**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_artifact_cli.py tools/tasktool/tests/test_worktree_authority.py -q
```

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add tools/tasktool/artifacts.py tools/tasktool/commands.py tools/tasktool/cli.py tools/tasktool/tests/test_artifact_cli.py tools/tasktool/tests/test_worktree_authority.py
git commit -m "X17: add artifact commit and routed worktree coverage"
```

---

## Task 5: Update workflow skills and run full verification

**Files:**
- Modify: `skills/brainstorming/SKILL.md`
- Modify: `skills/writing-plans/SKILL.md`
- Modify: `skills/tasklist-discipline/SKILL.md`
- Modify: `skills/external-review/SKILL.md`
- Modify: `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py`

- [ ] **Step 1: Add docs tests for skill wording**

Update `tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py` with checks for:

```python
def test_planning_skills_reference_artifact_transactions():
    root = Path(__file__).resolve().parents[3]
    brainstorming = (root / "skills/brainstorming/SKILL.md").read_text(encoding="utf-8")
    writing = (root / "skills/writing-plans/SKILL.md").read_text(encoding="utf-8")
    discipline = (root / "skills/tasklist-discipline/SKILL.md").read_text(encoding="utf-8")
    review = (root / "skills/external-review/SKILL.md").read_text(encoding="utf-8")

    assert "tasktool prepare" in brainstorming
    assert "tasktool artifact add" in brainstorming
    assert "tasktool artifact commit" in brainstorming
    assert "tasktool artifact status" in writing
    assert "workflow artifacts" in discipline
    assert "tasktool artifact add" in review
```

- [ ] **Step 2: Run the docs test and confirm failure**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py -q
```

Expected: failure until skill docs are updated.

- [ ] **Step 3: Patch `skills/brainstorming/SKILL.md`**

In the spec-writing checklist, replace generic tasktool row/ref guidance with:

```markdown
Before writing the spec file, reserve the row and future spec path:

`tasktool prepare cross --title "<title>" --spec docs/specs/YYYY-MM-DD-XNN-slug-design.md`

or, for an existing row:

`tasktool prepare existing XNN --spec docs/specs/YYYY-MM-DD-XNN-slug-design.md`

After writing the spec file, run `tasktool artifact add XNN --kind spec --path <spec-path>` so the now-existing artifact is staged. After the spec review passes, register the reviewer chain with `tasktool artifact add XNN --kind reviewer --path docs/reviewer/<chain>/`, run `tasktool artifact status XNN --strict`, and close the spec transaction with `tasktool artifact commit XNN --message "XNN: add <slug> spec"` unless the user explicitly asked not to commit.
```

- [ ] **Step 4: Patch `skills/writing-plans/SKILL.md`**

In the save/handoff sections, add:

```markdown
Before writing the plan and handoff, register future paths with `tasktool prepare existing <id> --plan <plan-path> --handoff <handoff-path>`. After writing each file, run `tasktool artifact add <id> --kind plan --path <plan-path>` and `tasktool artifact add <id> --kind handoff --path <handoff-path>`. After plan review passes, register the reviewer chain, run `tasktool artifact status <id> --strict`, and use `tasktool artifact commit <id> --message "<id>: add <slug> plan"` unless the user explicitly asked not to commit.
```

- [ ] **Step 5: Patch `skills/tasklist-discipline/SKILL.md`**

Add a short section:

```markdown
## Workflow artifacts

Spec, plan, handoff, reviewer-chain, and archived-task paths are workflow artifacts. Register them through `tasktool artifact add` or `tasktool prepare`; do not hand-edit `docs/tasklist.json` refs for these paths. Use `tasktool artifact status <id> --strict` before handing work to another agent.
```

- [ ] **Step 6: Patch `skills/external-review/SKILL.md`**

After the successful review description, add:

```markdown
When `docs/tasklist.json` exists and the reviewed target maps to a tasktool row, register the chain directory after a passing spec or plan review:

`tasktool artifact add <id> --kind reviewer --path docs/reviewer/<chain>/`
```

- [ ] **Step 7: Run docs and full tasktool tests**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests -q
tools/tasktool/tasktool validate --strict-format
git diff --check
```

Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add skills/brainstorming/SKILL.md skills/writing-plans/SKILL.md skills/tasklist-discipline/SKILL.md skills/external-review/SKILL.md tools/tasktool/tests/test_skill_tasktool_lifecycle_docs.py
git commit -m "X17: document transactional workflow artifact handling"
```

---

## Closeout

- [ ] **Step 1: Run final verification**

```bash
PYTHONPATH=tools pytest tools/tasktool/tests -q
tools/tasktool/tasktool validate --strict-format
git diff --check
```

Expected:
- pytest passes.
- tasktool validation prints `ok`.
- `git diff --check` prints nothing.

- [ ] **Step 2: Run external post-slice review**

```bash
external-reviewer review \
  --kind post-slice \
  --work-id X17 \
  --file docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md \
  --context docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md \
  --context docs/tasklist.json \
  --caller-provider codex \
  --reviewer-provider codex \
  --emit json
```

Expected: `merged_verdict` is `ready` or `ready with small edits`.

- [ ] **Step 3: Close X17**

```bash
tools/tasktool/tasktool close X17 \
  --refs docs/specs/2026-05-21-X17-transactional-spec-plan-artifacts-design.md \
  --refs docs/plans/2026-05-21-X17-transactional-spec-plan-artifacts.md \
  --refs docs/handoffs/2026-05-21-X17-transactional-spec-plan-artifacts-prompt.md \
  --refs docs/reviewer/x17-transactional-spec-plan-artifacts-X17-post-slice/ \
  --note "Added transactional tasktool handling for spec/plan/handoff/reviewer artifacts."
```

Expected: X17 status becomes `done`.

- [ ] **Step 4: Version decision**

This changes `tools/` and `skills/`, so before a finished-work commit that ships to users, ask:

```text
Bump the version before/after this commit? (current: read from package.json -> patch / minor / no bump)
```

Follow `AGENTS.md`: if the user chooses a bump, run `./scripts/bump-version.sh <new-version>` and commit the bump separately before any local publish script.
