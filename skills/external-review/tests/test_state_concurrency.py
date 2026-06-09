"""Concurrency test for the production rate-limit write path.

Round-2 F1 fix: `run_one_reviewer` previously did a non-atomic
`load_state() -> mutate -> save_state()` sequence. Two concurrent
invocations could read the same baseline and the last writer would
clobber the first. Switching to `update_state(mutator)` holds the
state lock across read+write, preserving distinct keys.
"""

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "external-reviewer.py"


def _make_repo(root: Path, name: str) -> Path:
    repo = root / name
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\nbody\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    return repo


def _make_fake(repo: Path, name: str) -> Path:
    fake = repo / name
    fake.write_text(
        "#!/usr/bin/env bash\n"
        # Sleep briefly so both processes overlap the read-modify-write
        # window of the production rate-limit recorder.
        "sleep 0.2\n"
        "echo \"ERROR: You've hit your usage limit. Try again at 11:59 PM.\" >&2\n"
        "exit 1\n"
    )
    fake.chmod(0o755)
    return fake


ITERATIONS = 8


def _run_review(script: Path, repo: Path, fake: Path, state: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(fake)
    env["AGENT_REVIEWER_STATE_FILE"] = str(state)
    return subprocess.run(
        [
            sys.executable,
            str(script),
            "review",
            "--kind",
            "plan",
            "--file",
            "plan.md",
            "--emit",
            "json",
            "--no-preflight",
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_concurrent_production_writers_preserve_distinct_keys(tmp_path):
    """Two concurrent `review` invocations recording rate limits for
    different reviewer commands must both end up in the shared state
    file. This exercises the real production write path in
    `run_one_reviewer`, not just `update_state()` directly.

    Without the F1 fix (atomic update_state in run_one_reviewer), the
    load_state -> mutate -> save_state sequence races: two processes
    that both read the same baseline state, then each rewrite it with
    only their own key. The last writer wins and one key is silently
    dropped. We loop several iterations to amplify the collision
    probability — even a single dropped key in any iteration fails.
    """
    repo_a = _make_repo(tmp_path, "a")
    repo_b = _make_repo(tmp_path, "b")
    fake_a = _make_fake(repo_a, "fake-a")
    fake_b = _make_fake(repo_b, "fake-b")

    for i in range(ITERATIONS):
        state = tmp_path / f"rs-{i}.json"
        results: dict[str, subprocess.CompletedProcess] = {}

        def run(label: str, repo: Path, fake: Path) -> None:
            results[label] = _run_review(SCRIPT, repo, fake, state)

        t1 = threading.Thread(target=run, args=("a", repo_a, fake_a))
        t2 = threading.Thread(target=run, args=("b", repo_b, fake_b))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        for label, proc in results.items():
            assert proc.returncode != 0, (
                f"iter {i} {label}: unexpected success: {proc.stdout}\n{proc.stderr}"
            )

        assert state.exists(), f"iter {i}: state file was never written"
        final = json.loads(state.read_text())
        keys = set(final.get("limits", {}).keys())
        assert str(fake_a) in keys, (
            f"iter {i}: missing fake_a key in {keys} — non-atomic RMW "
            f"clobbered the entry"
        )
        assert str(fake_b) in keys, (
            f"iter {i}: missing fake_b key in {keys} — non-atomic RMW "
            f"clobbered the entry"
        )
