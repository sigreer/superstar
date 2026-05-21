from __future__ import annotations

from pathlib import Path

import pytest

from tasktool.artifacts import (
    ArtifactError,
    ArtifactKind,
    derive_target_slug,
    normalize_artifact_path,
    same_slug_orphans,
)


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


def test_derive_target_slug_removes_date_id_and_suffix() -> None:
    assert derive_target_slug(
        {"docs/specs/2026-05-21-X17-transactional-artifacts-design.md"},
        "X17",
    ) == "transactional-artifacts"


def test_same_slug_orphans_finds_plan_and_reviewer_chain(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "docs" / "specs").mkdir(parents=True)
    (repo / "docs" / "plans").mkdir(parents=True)
    (repo / "docs" / "reviewer" / "x17-artifact-plan").mkdir(parents=True)
    spec = "docs/specs/2026-05-21-X17-artifact-design.md"
    (repo / spec).write_text("# spec\n", encoding="utf-8")
    (repo / "docs" / "plans" / "2026-05-21-X17-artifact.md").write_text("# plan\n", encoding="utf-8")

    assert same_slug_orphans(repo, row_id="X17", referenced={spec}) == [
        "docs/plans/2026-05-21-X17-artifact.md",
        "docs/reviewer/x17-artifact-plan",
    ]
