"""Regression: heading-style verdict (`Overall verdict\\n\\nready`) must parse.

Reviewers commonly emit the verdict as a heading with the value on the next
line, without a `:`/`-` separator. parse_verdict's regex requires that
separator, so record_reviewer_round normalises heading-style verdicts before
parsing. Without that normalisation the round records verdict_valid=false /
merged_verdict=null despite the textual verdict being unambiguous.
"""
from pathlib import Path
import subprocess, sys, json, os

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


FAKE_REVIEWER_HEADING_STYLE = """#!/usr/bin/env bash
cat <<'EOF'
## Findings
none

5. Overall verdict

ready with small edits
EOF
"""

FAKE_REVIEWER_BOLD_HEADING_STYLE = """#!/usr/bin/env bash
cat <<'EOF'
## Findings
none

**5. Overall Verdict**

ready
EOF
"""


FAKE_REVIEWER_BARE_HEADING_STYLE = """#!/usr/bin/env bash
cat <<'EOF'
## Findings
none

**Verdict**

ready with small edits
EOF
"""


def test_bare_heading_style_verdict_parses(tmp_path):
    """Claude commonly emits `**Verdict**\\n\\nvalue` (no `Overall`).

    The bare form must normalise the same way the `Overall verdict` heading
    style does, so end-to-end the round records verdict_valid=True.
    """
    payload = _run(FAKE_REVIEWER_BARE_HEADING_STYLE, tmp_path)
    assert payload["verdict"] == "ready with small edits"
    assert payload["verdict_valid"] is True
    assert payload["merged_verdict"] == "ready with small edits"


def _run(reviewer_script: str, tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)

    reviewer = repo / "stub-reviewer.sh"
    reviewer.write_text(reviewer_script); reviewer.chmod(0o755)

    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "plan", "--file", "plan.md", "--emit", "json",
         "--no-preflight"],
        cwd=repo, env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_heading_style_verdict_parses(tmp_path):
    payload = _run(FAKE_REVIEWER_HEADING_STYLE, tmp_path)
    assert payload["verdict"] == "ready with small edits"
    assert payload["verdict_valid"] is True
    assert payload["merged_verdict"] == "ready with small edits"


def test_bold_heading_style_verdict_parses(tmp_path):
    """Codex commonly emits `**N. Overall Verdict**\\n\\nready`.

    The leading/trailing `**` markdown emphasis broke the prior
    `_VERDICT_HEADING_STYLE` regex (\\s doesn't match `*`), causing
    verdict_valid=false despite an unambiguous textual verdict — observed
    on the p2-tasktool-design-P2-post-phase chain (r1-r3).
    """
    payload = _run(FAKE_REVIEWER_BOLD_HEADING_STYLE, tmp_path)
    assert payload["verdict"] == "ready"
    assert payload["verdict_valid"] is True
    assert payload["merged_verdict"] == "ready"
