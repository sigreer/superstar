import subprocess, sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "external-reviewer.py"


def test_review_help_works():
    """external-reviewer.py review --help must exit 0 with subparser help."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "review", "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode == 0, proc.stderr
    assert "--file" in proc.stdout


def test_review_state_file_flag_accepted(tmp_path):
    """--state-file must be a known flag on the review subcommand (argparse accepts it)."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "review", "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert "--state-file" in proc.stdout


def test_existing_review_flags_still_present():
    """Existing flags (--kind, --file, --context, --work-id, --emit) survive the refactor."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "review", "--help"],
        capture_output=True, text=True, timeout=10,
    )
    for flag in ("--kind", "--file", "--context", "--work-id", "--emit"):
        assert flag in proc.stdout, f"Missing: {flag}"


def test_unknown_command_exits_nonzero():
    """An unrecognised subcommand must produce a non-zero exit, not a crash."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "no-such-cmd"],
        capture_output=True, text=True, timeout=10,
    )
    assert proc.returncode != 0
