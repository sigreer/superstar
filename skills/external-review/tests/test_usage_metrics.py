from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("external_reviewer", SCRIPTS / "external-reviewer.py")
er = importlib.util.module_from_spec(spec)
spec.loader.exec_module(er)


FAKE_REVIEWER_WITH_USAGE = """#!/usr/bin/env python3
import json
import os
from pathlib import Path

response_dir = Path(os.environ["AGENT_REVIEWER_RESPONSE_DIR"])
response_dir.mkdir(parents=True, exist_ok=True)
(response_dir / "reviewer-metadata.json").write_text(json.dumps({
    "provider": "codex",
    "model": "gpt-5.3-codex",
    "exact_usage": {
        "input_tokens": 101,
        "output_tokens": 23,
        "total_tokens": 124
    }
}))
print("## F1")
print("Severity: minor")
print("Looks fine.")
print("")
print("Overall verdict: ready")
"""


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True)
    (repo / "plan.md").write_text("# Plan\n\nDo the thing.\n")
    subprocess.run(["git", "-C", str(repo), "add", "plan.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    return repo


def _subprocess_env(tmp_path, **overrides):
    env = {
        "PATH": os.environ["PATH"],
        "AGENT_REVIEWER_STATE_FILE": str(tmp_path / "reviewer-state.json"),
    }
    env.update(overrides)
    return env


def test_review_round_records_timing_estimates_and_exact_sidecar_usage(tmp_path):
    repo = _init_repo(tmp_path)
    reviewer = repo / "reviewer.py"
    reviewer.write_text(FAKE_REVIEWER_WITH_USAGE)
    reviewer.chmod(0o755)

    env = _subprocess_env(tmp_path, AGENT_REVIEWER_CMD=str(reviewer))
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "external-reviewer.py"),
            "review",
            "--kind",
            "plan",
            "--file",
            "plan.md",
            "--emit",
            "json",
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["usage_capture_status"] == "exact"
    assert payload["estimated_usage"]["formula"] == "ceil(chars / 4)"
    assert payload["exact_usage"]["total_tokens"] == 124

    manifest = json.loads((repo / "docs" / "reviewer" / "plan-plan" / "chain.json").read_text())
    round_entry = manifest["rounds"][0]
    assert round_entry["started_at"].endswith("Z")
    assert round_entry["finished_at"].endswith("Z")
    assert round_entry["duration_ms"] >= 0
    assert round_entry["usage_capture_status"] == "exact"
    assert round_entry["estimated_usage"]["prompt_chars"] > 0
    assert round_entry["estimated_usage"]["response_chars"] > 0
    assert round_entry["exact_usage"]["provider"] == "codex"
    assert round_entry["exact_usage"]["model"] == "gpt-5.3-codex"
    assert round_entry["reviewers"][0]["usage_capture_status"] == "exact"
    assert round_entry["reviewers"][0]["exact_usage"]["total_tokens"] == 124


def test_stats_reports_grouped_round_metrics_and_provider_comparison(tmp_path):
    repo = _init_repo(tmp_path)
    reviewer = repo / "reviewer.py"
    reviewer.write_text(FAKE_REVIEWER_WITH_USAGE)
    reviewer.chmod(0o755)
    env = _subprocess_env(tmp_path, AGENT_REVIEWER_CMD=str(reviewer))

    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "external-reviewer.py"),
            "review",
            "--kind",
            "plan",
            "--file",
            "plan.md",
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )

    json_result = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"), "stats", "--json"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert json_result.returncode == 0, json_result.stderr
    stats = json.loads(json_result.stdout)
    assert stats["groups"]["plan"]["round_count"] == 1
    assert stats["groups"]["plan"]["first_round_count"] == 1
    assert stats["groups"]["plan"]["pass_count"] == 1
    assert stats["provider_comparison"]["codex"]["round_count"] == 1
    assert stats["provider_comparison"]["codex"]["estimated_total_tokens"] > 0

    text_result = subprocess.run(
        [sys.executable, str(SCRIPTS / "external-reviewer.py"), "stats"],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert text_result.returncode == 0, text_result.stderr
    assert "kind" in text_result.stdout
    assert "plan" in text_result.stdout
    assert "codex" in text_result.stdout


def test_stats_estimates_usage_for_legacy_rounds_from_request_and_response_files(tmp_path):
    repo = _init_repo(tmp_path)
    chain_dir = repo / "docs" / "reviewer" / "legacy-plan"
    chain_dir.mkdir(parents=True)
    (chain_dir / "r1-2026-05-20T1200-request.md").write_text("abcd" * 10)
    (chain_dir / "r1-2026-05-20T1200-response.md").write_text("xy" * 10)
    (chain_dir / "chain.json").write_text(json.dumps({
        "schema_version": 1,
        "chain": "legacy-plan",
        "kind": "plan",
        "target": "plan.md",
        "rounds": [{
            "round": 1,
            "status": "ok",
            "returncode": 0,
            "verdict": "ready",
            "verdict_valid": True,
            "provider": "claude",
            "request": "r1-2026-05-20T1200-request.md",
            "response": "r1-2026-05-20T1200-response.md",
        }],
    }))

    stats = er.collect_review_stats(repo / "docs" / "reviewer")

    assert stats["groups"]["plan"]["round_count"] == 1
    assert stats["provider_comparison"]["claude"]["round_count"] == 1
    assert stats["provider_comparison"]["claude"]["estimated_input_tokens"] == 10
    assert stats["provider_comparison"]["claude"]["estimated_output_tokens"] == 5


def test_stats_counts_each_reviewer_invocation_for_provider_comparison(tmp_path):
    repo = _init_repo(tmp_path)
    chain_dir = repo / "docs" / "reviewer" / "sweep-plan"
    chain_dir.mkdir(parents=True)
    (chain_dir / "primary-request.md").write_text("a" * 40)
    (chain_dir / "primary-response.md").write_text("b" * 20)
    (chain_dir / "sweep-request.md").write_text("c" * 80)
    (chain_dir / "sweep-response.md").write_text("d" * 40)
    (chain_dir / "chain.json").write_text(json.dumps({
        "schema_version": 1,
        "chain": "sweep-plan",
        "kind": "plan",
        "target": "plan.md",
        "rounds": [{
            "round": 1,
            "status": "ok",
            "returncode": 0,
            "verdict": "ready",
            "verdict_valid": True,
            "request": "primary-request.md",
            "response": "primary-response.md",
            "reviewers": [
                {
                    "role": "primary",
                    "provider": "codex",
                    "duration_ms": 100,
                    "request": "primary-request.md",
                    "response": "primary-response.md",
                    "estimated_usage": {
                        "estimated_input_tokens": 10,
                        "estimated_output_tokens": 5,
                        "estimated_total_tokens": 15,
                    },
                },
                {
                    "role": "sweep",
                    "provider": "codex",
                    "duration_ms": 200,
                    "request": "sweep-request.md",
                    "response": "sweep-response.md",
                    "estimated_usage": {
                        "estimated_input_tokens": 20,
                        "estimated_output_tokens": 10,
                        "estimated_total_tokens": 30,
                    },
                },
            ],
        }],
    }))

    stats = er.collect_review_stats(repo / "docs" / "reviewer")

    assert stats["groups"]["plan"]["round_count"] == 1
    assert stats["provider_comparison"]["codex"]["round_count"] == 2
    assert stats["provider_comparison"]["codex"]["estimated_total_tokens"] == 45
    assert stats["provider_comparison"]["codex"]["total_duration_ms"] == 300


def test_usage_sidecar_parses_codex_token_count_events(tmp_path):
    response_dir = tmp_path / "response"
    response_dir.mkdir()
    (response_dir / "reviewer-metadata.json").write_text(json.dumps({
        "provider": "codex",
        "codex_events_file": "codex-events.jsonl",
    }))
    (response_dir / "codex-events.jsonl").write_text(
        json.dumps({"type": "token_count", "input_tokens": 12, "output_tokens": 7, "total_tokens": 19}) + "\n"
    )

    exact, model, error = er.load_usage_sidecar(response_dir, provider="codex")

    assert error is None
    assert model is None
    assert exact["provider"] == "codex"
    assert exact["input_tokens"] == 12
    assert exact["output_tokens"] == 7
    assert exact["total_tokens"] == 19


def test_usage_sidecar_parses_claude_json_usage(tmp_path):
    response_dir = tmp_path / "response"
    response_dir.mkdir()
    (response_dir / "reviewer-metadata.json").write_text(json.dumps({
        "provider": "claude",
        "claude_output_file": "claude-output.json",
    }))
    (response_dir / "claude-output.json").write_text(json.dumps({
        "model": "claude-sonnet-4-5",
        "result": "Overall verdict: ready\n",
        "usage": {
            "input_tokens": 40,
            "output_tokens": 11,
        },
    }))

    exact, model, error = er.load_usage_sidecar(response_dir, provider="claude")

    assert error is None
    assert model == "claude-sonnet-4-5"
    assert exact["provider"] == "claude"
    assert exact["model"] == "claude-sonnet-4-5"
    assert exact["total_tokens"] == 51
