import json
import os
import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
PYTHONPATH = str(Path(__file__).resolve().parents[2])


def run(root, *args):
    env = os.environ.copy()
    env["PYTHONPATH"] = PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, str(TOOL), "--project-root", str(root), *args],
        text=True,
        capture_output=True,
        env=env,
    )


def seed(root):
    (root / "docs").mkdir()
    assert run(root, "init", "--project", "demo").returncode == 0
    assert run(root, "create", "phase", "--title", "Phase").returncode == 0
    assert run(root, "create", "slice", "P1", "--title", "Slice").returncode == 0
    assert run(root, "create", "task", "P1.S1", "--title", "Task").returncode == 0


def tasklist(root):
    return json.loads((root / "docs" / "tasklist.json").read_text())


def ready_chain(root):
    chain = root / "docs" / "reviewer" / "p1-s1-post-slice"
    chain.mkdir(parents=True)
    (chain / "chain.json").write_text('{"rounds":[{"round":1,"merged_verdict":"ready","status":"ok"}]}')
    return chain


def test_start_slice_sets_in_progress_and_started(tmp_path):
    seed(tmp_path)
    r = run(tmp_path, "start", "P1.S1")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "in_progress"
    assert sl["started"]


def test_set_in_progress_sets_started(tmp_path):
    seed(tmp_path)
    r = run(tmp_path, "set", "P1.S1", "--status", "in_progress")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "in_progress"
    assert sl["started"]


def test_start_blocked_item_requires_resume(tmp_path):
    seed(tmp_path)
    assert run(tmp_path, "block", "P1.S1", "--on", "external:waiting").returncode == 0
    r = run(tmp_path, "start", "P1.S1")
    assert r.returncode == 1
    assert "use start --resume" in r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "blocked"
    assert sl["blocked_on"] == {"kind": "external", "value": "waiting"}


def test_start_resume_clears_blocked_on_and_sets_started(tmp_path):
    seed(tmp_path)
    assert run(tmp_path, "block", "P1.S1", "--on", "external:waiting").returncode == 0
    r = run(tmp_path, "start", "P1.S1", "--resume")
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "in_progress"
    assert sl["blocked_on"] is None
    assert sl["started"]


def test_set_in_progress_on_blocked_item_refuses_without_resume(tmp_path):
    seed(tmp_path)
    assert run(tmp_path, "block", "P1.S1", "--on", "external:waiting").returncode == 0
    r = run(tmp_path, "set", "P1.S1", "--status", "in_progress")
    assert r.returncode == 1
    assert "use start --resume" in r.stderr


def test_start_done_item_refuses(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    assert run(tmp_path, "start", "P1.S1").returncode == 0
    assert run(tmp_path, "close", "P1.S1", "--reviewer-chain", str(chain)).returncode == 0
    r = run(tmp_path, "start", "P1.S1")
    assert r.returncode == 1
    assert "already done" in r.stderr


def test_close_ready_slice_refuses_without_override(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    r = run(tmp_path, "close", "P1.S1", "--reviewer-chain", str(chain))
    assert r.returncode == 1
    assert "must be started before close" in r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "ready"
    assert sl["closed"] is None


def test_close_ready_slice_override_requires_reason(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    r = run(tmp_path, "close", "P1.S1", "--reviewer-chain", str(chain), "--allow-ready-close")
    assert r.returncode == 1
    assert "requires --reason" in r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "ready"
    assert sl["closed"] is None


def test_close_ready_slice_override_records_note(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    r = run(
        tmp_path,
        "close",
        "P1.S1",
        "--reviewer-chain",
        str(chain),
        "--allow-ready-close",
        "--reason",
        "legacy slice closed before start existed",
    )
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "done"
    assert "ready-close override for P1.S1: legacy slice closed before start existed" in sl["notes"]


def test_set_done_ready_slice_refuses_without_start(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    r = run(tmp_path, "set", "P1.S1", "--status", "done", "--reviewer-chain", str(chain))
    assert r.returncode == 1
    assert "must be started before close" in r.stderr
    assert "tasktool start P1.S1" in r.stderr
    assert "tasktool set P1.S1 --status done --allow-ready-close --reason" in r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "ready"
    assert sl["closed"] is None


def test_set_done_ready_slice_override_requires_reason(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    r = run(
        tmp_path,
        "set",
        "P1.S1",
        "--status",
        "done",
        "--reviewer-chain",
        str(chain),
        "--allow-ready-close",
    )
    assert r.returncode == 1
    assert "requires --reason" in r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "ready"
    assert sl["closed"] is None


def test_set_done_ready_slice_override_records_note(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    r = run(
        tmp_path,
        "set",
        "P1.S1",
        "--status",
        "done",
        "--reviewer-chain",
        str(chain),
        "--allow-ready-close",
        "--reason",
        "legacy scripted close before start existed",
    )
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "done"
    assert sl["started"] is None
    assert sl["closed"]
    assert "ready-close override for P1.S1: legacy scripted close before start existed" in sl["notes"]
    assert sl["reviewer_chain"] == "docs/reviewer/p1-s1-post-slice"


def test_set_done_started_slice_records_reviewer_chain(tmp_path):
    seed(tmp_path)
    chain = ready_chain(tmp_path)
    assert run(tmp_path, "start", "P1.S1").returncode == 0
    r = run(tmp_path, "set", "P1.S1", "--status", "done", "--reviewer-chain", str(chain))
    assert r.returncode == 0, r.stdout + r.stderr
    sl = tasklist(tmp_path)["phases"][0]["slices"][0]
    assert sl["status"] == "done"
    assert sl["reviewer_chain"] == "docs/reviewer/p1-s1-post-slice"
