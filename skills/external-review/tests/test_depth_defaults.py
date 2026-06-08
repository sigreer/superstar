from pathlib import Path
import sys, importlib.util
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)


def test_spec_defaults_standard():
    assert er.resolve_review_depth(None, "spec") == "standard"


def test_plan_defaults_standard():
    assert er.resolve_review_depth(None, "plan") == "standard"


def test_design_implementation_other_default_standard():
    for kind in ("design", "implementation", "other"):
        assert er.resolve_review_depth(None, kind) == "standard"


def test_post_slice_defaults_thorough():
    assert er.resolve_review_depth(None, "post-slice") == "thorough"


def test_post_phase_defaults_thorough():
    assert er.resolve_review_depth(None, "post-phase") == "thorough"


def test_explicit_flag_wins_over_kind_default():
    assert er.resolve_review_depth("exhaustive", "spec") == "exhaustive"
    assert er.resolve_review_depth("standard", "post-slice") == "standard"


def test_argparse_review_depth_default_is_none():
    args = er.parse_args([
        "review", "--kind", "spec", "--file", "x.md",
    ])
    assert args.review_depth is None


import subprocess, os, json


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# plan\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    reviewer = repo / "stub.sh"
    reviewer.write_text("#!/usr/bin/env bash\necho 'Overall verdict: ready'\n")
    reviewer.chmod(0o755)
    return repo


def _run(repo, *args):
    env = os.environ.copy()
    env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"), "review", *args],
        cwd=repo, env=env, capture_output=True, text=True,
    )


def test_round_entry_records_depth_resolved(tmp_path):
    repo = _init_repo(tmp_path)
    r = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json")
    assert r.returncode == 0, r.stderr
    chains = list((repo / "docs" / "reviewer").glob("*/chain.json"))
    assert len(chains) == 1
    manifest = json.loads(chains[0].read_text())
    assert manifest["rounds"][-1]["depth_resolved"] == "standard"
