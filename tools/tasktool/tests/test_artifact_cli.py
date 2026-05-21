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


def test_artifact_add_reviewer_directory_registers_ref(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    chain = root / "docs" / "reviewer" / "x1-artifact-plan"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[]}\n', encoding="utf-8")

    r = _tasktool(root, "artifact", "add", "X1", "--kind", "reviewer", "--path", "docs/reviewer/x1-artifact-plan")

    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads((root / "docs/tasklist.json").read_text(encoding="utf-8"))
    assert "docs/reviewer/x1-artifact-plan" in data["cross_cutting"][0]["refs"]


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


def test_artifact_status_json_reports_problem_shape(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert _tasktool(root, "artifact", "add", "X1", "--kind", "spec", "--path", "docs/specs/missing.md", "--allow-missing").returncode == 0

    r = _tasktool(root, "artifact", "status", "X1", "--strict", "--format", "json")

    assert r.returncode == 1
    data = json.loads(r.stdout)
    assert data["ok"] is False
    assert data["problems"][0]["code"] == "missing-referenced-artifact"


def test_artifact_status_reports_unreferenced_reviewer_directory(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    chain = root / "docs" / "reviewer" / "x1-plan"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[]}\n', encoding="utf-8")

    r = _tasktool(root, "artifact", "status", "--strict")

    assert r.returncode == 1
    assert "unreferenced-workflow-artifact" in r.stdout
    assert "docs/reviewer/x1-plan" in r.stdout


def test_artifact_status_accepts_archived_phase_and_snapshot_artifacts(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    archive_rel = "docs/archived-tasks/P1-archived-work.md"
    spec_rel = "docs/specs/2026-05-21-P1-archived-work-design.md"
    chain_rel = "docs/reviewer/p1-archived-work-post-phase"
    (root / archive_rel).parent.mkdir(parents=True)
    (root / spec_rel).parent.mkdir(parents=True)
    (root / chain_rel).mkdir(parents=True)
    (root / spec_rel).write_text("# archived spec\n", encoding="utf-8")
    (root / chain_rel / "chain.json").write_text('{"rounds":[]}\n', encoding="utf-8")
    snapshot = {
        "project": "demo",
        "schema_version": 1,
        "phases": [
            {
                "id": "P1",
                "title": "Archived work",
                "created": "2026-05-21",
                "status": "done",
                "spec_path": spec_rel,
                "phase_reviewer_chain": chain_rel,
                "slices": [],
            }
        ],
        "cross_cutting": [],
        "archived_phases": [],
    }
    (root / archive_rel).write_text(
        "# P1 - Archived work\n\n```json\n"
        + json.dumps(snapshot, indent=2, sort_keys=True)
        + "\n```\n",
        encoding="utf-8",
    )
    data = json.loads((root / "docs/tasklist.json").read_text(encoding="utf-8"))
    data["archived_phases"] = [
        {
            "id": "P1",
            "title": "Archived work",
            "archived_path": archive_rel,
            "archived_date": "2026-05-21",
        }
    ]
    (root / "docs/tasklist.json").write_text(json.dumps(data), encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "archive phase")

    r = _tasktool(root, "artifact", "status", "--strict")

    assert r.returncode == 0, r.stdout + r.stderr


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
    assert not (root / "docs" / "specs" / "2026-05-21-X2-prepared-design.md").exists()


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


def test_prepare_phase_registers_handoff_on_planning_path(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    r = _tasktool(
        root,
        "prepare",
        "phase",
        "--title",
        "Prepared phase",
        "--handoff",
        "docs/handoffs/2026-05-21-P1-prepared-prompt.md",
    )

    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads((root / "docs/tasklist.json").read_text(encoding="utf-8"))
    assert data["phases"][0]["id"] == "P1"
    assert data["phases"][0]["planning_path"] == "docs/handoffs/2026-05-21-P1-prepared-prompt.md"


def test_prepare_rejects_invalid_artifact_kind_before_allocating_row(tmp_path: Path) -> None:
    root = _repo(tmp_path)

    r = _tasktool(
        root,
        "prepare",
        "cross",
        "--title",
        "Invalid prepared artifact",
        "--plan",
        "docs/specs/wrong-kind.md",
    )

    assert r.returncode == 1
    assert "plan artifacts must live under docs/plans/" in r.stderr
    data = json.loads((root / "docs/tasklist.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in data["cross_cutting"]] == ["X1"]
    assert _git(root, "status", "--porcelain").stdout == ""


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


def test_artifact_commit_refuses_unrelated_staged_workflow_file(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert _tasktool(root, "artifact", "add", "X1", "--kind", "spec", "--path", "docs/specs/future.md", "--allow-missing").returncode == 0
    spec = root / "docs" / "specs" / "future.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("# future\n", encoding="utf-8")
    other = root / "docs" / "plans" / "other.md"
    other.parent.mkdir(parents=True)
    other.write_text("# other\n", encoding="utf-8")
    _git(root, "add", "docs/plans/other.md")

    r = _tasktool(root, "artifact", "commit", "X1", "--message", "X1: artifacts")

    assert r.returncode == 1
    assert "unrelated staged paths" in r.stderr
    assert "docs/plans/other.md" in r.stderr


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
