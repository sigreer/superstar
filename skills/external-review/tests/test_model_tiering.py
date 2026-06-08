from pathlib import Path
import subprocess, os, sys, importlib.util

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec); spec.loader.exec_module(er)

LIGHT = {"AGENT_REVIEWER_MODEL_LIGHT": "small-model"}
STRONG = {"AGENT_REVIEWER_MODEL_STRONG": "big-model"}
BOTH = {**LIGHT, **STRONG}


def test_spec_primary_uses_light():
    assert er.model_for_invocation("spec", "primary", env=BOTH) == "small-model"


def test_plan_primary_any_round_uses_light():
    # Matrix is round-independent: follow-up primaries keep their kind's tier.
    assert er.model_for_invocation("plan", "primary", env=BOTH) == "small-model"


def test_post_slice_primary_uses_strong():
    assert er.model_for_invocation("post-slice", "primary", env=BOTH) == "big-model"


def test_post_phase_primary_uses_strong():
    assert er.model_for_invocation("post-phase", "primary", env=BOTH) == "big-model"


def test_sweep_always_strong_even_for_spec():
    assert er.model_for_invocation("spec", "sweep", env=BOTH) == "big-model"


def test_no_cross_tier_fallback():
    # LIGHT never substitutes for STRONG and vice versa.
    assert er.model_for_invocation("post-slice", "primary", env=LIGHT) is None
    assert er.model_for_invocation("spec", "primary", env=STRONG) is None


def test_unset_env_returns_none():
    assert er.model_for_invocation("spec", "primary", env={}) is None


def test_cli_model_overrides_matrix():
    assert er.model_for_invocation("spec", "primary", cli_model="forced", env=BOTH) == "forced"


def test_context_env_includes_model_when_set(tmp_path):
    ctx = er.ReviewerInvocationContext(
        repo_root=tmp_path, chain_dir=tmp_path, request_file=tmp_path / "r.md",
        response_dir=tmp_path, scratch_dir=tmp_path, target_file=tmp_path / "t.md",
        kind="spec", role="primary", sweep_index=None,
        provider="claude", caller_provider="codex", model="small-model",
    )
    assert ctx.env()["AGENT_REVIEWER_MODEL"] == "small-model"


def test_context_env_omits_model_when_unset(tmp_path):
    ctx = er.ReviewerInvocationContext(
        repo_root=tmp_path, chain_dir=tmp_path, request_file=tmp_path / "r.md",
        response_dir=tmp_path, scratch_dir=tmp_path, target_file=tmp_path / "t.md",
        kind="spec", role="primary", sweep_index=None,
        provider="claude", caller_provider="codex",
    )
    assert "AGENT_REVIEWER_MODEL" not in ctx.env()


def test_argparse_model_flag_default_none():
    args = er.parse_args(["review", "--kind", "spec", "--file", "x.md"])
    assert args.model is None


# ---------------------------------------------------------------------------
# End-to-end helpers (adapted from test_resolution_gate.py)
# ---------------------------------------------------------------------------

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


def _run(repo, *args, env=None):
    base_env = os.environ.copy()
    if env:
        base_env.update(env)
    base_env["AGENT_REVIEWER_CMD"] = str(repo / "stub.sh")
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"), "review", *args],
        cwd=repo, env=base_env, capture_output=True, text=True,
    )


def test_model_recorded_end_to_end_without_sidecar(tmp_path):
    # F3 gate: a stub reviewer emits no usage sidecar; the requested tier
    # model must still land in emitted JSON and chain.json round entry.
    import json as _json
    repo = _init_repo(tmp_path)
    r = _run(repo, "--kind", "spec", "--file", "plan.md", "--emit", "json",
             env={"AGENT_REVIEWER_MODEL_LIGHT": "small-model"})
    assert r.returncode == 0, r.stderr
    payload = _json.loads(r.stdout)
    assert payload["model"] == "small-model"
    assert payload["reviewers"][0]["model"] == "small-model"
    chain_json = next((repo / "docs" / "reviewer").glob("*/chain.json"))
    manifest = _json.loads(chain_json.read_text())
    assert manifest["rounds"][-1]["model"] == "small-model"
