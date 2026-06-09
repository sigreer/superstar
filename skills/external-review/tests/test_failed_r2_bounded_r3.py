from pathlib import Path
import os, subprocess, sys, json, importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


FAKE_R1_LARGE = """#!/usr/bin/env bash
cat <<'EOF'
## F1
Severity: blocking
EOF
awk 'BEGIN { for (i=0;i<8000;i++) print "finding-body-line filler text "; }'
cat <<'EOF'

Overall verdict: revise
EOF
"""

FAKE_R2_ECHO_FAIL = """#!/usr/bin/env bash
echo "Reading prompt from stdin..." 1>&2
cat 1>&2
exit 1
"""

FAKE_R3_READY = """#!/usr/bin/env bash
echo "review body"
echo "Overall verdict: ready"
"""


def _init(tmp_path):
    repo = tmp_path / "repo"; repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n" + ("body line\n" * 200))
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    return repo


def _run(repo, reviewer_src, *extra_args):
    reviewer = repo / "fake.sh"; reviewer.write_text(reviewer_src); reviewer.chmod(0o755)
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(reviewer)
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"),
         "review", "--kind", "post-slice", "--file", "plan.md",
         "--work-id", "P1.S1", "--prompt-transport", "stdin", "--emit", "json",
         *extra_args],
        cwd=repo, env=env, capture_output=True, text=True, timeout=60,
    )


def test_failed_r2_yields_bounded_and_clean_r3_request(tmp_path):
    repo = _init(tmp_path)
    r1 = _run(repo, FAKE_R1_LARGE, "--no-preflight")
    assert r1.returncode == 0, r1.stderr
    chain_dir = repo / "docs/reviewer/plan-P1-S1-post-slice"
    # Satisfy resolution gate so r2 actually invokes the (failing) reviewer.
    (chain_dir / "r1-resolution.md").write_text("ok\n")
    r2 = _run(repo, FAKE_R2_ECHO_FAIL)
    assert r2.returncode != 0
    payload = json.loads(r2.stdout)
    assert payload["status"] == "failed"
    assert payload["verdict_valid"] is False
    r2_response = next(chain_dir.glob("r2-*-response.md"))
    assert r2_response.stat().st_size < 8 * 1024, r2_response.stat().st_size
    assert er.PROMPT_SENTINEL_START not in r2_response.read_text()
    r3 = _run(repo, FAKE_R3_READY)
    assert r3.returncode == 0, (
        f"r3 did not succeed; rc={r3.returncode} stderr={r3.stderr}"
    )
    r3_request = next(chain_dir.glob("r3-*-request.md"))
    body = r3_request.read_text()
    assert "Reading prompt from stdin..." not in body


def test_r3_request_size_bounded(tmp_path):
    repo = _init(tmp_path)
    r1 = _run(repo, FAKE_R1_LARGE, "--no-preflight")
    assert r1.returncode == 0, r1.stderr
    chain_dir = repo / "docs/reviewer/plan-P1-S1-post-slice"
    (chain_dir / "r1-resolution.md").write_text("ok\n")
    r2 = _run(repo, FAKE_R2_ECHO_FAIL)
    assert r2.returncode != 0
    r3 = _run(repo, FAKE_R3_READY)
    assert r3.returncode == 0, r3.stderr
    r3_request = next(chain_dir.glob("r3-*-request.md"))
    assert r3_request.stat().st_size < 250 * 1024, (
        f"r3 request bytes={r3_request.stat().st_size}; expected < 250 KB"
    )
