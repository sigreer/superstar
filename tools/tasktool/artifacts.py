from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


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

WORKFLOW_DIRS = {
    "docs/specs": ArtifactKind.SPEC,
    "docs/plans": ArtifactKind.PLAN,
    "docs/handoffs": ArtifactKind.HANDOFF,
    "docs/reviewer": ArtifactKind.REVIEWER,
    "docs/archived-tasks": ArtifactKind.ARCHIVE,
}

ALLOWED_TRANSACTION_FILES = {"docs/tasklist.json", ".tasktool/config.json"}


@dataclass(frozen=True)
class NormalizedArtifact:
    kind: ArtifactKind
    relative_path: str
    invocation_path: Path
    write_path: Path
    exists_in_write_root: bool


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


def add_artifact_to_item(item, artifact: NormalizedArtifact) -> bool:
    refs = getattr(item, "refs", None)
    added = False
    if refs is not None:
        if artifact.relative_path not in refs:
            refs.append(artifact.relative_path)
            added = True
    elif artifact.kind == ArtifactKind.HANDOFF and hasattr(item, "planning_path"):
        added = item.planning_path != artifact.relative_path
        item.planning_path = artifact.relative_path
    elif artifact.kind not in {ArtifactKind.SPEC, ArtifactKind.PLAN, ArtifactKind.REVIEWER}:
        raise ArtifactError("this item kind does not have refs")

    if artifact.kind == ArtifactKind.SPEC and hasattr(item, "spec_path"):
        added = item.spec_path != artifact.relative_path or added
        item.spec_path = artifact.relative_path
    elif artifact.kind == ArtifactKind.PLAN and hasattr(item, "plan_path"):
        added = item.plan_path != artifact.relative_path or added
        item.plan_path = artifact.relative_path
    elif artifact.kind == ArtifactKind.REVIEWER:
        if hasattr(item, "reviewer_chain"):
            added = item.reviewer_chain != artifact.relative_path or added
            item.reviewer_chain = artifact.relative_path
        elif hasattr(item, "phase_reviewer_chain"):
            added = item.phase_reviewer_chain != artifact.relative_path or added
            item.phase_reviewer_chain = artifact.relative_path
        elif refs is None:
            raise ArtifactError("this item kind does not have refs")
    return added


def artifact_kind_for_path(rel: str) -> ArtifactKind | None:
    for kind, prefix in KIND_PREFIXES.items():
        if rel.startswith(prefix):
            return kind
    return None


def is_workflow_artifact_path(rel: str) -> bool:
    return artifact_kind_for_path(rel) is not None


def referenced_paths_for_item(item) -> set[str]:
    paths = {
        path
        for path in (getattr(item, "refs", []) or [])
        if is_workflow_artifact_path(path)
    }
    for attr in ("spec_path", "plan_path", "planning_path", "reviewer_chain", "phase_reviewer_chain"):
        value = getattr(item, attr, None)
        if value and is_workflow_artifact_path(value):
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
            path = line[3:]
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            statuses[path] = GitPathStatus(index=line[0], worktree=line[1])
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
    return "".join(
        f"{p.severity} {p.code} {p.path}: {p.message}\n"
        for p in rows
    )


def render_status_json(problems: Iterable[ArtifactProblem]) -> str:
    rows = list(problems)
    return json.dumps(
        {"ok": not rows, "problems": [asdict(p) for p in rows]},
        indent=2,
        sort_keys=True,
    ) + "\n"


def workflow_files(root: Path) -> set[str]:
    found: set[str] = set()
    for base in WORKFLOW_DIRS:
        path = root / base
        if not path.exists():
            continue
        if base == "docs/reviewer":
            for child in path.iterdir():
                if child.is_dir():
                    found.add(child.relative_to(root).as_posix())
            continue
        for child in path.rglob("*"):
            if child.is_file():
                found.add(child.relative_to(root).as_posix())
    return found


def _path_is_allowed_by_transaction(rel: str, allowed_paths: set[str]) -> bool:
    for allowed in allowed_paths:
        if rel == allowed or rel.startswith(allowed.rstrip("/") + "/"):
            return True
    return False


def disallowed_staged_paths(repo_root: Path, allowed_paths: Iterable[str]) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    allowed = set(allowed_paths)
    bad = []
    for rel in result.stdout.splitlines():
        if rel in ALLOWED_TRANSACTION_FILES:
            continue
        if not _path_is_allowed_by_transaction(rel, allowed):
            bad.append(rel)
    return bad


def derive_target_slug(paths: set[str], row_id: str) -> str | None:
    row_id_l = row_id.lower()
    for rel in sorted(paths):
        if not rel.startswith(("docs/specs/", "docs/plans/", "docs/handoffs/")):
            continue
        name = Path(rel).name
        if not name.endswith(".md"):
            continue
        stem = name.removesuffix(".md")
        stem = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem)
        for prefix in (f"{row_id}-", f"{row_id_l}-"):
            if stem.lower().startswith(prefix.lower()):
                stem = stem[len(prefix):]
                break
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
    for rel in workflow_files(repo_root):
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
