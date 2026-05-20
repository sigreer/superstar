import json, os, subprocess, sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"
PKG_DIR = Path(__file__).resolve().parents[3] / "tools"

def _run(root, *args):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PKG_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, str(TOOL), "--project-root", str(root), *args],
        capture_output=True, text=True, env=env,
    )

def _seed(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "specs").mkdir()
    (tmp_path / "docs" / "plans").mkdir()
    assert _run(tmp_path, "config", "init-local").returncode == 0
    _run(tmp_path, "init", "--project", "demo")
    pid = _run(tmp_path, "create", "phase", "--title", "Phase one").stdout.strip()
    sid = _run(tmp_path, "create", "slice", pid, "--title", "Slice one").stdout.strip()
    return pid, sid

def test_orphan_spec_filename_is_flagged(tmp_path):
    pid, sid = _seed(tmp_path)
    orphan = tmp_path / "docs" / "specs" / "2026-05-18-P99-orphan-design.md"
    orphan.write_text("# orphan\n")
    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(orphan))
    assert r.returncode == 1, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    assert any("P99" in e for e in payload["errors"])

def test_known_id_filename_passes(tmp_path):
    pid, sid = _seed(tmp_path)
    known = tmp_path / "docs" / "plans" / f"2026-05-18-{pid.lower()}-{sid.lower()}-thing.md"
    known.write_text("# plan\n")
    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(known))
    assert r.returncode == 0, r.stdout + r.stderr

def test_cross_cutting_top_level_filename_passes(tmp_path):
    _seed(tmp_path)
    cid = _run(tmp_path, "create", "cross", "--title", "C4").stdout.strip()
    f = tmp_path / "docs" / "specs" / f"2026-05-18-{cid.lower()}-design.md"
    f.write_text("# cross spec\n")
    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(f))
    assert r.returncode == 0, r.stdout + r.stderr

def test_cross_cutting_unknown_top_level_is_flagged(tmp_path):
    _seed(tmp_path)
    f = tmp_path / "docs" / "specs" / "2026-05-18-x99-design.md"
    f.write_text("# nope\n")
    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(f))
    assert r.returncode == 1, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    assert any("X99" in e for e in payload["errors"])

def test_wrong_phase_qualified_id_is_flagged(tmp_path):
    _seed(tmp_path)  # creates P1.S1
    orphan = tmp_path / "docs" / "plans" / "2026-05-18-p99-s1-thing.md"
    orphan.write_text("# wrong-phase\n")
    r = _run(tmp_path, "validate", "--format", "json", "--check-orphans", str(orphan))
    assert r.returncode == 1, r.stdout + r.stderr
    payload = json.loads(r.stdout)
    assert any("P99.S1" in e for e in payload["errors"])
