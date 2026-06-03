from __future__ import annotations

import json
import subprocess
from pathlib import Path

TASKTOOL = Path(__file__).resolve().parents[1] / "tasktool"


def _run(cwd: Path, *args: str) -> str:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True).stdout


def _tasktool(repo: Path, *args: str, check: bool = True):
    return subprocess.run(
        [str(TASKTOOL), "--project-root", str(repo), *args],
        text=True, capture_output=True, check=check,
    )


def _init_repo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    _run(root, "git", "init", "-q", "-b", "main")
    _run(root, "git", "config", "user.email", "t@example.com")
    _run(root, "git", "config", "user.name", "t")
    (root / "README").write_text("init\n")
    _run(root, "git", "add", "README")
    _run(root, "git", "commit", "-q", "-m", "init")
    return root


def _seed(repo: Path, *slice_titles: str) -> None:
    (repo / "docs").mkdir(exist_ok=True)
    _tasktool(repo, "config", "init-local")
    _tasktool(repo, "init", "--project", "demo")
    _tasktool(repo, "create", "phase", "--title", "Phase 1")
    for title in slice_titles:
        _tasktool(repo, "create", "slice", "P1", "--title", title)
    _run(repo, "git", "add", "-A")
    _run(repo, "git", "commit", "-q", "-m", "seed")


def test_integration_reports_base_ahead_count(tmp_path):
    repo = _init_repo(tmp_path / "proj")
    _seed(repo, "First slice")
    _tasktool(repo, "start", "P1.S1")  # records worktree_base_sha at current main
    # Advance main by two commits after the worktree branched.
    (repo / "x").write_text("1")
    _run(repo, "git", "add", "x")
    _run(repo, "git", "commit", "-q", "-m", "x")
    (repo / "y").write_text("2")
    _run(repo, "git", "add", "y")
    _run(repo, "git", "commit", "-q", "-m", "y")
    out = _tasktool(repo, "worktree", "status", "P1.S1", "--integration").stdout
    assert "base ahead of worktree_base_sha: 2 commit" in out


def _start_worktree(repo: Path, slice_qid: str) -> Path:
    out = _tasktool(repo, "start", slice_qid).stdout
    # `start` prints `cd <path>`; recover the path from tasklist.json instead.
    data = json.loads((repo / "docs" / "tasklist.json").read_text())
    slc = next(
        s for ph in data["phases"] for s in ph["slices"]
        if f"{ph['id']}.{s['id']}" == slice_qid
    )
    return (repo / slc["worktree_path"]).resolve()


def _land_sibling(repo: Path, sibling_qid: str) -> None:
    """Close + merge + prune a sibling so it stamps landed_base_sha."""
    data = json.loads((repo / "docs" / "tasklist.json").read_text())
    slc = next(
        s for ph in data["phases"] for s in ph["slices"]
        if f"{ph['id']}.{s['id']}" == sibling_qid
    )
    branch = slc["worktree_branch"]
    wt_path = (repo / slc["worktree_path"]).resolve()
    # Make a real commit on the sibling branch so the merge is non-empty.
    (wt_path / "sibling-work").write_text("x")
    _run(wt_path, "git", "add", "sibling-work")
    _run(wt_path, "git", "commit", "-q", "-m", "sibling work")
    _tasktool(repo, "close", sibling_qid, "--skip-review-gate")
    # start/close route tasklist mutations to the authoritative checkout, leaving
    # docs/tasklist.json dirty on main; commit it so the sibling-branch merge
    # (which carries its own docs/tasklist.json) is not refused.
    _run(repo, "git", "add", "docs/tasklist.json")
    _run(repo, "git", "commit", "-q", "-m", f"route mutations before merge {branch}")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", f"merge {branch}", branch)
    _tasktool(repo, "worktree", "prune", sibling_qid)


def test_integration_reports_landed_sibling_via_landed_base_sha(tmp_path):
    repo = _init_repo(tmp_path / "proj")
    _seed(repo, "This slice", "Sibling slice")
    # Start this slice first so its worktree_base_sha predates the sibling landing.
    _start_worktree(repo, "P1.S1")
    _start_worktree(repo, "P1.S2")
    _land_sibling(repo, "P1.S2")  # stamps landed_base_sha = main HEAD after merge
    out = _tasktool(repo, "worktree", "status", "P1.S1", "--integration").stdout
    assert "landed since worktree_base_sha:" in out
    assert "P1.S2" in out
    assert "(authoritative)" in out


def test_integration_reports_landed_sibling_via_ancestry_fallback(tmp_path):
    repo = _init_repo(tmp_path / "proj")
    _seed(repo, "This slice", "Sibling slice")
    _start_worktree(repo, "P1.S1")
    sib_wt = _start_worktree(repo, "P1.S2")
    data = json.loads((repo / "docs" / "tasklist.json").read_text())
    sib = next(s for s in data["phases"][0]["slices"] if s["id"] == "S2")
    branch = sib["worktree_branch"]
    # Real commit, close, merge — but DO NOT prune (so no landed_base_sha stamp).
    (sib_wt / "w").write_text("x")
    _run(sib_wt, "git", "add", "w")
    _run(sib_wt, "git", "commit", "-q", "-m", "w")
    _tasktool(repo, "close", "P1.S2", "--skip-review-gate")
    _run(repo, "git", "add", "docs/tasklist.json")
    _run(repo, "git", "commit", "-q", "-m", "route mutations")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m", branch)
    out = _tasktool(repo, "worktree", "status", "P1.S1", "--integration").stdout
    assert "P1.S2 (ancestry)" in out


def test_integration_reports_unknown_for_done_sibling_without_branch_or_sha(tmp_path):
    repo = _init_repo(tmp_path / "proj")
    _seed(repo, "This slice", "Sibling slice")
    _start_worktree(repo, "P1.S1")
    # Sibling was started in-place (no branch) and closed; neither signal exists.
    _tasktool(repo, "start", "P1.S2", "--in-place")
    _tasktool(repo, "close", "P1.S2", "--skip-review-gate")
    out = _tasktool(repo, "worktree", "status", "P1.S1", "--integration").stdout
    # Not silently treated as landed: it must NOT appear in the landed list.
    assert "P1.S2 (authoritative)" not in out
    assert "P1.S2 (ancestry)" not in out
    # And the unknown state is surfaced.
    assert "P1.S2 (unknown)" in out


def test_integration_ancestry_not_landed_when_sibling_merged_before_base_sha(tmp_path):
    """F2 negative case: a done sibling whose branch is already an ancestor of
    THIS slice's worktree_base_sha (it merged BEFORE this worktree branched)
    must be reported NOT landed-since — `branch_is_merged(into=base_head)` is
    true for it, so the half-open window is what excludes it."""
    repo = _init_repo(tmp_path / "proj")
    _seed(repo, "This slice", "Sibling slice")
    # Start the SIBLING first, do its work, and MERGE it into main — all BEFORE
    # this slice's worktree branches.
    sib_wt = _start_worktree(repo, "P1.S2")
    data = json.loads((repo / "docs" / "tasklist.json").read_text())
    sib = next(s for s in data["phases"][0]["slices"] if s["id"] == "S2")
    branch = sib["worktree_branch"]
    (sib_wt / "w").write_text("x")
    _run(sib_wt, "git", "add", "w")
    _run(sib_wt, "git", "commit", "-q", "-m", "w")
    _tasktool(repo, "close", "P1.S2", "--skip-review-gate")
    _run(repo, "git", "add", "docs/tasklist.json")
    _run(repo, "git", "commit", "-q", "-m", "route mutations")
    _run(repo, "git", "merge", "--no-ff", "-q", "-m", "m", branch)
    # NOTE: do NOT prune S2, so it has no landed_base_sha and falls to the
    # ancestry branch. Its branch ref still exists and IS an ancestor of main.
    # NOW this slice branches — base_sha = main HEAD, which already contains S2.
    _start_worktree(repo, "P1.S1")
    out = _tasktool(repo, "worktree", "status", "P1.S1", "--integration").stdout
    # S2 merged before P1.S1 branched: it is NOT "landed since worktree_base_sha".
    assert "P1.S2 (ancestry)" not in out
    assert "P1.S2 (authoritative)" not in out
    # It is also not "undetermined": its branch is genuinely merged into base,
    # just outside the window. It must not appear in the landed list at all.
    # (The signal `merged-before-window` is non-landed and not surfaced.)
