from pathlib import Path

from tasktool.worktree_lifecycle import legacy_worktree_dirs


def test_legacy_worktree_dirs_detects_each_known_path(tmp_path):
    repo = tmp_path / "repo"
    home = tmp_path / "home"
    (repo / ".claude" / "worktrees").mkdir(parents=True)
    (repo / ".codex" / "worktrees").mkdir(parents=True)
    (home / ".config" / "superstar" / "worktrees" / "demo").mkdir(parents=True)
    found = legacy_worktree_dirs(repo, home=home, project_name="demo")
    expected = {
        repo / ".claude" / "worktrees",
        repo / ".codex" / "worktrees",
        home / ".config" / "superstar" / "worktrees" / "demo",
    }
    assert set(found) == expected


def test_legacy_worktree_dirs_empty_when_none_present(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    assert legacy_worktree_dirs(repo, home=home, project_name="demo") == []


def test_legacy_worktree_dirs_ignores_missing_project_dir(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    home = tmp_path / "home"
    (home / ".config" / "superstar" / "worktrees").mkdir(parents=True)
    # No per-project subdir under worktrees/ → no match
    assert legacy_worktree_dirs(repo, home=home, project_name="absent") == []


def test_gitignore_entry_idempotent(tmp_path):
    """F4 acceptance: running the audit twice must not add `.worktrees/` twice."""
    from tasktool.worktree_lifecycle import ensure_gitignore_entry

    repo = tmp_path / "repo"
    repo.mkdir()
    gi = repo / ".gitignore"
    gi.write_text("node_modules/\n")
    # First call adds the entry
    changed_first = ensure_gitignore_entry(repo)
    assert changed_first is True
    text_after_first = gi.read_text()
    assert text_after_first.count(".worktrees/\n") == 1
    # Second call is a no-op
    changed_second = ensure_gitignore_entry(repo)
    assert changed_second is False
    assert gi.read_text() == text_after_first


def test_gitignore_entry_creates_file_when_absent(tmp_path):
    from tasktool.worktree_lifecycle import ensure_gitignore_entry
    repo = tmp_path / "repo"
    repo.mkdir()
    changed = ensure_gitignore_entry(repo)
    assert changed is True
    assert (repo / ".gitignore").read_text() == ".worktrees/\n"
