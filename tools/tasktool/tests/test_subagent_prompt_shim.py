"""Spec §6 P5.S3: assert each dispatched-subagent prompt template instructs
the subagent to export SUPERSTAR_SUBAGENT_ROLE, and that the coordinator's
own SKILL.md does NOT set the same variable for itself."""
from __future__ import annotations
from pathlib import Path

import os
import subprocess
import sys

PROMPTS = Path(__file__).resolve().parents[3] / "skills" / "subagent-driven-development"

EXPECTED = {
    "implementer-prompt.md": "implementer",
    "spec-reviewer-prompt.md": "spec-reviewer",
    "code-quality-reviewer-prompt.md": "code-quality-reviewer",
}


def test_each_subagent_prompt_exports_subagent_role():
    for fname, role in EXPECTED.items():
        text = (PROMPTS / fname).read_text()
        expected = f"export SUPERSTAR_SUBAGENT_ROLE={role}"
        assert expected in text, (
            f"{fname} must contain `{expected}` so dispatched subagents "
            f"trigger the tasktool subagent guard (spec §5.3)."
        )


def test_each_subagent_prompt_forbids_calling_tasktool_start():
    for fname in EXPECTED:
        text = (PROMPTS / fname).read_text().lower()
        assert ("do not run `tasktool start`" in text or
                "do not call `tasktool start`" in text or
                "do not start the slice yourself" in text), (
            f"{fname} must explicitly forbid the dispatched subagent from "
            f"calling tasktool start"
        )


def test_coordinator_skill_does_not_set_subagent_role_for_itself():
    skill = (PROMPTS / "SKILL.md").read_text()
    assert "export SUPERSTAR_SUBAGENT_ROLE" not in skill, (
        "subagent-driven-development SKILL.md must not instruct the "
        "coordinator to export SUPERSTAR_SUBAGENT_ROLE for itself"
    )


PYTHONPATH_REPO = str(Path(__file__).resolve().parents[2])
TASKTOOL_MAIN = Path(__file__).resolve().parents[2] / "tasktool" / "__main__.py"


def _seed_tmp(tmp_path, env_extra=None):
    (tmp_path / "docs").mkdir()
    def _seed(*args):
        env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": PYTHONPATH_REPO}
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            [sys.executable, str(TASKTOOL_MAIN),
             "--project-root", str(tmp_path), *args],
            env=env, text=True, capture_output=True,
        )
    assert _seed("config", "init-local").returncode == 0
    assert _seed("init", "--project", "demo").returncode == 0
    assert _seed("create", "phase", "--title", "Phase").returncode == 0
    assert _seed("create", "slice", "P1", "--title", "Slice").returncode == 0


def test_simulated_subagent_dispatch_refuses_tasktool_start(tmp_path):
    _seed_tmp(tmp_path)
    script = (
        f"export SUPERSTAR_SUBAGENT_ROLE=implementer && "
        f"{sys.executable} {TASKTOOL_MAIN} "
        f"--project-root {tmp_path} start P1.S1"
    )
    r = subprocess.run(
        ["env", "-i",
         f"PATH={os.environ.get('PATH','')}",
         f"PYTHONPATH={PYTHONPATH_REPO}",
         "bash", "-c", script],
        text=True, capture_output=True,
    )
    assert r.returncode != 0, (
        f"simulated subagent should have been refused; stdout={r.stdout!r} "
        f"stderr={r.stderr!r}"
    )
    spec_sentence = (
        "Subagents must inherit the parent's worktree; call the parent or "
        "'cd' into the existing recorded path: <not recorded>."
    )
    assert spec_sentence in (r.stdout + r.stderr), (
        f"refusal did not carry the spec sentence verbatim; "
        f"got: {r.stdout + r.stderr!r}"
    )


def test_simulated_coordinator_dispatch_proceeds(tmp_path):
    _seed_tmp(tmp_path)
    script = (
        f"{sys.executable} {TASKTOOL_MAIN} "
        f"--project-root {tmp_path} start P1.S1"
    )
    r = subprocess.run(
        ["env", "-i",
         f"PATH={os.environ.get('PATH','')}",
         f"PYTHONPATH={PYTHONPATH_REPO}",
         "bash", "-c", script],
        text=True, capture_output=True,
    )
    assert r.returncode == 0, (
        f"coordinator (no SUPERSTAR_SUBAGENT_ROLE) should have proceeded; "
        f"stdout={r.stdout!r} stderr={r.stderr!r}"
    )
